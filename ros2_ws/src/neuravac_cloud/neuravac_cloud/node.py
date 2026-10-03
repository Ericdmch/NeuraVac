"""Optional asynchronous advisory worker. Never publishes actuator commands."""

from neuravac_base.contracts import decode
from neuravac_base.util import AsyncWorker, ConfigNode, spin
from std_msgs.msg import String

from neuravac_core.cloud.client import NebiusClient
from neuravac_core.cloud.config import NebiusConfig


class CloudNode(ConfigNode):
    def __init__(self):
        super().__init__("cloud_reasoner")
        self.enabled = self.declare_parameter("enabled", False).value
        self.worker = AsyncWorker()
        self.client = None
        self.pending = None
        self.error = None
        self.results = self.create_publisher(String, "/cloud/result", 10)
        self.telemetry = self.create_publisher(String, "/ai_decisions", 10)
        if self.enabled:
            try:
                self.client = NebiusClient(NebiusConfig.from_env())
            except ValueError:
                self.error = "cloud_configuration_invalid"
        self.create_subscription(String, "/cloud/request", self.request, 10)
        self.create_timer(0.05, self.tick)

    def request(self, msg):
        try:
            data = decode(
                msg.data, "cloud_request", self.seconds(), self.config.safety.camera_timeout_s
            )
            p = data["payload"]
            if set(p) != {"request_id", "world"} or not isinstance(p["request_id"], str):
                raise ValueError("invalid request")
            if not self.client:
                self.publish_json(
                    self.results,
                    "cloud_result",
                    {
                        "request_id": p["request_id"],
                        "decision": None,
                        "error": self.error or "disabled",
                    },
                )
            elif self.pending is None:
                self.pending = (p["request_id"], self.worker.submit(self.client.decide(p["world"])))
        except (ValueError, KeyError):
            pass

    def tick(self):
        if self.pending and self.pending[1].done():
            request, future = self.pending
            self.pending = None
            try:
                decision = future.result().model_dump(mode="json")
                error = None
            except Exception:
                decision = None
                error = "cloud_request_failed"
            self.publish_json(
                self.results,
                "cloud_result",
                {"request_id": request, "decision": decision, "error": error},
            )
            self.publish_json(
                self.telemetry,
                "ai_decision",
                dict(self.client.last_telemetry, request_id=request, decision=decision),
            )

    def destroy_node(self):
        if self.pending:
            self.pending[1].cancel()
        if self.client:
            try:
                self.worker.submit(self.client.aclose()).result(timeout=2)
            except Exception:
                pass
        self.worker.close()
        return super().destroy_node()


def main():
    spin(CloudNode)
