"""Fresh, paired common-entropy coefficient attribution for G53-P0.

The only treatment is the immutable coefficient multiplying the raw entropy
gradient.  Both arms are baseline-free before trajectories or optimizers are
constructed and execute the same replay, entropy, and autograd graph.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import CodeType
from types import MappingProxyType, SimpleNamespace
from typing import Any

import numpy as np
import torch
from torch import nn

from ha_ctse_process import anchored_residual_g19 as g19
from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_common_fast_anchor_attribution_g50 as g50,
)
from ha_ctse_process.continuous_roster_seed import seed_block_from_bases
from ha_ctse_process import (
    continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51 as g51,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47 as g47,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49 as g49,
)


ALGORITHM_ID = "CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_ENTROPY_ATTRIBUTION_G53"
SOURCE_ID = f"{ALGORITHM_ID}_P0"
SCHEMA_VERSION = 1
CLAIM_IDENTITY = (
    "PRE_TANH_GAUSSIAN_LOG_STD_ENTROPY_BONUS_COEFFICIENT_0P01_VS_EXACT_ZERO"
)
ESTIMAND = "Delta_entropy=U_COMMON_ENTROPY-U_NO_ENTROPY"
EXPERIMENT_CLASS = "ORDINARY_NONFORMAL_B_SINGLE_ROOT_CONDITIONAL"

G50_SOURCE_COMMIT = "b8290699f5c10c593bbc21a6666c17950fae84d3"
G50_EXECUTION_COMMIT = "23af6bf7c80a4b73c09cf0423f9f539972b1b55d"
G50_ALIGNMENT_COMMIT = "4df41063d077ace7e0c9212e0cbadbf56e1be4b7"
G50_FORMAL_BRANCH = "FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50"
G51_SOURCE_COMMIT = "ce6ed8659c480ca2779155b2871dc82b89fa0e95"
G51_EXECUTION_COMMIT = "fa52274bdc6d90c79ef1658cd5c060046f113692"
G51_ALIGNED_IMPLEMENTATION_COMMIT = "188b210975a0f243ae34318d658fbf943d1d63ab"
G51_ALIGNMENT_COMMIT = "aa756dcd06a2ea622c155f2983a89bb5d76e9d80"
G51_FORMAL_BRANCH = "PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51"
G51_EXACT_RESULT = "D_G51=0"

COMMON_ENTROPY_ARM = "COMMON_ENTROPY_COEFFICIENT_0P01"
NO_ENTROPY_ARM = "EXACT_ZERO_ENTROPY_COEFFICIENT"
REFERENCE_ARM = COMMON_ENTROPY_ARM
NULL_ARM = NO_ENTROPY_ARM
ARMS = (REFERENCE_ARM, NULL_ARM)

REFERENCE_ENTROPY_COEFFICIENT = float.fromhex("0x1.47ae147ae147bp-7")
NULL_ENTROPY_COEFFICIENT = float.fromhex("0x0.0p+0")
assert REFERENCE_ENTROPY_COEFFICIENT.hex() == "0x1.47ae147ae147bp-7"
assert NULL_ENTROPY_COEFFICIENT.hex() == "0x0.0p+0"
ENTROPY_COEFFICIENTS: Mapping[str, float] = MappingProxyType(
    {
        REFERENCE_ARM: REFERENCE_ENTROPY_COEFFICIENT,
        NULL_ARM: NULL_ENTROPY_COEFFICIENT,
    }
)

PPO_PASSES = 2
NUM_ENVS = 8
HORIZON = 48
NORMALIZATION_ROWS = NUM_ENVS * HORIZON
PHASE_A_UPDATES = 10
PHASE_B_UPDATES = 10
SHARED_PRETREATMENT_BATCHES = 1
POST_TREATMENT_ARM_LOCAL_PHYSICAL_COLLECTIONS_PER_ROOT = 38
TRAINING_TRANSITIONS = 14_976
EVALUATION_CAPACITIES = (6, 8, 12)
EVALUATION_CELLS = 24
EVALUATION_EPISODES_PER_CELL = 6
EVALUATION_TRANSITIONS = 6_912
TOTAL_REAL_TRANSITIONS = 21_888
OPTIMIZER_STEPS = 80
BOOTSTRAP_RESAMPLES = 250
PRIMARY_MARGIN = 0.05
UTILITY_FLOOR = 0.90
EVENT_FLOOR = 0.85
SEGMENT_FLOOR = 0.85
PROCESS_MARGIN = -0.05
STOCHASTIC_FLOOR = 0.80
MINIMUM_REPLICATE_FLOOR = 0.85
K_SEARCH = 0
G52_CARRY_STATE_COUNT = 0

SEED_BASES = MappingProxyType(
    {
        "initialization": 10_541_000,
        "phase_A_ledger": 10_542_000,
        "phase_A_action": 10_543_000,
        "phase_A_gradient_probe": 10_544_000,
        "phase_B_ledger": 10_545_000,
        "phase_B_action": 10_546_000,
        "phase_B_gradient_probe": 10_547_000,
        "evaluation_ledger": 10_548_000,
        "evaluation_process": 10_549_000,
        "evaluation_action": 10_550_000,
    }
)
BOOTSTRAP_SEED = 10_551_053
NONFORMAL_SEED_OFFSET = 900_000

INVALID_BRANCH = "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_ENTROPY_ATTRIBUTION_G53"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_ENTROPY_ATTRIBUTION_"
    "G53_EXERCISE_COMPLETE"
)
FUTURE_CLAIM_BRANCHES = (
    INVALID_BRANCH,
    "SOURCE_OR_REFERENCE_ACCESS_FAILURE_G53",
    "NO_ENTROPY_FINITE_BUDGET_SUFFICIENT_G53",
    "COMMON_ENTROPY_FINITE_BUDGET_ADVANTAGE_G53",
    "MIXED_UNDERPOWERED_COMMON_ENTROPY_ATTRIBUTION_G53",
)


class G53InvariantError(RuntimeError):
    """A frozen G53 construction, gradient, pairing, or artifact gate failed."""

    def __init__(self, reason: str, diagnostics: Mapping[str, object] | None = None):
        self.reason = str(reason)
        self.diagnostics = dict(diagnostics or {})
        super().__init__(f"G53 invariant failed: {self.reason}")

    def __reduce__(self) -> tuple[type[G53InvariantError], tuple[str, dict[str, object]]]:
        return type(self), (self.reason, dict(self.diagnostics))


G53PhaseAModel = g51.G51NoBaselinePhaseAProjection
G53PhaseBModel = g50.G50PhaseBProjection


@dataclass(frozen=True)
class EntropyPlan:
    policy_loss: torch.Tensor
    raw_entropy: torch.Tensor
    policy_gradients: tuple[torch.Tensor, ...]
    raw_entropy_gradients: tuple[torch.Tensor, ...]
    scaled_entropy_gradients: tuple[torch.Tensor, ...]
    assigned_gradients: tuple[torch.Tensor, ...]
    replay: g47.G47ActorReplay
    coefficient: float


def entropy_coefficient(
    arm: str, *, audit: list[tuple[str, str]] | None = None, phase: str = ""
) -> float:
    """Return the sole local treatment value; called once per arm/pass plan."""

    try:
        value = ENTROPY_COEFFICIENTS[arm]
    except KeyError as error:
        raise ValueError("G53 entropy arm is not registered") from error
    if audit is not None:
        audit.append((str(phase), arm))
    return value


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    if isinstance(replicate, bool) or not isinstance(replicate, int) or not 0 <= replicate < 3:
        raise ValueError("G53 replicate outside frozen future support")
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


def _rows_digest(rows: Sequence[torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(_tensor_digest(row).encode("ascii"))
    return digest.hexdigest()


def _rows_equal(left: Sequence[torch.Tensor], right: Sequence[torch.Tensor]) -> bool:
    return len(left) == len(right) and all(torch.equal(a, b) for a, b in zip(left, right))


def _norm64(rows: Sequence[torch.Tensor]) -> float:
    total = sum(row.detach().to(torch.float64).square().sum() for row in rows)
    return float(torch.sqrt(total).cpu())


def _gradient_rows(
    objective: torch.Tensor, parameters: Sequence[nn.Parameter]
) -> tuple[torch.Tensor, ...]:
    raw = torch.autograd.grad(
        objective, tuple(parameters), retain_graph=True, allow_unused=True
    )
    rows = tuple(
        torch.zeros_like(parameter) if gradient is None else gradient.detach().clone()
        for gradient, parameter in zip(raw, parameters)
    )
    if any(not bool(torch.isfinite(row).all()) for row in rows):
        raise G53InvariantError("nonfinite_gradient")
    return rows


def _state_equal(left: nn.Module, right: nn.Module) -> bool:
    return g40.state_bytes(left) == g40.state_bytes(right) and g40.buffer_bytes(
        left
    ) == g40.buffer_bytes(right)


def _parameter_names(model: nn.Module, parameters: Sequence[nn.Parameter]) -> tuple[str, ...]:
    by_id = {id(parameter): name for name, parameter in model.named_parameters()}
    return tuple(by_id.get(id(parameter), "<foreign>") for parameter in parameters)


def _optimizer_parameters(optimizer: torch.optim.Optimizer) -> tuple[nn.Parameter, ...]:
    return tuple(parameter for group in optimizer.param_groups for parameter in group["params"])


def _optimizer_state(model: nn.Module, optimizer: torch.optim.Optimizer) -> dict[str, object]:
    names = _parameter_names(model, _optimizer_parameters(optimizer))
    output: dict[str, object] = {}
    for name, parameter in zip(names, _optimizer_parameters(optimizer)):
        output[name] = {
            key: value.detach().cpu().clone() if isinstance(value, torch.Tensor) else copy.deepcopy(value)
            for key, value in sorted(optimizer.state.get(parameter, {}).items())
        }
    return output


def _gradient_slots(model: nn.Module) -> tuple[torch.Tensor | None, ...]:
    return tuple(
        None if parameter.grad is None else parameter.grad.detach().clone()
        for parameter in model.parameters()
    )


def _nested_equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return torch.equal(left, right)
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return tuple(left) == tuple(right) and all(_nested_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(_nested_equal(a, b) for a, b in zip(left, right))
    return left == right


def make_phase_A_models(
    *, member_capacity: int, initialization_seed: int
) -> dict[str, G53PhaseAModel]:
    """Project one fresh G50-null source once, then clone the G53 arms."""

    fresh_source = g40.make_model(
        int(member_capacity), initialization_seed=int(initialization_seed)
    )
    # The frozen G53 start state supersedes the predecessor's -1 exploration
    # initialization.  Apply it once on the fresh, pre-projection ancestor so
    # both deep-cloned arms inherit identical exact-zero bytes.
    with torch.no_grad():
        fresh_source.log_std.zero_()
    rng_before = torch.random.get_rng_state().clone()
    baseline_free_ancestor = g51.G51NoBaselinePhaseAProjection(fresh_source)
    models = {arm: copy.deepcopy(baseline_free_ancestor) for arm in ARMS}
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise G53InvariantError("construction_or_clone_consumed_RNG")
    if not _state_equal(models[REFERENCE_ARM], models[NULL_ARM]):
        raise G53InvariantError("initial_arm_state_mismatch")
    if g40.shared_tensor_storage_count(tuple(models.values())) != 0:
        raise G53InvariantError("initial_arm_storage_alias")
    if any(hasattr(model, "credit_baselines") for model in models.values()):
        raise G53InvariantError("baseline_present_before_trajectory")
    if any(not hasattr(model, "slow_critic") for model in models.values()):
        raise G53InvariantError("phase_A_slow_critic_missing")
    return models


def make_phase_A_optimizers(
    models: Mapping[str, G53PhaseAModel],
) -> dict[str, torch.optim.Adam]:
    if tuple(models) != ARMS:
        raise ValueError("G53 phase-A optimizer construction requires exact arms")
    optimizers = {
        arm: torch.optim.Adam(
            models[arm].full_actor_parameters(),
            lr=g40.LEARNING_RATE,
            betas=(0.9, 0.999),
            eps=1e-8,
            weight_decay=0.0,
            amsgrad=False,
        )
        for arm in ARMS
    }
    if any(optimizer.state for optimizer in optimizers.values()):
        raise G53InvariantError("phase_A_Adam_not_fresh")
    return optimizers


def phase_A_boundary_audit(
    models: Mapping[str, G53PhaseAModel],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    exact = tuple(models) == ARMS and tuple(optimizers) == ARMS
    names = {
        arm: _parameter_names(models[arm], models[arm].full_actor_parameters())
        for arm in ARMS
    } if exact else {}
    optimizer_names = {
        arm: _parameter_names(models[arm], _optimizer_parameters(optimizers[arm]))
        for arm in ARMS
    } if exact else {}
    slow_equal = bool(
        exact
        and g40.state_bytes(models[REFERENCE_ARM].slow_critic)
        == g40.state_bytes(models[NULL_ARM].slow_critic)
    )
    passed = bool(
        exact
        and _state_equal(models[REFERENCE_ARM], models[NULL_ARM])
        and names[REFERENCE_ARM] == names[NULL_ARM]
        and all(optimizer_names[arm] == names[arm] for arm in ARMS)
        and all(not optimizers[arm].state for arm in ARMS)
        and g40.shared_tensor_storage_count(tuple(models.values())) == 0
        and all(not hasattr(models[arm], "credit_baselines") for arm in ARMS)
        and slow_equal
    )
    return {
        "fresh_G50_null_source_count": 1,
        "G51_NoBaselinePhaseAProjection_count": 1,
        "G51_make_phase_A_models_call_count": 0,
        "baseline_free_before_trajectory_or_optimizer": True,
        "model_state_bytes_equal": exact and _state_equal(models[REFERENCE_ARM], models[NULL_ARM]),
        "actor_parameter_names": list(names.get(REFERENCE_ARM, ())),
        "actor_parameter_order_equal": exact and names[REFERENCE_ARM] == names[NULL_ARM],
        "optimizer_parameter_order_equal": exact and all(optimizer_names[arm] == names[arm] for arm in ARMS),
        "Adam_states_empty": exact and all(not optimizers[arm].state for arm in ARMS),
        "slow_critic_state_bytes_equal_and_unexposed": slow_equal,
        "shared_storage_count": g40.shared_tensor_storage_count(tuple(models.values())) if exact else -1,
        "projection_RNG_consumption": 0,
        "G52_CARRY_state_count": G52_CARRY_STATE_COUNT,
        "passed": passed,
    }


def _normalized_reward(trajectory: g47.G47ActorTrajectory) -> g49.SingleChannelNormalization:
    return g49._normalize_single(g49._single_immediate_target(trajectory.rewards))


def _phase_A_plan(
    model: G53PhaseAModel,
    trajectory: g47.G47ActorTrajectory,
    normalized: torch.Tensor,
    *,
    coefficient: float,
) -> EntropyPlan:
    return _build_entropy_plan(model, trajectory, normalized, coefficient=coefficient)


def _phase_B_plan(
    model: G53PhaseBModel,
    trajectory: g47.G47ActorTrajectory,
    normalized: torch.Tensor,
    *,
    coefficient: float,
) -> EntropyPlan:
    return _build_entropy_plan(model, trajectory, normalized, coefficient=coefficient)


def _build_entropy_plan(
    model: G53PhaseAModel | G53PhaseBModel,
    trajectory: g47.G47ActorTrajectory,
    normalized: torch.Tensor,
    *,
    coefficient: float,
) -> EntropyPlan:
    if coefficient not in (REFERENCE_ENTROPY_COEFFICIENT, NULL_ENTROPY_COEFFICIENT):
        raise ValueError("G53 plan coefficient outside frozen support")
    replay = g47.actor_only_replay(model, trajectory)
    policy_loss = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, normalized
    )
    raw_entropy = g40._entropy(replay)
    parameters = model.full_actor_parameters()
    policy_rows = _gradient_rows(policy_loss, parameters)
    raw_rows = _gradient_rows(raw_entropy, parameters)
    # This multiplication is deliberately executed even when coefficient is
    # exact zero.  No zero-arm skip, detach, or replacement is permitted.
    scaled_rows = tuple(row * coefficient for row in raw_rows)
    assigned = tuple(policy - scaled for policy, scaled in zip(policy_rows, scaled_rows))
    if any(not bool(torch.isfinite(row).all()) for row in (*scaled_rows, *assigned)):
        raise G53InvariantError("nonfinite_scaled_or_assigned_gradient")
    return EntropyPlan(
        policy_loss=policy_loss,
        raw_entropy=raw_entropy,
        policy_gradients=policy_rows,
        raw_entropy_gradients=raw_rows,
        scaled_entropy_gradients=scaled_rows,
        assigned_gradients=assigned,
        replay=replay,
        coefficient=coefficient,
    )


def _apply_plan(
    model: G53PhaseAModel | G53PhaseBModel,
    optimizer: torch.optim.Optimizer,
    plan: EntropyPlan,
) -> None:
    parameters = model.full_actor_parameters()
    if _optimizer_parameters(optimizer) != parameters:
        raise G53InvariantError("optimizer_parameter_order_invalid")
    optimizer.zero_grad(set_to_none=True)
    for parameter, gradient in zip(parameters, plan.assigned_gradients):
        parameter.grad = gradient.detach().clone()
    g40._optimizer_step(optimizer, parameters)


def _trajectory_digest(trajectory: g47.G47ActorTrajectory) -> dict[str, str]:
    return {
        name: _tensor_digest(value)
        for name, value in vars(trajectory).items()
        if isinstance(value, torch.Tensor)
    }


def _actor_metadata(model: nn.Module) -> dict[str, object]:
    actor = model.policy  # type: ignore[attr-defined]
    return {
        "observation_dim": int(actor.observation_dim),
        "action_dim": int(actor.action_dim),
        "member_capacity": int(actor.member_capacity),
        "parameter_names": list(_parameter_names(model, model.full_actor_parameters())),  # type: ignore[attr-defined]
        "log_std_hex": [float(value).hex() for value in actor.log_std.detach().cpu().tolist()],
    }


def _activation(
    reference: Sequence[torch.Tensor], null: Sequence[torch.Tensor]
) -> dict[str, object]:
    reference_norm = _norm64(reference)
    null_norm = _norm64(null)
    difference = _norm64(tuple(a - b for a, b in zip(reference, null)))
    denominator = max(reference_norm, null_norm)
    q_H = 0.0 if reference_norm == 0.0 and null_norm == 0.0 else difference / denominator
    if not np.isfinite(q_H):
        raise G53InvariantError("q_H_nonfinite")
    return {
        "reference_scaled_entropy_gradient_norm64": reference_norm,
        "null_scaled_entropy_gradient_norm64": null_norm,
        "difference_norm64": difference,
        "q_H": q_H,
        "active_iff_q_H_gt_0": q_H > 0.0,
    }


def _optimize_update(
    *,
    phase: str,
    models: Mapping[str, G53PhaseAModel | G53PhaseBModel],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, g47.G47ActorTrajectory],
    update_index: int,
    episode_ids: Mapping[str, Sequence[int]] | None,
) -> dict[str, object]:
    if tuple(models) != ARMS or tuple(optimizers) != ARMS or tuple(trajectories) != ARMS:
        raise ValueError("G53 update requires exact ordered arms")
    shared_pretreatment = trajectories[REFERENCE_ARM] is trajectories[NULL_ARM]
    if phase == "A" and update_index == 0 and not shared_pretreatment:
        raise G53InvariantError("phase_A_update0_not_same_stored_object")
    if not (phase == "A" and update_index == 0) and shared_pretreatment:
        raise G53InvariantError("post_treatment_trajectory_forced_equal")
    paired_ids = bool(
        episode_ids is not None
        and tuple(episode_ids) == ARMS
        and tuple(episode_ids[REFERENCE_ARM]) == tuple(episode_ids[NULL_ARM])
    )
    if episode_ids is not None and not paired_ids:
        raise G53InvariantError("episode_ID_pairing_invalid")

    if shared_pretreatment:
        common_normalization = _normalized_reward(trajectories[REFERENCE_ARM])
        normalization = {arm: common_normalization for arm in ARMS}
    else:
        normalization = {arm: _normalized_reward(trajectories[arm]) for arm in ARMS}
    records: list[dict[str, object]] = []
    first_certificate: dict[str, object] | None = None
    plan_builder = _phase_A_plan if phase == "A" else _phase_B_plan
    for pass_index in range(PPO_PASSES):
        coefficient_audit: list[tuple[str, str]] = []
        coefficients = {
            arm: entropy_coefficient(arm, audit=coefficient_audit, phase=phase)
            for arm in ARMS
        }
        expected_coefficient_audit = [(phase, arm) for arm in ARMS]
        if coefficient_audit != expected_coefficient_audit:
            raise G53InvariantError(
                "coefficient_read_inventory_invalid",
                {"observed": coefficient_audit, "expected": expected_coefficient_audit},
            )
        model_before = {arm: g40.state_bytes(models[arm]) for arm in ARMS}
        optimizer_before = {arm: _optimizer_state(models[arm], optimizers[arm]) for arm in ARMS}
        gradients_before = {arm: _gradient_slots(models[arm]) for arm in ARMS}
        rng_before = torch.random.get_rng_state().clone()
        plans = {
            arm: plan_builder(
                models[arm], trajectories[arm], normalization[arm].normalized,
                coefficient=coefficients[arm],
            )
            for arm in ARMS
        }
        reverse = {
            arm: plan_builder(
                models[arm], trajectories[arm], normalization[arm].normalized,
                coefficient=coefficients[arm],
            )
            for arm in reversed(ARMS)
        }
        reverse_preserved = bool(
            all(_rows_equal(plans[arm].assigned_gradients, reverse[arm].assigned_gradients) for arm in ARMS)
            and all(model_before[arm] == g40.state_bytes(models[arm]) for arm in ARMS)
            and all(_nested_equal(optimizer_before[arm], _optimizer_state(models[arm], optimizers[arm])) for arm in ARMS)
            and all(_nested_equal(gradients_before[arm], _gradient_slots(models[arm])) for arm in ARMS)
            and torch.equal(rng_before, torch.random.get_rng_state())
        )
        if not reverse_preserved:
            raise G53InvariantError("reverse_plan_preparation_mutated_state")

        common_raw = _rows_equal(
            plans[REFERENCE_ARM].raw_entropy_gradients,
            plans[NULL_ARM].raw_entropy_gradients,
        )
        null_zero = all(
            torch.equal(row, torch.zeros_like(row))
            for row in plans[NULL_ARM].scaled_entropy_gradients
        )
        names = _parameter_names(models[REFERENCE_ARM], models[REFERENCE_ARM].full_actor_parameters())
        support = [
            name for name, row in zip(names, plans[REFERENCE_ARM].raw_entropy_gradients)
            if bool(torch.count_nonzero(row))
        ]
        reference_scaled_support = [
            name for name, row in zip(names, plans[REFERENCE_ARM].scaled_entropy_gradients)
            if bool(torch.count_nonzero(row))
        ]
        activation = _activation(
            plans[REFERENCE_ARM].scaled_entropy_gradients,
            plans[NULL_ARM].scaled_entropy_gradients,
        )
        pre_equal = bool(
            _state_equal(models[REFERENCE_ARM], models[NULL_ARM])
            and _rows_equal(plans[REFERENCE_ARM].policy_gradients, plans[NULL_ARM].policy_gradients)
            and common_raw
        ) if shared_pretreatment else None
        actor_metadata_equal_before_step = (
            _actor_metadata(models[REFERENCE_ARM])
            == _actor_metadata(models[NULL_ARM])
        )
        for arm in ARMS:
            _apply_plan(models[arm], optimizers[arm], plans[arm])
        post_diverged = bool(
            not _state_equal(models[REFERENCE_ARM], models[NULL_ARM])
            or not _nested_equal(
                _optimizer_state(models[REFERENCE_ARM], optimizers[REFERENCE_ARM]),
                _optimizer_state(models[NULL_ARM], optimizers[NULL_ARM]),
            )
        )
        if phase == "A" and update_index == 0 and pass_index == 0:
            coefficient_only = bool(
                _rows_equal(
                    plans[REFERENCE_ARM].policy_gradients,
                    plans[NULL_ARM].policy_gradients,
                )
                and common_raw
                and all(
                    torch.equal(
                        plan.assigned_gradients[index],
                        plan.policy_gradients[index]
                        - plan.scaled_entropy_gradients[index],
                    )
                    for plan in plans.values()
                    for index in range(len(plan.assigned_gradients))
                )
            )
            first_certificate = {
                "same_stored_trajectory_object": shared_pretreatment,
                "model_mask_RNG_actor_metadata_Adam_equal": bool(
                    pre_equal
                    and torch.equal(trajectories[REFERENCE_ARM].active_mask, trajectories[NULL_ARM].active_mask)
                    and actor_metadata_equal_before_step
                    and _nested_equal(optimizer_before[REFERENCE_ARM], optimizer_before[NULL_ARM])
                    and torch.equal(rng_before, torch.random.get_rng_state())
                ),
                "stored_trajectory_digest": _trajectory_digest(trajectories[REFERENCE_ARM]),
                "replay_old_logprob_target_centered_normalized_policy_gradient_equal": bool(
                    pre_equal
                    and normalization[REFERENCE_ARM] is normalization[NULL_ARM]
                    and torch.equal(plans[REFERENCE_ARM].replay.log_probs, plans[NULL_ARM].replay.log_probs)
                    and torch.equal(trajectories[REFERENCE_ARM].old_log_probs, trajectories[NULL_ARM].old_log_probs)
                    and torch.equal(normalization[REFERENCE_ARM].target, normalization[NULL_ARM].target)
                    and torch.equal(normalization[REFERENCE_ARM].centered, normalization[NULL_ARM].centered)
                    and torch.equal(normalization[REFERENCE_ARM].normalized, normalization[NULL_ARM].normalized)
                ),
                "raw_entropy_scalar_equal_finite": bool(
                    torch.equal(plans[REFERENCE_ARM].raw_entropy.detach(), plans[NULL_ARM].raw_entropy.detach())
                    and torch.isfinite(plans[REFERENCE_ARM].raw_entropy)
                ),
                "raw_entropy_gradient_equal_finite": common_raw,
                "raw_entropy_gradient_support": support,
                "null_scaled_gradient_finite_bytewise_zero": null_zero,
                "reference_scaled_gradient_support": reference_scaled_support,
                "reference_scaled_gradient_positive_norm": activation["reference_scaled_entropy_gradient_norm64"] > 0.0,
                "coefficient_is_sole_graph_delta": coefficient_only,
                "post_step_actor_or_Adam_state_differs": post_diverged,
                "activation": activation,
            }
            if not (
                first_certificate["same_stored_trajectory_object"]
                and first_certificate["model_mask_RNG_actor_metadata_Adam_equal"]
                and first_certificate["replay_old_logprob_target_centered_normalized_policy_gradient_equal"]
                and first_certificate["raw_entropy_scalar_equal_finite"]
                and first_certificate["raw_entropy_gradient_equal_finite"]
                and support == ["policy.log_std"]
                and first_certificate["null_scaled_gradient_finite_bytewise_zero"]
                and reference_scaled_support == ["policy.log_std"]
                and first_certificate["reference_scaled_gradient_positive_norm"]
                and first_certificate["coefficient_is_sole_graph_delta"]
                and first_certificate["post_step_actor_or_Adam_state_differs"]
                and activation["active_iff_q_H_gt_0"]
            ):
                raise G53InvariantError("first_common_batch_activation_gate_failed", first_certificate)
        records.append(
            {
                "pass_index": pass_index,
                "plans_prepared_before_either_step": True,
                "reverse_preparation_preserved_model_optimizer_gradient_and_RNG": reverse_preserved,
                "coefficient_read_audit": [list(row) for row in coefficient_audit],
                "coefficient_call_count_per_arm": {
                    arm: sum(row == (phase, arm) for row in coefficient_audit)
                    for arm in ARMS
                },
                "coefficient_hex": {arm: coefficients[arm].hex() for arm in ARMS},
                "raw_entropy_gradient_digest": {arm: _rows_digest(plans[arm].raw_entropy_gradients) for arm in ARMS},
                "scaled_entropy_gradient_digest": {arm: _rows_digest(plans[arm].scaled_entropy_gradients) for arm in ARMS},
                "normalization_rows": NORMALIZATION_ROWS,
                "physical_normalization_instances": 1 if shared_pretreatment else 2,
                "normalization_exposures": 2,
                "optimizer_steps_per_arm": 1,
            }
        )
    return {
        "algorithm_id": ALGORITHM_ID,
        "phase": phase,
        "update_index": int(update_index),
        "shared_pretreatment_physical_collection_count": 1 if shared_pretreatment else 0,
        "arm_exposures": 2,
        "paired_episode_IDs": paired_ids if episode_ids is not None else True,
        "post_treatment_arm_local_on_policy": not shared_pretreatment,
        "pass_records": records,
        "first_batch_activation_certificate": first_certificate,
        "optimizer_steps_per_arm": PPO_PASSES,
        "passed": True,
    }


def optimize_phase_A_update(
    models: Mapping[str, G53PhaseAModel],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, g47.G47ActorTrajectory] | g47.G47ActorTrajectory,
    *,
    update_index: int,
    episode_ids: Mapping[str, Sequence[int]] | None = None,
) -> dict[str, object]:
    rows = (
        {arm: trajectories for arm in ARMS}
        if isinstance(trajectories, g47.G47ActorTrajectory)
        else dict(trajectories)
    )
    return _optimize_update(
        phase="A", models=models, optimizers=optimizers, trajectories=rows,
        update_index=update_index, episode_ids=episode_ids,
    )


def project_phase_B_models(
    phase_A_models: Mapping[str, G53PhaseAModel], *, completed_phase_A_updates: int
) -> tuple[dict[str, G53PhaseBModel], dict[str, dict[str, object]]]:
    if tuple(phase_A_models) != ARMS:
        raise ValueError("G53 phase boundary requires exact arms")
    rng_before = torch.random.get_rng_state().clone()
    models = {arm: g50.G50PhaseBProjection(phase_A_models[arm]) for arm in ARMS}
    certificates: dict[str, dict[str, object]] = {}
    for arm in ARMS:
        source_state = phase_A_models[arm].state_dict()
        target_state = models[arm].state_dict()
        retained = {name: value for name, value in source_state.items() if name in target_state}
        actor_equal = tuple(retained) == tuple(target_state) and all(
            torch.equal(retained[name], target_state[name]) for name in retained
        )
        forbidden = [
            name for name in target_state
            if any(token in name for token in ("credit_baselines", "slow_critic", ".critic.", "delayed_residual"))
        ]
        certificates[arm] = {
            "completed_phase_A_updates": int(completed_phase_A_updates),
            "retained_actor_and_log_std_bytes_equal": actor_equal,
            "slow_critic_deleted_at_common_boundary": not hasattr(models[arm], "slow_critic"),
            "baseline_absent": not hasattr(models[arm], "credit_baselines"),
            "forbidden_state_keys": forbidden,
            "phase_A_optimizer_disposed": True,
            "projection_optimizer_steps": 0,
            "projection_RNG_consumption": 0,
            "passed": bool(actor_equal and not forbidden),
        }
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise G53InvariantError("phase_B_projection_consumed_RNG")
    if g40.shared_tensor_storage_count(tuple(models.values())) != 0:
        raise G53InvariantError("phase_B_storage_alias")
    if not all(row["passed"] is True for row in certificates.values()):
        raise G53InvariantError("phase_B_projection_invalid", certificates)
    return models, certificates


def make_phase_B_optimizers(
    models: Mapping[str, G53PhaseBModel],
) -> dict[str, torch.optim.Adam]:
    if tuple(models) != ARMS:
        raise ValueError("G53 phase-B optimizer construction requires exact arms")
    optimizers = {arm: g50.g41.make_actor_head_optimizer(models[arm]) for arm in ARMS}
    if any(optimizer.state for optimizer in optimizers.values()):
        raise G53InvariantError("phase_B_Adam_not_fresh")
    return optimizers


def optimize_phase_B_update(
    models: Mapping[str, G53PhaseBModel],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, g47.G47ActorTrajectory],
    *,
    update_index: int,
    episode_ids: Mapping[str, Sequence[int]] | None = None,
) -> dict[str, object]:
    return _optimize_update(
        phase="B", models=models, optimizers=optimizers, trajectories=trajectories,
        update_index=update_index, episode_ids=episode_ids,
    )


def static_configuration_certificate(*, formal: bool = False) -> dict[str, object]:
    if formal:
        raise ValueError("G53 formal runtime is not authorized")
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "experiment_class": EXPERIMENT_CLASS,
        "formal": False,
        "independent_roots": 1,
        "arms": list(ARMS),
        "entropy_coefficients_hex": {
            arm: ENTROPY_COEFFICIENTS[arm].hex() for arm in ARMS
        },
        "phase_A_updates_per_arm": PHASE_A_UPDATES,
        "phase_B_updates_per_arm": PHASE_B_UPDATES,
        "environments_per_update": NUM_ENVS,
        "H": HORIZON,
        "PPO_passes": PPO_PASSES,
        "shared_pretreatment_batches": SHARED_PRETREATMENT_BATCHES,
        "post_treatment_arm_local_physical_collections_per_root": POST_TREATMENT_ARM_LOCAL_PHYSICAL_COLLECTIONS_PER_ROOT,
        "physical_training_collection_count": 39,
        "arm_update_exposures": 40,
        "training_transition_formula": "(2*(10+10)-1)*8*48",
        "training_transitions": TRAINING_TRANSITIONS,
        "evaluation_capacities": list(EVALUATION_CAPACITIES),
        "evaluation_cells": EVALUATION_CELLS,
        "episodes_per_cell": EVALUATION_EPISODES_PER_CELL,
        "evaluation_transitions": EVALUATION_TRANSITIONS,
        "total_real_transitions": TOTAL_REAL_TRANSITIONS,
        "optimizer_steps": OPTIMIZER_STEPS,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "seed_bases": dict(SEED_BASES),
        "effective_nonformal_seed_block": seed_block(0, formal=False),
        "bootstrap_seed_base": BOOTSTRAP_SEED,
        "effective_nonformal_bootstrap_seed": bootstrap_seed(formal=False),
        "nonformal_seed_offset": NONFORMAL_SEED_OFFSET,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "retry_rescue_extra_root_sweep_seed_search": False,
        "checkpoint_selection": "final_only_actor",
        "future_three_root_access_floors": {
            "utility": UTILITY_FLOOR,
            "event": EVENT_FLOOR,
            "segment": SEGMENT_FLOOR,
            "process_margin": PROCESS_MARGIN,
            "stochastic": STOCHASTIC_FLOOR,
            "minimum_replicate": MINIMUM_REPLICATE_FLOOR,
            "primary_margin": PRIMARY_MARGIN,
        },
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "python_fallback": False,
        "G52_CARRY_state_count": 0,
    }


def reconstruct_static_certificate() -> dict[str, object]:
    """Zero-trajectory source and entropy-gradient binding certificate."""

    with torch.random.fork_rng():
        model = make_phase_A_models(member_capacity=8, initialization_seed=10_541_000)[REFERENCE_ARM]
        parameters = model.full_actor_parameters()
        names = _parameter_names(model, parameters)
        active_mask = torch.ones((1, 1, 8), dtype=torch.bool)
        entropy_per_member = (
            0.5 * torch.log(torch.tensor(2.0 * np.pi * np.e))
            + model.log_std.clamp(-5.0, 2.0)
        ).sum().expand(1, 1, 8)
        raw_entropy = g40._entropy(SimpleNamespace(active_mask=active_mask, entropies=entropy_per_member))
        gradients = torch.autograd.grad(raw_entropy, parameters, allow_unused=True)
        support = [name for name, row in zip(names, gradients) if row is not None and bool(torch.count_nonzero(row))]
    forbidden_names = {"credit_baselines", "baseline_values"}
    plan_reads = set(_build_entropy_plan.__code__.co_names)
    def reads_name(code: CodeType, name: str) -> bool:
        return name in code.co_names or any(
            reads_name(value, name) for value in code.co_consts
            if isinstance(value, CodeType)
        )
    coefficient_read_components = {
        "construction": any(
            reads_name(function.__code__, "entropy_coefficient")
            for function in (
                make_phase_A_models, make_phase_A_optimizers,
                project_phase_B_models, make_phase_B_optimizers,
            )
        ),
        "collection": reads_name(_normalized_reward.__code__, "entropy_coefficient"),
        "evaluation": reads_name(load_final_checkpoint_model.__code__, "entropy_coefficient"),
        "result_selection": reads_name(validate_final_checkpoint.__code__, "entropy_coefficient"),
    }
    return {
        "algorithm_id": ALGORITHM_ID,
        "g40_entropy_callable_bound": g40._entropy.__module__.endswith("g40"),
        "g19_coefficient_authority_exact": g19.ENTROPY_COEFFICIENT.hex() == REFERENCE_ENTROPY_COEFFICIENT.hex(),
        "g40_coefficient_authority_exact": g40.ENTROPY_COEFFICIENT.hex() == REFERENCE_ENTROPY_COEFFICIENT.hex(),
        "g40_global_coefficient_unmutated": g40.ENTROPY_COEFFICIENT == 0.01,
        "initial_log_std_exact_zero": bool(torch.equal(model.log_std.detach(), torch.zeros_like(model.log_std))),
        "synthetic_raw_entropy_finite": bool(torch.isfinite(raw_entropy)),
        "synthetic_raw_entropy_gradient_support": support,
        "actor_parameter_names": list(names),
        "actor_parameter_name_count": len(names),
        "expected_actor_parameter_name_count": 17,
        "plan_binds_g40_entropy": "_entropy" in plan_reads,
        "coefficient_call_per_arm_pass_owned_by_update": reads_name(
            _optimize_update.__code__, "entropy_coefficient"
        ),
        "coefficient_read_outside_plan_execution": coefficient_read_components,
        "forbidden_baseline_names_absent": not bool(forbidden_names & set(model.__dict__)),
        "G52_import_or_carry_count": 0,
        "provenance": {
            "G50": [G50_SOURCE_COMMIT, G50_EXECUTION_COMMIT, G50_ALIGNMENT_COMMIT, G50_FORMAL_BRANCH],
            "G51": [G51_SOURCE_COMMIT, G51_EXECUTION_COMMIT, G51_ALIGNED_IMPLEMENTATION_COMMIT, G51_ALIGNMENT_COMMIT, G51_FORMAL_BRANCH, G51_EXACT_RESULT],
        },
        "configuration": static_configuration_certificate(formal=False),
        "passed": bool(
            support == ["policy.log_std"]
            and len(names) == 17
            and torch.isfinite(raw_entropy)
            and g40.ENTROPY_COEFFICIENT == g19.ENTROPY_COEFFICIENT == 0.01
            and "_entropy" in plan_reads
            and not any(coefficient_read_components.values())
        ),
    }


def validate_static_certificate(value: object) -> bool:
    return bool(
        isinstance(value, Mapping)
        and set(value) == {
            "algorithm_id", "g40_entropy_callable_bound",
            "g19_coefficient_authority_exact", "g40_coefficient_authority_exact",
            "g40_global_coefficient_unmutated", "initial_log_std_exact_zero",
            "synthetic_raw_entropy_finite", "synthetic_raw_entropy_gradient_support",
            "actor_parameter_names", "actor_parameter_name_count",
            "expected_actor_parameter_name_count", "plan_binds_g40_entropy",
            "coefficient_call_per_arm_pass_owned_by_update",
            "coefficient_read_outside_plan_execution",
            "forbidden_baseline_names_absent", "G52_import_or_carry_count",
            "provenance", "configuration", "passed",
        }
        and value.get("algorithm_id") == ALGORITHM_ID
        and value.get("g40_entropy_callable_bound") is True
        and value.get("g19_coefficient_authority_exact") is True
        and value.get("g40_global_coefficient_unmutated") is True
        and value.get("initial_log_std_exact_zero") is True
        and value.get("synthetic_raw_entropy_finite") is True
        and value.get("synthetic_raw_entropy_gradient_support") == ["policy.log_std"]
        and value.get("actor_parameter_name_count") == 17
        and isinstance(value.get("actor_parameter_names"), list)
        and len(value["actor_parameter_names"]) == 17
        and value.get("expected_actor_parameter_name_count") == 17
        and value.get("plan_binds_g40_entropy") is True
        and value.get("coefficient_call_per_arm_pass_owned_by_update") is True
        and value.get("coefficient_read_outside_plan_execution")
        == {"construction": False, "collection": False, "evaluation": False, "result_selection": False}
        and value.get("G52_import_or_carry_count") == 0
        and value.get("forbidden_baseline_names_absent") is True
        and value.get("provenance") == {
            "G50": [G50_SOURCE_COMMIT, G50_EXECUTION_COMMIT, G50_ALIGNMENT_COMMIT, G50_FORMAL_BRANCH],
            "G51": [
                G51_SOURCE_COMMIT, G51_EXECUTION_COMMIT,
                G51_ALIGNED_IMPLEMENTATION_COMMIT, G51_ALIGNMENT_COMMIT,
                G51_FORMAL_BRANCH, G51_EXACT_RESULT,
            ],
        }
        and value.get("configuration") == static_configuration_certificate(formal=False)
        and value.get("passed") is True
    )


def build_final_checkpoint(
    *,
    model: G53PhaseBModel,
    optimizer: torch.optim.Optimizer,
    source_commit: str,
    arm: str,
    phase_boundary_certificate: Mapping[str, object],
) -> dict[str, object]:
    if arm not in ARMS or phase_boundary_certificate.get("passed") is not True:
        raise G53InvariantError("checkpoint_boundary_invalid")
    actor_state = {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
        if name != "policy.log_std"
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "algorithm_id": ALGORITHM_ID,
        "source_id": SOURCE_ID,
        "source_commit": source_commit,
        "kind": "final_only_actor",
        "formal": False,
        "arm": arm,
        "completed_phase_A_updates": PHASE_A_UPDATES,
        "completed_phase_B_updates": PHASE_B_UPDATES,
        "actor_state": actor_state,
        "log_std": model.log_std.detach().cpu().clone(),
        "actor_Adam_state": _optimizer_state(model, optimizer),
        "phase_boundary_certificate": dict(phase_boundary_certificate),
        "baseline_actor_read_count": 0,
        "G52_CARRY_state_count": 0,
    }
    if not validate_final_checkpoint(payload):
        raise G53InvariantError("final_checkpoint_invalid")
    return payload


def validate_final_checkpoint(value: object) -> bool:
    expected_keys = {
        "schema_version", "algorithm_id", "source_id", "source_commit", "kind",
        "formal", "arm", "completed_phase_A_updates", "completed_phase_B_updates",
        "actor_state", "log_std", "actor_Adam_state", "phase_boundary_certificate",
        "baseline_actor_read_count", "G52_CARRY_state_count",
    }
    if not isinstance(value, Mapping) or set(value) != expected_keys:
        return False
    actor_state = value.get("actor_state")
    adam = value.get("actor_Adam_state")
    forbidden = ("credit_baselines", "slow_critic", ".critic.", "delayed_residual")
    expected_actor_names = g50._PHASE_B_ACTOR_STATE_KEYS
    expected_adam_names = g50._PHASE_B_ADAM_KEYS
    with torch.random.fork_rng():
        shell_source = g40.make_model(8, initialization_seed=0)
        with torch.no_grad():
            shell_source.log_std.zero_()
        shell = g50.G50PhaseBProjection(
            g51.G51NoBaselinePhaseAProjection(shell_source)
        )
        expected_state = shell.state_dict()
    def exact_tensor(row: object, expected: torch.Tensor) -> bool:
        return bool(
            isinstance(row, torch.Tensor)
            and row.shape == expected.shape
            and row.dtype == expected.dtype
            and bool(torch.isfinite(row).all())
        )
    boundary = value.get("phase_boundary_certificate")
    boundary_valid = bool(
        isinstance(boundary, Mapping)
        and set(boundary) == {
            "completed_phase_A_updates", "retained_actor_and_log_std_bytes_equal",
            "slow_critic_deleted_at_common_boundary", "baseline_absent",
            "forbidden_state_keys", "phase_A_optimizer_disposed",
            "projection_optimizer_steps", "projection_RNG_consumption", "passed",
        }
        and boundary.get("completed_phase_A_updates") == PHASE_A_UPDATES
        and boundary.get("retained_actor_and_log_std_bytes_equal") is True
        and boundary.get("slow_critic_deleted_at_common_boundary") is True
        and boundary.get("baseline_absent") is True
        and boundary.get("forbidden_state_keys") == []
        and boundary.get("phase_A_optimizer_disposed") is True
        and boundary.get("projection_optimizer_steps") == 0
        and boundary.get("projection_RNG_consumption") == 0
        and boundary.get("passed") is True
    )
    adam_valid = bool(
        isinstance(adam, Mapping)
        and tuple(adam) == expected_adam_names
        and all(
            isinstance(adam[name], Mapping)
            and set(adam[name]) == {"step", "exp_avg", "exp_avg_sq"}
            and isinstance(adam[name]["step"], torch.Tensor)
            and adam[name]["step"].ndim == 0
            and adam[name]["step"].dtype == torch.float32
            and bool(torch.isfinite(adam[name]["step"]))
            and float(
                adam[name]["step"].detach().cpu()
            ) == float(PHASE_B_UPDATES * PPO_PASSES)
            and exact_tensor(adam[name]["exp_avg"], expected_state[name])
            and exact_tensor(adam[name]["exp_avg_sq"], expected_state[name])
            for name in expected_adam_names
        )
    )
    return bool(
        value.get("schema_version") == SCHEMA_VERSION
        and value.get("algorithm_id") == ALGORITHM_ID
        and value.get("source_id") == SOURCE_ID
        and isinstance(value.get("source_commit"), str)
        and len(value["source_commit"]) == 40
        and all(character in "0123456789abcdef" for character in value["source_commit"])
        and value.get("kind") == "final_only_actor"
        and value.get("formal") is False
        and value.get("arm") in ARMS
        and value.get("completed_phase_A_updates") == PHASE_A_UPDATES
        and value.get("completed_phase_B_updates") == PHASE_B_UPDATES
        and isinstance(actor_state, Mapping)
        and tuple(actor_state) == expected_actor_names
        and not any(token in name for name in actor_state for token in forbidden)
        and all(exact_tensor(actor_state[name], expected_state[name]) for name in expected_actor_names)
        and exact_tensor(value.get("log_std"), expected_state["policy.log_std"])
        and adam_valid
        and boundary_valid
        and value.get("baseline_actor_read_count") == 0
        and value.get("G52_CARRY_state_count") == 0
    )


def load_final_checkpoint_model(
    checkpoint: Mapping[str, object], *, member_capacity: int
) -> G53PhaseBModel:
    if not validate_final_checkpoint(checkpoint):
        raise G53InvariantError("checkpoint_reload_validation_failed")
    fresh = g40.make_model(int(member_capacity), initialization_seed=0)
    phase_A = g51.G51NoBaselinePhaseAProjection(fresh)
    model = g50.G50PhaseBProjection(phase_A)
    state = dict(checkpoint["actor_state"])  # type: ignore[arg-type]
    state["policy.log_std"] = checkpoint["log_std"]
    model.load_state_dict(state, strict=True)
    return model


def serialize_diagnostics(value: Mapping[str, object]) -> str:
    def safe(row: object) -> object:
        if isinstance(row, torch.Tensor):
            return {"dtype": str(row.dtype), "shape": list(row.shape), "sha256": _tensor_digest(row)}
        if isinstance(row, Mapping):
            return {str(key): safe(item) for key, item in row.items()}
        if isinstance(row, (list, tuple)):
            return [safe(item) for item in row]
        return row
    return json.dumps(safe(value), sort_keys=True, separators=(",", ":"))
