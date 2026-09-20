from __future__ import annotations

import copy
import math

import pytest
import torch

from experiments.candidates.team_conditioned_termination.policy import (
    MaskPolicy,
    PPOUpdater,
    RolloutBatch,
    ValueCritic,
    compute_gae,
)


def _state(module: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().clone() for name, value in module.state_dict().items()}


def _configure_prefix_probe(policy: MaskPolicy) -> None:
    """Make the second logit respond only to the first realized prefix bit."""

    prefix_zero_index = policy.context_dim + policy.n_agents
    with torch.no_grad():
        for parameter in policy.actor.parameters():
            parameter.zero_()
        policy.actor.initial_logit.zero_()
        policy.actor.body[0].weight[0, prefix_zero_index] = 1.0
        policy.actor.body[2].weight[0, 0] = 1.0
        policy.actor.logit_head.weight[0, 0] = 2.0


def test_paired_initialization_probability_and_private_sampling_rng() -> None:
    torch.manual_seed(91)
    before_initialization = torch.get_rng_state().clone()
    joint = MaskPolicy(4, 3, "joint", hidden_size=8, seed=701)
    independent = MaskPolicy(4, 3, "independent", hidden_size=8, seed=701)
    assert torch.equal(torch.get_rng_state(), before_initialization)
    assert joint.context_dim == independent.context_dim == 4
    assert joint.n_agents == independent.n_agents == 3
    assert joint.hidden_size == independent.hidden_size == 8
    for name, value in joint.state_dict().items():
        torch.testing.assert_close(value, independent.state_dict()[name], rtol=0, atol=0)

    context = torch.randn(32, 4)
    eligible = torch.ones(32, 3, dtype=torch.bool)
    forced = torch.zeros_like(eligible)
    actions = torch.zeros_like(eligible)
    evaluation = joint.evaluate_actions(context, eligible, forced, actions)
    torch.testing.assert_close(
        torch.sigmoid(evaluation.logits),
        torch.full_like(evaluation.logits, 0.1),
        rtol=1e-6,
        atol=1e-7,
    )

    before_sampling = torch.get_rng_state().clone()
    joint_sample = joint.sample(context, eligible, forced)
    independent_sample = independent.sample(context, eligible, forced)
    assert torch.equal(torch.get_rng_state(), before_sampling)
    assert torch.equal(joint_sample.actions, independent_sample.actions)
    torch.testing.assert_close(joint_sample.log_prob, independent_sample.log_prob)


def test_initialization_does_not_call_all_device_manual_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_manual_seed(_seed: int) -> None:
        raise AssertionError("module initialization must not reseed all devices")

    monkeypatch.setattr(torch, "manual_seed", forbidden_manual_seed)
    policy = MaskPolicy(2, 2, "joint", hidden_size=4, seed=702)
    critic = ValueCritic(2, hidden_size=4, seed=703)
    assert policy.context_dim == critic.context_dim == 2


def test_one_team_log_probability_credits_every_eligible_keep_and_end() -> None:
    policy = MaskPolicy(2, 4, "joint", hidden_size=8, seed=5)
    context = torch.zeros(1, 2)
    eligible = torch.tensor([[True, True, False, True]])
    forced = torch.tensor([[False, False, True, False]])
    actions = torch.tensor([[False, True, True, False]])
    result = policy.evaluate_actions(context, eligible, forced, actions)
    expected = 2.0 * math.log(0.9) + math.log(0.1)
    torch.testing.assert_close(
        result.log_prob, torch.tensor([expected]), rtol=1e-6, atol=1e-7
    )
    expected_entropy = -0.1 * math.log(0.1) - 0.9 * math.log(0.9)
    torch.testing.assert_close(
        result.entropy,
        torch.tensor([3.0 * expected_entropy]),
        rtol=1e-6,
        atol=1e-7,
    )
    # The forced END has a finite diagnostic log probability but contributes
    # exactly zero to the one team actor likelihood.
    assert torch.isfinite(result.bit_log_prob).all()
    changed_forced_diagnostic = result.bit_log_prob.clone()
    changed_forced_diagnostic[:, 2] = 1e30
    reconstructed = torch.where(
        eligible, changed_forced_diagnostic, torch.zeros_like(changed_forced_diagnostic)
    ).sum(-1)
    torch.testing.assert_close(reconstructed, result.log_prob)


def test_undefined_forced_diagnostic_cannot_enter_actor_reduction() -> None:
    class AgentSpecificDiagnostic(torch.nn.Module):
        def forward(self, features: torch.Tensor) -> torch.Tensor:
            # Identity starts after the one context feature.  Agent zero's raw
            # diagnostic is deliberately undefined; agent one remains finite.
            is_agent_zero = features[:, 1].bool()
            return torch.where(
                is_agent_zero,
                torch.full_like(features[:, 0], float("nan")),
                torch.zeros_like(features[:, 0]),
            )

    policy = MaskPolicy(1, 2, "joint", hidden_size=4, seed=11)
    policy.actor = AgentSpecificDiagnostic()
    context = torch.zeros(1, 1)
    eligible = torch.tensor([[False, True]])
    forced = torch.tensor([[True, False]])
    actions = torch.tensor([[True, False]])
    result = policy.evaluate_actions(context, eligible, forced, actions)
    assert torch.isnan(result.logits[0, 0])
    assert torch.isfinite(result.log_prob).all()
    assert torch.isfinite(result.entropy).all()

    active = torch.tensor([[True, False]])
    no_forcing = torch.zeros_like(active)
    with pytest.raises(FloatingPointError, match="active policy logits"):
        policy.evaluate_actions(context, active, no_forcing, torch.zeros_like(active))


def test_joint_uses_realized_forced_prefix_while_independent_zeros_it() -> None:
    joint = MaskPolicy(1, 3, "joint", hidden_size=4, seed=3)
    independent = MaskPolicy(1, 3, "independent", hidden_size=4, seed=3)
    _configure_prefix_probe(joint)
    _configure_prefix_probe(independent)
    context = torch.zeros(1, 1)
    eligible = torch.tensor([[False, True, False]])
    forced = torch.tensor([[True, False, False]])
    actions = torch.tensor([[True, False, False]])

    joint_eval = joint.evaluate_actions(context, eligible, forced, actions)
    independent_eval = independent.evaluate_actions(context, eligible, forced, actions)
    assert joint_eval.logits[0, 1] > 0.0
    assert independent_eval.logits[0, 1] == 0.0
    assert joint_eval.log_prob[0] < independent_eval.log_prob[0]
    # No future action can leak backward through teacher forcing.
    alternate = actions.clone()
    alternate[:, 2] = True
    with pytest.raises(ValueError, match="outside eligibility"):
        joint.evaluate_actions(context, eligible, forced, alternate)


def test_sampling_replays_the_stored_whole_mask_exactly() -> None:
    policy = MaskPolicy(3, 4, "joint", hidden_size=8, seed=22)
    _configure_prefix_probe(policy)
    context = torch.zeros(6, 3)
    eligible = torch.tensor(
        [[False, True, True, True], [True, True, False, True]] * 3,
        dtype=torch.bool,
    )
    forced = torch.tensor(
        [[True, False, False, False], [False, False, True, False]] * 3,
        dtype=torch.bool,
    )
    generator = torch.Generator(device="cpu").manual_seed(409)
    sample = policy.sample(context, eligible, forced, generator=generator)
    replay = policy.evaluate_actions(context, eligible, forced, sample.actions)
    assert torch.equal(sample.actions[~eligible], forced[~eligible])
    torch.testing.assert_close(replay.logits, sample.logits, rtol=0, atol=0)
    torch.testing.assert_close(replay.log_prob, sample.log_prob, rtol=0, atol=0)
    torch.testing.assert_close(replay.entropy, sample.entropy, rtol=0, atol=0)


def test_gae_terminal_bootstrap_truncation_bootstrap_and_trace_boundaries() -> None:
    rewards = torch.tensor([[1.0], [2.0], [3.0], [4.0]])
    values = torch.zeros_like(rewards)
    next_values = torch.tensor([[0.0], [10.0], [0.0], [100.0]])
    terminated = torch.tensor([[False], [False], [False], [True]])
    truncated = torch.tensor([[False], [True], [False], [False]])
    advantages, returns = compute_gae(
        rewards,
        values,
        next_values,
        terminated,
        truncated,
        gamma=0.9,
        gae_lambda=0.8,
    )
    # Step 1 bootstraps from 10 but does not inherit step 2.  Step 3 ignores
    # the supplied 100 because an actual terminal has zero bootstrap.
    expected = torch.tensor([[8.92], [11.0], [5.88], [4.0]])
    torch.testing.assert_close(advantages, expected)
    torch.testing.assert_close(returns, expected)
    assert not advantages.requires_grad
    assert not returns.requires_grad


def _mixed_batch(policy: MaskPolicy) -> RolloutBatch:
    context = torch.tensor(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
        ]
    )
    eligible = torch.tensor(
        [
            [True, False],
            [False, True],
            [False, False],
            [False, False],
            [False, False],
        ]
    )
    forced = torch.tensor(
        [
            [False, False],
            [False, False],
            [True, True],
            [False, False],
            [True, False],
        ]
    )
    actions = forced.clone()  # Both eligible decisions execute KEEP.
    with torch.no_grad():
        old_log_prob = policy.evaluate_actions(
            context, eligible, forced, actions
        ).log_prob
    return RolloutBatch(
        context=context,
        actions=actions,
        eligible=eligible,
        forced_end=forced,
        old_log_prob=old_log_prob,
        advantages=torch.tensor([2.0, -1.0, 100.0, -100.0, 500.0]),
        returns=torch.tensor([1.0, -1.0, 0.5, 2.0, -2.0]),
    )


def test_ppo_keeps_tail_counts_forced_critic_rows_and_private_shuffle_rng() -> None:
    policy = MaskPolicy(3, 2, "joint", hidden_size=8, seed=81)
    critic = ValueCritic(3, hidden_size=8, seed=82)
    updater = PPOUpdater(
        policy,
        critic,
        learning_rate=1e-2,
        epochs=2,
        minibatch_size=2,
        seed=83,
    )
    batch = _mixed_batch(policy)
    actor_before = _state(policy)
    critic_before = _state(critic)
    torch.manual_seed(97)
    global_before = torch.get_rng_state().clone()
    stats = updater.update(batch)
    assert torch.equal(torch.get_rng_state(), global_before)

    assert stats["planned_rows"] == 5
    assert stats["optional_rows"] == 2
    assert stats["visited_rows"] == 10
    assert stats["actor_visited_rows"] == 4
    assert stats["critic_optimizer_steps"] == 6
    assert 2 <= stats["actor_optimizer_steps"] <= 4
    assert stats["max_minibatch_size"] == 2
    assert any(
        not torch.equal(actor_before[name], value)
        for name, value in policy.state_dict().items()
    )
    assert any(
        not torch.equal(critic_before[name], value)
        for name, value in critic.state_dict().items()
    )
    assert all(
        math.isfinite(float(stats[key]))
        for key in ("actor_loss", "critic_loss", "entropy")
    )


def test_all_forced_update_skips_actor_optimizer_even_with_existing_momentum() -> None:
    policy = MaskPolicy(3, 2, "joint", hidden_size=8, seed=101)
    critic = ValueCritic(3, hidden_size=8, seed=102)
    updater = PPOUpdater(
        policy,
        critic,
        learning_rate=1e-2,
        epochs=1,
        minibatch_size=2,
        seed=103,
    )
    updater.update(_mixed_batch(policy))
    assert updater.actor_optimizer.state

    rows = 3
    context = torch.randn(rows, 3)
    eligible = torch.zeros(rows, 2, dtype=torch.bool)
    forced = torch.tensor([[True, True], [False, True], [True, False]])
    actions = forced.clone()
    with torch.no_grad():
        old_log_prob = policy.evaluate_actions(
            context, eligible, forced, actions
        ).log_prob
    batch = RolloutBatch(
        context=context,
        actions=actions,
        eligible=eligible,
        forced_end=forced,
        old_log_prob=old_log_prob,
        advantages=torch.zeros(rows),
        returns=torch.tensor([1.0, -1.0, 0.5]),
    )
    actor_before = _state(policy)
    optimizer_before = copy.deepcopy(updater.actor_optimizer.state_dict())
    stats = updater.update(batch)
    assert stats["actor_optimizer_steps"] == 0
    assert stats["actor_visited_rows"] == 0
    assert stats["critic_optimizer_steps"] == 2
    for name, value in policy.state_dict().items():
        torch.testing.assert_close(value, actor_before[name], rtol=0, atol=0)
    optimizer_after = updater.actor_optimizer.state_dict()
    assert optimizer_after["param_groups"] == optimizer_before["param_groups"]
    assert optimizer_after["state"].keys() == optimizer_before["state"].keys()
    for parameter_id, prior_state in optimizer_before["state"].items():
        for name, prior_value in prior_state.items():
            current_value = optimizer_after["state"][parameter_id][name]
            if isinstance(prior_value, torch.Tensor):
                assert torch.equal(current_value, prior_value)
            else:
                assert current_value == prior_value


def test_ppo_ratio_overflow_fails_before_actor_optimizer_step() -> None:
    policy = MaskPolicy(1, 1, "joint", hidden_size=4, seed=111)
    critic = ValueCritic(1, hidden_size=4, seed=112)
    updater = PPOUpdater(policy, critic, epochs=1, minibatch_size=2, seed=113)
    context = torch.zeros(2, 1)
    eligible = torch.ones(2, 1, dtype=torch.bool)
    forced = torch.zeros_like(eligible)
    actions = torch.tensor([[False], [True]])
    batch = RolloutBatch(
        context=context,
        actions=actions,
        eligible=eligible,
        forced_end=forced,
        old_log_prob=torch.full((2,), -1e30),
        advantages=torch.tensor([1.0, -1.0]),
        returns=torch.zeros(2),
    )
    actor_before = _state(policy)
    with pytest.raises(FloatingPointError, match="PPO ratios"):
        updater.update(batch)
    for name, value in policy.state_dict().items():
        torch.testing.assert_close(value, actor_before[name], rtol=0, atol=0)
    assert not updater.actor_optimizer.state
    assert not updater.critic_optimizer.state


def test_nonfinite_critic_loss_fails_before_critic_optimizer_step() -> None:
    policy = MaskPolicy(1, 1, "joint", hidden_size=4, seed=121)
    critic = ValueCritic(1, hidden_size=4, seed=122)
    updater = PPOUpdater(policy, critic, epochs=1, minibatch_size=2, seed=123)
    context = torch.zeros(2, 1)
    eligible = torch.zeros(2, 1, dtype=torch.bool)
    forced = torch.tensor([[True], [False]])
    critic_before = _state(critic)
    batch = RolloutBatch(
        context=context,
        actions=forced.clone(),
        eligible=eligible,
        forced_end=forced,
        old_log_prob=torch.zeros(2),
        advantages=torch.zeros(2),
        returns=torch.full((2,), torch.finfo(torch.float32).max),
    )
    with pytest.raises(FloatingPointError, match="critic loss"):
        updater.update(batch)
    for name, value in critic.state_dict().items():
        torch.testing.assert_close(value, critic_before[name], rtol=0, atol=0)
    assert not updater.actor_optimizer.state
    assert not updater.critic_optimizer.state


def test_nonfinite_actor_gradient_fails_before_actor_optimizer_step() -> None:
    class InfiniteBackward(torch.autograd.Function):
        @staticmethod
        def forward(ctx: object, weight: torch.Tensor) -> torch.Tensor:
            return weight * 0.0

        @staticmethod
        def backward(ctx: object, gradient: torch.Tensor) -> tuple[torch.Tensor]:
            return (torch.full_like(gradient, float("inf")),)

    class FiniteLogitInfiniteGradient(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.weight = torch.nn.Parameter(torch.tensor(0.0))

        def forward(self, features: torch.Tensor) -> torch.Tensor:
            return InfiniteBackward.apply(self.weight).expand(features.shape[0])

    policy = MaskPolicy(1, 1, "joint", hidden_size=4, seed=131)
    policy.actor = FiniteLogitInfiniteGradient()
    critic = ValueCritic(1, hidden_size=4, seed=132)
    updater = PPOUpdater(policy, critic, epochs=1, minibatch_size=2, seed=133)
    context = torch.zeros(2, 1)
    eligible = torch.ones(2, 1, dtype=torch.bool)
    forced = torch.zeros_like(eligible)
    actions = torch.tensor([[False], [True]])
    with torch.no_grad():
        old_log_prob = policy.evaluate_actions(
            context, eligible, forced, actions
        ).log_prob
    batch = RolloutBatch(
        context=context,
        actions=actions,
        eligible=eligible,
        forced_end=forced,
        old_log_prob=old_log_prob,
        advantages=torch.tensor([1.0, -1.0]),
        returns=torch.zeros(2),
    )
    actor_before = _state(policy)
    with pytest.raises(FloatingPointError, match="actor gradient norm"):
        updater.update(batch)
    for name, value in policy.state_dict().items():
        torch.testing.assert_close(value, actor_before[name], rtol=0, atol=0)
    assert not updater.actor_optimizer.state
    assert not updater.critic_optimizer.state
