from dataclasses import dataclass

import numpy as np
import torch

from ha_ctse_process.situation_transition import (
    SituationTransitionPredictor,
    TeamTransitionInterval,
    attribute_interval_rewards_to_segments,
    reward_is_active,
    scaled_clipped_residual,
    skill_count_vector,
    valid_transition_mask,
)


@dataclass
class DummySegment:
    env_id: int
    rollout_indices: list[int]
    rewards: list[float]


def test_predictor_input_boundary_is_kappa_plus_skill_counts_only():
    predictor = SituationTransitionPredictor(num_situations=4, n_skills=6, hidden_dim=16)

    assert predictor.kappa_embedding.num_embeddings == 4
    assert predictor.prior_head[1].in_features == 16
    assert predictor.posterior_head[1].in_features == 16 + 6

    kappa = torch.tensor([0, 1])
    xi = torch.zeros(2, 6)
    posterior_logits, prior_logits = predictor(kappa, xi)
    assert posterior_logits.shape == (2, 4)
    assert prior_logits.shape == (2, 4)


def test_losses_detach_xi_so_head_training_does_not_backprop_to_policy_source():
    predictor = SituationTransitionPredictor(num_situations=4, n_skills=3, hidden_dim=8)
    policy_source = torch.nn.Parameter(torch.ones(1, 3))
    xi = policy_source.expand(4, -1)
    kappa = torch.tensor([0, 1, 2, 3])
    kappa_next = torch.tensor([1, 1, 2, 0])

    terms = predictor.losses(kappa, xi, kappa_next)
    (terms["posterior_loss"] + terms["prior_loss"]).backward()

    assert policy_source.grad is None
    assert any(param.grad is not None for param in predictor.parameters())


def test_policy_reward_use_does_not_update_predictor_parameters():
    predictor = SituationTransitionPredictor(num_situations=4, n_skills=3, hidden_dim=8)
    before = [param.detach().clone() for param in predictor.parameters()]
    policy_param = torch.nn.Parameter(torch.tensor([1.0]))
    opt = torch.optim.SGD([policy_param], lr=0.1)

    reward = predictor.reward(
        torch.tensor([0, 1]),
        torch.zeros(2, 3),
        torch.tensor([1, 2]),
        coef=0.05,
        clip=2.0,
    )
    loss = -(reward.detach().mean() * policy_param)
    opt.zero_grad()
    loss.backward()
    opt.step()

    after = list(predictor.parameters())
    assert all(torch.allclose(old, new.detach()) for old, new in zip(before, after))


def test_reward_guard_and_clip_before_coef():
    assert not reward_is_active(True, False, total_steps=100000, warmup_steps=0, coef=0.05)
    assert not reward_is_active(True, True, total_steps=1000, warmup_steps=2000, coef=0.05)
    assert not reward_is_active(True, True, total_steps=100000, warmup_steps=0, coef=0.0)
    assert reward_is_active(True, True, total_steps=100000, warmup_steps=0, coef=0.05)

    residual = torch.tensor([-10.0, -1.0, 0.5, 10.0])
    reward = scaled_clipped_residual(residual, coef=0.05, clip=2.0)
    assert torch.allclose(reward, torch.tensor([-0.1, -0.05, 0.025, 0.1]))


def test_missing_kappa_dropped_and_self_change_split_partitions():
    mask = valid_transition_mask(
        np.asarray([0, -1, 2, 5]),
        np.asarray([0, 1, -1, 2]),
        num_situations=4,
    )
    assert mask.tolist() == [True, False, False, False]

    predictor = SituationTransitionPredictor(num_situations=4, n_skills=3, hidden_dim=8)
    terms = predictor.losses(
        torch.tensor([0, 1, 2, 3]),
        torch.zeros(4, 3),
        torch.tensor([0, 2, 2, 0]),
    )
    assert torch.isclose(terms["self_frac"], torch.tensor(0.5))
    assert terms["mi"].numel() == 4


def test_skill_counts_and_interval_attribution_are_permutation_invariant():
    assert skill_count_vector(np.asarray([2, 1, 2, 0]), 4).tolist() == [1.0, 1.0, 2.0, 0.0]

    intervals = [
        TeamTransitionInterval(env_id=0, start_step=0, end_step=10, kappa=0, xi=np.zeros(3), kappa_next=1),
        TeamTransitionInterval(env_id=1, start_step=0, end_step=10, kappa=1, xi=np.zeros(3), kappa_next=1),
    ]
    segments = [
        DummySegment(env_id=0, rollout_indices=[0, 5, 9], rewards=[1.0]),
        DummySegment(env_id=0, rollout_indices=[10, 11], rewards=[1.0]),
        DummySegment(env_id=1, rollout_indices=[4, 8], rewards=[1.0]),
    ]
    rewards, applied = attribute_interval_rewards_to_segments(
        intervals,
        np.asarray([0.25, -0.5], dtype=np.float32),
        segments,
    )
    assert applied == 2
    assert np.allclose(rewards, np.asarray([0.25, 0.0, -0.5], dtype=np.float32))
