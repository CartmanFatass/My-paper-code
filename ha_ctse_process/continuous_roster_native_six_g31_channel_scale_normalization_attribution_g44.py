"""Exact independent-channel versus pooled-channel G31 scale attribution."""

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
    continuous_roster_native_six_g31_db_norm_schedule_attribution_g43 as g43,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory


ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_"
    "ATTRIBUTION_G44"
)
SOURCE_ID = f"{ALGORITHM_ID}_P0"
ACCEPTED_G40_SOURCE_COMMIT = "97a8b237e0cec6c2713dd2a710d324040fa3dfc2"
ACCEPTED_G41_SOURCE_COMMIT = "a5f63c349228fc2bba7843647e0ae4c34361c1c9"
ACCEPTED_G42_REFERENCE_SOURCE_COMMIT = (
    "a6c3c2971ee74e76a453995c3a7c12627bb8f02c"
)
ACCEPTED_G42_ALIGNED_SOURCE_COMMIT = (
    "6b8ea82d8fdbc76c14a414ff2b042a126f945dfb"
)
ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT = (
    "309858dca06af66f13857f94773bcef37527d821"
)
ACCEPTED_G43_SOURCE_COMMIT = "bb42840ab1479abde7f3485006bfbbee981a73cf"
ACCEPTED_G43_ALIGNED_SOURCE_COMMIT = (
    "45e16f71d171228135b6444bee1678b157d79abe"
)
ACCEPTED_G43_ALIGNMENT_STAGE_COMMIT = (
    "889c0b4e3d68a8d74f811ae9ecfe7b5213abfa76"
)
INDEPENDENT_ARM = "NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE"
POOLED_ARM = "NATIVE6_G31_EQUAL_MEAN_POOLED_SCALE"
ARMS = (INDEPENDENT_ARM, POOLED_ARM)
# Compatibility names used only by the isolated G43 orchestration backend.
DBNORM_ARM = INDEPENDENT_ARM
MEAN_ARM = POOLED_ARM
ACCEPTED_G40_ANCHOR_REPLICATES = (0, 1, 2)
PPO_PASSES = 2
NUM_ENVS = 8
HORIZON = 48
MAX_CONFORMANCE_TRANSITIONS = NUM_ENVS * HORIZON
NORMALIZATION_ROWS = MAX_CONFORMANCE_TRANSITIONS
GRADIENT_LIVE_TOLERANCE = g40.GRADIENT_LIVE_TOLERANCE
SCALE_MATCH_ATOL = 1e-8
SCALE_MATCH_RTOL = 1e-6
ACTIVATION_TOLERANCE = 1e-6
EQUAL_MEAN_COEFFICIENT = 0.5


def _normalization_mask_digest() -> str:
    mask = np.ones((HORIZON, NUM_ENVS), dtype=np.uint8)
    digest = hashlib.sha256()
    digest.update(b"shape=48x8|dtype=uint8|")
    digest.update(mask.tobytes(order="C"))
    return digest.hexdigest()


NORMALIZATION_MASK_DIGEST = _normalization_mask_digest()


class G44GradientGateError(ValueError):
    """A frozen G44 gate failed before either arm optimizer step."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object]) -> None:
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics)
        super().__init__(f"G44 gradient gate failed before optimizer step: {reason}")

    def to_record(self) -> dict[str, object]:
        return {
            "passed": False,
            "stage": "before_either_arm_optimizer_step",
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
        }


@dataclass(frozen=True)
class ChannelNormalization:
    centered_immediate: torch.Tensor
    centered_successor: torch.Tensor
    independent_immediate: torch.Tensor
    independent_successor: torch.Tensor
    pooled_immediate: torch.Tensor
    pooled_successor: torch.Tensor
    immediate_mean: float
    successor_mean: float
    immediate_centered_sum_square: float
    successor_centered_sum_square: float
    immediate_scale: float
    successor_scale: float
    pooled_scale: float
    normalization_row_count: int
    normalization_mask_digest: str


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
        raise G44GradientGateError(error.reason, error.diagnostics) from error


def _global_norm(rows: Sequence[torch.Tensor]) -> float:
    return g43._global_norm(rows)


def _rows_bitwise_equal(
    left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]
) -> bool:
    return len(left) == len(right) and all(
        torch.equal(a, b) for a, b in zip(left, right)
    )


def _finite_tensor(name: str, value: torch.Tensor) -> None:
    if not bool(torch.isfinite(value).all()):
        raise G44GradientGateError(f"{name}_nonfinite", {})


def normalize_credit_channels(credit: g41.G41Credit) -> ChannelNormalization:
    """Center separately and apply the exact independent and pooled RMS rules."""

    immediate = credit.immediate_advantage.detach()
    successor = credit.successor_advantage.detach()
    if (
        immediate.shape != successor.shape
        or tuple(immediate.shape) != (HORIZON, NUM_ENVS)
    ):
        raise G44GradientGateError(
            "normalization_row_inventory_mismatch",
            {
                "immediate_shape": tuple(immediate.shape),
                "successor_shape": tuple(successor.shape),
                "expected_rows": NORMALIZATION_ROWS,
            },
        )
    _finite_tensor("immediate_residual", immediate)
    _finite_tensor("successor_residual", successor)
    work_i = immediate.to(torch.float64)
    work_s = successor.to(torch.float64)
    mean_i = work_i.mean()
    mean_s = work_s.mean()
    centered_i = work_i - mean_i
    centered_s = work_s - mean_s
    immediate_centered_sum_square = centered_i.square().sum()
    successor_centered_sum_square = centered_s.square().sum()
    scale_i = torch.sqrt(
        immediate_centered_sum_square / float(NORMALIZATION_ROWS)
    )
    scale_s = torch.sqrt(
        successor_centered_sum_square / float(NORMALIZATION_ROWS)
    )
    pooled = torch.sqrt(
        (immediate_centered_sum_square + successor_centered_sum_square)
        / float(2 * NORMALIZATION_ROWS)
    )
    for name, scalar in (
        ("immediate_mean", mean_i),
        ("successor_mean", mean_s),
        ("immediate_scale", scale_i),
        ("successor_scale", scale_s),
        ("pooled_scale", pooled),
    ):
        _finite_tensor(name, scalar)

    def divide_or_zero(centered: torch.Tensor, scale: torch.Tensor) -> torch.Tensor:
        return torch.zeros_like(centered) if float(scale) == 0.0 else centered / scale

    independent_i = divide_or_zero(centered_i, scale_i)
    independent_s = divide_or_zero(centered_s, scale_s)
    pooled_i = divide_or_zero(centered_i, pooled)
    pooled_s = divide_or_zero(centered_s, pooled)
    for name, row in (
        ("independent_immediate", independent_i),
        ("independent_successor", independent_s),
        ("pooled_immediate", pooled_i),
        ("pooled_successor", pooled_s),
    ):
        _finite_tensor(name, row)
    return ChannelNormalization(
        centered_immediate=centered_i.to(immediate.dtype),
        centered_successor=centered_s.to(successor.dtype),
        independent_immediate=independent_i.to(immediate.dtype),
        independent_successor=independent_s.to(successor.dtype),
        pooled_immediate=pooled_i.to(immediate.dtype),
        pooled_successor=pooled_s.to(successor.dtype),
        immediate_mean=float(mean_i),
        successor_mean=float(mean_s),
        immediate_centered_sum_square=float(immediate_centered_sum_square),
        successor_centered_sum_square=float(successor_centered_sum_square),
        immediate_scale=float(scale_i),
        successor_scale=float(scale_s),
        pooled_scale=float(pooled),
        normalization_row_count=NORMALIZATION_ROWS,
        normalization_mask_digest=NORMALIZATION_MASK_DIGEST,
    )


def _equal_mean(
    immediate: Sequence[torch.Tensor],
    successor: Sequence[torch.Tensor],
    parameters: Sequence[nn.Parameter],
) -> tuple[torch.Tensor, ...]:
    left = _gradient_rows(immediate, parameters)
    right = _gradient_rows(successor, parameters)
    result = tuple(
        (
            EQUAL_MEAN_COEFFICIENT
            * (a.to(torch.float64) + b.to(torch.float64))
        ).to(parameter.dtype)
        for a, b, parameter in zip(left, right, parameters)
    )
    if any(not bool(torch.isfinite(row).all()) for row in result):
        raise G44GradientGateError("equal_mean_nonfinite", {})
    return result


def _add_entropy(
    credit: Sequence[torch.Tensor], entropy: Sequence[torch.Tensor]
) -> tuple[torch.Tensor, ...]:
    if len(credit) != len(entropy):
        raise G44GradientGateError("entropy_gradient_inventory_mismatch", {})
    rows = tuple(
        (a.to(torch.float64) + b.to(torch.float64)).to(a.dtype)
        for a, b in zip(credit, entropy)
    )
    if any(not bool(torch.isfinite(row).all()) for row in rows):
        raise G44GradientGateError("credit_plus_entropy_nonfinite", {})
    return rows


def _scale_to_counterfactual_norm(
    raw: Sequence[torch.Tensor],
    parameters: Sequence[nn.Parameter],
    *,
    counterfactual_norm: float,
) -> tuple[tuple[torch.Tensor, ...], dict[str, object]]:
    rows = _gradient_rows(raw, parameters)
    raw_norm = _global_norm(rows)
    values = (raw_norm, counterfactual_norm)
    if any(not np.isfinite(value) or value < 0.0 for value in values):
        raise G44GradientGateError(
            "pooled_norm_nonfinite_or_negative",
            {"raw_norm": raw_norm, "counterfactual_norm": counterfactual_norm},
        )
    if counterfactual_norm == 0.0:
        assigned = tuple(torch.zeros_like(parameter) for parameter in parameters)
        scale = 0.0
    elif raw_norm == 0.0:
        raise G44GradientGateError(
            "positive_counterfactual_norm_with_zero_pooled_direction",
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
        raise G44GradientGateError(
            "pooled_counterfactual_norm_match_failed",
            {
                "assigned_norm": assigned_norm,
                "counterfactual_norm": counterfactual_norm,
                "error": error,
                "tolerance": tolerance,
            },
        )
    return assigned, {
        "raw_credit_norm": raw_norm,
        "counterfactual_independent_credit_norm": counterfactual_norm,
        "assigned_credit_norm": assigned_norm,
        "scale": scale,
        "assigned_norm_match_error": error,
        "assigned_norm_match_tolerance": tolerance,
        "unscaled_raw_norm_compared_to_counterfactual": False,
        "counterfactual_scale_shadow": True,
        "shadow_output_type": "one_detached_scalar_norm",
        "shadow_vector_serialized": False,
        "shadow_vector_coordinate_use_outside_norm": 0,
        "shadow_gradient_assignment_count": 0,
        "shadow_optimizer_state_count": 0,
        "shadow_RNG_consumption": 0,
        "shadow_model_mutation_count": 0,
        "shadow_checkpoint_selection_reads": 0,
        "shadow_evaluation_reads": 0,
        "pooled_arm_evidence_read_count": 0,
        "actor_credit_gradients_exact_zero": all(
            bool(torch.count_nonzero(row) == 0) for row in assigned
        ),
        "passed": True,
    }


def _unit_direction_distance(
    left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]
) -> float:
    left_norm = _global_norm(left)
    right_norm = _global_norm(right)
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    total = sum(
        (
            a.detach().to(torch.float64) / left_norm
            - b.detach().to(torch.float64) / right_norm
        ).square().sum()
        for a, b in zip(left, right)
    )
    value = float(torch.sqrt(total))
    if not np.isfinite(value) or value < 0.0:
        raise G44GradientGateError("direction_distance_nonfinite", {})
    return value


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
    values = (left_norm, right_norm, dot, distance)
    if any(not np.isfinite(value) for value in values):
        raise G44GradientGateError("direction_scalar_evidence_nonfinite", {})
    return left_norm, right_norm, dot, distance


def _normalization_statistics(
    normalization: ChannelNormalization,
) -> dict[str, object]:
    return {
        "immediate_mean": normalization.immediate_mean,
        "successor_mean": normalization.successor_mean,
        "immediate_centered_sum_square": (
            normalization.immediate_centered_sum_square
        ),
        "successor_centered_sum_square": (
            normalization.successor_centered_sum_square
        ),
        "immediate_scale": normalization.immediate_scale,
        "successor_scale": normalization.successor_scale,
        "pooled_scale": normalization.pooled_scale,
        "normalization_row_count": normalization.normalization_row_count,
        "normalization_mask_digest": normalization.normalization_mask_digest,
    }


NORMALIZATION_STATISTIC_FIELDS = (
    "immediate_mean",
    "successor_mean",
    "immediate_centered_sum_square",
    "successor_centered_sum_square",
    "immediate_scale",
    "successor_scale",
    "pooled_scale",
    "normalization_row_count",
    "normalization_mask_digest",
)


def validate_normalization_statistics(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    numeric_names = NORMALIZATION_STATISTIC_FIELDS[:-2]
    if any(
        isinstance(value.get(name), bool)
        or not isinstance(value.get(name), (int, float))
        or not np.isfinite(float(value[name]))
        or (
            name not in ("immediate_mean", "successor_mean")
            and float(value[name]) < 0.0
        )
        for name in numeric_names
    ):
        return False
    row_count = value.get("normalization_row_count")
    if (
        isinstance(row_count, bool)
        or row_count != NORMALIZATION_ROWS
        or value.get("normalization_mask_digest") != NORMALIZATION_MASK_DIGEST
    ):
        return False
    immediate_sum = float(value["immediate_centered_sum_square"])
    successor_sum = float(value["successor_centered_sum_square"])
    return bool(
        float(value["immediate_scale"])
        == float(np.sqrt(immediate_sum / float(NORMALIZATION_ROWS)))
        and float(value["successor_scale"])
        == float(np.sqrt(successor_sum / float(NORMALIZATION_ROWS)))
        and float(value["pooled_scale"])
        == float(
            np.sqrt(
                (immediate_sum + successor_sum)
                / float(2 * NORMALIZATION_ROWS)
            )
        )
    )


def _normalization_statistics_match(left: object, right: object) -> bool:
    return bool(
        validate_normalization_statistics(left)
        and validate_normalization_statistics(right)
        and isinstance(left, Mapping)
        and isinstance(right, Mapping)
        and all(left.get(name) == right.get(name) for name in NORMALIZATION_STATISTIC_FIELDS)
    )


def _normalization_evidence_by_arm(
    normalizations: Mapping[str, ChannelNormalization],
) -> dict[str, object]:
    if tuple(normalizations) != ARMS:
        raise G44GradientGateError(
            "normalization_arm_inventory_mismatch",
            {"observed_arms": list(normalizations)},
        )
    evidence: dict[str, object] = {
        arm: {"arm": arm, **_normalization_statistics(normalizations[arm])}
        for arm in ARMS
    }
    if not validate_normalization_by_arm(evidence):
        raise G44GradientGateError("normalization_by_arm_invalid", evidence)
    return evidence


def validate_normalization_by_arm(value: object) -> bool:
    if not isinstance(value, Mapping) or tuple(value) != ARMS:
        return False
    expected_keys = {"arm", *NORMALIZATION_STATISTIC_FIELDS}
    return all(
        isinstance(value.get(arm), Mapping)
        and set(value[arm]) == expected_keys  # type: ignore[arg-type,index]
        and value[arm].get("arm") == arm  # type: ignore[index]
        and validate_normalization_statistics(value[arm])
        for arm in ARMS
    )


def _canonical_normalization_by_arm(value: Mapping[str, object]) -> dict[str, object]:
    if not validate_normalization_by_arm(value):
        raise ValueError("G44 per-arm normalization evidence invalid")
    return {
        arm: {
            "arm": arm,
            **{
                name: value[arm][name]  # type: ignore[index]
                for name in NORMALIZATION_STATISTIC_FIELDS
            },
        }
        for arm in ARMS
    }


def _schedule_record(
    normalization: ChannelNormalization,
    independent_credit: Sequence[torch.Tensor],
    pooled_counterfactual_credit: Sequence[torch.Tensor],
) -> dict[str, object]:
    independent_norm, pooled_norm, direction_dot, q_direction = (
        _direction_scalar_evidence(
            independent_credit, pooled_counterfactual_credit
        )
    )
    maximum = max(normalization.immediate_scale, normalization.successor_scale)
    q_scale = (
        abs(normalization.immediate_scale - normalization.successor_scale) / maximum
        if maximum > 0.0
        else 0.0
    )
    values = (
        normalization.immediate_scale,
        normalization.successor_scale,
        normalization.pooled_scale,
        q_scale,
        independent_norm,
        pooled_norm,
        q_direction,
    )
    if any(not np.isfinite(value) or value < 0.0 for value in values):
        raise G44GradientGateError("activation_scalar_nonfinite_or_negative", {})
    active = bool(
        q_scale > ACTIVATION_TOLERANCE
        and q_direction > ACTIVATION_TOLERANCE
        and independent_norm > 0.0
        and pooled_norm > 0.0
    )
    record = {
        **_normalization_statistics(normalization),
        "s_I": normalization.immediate_scale,
        "s_S": normalization.successor_scale,
        "s_P": normalization.pooled_scale,
        "q_scale": q_scale,
        "independent_credit_norm": independent_norm,
        "pooled_counterfactual_credit_norm": pooled_norm,
        "reference_credit_dot_product": direction_dot,
        "q_direction": q_direction,
        "activation_threshold": ACTIVATION_TOLERANCE,
        "evidence_source_arm": INDEPENDENT_ARM,
        "reference_pooled_counterfactual": True,
        "pooled_arm_evidence_read_count": 0,
        "strict_activation_observed": active,
        "passed": True,
    }
    if not validate_schedule_record(record):
        raise G44GradientGateError("schedule_record_invalid", record)
    return record


def validate_schedule_record(value: object) -> bool:
    if (
        not isinstance(value, Mapping)
        or value.get("passed") is not True
        or not validate_normalization_statistics(value)
    ):
        return False
    names = (
        "s_I",
        "s_S",
        "s_P",
        "q_scale",
        "independent_credit_norm",
        "pooled_counterfactual_credit_norm",
        "reference_credit_dot_product",
        "q_direction",
    )
    if any(
        isinstance(value.get(name), bool)
        or not isinstance(value.get(name), (int, float))
        or not np.isfinite(float(value[name]))
        or (
            name != "reference_credit_dot_product"
            and float(value[name]) < 0.0
        )
        for name in names
    ):
        return False
    maximum = max(float(value["s_I"]), float(value["s_S"]))
    q_scale = (
        abs(float(value["s_I"]) - float(value["s_S"])) / maximum
        if maximum > 0.0
        else 0.0
    )
    active = bool(
        q_scale > ACTIVATION_TOLERANCE
        and float(value["q_direction"]) > ACTIVATION_TOLERANCE
        and float(value["independent_credit_norm"]) > 0.0
        and float(value["pooled_counterfactual_credit_norm"]) > 0.0
    )
    independent_norm = float(value["independent_credit_norm"])
    pooled_norm = float(value["pooled_counterfactual_credit_norm"])
    if independent_norm > 0.0 and pooled_norm > 0.0:
        cosine = max(
            -1.0,
            min(
                1.0,
                float(value["reference_credit_dot_product"])
                / (independent_norm * pooled_norm),
            ),
        )
        expected_direction = float(np.sqrt(max(0.0, 2.0 - 2.0 * cosine)))
    else:
        expected_direction = 0.0
    return bool(
        float(value["q_scale"]) == q_scale
        and float(value["q_direction"]) == expected_direction
        and float(value["s_I"]) == float(value["immediate_scale"])
        and float(value["s_S"]) == float(value["successor_scale"])
        and float(value["s_P"]) == float(value["pooled_scale"])
        and value.get("activation_threshold") == ACTIVATION_TOLERANCE
        and value.get("evidence_source_arm") == INDEPENDENT_ARM
        and value.get("reference_pooled_counterfactual") is True
        and value.get("pooled_arm_evidence_read_count") == 0
        and value.get("strict_activation_observed") is active
    )


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
    immediate_baseline_loss = F.mse_loss(
        replay.immediate_baselines, trajectory.rewards.detach()
    )
    successor_baseline_loss = F.mse_loss(
        replay.successor_baselines, credit.successor_targets
    )
    immediate_baseline = _gradient_rows(
        torch.autograd.grad(
            immediate_baseline_loss,
            baseline_parameters,
            retain_graph=True,
            allow_unused=True,
        ),
        baseline_parameters,
    )
    successor_baseline = _gradient_rows(
        torch.autograd.grad(
            successor_baseline_loss,
            baseline_parameters,
            retain_graph=True,
            allow_unused=True,
        ),
        baseline_parameters,
    )
    try:
        evidence = g43.registered_gradient_evidence(
            model,
            immediate_actor,
            successor_actor,
            immediate_baseline,
            successor_baseline,
        )
    except g43.G43GradientGateError as error:
        raise G44GradientGateError(error.reason, error.diagnostics) from error
    if not g43.validate_registered_gradient_evidence(evidence):
        raise G44GradientGateError("registered_gradient_evidence_failed", evidence)
    return _GradientProbe(
        policy=EQUAL_MEAN_COEFFICIENT * (immediate + successor)
        + entropy_objective,
        immediate_baseline_loss=immediate_baseline_loss,
        successor_baseline_loss=successor_baseline_loss,
        immediate_credit_gradients=immediate_actor,
        successor_credit_gradients=successor_actor,
        entropy_gradients=entropy,
        immediate_baseline_gradients=immediate_baseline,
        successor_baseline_gradients=successor_baseline,
        gradient_evidence=evidence,
    )


def project_g44_arms(
    anchor: g40.G40NativeSixPolicy, *, accepted_anchor_replicate: int
) -> dict[str, g41.G41NoSlowProjection]:
    if accepted_anchor_replicate not in ACCEPTED_G40_ANCHOR_REPLICATES:
        raise ValueError("G44 requires accepted G40 anchor replicate 0, 1, or 2")
    rng_before = torch.random.get_rng_state().clone()
    g43_models = g43.project_g43_arms(
        anchor, accepted_anchor_replicate=accepted_anchor_replicate
    )
    models = {
        INDEPENDENT_ARM: g43_models[g43.DBNORM_ARM],
        POOLED_ARM: g43_models[g43.MEAN_ARM],
    }
    if g40.state_bytes(models[INDEPENDENT_ARM]) != g40.state_bytes(
        models[POOLED_ARM]
    ):
        raise RuntimeError("G44 branch states differ before treatment")
    if g40.shared_tensor_storage_count((anchor, *models.values())) != 0:
        raise RuntimeError("G44 projection shares retained storage")
    if any(hasattr(model, "slow_critic") for model in models.values()):
        raise RuntimeError("G44 reintroduced the standalone slow critic")
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise RuntimeError("G44 projection advanced model RNG")
    return models


# Name consumed by the isolated G43 orchestration backend.
project_g43_arms = project_g44_arms


def _optimizer_owns_actor_head(
    optimizer: torch.optim.Optimizer, model: g41.G41NoSlowProjection
) -> bool:
    return g43._optimizer_owns_actor_head(optimizer, model)


def _optimizer_step_value(
    optimizer: torch.optim.Optimizer, parameter: nn.Parameter
) -> float:
    return g43._optimizer_step_value(optimizer, parameter)


def branch_boundary_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS:
        return {"passed": False, "inventory_valid": False}
    remapped_models = {
        g43.DBNORM_ARM: models[INDEPENDENT_ARM],
        g43.MEAN_ARM: models[POOLED_ARM],
    }
    remapped_optimizers = {
        g43.DBNORM_ARM: optimizers[INDEPENDENT_ARM],
        g43.MEAN_ARM: optimizers[POOLED_ARM],
    }
    base = g43.branch_boundary_audit(remapped_models, remapped_optimizers)
    provenance_valid = bool(
        ACCEPTED_G40_SOURCE_COMMIT == g43.ACCEPTED_G40_SOURCE_COMMIT
        and ACCEPTED_G41_SOURCE_COMMIT == g43.ACCEPTED_G41_SOURCE_COMMIT
        and ACCEPTED_G42_REFERENCE_SOURCE_COMMIT
        == g43.ACCEPTED_G42_REFERENCE_SOURCE_COMMIT
        and ACCEPTED_G42_ALIGNED_SOURCE_COMMIT
        == g43.ACCEPTED_G42_ALIGNED_SOURCE_COMMIT
        and ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT
        == g43.ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT
        and len(ACCEPTED_G43_SOURCE_COMMIT) == 40
        and len(ACCEPTED_G43_ALIGNED_SOURCE_COMMIT) == 40
        and len(ACCEPTED_G43_ALIGNMENT_STAGE_COMMIT) == 40
    )
    no_db_state = all(
        all("db" not in name.lower() for name, _ in model.named_parameters())
        for model in models.values()
    )
    return {
        **base,
        "arms": list(ARMS),
        "accepted_g40_source_commit": ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g42_reference_source_commit": ACCEPTED_G42_REFERENCE_SOURCE_COMMIT,
        "accepted_g42_aligned_source_commit": ACCEPTED_G42_ALIGNED_SOURCE_COMMIT,
        "accepted_g42_alignment_stage_commit": ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT,
        "accepted_g43_source_commit": ACCEPTED_G43_SOURCE_COMMIT,
        "accepted_g43_aligned_source_commit": ACCEPTED_G43_ALIGNED_SOURCE_COMMIT,
        "accepted_g43_alignment_stage_commit": ACCEPTED_G43_ALIGNMENT_STAGE_COMMIT,
        "db_vector_present": False,
        "db_norm_present": False,
        "db_shadow_present": False,
        "no_db_state": no_db_state,
        "provenance_valid": provenance_valid,
        "passed": bool(base.get("passed") is True and provenance_valid and no_db_state),
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
    passed = bool(
        inventory
        and authority
        and steps
        and all(model.phase == "credit_branch" for model in models.values())
        and all(not hasattr(model, "slow_critic") for model in models.values())
    )
    return {
        "inventory_valid": inventory,
        "continuation": True,
        "update_index": update_index,
        "accepted_g40_anchor_authority": (
            g41.accepted_g40_anchor_identity(
                models[INDEPENDENT_ARM].accepted_g40_anchor_authority.replicate
            )
            if authority
            else None
        ),
        "authority_valid": authority,
        "optimizer_expected_step_before": expected,
        "optimizer_step_state_valid": steps,
        "passed": passed,
    }


def _direct_treatment_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    independent_probes: Mapping[str, _GradientProbe],
    normalizations: Mapping[str, ChannelNormalization],
) -> dict[str, object]:
    left = models[INDEPENDENT_ARM]
    right = models[POOLED_ARM]
    trajectory = g40.branch_trajectory_match(
        trajectories[INDEPENDENT_ARM], trajectories[POOLED_ARM]
    )
    channels_equal = {
        name: _rows_bitwise_equal(
            getattr(independent_probes[INDEPENDENT_ARM], name),
            getattr(independent_probes[POOLED_ARM], name),
        )
        for name in (
            "immediate_credit_gradients",
            "successor_credit_gradients",
            "entropy_gradients",
            "immediate_baseline_gradients",
            "successor_baseline_gradients",
        )
    }
    normalization_equal = all(
        torch.equal(
            getattr(normalizations[INDEPENDENT_ARM], name),
            getattr(normalizations[POOLED_ARM], name),
        )
        for name in (
            "centered_immediate",
            "centered_successor",
            "independent_immediate",
            "independent_successor",
            "pooled_immediate",
            "pooled_successor",
        )
    )
    passed = bool(
        trajectory["passed"] is True
        and g40.state_bytes(left.policy) == g40.state_bytes(right.policy)
        and torch.equal(left.log_std, right.log_std)
        and g40.state_bytes(left.credit_baselines)
        == g40.state_bytes(right.credit_baselines)
        and all(channels_equal.values())
        and normalization_equal
        and all(optimizer.state == {} for optimizer in optimizers.values())
    )
    return {
        "trajectory_bitwise_equal": trajectory["passed"],
        "actor_bytes_equal": g40.state_bytes(left.policy)
        == g40.state_bytes(right.policy),
        "log_std_bitwise_equal": torch.equal(left.log_std, right.log_std),
        "shared_baseline_bytes_equal": g40.state_bytes(left.credit_baselines)
        == g40.state_bytes(right.credit_baselines),
        "pre_treatment_channel_gradients_bitwise_equal": channels_equal,
        "normalization_inputs_bitwise_equal": normalization_equal,
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
    inventory = tuple(models) == ARMS and tuple(optimizers) == ARMS and tuple(plans) == ARMS
    model_storage = bool(
        inventory
        and g40.shared_tensor_storage_count(tuple(models.values())) == 0
        and id(optimizers[INDEPENDENT_ARM].state) != id(optimizers[POOLED_ARM].state)
    )
    gradient_storage = bool(
        inventory
        and not {
            row.untyped_storage().data_ptr()
            for row in plans[INDEPENDENT_ARM].gradients
        }.intersection(
            row.untyped_storage().data_ptr()
            for row in plans[POOLED_ARM].gradients
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
        raise ValueError("G44 optimizer arm/type mismatch")
    if not _optimizer_owns_actor_head(optimizer, model):
        raise ValueError("G44 optimizer parameter inventory mismatch")
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
        raise G44GradientGateError("stale_or_missing_gradient", {"arm": arm})
    g40._optimizer_step(optimizer, all_parameters)
    after = tuple(
        _optimizer_step_value(optimizer, parameter) for parameter in all_parameters
    )
    if any(value != prior + 1.0 for prior, value in zip(before, after)):
        raise RuntimeError("G44 Adam exposure did not advance exactly once")
    return (
        float(plan.policy.detach()),
        float(plan.immediate_baseline_loss.detach()),
        float(plan.successor_baseline_loss.detach()),
    )


def _prepare_passes(
    models: Mapping[str, g41.G41NoSlowProjection],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    credits: Mapping[str, g41.G41Credit],
    normalizations: Mapping[str, ChannelNormalization],
) -> tuple[
    dict[str, _PassPlan],
    dict[str, _GradientProbe],
    dict[str, _GradientProbe],
    dict[str, object],
]:
    replays = {
        arm: g41.retained_replay(models[arm], trajectories[arm]) for arm in ARMS
    }
    independent = {
        arm: _gradient_probe(
            models[arm],
            replays[arm],
            trajectories[arm],
            credits[arm],
            (
                normalizations[arm].independent_immediate,
                normalizations[arm].independent_successor,
            ),
        )
        for arm in ARMS
    }
    pooled = {
        arm: _gradient_probe(
            models[arm],
            replays[arm],
            trajectories[arm],
            credits[arm],
            (
                normalizations[arm].pooled_immediate,
                normalizations[arm].pooled_successor,
            ),
        )
        for arm in ARMS
    }
    common_terms_equal = {
        arm: bool(
            _rows_bitwise_equal(
                independent[arm].entropy_gradients,
                pooled[arm].entropy_gradients,
            )
            and torch.equal(
                independent[arm].immediate_baseline_loss,
                pooled[arm].immediate_baseline_loss,
            )
            and torch.equal(
                independent[arm].successor_baseline_loss,
                pooled[arm].successor_baseline_loss,
            )
            and _rows_bitwise_equal(
                independent[arm].immediate_baseline_gradients,
                pooled[arm].immediate_baseline_gradients,
            )
            and _rows_bitwise_equal(
                independent[arm].successor_baseline_gradients,
                pooled[arm].successor_baseline_gradients,
            )
        )
        for arm in ARMS
    }
    if not all(common_terms_equal.values()):
        raise G44GradientGateError(
            "normalization_changed_entropy_or_baseline_terms",
            {"arm_equality": common_terms_equal},
        )
    independent_credit = _equal_mean(
        independent[INDEPENDENT_ARM].immediate_credit_gradients,
        independent[INDEPENDENT_ARM].successor_credit_gradients,
        models[INDEPENDENT_ARM].full_actor_parameters(),
    )
    reference_pooled_counterfactual = _equal_mean(
        pooled[INDEPENDENT_ARM].immediate_credit_gradients,
        pooled[INDEPENDENT_ARM].successor_credit_gradients,
        models[INDEPENDENT_ARM].full_actor_parameters(),
    )
    pooled_raw = _equal_mean(
        pooled[POOLED_ARM].immediate_credit_gradients,
        pooled[POOLED_ARM].successor_credit_gradients,
        models[POOLED_ARM].full_actor_parameters(),
    )
    pooled_counterfactual_independent = _equal_mean(
        independent[POOLED_ARM].immediate_credit_gradients,
        independent[POOLED_ARM].successor_credit_gradients,
        models[POOLED_ARM].full_actor_parameters(),
    )
    pooled_assigned, shadow = _scale_to_counterfactual_norm(
        pooled_raw,
        models[POOLED_ARM].full_actor_parameters(),
        counterfactual_norm=_global_norm(pooled_counterfactual_independent),
    )
    common_entropy = independent[INDEPENDENT_ARM].entropy_gradients
    independent_assigned = _add_entropy(independent_credit, common_entropy)
    pooled_with_entropy = _add_entropy(pooled_assigned, common_entropy)
    schedule = _schedule_record(
        normalizations[INDEPENDENT_ARM],
        independent_credit,
        reference_pooled_counterfactual,
    )
    plans = {
        INDEPENDENT_ARM: _PassPlan(
            policy=independent[INDEPENDENT_ARM].policy,
            immediate_baseline_loss=independent[
                INDEPENDENT_ARM
            ].immediate_baseline_loss,
            successor_baseline_loss=independent[
                INDEPENDENT_ARM
            ].successor_baseline_loss,
            gradients=independent_assigned,
            gradient_evidence=independent[INDEPENDENT_ARM].gradient_evidence,
            composition_record={
                "mode": "equal_mean_independent_channel_scale",
                "literal_coefficient": EQUAL_MEAN_COEFFICIENT,
                "credit_norm_before_entropy": _global_norm(independent_credit),
                "entropy_gradient_norm": _global_norm(
                    common_entropy
                ),
                "assigned_actor_gradient_norm": _global_norm(independent_assigned),
                "entropy_added_after_credit_gate": True,
                "entropy_gradient_source_arm": INDEPENDENT_ARM,
                "entropy_gradient_bitwise_identical_across_arms": True,
                "entropy_and_baseline_terms_bitwise_independent_of_scale_path": True,
                "passed": True,
            },
        ),
        POOLED_ARM: _PassPlan(
            policy=pooled[POOLED_ARM].policy,
            immediate_baseline_loss=pooled[POOLED_ARM].immediate_baseline_loss,
            successor_baseline_loss=pooled[POOLED_ARM].successor_baseline_loss,
            gradients=pooled_with_entropy,
            gradient_evidence=pooled[POOLED_ARM].gradient_evidence,
            composition_record={
                "mode": "equal_mean_pooled_channel_scale_norm_matched",
                "literal_coefficient": EQUAL_MEAN_COEFFICIENT,
                **shadow,
                "entropy_gradient_norm": _global_norm(
                    common_entropy
                ),
                "assigned_actor_gradient_norm": _global_norm(pooled_with_entropy),
                "entropy_added_after_credit_gate": True,
                "entropy_gradient_source_arm": INDEPENDENT_ARM,
                "entropy_gradient_bitwise_identical_across_arms": True,
                "entropy_and_baseline_terms_bitwise_independent_of_scale_path": True,
            },
        ),
    }
    return plans, independent, pooled, schedule


def optimize_channel_scale_update(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory] | AnchoredRosterTrajectory,
    *,
    update_index: int = 0,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, object]:
    if int(ppo_passes) != PPO_PASSES:
        raise ValueError("G44 requires exactly two PPO passes")
    if isinstance(update_index, bool) or not isinstance(update_index, int) or update_index < 0:
        raise ValueError("G44 update index must be a nonnegative integer")
    trajectory_map = (
        {arm: trajectories for arm in ARMS}
        if isinstance(trajectories, AnchoredRosterTrajectory)
        else dict(trajectories)
    )
    if tuple(trajectory_map) != ARMS or any(
        trajectory.rewards.numel() != MAX_CONFORMANCE_TRANSITIONS
        for trajectory in trajectory_map.values()
    ):
        raise ValueError("G44 update requires paired 8x48 real trajectories")
    boundary = _continuation_audit(models, optimizers, update_index=update_index)
    if boundary.get("passed") is not True:
        raise ValueError("G44 branch boundary failed before optimizer step")
    credits = {
        arm: g41.compute_g31_credit_without_slow(
            rewards=trajectory.rewards,
            immediate_baselines=trajectory.old_immediate_baselines,
            successor_baselines=trajectory.old_successor_baselines,
            terminals=g40.terminal_mask(trajectory),
        )
        for arm, trajectory in trajectory_map.items()
    }
    normalizations = {arm: normalize_credit_channels(credit) for arm, credit in credits.items()}
    normalization_by_arm = _normalization_evidence_by_arm(normalizations)
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
        plans, independent, _, schedule = _prepare_passes(
            models, trajectory_map, credits, normalizations
        )
        if update_index == 0 and pass_index == 0:
            direct_audit = _direct_treatment_audit(
                models,
                optimizers,
                trajectory_map,
                independent,
                normalizations,
            )
            if direct_audit.get("passed") is not True:
                raise G44GradientGateError(
                    "first_paired_direct_treatment_mismatch", direct_audit
                )
            swap_guard = order_swap_guard(models, optimizers, plans)
            if swap_guard.get("passed") is not True:
                raise G44GradientGateError("order_swap_guard_failed", swap_guard)
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
                "normalization_by_arm": _canonical_normalization_by_arm(
                    normalization_by_arm
                ),
                "channel_scale_schedule": schedule,
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
        "accepted_g42_reference_source_commit": ACCEPTED_G42_REFERENCE_SOURCE_COMMIT,
        "accepted_g42_aligned_source_commit": ACCEPTED_G42_ALIGNED_SOURCE_COMMIT,
        "accepted_g42_alignment_stage_commit": ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT,
        "accepted_g43_source_commit": ACCEPTED_G43_SOURCE_COMMIT,
        "accepted_g43_aligned_source_commit": ACCEPTED_G43_ALIGNED_SOURCE_COMMIT,
        "accepted_g43_alignment_stage_commit": ACCEPTED_G43_ALIGNMENT_STAGE_COMMIT,
        "accepted_g40_anchor_replicate": models[
            INDEPENDENT_ARM
        ].accepted_g40_anchor_authority.replicate,
        "branch_boundary": boundary,
        "update_index": update_index,
        "arms": list(ARMS),
        "branch_update_order": list(ARMS),
        "paired_collection_before_update": True,
        "normalization_rows": NORMALIZATION_ROWS,
        "normalization_unit": "one_team_residual_row_per_primitive_step",
        "same_ordered_row_set_for_both_channels": True,
        "active_count_weighting": False,
        "episode_exclusions": "none",
        "normalization_count": 1,
        "normalization_recomputed_between_passes": False,
        "actor_head_optimizer_steps_before": steps_before,
        "actor_head_optimizer_steps": steps_after,
        "actor_head_optimizer_step_delta": PPO_PASSES,
        "baseline_update_rule_equal": True,
        "baseline_optimizer_exposure_equal": (
            steps_after[INDEPENDENT_ARM] == steps_after[POOLED_ARM]
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
                g43.validate_registered_gradient_evidence(
                    pass_record["gradient_evidence"][arm]  # type: ignore[index]
                )
                for arm in ARMS
            )
            and validate_schedule_record(
                pass_record["channel_scale_schedule"]  # type: ignore[index]
            )
            and validate_normalization_by_arm(
                pass_record["normalization_by_arm"]  # type: ignore[index]
            )
            and _normalization_statistics_match(
                pass_record["channel_scale_schedule"],  # type: ignore[index]
                pass_record["normalization_by_arm"][  # type: ignore[index]
                    INDEPENDENT_ARM
                ],
            )
            for pass_record in pass_records
        )
    )
    if not _update_evidence_valid(record):
        raise RuntimeError("G44 serialized update evidence failed validation")
    return record


# Name consumed by the isolated G43 orchestration backend.
optimize_norm_schedule_update = optimize_channel_scale_update


def _valid_composition(value: object, arm: str) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    if value.get("literal_coefficient") != EQUAL_MEAN_COEFFICIENT:
        return False
    if value.get("entropy_added_after_credit_gate") is not True:
        return False
    if (
        value.get("entropy_gradient_source_arm") != INDEPENDENT_ARM
        or value.get("entropy_gradient_bitwise_identical_across_arms") is not True
    ):
        return False
    if (
        value.get("entropy_and_baseline_terms_bitwise_independent_of_scale_path")
        is not True
    ):
        return False
    if arm == INDEPENDENT_ARM:
        return value.get("mode") == "equal_mean_independent_channel_scale"
    return bool(
        value.get("mode") == "equal_mean_pooled_channel_scale_norm_matched"
        and value.get("counterfactual_scale_shadow") is True
        and value.get("shadow_output_type") == "one_detached_scalar_norm"
        and value.get("shadow_vector_serialized") is False
        and value.get("shadow_vector_coordinate_use_outside_norm") == 0
        and value.get("shadow_gradient_assignment_count") == 0
        and value.get("shadow_optimizer_state_count") == 0
        and value.get("shadow_RNG_consumption") == 0
        and value.get("shadow_model_mutation_count") == 0
        and value.get("shadow_checkpoint_selection_reads") == 0
        and value.get("shadow_evaluation_reads") == 0
        and value.get("pooled_arm_evidence_read_count") == 0
        and value.get("unscaled_raw_norm_compared_to_counterfactual") is False
        and float(value.get("assigned_norm_match_error", np.inf))
        <= float(value.get("assigned_norm_match_tolerance", -1.0))
    )


def _update_evidence_valid(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    replicate = value.get("accepted_g40_anchor_replicate")
    boundary = value.get("branch_boundary")
    if (
        isinstance(replicate, bool)
        or not isinstance(replicate, int)
        or replicate not in ACCEPTED_G40_ANCHOR_REPLICATES
        or not isinstance(boundary, Mapping)
        or boundary.get("accepted_g40_anchor_authority")
        != g41.accepted_g40_anchor_identity(replicate)
        or value.get("branch_update_order") != list(ARMS)
        or value.get("normalization_rows") != NORMALIZATION_ROWS
        or value.get("normalization_count") != 1
        or value.get("normalization_recomputed_between_passes") is not False
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
        evidence = record.get("gradient_evidence")
        composition = record.get("composition")
        normalization_by_arm = record.get("normalization_by_arm")
        if (
            not isinstance(evidence, Mapping)
            or tuple(evidence) != ARMS
            or any(
                not g43.validate_registered_gradient_evidence(evidence.get(arm))
                for arm in ARMS
            )
            or not isinstance(composition, Mapping)
            or tuple(composition) != ARMS
            or any(not _valid_composition(composition.get(arm), arm) for arm in ARMS)
            or not validate_normalization_by_arm(normalization_by_arm)
            or not validate_schedule_record(record.get("channel_scale_schedule"))
            or not isinstance(normalization_by_arm, Mapping)
            or not _normalization_statistics_match(
                record.get("channel_scale_schedule"),
                normalization_by_arm.get(INDEPENDENT_ARM),
            )
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


def build_conclusion_evidence(
    update_records: Sequence[Mapping[str, object]], *, formal: bool
) -> dict[str, object]:
    if not isinstance(formal, bool) or not update_records:
        raise ValueError("G44 conclusion evidence requires records and bool scope")
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
            schedule = pass_record["channel_scale_schedule"]
            normalization_by_arm = _canonical_normalization_by_arm(
                pass_record["normalization_by_arm"]
            )
            maximum = max(float(schedule["s_I"]), float(schedule["s_S"]))
            q_scale = (
                abs(float(schedule["s_I"]) - float(schedule["s_S"])) / maximum
                if maximum > 0.0
                else 0.0
            )
            independent_norm = float(schedule["independent_credit_norm"])
            pooled_norm = float(schedule["pooled_counterfactual_credit_norm"])
            if independent_norm > 0.0 and pooled_norm > 0.0:
                cosine = max(
                    -1.0,
                    min(
                        1.0,
                        float(schedule["reference_credit_dot_product"])
                        / (independent_norm * pooled_norm),
                    ),
                )
                q_direction = float(
                    np.sqrt(max(0.0, 2.0 - 2.0 * cosine))
                )
            else:
                q_direction = 0.0
            active = bool(
                q_scale > ACTIVATION_TOLERANCE
                and q_direction > ACTIVATION_TOLERANCE
                and independent_norm > 0.0
                and pooled_norm > 0.0
            )
            if (
                float(schedule["q_scale"]) != q_scale
                or float(schedule["q_direction"]) != q_direction
                or schedule.get("strict_activation_observed") is not active
            ):
                records_valid = False
            rows_by_replicate[replicate].append(
                {
                    "normalization_by_arm": normalization_by_arm,
                    "immediate_mean": float(schedule["immediate_mean"]),
                    "successor_mean": float(schedule["successor_mean"]),
                    "immediate_centered_sum_square": float(
                        schedule["immediate_centered_sum_square"]
                    ),
                    "successor_centered_sum_square": float(
                        schedule["successor_centered_sum_square"]
                    ),
                    "immediate_scale": float(schedule["immediate_scale"]),
                    "successor_scale": float(schedule["successor_scale"]),
                    "pooled_scale": float(schedule["pooled_scale"]),
                    "normalization_row_count": int(
                        schedule["normalization_row_count"]
                    ),
                    "normalization_mask_digest": str(
                        schedule["normalization_mask_digest"]
                    ),
                    "s_I": float(schedule["s_I"]),
                    "s_S": float(schedule["s_S"]),
                    "s_P": float(schedule["s_P"]),
                    "q_scale": q_scale,
                    "independent_credit_norm": float(
                        schedule["independent_credit_norm"]
                    ),
                    "pooled_counterfactual_credit_norm": float(
                        schedule["pooled_counterfactual_credit_norm"]
                    ),
                    "reference_credit_dot_product": float(
                        schedule["reference_credit_dot_product"]
                    ),
                    "q_direction": q_direction,
                    "active": active,
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
            "q_scale>1e-6_and_q_direction>1e-6_and_both_credit_norms_positive"
        ),
        "evidence_source_arm": INDEPENDENT_ARM,
        "normalization_evidence_arms": list(ARMS),
        "reference_pooled_counterfactual": True,
        "pooled_arm_evidence_read_count": 0,
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
        or value.get("evidence_source_arm") != INDEPENDENT_ARM
        or value.get("normalization_evidence_arms") != list(ARMS)
        or value.get("reference_pooled_counterfactual") is not True
        or value.get("pooled_arm_evidence_read_count") != 0
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
            normalization_by_arm = item.get("normalization_by_arm")
            if (
                not validate_normalization_by_arm(normalization_by_arm)
                or not isinstance(normalization_by_arm, Mapping)
                or not _normalization_statistics_match(
                    item, normalization_by_arm.get(INDEPENDENT_ARM)
                )
            ):
                return False
            names = (
                "immediate_mean",
                "successor_mean",
                "immediate_centered_sum_square",
                "successor_centered_sum_square",
                "immediate_scale",
                "successor_scale",
                "pooled_scale",
                "s_I",
                "s_S",
                "s_P",
                "q_scale",
                "independent_credit_norm",
                "pooled_counterfactual_credit_norm",
                "reference_credit_dot_product",
                "q_direction",
            )
            if any(
                isinstance(item.get(name), bool)
                or not isinstance(item.get(name), (int, float))
                or not np.isfinite(float(item[name]))
                or (
                    name
                    not in (
                        "immediate_mean",
                        "successor_mean",
                        "reference_credit_dot_product",
                    )
                    and float(item[name]) < 0.0
                )
                for name in names
            ):
                return False
            row_count = item.get("normalization_row_count")
            if (
                isinstance(row_count, bool)
                or row_count != NORMALIZATION_ROWS
                or item.get("normalization_mask_digest")
                != NORMALIZATION_MASK_DIGEST
            ):
                return False
            immediate_sum = float(item["immediate_centered_sum_square"])
            successor_sum = float(item["successor_centered_sum_square"])
            if (
                float(item["immediate_scale"])
                != float(np.sqrt(immediate_sum / float(NORMALIZATION_ROWS)))
                or float(item["successor_scale"])
                != float(np.sqrt(successor_sum / float(NORMALIZATION_ROWS)))
                or float(item["pooled_scale"])
                != float(
                    np.sqrt(
                        (immediate_sum + successor_sum)
                        / float(2 * NORMALIZATION_ROWS)
                    )
                )
                or float(item["s_I"]) != float(item["immediate_scale"])
                or float(item["s_S"]) != float(item["successor_scale"])
                or float(item["s_P"]) != float(item["pooled_scale"])
            ):
                return False
            maximum = max(float(item["s_I"]), float(item["s_S"]))
            q_scale = (
                abs(float(item["s_I"]) - float(item["s_S"])) / maximum
                if maximum > 0.0
                else 0.0
            )
            independent_norm = float(item["independent_credit_norm"])
            pooled_norm = float(item["pooled_counterfactual_credit_norm"])
            if independent_norm > 0.0 and pooled_norm > 0.0:
                cosine = max(
                    -1.0,
                    min(
                        1.0,
                        float(item["reference_credit_dot_product"])
                        / (independent_norm * pooled_norm),
                    ),
                )
                q_direction = float(
                    np.sqrt(max(0.0, 2.0 - 2.0 * cosine))
                )
            else:
                q_direction = 0.0
            expected_active = bool(
                q_scale > ACTIVATION_TOLERANCE
                and q_direction > ACTIVATION_TOLERANCE
                and independent_norm > 0.0
                and pooled_norm > 0.0
            )
            if (
                float(item["q_scale"]) != q_scale
                or float(item["q_direction"]) != q_direction
                or item.get("active") is not expected_active
            ):
                return False
            active |= expected_active
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
        raise ValueError("G44 refuses to serialize invalid update evidence")
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
        raise ValueError("G44 final checkpoint arm is not registered")
    if not _update_evidence_valid(final_update_record):
        raise ValueError("G44 final checkpoint update evidence invalid")
    if not validate_conclusion_evidence(conclusion_evidence):
        raise ValueError("G44 final checkpoint activation evidence invalid")
    if conclusion_evidence.get("formal") is not formal:
        raise ValueError("G44 final checkpoint scope mismatch")
    state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
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
        "accepted_g43_source_commit": ACCEPTED_G43_SOURCE_COMMIT,
        "normalization_evidence_arms": list(ARMS),
        "actor_head_optimizer_steps": PPO_PASSES,
        "standalone_slow_present": False,
        "standalone_slow_critic_present": False,
        "db_vector_present": False,
        "db_norm_present": False,
        "db_shadow_present": False,
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
