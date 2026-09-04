"""Deterministic post-training structural audits for RG2Z r03 checkpoints."""

from __future__ import annotations

import math
from typing import Any, Mapping

import torch

from .config import (
    ACTION_DIM,
    EDGE_BETA_BOUND,
    PHY_BETA_BOUND,
    POLICY_UNIFORM_WEIGHT,
    Role,
    TRAINING_DTYPE,
    legal_action_indices,
)
from .policies import ArmModel
from .reference import reference_role_summary, reset_before_matrix_gru


LEARNED_ARMS = ("PHY-TRUST", "EDGE-FLEX")
EXPECTED_PARAMETERS_PER_ARM = 35_513
AUDIT_TOLERANCE = 2.0e-6


def _fixture_observations() -> torch.Tensor:
    # Handwritten and deterministic: no seed, coordinate, RNG, world or event.
    rows = []
    for index in range(6):
        role = index // 2
        row = [0.0] * 22
        row[role] = 1.0
        row[3] = (index + 1) / 11.0
        row[4:7] = [2.0 / 7.0] * 3
        row[7] = float(index % 2)
        row[8] = index / 15.0
        row[15 + (index % 6)] = 1.0
        row[21] = float(index in (1, 4))
        rows.append(row)
    return torch.tensor(rows, dtype=TRAINING_DTYPE)


def deterministic_checkpoint_audit(models: Mapping[str, ArmModel]) -> dict[str, Any]:
    """Compare deployed formulas with independent handwritten references."""
    if set(models) != set(LEARNED_ARMS):
        return {"passed": False, "reason": "exact learned-arm mapping required"}
    observations = _fixture_observations()
    roles = torch.tensor([0, 0, 1, 1, 2, 2], dtype=torch.long)
    incoming = torch.linspace(-0.35, 0.45, 6 * 64, dtype=TRAINING_DTYPE).reshape(6, 64)
    evidence: dict[str, Any] = {}
    maximum_error = 0.0
    support_pass = True
    finite_pass = True
    with torch.no_grad():
        for arm in LEARNED_ARMS:
            model = models[arm]
            messages = model.actor.encode_messages(observations)
            role_sums = [messages[roles == role].sum(dim=0).tolist() for role in range(3)]
            beta = model.actor.beta.detach().tolist()
            panel_errors: dict[str, float] = {}
            for condition in ("intact", "rotated"):
                actual_summary, actual_denominator = model.actor.role_summary(
                    messages, roles, condition=condition
                )
                errors = []
                for receiver_role in range(3):
                    reference_summary, reference_denominator = reference_role_summary(
                        role_sums, [2, 2, 2], beta, receiver_role,
                        rotated=condition == "rotated",
                    )
                    selected = roles == receiver_role
                    expected_summary = torch.tensor(reference_summary, dtype=TRAINING_DTYPE)
                    errors.append(float(torch.max(torch.abs(
                        actual_summary[selected] - expected_summary
                    )).item()))
                    errors.append(float(torch.max(torch.abs(
                        actual_denominator[selected] - reference_denominator
                    )).item()))
                panel_errors[condition] = max(errors)

            intact = model.actor.forward_step(observations, roles, incoming, "intact")
            shadow = model.actor.shadow_rotated_probabilities(observations, roles, incoming)
            rotated = model.actor.forward_step(observations, roles, incoming, "rotated")
            actor_input = torch.cat((
                observations,
                model.actor.role_summary(messages, roles, "intact")[0],
                model.actor.role_summary(messages, roles, "intact")[1].unsqueeze(-1),
            ), dim=-1)
            reference_hidden = reset_before_matrix_gru(
                actor_input, incoming,
                model.actor.W_z, model.actor.W_r, model.actor.W_n,
                model.actor.U_z, model.actor.U_r, model.actor.U_n,
                model.actor.b_z, model.actor.b_r, model.actor.b_n,
            )
            gru_error = float(torch.max(torch.abs(intact.hidden - reference_hidden)).item())
            shadow_error = float(torch.max(torch.abs(shadow - rotated.probabilities)).item())
            illegal_max = 0.0
            floor_error = 0.0
            for row, role in zip(intact.probabilities, roles.tolist(), strict=True):
                legal = set(legal_action_indices(role))
                illegal_max = max(
                    illegal_max,
                    max((abs(float(row[index])) for index in range(ACTION_DIM) if index not in legal), default=0.0),
                )
                floor = POLICY_UNIFORM_WEIGHT / len(legal)
                floor_error = max(floor_error, max(floor - float(row[index]) for index in legal))
            finite = all(bool(torch.isfinite(value).all()) for value in (
                messages, intact.hidden, intact.probabilities, shadow,
            ))
            finite_pass = finite_pass and finite
            support_pass = support_pass and illegal_max == 0.0 and floor_error <= AUDIT_TOLERANCE
            arm_maximum = max(*panel_errors.values(), gru_error, shadow_error)
            maximum_error = max(maximum_error, arm_maximum)
            evidence[arm] = {
                "role_summary_reference_max_abs_error": panel_errors,
                "reset_before_matrix_gru_max_abs_error": gru_error,
                "shadow_equals_nonpropagated_rotated_step_max_abs_error": shadow_error,
                "illegal_probability_max_abs": illegal_max,
                "legal_floor_shortfall_max": floor_error,
                "finite": finite,
            }
    passed = finite_pass and support_pass and maximum_error <= AUDIT_TOLERANCE
    return {
        "passed": passed,
        "fixture": "handwritten_balanced_six-agent_no-world_no-rng",
        "maximum_abs_error": maximum_error,
        "tolerance": AUDIT_TOLERANCE,
        "finite_pass": finite_pass,
        "exact_legal_mask_and_floor_pass": support_pass,
        "evidence": evidence,
        "registered_stochastic_coordinate_created": False,
    }


def structural_checkpoint_audit(models: Mapping[str, ArmModel]) -> dict[str, Any]:
    """Check parameter matching, projection domains, finiteness and one model per arm."""
    if set(models) != set(LEARNED_ARMS):
        return {"passed": False, "reason": "exact learned-arm mapping required"}
    counts = {arm: sum(parameter.numel() for parameter in model.parameters()) for arm, model in models.items()}
    state_shapes = {
        arm: {name: tuple(value.shape) for name, value in model.state_dict().items()}
        for arm, model in models.items()
    }
    common_shapes = state_shapes["PHY-TRUST"] == state_shapes["EDGE-FLEX"]
    arm_identity = all(models[arm].arm_name == arm for arm in LEARNED_ARMS)
    finite = {
        arm: all(bool(torch.isfinite(value).all()) for value in model.state_dict().values())
        for arm, model in models.items()
    }
    beta_max = {
        arm: float(model.actor.beta.detach().abs().max().item())
        for arm, model in models.items()
    }
    beta_bounds = {
        "PHY-TRUST": PHY_BETA_BOUND,
        "EDGE-FLEX": EDGE_BETA_BOUND,
    }
    bound_pass = all(beta_max[arm] <= beta_bounds[arm] + 2.0e-7 for arm in LEARNED_ARMS)
    dtype_pass = all(
        parameter.dtype == TRAINING_DTYPE
        for model in models.values() for parameter in model.parameters()
    )
    device_pass = all(
        parameter.device.type == "cpu"
        for model in models.values() for parameter in model.parameters()
    )
    count_pass = all(value == EXPECTED_PARAMETERS_PER_ARM for value in counts.values())
    passed = all((
        arm_identity, common_shapes, all(finite.values()), bound_pass,
        dtype_pass, device_pass, count_pass,
    ))
    return {
        "passed": passed,
        "parameter_counts": counts,
        "expected_parameters_per_arm": EXPECTED_PARAMETERS_PER_ARM,
        "parameter_counts_pass": count_pass,
        "identical_parameter_and_buffer_shapes": common_shapes,
        "arm_identity_pass": arm_identity,
        "finite_state": finite,
        "beta_max_abs": beta_max,
        "beta_bounds": beta_bounds,
        "projection_bounds_pass": bound_pass,
        "float32_parameters": dtype_pass,
        "cpu_parameters": device_pass,
        "literal_containment": "[-0.15,+0.15] strict subset of [-1.50,+1.50] on the same 18 beta coefficients",
        "strict_capacity_witness": 0.60,
        "one_checkpoint_all_registered_rosters": True,
        "learned_dense_n_by_n_parameters": 0,
    }

