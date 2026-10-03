import { describe, expect, it } from 'vitest';
import { cloudLabel, controlAvailability, mapPoint, metricValue, parseSnapshot } from './telemetry';

const idle = { mode: 'simulation', mission_id: 'mission-1', state: 'IDLE', connected: true, battery_percent: 86, safety: { safe: true, latched: false, reasons: [] }, world: { width: 8, height: 6 } };

describe('honest telemetry', () => {
  it('does not invent missing metrics or accept nonfinite values', () => {
    expect(metricValue(undefined)).toBe('—');
    expect(metricValue(Number.NaN)).toBe('—');
    expect(metricValue(0)).toBe('0');
    expect(metricValue(51.23, '%')).toBe('51.2%');
  });
  it('preserves small debris scores instead of rounding remaining debris to zero', () => {
    expect(metricValue(0.03)).toBe('0.03');
    expect(metricValue(0.005)).toBe('0.005');
    expect(metricValue(0.00001)).not.toBe('0');
  });
  it('rejects malformed snapshots but accepts missing optional observations', () => {
    expect(parseSnapshot(null)).toBeNull();
    expect(parseSnapshot({ state: 'CLEANING' })).toBeNull();
    expect(parseSnapshot(idle)?.state).toBe('IDLE');
    expect(parseSnapshot({ ...idle, battery_percent: 'broken' })).toBeNull();
  });
  it('accepts explicit null optional metadata from the backend without inventing values', () => {
    const snapshot = parseSnapshot({ ...idle, mission_id: null, cloud: { status: 'offline', model: null, latency_ms: null, request_id: null } });
    expect(snapshot).not.toBeNull();
    expect(snapshot?.cloud?.model).toBeUndefined();
    expect(metricValue(snapshot?.cloud?.latency_ms)).toBe('—');
  });
  it('only describes cloud as active when backend reports it', () => {
    expect(cloudLabel()).toBe('Not reported');
    expect(cloudLabel({ status: 'offline', model: 'Nemotron' })).toBe('Offline · deterministic planning');
    expect(cloudLabel({ status: 'connected', model: 'Nemotron' })).toBe('Connected');
  });
});

describe('control availability', () => {
  it('requires fresh connected healthy idle telemetry to start', () => {
    const snapshot = parseSnapshot(idle)!;
    expect(controlAvailability(snapshot, true, false).start).toBe(true);
    expect(controlAvailability(snapshot, false, false).start).toBe(false);
    expect(controlAvailability({ ...snapshot, connected: false }, true, false).start).toBe(false);
    expect(controlAvailability({ ...snapshot, safety: { safe: false, reasons: ['cliff'], latched: true } }, true, false).start).toBe(false);
    expect(controlAvailability(snapshot, true, true).start).toBe(false);
  });
  it('resumes only a healthy paused mission; never restricts available emergency stop on a safety fault', () => {
    const snapshot = parseSnapshot(idle)!;
    expect(controlAvailability({ ...snapshot, state: 'PAUSED' }, true, false).resume).toBe(true);
    expect(controlAvailability({ ...snapshot, state: 'PAUSED', safety: { safe: false, latched: true } }, true, false).resume).toBe(false);
    expect(controlAvailability({ ...snapshot, safety: { safe: false, latched: true } }, true, true).estop).toBe(true);
    expect(controlAvailability(null, false, false).estop).toBe(true);
  });
  it('prevents simulated chair mutation on hardware and blocks pause in terminal states', () => {
    const snapshot = parseSnapshot(idle)!;
    expect(controlAvailability(snapshot, true, false).moveChair).toBe(true);
    expect(controlAvailability({ ...snapshot, mode: 'hardware' }, true, false).moveChair).toBe(false);
    expect(controlAvailability({ ...snapshot, state: 'CLEANING' }, true, false).pause).toBe(true);
    expect(controlAvailability({ ...snapshot, state: 'COMPLETE' }, true, false).pause).toBe(false);
  });
  it('aligns restart and fault reset with backend transitions', () => {
    const snapshot = parseSnapshot(idle)!;
    expect(controlAvailability({ ...snapshot, state: 'COMPLETE' }, true, false).start).toBe(true);
    expect(controlAvailability(snapshot, true, false).reset).toBe(false);
    expect(controlAvailability({ ...snapshot, state: 'FAULT', safety: { safe: false, latched: true } }, true, false).reset).toBe(true);
    expect(controlAvailability({ ...snapshot, state: 'FAULT' }, false, false).reset).toBe(false);
  });
});

describe('map coordinates', () => {
  it('projects map meters into SVG coordinates and inverts the map y axis', () => {
    expect(mapPoint([0, 0], 8, 6)).toEqual([0, 600]);
    expect(mapPoint([8, 6], 8, 6)).toEqual([800, 0]);
    expect(mapPoint([4, 3], 8, 6)).toEqual([400, 300]);
  });
  it('rejects absent, nonfinite and out of bounds map geometry', () => {
    expect(mapPoint([1, 2], 0, 6)).toBeNull();
    expect(mapPoint([Number.NaN, 2], 8, 6)).toBeNull();
    expect(mapPoint([9, 2], 8, 6)).toBeNull();
  });
  it('projects valid negative map-frame coordinates relative to the SLAM origin', () => {
    const origin = { x: -4, y: -3, yaw: 0 };
    expect(mapPoint([-4, -3], 8, 6, origin)).toEqual([0, 600]);
    expect(mapPoint([0, 0], 8, 6, origin)).toEqual([400, 300]);
    expect(mapPoint([4, 3], 8, 6, origin)).toEqual([800, 0]);
    expect(mapPoint([-4.1, -3], 8, 6, origin)).toBeNull();
  });
  it('applies inverse origin rotation before map projection', () => {
    const point = mapPoint([-1, 7], 8, 6, { x: 2, y: 3, yaw: Math.PI / 2 });
    expect(point?.[0]).toBeCloseTo(400);
    expect(point?.[1]).toBeCloseTo(300);
    const edge = mapPoint([-4, 11], 8, 6, { x: 2, y: 3, yaw: Math.PI / 2 });
    expect(edge?.[0]).toBeCloseTo(800);
    expect(edge?.[1]).toBeCloseTo(0);
  });
  it('validates map origin metadata and rejects invalid projection origins', () => {
    expect(parseSnapshot({ ...idle, world: { width: 8, height: 6, origin: { x: -4, y: -3, yaw: 0 } } })?.world?.origin).toEqual({ x: -4, y: -3, yaw: 0 });
    expect(parseSnapshot({ ...idle, world: { origin: { x: 'bad', y: -3, yaw: 0 } } })).toBeNull();
    expect(mapPoint([0, 0], 8, 6, { x: Number.NaN, y: 0, yaw: 0 })).toBeNull();
  });
});
