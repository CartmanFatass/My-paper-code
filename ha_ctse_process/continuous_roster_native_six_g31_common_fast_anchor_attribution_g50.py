"""Frozen two-phase common-fast-anchor attribution for G50-P0.

G50 changes only the phase-A actor credit.  Both arms retain the complete G40
fast-anchor graph and the same immediate-baseline fitting exposure.  The
reference uses G40's baseline-conditioned immediate advantage; the null uses
the G49 single-immediate normalized reward while its baseline remains a
storage-disjoint shadow.  Phase A state is then projected to the exact
baseline-free G49 actor route with fresh Adam state.
"""

from __future__ import annotations

import copy
import hashlib
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
    continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49
    as g49,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_realized_successor_channel_attribution_g48
    as g48,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47 as g47,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from ha_ctse_process.anchored_residual_g19 import (
    AnchoredRosterTrajectory,
    normalize_advantage,
    replay_trajectory,
)
from ha_ctse_process.continuous_roster_seed import seed_block_from_bases


ALGORITHM_ID = "CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50"
SOURCE_ID = f"{ALGORITHM_ID}_P0"
SCHEMA_VERSION = 2

DESIGN_STAGE_COMMIT = "b673032361b36dfc5531a06f4a8a37ce0e2c7b62"
RESULT_CONTRACT_STAGE_COMMIT = "22df8091c9f0cbd129f1473862186ce84bcb712a"
DESIGN_DISPOSITION = "CONTRACT_IDENTIFIED_B"
RESULT_CONTRACT_DISPOSITION = "RESULT_CONTRACT_IDENTIFIED"

REFERENCE_ARM = "FAST_ANCHOR_THEN_SINGLE_IMMEDIATE"
NULL_ARM = "SINGLE_IMMEDIATE_FROM_INITIALIZATION"
ARMS = (REFERENCE_ARM, NULL_ARM)

PHASE_A_OBJECTIVE_CONTRACT_ID = "G40_COMMON_NATIVE6_FAST_ANCHOR_V1"
PHASE_A_SOURCE_COMMIT = "97a8b237e0cec6c2713dd2a710d324040fa3dfc2"
PHASE_A_ALGORITHM_ID = g40.ALGORITHM_ID
PHASE_A_INTERPRETATION = "B_COMPLETE_HISTORICAL_FAST_ANCHOR_PACKAGE"
ACCEPTED_G40_ANCHOR_REPLICATES = g48.ACCEPTED_G40_ANCHOR_REPLICATES

PHASE_B_SOURCE_COMMIT = "8ecb01fd3ac0debf1b792e4e51293e07974d633b"
PHASE_B_ALIGNED_IMPLEMENTATION_COMMIT = (
    "9edddc845d88191bbfbd6c2ec779551edbbcb78a"
)
PHASE_B_ALIGNMENT_STAGE_COMMIT = "b56288597c6c91f784fb5f0fcc36ec5ef92de452"
PHASE_B_FORMAL_BRANCH = "DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_EXACTLY_COLLAPSIBLE_G49"

PPO_PASSES = 2
NUM_ENVS = 8
HORIZON = 48
NORMALIZATION_ROWS = NUM_ENVS * HORIZON
ACTIVATION_TOLERANCE = 1e-6
GRADIENT_LIVE_TOLERANCE = 1e-12
K_SEARCH = 0

SEED_BASES = {
    "initialization": 10_501_000,
    "phase_A_ledger": 10_502_000,
    "phase_A_action": 10_503_000,
    "phase_A_gradient_probe": 10_504_000,
    "phase_B_ledger": 10_505_000,
    "phase_B_action": 10_506_000,
    "phase_B_gradient_probe": 10_507_000,
    "evaluation_ledger": 10_508_000,
    "evaluation_process": 10_509_000,
    "evaluation_action": 10_510_000,
}
BOOTSTRAP_SEED = 10_511_050
NONFORMAL_SEED_OFFSET = 900_000

NULL_READ_CERTIFICATE = {
    "baseline_read_into_null_actor_advantage": 0,
    "baseline_read_into_null_actor_gradient": 0,
    "baseline_read_into_null_action_or_logprob": 0,
    "baseline_read_into_null_checkpoint_selection": 0,
    "baseline_read_into_null_evaluation": 0,
    "baseline_read_into_null_result_selection": 0,
}


class G50InvariantError(RuntimeError):
    """Fail-closed G50 graph, gradient, projection, or evidence error."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object] | None = None):
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics or {})
        super().__init__(f"G50 invariant failed before optimizer step: {self.reason}")


@dataclass(frozen=True)
class _PhaseAPlan:
    actor_credit: tuple[torch.Tensor, ...]
    entropy: tuple[torch.Tensor, ...]
    actor_assigned: tuple[torch.Tensor, ...]
    baseline_assigned: tuple[torch.Tensor, ...]
    policy_loss: torch.Tensor
    baseline_loss: torch.Tensor
    actor_groups: dict[str, object]


class G50PhaseBActor(g40.g39.g38.G38FoldableMatchedCSActor):
    """G49 actor route after physical removal of the zero Phase-A residual."""

    def _action_mean_for_member(
        self,
        *,
        candidate: torch.Tensor,
        prefix_fraction: torch.Tensor,
        observation: torch.Tensor,
    ) -> torch.Tensor:
        head_input = torch.cat((candidate, prefix_fraction), dim=-1)
        action_mean = self.action_mean(head_input)
        # The deleted Phase-A residual was exactly zero.  Retain its addition
        # slot without retaining a module, parameter, buffer, or schema field so
        # the accepted G49 floating-point expression remains byte-identical.
        return (
            action_mean
            + torch.zeros_like(action_mean)
            + self.current_readout(observation)
        )


class G50PhaseBProjection(g47.G47NoBaselineProjection):
    """Physical actor-only projection of one freshly trained G50 phase-A arm."""

    def __init__(self, source: g40.G40NativeSixPolicy) -> None:
        nn.Module.__init__(self)
        rng_before = torch.random.get_rng_state().clone()
        self.policy = copy.deepcopy(source.policy)
        if type(self.policy) is not g40.g39.g38.G38FoldableMatchedCSActor:
            raise G50InvariantError("phase_B_actor_source_class_invalid")
        # G47's actor-only executor dispatches through this method.  Switch the
        # retained object to the G50 route before deleting the Phase-A residual;
        # no module construction, parameter copy, or RNG consumption occurs.
        self.policy.__class__ = G50PhaseBActor
        # These complete-G40 modules are phase-A-only.  Removing them makes the
        # phase-B object and its state_dict structurally actor-only.
        if hasattr(self.policy, "critic"):
            delattr(self.policy, "critic")
        if hasattr(self.policy, "delayed_residual"):
            delattr(self.policy, "delayed_residual")
        self.member_capacity = int(source.member_capacity)
        self.critic_state_dim = int(source.critic_state_dim)
        self.phase = "credit_branch"
        self.g50_phase_A_completed_updates = 0
        self.projection_rng_unchanged = bool(
            torch.equal(rng_before, torch.random.get_rng_state())
        )
        if not self.projection_rng_unchanged:
            raise G50InvariantError("phase_B_projection_consumed_rng")
        for parameter in self.parameters():
            parameter.requires_grad_(True)


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    if isinstance(replicate, bool) or not isinstance(replicate, int) or not 0 <= replicate < 3:
        raise ValueError("G50 replicate outside frozen support")
    return seed_block_from_bases(
        SEED_BASES,
        replicate,
        formal=formal,
        nonformal_offset=NONFORMAL_SEED_OFFSET,
    )


def bootstrap_seed(*, formal: bool) -> int:
    return BOOTSTRAP_SEED + (0 if formal else NONFORMAL_SEED_OFFSET)


def _tensor_digest(value: torch.Tensor) -> str:
    row = value.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(row.dtype).encode("ascii"))
    digest.update(json.dumps(list(row.shape), separators=(",", ":")).encode("ascii"))
    digest.update(row.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _gradient_digest(rows: Sequence[torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(_tensor_digest(row).encode("ascii"))
    return digest.hexdigest()


def _gradient_rows(
    rows: Sequence[torch.Tensor | None], parameters: Sequence[nn.Parameter]
) -> tuple[torch.Tensor, ...]:
    if len(rows) != len(parameters):
        raise G50InvariantError("gradient_inventory_mismatch")
    output = tuple(
        torch.zeros_like(parameter) if row is None else row.detach().clone()
        for row, parameter in zip(rows, parameters)
    )
    if any(not bool(torch.isfinite(row).all()) for row in output):
        raise G50InvariantError("nonfinite_gradient")
    return output


def _global_norm(rows: Sequence[torch.Tensor]) -> float:
    total = sum(row.detach().to(torch.float64).square().sum() for row in rows)
    return float(torch.sqrt(total).cpu())


def _rows_equal(left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]) -> bool:
    return len(left) == len(right) and all(torch.equal(a, b) for a, b in zip(left, right))


def _mapping_equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return torch.equal(left, right)
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return tuple(left) == tuple(right) and all(
            _mapping_equal(left[name], right[name]) for name in left
        )
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(
            _mapping_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def _optimizer_parameters(optimizer: torch.optim.Optimizer) -> tuple[nn.Parameter, ...]:
    return tuple(parameter for group in optimizer.param_groups for parameter in group["params"])


def _optimizer_step_value(
    optimizer: torch.optim.Optimizer, parameter: nn.Parameter
) -> float:
    state = optimizer.state.get(parameter, {})
    value = state.get("step", 0.0)
    return float(value.detach().cpu()) if isinstance(value, torch.Tensor) else float(value)


def _optimizer_hyperparameters(optimizer: torch.optim.Optimizer) -> dict[str, object]:
    if not isinstance(optimizer, torch.optim.Adam) or len(optimizer.param_groups) != 1:
        return {"valid": False}
    group = optimizer.param_groups[0]
    return {
        "valid": True,
        "lr": group["lr"],
        "betas": group["betas"],
        "eps": group["eps"],
        "weight_decay": group["weight_decay"],
        "amsgrad": group["amsgrad"],
    }


def _clone_optimizer_row(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    return copy.deepcopy(value)


def _optimizer_state_by_name(
    optimizer: torch.optim.Optimizer, model: nn.Module
) -> dict[str, dict[str, object]]:
    by_id = {id(parameter): name for name, parameter in model.named_parameters()}
    return {
        by_id[id(parameter)]: {
            key: _clone_optimizer_row(value)
            for key, value in sorted(optimizer.state.get(parameter, {}).items())
        }
        for parameter in _optimizer_parameters(optimizer)
    }


def _baseline_optimizer_state(
    optimizer: torch.optim.Optimizer, model: g40.G40NativeSixPolicy
) -> dict[str, dict[str, object]]:
    return {
        name: row
        for name, row in _optimizer_state_by_name(optimizer, model).items()
        if name.startswith("credit_baselines.")
    }


def _parameter_storage_ids(module: nn.Module) -> set[int]:
    return {
        int(value.untyped_storage().data_ptr())
        for value in (*module.parameters(), *module.buffers())
        if value.numel() > 0
    }


def make_phase_A_models(
    *, member_capacity: int, initialization_seed: int
) -> dict[str, g40.G40NativeSixPolicy]:
    initial = g40.make_model(member_capacity, initialization_seed=initialization_seed)
    rng_before_projection = torch.random.get_rng_state().clone()
    models = {arm: copy.deepcopy(initial) for arm in ARMS}
    if not torch.equal(rng_before_projection, torch.random.get_rng_state()):
        raise G50InvariantError("phase_A_projection_consumed_rng")
    if g40.state_bytes(models[REFERENCE_ARM]) != g40.state_bytes(models[NULL_ARM]):
        raise G50InvariantError("phase_A_initial_bytes_mismatch")
    if _parameter_storage_ids(models[REFERENCE_ARM]) & _parameter_storage_ids(models[NULL_ARM]):
        raise G50InvariantError("phase_A_storage_alias")
    return models


def make_phase_A_optimizers(
    models: Mapping[str, g40.G40NativeSixPolicy],
) -> dict[str, torch.optim.Adam]:
    if tuple(models) != ARMS:
        raise ValueError("G50 phase-A optimizer construction requires exact arms")
    optimizers = {
        arm: torch.optim.Adam(
            models[arm].actor_credit_parameters(),
            lr=g40.LEARNING_RATE,
            betas=(0.9, 0.999),
            eps=1e-8,
            weight_decay=0.0,
            amsgrad=False,
        )
        for arm in ARMS
    }
    if any(optimizer.state for optimizer in optimizers.values()):
        raise G50InvariantError("phase_A_Adam_not_empty")
    return optimizers


def phase_A_boundary_audit(
    models: Mapping[str, g40.G40NativeSixPolicy],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    reference = models.get(REFERENCE_ARM)
    null = models.get(NULL_ARM)
    if not isinstance(reference, g40.G40NativeSixPolicy) or not isinstance(
        null, g40.G40NativeSixPolicy
    ):
        return {"passed": False}
    names = {
        arm: tuple(name for name, parameter in models[arm].named_parameters() if parameter.requires_grad)
        for arm in ARMS
    }
    optimizer_names = {
        arm: tuple(
            {id(parameter): name for name, parameter in models[arm].named_parameters()}[
                id(parameter)
            ]
            for parameter in _optimizer_parameters(optimizers[arm])
        )
        for arm in ARMS
    }
    hyper = {arm: _optimizer_hyperparameters(optimizers[arm]) for arm in ARMS}
    passed = bool(
        g40.state_bytes(reference) == g40.state_bytes(null)
        and g40.buffer_bytes(reference) == g40.buffer_bytes(null)
        and names[REFERENCE_ARM] == names[NULL_ARM]
        and optimizer_names[REFERENCE_ARM] == optimizer_names[NULL_ARM]
        and optimizer_names[REFERENCE_ARM] == tuple(g40.actor_credit_parameter_names(reference))
        and hyper[REFERENCE_ARM] == hyper[NULL_ARM]
        and hyper[REFERENCE_ARM]
        == {
            "valid": True,
            "lr": 1e-3,
            "betas": (0.9, 0.999),
            "eps": 1e-8,
            "weight_decay": 0.0,
            "amsgrad": False,
        }
        and not optimizers[REFERENCE_ARM].state
        and not optimizers[NULL_ARM].state
        and not (
            _parameter_storage_ids(reference) & _parameter_storage_ids(null)
        )
    )
    return {
        "phase_A_model_class": type(reference).__name__,
        "model_state_bytes_equal": g40.state_bytes(reference) == g40.state_bytes(null),
        "parameter_names_order_masks_equal": names[REFERENCE_ARM] == names[NULL_ARM],
        "optimizer_parameter_order_equal": optimizer_names[REFERENCE_ARM]
        == optimizer_names[NULL_ARM],
        "optimizer_hyperparameters_equal": hyper[REFERENCE_ARM] == hyper[NULL_ARM],
        "optimizer_states_empty": not optimizers[REFERENCE_ARM].state
        and not optimizers[NULL_ARM].state,
        "baseline_storage_disjoint": not (
            _parameter_storage_ids(reference.credit_baselines)
            & _parameter_storage_ids(null.credit_baselines)
        ),
        "projection_RNG_consumption": 0,
        "passed": passed,
    }


def _actor_gradients(
    objective: torch.Tensor, model: g40.G40NativeSixPolicy
) -> tuple[torch.Tensor, ...]:
    parameters = model.full_actor_parameters()
    return _gradient_rows(
        torch.autograd.grad(objective, parameters, retain_graph=True, allow_unused=True),
        parameters,
    )


def _baseline_gradients(
    objective: torch.Tensor, model: g40.G40NativeSixPolicy
) -> tuple[torch.Tensor, ...]:
    parameters = tuple(model.credit_baselines.parameters())
    return _gradient_rows(
        torch.autograd.grad(objective, parameters, retain_graph=True, allow_unused=True),
        parameters,
    )


def _actor_group_evidence(
    model: g40.G40NativeSixPolicy,
    reference_rows: Sequence[torch.Tensor],
    null_rows: Sequence[torch.Tensor],
) -> dict[str, object]:
    actor_parameters = model.full_actor_parameters()
    indices = {id(parameter): index for index, parameter in enumerate(actor_parameters)}
    groups: dict[str, object] = {}
    for name in g40.REGISTERED_ACTOR_GROUPS:
        parameters = g40._actor_groups(model)[name]
        left = tuple(reference_rows[indices[id(parameter)]] for parameter in parameters)
        right = tuple(null_rows[indices[id(parameter)]] for parameter in parameters)
        left_norm = _global_norm(left)
        right_norm = _global_norm(right)
        finite = bool(np.isfinite(left_norm) and np.isfinite(right_norm))
        groups[name] = {
            "reference_gradient_norm": left_norm,
            "null_counterfactual_gradient_norm": right_norm,
            "finite": finite,
            "live_in_at_least_one": bool(
                finite
                and max(left_norm, right_norm) > GRADIENT_LIVE_TOLERANCE
            ),
        }
    groups["passed"] = all(
        bool(groups[name]["finite"] and groups[name]["live_in_at_least_one"])  # type: ignore[index]
        for name in g40.REGISTERED_ACTOR_GROUPS
    )
    return groups


def phase_A_activation(
    reference_rows: Sequence[torch.Tensor], null_rows: Sequence[torch.Tensor]
) -> dict[str, object]:
    if len(reference_rows) != len(null_rows) or any(
        not bool(torch.isfinite(row).all()) for row in (*reference_rows, *null_rows)
    ):
        raise G50InvariantError("phase_A_activation_nonfinite_or_shape_invalid")
    reference_norm = _global_norm(reference_rows)
    null_norm = _global_norm(null_rows)
    denominator = max(reference_norm, null_norm)
    difference = _global_norm(tuple(a - b for a, b in zip(reference_rows, null_rows)))
    q_A = 0.0 if denominator == 0.0 else difference / denominator
    if not np.isfinite(q_A):
        raise G50InvariantError("phase_A_q_A_nonfinite")
    return {
        "reference_gradient_norm": reference_norm,
        "null_counterfactual_gradient_norm": null_norm,
        "difference_gradient_norm": difference,
        "q_A": q_A,
        "activation_tolerance": ACTIVATION_TOLERANCE,
        "treatment_active": bool(q_A > ACTIVATION_TOLERANCE),
        "reference_only_activation_evidence": True,
        "actual_null_activation_evidence_read_count": 0,
    }


def _phase_A_plan(
    *,
    arm: str,
    model: g40.G40NativeSixPolicy,
    trajectory: AnchoredRosterTrajectory,
    normalized_actor_credit: torch.Tensor,
    baseline_trajectory: AnchoredRosterTrajectory,
) -> _PhaseAPlan:
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    policy = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized_actor_credit
    )
    entropy_objective = -g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
    actor_credit = _actor_gradients(policy, model)
    entropy = _actor_gradients(entropy_objective, model)
    actor_assigned = tuple(a + b for a, b in zip(actor_credit, entropy))

    # Both arms fit an identical, reference-owned shadow batch.  This keeps the
    # complete baseline module, loss and Adam exposure matched while preventing
    # any null actor read of baseline outputs.
    baseline_values = model.credit_baselines(baseline_trajectory.critic_states)[..., 0]
    baseline_loss = F.mse_loss(
        baseline_values, baseline_trajectory.rewards.detach()
    )
    baseline_objective = g40.VALUE_COEFFICIENT * baseline_loss
    baseline_assigned = _baseline_gradients(baseline_objective, model)
    if arm == NULL_ARM and any(NULL_READ_CERTIFICATE.values()):
        raise G50InvariantError("null_baseline_read_certificate_invalid")
    return _PhaseAPlan(
        actor_credit=actor_credit,
        entropy=entropy,
        actor_assigned=actor_assigned,
        baseline_assigned=baseline_assigned,
        policy_loss=policy,
        baseline_loss=baseline_loss,
        actor_groups={},
    )


def _assign_and_step(
    model: g40.G40NativeSixPolicy,
    optimizer: torch.optim.Optimizer,
    plan: _PhaseAPlan,
) -> None:
    parameters = model.actor_credit_parameters()
    assigned = (*plan.actor_assigned, *plan.baseline_assigned)
    if tuple(id(row) for row in parameters) != tuple(
        id(row) for row in _optimizer_parameters(optimizer)
    ):
        raise G50InvariantError("phase_A_optimizer_parameter_order_invalid")
    optimizer.zero_grad(set_to_none=True)
    for parameter, gradient in zip(parameters, assigned):
        parameter.grad = gradient.detach().clone()
    g40._optimizer_step(optimizer, parameters)


def phase_A_order_swap_guard(
    models: Mapping[str, g40.G40NativeSixPolicy],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
) -> dict[str, object]:
    """Prove reverse preparation order is a zero-step, zero-mutation operation."""

    model_before = {arm: g40.state_bytes(models[arm]) for arm in ARMS}
    optimizer_before = {
        arm: _optimizer_state_by_name(optimizers[arm], models[arm]) for arm in ARMS
    }
    gradient_slots_before = {
        arm: tuple(
            None if parameter.grad is None else parameter.grad.detach().clone()
            for parameter in models[arm].actor_credit_parameters()
        )
        for arm in ARMS
    }
    rng_before = torch.random.get_rng_state().clone()
    reference_trajectory = trajectories[REFERENCE_ARM]
    reference_credit = g40.compute_credit_targets(
        rewards=reference_trajectory.rewards,
        slow_values=reference_trajectory.old_values,
        immediate_baselines=reference_trajectory.old_immediate_baselines,
        successor_baselines=reference_trajectory.old_successor_baselines,
        terminals=g40.terminal_mask(reference_trajectory),
    )
    normalized = {
        REFERENCE_ARM: normalize_advantage(reference_credit.immediate_advantage),
        NULL_ARM: g49._normalize_single(
            g49._single_immediate_target(trajectories[NULL_ARM].rewards)
        ).normalized,
    }

    def prepare(order: Sequence[str]) -> dict[str, tuple[str, str]]:
        output: dict[str, tuple[str, str]] = {}
        for arm in order:
            row = _phase_A_plan(
                arm=arm,
                model=models[arm],
                trajectory=trajectories[arm],
                normalized_actor_credit=normalized[arm],
                baseline_trajectory=reference_trajectory,
            )
            output[arm] = (
                _gradient_digest(row.actor_assigned),
                _gradient_digest(row.baseline_assigned),
            )
        return output

    forward = prepare(ARMS)
    reverse = prepare(tuple(reversed(ARMS)))
    model_unchanged = all(
        model_before[arm] == g40.state_bytes(models[arm]) for arm in ARMS
    )
    optimizer_unchanged = all(
        _mapping_equal(
            optimizer_before[arm],
            _optimizer_state_by_name(optimizers[arm], models[arm]),
        )
        for arm in ARMS
    )
    gradient_slots_unchanged = True
    for arm in ARMS:
        for before, parameter in zip(
            gradient_slots_before[arm], models[arm].actor_credit_parameters()
        ):
            if before is None:
                gradient_slots_unchanged &= parameter.grad is None
            else:
                gradient_slots_unchanged &= parameter.grad is not None and torch.equal(
                    before, parameter.grad
                )
    passed = bool(
        forward == reverse
        and model_unchanged
        and optimizer_unchanged
        and gradient_slots_unchanged
        and torch.equal(rng_before, torch.random.get_rng_state())
    )
    return {
        "forward_preparation": forward,
        "reverse_preparation": reverse,
        "mate_inputs_unchanged": model_unchanged,
        "optimizer_state_unchanged": optimizer_unchanged,
        "gradient_slots_unchanged": gradient_slots_unchanged,
        "RNG_unchanged": torch.equal(rng_before, torch.random.get_rng_state()),
        "optimizer_steps": 0,
        "passed": passed,
    }


def optimize_phase_A_update(
    models: Mapping[str, g40.G40NativeSixPolicy],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, AnchoredRosterTrajectory],
    *,
    replicate: int,
    update_index: int,
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS or tuple(trajectories) != ARMS:
        raise ValueError("G50 phase-A update requires exact ordered arms")
    boundary = phase_A_boundary_audit(models, optimizers) if update_index == 0 else None
    if boundary is not None and boundary["passed"] is not True:
        raise G50InvariantError("phase_A_boundary_invalid", boundary)

    reference_trajectory = trajectories[REFERENCE_ARM]
    reference_replay = replay_trajectory(
        models[REFERENCE_ARM], reference_trajectory, device=torch.device("cpu")
    )
    reference_credit = g40.compute_credit_targets(
        rewards=reference_trajectory.rewards,
        slow_values=reference_trajectory.old_values,
        immediate_baselines=reference_trajectory.old_immediate_baselines,
        successor_baselines=reference_trajectory.old_successor_baselines,
        terminals=g40.terminal_mask(reference_trajectory),
    )
    del reference_replay
    normalized = {
        REFERENCE_ARM: normalize_advantage(reference_credit.immediate_advantage),
        NULL_ARM: g49._normalize_single(
            g49._single_immediate_target(trajectories[NULL_ARM].rewards)
        ).normalized,
    }
    reference_raw_counterfactual = g49._normalize_single(
        g49._single_immediate_target(reference_trajectory.rewards)
    ).normalized

    pass_records: list[dict[str, object]] = []
    for pass_index in range(PPO_PASSES):
        plans = {
            arm: _phase_A_plan(
                arm=arm,
                model=models[arm],
                trajectory=trajectories[arm],
                normalized_actor_credit=normalized[arm],
                baseline_trajectory=reference_trajectory,
            )
            for arm in ARMS
        }
        reference_counterfactual_replay = replay_trajectory(
            models[REFERENCE_ARM], reference_trajectory, device=torch.device("cpu")
        )
        counterfactual_loss = g40._policy_loss_from_normalized_advantage(
            reference_counterfactual_replay,
            reference_trajectory,
            reference_raw_counterfactual,
        )
        counterfactual = _actor_gradients(
            counterfactual_loss, models[REFERENCE_ARM]
        )
        activation = phase_A_activation(
            plans[REFERENCE_ARM].actor_credit, counterfactual
        )
        groups = _actor_group_evidence(
            models[REFERENCE_ARM], plans[REFERENCE_ARM].actor_credit, counterfactual
        )
        baseline_equal = _rows_equal(
            plans[REFERENCE_ARM].baseline_assigned,
            plans[NULL_ARM].baseline_assigned,
        )
        baseline_loss_equal = torch.equal(
            plans[REFERENCE_ARM].baseline_loss.detach(),
            plans[NULL_ARM].baseline_loss.detach(),
        )
        if not groups["passed"] or not baseline_equal or not baseline_loss_equal:
            raise G50InvariantError(
                "phase_A_pre_step_gate_invalid",
                {
                    "actor_groups": groups,
                    "baseline_parameter_gradient_bytes_equal": baseline_equal,
                    "baseline_MSE_loss_bytes_equal": baseline_loss_equal,
                },
            )

        common_entropy_equal = _rows_equal(
            plans[REFERENCE_ARM].entropy, plans[NULL_ARM].entropy
        )
        if update_index == 0 and pass_index == 0 and not common_entropy_equal:
            raise G50InvariantError("first_batch_entropy_gradient_mismatch")

        # Both complete plans are prepared and validated before either step.
        _assign_and_step(
            models[REFERENCE_ARM], optimizers[REFERENCE_ARM], plans[REFERENCE_ARM]
        )
        _assign_and_step(models[NULL_ARM], optimizers[NULL_ARM], plans[NULL_ARM])
        baseline_state_equal = g40.state_bytes(
            models[REFERENCE_ARM].credit_baselines
        ) == g40.state_bytes(models[NULL_ARM].credit_baselines)
        baseline_adam_equal = _mapping_equal(
            _baseline_optimizer_state(
                optimizers[REFERENCE_ARM], models[REFERENCE_ARM]
            ),
            _baseline_optimizer_state(optimizers[NULL_ARM], models[NULL_ARM]),
        )
        if not baseline_state_equal or not baseline_adam_equal:
            raise G50InvariantError("phase_A_shadow_baseline_departed")
        pass_records.append(
            {
                "pass_index": pass_index,
                "plans_prepared_before_either_step": True,
                "branch_update_order": list(ARMS),
                "reference_actor_credit_digest": _gradient_digest(
                    plans[REFERENCE_ARM].actor_credit
                ),
                "null_actor_credit_digest": _gradient_digest(
                    plans[NULL_ARM].actor_credit
                ),
                "reference_counterfactual_digest": _gradient_digest(counterfactual),
                "common_entropy_gradient_bytes_equal_on_forced_first_batch": (
                    common_entropy_equal if update_index == 0 and pass_index == 0 else None
                ),
                "baseline_MSE_loss_bytes_equal": baseline_loss_equal,
                "baseline_parameter_gradient_bytes_equal": baseline_equal,
                "baseline_state_bytes_equal_after_pass": baseline_state_equal,
                "baseline_Adam_state_bytes_equal_after_pass": baseline_adam_equal,
                "actor_group_liveness": groups,
                "activation": activation,
                "null_baseline_reads": dict(NULL_READ_CERTIFICATE),
                "actor_optimizer_steps": {arm: 1 for arm in ARMS},
            }
        )
    return {
        "replicate": int(replicate),
        "update_index": int(update_index),
        "phase": "A",
        "objective_contract_id": PHASE_A_OBJECTIVE_CONTRACT_ID,
        "phase_A_reference_interpretation": PHASE_A_INTERPRETATION,
        "boundary": boundary,
        "advantage_normalization_count": {arm: 1 for arm in ARMS},
        "advantage_recomputed_between_passes": False,
        "pass_records": pass_records,
        "optimizer_steps_per_arm": {arm: PPO_PASSES for arm in ARMS},
        "diagnostic_optimizer_steps": 0,
        "passed": True,
    }


def build_phase_A_conclusion_evidence(
    update_records: Sequence[Mapping[str, object]], *, formal: bool
) -> dict[str, object]:
    expected_replicates = (0, 1, 2) if formal else (0,)
    active = {replicate: False for replicate in expected_replicates}
    for update in update_records:
        replicate = int(update["replicate"])
        if replicate not in active:
            return {"passed": False, "reason": "replicate_inventory"}
        for record in update.get("pass_records", []):  # type: ignore[assignment]
            if isinstance(record, Mapping):
                activation = record.get("activation")
                if isinstance(activation, Mapping):
                    active[replicate] |= activation.get("treatment_active") is True
    return {
        "formal": formal,
        "required_replicates": list(expected_replicates),
        # JSON object keys are strings. Emit the terminal representation at
        # construction time so one exact validator applies before and after
        # manifest serialization.
        "active_phase_A_pass_by_replicate": {
            str(replicate): active[replicate] for replicate in expected_replicates
        },
        "activation_tolerance": ACTIVATION_TOLERANCE,
        "strict_activation": True,
        "reference_only_activation_evidence": True,
        "actual_null_activation_evidence_read_count": 0,
        "passed": all(active.values()),
    }


def validate_phase_A_conclusion_evidence(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    formal = value.get("formal")
    expected = [0, 1, 2] if formal is True else [0]
    expected_keys = [str(replicate) for replicate in expected]
    active = value.get("active_phase_A_pass_by_replicate")
    return bool(
        formal in (True, False)
        and value.get("required_replicates") == expected
        and isinstance(active, Mapping)
        and set(active) == set(expected_keys)
        and all(active[key] is True for key in expected_keys)
        and value.get("activation_tolerance") == ACTIVATION_TOLERANCE
        and value.get("strict_activation") is True
        and value.get("reference_only_activation_evidence") is True
        and value.get("actual_null_activation_evidence_read_count") == 0
        and value.get("passed") is True
    )


def _phase_B_actor_state(model: G50PhaseBProjection) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
        if name != "policy.log_std"
    }


def project_phase_B_models(
    phase_A_models: Mapping[str, g40.G40NativeSixPolicy],
    *,
    completed_phase_A_updates: int,
) -> tuple[dict[str, G50PhaseBProjection], dict[str, dict[str, object]]]:
    if tuple(phase_A_models) != ARMS:
        raise ValueError("G50 phase boundary requires exact arms")
    rng_before = torch.random.get_rng_state().clone()
    models = {
        arm: G50PhaseBProjection(phase_A_models[arm]) for arm in ARMS
    }
    certificates: dict[str, dict[str, object]] = {}
    for arm in ARMS:
        model = models[arm]
        model.g50_phase_A_completed_updates = int(completed_phase_A_updates)
        state_names = tuple(model.state_dict())
        forbidden = tuple(
            name
            for name in state_names
            if "credit_baselines" in name
            or "slow_critic" in name
            or ".critic." in name
            or "delayed_residual" in name
        )
        source_actor = {
            name: value
            for name, value in phase_A_models[arm].state_dict().items()
            if name in model.state_dict()
        }
        actor_equal = tuple(source_actor) == state_names and all(
            torch.equal(source_actor[name], model.state_dict()[name])
            for name in state_names
        )
        certificates[arm] = {
            "completed_phase_A_updates": int(completed_phase_A_updates),
            "phase_A_optimizer_deleted": True,
            "phase_A_Adam_state_count": 0,
            "phase_A_baseline_deleted": not hasattr(model, "credit_baselines"),
            "phase_A_slow_critic_deleted": not hasattr(model, "slow_critic"),
            "policy_critic_deleted": not hasattr(model.policy, "critic"),
            "policy_delayed_residual_deleted": not hasattr(
                model.policy, "delayed_residual"
            ),
            "forbidden_phase_A_state_keys": list(forbidden),
            "actor_log_std_bytes_preserved": actor_equal,
            "projection_optimizer_steps": 0,
            "projection_RNG_consumption": 0,
            "passed": bool(actor_equal and not forbidden),
        }
        if certificates[arm]["passed"] is not True:
            raise G50InvariantError("phase_A_to_B_projection_invalid", certificates[arm])
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise G50InvariantError("phase_A_to_B_projection_consumed_rng")
    if _parameter_storage_ids(models[REFERENCE_ARM]) & _parameter_storage_ids(models[NULL_ARM]):
        raise G50InvariantError("phase_B_storage_alias")
    return models, certificates


def phase_B_actor_interface_evidence(
    *, member_capacity: int, initialization_seed: int
) -> dict[str, object]:
    """Exercise the deleted-residual production dispatch with zero transitions."""

    rng_before = torch.random.get_rng_state().clone()
    arm_rows: dict[str, dict[str, object]] = {}
    with torch.random.fork_rng():
        phase_A = make_phase_A_models(
            member_capacity=member_capacity, initialization_seed=initialization_seed
        )
        projected, certificates = project_phase_B_models(
            phase_A, completed_phase_A_updates=10
        )
        for arm in ARMS:
            model = projected[arm]
            actor = model.policy
            step = g47._actor_only_step(
                model,
                observations=torch.zeros(
                    (1, member_capacity, actor.observation_dim),
                    dtype=actor.log_std.dtype,
                ),
                active_mask=torch.ones((1, member_capacity), dtype=torch.bool),
                hidden=torch.zeros(
                    (1, member_capacity, actor.hidden_dim), dtype=actor.log_std.dtype
                ),
                deterministic=True,
            )
            arm_rows[arm] = {
                "actor_class": type(actor).__name__,
                "delayed_residual_absent": not hasattr(actor, "delayed_residual"),
                "projection_certificate_passed": certificates[arm]["passed"] is True,
                "actions_finite": bool(torch.isfinite(step.actions).all()),
                "action_shape": list(step.actions.shape),
            }
        expected_shape = [
            1,
            member_capacity,
            projected[REFERENCE_ARM].policy.action_dim,
        ]
    rng_unchanged = bool(torch.equal(rng_before, torch.random.get_rng_state()))
    passed = bool(
        rng_unchanged
        and all(
            row["actor_class"] == "G50PhaseBActor"
            and row["delayed_residual_absent"] is True
            and row["projection_certificate_passed"] is True
            and row["actions_finite"] is True
            and row["action_shape"] == expected_shape
            for row in arm_rows.values()
        )
    )
    evidence: dict[str, object] = {
        "arms": arm_rows,
        "projection_RNG_consumption": 0 if rng_unchanged else 1,
        "scientific_real_transitions": 0,
        "optimizer_steps": 0,
        "passed": passed,
    }
    if not passed:
        raise G50InvariantError("phase_B_actor_interface_invalid", evidence)
    return evidence


def make_phase_B_optimizers(
    models: Mapping[str, G50PhaseBProjection],
) -> dict[str, torch.optim.Adam]:
    optimizers = {arm: g41.make_actor_head_optimizer(models[arm]) for arm in ARMS}
    if any(optimizer.state for optimizer in optimizers.values()):
        raise G50InvariantError("phase_B_Adam_not_fresh")
    if any(
        tuple(id(row) for row in _optimizer_parameters(optimizers[arm]))
        != tuple(id(row) for row in models[arm].full_actor_parameters())
        for arm in ARMS
    ):
        raise G50InvariantError("phase_B_Adam_parameter_order_invalid")
    return optimizers


def optimize_phase_B_update(
    models: Mapping[str, G50PhaseBProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, g47.G47ActorTrajectory],
    *,
    replicate: int,
    update_index: int,
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS or tuple(trajectories) != ARMS:
        raise ValueError("G50 phase-B update requires exact ordered arms")
    normalized = {
        arm: g49._normalize_single(
            g49._single_immediate_target(trajectories[arm].rewards)
        )
        for arm in ARMS
    }
    records: list[dict[str, object]] = []
    for pass_index in range(PPO_PASSES):
        probes = {
            arm: g49._single_probe(
                models[arm], trajectories[arm], normalized[arm].normalized
            )
            for arm in ARMS
        }
        # Both plans exist before the fixed reference-then-null step order.
        for arm in ARMS:
            g49._apply_pass(models[arm], optimizers[arm], probes[arm].assigned)
        records.append(
            {
                "pass_index": pass_index,
                "plans_prepared_before_either_step": True,
                "branch_update_order": list(ARMS),
                "single_channel_target_digest": {
                    arm: _tensor_digest(normalized[arm].target) for arm in ARMS
                },
                "single_channel_normalized_digest": {
                    arm: _tensor_digest(normalized[arm].normalized) for arm in ARMS
                },
                "single_channel_gradient_digest": {
                    arm: _gradient_digest(probes[arm].gradient) for arm in ARMS
                },
                "entropy_addition_count": {arm: 1 for arm in ARMS},
                "actor_Adam_step_count": {arm: 1 for arm in ARMS},
                "phase_B_route": "G49_SINGLE_IMMEDIATE",
            }
        )
    return {
        "replicate": int(replicate),
        "update_index": int(update_index),
        "phase": "B",
        "phase_B_source_commit": PHASE_B_SOURCE_COMMIT,
        "phase_B_formal_branch": PHASE_B_FORMAL_BRANCH,
        "pass_records": records,
        "optimizer_steps_per_arm": {arm: PPO_PASSES for arm in ARMS},
        "passed": True,
    }


def static_configuration_certificate(*, formal: bool) -> dict[str, object]:
    replicates = 3 if formal else 1
    updates = 100 if formal else 10
    episodes = 48 if formal else 6
    bootstrap = 10_000 if formal else 250
    training = replicates * len(ARMS) * (updates + updates) * NUM_ENVS * HORIZON
    evaluation = replicates * len(ARMS) * 3 * 4 * episodes * HORIZON
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "arms": list(ARMS),
        "replicates": replicates,
        "phase_A_updates_per_arm": updates,
        "phase_B_updates_per_arm": updates,
        "environments_per_update": NUM_ENVS,
        "PPO_passes": PPO_PASSES,
        "evaluation_capacities": [6, 8, 12],
        "evaluation_cells": replicates * len(ARMS) * 3 * 4,
        "episodes_per_cell": episodes,
        "training_transitions": training,
        "evaluation_transitions": evaluation,
        "total_real_transitions": training + evaluation,
        "optimizer_steps": replicates * len(ARMS) * (updates + updates) * PPO_PASSES,
        "bootstrap_resamples": bootstrap,
        "activation_tolerance": ACTIVATION_TOLERANCE,
        "gradient_live_tolerance": GRADIENT_LIVE_TOLERANCE,
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


_CHECKPOINT_KEYS = {
    "schema_version",
    "algorithm_id",
    "source_id",
    "source_commit",
    "formal",
    "replicate",
    "arm",
    "kind",
    "phase_A_objective_contract_id",
    "phase_A_source_commit",
    "completed_phase_A_updates",
    "phase_B_source_commit",
    "phase_B_formal_branch",
    "completed_phase_B_updates",
    "configuration",
    "seed_block",
    "actor_state",
    "log_std",
    "phase_B_actor_Adam_state",
    "phase_A_state_disposal_certificate",
    "phase_B_single_immediate_route_certificate",
    "source_process_lifecycle_provenance",
}

_PHASE_B_ACTOR_STATE_KEYS = (
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
_PHASE_B_ADAM_KEYS = ("policy.log_std", *_PHASE_B_ACTOR_STATE_KEYS)


def build_final_checkpoint(
    *,
    model: G50PhaseBProjection,
    optimizer: torch.optim.Optimizer,
    source_commit: str,
    formal: bool,
    replicate: int,
    arm: str,
    completed_phase_A_updates: int,
    completed_phase_B_updates: int,
    configuration: Mapping[str, object],
    seeds: Mapping[str, int],
    disposal_certificate: Mapping[str, object],
) -> dict[str, object]:
    if arm not in ARMS or disposal_certificate.get("passed") is not True:
        raise G50InvariantError("checkpoint_projection_certificate_invalid")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": source_commit,
        "formal": bool(formal),
        "replicate": int(replicate),
        "arm": arm,
        "kind": "final_only",
        "phase_A_objective_contract_id": PHASE_A_OBJECTIVE_CONTRACT_ID,
        "phase_A_source_commit": PHASE_A_SOURCE_COMMIT,
        "completed_phase_A_updates": int(completed_phase_A_updates),
        "phase_B_source_commit": PHASE_B_SOURCE_COMMIT,
        "phase_B_formal_branch": PHASE_B_FORMAL_BRANCH,
        "completed_phase_B_updates": int(completed_phase_B_updates),
        "configuration": dict(configuration),
        "seed_block": dict(seeds),
        "actor_state": _phase_B_actor_state(model),
        "log_std": model.log_std.detach().cpu().clone(),
        "phase_B_actor_Adam_state": _optimizer_state_by_name(optimizer, model),
        "phase_A_state_disposal_certificate": dict(disposal_certificate),
        "phase_B_single_immediate_route_certificate": {
            "target_law": "x_I=r_t",
            "normalization_instances": 1,
            "channel_losses": 1,
            "gradient_constructions": 1,
            "entropy_addition_count": 1,
            "second_immediate_channel": False,
            "realized_successor_channel": False,
            "baseline_module": False,
            "slow_critic": False,
        },
        "source_process_lifecycle_provenance": {
            "training_source": "G32_capacity8_fixed_process",
            "evaluation_source": "G34_P0_fixed_and_random_processes",
            "external_reward_unchanged": True,
            "paired_source_ledgers": True,
            "member_owned_action_noise": True,
        },
    }
    if not validate_final_checkpoint(payload):
        raise G50InvariantError("final_checkpoint_invalid")
    return payload


def validate_final_checkpoint(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != _CHECKPOINT_KEYS:
        return False
    actor_state = value.get("actor_state")
    adam = value.get("phase_B_actor_Adam_state")
    disposal = value.get("phase_A_state_disposal_certificate")
    route = value.get("phase_B_single_immediate_route_certificate")
    forbidden_fragments = (
        "credit_baselines",
        "slow_critic",
        ".critic.",
        "delayed_residual",
        "phase_A_optimizer",
        "second_immediate",
        "realized_successor",
    )
    actor_keys = tuple(actor_state) if isinstance(actor_state, Mapping) else ()
    formal = value.get("formal")
    expected_updates = 100 if formal is True else 10
    completed_phase_B_updates = value.get("completed_phase_B_updates")
    adam_steps_valid = False
    if isinstance(adam, Mapping) and tuple(adam) == _PHASE_B_ADAM_KEYS:
        expected_steps = expected_updates * PPO_PASSES
        adam_steps_valid = all(
            isinstance(adam[name], Mapping)
            and set(adam[name]) == {"step", "exp_avg", "exp_avg_sq"}
            and float(
                adam[name]["step"].detach().cpu()
                if isinstance(adam[name]["step"], torch.Tensor)
                else adam[name]["step"]
            )
            == float(expected_steps)
            and isinstance(adam[name]["exp_avg"], torch.Tensor)
            and isinstance(adam[name]["exp_avg_sq"], torch.Tensor)
            for name in _PHASE_B_ADAM_KEYS
        )
    return bool(
        value.get("schema_version") == SCHEMA_VERSION
        and value.get("algorithm_id") == ALGORITHM_ID
        and value.get("source_id") == SOURCE_ID
        and formal in (True, False)
        and isinstance(value.get("source_commit"), str)
        and len(value["source_commit"]) == 40
        and all(character in "0123456789abcdef" for character in value["source_commit"])
        and value.get("arm") in ARMS
        and value.get("kind") == "final_only"
        and value.get("phase_A_objective_contract_id")
        == PHASE_A_OBJECTIVE_CONTRACT_ID
        and value.get("phase_A_source_commit") == PHASE_A_SOURCE_COMMIT
        and value.get("phase_B_source_commit") == PHASE_B_SOURCE_COMMIT
        and value.get("phase_B_formal_branch") == PHASE_B_FORMAL_BRANCH
        and isinstance(actor_state, Mapping)
        and actor_keys == _PHASE_B_ACTOR_STATE_KEYS
        and not any(
            fragment in key for key in actor_keys for fragment in forbidden_fragments
        )
        and isinstance(value.get("log_std"), torch.Tensor)
        and value.get("completed_phase_A_updates") == expected_updates
        and completed_phase_B_updates == expected_updates
        and adam_steps_valid
        and isinstance(disposal, Mapping)
        and disposal.get("passed") is True
        and isinstance(route, Mapping)
        and route
        == {
            "target_law": "x_I=r_t",
            "normalization_instances": 1,
            "channel_losses": 1,
            "gradient_constructions": 1,
            "entropy_addition_count": 1,
            "second_immediate_channel": False,
            "realized_successor_channel": False,
            "baseline_module": False,
            "slow_critic": False,
        }
    )


def load_phase_B_checkpoint_model(
    checkpoint: Mapping[str, object], *, member_capacity: int
) -> G50PhaseBProjection:
    if not validate_final_checkpoint(checkpoint):
        raise G50InvariantError("checkpoint_reload_validation_failed")
    seed = int(checkpoint["seed_block"]["initialization"])  # type: ignore[index]
    shell = g40.make_model(member_capacity, initialization_seed=seed)
    model = G50PhaseBProjection(shell)
    state = dict(checkpoint["actor_state"])  # type: ignore[arg-type]
    state["policy.log_std"] = checkpoint["log_std"]
    model.load_state_dict(state, strict=True)
    return model


def serialize_diagnostics(value: Mapping[str, object]) -> str:
    def normalize(row: object) -> object:
        if isinstance(row, torch.Tensor):
            return {
                "dtype": str(row.dtype),
                "shape": list(row.shape),
                "sha256": _tensor_digest(row),
            }
        if isinstance(row, Mapping):
            return {str(key): normalize(item) for key, item in row.items()}
        if isinstance(row, (list, tuple)):
            return [normalize(item) for item in row]
        return row

    return json.dumps(normalize(value), sort_keys=True, separators=(",", ":"))
