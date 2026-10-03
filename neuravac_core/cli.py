import argparse
import asyncio
import json
import os
from pathlib import Path

from neuravac_core.config import load_config
from neuravac_core.recording import SessionRecorder, replay_events, replay_world
from neuravac_core.runtime import SimulationRuntime
from neuravac_core.utils.logging import configure_logging
from sim.sim2d.environment import Environment


async def demo(args) -> None:
    config = load_config(args.config)
    cloud = None
    if args.cloud:
        from neuravac_core.cloud import NebiusClient, NebiusConfig

        cloud = NebiusClient(NebiusConfig.from_env())
    runtime = SimulationRuntime(
        config=config,
        environment=Environment.from_yaml(args.scenario),
        db_path=args.database,
        cloud=cloud,
        recorder=SessionRecorder(args.record) if args.record else None,
    )
    try:
        await runtime.initialize()
        runtime.start()
        await runtime.run_until_terminal(realtime=bool(args.cloud or args.realtime))
        result = runtime.snapshot()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "state": result["state"],
                    "mode": result["mode"],
                    "cloud": result["cloud"],
                    "metrics": result["metrics"],
                    "attempts": result["attempts"],
                    "output": str(args.output),
                },
                indent=2,
            )
        )
        if result["state"] != "COMPLETE":
            raise SystemExit(1)
    finally:
        await runtime.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="NeuraVac: observe, act, verify physical outcomes")
    parser.add_argument("--config", default=os.getenv("NEURAVAC_CONFIG", "config/robot.yaml"))
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("demo", help="Run deterministic complete cleaning scenario")
    run.add_argument("--scenario", type=Path, default=Path("config/demo.yaml"))
    run.add_argument(
        "--cloud", action="store_true", help="Explicitly use configured Nebius/Nemotron runtime"
    )
    run.add_argument("--realtime", action="store_true")
    run.add_argument("--record", type=Path)
    run.add_argument("--database", default="artifacts/missions.db")
    run.add_argument("--output", type=Path, default=Path("artifacts/demo.json"))
    web = commands.add_parser("dashboard", help="Live simulator dashboard; starts IDLE")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8000)
    web.add_argument("--cloud", action="store_true")
    replay = commands.add_parser(
        "replay", help="Read recorded observations without actuator access"
    )
    replay.add_argument("session", type=Path)
    export = commands.add_parser("export", help="Export mission SQLite table to CSV")
    export.add_argument(
        "table",
        choices=[
            "missions",
            "cleaning_regions",
            "cleaning_attempts",
            "safety_events",
            "ai_decisions",
        ],
    )
    export.add_argument("--database", default="artifacts/missions.db")
    export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    configure_logging()
    if args.command == "demo":
        asyncio.run(demo(args))
    elif args.command == "dashboard":
        if args.host not in ("127.0.0.1", "localhost", "::1"):
            if not os.getenv("NEURAVAC_API_TOKEN"):
                parser.error("remote binding requires NEURAVAC_API_TOKEN")
        import uvicorn

        from dashboard.backend.app import create_app

        cloud = None
        if args.cloud:
            from neuravac_core.cloud import NebiusClient, NebiusConfig

            cloud = NebiusClient(NebiusConfig.from_env())
        runtime = SimulationRuntime(
            config=load_config(args.config), db_path="artifacts/missions.db", cloud=cloud
        )
        uvicorn.run(create_app(runtime=runtime), host=args.host, port=args.port)
    elif args.command == "replay":
        world = replay_world(args.session, load_config(args.config))
        print(
            json.dumps(
                {"events": sum(1 for _ in replay_events(args.session)), "world": world.to_dict()},
                indent=2,
            )
        )
    else:
        from neuravac_core.storage import MissionStore

        store = MissionStore(args.database)
        try:
            store.export_csv(args.table, args.output)
        finally:
            store.close()


if __name__ == "__main__":
    main()
