import numpy as np
import torch

from experiments.candidates.uav_service_age.b01.learner import (
    Learner, actor_objective, finite_returns, innovations, parameter_digest,
)
from experiments.candidates.uav_service_age.b01.metrics import actual_ages, add_age_raw


def test_actual_age_and_report_reward_partition_including_boundaries():
    served = np.ones((256, 50), dtype=bool)
    served[:, 0] = False
    served[1:7, 1] = False
    served[253:, 2] = False
    age = actual_ages(served)
    np.testing.assert_array_equal(age[:, 0], np.arange(1, 257))
    np.testing.assert_array_equal(age[:8, 1], [0, 1, 2, 3, 4, 5, 6, 0])
    assert age[:, 0].sum() == 256 * 257 // 2
    assert age[253:, 2].sum() == 6
    raw = {'connections': served[:, None, :]}
    add_age_raw(raw, 256)
    assert len(raw['report_rewards']) == 64
    np.testing.assert_allclose(raw['report_rewards'].sum(), -age.mean(), atol=1e-14)
    np.testing.assert_allclose(finite_returns(raw['report_rewards'])[0], -age.mean(), atol=1e-14)


def test_fixed_64_actor_and_entropy_denominator_without_whitening():
    logits = torch.zeros((64, 2), requires_grad=True)
    choices = torch.zeros(64, dtype=torch.long)
    old = torch.full((64,), -np.log(2), dtype=torch.float32)
    advantage = torch.full((64,), 3.)
    sampled = torch.zeros(64, dtype=torch.bool)
    sampled[0] = True
    loss, policy, entropy = actor_objective(logits, choices, old, advantage, sampled)
    torch.testing.assert_close(policy, torch.tensor(-3. / 64))
    torch.testing.assert_close(entropy, torch.tensor(np.log(2) / 64, dtype=torch.float32))
    loss.backward()
    assert torch.count_nonzero(logits.grad[1:]) == 0


def test_initial_mixture_zero_effective_episode_and_actual_optimizer_movement():
    learner = Learner(5, seed=701)
    features = np.zeros((64, 5), np.float32)
    features[:, 0] = np.linspace(0, 1, 64)
    np.testing.assert_array_equal(learner.probabilities(features[0]), [.5, .5])
    before = parameter_digest(learner.actor)
    rewards = -np.arange(1, 65) / 6400
    info, saved = learner.update(features, np.full(64, -1), np.full(64, np.nan),
                                 np.zeros(64, bool), rewards)
    assert info['actor_updates'] == 0 and info['critic_updates'] == 4
    assert parameter_digest(learner.actor) == before
    assert info['critic_displacement'] > 0
    assert info['denominator'] == 64
    choices = np.arange(64) % 2
    info, saved = learner.update(features, choices, np.full(64, -np.log(2)),
                                 np.ones(64, bool), rewards)
    assert info['actor_updates'] == 4 and learner.critic_updates == 8
    assert info['actor_displacement'] > 0
    np.testing.assert_allclose(saved['returns'][0], rewards.sum())


def test_clock_addressed_common_innovations_do_not_shift_for_alias():
    left = innovations(705, training=False)
    right = innovations(705, training=False)
    # L0 and L1 may have different aliases but each samples from the same clock index.
    for slot in (0, 5, 17, 63):
        assert left[slot] == right[slot]
    assert not np.array_equal(left, innovations(705, training=True))
    assert not np.array_equal(left, innovations(706, training=False))
