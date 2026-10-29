"""HTTP interface for the autonomous mapping coordinator."""
import math
from flask import Flask, jsonify, render_template, request


def create_app(bridge):
    app = Flask(__name__)

    @app.get('/')
    def index():
        return render_template('autonomy.html')

    @app.get('/api/state')
    def state():
        response = jsonify(bridge.snapshot())
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.post('/api/mission')
    def mission():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or payload.get('command') not in ('start', 'return', 'stop'):
            return jsonify(error='Invalid mission command'), 400
        command = payload['command']
        body = {'command': command}
        if command == 'start':
            target = payload.get('return_goal')
            if (not isinstance(target, list) or len(target) != 2 or any(
                    isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in target)):
                return jsonify(error='Select a valid return point on the map'), 400
            body['return_goal'] = target
        bridge.send(body)
        return jsonify(message='Request sent; check the mission status for acceptance'), 202

    return app
