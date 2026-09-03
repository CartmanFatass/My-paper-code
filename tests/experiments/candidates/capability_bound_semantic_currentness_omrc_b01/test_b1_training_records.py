from __future__ import annotations

from dataclasses import replace

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_training_records import (
    TrainingExposureRecords,
    TrainingRecordError,
    build_training_exposure_records,
    merge_training_exposure_slices,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.model import (
    CommonRecurrentActorCritic,
    SERVE,
    WAIT,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import (
    EPISODE_TRANSITIONS,
    EPISODES_PER_ROLLOUT,
    EpisodeRollout,
    PPOLossRecord,
    RecurrentPPOTrainer,
)


RUN = "CBSC-OMRC-B1-THREE-SEED-SCOUT"
ARM = "STRUCT-CURRENTNESS-GRU"
SEED = 21101


def _rollout(update: int = 0) -> EpisodeRollout:
    shape = (EPISODES_PER_ROLLOUT, EPISODE_TRANSITIONS)
    observations = torch.zeros((*shape, 168), dtype=torch.float32)
    decisions = torch.zeros(shape, dtype=torch.bool)
    decisions[:, 12::6] = True
    actions = torch.full(shape, WAIT, dtype=torch.int64)
    actions[decisions] = SERVE
    rewards = torch.zeros(shape, dtype=torch.float32)
    rewards[:, 12::6] = torch.tensor(-0.4, dtype=torch.float32)
    rewards[:, 13::6] = torch.tensor(1.0, dtype=torch.float32)
    terminated = torch.zeros(shape, dtype=torch.bool)
    terminated[:, -1] = True
    old_log_probabilities = torch.zeros(shape, dtype=torch.float32)
    old_log_probabilities[decisions] = torch.tensor(-1.25, dtype=torch.float32)
    return EpisodeRollout(
        observations=observations,
        actions=actions,
        rewards=rewards,
        terminated=terminated,
        decision_mask=decisions,
        old_log_probabilities=old_log_probabilities,
        old_values=torch.zeros(shape, dtype=torch.float32),
        episode_ids=torch.arange(update * 8, update * 8 + 8, dtype=torch.int64),
    )


def _optimizer_steps(update: int = 0) -> tuple[PPOLossRecord, ...]:
    rows: list[PPOLossRecord] = []
    for epoch in range(4):
        for minibatch in range(4):
            offset = 2 * minibatch
            rows.append(
                PPOLossRecord(
                    ppo_epoch=epoch,
                    minibatch=minibatch,
                    episode_ids=(update * 8 + offset, update * 8 + offset + 1),
                    actor_loss=0.25,
                    value_loss=0.5,
                    entropy=0.75,
                    total_loss=0.4925,
                    gradient_norm=0.6,
                    rollout_update=update,
                    postclip_gradient_norm=0.5,
                    optimizer_step_count=update * 16 + epoch * 4 + minibatch + 1,
                    parameter_sha256_after_step=f"{update * 16 + epoch * 4 + minibatch + 1:064x}",
                )
            )
    return tuple(rows)


def test_public_builder_emits_exact_canonical_training_rows() -> None:
    records = build_training_exposure_records(
        run_name=RUN,
        seed=SEED,
        arm=ARM,
        rollout_update=0,
        rollout=_rollout(),
        optimizer_steps=_optimizer_steps(),
    )
    payload = records.canonical_dict()
    assert tuple(payload) == ("training_decisions", "training_episodes", "optimizer_steps")
    assert len(payload["training_decisions"]) == 192
    assert len(payload["training_episodes"]) == 8
    assert len(payload["optimizer_steps"]) == 16
    assert payload["training_decisions"][0] == {
        "run_order": 0,
        "run_name": RUN,
        "seed": SEED,
        "arm_order": 0,
        "arm": ARM,
        "training_episode_id": 0,
        "opportunity_id": 0,
        "rollout_update": 0,
        "policy_version": 0,
        "selected_action": 0,
        "legal_mask": [False, True, True, True],
        "selected_log_probability": -1.25,
        "decision_reward": pytest.approx(-0.4),
        "settlement_reward": 1.0,
        "opportunity_return": pytest.approx(0.6),
    }
    assert payload["training_episodes"][0]["action_count_serve"] == 24
    assert payload["training_episodes"][0]["run_order"] == 0
    assert payload["training_episodes"][0]["arm_order"] == 0
    assert payload["training_episodes"][0]["episode_return"] == pytest.approx(14.4)
    step = payload["optimizer_steps"][0]
    assert step["run_order"] == 0 and step["arm_order"] == 0
    assert step["ordered_episode_ids"] == [0, 1]
    assert step["actor_loss_fp32_bits"] == "3e800000"
    assert step["preclip_gradient_norm_fp32_bits"] == "3f19999a"
    assert step["postclip_gradient_norm_fp32_bits"] == "3f000000"
    assert step["optimizer_step_count"] == 1


def test_resume_merge_rejects_duplicate_gap_nonfinite_and_non_fp32_rows() -> None:
    first = build_training_exposure_records(
        run_name=RUN,
        seed=SEED,
        arm=ARM,
        rollout_update=0,
        rollout=_rollout(0),
        optimizer_steps=_optimizer_steps(0),
    )
    second = build_training_exposure_records(
        run_name=RUN,
        seed=SEED,
        arm=ARM,
        rollout_update=1,
        rollout=_rollout(1),
        optimizer_steps=_optimizer_steps(1),
    )
    merged = merge_training_exposure_slices(
        (second, first), start_update=0, stop_update=2
    )
    assert [row["training_episode_id"] for row in merged.training_episodes] == list(range(16))
    assert [row["optimizer_step_count"] for row in merged.optimizer_steps] == list(range(1, 33))
    with pytest.raises(TrainingRecordError, match="duplicate"):
        merge_training_exposure_slices((first, first), start_update=0, stop_update=1)
    with pytest.raises(TrainingRecordError, match="coverage"):
        merge_training_exposure_slices((second,), start_update=0, stop_update=2)

    non_fp32_rows = first.canonical_dict()
    non_fp32_rows["training_decisions"][0]["selected_log_probability"] = 0.1
    non_fp32 = TrainingExposureRecords(
        tuple(non_fp32_rows["training_decisions"]),
        tuple(non_fp32_rows["training_episodes"]),
        tuple(non_fp32_rows["optimizer_steps"]),
    )
    with pytest.raises(TrainingRecordError, match="exact FP32"):
        merge_training_exposure_slices((non_fp32,), start_update=0, stop_update=1)

    mismatched_order_rows = first.canonical_dict()
    mismatched_order_rows["optimizer_steps"][0]["arm_order"] = 3
    mismatched_order = TrainingExposureRecords(
        tuple(mismatched_order_rows["training_decisions"]),
        tuple(mismatched_order_rows["training_episodes"]),
        tuple(mismatched_order_rows["optimizer_steps"]),
    )
    with pytest.raises(TrainingRecordError, match="order.*identity"):
        merge_training_exposure_slices((mismatched_order,), start_update=0, stop_update=1)

    nonfinite = replace(_rollout(), rewards=_rollout().rewards.clone())
    nonfinite.rewards[0, 12] = float("nan")
    with pytest.raises((TrainingRecordError, ValueError), match="nonfinite"):
        build_training_exposure_records(
            run_name=RUN,
            seed=SEED,
            arm=ARM,
            rollout_update=0,
            rollout=nonfinite,
            optimizer_steps=_optimizer_steps(),
        )


def test_real_trainer_exposes_postclip_norm_actual_adam_count_and_parameter_sha() -> None:
    model = CommonRecurrentActorCritic(SEED, address_u64=lambda _: 1 << 63)
    trainer = RecurrentPPOTrainer(
        model, run_name=RUN, seed=SEED, address_u64=lambda _: 1 << 63
    )
    rollout = _rollout()
    losses = trainer.train_rollout(rollout)
    records = build_training_exposure_records(
        run_name=RUN,
        seed=SEED,
        arm=ARM,
        rollout_update=0,
        rollout=rollout,
        optimizer_steps=losses,
    )
    assert len(losses) == 16
    assert [row.optimizer_step_count for row in losses] == list(range(1, 17))
    assert all(len(row.parameter_sha256_after_step) == 64 for row in losses)
    assert all(row.postclip_gradient_norm <= 0.5 for row in losses)
    assert records.optimizer_steps[-1]["parameter_sha256_after_step"] == losses[-1].parameter_sha256_after_step


def test_full_b1_training_coverage_is_exactly_384_9216_and_768_rows() -> None:
    chunks = tuple(
        build_training_exposure_records(
            run_name=RUN,
            seed=SEED,
            arm=ARM,
            rollout_update=update,
            rollout=_rollout(update),
            optimizer_steps=_optimizer_steps(update),
        )
        for update in range(48)
    )
    complete = merge_training_exposure_slices(
        tuple(reversed(chunks)),
        start_update=0,
        stop_update=48,
        require_full_b1=True,
    )
    assert len(complete.training_episodes) == 384
    assert len(complete.training_decisions) == 9_216
    assert len(complete.optimizer_steps) == 768
    assert complete.training_decisions[0]["training_episode_id"] == 0
    assert complete.training_decisions[-1]["training_episode_id"] == 383
    assert complete.optimizer_steps[-1]["optimizer_step_count"] == 768
