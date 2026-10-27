#!/usr/bin/env python3
"""Publish compressed camera frames and floor-model detections over ROS 2."""

import importlib
import math
import sys
import threading
from pathlib import Path

import rclpy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from roomba_interfaces.msg import VisionDetection, VisionDetectionArray
from sensor_msgs.msg import CompressedImage


IMAGE_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
    reliability=ReliabilityPolicy.BEST_EFFORT,
)


def suggested_action(label):
    """Map a detector label to advisory cleaning metadata."""
    return {
        'solid_debris': 'clean',
        'large_debris': 'avoid',
        'cable': 'avoid',
        'shoe': 'avoid',
        'liquid_spill': 'avoid_and_review',
    }.get(label.lower().replace(' ', '_'), 'observe')


def normalized_detection(detection, image_width, image_height):
    """Convert one model result into the public ROS message representation."""
    x_min, y_min, x_max, y_max = map(float, detection['xyxy'])
    width = max(0.0, x_max - x_min)
    height = max(0.0, y_max - y_min)

    message = VisionDetection()
    message.label = str(detection['label'])
    message.confidence = float(detection['confidence'])
    message.x_min_px = x_min
    message.y_min_px = y_min
    message.x_max_px = x_max
    message.y_max_px = y_max
    message.center_x_norm = min(max((x_min + x_max) / (2.0 * image_width), 0.0), 1.0)
    message.center_y_norm = min(max((y_min + y_max) / (2.0 * image_height), 0.0), 1.0)
    message.width_norm = min(max(width / image_width, 0.0), 1.0)
    message.height_norm = min(max(height / image_height, 0.0), 1.0)
    message.suggested_action = suggested_action(message.label)
    return message


class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')

        self.declare_parameter('bundle_dir', '~/floor-vision-pi')
        self.declare_parameter('model_path', '')
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('camera_device', '')
        self.declare_parameter('camera_fourcc', 'MJPG')
        self.declare_parameter('camera_width', 1920)
        self.declare_parameter('camera_height', 1080)
        self.declare_parameter('camera_publish_hz', 12.0)
        self.declare_parameter('camera_frame_id', 'camera_optical_frame')
        self.declare_parameter('flip_code', -1)  # Added safely without duplicating width
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('threads', 3)
        self.declare_parameter('inference_hz', 5.0)
        self.declare_parameter('imgsz', 0)
        self.declare_parameter('publish_annotated_image', True)
        self.declare_parameter('jpeg_quality', 80)
        self.declare_parameter('camera_jpeg_quality', 68)
        self.declare_parameter('save_observations', True)
        self.declare_parameter('observations_dir', '')
        self.declare_parameter('observation_interval', 2.0)

        self._bundle_dir = Path(
            self.get_parameter('bundle_dir').value
        ).expanduser().resolve()
        self._camera_frame_id = str(self.get_parameter('camera_frame_id').value)
        self._publish_annotated = bool(
            self.get_parameter('publish_annotated_image').value
        )
        self._jpeg_quality = int(self.get_parameter('jpeg_quality').value)
        self._camera_jpeg_quality = int(self.get_parameter('camera_jpeg_quality').value)
        if not 1 <= self._jpeg_quality <= 100:
            raise ValueError('jpeg_quality must be between 1 and 100')
        if not 1 <= self._camera_jpeg_quality <= 100:
            raise ValueError('camera_jpeg_quality must be between 1 and 100')

        inference_hz = float(self.get_parameter('inference_hz').value)
        camera_publish_hz = float(self.get_parameter('camera_publish_hz').value)
        threads = int(self.get_parameter('threads').value)
        if not math.isfinite(inference_hz) or inference_hz <= 0:
            raise ValueError('inference_hz must be a finite positive number')
        if not math.isfinite(camera_publish_hz) or camera_publish_hz <= 0:
            raise ValueError('camera_publish_hz must be a finite positive number')
        if threads < 1:
            raise ValueError('threads must be at least 1')

        runtime = self._load_runtime()
        camera_index = int(self.get_parameter('camera_index').value)
        camera_width = int(self.get_parameter('camera_width').value)
        camera_height = int(self.get_parameter('camera_height').value)
        if camera_index < 0 or camera_width < 1 or camera_height < 1:
            raise ValueError('camera_index must be nonnegative and dimensions positive')

        # A device path such as /dev/neuravac_camera survives the USB port
        # changing; it is resolved on every (re)open so camera recovery after a
        # replug picks up the new /dev/videoN. Empty means use camera_index.
        camera_device = str(self.get_parameter('camera_device').value).strip()

        # Most USB webcams cannot stream uncompressed video at 1080p and then
        # time out with "select() timeout". Ask for MJPEG, the format the
        # dashboard's own capture uses. Empty keeps the driver default.
        camera_fourcc = str(self.get_parameter('camera_fourcc').value).strip()
        if camera_fourcc and len(camera_fourcc) != 4:
            raise ValueError('camera_fourcc must be four characters, e.g. MJPG')

        def open_camera(index):
            if camera_device:
                capture = runtime.cv2.VideoCapture(camera_device, runtime.cv2.CAP_V4L2)
            else:
                capture = runtime.cv2.VideoCapture(index, runtime.cv2.CAP_V4L2)  # Force V4L2 backend for Linux webcams
            
            if camera_fourcc:
                capture.set(
                    runtime.cv2.CAP_PROP_FOURCC,
                    runtime.cv2.VideoWriter_fourcc(*camera_fourcc),
                )
            capture.set(runtime.cv2.CAP_PROP_FRAME_WIDTH, camera_width)
            capture.set(runtime.cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
            capture.set(runtime.cv2.CAP_PROP_FPS, max(camera_publish_hz, inference_hz))
            
            # --- CRITICAL FOR REMOVING LAG ---
            capture.set(runtime.cv2.CAP_PROP_BUFFERSIZE, 1)
            # ---------------------------------
            return capture

        self._camera = runtime.RecoveringCamera(camera_index, factory=open_camera)
        self._models = runtime.models
        self._device = runtime.device
        self._imgsz = runtime.imgsz
        self._thresholds = runtime.thresholds
        self._conf = runtime.conf
        self._observation_store = runtime.observation_store
        self._detect_objects = runtime.detect_objects
        self._colors = runtime.colors
        self._cv2 = runtime.cv2

        self._image_pub = self.create_publisher(
            CompressedImage, 'camera/image/compressed', IMAGE_QOS
        )
        self._annotated_pub = None
        if self._publish_annotated:
            self._annotated_pub = self.create_publisher(
                CompressedImage, 'camera/image_annotated/compressed', IMAGE_QOS
            )
        self._detections_pub = self.create_publisher(
            VisionDetectionArray, 'camera/detections', 10
        )

        self._last_width = 0
        self._last_height = 0
        self._frame_lock = threading.Lock()
        self._latest_frame = None
        self._latest_stamp = None
        self._camera_callback_group = MutuallyExclusiveCallbackGroup()
        self._camera_timer = self.create_timer(
            1.0 / camera_publish_hz, self._capture_and_publish,
            callback_group=self._camera_callback_group,
        )
        self._timer = self.create_timer(1.0 / inference_hz, self._process_frame)
        self.get_logger().info(
            f'Vision ready: model={runtime.model_path}, imgsz={self._imgsz}, '
            f'device={self._device}, camera={camera_device or camera_index}, '
            f'camera={camera_publish_hz:g} Hz, inference={inference_hz:g} Hz'
        )
        self.get_logger().info(
            'Publishing compressed frames, detections, and advisory actions; '
            'this node does not command the Roomba.'
        )

    def _load_runtime(self):
        if not self._bundle_dir.is_dir():
            raise FileNotFoundError(
                f'Floor vision bundle not found: {self._bundle_dir}. '
                'Set the bundle_dir parameter to the deployed floor-vision-pi directory.'
            )
        bundle_path = str(self._bundle_dir)
        if bundle_path not in sys.path:
            sys.path.insert(0, bundle_path)

        # Reuse the deployment bundle's camera recovery, model profile, and
        # inference functions so the ROS process uses the same calibrated path.
        floor_app = importlib.import_module('main')
        camera_capture = importlib.import_module('camera_capture')
        floor_profile = importlib.import_module('floor_profile')
        ncnn_runtime = importlib.import_module('ncnn_runtime')
        observation_store_module = importlib.import_module('observation_store')

        explicit_model = str(self.get_parameter('model_path').value).strip()
        model_path = (Path(explicit_model).expanduser().resolve() if explicit_model
                      else floor_app.default_floor_model(self._bundle_dir))
        if not model_path.exists():
            raise FileNotFoundError(f'Floor model not found: {model_path}')

        requested_imgsz = int(self.get_parameter('imgsz').value)
        if requested_imgsz < 0:
            raise ValueError('imgsz must be zero (profile default) or a positive size')
        profile = floor_profile.load_profile(
            model_path, requested_imgsz if requested_imgsz > 0 else None
        )
        imgsz = requested_imgsz or profile.get('imgsz', 512)
        thresholds = profile.get('class_thresholds')
        conf = min((thresholds or {'all': 0.35}).values())
        threads = int(self.get_parameter('threads').value)
        device = str(self.get_parameter('device').value)

        import numpy as np
        import torch
        from ultralytics import YOLO

        torch.set_num_threads(threads)
        self._cv2 = __import__('cv2')
        self._cv2.setNumThreads(threads)
        model = YOLO(str(model_path), task='detect')
        floor_profile.configure_floor_head(model)
        if model_path.is_dir():
            model.predict(
                np.zeros((imgsz, imgsz, 3), dtype=np.uint8),
                imgsz=imgsz, device=device, verbose=False,
            )
            ncnn_runtime.configure_threads(model, model_path, threads)
        ncnn_runtime.configure_torch_threads(model, threads)

        observation_store = None
        if bool(self.get_parameter('save_observations').value):
            observations_dir = str(self.get_parameter('observations_dir').value).strip()
            observation_path = (Path(observations_dir).expanduser()
                                if observations_dir else self._bundle_dir / 'observations')
            observation_store = observation_store_module.ObservationStore(
                observation_path,
                float(self.get_parameter('observation_interval').value),
            )

        class Runtime:
            pass

        runtime = Runtime()
        runtime.RecoveringCamera = camera_capture.RecoveringCamera
        runtime.models = [(model, (0, 0, 255))]
        runtime.device = device
        runtime.imgsz = imgsz
        runtime.thresholds = thresholds
        runtime.conf = conf
        runtime.observation_store = observation_store
        runtime.detect_objects = floor_app.detect_objects
        runtime.colors = floor_app.FLOOR_COLORS
        runtime.cv2 = self._cv2
        runtime.model_path = model_path
        return runtime

    def _capture_and_publish(self):
        try:
            frame = self._camera.read()
        except Exception as error:
            self.get_logger().fatal(f'Camera stopped after recovery attempts: {error}')
            self._publish_invalid_batch(self.get_clock().now().to_msg())
            if rclpy.ok():
                rclpy.shutdown()
            return

        if frame is None:
            return
        stamp = self.get_clock().now().to_msg()
        flip_param = self.get_parameter('flip_code').value
        if flip_param is not None and flip_param in (-1, 0, 1):
            frame = self._cv2.flip(frame, int(flip_param))
        height, width = frame.shape[:2]
        self._last_width = width
        self._last_height = height
        with self._frame_lock:
            self._latest_frame = frame
            self._latest_stamp = stamp
        image_message = self._encode_frame(frame, stamp, self._camera_jpeg_quality)
        if image_message is not None:
            self._image_pub.publish(image_message)

    def _process_frame(self):
        with self._frame_lock:
            frame = None if self._latest_frame is None else self._latest_frame.copy()
            stamp = self._latest_stamp
        if frame is None or stamp is None:
            self._publish_invalid_batch(self.get_clock().now().to_msg())
            return
        height, width = frame.shape[:2]

        batch = VisionDetectionArray()
        batch.header.stamp = stamp
        batch.header.frame_id = self._camera_frame_id
        batch.image_width = width
        batch.image_height = height
        batch.frame_valid = True

        detections = self._detect_objects(
            frame,
            self._models,
            device=self._device,
            imgsz=self._imgsz,
            conf=self._conf,
            class_thresholds=self._thresholds,
            square_input=True,
        )
        batch.detections = [
            normalized_detection(detection, width, height)
            for detection in detections
        ]
        self._detections_pub.publish(batch)

        if self._annotated_pub is not None:
            annotated = self._annotate(frame, detections)
            annotated_message = self._encode_frame(annotated, stamp)
            if annotated_message is not None:
                self._annotated_pub.publish(annotated_message)

        if self._observation_store is not None:
            self._observation_store.record(frame, detections)

    def _publish_invalid_batch(self, stamp):
        batch = VisionDetectionArray()
        batch.header.stamp = stamp
        batch.header.frame_id = self._camera_frame_id
        batch.image_width = self._last_width
        batch.image_height = self._last_height
        batch.frame_valid = False
        batch.detections = []
        self._detections_pub.publish(batch)

    def _encode_frame(self, frame, stamp, quality=None):
        options = [self._cv2.IMWRITE_JPEG_QUALITY, quality or self._jpeg_quality]
        success, encoded = self._cv2.imencode('.jpg', frame, options)
        if not success:
            self.get_logger().warning('Could not JPEG-encode camera frame')
            return None
        message = CompressedImage()
        message.header.stamp = stamp
        message.header.frame_id = self._camera_frame_id
        message.format = 'jpeg'
        message.data = encoded.tobytes()
        return message

    def _annotate(self, frame, detections):
        annotated = frame.copy()
        for detection in detections:
            x_min, y_min, x_max, y_max = map(int, detection['xyxy'])
            label = f"{detection['label']} {float(detection['confidence']):.2f}"
            color = detection.get(
                'color', self._colors.get(detection['label'], (0, 255, 0))
            )
            self._cv2.rectangle(annotated, (x_min, y_min), (x_max, y_max), color, 2)
            self._cv2.putText(
                annotated, label, (x_min, max(20, y_min - 8)),
                self._cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
            )
        return annotated

    def destroy_node(self):
        camera = getattr(self, '_camera', None)
        if camera is not None:
            camera.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    executor = MultiThreadedExecutor(num_threads=2)
    try:
        node = VisionNode()
        executor.add_node(node)
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception as error:
        if node is not None:
            node.get_logger().fatal(f'Could not start vision node: {error}')
        else:
            print(f'Could not start vision node: {error}', file=sys.stderr)
        raise
    finally:
        executor.shutdown()
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
