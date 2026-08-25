"""SYNTHETIC_TEST_ONLY checks for the empirical analyzer contract.

No test below constructs or admits an empirical coordinate, model, checkpoint,
or activity.  Branch mathematics is exercised only through the shared pure
reducer on hand-written synthetic aggregate arrays.  The empirical entry point
is exercised only for fail-closed refusal.
"""

from __future__ import annotations

from dataclasses import asdict
import math

import pytest

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (
    LEARNED_PACKAGES,
    SCIENCE_REVISION,
    SCRIPTED_PACKAGES,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_artifacts import (
    ANALYZER_OUTPUT_SCHEMA,
    BLOCK_COUNT,
    EMPIRICAL_OBJECT,
    REGISTERED_TAIL_COUNT,
    REGISTERED_TAIL_NAMES,
    EmpiricalBindings,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_inference import (
    EMPIRICAL_ANALYZER_INPUT_SCHEMA,
    EMPIRICAL_RECORD_CLASS,
    SYNTHETIC_TEST_ONLY,
    analyze_empirical_complete_panel,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import (
    BRANCHES,
    DEGREES_OF_FREEDOM,
    DIRECT_VALUE_VARIABLES,
    GAMMA_GLOBAL,
    HELDOUT_CELLS,
    MECHANISM_VARIABLES,
    PREREQUISITE_VARIABLES,
    TRAINING_CELLS,
    compute_registered_bounds,
    reduce_complete_bounds,
)


def _synthetic_bindings() -> EmpiricalBindings:
    """Opaque fake digests only; these do not identify a real coordinate."""

    synthetic_origin = "SYNTHETIC-TEST-ORIGIN"
    return EmpiricalBindings(
        source_manifest_sha256="1" * 64,
        config_sha256="2" * 64,
        native_binding_sha256="3" * 64,
        coordinate_digest="4" * 64,
        master_digest="5" * 64,
        origin_lease_id=synthetic_origin,
        lease_id=synthetic_origin,
        lease_binding_sha256="6" * 64,
    )


def _synthetic_refusal_record(index: int) -> dict[str, object]:
    """Exact top-level shape whose synthetic fence must fire before payload reads."""

    return {
        "schema": EMPIRICAL_ANALYZER_INPUT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "record_class": SYNTHETIC_TEST_ONLY,
        "empirical_record": False,
        "fixture_only": True,
        "synthetic_test_only": True,
        "block_index": index,
        "block_complete_sha256": "7" * 64,
        "aggregate_sha256": "8" * 64,
        "bindings": {"must_not_be_read": object()},
        "technical_complete": False,
        "complete_marker_bound": False,
        "treatment_fidelity": False,
        "analytic_containment": False,
        "selection_or_adaptation": True,
        "evaluation_adaptation": True,
        "forbidden_information": True,
        "registered_coordinate": False,
        "learned_arms": [],
        "scripted_packages": [],
        "training_cells": [],
        "heldout_cells": [],
        "updates_completed": {},
        "training_cell_episodes": {},
        "learned_heldout_episodes": {},
        "scripted_heldout_episodes": {},
        "counts": {},
        "aggregates": {"must_not_be_read": object()},
    }


def _synthetic_aggregate_arrays(
    *,
    prerequisite: dict[str, float] | None = None,
    direct: dict[str, float] | None = None,
    mechanism: dict[str, float] | None = None,
):
    """Hand-written SYNTHETIC_TEST_ONLY arrays, never empirical records."""

    prerequisite_values = {name: [1.0] * 20 for name in PREREQUISITE_VARIABLES}
    direct_values = {name: [0.0] * 20 for name in DIRECT_VALUE_VARIABLES}
    mechanism_values = {name: [0.0] * 20 for name in MECHANISM_VARIABLES}
    for target, changes in (
        (prerequisite_values, prerequisite or {}),
        (direct_values, direct or {}),
        (mechanism_values, mechanism or {}),
    ):
        for name, value in changes.items():
            target[name] = [float(value)] * 20
    return prerequisite_values, direct_values, mechanism_values


def _reduce_synthetic_only(**changes):
    prerequisite, direct, mechanism = compute_registered_bounds(
        *_synthetic_aggregate_arrays(**changes)
    )
    return reduce_complete_bounds(prerequisite, direct, mechanism), (
        prerequisite,
        direct,
        mechanism,
    )


def test_empirical_entry_refuses_all_synthetic_or_fixture_records_before_values() -> None:
    records = [_synthetic_refusal_record(index) for index in range(BLOCK_COUNT)]
    outcome = analyze_empirical_complete_panel(records, expected_bindings=_synthetic_bindings())
    assert outcome.admitted_empirical is False
    assert outcome.branch == "INVALID_OR_INCOMPLETE"
    assert outcome.scientific_branch is None
    assert outcome.bounds == {}
    assert outcome.gates == {}
    assert outcome.predicates == {}
    assert outcome.analyzer_payload is None
    assert "fixture or synthetic" in outcome.failure_reason


@pytest.mark.parametrize("count", [0, 1, 19, 21])
def test_empirical_entry_releases_nothing_before_exact_twenty_blocks(count: int) -> None:
    records = [_synthetic_refusal_record(index) for index in range(count)]
    outcome = analyze_empirical_complete_panel(records, expected_bindings=_synthetic_bindings())
    assert outcome.admitted_empirical is False
    assert outcome.scientific_branch is None
    assert outcome.analyzer_payload is None
    assert outcome.bounds == {}
    assert "exactly twenty" in outcome.failure_reason


def test_frozen_empirical_identity_and_tail_inventory_are_exact_constants() -> None:
    assert EMPIRICAL_RECORD_CLASS == "EMPIRICAL_COMPLETE_BLOCK"
    assert ANALYZER_OUTPUT_SCHEMA == "RCLE_TBCFV_R04_EMPIRICAL_ANALYZER_OUTPUT_V1"
    assert BLOCK_COUNT == 20
    assert len(LEARNED_PACKAGES) == 5
    assert len(SCRIPTED_PACKAGES) == 3
    assert len(TRAINING_CELLS) == 8
    assert len(HELDOUT_CELLS) == 8
    assert len(PREREQUISITE_VARIABLES) == 44
    assert len(DIRECT_VALUE_VARIABLES) == 4
    assert len(MECHANISM_VARIABLES) == 10
    assert REGISTERED_TAIL_COUNT == len(REGISTERED_TAIL_NAMES) == 72
    assert DEGREES_OF_FREEDOM == 19
    assert GAMMA_GLOBAL == 1.0 - 0.05 / 72
    assert set(asdict(_synthetic_bindings())) == {
        "source_manifest_sha256",
        "config_sha256",
        "native_binding_sha256",
        "coordinate_digest",
        "master_digest",
        "origin_lease_id",
        "lease_id",
        "lease_binding_sha256",
    }


def test_shared_math_has_zero_variance_and_exact_inclusive_strict_edges() -> None:
    reduced, bounds = _reduce_synthetic_only(
        direct={
            "time.8_to_12": 2.0,
            "time.12_to_8": -2.0,
            "loss.8_to_12": 0.02,
            "loss.12_to_8": -0.02,
        },
        mechanism={
            "churn_specificity.8_to_12": 2.0,
            "fragmentation.8_to_12": 0.05,
            "commonality.8_to_12": 2.0,
            "persistence.8_to_12": 2.0,
            "bundle.8_to_12": 4.0,
        },
    )
    assert reduced.branch == "TARGET_SPECIFIC_NO_MATERIAL"
    for family in bounds:
        for bound in family.values():
            assert bound.standard_deviation == 0.0
            assert bound.lower == bound.mean
            if hasattr(bound, "upper"):
                assert bound.upper == bound.mean
    strict, _ = _reduce_synthetic_only(direct={"time.8_to_12": 4.0})
    assert strict.predicates["c1p1_target_win"] is False


@pytest.mark.parametrize(
    ("changes", "branch"),
    [
        ({"prerequisite": {"opportunity.time.8_to_12": 0.0}}, BRANCHES[1]),
        (
            {"prerequisite": {"scaffold.time.8_to_8.active_continuation": 0.0}},
            BRANCHES[2],
        ),
        (
            {"prerequisite": {"flex.time_gap.8_to_8.active_continuation": 0.0}},
            BRANCHES[3],
        ),
        (
            {
                "direct": {"time.8_to_12": 5.0},
                "mechanism": {
                    "churn_specificity.8_to_12": 3.0,
                    "fragmentation.8_to_12": 0.06,
                    "commonality.8_to_12": 3.0,
                    "persistence.8_to_12": 3.0,
                    "bundle.8_to_12": 5.0,
                },
            },
            BRANCHES[4],
        ),
        (
            {
                "direct": {"time.8_to_12": 5.0},
                "mechanism": {
                    "churn_specificity.8_to_12": 3.0,
                    "fragmentation.8_to_12": 0.06,
                    "commonality.8_to_12": 3.0,
                    "bundle.8_to_12": 5.0,
                },
            },
            BRANCHES[5],
        ),
        ({"direct": {"time.8_to_12": 5.0}}, BRANCHES[6]),
        (
            {
                "direct": {"time.8_to_12": 5.0},
                "mechanism": {"churn_specificity.8_to_12": 3.0},
            },
            BRANCHES[7],
        ),
        ({"direct": {"time.8_to_12": -5.0}}, BRANCHES[8]),
        ({"mechanism": {"fragmentation.8_to_12": 0.06}}, BRANCHES[9]),
        ({}, BRANCHES[10]),
        ({"direct": {"time.8_to_12": 3.0}}, BRANCHES[11]),
    ],
)
def test_shared_pure_reducer_covers_identical_first_match_map_on_synthetic_only_arrays(
    changes, branch
) -> None:
    reduced, _ = _reduce_synthetic_only(**changes)
    assert reduced.branch == branch


def test_nonfinite_synthetic_arrays_fail_before_shared_reduction() -> None:
    prerequisite, direct, mechanism = _synthetic_aggregate_arrays()
    direct[DIRECT_VALUE_VARIABLES[0]][0] = math.nan
    with pytest.raises(ValueError, match="finite"):
        compute_registered_bounds(prerequisite, direct, mechanism)
