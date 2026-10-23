from flask import Flask, jsonify, render_template, request
from ament_index_python.packages import get_package_share_directory
import os
import rclpy
from rclpy.node import Node
from roomba_interfaces.msg import SerialData
import threading

app = Flask(__name__)

class WebBridge(Node):
    def __init__(self, data_type, topic):
        super().__init__('web_bridge_node')
        self.serial_tx = self.create_publisher(
            data_type,
            topicro,
            10
        )

    def to_uint8_list(self, data):
        # Convert string data to a list of uint8 values
        return [ord(char) for char in data]

    def send_serial_data(self, data):
        msg = SerialData()
    

        # throw out all non integers, processes the string into a list of integers
        msg.data = [int(t) for t in data.replace(',', ' ').split() if t.isdigit()]

        self.serial_tx.publish(msg)
        self.get_logger().info(f'Sent {len(msg.data)} bytes to serial: {msg.data}')




def create_app(serial_bridge, template_dir):
    app = Flask(__name__, template_folder=template_dir)

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.post('/submit')
    def submit():
        payload = request.get_json(silent=True)
        serial_data = payload.get('data', '').strip() if payload else ''

        if not serial_data:
            return jsonify(error='Serial data is required'), 400

        serial_bridge.send_serial_data(serial_data)

        return jsonify(message=serial_data)

    return app



def main(args=None):
    rclpy.init(args=args)
    serial_bridge = WebBridge(SerialData, 'serial_data')
    threading.Thread(target=rclpy.spin, args=(serial_bridge,), daemon=True).start()

    template_dir = os.path.join(get_package_share_directory('web'), 'templates')
    app = create_app(serial_bridge, template_dir)   # your routes, built inside a function
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        serial_bridge.destroy_node()
        rclpy.shutdown()