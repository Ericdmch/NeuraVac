"""
THIS FILE IS NOT A ROS2 NODE OR PACKAGE
MEANT FOR WEB-ONLY TESTING OF THE REACT FRONTEND WITHOUT A ROS2 ENVIRONMENT
"""

import math
import json
import os
import time

from flask import Flask, Response, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SPEED = 200
MIN_SPEED = 50
MAX_SPEED = 500
SPEED_STEP = 50


class FakeSerialBridge:
    def send_serial_data(self, data):
        print(f'[web-only] would send to serial: {data}')


class FakeLidarBridge:
    def relocalize_slam(self):
        return False, 'SLAM relocalization is unavailable in web-only mode.'

    def snapshot(self):
        return {
            'points': [
                {
                    # make a circle with a sine wave pattern for distance
                    'angle_deg': angle,
                    'distance_mm': 500,
                    'intensity': 100,
                }
                for angle in range(0, 360, 1)
            ],
        }

    def polar_to_cartesian(self, angle_deg, distance_mm):
        angle_rad = math.radians(angle_deg)
        x = distance_mm * math.cos(angle_rad)
        y = distance_mm * math.sin(angle_rad)
        return x, y


def find_web_dirs():
    try:
        from ament_index_python.packages import get_package_share_directory
        share = get_package_share_directory('web')
        return os.path.join(share, 'templates'), os.path.join(share, 'static')
    except Exception:
        return os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'static')


def create_app(serial_bridge, lidar_bridge, template_dir, static_dir):
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir,
                static_url_path='/static')
    speed = DEFAULT_SPEED

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.post('/submit')
    def submit():
        payload = request.get_json(silent=True) or {}
        text = str(payload.get('data', '')).strip()
        if not text:
            return jsonify(error='Serial data is required'), 400
        serial_bridge.send_serial_data(text)
        return jsonify(message=text)

    @app.post('/override')
    def override():
        nonlocal speed
        payload = request.get_json(silent=True) or {}
        key = str(payload.get('key', '')).upper()
        pressed = payload.get('pressed')
        if key not in {'Q', 'W', 'E', 'A', 'S', 'D'} or not isinstance(pressed, bool):
            return jsonify(error='A valid override key and pressed state are required'), 400
        print(f'[override] key {key} {"pressed" if pressed else "released"}')
        if pressed and key in {'Q', 'E'}:
            speed = max(
                MIN_SPEED,
                min(MAX_SPEED, speed + (SPEED_STEP if key == 'E' else -SPEED_STEP)),
            )
        return jsonify(key=key, pressed=pressed, speed=speed)

    @app.post('/slam/relocalize')
    def relocalize_slam():
        success, message = lidar_bridge.relocalize_slam()
        if not success:
            return jsonify(error=message), 503
        return jsonify(relocalized=True, message=message)

    @app.get('/lidar')
    def lidar():
        return jsonify(lidar_points())

    def lidar_points():
        return [
            {
                'x': lidar_bridge.polar_to_cartesian(point['angle_deg'], point['distance_mm'])[0],
                'y': lidar_bridge.polar_to_cartesian(point['angle_deg'], point['distance_mm'])[1],
            }
            for point in lidar_bridge.snapshot()['points']
        ]

    @app.get('/lidar/stream')
    def lidar_stream():
        def events():
            while True:
                yield f'data: {json.dumps(lidar_points(), separators=(",", ":"))}\n\n'
                time.sleep(0.2)

        return Response(
            events(),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
        )



    return app


def main():
    template_dir, static_dir = find_web_dirs()
    print('templates:', template_dir, os.path.isdir(template_dir))
    print('static:   ', static_dir, os.path.isdir(static_dir))
    print('files:    ', os.listdir(static_dir) if os.path.isdir(static_dir) else 'MISSING')

    app = create_app(FakeSerialBridge(), FakeLidarBridge(), template_dir, static_dir)
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
