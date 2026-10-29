"""Relay SLAM Toolbox's map and map/base TF to existing dashboard contracts."""
from pathlib import Path
import time

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.time import Time
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data
from std_srvs.srv import Trigger
from slam_toolbox.srv import Reset, SerializePoseGraph
from tf2_ros import Buffer, TransformListener, TransformException


class DashboardBridge(Node):
    def __init__(self):
        super().__init__('neuravac_mapping_dashboard')
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        durable = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.map_pub = self.create_publisher(OccupancyGrid, 'slam/map', durable)
        self.pose_pub = self.create_publisher(PoseStamped, 'slam/pose', 10)
        self.status_pub = self.create_publisher(String, 'slam/status', durable)
        self.create_subscription(OccupancyGrid, 'map', self.map_pub.publish, durable)
        self.service_group = ReentrantCallbackGroup()
        self.reset_client = self.create_client(Reset, 'slam_toolbox/reset', callback_group=self.service_group)
        self.save_client = self.create_client(SerializePoseGraph, 'slam_toolbox/serialize_map', callback_group=self.service_group)
        self.create_service(Trigger, 'slam/reset', self.reset, callback_group=self.service_group)
        self.create_service(Trigger, 'slam/save', self.save, callback_group=self.service_group)
        self.last_scan_received = None
        self.create_subscription(LaserScan, 'scan', self.on_scan, qos_profile_sensor_data)
        self.create_timer(.1, self.publish_pose)

    def on_scan(self, _message):
        self.last_scan_received = time.monotonic()

    def publish_pose(self):
        status = 'WAITING FOR LOCALIZATION'
        try:
            tf = self.buffer.lookup_transform('map', 'base_link', Time())
            age = (self.get_clock().now().nanoseconds * 1e-9 -
                   tf.header.stamp.sec - tf.header.stamp.nanosec * 1e-9)
            if age < .5:
                pose = PoseStamped()
                pose.header = tf.header
                pose.pose.position.x = tf.transform.translation.x
                pose.pose.position.y = tf.transform.translation.y
                pose.pose.orientation = tf.transform.rotation
                self.pose_pub.publish(pose)
                status = ('TRACKING' if self.last_scan_received is not None and
                          time.monotonic() - self.last_scan_received < .5 else 'WAITING FOR SCANS')
            else:
                status = 'STALE ODOMETRY'
        except TransformException:
            pass
        self.status_pub.publish(String(data=status))

    async def reset(self, _request, response):
        if not self.reset_client.service_is_ready():
            response.success, response.message = False, 'SLAM Toolbox reset unavailable'
            return response
        request = Reset.Request()
        request.pause_new_measurements = False
        result = await self.reset_client.call_async(request)
        response.success = result.result == Reset.Response.RESULT_SUCCESS
        response.message = 'SLAM Toolbox reset; fresh scans rebuild the map.'
        return response

    async def save(self, _request, response):
        if not self.save_client.service_is_ready():
            response.success, response.message = False, 'SLAM Toolbox save unavailable'
            return response
        path = Path.home() / 'Neuravac/maps/toolbox'
        path.parent.mkdir(parents=True, exist_ok=True)
        request = SerializePoseGraph.Request()
        request.filename = str(path)
        result = await self.save_client.call_async(request)
        response.success = result.result == SerializePoseGraph.Response.RESULT_SUCCESS
        response.message = 'Saved pose graph to ' + str(path)
        return response


def main():
    rclpy.init()
    node = DashboardBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
