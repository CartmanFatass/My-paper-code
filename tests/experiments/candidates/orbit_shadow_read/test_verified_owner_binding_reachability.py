from __future__ import annotations

from dataclasses import fields, replace
import inspect
import json
import math

import pytest

from experiments.candidates.orbit_shadow_read import (
    verified_owner_binding_reachability as a2,
)


def _valid_fixture():
    fixture = a2.build_fixture()
    outcomes = tuple(
        a2.verify_owner_binding(certificate, fixture.trust_store, fixture.expectation)
        for certificate in fixture.valid_certificates
    )
    return fixture, outcomes


def _evaluate_pair(actor_input, jointly_relabelled_actor_input, model, permuted, context):
    return a2.evaluate_route_cell(
        actor_input=actor_input,
        clone=a2.restore_route_clone(model, context),
        jointly_relabelled_actor_input=jointly_relabelled_actor_input,
        jointly_permuted_clone=a2.restore_route_clone(permuted, context),
    )


def test_verified_view_binds_distinct_opaque_owners_to_identical_content():
    fixture, outcomes = _valid_fixture()
    first, second = outcomes

    assert fixture.valid_certificates[0].statement == fixture.valid_certificates[1].statement
    assert first.view.status is second.view.status is a2.VerificationStatus.VALID
    assert first.quarantine is second.quarantine is None
    assert first.view.epoch == second.view.epoch == fixture.expectation.epoch
    assert first.view.payload_digest == second.view.payload_digest
    assert first.view.source_snapshot_digest == second.view.source_snapshot_digest
    assert first.view.opaque_owner_handle != second.view.opaque_owner_handle
    assert a2.OPAQUE_HANDLE_PATTERN.fullmatch(first.view.opaque_owner_handle)
    assert a2.OPAQUE_HANDLE_PATTERN.fullmatch(second.view.opaque_owner_handle)
    assert len(first.view.opaque_owner_handle) == len(second.view.opaque_owner_handle)
    assert first.view.as_tuple() == (
        a2.VerificationStatus.VALID,
        first.view.opaque_owner_handle,
        fixture.expectation.epoch,
        fixture.expectation.payload_digest,
        fixture.expectation.source_snapshot_digest,
    )


@pytest.mark.parametrize(
    ("cause", "expected_reason"),
    (
        ("trust", a2.InvalidReason.UNTRUSTED_PRINCIPAL),
        ("authorization", a2.InvalidReason.UNAUTHORIZED_PRINCIPAL),
        ("signature", a2.InvalidReason.INVALID_SIGNATURE),
        ("schema", a2.InvalidReason.SCHEMA_MISMATCH),
        ("epoch", a2.InvalidReason.EPOCH_MISMATCH),
        ("payload_digest", a2.InvalidReason.PAYLOAD_DIGEST_MISMATCH),
        ("source_snapshot_digest", a2.InvalidReason.SOURCE_SNAPSHOT_DIGEST_MISMATCH),
    ),
)
def test_every_invalid_cause_is_all_bottom_and_quarantines_payload(cause, expected_reason):
    fixture = a2.build_fixture()
    certificate, trust_store = a2.invalid_certificate_for(cause, fixture)
    outcome = a2.verify_owner_binding(certificate, trust_store, fixture.expectation)

    assert outcome.view.as_tuple() == (
        a2.VerificationStatus.INVALID,
        a2.BOTTOM,
        a2.BOTTOM,
        a2.BOTTOM,
        a2.BOTTOM,
    )
    assert outcome.quarantine is not None
    assert outcome.quarantine.reason is expected_reason
    assert outcome.quarantine.payload == certificate.statement.payload
    with pytest.raises(ValueError, match="all bottom"):
        a2.VerifiedOwnerBindingView(
            a2.VerificationStatus.INVALID,
            "obh_" + "0" * 32,
            a2.BOTTOM,
            a2.BOTTOM,
            a2.BOTTOM,
        )


def test_actor_boundary_contains_no_raw_authentication_or_lookup_identifiers():
    actor_fields = {item.name for item in fields(a2.ActorInput)}
    forbidden = {
        "certificate",
        "signature",
        "key_id",
        "certificate_digest",
        "trust_store_index",
        "cache_address",
        "internal_id",
        "payload",
        "principal_id",
    }
    assert actor_fields.isdisjoint(forbidden)
    assert tuple(inspect.signature(a2.zero_path_owner_bypass).parameters) == (
        "current_state",
        "action_space",
    )


def test_principal_swap_is_identical_outside_handle_slice_and_nulls_are_invariant():
    fixture, outcomes = _valid_fixture()
    model = a2.build_model(tuple(outcome.view.opaque_owner_handle for outcome in outcomes))
    handles = tuple(outcome.view.opaque_owner_handle for outcome in outcomes)
    permuted = a2.permute_owner_aliases_and_embedding_rows(model, handles[::-1])
    context = a2.build_frozen_context()
    tolerance = a2.freeze_tolerances()

    by_route = {}
    for route in a2.Route:
        route_inputs = tuple(
            a2.build_actor_input(
                view=outcome.view,
                route=route,
                role=0,
                context=context,
                model=model,
            )
            for outcome in outcomes
        )
        assert route_inputs[0].nonprincipal_tensor == route_inputs[1].nonprincipal_tensor
        assert route_inputs[0].nonprincipal_bytes() == route_inputs[1].nonprincipal_bytes()
        relabelled_inputs = tuple(
            a2.build_actor_input(
                view=replace(
                    outcome.view,
                    opaque_owner_handle=handles[1 - index],
                ),
                route=route,
                role=0,
                context=context,
                model=permuted,
            )
            for index, outcome in enumerate(outcomes)
        )
        by_route[route] = tuple(
            _evaluate_pair(item, relabelled_inputs[index], model, permuted, context)
            for index, item in enumerate(route_inputs)
        )

    assert by_route[a2.Route.CANDIDATE][0].owner_slice != by_route[a2.Route.CANDIDATE][1].owner_slice
    for route in (a2.Route.OWNER_BLIND, a2.Route.VALIDITY_ONLY):
        assert by_route[route][0].owner_slice == by_route[route][1].owner_slice
        assert by_route[route][0].logits == by_route[route][1].logits
        assert by_route[route][0].kernel == by_route[route][1].kernel
    assert tolerance.observations_before_freeze == 0


def test_invalid_routes_fail_closed_to_exact_current_state_only_bypass():
    fixture = a2.build_fixture()
    certificate, trust_store = a2.invalid_certificate_for("signature", fixture)
    outcome = a2.verify_owner_binding(certificate, trust_store, fixture.expectation)
    context = a2.build_frozen_context()
    handles = tuple(
        a2.verify_owner_binding(item, fixture.trust_store, fixture.expectation)
        .view.opaque_owner_handle
        for item in fixture.valid_certificates
    )
    model = a2.build_model(handles)
    permuted = a2.permute_owner_aliases_and_embedding_rows(model, handles[::-1])
    expected = a2.zero_path_owner_bypass(context.current_state, context.action_space)

    for route in a2.Route:
        actor_input = a2.build_actor_input(
            view=outcome.view,
            route=route,
            role=1,
            context=context,
            model=model,
        )
        jointly_relabelled_actor_input = a2.build_actor_input(
            view=outcome.view,
            route=route,
            role=1,
            context=context,
            model=permuted,
        )
        record = _evaluate_pair(
            actor_input,
            jointly_relabelled_actor_input,
            model,
            permuted,
            context,
        )
        assert record.logits == expected.logits
        assert record.kernel == expected.kernel
        assert record.legal_actions == context.action_space.actions
        assert record.used_zero_path is True
        assert record.joint_alias_permutation_output_equal is True


def test_owner_residual_is_normalized_zero_main_effect_and_alias_row_permutation_invariant():
    fixture, outcomes = _valid_fixture()
    handles = tuple(outcome.view.opaque_owner_handle for outcome in outcomes)
    model = a2.build_model(handles)
    context = a2.build_frozen_context()

    for handle in handles:
        rows = tuple(a2.owner_by_role_residual(model, handle, role) for role in (0, 1))
        assert all(math.isclose(math.sqrt(sum(value * value for value in row)), 1.0) for row in rows)
        assert tuple(0.5 * (rows[0][i] + rows[1][i]) for i in range(len(rows[0]))) == (
            0.0,
            0.0,
            0.0,
        )

    permuted = a2.permute_owner_aliases_and_embedding_rows(model, handles[::-1])
    for principal_index, outcome in enumerate(outcomes):
        original = a2.build_actor_input(
            view=outcome.view,
            route=a2.Route.CANDIDATE,
            role=1,
            context=context,
            model=model,
        )
        relabeled_view = replace(
            outcome.view,
            opaque_owner_handle=handles[1 - principal_index],
        )
        relabeled = a2.build_actor_input(
            view=relabeled_view,
            route=a2.Route.CANDIDATE,
            role=1,
            context=context,
            model=permuted,
        )
        assert original.owner_slice == relabeled.owner_slice
        evaluated = _evaluate_pair(original, relabeled, model, permuted, context)
        assert evaluated.joint_alias_permutation_output_equal is True


def test_regression_reporting_clone_id_cannot_feed_the_evaluator():
    """A P0/P1-encoded ID would be a sufficient synthetic owner channel."""

    assert "clone_id" not in {item.name for item in fields(a2.RouteClone)}
    assert "principal_label" not in {item.name for item in fields(a2.RouteClone)}
    assert tuple(inspect.signature(a2.evaluate_route_cell).parameters) == (
        "actor_input",
        "clone",
        "jointly_relabelled_actor_input",
        "jointly_permuted_clone",
    )

    def wrong_logits_from_reporting_id(reporting_id):
        return (1.0, -1.0, 0.0) if "-P1-" in reporting_id else (-1.0, 1.0, 0.0)

    assert wrong_logits_from_reporting_id("candidate-P0-R0") != (
        wrong_logits_from_reporting_id("candidate-P1-R0")
    )

    fixture, outcomes = _valid_fixture()
    handles = tuple(outcome.view.opaque_owner_handle for outcome in outcomes)
    model = a2.build_model(handles)
    permuted = a2.permute_owner_aliases_and_embedding_rows(model, handles[::-1])
    context = a2.build_frozen_context()
    original = a2.build_actor_input(
        view=outcomes[0].view,
        route=a2.Route.CANDIDATE,
        role=0,
        context=context,
        model=model,
    )
    relabelled = a2.build_actor_input(
        view=replace(outcomes[0].view, opaque_owner_handle=handles[1]),
        route=a2.Route.CANDIDATE,
        role=0,
        context=context,
        model=permuted,
    )
    evaluation = _evaluate_pair(original, relabelled, model, permuted, context)
    p0_record = a2._attach_reporting_identity(
        evaluation,
        route=a2.Route.CANDIDATE,
        principal_label="P0",
        role=0,
        reporting_clone_id="candidate-P0-R0",
        valid=True,
    )
    p1_record = a2._attach_reporting_identity(
        evaluation,
        route=a2.Route.CANDIDATE,
        principal_label="P1",
        role=0,
        reporting_clone_id="candidate-P1-R0",
        valid=True,
    )
    assert p0_record.logits == p1_record.logits == evaluation.logits
    assert p0_record.kernel == p1_record.kernel == evaluation.kernel


@pytest.mark.parametrize(
    ("changes", "expected"),
    (
        ({"invalid_control": False}, a2.Branch.A2_INVALID_CONTROL),
        ({"owner_alias_consumed": False}, a2.Branch.A2_OWNER_ALIAS_NOT_CONSUMED),
        ({"logit_estimand_defined": False}, a2.Branch.A2_NO_LOGIT_ESTIMAND),
        ({"candidate_logit_reachable": False}, a2.Branch.A2_NO_LOGIT_ESTIMAND),
        ({"invalid_fallback_exact": False}, a2.Branch.A2_FAIL_OPEN_INVALID),
        ({"controlled_path": False}, a2.Branch.A2_LEAKAGE_OR_UNCONTROLLED_PATH),
        ({"comparator_invariant": False}, a2.Branch.A2_GENERIC_PROVENANCE_GATE),
        ({"owner_main_effect_zero": False}, a2.Branch.A2_OWNER_MAIN_EFFECT_ONLY),
        ({"candidate_kernel_reachable": False}, a2.Branch.A2_LOGIT_REACHABILITY_ONLY),
        ({}, a2.Branch.A2_OWNER_BINDING_REACHES_FIRST_ACTION_KERNEL),
    ),
)
def test_branch_precedence_is_exact_and_fail_closed(changes, expected):
    witnesses = a2.BranchWitnesses(
        invalid_control=True,
        owner_alias_consumed=True,
        logit_estimand_defined=True,
        invalid_fallback_exact=True,
        controlled_path=True,
        comparator_invariant=True,
        owner_main_effect_zero=True,
        candidate_logit_reachable=True,
        candidate_kernel_reachable=True,
    )
    assert a2.select_branch(replace(witnesses, **changes)) is expected


def test_registered_audit_is_deterministic_branch_nine_and_uses_exactly_fifteen_cells():
    first = a2.run_verified_owner_binding_audit()
    second = a2.run_verified_owner_binding_audit()

    assert first.branch is a2.Branch.A2_OWNER_BINDING_REACHES_FIRST_ACTION_KERNEL
    assert first.route_cell_calls == 15
    assert first.environment_transitions == 0
    assert first.learner_calls == first.trainer_calls == first.optimizer_updates == 0
    assert first.return_evaluations == first.model_fits == 0
    assert len(first.records) == 15
    assert len({record.clone_id for record in first.records}) == 15
    assert all(first.witnesses.as_dict().values())
    assert first.to_bytes() == second.to_bytes()
    payload = json.loads(first.to_bytes())
    assert payload["branch_precedence"] == [branch.value for branch in a2.Branch]
    assert payload["branch"] == a2.Branch.A2_OWNER_BINDING_REACHES_FIRST_ACTION_KERNEL.value
