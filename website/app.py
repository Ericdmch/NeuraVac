from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.post("/api/serial-monitor")
def serial_monitor():
    """Print text submitted by the browser serial monitor."""
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        message = payload.get("message")
    else:
        message = request.get_data(as_text=True)

    if not isinstance(message, str) or not message.strip():
        return jsonify(error="message must be a non-empty string"), 400

    print(f"[serial monitor] {message}", flush=True)
    return jsonify(message=message), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)