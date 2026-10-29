from collections import deque
import json
import base64
import math
import os
import threading
import time
import signal

import yaml
from ament_index_python.packages import get_package_share_directory
from flask import Flask, Response, jsonify, render_template, request
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
import rclpy
from rclpy.executors import MultiThreadedExecutor, ExternalShutdownException
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from roomba_interfaces.msg import LidarPoint, SerialData
from roomba_interfaces.srv import RequestTelemetry
from std_srvs.srv import Trigger
from std_msgs.msg import String

from .override import roomba_drive
from .camera import CameraCapture, LatestJpeg
from .telemetry import SensorState


app = Flask(__name__)


# OVERRIDE CONSTANTS
STRAIGHT = 32768

DEFAULT_DRIVE_CONFIG = {
    'default_drive_speed_mm_s': 200,
    'min_drive_speed_mm_s': 50,
    'max_drive_speed_mm_s': 500,
    'drive_speed_step_mm_s': 50,
}

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
        self._telemetry_client = self.bridge.create_client(
            RequestTelemetry, 'request_telemetry'
        )

    def request_telemetry(self):
        if not self._telemetry_client.wait_for_service(timeout_sec=0.5):
            return False
        before = self.sensors.version()
        if not self.sensors.request(time.monotonic()):
            return False

        completed = threading.Event()
        future = self._telemetry_client.call_async(RequestTelemetry.Request())
        future.add_done_callback(lambda _future: completed.set())
        if not completed.wait(timeout=1.0):
            self.sensors.cancel_request()
            return False
        try:
            response = future.result()
        except Exception:
            self.sensors.cancel_request()
            return False
        if not response.accepted:
            self.sensors.cancel_request()
            return False
        if not self.sensors.wait_for_update(before, timeout=1.0):
            self.sensors.cancel_request()
            return False
        return True

    def receive_serial(self, message):
        now = time.monotonic()
        self.sensors.request(now)
        self.sensors.receive(bytes(message.data), now)
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
    STREAM_BATCH_SECONDS = 0.02

    def __init__(self, topic, data_type = LidarPoint):
        self.bridge = WebBridge(name='web_lidar_node')
        self.bridge.add_subscriber(data_type, topic, self.lidar_callback)

        self.topic = topic
        self._condition = threading.Condition()
        self._points = deque(maxlen=1440)
        self._sequence = 0
        self._map_condition = threading.Condition()
        self._map_sequence = 0
        self._map = None
        self._pose_lock = threading.Lock()
        self._slam_pose = None
        self.bridge.add_subscriber(OccupancyGrid, 'slam/map', self.map_callback, 1)
        self.bridge.add_subscriber(PoseStamped, 'slam/pose', self.pose_callback, 10)
        self.bridge.add_subscriber(String, 'slam/status', self.status_callback, 1)
        self._slam_reset_client = self.bridge.create_client(Trigger, 'slam/reset')

    def reset_slam(self):
        if not self._slam_reset_client.wait_for_service(timeout_sec=0.5):
            return False, 'SLAM reset service is unavailable.'
        completed = threading.Event()
        future = self._slam_reset_client.call_async(Trigger.Request())
        future.add_done_callback(lambda _future: completed.set())
        if not completed.wait(timeout=2.0):
            return False, 'SLAM reset request timed out.'
        try:
            response = future.result()
        except Exception as error:
            return False, f'SLAM reset failed: {error}'
        return response.success, response.message

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

    def stream(self):
        """Send only new LiDAR returns with their measurement age."""
        sequence = 0
        while True:
            previous_sequence = sequence
            with self._condition:
                arrived = self._condition.wait_for(
                    lambda: self._sequence > sequence,
                    timeout=0.1,
                )
                if arrived:
                    deadline = time.monotonic() + self.STREAM_BATCH_SECONDS
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            break
                        self._condition.wait(timeout=remaining)
                    sequence = self._sequence
                    cutoff = time.monotonic() - self.RECENT_POINT_MAX_AGE_SECONDS
                    points = [
                        (timestamp, point)
                        for point_sequence, timestamp, point in self._points
                        if point_sequence > previous_sequence and timestamp >= cutoff
                    ]
                else:
                    points = []

            now = time.monotonic()
            batch = []
            for timestamp, point in points:
                x, y = self.polar_to_cartesian(
                    point['angle_deg'], point['distance_mm']
                )
                age_ms = max(0.0, (now - timestamp) * 1000)
                batch.append((x, y, age_ms))
            yield f'data: {json.dumps(batch, separators=(",", ":"))}\n\n'

    def current_sequence(self):
        with self._condition:
            return self._sequence

    def map_callback(self, message):
        encoded = base64.b64encode(bytes(value & 0xff for value in message.data)).decode('ascii')
        payload = {
            'tracking_status': getattr(self, '_tracking_status', 'TRACKING'),
            'width': int(message.info.width),
            'height': int(message.info.height),
            'resolution': float(message.info.resolution),
            'origin_x': float(message.info.origin.position.x),
            'origin_y': float(message.info.origin.position.y),
            'data': encoded,
        }
        with self._pose_lock:
            pose = self._slam_pose
        if pose is not None:
            payload['robot_x'] = pose['x']
            payload['robot_y'] = pose['y']
            payload['robot_yaw'] = pose['yaw']
        with self._map_condition:
            self._map = payload
            self._map_sequence += 1
            self._map_condition.notify_all()

    def status_callback(self, message):
        self._tracking_status = message.data
        with self._map_condition:
            if self._map is not None:
                self._map = {**self._map, 'tracking_status': message.data}
                self._map_sequence += 1
                self._map_condition.notify_all()

    def pose_callback(self, message):
        q = message.pose.orientation
        pose = {
            'x': float(message.pose.position.x),
            'y': float(message.pose.position.y),
            'yaw': math.atan2(
                2.0 * (q.w * q.z + q.x * q.y),
                1.0 - 2.0 * (q.y * q.y + q.z * q.z),
            ),
        }
        with self._pose_lock:
            self._slam_pose = pose
        with self._map_condition:
            if self._map is not None:
                self._map = {**self._map, 'robot_x': pose['x'],
                             'robot_y': pose['y'], 'robot_yaw': pose['yaw']}
                self._map_sequence += 1
                self._map_condition.notify_all()

    def wait_for_map(self, after_sequence, timeout):
        with self._map_condition:
            self._map_condition.wait_for(
                lambda: self._map_sequence > after_sequence, timeout=timeout
            )
            return self._map_sequence, self._map

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


def create_app(serial_bridge, lidar_bridge, template_dir, static_dir=None, camera=None,
               drive_config=None):
    if static_dir is None:
        static_dir = os.path.join(os.path.dirname(template_dir), 'static')
    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static',
    )
    active_override = None
    settings = {**DEFAULT_DRIVE_CONFIG, **(drive_config or {})}
    min_speed = min(500, max(0, int(settings['min_drive_speed_mm_s'])))
    max_speed = max(
        min_speed, min(500, int(settings['max_drive_speed_mm_s']))
    )
    speed_step = max(1, int(settings['drive_speed_step_mm_s']))
    default_speed = max(
        min_speed, min(max_speed, int(settings['default_drive_speed_mm_s']))
    )
    speed = default_speed

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/drive/config')
    def drive_config_endpoint():
        return jsonify(
            default_speed_mm_s=default_speed,
            min_speed_mm_s=min_speed,
            max_speed_mm_s=max_speed,
            speed_step_mm_s=speed_step,
        )

    @app.get('/telemetry')
    def telemetry():
        response = jsonify(serial_bridge.snapshot())
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.post('/telemetry/request')
    def request_telemetry():
        if not serial_bridge.request_telemetry():
            return jsonify(error='No fresh Roomba sensor response was received.'), 503
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
                    min_speed,
                    min(max_speed, speed + (speed_step if key == 'E' else -speed_step)),
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

    @app.post('/roomba/led')
    def roomba_led():
        payload = request.get_json(silent=True) or {}
        color = payload.get('color')
        intensity = payload.get('intensity')
        if any(not isinstance(value, int) or isinstance(value, bool)
               or value < 0 or value > 255 for value in (color, intensity)):
            return jsonify(error='Color and intensity must be integers from 0 to 255.'), 400
        serial_bridge.send_message(SerialData(data=[139, 0, color, intensity]))
        return jsonify(sent=True, color=color, intensity=intensity)

    @app.post('/roomba/song')
    def roomba_song():
        payload = request.get_json(silent=True) or {}
        song_number = payload.get('song_number')
        notes = payload.get('notes')
        if (not isinstance(song_number, int) or isinstance(song_number, bool)
                or not 0 <= song_number <= 15):
            return jsonify(error='Song number must be an integer from 0 to 15.'), 400
        if not isinstance(notes, list) or not 1 <= len(notes) <= 16:
            return jsonify(error='A song must contain between 1 and 16 notes.'), 400

        note_bytes = []
        for item in notes:
            if not isinstance(item, dict):
                return jsonify(error='Each note must contain note and duration values.'), 400
            note, duration = item.get('note'), item.get('duration')
            if (not isinstance(note, int) or isinstance(note, bool) or not 31 <= note <= 127
                    or not isinstance(duration, int) or isinstance(duration, bool)
                    or not 0 <= duration <= 255):
                return jsonify(error='Notes must be 31–127 and durations 0–255.'), 400
            note_bytes.extend((note, duration))

        # Define the selected slot and play it in one ordered serial write.
        command = [140, song_number, len(notes), *note_bytes, 141, song_number]
        serial_bridge.send_message(SerialData(data=command))
        return jsonify(sent=True, song_number=song_number, note_count=len(notes))

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
        return Response(
            lidar_bridge.stream(), mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache, no-transform',
                'X-Accel-Buffering': 'no',
            },
        )

    @app.get('/slam/map/stream')
    def slam_map_stream():
        def events():
            sequence = 0
            while True:
                sequence, occupancy = lidar_bridge.wait_for_map(sequence, timeout=15.0)
                if occupancy is None:
                    yield ': waiting for LiDAR map\n\n'
                    continue
                yield f'data: {json.dumps(occupancy, separators=(",", ":"))}\n\n'

        return Response(
            events(), mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
        )

    @app.post('/slam/reset')
    def reset_slam():
        success, message = lidar_bridge.reset_slam()
        if not success:
            return jsonify(error=message), 503
        return jsonify(reset=True, message=message)

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
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)

    def interrupt(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupt)

    serial_bridge = SerialBridge('serial_tx', SerialData)
    lidar_bridge = LidarBridge('lidar_points', LidarPoint)
    camera = build_camera(lidar_bridge.bridge)

    executor = MultiThreadedExecutor()
    executor.add_node(serial_bridge.bridge)
    executor.add_node(lidar_bridge.bridge)
    def spin_ros():
        try:
            executor.spin()
        except ExternalShutdownException:
            pass

    ros_thread = threading.Thread(target=spin_ros, daemon=True)
    ros_thread.start()

    web_root = os.environ.get('NEURAVAC_WEB_ROOT') or get_package_share_directory('web')
    template_dir = os.path.join(web_root, 'templates')
    static_dir = os.path.join(web_root, 'static')
    config_path = os.path.join(web_root, 'config', 'web_params.yaml')
    with open(config_path, encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file) or {}
    drive_config = config.get('web_node', {}).get('ros__parameters', {})
    app = create_app(
        serial_bridge, lidar_bridge, template_dir, static_dir, camera,
        drive_config=drive_config,
    )
    camera.start()

    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        camera.close()
        executor.shutdown()
        ros_thread.join(timeout=2.0)
        serial_bridge.bridge.destroy_node()
        lidar_bridge.bridge.destroy_node()
        if rclpy.ok():
            rclpy.try_shutdown()
