"""Proof-sized isolated technical fixtures for VSP06-A2."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.candidates.vsp_06_mssr import selected_p_causal_generic_null as a2


def _complete_evidence() -> dict[str, object]:
    evidence: dict[str, object] = {
        name: True for name in a2.REQUIRED_BOOLEAN_EVIDENCE
    }
    evidence.update(
        {
            "selected_p_raw_logit_effect": 0.2,
            "selected_p_centered_logit_effect": 0.2,
            "selected_p_kernel_effect": 0.05,
            "decoy_kernel_error": 0.0,
            "current_rebuild_error": 0.1,
            "generic_compiler_error": 0.0,
            "tolerance": a2.FLOAT32_SCALED_TOLERANCE,
        }
    )
    return evidence


def test_authoritative_seven_branch_precedence_is_exact_and_fail_closed() -> None:
    evidence = _complete_evidence()
    assert a2.classify_audit(evidence) == a2.CAUSAL_GENERIC_COMPILES
    assert a2.classify_audit({}) == a2.INVALID

    invalid = dict(evidence, provenance_authenticated=False)
    moved_selected_p = dict(evidence, decoy_selected_p_fixed=False)
    authenticated_decoy = dict(evidence, decoy_carriers_unauthenticated=False)
    action_null = dict(evidence, selected_p_raw_logit_effect=0.0)
    decoy = dict(evidence, decoy_kernel_error=0.01)
    logit_only = dict(
        evidence,
        selected_p_centered_logit_effect=0.0,
        selected_p_kernel_effect=0.0,
    )
    mixed_logit_only = dict(
        evidence,
        selected_p_centered_logit_effect=0.2,
        selected_p_kernel_effect=0.0,
    )
    current = dict(evidence, current_rebuild_error=0.0)
    generic = dict(evidence, generic_compiler_error=0.01)

    assert a2.classify_audit(invalid) == a2.INVALID
    assert a2.classify_audit(moved_selected_p) == a2.INVALID
    assert a2.classify_audit(authenticated_decoy) == a2.INVALID
    assert a2.classify_audit(action_null) == a2.ACTION_NULL
    assert a2.classify_audit(decoy) == a2.DECOY_SENSITIVE
    assert a2.classify_audit(logit_only) == a2.LOGIT_ONLY
    assert a2.classify_audit(mixed_logit_only) == a2.LOGIT_ONLY
    assert a2.classify_audit(current) == a2.CURRENT_REBUILD_COMPILES
    assert a2.classify_audit(generic) == a2.GENERIC_COMPILER_FAILS

    # Earlier branches dominate later defects.
    assert (
        a2.classify_audit(dict(invalid, selected_p_raw_logit_effect=0.0))
        == a2.INVALID
    )
    assert (
        a2.classify_audit(dict(action_null, decoy_kernel_error=0.01))
        == a2.ACTION_NULL
    )
    assert (
        a2.classify_audit(dict(decoy, current_rebuild_error=0.0))
        == a2.DECOY_SENSITIVE
    )
    assert (
        a2.classify_audit(dict(logit_only, current_rebuild_error=0.0))
        == a2.LOGIT_ONLY
    )
    assert (
        a2.classify_audit(
            dict(
                mixed_logit_only,
                current_rebuild_error=0.0,
                generic_compiler_error=0.01,
            )
        )
        == a2.LOGIT_ONLY
    )
    assert (
        a2.classify_audit(dict(current, generic_compiler_error=0.01))
        == a2.CURRENT_REBUILD_COMPILES
    )


def _generic_input(label: str, p: str) -> a2.GenericInput:
    return a2.GenericInput(
        X="same-full-current-X",
        P=p,
        provenance=f"authenticated-{label}",
        recurrence="same-recurrence",
        legal_mask="all-legal",
        sampled_order=("owner",),
        production_path="mssr_joint_spf_pre_recurrence_v1",
    )


def test_equal_information_generic_compiler_exactly_compiles_finite_mapping() -> None:
    left = _generic_input("left", "negative-P")
    right = _generic_input("right", "positive-P")
    left_logits = np.asarray([0.25, -0.25, 0.0], dtype=np.float32)
    right_logits = np.asarray([-0.25, 0.25, 0.0], dtype=np.float32)
    compiler = a2.GenericFiniteCompiler(support_cardinality=2, action_dimension=3)
    compiler.compile(((left, left_logits), (right, right_logits)))

    assert compiler.scalar_capacity == 6
    assert compiler.compiled_scalar_count == 6
    assert compiler.reserved_scalar_capacity == 0
    assert np.array_equal(compiler(left), left_logits)
    assert np.array_equal(compiler(right), right_logits)

    unseen = replace(right, provenance="unauthenticated")
    with pytest.raises(a2.AuditContractError, match="unseen information"):
        compiler(unseen)


def test_generic_compiler_rejects_unmatched_capacity_and_duplicate_information() -> None:
    left = _generic_input("left", "negative-P")
    logits = np.zeros(3, dtype=np.float32)
    compiler = a2.GenericFiniteCompiler(support_cardinality=2, action_dimension=3)
    with pytest.raises(a2.AuditContractError, match="support capacity"):
        compiler.compile(((left, logits),))
    with pytest.raises(a2.AuditContractError, match="duplicated"):
        compiler.compile(((left, logits), (left, logits)))
    with pytest.raises(a2.AuditContractError, match="scalar capacity"):
        a2.GenericFiniteCompiler(
            support_cardinality=2, action_dimension=3, scalar_capacity=5
        )


def test_tolerance_and_activity_budget_are_predeclared_not_observation_fit() -> None:
    assert a2.FLOAT32_SCALED_TOLERANCE == (
        a2.TOLERANCE_MULTIPLIER * np.finfo(np.float32).eps
    )
    assert a2.REGISTERED_PRODUCTION_KERNEL_CALLS == 10
    assert a2.REGISTERED_PRODUCTION_KERNEL_CALLS <= a2.MAX_PRODUCTION_KERNEL_CALLS


def test_weight_freeze_digest_covers_actor_and_critic() -> None:
    class Owner:
        commitment_model = torch.nn.Linear(2, 2)
        event_critic = torch.nn.Linear(2, 1)

    owner = Owner()
    baseline = a2._owner_weight_digest(owner)
    with torch.no_grad():
        owner.event_critic.bias.add_(1.0)
    assert a2._owner_weight_digest(owner) != baseline


def _technical_history() -> a2.HistoryInput:
    next_p = float(np.clip(0.2 * 0.25, -1.0, 1.0))
    return a2.HistoryInput(
        label="left",
        context_hex="",
        context={},
        selected_p_hex="technical-selected-p",
        selected_p=torch.as_tensor([[np.float32(next_p)]], dtype=torch.float32),
        provenance={
            "episode_id": 60809,
            "owner_lifecycle_key": a2.a1.OWNER,
            "membership_epoch": 0,
            "partner_lifecycle_key": a2.a1.HISTORICAL_SOURCE,
            "event_index": 0,
            "prior_p": 0.0,
            "payload": 0.25,
            "next_p": next_p,
            "writer_policy_version": 0,
        },
        accepted_logits=np.zeros(3, dtype=np.float32),
        accepted_probabilities=np.full(3, 1.0 / 3.0, dtype=np.float32),
        accepted_action=0,
    )


def test_decoy_perturbs_real_unselected_carrier_with_selected_p_fixed() -> None:
    history = _technical_history()
    baseline = a2._make_unauthenticated_decoy(
        history,
        value=np.float32(-0.125),
        carrier_id="same-unselected-carrier",
    )
    perturbed = a2._make_unauthenticated_decoy(
        history,
        value=np.float32(0.125),
        carrier_id="same-unselected-carrier",
    )
    selected_before, trace_before = a2._select_p_at_production_boundary(
        history, baseline
    )
    selected_after, trace_after = a2._select_p_at_production_boundary(
        history, perturbed
    )

    assert torch.equal(selected_before, history.selected_p)
    assert torch.equal(selected_after, history.selected_p)
    assert trace_before["selected_p_digest"] == trace_after["selected_p_digest"]
    assert (
        trace_before["selected_provenance_digest"]
        == trace_after["selected_provenance_digest"]
    )
    assert (
        trace_before["unselected_payload_digest"]
        != trace_after["unselected_payload_digest"]
    )
    assert trace_before["unselected_authenticated"] is False
    assert trace_after["unselected_authenticated"] is False
    assert trace_before["unselected_selected"] is False
    assert trace_after["unselected_selected"] is False


def test_decoy_selection_fails_closed_if_unauthenticated_carrier_is_selected() -> None:
    history = _technical_history()
    decoy = a2._make_unauthenticated_decoy(
        history,
        value=np.float32(0.125),
        carrier_id="unselected-carrier",
    )
    with pytest.raises(a2.AuditContractError, match="marked selected"):
        a2._select_p_at_production_boundary(history, replace(decoy, selected=True))


def test_registered_audit_fails_before_factory_or_kernel_on_wrong_a1_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid receipt reached production factory/kernel")

    monkeypatch.setattr(a2.a1, "_factory_triplet", forbidden)
    with pytest.raises(a2.AuditContractError, match="accepted A1"):
        a2.registered_audit({"raw_output_binding": "wrong"})
