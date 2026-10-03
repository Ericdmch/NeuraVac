import logging

from neuravac_core.models import MissionState

logger = logging.getLogger(__name__)

_EDGES = {
    "BOOTING": {"SELF_TEST"},
    "SELF_TEST": {"IDLE"},
    "IDLE": {"MAPPING", "SCANNING"},
    "MAPPING": {"SCANNING", "IDLE"},
    "SCANNING": {"PLANNING"},
    "PLANNING": {"NAVIGATING", "COMPLETE", "SCANNING"},
    "NAVIGATING": {"CLEANING", "REPLANNING", "SCANNING"},
    "CLEANING": {"VERIFYING"},
    "VERIFYING": {"RETRYING", "PLANNING"},
    "RETRYING": {"CLEANING"},
    "REPLANNING": {"NAVIGATING", "PLANNING"},
    "RETURNING_HOME": {"PAUSED", "IDLE"},
    "PAUSED": {"SCANNING", "IDLE"},
    "FAULT": {"SELF_TEST"},
    "COMPLETE": {"IDLE", "SCANNING"},
}


class MissionMachine:
    def __init__(self) -> None:
        self.state = MissionState.BOOTING
        self.transitions: list[dict[str, str]] = []

    def transition(self, next_state: str | MissionState, reason: str = "") -> None:
        target = MissionState(next_state)
        if target == self.state:
            return
        if target not in ("FAULT", "PAUSED", "RETURNING_HOME") and target not in _EDGES[self.state]:
            raise ValueError(f"illegal mission transition {self.state} → {target}")
        record = {"from": str(self.state), "to": str(target), "reason": reason}
        self.transitions.append(record)
        logger.info("mission_transition", extra={"event": "mission_transition", "data": record})
        self.state = target
