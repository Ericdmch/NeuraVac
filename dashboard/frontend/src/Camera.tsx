import { useEffect, useState } from 'react';
import Icon from './Icon';
export default function Camera({ token, simulation }: { token: string; simulation: boolean }) {
  const [enabled, setEnabled] = useState(false);
  const [frame, setFrame] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!enabled) return;
    let disposed = false;
    let objectUrl: string | null = null;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    const load = async () => {
      try {
        const response = await fetch('/api/camera', { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: controller.signal, cache: 'no-store' });
        if (!response.ok) throw new Error(`Camera unavailable (${response.status})`);
        if (!response.headers.get('content-type')?.startsWith('image/')) throw new Error('Camera endpoint did not return an image');
        const blob = await response.blob();
        if (disposed) return;
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = URL.createObjectURL(blob);
        setFrame(objectUrl); setError(null);
      } catch (reason) { if (!disposed) { setFrame(null); setError(reason instanceof Error ? reason.message : 'Camera unavailable'); } }
      if (!disposed) timer = setTimeout(() => { void load(); }, 2500);
    };
    void load();
    return () => { disposed = true; controller.abort(); clearTimeout(timer); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [enabled, token]);
  return <section className="panel camera-panel"><div className="panel-heading compact"><h2><Icon name="camera" size={18} />{simulation ? 'Simulated sensor preview' : 'Camera preview'}</h2><button className="text-button" onClick={() => { setEnabled(!enabled); setFrame(null); setError(null); }}>{enabled ? 'Close' : 'Open preview'}</button></div>{enabled ? <div className="camera-frame">{frame ? <img src={frame} alt={simulation ? 'Labeled floor observation rendered by the simulator' : 'Latest camera frame reported by the robot'} /> : <p role="status">{error ?? 'Requesting camera frame…'}</p>}</div> : <p className="camera-note">{simulation ? 'Labeled simulator observation · loaded on request' : 'Optional robot camera · loaded on request'}</p>}</section>;
}
