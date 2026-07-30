"""Exact phase-A shadow-baseline deletion for the accepted G50 null route.

Both arms originate from one complete G50 single-immediate initialization.  The
reference keeps the immediate-baseline fitting loss and Adam suffix; the reduced
arm deletes that package before optimizer construction and exposes only the
actor-only G47 replay boundary.  Phase B is the common G49 single-immediate
route with a fresh Adam optimizer.
"""

from __future__ import annotations

import copy
import dis
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import torch
from torch import nn
from torch.nn import functional as F

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_common_fast_anchor_attribution_g50 as g50,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49
    as g49,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47 as g47,
)
from ha_ctse_process.anchored_residual_g19 import (
    AnchoredRosterTrajectory,
    replay_trajectory,
)


ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51"
)
SOURCE_ID = f"{ALGORITHM_ID}_P0"
SCHEMA_VERSION = 1
DESIGN_DISPOSITION = "PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51"

DESIGN_STAGE_COMMIT = "fb16a412841ad69912d927262dae8f694ea5471a"
PREDECESSOR_SOURCE_COMMIT = "044d9690fa19aa07b8e68bf5cbb2a159c19be8c1"
ACCEPTED_G50_FORMAL_SOURCE_COMMIT = "b8290699f5c10c593bbc21a6666c17950fae84d3"
ACCEPTED_G50_EXECUTION_CODE_COMMIT = "23af6bf7c80a4b73c09cf0423f9f539972b1b55d"
ACCEPTED_G50_ALIGNMENT_STAGE_COMMIT = "4df41063d077ace7e0c9212e0cbadbf56e1be4b7"
ACCEPTED_G50_FORMAL_BRANCH = "FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50"

REFERENCE_ARM = "G50_FRESH_SINGLE_IMMEDIATE_WITH_PHASE_A_SHADOW_BASELINE"
REDUCED_ARM = "G50_FRESH_SINGLE_IMMEDIATE_WITHOUT_PHASE_A_BASELINE_MODULE"
ARMS = (REFERENCE_ARM, REDUCED_ARM)

PPO_PASSES = 2
NUM_ENVS = 8
HORIZON = 48
NORMALIZATION_ROWS = NUM_ENVS * HORIZON
MAX_REAL_TRANSITIONS = NORMALIZATION_ROWS
K_SEARCH = 0

INVALID_RESULT = "INVALID_G50_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51"
COUPLING_RESULT = "UNREGISTERED_PHASE_A_SHADOW_BASELINE_COUPLING_G51"
EXACT_RESULT = "PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51"
NUMERICALLY_UNRESOLVED_RESULT = (
    "NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51"
)
RESULT_BRANCHES = (
    INVALID_RESULT,
    COUPLING_RESULT,
    EXACT_RESULT,
    NUMERICALLY_UNRESOLVED_RESULT,
)
ASSESSMENT_ALLOWED_FAILURE_REASONS = (
    "static_certificate_failed_before_optimizer",
    "phase_A_pre_step_semantic_coupling",
    "phase_A_pre_step_numeric_difference",
    "phase_A_actual_Adam_kernel_difference",
)
_PRE_STEP_FAILURE_REASONS = (
    "phase_A_pre_step_semantic_coupling",
    "phase_A_pre_step_numeric_difference",
)
_PRE_STEP_NUMERIC_EQUALITY_KEYS = (
    "actor_assigned_gradient_bytes_equal",
    "policy_loss_bytes_equal",
    "teacher_logprob_bytes_equal",
    "teacher_pre_tanh_bytes_equal",
    "teacher_action_bytes_equal",
)
_PRE_STEP_CROSS_GRADIENT_COUNT_KEYS = (
    "baseline_loss_gradient_into_actor_count",
    "actor_loss_gradient_into_baseline_count",
)
_PRE_STEP_COMPARISON_KEYS = frozenset(
    (*_PRE_STEP_NUMERIC_EQUALITY_KEYS, *_PRE_STEP_CROSS_GRADIENT_COUNT_KEYS,
     "plan_RNG_unchanged")
)

ACTOR_PARAMETER_PREFIX = "policy."
BASELINE_PARAMETER_PREFIX = "credit_baselines."
_BASELINE_RESIDUE_TOKENS = (
    "baseline",
    "critic_state",
    "true_state",
    "dummy",
    "compatibility",
)
_PHASE_BOUNDARY_COMMON_KEYS = {
    "completed_phase_A_updates",
    "retained_actor_bytes_equal",
    "phase_A_state_deleted",
    "fresh_phase_B_state_required",
    "projection_optimizer_steps",
    "projection_RNG_consumption",
    "passed",
}
_SOURCE_PROVENANCE_KEYS = {
    "implementation_commit",
    "design_stage_commit",
    "predecessor_source_commit",
    "accepted_G50_formal_source_commit",
    "accepted_G50_execution_code_commit",
    "accepted_G50_alignment_stage_commit",
    "accepted_G50_formal_branch",
}
_PHASE_B_ZERO_STEP_PREDICATE_KEYS = (
    "same_stored_actor_trajectory",
    "g49_single_probe_identity_bound",
    "g49_apply_pass_identity_bound",
    "single_immediate_normalization_once",
    "actor_state_bytes_equal",
    "log_std_bytes_equal",
    "actor_parameter_order_equal",
    "actor_optimizer_parameter_order_equal",
    "actor_optimizer_hyperparameters_equal",
    "actor_Adam_state_fresh_equal",
    "actor_Adam_storage_disjoint",
    "assigned_actor_gradient_bytes_equal",
    "actor_trace_equal",
    "RNG_unchanged",
    "model_state_unchanged",
    "optimizer_state_unchanged",
    "gradient_slots_unchanged",
    "zero_optimizer_steps",
)
_PHASE_B_ZERO_STEP_KEYS = {
    "certificate_kind",
    "algorithm_id",
    "phase_B_route",
    "single_probe_identity",
    "apply_pass_identity",
    "normalization_record",
    "target_digest",
    "normalized_digest",
    "actor_parameter_names",
    "optimizer_parameter_names",
    "optimizer_hyperparameters",
    "assigned_gradient_digest",
    "actor_trace",
    "predicates",
    "episodes",
    "H",
    "real_transitions",
    "phase_B_optimizer_steps",
    "K_search",
    "passed",
}


class G51InvariantError(ValueError):
    """A frozen G51 construction or exact-equivalence predicate failed."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object] | None = None):
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics or {})
        super().__init__(f"G51 invariant failed: {self.reason}")

    def __reduce__(self) -> tuple[type[G51InvariantError], tuple[str, dict[str, object]]]:
        return type(self), (self.reason, dict(self.diagnostics))

    def to_record(self) -> dict[str, object]:
        return {"passed": False, "reason": self.reason, "diagnostics": self.diagnostics}


class G51NoBaselinePhaseAProjection(g47.G47NoBaselineProjection):
    """Storage-disjoint G50 phase-A actor with no baseline callable or state."""

    def __init__(self, source: g40.G40NativeSixPolicy) -> None:
        nn.Module.__init__(self)
        rng_before = torch.random.get_rng_state().clone()
        self.policy = copy.deepcopy(source.policy)
        # G51 deletes only the phase-A shadow baseline treatment.  The accepted
        # G50 slow critic remains as storage-disjoint, optimizer-unexposed
        # phase-A state and is removed later by the ordinary G50 phase boundary.
        self.slow_critic = copy.deepcopy(source.slow_critic)
        self.member_capacity = int(source.member_capacity)
        self.critic_state_dim = int(source.critic_state_dim)
        self.phase = str(source.phase)
        self.projection_rng_unchanged = bool(
            torch.equal(rng_before, torch.random.get_rng_state())
        )
        if not self.projection_rng_unchanged:
            raise G51InvariantError("phase_A_projection_consumed_RNG")

    def begin_credit_branch_phase(self) -> None:
        if self.phase == "credit_branch":
            return
        super().begin_credit_branch_phase()


G51Model = g40.G40NativeSixPolicy | G51NoBaselinePhaseAProjection


@dataclass(frozen=True)
class _ReducedPlan:
    policy_loss: torch.Tensor
    entropy_objective: torch.Tensor
    assigned: tuple[torch.Tensor, ...]
    replay: g47.G47ActorReplay


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    return g50.seed_block(replicate, formal=formal)


def bootstrap_seed(*, formal: bool) -> int:
    return g50.bootstrap_seed(formal=formal)


def _tensor_digest(value: torch.Tensor) -> str:
    return g50._tensor_digest(value)


def _parameter_names(model: nn.Module, parameters: Sequence[nn.Parameter]) -> tuple[str, ...]:
    by_id = {id(parameter): name for name, parameter in model.named_parameters()}
    return tuple(by_id.get(id(parameter), "<foreign>") for parameter in parameters)


def _optimizer_parameters(optimizer: torch.optim.Optimizer) -> tuple[nn.Parameter, ...]:
    return tuple(parameter for group in optimizer.param_groups for parameter in group["params"])


def _actor_names(model: G51Model) -> tuple[str, ...]:
    return _parameter_names(model, model.full_actor_parameters())


def _actor_state(model: nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
        if name.startswith(ACTOR_PARAMETER_PREFIX)
        and not name.startswith("policy.critic.")
        and not name.startswith("policy.delayed_residual.")
    }


def _state_equal(left: Mapping[str, torch.Tensor], right: Mapping[str, torch.Tensor]) -> bool:
    return tuple(left) == tuple(right) and all(torch.equal(left[name], right[name]) for name in left)


def _clone_value(value: object) -> object:
    return value.detach().cpu().clone() if isinstance(value, torch.Tensor) else copy.deepcopy(value)


def _optimizer_state_by_name(
    optimizer: torch.optim.Optimizer, model: nn.Module, *, actor_only: bool = False
) -> dict[str, dict[str, object]]:
    names = _parameter_names(model, _optimizer_parameters(optimizer))
    if "<foreign>" in names:
        raise G51InvariantError("optimizer_contains_foreign_parameter")
    return {
        name: {key: _clone_value(value) for key, value in sorted(optimizer.state.get(parameter, {}).items())}
        for name, parameter in zip(names, _optimizer_parameters(optimizer))
        if not actor_only or name in _actor_names(model)  # type: ignore[arg-type]
    }


def _nested_equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return torch.equal(left, right)
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return tuple(left) == tuple(right) and all(_nested_equal(left[key], right[key]) for key in left)
    if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        return len(left) == len(right) and all(_nested_equal(a, b) for a, b in zip(left, right))
    return left == right


def _optimizer_hyperparameters(optimizer: torch.optim.Optimizer) -> dict[str, object]:
    if not isinstance(optimizer, torch.optim.Adam) or len(optimizer.param_groups) != 1:
        return {"valid": False}
    group = optimizer.param_groups[0]
    return {
        "valid": True,
        **{name: group.get(name) for name in (
            "lr", "betas", "eps", "weight_decay", "amsgrad", "maximize",
            "foreach", "capturable", "differentiable", "fused",
        )},
    }


def _callable_identity(function: Any) -> dict[str, str]:
    code = function.__code__
    digest = hashlib.sha256()
    digest.update(code.co_code)
    digest.update(repr(code.co_names).encode("utf-8"))
    digest.update(repr(code.co_varnames).encode("utf-8"))
    return {
        "module": str(function.__module__),
        "qualname": str(function.__qualname__),
        "code_digest": digest.hexdigest(),
    }


def _gradient_slots(model: nn.Module) -> tuple[torch.Tensor | None, ...]:
    return tuple(
        None if parameter.grad is None else parameter.grad.detach().clone()
        for parameter in model.parameters()
    )


def _optimizer_ledger(
    *,
    paired_passes: int,
    failure_detected_before_current_pair: bool,
) -> dict[str, object]:
    passes = int(paired_passes)
    return {
        "reference_actor_steps": passes,
        "reduced_actor_steps": passes,
        "reference_baseline_parameter_Adam_exposures": passes,
        "reduced_baseline_parameter_Adam_exposures": 0,
        "completed_paired_passes": passes,
        "phase_B_steps": 0,
        "failure_detected_before_current_pair": bool(
            failure_detected_before_current_pair
        ),
        "no_steps_after_detection": True,
    }


def validate_optimizer_ledger(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != {
        "reference_actor_steps", "reduced_actor_steps",
        "reference_baseline_parameter_Adam_exposures",
        "reduced_baseline_parameter_Adam_exposures",
        "completed_paired_passes", "phase_B_steps",
        "failure_detected_before_current_pair", "no_steps_after_detection",
    }:
        return False
    passes = value.get("completed_paired_passes")
    return bool(
        isinstance(passes, int) and not isinstance(passes, bool)
        and 0 <= passes <= PPO_PASSES
        and value.get("reference_actor_steps") == passes
        and value.get("reduced_actor_steps") == passes
        and value.get("reference_baseline_parameter_Adam_exposures") == passes
        and value.get("reduced_baseline_parameter_Adam_exposures") == 0
        and value.get("phase_B_steps") == 0
        and value.get("failure_detected_before_current_pair") in (True, False)
        and value.get("no_steps_after_detection") is True
    )


def _storage_ids(module: nn.Module) -> set[int]:
    return {
        int(value.untyped_storage().data_ptr())
        for value in (*module.parameters(), *module.buffers())
        if value.numel()
    }


def make_phase_A_models(
    *, member_capacity: int, initialization_seed: int
) -> dict[str, G51Model]:
    inherited = g50.make_phase_A_models(
        member_capacity=int(member_capacity), initialization_seed=int(initialization_seed)
    )
    source = inherited[g50.NULL_ARM]
    rng_before = torch.random.get_rng_state().clone()
    reference = copy.deepcopy(source)
    reduced = G51NoBaselinePhaseAProjection(source)
    models: dict[str, G51Model] = {REFERENCE_ARM: reference, REDUCED_ARM: reduced}
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise G51InvariantError("phase_A_projection_consumed_RNG")
    if not _state_equal(_actor_state(reference), _actor_state(reduced)):
        raise G51InvariantError("phase_A_actor_bytes_changed_by_projection")
    if g40.shared_tensor_storage_count(tuple(models.values())) != 0:
        raise G51InvariantError("phase_A_arm_storage_alias")
    if hasattr(reduced, "credit_baselines") or any(
        BASELINE_PARAMETER_PREFIX in name for name in reduced.state_dict()
    ):
        raise G51InvariantError("reduced_phase_A_retained_module")
    return models


def make_phase_A_optimizers(
    models: Mapping[str, G51Model],
) -> dict[str, torch.optim.Adam]:
    if tuple(models) != ARMS:
        raise ValueError("G51 phase-A optimizer construction requires exact arms")
    reference = models[REFERENCE_ARM]
    reduced = models[REDUCED_ARM]
    if not isinstance(reference, g40.G40NativeSixPolicy) or not isinstance(
        reduced, G51NoBaselinePhaseAProjection
    ):
        raise TypeError("G51 phase-A model types invalid")
    optimizers = {
        REFERENCE_ARM: torch.optim.Adam(
            reference.actor_credit_parameters(), lr=g40.LEARNING_RATE,
            betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, amsgrad=False,
        ),
        REDUCED_ARM: torch.optim.Adam(
            reduced.full_actor_parameters(), lr=g40.LEARNING_RATE,
            betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, amsgrad=False,
        ),
    }
    if any(optimizer.state for optimizer in optimizers.values()):
        raise G51InvariantError("phase_A_Adam_not_fresh")
    return optimizers


def phase_A_boundary_audit(
    models: Mapping[str, G51Model], optimizers: Mapping[str, torch.optim.Optimizer]
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS:
        return {"passed": False, "inventory_valid": False}
    reference, reduced = models[REFERENCE_ARM], models[REDUCED_ARM]
    if not isinstance(reference, g40.G40NativeSixPolicy) or not isinstance(
        reduced, G51NoBaselinePhaseAProjection
    ):
        return {"passed": False, "model_types_valid": False}
    actor_names = _actor_names(reference)
    reduced_actor_names = _actor_names(reduced)
    baseline_names = tuple(
        name for name, _ in reference.named_parameters() if name.startswith(BASELINE_PARAMETER_PREFIX)
    )
    reference_optimizer_names = _parameter_names(reference, _optimizer_parameters(optimizers[REFERENCE_ARM]))
    reduced_optimizer_names = _parameter_names(reduced, _optimizer_parameters(optimizers[REDUCED_ARM]))
    actor_equal = _state_equal(_actor_state(reference), _actor_state(reduced))
    reference_retained_state = {
        name: value
        for name, value in reference.state_dict().items()
        if not name.startswith(BASELINE_PARAMETER_PREFIX)
    }
    reduced_state = reduced.state_dict()
    only_baseline_delta = tuple(reference_retained_state) == tuple(reduced_state) and all(
        torch.equal(reference_retained_state[name], reduced_state[name])
        for name in reference_retained_state
    )
    slow_state_equal = g40.state_bytes(reference.slow_critic) == g40.state_bytes(
        reduced.slow_critic
    )
    slow_masks_equal = tuple(
        parameter.requires_grad for parameter in reference.slow_critic.parameters()
    ) == tuple(parameter.requires_grad for parameter in reduced.slow_critic.parameters())
    storage_count = g40.shared_tensor_storage_count(tuple(models.values()))
    actor_baseline_storage = len(_storage_ids(reference.policy) & _storage_ids(reference.credit_baselines))
    hyper_equal = _optimizer_hyperparameters(optimizers[REFERENCE_ARM]) == _optimizer_hyperparameters(optimizers[REDUCED_ARM])
    passed = bool(
        actor_equal and torch.equal(reference.log_std, reduced.log_std)
        and actor_names == reduced_actor_names
        and reference_optimizer_names == actor_names + baseline_names
        and reduced_optimizer_names == actor_names
        and not optimizers[REFERENCE_ARM].state and not optimizers[REDUCED_ARM].state
        and storage_count == 0 and actor_baseline_storage == 0 and hyper_equal
        and only_baseline_delta and slow_state_equal and slow_masks_equal
        and not hasattr(reduced, "credit_baselines")
    )
    return {
        "inventory_valid": True,
        "actor_state_bytes_equal": actor_equal,
        "log_std_bytes_equal": torch.equal(reference.log_std, reduced.log_std),
        "actor_parameter_names_equal": actor_names == reduced_actor_names,
        "actor_parameter_shapes_equal": tuple(p.shape for p in reference.full_actor_parameters()) == tuple(p.shape for p in reduced.full_actor_parameters()),
        "actor_parameter_order_equal": actor_names == reduced_actor_names,
        "actor_trainable_masks_equal": tuple(p.requires_grad for p in reference.full_actor_parameters()) == tuple(p.requires_grad for p in reduced.full_actor_parameters()),
        "slow_critic_state_bytes_equal": slow_state_equal,
        "slow_critic_trainable_masks_equal": slow_masks_equal,
        "only_phase_A_module_and_state_delta_is_credit_baselines": only_baseline_delta,
        "actor_parameter_names": list(actor_names),
        "reference_baseline_parameter_names": list(baseline_names),
        "reference_optimizer_parameter_names": list(reference_optimizer_names),
        "reduced_optimizer_parameter_names": list(reduced_optimizer_names),
        "reference_actor_prefix_then_baseline_suffix": reference_optimizer_names == actor_names + baseline_names,
        "reduced_actor_only": reduced_optimizer_names == actor_names,
        "shared_actor_parameter_storage_count": storage_count,
        "baseline_parameter_storage_shared_with_actor": actor_baseline_storage,
        "optimizer_hyperparameters_equal": hyper_equal,
        "optimizer_states_empty": not optimizers[REFERENCE_ARM].state and not optimizers[REDUCED_ARM].state,
        "projection_RNG_consumption": 0,
        "projection_optimizer_steps": 0,
        "passed": passed,
    }


def _bytecode_reads(functions: Sequence[Any]) -> list[str]:
    return sorted({
        str(instruction.argval)
        for function in functions
        for instruction in dis.get_instructions(function)
        if instruction.opname in {"LOAD_ATTR", "LOAD_METHOD", "LOAD_GLOBAL"}
    })


def _module_graph(module: nn.Module) -> dict[str, object]:
    return {
        "modules": [
            {"name": name, "type": type(row).__qualname__}
            for name, row in module.named_modules()
        ],
        "parameters": [
            {
                "name": name,
                "shape": list(parameter.shape),
                "requires_grad": parameter.requires_grad,
                "storage": int(parameter.untyped_storage().data_ptr()),
            }
            for name, parameter in module.named_parameters()
        ],
        "buffers": [
            {
                "name": name,
                "shape": list(buffer.shape),
                "storage": int(buffer.untyped_storage().data_ptr()),
            }
            for name, buffer in module.named_buffers()
        ],
    }


def _reference_baseline_forward_audit(
    reference: g40.G40NativeSixPolicy,
) -> dict[str, object]:
    baseline = reference.credit_baselines
    modules = tuple(baseline.modules())
    forward_hook_count = sum(
        len(row._forward_pre_hooks) + len(row._forward_hooks) for row in modules
    )
    backward_hook_count = sum(len(row._backward_hooks) for row in modules)
    stochastic_module_count = sum(
        isinstance(row, (nn.Dropout, nn.AlphaDropout, nn.FeatureAlphaDropout))
        for row in modules
    )
    buffers_before = g40.buffer_bytes(baseline)
    rng_before = torch.random.get_rng_state().clone()
    parameter = next(baseline.parameters())
    output = baseline(
        torch.zeros(
            (2, reference.critic_state_dim),
            dtype=parameter.dtype,
            device=parameter.device,
        )
    )
    rng_change_count = int(
        not torch.equal(rng_before, torch.random.get_rng_state())
    )
    buffer_mutation_count = int(buffers_before != g40.buffer_bytes(baseline))
    return {
        "input_schema": [2, int(reference.critic_state_dim)],
        "output_schema": list(output.shape),
        "output_finite": bool(torch.isfinite(output).all()),
        "RNG_change_count": rng_change_count,
        "buffer_mutation_count": buffer_mutation_count,
        "forward_hook_count": forward_hook_count,
        "backward_hook_count": backward_hook_count,
        "stochastic_module_count": stochastic_module_count,
    }


def _operation_token_count(functions: Sequence[Any], tokens: Sequence[str]) -> int:
    reads = _bytecode_reads(functions)
    return sum(any(token in row.lower() for token in tokens) for row in reads)


def reconstruct_static_certificate(
    models: Mapping[str, G51Model], optimizers: Mapping[str, torch.optim.Optimizer]
) -> dict[str, object]:
    boundary = phase_A_boundary_audit(models, optimizers)
    reduced = models.get(REDUCED_ARM)
    reference = models.get(REFERENCE_ARM)
    if not isinstance(reference, g40.G40NativeSixPolicy) or not isinstance(
        reduced, G51NoBaselinePhaseAProjection
    ):
        return {"passed": False, "model_types_valid": False}
    components = {
        "actor_gradient": (g47._actor_only_trajectory_view, g47.actor_only_replay, _reduced_plan),
        "entropy": (_reduced_plan,),
        "action_or_logprob": (g47._actor_only_step, g47.actor_only_replay),
        "source_or_lifecycle": (g47._source_trace_evidence,),
        "checkpoint_selection": (canonical_actor_projection,),
        "evaluation": (g47._actor_only_step,),
        "result_selection": (classify_result,),
    }
    reads = {name: _bytecode_reads(functions) for name, functions in components.items()}
    forbidden = {
        name: [row for row in values if any(token in row.lower() for token in _BASELINE_RESIDUE_TOKENS[:3])]
        for name, values in reads.items()
    }
    reference_actor = tuple(reference.full_actor_parameters())
    baseline_parameters = tuple(reference.credit_baselines.parameters())
    reduced_actor = tuple(reduced.full_actor_parameters())
    actor_ids = {id(row) for row in reference_actor}
    baseline_ids = {id(row) for row in baseline_parameters}
    actor_storage = {
        int(row.untyped_storage().data_ptr()) for row in reference_actor if row.numel()
    }
    baseline_storage = {
        int(row.untyped_storage().data_ptr())
        for row in baseline_parameters
        if row.numel()
    }
    reference_graph = _module_graph(reference)
    reduced_graph = _module_graph(reduced)
    baseline_forward = _reference_baseline_forward_audit(reference)
    reduced_named_modules = tuple(name for name, _ in reduced.named_modules())
    reduced_named_parameters = tuple(name for name, _ in reduced.named_parameters())
    reduced_state_keys = tuple(reduced.state_dict())
    static_predicates = {
        "shared_actor_baseline_parameter_count": len(actor_ids & baseline_ids),
        "shared_actor_baseline_storage_count": len(actor_storage & baseline_storage),
        "reduced_baseline_module_count": sum(
            "baseline" in name.lower() for name in reduced_named_modules
        ),
        "reduced_baseline_parameter_count": sum(
            "baseline" in name.lower() for name in reduced_named_parameters
        ),
        "reduced_baseline_state_key_count": sum(
            "baseline" in name.lower() for name in reduced_state_keys
        ),
        "reduced_actor_gradient_forbidden_read_count": len(forbidden["actor_gradient"]),
        "reduced_entropy_forbidden_read_count": len(forbidden["entropy"]),
        "reduced_action_logprob_forbidden_read_count": len(forbidden["action_or_logprob"]),
        "reduced_source_lifecycle_forbidden_read_count": len(forbidden["source_or_lifecycle"]),
        "reduced_checkpoint_forbidden_read_count": len(forbidden["checkpoint_selection"]),
        "reduced_evaluation_forbidden_read_count": len(forbidden["evaluation"]),
        "reduced_result_forbidden_read_count": len(forbidden["result_selection"]),
        "reference_baseline_forward_RNG_change_count": int(
            baseline_forward["RNG_change_count"]
        ),
        "reference_baseline_buffer_mutation_count": int(
            baseline_forward["buffer_mutation_count"]
        ),
        "reference_baseline_forward_hook_count": int(
            baseline_forward["forward_hook_count"]
        ),
        "reference_baseline_backward_hook_count": int(
            baseline_forward["backward_hook_count"]
        ),
        "reference_baseline_stochastic_module_count": int(
            baseline_forward["stochastic_module_count"]
        ),
    }
    step_functions = (g50._assign_and_step, _apply_reduced_pass, g40._optimizer_step)
    reference_optimizer_names = _parameter_names(
        reference, _optimizer_parameters(optimizers[REFERENCE_ARM])
    )
    reduced_optimizer_names = _parameter_names(
        reduced, _optimizer_parameters(optimizers[REDUCED_ARM])
    )
    group_selector_count = sum(
        group.get(name) is not False
        for optimizer in optimizers.values()
        for group in optimizer.param_groups
        for name in ("foreach", "fused")
    )
    parameter_list_size_difference = abs(
        len(_optimizer_parameters(optimizers[REFERENCE_ARM]))
        - len(_optimizer_parameters(optimizers[REDUCED_ARM]))
    )
    optimizer_predicates = {
        "actual_optimizer_is_Adam": all(
            isinstance(row, torch.optim.Adam) for row in optimizers.values()
        ),
        "actor_parameter_order_equal": _actor_names(reference)
        == _actor_names(reduced),
        "reference_actor_prefix_baseline_suffix": reference_optimizer_names
        == _actor_names(reference)
        + tuple(
            name
            for name, _ in reference.named_parameters()
            if name.startswith(BASELINE_PARAMETER_PREFIX)
        ),
        "reduced_actor_only_order": reduced_optimizer_names
        == _actor_names(reduced),
        "actor_hyperparameters_equal": _optimizer_hyperparameters(
            optimizers[REFERENCE_ARM]
        )
        == _optimizer_hyperparameters(optimizers[REDUCED_ARM]),
        "fresh_actor_state_rows_equal_not_factorization": _nested_equal(
            _optimizer_state_by_name(
                optimizers[REFERENCE_ARM], reference, actor_only=True
            ),
            _optimizer_state_by_name(
                optimizers[REDUCED_ARM], reduced, actor_only=True
            ),
        ),
        "global_gradient_clipping_call_count": _operation_token_count(
            step_functions, ("clip_grad",)
        ),
        "joint_gradient_normalization_call_count": _operation_token_count(
            step_functions, ("normalize_grad", "global_norm")
        ),
        "loss_count_scaling_call_count": _operation_token_count(
            step_functions, ("loss_count",)
        ),
        "optimizer_group_size_scaling_call_count": _operation_token_count(
            step_functions, ("group_size", "parameter_count")
        ),
        "non_parameter_optimizer_state_count": sum(
            not isinstance(key, nn.Parameter)
            for optimizer in optimizers.values()
            for key in optimizer.state
        ),
        "scheduler_attachment_count": sum(
            "scheduler" in str(name).lower()
            for optimizer in optimizers.values()
            for name in optimizer.__dict__
        ),
        "cross_parameter_moment_reduction_call_count": _operation_token_count(
            step_functions, ("moment_reduction", "multi_tensor_norm")
        ),
        "parameter_list_kernel_selector_count": group_selector_count,
        "parameter_list_size_difference": parameter_list_size_difference,
        "actual_kernel_witness_required": bool(
            group_selector_count or parameter_list_size_difference
        ),
    }
    reduced_schema_absent = not hasattr(reduced, "credit_baselines") and all(
        not name.startswith(BASELINE_PARAMETER_PREFIX) for name in reduced.state_dict()
    )
    passed = bool(
        boundary.get("passed") is True
        and all(not values for values in forbidden.values())
        and all(value == 0 for value in static_predicates.values())
        and all(optimizer_predicates[name] is True for name in (
            "actual_optimizer_is_Adam", "actor_parameter_order_equal",
            "reference_actor_prefix_baseline_suffix", "reduced_actor_only_order",
            "actor_hyperparameters_equal",
            "fresh_actor_state_rows_equal_not_factorization",
            "actual_kernel_witness_required",
        ))
        and all(
            optimizer_predicates[name] == 0
            for name in (
                "global_gradient_clipping_call_count",
                "joint_gradient_normalization_call_count",
                "loss_count_scaling_call_count",
                "optimizer_group_size_scaling_call_count",
                "non_parameter_optimizer_state_count",
                "scheduler_attachment_count",
                "cross_parameter_moment_reduction_call_count",
            )
        )
        and reduced_schema_absent
        and baseline_forward["output_finite"] is True
    )
    return {
        "certificate_kind": "actual_zero_trajectory_dependency_graph_with_witness_required_Adam_closure",
        "boundary": boundary,
        "reference_module_parameter_graph": reference_graph,
        "reduced_module_parameter_graph": reduced_graph,
        "reference_baseline_forward_audit": baseline_forward,
        "path_identities": {
            "reference_plan": _callable_identity(g50._phase_A_plan),
            "reference_step": _callable_identity(g50._assign_and_step),
            "reduced_plan": _callable_identity(_reduced_plan),
            "reduced_step": _callable_identity(_apply_reduced_pass),
            "Adam_step": _callable_identity(torch.optim.Adam.step),
            "registered_optimizer_step": _callable_identity(g40._optimizer_step),
        },
        "component_bytecode_reads": reads,
        "forbidden_reduced_dependency_reads": forbidden,
        "static_predicates": static_predicates,
        "optimizer_predicates": optimizer_predicates,
        "reduced_module_parameter_state_and_callable_absent": reduced_schema_absent,
        "witness_closure_requirements": [
            "actual_autograd_cross_gradient_zero",
            "actual_assigned_actor_gradients_equal",
            "actual_kernel_actor_Adam_step_exp_avg_exp_avg_sq_equal",
        ],
        "K_search": K_SEARCH,
        "hypothetical_transitions": 0,
        "formal_statistical_run": False,
        "passed": passed,
    }


def validate_static_certificate(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    static = value.get("static_predicates")
    optimizer = value.get("optimizer_predicates")
    forbidden = value.get("forbidden_reduced_dependency_reads")
    boundary = value.get("boundary")
    reference_graph = value.get("reference_module_parameter_graph")
    reduced_graph = value.get("reduced_module_parameter_graph")
    baseline_audit = value.get("reference_baseline_forward_audit")
    reduced_modules = (
        reduced_graph.get("modules") if isinstance(reduced_graph, Mapping) else None
    )
    reduced_parameters = (
        reduced_graph.get("parameters") if isinstance(reduced_graph, Mapping) else None
    )
    return bool(
        value.get("certificate_kind")
        == "actual_zero_trajectory_dependency_graph_with_witness_required_Adam_closure"
        and isinstance(value.get("reference_module_parameter_graph"), Mapping)
        and isinstance(value.get("reduced_module_parameter_graph"), Mapping)
        and isinstance(value.get("reference_baseline_forward_audit"), Mapping)
        and isinstance(boundary, Mapping) and boundary.get("passed") is True
        and isinstance(reference_graph, Mapping)
        and isinstance(reference_graph.get("modules"), list)
        and any(
            "credit_baselines" in str(row.get("name"))
            for row in reference_graph["modules"]
            if isinstance(row, Mapping)
        )
        and isinstance(reduced_modules, list)
        and isinstance(reduced_parameters, list)
        and isinstance(baseline_audit, Mapping)
        and set(baseline_audit) == {
            "input_schema", "output_schema", "output_finite",
            "RNG_change_count", "buffer_mutation_count", "forward_hook_count",
            "backward_hook_count", "stochastic_module_count",
        }
        and isinstance(baseline_audit.get("input_schema"), list)
        and len(baseline_audit["input_schema"]) == 2
        and baseline_audit["input_schema"][0] == 2
        and isinstance(baseline_audit["input_schema"][1], int)
        and baseline_audit["input_schema"][1] > 0
        and baseline_audit.get("output_schema") == [2, 2]
        and baseline_audit.get("output_finite") is True
        and value.get("path_identities")
        == {
            "reference_plan": _callable_identity(g50._phase_A_plan),
            "reference_step": _callable_identity(g50._assign_and_step),
            "reduced_plan": _callable_identity(_reduced_plan),
            "reduced_step": _callable_identity(_apply_reduced_pass),
            "Adam_step": _callable_identity(torch.optim.Adam.step),
            "registered_optimizer_step": _callable_identity(g40._optimizer_step),
        }
        and isinstance(static, Mapping) and static
        and all(row == 0 for row in static.values())
        and static.get("reduced_baseline_module_count") == sum(
            "baseline" in str(row.get("name", "")).lower()
            for row in reduced_modules if isinstance(row, Mapping)
        )
        and static.get("reduced_baseline_parameter_count") == sum(
            "baseline" in str(row.get("name", "")).lower()
            for row in reduced_parameters if isinstance(row, Mapping)
        )
        and static.get("reference_baseline_forward_RNG_change_count")
        == baseline_audit.get("RNG_change_count")
        and static.get("reference_baseline_buffer_mutation_count")
        == baseline_audit.get("buffer_mutation_count")
        and static.get("reference_baseline_forward_hook_count")
        == baseline_audit.get("forward_hook_count")
        and static.get("reference_baseline_backward_hook_count")
        == baseline_audit.get("backward_hook_count")
        and static.get("reference_baseline_stochastic_module_count")
        == baseline_audit.get("stochastic_module_count")
        and isinstance(forbidden, Mapping) and forbidden
        and all(row == [] for row in forbidden.values())
        and isinstance(optimizer, Mapping)
        and all(optimizer.get(name) is True for name in (
            "actual_optimizer_is_Adam", "actor_parameter_order_equal",
            "reference_actor_prefix_baseline_suffix", "reduced_actor_only_order",
            "actor_hyperparameters_equal",
            "fresh_actor_state_rows_equal_not_factorization",
            "actual_kernel_witness_required",
        ))
        and all(optimizer.get(name) == 0 for name in (
            "global_gradient_clipping_call_count",
            "joint_gradient_normalization_call_count",
            "loss_count_scaling_call_count",
            "optimizer_group_size_scaling_call_count",
            "non_parameter_optimizer_state_count",
            "scheduler_attachment_count",
            "cross_parameter_moment_reduction_call_count",
        ))
        and isinstance(optimizer.get("parameter_list_kernel_selector_count"), int)
        and optimizer.get("parameter_list_kernel_selector_count") > 0
        and isinstance(optimizer.get("parameter_list_size_difference"), int)
        and optimizer.get("parameter_list_size_difference") > 0
        and value.get("witness_closure_requirements") == [
            "actual_autograd_cross_gradient_zero",
            "actual_assigned_actor_gradients_equal",
            "actual_kernel_actor_Adam_step_exp_avg_exp_avg_sq_equal",
        ]
        and value.get("reduced_module_parameter_state_and_callable_absent") is True
        and value.get("K_search") == 0 and value.get("hypothetical_transitions") == 0
        and value.get("formal_statistical_run") is False
    )


def _gradient_rows(
    objective: torch.Tensor, parameters: Sequence[nn.Parameter], *, retain_graph: bool = True
) -> tuple[torch.Tensor, ...]:
    rows = torch.autograd.grad(objective, parameters, retain_graph=retain_graph, allow_unused=True)
    output = tuple(torch.zeros_like(parameter) if row is None else row.detach().clone() for row, parameter in zip(rows, parameters))
    if any(not bool(torch.isfinite(row).all()) for row in output):
        raise G51InvariantError("nonfinite_actor_gradient")
    return output


def _reduced_plan(
    model: G51NoBaselinePhaseAProjection,
    trajectory: g47.G47ActorTrajectory,
    normalized: torch.Tensor,
) -> _ReducedPlan:
    replay = g47.actor_only_replay(model, trajectory)
    policy = g40._policy_loss_from_normalized_advantage(replay, trajectory, normalized)
    entropy = -g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
    parameters = model.full_actor_parameters()
    actor_rows = _gradient_rows(policy, parameters)
    entropy_rows = _gradient_rows(entropy, parameters)
    return _ReducedPlan(
        policy_loss=policy,
        entropy_objective=entropy,
        assigned=tuple(a + b for a, b in zip(actor_rows, entropy_rows)),
        replay=replay,
    )


def _apply_reduced_pass(
    model: G51NoBaselinePhaseAProjection,
    optimizer: torch.optim.Optimizer,
    assigned: Sequence[torch.Tensor],
) -> None:
    parameters = model.full_actor_parameters()
    if tuple(id(row) for row in _optimizer_parameters(optimizer)) != tuple(id(row) for row in parameters):
        raise G51InvariantError("reduced_optimizer_parameter_order_invalid")
    optimizer.zero_grad(set_to_none=True)
    for parameter, gradient in zip(parameters, assigned):
        parameter.grad = gradient.detach().clone()
    g40._optimizer_step(optimizer, parameters)


def _actor_adam_equal(
    models: Mapping[str, G51Model], optimizers: Mapping[str, torch.optim.Optimizer]
) -> bool:
    return _nested_equal(
        _optimizer_state_by_name(optimizers[REFERENCE_ARM], models[REFERENCE_ARM], actor_only=True),
        _optimizer_state_by_name(optimizers[REDUCED_ARM], models[REDUCED_ARM], actor_only=True),
    )


def optimize_phase_A_update(
    models: Mapping[str, G51Model],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectory: AnchoredRosterTrajectory,
    *,
    update_index: int = 0,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, object]:
    if int(ppo_passes) != PPO_PASSES:
        raise ValueError("G51 witness requires exactly two PPO passes")
    if trajectory.rewards.numel() != NORMALIZATION_ROWS:
        raise ValueError("G51 witness requires one stored 8x48 trajectory")
    static = reconstruct_static_certificate(models, optimizers)
    if not validate_static_certificate(static):
        raise G51InvariantError("static_certificate_failed_before_optimizer", static)
    reference, reduced = models[REFERENCE_ARM], models[REDUCED_ARM]
    if not isinstance(reference, g40.G40NativeSixPolicy) or not isinstance(reduced, G51NoBaselinePhaseAProjection):
        raise TypeError("G51 phase-A model types invalid")
    normalization = g49._normalize_single(g49._single_immediate_target(trajectory.rewards))
    reduced_trajectory = g47._actor_only_trajectory_view(trajectory)
    source_trace = g47._source_trace_evidence(trajectory)
    pass_records: list[dict[str, object]] = []
    rng_before = torch.random.get_rng_state().clone()
    for pass_index in range(PPO_PASSES):
        plan_rng_before = torch.random.get_rng_state().clone()
        reference_plan = g50._phase_A_plan(
            arm=g50.NULL_ARM, model=reference, trajectory=trajectory,
            normalized_actor_credit=normalization.normalized,
            baseline_trajectory=trajectory,
        )
        reduced_plan = _reduced_plan(reduced, reduced_trajectory, normalization.normalized)
        plan_rng_unchanged = torch.equal(
            plan_rng_before, torch.random.get_rng_state()
        )
        baseline_into_actor = torch.autograd.grad(
            reference_plan.baseline_loss, reference.full_actor_parameters(),
            retain_graph=True, allow_unused=True,
        )
        actor_into_baseline = torch.autograd.grad(
            reference_plan.policy_loss, tuple(reference.credit_baselines.parameters()),
            retain_graph=True, allow_unused=True,
        )
        reference_replay = replay_trajectory(reference, trajectory, device=torch.device("cpu"))
        pre_equal = {
            "actor_assigned_gradient_bytes_equal": g50._rows_equal(reference_plan.actor_assigned, reduced_plan.assigned),
            "policy_loss_bytes_equal": torch.equal(reference_plan.policy_loss.detach(), reduced_plan.policy_loss.detach()),
            "teacher_logprob_bytes_equal": torch.equal(reference_replay.log_probs, reduced_plan.replay.log_probs),
            "teacher_pre_tanh_bytes_equal": torch.equal(trajectory.pre_tanh_actions, reduced_plan.replay.pre_tanh_actions),
            "teacher_action_bytes_equal": torch.equal(trajectory.actions, reduced_plan.replay.actions),
            "baseline_loss_gradient_into_actor_count": sum(row is not None for row in baseline_into_actor),
            "actor_loss_gradient_into_baseline_count": sum(row is not None for row in actor_into_baseline),
        }
        pre_step_diagnostics = {
            **pre_equal,
            "plan_RNG_unchanged": plan_rng_unchanged,
        }
        semantic_coupling = bool(
            any(
                pre_equal[key] != 0
                for key in _PRE_STEP_CROSS_GRADIENT_COUNT_KEYS
            )
            or not plan_rng_unchanged
        )
        numeric_difference = any(
            pre_equal[key] is not True for key in _PRE_STEP_NUMERIC_EQUALITY_KEYS
        )
        if semantic_coupling or numeric_difference:
            raise G51InvariantError(
                (
                    "phase_A_pre_step_semantic_coupling"
                    if semantic_coupling
                    else "phase_A_pre_step_numeric_difference"
                ),
                {
                    "pass_index": pass_index,
                    "optimizer_ledger": _optimizer_ledger(
                        paired_passes=pass_index,
                        failure_detected_before_current_pair=True,
                    ),
                    "static_certificate": static,
                    "comparison": pre_step_diagnostics,
                },
            )
        reference_actor_steps_before = tuple(
            g50._optimizer_step_value(optimizers[REFERENCE_ARM], parameter)
            for parameter in reference.full_actor_parameters()
        )
        reference_baseline_steps_before = tuple(
            g50._optimizer_step_value(optimizers[REFERENCE_ARM], parameter)
            for parameter in reference.credit_baselines.parameters()
        )
        reduced_actor_steps_before = tuple(
            g50._optimizer_step_value(optimizers[REDUCED_ARM], parameter)
            for parameter in reduced.full_actor_parameters()
        )
        g50._assign_and_step(reference, optimizers[REFERENCE_ARM], reference_plan)
        _apply_reduced_pass(reduced, optimizers[REDUCED_ARM], reduced_plan.assigned)
        reference_actor_steps_after = tuple(
            g50._optimizer_step_value(optimizers[REFERENCE_ARM], parameter)
            for parameter in reference.full_actor_parameters()
        )
        reference_baseline_steps_after = tuple(
            g50._optimizer_step_value(optimizers[REFERENCE_ARM], parameter)
            for parameter in reference.credit_baselines.parameters()
        )
        reduced_actor_steps_after = tuple(
            g50._optimizer_step_value(optimizers[REDUCED_ARM], parameter)
            for parameter in reduced.full_actor_parameters()
        )
        actor_exposure_exact = bool(
            all(after == before + 1.0 for before, after in zip(
                reference_actor_steps_before, reference_actor_steps_after
            ))
            and all(after == before + 1.0 for before, after in zip(
                reduced_actor_steps_before, reduced_actor_steps_after
            ))
        )
        baseline_exposure_exact = bool(
            reference_baseline_steps_before
            and all(after == before + 1.0 for before, after in zip(
                reference_baseline_steps_before, reference_baseline_steps_after
            ))
        )
        actor_equal = _state_equal(_actor_state(reference), _actor_state(reduced))
        adam_equal = _actor_adam_equal(models, optimizers)
        post = {
            "actor_parameter_bytes_equal": actor_equal,
            "log_std_bytes_equal": torch.equal(reference.log_std, reduced.log_std),
            "actor_Adam_step_bytes_equal": adam_equal,
            "actor_Adam_exp_avg_bytes_equal": adam_equal,
            "actor_Adam_exp_avg_sq_bytes_equal": adam_equal,
        }
        if not all(post.values()) or not actor_exposure_exact or not baseline_exposure_exact:
            raise G51InvariantError(
                "phase_A_actual_Adam_kernel_difference",
                {
                    "pass_index": pass_index,
                    "optimizer_ledger": _optimizer_ledger(
                        paired_passes=pass_index + 1,
                        failure_detected_before_current_pair=False,
                    ),
                    "static_certificate": static,
                    "comparison": post,
                },
            )
        pass_records.append({
            "pass_index": pass_index,
            "plans_prepared_before_either_step": True,
            "same_stored_trajectory": True,
            **pre_equal,
            **post,
            "pre_tanh_bytes_equal": pre_equal["teacher_pre_tanh_bytes_equal"],
            "action_bytes_equal": pre_equal["teacher_action_bytes_equal"],
            "logprob_bytes_equal": pre_equal["teacher_logprob_bytes_equal"],
            "baseline_RNG_consumption": int(not plan_rng_unchanged),
            "reference_baseline_parameter_Adam_exposure_count": int(
                baseline_exposure_exact
            ),
            "reduced_baseline_parameter_Adam_exposure_count": sum(
                "baseline" in name.lower()
                for name, _ in reduced.named_parameters()
            ),
            "actor_gradient_digest": g50._gradient_digest(reference_plan.actor_assigned),
            "baseline_gradient_digest": g50._gradient_digest(reference_plan.baseline_assigned),
            "passed": True,
        })
    cross_gradient_evidence = {
        "baseline_loss_gradient_into_actor_count": sum(
            int(row["baseline_loss_gradient_into_actor_count"])
            for row in pass_records
        ),
        "actor_loss_gradient_into_baseline_count": sum(
            int(row["actor_loss_gradient_into_baseline_count"])
            for row in pass_records
        ),
    }
    cross_gradient_evidence["all_zero"] = all(
        value == 0 for value in cross_gradient_evidence.values()
    )
    actual_kernel_equality = {
        "pass_count": len(pass_records),
        "assigned_actor_gradients_equal": all(
            row["actor_assigned_gradient_bytes_equal"] is True
            for row in pass_records
        ),
        "actor_parameters_equal": all(
            row["actor_parameter_bytes_equal"] is True for row in pass_records
        ),
        "log_std_equal": all(
            row["log_std_bytes_equal"] is True for row in pass_records
        ),
        "Adam_step_equal": all(
            row["actor_Adam_step_bytes_equal"] is True for row in pass_records
        ),
        "Adam_exp_avg_equal": all(
            row["actor_Adam_exp_avg_bytes_equal"] is True for row in pass_records
        ),
        "Adam_exp_avg_sq_equal": all(
            row["actor_Adam_exp_avg_sq_bytes_equal"] is True for row in pass_records
        ),
    }
    actual_kernel_equality["all_equal"] = all(
        value is True
        for name, value in actual_kernel_equality.items()
        if name != "pass_count"
    ) and actual_kernel_equality["pass_count"] == PPO_PASSES
    record = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "update_index": int(update_index),
        "static_certificate": static,
        "normalization_instances": 1,
        "normalization_before_both_PPO_passes": True,
        "normalization_recomputed_between_passes": False,
        "normalization_rows": NORMALIZATION_ROWS,
        "source_trace": source_trace,
        "shared_stored_phase_A_batches": 1,
        "episodes": NUM_ENVS,
        "H": HORIZON,
        "real_transitions": MAX_REAL_TRANSITIONS,
        "PPO_passes_per_arm": PPO_PASSES,
        "actor_optimizer_steps_per_arm": PPO_PASSES,
        "reference_baseline_parameter_Adam_exposures": PPO_PASSES,
        "reduced_baseline_parameter_Adam_exposures": 0,
        "total_optimizer_steps": 2 * PPO_PASSES,
        "phase_B_optimizer_steps": 0,
        "pass_records": pass_records,
        "actual_autograd_cross_gradient_evidence": cross_gradient_evidence,
        "actual_kernel_Adam_equality": actual_kernel_equality,
        "torch_RNG_unchanged": torch.equal(rng_before, torch.random.get_rng_state()),
        "K_search": 0,
        "hypothetical_transitions": 0,
        "D_G51": 0,
        "passed": True,
    }
    if not validate_phase_A_update_evidence(record):
        raise G51InvariantError("phase_A_evidence_validation_failed", record)
    return record


def validate_phase_A_update_evidence(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    records = value.get("pass_records")
    cross = value.get("actual_autograd_cross_gradient_evidence")
    kernel = value.get("actual_kernel_Adam_equality")
    return bool(
        value.get("algorithm_id") == ALGORITHM_ID
        and validate_static_certificate(value.get("static_certificate"))
        and value.get("normalization_instances") == 1
        and value.get("normalization_before_both_PPO_passes") is True
        and value.get("normalization_recomputed_between_passes") is False
        and value.get("normalization_rows") == NORMALIZATION_ROWS
        and value.get("shared_stored_phase_A_batches") == 1
        and value.get("episodes") == NUM_ENVS and value.get("H") == HORIZON
        and value.get("real_transitions") == MAX_REAL_TRANSITIONS
        and value.get("PPO_passes_per_arm") == PPO_PASSES
        and value.get("actor_optimizer_steps_per_arm") == PPO_PASSES
        and value.get("reference_baseline_parameter_Adam_exposures") == PPO_PASSES
        and value.get("reduced_baseline_parameter_Adam_exposures") == 0
        and value.get("total_optimizer_steps") == 4
        and value.get("phase_B_optimizer_steps") == 0
        and isinstance(records, list) and len(records) == PPO_PASSES
        and all(
            isinstance(row, Mapping) and row.get("pass_index") == index
            and row.get("plans_prepared_before_either_step") is True
            and row.get("same_stored_trajectory") is True
            and all(row.get(name) is True for name in (
                "actor_assigned_gradient_bytes_equal", "policy_loss_bytes_equal",
                "teacher_logprob_bytes_equal", "teacher_pre_tanh_bytes_equal",
                "teacher_action_bytes_equal", "actor_parameter_bytes_equal",
                "log_std_bytes_equal", "actor_Adam_step_bytes_equal",
                "actor_Adam_exp_avg_bytes_equal", "actor_Adam_exp_avg_sq_bytes_equal",
                "pre_tanh_bytes_equal", "action_bytes_equal", "logprob_bytes_equal",
            ))
            and row.get("baseline_loss_gradient_into_actor_count") == 0
            and row.get("actor_loss_gradient_into_baseline_count") == 0
            and row.get("baseline_RNG_consumption") == 0
            and row.get("reference_baseline_parameter_Adam_exposure_count") == 1
            and row.get("reduced_baseline_parameter_Adam_exposure_count") == 0
            and row.get("passed") is True
            for index, row in enumerate(records)
        )
        and isinstance(cross, Mapping)
        and set(cross) == {
            "baseline_loss_gradient_into_actor_count",
            "actor_loss_gradient_into_baseline_count",
            "all_zero",
        }
        and cross.get("baseline_loss_gradient_into_actor_count")
        == sum(int(row["baseline_loss_gradient_into_actor_count"]) for row in records)
        and cross.get("actor_loss_gradient_into_baseline_count")
        == sum(int(row["actor_loss_gradient_into_baseline_count"]) for row in records)
        and cross.get("all_zero") is True
        and isinstance(kernel, Mapping)
        and set(kernel) == {
            "pass_count", "assigned_actor_gradients_equal",
            "actor_parameters_equal", "log_std_equal", "Adam_step_equal",
            "Adam_exp_avg_equal", "Adam_exp_avg_sq_equal", "all_equal",
        }
        and kernel.get("pass_count") == PPO_PASSES
        and all(kernel.get(name) is True for name in (
            "assigned_actor_gradients_equal", "actor_parameters_equal",
            "log_std_equal", "Adam_step_equal", "Adam_exp_avg_equal",
            "Adam_exp_avg_sq_equal", "all_equal",
        ))
        and value.get("K_search") == 0 and value.get("hypothetical_transitions") == 0
        and value.get("torch_RNG_unchanged") is True and value.get("D_G51") == 0
    )


def project_phase_B_models(
    phase_A_models: Mapping[str, G51Model], *, completed_phase_A_updates: int
) -> tuple[dict[str, g50.G50PhaseBProjection], dict[str, dict[str, object]]]:
    if tuple(phase_A_models) != ARMS:
        raise ValueError("G51 phase boundary requires exact arms")
    rng_before = torch.random.get_rng_state().clone()
    models = {arm: g50.G50PhaseBProjection(phase_A_models[arm]) for arm in ARMS}
    certificates: dict[str, dict[str, object]] = {}
    for arm in ARMS:
        source_state = phase_A_models[arm].state_dict()
        projected_state = models[arm].state_dict()
        retained = {name: value for name, value in source_state.items() if name in projected_state}
        equal = tuple(retained) == tuple(projected_state) and all(
            torch.equal(retained[name], projected_state[name]) for name in retained
        )
        common = {
            "completed_phase_A_updates": int(completed_phase_A_updates),
            "retained_actor_bytes_equal": equal,
            "phase_A_state_deleted": True,
            "fresh_phase_B_state_required": True,
            "projection_optimizer_steps": 0,
            "projection_RNG_consumption": 0,
            "passed": bool(equal),
        }
        if arm == REFERENCE_ARM:
            common["reference_shadow_baseline_deleted"] = not hasattr(models[arm], "credit_baselines")
        certificates[arm] = common
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise G51InvariantError("phase_B_projection_consumed_RNG")
    if not _state_equal(_actor_state(models[REFERENCE_ARM]), _actor_state(models[REDUCED_ARM])):
        raise G51InvariantError("phase_B_projection_actor_difference")
    if g40.shared_tensor_storage_count(tuple(models.values())) != 0:
        raise G51InvariantError("phase_B_storage_alias")
    if not all(row["passed"] is True for row in certificates.values()):
        raise G51InvariantError("phase_B_projection_invalid", certificates)
    return models, certificates


def make_phase_B_optimizers(
    models: Mapping[str, g50.G50PhaseBProjection],
) -> dict[str, torch.optim.Adam]:
    if tuple(models) != ARMS:
        raise ValueError("G51 phase-B optimizer construction requires exact arms")
    optimizers = {arm: g50.g41.make_actor_head_optimizer(models[arm]) for arm in ARMS}
    if any(optimizer.state for optimizer in optimizers.values()):
        raise G51InvariantError("phase_B_Adam_not_fresh")
    return optimizers


def build_phase_B_zero_step_certificate(
    models: Mapping[str, g50.G50PhaseBProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectory: AnchoredRosterTrajectory | g47.G47ActorTrajectory,
) -> dict[str, object]:
    """Certify the common G49 continuation without taking a phase-B step."""

    if tuple(models) != ARMS or tuple(optimizers) != ARMS:
        raise ValueError("G51 phase-B zero-step certificate requires exact arms")
    actor_trajectory = g47._actor_only_trajectory_view(trajectory)
    if actor_trajectory.rewards.numel() != NORMALIZATION_ROWS:
        raise ValueError("G51 phase-B certificate requires one stored 8x48 batch")

    model_before = {arm: g40.state_bytes(models[arm]) for arm in ARMS}
    optimizer_before = {
        arm: _optimizer_state_by_name(optimizers[arm], models[arm]) for arm in ARMS
    }
    gradients_before = {arm: _gradient_slots(models[arm]) for arm in ARMS}
    rng_before = torch.random.get_rng_state().clone()

    # One shared normalization and the exact accepted G49 probe are used for
    # both arms.  _apply_pass is deliberately bound but never invoked here.
    normalization = g49._normalize_single(
        g49._single_immediate_target(actor_trajectory.rewards)
    )
    normalization_record = g49._single_normalization_record(normalization)
    probes = {
        arm: g49._single_probe(
            models[arm], actor_trajectory, normalization.normalized
        )
        for arm in ARMS
    }
    traces = {arm: g47.actor_trace(models[arm], actor_trajectory) for arm in ARMS}

    actor_names = {arm: _actor_names(models[arm]) for arm in ARMS}
    optimizer_names = {
        arm: _parameter_names(models[arm], _optimizer_parameters(optimizers[arm]))
        for arm in ARMS
    }
    hyperparameters = {
        arm: _optimizer_hyperparameters(optimizers[arm]) for arm in ARMS
    }
    optimizer_after = {
        arm: _optimizer_state_by_name(optimizers[arm], models[arm]) for arm in ARMS
    }
    gradients_after = {arm: _gradient_slots(models[arm]) for arm in ARMS}
    actor_equal = _state_equal(
        _actor_state(models[REFERENCE_ARM]), _actor_state(models[REDUCED_ARM])
    )
    state_storage_disjoint = g40.shared_tensor_storage_count(tuple(models.values())) == 0
    optimizer_objects_disjoint = bool(
        optimizers[REFERENCE_ARM] is not optimizers[REDUCED_ARM]
        and optimizers[REFERENCE_ARM].state is not optimizers[REDUCED_ARM].state
    )
    predicates = {
        "same_stored_actor_trajectory": True,
        "g49_single_probe_identity_bound": True,
        "g49_apply_pass_identity_bound": True,
        "single_immediate_normalization_once": True,
        "actor_state_bytes_equal": actor_equal,
        "log_std_bytes_equal": torch.equal(
            models[REFERENCE_ARM].log_std, models[REDUCED_ARM].log_std
        ),
        "actor_parameter_order_equal": actor_names[REFERENCE_ARM]
        == actor_names[REDUCED_ARM],
        "actor_optimizer_parameter_order_equal": bool(
            optimizer_names[REFERENCE_ARM] == actor_names[REFERENCE_ARM]
            and optimizer_names[REDUCED_ARM] == actor_names[REDUCED_ARM]
        ),
        "actor_optimizer_hyperparameters_equal": hyperparameters[REFERENCE_ARM]
        == hyperparameters[REDUCED_ARM],
        "actor_Adam_state_fresh_equal": bool(
            not optimizers[REFERENCE_ARM].state
            and not optimizers[REDUCED_ARM].state
            and _nested_equal(
                optimizer_after[REFERENCE_ARM], optimizer_after[REDUCED_ARM]
            )
        ),
        "actor_Adam_storage_disjoint": bool(
            state_storage_disjoint and optimizer_objects_disjoint
        ),
        "assigned_actor_gradient_bytes_equal": g50._rows_equal(
            probes[REFERENCE_ARM].assigned, probes[REDUCED_ARM].assigned
        ),
        "actor_trace_equal": traces[REFERENCE_ARM] == traces[REDUCED_ARM],
        "RNG_unchanged": torch.equal(rng_before, torch.random.get_rng_state()),
        "model_state_unchanged": all(
            model_before[arm] == g40.state_bytes(models[arm]) for arm in ARMS
        ),
        "optimizer_state_unchanged": all(
            _nested_equal(optimizer_before[arm], optimizer_after[arm]) for arm in ARMS
        ),
        "gradient_slots_unchanged": all(
            _nested_equal(gradients_before[arm], gradients_after[arm]) for arm in ARMS
        ),
        "zero_optimizer_steps": True,
    }
    record = {
        "certificate_kind": "actual_G49_zero_step_route_and_Adam_factorization",
        "algorithm_id": ALGORITHM_ID,
        "phase_B_route": "G49_SINGLE_IMMEDIATE",
        "single_probe_identity": _callable_identity(g49._single_probe),
        "apply_pass_identity": _callable_identity(g49._apply_pass),
        "normalization_record": normalization_record,
        "target_digest": _tensor_digest(normalization.target),
        "normalized_digest": _tensor_digest(normalization.normalized),
        "actor_parameter_names": {
            arm: list(actor_names[arm]) for arm in ARMS
        },
        "optimizer_parameter_names": {
            arm: list(optimizer_names[arm]) for arm in ARMS
        },
        "optimizer_hyperparameters": hyperparameters,
        "assigned_gradient_digest": {
            arm: g50._gradient_digest(probes[arm].assigned) for arm in ARMS
        },
        "actor_trace": traces,
        "predicates": predicates,
        "episodes": NUM_ENVS,
        "H": HORIZON,
        "real_transitions": NORMALIZATION_ROWS,
        "phase_B_optimizer_steps": 0,
        "K_search": 0,
        "passed": all(predicates.values()),
    }
    if not validate_phase_B_zero_step_certificate(record):
        raise G51InvariantError("phase_B_zero_step_certificate_invalid", record)
    return record


def validate_phase_B_zero_step_certificate(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != _PHASE_B_ZERO_STEP_KEYS:
        return False
    predicates = value.get("predicates")
    actor_names = value.get("actor_parameter_names")
    optimizer_names = value.get("optimizer_parameter_names")
    hyperparameters = value.get("optimizer_hyperparameters")
    gradient_digests = value.get("assigned_gradient_digest")
    traces = value.get("actor_trace")
    normalization = value.get("normalization_record")
    expected_hyperparameters = {
        "valid": True,
        "lr": g40.LEARNING_RATE,
        "betas": (0.9, 0.999),
        "eps": 1e-8,
        "weight_decay": 0.0,
        "amsgrad": False,
        "maximize": False,
        "foreach": None,
        "capturable": False,
        "differentiable": False,
        "fused": None,
    }
    return bool(
        value.get("certificate_kind")
        == "actual_G49_zero_step_route_and_Adam_factorization"
        and value.get("algorithm_id") == ALGORITHM_ID
        and value.get("phase_B_route") == "G49_SINGLE_IMMEDIATE"
        and value.get("single_probe_identity")
        == _callable_identity(g49._single_probe)
        and value.get("apply_pass_identity") == _callable_identity(g49._apply_pass)
        and g49.validate_single_normalization_record(normalization)
        and isinstance(normalization, Mapping)
        and value.get("target_digest") == normalization.get("target_digest")
        and value.get("normalized_digest") == normalization.get("normalized_digest")
        and isinstance(actor_names, Mapping) and tuple(actor_names) == ARMS
        and isinstance(optimizer_names, Mapping) and tuple(optimizer_names) == ARMS
        and actor_names[REFERENCE_ARM] == actor_names[REDUCED_ARM]
        and optimizer_names[REFERENCE_ARM] == actor_names[REFERENCE_ARM]
        and optimizer_names[REDUCED_ARM] == actor_names[REDUCED_ARM]
        and isinstance(hyperparameters, Mapping) and tuple(hyperparameters) == ARMS
        and hyperparameters[REFERENCE_ARM] == expected_hyperparameters
        and hyperparameters[REDUCED_ARM] == expected_hyperparameters
        and isinstance(gradient_digests, Mapping) and tuple(gradient_digests) == ARMS
        and gradient_digests[REFERENCE_ARM] == gradient_digests[REDUCED_ARM]
        and all(
            isinstance(gradient_digests[arm], str)
            and len(gradient_digests[arm]) == 64
            for arm in ARMS
        )
        and isinstance(traces, Mapping) and tuple(traces) == ARMS
        and traces[REFERENCE_ARM] == traces[REDUCED_ARM]
        and isinstance(predicates, Mapping)
        and tuple(predicates) == _PHASE_B_ZERO_STEP_PREDICATE_KEYS
        and all(predicates[name] is True for name in _PHASE_B_ZERO_STEP_PREDICATE_KEYS)
        and value.get("episodes") == NUM_ENVS and value.get("H") == HORIZON
        and value.get("real_transitions") == NORMALIZATION_ROWS
        and value.get("phase_B_optimizer_steps") == 0
        and value.get("K_search") == 0 and value.get("passed") is True
    )


def optimize_phase_B_update(
    models: Mapping[str, g50.G50PhaseBProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, g47.G47ActorTrajectory] | g47.G47ActorTrajectory,
    *, update_index: int = 0,
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS:
        raise ValueError("G51 phase-B update requires exact arms")
    rows = trajectories if isinstance(trajectories, Mapping) else {arm: trajectories for arm in ARMS}
    if tuple(rows) != ARMS:
        raise ValueError("G51 phase-B trajectory inventory invalid")
    if not torch.equal(rows[REFERENCE_ARM].rewards, rows[REDUCED_ARM].rewards):
        raise G51InvariantError("phase_B_source_pairing_invalid")
    normalized = g49._normalize_single(g49._single_immediate_target(rows[REFERENCE_ARM].rewards))
    records: list[dict[str, object]] = []
    for pass_index in range(PPO_PASSES):
        probes = {arm: g49._single_probe(models[arm], rows[arm], normalized.normalized) for arm in ARMS}
        gradients_equal = g50._rows_equal(probes[REFERENCE_ARM].assigned, probes[REDUCED_ARM].assigned)
        if not gradients_equal:
            raise G51InvariantError("phase_B_common_G49_gradient_difference")
        for arm in ARMS:
            g49._apply_pass(models[arm], optimizers[arm], probes[arm].assigned)
        actor_equal = _state_equal(_actor_state(models[REFERENCE_ARM]), _actor_state(models[REDUCED_ARM]))
        adam_equal = _nested_equal(
            _optimizer_state_by_name(optimizers[REFERENCE_ARM], models[REFERENCE_ARM]),
            _optimizer_state_by_name(optimizers[REDUCED_ARM], models[REDUCED_ARM]),
        )
        records.append({
            "pass_index": pass_index,
            "common_G49_single_immediate_route": True,
            "actor_gradient_bytes_equal": gradients_equal,
            "actor_parameter_bytes_equal": actor_equal,
            "actor_Adam_bytes_equal": adam_equal,
            "passed": bool(gradients_equal and actor_equal and adam_equal),
        })
    record = {
        "algorithm_id": ALGORITHM_ID,
        "update_index": int(update_index),
        "phase_B_route": "G49_SINGLE_IMMEDIATE",
        "normalization_instances": 1,
        "PPO_passes_per_arm": PPO_PASSES,
        "optimizer_steps_per_arm": PPO_PASSES,
        "pass_records": records,
        "D_G51_phase_B": 0 if all(row["passed"] for row in records) else 1,
        "passed": all(row["passed"] for row in records),
    }
    if not validate_phase_B_update_evidence(record):
        raise G51InvariantError("phase_B_evidence_validation_failed", record)
    return record


def validate_phase_B_update_evidence(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    records = value.get("pass_records")
    return bool(
        value.get("algorithm_id") == ALGORITHM_ID
        and value.get("phase_B_route") == "G49_SINGLE_IMMEDIATE"
        and value.get("normalization_instances") == 1
        and value.get("PPO_passes_per_arm") == PPO_PASSES
        and value.get("optimizer_steps_per_arm") == PPO_PASSES
        and isinstance(records, list) and len(records) == PPO_PASSES
        and all(isinstance(row, Mapping) and row.get("passed") is True for row in records)
        and value.get("D_G51_phase_B") == 0 and value.get("passed") is True
    )


def _contains_reduced_residue(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            any(token in str(key).lower() for token in _BASELINE_RESIDUE_TOKENS)
            or _contains_reduced_residue(row)
            for key, row in value.items()
        )
    if isinstance(value, (list, tuple, set)):
        return any(_contains_reduced_residue(row) for row in value)
    return isinstance(value, str) and any(token in value.lower() for token in _BASELINE_RESIDUE_TOKENS)


def _checkpoint_actor_state(model: nn.Module) -> tuple[dict[str, torch.Tensor], torch.Tensor]:
    state = _actor_state(model)
    log_std = state.pop("policy.log_std")
    return state, log_std


def build_final_checkpoints(
    models: Mapping[str, g50.G50PhaseBProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    *,
    source_commit: str,
    completed_phase_A_updates: int,
    completed_phase_B_updates: int,
    phase_boundary_evidence: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS or tuple(phase_boundary_evidence) != ARMS:
        raise ValueError("G51 final checkpoint requires exact ordered arms")
    if len(source_commit) != 40:
        raise ValueError("G51 source commit must be a full 40-character identity")
    if _contains_reduced_residue(phase_boundary_evidence[REDUCED_ARM]):
        raise G51InvariantError("reduced_phase_boundary_evidence_contains_residue")
    checkpoints: dict[str, dict[str, object]] = {}
    for arm in ARMS:
        actor_state, log_std = _checkpoint_actor_state(models[arm])
        payload: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "kind": "final_only",
            "final_only_checkpoint_identity": "G51_CANONICAL_FINAL_ACTOR_CHECKPOINT_V1",
            "actor_state": actor_state,
            "log_std": log_std,
            "actor_Adam_state": _optimizer_state_by_name(optimizers[arm], models[arm]),
            "completed_phase_A_updates": int(completed_phase_A_updates),
            "completed_phase_B_updates": int(completed_phase_B_updates),
            "source": {
                "implementation_commit": source_commit,
                "design_stage_commit": DESIGN_STAGE_COMMIT,
                "predecessor_source_commit": PREDECESSOR_SOURCE_COMMIT,
                "accepted_G50_formal_source_commit": ACCEPTED_G50_FORMAL_SOURCE_COMMIT,
                "accepted_G50_execution_code_commit": ACCEPTED_G50_EXECUTION_CODE_COMMIT,
                "accepted_G50_alignment_stage_commit": ACCEPTED_G50_ALIGNMENT_STAGE_COMMIT,
                "accepted_G50_formal_branch": ACCEPTED_G50_FORMAL_BRANCH,
            },
        }
        if arm == REFERENCE_ARM:
            payload.update(
                {
                    "algorithm_id": ALGORITHM_ID,
                    "source_id": SOURCE_ID,
                    "arm": REFERENCE_ARM,
                }
            )
            payload["phase_A_reference_evidence"] = copy.deepcopy(phase_boundary_evidence[arm])
        else:
            payload["phase_A_projection_evidence"] = copy.deepcopy(phase_boundary_evidence[arm])
        checkpoints[arm] = payload
    if not validate_checkpoint_pair(checkpoints):
        raise G51InvariantError("final_checkpoint_pair_invalid")
    return checkpoints


def canonical_actor_projection(checkpoint: Mapping[str, object]) -> dict[str, object]:
    required = (
        "actor_state", "log_std", "actor_Adam_state", "completed_phase_A_updates",
        "completed_phase_B_updates", "source", "final_only_checkpoint_identity",
    )
    if any(name not in checkpoint for name in required):
        raise ValueError("G51 canonical checkpoint fields missing")
    return {name: checkpoint[name] for name in required}


def validate_checkpoint_pair(value: object) -> bool:
    if not isinstance(value, Mapping) or tuple(value) != ARMS:
        return False
    reference, reduced = value.get(REFERENCE_ARM), value.get(REDUCED_ARM)
    if not isinstance(reference, Mapping) or not isinstance(reduced, Mapping):
        return False
    common_payload_keys = {
        "schema_version", "kind", "final_only_checkpoint_identity", "actor_state", "log_std",
        "actor_Adam_state", "completed_phase_A_updates", "completed_phase_B_updates",
        "source",
    }
    if set(reference) != common_payload_keys | {
        "algorithm_id", "source_id", "arm", "phase_A_reference_evidence"
    }:
        return False
    if set(reduced) != common_payload_keys | {"phase_A_projection_evidence"}:
        return False
    if _contains_reduced_residue(reduced):
        return False
    reference_boundary = reference.get("phase_A_reference_evidence")
    reduced_boundary = reduced.get("phase_A_projection_evidence")
    if (
        not isinstance(reference_boundary, Mapping)
        or not isinstance(reduced_boundary, Mapping)
        or set(reference_boundary)
        != _PHASE_BOUNDARY_COMMON_KEYS | {"reference_shadow_baseline_deleted"}
        or set(reduced_boundary) != _PHASE_BOUNDARY_COMMON_KEYS
    ):
        return False
    for arm, row in ((REFERENCE_ARM, reference), (REDUCED_ARM, reduced)):
        source = row.get("source")
        boundary = (
            row.get("phase_A_reference_evidence")
            if arm == REFERENCE_ARM
            else row.get("phase_A_projection_evidence")
        )
        if (
            row.get("schema_version") != SCHEMA_VERSION or row.get("kind") != "final_only"
            or row.get("final_only_checkpoint_identity") != "G51_CANONICAL_FINAL_ACTOR_CHECKPOINT_V1"
            or not isinstance(row.get("actor_state"), Mapping)
            or not isinstance(row.get("log_std"), torch.Tensor)
            or not isinstance(row.get("actor_Adam_state"), Mapping)
            or not isinstance(source, Mapping)
            or set(source) != _SOURCE_PROVENANCE_KEYS
            or not isinstance(source.get("implementation_commit"), str)
            or len(source["implementation_commit"]) != 40
            or source.get("design_stage_commit") != DESIGN_STAGE_COMMIT
            or source.get("predecessor_source_commit") != PREDECESSOR_SOURCE_COMMIT
            or source.get("accepted_G50_formal_source_commit")
            != ACCEPTED_G50_FORMAL_SOURCE_COMMIT
            or source.get("accepted_G50_execution_code_commit")
            != ACCEPTED_G50_EXECUTION_CODE_COMMIT
            or source.get("accepted_G50_alignment_stage_commit")
            != ACCEPTED_G50_ALIGNMENT_STAGE_COMMIT
            or source.get("accepted_G50_formal_branch") != ACCEPTED_G50_FORMAL_BRANCH
            or not isinstance(boundary, Mapping)
            or boundary.get("completed_phase_A_updates")
            != row.get("completed_phase_A_updates")
            or boundary.get("retained_actor_bytes_equal") is not True
            or boundary.get("phase_A_state_deleted") is not True
            or boundary.get("fresh_phase_B_state_required") is not True
            or boundary.get("projection_optimizer_steps") != 0
            or boundary.get("projection_RNG_consumption") != 0
            or boundary.get("passed") is not True
        ):
            return False
        if arm == REFERENCE_ARM and (
            row.get("algorithm_id") != ALGORITHM_ID
            or row.get("source_id") != SOURCE_ID
            or row.get("arm") != REFERENCE_ARM
        ):
            return False
    if reference_boundary.get("reference_shadow_baseline_deleted") is not True:
        return False
    try:
        return _nested_equal(canonical_actor_projection(reference), canonical_actor_projection(reduced))
    except (TypeError, ValueError):
        return False


def build_inductive_equality_certificate(
    *,
    phase_A_evidence: Mapping[str, object] | None,
    phase_boundary_evidence: Mapping[str, Mapping[str, object]],
    checkpoints: Mapping[str, Mapping[str, object]],
    phase_B_evidence: Mapping[str, object] | None = None,
) -> dict[str, object]:
    # This implementation leaves PyTorch's accepted Adam foreach/fused kernel
    # selection untouched.  Static factorization alone therefore cannot close
    # the parameter-list numerical risk; the permitted actual-kernel phase-A
    # witness is mandatory for exact classification.
    phase_A_equal = phase_A_evidence is not None and validate_phase_A_update_evidence(
        phase_A_evidence
    )
    cross_gradient_closed = bool(
        phase_A_equal
        and isinstance(phase_A_evidence, Mapping)
        and isinstance(
            phase_A_evidence.get("actual_autograd_cross_gradient_evidence"),
            Mapping,
        )
        and phase_A_evidence["actual_autograd_cross_gradient_evidence"].get(
            "all_zero"
        )
        is True
    )
    actual_kernel_closed = bool(
        phase_A_equal
        and isinstance(phase_A_evidence, Mapping)
        and isinstance(phase_A_evidence.get("actual_kernel_Adam_equality"), Mapping)
        and phase_A_evidence["actual_kernel_Adam_equality"].get("all_equal")
        is True
    )
    boundary_equal = bool(
        tuple(phase_boundary_evidence) == ARMS
        and all(row.get("passed") is True for row in phase_boundary_evidence.values())
    )
    fresh_phase_B = all(
        row.get("fresh_phase_B_state_required") is True for row in phase_boundary_evidence.values()
    )
    phase_B_equal = validate_phase_B_zero_step_certificate(phase_B_evidence)
    checkpoint_equal = validate_checkpoint_pair(checkpoints)
    fields = {
        "actor_gradient": 0 if phase_A_equal and cross_gradient_closed else 1,
        "actor_log_std": 0 if phase_A_equal else 1,
        "actor_Adam": 0 if phase_A_equal and actual_kernel_closed else 1,
        "pre_tanh_action_logprob": 0 if phase_A_equal else 1,
        "reward_roster_lifecycle": 0 if phase_A_equal else 1,
        "phase_boundary_projection": 0 if boundary_equal else 1,
        "phase_B_actor_Adam": 0 if fresh_phase_B and phase_B_equal else 1,
        "canonical_final_checkpoint": 0 if checkpoint_equal else 1,
    }
    return {
        "certificate_kind": "G51_exact_inductive_actor_and_per_parameter_Adam_equality",
        "base_actor_and_Adam_equal": phase_A_equal,
        "assigned_actor_gradients_equal": phase_A_equal,
        "actual_autograd_cross_gradient_zero": cross_gradient_closed,
        "actual_kernel_Adam_equality": actual_kernel_closed,
        "per_parameter_Adam_preserves_equality": actual_kernel_closed,
        "paired_source_and_action_noise_preserve_trajectory": phase_A_equal,
        "phase_A_induction_valid_for_every_update": phase_A_equal,
        "phase_boundary_actor_equal_and_state_deleted": boundary_equal,
        "fresh_phase_B_Adam_equal": fresh_phase_B,
        "common_G49_phase_B_induction_valid": phase_B_equal,
        "registered_difference_vector": fields,
        "D_G51": max(fields.values()),
        "passed": all(value == 0 for value in fields.values()),
    }


def validate_inductive_equality_certificate(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    fields = value.get("registered_difference_vector")
    expected = (
        "actor_gradient", "actor_log_std", "actor_Adam",
        "pre_tanh_action_logprob", "reward_roster_lifecycle",
        "phase_boundary_projection", "phase_B_actor_Adam",
        "canonical_final_checkpoint",
    )
    return bool(
        value.get("certificate_kind") == "G51_exact_inductive_actor_and_per_parameter_Adam_equality"
        and all(value.get(name) is True for name in (
            "base_actor_and_Adam_equal", "assigned_actor_gradients_equal",
            "actual_autograd_cross_gradient_zero", "actual_kernel_Adam_equality",
            "per_parameter_Adam_preserves_equality",
            "paired_source_and_action_noise_preserve_trajectory",
            "phase_A_induction_valid_for_every_update",
            "phase_boundary_actor_equal_and_state_deleted", "fresh_phase_B_Adam_equal",
            "common_G49_phase_B_induction_valid",
        ))
        and isinstance(fields, Mapping) and tuple(fields) == expected
        and all(fields[name] == 0 for name in expected)
        and value.get("D_G51") == 0 and value.get("passed") is True
    )


def build_structural_witness(
    trajectory: AnchoredRosterTrajectory,
    *,
    member_capacity: int = 8,
    initialization_seed: int = 10_501_000,
    source_commit: str = ACCEPTED_G50_EXECUTION_CODE_COMMIT,
    completed_phase_A_updates: int = 1,
    completed_phase_B_updates: int = 0,
) -> dict[str, object]:
    if not isinstance(trajectory, AnchoredRosterTrajectory):
        raise ValueError("G51 exact structural witness requires one actual 8x48 trajectory")
    models = make_phase_A_models(member_capacity=member_capacity, initialization_seed=initialization_seed)
    phase_A_optimizers = make_phase_A_optimizers(models)
    static = reconstruct_static_certificate(models, phase_A_optimizers)
    phase_A = optimize_phase_A_update(models, phase_A_optimizers, trajectory)
    projected, boundary = project_phase_B_models(
        models, completed_phase_A_updates=completed_phase_A_updates
    )
    phase_B_optimizers = make_phase_B_optimizers(projected)
    phase_B_zero_step = build_phase_B_zero_step_certificate(
        projected, phase_B_optimizers, trajectory
    )
    checkpoints = build_final_checkpoints(
        projected, phase_B_optimizers, source_commit=source_commit,
        completed_phase_A_updates=completed_phase_A_updates,
        completed_phase_B_updates=completed_phase_B_updates,
        phase_boundary_evidence=boundary,
    )
    inductive = build_inductive_equality_certificate(
        phase_A_evidence=phase_A,
        phase_boundary_evidence=boundary,
        checkpoints=checkpoints,
        phase_B_evidence=phase_B_zero_step,
    )
    bundle = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "static_certificate": static,
        "phase_A_update_evidence": phase_A,
        "phase_boundary_evidence": boundary,
        "phase_B_zero_step_certificate": phase_B_zero_step,
        "phase_B_optimizer_steps": 0,
        "checkpoints": checkpoints,
        "inductive_equality_certificate": inductive,
        "result": EXACT_RESULT if validate_static_certificate(static) and validate_inductive_equality_certificate(inductive) else INVALID_RESULT,
        "passed": validate_static_certificate(static) and validate_inductive_equality_certificate(inductive),
    }
    if not validate_structural_witness(bundle):
        raise G51InvariantError("structural_witness_validation_failed")
    return bundle


def validate_structural_witness(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    phase_A = value.get("phase_A_update_evidence")
    return bool(
        value.get("algorithm_id") == ALGORITHM_ID
        and validate_static_certificate(value.get("static_certificate"))
        and validate_phase_A_update_evidence(phase_A)
        and value.get("phase_B_optimizer_steps") == 0
        and validate_checkpoint_pair(value.get("checkpoints"))
        and validate_phase_B_zero_step_certificate(
            value.get("phase_B_zero_step_certificate")
        )
        and validate_inductive_equality_certificate(value.get("inductive_equality_certificate"))
        and value.get("result") == EXACT_RESULT and value.get("passed") is True
    )


def _static_certificate_schema_valid(value: object) -> bool:
    return bool(
        isinstance(value, Mapping)
        and set(value)
        == {
            "certificate_kind",
            "boundary",
            "reference_module_parameter_graph",
            "reduced_module_parameter_graph",
            "reference_baseline_forward_audit",
            "path_identities",
            "component_bytecode_reads",
            "forbidden_reduced_dependency_reads",
            "static_predicates",
            "optimizer_predicates",
            "reduced_module_parameter_state_and_callable_absent",
            "witness_closure_requirements",
            "K_search",
            "hypothetical_transitions",
            "formal_statistical_run",
            "passed",
        }
        and value.get("certificate_kind")
        == "actual_zero_trajectory_dependency_graph_with_witness_required_Adam_closure"
        and isinstance(value.get("boundary"), Mapping)
        and isinstance(value.get("static_predicates"), Mapping)
        and isinstance(value.get("optimizer_predicates"), Mapping)
        and isinstance(value.get("forbidden_reduced_dependency_reads"), Mapping)
    )


def _static_coupling_detected(value: Mapping[str, object]) -> bool:
    static = value.get("static_predicates")
    optimizer = value.get("optimizer_predicates")
    forbidden = value.get("forbidden_reduced_dependency_reads")
    if not isinstance(static, Mapping) or not isinstance(optimizer, Mapping):
        return False
    optimizer_coupling_counts = (
        "global_gradient_clipping_call_count",
        "joint_gradient_normalization_call_count",
        "loss_count_scaling_call_count",
        "optimizer_group_size_scaling_call_count",
        "non_parameter_optimizer_state_count",
        "scheduler_attachment_count",
        "cross_parameter_moment_reduction_call_count",
    )
    required_optimizer_relations = (
        "actual_optimizer_is_Adam",
        "actor_parameter_order_equal",
        "reference_actor_prefix_baseline_suffix",
        "reduced_actor_only_order",
        "actor_hyperparameters_equal",
    )
    return bool(
        any(isinstance(row, int) and row > 0 for row in static.values())
        or any(
            isinstance(optimizer.get(name), int) and optimizer.get(name) > 0
            for name in optimizer_coupling_counts
        )
        or any(optimizer.get(name) is not True for name in required_optimizer_relations)
        or (
            isinstance(forbidden, Mapping)
            and any(isinstance(row, list) and row for row in forbidden.values())
        )
    )


def _pre_step_comparison(
    diagnostics: object,
) -> tuple[Mapping[str, object] | None, Mapping[str, object] | None]:
    if not isinstance(diagnostics, Mapping):
        return None, None
    static = diagnostics.get("static_certificate")
    comparison = diagnostics.get("comparison")
    return (
        static if isinstance(static, Mapping) else None,
        comparison if isinstance(comparison, Mapping) else None,
    )


def _pre_step_semantic_predicates_complete(diagnostics: object) -> bool:
    static, comparison = _pre_step_comparison(diagnostics)
    return bool(
        static is not None
        and comparison is not None
        and validate_static_certificate(static)
        and set(comparison) == _PRE_STEP_COMPARISON_KEYS
        and all(
            isinstance(comparison.get(name), bool)
            for name in _PRE_STEP_NUMERIC_EQUALITY_KEYS
        )
        and all(
            isinstance(comparison.get(name), int)
            and not isinstance(comparison.get(name), bool)
            and int(comparison[name]) >= 0
            for name in _PRE_STEP_CROSS_GRADIENT_COUNT_KEYS
        )
        and isinstance(comparison.get("plan_RNG_unchanged"), bool)
    )


def _pre_step_semantic_coupling_detected(diagnostics: object) -> bool:
    static, comparison = _pre_step_comparison(diagnostics)
    if (
        static is None
        or comparison is None
        or not _pre_step_semantic_predicates_complete(diagnostics)
    ):
        return False
    return bool(
        _static_coupling_detected(static)
        or any(
            int(comparison[name]) > 0
            for name in _PRE_STEP_CROSS_GRADIENT_COUNT_KEYS
        )
        or comparison.get("plan_RNG_unchanged") is False
    )


def _pre_step_numeric_difference_detected(diagnostics: object) -> bool:
    static, comparison = _pre_step_comparison(diagnostics)
    if (
        static is None
        or comparison is None
        or not validate_static_certificate(static)
        or not _pre_step_semantic_predicates_complete(diagnostics)
        or _pre_step_semantic_coupling_detected(diagnostics)
        or any(name not in comparison for name in _PRE_STEP_NUMERIC_EQUALITY_KEYS)
    ):
        return False
    return any(
        comparison.get(name) is not True
        for name in _PRE_STEP_NUMERIC_EQUALITY_KEYS
    )


def _failure_route_consistent(
    failure: object,
    evidence: Mapping[str, object],
    result: object,
) -> bool:
    if failure is None:
        return True
    if not isinstance(failure, Mapping) or set(failure) != {
        "passed",
        "reason",
        "diagnostics",
    } or failure.get("passed") is not False:
        return False
    reason = failure.get("reason")
    diagnostics = failure.get("diagnostics")
    if reason == "phase_A_pre_step_semantic_coupling":
        return bool(
            result == COUPLING_RESULT
            and evidence.get("semantic_coupling_detected") is True
            and _pre_step_semantic_coupling_detected(diagnostics)
        )
    if reason == "phase_A_pre_step_numeric_difference":
        return bool(
            result == NUMERICALLY_UNRESOLVED_RESULT
            and evidence.get("semantic_coupling_detected") is not True
            and _pre_step_numeric_difference_detected(diagnostics)
        )
    if reason == "phase_A_actual_Adam_kernel_difference":
        return bool(
            result == NUMERICALLY_UNRESOLVED_RESULT
            and evidence.get("semantic_coupling_detected") is not True
        )
    if reason == "static_certificate_failed_before_optimizer":
        return result == INVALID_RESULT
    return bool(
        result == INVALID_RESULT and evidence.get("evidence_valid") is False
    )


def classify_result(evidence: Mapping[str, object]) -> str:
    if evidence.get("provenance_valid", True) is not True or evidence.get("evidence_valid", True) is not True:
        return INVALID_RESULT
    static = evidence.get("static_certificate", evidence)
    if not _static_certificate_schema_valid(static):
        return INVALID_RESULT
    assert isinstance(static, Mapping)
    if _static_coupling_detected(static) or evidence.get("semantic_coupling_detected") is True:
        return COUPLING_RESULT
    inductive = evidence.get("inductive_equality_certificate")
    exact = validate_static_certificate(static) and validate_inductive_equality_certificate(
        inductive
    )
    if exact:
        return EXACT_RESULT
    if validate_static_certificate(static):
        return NUMERICALLY_UNRESOLVED_RESULT
    return INVALID_RESULT


def build_result_evidence_envelope(
    evidence: Mapping[str, object],
    *,
    failure: G51InvariantError | None = None,
) -> dict[str, object]:
    """Preserve bounded invalid/coupling/numerical evidence without success."""

    routed = dict(evidence)
    failure_record: dict[str, object] | None = None
    if failure is not None:
        failure_record = failure.to_record()
        if (
            failure.reason == "phase_A_pre_step_semantic_coupling"
            and _pre_step_semantic_coupling_detected(failure.diagnostics)
        ):
            routed["semantic_coupling_detected"] = True
        elif (
            failure.reason == "phase_A_pre_step_numeric_difference"
            and _pre_step_numeric_difference_detected(failure.diagnostics)
        ) or failure.reason == "phase_A_actual_Adam_kernel_difference":
            routed["numerical_kernel_unresolved"] = True
        else:
            routed["evidence_valid"] = False
    result = classify_result(routed)
    inductive = routed.get("inductive_equality_certificate")
    difference = (
        inductive.get("D_G51")
        if isinstance(inductive, Mapping)
        else None
    )
    envelope = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "schema_version": SCHEMA_VERSION,
        "result": result,
        "result_order": list(RESULT_BRANCHES),
        "failure_evidence": failure_record,
        "D_G51": difference,
        "evidence": routed,
        "valid_evidence": result != INVALID_RESULT,
        "successful_exact_result": result == EXACT_RESULT,
    }
    if not validate_result_evidence_envelope(envelope):
        raise G51InvariantError("result_evidence_envelope_invalid")
    return envelope


def validate_result_evidence_envelope(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != {
        "algorithm_id", "source_id", "schema_version", "result",
        "result_order", "failure_evidence", "D_G51", "evidence",
        "valid_evidence", "successful_exact_result",
    }:
        return False
    evidence = value.get("evidence")
    failure = value.get("failure_evidence")
    result = value.get("result")
    return bool(
        value.get("algorithm_id") == ALGORITHM_ID
        and value.get("source_id") == SOURCE_ID
        and value.get("schema_version") == SCHEMA_VERSION
        and value.get("result_order") == list(RESULT_BRANCHES)
        and isinstance(evidence, Mapping)
        and result == classify_result(evidence)
        and result in RESULT_BRANCHES
        and _failure_route_consistent(failure, evidence, result)
        and value.get("valid_evidence") is (result != INVALID_RESULT)
        and value.get("successful_exact_result") is (result == EXACT_RESULT)
        and (result != EXACT_RESULT or value.get("D_G51") == 0)
    )


def _assessment_provenance(source_commit: str) -> dict[str, object]:
    return {
        "implementation_source_commit": str(source_commit),
        "design_stage_commit": DESIGN_STAGE_COMMIT,
        "predecessor_source_commit": PREDECESSOR_SOURCE_COMMIT,
        "accepted_G50_formal_source_commit": ACCEPTED_G50_FORMAL_SOURCE_COMMIT,
        "accepted_G50_execution_code_commit": ACCEPTED_G50_EXECUTION_CODE_COMMIT,
        "accepted_G50_alignment_stage_commit": ACCEPTED_G50_ALIGNMENT_STAGE_COMMIT,
        "accepted_G50_formal_branch": ACCEPTED_G50_FORMAL_BRANCH,
        "design_disposition": DESIGN_DISPOSITION,
        "arms": list(ARMS),
    }


def assess_structural_witness(
    trajectory: AnchoredRosterTrajectory,
    *,
    member_capacity: int = 8,
    initialization_seed: int = 10_501_000,
    source_commit: str = ACCEPTED_G50_EXECUTION_CODE_COMMIT,
    completed_phase_A_updates: int = 1,
    completed_phase_B_updates: int = 0,
) -> dict[str, object]:
    """Run one strict witness or preserve an allow-listed adverse outcome."""

    bundle: Mapping[str, object] | None = None
    failure: G51InvariantError | None = None
    try:
        bundle = build_structural_witness(
            trajectory,
            member_capacity=member_capacity,
            initialization_seed=initialization_seed,
            source_commit=source_commit,
            completed_phase_A_updates=completed_phase_A_updates,
            completed_phase_B_updates=completed_phase_B_updates,
        )
        phase_A = bundle["phase_A_update_evidence"]
        if not isinstance(phase_A, Mapping):
            raise G51InvariantError("assessment_positive_phase_A_evidence_missing")
        ledger = _optimizer_ledger(
            paired_passes=int(phase_A["actor_optimizer_steps_per_arm"]),
            failure_detected_before_current_pair=False,
        )
        evidence = {
            **dict(bundle),
            "provenance_valid": True,
            "evidence_valid": True,
            "numerical_witness_invoked": True,
            "numerical_witness_all_zero": True,
            "optimizer_ledger": ledger,
        }
    except G51InvariantError as error:
        if error.reason not in ASSESSMENT_ALLOWED_FAILURE_REASONS:
            raise
        failure = error
        if error.reason == "static_certificate_failed_before_optimizer":
            static = error.diagnostics
            ledger = _optimizer_ledger(
                paired_passes=0,
                failure_detected_before_current_pair=True,
            )
            evidence_valid = False
        else:
            static = error.diagnostics.get("static_certificate")
            ledger = error.diagnostics.get("optimizer_ledger")
            evidence_valid = True
        if not validate_optimizer_ledger(ledger):
            raise
        assert isinstance(ledger, Mapping)
        pass_index = error.diagnostics.get("pass_index")
        if error.reason in _PRE_STEP_FAILURE_REASONS:
            ledger_consistent = bool(
                isinstance(pass_index, int)
                and ledger["completed_paired_passes"] == pass_index
                and ledger["failure_detected_before_current_pair"] is True
            )
        elif error.reason == "phase_A_actual_Adam_kernel_difference":
            ledger_consistent = bool(
                isinstance(pass_index, int)
                and ledger["completed_paired_passes"] == pass_index + 1
                and ledger["failure_detected_before_current_pair"] is False
            )
        else:
            ledger_consistent = bool(
                ledger["completed_paired_passes"] == 0
                and ledger["failure_detected_before_current_pair"] is True
            )
        if not ledger_consistent:
            raise
        evidence = {
            "static_certificate": static,
            "phase_A_update_evidence": None,
            "phase_boundary_evidence": None,
            "phase_B_zero_step_certificate": None,
            "inductive_equality_certificate": None,
            "checkpoints": None,
            "provenance_valid": True,
            "evidence_valid": evidence_valid,
            "numerical_witness_invoked": error.reason
            != "static_certificate_failed_before_optimizer",
            "numerical_witness_all_zero": False,
            "optimizer_ledger": ledger,
        }
    result_envelope = build_result_evidence_envelope(evidence, failure=failure)
    assessment = {
        "assessment_kind": "G51_STRICT_WITNESS_WITH_ADVERSE_EVIDENCE_V1",
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "schema_version": SCHEMA_VERSION,
        "provenance": _assessment_provenance(source_commit),
        "optimizer_ledger": ledger,
        "static_certificate": evidence.get("static_certificate"),
        "phase_A_update_evidence": evidence.get("phase_A_update_evidence"),
        "phase_boundary_evidence": evidence.get("phase_boundary_evidence"),
        "phase_B_zero_step_certificate": evidence.get(
            "phase_B_zero_step_certificate"
        ),
        "inductive_equality_certificate": evidence.get(
            "inductive_equality_certificate"
        ),
        "checkpoints": evidence.get("checkpoints"),
        "result_envelope": result_envelope,
        "passed": result_envelope["result"] == EXACT_RESULT,
    }
    if not validate_structural_assessment(assessment):
        raise G51InvariantError("structural_assessment_validation_failed")
    return assessment


def validate_structural_assessment(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != {
        "assessment_kind", "algorithm_id", "source_id", "schema_version",
        "provenance", "optimizer_ledger", "static_certificate",
        "phase_A_update_evidence", "phase_boundary_evidence",
        "phase_B_zero_step_certificate", "inductive_equality_certificate",
        "checkpoints", "result_envelope", "passed",
    }:
        return False
    envelope = value.get("result_envelope")
    ledger = value.get("optimizer_ledger")
    if not validate_result_evidence_envelope(envelope) or not validate_optimizer_ledger(
        ledger
    ):
        return False
    assert isinstance(envelope, Mapping) and isinstance(ledger, Mapping)
    evidence = envelope.get("evidence")
    failure = envelope.get("failure_evidence")
    if not isinstance(evidence, Mapping):
        return False
    for name in (
        "static_certificate", "phase_A_update_evidence",
        "phase_boundary_evidence", "phase_B_zero_step_certificate",
        "inductive_equality_certificate", "checkpoints", "optimizer_ledger",
    ):
        if not _nested_equal(value.get(name), evidence.get(name)):
            return False
    result = envelope.get("result")
    base = bool(
        value.get("assessment_kind")
        == "G51_STRICT_WITNESS_WITH_ADVERSE_EVIDENCE_V1"
        and value.get("algorithm_id") == ALGORITHM_ID
        and value.get("source_id") == SOURCE_ID
        and value.get("schema_version") == SCHEMA_VERSION
        and isinstance(value.get("provenance"), Mapping)
        and set(value["provenance"])
        == set(_assessment_provenance(ACCEPTED_G50_EXECUTION_CODE_COMMIT))
        and isinstance(
            value["provenance"].get("implementation_source_commit"), str
        )
        and len(value["provenance"]["implementation_source_commit"]) == 40
        and {
            key: row
            for key, row in value["provenance"].items()
            if key != "implementation_source_commit"
        }
        == {
            key: row
            for key, row in _assessment_provenance(
                ACCEPTED_G50_EXECUTION_CODE_COMMIT
            ).items()
            if key != "implementation_source_commit"
        }
        and value.get("passed") is (result == EXACT_RESULT)
        and ledger.get("phase_B_steps") == 0
        and ledger.get("no_steps_after_detection") is True
    )
    if not base:
        return False
    if result == EXACT_RESULT:
        checkpoints = value.get("checkpoints")
        reference_checkpoint = (
            checkpoints.get(REFERENCE_ARM)
            if isinstance(checkpoints, Mapping)
            else None
        )
        checkpoint_source = (
            reference_checkpoint.get("source")
            if isinstance(reference_checkpoint, Mapping)
            else None
        )
        return bool(
            failure is None
            and ledger.get("completed_paired_passes") == PPO_PASSES
            and ledger.get("failure_detected_before_current_pair") is False
            and evidence.get("numerical_witness_invoked") is True
            and evidence.get("numerical_witness_all_zero") is True
            and isinstance(checkpoint_source, Mapping)
            and checkpoint_source.get("implementation_commit")
            == value["provenance"].get("implementation_source_commit")
            and validate_structural_witness(evidence)
        )
    if not isinstance(failure, Mapping):
        return False
    reason = failure.get("reason")
    diagnostics = failure.get("diagnostics")
    if reason not in ASSESSMENT_ALLOWED_FAILURE_REASONS or not isinstance(
        diagnostics, Mapping
    ):
        return False
    pass_index = diagnostics.get("pass_index")
    if result == COUPLING_RESULT:
        return bool(
            reason == "phase_A_pre_step_semantic_coupling"
            and _pre_step_semantic_coupling_detected(diagnostics)
            and isinstance(pass_index, int)
            and ledger.get("completed_paired_passes") == pass_index
            and ledger.get("failure_detected_before_current_pair") is True
        )
    if result == NUMERICALLY_UNRESOLVED_RESULT:
        if reason == "phase_A_pre_step_numeric_difference":
            return bool(
                _pre_step_numeric_difference_detected(diagnostics)
                and isinstance(pass_index, int)
                and ledger.get("completed_paired_passes") == pass_index
                and ledger.get("failure_detected_before_current_pair") is True
            )
        return bool(
            reason == "phase_A_actual_Adam_kernel_difference"
            and isinstance(pass_index, int)
            and ledger.get("completed_paired_passes") == pass_index + 1
            and ledger.get("failure_detected_before_current_pair") is False
        )
    return bool(
        result == INVALID_RESULT
        and reason == "static_certificate_failed_before_optimizer"
        and not validate_static_certificate(value.get("static_certificate"))
        and ledger.get("completed_paired_passes") == 0
        and ledger.get("failure_detected_before_current_pair") is True
    )


def _json_safe(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return {"tensor_digest": _tensor_digest(value), "shape": list(value.shape), "dtype": str(value.dtype)}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(row) for key, row in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(row) for row in value]
    return value


def serialize_diagnostics(record: Mapping[str, object]) -> str:
    return json.dumps(_json_safe(record), sort_keys=True, separators=(",", ":"), allow_nan=False)
