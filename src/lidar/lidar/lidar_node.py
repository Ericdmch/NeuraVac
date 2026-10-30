import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.time import Time
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from neuravac_mapping.scan_math import ScanAssembler
import serial
from serial import SerialException
from roomba_interfaces.msg import LidarPoint, SerialData

class Lidar(Node):
    def __init__(self):
        super().__init__('lidar_node')

        # Serial connection
        self.declare_parameter('serial_port', '/dev/neuravac_lidar')
        self.declare_parameter('baudrate', 230400)

        serial_port = self.get_parameter('serial_port').value
        baudrate = self.get_parameter('baudrate').value
        
        try:
            self.serial = serial.Serial(
                port=serial_port,
                baudrate=baudrate,
                timeout=0,
            )
        except serial.SerialException as error:
            self.get_logger().error(
                f'Unable to open Lidar serial port {serial_port!r}: {error}'
            )
            raise

        self.get_logger().info(
            f'Lidar serial connection opened on {serial_port} at {baudrate} baud'
        )

        # ROS2 Serial topics (15ms / ~66 Hz drains incoming serial buffer cleanly without 500 Hz CPU spin)
        self.serial_timer = self.create_timer(0.015, self.read_serial)
        
        self.lidar_points = self.create_publisher(
            LidarPoint,
            'lidar_points',
            1000
        )
        
        # self.send_raw = False

        # if self.send_raw:
        #     self.lidar_raw = self.create_publisher(
        #         SerialData, 
        #         'lidar_raw',
        #         10
        #     )

        # Parseing lidar data
        self._buffer = bytearray()
        self._scan_assembler = ScanAssembler()
        self._scan_pub = self.create_publisher(LaserScan, 'scan_raw', qos_profile_sensor_data)

    def read_serial(self):
        waiting = self.serial.in_waiting
        if waiting == 0:
            return

        data = self.serial.read(waiting)

        # if self.send_raw:
        #     self.lidar_raw.publish(SerialData(data=data))

        self._buffer.extend(data)


        points = self.extract_packet()
        if points:
            for point in points:
                self.lidar_points.publish(point)
                stamp = self.get_clock().now().nanoseconds * 1e-9
                scan = self._scan_assembler.add(point.angle_deg, point.distance_mm, stamp)
                if scan is not None:
                    self.publish_scan(scan)


    def publish_scan(self, scan):
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

    def extract_packet(self):
        """
        0-1	Header (AA 55)	    2 bytes
        2	M&T	                1 byte
        3	LSN (sample count)	1 byte
        4-5	FSA (start angle)	2 bytes
        6-7	LSA (end angle)	    2 bytes
        8-9	CS (checksum)	    2 bytes
        10 onward	            Samples	3 bytes per sample

        Returns a list of LidarPoint objects, each containing angle, distance, and intensity.
        Clears up the buffer too
        """

        points = []
        while True:
            start = self._buffer.find(b'\xAA\x55')

            if start == -1:
                if self._buffer.endswith(b'\xAA'):
                    self._buffer = bytearray(b"\xAA")
                else:
                    self._buffer.clear()
            
                return points
            
            if start:
                del self._buffer[:start]

            if len(self._buffer) < 4:
                return points

            lsn = self._buffer[3]
            packet_length = 10 + lsn * 3

            if len(self._buffer) < packet_length:
                return points

            packet = self._buffer[:packet_length]
            del self._buffer[:packet_length]

            decoded = self.decode_packet(packet)
            if decoded:
                points.extend(decoded)

    
    def checksum(self, received_cs, packet):
        lsn = packet[3]

        calculated_cs = 0x55AA
        calculated_cs ^= (lsn << 8) | packet[2]
        calculated_cs ^= int.from_bytes(packet[4:6], 'little')
        calculated_cs ^= int.from_bytes(packet[6:8], 'little')

        for i in range(lsn):
            offset = 10 + i * 3

            # First sample byte: intensity
            calculated_cs ^= packet[offset]

            # Next two bytes: distance data
            calculated_cs ^= int.from_bytes(
                packet[offset + 1:offset + 3], 'little'
            )

        return calculated_cs == received_cs

    def decode_packet(self,packet, polar = True):
        
        header = packet[0:2]
        m_and_t = packet[2]
        lsn = packet[3]
        fsa = int.from_bytes(packet[4:6], byteorder='little', signed=False)
        lsa = int.from_bytes(packet[6:8], byteorder='little', signed=False)
        cs = int.from_bytes(packet[8:10], byteorder='little', signed=False)
        samples = packet[10:]

        expected_len = 10 + lsn * 3
        if len(packet) != expected_len:
            self.get_logger().warning("Invalid packet length")
            return

        packet_type = m_and_t & 0b1
        scan_frequency = m_and_t >> 1

        start_angle = (fsa >> 1) / 64.0
        end_angle = (lsa >> 1) / 64.0
        angle_diff = end_angle - start_angle

        if angle_diff < 0:
            angle_diff += 360.0


        if not self.checksum(cs, packet):
            self.get_logger().warning("Invalid checksum")
            return

        points = []

        for i in range(lsn):
            b0, b1, b2 = samples[i * 3: (i+1) * 3]

            distance = (b2 << 6) | (b1 >> 2)
            intensity = ((b1 & 0x03) << 6) | (b0 >> 2)

            if lsn <= 1:
                angle = start_angle
            else:
                angle = start_angle + (angle_diff / (lsn - 1)) * i
                        
            points.append(LidarPoint(
                angle_deg=angle,
                distance_mm=distance,
                intensity=intensity
            ))
            
        return points


def main(args=None):
    rclpy.init(args=args)

    try:
        node = Lidar()

        rclpy.spin(node)

    except (SerialException, KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if 'node' in locals():
            if node.serial.is_open:
                node.serial.close()
            node.destroy_node()
        rclpy.try_shutdown()
