from flask import Flask, jsonify, render_template, request
from ament_index_python.packages import get_package_share_directory
import os
import rclpy
from rclpy.node import Node
from roomba_interfaces.msg import SerialData, LidarPoint
import threading

app = Flask(__name__)

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
        self.bridge.add_publisher(data_type, topic)
        
        self.topic = topic

    def send_serial_data(self, data):
        msg = SerialData()

        # throw out all non integers, processes the string into a list of integers
        msg.data = [int(t) for t in data.replace(',', ' ').split() if t.isdigit()]

        self.bridge.publish(self.topic, msg)

class LidarBridge:
    def __init__(self, topic, data_type = LidarPoint):
        self.bridge = WebBridge(name='web_lidar_node')
        self.bridge.add_subscriber(data_type, topic, self.lidar_callback)

        self.topic = topic

    def lidar_callback(self, msg):
        self.bridge.get_logger().info(f"Deg: {msg.angle_deg}, Dst: {msg.distance_mm}, Int: {msg.intensity}")

    
# def create_app(serial_bridge, template_dir):
#     app = Flask(__name__, template_folder=template_dir)

#     @app.get('/')
#     def index():
#         return render_template('index.html')

#     @app.post('/submit')
#     def submit():
#         payload = request.get_json(silent=True)
#         serial_data = payload.get('data', '').strip() if payload else ''

#         if not serial_data:
#             return jsonify(error='Serial data is required'), 400

#         serial_bridge.send_serial_data(serial_data)

#         return jsonify(message=serial_data)

#     return app



def main(args=None):
    rclpy.init(args=args)
    lidar_bridge = LidarBridge('lidar_points', LidarPoint)
    try:
        rclpy.spin(lidar_bridge.bridge)
    except KeyboardInterrupt:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


    # rclpy.init(args=args)
    # serial_bridge = SerialBridge('serial_data', SerialData)
    # threading.Thread(target=rclpy.spin, args=(serial_bridge.bridge,), daemon=True).start()

    # template_dir = os.path.join(get_package_share_directory('web'), 'templates')
    # app = create_app(serial_bridge, template_dir)

    # try:
    #     app.run(host='0.0.0.0', port=5000, debug=False)
    # finally:
    #     serial_bridge.bridge.destroy_node()
    #     rclpy.shutdown()