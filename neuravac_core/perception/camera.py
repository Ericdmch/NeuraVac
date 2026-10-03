"""One-frame buffer; capture never builds an unbounded inference backlog."""

import time
from threading import Event, Lock, Thread

from neuravac_core.perception.interface import CameraFrame


class LatestFrameBuffer:
    def __init__(self):
        self._lock = Lock()
        self._frame: CameraFrame | None = None

    def publish(self, frame: CameraFrame):
        with self._lock:
            self._frame = frame

    def latest(self) -> CameraFrame | None:
        with self._lock:
            return self._frame


class CameraCapture(LatestFrameBuffer):
    def __init__(self, device=0, width=320, height=320, clock=time.monotonic):
        super().__init__()
        self.device, self.width, self.height, self.clock = device, width, height, clock
        self._stop = Event()
        self._thread: Thread | None = None
        self.error: Exception | None = None
        self._capture = None

    def start(self):
        import cv2

        if self._thread is not None:
            raise RuntimeError("Capture already started")
        self._capture = cv2.VideoCapture(self.device)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not self._capture.isOpened():
            self._capture.release()
            raise RuntimeError(f"Unable to open camera {self.device}")
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self):
        import cv2

        assert self._capture is not None
        try:
            while not self._stop.is_set():
                ok, bgr = self._capture.read()
                if not ok:
                    raise RuntimeError("Camera frame read failed")
                self.publish(CameraFrame(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), self.clock()))
        except Exception as exc:
            self.error = exc
        finally:
            self._capture.release()

    def latest(self):
        if self.error:
            raise RuntimeError("Camera capture failed") from self.error
        return super().latest()

    def close(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                raise RuntimeError("Camera driver did not stop within two seconds")

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.close()
