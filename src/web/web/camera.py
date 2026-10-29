"""One USB capture shared by every dashboard viewer, with reconnect support."""

import logging
import threading
import time


class LatestJpeg:
    """Newest JPEG pushed in by a ROS subscription, same interface as CameraCapture.

    Used when the vision node owns the webcam and publishes its frames, since
    only one process can capture from the device.
    """

    MAX_AGE_SECONDS = 2.0

    def __init__(self):
        self._lock = threading.Lock()
        self._jpeg = None
        self._updated = 0.0

    def update(self, jpeg):
        with self._lock:
            self._jpeg = bytes(jpeg)
            self._updated = time.monotonic()

    def start(self):
        pass

    def snapshot(self):
        with self._lock:
            if time.monotonic() - self._updated > self.MAX_AGE_SECONDS:
                return None
            return self._jpeg

    def close(self):
        pass


class CameraCapture:
    def __init__(self, device='/dev/neuravac_camera', width=1280, height=720):
        self.device = device
        self.width = width
        self.height = height
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._jpeg = None
        self._updated = 0.0
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._capture, daemon=True)
        self._thread.start()

    def snapshot(self):
        with self._lock:
            if time.monotonic() - self._updated > 2.0:
                return None
            return self._jpeg

    def close(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3)

    def _capture(self):
        try:
            import cv2
        except ImportError:
            logging.getLogger(__name__).error('Camera requires python3-opencv')
            return
        while not self._stop.is_set():
            capture = None
            try:
                capture = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
                capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                capture.set(cv2.CAP_PROP_FPS, 15)
                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not capture.isOpened():
                    raise RuntimeError(f'Cannot open camera {self.device}')
                while not self._stop.is_set():
                    ok, frame = capture.read()
                    if not ok:
                        raise RuntimeError('Camera read failed')
                    ok, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    if not ok:
                        raise RuntimeError('Camera JPEG encoding failed')
                    with self._lock:
                        self._jpeg = jpeg.tobytes()
                        self._updated = time.monotonic()
                    self._stop.wait(0.03)
            except Exception as error:
                logging.getLogger(__name__).warning('Camera offline: %s', error)
            finally:
                with self._lock:
                    self._jpeg = None
                if capture is not None:
                    capture.release()
            self._stop.wait(2)
