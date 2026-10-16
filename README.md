# NeuraVac

## Read sensor data

`neuravac.hardware.sensors` prints all sensor values as JSON, once per second. It defaults to
the Roomba 680 Open Interface group 100 (80 bytes, packets 7-58), including
bumps, cliffs, dirt, infrared, buttons, odometry, battery, signal strengths,
encoders, motor currents, and interface status. Unsupported/reserved fields
remain visible as raw values; hardware availability varies by model.

Install the runtime dependencies in your Python environment:

```sh
python3 -m pip install -e .
```

On the Raspberry Pi, replace the device name with your serial adapter:

```sh
python3 -m neuravac.hardware.sensors --port /dev/ttyUSB0 --baud 115200 --once --pretty
python3 -m neuravac.hardware.sensors --port /dev/ttyUSB0 --baud 115200 --interval 1
```

On Windows, pass the repository configuration file explicitly. It contains
`PORT` and `BAUD_RATE`; `--port`, `--baud`, and `--config` override those
settings:

```sh
env\Scripts\python.exe -m pip install -e .
env\Scripts\python.exe -m neuravac.hardware.sensors --config config.json --once --pretty
```

Use the same interpreter to start the web app:

```sh
env\Scripts\python.exe -m neuravac
```

The `python` and `pip` commands must refer to the same environment. If the
virtual environment is activated, these equivalent commands are sufficient:

```sh
python -m pip install -e .
python -m neuravac.hardware.sensors --config config.json --once --pretty
```

Output without `--pretty` is one JSON object per line, suitable for logging:

```sh
python3 -m neuravac.hardware.sensors --config config.json \
  --port /dev/ttyUSB0 --baud 115200 > sensors.jsonl
```

The older [SCI manual](docs/Roomba_SCI_manual.md) defines "all sensors" as
group 0, a 26-byte response. To follow that manual exactly on an SCI robot:

```sh
python3 -m neuravac.hardware.sensors --protocol sci \
  --port /dev/ttyUSB0 --baud 57600 --once --pretty
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
CLEAN if reads time out. Close any other serial client before running this
script. Responses have no checksum; after an incomplete response the script
exits rather than interpreting misaligned bytes.

## Run the web app

The Flask app is exposed through the package entry point:

```sh
python -m neuravac
```

It serves the web interface at `http://127.0.0.1:5000/`. The app uses the
Roomba controller in `neuravac.hardware.roomba` and the shared helpers in
`neuravac.helpers`.

## Project layout

| Path | Purpose |
| --- | --- |
| `neuravac/__main__.py` | Runs the web app with `python -m neuravac` |
| `neuravac/web/app.py` | Flask routes and web interface |
| `neuravac/hardware/roomba.py` | Roomba serial controller |
| `neuravac/hardware/sensors.py` | Sensor polling and JSON output |
| `neuravac/helpers.py` | Shared configuration and protocol helpers |
| `neuravac/secrets.py` | Reads values from the local `secrets.env` file |
| `neuravac/nebius.py` | Provides the Nebius OpenAI-compatible client class |
| `config.json` | Local serial port and baud-rate settings |

## Reading secrets

Keep local secrets in the Git-ignored `secrets.env` file using `KEY=value`
entries:

```dotenv
ROBOT_API_KEY="replace-me"
```

Read a value by key without printing it:

```python
from neuravac.secrets import get_secret

api_key = get_secret("ROBOT_API_KEY")
```

For Nebius, add `NEBIUS_API_KEY` to `secrets.env`. The configured
Create the configured OpenAI-compatible client with:

```python
from neuravac.nebius import Nebius

nebius = Nebius()
response = nebius.client.chat.completions.create(
    model="your-model",
    messages=[{"role": "user", "content": "Hello"}],
)
```


## Minimum Viable Product

### Artifical Intelligenc
- Analyze images of floor and detect debris
- Draw rectangles around  debris for roomba to navigat

### Slam
- Plot roomba location in birds eye
