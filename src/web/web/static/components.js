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
        if (!stopped) timer = window.setTimeout(update, 500);
      }
    }
    update();
    return () => { stopped = true; window.clearTimeout(timer); controller?.abort(); };
  }, []);
  return telemetry;
}

function SensorPanel({ telemetry }) {
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
  return <section className="sensor-panel panel" aria-labelledby="sensor-title">
    <div className="panel-header">
      <div><p className="console-label">ROOMBA / TELEMETRY</p><h2 id="sensor-title">Robot sensors</h2></div>
      <Status online={!!values}>{values ? 'LIVE' : 'NO DATA'}</Status>
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
      <p className="panel-note">{values ? `Updated ${telemetry.age_seconds.toFixed(1)} s ago · polls at 2 Hz` : 'Readings unavailable or older than 2 s.'}</p>
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
    const maxRange = Math.max(
      ...scan.map((point) => Math.hypot(point.x, point.y)),
      1
    );

    canvas.width = width * scale;
    canvas.height = height * scale;
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
      const distance = Math.min(Math.hypot(point.x, point.y) / maxRange, 1) * radius;
      const scale = Math.hypot(point.x, point.y) ? distance / Math.hypot(point.x, point.y) : 0;
      const x = point.x * scale;
      const y = point.y * scale;
      context.fillStyle = '#ff8a3d';
      context.fillRect(x - 1.5, y - 1.5, 3, 3);
    });
    context.restore();
  }

  React.useEffect(() => {
    let isMounted = true;
    let requestInFlight = false;

    async function updateLidar() {
      if (requestInFlight) {
        return;
      }
      requestInFlight = true;

      try {
        const response = await fetch('/lidar', { cache: 'no-store' });
        if (!response.ok) {
          throw new Error(`Lidar endpoint returned HTTP ${response.status}`);
        }

        const scan = await response.json();
        if (isMounted) {
          scanRef.current = scan;
          setRulerLength(Math.round(
            Math.max(...scan.map((point) => Math.hypot(point.x, point.y)), 1) / 2
          ));
          drawLidar(scan);
          setIsOnline(scan.length > 0);
        }
      } catch (error) {
        if (isMounted) {
          setIsOnline(false);
          console.error('Unable to read lidar data.', error);
        }
      } finally {
        requestInFlight = false;
      }
    }

    updateLidar();
    const interval = window.setInterval(updateLidar, 50);
    return () => {
      isMounted = false;
      window.clearInterval(interval);
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

function App() {
  const telemetry = useTelemetry();
  return (
    <main className="page">
      <header className="site-header">
        <div><p className="console-label">ROBOT OPERATIONS</p><h1>NeuraVac<span> / live console</span></h1></div>
        <Status online={!!telemetry?.online}>{telemetry?.online ? 'ROOMBA CONNECTED' : 'WAITING FOR ROOMBA'}</Status>
      </header>
      <div className="dashboard-grid">
        <div className="visual-column"><CameraView /><LidarView /></div>
        <aside className="control-column"><SensorPanel telemetry={telemetry} /><RemoteOverride /></aside>
      </div>
      <SerialConsole telemetry={telemetry} />
      <footer>NeuraVac · Live readings from the Raspberry Pi</footer>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
