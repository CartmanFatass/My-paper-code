from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.vsp_05.support_map import (
    CELL_NAMESPACE_STRIDE,
    CELLS,
    EPISODE_NAMESPACE_BASE,
    FULL_CONFIG,
    FULL_TASK_SEEDS,
    MEMBERSHIP_KINDS,
    OPPORTUNITY_CATEGORIES,
    PROPOSED_SKILLS,
    SEED_NAMESPACE_STRIDE,
    SMOKE_CONFIG,
    CellCleanProcessDynamicRosterEnv,
    SupportCell,
    build_episode_roster,
    classify_support_receipt,
    run_support_map,
)
from ha_ctse_process.dynamic_roster_clean_process_testbed import (
    CleanProcessDynamicRosterEnv,
    make_clean_process_dynamic_roster_ledger,
)
from ha_ctse_process.dynamic_roster_testbed import constructive_actions


@pytest.fixture(scope="module")
def smoke_result():
    return run_support_map(SMOKE_CONFIG, code_revision="TEST")


def test_direct_script_entrypoint_resolves_project_package():
    project_root = Path(__file__).resolve().parents[4]
    completed = subprocess.run(
        [sys.executable, "scripts/run_vsp05_b0_support_map.py", "--help"],
        cwd=project_root,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--config" in completed.stdout


def test_frozen_cells_roots_counts_and_namespace_are_exact():
    assert [cell.name for cell in CELLS] == [
        "REFERENCE",
        "THRESHOLD_MID",
        "THRESHOLD_NEAR_GATE",
        "DRIVE_HIGH",
        "STEP_HIGH",
        "DRIVE_STEP_HIGH",
    ]
    assert [(cell.dynamics(), cell.geometry()) for cell in CELLS] == [
        ((0.75, 0.25, 0.125), (0.125, 0.25, 0.25, 0.0625)),
        ((0.75, 0.25, 0.125), (0.125, 0.1875, 0.25, 0.125)),
        ((0.75, 0.25, 0.125), (0.125, 0.15625, 0.25, 0.1875)),
        ((0.75, 0.375, 0.125), (0.125, 0.25, 0.25, 0.0625)),
        ((0.75, 0.25, 0.1875), (0.125, 0.25, 0.25, 0.0625)),
        ((0.75, 0.375, 0.1875), (0.125, 0.25, 0.25, 0.0625)),
    ]
    assert FULL_TASK_SEEDS == (68101, 68102, 68103)
    assert FULL_CONFIG.counts() == {
        "cells": 6,
        "task_seeds": 3,
        "episodes": 432,
        "environment_transitions": 34_560,
    }
    assert SMOKE_CONFIG.counts() == {
        "cells": 6,
        "task_seeds": 1,
        "episodes": 6,
        "environment_transitions": 480,
    }
    roster = build_episode_roster(FULL_CONFIG)
    ids = [int(row["episode_id"]) for row in roster]
    assert len(ids) == len(set(ids)) == 432
    assert min(ids) >= EPISODE_NAMESPACE_BASE
    assert min(ids) > 31  # disjoint from B1's zero-based episode namespace
    assert ids[0] == EPISODE_NAMESPACE_BASE
    assert ids[24] == EPISODE_NAMESPACE_BASE + SEED_NAMESPACE_STRIDE
    assert ids[72] == EPISODE_NAMESPACE_BASE + CELL_NAMESPACE_STRIDE


def test_receipt_geometry_is_symmetric_inclusive_and_ordered():
    for cell in CELLS:
        negative_truth = classify_support_receipt(
            cell, 0, -cell.truth_position, 9.0
        )
        positive_truth = classify_support_receipt(
            cell, 2, cell.truth_position, -9.0
        )
        assert negative_truth == positive_truth
        assert (negative_truth.gate, negative_truth.truth, negative_truth.label) == (
            True,
            True,
            0,
        )
        negative_alias = classify_support_receipt(
            cell, 0, -cell.hard_position, 9.0
        )
        positive_alias = classify_support_receipt(
            cell, 2, cell.hard_position, -9.0
        )
        assert negative_alias == positive_alias
        assert (negative_alias.gate, negative_alias.truth, negative_alias.label) == (
            True,
            False,
            1,
        )
        hold_truth = classify_support_receipt(
            cell, 1, 0.9, cell.truth_velocity
        )
        hold_alias = classify_support_receipt(
            cell, 1, -0.9, cell.hard_velocity
        )
        unresolved = classify_support_receipt(
            cell, 1, 0.0, cell.hard_velocity + 1e-8
        )
        assert hold_truth.label == 0 and hold_alias.label == 1
        assert unresolved.label is None and not unresolved.gate
    with pytest.raises(ValueError, match="truth > hard"):
        SupportCell("BAD_POSITION", 0.75, 0.25, 0.125, 0.2, 0.2, 0.25, 0.1)
    with pytest.raises(ValueError, match="truth < hard"):
        SupportCell("BAD_VELOCITY", 0.75, 0.25, 0.125, 0.1, 0.2, 0.2, 0.2)


def test_candidate_local_dynamics_change_only_requested_process_factors():
    cell = CELLS[-1]
    ledger = make_clean_process_dynamic_roster_ledger(7, master_seed=68101)
    candidate = CellCleanProcessDynamicRosterEnv(deepcopy(ledger), cell=cell)
    reference = CleanProcessDynamicRosterEnv(deepcopy(ledger))
    assert CellCleanProcessDynamicRosterEnv.step is CleanProcessDynamicRosterEnv.step
    assert CellCleanProcessDynamicRosterEnv.observe is CleanProcessDynamicRosterEnv.observe
    candidate.process_states[0] = np.asarray((0.2, -0.4), dtype=np.float64)
    candidate._advance_process(0, 2)
    expected_velocity = cell.damping * -0.4 + cell.drive
    expected_position = np.clip(0.2 + cell.step * expected_velocity, -1.0, 1.0)
    assert np.array_equal(
        candidate.process_states[0],
        np.asarray((expected_position, expected_velocity), dtype=np.float64),
    )

    candidate = CellCleanProcessDynamicRosterEnv(deepcopy(ledger), cell=cell)
    candidate_view = candidate.observe()
    reference_view = reference.observe()
    assert candidate_view.active_keys == reference_view.active_keys
    assert np.array_equal(candidate_view.observations, reference_view.observations)
    actions = constructive_actions(reference, reference_view)
    candidate_reward, candidate_terminal, _ = candidate.step(actions)
    reference_reward, reference_terminal, _ = reference.step(actions)
    assert candidate_reward == reference_reward
    assert candidate_terminal == reference_terminal
    assert candidate.ledger.episode_id == reference.ledger.episode_id
    assert candidate.ledger.master_seed == reference.ledger.master_seed
    assert candidate.ledger.temporary_leave == reference.ledger.temporary_leave
    assert candidate.ledger.terminal_leave == reference.ledger.terminal_leave
    assert candidate.ledger.wave_arrivals == reference.ledger.wave_arrivals
    assert np.array_equal(
        candidate.ledger.owner_priorities, reference.ledger.owner_priorities
    )


def test_smoke_uses_real_runtime_and_emits_complete_zero_filled_grid(smoke_result):
    assert smoke_result["stage"] == "experiment"
    assert smoke_result["evidence_level"] == "A"
    assert smoke_result["formal"] is False
    assert smoke_result["arm"] == "DET_GATE_ONLY"
    assert smoke_result["actual_counts"] == SMOKE_CONFIG.counts()
    assert smoke_result["call_counts"]["environment_transition"] == 480
    assert smoke_result["call_counts"]["supplied_executor"] == 480
    assert (
        smoke_result["call_counts"]["variable_roster_event_core_transaction"]
        == 480
    )
    assert smoke_result["call_counts"]["proposal_policy"] > 0
    for key in ("learner", "trainer", "optimizer_update"):
        assert smoke_result["call_counts"][key] == 0
    assert smoke_result["updates"] == 0
    assert smoke_result["K_search"] == 0
    assert smoke_result["hypothetical_transitions"] == 0
    assert smoke_result["scientific_disposition"] is None
    assert smoke_result["c_treatment_licensed"] is False
    assert smoke_result["all_cells_reported"] is True

    rows = smoke_result["aggregate_rows"]
    assert len(rows) == len(CELLS) * len(PROPOSED_SKILLS) * len(
        OPPORTUNITY_CATEGORIES
    )
    assert {
        (
            row["cell"],
            row["task_seed"],
            row["proposed_skill"],
            row["opportunity_lifecycle"],
        )
        for row in rows
    } == {
        (cell.name, 68101, proposed, category)
        for cell in CELLS
        for proposed in PROPOSED_SKILLS
        for category in OPPORTUNITY_CATEGORIES
    }
    for row in rows:
        assert set(row["class_ratio"]) == {
            "strict_truth",
            "alias",
            "alias_fraction_of_gated",
        }
        assert len(row["gated_position_range"]) == 2
        assert len(row["gated_velocity_range"]) == 2
        assert set(row["event_rank_coverage"]) == {
            "minimum",
            "maximum",
            "distinct_count",
        }
    assert all(
        set(row["counts"]) == set(MEMBERSHIP_KINDS)
        for row in smoke_result["membership_event_coverage"]
    )


def test_smoke_is_canonical_and_has_no_adaptive_or_best_cell_field(
    smoke_result,
):
    repeated = run_support_map(SMOKE_CONFIG, code_revision="TEST")
    assert repeated == smoke_result
    canonical = json.dumps(repeated, indent=2, sort_keys=True) + "\n"
    assert json.loads(canonical) == smoke_result
    assert canonical.endswith("\n")

    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield str(key)
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    lowered = {key.lower() for key in keys(smoke_result)}
    assert not any("best" in key for key in lowered)
    assert "selected_cell" not in lowered
    assert smoke_result["configuration"]["cell_roster_frozen_before_results"] is True
    assert smoke_result["exclusions"]["adaptive_cell_search"] is True
