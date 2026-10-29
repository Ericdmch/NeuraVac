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
  const [isEnabled, setIsEnabled] = React.useState(false);
  const [activeKeys, setActiveKeys] = React.useState(new Set());
  const [speed, setSpeed] = React.useState(200);
  const heldKeys = React.useRef(new Set());
  const [error, setError] = React.useState('');
  const queue = React.useRef(Promise.resolve());

  function sendOverride(key, pressed) {
    if (pressed) heldKeys.current.add(key); else heldKeys.current.delete(key);
    setActiveKeys(new Set(heldKeys.current));
    // Keep press/release order even on a slow connection.
    queue.current = queue.current.catch(() => {}).then(async () => {
      if (pressed && !heldKeys.current.has(key)) return;
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
  function releaseAll() { [...heldKeys.current].forEach(key => sendOverride(key, false)); }
  React.useEffect(() => {
    function keyDown(event) {
      if (!isEnabled || event.repeat || event.target.closest('input, textarea, select, [contenteditable="true"]')) return;
      const key = event.key.toUpperCase();
      if (controls.includes(key)) { event.preventDefault(); sendOverride(key, true); }
    }
    function keyUp(event) {
      const key = event.key.toUpperCase();
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
  return <section className={`remote-override panel ${isEnabled ? 'is-enabled' : ''}`} aria-labelledby="remote-override-title">
    <div className="panel-header"><div><p className="console-label">MANUAL / KEYBOARD</p><h2 id="remote-override-title">Drive controls</h2></div>
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
    <p className="panel-note">{error || (isEnabled ? 'Hold a key or button to drive. Release to stop.' : 'Enable manual control to use WASD. Q / E adjust speed.')}</p>
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
    const stream = new EventSource('/lidar/stream');
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
      if (stream.readyState === EventSource.CLOSED) {
        console.error('LiDAR event stream closed.');
      }
    };

    const expiryTimer = window.setInterval(() => {
      const points = rollingPointsRef.current;
      if (points.length && performance.now() - points[points.length - 1].receivedAt >= 250) {
        scheduleDraw();
      }
    }, 50);

    return () => {
      isMounted = false;
      stream.close();
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
  const [status, setStatus] = React.useState('WAITING FOR MAP');
  const [resetting, setResetting] = React.useState(false);
  const [resetError, setResetError] = React.useState('');

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

  React.useEffect(() => {
    const stream = new EventSource('/slam/map/stream');
    let latestMap = null;
    function drawMap(map) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const context = canvas.getContext('2d');
      const width = canvas.width = Math.max(1, canvas.clientWidth * devicePixelRatio);
      const height = canvas.height = Math.max(1, canvas.clientHeight * devicePixelRatio);
      context.fillStyle = '#0b121c'; context.fillRect(0, 0, width, height);
      const binary = atob(map.data);
      const cells = new Uint8Array(binary.length);
      let minX = map.width, minY = map.height, maxX = -1, maxY = -1;
      for (let i = 0; i < binary.length; i += 1) {
        cells[i] = binary.charCodeAt(i);
        if (cells[i] >= 40 && cells[i] !== 255) {
          const x = i % map.width, y = Math.floor(i / map.width);
          minX = Math.min(minX, x); minY = Math.min(minY, y);
          maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
        }
      }
      let robotX = ((map.robot_x ?? 0) - map.origin_x) / map.resolution;
      let robotY = ((map.robot_y ?? 0) - map.origin_y) / map.resolution;
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
      const margin = 12;
      minX = Math.max(0, minX - margin); minY = Math.max(0, minY - margin);
      maxX = Math.min(map.width - 1, maxX + margin); maxY = Math.min(map.height - 1, maxY + margin);
      const cropWidth = maxX - minX + 1, cropHeight = maxY - minY + 1;
      const fit = Math.min(width / cropWidth, height / cropHeight);
      const drawWidth = cropWidth * fit, drawHeight = cropHeight * fit;
      const left = (width - drawWidth) / 2, top = (height - drawHeight) / 2;
      const image = context.createImageData(cropWidth, cropHeight);
      for (let y = 0; y < cropHeight; y += 1) {
        for (let x = 0; x < cropWidth; x += 1) {
          const value = cells[(minY + y) * map.width + minX + x];
          const offset = (y * cropWidth + x) * 4;
          if (value === 255) image.data.set([17, 27, 39, 255], offset);
          else if (value >= 75) image.data.set([255, 138, 61, 255], offset);
          else if (value >= 40) image.data.set([186, 133, 93, 235], offset);
          else image.data.set([35, 51, 66, 255], offset);
        }
      }
      const layer = document.createElement('canvas');
      layer.width = cropWidth; layer.height = cropHeight;
      layer.getContext('2d').putImageData(image, 0, 0);
      context.imageSmoothingEnabled = false;
      context.drawImage(layer, left, top, drawWidth, drawHeight);
      if (hasRobotPose && robotX >= minX && robotX <= maxX && robotY >= minY && robotY <= maxY) {
        context.fillStyle = '#63b3ff'; context.beginPath();
        context.arc(left + (robotX - minX) * fit, top + (robotY - minY) * fit, 5 * devicePixelRatio, 0, Math.PI * 2);
        context.fill();
        const heading = map.robot_yaw ?? 0;
        const markerX = left + (robotX - minX) * fit;
        const markerY = top + (robotY - minY) * fit;
        const length = 19 * devicePixelRatio;
        context.save();
        context.translate(markerX, markerY);
        // Occupancy grid rows increase downward in this canvas.
        context.rotate(3 * Math.PI / 2 - heading);
        context.strokeStyle = '#63b3ff';
        context.lineWidth = 2.5 * devicePixelRatio;
        context.beginPath();
        context.moveTo(0, 0); context.lineTo(length, 0);
        context.moveTo(length - 6 * devicePixelRatio, -5 * devicePixelRatio);
        context.lineTo(length, 0);
        context.lineTo(length - 6 * devicePixelRatio, 5 * devicePixelRatio);
        context.stroke();
        context.restore();
      }
      return true;
    }
    stream.onmessage = event => {
      try {
        latestMap = JSON.parse(event.data);
        setStatus(drawMap(latestMap) ? (latestMap.tracking_status || 'TRACKING') : 'WAITING FOR SCANS');
      }
      catch (error) { console.error('Unable to decode LiDAR map.', error); }
    };
    stream.onerror = () => setStatus('WAITING FOR MAP');
    const resize = () => { if (latestMap) drawMap(latestMap); };
    window.addEventListener('resize', resize);
    return () => { stream.close(); window.removeEventListener('resize', resize); };
  }, []);

  return <section className="lidar-view slam-map-view" aria-labelledby="slam-map-title">
    <div className="lidar-header"><div><p className="console-label">LIDAR + WHEEL ODOMETRY / SCAN MATCHED</p><h2 id="slam-map-title">Room map</h2></div>
      <div className="slam-map-actions">
        <button className="telemetry-refresh" type="button" onClick={resetMap} disabled={resetting}>
          {resetting ? 'RESETTING…' : 'RESET & REMAP'}
        </button>
        <span className={`connection-status ${status === 'WAITING FOR MAP' ? '' : 'is-online'}`}><span className="status-dot" />{status}</span>
      </div>
    </div>
    <div className="slam-map-canvas-wrap"><canvas ref={canvasRef} aria-label="LiDAR-built room occupancy map" /></div>
    <p className="panel-note slam-map-note">{resetError || 'Orange = persistent wall returns · Blue = estimated robot pose · Reset clears the map and pose; fresh scans rebuild it.'}</p>
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
      if (!stopped) timer = window.setTimeout(updateFrame, 200);
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

function App() {
  const { telemetry, requestTelemetry } = useTelemetry();
  return (
    <main className="page">
      <header className="site-header">
        <div><p className="console-label">ROBOT OPERATIONS</p><h1>NeuraVac<span> / live console</span></h1></div>
        <Status online={!!telemetry?.online}>{telemetry?.online ? 'ROOMBA CONNECTED' : 'WAITING FOR ROOMBA'}</Status>
      </header>
      <div className="dashboard-grid">
        <div className="visual-column"><CameraView /><LidarView /><SlamMapView /></div>
        <aside className="control-column"><SensorPanel telemetry={telemetry} onRequestTelemetry={requestTelemetry} /><RemoteOverride /><RoombaEffects /></aside>
      </div>
      <SerialConsole telemetry={telemetry} />
      <footer>NeuraVac · Live readings from the Raspberry Pi</footer>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
