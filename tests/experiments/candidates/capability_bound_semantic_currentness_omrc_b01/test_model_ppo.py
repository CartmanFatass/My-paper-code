from __future__ import annotations

from dataclasses import replace
import hashlib
import inspect
import json
import math

import numpy as np
import pytest
import torch
from torch.nn import functional as F

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.checkpoint import (
    CheckpointValidationError,
    capture_checkpoint,
    load_checkpoint,
    restore_checkpoint,
    save_checkpoint,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.model import (
    ACTIVE_PARAMETER_COUNT,
    HIDDEN_DIM,
    PRIMITIVE_DIM,
    REFRESH,
    SAFE_FALLBACK,
    SERVE,
    WAIT,
    CommonRecurrentActorCritic,
    ExplicitGRUCell,
    greedy_action,
    masked_action,
    model_parameter_digest,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import (
    ADAM_STEPS_PER_UPDATE,
    EPISODE_TRANSITIONS,
    EPISODES_PER_ROLLOUT,
    EpisodeRollout,
    PPOLossRecord,
    RecurrentPPOTrainer,
    compute_gae,
    config_digest,
    make_adam,
    ordered_episode_indices,
)


def canonical_u64(address) -> int:
    encoded = json.dumps(
        list(address), ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(encoded).digest()[:8], "big")


@pytest.fixture(scope="module")
def initialized_model() -> CommonRecurrentActorCritic:
    return CommonRecurrentActorCritic(21001)


def test_custom_gru_matches_literal_manual_reset_update_new_equation() -> None:
    cell = ExplicitGRUCell()
    with torch.no_grad():
        for index, parameter in enumerate(cell.parameters()):
            values = torch.arange(parameter.numel(), dtype=torch.float32).reshape(parameter.shape)
            parameter.copy_(((values + index) % 29 - 14) / 100.0)
    inputs = torch.arange(2 * HIDDEN_DIM, dtype=torch.float32).reshape(2, HIDDEN_DIM) / 1000.0
    hidden = torch.flip(inputs, dims=(1,))
    reset = torch.sigmoid(
        F.linear(inputs, cell.weight_ir, cell.bias_ir)
        + F.linear(hidden, cell.weight_hr, cell.bias_hr)
    )
    update = torch.sigmoid(
        F.linear(inputs, cell.weight_iz, cell.bias_iz)
        + F.linear(hidden, cell.weight_hz, cell.bias_hz)
    )
    new = torch.tanh(
        F.linear(inputs, cell.weight_in, cell.bias_in)
        + reset * F.linear(hidden, cell.weight_hn, cell.bias_hn)
    )
    expected = (1.0 - update) * new + update * hidden
    torch.testing.assert_close(cell(inputs, hidden), expected, rtol=0.0, atol=0.0)
    assert not any(isinstance(module, (torch.nn.GRU, torch.nn.GRUCell)) for module in cell.modules())


def test_parameter_initialization_addresses_bytes_count_and_arm_parity(
    initialized_model: CommonRecurrentActorCritic,
) -> None:
    model = initialized_model
    assert model.active_parameter_count == ACTIVE_PARAMETER_COUNT == 121_349
    assert all(parameter.dtype == torch.float32 for parameter in model.parameters())
    assert all(torch.count_nonzero(parameter).item() == 0 for name, parameter in model.named_parameters() if "bias" in name)
    adapter_columns = model.input_weight[:, PRIMITIVE_DIM:].detach().cpu().numpy()
    assert adapter_columns.tobytes() == bytes(adapter_columns.nbytes)
    assert not np.signbit(adapter_columns).any()

    address = ["CBSC-OMRC-B01", "PARAM", 21001, "input.weight", 0]
    uniform = (canonical_u64(address) + 0.5) / float(1 << 64)
    expected = np.float32((2.0 * uniform - 1.0) * math.sqrt(6.0 / (168 + 128)))
    assert model.input_weight.detach().cpu().numpy()[0, 0].tobytes() == expected.tobytes()

    clone = CommonRecurrentActorCritic(21001)
    assert model_parameter_digest(clone) == model.initialization_digest
    for (left_name, left), (right_name, right) in zip(
        model.named_parameters(), clone.named_parameters(), strict=True
    ):
        assert left_name == right_name and torch.equal(left, right)
    assert torch.count_nonzero(model.initial_hidden(3)).item() == 0


def test_parameter_addresses_are_per_logical_gate_and_row_major_flat_index() -> None:
    seen: list[tuple] = []

    def recording_u64(address) -> int:
        seen.append(tuple(address))
        return 1 << 63

    model = CommonRecurrentActorCritic(7, address_u64=recording_u64)
    assert ("CBSC-OMRC-B01", "PARAM", 7, "input.weight", 0) in seen
    assert ("CBSC-OMRC-B01", "PARAM", 7, "input.weight", 135) in seen
    assert ("CBSC-OMRC-B01", "PARAM", 7, "input.weight", 168) in seen
    assert ("CBSC-OMRC-B01", "PARAM", 7, "input.weight", 136) not in seen
    for logical in (
        "gru.weight_ir",
        "gru.weight_iz",
        "gru.weight_in",
        "gru.weight_hr",
        "gru.weight_hz",
        "gru.weight_hn",
        "actor.weight",
        "value.weight",
    ):
        assert any(address[3] == logical and address[4] == 0 for address in seen)
    assert torch.count_nonzero(model.input_weight[:, 136:]).item() == 0


def test_masked_action_uses_strict_float64_cumulative_and_forced_wait_consumes_nothing() -> None:
    logits = torch.zeros((4, 4), dtype=torch.float32)
    decisions = torch.tensor([False, True, True, True])
    third = float((torch.softmax(logits[0, 1:4], dim=0).to(torch.float64) / 1.0)[0].item())
    uniforms = torch.tensor([0.0, third, np.nextafter(2.0 / 3.0, 1.0)], dtype=torch.float64)
    selection = masked_action(logits, decisions, uniforms=uniforms)
    assert selection.actions.tolist() == [WAIT, SERVE, REFRESH, SAFE_FALLBACK]
    assert selection.consumed_uniform.tolist() == [False, True, True, True]
    expected_log_probability = torch.log_softmax(torch.zeros(3), dim=0)[0]
    torch.testing.assert_close(selection.log_probabilities[1:], expected_log_probability.expand(3))
    forced = masked_action(logits[:1], torch.tensor([False]), uniforms=torch.empty(0, dtype=torch.float64))
    assert forced.actions.item() == WAIT and not forced.consumed_uniform.item()

    greedy = greedy_action(torch.tensor([[99.0, 2.0, 2.0, 2.0]]), torch.tensor([True]))
    assert greedy.actions.item() == SERVE
    assert not greedy.consumed_uniform.item()


def make_rollout(model: CommonRecurrentActorCritic, update: int = 0) -> EpisodeRollout:
    shape = (EPISODES_PER_ROLLOUT, EPISODE_TRANSITIONS)
    observations = torch.zeros((*shape, 168), dtype=torch.float32)
    # A deterministic, arm-independent primitive signal at the first row gives
    # the BPTT test a nonzero recurrent path without invoking any environment.
    observations[:, 0, 0] = torch.arange(1, 9, dtype=torch.float32) / 8.0
    decisions = torch.zeros(shape, dtype=torch.bool)
    decisions[:, 12::6] = True
    actions = torch.full(shape, WAIT, dtype=torch.int64)
    actions[decisions] = SERVE
    rewards = torch.zeros(shape, dtype=torch.float32)
    rewards[:, 12::6] = -0.4
    rewards[:, 13::6] = 1.0
    terminated = torch.zeros(shape, dtype=torch.bool)
    terminated[:, -1] = True
    with torch.no_grad():
        sequence = model.forward_episode(observations)
        old_log_probabilities = torch.zeros(shape, dtype=torch.float32)
        legal = torch.log_softmax(sequence.logits[decisions][:, 1:4], dim=-1)
        old_log_probabilities[decisions] = legal[:, 0]
        old_values = sequence.values.detach().clone()
    episode_ids = torch.arange(update * 8, update * 8 + 8, dtype=torch.int64)
    return EpisodeRollout(
        observations,
        actions,
        rewards,
        terminated,
        decisions,
        old_log_probabilities,
        old_values,
        episode_ids,
    )


def test_gae_keeps_delayed_settlement_terminal_zero_and_normalizes_decisions_once() -> None:
    model = CommonRecurrentActorCritic(1, address_u64=lambda _: 1 << 63)
    rollout = make_rollout(model)
    rewards = torch.zeros_like(rollout.rewards)
    rewards[:, 12] = -0.4
    rewards[:, 13] = 1.0
    zero_value_rollout = replace(
        rollout, rewards=rewards, old_values=torch.zeros_like(rollout.old_values)
    )
    computed = compute_gae(zero_value_rollout)
    expected_decision = torch.tensor(-0.4 + 0.95, dtype=torch.float32)
    torch.testing.assert_close(computed.advantages[:, 12], expected_decision.expand(8))
    torch.testing.assert_close(computed.advantages[:, 13], torch.ones(8))
    assert torch.count_nonzero(computed.decision_advantages[~rollout.decision_mask]).item() == 0
    decision_advantages = computed.decision_advantages[rollout.decision_mask]
    assert abs(float(decision_advantages.mean().item())) < 1e-6
    assert torch.equal(computed.value_targets, computed.advantages)


def test_order_is_external_exact_fisher_yates_and_has_no_arm_component() -> None:
    addresses: list[tuple] = []

    def u64(address) -> int:
        addresses.append(tuple(address))
        return canonical_u64(address)

    order, accepted = ordered_episode_indices("CBSC-OMRC-B0-INSTRUMENT", 21001, 0, 0, address_u64=u64)
    assert sorted(order) == list(range(8))
    assert len(accepted) == 7
    assert all(address[:2] == ("CBSC-OMRC-B01", "ORDER") for address in accepted)
    assert all(len(address) == 8 and address[2] == "CBSC-OMRC-B0-INSTRUMENT" for address in accepted)
    assert all("STRUCT" not in address and "RAW" not in address for address in accepted)


def test_full_episode_bptt_and_exact_update_counters(
    initialized_model: CommonRecurrentActorCritic, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = initialized_model
    rollout = make_rollout(model)
    sequence = model.forward_episode(rollout.observations[:2])
    assert sequence.logits.shape == (2, 152, 4)
    assert sequence.values.shape == (2, 152)
    late_loss = sequence.values[:, -1].sum()
    model.zero_grad(set_to_none=True)
    late_loss.backward()
    assert model.input_weight.grad is not None
    assert torch.count_nonzero(model.input_weight.grad[:, 0]).item() > 0

    trainer = RecurrentPPOTrainer(model, run_name="CBSC-OMRC-B0-INSTRUMENT", seed=21001)
    calls: list[tuple[int, int, tuple[int, ...], tuple[int, ...]]] = []

    def bounded_minibatch(rollout_arg, advantages, epoch, minibatch, selected):
        calls.append((epoch, minibatch, selected, tuple(rollout_arg.observations.shape)))
        return PPOLossRecord(epoch, minibatch, tuple(selected), 0.0, 0.0, 0.0, 0.0, 0.0)

    monkeypatch.setattr(trainer, "_train_minibatch", bounded_minibatch)
    records = trainer.train_rollout(rollout)
    assert len(records) == len(calls) == ADAM_STEPS_PER_UPDATE == 16
    assert all(call[3] == (8, 152, 168) and len(call[2]) == 2 for call in calls)
    assert trainer.counters.rollout_updates == 1
    assert trainer.counters.adam_steps == 16
    assert trainer.counters.train_episodes == 8
    assert trainer.counters.train_transitions == 1216
    assert trainer.counters.train_decisions == 192


def test_adam_is_fp32_zero_initialized_with_frozen_hyperparameters(
    initialized_model: CommonRecurrentActorCritic,
) -> None:
    optimizer = make_adam(initialized_model)
    assert optimizer.defaults["lr"] == 3e-4
    assert optimizer.defaults["betas"] == (0.9, 0.999)
    assert optimizer.defaults["eps"] == 1e-8
    assert optimizer.defaults["weight_decay"] == 0.0
    for parameter in initialized_model.parameters():
        state = optimizer.state[parameter]
        assert state["step"].dtype == torch.float32 and state["step"].item() == 0
        assert state["exp_avg"].dtype == torch.float32 and not state["exp_avg"].any().item()
        assert state["exp_avg_sq"].dtype == torch.float32 and not state["exp_avg_sq"].any().item()


def test_checkpoint_roundtrip_restores_exact_model_adam_counters_and_digests(tmp_path) -> None:
    model = CommonRecurrentActorCritic(21001, address_u64=lambda _: 1 << 63)
    trainer = RecurrentPPOTrainer(model, run_name="CBSC-OMRC-B0-INSTRUMENT", seed=21001)
    # Create nonzero but valid persistent state without executing a scientific rollout.
    parameter = next(model.parameters())
    parameter.grad = torch.ones_like(parameter)
    trainer.optimizer.step()
    trainer.optimizer.zero_grad(set_to_none=True)
    trainer.counters.rollout_updates = 1
    trainer.counters.adam_steps = 16
    trainer.counters.train_episodes = 8
    trainer.counters.train_transitions = 1216
    trainer.counters.train_decisions = 192
    trainer.restore_minibatch_order_digest(hashlib.sha256(b"order").hexdigest())
    tape_digest = hashlib.sha256(b"tape").hexdigest()
    action_digest = hashlib.sha256(b"action").hexdigest()
    payload = capture_checkpoint(
        trainer,
        arm="STRUCT-CURRENTNESS-GRU",
        training_tape_digest=tape_digest,
        action_uniform_digest=action_digest,
    )
    assert "hidden" not in payload and "adapter_state" not in payload
    path = tmp_path / "checkpoint.pt"
    save_checkpoint(path, payload)
    with pytest.raises(FileExistsError):
        save_checkpoint(path, payload)
    loaded = load_checkpoint(path)

    resumed_model = CommonRecurrentActorCritic(21001, address_u64=lambda _: 1 << 63)
    resumed = RecurrentPPOTrainer(
        resumed_model, run_name="CBSC-OMRC-B0-INSTRUMENT", seed=21001
    )
    restore_checkpoint(
        loaded,
        resumed,
        expected_arm="STRUCT-CURRENTNESS-GRU",
        expected_training_tape_digest=tape_digest,
        expected_action_uniform_digest=action_digest,
    )
    assert model_parameter_digest(resumed_model) == model_parameter_digest(model)
    assert resumed.optimizer.state_dict()["state"].keys() == trainer.optimizer.state_dict()["state"].keys()
    for key, state in trainer.optimizer.state_dict()["state"].items():
        for state_name, value in state.items():
            other = resumed.optimizer.state_dict()["state"][key][state_name]
            assert torch.equal(value, other)
    assert resumed.counters == trainer.counters
    assert resumed.minibatch_order_digest == trainer.minibatch_order_digest
    assert loaded["digests"]["configuration"] == config_digest(trainer.config)

    bad = dict(loaded)
    bad["digests"] = dict(loaded["digests"], training_tape=hashlib.sha256(b"other").hexdigest())
    with pytest.raises(CheckpointValidationError, match="digest mismatch"):
        restore_checkpoint(
            bad,
            resumed,
            expected_arm="STRUCT-CURRENTNESS-GRU",
            expected_training_tape_digest=tape_digest,
            expected_action_uniform_digest=action_digest,
        )


def test_authoritative_modules_have_no_q_learning_replay_or_framework_gru_imports() -> None:
    import experiments.candidates.capability_bound_semantic_currentness.omrc_b01.model as model_module
    import experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo as ppo_module

    sources = inspect.getsource(model_module) + inspect.getsource(ppo_module)
    assert "RecurrentQLearner" not in sources
    assert "BoundedReplay" not in sources
    assert "OnlineQTrainer" not in sources
    assert "nn.GRU(" not in sources and "nn.GRUCell(" not in sources
