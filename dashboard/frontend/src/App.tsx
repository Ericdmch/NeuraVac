import { useCallback, useEffect, useRef, useState } from 'react';
import Dashboard from './Dashboard';
import { parseSnapshot, type Snapshot } from './telemetry';

export default function App() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [token, setToken] = useState('');
  const [receivedAt, setReceivedAt] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const [error, setError] = useState<string | null>(null);
  const [commandError, setCommandError] = useState<string | null>(null);
  const [transport, setTransport] = useState('Connecting');
  const [pending, setPending] = useState<string | null>(null);
  const commandControllers = useRef(new Set<AbortController>());
  const busy = useRef(false);
  const receive = useCallback((value: unknown) => {
    const parsed = parseSnapshot(value);
    if (!parsed) throw new Error('Backend returned an invalid telemetry snapshot');
    setSnapshot(parsed); setReceivedAt(Date.now()); setError(null);
  }, []);
  useEffect(() => {
    const controllers = commandControllers.current;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => { clearInterval(timer); controllers.forEach(controller => controller.abort()); };
  }, []);
  useEffect(() => {
    let disposed = false;
    let ws: WebSocket | null = null;
    let retryMs = 1000;
    let retryTimer: ReturnType<typeof setTimeout>;
    let pollTimer: ReturnType<typeof setTimeout>;
    let pollController: AbortController | null = null;
    setReceivedAt(null);
    setSnapshot(null);
    setError(null);
    setCommandError(null);
    const poll = async () => {
      pollController = new AbortController();
      const timeout = setTimeout(() => pollController?.abort(), 4000);
      try {
        const response = await fetch('/api/state', { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: pollController.signal, cache: 'no-store' });
        if (!response.ok) throw new Error(`Telemetry request failed (${response.status})${response.status === 401 || response.status === 403 ? ' · Check the backend control token.' : ''}`);
        const value: unknown = await response.json();
        if (!disposed) { receive(value); if (ws?.readyState !== WebSocket.OPEN) setTransport(token ? 'Authenticated polling' : 'HTTP polling'); }
      } catch (reason) { if (!disposed && ws?.readyState !== WebSocket.OPEN) { setError(reason instanceof Error ? reason.message : 'Unable to reach backend'); setTransport('Backend unavailable'); } }
      finally { clearTimeout(timeout); if (!disposed) pollTimer = setTimeout(() => { void poll(); }, 2500); }
    };
    const connect = () => {
      if (disposed) return;
      const url = new URL('/ws', window.location.href); url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(url);
      ws.onopen = () => {
        if (disposed) return;
        if (token) ws?.send(JSON.stringify({ token }));
        setTransport('Socket connected · awaiting telemetry');
      };
      ws.onmessage = event => {
        if (disposed) return;
        try { receive(JSON.parse(String(event.data)) as unknown); retryMs = 1000; setTransport(token ? 'Authenticated WebSocket' : 'Live WebSocket'); }
        catch (reason) { setError(reason instanceof Error ? reason.message : 'Invalid WebSocket telemetry'); }
      };
      ws.onclose = () => { if (!disposed) { setTransport('HTTP polling · reconnecting'); retryTimer = setTimeout(connect, retryMs); retryMs = Math.min(retryMs * 2, 30000); } };
    };
    void poll(); connect();
    return () => { disposed = true; clearTimeout(retryTimer); clearTimeout(pollTimer); pollController?.abort(); ws?.close(); };
  }, [receive, token]);
  const action = async (name: string) => {
    if (busy.current && name !== 'estop') return;
    busy.current = true;
    setPending(name); setCommandError(null);
    const controller = new AbortController();
    commandControllers.current.add(controller);
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const endpoint = name === 'move-chair' ? '/api/demo/move-chair' : `/api/mission/${name}`;
      const response = await fetch(endpoint, { method: 'POST', headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: controller.signal });
      if (!response.ok) {
        let detail = '';
        try { const payload: unknown = await response.json(); if (payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string') detail = ` · ${payload.detail}`; } catch { /* Some proxies return non-JSON errors. */ }
        throw new Error(`Command rejected (${response.status})${detail}`);
      }
      // Commands never optimistically change mission or safety telemetry.
    } catch (reason) {
      setCommandError(reason instanceof Error && reason.name === 'AbortError' ? 'Command timed out. Delivery is unconfirmed; check telemetry and the robot.' : reason instanceof Error ? reason.message : 'Command failed');
    } finally { clearTimeout(timeout); commandControllers.current.delete(controller); if (commandControllers.current.size === 0) { setPending(null); busy.current = false; } }
  };
  const ageSeconds = receivedAt === null ? null : Math.max(0, Math.floor((now - receivedAt) / 1000));
  const fresh = receivedAt !== null && now - receivedAt < 6000;
  return <Dashboard snapshot={snapshot} fresh={fresh} pending={pending} error={commandError ?? error} transport={transport} ageSeconds={ageSeconds} onAction={name => { void action(name); }} token={token} onToken={setToken} />;
}
