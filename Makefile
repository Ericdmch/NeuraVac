PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python
FRONTEND := dashboard/frontend
SESSION ?= artifacts/demo-session.jsonl
.PHONY: install lint typecheck test test-unit test-integration test-scenarios test-hardware test-cloud frontend frontend-lint frontend-test frontend-build sim dashboard replay benchmark demo record audit check clean
install:
	test -x $(PY) || $(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -e '.[dev]'
	cd $(FRONTEND) && npm ci
lint:
	$(VENV)/bin/ruff check neuravac_core sim dashboard/backend datasets ml tools tests ros2_ws
	$(VENV)/bin/ruff format --check neuravac_core sim dashboard/backend datasets ml tools tests ros2_ws

typecheck:
	$(VENV)/bin/mypy

test:
	$(PY) -m pytest

test-unit:
	$(PY) -m pytest tests/unit

test-integration:
	$(PY) -m pytest tests/integration tests/replay

test-scenarios:
	$(PY) -m pytest tests/scenarios

test-hardware:
	$(PY) -m pytest -m hardware tests/hardware

test-cloud:
	$(PY) -m pytest -m cloud tests/cloud

frontend: frontend-lint frontend-test frontend-build
frontend-lint:
	cd $(FRONTEND) && npm run lint
frontend-test:
	cd $(FRONTEND) && npm test
frontend-build:
	cd $(FRONTEND) && npm run build
sim: dashboard
dashboard: frontend-build
	$(PY) -m neuravac_core.cli dashboard
replay:
	$(PY) -m neuravac_core.cli replay '$(SESSION)'
benchmark:
	$(PY) -m tools.benchmark_pi
demo:
	$(PY) -m neuravac_core.cli demo --record artifacts/demo-session.jsonl
record: demo
audit:
	$(PY) -m tools.audit_secrets
check: lint typecheck test frontend audit
clean:
	$(PY) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', '.pytest_cache', '.ruff_cache', '.mypy_cache']]"
