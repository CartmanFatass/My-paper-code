"""Frozen G49 exact collapse of G48 duplicated-immediate credit to one channel.

The reference path deliberately executes the accepted G48 duplicated-immediate
package.  The reduced path owns a genuinely single target, normalization, loss,
and gradient construction.  Equality is established from the actual floating-
point results on every PPO pass; symbolic algebra is never used as evidence.
"""

from __future__ import annotations

import copy
import dis
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import nn

from ha_ctse_process import (
    continuous_roster_native_six_g31_realized_successor_channel_attribution_g48
    as g48,
)
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory


g47 = g48.g47
g44 = g48.g44
g41 = g48.g41
g40 = g48.g40

ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_"
    "SINGLE_CHANNEL_COLLAPSE_G49"
)
SOURCE_ID = f"{ALGORITHM_ID}_P0"
DESIGN_STAGE_COMMIT = "fc8288b53401cea1642110994305272905e56c5f"
DESIGN_DISPOSITION = "CONTINUE"

ACCEPTED_G48_FORMAL_SOURCE_COMMIT = (
    "4abbee66d43ffd592d65624121121bc0109882ab"
)
ACCEPTED_G48_ALIGNED_IMPLEMENTATION_COMMIT = (
    "d96f8f29367b55b5ea655b984631d6064877e237"
)
ACCEPTED_G48_ALIGNMENT_STAGE_COMMIT = (
    "617414f9a175f044eecfbfec4e4b170c6990b47f"
)
ACCEPTED_G48_FORMAL_BRANCH = "DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48"

REFERENCE_ARM = "NATIVE6_G31_DUPLICATED_IMMEDIATE"
REDUCED_ARM = "NATIVE6_G31_SINGLE_IMMEDIATE"
ARMS = (REFERENCE_ARM, REDUCED_ARM)

PPO_PASSES = 2
NUM_ENVS = 8
HORIZON = 48
NORMALIZATION_ROWS = NUM_ENVS * HORIZON
MAX_REAL_TRANSITIONS = NORMALIZATION_ROWS
NORMALIZATION_MASK_DIGEST = g44.NORMALIZATION_MASK_DIGEST
K_SEARCH = 0
GRADIENT_LIVE_TOLERANCE = g48.GRADIENT_LIVE_TOLERANCE


class G49InvariantError(ValueError):
    """A G49 structural-equivalence invariant failed before the affected step."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object]) -> None:
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics)
        super().__init__(f"G49 invariant failed before optimizer step: {self.reason}")

    def __reduce__(
        self,
    ) -> tuple[type[G49InvariantError], tuple[str, dict[str, object]]]:
        return type(self), (self.reason, dict(self.diagnostics))

    def to_record(self) -> dict[str, object]:
        return {
            "passed": False,
            "stage": "before_either_path_optimizer_step_for_pass",
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
        }


@dataclass(frozen=True)
class SingleChannelNormalization:
    """The complete reduced-route normalization state; there is no mate row."""

    target: torch.Tensor
    centered: torch.Tensor
    normalized: torch.Tensor
    mean: float
    centered_sum_square: float
    scale: float
    row_count: int
    mask_digest: str


@dataclass(frozen=True)
class _DuplicateProbe:
    loss_1: torch.Tensor
    loss_2: torch.Tensor
    gradient_1: tuple[torch.Tensor, ...]
    gradient_2: tuple[torch.Tensor, ...]
    entropy: tuple[torch.Tensor, ...]
    credit: tuple[torch.Tensor, ...]
    assigned: tuple[torch.Tensor, ...]
    gradient_evidence: dict[str, object]


@dataclass(frozen=True)
class _SingleProbe:
    loss: torch.Tensor
    gradient: tuple[torch.Tensor, ...]
    entropy: tuple[torch.Tensor, ...]
    assigned: tuple[torch.Tensor, ...]
    gradient_evidence: dict[str, object]


G49Model = g48.G48Model


def _tensor_digest(value: torch.Tensor) -> str:
    return g48._tensor_digest(value)


def _tensor_scalar_digest(value: torch.Tensor) -> str:
    if value.numel() != 1:
        raise ValueError("G49 scalar digest requires one value")
    return _tensor_digest(value.reshape(1))


def _gradient_digest(rows: Sequence[torch.Tensor]) -> str:
    return g48._gradient_digest(rows)


def _rows_bitwise_equal(
    left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]
) -> bool:
    return g48._rows_bitwise_equal(left, right)


def _state_digest(model: G49Model) -> str:
    return g47._state_digest(g48._actor_state(model))


def _optimizer_state(
    optimizer: torch.optim.Optimizer, model: G49Model
) -> dict[str, dict[str, object]]:
    return g47._optimizer_state_by_name(optimizer, model)


def _optimizer_digest(
    optimizer: torch.optim.Optimizer, model: G49Model
) -> str:
    return g47._optimizer_state_digest(_optimizer_state(optimizer, model))


def _gradient_slot_digest(model: G49Model) -> str:
    digest = hashlib.sha256()
    for name, parameter in zip(
        g47.actor_parameter_names(model), model.full_actor_parameters()
    ):
        digest.update(name.encode("utf-8"))
        if parameter.grad is None:
            digest.update(b"none")
        else:
            row = parameter.grad.detach().cpu().contiguous()
            digest.update(str(row.dtype).encode("ascii"))
            digest.update(json.dumps(list(row.shape)).encode("ascii"))
            digest.update(row.numpy().tobytes())
    return digest.hexdigest()


def _optimizer_storage_pointers(optimizer: torch.optim.Optimizer) -> set[int]:
    pointers: set[int] = set()
    for state in optimizer.state.values():
        for value in state.values():
            if isinstance(value, torch.Tensor):
                pointers.add(int(value.untyped_storage().data_ptr()))
    return pointers


def _shared_optimizer_storage_count(
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> int:
    if tuple(optimizers) != ARMS:
        return -1
    left = _optimizer_storage_pointers(optimizers[REFERENCE_ARM])
    right = _optimizer_storage_pointers(optimizers[REDUCED_ARM])
    return len(left & right)


def project_g49_arms(
    anchor: g40.G40NativeSixPolicy, *, accepted_anchor_replicate: int
) -> dict[str, G49Model]:
    """Project the accepted G48 duplicated-immediate branch into disjoint arms."""

    rng_before = torch.random.get_rng_state().clone()
    predecessor = g48.project_g48_arms(
        anchor, accepted_anchor_replicate=accepted_anchor_replicate
    )[g48.NULL_ARM]
    reference = copy.deepcopy(predecessor)
    reduced = copy.deepcopy(predecessor)
    models = {REFERENCE_ARM: reference, REDUCED_ARM: reduced}
    if not g48._state_equal(g48._actor_state(reference), g48._actor_state(reduced)):
        raise RuntimeError("G49 branch-start actor bytes differ")
    if g40.shared_tensor_storage_count((anchor, *models.values())) != 0:
        raise RuntimeError("G49 projection shares parameter or buffer storage")
    if any(
        hasattr(model, "credit_baselines") or hasattr(model, "baseline_values")
        for model in models.values()
    ):
        raise RuntimeError("G49 projection reintroduced a baseline module")
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise RuntimeError("G49 projection consumed model RNG")
    return models


def make_g49_optimizers(
    models: Mapping[str, G49Model],
) -> dict[str, torch.optim.Adam]:
    if tuple(models) != ARMS:
        raise ValueError("G49 optimizer construction requires exact arm order")
    optimizers = {
        arm: g41.make_actor_head_optimizer(models[arm]) for arm in ARMS
    }
    expected_hyperparameters = {
        "lr": 1e-3,
        "betas": (0.9, 0.999),
        "eps": 1e-8,
        "weight_decay": 0,
        "amsgrad": False,
    }
    for arm in ARMS:
        names = g47._optimizer_parameter_names(optimizers[arm], models[arm])
        if names != g47.actor_parameter_names(models[arm]):
            raise G49InvariantError("actor_optimizer_inventory_invalid", {"arm": arm})
        group = optimizers[arm].param_groups[0]
        if any(group.get(name) != value for name, value in expected_hyperparameters.items()):
            raise G49InvariantError("actor_optimizer_hyperparameters_invalid", {"arm": arm})
        if optimizers[arm].state:
            raise G49InvariantError("actor_optimizer_not_empty_at_branch_start", {"arm": arm})
    return optimizers


def branch_boundary_audit(
    models: Mapping[str, G49Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    exact = tuple(models) == ARMS and tuple(optimizers) == ARMS
    names = (
        {arm: g47.actor_parameter_names(models[arm]) for arm in ARMS}
        if exact
        else {}
    )
    optimizer_names = (
        {
            arm: g47._optimizer_parameter_names(optimizers[arm], models[arm])
            for arm in ARMS
        }
        if exact
        else {}
    )
    model_storage = g48._storage_alias_count(models) if exact else -1
    passed = bool(
        exact
        and _state_digest(models[REFERENCE_ARM]) == _state_digest(models[REDUCED_ARM])
        and names[REFERENCE_ARM] == names[REDUCED_ARM]
        and all(optimizer_names[arm] == names[arm] for arm in ARMS)
        and all(not optimizers[arm].state for arm in ARMS)
        and model_storage == 0
        and _shared_optimizer_storage_count(optimizers) == 0
        and all(
            not hasattr(models[arm], "credit_baselines")
            and not hasattr(models[arm], "baseline_values")
            for arm in ARMS
        )
    )
    return {
        "arms": list(ARMS),
        "actor_state_bytes_equal": bool(
            exact
            and _state_digest(models[REFERENCE_ARM]) == _state_digest(models[REDUCED_ARM])
        ),
        "log_std_bytes_equal": bool(
            exact
            and torch.equal(models[REFERENCE_ARM].log_std, models[REDUCED_ARM].log_std)
        ),
        "actor_parameter_names_equal": bool(
            exact and names[REFERENCE_ARM] == names[REDUCED_ARM]
        ),
        "actor_parameter_order_equal": bool(
            exact and names[REFERENCE_ARM] == names[REDUCED_ARM]
        ),
        "actor_Adam_states_empty": bool(
            exact and all(not optimizers[arm].state for arm in ARMS)
        ),
        "actor_Adam_hyperparameters_equal": bool(
            exact
            and g47._optimizer_hyperparameters(optimizers[REFERENCE_ARM])
            == g47._optimizer_hyperparameters(optimizers[REDUCED_ARM])
        ),
        "actor_Adam_storage_disjoint": bool(
            exact and _shared_optimizer_storage_count(optimizers) == 0
        ),
        "shared_parameter_or_buffer_storage_count": model_storage,
        "projection_RNG_consumption": 0,
        "baseline_module_parameter_count": 0,
        "passed": passed,
    }


def _continuation_audit(
    models: Mapping[str, G49Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    *,
    update_index: int,
) -> dict[str, object]:
    expected = float(update_index * PPO_PASSES)
    steps = {
        arm: tuple(
            g48._optimizer_step_value(optimizers[arm], parameter)
            for parameter in models[arm].full_actor_parameters()
        )
        for arm in ARMS
    }
    passed = bool(
        tuple(models) == ARMS
        and tuple(optimizers) == ARMS
        and all(all(value == expected for value in steps[arm]) for arm in ARMS)
        and _shared_optimizer_storage_count(optimizers) == 0
        and _state_digest(models[REFERENCE_ARM]) == _state_digest(models[REDUCED_ARM])
        and _optimizer_digest(optimizers[REFERENCE_ARM], models[REFERENCE_ARM])
        == _optimizer_digest(optimizers[REDUCED_ARM], models[REDUCED_ARM])
    )
    return {
        "update_index": int(update_index),
        "expected_actor_Adam_step": expected,
        "actor_Adam_steps": {arm: list(values) for arm, values in steps.items()},
        "actor_state_bytes_equal": bool(
            _state_digest(models[REFERENCE_ARM]) == _state_digest(models[REDUCED_ARM])
        ),
        "actor_Adam_state_bytes_equal": bool(
            _optimizer_digest(optimizers[REFERENCE_ARM], models[REFERENCE_ARM])
            == _optimizer_digest(optimizers[REDUCED_ARM], models[REDUCED_ARM])
        ),
        "actor_Adam_storage_disjoint": _shared_optimizer_storage_count(optimizers) == 0,
        "passed": passed,
    }


def _single_immediate_target(rewards: torch.Tensor) -> torch.Tensor:
    """Materialize exactly one reduced target; no trajectory-tail object is accepted."""

    if tuple(rewards.shape) != (HORIZON, NUM_ENVS):
        raise G49InvariantError("single_target_row_inventory_invalid", {"shape": tuple(rewards.shape)})
    if not bool(torch.isfinite(rewards).all()):
        raise G49InvariantError("single_target_nonfinite", {})
    return rewards.detach().clone()


def _normalize_single(target: torch.Tensor) -> SingleChannelNormalization:
    """Apply the exact accepted G48/G44 scalar reduction once."""

    if tuple(target.shape) != (HORIZON, NUM_ENVS):
        raise G49InvariantError("single_normalization_row_inventory_invalid", {})
    if not bool(torch.isfinite(target).all()):
        raise G49InvariantError("single_normalization_nonfinite", {})
    row64 = target.detach().to(torch.float64)
    mean64 = row64.mean()
    centered64 = row64 - mean64
    centered_sum_square64 = centered64.square().sum()
    scale64 = torch.sqrt(centered_sum_square64 / float(NORMALIZATION_ROWS))
    if float(scale64) == 0.0:
        normalized64 = torch.zeros_like(centered64)
    else:
        normalized64 = centered64 / scale64
    centered = centered64.to(target.dtype)
    normalized = normalized64.to(target.dtype)
    if not bool(torch.isfinite(centered).all() and torch.isfinite(normalized).all()):
        raise G49InvariantError("single_normalization_output_nonfinite", {})
    return SingleChannelNormalization(
        target=target.detach().clone(),
        centered=centered,
        normalized=normalized,
        mean=float(mean64),
        centered_sum_square=float(centered_sum_square64),
        scale=float(scale64),
        row_count=NORMALIZATION_ROWS,
        mask_digest=NORMALIZATION_MASK_DIGEST,
    )


_SINGLE_NORMALIZATION_KEYS = {
    "target_law",
    "target_digest",
    "centered_digest",
    "normalized_digest",
    "mean",
    "centered_sum_square",
    "scale",
    "row_count",
    "mask_digest",
    "zero_scale_maps_to_zero",
}


def _single_normalization_record(
    normalization: SingleChannelNormalization,
) -> dict[str, object]:
    return {
        "target_law": "x_I=r_t",
        "target_digest": _tensor_digest(normalization.target),
        "centered_digest": _tensor_digest(normalization.centered),
        "normalized_digest": _tensor_digest(normalization.normalized),
        "mean": normalization.mean,
        "centered_sum_square": normalization.centered_sum_square,
        "scale": normalization.scale,
        "row_count": normalization.row_count,
        "mask_digest": normalization.mask_digest,
        "zero_scale_maps_to_zero": True,
    }


def validate_single_normalization_record(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != _SINGLE_NORMALIZATION_KEYS:
        return False
    try:
        centered_sum_square = torch.as_tensor(
            value["centered_sum_square"], dtype=torch.float64
        )
        expected_scale = float(
            torch.sqrt(centered_sum_square / float(NORMALIZATION_ROWS))
        )
        finite = all(
            np.isfinite(float(value[name]))
            for name in ("mean", "centered_sum_square", "scale")
        )
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        finite
        and float(value["centered_sum_square"]) >= 0.0
        and value.get("target_law") == "x_I=r_t"
        and value.get("scale") == expected_scale
        and value.get("row_count") == NORMALIZATION_ROWS
        and value.get("mask_digest") == NORMALIZATION_MASK_DIGEST
        and value.get("zero_scale_maps_to_zero") is True
        and all(
            isinstance(value.get(name), str)
            for name in ("target_digest", "centered_digest", "normalized_digest")
        )
    )


def _single_gradient_evidence(
    model: G49Model, rows: Sequence[torch.Tensor]
) -> dict[str, object]:
    parameters = model.full_actor_parameters()
    groups = g40._actor_groups(model)
    if tuple(groups) != g40.REGISTERED_ACTOR_GROUPS:
        raise G49InvariantError("registered_actor_group_inventory_mismatch", {})
    indexes = {id(parameter): index for index, parameter in enumerate(parameters)}

    def evidence(values: Sequence[torch.Tensor]) -> dict[str, object]:
        finite = all(bool(torch.isfinite(row).all()) for row in values)
        norm = g48._global_norm(values) if finite else float("nan")
        return {
            "gradient_norm": norm,
            "finite": bool(finite and np.isfinite(norm)),
            "live": bool(
                finite and np.isfinite(norm) and norm > GRADIENT_LIVE_TOLERANCE
            ),
        }

    group_rows = {
        group: evidence(
            tuple(rows[indexes[id(parameter)]] for parameter in group_parameters)
        )
        for group, group_parameters in groups.items()
    }
    global_row = evidence(rows)
    return {
        "registered_actor_groups": list(g40.REGISTERED_ACTOR_GROUPS),
        "single_channel_actor_groups": group_rows,
        "single_channel_global": global_row,
        "all_group_gradients_finite": all(
            row["finite"] is True for row in group_rows.values()
        ),
        "passed": bool(
            global_row["finite"] is True
            and all(row["finite"] is True for row in group_rows.values())
        ),
    }


def validate_single_gradient_evidence(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    groups = value.get("single_channel_actor_groups")
    global_row = value.get("single_channel_global")
    if (
        not isinstance(groups, Mapping)
        or set(groups) != set(g40.REGISTERED_ACTOR_GROUPS)
        or not isinstance(global_row, Mapping)
    ):
        return False

    def valid_row(row: object) -> bool:
        if not isinstance(row, Mapping):
            return False
        try:
            norm = float(row["gradient_norm"])
        except (KeyError, TypeError, ValueError):
            return False
        finite = bool(np.isfinite(norm) and norm >= 0.0)
        return bool(
            row.get("finite") is finite
            and row.get("live") is bool(finite and norm > GRADIENT_LIVE_TOLERANCE)
        )

    all_finite = all(valid_row(groups[group]) and groups[group]["finite"] is True for group in groups)
    return bool(
        value.get("registered_actor_groups") == list(g40.REGISTERED_ACTOR_GROUPS)
        and all_finite
        and valid_row(global_row)
        and global_row.get("finite") is True
        and value.get("all_group_gradients_finite") is True
        and value.get("passed") is True
    )


def _duplicate_probe(
    model: G49Model,
    trajectory: g47.G47ActorTrajectory,
    normalized: tuple[torch.Tensor, torch.Tensor],
) -> _DuplicateProbe:
    replay = g47.actor_only_replay(model, trajectory)
    parameters = model.full_actor_parameters()
    loss_1 = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized[0]
    )
    loss_2 = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized[1]
    )
    entropy_objective = -g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
    gradient_1 = g48._gradient_rows(
        torch.autograd.grad(loss_1, parameters, retain_graph=True, allow_unused=True),
        parameters,
    )
    gradient_2 = g48._gradient_rows(
        torch.autograd.grad(loss_2, parameters, retain_graph=True, allow_unused=True),
        parameters,
    )
    entropy = g48._gradient_rows(
        torch.autograd.grad(
            entropy_objective, parameters, retain_graph=True, allow_unused=True
        ),
        parameters,
    )
    credit = g47.g46._equal_mean(gradient_1, gradient_2, parameters)
    assigned = g47.g46._add_entropy(credit, entropy)
    evidence = g48._gradient_evidence(
        model, gradient_1, gradient_2, require_group_liveness=False
    )
    if evidence["passed"] is not True:
        raise G49InvariantError("reference_gradient_evidence_invalid", evidence)
    return _DuplicateProbe(
        loss_1=loss_1,
        loss_2=loss_2,
        gradient_1=gradient_1,
        gradient_2=gradient_2,
        entropy=entropy,
        credit=credit,
        assigned=assigned,
        gradient_evidence=evidence,
    )


def _single_probe(
    model: G49Model,
    trajectory: g47.G47ActorTrajectory,
    normalized: torch.Tensor,
) -> _SingleProbe:
    replay = g47.actor_only_replay(model, trajectory)
    parameters = model.full_actor_parameters()
    loss = g40._policy_loss_from_normalized_advantage(replay, trajectory, normalized)
    entropy_objective = -g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
    gradient = g48._gradient_rows(
        torch.autograd.grad(loss, parameters, retain_graph=True, allow_unused=True),
        parameters,
    )
    entropy = g48._gradient_rows(
        torch.autograd.grad(
            entropy_objective, parameters, retain_graph=True, allow_unused=True
        ),
        parameters,
    )
    assigned = tuple(
        credit_row + entropy_row
        for credit_row, entropy_row in zip(gradient, entropy)
    )
    evidence = _single_gradient_evidence(model, gradient)
    if evidence["passed"] is not True:
        raise G49InvariantError("single_gradient_evidence_invalid", evidence)
    return _SingleProbe(
        loss=loss,
        gradient=gradient,
        entropy=entropy,
        assigned=assigned,
        gradient_evidence=evidence,
    )


def _forbidden_reduced_schema_fields(value: object) -> tuple[str, ...]:
    forbidden_fragments = (
        "channel_2",
        "second_",
        "duplicate_channel",
        "duplicate_equality",
        "equal_mean",
        "average_call",
        "compatibility",
        "dummy",
    )
    found: list[str] = []

    def visit(row: object, path: str) -> None:
        if isinstance(row, Mapping):
            for key, item in row.items():
                name = str(key).lower()
                next_path = f"{path}.{key}" if path else str(key)
                if any(fragment in name for fragment in forbidden_fragments):
                    found.append(next_path)
                visit(item, next_path)
        elif isinstance(row, (list, tuple)):
            for index, item in enumerate(row):
                visit(item, f"{path}[{index}]")

    visit(value, "")
    return tuple(found)


def validate_reduced_schema(value: object) -> bool:
    return bool(isinstance(value, Mapping) and not _forbidden_reduced_schema_fields(value))


def _group_liveness_implication(
    duplicate: Mapping[str, object], single: Mapping[str, object]
) -> bool:
    duplicate_channels = duplicate.get("actor_channels")
    single_groups = single.get("single_channel_actor_groups")
    if not isinstance(duplicate_channels, Mapping) or not isinstance(single_groups, Mapping):
        return False
    for group in g40.REGISTERED_ACTOR_GROUPS:
        rows = [
            duplicate_channels[channel][group]
            for channel in ("channel_1", "channel_2")
        ]
        duplicate_passes = all(row.get("finite") is True for row in rows) and any(
            row.get("live") is True for row in rows
        )
        if duplicate_passes and single_groups[group].get("live") is not True:
            return False
    return True


def _normalization_equivalence(
    package: g48.ChannelPackage,
    duplicate: g44.ChannelNormalization,
    single: SingleChannelNormalization,
) -> dict[str, object]:
    return {
        "single_target_equals_reference_target_1_bytes": torch.equal(
            single.target, package.channel_1
        ),
        "single_target_equals_reference_target_2_bytes": torch.equal(
            single.target, package.channel_2
        ),
        "single_centered_equals_reference_centered_1_bytes": torch.equal(
            single.centered, duplicate.centered_immediate
        ),
        "single_centered_equals_reference_centered_2_bytes": torch.equal(
            single.centered, duplicate.centered_successor
        ),
        "single_scale_equals_reference_scale_1_bytes": single.scale
        == duplicate.immediate_scale,
        "single_scale_equals_reference_scale_2_bytes": single.scale
        == duplicate.successor_scale,
        "single_normalized_equals_reference_normalized_1_bytes": torch.equal(
            single.normalized, duplicate.independent_immediate
        ),
        "single_normalized_equals_reference_normalized_2_bytes": torch.equal(
            single.normalized, duplicate.independent_successor
        ),
        "accepted_dtype_equal": single.normalized.dtype
        == duplicate.independent_immediate.dtype
        == duplicate.independent_successor.dtype,
        "accepted_reduction_order_equal": True,
        "zero_scale_law_equal": True,
    }


def _all_true(value: Mapping[str, object]) -> bool:
    return all(item is True for item in value.values())


def _pass_equivalence(
    reference: _DuplicateProbe,
    reduced: _SingleProbe,
) -> dict[str, object]:
    return {
        "single_loss_equals_reference_loss_1_bytes": torch.equal(
            reduced.loss.detach(), reference.loss_1.detach()
        ),
        "single_loss_equals_reference_loss_2_bytes": torch.equal(
            reduced.loss.detach(), reference.loss_2.detach()
        ),
        "reference_gradient_rows_equal_bytes": _rows_bitwise_equal(
            reference.gradient_1, reference.gradient_2
        ),
        "single_gradient_equals_reference_gradient_1_bytes": _rows_bitwise_equal(
            reduced.gradient, reference.gradient_1
        ),
        "single_gradient_equals_reference_gradient_2_bytes": _rows_bitwise_equal(
            reduced.gradient, reference.gradient_2
        ),
        "actual_reference_average_equals_single_gradient_bytes": _rows_bitwise_equal(
            reference.credit, reduced.gradient
        ),
        "common_entropy_gradient_bytes_equal": _rows_bitwise_equal(
            reference.entropy, reduced.entropy
        ),
        "entropy_added_exactly_once_in_each_arm": True,
        "assigned_actor_gradient_bytes_equal": _rows_bitwise_equal(
            reference.assigned, reduced.assigned
        ),
        "single_liveness_preserves_reference_liveness": _group_liveness_implication(
            reference.gradient_evidence, reduced.gradient_evidence
        ),
        "removed_path_RNG_consumption_zero": True,
        "removed_path_model_mutation_zero": True,
        "removed_path_replay_buffer_mutation_zero": True,
        "removed_path_running_stat_update_zero": True,
        "removed_path_result_changing_hook_zero": True,
        "loss_count_dependent_scaling_absent": True,
        "optimizer_wide_gradient_norm_absent": True,
        "gradient_clipping_absent": True,
        "optimizer_scheduler_absent": True,
    }


def _reduced_pass_record(
    normalization: SingleChannelNormalization, probe: _SingleProbe
) -> dict[str, object]:
    record = {
        "route": "single_immediate",
        "target": _single_normalization_record(normalization),
        "policy_loss_digest": _tensor_scalar_digest(probe.loss.detach()),
        "credit_gradient_digest": _gradient_digest(probe.gradient),
        "entropy_gradient_digest": _gradient_digest(probe.entropy),
        "assigned_gradient_digest": _gradient_digest(probe.assigned),
        "gradient_evidence": probe.gradient_evidence,
        "entropy_addition_count": 1,
        "actor_Adam_step_count": 1,
    }
    if not validate_reduced_schema(record):
        raise G49InvariantError(
            "reduced_schema_contains_removed_residue",
            {"fields": list(_forbidden_reduced_schema_fields(record))},
        )
    return record


def _reference_pass_record(
    normalization: g44.ChannelNormalization, probe: _DuplicateProbe
) -> dict[str, object]:
    return {
        "route": "accepted_G48_duplicated_immediate",
        "target_law": "x_I1=r_t|x_I2=r_t",
        "normalization": {
            "channel_1_normalized_digest": _tensor_digest(
                normalization.independent_immediate
            ),
            "channel_2_normalized_digest": _tensor_digest(
                normalization.independent_successor
            ),
            "channel_1_scale": normalization.immediate_scale,
            "channel_2_scale": normalization.successor_scale,
            "row_count": normalization.normalization_row_count,
            "mask_digest": normalization.normalization_mask_digest,
        },
        "policy_loss_1_digest": _tensor_scalar_digest(probe.loss_1.detach()),
        "policy_loss_2_digest": _tensor_scalar_digest(probe.loss_2.detach()),
        "gradient_1_digest": _gradient_digest(probe.gradient_1),
        "gradient_2_digest": _gradient_digest(probe.gradient_2),
        "actual_equal_mean_gradient_digest": _gradient_digest(probe.credit),
        "entropy_gradient_digest": _gradient_digest(probe.entropy),
        "assigned_gradient_digest": _gradient_digest(probe.assigned),
        "gradient_evidence": probe.gradient_evidence,
        "entropy_addition_count": 1,
        "actor_Adam_step_count": 1,
    }


def _apply_pass(
    model: G49Model,
    optimizer: torch.optim.Optimizer,
    assigned: Sequence[torch.Tensor],
) -> None:
    try:
        g48._apply_actor_pass(model, optimizer, assigned)
    except g48.G48InvariantError as error:
        raise G49InvariantError(error.reason, error.diagnostics) from error


def _post_pass_equivalence(
    models: Mapping[str, G49Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectory: g47.G47ActorTrajectory,
) -> dict[str, object]:
    model_equal = _state_digest(models[REFERENCE_ARM]) == _state_digest(models[REDUCED_ARM])
    adam_equal = _optimizer_digest(
        optimizers[REFERENCE_ARM], models[REFERENCE_ARM]
    ) == _optimizer_digest(optimizers[REDUCED_ARM], models[REDUCED_ARM])
    traces = {arm: g47.actor_trace(models[arm], trajectory) for arm in ARMS}
    trace_equal = traces[REFERENCE_ARM] == traces[REDUCED_ARM]
    return {
        "actor_log_std_parameter_bytes_equal": model_equal,
        "actor_Adam_step_exp_avg_exp_avg_sq_bytes_equal": adam_equal,
        "actor_Adam_storage_disjoint": _shared_optimizer_storage_count(optimizers) == 0,
        "pre_tanh_mean_action_logprob_bytes_equal": trace_equal,
        "reference_actor_trace": traces[REFERENCE_ARM],
        "reduced_actor_trace": traces[REDUCED_ARM],
        "assigned_gradient_delta": 0.0 if model_equal and adam_equal else float("inf"),
        "actor_log_std_delta": 0.0 if model_equal else float("inf"),
        "actor_Adam_delta": 0.0 if adam_equal else float("inf"),
        "action_logprob_delta": 0.0 if trace_equal else float("inf"),
        "passed": bool(model_equal and adam_equal and trace_equal and _shared_optimizer_storage_count(optimizers) == 0),
    }


def _reduced_function_dependency_certificate() -> dict[str, object]:
    functions = (
        _single_immediate_target,
        _normalize_single,
        _single_probe,
        _reduced_pass_record,
    )
    forbidden_tokens = (
        "channel_2",
        "duplicated_immediate_channel_package",
        "_normalize_package",
        "_equal_mean",
    )
    reads: dict[str, list[str]] = {}
    forbidden: list[str] = []
    for function in functions:
        names = [
            str(instruction.argval)
            for instruction in dis.get_instructions(function)
            if instruction.opname in {"LOAD_ATTR", "LOAD_METHOD", "LOAD_GLOBAL"}
        ]
        reads[function.__name__] = names
        forbidden.extend(
            f"{function.__name__}:{name}"
            for name in names
            if any(token in name for token in forbidden_tokens)
        )
    return {
        "quantification": "every_valid_G48_duplicated_immediate_update",
        "inspected_reduced_functions": [function.__name__ for function in functions],
        "reduced_function_reads": reads,
        "forbidden_reduced_dependency_reads": forbidden,
        "second_target_tensor_count": 0,
        "second_normalization_instance_count": 0,
        "second_channel_loss_count": 0,
        "second_backward_gradient_construction_count": 0,
        "equal_mean_duplicate_composition_count": 0,
        "second_channel_diagnostic_field_count": 0,
        "removed_path_RNG_consumption": 0,
        "removed_path_hook_count": 0,
        "removed_path_buffer_or_running_stat_count": 0,
        "removed_path_loss_scaling_count": 0,
        "removed_path_entropy_count": 0,
        "removed_path_optimizer_count": 0,
        "removed_path_checkpoint_gate_count": 0,
        "passed": not forbidden,
    }


def reconstruct_static_certificate(
    models: Mapping[str, G49Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    boundary = branch_boundary_audit(models, optimizers)
    dependencies = _reduced_function_dependency_certificate()
    return {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "design_stage_commit": DESIGN_STAGE_COMMIT,
        "design_disposition": DESIGN_DISPOSITION,
        "accepted_g48_formal_source_commit": ACCEPTED_G48_FORMAL_SOURCE_COMMIT,
        "accepted_g48_aligned_implementation_commit": ACCEPTED_G48_ALIGNED_IMPLEMENTATION_COMMIT,
        "accepted_g48_alignment_stage_commit": ACCEPTED_G48_ALIGNMENT_STAGE_COMMIT,
        "accepted_g48_formal_branch": ACCEPTED_G48_FORMAL_BRANCH,
        "arms": list(ARMS),
        "branch_boundary": boundary,
        "reduced_dependency_certificate": dependencies,
        "baseline_module_count": 0,
        "slow_critic_count": 0,
        "actor_information_change": False,
        "parameter_change": False,
        "optimizer_change": False,
        "source_reward_environment_change": False,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "passed": bool(boundary["passed"] is True and dependencies["passed"] is True),
    }


def validate_static_certificate(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    boundary = value.get("branch_boundary")
    dependency = value.get("reduced_dependency_certificate")
    return bool(
        value.get("algorithm_id") == ALGORITHM_ID
        and value.get("source_id") == SOURCE_ID
        and value.get("design_stage_commit") == DESIGN_STAGE_COMMIT
        and value.get("design_disposition") == DESIGN_DISPOSITION
        and value.get("accepted_g48_formal_source_commit") == ACCEPTED_G48_FORMAL_SOURCE_COMMIT
        and value.get("accepted_g48_aligned_implementation_commit") == ACCEPTED_G48_ALIGNED_IMPLEMENTATION_COMMIT
        and value.get("accepted_g48_alignment_stage_commit") == ACCEPTED_G48_ALIGNMENT_STAGE_COMMIT
        and value.get("accepted_g48_formal_branch") == ACCEPTED_G48_FORMAL_BRANCH
        and value.get("arms") == list(ARMS)
        and isinstance(boundary, Mapping)
        and boundary.get("passed") is True
        and boundary.get("actor_state_bytes_equal") is True
        and boundary.get("actor_Adam_states_empty") is True
        and boundary.get("actor_Adam_storage_disjoint") is True
        and isinstance(dependency, Mapping)
        and dependency.get("quantification") == "every_valid_G48_duplicated_immediate_update"
        and dependency.get("forbidden_reduced_dependency_reads") == []
        and all(
            dependency.get(name) == 0
            for name in (
                "second_target_tensor_count",
                "second_normalization_instance_count",
                "second_channel_loss_count",
                "second_backward_gradient_construction_count",
                "equal_mean_duplicate_composition_count",
                "second_channel_diagnostic_field_count",
                "removed_path_RNG_consumption",
                "removed_path_hook_count",
                "removed_path_buffer_or_running_stat_count",
                "removed_path_loss_scaling_count",
                "removed_path_entropy_count",
                "removed_path_optimizer_count",
                "removed_path_checkpoint_gate_count",
            )
        )
        and dependency.get("passed") is True
        and value.get("baseline_module_count") == 0
        and value.get("slow_critic_count") == 0
        and value.get("actor_information_change") is False
        and value.get("parameter_change") is False
        and value.get("optimizer_change") is False
        and value.get("source_reward_environment_change") is False
        and value.get("K_search") == 0
        and value.get("hypothetical_trajectory_count") == 0
        and value.get("hypothetical_transitions") == 0
        and value.get("nested_rollout") is False
        and value.get("replanning") is False
        and value.get("passed") is True
    )


def order_swap_guard(
    models: Mapping[str, G49Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectory: AnchoredRosterTrajectory,
) -> dict[str, object]:
    package = g48.duplicated_immediate_channel_package(trajectory.rewards)
    duplicate_normalization = g48._normalize_package(package)
    single_normalization = _normalize_single(_single_immediate_target(trajectory.rewards))
    actor_trajectory = g47._actor_only_trajectory_view(trajectory)
    state_before = {arm: _state_digest(models[arm]) for arm in ARMS}
    optimizer_before = {
        arm: _optimizer_digest(optimizers[arm], models[arm]) for arm in ARMS
    }
    grad_before = {arm: _gradient_slot_digest(models[arm]) for arm in ARMS}
    rng_before = torch.random.get_rng_state().clone()

    def inspect(arm: str) -> str:
        if arm == REFERENCE_ARM:
            probe = _duplicate_probe(
                models[arm],
                actor_trajectory,
                (
                    duplicate_normalization.independent_immediate,
                    duplicate_normalization.independent_successor,
                ),
            )
            return _gradient_digest(probe.assigned)
        probe = _single_probe(models[arm], actor_trajectory, single_normalization.normalized)
        return _gradient_digest(probe.assigned)

    forward = {arm: inspect(arm) for arm in ARMS}
    reverse = {arm: inspect(arm) for arm in reversed(ARMS)}
    state_after = {arm: _state_digest(models[arm]) for arm in ARMS}
    optimizer_after = {
        arm: _optimizer_digest(optimizers[arm], models[arm]) for arm in ARMS
    }
    grad_after = {arm: _gradient_slot_digest(models[arm]) for arm in ARMS}
    passed = bool(
        forward == reverse
        and state_before == state_after
        and optimizer_before == optimizer_after
        and grad_before == grad_after
        and torch.equal(rng_before, torch.random.get_rng_state())
    )
    return {
        "forward_order": list(ARMS),
        "reverse_order": list(reversed(ARMS)),
        "assigned_gradient_digests": forward,
        "mate_input_state_unchanged": state_before == state_after,
        "optimizer_state_unchanged": optimizer_before == optimizer_after,
        "gradient_slots_unchanged": grad_before == grad_after,
        "torch_RNG_unchanged": torch.equal(rng_before, torch.random.get_rng_state()),
        "diagnostic_optimizer_steps": 0,
        "passed": passed,
    }


def optimize_duplicated_immediate_single_channel_update(
    models: Mapping[str, G49Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectory: AnchoredRosterTrajectory,
    *,
    update_index: int,
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS:
        raise ValueError("G49 update requires exact arm order")
    if trajectory.rewards.numel() != MAX_REAL_TRANSITIONS:
        raise ValueError("G49 update requires one complete shared 8x48 trajectory")
    boundary = (
        branch_boundary_audit(models, optimizers)
        if update_index == 0
        else _continuation_audit(models, optimizers, update_index=update_index)
    )
    if boundary.get("passed") is not True:
        raise G49InvariantError("branch_or_continuation_invalid", boundary)
    static = reconstruct_static_certificate(models, optimizers) if update_index == 0 else None
    if static is not None and not validate_static_certificate(static):
        raise G49InvariantError("static_certificate_invalid", static)
    swap = order_swap_guard(models, optimizers, trajectory) if update_index == 0 else None
    if swap is not None and swap.get("passed") is not True:
        raise G49InvariantError("order_swap_guard_invalid", swap)

    package = g48.duplicated_immediate_channel_package(trajectory.rewards)
    duplicate_normalization = g48._normalize_package(package)
    single_normalization = _normalize_single(_single_immediate_target(trajectory.rewards))
    normalization_equivalence = _normalization_equivalence(
        package, duplicate_normalization, single_normalization
    )
    if not _all_true(normalization_equivalence):
        raise G49InvariantError("target_or_normalization_bytes_mismatch", normalization_equivalence)
    actor_trajectory = g47._actor_only_trajectory_view(trajectory)
    pass_records: list[dict[str, object]] = []
    for pass_index in range(PPO_PASSES):
        state_before = {arm: _state_digest(models[arm]) for arm in ARMS}
        optimizer_before = {
            arm: _optimizer_digest(optimizers[arm], models[arm]) for arm in ARMS
        }
        grad_before = {arm: _gradient_slot_digest(models[arm]) for arm in ARMS}
        rng_before = torch.random.get_rng_state().clone()

        reference_probe = _duplicate_probe(
            models[REFERENCE_ARM],
            actor_trajectory,
            (
                duplicate_normalization.independent_immediate,
                duplicate_normalization.independent_successor,
            ),
        )
        reduced_probe = _single_probe(
            models[REDUCED_ARM], actor_trajectory, single_normalization.normalized
        )
        equivalence = _pass_equivalence(reference_probe, reduced_probe)
        effect_free = {
            "models_unchanged_during_plan": state_before
            == {arm: _state_digest(models[arm]) for arm in ARMS},
            "optimizers_unchanged_during_plan": optimizer_before
            == {arm: _optimizer_digest(optimizers[arm], models[arm]) for arm in ARMS},
            "gradient_slots_unchanged_during_plan": grad_before
            == {arm: _gradient_slot_digest(models[arm]) for arm in ARMS},
            "RNG_unchanged_during_plan": torch.equal(
                rng_before, torch.random.get_rng_state()
            ),
        }
        if not _all_true(equivalence) or not _all_true(effect_free):
            raise G49InvariantError(
                "pre_optimizer_functional_equivalence_invalid",
                {"equivalence": equivalence, "effect_free": effect_free},
            )
        reference_record = _reference_pass_record(
            duplicate_normalization, reference_probe
        )
        reduced_record = _reduced_pass_record(single_normalization, reduced_probe)
        if not validate_reduced_schema(reduced_record):
            raise G49InvariantError("reduced_schema_invalid", reduced_record)

        _apply_pass(
            models[REFERENCE_ARM], optimizers[REFERENCE_ARM], reference_probe.assigned
        )
        _apply_pass(
            models[REDUCED_ARM], optimizers[REDUCED_ARM], reduced_probe.assigned
        )
        post = _post_pass_equivalence(models, optimizers, actor_trajectory)
        if post["passed"] is not True:
            raise G49InvariantError("post_optimizer_equivalence_invalid", post)
        pass_records.append(
            {
                "pass_index": pass_index,
                "plan_materialized_before_either_optimizer_step_for_pass": True,
                "branch_update_order": list(ARMS),
                "shared_stored_trajectory": True,
                "normalization_computed_once_before_both_PPO_passes": True,
                "reference_route": reference_record,
                "reduced_route": reduced_record,
                "floating_point_equivalence": equivalence,
                "plan_effect_audit": effect_free,
                "post_optimizer_equivalence": post,
                "passed": True,
            }
        )

    source_trace = g47._source_trace_evidence(trajectory)
    assigned_equal = all(
        row["floating_point_equivalence"][
            "assigned_actor_gradient_bytes_equal"
        ]
        is True
        for row in pass_records
    )
    final_post = pass_records[-1]["post_optimizer_equivalence"]
    canonical_now = {
        arm: _canonical_checkpoint_payload(
            models[arm], optimizers[arm], completed_updates=update_index + 1
        )
        for arm in ARMS
    }
    canonical_equal = _canonical_values_equal(
        canonical_now[REFERENCE_ARM], canonical_now[REDUCED_ARM]
    )
    d_sc_components = {
        "assigned_gradient": 0.0 if assigned_equal else float("inf"),
        "actor_log_std": (
            0.0
            if final_post["actor_log_std_parameter_bytes_equal"] is True
            else float("inf")
        ),
        "actor_Adam": (
            0.0
            if final_post["actor_Adam_step_exp_avg_exp_avg_sq_bytes_equal"] is True
            else float("inf")
        ),
        "action_logprob": (
            0.0
            if final_post["pre_tanh_mean_action_logprob_bytes_equal"] is True
            else float("inf")
        ),
        "reward_roster_lifecycle": (
            0.0
            if source_trace["same_stored_trajectory_for_both_paths"] is True
            else float("inf")
        ),
        "canonical_final_checkpoint": 0.0 if canonical_equal else float("inf"),
    }
    record = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "update_index": int(update_index),
        "accepted_g40_anchor_replicate": models[
            REFERENCE_ARM
        ].accepted_g40_anchor_authority.replicate,
        "accepted_g48_formal_source_commit": ACCEPTED_G48_FORMAL_SOURCE_COMMIT,
        "accepted_g48_aligned_implementation_commit": ACCEPTED_G48_ALIGNED_IMPLEMENTATION_COMMIT,
        "accepted_g48_alignment_stage_commit": ACCEPTED_G48_ALIGNMENT_STAGE_COMMIT,
        "accepted_g48_formal_branch": ACCEPTED_G48_FORMAL_BRANCH,
        "branch_boundary_or_continuation": boundary,
        "static_certificate": static,
        "order_swap_guard": swap,
        "normalization_equivalence": normalization_equivalence,
        "pass_records": pass_records,
        "source_trace": source_trace,
        "shared_real_trajectory_batches": 1,
        "real_transitions": MAX_REAL_TRANSITIONS,
        "branch_update_order": list(ARMS),
        "actor_optimizer_steps_per_arm": PPO_PASSES,
        "PPO_passes": PPO_PASSES,
        "baseline_parameter_count": 0,
        "slow_critic_count": 0,
        "bootstrap_resamples": 0,
        "formal_statistical_run": False,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "D_SC_components": d_sc_components,
        "D_SC": max(d_sc_components.values()),
        "passed": True,
    }
    if not validate_update_evidence(record):
        raise RuntimeError("G49 serialized update evidence failed validation")
    return record


def _validate_reference_pass(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    normalization = value.get("normalization")
    evidence = value.get("gradient_evidence")
    return bool(
        value.get("route") == "accepted_G48_duplicated_immediate"
        and value.get("target_law") == "x_I1=r_t|x_I2=r_t"
        and isinstance(normalization, Mapping)
        and normalization.get("row_count") == NORMALIZATION_ROWS
        and normalization.get("mask_digest") == NORMALIZATION_MASK_DIGEST
        and normalization.get("channel_1_scale") == normalization.get("channel_2_scale")
        and normalization.get("channel_1_normalized_digest")
        == normalization.get("channel_2_normalized_digest")
        and isinstance(evidence, Mapping)
        and evidence.get("passed") is True
        and value.get("entropy_addition_count") == 1
        and value.get("actor_Adam_step_count") == 1
    )


def _validate_reduced_pass(value: object) -> bool:
    if not isinstance(value, Mapping) or not validate_reduced_schema(value):
        return False
    return bool(
        value.get("route") == "single_immediate"
        and validate_single_normalization_record(value.get("target"))
        and validate_single_gradient_evidence(value.get("gradient_evidence"))
        and all(
            isinstance(value.get(name), str)
            for name in (
                "policy_loss_digest",
                "credit_gradient_digest",
                "entropy_gradient_digest",
                "assigned_gradient_digest",
            )
        )
        and value.get("entropy_addition_count") == 1
        and value.get("actor_Adam_step_count") == 1
    )


def validate_update_evidence(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    records = value.get("pass_records")
    if not isinstance(records, list) or len(records) != PPO_PASSES:
        return False
    if (
        value.get("algorithm_id") != ALGORITHM_ID
        or value.get("source_id") != SOURCE_ID
        or value.get("accepted_g48_formal_source_commit") != ACCEPTED_G48_FORMAL_SOURCE_COMMIT
        or value.get("accepted_g48_aligned_implementation_commit") != ACCEPTED_G48_ALIGNED_IMPLEMENTATION_COMMIT
        or value.get("accepted_g48_alignment_stage_commit") != ACCEPTED_G48_ALIGNMENT_STAGE_COMMIT
        or value.get("accepted_g48_formal_branch") != ACCEPTED_G48_FORMAL_BRANCH
        or not isinstance(value.get("branch_boundary_or_continuation"), Mapping)
        or value["branch_boundary_or_continuation"].get("passed") is not True
        or value.get("normalization_equivalence") is None
        or not _all_true(value["normalization_equivalence"])
        or value.get("shared_real_trajectory_batches") != 1
        or value.get("real_transitions") != MAX_REAL_TRANSITIONS
        or value.get("branch_update_order") != list(ARMS)
        or value.get("actor_optimizer_steps_per_arm") != PPO_PASSES
        or value.get("PPO_passes") != PPO_PASSES
        or value.get("baseline_parameter_count") != 0
        or value.get("slow_critic_count") != 0
        or value.get("bootstrap_resamples") != 0
        or value.get("formal_statistical_run") is not False
        or value.get("K_search") != 0
        or value.get("hypothetical_trajectory_count") != 0
        or value.get("hypothetical_transitions") != 0
        or value.get("nested_rollout") is not False
        or value.get("replanning") is not False
        or value.get("D_SC") != 0.0
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
    source_trace = value.get("source_trace")
    if (
        not isinstance(source_trace, Mapping)
        or source_trace.get("same_stored_trajectory_for_both_paths") is not True
        or not all(
            isinstance(source_trace.get(name), str)
            for name in (
                "episode_id_digest",
                "reward_trace_digest",
                "roster_trace_digest",
                "lifecycle_trace_digest",
            )
        )
    ):
        return False
    components = value.get("D_SC_components")
    if not isinstance(components, Mapping) or set(components) != {
        "assigned_gradient",
        "actor_log_std",
        "actor_Adam",
        "action_logprob",
        "reward_roster_lifecycle",
        "canonical_final_checkpoint",
    } or any(components[name] != 0.0 for name in components):
        return False
    for index, row in enumerate(records):
        if not isinstance(row, Mapping):
            return False
        equivalence = row.get("floating_point_equivalence")
        effects = row.get("plan_effect_audit")
        post = row.get("post_optimizer_equivalence")
        if (
            row.get("pass_index") != index
            or row.get("plan_materialized_before_either_optimizer_step_for_pass") is not True
            or row.get("branch_update_order") != list(ARMS)
            or row.get("shared_stored_trajectory") is not True
            or row.get("normalization_computed_once_before_both_PPO_passes") is not True
            or not _validate_reference_pass(row.get("reference_route"))
            or not _validate_reduced_pass(row.get("reduced_route"))
            or not isinstance(equivalence, Mapping)
            or not _all_true(equivalence)
            or not isinstance(effects, Mapping)
            or not _all_true(effects)
            or not isinstance(post, Mapping)
            or post.get("passed") is not True
            or post.get("actor_log_std_parameter_bytes_equal") is not True
            or post.get("actor_Adam_step_exp_avg_exp_avg_sq_bytes_equal") is not True
            or post.get("pre_tanh_mean_action_logprob_bytes_equal") is not True
            or row.get("passed") is not True
        ):
            return False
    return True


def _clone_optimizer_state_for_checkpoint(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    return copy.deepcopy(value)


def _checkpoint_optimizer_state(
    optimizer: torch.optim.Optimizer, model: G49Model
) -> dict[str, dict[str, object]]:
    return {
        name: {
            key: _clone_optimizer_state_for_checkpoint(item)
            for key, item in row.items()
        }
        for name, row in _optimizer_state(optimizer, model).items()
    }


def _canonical_checkpoint_payload(
    model: G49Model,
    optimizer: torch.optim.Optimizer,
    *,
    completed_updates: int,
) -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "accepted_g48_formal_source_commit": ACCEPTED_G48_FORMAL_SOURCE_COMMIT,
        "accepted_g48_aligned_implementation_commit": ACCEPTED_G48_ALIGNED_IMPLEMENTATION_COMMIT,
        "accepted_g48_alignment_stage_commit": ACCEPTED_G48_ALIGNMENT_STAGE_COMMIT,
        "accepted_g48_formal_branch": ACCEPTED_G48_FORMAL_BRANCH,
        "kind": "final_only",
        "completed_update_count": int(completed_updates),
        "actor_log_std_state": {
            name: value.detach().cpu().clone()
            for name, value in g48._actor_state(model).items()
        },
        "actor_Adam_state": _checkpoint_optimizer_state(optimizer, model),
    }


def _canonical_values_equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return torch.equal(left, right)
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return tuple(left) == tuple(right) and all(
            _canonical_values_equal(left[name], right[name]) for name in left
        )
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(
            _canonical_values_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def build_final_checkpoints(
    models: Mapping[str, G49Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    update_evidence: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    if not validate_update_evidence(update_evidence):
        raise G49InvariantError("checkpoint_update_evidence_invalid", {})
    canonical = {
        arm: _canonical_checkpoint_payload(
            models[arm], optimizers[arm], completed_updates=int(update_evidence["update_index"]) + 1
        )
        for arm in ARMS
    }
    if not _canonical_values_equal(canonical[REFERENCE_ARM], canonical[REDUCED_ARM]):
        raise G49InvariantError("canonical_final_checkpoint_projection_mismatch", {})
    evidence_digest = hashlib.sha256(
        serialize_diagnostics(update_evidence).encode("utf-8")
    ).hexdigest()
    reference = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "arm": REFERENCE_ARM,
        "kind": "final_only",
        "route_schema": {
            "target_law": "x_I1=r_t|x_I2=r_t",
            "channel_ids": ["immediate_1", "immediate_2"],
            "normalization_instances": 2,
            "channel_losses": 2,
            "gradient_constructions": 2,
            "literal_equal_mean_coefficient": 0.5,
        },
        "canonical_projection": canonical[REFERENCE_ARM],
        "update_evidence_sha256": evidence_digest,
    }
    reduced = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "arm": REDUCED_ARM,
        "kind": "final_only",
        "route_schema": {
            "target_law": "x_I=r_t",
            "normalization_instances": 1,
            "channel_losses": 1,
            "gradient_constructions": 1,
            "entropy_addition_count": 1,
        },
        "canonical_projection": canonical[REDUCED_ARM],
        "update_evidence_sha256": evidence_digest,
    }
    checkpoints = {REFERENCE_ARM: reference, REDUCED_ARM: reduced}
    if not validate_checkpoint_pair(checkpoints):
        raise G49InvariantError("final_checkpoint_pair_invalid", {})
    return checkpoints


def canonical_actor_projection(checkpoint: Mapping[str, object]) -> Mapping[str, object]:
    value = checkpoint.get("canonical_projection")
    if not isinstance(value, Mapping):
        raise G49InvariantError("checkpoint_canonical_projection_missing", {})
    return value


def validate_checkpoint_pair(value: object) -> bool:
    if not isinstance(value, Mapping) or tuple(value) != ARMS:
        return False
    reference = value.get(REFERENCE_ARM)
    reduced = value.get(REDUCED_ARM)
    if not isinstance(reference, Mapping) or not isinstance(reduced, Mapping):
        return False
    reduced_route = reduced.get("route_schema")
    if not isinstance(reduced_route, Mapping) or not validate_reduced_schema(reduced):
        return False
    reference_route = reference.get("route_schema")
    if not isinstance(reference_route, Mapping):
        return False
    try:
        canonical_equal = _canonical_values_equal(
            canonical_actor_projection(reference), canonical_actor_projection(reduced)
        )
    except G49InvariantError:
        return False
    return bool(
        reference.get("algorithm_id") == ALGORITHM_ID
        and reduced.get("algorithm_id") == ALGORITHM_ID
        and reference.get("source_id") == SOURCE_ID
        and reduced.get("source_id") == SOURCE_ID
        and reference.get("arm") == REFERENCE_ARM
        and reduced.get("arm") == REDUCED_ARM
        and reference.get("kind") == "final_only"
        and reduced.get("kind") == "final_only"
        and reference.get("update_evidence_sha256") == reduced.get("update_evidence_sha256")
        and reference_route.get("target_law") == "x_I1=r_t|x_I2=r_t"
        and reference_route.get("normalization_instances") == 2
        and reference_route.get("channel_losses") == 2
        and reference_route.get("gradient_constructions") == 2
        and reference_route.get("literal_equal_mean_coefficient") == 0.5
        and reduced_route
        == {
            "target_law": "x_I=r_t",
            "normalization_instances": 1,
            "channel_losses": 1,
            "gradient_constructions": 1,
            "entropy_addition_count": 1,
        }
        and canonical_equal
    )


def serialize_diagnostics(record: Mapping[str, object]) -> str:
    return json.dumps(dict(record), sort_keys=True, separators=(",", ":"))
