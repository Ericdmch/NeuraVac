export type Position = [number, number];
export interface MapOrigin { x: number; y: number; yaw: number }
export interface FloorObject { id: string; class_name: string; position?: Position; confidence?: number; traversable?: boolean; vacuumable?: boolean }
export interface Region { id: string; position?: Position; debris_score?: number; confidence?: number; cleaned?: boolean; reachable?: boolean }
export interface Attempt { region_id: string; before_score?: number; after_score?: number; improvement?: number; pass_number?: number; success?: boolean; duration_s?: number }
export interface MissionEvent { event: string; timestamp?: number | string; data?: Record<string, unknown> }
export interface Cloud { status?: string; model?: string; latency_ms?: number; request_id?: string }
export interface Snapshot {
  mode: 'simulation' | 'hardware'; mission_id?: string; state: string; battery_percent?: number; connected: boolean;
  safety?: { safe?: boolean; reasons?: string[]; latched?: boolean };
  cloud?: Cloud;
  pose?: { x: number; y: number; yaw: number };
  world?: { width?: number; height?: number; origin?: MapOrigin; objects?: FloorObject[]; regions?: Region[]; obstacles?: { id: string; x: number; y: number; radius: number; class_name?: string }[] };
  path?: Position[];
  metrics?: { initial_debris_score?: number; current_debris_score?: number; cleanliness_percent?: number; coverage_percent?: number; regions_remaining?: number; successful_passes?: number; retried_passes?: number };
  attempts?: Attempt[]; events?: MissionEvent[];
  self_test?: { status?: string; checks?: Record<string, unknown> | unknown[] };
}

export function metricValue(value?: number, suffix = ''): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  const rounded = Number(value.toFixed(suffix ? 1 : 3));
  const displayed = value !== 0 && rounded === 0 ? value.toPrecision(2) : rounded;
  return `${displayed}${suffix}`;
}

function record(value: unknown): value is Record<string, unknown> { return value !== null && typeof value === 'object' && !Array.isArray(value); }
function finite(value: unknown): value is number { return typeof value === 'number' && Number.isFinite(value); }
function optionalNumber(value: unknown): value is number | undefined { return value === undefined || finite(value); }
function position(value: unknown): value is Position { return Array.isArray(value) && value.length === 2 && value.every(finite); }
function entriesValid(value: unknown, check: (item: unknown) => boolean) { return value === undefined || (Array.isArray(value) && value.every(check)); }

function omitNull(value: Record<string, unknown>): Record<string, unknown> { return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== null)); }
export function parseSnapshot(input: unknown): Snapshot | null {
  if (!record(input)) return null;
  const value = omitNull(input);
  for (const key of ['cloud', 'safety', 'metrics', 'pose', 'world', 'self_test']) {
    const section = value[key];
    if (record(section)) value[key] = omitNull(section);
  }
  for (const key of ['attempts', 'events']) {
    const section = value[key];
    if (Array.isArray(section)) value[key] = section.map(item => record(item) ? omitNull(item) : item);
  }
  if (!['simulation', 'hardware'].includes(String(value.mode)) || typeof value.state !== 'string' || !value.state || typeof value.connected !== 'boolean') return null;
  if (!optionalNumber(value.battery_percent) || (value.mission_id !== undefined && typeof value.mission_id !== 'string')) return null;
  if (value.safety !== undefined && (!record(value.safety) || (value.safety.safe !== undefined && typeof value.safety.safe !== 'boolean') || (value.safety.latched !== undefined && typeof value.safety.latched !== 'boolean') || !entriesValid(value.safety.reasons, item => typeof item === 'string'))) return null;
  if (value.cloud !== undefined && (!record(value.cloud) || !optionalNumber(value.cloud.latency_ms) || ['status', 'model', 'request_id'].some(key => value.cloud && record(value.cloud) && value.cloud[key] !== undefined && typeof value.cloud[key] !== 'string'))) return null;
  if (value.metrics !== undefined && (!record(value.metrics) || Object.values(value.metrics).some(item => !optionalNumber(item)))) return null;
  if (value.pose !== undefined && (!record(value.pose) || !finite(value.pose.x) || !finite(value.pose.y) || !finite(value.pose.yaw))) return null;
  if (value.world !== undefined) {
    if (!record(value.world) || !optionalNumber(value.world.width) || !optionalNumber(value.world.height)) return null;
    if (value.world.origin !== undefined && (!record(value.world.origin) || !finite(value.world.origin.x) || !finite(value.world.origin.y) || !finite(value.world.origin.yaw))) return null;
    if (!entriesValid(value.world.objects, item => record(item) && typeof item.id === 'string' && typeof item.class_name === 'string' && (item.position === undefined || position(item.position)) && optionalNumber(item.confidence) && [item.traversable, item.vacuumable].every(flag => flag === undefined || typeof flag === 'boolean'))) return null;
    if (!entriesValid(value.world.regions, item => record(item) && typeof item.id === 'string' && (item.position === undefined || position(item.position)) && optionalNumber(item.debris_score) && optionalNumber(item.confidence) && [item.cleaned, item.reachable].every(flag => flag === undefined || typeof flag === 'boolean'))) return null;
    if (!entriesValid(value.world.obstacles, item => record(item) && typeof item.id === 'string' && finite(item.x) && finite(item.y) && finite(item.radius) && item.radius >= 0 && (item.class_name === undefined || typeof item.class_name === 'string'))) return null;
  }
  if (!entriesValid(value.path, position)) return null;
  if (!entriesValid(value.attempts, item => record(item) && typeof item.region_id === 'string' && ['before_score', 'after_score', 'improvement', 'pass_number', 'duration_s'].every(key => optionalNumber(item[key])) && (item.success === undefined || typeof item.success === 'boolean'))) return null;
  if (!entriesValid(value.events, item => record(item) && typeof item.event === 'string' && (item.timestamp === undefined || finite(item.timestamp) || typeof item.timestamp === 'string') && (item.data === undefined || record(item.data)))) return null;
  if (value.self_test !== undefined && (!record(value.self_test) || (value.self_test.status !== undefined && typeof value.self_test.status !== 'string') || (value.self_test.checks !== undefined && !record(value.self_test.checks) && !Array.isArray(value.self_test.checks)))) return null;
  return value as unknown as Snapshot;
}

export function cloudLabel(cloud?: Cloud): string {
  if (!cloud?.status) return 'Not reported';
  if (['offline', 'disabled', 'fallback', 'not_configured', 'unavailable', 'deterministic'].includes(cloud.status.toLowerCase())) return 'Offline · deterministic planning';
  return cloud.status.charAt(0).toUpperCase() + cloud.status.slice(1).replaceAll('_', ' ');
}

export function controlAvailability(snapshot: Snapshot | null, fresh: boolean, pending: boolean) {
  const ready = Boolean(snapshot && fresh && snapshot.connected && !pending);
  const healthy = ready && snapshot?.safety?.safe === true && snapshot.safety.latched !== true;
  const active = ['SCANNING', 'PLANNING', 'NAVIGATING', 'CLEANING', 'VERIFYING', 'RETRYING', 'REPLANNING'].includes(snapshot?.state ?? '');
  return {
    start: healthy && ['IDLE', 'COMPLETE'].includes(snapshot?.state ?? ''),
    pause: ready && active,
    resume: healthy && snapshot?.state === 'PAUSED',
    reset: ready && snapshot?.state === 'FAULT',
    estop: true,
    moveChair: ready && snapshot?.mode === 'simulation',
  };
}

export function mapPoint(point: Position, width: number, height: number, origin: MapOrigin = { x: 0, y: 0, yaw: 0 }): Position | null {
  if (![...point, width, height, origin.x, origin.y, origin.yaw].every(Number.isFinite) || width <= 0 || height <= 0) return null;
  const dx = point[0] - origin.x;
  const dy = point[1] - origin.y;
  const cosine = Math.cos(origin.yaw);
  const sine = Math.sin(origin.yaw);
  const localX = cosine * dx + sine * dy;
  const localY = -sine * dx + cosine * dy;
  // Permit floating-point roundoff at a rotated grid boundary, not outside-map geometry.
  const tolerance = Math.max(width, height) * 1e-9;
  if (![localX, localY].every(Number.isFinite) || localX < -tolerance || localX > width + tolerance || localY < -tolerance || localY > height + tolerance) return null;
  return [Math.max(0, Math.min(width, localX)) / width * 800, (1 - Math.max(0, Math.min(height, localY)) / height) * 600];
}
