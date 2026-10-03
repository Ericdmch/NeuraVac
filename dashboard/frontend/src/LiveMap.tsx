import { mapPoint, metricValue, type Snapshot, type Position } from './telemetry';
import Icon from './Icon';

export default function LiveMap({ snapshot, fresh }: { snapshot: Snapshot | null; fresh: boolean }) {
  const world = snapshot?.world;
  const width = world?.width ?? 0;
  const height = world?.height ?? 0;
  const origin = world?.origin ?? { x: 0, y: 0, yaw: 0 };
  const valid = width > 0 && height > 0;
  const project = (position?: Position) => (position ? mapPoint(position, width, height, origin) : null);
  const robot = snapshot?.pose ? project([snapshot.pose.x, snapshot.pose.y]) : null;
  const path = (snapshot?.path ?? []).map(project);
  const safePath = path.every(point => point !== null);

  return (
    <section className="panel map-panel" id="map" aria-labelledby="map-title">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Spatial intelligence</span>
          <h2 id="map-title">Semantic floor map</h2>
        </div>
        <div className="panel-heading-meta">
          {valid && <span className="dimension-tag">{metricValue(width, 'm')} × {metricValue(height, 'm')}</span>}
          <span className={`badge ${fresh ? 'green' : 'muted'}`}>
            <span className="dot" />
            {fresh ? 'Live map' : 'Awaiting map'}
          </span>
        </div>
      </div>
      <div className="map-canvas">
        {valid ? (
          <svg
            className="floor-map"
            viewBox="-40 -40 880 680"
            role="img"
            aria-label={`Semantic floor map, ${width} by ${height} meters, origin (${origin.x}, ${origin.y}), yaw ${origin.yaw} radians. Robot, planned path, objects and cleaning regions.`}
          >
            <defs>
              <pattern id="floor-grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M40 0H0V40" fill="none" stroke="#e2e8f0" strokeWidth="0.75" />
              </pattern>
              <pattern id="debris-pattern" width="16" height="16" patternUnits="userSpaceOnUse">
                <circle cx="4" cy="4" r="1.5" fill="#d97706" />
                <circle cx="12" cy="12" r="1.5" fill="#d97706" />
              </pattern>
            </defs>
            <rect x="0" y="0" width="800" height="600" rx="8" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="1.5" />
            <rect x="0" y="0" width="800" height="600" rx="8" fill="url(#floor-grid)" />
            <text x="0" y="-17" className="map-axis">{metricValue(width, ' m')}</text>
            <text x="813" y="594" className="map-axis">{metricValue(height, ' m')}</text>
            <text x="400" y="-17" className="map-axis" textAnchor="middle">
              Origin ({metricValue(origin.x)}, {metricValue(origin.y)}) m · yaw {metricValue(origin.yaw)} rad
            </text>
            {(world?.regions ?? []).map(region => {
              const p = project(region.position);
              return p && (
                <g key={region.id}>
                  <title>{`${region.id}: debris ${metricValue(region.debris_score)}, ${region.cleaned ? 'cleaned' : region.reachable === false ? 'unreachable' : 'pending verification'}`}</title>
                  <circle
                    cx={p[0]}
                    cy={p[1]}
                    r="42"
                    fill={region.cleaned ? '#76b90014' : 'url(#debris-pattern)'}
                    stroke={region.cleaned ? '#76b900' : '#f59e0b'}
                    strokeWidth="1.5"
                    strokeDasharray={region.reachable === false ? '4 5' : undefined}
                  />
                  <text x={p[0]} y={p[1] + 61} className="map-label" textAnchor="middle">
                    {region.id}
                  </text>
                  {region.cleaned && (
                    <path
                      d={`M${p[0] - 10} ${p[1]}l7 7 15-15`}
                      fill="none"
                      stroke="#76b900"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  )}
                </g>
              );
            })}
            {(world?.obstacles ?? []).map(obstacle => {
              const p = project([obstacle.x, obstacle.y]);
              return p && (
                <g key={obstacle.id} transform={`translate(${p[0]} ${p[1]})`}>
                  <title>{`${obstacle.id}: geometric obstacle${obstacle.class_name ? `, ${obstacle.class_name}` : ''}`}</title>
                  <circle
                    r={Math.max(5, (obstacle.radius / width) * 800)}
                    fill="#64748b12"
                    stroke="#94a3b8"
                    strokeDasharray="3 4"
                    strokeWidth="1.25"
                  />
                  {(obstacle.class_name === 'chair' || (snapshot?.mode === 'simulation' && obstacle.id === 'chair')) && (
                    <>
                      <rect x="-25" y="-22" width="50" height="44" rx="6" fill="#f1f5f9" stroke="#64748b" strokeWidth="1.5" />
                      <path
                        d="M-29-29h58v13m-51 39v9m44-9v9"
                        fill="none"
                        stroke="#64748b"
                        strokeWidth="3.5"
                        strokeLinecap="round"
                      />
                      <text y="-42" className="map-label" textAnchor="middle">
                        Chair
                      </text>
                    </>
                  )}
                </g>
              );
            })}
            {safePath && path.length > 1 && (
              <polyline
                points={path.map(p => p!.join(',')).join(' ')}
                fill="none"
                stroke="#76b900"
                strokeWidth="2.5"
                strokeDasharray="6 6"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <title>Backend planned path</title>
              </polyline>
            )}
            {(world?.objects ?? []).map(object => {
              const p = project(object.position);
              if (!p) return null;
              const kind = object.class_name.toLowerCase();
              return (
                <g key={object.id} transform={`translate(${p[0]} ${p[1]})`}>
                  <title>{`${object.class_name}: ${object.id}, confidence ${metricValue(object.confidence)}, ${object.traversable === false ? 'avoid' : 'traversability not restricted'}`}</title>
                  {kind.includes('cable') || kind.includes('wire') ? (
                    <>
                      <path
                        d="M-35 5c0-35 26-30 26-8s30 25 25 0 25-29 25-1"
                        fill="none"
                        stroke="#ea580c"
                        strokeWidth="4"
                        strokeLinecap="round"
                      />
                      <rect x="36" y="-10" width="9" height="15" rx="2" fill="#ea580c" />
                    </>
                  ) : kind.includes('chair') ? (
                    <>
                      <rect x="-25" y="-22" width="50" height="44" rx="6" fill="#f1f5f9" stroke="#64748b" strokeWidth="1.5" />
                      <path
                        d="M-29-29h58v13m-51 39v9m44-9v9"
                        fill="none"
                        stroke="#64748b"
                        strokeWidth="3.5"
                        strokeLinecap="round"
                      />
                    </>
                  ) : (
                    <rect
                      x="-18"
                      y="-18"
                      width="36"
                      height="36"
                      rx="6"
                      fill={object.vacuumable ? '#fef3c7' : '#f1f5f9'}
                      stroke={object.vacuumable ? '#d97706' : '#64748b'}
                      strokeWidth="1.5"
                    />
                  )}
                  <text x="0" y="46" className="map-label" textAnchor="middle">
                    {object.class_name.charAt(0).toUpperCase() + object.class_name.slice(1)}
                  </text>
                </g>
              );
            })}
            {robot && (
              <g transform={`translate(${robot[0]} ${robot[1]})`}>
                <title>Robot position from telemetry</title>
                <circle r="36" fill="#76b90012" stroke="#76b90030" strokeWidth="1.5" />
                <circle r="22" fill="#ffffff" stroke="#111827" strokeWidth="2.5" />
                <g transform={`rotate(${-((snapshot?.pose?.yaw ?? 0) - origin.yaw) * 180 / Math.PI})`}>
                  <path d="m8 0-10-6v12Z" fill="#76b900" />
                  <circle cx="-8" cy="0" r="2.5" fill="#111827" />
                </g>
                <text x="0" y="-46" className="map-label robot-label" textAnchor="middle">
                  NEURAVAC
                </text>
              </g>
            )}
          </svg>
        ) : (
          <div className="map-empty">
            <div className="empty-map-icon">
              <Icon name="map" size={32} />
            </div>
            <h3>No map received</h3>
            <p>The robot’s spatial model will appear when telemetry reports map dimensions and SLAM pose.</p>
            <span className="empty-coordinate">MAP FRAME · METRIC GRID</span>
          </div>
        )}
        <div className="map-tag">
          <span className="dot" />
          {snapshot?.mode === 'simulation'
            ? 'Simulation environment'
            : snapshot?.mode === 'hardware'
              ? 'Hardware environment'
              : 'Environment not reported'}
        </div>
      </div>
      <div className="map-legend">
        <span><i className="legend-robot" />Robot position</span>
        <span><i className="legend-path" />Planned path</span>
        <span><i className="legend-dirty" />Debris region</span>
        <span><i className="legend-clean" />Cleaned region</span>
        <span><i className="legend-avoid" />Avoid / obstacle</span>
      </div>
      <div className="map-footnote">
        <Icon name="shield" size={14} />
        <span>Semantic labels guide coverage planning. Real-time safety filters execute locally on edge MCU.</span>
      </div>
    </section>
  );
}
