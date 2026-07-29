"""Frozen G48 realized-successor channel attribution on the G47 actor-only route."""

from __future__ import annotations

import copy
import dis
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import nn

from ha_ctse_process import (
    continuous_roster_native_six_credit_reduction_g40 as g40,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44
    as g44,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47 as g47,
)
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory


g41 = g47.g41

ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48"
)
SOURCE_ID = f"{ALGORITHM_ID}_P0"
DESIGN_STAGE_COMMIT = "35a924424f842699dd275949626ef568aee08a22"
DESIGN_SOURCE_COMMIT = "9d5416d69051365e9da35e496949fabd8e9a1493"
DESIGN_DISPOSITION = "IDENTIFIABLE_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48"

ACCEPTED_G47_FORMAL_SOURCE_COMMIT = (
    "23939a16f9a6035fda91506f6e76ff742bf23b73"
)
ACCEPTED_G47_ALIGNED_IMPLEMENTATION_COMMIT = (
    "fab68ae1a87578b59c1a004ac5415edf55ee7452"
)
ACCEPTED_G47_ALIGNMENT_STAGE_COMMIT = (
    "33432c16df22e5432710a5e5b05aa34a82c5a45f"
)
ACCEPTED_G47_FORMAL_BRANCH = "SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G47"

ACCEPTED_G40_SOURCE_COMMIT = g47.g46.ACCEPTED_G40_SOURCE_COMMIT
ACCEPTED_G41_SOURCE_COMMIT = g47.g46.ACCEPTED_G41_SOURCE_COMMIT
ACCEPTED_G42_REFERENCE_SOURCE_COMMIT = g47.g46.g45.g44.ACCEPTED_G42_REFERENCE_SOURCE_COMMIT
ACCEPTED_G42_ALIGNED_SOURCE_COMMIT = g47.g46.g45.g44.ACCEPTED_G42_ALIGNED_SOURCE_COMMIT
ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT = g47.g46.g45.g44.ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT
ACCEPTED_G40_ANCHOR_REPLICATES = g47.ACCEPTED_G40_ANCHOR_REPLICATES

REFERENCE_ARM = "NATIVE6_G31_IMMEDIATE_REALIZED_SUCCESSOR"
NULL_ARM = "NATIVE6_G31_DUPLICATED_IMMEDIATE"
ARMS = (REFERENCE_ARM, NULL_ARM)

# Compatibility names used only by the isolated accepted orchestration backend.
DBNORM_ARM = REFERENCE_ARM
MEAN_ARM = NULL_ARM

PPO_PASSES = 2
NUM_ENVS = 8
HORIZON = 48
MAX_CONFORMANCE_TRANSITIONS = NUM_ENVS * HORIZON
NORMALIZATION_ROWS = MAX_CONFORMANCE_TRANSITIONS
NORMALIZATION_MASK_DIGEST = g44.NORMALIZATION_MASK_DIGEST
K_SEARCH = 0
EQUAL_MEAN_COEFFICIENT = 0.5
ACTIVATION_TOLERANCE = 1e-6
GRADIENT_LIVE_TOLERANCE = 1e-12


class G48InvariantError(ValueError):
    """A frozen G48 predicate failed before the affected optimizer step."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object]) -> None:
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics)
        super().__init__(f"G48 invariant failed before optimizer step: {self.reason}")

    def __reduce__(
        self,
    ) -> tuple[type[G48InvariantError], tuple[str, dict[str, object]]]:
        return type(self), (self.reason, dict(self.diagnostics))

    def to_record(self) -> dict[str, object]:
        return {
            "passed": False,
            "stage": "before_either_arm_optimizer_step",
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
        }


@dataclass(frozen=True)
class ChannelPackage:
    channel_1: torch.Tensor
    channel_2: torch.Tensor
    target_route: str
    channel_ids: tuple[str, str]
    realized_successor_read_count: int


@dataclass(frozen=True)
class GradientProbe:
    channel_1_gradients: tuple[torch.Tensor, ...]
    channel_2_gradients: tuple[torch.Tensor, ...]
    entropy_gradients: tuple[torch.Tensor, ...]
    credit_gradients: tuple[torch.Tensor, ...]
    assigned_gradients: tuple[torch.Tensor, ...]
    gradient_evidence: dict[str, object]


G48Model = g47.G47NoBaselineProjection


def _tensor_digest(value: torch.Tensor) -> str:
    return g47._tensor_digest(value)


def _gradient_rows(
    rows: Sequence[torch.Tensor | None], parameters: Sequence[nn.Parameter]
) -> tuple[torch.Tensor, ...]:
    try:
        return g47._gradient_rows(rows, parameters)
    except g47.G47InvariantError as error:
        raise G48InvariantError(error.reason, error.diagnostics) from error


def _global_norm(rows: Sequence[torch.Tensor]) -> float:
    return g47._global_norm(rows)


def _rows_bitwise_equal(
    left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]
) -> bool:
    return g47._rows_bitwise_equal(left, right)


def _flatten_float64(rows: Sequence[torch.Tensor]) -> torch.Tensor:
    if not rows:
        return torch.zeros(0, dtype=torch.float64)
    return torch.cat(tuple(row.detach().to(torch.float64).reshape(-1) for row in rows))


def _gradient_digest(rows: Sequence[torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        value = row.detach().cpu().contiguous()
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(json.dumps(list(value.shape), separators=(",", ":")).encode("ascii"))
        digest.update(value.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _actor_state(model: G48Model) -> dict[str, torch.Tensor]:
    return g47._actor_state(model)


def _state_equal(
    left: Mapping[str, torch.Tensor], right: Mapping[str, torch.Tensor]
) -> bool:
    return g47._state_equal(left, right)


def _optimizer_owns_actor_head(
    optimizer: torch.optim.Optimizer, model: G48Model
) -> bool:
    names = g47._optimizer_parameter_names(optimizer, model)
    return names == g47.actor_parameter_names(model)


def _optimizer_step_value(
    optimizer: torch.optim.Optimizer, parameter: nn.Parameter
) -> float:
    return g47.g46._optimizer_step_value(optimizer, parameter)


def project_g48_arms(
    anchor: g40.G40NativeSixPolicy, *, accepted_anchor_replicate: int
) -> dict[str, G48Model]:
    """Clone only the accepted G47 no-baseline actor into both G48 arms."""

    if accepted_anchor_replicate not in ACCEPTED_G40_ANCHOR_REPLICATES:
        raise ValueError("G48 requires accepted G40 anchor replicate 0, 1, or 2")
    rng_before = torch.random.get_rng_state().clone()
    predecessor = g47.project_g47_arms(
        anchor, accepted_anchor_replicate=accepted_anchor_replicate
    )[g47.REDUCED_ARM]
    reference = copy.deepcopy(predecessor)
    null = copy.deepcopy(predecessor)
    models = {REFERENCE_ARM: reference, NULL_ARM: null}
    if not _state_equal(_actor_state(reference), _actor_state(null)):
        raise RuntimeError("G48 branch-start actor bytes differ")
    if any(
        hasattr(model, "credit_baselines") or hasattr(model, "baseline_values")
        for model in models.values()
    ):
        raise RuntimeError("G48 projection reintroduced a baseline module")
    if g40.shared_tensor_storage_count((anchor, *models.values())) != 0:
        raise RuntimeError("G48 projection shares parameter or buffer storage")
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise RuntimeError("G48 projection consumed model RNG")
    return models


# Accepted generic runner interface.
project_g43_arms = project_g48_arms


def make_g48_optimizers(
    models: Mapping[str, G48Model],
) -> dict[str, torch.optim.Adam]:
    if tuple(models) != ARMS:
        raise ValueError("G48 optimizer construction requires exact arms")
    optimizers = {
        arm: g41.make_actor_head_optimizer(models[arm]) for arm in ARMS
    }
    if any(not _optimizer_owns_actor_head(optimizers[arm], models[arm]) for arm in ARMS):
        raise G48InvariantError("actor_optimizer_inventory_invalid", {})
    if any(bool(optimizer.state) for optimizer in optimizers.values()):
        raise G48InvariantError("actor_optimizer_not_empty_at_branch_start", {})
    return optimizers


def _storage_alias_count(models: Mapping[str, G48Model]) -> int:
    storages: set[int] = set()
    aliases = 0
    for model in models.values():
        for value in model.state_dict().values():
            pointer = int(value.untyped_storage().data_ptr())
            if pointer in storages:
                aliases += 1
            storages.add(pointer)
    return aliases


def branch_boundary_audit(
    models: Mapping[str, G48Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    exact = tuple(models) == ARMS and tuple(optimizers) == ARMS
    states = {arm: _actor_state(models[arm]) for arm in ARMS} if exact else {}
    names = {
        arm: g47.actor_parameter_names(models[arm]) for arm in ARMS
    } if exact else {}
    optimizer_names = {
        arm: g47._optimizer_parameter_names(optimizers[arm], models[arm])
        for arm in ARMS
    } if exact else {}
    passed = bool(
        exact
        and all(isinstance(models[arm], G48Model) for arm in ARMS)
        and all(models[arm].phase == "credit_branch" for arm in ARMS)
        and _state_equal(states[REFERENCE_ARM], states[NULL_ARM])
        and names[REFERENCE_ARM] == names[NULL_ARM]
        and all(optimizer_names[arm] == names[arm] for arm in ARMS)
        and all(not optimizers[arm].state for arm in ARMS)
        and _storage_alias_count(models) == 0
        and all(
            not hasattr(models[arm], "credit_baselines")
            and not hasattr(models[arm], "baseline_values")
            for arm in ARMS
        )
    )
    return {
        "arms": list(ARMS),
        "branch_start_actor_bytes_equal": bool(
            exact and _state_equal(states[REFERENCE_ARM], states[NULL_ARM])
        ),
        "branch_start_log_std_bytes_equal": bool(
            exact and torch.equal(models[REFERENCE_ARM].log_std, models[NULL_ARM].log_std)
        ),
        "actor_parameter_order_equal": bool(
            exact and names[REFERENCE_ARM] == names[NULL_ARM]
        ),
        "actor_Adam_states_empty": bool(
            exact and all(not optimizers[arm].state for arm in ARMS)
        ),
        "shared_parameter_buffer_storage_count": (
            _storage_alias_count(models) if exact else -1
        ),
        "baseline_parameter_count": (
            sum(
                1
                for model in models.values()
                for name, _ in model.named_parameters()
                if name.startswith("credit_baselines.")
            )
            if exact
            else -1
        ),
        "passed": passed,
    }


def _continuation_audit(
    models: Mapping[str, G48Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    *,
    update_index: int,
) -> dict[str, object]:
    expected = float(update_index * PPO_PASSES)
    step_values = {
        arm: tuple(
            _optimizer_step_value(optimizers[arm], parameter)
            for parameter in models[arm].full_actor_parameters()
        )
        for arm in ARMS
    }
    passed = bool(
        tuple(models) == ARMS
        and tuple(optimizers) == ARMS
        and all(models[arm].phase == "credit_branch" for arm in ARMS)
        and all(all(value == expected for value in step_values[arm]) for arm in ARMS)
        and _storage_alias_count(models) == 0
        and all(_optimizer_owns_actor_head(optimizers[arm], models[arm]) for arm in ARMS)
    )
    return {
        "update_index": int(update_index),
        "expected_actor_Adam_step": expected,
        "actor_Adam_steps": {arm: list(values) for arm, values in step_values.items()},
        "shared_parameter_buffer_storage_count": _storage_alias_count(models),
        "passed": passed,
    }


def reference_channel_package(trajectory: AnchoredRosterTrajectory) -> ChannelPackage:
    """Read rewards and the realized return tail exactly once for the reference arm."""

    credit = g47.g46.g45._no_read_credit(trajectory)
    return ChannelPackage(
        channel_1=credit.immediate_advantage.detach().clone(),
        channel_2=credit.successor_advantage.detach().clone(),
        target_route="immediate_reward|realized_successor_G_next",
        channel_ids=("immediate", "realized_successor"),
        realized_successor_read_count=1,
    )


def duplicated_immediate_channel_package(rewards: torch.Tensor) -> ChannelPackage:
    """Construct the null from rewards only; no trajectory-tail object is accepted."""

    if tuple(rewards.shape) != (HORIZON, NUM_ENVS):
        raise G48InvariantError("null_reward_row_inventory_invalid", {"shape": tuple(rewards.shape)})
    if not bool(torch.isfinite(rewards).all()):
        raise G48InvariantError("null_reward_nonfinite", {})
    first = rewards.detach().clone()
    second = rewards.detach().clone()
    if first.data_ptr() == second.data_ptr() or not torch.equal(first, second):
        raise G48InvariantError("duplicate_immediate_materialization_invalid", {})
    return ChannelPackage(
        channel_1=first,
        channel_2=second,
        target_route="duplicated_immediate_reward_only",
        channel_ids=("immediate_1", "immediate_2"),
        realized_successor_read_count=0,
    )


def _normalize_package(package: ChannelPackage) -> g44.ChannelNormalization:
    placeholder = g41.G41Credit(
        returns=package.channel_1,
        successor_targets=package.channel_2,
        immediate_advantage=package.channel_1,
        successor_advantage=package.channel_2,
    )
    try:
        return g44.normalize_credit_channels(placeholder)
    except g44.G44GradientGateError as error:
        raise G48InvariantError(error.reason, error.diagnostics) from error


def _normalization_record(
    package: ChannelPackage, normalization: g44.ChannelNormalization
) -> dict[str, object]:
    return {
        "target_route": package.target_route,
        "channel_ids": list(package.channel_ids),
        "channel_1_mean": normalization.immediate_mean,
        "channel_2_mean": normalization.successor_mean,
        "channel_1_centered_sum_square": normalization.immediate_centered_sum_square,
        "channel_2_centered_sum_square": normalization.successor_centered_sum_square,
        "channel_1_scale": normalization.immediate_scale,
        "channel_2_scale": normalization.successor_scale,
        "channel_1_normalized_digest": _tensor_digest(normalization.independent_immediate),
        "channel_2_normalized_digest": _tensor_digest(normalization.independent_successor),
        "normalization_row_count": normalization.normalization_row_count,
        "normalization_mask_digest": normalization.normalization_mask_digest,
        "realized_successor_read_count": package.realized_successor_read_count,
        "duplicate_channel_bytes_equal": bool(
            package.channel_ids == ("immediate_1", "immediate_2")
            and torch.equal(
                normalization.independent_immediate,
                normalization.independent_successor,
            )
        ),
    }


def validate_normalization_record(value: object, arm: str) -> bool:
    if not isinstance(value, Mapping) or arm not in ARMS:
        return False
    expected_ids = (
        ["immediate", "realized_successor"]
        if arm == REFERENCE_ARM
        else ["immediate_1", "immediate_2"]
    )
    expected_route = (
        "immediate_reward|realized_successor_G_next"
        if arm == REFERENCE_ARM
        else "duplicated_immediate_reward_only"
    )
    try:
        sum_1 = torch.as_tensor(value["channel_1_centered_sum_square"], dtype=torch.float64)
        sum_2 = torch.as_tensor(value["channel_2_centered_sum_square"], dtype=torch.float64)
        scale_1 = float(torch.sqrt(sum_1 / float(NORMALIZATION_ROWS)))
        scale_2 = float(torch.sqrt(sum_2 / float(NORMALIZATION_ROWS)))
        finite = all(
            np.isfinite(float(value[name]))
            for name in (
                "channel_1_mean",
                "channel_2_mean",
                "channel_1_centered_sum_square",
                "channel_2_centered_sum_square",
                "channel_1_scale",
                "channel_2_scale",
            )
        )
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        finite
        and value.get("target_route") == expected_route
        and value.get("channel_ids") == expected_ids
        and value.get("channel_1_scale") == scale_1
        and value.get("channel_2_scale") == scale_2
        and value.get("normalization_row_count") == NORMALIZATION_ROWS
        and value.get("normalization_mask_digest") == NORMALIZATION_MASK_DIGEST
        and isinstance(value.get("channel_1_normalized_digest"), str)
        and isinstance(value.get("channel_2_normalized_digest"), str)
        and value.get("realized_successor_read_count")
        == (1 if arm == REFERENCE_ARM else 0)
        and (
            arm == REFERENCE_ARM
            or (
                value.get("duplicate_channel_bytes_equal") is True
                and value.get("channel_1_mean") == value.get("channel_2_mean")
                and value.get("channel_1_centered_sum_square")
                == value.get("channel_2_centered_sum_square")
                and value.get("channel_1_scale") == value.get("channel_2_scale")
                and value.get("channel_1_normalized_digest")
                == value.get("channel_2_normalized_digest")
            )
        )
    )


def _row_evidence(rows: Sequence[torch.Tensor]) -> dict[str, object]:
    finite = all(bool(torch.isfinite(row).all()) for row in rows)
    norm = _global_norm(rows) if finite else float("nan")
    return {
        "gradient_norm": norm,
        "finite": bool(finite and np.isfinite(norm)),
        "live": bool(finite and np.isfinite(norm) and norm > GRADIENT_LIVE_TOLERANCE),
    }


def _gradient_evidence(
    model: G48Model,
    channel_1: Sequence[torch.Tensor],
    channel_2: Sequence[torch.Tensor],
    *,
    require_group_liveness: bool,
) -> dict[str, object]:
    parameters = model.full_actor_parameters()
    groups = g40._actor_groups(model)
    if tuple(groups) != g40.REGISTERED_ACTOR_GROUPS:
        raise G48InvariantError("registered_actor_group_inventory_mismatch", {})
    indexes = {id(parameter): index for index, parameter in enumerate(parameters)}
    rows = {"channel_1": tuple(channel_1), "channel_2": tuple(channel_2)}
    group_rows = {
        channel: {
            group: _row_evidence(
                tuple(values[indexes[id(parameter)]] for parameter in group_parameters)
            )
            for group, group_parameters in groups.items()
        }
        for channel, values in rows.items()
    }
    global_rows = {name: _row_evidence(values) for name, values in rows.items()}
    finite = all(
        group_rows[channel][group]["finite"] is True
        for channel in group_rows
        for group in g40.REGISTERED_ACTOR_GROUPS
    ) and all(value["finite"] is True for value in global_rows.values())
    group_live = all(
        any(group_rows[channel][group]["live"] is True for channel in group_rows)
        for group in g40.REGISTERED_ACTOR_GROUPS
    )
    return {
        "registered_actor_groups": list(g40.REGISTERED_ACTOR_GROUPS),
        "actor_channels": group_rows,
        "actor_channel_global": global_rows,
        "group_liveness_required": require_group_liveness,
        "all_group_gradients_finite": finite,
        "every_group_live_in_at_least_one_channel": group_live,
        "passed": bool(finite and (group_live or not require_group_liveness)),
    }


def _probe(
    model: G48Model,
    trajectory: g47.G47ActorTrajectory,
    normalized: tuple[torch.Tensor, torch.Tensor],
    *,
    require_group_liveness: bool,
) -> GradientProbe:
    replay = g47.actor_only_replay(model, trajectory)
    parameters = model.full_actor_parameters()
    loss_1 = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized[0]
    )
    loss_2 = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized[1]
    )
    entropy_objective = -g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
    row_1 = _gradient_rows(
        torch.autograd.grad(loss_1, parameters, retain_graph=True, allow_unused=True),
        parameters,
    )
    row_2 = _gradient_rows(
        torch.autograd.grad(loss_2, parameters, retain_graph=True, allow_unused=True),
        parameters,
    )
    entropy = _gradient_rows(
        torch.autograd.grad(
            entropy_objective, parameters, retain_graph=True, allow_unused=True
        ),
        parameters,
    )
    credit = g47.g46._equal_mean(row_1, row_2, parameters)
    assigned = g47.g46._add_entropy(credit, entropy)
    evidence = _gradient_evidence(
        model,
        row_1,
        row_2,
        require_group_liveness=require_group_liveness,
    )
    if evidence["passed"] is not True:
        raise G48InvariantError("actor_gradient_liveness_invalid", evidence)
    return GradientProbe(
        channel_1_gradients=row_1,
        channel_2_gradients=row_2,
        entropy_gradients=entropy,
        credit_gradients=credit,
        assigned_gradients=assigned,
        gradient_evidence=evidence,
    )


def _activation_scalars(
    normalized_immediate: torch.Tensor,
    normalized_successor: torch.Tensor,
    reference_credit: Sequence[torch.Tensor],
    null_counterfactual: Sequence[torch.Tensor],
) -> dict[str, object]:
    target_difference = (
        normalized_successor.detach().to(torch.float64)
        - normalized_immediate.detach().to(torch.float64)
    )
    target_difference_sum_square = float(target_difference.square().sum())
    q_target = float(
        torch.sqrt(
            torch.as_tensor(target_difference_sum_square, dtype=torch.float64)
            / float(NORMALIZATION_ROWS)
        )
    )
    reference = _flatten_float64(reference_credit)
    null = _flatten_float64(null_counterfactual)
    if reference.shape != null.shape:
        raise G48InvariantError("activation_credit_inventory_mismatch", {})
    if not bool(torch.isfinite(reference).all() and torch.isfinite(null).all()):
        raise G48InvariantError("activation_credit_nonfinite", {})
    reference_norm_square = float(reference.square().sum())
    null_norm_square = float(null.square().sum())
    difference = reference - null
    difference_sum_square = float(difference.square().sum())
    reference_norm = math.sqrt(reference_norm_square)
    null_norm = math.sqrt(null_norm_square)
    difference_norm = math.sqrt(difference_sum_square)
    denominator = max(reference_norm, null_norm)
    q_credit = 0.0 if denominator == 0.0 else difference_norm / denominator
    direction_distance: float | None = None
    if reference_norm > 0.0 and null_norm > 0.0:
        direction_distance = float(
            torch.linalg.vector_norm(
                reference / reference_norm - null / null_norm
            )
        )
    scalars = (
        target_difference_sum_square,
        q_target,
        reference_norm_square,
        null_norm_square,
        difference_sum_square,
        q_credit,
    )
    if any(not np.isfinite(value) or value < 0.0 for value in scalars):
        raise G48InvariantError("activation_scalar_nonfinite", {})
    return {
        "target_difference_sum_square": target_difference_sum_square,
        "normalization_row_count": NORMALIZATION_ROWS,
        "q_target": q_target,
        "reference_credit_norm_square": reference_norm_square,
        "null_counterfactual_credit_norm_square": null_norm_square,
        "reference_credit_norm": reference_norm,
        "null_counterfactual_credit_norm": null_norm,
        "full_credit_vector_difference_sum_square": difference_sum_square,
        "full_credit_vector_difference_norm": difference_norm,
        "q_credit": q_credit,
        "unit_direction_distance_descriptive": direction_distance,
        "treatment_active": bool(
            q_target > ACTIVATION_TOLERANCE and q_credit > ACTIVATION_TOLERANCE
        ),
    }


def activation_record(
    normalization: g44.ChannelNormalization,
    reference_probe: GradientProbe,
) -> dict[str, object]:
    null_counterfactual = tuple(
        row.detach().clone() for row in reference_probe.channel_1_gradients
    )
    record = {
        **_activation_scalars(
            normalization.independent_immediate,
            normalization.independent_successor,
            reference_probe.credit_gradients,
            null_counterfactual,
        ),
        "evidence_source_arm": REFERENCE_ARM,
        "reference_evidence_source": True,
        "reference_null_counterfactual": "0.5*(g_I+g_I)",
        "actual_null_evidence_read_count": 0,
        "activation_tolerance": ACTIVATION_TOLERANCE,
        "direction_distance_conclusion_gate": False,
    }
    if not validate_activation_record(record):
        raise G48InvariantError("activation_record_invalid", record)
    return record


def validate_activation_record(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    try:
        target_sum = float(value["target_difference_sum_square"])
        row_count = int(value["normalization_row_count"])
        reference_square = float(value["reference_credit_norm_square"])
        null_square = float(value["null_counterfactual_credit_norm_square"])
        difference_square = float(value["full_credit_vector_difference_sum_square"])
        reference_norm = math.sqrt(reference_square)
        null_norm = math.sqrt(null_square)
        difference_norm = math.sqrt(difference_square)
        expected_q_target = float(
            torch.sqrt(
                torch.as_tensor(target_sum, dtype=torch.float64) / float(row_count)
            )
        )
        denominator = max(reference_norm, null_norm)
        expected_q_credit = 0.0 if denominator == 0.0 else difference_norm / denominator
        expected_active = bool(
            expected_q_target > ACTIVATION_TOLERANCE
            and expected_q_credit > ACTIVATION_TOLERANCE
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False
    scalar_values = (target_sum, reference_square, null_square, difference_square)
    return bool(
        row_count == NORMALIZATION_ROWS
        and all(np.isfinite(row) and row >= 0.0 for row in scalar_values)
        and value.get("q_target") == expected_q_target
        and value.get("q_credit") == expected_q_credit
        and value.get("reference_credit_norm") == reference_norm
        and value.get("null_counterfactual_credit_norm") == null_norm
        and value.get("full_credit_vector_difference_norm") == difference_norm
        and value.get("treatment_active") is expected_active
        and value.get("evidence_source_arm") == REFERENCE_ARM
        and value.get("reference_evidence_source") is True
        and value.get("reference_null_counterfactual") == "0.5*(g_I+g_I)"
        and value.get("actual_null_evidence_read_count") == 0
        and value.get("activation_tolerance") == ACTIVATION_TOLERANCE
        and value.get("direction_distance_conclusion_gate") is False
    )


def _apply_actor_pass(
    model: G48Model,
    optimizer: torch.optim.Optimizer,
    assigned: Sequence[torch.Tensor],
) -> None:
    parameters = model.full_actor_parameters()
    before = tuple(_optimizer_step_value(optimizer, row) for row in parameters)
    optimizer.zero_grad(set_to_none=True)
    for parameter, gradient in zip(parameters, assigned):
        parameter.grad = gradient.detach().clone()
    if any(parameter.grad is None or not bool(torch.isfinite(parameter.grad).all()) for parameter in parameters):
        raise G48InvariantError("stale_missing_or_nonfinite_actor_gradient", {})
    g40._optimizer_step(optimizer, parameters)
    after = tuple(_optimizer_step_value(optimizer, row) for row in parameters)
    if any(current != prior + 1.0 for prior, current in zip(before, after)):
        raise G48InvariantError("actor_Adam_exposure_mismatch", {})


def _prepared_packages(
    trajectories: Mapping[str, AnchoredRosterTrajectory],
) -> tuple[
    dict[str, ChannelPackage],
    dict[str, g44.ChannelNormalization],
    dict[str, g47.G47ActorTrajectory],
]:
    packages = {
        REFERENCE_ARM: reference_channel_package(trajectories[REFERENCE_ARM]),
        NULL_ARM: duplicated_immediate_channel_package(
            trajectories[NULL_ARM].rewards
        ),
    }
    normalizations = {arm: _normalize_package(packages[arm]) for arm in ARMS}
    actor_trajectories = {
        arm: g47._actor_only_trajectory_view(trajectories[arm]) for arm in ARMS
    }
    null_record = _normalization_record(
        packages[NULL_ARM], normalizations[NULL_ARM]
    )
    if not validate_normalization_record(null_record, NULL_ARM):
        raise G48InvariantError("null_duplicate_normalization_invalid", null_record)
    return packages, normalizations, actor_trajectories


def order_swap_guard(
    models: Mapping[str, G48Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
) -> dict[str, object]:
    state_before = {arm: g47._state_digest(_actor_state(models[arm])) for arm in ARMS}
    optimizer_before = {
        arm: g47._optimizer_state_digest(
            g47._optimizer_state_by_name(optimizers[arm], models[arm])
        )
        for arm in ARMS
    }
    rng_before = torch.random.get_rng_state().clone()
    _, normalizations, actor_trajectories = _prepared_packages(trajectories)

    def probe_digest(arm: str) -> str:
        row = normalizations[arm]
        probe = _probe(
            models[arm],
            actor_trajectories[arm],
            (row.independent_immediate, row.independent_successor),
            require_group_liveness=arm == REFERENCE_ARM,
        )
        return _gradient_digest(probe.assigned_gradients)

    forward = {arm: probe_digest(arm) for arm in ARMS}
    reverse = {arm: probe_digest(arm) for arm in reversed(ARMS)}
    state_after = {arm: g47._state_digest(_actor_state(models[arm])) for arm in ARMS}
    optimizer_after = {
        arm: g47._optimizer_state_digest(
            g47._optimizer_state_by_name(optimizers[arm], models[arm])
        )
        for arm in ARMS
    }
    passed = bool(
        forward == reverse
        and state_before == state_after
        and optimizer_before == optimizer_after
        and torch.equal(rng_before, torch.random.get_rng_state())
    )
    return {
        "forward_order": list(ARMS),
        "reverse_order": list(reversed(ARMS)),
        "assigned_gradient_digests": forward,
        "mate_input_state_unchanged": state_before == state_after,
        "optimizer_state_unchanged": optimizer_before == optimizer_after,
        "torch_RNG_unchanged": torch.equal(rng_before, torch.random.get_rng_state()),
        "diagnostic_optimizer_steps": 0,
        "passed": passed,
    }


def _null_zero_read_certificate() -> dict[str, object]:
    reads = tuple(
        instruction.argval
        for instruction in dis.get_instructions(duplicated_immediate_channel_package)
        if instruction.opname in {"LOAD_ATTR", "LOAD_METHOD", "LOAD_GLOBAL"}
    )
    forbidden = tuple(
        name for name in reads if isinstance(name, str) and "successor" in name.lower()
    )
    return {
        "realized_successor_read_into_null_target": 0,
        "realized_successor_read_into_null_normalization": 0,
        "realized_successor_read_into_null_actor_loss": 0,
        "realized_successor_read_into_null_gradient_scale": 0,
        "realized_successor_read_into_null_checkpoint_selection": 0,
        "realized_successor_read_into_null_evaluation": 0,
        "realized_successor_read_into_null_result_selection": 0,
        "successor_counterfactual_calls": 0,
        "null_builder_forbidden_bytecode_reads": list(forbidden),
        "passed": not forbidden,
    }


def reconstruct_static_certificate(
    models: Mapping[str, G48Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    boundary = branch_boundary_audit(models, optimizers)
    zero_reads = _null_zero_read_certificate()
    return {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "accepted_g47_formal_source_commit": ACCEPTED_G47_FORMAL_SOURCE_COMMIT,
        "accepted_g47_aligned_implementation_commit": ACCEPTED_G47_ALIGNED_IMPLEMENTATION_COMMIT,
        "accepted_g47_alignment_stage_commit": ACCEPTED_G47_ALIGNMENT_STAGE_COMMIT,
        "accepted_g47_formal_branch": ACCEPTED_G47_FORMAL_BRANCH,
        "arms": list(ARMS),
        "branch_boundary": boundary,
        "null_zero_reads": zero_reads,
        "baseline_module_parameter_count": 0,
        "baseline_optimizer_state_count": 0,
        "actor_information_change": False,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "passed": bool(boundary["passed"] is True and zero_reads["passed"] is True),
    }


def validate_static_certificate(value: object) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("algorithm_id") == ALGORITHM_ID
        and value.get("source_id") == SOURCE_ID
        and value.get("accepted_g47_formal_source_commit")
        == ACCEPTED_G47_FORMAL_SOURCE_COMMIT
        and value.get("accepted_g47_aligned_implementation_commit")
        == ACCEPTED_G47_ALIGNED_IMPLEMENTATION_COMMIT
        and value.get("accepted_g47_alignment_stage_commit")
        == ACCEPTED_G47_ALIGNMENT_STAGE_COMMIT
        and value.get("accepted_g47_formal_branch") == ACCEPTED_G47_FORMAL_BRANCH
        and value.get("arms") == list(ARMS)
        and isinstance(value.get("branch_boundary"), Mapping)
        and value["branch_boundary"].get("passed") is True
        and value["branch_boundary"].get("baseline_parameter_count") == 0
        and isinstance(value.get("null_zero_reads"), Mapping)
        and value["null_zero_reads"].get("passed") is True
        and value.get("baseline_module_parameter_count") == 0
        and value.get("baseline_optimizer_state_count") == 0
        and value.get("actor_information_change") is False
        and value.get("K_search") == 0
        and value.get("hypothetical_trajectory_count") == 0
        and value.get("hypothetical_transitions") == 0
        and value.get("nested_rollout") is False
        and value.get("replanning") is False
        and value.get("passed") is True
    )


def optimize_realized_successor_channel_update(
    models: Mapping[str, G48Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    *,
    update_index: int,
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS or tuple(trajectories) != ARMS:
        raise ValueError("G48 update requires exact arm order")
    if any(row.rewards.numel() != MAX_CONFORMANCE_TRANSITIONS for row in trajectories.values()):
        raise ValueError("G48 update requires two complete stored 8x48 trajectories")
    boundary = (
        branch_boundary_audit(models, optimizers)
        if update_index == 0
        else _continuation_audit(models, optimizers, update_index=update_index)
    )
    if boundary.get("passed") is not True:
        raise G48InvariantError("branch_or_continuation_invalid", boundary)
    static = reconstruct_static_certificate(models, optimizers) if update_index == 0 else None
    if static is not None and not validate_static_certificate(static):
        raise G48InvariantError("static_certificate_invalid", static)
    swap = order_swap_guard(models, optimizers, trajectories) if update_index == 0 else None
    if swap is not None and swap.get("passed") is not True:
        raise G48InvariantError("order_swap_guard_invalid", swap)
    packages, normalizations, actor_trajectories = _prepared_packages(trajectories)
    normalization_records = {
        arm: _normalization_record(packages[arm], normalizations[arm]) for arm in ARMS
    }
    if any(not validate_normalization_record(normalization_records[arm], arm) for arm in ARMS):
        raise G48InvariantError("normalization_evidence_invalid", normalization_records)
    pass_records: list[dict[str, object]] = []
    for pass_index in range(PPO_PASSES):
        reference_probe = _probe(
            models[REFERENCE_ARM],
            actor_trajectories[REFERENCE_ARM],
            (
                normalizations[REFERENCE_ARM].independent_immediate,
                normalizations[REFERENCE_ARM].independent_successor,
            ),
            require_group_liveness=True,
        )
        null_probe = _probe(
            models[NULL_ARM],
            actor_trajectories[NULL_ARM],
            (
                normalizations[NULL_ARM].independent_immediate,
                normalizations[NULL_ARM].independent_successor,
            ),
            require_group_liveness=False,
        )
        if not _rows_bitwise_equal(
            null_probe.channel_1_gradients, null_probe.channel_2_gradients
        ):
            raise G48InvariantError("null_duplicate_channel_gradient_mismatch", {})
        activation = activation_record(
            normalizations[REFERENCE_ARM], reference_probe
        )
        combined_finite = all(
            bool(torch.isfinite(row).all())
            for row in (
                *reference_probe.credit_gradients,
                *reference_probe.channel_1_gradients,
                *null_probe.credit_gradients,
            )
        )
        if not combined_finite:
            raise G48InvariantError("combined_credit_nonfinite", {})
        reference_entropy_digest = _gradient_digest(reference_probe.entropy_gradients)
        null_entropy_digest = _gradient_digest(null_probe.entropy_gradients)
        _apply_actor_pass(
            models[REFERENCE_ARM],
            optimizers[REFERENCE_ARM],
            reference_probe.assigned_gradients,
        )
        _apply_actor_pass(
            models[NULL_ARM],
            optimizers[NULL_ARM],
            null_probe.assigned_gradients,
        )
        pass_records.append(
            {
                "pass_index": pass_index,
                "branch_update_order": list(ARMS),
                "paired_collection_before_update": True,
                "normalization_reused_across_both_PPO_passes": True,
                "normalization_by_arm": normalization_records,
                "reference_gradient_evidence": reference_probe.gradient_evidence,
                "null_gradient_evidence": null_probe.gradient_evidence,
                "reference_credit_gradient_digest": _gradient_digest(
                    reference_probe.credit_gradients
                ),
                "null_credit_gradient_digest": _gradient_digest(
                    null_probe.credit_gradients
                ),
                "null_duplicate_channel_gradient_bytes_equal": True,
                "common_entropy_added_once": True,
                "entropy_gradient_digest_by_arm": {
                    REFERENCE_ARM: reference_entropy_digest,
                    NULL_ARM: null_entropy_digest,
                },
                "activation": activation,
                "actual_null_activation_evidence_read_count": 0,
                "actor_Adam_step_completed_by_arm": {arm: True for arm in ARMS},
                "passed": True,
            }
        )
    record = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "update_index": int(update_index),
        "accepted_g40_anchor_replicate": models[
            REFERENCE_ARM
        ].accepted_g40_anchor_authority.replicate,
        "accepted_g47_formal_source_commit": ACCEPTED_G47_FORMAL_SOURCE_COMMIT,
        "accepted_g47_aligned_implementation_commit": ACCEPTED_G47_ALIGNED_IMPLEMENTATION_COMMIT,
        "accepted_g47_alignment_stage_commit": ACCEPTED_G47_ALIGNMENT_STAGE_COMMIT,
        "accepted_g47_formal_branch": ACCEPTED_G47_FORMAL_BRANCH,
        "branch_boundary_or_continuation": boundary,
        "static_certificate": static,
        "order_swap_guard": swap,
        "pass_records": pass_records,
        "paired_collection_before_update": True,
        "branch_update_order": list(ARMS),
        "actor_optimizer_steps_per_arm": PPO_PASSES,
        "baseline_parameter_count": 0,
        "baseline_optimizer_steps": 0,
        "real_transitions": 2 * MAX_CONFORMANCE_TRANSITIONS,
        "PPO_passes": PPO_PASSES,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "passed": True,
    }
    if not _update_evidence_valid(record):
        raise RuntimeError("G48 serialized update evidence failed validation")
    return record


# Accepted generic orchestration name.
optimize_norm_schedule_update = optimize_realized_successor_channel_update


def _update_evidence_valid(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    records = value.get("pass_records")
    if not isinstance(records, list) or len(records) != PPO_PASSES:
        return False
    if (
        value.get("algorithm_id") != ALGORITHM_ID
        or value.get("source_id") != SOURCE_ID
        or value.get("accepted_g47_formal_source_commit")
        != ACCEPTED_G47_FORMAL_SOURCE_COMMIT
        or value.get("accepted_g47_aligned_implementation_commit")
        != ACCEPTED_G47_ALIGNED_IMPLEMENTATION_COMMIT
        or value.get("accepted_g47_alignment_stage_commit")
        != ACCEPTED_G47_ALIGNMENT_STAGE_COMMIT
        or value.get("accepted_g47_formal_branch") != ACCEPTED_G47_FORMAL_BRANCH
        or not isinstance(value.get("branch_boundary_or_continuation"), Mapping)
        or value["branch_boundary_or_continuation"].get("passed") is not True
        or value.get("paired_collection_before_update") is not True
        or value.get("branch_update_order") != list(ARMS)
        or value.get("actor_optimizer_steps_per_arm") != PPO_PASSES
        or value.get("baseline_parameter_count") != 0
        or value.get("baseline_optimizer_steps") != 0
        or value.get("real_transitions") != 2 * MAX_CONFORMANCE_TRANSITIONS
        or value.get("PPO_passes") != PPO_PASSES
        or value.get("K_search") != 0
        or value.get("hypothetical_trajectory_count") != 0
        or value.get("hypothetical_transitions") != 0
        or value.get("nested_rollout") is not False
        or value.get("replanning") is not False
    ):
        return False
    if value.get("update_index") == 0:
        if not validate_static_certificate(value.get("static_certificate")):
            return False
        swap = value.get("order_swap_guard")
        if not isinstance(swap, Mapping) or swap.get("passed") is not True:
            return False
    elif value.get("static_certificate") is not None or value.get("order_swap_guard") is not None:
        return False
    for index, row in enumerate(records):
        if not isinstance(row, Mapping):
            return False
        normalizations = row.get("normalization_by_arm")
        entropy = row.get("entropy_gradient_digest_by_arm")
        reference_evidence = row.get("reference_gradient_evidence")
        null_evidence = row.get("null_gradient_evidence")
        if (
            row.get("pass_index") != index
            or row.get("branch_update_order") != list(ARMS)
            or row.get("paired_collection_before_update") is not True
            or row.get("normalization_reused_across_both_PPO_passes") is not True
            or not isinstance(normalizations, Mapping)
            or set(normalizations) != set(ARMS)
            or any(
                not validate_normalization_record(normalizations[arm], arm)
                for arm in ARMS
            )
            or not isinstance(reference_evidence, Mapping)
            or reference_evidence.get("passed") is not True
            or reference_evidence.get("group_liveness_required") is not True
            or not isinstance(null_evidence, Mapping)
            or null_evidence.get("passed") is not True
            or null_evidence.get("group_liveness_required") is not False
            or row.get("null_duplicate_channel_gradient_bytes_equal") is not True
            or row.get("common_entropy_added_once") is not True
            or not isinstance(entropy, Mapping)
            or set(entropy) != set(ARMS)
            or any(not isinstance(entropy[arm], str) for arm in ARMS)
            or not validate_activation_record(row.get("activation"))
            or row.get("actual_null_activation_evidence_read_count") != 0
            or row.get("actor_Adam_step_completed_by_arm")
            != {arm: True for arm in ARMS}
            or row.get("passed") is not True
        ):
            return False
    return True


def build_conclusion_evidence(
    update_records: Sequence[Mapping[str, object]], *, formal: bool
) -> dict[str, object]:
    expected_replicates = [0, 1, 2] if formal else [0]
    activations: list[dict[str, object]] = []
    for record in update_records:
        if not _update_evidence_valid(record):
            raise G48InvariantError("conclusion_update_evidence_invalid", {})
        replicate = int(record["accepted_g40_anchor_replicate"])
        for pass_record in record["pass_records"]:  # type: ignore[index]
            activations.append(
                {
                    "replicate": replicate,
                    "update_index": int(record["update_index"]),
                    "pass_index": int(pass_record["pass_index"]),
                    "activation": dict(pass_record["activation"]),
                }
            )
    counts = {
        str(replicate): sum(
            row["replicate"] == replicate
            and validate_activation_record(row["activation"])
            and row["activation"]["treatment_active"] is True
            for row in activations
        )
        for replicate in expected_replicates
    }
    record = {
        "algorithm_id": ALGORITHM_ID,
        "formal": formal,
        "expected_replicates": expected_replicates,
        "activation_source_arm": REFERENCE_ARM,
        "actual_null_evidence_read_count": 0,
        "activation_records": activations,
        "active_pass_count_by_replicate": counts,
        "activation_tolerance": ACTIVATION_TOLERANCE,
        "passed": all(counts[str(replicate)] >= 1 for replicate in expected_replicates),
    }
    return record


def validate_conclusion_evidence(value: object) -> bool:
    if not isinstance(value, Mapping) or not isinstance(value.get("formal"), bool):
        return False
    expected = [0, 1, 2] if value["formal"] else [0]
    records = value.get("activation_records")
    if not isinstance(records, list):
        return False
    counts = {str(replicate): 0 for replicate in expected}
    for row in records:
        if (
            not isinstance(row, Mapping)
            or row.get("replicate") not in expected
            or not validate_activation_record(row.get("activation"))
        ):
            return False
        if row["activation"]["treatment_active"] is True:
            counts[str(row["replicate"])] += 1
    return bool(
        value.get("algorithm_id") == ALGORITHM_ID
        and value.get("expected_replicates") == expected
        and value.get("activation_source_arm") == REFERENCE_ARM
        and value.get("actual_null_evidence_read_count") == 0
        and value.get("active_pass_count_by_replicate") == counts
        and value.get("activation_tolerance") == ACTIVATION_TOLERANCE
        and value.get("passed") is all(counts[str(replicate)] >= 1 for replicate in expected)
        and value.get("passed") is True
    )


def _target_route_certificate(arm: str) -> dict[str, object]:
    if arm == REFERENCE_ARM:
        return {
            "target_law": "x_I=r_t|x_S=G_(t+1)",
            "channel_ids": ["immediate", "realized_successor"],
            "realized_successor_actor_credit_reads": 1,
        }
    if arm == NULL_ARM:
        return {
            "target_law": "x_I1=r_t|x_I2=r_t",
            "channel_ids": ["immediate_1", "immediate_2"],
            "realized_successor_actor_credit_reads": 0,
            "successor_counterfactual_calls": 0,
            "duplicate_channel_evidence_required": True,
        }
    raise ValueError("G48 checkpoint arm is not registered")


def build_final_checkpoint(
    arm: str,
    model: G48Model,
    final_update_record: Mapping[str, object],
    conclusion_evidence: Mapping[str, object],
    *,
    formal: bool,
) -> dict[str, object]:
    if arm not in ARMS or not _update_evidence_valid(final_update_record):
        raise G48InvariantError("checkpoint_final_update_invalid", {"arm": arm})
    if not validate_conclusion_evidence(conclusion_evidence):
        raise G48InvariantError("checkpoint_conclusion_invalid", {"arm": arm})
    state = {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }
    if any(name.startswith("credit_baselines.") for name in state):
        raise G48InvariantError("checkpoint_reintroduced_baseline_module", {})
    certificate = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "arm": arm,
        "formal": formal,
        "kind": "final_only",
        "model_state": state,
        "model_state_digest": g47._state_digest(state),
        "standalone_slow_present": False,
        "baseline_module_present": False,
        "baseline_optimizer_state_count": 0,
        "actor_head_optimizer_steps": PPO_PASSES,
        "target_route_certificate": _target_route_certificate(arm),
        "final_update_evidence": dict(final_update_record),
        "conclusion_evidence": dict(conclusion_evidence),
        "diagnostics": {"treatment_activation": dict(conclusion_evidence)},
    }
    if arm == NULL_ARM and any(
        "successor" in name.lower()
        for name in certificate["model_state"]
    ):
        raise G48InvariantError("null_checkpoint_successor_schema_present", {})
    return certificate


def serialize_diagnostics(record: Mapping[str, object]) -> str:
    return json.dumps(dict(record), sort_keys=True, separators=(",", ":"))
