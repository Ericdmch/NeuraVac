import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import Dashboard, { type DashboardProps } from './Dashboard';
import type { Snapshot } from './telemetry';
const props: DashboardProps = { snapshot: null, fresh: false, pending: null, error: null, transport: 'Connecting', ageSeconds: null, onAction: () => {}, token: '', onToken: () => {} };
const snapshot: Snapshot = { mode: 'simulation', mission_id: 'm1', state: 'CLEANING', connected: true, safety: { safe: true, latched: false }, cloud: { status: 'offline' }, world: { width: 8, height: 6, objects: [{ id: 'c1', class_name: 'cable', position: [2, 3], traversable: false }], regions: [{ id: 'r1', position: [4, 3], cleaned: false, debris_score: 0.8 }] }, pose: { x: 1, y: 1, yaw: 0 }, metrics: { cleanliness_percent: 35 }, attempts: [{ region_id: 'r1', before_score: 0.8, after_score: 0.4, pass_number: 1, success: false }] };
describe('dashboard rendering', () => {
  it('shows a truthful empty state without fabricated telemetry', () => {
    const html = renderToStaticMarkup(<Dashboard {...props} />);
    expect(html).toContain('Waiting for telemetry');
    expect(html).toContain('No map received');
    expect(html).toContain('Start mission');
    expect(html).not.toContain('100%');
  });
  it('renders received map, verified before/after observations and deterministic cloud mode', () => {
    const html = renderToStaticMarkup(<Dashboard {...props} snapshot={snapshot} fresh />);
    expect(html).toContain('Simulation');
    expect(html).toContain('Offline · deterministic planning');
    expect(html).toContain('35%');
    expect(html).toContain('Cable');
    expect(html).toContain('Before');
    expect(html).toContain('After');
    expect(html).toContain('0.8');
    expect(html).toContain('0.4');
    expect(html).toContain('Retry needed');
  });
  it('marks cached telemetry stale and offers only a best-effort emergency stop', () => {
    const html = renderToStaticMarkup(<Dashboard {...props} snapshot={snapshot} error="Connection lost" />);
    expect(html).toContain('Telemetry stale');
    expect(html).toContain('Connection lost');
    expect(html).toContain('Emergency stop');
    expect(html).toMatch(/disabled=""[^>]*>.*?Pause/s);
  });
  it('draws the explicitly identified simulation chair while keeping its detector class', () => {
    const html = renderToStaticMarkup(<Dashboard {...props} snapshot={{ ...snapshot, world: { ...snapshot.world, obstacles: [{ id: 'chair', class_name: 'large_object', x: 3, y: 2, radius: 0.3 }] } }} fresh />);
    expect(html).toContain('Chair');
    expect(html).toContain('large_object');
  });
  it('renders negative-origin robot, hazard, region and planned path in one map frame', () => {
    const html = renderToStaticMarkup(<Dashboard {...props} snapshot={{ ...snapshot, mode: 'hardware', pose: { x: -2, y: -1.5, yaw: 0 }, path: [[-4, -3], [0, 0], [4, 3]], world: { width: 8, height: 6, origin: { x: -4, y: -3, yaw: 0 }, objects: [{ id: 'negative-cable', class_name: 'cable', position: [-3, -2] }], obstacles: [{ id: 'negative-hazard', x: -2, y: -1, radius: 0.3 }], regions: [{ id: 'negative-region', position: [-1, -1] }] } }} fresh />);
    expect(html.includes('translate(200 450)')).toBe(true);
    expect(html.includes('translate(100 500)')).toBe(true);
    const hazardTransform = html.match(/transform="translate\(([^ ]+) ([^)]+)\)"><title>negative-hazard/);
    expect(Number(hazardTransform?.[1])).toBeCloseTo(200);
    expect(Number(hazardTransform?.[2])).toBeCloseTo(400);
    expect(html.includes('negative-region')).toBe(true);
    expect(html.includes('points="0,600 400,300 800,0"')).toBe(true);
  });
  it('labels coverage as target verification rather than whole-floor coverage', () => {
    const html = renderToStaticMarkup(<Dashboard {...props} snapshot={snapshot} fresh />);
    expect(html.includes('Target coverage')).toBe(true);
    expect(html.includes('Fraction of cleaning targets verified')).toBe(true);
    expect(html.includes('reachable floor coverage')).toBe(false);
  });
});
