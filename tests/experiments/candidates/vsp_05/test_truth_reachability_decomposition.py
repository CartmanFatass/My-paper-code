from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.vsp_05.support_map import (
    CELLS,
    FULL_CONFIG as B0_FULL_CONFIG,
    FULL_TASK_SEEDS,
    OPPORTUNITY_CATEGORIES,
    SupportMapConfig,
    classify_support_receipt,
)
from experiments.candidates.vsp_05.truth_reachability_decomposition import (
    CAPTURE_BOUNDARY,
    FULL_CONFIG,
    MASK_FIELDS,
    NEAR_MISS_DOMAIN,
    SEMANTIC_MISSING_FIELDS,
    SMOKE_CONFIG,
    SKILLS,
    TRUTH_SET_DOMAIN,
    _mask_code,
    run_differential_nonintervention_smoke,
    run_truth_reachability_decomposition,
    semantic_missing_predicates,
    semantic_near_miss_class,
)


@pytest.fixture(scope="module")
def smoke_result():
    return run_truth_reachability_decomposition(
        SMOKE_CONFIG, code_revision="FOCUSED_TEST"
    )


def test_direct_script_entrypoint_resolves_project_package():
    project_root = Path(__file__).resolve().parents[4]
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_vsp05_a1_truth_reachability_decomposition.py",
            "--help",
        ],
        cwd=project_root,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.count("--config") >= 1
    assert "--output" in completed.stdout


def test_registered_configuration_and_namespace_are_exact_b0_reuse(smoke_result):
    assert FULL_CONFIG is B0_FULL_CONFIG
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
    assert smoke_result["configuration"]["episode_namespace"][
        "unchanged_from_b0"
    ] is True
    wrong = SupportMapConfig("smoke", (68101,), 2)
    with pytest.raises(ValueError, match="only the registered"):
        run_truth_reachability_decomposition(wrong, code_revision="TEST")


def test_capture_is_after_membership_commit_and_before_current_primitive_step(
    smoke_result,
):
    rows = smoke_result["real_frontier_rows"]
    assert rows
    assert all(row["capture_boundary"] == CAPTURE_BOUNDARY for row in rows)
    assert all(row["committed_record_present"] for row in rows)
    assert all(
        row["environment_step"]
        == row["physical_time"]
        == row["completed_primitive_transitions_at_capture"]
        for row in rows
    )
    joins = [row for row in rows if row["lifecycle_category"] == "JOIN"]
    assert joins
    assert all(row["incumbent_present"] is False for row in joins)
    assert all(row["incumbent_skill"] is None for row in joins)
    assert all(row["different_successor"] is False for row in joins)
    assert all(row["complete_mask"]["different_successor"] is False for row in joins)


def test_event_ranks_are_exact_per_key_and_never_double_incremented(smoke_result):
    grouped = defaultdict(list)
    for row in smoke_result["real_frontier_rows"]:
        grouped[(row["cell"], row["task_seed"], row["episode_id"], row["lifecycle_key"])].append(
            (row["environment_step"], row["event_rank"])
        )
    assert grouped
    for values in grouped.values():
        ordered = [rank for _, rank in sorted(values)]
        assert ordered == list(range(1, len(ordered) + 1))


def test_all_skill_classification_matches_existing_frozen_classifier(smoke_result):
    cells = {cell.name: cell for cell in CELLS}
    for row in smoke_result["real_frontier_rows"]:
        assert set(row["all_skill_classification"]) == {"0", "1", "2"}
        for skill in SKILLS:
            receipt = classify_support_receipt(
                cells[row["cell"]], skill, row["position"], row["velocity"]
            )
            assert row["all_skill_classification"][str(skill)] == {
                "gate": receipt.gate,
                "strict_truth": receipt.truth,
            }
            if receipt.truth:
                assert receipt.gate
        actual = row["all_skill_classification"][str(row["actual_proposal"])]
        assert actual["gate"] == row["actual_proposal_gate"]
        assert actual["strict_truth"] == row["actual_proposal_strict_truth"]


def test_complete_mask_and_missing_set_are_simultaneous_not_first_blocker():
    mask = {
        "frontier_present": True,
        "incumbent_present": False,
        "different_successor": False,
        "actual_proposal_gate": False,
        "truth_any_skill": False,
        "truth_non_incumbent_skill": False,
        "truth_actual_proposal": False,
        "eligible_strict_truth": False,
    }
    missing = semantic_missing_predicates(mask)
    assert missing == tuple(
        field
        for field in SEMANTIC_MISSING_FIELDS
        if field
        in {
            "incumbent_present",
            "different_successor",
            "truth_any_skill",
            "truth_non_incumbent_skill",
            "truth_actual_proposal",
        }
    )
    assert "actual_proposal_gate" not in missing
    assert semantic_near_miss_class(mask) == "MISSING:" + "|".join(missing)
    assert _mask_code(mask) == 1

    inconsistent = dict(mask)
    inconsistent["truth_actual_proposal"] = True
    with pytest.raises(ValueError, match="must imply"):
        semantic_missing_predicates(inconsistent)


def test_zero_retaining_mask_and_stratified_tables_are_complete(smoke_result):
    tables = smoke_result["predicate_tables"]
    histogram = tables["complete_mask_histogram"]
    assert len(histogram) == 256
    assert [row["mask_code"] for row in histogram] == list(range(256))
    assert sum(row["count"] for row in histogram) == len(
        smoke_result["real_frontier_rows"]
    )
    assert any(row["count"] == 0 for row in histogram)
    assert len(tables["by_cell"]) == len(CELLS)
    assert len(tables["by_seed"]) == len(FULL_TASK_SEEDS)
    assert len(tables["by_cell_seed"]) == len(CELLS) * len(FULL_TASK_SEEDS)
    assert len(tables["by_lifecycle_category"]) == len(OPPORTUNITY_CATEGORIES)
    assert len(tables["by_incumbent"]) == 4
    assert len(tables["by_actual_proposal"]) == len(SKILLS)
    assert len(tables["by_truth_skill_set"]) == len(TRUTH_SET_DOMAIN) == 8
    assert [row["semantic_near_miss_class"] for row in tables["by_semantic_near_miss"]] == list(
        NEAR_MISS_DOMAIN
    )
    assert len(NEAR_MISS_DOMAIN) == 64
    assert any(row["count"] == 0 for row in tables["by_semantic_near_miss"])


def test_static_compatibility_is_complete_and_never_real_reachability(smoke_result):
    real_rows = smoke_result["real_frontier_rows"]
    static_rows = smoke_result["static_hypothetical_incumbent_rows"]
    assert len(static_rows) == 3 * len(real_rows)
    grouped = defaultdict(set)
    for row in static_rows:
        assert row["static"] is True
        assert row["reachable_evidence"] is False
        assert row["hypothetical_environment_transitions"] == 0
        grouped[row["source_real_frontier_id"]].add(
            row["hypothetical_incumbent_skill"]
        )
    assert grouped
    assert all(values == {0, 1, 2} for values in grouped.values())
    table = smoke_result["static_compatibility_table"]
    assert table["reachable_evidence"] is False
    assert table["hypothetical_environment_transitions"] == 0
    assert len(table["joint_zero_filled"]) == 36
    assert sum(row["count"] for row in table["joint_zero_filled"]) == len(
        static_rows
    )


def test_smoke_real_activity_and_protected_zero_calls_are_exact(smoke_result):
    assert smoke_result["actual_counts"] == SMOKE_CONFIG.counts()
    calls = smoke_result["call_counts"]
    assert calls["environment_transition"] == 480
    assert calls["supplied_executor"] == 480
    assert calls["variable_roster_event_core_transaction"] == 480
    assert calls["proposal_policy"] == len(smoke_result["real_frontier_rows"])
    assert calls["static_classification"] == 3 * calls["proposal_policy"]
    for name in (
        "hypothetical_environment_transition",
        "learner",
        "trainer",
        "optimizer_update",
    ):
        assert calls[name] == 0
    assert smoke_result["real_calls"]["hypothetical_environment"] is False
    assert smoke_result["real_calls"]["learner"] is False
    assert smoke_result["real_calls"]["trainer"] is False
    assert smoke_result["real_calls"]["optimizer"] is False
    assert smoke_result["K_search"] == 0
    assert smoke_result["hypothetical_transitions"] == 0
    assert smoke_result["updates"] == 0
    assert smoke_result["scientific_disposition"] is None
    assert smoke_result["c_treatment_licensed"] is False
    assert 1 <= smoke_result["decision_map"]["branch"] <= 5
    assert smoke_result["decision_map"]["finite_evidence_only"] is True


def test_differential_smoke_proves_nonintervention_on_real_runtime():
    evidence = run_differential_nonintervention_smoke(steps=12)
    assert evidence["all_equal"] is True
    assert all(evidence["checks"].values())
    assert evidence["observed_real_frontier_rows"] > 0
    assert evidence["observed_static_rows"] == 3 * evidence[
        "observed_real_frontier_rows"
    ]
    assert evidence["hypothetical_environment_transitions"] == 0


def test_smoke_is_deterministic_and_json_canonical(smoke_result):
    repeated = run_truth_reachability_decomposition(
        SMOKE_CONFIG, code_revision="FOCUSED_TEST"
    )
    assert repeated == smoke_result
    canonical = json.dumps(repeated, indent=2, sort_keys=True) + "\n"
    assert json.loads(canonical) == smoke_result
    assert canonical.endswith("\n")
    assert set(smoke_result["predicate_tables"]["mask_field_bit_order"]) == set(
        MASK_FIELDS
    )
