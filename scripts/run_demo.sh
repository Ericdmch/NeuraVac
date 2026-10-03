#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec .venv/bin/python -m neuravac_core.cli demo --record artifacts/demo-session.jsonl "$@"
