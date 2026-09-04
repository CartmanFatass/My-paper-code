from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.scdmp_variable_k.d6_duration_action_relevance_a01 import decide_branch


ROOT = Path(__file__).resolve().parents[5]
RUNNER = ROOT / "scripts" / "run_scdmp_d6_duration_action_relevance_a01.py"


@pytest.mark.parametrize(
    ("inputs", "expected"),
    [
        ({"resource_ready": False, "integrity_valid": False,
          "source_population_established": False, "w": 0, "r7": 0, "r13": 0},
         "A_NO_RESULT_RESOURCE_REFUSAL"),
        ({"resource_ready": True, "integrity_valid": False,
          "source_population_established": False, "w": 0, "r7": 0, "r13": 0},
         "A_INVALID_EVIDENCE"),
        ({"resource_ready": True, "integrity_valid": True,
          "source_population_established": False, "w": 0, "r7": 0, "r13": 0},
         "A_SOURCE_POPULATION_NOT_ESTABLISHED"),
        ({"resource_ready": True, "integrity_valid": True,
          "source_population_established": True, "w": 1, "r7": 1, "r13": 1},
         "A_TWO_SIDED_DURATION_ACTION_RELEVANCE"),
        ({"resource_ready": True, "integrity_valid": True,
          "source_population_established": True, "w": 1, "r7": 1, "r13": 0},
         "A_ONE_SIDED_DURATION_ACTION_RELEVANCE"),
        ({"resource_ready": True, "integrity_valid": True,
          "source_population_established": True, "w": 1, "r7": 0, "r13": 0},
         "A_ACTION_RELEVANT_NO_MATERIAL_CROSS_K_PREFERENCE"),
        ({"resource_ready": True, "integrity_valid": True,
          "source_population_established": True, "w": 0, "r7": 0, "r13": 0},
         "A_ZERO_ACTION_VALUE_SPAN"),
    ],
)
def test_ordered_seven_branch_rule(inputs: dict[str, object], expected: str) -> None:
    assert decide_branch(**inputs) == expected


def test_runner_toy_native_smoke(tmp_path: Path) -> None:
    output = tmp_path / "technical-timing-counts.json"
    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--seed", "17", "smoke", "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == "technical-smoke"
    assert payload["scientific_state_created"] is False
    assert payload["counts"]["native_missions"] == 2
    assert payload["counts"]["native_transitions"] > 0
    assert payload["unit_seconds"]["native_mission"] > 0
    assert payload["projected_counts"]["native_missions"] == 1154
    assert payload["projected_seconds"] > 60
    assert (tmp_path / "native-build" / "d6_a01_native.cpp").is_file()
    assert "branch" not in payload
