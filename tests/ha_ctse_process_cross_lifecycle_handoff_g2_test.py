from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from ha_ctse_process.cross_lifecycle_handoff_g2 import (
    PASS_RESULT,
    build_cases,
    evaluate_information_gate,
    simulate_handoff,
    validate_cases,
)


def test_exhaustive_cases_are_balanced_anonymous_and_cover_handoffs() -> None:
    cases = build_cases()
    inventory = validate_cases(cases)

    assert len(cases) == 96
    assert inventory == {
        "bits": [-1, 1],
        "creator_durations": [1, 2],
        "successor_durations": [2, 4],
        "physical_slots": [0, 1, 2],
        "mapping_count": 12,
        "same_slot_handoffs": 48,
        "cross_slot_handoffs": 48,
        "active_count_profile": [2, 1, 2],
    }

    first = cases[0]
    with pytest.raises(ValueError, match="sign mate"):
        validate_cases(tuple(case for case in cases if case != first))


def test_information_bound_and_constructive_controls_are_exact() -> None:
    result = evaluate_information_gate(build_cases())

    assert result["result"] == PASS_RESULT
    assert result["formal"] is False
    assert result["metrics"] == {
        "successor_per_member_bayes_bound": 0.5,
        "per_member_rec_utility": 0.5,
        "dum_utility": 0.5,
        "team_rec_utility": 1.0,
        "ehc_utility": 1.0,
        "random_mark_utility": 0.5,
        "ehc_flip_action_change": 1.0,
        "ehc_flip_utility": 0.0,
        "ehc_flip_utility_drop": 1.0,
    }
    assert result["state_ownership"] == {
        "creator_member_state_deleted": True,
        "successor_member_state_zero_at_join": True,
        "team_recurrent_state_survives": True,
        "event_held_state_survives": True,
        "fixed_slot_is_state_owner": False,
    }


def test_successor_trace_has_no_bit_or_identity_leakage() -> None:
    cases = build_cases()
    grouped: dict[tuple[object, ...], set[int]] = {}
    for case in cases:
        grouped.setdefault(case.successor_trace_key(), set()).add(case.bit)

    assert len(grouped) == 2
    assert all(bits == {-1, 1} for bits in grouped.values())
    assert {len(trace) for trace in grouped} == {2, 4}

    same_slot = next(case for case in cases if case.creator_slot == case.successor_slot)
    cross_slot = next(case for case in cases if case.creator_slot != case.successor_slot)
    for case in (same_slot, cross_slot):
        state = simulate_handoff(case)
        assert state.successor_value(case) == 0
        assert state.team_recurrent_state == case.bit
        assert state.held_mark == case.bit
        assert state.held_owner_slot is None
        assert not any(
            member.physical_slot == case.creator_slot and member.lifecycle == 0
            for member in state.members
        )
        assert state.with_held_mark(-case.bit).held_mark == -case.bit


def test_nonformal_runner_writes_one_compact_result(tmp_path: Path) -> None:
    run_root = tmp_path / "handoff-g2"
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_cross_lifecycle_handoff_g2.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "exercise",
            "--output-dir",
            str(run_root),
            "--source-commit",
            "a" * 40,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr

    artifact = json.loads((run_root / "result.json").read_text(encoding="utf-8"))
    assert artifact["formal"] is False
    assert artifact["source_commit"] == "a" * 40
    assert artifact["result"] == PASS_RESULT
    assert artifact["case_count"] == 96
    assert sorted(path.name for path in run_root.iterdir()) == ["result.json"]

    repeated = subprocess.run(
        [
            sys.executable,
            str(script),
            "exercise",
            "--output-dir",
            str(run_root),
            "--source-commit",
            "a" * 40,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert repeated.returncode != 0
    assert "already exists" in repeated.stderr
