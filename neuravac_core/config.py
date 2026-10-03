"""Typed YAML; reject unknown keys rather than silently accepting misspellings."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, model_validator

from neuravac_core.models import StrictModel


class SafetyConfig(StrictModel):
    watchdog_s: float = Field(default=0.5, gt=0, le=2)
    sensor_timeout_s: float = Field(default=0.5, gt=0)
    camera_timeout_s: float = Field(default=2, gt=0)
    critical_battery_percent: float = Field(default=8, ge=0, le=100)
    return_battery_percent: float = Field(default=20, ge=0, le=100)
    max_current_a: float = Field(default=5, gt=0)
    require_camera: bool = True
    max_linear_mps: float = Field(default=0.25, gt=0, le=0.5)
    max_angular_rps: float = Field(default=1, gt=0, le=3)

    @model_validator(mode="after")
    def battery_order(self) -> "SafetyConfig":
        if self.return_battery_percent <= self.critical_battery_percent:
            raise ValueError("return battery must exceed critical battery")
        return self


class CleaningConfig(StrictModel):
    max_retries: int = Field(default=2, ge=0, le=10)
    minimum_improvement: float = Field(default=0.05, ge=0)
    success_threshold: float = Field(default=0.08, ge=0)
    vacuum_radius_m: float = Field(default=0.22, gt=0)
    pass_duration_s: float = Field(default=1, gt=0)
    cluster_radius_m: float = Field(default=0.4, gt=0)


class SemanticConfig(StrictModel):
    association_radius_m: float = Field(default=0.3, gt=0)
    stale_after_s: float = Field(default=30, gt=0)
    min_confidence: float = Field(default=0.7, ge=0, le=1)
    hazard_expansion_m: float = Field(default=0.15, ge=0)
    unknown_cost: int = Field(default=100, ge=1, le=100)


class PlanningConfig(StrictModel):
    amount_weight: float = Field(default=1, ge=0)
    confidence_weight: float = Field(default=1, ge=0)
    distance_weight: float = Field(default=1, ge=0)
    failure_weight: float = Field(default=1, ge=0)
    battery_cost_weight: float = Field(default=0.1, ge=0)


class RobotConfig(StrictModel):
    backend: Literal["mock", "sim", "roomba_oi", "mcu_bridge"] = "mock"
    serial_port: str = "/dev/ttyUSB0"
    baud_rate: int = Field(default=115200, gt=0)
    wheel_base_m: float = Field(default=0.235, gt=0)
    wheel_radius_m: float = Field(default=0.036, gt=0)
    encoder_ticks_per_rev: float = Field(default=508.8, gt=0)
    encoder_supported: bool = True
    robot_radius_m: float = Field(default=0.17, gt=0)
    control_hz: float = Field(default=20, ge=10, le=100)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    cleaning: CleaningConfig = Field(default_factory=CleaningConfig)
    semantic: SemanticConfig = Field(default_factory=SemanticConfig)
    planning: PlanningConfig = Field(default_factory=PlanningConfig)


def load_config(path: str | Path) -> RobotConfig:
    with Path(path).open() as stream:
        payload = yaml.safe_load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return RobotConfig.model_validate(payload)
