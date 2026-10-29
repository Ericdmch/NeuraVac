"""Apply integration edits to the Pi checkout without replacing unrelated work."""
from pathlib import Path
root = Path.home() / 'Neuravac'

def edit(path, fn):
    p = root / path
    p.write_text(fn(p.read_text()))

def lidar(s):
    if 'ScanAssembler' in s:
        return s
    s = s.replace('from rclpy.node import Node', 'from rclpy.node import Node\nfrom rclpy.time import Time\nfrom rclpy.qos import qos_profile_sensor_data\nfrom sensor_msgs.msg import LaserScan\nfrom neuravac_mapping.scan_math import ScanAssembler')
    s = s.replace('self._buffer = bytearray()', "self._buffer = bytearray()\n        self._scan_assembler = ScanAssembler()\n        self._scan_pub = self.create_publisher(LaserScan, 'scan_raw', qos_profile_sensor_data)", 1)
    s = s.replace('''                self.lidar_points.publish(point)''', '''                self.lidar_points.publish(point)
                stamp = self.get_clock().now().nanoseconds * 1e-9
                scan = self._scan_assembler.add(point.angle_deg, point.distance_mm, stamp)
                if scan is not None:
                    self.publish_scan(scan)''')
    idx = s.index('    def extract_packet(self):')
    s = s[:idx] + '''    def publish_scan(self, scan):
        message = LaserScan()
        message.header.stamp = Time(seconds=scan['stamp']).to_msg()
        message.header.frame_id = 'lidar_link'
        message.angle_min = 0.0
        message.angle_increment = scan['angle_increment']
        message.angle_max = (len(scan['ranges']) - 1) * message.angle_increment
        message.scan_time = scan['duration']
        message.time_increment = scan['duration'] / len(scan['ranges'])
        message.range_min, message.range_max = 0.12, 8.0
        message.ranges = scan['ranges']
        self._scan_pub.publish(message)

''' + s[idx:]
    return s

edit('src/lidar/lidar/lidar_node.py', lidar)
edit('src/lidar/package.xml', lambda s: s if 'neuravac_mapping' in s else s.replace(
    '<exec_depend>python3-serial</exec_depend>', '<exec_depend>python3-serial</exec_depend>\n  <exec_depend>sensor_msgs</exec_depend>\n  <exec_depend>neuravac_mapping</exec_depend>'))

def bringup(s):
    if 'slam_backend' in s:
        return s
    s = s.replace('from launch.actions import ', 'from launch.launch_description_sources import PythonLaunchDescriptionSource\nfrom launch.actions import IncludeLaunchDescription, ')
    start = s.index("        if enabled(context, 'use_slam'):")
    stop = s.index('\n    use_vision = ', start)
    s = s[:start] + '''        if enabled(context, 'use_slam'):
            backend = LaunchConfiguration('slam_backend').perform(context)
            if backend == 'toolbox':
                nodes.append(IncludeLaunchDescription(PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory('neuravac_mapping'),
                                 'launch', 'mapping.launch.py'))))
            elif backend == 'legacy':
                nodes.append(Node(
                    package='neuravac_slam', executable='slam_node', name='neuravac_slam',
                    parameters=[package_config('neuravac_slam', 'slam_params.yaml')],
                    output='screen', respawn=True, respawn_delay=3.0))
            else:
                raise ValueError('slam_backend must be toolbox or legacy')
''' + s[stop:]
    s = s.replace('    arguments = [', "    arguments = [\n        DeclareLaunchArgument('slam_backend', default_value='toolbox'),")
    return s

edit('src/bringup/launch/robot.launch.py', bringup)
edit('src/bringup/package.xml', lambda s: s if '<exec_depend>neuravac_mapping</exec_depend>' in s else s.replace(
    '</package>', '  <exec_depend>neuravac_mapping</exec_depend>\n</package>'))

def arrow(s):
    # User requested another half-turn from the deployed +90-degree arrow.
    return s.replace('context.rotate(heading + Math.PI / 2);',
                     'context.rotate(heading + 3 * Math.PI / 2);').replace(
                     'Display-only clockwise quarter-turn', 'Display-only 270-degree offset')
edit('src/web/web/static/components.js', arrow)
