import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from neuravac_ros.web_gateway import RosWebGateway
from src.helpers import parse_opcode

app = Flask(__name__)
gateway = RosWebGateway()


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/serial-monitor/status")
def serial_monitor_status():
    """Report the serial status last reported by the ROS 2 bridge."""
    connected = gateway.connected
    return jsonify(connected=connected, error=gateway.error), 200 if connected else 503


@app.post("/api/serial-monitor")
def serial_monitor():
    """Send opcode bytes submitted by the browser serial monitor to the Roomba."""
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        message = payload.get("message")
    else:
        message = request.get_data(as_text=True)

    if not isinstance(message, str) or not message.strip():
        return jsonify(error="message must be a non-empty string"), 400

    try:
        code = parse_opcode(message)
        gateway.send_command(code)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except RuntimeError as error:
        return jsonify(error=str(error)), 503

    print(f"[serial monitor] sent {message}", flush=True)
    return jsonify(message=f"sent: {message}"), 200


@app.get("/api/serial-monitor/messages")
def serial_monitor_messages():
    """Return serial bytes received by the ROS 2 bridge since the last poll."""
    return jsonify(messages=gateway.drain_messages()), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
