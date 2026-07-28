"""Exact baseline-shadow norm schedule versus raw-norm G31 attribution."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

from ha_ctse_process import (
    continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45
    as g45,
)
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory


g40 = g45.g40
g41 = g45.g41
g43 = g45.g43
g44 = g45.g44

ALGORITHM_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_"
    "ATTRIBUTION_G46"
)
SOURCE_ID = f"{ALGORITHM_ID}_P0"
ACCEPTED_G40_SOURCE_COMMIT = g45.ACCEPTED_G40_SOURCE_COMMIT
ACCEPTED_G41_SOURCE_COMMIT = g45.ACCEPTED_G41_SOURCE_COMMIT
ACCEPTED_G45_FORMAL_SOURCE_COMMIT = (
    "d2502f4d1732601aa1249a1df7627690d51a9954"
)
ACCEPTED_G45_ALIGNED_IMPLEMENTATION_COMMIT = (
    "a42da997712d9c941ac9a6ca08992f4c5de033a2"
)
ACCEPTED_G45_ALIGNMENT_STAGE_COMMIT = (
    "40840069c4cfe0baad67e2800d13bbee872844b0"
)

SHADOW_NORM_ARM = "NATIVE6_G31_NO_READ_BASELINE_SHADOW_NORM"
RAW_NORM_ARM = "NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM"
ARMS = (SHADOW_NORM_ARM, RAW_NORM_ARM)

# Names consumed by the accepted isolated G43/G44/G45 orchestration layers.
DBNORM_ARM = SHADOW_NORM_ARM
MEAN_ARM = RAW_NORM_ARM
INDEPENDENT_ARM = SHADOW_NORM_ARM
POOLED_ARM = RAW_NORM_ARM
BASELINE_READ_ARM = SHADOW_NORM_ARM
BASELINE_SHADOW_NO_READ_ARM = RAW_NORM_ARM

ACCEPTED_G40_ANCHOR_REPLICATES = g45.ACCEPTED_G40_ANCHOR_REPLICATES
PPO_PASSES = g45.PPO_PASSES
NUM_ENVS = g45.NUM_ENVS
HORIZON = g45.HORIZON
MAX_CONFORMANCE_TRANSITIONS = g45.MAX_CONFORMANCE_TRANSITIONS
NORMALIZATION_ROWS = g45.NORMALIZATION_ROWS
NORMALIZATION_MASK_DIGEST = g45.NORMALIZATION_MASK_DIGEST
GRADIENT_LIVE_TOLERANCE = g45.GRADIENT_LIVE_TOLERANCE
EQUAL_MEAN_COEFFICIENT = g45.EQUAL_MEAN_COEFFICIENT
SCALE_MATCH_ATOL = 1e-8
SCALE_MATCH_RTOL = 1e-6
ACTIVATION_TOLERANCE = 1e-6
DIRECTION_TOLERANCE = 1e-6
TARGET_ONLY_RESIDUAL_LAW = "r|Gnext"

BASELINE_PARAMETER_NAMES = g45.BASELINE_PARAMETER_NAMES
BASELINE_GRADIENT_GROUP_RECONSTRUCTION = (
    g45.BASELINE_GRADIENT_GROUP_RECONSTRUCTION
)


class G46GradientGateError(ValueError):
    """A frozen G46 gate failed before either arm optimizer step."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object]) -> None:
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics)
        super().__init__(f"G46 gradient gate failed before optimizer step: {reason}")

    def __reduce__(
        self,
    ) -> tuple[type[G46GradientGateError], tuple[str, dict[str, object]]]:
        return type(self), (self.reason, dict(self.diagnostics))

    def to_record(self) -> dict[str, object]:
        return {
            "passed": False,
            "stage": "before_either_arm_optimizer_step",
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
        }


# The isolated G45 runner catches this compatibility name at its private boundary.
G45GradientGateError = G46GradientGateError


@dataclass(frozen=True)
class _PassPlan:
    policy: torch.Tensor
    immediate_baseline_loss: torch.Tensor
    successor_baseline_loss: torch.Tensor
    gradients: tuple[torch.Tensor, ...]
    gradient_evidence: dict[str, object]
    composition_record: dict[str, object]


def _translate_error(error: g45.G45GradientGateError) -> G46GradientGateError:
    return G46GradientGateError(error.reason, error.diagnostics)


def _gradient_rows(
    rows: Sequence[torch.Tensor | None], parameters: Sequence[nn.Parameter]
) -> tuple[torch.Tensor, ...]:
    try:
        return g45._gradient_rows(rows, parameters)
    except g45.G45GradientGateError as error:
        raise _translate_error(error) from error


def _global_norm(rows: Sequence[torch.Tensor]) -> float:
    return g45._global_norm(rows)


def _rows_bitwise_equal(
    left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]
) -> bool:
    return g45._rows_bitwise_equal(left, right)


validate_baseline_gradient_group_evidence = (
    g45.validate_baseline_gradient_group_evidence
)
baseline_gradient_group_evidence = g45.baseline_gradient_group_evidence
registered_gradient_evidence = g45.registered_gradient_evidence
validate_registered_gradient_evidence = g45.validate_registered_gradient_evidence
_tensor_digest = g45._tensor_digest
_sequence_digest = g45._sequence_digest
_episode_ids = g45._episode_ids
_read_credit = g45._read_credit
_no_read_credit = g45._no_read_credit
_normalize_credit = g45._normalize_credit
_equal_mean = g45._equal_mean
_add_entropy = g45._add_entropy
_optimizer_step_value = g45._optimizer_step_value


def _optimizer_owns_actor_head(
    optimizer: torch.optim.Optimizer, model: g41.G41NoSlowProjection
) -> bool:
    """Expose the accepted optimizer inventory gate to private orchestration."""

    return g45._optimizer_owns_actor_head(optimizer, model)


def _gradient_probe(
    model: g41.G41NoSlowProjection,
    replay: g41.G41RetainedReplay,
    trajectory: AnchoredRosterTrajectory,
    credit: g41.G41Credit,
    normalized_advantages: tuple[torch.Tensor, torch.Tensor],
) -> g45._GradientProbe:
    try:
        return g45._gradient_probe(
            model, replay, trajectory, credit, normalized_advantages
        )
    except g45.G45GradientGateError as error:
        raise _translate_error(error) from error


def _arm_credit_evidence(
    arm: str,
    trajectory: AnchoredRosterTrajectory,
    credit: g41.G41Credit,
    normalization: g44.ChannelNormalization,
) -> dict[str, object]:
    if arm not in ARMS:
        raise ValueError("G46 residual evidence arm is not registered")
    return {
        "arm": arm,
        "residual_law_id": TARGET_ONLY_RESIDUAL_LAW,
        "channels": {
            "immediate": g45._channel_evidence(
                residual_law_id="r",
                residual=credit.immediate_advantage,
                normalized=normalization.independent_immediate,
                mean=normalization.immediate_mean,
                centered_sum_square=normalization.immediate_centered_sum_square,
                scale=normalization.immediate_scale,
            ),
            "successor": g45._channel_evidence(
                residual_law_id="Gnext",
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
        "actual_residual_baseline_read_count": 0,
        "actual_direction_baseline_coordinate_read_count": 0,
        "passed": True,
    }


def validate_arm_credit_evidence(value: object, arm: str) -> bool:
    if not isinstance(value, Mapping) or arm not in ARMS:
        return False
    channels = value.get("channels")
    if (
        value.get("passed") is not True
        or value.get("arm") != arm
        or value.get("residual_law_id") != TARGET_ONLY_RESIDUAL_LAW
        or not isinstance(channels, Mapping)
        or tuple(channels) != ("immediate", "successor")
        or value.get("primitive_row_count") != NORMALIZATION_ROWS
        or value.get("primitive_row_mask_digest") != NORMALIZATION_MASK_DIGEST
        or value.get("baseline_predictions_frozen_across_both_passes") is not True
        or value.get("normalization_count") != 1
        or value.get("normalization_recomputed_between_passes") is not False
        or value.get("actual_residual_baseline_read_count") != 0
        or value.get("actual_direction_baseline_coordinate_read_count") != 0
    ):
        return False
    for name, law in (("immediate", "r"), ("successor", "Gnext")):
        row = channels.get(name)
        if not isinstance(row, Mapping) or row.get("residual_law_id") != law:
            return False
        for field in ("residual_mean", "centered_sum_square", "RMS_scale"):
            number = row.get(field)
            if (
                isinstance(number, bool)
                or not isinstance(number, (int, float))
                or not np.isfinite(float(number))
                or (field != "residual_mean" and float(number) < 0.0)
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
    return all(
        isinstance(value.get(field), str) and len(str(value[field])) == 64
        for field in (
            "episode_id_digest",
            "true_current_state_input_digest",
            "immediate_target_digest",
            "successor_target_digest",
            "immediate_baseline_output_digest",
            "successor_baseline_output_digest",
        )
    )


def project_g46_arms(
    anchor: g40.G40NativeSixPolicy, *, accepted_anchor_replicate: int
) -> dict[str, g41.G41NoSlowProjection]:
    rng_before = torch.random.get_rng_state().clone()
    inherited = g45.project_g45_arms(
        anchor, accepted_anchor_replicate=accepted_anchor_replicate
    )
    models = {
        SHADOW_NORM_ARM: inherited[g45.BASELINE_READ_ARM],
        RAW_NORM_ARM: inherited[g45.BASELINE_SHADOW_NO_READ_ARM],
    }
    if g40.state_bytes(models[SHADOW_NORM_ARM]) != g40.state_bytes(
        models[RAW_NORM_ARM]
    ):
        raise RuntimeError("G46 branch states differ before treatment")
    if g40.shared_tensor_storage_count((anchor, *models.values())) != 0:
        raise RuntimeError("G46 projection shares retained storage")
    if any(hasattr(model, "slow_critic") for model in models.values()):
        raise RuntimeError("G46 reintroduced the standalone slow critic")
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise RuntimeError("G46 projection advanced model RNG")
    return models


# Names consumed by the accepted isolated orchestration backend.
project_g43_arms = project_g46_arms
project_g44_arms = project_g46_arms
project_g45_arms = project_g46_arms


def branch_boundary_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS:
        return {"passed": False, "inventory_valid": False}
    inherited = g45.branch_boundary_audit(
        {
            g45.BASELINE_READ_ARM: models[SHADOW_NORM_ARM],
            g45.BASELINE_SHADOW_NO_READ_ARM: models[RAW_NORM_ARM],
        },
        {
            g45.BASELINE_READ_ARM: optimizers[SHADOW_NORM_ARM],
            g45.BASELINE_SHADOW_NO_READ_ARM: optimizers[RAW_NORM_ARM],
        },
    )
    states_equal = g40.state_bytes(models[SHADOW_NORM_ARM]) == g40.state_bytes(
        models[RAW_NORM_ARM]
    )
    storage_disjoint = g40.shared_tensor_storage_count(tuple(models.values())) == 0
    optimizer_separate = bool(
        all(optimizer.state == {} for optimizer in optimizers.values())
        and id(optimizers[SHADOW_NORM_ARM].state)
        != id(optimizers[RAW_NORM_ARM].state)
    )
    provenance = bool(
        ACCEPTED_G40_SOURCE_COMMIT == g45.ACCEPTED_G40_SOURCE_COMMIT
        and ACCEPTED_G41_SOURCE_COMMIT == g45.ACCEPTED_G41_SOURCE_COMMIT
        and len(ACCEPTED_G45_FORMAL_SOURCE_COMMIT) == 40
        and len(ACCEPTED_G45_ALIGNED_IMPLEMENTATION_COMMIT) == 40
        and len(ACCEPTED_G45_ALIGNMENT_STAGE_COMMIT) == 40
    )
    return {
        **inherited,
        "arms": list(ARMS),
        "accepted_g45_formal_source_commit": ACCEPTED_G45_FORMAL_SOURCE_COMMIT,
        "accepted_g45_aligned_implementation_commit": (
            ACCEPTED_G45_ALIGNED_IMPLEMENTATION_COMMIT
        ),
        "accepted_g45_alignment_stage_commit": (
            ACCEPTED_G45_ALIGNMENT_STAGE_COMMIT
        ),
        "model_state_bytes_equal": states_equal,
        "optimizer_states_empty_and_separate": optimizer_separate,
        "shared_parameter_buffer_gradient_optimizer_storage_count": (
            0 if storage_disjoint and optimizer_separate else 1
        ),
        "provenance_valid": provenance,
        "passed": bool(
            inherited.get("passed") is True
            and states_equal
            and storage_disjoint
            and optimizer_separate
            and provenance
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
    return {
        "inventory_valid": inventory,
        "continuation": True,
        "update_index": update_index,
        "accepted_g40_anchor_authority": (
            g41.accepted_g40_anchor_identity(
                models[SHADOW_NORM_ARM].accepted_g40_anchor_authority.replicate
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


def corrected_q_norm(baseline_norm: float, raw_norm: float) -> float:
    values = (baseline_norm, raw_norm)
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(float(value))
        or float(value) < 0.0
        for value in values
    ):
        raise G46GradientGateError(
            "q_norm_nonfinite_or_negative",
            {"baseline_norm": baseline_norm, "raw_norm": raw_norm},
        )
    baseline = float(baseline_norm)
    raw = float(raw_norm)
    if baseline == 0.0 and raw == 0.0:
        return 0.0
    if baseline == raw:
        return 0.0
    if baseline == 0.0:
        return 1.0
    if raw == 0.0:
        raise G46GradientGateError(
            "positive_baseline_norm_with_zero_raw_direction",
            {"baseline_norm": baseline},
        )
    return abs(baseline - raw) / max(baseline, raw)


def _unit_direction_record(
    reference: Sequence[torch.Tensor], raw: Sequence[torch.Tensor]
) -> dict[str, object]:
    if not reference or len(reference) != len(raw):
        raise G46GradientGateError("unit_direction_inventory_mismatch", {})
    reference_flat = torch.cat(
        [row.detach().to(torch.float64).reshape(-1) for row in reference]
    )
    raw_flat = torch.cat(
        [row.detach().to(torch.float64).reshape(-1) for row in raw]
    )
    if not bool(torch.isfinite(reference_flat).all()) or not bool(
        torch.isfinite(raw_flat).all()
    ):
        raise G46GradientGateError("unit_direction_nonfinite_coordinate", {})
    # Reuse the registered float64 global-norm reduction for both the schedule
    # and direction certificate.  A second flatten-and-reduce implementation
    # can differ by one ULP and would make an otherwise identical record fail
    # its exact reconstruction gate.
    reference_norm = _global_norm(reference)
    raw_norm = _global_norm(raw)
    if not np.isfinite(reference_norm) or not np.isfinite(raw_norm):
        raise G46GradientGateError("unit_direction_nonfinite_norm", {})
    if reference_norm == 0.0 or raw_norm == 0.0:
        return {
            "direction_rule_evaluated": False,
            "reference_assigned_credit_norm": reference_norm,
            "raw_assigned_credit_norm": raw_norm,
            "reference_raw_unit_dot_product": None,
            "unit_direction_delta_sum_square": None,
            "unit_direction_distance": None,
            "direction_tolerance": DIRECTION_TOLERANCE,
            "passed": True,
        }
    reference_unit = reference_flat / reference_norm
    raw_unit = raw_flat / raw_norm
    delta_square = float((reference_unit - raw_unit).square().sum())
    distance = float(
        torch.sqrt(torch.as_tensor(delta_square, dtype=torch.float64))
    )
    dot = float((reference_unit * raw_unit).sum())
    if any(not np.isfinite(value) for value in (delta_square, distance, dot)):
        raise G46GradientGateError("unit_direction_nonfinite_normalized_row", {})
    if distance > DIRECTION_TOLERANCE:
        raise G46GradientGateError(
            "unit_direction_mismatch",
            {"distance": distance, "tolerance": DIRECTION_TOLERANCE},
        )
    return {
        "direction_rule_evaluated": True,
        "reference_assigned_credit_norm": reference_norm,
        "raw_assigned_credit_norm": raw_norm,
        "reference_raw_unit_dot_product": dot,
        "unit_direction_delta_sum_square": delta_square,
        "unit_direction_distance": distance,
        "direction_tolerance": DIRECTION_TOLERANCE,
        "passed": True,
    }


def _reference_schedule(
    raw: Sequence[torch.Tensor],
    parameters: Sequence[nn.Parameter],
    *,
    baseline_counterfactual_norm: float,
) -> tuple[tuple[torch.Tensor, ...], dict[str, object]]:
    rows = _gradient_rows(raw, parameters)
    raw_norm = _global_norm(rows)
    if any(
        not np.isfinite(value) or value < 0.0
        for value in (raw_norm, baseline_counterfactual_norm)
    ):
        raise G46GradientGateError(
            "reference_schedule_nonfinite_or_negative",
            {
                "raw_norm": raw_norm,
                "baseline_counterfactual_norm": baseline_counterfactual_norm,
            },
        )
    if baseline_counterfactual_norm == 0.0:
        assigned = tuple(torch.zeros_like(parameter) for parameter in parameters)
        scale = 0.0
    elif raw_norm == 0.0:
        raise G46GradientGateError(
            "positive_baseline_norm_with_zero_reference_raw_direction",
            {"baseline_counterfactual_norm": baseline_counterfactual_norm},
        )
    else:
        scale = baseline_counterfactual_norm / raw_norm
        assigned = tuple(
            (row.to(torch.float64) * scale).to(parameter.dtype)
            for row, parameter in zip(rows, parameters)
        )
    assigned_norm = _global_norm(assigned)
    error = abs(assigned_norm - baseline_counterfactual_norm)
    tolerance = SCALE_MATCH_ATOL + SCALE_MATCH_RTOL * abs(
        baseline_counterfactual_norm
    )
    if error > tolerance:
        raise G46GradientGateError(
            "reference_schedule_norm_match_failed",
            {
                "assigned_norm": assigned_norm,
                "baseline_counterfactual_norm": baseline_counterfactual_norm,
                "error": error,
                "tolerance": tolerance,
            },
        )
    return assigned, {
        "raw_credit_norm": raw_norm,
        "baseline_read_counterfactual_credit_norm": baseline_counterfactual_norm,
        "assigned_credit_norm": assigned_norm,
        "scale": scale,
        "assigned_norm_match_error": error,
        "assigned_norm_match_tolerance": tolerance,
        "actual_residual_baseline_read_count": 0,
        "actual_direction_baseline_coordinate_read_count": 0,
        "baseline_read_into_actual_scalar_norm": 1,
        "baseline_counterfactual_calls": 1,
        "counterfactual_baseline_scalar_shadow": True,
        "counterfactual_shadow_output_type": "one_detached_scalar_credit_norm",
        "counterfactual_vector_serialized": False,
        "counterfactual_vector_coordinate_use_outside_norm": 0,
        "counterfactual_gradient_assignment_count": 0,
        "counterfactual_optimizer_state_count": 0,
        "counterfactual_RNG_consumption": 0,
        "counterfactual_model_mutation_count": 0,
        "baseline_target_fitting_retained": True,
        "actor_credit_gradients_exact_zero": all(
            bool(torch.count_nonzero(row) == 0) for row in assigned
        ),
        "passed": True,
    }


def _raw_schedule(
    raw: Sequence[torch.Tensor], parameters: Sequence[nn.Parameter]
) -> tuple[tuple[torch.Tensor, ...], dict[str, object]]:
    rows = _gradient_rows(raw, parameters)
    raw_norm = _global_norm(rows)
    if not np.isfinite(raw_norm) or raw_norm < 0.0:
        raise G46GradientGateError("raw_schedule_nonfinite_or_negative", {})
    return rows, {
        "raw_credit_norm": raw_norm,
        "assigned_credit_norm": raw_norm,
        "literal_raw_equal_mean_credit_gradient": True,
        "actual_residual_baseline_read_count": 0,
        "actual_direction_baseline_coordinate_read_count": 0,
        "baseline_read_into_actual_scalar_norm": 0,
        "baseline_counterfactual_calls": 0,
        "learned_or_tunable_scale": 0,
        "baseline_target_fitting_retained": True,
        "actor_credit_gradients_exact_zero": all(
            bool(torch.count_nonzero(row) == 0) for row in rows
        ),
        "passed": True,
    }


def _activation_record(
    reference_assigned: Sequence[torch.Tensor],
    reference_raw_counterfactual: Sequence[torch.Tensor],
    *,
    baseline_counterfactual_norm: float,
) -> dict[str, object]:
    raw_norm = _global_norm(reference_raw_counterfactual)
    q_norm = corrected_q_norm(baseline_counterfactual_norm, raw_norm)
    direction = _unit_direction_record(
        reference_assigned, reference_raw_counterfactual
    )
    active = bool(q_norm > ACTIVATION_TOLERANCE)
    record = {
        "baseline_read_counterfactual_credit_norm": float(
            baseline_counterfactual_norm
        ),
        "raw_equal_mean_credit_norm": raw_norm,
        "q_norm": q_norm,
        "activation_threshold": ACTIVATION_TOLERANCE,
        "strict_treatment_activation_observed": active,
        "evidence_source_arms": list(ARMS),
        "direction_evidence_source_arm": SHADOW_NORM_ARM,
        "reference_local_raw_counterfactual": True,
        "raw_arm_gradient_read_count": 0,
        "reference_baseline_counterfactual_calls": 1,
        "raw_arm_baseline_counterfactual_calls": 0,
        "q_norm_reconstructed_not_caller_flag": True,
        **direction,
        "passed": True,
    }
    if not validate_activation_record(record):
        raise G46GradientGateError("activation_record_invalid", record)
    return record


def validate_activation_record(value: object) -> bool:
    if not isinstance(value, Mapping) or value.get("passed") is not True:
        return False
    baseline = value.get("baseline_read_counterfactual_credit_norm")
    raw = value.get("raw_equal_mean_credit_norm")
    try:
        expected_q = corrected_q_norm(baseline, raw)  # type: ignore[arg-type]
    except G46GradientGateError:
        return False
    if (
        value.get("q_norm") != expected_q
        or value.get("activation_threshold") != ACTIVATION_TOLERANCE
        or value.get("strict_treatment_activation_observed")
        is not (expected_q > ACTIVATION_TOLERANCE)
        or value.get("evidence_source_arms") != list(ARMS)
        or value.get("direction_evidence_source_arm") != SHADOW_NORM_ARM
        or value.get("reference_local_raw_counterfactual") is not True
        or value.get("raw_arm_gradient_read_count") != 0
        or value.get("reference_baseline_counterfactual_calls") != 1
        or value.get("raw_arm_baseline_counterfactual_calls") != 0
        or value.get("q_norm_reconstructed_not_caller_flag") is not True
        or value.get("direction_tolerance") != DIRECTION_TOLERANCE
    ):
        return False
    reference_norm = value.get("reference_assigned_credit_norm")
    raw_assigned_norm = value.get("raw_assigned_credit_norm")
    if any(
        isinstance(number, bool)
        or not isinstance(number, (int, float))
        or not np.isfinite(float(number))
        or float(number) < 0.0
        for number in (reference_norm, raw_assigned_norm)
    ):
        return False
    tolerance = SCALE_MATCH_ATOL + SCALE_MATCH_RTOL * abs(float(baseline))
    if abs(float(reference_norm) - float(baseline)) > tolerance:
        return False
    if float(raw_assigned_norm) != float(raw):
        return False
    evaluated = float(reference_norm) > 0.0 and float(raw_assigned_norm) > 0.0
    if value.get("direction_rule_evaluated") is not evaluated:
        return False
    if not evaluated:
        return all(
            value.get(field) is None
            for field in (
                "reference_raw_unit_dot_product",
                "unit_direction_delta_sum_square",
                "unit_direction_distance",
            )
        )
    delta_square = value.get("unit_direction_delta_sum_square")
    distance = value.get("unit_direction_distance")
    dot = value.get("reference_raw_unit_dot_product")
    if any(
        isinstance(number, bool)
        or not isinstance(number, (int, float))
        or not np.isfinite(float(number))
        for number in (delta_square, distance, dot)
    ):
        return False
    expected_distance = float(
        torch.sqrt(torch.as_tensor(float(delta_square), dtype=torch.float64))
    )
    return bool(
        float(delta_square) >= 0.0
        and float(distance) == expected_distance
        and float(distance) <= DIRECTION_TOLERANCE
        and -1.0 - 1e-12 <= float(dot) <= 1.0 + 1e-12
    )


def _direct_treatment_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    credits: Mapping[str, g41.G41Credit],
    probes: Mapping[str, g45._GradientProbe],
    residual_evidence: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    left = models[SHADOW_NORM_ARM]
    right = models[RAW_NORM_ARM]
    trajectory = g40.branch_trajectory_match(
        trajectories[SHADOW_NORM_ARM], trajectories[RAW_NORM_ARM]
    )
    credit_equal = all(
        torch.equal(
            getattr(credits[SHADOW_NORM_ARM], name),
            getattr(credits[RAW_NORM_ARM], name),
        )
        for name in (
            "returns",
            "successor_targets",
            "immediate_advantage",
            "successor_advantage",
        )
    )
    gradient_equal = all(
        _rows_bitwise_equal(
            getattr(probes[SHADOW_NORM_ARM], name),
            getattr(probes[RAW_NORM_ARM], name),
        )
        for name in (
            "immediate_credit_gradients",
            "successor_credit_gradients",
            "entropy_gradients",
            "immediate_baseline_gradients",
            "successor_baseline_gradients",
        )
    )
    losses_equal = bool(
        torch.equal(
            probes[SHADOW_NORM_ARM].immediate_baseline_loss,
            probes[RAW_NORM_ARM].immediate_baseline_loss,
        )
        and torch.equal(
            probes[SHADOW_NORM_ARM].successor_baseline_loss,
            probes[RAW_NORM_ARM].successor_baseline_loss,
        )
    )
    residual_equal = all(
        residual_evidence[SHADOW_NORM_ARM][name]
        == residual_evidence[RAW_NORM_ARM][name]
        for name in (
            "residual_law_id",
            "channels",
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
    passed = bool(
        trajectory["passed"] is True
        and g40.state_bytes(left.policy) == g40.state_bytes(right.policy)
        and torch.equal(left.log_std, right.log_std)
        and g40.state_bytes(left.credit_baselines)
        == g40.state_bytes(right.credit_baselines)
        and credit_equal
        and gradient_equal
        and losses_equal
        and residual_equal
        and all(optimizer.state == {} for optimizer in optimizers.values())
    )
    return {
        "trajectory_bitwise_equal": trajectory["passed"],
        "actor_bytes_equal": g40.state_bytes(left.policy)
        == g40.state_bytes(right.policy),
        "log_std_bitwise_equal": torch.equal(left.log_std, right.log_std),
        "shared_baseline_bytes_equal": g40.state_bytes(left.credit_baselines)
        == g40.state_bytes(right.credit_baselines),
        "target_only_credit_bitwise_equal": credit_equal,
        "channel_entropy_baseline_gradients_bitwise_equal": gradient_equal,
        "baseline_losses_bitwise_equal": losses_equal,
        "target_only_residual_evidence_bitwise_equal": residual_equal,
        "only_permitted_difference_is_scalar_norm_schedule": True,
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
        and id(optimizers[SHADOW_NORM_ARM].state)
        != id(optimizers[RAW_NORM_ARM].state)
    )
    gradient_storage = bool(
        inventory
        and not {
            row.untyped_storage().data_ptr()
            for row in plans[SHADOW_NORM_ARM].gradients
        }.intersection(
            row.untyped_storage().data_ptr()
            for row in plans[RAW_NORM_ARM].gradients
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
        raise ValueError("G46 optimizer arm/type mismatch")
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
        raise G46GradientGateError("stale_or_missing_gradient", {"arm": arm})
    g40._optimizer_step(optimizer, all_parameters)
    after = tuple(
        _optimizer_step_value(optimizer, parameter) for parameter in all_parameters
    )
    if any(value != prior + 1.0 for prior, value in zip(before, after)):
        raise RuntimeError("G46 Adam exposure did not advance exactly once")
    return (
        float(plan.policy.detach()),
        float(plan.immediate_baseline_loss.detach()),
        float(plan.successor_baseline_loss.detach()),
    )


def _prepare_passes(
    models: Mapping[str, g41.G41NoSlowProjection],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    target_credits: Mapping[str, g41.G41Credit],
    target_normalizations: Mapping[str, g44.ChannelNormalization],
    reference_read_credit: g41.G41Credit,
    reference_read_normalization: g44.ChannelNormalization,
) -> tuple[
    dict[str, _PassPlan],
    dict[str, g45._GradientProbe],
    dict[str, object],
]:
    replays = {
        arm: g41.retained_replay(models[arm], trajectories[arm]) for arm in ARMS
    }
    actual_probes = {
        arm: _gradient_probe(
            models[arm],
            replays[arm],
            trajectories[arm],
            target_credits[arm],
            (
                target_normalizations[arm].independent_immediate,
                target_normalizations[arm].independent_successor,
            ),
        )
        for arm in ARMS
    }
    reference_counterfactual = _gradient_probe(
        models[SHADOW_NORM_ARM],
        replays[SHADOW_NORM_ARM],
        trajectories[SHADOW_NORM_ARM],
        reference_read_credit,
        (
            reference_read_normalization.independent_immediate,
            reference_read_normalization.independent_successor,
        ),
    )
    reference_actual = actual_probes[SHADOW_NORM_ARM]
    if not (
        _rows_bitwise_equal(
            reference_actual.entropy_gradients,
            reference_counterfactual.entropy_gradients,
        )
        and torch.equal(
            reference_actual.immediate_baseline_loss,
            reference_counterfactual.immediate_baseline_loss,
        )
        and torch.equal(
            reference_actual.successor_baseline_loss,
            reference_counterfactual.successor_baseline_loss,
        )
        and _rows_bitwise_equal(
            reference_actual.immediate_baseline_gradients,
            reference_counterfactual.immediate_baseline_gradients,
        )
        and _rows_bitwise_equal(
            reference_actual.successor_baseline_gradients,
            reference_counterfactual.successor_baseline_gradients,
        )
    ):
        raise G46GradientGateError(
            "counterfactual_changed_entropy_or_baseline_terms", {}
        )
    reference_raw = _equal_mean(
        reference_actual.immediate_credit_gradients,
        reference_actual.successor_credit_gradients,
        models[SHADOW_NORM_ARM].full_actor_parameters(),
    )
    reference_counterfactual_vector = _equal_mean(
        reference_counterfactual.immediate_credit_gradients,
        reference_counterfactual.successor_credit_gradients,
        models[SHADOW_NORM_ARM].full_actor_parameters(),
    )
    raw_arm_credit, raw_certificate = _raw_schedule(
        _equal_mean(
            actual_probes[RAW_NORM_ARM].immediate_credit_gradients,
            actual_probes[RAW_NORM_ARM].successor_credit_gradients,
            models[RAW_NORM_ARM].full_actor_parameters(),
        ),
        models[RAW_NORM_ARM].full_actor_parameters(),
    )
    baseline_norm = _global_norm(reference_counterfactual_vector)
    reference_credit, reference_certificate = _reference_schedule(
        reference_raw,
        models[SHADOW_NORM_ARM].full_actor_parameters(),
        baseline_counterfactual_norm=baseline_norm,
    )
    activation = _activation_record(
        reference_credit,
        reference_raw,
        baseline_counterfactual_norm=baseline_norm,
    )
    reference_with_entropy = _add_entropy(
        reference_credit, reference_actual.entropy_gradients
    )
    raw_with_entropy = _add_entropy(
        raw_arm_credit, actual_probes[RAW_NORM_ARM].entropy_gradients
    )
    plans = {
        SHADOW_NORM_ARM: _PassPlan(
            policy=reference_actual.policy,
            immediate_baseline_loss=reference_actual.immediate_baseline_loss,
            successor_baseline_loss=reference_actual.successor_baseline_loss,
            gradients=reference_with_entropy,
            gradient_evidence=reference_actual.gradient_evidence,
            composition_record={
                "mode": "target_only_baseline_shadow_norm_matched",
                "literal_coefficient": EQUAL_MEAN_COEFFICIENT,
                "residual_law_id": TARGET_ONLY_RESIDUAL_LAW,
                **reference_certificate,
                "entropy_gradient_norm": _global_norm(
                    reference_actual.entropy_gradients
                ),
                "assigned_actor_gradient_norm": _global_norm(
                    reference_with_entropy
                ),
                "entropy_added_after_credit_gate": True,
            },
        ),
        RAW_NORM_ARM: _PassPlan(
            policy=actual_probes[RAW_NORM_ARM].policy,
            immediate_baseline_loss=actual_probes[
                RAW_NORM_ARM
            ].immediate_baseline_loss,
            successor_baseline_loss=actual_probes[
                RAW_NORM_ARM
            ].successor_baseline_loss,
            gradients=raw_with_entropy,
            gradient_evidence=actual_probes[RAW_NORM_ARM].gradient_evidence,
            composition_record={
                "mode": "target_only_literal_raw_equal_mean_norm",
                "literal_coefficient": EQUAL_MEAN_COEFFICIENT,
                "residual_law_id": TARGET_ONLY_RESIDUAL_LAW,
                **raw_certificate,
                "entropy_gradient_norm": _global_norm(
                    actual_probes[RAW_NORM_ARM].entropy_gradients
                ),
                "assigned_actor_gradient_norm": _global_norm(raw_with_entropy),
                "entropy_added_after_credit_gate": True,
            },
        ),
    }
    return plans, actual_probes, activation


def _canonical_residual_evidence(
    value: Mapping[str, object],
) -> dict[str, object]:
    if set(value) != set(ARMS) or any(
        not validate_arm_credit_evidence(value.get(arm), arm) for arm in ARMS
    ):
        raise ValueError("G46 per-arm residual evidence invalid")
    decoded = json.loads(json.dumps(value, sort_keys=True))
    return {arm: decoded[arm] for arm in ARMS}


def optimize_baseline_shadow_norm_update(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory] | AnchoredRosterTrajectory,
    *,
    update_index: int = 0,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, object]:
    if int(ppo_passes) != PPO_PASSES:
        raise ValueError("G46 requires exactly two PPO passes")
    if (
        isinstance(update_index, bool)
        or not isinstance(update_index, int)
        or update_index < 0
    ):
        raise ValueError("G46 update index must be a nonnegative integer")
    trajectory_map = (
        {arm: trajectories for arm in ARMS}
        if isinstance(trajectories, AnchoredRosterTrajectory)
        else dict(trajectories)
    )
    if tuple(trajectory_map) != ARMS or any(
        trajectory.rewards.numel() != MAX_CONFORMANCE_TRANSITIONS
        for trajectory in trajectory_map.values()
    ):
        raise ValueError("G46 update requires paired 8x48 real trajectories")
    boundary = _continuation_audit(models, optimizers, update_index=update_index)
    if boundary.get("passed") is not True:
        raise ValueError("G46 branch boundary failed before optimizer step")

    target_credits = {
        arm: _no_read_credit(trajectory_map[arm]) for arm in ARMS
    }
    target_normalizations = {
        arm: _normalize_credit(target_credits[arm]) for arm in ARMS
    }
    reference_read_credit = _read_credit(trajectory_map[SHADOW_NORM_ARM])
    reference_read_normalization = _normalize_credit(reference_read_credit)
    residual_evidence = {
        arm: _arm_credit_evidence(
            arm,
            trajectory_map[arm],
            target_credits[arm],
            target_normalizations[arm],
        )
        for arm in ARMS
    }
    canonical_residuals = _canonical_residual_evidence(residual_evidence)
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
        plans, probes, activation = _prepare_passes(
            models,
            trajectory_map,
            target_credits,
            target_normalizations,
            reference_read_credit,
            reference_read_normalization,
        )
        if update_index == 0 and pass_index == 0:
            direct_audit = _direct_treatment_audit(
                models,
                optimizers,
                trajectory_map,
                target_credits,
                probes,
                residual_evidence,
            )
            if direct_audit.get("passed") is not True:
                raise G46GradientGateError(
                    "first_paired_direct_treatment_mismatch", direct_audit
                )
            swap_guard = order_swap_guard(models, optimizers, plans)
            if swap_guard.get("passed") is not True:
                raise G46GradientGateError("order_swap_guard_failed", swap_guard)
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
                    canonical_residuals
                ),
                "baseline_shadow_norm_activation": activation,
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
        "accepted_g45_formal_source_commit": ACCEPTED_G45_FORMAL_SOURCE_COMMIT,
        "accepted_g45_aligned_implementation_commit": (
            ACCEPTED_G45_ALIGNED_IMPLEMENTATION_COMMIT
        ),
        "accepted_g45_alignment_stage_commit": (
            ACCEPTED_G45_ALIGNMENT_STAGE_COMMIT
        ),
        "accepted_g40_anchor_replicate": models[
            SHADOW_NORM_ARM
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
            steps_after[SHADOW_NORM_ARM] == steps_after[RAW_NORM_ARM]
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
                pass_record["baseline_shadow_norm_activation"]  # type: ignore[index]
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
        raise RuntimeError("G46 serialized update evidence failed validation")
    return record


# Names consumed by accepted isolated orchestration and readiness helpers.
optimize_norm_schedule_update = optimize_baseline_shadow_norm_update
optimize_channel_scale_update = optimize_baseline_shadow_norm_update
optimize_baseline_conditioning_update = optimize_baseline_shadow_norm_update


def _valid_composition(value: object, arm: str) -> bool:
    if (
        not isinstance(value, Mapping)
        or value.get("passed") is not True
        or value.get("literal_coefficient") != EQUAL_MEAN_COEFFICIENT
        or value.get("residual_law_id") != TARGET_ONLY_RESIDUAL_LAW
        or value.get("entropy_added_after_credit_gate") is not True
        or value.get("baseline_target_fitting_retained") is not True
        or value.get("actual_residual_baseline_read_count") != 0
        or value.get("actual_direction_baseline_coordinate_read_count") != 0
    ):
        return False
    if arm == SHADOW_NORM_ARM:
        return bool(
            value.get("mode") == "target_only_baseline_shadow_norm_matched"
            and value.get("baseline_read_into_actual_scalar_norm") == 1
            and value.get("baseline_counterfactual_calls") == 1
            and value.get("counterfactual_baseline_scalar_shadow") is True
            and value.get("counterfactual_shadow_output_type")
            == "one_detached_scalar_credit_norm"
            and value.get("counterfactual_vector_serialized") is False
            and value.get("counterfactual_vector_coordinate_use_outside_norm") == 0
            and value.get("counterfactual_gradient_assignment_count") == 0
            and value.get("counterfactual_optimizer_state_count") == 0
            and value.get("counterfactual_RNG_consumption") == 0
            and value.get("counterfactual_model_mutation_count") == 0
            and "counterfactual_vector" not in value
            and float(value.get("assigned_norm_match_error", np.inf))
            <= float(value.get("assigned_norm_match_tolerance", -1.0))
        )
    return bool(
        arm == RAW_NORM_ARM
        and value.get("mode") == "target_only_literal_raw_equal_mean_norm"
        and value.get("literal_raw_equal_mean_credit_gradient") is True
        and value.get("baseline_read_into_actual_scalar_norm") == 0
        and value.get("baseline_counterfactual_calls") == 0
        and value.get("learned_or_tunable_scale") == 0
        and "counterfactual_vector" not in value
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
        activation = record.get("baseline_shadow_norm_activation")
        if (
            not isinstance(gradients, Mapping)
            or set(gradients) != set(ARMS)
            or any(
                not validate_registered_gradient_evidence(gradients.get(arm))
                for arm in ARMS
            )
            or not isinstance(compositions, Mapping)
            or set(compositions) != set(ARMS)
            or any(
                not _valid_composition(compositions.get(arm), arm) for arm in ARMS
            )
            or not isinstance(residuals, Mapping)
            or set(residuals) != set(ARMS)
            or any(
                not validate_arm_credit_evidence(residuals.get(arm), arm)
                for arm in ARMS
            )
            or not validate_activation_record(activation)
            or activation.get("baseline_read_counterfactual_credit_norm")
            != compositions[SHADOW_NORM_ARM].get(
                "baseline_read_counterfactual_credit_norm"
            )
            or activation.get("raw_equal_mean_credit_norm")
            != compositions[SHADOW_NORM_ARM].get("raw_credit_norm")
            or activation.get("reference_assigned_credit_norm")
            != compositions[SHADOW_NORM_ARM].get("assigned_credit_norm")
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
        raise ValueError("G46 pass gradient evidence invalid")
    groups = {
        arm: gradients[arm]["baseline_gradient_groups"]  # type: ignore[index]
        for arm in ARMS
    }
    if not validate_baseline_gradient_groups_by_arm(groups):
        raise ValueError("G46 per-arm baseline gradient evidence invalid")
    return json.loads(json.dumps(groups, sort_keys=True))


def build_conclusion_evidence(
    update_records: Sequence[Mapping[str, object]], *, formal: bool
) -> dict[str, object]:
    if not isinstance(formal, bool) or not update_records:
        raise ValueError("G46 conclusion evidence requires records and bool scope")
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
            activation = pass_record["baseline_shadow_norm_activation"]
            if not validate_activation_record(activation):
                records_valid = False
            rows_by_replicate[replicate].append(
                {
                    "residual_evidence_by_arm": _canonical_residual_evidence(
                        pass_record["residual_evidence_by_arm"]
                    ),
                    "baseline_gradient_groups_by_arm": (
                        _baseline_gradient_groups_from_pass(pass_record)
                    ),
                    "activation": json.loads(
                        json.dumps(activation, sort_keys=True)
                    ),
                    "active": bool(
                        activation["strict_treatment_activation_observed"]
                    ),
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
        "activation_predicate": "corrected_q_norm>1e-6_strict",
        "direction_tolerance": DIRECTION_TOLERANCE,
        "evidence_arms": list(ARMS),
        "q_norm_reconstructed_from_all_update_records": True,
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
        or value.get("direction_tolerance") != DIRECTION_TOLERANCE
        or value.get("evidence_arms") != list(ARMS)
        or value.get("q_norm_reconstructed_from_all_update_records") is not True
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
            if (
                not isinstance(residuals, Mapping)
                or set(residuals) != set(ARMS)
                or any(
                    not validate_arm_credit_evidence(residuals.get(arm), arm)
                    for arm in ARMS
                )
                or not validate_baseline_gradient_groups_by_arm(
                    item.get("baseline_gradient_groups_by_arm")
                )
                or not validate_activation_record(item.get("activation"))
            ):
                return False
            reconstructed_active = bool(
                item["activation"]["strict_treatment_activation_observed"]
            )
            if item.get("active") is not reconstructed_active:
                return False
            active |= reconstructed_active
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
        raise ValueError("G46 refuses to serialize invalid update evidence")
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
        raise ValueError("G46 final checkpoint arm is not registered")
    if not _update_evidence_valid(final_update_record):
        raise ValueError("G46 final checkpoint update evidence invalid")
    if not validate_conclusion_evidence(conclusion_evidence):
        raise ValueError("G46 final checkpoint activation evidence invalid")
    if conclusion_evidence.get("formal") is not formal:
        raise ValueError("G46 final checkpoint scope mismatch")
    state = {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }
    raw_certificate = final_update_record["pass_records"][-1]["composition"][  # type: ignore[index]
        RAW_NORM_ARM
    ]
    if not _valid_composition(raw_certificate, RAW_NORM_ARM):
        raise ValueError("G46 final checkpoint raw-norm certificate invalid")
    baseline_groups = _baseline_gradient_groups_from_pass(
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
        "accepted_g45_formal_source_commit": ACCEPTED_G45_FORMAL_SOURCE_COMMIT,
        "residual_evidence_arms": list(ARMS),
        "actor_head_optimizer_steps": PPO_PASSES,
        "standalone_slow_present": False,
        "standalone_slow_critic_present": False,
        "db_vector_present": False,
        "db_norm_present": False,
        "db_shadow_present": False,
        "baseline_checkpoint_selection_read_count": 0,
        "baseline_evaluation_metric_read_count": 0,
        "baseline_gradient_groups_by_arm": baseline_groups,
        "no_read_certificate": dict(raw_certificate),
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
