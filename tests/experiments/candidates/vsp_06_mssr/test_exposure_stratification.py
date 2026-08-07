"""Tests for the loop-3 exposure stratification (Pro guard A).

Proof-sized: the expensive full stratification runs at most once (the module
caches it); the classifier itself is additionally unit-tested on synthetic
inputs with no rollout.
"""

from __future__ import annotations

import pytest

from experiments.candidates.vsp_06_mssr.exposure_stratification import (
    DIFFER_KIND_PARTNER_IDENTITY_ONLY,
    DIFFER_KIND_PAYLOAD_SEQUENCE,
    DIFFER_KIND_ROW_COUNT,
    EQUAL_PAYLOAD_CORRECTED_NAME,
    EXPOSURE_PRE_PERTURBATION,
    EXPOSURE_POST_PERTURBATION_TARGET_UNEXPOSED,
    EXPOSURE_TARGET_EXPOSED_EQUAL_PAYLOAD,
    EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD,
    P_SUBCLASS_CANCELLED,
    P_SUBCLASS_DECAYED,
    P_SUBCLASS_NEVER_CHANGED,
    P_SUBCLASS_STILL_DIFFERENT,
    PRIMARY_CLASSES,
    SCOPE,
    classify,
    decompose_row_different,
    proof,
)
from experiments.candidates.vsp_06_mssr.history_reconvergence_search import (
    OpportunityComparison,
)
from experiments.candidates.vsp_06_mssr.d1_change_f_matched_pair import (
    FROZEN_SOURCED_PAIR,
)


def _comparison(
    *,
    window=(10,),
    physical_time=20,
    znp_full_match=False,
    znp_minus_hidden_match=False,
) -> OpportunityComparison:
    return OpportunityComparison(
        episode_id=0,
        base_family="sym_persist_idle",
        target_key="0",
        partner_key="2",
        window=tuple(window),
        physical_time=int(physical_time),
        membership_epoch=0,
        znp_full_match=bool(znp_full_match),
        znp_minus_hidden_match=bool(znp_minus_hidden_match),
        delta_p=0.0,
        high_hidden_l2_gap=0.0,
    )


ROW_A = (0, "2", 0.5)
ROW_B = (0, "2", 0.25)
ROW_C = (0, "3", 0.5)


def test_classify_unit_semantics():
    """The registered rule on synthetic inputs: pre-perturbation by time;
    unexposed / exposed-equal split by post-flip write count; exposed-different
    by positional row difference; refinements follow the digest flags."""
    # Pre-perturbation: opportunity read precedes the flipped primitive.
    flags = classify(_comparison(window=(10,), physical_time=10), {}, {})
    assert flags["primary"] == EXPOSURE_PRE_PERTURBATION

    # Post-perturbation, rows equal, no post-flip write: unexposed.
    trajectory = {8: (ROW_A,), 12: (ROW_A,), 20: (ROW_A,)}
    flags = classify(
        _comparison(window=(10,), physical_time=20), trajectory, dict(trajectory)
    )
    assert flags["primary"] == EXPOSURE_POST_PERTURBATION_TARGET_UNEXPOSED
    assert flags["post_flip_write_count"] == 0

    # Post-perturbation, rows equal, one post-flip write: exposed, equal payload.
    trajectory = {8: (ROW_A,), 12: (ROW_A,), 20: (ROW_A, ROW_B)}
    flags = classify(
        _comparison(window=(10,), physical_time=20), trajectory, dict(trajectory)
    )
    assert flags["primary"] == EXPOSURE_TARGET_EXPOSED_EQUAL_PAYLOAD
    assert flags["post_flip_write_count"] == 1

    # Rows differ positionally (payload or partner): exposed, different payload;
    # refinements mirror the comparison's digest flags.
    base = {8: (ROW_A,), 12: (ROW_A,), 20: (ROW_A, ROW_B)}
    perturbed = {8: (ROW_A,), 12: (ROW_A,), 20: (ROW_A, ROW_C)}
    flags = classify(
        _comparison(
            window=(10,), physical_time=20, znp_minus_hidden_match=True
        ),
        base,
        perturbed,
    )
    assert flags["primary"] == EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD
    assert flags["post_exposure_environment_reconverged"] is True
    assert flags["post_exposure_full_non_p_reconverged"] is False

    # A length mismatch is itself a differing exposure.
    base = {12: (ROW_A,), 20: (ROW_A, ROW_B)}
    perturbed = {12: (ROW_A,), 20: (ROW_A,)}
    flags = classify(
        _comparison(window=(10,), physical_time=20, znp_full_match=True),
        base,
        perturbed,
    )
    assert flags["primary"] == EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD
    assert flags["post_exposure_full_non_p_reconverged"] is True

    # The registered rule is defined for single-step windows only.
    with pytest.raises(ValueError):
        classify(_comparison(window=(10, 11), physical_time=20), {}, {})


def _snap(rows, p):
    return {"rows": rows, "current_p": float(p)}


def test_decompose_row_different_unit_semantics():
    """Pro loop-4 C5 differ-kind rule on synthetic inputs: row-count beats
    payload beats partner-identity-only; P subclasses apply to the payload kind
    only and follow the measured current_p trajectory."""
    comparison = _comparison(window=(10,), physical_time=20)

    # Row-count mismatch: a write occasion itself moved.
    base = {12: _snap((ROW_A,), 0.5), 20: _snap((ROW_A, ROW_B), 0.4)}
    pert = {12: _snap((ROW_A,), 0.5), 20: _snap((ROW_A,), 0.5)}
    out = decompose_row_different(comparison, base, pert)
    assert out["differ_kind"] == DIFFER_KIND_ROW_COUNT
    assert out["p_subclass"] is None
    assert out["row_count_differs"]

    # Payload differs, P still different at the compared time.
    base = {12: _snap((ROW_A,), 0.5), 20: _snap((ROW_A, ROW_B), 0.4)}
    pert = {12: _snap((ROW_A,), 0.5), 20: _snap((ROW_A, ROW_C), 0.3)}
    out = decompose_row_different(comparison, base, pert)
    assert out["differ_kind"] == DIFFER_KIND_PAYLOAD_SEQUENCE
    assert out["p_subclass"] == P_SUBCLASS_STILL_DIFFERENT
    assert out["payload_diff_position_count"] == 1

    # ONE payload difference, P differed earlier, exactly equal now: decayed.
    base = {12: _snap((ROW_A,), 0.5), 16: _snap((ROW_A, ROW_B), 0.4),
            20: _snap((ROW_A, ROW_B), 0.25)}
    pert = {12: _snap((ROW_A,), 0.5), 16: _snap((ROW_A, ROW_C), 0.3),
            20: _snap((ROW_A, ROW_C), 0.25)}
    out = decompose_row_different(comparison, base, pert)
    assert out["differ_kind"] == DIFFER_KIND_PAYLOAD_SEQUENCE
    assert out["p_subclass"] == P_SUBCLASS_DECAYED
    assert out["p_ever_differed_pre_comparison"]
    assert out["p_equal_at_comparison"]

    # TWO payload differences, P differed earlier, equal now: cancelled.
    row_d = (1, "2", 0.75)
    row_e = (1, "2", 0.1)
    base = {16: _snap((ROW_A, ROW_B), 0.4), 20: _snap((ROW_A, ROW_B, row_d), 0.25)}
    pert = {16: _snap((ROW_A, ROW_C), 0.3), 20: _snap((ROW_A, ROW_C, row_e), 0.25)}
    out = decompose_row_different(comparison, base, pert)
    assert out["differ_kind"] == DIFFER_KIND_PAYLOAD_SEQUENCE
    assert out["p_subclass"] == P_SUBCLASS_CANCELLED
    assert out["payload_diff_position_count"] == 2

    # Payload differs but P never differed at any shared time.
    base = {16: _snap((ROW_A,), 0.5), 20: _snap((ROW_A, ROW_B), 0.25)}
    pert = {16: _snap((ROW_A,), 0.5), 20: _snap((ROW_A, ROW_C), 0.25)}
    out = decompose_row_different(comparison, base, pert)
    assert out["p_subclass"] == P_SUBCLASS_NEVER_CHANGED

    # Partner identity only: NOT a differing scalar-P exposure; no P subclass.
    row_same_payload_other_partner = (0, "3", 0.25)
    base = {20: _snap((ROW_A, ROW_B), 0.25)}
    pert = {20: _snap((ROW_A, row_same_payload_other_partner), 0.25)}
    out = decompose_row_different(comparison, base, pert)
    assert out["differ_kind"] == DIFFER_KIND_PARTNER_IDENTITY_ONLY
    assert out["p_subclass"] is None
    assert out["partner_diff_position_count"] == 1
    assert out["payload_diff_position_count"] == 0

    # Not row-different at the compared time: refuse to classify.
    base = {20: _snap((ROW_A,), 0.5)}
    with pytest.raises(ValueError):
        decompose_row_different(comparison, base, dict(base))

    # Single-step windows only.
    with pytest.raises(ValueError):
        decompose_row_different(
            _comparison(window=(10, 11), physical_time=20), base, dict(base)
        )


def test_primary_classes_partition_all_comparisons():
    """The four primary classes partition every compared opportunity, and the
    set totals reproduce the frozen loop-3 / loop-4 counts (378/316/25/10)."""
    report = proof()
    counts = report["counts"]
    assert counts["comparisons"] == 378
    assert sum(counts["primary"].values()) == counts["comparisons"]
    assert set(counts["primary"]) == set(PRIMARY_CLASSES)

    full = report["full_match_stratification"]
    assert full["total"] == 316
    assert sum(full["primary"].values()) == full["total"]

    residual = report["hidden_residual_stratification"]
    assert residual["total"] == 25
    assert sum(residual["primary"].values()) == residual["total"]

    sourcing = report["reconverged_p_different_stratification"]
    assert sourcing["total"] == 10
    assert sum(sourcing["primary"].values()) == sourcing["total"]

    # The refinements live inside the exposed-with-different-payload class.
    exposed_different = counts["primary"][EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD]
    assert counts["post_exposure_environment_reconverged"] <= exposed_different
    assert counts["post_exposure_full_non_p_reconverged"] <= exposed_different

    # Frozen MEASURED splits (regression pins; a drift in any class must fail
    # loudly, not slip through the partition identities above).
    assert counts["primary"] == {
        EXPOSURE_PRE_PERTURBATION: 210,
        EXPOSURE_POST_PERTURBATION_TARGET_UNEXPOSED: 81,
        EXPOSURE_TARGET_EXPOSED_EQUAL_PAYLOAD: 66,
        EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD: 21,
    }
    assert counts["post_exposure_environment_reconverged"] == 15
    assert counts["post_exposure_full_non_p_reconverged"] == 0
    assert full["primary"] == {
        EXPOSURE_PRE_PERTURBATION: 210,
        EXPOSURE_POST_PERTURBATION_TARGET_UNEXPOSED: 50,
        EXPOSURE_TARGET_EXPOSED_EQUAL_PAYLOAD: 56,
        EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD: 0,
    }
    assert residual["primary"] == {
        EXPOSURE_PRE_PERTURBATION: 0,
        EXPOSURE_POST_PERTURBATION_TARGET_UNEXPOSED: 0,
        EXPOSURE_TARGET_EXPOSED_EQUAL_PAYLOAD: 10,
        EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD: 15,
    }

    # Every classified row is internally consistent.
    for row in report["classified"]:
        assert row["primary"] in PRIMARY_CLASSES
        if row["primary"] != EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD:
            assert not row["post_exposure_environment_reconverged"]
            assert not row["post_exposure_full_non_p_reconverged"]
            assert row["differ_kind"] is None and row["p_subclass"] is None
        else:
            assert row["differ_kind"] is not None

    # Pro loop-4 C5: the corrected equal-payload semantics are registered.
    rule = report["classification_rule"]
    assert rule["equal_payload_corrected_name"] == EQUAL_PAYLOAD_CORRECTED_NAME

    # Differ-kind decomposition of the row-different class is a partition, and
    # P subclasses cover exactly the payload-sequence kind.
    decomposition = report["row_different_decomposition"]
    assert decomposition["total"] == 21
    assert sum(decomposition["differ_kind"].values()) == decomposition["total"]
    assert (
        sum(decomposition["p_subclass"].values())
        == decomposition["differ_kind"][DIFFER_KIND_PAYLOAD_SEQUENCE]
    )
    # Frozen MEASURED decomposition pins: 16 payload-sequence-different (ALL
    # with the current P STILL different) and 5 partner-identity-only.
    assert decomposition["differ_kind"] == {
        DIFFER_KIND_PARTNER_IDENTITY_ONLY: 5,
        DIFFER_KIND_PAYLOAD_SEQUENCE: 16,
        DIFFER_KIND_ROW_COUNT: 0,
    }
    assert decomposition["p_subclass"] == {
        P_SUBCLASS_STILL_DIFFERENT: 16,
        P_SUBCLASS_NEVER_CHANGED: 0,
        P_SUBCLASS_DECAYED: 0,
        P_SUBCLASS_CANCELLED: 0,
    }
    # The five dP=0 row-different cases are each decomposed -- and every one is
    # PARTNER-IDENTITY-ONLY with the P trajectory equal at every shared time:
    # not a differing scalar-P exposure at all (the P update consumes payload),
    # hence NOT evidence that P forgot while F retained.
    zero_cases = decomposition["delta_p_zero_cases"]
    assert len(zero_cases) == 5
    for case in zero_cases:
        assert case["differ_kind"] == DIFFER_KIND_PARTNER_IDENTITY_ONLY
        assert case["p_subclass"] is None
        assert case["payload_diff_position_count"] == 0
        assert case["partner_diff_position_count"] >= 1
        assert not case["row_count_differs"]
        assert not case["p_ever_differed_pre_comparison"]


def test_frozen_d1_pair_is_exposed_different():
    """The loop-4 sourced pair's compared opportunity classifies as exposed with
    a DIFFERENT payload, environment-reconverged but not fully reconverged --
    exactly the obstruction class CHANGE_F is meant to remove."""
    pair = FROZEN_SOURCED_PAIR
    report = proof()
    rows = [
        row
        for row in report["classified"]
        if row["base_family"] == pair.base_family
        and row["target_key"] == pair.target_key
        and row["partner_key"] == pair.partner_key
        and tuple(row["window"]) == pair.window
        and row["physical_time"] == pair.physical_time
    ]
    assert len(rows) == 1
    row = rows[0]
    assert row["primary"] == EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD
    assert row["post_exposure_environment_reconverged"] is True
    assert row["post_exposure_full_non_p_reconverged"] is False
    assert abs(row["delta_p"] - pair.delta_p) < 1e-12

    # The whole loop-4 sourcing set is exposed-different (matches d1's own
    # exposure_positive filter, which admitted all 10).
    sourcing = report["reconverged_p_different_stratification"]
    assert (
        sourcing["primary"][EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD]
        == sourcing["total"]
    )


def test_scope_registers_rule_and_defers_reading():
    """SCOPE names Pro's flags, states the mechanical rule, and defers the
    reading of the strata to External Pro."""
    scope = SCOPE.lower()
    for name in PRIMARY_CLASSES:
        assert name.lower() in scope
    assert "mechanical" in scope
    assert "belongs to external pro" in scope
    assert "control" in scope
    assert "no population, support, or overlap claim" in scope
