"""Lightweight source secret audit; prints file/line/rule, never matched values."""

import argparse
import json
import re
import subprocess
from pathlib import Path

RULES = {
    "credential_assignment": re.compile(
        r"""(?i)(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*["']?([A-Za-z0-9_./+\-=]{16,})"""
    ),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "aws_key": re.compile(r"AKIA[0-9A-Z]{16}"),
}


def scan_paths(paths: list[Path]) -> list[dict]:
    findings = []
    for path in paths:
        if not path.is_file() or path.name.endswith((".lock", ".png", ".jpg", ".mp4", ".onnx")):
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for name, pattern in RULES.items():
                match = pattern.search(line)
                if match:
                    if name == "credential_assignment" and match.group(1) in (
                        "NEBIUS_API_KEY",
                        "NEURAVAC_API_TOKEN",
                        "YOUR_API_KEY_HERE",
                    ):
                        continue
                    findings.append({"file": str(path), "line": number, "rule": name})
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths
    if not paths:
        output = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
        )
        paths = [Path(p.decode()) for p in output.split(b"\0") if p]
    findings = scan_paths(paths)
    print(json.dumps({"findings": findings, "files_checked": len(paths)}, indent=2))
    raise SystemExit(bool(findings))


if __name__ == "__main__":
    main()
