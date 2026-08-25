from __future__ import annotations

import json

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from experiments.candidates.eociv_lite import payload_content_learnability as b2
from experiments.candidates.eociv_lite import real_valve_learning as b1
from experiments.candidates.eociv_lite import host_reward_snr_discrimination as b5
from experiments.candidates.eociv_lite import sibling_env as sib


def _actor(seed: int = 87031) -> b1.RecurrentActorCritic:
    return b1.RecurrentActorCritic(
        b5.PROFILES[0].member_capacity, seed, encoder_kind="content_separating"
    )


def test_registered_plans_counts_namespaces_and_block_order_are_exact() -> None:
    assert b5.FULL_PLAN.training_episodes == 576
    assert b5.FULL_PLAN.optimizer_updates == 144
    assert b5.FULL_PLAN.training_transitions == 27_648
    assert b5.FULL_PLAN.evaluation_episodes == 648
    assert b5.FULL_PLAN.evaluation_transitions == 31_104
    assert b5.FULL_PLAN.maximum_transitions == 58_752
    assert b5.SMOKE_PLAN.training_episodes == 24
    assert b5.SMOKE_PLAN.optimizer_updates == 6
    assert b5.SMOKE_PLAN.training_transitions == 1_152
    assert b5.SMOKE_PLAN.evaluation_episodes == 54
    assert b5.SMOKE_PLAN.evaluation_transitions == 2_592
    assert b5.SMOKE_PLAN.maximum_transitions == 3_744
    assert b5.SMOKE_PLAN.mid_update == 2

    identities = {
        stage: b5.episode_id(stage, 2, 1, 3)
        for stage in ("train", *b5.CHECKPOINTS)
    }
    assert identities == {
        "train": 14_210_003,
        "INIT": 15_210_003,
        "MID": 16_210_003,
        "FINAL": 17_210_003,
    }
    assert not set(identities.values()) & set(range(10_000_000, 14_000_000))
    order = [
        (root, profile.name)
        for root in range(b5.FULL_PLAN.blocks_per_profile)
        for profile in b5.PROFILES
    ]
    assert order[:6] == [
        (0, "train_4_3_6_5"), (0, "train_5_3_7_6"), (0, "train_6_4_8_6"),
        (1, "train_4_3_6_5"), (1, "train_5_3_7_6"), (1, "train_6_4_8_6"),
    ]


def test_balanced_order_and_iid_tape_are_frozen_with_repeats_allowed() -> None:
    assert b5.shock_tuples_for_block(
        "BALANCED_SHOCK_BLOCK", 87031, b5.PROFILES[0].name, 0
    ) == b5.CRITICAL_TUPLES
    first = b5.shock_tuples_for_block(
        "IID_SHOCK_BLOCK", 87031, b5.PROFILES[0].name, 0
    )
    second = b5.shock_tuples_for_block(
        "IID_SHOCK_BLOCK", 87031, b5.PROFILES[0].name, 0
    )
    assert first == second
    assert first == (
        (sib.SHOCK_B, sib.SHOCK_B),
        (sib.SHOCK_B, sib.SHOCK_B),
        (sib.SHOCK_A, sib.SHOCK_B),
        (sib.SHOCK_A, sib.SHOCK_B),
    )
    assert all(len(value) == 2 and set(value) <= {sib.SHOCK_A, sib.SHOCK_B} for value in first)
    # IID sampling is with replacement; the interface does not impose exact enumeration.
    assert len(set(first)) < len(first)


def test_explicit_training_shock_changes_only_hidden_tuple_not_public_root_or_tape() -> None:
    profile = b5.PROFILES[0]
    registered_id = b5.episode_id("train", 0, 0, 0)
    left = b5._make_runner(_actor(), profile, registered_id, b2._correct_body, (sib.SHOCK_A, sib.SHOCK_A))
    right = b5._make_runner(_actor(), profile, registered_id, b2._correct_body, (sib.SHOCK_B, sib.SHOCK_B))
    assert left.env._shock_states == (sib.SHOCK_A, sib.SHOCK_NONE, sib.SHOCK_A)
    assert right.env._shock_states == (sib.SHOCK_B, sib.SHOCK_NONE, sib.SHOCK_B)
    assert b5.public_world_digest(left.env) == b5.public_world_digest(right.env)
    assert b5.lifecycle_digest(left) == b5.lifecycle_digest(right)
    assert b5.action_noise_digest(left) == b5.action_noise_digest(right)
    assert left.env.ledger.episode_id == right.env.ledger.episode_id


def test_hand_checkable_four_vector_gradient_moments_are_exact() -> None:
    vectors = [
        torch.tensor([1.0, 0.0]),
        torch.tensor([-1.0, 0.0]),
        torch.tensor([0.0, 1.0]),
        torch.tensor([0.0, -1.0]),
    ]
    result = b5.gradient_moments_from_vectors(vectors)
    assert result["signal_sq"] == pytest.approx(0.0)
    assert result["noise_sq"] == pytest.approx(1.0)
    assert result["snr"] == pytest.approx(0.0)
    assert result["episode_contribution_norms"] == pytest.approx([1.0] * 4)

    shifted = b5.gradient_moments_from_vectors(
        [torch.tensor([1.0, 0.0]), torch.tensor([3.0, 0.0]),
         torch.tensor([1.0, 0.0]), torch.tensor([3.0, 0.0])]
    )
    assert shifted["signal_sq"] == pytest.approx(4.0)
    assert shifted["noise_sq"] == pytest.approx(1.0)
    assert shifted["snr"] == pytest.approx(4.0)


def test_autograd_moments_leave_grad_untouched_and_zero_missing_contributions() -> None:
    actor_parameter = torch.nn.Parameter(torch.tensor([1.0, -2.0]))
    critic_only = torch.nn.Parameter(torch.tensor([5.0]))
    losses = [factor * actor_parameter.square().sum() for factor in (1.0, 2.0, 3.0, 4.0)]
    result = b5._gradient_moments(losses, (actor_parameter, critic_only))
    assert actor_parameter.grad is None
    assert critic_only.grad is None
    assert np.isfinite(result["snr"])
    assert len(result["episode_contribution_norms"]) == 4


def test_one_block_uses_exactly_one_optimizer_step_and_clip_and_preserves_b4_gae(monkeypatch) -> None:
    class CountingAdam(torch.optim.Adam):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.step_count = 0

        def step(self, closure=None):
            self.step_count += 1
            return super().step(closure)

    actor = _actor()
    optimizer = CountingAdam(actor.parameters(), lr=b1.ACTOR_LR)
    clip_count = 0
    original_clip = torch.nn.utils.clip_grad_norm_

    def counted_clip(*args, **kwargs):
        nonlocal clip_count
        clip_count += 1
        return original_clip(*args, **kwargs)

    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", counted_clip)
    row = b5._train_block(
        actor, optimizer, "BALANCED_SHOCK_BLOCK", 87031, b5.PROFILES[0],
        b5.episode_id("train", 0, 0, 0), 0,
    )
    assert optimizer.step_count == 1
    assert clip_count == 1
    assert row["optimizer_steps"] == row["clip_calls"] == 1
    assert len(row["episodes"]) == 4
    assert row["shock_tuples"] == [list(value) for value in b5.CRITICAL_TUPLES]
    assert all(row["matching"].values())
    assert not row["nonfinite"]

    probe_actor = _actor(87032)
    probe_actor.set_capture(True)
    runner = b5._make_runner(
        probe_actor, b5.PROFILES[0], b5.episode_id("train", 0, 0, 1),
        b2._correct_body, (sib.SHOCK_A, sib.SHOCK_B),
    )
    actor_loss, critic_loss, parts = b5._episode_loss_tensors(probe_actor, runner.env.reward_trace)
    b4_loss, b4_parts = probe_actor.episode_loss_gae_norm(
        runner.env.reward_trace, gae_lambda=b5.GAE_LAMBDA,
        normalization_epsilon=b5.NORMALIZATION_EPSILON,
    )
    assert float(actor_loss + 0.5 * critic_loss) == pytest.approx(float(b4_loss))
    assert {key: parts[key] for key in b4_parts} == pytest.approx(b4_parts)
    assert np.isfinite(parts["value_target_mean"])
    assert np.isfinite(parts["value_target_population_std"])
    assert parts["value_target_population_std"] >= 0.0


def test_registered_smoke_is_real_matched_complete_and_canonical() -> None:
    first = b5.run_experiment("smoke")
    second = b5.run_experiment("smoke")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["mechanical_status"] == "MECHANICAL_B5_COMPLETE"
    assert first["scientific_disposition"] is None
    assert first["registered_c_outcome_experiment_licensed"] is False
    assert first["counts"] == {
        "environment_transitions": 3_744,
        "policy_calls": 3_744,
        "learner_episodes": 24,
        "trainer_blocks": 6,
        "optimizer_updates": 6,
        "clip_calls": 6,
        "training_episodes": 24,
        "evaluation_episodes": 54,
    }
    assert all(first["matching_proof"].values())
    assert len(first["actors"]) == 2
    assert all(len(actor["training_blocks"]) == 3 for actor in first["actors"])
    assert len(first["evaluation_rows"]) == 18
    assert len(first["paired_balanced_minus_iid_final_minus_init_cells"]) == 3
    assert len(first["snr_summaries"]) == 6
    assert len(first["paired_snr_differences"]) == 3
    assert len(first["final_lag_4_to_11_retention_confirmation"]) == 24
    assert first["gradient_and_critic_summary"]["all_finite"]
    for actor in first["actors"]:
        for block in actor["training_blocks"]:
            for episode in block["episodes"]:
                assert np.isfinite(episode["value_target_mean"])
                assert np.isfinite(episode["value_target_population_std"])
    for row in first["evaluation_rows"]:
        assert all(row["matching"].values())
        assert set(row["arms"]) == set(b5.EVALUATION_ARMS)
        assert row["natural_shock_tuple"][1] == sib.SHOCK_NONE
