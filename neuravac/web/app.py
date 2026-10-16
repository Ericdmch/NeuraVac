import serial
from flask import Flask, jsonify, render_template, request

from neuravac.hardware.roomba import Roomba
from neuravac.protocol import parse_opcode

app = Flask(__name__)
roomba = None


def get_roomba():
    """Create or reconnect the shared Roomba serial connection when needed."""
    global roomba

    if roomba is None:
        roomba = Roomba()

    if not roomba.ser or not roomba.ser.is_open:
        roomba.connect_serial(attempts=0)

    if not roomba.ser or not roomba.ser.is_open:
        raise ConnectionError("Unable to open the Roomba serial port")

    return roomba


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/serial-monitor/status")
def serial_monitor_status():
    """Report whether the Roomba serial connection is available."""
    try:
        get_roomba()
    except ConnectionError as error:
        return jsonify(connected=False, error=str(error)), 503

    return jsonify(connected=True), 200


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
        get_roomba()._send_opcode(code=code)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except (ConnectionError, serial.SerialException) as error:
        return jsonify(error=str(error)), 503

    print(f"[serial monitor] sent {message}", flush=True)
    return jsonify(message=f"sent: {message}"), 200


@app.get("/api/serial-monitor/messages")
def serial_monitor_messages():
    """Read any bytes waiting from the Roomba without blocking."""
    try:
        connection = get_roomba()
        available = connection.ser.in_waiting
        if not available:
            return jsonify(messages=[]), 200

        data = connection.ser.read(available)
    except (ConnectionError, serial.SerialException) as error:
        return jsonify(error=str(error)), 503

    if not data:
        return jsonify(messages=[]), 200

    message = f"received: {data.hex(' ')}"
    print(f"[serial monitor] {message}", flush=True)
    return jsonify(messages=[message]), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)