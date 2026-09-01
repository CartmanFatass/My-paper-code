from __future__ import annotations

import copy

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.online import (
    PERFORMANCE_DISPOSITION,
    OnlineQTrainer,
    PotentialOutcomeTape,
    PredictiveStep,
    RecurrentQLearner,
    TapeValidationError,
    TrainerConfig,
    TrainerValidationError,
    VectorizedPotentialOutcomeBatch,
    evaluate_adaptation_free,
)


def fixture_tape(*, batch: int = 4, horizon: int = 6) -> PotentialOutcomeTape:
    feature_dim, actions = 3, 2
    observation = torch.arange(batch * horizon * feature_dim, dtype=torch.float32).reshape(
        batch, horizon, feature_dim
    ) / 100.0
    next_observation = torch.empty((batch, horizon, actions, feature_dim), dtype=torch.float32)
    next_observation[:, :, 0] = observation + 1.0
    next_observation[:, :, 1] = observation - 1.0
    action_reward = torch.stack(
        (
            observation[:, :, 0] + 0.25,
            -observation[:, :, 0] - 0.5,
        ),
        dim=2,
    )
    terminated = torch.zeros((batch, horizon, actions), dtype=torch.bool)
    terminated[:, 2, 1] = True
    terminated[:, -1, :] = True
    return PotentialOutcomeTape(observation, action_reward, next_observation, terminated)


def fixture_config() -> TrainerConfig:
    # These are deliberately local engineering-fixture values, not a study contract.
    return TrainerConfig(
        replay_capacity=64,
        batch_size=4,
        warmup_interactions=4,
        learning_rate=1.0e-3,
        gamma=0.9,
        epsilon=0.35,
        gradient_clip_norm=5.0,
    )


def clone_tensor_tree(value):
    if isinstance(value, torch.Tensor):
        return value.clone()
    if isinstance(value, dict):
        return {key: clone_tensor_tree(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clone_tensor_tree(item) for item in value]
    if isinstance(value, tuple):
        return tuple(clone_tensor_tree(item) for item in value)
    return copy.deepcopy(value)


def assert_tensor_tree_equal(left, right) -> None:
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor)
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            assert_tensor_tree_equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert type(left) is type(right) and len(left) == len(right)
        for a, b in zip(left, right):
            assert_tensor_tree_equal(a, b)
    else:
        assert left == right


def test_tape_strict_shape_dtype_and_finite_validation() -> None:
    tape = fixture_tape()
    assert (tape.batch_size, tape.horizon, tape.feature_dim, tape.action_count) == (4, 6, 3, 2)
    with pytest.raises(TapeValidationError, match="float32"):
        PotentialOutcomeTape(
            tape.observation.double(),
            tape.action_reward,
            tape.next_observation,
            tape.terminated,
        )
    broken = tape.next_observation.clone()
    broken[0, 0, 0, 0] = torch.nan
    with pytest.raises(TapeValidationError, match="finite"):
        PotentialOutcomeTape(tape.observation, tape.action_reward, broken, tape.terminated)
    with pytest.raises(TapeValidationError, match="shape"):
        PotentialOutcomeTape(
            tape.observation,
            tape.action_reward,
            tape.next_observation[:, :, :, :2],
            tape.terminated,
        )


def test_tape_digest_changes_with_same_shape_content() -> None:
    tape = fixture_tape()
    altered_reward = tape.action_reward.clone()
    altered_reward[0, 0, 0] += 1.0
    altered = PotentialOutcomeTape(
        tape.observation.clone(),
        altered_reward,
        tape.next_observation.clone(),
        tape.terminated.clone(),
    )
    assert len(tape.content_digest) == 64
    assert tape.content_digest != altered.content_digest


def test_batched_gather_carries_chosen_transition_and_resets_only_terminated_lane() -> None:
    tape = fixture_tape(batch=2, horizon=3)
    host = VectorizedPotentialOutcomeBatch(tape)
    first_action = torch.tensor((0, 1), dtype=torch.int64)
    # Make just the second selected branch terminal at the first opportunity.
    tape.terminated[1, 0, 1] = True
    first = host.step(first_action)
    expected_next = torch.stack((tape.next_observation[0, 0, 0], tape.next_observation[1, 0, 1]))
    torch.testing.assert_close(first.next_observation, expected_next, rtol=0.0, atol=0.0)
    expected_current = torch.stack((expected_next[0], tape.observation[1, 1]))
    torch.testing.assert_close(host.observation(), expected_current, rtol=0.0, atol=0.0)

    saved = host.state_dict()
    restored = VectorizedPotentialOutcomeBatch(tape)
    restored.load_state_dict(saved)
    torch.testing.assert_close(restored.observation(), expected_current, rtol=0.0, atol=0.0)
    second_action = torch.tensor((1, 0), dtype=torch.int64)
    actual = restored.step(second_action)
    # Later rows are open-loop potential outcomes; terminated resets state but
    # does not remove the lane from this subsequent opportunity.
    assert actual.reward.shape == (2,)
    assert restored.cursor == 2


def test_recurrent_learner_is_fp32_and_epsilon_action_uses_explicit_rng_deterministically() -> None:
    torch.manual_seed(7)
    learner = RecurrentQLearner(feature_dim=3, action_count=2, hidden_dim=5)
    assert all(parameter.dtype == torch.float32 for parameter in learner.parameters())
    observation = torch.linspace(-1.0, 1.0, 12, dtype=torch.float32).reshape(4, 3)
    hidden = learner.initial_state(4)
    left_rng = torch.Generator(device="cpu").manual_seed(991)
    right_rng = torch.Generator(device="cpu").manual_seed(991)
    left = learner.epsilon_action(observation, hidden, epsilon=0.65, generator=left_rng)
    right = learner.epsilon_action(observation, hidden, epsilon=0.65, generator=right_rng)
    assert torch.equal(left.action, right.action)
    assert torch.equal(left.next_state, right.next_state)
    assert left.action.dtype == torch.int64


def test_online_fixture_produces_nonzero_interactions_and_updates_with_bounded_replay() -> None:
    torch.manual_seed(11)
    tape = fixture_tape()
    learner = RecurrentQLearner(3, 2, 7)
    trainer = OnlineQTrainer(
        learner,
        fixture_config(),
        torch.Generator(device="cpu").manual_seed(12),
    )
    before = {name: value.clone() for name, value in learner.state_dict().items()}
    receipt = trainer.run(tape)
    assert receipt.interactions == tape.batch_size * tape.horizon
    assert receipt.updates > 0
    assert receipt.mean_loss is not None and receipt.mean_loss >= 0.0
    assert trainer.replay.size <= trainer.config.replay_capacity
    assert any(not torch.equal(before[name], value) for name, value in learner.state_dict().items())
    assert trainer.hidden is not None and torch.count_nonzero(trainer.hidden).item() == 0
    assert receipt.performance_disposition == "PILOT_ONLY"


class FixedPredictivePolicy:
    def __init__(self) -> None:
        self.weight = torch.tensor((1.0, -1.0, 0.5), dtype=torch.float32)

    def initial_state(self, batch_size: int, device=None) -> torch.Tensor:
        return torch.zeros((batch_size, 1), dtype=torch.float32, device=device)

    def state_dict(self) -> dict[str, torch.Tensor]:
        return {"weight": self.weight}

    def predict(self, observation: torch.Tensor, state: torch.Tensor) -> PredictiveStep:
        score = observation @ self.weight.to(observation.device)
        return PredictiveStep(action=(score < 0).to(torch.int64), next_state=state + 0.25)


@pytest.mark.parametrize("kind", ("learner", "fixed"))
def test_adaptation_free_evaluator_supports_both_interfaces_without_state_mutation(kind: str) -> None:
    tape = fixture_tape()
    if kind == "learner":
        torch.manual_seed(21)
        policy = RecurrentQLearner(3, 2, 5)
        initial = policy.initial_state(tape.batch_size)
        model_before = {name: value.clone() for name, value in policy.state_dict().items()}
    else:
        policy = FixedPredictivePolicy()
        initial = policy.initial_state(tape.batch_size)
        model_before = None
    initial_before = initial.clone()
    receipt = evaluate_adaptation_free(tape, policy, initial_state=initial)
    assert receipt.interactions == tape.batch_size * tape.horizon
    assert receipt.returns.dtype == torch.float32
    assert receipt.model_unchanged and receipt.input_state_unchanged
    assert torch.equal(initial, initial_before)
    if model_before is not None:
        assert all(torch.equal(value, policy.state_dict()[name]) for name, value in model_before.items())


def test_adaptation_free_evaluator_restores_training_mode_when_state_validation_fails() -> None:
    tape = fixture_tape()
    policy = RecurrentQLearner(3, 2, 5)
    policy.train()
    invalid_state = torch.zeros((tape.batch_size,), dtype=torch.float32)
    with pytest.raises(TapeValidationError, match="shape"):
        evaluate_adaptation_free(tape, policy, initial_state=invalid_state)
    assert policy.training


def test_checkpoint_resume_is_exact_including_chosen_current_state_replay_optimizer_and_rng() -> None:
    tape = fixture_tape()
    torch.manual_seed(31)
    template = RecurrentQLearner(3, 2, 6)
    initial_model = clone_tensor_tree(template.state_dict())

    left_model = RecurrentQLearner(3, 2, 6)
    left_model.load_state_dict(initial_model)
    left = OnlineQTrainer(
        left_model,
        fixture_config(),
        torch.Generator(device="cpu").manual_seed(32),
    )
    partial = left.run(tape, max_steps=3)
    assert partial.cursor == 3
    checkpoint = clone_tensor_tree(left.state_dict())
    assert not torch.equal(checkpoint["current_observation"], tape.observation[:, 3])

    right_model = RecurrentQLearner(3, 2, 6)
    right = OnlineQTrainer(
        right_model,
        fixture_config(),
        torch.Generator(device="cpu").manual_seed(999),
    )
    right.load_state_dict(checkpoint)
    left_receipt = left.run(tape)
    right_receipt = right.run(tape)
    assert left_receipt == right_receipt
    assert_tensor_tree_equal(left.state_dict(), right.state_dict())

    altered_reward = tape.action_reward.clone()
    altered_reward[0, 0, 0] += 1.0
    same_shape_different_content = PotentialOutcomeTape(
        tape.observation.clone(),
        altered_reward,
        tape.next_observation.clone(),
        tape.terminated.clone(),
    )
    with pytest.raises(TrainerValidationError, match="different tape content"):
        right.run(same_shape_different_content)


def test_performance_claim_is_explicitly_pilot_only() -> None:
    assert PERFORMANCE_DISPOSITION == "PILOT_ONLY"
