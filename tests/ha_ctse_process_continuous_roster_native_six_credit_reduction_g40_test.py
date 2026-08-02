from __future__ import annotations

import copy

import pytest
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from envs.continuous_roster import runtime_capacity as roster_env


def _model() -> g40.G40NativeSixPolicy:
    return g40.make_model(8, initialization_seed=10_401_000)


def _state(parameters: tuple[torch.nn.Parameter, ...]) -> tuple[torch.Tensor, ...]:
    return tuple(row.detach().clone() for row in parameters)


def test_seed_law_is_exact_and_anchor_clone_inventory_is_byte_matched() -> None:
    assert g40.seed_block(2, formal=True) == {
        "anchor_model": 10_401_002,
        "anchor_ledger": 10_402_002,
        "anchor_action": 10_403_002,
        "branch_ledger": 10_404_002,
        "branch_action": 10_405_002,
        "branch_gradient_probe": 10_406_002,
        "evaluation_base_ledger": 10_407_002,
        "evaluation_process": 10_408_002,
        "evaluation_action": 10_409_002,
    }
    formal = g40.seed_block(0, formal=True)
    nonformal = g40.seed_block(0, formal=False)
    assert all(nonformal[name] - formal[name] == 900_000 for name in formal)
    assert g40.bootstrap_seed(formal=True) == 10_410_040
    assert g40.bootstrap_seed(formal=False) == 11_310_040

    anchor = _model()
    accepted_g39 = g40.g39.make_paired_models(
        8, initialization_seed=10_401_000
    )[g40.g39.NATIVE6_ARM]
    assert g40.state_bytes(anchor) == g40.state_bytes(accepted_g39)
    assert g40.baseline_inventory(anchor) == g40.baseline_inventory(accepted_g39)
    assert g40.state_bytes(anchor.credit_baselines) == g40.state_bytes(
        accepted_g39.credit_baselines
    )
    arms = g40.clone_anchor_models(anchor)
    for model in arms.values():
        model.begin_credit_branch_phase()
    optimizers = {
        **{
            f"{arm}:actor": torch.optim.Adam(
                model.actor_credit_parameters(), lr=1e-3
            )
            for arm, model in arms.items()
        },
        **{
            f"{arm}:critic": torch.optim.Adam(
                model.slow_critic_parameters(), lr=1e-3
            )
            for arm, model in arms.items()
        },
    }
    audit = g40.branch_boundary_audit(anchor, arms, optimizers)
    assert audit["passed"] is True, audit
    assert audit["model_state_bytes_equal"] is True
    assert audit["buffer_bytes_equal"] is True
    assert audit["log_std_equal"] is True
    assert audit["shared_tensor_storage_count"] == 0
    assert audit["baseline_semantic_keys_equal"] is True
    assert audit["baseline_state_shapes_equal"] is True
    assert audit["baseline_parameter_count_equal"] is True
    assert audit["baseline_initial_tensor_bytes_equal"] is True
    assert audit["baseline_state_bytes_equal"] is True
    assert audit["accepted_g39_initial_baseline_state_equal"] is True
    assert audit["shared_two_output_credit_baseline"] is True
    inventory = audit["inventory"]
    assert inventory[g40.G31_ARM] == inventory[g40.GAE1_ARM]
    assert inventory[g40.G31_ARM]["credit_baseline"][
        "shared_two_output_module"
    ] is True

    forged = g40.clone_anchor_models(anchor)
    for model in forged.values():
        model.begin_credit_branch_phase()
    with torch.no_grad():
        forged[g40.G31_ARM].credit_baselines[2].bias[0].add_(1.0)
    forged_optimizers = {
        **{
            f"{arm}:actor": torch.optim.Adam(
                model.actor_credit_parameters(), lr=1e-3
            )
            for arm, model in forged.items()
        },
        **{
            f"{arm}:critic": torch.optim.Adam(
                model.slow_critic_parameters(), lr=1e-3
            )
            for arm, model in forged.items()
        },
    }
    forged_audit = g40.branch_boundary_audit(
        anchor, forged, forged_optimizers
    )
    assert forged_audit["passed"] is False
    assert forged_audit["baseline_state_bytes_equal"] is False


def test_exact_returns_successor_targets_and_lambda_one_identity() -> None:
    rewards = torch.tensor([[1.0], [2.0], [3.0]])
    values = torch.tensor([[0.2], [0.3], [0.4]])
    immediate = torch.tensor([[0.1], [0.2], [0.3]])
    successor = torch.tensor([[0.4], [0.5], [0.6]])
    terminals = torch.tensor([[False], [False], [True]])
    credit = g40.compute_credit_targets(
        rewards=rewards,
        slow_values=values,
        immediate_baselines=immediate,
        successor_baselines=successor,
        terminals=terminals,
    )
    expected_returns = torch.tensor(
        [[1.0 + 0.99 * (2.0 + 0.99 * 3.0)], [2.0 + 0.99 * 3.0], [3.0]]
    )
    torch.testing.assert_close(credit.returns, expected_returns, rtol=0, atol=1e-6)
    torch.testing.assert_close(
        credit.successor_targets,
        torch.tensor([[2.0 + 0.99 * 3.0], [3.0], [0.0]]),
        rtol=0,
        atol=1e-6,
    )
    assert torch.equal(credit.gae1_advantage, credit.returns - values)
    assert credit.gae1_identity_error <= 1e-6
    assert credit.returns.requires_grad is False
    assert credit.successor_targets.requires_grad is False
    assert credit.gae1_advantage.requires_grad is False


def test_first_paired_8x48_branch_batch_closes_all_learning_signal_gates() -> None:
    anchor = _model()
    first_anchor = g40.collect_g40_trajectory(
        anchor,
        episode_ids=range(8),
        ledger_seed=10_402_000,
        action_seed=10_403_000,
        device=torch.device("cpu"),
    )
    assert g40.source_preflight_audit()["passed"] is True
    pre_common = g40.pre_common_gradient_audit(anchor, first_anchor)
    assert g40.validate_pre_common_gradient_audit(pre_common) is True
    forged = copy.deepcopy(pre_common)
    forged["centralized_slow_critic"]["gradient_norm"] = 0.0
    forged["centralized_slow_critic"]["live"] = False
    assert g40.validate_pre_common_gradient_audit(forged) is False
    arms = g40.clone_anchor_models(anchor)
    for model in arms.values():
        model.begin_credit_branch_phase()
    trajectories = {
        arm: g40.collect_g40_trajectory(
            model,
            episode_ids=range(8),
            ledger_seed=10_406_000,
            action_seed=10_406_000,
            device=torch.device("cpu"),
        )
        for arm, model in arms.items()
    }
    left, right = (trajectories[arm] for arm in g40.ARMS)
    match = g40.branch_trajectory_match(left, right)
    assert match["passed"] is True, match
    noise = torch.as_tensor(
        roster_env.make_action_noise(
            range(8), action_seed=10_406_000, member_capacity=8
        )[0]
    )
    forward = g40.branch_forward_match(
        arms[g40.G31_ARM],
        arms[g40.GAE1_ARM],
        observations=left.observations[0],
        active_mask=left.active_mask[0],
        critic_state=left.critic_states[0],
        sampling_noise=noise,
    )
    assert forward["passed"] is True, forward
    audit = g40.branch_gradient_audit(arms, trajectories)
    assert audit["passed"] is True, audit
    assert g40.validate_branch_gradient_audit(audit) is True
    assert max(audit["gae1_identity_errors"].values()) <= 1e-6
    assert audit["shadow_independence"]["diagnostic_optimizer_steps"] == 0


def test_shadow_losses_change_only_shadow_heads_and_not_ordinary_actor_or_critic() -> None:
    model = _model()
    model.begin_credit_branch_phase()
    trajectory = g40.collect_g40_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=10_406_000,
        action_seed=10_406_000,
        device=torch.device("cpu"),
    )
    enabled = copy.deepcopy(model)
    omitted = copy.deepcopy(model)
    enabled_actor_before = _state(enabled.full_actor_parameters())
    enabled_baseline_before = _state(tuple(enabled.credit_baselines.parameters()))
    omitted_baseline_before = _state(tuple(omitted.credit_baselines.parameters()))
    enabled_final_before = enabled.credit_baselines[2].weight.detach().clone()
    direct = model.credit_baselines(trajectory.critic_states)
    immediate, successor = model.baseline_values(trajectory.critic_states)
    assert torch.equal(immediate, direct[..., 0])
    assert torch.equal(successor, direct[..., 1])

    def update(row: g40.G40NativeSixPolicy, include: bool) -> dict[str, float]:
        return g40.optimize_credit_branch_update(
            g40.GAE1_ARM,
            row,
            torch.optim.Adam(row.actor_credit_parameters(), lr=1e-3),
            torch.optim.Adam(row.slow_critic_parameters(), lr=1e-3),
            trajectory,
            ppo_passes=2,
            include_shadow_losses=include,
        )

    enabled_metrics = update(enabled, True)
    omitted_metrics = update(omitted, False)
    assert enabled_metrics["gradient_clipping_applied"] == 0.0
    assert enabled_metrics["baseline_gradients_enter_direction_norm"] == 0.0
    assert enabled_metrics["advantage_normalization_count"] == 1.0
    assert enabled_metrics["advantage_recomputed_between_passes"] == 0.0
    assert all(
        torch.equal(left, right)
        for left, right in zip(
            enabled.full_actor_parameters(), omitted.full_actor_parameters()
        )
    )
    assert all(
        torch.equal(left, right)
        for left, right in zip(
            enabled.slow_critic_parameters(), omitted.slow_critic_parameters()
        )
    )
    assert any(
        not torch.equal(before, after)
        for before, after in zip(
            enabled_baseline_before, enabled.credit_baselines.parameters()
        )
    )
    enabled_final = enabled.credit_baselines[2].weight.detach()
    assert not torch.equal(enabled_final_before[0], enabled_final[0])
    assert not torch.equal(enabled_final_before[1], enabled_final[1])
    assert all(
        torch.equal(before, after)
        for before, after in zip(
            omitted_baseline_before, omitted.credit_baselines.parameters()
        )
    )
    assert any(
        not torch.equal(before, after)
        for before, after in zip(enabled_actor_before, enabled.full_actor_parameters())
    )


def test_collector_requires_the_registered_cpp_batch_without_python_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    class RejectedNativeBatch:
        def __init__(self, envs: object) -> None:
            calls.append(len(tuple(envs)))
            raise RuntimeError("native backend unavailable")

    monkeypatch.setattr(
        g40.g39.toy_cpp, "ContinuousRosterToyBatch", RejectedNativeBatch
    )
    with pytest.raises(RuntimeError, match="native backend unavailable"):
        g40.collect_g40_trajectory(
            _model(),
            episode_ids=(0,),
            ledger_seed=10_402_000,
            action_seed=10_403_000,
            device=torch.device("cpu"),
        )
    assert calls == [1]
    controls = g40.source_controls()
    assert controls["environment_backend"] == (
        "ContinuousRosterToyBatch_CPU_CPP_required"
    )
    assert controls["environment_backend_python_fallback"] is False
