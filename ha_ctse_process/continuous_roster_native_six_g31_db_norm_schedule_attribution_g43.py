"""Exact G31 DB-derived norm schedule versus a fixed equal-mean null."""

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
    continuous_roster_native_six_g31_direction_balance_attribution_g42 as g42,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory


ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43"
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
DBNORM_ARM = "NATIVE6_G31_DBNORM_NO_SLOW"
MEAN_ARM = "NATIVE6_G31_MEAN_NO_SLOW"
ARMS = (DBNORM_ARM, MEAN_ARM)
ACCEPTED_G40_ANCHOR_REPLICATES = (0, 1, 2)
PPO_PASSES = g41.PPO_PASSES
MAX_CONFORMANCE_TRANSITIONS = g41.MAX_CONFORMANCE_TRANSITIONS
GRADIENT_LIVE_TOLERANCE = g40.GRADIENT_LIVE_TOLERANCE
SCALE_MATCH_ATOL = 1e-8
SCALE_MATCH_RTOL = 1e-6
ACTIVATION_TOLERANCE = 1e-6
MEAN_LITERAL_COEFFICIENT = 0.5


class G43GradientGateError(ValueError):
    """A frozen pre-step gradient or schedule gate failed."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object]) -> None:
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics)
        super().__init__(f"G43 gradient gate failed before optimizer step: {reason}")

    def to_record(self) -> dict[str, object]:
        return {
            "passed": False,
            "stage": "before_either_arm_optimizer_step",
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
            "fallback_channel_count": 0,
            "per_group_scale_count": 0,
        }


@dataclass(frozen=True)
class EqualMeanComposition:
    gradients: tuple[torch.Tensor, ...]
    raw_sum_gradients: tuple[torch.Tensor, ...]
    immediate_norm: float
    successor_norm: float
    raw_sum_norm: float
    applied_gradient_norm: float
    literal_coefficient: float


@dataclass(frozen=True)
class _ChannelGradientProbe:
    policy: torch.Tensor
    immediate_baseline_loss: torch.Tensor
    successor_baseline_loss: torch.Tensor
    immediate_actor_gradients: tuple[torch.Tensor, ...]
    successor_actor_gradients: tuple[torch.Tensor, ...]
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
        return g42._gradient_rows(rows, parameters)
    except g42.G42GradientGateError as error:
        raise G43GradientGateError(error.reason, error.diagnostics) from error


def _global_norm(rows: Sequence[torch.Tensor]) -> float:
    return g42._global_norm(rows)


def _rows_bitwise_equal(
    left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]
) -> bool:
    return len(left) == len(right) and all(
        torch.equal(left_row, right_row)
        for left_row, right_row in zip(left, right)
    )


def compose_equal_mean_gradients(
    immediate: Sequence[torch.Tensor | None],
    successor: Sequence[torch.Tensor | None],
    parameters: Sequence[nn.Parameter],
) -> EqualMeanComposition:
    """Construct exactly ``0.5 * (g_I + g_S)`` in fixed parameter order."""

    immediate_rows = _gradient_rows(immediate, parameters)
    successor_rows = _gradient_rows(successor, parameters)
    raw_sum = tuple(
        left.to(torch.float64) + right.to(torch.float64)
        for left, right in zip(immediate_rows, successor_rows)
    )
    gradients = tuple(
        (MEAN_LITERAL_COEFFICIENT * row).to(parameter.dtype)
        for row, parameter in zip(raw_sum, parameters)
    )
    expected = tuple(
        (torch.tensor(0.5, dtype=torch.float64) * row).to(parameter.dtype)
        for row, parameter in zip(raw_sum, parameters)
    )
    if not _rows_bitwise_equal(gradients, expected):
        raise G43GradientGateError("equal_mean_fixed_order_mismatch", {})
    if any(not bool(torch.isfinite(row).all()) for row in gradients):
        raise G43GradientGateError("equal_mean_nonfinite", {})
    return EqualMeanComposition(
        gradients=gradients,
        raw_sum_gradients=raw_sum,
        immediate_norm=_global_norm(immediate_rows),
        successor_norm=_global_norm(successor_rows),
        raw_sum_norm=_global_norm(raw_sum),
        applied_gradient_norm=_global_norm(gradients),
        literal_coefficient=MEAN_LITERAL_COEFFICIENT,
    )


def mean_dependency_audit() -> dict[str, object]:
    """Reconstruct that MEAN has no direction-balanced schedule dependency."""

    functions = (compose_equal_mean_gradients, _gradient_rows, _global_norm)
    reads_by_function = {
        function.__name__: tuple(
            str(instruction.argval)
            for instruction in dis.get_instructions(function)
            if instruction.opname in {"LOAD_GLOBAL", "LOAD_ATTR", "LOAD_METHOD"}
        )
        for function in functions
    }
    forbidden_markers = (
        "direction_balanced",
        "db_direction",
        "registered_gradient_norm",
        "scale_matched",
    )
    forbidden = tuple(
        f"{function_name}:{name}"
        for function_name, reads in reads_by_function.items()
        for name in reads
        if any(marker in name.lower() for marker in forbidden_markers)
    )
    signature = tuple(inspect.signature(compose_equal_mean_gradients).parameters)
    passed = bool(
        signature == ("immediate", "successor", "parameters")
        and not forbidden
        and MEAN_LITERAL_COEFFICIENT == 0.5
    )
    return {
        "audited_functions": tuple(function.__name__ for function in functions),
        "bytecode_reads": reads_by_function,
        "input_signature": signature,
        "literal_coefficient": MEAN_LITERAL_COEFFICIENT,
        "coefficient_trainable": False,
        "coefficient_configurable": False,
        "search_count": 0,
        "DB_vector_read_count": 0,
        "DB_norm_read_count": 0,
        "DB_composer_call_count": 0,
        "shadow_DB_state_count": 0,
        "fallback_channel_count": 0,
        "per_group_scale_count": 0,
        "forbidden_schedule_reads": forbidden,
        "passed": passed,
    }


def equal_mean_composition_record(
    composition: EqualMeanComposition,
) -> dict[str, object]:
    dependency = mean_dependency_audit()
    return {
        "mode": "fixed_order_equal_mean_raw_sum",
        "immediate_norm": composition.immediate_norm,
        "successor_norm": composition.successor_norm,
        "raw_sum_norm": composition.raw_sum_norm,
        "equal_mean_norm": composition.applied_gradient_norm,
        "literal_coefficient": composition.literal_coefficient,
        "bitwise_fixed_order_construction": True,
        "actor_gradients_exact_zero": all(
            bool(torch.count_nonzero(row) == 0) for row in composition.gradients
        ),
        **{
            name: dependency[name]
            for name in (
                "coefficient_trainable",
                "coefficient_configurable",
                "search_count",
                "DB_vector_read_count",
                "DB_norm_read_count",
                "DB_composer_call_count",
                "shadow_DB_state_count",
                "fallback_channel_count",
                "per_group_scale_count",
            )
        },
        "passed": dependency["passed"] is True,
    }


def _dbnorm_composition(
    immediate: Sequence[torch.Tensor | None],
    successor: Sequence[torch.Tensor | None],
    parameters: Sequence[nn.Parameter],
    *,
    db_norm: float,
) -> g42.ScaleMatchedRawSumComposition:
    try:
        return g42.compose_scale_matched_raw_sum_gradients(
            immediate,
            successor,
            parameters,
            registered_gradient_norm=db_norm,
        )
    except g42.G42GradientGateError as error:
        raise G43GradientGateError(error.reason, error.diagnostics) from error


def dbnorm_composition_record(
    composition: g42.ScaleMatchedRawSumComposition,
) -> dict[str, object]:
    return {
        "mode": "db_derived_global_norm_raw_sum_direction",
        "db_norm": composition.registered_gradient_norm,
        "raw_sum_norm": composition.raw_sum_norm,
        "applied_gradient_norm": composition.applied_gradient_norm,
        "dbnorm_scale": composition.scale_factor,
        "scale_match_error": composition.scale_match_error,
        "scale_match_tolerance": composition.scale_match_tolerance,
        "zero_db_norm": composition.registered_norm_zero,
        "zero_raw_sum": composition.raw_sum_norm == 0.0,
        "actor_gradients_exact_zero": all(
            bool(torch.count_nonzero(row) == 0) for row in composition.gradients
        ),
        "DB_vector_serialized": False,
        "fallback_channel_count": 0,
        "per_group_scale_count": 0,
        "passed": True,
    }


def treatment_schedule_record(
    *,
    dbnorm: g42.ScaleMatchedRawSumComposition,
    reference_equal_mean: EqualMeanComposition,
) -> dict[str, object]:
    db_norm = float(dbnorm.registered_gradient_norm)
    raw_sum_norm = float(dbnorm.raw_sum_norm)
    mean_norm = float(reference_equal_mean.applied_gradient_norm)
    values = (db_norm, raw_sum_norm, mean_norm, float(dbnorm.scale_factor))
    if any(not np.isfinite(value) or value < 0.0 for value in values):
        raise G43GradientGateError("schedule_scalar_nonfinite_or_negative", {})
    if reference_equal_mean.raw_sum_norm != raw_sum_norm:
        raise G43GradientGateError(
            "reference_equal_mean_raw_sum_mismatch",
            {
                "dbnorm_raw_sum_norm": raw_sum_norm,
                "reference_equal_mean_raw_sum_norm": (
                    reference_equal_mean.raw_sum_norm
                ),
            },
        )
    denominator = max(db_norm, mean_norm)
    if denominator > 0.0:
        q = abs(db_norm - mean_norm) / denominator
        q_state = "defined_positive_denominator"
        q_counting = True
    else:
        q = 0.0
        q_state = "both_zero_noncounting_zero_step"
        q_counting = False
    record = {
        "db_norm": db_norm,
        "raw_sum_norm": raw_sum_norm,
        "equal_mean_norm": mean_norm,
        "dbnorm_scale": float(dbnorm.scale_factor),
        "q": q,
        "q_state": q_state,
        "q_counting": q_counting,
        "zero_db_norm": db_norm == 0.0,
        "zero_raw_sum": raw_sum_norm == 0.0,
        "evidence_source_arm": DBNORM_ARM,
        "reference_equal_mean_counterfactual": True,
        "null_arm_evidence_read_count": 0,
        "activation_threshold": ACTIVATION_TOLERANCE,
        "strict_activation_observed": bool(q_counting and q > ACTIVATION_TOLERANCE),
        "passed": True,
    }
    if not validate_treatment_schedule_record(record):
        raise G43GradientGateError("treatment_schedule_record_invalid", record)
    return record


def validate_treatment_schedule_record(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    names = ("db_norm", "raw_sum_norm", "equal_mean_norm", "dbnorm_scale", "q")
    if any(
        isinstance(value.get(name), bool)
        or not isinstance(value.get(name), (int, float))
        or not np.isfinite(float(value[name]))
        or float(value[name]) < 0.0
        for name in names
    ):
        return False
    db_norm = float(value["db_norm"])
    mean_norm = float(value["equal_mean_norm"])
    denominator = max(db_norm, mean_norm)
    expected_q = abs(db_norm - mean_norm) / denominator if denominator > 0.0 else 0.0
    expected_counting = denominator > 0.0
    return bool(
        float(value["q"]) == expected_q
        and value.get("q_counting") is expected_counting
        and value.get("q_state")
        == (
            "defined_positive_denominator"
            if expected_counting
            else "both_zero_noncounting_zero_step"
        )
        and value.get("zero_db_norm") is (db_norm == 0.0)
        and value.get("zero_raw_sum") is (float(value["raw_sum_norm"]) == 0.0)
        and value.get("evidence_source_arm") == DBNORM_ARM
        and value.get("reference_equal_mean_counterfactual") is True
        and value.get("null_arm_evidence_read_count") == 0
        and value.get("activation_threshold") == ACTIVATION_TOLERANCE
        and value.get("strict_activation_observed")
        is bool(expected_counting and expected_q > ACTIVATION_TOLERANCE)
    )


def registered_gradient_evidence(
    model: g41.G41NoSlowProjection,
    immediate_actor_gradients: Sequence[torch.Tensor | None],
    successor_actor_gradients: Sequence[torch.Tensor | None],
    immediate_baseline_gradients: Sequence[torch.Tensor | None],
    successor_baseline_gradients: Sequence[torch.Tensor | None],
) -> dict[str, object]:
    try:
        return g42.registered_gradient_evidence(
            model,
            immediate_actor_gradients,
            successor_actor_gradients,
            immediate_baseline_gradients,
            successor_baseline_gradients,
        )
    except g42.G42GradientGateError as error:
        raise G43GradientGateError(error.reason, error.diagnostics) from error


validate_registered_gradient_evidence = g42.validate_registered_gradient_evidence


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
    evidence = registered_gradient_evidence(
        model,
        immediate_actor,
        successor_actor,
        immediate_baseline,
        successor_baseline,
    )
    if not validate_registered_gradient_evidence(evidence):
        raise G43GradientGateError("registered_gradient_evidence_failed", evidence)
    return _ChannelGradientProbe(
        policy=0.5 * (immediate + successor),
        immediate_baseline_loss=immediate_baseline_loss,
        successor_baseline_loss=successor_baseline_loss,
        immediate_actor_gradients=immediate_actor,
        successor_actor_gradients=successor_actor,
        immediate_baseline_gradients=immediate_baseline,
        successor_baseline_gradients=successor_baseline,
        gradient_evidence=evidence,
    )


def project_g43_arms(
    anchor: g40.G40NativeSixPolicy, *, accepted_anchor_replicate: int
) -> dict[str, g41.G41NoSlowProjection]:
    if accepted_anchor_replicate not in ACCEPTED_G40_ANCHOR_REPLICATES:
        raise ValueError("G43 requires accepted G40 anchor replicate 0, 1, or 2")
    rng_before = torch.random.get_rng_state().clone()
    g42_models = g42.project_g42_arms(
        anchor, accepted_anchor_replicate=accepted_anchor_replicate
    )
    models = {
        DBNORM_ARM: g42_models[g42.DB_ARM],
        MEAN_ARM: g42_models[g42.NO_DB_ARM],
    }
    if g40.state_bytes(models[DBNORM_ARM]) != g40.state_bytes(models[MEAN_ARM]):
        raise RuntimeError("G43 branch states differ before treatment")
    if g40.shared_tensor_storage_count((anchor, *models.values())) != 0:
        raise RuntimeError("G43 branch projection shares retained storage")
    if any(hasattr(model, "slow_critic") for model in models.values()):
        raise RuntimeError("G43 reintroduced the standalone slow critic")
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise RuntimeError("G43 projection advanced model RNG")
    return models


def _optimizer_owns_actor_head(
    optimizer: torch.optim.Optimizer, model: g41.G41NoSlowProjection
) -> bool:
    return g42._optimizer_owns_actor_head(optimizer, model)


def branch_boundary_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS:
        return {"passed": False, "inventory_valid": False}
    remapped_models = {
        g42.DB_ARM: models[DBNORM_ARM],
        g42.NO_DB_ARM: models[MEAN_ARM],
    }
    remapped_optimizers = {
        g42.DB_ARM: optimizers[DBNORM_ARM],
        g42.NO_DB_ARM: optimizers[MEAN_ARM],
    }
    base = g42.branch_boundary_audit(remapped_models, remapped_optimizers)
    provenance_valid = bool(
        ACCEPTED_G40_SOURCE_COMMIT == g41.ACCEPTED_G40_SOURCE_COMMIT
        and ACCEPTED_G41_SOURCE_COMMIT == g42.ACCEPTED_G41_SOURCE_COMMIT
        and len(ACCEPTED_G42_REFERENCE_SOURCE_COMMIT) == 40
        and len(ACCEPTED_G42_ALIGNED_SOURCE_COMMIT) == 40
        and len(ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT) == 40
    )
    return {
        **base,
        "arms": list(ARMS),
        "accepted_g40_source_commit": ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g42_reference_source_commit": (
            ACCEPTED_G42_REFERENCE_SOURCE_COMMIT
        ),
        "accepted_g42_aligned_source_commit": ACCEPTED_G42_ALIGNED_SOURCE_COMMIT,
        "accepted_g42_alignment_stage_commit": ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT,
        "provenance_valid": provenance_valid,
        "passed": bool(base.get("passed") is True and provenance_valid),
    }


def _optimizer_step_value(
    optimizer: torch.optim.Optimizer, parameter: nn.Parameter
) -> float:
    return g42._optimizer_step_value(optimizer, parameter)


def _optimizer_parameter_states_equal(
    left_optimizer: torch.optim.Optimizer,
    right_optimizer: torch.optim.Optimizer,
    left_parameters: Sequence[nn.Parameter],
    right_parameters: Sequence[nn.Parameter],
) -> bool:
    return g42._optimizer_parameter_states_equal(
        left_optimizer, right_optimizer, left_parameters, right_parameters
    )


def _direct_treatment_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    probes: Mapping[str, _ChannelGradientProbe],
) -> dict[str, object]:
    left_model, right_model = models[DBNORM_ARM], models[MEAN_ARM]
    left_probe, right_probe = probes[DBNORM_ARM], probes[MEAN_ARM]
    trajectory = g40.branch_trajectory_match(
        trajectories[DBNORM_ARM], trajectories[MEAN_ARM]
    )
    actor_equal = g40.state_bytes(left_model.policy) == g40.state_bytes(
        right_model.policy
    )
    log_std_equal = torch.equal(left_model.log_std, right_model.log_std)
    baseline_equal = g40.state_bytes(
        left_model.credit_baselines
    ) == g40.state_bytes(right_model.credit_baselines)
    channel_equal = {
        "immediate": _rows_bitwise_equal(
            left_probe.immediate_actor_gradients,
            right_probe.immediate_actor_gradients,
        ),
        "successor": _rows_bitwise_equal(
            left_probe.successor_actor_gradients,
            right_probe.successor_actor_gradients,
        ),
    }
    baseline_gradient_equal = {
        "immediate": _rows_bitwise_equal(
            left_probe.immediate_baseline_gradients,
            right_probe.immediate_baseline_gradients,
        ),
        "successor": _rows_bitwise_equal(
            left_probe.successor_baseline_gradients,
            right_probe.successor_baseline_gradients,
        ),
    }
    optimizers_empty = all(optimizer.state == {} for optimizer in optimizers.values())
    passed = bool(
        trajectory["passed"] is True
        and actor_equal
        and log_std_equal
        and baseline_equal
        and all(channel_equal.values())
        and all(baseline_gradient_equal.values())
        and optimizers_empty
    )
    return {
        "trajectory_bitwise_equal": trajectory["passed"],
        "actor_bytes_equal": actor_equal,
        "log_std_bitwise_equal": log_std_equal,
        "shared_baseline_bytes_equal": baseline_equal,
        "channel_actor_gradients_bitwise_equal": channel_equal,
        "baseline_output_gradients_bitwise_equal": baseline_gradient_equal,
        "optimizer_states_empty": optimizers_empty,
        "non_collinearity_detected": not all(channel_equal.values()),
        "passed": passed,
    }


def order_swap_guard(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    plans: Mapping[str, _PassPlan],
) -> dict[str, object]:
    inventory_valid = tuple(models) == ARMS and tuple(optimizers) == ARMS and tuple(plans) == ARMS
    storage_disjoint = bool(
        inventory_valid
        and g40.shared_tensor_storage_count(tuple(models.values())) == 0
        and id(optimizers[DBNORM_ARM].state) != id(optimizers[MEAN_ARM].state)
    )
    gradient_storage_disjoint = bool(
        inventory_valid
        and not {
            row.untyped_storage().data_ptr()
            for row in plans[DBNORM_ARM].gradients
        }.intersection(
            row.untyped_storage().data_ptr() for row in plans[MEAN_ARM].gradients
        )
    )
    passed = bool(inventory_valid and storage_disjoint and gradient_storage_disjoint)
    return {
        "guard_kind": "precomputed_plan_disjoint_storage_commutativity",
        "plans_materialized_before_either_optimizer": inventory_valid,
        "registered_order": list(ARMS),
        "swapped_order": list(reversed(ARMS)),
        "model_optimizer_storage_disjoint": storage_disjoint,
        "assigned_gradient_storage_disjoint": gradient_storage_disjoint,
        "diagnostic_optimizer_steps": 0,
        "passed": passed,
    }


def _apply_pass(
    arm: str,
    model: g41.G41NoSlowProjection,
    optimizer: torch.optim.Optimizer,
    plan: _PassPlan,
) -> tuple[float, float, float]:
    if arm not in ARMS or not isinstance(optimizer, torch.optim.Adam):
        raise ValueError("G43 optimizer arm/type mismatch")
    if not _optimizer_owns_actor_head(optimizer, model):
        raise ValueError("G43 optimizer parameter inventory mismatch")
    actor_parameters = model.full_actor_parameters()
    actor_head_parameters = model.actor_credit_parameters()
    steps_before = tuple(
        _optimizer_step_value(optimizer, parameter)
        for parameter in actor_head_parameters
    )
    optimizer.zero_grad(set_to_none=True)
    (plan.immediate_baseline_loss + plan.successor_baseline_loss).backward()
    for parameter, gradient in zip(actor_parameters, plan.gradients):
        parameter.grad = gradient.clone()
    if any(parameter.grad is None for parameter in actor_head_parameters):
        raise G43GradientGateError("stale_or_missing_gradient", {"arm": arm})
    g40._optimizer_step(optimizer, actor_head_parameters)
    steps_after = tuple(
        _optimizer_step_value(optimizer, parameter)
        for parameter in actor_head_parameters
    )
    if any(after != before + 1.0 for before, after in zip(steps_before, steps_after)):
        raise RuntimeError("G43 Adam exposure did not advance exactly once")
    return (
        float(plan.policy.detach()),
        float(plan.immediate_baseline_loss.detach()),
        float(plan.successor_baseline_loss.detach()),
    )


def _continuation_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    *,
    update_index: int,
) -> dict[str, object]:
    if update_index == 0:
        return branch_boundary_audit(models, optimizers)
    expected = float(update_index * PPO_PASSES)
    inventory_valid = tuple(models) == ARMS and tuple(optimizers) == ARMS
    authority_valid = bool(
        inventory_valid
        and all(
            model.accepted_g40_anchor_authority
            == g41.accepted_g40_anchor_authority(
                model.accepted_g40_anchor_authority.replicate
            )
            for model in models.values()
        )
    )
    step_valid = bool(
        inventory_valid
        and all(
            all(
                _optimizer_step_value(optimizers[arm], parameter) == expected
                for parameter in models[arm].actor_credit_parameters()
            )
            for arm in ARMS
        )
    )
    passed = bool(
        inventory_valid
        and authority_valid
        and step_valid
        and all(not hasattr(model, "slow_critic") for model in models.values())
        and all(model.phase == "credit_branch" for model in models.values())
    )
    return {
        "inventory_valid": inventory_valid,
        "continuation": True,
        "update_index": update_index,
        "accepted_g40_anchor_authority": (
            g41.accepted_g40_anchor_identity(
                models[DBNORM_ARM].accepted_g40_anchor_authority.replicate
            )
            if authority_valid
            else None
        ),
        "authority_valid": authority_valid,
        "optimizer_expected_step_before": expected,
        "optimizer_step_state_valid": step_valid,
        "passed": passed,
    }


def _prepare_passes(
    models: Mapping[str, g41.G41NoSlowProjection],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    credits: Mapping[str, g41.G41Credit],
    normalized: Mapping[str, tuple[torch.Tensor, torch.Tensor]],
) -> tuple[dict[str, _PassPlan], dict[str, _ChannelGradientProbe], dict[str, object]]:
    replays = {
        arm: g41.retained_replay(models[arm], trajectories[arm]) for arm in ARMS
    }
    probes = {
        arm: _channel_gradient_probe(
            models[arm], replays[arm], trajectories[arm], credits[arm], normalized[arm]
        )
        for arm in ARMS
    }
    _, db_gradients = g40._actor_objective_gradients(
        g40.G31_ARM,
        models[DBNORM_ARM],
        replays[DBNORM_ARM],
        trajectories[DBNORM_ARM],
        normalized[DBNORM_ARM],
    )
    db_norm = g40._norm_rows(db_gradients)
    dbnorm = _dbnorm_composition(
        probes[DBNORM_ARM].immediate_actor_gradients,
        probes[DBNORM_ARM].successor_actor_gradients,
        models[DBNORM_ARM].full_actor_parameters(),
        db_norm=db_norm,
    )
    mean = compose_equal_mean_gradients(
        probes[MEAN_ARM].immediate_actor_gradients,
        probes[MEAN_ARM].successor_actor_gradients,
        models[MEAN_ARM].full_actor_parameters(),
    )
    reference_equal_mean = compose_equal_mean_gradients(
        probes[DBNORM_ARM].immediate_actor_gradients,
        probes[DBNORM_ARM].successor_actor_gradients,
        models[DBNORM_ARM].full_actor_parameters(),
    )
    plans = {
        DBNORM_ARM: _PassPlan(
            policy=probes[DBNORM_ARM].policy,
            immediate_baseline_loss=probes[DBNORM_ARM].immediate_baseline_loss,
            successor_baseline_loss=probes[DBNORM_ARM].successor_baseline_loss,
            gradients=dbnorm.gradients,
            gradient_evidence=probes[DBNORM_ARM].gradient_evidence,
            composition_record=dbnorm_composition_record(dbnorm),
        ),
        MEAN_ARM: _PassPlan(
            policy=probes[MEAN_ARM].policy,
            immediate_baseline_loss=probes[MEAN_ARM].immediate_baseline_loss,
            successor_baseline_loss=probes[MEAN_ARM].successor_baseline_loss,
            gradients=mean.gradients,
            gradient_evidence=probes[MEAN_ARM].gradient_evidence,
            composition_record=equal_mean_composition_record(mean),
        ),
    }
    return plans, probes, treatment_schedule_record(
        dbnorm=dbnorm,
        reference_equal_mean=reference_equal_mean,
    )


def optimize_norm_schedule_update(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory] | AnchoredRosterTrajectory,
    *,
    update_index: int = 0,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, object]:
    if int(ppo_passes) != PPO_PASSES:
        raise ValueError("G43 requires exactly two PPO passes")
    if isinstance(update_index, bool) or not isinstance(update_index, int) or update_index < 0:
        raise ValueError("G43 update index must be a nonnegative integer")
    trajectory_map = (
        {arm: trajectories for arm in ARMS}
        if isinstance(trajectories, AnchoredRosterTrajectory)
        else dict(trajectories)
    )
    if tuple(trajectory_map) != ARMS or any(
        trajectory.rewards.numel() != MAX_CONFORMANCE_TRANSITIONS
        for trajectory in trajectory_map.values()
    ):
        raise ValueError("G43 update requires paired 8x48 real trajectories")
    boundary = _continuation_audit(models, optimizers, update_index=update_index)
    if boundary.get("passed") is not True:
        raise ValueError("G43 branch boundary failed before optimizer step")
    credits = {
        arm: g41.compute_g31_credit_without_slow(
            rewards=trajectory.rewards,
            immediate_baselines=trajectory.old_immediate_baselines,
            successor_baselines=trajectory.old_successor_baselines,
            terminals=g40.terminal_mask(trajectory),
        )
        for arm, trajectory in trajectory_map.items()
    }
    normalized = {
        arm: g41._normalized_g31_advantages(credit)
        for arm, credit in credits.items()
    }
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
        plans, probes, schedule = _prepare_passes(
            models, trajectory_map, credits, normalized
        )
        if update_index == 0 and pass_index == 0:
            direct_audit = _direct_treatment_audit(
                models, optimizers, trajectory_map, probes
            )
            if direct_audit.get("passed") is not True:
                raise G43GradientGateError(
                    "first_paired_direct_treatment_mismatch", direct_audit
                )
            swap_guard = order_swap_guard(models, optimizers, plans)
            if swap_guard.get("passed") is not True:
                raise G43GradientGateError("order_swap_guard_failed", swap_guard)
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
                "treatment_schedule": schedule,
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
    exposure_valid = all(
        steps_after[arm] == steps_before[arm] + PPO_PASSES for arm in ARMS
    )
    record: dict[str, object] = {
        "algorithm_id": ALGORITHM_ID,
        "accepted_g40_source_commit": ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g42_reference_source_commit": ACCEPTED_G42_REFERENCE_SOURCE_COMMIT,
        "accepted_g42_aligned_source_commit": ACCEPTED_G42_ALIGNED_SOURCE_COMMIT,
        "accepted_g42_alignment_stage_commit": ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT,
        "accepted_g40_anchor_replicate": models[
            DBNORM_ARM
        ].accepted_g40_anchor_authority.replicate,
        "branch_boundary": boundary,
        "update_index": update_index,
        "arms": list(ARMS),
        "branch_update_order": list(ARMS),
        "paired_collection_before_update": True,
        "advantage_normalization_count": 2,
        "advantage_recomputed_between_passes": False,
        "actor_head_optimizer_steps_before": steps_before,
        "actor_head_optimizer_steps": steps_after,
        "actor_head_optimizer_step_delta": PPO_PASSES,
        "baseline_update_rule_equal": True,
        "baseline_optimizer_exposure_equal": (
            steps_after[DBNORM_ARM] == steps_after[MEAN_ARM]
        ),
        "first_paired_direct_treatment_audit": direct_audit,
        "order_swap_guard": swap_guard,
        "mean_dependency_audit": mean_dependency_audit(),
        "pass_records": pass_records,
        "torch_rng_unchanged": torch.equal(
            rng_before, torch.random.get_rng_state()
        ),
        "real_transitions": len(ARMS) * MAX_CONFORMANCE_TRANSITIONS,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "passed": False,
    }
    record["passed"] = bool(
        exposure_valid
        and record["torch_rng_unchanged"] is True
        and record["mean_dependency_audit"]["passed"] is True  # type: ignore[index]
        and all(
            all(
                validate_registered_gradient_evidence(
                    pass_record["gradient_evidence"][arm]  # type: ignore[index]
                )
                for arm in ARMS
            )
            and validate_treatment_schedule_record(
                pass_record["treatment_schedule"]  # type: ignore[index]
            )
            for pass_record in pass_records
        )
    )
    if not _update_evidence_valid(record):
        raise RuntimeError("G43 serialized update evidence failed validation")
    return record


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
        or value.get("advantage_normalization_count") != 2
        or value.get("advantage_recomputed_between_passes") is not False
        or value.get("actor_head_optimizer_step_delta") != PPO_PASSES
        or value.get("K_search") != 0
        or value.get("hypothetical_trajectory_count") != 0
        or value.get("hypothetical_transitions") != 0
        or value.get("nested_rollout") is not False
        or value.get("replanning") is not False
        or value.get("torch_rng_unchanged") is not True
    ):
        return False
    dependency = value.get("mean_dependency_audit")
    if not isinstance(dependency, Mapping) or dependency.get("passed") is not True:
        return False
    records = value.get("pass_records")
    if not isinstance(records, list) or len(records) != PPO_PASSES:
        return False
    for pass_index, record in enumerate(records):
        if (
            not isinstance(record, Mapping)
            or record.get("pass_index") != pass_index
            or record.get("plans_materialized_before_either_optimizer") is not True
            or record.get("branch_update_order") != list(ARMS)
        ):
            return False
        evidence = record.get("gradient_evidence")
        composition = record.get("composition")
        if (
            not isinstance(evidence, Mapping)
            or tuple(evidence) != ARMS
            or any(
                not validate_registered_gradient_evidence(evidence.get(arm))
                for arm in ARMS
            )
            or not isinstance(composition, Mapping)
            or tuple(composition) != ARMS
            or composition[DBNORM_ARM].get("mode")
            != "db_derived_global_norm_raw_sum_direction"
            or composition[MEAN_ARM].get("mode")
            != "fixed_order_equal_mean_raw_sum"
            or composition[MEAN_ARM].get("DB_vector_read_count") != 0
            or composition[MEAN_ARM].get("DB_norm_read_count") != 0
            or not validate_treatment_schedule_record(
                record.get("treatment_schedule")
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
        raise ValueError("G43 conclusion evidence requires records and bool scope")
    q_by_replicate: dict[int, list[float]] = {}
    counting_by_replicate: dict[int, list[bool]] = {}
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
        q_by_replicate.setdefault(replicate, [])
        counting_by_replicate.setdefault(replicate, [])
        for pass_record in record["pass_records"]:  # type: ignore[index]
            schedule = pass_record["treatment_schedule"]
            denominator = max(
                float(schedule["db_norm"]),
                float(schedule["equal_mean_norm"]),
            )
            reconstructed = (
                abs(
                    float(schedule["db_norm"])
                    - float(schedule["equal_mean_norm"])
                )
                / denominator
                if denominator > 0.0
                else 0.0
            )
            if float(schedule["q"]) != reconstructed:
                records_valid = False
            q_by_replicate[replicate].append(reconstructed)
            counting_by_replicate[replicate].append(denominator > 0.0)
    required = (
        list(ACCEPTED_G40_ANCHOR_REPLICATES)
        if formal
        else sorted(q_by_replicate)
    )
    rows = [
        {
            "replicate": replicate,
            "reconstructed_q": q_by_replicate.get(replicate, []),
            "q_counting": counting_by_replicate.get(replicate, []),
            "strict_activation_observed": any(
                counting and q > ACTIVATION_TOLERANCE
                for q, counting in zip(
                    q_by_replicate.get(replicate, []),
                    counting_by_replicate.get(replicate, []),
                )
            ),
        }
        for replicate in required
    ]
    scope_valid = (
        set(q_by_replicate) == set(ACCEPTED_G40_ANCHOR_REPLICATES)
        if formal
        else len(q_by_replicate) == 1
    )
    return {
        "formal": formal,
        "required_replicates": required,
        "activation_threshold": ACTIVATION_TOLERANCE,
        "strictly_greater_required": True,
        "reconstructed_from_all_update_records": True,
        "records_valid": records_valid,
        "replicate_rows": rows,
        "passed": bool(
            records_valid
            and scope_valid
            and rows
            and all(row["strict_activation_observed"] for row in rows)
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
        or value.get("strictly_greater_required") is not True
        or value.get("reconstructed_from_all_update_records") is not True
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
        q_values = row.get("reconstructed_q")
        counting = row.get("q_counting")
        if (
            isinstance(replicate, bool)
            or not isinstance(replicate, int)
            or replicate not in ACCEPTED_G40_ANCHOR_REPLICATES
            or not isinstance(q_values, list)
            or not isinstance(counting, list)
            or not q_values
            or len(q_values) != len(counting)
            or any(
                isinstance(q, bool)
                or not isinstance(q, (int, float))
                or not np.isfinite(float(q))
                or float(q) < 0.0
                for q in q_values
            )
            or any(not isinstance(flag, bool) for flag in counting)
        ):
            return False
        activated = any(
            flag and float(q) > ACTIVATION_TOLERANCE
            for q, flag in zip(q_values, counting)
        )
        if row.get("strict_activation_observed") is not activated:
            return False
        observed.append(replicate)
    return bool(
        observed == required
        and value.get("passed") is True
        and all(row["strict_activation_observed"] for row in rows)
    )


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
    if arm not in ARMS or not _update_evidence_valid(update_record):
        raise ValueError("G43 final checkpoint requires a valid registered arm/update")
    if (
        not isinstance(formal, bool)
        or conclusion_evidence.get("formal") is not formal
        or not validate_conclusion_evidence(conclusion_evidence)
    ):
        raise ValueError("G43 final checkpoint requires active norm-schedule evidence")
    if hasattr(model, "slow_critic") or model.phase != "credit_branch":
        raise ValueError("G43 final checkpoint requires the no-slow branch")
    authority = model.accepted_g40_anchor_authority
    if authority != g41.accepted_g40_anchor_authority(authority.replicate):
        raise ValueError("G43 final checkpoint lost accepted anchor authority")
    state = {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }
    if any("slow_critic" in name for name in state):
        raise ValueError("G43 final checkpoint contains standalone slow state")
    return {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "accepted_g40_source_commit": ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g42_reference_source_commit": ACCEPTED_G42_REFERENCE_SOURCE_COMMIT,
        "accepted_g42_aligned_source_commit": ACCEPTED_G42_ALIGNED_SOURCE_COMMIT,
        "accepted_g42_alignment_stage_commit": ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT,
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(
            authority.replicate
        ),
        "arm": arm,
        "gradient_schedule": (
            "db_derived_global_norm_raw_sum_direction"
            if arm == DBNORM_ARM
            else "fixed_literal_half_raw_sum"
        ),
        "checkpoint_kind": "FINAL_ONLY_NO_SLOW_DB_NORM_ATTRIBUTION",
        "formal": formal,
        "actor_head_optimizer_steps": PPO_PASSES,
        "standalone_slow_present": False,
        "model_state": state,
        "model_state_digest": g41._state_digest(state),
        "diagnostics": {
            "passed": True,
            "real_transitions": update_record["real_transitions"],
            "K_search": 0,
            "hypothetical_transitions": 0,
            "treatment_activation": dict(conclusion_evidence),
        },
    }
