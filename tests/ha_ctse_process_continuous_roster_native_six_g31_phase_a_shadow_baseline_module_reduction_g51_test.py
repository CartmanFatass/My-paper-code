from __future__ import annotations

import copy
import inspect
import json

import pytest
import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51
    as g51,
)


def test_static_projection_optimizer_factorization_and_inductive_checkpoint() -> None:
    accepted_null = g51.g50.make_phase_A_models(
        member_capacity=8, initialization_seed=10_501_000
    )[g51.g50.NULL_ARM]
    models = g51.make_phase_A_models(member_capacity=8, initialization_seed=10_501_000)
    optimizers = g51.make_phase_A_optimizers(models)

    reference = models[g51.REFERENCE_ARM]
    reduced = models[g51.REDUCED_ARM]
    assert hasattr(reference, "credit_baselines")
    assert not hasattr(reduced, "credit_baselines")
    assert hasattr(reduced, "slow_critic")
    assert g51.g40.state_bytes(reference.slow_critic) == g51.g40.state_bytes(
        reduced.slow_critic
    )
    assert reference.phase == accepted_null.phase == "fast"
    assert g51.g40.state_bytes(reference) == g51.g40.state_bytes(accepted_null)
    assert tuple(
        (name, parameter.requires_grad)
        for name, parameter in reference.named_parameters()
    ) == tuple(
        (name, parameter.requires_grad)
        for name, parameter in accepted_null.named_parameters()
    )
    assert "critic_state" not in inspect.signature(g51.g47._actor_only_step).parameters

    boundary = g51.phase_A_boundary_audit(models, optimizers)
    assert boundary["passed"] is True, boundary
    assert boundary["projection_RNG_consumption"] == 0
    assert boundary["only_phase_A_module_and_state_delta_is_credit_baselines"] is True
    assert boundary["slow_critic_state_bytes_equal"] is True
    assert boundary["slow_critic_trainable_masks_equal"] is True
    assert boundary["reference_optimizer_parameter_names"] == (
        boundary["actor_parameter_names"] + boundary["reference_baseline_parameter_names"]
    )
    assert boundary["reduced_optimizer_parameter_names"] == boundary["actor_parameter_names"]

    static = g51.reconstruct_static_certificate(models, optimizers)
    assert g51.validate_static_certificate(static), static
    assert all(value == 0 for value in static["static_predicates"].values())
    assert static["optimizer_predicates"]["actual_kernel_witness_required"] is True
    assert "actor_Adam_state_factorized" not in static["optimizer_predicates"]
    assert static["reference_baseline_forward_audit"]["RNG_change_count"] == 0
    assert static["reference_baseline_forward_audit"]["buffer_mutation_count"] == 0

    path_tamper = copy.deepcopy(static)
    path_tamper["path_identities"]["reference_plan"]["code_digest"] = "0" * 64
    assert not g51.validate_static_certificate(path_tamper)

    forward_tamper = copy.deepcopy(static)
    forward_tamper["reference_baseline_forward_audit"]["RNG_change_count"] = 1
    assert not g51.validate_static_certificate(forward_tamper)

    projected, projection = g51.project_phase_B_models(
        models, completed_phase_A_updates=1
    )
    phase_B_optimizers = g51.make_phase_B_optimizers(projected)
    assert all(not optimizer.state for optimizer in phase_B_optimizers.values())
    checkpoints = g51.build_final_checkpoints(
        projected,
        phase_B_optimizers,
        source_commit="a" * 40,
        completed_phase_A_updates=1,
        completed_phase_B_updates=0,
        phase_boundary_evidence=projection,
    )
    assert g51.validate_checkpoint_pair(checkpoints)
    reduced_checkpoint = checkpoints[g51.REDUCED_ARM]
    assert "algorithm_id" not in reduced_checkpoint
    assert "source_id" not in reduced_checkpoint
    assert "arm" not in reduced_checkpoint
    assert not g51._contains_reduced_residue(reduced_checkpoint)
    certificate = g51.build_inductive_equality_certificate(
        phase_A_evidence=None,
        phase_boundary_evidence=projection,
        checkpoints=checkpoints,
    )
    assert not g51.validate_inductive_equality_certificate(certificate)
    assert certificate["D_G51"] == 1
    assert g51.classify_result(
        {
            "static_certificate": static,
            "inductive_equality_certificate": certificate,
        }
    ) == g51.NUMERICALLY_UNRESOLVED_RESULT

    extra_nested = copy.deepcopy(checkpoints)
    extra_nested[g51.REDUCED_ARM]["phase_A_projection_evidence"][
        "innocuous_extra"
    ] = 0
    assert not g51.validate_checkpoint_pair(extra_nested)

    forbidden_value = copy.deepcopy(checkpoints)
    forbidden_value[g51.REDUCED_ARM]["phase_A_projection_evidence"][
        "retained_actor_bytes_equal"
    ] = "credit_baselines.synthetic"
    assert not g51.validate_checkpoint_pair(forbidden_value)

    extra_source = copy.deepcopy(checkpoints)
    extra_source[g51.REDUCED_ARM]["source"]["innocuous_extra"] = 0
    assert not g51.validate_checkpoint_pair(extra_source)


def test_identity_result_order_and_zero_phase_B_structural_helper() -> None:
    assert g51.RESULT_BRANCHES == (
        g51.INVALID_RESULT,
        g51.COUPLING_RESULT,
        g51.EXACT_RESULT,
        g51.NUMERICALLY_UNRESOLVED_RESULT,
    )
    with pytest.raises(ValueError, match="actual 8x48 trajectory"):
        g51.build_structural_witness(None)  # type: ignore[arg-type]

    update_source = inspect.getsource(g51.optimize_phase_A_update)
    assert "reference_baseline_optimizer_steps" not in update_source
    assert "reference_baseline_Adam_step_count" not in update_source
    assert "reference_baseline_parameter_Adam_exposures" in update_source
    assert "reference_baseline_parameter_Adam_exposure_count" in update_source
    assert '"total_optimizer_steps": 2 * PPO_PASSES' in update_source
    assert '"phase_B_optimizer_steps": 0' in update_source

    models = g51.make_phase_A_models(
        member_capacity=8, initialization_seed=10_501_000
    )
    optimizers = g51.make_phase_A_optimizers(models)
    static_only = g51.reconstruct_static_certificate(models, optimizers)
    assert g51.classify_result(static_only) == g51.NUMERICALLY_UNRESOLVED_RESULT

    coupling = {"static_certificate": copy.deepcopy(static_only)}
    coupling["static_certificate"]["static_predicates"][  # type: ignore[index]
        "baseline_output_read_into_actor_credit"
    ] = 1
    coupling["static_certificate"]["passed"] = False  # type: ignore[index]
    assert g51.classify_result(coupling) == g51.COUPLING_RESULT

    caller_authored_zero = {
        "static_certificate": static_only,
        "D_G51": 0,
    }
    assert g51.classify_result(caller_authored_zero) == (
        g51.NUMERICALLY_UNRESOLVED_RESULT
    )

    numerical_envelope = g51.build_result_evidence_envelope(caller_authored_zero)
    assert g51.validate_result_evidence_envelope(numerical_envelope)
    assert numerical_envelope["result"] == g51.NUMERICALLY_UNRESOLVED_RESULT
    assert numerical_envelope["successful_exact_result"] is False
    json.loads(g51.serialize_diagnostics(numerical_envelope))

    coupling_envelope = g51.build_result_evidence_envelope(coupling)
    assert g51.validate_result_evidence_envelope(coupling_envelope)
    assert coupling_envelope["result"] == g51.COUPLING_RESULT
    assert coupling_envelope["failure_evidence"] is None

    numerical_failure = g51.G51InvariantError(
        "phase_A_actual_Adam_kernel_difference", {"pass_index": 0}
    )
    preserved_numerical = g51.build_result_evidence_envelope(
        {"static_certificate": static_only}, failure=numerical_failure
    )
    assert preserved_numerical["result"] == g51.NUMERICALLY_UNRESOLVED_RESULT
    assert preserved_numerical["failure_evidence"]["diagnostics"] == {
        "pass_index": 0
    }

    invalid_first = g51.build_result_evidence_envelope(
        {"static_certificate": static_only, "evidence_valid": False},
        failure=g51.G51InvariantError("localized_coupling", {"path": "x"}),
    )
    assert invalid_first["result"] == g51.INVALID_RESULT


def test_actual_phase_B_zero_step_G49_certificate_is_required_and_tamper_closed() -> None:
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        models = g51.make_phase_A_models(
            member_capacity=8, initialization_seed=10_501_000
        )
        trajectory = g51.g40.collect_g40_trajectory(
            models[g51.REFERENCE_ARM],
            episode_ids=range(8),
            ledger_seed=11_402_000,
            action_seed=11_403_000,
            device=torch.device("cpu"),
        )
        assessment = g51.assess_structural_witness(
            trajectory, source_commit="a" * 40
        )
        assert g51.validate_structural_assessment(assessment), assessment
        assert assessment["passed"] is True
        assert assessment["result_envelope"]["result"] == g51.EXACT_RESULT
        assert assessment["optimizer_ledger"] == {
            "reference_actor_steps": 2,
            "reduced_actor_steps": 2,
            "reference_baseline_parameter_Adam_exposures": 2,
            "reduced_baseline_parameter_Adam_exposures": 0,
            "completed_paired_passes": 2,
            "phase_B_steps": 0,
            "failure_detected_before_current_pair": False,
            "no_steps_after_detection": True,
        }
        phase_A = assessment["phase_A_update_evidence"]
        assert phase_A["actual_autograd_cross_gradient_evidence"]["all_zero"] is True
        assert phase_A["actual_kernel_Adam_equality"]["all_equal"] is True

        cross_tamper = copy.deepcopy(phase_A)
        cross_tamper["actual_autograd_cross_gradient_evidence"]["all_zero"] = False
        assert not g51.validate_phase_A_update_evidence(cross_tamper)

        kernel_tamper = copy.deepcopy(phase_A)
        kernel_tamper["actual_kernel_Adam_equality"]["all_equal"] = False
        assert not g51.validate_phase_A_update_evidence(kernel_tamper)
        boundary = assessment["phase_boundary_evidence"]
        zero_step = assessment["phase_B_zero_step_certificate"]
        assert g51.validate_phase_B_zero_step_certificate(zero_step), zero_step
        assert zero_step["phase_B_optimizer_steps"] == 0
        assert all(zero_step["predicates"].values())
        checkpoints = assessment["checkpoints"]
        missing = g51.build_inductive_equality_certificate(
            phase_A_evidence=phase_A,
            phase_boundary_evidence=boundary,
            checkpoints=checkpoints,
            phase_B_evidence=None,
        )
        assert missing["D_G51"] == 1
        assert not g51.validate_inductive_equality_certificate(missing)

        exact = g51.build_inductive_equality_certificate(
            phase_A_evidence=phase_A,
            phase_boundary_evidence=boundary,
            checkpoints=checkpoints,
            phase_B_evidence=zero_step,
        )
        assert g51.validate_inductive_equality_certificate(exact), exact
        assert exact["D_G51"] == 0

        predicate_tamper = copy.deepcopy(zero_step)
        predicate_tamper["predicates"]["actor_trace_equal"] = False
        assert not g51.validate_phase_B_zero_step_certificate(predicate_tamper)

        identity_tamper = copy.deepcopy(zero_step)
        identity_tamper["single_probe_identity"]["code_digest"] = "0" * 64
        assert not g51.validate_phase_B_zero_step_certificate(identity_tamper)

        normalization_tamper = copy.deepcopy(zero_step)
        normalization_tamper["normalized_digest"] = "0" * 64
        assert not g51.validate_phase_B_zero_step_certificate(normalization_tamper)
    finally:
        torch.set_num_threads(previous_threads)


def test_assessment_allowlist_ledgers_partial_rejection_and_forged_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models = g51.make_phase_A_models(
        member_capacity=8, initialization_seed=10_501_000
    )
    static = g51.reconstruct_static_certificate(
        models, g51.make_phase_A_optimizers(models)
    )

    def fail(reason: str, diagnostics: dict[str, object]) -> None:
        raise g51.G51InvariantError(reason, diagnostics)

    pre_error = {
        "pass_index": 0,
        "optimizer_ledger": g51._optimizer_ledger(
            paired_passes=0, failure_detected_before_current_pair=True
        ),
        "static_certificate": static,
        "comparison": {"baseline_loss_gradient_into_actor_count": 1},
    }
    monkeypatch.setattr(
        g51,
        "build_structural_witness",
        lambda *_args, **_kwargs: fail(
            "phase_A_pre_step_coupling_or_numeric_difference", pre_error
        ),
    )
    coupling = g51.assess_structural_witness(None)  # type: ignore[arg-type]
    assert g51.validate_structural_assessment(coupling)
    assert coupling["result_envelope"]["result"] == g51.COUPLING_RESULT
    assert coupling["optimizer_ledger"]["reference_actor_steps"] == 0
    assert coupling["optimizer_ledger"]["reduced_actor_steps"] == 0
    assert coupling["optimizer_ledger"]["failure_detected_before_current_pair"] is True

    post_error = {
        "pass_index": 0,
        "optimizer_ledger": g51._optimizer_ledger(
            paired_passes=1, failure_detected_before_current_pair=False
        ),
        "static_certificate": static,
        "comparison": {"actor_Adam_exp_avg_bytes_equal": False},
    }
    monkeypatch.setattr(
        g51,
        "build_structural_witness",
        lambda *_args, **_kwargs: fail(
            "phase_A_actual_Adam_kernel_difference", post_error
        ),
    )
    unresolved = g51.assess_structural_witness(None)  # type: ignore[arg-type]
    assert g51.validate_structural_assessment(unresolved)
    assert unresolved["result_envelope"]["result"] == (
        g51.NUMERICALLY_UNRESOLVED_RESULT
    )
    assert unresolved["optimizer_ledger"]["reference_actor_steps"] == 1
    assert unresolved["optimizer_ledger"]["reduced_actor_steps"] == 1
    assert unresolved["optimizer_ledger"]["failure_detected_before_current_pair"] is False

    invalid_static = copy.deepcopy(static)
    invalid_static["passed"] = False
    monkeypatch.setattr(
        g51,
        "build_structural_witness",
        lambda *_args, **_kwargs: fail(
            "static_certificate_failed_before_optimizer", invalid_static
        ),
    )
    invalid = g51.assess_structural_witness(None)  # type: ignore[arg-type]
    assert g51.validate_structural_assessment(invalid)
    assert invalid["result_envelope"]["result"] == g51.INVALID_RESULT
    assert invalid["optimizer_ledger"]["completed_paired_passes"] == 0

    partial = copy.deepcopy(pre_error)
    partial["optimizer_ledger"]["reference_actor_steps"] = 1
    monkeypatch.setattr(
        g51,
        "build_structural_witness",
        lambda *_args, **_kwargs: fail(
            "phase_A_pre_step_coupling_or_numeric_difference", partial
        ),
    )
    with pytest.raises(g51.G51InvariantError) as partial_error:
        g51.assess_structural_witness(None)  # type: ignore[arg-type]
    assert partial_error.value.reason == (
        "phase_A_pre_step_coupling_or_numeric_difference"
    )

    forged = copy.deepcopy(coupling)
    forged["result_envelope"]["result"] = g51.EXACT_RESULT
    assert not g51.validate_structural_assessment(forged)

    monkeypatch.setattr(
        g51,
        "build_structural_witness",
        lambda *_args, **_kwargs: fail("unknown_failure", {}),
    )
    with pytest.raises(g51.G51InvariantError, match="unknown_failure"):
        g51.assess_structural_witness(None)  # type: ignore[arg-type]
