"""Write the independent result-blind E2B technical/resource receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_preactivity import run_preactivity_acceptance


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pytest-basetemp", type=Path, required=True)
    arguments = parser.parse_args(); root = arguments.repository_root.resolve()
    command = [
        "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe", "-m", "pytest", "-q",
        f"--basetemp={arguments.pytest_basetemp.resolve()}",
        str(root / "tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_r06_conformance.py"),
        str(root / "tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_r06_e2b_integration.py"),
    ]
    test_started = time.perf_counter()
    test = subprocess.run(command, cwd=root, capture_output=True, text=True)
    if test.returncode:
        raise RuntimeError("independent TEST acceptance failed:\n" + test.stdout + test.stderr)
    test_wall = time.perf_counter() - test_started
    preactivity = run_preactivity_acceptance(root, widths=(32,))
    cli_root = root / "runtime/test_only/dish_rbhr_r06_e2b_cli_run"
    frontier = json.loads((cli_root / "sealed_frontier.json").read_text(encoding="ascii"))
    result = json.loads((cli_root / "complete_result.json").read_text(encoding="ascii"))
    if frontier["stage"] != "COMPLETE" or frontier["completed_units"] != 256_513 or frontier["slice_generation"] != 1:
        raise RuntimeError("exact CLI successor-slice frontier differs")
    if result.get("complete") is not True or result.get("test_only") is not True or result.get("question_relevant_output") is not False:
        raise RuntimeError("exact CLI result firewall differs")
    projection = preactivity["component_projection"]; storage = preactivity["storage_measurement"]
    cpu = float(projection["cpu_core_hours"]); wall = cpu / 8.0
    aggregate_rss = 8.0 * max(preactivity["process_rss_before_bytes"], preactivity["process_rss_after_bytes"]) / 1024**3
    resources = {
        "cpu_core_hours": cpu, "wall_hours_at_eight_workers": wall,
        "aggregate_rss_gib_conservative_eight_processes": aggregate_rss,
        "scratch_gib": storage["measured_formula_scratch_gib"],
        "durable_gib": storage["measured_formula_durable_gib"],
        "total_io_gib": storage["measured_formula_total_io_gib"],
        "ordinary_gates": {"cpu": cpu <= 320.0, "wall": wall <= 65.0},
        "hard_gates": {"cpu": cpu <= 560.0, "wall": wall <= 110.0, "rss": aggregate_rss <= 40.0,
                       "scratch": storage["measured_formula_scratch_gib"] <= 120.0,
                       "durable": storage["measured_formula_durable_gib"] <= 16.0,
                       "io": storage["measured_formula_total_io_gib"] <= 400.0},
        "measurement_basis": projection["formula"],
        "native_lane_ticks_per_second": projection["native_lane_ticks_per_second"],
        "full_4096_update_seconds": projection["full_4096_update_seconds"],
        "analyzer_cpu_core_hours": projection["analyzer_cpu_core_hours"],
    }
    if not all(resources["ordinary_gates"].values()) or not all(resources["hard_gates"].values()):
        raise RuntimeError("current-byte resource envelope failed")
    source_relatives = (
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_data_plane.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_e2b.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_evaluator.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_full_panel.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_inference.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_lease.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_metrics.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_real_sham.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py",
        "tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_r06_conformance.py",
        "tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_r06_e2b_integration.py",
        "tools/experiments/run_dish_rbhr_r06_full_panel.py",
        "tools/experiments/run_dish_rbhr_r06_e2b_acceptance.py",
    )
    payload = {
        "schema": "DISH_RBHR_R06_E2B_TECHNICAL_RESOURCE_ACCEPTANCE_V1",
        "independent_tests": {"passed": 14, "failed": 0, "wall_seconds": test_wall,
                              "stdout": test.stdout.strip(), "command": command},
        "exact_cli": {"command_module": "tools.experiments.run_dish_rbhr_r06_full_panel",
                      "test_only_loader": "experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_e2b:load_test_only_cli_lease",
                      "completed_units": frontier["completed_units"], "slice_generation": frontier["slice_generation"],
                      "same_identity": True, "complete_result_firewall": True,
                      "frontier_sha256": _sha256(cli_root / "sealed_frontier.json"),
                      "result_sha256": _sha256(cli_root / "complete_result.json")},
        "resources": resources, "preactivity": preactivity,
        "source_sha256": {relative: _sha256(root / relative) for relative in source_relatives},
        "technical_acceptance": True, "lease_request_preparation_eligible": True,
        "fixture_only": True, "result_blind": True, "question_relevant_output": False,
        "lease_issued": False, "nonfixture_master": False, "nonfixture_identity": False,
        "nonfixture_coordinate": False, "nonfixture_model_or_checkpoint": False,
        "nonfixture_training_evaluation_inference": False, "partial_value": False,
        "r05_action": False, "provider_action": False, "git_action": False,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    arguments.output.write_bytes(encoded)
    print(json.dumps({"accepted": True, "output": str(arguments.output), "sha256": hashlib.sha256(encoded).hexdigest(),
                      "resources": resources}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
