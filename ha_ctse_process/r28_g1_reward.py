"""Frozen R28-G1 deterministic action-process reward.

The scorer is calibrated offline by R28-G0.  This module only evaluates that
frozen scorer and attributes a bounded reward to eligible low-level rollout
steps.  It owns no optimizer and never changes high-level segment returns.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch
import torch.nn.functional as F

from ha_ctse_process.r27_g2_analysis import late_action_features
from ha_ctse_process.r28_g0_target import (
    CONTEXT_WIDTH,
    DURATION_STEPS,
    EXPERIMENT_ID as G0_EXPERIMENT_ID,
    HEAD_INPUT_WIDTH,
    N_AGENTS,
    N_SKILLS,
    STREAM_WIDTH,
)


ARMS = ("probe_only", "sham_reward", "real_reward")
FINAL_CHECKPOINT_ID = "arm0_final"
FINAL_CHECKPOINT_PATH = (
    "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/"
    "standalone_process_core_final.pt"
)
SHAM_SEED = 28022
REWARD_SCALE = 0.02
REWARD_CLIP = 0.05
OOD_KILL_FRACTION = 0.20
RATIO_KILL_FRACTION = 0.05
FINAL_WINDOW = 10
SUPPORT_FEATURE_NAMES = tuple(
    f"action{action}_{statistic}"
    for action in range(4)
    for statistic in ("mean", "std", "slope")
)


class R28G1ContractError(RuntimeError):
    """The frozen implementation contract was violated before PPO."""


@dataclass(frozen=True)
class R28G1SupportEvaluation:
    """Pure support-envelope evaluation for frozen action-process features."""

    support: np.ndarray
    distances: np.ndarray
    thresholds: np.ndarray
    distance_ratio: np.ndarray
    abs_z: np.ndarray
    ood_fraction: float


def _array(name: str, value: Any, shape: tuple[int, ...]) -> np.ndarray:
    result = np.asarray(value, dtype=np.float32)
    if result.shape != shape:
        raise R28G1ContractError(f"{name} shape {result.shape} != {shape}")
    if not np.isfinite(result).all():
        raise R28G1ContractError(f"{name} contains non-finite values")
    return result


def _scalar(name: str, value: Any, *, positive: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise R28G1ContractError(f"{name} must be numeric") from exc
    if not np.isfinite(result) or (positive and result <= 0.0):
        qualifier = "positive and finite" if positive else "finite"
        raise R28G1ContractError(f"{name} must be {qualifier}")
    return result


@dataclass(frozen=True)
class FrozenHead:
    name: str
    mean: torch.Tensor
    std: torch.Tensor
    weight: torch.Tensor
    bias: torch.Tensor
    temperature: float

    @classmethod
    def from_payload(
        cls,
        name: str,
        payload: Mapping[str, Any],
        device: torch.device,
    ) -> "FrozenHead":
        if not isinstance(payload, Mapping):
            raise R28G1ContractError(f"head {name} is not a mapping")
        if str(payload.get("name")) != name:
            raise R28G1ContractError(f"head {name} name mismatch")
        mean = _array(f"{name}.mean", payload.get("mean"), (HEAD_INPUT_WIDTH,))
        std = _array(f"{name}.std", payload.get("std"), (HEAD_INPUT_WIDTH,))
        if np.any(std <= 0.0):
            raise R28G1ContractError(f"{name}.std must be positive")
        weight = _array(
            f"{name}.weight", payload.get("weight"), (N_SKILLS, HEAD_INPUT_WIDTH)
        )
        bias = _array(f"{name}.bias", payload.get("bias"), (N_SKILLS,))
        temperature = _scalar(
            f"{name}.temperature", payload.get("temperature"), positive=True
        )
        return cls(
            name=name,
            mean=torch.as_tensor(mean, dtype=torch.float32, device=device),
            std=torch.as_tensor(std, dtype=torch.float32, device=device),
            weight=torch.as_tensor(weight, dtype=torch.float32, device=device),
            bias=torch.as_tensor(bias, dtype=torch.float32, device=device),
            temperature=temperature,
        )

    def log_probs(self, features: torch.Tensor) -> torch.Tensor:
        standardized = (features - self.mean) / self.std
        logits = F.linear(standardized, self.weight, self.bias)
        return F.log_softmax(logits / self.temperature, dim=-1)


def empty_r28_g1_metrics(arm: str = "probe_only") -> dict[str, float]:
    metrics = {
        "r28_g1_active": 0.0,
        "r28_g1_arm_code": float(ARMS.index(arm)) if arm in ARMS else -1.0,
        "r28_g1_segments_seen": 0.0,
        "r28_g1_structural_rows": 0.0,
        "r28_g1_initial_rows_rejected": 0.0,
        "r28_g1_episode_truncated_rows_rejected": 0.0,
        "r28_g1_update_truncated_rows_rejected": 0.0,
        "r28_g1_length_rows_rejected": 0.0,
        "r28_g1_pre_window_rows_rejected": 0.0,
        "r28_g1_ood_fraction": 0.0,
        "r28_g1_in_support_rows": 0.0,
        "r28_g1_support_distance_ratio_mean": 0.0,
        "r28_g1_support_distance_ratio_p95": 0.0,
        "r28_g1_support_kill_switch_event": 0.0,
        "r28_g1_rewardable_groups": 0.0,
        "r28_g1_rewardable_rows": 0.0,
        "r28_g1_unbalanced_groups": 0.0,
        "r28_g1_real_score_mean": 0.0,
        "r28_g1_sham_score_mean": 0.0,
        "r28_g1_real_minus_sham_score_mean": 0.0,
        "r28_g1_real_centered_abs_mean": 0.0,
        "r28_g1_sham_centered_abs_mean": 0.0,
        "r28_g1_selected_segment_reward_abs_mean": 0.0,
        "r28_g1_selected_distributed_reward_abs_mean": 0.0,
        "r28_g1_reward_applied_steps": 0.0,
        "r28_g1_reward_env_ratio": 0.0,
        "r28_g1_ratio_kill_switch_event": 0.0,
    }
    metrics.update(
        {
            f"r28_g1_support_abs_z_{name}": 0.0
            for name in SUPPORT_FEATURE_NAMES
        }
    )
    return metrics


def fixed_point_free_derangement(
    labels: np.ndarray,
    *,
    policy_update: int,
    agent_id: int,
    duration_id: int,
) -> np.ndarray:
    """Return a marginal-preserving, update-specific label derangement."""

    real = np.asarray(labels, dtype=np.int64).reshape(-1)
    if real.size == 0 or np.any((real < 0) | (real >= N_SKILLS)):
        raise R28G1ContractError("sham labels are empty or outside the codebook")
    counts = np.bincount(real, minlength=N_SKILLS)
    if np.any(counts == 0) or int(np.max(counts)) > real.size // 2:
        raise R28G1ContractError("group does not admit the frozen sham derangement")

    rng = np.random.default_rng(
        np.random.SeedSequence(
            [SHAM_SEED, int(policy_update), int(agent_id), int(duration_id)]
        )
    )
    # Place equal real labels in contiguous circular blocks, randomizing both
    # block order and row order within each block.  At least the rotation by the
    # largest block width is valid when max(counts) <= n / 2, so enumerating
    # circular shifts here is complete for every group admitted by the frozen
    # balance condition rather than relying on random row permutations.
    block_order = rng.permutation(N_SKILLS)
    ordered_rows = np.concatenate(
        [rng.permutation(np.flatnonzero(real == label)) for label in block_order]
    )
    ordered_labels = real[ordered_rows]
    valid_shifts = [
        shift
        for shift in range(1, real.size)
        if np.all(np.roll(ordered_labels, shift) != ordered_labels)
    ]
    if not valid_shifts:
        raise R28G1ContractError("balanced group has no circular sham derangement")
    assigned_ordered = np.roll(
        ordered_labels,
        valid_shifts[int(rng.integers(0, len(valid_shifts)))],
    )
    chosen = np.empty_like(real)
    chosen[ordered_rows] = assigned_ordered
    if not np.array_equal(np.bincount(chosen, minlength=N_SKILLS), counts):
        raise R28G1ContractError("sham derangement changed the label marginal")
    if np.any(chosen == real):
        raise R28G1ContractError("sham derangement contains a fixed point")
    return chosen


class FrozenR28G1Reward:
    """Frozen G0 scorer plus low-rollout attribution and kill switches."""

    def __init__(
        self,
        *,
        arm: str,
        scorer_path: str | Path,
        actor_base: torch.nn.Module,
        device: str | torch.device,
        frozen_actor_base_state: Mapping[str, torch.Tensor] | None = None,
    ):
        if arm not in ARMS:
            raise R28G1ContractError(f"unsupported R28-G1 arm {arm!r}")
        self.arm = arm
        self.scorer_path = str(Path(scorer_path))
        self.device = torch.device(device)
        try:
            payload = torch.load(Path(scorer_path), map_location="cpu", weights_only=True)
        except TypeError:  # PyTorch before the weights_only argument.
            payload = torch.load(Path(scorer_path), map_location="cpu")
        if not isinstance(payload, Mapping):
            raise R28G1ContractError("G0 scorer payload is not a mapping")
        self._validate_payload(payload)
        heads = payload["heads"]
        self.heads = {
            name: FrozenHead.from_payload(name, heads[name], self.device)
            for name in ("q_full", "q_context", "q_pre")
        }
        envelope = payload["support_envelope"]
        self.support_means = _array(
            "support.means", envelope.get("means"), (len(DURATION_STEPS), N_SKILLS, STREAM_WIDTH)
        )
        self.support_variances = _array(
            "support.variances",
            envelope.get("variances"),
            (len(DURATION_STEPS), N_SKILLS, STREAM_WIDTH),
        )
        if np.any(self.support_variances <= 0.0):
            raise R28G1ContractError("support variances must be positive")
        self.support_thresholds = _array(
            "support.thresholds", envelope.get("thresholds"), (len(DURATION_STEPS), N_SKILLS)
        )
        if np.any(self.support_thresholds < 0.0):
            raise R28G1ContractError("support thresholds must be non-negative")
        kill_fraction = _scalar(
            "support.future_ood_kill_fraction",
            envelope.get("future_ood_kill_fraction"),
            positive=True,
        )
        if not np.isclose(kill_fraction, OOD_KILL_FRACTION):
            raise R28G1ContractError("G0 support kill fraction drifted from 0.20")

        self.phi0 = copy.deepcopy(actor_base).to(self.device)
        if frozen_actor_base_state is not None:
            self.phi0.load_state_dict(dict(frozen_actor_base_state), strict=True)
        for name, value in self.phi0.state_dict().items():
            if not torch.isfinite(value).all():
                raise R28G1ContractError(
                    f"frozen actor-base tensor {name} is non-finite"
                )
        self.phi0.eval()
        for parameter in self.phi0.parameters():
            parameter.requires_grad_(False)

    @staticmethod
    def _validate_payload(payload: Mapping[str, Any]) -> None:
        if payload.get("experiment_id") != G0_EXPERIMENT_ID:
            raise R28G1ContractError("scorer experiment_id is not the frozen R28-G0 experiment")
        if payload.get("checkpoint_id") != FINAL_CHECKPOINT_ID:
            raise R28G1ContractError("scorer checkpoint_id is not arm0_final")
        if payload.get("authorized_for_g1_package_review") is not True:
            raise R28G1ContractError("scorer is not authorized for the G1 package")
        heads = payload.get("heads")
        if not isinstance(heads, Mapping) or set(heads) != {
            "q_full",
            "q_context",
            "q_pre",
        }:
            raise R28G1ContractError("scorer head set is not exactly q_full/q_context/q_pre")
        if not isinstance(payload.get("support_envelope"), Mapping):
            raise R28G1ContractError("scorer support envelope is missing")
        contract = payload.get("scientific_contract")
        if not isinstance(contract, Mapping):
            raise R28G1ContractError("scorer scientific contract is missing")
        if tuple(contract.get("duration_steps", ())) != DURATION_STEPS:
            raise R28G1ContractError("scorer duration steps drifted")
        if int(contract.get("head_input_width", -1)) != HEAD_INPUT_WIDTH:
            raise R28G1ContractError("scorer head width drifted")
        slots = contract.get("checkpoint_slots")
        final = slots.get(FINAL_CHECKPOINT_ID) if isinstance(slots, Mapping) else None
        if not isinstance(final, Mapping):
            raise R28G1ContractError("scorer final checkpoint slot is missing")
        if str(final.get("path")) != FINAL_CHECKPOINT_PATH:
            raise R28G1ContractError("scorer registered final checkpoint path drifted")
        if int(final.get("update", -1)) != 32 or int(final.get("total_steps", -1)) != 1_000_000:
            raise R28G1ContractError("scorer registered source exposure drifted")

    def checkpoint_state(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "scorer_path": self.scorer_path,
            "source_total_steps": 1_000_000,
            "source_update_idx": 32,
            "source_checkpoint_id": FINAL_CHECKPOINT_ID,
            "frozen_actor_base": {
                name: value.detach().cpu().clone()
                for name, value in self.phi0.state_dict().items()
            },
        }

    def _context(self, segment: Any) -> np.ndarray:
        observation = np.asarray(segment.high_obs, dtype=np.float32).reshape(1, -1)
        if not np.isfinite(observation).all():
            raise R28G1ContractError("segment assignment observation is non-finite")
        with torch.no_grad():
            encoded = self.phi0(
                torch.as_tensor(observation, dtype=torch.float32, device=self.device)
            ).detach().cpu().numpy().reshape(-1)
        if encoded.shape != (256,) or not np.isfinite(encoded).all():
            raise R28G1ContractError("frozen actor-base context shape or value mismatch")
        agent_id = int(segment.agent_id)
        duration_id = int(segment.duration_idx)
        phase_id = min(max(int(segment.episode_step_start), 0) // 100, 2)
        if not 0 <= agent_id < N_AGENTS or not 0 <= duration_id < len(DURATION_STEPS):
            raise R28G1ContractError("segment agent or duration is outside the frozen contract")
        agent = np.eye(N_AGENTS, dtype=np.float32)[agent_id]
        duration = np.eye(len(DURATION_STEPS), dtype=np.float32)[duration_id]
        phase = np.eye(3, dtype=np.float32)[phase_id]
        context = np.concatenate((encoded.astype(np.float32), agent, duration, phase))
        if context.shape != (CONTEXT_WIDTH,):
            raise R28G1ContractError("R28-G1 context width drifted")
        return context

    @staticmethod
    def _structural_reason(segment: Any) -> str | None:
        if bool(segment.initial_assignment):
            return "initial"
        if str(getattr(segment, "completion_reason", "")) == "episode" or bool(segment.terminal):
            return "episode_truncated"
        if str(getattr(segment, "completion_reason", "")) != "renewal":
            return "update_truncated"
        duration_id = int(segment.duration_idx)
        if not 0 <= duration_id < len(DURATION_STEPS):
            return "length"
        expected = int(DURATION_STEPS[duration_id])
        if int(segment.length) != expected or int(segment.duration_target) * 10 != expected:
            return "length"
        deterministic = getattr(segment, "deterministic_actions", ())
        if len(deterministic) != expected:
            return "length"
        pre = getattr(segment, "pre_assignment_deterministic_actions", ())
        if len(pre) != FINAL_WINDOW:
            return "pre_window"
        if int(getattr(segment, "pre_assignment_episode_id", -1)) != int(
            getattr(segment, "episode_id", -2)
        ):
            return "pre_window"
        if int(getattr(segment, "pre_assignment_policy_update", -1)) != int(
            getattr(segment, "policy_update", -2)
        ):
            return "pre_window"
        return None

    @staticmethod
    def _validate_rollout_alignment(segment: Any, rollout: Any) -> None:
        indices = np.asarray(segment.rollout_indices[-FINAL_WINDOW:], dtype=np.int64)
        if indices.shape != (FINAL_WINDOW,) or np.any(np.diff(indices) <= 0):
            raise R28G1ContractError("R28 final-window rollout indices are malformed")
        deterministic = np.asarray(
            segment.deterministic_actions[-FINAL_WINDOW:], dtype=np.float32
        )
        if deterministic.ndim != 2 or not np.isfinite(deterministic).all():
            raise R28G1ContractError("R28 segment deterministic evidence is malformed")
        seen: set[tuple[int, int]] = set()
        for offset, rollout_index in enumerate(indices):
            index = int(rollout_index)
            if not 0 <= index < len(rollout.rewards):
                raise R28G1ContractError("R28 reward index crosses the rollout boundary")
            key = (index, int(segment.agent_id))
            if key in seen:
                raise R28G1ContractError("R28 reward index is duplicated within a segment")
            seen.add(key)
            if int(rollout.env_ids[index]) != int(segment.env_id):
                raise R28G1ContractError("R28 reward index crosses an environment")
            if int(np.asarray(rollout.skills[index])[int(segment.agent_id)]) != int(segment.skill):
                raise R28G1ContractError("R28 reward index crosses a skill assignment")
            rollout_action = np.asarray(
                rollout.deterministic_actions[index], dtype=np.float32
            )[int(segment.agent_id)].reshape(-1)
            if rollout_action.shape != deterministic[offset].reshape(-1).shape or not np.array_equal(
                rollout_action, deterministic[offset].reshape(-1)
            ):
                raise R28G1ContractError("R28 recurrent deterministic evidence mismatch")

    def _score_rows(
        self,
        post: np.ndarray,
        pre: np.ndarray,
        context: np.ndarray,
    ) -> dict[str, np.ndarray]:
        post_t = torch.as_tensor(post, dtype=torch.float32, device=self.device)
        pre_t = torch.as_tensor(pre, dtype=torch.float32, device=self.device)
        context_t = torch.as_tensor(context, dtype=torch.float32, device=self.device)
        full_input = torch.cat((post_t, context_t), dim=1)
        context_input = torch.cat((torch.zeros_like(post_t), context_t), dim=1)
        pre_input = torch.cat((pre_t, context_t), dim=1)
        if tuple(full_input.shape[1:]) != (HEAD_INPUT_WIDTH,):
            raise R28G1ContractError("R28 head input width mismatch")
        with torch.no_grad():
            result = {
                "q_full": self.heads["q_full"].log_probs(full_input),
                "q_context": self.heads["q_context"].log_probs(context_input),
                "q_pre": self.heads["q_pre"].log_probs(pre_input),
            }
        arrays = {
            name: value.detach().cpu().numpy() for name, value in result.items()
        }
        if not all(np.isfinite(value).all() for value in arrays.values()):
            raise R28G1ContractError("R28 frozen head produced a non-finite score")
        return arrays

    def evaluate_support(
        self,
        post: np.ndarray,
        labels: np.ndarray,
        durations: np.ndarray,
    ) -> R28G1SupportEvaluation:
        """Evaluate frozen support without scoring or mutating rollout state."""

        features = np.asarray(post, dtype=np.float32)
        label_ids = np.asarray(labels, dtype=np.int64).reshape(-1)
        duration_ids = np.asarray(durations, dtype=np.int64).reshape(-1)
        if features.ndim != 2 or features.shape[1] != STREAM_WIDTH:
            raise R28G1ContractError(
                f"R28 support feature shape {features.shape} != (rows, {STREAM_WIDTH})"
            )
        row_count = int(features.shape[0])
        if row_count == 0:
            raise R28G1ContractError("R28 support evaluation requires at least one row")
        if label_ids.shape != (row_count,) or duration_ids.shape != (row_count,):
            raise R28G1ContractError("R28 support label or duration shape mismatch")
        if np.any((label_ids < 0) | (label_ids >= N_SKILLS)):
            raise R28G1ContractError("R28 label is outside the frozen codebook")
        if np.any((duration_ids < 0) | (duration_ids >= len(DURATION_STEPS))):
            raise R28G1ContractError("R28 duration is outside the frozen contract")
        if not np.isfinite(features).all():
            raise R28G1ContractError("R28 support features contain non-finite values")

        support = np.zeros(row_count, dtype=np.bool_)
        support_distances = np.zeros(row_count, dtype=np.float64)
        support_limits = np.zeros(row_count, dtype=np.float64)
        support_abs_z = np.zeros((row_count, STREAM_WIDTH), dtype=np.float64)
        for index in range(row_count):
            mean = self.support_means[duration_ids[index], label_ids[index]]
            variance = self.support_variances[duration_ids[index], label_ids[index]]
            threshold = self.support_thresholds[duration_ids[index], label_ids[index]]
            contribution = np.square(features[index] - mean) / variance
            distance = float(np.sum(contribution))
            if not np.isfinite(distance):
                raise R28G1ContractError("R28 support distance is non-finite")
            support_distances[index] = distance
            support_limits[index] = float(threshold)
            support_abs_z[index] = np.sqrt(contribution)
            support[index] = distance <= float(threshold)
        distance_ratio = support_distances / np.maximum(support_limits, 1e-12)
        return R28G1SupportEvaluation(
            support=support,
            distances=support_distances,
            thresholds=support_limits,
            distance_ratio=distance_ratio,
            abs_z=support_abs_z,
            ood_fraction=float(np.mean(~support)),
        )

    def apply(
        self,
        segments: Sequence[Any],
        rollout: Any,
        *,
        policy_update: int,
    ) -> dict[str, float]:
        metrics = empty_r28_g1_metrics(self.arm)
        metrics["r28_g1_active"] = 1.0
        metrics["r28_g1_segments_seen"] = float(len(segments))
        rows: list[Any] = []
        reject_key = {
            "initial": "r28_g1_initial_rows_rejected",
            "episode_truncated": "r28_g1_episode_truncated_rows_rejected",
            "update_truncated": "r28_g1_update_truncated_rows_rejected",
            "length": "r28_g1_length_rows_rejected",
            "pre_window": "r28_g1_pre_window_rows_rejected",
        }
        for segment in segments:
            reason = self._structural_reason(segment)
            if reason is not None:
                metrics[reject_key[reason]] += 1.0
                continue
            if int(segment.policy_update) != int(policy_update):
                raise R28G1ContractError("segment policy-update identity mismatch")
            self._validate_rollout_alignment(segment, rollout)
            rows.append(segment)
        metrics["r28_g1_structural_rows"] = float(len(rows))
        if not rows:
            return metrics

        post = np.asarray(
            [late_action_features(np.asarray(row.deterministic_actions[-FINAL_WINDOW:])) for row in rows],
            dtype=np.float32,
        )
        pre = np.asarray(
            [late_action_features(np.asarray(row.pre_assignment_deterministic_actions)) for row in rows],
            dtype=np.float32,
        )
        context = np.asarray([self._context(row) for row in rows], dtype=np.float32)
        labels = np.asarray([int(row.skill) for row in rows], dtype=np.int64)
        durations = np.asarray([int(row.duration_idx) for row in rows], dtype=np.int64)
        agents = np.asarray([int(row.agent_id) for row in rows], dtype=np.int64)
        if np.any((labels < 0) | (labels >= N_SKILLS)):
            raise R28G1ContractError("R28 label is outside the frozen codebook")
        if not (np.isfinite(post).all() and np.isfinite(pre).all() and np.isfinite(context).all()):
            raise R28G1ContractError("R28 feature construction produced non-finite values")

        support_evaluation = self.evaluate_support(post, labels, durations)
        support = support_evaluation.support
        distance_ratio = support_evaluation.distance_ratio
        metrics["r28_g1_support_distance_ratio_mean"] = float(
            np.mean(distance_ratio)
        )
        metrics["r28_g1_support_distance_ratio_p95"] = float(
            np.quantile(distance_ratio, 0.95, method="linear")
        )
        for feature_index, name in enumerate(SUPPORT_FEATURE_NAMES):
            metrics[f"r28_g1_support_abs_z_{name}"] = float(
                np.mean(support_evaluation.abs_z[:, feature_index])
            )
        ood_fraction = support_evaluation.ood_fraction
        metrics["r28_g1_ood_fraction"] = ood_fraction
        metrics["r28_g1_in_support_rows"] = float(np.sum(support))
        if ood_fraction > OOD_KILL_FRACTION:
            metrics["r28_g1_support_kill_switch_event"] = 1.0
            return metrics

        log_probs = self._score_rows(post, pre, context)
        row_indices = np.arange(len(rows), dtype=np.int64)
        sham_labels = np.full(len(rows), -1, dtype=np.int64)
        real_centered = np.zeros(len(rows), dtype=np.float32)
        sham_centered = np.zeros(len(rows), dtype=np.float32)
        rewardable = np.zeros(len(rows), dtype=np.bool_)
        real_scores = np.full(len(rows), np.nan, dtype=np.float32)
        sham_scores = np.full(len(rows), np.nan, dtype=np.float32)

        for agent_id in range(N_AGENTS):
            for duration_id in range(len(DURATION_STEPS)):
                group = row_indices[
                    support & (agents == agent_id) & (durations == duration_id)
                ]
                if group.size == 0:
                    continue
                counts = np.bincount(labels[group], minlength=N_SKILLS)
                if np.any(counts == 0) or int(np.max(counts)) > group.size // 2:
                    metrics["r28_g1_unbalanced_groups"] += 1.0
                    continue
                group_sham = fixed_point_free_derangement(
                    labels[group],
                    policy_update=policy_update,
                    agent_id=agent_id,
                    duration_id=duration_id,
                )
                sham_labels[group] = group_sham
                real = (
                    log_probs["q_full"][group, labels[group]]
                    - np.maximum(
                        log_probs["q_context"][group, labels[group]],
                        log_probs["q_pre"][group, labels[group]],
                    )
                )
                sham = (
                    log_probs["q_full"][group, group_sham]
                    - np.maximum(
                        log_probs["q_context"][group, group_sham],
                        log_probs["q_pre"][group, group_sham],
                    )
                )
                if not (np.isfinite(real).all() and np.isfinite(sham).all()):
                    raise R28G1ContractError("R28 frozen score is non-finite")
                real_scores[group] = real
                sham_scores[group] = sham
                real_centered[group] = np.clip(
                    REWARD_SCALE * (real - float(np.mean(real))),
                    -REWARD_CLIP,
                    REWARD_CLIP,
                )
                sham_centered[group] = np.clip(
                    REWARD_SCALE * (sham - float(np.mean(sham))),
                    -REWARD_CLIP,
                    REWARD_CLIP,
                )
                rewardable[group] = True
                metrics["r28_g1_rewardable_groups"] += 1.0

        rewardable_count = int(np.sum(rewardable))
        metrics["r28_g1_rewardable_rows"] = float(rewardable_count)
        if rewardable_count == 0:
            return metrics
        metrics["r28_g1_real_score_mean"] = float(np.mean(real_scores[rewardable]))
        metrics["r28_g1_sham_score_mean"] = float(np.mean(sham_scores[rewardable]))
        metrics["r28_g1_real_minus_sham_score_mean"] = float(
            np.mean(real_scores[rewardable] - sham_scores[rewardable])
        )
        metrics["r28_g1_real_centered_abs_mean"] = float(
            np.mean(np.abs(real_centered[rewardable]))
        )
        metrics["r28_g1_sham_centered_abs_mean"] = float(
            np.mean(np.abs(sham_centered[rewardable]))
        )

        selected = np.zeros(len(rows), dtype=np.float32)
        if self.arm == "real_reward":
            selected[rewardable] = real_centered[rewardable]
        elif self.arm == "sham_reward":
            selected[rewardable] = sham_centered[rewardable]
        metrics["r28_g1_selected_segment_reward_abs_mean"] = float(
            np.mean(np.abs(selected[rewardable]))
        )

        original = np.asarray(rollout.rewards, dtype=np.float32)
        if original.ndim != 2 or original.shape[1] != N_AGENTS:
            raise R28G1ContractError("R28 low rollout reward shape mismatch")
        if not np.isfinite(original).all():
            raise R28G1ContractError("original individual environment reward is non-finite")
        distributed = np.zeros_like(original, dtype=np.float32)
        occupied: set[tuple[int, int]] = set()
        for row_index in np.flatnonzero(rewardable):
            reward = float(selected[row_index]) / float(FINAL_WINDOW)
            segment = rows[int(row_index)]
            for rollout_index in segment.rollout_indices[-FINAL_WINDOW:]:
                key = (int(rollout_index), int(segment.agent_id))
                if key in occupied:
                    raise R28G1ContractError("R28 low reward attribution overlaps")
                occupied.add(key)
                distributed[key] = reward
        if not np.isfinite(distributed).all():
            raise R28G1ContractError("R28 distributed reward is non-finite")
        numerator = float(np.mean(np.abs(distributed)))
        denominator = max(float(np.mean(np.abs(original))), 1e-8)
        ratio = numerator / denominator
        if not np.isfinite(ratio):
            raise R28G1ContractError("R28 reward/environment ratio is non-finite")
        metrics["r28_g1_selected_distributed_reward_abs_mean"] = numerator
        metrics["r28_g1_reward_env_ratio"] = ratio
        if ratio > RATIO_KILL_FRACTION:
            metrics["r28_g1_ratio_kill_switch_event"] = 1.0
            return metrics
        if self.arm != "probe_only":
            updated = original + distributed
            if not np.isfinite(updated).all():
                raise R28G1ContractError("R28-updated low reward is non-finite")
            for index in range(updated.shape[0]):
                rollout.rewards[index] = updated[index].copy()
            metrics["r28_g1_reward_applied_steps"] = float(np.count_nonzero(distributed))
        return metrics
