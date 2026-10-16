"""Read values from the repository's local secrets.env file."""

from pathlib import Path


DEFAULT_SECRETS_PATH = Path(__file__).resolve().parents[1] / "secrets.env"


def get_secret(key: str, env_path: str | Path = DEFAULT_SECRETS_PATH) -> str:
    """Return a secret from a dotenv-style file by key.

    ``env_path`` may be supplied when the secrets file lives elsewhere.
    Values may be unquoted or wrapped in single or double quotes. Missing
    files and keys raise explicit errors instead of returning an empty value.
    """
    if not key or key.strip() != key or "=" in key:
        raise ValueError("key must be a non-empty environment variable name")

    path = Path(env_path)
    values: dict[str, str] = {}

    with path.open(encoding="utf-8") as secrets_file:
        for line_number, raw_line in enumerate(secrets_file, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            if "=" not in line:
                raise ValueError(f"Invalid entry in {path} at line {line_number}")

            name, value = (part.strip() for part in line.split("=", 1))
            if not name:
                raise ValueError(f"Invalid entry in {path} at line {line_number}")
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[name] = value

    try:
        return values[key]
    except KeyError as error:
        raise KeyError(f"Secret key {key!r} was not found in {path}") from error
