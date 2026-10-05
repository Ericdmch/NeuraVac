import serial
import time

import helpers

class Roomba:
    """Control a Roomba through its serial Open Interface commands."""

    def __init__(self):
        # Load the serial connection settings from config.json.
        self.port = helpers.getConfig("PORT")
        self.baud = helpers.getConfig("BAUD_RATE")

        self.ser = None

        # Each command starts with an Open Interface opcode byte.
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
        """Open the serial port, retrying after timeout seconds on failure."""
        try:
            self.ser = serial.Serial(self.port,self.baud)

        except Exception as e:
            if attempts > 0:
                # attempts counts retries remaining after the initial connection.
                print(f"attempting to reconnect.. [{attempts}]")
                time.sleep(timeout)
                self.connect_serial(timeout,attempts-1)
            else:
                print(f"Failed to connect {e}")

    def _send_opcode(self, *args, **kwargs):
        """Send explicit opcode bytes or a named command with optional data."""
        code = kwargs.get("code")

        # Prefer explicit code, then a command name, then positional bytes.
        if not code and "name" in kwargs:
            code = self._get_opcode(kwargs["name"])

        if not code and args:
            if isinstance(args[0], (list, tuple)):
                code = args[0]
            else:
                code = list(args)

        if code and "data" in kwargs:
            # Command parameters follow the opcode in the same byte packet.
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
        """Look up a command's opcode, returning None for unknown names."""
        return self._commands.get(name)

    

    def start_roomba(self, safe_mode=True):
        """Start the interface and select safe or full control mode."""
        # Allow the robot time to process each mode change.
        self._send_opcode(name="start")
        time.sleep(0.2)
        self._send_opcode(name="mode-safe" if safe_mode else "mode-full")
        time.sleep(0.2)

        if self._debug:
            print("Starting Roomba")

    def stop_roomba(self):
        """Return the interface to passive mode and close the serial port."""
        if self.ser and self.ser.is_open:
            self._send_opcode(name="start")
            self.ser.close()

        if self._debug:
            print("Stopping Roomba")

    def set_led(self, color, intensity=255):
        """Set the power LED color and brightness using byte values (0–255)."""
        # A zero LED bitmask leaves the other indicator LEDs off.
        self._send_opcode(name="leds", data=[0b00000000, color, intensity])


    def drive(self, velocity, radius=None):
        """Drive at velocity in mm/s, with an optional turn radius in mm."""
        # Clamp motion parameters to the supported command ranges.
        velocity = max(-500, min(500, int(velocity)))

        if radius is None:
            radius = 0x8000                      # special case: drive straight
        else:
            radius = max(-2000, min(2000, int(radius)))

        # The drive command expects velocity then radius, high byte first.
        data = helpers.split16(velocity) + helpers.split16(radius)
        self._send_opcode(name="drive", data=data)

        print(f"driving velocity: {velocity}   radius {radius}")


    def define_song(self, number, song):
        """Placeholder for defining a song in the robot's song storage."""
        ...
        
if __name__ == "__main__":
    # Manual hardware demo: Enter advances from LED setup to driving to shutdown.
    myRoomba = Roomba()
    myRoomba.connect_serial(attempts=1)
    myRoomba.start_roomba(safe_mode=False)
    myRoomba.set_led(255)
    input()
    myRoomba.drive(500)
    input()
    myRoomba.stop_roomba()
