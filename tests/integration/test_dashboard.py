from fastapi.testclient import TestClient

from dashboard.backend.app import create_app


def test_dashboard_idle_explicit_start_pause_and_estop(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "test.db", background=False)) as client:
        assert client.get("/api/state").json()["state"] == "IDLE"
        assert client.post("/api/mission/start").status_code == 200
        assert client.post("/api/mission/start").status_code == 409
        assert client.post("/api/mission/pause").json()["state"] == "PAUSED"
        assert client.post("/api/mission/estop").json()["safety"]["latched"]
        assert client.get("/api/history/cleaning_attempts").status_code == 200
        assert client.get("/api/history/garbage").status_code == 404
        with client.websocket_connect("/ws") as websocket:
            assert websocket.receive_json()["state"] == "FAULT"


def test_remote_controls_require_token_and_websocket_auth(tmp_path):
    with TestClient(
        create_app(db_path=tmp_path / "secure.db", background=False, api_token="private")
    ) as client:
        assert client.post("/api/mission/start").status_code == 401
        assert (
            client.post(
                "/api/mission/start", headers={"Authorization": "Bearer private"}
            ).status_code
            == 200
        )
        assert client.get("/api/state").status_code == 401
        assert (
            client.get("/api/state", headers={"Authorization": "Bearer private"}).status_code == 200
        )


def test_websocket_first_message_auth_accepts_valid_and_rejects_bad_token(tmp_path):
    import pytest
    from starlette.websockets import WebSocketDisconnect

    with TestClient(
        create_app(db_path=tmp_path / "ws.db", background=False, api_token="private")
    ) as client:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"token": "private"})
            assert websocket.receive_json()["state"] == "IDLE"
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"token": "wrong"})
            with pytest.raises(WebSocketDisconnect):
                websocket.receive_json()
