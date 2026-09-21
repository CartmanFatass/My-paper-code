from __future__ import annotations

import copy
import math

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.frozen_mean_gate_b08.engine import (
    Gate,
    collect_episode,
    freeze_foundation,
    make_critic,
    make_optimizers,
    update,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import (
    SyntheticAdapter,
    actor_features,
    team_reward,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Actor


def _actor(seed: int = 101) -> Actor:
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(seed)
        actor = Actor()
    return freeze_foundation(actor)  # type: ignore[return-value]


def _state(module: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().clone() for name, value in module.state_dict().items()}


def _assert_state(module: torch.nn.Module, expected: dict[str, torch.Tensor]) -> None:
    assert module.state_dict().keys() == expected.keys()
    for name, value in module.state_dict().items():
        torch.testing.assert_close(value, expected[name], rtol=0, atol=0)


def test_gate_initialization_simple_nesting_and_private_module_rng() -> None:
    torch.manual_seed(301)
    global_before = torch.get_rng_state().clone()
    agreement = Gate("agreement", seed=302)
    contextual = Gate("contextual", seed=303)
    contextual_repeat = Gate("contextual", seed=303)
    assert torch.equal(torch.get_rng_state(), global_before)

    context = torch.zeros(2, 5, 175)
    context[0, :, -1] = torch.linspace(0.0, 1.0, 5)
    assert torch.equal(agreement(context), torch.zeros(2, 5))
    assert torch.equal(contextual(context), agreement(context))
    for left, right in zip(contextual.parameters(), contextual_repeat.parameters()):
        torch.testing.assert_close(left, right, rtol=0, atol=0)

    with torch.no_grad():
        agreement.b0.fill_(0.25)
        agreement.b1.fill_(-2.0)
        contextual.b0.copy_(agreement.b0)
        contextual.b1.copy_(agreement.b1)
        contextual.residual[-1].bias.fill_(0.75)
    torch.testing.assert_close(
        contextual(context), agreement(context) + 0.75, rtol=0, atol=0
    )
    assert agreement(context)[0, 0] > agreement(context)[0, -1]
    keep = torch.tensor([[True, False, True, False, True]] * 2)
    logits = agreement(context)
    expected = torch.where(keep, -torch.nn.functional.softplus(-logits),
                           -torch.nn.functional.softplus(logits))
    torch.testing.assert_close(agreement.log_prob(context, keep), expected)


def test_critic_initialization_and_foundation_freeze_preserve_rng_and_bytes() -> None:
    actor = _actor(311)
    actor.train()
    for parameter in actor.parameters():
        parameter.requires_grad_(True)
    before = _state(actor)
    torch.manual_seed(312)
    global_before = torch.get_rng_state().clone()
    first = make_critic(313)
    second = make_critic(313)
    assert torch.equal(torch.get_rng_state(), global_before)
    _assert_state(first, _state(second))
    returned = freeze_foundation(actor)
    assert returned is actor and not actor.training
    assert not any(parameter.requires_grad for parameter in actor.parameters())
    _assert_state(actor, before)


def test_learned_collection_has_legal_predecision_feedback_and_fixed_coins() -> None:
    horizon = 5
    foundation = _actor(321)
    foundation_before = _state(foundation)
    gate = Gate("agreement", seed=322)
    with torch.no_grad():
        gate.b0.fill_(0.2)
        gate.b1.fill_(-0.4)
    critic = make_critic(323)
    actor_inputs: list[torch.Tensor] = []
    handle = foundation.register_forward_pre_hook(
        lambda _module, args: actor_inputs.append(args[0].detach().clone())
    )
    counts: dict[str, int] = {}
    torch.manual_seed(324)
    global_before = torch.get_rng_state().clone()
    episode = collect_episode(
        SyntheticAdapter(7, horizon), foundation, gate, critic,
        horizon=horizon, reset_seed=17, gate_seed=325, phase="train",
        check=lambda: None, counts=counts,
    )
    assert torch.equal(torch.get_rng_state(), global_before)
    handle.remove()
    _assert_state(foundation, foundation_before)

    expected_uniforms = torch.rand(
        (horizon, 5), generator=torch.Generator(device="cpu").manual_seed(325)
    )
    torch.testing.assert_close(episode["gate_uniforms"], expected_uniforms, rtol=0, atol=0)
    assert episode["context"].shape == (horizon, 5, 175)
    assert episode["critic"].shape == (horizon, 136)
    assert not episode["eligible"][0].any()
    assert torch.equal(episode["eligible"][1:], ~episode["keep"][:-1])
    assert not episode["keep"][~episode["eligible"]].any()
    assert not episode["logp"][~episode["eligible"]].any()
    torch.testing.assert_close(episode["context"][..., 104:107], episode["previous"])
    torch.testing.assert_close(episode["context"][..., 107:110], episode["means"].tanh())
    expected_d = (
        (episode["means"].tanh() - episode["previous"]).square().sum(-1) / 12.0
    )
    torch.testing.assert_close(episode["context"][..., -1], expected_d)
    commitments = episode["critic"][:, 116:].reshape(horizon, 5, 4)
    torch.testing.assert_close(commitments[..., :3], episode["previous"])
    torch.testing.assert_close(
        commitments[..., 3], episode["eligible"].float() / 4.0
    )
    assert all(not value[..., -1].any() for value in actor_inputs)
    assert counts == {
        "gate_uniform_values": 25,
        "reset_calls": 1,
        "foundation_forward_calls": 5,
        "recurrent_agent_observations": 25,
        "gate_decisions": int(episode["eligible"].sum()),
        "keep_decisions": int(episode["keep"].sum()),
        "end_decisions": int((episode["eligible"] & ~episode["keep"]).sum()),
        "forced_fresh_decisions": int((~episode["eligible"]).sum()),
        "final_gate_credit_decisions": int(episode["eligible"][-1].sum()),
        "team_steps": 5,
        "train_team_steps": 5,
        "train_episodes": 1,
    }

    replay_counts: dict[str, int] = {}
    replay = collect_episode(
        SyntheticAdapter(99, horizon), foundation, gate, critic,
        horizon=horizon, reset_seed=17, gate_seed=325, phase="train",
        check=lambda: None, counts=replay_counts,
    )
    for name in episode:
        torch.testing.assert_close(episode[name], replay[name], rtol=0, atol=0)


def test_ordinary_collection_matches_independent_frozen_mean_loop() -> None:
    horizon = 4
    reset_seed = 41
    foundation = _actor(331)
    episode = collect_episode(
        SyntheticAdapter(12, horizon), foundation, None, None,
        horizon=horizon, reset_seed=reset_seed, gate_seed=999, phase="eval",
        check=lambda: None, counts=(counts := {}),
    )

    env = SyntheticAdapter(50, horizon)
    obs, info = env.reset(seed=reset_seed)
    state = info["state"]
    hidden = torch.zeros(1, 5, 64)
    last = np.zeros((5, 3), dtype=np.float32)
    expected_commands, expected_means, expected_rewards = [], [], []
    for _tick in range(horizon):
        x = actor_features(obs, last, np.zeros(5, dtype=np.int64))
        with torch.no_grad():
            mean, _recurrent, hidden = foundation(torch.from_numpy(x)[None], hidden)
        command = mean[0].tanh().numpy()
        obs, _scalar, _terminated, _truncated, info = env.step(command)
        state = info["next_state"]
        expected_commands.append(torch.from_numpy(command.copy()))
        expected_means.append(mean[0].clone())
        expected_rewards.append(team_reward(info))
        last = command.copy()
    del state
    torch.testing.assert_close(episode["commands"], torch.stack(expected_commands), rtol=0, atol=0)
    torch.testing.assert_close(episode["means"], torch.stack(expected_means), rtol=0, atol=0)
    assert episode["reward"].dtype == torch.float64
    torch.testing.assert_close(
        episode["reward"], torch.tensor(expected_rewards, dtype=torch.float64)
    )
    assert not episode["eligible"].any() and not episode["keep"].any()
    assert not episode["gate_uniforms"].any() and not episode["keep_probability"].any()
    assert counts["forced_fresh_decisions"] == horizon * 5
    assert counts.get("gate_uniform_values", 0) == counts.get("gate_decisions", 0) == 0


def test_returned_transition_is_counted_before_invalid_reward() -> None:
    class InvalidReward(SyntheticAdapter):
        def step(self, actions):
            result = list(super().step(actions))
            result[-1] = copy.deepcopy(result[-1])
            result[-1]["rewards_dict"]["uav_0"] = float("nan")
            return tuple(result)

    counts: dict[str, int] = {}
    with pytest.raises(FloatingPointError, match="nonfinite team reward"):
        collect_episode(
            InvalidReward(1, 3), _actor(341), Gate("agreement", 342), make_critic(343),
            horizon=3, reset_seed=2, gate_seed=344, phase="eval",
            check=lambda: None, counts=counts,
        )
    assert counts["reset_calls"] == 1
    assert counts["foundation_forward_calls"] == 1
    assert counts["team_steps"] == counts["eval_team_steps"] == 1
    assert counts.get("eval_episodes", 0) == 0


def test_collection_requires_the_boundary_at_the_exact_horizon() -> None:
    class EarlyBoundary(SyntheticAdapter):
        def step(self, actions):
            obs, scalar, _terminated, truncated, info = super().step(actions)
            return obs, scalar, True, truncated, info

    class MissingBoundary(SyntheticAdapter):
        def step(self, actions):
            obs, scalar, _terminated, truncated, info = super().step(actions)
            return obs, scalar, False, truncated, info

    early_counts: dict[str, int] = {}
    with pytest.raises(RuntimeError, match="boundary at 1/3"):
        collect_episode(
            EarlyBoundary(1, 3), _actor(345), None, None,
            horizon=3, reset_seed=2, gate_seed=0, phase="eval",
            check=lambda: None, counts=early_counts,
        )
    assert early_counts["team_steps"] == 1 and early_counts["eval_episodes"] == 0

    missing_counts: dict[str, int] = {}
    with pytest.raises(RuntimeError, match="did not terminate at exact horizon 3"):
        collect_episode(
            MissingBoundary(1, 3), _actor(346), None, None,
            horizon=3, reset_seed=2, gate_seed=0, phase="eval",
            check=lambda: None, counts=missing_counts,
        )
    assert missing_counts["team_steps"] == 3 and missing_counts["eval_episodes"] == 0


def _tensor_episode(
    gate: Gate,
    horizon: int,
    rewards: torch.Tensor,
    eligible: torch.Tensor,
    keep: torch.Tensor,
) -> dict[str, torch.Tensor]:
    context = torch.zeros(horizon, 5, 175)
    context[..., -1] = torch.linspace(0.0, 1.0, horizon)[:, None]
    with torch.no_grad():
        logp = torch.where(eligible, gate.log_prob(context, keep), torch.zeros(horizon, 5))
    return {
        "context": context,
        "critic": torch.linspace(-1.0, 1.0, horizon * 136).reshape(horizon, 136),
        "eligible": eligible,
        "keep": keep,
        "logp": logp,
        "value": torch.zeros(horizon),
        "reward": rewards,
    }


def test_update_uses_normalized_full_returns_optional_likelihood_and_forced_denominator() -> None:
    gate = Gate("agreement", 351)
    critic = make_critic(352)
    with torch.no_grad():
        for parameter in critic.parameters():
            parameter.zero_()
    gate_optimizer, critic_optimizer = make_optimizers(gate, critic)
    eligible_a = torch.tensor([[True, False, False, False, False], [False] * 5])
    eligible_b = torch.tensor([[False, True, False, False, False], [False] * 5])
    keep_a = torch.tensor([[True, False, False, False, False], [False] * 5])
    keep_b = torch.zeros(2, 5, dtype=torch.bool)
    first = _tensor_episode(gate, 2, torch.tensor([1.0, 3.0]), eligible_a, keep_a)
    second = _tensor_episode(gate, 2, torch.tensor([2.0, 0.0]), eligible_b, keep_b)
    first["logp"][~eligible_a] = 1e30
    second["logp"][~eligible_b] = -1e30
    counts: dict[str, int] = {}
    records = update(
        gate, critic, gate_optimizer, critic_optimizer, [first, second],
        torch.Generator(device="cpu").manual_seed(353),
        horizon=2, check=lambda: None, counts=counts,
    )
    targets = torch.tensor([2.0, 1.5, 1.0, 0.0])
    advantage = (targets - targets.mean()) / (targets.std(unbiased=False) + 1e-8)
    expected_gate_loss = -(advantage[0] + advantage[2]) / 4.0
    torch.testing.assert_close(torch.tensor(records[0]["gate_loss"]), expected_gate_loss)
    torch.testing.assert_close(torch.tensor(records[0]["critic_loss"]),
                               0.5 * targets.square().mean())
    assert len(records) == 4
    assert counts == {
        "update_calls": 1,
        "visited_rows": 16,
        "max_minibatch": 4,
        "gate_optimizer_steps": 4,
        "optimizer_steps": 8,
        "critic_optimizer_steps": 4,
    }


def test_collected_rollout_moves_gate_and_critic_but_not_foundation() -> None:
    foundation = _actor(361)
    foundation_before = _state(foundation)
    gate = Gate("contextual", 362)
    critic = make_critic(363)
    gate_before, critic_before = _state(gate), _state(critic)
    episodes, counts = [], {}
    for episode_index in range(2):
        episodes.append(collect_episode(
            SyntheticAdapter(20 + episode_index, 4), foundation, gate, critic,
            horizon=4, reset_seed=30 + episode_index, gate_seed=364 + episode_index,
            phase="train", check=lambda: None, counts=counts,
        ))
    gate_optimizer, critic_optimizer = make_optimizers(gate, critic)
    records = update(
        gate, critic, gate_optimizer, critic_optimizer, episodes,
        torch.Generator(device="cpu").manual_seed(366),
        horizon=4, check=lambda: None, counts=counts,
    )
    assert len(records) == 4
    assert any(not torch.equal(value, gate_before[name]) for name, value in gate.state_dict().items())
    assert any(not torch.equal(value, critic_before[name]) for name, value in critic.state_dict().items())
    _assert_state(foundation, foundation_before)
    assert counts["gate_optimizer_steps"] == counts["critic_optimizer_steps"] == 4


def test_production_sized_tensor_update_has_bounded_minibatches() -> None:
    horizon = 256
    gate = Gate("agreement", 371)
    critic = make_critic(372)
    eligible = torch.ones(horizon, 5, dtype=torch.bool)
    keep = torch.zeros_like(eligible)
    episodes = [
        _tensor_episode(gate, horizon, torch.linspace(0.0, 1.0, horizon), eligible, keep),
        _tensor_episode(gate, horizon, torch.linspace(1.0, 0.0, horizon), eligible, keep),
    ]
    gate_optimizer, critic_optimizer = make_optimizers(gate, critic)
    counts: dict[str, int] = {}
    records = update(
        gate, critic, gate_optimizer, critic_optimizer, episodes,
        torch.Generator(device="cpu").manual_seed(373),
        horizon=horizon, check=lambda: None, counts=counts,
    )
    assert len(records) == 8 and max(record["rows"] for record in records) == 256
    assert counts["visited_rows"] == 4 * 2 * horizon
    assert counts["max_minibatch"] == 256
    assert counts["gate_optimizer_steps"] == counts["critic_optimizer_steps"] == 8
    assert counts["optimizer_steps"] == 16


def test_update_failure_preserves_completed_actor_step_count() -> None:
    class FailFourthCheck:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self) -> None:
            self.calls += 1
            if self.calls == 4:
                raise RuntimeError("synthetic stop")

    gate = Gate("agreement", 381)
    critic = make_critic(382)
    eligible = torch.ones(2, 5, dtype=torch.bool)
    keep = torch.zeros_like(eligible)
    episodes = [
        _tensor_episode(gate, 2, torch.tensor([1.0, 0.0]), eligible, keep),
        _tensor_episode(gate, 2, torch.tensor([0.5, -0.5]), eligible, keep),
    ]
    gate_optimizer, critic_optimizer = make_optimizers(gate, critic)
    counts: dict[str, int] = {}
    with pytest.raises(RuntimeError, match="synthetic stop"):
        update(
            gate, critic, gate_optimizer, critic_optimizer, episodes,
            torch.Generator(device="cpu").manual_seed(383),
            horizon=2, check=FailFourthCheck(), counts=counts,
        )
    assert counts["update_calls"] == 1
    assert counts["visited_rows"] == 4
    assert counts["gate_optimizer_steps"] == counts["optimizer_steps"] == 1
    assert counts.get("critic_optimizer_steps", 0) == 0
