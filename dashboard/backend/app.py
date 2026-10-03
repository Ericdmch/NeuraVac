"""Local-first dashboard API. Production serves pre-built frontend assets."""

import asyncio
import contextlib
import hmac
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from neuravac_core.runtime import SimulationRuntime
from neuravac_core.storage import TABLES


def create_app(
    db_path: str | Path = "artifacts/missions.db",
    background: bool = True,
    api_token: str | None = None,
    runtime: SimulationRuntime | None = None,
) -> FastAPI:
    engine = runtime or SimulationRuntime(db_path=db_path)
    token = api_token if api_token is not None else os.environ.get("NEURAVAC_API_TOKEN", "")

    async def authenticate(authorization: str | None = Header(default=None)) -> None:
        if token and not hmac.compare_digest(authorization or "", f"Bearer {token}"):
            raise HTTPException(401, "A valid dashboard token is required")

    async def loop() -> None:
        while True:
            await engine.tick()
            await asyncio.sleep(1 / engine.config.control_hz)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await engine.initialize()
        task = asyncio.create_task(loop()) if background else None
        yield
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await engine.close()

    app = FastAPI(title="NeuraVac", version="0.1.0", lifespan=lifespan)
    app.state.runtime = engine
    guard = [Depends(authenticate)]

    @app.get("/api/state", dependencies=guard)
    async def state():
        return engine.snapshot()

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "mode": "simulation"}

    @app.post("/api/mission/{action}", dependencies=guard)
    async def control(action: str):
        try:
            if action == "start":
                engine.start()
            elif action == "pause":
                await engine.pause()
            elif action == "resume":
                engine.resume()
            elif action == "estop":
                await engine.emergency_stop()
            elif action == "reset":
                engine.reset()
            else:
                raise HTTPException(404, "Unknown mission control")
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        return engine.snapshot()

    @app.post("/api/demo/move-chair", dependencies=guard)
    async def move_chair():
        engine.move_chair()
        return engine.snapshot()

    @app.get("/api/history/{table}", dependencies=guard)
    async def history(table: str):
        if table not in TABLES:
            raise HTTPException(404, "Unknown mission history table")
        return engine.store.export_table(table)

    @app.get("/api/camera", dependencies=guard)
    async def camera():
        # Honest SVG rendering of the simulator floor sensor, never a physical feed claim.
        shapes = []
        for dirt in engine.environment.dirt:
            if dirt.score > 0:
                shapes.append(
                    f'<circle cx="{dirt.x * 100}" cy="{dirt.y * 100}" r="{5 + 10 * dirt.score}" fill="#eab65a"/>'
                )
        for obstacle in engine.environment.obstacles:
            color = "#f36e75" if obstacle.class_name == "cable" else "#778d9b"
            shapes.append(
                f'<circle cx="{obstacle.x * 100}" cy="{obstacle.y * 100}" r="{obstacle.radius * 100}" fill="{color}"/>'
            )
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400"><rect width="600" height="400" fill="#17262e"/>{"".join(shapes)}<text x="12" y="24" fill="white">Simulated camera · labeled floor observation</text></svg>'
        return Response(svg, media_type="image/svg+xml", headers={"Cache-Control": "no-store"})

    @app.websocket("/ws")
    async def websocket(websocket: WebSocket):
        await websocket.accept()
        if token:
            # First-message auth avoids credentials in URL/access logs.
            try:
                auth = await asyncio.wait_for(websocket.receive_json(), timeout=5)
                if not isinstance(auth, dict) or not hmac.compare_digest(
                    str(auth.get("token", "")), token
                ):
                    await websocket.close(code=1008)
                    return
            except (TimeoutError, ValueError, WebSocketDisconnect):
                await websocket.close(code=1008)
                return
        try:
            while True:
                await asyncio.wait_for(websocket.send_json(engine.snapshot()), timeout=1)
                await asyncio.sleep(0.25)
        except (WebSocketDisconnect, TimeoutError, RuntimeError):
            return

    dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="dashboard")
    return app


app = create_app()
