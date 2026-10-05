"""
Roomba dev panel: a single-file Flask app.

Run:   pip install flask
       python roomba_web.py
Open:  http://127.0.0.1:5000

Needs roomba.py (the Roomba class), helpers.py and config.json in the same folder.
"""
import atexit
import functools
import re
import threading
import time

from flask import Flask, jsonify, request

from roomba import Roomba
from sensors import decode_sensors, read_exact

HOST = "127.0.0.1"        # localhost only: this app has no auth and moves a robot
PORT = 5000
WATCHDOG_TIMEOUT = 0.5    # seconds without a drive command before the wheels are stopped


# ----------------------------------------------------------------------------
# Note parsing (so "A4", "C#5", "Bb3", "R" or a raw MIDI number all work)
# ----------------------------------------------------------------------------
NOTE_OFFSETS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def parse_note(n):
    if isinstance(n, (int, float)):
        return int(n)
    s = str(n).strip()
    if s.isdigit():
        return int(s)
    if s.upper() in ("R", "REST"):
        return 0
    letter = s[:1].upper()
    if letter not in NOTE_OFFSETS:
        raise ValueError(f"bad note {n!r}")
    midi = NOTE_OFFSETS[letter]
    rest = s[1:]
    if rest[:1] == "#":
        midi += 1
        rest = rest[1:]
    elif rest[:1] == "b":
        midi -= 1
        rest = rest[1:]
    octave = int(rest) if rest else 4
    return 12 * (octave + 1) + midi


def parse_song(text):
    """'C5:16 E5:16 R:8 G5:32' -> [('C5', 16), ('E5', 16), ('R', 8), ('G5', 32)]"""
    out = []
    for tok in re.split(r"[\s,]+", text.strip()):
        if not tok:
            continue
        if ":" in tok:
            n, d = tok.rsplit(":", 1)
            out.append((n, int(d)))
        else:
            out.append((tok, 16))
    return out


# ----------------------------------------------------------------------------
# Roomba subclass: adds what the web panel needs without touching roomba.py
# ----------------------------------------------------------------------------
class RoombaDev(Roomba):
    MAX_SONG_SLOT = 3   # 500/600 series: slots 0-3

    def __init__(self):
        super().__init__()
        self.baud = int(self.baud)
        self.song_secs = {}

    def _send_opcode(self, *args, **kwargs):
        # parent's flush() is unreachable; flush here and leave a 20 ms gap
        n = super()._send_opcode(*args, **kwargs)
        if self.ser and self.ser.is_open:
            self.ser.flush()
        time.sleep(0.02)
        return n

    def drive(self, velocity, radius=None):
        # same as the parent, minus the print on every call (the UI sends 10/s)
        import helpers
        velocity = max(-500, min(500, int(velocity)))
        radius = 0x8000 if radius is None else max(-2000, min(2000, int(radius)))
        self._send_opcode(name="drive", data=helpers.split16(velocity) + helpers.split16(radius))

    def leds(self, bits, color, intensity):
        clamp = lambda x: max(0, min(255, int(x)))
        self._send_opcode(name="leds", data=[int(bits) & 0x0F, clamp(color), clamp(intensity)])

    def define_song(self, number, song, transpose=0):
        if not 0 <= number <= self.MAX_SONG_SLOT:
            raise ValueError(f"song slot must be 0-{self.MAX_SONG_SLOT}")
        song = list(song)[:16]
        if not song:
            raise ValueError("empty song")
        data = [number, len(song)]
        total = 0
        for n, d in song:
            n = parse_note(n)
            if n != 0:
                n = max(31, min(127, n + transpose))
            d = max(0, min(255, int(d)))
            data += [n, d]
            total += d
        self._send_opcode(name="define-song", data=data)
        self.song_secs[number] = total / 64
        return total / 64

    def play_song(self, number):
        self._send_opcode(name="play-song", data=[number])

    def load_sounds(self):
        self.define_song(1, [("C5", 8), ("E5", 8), ("G5", 8), ("C6", 20)])   # chime
        self.define_song(2, [("E3", 12), ("C3", 24)])                        # error buzz


# ----------------------------------------------------------------------------
# Shared state
# ----------------------------------------------------------------------------
app = Flask(__name__)
lock = threading.Lock()
roomba = None
state = {"mode": None}                        # None, "safe" or "full"
drive_state = {"moving": False, "t": 0.0}
SOUNDS = {"chime": 1, "error": 2}


def ready():
    return bool(roomba and state["mode"] and roomba.ser and roomba.ser.is_open)


def status_dict():
    return {"mode": state["mode"], "port": roomba.port if roomba else None,
            "baud": roomba.baud if roomba else None, "moving": drive_state["moving"]}


def err(msg, code=400):
    return jsonify(ok=False, error=msg), code


def api(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:
            return err(f"{type(e).__name__}: {e}", 500)
    return wrapper


def _shutdown_locked():
    global roomba
    if roomba is not None and roomba.ser and roomba.ser.is_open:
        try:
            roomba.drive(0)
            roomba.leds(0, 0, 0)
        finally:
            roomba.stop_roomba()
    roomba = None
    state["mode"] = None
    drive_state["moving"] = False


def shutdown():
    with lock:
        _shutdown_locked()


atexit.register(shutdown)


def watchdog():
    """If the browser stops sending drive commands while moving (tab closed,
    network drop, crash), stop the wheels."""
    while True:
        time.sleep(0.1)
        if drive_state["moving"] and time.time() - drive_state["t"] > WATCHDOG_TIMEOUT:
            with lock:
                if roomba and drive_state["moving"]:
                    roomba.drive(0)
                    drive_state["moving"] = False
                    print("watchdog: no drive command received, stopped wheels")


threading.Thread(target=watchdog, daemon=True).start()


# ----------------------------------------------------------------------------
# API
# ----------------------------------------------------------------------------
@app.get("/api/status")
def api_status():
    return jsonify(ok=True, **status_dict())


@app.post("/api/connect")
@api
def api_connect():
    global roomba
    safe = bool((request.get_json(silent=True) or {}).get("safe", False))
    with lock:
        if roomba is not None:
            _shutdown_locked()
        r = RoombaDev()
        r.connect_serial(attempts=0)
        if not (r.ser and r.ser.is_open):
            return err(f"Could not open serial port {r.port}", 500)
        time.sleep(0.5)                 # opening the port can toggle DTR; let it settle
        r.start_roomba(safe_mode=safe)
        r._send_opcode(code=[150, 0])  # Pause any previous sensor stream.
        r.ser.reset_input_buffer()
        r.load_sounds()
        roomba = r
        state["mode"] = "safe" if safe else "full"
    return jsonify(ok=True, **status_dict())


@app.post("/api/disconnect")
@api
def api_disconnect():
    shutdown()
    return jsonify(ok=True, **status_dict())


@app.get("/api/sensors")
@api
def api_sensors():
    # Keep the read shorter than the drive watchdog deadline. All serial
    # traffic uses the same lock so commands cannot interrupt a response.
    with lock:
        if not ready():
            return err("Connect the Roomba to read sensors", 409)
        try:
            roomba.ser.reset_input_buffer()
            roomba._send_opcode(code=[142, 100])
            payload = read_exact(roomba.ser, 80, 0.12)
            sample = decode_sensors(payload, "oi")
        except (OSError, ValueError, TimeoutError) as error:
            # Stop on an incomplete response; the next poll clears stale bytes.
            roomba.drive(0)
            drive_state["moving"] = False
            return err(f"Sensor read failed: {error}. Wake the robot with CLEAN.", 503)
        return jsonify(ok=True, timestamp=time.time(), sensors=sample)


@app.post("/api/drive")
@api
def api_drive():
    if not ready():
        return err("Roomba not started", 409)
    d = request.get_json(silent=True) or {}
    v = int(d.get("velocity", 0))
    r = d.get("radius")
    r = None if r is None else int(r)
    with lock:
        roomba.drive(v, r)
        drive_state["moving"] = v != 0
        drive_state["t"] = time.time()
    return jsonify(ok=True)


@app.post("/api/led")
@api
def api_led():
    if not ready():
        return err("Roomba not started", 409)
    d = request.get_json(silent=True) or {}
    with lock:
        roomba.leds(d.get("bits", 0), d.get("color", 255), d.get("intensity", 255))
    return jsonify(ok=True)


@app.post("/api/beep")
@api
def api_beep():
    if not ready():
        return err("Roomba not started", 409)
    d = request.get_json(silent=True) or {}
    with lock:
        secs = roomba.define_song(0, [(d.get("note", "A4"), d.get("duration", 16))])
        roomba.play_song(0)
    return jsonify(ok=True, seconds=secs)


@app.post("/api/sound")
@api
def api_sound():
    if not ready():
        return err("Roomba not started", 409)
    name = (request.get_json(silent=True) or {}).get("name")
    if name not in SOUNDS:
        return err(f"unknown sound {name!r}")
    with lock:
        roomba.play_song(SOUNDS[name])
    return jsonify(ok=True)


@app.post("/api/song")
@api
def api_song():
    if not ready():
        return err("Roomba not started", 409)
    d = request.get_json(silent=True) or {}
    song = parse_song(d.get("notes", ""))
    with lock:
        secs = roomba.define_song(3, song, transpose=int(d.get("transpose", 0)))
        roomba.play_song(3)
    return jsonify(ok=True, seconds=secs)


# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------
@app.get("/")
def index():
    return INDEX_HTML


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Roomba dev panel</title>
<style>
  :root { --bg:#14161a; --card:#1d2026; --fg:#e8eaed; --mut:#8b919a; --acc:#4ade80; --bad:#f87171; --bd:#2b2f37; }
  * { box-sizing: border-box; }
  body { margin:0 auto; max-width:920px; padding:16px; background:var(--bg); color:var(--fg);
         font:15px system-ui, sans-serif; }
  h1 { font-size:20px; margin:0 0 14px; display:flex; align-items:center; gap:12px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:14px; }
  .card { background:var(--card); border:1px solid var(--bd); border-radius:10px; padding:14px; }
  .card h2 { margin:0 0 10px; font-size:13px; text-transform:uppercase; letter-spacing:.06em; color:var(--mut); }
  .row { display:flex; gap:8px; align-items:center; margin:8px 0; flex-wrap:wrap; }
  label { color:var(--mut); font-size:13px; }
  button, select, input[type=text], input[type=number] {
    background:#272b33; color:var(--fg); border:1px solid var(--bd); border-radius:6px;
    padding:8px 12px; font:inherit; }
  button { cursor:pointer; }
  button:hover { background:#31363f; }
  button.primary { background:#166534; border-color:#22c55e; }
  button.danger { background:#7f1d1d; border-color:#ef4444; }
  input[type=text] { flex:1; min-width:0; }
  input[type=number] { width:80px; }
  input[type=range] { flex:1; }
  .pill { font-size:12px; padding:3px 10px; border-radius:99px; background:#3b1d1d; color:var(--bad); }
  .pill.on { background:#14351f; color:var(--acc); }
  .pad { display:grid; grid-template-columns:repeat(3, 64px); grid-template-rows:repeat(2, 64px); gap:6px; justify-content:center; margin:12px 0; }
  .pad button { font-size:20px; font-weight:600; padding:0; touch-action:none; user-select:none; }
  .pad button.held { background:var(--acc); color:#000; }
  #state { font-size:22px; font-weight:600; text-align:center; }
  #speedv { text-align:center; color:var(--acc); }
  #log { height:150px; overflow:auto; font:12px ui-monospace, Consolas, monospace; color:var(--mut); }
  #log .bad { color:var(--bad); }
  .hint { color:var(--mut); font-size:12px; line-height:1.5; }
  #sensorValues { display:grid; grid-template-columns:1fr 1fr; gap:6px 16px; }
  #sensorValues dt { color:var(--mut); overflow-wrap:anywhere; }
  #sensorValues dd { margin:0; overflow-wrap:anywhere; }
  kbd { background:#272b33; border:1px solid var(--bd); border-radius:4px; padding:0 5px; }
</style>
</head>
<body>
<h1>Roomba dev panel <span id="pill" class="pill">disconnected</span></h1>

<div class="grid">
  <div class="card">
    <h2>Connection</h2>
    <div class="row">
      <label>Mode</label>
      <select id="mode">
        <option value="full">Full (no cliff/wheel-drop safety)</option>
        <option value="safe">Safe</option>
      </select>
    </div>
    <div class="row">
      <button class="primary" id="connect">Connect &amp; start</button>
      <button class="danger" id="disconnect">Disconnect</button>
    </div>
    <div class="hint">Wake the robot (press Clean) and keep it off the charger first.
      The server stops the wheels if drive commands stop arriving.</div>
  </div>

  <div class="card">
    <h2>Drive</h2>
    <div id="state">STOPPED</div>
    <div id="speedv">150 mm/s</div>
    <div class="pad">
      <span></span><button data-k="w">W</button><span></span>
      <button data-k="a">A</button><button data-k="s">S</button><button data-k="d">D</button>
    </div>
    <div class="row"><label>Speed</label>
      <input type="range" id="speed" min="25" max="500" step="25" value="150"></div>
    <div class="row"><button class="danger" id="stop" style="width:100%">STOP (space)</button></div>
    <div class="hint"><kbd>W</kbd><kbd>S</kbd> forward/back, <kbd>A</kbd><kbd>D</kbd> spin,
      <kbd>W</kbd>+<kbd>A</kbd> arc, <kbd>Q</kbd>/<kbd>E</kbd> or <kbd>&darr;</kbd>/<kbd>&uarr;</kbd> speed,
      <kbd>Space</kbd> stop.</div>
  </div>

  <div class="card">
    <h2>LEDs</h2>
    <div class="row"><label>Power color</label>
      <input type="range" id="lcolor" min="0" max="255" value="255"></div>
    <div class="row"><label>Intensity</label>
      <input type="range" id="lint" min="0" max="255" value="255"></div>
    <div class="row">
      <label><input type="checkbox" class="lbit" data-b="1"> debris</label>
      <label><input type="checkbox" class="lbit" data-b="2"> spot</label>
      <label><input type="checkbox" class="lbit" data-b="4"> dock</label>
      <label><input type="checkbox" class="lbit" data-b="8"> check</label>
    </div>
    <div class="hint">Power color: 0 = green, 255 = red.</div>
  </div>

  <div class="card">
    <h2>Sound</h2>
    <div class="row">
      <input type="text" id="note" value="A4" placeholder="note">
      <input type="number" id="dur" value="16" min="1" max="255" title="1/64 s units">
      <button id="beep">Beep</button>
    </div>
    <div class="row">
      <button data-s="chime">Chime</button>
      <button data-s="error">Error</button>
    </div>
    <div class="row">
      <input type="text" id="song" value="E5:8 E5:8 R:8 E5:8 R:8 C5:8 E5:16 G5:32">
    </div>
    <div class="row">
      <label>Transpose</label><input type="number" id="trans" value="0" min="-36" max="36">
      <button id="playsong">Play song</button>
    </div>
    <div class="hint">Notes like <code>C5</code>, <code>F#4</code>, <code>Bb3</code>, <code>R</code> (rest) or MIDI numbers (31-127).
      Duration is in 1/64 s (32 = half a second). Max 16 notes. Sounds need Safe or Full mode.</div>
  </div>
</div>

<div class="card" style="margin-top:14px">
  <h2>Sensors</h2>
  <div id="sensorStatus" class="hint">Connect to read sensors.</div>
  <dl id="sensorValues"></dl>
  <div class="hint">Updates once per second. Distance and angle are changes since the previous sensor request.</div>
</div>

<div class="card" style="margin-top:14px">
  <h2>Log</h2>
  <div id="log"></div>
</div>

<script>
const $ = id => document.getElementById(id);
const ARC = 300;
let ready = false, speed = 150, inflight = false, stopsLeft = 0;
const held = new Set();

function log(msg, bad) {
  const d = document.createElement('div');
  if (bad) d.className = 'bad';
  d.textContent = new Date().toLocaleTimeString() + '  ' + msg;
  $('log').appendChild(d);
  while ($('log').children.length > 80) $('log').removeChild($('log').firstChild);
  $('log').scrollTop = $('log').scrollHeight;
}

async function api(path, body) {
  try {
    const r = await fetch(path, {method: 'POST', headers: {'Content-Type': 'application/json'},
                                 body: JSON.stringify(body || {})});
    const j = await r.json();
    if (!j.ok) log(path + ': ' + j.error, true);
    return j;
  } catch (e) {
    log(path + ': ' + e, true);
    return {ok: false};
  }
}

function setStatus(s) {
  ready = !!s.mode;
  $('pill').textContent = ready ? ('connected (' + s.mode + ')') : 'disconnected';
  $('pill').className = 'pill' + (ready ? ' on' : '');
  if (!ready) {
    $('sensorValues').replaceChildren();
    $('sensorStatus').textContent = 'Connect to read sensors.';
  }
}

let sensorPolling = false;
async function refreshSensors() {
  if (!ready || sensorPolling) return;
  sensorPolling = true;
  try {
    const response = await fetch('/api/sensors');
    const data = await response.json();
    if (!ready) return;
    if (!data.ok) throw new Error(data.error);
    const rows = document.createDocumentFragment();
    function add(name, value) {
      if (value !== null && typeof value === 'object') {
        for (const [key, item] of Object.entries(value)) add(name + ' / ' + key, item);
        return;
      }
      const label = document.createElement('dt');
      const reading = document.createElement('dd');
      label.textContent = name.replaceAll('_', ' ');
      reading.textContent = value === null ? 'Unavailable' : String(value);
      rows.append(label, reading);
    }
    for (const [name, value] of Object.entries(data.sensors)) add(name, value);
    $('sensorValues').replaceChildren(rows);
    $('sensorStatus').textContent = 'Updated ' + new Date(data.timestamp * 1000).toLocaleTimeString();
  } catch (error) {
    $('sensorValues').replaceChildren();
    $('sensorStatus').textContent = error.message;
  } finally {
    sensorPolling = false;
  }
}

async function refresh() {
  try { setStatus(await (await fetch('/api/status')).json()); } catch (e) {}
}

/* ---------- driving ---------- */
function compute() {
  if (held.has(' ')) return [0, null];
  const fwd = (held.has('w') ? 1 : 0) - (held.has('s') ? 1 : 0);
  const turn = (held.has('a') ? 1 : 0) - (held.has('d') ? 1 : 0);
  if (!fwd && !turn) return [0, null];
  if (!fwd) return [speed, turn > 0 ? 1 : -1];            // spin in place
  return [fwd * speed, turn === 0 ? null : (turn > 0 ? ARC : -ARC)];
}

function describe([v, r]) {
  if (v === 0) return 'STOPPED';
  if (r === null) return v > 0 ? 'FORWARD' : 'REVERSE';
  if (r === 1 || r === -1) return r === 1 ? 'SPIN LEFT' : 'SPIN RIGHT';
  return r > 0 ? 'ARC LEFT' : 'ARC RIGHT';
}

async function tick() {
  const cmd = compute();
  $('state').textContent = describe(cmd);
  $('speedv').textContent = speed + ' mm/s';
  document.querySelectorAll('.pad button').forEach(b => b.classList.toggle('held', held.has(b.dataset.k)));
  if (!ready) return;
  const [v, r] = cmd;
  let j = null;
  if (v !== 0) {
    stopsLeft = 3;
    if (inflight) return;
    inflight = true;
    j = await api('/api/drive', {velocity: v, radius: r});
    inflight = false;
  } else if (stopsLeft > 0) {
    stopsLeft--;                                           // a few stop commands in case one is lost
    j = await api('/api/drive', {velocity: 0, radius: null});
  }
  if (j && !j.ok) { ready = false; refresh(); }
}
setInterval(tick, 100);

const typing = e => e.target.tagName === 'TEXTAREA' ||
  (e.target.tagName === 'INPUT' && ['text', 'number'].includes(e.target.type));

addEventListener('keydown', e => {
  if (typing(e)) return;
  const k = e.key.toLowerCase();
  if (k.length === 1 && 'wasd '.includes(k)) { held.add(k); e.preventDefault(); tick(); }
  else if (k === 'arrowup' || k === 'e') { setSpeed(speed + 25); e.preventDefault(); }
  else if (k === 'arrowdown' || k === 'q') { setSpeed(speed - 25); e.preventDefault(); }
});
addEventListener('keyup', e => { held.delete(e.key.toLowerCase()); tick(); });
addEventListener('blur', () => { held.clear(); tick(); });
document.addEventListener('visibilitychange', () => { held.clear(); tick(); });

function setSpeed(v) {
  speed = Math.max(25, Math.min(500, v));
  $('speed').value = speed;
  tick();
}
$('speed').addEventListener('input', e => setSpeed(+e.target.value));

document.querySelectorAll('.pad button').forEach(b => {
  const k = b.dataset.k;
  b.addEventListener('pointerdown', e => { held.add(k); tick(); });
  ['pointerup', 'pointerleave', 'pointercancel'].forEach(ev =>
    b.addEventListener(ev, () => { held.delete(k); tick(); }));
});
$('stop').addEventListener('click', async () => {
  held.clear(); stopsLeft = 3;
  await api('/api/drive', {velocity: 0, radius: null});
});

/* ---------- connection ---------- */
$('connect').addEventListener('click', async () => {
  log('connecting...');
  const j = await api('/api/connect', {safe: $('mode').value === 'safe'});
  if (j.ok) { setStatus(j); log('connected on ' + j.port + ' @ ' + j.baud + ' (' + j.mode + ' mode)'); sendLed(); }
});
$('disconnect').addEventListener('click', async () => {
  held.clear();
  const j = await api('/api/disconnect');
  if (j.ok) { setStatus(j); log('disconnected'); }
});

/* ---------- LEDs ---------- */
function ledBits() {
  let b = 0;
  document.querySelectorAll('.lbit').forEach(c => { if (c.checked) b |= +c.dataset.b; });
  return b;
}
function sendLed() {
  if (!ready) return;
  api('/api/led', {bits: ledBits(), color: +$('lcolor').value, intensity: +$('lint').value});
}
let ledTimer = null;
const ledSoon = () => { clearTimeout(ledTimer); ledTimer = setTimeout(sendLed, 80); };
['lcolor', 'lint'].forEach(id => $(id).addEventListener('input', ledSoon));
document.querySelectorAll('.lbit').forEach(c => c.addEventListener('change', sendLed));

/* ---------- sound ---------- */
$('beep').addEventListener('click', () => api('/api/beep', {note: $('note').value, duration: +$('dur').value}));
document.querySelectorAll('[data-s]').forEach(b =>
  b.addEventListener('click', () => api('/api/sound', {name: b.dataset.s})));
$('playsong').addEventListener('click', () =>
  api('/api/song', {notes: $('song').value, transpose: +$('trans').value}));

refresh();
setInterval(refresh, 2000);
setInterval(refreshSensors, 1000);
tick();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    # use_reloader=False matters: the reloader would start a second process
    # that tries to open the same COM port.
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False, threaded=True)
