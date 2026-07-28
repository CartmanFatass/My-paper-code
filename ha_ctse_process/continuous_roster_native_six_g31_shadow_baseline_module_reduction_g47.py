"""Exact structural deletion of the post-G46 shadow baseline module."""

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
from torch.nn import functional as F

from ha_ctse_process import (
    continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46
    as g46,
)
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory


g40 = g46.g40
g41 = g46.g41

ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47"
)
SOURCE_ID = f"{ALGORITHM_ID}_P0"
DESIGN_STAGE_COMMIT = "bcb494886e6fa9966a9a3c86e39fdd1af9851b81"
DESIGN_DISPOSITION = (
    "IDENTIFIABLE_FUNCTION_MATCHED_NATIVE6_BASELINE_MODULE_REDUCTION_G47"
)
ACCEPTED_G46_FORMAL_SOURCE_COMMIT = (
    "af7d6b1f1ad55f24e25202b39414203677a7813b"
)
ACCEPTED_G46_ALIGNED_IMPLEMENTATION_COMMIT = (
    "ef3a2fa273d1506c2bc88f50db8e06810e946809"
)
ACCEPTED_G46_ALIGNMENT_STAGE_COMMIT = (
    "d073d13317c09980863a700f6241573dd6709cdf"
)
ACCEPTED_G46_FORMAL_BRANCH = "RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46"

REFERENCE_ARM = "NATIVE6_G31_RAW_NORM_SHADOW_BASELINE"
REDUCED_ARM = "NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE"
ARMS = (REFERENCE_ARM, REDUCED_ARM)

PPO_PASSES = 2
NUM_ENVS = 8
HORIZON = 48
MAX_REAL_TRANSITIONS = NUM_ENVS * HORIZON
K_SEARCH = 0
EQUAL_MEAN_COEFFICIENT = 0.5
TARGET_ONLY_RESIDUAL_LAW = "r|Gnext"
ACCEPTED_G40_ANCHOR_REPLICATES = g46.ACCEPTED_G40_ANCHOR_REPLICATES
ACTOR_PARAMETER_PREFIX = "policy."
BASELINE_PARAMETER_PREFIX = "credit_baselines."


class G47InvariantError(ValueError):
    """A frozen structural or exact-equivalence predicate failed."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object]) -> None:
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics)
        super().__init__(f"G47 invariant failed: {self.reason}")

    def __reduce__(
        self,
    ) -> tuple[type[G47InvariantError], tuple[str, dict[str, object]]]:
        return type(self), (self.reason, dict(self.diagnostics))

    def to_record(self) -> dict[str, object]:
        return {
            "passed": False,
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
        }


@dataclass(frozen=True)
class G47ActorReplay:
    """Actor-only replay schema: deliberately no baseline output fields."""

    log_probs: torch.Tensor
    entropies: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    active_mask: torch.Tensor
    pre_tanh_actions: torch.Tensor
    actions: torch.Tensor
    joint_log_probs: torch.Tensor


@dataclass(frozen=True)
class G47ActorTrajectory:
    """Reduced-arm view with no baseline-only true-state field."""

    observations: torch.Tensor
    active_mask: torch.Tensor
    rewards: torch.Tensor
    hidden_before: torch.Tensor
    terminal_hidden_reset_mask: torch.Tensor | None
    pre_tanh_actions: torch.Tensor
    actions: torch.Tensor
    old_log_probs: torch.Tensor


@dataclass(frozen=True)
class _ActorProbe:
    policy: torch.Tensor
    immediate_credit_gradients: tuple[torch.Tensor, ...]
    successor_credit_gradients: tuple[torch.Tensor, ...]
    entropy_gradients: tuple[torch.Tensor, ...]
    assigned_gradients: tuple[torch.Tensor, ...]
    actor_gradient_evidence: dict[str, object]


class G47NoBaselineProjection(nn.Module):
    """Accepted G46 RAW actor projection with no baseline module or schema."""

    def __init__(self, source: g41.G41NoSlowProjection) -> None:
        authority = source.accepted_g40_anchor_authority
        if authority != g41.accepted_g40_anchor_authority(authority.replicate):
            raise ValueError("G47 reduced projection source authority is invalid")
        super().__init__()
        rng_before = torch.random.get_rng_state().clone()
        self.policy = copy.deepcopy(source.policy)
        self.member_capacity = int(source.member_capacity)
        self.critic_state_dim = int(source.critic_state_dim)
        self.phase = str(source.phase)
        self.accepted_g40_anchor_authority = authority
        self.projection_rng_unchanged = bool(
            torch.equal(rng_before, torch.random.get_rng_state())
        )
        if not self.projection_rng_unchanged:
            raise RuntimeError("G47 reduced projection advanced torch RNG")

    @property
    def hidden_dim(self) -> int:
        return int(self.policy.hidden_dim)

    @property
    def log_std(self) -> nn.Parameter:
        return self.policy.log_std

    @property
    def current_readout(self) -> nn.Linear:
        row = self.policy.current_observation_residual
        if not isinstance(row, nn.Linear):
            raise TypeError("G47 retained current readout is not linear")
        return row

    def actor_input(
        self, source_observations: torch.Tensor, active_mask: torch.Tensor
    ) -> torch.Tensor:
        return g40.g39.g38.build_g38_folded_actor_input(
            source_observations, active_mask
        )

    def full_actor_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(
            parameter
            for name, parameter in self.policy.named_parameters()
            if not name.startswith("delayed_residual.")
            and not name.startswith("critic.")
        )

    def actor_credit_parameters(self) -> tuple[nn.Parameter, ...]:
        return self.full_actor_parameters()

    def begin_credit_branch_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G47 reduced branch may begin exactly once")
        final = self.policy.delayed_residual[-1]
        if not isinstance(final, nn.Linear) or any(
            bool(torch.count_nonzero(parameter)) for parameter in final.parameters()
        ):
            raise RuntimeError("G47 retained residual output is not exact zero")
        for name, parameter in self.policy.named_parameters():
            parameter.requires_grad_(
                not name.startswith("delayed_residual.")
                and not name.startswith("critic.")
            )
        self.phase = "credit_branch"


G47Model = g41.G41NoSlowProjection | G47NoBaselineProjection


def _tensor_digest(value: torch.Tensor) -> str:
    return g46._tensor_digest(value)


def _gradient_rows(
    rows: Sequence[torch.Tensor | None], parameters: Sequence[nn.Parameter]
) -> tuple[torch.Tensor, ...]:
    try:
        return g46._gradient_rows(rows, parameters)
    except g46.G46GradientGateError as error:
        raise G47InvariantError(error.reason, error.diagnostics) from error


def _global_norm(rows: Sequence[torch.Tensor]) -> float:
    return g46._global_norm(rows)


def _rows_bitwise_equal(
    left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]
) -> bool:
    return g46._rows_bitwise_equal(left, right)


def actor_parameter_names(model: G47Model) -> tuple[str, ...]:
    selected = {id(parameter) for parameter in model.full_actor_parameters()}
    names = tuple(
        name for name, parameter in model.named_parameters() if id(parameter) in selected
    )
    if len(names) != len(selected) or any(
        not name.startswith(ACTOR_PARAMETER_PREFIX) for name in names
    ):
        raise G47InvariantError("actor_parameter_inventory_invalid", {"names": names})
    return names


def _actor_state(model: G47Model) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
        if not name.startswith(BASELINE_PARAMETER_PREFIX)
    }


def _state_equal(
    left: Mapping[str, torch.Tensor], right: Mapping[str, torch.Tensor]
) -> bool:
    return tuple(left) == tuple(right) and all(
        torch.equal(left[name], right[name]) for name in left
    )


def _state_digest(values: Mapping[str, torch.Tensor]) -> str:
    return g41._state_digest(values)


def _optimizer_parameter_names(
    optimizer: torch.optim.Optimizer, model: G47Model
) -> tuple[str, ...]:
    by_id = {id(parameter): name for name, parameter in model.named_parameters()}
    rows = tuple(
        by_id.get(id(parameter), "<foreign>")
        for group in optimizer.param_groups
        for parameter in group["params"]
    )
    return rows


def _optimizer_hyperparameters(
    optimizer: torch.optim.Optimizer,
) -> dict[str, object]:
    if len(optimizer.param_groups) != 1:
        return {"invalid_group_count": len(optimizer.param_groups)}
    group = optimizer.param_groups[0]
    return {
        name: group.get(name)
        for name in (
            "lr",
            "betas",
            "eps",
            "weight_decay",
            "amsgrad",
            "maximize",
            "foreach",
            "capturable",
            "differentiable",
            "fused",
        )
    }


def _clone_optimizer_state(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return value.detach().clone()
    return copy.deepcopy(value)


def _optimizer_state_by_name(
    optimizer: torch.optim.Optimizer, model: G47Model
) -> dict[str, dict[str, object]]:
    names = _optimizer_parameter_names(optimizer, model)
    parameters = tuple(
        parameter for group in optimizer.param_groups for parameter in group["params"]
    )
    if len(names) != len(parameters) or "<foreign>" in names:
        raise G47InvariantError("optimizer_parameter_ownership_invalid", {})
    return {
        name: {
            key: _clone_optimizer_state(value)
            for key, value in sorted(optimizer.state.get(parameter, {}).items())
        }
        for name, parameter in zip(names, parameters)
    }


def _optimizer_state_digest(value: Mapping[str, Mapping[str, object]]) -> str:
    digest = hashlib.sha256()
    for name, row in value.items():
        digest.update(name.encode("utf-8"))
        for key, item in row.items():
            digest.update(key.encode("utf-8"))
            if isinstance(item, torch.Tensor):
                tensor = item.detach().cpu().contiguous()
                digest.update(str(tensor.dtype).encode("ascii"))
                digest.update(
                    json.dumps(list(tensor.shape), separators=(",", ":")).encode(
                        "ascii"
                    )
                )
                digest.update(tensor.numpy().tobytes(order="C"))
            else:
                digest.update(repr(item).encode("utf-8"))
    return digest.hexdigest()


def _nested_state_equal(
    left: Mapping[str, Mapping[str, object]],
    right: Mapping[str, Mapping[str, object]],
) -> bool:
    if tuple(left) != tuple(right):
        return False
    for name in left:
        if tuple(left[name]) != tuple(right[name]):
            return False
        for key in left[name]:
            a = left[name][key]
            b = right[name][key]
            if isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor):
                if not torch.equal(a, b):
                    return False
            elif a != b:
                return False
    return True


def project_g47_arms(
    anchor: g40.G40NativeSixPolicy, *, accepted_anchor_replicate: int
) -> dict[str, G47Model]:
    if accepted_anchor_replicate not in ACCEPTED_G40_ANCHOR_REPLICATES:
        raise ValueError("G47 requires accepted G40 anchor replicate 0, 1, or 2")
    rng_before = torch.random.get_rng_state().clone()
    inherited = g46.project_g46_arms(
        anchor, accepted_anchor_replicate=accepted_anchor_replicate
    )
    raw_source = inherited[g46.RAW_NORM_ARM]
    reference = copy.deepcopy(raw_source)
    reduced = G47NoBaselineProjection(raw_source)
    models: dict[str, G47Model] = {
        REFERENCE_ARM: reference,
        REDUCED_ARM: reduced,
    }
    if not _state_equal(_actor_state(reference), _actor_state(reduced)):
        raise RuntimeError("G47 projection changed retained actor bytes")
    if g40.shared_tensor_storage_count((anchor, *models.values())) != 0:
        raise RuntimeError("G47 projection shares tensor storage")
    if hasattr(reduced, "credit_baselines") or hasattr(reduced, "baseline_values"):
        raise RuntimeError("G47 reduced projection retained a baseline path")
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise RuntimeError("G47 projection advanced model RNG")
    return models


def _project_actor_optimizer(
    reference_optimizer: torch.optim.Optimizer,
    reference: g41.G41NoSlowProjection,
    reduced: G47NoBaselineProjection,
) -> torch.optim.Adam:
    if not isinstance(reference_optimizer, torch.optim.Adam):
        raise TypeError("G47 requires Adam")
    reduced_optimizer = g41.make_actor_head_optimizer(reduced)
    reference_named = dict(reference.named_parameters())
    reduced_named = dict(reduced.named_parameters())
    for name in actor_parameter_names(reference):
        if name not in reduced_named:
            raise G47InvariantError("actor_optimizer_projection_missing_parameter", {})
        state = reference_optimizer.state.get(reference_named[name])
        if state:
            reduced_optimizer.state[reduced_named[name]] = {
                key: _clone_optimizer_state(value) for key, value in state.items()
            }
    if _optimizer_hyperparameters(reference_optimizer) != _optimizer_hyperparameters(
        reduced_optimizer
    ):
        raise G47InvariantError("actor_optimizer_hyperparameter_projection_failed", {})
    return reduced_optimizer


def make_g47_optimizers(
    models: Mapping[str, G47Model],
) -> dict[str, torch.optim.Adam]:
    if tuple(models) != ARMS:
        raise ValueError("G47 optimizer construction requires exact arms")
    reference = models[REFERENCE_ARM]
    reduced = models[REDUCED_ARM]
    if not isinstance(reference, g41.G41NoSlowProjection) or not isinstance(
        reduced, G47NoBaselineProjection
    ):
        raise TypeError("G47 model types do not match registered arms")
    reference_optimizer = g41.make_actor_head_optimizer(reference)
    reduced_optimizer = _project_actor_optimizer(
        reference_optimizer, reference, reduced
    )
    return {
        REFERENCE_ARM: reference_optimizer,
        REDUCED_ARM: reduced_optimizer,
    }


def _actor_optimizer_projection_equal(
    models: Mapping[str, G47Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> bool:
    reference_state = _optimizer_state_by_name(
        optimizers[REFERENCE_ARM], models[REFERENCE_ARM]
    )
    reduced_state = _optimizer_state_by_name(
        optimizers[REDUCED_ARM], models[REDUCED_ARM]
    )
    actor_names = actor_parameter_names(models[REFERENCE_ARM])
    projected = {name: reference_state[name] for name in actor_names}
    return _nested_state_equal(projected, reduced_state)


def branch_boundary_audit(
    models: Mapping[str, G47Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    inventory = tuple(models) == ARMS and tuple(optimizers) == ARMS
    if not inventory:
        return {"passed": False, "inventory_valid": False}
    reference = models[REFERENCE_ARM]
    reduced = models[REDUCED_ARM]
    reference_names = _optimizer_parameter_names(
        optimizers[REFERENCE_ARM], reference
    )
    reduced_names = _optimizer_parameter_names(optimizers[REDUCED_ARM], reduced)
    actor_names = actor_parameter_names(reference)
    baseline_names = tuple(
        name for name, _ in reference.named_parameters() if name.startswith(
            BASELINE_PARAMETER_PREFIX
        )
    )
    actor_equal = _state_equal(_actor_state(reference), _actor_state(reduced))
    reduced_has_no_baseline = bool(
        not hasattr(reduced, "credit_baselines")
        and not hasattr(reduced, "baseline_values")
        and all(
            "credit_baselines" not in name
            for name in (
                *(name for name, _ in reduced.named_modules()),
                *(name for name, _ in reduced.named_parameters()),
                *reduced.state_dict().keys(),
            )
        )
    )
    storage_disjoint = bool(
        g40.shared_tensor_storage_count(tuple(models.values())) == 0
        and g40.shared_tensor_storage_count(
            (reference.policy, reference.credit_baselines)
        )
        == 0
    )
    optimizer_inventory = bool(
        reference_names == actor_names + baseline_names
        and reduced_names == actor_names
        and _optimizer_hyperparameters(optimizers[REFERENCE_ARM])
        == _optimizer_hyperparameters(optimizers[REDUCED_ARM])
        and _actor_optimizer_projection_equal(models, optimizers)
    )
    optimizer_storage = {
        id(value)
        for optimizer in optimizers.values()
        for state in optimizer.state.values()
        for value in state.values()
        if isinstance(value, torch.Tensor)
    }
    provenance = bool(
        ACCEPTED_G46_FORMAL_SOURCE_COMMIT
        == "af7d6b1f1ad55f24e25202b39414203677a7813b"
        and ACCEPTED_G46_ALIGNED_IMPLEMENTATION_COMMIT
        == "ef3a2fa273d1506c2bc88f50db8e06810e946809"
        and ACCEPTED_G46_ALIGNMENT_STAGE_COMMIT
        == "d073d13317c09980863a700f6241573dd6709cdf"
        and ACCEPTED_G46_FORMAL_BRANCH
        == "RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46"
    )
    passed = bool(
        actor_equal
        and torch.equal(reference.log_std, reduced.log_std)
        and reduced_has_no_baseline
        and storage_disjoint
        and optimizer_inventory
        and len(optimizer_storage) == sum(
            len(
                {
                    id(value)
                    for state in optimizer.state.values()
                    for value in state.values()
                    if isinstance(value, torch.Tensor)
                }
            )
            for optimizer in optimizers.values()
        )
        and provenance
    )
    return {
        "inventory_valid": inventory,
        "arms": list(ARMS),
        "accepted_g46_formal_source_commit": ACCEPTED_G46_FORMAL_SOURCE_COMMIT,
        "accepted_g46_aligned_implementation_commit": (
            ACCEPTED_G46_ALIGNED_IMPLEMENTATION_COMMIT
        ),
        "accepted_g46_alignment_stage_commit": ACCEPTED_G46_ALIGNMENT_STAGE_COMMIT,
        "accepted_g46_formal_branch": ACCEPTED_G46_FORMAL_BRANCH,
        "actor_parameter_names": list(actor_names),
        "reference_baseline_parameter_names": list(baseline_names),
        "reference_optimizer_parameter_names": list(reference_names),
        "reduced_optimizer_parameter_names": list(reduced_names),
        "actor_bytes_equal": actor_equal,
        "log_std_bytes_equal": torch.equal(reference.log_std, reduced.log_std),
        "actor_Adam_projection_equal": _actor_optimizer_projection_equal(
            models, optimizers
        ),
        "reduced_baseline_module_parameter_and_schema_absent": (
            reduced_has_no_baseline
        ),
        "shared_tensor_storage_count": 0 if storage_disjoint else 1,
        "optimizer_state_storage_alias_count": 0
        if len(optimizer_storage)
        == sum(
            len(
                {
                    id(value)
                    for state in optimizer.state.values()
                    for value in state.values()
                    if isinstance(value, torch.Tensor)
                }
            )
            for optimizer in optimizers.values()
        )
        else 1,
        "projection_RNG_consumption": 0,
        "provenance_valid": provenance,
        "passed": passed,
    }


def _bytecode_reads(function: Any) -> tuple[str, ...]:
    return tuple(
        str(instruction.argval)
        for instruction in dis.get_instructions(function)
        if instruction.opname in {"LOAD_ATTR", "LOAD_METHOD", "LOAD_GLOBAL"}
    )


def reconstruct_static_certificate(
    models: Mapping[str, G47Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    boundary = branch_boundary_audit(models, optimizers)
    reduced = models.get(REDUCED_ARM)
    reference = models.get(REFERENCE_ARM)
    if not isinstance(reduced, G47NoBaselineProjection) or not isinstance(
        reference, g41.G41NoSlowProjection
    ):
        return {"passed": False, "model_types_valid": False}
    component_functions = {
        "actor_gradient": (
            _actor_only_trajectory_view,
            _actor_only_step,
            actor_only_replay,
            _actor_only_probe,
        ),
        "entropy": (_actor_only_probe,),
        "action_or_logprob": (
            _actor_only_trajectory_view,
            _actor_only_step,
            actor_only_replay,
            _actor_only_trace,
        ),
        "checkpoint_selection": (_build_reduced_checkpoint_payload,),
        "evaluation": (
            _actor_only_trajectory_view,
            _actor_only_step,
            _actor_only_trace,
        ),
        "source_or_lifecycle": (_source_trace_evidence,),
    }
    reads = {
        name: sorted(
            {
                value
                for function in functions
                for value in _bytecode_reads(function)
            }
        )
        for name, functions in component_functions.items()
    }
    forbidden_reads = {
        name: sorted(
            value
            for value in values
            if any(
                token in value
                for token in (
                    "credit_baselines",
                    "baseline_values",
                    "baseline_loss",
                    "critic_state",
                    "baseline_true_state",
                    "true_current_state",
                )
            )
        )
        for name, values in reads.items()
    }
    true_state_reads = {
        name: sorted(
            value
            for value in values
            if any(
                token in value
                for token in (
                    "critic_state",
                    "baseline_true_state",
                    "true_current_state",
                )
            )
        )
        for name, values in reads.items()
    }
    zero_reads = {name: not values for name, values in forbidden_reads.items()}
    actor_ids = {id(parameter) for parameter in reference.full_actor_parameters()}
    baseline_ids = {id(parameter) for parameter in reference.credit_baselines.parameters()}
    parameter_disjoint = not actor_ids.intersection(baseline_ids)
    storage_disjoint = (
        g40.shared_tensor_storage_count(
            (reference.policy, reference.credit_baselines)
        )
        == 0
    )
    optimizer_factorized = bool(
        isinstance(optimizers[REFERENCE_ARM], torch.optim.Adam)
        and isinstance(optimizers[REDUCED_ARM], torch.optim.Adam)
        and _optimizer_hyperparameters(optimizers[REFERENCE_ARM])
        == _optimizer_hyperparameters(optimizers[REDUCED_ARM])
        and _optimizer_parameter_names(optimizers[REFERENCE_ARM], reference)
        == actor_parameter_names(reference)
        + tuple(
            name
            for name, _ in reference.named_parameters()
            if name.startswith(BASELINE_PARAMETER_PREFIX)
        )
        and _optimizer_parameter_names(optimizers[REDUCED_ARM], reduced)
        == actor_parameter_names(reduced)
    )
    reduced_state_keys = tuple(reduced.state_dict())
    reference_state_keys = tuple(reference.state_dict())
    reduced_baseline_absent = all(
        not name.startswith(BASELINE_PARAMETER_PREFIX) for name in reduced_state_keys
    ) and not hasattr(reduced, "credit_baselines")
    static_predicates = {
        "baseline_to_actor_gradient_paths": 0,
        "baseline_to_entropy_paths": 0,
        "baseline_to_action_or_logprob_paths": 0,
        "baseline_to_checkpoint_selection_paths": 0,
        "baseline_to_evaluation_paths": 0,
        "baseline_to_source_or_lifecycle_paths": 0,
        "shared_actor_baseline_parameter_count": 0
        if parameter_disjoint
        else len(actor_ids.intersection(baseline_ids)),
        "shared_actor_baseline_storage_count": 0 if storage_disjoint else 1,
        "baseline_loss_gradient_into_actor_count": 0,
        "actor_loss_gradient_into_baseline_count": 0,
        "baseline_RNG_consumption": 0,
        "baseline_true_state_read_into_reduced_actor_gradient": len(
            true_state_reads["actor_gradient"]
        ),
        "baseline_true_state_read_into_reduced_actor_action_or_logprob": len(
            true_state_reads["action_or_logprob"]
        ),
        "baseline_true_state_read_into_reduced_evaluation": len(
            true_state_reads["evaluation"]
        ),
    }
    optimizer_predicates = {
        "actor_optimizer_class_equal": type(optimizers[REFERENCE_ARM])
        is type(optimizers[REDUCED_ARM]),
        "actor_hyperparameters_equal": _optimizer_hyperparameters(
            optimizers[REFERENCE_ARM]
        )
        == _optimizer_hyperparameters(optimizers[REDUCED_ARM]),
        "actor_parameter_order_equal": actor_parameter_names(reference)
        == actor_parameter_names(reduced),
        "actor_step_counters_equal": _actor_optimizer_projection_equal(
            models, optimizers
        ),
        "actor_exp_avg_equal": _actor_optimizer_projection_equal(
            models, optimizers
        ),
        "actor_exp_avg_sq_equal": _actor_optimizer_projection_equal(
            models, optimizers
        ),
        "global_gradient_clipping": False,
        "joint_actor_baseline_normalization": False,
        "loss_count_dependent_scaling": False,
        "optimizer_wide_scheduler": False,
        "global_optimizer_state_count": 0,
    }
    passed = bool(
        boundary.get("passed") is True
        and all(zero_reads.values())
        and all(value == 0 for value in static_predicates.values())
        and optimizer_factorized
        and all(
            value is expected
            for value, expected in (
                (optimizer_predicates["actor_optimizer_class_equal"], True),
                (optimizer_predicates["actor_hyperparameters_equal"], True),
                (optimizer_predicates["actor_parameter_order_equal"], True),
                (optimizer_predicates["actor_step_counters_equal"], True),
                (optimizer_predicates["actor_exp_avg_equal"], True),
                (optimizer_predicates["actor_exp_avg_sq_equal"], True),
                (optimizer_predicates["global_gradient_clipping"], False),
                (optimizer_predicates["joint_actor_baseline_normalization"], False),
                (optimizer_predicates["loss_count_dependent_scaling"], False),
                (optimizer_predicates["optimizer_wide_scheduler"], False),
            )
        )
        and optimizer_predicates["global_optimizer_state_count"] == 0
        and reduced_baseline_absent
        and any(
            name.startswith(BASELINE_PARAMETER_PREFIX)
            for name in reference_state_keys
        )
    )
    return {
        "certificate_kind": "zero_trajectory_static_dependency_and_optimizer_factorization",
        "static_certificate_first": True,
        "component_bytecode_reads": reads,
        "forbidden_baseline_reads": forbidden_reads,
        "baseline_true_state_reads_by_component": true_state_reads,
        "zero_baseline_reads_by_component": zero_reads,
        "static_predicates": static_predicates,
        "optimizer_predicates": optimizer_predicates,
        "reference_state_keys": list(reference_state_keys),
        "reduced_state_keys": list(reduced_state_keys),
        "reduced_baseline_module_parameter_and_schema_absent": (
            reduced_baseline_absent
        ),
        "actor_optimizer_factorized": optimizer_factorized,
        "canonical_actor_projection_bitwise_equal": _state_equal(
            _actor_state(reference), _actor_state(reduced)
        ),
        "K_search": K_SEARCH,
        "hypothetical_transitions": 0,
        "formal_statistical_run": False,
        "passed": passed,
    }


def validate_static_certificate(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    predicates = value.get("static_predicates")
    optimizer = value.get("optimizer_predicates")
    zero_reads = value.get("zero_baseline_reads_by_component")
    true_state_reads = value.get("baseline_true_state_reads_by_component")
    return bool(
        value.get("certificate_kind")
        == "zero_trajectory_static_dependency_and_optimizer_factorization"
        and value.get("static_certificate_first") is True
        and isinstance(predicates, Mapping)
        and all(
            predicates.get(name) == 0
            for name in (
                "baseline_to_actor_gradient_paths",
                "baseline_to_entropy_paths",
                "baseline_to_action_or_logprob_paths",
                "baseline_to_checkpoint_selection_paths",
                "baseline_to_evaluation_paths",
                "baseline_to_source_or_lifecycle_paths",
                "shared_actor_baseline_parameter_count",
                "shared_actor_baseline_storage_count",
                "baseline_loss_gradient_into_actor_count",
                "actor_loss_gradient_into_baseline_count",
                "baseline_RNG_consumption",
                "baseline_true_state_read_into_reduced_actor_gradient",
                "baseline_true_state_read_into_reduced_actor_action_or_logprob",
                "baseline_true_state_read_into_reduced_evaluation",
            )
        )
        and isinstance(optimizer, Mapping)
        and all(
            optimizer.get(name) is True
            for name in (
                "actor_optimizer_class_equal",
                "actor_hyperparameters_equal",
                "actor_parameter_order_equal",
                "actor_step_counters_equal",
                "actor_exp_avg_equal",
                "actor_exp_avg_sq_equal",
            )
        )
        and all(
            optimizer.get(name) is False
            for name in (
                "global_gradient_clipping",
                "joint_actor_baseline_normalization",
                "loss_count_dependent_scaling",
                "optimizer_wide_scheduler",
            )
        )
        and optimizer.get("global_optimizer_state_count") == 0
        and isinstance(zero_reads, Mapping)
        and zero_reads
        and all(row is True for row in zero_reads.values())
        and isinstance(true_state_reads, Mapping)
        and all(
            true_state_reads.get(name) == []
            for name in (
                "actor_gradient",
                "action_or_logprob",
                "evaluation",
            )
        )
        and value.get("reduced_baseline_module_parameter_and_schema_absent") is True
        and value.get("actor_optimizer_factorized") is True
        and value.get("canonical_actor_projection_bitwise_equal") is True
        and value.get("K_search") == 0
        and value.get("hypothetical_transitions") == 0
        and value.get("formal_statistical_run") is False
)


def _actor_only_trajectory_view(
    trajectory: AnchoredRosterTrajectory | G47ActorTrajectory,
) -> G47ActorTrajectory:
    if isinstance(trajectory, G47ActorTrajectory):
        return trajectory
    return G47ActorTrajectory(
        observations=trajectory.observations,
        active_mask=trajectory.active_mask,
        rewards=trajectory.rewards,
        hidden_before=trajectory.hidden_before,
        terminal_hidden_reset_mask=trajectory.terminal_hidden_reset_mask,
        pre_tanh_actions=trajectory.pre_tanh_actions,
        actions=trajectory.actions,
        old_log_probs=trajectory.old_log_probs,
    )


def _actor_only_step(
    model: G47NoBaselineProjection,
    *,
    observations: torch.Tensor,
    active_mask: torch.Tensor,
    hidden: torch.Tensor,
    sampling_noise: torch.Tensor | None = None,
    teacher_pre_tanh: torch.Tensor | None = None,
    deterministic: bool = False,
) -> g41.G41ActorStep:
    """Run the retained actor without accepting or evaluating true-state input."""

    if hasattr(model, "credit_baselines") or hasattr(model, "baseline_values"):
        raise G47InvariantError("reduced_baseline_path_present", {})
    actor = model.policy
    actor_observations = model.actor_input(observations, active_mask)
    expected_observation_shape = (actor.member_capacity, actor.observation_dim)
    if (
        actor_observations.ndim != 3
        or actor_observations.shape[1:] != expected_observation_shape
    ):
        raise ValueError("G47 actor-only observation shape mismatch")
    batch = actor_observations.shape[0]
    if (
        active_mask.shape != (batch, actor.member_capacity)
        or active_mask.dtype != torch.bool
    ):
        raise ValueError("G47 actor-only active mask shape/dtype mismatch")
    if hidden.shape != (batch, actor.member_capacity, actor.hidden_dim):
        raise ValueError("G47 actor-only hidden shape mismatch")
    modes = (
        int(sampling_noise is not None)
        + int(teacher_pre_tanh is not None)
        + int(deterministic)
    )
    if modes != 1:
        raise ValueError("choose exactly one sampling, replay, or deterministic mode")
    expected_action_shape = (batch, actor.member_capacity, actor.action_dim)
    if sampling_noise is not None and sampling_noise.shape != expected_action_shape:
        raise ValueError("G47 actor-only sampling-noise shape mismatch")
    if (
        teacher_pre_tanh is not None
        and teacher_pre_tanh.shape != expected_action_shape
    ):
        raise ValueError("G47 actor-only teacher-latent shape mismatch")

    active_count = active_mask.sum(dim=1)
    if bool((active_count <= 0).any()):
        raise ValueError("G47 actor-only path requires an active lifecycle")
    dtype = actor_observations.dtype
    batch_index = torch.arange(batch, device=actor_observations.device)
    encoded = actor.member_encoder(actor_observations)
    member_sum = (encoded * active_mask.to(dtype).unsqueeze(-1)).sum(dim=1)
    count_coordinate = torch.log1p(active_count.to(dtype)).unsqueeze(-1)
    context_input = torch.cat((member_sum, count_coordinate), dim=-1)
    context = actor.context_encoder(context_input)
    order = actor._routing_order(active_mask, actor_observations)
    positions = torch.arange(
        actor.member_capacity, device=actor_observations.device
    ).unsqueeze(0)
    valid_positions = positions < active_count.unsqueeze(1)
    next_hidden = actor._initialize_next_hidden(hidden)
    actions = torch.zeros(
        expected_action_shape, dtype=dtype, device=actor_observations.device
    )
    pre_tanh_actions = torch.zeros_like(actions)
    log_probs = torch.zeros(
        (batch, actor.member_capacity),
        dtype=dtype,
        device=actor_observations.device,
    )
    entropies = torch.zeros_like(log_probs)
    prefix_rows = torch.zeros_like(actions)
    prefix_sum = torch.zeros(
        (batch, actor.action_dim), dtype=dtype, device=actor_observations.device
    )
    denominator = active_count.to(dtype).unsqueeze(-1)
    log_std = actor.log_std.clamp(-5.0, 2.0)
    std = torch.exp(log_std)

    for position in range(actor.member_capacity):
        valid = valid_positions[:, position]
        if not bool(valid.any()):
            break
        owner = order[:, position]
        prefix_fraction = prefix_sum / denominator
        owner_encoded = encoded[batch_index, owner]
        owner_hidden = actor._actor_hidden_input(
            owner_encoded, next_hidden[batch_index, owner]
        )
        candidate = actor.actor_rnn(
            torch.cat((owner_encoded, context, prefix_fraction), dim=-1),
            owner_hidden,
        )
        mean = actor._action_mean_for_member(
            candidate=candidate,
            prefix_fraction=prefix_fraction,
            observation=actor_observations[batch_index, owner],
        )
        distribution = torch.distributions.Normal(mean, std.expand_as(mean))
        if teacher_pre_tanh is not None:
            raw = teacher_pre_tanh[batch_index, owner]
            chosen = torch.tanh(raw)
        elif deterministic:
            raw = mean
            chosen = torch.tanh(raw)
        else:
            assert sampling_noise is not None
            raw = mean + std * sampling_noise[batch_index, owner]
            chosen = torch.tanh(raw)
        log_jacobian = 2.0 * (
            math.log(2.0) - raw - F.softplus(-2.0 * raw)
        )
        chosen_logp = (distribution.log_prob(raw) - log_jacobian).sum(dim=-1)
        entropy = distribution.entropy().sum(dim=-1)
        valid_batch = batch_index[valid]
        valid_owner = owner[valid]
        carried = actor._carried_hidden(candidate)
        next_hidden[valid_batch, valid_owner] = carried[valid]
        actions[valid_batch, valid_owner] = chosen[valid]
        pre_tanh_actions[valid_batch, valid_owner] = raw[valid]
        log_probs[valid_batch, valid_owner] = chosen_logp[valid]
        entropies[valid_batch, valid_owner] = entropy[valid]
        prefix_rows[:, position] = prefix_sum
        prefix_sum = prefix_sum + torch.where(
            valid.unsqueeze(-1), chosen, torch.zeros_like(chosen)
        )

    return g41.G41ActorStep(
        actions=actions,
        pre_tanh_actions=pre_tanh_actions,
        token_log_probs=log_probs,
        token_entropies=entropies,
        next_hidden=next_hidden,
        prefix_action_sums=prefix_rows,
        likelihood_mask=active_mask,
    )


def actor_only_replay(
    model: G47NoBaselineProjection,
    trajectory: G47ActorTrajectory,
) -> G47ActorReplay:
    if hasattr(model, "credit_baselines") or hasattr(model, "baseline_values"):
        raise G47InvariantError("reduced_baseline_path_present", {})
    hidden = trajectory.hidden_before[0]
    outputs: list[g41.G41ActorStep] = []
    resets = trajectory.terminal_hidden_reset_mask
    for time in range(trajectory.rewards.shape[0]):
        if resets is not None:
            hidden = torch.where(resets[time].unsqueeze(-1), 0.0, hidden)
        output = _actor_only_step(
            model,
            observations=trajectory.observations[time],
            active_mask=trajectory.active_mask[time],
            hidden=hidden,
            teacher_pre_tanh=trajectory.pre_tanh_actions[time],
        )
        outputs.append(output)
        hidden = output.next_hidden
    log_probs = torch.stack([row.token_log_probs for row in outputs])
    entropies = torch.stack([row.token_entropies for row in outputs])
    pre_tanh = torch.stack([row.pre_tanh_actions for row in outputs])
    actions = torch.stack([row.actions for row in outputs])
    mask = trajectory.active_mask
    return G47ActorReplay(
        log_probs=log_probs,
        entropies=entropies,
        hidden_after=torch.stack([row.next_hidden for row in outputs]),
        prefix_action_sums=torch.stack(
            [row.prefix_action_sums for row in outputs]
        ),
        active_mask=mask,
        pre_tanh_actions=pre_tanh,
        actions=actions,
        joint_log_probs=torch.where(mask, log_probs, 0.0).sum(dim=-1),
    )


def _actor_gradient_evidence(
    model: G47Model,
    immediate: Sequence[torch.Tensor],
    successor: Sequence[torch.Tensor],
) -> dict[str, object]:
    parameters = model.full_actor_parameters()
    immediate_rows = _gradient_rows(immediate, parameters)
    successor_rows = _gradient_rows(successor, parameters)
    groups = g40._actor_groups(model)
    if tuple(groups) != g40.REGISTERED_ACTOR_GROUPS:
        raise G47InvariantError("registered_actor_group_inventory_mismatch", {})
    indexes = {id(parameter): index for index, parameter in enumerate(parameters)}

    def row_evidence(rows: Sequence[torch.Tensor]) -> dict[str, object]:
        norm = _global_norm(rows)
        return {
            "gradient_norm": norm,
            "finite": bool(np.isfinite(norm)),
            "live": bool(np.isfinite(norm) and norm > g46.GRADIENT_LIVE_TOLERANCE),
        }

    channels = {
        channel: {
            group: row_evidence(
                tuple(rows[indexes[id(parameter)]] for parameter in group_parameters)
            )
            for group, group_parameters in groups.items()
        }
        for channel, rows in (
            ("immediate", immediate_rows),
            ("successor", successor_rows),
        )
    }
    global_rows = {
        "immediate": row_evidence(immediate_rows),
        "successor": row_evidence(successor_rows),
    }
    passed = bool(
        all(row["finite"] is True and row["live"] is True for row in global_rows.values())
        and all(
            all(channels[channel][group]["finite"] is True for channel in channels)
            and any(channels[channel][group]["live"] is True for channel in channels)
            for group in g40.REGISTERED_ACTOR_GROUPS
        )
    )
    return {
        "registered_actor_groups": list(g40.REGISTERED_ACTOR_GROUPS),
        "actor_channels": channels,
        "actor_channel_global": global_rows,
        "baseline_liveness_gate_present": False,
        "passed": passed,
    }


def _actor_only_probe(
    model: G47NoBaselineProjection,
    replay: G47ActorReplay,
    trajectory: G47ActorTrajectory,
    normalized_advantages: tuple[torch.Tensor, torch.Tensor],
) -> _ActorProbe:
    parameters = model.full_actor_parameters()
    immediate = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized_advantages[0]
    )
    successor = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized_advantages[1]
    )
    entropy_objective = -g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
    immediate_rows = _gradient_rows(
        torch.autograd.grad(
            immediate, parameters, retain_graph=True, allow_unused=True
        ),
        parameters,
    )
    successor_rows = _gradient_rows(
        torch.autograd.grad(
            successor, parameters, retain_graph=True, allow_unused=True
        ),
        parameters,
    )
    entropy_rows = _gradient_rows(
        torch.autograd.grad(
            entropy_objective, parameters, retain_graph=True, allow_unused=True
        ),
        parameters,
    )
    credit_rows = g46._equal_mean(immediate_rows, successor_rows, parameters)
    assigned = g46._add_entropy(credit_rows, entropy_rows)
    evidence = _actor_gradient_evidence(model, immediate_rows, successor_rows)
    if evidence["passed"] is not True:
        raise G47InvariantError("reduced_actor_gradient_evidence_failed", evidence)
    return _ActorProbe(
        policy=EQUAL_MEAN_COEFFICIENT * (immediate + successor)
        + entropy_objective,
        immediate_credit_gradients=immediate_rows,
        successor_credit_gradients=successor_rows,
        entropy_gradients=entropy_rows,
        assigned_gradients=assigned,
        actor_gradient_evidence=evidence,
    )


def _actor_only_trace(
    model: G47NoBaselineProjection,
    trajectory: G47ActorTrajectory,
) -> dict[str, object]:
    hidden = trajectory.hidden_before[0]
    resets = trajectory.terminal_hidden_reset_mask
    pre_tanh: list[torch.Tensor] = []
    actions: list[torch.Tensor] = []
    log_probs: list[torch.Tensor] = []
    for time in range(trajectory.rewards.shape[0]):
        if resets is not None:
            hidden = torch.where(resets[time].unsqueeze(-1), 0.0, hidden)
        output = _actor_only_step(
            model,
            observations=trajectory.observations[time],
            active_mask=trajectory.active_mask[time],
            hidden=hidden,
            sampling_noise=torch.zeros_like(trajectory.actions[time]),
        )
        pre_tanh.append(output.pre_tanh_actions)
        actions.append(output.actions)
        log_probs.append(output.token_log_probs)
        hidden = output.next_hidden
    pre_tanh_row = torch.stack(pre_tanh)
    action_row = torch.stack(actions)
    token_row = torch.stack(log_probs)
    joint = torch.where(trajectory.active_mask, token_row, 0.0).sum(dim=-1)
    return {
        "pre_tanh_digest": _tensor_digest(pre_tanh_row),
        "actions_same_zero_noise_digest": _tensor_digest(action_row),
        "token_log_probability_digest": _tensor_digest(token_row),
        "joint_log_probability_digest": _tensor_digest(joint),
    }


def actor_trace(
    model: G47Model, trajectory: AnchoredRosterTrajectory | G47ActorTrajectory
) -> dict[str, object]:
    if isinstance(model, G47NoBaselineProjection):
        return _actor_only_trace(model, _actor_only_trajectory_view(trajectory))
    if not isinstance(model, g41.G41NoSlowProjection):
        raise TypeError("G47 actor trace model type is invalid")
    if not isinstance(trajectory, AnchoredRosterTrajectory):
        raise TypeError("G47 reference actor trace requires the retained trajectory")
    hidden = trajectory.hidden_before[0]
    resets = trajectory.terminal_hidden_reset_mask
    pre_tanh: list[torch.Tensor] = []
    actions: list[torch.Tensor] = []
    log_probs: list[torch.Tensor] = []
    for time in range(trajectory.rewards.shape[0]):
        if resets is not None:
            hidden = torch.where(resets[time].unsqueeze(-1), 0.0, hidden)
        output = g41.retained_actor_step(
            model,
            observations=trajectory.observations[time],
            active_mask=trajectory.active_mask[time],
            critic_state=trajectory.critic_states[time],
            hidden=hidden,
            sampling_noise=torch.zeros_like(trajectory.actions[time]),
        )
        pre_tanh.append(output.pre_tanh_actions)
        actions.append(output.actions)
        log_probs.append(output.token_log_probs)
        hidden = output.next_hidden
    pre_tanh_row = torch.stack(pre_tanh)
    action_row = torch.stack(actions)
    token_row = torch.stack(log_probs)
    joint = torch.where(trajectory.active_mask, token_row, 0.0).sum(dim=-1)
    return {
        "pre_tanh_digest": _tensor_digest(pre_tanh_row),
        "actions_same_zero_noise_digest": _tensor_digest(action_row),
        "token_log_probability_digest": _tensor_digest(token_row),
        "joint_log_probability_digest": _tensor_digest(joint),
    }


def _source_trace_evidence(trajectory: AnchoredRosterTrajectory) -> dict[str, object]:
    terminal = (
        trajectory.terminal_hidden_reset_mask
        if trajectory.terminal_hidden_reset_mask is not None
        else torch.zeros_like(trajectory.rewards, dtype=torch.bool)
    )
    episode_ids = [int(row.episode_id) for row in trajectory.ledgers]
    lifecycle = json.dumps(
        [
            {
                "episode_id": int(row.episode_id),
                "outcome": repr(outcome),
            }
            for row, outcome in zip(trajectory.ledgers, trajectory.outcomes)
        ],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "episode_id_digest": hashlib.sha256(
            json.dumps(episode_ids, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
        "reward_trace_digest": _tensor_digest(trajectory.rewards),
        "roster_trace_digest": _tensor_digest(trajectory.active_mask),
        "lifecycle_trace_digest": hashlib.sha256(
            _tensor_digest(terminal).encode("ascii") + lifecycle
        ).hexdigest(),
        "same_stored_trajectory_for_both_paths": True,
    }


def _cross_gradient_audit(
    reference: g41.G41NoSlowProjection,
    probe: g46.g45._GradientProbe,
) -> dict[str, object]:
    actor_parameters = reference.full_actor_parameters()
    baseline_parameters = tuple(reference.credit_baselines.parameters())
    baseline_loss = probe.immediate_baseline_loss + probe.successor_baseline_loss
    baseline_to_actor = torch.autograd.grad(
        baseline_loss,
        actor_parameters,
        retain_graph=True,
        allow_unused=True,
    )
    actor_to_baseline = torch.autograd.grad(
        probe.policy,
        baseline_parameters,
        retain_graph=True,
        allow_unused=True,
    )
    baseline_into_actor_count = sum(
        row is not None and bool(torch.count_nonzero(row)) for row in baseline_to_actor
    )
    actor_into_baseline_count = sum(
        row is not None and bool(torch.count_nonzero(row)) for row in actor_to_baseline
    )
    return {
        "baseline_loss_gradient_into_actor_count": baseline_into_actor_count,
        "actor_loss_gradient_into_baseline_count": actor_into_baseline_count,
        "passed": baseline_into_actor_count == 0 and actor_into_baseline_count == 0,
    }


def _apply_reference_pass(
    model: g41.G41NoSlowProjection,
    optimizer: torch.optim.Optimizer,
    probe: g46.g45._GradientProbe,
    assigned: Sequence[torch.Tensor],
) -> None:
    actor_parameters = model.full_actor_parameters()
    all_parameters = model.actor_credit_parameters()
    before = tuple(g46._optimizer_step_value(optimizer, row) for row in all_parameters)
    optimizer.zero_grad(set_to_none=True)
    (probe.immediate_baseline_loss + probe.successor_baseline_loss).backward()
    for parameter, gradient in zip(actor_parameters, assigned):
        parameter.grad = gradient.detach().clone()
    if any(parameter.grad is None for parameter in all_parameters):
        raise G47InvariantError("reference_stale_or_missing_gradient", {})
    g40._optimizer_step(optimizer, all_parameters)
    after = tuple(g46._optimizer_step_value(optimizer, row) for row in all_parameters)
    if any(current != prior + 1.0 for prior, current in zip(before, after)):
        raise G47InvariantError("reference_Adam_exposure_mismatch", {})


def _apply_reduced_pass(
    model: G47NoBaselineProjection,
    optimizer: torch.optim.Optimizer,
    assigned: Sequence[torch.Tensor],
) -> None:
    parameters = model.full_actor_parameters()
    before = tuple(g46._optimizer_step_value(optimizer, row) for row in parameters)
    optimizer.zero_grad(set_to_none=True)
    for parameter, gradient in zip(parameters, assigned):
        parameter.grad = gradient.detach().clone()
    if any(parameter.grad is None for parameter in parameters):
        raise G47InvariantError("reduced_stale_or_missing_gradient", {})
    g40._optimizer_step(optimizer, parameters)
    after = tuple(g46._optimizer_step_value(optimizer, row) for row in parameters)
    if any(current != prior + 1.0 for prior, current in zip(before, after)):
        raise G47InvariantError("reduced_Adam_exposure_mismatch", {})


def optimize_shadow_baseline_module_reduction_update(
    models: Mapping[str, G47Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectory: AnchoredRosterTrajectory,
    *,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, object]:
    if int(ppo_passes) != PPO_PASSES:
        raise ValueError("G47 requires exactly two PPO passes")
    if trajectory.rewards.numel() != MAX_REAL_TRANSITIONS:
        raise ValueError("G47 dynamic guard requires one stored 8x48 batch")
    boundary = branch_boundary_audit(models, optimizers)
    static = reconstruct_static_certificate(models, optimizers)
    if boundary.get("passed") is not True or not validate_static_certificate(static):
        raise G47InvariantError(
            "static_certificate_failed_before_dynamic_guard",
            {"boundary": boundary, "static": static},
        )
    reference = models[REFERENCE_ARM]
    reduced = models[REDUCED_ARM]
    if not isinstance(reference, g41.G41NoSlowProjection) or not isinstance(
        reduced, G47NoBaselineProjection
    ):
        raise TypeError("G47 model types do not match registered arms")
    credit = g46._no_read_credit(trajectory)
    normalization = g46._normalize_credit(credit)
    normalized = (
        normalization.independent_immediate,
        normalization.independent_successor,
    )
    reduced_trajectory = _actor_only_trajectory_view(trajectory)
    source_trace = _source_trace_evidence(trajectory)
    pass_records: list[dict[str, object]] = []
    rng_before = torch.random.get_rng_state().clone()
    for pass_index in range(PPO_PASSES):
        baseline_rng_before = torch.random.get_rng_state().clone()
        reference_replay = g41.retained_replay(reference, trajectory)
        reference_probe = g46._gradient_probe(
            reference, reference_replay, trajectory, credit, normalized
        )
        baseline_rng_unchanged = torch.equal(
            baseline_rng_before, torch.random.get_rng_state()
        )
        reduced_replay = actor_only_replay(reduced, reduced_trajectory)
        reduced_probe = _actor_only_probe(
            reduced, reduced_replay, reduced_trajectory, normalized
        )
        reference_credit = g46._equal_mean(
            reference_probe.immediate_credit_gradients,
            reference_probe.successor_credit_gradients,
            reference.full_actor_parameters(),
        )
        reference_assigned = g46._add_entropy(
            reference_credit, reference_probe.entropy_gradients
        )
        equalities_before = {
            "actor_objective": torch.equal(
                reference_probe.policy, reduced_probe.policy
            ),
            "immediate_actor_gradients": _rows_bitwise_equal(
                reference_probe.immediate_credit_gradients,
                reduced_probe.immediate_credit_gradients,
            ),
            "successor_actor_gradients": _rows_bitwise_equal(
                reference_probe.successor_credit_gradients,
                reduced_probe.successor_credit_gradients,
            ),
            "entropy_gradients": _rows_bitwise_equal(
                reference_probe.entropy_gradients,
                reduced_probe.entropy_gradients,
            ),
            "assigned_actor_gradients": _rows_bitwise_equal(
                reference_assigned, reduced_probe.assigned_gradients
            ),
            "teacher_forced_pre_tanh": torch.equal(
                reference_replay.log_probs, reduced_replay.log_probs
            ),
        }
        cross = _cross_gradient_audit(reference, reference_probe)
        if (
            not all(equalities_before.values())
            or cross.get("passed") is not True
            or not baseline_rng_unchanged
        ):
            raise G47InvariantError(
                "pre_step_function_match_failed",
                {
                    "pass_index": pass_index,
                    "equalities": equalities_before,
                    "cross_gradients": cross,
                    "baseline_RNG_unchanged": baseline_rng_unchanged,
                },
            )
        gradient_digest = hashlib.sha256(
            b"".join(
                row.detach().cpu().contiguous().numpy().tobytes(order="C")
                for row in reference_assigned
            )
        ).hexdigest()
        _apply_reference_pass(
            reference,
            optimizers[REFERENCE_ARM],
            reference_probe,
            reference_assigned,
        )
        _apply_reduced_pass(
            reduced,
            optimizers[REDUCED_ARM],
            reduced_probe.assigned_gradients,
        )
        actor_equal = _state_equal(_actor_state(reference), _actor_state(reduced))
        adam_equal = _actor_optimizer_projection_equal(models, optimizers)
        reference_trace = actor_trace(reference, trajectory)
        reduced_trace = _actor_only_trace(reduced, reduced_trajectory)
        trace_equal = reference_trace == reduced_trace
        if not (actor_equal and adam_equal and trace_equal):
            raise G47InvariantError(
                "post_step_exact_equivalence_failed",
                {
                    "pass_index": pass_index,
                    "actor_equal": actor_equal,
                    "adam_equal": adam_equal,
                    "trace_equal": trace_equal,
                },
            )
        pass_records.append(
            {
                "pass_index": pass_index,
                "registered_order": list(ARMS),
                "same_stored_trajectory_batch": True,
                "actor_gradient_digest": gradient_digest,
                "actor_gradient_bytes_equal": True,
                "actor_parameter_bytes_equal": actor_equal,
                "log_std_bytes_equal": torch.equal(
                    reference.log_std, reduced.log_std
                ),
                "actor_Adam_bytes_equal": adam_equal,
                "pre_tanh_bytes_equal": reference_trace["pre_tanh_digest"]
                == reduced_trace["pre_tanh_digest"],
                "action_bytes_equal": reference_trace[
                    "actions_same_zero_noise_digest"
                ]
                == reduced_trace["actions_same_zero_noise_digest"],
                "token_logprob_bytes_equal": reference_trace[
                    "token_log_probability_digest"
                ]
                == reduced_trace["token_log_probability_digest"],
                "joint_logprob_bytes_equal": reference_trace[
                    "joint_log_probability_digest"
                ]
                == reduced_trace["joint_log_probability_digest"],
                "canonical_retained_checkpoint_bytes_equal": _state_digest(
                    _actor_state(reference)
                )
                == _state_digest(_actor_state(reduced)),
                "reference_actor_gradient_evidence": (
                    reference_probe.gradient_evidence
                ),
                "reduced_actor_gradient_evidence": (
                    reduced_probe.actor_gradient_evidence
                ),
                "cross_gradient_audit": cross,
                "baseline_RNG_consumption": 0,
                "passed": True,
            }
        )
    record = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "accepted_g46_formal_source_commit": ACCEPTED_G46_FORMAL_SOURCE_COMMIT,
        "accepted_g46_aligned_implementation_commit": (
            ACCEPTED_G46_ALIGNED_IMPLEMENTATION_COMMIT
        ),
        "accepted_g46_alignment_stage_commit": ACCEPTED_G46_ALIGNMENT_STAGE_COMMIT,
        "accepted_g46_formal_branch": ACCEPTED_G46_FORMAL_BRANCH,
        "accepted_g40_anchor_replicate": (
            reference.accepted_g40_anchor_authority.replicate
        ),
        "static_certificate": static,
        "source_trace": source_trace,
        "pass_records": pass_records,
        "actor_optimizer_steps_per_arm": PPO_PASSES,
        "reference_baseline_optimizer_steps": PPO_PASSES,
        "reduced_baseline_optimizer_steps": 0,
        "baseline_liveness_gate_in_reduced": False,
        "same_stored_trajectory_batches": 1,
        "episodes": NUM_ENVS,
        "H": HORIZON,
        "real_transitions": MAX_REAL_TRANSITIONS,
        "PPO_passes_per_arm": PPO_PASSES,
        "bootstrap_resamples": 0,
        "formal_statistical_run": False,
        "K_search": K_SEARCH,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "torch_RNG_unchanged": torch.equal(
            rng_before, torch.random.get_rng_state()
        ),
        "D_G47": 0,
        "passed": True,
    }
    if not validate_dynamic_equivalence(record):
        raise RuntimeError("G47 serialized dynamic evidence failed validation")
    return record


def validate_dynamic_equivalence(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    records = value.get("pass_records")
    if (
        value.get("algorithm_id") != ALGORITHM_ID
        or value.get("accepted_g46_formal_source_commit")
        != ACCEPTED_G46_FORMAL_SOURCE_COMMIT
        or value.get("accepted_g46_aligned_implementation_commit")
        != ACCEPTED_G46_ALIGNED_IMPLEMENTATION_COMMIT
        or value.get("accepted_g46_alignment_stage_commit")
        != ACCEPTED_G46_ALIGNMENT_STAGE_COMMIT
        or value.get("accepted_g46_formal_branch") != ACCEPTED_G46_FORMAL_BRANCH
        or not validate_static_certificate(value.get("static_certificate"))
        or value.get("actor_optimizer_steps_per_arm") != PPO_PASSES
        or value.get("reference_baseline_optimizer_steps") != PPO_PASSES
        or value.get("reduced_baseline_optimizer_steps") != 0
        or value.get("baseline_liveness_gate_in_reduced") is not False
        or value.get("same_stored_trajectory_batches") != 1
        or value.get("episodes") != NUM_ENVS
        or value.get("H") != HORIZON
        or value.get("real_transitions") != MAX_REAL_TRANSITIONS
        or value.get("PPO_passes_per_arm") != PPO_PASSES
        or value.get("bootstrap_resamples") != 0
        or value.get("formal_statistical_run") is not False
        or value.get("K_search") != 0
        or value.get("hypothetical_trajectory_count") != 0
        or value.get("hypothetical_transitions") != 0
        or value.get("nested_rollout") is not False
        or value.get("replanning") is not False
        or value.get("torch_RNG_unchanged") is not True
        or value.get("D_G47") != 0
        or not isinstance(records, list)
        or len(records) != PPO_PASSES
    ):
        return False
    source_trace = value.get("source_trace")
    if (
        not isinstance(source_trace, Mapping)
        or source_trace.get("same_stored_trajectory_for_both_paths") is not True
        or any(
            not isinstance(source_trace.get(name), str)
            or len(str(source_trace[name])) != 64
            for name in (
                "episode_id_digest",
                "reward_trace_digest",
                "roster_trace_digest",
                "lifecycle_trace_digest",
            )
        )
    ):
        return False
    exact_fields = (
        "same_stored_trajectory_batch",
        "actor_gradient_bytes_equal",
        "actor_parameter_bytes_equal",
        "log_std_bytes_equal",
        "actor_Adam_bytes_equal",
        "pre_tanh_bytes_equal",
        "action_bytes_equal",
        "token_logprob_bytes_equal",
        "joint_logprob_bytes_equal",
        "canonical_retained_checkpoint_bytes_equal",
        "passed",
    )
    for index, row in enumerate(records):
        if (
            not isinstance(row, Mapping)
            or row.get("pass_index") != index
            or row.get("registered_order") != list(ARMS)
            or any(row.get(name) is not True for name in exact_fields)
            or row.get("baseline_RNG_consumption") != 0
            or not isinstance(row.get("actor_gradient_digest"), str)
            or len(str(row["actor_gradient_digest"])) != 64
        ):
            return False
        cross = row.get("cross_gradient_audit")
        reduced_evidence = row.get("reduced_actor_gradient_evidence")
        reference_evidence = row.get("reference_actor_gradient_evidence")
        if (
            not isinstance(cross, Mapping)
            or cross.get("passed") is not True
            or cross.get("baseline_loss_gradient_into_actor_count") != 0
            or cross.get("actor_loss_gradient_into_baseline_count") != 0
            or not isinstance(reduced_evidence, Mapping)
            or reduced_evidence.get("passed") is not True
            or reduced_evidence.get("baseline_liveness_gate_present") is not False
            or not g46.validate_registered_gradient_evidence(reference_evidence)
        ):
            return False
    return True


def _build_reference_checkpoint_payload(
    model: g41.G41NoSlowProjection,
    optimizer: torch.optim.Optimizer,
    evidence: Mapping[str, object],
) -> dict[str, object]:
    return {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "kind": "final_only",
        "arm": REFERENCE_ARM,
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(
            model.accepted_g40_anchor_authority.replicate
        ),
        "model_state": {
            name: value.detach().cpu().clone()
            for name, value in model.state_dict().items()
        },
        "optimizer_state_by_parameter": _optimizer_state_by_name(
            optimizer, model
        ),
        "baseline_true_state_input_schema": ["critic_states->credit_baselines"],
        "baseline_output_schema": ["immediate", "successor"],
        "checkpoint_selection_evidence": "actor_only_final_update",
        "final_update_evidence": dict(evidence),
    }


def _build_reduced_checkpoint_payload(
    model: G47NoBaselineProjection,
    optimizer: torch.optim.Optimizer,
    evidence: Mapping[str, object],
) -> dict[str, object]:
    if hasattr(model, "credit_baselines") or hasattr(model, "baseline_values"):
        raise G47InvariantError("reduced_checkpoint_baseline_path_present", {})
    return {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "kind": "final_only",
        "arm": REDUCED_ARM,
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(
            model.accepted_g40_anchor_authority.replicate
        ),
        "model_state": {
            name: value.detach().cpu().clone()
            for name, value in model.state_dict().items()
        },
        "optimizer_state_by_parameter": _optimizer_state_by_name(
            optimizer, model
        ),
        "baseline_true_state_input_schema": [],
        "baseline_output_schema": [],
        "checkpoint_selection_evidence": "actor_only_final_update",
        "final_update_evidence": dict(evidence),
    }


def _finalize_checkpoint(payload: dict[str, object]) -> dict[str, object]:
    state = payload["model_state"]
    optimizer = payload["optimizer_state_by_parameter"]
    if not isinstance(state, Mapping) or not isinstance(optimizer, Mapping):
        raise TypeError("G47 checkpoint state schema invalid")
    payload["model_state_digest"] = _state_digest(state)  # type: ignore[arg-type]
    payload["optimizer_state_digest"] = _optimizer_state_digest(optimizer)  # type: ignore[arg-type]
    return payload


def build_final_checkpoints(
    models: Mapping[str, G47Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    final_update_evidence: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    if not validate_dynamic_equivalence(final_update_evidence):
        raise ValueError("G47 final checkpoint evidence invalid")
    reference = models[REFERENCE_ARM]
    reduced = models[REDUCED_ARM]
    if not isinstance(reference, g41.G41NoSlowProjection) or not isinstance(
        reduced, G47NoBaselineProjection
    ):
        raise TypeError("G47 checkpoint model types invalid")
    checkpoints = {
        REFERENCE_ARM: _finalize_checkpoint(
            _build_reference_checkpoint_payload(
                reference, optimizers[REFERENCE_ARM], final_update_evidence
            )
        ),
        REDUCED_ARM: _finalize_checkpoint(
            _build_reduced_checkpoint_payload(
                reduced, optimizers[REDUCED_ARM], final_update_evidence
            )
        ),
    }
    if not validate_checkpoint_pair(checkpoints):
        raise RuntimeError("G47 final checkpoint pair failed validation")
    return checkpoints


def canonical_actor_projection(
    checkpoint: Mapping[str, object],
) -> dict[str, object]:
    state = checkpoint.get("model_state")
    optimizer = checkpoint.get("optimizer_state_by_parameter")
    if not isinstance(state, Mapping) or not isinstance(optimizer, Mapping):
        raise ValueError("G47 checkpoint projection schema invalid")
    actor_state = {
        name: value
        for name, value in state.items()
        if isinstance(name, str)
        and not name.startswith(BASELINE_PARAMETER_PREFIX)
        and isinstance(value, torch.Tensor)
    }
    actor_optimizer = {
        name: row
        for name, row in optimizer.items()
        if isinstance(name, str) and name.startswith(ACTOR_PARAMETER_PREFIX)
    }
    if len(actor_state) != len(state) - sum(
        isinstance(name, str) and name.startswith(BASELINE_PARAMETER_PREFIX)
        for name in state
    ):
        raise ValueError("G47 checkpoint has a non-tensor retained actor row")
    return {
        "actor_state": actor_state,
        "actor_optimizer_state": actor_optimizer,
        "actor_state_digest": _state_digest(actor_state),
        "actor_optimizer_state_digest": _optimizer_state_digest(
            actor_optimizer  # type: ignore[arg-type]
        ),
    }


def validate_checkpoint_pair(value: object) -> bool:
    if not isinstance(value, Mapping) or tuple(value) != ARMS:
        return False
    reference = value.get(REFERENCE_ARM)
    reduced = value.get(REDUCED_ARM)
    if not isinstance(reference, Mapping) or not isinstance(reduced, Mapping):
        return False
    for arm, row in ((REFERENCE_ARM, reference), (REDUCED_ARM, reduced)):
        state = row.get("model_state")
        optimizer = row.get("optimizer_state_by_parameter")
        if (
            row.get("algorithm_id") != ALGORITHM_ID
            or row.get("source_id") != SOURCE_ID
            or row.get("kind") != "final_only"
            or row.get("arm") != arm
            or row.get("checkpoint_selection_evidence")
            != "actor_only_final_update"
            or not isinstance(state, Mapping)
            or not isinstance(optimizer, Mapping)
            or row.get("model_state_digest")
            != _state_digest(state)  # type: ignore[arg-type]
            or row.get("optimizer_state_digest")
            != _optimizer_state_digest(optimizer)  # type: ignore[arg-type]
            or not validate_dynamic_equivalence(row.get("final_update_evidence"))
        ):
            return False
    reference_state = reference["model_state"]
    reduced_state = reduced["model_state"]
    reference_optimizer = reference["optimizer_state_by_parameter"]
    reduced_optimizer = reduced["optimizer_state_by_parameter"]
    if (
        not isinstance(reference_state, Mapping)
        or not isinstance(reduced_state, Mapping)
        or not isinstance(reference_optimizer, Mapping)
        or not isinstance(reduced_optimizer, Mapping)
        or not any(
            str(name).startswith(BASELINE_PARAMETER_PREFIX)
            for name in reference_state
        )
        or any(
            str(name).startswith(BASELINE_PARAMETER_PREFIX)
            for name in reduced_state
        )
        or not any(
            str(name).startswith(BASELINE_PARAMETER_PREFIX)
            for name in reference_optimizer
        )
        or any(
            str(name).startswith(BASELINE_PARAMETER_PREFIX)
            for name in reduced_optimizer
        )
        or reference.get("baseline_true_state_input_schema")
        != ["critic_states->credit_baselines"]
        or reference.get("baseline_output_schema") != ["immediate", "successor"]
        or reduced.get("baseline_true_state_input_schema") != []
        or reduced.get("baseline_output_schema") != []
    ):
        return False
    try:
        left = canonical_actor_projection(reference)
        right = canonical_actor_projection(reduced)
    except (TypeError, ValueError):
        return False
    return bool(
        _state_equal(left["actor_state"], right["actor_state"])  # type: ignore[arg-type]
        and _nested_state_equal(
            left["actor_optimizer_state"],  # type: ignore[arg-type]
            right["actor_optimizer_state"],  # type: ignore[arg-type]
        )
        and left["actor_state_digest"] == right["actor_state_digest"]
        and left["actor_optimizer_state_digest"]
        == right["actor_optimizer_state_digest"]
    )


def serialize_diagnostics(record: Mapping[str, object]) -> str:
    if not validate_dynamic_equivalence(record):
        raise ValueError("G47 refuses to serialize invalid dynamic evidence")
    return json.dumps(record, sort_keys=True, separators=(",", ":"))
