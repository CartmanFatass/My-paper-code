"""Exact shared-baseline READ versus shadow-NO_READ G31 attribution."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44
    as g44,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_db_norm_schedule_attribution_g43 as g43,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory


ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_"
    "ATTRIBUTION_G45"
)
SOURCE_ID = f"{ALGORITHM_ID}_P0"
ACCEPTED_G40_SOURCE_COMMIT = "97a8b237e0cec6c2713dd2a710d324040fa3dfc2"
ACCEPTED_G41_SOURCE_COMMIT = "a5f63c349228fc2bba7843647e0ae4c34361c1c9"
ACCEPTED_G44_FORMAL_SOURCE_COMMIT = (
    "96e35ddf55de71e56c6bcace4746c408909480dd"
)
ACCEPTED_G44_ALIGNED_SOURCE_COMMIT = (
    "1a6e046801ab3d83830d4c9f6e9724c8c47659da"
)
ACCEPTED_G44_ALIGNMENT_STAGE_COMMIT = (
    "b55578a8e57f444895da59efe9268ebe31edf511"
)
BASELINE_READ_ARM = "NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_READ"
BASELINE_SHADOW_NO_READ_ARM = (
    "NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ"
)
ARMS = (BASELINE_READ_ARM, BASELINE_SHADOW_NO_READ_ARM)
# Names consumed by the isolated accepted orchestration backend.
DBNORM_ARM = BASELINE_READ_ARM
MEAN_ARM = BASELINE_SHADOW_NO_READ_ARM
INDEPENDENT_ARM = BASELINE_READ_ARM
POOLED_ARM = BASELINE_SHADOW_NO_READ_ARM
ACCEPTED_G40_ANCHOR_REPLICATES = (0, 1, 2)
PPO_PASSES = 2
NUM_ENVS = 8
HORIZON = 48
MAX_CONFORMANCE_TRANSITIONS = NUM_ENVS * HORIZON
NORMALIZATION_ROWS = MAX_CONFORMANCE_TRANSITIONS
NORMALIZATION_MASK_DIGEST = g44.NORMALIZATION_MASK_DIGEST
GRADIENT_LIVE_TOLERANCE = g40.GRADIENT_LIVE_TOLERANCE
BASELINE_PARAMETER_NAMES = (
    "credit_baselines.0.weight",
    "credit_baselines.0.bias",
    "credit_baselines.2.weight",
    "credit_baselines.2.bias",
)
BASELINE_GRADIENT_GROUP_RECONSTRUCTION = {
    "immediate_output_row": [
        "immediate_loss:credit_baselines.2.weight[0]",
        "immediate_loss:credit_baselines.2.bias[0]",
    ],
    "successor_output_row": [
        "successor_loss:credit_baselines.2.weight[1]",
        "successor_loss:credit_baselines.2.bias[1]",
    ],
    "shared_trunk_union": [
        "immediate_loss:credit_baselines.0.weight",
        "immediate_loss:credit_baselines.0.bias",
        "successor_loss:credit_baselines.0.weight",
        "successor_loss:credit_baselines.0.bias",
    ],
}
SCALE_MATCH_ATOL = 1e-8
SCALE_MATCH_RTOL = 1e-6
ACTIVATION_TOLERANCE = 1e-6
EQUAL_MEAN_COEFFICIENT = 0.5
READ_RESIDUAL_LAW = "r_minus_bI|Gnext_minus_bS"
NO_READ_RESIDUAL_LAW = "r|Gnext"


class G45GradientGateError(ValueError):
    """A frozen G45 gate failed before either arm optimizer step."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object]) -> None:
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics)
        super().__init__(f"G45 gradient gate failed before optimizer step: {reason}")

    def __reduce__(
        self,
    ) -> tuple[type[G45GradientGateError], tuple[str, dict[str, object]]]:
        return type(self), (self.reason, dict(self.diagnostics))

    def to_record(self) -> dict[str, object]:
        return {
            "passed": False,
            "stage": "before_either_arm_optimizer_step",
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
        }


@dataclass(frozen=True)
class _GradientProbe:
    policy: torch.Tensor
    immediate_baseline_loss: torch.Tensor
    successor_baseline_loss: torch.Tensor
    immediate_credit_gradients: tuple[torch.Tensor, ...]
    successor_credit_gradients: tuple[torch.Tensor, ...]
    entropy_gradients: tuple[torch.Tensor, ...]
    immediate_baseline_gradients: tuple[torch.Tensor, ...]
    successor_baseline_gradients: tuple[torch.Tensor, ...]
    gradient_evidence: dict[str, object]


@dataclass(frozen=True)
class _PassPlan:
    policy: torch.Tensor
    immediate_baseline_loss: torch.Tensor
    successor_baseline_loss: torch.Tensor
    gradients: tuple[torch.Tensor, ...]
    gradient_evidence: dict[str, object]
    composition_record: dict[str, object]


def _gradient_rows(
    rows: Sequence[torch.Tensor | None], parameters: Sequence[nn.Parameter]
) -> tuple[torch.Tensor, ...]:
    try:
        return g43._gradient_rows(rows, parameters)
    except g43.G43GradientGateError as error:
        raise G45GradientGateError(error.reason, error.diagnostics) from error


def _global_norm(rows: Sequence[torch.Tensor]) -> float:
    return g43._global_norm(rows)


def validate_baseline_gradient_group_evidence(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    expected_keys = {
        "parameter_inventory",
        "group_reconstruction",
        "immediate_output_row_gradient_norm",
        "successor_output_row_gradient_norm",
        "shared_trunk_union_gradient_norm",
        "all_group_gradients_finite",
        "gradient_live_tolerance",
        "passed",
    }
    if (
        set(value) != expected_keys
        or value.get("parameter_inventory") != list(BASELINE_PARAMETER_NAMES)
        or value.get("group_reconstruction")
        != BASELINE_GRADIENT_GROUP_RECONSTRUCTION
        or value.get("all_group_gradients_finite") is not True
        or value.get("gradient_live_tolerance") != GRADIENT_LIVE_TOLERANCE
    ):
        return False
    norms = (
        value.get("immediate_output_row_gradient_norm"),
        value.get("successor_output_row_gradient_norm"),
        value.get("shared_trunk_union_gradient_norm"),
    )
    return bool(
        value.get("passed") is True
        and all(
            isinstance(norm, (int, float))
            and not isinstance(norm, bool)
            and np.isfinite(float(norm))
            and float(norm) > GRADIENT_LIVE_TOLERANCE
            for norm in norms
        )
    )


def baseline_gradient_group_evidence(
    model: g41.G41NoSlowProjection,
    immediate_baseline_gradients: Sequence[torch.Tensor | None],
    successor_baseline_gradients: Sequence[torch.Tensor | None],
) -> dict[str, object]:
    named_parameters = tuple(model.credit_baselines.named_parameters())
    local_names = tuple(name for name, _ in named_parameters)
    if local_names != ("0.weight", "0.bias", "2.weight", "2.bias"):
        raise G45GradientGateError(
            "baseline_parameter_inventory_mismatch",
            {"observed_parameter_names": list(local_names)},
        )
    parameters = tuple(parameter for _, parameter in named_parameters)
    immediate = _gradient_rows(immediate_baseline_gradients, parameters)
    successor = _gradient_rows(successor_baseline_gradients, parameters)
    immediate_by_name = dict(zip(local_names, immediate))
    successor_by_name = dict(zip(local_names, successor))
    output_weight = immediate_by_name["2.weight"]
    output_bias = immediate_by_name["2.bias"]
    if output_weight.ndim != 2 or output_weight.shape[0] != 2 or output_bias.shape != (2,):
        raise G45GradientGateError(
            "baseline_output_schema_mismatch",
            {
                "weight_shape": list(output_weight.shape),
                "bias_shape": list(output_bias.shape),
            },
        )
    immediate_output_rows = (
        immediate_by_name["2.weight"][0],
        immediate_by_name["2.bias"][0:1],
    )
    successor_output_rows = (
        successor_by_name["2.weight"][1],
        successor_by_name["2.bias"][1:2],
    )
    shared_trunk_union = (
        immediate_by_name["0.weight"],
        immediate_by_name["0.bias"],
        successor_by_name["0.weight"],
        successor_by_name["0.bias"],
    )
    all_rows = immediate_output_rows + successor_output_rows + shared_trunk_union
    evidence: dict[str, object] = {
        "parameter_inventory": list(BASELINE_PARAMETER_NAMES),
        "group_reconstruction": {
            name: list(rows)
            for name, rows in BASELINE_GRADIENT_GROUP_RECONSTRUCTION.items()
        },
        "immediate_output_row_gradient_norm": _global_norm(immediate_output_rows),
        "successor_output_row_gradient_norm": _global_norm(successor_output_rows),
        "shared_trunk_union_gradient_norm": _global_norm(shared_trunk_union),
        "all_group_gradients_finite": all(
            bool(torch.isfinite(row).all()) for row in all_rows
        ),
        "gradient_live_tolerance": GRADIENT_LIVE_TOLERANCE,
        "passed": False,
    }
    evidence["passed"] = bool(
        evidence["all_group_gradients_finite"] is True
        and all(
            float(evidence[name]) > GRADIENT_LIVE_TOLERANCE
            for name in (
                "immediate_output_row_gradient_norm",
                "successor_output_row_gradient_norm",
                "shared_trunk_union_gradient_norm",
            )
        )
    )
    return evidence


def registered_gradient_evidence(
    model: g41.G41NoSlowProjection,
    immediate_actor_gradients: Sequence[torch.Tensor | None],
    successor_actor_gradients: Sequence[torch.Tensor | None],
    immediate_baseline_gradients: Sequence[torch.Tensor | None],
    successor_baseline_gradients: Sequence[torch.Tensor | None],
) -> dict[str, object]:
    try:
        evidence = g43.registered_gradient_evidence(
            model,
            immediate_actor_gradients,
            successor_actor_gradients,
            immediate_baseline_gradients,
            successor_baseline_gradients,
        )
    except g43.G43GradientGateError as error:
        raise G45GradientGateError(error.reason, error.diagnostics) from error
    evidence["baseline_gradient_groups"] = baseline_gradient_group_evidence(
        model, immediate_baseline_gradients, successor_baseline_gradients
    )
    evidence["passed"] = bool(
        g43.validate_registered_gradient_evidence(evidence)
        and validate_baseline_gradient_group_evidence(
            evidence["baseline_gradient_groups"]
        )
    )
    return evidence


def validate_registered_gradient_evidence(value: object) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("passed") is True
        and g43.validate_registered_gradient_evidence(value)
        and validate_baseline_gradient_group_evidence(
            value.get("baseline_gradient_groups")
        )
    )


def _rows_bitwise_equal(
    left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]
) -> bool:
    return len(left) == len(right) and all(
        torch.equal(a, b) for a, b in zip(left, right)
    )


def _tensor_digest(value: torch.Tensor) -> str:
    row = value.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(row.dtype).encode("ascii"))
    digest.update(json.dumps(list(row.shape), separators=(",", ":")).encode("ascii"))
    digest.update(row.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _sequence_digest(values: Sequence[int]) -> str:
    return hashlib.sha256(
        json.dumps([int(value) for value in values], separators=(",", ":")).encode(
            "ascii"
        )
    ).hexdigest()


def _episode_ids(trajectory: AnchoredRosterTrajectory) -> tuple[int, ...]:
    values = tuple(int(row.episode_id) for row in trajectory.ledgers)
    if len(values) != NUM_ENVS or len(set(values)) != NUM_ENVS:
        raise G45GradientGateError(
            "episode_id_inventory_mismatch", {"episode_ids": list(values)}
        )
    return values


def _centered_rms(value: torch.Tensor) -> float:
    row = value.detach().to(torch.float64)
    centered = row - row.mean()
    result = torch.sqrt(centered.square().mean())
    if not bool(torch.isfinite(result)):
        raise G45GradientGateError("centered_baseline_rms_nonfinite", {})
    return float(result)


def _read_credit(trajectory: AnchoredRosterTrajectory) -> g41.G41Credit:
    return g41.compute_g31_credit_without_slow(
        rewards=trajectory.rewards,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=g40.terminal_mask(trajectory),
    )


def _no_read_credit(trajectory: AnchoredRosterTrajectory) -> g41.G41Credit:
    """Construct the NO_READ credit using rewards and terminals only."""

    rewards = trajectory.rewards.detach()
    terminals = g40.terminal_mask(trajectory)
    if rewards.ndim != 2 or terminals.shape != rewards.shape:
        raise ValueError("G45 NO_READ credit expects matching [time,batch] rows")
    if terminals.dtype != torch.bool or not bool(torch.isfinite(rewards).all()):
        raise ValueError("G45 NO_READ reward or terminal inventory is invalid")
    work_rewards = rewards.to(torch.float64)
    nonterminal = (~terminals).to(torch.float64)
    work_returns = torch.empty_like(work_rewards)
    running = torch.zeros_like(work_rewards[0])
    for time in range(rewards.shape[0] - 1, -1, -1):
        running = work_rewards[time] + g40.GAMMA * nonterminal[time] * running
        work_returns[time] = running
    next_returns = torch.cat(
        (work_returns[1:], torch.zeros_like(work_returns[:1])), dim=0
    )
    returns = work_returns.to(rewards.dtype).detach()
    successor = (nonterminal * next_returns).to(rewards.dtype).detach()
    return g41.G41Credit(
        returns=returns,
        successor_targets=successor,
        immediate_advantage=rewards,
        successor_advantage=successor,
    )


def _normalize_credit(
    credit: g41.G41Credit,
) -> g44.ChannelNormalization:
    try:
        return g44.normalize_credit_channels(credit)
    except g44.G44GradientGateError as error:
        raise G45GradientGateError(error.reason, error.diagnostics) from error


def _equal_mean(
    immediate: Sequence[torch.Tensor],
    successor: Sequence[torch.Tensor],
    parameters: Sequence[nn.Parameter],
) -> tuple[torch.Tensor, ...]:
    left = _gradient_rows(immediate, parameters)
    right = _gradient_rows(successor, parameters)
    rows = tuple(
        (
            EQUAL_MEAN_COEFFICIENT
            * (a.to(torch.float64) + b.to(torch.float64))
        ).to(parameter.dtype)
        for a, b, parameter in zip(left, right, parameters)
    )
    if any(not bool(torch.isfinite(row).all()) for row in rows):
        raise G45GradientGateError("equal_mean_nonfinite", {})
    return rows


def _add_entropy(
    credit: Sequence[torch.Tensor], entropy: Sequence[torch.Tensor]
) -> tuple[torch.Tensor, ...]:
    if len(credit) != len(entropy):
        raise G45GradientGateError("entropy_gradient_inventory_mismatch", {})
    rows = tuple(
        (a.to(torch.float64) + b.to(torch.float64)).to(a.dtype)
        for a, b in zip(credit, entropy)
    )
    if any(not bool(torch.isfinite(row).all()) for row in rows):
        raise G45GradientGateError("credit_plus_entropy_nonfinite", {})
    return rows


def _scale_to_counterfactual_norm(
    raw: Sequence[torch.Tensor],
    parameters: Sequence[nn.Parameter],
    *,
    counterfactual_norm: float,
) -> tuple[tuple[torch.Tensor, ...], dict[str, object]]:
    rows = _gradient_rows(raw, parameters)
    raw_norm = _global_norm(rows)
    if any(
        not np.isfinite(value) or value < 0.0
        for value in (raw_norm, counterfactual_norm)
    ):
        raise G45GradientGateError(
            "no_read_norm_nonfinite_or_negative",
            {"raw_norm": raw_norm, "counterfactual_norm": counterfactual_norm},
        )
    if counterfactual_norm == 0.0:
        assigned = tuple(torch.zeros_like(parameter) for parameter in parameters)
        scale = 0.0
    elif raw_norm == 0.0:
        raise G45GradientGateError(
            "positive_counterfactual_norm_with_zero_no_read_direction",
            {"counterfactual_norm": counterfactual_norm},
        )
    else:
        scale = counterfactual_norm / raw_norm
        assigned = tuple(
            (row.to(torch.float64) * scale).to(parameter.dtype)
            for row, parameter in zip(rows, parameters)
        )
    assigned_norm = _global_norm(assigned)
    error = abs(assigned_norm - counterfactual_norm)
    tolerance = SCALE_MATCH_ATOL + SCALE_MATCH_RTOL * abs(counterfactual_norm)
    if error > tolerance:
        raise G45GradientGateError(
            "no_read_counterfactual_norm_match_failed",
            {
                "assigned_norm": assigned_norm,
                "counterfactual_norm": counterfactual_norm,
                "error": error,
                "tolerance": tolerance,
            },
        )
    return assigned, {
        "raw_credit_norm": raw_norm,
        "baseline_read_counterfactual_credit_norm": counterfactual_norm,
        "assigned_credit_norm": assigned_norm,
        "scale": scale,
        "assigned_norm_match_error": error,
        "assigned_norm_match_tolerance": tolerance,
        "actual_residual_baseline_read_count": 0,
        "actual_direction_baseline_coordinate_read_count": 0,
        "counterfactual_baseline_scalar_shadow": True,
        "counterfactual_shadow_output_type": "one_detached_scalar_credit_norm",
        "counterfactual_vector_serialized": False,
        "counterfactual_vector_coordinate_use_outside_norm": 0,
        "counterfactual_gradient_assignment_count": 0,
        "counterfactual_optimizer_state_count": 0,
        "counterfactual_RNG_consumption": 0,
        "counterfactual_model_mutation_count": 0,
        "baseline_target_fitting_retained": True,
        "baseline_action_or_logprob_read_count": 0,
        "baseline_checkpoint_selection_read_count": 0,
        "baseline_evaluation_metric_read_count": 0,
        "actor_credit_gradients_exact_zero": all(
            bool(torch.count_nonzero(row) == 0) for row in assigned
        ),
        "passed": True,
    }


def _direction_scalar_evidence(
    left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]
) -> tuple[float, float, float, float]:
    left_norm = _global_norm(left)
    right_norm = _global_norm(right)
    dot = float(
        sum(
            (a.detach().to(torch.float64) * b.detach().to(torch.float64)).sum()
            for a, b in zip(left, right)
        )
    )
    if left_norm > 0.0 and right_norm > 0.0:
        cosine = max(-1.0, min(1.0, dot / (left_norm * right_norm)))
        distance = float(np.sqrt(max(0.0, 2.0 - 2.0 * cosine)))
    else:
        distance = 0.0
    if any(not np.isfinite(value) for value in (left_norm, right_norm, dot, distance)):
        raise G45GradientGateError("direction_scalar_evidence_nonfinite", {})
    return left_norm, right_norm, dot, distance


def _gradient_probe(
    model: g41.G41NoSlowProjection,
    replay: g41.G41RetainedReplay,
    trajectory: AnchoredRosterTrajectory,
    credit: g41.G41Credit,
    normalized_advantages: tuple[torch.Tensor, torch.Tensor],
) -> _GradientProbe:
    actor_parameters = model.full_actor_parameters()
    baseline_parameters = tuple(model.credit_baselines.parameters())
    immediate = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized_advantages[0]
    )
    successor = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized_advantages[1]
    )
    entropy_objective = -g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
    immediate_actor = _gradient_rows(
        torch.autograd.grad(
            immediate, actor_parameters, retain_graph=True, allow_unused=True
        ),
        actor_parameters,
    )
    successor_actor = _gradient_rows(
        torch.autograd.grad(
            successor, actor_parameters, retain_graph=True, allow_unused=True
        ),
        actor_parameters,
    )
    entropy = _gradient_rows(
        torch.autograd.grad(
            entropy_objective,
            actor_parameters,
            retain_graph=True,
            allow_unused=True,
        ),
        actor_parameters,
    )
    immediate_loss = F.mse_loss(
        replay.immediate_baselines, trajectory.rewards.detach()
    )
    successor_loss = F.mse_loss(
        replay.successor_baselines, credit.successor_targets
    )
    immediate_baseline = _gradient_rows(
        torch.autograd.grad(
            immediate_loss,
            baseline_parameters,
            retain_graph=True,
            allow_unused=True,
        ),
        baseline_parameters,
    )
    successor_baseline = _gradient_rows(
        torch.autograd.grad(
            successor_loss,
            baseline_parameters,
            retain_graph=True,
            allow_unused=True,
        ),
        baseline_parameters,
    )
    evidence = registered_gradient_evidence(
        model,
        immediate_actor,
        successor_actor,
        immediate_baseline,
        successor_baseline,
    )
    if not validate_registered_gradient_evidence(evidence):
        raise G45GradientGateError("registered_gradient_evidence_failed", evidence)
    return _GradientProbe(
        policy=EQUAL_MEAN_COEFFICIENT * (immediate + successor)
        + entropy_objective,
        immediate_baseline_loss=immediate_loss,
        successor_baseline_loss=successor_loss,
        immediate_credit_gradients=immediate_actor,
        successor_credit_gradients=successor_actor,
        entropy_gradients=entropy,
        immediate_baseline_gradients=immediate_baseline,
        successor_baseline_gradients=successor_baseline,
        gradient_evidence=evidence,
    )


def _channel_evidence(
    *,
    residual_law_id: str,
    residual: torch.Tensor,
    normalized: torch.Tensor,
    mean: float,
    centered_sum_square: float,
    scale: float,
) -> dict[str, object]:
    return {
        "residual_law_id": residual_law_id,
        "residual_mean": mean,
        "centered_sum_square": centered_sum_square,
        "RMS_scale": scale,
        "residual_digest": _tensor_digest(residual),
        "normalized_row_digest": _tensor_digest(normalized),
        "normalization_row_count": NORMALIZATION_ROWS,
        "normalization_mask_digest": NORMALIZATION_MASK_DIGEST,
    }


def _arm_credit_evidence(
    arm: str,
    trajectory: AnchoredRosterTrajectory,
    credit: g41.G41Credit,
    normalization: g44.ChannelNormalization,
) -> dict[str, object]:
    if arm not in ARMS:
        raise ValueError("G45 residual evidence arm is not registered")
    law = READ_RESIDUAL_LAW if arm == BASELINE_READ_ARM else NO_READ_RESIDUAL_LAW
    return {
        "arm": arm,
        "residual_law_id": law,
        "channels": {
            "immediate": _channel_evidence(
                residual_law_id=("r_minus_bI" if arm == BASELINE_READ_ARM else "r"),
                residual=credit.immediate_advantage,
                normalized=normalization.independent_immediate,
                mean=normalization.immediate_mean,
                centered_sum_square=normalization.immediate_centered_sum_square,
                scale=normalization.immediate_scale,
            ),
            "successor": _channel_evidence(
                residual_law_id=(
                    "Gnext_minus_bS" if arm == BASELINE_READ_ARM else "Gnext"
                ),
                residual=credit.successor_advantage,
                normalized=normalization.independent_successor,
                mean=normalization.successor_mean,
                centered_sum_square=normalization.successor_centered_sum_square,
                scale=normalization.successor_scale,
            ),
        },
        "primitive_row_count": NORMALIZATION_ROWS,
        "primitive_row_mask_digest": NORMALIZATION_MASK_DIGEST,
        "episode_id_digest": _sequence_digest(_episode_ids(trajectory)),
        "true_current_state_input_digest": _tensor_digest(trajectory.critic_states),
        "immediate_target_digest": _tensor_digest(trajectory.rewards.detach()),
        "successor_target_digest": _tensor_digest(credit.successor_targets),
        "immediate_baseline_output_digest": _tensor_digest(
            trajectory.old_immediate_baselines
        ),
        "successor_baseline_output_digest": _tensor_digest(
            trajectory.old_successor_baselines
        ),
        "baseline_predictions_frozen_across_both_passes": True,
        "normalization_count": 1,
        "normalization_recomputed_between_passes": False,
        "actual_residual_baseline_read_count": (
            2 if arm == BASELINE_READ_ARM else 0
        ),
        "actual_direction_baseline_coordinate_read_count": (
            2 if arm == BASELINE_READ_ARM else 0
        ),
        "passed": True,
    }


def validate_arm_credit_evidence(value: object, arm: str) -> bool:
    if not isinstance(value, Mapping) or arm not in ARMS:
        return False
    expected_law = READ_RESIDUAL_LAW if arm == BASELINE_READ_ARM else NO_READ_RESIDUAL_LAW
    channels = value.get("channels")
    if (
        value.get("passed") is not True
        or value.get("arm") != arm
        or value.get("residual_law_id") != expected_law
        or not isinstance(channels, Mapping)
        or tuple(channels) != ("immediate", "successor")
        or value.get("primitive_row_count") != NORMALIZATION_ROWS
        or value.get("primitive_row_mask_digest") != NORMALIZATION_MASK_DIGEST
        or value.get("baseline_predictions_frozen_across_both_passes") is not True
        or value.get("normalization_count") != 1
        or value.get("normalization_recomputed_between_passes") is not False
    ):
        return False
    for name, law in (
        (
            "immediate",
            "r_minus_bI" if arm == BASELINE_READ_ARM else "r",
        ),
        (
            "successor",
            "Gnext_minus_bS" if arm == BASELINE_READ_ARM else "Gnext",
        ),
    ):
        row = channels.get(name)
        if not isinstance(row, Mapping) or row.get("residual_law_id") != law:
            return False
        numbers = ("residual_mean", "centered_sum_square", "RMS_scale")
        if any(
            isinstance(row.get(field), bool)
            or not isinstance(row.get(field), (int, float))
            or not np.isfinite(float(row[field]))
            or (field != "residual_mean" and float(row[field]) < 0.0)
            for field in numbers
        ):
            return False
        expected_scale = float(
            torch.sqrt(
                torch.as_tensor(
                    float(row["centered_sum_square"]), dtype=torch.float64
                )
                / float(NORMALIZATION_ROWS)
            )
        )
        if (
            float(row["RMS_scale"]) != expected_scale
            or row.get("normalization_row_count") != NORMALIZATION_ROWS
            or row.get("normalization_mask_digest") != NORMALIZATION_MASK_DIGEST
            or any(
                not isinstance(row.get(field), str)
                or len(str(row[field])) != 64
                for field in ("residual_digest", "normalized_row_digest")
            )
        ):
            return False
    digest_fields = (
        "episode_id_digest",
        "true_current_state_input_digest",
        "immediate_target_digest",
        "successor_target_digest",
        "immediate_baseline_output_digest",
        "successor_baseline_output_digest",
    )
    if any(
        not isinstance(value.get(field), str) or len(str(value[field])) != 64
        for field in digest_fields
    ):
        return False
    expected_reads = 2 if arm == BASELINE_READ_ARM else 0
    return bool(
        value.get("actual_residual_baseline_read_count") == expected_reads
        and value.get("actual_direction_baseline_coordinate_read_count")
        == expected_reads
    )


def project_g45_arms(
    anchor: g40.G40NativeSixPolicy, *, accepted_anchor_replicate: int
) -> dict[str, g41.G41NoSlowProjection]:
    if accepted_anchor_replicate not in ACCEPTED_G40_ANCHOR_REPLICATES:
        raise ValueError("G45 requires accepted G40 anchor replicate 0, 1, or 2")
    rng_before = torch.random.get_rng_state().clone()
    g44_models = g44.project_g44_arms(
        anchor, accepted_anchor_replicate=accepted_anchor_replicate
    )
    models = {
        BASELINE_READ_ARM: g44_models[g44.INDEPENDENT_ARM],
        BASELINE_SHADOW_NO_READ_ARM: g44_models[g44.POOLED_ARM],
    }
    if g40.state_bytes(models[BASELINE_READ_ARM]) != g40.state_bytes(
        models[BASELINE_SHADOW_NO_READ_ARM]
    ):
        raise RuntimeError("G45 branch states differ before treatment")
    if g40.shared_tensor_storage_count((anchor, *models.values())) != 0:
        raise RuntimeError("G45 projection shares retained storage")
    if any(hasattr(model, "slow_critic") for model in models.values()):
        raise RuntimeError("G45 reintroduced the standalone slow critic")
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise RuntimeError("G45 projection advanced model RNG")
    return models


# Compatibility names consumed by accepted G43/G44 isolated orchestration.
project_g43_arms = project_g45_arms
project_g44_arms = project_g45_arms


def _optimizer_step_value(
    optimizer: torch.optim.Optimizer, parameter: nn.Parameter
) -> float:
    return g43._optimizer_step_value(optimizer, parameter)


def _optimizer_owns_actor_head(
    optimizer: torch.optim.Optimizer, model: g41.G41NoSlowProjection
) -> bool:
    return g44._optimizer_owns_actor_head(optimizer, model)


def branch_boundary_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS:
        return {"passed": False, "inventory_valid": False}
    remapped_models = {
        g44.INDEPENDENT_ARM: models[BASELINE_READ_ARM],
        g44.POOLED_ARM: models[BASELINE_SHADOW_NO_READ_ARM],
    }
    remapped_optimizers = {
        g44.INDEPENDENT_ARM: optimizers[BASELINE_READ_ARM],
        g44.POOLED_ARM: optimizers[BASELINE_SHADOW_NO_READ_ARM],
    }
    base = g44.branch_boundary_audit(remapped_models, remapped_optimizers)
    provenance = bool(
        ACCEPTED_G40_SOURCE_COMMIT == g44.ACCEPTED_G40_SOURCE_COMMIT
        and ACCEPTED_G41_SOURCE_COMMIT == g44.ACCEPTED_G41_SOURCE_COMMIT
        and len(ACCEPTED_G44_FORMAL_SOURCE_COMMIT) == 40
        and len(ACCEPTED_G44_ALIGNED_SOURCE_COMMIT) == 40
        and len(ACCEPTED_G44_ALIGNMENT_STAGE_COMMIT) == 40
    )
    state_equal = g40.state_bytes(models[BASELINE_READ_ARM]) == g40.state_bytes(
        models[BASELINE_SHADOW_NO_READ_ARM]
    )
    storage_disjoint = g40.shared_tensor_storage_count(tuple(models.values())) == 0
    optimizer_empty_separate = bool(
        all(optimizer.state == {} for optimizer in optimizers.values())
        and id(optimizers[BASELINE_READ_ARM].state)
        != id(optimizers[BASELINE_SHADOW_NO_READ_ARM].state)
    )
    return {
        **base,
        "arms": list(ARMS),
        "accepted_g40_source_commit": ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g44_formal_source_commit": ACCEPTED_G44_FORMAL_SOURCE_COMMIT,
        "accepted_g44_aligned_source_commit": ACCEPTED_G44_ALIGNED_SOURCE_COMMIT,
        "accepted_g44_alignment_stage_commit": ACCEPTED_G44_ALIGNMENT_STAGE_COMMIT,
        "model_state_bytes_equal": state_equal,
        "baseline_schema_equal": g40.baseline_inventory(models[BASELINE_READ_ARM])
        == g40.baseline_inventory(models[BASELINE_SHADOW_NO_READ_ARM]),
        "shared_parameter_buffer_gradient_optimizer_storage_count": 0
        if storage_disjoint and optimizer_empty_separate
        else 1,
        "optimizer_states_empty_and_separate": optimizer_empty_separate,
        "provenance_valid": provenance,
        "passed": bool(
            base.get("passed") is True
            and provenance
            and state_equal
            and storage_disjoint
            and optimizer_empty_separate
        ),
    }


def _continuation_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    *,
    update_index: int,
) -> dict[str, object]:
    if update_index == 0:
        return branch_boundary_audit(models, optimizers)
    expected = float(update_index * PPO_PASSES)
    inventory = tuple(models) == ARMS and tuple(optimizers) == ARMS
    steps = bool(
        inventory
        and all(
            all(
                _optimizer_step_value(optimizers[arm], parameter) == expected
                for parameter in models[arm].actor_credit_parameters()
            )
            for arm in ARMS
        )
    )
    authority = bool(
        inventory
        and all(
            model.accepted_g40_anchor_authority
            == g41.accepted_g40_anchor_authority(
                model.accepted_g40_anchor_authority.replicate
            )
            for model in models.values()
        )
    )
    return {
        "inventory_valid": inventory,
        "continuation": True,
        "update_index": update_index,
        "accepted_g40_anchor_authority": (
            g41.accepted_g40_anchor_identity(
                models[BASELINE_READ_ARM].accepted_g40_anchor_authority.replicate
            )
            if authority
            else None
        ),
        "authority_valid": authority,
        "optimizer_expected_step_before": expected,
        "optimizer_step_state_valid": steps,
        "passed": bool(
            inventory
            and authority
            and steps
            and all(model.phase == "credit_branch" for model in models.values())
            and all(not hasattr(model, "slow_critic") for model in models.values())
        ),
    }


def _activation_record(
    trajectory: AnchoredRosterTrajectory,
    read_credit: Sequence[torch.Tensor],
    no_read_counterfactual_credit: Sequence[torch.Tensor],
) -> dict[str, object]:
    read_norm, no_read_norm, dot, q_direction = _direction_scalar_evidence(
        read_credit, no_read_counterfactual_credit
    )
    immediate_rms = _centered_rms(trajectory.old_immediate_baselines)
    successor_rms = _centered_rms(trajectory.old_successor_baselines)
    q_baseline = max(immediate_rms, successor_rms)
    values = (
        immediate_rms,
        successor_rms,
        q_baseline,
        read_norm,
        no_read_norm,
        q_direction,
    )
    if any(not np.isfinite(value) or value < 0.0 for value in values):
        raise G45GradientGateError("activation_scalar_nonfinite_or_negative", {})
    active = bool(
        q_baseline > ACTIVATION_TOLERANCE
        and q_direction > ACTIVATION_TOLERANCE
        and read_norm > 0.0
        and no_read_norm > 0.0
    )
    record = {
        "centered_immediate_baseline_RMS": immediate_rms,
        "centered_successor_baseline_RMS": successor_rms,
        "q_baseline": q_baseline,
        "reference_READ_credit_norm": read_norm,
        "reference_NO_READ_counterfactual_credit_norm": no_read_norm,
        "reference_credit_dot_product": dot,
        "q_direction": q_direction,
        "reference_immediate_baseline_output_digest": _tensor_digest(
            trajectory.old_immediate_baselines
        ),
        "reference_successor_baseline_output_digest": _tensor_digest(
            trajectory.old_successor_baselines
        ),
        "activation_threshold": ACTIVATION_TOLERANCE,
        "evidence_source_arm": BASELINE_READ_ARM,
        "reference_no_read_counterfactual": True,
        "no_read_arm_evidence_read_count": 0,
        "strict_activation_observed": active,
        "passed": True,
    }
    if not validate_activation_record(record):
        raise G45GradientGateError("activation_record_invalid", record)
    return record


def validate_activation_record(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    names = (
        "centered_immediate_baseline_RMS",
        "centered_successor_baseline_RMS",
        "q_baseline",
        "reference_READ_credit_norm",
        "reference_NO_READ_counterfactual_credit_norm",
        "reference_credit_dot_product",
        "q_direction",
    )
    if any(
        isinstance(value.get(name), bool)
        or not isinstance(value.get(name), (int, float))
        or not np.isfinite(float(value[name]))
        or (
            name != "reference_credit_dot_product" and float(value[name]) < 0.0
        )
        for name in names
    ):
        return False
    read_norm = float(value["reference_READ_credit_norm"])
    no_read_norm = float(value["reference_NO_READ_counterfactual_credit_norm"])
    if read_norm > 0.0 and no_read_norm > 0.0:
        cosine = max(
            -1.0,
            min(
                1.0,
                float(value["reference_credit_dot_product"])
                / (read_norm * no_read_norm),
            ),
        )
        q_direction = float(np.sqrt(max(0.0, 2.0 - 2.0 * cosine)))
    else:
        q_direction = 0.0
    q_baseline = max(
        float(value["centered_immediate_baseline_RMS"]),
        float(value["centered_successor_baseline_RMS"]),
    )
    active = bool(
        q_baseline > ACTIVATION_TOLERANCE
        and q_direction > ACTIVATION_TOLERANCE
        and read_norm > 0.0
        and no_read_norm > 0.0
    )
    return bool(
        float(value["q_baseline"]) == q_baseline
        and float(value["q_direction"]) == q_direction
        and value.get("activation_threshold") == ACTIVATION_TOLERANCE
        and value.get("evidence_source_arm") == BASELINE_READ_ARM
        and value.get("reference_no_read_counterfactual") is True
        and value.get("no_read_arm_evidence_read_count") == 0
        and value.get("strict_activation_observed") is active
        and all(
            isinstance(value.get(field), str) and len(str(value[field])) == 64
            for field in (
                "reference_immediate_baseline_output_digest",
                "reference_successor_baseline_output_digest",
            )
        )
    )


def _direct_treatment_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    credits: Mapping[str, g41.G41Credit],
    probes: Mapping[str, _GradientProbe],
    residual_evidence: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    left = models[BASELINE_READ_ARM]
    right = models[BASELINE_SHADOW_NO_READ_ARM]
    trajectory = g40.branch_trajectory_match(
        trajectories[BASELINE_READ_ARM],
        trajectories[BASELINE_SHADOW_NO_READ_ARM],
    )
    baseline_terms_equal = bool(
        torch.equal(
            probes[BASELINE_READ_ARM].immediate_baseline_loss,
            probes[BASELINE_SHADOW_NO_READ_ARM].immediate_baseline_loss,
        )
        and torch.equal(
            probes[BASELINE_READ_ARM].successor_baseline_loss,
            probes[BASELINE_SHADOW_NO_READ_ARM].successor_baseline_loss,
        )
        and _rows_bitwise_equal(
            probes[BASELINE_READ_ARM].immediate_baseline_gradients,
            probes[BASELINE_SHADOW_NO_READ_ARM].immediate_baseline_gradients,
        )
        and _rows_bitwise_equal(
            probes[BASELINE_READ_ARM].successor_baseline_gradients,
            probes[BASELINE_SHADOW_NO_READ_ARM].successor_baseline_gradients,
        )
    )
    entropy_equal = _rows_bitwise_equal(
        probes[BASELINE_READ_ARM].entropy_gradients,
        probes[BASELINE_SHADOW_NO_READ_ARM].entropy_gradients,
    )
    target_equal = bool(
        torch.equal(
            credits[BASELINE_READ_ARM].returns,
            credits[BASELINE_SHADOW_NO_READ_ARM].returns,
        )
        and torch.equal(
            credits[BASELINE_READ_ARM].successor_targets,
            credits[BASELINE_SHADOW_NO_READ_ARM].successor_targets,
        )
    )
    read_row = residual_evidence[BASELINE_READ_ARM]
    no_read_row = residual_evidence[BASELINE_SHADOW_NO_READ_ARM]
    shared_evidence = all(
        read_row[name] == no_read_row[name]
        for name in (
            "primitive_row_count",
            "primitive_row_mask_digest",
            "episode_id_digest",
            "true_current_state_input_digest",
            "immediate_target_digest",
            "successor_target_digest",
            "immediate_baseline_output_digest",
            "successor_baseline_output_digest",
        )
    )
    only_residual_law_differs = bool(
        read_row["residual_law_id"] == READ_RESIDUAL_LAW
        and no_read_row["residual_law_id"] == NO_READ_RESIDUAL_LAW
        and shared_evidence
    )
    passed = bool(
        trajectory["passed"] is True
        and g40.state_bytes(left.policy) == g40.state_bytes(right.policy)
        and torch.equal(left.log_std, right.log_std)
        and g40.state_bytes(left.credit_baselines)
        == g40.state_bytes(right.credit_baselines)
        and target_equal
        and baseline_terms_equal
        and entropy_equal
        and only_residual_law_differs
        and all(optimizer.state == {} for optimizer in optimizers.values())
    )
    return {
        "trajectory_bitwise_equal": trajectory["passed"],
        "actor_bytes_equal": g40.state_bytes(left.policy)
        == g40.state_bytes(right.policy),
        "log_std_bitwise_equal": torch.equal(left.log_std, right.log_std),
        "shared_baseline_bytes_equal": g40.state_bytes(left.credit_baselines)
        == g40.state_bytes(right.credit_baselines),
        "targets_bitwise_equal": target_equal,
        "baseline_losses_and_gradients_bitwise_equal": baseline_terms_equal,
        "entropy_rule_and_gradients_bitwise_equal": entropy_equal,
        "only_permitted_difference_is_residual_baseline_read": (
            only_residual_law_differs
        ),
        "optimizer_states_empty": all(
            optimizer.state == {} for optimizer in optimizers.values()
        ),
        "passed": passed,
    }


def order_swap_guard(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    plans: Mapping[str, _PassPlan],
) -> dict[str, object]:
    inventory = (
        tuple(models) == ARMS and tuple(optimizers) == ARMS and tuple(plans) == ARMS
    )
    model_storage = bool(
        inventory
        and g40.shared_tensor_storage_count(tuple(models.values())) == 0
        and id(optimizers[BASELINE_READ_ARM].state)
        != id(optimizers[BASELINE_SHADOW_NO_READ_ARM].state)
    )
    gradient_storage = bool(
        inventory
        and not {
            row.untyped_storage().data_ptr()
            for row in plans[BASELINE_READ_ARM].gradients
        }.intersection(
            row.untyped_storage().data_ptr()
            for row in plans[BASELINE_SHADOW_NO_READ_ARM].gradients
        )
    )
    return {
        "guard_kind": "precomputed_plan_disjoint_storage_commutativity",
        "plans_materialized_before_either_optimizer": inventory,
        "registered_order": list(ARMS),
        "swapped_order": list(reversed(ARMS)),
        "model_optimizer_storage_disjoint": model_storage,
        "assigned_gradient_storage_disjoint": gradient_storage,
        "diagnostic_optimizer_steps": 0,
        "passed": bool(inventory and model_storage and gradient_storage),
    }


def _apply_pass(
    arm: str,
    model: g41.G41NoSlowProjection,
    optimizer: torch.optim.Optimizer,
    plan: _PassPlan,
) -> tuple[float, float, float]:
    if arm not in ARMS or not isinstance(optimizer, torch.optim.Adam):
        raise ValueError("G45 optimizer arm/type mismatch")
    actor_parameters = model.full_actor_parameters()
    all_parameters = model.actor_credit_parameters()
    before = tuple(
        _optimizer_step_value(optimizer, parameter) for parameter in all_parameters
    )
    optimizer.zero_grad(set_to_none=True)
    (plan.immediate_baseline_loss + plan.successor_baseline_loss).backward()
    for parameter, gradient in zip(actor_parameters, plan.gradients):
        parameter.grad = gradient.clone()
    if any(parameter.grad is None for parameter in all_parameters):
        raise G45GradientGateError("stale_or_missing_gradient", {"arm": arm})
    g40._optimizer_step(optimizer, all_parameters)
    after = tuple(
        _optimizer_step_value(optimizer, parameter) for parameter in all_parameters
    )
    if any(value != prior + 1.0 for prior, value in zip(before, after)):
        raise RuntimeError("G45 Adam exposure did not advance exactly once")
    return (
        float(plan.policy.detach()),
        float(plan.immediate_baseline_loss.detach()),
        float(plan.successor_baseline_loss.detach()),
    )


def _prepare_passes(
    models: Mapping[str, g41.G41NoSlowProjection],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    read_credits: Mapping[str, g41.G41Credit],
    no_read_credits: Mapping[str, g41.G41Credit],
    read_normalizations: Mapping[str, g44.ChannelNormalization],
    no_read_normalizations: Mapping[str, g44.ChannelNormalization],
) -> tuple[
    dict[str, _PassPlan],
    dict[str, _GradientProbe],
    dict[str, _GradientProbe],
    dict[str, object],
]:
    replays = {
        arm: g41.retained_replay(models[arm], trajectories[arm]) for arm in ARMS
    }
    read_probes = {
        arm: _gradient_probe(
            models[arm],
            replays[arm],
            trajectories[arm],
            read_credits[arm],
            (
                read_normalizations[arm].independent_immediate,
                read_normalizations[arm].independent_successor,
            ),
        )
        for arm in ARMS
    }
    no_read_probes = {
        arm: _gradient_probe(
            models[arm],
            replays[arm],
            trajectories[arm],
            no_read_credits[arm],
            (
                no_read_normalizations[arm].independent_immediate,
                no_read_normalizations[arm].independent_successor,
            ),
        )
        for arm in ARMS
    }
    common_terms_equal = {
        arm: bool(
            _rows_bitwise_equal(
                read_probes[arm].entropy_gradients,
                no_read_probes[arm].entropy_gradients,
            )
            and torch.equal(
                read_probes[arm].immediate_baseline_loss,
                no_read_probes[arm].immediate_baseline_loss,
            )
            and torch.equal(
                read_probes[arm].successor_baseline_loss,
                no_read_probes[arm].successor_baseline_loss,
            )
            and _rows_bitwise_equal(
                read_probes[arm].immediate_baseline_gradients,
                no_read_probes[arm].immediate_baseline_gradients,
            )
            and _rows_bitwise_equal(
                read_probes[arm].successor_baseline_gradients,
                no_read_probes[arm].successor_baseline_gradients,
            )
        )
        for arm in ARMS
    }
    if not all(common_terms_equal.values()):
        raise G45GradientGateError(
            "baseline_read_changed_entropy_or_baseline_terms",
            {"arm_equality": common_terms_equal},
        )
    read_credit = _equal_mean(
        read_probes[BASELINE_READ_ARM].immediate_credit_gradients,
        read_probes[BASELINE_READ_ARM].successor_credit_gradients,
        models[BASELINE_READ_ARM].full_actor_parameters(),
    )
    reference_no_read_counterfactual = _equal_mean(
        no_read_probes[BASELINE_READ_ARM].immediate_credit_gradients,
        no_read_probes[BASELINE_READ_ARM].successor_credit_gradients,
        models[BASELINE_READ_ARM].full_actor_parameters(),
    )
    no_read_raw = _equal_mean(
        no_read_probes[BASELINE_SHADOW_NO_READ_ARM].immediate_credit_gradients,
        no_read_probes[BASELINE_SHADOW_NO_READ_ARM].successor_credit_gradients,
        models[BASELINE_SHADOW_NO_READ_ARM].full_actor_parameters(),
    )
    local_read_counterfactual = _equal_mean(
        read_probes[BASELINE_SHADOW_NO_READ_ARM].immediate_credit_gradients,
        read_probes[BASELINE_SHADOW_NO_READ_ARM].successor_credit_gradients,
        models[BASELINE_SHADOW_NO_READ_ARM].full_actor_parameters(),
    )
    no_read_assigned, shadow = _scale_to_counterfactual_norm(
        no_read_raw,
        models[BASELINE_SHADOW_NO_READ_ARM].full_actor_parameters(),
        counterfactual_norm=_global_norm(local_read_counterfactual),
    )
    read_with_entropy = _add_entropy(
        read_credit, read_probes[BASELINE_READ_ARM].entropy_gradients
    )
    no_read_with_entropy = _add_entropy(
        no_read_assigned,
        no_read_probes[BASELINE_SHADOW_NO_READ_ARM].entropy_gradients,
    )
    activation = _activation_record(
        trajectories[BASELINE_READ_ARM],
        read_credit,
        reference_no_read_counterfactual,
    )
    plans = {
        BASELINE_READ_ARM: _PassPlan(
            policy=read_probes[BASELINE_READ_ARM].policy,
            immediate_baseline_loss=read_probes[
                BASELINE_READ_ARM
            ].immediate_baseline_loss,
            successor_baseline_loss=read_probes[
                BASELINE_READ_ARM
            ].successor_baseline_loss,
            gradients=read_with_entropy,
            gradient_evidence=read_probes[BASELINE_READ_ARM].gradient_evidence,
            composition_record={
                "mode": "independent_scale_baseline_read",
                "literal_coefficient": EQUAL_MEAN_COEFFICIENT,
                "residual_law_id": READ_RESIDUAL_LAW,
                "actual_residual_baseline_read_count": 2,
                "actual_direction_baseline_coordinate_read_count": 2,
                "credit_norm_before_entropy": _global_norm(read_credit),
                "entropy_gradient_norm": _global_norm(
                    read_probes[BASELINE_READ_ARM].entropy_gradients
                ),
                "assigned_actor_gradient_norm": _global_norm(read_with_entropy),
                "entropy_added_after_credit_gate": True,
                "baseline_target_fitting_retained": True,
                "passed": True,
            },
        ),
        BASELINE_SHADOW_NO_READ_ARM: _PassPlan(
            policy=no_read_probes[BASELINE_SHADOW_NO_READ_ARM].policy,
            immediate_baseline_loss=no_read_probes[
                BASELINE_SHADOW_NO_READ_ARM
            ].immediate_baseline_loss,
            successor_baseline_loss=no_read_probes[
                BASELINE_SHADOW_NO_READ_ARM
            ].successor_baseline_loss,
            gradients=no_read_with_entropy,
            gradient_evidence=no_read_probes[
                BASELINE_SHADOW_NO_READ_ARM
            ].gradient_evidence,
            composition_record={
                "mode": "independent_scale_baseline_shadow_no_read_norm_matched",
                "literal_coefficient": EQUAL_MEAN_COEFFICIENT,
                "residual_law_id": NO_READ_RESIDUAL_LAW,
                **shadow,
                "entropy_gradient_norm": _global_norm(
                    no_read_probes[BASELINE_SHADOW_NO_READ_ARM].entropy_gradients
                ),
                "assigned_actor_gradient_norm": _global_norm(no_read_with_entropy),
                "entropy_added_after_credit_gate": True,
            },
        ),
    }
    return plans, read_probes, no_read_probes, activation


def _canonical_residual_evidence(
    value: Mapping[str, object],
) -> dict[str, object]:
    if tuple(value) != ARMS or any(
        not validate_arm_credit_evidence(value.get(arm), arm) for arm in ARMS
    ):
        raise ValueError("G45 per-arm residual evidence invalid")
    return json.loads(json.dumps(value, sort_keys=True))


def optimize_baseline_conditioning_update(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory] | AnchoredRosterTrajectory,
    *,
    update_index: int = 0,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, object]:
    if int(ppo_passes) != PPO_PASSES:
        raise ValueError("G45 requires exactly two PPO passes")
    if (
        isinstance(update_index, bool)
        or not isinstance(update_index, int)
        or update_index < 0
    ):
        raise ValueError("G45 update index must be a nonnegative integer")
    trajectory_map = (
        {arm: trajectories for arm in ARMS}
        if isinstance(trajectories, AnchoredRosterTrajectory)
        else dict(trajectories)
    )
    if tuple(trajectory_map) != ARMS or any(
        trajectory.rewards.numel() != MAX_CONFORMANCE_TRANSITIONS
        for trajectory in trajectory_map.values()
    ):
        raise ValueError("G45 update requires paired 8x48 real trajectories")
    boundary = _continuation_audit(models, optimizers, update_index=update_index)
    if boundary.get("passed") is not True:
        raise ValueError("G45 branch boundary failed before optimizer step")

    read_credits = {arm: _read_credit(trajectory_map[arm]) for arm in ARMS}
    no_read_credits = {arm: _no_read_credit(trajectory_map[arm]) for arm in ARMS}
    actual_credits = {
        BASELINE_READ_ARM: read_credits[BASELINE_READ_ARM],
        BASELINE_SHADOW_NO_READ_ARM: no_read_credits[
            BASELINE_SHADOW_NO_READ_ARM
        ],
    }
    read_normalizations = {
        arm: _normalize_credit(read_credits[arm]) for arm in ARMS
    }
    no_read_normalizations = {
        arm: _normalize_credit(no_read_credits[arm]) for arm in ARMS
    }
    actual_normalizations = {
        BASELINE_READ_ARM: read_normalizations[BASELINE_READ_ARM],
        BASELINE_SHADOW_NO_READ_ARM: no_read_normalizations[
            BASELINE_SHADOW_NO_READ_ARM
        ],
    }
    residual_evidence = {
        arm: _arm_credit_evidence(
            arm,
            trajectory_map[arm],
            actual_credits[arm],
            actual_normalizations[arm],
        )
        for arm in ARMS
    }
    canonical_residual_evidence = _canonical_residual_evidence(
        residual_evidence
    )
    steps_before = {
        arm: min(
            _optimizer_step_value(optimizers[arm], parameter)
            for parameter in models[arm].actor_credit_parameters()
        )
        for arm in ARMS
    }
    rng_before = torch.random.get_rng_state().clone()
    pass_records: list[dict[str, object]] = []
    direct_audit: dict[str, object] | None = None
    swap_guard: dict[str, object] | None = None
    for pass_index in range(PPO_PASSES):
        plans, read_probes, no_read_probes, activation = _prepare_passes(
            models,
            trajectory_map,
            read_credits,
            no_read_credits,
            read_normalizations,
            no_read_normalizations,
        )
        actual_probes = {
            BASELINE_READ_ARM: read_probes[BASELINE_READ_ARM],
            BASELINE_SHADOW_NO_READ_ARM: no_read_probes[
                BASELINE_SHADOW_NO_READ_ARM
            ],
        }
        if update_index == 0 and pass_index == 0:
            direct_audit = _direct_treatment_audit(
                models,
                optimizers,
                trajectory_map,
                actual_credits,
                actual_probes,
                residual_evidence,
            )
            if direct_audit.get("passed") is not True:
                raise G45GradientGateError(
                    "first_paired_direct_treatment_mismatch", direct_audit
                )
            swap_guard = order_swap_guard(models, optimizers, plans)
            if swap_guard.get("passed") is not True:
                raise G45GradientGateError("order_swap_guard_failed", swap_guard)
        metrics = {
            arm: _apply_pass(arm, models[arm], optimizers[arm], plans[arm])
            for arm in ARMS
        }
        pass_records.append(
            {
                "pass_index": pass_index,
                "gradient_evidence": {
                    arm: plans[arm].gradient_evidence for arm in ARMS
                },
                "composition": {
                    arm: plans[arm].composition_record for arm in ARMS
                },
                "residual_evidence_by_arm": _canonical_residual_evidence(
                    canonical_residual_evidence
                ),
                "baseline_conditioning_activation": activation,
                "policy_loss": {arm: metrics[arm][0] for arm in ARMS},
                "immediate_baseline_loss": {
                    arm: metrics[arm][1] for arm in ARMS
                },
                "successor_baseline_loss": {
                    arm: metrics[arm][2] for arm in ARMS
                },
                "plans_materialized_before_either_optimizer": True,
                "branch_update_order": list(ARMS),
            }
        )
    steps_after = {
        arm: min(
            _optimizer_step_value(optimizers[arm], parameter)
            for parameter in models[arm].actor_credit_parameters()
        )
        for arm in ARMS
    }
    record: dict[str, object] = {
        "algorithm_id": ALGORITHM_ID,
        "accepted_g40_source_commit": ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g44_formal_source_commit": ACCEPTED_G44_FORMAL_SOURCE_COMMIT,
        "accepted_g44_aligned_source_commit": ACCEPTED_G44_ALIGNED_SOURCE_COMMIT,
        "accepted_g44_alignment_stage_commit": ACCEPTED_G44_ALIGNMENT_STAGE_COMMIT,
        "accepted_g40_anchor_replicate": models[
            BASELINE_READ_ARM
        ].accepted_g40_anchor_authority.replicate,
        "branch_boundary": boundary,
        "update_index": update_index,
        "arms": list(ARMS),
        "branch_update_order": list(ARMS),
        "paired_collection_before_update": True,
        "normalization_rows": NORMALIZATION_ROWS,
        "normalization_unit": "one_team_residual_row_per_primitive_step",
        "active_count_weighting": False,
        "episode_exclusions": "none",
        "normalization_count": 1,
        "normalization_recomputed_between_passes": False,
        "baseline_predictions_frozen_across_both_passes": True,
        "actor_head_optimizer_steps_before": steps_before,
        "actor_head_optimizer_steps": steps_after,
        "actor_head_optimizer_step_delta": PPO_PASSES,
        "baseline_update_rule_equal": True,
        "baseline_optimizer_exposure_equal": (
            steps_after[BASELINE_READ_ARM]
            == steps_after[BASELINE_SHADOW_NO_READ_ARM]
        ),
        "first_paired_direct_treatment_audit": direct_audit,
        "order_swap_guard": swap_guard,
        "pass_records": pass_records,
        "torch_rng_unchanged": torch.equal(rng_before, torch.random.get_rng_state()),
        "real_transitions": len(ARMS) * MAX_CONFORMANCE_TRANSITIONS,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "passed": False,
    }
    record["passed"] = bool(
        all(steps_after[arm] == steps_before[arm] + PPO_PASSES for arm in ARMS)
        and record["torch_rng_unchanged"] is True
        and all(
            all(
                validate_registered_gradient_evidence(
                    pass_record["gradient_evidence"][arm]  # type: ignore[index]
                )
                for arm in ARMS
            )
            and validate_activation_record(
                pass_record["baseline_conditioning_activation"]  # type: ignore[index]
            )
            and all(
                validate_arm_credit_evidence(
                    pass_record["residual_evidence_by_arm"][arm], arm  # type: ignore[index]
                )
                for arm in ARMS
            )
            for pass_record in pass_records
        )
    )
    if not _update_evidence_valid(record):
        raise RuntimeError("G45 serialized update evidence failed validation")
    return record


# Names consumed by accepted isolated orchestration and readiness helpers.
optimize_norm_schedule_update = optimize_baseline_conditioning_update
optimize_channel_scale_update = optimize_baseline_conditioning_update


def _valid_composition(value: object, arm: str) -> bool:
    if (
        not isinstance(value, Mapping)
        or value.get("passed") is not True
        or value.get("literal_coefficient") != EQUAL_MEAN_COEFFICIENT
        or value.get("entropy_added_after_credit_gate") is not True
        or value.get("baseline_target_fitting_retained") is not True
    ):
        return False
    if arm == BASELINE_READ_ARM:
        return bool(
            value.get("mode") == "independent_scale_baseline_read"
            and value.get("residual_law_id") == READ_RESIDUAL_LAW
            and value.get("actual_residual_baseline_read_count") == 2
            and value.get("actual_direction_baseline_coordinate_read_count") == 2
        )
    return bool(
        value.get("mode")
        == "independent_scale_baseline_shadow_no_read_norm_matched"
        and value.get("residual_law_id") == NO_READ_RESIDUAL_LAW
        and value.get("actual_residual_baseline_read_count") == 0
        and value.get("actual_direction_baseline_coordinate_read_count") == 0
        and value.get("counterfactual_baseline_scalar_shadow") is True
        and value.get("counterfactual_shadow_output_type")
        == "one_detached_scalar_credit_norm"
        and value.get("counterfactual_vector_serialized") is False
        and value.get("counterfactual_vector_coordinate_use_outside_norm") == 0
        and value.get("counterfactual_gradient_assignment_count") == 0
        and value.get("counterfactual_optimizer_state_count") == 0
        and value.get("counterfactual_RNG_consumption") == 0
        and value.get("counterfactual_model_mutation_count") == 0
        and value.get("baseline_action_or_logprob_read_count") == 0
        and value.get("baseline_checkpoint_selection_read_count") == 0
        and value.get("baseline_evaluation_metric_read_count") == 0
        and "counterfactual_vector" not in value
        and float(value.get("assigned_norm_match_error", np.inf))
        <= float(value.get("assigned_norm_match_tolerance", -1.0))
    )


def _update_evidence_valid(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    replicate = value.get("accepted_g40_anchor_replicate")
    boundary = value.get("branch_boundary")
    if (
        value.get("algorithm_id") != ALGORITHM_ID
        or isinstance(replicate, bool)
        or not isinstance(replicate, int)
        or replicate not in ACCEPTED_G40_ANCHOR_REPLICATES
        or not isinstance(boundary, Mapping)
        or boundary.get("accepted_g40_anchor_authority")
        != g41.accepted_g40_anchor_identity(replicate)
        or value.get("branch_update_order") != list(ARMS)
        or value.get("normalization_rows") != NORMALIZATION_ROWS
        or value.get("normalization_count") != 1
        or value.get("normalization_recomputed_between_passes") is not False
        or value.get("baseline_predictions_frozen_across_both_passes") is not True
        or value.get("actor_head_optimizer_step_delta") != PPO_PASSES
        or value.get("K_search") != 0
        or value.get("hypothetical_trajectory_count") != 0
        or value.get("hypothetical_transitions") != 0
        or value.get("nested_rollout") is not False
        or value.get("replanning") is not False
        or value.get("torch_rng_unchanged") is not True
    ):
        return False
    records = value.get("pass_records")
    if not isinstance(records, list) or len(records) != PPO_PASSES:
        return False
    for index, record in enumerate(records):
        if (
            not isinstance(record, Mapping)
            or record.get("pass_index") != index
            or record.get("plans_materialized_before_either_optimizer") is not True
            or record.get("branch_update_order") != list(ARMS)
        ):
            return False
        gradients = record.get("gradient_evidence")
        compositions = record.get("composition")
        residuals = record.get("residual_evidence_by_arm")
        activation = record.get("baseline_conditioning_activation")
        if (
            not isinstance(gradients, Mapping)
            or tuple(gradients) != ARMS
            or any(
                not validate_registered_gradient_evidence(gradients.get(arm))
                for arm in ARMS
            )
            or not isinstance(compositions, Mapping)
            or tuple(compositions) != ARMS
            or any(
                not _valid_composition(compositions.get(arm), arm) for arm in ARMS
            )
            or not isinstance(residuals, Mapping)
            or tuple(residuals) != ARMS
            or any(
                not validate_arm_credit_evidence(residuals.get(arm), arm)
                for arm in ARMS
            )
            or not validate_activation_record(activation)
        ):
            return False
        read_row = residuals[BASELINE_READ_ARM]  # type: ignore[index]
        if (
            not isinstance(activation, Mapping)
            or activation.get("reference_immediate_baseline_output_digest")
            != read_row.get("immediate_baseline_output_digest")
            or activation.get("reference_successor_baseline_output_digest")
            != read_row.get("successor_baseline_output_digest")
        ):
            return False
    if value.get("update_index") == 0:
        direct = value.get("first_paired_direct_treatment_audit")
        swap = value.get("order_swap_guard")
        if (
            not isinstance(direct, Mapping)
            or direct.get("passed") is not True
            or not isinstance(swap, Mapping)
            or swap.get("passed") is not True
            or swap.get("diagnostic_optimizer_steps") != 0
        ):
            return False
    return True


def validate_baseline_gradient_groups_by_arm(value: object) -> bool:
    return bool(
        isinstance(value, Mapping)
        and set(value) == set(ARMS)
        and all(
            validate_baseline_gradient_group_evidence(value.get(arm)) for arm in ARMS
        )
    )


def _baseline_gradient_groups_from_pass(
    pass_record: Mapping[str, object],
) -> dict[str, object]:
    gradients = pass_record.get("gradient_evidence")
    if (
        not isinstance(gradients, Mapping)
        or set(gradients) != set(ARMS)
        or any(
            not validate_registered_gradient_evidence(gradients.get(arm))
            for arm in ARMS
        )
    ):
        raise ValueError("G45 pass gradient evidence invalid")
    groups = {
        arm: gradients[arm]["baseline_gradient_groups"]  # type: ignore[index]
        for arm in ARMS
    }
    if not validate_baseline_gradient_groups_by_arm(groups):
        raise ValueError("G45 per-arm baseline gradient evidence invalid")
    return json.loads(json.dumps(groups, sort_keys=True))


def build_conclusion_evidence(
    update_records: Sequence[Mapping[str, object]], *, formal: bool
) -> dict[str, object]:
    if not isinstance(formal, bool) or not update_records:
        raise ValueError("G45 conclusion evidence requires records and bool scope")
    rows_by_replicate: dict[int, list[dict[str, object]]] = {}
    records_valid = True
    for record in update_records:
        replicate = record.get("accepted_g40_anchor_replicate")
        if (
            isinstance(replicate, bool)
            or not isinstance(replicate, int)
            or replicate not in ACCEPTED_G40_ANCHOR_REPLICATES
            or not _update_evidence_valid(record)
        ):
            records_valid = False
            continue
        rows_by_replicate.setdefault(replicate, [])
        for pass_record in record["pass_records"]:  # type: ignore[index]
            activation = pass_record["baseline_conditioning_activation"]
            residuals = _canonical_residual_evidence(
                pass_record["residual_evidence_by_arm"]
            )
            baseline_gradient_groups = _baseline_gradient_groups_from_pass(
                pass_record
            )
            if not validate_activation_record(activation):
                records_valid = False
            rows_by_replicate[replicate].append(
                {
                    "residual_evidence_by_arm": residuals,
                    "baseline_gradient_groups_by_arm": baseline_gradient_groups,
                    "centered_immediate_baseline_RMS": float(
                        activation["centered_immediate_baseline_RMS"]
                    ),
                    "centered_successor_baseline_RMS": float(
                        activation["centered_successor_baseline_RMS"]
                    ),
                    "q_baseline": float(activation["q_baseline"]),
                    "reference_READ_credit_norm": float(
                        activation["reference_READ_credit_norm"]
                    ),
                    "reference_NO_READ_counterfactual_credit_norm": float(
                        activation[
                            "reference_NO_READ_counterfactual_credit_norm"
                        ]
                    ),
                    "reference_credit_dot_product": float(
                        activation["reference_credit_dot_product"]
                    ),
                    "q_direction": float(activation["q_direction"]),
                    "reference_immediate_baseline_output_digest": str(
                        activation[
                            "reference_immediate_baseline_output_digest"
                        ]
                    ),
                    "reference_successor_baseline_output_digest": str(
                        activation[
                            "reference_successor_baseline_output_digest"
                        ]
                    ),
                    "active": bool(activation["strict_activation_observed"]),
                }
            )
    required = (
        list(ACCEPTED_G40_ANCHOR_REPLICATES)
        if formal
        else sorted(rows_by_replicate)
    )
    replicate_rows = [
        {
            "replicate": replicate,
            "reconstructed_passes": rows_by_replicate.get(replicate, []),
            "strict_activation_observed": any(
                bool(row["active"])
                for row in rows_by_replicate.get(replicate, [])
            ),
        }
        for replicate in required
    ]
    scope_valid = (
        set(rows_by_replicate) == set(ACCEPTED_G40_ANCHOR_REPLICATES)
        if formal
        else len(rows_by_replicate) == 1
    )
    return {
        "formal": formal,
        "required_replicates": required,
        "activation_threshold": ACTIVATION_TOLERANCE,
        "activation_predicate": (
            "q_baseline>1e-6_and_q_direction>1e-6_and_both_credit_norms_positive"
        ),
        "evidence_source_arm": BASELINE_READ_ARM,
        "residual_evidence_arms": list(ARMS),
        "reference_no_read_counterfactual": True,
        "no_read_arm_evidence_read_count": 0,
        "reconstructed_from_all_update_records": True,
        "forged_pass_flag_sufficient": False,
        "records_valid": records_valid,
        "replicate_rows": replicate_rows,
        "passed": bool(
            records_valid
            and scope_valid
            and replicate_rows
            and all(row["strict_activation_observed"] for row in replicate_rows)
        ),
    }


def validate_conclusion_evidence(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    formal = value.get("formal")
    required = value.get("required_replicates")
    rows = value.get("replicate_rows")
    if (
        not isinstance(formal, bool)
        or not isinstance(required, list)
        or not isinstance(rows, list)
        or not rows
        or value.get("activation_threshold") != ACTIVATION_TOLERANCE
        or value.get("evidence_source_arm") != BASELINE_READ_ARM
        or value.get("residual_evidence_arms") != list(ARMS)
        or value.get("reference_no_read_counterfactual") is not True
        or value.get("no_read_arm_evidence_read_count") != 0
        or value.get("reconstructed_from_all_update_records") is not True
        or value.get("forged_pass_flag_sufficient") is not False
        or value.get("records_valid") is not True
    ):
        return False
    expected = list(ACCEPTED_G40_ANCHOR_REPLICATES) if formal else required
    if required != expected or (not formal and len(required) != 1):
        return False
    observed: list[int] = []
    for row in rows:
        if not isinstance(row, Mapping):
            return False
        replicate = row.get("replicate")
        passes = row.get("reconstructed_passes")
        if (
            isinstance(replicate, bool)
            or not isinstance(replicate, int)
            or replicate not in ACCEPTED_G40_ANCHOR_REPLICATES
            or not isinstance(passes, list)
            or not passes
        ):
            return False
        active = False
        for item in passes:
            if not isinstance(item, Mapping):
                return False
            residuals = item.get("residual_evidence_by_arm")
            baseline_gradient_groups = item.get(
                "baseline_gradient_groups_by_arm"
            )
            if (
                not isinstance(residuals, Mapping)
                or tuple(residuals) != ARMS
                or any(
                    not validate_arm_credit_evidence(residuals.get(arm), arm)
                    for arm in ARMS
                )
                or not validate_baseline_gradient_groups_by_arm(
                    baseline_gradient_groups
                )
            ):
                return False
            activation = {
                "centered_immediate_baseline_RMS": item.get(
                    "centered_immediate_baseline_RMS"
                ),
                "centered_successor_baseline_RMS": item.get(
                    "centered_successor_baseline_RMS"
                ),
                "q_baseline": item.get("q_baseline"),
                "reference_READ_credit_norm": item.get(
                    "reference_READ_credit_norm"
                ),
                "reference_NO_READ_counterfactual_credit_norm": item.get(
                    "reference_NO_READ_counterfactual_credit_norm"
                ),
                "reference_credit_dot_product": item.get(
                    "reference_credit_dot_product"
                ),
                "q_direction": item.get("q_direction"),
                "reference_immediate_baseline_output_digest": item.get(
                    "reference_immediate_baseline_output_digest"
                ),
                "reference_successor_baseline_output_digest": item.get(
                    "reference_successor_baseline_output_digest"
                ),
                "activation_threshold": ACTIVATION_TOLERANCE,
                "evidence_source_arm": BASELINE_READ_ARM,
                "reference_no_read_counterfactual": True,
                "no_read_arm_evidence_read_count": 0,
                "strict_activation_observed": item.get("active"),
                "passed": True,
            }
            if not validate_activation_record(activation):
                return False
            read_row = residuals[BASELINE_READ_ARM]
            if (
                activation["reference_immediate_baseline_output_digest"]
                != read_row.get("immediate_baseline_output_digest")
                or activation["reference_successor_baseline_output_digest"]
                != read_row.get("successor_baseline_output_digest")
            ):
                return False
            active |= bool(item.get("active"))
        if row.get("strict_activation_observed") is not active:
            return False
        observed.append(replicate)
    return bool(
        observed == required
        and value.get("passed") is True
        and all(row["strict_activation_observed"] for row in rows)
    )


def serialize_diagnostics(record: Mapping[str, object]) -> str:
    if not _update_evidence_valid(record):
        raise ValueError("G45 refuses to serialize invalid update evidence")
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def build_final_checkpoint(
    arm: str,
    model: g41.G41NoSlowProjection,
    final_update_record: Mapping[str, object],
    conclusion_evidence: Mapping[str, object],
    *,
    formal: bool,
) -> dict[str, object]:
    if arm not in ARMS:
        raise ValueError("G45 final checkpoint arm is not registered")
    if not _update_evidence_valid(final_update_record):
        raise ValueError("G45 final checkpoint update evidence invalid")
    if not validate_conclusion_evidence(conclusion_evidence):
        raise ValueError("G45 final checkpoint activation evidence invalid")
    if conclusion_evidence.get("formal") is not formal:
        raise ValueError("G45 final checkpoint scope mismatch")
    state = {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }
    no_read_certificate = (
        final_update_record["pass_records"][-1]["composition"][  # type: ignore[index]
            BASELINE_SHADOW_NO_READ_ARM
        ]
    )
    if not _valid_composition(
        no_read_certificate, BASELINE_SHADOW_NO_READ_ARM
    ):
        raise ValueError("G45 final checkpoint no-read certificate invalid")
    baseline_gradient_groups = _baseline_gradient_groups_from_pass(
        final_update_record["pass_records"][-1]  # type: ignore[index]
    )
    return {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "kind": "final_only",
        "arm": arm,
        "formal": formal,
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(
            model.accepted_g40_anchor_authority.replicate
        ),
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g44_formal_source_commit": ACCEPTED_G44_FORMAL_SOURCE_COMMIT,
        "residual_evidence_arms": list(ARMS),
        "actor_head_optimizer_steps": PPO_PASSES,
        "standalone_slow_present": False,
        "standalone_slow_critic_present": False,
        "db_vector_present": False,
        "db_norm_present": False,
        "db_shadow_present": False,
        "baseline_checkpoint_selection_read_count": 0,
        "baseline_evaluation_metric_read_count": 0,
        "baseline_gradient_groups_by_arm": baseline_gradient_groups,
        "no_read_certificate": dict(no_read_certificate),
        "model_state": state,
        "model_state_digest": g41._state_digest(state),
        "final_update_evidence": dict(final_update_record),
        "conclusion_evidence": dict(conclusion_evidence),
        "diagnostics": {
            "passed": True,
            "real_transitions": final_update_record["real_transitions"],
            "K_search": 0,
            "hypothetical_transitions": 0,
            "treatment_activation": dict(conclusion_evidence),
        },
    }
