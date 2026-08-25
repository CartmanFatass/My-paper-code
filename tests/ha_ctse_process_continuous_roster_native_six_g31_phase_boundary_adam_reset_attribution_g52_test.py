from __future__ import annotations

import copy
import inspect

import pytest
import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_phase_boundary_adam_reset_attribution_g52
    as g52,
)


@pytest.fixture(scope="module")
def ready_source() -> tuple[object, torch.optim.Adam]:
    model, optimizer = g52.make_fresh_phase_A_ancestor(
        member_capacity=8, initialization_seed=10_521_000
    )
    g52.make_synthetic_boundary_state_for_readiness(model, optimizer, step=200)
    return model, optimizer


def _destination(source_model: object) -> tuple[object, torch.optim.Adam]:
    model = g52.g50.G50PhaseBProjection(source_model)  # type: ignore[arg-type]
    return model, g52.make_actor_adam(model)


def _synthetic_trajectory(model: object, *, reward_offset: float = 0.0) -> object:
    actor = model.policy  # type: ignore[attr-defined]
    time, environments, capacity = 48, 8, 8
    return g52.g47.G47ActorTrajectory(
        observations=torch.zeros(time, environments, capacity, actor.observation_dim),
        active_mask=torch.ones(time, environments, capacity, dtype=torch.bool),
        rewards=torch.linspace(-1.0, 1.0, time * environments).reshape(
            time, environments
        )
        + reward_offset,
        hidden_before=torch.zeros(
            time, environments, capacity, actor.hidden_dim
        ),
        terminal_hidden_reset_mask=None,
        pre_tanh_actions=torch.zeros(
            time, environments, capacity, actor.action_dim
        ),
        actions=torch.zeros(time, environments, capacity, actor.action_dim),
        old_log_probs=torch.zeros(time, environments, capacity),
    )


def test_identity_ancestry_inventory_and_common_ancestor(ready_source: tuple[object, torch.optim.Adam]) -> None:
    model, optimizer = ready_source
    assert g52.SOURCE_ID == f"{g52.ALGORITHM_ID}_P0"
    assert g52.ACCEPTED_ANCESTRY == (
        "G49_P0@8ecb01fd3ac0debf1b792e4e51293e07974d633b",
        "G50_P0@b8290699f5c10c593bbc21a6666c17950fae84d3",
        "G51_P0@ce6ed8659c480ca2779155b2871dc82b89fa0e95",
        "G52_P0",
    )
    assert g52.ARMS == (g52.RESET_ARM, g52.CARRY_ARM)
    assert type(model) is g52.g51.G51NoBaselinePhaseAProjection
    assert not hasattr(model, "credit_baselines")
    assert g52._parameter_names(model, g52.actor_parameters(model)) == g52.ACTOR_PARAMETER_NAMES
    assert len(g52.ACTOR_PARAMETER_NAMES) == 17
    assert all(float(optimizer.state[p]["step"]) == 200.0 for p in g52.actor_parameters(model))

    rng = torch.random.get_rng_state().clone()
    models, optimizers, boundary = g52.project_phase_B_arms(
        model, optimizer, completed_phase_A_updates=100, expected_step=200  # type: ignore[arg-type]
    )
    assert torch.equal(rng, torch.random.get_rng_state())
    assert boundary["passed"] is True
    assert boundary["actor_inventory_count"] == 17
    assert boundary["projected_actor_digests"][g52.RESET_ARM] == boundary["ancestor_actor_digest"]
    assert boundary["projected_actor_digests"][g52.CARRY_ARM] == boundary["ancestor_actor_digest"]
    assert not optimizers[g52.RESET_ARM].state
    assert len(optimizers[g52.CARRY_ARM].state) == 17
    assert g52.optimizer_hyperparameters(optimizers[g52.RESET_ARM]) == g52.optimizer_hyperparameters(
        optimizers[g52.CARRY_ARM]
    )
    assert not (g52._module_storage_ids(models[g52.RESET_ARM]) & g52._module_storage_ids(models[g52.CARRY_ARM]))


def test_exact_carry_install_and_all_fail_closed_modes(
    ready_source: tuple[object, torch.optim.Adam]
) -> None:
    model, optimizer = ready_source
    destination_model, destination_optimizer = _destination(model)
    rng = torch.random.get_rng_state().clone()
    installed = g52.install_carried_adam_state(
        source_model=model,  # type: ignore[arg-type]
        source_optimizer=optimizer,
        destination_model=destination_model,  # type: ignore[arg-type]
        destination_optimizer=destination_optimizer,
        expected_step=200,
    )
    assert installed["passed"] is True
    assert installed["source_state_digest"] == installed["installed_state_digest"]
    assert installed["install_optimizer_steps"] == 0
    assert installed["install_RNG_consumption"] == 0
    assert torch.equal(rng, torch.random.get_rng_state())

    parameters = g52.actor_parameters(model)  # type: ignore[arg-type]
    first = parameters[0]
    original_state = copy.deepcopy(optimizer.state[first])

    def rejects(reason: str | None = None) -> None:
        target, target_optimizer = _destination(model)
        match = None if reason is None else reason
        with pytest.raises(g52.G52InvariantError, match=match):
            g52.install_carried_adam_state(
                source_model=model,  # type: ignore[arg-type]
                source_optimizer=optimizer,
                destination_model=target,  # type: ignore[arg-type]
                destination_optimizer=target_optimizer,
                expected_step=200,
            )

    removed = optimizer.state.pop(first)
    rejects("missing_extra_or_foreign")
    optimizer.state[first] = removed

    foreign = torch.nn.Parameter(torch.zeros(1))
    optimizer.state[foreign] = copy.deepcopy(original_state)
    rejects("missing_extra_or_foreign")
    optimizer.state.pop(foreign)

    group = optimizer.param_groups[0]["params"]
    optimizer.param_groups[0]["params"] = list(reversed(group))
    rejects("reordered")
    optimizer.param_groups[0]["params"] = group

    cases = (
        ("exp_avg", torch.zeros(3), "shape"),
        ("exp_avg", torch.zeros_like(first, dtype=torch.float64), "dtype"),
        ("exp_avg", torch.empty_like(first, device="meta"), "device"),
        ("exp_avg", torch.full_like(first, float("nan")), "nonfinite"),
        ("step", torch.tensor(199.0), "step_invalid"),
    )
    for key, value, reason in cases:
        optimizer.state[first][key] = value
        rejects(reason)
        optimizer.state[first] = copy.deepcopy(original_state)

    optimizer.state[first].pop("exp_avg_sq")
    rejects("malformed")
    optimizer.state[first] = copy.deepcopy(original_state)

    optimizer.state[first]["exp_avg_sq"] = optimizer.state[first]["exp_avg"]
    rejects("shared_storage")
    optimizer.state[first] = copy.deepcopy(original_state)

    target, target_optimizer = _destination(model)
    target_optimizer.param_groups[0]["lr"] = 2e-3
    with pytest.raises(g52.G52InvariantError, match="hyperparameters"):
        g52.install_carried_adam_state(
            source_model=model,  # type: ignore[arg-type]
            source_optimizer=optimizer,
            destination_model=target,  # type: ignore[arg-type]
            destination_optimizer=target_optimizer,
            expected_step=200,
        )

    target, target_optimizer = _destination(model)
    target_optimizer.state[g52.actor_parameters(target)[0]] = copy.deepcopy(original_state)
    with pytest.raises(g52.G52InvariantError, match="not_empty"):
        g52.install_carried_adam_state(
            source_model=model,  # type: ignore[arg-type]
            source_optimizer=optimizer,
            destination_model=target,  # type: ignore[arg-type]
            destination_optimizer=target_optimizer,
            expected_step=200,
        )


def test_actual_adam_first_step_delta_certificate_and_tamper(
    ready_source: tuple[object, torch.optim.Adam]
) -> None:
    source_model, source_optimizer = ready_source
    models, optimizers, boundary = g52.project_phase_B_arms(
        source_model,  # type: ignore[arg-type]
        source_optimizer,
        completed_phase_A_updates=100,
        expected_step=200,
    )
    trajectory = _synthetic_trajectory(models[g52.RESET_ARM])
    update, certificate = g52.execute_first_phase_B_update(
        models,
        optimizers,
        trajectory,
        carry_install_evidence=boundary["CARRY_install"],
    )
    assert update["first_batch_materialized_before_either_step"] is True
    assert update["both_first_step_plans_materialized_before_either_step"] is True
    assert update["first_step_actor_batch_target_gradient_equal"] is True
    assert update["optimizer_steps_per_arm"] == 2
    assert g52.validate_boundary_activation_certificate(certificate)
    assert certificate["valid"] is True
    assert certificate["active"] is True
    assert certificate["norms"]["q_r"] > 0.0
    assert certificate["predicates"]["post_step_bytes_differ"] is True
    assert certificate["boundary_operationally_valid"] is True
    assert certificate["scientifically_valid"] is True
    post_state = certificate["post_step_optimizer_state"]
    assert post_state[g52.RESET_ARM]["expected_step"] == 1
    assert set(post_state[g52.RESET_ARM]["step_values"].values()) == {1}
    assert post_state[g52.CARRY_ARM]["expected_step"] == 201
    assert set(post_state[g52.CARRY_ARM]["step_values"].values()) == {201}
    assert post_state[g52.RESET_ARM]["state_digest"] != post_state[g52.CARRY_ARM]["state_digest"]
    assert certificate["predicates"]["post_step_optimizer_storage_disjoint"] is True

    tampered = copy.deepcopy(certificate)
    tampered["norms"]["q_r"] = 0.0
    assert not g52.validate_boundary_activation_certificate(tampered)
    tampered = copy.deepcopy(certificate)
    tampered["parameter_names"] = tampered["parameter_names"][:-1]
    assert not g52.validate_boundary_activation_certificate(tampered)
    tampered = copy.deepcopy(certificate)
    tampered["assigned_gradient_digests"][g52.CARRY_ARM] = "0" * 64
    assert not g52.validate_boundary_activation_certificate(tampered)


def test_q_r_edge_rules_and_inactive_branch_predicate() -> None:
    zero = (torch.zeros(2),)
    ratio = g52.activation_ratio(zero, zero)
    assert ratio == {
        "valid": True,
        "reason": None,
        "reset_norm": 0.0,
        "carry_norm": 0.0,
        "numerator": 0.0,
        "denominator": 0.0,
        "q_r": 0.0,
    }
    assert g52.activation_ratio((torch.tensor([float("nan")]),), zero)["valid"] is False
    assert g52.activation_ratio((), ())["valid"] is False

    ancestor, ancestor_optimizer = g52.make_fresh_phase_A_ancestor(
        member_capacity=8, initialization_seed=10_521_111
    )
    g52.make_synthetic_boundary_state_for_readiness(ancestor, ancestor_optimizer, step=20)
    models, optimizers, boundary = g52.project_phase_B_arms(
        ancestor, ancestor_optimizer, completed_phase_A_updates=10, expected_step=20
    )
    g52.make_synthetic_boundary_state_for_readiness(
        models[g52.RESET_ARM], optimizers[g52.RESET_ARM], step=1
    )
    for parameter in g52.actor_parameters(models[g52.CARRY_ARM]):
        optimizers[g52.CARRY_ARM].state[parameter]["step"].fill_(21.0)
    evidence = {
        g52.RESET_ARM: g52.inspect_post_step_adam_state(
            arm=g52.RESET_ARM, model=models[g52.RESET_ARM],
            optimizer=optimizers[g52.RESET_ARM], expected_step=1,
        ),
        g52.CARRY_ARM: g52.inspect_post_step_adam_state(
            arm=g52.CARRY_ARM, model=models[g52.CARRY_ARM],
            optimizer=optimizers[g52.CARRY_ARM], expected_step=21,
        ),
    }
    pre = g52._actor_rows(models[g52.RESET_ARM])
    certificate = g52.build_boundary_activation_certificate(
        pre_step_rows=pre,
        post_step_rows={
            arm: tuple(row.clone() for row in pre)
            for arm in g52.ARMS
        },
        batch_digest="1" * 64,
        target_digest="2" * 64,
        normalized_target_digest="3" * 64,
        assigned_gradient_digests={arm: "4" * 64 for arm in g52.ARMS},
        reset_empty_state=True,
        carry_state_digest=boundary["CARRY_install"]["installed_state_digest"],
        carried_state_finite_nonzero=True,
        post_step_optimizer_state=evidence,
        post_step_optimizer_storage_disjoint=True,
        carry_boundary_step=20,
    )
    assert g52.validate_boundary_activation_certificate(certificate)
    assert certificate["boundary_operationally_valid"] is True
    assert certificate["scientifically_valid"] is False
    assert certificate["valid"] is False
    assert certificate["active"] is False
    assert certificate["norms"]["q_r"] == 0.0


def test_post_step_nonfinite_adam_state_is_sealed_scientific_invalidity() -> None:
    ancestor, ancestor_optimizer = g52.make_fresh_phase_A_ancestor(
        member_capacity=8, initialization_seed=10_521_222
    )
    g52.make_synthetic_boundary_state_for_readiness(ancestor, ancestor_optimizer, step=200)
    models, optimizers, boundary = g52.project_phase_B_arms(
        ancestor, ancestor_optimizer, completed_phase_A_updates=100, expected_step=200
    )
    trajectory = _synthetic_trajectory(models[g52.RESET_ARM])
    actor_trajectory = g52.g47._actor_only_trajectory_view(trajectory)
    normalized = g52.g49._normalize_single(g52.g49._single_immediate_target(actor_trajectory.rewards))
    pre = g52._actor_rows(models[g52.RESET_ARM])
    plans = {arm: g52.g49._single_probe(models[arm], actor_trajectory, normalized.normalized) for arm in g52.ARMS}
    gradients = {arm: g52._named_tensor_digest(g52.ACTOR_PARAMETER_NAMES, plans[arm].assigned) for arm in g52.ARMS}
    for arm in g52.ARMS:
        g52.g49._apply_pass(models[arm], optimizers[arm], plans[arm].assigned)
    first_parameter = g52.actor_parameters(models[g52.CARRY_ARM])[0]
    optimizers[g52.CARRY_ARM].state[first_parameter]["exp_avg_sq"].fill_(float("inf"))
    evidence = {
        g52.RESET_ARM: g52.inspect_post_step_adam_state(
            arm=g52.RESET_ARM, model=models[g52.RESET_ARM], optimizer=optimizers[g52.RESET_ARM], expected_step=1
        ),
        g52.CARRY_ARM: g52.inspect_post_step_adam_state(
            arm=g52.CARRY_ARM, model=models[g52.CARRY_ARM], optimizer=optimizers[g52.CARRY_ARM], expected_step=201
        ),
    }
    certificate = g52.build_boundary_activation_certificate(
        pre_step_rows=pre,
        post_step_rows={arm: g52._actor_rows(models[arm]) for arm in g52.ARMS},
        batch_digest=g52._trajectory_digest(actor_trajectory),
        target_digest=g52._tensor_digest(normalized.target),
        normalized_target_digest=g52._tensor_digest(normalized.normalized),
        assigned_gradient_digests=gradients,
        reset_empty_state=True,
        carry_state_digest=boundary["CARRY_install"]["installed_state_digest"],
        carried_state_finite_nonzero=True,
        post_step_optimizer_state=evidence,
        post_step_optimizer_storage_disjoint=True,
        carry_boundary_step=200,
    )
    assert g52.validate_boundary_activation_certificate(certificate)
    assert evidence[g52.CARRY_ARM]["predicates"]["state_finite"] is False
    assert certificate["boundary_operationally_valid"] is False
    assert certificate["scientifically_valid"] is False
    assert certificate["active"] is False


def test_later_updates_are_arm_specific_and_no_forced_trajectory_equality() -> None:
    ancestor, ancestor_optimizer = g52.make_fresh_phase_A_ancestor(
        member_capacity=8, initialization_seed=10_521_444
    )
    g52.make_synthetic_boundary_state_for_readiness(ancestor, ancestor_optimizer, step=200)
    models, optimizers, _ = g52.project_phase_B_arms(
        ancestor, ancestor_optimizer, completed_phase_A_updates=100, expected_step=200
    )
    reset_trajectory = _synthetic_trajectory(models[g52.RESET_ARM])
    carry_trajectory = _synthetic_trajectory(models[g52.CARRY_ARM])
    carry_trajectory.rewards.copy_(carry_trajectory.rewards.square())
    record = g52.optimize_phase_B_update(
        models,
        optimizers,
        {g52.RESET_ARM: reset_trajectory, g52.CARRY_ARM: carry_trajectory},
        update_index=1,
    )
    assert record["separate_on_policy_collection"] is True
    assert record["paired_exogenous_assignments_only"] is True
    assert record["forced_common_actions_or_trajectories"] is False
    assert record["optimizer_steps_per_arm"] == 2
    for pass_record in record["records"]:
        assert pass_record["arm_specific_trajectory_digests"][g52.RESET_ARM] != pass_record["arm_specific_trajectory_digests"][g52.CARRY_ARM]
        assert pass_record["arm_specific_target_digests"][g52.RESET_ARM] != pass_record["arm_specific_target_digests"][g52.CARRY_ARM]


def test_exact_costs_search_ceiling_and_claim_limits() -> None:
    nonformal = g52.static_configuration_certificate(formal=False)
    formal = g52.static_configuration_certificate(formal=True)
    assert (nonformal["training_real_transitions"], nonformal["evaluation_real_transitions"]) == (
        11_136,
        6_912,
    )
    assert (nonformal["total_real_transitions"], nonformal["optimizer_steps"], nonformal["bootstrap_resamples"]) == (
        18_048,
        60,
        250,
    )
    assert (formal["training_real_transitions"], formal["evaluation_real_transitions"]) == (
        344_448,
        165_888,
    )
    assert (formal["total_real_transitions"], formal["optimizer_steps"], formal["bootstrap_resamples"]) == (
        510_336,
        1_800,
        10_000,
    )
    assert nonformal["hard_ceiling"] == {
        "total_real_transitions": 22_272,
        "optimizer_steps": 80,
        "bootstrap_resamples": 250,
        "wall_clock_seconds": 1_200,
    }
    assert formal["hard_ceiling"] == {
        "total_real_transitions": 626_688,
        "optimizer_steps": 2_400,
        "bootstrap_resamples": 10_000,
        "wall_clock_seconds": 28_800,
    }
    for row in (nonformal, formal):
        assert row["H"] == 48
        assert row["K_search"] == 0
        assert row["hypothetical_trajectory_count"] == 0
        assert row["hypothetical_transitions"] == 0
        assert row["nested_rollout"] is False
        assert row["replanning"] is False
    assert "component" in g52.CLAIM_CEILINGS[g52.RESET_ADVANTAGE_RESULT]
    assert "broader transport" in g52.CLAIM_CEILINGS[g52.PERSISTENT_SUFFICIENT_RESULT]


def test_training_real_transition_formula_subtracts_one_shared_phase_b_batch_per_root() -> None:
    batch_transitions = g52.NUM_ENVS * g52.HORIZON
    for formal, roots, phase_a, phase_b in (
        (False, 1, 10, 10),
        (True, 3, 100, 100),
    ):
        certificate = g52.static_configuration_certificate(formal=formal)
        shared_batch_count = roots * (phase_a + 2 * phase_b - 1)
        old_double_count = roots * (phase_a + 2 * phase_b) * batch_transitions
        assert certificate["training_real_transitions"] == shared_batch_count * batch_transitions
        assert old_double_count - certificate["training_real_transitions"] == roots * batch_transitions
        assert certificate["optimizer_steps"] == roots * (phase_a + 2 * phase_b) * g52.PPO_PASSES
