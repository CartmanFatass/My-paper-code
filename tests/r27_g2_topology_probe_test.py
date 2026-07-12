from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "r27_g2_topology_probe.py"
RUNNER = ROOT / "scripts" / "run_r27_g2_topology_probe_cloud.sh"


def _load_probe_module():
    spec = importlib.util.spec_from_file_location("r27_g2_topology_probe", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parser_defaults_to_bounded_parallel_cuda_probe(tmp_path: Path):
    module = _load_probe_module()
    args = module.parse_args(["--output", str(tmp_path / "result.json")])

    assert args.workers == 8
    assert args.device == "cuda"
    assert args.residency_seconds == 300.0
    assert args.startup_timeout_seconds == 480.0
    assert args.max_wall_seconds == 900.0
    assert args.min_free_gpu_mib == 4096.0
    assert args.fixture is False


@pytest.mark.parametrize("workers", [0, 1, 65])
def test_probe_rejects_serial_or_out_of_range_workers(
    tmp_path: Path, workers: int
):
    module = _load_probe_module()
    args = module.parse_args(
        [
            "--output",
            str(tmp_path / "result.json"),
            "--workers",
            str(workers),
            "--fixture",
        ]
    )
    with pytest.raises(ValueError, match="workers must be in 2..64"):
        module._validate_args(args)


def _run_fixture(tmp_path: Path, *extra: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    output = tmp_path / "topology_probe.json"
    command = [
        sys.executable,
        str(PROBE),
        "--output",
        str(output),
        "--workers",
        "2",
        "--fixture",
        "--residency-seconds",
        "0.05",
        "--startup-timeout-seconds",
        "5",
        "--shutdown-timeout-seconds",
        "2",
        "--max-wall-seconds",
        "10",
        *extra,
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert output.is_file(), completed.stderr
    return completed, json.loads(output.read_text(encoding="utf-8"))


def test_fixture_proves_barrier_residency_without_scientific_evidence(tmp_path: Path):
    completed, report = _run_fixture(tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert report["status"] == "FIXTURE_PASS"
    assert report["operational_gate"] == "PASS"
    assert report["classification"] == "NOT_APPLICABLE"
    assert report["scientific_evidence"] is False
    assert report["failure_class"] == "NONE"
    assert report["resource_failure"] is False
    assert report["workers_requested"] == 2
    assert report["workers_ready"] == 2
    assert report["workers_resident"] == 2
    assert report["workers_passed"] == 2
    assert len({worker["pid"] for worker in report["workers"]}) == 2
    assert all(worker["activity_cycles"] >= 1 for worker in report["workers"])


def test_fixture_worker_failure_is_fail_closed(tmp_path: Path):
    completed, report = _run_fixture(
        tmp_path, "--fixture-fail-worker", "1"
    )

    assert completed.returncode == 1
    assert report["status"] == "FIXTURE_FAIL"
    assert report["operational_gate"] == "FAIL"
    assert report["scientific_evidence"] is False
    assert report["failure_class"] == "EXECUTION"
    assert report["resource_failure"] is False
    assert report["workers_passed"] < report["workers_requested"]
    assert report["failures"]


def test_fixture_resource_failure_is_explicitly_machine_readable(tmp_path: Path):
    completed, report = _run_fixture(
        tmp_path, "--fixture-resource-fail-worker", "1"
    )

    assert completed.returncode == 1
    assert report["status"] == "FIXTURE_FAIL"
    assert report["operational_gate"] == "FAIL"
    assert report["failure_class"] == "RESOURCE_CAPACITY"
    assert report["resource_failure"] is True
    assert report["workers_passed"] < report["workers_requested"]


def test_cloud_runner_exposes_fail_closed_status_contract():
    text = RUNNER.read_text(encoding="utf-8")

    assert 'PROBE_WORKERS="${PROBE_WORKERS:-8}"' in text
    assert 'RUN_ROOT="${RUN_ROOT:-logs/r27_g2_topology_probe_' in text
    assert "standalone_process_core_final.pt" in text
    assert '"state=succeeded"' in text
    assert '"probe_status=PASS"' in text
    assert '"failure_class=NONE"' in text
    assert '"failure_class=$failure_class"' in text
    assert '"workers_requested=$PROBE_WORKERS"' in text
    assert '"workers_passed=$PROBE_WORKERS"' in text
    assert '"scientific_evidence=false"' in text
    assert "CPU fallback is forbidden" in text
    assert "PROBE_WORKERS < 2" in text


def test_production_probe_uses_real_agent_env_forward_and_process_barrier():
    text = PROBE.read_text(encoding="utf-8")

    assert 'context = mp.get_context("spawn")' in text
    assert "barrier = context.Barrier(int(args.workers))" in text
    assert "_configure_agent(source_args)" in text
    assert "agent.maybe_assign_skills(" in text
    assert "agent.act_low(" in text
    assert 'env.step(actions)' in text
    assert "agent.r27_g2_audit_step(" in text
    assert "R27G2ResetArtifact.allocate(" in text
