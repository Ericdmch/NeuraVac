"""Cloud settings use explicit process environment, never credential files."""

import os
import re
from collections.abc import Mapping
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator

from neuravac_core.models import StrictModel


def https_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("endpoint must be HTTPS without credentials, query or fragment")
    # Access validates the port, too.
    _ = parsed.port
    return value.rstrip("/")


class HTTPConfig(StrictModel):
    api_key: SecretStr = Field(exclude=True, repr=False)
    model: str = Field(min_length=1, max_length=200)
    timeout_s: float = Field(default=8, gt=0, le=120)
    max_retries: int = Field(default=2, ge=0, le=10)
    backoff_s: float = Field(default=0.25, ge=0, le=10)
    max_backoff_s: float = Field(default=2, ge=0, le=30)
    max_tokens: int = Field(default=512, ge=64, le=4096)
    max_response_bytes: int = Field(default=1_048_576, ge=1024, le=10_485_760)

    @field_validator("api_key")
    @classmethod
    def valid_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("API key is required")
        return value

    @field_validator("model")
    @classmethod
    def valid_model(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_./:-]+", value):
            raise ValueError("invalid model identifier")
        return value


class NebiusConfig(HTTPConfig):
    base_url: str = "https://api.tokenfactory.nebius.com/v1"

    _https = field_validator("base_url")(https_url)

    @field_validator("model")
    @classmethod
    def nvidia_nemotron(cls, value: str) -> str:
        if not value.lower().startswith("nvidia/") or "nemotron" not in value.lower():
            raise ValueError("select an account-available NVIDIA Nemotron model")
        return value

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "NebiusConfig":
        settings = os.environ if env is None else env
        values: dict = {}
        for field, name in {
            "api_key": "NEBIUS_API_KEY",
            "model": "NEBIUS_MODEL",
            "base_url": "NEBIUS_BASE_URL",
            "timeout_s": "NEBIUS_TIMEOUT_S",
            "max_retries": "NEBIUS_MAX_RETRIES",
            "backoff_s": "NEBIUS_BACKOFF_S",
            "max_backoff_s": "NEBIUS_MAX_BACKOFF_S",
            "max_tokens": "NEBIUS_MAX_TOKENS",
        }.items():
            if name in settings:
                values[field] = settings[name]
        if not values.get("api_key") or not values.get("model"):
            raise ValueError("NEBIUS_API_KEY and NEBIUS_MODEL are required")
        return cls.model_validate(values)


class PhysicalReasoningConfig(HTTPConfig):
    """Explicit OpenAI-compatible URLs; no physical-AI API is assumed to exist."""

    enabled: bool = False
    api_key: SecretStr = Field(default=SecretStr(""), exclude=True, repr=False)
    model: str = ""
    completion_url: str | None = None
    models_url: str | None = None

    @field_validator("completion_url", "models_url")
    @classmethod
    def optional_https(cls, value: str | None) -> str | None:
        return https_url(value) if value else value

    @model_validator(mode="after")
    def explicit_endpoint(self) -> "PhysicalReasoningConfig":
        if self.enabled:
            if not (
                self.completion_url
                and self.models_url
                and self.model
                and self.api_key.get_secret_value()
            ):
                raise ValueError(
                    "enabled physical reasoning requires both verified API URLs, model and key"
                )
            completion, models = urlsplit(self.completion_url), urlsplit(self.models_url)
            if (completion.hostname, completion.port) != (models.hostname, models.port):
                raise ValueError("discovery and completion URLs must use the same HTTPS origin")
        return self

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "PhysicalReasoningConfig":
        settings = os.environ if env is None else env
        enabled = settings.get("PHYSICAL_REASONING_ENABLED", "0")
        if enabled not in {"0", "1"}:
            raise ValueError("PHYSICAL_REASONING_ENABLED must be 0 or 1")
        if enabled == "0":
            return cls()
        return cls(
            enabled=True,
            completion_url=settings.get("PHYSICAL_REASONING_COMPLETION_URL"),
            models_url=settings.get("PHYSICAL_REASONING_MODELS_URL"),
            model=settings.get("PHYSICAL_REASONING_MODEL", ""),
            api_key=SecretStr(settings.get("PHYSICAL_REASONING_API_KEY", "")),
        )
