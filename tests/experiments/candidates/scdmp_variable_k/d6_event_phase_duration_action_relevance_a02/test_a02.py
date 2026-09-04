from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.scdmp_variable_k.d6_event_phase_duration_action_relevance_a02 import (
    decide_branch,
)


ROOT = Path(__file__).resolve().parents[5]
RUNNER = ROOT / "scripts" / "run_scdmp_d6_event_phase_duration_action_relevance_a02.py"
VALID = {
    "resource_ready": True, "integrity_valid": True, "population_established": True,
    "k7": 0, "k78": 0, "n7_plus": 0, "n7_minus": 0,
    "n78_minus": 0, "n78_plus": 0, "all_zero": False,
}


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"resource_ready": False}, "A02_NO_RESULT_RESOURCE_REFUSAL"),
        ({"integrity_valid": False}, "A02_INVALID_EVIDENCE"),
        ({"population_established": False}, "A02_EVENT_PHASE_POPULATION_NOT_ESTABLISHED"),
        ({"k7": 192, "k78": -192, "n7_plus": 4, "n78_minus": 4},
         "A02_EXPECTED_TWO_SIDED_EVENT_ALIGNMENT"),
        ({"k7": -192, "n7_minus": 4}, "A02_REVERSED_EVENT_ALIGNMENT"),
        ({"k7": 192, "n7_plus": 4}, "A02_SHORT_ALIGNMENT_ONLY"),
        ({"k78": -192, "n78_minus": 4}, "A02_LONG_ALIGNMENT_ONLY"),
        ({"all_zero": True}, "A02_ZERO_DURATION_POLICY_SPAN"),
        ({"k7": 31, "k78": -31}, "A02_NONMATERIAL_OR_HETEROGENEOUS_EVENT_ALIGNMENT"),
    ],
)
def test_ordered_nine_branch_rule(changes: dict[str, object], expected: str) -> None:
    inputs = {**VALID, **changes}
    assert decide_branch(**inputs) == expected


def test_runner_toy_native_smoke(tmp_path: Path) -> None:
    output = tmp_path / "technical-timing-counts.json"
    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--seed", "17", "smoke", "--output", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == "technical-smoke"
    assert payload["scientific_state_created"] is False
    assert payload["counts"]["native_missions"] == 2
    assert payload["counts"]["native_transitions"] > 0
    assert payload["event_schedule"] == [
        {"kind": "aligned", "clock": 7, "graph": "HR", "event_applied": True,
         "visible_order": "HR", "latency": 0},
        {"kind": "intrahold", "clock": 13, "graph": "RH", "event_applied": True,
         "visible_order": "RH", "latency": 6},
    ]
    assert payload["unit_seconds"]["native_mission"] > 0
    assert payload["projected_counts"]["native_missions"] == 770
    assert payload["projected_seconds"] > 60
    assert (tmp_path / "native-build" / "d6_a02_native.cpp").is_file()
    assert "branch" not in payload
