"""Build and validate the zero-science G51 structural-reduction proof."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import multiprocessing
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


_THREAD_ENV_NAMES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
for _thread_env_name in _THREAD_ENV_NAMES:
    os.environ[_thread_env_name] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51
    as source,
)
from scripts import (
    run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50
    as g50_runner,
)


SCHEMA_VERSION = source.SCHEMA_VERSION
ALGORITHM_ID = source.ALGORITHM_ID
SOURCE_ID = source.SOURCE_ID
DESIGN_STAGE_COMMIT = "fb16a412841ad69912d927262dae8f694ea5471a"
ACCEPTED_PREDECESSOR_SOURCE_COMMIT = (
    "044d9690fa19aa07b8e68bf5cbb2a159c19be8c1"
)

# G51 is an unaligned code candidate.  No token or source/stage value in this
# file can authorize formal execution; a later independently reviewed binding
# must change that boundary in a separate assignment.
AUTHORIZATION_TOKEN: None = None
ALIGNED_IMPLEMENTATION_COMMIT: None = None
ALIGNMENT_STAGE_COMMIT: None = None
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_"
    "REDUCTION_G51_CODE_SCIENCE_ALIGNMENT_AUDIT"
)

INVALID_BRANCH = source.INVALID_RESULT
COUPLING_BRANCH = source.COUPLING_RESULT
REMOVABLE_BRANCH = source.EXACT_RESULT
UNRESOLVED_BRANCH = source.NUMERICALLY_UNRESOLVED_RESULT
FIRST_MATCH_ORDER = (
    INVALID_BRANCH,
    COUPLING_BRANCH,
    REMOVABLE_BRANCH,
    UNRESOLVED_BRANCH,
)
if tuple(source.RESULT_BRANCHES) != FIRST_MATCH_ORDER:
    raise RuntimeError("G51 source result order does not match the frozen contract")

TRAIN_MANIFEST = "train_manifest.json"
EVALUATION_MANIFEST = "evaluation_manifest.json"
ANALYSIS_RESULT = "analysis_result.json"
CHECKPOINT_DIRECTORY = "checkpoints"
CHECKPOINT_FILES = {
    source.REFERENCE_ARM: "reference_final.pt",
    source.REDUCED_ARM: "reduced_final.pt",
}
TWO_PROCESS_REPORT_REFERENCE = "parallel_proof/two_process_equivalence.json"
SHARED_TRAJECTORY_REFERENCE = "proof_inputs/shared_phase_A_trajectory.pt"
ASSESSMENT_REFERENCE = "proof/result_assessment.pt"

DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 1
MAX_CPU_BUDGET = 6
MAX_PROCESS_WORKERS = 1
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}
WALL_CLOCK_CAP_SECONDS = 1_200.0

_TRAIN_KEYS = frozenset(
    {
        "schema_version",
        "algorithm_id",
        "source_id",
        "source_commit",
        "formal",
        "formal_statistical_run",
        "scientific_iteration_cost",
        "configuration",
        "source_controls",
        "native_backend",
        "seed_block",
        "cpu_execution",
        "result_assessment",
        "result_branch",
        "work_accounting",
        "operational_valid",
        "static_certificate",
        "structural_witness",
        "shared_phase_A_trajectory",
        "checkpoint_inventory",
        "checkpoint_selection",
        "execution_readiness_proof_only",
        "two_process_proof",
        "two_process_proof_artifact",
        "passed",
    }
)
_CHECKPOINT_ROW_KEYS = frozenset({"path", "sha256", "kind"})
_SHARED_TRAJECTORY_KEYS = frozenset(
    {"path", "sha256", "real_transitions", "used_by_both_paths", "source_trace"}
)
_STRUCTURAL_WITNESS_KEYS = frozenset(
    {
        "phase_A_update_evidence",
        "phase_boundary_evidence",
        "phase_B_zero_step_certificate",
        "inductive_equality_certificate",
    }
)
_EVALUATION_KEYS = frozenset(
    {
        "schema_version",
        "algorithm_id",
        "source_id",
        "source_commit",
        "formal",
        "formal_statistical_run",
        "scientific_iteration_cost",
        "train_manifest_sha256",
        "evaluation_kind",
        "D_G51",
        "registered_difference_vector",
        "canonical_final_checkpoint_projection_equal",
        "evaluation_optimizer_steps",
        "environment_transitions",
        "result_assessment_sha256",
        "result_branch",
        "operational_valid",
        "passed",
    }
)
_ANALYSIS_KEYS = frozenset(
    {
        "schema_version",
        "algorithm_id",
        "source_id",
        "source_commit",
        "formal",
        "formal_statistical_run",
        "scientific_iteration_cost",
        "train_manifest_sha256",
        "evaluation_manifest_sha256",
        "metrics",
        "first_match_order",
        "result_branch",
        "claim_ceiling",
        "result_assessment_sha256",
        "operational_valid",
        "passed",
    }
)
_METRIC_KEYS = frozenset(
    {
        "operational_valid",
        "coupling_localized",
        "static_dependency_certificate",
        "per_parameter_Adam_factorization",
        "D_G51",
        "numerical_witness_invoked",
        "numerical_witness_all_zero",
    }
)
_PROCESS_REPORT_KEYS = frozenset(
    {
        "proof_kind",
        "worker_count",
        "distinct_processes",
        "single_thread_workers",
        "deterministic_preassigned_index_merge",
        "semantic_payload_equal",
        "semantic_digest",
        "mechanical_reconstruction_not_scientific_witness",
        "scientific_real_transitions",
        "optimizer_steps",
        "formal",
        "formal_statistical_run",
        "scientific_iteration_cost",
        "passed",
    }
)
_STATIC_CERTIFICATE_KEYS = frozenset(
    {
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
)
_BOUNDARY_KEYS = frozenset(
    {
        "inventory_valid",
        "actor_state_bytes_equal",
        "log_std_bytes_equal",
        "actor_parameter_names_equal",
        "actor_parameter_shapes_equal",
        "actor_parameter_order_equal",
        "actor_trainable_masks_equal",
        "slow_critic_state_bytes_equal",
        "slow_critic_trainable_masks_equal",
        "only_phase_A_module_and_state_delta_is_credit_baselines",
        "actor_parameter_names",
        "reference_baseline_parameter_names",
        "reference_optimizer_parameter_names",
        "reduced_optimizer_parameter_names",
        "reference_actor_prefix_then_baseline_suffix",
        "reduced_actor_only",
        "shared_actor_parameter_storage_count",
        "baseline_parameter_storage_shared_with_actor",
        "optimizer_hyperparameters_equal",
        "optimizer_states_empty",
        "projection_RNG_consumption",
        "projection_optimizer_steps",
        "passed",
    }
)
_DEPENDENCY_COMPONENT_KEYS = frozenset(
    {
        "actor_gradient",
        "entropy",
        "action_or_logprob",
        "source_or_lifecycle",
        "checkpoint_selection",
        "evaluation",
        "result_selection",
    }
)
_STATIC_PREDICATE_KEYS = frozenset(
    {
        "shared_actor_baseline_parameter_count",
        "shared_actor_baseline_storage_count",
        "reduced_baseline_module_count",
        "reduced_baseline_parameter_count",
        "reduced_baseline_state_key_count",
        "reduced_actor_gradient_forbidden_read_count",
        "reduced_entropy_forbidden_read_count",
        "reduced_action_logprob_forbidden_read_count",
        "reduced_source_lifecycle_forbidden_read_count",
        "reduced_checkpoint_forbidden_read_count",
        "reduced_evaluation_forbidden_read_count",
        "reduced_result_forbidden_read_count",
        "reference_baseline_forward_RNG_change_count",
        "reference_baseline_buffer_mutation_count",
        "reference_baseline_forward_hook_count",
        "reference_baseline_backward_hook_count",
        "reference_baseline_stochastic_module_count",
    }
)
_OPTIMIZER_PREDICATE_KEYS = frozenset(
    {
        "actual_optimizer_is_Adam",
        "actor_parameter_order_equal",
        "reference_actor_prefix_baseline_suffix",
        "reduced_actor_only_order",
        "actor_hyperparameters_equal",
        "fresh_actor_state_rows_equal_not_factorization",
        "global_gradient_clipping_call_count",
        "joint_gradient_normalization_call_count",
        "loss_count_scaling_call_count",
        "optimizer_group_size_scaling_call_count",
        "non_parameter_optimizer_state_count",
        "scheduler_attachment_count",
        "cross_parameter_moment_reduction_call_count",
        "parameter_list_kernel_selector_count",
        "parameter_list_size_difference",
        "actual_kernel_witness_required",
    }
)
_PHASE_A_EVIDENCE_KEYS = frozenset(
    {
        "algorithm_id",
        "source_id",
        "update_index",
        "static_certificate",
        "normalization_instances",
        "normalization_before_both_PPO_passes",
        "normalization_recomputed_between_passes",
        "normalization_rows",
        "source_trace",
        "shared_stored_phase_A_batches",
        "episodes",
        "H",
        "real_transitions",
        "PPO_passes_per_arm",
        "actor_optimizer_steps_per_arm",
        "reference_baseline_parameter_Adam_exposures",
        "reduced_baseline_parameter_Adam_exposures",
        "total_optimizer_steps",
        "phase_B_optimizer_steps",
        "pass_records",
        "actual_autograd_cross_gradient_evidence",
        "actual_kernel_Adam_equality",
        "torch_RNG_unchanged",
        "K_search",
        "hypothetical_transitions",
        "D_G51",
        "passed",
    }
)
_PHASE_A_PASS_KEYS = frozenset(
    {
        "pass_index",
        "plans_prepared_before_either_step",
        "same_stored_trajectory",
        "actor_assigned_gradient_bytes_equal",
        "policy_loss_bytes_equal",
        "teacher_logprob_bytes_equal",
        "teacher_pre_tanh_bytes_equal",
        "teacher_action_bytes_equal",
        "baseline_loss_gradient_into_actor_count",
        "actor_loss_gradient_into_baseline_count",
        "actor_parameter_bytes_equal",
        "log_std_bytes_equal",
        "actor_Adam_step_bytes_equal",
        "actor_Adam_exp_avg_bytes_equal",
        "actor_Adam_exp_avg_sq_bytes_equal",
        "pre_tanh_bytes_equal",
        "action_bytes_equal",
        "logprob_bytes_equal",
        "baseline_RNG_consumption",
        "reference_baseline_parameter_Adam_exposure_count",
        "reduced_baseline_parameter_Adam_exposure_count",
        "actor_gradient_digest",
        "baseline_gradient_digest",
        "passed",
    }
)
_SOURCE_TRACE_KEYS = frozenset(
    {
        "episode_id_digest",
        "reward_trace_digest",
        "roster_trace_digest",
        "lifecycle_trace_digest",
        "same_stored_trajectory_for_both_paths",
    }
)
_PHASE_BOUNDARY_COMMON_KEYS = frozenset(
    {
        "completed_phase_A_updates",
        "retained_actor_bytes_equal",
        "phase_A_state_deleted",
        "fresh_phase_B_state_required",
        "projection_optimizer_steps",
        "projection_RNG_consumption",
        "passed",
    }
)
_INDUCTIVE_CERTIFICATE_KEYS = frozenset(
    {
        "certificate_kind",
        "base_actor_and_Adam_equal",
        "assigned_actor_gradients_equal",
        "actual_autograd_cross_gradient_zero",
        "actual_kernel_Adam_equality",
        "per_parameter_Adam_preserves_equality",
        "paired_source_and_action_noise_preserve_trajectory",
        "phase_A_induction_valid_for_every_update",
        "phase_boundary_actor_equal_and_state_deleted",
        "fresh_phase_B_Adam_equal",
        "common_G49_phase_B_induction_valid",
        "registered_difference_vector",
        "D_G51",
        "passed",
    }
)
_DIFFERENCE_VECTOR_KEYS = frozenset(
    {
        "actor_gradient",
        "actor_log_std",
        "actor_Adam",
        "pre_tanh_action_logprob",
        "reward_roster_lifecycle",
        "phase_boundary_projection",
        "phase_B_actor_Adam",
        "canonical_final_checkpoint",
    }
)
_CHECKPOINT_COMMON_KEYS = frozenset(
    {
        "schema_version",
        "kind",
        "final_only_checkpoint_identity",
        "actor_state",
        "log_std",
        "actor_Adam_state",
        "completed_phase_A_updates",
        "completed_phase_B_updates",
        "source",
    }
)
_CHECKPOINT_SOURCE_KEYS = frozenset(
    {
        "implementation_commit",
        "design_stage_commit",
        "predecessor_source_commit",
        "accepted_G50_formal_source_commit",
        "accepted_G50_execution_code_commit",
        "accepted_G50_alignment_stage_commit",
        "accepted_G50_formal_branch",
    }
)
_NATIVE_BACKEND_KEYS = frozenset(
    {"kind", "required", "python_fallback", "module", "build_identity"}
)
_MODULE_GRAPH_KEYS = frozenset({"modules", "parameters", "buffers"})
_MODULE_ROW_KEYS = frozenset({"name", "type"})
_PARAMETER_ROW_KEYS = frozenset({"name", "shape", "requires_grad", "storage"})
_BUFFER_ROW_KEYS = frozenset({"name", "shape", "storage"})
_BASELINE_FORWARD_AUDIT_KEYS = frozenset(
    {
        "input_schema",
        "output_schema",
        "output_finite",
        "RNG_change_count",
        "buffer_mutation_count",
        "forward_hook_count",
        "backward_hook_count",
        "stochastic_module_count",
    }
)
_PATH_IDENTITY_KEYS = frozenset(
    {
        "reference_plan",
        "reference_step",
        "reduced_plan",
        "reduced_step",
        "Adam_step",
        "registered_optimizer_step",
    }
)
_CALLABLE_IDENTITY_KEYS = frozenset({"module", "qualname", "code_digest"})
_CROSS_GRADIENT_KEYS = frozenset(
    {
        "baseline_loss_gradient_into_actor_count",
        "actor_loss_gradient_into_baseline_count",
        "all_zero",
    }
)
_ACTUAL_KERNEL_KEYS = frozenset(
    {
        "pass_count",
        "assigned_actor_gradients_equal",
        "actor_parameters_equal",
        "log_std_equal",
        "Adam_step_equal",
        "Adam_exp_avg_equal",
        "Adam_exp_avg_sq_equal",
        "all_equal",
    }
)
_PHASE_B_ZERO_STEP_KEYS = frozenset(
    {
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
)
_PHASE_B_ZERO_STEP_PREDICATE_KEYS = frozenset(
    {
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
    }
)
_NORMALIZATION_RECORD_KEYS = frozenset(
    {
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
)
_OPTIMIZER_HYPERPARAMETER_KEYS = frozenset(
    {
        "valid",
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
    }
)
_ACTOR_TRACE_KEYS = frozenset(
    {
        "pre_tanh_digest",
        "actions_same_zero_noise_digest",
        "token_log_probability_digest",
        "joint_log_probability_digest",
    }
)
_RESULT_ENVELOPE_KEYS = frozenset(
    {
        "algorithm_id",
        "source_id",
        "schema_version",
        "result",
        "result_order",
        "failure_evidence",
        "D_G51",
        "evidence",
        "valid_evidence",
        "successful_exact_result",
    }
)
_ASSESSMENT_REFERENCE_KEYS = frozenset({"path", "sha256", "result"})
_ASSESSMENT_KEYS = frozenset(
    {
        "assessment_kind",
        "algorithm_id",
        "source_id",
        "schema_version",
        "provenance",
        "optimizer_ledger",
        "static_certificate",
        "phase_A_update_evidence",
        "phase_boundary_evidence",
        "phase_B_zero_step_certificate",
        "inductive_equality_certificate",
        "checkpoints",
        "result_envelope",
        "passed",
    }
)
_ASSESSMENT_PROVENANCE_KEYS = frozenset(
    {
        "implementation_source_commit",
        "design_stage_commit",
        "predecessor_source_commit",
        "accepted_G50_formal_source_commit",
        "accepted_G50_execution_code_commit",
        "accepted_G50_alignment_stage_commit",
        "accepted_G50_formal_branch",
        "design_disposition",
        "arms",
    }
)
_FAILURE_EVIDENCE_KEYS = frozenset({"passed", "reason", "diagnostics"})
_OPTIMIZER_LEDGER_KEYS = frozenset(
    {
        "reference_actor_steps",
        "reduced_actor_steps",
        "reference_baseline_parameter_Adam_exposures",
        "reduced_baseline_parameter_Adam_exposures",
        "completed_paired_passes",
        "phase_B_steps",
        "failure_detected_before_current_pair",
        "no_steps_after_detection",
    }
)
_WORK_ACCOUNTING_KEYS = frozenset(
    {
        "fresh_initializations",
        "shared_phase_A_batches",
        "real_transitions",
        "reference_actor_optimizer_steps",
        "reduced_actor_optimizer_steps",
        "reference_baseline_parameter_Adam_exposures",
        "reduced_baseline_parameter_Adam_exposures",
        "completed_paired_passes",
        "phase_B_optimizer_steps",
        "execution_stopped_at_recorded_boundary",
    }
)
_SHARED_TRAJECTORY_TENSOR_FIELDS = (
    "observations",
    "active_mask",
    "critic_states",
    "actions",
    "pre_tanh_actions",
    "old_log_probs",
    "old_values",
    "old_immediate_baselines",
    "old_successor_baselines",
    "rewards",
    "hidden_before",
    "hidden_after",
    "prefix_action_sums",
    "terminal_hidden_reset_mask",
)


def _activate_single_thread_runtime() -> None:
    for name in _THREAD_ENV_NAMES:
        os.environ[name] = "1"
    torch.set_num_threads(1)


def _valid_commit(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{40}", value) is not None
    )


def _require_exact_keys(
    value: object, expected: frozenset[str], *, label: str
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise ValueError(f"G51 {label} schema mismatch")
    return value


def _native_backend_identity() -> dict[str, object]:
    row = _require_exact_keys(
        g50_runner._backend._native_backend_identity(),
        _NATIVE_BACKEND_KEYS,
        label="native backend identity",
    )
    if (
        row.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
        or row.get("required") is not True
        or row.get("python_fallback") is not False
        or not isinstance(row.get("module"), str)
        or not row.get("module")
        or not isinstance(row.get("build_identity"), str)
        or re.fullmatch(r"[0-9a-f]{20}", str(row["build_identity"])) is None
    ):
        raise RuntimeError("G51 inherited native backend identity is invalid")
    return dict(row)


def _strict_native_backend(value: object) -> bool:
    try:
        row = _require_exact_keys(
            value, _NATIVE_BACKEND_KEYS, label="native backend identity"
        )
        return dict(row) == _native_backend_identity()
    except (RuntimeError, ValueError):
        return False


def _strict_callable_identity(value: object) -> bool:
    try:
        row = _require_exact_keys(
            value, _CALLABLE_IDENTITY_KEYS, label="callable identity"
        )
    except ValueError:
        return False
    return bool(
        isinstance(row.get("module"), str)
        and row.get("module")
        and isinstance(row.get("qualname"), str)
        and row.get("qualname")
        and isinstance(row.get("code_digest"), str)
        and re.fullmatch(r"[0-9a-f]{64}", str(row["code_digest"])) is not None
    )


def _strict_module_graph(value: object) -> bool:
    try:
        row = _require_exact_keys(value, _MODULE_GRAPH_KEYS, label="module graph")
        modules = row.get("modules")
        parameters = row.get("parameters")
        buffers = row.get("buffers")
        if not all(isinstance(rows, list) for rows in (modules, parameters, buffers)):
            return False
        for module in modules:  # type: ignore[union-attr]
            item = _require_exact_keys(module, _MODULE_ROW_KEYS, label="module row")
            if not all(isinstance(item.get(name), str) for name in _MODULE_ROW_KEYS):
                return False
        for parameter in parameters:  # type: ignore[union-attr]
            item = _require_exact_keys(
                parameter, _PARAMETER_ROW_KEYS, label="parameter row"
            )
            if (
                not isinstance(item.get("name"), str)
                or not isinstance(item.get("shape"), list)
                or not all(isinstance(size, int) and size >= 0 for size in item["shape"])
                or not isinstance(item.get("requires_grad"), bool)
                or not isinstance(item.get("storage"), int)
            ):
                return False
        for buffer in buffers:  # type: ignore[union-attr]
            item = _require_exact_keys(buffer, _BUFFER_ROW_KEYS, label="buffer row")
            if (
                not isinstance(item.get("name"), str)
                or not isinstance(item.get("shape"), list)
                or not all(isinstance(size, int) and size >= 0 for size in item["shape"])
                or not isinstance(item.get("storage"), int)
            ):
                return False
    except ValueError:
        return False
    return True


def _stable_Adam_step_identity() -> dict[str, str]:
    surface = torch.optim.Adam.step
    if (
        surface is not torch.optim.Adam.step
        or surface.__module__ != "torch.optim.adam"
        or surface.__qualname__ != "Adam.step"
    ):
        raise RuntimeError("G51 torch.optim.Adam.step resolution changed")
    underlying = inspect.unwrap(surface)
    identity = source._callable_identity(underlying)
    if (
        identity.get("module") != "torch.optim.adam"
        or identity.get("qualname") != "Adam.step"
        or re.fullmatch(r"[0-9a-f]{64}", identity.get("code_digest", "")) is None
    ):
        raise RuntimeError("G51 stable torch.optim.Adam.step identity is invalid")
    return identity


def _rewrite_static_Adam_identity(
    value: object, *, source_validation_view: bool
) -> object:
    if isinstance(value, Mapping):
        rewritten = {
            key: _rewrite_static_Adam_identity(
                row, source_validation_view=source_validation_view
            )
            for key, row in value.items()
        }
        if (
            rewritten.get("certificate_kind")
            == "actual_zero_trajectory_dependency_graph_with_witness_required_Adam_closure"
            and isinstance(rewritten.get("path_identities"), Mapping)
        ):
            paths = dict(rewritten["path_identities"])
            paths["Adam_step"] = (
                source._callable_identity(torch.optim.Adam.step)
                if source_validation_view
                else _stable_Adam_step_identity()
            )
            rewritten["path_identities"] = paths
        return rewritten
    if isinstance(value, list):
        return [
            _rewrite_static_Adam_identity(
                row, source_validation_view=source_validation_view
            )
            for row in value
        ]
    if isinstance(value, tuple):
        return tuple(
            _rewrite_static_Adam_identity(
                row, source_validation_view=source_validation_view
            )
            for row in value
        )
    return value


def _source_validation_view(value: object) -> object:
    return _rewrite_static_Adam_identity(value, source_validation_view=True)


def _bind_stable_Adam_identity(value: object) -> object:
    return _rewrite_static_Adam_identity(value, source_validation_view=False)


def _static_Adam_bindings_are_stable(value: object) -> bool:
    found = False
    valid = True

    def visit(row: object) -> None:
        nonlocal found, valid
        if isinstance(row, Mapping):
            if (
                row.get("certificate_kind")
                == "actual_zero_trajectory_dependency_graph_with_witness_required_Adam_closure"
            ):
                found = True
                paths = row.get("path_identities")
                valid = bool(
                    valid
                    and isinstance(paths, Mapping)
                    and paths.get("Adam_step") == _stable_Adam_step_identity()
                )
            for child in row.values():
                visit(child)
        elif isinstance(row, (list, tuple)):
            for child in row:
                visit(child)

    visit(value)
    return found and valid


def _strict_static_certificate(value: object) -> bool:
    try:
        row = _require_exact_keys(
            value, _STATIC_CERTIFICATE_KEYS, label="static certificate"
        )
        boundary = _require_exact_keys(
            row.get("boundary"), _BOUNDARY_KEYS, label="phase-A boundary"
        )
        reference_graph = row.get("reference_module_parameter_graph")
        reduced_graph = row.get("reduced_module_parameter_graph")
        baseline_audit = _require_exact_keys(
            row.get("reference_baseline_forward_audit"),
            _BASELINE_FORWARD_AUDIT_KEYS,
            label="reference baseline forward audit",
        )
        path_identities = _require_exact_keys(
            row.get("path_identities"), _PATH_IDENTITY_KEYS, label="path identities"
        )
        components = _require_exact_keys(
            row.get("component_bytecode_reads"),
            _DEPENDENCY_COMPONENT_KEYS,
            label="component bytecode reads",
        )
        forbidden = _require_exact_keys(
            row.get("forbidden_reduced_dependency_reads"),
            _DEPENDENCY_COMPONENT_KEYS,
            label="forbidden dependency reads",
        )
        static = _require_exact_keys(
            row.get("static_predicates"),
            _STATIC_PREDICATE_KEYS,
            label="static predicates",
        )
        optimizer = _require_exact_keys(
            row.get("optimizer_predicates"),
            _OPTIMIZER_PREDICATE_KEYS,
            label="optimizer predicates",
        )
    except ValueError:
        return False
    return bool(
        source.validate_static_certificate(_source_validation_view(row))
        and row.get("certificate_kind")
        == "actual_zero_trajectory_dependency_graph_with_witness_required_Adam_closure"
        and boundary.get("passed") is True
        and _strict_module_graph(reference_graph)
        and _strict_module_graph(reduced_graph)
        and isinstance(baseline_audit.get("input_schema"), list)
        and len(baseline_audit["input_schema"]) == 2
        and baseline_audit["input_schema"][0] == 2
        and isinstance(baseline_audit["input_schema"][1], int)
        and baseline_audit["input_schema"][1] > 0
        and baseline_audit.get("output_schema") == [2, 2]
        and baseline_audit.get("output_finite") is True
        and all(
            baseline_audit[name] == 0
            for name in (
                "RNG_change_count",
                "buffer_mutation_count",
                "forward_hook_count",
                "backward_hook_count",
                "stochastic_module_count",
            )
        )
        and all(_strict_callable_identity(path_identities[name]) for name in _PATH_IDENTITY_KEYS)
        and path_identities["Adam_step"] == _stable_Adam_step_identity()
        and all(
            isinstance(components[name], list)
            and all(isinstance(item, str) for item in components[name])
            for name in _DEPENDENCY_COMPONENT_KEYS
        )
        and all(forbidden[name] == [] for name in _DEPENDENCY_COMPONENT_KEYS)
        and all(static[name] == 0 for name in _STATIC_PREDICATE_KEYS)
        and all(
            optimizer[name] is True
            for name in (
                "actual_optimizer_is_Adam",
                "actor_parameter_order_equal",
                "reference_actor_prefix_baseline_suffix",
                "reduced_actor_only_order",
                "actor_hyperparameters_equal",
                "fresh_actor_state_rows_equal_not_factorization",
                "actual_kernel_witness_required",
            )
        )
        and all(
            optimizer[name] == 0
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
        and isinstance(optimizer["parameter_list_kernel_selector_count"], int)
        and optimizer["parameter_list_kernel_selector_count"] > 0
        and isinstance(optimizer["parameter_list_size_difference"], int)
        and optimizer["parameter_list_size_difference"] > 0
        and row.get("witness_closure_requirements")
        == [
            "actual_autograd_cross_gradient_zero",
            "actual_assigned_actor_gradients_equal",
            "actual_kernel_actor_Adam_step_exp_avg_exp_avg_sq_equal",
        ]
    )


def _strict_phase_A_evidence(value: object) -> bool:
    try:
        row = _require_exact_keys(
            value, _PHASE_A_EVIDENCE_KEYS, label="phase-A evidence"
        )
        trace = _require_exact_keys(
            row.get("source_trace"), _SOURCE_TRACE_KEYS, label="source trace"
        )
        records = row.get("pass_records")
        if not isinstance(records, list) or len(records) != source.PPO_PASSES:
            return False
        for record in records:
            _require_exact_keys(
                record, _PHASE_A_PASS_KEYS, label="phase-A pass record"
            )
        cross = _require_exact_keys(
            row.get("actual_autograd_cross_gradient_evidence"),
            _CROSS_GRADIENT_KEYS,
            label="actual autograd cross-gradient evidence",
        )
        kernel = _require_exact_keys(
            row.get("actual_kernel_Adam_equality"),
            _ACTUAL_KERNEL_KEYS,
            label="actual Adam kernel equality",
        )
    except ValueError:
        return False
    return bool(
        source.validate_phase_A_update_evidence(_source_validation_view(row))
        and _strict_static_certificate(row.get("static_certificate"))
        and trace.get("same_stored_trajectory_for_both_paths") is True
        and cross.get("all_zero") is True
        and kernel.get("all_equal") is True
    )


def _strict_phase_B_zero_step_certificate(value: object) -> bool:
    try:
        row = _require_exact_keys(
            value, _PHASE_B_ZERO_STEP_KEYS, label="phase-B zero-step certificate"
        )
        _require_exact_keys(
            row.get("single_probe_identity"),
            _CALLABLE_IDENTITY_KEYS,
            label="phase-B single-probe identity",
        )
        _require_exact_keys(
            row.get("apply_pass_identity"),
            _CALLABLE_IDENTITY_KEYS,
            label="phase-B apply-pass identity",
        )
        _require_exact_keys(
            row.get("normalization_record"),
            _NORMALIZATION_RECORD_KEYS,
            label="phase-B normalization record",
        )
        predicates = _require_exact_keys(
            row.get("predicates"),
            _PHASE_B_ZERO_STEP_PREDICATE_KEYS,
            label="phase-B zero-step predicates",
        )
        canonical = dict(row)
        for field in (
            "actor_parameter_names",
            "optimizer_parameter_names",
            "optimizer_hyperparameters",
            "assigned_gradient_digest",
            "actor_trace",
        ):
            arm_rows = _require_exact_keys(
                row.get(field), frozenset(source.ARMS), label=f"phase-B {field}"
            )
            if field == "optimizer_hyperparameters":
                copied: dict[str, dict[str, object]] = {}
                for arm in source.ARMS:
                    hyper = dict(
                        _require_exact_keys(
                            arm_rows[arm],
                            _OPTIMIZER_HYPERPARAMETER_KEYS,
                            label="phase-B optimizer hyperparameters",
                        )
                    )
                    if isinstance(hyper.get("betas"), list):
                        hyper["betas"] = tuple(hyper["betas"])
                    copied[arm] = hyper
                canonical[field] = copied
            elif field == "actor_trace":
                for arm in source.ARMS:
                    trace = _require_exact_keys(
                        arm_rows[arm], _ACTOR_TRACE_KEYS, label="phase-B actor trace"
                    )
                    if not all(
                        isinstance(trace[name], str)
                        and re.fullmatch(r"[0-9a-f]{64}", trace[name]) is not None
                        for name in _ACTOR_TRACE_KEYS
                    ):
                        return False
        if not all(predicates[name] is True for name in _PHASE_B_ZERO_STEP_PREDICATE_KEYS):
            return False
    except (KeyError, TypeError, ValueError):
        return False
    return source.validate_phase_B_zero_step_certificate(canonical)


def _strict_phase_boundary(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != set(source.ARMS):
        return False
    try:
        reference = _require_exact_keys(
            value.get(source.REFERENCE_ARM),
            _PHASE_BOUNDARY_COMMON_KEYS
            | frozenset({"reference_shadow_baseline_deleted"}),
            label="reference phase boundary",
        )
        reduced = _require_exact_keys(
            value.get(source.REDUCED_ARM),
            _PHASE_BOUNDARY_COMMON_KEYS,
            label="reduced phase boundary",
        )
    except ValueError:
        return False
    return bool(
        reference.get("passed") is True
        and reference.get("reference_shadow_baseline_deleted") is True
        and reduced.get("passed") is True
        and reference.get("completed_phase_A_updates") == 1
        and reduced.get("completed_phase_A_updates") == 1
    )


def _strict_inductive_certificate(value: object) -> bool:
    try:
        row = _require_exact_keys(
            value, _INDUCTIVE_CERTIFICATE_KEYS, label="inductive certificate"
        )
        vector = _require_exact_keys(
            row.get("registered_difference_vector"),
            _DIFFERENCE_VECTOR_KEYS,
            label="registered difference vector",
        )
    except ValueError:
        return False
    return bool(
        source.validate_inductive_equality_certificate(row)
        and all(vector[name] == 0 for name in _DIFFERENCE_VECTOR_KEYS)
    )


def _strict_checkpoint_pair(
    value: object, *, static: Mapping[str, object], source_commit: str
) -> bool:
    if not isinstance(value, Mapping) or tuple(value) != source.ARMS:
        return False
    boundary = static.get("boundary")
    if not isinstance(boundary, Mapping):
        return False
    actor_names = boundary.get("actor_parameter_names")
    if not isinstance(actor_names, list) or not all(
        isinstance(name, str) for name in actor_names
    ):
        return False
    actor_state_names = [name for name in actor_names if name != "policy.log_std"]
    try:
        reference = _require_exact_keys(
            value.get(source.REFERENCE_ARM),
            _CHECKPOINT_COMMON_KEYS
            | frozenset(
                {
                    "algorithm_id",
                    "source_id",
                    "arm",
                    "phase_A_reference_evidence",
                }
            ),
            label="reference checkpoint",
        )
        reduced = _require_exact_keys(
            value.get(source.REDUCED_ARM),
            _CHECKPOINT_COMMON_KEYS
            | frozenset({"phase_A_projection_evidence"}),
            label="reduced checkpoint",
        )
        for row in (reference, reduced):
            source_row = _require_exact_keys(
                row.get("source"), _CHECKPOINT_SOURCE_KEYS, label="checkpoint source"
            )
            actor_state = row.get("actor_state")
            adam = row.get("actor_Adam_state")
            if (
                not isinstance(actor_state, Mapping)
                or list(actor_state) != actor_state_names
                or not all(isinstance(item, torch.Tensor) for item in actor_state.values())
                or not isinstance(adam, Mapping)
                or list(adam) != actor_names
                or not all(isinstance(item, Mapping) and not item for item in adam.values())
                or row.get("completed_phase_A_updates") != 1
                or row.get("completed_phase_B_updates") != 0
                or source_row.get("implementation_commit") != source_commit
                or source_row.get("design_stage_commit") != DESIGN_STAGE_COMMIT
                or source_row.get("predecessor_source_commit")
                != ACCEPTED_PREDECESSOR_SOURCE_COMMIT
                or source_row.get("accepted_G50_alignment_stage_commit")
                != "4df41063d077ace7e0c9212e0cbadbf56e1be4b7"
                or source_row.get("accepted_G50_formal_source_commit")
                != source.ACCEPTED_G50_FORMAL_SOURCE_COMMIT
                or source_row.get("accepted_G50_execution_code_commit")
                != source.ACCEPTED_G50_EXECUTION_CODE_COMMIT
                or source_row.get("accepted_G50_formal_branch")
                != source.ACCEPTED_G50_FORMAL_BRANCH
            ):
                return False
        if (
            reference.get("algorithm_id") != ALGORITHM_ID
            or reference.get("source_id") != SOURCE_ID
            or reference.get("arm") != source.REFERENCE_ARM
            or any(
                name in reduced for name in ("algorithm_id", "source_id", "arm")
            )
        ):
            return False
        if not _strict_phase_boundary(
            {
                source.REFERENCE_ARM: reference["phase_A_reference_evidence"],
                source.REDUCED_ARM: reduced["phase_A_projection_evidence"],
            }
        ):
            return False
    except (KeyError, ValueError):
        return False
    return source.validate_checkpoint_pair(value)


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"G51 JSON artifact is not an object: {path}")
    return value


def _artifact_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _semantic_digest(value: object) -> str:
    digest = hashlib.sha256()

    def visit(row: object) -> None:
        if isinstance(row, torch.Tensor):
            tensor = row.detach().cpu().contiguous()
            digest.update(b"tensor")
            digest.update(str(tensor.dtype).encode("ascii"))
            digest.update(json.dumps(list(tensor.shape)).encode("ascii"))
            digest.update(tensor.numpy().tobytes())
        elif isinstance(row, Mapping):
            digest.update(b"mapping")
            for key in sorted(row, key=lambda item: str(item)):
                digest.update(str(key).encode("utf-8"))
                visit(row[key])
        elif isinstance(row, (list, tuple)):
            digest.update(b"sequence")
            for item in row:
                visit(item)
        else:
            digest.update(type(row).__name__.encode("ascii"))
            digest.update(repr(row).encode("utf-8"))

    visit(value)
    return digest.hexdigest()


def _canonical_values_equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
        return bool(
            isinstance(left, torch.Tensor)
            and isinstance(right, torch.Tensor)
            and left.dtype == right.dtype
            and tuple(left.shape) == tuple(right.shape)
            and torch.equal(left.detach().cpu(), right.detach().cpu())
        )
    if isinstance(left, Mapping) or isinstance(right, Mapping):
        return bool(
            isinstance(left, Mapping)
            and isinstance(right, Mapping)
            and set(left) == set(right)
            and all(_canonical_values_equal(left[key], right[key]) for key in left)
        )
    if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        return bool(
            isinstance(left, (list, tuple))
            and isinstance(right, (list, tuple))
            and len(left) == len(right)
            and all(
                _canonical_values_equal(left_row, right_row)
                for left_row, right_row in zip(left, right, strict=True)
            )
        )
    return type(left) is type(right) and left == right


def _resolve_cpu_execution(
    cpu_budget: int | None, process_workers: int | None
) -> dict[str, object]:
    cpu = DEFAULT_CPU_BUDGET if cpu_budget is None else cpu_budget
    workers = DEFAULT_PROCESS_WORKERS if process_workers is None else process_workers
    if (
        isinstance(cpu, bool)
        or not isinstance(cpu, int)
        or not 1 <= cpu <= MAX_CPU_BUDGET
    ):
        raise ValueError("G51 cpu_budget must be an integer in 1..6")
    if workers != 1 or isinstance(workers, bool):
        raise ValueError(
            "G51 production proof is single-process and requires process_workers=1"
        )
    if workers > cpu:
        raise ValueError("G51 process_workers exceeds cpu_budget")
    return {
        "cpu_budget": cpu,
        "process_workers": workers,
        "supported_cpu_budget_ceiling": MAX_CPU_BUDGET,
        "supported_process_worker_ceiling": MAX_PROCESS_WORKERS,
        "cpu_parallelism_fixed_at_launch": True,
        "cpu_continuous_adaptation": False,
        "worker_start_method": "spawn",
        "deterministic_merge": "preassigned_index_not_completion_order",
        "worker_thread_controls": {
            **WORKER_THREAD_ENV,
            "torch_intraop_threads": 1,
        },
    }


def _configuration(
    *,
    formal: bool,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
    completed_paired_passes: int = source.PPO_PASSES,
    numerical_witness_invoked: bool = True,
    fresh_initializations: int = 1,
    shared_phase_A_batches: int = 1,
    real_transitions: int = source.MAX_REAL_TRANSITIONS,
) -> dict[str, object]:
    if not isinstance(formal, bool):
        raise TypeError("G51 formal scope must be bool")
    if (
        isinstance(completed_paired_passes, bool)
        or not isinstance(completed_paired_passes, int)
        or not 0 <= completed_paired_passes <= source.PPO_PASSES
        or not isinstance(numerical_witness_invoked, bool)
        or isinstance(fresh_initializations, bool)
        or fresh_initializations not in (0, 1)
        or isinstance(shared_phase_A_batches, bool)
        or shared_phase_A_batches not in (0, 1)
        or isinstance(real_transitions, bool)
        or real_transitions not in (0, source.MAX_REAL_TRANSITIONS)
    ):
        raise ValueError("G51 configuration work accounting is invalid")
    return {
        **_resolve_cpu_execution(cpu_budget, process_workers),
        "formal": formal,
        "formal_statistical_run": False,
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_python_fallback": False,
        "proof_kind": (
            "structural_certificate_plus_mandatory_actual_Adam_kernel_witness"
        ),
        "accepted_G50_fresh_initializations": fresh_initializations,
        "shared_stored_phase_A_batches": shared_phase_A_batches,
        "episodes": source.NUM_ENVS,
        "horizon": source.HORIZON,
        "real_transitions": real_transitions,
        "PPO_passes_per_arm": source.PPO_PASSES,
        "actor_optimizer_steps_per_arm": completed_paired_passes,
        "reference_baseline_parameter_Adam_exposures": completed_paired_passes,
        "reduced_baseline_parameter_Adam_exposures": 0,
        "total_optimizer_steps": 2 * completed_paired_passes,
        "phase_B_optimizer_steps": 0,
        "bootstrap_resamples": 0,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "numerical_witness_invoked": numerical_witness_invoked,
        "same_stored_trajectory_for_both_paths": True,
        "checkpoint_selection": "final_only_proof_witness",
        "arms": list(source.ARMS),
        "wall_clock_cap_seconds": WALL_CLOCK_CAP_SECONDS,
    }


def source_controls() -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "parent_source_id": source.g50.SOURCE_ID,
        "design_stage_commit": DESIGN_STAGE_COMMIT,
        "design_disposition": source.DESIGN_DISPOSITION,
        "accepted_predecessor_source_commit": ACCEPTED_PREDECESSOR_SOURCE_COMMIT,
        "accepted_g50_formal_source_commit": (
            source.ACCEPTED_G50_FORMAL_SOURCE_COMMIT
        ),
        "accepted_g50_execution_code_commit": (
            source.ACCEPTED_G50_EXECUTION_CODE_COMMIT
        ),
        "accepted_g50_alignment_stage_commit": (
            source.ACCEPTED_G50_ALIGNMENT_STAGE_COMMIT
        ),
        "accepted_g50_formal_branch": source.ACCEPTED_G50_FORMAL_BRANCH,
        "reference_arm": source.REFERENCE_ARM,
        "reduced_arm": source.REDUCED_ARM,
        "first_match_order": list(FIRST_MATCH_ORDER),
        "formal_alignment_status": "UNALIGNED_FAIL_CLOSED",
        "formal_authorization_token": None,
        "aligned_implementation_commit": None,
        "alignment_stage_commit": None,
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_python_fallback": False,
        "K_search": 0,
        "hypothetical_transitions": 0,
    }


def _fresh_root(root: Path) -> Path:
    resolved = Path(root).resolve()
    if resolved.exists() and (
        not resolved.is_dir() or any(resolved.iterdir())
    ):
        raise ValueError("G51 run root must be absent or empty")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _checkpoint_path(run_root: Path, arm: str) -> Path:
    if arm not in source.ARMS:
        raise ValueError("G51 checkpoint arm is not registered")
    return Path(run_root) / CHECKPOINT_DIRECTORY / CHECKPOINT_FILES[arm]


def _save_checkpoint(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(dict(value), path)


def _load_checkpoint(path: Path) -> dict[str, object]:
    value = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(value, dict):
        raise ValueError(f"G51 checkpoint is not an object: {path}")
    return value


def _load_shared_phase_A_trajectory(path: Path) -> object:
    return torch.load(path, map_location="cpu", weights_only=False)


def _strict_shared_phase_A_trajectory(value: object) -> bool:
    if type(value) is not source.AnchoredRosterTrajectory:
        return False
    expected_prefix = (source.HORIZON, source.NUM_ENVS)
    if not all(
        isinstance(getattr(value, name, None), torch.Tensor)
        and tuple(getattr(value, name).shape[:2]) == expected_prefix
        for name in _SHARED_TRAJECTORY_TENSOR_FIELDS
    ):
        return False
    return bool(
        tuple(value.rewards.shape) == expected_prefix
        and value.rewards.numel() == source.MAX_REAL_TRANSITIONS
        and isinstance(value.ledgers, tuple)
        and len(value.ledgers) == source.NUM_ENVS
        and isinstance(value.outcomes, tuple)
        and len(value.outcomes) == source.NUM_ENVS
    )


def _strict_result_envelope(value: object) -> bool:
    try:
        row = _require_exact_keys(
            value, _RESULT_ENVELOPE_KEYS, label="source result envelope"
        )
        failure = row.get("failure_evidence")
        if failure is not None:
            failure_row = _require_exact_keys(
                failure, _FAILURE_EVIDENCE_KEYS, label="source failure evidence"
            )
            if (
                failure_row.get("passed") is not False
                or not isinstance(failure_row.get("reason"), str)
                or not isinstance(failure_row.get("diagnostics"), Mapping)
            ):
                return False
    except ValueError:
        return False
    return bool(
        _static_Adam_bindings_are_stable(row)
        and source.validate_result_evidence_envelope(_source_validation_view(row))
    )


def _strict_structural_assessment(
    value: object, *, source_commit: str
) -> bool:
    try:
        row = _require_exact_keys(
            value, _ASSESSMENT_KEYS, label="structural assessment"
        )
        provenance = _require_exact_keys(
            row.get("provenance"),
            _ASSESSMENT_PROVENANCE_KEYS,
            label="assessment provenance",
        )
        ledger = _require_exact_keys(
            row.get("optimizer_ledger"),
            _OPTIMIZER_LEDGER_KEYS,
            label="assessment optimizer ledger",
        )
    except ValueError:
        return False
    envelope = row.get("result_envelope")
    if (
        not source.validate_optimizer_ledger(ledger)
        or not _strict_result_envelope(envelope)
        or not source.validate_structural_assessment(_source_validation_view(row))
        or provenance.get("implementation_source_commit") != source_commit
    ):
        return False
    assert isinstance(envelope, Mapping)
    result = envelope.get("result")
    if result == REMOVABLE_BRANCH:
        return bool(
            row.get("passed") is True
            and _strict_static_certificate(row.get("static_certificate"))
            and _strict_phase_A_evidence(row.get("phase_A_update_evidence"))
            and _strict_phase_boundary(row.get("phase_boundary_evidence"))
            and _strict_phase_B_zero_step_certificate(
                row.get("phase_B_zero_step_certificate")
            )
            and _strict_inductive_certificate(
                row.get("inductive_equality_certificate")
            )
            and _strict_checkpoint_pair(
                row.get("checkpoints"),
                static=row["static_certificate"],
                source_commit=source_commit,
            )
        )
    if result not in {INVALID_BRANCH, COUPLING_BRANCH, UNRESOLVED_BRANCH}:
        return False
    if any(
        row.get(name) is not None
        for name in (
            "phase_A_update_evidence",
            "phase_boundary_evidence",
            "phase_B_zero_step_certificate",
            "inductive_equality_certificate",
            "checkpoints",
        )
    ):
        return False
    return bool(
        row.get("passed") is False
        and (
            result == INVALID_BRANCH
            or _strict_static_certificate(row.get("static_certificate"))
        )
    )


def _assessment_record(
    *,
    source_commit: str,
    evidence: Mapping[str, object],
    ledger: Mapping[str, object],
    failure: source.G51InvariantError | None,
) -> dict[str, object]:
    source_evidence = _source_validation_view(evidence)
    if not isinstance(source_evidence, dict):
        raise RuntimeError("G51 source evidence validation view failed")
    source_failure = (
        None
        if failure is None
        else source.G51InvariantError(
            failure.reason,
            _source_validation_view(failure.diagnostics),
        )
    )
    envelope = source.build_result_evidence_envelope(
        source_evidence, failure=source_failure
    )
    assessment = {
        "assessment_kind": "G51_STRICT_WITNESS_WITH_ADVERSE_EVIDENCE_V1",
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "schema_version": SCHEMA_VERSION,
        "provenance": source._assessment_provenance(source_commit),
        "optimizer_ledger": dict(ledger),
        "static_certificate": source_evidence.get("static_certificate"),
        "phase_A_update_evidence": source_evidence.get("phase_A_update_evidence"),
        "phase_boundary_evidence": source_evidence.get("phase_boundary_evidence"),
        "phase_B_zero_step_certificate": source_evidence.get(
            "phase_B_zero_step_certificate"
        ),
        "inductive_equality_certificate": source_evidence.get(
            "inductive_equality_certificate"
        ),
        "checkpoints": source_evidence.get("checkpoints"),
        "result_envelope": envelope,
        "passed": envelope["result"] == REMOVABLE_BRANCH,
    }
    bound = _bind_stable_Adam_identity(assessment)
    if not isinstance(bound, dict):
        raise RuntimeError("G51 stable Adam identity binding failed")
    assessment = bound
    if not _strict_structural_assessment(
        assessment, source_commit=source_commit
    ):
        raise RuntimeError("G51 structural assessment construction failed")
    return assessment


def _positive_assessment(
    *,
    source_commit: str,
    static: Mapping[str, object],
    phase_A: Mapping[str, object],
    phase_boundary: Mapping[str, Mapping[str, object]],
    phase_B_zero_step: Mapping[str, object],
    checkpoints: Mapping[str, Mapping[str, object]],
    inductive: Mapping[str, object],
) -> dict[str, object]:
    ledger = source._optimizer_ledger(
        paired_passes=int(phase_A["actor_optimizer_steps_per_arm"]),
        failure_detected_before_current_pair=False,
    )
    bundle = {
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "static_certificate": static,
        "phase_A_update_evidence": phase_A,
        "phase_boundary_evidence": phase_boundary,
        "phase_B_zero_step_certificate": phase_B_zero_step,
        "phase_B_optimizer_steps": 0,
        "checkpoints": checkpoints,
        "inductive_equality_certificate": inductive,
        "result": REMOVABLE_BRANCH,
        "passed": True,
    }
    evidence = {
        **bundle,
        "provenance_valid": True,
        "evidence_valid": True,
        "numerical_witness_invoked": True,
        "numerical_witness_all_zero": True,
        "optimizer_ledger": ledger,
    }
    return _assessment_record(
        source_commit=source_commit,
        evidence=evidence,
        ledger=ledger,
        failure=None,
    )


def _adverse_assessment(
    *, source_commit: str, failure: source.G51InvariantError
) -> dict[str, object]:
    if failure.reason not in source.ASSESSMENT_ALLOWED_FAILURE_REASONS:
        raise failure
    if failure.reason == "static_certificate_failed_before_optimizer":
        static = failure.diagnostics
        ledger = source._optimizer_ledger(
            paired_passes=0, failure_detected_before_current_pair=True
        )
        evidence_valid = False
    else:
        static = failure.diagnostics.get("static_certificate")
        ledger = failure.diagnostics.get("optimizer_ledger")
        evidence_valid = True
    if not source.validate_optimizer_ledger(ledger):
        raise failure
    assert isinstance(ledger, Mapping)
    pass_index = failure.diagnostics.get("pass_index")
    if failure.reason == "phase_A_pre_step_coupling_or_numeric_difference":
        ledger_consistent = bool(
            isinstance(pass_index, int)
            and not isinstance(pass_index, bool)
            and ledger["completed_paired_passes"] == pass_index
            and ledger["failure_detected_before_current_pair"] is True
        )
    elif failure.reason == "phase_A_actual_Adam_kernel_difference":
        ledger_consistent = bool(
            isinstance(pass_index, int)
            and not isinstance(pass_index, bool)
            and ledger["completed_paired_passes"] == pass_index + 1
            and ledger["failure_detected_before_current_pair"] is False
        )
    else:
        ledger_consistent = bool(
            ledger["completed_paired_passes"] == 0
            and ledger["failure_detected_before_current_pair"] is True
        )
    if not ledger_consistent:
        raise failure
    evidence = {
        "static_certificate": static,
        "phase_A_update_evidence": None,
        "phase_boundary_evidence": None,
        "phase_B_zero_step_certificate": None,
        "inductive_equality_certificate": None,
        "checkpoints": None,
        "provenance_valid": True,
        "evidence_valid": evidence_valid,
        "numerical_witness_invoked": failure.reason
        != "static_certificate_failed_before_optimizer",
        "numerical_witness_all_zero": False,
        "optimizer_ledger": ledger,
    }
    return _assessment_record(
        source_commit=source_commit,
        evidence=evidence,
        ledger=ledger,  # type: ignore[arg-type]
        failure=failure,
    )


def _work_accounting(assessment: Mapping[str, object]) -> dict[str, object]:
    ledger = assessment.get("optimizer_ledger")
    if not isinstance(ledger, Mapping) or not source.validate_optimizer_ledger(ledger):
        raise ValueError("G51 assessment optimizer ledger is invalid")
    return {
        "fresh_initializations": 1,
        "shared_phase_A_batches": 1,
        "real_transitions": source.MAX_REAL_TRANSITIONS,
        "reference_actor_optimizer_steps": ledger["reference_actor_steps"],
        "reduced_actor_optimizer_steps": ledger["reduced_actor_steps"],
        "reference_baseline_parameter_Adam_exposures": ledger[
            "reference_baseline_parameter_Adam_exposures"
        ],
        "reduced_baseline_parameter_Adam_exposures": ledger[
            "reduced_baseline_parameter_Adam_exposures"
        ],
        "completed_paired_passes": ledger["completed_paired_passes"],
        "phase_B_optimizer_steps": ledger["phase_B_steps"],
        "execution_stopped_at_recorded_boundary": True,
    }


def _strict_work_accounting(
    value: object, *, assessment: Mapping[str, object]
) -> bool:
    try:
        row = _require_exact_keys(
            value, _WORK_ACCOUNTING_KEYS, label="work accounting"
        )
    except ValueError:
        return False
    return dict(row) == _work_accounting(assessment)


def _formal_admission_errors(
    *,
    source_commit: str,
    authorization_token: str | None,
    preflight_root: Path | None,
    alignment_disposition: str | None,
    aligned_source_commit: str | None,
    alignment_stage_commit: str | None,
) -> list[str]:
    del (
        source_commit,
        authorization_token,
        preflight_root,
        alignment_disposition,
        aligned_source_commit,
        alignment_stage_commit,
    )
    return ["G51 formal execution requires an independently ALIGNED source"]


# Keep the new source coupling in this small adapter block.  The proof entry
# constructs the accepted complete G50 null graph once, clones both arms,
# collects one shared 8x48 batch, and invokes the actual phase-A Adam kernel.
def _prepare_static_source_boundary() -> tuple[
    dict[str, source.G51Model],
    dict[str, torch.optim.Adam],
    dict[str, object],
    dict[str, object],
    dict[str, int],
]:
    seeds = source.seed_block(0, formal=False)
    g50_runner._backend.configure_runtime(seeds["phase_A_gradient_probe"])
    models = source.make_phase_A_models(
        member_capacity=8,
        initialization_seed=seeds["initialization"],
    )
    optimizers = source.make_phase_A_optimizers(models)
    boundary = source.phase_A_boundary_audit(models, optimizers)
    static = _bind_stable_Adam_identity(
        source.reconstruct_static_certificate(models, optimizers)
    )
    if not isinstance(static, dict):
        raise RuntimeError("G51 static Adam identity binding failed")
    return models, optimizers, dict(boundary), static, seeds


def _materialize_source_bundle(
    *, source_commit: str
) -> tuple[
    dict[str, object],
    object,
    dict[str, int],
]:
    models, optimizers, _, _, seeds = _prepare_static_source_boundary()
    trajectory = source.g40.collect_g40_trajectory(
        models[source.REFERENCE_ARM],
        episode_ids=tuple(range(source.NUM_ENVS)),
        ledger_seed=seeds["phase_A_ledger"],
        action_seed=seeds["phase_A_action"],
        device=torch.device("cpu"),
    )
    try:
        phase_A = source.optimize_phase_A_update(
            models,
            optimizers,
            trajectory,
            update_index=0,
        )
    except source.G51InvariantError as failure:
        assessment = _adverse_assessment(
            source_commit=source_commit, failure=failure
        )
        return assessment, trajectory, seeds
    bound_phase_A = _bind_stable_Adam_identity(phase_A)
    if not isinstance(bound_phase_A, dict) or not _strict_phase_A_evidence(
        bound_phase_A
    ):
        raise RuntimeError("G51 phase-A witness failed")
    static = phase_A["static_certificate"]
    if not isinstance(static, Mapping):
        raise RuntimeError("G51 phase-A static certificate is absent")
    phase_B_models, phase_boundary = source.project_phase_B_models(
        models,
        completed_phase_A_updates=1,
    )
    phase_B_optimizers = source.make_phase_B_optimizers(phase_B_models)
    phase_B_zero_step = source.build_phase_B_zero_step_certificate(
        phase_B_models, phase_B_optimizers, trajectory
    )
    if not _strict_phase_B_zero_step_certificate(phase_B_zero_step):
        raise RuntimeError("G51 phase-B zero-step certificate failed")
    checkpoints = source.build_final_checkpoints(
        phase_B_models,
        phase_B_optimizers,
        source_commit=source_commit,
        completed_phase_A_updates=1,
        completed_phase_B_updates=0,
        phase_boundary_evidence=phase_boundary,
    )
    inductive = source.build_inductive_equality_certificate(
        phase_A_evidence=phase_A,
        phase_boundary_evidence=phase_boundary,
        phase_B_evidence=phase_B_zero_step,
        checkpoints=checkpoints,
    )
    if not _strict_inductive_certificate(inductive):
        raise RuntimeError("G51 inductive equality certificate failed")
    if not _strict_checkpoint_pair(
        checkpoints, static=static, source_commit=source_commit
    ):
        raise RuntimeError("G51 checkpoint pair failed")
    assessment = _positive_assessment(
        source_commit=source_commit,
        static=static,
        phase_A=phase_A,
        phase_boundary=phase_boundary,
        phase_B_zero_step=phase_B_zero_step,
        checkpoints=checkpoints,
        inductive=inductive,
    )
    return assessment, trajectory, seeds


def _validate_source_products(
    *,
    assessment: object,
    static: object,
    witness: object,
    checkpoints: object,
    source_commit: str,
) -> bool:
    if not isinstance(assessment, Mapping) or not _strict_structural_assessment(
        assessment, source_commit=source_commit
    ):
        return False
    envelope = assessment.get("result_envelope")
    if not isinstance(envelope, Mapping):
        return False
    result = envelope.get("result")
    if not _canonical_values_equal(static, assessment.get("static_certificate")):
        return False
    if result != REMOVABLE_BRANCH:
        return witness is None and checkpoints == {}
    if not isinstance(witness, Mapping) or set(witness) != set(
        _STRUCTURAL_WITNESS_KEYS
    ):
        return False
    phase_A = witness.get("phase_A_update_evidence")
    phase_B = witness.get("phase_B_zero_step_certificate")
    boundary = witness.get("phase_boundary_evidence")
    inductive = witness.get("inductive_equality_certificate")
    return bool(
        _strict_static_certificate(static)
        and _strict_phase_A_evidence(phase_A)
        and _strict_phase_boundary(boundary)
        and _strict_phase_B_zero_step_certificate(phase_B)
        and _strict_inductive_certificate(inductive)
        and _strict_checkpoint_pair(
            checkpoints, static=static, source_commit=source_commit
        )
        and _canonical_values_equal(
            assessment.get("phase_A_update_evidence"), phase_A
        )
        and _canonical_values_equal(
            assessment.get("phase_boundary_evidence"), boundary
        )
        and _canonical_values_equal(
            assessment.get("phase_B_zero_step_certificate"), phase_B
        )
        and _canonical_values_equal(
            assessment.get("inductive_equality_certificate"), inductive
        )
        and _canonical_values_equal(assessment.get("checkpoints"), checkpoints)
    )


def _write_training_assessment(
    *,
    root: Path,
    source_commit: str,
    assessment: Mapping[str, object],
    trajectory: object,
    seeds: Mapping[str, int],
    native_backend: Mapping[str, object],
    cpu_budget: int | None,
    process_workers: int | None,
) -> dict[str, object]:
    if not _strict_structural_assessment(
        assessment, source_commit=source_commit
    ) or not _strict_shared_phase_A_trajectory(trajectory):
        raise ValueError("G51 training assessment or trajectory is invalid")
    envelope = assessment["result_envelope"]
    assert isinstance(envelope, Mapping)
    result = envelope["result"]
    evidence = envelope["evidence"]
    assert isinstance(evidence, Mapping)
    work = _work_accounting(assessment)
    configuration = _configuration(
        formal=False,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
        completed_paired_passes=int(work["completed_paired_passes"]),
        numerical_witness_invoked=bool(evidence["numerical_witness_invoked"]),
        fresh_initializations=1,
        shared_phase_A_batches=1,
        real_transitions=source.MAX_REAL_TRANSITIONS,
    )
    trajectory_path = root / SHARED_TRAJECTORY_REFERENCE
    trajectory_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(trajectory, trajectory_path)
    source_trace = source.g47._source_trace_evidence(trajectory)
    assessment_path = root / ASSESSMENT_REFERENCE
    _save_checkpoint(assessment_path, assessment)
    exact = result == REMOVABLE_BRANCH
    if exact:
        checkpoints = assessment["checkpoints"]
        assert isinstance(checkpoints, Mapping)
        witness: dict[str, object] | None = {
            "phase_A_update_evidence": assessment["phase_A_update_evidence"],
            "phase_boundary_evidence": assessment["phase_boundary_evidence"],
            "phase_B_zero_step_certificate": assessment[
                "phase_B_zero_step_certificate"
            ],
            "inductive_equality_certificate": assessment[
                "inductive_equality_certificate"
            ],
        }
    else:
        checkpoints = {}
        witness = None
    checkpoint_inventory: dict[str, dict[str, object]] = {}
    for arm in source.ARMS if exact else ():
        path = _checkpoint_path(root, arm)
        checkpoint = checkpoints[arm]
        assert isinstance(checkpoint, Mapping)
        _save_checkpoint(path, checkpoint)
        checkpoint_inventory[arm] = {
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "sha256": _artifact_digest(path),
            "kind": "final_only_proof_witness",
        }
    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": source_commit,
        "formal": False,
        "formal_statistical_run": False,
        "scientific_iteration_cost": 0,
        "configuration": configuration,
        "source_controls": source_controls(),
        "native_backend": dict(native_backend),
        "seed_block": dict(seeds),
        "cpu_execution": _resolve_cpu_execution(cpu_budget, process_workers),
        "result_assessment": {
            "path": ASSESSMENT_REFERENCE,
            "sha256": _artifact_digest(assessment_path),
            "result": result,
        },
        "result_branch": result,
        "work_accounting": work,
        "operational_valid": True,
        "static_certificate": assessment.get("static_certificate"),
        "structural_witness": witness,
        "shared_phase_A_trajectory": {
            "path": SHARED_TRAJECTORY_REFERENCE,
            "sha256": _artifact_digest(trajectory_path),
            "real_transitions": source.MAX_REAL_TRANSITIONS,
            "used_by_both_paths": True,
            "source_trace": source_trace,
        },
        "checkpoint_inventory": checkpoint_inventory,
        "checkpoint_selection": "final_only_proof_witness" if exact else None,
        "execution_readiness_proof_only": False,
        "two_process_proof": None,
        "two_process_proof_artifact": None,
        "passed": exact,
    }
    _write_json(root / TRAIN_MANIFEST, manifest)
    validate_training_artifacts(root, expected_source_commit=source_commit)
    return manifest


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    preflight_root: Path | None = None,
    alignment_disposition: str | None = None,
    aligned_source_commit: str | None = None,
    alignment_stage_commit: str | None = None,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
    _interface_smoke_only: bool = False,
) -> dict[str, object]:
    if not _valid_commit(source_commit):
        raise ValueError("G51 train requires a lowercase 40-character source commit")
    configuration = _configuration(
        formal=formal,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )
    if formal:
        errors = _formal_admission_errors(
            source_commit=source_commit,
            authorization_token=authorization_token,
            preflight_root=preflight_root,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
            alignment_stage_commit=alignment_stage_commit,
        )
        raise ValueError(" | ".join(errors))
    if any(
        value is not None
        for value in (
            authorization_token,
            preflight_root,
            alignment_disposition,
            aligned_source_commit,
            alignment_stage_commit,
        )
    ):
        raise ValueError("G51 proof-only scope forbids formal admission fields")
    _activate_single_thread_runtime()
    if _interface_smoke_only:
        _, _, boundary, static, _ = _prepare_static_source_boundary()
        if (
            set(boundary) != set(_BOUNDARY_KEYS)
            or boundary.get("passed") is not True
            or not _strict_static_certificate(static)
        ):
            raise RuntimeError("G51 interface smoke static boundary failed")
        configuration = _configuration(
            formal=False,
            cpu_budget=cpu_budget,
            process_workers=process_workers,
            completed_paired_passes=0,
            numerical_witness_invoked=False,
            fresh_initializations=1,
            shared_phase_A_batches=0,
            real_transitions=0,
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "algorithm_id": ALGORITHM_ID,
            "source_id": SOURCE_ID,
            "source_commit": source_commit,
            "formal": False,
            "configuration": configuration,
            "source_controls": source_controls(),
            "native_backend": _native_backend_identity(),
            "phase_A_boundary": boundary,
            "static_certificate": static,
            "return_schema": "G51_train_manifest_v1",
            "scientific_real_transitions": 0,
            "optimizer_steps": 0,
            "scientific_iteration_cost": 0,
            "passed": True,
        }
    root = _fresh_root(run_root)
    native_backend = _native_backend_identity()
    assessment, trajectory, seeds = _materialize_source_bundle(
        source_commit=source_commit
    )
    return _write_training_assessment(
        root=root,
        source_commit=source_commit,
        assessment=assessment,
        trajectory=trajectory,
        seeds=seeds,
        native_backend=native_backend,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )


def record_terminal_assessment(
    *,
    run_root: Path,
    source_commit: str,
    assessment: Mapping[str, object],
    trajectory: object,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, object]:
    if not _valid_commit(source_commit) or not _strict_structural_assessment(
        assessment, source_commit=source_commit
    ):
        raise ValueError("G51 terminal assessment is invalid")
    envelope = assessment.get("result_envelope")
    if not isinstance(envelope, Mapping) or envelope.get("result") == REMOVABLE_BRANCH:
        raise ValueError("G51 terminal recorder cannot admit an exact result")
    _activate_single_thread_runtime()
    root = _fresh_root(run_root)
    return _write_training_assessment(
        root=root,
        source_commit=source_commit,
        assessment=assessment,
        trajectory=trajectory,
        seeds=source.seed_block(0, formal=False),
        native_backend=_native_backend_identity(),
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )


def validate_training_artifacts(
    run_root: Path, *, expected_source_commit: str | None = None
) -> dict[str, object]:
    root = Path(run_root).resolve()
    manifest = _read_json(root / TRAIN_MANIFEST)
    _require_exact_keys(manifest, _TRAIN_KEYS, label="train manifest")
    source_commit = manifest.get("source_commit")
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("algorithm_id") != ALGORITHM_ID
        or manifest.get("source_id") != SOURCE_ID
        or not _valid_commit(source_commit)
        or (
            expected_source_commit is not None
            and source_commit != expected_source_commit
        )
        or manifest.get("formal") is not False
        or manifest.get("formal_statistical_run") is not False
        or manifest.get("scientific_iteration_cost") != 0
        or manifest.get("source_controls") != source_controls()
        or not _strict_native_backend(manifest.get("native_backend"))
        or manifest.get("seed_block") != source.seed_block(0, formal=False)
        or manifest.get("operational_valid") is not True
    ):
        raise ValueError("G51 train manifest invariant mismatch")
    assessment_reference = _require_exact_keys(
        manifest.get("result_assessment"),
        _ASSESSMENT_REFERENCE_KEYS,
        label="result assessment reference",
    )
    assessment_path = root / str(assessment_reference.get("path"))
    if (
        assessment_reference.get("path") != ASSESSMENT_REFERENCE
        or not assessment_path.is_file()
        or assessment_reference.get("sha256") != _artifact_digest(assessment_path)
    ):
        raise ValueError("G51 result assessment identity mismatch")
    assessment = _load_checkpoint(assessment_path)
    if not _strict_structural_assessment(
        assessment, source_commit=str(source_commit)
    ):
        raise ValueError("G51 result assessment validation failed")
    envelope = assessment["result_envelope"]
    assert isinstance(envelope, Mapping)
    result_branch = envelope["result"]
    exact = result_branch == REMOVABLE_BRANCH
    if (
        assessment_reference.get("result") != result_branch
        or manifest.get("result_branch") != result_branch
        or manifest.get("passed") is not exact
        or not _strict_work_accounting(
            manifest.get("work_accounting"), assessment=assessment
        )
    ):
        raise ValueError("G51 branch/result accounting mismatch")
    work = manifest["work_accounting"]
    assert isinstance(work, Mapping)
    evidence = envelope.get("evidence")
    assert isinstance(evidence, Mapping)
    configuration = manifest.get("configuration")
    if not isinstance(configuration, Mapping) or dict(configuration) != _configuration(
        formal=False,
        cpu_budget=int(configuration.get("cpu_budget", 0)),
        process_workers=int(configuration.get("process_workers", 0)),
        completed_paired_passes=int(work["completed_paired_passes"]),
        numerical_witness_invoked=bool(evidence["numerical_witness_invoked"]),
        fresh_initializations=int(work["fresh_initializations"]),
        shared_phase_A_batches=int(work["shared_phase_A_batches"]),
        real_transitions=int(work["real_transitions"]),
    ):
        raise ValueError("G51 serialized configuration mismatch")
    if manifest.get("cpu_execution") != _resolve_cpu_execution(
        int(configuration["cpu_budget"]),
        int(configuration["process_workers"]),
    ):
        raise ValueError("G51 CPU execution record mismatch")
    shared = _require_exact_keys(
        manifest.get("shared_phase_A_trajectory"),
        _SHARED_TRAJECTORY_KEYS,
        label="shared trajectory",
    )
    trajectory_path = root / str(shared.get("path"))
    if (
        shared.get("path") != SHARED_TRAJECTORY_REFERENCE
        or shared.get("real_transitions") != source.MAX_REAL_TRANSITIONS
        or shared.get("used_by_both_paths") is not True
        or not trajectory_path.is_file()
        or shared.get("sha256") != _artifact_digest(trajectory_path)
    ):
        raise ValueError("G51 shared trajectory identity mismatch")
    trajectory = _load_shared_phase_A_trajectory(trajectory_path)
    if not _strict_shared_phase_A_trajectory(trajectory):
        raise ValueError("G51 shared trajectory payload is not the exact 8x48 type")
    witness = manifest.get("structural_witness")
    recomputed_trace = source.g47._source_trace_evidence(trajectory)
    try:
        _require_exact_keys(
            shared.get("source_trace"),
            _SOURCE_TRACE_KEYS,
            label="serialized source trace",
        )
        _require_exact_keys(
            recomputed_trace, _SOURCE_TRACE_KEYS, label="recomputed source trace"
        )
    except ValueError as error:
        raise ValueError("G51 shared trajectory source trace schema mismatch") from error
    if shared.get("source_trace") != recomputed_trace:
        raise ValueError("G51 shared trajectory source trace mismatch")
    if exact:
        phase_A = (
            witness.get("phase_A_update_evidence")
            if isinstance(witness, Mapping)
            else None
        )
        if (
            not isinstance(phase_A, Mapping)
            or phase_A.get("source_trace") != recomputed_trace
        ):
            raise ValueError("G51 phase-A evidence source trace mismatch")
    inventory = manifest.get("checkpoint_inventory")
    expected_inventory = set(source.ARMS) if exact else set()
    if not isinstance(inventory, Mapping) or set(inventory) != expected_inventory:
        raise ValueError("G51 final checkpoint inventory mismatch")
    checkpoints: dict[str, dict[str, object]] = {}
    for arm in source.ARMS if exact else ():
        row = _require_exact_keys(
            inventory.get(arm), _CHECKPOINT_ROW_KEYS, label="checkpoint row"
        )
        expected = f"{CHECKPOINT_DIRECTORY}/{CHECKPOINT_FILES[arm]}"
        if row.get("path") != expected or row.get("kind") != "final_only_proof_witness":
            raise ValueError("G51 checkpoint inventory row mismatch")
        path = root / expected
        if not path.is_file() or row.get("sha256") != _artifact_digest(path):
            raise ValueError("G51 checkpoint digest mismatch")
        checkpoints[arm] = _load_checkpoint(path)
    if (
        (exact and manifest.get("checkpoint_selection") != "final_only_proof_witness")
        or (not exact and manifest.get("checkpoint_selection") is not None)
    ):
        raise ValueError("G51 checkpoint selection/branch mismatch")
    if not _validate_source_products(
        assessment=assessment,
        static=manifest.get("static_certificate"),
        witness=witness,
        checkpoints=checkpoints,
        source_commit=str(source_commit),
    ):
        raise ValueError("G51 source evidence/checkpoint validation failed")
    readiness = manifest.get("execution_readiness_proof_only") is True
    report_reference = manifest.get("two_process_proof_artifact")
    if readiness:
        if not exact:
            raise ValueError("G51 adverse result cannot claim execution readiness")
        if report_reference != TWO_PROCESS_REPORT_REFERENCE:
            raise ValueError("G51 readiness process-proof reference mismatch")
        report = _read_json(root / str(report_reference))
        _validate_process_report(report)
        if report != manifest.get("two_process_proof"):
            raise ValueError("G51 readiness process-proof payload mismatch")
    elif (
        report_reference is not None
        or manifest.get("two_process_proof") is not None
    ):
        raise ValueError("G51 ordinary artifact contains readiness-only proof")
    return manifest


_WORKER_PAYLOAD_KEYS = frozenset(
    {
        "index",
        "pid",
        "thread_environment",
        "torch_intraop_threads",
        "semantic_digest",
    }
)


def _proof_reload_worker(task: Mapping[str, object]) -> None:
    _activate_single_thread_runtime()
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G51 readiness worker output path is not fresh")
    root = Path(str(task["run_root"]))
    training = validate_training_artifacts(root)
    checkpoints = {
        arm: _load_checkpoint(_checkpoint_path(root, arm)) for arm in source.ARMS
    }
    semantic = {
        "source_commit": training["source_commit"],
        "native_backend": training["native_backend"],
        "seed_block": training["seed_block"],
        "result_assessment": training["result_assessment"],
        "result_branch": training["result_branch"],
        "work_accounting": training["work_accounting"],
        "operational_valid": training["operational_valid"],
        "shared_phase_A_trajectory": training["shared_phase_A_trajectory"],
        "static_certificate": training["static_certificate"],
        "structural_witness": training["structural_witness"],
        "checkpoint_inventory": training["checkpoint_inventory"],
        "canonical_actor_projections": {
            arm: source.canonical_actor_projection(checkpoints[arm])
            for arm in source.ARMS
        },
    }
    payload = {
        "index": int(task["index"]),
        "pid": os.getpid(),
        "thread_environment": {
            name: os.environ.get(name) for name in _THREAD_ENV_NAMES
        },
        "torch_intraop_threads": torch.get_num_threads(),
        "semantic_digest": _semantic_digest(semantic),
    }
    _write_json(output_path, payload)


def _proof_process_entry(
    task: Mapping[str, object], ready_event: Any, release_event: Any
) -> None:
    _activate_single_thread_runtime()
    ready_event.set()
    if not release_event.wait(timeout=60.0):
        raise RuntimeError("G51 readiness worker release barrier timed out")
    _proof_reload_worker(task)


def _run_distinct_proof_workers(
    tasks: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if [task.get("index") for task in tasks] != [0, 1]:
        raise ValueError("G51 readiness requires exactly two indexed proof tasks")
    context = multiprocessing.get_context("spawn")
    ready_events = [context.Event() for _ in tasks]
    release_event = context.Event()
    processes = [
        context.Process(
            target=_proof_process_entry,
            args=(dict(task), ready_event, release_event),
        )
        for task, ready_event in zip(tasks, ready_events, strict=True)
    ]
    try:
        for process in processes:
            process.start()
        for index, ready_event in enumerate(ready_events):
            if not ready_event.wait(timeout=60.0):
                raise RuntimeError(
                    f"G51 readiness worker {index} failed to reach the release barrier"
                )
        pids = [process.pid for process in processes]
        if any(pid is None for pid in pids) or len(set(pids)) != 2:
            raise RuntimeError("G51 readiness did not launch two distinct processes")
        release_event.set()
        for process in processes:
            process.join(timeout=60.0)
        if any(process.is_alive() for process in processes):
            raise RuntimeError("G51 readiness worker timed out")
        if any(process.exitcode != 0 for process in processes):
            raise RuntimeError("G51 readiness worker exited unsuccessfully")
    finally:
        release_event.set()
        for process in processes:
            if process.pid is not None and process.is_alive():
                process.terminate()
        for process in processes:
            if process.pid is not None:
                process.join(timeout=5.0)
    results: list[dict[str, object]] = []
    for task, process in zip(tasks, processes, strict=True):
        output_path = Path(str(task["output_path"]))
        if not output_path.is_file():
            raise RuntimeError("G51 readiness worker did not produce its output")
        row = _read_json(output_path)
        _require_exact_keys(row, _WORKER_PAYLOAD_KEYS, label="worker payload")
        if row.get("index") != task["index"] or row.get("pid") != process.pid:
            raise RuntimeError("G51 readiness worker identity/output mismatch")
        results.append(row)
    return results


def _validate_process_report(report: object) -> Mapping[str, object]:
    value = _require_exact_keys(
        report, _PROCESS_REPORT_KEYS, label="two-process report"
    )
    if (
        value.get("proof_kind")
        != "two_process_G51_independent_artifact_reload"
        or value.get("worker_count") != 2
        or value.get("distinct_processes") is not True
        or value.get("single_thread_workers") is not True
        or value.get("deterministic_preassigned_index_merge") is not True
        or value.get("semantic_payload_equal") is not True
        or not isinstance(value.get("semantic_digest"), str)
        or re.fullmatch(r"[0-9a-f]{64}", str(value["semantic_digest"])) is None
        or value.get("mechanical_reconstruction_not_scientific_witness") is not True
        or value.get("scientific_real_transitions") != 0
        or value.get("optimizer_steps") != 0
        or value.get("formal") is not False
        or value.get("formal_statistical_run") is not False
        or value.get("scientific_iteration_cost") != 0
        or value.get("passed") is not True
    ):
        raise ValueError("G51 two-process report invariant mismatch")
    return value


def prove_two_process_artifact_reload(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    tasks = tuple(
        {
            "index": index,
            "run_root": str(root),
            "output_path": str(root / "parallel_proof" / f"worker_{index}.json"),
        }
        for index in range(2)
    )
    rows = _run_distinct_proof_workers(tasks)
    semantic_equal = rows[0]["semantic_digest"] == rows[1]["semantic_digest"]
    report = {
        "proof_kind": "two_process_G51_independent_artifact_reload",
        "worker_count": 2,
        "distinct_processes": len({int(row["pid"]) for row in rows}) == 2,
        "single_thread_workers": all(
            row["torch_intraop_threads"] == 1
            and all(
                row["thread_environment"].get(name) == "1"  # type: ignore[union-attr]
                for name in _THREAD_ENV_NAMES
            )
            for row in rows
        ),
        "deterministic_preassigned_index_merge": [row["index"] for row in rows]
        == [0, 1],
        "semantic_payload_equal": semantic_equal,
        "semantic_digest": rows[0]["semantic_digest"] if semantic_equal else "",
        "mechanical_reconstruction_not_scientific_witness": True,
        "scientific_real_transitions": 0,
        "optimizer_steps": 0,
        "formal": False,
        "formal_statistical_run": False,
        "scientific_iteration_cost": 0,
        "passed": bool(semantic_equal),
    }
    _write_json(root / TWO_PROCESS_REPORT_REFERENCE, report)
    _validate_process_report(report)
    return report


def _attach_readiness_process_proof(
    manifest: Mapping[str, object], report: Mapping[str, object]
) -> dict[str, object]:
    if manifest.get("execution_readiness_proof_only") is not False:
        raise ValueError("G51 readiness manifest was complete before process proof")
    if (
        manifest.get("two_process_proof") is not None
        or manifest.get("two_process_proof_artifact") is not None
    ):
        raise ValueError("G51 readiness process proof was already attached")
    _validate_process_report(report)
    updated = dict(manifest)
    updated["execution_readiness_proof_only"] = True
    updated["two_process_proof"] = dict(report)
    updated["two_process_proof_artifact"] = TWO_PROCESS_REPORT_REFERENCE
    return updated


def _inductive_certificate(training: Mapping[str, object]) -> Mapping[str, object]:
    witness = training.get("structural_witness")
    if not isinstance(witness, Mapping):
        raise ValueError("G51 structural witness is absent")
    certificate = witness.get("inductive_equality_certificate")
    if (
        not isinstance(certificate, Mapping)
        or not _strict_inductive_certificate(certificate)
    ):
        raise ValueError("G51 inductive equality certificate is invalid")
    return certificate


def evaluate(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    if (root / EVALUATION_MANIFEST).exists():
        raise ValueError("G51 evaluation artifact already exists")
    training = validate_training_artifacts(root)
    result_branch = training["result_branch"]
    exact = result_branch == REMOVABLE_BRANCH
    assessment_reference = training["result_assessment"]
    assert isinstance(assessment_reference, Mapping)
    assessment = _load_checkpoint(root / ASSESSMENT_REFERENCE)
    envelope = assessment["result_envelope"]
    assert isinstance(envelope, Mapping)
    if exact:
        checkpoints = {
            arm: _load_checkpoint(_checkpoint_path(root, arm)) for arm in source.ARMS
        }
        if not source.validate_checkpoint_pair(checkpoints):
            raise RuntimeError("G51 evaluate checkpoint reload mismatch")
        reference_projection = source.canonical_actor_projection(
            checkpoints[source.REFERENCE_ARM]
        )
        reduced_projection = source.canonical_actor_projection(
            checkpoints[source.REDUCED_ARM]
        )
        canonical_equal: bool | None = _canonical_values_equal(
            reference_projection, reduced_projection
        )
        certificate = _inductive_certificate(training)
        difference = certificate.get("registered_difference_vector")
        if not isinstance(difference, Mapping):
            raise RuntimeError("G51 registered difference vector is absent")
        difference_vector: dict[str, object] | None = dict(difference)
        D_G51 = certificate.get("D_G51")
        evaluation_kind = "exact_registered_D_G51_and_canonical_actor_projection"
    else:
        canonical_equal = None
        difference_vector = None
        D_G51 = envelope.get("D_G51")
        evaluation_kind = "terminal_source_result_envelope"
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": training["source_commit"],
        "formal": False,
        "formal_statistical_run": False,
        "scientific_iteration_cost": 0,
        "train_manifest_sha256": _artifact_digest(root / TRAIN_MANIFEST),
        "evaluation_kind": evaluation_kind,
        "D_G51": D_G51,
        "registered_difference_vector": difference_vector,
        "canonical_final_checkpoint_projection_equal": canonical_equal,
        "evaluation_optimizer_steps": 0,
        "environment_transitions": 0,
        "result_assessment_sha256": assessment_reference["sha256"],
        "result_branch": result_branch,
        "operational_valid": True,
        "passed": bool(exact and D_G51 == 0 and canonical_equal),
    }
    if exact and result["passed"] is not True:
        raise RuntimeError("G51 evaluation exact projection mismatch")
    _write_json(root / EVALUATION_MANIFEST, result)
    validate_evaluation_artifacts(root)
    return result


def validate_evaluation_artifacts(run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    training = validate_training_artifacts(root)
    result_branch = training["result_branch"]
    exact = result_branch == REMOVABLE_BRANCH
    certificate = _inductive_certificate(training) if exact else None
    value = _read_json(root / EVALUATION_MANIFEST)
    _require_exact_keys(value, _EVALUATION_KEYS, label="evaluation manifest")
    expected_vector = (
        certificate.get("registered_difference_vector")
        if isinstance(certificate, Mapping)
        else None
    )
    assessment_reference = training["result_assessment"]
    assert isinstance(assessment_reference, Mapping)
    assessment = _load_checkpoint(root / ASSESSMENT_REFERENCE)
    envelope = assessment["result_envelope"]
    assert isinstance(envelope, Mapping)
    expected_D = certificate.get("D_G51") if exact else envelope.get("D_G51")
    expected_kind = (
        "exact_registered_D_G51_and_canonical_actor_projection"
        if exact
        else "terminal_source_result_envelope"
    )
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("algorithm_id") != ALGORITHM_ID
        or value.get("source_id") != SOURCE_ID
        or value.get("source_commit") != training.get("source_commit")
        or value.get("formal") is not False
        or value.get("formal_statistical_run") is not False
        or value.get("scientific_iteration_cost") != 0
        or value.get("train_manifest_sha256")
        != _artifact_digest(root / TRAIN_MANIFEST)
        or value.get("evaluation_kind") != expected_kind
        or value.get("D_G51") != expected_D
        or value.get("registered_difference_vector") != expected_vector
        or (
            exact
            and (
                value.get("D_G51") != 0
                or value.get("canonical_final_checkpoint_projection_equal") is not True
            )
        )
        or (
            not exact
            and value.get("canonical_final_checkpoint_projection_equal") is not None
        )
        or value.get("evaluation_optimizer_steps") != 0
        or value.get("environment_transitions") != 0
        or value.get("result_assessment_sha256")
        != assessment_reference.get("sha256")
        or value.get("result_branch") != result_branch
        or value.get("operational_valid") is not True
        or value.get("passed") is not exact
    ):
        raise ValueError("G51 evaluation artifact invariant mismatch")
    return value


def select_g51_result_branch(metrics: Mapping[str, object]) -> str:
    if metrics.get("operational_valid") is not True:
        return INVALID_BRANCH
    if metrics.get("coupling_localized") is True:
        return COUPLING_BRANCH
    if (
        metrics.get("static_dependency_certificate") is True
        and metrics.get("per_parameter_Adam_factorization") is True
        and metrics.get("D_G51") == 0
        and metrics.get("numerical_witness_invoked") is True
        and metrics.get("numerical_witness_all_zero") is True
    ):
        return REMOVABLE_BRANCH
    return UNRESOLVED_BRANCH


def _analysis_metrics(
    training: Mapping[str, object], evaluation: Mapping[str, object]
) -> dict[str, object]:
    result_branch = training.get("result_branch")
    static = training.get("static_certificate")
    witness = training.get("structural_witness")
    phase_A = (
        witness.get("phase_A_update_evidence")
        if isinstance(witness, Mapping)
        else None
    )
    cross = (
        phase_A.get("actual_autograd_cross_gradient_evidence")
        if isinstance(phase_A, Mapping)
        else None
    )
    kernel = (
        phase_A.get("actual_kernel_Adam_equality")
        if isinstance(phase_A, Mapping)
        else None
    )
    factorized = bool(
        isinstance(cross, Mapping)
        and cross.get("all_zero") is True
        and isinstance(kernel, Mapping)
        and kernel.get("all_equal") is True
    )
    configuration = training.get("configuration")
    numerical_invoked = bool(
        isinstance(configuration, Mapping)
        and configuration.get("numerical_witness_invoked") is True
    )
    return {
        "operational_valid": result_branch != INVALID_BRANCH,
        "coupling_localized": result_branch == COUPLING_BRANCH,
        "static_dependency_certificate": _strict_static_certificate(static),
        "per_parameter_Adam_factorization": factorized,
        "D_G51": evaluation.get("D_G51"),
        "numerical_witness_invoked": numerical_invoked,
        "numerical_witness_all_zero": bool(
            result_branch == REMOVABLE_BRANCH and evaluation.get("D_G51") == 0
        ),
    }


def _result_assessment(
    root: Path, training: Mapping[str, object]
) -> Mapping[str, object]:
    reference = training.get("result_assessment")
    if not isinstance(reference, Mapping):
        raise ValueError("G51 result assessment reference is absent")
    assessment = _load_checkpoint(root / ASSESSMENT_REFERENCE)
    if not _strict_structural_assessment(
        assessment, source_commit=str(training.get("source_commit"))
    ):
        raise ValueError("G51 result assessment is invalid")
    return assessment


def analyze(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    if (root / ANALYSIS_RESULT).exists():
        raise ValueError("G51 analysis artifact already exists")
    training = validate_training_artifacts(root)
    evaluation = validate_evaluation_artifacts(root)
    assessment = _result_assessment(root, training)
    envelope = assessment["result_envelope"]
    assert isinstance(envelope, Mapping)
    source_evidence = envelope["evidence"]
    assert isinstance(source_evidence, Mapping)
    metrics = _analysis_metrics(training, evaluation)
    branch = select_g51_result_branch(metrics)
    source_branch = source.classify_result(_source_validation_view(source_evidence))
    if source_branch != branch or branch != training.get("result_branch"):
        raise RuntimeError("G51 runner/source branch classification mismatch")
    exact = branch == REMOVABLE_BRANCH
    assessment_reference = training["result_assessment"]
    assert isinstance(assessment_reference, Mapping)
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": training["source_commit"],
        "formal": False,
        "formal_statistical_run": False,
        "scientific_iteration_cost": 0,
        "train_manifest_sha256": _artifact_digest(root / TRAIN_MANIFEST),
        "evaluation_manifest_sha256": _artifact_digest(
            root / EVALUATION_MANIFEST
        ),
        "metrics": metrics,
        "first_match_order": list(FIRST_MATCH_ORDER),
        "result_branch": branch,
        "claim_ceiling": (
            "exact_G50_P0_phase_A_shadow_baseline_package_removability_only"
        ),
        "result_assessment_sha256": assessment_reference["sha256"],
        "operational_valid": True,
        "passed": exact,
    }
    _write_json(root / ANALYSIS_RESULT, result)
    validate_analysis_artifacts(root)
    return result


def validate_analysis_artifacts(run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    training = validate_training_artifacts(root)
    evaluation = validate_evaluation_artifacts(root)
    assessment = _result_assessment(root, training)
    envelope = assessment["result_envelope"]
    assert isinstance(envelope, Mapping)
    source_evidence = envelope["evidence"]
    assert isinstance(source_evidence, Mapping)
    value = _read_json(root / ANALYSIS_RESULT)
    _require_exact_keys(value, _ANALYSIS_KEYS, label="analysis result")
    metrics = value.get("metrics")
    _require_exact_keys(metrics, _METRIC_KEYS, label="analysis metrics")
    expected_metrics = _analysis_metrics(training, evaluation)
    expected_branch = training.get("result_branch")
    exact = expected_branch == REMOVABLE_BRANCH
    assessment_reference = training["result_assessment"]
    assert isinstance(assessment_reference, Mapping)
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("algorithm_id") != ALGORITHM_ID
        or value.get("source_id") != SOURCE_ID
        or value.get("source_commit") != training.get("source_commit")
        or value.get("formal") is not False
        or value.get("formal_statistical_run") is not False
        or value.get("scientific_iteration_cost") != 0
        or value.get("train_manifest_sha256")
        != _artifact_digest(root / TRAIN_MANIFEST)
        or value.get("evaluation_manifest_sha256")
        != _artifact_digest(root / EVALUATION_MANIFEST)
        or metrics != expected_metrics
        or value.get("first_match_order") != list(FIRST_MATCH_ORDER)
        or value.get("result_branch") != select_g51_result_branch(metrics)
        or value.get("result_branch") != expected_branch
        or value.get("result_branch")
        != source.classify_result(_source_validation_view(source_evidence))
        or value.get("claim_ceiling")
        != "exact_G50_P0_phase_A_shadow_baseline_package_removability_only"
        or value.get("result_assessment_sha256")
        != assessment_reference.get("sha256")
        or value.get("operational_valid") is not True
        or value.get("passed") is not exact
    ):
        raise ValueError("G51 analysis artifact invariant mismatch")
    return value


def reload_artifacts(run_root: Path) -> dict[str, dict[str, object]]:
    return {
        "training": validate_training_artifacts(run_root),
        "evaluation": validate_evaluation_artifacts(run_root),
        "analysis": validate_analysis_artifacts(run_root),
    }


def readiness_interface_smoke(*, source_commit: str) -> dict[str, object]:
    row = train(
        run_root=Path("."),
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        cpu_budget=DEFAULT_CPU_BUDGET,
        process_workers=DEFAULT_PROCESS_WORKERS,
        _interface_smoke_only=True,
    )
    row["interfaces"] = [
            "train",
            "evaluate",
            "analyze",
            "exercise",
            "readiness-smoke",
            "readiness-train",
            "readiness-validate",
            "readiness-reload",
            "readiness-evaluate",
            "readiness-analyze",
        ]
    return row


def readiness_train(*, run_root: Path, source_commit: str) -> dict[str, object]:
    root = Path(run_root).resolve()
    manifest = train(
        run_root=root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        cpu_budget=DEFAULT_CPU_BUDGET,
        process_workers=DEFAULT_PROCESS_WORKERS,
    )
    if manifest.get("result_branch") != REMOVABLE_BRANCH:
        return manifest
    report = prove_two_process_artifact_reload(run_root=root)
    manifest = _attach_readiness_process_proof(manifest, report)
    _write_json(root / TRAIN_MANIFEST, manifest)
    validate_training_artifacts(root, expected_source_commit=source_commit)
    return manifest


def readiness_validate(*, run_root: Path) -> dict[str, object]:
    training = validate_training_artifacts(run_root)
    if training.get("execution_readiness_proof_only") is not True:
        raise RuntimeError("G51 readiness validation requires process proof")
    return {
        "artifact_validation": True,
        "source_commit": training["source_commit"],
        "additional_optimizer_steps": 0,
        "additional_environment_transitions": 0,
        "passed": True,
    }


def readiness_reload(*, run_root: Path) -> dict[str, object]:
    root = Path(run_root).resolve()
    before = _artifact_digest(root / TRAIN_MANIFEST)
    training = validate_training_artifacts(root)
    checkpoints = {
        arm: _load_checkpoint(_checkpoint_path(root, arm)) for arm in source.ARMS
    }
    if not source.validate_checkpoint_pair(checkpoints):
        raise RuntimeError("G51 readiness checkpoint reload failed")
    after = _artifact_digest(root / TRAIN_MANIFEST)
    if before != after:
        raise RuntimeError("G51 readiness reload mutated the train artifact")
    return {
        "artifact_reload": True,
        "source_commit": training["source_commit"],
        "train_manifest_sha256": before,
        "additional_optimizer_steps": 0,
        "additional_environment_transitions": 0,
        "passed": True,
    }


def readiness_evaluate(*, run_root: Path) -> dict[str, object]:
    readiness_reload(run_root=run_root)
    return evaluate(run_root=run_root)


def readiness_analyze(*, run_root: Path) -> dict[str, object]:
    return analyze(run_root=run_root)


def exercise(*, run_root: Path, source_commit: str) -> dict[str, object]:
    train(
        run_root=run_root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
    )
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def _reject_cli_formal_authority(args: argparse.Namespace) -> None:
    if args.formal or any(
        getattr(args, name) is not None
        for name in (
            "authorization_token",
            "preflight_root",
            "alignment_disposition",
            "aligned_source_commit",
            "alignment_stage_commit",
        )
    ):
        raise ValueError(
            "G51 proof-only CLI forbids formal execution or admission fields"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage",
        choices=(
            "train",
            "evaluate",
            "analyze",
            "exercise",
            "readiness-smoke",
            "readiness-train",
            "readiness-validate",
            "readiness-reload",
            "readiness-evaluate",
            "readiness-analyze",
        ),
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--alignment-disposition")
    parser.add_argument("--aligned-source-commit")
    parser.add_argument("--alignment-stage-commit")
    parser.add_argument("--cpu-budget", type=int)
    parser.add_argument("--process-workers", type=int)
    args = parser.parse_args()
    _reject_cli_formal_authority(args)
    if args.stage in {
        "train",
        "exercise",
        "readiness-smoke",
        "readiness-train",
    } and args.source_commit is None:
        raise ValueError("G51 entry requires source commit")
    if args.stage == "readiness-smoke":
        readiness_interface_smoke(source_commit=args.source_commit)
    elif args.stage == "readiness-train":
        readiness_train(run_root=args.run_root, source_commit=args.source_commit)
    elif args.stage == "readiness-validate":
        readiness_validate(run_root=args.run_root)
    elif args.stage == "readiness-reload":
        readiness_reload(run_root=args.run_root)
    elif args.stage == "readiness-evaluate":
        readiness_evaluate(run_root=args.run_root)
    elif args.stage == "readiness-analyze":
        readiness_analyze(run_root=args.run_root)
    elif args.stage == "train":
        train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            preflight_root=args.preflight_root,
            alignment_disposition=args.alignment_disposition,
            aligned_source_commit=args.aligned_source_commit,
            alignment_stage_commit=args.alignment_stage_commit,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )
    elif args.stage == "evaluate":
        evaluate(run_root=args.run_root)
    elif args.stage == "analyze":
        analyze(run_root=args.run_root)
    else:
        exercise(run_root=args.run_root, source_commit=args.source_commit)


if __name__ == "__main__":
    main()
