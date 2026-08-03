"""Frozen OR/DUM/EHC event-held commitment package for noncalendar G0."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import random
import tempfile
from time import perf_counter
from typing import Any, Iterable, Literal, Mapping

import numpy as np
import torch
import torch.nn.functional as F

from ha_ctse_process.dynamic_roster_direct import (
    LEARNING_RATE,
    PPO_PASSES,
    model_state_copy,
    nested_state_maximum_difference,
)
from ha_ctse_process.dynamic_roster_testbed import ACTION_COUNT, HORIZON, MAX_LIFECYCLES, OBSERVATION_DIM
from ha_ctse_process.event_commitment_rng import (
    OPPORTUNITY_SUPPORT,
    RNG_NAMES,
    _float32_payload,
    _raw_event_trace_digest,
    _seed,
    authoritative_seed_map,
    collection_rng_schedules,
    make_rng_binding,
    make_training_state,
    owned_rng_states,
    replay_rng_schedule_arrays,
    replay_rng_schedule_end_state,
    validate_rng_binding,
)
from ha_ctse_process.event_commitment_types import (
    ArmName,
    CollectionCursor,
    CommitmentArm,
    EVENT_INPUT_DIM,
    EventTrajectory,
    LifecycleState,
    MARK_DIM,
    SegmentRecord,
    TrainingState,
)
from ha_ctse_process.event_commitment_collector import (
    CREATE,
    KEEP,
    RENEW,
    _AuditRowStream,
    collect_trajectory,
)
from ha_ctse_process.event_commitment_replay import (
    validate_replay,
)
from ha_ctse_process.event_commitment_optimizer import (
    EVENT_ENTROPY_COEFFICIENT,
    _gradient_summaries,
    _optimizer_pass_record,
    _pack_trajectory_once,
    compute_gae,
    optimize_update,
    optimizer_ownership_manifest,
)
from ha_ctse_process.event_commitment_audit import (
    _nested_equal,
    _rng_states,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    ADDED_PARAMETER_COUNT,
    CHECKPOINT_KIND,
    CHECKPOINT_SCHEMA_VERSION,
    CAUSAL_AUDIT_CONTINUOUS_ATOL,
    EVENT_JOINT_FACTOR_COUNT,
    EVENT_SEED,
    FORMAL_EVAL_EPISODES,
    FORMAL_NUM_ENVS,
    FORMAL_TRAIN_EPISODES,
    FORMAL_TRANSITIONS_PER_ARM,
    FORMAL_UPDATES,
    HELD_OUT_EVAL_TASK_SEED,
    IID_EVAL_TASK_SEED,
    MARK_SEED,
    MODEL_INITIALIZATION_SEED,
    OPPORTUNITY_SEED,
    PARAMETER_COUNT,
    REGISTERED_CONTRACT,
    REPLAY_COMPONENT_FIELDS,
    REPLAY_EVENT_JOINT_RATIO_FIELDS,
    REPLAY_EXACT_FIELDS,
    REPLAY_JOINT_FIELDS,
    REPLAY_JOINT_RECORD_FIELDS,
    REPLAY_LOG_COMPONENT_ATOL,
    REPLAY_LOG_COMPONENT_FIELDS,
    REPLAY_LOG_COMPONENT_RTOL,
    REPLAY_LOG_RATIO_DRIFT_CAP,
    REPLAY_RECORD_SCHEMA_VERSION,
    REPLAY_STATE_ATOL,
    REPLAY_STATE_FIELDS,
    REPLAY_WORST_RECORD_FIELDS,
    RESUME_TOLERANCE,
    RNG_BINDING_SCHEMA_VERSION,
    TRAIN_ORDER_SEED,
    TRAIN_TASK_SEED,
    TRAIN_ACTION_SEED,
    float32_reduction_gamma,
    frontier_order,
    make_noncalendar_ledger,
    make_rng,
    registered_contract,
    require_active_backend_device,
    NoncalendarLedger,
    NoncalendarTrackingEnv,
    TrackingOutcome,
)

def initialize_arms(
    device: torch.device,
    *,
    replicate: int = 0,
    event_seed: int = EVENT_SEED,
    mark_seed: int = MARK_SEED,
) -> tuple[dict[ArmName, CommitmentArm], dict[ArmName, torch.optim.Optimizer], dict[ArmName, torch.optim.Optimizer | None]]:
    # Every arm of every replicate is constructed here, so this is the single
    # place where a device that disagrees with the activated execution backend
    # can be refused before any parameter exists on it.
    require_active_backend_device(device)
    cpu_rng = torch.get_rng_state().clone()
    cuda_rngs = [value.clone() for value in torch.cuda.get_rng_state_all()] if torch.cuda.is_available() else []
    try:
        torch.manual_seed(_seed(MODEL_INITIALIZATION_SEED, replicate))
        ordinary = CommitmentArm("OR")
        base_state = deepcopy(ordinary.base.state_dict())
        dum = CommitmentArm("DUM")
        dum.base.load_state_dict(base_state, strict=True)
        assert dum.W_z is not None and dum.event_head is not None and dum.mark_head is not None
        torch.manual_seed(_seed(event_seed, replicate))
        dum.W_z.reset_parameters()
        dum.event_head.reset_parameters()
        torch.manual_seed(_seed(mark_seed, replicate))
        dum.mark_head.reset_parameters()
        ehc = CommitmentArm("EHC")
        ehc.base.load_state_dict(base_state, strict=True)
        assert ehc.W_z is not None and ehc.event_head is not None and ehc.mark_head is not None
        ehc.W_z.load_state_dict(deepcopy(dum.W_z.state_dict()), strict=True)
        ehc.event_head.load_state_dict(deepcopy(dum.event_head.state_dict()), strict=True)
        ehc.mark_head.load_state_dict(deepcopy(dum.mark_head.state_dict()), strict=True)
    finally:
        torch.set_rng_state(cpu_rng)
        if torch.cuda.is_available():
            torch.cuda.set_rng_state_all(cuda_rngs)
    arms: dict[ArmName, CommitmentArm] = {"OR": ordinary.to(device), "DUM": dum.to(device), "EHC": ehc.to(device)}
    base_optimizers = {
        name: torch.optim.Adam(arm.base_optimizer_parameters(), lr=LEARNING_RATE, eps=1e-5, weight_decay=0.0)
        for name, arm in arms.items()
    }
    event_optimizers: dict[ArmName, torch.optim.Optimizer | None] = {
        "OR": None,
        "DUM": torch.optim.Adam(arms["DUM"].event_parameters(), lr=LEARNING_RATE, eps=1e-5, weight_decay=0.0),
        "EHC": torch.optim.Adam(arms["EHC"].event_parameters(), lr=LEARNING_RATE, eps=1e-5, weight_decay=0.0),
    }
    if ordinary.base_parameter_count != PARAMETER_COUNT:
        raise RuntimeError("ordinary source parameter count drift")
    if dum.added_parameter_count != ADDED_PARAMETER_COUNT or ehc.added_parameter_count != ADDED_PARAMETER_COUNT:
        raise RuntimeError("commitment addition parameter count drift")
    return arms, base_optimizers, event_optimizers


def action_distribution_tv(
    logits_natural: torch.Tensor, logits_perm: torch.Tensor
) -> torch.Tensor:
    """Primitive action-distribution total variation from two logit vectors.

    `I_TV = 0.5 * sum_a |pi(a) - pi(a_perm)|`, where `pi`/`pi_perm` are the
    softmax distributions induced by `logits_natural`/`logits_perm` along
    their last dimension. This is exactly zero whenever the two logit
    vectors differ only by a constant (softmax is shift-invariant), and it
    always lies in `[0, 1]` because it is the total-variation distance
    between two categorical distributions over the same three actions.
    """

    pi_natural = torch.softmax(logits_natural, dim=-1)
    pi_perm = torch.softmax(logits_perm, dim=-1)
    return 0.5 * torch.abs(pi_natural - pi_perm).sum(dim=-1)


def batched_natural_and_permuted_action_tv(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Trajectory-batched teacher-forced `I_TV` with one AR-position loop.

    Time and environment are flattened into one batch. The only loop is the
    genuine autoregressive primitive position; focal-key gathers, prefix
    updates, ascending-key cyclic mark permutation and both W_z evaluations
    remain on device. The returned dense tensor and eligibility mask have
    shape `(time, environment, lifecycle)` and perform no host conversion.
    """

    shape = trajectory.active_mask.shape
    if arm.arm != "EHC" or arm.W_z is None:
        return (
            torch.zeros(shape, dtype=torch.float32, device=device),
            torch.zeros(shape, dtype=torch.bool, device=device),
        )
    time_steps, environments, lifecycles = shape
    batch = time_steps * environments
    observations = trajectory.observations.to(device).reshape(
        batch, lifecycles, OBSERVATION_DIM
    )
    active = trajectory.active_mask.to(device).reshape(batch, lifecycles)
    order = trajectory.orders.to(device).reshape(batch, lifecycles)
    hidden_before = trajectory.hidden_before.to(device).reshape(
        batch, lifecycles, -1
    )
    natural_actions = trajectory.actions.to(device).reshape(batch, lifecycles)
    z = trajectory.primitive_z.to(device).reshape(batch, lifecycles, MARK_DIM)
    batch_indices = torch.arange(batch, device=device)
    with torch.no_grad():
        prepared = arm.base.prepare_step(
            observations=observations, active_mask=active, validated=True
        )
        active_counts = active.sum(dim=1)
        prefix = torch.zeros(
            (batch, ACTION_COUNT), dtype=observations.dtype, device=device
        )
        base_logits = torch.zeros(
            (batch, lifecycles, ACTION_COUNT),
            dtype=observations.dtype,
            device=device,
        )
        for position in range(lifecycles):
            valid = position < active_counts
            focal = order[:, position].clamp(0, lifecycles - 1)
            local_embedding = prepared.member_embeddings[batch_indices, focal]
            local_hidden = hidden_before[batch_indices, focal]
            candidate_hidden = arm.base.actor_rnn(
                torch.cat((local_embedding, prepared.context, prefix), dim=-1),
                local_hidden,
            )
            logits = arm.base.action_head(
                torch.cat((candidate_hidden, prefix), dim=-1)
            )
            previous = base_logits[batch_indices, focal]
            base_logits[batch_indices, focal] = torch.where(
                valid.unsqueeze(-1), logits, previous
            )
            selected = natural_actions[batch_indices, focal].clamp(0, ACTION_COUNT - 1)
            prefix = prefix + F.one_hot(
                selected, num_classes=ACTION_COUNT
            ).to(prefix.dtype) * valid.unsqueeze(-1)

        keys = torch.arange(lifecycles, device=device)
        candidates = keys.view(1, 1, lifecycles)
        targets = keys.view(1, lifecycles, 1)
        lower_active = active.unsqueeze(1) & (candidates < targets)
        lower_key = torch.where(
            lower_active, candidates, torch.full_like(candidates, -1)
        ).amax(dim=-1)
        maximum_active = torch.where(
            active, keys.view(1, lifecycles), torch.full_like(active, -1, dtype=torch.long)
        ).amax(dim=-1, keepdim=True)
        predecessor = torch.where(lower_key >= 0, lower_key, maximum_active)
        predecessor = predecessor.clamp_min(0)
        permuted_z = z.gather(
            1, predecessor.unsqueeze(-1).expand(-1, -1, MARK_DIM)
        )
        natural_logits = base_logits + arm.W_z(z.detach())
        permuted_logits = base_logits + arm.W_z(permuted_z.detach())
        tv = action_distribution_tv(natural_logits, permuted_logits)
        eligible = active & active_counts.unsqueeze(-1).ge(2)
        tv = torch.where(eligible, tv, torch.zeros_like(tv))
    return (
        tv.reshape(time_steps, environments, lifecycles),
        eligible.reshape(time_steps, environments, lifecycles),
    )


def runtime_rng_snapshot() -> dict[str, Any]:
    return {
        "python": deepcopy(random.getstate()),
        "numpy": deepcopy(np.random.get_state()),
        "torch_cpu": torch.get_rng_state().clone(),
        "torch_cuda": [
            value.clone() for value in torch.cuda.get_rng_state_all()
        ] if torch.cuda.is_available() else [],
    }


def runtime_rng_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _nested_equal(dict(left), dict(right))


def save_checkpoint(
    path: Path,
    *,
    arm: CommitmentArm,
    base_optimizer: torch.optim.Optimizer,
    event_optimizer: torch.optim.Optimizer | None,
    state: TrainingState,
) -> None:
    if state.pending_cursor is not None:
        raise ValueError("checkpoint requires an empty rollout buffer")
    if state.arm != arm.arm or (event_optimizer is None) != (arm.arm == "OR"):
        raise ValueError("checkpoint arm/optimizer ownership mismatch")
    if state.seed_map != authoritative_seed_map(state.profile, state.replicate):
        raise ValueError("checkpoint seed map drift")
    path.parent.mkdir(parents=True, exist_ok=True)
    global_state = runtime_rng_snapshot()
    payload = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "kind": CHECKPOINT_KIND,
        "contract": registered_contract(),
        "arm": arm.arm,
        "replicate": state.replicate,
        "profile": state.profile,
        "seed_map": dict(state.seed_map),
        "model_state": arm.state_dict(),
        "base_optimizer_state": base_optimizer.state_dict(),
        "event_optimizer_state": (
            None if event_optimizer is None else event_optimizer.state_dict()
        ),
        "completed_update": state.completed_update,
        "next_episode_id": state.next_episode_id,
        "exposure": {
            "base": state.base_optimizer_steps,
            "event": state.event_optimizer_steps,
        },
        "normalizers": None,
        "collector": {
            "position": 0,
            "pending_environments": [],
            "membership_snapshots": [],
            "accumulators": [],
            "lifecycles": [],
            "segments": [],
            "masks": [],
        },
        "python_rng": global_state["python"],
        "numpy_global_rng": global_state["numpy"],
        "torch_cpu_rng": global_state["torch_cpu"],
        "torch_cuda_rng": global_state["torch_cuda"],
        "owned_rngs": _rng_states(state),
    }
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.",
            suffix=".tmp", delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            torch.save(payload, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def load_checkpoint(
    path: Path,
    *,
    device: torch.device,
    expected_arm: ArmName,
    expected_replicate: int,
    formal_evaluation: bool = False,
) -> tuple[
    CommitmentArm,
    torch.optim.Optimizer,
    torch.optim.Optimizer | None,
    TrainingState,
]:
    require_active_backend_device(device)
    payload = torch.load(path, map_location="cpu", weights_only=False)
    required = {
        "schema_version", "kind", "contract", "arm", "replicate", "profile",
        "seed_map", "model_state", "base_optimizer_state",
        "event_optimizer_state", "completed_update", "next_episode_id",
        "exposure", "normalizers", "collector", "python_rng",
        "numpy_global_rng", "torch_cpu_rng", "torch_cuda_rng", "owned_rngs",
    }
    if set(payload) != required:
        raise ValueError("checkpoint key set mismatch")
    if (
        payload["schema_version"] != CHECKPOINT_SCHEMA_VERSION
        or payload["kind"] != CHECKPOINT_KIND
        or payload["contract"] != registered_contract()
    ):
        raise ValueError("checkpoint registered contract mismatch")
    if payload["arm"] != expected_arm or int(payload["replicate"]) != int(expected_replicate):
        raise ValueError("checkpoint expected arm/replicate mismatch")
    profile = payload["profile"]
    if profile not in ("train", "iid", "held_out"):
        raise ValueError("checkpoint profile mismatch")
    expected_seed_map = authoritative_seed_map(profile, expected_replicate)
    if payload["seed_map"] != expected_seed_map:
        raise ValueError("checkpoint seed map mismatch")
    if set(payload["owned_rngs"]) != set(RNG_NAMES):
        raise ValueError("checkpoint owned-RNG key set mismatch")
    event_state = payload["event_optimizer_state"]
    if (expected_arm == "OR" and event_state is not None) or (
        expected_arm != "OR" and event_state is None
    ):
        raise ValueError("checkpoint event optimizer ownership mismatch")
    if payload["normalizers"] is not None or payload["collector"] != {
        "position": 0,
        "pending_environments": [],
        "membership_snapshots": [],
        "accumulators": [],
        "lifecycles": [],
        "segments": [],
        "masks": [],
    }:
        raise ValueError("checkpoint boundary is not empty")
    completed_update = int(payload["completed_update"])
    next_episode_id = int(payload["next_episode_id"])
    base_steps = int(payload["exposure"]["base"])
    event_steps = int(payload["exposure"]["event"])
    expected_event_steps = 0 if expected_arm == "OR" else completed_update * PPO_PASSES
    if base_steps != completed_update * PPO_PASSES or event_steps != expected_event_steps:
        raise ValueError("checkpoint optimizer exposure mismatch")
    if formal_evaluation and (
        profile != "train"
        or completed_update != FORMAL_UPDATES
        or next_episode_id != FORMAL_TRAIN_EPISODES
        or base_steps != FORMAL_UPDATES * PPO_PASSES
        or event_steps != (0 if expected_arm == "OR" else FORMAL_UPDATES * PPO_PASSES)
    ):
        raise ValueError("formal evaluation accepts only the registered update-250 boundary")
    if len(payload["torch_cuda_rng"]) != (
        torch.cuda.device_count() if torch.cuda.is_available() else 0
    ):
        raise ValueError("checkpoint CUDA RNG device-set mismatch")

    arms, base_optimizers, event_optimizers = initialize_arms(
        device, replicate=expected_replicate
    )
    arm = arms[expected_arm]
    base_optimizer = base_optimizers[expected_arm]
    event_optimizer = event_optimizers[expected_arm]
    arm.load_state_dict(payload["model_state"], strict=True)
    base_optimizer.load_state_dict(payload["base_optimizer_state"])
    if event_optimizer is not None:
        event_optimizer.load_state_dict(event_state)
    for optimizer in (base_optimizer, event_optimizer):
        if optimizer is not None:
            for optimizer_state in optimizer.state.values():
                for key, value in optimizer_state.items():
                    if isinstance(value, torch.Tensor):
                        optimizer_state[key] = value.to(device)
    state = make_training_state(
        expected_arm, expected_replicate, profile=profile
    )
    state.completed_update = completed_update
    state.next_episode_id = next_episode_id
    state.base_optimizer_steps = base_steps
    state.event_optimizer_steps = event_steps
    for name in RNG_NAMES:
        state.rngs[name].bit_generator.state = deepcopy(payload["owned_rngs"][name])
    random.setstate(payload["python_rng"])
    np.random.set_state(payload["numpy_global_rng"])
    torch.set_rng_state(payload["torch_cpu_rng"])
    if torch.cuda.is_available():
        torch.cuda.set_rng_state_all(payload["torch_cuda_rng"])
    return arm, base_optimizer, event_optimizer, state


def compare_continuations(
    left_arm: CommitmentArm,
    right_arm: CommitmentArm,
    left_trajectory: EventTrajectory,
    right_trajectory: EventTrajectory,
    left_optimizer: torch.optim.Optimizer,
    right_optimizer: torch.optim.Optimizer,
    left_event_optimizer: torch.optim.Optimizer | None,
    right_event_optimizer: torch.optim.Optimizer | None,
    left_state: TrainingState,
    right_state: TrainingState,
    left_global_rng: Mapping[str, Any],
    right_global_rng: Mapping[str, Any],
) -> dict[str, Any]:
    discrete_names = (
        "active_mask", "orders", "actions", "terminal", "event_kind",
        "event_categorical_actions", "event_cat_mask", "event_mark_mask",
        "membership_epoch", "segment_id", "q_before",
    )
    continuous_names = (
        "observations", "old_log_probs", "old_values", "hidden_before",
        "hidden_after", "prefix_counts", "primitive_z", "event_inputs",
        "event_u", "event_z_pre", "event_new_z", "event_old_cat_logp",
        "event_old_mark_component_logp", "event_old_joint_logp",
        "candidate_u", "candidate_z",
    )
    discrete_equal = all(
        torch.equal(getattr(left_trajectory, name), getattr(right_trajectory, name))
        for name in discrete_names
    )
    continuous_error = max(
        float(
            torch.max(
                torch.abs(
                    getattr(left_trajectory, name)
                    - getattr(right_trajectory, name)
                )
            ).detach().cpu()
        )
        for name in continuous_names
    )
    lifecycle_equal = (
        left_trajectory.ledger_ids == right_trajectory.ledger_ids
        and left_trajectory.outcomes == right_trajectory.outcomes
        and left_trajectory.segments == right_trajectory.segments
    )
    return {
        "discrete_equal": discrete_equal,
        "lifecycle_equal": lifecycle_equal,
        "owned_rng_equal": _nested_equal(
            _rng_states(left_state), _rng_states(right_state)
        ),
        "global_rng_equal": runtime_rng_equal(left_global_rng, right_global_rng),
        "continuous_error": continuous_error,
        "model_error": nested_state_maximum_difference(
            left_arm.state_dict(), right_arm.state_dict()
        ),
        "base_optimizer_error": nested_state_maximum_difference(
            left_optimizer.state_dict(), right_optimizer.state_dict()
        ),
        "event_optimizer_error": nested_state_maximum_difference(
            None if left_event_optimizer is None else left_event_optimizer.state_dict(),
            None if right_event_optimizer is None else right_event_optimizer.state_dict(),
        ),
    }

def factor_counts(trajectory: EventTrajectory) -> dict[str, int]:
    return {"create": int((trajectory.event_kind == CREATE).sum()), "keep": int((trajectory.event_kind == KEEP).sum()), "renew": int((trajectory.event_kind == RENEW).sum()), "categorical": int(trajectory.event_cat_mask.sum()), "mark": int(trajectory.event_mark_mask.sum())}


def parameter_and_optimizer_counts(arm: CommitmentArm, base_optimizer: torch.optim.Optimizer, event_optimizer: torch.optim.Optimizer | None) -> dict[str, int]:
    optimizer_count = lambda opt: 0 if opt is None else sum(p.numel() for group in opt.param_groups for p in group["params"])
    return {"base_model": arm.base_parameter_count, "added_model": arm.added_parameter_count, "base_optimizer": optimizer_count(base_optimizer), "event_optimizer": optimizer_count(event_optimizer)}
