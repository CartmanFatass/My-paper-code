from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.scdmp_variable_k.d6_cross_k_q_sharing_b01.rules import decide_branch


ROOT = Path(__file__).resolve().parents[5]


def _base() -> dict[str, object]:
    return {
        "integrity_valid": True, "host_pass": True,
        "exposure_final": {"D6": [0.2, 0.2, 0.2], "D8": [0.2, 0.2, 0.2]},
        "d6_competent": [True, True, True], "d8_competent": [True, True, True],
        "delta_t": [0, 0, 0], "delta_auc": [0.0, 0.0, 0.0],
        "witness": [False, False, False], "final_return_difference": [0.0, 0.0, 0.0],
    }


@pytest.mark.parametrize(
    ("changes", "expected"),
    (
        ({"integrity_valid": False}, "INVALID_EVIDENCE"),
        ({"host_pass": False, "exposure_final": {}}, "HOST_NOT_DURATION_DISCRIMINATING"),
        ({"exposure_final": {"D6": [0.0, 0.2, 0.2], "D8": [0.2, 0.2, 0.2]}}, "EXPOSURE_NOT_ACHIEVED"),
        ({"d8_competent": [True, False, True]}, "D8_COMPARATOR_NOT_COMPETENT"),
        ({"delta_t": [20, 20, 40], "delta_auc": [0.05, 0.05, 0.08],
          "witness": [True, True, False]}, "PRELIMINARY_CROSS_K_VALUE_SHARING_SIGNAL"),
        ({"d6_competent": [False, False, True]}, "PRELIMINARY_NEGATIVE_TRANSFER"),
        ({}, "NO_MATERIAL_VALUE_SHARING_DIFFERENCE"),
        ({"delta_t": [20, 20, 20]}, "INSTABILITY_OR_STATE_HETEROGENEITY"),
    ),
)
def test_ordered_result_rule(changes: dict[str, object], expected: str) -> None:
    facts = _base()
    facts.update(changes)
    assert decide_branch(facts) == expected


def test_toy_smoke_runs_end_to_end_without_scientific_state(tmp_path: Path) -> None:
    output = tmp_path / "smoke"
    completed = subprocess.run([
        sys.executable, str(ROOT / "scripts" / "run_scdmp_d6_cross_k_q_sharing_b01.py"),
        "--seed", "9029", "smoke", "--output-root", str(output),
    ], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert not (output / "summary.json").exists()
    technical = json.loads((output / "technical-timing-counts.json").read_text(encoding="utf-8"))
    assert technical["scientific_result_state_created"] is False
    assert all(value > 0 for value in technical["counts"].values())
    assert all(value >= 0.0 for value in technical["unit_seconds"].values())
