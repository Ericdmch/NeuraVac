"""Occupancy-grid coordinates and conservative known-space reachability."""
from collections import deque
import math


class GridGeometry:
    def __init__(self, width, height, resolution, origin_x, origin_y, origin_yaw):
        if (not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0
                or not all(math.isfinite(v) for v in (resolution, origin_x, origin_y, origin_yaw))
                or resolution <= 0):
            raise ValueError('Invalid grid geometry')
        self.width, self.height, self.resolution = width, height, resolution
        self.x, self.y, self.yaw = origin_x, origin_y, origin_yaw

    def world_cell(self, x, y):
        if not math.isfinite(x) or not math.isfinite(y):
            return None
        dx, dy = x - self.x, y - self.y
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        col = math.floor((c * dx + s * dy) / self.resolution)
        row = math.floor((-s * dx + c * dy) / self.resolution)
        return (col, row) if 0 <= col < self.width and 0 <= row < self.height else None

    def cell_center(self, cell):
        col, row = cell
        if not (0 <= col < self.width and 0 <= row < self.height):
            raise ValueError('Cell outside map')
        x, y = (col + .5) * self.resolution, (row + .5) * self.resolution
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return self.x + c*x - s*y, self.y + s*x + c*y


def route_to(rows, start, goal, clearance_cells, free_threshold=20):
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError('Grid must be rectangular and nonempty')
    if not isinstance(clearance_cells, int) or clearance_cells < 0:
        raise ValueError('Clearance must be a nonnegative integer')
    height, width = len(rows), len(rows[0])
    if any(not isinstance(v, int) or v < -1 or v > 100 for row in rows for v in row):
        raise ValueError('Invalid occupancy value')
    def free(cell):
        x, y = cell
        for dy in range(-clearance_cells, clearance_cells + 1):
            for dx in range(-clearance_cells, clearance_cells + 1):
                if dx*dx + dy*dy > clearance_cells*clearance_cells:
                    continue
                xx, yy = x + dx, y + dy
                if not (0 <= xx < width and 0 <= yy < height and 0 <= rows[yy][xx] <= free_threshold):
                    return False
        return True
    if start is None or goal is None or not free(start) or not free(goal):
        return None
    parents = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            path = []
            while cell is not None:
                path.append(cell)
                cell = parents[cell]
            return list(reversed(path))
        x, y = cell
        for point in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
            if point not in parents and free(point):
                parents[point] = cell
                queue.append(point)
    return None
