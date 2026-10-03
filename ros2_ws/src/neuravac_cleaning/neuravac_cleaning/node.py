"""Stationary cleaning passes require a fresh BEFORE and AFTER world observation."""

from neuravac_base.contracts import decode, restore_world
from neuravac_base.util import ConfigNode, spin
from std_msgs.msg import String

from neuravac_core.cleaning import evaluate_pass, should_retry


class CleaningNode(ConfigNode):
    def __init__(self):
        super().__init__("cleaning_verifier")
        self.world = None
        self.world_stamp = 0.0
        self.observed_at = 0.0
        self.safe = False
        self.active = None
        self.commands = self.create_publisher(String, "/mission/cleaning_cmd", 10)
        self.results = self.create_publisher(String, "/cleaning/result", 10)
        self.create_subscription(String, "/world_model", self.observation, 10)
        self.create_subscription(String, "/cleaning/request", self.request, 10)
        self.create_subscription(String, "/cleaning/cancel", self.cancel, 10)
        self.create_timer(0.05, self.tick)

    def observation(self, msg):
        try:
            data = decode(
                msg.data, "world_model", self.seconds(), self.config.safety.camera_timeout_s
            )
            p = data["payload"]
            self.world = restore_world(p["world"], self.config)
            self.world_stamp = data["stamp"]
            self.observed_at = p["observed_at"]
            self.safe = p["available"] is True and p["safety"].get("safe") is True
        except (ValueError, KeyError, TypeError):
            self.safe = False

    def request(self, msg):
        try:
            p = decode(msg.data, "cleaning_request", self.seconds(), self.config.safety.watchdog_s)[
                "payload"
            ]
            if (
                set(p) != {"request_id", "region_id", "pass_number"}
                or not isinstance(p["request_id"], str)
                or type(p["pass_number"]) is not int
                or not 1 <= p["pass_number"] <= self.config.cleaning.max_retries + 1
            ):
                raise ValueError("invalid request")
            if self.active:
                self.finish(False, "busy")
                return
            self.active = dict(
                p,
                phase="BEFORE",
                started=self.seconds(),
                before=None,
                deadline=self.seconds() + self.config.safety.camera_timeout_s + 2,
            )
        except (ValueError, KeyError):
            self.active = None
            self.command(False)

    def cancel(self, msg):
        try:
            decode(msg.data, "cleaning_cancel", self.seconds(), self.config.safety.watchdog_s)
            if self.active:
                self.finish(False, "cancelled")
            self.command(False)
        except ValueError:
            pass

    def command(self, enabled):
        self.publish_json(self.commands, "cleaning_command", {"enabled": enabled})

    def finish(self, success, reason, attempt=None, retry=False):
        active = self.active
        self.active = None
        self.command(False)
        if active:
            self.publish_json(
                self.results,
                "cleaning_result",
                {
                    "request_id": active["request_id"],
                    "region_id": active["region_id"],
                    "success": success,
                    "reason": reason,
                    "retry": retry,
                    "attempt": attempt.to_dict() if attempt else None,
                },
            )

    def tick(self):
        now = self.seconds()
        active = self.active
        if not active:
            self.command(False)
            return
        if (
            not self.safe
            or not self.world
            or not 0 <= now - self.world_stamp <= self.config.safety.watchdog_s
        ):
            self.finish(False, "world_or_safety_unavailable")
            return
        region = self.world.regions.get(active["region_id"])
        if region is None or not self.world.safe_point(region.position):
            self.finish(False, "target_unsafe_or_missing")
            return
        if now > active["deadline"]:
            self.finish(False, "fresh_observation_timeout")
            return
        try:
            if active["phase"] == "BEFORE":
                self.command(False)
                if self.observed_at <= active["started"]:
                    return
                active["before"] = self.world.score(active["region_id"], self.observed_at)
                active.update(
                    phase="RUNNING",
                    end=now + self.config.cleaning.pass_duration_s,
                    deadline=now
                    + self.config.cleaning.pass_duration_s
                    + self.config.safety.camera_timeout_s
                    + 2,
                )
            if active["phase"] == "RUNNING":
                if now < active["end"]:
                    self.command(True)
                    return
                self.command(False)
                active["phase"] = "AFTER"
            if active["phase"] == "AFTER":
                self.command(False)
                if self.observed_at <= active["end"]:
                    return
                after = self.world.score(active["region_id"], self.observed_at)
                attempt = evaluate_pass(
                    active["region_id"],
                    active["before"],
                    after,
                    active["pass_number"],
                    self.config.cleaning.pass_duration_s,
                    self.config.cleaning,
                )
                self.finish(
                    attempt.success,
                    "verified" if attempt.success else "debris_remains",
                    attempt,
                    should_retry(attempt, self.config.cleaning),
                )
        except ValueError:
            self.finish(False, "observation_incomplete")


def main():
    spin(CleaningNode)
