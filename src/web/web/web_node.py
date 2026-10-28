from collections import deque
import json
import math
import os
import threading
import time

from ament_index_python.packages import get_package_share_directory
from flask import Flask, Response, jsonify, render_template, request
import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from roomba_interfaces.msg import LidarPoint, SerialData

from .override import roomba_drive
from .camera import CameraCapture, LatestJpeg
from .telemetry import SensorState


app = Flask(__name__)


# OVERRIDE CONSTANTS
STRAIGHT = 32768

DEFAULT_SPEED = 200
MIN_SPEED = 50
MAX_SPEED = 500
SPEED_STEP = 50

OVERRIDE_MOTIONS = {
    'W': (1, STRAIGHT),
    'S': (-1, STRAIGHT),
    'A': (1, 1),      # counter-clockwise (left)
    'D': (1, -1),     # clockwise (right)
}
SPEED_KEYS = {'Q', 'E'}


class WebBridge(Node):
    # Generic webbridge node that can be used to bridge any ROS2 topic to the web interface.
    def __init__(self, name='web_bridge_node'):
        super().__init__(name)
        self._pubs = {}
        self._subs = {}

        self.get_logger().info(f'WebBridge node {name} initialized.')

    def add_publisher(self, msg_type, topic, qos=10):
        if topic in self._pubs:
            self.get_logger().warn(f'Publisher for topic {topic} already exists.')
            return self._pubs[topic]

        pub = self.create_publisher(msg_type, topic, qos)
        self._pubs[topic] = pub
        return pub

    def publish(self, topic, msg):
        pub = self._pubs.get(topic)
        pub.publish(msg)

    def add_subscriber(self, msg_type, topic, callback, qos=10):
        if topic in self._subs:
            self.get_logger().warn(f'Subscriber for topic {topic} already exists.')
            return self._subs[topic]
            
        sub = self.create_subscription(msg_type, topic, callback, qos)
        self._subs[topic] = sub
        return sub

    def remove_subscriber(self, topic):
        sub = self._subs.pop(topic, None)
        if sub:
            self.destroy_subscription(sub)

    def remove_publisher(self, topic):
        pub = self._pubs.pop(topic, None)
        if pub:
            self.destroy_publisher(pub)


class SerialBridge:
    def __init__(self, topic, data_type = SerialData):
        self.bridge = WebBridge(name='web_serial_node')
        self.publisher = self.bridge.add_publisher(data_type, topic)

        self.topic = topic
        self.data_type = data_type
        self.sensors = SensorState()
        self._rx_lock = threading.Lock()
        self._rx_log = deque(maxlen=8)
        self._rx_sequence = 0
        self.bridge.add_subscriber(SerialData, 'serial_rx', self.receive_serial)
        self._sensor_timer = self.bridge.create_timer(0.5, self.poll_sensors)

    def poll_sensors(self):
        if self.publisher.get_subscription_count() and self.sensors.request(time.monotonic()):
            self.send_message(SerialData(data=[142, 0]))

    def receive_serial(self, message):
        self.sensors.receive(bytes(message.data), time.monotonic())
        with self._rx_lock:
            self._rx_sequence += 1
            self._rx_log.append({
                'id': self._rx_sequence,
                'text': bytes(message.data).hex(' '),
            })

    def snapshot(self):
        result = self.sensors.snapshot(time.monotonic())
        result['bridge_connected'] = self.publisher.get_subscription_count() > 0
        with self._rx_lock:
            result['serial_rx'] = list(self._rx_log)
        return result

    def send_serial_data(self, data):
        msg = self.data_type()

        # throw out all non integers, processes the string into a list of integers
        msg.data = [int(t) for t in data.replace(',', ' ').split() if t.isdigit()]

        self.bridge.publish(self.topic, msg)

    def send_message(self, message):
        self.bridge.publish(self.topic, message)

class LidarBridge:
    RECENT_POINT_MAX_AGE_SECONDS = 0.25
    STREAM_BATCH_SECONDS = 0.01

    def __init__(self, topic, data_type = LidarPoint):
        self.bridge = WebBridge(name='web_lidar_node')
        self.bridge.add_subscriber(data_type, topic, self.lidar_callback)

        self.topic = topic
        self._condition = threading.Condition()
        self._points = deque(maxlen=1440)
        self._sequence = 0

    def lidar_callback(self, msg):
        point = {
            'angle_deg': float(msg.angle_deg),
            'distance_mm': int(msg.distance_mm),
            'intensity': int(msg.intensity),
        }
        with self._condition:
            self._sequence += 1
            self._points.append((self._sequence, time.monotonic(), point))
            self._condition.notify_all()

    def wait_for_points(self, after_sequence, timeout):
        with self._condition:
            self._condition.wait_for(
                lambda: self._sequence > after_sequence,
                timeout=timeout,
            )
            latest_sequence = self._sequence
            cutoff = time.monotonic() - self.RECENT_POINT_MAX_AGE_SECONDS
            points = [
                point for sequence, timestamp, point in self._points
                if sequence > after_sequence and timestamp >= cutoff
            ]
            return latest_sequence, points

    def current_sequence(self):
        with self._condition:
            return self._sequence

    def snapshot(self):
        cutoff = time.monotonic() - self.RECENT_POINT_MAX_AGE_SECONDS
        with self._condition:
            recent_points = [
                (sequence, timestamp, point)
                for sequence, timestamp, point in self._points
                if timestamp >= cutoff
            ]
            self._points.clear()
            self._points.extend(recent_points)
            return [point for _, _, point in recent_points]

    @staticmethod
    def polar_to_cartesian(angle_deg, distance_mm):
        angle_rad = math.radians(angle_deg)
        return (
            distance_mm * math.cos(angle_rad),
            distance_mm * math.sin(angle_rad),
        )


def create_app(serial_bridge, lidar_bridge, template_dir, static_dir=None, camera=None):
    if static_dir is None:
        static_dir = os.path.join(os.path.dirname(template_dir), 'static')
    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static',
    )
    active_override = None
    speed = DEFAULT_SPEED

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/telemetry')
    def telemetry():
        response = jsonify(serial_bridge.snapshot())
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/camera/frame')
    def camera_frame():
        jpeg = camera.snapshot() if camera is not None else None
        if jpeg is None:
            response = jsonify(error='Camera unavailable. Reconnecting…')
            response.status_code = 503
        else:
            response = Response(jpeg, mimetype='image/jpeg')
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.post('/submit')
    def submit():
        payload = request.get_json(silent=True)
        serial_data = payload.get('data', '').strip() if payload else ''

        if not serial_data:
            return jsonify(error='Serial data is required'), 400

        serial_bridge.send_serial_data(serial_data)

        return jsonify(message=serial_data)

    @app.post('/override')
    def override():
        nonlocal active_override, speed
        payload = request.get_json(silent=True) or {}
        key = str(payload.get('key', '')).upper()
        pressed = payload.get('pressed')

        known = key in OVERRIDE_MOTIONS or key in SPEED_KEYS
        if not known or not isinstance(pressed, bool):
            return jsonify(error='A valid override key and pressed state are required'), 400

        app.logger.info('Key %s %s', key, 'pressed' if pressed else 'released')

        if key in SPEED_KEYS:
            if pressed:
                speed = max(
                    MIN_SPEED,
                    min(MAX_SPEED, speed + (SPEED_STEP if key == 'E' else -SPEED_STEP)),
                )
                if active_override:
                    direction, radius = OVERRIDE_MOTIONS[active_override]
                    serial_bridge.send_message(roomba_drive(speed * direction, radius))
            return jsonify(key=key, pressed=pressed, speed=speed)

        if pressed:
            direction, radius = OVERRIDE_MOTIONS[key]
            serial_bridge.send_message(roomba_drive(speed * direction, radius))
            active_override = key
        elif active_override == key:
            serial_bridge.send_message(roomba_drive(0, STRAIGHT))
            active_override = None

        return jsonify(key=key, pressed=pressed, speed=speed)

    @app.get('/lidar')
    def lidar():
        points = lidar_bridge.snapshot()
        scan = []
        for point in points:
            x, y = lidar_bridge.polar_to_cartesian(
                point['angle_deg'], point['distance_mm']
            )
            scan.append({'x': x, 'y': y})
        return jsonify(scan)

    @app.get('/lidar/stream')
    def lidar_stream():
        def events():
            sequence = lidar_bridge.current_sequence()
            while True:
                sequence, points = lidar_bridge.wait_for_points(sequence, timeout=1.0)
                if not points:
                    yield ': keepalive\n\n'
                    continue

                deadline = time.monotonic() + lidar_bridge.STREAM_BATCH_SECONDS
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    sequence, next_points = lidar_bridge.wait_for_points(
                        sequence, timeout=remaining
                    )
                    points.extend(next_points)

                scan = []
                for point in points:
                    x, y = lidar_bridge.polar_to_cartesian(
                        point['angle_deg'], point['distance_mm']
                    )
                    scan.append({'x': x, 'y': y})
                yield f'data: {json.dumps(scan, separators=(",", ":"))}\n\n'

        return Response(
            events(),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
        )

    return app


def build_camera(bridge):
    """Create the dashboard's camera feed.

    NEURAVAC_CAMERA_SOURCE=ros shows the frames the vision node publishes,
    because the webcam can only be opened by one process. Anything else (the
    default) opens NEURAVAC_CAMERA_DEVICE directly.
    """
    if os.environ.get('NEURAVAC_CAMERA_SOURCE', 'device').lower() == 'ros':
        from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import CompressedImage

        feed = LatestJpeg()

        def on_image(msg):
            if 'jpeg' in msg.format.lower() or 'jpg' in msg.format.lower():
                feed.update(msg.data)

        bridge.add_subscriber(
            CompressedImage,
            os.environ.get('NEURAVAC_CAMERA_TOPIC', 'camera/image/compressed'),
            on_image,
            QoSProfile(
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
                reliability=ReliabilityPolicy.BEST_EFFORT,
            ),
        )
        return feed

    return CameraCapture(
        device=os.environ.get('NEURAVAC_CAMERA_DEVICE', '/dev/neuravac_camera'),
        width=int(os.environ.get('NEURAVAC_CAMERA_WIDTH', '1280')),
        height=int(os.environ.get('NEURAVAC_CAMERA_HEIGHT', '720')),
    )


def main(args=None):
    rclpy.init(args=args)

    serial_bridge = SerialBridge('serial_tx', SerialData)
    lidar_bridge = LidarBridge('lidar_points', LidarPoint)
    camera = build_camera(lidar_bridge.bridge)

    executor = MultiThreadedExecutor()
    executor.add_node(serial_bridge.bridge)
    executor.add_node(lidar_bridge.bridge)
    threading.Thread(target=executor.spin, daemon=True).start()

    web_root = os.environ.get('NEURAVAC_WEB_ROOT') or get_package_share_directory('web')
    template_dir = os.path.join(web_root, 'templates')
    static_dir = os.path.join(web_root, 'static')
    camera.start()
    app = create_app(serial_bridge, lidar_bridge, template_dir, static_dir, camera)

    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        camera.close()
        executor.shutdown()
        serial_bridge.bridge.destroy_node()
        lidar_bridge.bridge.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
