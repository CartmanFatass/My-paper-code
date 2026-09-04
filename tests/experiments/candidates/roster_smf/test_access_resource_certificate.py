from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from itertools import product
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.roster_smf.access_resource_certificate import (
    AccessFacts,
    AccessEvent,
    AccessRegime,
    AccessSession,
    ClosureError,
    FeatureAccess,
    FiniteDesign,
    R_ALL,
    R_MAX,
    R_SELECTED,
    ResourceVector,
    SampleOutcome,
    TERMINAL,
    bind_snapshot,
    build_bound_snapshot,
    canonical_bytes,
    emulate_float32_census,
    evaluate_design,
    pair_design,
    resolve_access_regime,
    run_certificate,
    snapshot_token,
    validate_claim,
)
from ha_ctse_process.variable_roster_event_types import BoundaryMember, BoundarySnapshot


BULK_KEYS = ("bulk-1", "bulk-2", "bulk-3")
POSITIVE = {"bulk-1": Fraction(1), "bulk-2": Fraction(2), "bulk-3": Fraction(4)}
SIGNED = {"bulk-1": Fraction(1), "bulk-2": Fraction(-1), "bulk-3": Fraction(0)}


def bind(snapshot: BoundarySnapshot | None = None):
    return bind_snapshot(
        build_bound_snapshot() if snapshot is None else snapshot,
        protected_keys=("protected",),
        bulk_keys=BULK_KEYS,
        registry=FeatureAccess(),
    )


def member(key: str, epoch: int, value: float) -> BoundaryMember:
    return BoundaryMember.make(
        key,
        epoch,
        observation=[0.0],
        critic_member_features=[value],
        obs_dim=1,
        critic_member_dim=1,
    )


def custom_snapshot(*, physical_time: int = 41, bulk_1_epoch: int = 11) -> BoundarySnapshot:
    return BoundarySnapshot.make(
        physical_time=physical_time,
        members=(
            member("protected", 7, 10.0),
            member("bulk-1", bulk_1_epoch, 1.0),
            member("bulk-2", 13, 2.0),
            member("bulk-3", 17, 4.0),
        ),
        critic_global_features=[0.0],
        critic_global_dim=1,
    )


def test_real_boundary_snapshot_binding_and_full_access_terminal() -> None:
    snapshot = build_bound_snapshot()
    assert isinstance(snapshot, BoundarySnapshot)
    assert all(isinstance(row, BoundaryMember) for row in snapshot.members)
    assert tuple(float(row.critic_member_features[0]) for row in snapshot.members) == (
        10.0,
        1.0,
        2.0,
        4.0,
    )

    binding = bind(snapshot)
    result = run_certificate()

    assert binding.token.physical_time == 41
    assert binding.token.membership == (
        ("protected", 7),
        ("bulk-1", 11),
        ("bulk-2", 13),
        ("bulk-3", 17),
    )
    assert binding.census_total == 17
    assert result["actual_binding"] == "BOUND_VARIABLE_ROSTER_SNAPSHOT_FULL_ACCESS"
    assert result["regime"] == "FULL_ACCESS"
    assert result["terminal"] == TERMINAL == "CENSUS_CONFORMANT_PRODUCTION_HT_RETIRED"
    assert result["sampler_dependency"] == {
        "name": "cheap_g0_pair_sampler",
        "commitment": "finite-pair-table/N3-m2/precommitted@1",
        "present": True,
        "active": False,
        "reason": "retired_on_full_access",
    }


def test_full_access_trace_is_complete_and_exactly_once() -> None:
    binding = bind()
    regime = resolve_access_regime(AccessFacts(True, True, True, True, True, True))
    session = AccessSession(binding, regime)

    assert session.exact_census(binding.token) == 17
    assert [(event.lifecycle_key, event.kind) for event in session.trace] == [
        ("protected", "protected_exact"),
        ("bulk-1", "bulk_exact"),
        ("bulk-2", "bulk_exact"),
        ("bulk-3", "bulk_exact"),
    ]
    session.trace.append(session.trace[-1])
    with pytest.raises(ClosureError, match="incomplete, duplicated, or out of order"):
        session.validate_trace()
    wrong_kind = AccessSession(binding, regime)
    assert wrong_kind.exact_census(binding.token) == 17
    wrong_kind.trace[-1] = replace(wrong_kind.trace[-1], kind="bulk_sampled")
    with pytest.raises(ClosureError, match="incomplete, duplicated, or out of order"):
        wrong_kind.validate_trace()


def test_sampling_trace_cannot_touch_unsampled_expensive_row() -> None:
    binding = bind()
    regime = resolve_access_regime(AccessFacts(True, False, True, True, False, True))
    session = AccessSession(binding, regime, selected_bulk=("bulk-1", "bulk-3"))

    assert session.sampled_reads(binding.token) == (Fraction(10), Fraction(1), Fraction(4))
    assert [(event.lifecycle_key, event.kind) for event in session.trace] == [
        ("protected", "protected_exact"),
        ("bulk-1", "bulk_sampled"),
        ("bulk-3", "bulk_sampled"),
    ]
    session.trace[-1] = replace(session.trace[-1], kind="bulk_exact")
    with pytest.raises(ClosureError, match="incomplete, duplicated, or out of order"):
        session.validate_trace()
    sentinel = AccessSession(binding, regime, selected_bulk=("bulk-1", "bulk-3"))
    with pytest.raises(ClosureError, match="unsampled expensive bulk access"):
        sentinel.expensive_bulk("bulk-2", binding.token)


def test_access_fork_truth_table_is_exhaustive() -> None:
    for values in product((False, True), repeat=6):
        facts = AccessFacts(*values)
        expected_full = values[0] and values[1] and values[4]
        expected_sample = values[0] and values[2] and values[3] and values[5] and not values[4]
        if expected_full:
            assert resolve_access_regime(facts) is AccessRegime.FULL_ACCESS
        elif expected_sample:
            assert resolve_access_regime(facts) is AccessRegime.SAMPLING_NEEDED
        else:
            with pytest.raises(ClosureError, match="unresolved access regime"):
                resolve_access_regime(facts)


def test_componentwise_resource_contract_is_immutable_and_fail_closed() -> None:
    assert R_MAX == ResourceVector(4, 3, 4)
    assert R_ALL == ResourceVector(4, 3, 4)
    assert R_SELECTED == ResourceVector(3, 2, 3)
    assert R_ALL.within(R_MAX)
    assert R_SELECTED.within(R_MAX)
    assert not R_ALL.within(ResourceVector(3, 3, 4))
    with pytest.raises(FrozenInstanceError):
        R_MAX.row_reads = 5  # type: ignore[misc]
    with pytest.raises(ClosureError, match="unresolved access regime"):
        resolve_access_regime(AccessFacts(True, True, True, True, False, False))


def test_uniform_positive_ht_expectation_and_variance_are_exact() -> None:
    design = pair_design((Fraction(1, 3),) * 3)
    pi_i, pi_ij = design.inclusion_probabilities()
    evidence = evaluate_design(design, POSITIVE)

    assert pi_i == {key: Fraction(2, 3) for key in BULK_KEYS}
    assert pi_ij["bulk-1", "bulk-1"] == Fraction(2, 3)
    assert pi_ij["bulk-1", "bulk-2"] == Fraction(1, 3)
    assert evidence.sample_totals == (Fraction(9, 2), Fraction(15, 2), Fraction(9))
    assert evidence.expectation == evidence.census_total == 7
    assert evidence.design_variance == evidence.covariance_variance == Fraction(7, 2)


def test_uniform_signed_ht_expectation_and_variance_are_exact() -> None:
    evidence = evaluate_design(pair_design((Fraction(1, 3),) * 3), SIGNED)

    assert evidence.sample_totals == (Fraction(0), Fraction(3, 2), Fraction(-3, 2))
    assert evidence.expectation == evidence.census_total == 0
    assert evidence.design_variance == evidence.covariance_variance == Fraction(3, 2)


def test_unequal_design_requires_member_specific_weights() -> None:
    design = pair_design((Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)))
    pi_i, pi_ij = design.inclusion_probabilities()
    evidence = evaluate_design(design, POSITIVE)

    assert pi_i == {
        "bulk-1": Fraction(5, 6),
        "bulk-2": Fraction(2, 3),
        "bulk-3": Fraction(1, 2),
    }
    assert pi_ij["bulk-1", "bulk-2"] == Fraction(1, 2)
    assert pi_ij["bulk-1", "bulk-3"] == Fraction(1, 3)
    assert pi_ij["bulk-2", "bulk-3"] == Fraction(1, 6)
    assert evidence.sample_totals == (Fraction(21, 5), Fraction(46, 5), Fraction(11))
    assert evidence.expectation == evidence.census_total == 7
    assert evidence.design_variance == evidence.covariance_variance == Fraction(41, 5)
    assert evidence.common_weight_expectation == Fraction(25, 4) != 7
    assert evidence.raw_expectation == Fraction(25, 6) != 7


def test_protected_row_is_exact_and_excluded_from_sampling() -> None:
    evidence = evaluate_design(
        pair_design((Fraction(1, 3),) * 3),
        POSITIVE,
        protected_value=Fraction(10),
    )

    assert evidence.expectation == evidence.census_total == 17
    assert evidence.design_variance == Fraction(7, 2)
    bad_design = FiniteDesign(
        ("protected", "bulk-1", "bulk-2"),
        (
            SampleOutcome(("protected", "bulk-1"), Fraction(1, 3)),
            SampleOutcome(("protected", "bulk-2"), Fraction(1, 3)),
            SampleOutcome(("bulk-1", "bulk-2"), Fraction(1, 3)),
        ),
    )
    with pytest.raises(ClosureError, match="protected row entered"):
        evaluate_design(
            bad_design,
            {"protected": Fraction(10), "bulk-1": Fraction(1), "bulk-2": Fraction(2)},
        )


@pytest.mark.parametrize(
    "probabilities",
    [
        (Fraction(1, 2), Fraction(1, 2), Fraction(0)),
        (Fraction(1, 2), Fraction(2, 3), Fraction(-1, 6)),
    ],
)
def test_nonpositive_inclusion_probabilities_fail_closed(probabilities) -> None:
    with pytest.raises(ClosureError, match="nonpositive or invalid pair"):
        pair_design(probabilities).inclusion_probabilities()


def test_missing_pair_and_wrong_frame_fail_closed() -> None:
    missing_pair = FiniteDesign(
        BULK_KEYS,
        (
            SampleOutcome(("bulk-1", "bulk-2"), Fraction(1, 2)),
            SampleOutcome(("bulk-1", "bulk-3"), Fraction(1, 2)),
        ),
    )
    with pytest.raises(ClosureError, match="first- and second-order"):
        missing_pair.inclusion_probabilities()
    with pytest.raises(ClosureError, match="bulk frame mismatched"):
        evaluate_design(
            pair_design((Fraction(1, 3),) * 3),
            {"bulk-1": Fraction(1), "bulk-2": Fraction(2)},
        )


def test_snapshot_churn_and_epoch_mutation_fail_closed() -> None:
    original = custom_snapshot()
    token = snapshot_token(original)
    for changed in (
        custom_snapshot(physical_time=42),
        custom_snapshot(bulk_1_epoch=12),
    ):
        with pytest.raises(ClosureError, match="snapshot token or membership epoch changed"):
            bind_snapshot(
                changed,
                protected_keys=("protected",),
                bulk_keys=BULK_KEYS,
                registry=FeatureAccess(),
                expected_token=token,
            )
    session = AccessSession(bind(original), AccessRegime.FULL_ACCESS)
    with pytest.raises(ClosureError, match="mixed or mutated snapshot token"):
        session.exact_census(snapshot_token(custom_snapshot(physical_time=42)))


def test_duplicate_missing_or_overlapping_membership_fails_closed() -> None:
    snapshot = custom_snapshot()
    with pytest.raises(ValueError, match="duplicate lifecycle keys"):
        BoundarySnapshot.make(
            physical_time=41,
            members=(snapshot.members[0], snapshot.members[0]),
            critic_global_features=[0.0],
            critic_global_dim=1,
        )
    with pytest.raises(ClosureError, match="registered sample frame"):
        bind_snapshot(
            snapshot,
            protected_keys=("protected",),
            bulk_keys=("bulk-1", "bulk-2", "missing"),
            registry=FeatureAccess(),
        )
    with pytest.raises(ClosureError, match="unique and disjoint"):
        bind_snapshot(
            snapshot,
            protected_keys=("protected",),
            bulk_keys=("bulk-1", "bulk-2", "protected"),
            registry=FeatureAccess(),
        )


def test_dtype_reduction_order_and_gradient_contract_fail_closed() -> None:
    normal = custom_snapshot()
    bad_member = BoundaryMember(
        lifecycle_key="bulk-1",
        membership_epoch=11,
        observation=np.asarray([0.0], dtype=np.float32),
        critic_member_features=np.asarray([1.0], dtype=np.float64),
    )
    bad_snapshot = BoundarySnapshot(
        physical_time=41,
        members=(normal.members[0], bad_member, normal.members[2], normal.members[3]),
        critic_global_features=np.asarray([0.0], dtype=np.float32),
    )
    with pytest.raises(ClosureError, match="one-dimensional float32"):
        bind(bad_snapshot)
    binding = bind(normal)
    with pytest.raises(ClosureError, match="mixed dtype or reduction order"):
        emulate_float32_census(binding, dtype="float64")
    with pytest.raises(ClosureError, match="mixed dtype or reduction order"):
        emulate_float32_census(binding, reduction_order="bulk_then_protected")
    with pytest.raises(ClosureError, match="feature access registry differs"):
        bind_snapshot(
            normal,
            protected_keys=("protected",),
            bulk_keys=BULK_KEYS,
            registry=replace(FeatureAccess(), gradient_mode="attached"),
        )


def test_bound_projection_is_immutable_after_source_array_mutation() -> None:
    snapshot = custom_snapshot()
    binding = bind(snapshot)
    snapshot.members[1].critic_member_features[0] = np.float32(99.0)

    assert binding.bulk[0].value == 1
    assert binding.census_total == 17
    with pytest.raises(FrozenInstanceError):
        binding.bulk[0].value = Fraction(99)  # type: ignore[misc]


def test_downstream_nonlinear_unbiased_label_is_rejected() -> None:
    validate_claim("linear_pretransform_total", unbiased=True)
    validate_claim("normalized_ratio", unbiased=False)
    with pytest.raises(ClosureError, match="forbidden downstream"):
        validate_claim("normalized_ratio", unbiased=True)


def test_canonical_candidate_bytes_are_stable_and_report_exact_values() -> None:
    first = canonical_bytes()
    second = canonical_bytes()
    result = run_certificate()

    assert first == second
    assert first.endswith(b"\n")
    assert result["census_total"] == "17"
    assert result["float32_census"] == 17.0
    assert result["fixtures"] == {
        "uniform_positive": {"expectation": "7", "variance": "7/2"},
        "uniform_signed": {"expectation": "0", "variance": "3/2"},
        "unequal": {
            "expectation": "7",
            "variance": "41/5",
            "common_weight_expectation": "25/4",
            "raw_expectation": "25/6",
        },
        "protected_exact": {"expectation": "17", "variance": "7/2"},
    }


def test_candidate_has_no_reverse_production_import() -> None:
    root = Path(__file__).resolve().parents[4]
    forbidden = ("experiments.candidates.roster_smf", "access_resource_certificate")
    production_files = tuple(
        path
        for family in ("ha_ctse_process", "envs", "scripts")
        for path in (root / family).rglob("*.py")
    )
    references = {
        str(path.relative_to(root)): term
        for path in production_files
        for term in forbidden
        if term in path.read_text(encoding="utf-8", errors="strict")
    }
    assert references == {}
