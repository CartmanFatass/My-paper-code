from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from ha_ctse_process.async_commitment_roster_g3 import (
    FAIL_RESULT,
    PASS_RESULT,
    RosterState,
    evaluate_information_gate,
    validate_information_gate_result,
)
from scripts.run_async_commitment_roster_g3 import run_gate


@pytest.fixture(scope="module")
def gate_result() -> dict[str, object]:
    return evaluate_information_gate()


def test_lifecycle_owned_commitment_transition_contract() -> None:
    state = RosterState.empty()
    state = state.join(10, 0).commit(10, 2)
    state = state.temporary_leave(10)
    assert state.record(10).commitment == 2
    assert not state.record(10).active

    state = state.rejoin(10, 3)
    assert state.record(10).commitment == 2
    assert state.record(10).physical_slot == 3

    state = state.terminal_leave(10)
    assert not state.contains(10)
    state = state.join(11, 3)
    assert state.record(11).commitment is None


def test_exhaustive_gate_has_balanced_anonymous_source(
    gate_result: dict[str, object],
) -> None:
    assert gate_result["case_count"] == 18_400
    assert gate_result["case_counts_by_active"] == {
        "2": 400,
        "3": 3_600,
        "4": 14_400,
    }
    assert len(set(gate_result["case_counts_by_variant"].values())) == 1
    assert gate_result["checks"] == {
        "editor_context_anonymous": True,
        "event_variant_balanced": True,
        "physical_slot_permutation_invariant": True,
        "standing_roster_permutation_complete": True,
    }
    assert all(gate_result["state_ownership"].values())


def test_constructive_controls_nulls_and_intervention(
    gate_result: dict[str, object],
) -> None:
    metrics = gate_result["metrics"]
    assert metrics["roster_editor_utility"] == 1.0
    assert metrics["team_rec_oracle_utility"] == 1.0
    assert metrics["independent_editor_utility_by_active"] == {
        "2": 0.875,
        "3": pytest.approx(5.0 / 6.0),
        "4": 0.8125,
    }
    assert all(
        value < 1.0
        for value in metrics["shuffled_roster_utility_by_active"].values()
    )
    assert metrics["intervention_choice_change"] == 1.0
    assert metrics["intervention_adapted_utility"] == 1.0
    assert metrics["intervention_utility_gain_by_active"] == {
        "2": 0.5,
        "3": pytest.approx(1.0 / 3.0),
        "4": 0.25,
    }
    assert gate_result["result"] == PASS_RESULT
    validate_information_gate_result(gate_result)


def test_nonformal_runner_and_fail_closed_validation(
    tmp_path: Path,
    gate_result: dict[str, object],
) -> None:
    source_commit = "7a99f46e34d0ab6b8a55f62ec7701037f850a111"
    output = tmp_path / "gate"
    artifact = run_gate(output, source_commit=source_commit)
    assert artifact == output / "result.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["formal"] is False
    assert payload["source_commit"] == source_commit
    assert payload["result"] == PASS_RESULT
    validate_information_gate_result(payload)

    payload["formal"] = True
    with pytest.raises(ValueError, match="formal=false"):
        validate_information_gate_result(payload)

    payload = dict(gate_result)
    payload["result"] = FAIL_RESULT
    with pytest.raises(ValueError, match="registered result"):
        validate_information_gate_result(payload)


def test_runner_is_directly_executable(tmp_path: Path) -> None:
    source_commit = "7a99f46e34d0ab6b8a55f62ec7701037f850a111"
    output = tmp_path / "cli-gate"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_async_commitment_roster_g3.py",
            "--output-root",
            str(output),
            "--source-commit",
            source_commit,
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert (output / "result.json").is_file()
