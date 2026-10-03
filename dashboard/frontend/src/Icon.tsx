export type IconName = 'grid' | 'map' | 'spark' | 'shield' | 'battery' | 'play' | 'pause' | 'reset' | 'stop' | 'arrow' | 'robot' | 'camera' | 'signal' | 'check' | 'activity';
const paths: Record<IconName, string> = {
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
  map: 'm3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2V5m6-2v16m6-14v16',
  spark: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3',
  shield: 'm12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3m-4 9 3 3 5-5',
  battery: 'M3 6h16v12H3zM22 10v4M6 9v6m4-6v6m4-6v6',
  play: 'm8 4 12 8-12 8V4', pause: 'M8 4v16M16 4v16',
  reset: 'M3 10a9 9 0 1 1 2 8M3 3v7h7', stop: 'm8 3-5 5v8l5 5h8l5-5V8l-5-5H8m4 4v6m0 4v1',
  arrow: 'M4 12h16m-6-6 6 6-6 6', robot: 'M12 3v3M6 7h12l3 4v8H3v-8l3-4m1 4v3m10-3v3m-9 3h8',
  camera: 'M3 7h5l2-3h4l2 3h5v13H3V7m12 6a3 3 0 1 0-6 0 3 3 0 0 0 6 0',
  signal: 'M4 18v3M9 14v7m5-12v12m5-17v17', check: 'm4 12 5 5 11-11',
  activity: 'M2 12h5l3-8 4 16 3-8h5',
};
export default function Icon({ name, size = 20 }: { name: IconName; size?: number }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>; }
