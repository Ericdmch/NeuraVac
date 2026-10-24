import rclpy
from rclpy.node import Node
import serial
from serial import SerialException
from roomba_interfaces.msg import SerialData
from dataclasses import dataclass

@dataclass
class LidarPacket:
    header: bytes
    m_and_t: int
    lsn: int
    fsa: int
    lsa: int
    cs: int
    samples: list

@dataclass
class Point:
    angle_deg: float
    distance_mm: float
    intensity: int

class Lidar(Node):
    def __init__(self):
        super().__init__('lidar_node')

        # Serial connection
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
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
        # self.lidar_raw = self.create_publisher(
        #     SerialData, 
        #     'lidar_raw',
        #     10
        #)

        # Parseing lidar data
        self._buffer = bytearray()

    def read_serial(self):
        waiting = self.serial.in_waiting
        if waiting == 0:
            return

        data = self.serial.read(waiting)

        # self.lidar_raw.publish(SerialData(data=data))
        # self.get_logger().info(f'Received {len(data)} bytes from Lidar: {data.hex()}')

        self._buffer.extend(data)

        self.extract_packets()

    def extract_packets(self):
        """
        0-1	Header (AA 55)	    2 bytes
        2	M&T	                1 byte
        3	LSN (sample count)	1 byte
        4-5	FSA (start angle)	2 bytes
        6-7	LSA (end angle)	    2 bytes
        8-9	CS (checksum)	    2 bytes
        10 onward	            Samples	3 bytes per sample
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

            self.decode_packet(packet)

    
    def checksum(recieved_cs, packet):
        calculated_cs = 0
        for i in range(0, 8, 2):
            calculated_cs ^= int.from_bytes(packet[i:i + 2], byteorder='little')

    return calculated_cs == received_cs

    def decode_packet(self,packet, polar = True):
        expected_len = 10 + lsn * 3
        if len(packet) != expected_len:
            self.get_logger().warning("Invalid packet length")
            return

        header = packet[0:2]
        m_and_t = packet[2]
        lsn = packet[3]
        fsa = int.from_bytes(packet[4:6], byteorder='little', signed=False)
        lsa = int.from_bytes(packet[6:8], byteorder='little', signed=False)
        cs = int.from_bytes(packet[8:10], byteorder='little', signed=False)
        samples = packet[10:]

        packet_type = m_and_t & 0b1
        scan_frequency = m_and_t >> 1

        start_angle = (fsa >> 1) / 64.0
        end_angle = (lsa >> 1) / 64.0
        angle_diff = end_angle - start_angle

        if angle_diff < 0:
            angle_diff += 360.0


        if not self.checksum(cs, packet):
            return

        samples = [
            packet[10 + i * 3: 10 + (i + 1) * 3] for i in range(lsn)
        ]
        
            

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

