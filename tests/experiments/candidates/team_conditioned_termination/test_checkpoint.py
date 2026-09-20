from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import torch

from experiments.candidates.team_conditioned_termination.checkpoint import (
    GateArchitecture,
    GateCheckpointBinding,
    GateProgress,
    GateTrainingConfig,
    load_gate_checkpoint,
    save_gate_checkpoint,
)
from experiments.candidates.team_conditioned_termination.policy import (
    MaskPolicy,
    PPOUpdater,
    RolloutBatch,
    ValueCritic,
)


def _binding(*, mode: str = "joint") -> GateCheckpointBinding:
    return GateCheckpointBinding.create(
        arm="J" if mode == "joint" else "I",
        mode=mode,  # type: ignore[arg-type]
        foundation_sha256="a" * 64,
        source_sha="b" * 40,
        feature_config={
            "schema": "scaled-central-v1",
            "fields": ["state", "intent", "age", "eligibility"],
            "clip": 5.0,
        },
        rule_config={"caps": {"team": 10, "local": 10}, "mandatory_precedence": True},
        architecture=GateArchitecture(
            context_dim=3,
            n_agents=2,
            policy_hidden_size=8,
            critic_hidden_size=8,
            end_probability=0.2,
            policy_sample_seed=711,
        ),
        training=GateTrainingConfig(
            learning_rate=1e-2,
            critic_learning_rate=2e-2,
            clip_epsilon=0.15,
            entropy_coef=0.01,
            value_coef=0.6,
            max_grad_norm=0.7,
            epochs=2,
            minibatch_size=2,
        ),
    )


def _learner(binding: GateCheckpointBinding) -> tuple[MaskPolicy, ValueCritic, PPOUpdater]:
    architecture = binding.architecture
    training = binding.training
    policy = MaskPolicy(
        architecture.context_dim,
        architecture.n_agents,
        binding.mode,
        hidden_size=architecture.policy_hidden_size,
        seed=architecture.policy_sample_seed,
        end_probability=architecture.end_probability,
    )
    critic = ValueCritic(
        architecture.context_dim, hidden_size=architecture.critic_hidden_size, seed=712
    )
    updater = PPOUpdater(
        policy,
        critic,
        learning_rate=training.learning_rate,
        critic_learning_rate=training.critic_learning_rate,
        clip_epsilon=training.clip_epsilon,
        entropy_coef=training.entropy_coef,
        value_coef=training.value_coef,
        max_grad_norm=training.max_grad_norm,
        epochs=training.epochs,
        minibatch_size=training.minibatch_size,
        seed=713,
    )
    return policy, critic, updater


def _batch(policy: MaskPolicy) -> RolloutBatch:
    context = torch.tensor(
        [[0.0, 0.0, 0.0], [1.0, -1.0, 0.5], [0.4, 0.2, -0.3], [-0.8, 0.6, 1.0], [0.1, -0.2, 0.7]]
    )
    eligible = torch.tensor(
        [[True, True], [True, False], [False, True], [True, True], [True, False]]
    )
    forced = torch.tensor(
        [[False, False], [False, True], [True, False], [False, False], [False, False]]
    )
    actions = torch.tensor(
        [[False, True], [True, True], [True, False], [True, False], [False, False]]
    )
    with torch.no_grad():
        old_log_prob = policy.evaluate_actions(context, eligible, forced, actions).log_prob
    return RolloutBatch(
        context=context,
        actions=actions,
        eligible=eligible,
        forced_end=forced,
        old_log_prob=old_log_prob,
        advantages=torch.tensor([1.5, -0.7, 0.4, 2.0, -1.0]),
        returns=torch.tensor([0.8, -0.2, 1.1, 0.3, -0.6]),
    )


def _module_state(module: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {key: value.detach().clone() for key, value in module.state_dict().items()}


def _assert_module_state_equal(
    left: torch.nn.Module | dict[str, torch.Tensor],
    right: torch.nn.Module | dict[str, torch.Tensor],
) -> None:
    left_state = left.state_dict() if isinstance(left, torch.nn.Module) else left
    right_state = right.state_dict() if isinstance(right, torch.nn.Module) else right
    assert left_state.keys() == right_state.keys()
    for key in left_state:
        torch.testing.assert_close(left_state[key], right_state[key], rtol=0, atol=0)


def _assert_nested_equal(left: Any, right: Any) -> None:
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor)
        assert left.dtype == right.dtype and left.shape == right.shape
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert isinstance(right, dict) and left.keys() == right.keys()
        for key in left:
            _assert_nested_equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert isinstance(right, type(left)) and len(left) == len(right)
        for left_item, right_item in zip(left, right):
            _assert_nested_equal(left_item, right_item)
    else:
        assert type(left) is type(right) and left == right


def _sample_inputs() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    context = torch.tensor([[0.3, -0.4, 0.8], [-0.1, 0.7, 0.2], [0.9, 0.1, -0.5]])
    eligible = torch.tensor([[True, True], [True, False], [False, True]])
    forced = torch.tensor([[False, False], [False, True], [True, False]])
    return context, eligible, forced


def test_checkpoint_replays_owned_samples_and_next_ppo_update_exactly(tmp_path: Path) -> None:
    binding = _binding()
    policy, critic, updater = _learner(binding)
    gate_sampler = torch.Generator(device="cpu").manual_seed(714)
    context, eligible, forced = _sample_inputs()

    # Establish both private sampler streams and nonempty Adam moments.
    policy.sample(context, eligible, forced)
    policy.sample(context, eligible, forced, generator=gate_sampler)
    warmup_stats = updater.update(_batch(policy))
    assert warmup_stats["actor_optimizer_steps"] == 6
    assert warmup_stats["critic_optimizer_steps"] == 6
    assert updater.actor_optimizer.state and updater.critic_optimizer.state
    continuation_batch = _batch(policy)

    path = tmp_path / "gate.pt"
    torch.manual_seed(991)
    global_before = torch.get_rng_state().clone()
    save_gate_checkpoint(
        path,
        policy=policy,
        critic=critic,
        updater=updater,
        gate_sampler=gate_sampler,
        binding=binding,
        progress=GateProgress(completed_episodes=9, completed_updates=1),
    )
    assert torch.equal(torch.get_rng_state(), global_before)
    restored = load_gate_checkpoint(path, expected_binding=binding)
    assert torch.equal(torch.get_rng_state(), global_before)
    assert restored.binding == binding
    assert restored.progress == GateProgress(completed_episodes=9, completed_updates=1)

    expected_private = policy.sample(context, eligible, forced)
    actual_private = restored.policy.sample(context, eligible, forced)
    expected_gate = policy.sample(context, eligible, forced, generator=gate_sampler)
    actual_gate = restored.policy.sample(
        context, eligible, forced, generator=restored.gate_sampler
    )
    for expected, actual in (
        (expected_private, actual_private),
        (expected_gate, actual_gate),
    ):
        assert torch.equal(expected.actions, actual.actions)
        torch.testing.assert_close(expected.log_prob, actual.log_prob, rtol=0, atol=0)
        torch.testing.assert_close(expected.logits, actual.logits, rtol=0, atol=0)

    expected_stats = updater.update(continuation_batch)
    actual_stats = restored.updater.update(continuation_batch)
    assert actual_stats == expected_stats
    assert actual_stats["actor_optimizer_steps"] == 6
    assert actual_stats["critic_optimizer_steps"] == 6
    _assert_module_state_equal(policy, restored.policy)
    _assert_module_state_equal(critic, restored.critic)
    _assert_nested_equal(
        updater.actor_optimizer.state_dict(), restored.updater.actor_optimizer.state_dict()
    )
    _assert_nested_equal(
        updater.critic_optimizer.state_dict(), restored.updater.critic_optimizer.state_dict()
    )
    assert torch.equal(gate_sampler.get_state(), restored.gate_sampler.get_state())
    assert torch.equal(
        updater._shuffle_generator.get_state(), restored.updater._shuffle_generator.get_state()
    )
    assert torch.equal(torch.get_rng_state(), global_before)


def _save_fixture(path: Path) -> tuple[
    GateCheckpointBinding, MaskPolicy, ValueCritic, PPOUpdater, torch.Generator
]:
    binding = _binding()
    policy, critic, updater = _learner(binding)
    updater.update(_batch(policy))
    gate_sampler = torch.Generator(device="cpu").manual_seed(801)
    save_gate_checkpoint(
        path,
        policy=policy,
        critic=critic,
        updater=updater,
        gate_sampler=gate_sampler,
        binding=binding,
        progress=GateProgress(completed_episodes=3, completed_updates=1),
    )
    return binding, policy, critic, updater, gate_sampler


@pytest.mark.parametrize(
    "changed",
    ["arm", "foundation", "features", "training", "rule", "mode"],
)
def test_binding_mismatch_refuses_without_mutating_live_caller(
    tmp_path: Path, changed: str
) -> None:
    path = tmp_path / "gate.pt"
    binding, policy, critic, updater, gate_sampler = _save_fixture(path)
    policy_before = _module_state(policy)
    critic_before = _module_state(critic)
    actor_optimizer_before = copy.deepcopy(updater.actor_optimizer.state_dict())
    critic_optimizer_before = copy.deepcopy(updater.critic_optimizer.state_dict())
    gate_before = gate_sampler.get_state().clone()
    if changed == "arm":
        expected = replace(binding, arm="other-arm")
    elif changed == "foundation":
        expected = replace(binding, foundation_sha256="c" * 64)
    elif changed == "features":
        expected = replace(binding, feature_config_json='{"schema":"different"}')
    elif changed == "training":
        expected = replace(
            binding,
            training=replace(binding.training, learning_rate=5e-3),
        )
    elif changed == "rule":
        expected = replace(binding, rule_config_json='{"caps":{"local":9,"team":10}}')
    else:
        expected = replace(binding, arm="I", mode="independent")

    with pytest.raises(ValueError, match="binding does not match"):
        load_gate_checkpoint(path, expected_binding=expected)
    _assert_module_state_equal(policy, policy_before)
    _assert_module_state_equal(critic, critic_before)
    _assert_nested_equal(updater.actor_optimizer.state_dict(), actor_optimizer_before)
    _assert_nested_equal(updater.critic_optimizer.state_dict(), critic_optimizer_before)
    assert torch.equal(gate_sampler.get_state(), gate_before)


def test_malformed_tensor_state_refuses_without_mutating_live_caller(tmp_path: Path) -> None:
    path = tmp_path / "gate.pt"
    binding, policy, critic, updater, gate_sampler = _save_fixture(path)
    payload = torch.load(path, map_location="cpu", weights_only=True)
    payload["policy_state"].pop(next(iter(payload["policy_state"])))
    malformed = tmp_path / "malformed.pt"
    torch.save(payload, malformed)

    policy_before = _module_state(policy)
    critic_before = _module_state(critic)
    actor_optimizer_before = copy.deepcopy(updater.actor_optimizer.state_dict())
    gate_before = gate_sampler.get_state().clone()
    torch.manual_seed(992)
    global_before = torch.get_rng_state().clone()
    with pytest.raises(ValueError, match="state keys"):
        load_gate_checkpoint(malformed, expected_binding=binding)
    assert torch.equal(torch.get_rng_state(), global_before)
    _assert_module_state_equal(policy, policy_before)
    _assert_module_state_equal(critic, critic_before)
    _assert_nested_equal(updater.actor_optimizer.state_dict(), actor_optimizer_before)
    assert torch.equal(gate_sampler.get_state(), gate_before)


def test_malformed_adam_moment_refuses_without_mutating_live_caller(tmp_path: Path) -> None:
    path = tmp_path / "gate.pt"
    binding, policy, critic, updater, gate_sampler = _save_fixture(path)
    payload = torch.load(path, map_location="cpu", weights_only=True)
    parameter_id = next(iter(payload["actor_optimizer_state"]["state"]))
    payload["actor_optimizer_state"]["state"][parameter_id]["exp_avg"] = torch.zeros(1)
    malformed = tmp_path / "malformed-adam.pt"
    torch.save(payload, malformed)

    policy_before = _module_state(policy)
    actor_optimizer_before = copy.deepcopy(updater.actor_optimizer.state_dict())
    gate_before = gate_sampler.get_state().clone()
    torch.manual_seed(993)
    global_before = torch.get_rng_state().clone()
    with pytest.raises(ValueError, match="Adam exp_avg"):
        load_gate_checkpoint(malformed, expected_binding=binding)
    assert torch.equal(torch.get_rng_state(), global_before)
    _assert_module_state_equal(policy, policy_before)
    _assert_nested_equal(updater.actor_optimizer.state_dict(), actor_optimizer_before)
    assert torch.equal(gate_sampler.get_state(), gate_before)


def test_checkpoint_rejects_unsupported_metadata_before_write(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="unsupported metadata type"):
        GateCheckpointBinding.create(
            arm="J",
            mode="joint",
            foundation_sha256="a" * 64,
            source_sha="b" * 40,
            feature_config={"bad": object()},
            rule_config={},
            architecture=_binding().architecture,
            training=_binding().training,
        )
    assert not (tmp_path / "gate.pt").exists()
