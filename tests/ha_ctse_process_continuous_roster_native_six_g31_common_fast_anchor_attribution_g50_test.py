from __future__ import annotations

import copy
import inspect
import json

import pytest
import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_common_fast_anchor_attribution_g50 as g50,
)


def test_frozen_identity_seeds_and_inventory_are_exact() -> None:
    assert g50.ALGORITHM_ID == (
        "CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50"
    )
    assert g50.SOURCE_ID.endswith("_P0")
    assert g50.ARMS == (
        "FAST_ANCHOR_THEN_SINGLE_IMMEDIATE",
        "SINGLE_IMMEDIATE_FROM_INITIALIZATION",
    )
    assert g50.PHASE_A_OBJECTIVE_CONTRACT_ID == "G40_COMMON_NATIVE6_FAST_ANCHOR_V1"
    assert g50.PHASE_A_SOURCE_COMMIT == (
        "97a8b237e0cec6c2713dd2a710d324040fa3dfc2"
    )
    assert g50.PHASE_B_SOURCE_COMMIT == (
        "8ecb01fd3ac0debf1b792e4e51293e07974d633b"
    )
    formal = g50.seed_block(2, formal=True)
    nonformal = g50.seed_block(0, formal=False)
    assert formal["initialization"] == 10_501_002
    assert formal["evaluation_action"] == 10_510_002
    assert nonformal["initialization"] == 11_401_000
    assert nonformal["phase_B_gradient_probe"] == 11_407_000
    assert g50.seed_block(2, formal=False)["initialization"] == 11_401_002
    assert len(
        {g50.seed_block(index, formal=False)["initialization"] for index in range(3)}
    ) == 3
    assert g50.bootstrap_seed(formal=False) == 11_411_050

    exercise = g50.static_configuration_certificate(formal=False)
    assert exercise["training_transitions"] == 15_360
    assert exercise["evaluation_transitions"] == 6_912
    assert exercise["total_real_transitions"] == 22_272
    assert exercise["optimizer_steps"] == 80
    assert exercise["bootstrap_resamples"] == 250
    formal_config = g50.static_configuration_certificate(formal=True)
    assert formal_config["training_transitions"] == 460_800
    assert formal_config["evaluation_transitions"] == 165_888
    assert formal_config["total_real_transitions"] == 626_688
    assert formal_config["optimizer_steps"] == 2_400
    assert formal_config["bootstrap_resamples"] == 10_000


def test_phase_A_q_A_zero_nonfinite_and_strict_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    zero = g50.phase_A_activation((torch.zeros(2),), (torch.zeros(2),))
    assert zero["q_A"] == 0.0
    assert zero["treatment_active"] is False

    active = g50.phase_A_activation(
        (torch.tensor([1.0], dtype=torch.float64),),
        (torch.tensor([0.5], dtype=torch.float64),),
    )
    assert active["q_A"] == 0.5
    assert active["treatment_active"] is True
    assert active["actual_null_activation_evidence_read_count"] == 0

    values = iter((1.0, 1.0, g50.ACTIVATION_TOLERANCE))
    monkeypatch.setattr(g50, "_global_norm", lambda _rows: next(values))
    exact = g50.phase_A_activation((torch.ones(1),), (torch.ones(1),))
    assert exact["q_A"] == g50.ACTIVATION_TOLERANCE
    assert exact["treatment_active"] is False

    with pytest.raises(g50.G50InvariantError, match="nonfinite"):
        g50.phase_A_activation((torch.tensor([float("nan")]),), (torch.zeros(1),))


def test_phase_A_complete_graph_boundary_and_phase_B_physical_deletion() -> None:
    models = g50.make_phase_A_models(
        member_capacity=8, initialization_seed=10_501_000
    )
    optimizers = g50.make_phase_A_optimizers(models)
    boundary = g50.phase_A_boundary_audit(models, optimizers)
    assert boundary["passed"] is True
    assert boundary["phase_A_model_class"] == "G40NativeSixPolicy"
    for arm in g50.ARMS:
        model = models[arm]
        assert hasattr(model, "credit_baselines")
        assert hasattr(model, "slow_critic")
        assert hasattr(model.policy, "critic")
        assert hasattr(model.policy, "delayed_residual")
        assert tuple(optimizers[arm].param_groups[0]["params"]) == (
            model.actor_credit_parameters()
        )
        assert not optimizers[arm].state

    projected, certificates = g50.project_phase_B_models(
        models, completed_phase_A_updates=10
    )
    phase_B_optimizers = g50.make_phase_B_optimizers(projected)
    for arm in g50.ARMS:
        model = projected[arm]
        assert certificates[arm]["passed"] is True
        assert not hasattr(model, "credit_baselines")
        assert not hasattr(model, "slow_critic")
        assert not hasattr(model.policy, "critic")
        assert not hasattr(model.policy, "delayed_residual")
        assert not phase_B_optimizers[arm].state
        assert tuple(phase_B_optimizers[arm].param_groups[0]["params"]) == (
            model.full_actor_parameters()
        )
    reference_pointers = {
        parameter.untyped_storage().data_ptr()
        for parameter in projected[g50.REFERENCE_ARM].parameters()
    }
    null_pointers = {
        parameter.untyped_storage().data_ptr()
        for parameter in projected[g50.NULL_ARM].parameters()
    }
    assert reference_pointers.isdisjoint(null_pointers)


def test_phase_B_deleted_residual_dispatch_is_exact_and_executable() -> None:
    phase_A = g50.make_phase_A_models(
        member_capacity=8, initialization_seed=10_501_000
    )
    projected, certificates = g50.project_phase_B_models(
        phase_A, completed_phase_A_updates=10
    )

    for arm in g50.ARMS:
        source_actor = phase_A[arm].policy
        model = projected[arm]
        actor = model.policy
        assert isinstance(actor, g50.G50PhaseBActor)
        assert not hasattr(actor, "delayed_residual")
        assert certificates[arm]["policy_delayed_residual_deleted"] is True

        candidate = torch.linspace(-0.4, 0.4, actor.hidden_dim).reshape(1, -1)
        prefix = torch.tensor([[0.2, -0.1]], dtype=candidate.dtype)
        observation = torch.linspace(
            -0.3, 0.3, actor.observation_dim, dtype=candidate.dtype
        ).reshape(1, -1)
        expected = source_actor._action_mean_for_member(
            candidate=candidate,
            prefix_fraction=prefix,
            observation=observation,
        )
        actual = actor._action_mean_for_member(
            candidate=candidate,
            prefix_fraction=prefix,
            observation=observation,
        )
        assert torch.equal(actual, expected)

        step = g50.g47._actor_only_step(
            model,
            observations=torch.zeros((1, 8, actor.observation_dim)),
            active_mask=torch.ones((1, 8), dtype=torch.bool),
            hidden=torch.zeros((1, 8, actor.hidden_dim)),
            deterministic=True,
        )
        assert torch.isfinite(step.actions).all()
        assert tuple(step.actions.shape) == (1, 8, actor.action_dim)


def test_final_checkpoint_exact_schema_reload_and_residue_tamper_guards() -> None:
    models = g50.make_phase_A_models(
        member_capacity=8, initialization_seed=10_501_000
    )
    projected, certificates = g50.project_phase_B_models(
        models, completed_phase_A_updates=10
    )
    optimizers = g50.make_phase_B_optimizers(projected)
    arm = g50.REFERENCE_ARM
    for parameter in projected[arm].full_actor_parameters():
        optimizers[arm].state[parameter] = {
            "step": torch.tensor(20.0),
            "exp_avg": torch.zeros_like(parameter),
            "exp_avg_sq": torch.zeros_like(parameter),
        }
    checkpoint = g50.build_final_checkpoint(
        model=projected[arm],
        optimizer=optimizers[arm],
        source_commit="a" * 40,
        formal=False,
        replicate=0,
        arm=arm,
        completed_phase_A_updates=10,
        completed_phase_B_updates=10,
        configuration=g50.static_configuration_certificate(formal=False),
        seeds=g50.seed_block(0, formal=False),
        disposal_certificate=certificates[arm],
    )
    assert g50.validate_final_checkpoint(checkpoint)
    reloaded = g50.load_phase_B_checkpoint_model(checkpoint, member_capacity=6)
    assert not hasattr(reloaded, "credit_baselines")
    assert not hasattr(reloaded.policy, "critic")

    extra = copy.deepcopy(checkpoint)
    extra["legacy"] = {"phase_A_optimizer": "compatibility"}
    assert not g50.validate_final_checkpoint(extra)

    residue = copy.deepcopy(checkpoint)
    residue["actor_state"]["policy.critic.weight"] = torch.zeros(1)
    assert not g50.validate_final_checkpoint(residue)

    intermediate = copy.deepcopy(checkpoint)
    intermediate["kind"] = "phase_A_intermediate"
    assert not g50.validate_final_checkpoint(intermediate)


def test_activation_inventory_and_order_swap_guard_are_reconstructed() -> None:
    active_record = {
        "replicate": 0,
        "pass_records": [{"activation": {"treatment_active": True}}],
    }
    conclusion = g50.build_phase_A_conclusion_evidence(
        [active_record], formal=False
    )
    assert g50.validate_phase_A_conclusion_evidence(conclusion)
    assert conclusion["active_phase_A_pass_by_replicate"] == {"0": True}
    serialized = json.loads(json.dumps(conclusion, allow_nan=False))
    assert serialized == conclusion
    assert g50.validate_phase_A_conclusion_evidence(serialized)
    tampered = copy.deepcopy(conclusion)
    tampered["active_phase_A_pass_by_replicate"]["0"] = False
    assert not g50.validate_phase_A_conclusion_evidence(tampered)

    integer_keyed = copy.deepcopy(conclusion)
    integer_keyed["active_phase_A_pass_by_replicate"] = {0: True}
    assert not g50.validate_phase_A_conclusion_evidence(integer_keyed)

    formal_records = [
        {
            "replicate": replicate,
            "pass_records": [{"activation": {"treatment_active": True}}],
        }
        for replicate in (0, 1, 2)
    ]
    formal = g50.build_phase_A_conclusion_evidence(formal_records, formal=True)
    assert formal["active_phase_A_pass_by_replicate"] == {
        "0": True,
        "1": True,
        "2": True,
    }
    assert g50.validate_phase_A_conclusion_evidence(
        json.loads(json.dumps(formal, allow_nan=False))
    )

    implementation = inspect.getsource(g50.phase_A_order_swap_guard)
    assert "tuple(reversed(ARMS))" in implementation
    assert "optimizer_steps\": 0" in implementation
    assert ".step(" not in implementation


def test_null_shadow_read_certificate_and_phase_A_planning_are_fail_closed() -> None:
    assert g50.NULL_READ_CERTIFICATE == {
        "baseline_read_into_null_actor_advantage": 0,
        "baseline_read_into_null_actor_gradient": 0,
        "baseline_read_into_null_action_or_logprob": 0,
        "baseline_read_into_null_checkpoint_selection": 0,
        "baseline_read_into_null_evaluation": 0,
        "baseline_read_into_null_result_selection": 0,
    }
    implementation = inspect.getsource(g50.optimize_phase_A_update)
    assert "plans =" in implementation
    assert implementation.index("plans =") < implementation.index("_assign_and_step(")
    assert "reference_raw_counterfactual" in implementation
    assert "actual_null_activation_evidence_read_count" in inspect.getsource(
        g50.phase_A_activation
    )
