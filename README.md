# NeuraVac

## Read sensor data

`sensors.py` prints all sensor values as JSON, once per second. It defaults to
the Roomba 680 Open Interface group 100 (80 bytes, packets 7-58), including
bumps, cliffs, dirt, infrared, buttons, odometry, battery, signal strengths,
encoders, motor currents, and interface status. Unsupported/reserved fields
remain visible as raw values; hardware availability varies by model.

Install the serial dependency in your Python environment:

```sh
python3 -m pip install pyserial
```

On the Raspberry Pi, replace the device name with your serial adapter:

```sh
python3 sensors.py --port /dev/ttyUSB0 --baud 115200 --once --pretty
python3 sensors.py --port /dev/ttyUSB0 --baud 115200 --interval 1
```

On Windows, `python sensors.py --once --pretty` uses `PORT` and `BAUD_RATE`
from `config.json`. `--port`, `--baud`, and `--config` override those settings.
Output without `--pretty` is one JSON object per line, suitable for logging:

```sh
python3 sensors.py --port /dev/ttyUSB0 --baud 115200 > sensors.jsonl
```

The older [SCI manual](docs/Roomba_SCI_manual.md) defines "all sensors" as
group 0, a 26-byte response. To follow that manual exactly on an SCI robot:

```sh
python3 sensors.py --protocol sci --port /dev/ttyUSB0 --baud 57600 --once --pretty
```

The SCI decoder follows that manual's byte order, signed values, bit masks,
and angle conversion. The 680 decoder follows the
[iRobot Roomba 600/Create 2 OI specification](https://cdn-shop.adafruit.com/datasheets/create_2_Open_Interface_Spec.pdf):
OI angles are already degrees, button meanings differ, and the older right
dirt detector/caster-drop/vacuum-overcurrent fields are unused.

Distance and angle are changes **since the previous request**, not lifetime
totals. Battery current is negative during discharge and positive when charging;
it measures the whole battery, not the serial port's power draw. Encoder counts
wrap at 65535. Requested velocities describe commands, not measured speeds.
Older 600 firmware can return inaccurate odometry values.

The script starts passive mode and sends no driving commands. Press Ctrl+C to
close the port. Passive mode can sleep after five minutes; wake the robot with
CLEAN if reads time out. Close `wired.py`, `webapp.py`, or any other serial client
before running this script. Responses have no checksum; after an incomplete
response the script exits rather than interpreting misaligned bytes.
