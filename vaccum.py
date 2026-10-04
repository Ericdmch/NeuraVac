import serial
import time

import helpers

class Roomba:
    def __init__(self):
        self.port = helpers.getConfig("PORT")
        self.baud = helpers.getConfig("BAUD_RATE")

        self.ser = None

        self._commands = {
            "start": [128],
            "mode-safe": [131],
            "mode-full": [132],
            "power-off": [133],
            "leds": [139],
            "drive": [137],
            "define-song": [140],
            "play-song": [141]
         }

        self._debug = True

    def connect_serial(self, timeout = 3, attempts = 2):
        try:
            self.ser = serial.Serial(self.port,self.baud)

        except Exception as e:
            if attempts > 0:
                print(f"attempting to reconnect.. [{attempts}]")
                time.sleep(timeout)
                self.connect_serial(timeout,attempts-1)
            else:
                print(f"Failed to connect {e}")

    def _send_opcode(self, *args, **kwargs):
        code = kwargs.get("code")

        if not code and "name" in kwargs:
            code = self._get_opcode(kwargs["name"])

        if not code and args:
            if isinstance(args[0], (list, tuple)):
                code = args[0]
            else:
                code = list(args)

        if code and "data" in kwargs:
            code = list(code) + list(kwargs["data"])

        if self.ser and self.ser.is_open and code:
            return self.ser.write(bytes(code))

        if not (self.ser and self.ser.is_open):
            print("Serial not open, nothing sent")
            return 0
        if not code:
            print(f"No opcode found for {kwargs} {args}")
            return 0


        self.ser.flush()

    def _get_opcode(self, name:str):
        return self._commands.get(name)

    

    def start_roomba(self, safe_mode=True):
        self._send_opcode(name="start")
        time.sleep(0.2)
        self._send_opcode(name="mode-safe" if safe_mode else "mode-full")
        time.sleep(0.2)

        if self._debug:
            print("Starting Roomba")

    def stop_roomba(self):
        if self.ser and self.ser.is_open:
            self._send_opcode(name="start")
            self.ser.close()

        if self._debug:
            print("Stopping Roomba")

    def set_led(self, color, intensity=255):
        self._send_opcode(name="leds", data=[0b00000000, color, intensity])


    def drive(self, velocity, radius=None):
        velocity = max(-500, min(500, int(velocity)))

        if radius is None:
            radius = 0x8000                      # special case: drive straight
        else:
            radius = max(-2000, min(2000, int(radius)))

        data = helpers.split16(velocity) + helpers.split16(radius)
        self._send_opcode(name="drive", data=data)

        print(f"driving velocity: {velocity}   radius {radius}")


    def define_song(self, number, song):
        ...
        
if __name__ == "__main__":
    myRoomba = Roomba()
    myRoomba.connect_serial(attempts=1)
    myRoomba.start_roomba(safe_mode=False)
    myRoomba.set_led(255)
    input()
    myRoomba.drive(500)
    input()
    myRoomba.stop_roomba()