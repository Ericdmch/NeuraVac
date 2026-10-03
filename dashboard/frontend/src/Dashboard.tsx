import { cloudLabel, controlAvailability, metricValue, type MissionEvent, type Snapshot } from './telemetry';
import Icon, { type IconName } from './Icon';
import LiveMap from './LiveMap';
import Camera from './Camera';

export interface DashboardProps {
  snapshot: Snapshot | null;
  fresh: boolean;
  pending: string | null;
  error: string | null;
  transport: string;
  ageSeconds: number | null;
  onAction: (action: string) => void;
  token: string;
  onToken: (token: string) => void;
}

const human = (text: string) =>
  text.replaceAll('_', ' ').toLowerCase().replace(/^./, first => first.toUpperCase());

const eventTime = (timestamp?: number | string) =>
  typeof timestamp === 'number'
    ? `t ${metricValue(timestamp, ' s')}`
    : timestamp
      ? /^\d{4}-\d\d-\d\dT/.test(timestamp) && !Number.isNaN(Date.parse(timestamp))
        ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        : timestamp
      : 'Time not reported';

const bounded = (value?: number) => (value === undefined ? 0 : Math.max(0, Math.min(100, value)));

function PrimaryMetric({
  label,
  value,
  unit,
  icon,
  detail,
  percent,
}: {
  label: string;
  value?: number;
  unit?: string;
  icon: IconName;
  detail: string;
  percent?: boolean;
}) {
  return (
    <article className="kpi-hero-cell">
      <div className="kpi-cell-top">
        <span className="kpi-label">{label}</span>
        <span className="kpi-icon-wrap">
          <Icon name={icon} size={15} />
        </span>
      </div>
      <div className="kpi-value-row">
        <strong className="kpi-value">{metricValue(value, unit)}</strong>
      </div>
      {percent && (
        <div className="meter" aria-hidden="true">
          <span style={{ width: `${bounded(value)}%` }} />
        </div>
      )}
      <p className="kpi-detail">{detail}</p>
    </article>
  );
}

function Decision({ event }: { event: MissionEvent }) {
  return (
    <article className="decision">
      <span className="decision-mark">
        <Icon name="spark" size={15} />
      </span>
      <div className="decision-content">
        <div className="decision-heading">
          <strong>{human(event.event)}</strong>
          <time>{eventTime(event.timestamp)}</time>
        </div>
        {event.data && Object.keys(event.data).length > 0 ? (
          <dl className="decision-data">
            {Object.entries(event.data)
              .slice(0, 10)
              .map(([key, value]) => (
                <div key={key}>
                  <dt>{human(key)}</dt>
                  <dd>{typeof value === 'string' ? value : JSON.stringify(value)}</dd>
                </div>
              ))}
          </dl>
        ) : (
          <p>No decision payload reported.</p>
        )}
      </div>
    </article>
  );
}

export default function Dashboard({
  snapshot,
  fresh,
  pending,
  error,
  transport,
  ageSeconds,
  onAction,
  token,
  onToken,
}: DashboardProps) {
  const controls = controlAvailability(snapshot, fresh, pending !== null);
  const state = snapshot?.state;
  const safety = snapshot?.safety;
  const metrics = snapshot?.metrics;
  const events = snapshot?.events ?? [];
  const decisions = events
    .filter(event => /decision|plan|reason|cloud|reject/i.test(event.event))
    .slice(-3)
    .reverse();
  const attempts = (snapshot?.attempts ?? []).slice(-3).reverse();
  const regions = snapshot?.world?.regions ?? [];
  const clean = regions.filter(region => region.cleaned).length;
  const stages = [
    { label: 'Understand', state: ['SCANNING', 'PLANNING', 'REPLANNING'], icon: 'spark' },
    { label: 'Act', state: ['NAVIGATING', 'CLEANING', 'RETRYING'], icon: 'robot' },
    { label: 'Observe', state: ['VERIFYING', 'COMPLETE'], icon: 'check' },
  ] as const;
  const safeStatus = safety?.latched
    ? 'Stop latched'
    : safety?.safe === true
      ? 'Safety clear'
      : safety?.safe === false
        ? 'Safety inhibited'
        : 'Safety not reported';
  const mode =
    snapshot?.mode === 'simulation'
      ? 'Simulation'
      : snapshot?.mode === 'hardware'
        ? 'Hardware'
        : 'Mode not reported';

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to mission control
      </a>
      <aside className="sidebar" aria-label="Dashboard navigation">
        <a className="brand" href="#main" aria-label="NeuraVac home">
          <span className="brand-mark">
            <span className="brand-dot" />
          </span>
          <div className="brand-text">
            <span className="brand-name">
              Neura<span className="brand-light">Vac</span>
            </span>
            <span className="brand-sub">PHYSICAL AI</span>
          </div>
        </a>

        <div className="nav-group">
          <span className="nav-label">WORKSPACE</span>
          <nav>
            <a className="nav-item active" href="#main">
              <Icon name="grid" size={16} />
              <span>Mission control</span>
              <span className="nav-active-bar" />
            </a>
            <a className="nav-item" href="#map">
              <Icon name="map" size={16} />
              <span>Semantic map</span>
            </a>
            <a className="nav-item" href="#intelligence">
              <Icon name="spark" size={16} />
              <span>Intelligence</span>
            </a>
            <a className="nav-item" href="#observations">
              <Icon name="activity" size={16} />
              <span>Observations</span>
            </a>
          </nav>
        </div>

        <div className="sidebar-specs">
          <span className="specs-heading">SYSTEM SPECIFICATION</span>
          <div className="specs-list">
            <div className="spec-row">
              <span>Platform</span>
              <strong>NeuraVac Gen 2</strong>
            </div>
            <div className="spec-row">
              <span>Autonomy loop</span>
              <strong>10 Hz Edge SLAM</strong>
            </div>
            <div className="spec-row">
              <span>Runtime core</span>
              <strong>Physical AI v0.1</strong>
            </div>
          </div>
        </div>

        <div className="sidebar-bottom">
          <span className={`status-indicator ${fresh ? 'online' : 'standby'}`} />
          <div className="sidebar-status-meta">
            <strong>{fresh ? 'Telemetry connected' : 'Awaiting connection'}</strong>
            <small>{transport}</small>
          </div>
          <span className="version">v1.0</span>
        </div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="crumb-sep">/</span>
            <strong>Mission control</strong>
          </div>
          <div className="topbar-status">
            <span className={`badge ${snapshot?.mode === 'simulation' ? 'neutral' : 'accent'}`}>
              {mode}
            </span>
            <span className={`connection-pill ${fresh ? 'is-live' : ''}`}>
              <span className="dot" />
              {fresh ? 'LIVE' : snapshot ? 'STALE' : 'CONNECTING'}
            </span>
          </div>
        </header>

        <main id="main">
          <div className="page-heading">
            <div className="heading-content">
              <span className="eyebrow">NEURAVAC / MISSION CONTROL</span>
              <h1>Mission control</h1>
              <p>Real-time autonomy state, semantic obstacle mapping, and closed-loop verification.</p>
            </div>
            <div className="mission-reference">
              <span className="ref-label">MISSION</span>
              <strong className="ref-id">{snapshot?.mission_id ?? 'Awaiting mission'}</strong>
              <small className="ref-time">
                {ageSeconds === null ? 'No telemetry received' : `Last received ${ageSeconds}s ago`}
              </small>
            </div>
          </div>

          {!snapshot && (
            <div className="notice" role="status">
              <Icon name="signal" size={16} />
              <span>
                <strong>Waiting for telemetry</strong> · Connect the NeuraVac backend to see real mission data.
              </span>
            </div>
          )}

          {snapshot && !fresh && (
            <div className="notice warning" role="status">
              <Icon name="signal" size={16} />
              <span>
                <strong>Telemetry stale</strong> · Displaying the last received snapshot. Mission controls are disabled
                until readings recover.
              </span>
            </div>
          )}

          {error && (
            <div className="notice error" role="alert">
              <Icon name="activity" size={16} />
              <span>{error}</span>
            </div>
          )}

          <section className={`mission-strip ${safety?.latched || safety?.safe === false ? 'inhibited' : ''}`}>
            <div className="mission-state">
              <span className={`state-beacon ${fresh ? 'live' : ''}`} />
              <div>
                <strong>{state ? human(state) : 'Awaiting robot'}</strong>
                <span>
                  {snapshot
                    ? `${mode} mission · ${snapshot.connected ? 'Base connected' : 'Base disconnected'}`
                    : 'Start only after the robot is ready'}
                </span>
              </div>
            </div>

            <div className="mission-pipeline">
              {stages.map((stage, index) => (
                <div
                  key={stage.label}
                  className={stage.state.some(item => item === state) ? 'stage selected' : 'stage'}
                >
                  <Icon name={stage.icon} size={15} />
                  <span>{stage.label}</span>
                  {index < stages.length - 1 && <span className="stage-arrow">→</span>}
                </div>
              ))}
            </div>

            <div className={`safety-status ${safety?.safe && !safety.latched ? 'good' : 'uncertain'}`}>
              <Icon name="shield" size={16} />
              <span>{safeStatus}</span>
            </div>
          </section>

          <section className="kpi-panel" aria-label="Mission KPIs">
            <div className="kpi-primary-group">
              <PrimaryMetric
                label="Cleanliness"
                value={metrics?.cleanliness_percent}
                unit="%"
                icon="spark"
                detail="Backend cleanliness estimate"
                percent
              />
              <PrimaryMetric
                label="Target coverage"
                value={metrics?.coverage_percent}
                unit="%"
                icon="map"
                detail="Fraction of cleaning targets verified"
                percent
              />
            </div>
            <div className="kpi-secondary-group">
              <article className="kpi-sub-cell">
                <div className="kpi-sub-header">
                  <span className="kpi-sub-label">Regions remaining</span>
                  <strong className="kpi-sub-value">{metricValue(metrics?.regions_remaining)}</strong>
                </div>
                <p className="kpi-sub-detail">
                  {snapshot?.world?.regions
                    ? `${clean} of ${regions.length} regions marked cleaned`
                    : 'Awaiting region observations'}
                </p>
              </article>
              <article className="kpi-sub-cell">
                <div className="kpi-sub-header">
                  <span className="kpi-sub-label">Verified passes</span>
                  <strong className="kpi-sub-value">{metricValue(metrics?.successful_passes)}</strong>
                </div>
                <p className="kpi-sub-detail">
                  {metrics?.retried_passes === undefined
                    ? 'Awaiting pass verification'
                    : `${metricValue(metrics.retried_passes)} retried passes reported`}
                </p>
              </article>
            </div>
          </section>

          <div className="primary-grid">
            <LiveMap snapshot={snapshot} fresh={fresh} />

            <div className="control-column">
              <section className="panel robot-panel" aria-labelledby="robot-title">
                <div className="panel-heading compact">
                  <h2 id="robot-title">
                    <Icon name="robot" size={16} />
                    Robot & mission
                  </h2>
                </div>

                <div className="robot-summary">
                  <div className="battery-module">
                    <div className="battery-header">
                      <span className="battery-title">
                        <Icon name="battery" size={16} />
                        Battery
                      </span>
                      <strong className="battery-number">{metricValue(snapshot?.battery_percent, '%')}</strong>
                    </div>
                    <div className="battery-bar" aria-hidden="true">
                      <span style={{ width: `${bounded(snapshot?.battery_percent)}%` }} />
                    </div>
                  </div>
                  <div className="robot-telemetry">
                    <div className="telemetry-pill">
                      <span className={`telemetry-dot ${snapshot?.connected ? 'green' : 'gray'}`} />
                      <span>{snapshot?.connected ? 'Base connected' : snapshot ? 'Base disconnected' : 'Connection not reported'}</span>
                    </div>
                    <div className="telemetry-pill">
                      <span>{snapshot?.self_test?.status ? `Self-test: ${human(snapshot.self_test.status)}` : 'Self-test not reported'}</span>
                    </div>
                  </div>
                </div>

                <div className={`safety-box ${safety?.safe && !safety.latched ? 'clear' : ''}`}>
                  <Icon name="shield" size={18} />
                  <div>
                    <strong>{safeStatus}</strong>
                    <p>
                      {safety?.reasons?.length
                        ? safety.reasons.join(' · ')
                        : safety?.safe === true
                          ? 'No active safety inhibits reported.'
                          : 'Awaiting healthy safety telemetry.'}
                    </p>
                  </div>
                </div>

                <div className="mission-actions">
                  <button
                    className="primary-button"
                    disabled={!controls.start}
                    onClick={() => onAction('start')}
                  >
                    <Icon name="play" size={16} />
                    <span>{pending === 'start' ? 'Starting…' : 'Start mission'}</span>
                    <Icon name="arrow" size={15} />
                  </button>
                  <div className="paired-actions">
                    <button
                      className="secondary-button"
                      disabled={!controls.pause}
                      onClick={() => onAction('pause')}
                    >
                      <Icon name="pause" size={15} />
                      <span>{pending === 'pause' ? 'Pausing…' : 'Pause'}</span>
                    </button>
                    <button
                      className="secondary-button"
                      disabled={!controls.resume}
                      onClick={() => onAction('resume')}
                    >
                      <Icon name="play" size={15} />
                      <span>{pending === 'resume' ? 'Resuming…' : 'Resume'}</span>
                    </button>
                  </div>
                  <button
                    className="reset-button"
                    disabled={!controls.reset}
                    onClick={() => onAction('reset')}
                  >
                    <Icon name="reset" size={14} />
                    <span>{pending === 'reset' ? 'Resetting…' : 'Reset / clear stop'}</span>
                  </button>
                  <button
                    className="estop-button"
                    disabled={pending === 'estop'}
                    onClick={() => onAction('estop')}
                  >
                    <Icon name="stop" size={16} />
                    <span>{pending === 'estop' ? 'Sending emergency stop…' : 'Emergency stop'}</span>
                  </button>
                  <p className="control-hint">
                    Emergency stop latches until a healthy reset.{!fresh && ' Stop delivery requires a reachable backend.'}
                  </p>
                </div>

                {snapshot?.mode === 'simulation' && (
                  <div className="demo-control">
                    <button disabled={!controls.moveChair} onClick={() => onAction('move-chair')}>
                      <Icon name="map" size={15} />
                      <span>{pending === 'move-chair' ? 'Moving chair…' : 'Move chair in simulation'}</span>
                      <Icon name="arrow" size={14} />
                    </button>
                    <p>Introduce an obstacle to observe replanning.</p>
                  </div>
                )}
              </section>

              <section className="panel cloud-panel" id="intelligence" aria-labelledby="cloud-title">
                <div className="panel-heading compact">
                  <h2 id="cloud-title">
                    <Icon name="spark" size={16} />
                    Reasoning engine
                  </h2>
                  <span className="small-label">CLOUD</span>
                </div>
                <strong className="cloud-status">{cloudLabel(snapshot?.cloud)}</strong>
                <dl className="cloud-details">
                  <div>
                    <dt>Model</dt>
                    <dd>{snapshot?.cloud?.model ?? 'Not reported'}</dd>
                  </div>
                  <div>
                    <dt>Latency</dt>
                    <dd>{metricValue(snapshot?.cloud?.latency_ms, ' ms')}</dd>
                  </div>
                  <div>
                    <dt>Request ID</dt>
                    <dd>{snapshot?.cloud?.request_id ?? 'Not reported'}</dd>
                  </div>
                </dl>
                <p>Cloud proposes a decision. The world model validates it; safety remains local.</p>
              </section>
            </div>
          </div>

          <div className="secondary-grid">
            <section className="panel decisions-panel" aria-labelledby="decisions-title">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">Decision trail</span>
                  <h2 id="decisions-title">Autonomy decision log</h2>
                </div>
                <span className="small-label">STRUCTURED EVENTS</span>
              </div>
              {decisions.length ? (
                decisions.map((event, index) => (
                  <Decision key={`${event.event}-${event.timestamp}-${index}`} event={event} />
                ))
              ) : (
                <div className="empty-panel">
                  <Icon name="spark" size={24} />
                  <h3>Decisions will appear here</h3>
                  <p>Planner and cloud events are shown exactly as reported.</p>
                </div>
              )}
            </section>

            <section className="panel observations-panel" id="observations" aria-labelledby="observations-title">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">Closed-loop cleaning</span>
                  <h2 id="observations-title">Cleaning pass verification</h2>
                </div>
                <Icon name="activity" size={18} />
              </div>
              <div className="debris-summary">
                <span className="debris-label">Mission debris score</span>
                <span className="debris-values">
                  Initial <strong>{metricValue(metrics?.initial_debris_score)}</strong>
                  <span className="debris-arrow">→</span>
                  Current <strong>{metricValue(metrics?.current_debris_score)}</strong>
                </span>
              </div>
              {attempts.length ? (
                attempts.map((attempt, index) => (
                  <article className="attempt" key={`${attempt.region_id}-${attempt.pass_number}-${index}`}>
                    <div className="attempt-heading">
                      <strong>
                        {attempt.region_id}
                        <span> / Pass {metricValue(attempt.pass_number)}</span>
                      </strong>
                      <span
                        className={`badge ${attempt.success === true ? 'green' : attempt.success === false ? 'orange' : 'muted'}`}
                      >
                        {attempt.success === true
                          ? 'Verified'
                          : attempt.success === false
                            ? 'Retry needed'
                            : 'Result not reported'}
                      </span>
                    </div>
                    <div className="comparison">
                      <div className="comparison-metric">
                        <span>Before</span>
                        <strong>{metricValue(attempt.before_score)}</strong>
                      </div>
                      <Icon name="arrow" size={18} />
                      <div className="comparison-metric">
                        <span>After</span>
                        <strong>{metricValue(attempt.after_score)}</strong>
                      </div>
                      <div className="improvement">
                        <span>Improvement</span>
                        <strong>{metricValue(attempt.improvement)}</strong>
                      </div>
                    </div>
                    <p>Debris score · Duration {metricValue(attempt.duration_s, ' s')}</p>
                  </article>
                ))
              ) : (
                <div className="empty-panel">
                  <Icon name="check" size={24} />
                  <h3>Every pass needs evidence</h3>
                  <p>Fresh before and after observations will appear after a cleaning pass.</p>
                </div>
              )}
            </section>
          </div>

          <div className="bottom-grid">
            <section className="panel events-panel" aria-labelledby="events-title">
              <div className="panel-heading compact">
                <h2 id="events-title">Mission activity</h2>
                <span className="small-label">{events.length} RECEIVED EVENTS</span>
              </div>
              <div className="event-list">
                {events.length ? (
                  events
                    .slice(-8)
                    .reverse()
                    .map((event, index) => (
                      <div className="event-row" key={`${event.event}-${event.timestamp}-${index}`}>
                        <time>{eventTime(event.timestamp)}</time>
                        <span className="dot" />
                        <strong>{human(event.event)}</strong>
                        {event.data && (
                          <details>
                            <summary>Details</summary>
                            <pre>{JSON.stringify(event.data, null, 2)}</pre>
                          </details>
                        )}
                      </div>
                    ))
                ) : (
                  <p className="event-empty">Awaiting mission events.</p>
                )}
              </div>
            </section>

            <div className="access-column">
              <Camera token={token} simulation={snapshot?.mode === 'simulation'} />
              <details className="panel access-panel">
                <summary>
                  <span>Remote access token</span>
                  <span className="optional-tag">Optional</span>
                </summary>
                <div className="access-body">
                  <label htmlFor="access-token">Backend control token</label>
                  <input
                    id="access-token"
                    type="password"
                    autoComplete="off"
                    placeholder="Bearer token"
                    value={token}
                    onChange={event => onToken(event.target.value)}
                  />
                  <p>Held in this page’s memory. Sent only to this backend.</p>
                </div>
              </details>
            </div>
          </div>

          <footer className="footer">
            <div className="footer-left">
              <span className="footer-mark">N</span>
              <span className="footer-title">NeuraVac</span>
              <span className="footer-sep">/</span>
              <span className="footer-copy">Physical AI Robotics System</span>
            </div>
            <div className="footer-right">
              <span>Supervised Autonomy · Measurable Outcomes</span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
