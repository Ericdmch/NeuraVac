import rclpy
from rclpy.node import Node
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

        # ROS2 Serial topics
        self.serial_timer = self.create_timer(0.01, self.read_serial)
        
        self.lidar_points = self.create_publisher(
            LidarPoint,
            'lidar_points',
            10
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

        while True:
            start = self._buffer.find(b'\xAA\x55')

            if start == -1:
                if self._buffer.endswith(b'\xAA'):
                    self._buffer = bytearray(b"\xAA")
                else:
                    self._buffer.clear()
            
                return
            
            if start:
                del self._buffer[:start]

            if len(self._buffer) < 4:
                return

            lsn = self._buffer[3]
            packet_length = 10 + lsn * 3

            if len(self._buffer) < packet_length:
                return

            packet = self._buffer[:packet_length]
            del self._buffer[:packet_length]

            return self.decode_packet(packet)

    
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

    except (SerialException, KeyboardInterrupt):
        pass
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()
