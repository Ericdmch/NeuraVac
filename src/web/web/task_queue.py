"""Draggable Roomba task queue with polygon region cleaning, dock seeking (opcode 143), and override preemption."""
import math
import threading
import time
import uuid


TASK_PRESETS = [
    {
        'type': 'scan_area',
        'title': 'Scan Area',
        'description': 'Persistently explore unknown frontiers with SLAM Toolbox + Nav2 (escapes buffer zones)',
        'default_params': {'cleaning': False, 'target': [0.0, 0.0]},
    },
    {
        'type': 'return_home',
        'title': 'Return to Dock',
        'description': 'Navigate back to (0, 0) and park at dock with vacuum disabled',
        'default_params': {'cleaning': False, 'target': [0.0, 0.0], 'seek_dock': False},
    },
]

VALID_TASK_TYPES = {
    'override',
    'goto',
    'clean_polygon',
    'scan_area',
    'return_home',
    'seek_dock',
}

REGION_COLORS = ['#66d6a4', '#72b7f4', '#ffa66b', '#d48cff', '#ff7a9e', '#ffe066']


def point_in_polygon(x, y, vertices):
    """Ray-casting check for whether point (x, y) is inside polygon vertices."""
    n = len(vertices)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = float(vertices[i][0]), float(vertices[i][1])
        xj, yj = float(vertices[j][0]), float(vertices[j][1])
        intersect = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside


def generate_polygon_waypoints(vertices, spacing_m=0.25):
    """Generate a boustrophedon (lawnmower zig-zag) coverage path inside a polygon."""
    if not isinstance(vertices, (list, tuple)) or len(vertices) < 3:
        raise ValueError('A polygon requires at least 3 vertices')
    pts = []
    for v in vertices:
        if not isinstance(v, (list, tuple)) or len(v) != 2:
            raise ValueError('Each polygon vertex must be [x, y]')
        x, y = float(v[0]), float(v[1])
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError('Polygon vertices must be finite numbers')
        pts.append((x, y))

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    spacing = max(0.12, float(spacing_m))
    waypoints = []
    row_idx = 0
    y = min_y + spacing * 0.5
    while y <= max_y - spacing * 0.25 or row_idx == 0:
        row_pts = []
        x = min_x + spacing * 0.5
        while x <= max_x - spacing * 0.25 or not row_pts:
            if point_in_polygon(x, y, pts):
                row_pts.append([round(x, 3), round(y, 3)])
            x += spacing
            if x > max_x + spacing:
                break
        if row_idx % 2 == 1:
            row_pts.reverse()
        waypoints.extend(row_pts)
        y += spacing
        row_idx += 1
        if y > max_y + spacing or len(waypoints) >= 40:
            break

    if not waypoints:
        cx = round(sum(xs) / len(xs), 3)
        cy = round(sum(ys) / len(ys), 3)
        waypoints.append([cx, cy])

    return waypoints[:40]


CLEAN_SWEEP_RADIUS_M = 0.18


def generate_polygon_tiles(vertices, tile_size_m=0.10):
    """Generate a grid of [x, y] tile centers inside a polygon for visual purple-tile cleaning tracking."""
    if not isinstance(vertices, (list, tuple)) or len(vertices) < 3:
        return []
    pts = [(float(v[0]), float(v[1])) for v in vertices if isinstance(v, (list, tuple)) and len(v) == 2]
    if len(pts) < 3:
        return []
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    step = max(0.05, float(tile_size_m))
    tiles = []
    y = min_y + step * 0.5
    while y <= max_y:
        x = min_x + step * 0.5
        while x <= max_x:
            if point_in_polygon(x, y, pts):
                tiles.append([round(x, 3), round(y, 3)])
            x += step
            if len(tiles) >= 600:
                break
        if len(tiles) >= 600:
            break
        y += step
    if not tiles:
        cx = round(sum(xs) / len(xs), 3)
        cy = round(sum(ys) / len(ys), 3)
        tiles.append([cx, cy])
    return tiles


class TaskQueueManager:
    """Thread-safe task queue that drives the Roomba through ordered tasks and polygon regions."""

    def __init__(
        self,
        dispatch_fn=None,
        stop_fn=None,
        cleaning_fn=None,
        seek_dock_fn=None,
        override_hold_sec=2.5,
    ):
        self._lock = threading.RLock()
        self._queue = []
        self._history = []
        self._regions = []
        self._auto_run = True
        self._override_key_held = False
        self._override_pinned = False
        self._override_release_at = 0.0
        self._override_hold_sec = float(override_hold_sec)
        self._dispatch_fn = dispatch_fn or (lambda task: None)
        self._stop_fn = stop_fn or (lambda: None)
        self._cleaning_fn = cleaning_fn or (lambda enabled: None)
        self._seek_dock_fn = seek_dock_fn or (lambda: None)

    def _serialize_task(self, task):
        return {
            'id': task['id'],
            'type': task['type'],
            'title': task['title'],
            'status': task['status'],
            'params': dict(task.get('params') or {}),
            'note': task.get('note', ''),
            'created_at': task['created_at'],
        }

    def snapshot(self, autonomy_state=None, robot_pose=None):
        with self._lock:
            if robot_pose is not None:
                self._record_robot_sweep_locked(robot_pose)
            if autonomy_state is not None:
                self._tick_locked(autonomy_state, robot_pose=robot_pose)
            override_active = any(t['type'] == 'override' for t in self._queue)
            return {
                'queue': [self._serialize_task(t) for t in self._queue],
                'history': [self._serialize_task(t) for t in self._history[:5]],
                'regions': [dict(r) for r in self._regions],
                'auto_run': self._auto_run,
                'override_active': override_active,
                'override_pinned': self._override_pinned,
                'presets': TASK_PRESETS,
            }

    def record_robot_sweep(self, robot_pose):
        with self._lock:
            self._record_robot_sweep_locked(robot_pose)

    def _record_robot_sweep_locked(self, robot_pose):
        if not isinstance(robot_pose, (list, tuple)) or len(robot_pose) < 2:
            return
        try:
            rx, ry = float(robot_pose[0]), float(robot_pose[1])
        except (TypeError, ValueError):
            return
        if not (math.isfinite(rx) and math.isfinite(ry)):
            return

        active_region_ids = {
            t.get('params', {}).get('region_id')
            for t in self._queue
            if t['type'] == 'clean_polygon' and t['status'] == 'active'
        }
        rad_sq = CLEAN_SWEEP_RADIUS_M * CLEAN_SWEEP_RADIUS_M
        for reg in self._regions:
            if not reg.get('cleaning_active'):
                continue
            if active_region_ids and reg['id'] not in active_region_ids:
                continue
            uncleaned = reg.get('uncleaned_tiles') or []
            if uncleaned:
                remaining = [
                    pt for pt in uncleaned
                    if (pt[0] - rx) ** 2 + (pt[1] - ry) ** 2 > rad_sq
                ]
                reg['uncleaned_tiles'] = remaining
            swept = reg.setdefault('swept_points', [])
            if not swept or (swept[-1][0] - rx) ** 2 + (swept[-1][1] - ry) ** 2 >= 0.03 ** 2:
                swept.append([round(rx, 3), round(ry, 3)])
                if len(swept) > 600:
                    del swept[: len(swept) - 600]
            total = max(1, int(reg.get('total_tiles') or len(reg.get('tiles') or [])))
            cleaned = max(0, total - len(reg.get('uncleaned_tiles') or []))
            reg['cleaned_count'] = cleaned
            reg['progress_pct'] = round(100.0 * cleaned / total)

        for t in self._queue:
            if t['type'] == 'clean_polygon':
                rid = t.get('params', {}).get('region_id')
                reg = next((r for r in self._regions if r['id'] == rid), None) if rid else None
                if reg is not None:
                    t['params']['progress_pct'] = reg.get('progress_pct', 0)
                    t['params']['cleaned_count'] = reg.get('cleaned_count', 0)
                    t['params']['total_tiles'] = reg.get('total_tiles', 0)

    def add_region(self, name, vertices, spacing_m=0.25):
        waypoints = generate_polygon_waypoints(vertices, spacing_m=spacing_m)
        clean_verts = [[round(float(v[0]), 3), round(float(v[1]), 3)] for v in vertices]
        tiles = generate_polygon_tiles(clean_verts, tile_size_m=0.10)
        with self._lock:
            idx = len(self._regions) + 1
            region_name = (str(name or '').strip()) or f'Region {idx}'
            color = REGION_COLORS[(idx - 1) % len(REGION_COLORS)]
            region = {
                'id': uuid.uuid4().hex[:8],
                'name': region_name,
                'vertices': clean_verts,
                'waypoints': waypoints,
                'tiles': tiles,
                'uncleaned_tiles': [],
                'swept_points': [],
                'cleaning_active': False,
                'total_tiles': len(tiles),
                'cleaned_count': 0,
                'progress_pct': 0,
                'color': color,
            }
            self._regions.append(region)
            return dict(region)

    def remove_region(self, region_id):
        with self._lock:
            before = len(self._regions)
            self._regions = [r for r in self._regions if r['id'] != region_id]
            return len(self._regions) < before

    def add_task(self, task_type, title=None, params=None, position='end'):
        if task_type not in VALID_TASK_TYPES:
            raise ValueError(f'Unsupported task type: {task_type}')
        params = dict(params or {})

        with self._lock:
            if task_type == 'clean_polygon':
                region_id = params.get('region_id')
                region = next((r for r in self._regions if r['id'] == region_id), None) if region_id else None
                if region is not None:
                    vertices = region['vertices']
                    waypoints = list(region['waypoints'])
                    region_name = region['name']
                    region['cleaning_active'] = True
                    region['uncleaned_tiles'] = [list(pt) for pt in (region.get('tiles') or [])]
                    region['swept_points'] = []
                    region['cleaned_count'] = 0
                    region['progress_pct'] = 0
                else:
                    vertices = params.get('vertices')
                    waypoints = generate_polygon_waypoints(vertices, spacing_m=params.get('spacing_m', 0.25))
                    region_name = params.get('region_name') or 'Polygon Region'
                    auto_reg = self.add_region(region_name, vertices, spacing_m=params.get('spacing_m', 0.25))
                    region = next((r for r in self._regions if r['id'] == auto_reg['id']), None)
                    if region is not None:
                        region['cleaning_active'] = True
                        region['uncleaned_tiles'] = [list(pt) for pt in (region.get('tiles') or [])]
                        params['region_id'] = region['id']
                params['vertices'] = vertices
                params['waypoints'] = waypoints
                params['waypoint_index'] = 0
                params['target'] = waypoints[0]
                params['cleaning'] = bool(params.get('cleaning', True))
                params['total_tiles'] = region.get('total_tiles', 0) if region else 0
                params['cleaned_count'] = 0
                params['progress_pct'] = 0
                if not title:
                    title = f'Clean {region_name} ({len(waypoints)} pts)'

            if task_type == 'return_home':
                params['cleaning'] = False
                # Roomba OI Opcode 143 (Seek Dock) hardware-forces vacuum and brushes on in firmware.
                # Default seek_dock to False so return_home navigates to dock silently with zero vacuum.
                if 'seek_dock' not in params:
                    params['seek_dock'] = False

            if not title:
                if task_type == 'goto' and isinstance(params.get('target'), (list, tuple)) and len(params['target']) == 2:
                    tx, ty = float(params['target'][0]), float(params['target'][1])
                    title = f'Go to ({tx:.2f}, {ty:.2f}) m'
                else:
                    titles = {
                        'override': 'Manual Override',
                        'goto': 'Go to Point',
                        'clean_polygon': 'Clean Polygon Region',
                        'scan_area': 'Scan Area',
                        'return_home': 'Return to Dock',
                        'seek_dock': 'Seek Dock (IR Beams)',
                    }
                    title = titles.get(task_type, task_type)

            task = {
                'id': uuid.uuid4().hex[:10],
                'type': task_type,
                'title': str(title).strip() or task_type,
                'status': 'queued',
                'params': params,
                'note': '',
                'created_at': time.time(),
                '_dispatched_at': None,
                '_busy_seen': False,
                '_dock_stage': None,
            }
            if task_type == 'override':
                return self._insert_override_locked(pinned=bool(params.get('pinned', True)))
            if position == 'top':
                insert_idx = 1 if (self._queue and self._queue[0]['type'] == 'override') else 0
                if insert_idx < len(self._queue) and self._queue[insert_idx]['status'] == 'active':
                    self._demote_active_locked(self._queue[insert_idx])
                self._queue.insert(insert_idx, task)
            else:
                self._queue.append(task)
            self._maybe_start_top_locked()
            return self._serialize_task(task)

    def _demote_active_locked(self, task):
        task['status'] = 'queued'
        task['note'] = 'Paused / preempted'
        task['_dispatched_at'] = None
        task['_busy_seen'] = False
        task['_dock_stage'] = None
        if task.get('params', {}).get('cleaning'):
            self._cleaning_fn(False)

    def _insert_override_locked(self, pinned=False, key_held=False):
        now = time.monotonic()
        if pinned:
            self._override_pinned = True
        if key_held:
            self._override_key_held = True
            self._override_release_at = now + self._override_hold_sec
        if self._queue and self._queue[0]['type'] == 'override':
            ov = self._queue[0]
            ov['status'] = 'active'
            ov['title'] = 'Manual Override (Locked)' if self._override_pinned else 'Manual Override (WASD Active)'
            ov['note'] = 'Operator has direct control'
            return self._serialize_task(ov)

        for t in self._queue:
            if t['status'] == 'active':
                self._demote_active_locked(t)

        ov = {
            'id': 'override-active',
            'type': 'override',
            'title': 'Manual Override (Locked)' if self._override_pinned else 'Manual Override (WASD Active)',
            'status': 'active',
            'params': {'pinned': self._override_pinned},
            'note': 'Operator has direct control',
            'created_at': time.time(),
            '_dispatched_at': now,
            '_busy_seen': True,
        }
        self._queue.insert(0, ov)
        return self._serialize_task(ov)

    def notify_manual_key(self, pressed):
        with self._lock:
            now = time.monotonic()
            if pressed:
                self._insert_override_locked(pinned=self._override_pinned, key_held=True)
            else:
                self._override_key_held = False
                self._override_release_at = now + self._override_hold_sec

    def set_override_pinned(self, pinned):
        with self._lock:
            self._override_pinned = bool(pinned)
            if self._override_pinned:
                self._stop_fn()
                self._insert_override_locked(pinned=True)
            else:
                self._override_key_held = False
                self._override_release_at = 0.0
                self._remove_override_locked()
                self._maybe_start_top_locked()

    def _remove_override_locked(self):
        self._queue = [t for t in self._queue if t['type'] != 'override']
        self._override_pinned = False
        self._override_key_held = False

    def reorder(self, task_ids):
        if not isinstance(task_ids, list):
            raise ValueError('task_ids must be a list of task IDs')
        with self._lock:
            by_id = {t['id']: t for t in self._queue}
            override_tasks = [t for t in self._queue if t['type'] == 'override']
            reordered = []
            seen = set()
            for tid in task_ids:
                if tid in by_id and tid not in seen and by_id[tid]['type'] != 'override':
                    reordered.append(by_id[tid])
                    seen.add(tid)
            for t in self._queue:
                if t['id'] not in seen and t['type'] != 'override':
                    reordered.append(t)
            prev_active = next((t for t in reordered if t['status'] == 'active'), None)
            new_first = reordered[0] if reordered else None
            if prev_active is not None and new_first is not prev_active:
                self._stop_fn()
                self._demote_active_locked(prev_active)
            self._queue = override_tasks + reordered
            self._maybe_start_top_locked()
            return [self._serialize_task(t) for t in self._queue]

    def remove_task(self, task_id):
        with self._lock:
            target = next((t for t in self._queue if t['id'] == task_id), None)
            if target is None:
                return False
            if target['type'] == 'override':
                self._remove_override_locked()
                self._maybe_start_top_locked()
                return True
            was_active = target['status'] == 'active'
            rid = target.get('params', {}).get('region_id')
            self._queue = [t for t in self._queue if t['id'] != task_id]
            if rid and not any(t.get('params', {}).get('region_id') == rid for t in self._queue):
                reg = next((r for r in self._regions if r['id'] == rid), None)
                if reg is not None:
                    reg['cleaning_active'] = False
                    reg['uncleaned_tiles'] = []
            if was_active:
                if target.get('params', {}).get('cleaning'):
                    self._cleaning_fn(False)
                self._stop_fn()
            self._maybe_start_top_locked()
            return True

    def clear(self):
        with self._lock:
            had_active = any(t['status'] == 'active' and t['type'] != 'override' for t in self._queue)
            had_cleaning = any(t.get('params', {}).get('cleaning') for t in self._queue)
            self._queue = [t for t in self._queue if t['type'] == 'override' and self._override_pinned]
            for reg in self._regions:
                reg['cleaning_active'] = False
                reg['uncleaned_tiles'] = []
            if had_cleaning:
                self._cleaning_fn(False)
            if had_active:
                self._stop_fn()

    def set_auto_run(self, enabled):
        with self._lock:
            self._auto_run = bool(enabled)
            if self._auto_run:
                self._maybe_start_top_locked()
            else:
                for t in self._queue:
                    if t['status'] == 'active' and t['type'] != 'override':
                        self._stop_fn()
                        self._demote_active_locked(t)

    def _maybe_start_top_locked(self):
        if not self._auto_run or not self._queue:
            return
        top = self._queue[0]
        if top['type'] == 'override' or top['status'] == 'active':
            return
        top['status'] = 'active'
        top['_dispatched_at'] = time.monotonic()
        top['_busy_seen'] = False

        if top['type'] == 'seek_dock':
            top['_dock_stage'] = 'seeking_ir'
            top['note'] = 'Sent OI Opcode 143 (Seek Dock) — searching for Home Base IR beams…'
            self._cleaning_fn(False)
            self._seek_dock_fn()
            return

        if top['type'] == 'clean_polygon':
            wps = top.get('params', {}).get('waypoints') or []
            idx = int(top.get('params', {}).get('waypoint_index', 0))
            if wps and 0 <= idx < len(wps):
                top['params']['target'] = wps[idx]
                top['note'] = f'Cleaning waypoint {idx + 1}/{len(wps)} ({wps[idx][0]:.2f}, {wps[idx][1]:.2f}) m…'
            else:
                top['note'] = 'Cleaning polygon region…'
        elif top['type'] == 'return_home':
            top['_dock_stage'] = 'nav_to_dock'
            top['note'] = 'Navigating to dock area (0, 0) with vacuum off…'
            self._cleaning_fn(False)
        else:
            top['note'] = 'Executing…'

        if top.get('params', {}).get('cleaning'):
            self._cleaning_fn(True)
        else:
            self._cleaning_fn(False)
        self._dispatch_fn(top)

    def _advance_or_finish_polygon_locked(self, top, reason=''):
        wps = top.get('params', {}).get('waypoints') or []
        prev_idx = int(top.get('params', {}).get('waypoint_index', 0))
        if wps and 0 <= prev_idx < len(wps):
            self._record_robot_sweep_locked(wps[prev_idx])
        idx = prev_idx + 1
        if idx < len(wps):
            top['params']['waypoint_index'] = idx
            top['params']['target'] = wps[idx]
            top['_dispatched_at'] = time.monotonic()
            top['_busy_seen'] = False
            pct = top.get('params', {}).get('progress_pct', 0)
            top['note'] = f'Cleaning waypoint {idx + 1}/{len(wps)} ({pct}% swept)…'
            self._dispatch_fn(top)
            return True
        rid = top.get('params', {}).get('region_id')
        if rid:
            reg = next((r for r in self._regions if r['id'] == rid), None)
            if reg is not None:
                reg['cleaning_active'] = False
                reg['uncleaned_tiles'] = []
                reg['cleaned_count'] = reg.get('total_tiles', 0)
                reg['progress_pct'] = 100
        if top.get('params', {}).get('cleaning'):
            self._cleaning_fn(False)
        top['status'] = 'completed'
        top['note'] = reason or f'Finished cleaning polygon ({len(wps)} waypoints)'
        finished = self._queue.pop(0)
        self._history.insert(0, finished)
        del self._history[10:]
        self._maybe_start_top_locked()
        return False

    def _tick_locked(self, autonomy_state, robot_pose=None):
        now = time.monotonic()
        if self._queue and self._queue[0]['type'] == 'override':
            if not self._override_pinned and not self._override_key_held and now >= self._override_release_at:
                self._remove_override_locked()

        if not self._queue:
            return

        top = self._queue[0]
        if top['type'] == 'override':
            return

        if top['status'] != 'active':
            self._maybe_start_top_locked()
            return

        elapsed = now - (top.get('_dispatched_at') or now)

        # Handle OI Opcode 143 (Seek Dock) stage
        if top.get('_dock_stage') == 'seeking_ir':
            if elapsed >= 8.0:
                top['status'] = 'completed'
                top['note'] = 'Roomba Seek Dock (Opcode 143) active'
                finished = self._queue.pop(0)
                self._history.insert(0, finished)
                del self._history[10:]
                self._maybe_start_top_locked()
            return

        state_obj = autonomy_state if isinstance(autonomy_state, dict) else {}
        nav_state = state_obj.get('state')
        armed = bool(state_obj.get('armed'))
        reason = state_obj.get('reason') or ''

        if armed or nav_state in ('exploring', 'returning'):
            top['_busy_seen'] = True
            if reason and top['type'] != 'clean_polygon':
                top['note'] = reason

        if elapsed < 1.2 and not top['_busy_seen']:
            return

        if nav_state == 'complete' or (top['_busy_seen'] and nav_state == 'idle' and not armed):
            if top['type'] == 'clean_polygon':
                self._advance_or_finish_polygon_locked(top, reason=reason)
                return
            if top['type'] == 'return_home':
                if top.get('params', {}).get('seek_dock', False):
                    top['_dock_stage'] = 'seeking_ir'
                    top['_dispatched_at'] = now
                    top['note'] = 'Reached dock area — sent Opcode 143 (Seek Dock) for IR docking!'
                    self._cleaning_fn(False)
                    self._seek_dock_fn()
                    return
                top['status'] = 'completed'
                top['note'] = reason or 'Returned to dock at (0.00, 0.00) m'
                self._cleaning_fn(False)
                finished = self._queue.pop(0)
                self._history.insert(0, finished)
                del self._history[10:]
                self._maybe_start_top_locked()
                return
            top['status'] = 'completed'
            top['note'] = reason or 'Completed'
            if top.get('params', {}).get('cleaning'):
                self._cleaning_fn(False)
            finished = self._queue.pop(0)
            self._history.insert(0, finished)
            del self._history[10:]
            self._maybe_start_top_locked()
        elif nav_state == 'stopped' and (top['_busy_seen'] or elapsed >= 2.5):
            if 'redirecting' in reason.lower():
                return
            if top['type'] == 'clean_polygon':
                # Skip blocked waypoint and continue cleaning the rest of the polygon
                self._advance_or_finish_polygon_locked(top, reason=reason)
                return
            if top['type'] == 'return_home':
                if top.get('params', {}).get('seek_dock', False):
                    # Even if Nav2 stopped near the dock, trigger Roomba Opcode 143 Seek Dock if requested
                    top['_dock_stage'] = 'seeking_ir'
                    top['_dispatched_at'] = now
                    top['note'] = 'Triggered Opcode 143 (Seek Dock) to find Home Base beams…'
                    self._cleaning_fn(False)
                    self._seek_dock_fn()
                    return
                top['status'] = 'completed'
                top['note'] = reason or 'Returned to dock area'
                self._cleaning_fn(False)
                finished = self._queue.pop(0)
                self._history.insert(0, finished)
                del self._history[10:]
                self._maybe_start_top_locked()
                return
            if top.get('params', {}).get('cleaning'):
                self._cleaning_fn(False)
            top['status'] = 'failed'
            top['note'] = reason or 'Stopped before completion'
            failed = self._queue.pop(0)
            self._history.insert(0, failed)
            del self._history[10:]
            self._maybe_start_top_locked()
