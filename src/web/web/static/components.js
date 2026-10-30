function Status({ online, children }) {
  return <span className={`connection-status ${online ? 'is-online' : ''}`}>
    <span className="status-dot" />{children || (online ? 'LIVE' : 'OFFLINE')}
  </span>;
}

function useTelemetry() {
  const [telemetry, setTelemetry] = React.useState(null);
  React.useEffect(() => {
    let stopped = false;
    let timer;
    let controller;
    async function update() {
      controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 2500);
      try {
        const response = await fetch('/telemetry', { cache: 'no-store', signal: controller.signal });
        if (!response.ok) throw new Error('Telemetry unavailable');
        const result = await response.json();
        if (!stopped) setTelemetry(result);
      } catch (error) {
        if (!stopped) setTelemetry(null);
      } finally {
        window.clearTimeout(timeout);
        if (!stopped) timer = window.setTimeout(update, 5000);
      }
    }
    update();
    return () => { stopped = true; window.clearTimeout(timer); controller?.abort(); };
  }, []);
  async function requestTelemetry() {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 3000);
    try {
      const response = await fetch('/telemetry/request', {
        method: 'POST', cache: 'no-store', signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
      setTelemetry(result);
    } finally {
      window.clearTimeout(timeout);
    }
  }
  return { telemetry, requestTelemetry };
}

function SensorPanel({ telemetry, onRequestTelemetry }) {
  const [requesting, setRequesting] = React.useState(false);
  const [requestError, setRequestError] = React.useState('');
  const values = telemetry?.online ? telemetry.values : null;
  const percent = values?.battery_percent;
  const flags = [
    ['bump_left', 'Left bumper'], ['bump_right', 'Right bumper'],
    ['cliff_left', 'Cliff left'], ['cliff_front_left', 'Cliff front left'],
    ['cliff_front_right', 'Cliff front right'], ['cliff_right', 'Cliff right'],
    ['wheel_drop_left', 'Left wheel drop'], ['wheel_drop_right', 'Right wheel drop'],
    ['wall', 'Wall'], ['virtual_wall', 'Virtual wall'], ['overcurrent', 'Overcurrent'],
  ];
  const format = (key, unit) => values?.[key] == null ? '—' : `${values[key]}${unit}`;
  async function requestNow() {
    setRequesting(true);
    setRequestError('');
    try { await onRequestTelemetry(); }
    catch (error) { setRequestError(error.message || 'Sensor request failed'); }
    finally { setRequesting(false); }
  }
  return <section className="sensor-panel panel" aria-labelledby="sensor-title">
    <div className="panel-header">
      <div><p className="console-label">ROOMBA / TELEMETRY</p><h2 id="sensor-title">Robot sensors</h2></div>
      <div className="telemetry-actions">
        <button className="telemetry-refresh" type="button" onClick={requestNow} disabled={requesting}>
          {requesting ? 'REQUESTING…' : 'REQUEST NOW'}
        </button>
        <Status online={!!values}>{values ? 'LIVE' : 'NO DATA'}</Status>
      </div>
    </div>
    <div className="sensor-body">
      <div className="battery-heading">
        <div><span className="metric-label">Battery</span><strong>{percent == null ? '—' : `${percent.toFixed(0)}%`}</strong></div>
        <span className="subtle">{values?.charging_state || 'Waiting for sensor response'}</span>
      </div>
      <div className="battery-track"><div style={{ width: `${percent || 0}%` }} /></div>
      <div className="metric-grid">
        <div><span className="metric-label">Voltage</span><span>{format('voltage_v', ' V')}</span></div>
        <div><span className="metric-label">Current</span><span>{format('current_ma', ' mA')}</span></div>
        <div><span className="metric-label">Temperature</span><span>{format('temperature_c', ' °C')}</span></div>
        <div><span className="metric-label">Charge / capacity</span><span>{values ? `${values.charge_mah} / ${values.capacity_mah} mAh` : '—'}</span></div>
      </div>
      <h3 className="section-label">Contact & surroundings</h3>
      <div className="sensor-flags">{flags.map(([key, label]) => (
        <div key={key} className={`sensor-flag ${values ? (values[key] ? 'is-triggered' : 'is-clear') : ''}`}>
          <span>{label}</span><span>{values ? (values[key] ? 'ACTIVE' : 'CLEAR') : '—'}</span>
        </div>
      ))}</div>
      <div className="motion-readings">
        <span>Since last read <b>{format('distance_mm', ' mm')}</b></span>
        <span>Turn <b>{format('angle_deg', '°')}</b></span>
      </div>
      <p className="panel-note">{requestError || (values ? `Updated ${telemetry.age_seconds.toFixed(1)} s ago · display refreshes every 5 s` : 'Waiting for Roomba sensor data…')}</p>
    </div>
  </section>;
}

function SerialConsole({ telemetry }) {
  const [command, setCommand] = React.useState('');
  const [messages, setMessages] = React.useState(['Console ready. Commands are sent through ROS.']);
  const outputRef = React.useRef(null);
  const lastRx = React.useRef(0);
  React.useEffect(() => {
    const entries = (telemetry?.serial_rx || []).filter(entry => entry.id > lastRx.current);
    if (entries.length) {
      lastRx.current = entries[entries.length - 1].id;
      setMessages(current => [...current, ...entries.map(entry => `RX  ${entry.text}`)].slice(-100));
    }
  }, [telemetry]);
  React.useEffect(() => {
    if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
  }, [messages]);

  async function handleSubmit(event) {
    event.preventDefault();
    const text = command.trim();
    if (!text) return;
    try {
      const response = await fetch('/submit', {
        body: JSON.stringify({ data: text }), headers: { 'Content-Type': 'application/json' }, method: 'POST',
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setMessages(current => [...current, `TX  ${text}`].slice(-100));
      setCommand('');
    } catch (error) {
      setMessages(current => [...current, `! Command failed: ${error.message}`].slice(-100));
    }
  }
  return <details className="serial-console panel">
    <summary className="panel-header"><div><p className="console-label">ADVANCED / UART</p><h2>Serial console</h2></div>
      <Status online={!!telemetry?.bridge_connected}>{telemetry?.bridge_connected ? 'ROS LINK' : 'OFFLINE'}</Status>
    </summary>
    <div ref={outputRef} className="serial-output" role="log" aria-label="Serial messages">
      {messages.map((message, index) => <p key={index}>{message}</p>)}
    </div>
    <form className="serial-input" onSubmit={handleSubmit}>
      <label htmlFor="serial-command">SEND COMMAND · DECIMAL BYTES</label>
      <div className="command-row"><span className="command-prompt">&gt;</span>
        <input id="serial-command" value={command} onChange={event => setCommand(event.target.value)}
          placeholder="128 131" autoComplete="off" />
        <button type="submit">SEND</button>
      </div>
    </form>
  </details>;
}

function RemoteOverride() {
  const controls = ['Q', 'W', 'E', 'A', 'S', 'D'];
  const [isEnabled, setIsEnabled] = React.useState(true);
  const [activeKeys, setActiveKeys] = React.useState(new Set());
  const [speed, setSpeed] = React.useState(200);
  const [cleaning, setCleaning] = React.useState({ vacuum: false, side_brush: false, main_brush: false });
  const [cleaningBusy, setCleaningBusy] = React.useState(false);
  const cleaningRef = React.useRef(cleaning);
  cleaningRef.current = cleaning;
  const heldKeys = React.useRef(new Set());
  const pressTimes = React.useRef({});
  const [error, setError] = React.useState('');
  const queue = React.useRef(Promise.resolve());

  async function updateCleaning(patch) {
    const next = { ...cleaningRef.current, ...patch };
    setCleaning(next);
    cleaningRef.current = next;
    setCleaningBusy(true);
    try {
      const response = await fetch('/roomba/cleaning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(next),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
      if (result.cleaning) {
        setCleaning(result.cleaning);
        cleaningRef.current = result.cleaning;
      }
      setError('');
    } catch (err) {
      setError(err.message || 'Unable to update vacuum/cleaning motors.');
    } finally {
      setCleaningBusy(false);
    }
  }

  React.useEffect(() => {
    fetch('/roomba/cleaning')
      .then(res => (res.ok ? res.json() : null))
      .then(data => {
        if (data?.cleaning) {
          setCleaning(data.cleaning);
          cleaningRef.current = data.cleaning;
        }
      })
      .catch(() => {});
  }, []);

  function sendOverride(key, pressed) {
    if (pressed) {
      heldKeys.current.add(key);
      pressTimes.current[key] = performance.now();
    } else {
      heldKeys.current.delete(key);
    }
    setActiveKeys(new Set(heldKeys.current));
    // Keep press/release order and give quick clicks/taps a 250ms drive pulse.
    queue.current = queue.current.catch(() => {}).then(async () => {
      if (!pressed && ! ['Q', 'E'].includes(key)) {
        const elapsed = performance.now() - (pressTimes.current[key] || 0);
        if (elapsed < 250) {
          await new Promise(resolve => window.setTimeout(resolve, 250 - elapsed));
          if (heldKeys.current.has(key)) return;
        }
      }
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 1500);
      try {
        const response = await fetch('/override', {
          signal: controller.signal,
          body: JSON.stringify({ key, pressed }), headers: { 'Content-Type': 'application/json' }, method: 'POST',
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        if (typeof result.speed === 'number') setSpeed(result.speed);
        setError('');
      } catch (error) { setError('Control link unavailable. Check the robot.'); }
      finally { window.clearTimeout(timeout); }
    });
  }
  function releaseAll() {
    if (!heldKeys.current.size) return;
    heldKeys.current.clear();
    setActiveKeys(new Set());
    queue.current = queue.current.catch(() => {}).then(() => fetch('/override/stop', {method: 'POST'})).catch(() => setError('Control link unavailable. Check the robot.'));
  }
  function controlKey(key) {
    return ({ArrowUp:'W', ArrowDown:'S', ArrowLeft:'A', ArrowRight:'D'})[key] || key.toUpperCase();
  }
  React.useEffect(() => {
    function keyDown(event) {
      if (!isEnabled || event.repeat || event.target.closest('input, textarea, select, [contenteditable="true"]')) return;
      const key = controlKey(event.key);
      if (controls.includes(key)) { event.preventDefault(); sendOverride(key, true); }
      else if (key === 'V') { event.preventDefault(); updateCleaning({ vacuum: !cleaningRef.current.vacuum }); }
    }
    function keyUp(event) {
      const key = controlKey(event.key);
      if (heldKeys.current.has(key)) { event.preventDefault(); sendOverride(key, false); }
    }
    function hide() { if (document.hidden) releaseAll(); }
    window.addEventListener('keydown', keyDown);
    window.addEventListener('keyup', keyUp);
    window.addEventListener('blur', releaseAll);
    document.addEventListener('visibilitychange', hide);
    return () => {
      window.removeEventListener('keydown', keyDown); window.removeEventListener('keyup', keyUp);
      window.removeEventListener('blur', releaseAll); document.removeEventListener('visibilitychange', hide);
      releaseAll();
    };
  }, [isEnabled]);

  const anyCleaningActive = cleaning.vacuum || cleaning.main_brush || cleaning.side_brush;
  const allCleaningActive = cleaning.vacuum && cleaning.main_brush && cleaning.side_brush;

  return <section className={`remote-override panel ${isEnabled ? 'is-enabled' : ''}`} aria-labelledby="remote-override-title">
    <div className="panel-header"><div><p className="console-label">MANUAL / KEYBOARD</p><h2 id="remote-override-title">Drive &amp; vacuum controls</h2></div>
      <button className="enable-control" type="button" aria-pressed={isEnabled}
        onClick={() => { releaseAll(); setIsEnabled(current => !current); }}>
        {isEnabled ? 'Disable' : 'Enable'}
      </button>
    </div>
    <div className="control-speed"><span>Command speed</span><strong>{speed} <small>mm/s</small></strong></div>
    <div className="override-controls">{controls.map(key => <button key={key} type="button" disabled={!isEnabled}
      className={`override-key ${activeKeys.has(key) ? 'is-active' : ''}`} aria-label={{Q:'Decrease speed',W:'Forward',E:'Increase speed',A:'Turn left',S:'Reverse',D:'Turn right'}[key]}
      onPointerDown={event => { event.preventDefault(); event.currentTarget.setPointerCapture(event.pointerId); sendOverride(key, true); }}
      onPointerUp={() => sendOverride(key, false)} onPointerCancel={() => sendOverride(key, false)}
      onLostPointerCapture={() => { if (heldKeys.current.has(key)) sendOverride(key, false); }}
      onKeyDown={event => { if (!event.repeat && ['Enter',' '].includes(event.key)) { event.preventDefault(); sendOverride(key, true); } }}
      onKeyUp={event => { if (['Enter',' '].includes(event.key)) { event.preventDefault(); sendOverride(key, false); } }}
      onBlur={() => { if (heldKeys.current.has(key)) sendOverride(key, false); }}>
      <span>{key}</span><small>{{Q:'Slower',W:'Forward',E:'Faster',A:'Left',S:'Reverse',D:'Right'}[key]}</small>
    </button>)}</div>
    <div className="vacuum-controls" aria-label="Vacuum and brush controls">
      <div className="vacuum-header">
        <span className="section-label">VACUUM &amp; CLEANING MOTORS (OPCODE 138)</span>
        <button
          type="button"
          disabled={!isEnabled || cleaningBusy}
          className={`vacuum-master-btn ${anyCleaningActive ? 'is-active' : ''}`}
          onClick={() => {
            const nextState = !allCleaningActive;
            updateCleaning({ vacuum: nextState, main_brush: nextState, side_brush: nextState });
          }}
        >
          {allCleaningActive ? 'STOP ALL MOTORS' : 'ALL MOTORS ON'}
        </button>
      </div>
      <div className="vacuum-grid">
        <button
          type="button"
          disabled={!isEnabled || cleaningBusy}
          aria-pressed={cleaning.vacuum}
          className={`vacuum-btn ${cleaning.vacuum ? 'is-active' : ''}`}
          onClick={() => updateCleaning({ vacuum: !cleaning.vacuum })}
        >
          <span>VACUUM (V)</span>
          <small>{cleaning.vacuum ? 'RUNNING' : 'OFF'}</small>
        </button>
        <button
          type="button"
          disabled={!isEnabled || cleaningBusy}
          aria-pressed={cleaning.main_brush}
          className={`vacuum-btn ${cleaning.main_brush ? 'is-active' : ''}`}
          onClick={() => updateCleaning({ main_brush: !cleaning.main_brush })}
        >
          <span>MAIN BRUSH</span>
          <small>{cleaning.main_brush ? 'RUNNING' : 'OFF'}</small>
        </button>
        <button
          type="button"
          disabled={!isEnabled || cleaningBusy}
          aria-pressed={cleaning.side_brush}
          className={`vacuum-btn ${cleaning.side_brush ? 'is-active' : ''}`}
          onClick={() => updateCleaning({ side_brush: !cleaning.side_brush })}
        >
          <span>SIDE BRUSH</span>
          <small>{cleaning.side_brush ? 'RUNNING' : 'OFF'}</small>
        </button>
      </div>
    </div>
    <p className="panel-note">{error || (isEnabled ? 'Hold WASD/arrows to drive, Q/E for speed, or press V / click to toggle vacuum.' : 'Enable manual control to use WASD, Q/E speed, and vacuum/brush controls.')}</p>
  </section>;
}

function LidarView() {
  const canvasRef = React.useRef(null);
  const scanRef = React.useRef(null);
  const rollingPointsRef = React.useRef([]);
  const viewRef = React.useRef({ zoom: 1, panX: 0, panY: 0 });
  const dragRef = React.useRef(null);
  const [isOnline, setIsOnline] = React.useState(false);
  const [rulerLength, setRulerLength] = React.useState(500);

  function drawLidar(scan = scanRef.current) {
    const canvas = canvasRef.current;
    if (!canvas || !Array.isArray(scan)) {
      return;
    }

    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const size = Math.min(width, height);
    if (!width || !height) {
      return;
    }

    const scale = window.devicePixelRatio || 1;
    const context = canvas.getContext('2d');
    const { zoom, panX, panY } = viewRef.current;
    const radius = size * 0.46 * zoom;
    // Keep a physical scale: nearby returns (like a hand over the sensor)
    // should move toward the robot marker, not get hidden by per-frame scaling.
    const maxRange = 8000;

    if (canvas.width !== Math.round(width * scale) || canvas.height !== Math.round(height * scale)) {
      canvas.width = Math.round(width * scale);
      canvas.height = Math.round(height * scale);
    }
    context.setTransform(scale, 0, 0, scale, 0, 0);
    context.clearRect(0, 0, width, height);
    context.save();
    context.translate(width / 2 + panX, height / 2 + panY);

    // Do not add a grid or circular guide lines to the lidar canvas.
    context.fillStyle = '#2f8cff';
    context.beginPath();
    context.arc(0, 0, 4, 0, Math.PI * 2);
    context.fill();
    context.strokeStyle = '#f8fbff';
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(-9, 0);
    context.lineTo(9, 0);
    context.moveTo(0, -9);
    context.lineTo(0, 9);
    context.stroke();

    scan.forEach((point) => {
      const pointScale = radius / maxRange;
      const x = point.x * pointScale;
      const y = point.y * pointScale;
      context.fillStyle = '#ff8a3d';
      context.fillRect(x - 2, y - 2, 4, 4);
    });
    context.restore();
  }

  React.useEffect(() => {
    let isMounted = true;
    let stream = null;
    let drawScheduled = false;

    function drawRecentPoints() {
      drawScheduled = false;
      if (!isMounted) {
        return;
      }

      const cutoff = performance.now() - 250;
      const recentPoints = rollingPointsRef.current.filter(
        point => point.receivedAt >= cutoff
      );
      rollingPointsRef.current = recentPoints;
      const scan = recentPoints.map(({ x, y }) => ({ x, y }));
      scanRef.current = scan;

      if (scan.length) {
        setRulerLength(4000);
      }
      drawLidar(scan);
      setIsOnline(scan.length > 0);
    }

    function scheduleDraw() {
      if (!drawScheduled) {
        drawScheduled = true;
        window.requestAnimationFrame(drawRecentPoints);
      }
    }

    function connectStream() {
      if (stream || document.hidden || !isMounted) return;
      stream = new EventSource('/lidar/stream');
      stream.onmessage = event => {
        try {
          const batch = JSON.parse(event.data);
          const receivedAt = performance.now();
          const cutoff = receivedAt - 250;
          rollingPointsRef.current = rollingPointsRef.current.filter(
            point => point.receivedAt >= cutoff
          );
          for (const [x, y, ageMs] of batch) {
            rollingPointsRef.current.push({ x, y, receivedAt: receivedAt - ageMs });
          }
          scheduleDraw();
        } catch (error) {
          console.error('Unable to decode LiDAR update.', error);
        }
      };
      stream.onerror = () => {
        if (stream && stream.readyState === EventSource.CLOSED) {
          console.error('LiDAR event stream closed.');
        }
      };
    }

    function closeStream() {
      if (stream) {
        stream.close();
        stream = null;
      }
    }

    function handleVisibility() {
      if (document.hidden) closeStream();
      else connectStream();
    }

    connectStream();
    document.addEventListener('visibilitychange', handleVisibility);
    window.addEventListener('pagehide', closeStream);

    const expiryTimer = window.setInterval(() => {
      const points = rollingPointsRef.current;
      if (points.length && performance.now() - points[points.length - 1].receivedAt >= 250) {
        scheduleDraw();
      }
    }, 50);

    return () => {
      isMounted = false;
      closeStream();
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('pagehide', closeStream);
      window.clearInterval(expiryTimer);
    };
  }, []);

  React.useEffect(() => {
    function handleResize() {
      drawLidar();
    }

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return undefined;
    }

    canvas.addEventListener('wheel', handleWheel, { passive: false });
    return () => canvas.removeEventListener('wheel', handleWheel);
  }, []);

  function handleWheel(event) {
    event.preventDefault();
    event.stopPropagation();
    const direction = event.deltaY < 0 ? 1.1 : 0.9;
    viewRef.current.zoom = Math.min(5, Math.max(0.5, viewRef.current.zoom * direction));
    if (Array.isArray(scanRef.current)) {
      setRulerLength(Math.round(
        Math.max(...scanRef.current.map((point) => Math.hypot(point.x, point.y)), 1)
        / (2 * viewRef.current.zoom)
      ));
    }
    drawLidar();
  }

  function handlePointerDown(event) {
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      panX: viewRef.current.panX,
      panY: viewRef.current.panY,
    };
  }

  function handlePointerMove(event) {
    if (!dragRef.current) {
      return;
    }
    const drag = dragRef.current;
    const canvas = canvasRef.current;
    const size = canvas ? Math.min(canvas.clientWidth, canvas.clientHeight) : 0;
    const radius = size * 0.46 * viewRef.current.zoom;
    const panLimit = Math.max(0, radius - size / 2 + 6);
    viewRef.current.panX = Math.min(
      panLimit,
      Math.max(-panLimit, drag.panX + event.clientX - drag.startX)
    );
    viewRef.current.panY = Math.min(
      panLimit,
      Math.max(-panLimit, drag.panY + event.clientY - drag.startY)
    );
    drawLidar();
  }

  function handlePointerUp(event) {
    if (dragRef.current?.pointerId === event.pointerId) {
      dragRef.current = null;
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  return (
    <section className="lidar-view" aria-labelledby="lidar-view-title">
      <div className="lidar-header">
        <div>
          <p className="console-label">SENSOR FEED / 360° SCAN</p>
          <h2 id="lidar-view-title">Lidar View</h2>
        </div>
        <span className={`connection-status ${isOnline ? 'is-online' : ''}`}>
          <span className="status-dot" />
          {isOnline ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>
      <div className="lidar-canvas-wrap">
        <canvas
          ref={canvasRef}
          aria-label="Lidar scan visualization"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
        />
        <div className="lidar-ruler" aria-label={`${rulerLength} millimeter scale`}>
          <span className="ruler-line" />
          <span>{isOnline ? `${rulerLength} mm` : 'No scan'}</span>
        </div>
      </div>
    </section>
  );
}

function SlamMapView() {
  const canvasRef = React.useRef(null);
  const latestMapRef = React.useRef(null);
  const mapCacheRef = React.useRef({ key: null, cells: null, minX: 0, minY: 0, maxX: -1, maxY: -1, distSqGrid: null, cropKey: null });
  const autonomyRef = React.useRef({
    state: null, costmap: null, path: null, pose: null, motion_enabled: false,
    config: { buffer_zone_radius_m: 0.10, inflation_radius_m: 0.18, high_cost_threshold: 99, show_costmap_by_default: true },
  });
  const selectedRef = React.useRef(null);
  const viewBoundsRef = React.useRef(null);
  const showCostmapRef = React.useRef(true);
  const clickToMoveRef = React.useRef(true);
  const configLoadedRef = React.useRef(false);

  const [status, setStatus] = React.useState('WAITING FOR MAP');
  const [resetting, setResetting] = React.useState(false);
  const [resetError, setResetError] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [saveMessage, setSaveMessage] = React.useState('');
  const [selectedTarget, setSelectedTarget] = React.useState(null);
  const [showCostmap, setShowCostmap] = React.useState(true);
  const [clickToMove, setClickToMove] = React.useState(true);
  const [autonomySnap, setAutonomySnap] = React.useState(autonomyRef.current);
  const [missionNote, setMissionNote] = React.useState('');

  function isCellInBuffer(map, cells, cellX, cellY, costmap, cfg) {
    const res = map.resolution || 0.05;
    const bufferRadiusM = cfg?.buffer_zone_radius_m ?? 0.10;
    const highCostThreshold = cfg?.high_cost_threshold ?? 99;
    if (costmap && costmap.dataBytes) {
      const wx = map.origin_x + (cellX + 0.5) * res;
      const wy = map.origin_y + (cellY + 0.5) * res;
      const cx = Math.floor((wx - costmap.origin_x) / costmap.resolution);
      const cy = Math.floor((wy - costmap.origin_y) / costmap.resolution);
      if (cx >= 0 && cy >= 0 && cx < costmap.width && cy < costmap.height) {
        const cv = costmap.dataBytes[cy * costmap.width + cx];
        if (cv !== 255 && cv >= highCostThreshold) return true;
      }
    }
    const rCells = Math.ceil(bufferRadiusM / res);
    const r2 = (bufferRadiusM / res) * (bufferRadiusM / res);
    for (let dy = -rCells; dy <= rCells; dy += 1) {
      const ny = cellY + dy;
      if (ny < 0 || ny >= map.height) continue;
      for (let dx = -rCells; dx <= rCells; dx += 1) {
        if (dx * dx + dy * dy > r2) continue;
        const nx = cellX + dx;
        if (nx < 0 || nx >= map.width) continue;
        const v = cells[ny * map.width + nx];
        if (v >= 75 && v !== 255) return true;
      }
    }
    return false;
  }

  const redrawRef = React.useRef(() => {});

  async function saveMap() {
    setSaving(true);
    setSaveMessage('');
    try {
      const response = await fetch('/slam/save', { method: 'POST' });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Unable to save map.');
      setSaveMessage(result.message || 'Map saved.');
    } catch (error) {
      setSaveMessage(error.message);
    } finally {
      setSaving(false);
    }
  }

  async function resetMap() {
    setResetting(true);
    setResetError('');
    try {
      const response = await fetch('/slam/reset', { method: 'POST' });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Unable to reset map.');
      setStatus('RESET · WAITING FOR SCANS');
    } catch (error) {
      setResetError(error.message);
    } finally {
      setResetting(false);
    }
  }

  async function sendMission(command, targetOverride = null) {
    setMissionNote('');
    const body = { command };
    if (command === 'start' || command === 'goto') {
      const target = targetOverride || selectedRef.current;
      if (!target) {
        setMissionNote('Click a free cell (outside the red buffer zone) on the map first.');
        return;
      }
      body.return_goal = target;
    }
    try {
      const response = await fetch('/autonomy/mission', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Mission request failed.');
      if (command === 'goto' && body.return_goal) {
        setMissionNote(`Moving to (${body.return_goal[0].toFixed(2)}, ${body.return_goal[1].toFixed(2)}) m via Nav2…`);
      } else {
        setMissionNote(result.message || `Sent ${command}.`);
      }
    } catch (error) {
      setMissionNote(error.message);
    }
  }

  async function toggleMotion() {
    const next = !autonomyRef.current.motion_enabled;
    try {
      const response = await fetch('/autonomy/motion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: next }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Unable to toggle motion.');
      autonomyRef.current = { ...autonomyRef.current, motion_enabled: next };
      setAutonomySnap({ ...autonomyRef.current });
      setMissionNote(result.message);
    } catch (error) {
      setMissionNote(error.message);
    }
  }

  function handleCanvasClick(event) {
    const map = latestMapRef.current;
    const bounds = viewBoundsRef.current;
    const canvas = canvasRef.current;
    if (!map || !bounds || !canvas || !map.cells) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / Math.max(1, rect.width);
    const scaleY = canvas.height / Math.max(1, rect.height);
    // Canvas uses translate(width, 0) + scale(-1, 1), so reverse X from rect.right
    const px = (rect.right - event.clientX) * scaleX;
    const py = (event.clientY - rect.top) * scaleY;
    const cellX = Math.floor(bounds.minX + (px - bounds.left) / bounds.fit);
    const cellY = Math.floor(bounds.minY + (py - bounds.top) / bounds.fit);
    if (cellX < 0 || cellY < 0 || cellX >= map.width || cellY >= map.height) return;
    const { costmap, config } = autonomyRef.current;
    let targetCellX = cellX;
    let targetCellY = cellY;
    let snapped = false;
    function isTraversable(cx, cy) {
      if (cx < 0 || cy < 0 || cx >= map.width || cy >= map.height) return false;
      const v = map.cells[cy * map.width + cx];
      // Allow both known free space (0..55) and grey unexplored space (255),
      // as long as the cell is not a wall (75..100) or inside the red wall buffer.
      if (v !== 255 && v >= 55) return false;
      if (isCellInBuffer(map, map.cells, cx, cy, costmap, config)) return false;
      return true;
    }
    if (!isTraversable(targetCellX, targetCellY)) {
      let best = null;
      let bestD2 = 1e9;
      for (let rad = 1; rad <= 20; rad += 1) {
        for (let dy = -rad; dy <= rad; dy += 1) {
          for (let dx = -rad; dx <= rad; dx += 1) {
            const d2 = dx * dx + dy * dy;
            if (d2 >= bestD2) continue;
            if (isTraversable(cellX + dx, cellY + dy)) {
              best = [cellX + dx, cellY + dy];
              bestD2 = d2;
            }
          }
        }
        if (best) break;
      }
      if (!best) {
        setMissionNote('That area is completely blocked by walls. Click closer to open space.');
        return;
      }
      [targetCellX, targetCellY] = best;
      snapped = true;
    }
    const worldX = map.origin_x + (targetCellX + 0.5) * map.resolution;
    const worldY = map.origin_y + (targetCellY + 0.5) * map.resolution;
    const pt = [Number(worldX.toFixed(3)), Number(worldY.toFixed(3))];
    selectedRef.current = pt;
    setSelectedTarget(pt);
    redrawRef.current();
    if (clickToMoveRef.current) {
      sendMission('goto', pt);
      if (snapped) {
        setMissionNote(`Snapped outside wall buffer → moving to (${pt[0].toFixed(2)}, ${pt[1].toFixed(2)}) m…`);
      }
    } else {
      setMissionNote(`Target selected: (${pt[0].toFixed(2)}, ${pt[1].toFixed(2)}) m — click GO TO POINT or AUTO-MAP.`);
    }
  }

  React.useEffect(() => {
    let stopped = false;
    let timer;
    let lastCostmapB64 = null;
    let lastCostmapBytes = null;
    async function pollAutonomy() {
      if (!document.hidden) {
        try {
          const res = await fetch('/autonomy/state', { cache: 'no-store' });
          if (res.ok) {
            const data = await res.json();
            if (data.costmap && data.costmap.data) {
              if (data.costmap.data === lastCostmapB64 && lastCostmapBytes) {
                data.costmap.dataBytes = lastCostmapBytes;
              } else {
                const bin = atob(data.costmap.data);
                const arr = new Uint8Array(bin.length);
                for (let i = 0; i < bin.length; i += 1) arr[i] = bin.charCodeAt(i);
                lastCostmapB64 = data.costmap.data;
                lastCostmapBytes = arr;
                data.costmap.dataBytes = arr;
              }
            }
            if (!configLoadedRef.current && data.config) {
              configLoadedRef.current = true;
              const defShow = data.config.show_costmap_by_default ?? true;
              showCostmapRef.current = defShow;
              setShowCostmap(defShow);
            }
            autonomyRef.current = data;
            if (!stopped) {
              setAutonomySnap(data);
              redrawRef.current();
            }
          }
        } catch (_) {}
      }
      if (!stopped) timer = window.setTimeout(pollAutonomy, 800);
    }
    pollAutonomy();
    return () => { stopped = true; window.clearTimeout(timer); };
  }, []);

  React.useEffect(() => {
    let isMounted = true;
    let stream = null;
    function drawMap(map) {
      const canvas = canvasRef.current;
      if (!canvas || !map) return false;
      const context = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
      const width = canvas.width = Math.max(1, canvas.clientWidth * dpr);
      const height = canvas.height = Math.max(1, canvas.clientHeight * dpr);
      context.fillStyle = '#0b121c'; context.fillRect(0, 0, width, height);

      const cache = mapCacheRef.current;
      const mapKey = `${map.width}x${map.height}:${map.data}`;
      if (cache.key !== mapKey) {
        const binary = atob(map.data);
        const cells = new Uint8Array(binary.length);
        let cMinX = map.width, cMinY = map.height, cMaxX = -1, cMaxY = -1;
        for (let i = 0; i < binary.length; i += 1) {
          cells[i] = binary.charCodeAt(i);
          if (cells[i] !== 255) {
            const x = i % map.width, y = Math.floor(i / map.width);
            if (x < cMinX) cMinX = x;
            if (y < cMinY) cMinY = y;
            if (x > cMaxX) cMaxX = x;
            if (y > cMaxY) cMaxY = y;
          }
        }
        cache.key = mapKey;
        cache.cells = cells;
        cache.minX = cMinX;
        cache.minY = cMinY;
        cache.maxX = cMaxX;
        cache.maxY = cMaxY;
        cache.distSqGrid = null;
        cache.cropKey = null;
      }

      const cells = cache.cells;
      map.cells = cells;
      let minX = cache.minX, minY = cache.minY, maxX = cache.maxX, maxY = cache.maxY;

      const poseSnap = autonomyRef.current?.pose;
      const rxWorld = map.robot_x ?? (poseSnap ? poseSnap[0] : 0);
      const ryWorld = map.robot_y ?? (poseSnap ? poseSnap[1] : 0);
      const ryawWorld = map.robot_yaw ?? (poseSnap && poseSnap.length > 2 ? poseSnap[2] : 0);
      let robotX = (rxWorld - map.origin_x) / map.resolution;
      let robotY = (ryWorld - map.origin_y) / map.resolution;
      const hasRobotPose = robotX >= 0 && robotY >= 0 && robotX < map.width && robotY < map.height;
      if (hasRobotPose) {
        if (maxX < 0) {
          minX = Math.max(0, Math.floor(robotX) - 20);
          maxX = Math.min(map.width - 1, Math.ceil(robotX) + 20);
          minY = Math.max(0, Math.floor(robotY) - 20);
          maxY = Math.min(map.height - 1, Math.ceil(robotY) + 20);
        } else {
          minX = Math.min(minX, Math.floor(robotX));
          maxX = Math.max(maxX, Math.ceil(robotX));
          minY = Math.min(minY, Math.floor(robotY));
          maxY = Math.max(maxY, Math.ceil(robotY));
        }
      }
      if (maxX < 0) return false;
      const margin = 8;
      minX = Math.max(0, minX - margin); minY = Math.max(0, minY - margin);
      maxX = Math.min(map.width - 1, maxX + margin); maxY = Math.min(map.height - 1, maxY + margin);
      const cropWidth = maxX - minX + 1, cropHeight = maxY - minY + 1;
      const fit = Math.min(width / cropWidth, height / cropHeight);
      const drawWidth = cropWidth * fit, drawHeight = cropHeight * fit;
      const left = (width - drawWidth) / 2, top = (height - drawHeight) / 2;
      viewBoundsRef.current = { minX, minY, maxX, maxY, fit, left, top };

      const { costmap, path, state, config } = autonomyRef.current;
      const showCost = showCostmapRef.current;
      const res = map.resolution || 0.05;
      const bufferRadiusM = config?.buffer_zone_radius_m ?? 0.10;
      const inflationRadiusM = config?.inflation_radius_m ?? 0.18;
      const highCostThreshold = config?.high_cost_threshold ?? 99;

      // Precompute local distance-squared to nearest wall in crop ONLY when map or crop changes
      let distSqGrid = null;
      if (showCost) {
        const cropKey = `${mapKey}|${minX},${minY},${cropWidth},${cropHeight}|${inflationRadiusM}`;
        if (cache.cropKey === cropKey && cache.distSqGrid) {
          distSqGrid = cache.distSqGrid;
        } else {
          const maxCells = Math.ceil(inflationRadiusM / res);
          distSqGrid = new Float32Array(cropWidth * cropHeight);
          distSqGrid.fill(1e9);
          for (let y = 0; y < cropHeight; y += 1) {
            for (let x = 0; x < cropWidth; x += 1) {
              const v = cells[(minY + y) * map.width + minX + x];
              if (v >= 75 && v !== 255) {
                for (let dy = -maxCells; dy <= maxCells; dy += 1) {
                  const ny = y + dy;
                  if (ny < 0 || ny >= cropHeight) continue;
                  for (let dx = -maxCells; dx <= maxCells; dx += 1) {
                    const nx = x + dx;
                    if (nx < 0 || nx >= cropWidth) continue;
                    const d2 = (dx * dx + dy * dy) * res * res;
                    const idx = ny * cropWidth + nx;
                    if (d2 < distSqGrid[idx]) distSqGrid[idx] = d2;
                  }
                }
              }
            }
          }
          cache.cropKey = cropKey;
          cache.distSqGrid = distSqGrid;
        }
      }

      const bufSq = bufferRadiusM * bufferRadiusM;
      const infSq = inflationRadiusM * inflationRadiusM;
      const image = context.createImageData(cropWidth, cropHeight);
      for (let y = 0; y < cropHeight; y += 1) {
        for (let x = 0; x < cropWidth; x += 1) {
          const gx = minX + x, gy = minY + y;
          const value = cells[gy * map.width + gx];
          const offset = (y * cropWidth + x) * 4;
          if (value === 255) {
            image.data.set([17, 27, 39, 255], offset);
          } else if (value >= 75) {
            image.data.set([255, 138, 61, 255], offset);
          } else if (value >= 40) {
            image.data.set([186, 133, 93, 235], offset);
          } else {
            let r = 38, g = 56, b = 74;
            if (showCost) {
              let cv = 0;
              if (costmap && costmap.dataBytes) {
                const wx = map.origin_x + (gx + 0.5) * res;
                const wy = map.origin_y + (gy + 0.5) * res;
                const cx = Math.floor((wx - costmap.origin_x) / costmap.resolution);
                const cy = Math.floor((wy - costmap.origin_y) / costmap.resolution);
                if (cx >= 0 && cy >= 0 && cx < costmap.width && cy < costmap.height) {
                  const raw = costmap.dataBytes[cy * costmap.width + cx];
                  if (raw !== 255) cv = raw;
                }
              }
              const d2 = distSqGrid ? distSqGrid[y * cropWidth + x] : 1e9;
              if (cv >= highCostThreshold || d2 <= bufSq) {
                // Red high-cost buffer zone
                r = 205; g = 58; b = 62;
              } else if (cv > 0 || d2 <= infSq) {
                const t = cv > 0 ? (cv / highCostThreshold) : Math.max(0, 1 - (Math.sqrt(d2) - bufferRadiusM) / Math.max(0.01, inflationRadiusM - bufferRadiusM));
                r = Math.round(38 + 115 * t);
                g = Math.round(56 + 32 * t);
                b = Math.round(74 - 24 * t);
              }
            }
            image.data.set([r, g, b, 255], offset);
          }
        }
      }
      const layer = document.createElement('canvas');
      layer.width = cropWidth; layer.height = cropHeight;
      layer.getContext('2d').putImageData(image, 0, 0);
      context.imageSmoothingEnabled = false;
      context.save();
      context.translate(width, 0);
      context.scale(-1, 1);
      context.drawImage(layer, left, top, drawWidth, drawHeight);

      function worldToCanvas(wx, wy) {
        const cx = (wx - map.origin_x) / map.resolution;
        const cy = (wy - map.origin_y) / map.resolution;
        return [left + (cx - minX) * fit, top + (cy - minY) * fit];
      }

      if (Array.isArray(path) && path.length > 1) {
        context.strokeStyle = '#66d6a4';
        context.lineWidth = 2.5 * dpr;
        context.beginPath();
        path.forEach(([wx, wy], idx) => {
          const [px, py] = worldToCanvas(wx, wy);
          if (idx === 0) context.moveTo(px, py);
          else context.lineTo(px, py);
        });
        context.stroke();
      }

      if (state?.current_goal && Array.isArray(state.current_goal)) {
        const [gx, gy] = worldToCanvas(state.current_goal[0], state.current_goal[1]);
        context.fillStyle = '#66d6a4';
        context.beginPath();
        context.arc(gx, gy, 4.5 * dpr, 0, Math.PI * 2);
        context.fill();
      }

      if (selectedRef.current) {
        const [sx, sy] = worldToCanvas(selectedRef.current[0], selectedRef.current[1]);
        context.strokeStyle = '#ffb040';
        context.lineWidth = 2 * dpr;
        context.beginPath();
        context.arc(sx, sy, 7 * dpr, 0, Math.PI * 2);
        context.stroke();
        context.fillStyle = '#ffb040';
        context.beginPath();
        context.arc(sx, sy, 3.5 * dpr, 0, Math.PI * 2);
        context.fill();
      }

      if (hasRobotPose && robotX >= minX && robotX <= maxX && robotY >= minY && robotY <= maxY) {
        const markerX = left + (robotX - minX) * fit;
        const markerY = top + (robotY - minY) * fit;
        context.fillStyle = '#63b3ff'; context.beginPath();
        context.arc(markerX, markerY, 5 * dpr, 0, Math.PI * 2);
        context.fill();
        const heading = ryawWorld;
        const length = 19 * dpr;
        context.save();
        context.translate(markerX, markerY);
        context.rotate(heading);
        context.strokeStyle = '#63b3ff';
        context.lineWidth = 2.5 * dpr;
        context.beginPath();
        context.moveTo(0, 0); context.lineTo(length, 0);
        context.moveTo(length - 6 * dpr, -5 * dpr);
        context.lineTo(length, 0);
        context.lineTo(length - 6 * dpr, 5 * dpr);
        context.stroke();
        context.restore();
      }
      context.restore();
      return true;
    }

    redrawRef.current = () => {
      if (latestMapRef.current) drawMap(latestMapRef.current);
    };

    function connectStream() {
      if (stream || document.hidden || !isMounted) return;
      stream = new EventSource('/slam/map/stream');
      stream.onmessage = event => {
        try {
          latestMapRef.current = JSON.parse(event.data);
          setStatus(drawMap(latestMapRef.current) ? (latestMapRef.current.tracking_status || 'TRACKING') : 'WAITING FOR SCANS');
        }
        catch (error) { console.error('Unable to decode LiDAR map.', error); }
      };
      stream.onerror = () => setStatus('WAITING FOR MAP');
    }

    function closeStream() {
      if (stream) {
        stream.close();
        stream = null;
      }
    }

    function handleVisibility() {
      if (document.hidden) closeStream();
      else connectStream();
    }

    connectStream();
    document.addEventListener('visibilitychange', handleVisibility);
    window.addEventListener('pagehide', closeStream);
    const resize = () => { if (latestMapRef.current) drawMap(latestMapRef.current); };
    window.addEventListener('resize', resize);
    return () => {
      isMounted = false;
      closeStream();
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('pagehide', closeStream);
      window.removeEventListener('resize', resize);
    };
  }, []);

  const mState = autonomySnap?.state?.state || 'idle';
  const mReason = autonomySnap?.state?.reason || '';
  const isBusy = mState === 'exploring' || mState === 'returning';
  const bufRadius = autonomySnap?.config?.buffer_zone_radius_m ?? 0.10;

  return <section className="lidar-view slam-map-view" aria-labelledby="slam-map-title">
    <div className="lidar-header">
      <div>
        <p className="console-label">SLAM TOOLBOX + NAV2 COSTMAP · {mState.toUpperCase()}</p>
        <h2 id="slam-map-title">Room map &amp; autonomous navigation</h2>
      </div>
      <div className="slam-map-actions">
        <button className={`telemetry-refresh ${clickToMove ? 'is-active-toggle' : ''}`} type="button"
          onClick={() => { clickToMoveRef.current = !clickToMove; setClickToMove(!clickToMove); }}>
          {clickToMove ? 'CLICK-TO-MOVE: ON' : 'CLICK-TO-MOVE: OFF'}
        </button>
        <button className={`telemetry-refresh ${showCostmap ? 'is-active-toggle' : ''}`} type="button"
          onClick={() => { showCostmapRef.current = !showCostmap; setShowCostmap(!showCostmap); redrawRef.current(); }}>
          {showCostmap ? `BUFFER ON (${bufRadius}m)` : 'BUFFER OFF'}
        </button>
        <button className={`telemetry-refresh ${autonomySnap?.motion_enabled ? 'is-armed-toggle' : ''}`} type="button" onClick={toggleMotion}>
          {autonomySnap?.motion_enabled ? 'MOTION ENABLED' : 'MOTION LOCKED'}
        </button>
        <button className="telemetry-refresh" type="button" onClick={saveMap} disabled={saving}>
          {saving ? 'SAVING…' : 'SAVE MAP'}
        </button>
        <button className="telemetry-refresh" type="button" onClick={resetMap} disabled={resetting}>
          {resetting ? 'RESETTING…' : 'RESET & REMAP'}
        </button>
        <span className={`connection-status ${status === 'WAITING FOR MAP' ? '' : 'is-online'}`}><span className="status-dot" />{status}</span>
      </div>
    </div>
    <div className="autonomy-ActionBar">
      <button className="autonomy-btn goto-btn" type="button" disabled={!selectedTarget || isBusy} onClick={() => sendMission('goto')}>
        GO TO POINT
      </button>
      <button className="autonomy-btn start-btn" type="button" disabled={!selectedTarget || isBusy} onClick={() => sendMission('start')}>
        AUTO-MAP ROOM
      </button>
      <button className="autonomy-btn return-btn" type="button" disabled={mState !== 'exploring'} onClick={() => sendMission('return')}>
        END &amp; RETURN
      </button>
      <button className="autonomy-btn stop-btn" type="button" onClick={() => sendMission('stop')}>
        STOP
      </button>
      <span className="autonomy-target-readout">
        {selectedTarget ? `Target: (${selectedTarget[0].toFixed(2)}, ${selectedTarget[1].toFixed(2)}) m` : 'Click any clear cell on the map to set target'}
      </span>
    </div>
    <div className="slam-map-canvas-wrap">
      <canvas ref={canvasRef} onClick={handleCanvasClick} style={{ cursor: 'crosshair' }} aria-label="LiDAR-built room occupancy map; click to select navigation target" />
    </div>
    <p className="panel-note slam-map-note">
      {missionNote || mReason || saveMessage || resetError || `Click map to place target (gold) · Red = ${bufRadius} m obstacle buffer zone · Green = Nav2 path · Blue = robot pose.`}
    </p>
  </section>;
}

function CameraView() {
  const [frameUrl, setFrameUrl] = React.useState(null);
  const [isOnline, setIsOnline] = React.useState(false);

  React.useEffect(() => {
    let stopped = false;
    let timer;
    let currentUrl;
    const controller = new AbortController();

    async function updateFrame() {
      try {
        const response = await fetch('/camera/frame', {
          cache: 'no-store', signal: controller.signal,
        });
        if (!response.ok) throw new Error('Camera offline');
        const blob = await response.blob();
        if (stopped) return;
        const nextUrl = URL.createObjectURL(blob);
        const previousUrl = currentUrl;
        currentUrl = nextUrl;
        setFrameUrl(nextUrl);
        setIsOnline(true);
        if (previousUrl) URL.revokeObjectURL(previousUrl);
      } catch (error) {
        if (stopped) return;
        setIsOnline(false);
        setFrameUrl(null);
        if (currentUrl) URL.revokeObjectURL(currentUrl);
        currentUrl = null;
      }
      if (!stopped) timer = window.setTimeout(updateFrame, 100);
    }

    updateFrame();
    return () => {
      stopped = true;
      controller.abort();
      window.clearTimeout(timer);
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, []);

  return (
    <section className="camera-view" aria-labelledby="camera-view-title">
      <div className="lidar-header">
        <div>
          <p className="console-label">LIVE FEED / USB CAMERA</p>
          <h2 id="camera-view-title">Camera</h2>
        </div>
        <span className={`connection-status ${isOnline ? 'is-online' : ''}`}>
          <span className="status-dot" />
          {isOnline ? 'LIVE' : 'OFFLINE'}
        </span>
      </div>
      <div className="camera-frame">
        {frameUrl ? <img src={frameUrl} alt="Live view from the robot camera" /> : (
          <p role="status">Camera unavailable. Reconnecting…</p>
        )}
      </div>
    </section>
  );
}

function RoombaEffects() {
  const [color, setColor] = React.useState(0);
  const [intensity, setIntensity] = React.useState(180);
  const [songNumber, setSongNumber] = React.useState(0);
  const [notesText, setNotesText] = React.useState('C4:24 E4:24 G4:24 C5:48');
  const [status, setStatus] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const hue = 120 - (color * 120 / 255);

  async function send(path, body) {
    setBusy(true);
    setStatus('');
    try {
      const response = await fetch(path, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
      setStatus('Command sent');
    } catch (error) { setStatus(error.message || 'Roomba command failed'); }
    finally { setBusy(false); }
  }

  function playSong(event) {
    event.preventDefault();
    const names = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
    const tokens = notesText.trim().split(/\s+/).filter(Boolean);
    if (!tokens.length || tokens.length > 16) {
      setStatus('Enter between 1 and 16 notes, for example C4:32 D4:32');
      return;
    }
    const notes = [];
    for (const token of tokens) {
      const match = /^([A-G])(#?)([1-9]):(\d{1,3})$/i.exec(token);
      if (!match) { setStatus(`Invalid note “${token}”. Use note names like C4:32.`); return; }
      const note = (Number(match[3]) + 1) * 12 + names[match[1].toUpperCase()] + (match[2] ? 1 : 0);
      const duration = Number(match[4]);
      if (note < 31 || note > 127 || duration < 0 || duration > 255) {
        setStatus(`${token} is outside the Roomba note or duration range.`); return;
      }
      notes.push({ note, duration });
    }
    send('/roomba/song', { song_number: Number(songNumber), notes });
  }

  return <section className="panel roomba-effects" aria-labelledby="effects-title">
    <div className="panel-header"><div><p className="console-label">OI ACCESSORIES</p><h2 id="effects-title">LEDs & songs</h2></div></div>
    <div className="effects-body">
      <div className="effect-heading"><h3>Power LED</h3><span className="led-preview" style={{ backgroundColor: `hsl(${hue} 100% 50% / ${Math.max(0.12, intensity / 255)})` }} /></div>
      <label className="effect-control">Color <span>{color < 128 ? 'Green' : 'Red'} · {color}</span>
        <input aria-label="Power LED color from green to red" type="range" min="0" max="255" value={color}
          onChange={event => setColor(Number(event.target.value))} />
      </label>
      <label className="effect-control">Intensity <span>{intensity}</span>
        <input aria-label="Power LED intensity" type="range" min="0" max="255" value={intensity}
          onChange={event => setIntensity(Number(event.target.value))} />
      </label>
      <button className="effect-button" disabled={busy} onClick={() => send('/roomba/led', { color, intensity })}>Set LED</button>

      <form className="song-form" onSubmit={playSong}>
        <h3>Play a tune</h3>
        <label className="effect-control">Song slot (0–15)
          <input type="number" min="0" max="15" value={songNumber}
            onChange={event => setSongNumber(event.target.value)} />
        </label>
        <label className="effect-control">Notes · note:duration
          <input type="text" value={notesText} maxLength="180" placeholder="C4:32 D4:32 E4:48"
            onChange={event => setNotesText(event.target.value)} />
        </label>
        <p className="panel-note">MIDI note names; duration is in 1/64-second units. Up to 16 notes.</p>
        <button className="effect-button" type="submit" disabled={busy}>Save & play</button>
      </form>
      {status && <p className="panel-note effect-status" role="status">{status}</p>}
    </div>
  </section>;
}

function PiDiagnostics() {
  const [data, setData] = React.useState(null);
  React.useEffect(() => {
    let stopped = false, timer;
    async function poll() {
      try { const response = await fetch('/pi/diagnostics', { cache: 'no-store' }); if (!response.ok) throw new Error(); const result = await response.json(); if (!stopped) setData(result); }
      catch (_) { if (!stopped) setData(null); }
      if (!stopped) timer = setTimeout(poll, 2000);
    }
    poll(); return () => { stopped = true; clearTimeout(timer); };
  }, []);
  const flags = data?.throttled;
  return <section className="panel sensor-panel"><div className="panel-header"><div><p className="console-label">SYSTEM / DIAGNOSTICS</p><h2>Raspberry Pi</h2></div><Status online={!!data}>{data ? 'LIVE' : 'UNAVAILABLE'}</Status></div>
    <div className="sensor-body"><div className="metric-grid">
      <div><span className="metric-label">CPU temperature</span><span>{data?.temperature_c == null ? '—' : `${data.temperature_c} °C`}</span></div>
      <div><span className="metric-label">CPU usage</span><span>{data?.cpu_percent == null ? '—' : `${data.cpu_percent}%`}</span></div>
      <div><span className="metric-label">Throttling now</span><span>{flags ? (flags.current.includes('Throttling') ? 'Yes' : 'No') : '—'}</span></div>
      <div><span className="metric-label">Flags since boot</span><span>{flags ? (flags.history.join(', ') || 'Clear') : '—'}</span></div>
    </div><h3 className="section-label">USB devices</h3><div className="sensor-flags">{data?.usb_devices == null ? 'Unavailable' : data.usb_devices.length ? data.usb_devices.map((device, i) => <div className="sensor-flag" key={i}>{device}</div>) : 'No USB peripherals detected'}</div>
    <p className="panel-note">Updates every 2 seconds.</p></div></section>;
}

function App() {
  const { telemetry, requestTelemetry } = useTelemetry();
  return (
    <main className="page">
      <header className="site-header">
        <div><p className="console-label">ROBOT OPERATIONS</p><h1>NeuraVac<span> / live console</span></h1></div>
        <Status online={!!telemetry?.online}>{telemetry?.online ? 'ROOMBA CONNECTED' : 'WAITING FOR ROOMBA'}</Status>
      </header>
      <div className="dashboard-grid">
        <div className="visual-column"><CameraView /><SlamMapView /><LidarView /></div>
        <aside className="control-column"><SensorPanel telemetry={telemetry} onRequestTelemetry={requestTelemetry} /><PiDiagnostics /><RemoteOverride /><RoombaEffects /></aside>
      </div>
      <SerialConsole telemetry={telemetry} />
      <footer>NeuraVac · Live readings from the Raspberry Pi</footer>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
