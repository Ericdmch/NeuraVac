"""Structured event logs without credentials or private model reasoning."""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

_SECRET = re.compile(
    r"api.?key|token|authorization|password|secret|credential|chain.of.thought|reasoning_content",
    re.I,
)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: "[REDACTED]"
            if _SECRET.search(str(k))
            and not (
                k in {"prompt_tokens", "completion_tokens", "total_tokens"}
                and isinstance(v, int)
                and not isinstance(v, bool)
                and v >= 0
            )
            else redact(v)
            for k, v in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"(?i)Bearer\s+\S+", "Bearer [REDACTED]", value)
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            redact(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "node": record.name,
                    "event": getattr(record, "event", record.getMessage()),
                    "level": record.levelname,
                    "data": getattr(record, "data", {}),
                }
            ),
            default=str,
            allow_nan=False,
        )


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
