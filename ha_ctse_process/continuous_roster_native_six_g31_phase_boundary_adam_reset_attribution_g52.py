"""Fresh common-ancestor Adam-boundary attribution for G52-P0.

The only treatment is the Phase-B actor-Adam state.  RESET begins Phase B with
an empty Adam while CARRY receives exact, storage-disjoint clones of the common
Phase-A ancestor's ``step``, ``exp_avg`` and ``exp_avg_sq`` rows.  No
predecessor artifact is an initialization source.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

import torch
from torch import nn

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_common_fast_anchor_attribution_g50 as g50,
)
from ha_ctse_process.continuous_roster_seed import seed_block_from_bases
from ha_ctse_process import (
    continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49
    as g49,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51
    as g51,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47 as g47,
)


ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_BOUNDARY_ADAM_RESET_ATTRIBUTION_G52"
)
SOURCE_ID = f"{ALGORITHM_ID}_P0"
SCHEMA_VERSION = 1

ACCEPTED_ANCESTRY = (
    "G49_P0@8ecb01fd3ac0debf1b792e4e51293e07974d633b",
    "G50_P0@b8290699f5c10c593bbc21a6666c17950fae84d3",
    "G51_P0@ce6ed8659c480ca2779155b2871dc82b89fa0e95",
    "G52_P0",
)
REFERENCE_ARM = "SINGLE_IMMEDIATE_RESET_ADAM_AT_PHASE_BOUNDARY"
NULL_ARM = "SINGLE_IMMEDIATE_PERSISTENT_ADAM_ACROSS_PHASE_BOUNDARY"
RESET_ARM = REFERENCE_ARM
CARRY_ARM = NULL_ARM
ARMS = (RESET_ARM, CARRY_ARM)

PPO_PASSES = 2
NUM_ENVS = 8
HORIZON = 48
NORMALIZATION_ROWS = NUM_ENVS * HORIZON
FORMAL_PHASE_A_UPDATES = 100
FORMAL_PHASE_B_UPDATES = 100
NONFORMAL_PHASE_A_UPDATES = 10
NONFORMAL_PHASE_B_UPDATES = 10
EXPECTED_FORMAL_BOUNDARY_STEP = FORMAL_PHASE_A_UPDATES * PPO_PASSES
K_SEARCH = 0

ACTOR_PARAMETER_NAMES = (
    "policy.log_std",
    "policy.member_encoder.0.weight",
    "policy.member_encoder.0.bias",
    "policy.member_encoder.2.weight",
    "policy.member_encoder.2.bias",
    "policy.context_encoder.0.weight",
    "policy.context_encoder.0.bias",
    "policy.actor_rnn.weight_ih",
    "policy.actor_rnn.weight_hh",
    "policy.actor_rnn.bias_ih",
    "policy.actor_rnn.bias_hh",
    "policy.action_mean.0.weight",
    "policy.action_mean.0.bias",
    "policy.action_mean.2.weight",
    "policy.action_mean.2.bias",
    "policy.current_observation_residual.weight",
    "policy.current_observation_residual.bias",
)
if len(ACTOR_PARAMETER_NAMES) != 17:
    raise RuntimeError("G52 retained actor inventory must contain exactly 17 names")

SEED_BASES = {
    "initialization": 10_521_000,
    "phase_A_ledger": 10_522_000,
    "phase_A_action": 10_523_000,
    "phase_A_gradient_probe": 10_524_000,
    "phase_B_ledger": 10_525_000,
    "phase_B_action": 10_526_000,
    "phase_B_gradient_probe": 10_527_000,
    "evaluation_ledger": 10_528_000,
    "evaluation_process": 10_529_000,
    "evaluation_action": 10_530_000,
}
BOOTSTRAP_SEED = 10_531_052
NONFORMAL_SEED_OFFSET = 900_000

INVALID_RESULT = (
    "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_BOUNDARY_ADAM_RESET_ATTRIBUTION_G52"
)
SOURCE_FAILURE_RESULT = "SOURCE_OR_REFERENCE_ACCESS_FAILURE_G52"
PERSISTENT_SUFFICIENT_RESULT = "PERSISTENT_ADAM_CONTINUOUS_TRAINING_SUFFICIENT_G52"
RESET_ADVANTAGE_RESULT = "PHASE_BOUNDARY_ADAM_RESET_FINITE_BUDGET_ADVANTAGE_G52"
UNDERPOWERED_RESULT = "MIXED_UNDERPOWERED_PHASE_BOUNDARY_ADAM_RESET_ATTRIBUTION_G52"
RESULT_BRANCHES = (
    INVALID_RESULT,
    SOURCE_FAILURE_RESULT,
    PERSISTENT_SUFFICIENT_RESULT,
    RESET_ADVANTAGE_RESULT,
    UNDERPOWERED_RESULT,
)
MATERIALITY_MARGIN = 0.05


class G52InvariantError(ValueError):
    """A protected G52 lifecycle, Adam, or certificate predicate failed."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object] | None = None):
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics or {})
        super().__init__(f"G52 invariant failed: {self.reason}")


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    if isinstance(replicate, bool) or not isinstance(replicate, int) or not 0 <= replicate < 3:
        raise ValueError("G52 replicate outside frozen support")
    return seed_block_from_bases(
        SEED_BASES,
        replicate,
        formal=formal,
        nonformal_offset=NONFORMAL_SEED_OFFSET,
    )


def bootstrap_seed(*, formal: bool) -> int:
    return BOOTSTRAP_SEED + (0 if formal else NONFORMAL_SEED_OFFSET)


def _optimizer_parameters(optimizer: torch.optim.Optimizer) -> tuple[nn.Parameter, ...]:
    return tuple(parameter for group in optimizer.param_groups for parameter in group["params"])


def _parameter_names(model: nn.Module, parameters: Sequence[nn.Parameter]) -> tuple[str, ...]:
    by_id = {id(parameter): name for name, parameter in model.named_parameters()}
    return tuple(by_id.get(id(parameter), "<foreign>") for parameter in parameters)


def actor_parameters(model: nn.Module) -> tuple[nn.Parameter, ...]:
    if not hasattr(model, "full_actor_parameters"):
        raise G52InvariantError("model_has_no_actor_parameter_interface")
    parameters = tuple(model.full_actor_parameters())  # type: ignore[attr-defined]
    names = _parameter_names(model, parameters)
    if names != ACTOR_PARAMETER_NAMES or len(set(map(id, parameters))) != len(parameters):
        raise G52InvariantError("actor_inventory_invalid", {"names": list(names)})
    return parameters


def _tensor_storage_id(value: torch.Tensor) -> int | None:
    return None if value.numel() == 0 else int(value.untyped_storage().data_ptr())


def _module_storage_ids(module: nn.Module) -> set[int]:
    return {
        storage
        for value in (*module.parameters(), *module.buffers())
        if (storage := _tensor_storage_id(value)) is not None
    }


def _tensor_digest(value: torch.Tensor) -> str:
    original_device = str(value.device)
    row = value.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(row.dtype).encode("ascii"))
    digest.update(original_device.encode("ascii"))
    digest.update(json.dumps(list(row.shape), separators=(",", ":")).encode("ascii"))
    digest.update(row.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _named_tensor_digest(names: Sequence[str], rows: Sequence[torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name, row in zip(names, rows, strict=True):
        digest.update(name.encode("utf-8"))
        digest.update(_tensor_digest(row).encode("ascii"))
    return digest.hexdigest()


def _actor_rows(model: nn.Module) -> tuple[torch.Tensor, ...]:
    return tuple(parameter.detach().clone() for parameter in actor_parameters(model))


def _actor_digest(model: nn.Module) -> str:
    return _named_tensor_digest(ACTOR_PARAMETER_NAMES, _actor_rows(model))


def _all_finite(rows: Sequence[torch.Tensor]) -> bool:
    return all(bool(torch.isfinite(row).all()) for row in rows)


_ADAM_FLAGS = (
    "lr", "betas", "eps", "weight_decay", "amsgrad", "maximize",
    "foreach", "capturable", "differentiable", "fused",
    "decoupled_weight_decay",
)


def optimizer_hyperparameters(optimizer: torch.optim.Optimizer) -> dict[str, object]:
    if type(optimizer) is not torch.optim.Adam or len(optimizer.param_groups) != 1:
        raise G52InvariantError("optimizer_class_or_group_count_invalid")
    group = optimizer.param_groups[0]
    return {name: group.get(name) for name in _ADAM_FLAGS}


def make_actor_adam(model: nn.Module) -> torch.optim.Adam:
    optimizer = torch.optim.Adam(
        actor_parameters(model),
        lr=g40.LEARNING_RATE,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
        amsgrad=False,
    )
    if optimizer.state:
        raise G52InvariantError("fresh_Adam_not_empty")
    return optimizer


def make_fresh_phase_A_ancestor(
    *, member_capacity: int, initialization_seed: int
) -> tuple[g51.G51NoBaselinePhaseAProjection, torch.optim.Adam]:
    # make_phase_A_models performs one fresh G50 initialization; projection and
    # copies consume no RNG.  Only its null/single-immediate object is retained.
    inherited = g50.make_phase_A_models(
        member_capacity=int(member_capacity), initialization_seed=int(initialization_seed)
    )
    model = g51.G51NoBaselinePhaseAProjection(inherited[g50.NULL_ARM])
    if hasattr(model, "credit_baselines") or any(
        name.startswith("credit_baselines.") for name in model.state_dict()
    ):
        raise G52InvariantError("phase_A_baseline_package_present")
    optimizer = make_actor_adam(model)
    return model, optimizer


def optimize_phase_A_update(
    model: g51.G51NoBaselinePhaseAProjection,
    optimizer: torch.optim.Optimizer,
    trajectory: Any,
    *,
    update_index: int,
) -> dict[str, object]:
    if trajectory.rewards.numel() != NORMALIZATION_ROWS:
        raise ValueError("G52 Phase-A update requires one 8x48 batch")
    if _parameter_names(model, _optimizer_parameters(optimizer)) != ACTOR_PARAMETER_NAMES:
        raise G52InvariantError("phase_A_optimizer_parameter_inventory_invalid")
    normalized = g49._normalize_single(g49._single_immediate_target(trajectory.rewards))
    actor_trajectory = g47._actor_only_trajectory_view(trajectory)
    records: list[dict[str, object]] = []
    for pass_index in range(PPO_PASSES):
        rng_before = torch.random.get_rng_state().clone()
        plan = g51._reduced_plan(model, actor_trajectory, normalized.normalized)
        if not torch.equal(rng_before, torch.random.get_rng_state()):
            raise G52InvariantError("phase_A_plan_consumed_RNG")
        g51._apply_reduced_pass(model, optimizer, plan.assigned)
        records.append(
            {
                "pass_index": pass_index,
                "target_digest": _tensor_digest(normalized.target),
                "normalized_target_digest": _tensor_digest(normalized.normalized),
                "assigned_gradient_digest": _named_tensor_digest(
                    ACTOR_PARAMETER_NAMES, plan.assigned
                ),
                "optimizer_step": (int(update_index) * PPO_PASSES) + pass_index + 1,
            }
        )
    return {
        "update_index": int(update_index),
        "PPO_passes": PPO_PASSES,
        "optimizer_steps": PPO_PASSES,
        "records": records,
        "passed": True,
    }


def _validate_state_row(
    row: object, parameter: nn.Parameter, *, expected_step: int
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    if not isinstance(row, Mapping) or set(row) != {"exp_avg", "exp_avg_sq", "step"}:
        raise G52InvariantError("malformed_Adam_state_row")
    step, exp_avg, exp_avg_sq = row.get("step"), row.get("exp_avg"), row.get("exp_avg_sq")
    if not all(isinstance(value, torch.Tensor) for value in (step, exp_avg, exp_avg_sq)):
        raise G52InvariantError("non_tensor_Adam_state")
    assert isinstance(step, torch.Tensor)
    assert isinstance(exp_avg, torch.Tensor)
    assert isinstance(exp_avg_sq, torch.Tensor)
    if step.shape != torch.Size([]) or step.device != parameter.device:
        raise G52InvariantError("Adam_step_shape_or_device_invalid")
    if step.dtype != torch.float32 or not bool(torch.isfinite(step)):
        raise G52InvariantError("Adam_step_nonfinite_or_dtype_invalid")
    if float(step.detach().cpu()) != float(expected_step):
        raise G52InvariantError("Adam_step_invalid")
    for name, value in (("exp_avg", exp_avg), ("exp_avg_sq", exp_avg_sq)):
        if value.shape != parameter.shape:
            raise G52InvariantError(f"{name}_shape_invalid")
        if value.dtype != parameter.dtype:
            raise G52InvariantError(f"{name}_dtype_invalid")
        if value.device != parameter.device:
            raise G52InvariantError(f"{name}_device_invalid")
        if not bool(torch.isfinite(value).all()):
            raise G52InvariantError(f"{name}_nonfinite")
    if bool(torch.any(exp_avg_sq < 0)):
        raise G52InvariantError("exp_avg_sq_negative")
    return step, exp_avg, exp_avg_sq


def snapshot_actor_adam_state(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    *,
    expected_step: int = EXPECTED_FORMAL_BOUNDARY_STEP,
) -> dict[str, dict[str, torch.Tensor]]:
    parameters = actor_parameters(model)
    if type(optimizer) is not torch.optim.Adam or len(optimizer.param_groups) != 1:
        raise G52InvariantError("source_optimizer_class_invalid")
    optimizer_parameters = _optimizer_parameters(optimizer)
    names = _parameter_names(model, optimizer_parameters)
    if names != ACTOR_PARAMETER_NAMES or optimizer_parameters != parameters:
        raise G52InvariantError("source_optimizer_inventory_or_order_invalid")
    if set(optimizer.state) != set(parameters):
        raise G52InvariantError("source_optimizer_missing_extra_or_foreign_state")
    result: dict[str, dict[str, torch.Tensor]] = {}
    live_storages: list[int] = []
    for name, parameter in zip(ACTOR_PARAMETER_NAMES, parameters, strict=True):
        step, exp_avg, exp_avg_sq = _validate_state_row(
            optimizer.state[parameter], parameter, expected_step=int(expected_step)
        )
        live_storages.extend(
            storage
            for value in (step, exp_avg, exp_avg_sq)
            if (storage := _tensor_storage_id(value)) is not None
        )
        result[name] = {
            "exp_avg": exp_avg.detach().clone(),
            "exp_avg_sq": exp_avg_sq.detach().clone(),
            "step": step.detach().clone(),
        }
    if len(live_storages) != len(set(live_storages)):
        raise G52InvariantError("source_Adam_state_contains_shared_storage")
    storages = [
        _tensor_storage_id(value)
        for row in result.values()
        for value in row.values()
        if value.numel()
    ]
    if len(storages) != len(set(storages)):
        raise G52InvariantError("snapshot_contains_shared_storage")
    return result


def adam_state_digest(state: Mapping[str, Mapping[str, torch.Tensor]]) -> str:
    if tuple(state) != ACTOR_PARAMETER_NAMES:
        raise G52InvariantError("Adam_state_name_or_order_invalid")
    digest = hashlib.sha256()
    for name in ACTOR_PARAMETER_NAMES:
        row = state[name]
        if tuple(row) != ("exp_avg", "exp_avg_sq", "step"):
            raise G52InvariantError("Adam_state_row_order_invalid")
        digest.update(name.encode("utf-8"))
        for key in ("exp_avg", "exp_avg_sq", "step"):
            digest.update(key.encode("ascii"))
            digest.update(_tensor_digest(row[key]).encode("ascii"))
    return digest.hexdigest()


def install_carried_adam_state(
    *,
    source_model: nn.Module,
    source_optimizer: torch.optim.Optimizer,
    destination_model: nn.Module,
    destination_optimizer: torch.optim.Optimizer,
    expected_step: int = EXPECTED_FORMAL_BOUNDARY_STEP,
) -> dict[str, object]:
    """Install exact actor-Adam state after complete fail-closed validation."""

    rng_before = torch.random.get_rng_state().clone()
    source_parameters = actor_parameters(source_model)
    destination_parameters = actor_parameters(destination_model)
    if source_model is destination_model or source_optimizer is destination_optimizer:
        raise G52InvariantError("source_destination_object_alias")
    if _module_storage_ids(source_model) & _module_storage_ids(destination_model):
        raise G52InvariantError("source_destination_model_storage_alias")
    if _parameter_names(source_model, _optimizer_parameters(source_optimizer)) != ACTOR_PARAMETER_NAMES:
        raise G52InvariantError("source_optimizer_foreign_or_reordered_parameter")
    if _parameter_names(destination_model, _optimizer_parameters(destination_optimizer)) != ACTOR_PARAMETER_NAMES:
        raise G52InvariantError("destination_optimizer_foreign_or_reordered_parameter")
    if tuple(parameter.shape for parameter in source_parameters) != tuple(
        parameter.shape for parameter in destination_parameters
    ):
        raise G52InvariantError("source_destination_shape_bijection_invalid")
    if tuple(parameter.dtype for parameter in source_parameters) != tuple(
        parameter.dtype for parameter in destination_parameters
    ):
        raise G52InvariantError("source_destination_dtype_bijection_invalid")
    if tuple(parameter.device for parameter in source_parameters) != tuple(
        parameter.device for parameter in destination_parameters
    ):
        raise G52InvariantError("source_destination_device_bijection_invalid")
    if optimizer_hyperparameters(source_optimizer) != optimizer_hyperparameters(destination_optimizer):
        raise G52InvariantError("Adam_hyperparameters_or_flags_differ")
    if destination_optimizer.state:
        raise G52InvariantError("destination_Adam_not_empty")

    snapshot = snapshot_actor_adam_state(
        source_model, source_optimizer, expected_step=int(expected_step)
    )
    source_state_storages = {
        storage
        for parameter in source_parameters
        for value in source_optimizer.state[parameter].values()
        if isinstance(value, torch.Tensor)
        if (storage := _tensor_storage_id(value)) is not None
    }
    for name, destination_parameter in zip(
        ACTOR_PARAMETER_NAMES, destination_parameters, strict=True
    ):
        row = snapshot[name]
        destination_optimizer.state[destination_parameter] = {
            "step": row["step"].detach().clone(),
            "exp_avg": row["exp_avg"].detach().clone(),
            "exp_avg_sq": row["exp_avg_sq"].detach().clone(),
        }
    installed = snapshot_actor_adam_state(
        destination_model, destination_optimizer, expected_step=int(expected_step)
    )
    destination_state_storages = {
        storage
        for parameter in destination_parameters
        for value in destination_optimizer.state[parameter].values()
        if isinstance(value, torch.Tensor)
        if (storage := _tensor_storage_id(value)) is not None
    }
    if source_state_storages & destination_state_storages:
        raise G52InvariantError("carried_Adam_storage_alias")
    if adam_state_digest(snapshot) != adam_state_digest(installed):
        raise G52InvariantError("carried_Adam_bytes_differ")
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise G52InvariantError("Adam_install_consumed_RNG")
    nonzero = any(
        bool(torch.any(value != 0))
        for row in installed.values()
        for value in row.values()
    )
    if not nonzero:
        raise G52InvariantError("carried_Adam_state_all_zero")
    return {
        "parameter_names": list(ACTOR_PARAMETER_NAMES),
        "expected_step": int(expected_step),
        "source_state_digest": adam_state_digest(snapshot),
        "installed_state_digest": adam_state_digest(installed),
        "hyperparameters": optimizer_hyperparameters(destination_optimizer),
        "source_destination_storage_disjoint": True,
        "install_RNG_consumption": 0,
        "install_optimizer_steps": 0,
        "carried_state_finite_nonzero": True,
        "passed": True,
    }


def project_phase_B_arms(
    phase_A_model: g51.G51NoBaselinePhaseAProjection,
    phase_A_optimizer: torch.optim.Optimizer,
    *,
    completed_phase_A_updates: int,
    expected_step: int,
) -> tuple[
    dict[str, g50.G50PhaseBProjection],
    dict[str, torch.optim.Adam],
    dict[str, object],
]:
    snapshot = snapshot_actor_adam_state(
        phase_A_model, phase_A_optimizer, expected_step=int(expected_step)
    )
    ancestor_actor_digest = _actor_digest(phase_A_model)
    rng_before = torch.random.get_rng_state().clone()
    models = {arm: g50.G50PhaseBProjection(phase_A_model) for arm in ARMS}
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise G52InvariantError("phase_B_projection_consumed_RNG")
    if _module_storage_ids(models[RESET_ARM]) & _module_storage_ids(models[CARRY_ARM]):
        raise G52InvariantError("phase_B_arm_model_storage_alias")
    if _actor_digest(models[RESET_ARM]) != ancestor_actor_digest or _actor_digest(
        models[CARRY_ARM]
    ) != ancestor_actor_digest:
        raise G52InvariantError("phase_B_projection_changed_actor_bytes")
    optimizers = {arm: make_actor_adam(models[arm]) for arm in ARMS}
    carry_install = install_carried_adam_state(
        source_model=phase_A_model,
        source_optimizer=phase_A_optimizer,
        destination_model=models[CARRY_ARM],
        destination_optimizer=optimizers[CARRY_ARM],
        expected_step=int(expected_step),
    )
    if optimizers[RESET_ARM].state:
        raise G52InvariantError("RESET_Adam_not_empty_at_boundary")
    evidence = {
        "completed_phase_A_updates": int(completed_phase_A_updates),
        "expected_boundary_step": int(expected_step),
        "actor_parameter_names": list(ACTOR_PARAMETER_NAMES),
        "actor_inventory_count": len(ACTOR_PARAMETER_NAMES),
        "ancestor_actor_digest": ancestor_actor_digest,
        "phase_A_Adam_digest": adam_state_digest(snapshot),
        "projected_actor_digests": {arm: _actor_digest(models[arm]) for arm in ARMS},
        "RESET_empty_Adam": True,
        "CARRY_install": carry_install,
        "optimizer_hyperparameters_equal": optimizer_hyperparameters(optimizers[RESET_ARM])
        == optimizer_hyperparameters(optimizers[CARRY_ARM]),
        "projection_RNG_consumption": 0,
        "projection_optimizer_steps": 0,
        "model_storage_disjoint": True,
        "passed": True,
    }
    return models, optimizers, evidence


def activation_ratio(
    reset_delta: Sequence[torch.Tensor], carry_delta: Sequence[torch.Tensor]
) -> dict[str, object]:
    if len(reset_delta) != len(carry_delta) or not reset_delta:
        return {"valid": False, "reason": "delta_inventory_invalid"}
    reset64 = tuple(row.detach().to(torch.float64) for row in reset_delta)
    carry64 = tuple(row.detach().to(torch.float64) for row in carry_delta)
    if not _all_finite((*reset64, *carry64)):
        return {"valid": False, "reason": "nonfinite_delta"}
    reset_norm = float(torch.sqrt(sum(row.square().sum() for row in reset64)).cpu())
    carry_norm = float(torch.sqrt(sum(row.square().sum() for row in carry64)).cpu())
    numerator = float(
        torch.sqrt(sum((left - right).square().sum() for left, right in zip(reset64, carry64))).cpu()
    )
    denominator = max(reset_norm, carry_norm)
    if not all(math.isfinite(value) for value in (reset_norm, carry_norm, numerator, denominator)):
        return {"valid": False, "reason": "nonfinite_norm"}
    if denominator == 0.0:
        if numerator != 0.0:
            return {
                "valid": False,
                "reason": "zero_denominator_nonzero_numerator",
                "reset_norm": reset_norm,
                "carry_norm": carry_norm,
                "numerator": numerator,
                "denominator": denominator,
            }
        q_r = 0.0
    else:
        q_r = numerator / denominator
    if not math.isfinite(q_r):
        return {"valid": False, "reason": "nonfinite_q_r"}
    return {
        "valid": True,
        "reason": None,
        "reset_norm": reset_norm,
        "carry_norm": carry_norm,
        "numerator": numerator,
        "denominator": denominator,
        "q_r": q_r,
    }


def _canonical_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
            "utf-8"
        )
    ).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _raw_optimizer_state_digest(
    model: nn.Module, optimizer: torch.optim.Optimizer
) -> str:
    """Bind every live Adam row, including malformed/nonfinite rows.

    This routine deliberately does not call the fail-closed installer validator:
    post-step scientific invalidity must still be representable by a sealed
    structural certificate.
    """

    model_parameters = tuple(actor_parameters(model))
    by_id = {id(parameter): name for name, parameter in zip(ACTOR_PARAMETER_NAMES, model_parameters)}
    digest = hashlib.sha256()
    for index, parameter in enumerate(_optimizer_parameters(optimizer)):
        name = by_id.get(id(parameter), f"<foreign:{index}>")
        digest.update(name.encode("utf-8"))
    state_rows = sorted(
        optimizer.state.items(),
        key=lambda item: by_id.get(id(item[0]), f"<foreign:{id(item[0])}>"),
    )
    for parameter, row in state_rows:
        name = by_id.get(id(parameter), f"<foreign:{id(parameter)}>")
        digest.update(name.encode("utf-8"))
        if not isinstance(row, Mapping):
            digest.update(repr(row).encode("utf-8"))
            continue
        for key in sorted(row, key=str):
            digest.update(str(key).encode("utf-8"))
            value = row[key]
            if isinstance(value, torch.Tensor):
                digest.update(_tensor_digest(value).encode("ascii"))
            else:
                digest.update(repr(value).encode("utf-8"))
    return digest.hexdigest()


def inspect_post_step_adam_state(
    *,
    arm: str,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    expected_step: int,
) -> dict[str, object]:
    """Return a JSON-safe, complete post-step Adam inventory certificate.

    Malformed and nonfinite state is recorded as operationally invalid instead
    of raising.  This is essential to distinguish scientific boundary failure
    from artifact corruption.
    """

    parameters = actor_parameters(model)
    optimizer_parameters = _optimizer_parameters(optimizer)
    optimizer_names = _parameter_names(model, optimizer_parameters)
    retained_names = _parameter_names(model, tuple(optimizer.state))
    row_keys: dict[str, list[str]] = {}
    step_values: dict[str, int | None] = {}
    row_schema_exact = True
    shapes_match = True
    dtypes_match = True
    devices_match = True
    finite = True
    nonnegative_second_moment = True
    steps_exact = True
    state_storage_ids: list[int] = []
    model_storages = _module_storage_ids(model)
    for name, parameter in zip(ACTOR_PARAMETER_NAMES, parameters, strict=True):
        row = optimizer.state.get(parameter)
        if not isinstance(row, Mapping):
            row_keys[name] = []
            step_values[name] = None
            row_schema_exact = False
            steps_exact = False
            finite = False
            continue
        row_keys[name] = sorted(str(key) for key in row)
        if set(row) != {"step", "exp_avg", "exp_avg_sq"}:
            row_schema_exact = False
        step = row.get("step")
        exp_avg = row.get("exp_avg")
        exp_avg_sq = row.get("exp_avg_sq")
        if not isinstance(step, torch.Tensor):
            step_values[name] = None
            steps_exact = False
            finite = False
            row_schema_exact = False
        else:
            step_ok = (
                step.shape == torch.Size([])
                and step.dtype == torch.float32
                and step.device == parameter.device
                and bool(torch.isfinite(step))
            )
            value = int(float(step.detach().cpu())) if step_ok else None
            step_values[name] = value
            steps_exact = steps_exact and step_ok and value == int(expected_step)
            shapes_match = shapes_match and step.shape == torch.Size([])
            dtypes_match = dtypes_match and step.dtype == torch.float32
            devices_match = devices_match and step.device == parameter.device
            finite = finite and bool(torch.isfinite(step).all())
            if (storage := _tensor_storage_id(step)) is not None:
                state_storage_ids.append(storage)
        for value, second_moment in ((exp_avg, False), (exp_avg_sq, True)):
            if not isinstance(value, torch.Tensor):
                row_schema_exact = False
                shapes_match = False
                dtypes_match = False
                devices_match = False
                finite = False
                if second_moment:
                    nonnegative_second_moment = False
                continue
            shapes_match = shapes_match and value.shape == parameter.shape
            dtypes_match = dtypes_match and value.dtype == parameter.dtype
            devices_match = devices_match and value.device == parameter.device
            finite = finite and bool(torch.isfinite(value).all())
            if second_moment:
                nonnegative_second_moment = nonnegative_second_moment and bool(
                    torch.isfinite(value).all() and torch.all(value >= 0)
                )
            if (storage := _tensor_storage_id(value)) is not None:
                state_storage_ids.append(storage)
    exact_optimizer_inventory = (
        optimizer_names == ACTOR_PARAMETER_NAMES
        and optimizer_parameters == parameters
        and len(set(map(id, optimizer_parameters))) == len(parameters)
    )
    exact_retained_inventory = (
        retained_names == ACTOR_PARAMETER_NAMES and set(optimizer.state) == set(parameters)
    )
    storage_unique = len(state_storage_ids) == len(set(state_storage_ids))
    state_model_storage_disjoint = not (set(state_storage_ids) & model_storages)
    predicates = {
        "Adam_class_exact": type(optimizer) is torch.optim.Adam,
        "single_parameter_group": len(optimizer.param_groups) == 1,
        "optimizer_parameter_inventory_exact": exact_optimizer_inventory,
        "retained_state_inventory_exact": exact_retained_inventory,
        "state_row_schema_exact": row_schema_exact,
        "state_shapes_match": shapes_match,
        "state_dtypes_match": dtypes_match,
        "state_devices_match": devices_match,
        "state_finite": finite,
        "exp_avg_sq_nonnegative": nonnegative_second_moment,
        "steps_exact": steps_exact,
        "state_storage_unique": storage_unique,
        "state_model_storage_disjoint": state_model_storage_disjoint,
    }
    operationally_valid = all(value is True for value in predicates.values())
    return {
        "arm": arm,
        "expected_step": int(expected_step),
        "parameter_names": list(ACTOR_PARAMETER_NAMES),
        "optimizer_parameter_names": list(optimizer_names),
        "retained_state_names": list(retained_names),
        "state_keys_by_name": row_keys,
        "step_values": step_values,
        "state_digest": _raw_optimizer_state_digest(model, optimizer),
        "hyperparameters": optimizer_hyperparameters(optimizer)
        if type(optimizer) is torch.optim.Adam and len(optimizer.param_groups) == 1
        else None,
        "predicates": predicates,
        "operationally_valid": operationally_valid,
        "state_storage_ids": state_storage_ids,
    }


def _validate_post_step_adam_evidence(
    value: object, *, arm: str, expected_step: int
) -> bool:
    if not isinstance(value, Mapping):
        return False
    predicates = value.get("predicates")
    if not isinstance(predicates, Mapping):
        return False
    expected_predicates = {
        "Adam_class_exact", "single_parameter_group",
        "optimizer_parameter_inventory_exact", "retained_state_inventory_exact",
        "state_row_schema_exact", "state_shapes_match", "state_dtypes_match",
        "state_devices_match", "state_finite", "exp_avg_sq_nonnegative",
        "steps_exact", "state_storage_unique", "state_model_storage_disjoint",
    }
    operational = set(predicates) == expected_predicates and all(
        predicates[name] is True for name in expected_predicates
    )
    return bool(
        value.get("arm") == arm
        and value.get("expected_step") == int(expected_step)
        and value.get("parameter_names") == list(ACTOR_PARAMETER_NAMES)
        and isinstance(value.get("optimizer_parameter_names"), list)
        and isinstance(value.get("retained_state_names"), list)
        and isinstance(value.get("state_keys_by_name"), Mapping)
        and isinstance(value.get("step_values"), Mapping)
        and _is_sha256(value.get("state_digest"))
        and (
            "state_storage_ids" not in value
            or isinstance(value.get("state_storage_ids"), list)
        )
        and value.get("operationally_valid") is operational
    )


def build_boundary_activation_certificate(
    *,
    pre_step_rows: Sequence[torch.Tensor],
    post_step_rows: Mapping[str, Sequence[torch.Tensor]],
    batch_digest: str,
    target_digest: str,
    normalized_target_digest: str,
    assigned_gradient_digests: Mapping[str, str],
    reset_empty_state: bool,
    carry_state_digest: str,
    carried_state_finite_nonzero: bool,
    post_step_optimizer_state: Mapping[str, Mapping[str, object]],
    post_step_optimizer_storage_disjoint: bool,
    carry_boundary_step: int,
) -> dict[str, object]:
    if len(pre_step_rows) != len(ACTOR_PARAMETER_NAMES) or tuple(post_step_rows) != ARMS:
        raise G52InvariantError("activation_certificate_inventory_invalid")
    if any(len(post_step_rows[arm]) != len(ACTOR_PARAMETER_NAMES) for arm in ARMS):
        raise G52InvariantError("activation_certificate_post_inventory_invalid")
    pre = tuple(row.detach().clone() for row in pre_step_rows)
    post = {arm: tuple(row.detach().clone() for row in post_step_rows[arm]) for arm in ARMS}
    if any(
        after.shape != before.shape
        or after.dtype != before.dtype
        or after.device != before.device
        for arm in ARMS
        for before, after in zip(pre, post[arm], strict=True)
    ):
        raise G52InvariantError("activation_certificate_shape_dtype_device_bijection_invalid")
    deltas = {
        arm: tuple(after.to(torch.float64) - before.to(torch.float64) for before, after in zip(pre, post[arm]))
        for arm in ARMS
    }
    ratio = activation_ratio(deltas[RESET_ARM], deltas[CARRY_ARM])
    finite_parameters = _all_finite((*pre, *post[RESET_ARM], *post[CARRY_ARM]))
    post_bytes_differ = _named_tensor_digest(ACTOR_PARAMETER_NAMES, post[RESET_ARM]) != _named_tensor_digest(
        ACTOR_PARAMETER_NAMES, post[CARRY_ARM]
    )
    gradients_equal = bool(
        tuple(assigned_gradient_digests) == ARMS
        and assigned_gradient_digests[RESET_ARM] == assigned_gradient_digests[CARRY_ARM]
    )
    carry_post_step = int(carry_boundary_step) + 1
    reset_optimizer_row = post_step_optimizer_state.get(RESET_ARM)
    reset_optimizer_valid = bool(
        _validate_post_step_adam_evidence(
            reset_optimizer_row, arm=RESET_ARM, expected_step=1
        )
        and reset_optimizer_row.get("operationally_valid") is True
    )
    carry_optimizer_valid = bool(
        _validate_post_step_adam_evidence(
            post_step_optimizer_state.get(CARRY_ARM),
            arm=CARRY_ARM,
            expected_step=carry_post_step,
        )
        and post_step_optimizer_state.get(CARRY_ARM, {}).get("operationally_valid")
        is True
    )
    post_optimizer_hyperparameters_equal = bool(
        post_step_optimizer_state.get(RESET_ARM, {}).get("hyperparameters")
        == post_step_optimizer_state.get(CARRY_ARM, {}).get("hyperparameters")
        and post_step_optimizer_state.get(RESET_ARM, {}).get("hyperparameters")
        is not None
    )
    operationally_valid = bool(
        ratio.get("valid") is True
        and finite_parameters
        and reset_empty_state
        and carried_state_finite_nonzero
        and gradients_equal
        and _is_sha256(batch_digest)
        and _is_sha256(target_digest)
        and _is_sha256(normalized_target_digest)
        and _is_sha256(carry_state_digest)
        and reset_optimizer_valid
        and carry_optimizer_valid
        and post_step_optimizer_storage_disjoint
        and post_optimizer_hyperparameters_equal
    )
    q_r = ratio.get("q_r") if ratio.get("valid") is True else None
    active = bool(
        operationally_valid and isinstance(q_r, float) and q_r > 0.0 and post_bytes_differ
    )
    body: dict[str, object] = {
        "certificate_kind": "G52_ACTUAL_FIRST_PHASE_B_ADAM_BOUNDARY_V1",
        "algorithm_id": ALGORITHM_ID,
        "parameter_names": list(ACTOR_PARAMETER_NAMES),
        "pre_step_actor_digest": _named_tensor_digest(ACTOR_PARAMETER_NAMES, pre),
        "first_batch_digest": batch_digest,
        "target_digest": target_digest,
        "normalized_target_digest": normalized_target_digest,
        "assigned_gradient_digests": dict(assigned_gradient_digests),
        "RESET_empty_Adam": bool(reset_empty_state),
        "CARRY_installed_Adam_digest": carry_state_digest,
        "CARRY_boundary_step": int(carry_boundary_step),
        "post_step_optimizer_state": {
            arm: {
                key: copy.deepcopy(value)
                for key, value in post_step_optimizer_state[arm].items()
                if key != "state_storage_ids"
            }
            for arm in ARMS
        },
        "post_step_actor_digests": {
            arm: _named_tensor_digest(ACTOR_PARAMETER_NAMES, post[arm]) for arm in ARMS
        },
        "delta_digests": {
            arm: _named_tensor_digest(ACTOR_PARAMETER_NAMES, deltas[arm]) for arm in ARMS
        },
        "norms": {
            key: ratio.get(key)
            for key in ("reset_norm", "carry_norm", "numerator", "denominator", "q_r")
        },
        "predicates": {
            "exact_parameter_inventory": True,
            "pre_and_post_parameters_finite": finite_parameters,
            "first_batch_identical": True,
            "normalized_target_identical": True,
            "assigned_gradients_identical": gradients_equal,
            "RESET_state_empty": bool(reset_empty_state),
            "CARRY_state_finite_nonzero": bool(carried_state_finite_nonzero),
            "deltas_finite": ratio.get("reason") != "nonfinite_delta",
            "norms_and_q_finite": ratio.get("valid") is True,
            "denominator_rule_valid": ratio.get("reason")
            != "zero_denominator_nonzero_numerator",
            "post_step_bytes_differ": post_bytes_differ,
            "RESET_post_step_Adam_valid_at_step_1": reset_optimizer_valid,
            "CARRY_post_step_Adam_valid_at_boundary_plus_1": carry_optimizer_valid,
            "post_step_optimizer_storage_disjoint": bool(
                post_step_optimizer_storage_disjoint
            ),
            "post_step_optimizer_hyperparameters_equal": post_optimizer_hyperparameters_equal,
        },
        "boundary_operationally_valid": operationally_valid,
        "scientifically_valid": active,
        "valid": active,
        "active": active,
        "composite_state_only_no_component_attribution": True,
    }
    body["certificate_digest"] = _canonical_digest(body)
    return body


def validate_boundary_activation_certificate(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    body = dict(value)
    seal = body.pop("certificate_digest", None)
    if not isinstance(seal, str) or seal != _canonical_digest(body):
        return False
    predicates = body.get("predicates")
    norms = body.get("norms")
    if not isinstance(predicates, Mapping) or not isinstance(norms, Mapping):
        return False
    q_r = norms.get("q_r")
    finite_q = isinstance(q_r, (int, float)) and not isinstance(q_r, bool) and math.isfinite(float(q_r))
    required_operational = (
        "exact_parameter_inventory", "pre_and_post_parameters_finite",
        "first_batch_identical", "normalized_target_identical",
        "assigned_gradients_identical", "RESET_state_empty",
        "CARRY_state_finite_nonzero", "deltas_finite",
        "norms_and_q_finite", "denominator_rule_valid",
        "RESET_post_step_Adam_valid_at_step_1",
        "CARRY_post_step_Adam_valid_at_boundary_plus_1",
        "post_step_optimizer_storage_disjoint",
        "post_step_optimizer_hyperparameters_equal",
    )
    post_state = body.get("post_step_optimizer_state")
    if not isinstance(post_state, Mapping) or set(post_state) != set(ARMS):
        return False
    carry_row = post_state.get(CARRY_ARM)
    if not isinstance(carry_row, Mapping):
        return False
    carry_boundary_step = body.get("CARRY_boundary_step")
    state_evidence_structural = (
        _validate_post_step_adam_evidence(
            post_state.get(RESET_ARM), arm=RESET_ARM, expected_step=1
        )
        and isinstance(carry_boundary_step, int)
        and not isinstance(carry_boundary_step, bool)
        and _validate_post_step_adam_evidence(
            carry_row, arm=CARRY_ARM, expected_step=int(carry_boundary_step) + 1
        )
    )
    expected_operational = (
        all(predicates.get(name) is True for name in required_operational)
        and finite_q
        and state_evidence_structural
    )
    expected_active = bool(
        expected_operational
        and float(q_r) > 0.0
        and predicates.get("post_step_bytes_differ") is True
    )
    return bool(
        body.get("certificate_kind") == "G52_ACTUAL_FIRST_PHASE_B_ADAM_BOUNDARY_V1"
        and body.get("algorithm_id") == ALGORITHM_ID
        and body.get("parameter_names") == list(ACTOR_PARAMETER_NAMES)
        and body.get("boundary_operationally_valid") is expected_operational
        and body.get("scientifically_valid") is expected_active
        and body.get("valid") is expected_active
        and body.get("active") is expected_active
        and body.get("composite_state_only_no_component_attribution") is True
    )


def _trajectory_digest(trajectory: Any) -> str:
    digest = hashlib.sha256()
    for name in (
        "observations", "active_mask", "actions", "pre_tanh_actions", "log_probs", "rewards"
    ):
        value = getattr(trajectory, name, None)
        if isinstance(value, torch.Tensor):
            digest.update(name.encode("ascii"))
            digest.update(_tensor_digest(value).encode("ascii"))
    return digest.hexdigest()


def execute_first_phase_B_update(
    models: Mapping[str, g50.G50PhaseBProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectory: Any,
    *,
    carry_install_evidence: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS:
        raise ValueError("G52 first Phase-B update requires exact arms")
    actor_trajectory = g47._actor_only_trajectory_view(trajectory)
    pre = _actor_rows(models[RESET_ARM])
    if _named_tensor_digest(ACTOR_PARAMETER_NAMES, pre) != _actor_digest(models[CARRY_ARM]):
        raise G52InvariantError("pre_first_step_actor_bytes_differ")
    reset_empty = not optimizers[RESET_ARM].state
    normalized = g49._normalize_single(g49._single_immediate_target(actor_trajectory.rewards))
    # Both first-pass plans are completely materialized before either step.
    plans = {
        arm: g49._single_probe(models[arm], actor_trajectory, normalized.normalized)
        for arm in ARMS
    }
    gradient_digests = {
        arm: _named_tensor_digest(ACTOR_PARAMETER_NAMES, plans[arm].assigned) for arm in ARMS
    }
    if gradient_digests[RESET_ARM] != gradient_digests[CARRY_ARM]:
        raise G52InvariantError("first_step_assigned_gradients_differ")
    carry_digest = str(carry_install_evidence.get("installed_state_digest", ""))
    carry_boundary_step = carry_install_evidence.get("expected_step")
    if not isinstance(carry_boundary_step, int) or isinstance(carry_boundary_step, bool):
        raise G52InvariantError("carry_boundary_step_missing")
    for arm in ARMS:
        g49._apply_pass(models[arm], optimizers[arm], plans[arm].assigned)
    post = {arm: _actor_rows(models[arm]) for arm in ARMS}
    post_optimizer_state = {
        RESET_ARM: inspect_post_step_adam_state(
            arm=RESET_ARM,
            model=models[RESET_ARM],
            optimizer=optimizers[RESET_ARM],
            expected_step=1,
        ),
        CARRY_ARM: inspect_post_step_adam_state(
            arm=CARRY_ARM,
            model=models[CARRY_ARM],
            optimizer=optimizers[CARRY_ARM],
            expected_step=int(carry_boundary_step) + 1,
        ),
    }
    reset_state_storages = set(post_optimizer_state[RESET_ARM]["state_storage_ids"])
    carry_state_storages = set(post_optimizer_state[CARRY_ARM]["state_storage_ids"])
    optimizer_storage_disjoint = not (reset_state_storages & carry_state_storages)
    certificate = build_boundary_activation_certificate(
        pre_step_rows=pre,
        post_step_rows=post,
        batch_digest=_trajectory_digest(actor_trajectory),
        target_digest=_tensor_digest(normalized.target),
        normalized_target_digest=_tensor_digest(normalized.normalized),
        assigned_gradient_digests=gradient_digests,
        reset_empty_state=reset_empty,
        carry_state_digest=carry_digest,
        carried_state_finite_nonzero=carry_install_evidence.get("carried_state_finite_nonzero")
        is True,
        post_step_optimizer_state=post_optimizer_state,
        post_step_optimizer_storage_disjoint=optimizer_storage_disjoint,
        carry_boundary_step=int(carry_boundary_step),
    )
    if not validate_boundary_activation_certificate(certificate):
        raise G52InvariantError("first_step_activation_certificate_invalid")
    # The second PPO pass uses the same realized batch, but each now-diverged
    # arm gets its own newly materialized on-policy objective plan.
    second_plans = {
        arm: g49._single_probe(models[arm], actor_trajectory, normalized.normalized)
        for arm in ARMS
    }
    for arm in ARMS:
        g49._apply_pass(models[arm], optimizers[arm], second_plans[arm].assigned)
    update = {
        "update_index": 0,
        "first_batch_materialized_before_either_step": True,
        "both_first_step_plans_materialized_before_either_step": True,
        "first_step_actor_batch_target_gradient_equal": True,
        "first_step_certificate": certificate,
        "PPO_passes_per_arm": PPO_PASSES,
        "optimizer_steps_per_arm": PPO_PASSES,
        "certificate_structurally_valid": True,
        "boundary_operationally_valid": certificate["boundary_operationally_valid"],
        "treatment_active": certificate["active"],
        "passed": True,
    }
    return update, certificate


def optimize_phase_B_update(
    models: Mapping[str, g50.G50PhaseBProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, Any],
    *,
    update_index: int,
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS or tuple(trajectories) != ARMS:
        raise ValueError("G52 later Phase-B update requires exact ordered arms")
    records: list[dict[str, object]] = []
    for pass_index in range(PPO_PASSES):
        plans: dict[str, Any] = {}
        normalizations: dict[str, Any] = {}
        for arm in ARMS:
            row = g47._actor_only_trajectory_view(trajectories[arm])
            normalizations[arm] = g49._normalize_single(g49._single_immediate_target(row.rewards))
            plans[arm] = g49._single_probe(
                models[arm], row, normalizations[arm].normalized
            )
        for arm in ARMS:
            g49._apply_pass(models[arm], optimizers[arm], plans[arm].assigned)
        records.append(
            {
                "pass_index": pass_index,
                "plans_materialized_before_either_step": True,
                "arm_specific_trajectory_digests": {
                    arm: _trajectory_digest(g47._actor_only_trajectory_view(trajectories[arm]))
                    for arm in ARMS
                },
                "arm_specific_target_digests": {
                    arm: _tensor_digest(normalizations[arm].normalized) for arm in ARMS
                },
            }
        )
    return {
        "update_index": int(update_index),
        "separate_on_policy_collection": True,
        "paired_exogenous_assignments_only": True,
        "forced_common_actions_or_trajectories": False,
        "PPO_passes_per_arm": PPO_PASSES,
        "optimizer_steps_per_arm": PPO_PASSES,
        "records": records,
        "passed": True,
    }


def static_configuration_certificate(*, formal: bool) -> dict[str, object]:
    replicates = 3 if formal else 1
    phase_A_updates = FORMAL_PHASE_A_UPDATES if formal else NONFORMAL_PHASE_A_UPDATES
    phase_B_updates = FORMAL_PHASE_B_UPDATES if formal else NONFORMAL_PHASE_B_UPDATES
    episodes = 48 if formal else 6
    bootstrap = 10_000 if formal else 250
    # Phase-B update 0 is one realized batch shared by RESET and CARRY.  Every
    # later Phase-B update collects one batch per arm.
    training_batches_per_root = (
        phase_A_updates + len(ARMS) * phase_B_updates - 1
    )
    training = replicates * training_batches_per_root * NUM_ENVS * HORIZON
    evaluation = replicates * len(ARMS) * 3 * 4 * episodes * HORIZON
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "accepted_ancestry": list(ACCEPTED_ANCESTRY),
        "arms": list(ARMS),
        "independent_unit": "one_fresh_initialization_plus_complete_common_phase_A_history",
        "replicates": replicates,
        "phase_A_updates": phase_A_updates,
        "phase_B_updates_per_arm": phase_B_updates,
        "num_envs": NUM_ENVS,
        "H": HORIZON,
        "PPO_passes": PPO_PASSES,
        "evaluation_capacities": [6, 8, 12],
        "evaluation_cells": replicates * len(ARMS) * 3 * 4,
        "episodes_per_cell": episodes,
        "training_real_transitions": training,
        "evaluation_real_transitions": evaluation,
        "total_real_transitions": training + evaluation,
        "optimizer_steps": replicates
        * (phase_A_updates + len(ARMS) * phase_B_updates)
        * PPO_PASSES,
        "bootstrap_resamples": bootstrap,
        "wall_clock_cap_seconds": 28_800 if formal else 1_200,
        "hard_ceiling": {
            "total_real_transitions": 626_688 if formal else 22_272,
            "optimizer_steps": 2_400 if formal else 80,
            "bootstrap_resamples": 10_000 if formal else 250,
            "wall_clock_seconds": 28_800 if formal else 1_200,
        },
        "seed_bases": dict(SEED_BASES),
        "bootstrap_seed": bootstrap_seed(formal=formal),
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "checkpoint_selection": "final_only",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "python_fallback": False,
    }


def validate_static_configuration(value: object, *, formal: bool) -> bool:
    return isinstance(value, Mapping) and dict(value) == static_configuration_certificate(
        formal=formal
    )


def _checkpoint_actor_state(model: nn.Module) -> tuple[dict[str, torch.Tensor], torch.Tensor]:
    state = {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
        if name in ACTOR_PARAMETER_NAMES
    }
    if tuple(state) != ACTOR_PARAMETER_NAMES:
        raise G52InvariantError("checkpoint_actor_inventory_invalid")
    log_std = state.pop("policy.log_std")
    return state, log_std


def build_final_checkpoint(
    *,
    model: g50.G50PhaseBProjection,
    optimizer: torch.optim.Optimizer,
    source_commit: str,
    formal: bool,
    replicate: int,
    arm: str,
    completed_phase_A_updates: int,
    completed_phase_B_updates: int,
    configuration: Mapping[str, object],
    seeds: Mapping[str, int],
    boundary_evidence: Mapping[str, object],
    activation_certificate: Mapping[str, object],
) -> dict[str, object]:
    expected_updates = FORMAL_PHASE_B_UPDATES if formal else NONFORMAL_PHASE_B_UPDATES
    if arm not in ARMS or completed_phase_B_updates != expected_updates:
        raise G52InvariantError("checkpoint_arm_or_update_count_invalid")
    if not validate_boundary_activation_certificate(activation_certificate):
        raise G52InvariantError("checkpoint_activation_certificate_invalid")
    actor_state, log_std = _checkpoint_actor_state(model)
    adam = snapshot_actor_adam_state(
        model,
        optimizer,
        expected_step=(
            expected_updates * PPO_PASSES
            if arm == RESET_ARM
            else completed_phase_A_updates * PPO_PASSES + expected_updates * PPO_PASSES
        ),
    )
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": source_commit,
        "formal": bool(formal),
        "replicate": int(replicate),
        "arm": arm,
        "kind": "final_only",
        "final_only_checkpoint_identity": "G52_CANONICAL_FINAL_ACTOR_CHECKPOINT_V1",
        "completed_phase_A_updates": int(completed_phase_A_updates),
        "completed_phase_B_updates": int(completed_phase_B_updates),
        "configuration": dict(configuration),
        "seed_block": dict(seeds),
        "actor_state": actor_state,
        "log_std": log_std,
        "actor_Adam_state": adam,
        "boundary_evidence": copy.deepcopy(dict(boundary_evidence)),
        "activation_certificate": copy.deepcopy(dict(activation_certificate)),
        "checkpoint_selection": "final_only",
        "source_process_lifecycle_provenance": {
            "training_source": "G32_capacity8_fixed_process",
            "evaluation_source": "G34_P0_fixed_and_random_processes_capacity_6_8_12",
            "paired_exogenous_assignments": True,
            "member_owned_action_noise": True,
            "predecessor_artifact_initialization": False,
        },
    }
    if not validate_final_checkpoint(payload):
        raise G52InvariantError("final_checkpoint_invalid")
    return payload


def validate_final_checkpoint(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    formal = value.get("formal")
    expected_updates = FORMAL_PHASE_B_UPDATES if formal is True else NONFORMAL_PHASE_B_UPDATES
    actor_state = value.get("actor_state")
    arm = value.get("arm")
    expected_final_step = (
        expected_updates * PPO_PASSES
        if arm == RESET_ARM
        else 2 * expected_updates * PPO_PASSES
    )
    try:
        adam = value.get("actor_Adam_state")
        if not isinstance(adam, Mapping) or tuple(adam) != ACTOR_PARAMETER_NAMES:
            return False
        for name in ACTOR_PARAMETER_NAMES:
            parameter = (
                value["log_std"]
                if name == "policy.log_std"
                else actor_state[name]  # type: ignore[index]
            )
            row = adam[name]
            if (
                not isinstance(parameter, torch.Tensor)
                or not isinstance(row, Mapping)
                or tuple(row) != ("exp_avg", "exp_avg_sq", "step")
                or not isinstance(row["step"], torch.Tensor)
                or row["step"].shape != torch.Size([])
                or row["step"].dtype != torch.float32
                or row["step"].device != parameter.device
                or not bool(torch.isfinite(row["step"]))
                or float(row["step"].detach().cpu()) != float(expected_final_step)
                or not isinstance(row["exp_avg"], torch.Tensor)
                or not isinstance(row["exp_avg_sq"], torch.Tensor)
                or row["exp_avg"].shape != parameter.shape
                or row["exp_avg_sq"].shape != parameter.shape
                or row["exp_avg"].dtype != parameter.dtype
                or row["exp_avg_sq"].dtype != parameter.dtype
                or row["exp_avg"].device != parameter.device
                or row["exp_avg_sq"].device != parameter.device
                or not bool(torch.isfinite(row["exp_avg"]).all())
                or not bool(torch.isfinite(row["exp_avg_sq"]).all())
                or bool(torch.any(row["exp_avg_sq"] < 0))
            ):
                return False
    except (KeyError, TypeError, AttributeError, ValueError):
        return False
    return bool(
        value.get("schema_version") == SCHEMA_VERSION
        and value.get("algorithm_id") == ALGORITHM_ID
        and value.get("source_id") == SOURCE_ID
        and isinstance(value.get("source_commit"), str)
        and len(value["source_commit"]) == 40
        and all(character in "0123456789abcdef" for character in value["source_commit"])
        and formal in (True, False)
        and arm in ARMS
        and value.get("kind") == "final_only"
        and value.get("final_only_checkpoint_identity")
        == "G52_CANONICAL_FINAL_ACTOR_CHECKPOINT_V1"
        and value.get("completed_phase_A_updates") == expected_updates
        and value.get("completed_phase_B_updates") == expected_updates
        and isinstance(actor_state, Mapping)
        and tuple(actor_state) == ACTOR_PARAMETER_NAMES[1:]
        and isinstance(value.get("log_std"), torch.Tensor)
        and value.get("checkpoint_selection") == "final_only"
        and isinstance(value.get("boundary_evidence"), Mapping)
        and value["boundary_evidence"].get("passed") is True
        and validate_boundary_activation_certificate(value.get("activation_certificate"))
        and value.get("source_process_lifecycle_provenance")
        == {
            "training_source": "G32_capacity8_fixed_process",
            "evaluation_source": "G34_P0_fixed_and_random_processes_capacity_6_8_12",
            "paired_exogenous_assignments": True,
            "member_owned_action_noise": True,
            "predecessor_artifact_initialization": False,
        }
    )


def load_phase_B_checkpoint_model(
    checkpoint: Mapping[str, object], *, member_capacity: int
) -> g50.G50PhaseBProjection:
    if not validate_final_checkpoint(checkpoint):
        raise G52InvariantError("checkpoint_reload_validation_failed")
    seeds = checkpoint["seed_block"]
    if not isinstance(seeds, Mapping):
        raise G52InvariantError("checkpoint_seed_block_invalid")
    shell = g40.make_model(
        int(member_capacity), initialization_seed=int(seeds["initialization"])
    )
    model = g50.G50PhaseBProjection(shell)
    state = dict(checkpoint["actor_state"])  # type: ignore[arg-type]
    state["policy.log_std"] = checkpoint["log_std"]
    model.load_state_dict(state, strict=True)
    return model


def make_synthetic_boundary_state_for_readiness(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    *,
    step: int = EXPECTED_FORMAL_BOUNDARY_STEP,
) -> None:
    """Populate deterministic proof-only state; never used by scientific runs."""

    if optimizer.state:
        raise G52InvariantError("readiness_source_Adam_not_empty")
    for index, parameter in enumerate(actor_parameters(model), start=1):
        optimizer.state[parameter] = {
            "step": torch.tensor(float(step), dtype=torch.float32, device=parameter.device),
            "exp_avg": torch.full_like(parameter, index * 1e-4),
            "exp_avg_sq": torch.full_like(parameter, index * 1e-6),
        }
    snapshot_actor_adam_state(model, optimizer, expected_step=step)


CLAIM_CEILINGS = {
    PERSISTENT_SUFFICIENT_RESULT: (
        "Only the registered update-100 actor-Adam reset is removable inside exact G52-P0; "
        "optimizer-history irrelevance and broader transport are not established."
    ),
    RESET_ADVANTAGE_RESULT: (
        "Only a source-local finite-budget advantage of the exact composite reset over exact "
        "step/exp_avg/exp_avg_sq carry is supported; no component or universal necessity is identified."
    ),
    "otherwise": "Neither arm nor any optimizer-state component is ranked.",
}
