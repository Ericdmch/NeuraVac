"""Deterministic physical feedback loop with nonblocking optional cloud reasoning.

This runtime is explicitly simulation. ROS production adapters use the same pure
world/safety/verification modules and delegate movement to Nav2.
"""

import asyncio
import logging
import math
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from neuravac_core.base.driver import BaseDriver
from neuravac_core.cleaning import evaluate_pass, should_retry
from neuravac_core.config import RobotConfig
from neuravac_core.geometry.kinematics import wrap_angle
from neuravac_core.mission import MissionMachine
from neuravac_core.models import BumperState, CliffState, Decision
from neuravac_core.safety import (
    CommandArbiter,
    SafetyMonitor,
    SafetyStatus,
    SensorSnapshot,
    VelocityCommand,
)
from neuravac_core.storage import MissionStore
from neuravac_core.world import WorldModel
from sim.sim2d.base import SimRobotBase
from sim.sim2d.environment import Environment
from sim.sim2d.navigation import plan_path

logger = logging.getLogger(__name__)


class SimulationRuntime:
    def __init__(
        self,
        config: RobotConfig | None = None,
        environment: Environment | None = None,
        db_path: str | Path = ":memory:",
        cloud: Any = None,
        cloud_fallback: str = "deterministic",
        move_chair: bool = True,
        recorder: Any = None,
    ) -> None:
        self.config = config or RobotConfig(backend="sim")
        self.environment = environment or Environment.demo()
        self.base = SimRobotBase(self.environment, self.config)
        self.driver = BaseDriver(self.base, self.config)
        self.world = WorldModel(self.config)
        self.monitor = SafetyMonitor(self.config.safety)
        self.arbiter = CommandArbiter(self.config.safety)
        self.machine = MissionMachine()
        self.store = MissionStore(db_path)
        self.mission_id = "idle"
        self.sensors = SensorSnapshot(connected=False)
        self.safety_status = SafetyStatus()
        self.path: list[tuple[float, float]] = []
        self.events: list[dict] = []
        self.attempts: list[dict] = []
        self.cloud = cloud
        if cloud_fallback not in ("deterministic", "pause"):
            raise ValueError("invalid cloud fallback")
        self.cloud_fallback = cloud_fallback
        self.cloud_status = {"status": "offline", "model": None, "latency_ms": None}
        self._cloud_task: asyncio.Task[Decision] | None = None
        self._target_id: str | None = None
        self._pass_number = 0
        self._before = 0.0
        self._pass_started = 0.0
        self._observed = -math.inf
        self._recorded_observation_time = -math.inf
        self._initial_score = 0.0
        self._revision = self.environment.revision
        self._faults: set[str] = set()
        self._chair_auto = move_chair
        self._chair_moved = False
        self._navigation_ticks = 0
        self._closed = False
        self.recorder = recorder
        self.self_test: dict = {"status": "NOT_READY", "checks": {}}

    def event(self, event: str, **data: Any) -> None:
        entry = {"event": event, "timestamp": self.base.time, "data": data}
        self.events.append(entry)
        self.events = self.events[-200:]
        logger.info(
            event,
            extra={
                "event": event,
                "data": {
                    "mission": self.mission_id,
                    "state": self.machine.state,
                    "robot_pose": self.base.pose.model_dump(),
                    **data,
                },
            },
        )
        if self.recorder:
            self.recorder.write(event, self.base.time, data)

    async def initialize(self) -> None:
        self.machine.transition("SELF_TEST")
        await self.driver.connect()
        self.refresh_sensors()
        self.observe()
        self._initial_score = sum(r.debris_score for r in self.world.regions.values())
        self.safety_status = self.monitor.evaluate(self.sensors, self.base.time)
        cloud_ready = False
        if self.cloud and hasattr(self.cloud, "verify_model"):
            try:
                await self.cloud.verify_model()
                cloud_ready = True
                self.cloud_status = {
                    "status": "online",
                    "model": self.cloud.config.model,
                    "latency_ms": None,
                }
            except Exception as error:
                self.cloud_status = {
                    "status": "degraded",
                    "model": self.cloud.config.model,
                    "latency_ms": None,
                    "error": type(error).__name__,
                }
                self.event("cloud_self_test_degraded", reason=type(error).__name__)
        checks = {
            "base": self.base.connected,
            "lidar": True,
            "camera": True,
            "battery": self.base.battery.percent > self.config.safety.return_battery_percent,
            "map": True,
            "model": "simulated_camera",
            "safety": self.safety_status.safe,
            "cloud": cloud_ready,
        }
        self.self_test = {
            "status": "READY" if cloud_ready else "READY_WITH_DEGRADED_CLOUD",
            "checks": checks,
        }
        if not self.safety_status.safe or not checks["battery"]:
            self.self_test["status"] = "NOT_READY"
            self.machine.transition("FAULT")
            return
        self.machine.transition("IDLE")
        self.event("self_test", **self.self_test)

    def start(self) -> None:
        if (
            self.machine.state not in ("IDLE", "COMPLETE")
            or not self.safety_status.safe
            or self.self_test["status"] == "NOT_READY"
        ):
            raise ValueError("mission start requires IDLE/COMPLETE and healthy safety sensors")
        self.mission_id = uuid.uuid4().hex
        self._initial_score = sum(r.debris_score for r in self.world.regions.values())
        self.attempts = []
        self.arbiter.clear()
        self.machine.transition("SCANNING")
        self.store.record(
            "missions",
            self.mission_id,
            self.base.time,
            {"event": "started", "state": self.machine.state},
        )
        self.event("mission_started")

    def refresh_sensors(self) -> None:
        now = self.base.time
        self.sensors.connected = self.base.connected and "serial" not in self._faults
        for name in ("base", "scan", "camera", "heartbeat"):
            key = "lidar" if name == "scan" else name
            if key not in self._faults and not (name == "base" and "serial" in self._faults):
                setattr(self.sensors, name + "_timestamp", now)
        self.sensors.battery = self.base.battery.model_copy()
        self.sensors.bumper = self.base.bumper.model_copy()
        self.sensors.cliff = self.base.cliff.model_copy()

    def observe(self) -> None:
        if "camera" in self._faults:
            raise ValueError("camera unavailable")
        self.world.observe(self.environment.observe(self.base.time), self.base.time)
        self._observed = self.base.time
        if self.recorder and self.base.time != self._recorded_observation_time:
            self._recorded_observation_time = self.base.time
            self.recorder.write(
                "detections",
                self.base.time,
                {
                    "detections": [
                        d.model_dump(mode="json") for d in self.environment.observe(self.base.time)
                    ]
                },
            )

    def inject_fault(self, fault: str) -> None:
        self._faults.add(fault)
        if fault == "cliff":
            self.base.cliff = CliffState(front_left=True)
        if fault == "bumper":
            self.base.bumper = BumperState(left=True)
        if fault == "battery":
            self.base.battery.percent = 3
        if fault in ("camera", "lidar", "heartbeat", "serial"):
            attribute = {
                "camera": "camera",
                "lidar": "scan",
                "heartbeat": "heartbeat",
                "serial": "base",
            }[fault]
            setattr(self.sensors, attribute + "_timestamp", None)

    def clear_faults(self) -> None:
        self._faults.clear()
        self.base.bumper = BumperState()
        self.base.cliff = CliffState()
        self.refresh_sensors()

    async def pause(self) -> None:
        if self.machine.state not in ("FAULT", "BOOTING", "SELF_TEST"):
            self.machine.transition("PAUSED", "user pause")
        self.arbiter.clear()
        self._cancel_cloud()
        await self.driver.stop()
        self.event("mission_paused")

    def resume(self) -> None:
        if (
            self.machine.state != "PAUSED"
            or not self.monitor.evaluate(self.sensors, self.base.time).safe
        ):
            raise ValueError("resume requires PAUSED and healthy sensors")
        self._target_id = None
        self.arbiter.clear()
        self.machine.transition("SCANNING")

    async def emergency_stop(self) -> None:
        self.monitor.emergency_stop()
        self.safety_status = self.monitor.evaluate(self.sensors, self.base.time)
        self.machine.transition("FAULT", "emergency_stop")
        self._cancel_cloud()
        self.arbiter.clear()
        await self.driver.stop()
        self.store.record(
            "safety_events", self.mission_id, self.base.time, {"reasons": ["emergency_stop"]}
        )
        self.event("safety_fault", reasons=["emergency_stop"])

    def reset(self) -> None:
        if self.machine.state != "FAULT" or not self.monitor.reset(self.sensors, self.base.time):
            raise ValueError("reset requires FAULT and all sensors healthy")
        if self.base.battery.percent <= self.config.safety.return_battery_percent:
            raise ValueError("reset requires sufficient battery for self-test")
        self.arbiter.clear()
        self._target_id = None
        self.machine.transition("SELF_TEST")
        self.machine.transition("IDLE")
        self.self_test["checks"]["battery"] = True
        self.self_test["status"] = "READY_WITH_DEGRADED_CLOUD"
        self.event("safety_reset")

    def move_chair(self) -> None:
        if self.path:
            x, y = self.path[len(self.path) // 2]
        else:
            x, y = 3.8, 2.8
        # Do not teleport a chair onto the robot footprint.
        if math.dist((self.base.pose.x, self.base.pose.y), (x, y)) < 0.7:
            x, y = 3.8, 2.8
        self.environment.move_obstacle("chair", x, y)
        self._chair_moved = True

    def _route(self, target: tuple[float, float]) -> list[tuple[float, float]]:
        return plan_path(
            self.environment,
            (self.base.pose.x, self.base.pose.y),
            target,
            self.config.robot_radius_m + self.config.semantic.hazard_expansion_m + 0.15,
        )

    def _select_target(self, target_id: str) -> None:
        region = self.world.regions[target_id]
        self.path = self._route(region.position)
        if not self.path:
            region.reachable = False
            raise ValueError("target route blocked")
        self._target_id = target_id
        self._pass_number = 0
        self._navigation_ticks = 0
        self.machine.transition("NAVIGATING")
        self.event("target_selected", region_id=target_id, path=self.path)

    def _cancel_cloud(self) -> None:
        if self._cloud_task:
            self._cloud_task.cancel()
            self._cloud_task = None

    async def _planning(self) -> None:
        target = self.world.choose(
            self.base.pose,
            lambda p: bool(self._route(p)),
            battery_percent=self.base.battery.percent,
        )
        unresolved = [
            r
            for r in self.world.regions.values()
            if not r.cleaned and r.debris_score > self.config.cleaning.success_threshold
        ]
        if target is None:
            if unresolved:
                self.machine.transition("PAUSED", "unreachable debris; human inspection needed")
                self.event("human_help_required", reason="unreachable debris")
            else:
                self.machine.transition("COMPLETE")
                self.store.record(
                    "missions",
                    self.mission_id,
                    self.base.time,
                    {"event": "completed", "metrics": self.metrics()},
                )
                self.event("mission_complete", metrics=self.metrics())
            return
        if self.cloud is not None:
            if self._cloud_task is None:
                self.cloud_status = {
                    "status": "requesting",
                    "model": self.cloud.config.model,
                    "latency_ms": None,
                }
                self._cloud_task = asyncio.create_task(
                    self.cloud.decide(self.world.reasoning_state(self.base.battery.percent))
                )
                self.event("cloud_request_started", model=self.cloud.config.model)
                return
            if not self._cloud_task.done():
                return
            task, self._cloud_task = self._cloud_task, None
            try:
                decision = task.result()
                # Re-observe before accepting a response against changed physical state.
                self.observe()
                self.world.choose(
                    self.base.pose,
                    lambda p: bool(self._route(p)),
                    battery_percent=self.base.battery.percent,
                )
                self.world.validate_decision(decision, self.base.time)
                self.cloud_status = dict(self.cloud.last_telemetry)
                self.store.record(
                    "ai_decisions",
                    self.mission_id,
                    self.base.time,
                    {"decision": decision.model_dump(), "telemetry": self.cloud_status},
                )
                self.event("ai_decision", **decision.model_dump())
                if decision.action == "clean_region":
                    self._select_target(decision.target_id or "")
                elif decision.action == "return_home":
                    self._return_home()
                elif decision.action == "rescan_area":
                    self.machine.transition("SCANNING")
                elif decision.action == "finish":
                    self.machine.transition("COMPLETE")
                else:
                    self.machine.transition("PAUSED", decision.reason)
                    self.event("human_help_required", reason=decision.reason)
                return
            except Exception as error:
                self.cloud_status = {
                    **dict(getattr(self.cloud, "last_telemetry", {})),
                    "status": "degraded",
                    "error": type(error).__name__,
                }
                self.event(
                    "cloud_fallback", reason=type(error).__name__, policy=self.cloud_fallback
                )
                if self.cloud_fallback == "pause":
                    self.machine.transition("PAUSED", "cloud unavailable")
                    return
                target = self.world.choose(
                    self.base.pose,
                    lambda p: bool(self._route(p)),
                    battery_percent=self.base.battery.percent,
                )
                if target is None:
                    self.machine.transition("PAUSED", "target changed during reasoning")
                    return
        self.event(
            "local_decision",
            action="clean_region",
            target_id=target.id,
            reason="Reachable high-confidence debris; numerical ranking",
        )
        self._select_target(target.id)

    def _return_home(self) -> None:
        self.path = self._route((self.environment.start.x, self.environment.start.y))
        self._cancel_cloud()
        if not self.path:
            self.machine.transition("PAUSED", "home route blocked")
            return
        self.machine.transition("RETURNING_HOME")
        self.event("returning_home", reason="battery reserve or mission decision")

    def _navigate(self) -> tuple[float, float]:
        while self.path and math.dist((self.base.pose.x, self.base.pose.y), self.path[0]) < 0.06:
            self.path.pop(0)
        if not self.path:
            if self.machine.state == "RETURNING_HOME":
                self.machine.transition("PAUSED", "home reached; recharge required")
                self.event("home_reached")
            else:
                self._begin_pass()
            return 0, 0
        x, y = self.path[0]
        angle = wrap_angle(
            math.atan2(y - self.base.pose.y, x - self.base.pose.x) - self.base.pose.yaw
        )
        angular = max(
            -self.config.safety.max_angular_rps, min(self.config.safety.max_angular_rps, 3 * angle)
        )
        linear = min(
            self.config.safety.max_linear_mps,
            math.dist((x, y), (self.base.pose.x, self.base.pose.y)) * 3,
        )
        if abs(angle) > 0.25:
            linear = 0
        return linear, angular

    def _begin_pass(self) -> None:
        self.observe()
        self._before = self.world.score(self._target_id or "", self.base.time)
        self._pass_number += 1
        self._pass_started = self.base.time
        self.machine.transition("CLEANING")
        self.event(
            "cleaning_before",
            region_id=self._target_id,
            score=self._before,
            pass_number=self._pass_number,
        )

    def _verify(self) -> None:
        self.observe()
        target_id = self._target_id or ""
        after = self.world.score(target_id, self.base.time)
        attempt = evaluate_pass(
            target_id,
            self._before,
            after,
            self._pass_number,
            self.base.time - self._pass_started,
            self.config.cleaning,
        )
        payload = attempt.to_dict()
        self.attempts.append(payload)
        self.store.record("cleaning_attempts", self.mission_id, self.base.time, payload)
        self.event("cleaning_verified", **payload)
        if attempt.success:
            self.world.regions[target_id].cleaned = True
            self.store.record(
                "cleaning_regions",
                self.mission_id,
                self.base.time,
                self.world.regions[target_id].model_dump(),
            )
            self.machine.transition("PLANNING")
        elif should_retry(attempt, self.config.cleaning):
            self.world.regions[target_id].failures += 1
            self.machine.transition("RETRYING")
        else:
            self.machine.transition("PAUSED", "debris remains after retry limit or no improvement")
            self.event("human_help_required", reason="cleaning verification failed")

    async def tick(self, dt: float | None = None) -> None:
        dt = dt if dt is not None else 1 / self.config.control_hz
        self.refresh_sensors()
        self.safety_status = self.monitor.evaluate(self.sensors, self.base.time)
        if not self.safety_status.safe:
            self.arbiter.clear()
            self._cancel_cloud()
            await self.driver.stop()
            if self.machine.state != "FAULT":
                self.machine.transition("FAULT", ",".join(self.safety_status.reasons))
                self.store.record(
                    "safety_events",
                    self.mission_id,
                    self.base.time,
                    {"reasons": self.safety_status.reasons},
                )
                self.event("safety_fault", reasons=self.safety_status.reasons)
            self.base.step(dt)
            return
        linear = angular = 0.0
        vacuum = False
        try:
            if self.machine.state not in ("IDLE", "PAUSED", "FAULT", "COMPLETE"):
                if self.base.time - self._observed >= 0.2:
                    self.observe()
                if (
                    self.base.battery.percent <= self.config.safety.return_battery_percent
                    and self.machine.state != "RETURNING_HOME"
                ):
                    self._return_home()
                if self.machine.state == "SCANNING":
                    self.observe()
                    self.machine.transition("PLANNING")
                elif self.machine.state == "PLANNING":
                    await self._planning()
                elif self.machine.state in ("NAVIGATING", "RETURNING_HOME"):
                    self._navigation_ticks += 1
                    if (
                        self._chair_auto
                        and not self._chair_moved
                        and self.machine.state == "NAVIGATING"
                        and any(r.cleaned for r in self.world.regions.values())
                        and self._navigation_ticks == 15
                    ):
                        self.move_chair()
                    if self.environment.revision != self._revision:
                        self._revision = self.environment.revision
                        self.event("environment_changed", revision=self._revision)
                        if self.machine.state == "NAVIGATING":
                            self.machine.transition("REPLANNING")
                            self.observe()
                            self.path = self._route(
                                self.world.regions[self._target_id or ""].position
                            )
                            self.event("route_replanned", path=self.path)
                            if not self.path:
                                self.machine.transition("PAUSED", "route blocked")
                            else:
                                self.machine.transition("NAVIGATING")
                    if self.machine.state in ("NAVIGATING", "RETURNING_HOME"):
                        linear, angular = self._navigate()
                elif self.machine.state == "CLEANING":
                    if not self.world.safe_point((self.base.pose.x, self.base.pose.y)):
                        self.machine.transition("PAUSED", "new hazard near cleaning pass")
                    elif (
                        self.base.time - self._pass_started >= self.config.cleaning.pass_duration_s
                    ):
                        self.machine.transition("VERIFYING")
                    else:
                        vacuum = True
                elif self.machine.state == "VERIFYING":
                    self._verify()
                elif self.machine.state == "RETRYING":
                    self._begin_pass()
        except (ValueError, KeyError, ConnectionError) as error:
            self.machine.transition("FAULT", type(error).__name__)
            self.event("mission_fault", reason=str(error))
            self.arbiter.clear()
            linear = angular = 0
            vacuum = False
        command = VelocityCommand(
            source="navigation",
            linear_mps=linear,
            angular_rps=angular,
            timestamp=self.base.time,
            vacuum=vacuum,
            main_brush=vacuum,
            side_brush=vacuum,
        )
        self.arbiter.submit(command)
        safe = self.arbiter.select(self.base.time, self.safety_status)
        await self.driver.apply(safe, self.base.time)
        self.base.step(dt)
        if self.recorder:
            self.recorder.write(
                "tick",
                self.base.time,
                {
                    "command": safe.model_dump(),
                    "sensors": asdict(self.sensors),
                    "state": self.snapshot(),
                },
            )
        await asyncio.sleep(0)

    async def run_until_terminal(self, max_steps: int = 15000, realtime: bool = False) -> None:
        for _ in range(max_steps):
            await self.tick()
            if self.machine.state in ("COMPLETE", "FAULT", "PAUSED"):
                return
            if realtime:
                await asyncio.sleep(1 / self.config.control_hz)
        await self.pause()
        raise TimeoutError("mission exceeded deterministic step budget")

    def metrics(self) -> dict:
        current = sum(r.debris_score for r in self.world.regions.values())
        return {
            "initial_debris_score": self._initial_score,
            "current_debris_score": current,
            "cleanliness_percent": max(0, min(100, 100 * (1 - current / self._initial_score)))
            if self._initial_score
            else 100,
            "coverage_percent": 100
            * sum(r.cleaned for r in self.world.regions.values())
            / max(1, len(self.world.regions)),
            "regions_remaining": sum(
                not r.cleaned and r.debris_score > self.config.cleaning.success_threshold
                for r in self.world.regions.values()
            ),
            "successful_passes": sum(a["success"] for a in self.attempts),
            "retried_passes": sum(not a["success"] for a in self.attempts),
        }

    def snapshot(self) -> dict:
        return {
            "schema_version": 1,
            "mode": "simulation",
            "mission_id": self.mission_id,
            "state": str(self.machine.state),
            "battery_percent": self.base.battery.percent,
            "connected": self.base.connected,
            "safety": self.safety_status.model_dump(),
            "cloud": self.cloud_status,
            "pose": self.base.pose.model_dump(),
            "world": {
                **self.world.to_dict(),
                "width": self.environment.width,
                "height": self.environment.height,
                "obstacles": [asdict(o) for o in self.environment.obstacles],
            },
            "path": self.path,
            "metrics": self.metrics(),
            "attempts": self.attempts[-100:],
            "events": self.events[-30:],
            "self_test": self.self_test,
            "timestamp": self.base.time,
        }

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._cancel_cloud()
        await self.driver.close()
        if self.cloud:
            await self.cloud.aclose()
        if self.recorder:
            self.recorder.close()
        self.store.close()
