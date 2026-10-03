import json

from tools.audit_secrets import scan_paths
from tools.benchmark_pi import benchmark


def test_secret_audit_detects_assignment_without_leaking_value(tmp_path):
    clean = tmp_path / "clean.py"
    clean.write_text('NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")')
    dirty = tmp_path / "dirty.env"
    dirty.write_text('NEBIUS_API_KEY="' + "secret-value-0123456789" + '"')
    findings = scan_paths([clean, dirty])
    assert len(findings) == 1
    assert findings[0]["file"] == str(dirty)
    assert "secret-value" not in json.dumps(findings)


async def test_benchmark_reports_actual_samples_and_null_hardware():
    result = await benchmark(duration_s=0.12, control_hz=20)
    assert result["control_callback"]["samples"] >= 2
    assert result["control_callback"]["p95_ms"] >= 0
    assert result["perception_fps"] is None
    assert result["camera_fps"] is None
    assert result["cloud_latency_ms"] is None
    assert result["mode"] == "simulation_core"
