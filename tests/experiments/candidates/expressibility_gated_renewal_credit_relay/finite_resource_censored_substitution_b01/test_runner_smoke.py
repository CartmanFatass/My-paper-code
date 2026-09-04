from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[5]
RUNNER = ROOT / "scripts" / "run_egrcr_frcs_b01.py"


def test_toy_runner_writes_one_summary_and_exercises_full_chain(tmp_path: Path) -> None:
    admission = tmp_path / "admission.json"
    admission.write_text(
        json.dumps(
            {
                "schema_version": "test-fixture",
                "passed": True,
                "available_physical_bytes": 8 * 1024**3,
                "effective_available_bytes": 8 * 1024**3,
                "physical_floor_pass": True,
                "effective_floor_pass": True,
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "result"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "run",
            "--seed",
            "17",
            "--output-dir",
            str(output),
            "--admission-receipt",
            str(admission),
            "--toy",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert [path.name for path in output.iterdir()] == ["summary.json"]
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["profile"] == "toy_smoke_non_scientific"
    assert summary["branch"] is None
    assert summary["result_rule_applied"] is False
    assert summary["technical_outcome"] == "NON_SCIENTIFIC_TOY_SMOKE_COMPLETE"
    assert summary["integrity"]["complete_and_valid"] is False
    assert summary["integrity"]["scientific_contract_exact"] is False
    assert summary["integrity"]["scientific_integrity_applicable"] is False
    assert summary["counts"]["training_environment_transitions"] == 72
    assert summary["counts"]["optimizer_updates_per_learned_arm"] == 4
    assert summary["counts"]["evaluation_environment_transitions_per_arm_or_reference"] == 96
    assert summary["initialization"]["same_flat_32_scalar_initialization_bytes"] is True
    assert summary["initialization"]["distinct_mapping_and_reshape"] is True
    assert summary["shared_work"]["same_training_rows_and_terminal_targets"] is True
    assert summary["shared_work"]["identical_lossless_action_time_cell_encoding"] == (
        "(source s, content c, relation a)"
    )
    assert summary["shared_work"]["treatment_only_observation_field_present"] is False
    assert summary["learned_arms"]["GENERIC_PAIR"]["training"]["updates"] == 4
    assert summary["learned_arms"]["ASSOCIATION_FACTOR"]["training"]["updates"] == 4
    generic_work = summary["learned_arms"]["GENERIC_PAIR"]["analytical_forward_work"]
    factor_work = summary["learned_arms"]["ASSOCIATION_FACTOR"]["analytical_forward_work"]
    assert generic_work["row_count_basis"]["total_forward_rows"] == 48
    assert generic_work["total_multiplies"] == 48
    assert generic_work["total_adds"] == 48
    assert factor_work["total_multiplies"] == 144
    assert factor_work["total_adds"] == 192
    assert generic_work["backward_arithmetic_claimed"] is False
    assert factor_work["backward_arithmetic_claimed"] is False
    telemetry = summary["resource_telemetry"]
    assert telemetry["shared_setup_wall_seconds"] >= 0.0
    assert telemetry["per_learned_arm"]["GENERIC_PAIR"]["within_cap"] is True
    assert telemetry["per_learned_arm"]["ASSOCIATION_FACTOR"]["within_cap"] is True
    assert telemetry["invocation_within_cap"] is True
    reference = summary["exact_q_reference"]
    assert reference["role"] == "calibrated_exact_q_reference"
    assert reference["native_optimal_ceiling"] is False
    assert reference["softmax_temperature"] == 1.0
    assert summary["external_resource_admission"]["payload"]["passed"] is True


def test_runner_rejects_nonfrozen_scientific_seed_before_output(tmp_path: Path) -> None:
    output = tmp_path / "must_not_exist"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "run",
            "--seed",
            "17",
            "--output-dir",
            str(output),
            "--admission-receipt",
            str(tmp_path / "missing.json"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 2
    assert "requires frozen seed 2026090401" in completed.stderr
    assert not output.exists()
