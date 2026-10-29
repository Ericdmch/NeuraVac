"""Read-only end-to-end verification; sends no motor commands."""
import json
import math
import time
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid, Odometry
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from tf2_ros import Buffer, TransformListener, TransformException

rclpy.init()
node = Node('mapping_verification')
buffer = Buffer()
listener = TransformListener(buffer, node)
counts = {name: 0 for name in ('raw', 'scan', 'odom', 'map', 'pose', 'status')}
latest = {}
def callback(name):
    def receive(msg):
        counts[name] += 1
        latest[name] = msg
    return receive
node.create_subscription(LaserScan, 'scan_raw', callback('raw'), qos_profile_sensor_data)
node.create_subscription(LaserScan, 'scan', callback('scan'), qos_profile_sensor_data)
node.create_subscription(Odometry, 'odom', callback('odom'), 10)
node.create_subscription(PoseStamped, 'slam/pose', callback('pose'), 10)
node.create_subscription(String, 'slam/status', callback('status'), 10)
node.create_subscription(OccupancyGrid, 'slam/map', callback('map'),
                         QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
try:
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=.1)
    assert all(counts.values()), counts
    raw, scan = latest['raw'], latest['scan']
    assert raw.angle_increment < 0 and raw.time_increment > 0
    assert scan.header.frame_id == 'lidar_link'
    assert scan.angle_increment > 0 and scan.time_increment == 0
    assert sum(math.isfinite(v) for v in scan.ranges) >= 30
    assert latest['status'].data == 'TRACKING', latest['status'].data
    transforms = {}
    for parent, child in [('map', 'odom'), ('odom', 'base_link'), ('base_link', 'lidar_link')]:
        tf = buffer.lookup_transform(parent, child, Time())
        transforms[parent + ' -> ' + child] = dict(
            x=tf.transform.translation.x, y=tf.transform.translation.y)
    print(json.dumps(dict(counts=counts, tf=transforms, status=latest['status'].data,
        finite_ranges=sum(math.isfinite(v) for v in scan.ranges),
        scan_period_s=scan.scan_time, scan_rays=len(scan.ranges),
        map_size=[latest['map'].info.width, latest['map'].info.height])))
finally:
    node.destroy_node()
    rclpy.try_shutdown()
