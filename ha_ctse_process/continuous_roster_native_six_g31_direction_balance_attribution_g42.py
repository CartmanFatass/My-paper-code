"""Exact G41 direction-balance attribution with a scale-matched raw-sum null."""

from __future__ import annotations

import copy
import dis
import inspect
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory


ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42"
)
SOURCE_ID = f"{ALGORITHM_ID}_P0"
ACCEPTED_G41_SOURCE_COMMIT = "a5f63c349228fc2bba7843647e0ae4c34361c1c9"
DB_ARM = "NATIVE6_G31_DB_NO_SLOW"
NO_DB_ARM = "NATIVE6_G31_NO_DB_NO_SLOW"
ARMS = (DB_ARM, NO_DB_ARM)
ACCEPTED_G40_ANCHOR_REPLICATES = (0, 1, 2)
PPO_PASSES = g41.PPO_PASSES
MAX_CONFORMANCE_TRANSITIONS = g41.MAX_CONFORMANCE_TRANSITIONS
GRADIENT_LIVE_TOLERANCE = g40.GRADIENT_LIVE_TOLERANCE
SCALE_MATCH_ATOL = 1e-8
SCALE_MATCH_RTOL = 1e-6
DIRECTION_SEPARATION_TOLERANCE = 1e-6


class G42GradientGateError(ValueError):
    """A pre-step gradient-composition gate failed without a fallback."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object]) -> None:
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics)
        super().__init__(f"G42 gradient gate failed before optimizer step: {reason}")

    def to_record(self) -> dict[str, object]:
        return {
            "passed": False,
            "stage": "before_optimizer_step",
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
            "channel_fallback_used": False,
            "sum_perturbed": False,
        }


@dataclass(frozen=True)
class ScaleMatchedRawSumComposition:
    gradients: tuple[torch.Tensor, ...]
    raw_sum_gradients: tuple[torch.Tensor, ...]
    immediate_norm: float
    successor_norm: float
    raw_sum_norm: float
    registered_gradient_norm: float
    applied_gradient_norm: float
    scale_factor: float
    scale_match_error: float
    scale_match_tolerance: float
    registered_norm_zero: bool


@dataclass(frozen=True)
class _ChannelGradientProbe:
    policy: torch.Tensor
    immediate_baseline_loss: torch.Tensor
    successor_baseline_loss: torch.Tensor
    immediate_actor_gradients: tuple[torch.Tensor, ...]
    successor_actor_gradients: tuple[torch.Tensor, ...]
    gradient_evidence: dict[str, object]


@dataclass(frozen=True)
class _RawSumPassPlan:
    policy: torch.Tensor
    immediate_baseline_loss: torch.Tensor
    successor_baseline_loss: torch.Tensor
    composition: ScaleMatchedRawSumComposition
    gradient_evidence: dict[str, object]


def _gradient_rows(
    rows: Sequence[torch.Tensor | None], parameters: Sequence[nn.Parameter]
) -> tuple[torch.Tensor, ...]:
    if len(rows) != len(parameters) or not parameters:
        raise G42GradientGateError("gradient_inventory_mismatch", {})
    materialized = tuple(
        torch.zeros_like(parameter) if row is None else row.detach()
        for row, parameter in zip(rows, parameters)
    )
    if any(
        row.shape != parameter.shape or not bool(torch.isfinite(row).all())
        for row, parameter in zip(materialized, parameters)
    ):
        raise G42GradientGateError("gradient_shape_or_finiteness", {})
    return materialized


def _global_norm(rows: Sequence[torch.Tensor]) -> float:
    return float(
        torch.sqrt(
            sum(row.to(torch.float64).square().sum() for row in rows)
        )
        .detach()
        .cpu()
    )


def validate_scale_match(
    *, registered_gradient_norm: float, applied_gradient_norm: float
) -> tuple[float, float]:
    values = (registered_gradient_norm, applied_gradient_norm)
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(float(value))
        for value in values
    ):
        raise G42GradientGateError(
            "nonfinite_scale_match_input",
            {
                "registered_gradient_norm": registered_gradient_norm,
                "applied_gradient_norm": applied_gradient_norm,
            },
        )
    target = float(registered_gradient_norm)
    applied = float(applied_gradient_norm)
    tolerance = SCALE_MATCH_ATOL + SCALE_MATCH_RTOL * abs(target)
    error = abs(applied - target)
    if target < 0.0 or applied < 0.0:
        raise G42GradientGateError(
            "negative_scale_match_norm",
            {
                "registered_gradient_norm": target,
                "applied_gradient_norm": applied,
            },
        )
    if target == 0.0:
        if applied != 0.0:
            raise G42GradientGateError(
                "non_scale_match",
                {
                    "registered_gradient_norm": target,
                    "applied_gradient_norm": applied,
                    "scale_match_error": error,
                    "scale_match_tolerance": 0.0,
                },
            )
        return 0.0, 0.0
    if applied == 0.0 or error > tolerance:
        raise G42GradientGateError(
            "non_scale_match",
            {
                "registered_gradient_norm": target,
                "applied_gradient_norm": applied,
                "scale_match_error": error,
                "scale_match_tolerance": tolerance,
            },
        )
    return error, tolerance


def compose_scale_matched_raw_sum_gradients(
    immediate: Sequence[torch.Tensor | None],
    successor: Sequence[torch.Tensor | None],
    parameters: Sequence[nn.Parameter],
    *,
    registered_gradient_norm: float,
) -> ScaleMatchedRawSumComposition:
    """Use only the raw-sum direction and one registered scalar norm."""

    immediate_rows = _gradient_rows(immediate, parameters)
    successor_rows = _gradient_rows(successor, parameters)
    immediate_norm = _global_norm(immediate_rows)
    successor_norm = _global_norm(successor_rows)
    target = float(registered_gradient_norm)
    diagnostics = {
        "immediate_norm": immediate_norm,
        "successor_norm": successor_norm,
        "registered_gradient_norm": target,
    }
    raw_sum = tuple(
        left.to(torch.float64) + right.to(torch.float64)
        for left, right in zip(immediate_rows, successor_rows)
    )
    raw_sum_norm = _global_norm(raw_sum)
    diagnostics["raw_sum_norm"] = raw_sum_norm
    if not np.isfinite(target) or target < 0.0:
        raise G42GradientGateError(
            "registered_gradient_norm_negative_or_nonfinite", diagnostics
        )
    if target == 0.0:
        gradients = tuple(torch.zeros_like(parameter) for parameter in parameters)
        error, tolerance = validate_scale_match(
            registered_gradient_norm=target,
            applied_gradient_norm=_global_norm(gradients),
        )
        return ScaleMatchedRawSumComposition(
            gradients=gradients,
            raw_sum_gradients=raw_sum,
            immediate_norm=immediate_norm,
            successor_norm=successor_norm,
            raw_sum_norm=raw_sum_norm,
            registered_gradient_norm=target,
            applied_gradient_norm=0.0,
            scale_factor=0.0,
            scale_match_error=error,
            scale_match_tolerance=tolerance,
            registered_norm_zero=True,
        )
    if not np.isfinite(raw_sum_norm) or raw_sum_norm == 0.0:
        raise G42GradientGateError("positive_norm_raw_sum_zero_or_nonfinite", diagnostics)
    scale_factor = target / raw_sum_norm
    if not np.isfinite(scale_factor) or scale_factor <= 0.0:
        raise G42GradientGateError("invalid_scale_factor", diagnostics)
    gradients = tuple(
        (row * scale_factor).to(parameter.dtype)
        for row, parameter in zip(raw_sum, parameters)
    )
    if any(not bool(torch.isfinite(row).all()) for row in gradients):
        raise G42GradientGateError("scaled_raw_sum_nonfinite", diagnostics)
    applied_norm = _global_norm(gradients)
    error, tolerance = validate_scale_match(
        registered_gradient_norm=target,
        applied_gradient_norm=applied_norm,
    )
    return ScaleMatchedRawSumComposition(
        gradients=gradients,
        raw_sum_gradients=raw_sum,
        immediate_norm=immediate_norm,
        successor_norm=successor_norm,
        raw_sum_norm=raw_sum_norm,
        registered_gradient_norm=target,
        applied_gradient_norm=applied_norm,
        scale_factor=scale_factor,
        scale_match_error=error,
        scale_match_tolerance=tolerance,
        registered_norm_zero=False,
    )


def raw_sum_composition_record(
    composition: ScaleMatchedRawSumComposition,
) -> dict[str, object]:
    return {
        "mode": "scale_matched_raw_sum",
        "immediate_norm": composition.immediate_norm,
        "successor_norm": composition.successor_norm,
        "raw_sum_norm": composition.raw_sum_norm,
        "registered_gradient_norm": composition.registered_gradient_norm,
        "applied_gradient_norm": composition.applied_gradient_norm,
        "scale_factor": composition.scale_factor,
        "scale_match_error": composition.scale_match_error,
        "scale_match_tolerance": composition.scale_match_tolerance,
        "registered_norm_zero": composition.registered_norm_zero,
        "actor_gradients_exact_zero": all(
            bool(torch.count_nonzero(row) == 0)
            for row in composition.gradients
        ),
        "db_direction_input_present": False,
        "channel_fallback_used": False,
        "sum_perturbed": False,
        "passed": True,
    }


def _gradient_liveness_row(rows: Sequence[torch.Tensor]) -> dict[str, object]:
    norm = _global_norm(rows)
    finite = bool(np.isfinite(norm))
    return {
        "gradient_norm": norm,
        "finite": finite,
        "live": bool(finite and norm > GRADIENT_LIVE_TOLERANCE),
    }


def registered_gradient_evidence(
    model: g41.G41NoSlowProjection,
    immediate_actor_gradients: Sequence[torch.Tensor | None],
    successor_actor_gradients: Sequence[torch.Tensor | None],
    immediate_baseline_gradients: Sequence[torch.Tensor | None],
    successor_baseline_gradients: Sequence[torch.Tensor | None],
) -> dict[str, object]:
    """Bind every registered actor group and both baseline-output gradients."""

    actor_parameters = model.full_actor_parameters()
    baseline_parameters = tuple(model.credit_baselines.parameters())
    immediate_actor = _gradient_rows(
        immediate_actor_gradients, actor_parameters
    )
    successor_actor = _gradient_rows(
        successor_actor_gradients, actor_parameters
    )
    immediate_baseline = _gradient_rows(
        immediate_baseline_gradients, baseline_parameters
    )
    successor_baseline = _gradient_rows(
        successor_baseline_gradients, baseline_parameters
    )
    actor_groups = g40._actor_groups(model)
    if tuple(actor_groups) != g40.REGISTERED_ACTOR_GROUPS:
        raise G42GradientGateError(
            "registered_actor_group_inventory_mismatch",
            {"observed_actor_groups": tuple(actor_groups)},
        )
    actor_names = {
        id(parameter): name
        for name, parameter in g40._named_full_actor_parameters(model)
    }
    actor_indexes = {
        id(parameter): index
        for index, parameter in enumerate(actor_parameters)
    }
    grouped_parameter_ids = tuple(
        id(parameter)
        for parameters in actor_groups.values()
        for parameter in parameters
    )
    if (
        len(set(grouped_parameter_ids)) != len(grouped_parameter_ids)
        or set(grouped_parameter_ids) != set(actor_indexes)
        or set(actor_names) != set(actor_indexes)
    ):
        raise G42GradientGateError(
            "registered_actor_group_parameter_coverage_mismatch", {}
        )

    def channel_rows(
        gradients: tuple[torch.Tensor, ...],
    ) -> dict[str, dict[str, object]]:
        return {
            group: _gradient_liveness_row(
                tuple(gradients[actor_indexes[id(parameter)]] for parameter in parameters)
            )
            for group, parameters in actor_groups.items()
        }

    evidence = {
        "registered_actor_groups": list(g40.REGISTERED_ACTOR_GROUPS),
        "actor_group_parameter_names": {
            group: [actor_names[id(parameter)] for parameter in parameters]
            for group, parameters in actor_groups.items()
        },
        "actor_channels": {
            "immediate": channel_rows(immediate_actor),
            "successor": channel_rows(successor_actor),
        },
        "actor_channel_global": {
            "immediate": _gradient_liveness_row(immediate_actor),
            "successor": _gradient_liveness_row(successor_actor),
        },
        "baseline_outputs": {
            "immediate": _gradient_liveness_row(immediate_baseline),
            "successor": _gradient_liveness_row(successor_baseline),
        },
    }
    evidence["passed"] = validate_registered_gradient_evidence(evidence)
    return evidence


def _valid_live_gradient_row(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    norm = value.get("gradient_norm")
    return bool(
        value.get("finite") is True
        and value.get("live") is True
        and isinstance(norm, (int, float))
        and not isinstance(norm, bool)
        and np.isfinite(float(norm))
        and float(norm) > GRADIENT_LIVE_TOLERANCE
    )


def _valid_finite_gradient_row(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    norm = value.get("gradient_norm")
    if (
        not isinstance(norm, (int, float))
        or isinstance(norm, bool)
        or not np.isfinite(float(norm))
        or float(norm) < 0.0
    ):
        return False
    return bool(
        value.get("finite") is True
        and isinstance(value.get("live"), bool)
        and value.get("live")
        is (float(norm) > GRADIENT_LIVE_TOLERANCE)
    )


def validate_registered_gradient_evidence(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    if value.get("registered_actor_groups") != list(g40.REGISTERED_ACTOR_GROUPS):
        return False
    inventory = value.get("actor_group_parameter_names")
    channels = value.get("actor_channels")
    global_channels = value.get("actor_channel_global")
    baselines = value.get("baseline_outputs")
    if (
        not isinstance(inventory, Mapping)
        or set(inventory) != set(g40.REGISTERED_ACTOR_GROUPS)
        or any(
            not isinstance(inventory.get(group), list)
            or not inventory[group]
            or any(not isinstance(name, str) for name in inventory[group])
            for group in g40.REGISTERED_ACTOR_GROUPS
        )
        or not isinstance(channels, Mapping)
        or tuple(channels) != ("immediate", "successor")
        or not isinstance(global_channels, Mapping)
        or tuple(global_channels) != ("immediate", "successor")
        or any(
            not _valid_live_gradient_row(global_channels.get(channel))
            for channel in ("immediate", "successor")
        )
        or not isinstance(baselines, Mapping)
        or tuple(baselines) != ("immediate", "successor")
    ):
        return False
    for channel in ("immediate", "successor"):
        rows = channels.get(channel)
        if (
            not isinstance(rows, Mapping)
            or set(rows) != set(g40.REGISTERED_ACTOR_GROUPS)
            or any(
                not _valid_finite_gradient_row(rows.get(group))
                for group in g40.REGISTERED_ACTOR_GROUPS
            )
        ):
            return False
    return bool(
        all(
            any(
                channels[channel][group]["live"] is True
                for channel in ("immediate", "successor")
            )
            for group in g40.REGISTERED_ACTOR_GROUPS
        )
        and all(
            _valid_live_gradient_row(baselines.get(output))
            for output in ("immediate", "successor")
        )
    )


def _channel_gradient_probe(
    model: g41.G41NoSlowProjection,
    replay: g41.G41RetainedReplay,
    trajectory: AnchoredRosterTrajectory,
    credit: g41.G41Credit,
    normalized_advantages: tuple[torch.Tensor, torch.Tensor],
) -> _ChannelGradientProbe:
    actor_parameters = model.full_actor_parameters()
    baseline_parameters = tuple(model.credit_baselines.parameters())
    entropy_loss = g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
    immediate = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized_advantages[0]
    ) - entropy_loss
    successor = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized_advantages[1]
    ) - entropy_loss
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
    immediate_baseline_loss = F.mse_loss(
        replay.immediate_baselines, trajectory.rewards.detach()
    )
    successor_baseline_loss = F.mse_loss(
        replay.successor_baselines, credit.successor_targets
    )
    immediate_baseline = torch.autograd.grad(
        immediate_baseline_loss,
        baseline_parameters,
        retain_graph=True,
        allow_unused=True,
    )
    successor_baseline = torch.autograd.grad(
        successor_baseline_loss,
        baseline_parameters,
        retain_graph=True,
        allow_unused=True,
    )
    evidence = registered_gradient_evidence(
        model,
        immediate_actor,
        successor_actor,
        immediate_baseline,
        successor_baseline,
    )
    if not validate_registered_gradient_evidence(evidence):
        raise G42GradientGateError(
            "registered_gradient_evidence_failed", evidence
        )
    return _ChannelGradientProbe(
        policy=0.5 * (immediate + successor),
        immediate_baseline_loss=immediate_baseline_loss,
        successor_baseline_loss=successor_baseline_loss,
        immediate_actor_gradients=immediate_actor,
        successor_actor_gradients=successor_actor,
        gradient_evidence=evidence,
    )


def raw_sum_null_dependency_audit() -> dict[str, object]:
    functions = (
        compose_scale_matched_raw_sum_gradients,
        _gradient_rows,
        _global_norm,
        validate_scale_match,
    )
    reads_by_function = {
        function.__name__: tuple(
            str(instruction.argval)
            for instruction in dis.get_instructions(function)
            if instruction.opname
            in {"LOAD_GLOBAL", "LOAD_ATTR", "LOAD_METHOD"}
        )
        for function in functions
    }
    forbidden = tuple(
        f"{function_name}:{name}"
        for function_name, reads in reads_by_function.items()
        for name in reads
        if any(
            marker in name.lower()
            for marker in (
                "direction_balanced",
                "db_direction",
                "directionbalanced",
            )
        )
    )
    expected_signature = (
        "immediate",
        "successor",
        "parameters",
        "registered_gradient_norm",
    )
    observed_signature = tuple(
        inspect.signature(
            compose_scale_matched_raw_sum_gradients
        ).parameters
    )
    scalar_only_contract = observed_signature == expected_signature
    return {
        "audited_functions": tuple(function.__name__ for function in functions),
        "bytecode_reads": reads_by_function,
        "input_signature": observed_signature,
        "forbidden_db_direction_reads": forbidden,
        "registered_scalar_norm_only": scalar_only_contract and not forbidden,
        "passed": scalar_only_contract and not forbidden,
    }


def direction_unit_distance_record(
    db_gradients: Sequence[torch.Tensor],
    raw_sum_gradients: Sequence[torch.Tensor],
    *,
    registered_gradient_norm: float,
) -> dict[str, object]:
    if not db_gradients or len(db_gradients) != len(raw_sum_gradients):
        raise G42GradientGateError("direction_distance_inventory_mismatch", {})
    if any(
        left.shape != right.shape
        or not bool(torch.isfinite(left).all())
        or not bool(torch.isfinite(right).all())
        for left, right in zip(db_gradients, raw_sum_gradients)
    ):
        raise G42GradientGateError(
            "direction_distance_shape_or_finiteness", {}
        )
    db_norm = _global_norm(db_gradients)
    raw_sum_norm = _global_norm(raw_sum_gradients)
    validate_scale_match(
        registered_gradient_norm=registered_gradient_norm,
        applied_gradient_norm=db_norm,
    )
    if registered_gradient_norm == 0.0:
        return {
            "db_unit_direction_norm": 0.0,
            "raw_sum_unit_direction_norm": (
                0.0 if raw_sum_norm == 0.0 else 1.0
            ),
            "unit_direction_distance": 0.0,
            "unit_direction_distance_defined": False,
            "registered_norm_zero": True,
            "strict_separation_observed": False,
            "separation_threshold": DIRECTION_SEPARATION_TOLERANCE,
            "passed": True,
        }
    if not np.isfinite(raw_sum_norm) or raw_sum_norm == 0.0:
        raise G42GradientGateError(
            "positive_norm_raw_sum_zero_or_nonfinite",
            {
                "registered_gradient_norm": registered_gradient_norm,
                "raw_sum_norm": raw_sum_norm,
            },
        )
    distance = _global_norm(
        tuple(
            left.to(torch.float64) / db_norm
            - right.to(torch.float64) / raw_sum_norm
            for left, right in zip(db_gradients, raw_sum_gradients)
        )
    )
    if not np.isfinite(distance):
        raise G42GradientGateError("direction_distance_nonfinite", {})
    return {
        "db_unit_direction_norm": 1.0,
        "raw_sum_unit_direction_norm": 1.0,
        "unit_direction_distance": distance,
        "unit_direction_distance_defined": True,
        "registered_norm_zero": False,
        "strict_separation_observed": bool(
            distance > DIRECTION_SEPARATION_TOLERANCE
        ),
        "separation_threshold": DIRECTION_SEPARATION_TOLERANCE,
        "passed": True,
    }


def _update_gradient_evidence_valid(value: object) -> bool:
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
    ):
        return False
    pass_records = value.get("pass_records")
    if not isinstance(pass_records, list) or len(pass_records) != PPO_PASSES:
        return False
    for pass_index, pass_record in enumerate(pass_records):
        if (
            not isinstance(pass_record, Mapping)
            or pass_record.get("pass_index") != pass_index
        ):
            return False
        evidence_by_arm = pass_record.get("gradient_evidence")
        comparison = pass_record.get("direction_comparison")
        if (
            not isinstance(evidence_by_arm, Mapping)
            or tuple(evidence_by_arm) != ARMS
            or any(
                not validate_registered_gradient_evidence(
                    evidence_by_arm.get(arm)
                )
                for arm in ARMS
            )
            or not isinstance(comparison, Mapping)
            or comparison.get("passed") is not True
        ):
            return False
        distance = comparison.get("unit_direction_distance")
        if (
            not isinstance(distance, (int, float))
            or isinstance(distance, bool)
            or not np.isfinite(float(distance))
            or float(distance) < 0.0
        ):
            return False
    return True


def build_conclusion_evidence(
    update_records: Sequence[Mapping[str, object]], *, formal: bool
) -> dict[str, object]:
    if not isinstance(formal, bool) or not update_records:
        raise ValueError("G42 conclusion evidence requires records and a bool scope")
    rows_by_replicate: dict[int, list[float]] = {}
    defined_by_replicate: dict[int, list[bool]] = {}
    records_valid = True
    for record in update_records:
        replicate = record.get("accepted_g40_anchor_replicate")
        if (
            isinstance(replicate, bool)
            or not isinstance(replicate, int)
            or replicate not in ACCEPTED_G40_ANCHOR_REPLICATES
            or not _update_gradient_evidence_valid(record)
        ):
            records_valid = False
            continue
        rows_by_replicate.setdefault(replicate, [])
        defined_by_replicate.setdefault(replicate, [])
        for pass_record in record["pass_records"]:  # type: ignore[index]
            comparison = pass_record["direction_comparison"]
            rows_by_replicate[replicate].append(
                float(comparison["unit_direction_distance"])
            )
            defined_by_replicate[replicate].append(
                comparison["unit_direction_distance_defined"] is True
            )
    required_replicates = (
        list(ACCEPTED_G40_ANCHOR_REPLICATES)
        if formal
        else sorted(rows_by_replicate)
    )
    replicate_rows = [
        {
            "replicate": replicate,
            "unit_direction_distances": rows_by_replicate.get(replicate, []),
            "unit_direction_distance_defined": defined_by_replicate.get(
                replicate, []
            ),
            "strict_separation_observed": any(
                defined
                and distance > DIRECTION_SEPARATION_TOLERANCE
                for distance, defined in zip(
                    rows_by_replicate.get(replicate, []),
                    defined_by_replicate.get(replicate, []),
                )
            ),
        }
        for replicate in required_replicates
    ]
    scope_valid = (
        set(rows_by_replicate) == set(ACCEPTED_G40_ANCHOR_REPLICATES)
        if formal
        else len(rows_by_replicate) == 1
    )
    evidence = {
        "formal": formal,
        "required_replicates": required_replicates,
        "separation_threshold": DIRECTION_SEPARATION_TOLERANCE,
        "strictly_greater_required": True,
        "records_valid": records_valid,
        "gradient_evidence_valid": records_valid,
        "replicate_rows": replicate_rows,
        "passed": bool(
            records_valid
            and scope_valid
            and replicate_rows
            and all(row["strict_separation_observed"] for row in replicate_rows)
        ),
    }
    return evidence


def validate_conclusion_evidence(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    formal = value.get("formal")
    rows = value.get("replicate_rows")
    required = value.get("required_replicates")
    if (
        not isinstance(formal, bool)
        or value.get("separation_threshold") != DIRECTION_SEPARATION_TOLERANCE
        or value.get("strictly_greater_required") is not True
        or value.get("records_valid") is not True
        or value.get("gradient_evidence_valid") is not True
        or not isinstance(rows, list)
        or not isinstance(required, list)
        or not rows
    ):
        return False
    expected_replicates = (
        list(ACCEPTED_G40_ANCHOR_REPLICATES) if formal else required
    )
    if required != expected_replicates or (not formal and len(required) != 1):
        return False
    observed: list[int] = []
    for row in rows:
        if not isinstance(row, Mapping):
            return False
        replicate = row.get("replicate")
        distances = row.get("unit_direction_distances")
        defined = row.get("unit_direction_distance_defined")
        if (
            isinstance(replicate, bool)
            or not isinstance(replicate, int)
            or replicate not in ACCEPTED_G40_ANCHOR_REPLICATES
            or not isinstance(distances, list)
            or not isinstance(defined, list)
            or not distances
            or len(distances) != len(defined)
            or any(
                not isinstance(distance, (int, float))
                or isinstance(distance, bool)
                or not np.isfinite(float(distance))
                or float(distance) < 0.0
                for distance in distances
            )
            or any(not isinstance(item, bool) for item in defined)
        ):
            return False
        separated = any(
            item and float(distance) > DIRECTION_SEPARATION_TOLERANCE
            for distance, item in zip(distances, defined)
        )
        if row.get("strict_separation_observed") is not separated:
            return False
        observed.append(replicate)
    return bool(
        observed == required
        and value.get("passed") is True
        and all(row["strict_separation_observed"] for row in rows)
    )


def project_g42_arms(
    anchor: g40.G40NativeSixPolicy, *, accepted_anchor_replicate: int
) -> dict[str, g41.G41NoSlowProjection]:
    if accepted_anchor_replicate not in ACCEPTED_G40_ANCHOR_REPLICATES:
        raise ValueError("G42 requires accepted G40 anchor replicate 0, 1, or 2")
    rng_before = torch.random.get_rng_state().clone()
    full, db_model = g41.project_post_anchor_paths(
        anchor, accepted_anchor_replicate=accepted_anchor_replicate
    )
    no_db_model = copy.deepcopy(db_model)
    if g41._state_rows(g41.retained_state_dict(full)) != g41._state_rows(
        db_model.state_dict()
    ):
        raise RuntimeError("G42 did not preserve the accepted G41 projection")
    models = {DB_ARM: db_model, NO_DB_ARM: no_db_model}
    if any(hasattr(model, "slow_critic") for model in models.values()):
        raise RuntimeError("G42 reintroduced the standalone slow critic")
    if g40.state_bytes(db_model) != g40.state_bytes(no_db_model):
        raise RuntimeError("G42 arm states differ before attribution")
    if g40.shared_tensor_storage_count((anchor, *models.values())) != 0:
        raise RuntimeError("G42 arm projection shares tensor storage")
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise RuntimeError("G42 arm projection advanced global torch RNG")
    return models


def _optimizer_owns_actor_head(
    optimizer: torch.optim.Optimizer, model: g41.G41NoSlowProjection
) -> bool:
    owned = tuple(
        parameter
        for group in optimizer.param_groups
        for parameter in group["params"]
    )
    expected = model.actor_credit_parameters()
    return tuple(id(row) for row in owned) == tuple(id(row) for row in expected)


def branch_boundary_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    inventory_valid = set(models) == set(ARMS) and set(optimizers) == set(ARMS)
    if not inventory_valid:
        return {"passed": False, "inventory_valid": False}
    db_model, no_db_model = models[DB_ARM], models[NO_DB_ARM]
    authority = db_model.accepted_g40_anchor_authority
    authority_valid = bool(
        authority
        == g41.accepted_g40_anchor_authority(authority.replicate)
        == no_db_model.accepted_g40_anchor_authority
    )
    states_equal = g40.state_bytes(db_model) == g40.state_bytes(no_db_model)
    parameter_contract = tuple(
        (name, tuple(parameter.shape), bool(parameter.requires_grad))
        for name, parameter in db_model.named_parameters()
    )
    parameter_contract_equal = parameter_contract == tuple(
        (name, tuple(parameter.shape), bool(parameter.requires_grad))
        for name, parameter in no_db_model.named_parameters()
    )
    no_slow = all(not hasattr(model, "slow_critic") for model in models.values())
    storage_disjoint = g40.shared_tensor_storage_count(tuple(models.values())) == 0
    phases_valid = all(model.phase == "credit_branch" for model in models.values())
    optimizer_types = all(
        isinstance(optimizer, torch.optim.Adam)
        for optimizer in optimizers.values()
    )
    optimizer_order = all(
        _optimizer_owns_actor_head(optimizers[arm], models[arm]) for arm in ARMS
    )
    optimizer_states_empty = all(optimizer.state == {} for optimizer in optimizers.values())
    optimizer_states_separate = (
        id(optimizers[DB_ARM].state) != id(optimizers[NO_DB_ARM].state)
    )
    passed = bool(
        authority_valid
        and states_equal
        and parameter_contract_equal
        and no_slow
        and storage_disjoint
        and phases_valid
        and optimizer_types
        and optimizer_order
        and optimizer_states_empty
        and optimizer_states_separate
    )
    return {
        "inventory_valid": True,
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(
            authority.replicate
        ),
        "authority_valid": authority_valid,
        "model_state_bytes_equal": states_equal,
        "parameter_name_shape_trainable_contract_equal": (
            parameter_contract_equal
        ),
        "trainable_parameter_count": sum(
            parameter.numel()
            for parameter in db_model.parameters()
            if parameter.requires_grad
        ),
        "standalone_slow_absent": no_slow,
        "shared_tensor_storage_count": 0 if storage_disjoint else 1,
        "branch_phases_valid": phases_valid,
        "optimizer_types_adam": optimizer_types,
        "optimizer_parameter_order_equal": optimizer_order,
        "optimizer_states_empty_and_separate": (
            optimizer_states_empty and optimizer_states_separate
        ),
        "passed": passed,
    }


def _prepare_raw_sum_pass(
    model: g41.G41NoSlowProjection,
    replay: g41.G41RetainedReplay,
    trajectory: AnchoredRosterTrajectory,
    credit: g41.G41Credit,
    normalized_advantages: tuple[torch.Tensor, torch.Tensor],
    *,
    registered_gradient_norm: float,
) -> _RawSumPassPlan:
    probe = _channel_gradient_probe(
        model, replay, trajectory, credit, normalized_advantages
    )
    composition = compose_scale_matched_raw_sum_gradients(
        probe.immediate_actor_gradients,
        probe.successor_actor_gradients,
        model.full_actor_parameters(),
        registered_gradient_norm=registered_gradient_norm,
    )
    return _RawSumPassPlan(
        policy=probe.policy,
        immediate_baseline_loss=probe.immediate_baseline_loss,
        successor_baseline_loss=probe.successor_baseline_loss,
        composition=composition,
        gradient_evidence=probe.gradient_evidence,
    )


def _optimizer_step_value(
    optimizer: torch.optim.Optimizer, parameter: nn.Parameter
) -> float:
    value = optimizer.state.get(parameter, {}).get("step", 0.0)
    return float(value.detach().cpu()) if isinstance(value, torch.Tensor) else float(value)


def _apply_raw_sum_pass(
    model: g41.G41NoSlowProjection,
    optimizer: torch.optim.Optimizer,
    plan: _RawSumPassPlan,
) -> tuple[float, float, float]:
    actor_parameters = model.full_actor_parameters()
    actor_head_parameters = model.actor_credit_parameters()
    if not isinstance(optimizer, torch.optim.Adam) or not _optimizer_owns_actor_head(
        optimizer, model
    ):
        raise ValueError("G42 NO_DB optimizer inventory mismatch")
    steps_before = tuple(
        _optimizer_step_value(optimizer, parameter)
        for parameter in actor_head_parameters
    )
    optimizer.zero_grad(set_to_none=True)
    (plan.immediate_baseline_loss + plan.successor_baseline_loss).backward()
    for parameter, gradient in zip(actor_parameters, plan.composition.gradients):
        parameter.grad = gradient.clone()
    g40._optimizer_step(optimizer, actor_head_parameters)
    steps_after = tuple(
        _optimizer_step_value(optimizer, parameter)
        for parameter in actor_head_parameters
    )
    if any(after != before + 1.0 for before, after in zip(steps_before, steps_after)):
        raise RuntimeError("G42 NO_DB Adam exposure did not advance exactly once")
    return (
        float(plan.policy.detach()),
        float(plan.immediate_baseline_loss.detach()),
        float(plan.successor_baseline_loss.detach()),
    )


def _optimizer_parameter_states_equal(
    left_optimizer: torch.optim.Optimizer,
    right_optimizer: torch.optim.Optimizer,
    left_parameters: Sequence[nn.Parameter],
    right_parameters: Sequence[nn.Parameter],
) -> bool:
    for left, right in zip(left_parameters, right_parameters):
        left_state = left_optimizer.state.get(left, {})
        right_state = right_optimizer.state.get(right, {})
        if left_state.keys() != right_state.keys():
            return False
        for name in left_state:
            left_value, right_value = left_state[name], right_state[name]
            if isinstance(left_value, torch.Tensor):
                if not isinstance(right_value, torch.Tensor) or not torch.equal(
                    left_value, right_value
                ):
                    return False
            elif left_value != right_value:
                return False
    return len(left_parameters) == len(right_parameters)


def _replays_equal(
    left: g41.G41RetainedReplay, right: g41.G41RetainedReplay
) -> bool:
    return all(
        torch.equal(getattr(left, name), getattr(right, name))
        for name in (
            "log_probs",
            "entropies",
            "immediate_baselines",
            "successor_baselines",
            "hidden_after",
            "prefix_action_sums",
            "active_mask",
        )
    )


def optimize_matched_direction_attribution_update(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectory: AnchoredRosterTrajectory,
    *,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, object]:
    if int(ppo_passes) != PPO_PASSES:
        raise ValueError("G42 requires exactly two PPO passes")
    boundary = branch_boundary_audit(models, optimizers)
    if boundary.get("passed") is not True:
        raise ValueError("G42 branch boundary failed before optimizer step")
    if trajectory.rewards.numel() != MAX_CONFORMANCE_TRANSITIONS:
        raise ValueError("G42 proof batch must contain exactly 384 real transitions")
    db_model, no_db_model = models[DB_ARM], models[NO_DB_ARM]
    db_optimizer, no_db_optimizer = optimizers[DB_ARM], optimizers[NO_DB_ARM]
    credit = g41.compute_g31_credit_without_slow(
        rewards=trajectory.rewards,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=g40.terminal_mask(trajectory),
    )
    normalized = g41._normalized_g31_advantages(credit)
    rng_before = torch.random.get_rng_state().clone()
    pass_records: list[dict[str, object]] = []
    first_replays_equal = False
    for pass_index in range(PPO_PASSES):
        db_replay = g41.retained_replay(db_model, trajectory)
        no_db_replay = g41.retained_replay(no_db_model, trajectory)
        if pass_index == 0:
            first_replays_equal = _replays_equal(db_replay, no_db_replay)
            if not first_replays_equal:
                raise ValueError("G42 first paired replay differs before optimizer step")
        db_probe = _channel_gradient_probe(
            db_model, db_replay, trajectory, credit, normalized
        )
        _, db_preview_gradients = g40._actor_objective_gradients(
            g40.G31_ARM,
            db_model,
            db_replay,
            trajectory,
            normalized,
        )
        registered_norm = g40._norm_rows(db_preview_gradients)
        no_db_plan = _prepare_raw_sum_pass(
            no_db_model,
            no_db_replay,
            trajectory,
            credit,
            normalized,
            registered_gradient_norm=registered_norm,
        )
        direction_comparison = direction_unit_distance_record(
            db_preview_gradients,
            no_db_plan.composition.raw_sum_gradients,
            registered_gradient_norm=registered_norm,
        )
        db_metrics = g41._retained_actor_head_pass(
            db_model,
            db_optimizer,
            db_replay,
            trajectory,
            credit,
            normalized,
        )
        no_db_metrics = _apply_raw_sum_pass(
            no_db_model, no_db_optimizer, no_db_plan
        )
        pass_records.append(
            {
                "pass_index": pass_index,
                "db_policy_loss": db_metrics[0],
                "no_db_policy_loss": no_db_metrics[0],
                "db_immediate_baseline_loss": db_metrics[1],
                "no_db_immediate_baseline_loss": no_db_metrics[1],
                "db_successor_baseline_loss": db_metrics[2],
                "no_db_successor_baseline_loss": no_db_metrics[2],
                "db_registered_gradient_norm": registered_norm,
                "gradient_evidence": {
                    DB_ARM: db_probe.gradient_evidence,
                    NO_DB_ARM: no_db_plan.gradient_evidence,
                },
                "direction_comparison": direction_comparison,
                "no_db_composition": raw_sum_composition_record(
                    no_db_plan.composition
                ),
            }
        )
    rng_unchanged = torch.equal(rng_before, torch.random.get_rng_state())
    baseline_state_equal = g40.state_bytes(
        db_model.credit_baselines
    ) == g40.state_bytes(no_db_model.credit_baselines)
    baseline_optimizer_state_equal = _optimizer_parameter_states_equal(
        db_optimizer,
        no_db_optimizer,
        tuple(db_model.credit_baselines.parameters()),
        tuple(no_db_model.credit_baselines.parameters()),
    )
    optimizer_steps = {
        arm: min(
            _optimizer_step_value(optimizers[arm], parameter)
            for parameter in models[arm].actor_credit_parameters()
        )
        for arm in ARMS
    }
    source_trace = g40.branch_trajectory_match(trajectory, trajectory)
    passed = bool(
        first_replays_equal
        and rng_unchanged
        and baseline_state_equal
        and baseline_optimizer_state_equal
        and all(value == float(PPO_PASSES) for value in optimizer_steps.values())
        and source_trace["passed"] is True
        and raw_sum_null_dependency_audit()["passed"] is True
        and all(
            all(
                validate_registered_gradient_evidence(
                    pass_record["gradient_evidence"][arm]  # type: ignore[index]
                )
                for arm in ARMS
            )
            and pass_record["direction_comparison"]["passed"] is True  # type: ignore[index]
            for pass_record in pass_records
        )
    )
    if not passed:
        raise RuntimeError("G42 paired post-update invariant failed")
    record = {
        "algorithm_id": ALGORITHM_ID,
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g40_anchor_registry": [
            g41.accepted_g40_anchor_identity(replicate)
            for replicate in ACCEPTED_G40_ANCHOR_REPLICATES
        ],
        "arms": list(ARMS),
        "accepted_g40_anchor_replicate": int(
            boundary["accepted_g40_anchor_authority"]["replicate"]  # type: ignore[index]
        ),
        "branch_boundary": boundary,
        "first_paired_replay_equal": first_replays_equal,
        "advantage_normalization_count": 2,
        "advantage_recomputed_between_passes": False,
        "actor_head_optimizer_steps": optimizer_steps,
        "baseline_state_bytes_equal": baseline_state_equal,
        "baseline_optimizer_state_equal": baseline_optimizer_state_equal,
        "paired_source_trace_passed": source_trace["passed"],
        "torch_rng_unchanged": rng_unchanged,
        "raw_sum_null_dependency_audit": raw_sum_null_dependency_audit(),
        "pass_records": pass_records,
        "real_transitions": MAX_CONFORMANCE_TRANSITIONS,
        "K_search": 0,
        "hypothetical_transitions": 0,
        "treatment_separation_observed": any(
            pass_record["direction_comparison"][  # type: ignore[index]
                "strict_separation_observed"
            ]
            is True
            for pass_record in pass_records
        ),
        "passed": passed,
    }
    if not _update_gradient_evidence_valid(record):
        raise RuntimeError("G42 serialized gradient evidence failed validation")
    return record


def serialize_diagnostics(record: Mapping[str, object]) -> str:
    return json.dumps(dict(record), sort_keys=True, separators=(",", ":"))


def build_final_checkpoint(
    arm: str,
    model: g41.G41NoSlowProjection,
    update_record: Mapping[str, object],
    conclusion_evidence: Mapping[str, object],
    *,
    formal: bool,
) -> dict[str, object]:
    if arm not in ARMS or update_record.get("passed") is not True:
        raise ValueError("G42 final checkpoint requires one valid registered arm")
    if not _update_gradient_evidence_valid(update_record):
        raise ValueError("G42 final checkpoint requires valid group gradients")
    if (
        not isinstance(formal, bool)
        or conclusion_evidence.get("formal") is not formal
        or not validate_conclusion_evidence(conclusion_evidence)
    ):
        raise ValueError(
            "G42 final checkpoint requires non-collinear treatment evidence"
        )
    if hasattr(model, "slow_critic") or model.phase != "credit_branch":
        raise ValueError("G42 final checkpoint requires the no-slow branch")
    authority = model.accepted_g40_anchor_authority
    if authority != g41.accepted_g40_anchor_authority(authority.replicate):
        raise ValueError("G42 final checkpoint lost accepted anchor authority")
    state = {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }
    if any("slow_critic" in name for name in state):
        raise ValueError("G42 final checkpoint contains standalone slow state")
    direction_mode = (
        "registered_g31_direction_balanced"
        if arm == DB_ARM
        else "scale_matched_raw_sum_no_db"
    )
    return {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(
            authority.replicate
        ),
        "arm": arm,
        "direction_mode": direction_mode,
        "checkpoint_kind": "FINAL_ONLY_NO_SLOW_DIRECTION_ATTRIBUTION",
        "formal": formal,
        "actor_head_optimizer_steps": PPO_PASSES,
        "standalone_slow_present": False,
        "model_state": state,
        "model_state_digest": g41._state_digest(state),
        "diagnostics": {
            "passed": True,
            "real_transitions": update_record["real_transitions"],
            "K_search": update_record["K_search"],
            "hypothetical_transitions": update_record[
                "hypothetical_transitions"
            ],
            "treatment_separation": dict(conclusion_evidence),
        },
    }
