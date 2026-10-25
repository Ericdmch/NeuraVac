function Header({ title }) {
  return (
    <header className="site-header">
        <h1>/ {title}</h1>
    </header>
  );
}

function SerialConsole() {
  const [command, setCommand] = React.useState('');
  const [isOnline, setIsOnline] = React.useState(false);
  const [messages, setMessages] = React.useState([
    'Serial console ready. Waiting for a connection.',
  ]);
  const outputRef = React.useRef(null);

  React.useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [messages]);

  async function handleSubmit(event) {
    event.preventDefault();
    const text = command.trim();
    if (!text) {
      return;
    }

    try {
      const response = await fetch('/submit', {
        body: JSON.stringify({ data: text }),
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Serial bridge returned HTTP ${response.status}`);
      }

      setIsOnline(true);
      setMessages((current) => [...current, `> ${text}`]);
      setCommand('');
    } catch (error) {
      setIsOnline(false);
      setMessages((current) => [
        ...current,
        `! Unable to reach serial bridge: ${error.message}`,
      ]);
    }
  }

  return (
    <section className="serial-console" aria-labelledby="serial-console-title">
      <div className="serial-header">
        <div>
          <p className="console-label">DEVICE LINK / UART</p>
          <h2 id="serial-console-title">Serial Console</h2>
        </div>
        <span className={`connection-status ${isOnline ? 'is-online' : ''}`}>
          <span className="status-dot" />
          {isOnline ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>
      <div ref={outputRef} className="serial-output" role="log" aria-live="polite">
        {messages.map((message, index) => (
          <p key={`${message}-${index}`}>{message}</p>
        ))}
      </div>
      <form className="serial-input" onSubmit={handleSubmit}>
        <label htmlFor="serial-command">SEND COMMAND</label>
        <div className="command-row">
          <span className="command-prompt">&gt;</span>
          <input
            id="serial-command"
            value={command}
            onChange={(event) => setCommand(event.target.value)}
            placeholder="Type a serial command..."
            autoComplete="off"
          />
          <button type="submit">SEND</button>
        </div>
      </form>
    </section>
  );
}

function RemoteOverride() {
  const controls = ['Q', 'W', 'E', 'A', 'S', 'D'];
  const [isEnabled, setIsEnabled] = React.useState(false);
  const [activeKeys, setActiveKeys] = React.useState(new Set());

  async function sendOverride(key, pressed) {
    setActiveKeys((current) => {
      const next = new Set(current);
      if (pressed) {
        next.add(key);
      } else {
        next.delete(key);
      }
      return next;
    });

    try {
      const response = await fetch('/override', {
        body: JSON.stringify({ key, pressed }),
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Override endpoint returned HTTP ${response.status}`);
      }
    } catch (error) {
      console.error(`Unable to send ${key} override event.`, error);
    }
  }

  React.useEffect(() => {
    function handleKeyDown(event) {
      const key = event.key.toUpperCase();
      if (!isEnabled || !controls.includes(key) || event.repeat) {
        return;
      }
      event.preventDefault();
      sendOverride(key, true);
    }

    function handleKeyUp(event) {
      const key = event.key.toUpperCase();
      if (!isEnabled || !controls.includes(key)) {
        return;
      }
      event.preventDefault();
      sendOverride(key, false);
    }

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isEnabled]);

  function toggleOverride() {
    setIsEnabled((current) => !current);
    setActiveKeys(new Set());
  }

  return (
    <section
      className={`remote-override ${isEnabled ? 'is-enabled' : 'is-disabled'}`}
      aria-labelledby="remote-override-title"
      aria-pressed={isEnabled}
      onClick={toggleOverride}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          toggleOverride();
        }
      }}
      role="button"
      tabIndex="0"
    >
      <div className="remote-header">
        <div>
          <p className="console-label">MANUAL CONTROL / KEYBOARD</p>
          <h2 id="remote-override-title">Remote Override</h2>
        </div>
        <span className="override-hint">{isEnabled ? 'ENABLED' : 'DISABLED'}</span>
      </div>
      <div className="override-controls">
        {controls.map((key) => (
          <button
            className={activeKeys.has(key) ? 'override-key is-active' : 'override-key'}
            key={key}
            disabled={!isEnabled}
            onClick={(event) => event.stopPropagation()}
            onKeyDown={(event) => event.stopPropagation()}
            onBlur={() => {
              if (isEnabled && activeKeys.has(key)) {
                sendOverride(key, false);
              }
            }}
            onMouseDown={(event) => {
              event.stopPropagation();
              if (isEnabled) {
                sendOverride(key, true);
              }
            }}
            onMouseUp={(event) => {
              event.stopPropagation();
              if (isEnabled) {
                sendOverride(key, false);
              }
            }}
            onMouseLeave={() => {
              if (isEnabled && activeKeys.has(key)) {
                sendOverride(key, false);
              }
            }}
            type="button"
          >
            {key}
          </button>
        ))}
      </div>
      <p className="override-help">Hold a key or button to send an override command.</p>
    </section>
  );
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

    async function updateLidar() {
      try {
        const response = await fetch('/lidar');
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
          setIsOnline(true);
        }
      } catch (error) {
        if (isMounted) {
          setIsOnline(false);
          console.error('Unable to read lidar data.', error);
        }
      }
    }

    updateLidar();
    const interval = window.setInterval(updateLidar, 1000);
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
          <span>{rulerLength} mm</span>
        </div>
      </div>
    </section>
  );
}

function App() {
  return (
    <main className="page">
      <Header title={"Neuravac"} />

      <SerialConsole />
      <RemoteOverride />
      <LidarView />
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
