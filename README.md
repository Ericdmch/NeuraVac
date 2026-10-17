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


## ROS 2 serial bridge and website

The ROS 2 bridge keeps the existing `src/roomba.py` `Roomba` class as the
hardware interface and owns the serial port. It publishes bytes received from
the Roomba serial monitor on `/roomba/serial_monitor/messages`
(`std_msgs/msg/String`), publishes connection state on `/roomba/serial/status`,
and accepts hexadecimal opcode strings on `/roomba/serial_monitor/commands`.
The Flask website subscribes to those topics and forwards browser commands to
the bridge, so it does not open the serial port itself.

Make this repository available under the `src` directory of a ROS 2 workspace
(for example, as a symlink named `neuravac_ros`), then build and source it:

```sh
cd ~/ros2_ws
colcon build --packages-select neuravac_ros
source install/setup.bash
```

Set `PORT` in `config.json` to the robot's serial device. Start the bridge,
then run the website in another terminal with the same ROS environment sourced:

```sh
ros2 launch neuravac_ros neuravac.launch.py
python3 website/app.py
```

The website process also needs the ROS 2 Python environment because it subscribes
to the bridge topics. On Windows, run both commands in the same Ubuntu/WSL 2
environment where ROS 2 is installed and the robot's USB serial device is
available. Without ROS 2, Flask can still serve the dashboard, but the serial
monitor will show disconnected and cannot send or receive data.

The serial monitor is available on ROS topics for other nodes too. Do not run
`sensors.py`, `tests/wired.py`, or another serial client at the same time; the
bridge must be the only process using the Roomba serial port. The browser's raw
opcode monitor is intended for diagnostics; normal motion behavior should use
validated robot commands.

## Minimum Viable Product

### Artifical Intelligenc
- Analyze images of floor and detect debris
- Draw rectangles around  debris for roomba to navigat

### Slam
- Plot roomba location in birds eye
