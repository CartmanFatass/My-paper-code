"""Lossless canonical B1 training-exposure records.

The raw rows in this module are publication facts, not scientific reductions.
They intentionally preserve the policy version used to collect each rollout
and the exact FP32 bit patterns observed at every Adam step.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Any, Iterable, Mapping, Sequence

import torch

from .b0 import ARMS
from .b1_contract import (
    B1_MINIBATCHES_PER_EPOCH,
    B1_PPO_EPOCHS,
    B1_ROLLOUT_UPDATES,
    B1_RUN_NAME,
)
from .contract import DECISION_ACTION_MASK, OPPORTUNITY_COUNT
from .model import SAFE_FALLBACK, SERVE
from .ppo import (
    ADAM_STEPS_PER_UPDATE,
    EPISODES_PER_ROLLOUT,
    EpisodeRollout,
    PPOLossRecord,
)


class TrainingRecordError(ValueError):
    """Raw training exposure is incomplete, duplicated, or not literal."""


_DECISION_KEYS = frozenset(
    {
        "run_order",
        "run_name",
        "seed",
        "arm_order",
        "arm",
        "training_episode_id",
        "opportunity_id",
        "rollout_update",
        "policy_version",
        "selected_action",
        "legal_mask",
        "selected_log_probability",
        "decision_reward",
        "settlement_reward",
        "opportunity_return",
    }
)
_EPISODE_KEYS = frozenset(
    {
        "run_order",
        "run_name",
        "seed",
        "arm_order",
        "arm",
        "training_episode_id",
        "rollout_update",
        "policy_version",
        "episode_return",
        "action_count_serve",
        "action_count_refresh",
        "action_count_safe_fallback",
    }
)
_OPTIMIZER_KEYS = frozenset(
    {
        "run_order",
        "run_name",
        "seed",
        "arm_order",
        "arm",
        "rollout_update",
        "ppo_epoch",
        "minibatch_index",
        "ordered_episode_ids",
        "actor_loss_fp32_bits",
        "value_loss_fp32_bits",
        "entropy_fp32_bits",
        "total_loss_fp32_bits",
        "preclip_gradient_norm_fp32_bits",
        "postclip_gradient_norm_fp32_bits",
        "optimizer_step_count",
        "parameter_sha256_after_step",
    }
)


def _fp32_value(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TrainingRecordError(f"{name} must be a finite FP32 value")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise TrainingRecordError(f"{name} contains a nonfinite value")
    rounded = struct.unpack(">f", struct.pack(">f", numeric))[0]
    if numeric != rounded:
        raise TrainingRecordError(f"{name} is not an exact FP32 value")
    return numeric


def _fp32_bits(name: str, value: object) -> str:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise TrainingRecordError(f"{name} contains a nonfinite value")
    return struct.pack(">f", numeric).hex()


def _validate_fp32_bits(name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 8
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TrainingRecordError(f"{name} must be eight lowercase FP32-bit hex digits")
    if not math.isfinite(struct.unpack(">f", bytes.fromhex(value))[0]):
        raise TrainingRecordError(f"{name} encodes a nonfinite value")
    return value


def _require_sha256(name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TrainingRecordError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _validate_identity(run_name: object, seed: object, arm: object) -> tuple[str, int, str]:
    if run_name != B1_RUN_NAME:
        raise TrainingRecordError("training run differs from frozen B1")
    if type(seed) is not int:
        raise TrainingRecordError("training seed must be an integer")
    if type(arm) is not str or arm not in ARMS:
        raise TrainingRecordError("training arm differs from frozen B1")
    return run_name, seed, arm


def _validate_order_identity(row: Mapping[str, Any]) -> None:
    if row.get("run_order") != 0 or row.get("arm_order") != ARMS.index(row["arm"]):
        raise TrainingRecordError("canonical order differs from string identity")


@dataclass(frozen=True)
class TrainingExposureRecords:
    """Canonical raw rows for one or more contiguous rollout updates."""

    training_decisions: tuple[dict[str, Any], ...]
    training_episodes: tuple[dict[str, Any], ...]
    optimizer_steps: tuple[dict[str, Any], ...]

    def canonical_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "training_decisions": [dict(row) for row in self.training_decisions],
            "training_episodes": [dict(row) for row in self.training_episodes],
            "optimizer_steps": [dict(row) for row in self.optimizer_steps],
        }


def build_training_exposure_records(
    *,
    run_name: str,
    seed: int,
    arm: str,
    rollout_update: int,
    rollout: EpisodeRollout,
    optimizer_steps: Sequence[PPOLossRecord],
) -> TrainingExposureRecords:
    """Expose one collected rollout and its 16 Adam steps without reduction."""

    _validate_identity(run_name, seed, arm)
    if type(rollout_update) is not int or not 0 <= rollout_update < B1_ROLLOUT_UPDATES:
        raise TrainingRecordError("rollout update is outside frozen B1")
    if not isinstance(rollout, EpisodeRollout):
        raise TrainingRecordError("training records require an EpisodeRollout")
    expected_episode_ids = tuple(
        range(
            rollout_update * EPISODES_PER_ROLLOUT,
            (rollout_update + 1) * EPISODES_PER_ROLLOUT,
        )
    )
    observed_episode_ids = tuple(int(value) for value in rollout.episode_ids.cpu().tolist())
    if observed_episode_ids != expected_episode_ids:
        raise TrainingRecordError("rollout episode coverage differs from frozen B1")

    decision_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    legal_mask = list(DECISION_ACTION_MASK)
    for episode_index, episode_id in enumerate(expected_episode_ids):
        action_counts = [0, 0, 0]
        for opportunity_id in range(OPPORTUNITY_COUNT):
            decision_index = 12 + 6 * opportunity_id
            settlement_index = decision_index + 1
            action = int(rollout.actions[episode_index, decision_index].item())
            if not SERVE <= action <= SAFE_FALLBACK:
                raise TrainingRecordError("training decision contains illegal WAIT/action")
            action_counts[action - SERVE] += 1
            log_probability = _fp32_value(
                "selected log probability",
                float(rollout.old_log_probabilities[episode_index, decision_index].item()),
            )
            decision_reward_tensor = rollout.rewards[episode_index, decision_index]
            settlement_reward_tensor = rollout.rewards[episode_index, settlement_index]
            opportunity_return_tensor = decision_reward_tensor + settlement_reward_tensor
            decision_rows.append(
                {
                    "run_order": 0,
                    "run_name": run_name,
                    "seed": seed,
                    "arm_order": ARMS.index(arm),
                    "arm": arm,
                    "training_episode_id": episode_id,
                    "opportunity_id": opportunity_id,
                    "rollout_update": rollout_update,
                    "policy_version": rollout_update,
                    "selected_action": action - SERVE,
                    "legal_mask": legal_mask.copy(),
                    "selected_log_probability": log_probability,
                    "decision_reward": _fp32_value(
                        "decision reward", float(decision_reward_tensor.item())
                    ),
                    "settlement_reward": _fp32_value(
                        "settlement reward", float(settlement_reward_tensor.item())
                    ),
                    "opportunity_return": _fp32_value(
                        "opportunity return", float(opportunity_return_tensor.item())
                    ),
                }
            )
        episode_return = rollout.rewards[episode_index].sum(dtype=torch.float32)
        episode_rows.append(
            {
                "run_order": 0,
                "run_name": run_name,
                "seed": seed,
                "arm_order": ARMS.index(arm),
                "arm": arm,
                "training_episode_id": episode_id,
                "rollout_update": rollout_update,
                "policy_version": rollout_update,
                "episode_return": _fp32_value(
                    "episode return", float(episode_return.item())
                ),
                "action_count_serve": action_counts[0],
                "action_count_refresh": action_counts[1],
                "action_count_safe_fallback": action_counts[2],
            }
        )

    if len(optimizer_steps) != ADAM_STEPS_PER_UPDATE:
        raise TrainingRecordError("optimizer-step coverage differs from one rollout")
    optimizer_rows: list[dict[str, Any]] = []
    for expected_index, record in enumerate(optimizer_steps):
        if not isinstance(record, PPOLossRecord):
            raise TrainingRecordError("optimizer records must be PPOLossRecord values")
        epoch, minibatch = divmod(expected_index, B1_MINIBATCHES_PER_EPOCH)
        if (
            record.rollout_update != rollout_update
            or record.ppo_epoch != epoch
            or record.minibatch != minibatch
            or record.optimizer_step_count != rollout_update * ADAM_STEPS_PER_UPDATE + expected_index + 1
        ):
            raise TrainingRecordError("optimizer-step order/count differs from frozen B1")
        ordered_ids = list(record.episode_ids)
        if (
            len(ordered_ids) != 2
            or len(set(ordered_ids)) != 2
            or any(episode_id not in expected_episode_ids for episode_id in ordered_ids)
        ):
            raise TrainingRecordError("optimizer minibatch episode IDs are invalid")
        optimizer_rows.append(
            {
                "run_order": 0,
                "run_name": run_name,
                "seed": seed,
                "arm_order": ARMS.index(arm),
                "arm": arm,
                "rollout_update": rollout_update,
                "ppo_epoch": epoch,
                "minibatch_index": minibatch,
                "ordered_episode_ids": ordered_ids,
                "actor_loss_fp32_bits": _fp32_bits("actor loss", record.actor_loss),
                "value_loss_fp32_bits": _fp32_bits("value loss", record.value_loss),
                "entropy_fp32_bits": _fp32_bits("entropy", record.entropy),
                "total_loss_fp32_bits": _fp32_bits("total loss", record.total_loss),
                "preclip_gradient_norm_fp32_bits": _fp32_bits(
                    "preclip gradient norm", record.gradient_norm
                ),
                "postclip_gradient_norm_fp32_bits": _fp32_bits(
                    "postclip gradient norm", record.postclip_gradient_norm
                ),
                "optimizer_step_count": record.optimizer_step_count,
                "parameter_sha256_after_step": _require_sha256(
                    "parameter digest", record.parameter_sha256_after_step
                ),
            }
        )
    for epoch in range(B1_PPO_EPOCHS):
        epoch_ids = [
            episode_id
            for row in optimizer_rows
            if row["ppo_epoch"] == epoch
            for episode_id in row["ordered_episode_ids"]
        ]
        if sorted(epoch_ids) != list(expected_episode_ids):
            raise TrainingRecordError("optimizer epoch episode coverage differs from frozen B1")

    return merge_training_exposure_slices(
        (TrainingExposureRecords(tuple(decision_rows), tuple(episode_rows), tuple(optimizer_rows)),),
        start_update=rollout_update,
        stop_update=rollout_update + 1,
    )


def _duplicate_keys(rows: Iterable[Mapping[str, Any]], key_fields: tuple[str, ...]) -> bool:
    seen: set[tuple[object, ...]] = set()
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        if key in seen:
            return True
        seen.add(key)
    return False


def merge_training_exposure_slices(
    slices: Sequence[TrainingExposureRecords],
    *,
    start_update: int,
    stop_update: int,
    require_full_b1: bool = False,
) -> TrainingExposureRecords:
    """Canonicalize contiguous fresh/resume records and reject gaps/duplicates."""

    if (
        type(start_update) is not int
        or type(stop_update) is not int
        or not 0 <= start_update < stop_update <= B1_ROLLOUT_UPDATES
    ):
        raise TrainingRecordError("training slice boundaries are invalid")
    if type(require_full_b1) is not bool:
        raise TrainingRecordError("require_full_b1 must be a bool")
    if require_full_b1 and (start_update, stop_update) != (0, B1_ROLLOUT_UPDATES):
        raise TrainingRecordError("complete B1 training coverage requires updates 0..47")
    if not slices or any(not isinstance(value, TrainingExposureRecords) for value in slices):
        raise TrainingRecordError("one or more training exposure slices are required")

    decisions = [row for value in slices for row in value.training_decisions]
    episodes = [row for value in slices for row in value.training_episodes]
    steps = [row for value in slices for row in value.optimizer_steps]
    for rows, fields in (
        (decisions, ("run_order", "seed", "arm_order", "training_episode_id", "opportunity_id")),
        (episodes, ("run_order", "seed", "arm_order", "training_episode_id")),
        (steps, ("run_order", "seed", "arm_order", "rollout_update", "ppo_epoch", "minibatch_index")),
    ):
        if _duplicate_keys(rows, fields):
            raise TrainingRecordError("duplicate training publication key")

    identities = {
        (row.get("run_name"), row.get("seed"), row.get("arm"))
        for row in (*decisions, *episodes, *steps)
    }
    if len(identities) != 1:
        raise TrainingRecordError("training records contain mixed identities")
    run_name, seed, arm = next(iter(identities))
    _validate_identity(run_name, seed, arm)

    expected_episodes = list(
        range(start_update * EPISODES_PER_ROLLOUT, stop_update * EPISODES_PER_ROLLOUT)
    )
    expected_decision_keys = [
        (episode_id, opportunity_id)
        for episode_id in expected_episodes
        for opportunity_id in range(OPPORTUNITY_COUNT)
    ]
    observed_decision_keys = sorted(
        (row.get("training_episode_id"), row.get("opportunity_id")) for row in decisions
    )
    if observed_decision_keys != expected_decision_keys:
        raise TrainingRecordError("training decision coverage has a gap or extension")
    if sorted(row.get("training_episode_id") for row in episodes) != expected_episodes:
        raise TrainingRecordError("training episode coverage has a gap or extension")
    expected_step_keys = [
        (update, epoch, minibatch)
        for update in range(start_update, stop_update)
        for epoch in range(B1_PPO_EPOCHS)
        for minibatch in range(B1_MINIBATCHES_PER_EPOCH)
    ]
    if sorted(
        (row.get("rollout_update"), row.get("ppo_epoch"), row.get("minibatch_index"))
        for row in steps
    ) != expected_step_keys:
        raise TrainingRecordError("optimizer-step coverage has a gap or extension")

    for row in decisions:
        if frozenset(row) != _DECISION_KEYS:
            raise TrainingRecordError("training decision schema is incomplete or extended")
        _validate_order_identity(row)
        episode_id = row["training_episode_id"]
        update = episode_id // EPISODES_PER_ROLLOUT
        if row["rollout_update"] != update or row["policy_version"] != update:
            raise TrainingRecordError("training decision policy/update binding differs")
        if row["legal_mask"] != list(DECISION_ACTION_MASK) or row["selected_action"] not in (0, 1, 2):
            raise TrainingRecordError("training decision action/mask differs")
        for field in (
            "selected_log_probability",
            "decision_reward",
            "settlement_reward",
            "opportunity_return",
        ):
            _fp32_value(field, row[field])
    for row in episodes:
        if frozenset(row) != _EPISODE_KEYS:
            raise TrainingRecordError("training episode schema is incomplete or extended")
        _validate_order_identity(row)
        episode_id = row["training_episode_id"]
        update = episode_id // EPISODES_PER_ROLLOUT
        if row["rollout_update"] != update or row["policy_version"] != update:
            raise TrainingRecordError("training episode policy/update binding differs")
        _fp32_value("episode return", row["episode_return"])
        counts = [
            row["action_count_serve"],
            row["action_count_refresh"],
            row["action_count_safe_fallback"],
        ]
        if any(type(value) is not int or value < 0 for value in counts) or sum(counts) != OPPORTUNITY_COUNT:
            raise TrainingRecordError("training episode action counts differ")
    for row in steps:
        if frozenset(row) != _OPTIMIZER_KEYS:
            raise TrainingRecordError("optimizer-step schema is incomplete or extended")
        _validate_order_identity(row)
        for field in (
            "actor_loss_fp32_bits",
            "value_loss_fp32_bits",
            "entropy_fp32_bits",
            "total_loss_fp32_bits",
            "preclip_gradient_norm_fp32_bits",
            "postclip_gradient_norm_fp32_bits",
        ):
            _validate_fp32_bits(field, row[field])
        _require_sha256("parameter digest", row["parameter_sha256_after_step"])
        expected_count = (
            row["rollout_update"] * ADAM_STEPS_PER_UPDATE
            + row["ppo_epoch"] * B1_MINIBATCHES_PER_EPOCH
            + row["minibatch_index"]
            + 1
        )
        if row["optimizer_step_count"] != expected_count:
            raise TrainingRecordError("optimizer step count has a gap")
        update_episode_ids = set(
            range(
                row["rollout_update"] * EPISODES_PER_ROLLOUT,
                (row["rollout_update"] + 1) * EPISODES_PER_ROLLOUT,
            )
        )
        ordered_ids = row["ordered_episode_ids"]
        if type(ordered_ids) is not list or len(ordered_ids) != 2 or len(set(ordered_ids)) != 2 or any(
            type(value) is not int or value not in update_episode_ids for value in ordered_ids
        ):
            raise TrainingRecordError("optimizer minibatch episode IDs are invalid")
    for update in range(start_update, stop_update):
        expected = list(range(update * 8, (update + 1) * 8))
        for epoch in range(B1_PPO_EPOCHS):
            observed = sorted(
                episode_id
                for row in steps
                if row["rollout_update"] == update and row["ppo_epoch"] == epoch
                for episode_id in row["ordered_episode_ids"]
            )
            if observed != expected:
                raise TrainingRecordError("optimizer epoch episode coverage differs")

    decisions.sort(
        key=lambda row: (
            row["run_order"], row["seed"], row["arm_order"],
            row["training_episode_id"], row["opportunity_id"],
        )
    )
    episodes.sort(
        key=lambda row: (
            row["run_order"], row["seed"], row["arm_order"], row["training_episode_id"],
        )
    )
    steps.sort(
        key=lambda row: (
            row["run_order"], row["seed"], row["arm_order"],
            row["rollout_update"], row["ppo_epoch"], row["minibatch_index"],
        )
    )
    return TrainingExposureRecords(tuple(decisions), tuple(episodes), tuple(steps))


__all__ = [
    "TrainingExposureRecords",
    "TrainingRecordError",
    "build_training_exposure_records",
    "merge_training_exposure_slices",
]
