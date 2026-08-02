"""Frozen OR/DUM/EHC event-held commitment package for noncalendar G0."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import random
import tempfile
from time import perf_counter
from typing import Any, Iterable, Literal, Mapping
import zlib

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

from ha_ctse_process.dynamic_roster_direct import (
    ENTROPY_COEFFICIENT,
    GAE_LAMBDA,
    GAMMA,
    GRADIENT_CLIP,
    LEARNING_RATE,
    PPO_CLIP,
    PPO_PASSES,
    VALUE_CLIP,
    VALUE_COEFFICIENT,
    model_state_copy,
    nested_state_maximum_difference,
)
from ha_ctse_process.dynamic_roster_testbed import ACTION_COUNT, HORIZON, MAX_LIFECYCLES, OBSERVATION_DIM
from ha_ctse_process.event_commitment_rng import (
    OPPORTUNITY_SUPPORT,
    RNG_NAMES,
    _canonical_json_digest,
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
    _replay_event_heads,
    _replay_primitive,
    validate_replay,
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
    OPTIMIZER_CLIP_EPSILON,
    OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
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

EVENT_ENTROPY_COEFFICIENT = 0.01
AUDIT_BRANCHES = (
    "KEEP_HELD_MARK",
    "RENEW_DERANGED_MARK",
    "RENEW_CANDIDATE_MARK",
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


# Streams a fork branch owns. Only `opportunity` is ever consumed: forking
# supports deterministic policy decisions only (a stochastic collection's
# realized event/mark/primitive variates are not recoverable from the
# record), and `collect_trajectory`'s deterministic path draws no `event`,
# `mark` or `primitive` variates at all. Those three streams -- and with
# them the dtype-agreement check in `_AuditStream.take` and the
# float32/float64 distinction it guards -- are registered groundwork for
# stochastic forking, not exercised code.
AUDIT_STREAM_NAMES = ("opportunity", "event", "mark", "primitive")


class _AuditStream:
    """One fork-owned variate stream shared by both branches of a pair.

    The stream owns exactly one generator and one realized-variate log. The
    first consumer that reaches a flat position advances the generator once
    and appends the realized values; every later consumer replays the same
    values from its own position. Both branches of a fork therefore consume
    *identical* realized variates without either giving them independent
    generators or letting them advance one generator in turn.

    `script` pre-fills the log with variates recovered from the collected
    record (used for the `opportunity` stream, whose realized schedule is
    recoverable from `q_before` and is action-independent).
    """

    def __init__(
        self,
        name: str,
        generator: np.random.Generator,
        *,
        script: Iterable[int] | None = None,
        label: str = "",
    ) -> None:
        self.name = name
        self.generator = generator
        # Names the fork coordinate this stream belongs to, so an exhausted
        # script reports which opportunity it failed on.
        self.label = str(label)
        self.scripted = script is not None
        self.values: list[Any] = [] if script is None else [int(v) for v in script]
        self.dtype: np.dtype | None = None

    def take(self, position: int, count: int, produce: Any, dtype: Any) -> np.ndarray:
        if position < 0 or count < 0:
            raise ValueError("fork stream position/count must be non-negative")
        requested = np.dtype(dtype)
        if not self.scripted:
            # One stream is materialized exactly once and replayed, so every
            # consumer must draw it in the same precision: NumPy's float32
            # path consumes a different number of bits per variate than its
            # float64 path, and the two produce different values.
            if self.dtype is None:
                self.dtype = requested
            elif self.dtype != requested:
                raise RuntimeError(
                    f"fork {self.name} stream dtype changed "
                    f"{self.dtype} -> {requested}"
                )
        while len(self.values) < position + count:
            if self.scripted:
                raise RuntimeError(
                    f"fork {self.name} script exhausted{self.label}"
                )
            missing = position + count - len(self.values)
            drawn = np.asarray(produce(self.generator, missing, requested))
            if drawn.size <= 0:
                raise RuntimeError(f"fork {self.name} draw produced no variates")
            if drawn.dtype != requested:
                raise RuntimeError(
                    f"fork {self.name} draw returned {drawn.dtype}, not {requested}"
                )
            self.values.extend(drawn.reshape(-1).tolist())
        return np.asarray(self.values[position : position + count])


class _AuditStreamView:
    """One branch's own position/consumption bookkeeping over shared streams."""

    def __init__(
        self,
        streams: Mapping[str, _AuditStream],
        positions: Mapping[str, int] | None = None,
    ) -> None:
        self.streams = dict(streams)
        self.positions = (
            {name: 0 for name in self.streams}
            if positions is None
            else {name: int(positions[name]) for name in self.streams}
        )
        self.calls = {name: 0 for name in self.streams}
        self.consumed: dict[str, list[Any]] = {name: [] for name in self.streams}

    def take(self, name: str, count: int, produce: Any, dtype: Any) -> np.ndarray:
        values = self.streams[name].take(self.positions[name], count, produce, dtype)
        self.positions[name] += int(count)
        self.calls[name] += 1
        narrowed = values.astype(dtype)
        self.consumed[name].extend(narrowed.reshape(-1).tolist())
        return narrowed


class _AuditGenerator:
    """`np.random.Generator` facade over one branch view of one fork stream."""

    def __init__(self, view: _AuditStreamView, name: str) -> None:
        self._view = view
        self._name = name

    @staticmethod
    def _shape(size: Any) -> tuple[int, ...]:
        if size is None:
            return ()
        if isinstance(size, tuple):
            return tuple(int(v) for v in size)
        return (int(size),)

    def _values(self, size: Any, produce: Any, dtype: Any) -> tuple[np.ndarray, tuple[int, ...]]:
        shape = self._shape(size)
        count = int(np.prod(shape)) if shape else 1
        return self._view.take(self._name, count, produce, dtype), shape

    def random(self, size: Any = None, dtype: Any = np.float64) -> Any:
        values, shape = self._values(
            size, lambda generator, n, dt: generator.random(n, dtype=dt), dtype
        )
        return values.reshape(shape) if shape else values[0]

    def standard_normal(self, size: Any = None, dtype: Any = np.float64) -> Any:
        values, shape = self._values(
            size,
            lambda generator, n, dt: generator.standard_normal(n, dtype=dt),
            dtype,
        )
        return values.reshape(shape) if shape else values[0]

    def choice(self, a: Any, size: Any = None) -> Any:
        support = np.asarray(a)
        values, shape = self._values(
            size,
            lambda generator, n, _dt: generator.choice(support, size=n),
            np.int64,
        )
        if not bool(np.isin(values, support).all()):
            raise RuntimeError(f"fork {self._name} variate outside registered support")
        return values.reshape(shape) if shape else values[0]


def _audit_opportunity_script(
    trajectory: EventTrajectory, *, fallback: np.random.Generator
) -> tuple[list[int], dict[tuple[int, int, int], int], list[int]]:
    """Recover the realized opportunity schedule for a collected batch.

    Every request assigns `life.q` from one `opportunity` draw and every
    subsequent *active* step of that lifecycle decrements it by one, so the
    value assigned at `(env_index, time, key)` is
    `q_before[next active step] + 1`. The schedule is action-independent, so
    replaying it drives both branches of a fork and the factual continuation
    with the same realized variates. Trailing assignments with no later
    active step are unobservable (the lifecycle never requests again) and
    are filled from `fallback`.

    The schedule spans the *whole* collected width, because the collector
    draws one `choice` of size `len(requests)` per physical step over the
    batch, ordered env-major and then in frontier order within an env
    (`active_keys` is frontier-sorted). Returns that flat schedule, the flat
    index of each `(env_index, time, key)` request, and the cumulative
    request count per step.
    """

    active = trajectory.active_mask.detach().cpu().numpy()
    q_before = trajectory.q_before.detach().cpu().numpy()
    orders = trajectory.orders.detach().cpu().numpy()
    kinds = trajectory.event_kind.detach().cpu().numpy()
    steps = trajectory.time_steps
    env_count = int(trajectory.active_mask.shape[1])
    values: list[int] = []
    index_of: dict[tuple[int, int, int], int] = {}
    cumulative: list[int] = []
    support = set(int(v) for v in OPPORTUNITY_SUPPORT)
    for step in range(steps):
        for env_index in range(env_count):
            for raw in orders[step, env_index]:
                focal = int(raw)
                if focal < 0:
                    continue
                if not bool(active[step, env_index, focal]):
                    raise RuntimeError("frontier order lists an inactive lifecycle")
                requested = int(q_before[step, env_index, focal]) <= 0
                if requested != bool(int(kinds[step, env_index, focal]) != 0):
                    raise RuntimeError("recorded request schedule contradicts q_before")
                if not requested:
                    continue
                assigned: int | None = None
                for later in range(step + 1, steps):
                    if bool(active[later, env_index, focal]):
                        assigned = int(q_before[later, env_index, focal]) + 1
                        break
                if assigned is None:
                    assigned = int(fallback.choice(OPPORTUNITY_SUPPORT))
                if assigned not in support:
                    raise RuntimeError("recovered opportunity value outside support")
                index_of[(env_index, step, focal)] = len(values)
                values.append(assigned)
        cumulative.append(len(values))
    return values, index_of, cumulative


def _audit_cursor(
    ledgers: tuple[NoncalendarLedger, ...],
    episode_ids: tuple[int, ...],
    device: torch.device,
) -> CollectionCursor:
    return CollectionCursor(
        episode_ids=tuple(int(v) for v in episode_ids),
        ledgers=tuple(ledgers),
        environments=[NoncalendarTrackingEnv(ledger) for ledger in ledgers],
        hidden=torch.zeros((len(ledgers), MAX_LIFECYCLES, 32), device=device),
        lifecycles=[{} for _ in ledgers],
        segments=[[] for _ in ledgers],
    )


def _clone_audit_cursor(cursor: CollectionCursor) -> CollectionCursor:
    """Independent branch state built on the environment snapshot contract."""

    return CollectionCursor(
        episode_ids=cursor.episode_ids,
        ledgers=cursor.ledgers,
        environments=[
            NoncalendarTrackingEnv.from_snapshot_state(env.snapshot_state())
            for env in cursor.environments
        ],
        hidden=cursor.hidden.detach().clone(),
        lifecycles=[
            {
                key: LifecycleState(
                    life.membership_epoch,
                    life.z.detach().clone(),
                    life.q,
                    life.segment_id,
                    life.segment_start_active_step,
                    life.active_steps,
                    life.non_create_opportunities,
                    life.spell_opportunity_count,
                )
                for key, life in table.items()
            }
            for table in cursor.lifecycles
        ],
        segments=[list(records) for records in cursor.segments],
    )


def _audit_branch_state(
    arm_name: ArmName,
    replicate: int,
    profile: Literal["train", "iid", "held_out"],
    view: _AuditStreamView,
) -> TrainingState:
    rngs: dict[str, Any] = {
        name: np.random.default_rng(0) for name in RNG_NAMES if name not in AUDIT_STREAM_NAMES
    }
    for name in AUDIT_STREAM_NAMES:
        rngs[name] = _AuditGenerator(view, name)
    return TrainingState(
        arm=arm_name,
        replicate=int(replicate),
        profile=profile,
        seed_map=authoritative_seed_map(profile, int(replicate)),
        rngs=rngs,
    )


def _branch_boundary(cursor: CollectionCursor, env_index: int) -> dict[str, Any]:
    """Ledger-free, comparable description of one branch's fork-point state."""

    environment = cursor.environments[env_index]
    return {
        "members": deepcopy(environment.members),
        "time": int(environment.time),
        "counters": (
            int(environment.tracking_quarter_units),
            int(environment.active_rows),
            int(environment.completed_segments),
            int(environment.eligible_segments),
        ),
        "roster_sizes": tuple(environment.roster_sizes),
        "reward_trace": tuple(environment.reward_trace),
        "terminated": bool(environment._terminated),
        "hidden": cursor.hidden[env_index].detach().cpu().clone(),
        "lifecycles": {
            key: {
                "membership_epoch": int(life.membership_epoch),
                "z": life.z.detach().cpu().clone(),
                "q": int(life.q),
                "segment_id": int(life.segment_id),
                "segment_start_active_step": int(life.segment_start_active_step),
                "active_steps": int(life.active_steps),
                "non_create_opportunities": int(life.non_create_opportunities),
                "spell_opportunity_count": int(life.spell_opportunity_count),
            }
            for key, life in cursor.lifecycles[env_index].items()
        },
        "segments": tuple(cursor.segments[env_index]),
    }


def _apply_audit_event(
    cursor: CollectionCursor,
    *,
    env_index: int,
    key: int,
    selected_kind: int,
    new_z: torch.Tensor,
    assigned_q: int,
    record_epoch: int,
) -> SegmentRecord | None:
    """Apply one forced non-CREATE event exactly as the collector would.

    Mirrors the collector's post-decision lifecycle update for a single
    request: spell accounting, the RENEW segment close, the commitment mark
    install and the new `q`. `record_epoch` is the collected membership
    epoch at this coordinate (the collector reads it *after* membership
    processing), so a RENEW at a REJOIN step records the same epoch the
    collector recorded while leaving `life.membership_epoch` untouched for
    the collector's own REJOIN check on the very next step.

    A RENEW's `SegmentRecord` is *returned*, not appended. The forced event
    is applied before the branch collection runs, so appending it here would
    place it ahead of every record the fork step itself produces and the
    branch would stop being a literal continuation of the collected segment
    sequence. The caller splices it into its frontier-order position once
    the audit step has run (`_audit_focal_segment_index`).
    """

    life = cursor.lifecycles[env_index][key]
    record: SegmentRecord | None = None
    life.spell_opportunity_count += 1
    if selected_kind == RENEW:
        record = SegmentRecord(
            cursor.episode_ids[env_index], key, record_epoch, life.segment_id,
            life.segment_start_active_step, life.active_steps, False,
            "RENEW", life.spell_opportunity_count,
        )
        life.segment_id += 1
        life.segment_start_active_step = life.active_steps
        life.spell_opportunity_count = 0
    life.non_create_opportunities += 1
    life.z = new_z.detach().clone()
    life.q = int(assigned_q)
    return record


def _audit_focal_segment_index(
    branch: EventTrajectory,
    *,
    env_index: int,
    key: int,
    base: int,
    leading_closes: int,
) -> int:
    """Frontier-order position of the forced event's `SegmentRecord`.

    Within one environment the collector appends a physical step's segment
    records in a fixed order: the TERMINAL_LEAVE closes of the membership
    pass, then one RENEW record per *requesting* key in frontier order (the
    request list is built from `view.active_keys`), then any EPISODE_END
    closes of the terminal transition. The forced focal event already
    installed its `q`, so the collector does not re-request at that
    coordinate and the branch's own fork step produces every record except
    the focal one.

    `base` is the record count the branch inherited from the reconstructed
    prefix and `leading_closes` the number of TERMINAL_LEAVE closes the fork
    step performs for this environment; the remaining offset is counted off
    the branch's own step-0 row, which *is* the fork step. Splicing at the
    returned index reproduces exactly what appending in place would have
    produced, because nothing in `collect_trajectory` reads `cursor.segments`.
    """

    order = branch.orders[0, env_index].detach().cpu().numpy()
    kinds = branch.event_kind[0, env_index].detach().cpu().numpy()
    offset = int(leading_closes)
    for raw in order:
        other = int(raw)
        if other < 0:
            continue
        if other == key:
            return int(base) + offset
        if int(kinds[other]) == RENEW:
            offset += 1
    raise RuntimeError(
        "fork coordinate is absent from the fork-step frontier order "
        f"(env_index={env_index}, key={key})"
    )


def _check_audit_provenance(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    cursor: CollectionCursor,
    state: TrainingState,
    *,
    seed_map: Mapping[str, int],
) -> None:
    """Fail loudly when the rebuilt ledgers are not the collected ones.

    The fork rebuilds every ledger from `state.profile`/`state.seed_map`,
    but nothing in an `EventTrajectory` records which profile produced it.
    A profile or seed mismatch yields a different task ledger, hence a
    different membership schedule and frontier priority order, and would
    otherwise surface only as an opaque prefix reconstruction mismatch
    after a full rollout. The recorded step-0 frontier order is exactly the
    ledger-determined active roster in ledger-determined priority order, so
    comparing it against the rebuilt environments names the disagreement
    before any work is done.
    """

    if state.arm != arm.arm:
        raise ValueError(
            f"fork state owns arm {state.arm!r}, not {arm.arm!r}"
        )
    if state.seed_map != dict(seed_map):
        raise ValueError(
            "fork state seed map is not the authoritative map for profile "
            f"{state.profile!r} replicate {state.replicate}: "
            f"{state.seed_map} != {dict(seed_map)}"
        )
    recorded = trajectory.orders[0].detach().cpu().numpy()
    for env_index, environment in enumerate(cursor.environments):
        ledger = environment.ledger
        if ledger.profile != state.profile:
            raise ValueError(
                f"fork ledger profile {ledger.profile!r} does not match "
                f"collector profile {state.profile!r}"
            )
        row = recorded[env_index]
        collected = tuple(int(value) for value in row[row >= 0])
        rebuilt = tuple(int(value) for value in environment.observe().active_keys)
        if rebuilt != collected:
            raise ValueError(
                "fork ledger disagrees with the collected trajectory: profile "
                f"{state.profile!r}, replicate {state.replicate}, episode "
                f"{cursor.episode_ids[env_index]}, ledger seed "
                f"{state.seed_map['ledger']}, order seed "
                f"{state.seed_map['order']}; rebuilt step-0 roster {rebuilt} "
                f"!= collected {collected}"
            )


def _audit_row_scripts(
    trajectory: EventTrajectory,
    rngs: Mapping[str, np.random.Generator],
    *,
    time: int,
    env_index: int,
) -> tuple[
    dict[str, _AuditRowStream],
    dict[str, Any],
    dict[str, dict[str, Any]],
]:
    owned = {name: deepcopy(rngs[name]) for name in RNG_NAMES}
    start_states = {
        name: deepcopy(owned[name].bit_generator.state) for name in RNG_NAMES
    }
    schedules: dict[str, list[dict[str, Any]]] = {
        name: [] for name in RNG_NAMES
    }
    event_values: list[np.ndarray] = []
    mark_values: list[np.ndarray] = []
    opportunity_values: list[np.ndarray] = []
    primitive_values: list[np.ndarray] = []
    audit_by_time = {
        name: {
            int(entry["coordinates"]["time"]): entry
            for entry in trajectory.rng_audit["streams"][name]
            if "time" in entry["coordinates"]
        }
        for name in AUDIT_STREAM_NAMES
    }
    for step in range(int(time), int(trajectory.time_steps)):
        event_entry = audit_by_time["event"].get(step)
        request_rows = (
            [] if event_entry is None
            else event_entry["coordinates"]["requests"]
        )
        coordinates = np.asarray(
            [[int(row[0]), int(row[1])] for row in request_rows],
            dtype=np.int64,
        ).reshape(-1, 2)
        count = int(len(coordinates))
        if count:
            schedules["event"].append(deepcopy(audit_by_time["event"][step]))
            schedules["mark"].append(deepcopy(audit_by_time["mark"][step]))
            schedules["opportunity"].append(
                deepcopy(audit_by_time["opportunity"][step])
            )
            event = owned["event"].random(count)
            mark = owned["mark"].standard_normal((count, MARK_DIM))
            opportunity = owned["opportunity"].choice(
                OPPORTUNITY_SUPPORT, size=count
            )
            selected = coordinates[:, 0] == int(env_index)
            event_values.append(np.asarray(event)[selected])
            mark_values.append(np.asarray(mark)[selected])
            opportunity_values.append(np.asarray(opportunity)[selected])
        primitive = owned["primitive"].random(
            (len(trajectory.ledger_ids), MAX_LIFECYCLES), dtype=np.float32
        )
        schedules["primitive"].append(
            deepcopy(audit_by_time["primitive"][step])
        )
        primitive_values.append(np.asarray(primitive)[env_index])
    arrays = {
        "event": np.concatenate(event_values) if event_values else np.empty(0),
        "mark": np.concatenate(mark_values, axis=0).reshape(-1)
        if mark_values else np.empty(0),
        "opportunity": np.concatenate(opportunity_values)
        if opportunity_values else np.empty(0, dtype=np.int64),
        "primitive": np.concatenate(primitive_values)
        if primitive_values else np.empty(0, dtype=np.float32),
    }
    end_states = {
        name: deepcopy(owned[name].bit_generator.state) for name in RNG_NAMES
    }
    return (
        {name: _AuditRowStream(value) for name, value in arrays.items()},
        end_states,
        {
            name: {
                "start_state": start_states[name],
                "draw_schedule": schedules[name],
                "end_state": end_states[name],
            }
            for name in RNG_NAMES
        },
    )


def _audit_row_errors(
    branch: EventTrajectory,
    branch_index: int,
    original: EventTrajectory,
    original_env: int,
    *,
    start: int,
) -> dict[str, Any]:
    device = branch.rewards.device
    discrete_flags = [
        torch.any(
            getattr(branch, name)[:, branch_index]
            != getattr(original, name)[start:, original_env].to(device)
        ).to(torch.float32)
        for name in _AUDIT_DISCRETE_FIELDS
    ]
    continuous_maxima = []
    for name in _AUDIT_CONTINUOUS_FIELDS:
        left = getattr(branch, name)[:, branch_index]
        right = getattr(original, name)[start:, original_env].to(device)
        continuous_maxima.append(
            torch.max(torch.abs(left - right))
            if left.numel() else torch.zeros((), device=device)
        )
    packed = torch.stack((
        torch.stack(discrete_flags).sum(),
        torch.stack(continuous_maxima).max(),
    )).detach().cpu().tolist()
    return {
        "discrete_mismatch": int(packed[0]),
        "continuous_error": float(packed[1]),
        "segment_equal": branch.segments[branch_index] == original.segments[original_env],
        "outcome_equal": branch.outcomes[branch_index] == original.outcomes[original_env],
    }


def _float32_ulp_distance(left: float, right: float) -> int:
    def ordered(value: float) -> int:
        bits = int(np.asarray(value, dtype=np.float32).view(np.uint32))
        return 0x80000000 - bits if bits & 0x80000000 else bits + 0x80000000

    return abs(ordered(left) - ordered(right))


def _audit_row_continuous_diagnostic(
    branch: EventTrajectory,
    branch_index: int,
    original: EventTrajectory,
    original_env: int,
    *,
    start: int,
) -> dict[str, Any] | None:
    """Describe the worst failed field without changing persisted evidence."""

    worst: dict[str, Any] | None = None
    for name in _AUDIT_CONTINUOUS_FIELDS:
        replayed = getattr(branch, name)[:, branch_index].detach().cpu()
        stored = getattr(original, name)[start:, original_env].detach().cpu()
        difference = torch.abs(replayed - stored)
        if not difference.numel():
            continue
        flat_index = int(torch.argmax(difference).item())
        coordinate = tuple(
            int(value) for value in np.unravel_index(
                flat_index, tuple(difference.shape)
            )
        )
        absolute_error = float(difference.reshape(-1)[flat_index])
        if worst is not None and absolute_error <= float(worst["absolute_error"]):
            continue
        stored_value = float(stored.reshape(-1)[flat_index])
        replayed_value = float(replayed.reshape(-1)[flat_index])
        worst = {
            "field": name,
            "coordinate": {
                "time": int(start + coordinate[0]),
                "env_index": int(original_env),
                "field_indices": list(coordinate[1:]),
            },
            "stored": stored_value,
            "replayed": replayed_value,
            "absolute_error": absolute_error,
            "float32_ulp_distance": _float32_ulp_distance(
                stored_value, replayed_value
            ),
        }
    return worst


def _audit_payload_tensor(
    value: Any, *, name: str, device: torch.device
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Decode a supplied binary32 mark while preserving its exact bytes."""

    if isinstance(value, Mapping) and "bytes_b64" in value:
        encoded = base64.b64decode(str(value["bytes_b64"]), validate=True)
        array = np.frombuffer(encoded, dtype=np.float32).copy()
        if value.get("shape") != [MARK_DIM] or array.shape != (MARK_DIM,):
            raise ValueError(f"{name} payload shape mismatch")
        if hashlib.sha256(encoded).hexdigest() != value.get("sha256"):
            raise ValueError(f"{name} payload digest mismatch")
    elif isinstance(value, torch.Tensor):
        if value.dtype != torch.float32 or tuple(value.shape) != (MARK_DIM,):
            raise ValueError(f"{name} must be one float32 mark")
        array = value.detach().cpu().contiguous().numpy().copy()
    else:
        array = np.asarray(value)
        if array.dtype != np.float32 or array.shape != (MARK_DIM,):
            raise ValueError(f"{name} must preserve an exact float32 payload")
        array = np.ascontiguousarray(array)
    payload = _float32_payload(array)
    return torch.as_tensor(array, dtype=torch.float32, device=device), payload


def _audit_serialized_size(value: Any) -> int:
    def default(item: Any) -> Any:
        if isinstance(item, np.ndarray):
            return item.tolist()
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, torch.Tensor):
            return item.detach().cpu().tolist()
        if hasattr(item, "__dataclass_fields__"):
            return {
                name: getattr(item, name) for name in item.__dataclass_fields__
            }
        raise TypeError(f"unsupported audit evidence value {type(item)!r}")

    return len(json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=default
    ).encode("utf-8"))


def audit_opportunities_batched(
    arm: CommitmentArm,
    selected_states: list[dict[str, Any]],
    *,
    device: torch.device,
    debug: bool = False,
) -> list[dict[str, Any]]:
    """Execute Stage 2 in canonical original-slot width-16 continuations."""

    if arm.arm == "OR" or not selected_states:
        return []
    total_started = perf_counter()
    prefix_started = total_started
    prepared: list[dict[str, Any]] = []
    by_batch: dict[int, list[dict[str, Any]]] = {}
    prefix_cache: dict[tuple[int, int], CollectionCursor] = {}
    row_script_cache: dict[tuple[int, int, int], tuple[Any, ...]] = {}
    cell_script_cache: dict[tuple[int, int], list[tuple[Any, ...]]] = {}
    prefix_collector_calls = 0
    for value in selected_states:
        by_batch.setdefault(int(value["batch_index"]), []).append(value)
    for batch_index, records in by_batch.items():
        origin = records[0]["origin_state"]
        trajectory = records[0]["trajectory"]
        if len(trajectory.ledger_ids) != FORMAL_NUM_ENVS:
            raise ValueError("Stage-2 collection width is not registered width 16")
        trace_kind = {
            (
                int(row["coordinate"]["time"]),
                int(row["coordinate"]["env_index"]),
                int(row["coordinate"]["key"]),
            ): int(row["natural_kind"])
            for row in trajectory.raw_event_trace
        }
        replay_state = deepcopy(origin)
        cursor: CollectionCursor | None = None
        current_time = 0
        for time in sorted({int(value["time"]) for value in records}):
            delta = time - current_time
            if delta <= 0:
                raise ValueError("batched audit opportunities must follow CREATE")
            prefix = collect_trajectory(
                arm,
                replay_state,
                device=device,
                episode_ids=trajectory.ledger_ids if cursor is None else None,
                cursor=cursor,
                max_steps=delta,
                deterministic=False,
                profile=origin.profile,
            )
            cursor = prefix.cursor
            prefix_collector_calls += 1
            if cursor is None:
                raise RuntimeError("batched audit prefix unexpectedly terminated")
            current_time = time
            prefix_cache[(batch_index, time)] = _clone_audit_cursor(cursor)
            scripts: list[tuple[Any, ...]] = []
            for env_index in range(FORMAL_NUM_ENVS):
                script_key = (batch_index, time, env_index)
                cached = row_script_cache.get(script_key)
                if cached is None:
                    cached = _audit_row_scripts(
                        trajectory, replay_state.rngs,
                        time=time, env_index=env_index,
                    )
                    row_script_cache[script_key] = cached
                scripts.append(deepcopy(cached))
            cell_script_cache[(batch_index, time)] = scripts
            for record in records:
                if int(record["time"]) != time:
                    continue
                env_index = int(record["env_index"])
                key = int(record["key"])
                natural_kind = trace_kind.get((time, env_index, key))
                if natural_kind not in (KEEP, RENEW):
                    raise ValueError("selected audit coordinate is not in the raw trace")
                natural_action = "KEEP" if natural_kind == KEEP else "RENEW"
                if record.get("natural_action") != natural_action:
                    raise ValueError("selected-state natural action contradicts trace")
                streams, end_rng_states, rng_binding_material = deepcopy(
                    scripts[env_index]
                )
                expected_end_rng_states = record.get("expected_end_rng_states")
                if (
                    expected_end_rng_states is not None
                    and end_rng_states != expected_end_rng_states
                ):
                    raise RuntimeError("audit row script final RNG state mismatch")
                donor_u, donor_u_payload = _audit_payload_tensor(
                    record["donor_candidate_u"],
                    name="donor_candidate_u", device=device,
                )
                donor_z, donor_z_payload = _audit_payload_tensor(
                    record["donor_candidate_z"],
                    name="donor_candidate_z", device=device,
                )
                prepared.append({
                    **record,
                    "natural_kind": natural_kind,
                    "streams": streams,
                    "end_rng_states": end_rng_states,
                    "rng_binding_material": rng_binding_material,
                    "donor_u_tensor": donor_u,
                    "donor_z_tensor": donor_z,
                    "donor_candidate_u_payload": donor_u_payload,
                    "donor_candidate_z_payload": donor_z_payload,
                })

    results: dict[str, dict[str, Any]] = {}
    prefix_seconds = perf_counter() - prefix_started
    branch_started = perf_counter()
    branch_collector_calls = 0
    natural_control_layer_count = 0
    counterfactual_layer_count = 0
    cells = sorted({
        (int(value["batch_index"]), int(value["time"])) for value in prepared
    })
    for batch_index, time in cells:
        group = [
            value for value in prepared
            if int(value["batch_index"]) == batch_index
            and int(value["time"]) == time
        ]
        cell_scripts = cell_script_cache[(batch_index, time)]

        def new_result(pair: dict[str, Any]) -> dict[str, Any]:
            natural_kind = int(pair["natural_kind"])
            natural_branch = (
                AUDIT_BRANCHES[0] if natural_kind == KEEP else AUDIT_BRANCHES[2]
            )
            audit_id = str(pair["audit_id"])
            return results.setdefault(audit_id, {
                "audit_id": audit_id,
                "natural_action": "KEEP" if natural_kind == KEEP else "RENEW",
                "natural_branch": natural_branch,
                "end_rng_states": pair["end_rng_states"],
                "rng_binding_material": pair["rng_binding_material"],
                "donor_binding_material": {
                    "recipient_key": deepcopy(pair.get("recipient_key")),
                    "donor_key": deepcopy(pair.get("donor_key")),
                    "mapping_position": deepcopy(pair.get("mapping_position")),
                    "candidate_u": pair["donor_candidate_u_payload"],
                    "candidate_z": pair["donor_candidate_z_payload"],
                    "candidate_digest": _canonical_json_digest({
                        "candidate_u": pair["donor_candidate_u_payload"],
                        "candidate_z": pair["donor_candidate_z_payload"],
                    }),
                    "binding": deepcopy(pair.get("donor_binding")),
                },
                "selected_state": deepcopy(pair.get("selected_state", {
                    "batch_index": int(pair["batch_index"]),
                    "time": time,
                    "env_index": int(pair["env_index"]),
                    "key": int(pair["key"]),
                })),
                "branches": {},
            })

        def record_branch(
            pair: dict[str, Any], branch_name: str,
            branch_trajectory: EventTrajectory,
            row_streams: list[dict[str, _AuditRowStream]],
        ) -> None:
            env_index = int(pair["env_index"])
            streams = row_streams[env_index]
            result = new_result(pair)
            outcome = branch_trajectory.outcomes[env_index]
            result["branches"][branch_name] = {
                "outcome": outcome,
                "utility": float(outcome.utility),
                "stream_positions": {
                    name: int(stream.position) for name, stream in streams.items()
                },
                "stream_consumption": {
                    name: stream.consumption_record(pair["end_rng_states"][name])
                    for name, stream in streams.items()
                },
            }
            if debug:
                result["branches"][branch_name]["trajectory"] = branch_trajectory
                result["branches"][branch_name]["branch_index"] = env_index

        natural_streams = [deepcopy(value[0]) for value in cell_scripts]
        natural_state = make_training_state(
            arm.arm, int(group[0]["replicate"]), profile="held_out"
        )
        natural_trajectory = collect_trajectory(
            arm,
            natural_state,
            device=device,
            cursor=_clone_audit_cursor(prefix_cache[(batch_index, time)]),
            deterministic=False,
            row_rngs=natural_streams,
        )
        branch_collector_calls += 1
        natural_control_layer_count += 1
        for pair in group:
            natural_branch = (
                AUDIT_BRANCHES[0]
                if int(pair["natural_kind"]) == KEEP else AUDIT_BRANCHES[2]
            )
            record_branch(pair, natural_branch, natural_trajectory, natural_streams)
            env_index = int(pair["env_index"])
            natural_errors = _audit_row_errors(
                natural_trajectory,
                env_index,
                pair["trajectory"],
                env_index,
                start=time,
            )
            if not (
                natural_errors["discrete_mismatch"] == 0
                and natural_errors["continuous_error"]
                <= CAUSAL_AUDIT_CONTINUOUS_ATOL
                and natural_errors["segment_equal"]
                and natural_errors["outcome_equal"]
            ):
                diagnostic = _audit_row_continuous_diagnostic(
                    natural_trajectory, env_index, pair["trajectory"], env_index,
                    start=time,
                )
                raise RuntimeError(
                    "batched audit natural branch mismatch "
                    f"{natural_errors}; worst_continuous={diagnostic}"
                )
            new_result(pair)["natural_errors"] = natural_errors

        counterfactuals: list[dict[str, Any]] = []
        for pair in group:
            env_index = int(pair["env_index"])
            key = int(pair["key"])
            natural_branch = (
                AUDIT_BRANCHES[0]
                if int(pair["natural_kind"]) == KEEP else AUDIT_BRANCHES[2]
            )
            for branch_name, kind, new_z in (
                (AUDIT_BRANCHES[0], KEEP,
                 pair["trajectory"].event_z_pre[time, env_index, key]),
                (AUDIT_BRANCHES[1], RENEW, pair["donor_z_tensor"]),
                (AUDIT_BRANCHES[2], RENEW,
                 pair["trajectory"].candidate_z[time, env_index, key]),
            ):
                if branch_name != natural_branch:
                    counterfactuals.append({
                        "pair": pair, "branch_name": branch_name,
                        "kind": kind, "new_z": new_z,
                    })
        layers: list[dict[int, dict[str, Any]]] = []
        for spec in counterfactuals:
            env_index = int(spec["pair"]["env_index"])
            layer = next(
                (value for value in layers if env_index not in value), None
            )
            if layer is None:
                layer = {}
                layers.append(layer)
            layer[env_index] = spec
        for layer in layers:
            layer_streams = [deepcopy(value[0]) for value in cell_scripts]
            forced = {
                (time, env_index, int(spec["pair"]["key"])): (
                    int(spec["kind"]), spec["new_z"]
                )
                for env_index, spec in layer.items()
            }
            layer_state = make_training_state(
                arm.arm, int(group[0]["replicate"]), profile="held_out"
            )
            layer_trajectory = collect_trajectory(
                arm,
                layer_state,
                device=device,
                cursor=_clone_audit_cursor(prefix_cache[(batch_index, time)]),
                deterministic=False,
                forced_events=forced,
                row_rngs=layer_streams,
            )
            branch_collector_calls += 1
            counterfactual_layer_count += 1
            for spec in layer.values():
                record_branch(
                    spec["pair"], spec["branch_name"],
                    layer_trajectory, layer_streams,
                )
    branch_seconds = perf_counter() - branch_started
    ordered_results: list[dict[str, Any]] = []
    for selected in selected_states:
        result = results[str(selected["audit_id"])]
        branch_rows = [result["branches"][name] for name in AUDIT_BRANCHES]
        positions = [row["stream_positions"] for row in branch_rows]
        consumptions = [row["stream_consumption"] for row in branch_rows]
        if positions[1:] != positions[:-1] or consumptions[1:] != consumptions[:-1]:
            raise RuntimeError("batched audit branch RNG contract diverged")
        result["branch_outcomes"] = {
            name: result["branches"][name]["outcome"] for name in AUDIT_BRANCHES
        }
        result["rng_contract_equal"] = True
        result["telemetry"] = {
            "prefix_seconds": float(prefix_seconds),
            "branch_seconds": float(branch_seconds),
            "total_seconds": float(perf_counter() - total_started),
            "selected_state_count": len(selected_states),
            "collector_call_count": prefix_collector_calls + branch_collector_calls,
            "natural_control_layer_count": natural_control_layer_count,
            "counterfactual_layer_count": counterfactual_layer_count,
            "physical_row_count": branch_collector_calls * FORMAL_NUM_ENVS,
        }
        result["telemetry"]["serialized_size_bytes"] = _audit_serialized_size(result)
        ordered_results.append(result)
    return ordered_results


def _audit_stochastic_opportunity(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    env_index: int,
    time: int,
    key: int,
    device: torch.device,
    state: TrainingState,
    donor_candidate_u: Any,
    donor_candidate_z: Any,
    donor_binding: Mapping[str, Any] | None,
    diagnostics: dict[str, Any] | None,
) -> dict[str, Any]:
    """Replay one stochastic batch prefix and force one paired branch.

    ``state`` is the owned-RNG state at the beginning of the collected batch.
    Prefix replay therefore consumes the exact registered streams that made
    the natural record. Both branch states are cloned after that prefix and
    consume identical subsequent variates; only the focal KEEP/RENEW choice
    and installed mark differ.
    """

    started = perf_counter()
    env_index, time, key = int(env_index), int(time), int(key)
    natural_kind = int(trajectory.event_kind[time, env_index, key])
    if natural_kind not in (KEEP, RENEW):
        raise ValueError("audit coordinate is not an eligible non-CREATE opportunity")
    if time <= 0 or trajectory.cutoff or not trajectory.outcomes:
        raise ValueError("stochastic fork requires a complete eligible trajectory")
    if state.pending_cursor is not None:
        raise ValueError("stochastic fork requires a batch-origin collector state")
    if state.arm != arm.arm or state.profile != "held_out":
        raise ValueError("stochastic fork requires the matching held-out arm state")
    prefix_state = deepcopy(state)
    prefix = collect_trajectory(
        arm,
        prefix_state,
        device=device,
        episode_ids=trajectory.ledger_ids,
        max_steps=time,
        deterministic=False,
        profile=state.profile,
    )
    prefix_errors = _audit_window_errors(prefix, trajectory, start=0)
    if (
        prefix_errors["discrete_mismatch"] != 0.0
        or prefix_errors["continuous"] > CAUSAL_AUDIT_CONTINUOUS_ATOL
    ):
        raise RuntimeError(f"stochastic fork prefix mismatch {prefix_errors}")
    if prefix_state.pending_cursor is None:
        raise RuntimeError("stochastic fork prefix unexpectedly terminated")
    prefix_seconds = perf_counter() - started
    branch_started = perf_counter()

    z_pre = trajectory.event_z_pre[time, env_index, key].to(device)
    candidate = trajectory.candidate_z[time, env_index, key].to(device)
    donor_u, donor_u_payload = _audit_payload_tensor(
        donor_candidate_u, name="donor_candidate_u", device=device
    )
    donor_z, donor_z_payload = _audit_payload_tensor(
        donor_candidate_z, name="donor_candidate_z", device=device
    )
    natural_action = AUDIT_BRANCHES[0] if natural_kind == KEEP else AUDIT_BRANCHES[2]
    branches: dict[str, EventTrajectory] = {}
    branch_states: dict[str, TrainingState] = {}
    for name, kind, new_z in (
        (AUDIT_BRANCHES[0], KEEP, z_pre),
        (AUDIT_BRANCHES[1], RENEW, donor_z),
        (AUDIT_BRANCHES[2], RENEW, candidate),
    ):
        branch_state = deepcopy(prefix_state)
        branch_cursor = _clone_audit_cursor(prefix_state.pending_cursor)
        branch_state.pending_cursor = branch_cursor
        branch = collect_trajectory(
            arm,
            branch_state,
            device=device,
            cursor=branch_cursor,
            deterministic=False,
            forced_event=(time, env_index, key, kind, new_z),
        )
        if branch.cutoff or not branch.outcomes:
            raise RuntimeError(f"stochastic fork {name} branch did not terminate")
        branches[name] = branch
        branch_states[name] = branch_state

    natural_errors = _audit_window_errors(
        branches[natural_action], trajectory, start=time
    )
    natural_outcome_mismatch = (
        branches[natural_action].outcomes[env_index]
        != trajectory.outcomes[env_index]
    )
    if (
        natural_outcome_mismatch
        or natural_errors["discrete_mismatch"] != 0.0
        or natural_errors["continuous"] > CAUSAL_AUDIT_CONTINUOUS_ATOL
    ):
        raise RuntimeError(
            f"stochastic fork natural branch continuation mismatch {natural_errors}"
        )
    rng_states = [_rng_states(branch_states[name]) for name in AUDIT_BRANCHES]
    if any(not _nested_equal(rng_states[0], value) for value in rng_states[1:]):
        raise RuntimeError("stochastic fork branch RNG states diverged")
    if diagnostics is not None:
        diagnostics.clear()
        diagnostics.update({
            "coordinate": {"time": time, "env_index": env_index, "key": key},
            "episode_id": int(trajectory.ledger_ids[env_index]),
            "natural_action": natural_action,
            "prefix_errors": prefix_errors,
            "natural_branch_errors": natural_errors,
            "branch_rng_equal": True,
            "branch_trajectories": branches,
            "branch_rng_states": {
                name: _rng_states(branch_states[name]) for name in AUDIT_BRANCHES
            },
        })
    result = {
        "branches": {
            name: {
                "outcome": branches[name].outcomes[env_index],
                "utility": float(branches[name].outcomes[env_index].utility),
            }
            for name in AUDIT_BRANCHES
        },
        "branch_outcomes": {
            name: branches[name].outcomes[env_index] for name in AUDIT_BRANCHES
        },
        "natural_action": "KEEP" if natural_kind == KEEP else "RENEW",
        "natural_branch": natural_action,
        "rng_contract_equal": True,
        "donor_binding_material": {
            "candidate_u": donor_u_payload,
            "candidate_z": donor_z_payload,
            "candidate_digest": _canonical_json_digest({
                "candidate_u": donor_u_payload, "candidate_z": donor_z_payload,
            }),
            "binding": deepcopy(None if donor_binding is None else dict(donor_binding)),
        },
        "telemetry": {
            "prefix_seconds": float(prefix_seconds),
            "branch_seconds": float(perf_counter() - branch_started),
            "total_seconds": float(perf_counter() - started),
            "selected_state_count": 1,
            "collector_call_count": 4,
        },
    }
    result["telemetry"]["serialized_size_bytes"] = _audit_serialized_size(result)
    return result


def audit_single_opportunity(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    env_index: int,
    time: int,
    key: int,
    device: torch.device,
    state: TrainingState,
    donor_candidate_u: Any,
    donor_candidate_z: Any,
    donor_binding: Mapping[str, Any] | None = None,
    deterministic: bool = True,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Sequentially fork one eligible non-CREATE opportunity into KEEP/RENEW.

    Reconstructs the exact pre-event state at `(env_index, time, key)` by
    re-running the collector deterministically over the *whole collected
    batch* -- every episode of the trajectory, at the registered collection
    width -- under the realized opportunity schedule recovered from the
    record, then builds two independent branches from that reconstruction
    (environments via the snapshot contract, plus their own lifecycle
    tables, recurrent hidden state, commitment `z`/`q`, segment records and
    open-segment bookkeeping). The only treatment difference is the
    commitment mark at the focal coordinate: KEEP retains the existing `z`,
    RENEW installs `trajectory.candidate_z`. Both branches are advanced to
    episode termination -- never truncated, because this environment pays
    zero reward until the terminal step -- and each branch's external
    utility is the focal environment outcome's utility.

    Reconstruction runs at the collected width rather than at width 1
    because float32 reduction order depends on tensor shape: a width-1
    replay of a width-16 collection exceeds the registered continuous tolerance,
    drift can flip a primitive argmax at evaluation scale. Matching the
    batch shape removes that drift class instead of bounding it, which is
    what lets the natural-action branch be checked for *exact* reproduction
    of the collected continuation on every fork.

    Both branches consume identical realized variates by construction: the
    fork owns one generator per stream, seeded from the registered stream
    seeds plus this opportunity's stable provenance, and every realized
    value is materialized once in a shared log that both branches replay
    from their own positions. The request schedule is action-independent,
    so the two branches' draw counts align step for step.

    This implementation body is the deterministic verification path. The
    stochastic Stage-2 path dispatches above to a batch-origin RNG replay,
    because its factual event, mark and primitive variates must be recovered
    from the owned stream state rather than inferred from the trajectory.
    """

    if not deterministic:
        return _audit_stochastic_opportunity(
            arm,
            trajectory,
            env_index=env_index,
            time=time,
            key=key,
            device=device,
            state=state,
            donor_candidate_u=donor_candidate_u,
            donor_candidate_z=donor_candidate_z,
            donor_binding=donor_binding,
            diagnostics=diagnostics,
        )

    started = perf_counter()
    env_index, time, key = int(env_index), int(time), int(key)
    coordinate = {"time": time, "env_index": env_index, "key": key}
    if diagnostics is not None:
        # Emptied before any work so that every exit path -- including the
        # reconstruction and non-termination raises below -- leaves the
        # caller's dict describing *this* fork. A caller reusing one dict
        # across forks must never read a previous fork's values after a
        # failure.
        diagnostics.clear()
        diagnostics["coordinate"] = dict(coordinate)
    if arm.arm == "OR":
        raise ValueError("the ordinary source arm has no commitment opportunities")
    if trajectory.cutoff or not trajectory.outcomes:
        raise ValueError("fork requires a complete episode rollout")
    natural_kind = int(trajectory.event_kind[time, env_index, key])
    if natural_kind not in (KEEP, RENEW):
        raise ValueError("fork coordinate is not an eligible non-CREATE opportunity")
    if time <= 0 or time >= trajectory.time_steps:
        raise ValueError("fork coordinate is outside the collected episode")

    episode_ids = tuple(int(value) for value in trajectory.ledger_ids)
    if not 0 <= env_index < len(episode_ids):
        raise ValueError("fork env_index is outside the collected batch")
    episode_id = episode_ids[env_index]
    profile = state.profile
    replicate = int(state.replicate)
    seed_map = authoritative_seed_map(profile, replicate)
    ledgers = tuple(
        make_noncalendar_ledger(
            value, profile=profile,
            task_seed=state.seed_map["ledger"], order_seed=state.seed_map["order"],
        )
        for value in episode_ids
    )

    # Action-independent provenance: the pre-event segment id, not the
    # recorded post-event one (a natural RENEW already incremented it).
    segment_id = int(trajectory.segment_id[time, env_index, key]) - int(
        natural_kind == RENEW
    )
    stream_label = f" at (time={time}, env_index={env_index}, key={key})"
    streams = {
        name: _AuditStream(
            name,
            make_rng(seed_map[name], episode_id, time, key, segment_id),
            label=stream_label,
        )
        for name in AUDIT_STREAM_NAMES
    }
    script, script_index, cumulative = _audit_opportunity_script(
        trajectory, fallback=streams["opportunity"].generator
    )
    focal_index = script_index.get((env_index, time, key))
    if focal_index is None:
        raise RuntimeError(
            f"fork coordinate is not a recorded opportunity{stream_label}"
        )
    assigned_q = int(script[focal_index])
    prefix_position = int(cumulative[time - 1])
    if focal_index < prefix_position:
        raise RuntimeError(
            f"fork opportunity precedes the reconstructed prefix{stream_label}"
        )
    streams["opportunity"] = _AuditStream(
        "opportunity", streams["opportunity"].generator, script=script,
        label=stream_label,
    )

    prefix_cursor = _audit_cursor(ledgers, episode_ids, device)
    _check_audit_provenance(arm, trajectory, prefix_cursor, state, seed_map=seed_map)

    training_mode = arm.training
    try:
        prefix_view = _AuditStreamView(streams)
        prefix_state = _audit_branch_state(arm.arm, replicate, profile, prefix_view)
        prefix = collect_trajectory(
            arm, prefix_state, device=device, cursor=prefix_cursor,
            max_steps=time, deterministic=True,
        )
        if prefix_view.positions["opportunity"] != prefix_position:
            raise RuntimeError("reconstructed prefix consumed an unexpected schedule")
        prefix_errors = _audit_window_errors(prefix, trajectory, start=0)
        if prefix_errors["discrete_mismatch"] != 0.0:
            if diagnostics is not None:
                diagnostics["prefix_errors"] = prefix_errors
            raise RuntimeError(
                f"fork prefix reconstruction mismatch {prefix_errors} at "
                f"(time={time}, env_index={env_index}, key={key})"
            )
        if prefix_errors["continuous"] > CAUSAL_AUDIT_CONTINUOUS_ATOL:
            if diagnostics is not None:
                diagnostics["prefix_errors"] = prefix_errors
            raise RuntimeError(
                f"fork prefix reconstruction exceeds the causal-audit "
                f"continuous tolerance {prefix_errors} "
                f"at (time={time}, env_index={env_index}, key={key})"
            )
        prefix_seconds = perf_counter() - started
        branch_started = perf_counter()

        # The branch schedule drops the focal request: it is applied by the
        # treatment below, not sampled by the collector.
        branch_script = list(script)
        del branch_script[focal_index]
        streams["opportunity"] = _AuditStream(
            "opportunity", streams["opportunity"].generator, script=branch_script,
            label=stream_label,
        )
        record_epoch = int(trajectory.membership_epoch[time, env_index, key])
        z_pre = trajectory.event_z_pre[time, env_index, key].to(device)
        candidate = trajectory.candidate_z[time, env_index, key].to(device)
        donor_u, donor_u_payload = _audit_payload_tensor(
            donor_candidate_u, name="donor_candidate_u", device=device
        )
        donor_z, donor_z_payload = _audit_payload_tensor(
            donor_candidate_z, name="donor_candidate_z", device=device
        )
        # How many TERMINAL_LEAVE closes this environment performs at the
        # fork step, read from the environment's own membership pass on a
        # throwaway snapshot clone rather than inferred from the record:
        # `active_mask` cannot separate a terminal leave from a temporary
        # one. These closes precede the fork step's request loop, so they
        # precede the focal record.
        focal_probe = NoncalendarTrackingEnv.from_snapshot_state(
            prefix_cursor.environments[env_index].snapshot_state()
        )
        leading_closes = len(
            focal_probe.observe().membership_change.terminally_left
        )

        results: dict[str, Any] = {}
        boundaries: dict[str, Any] = {}
        views: dict[str, _AuditStreamView] = {}
        branch_trajectories: dict[str, EventTrajectory] = {}
        for name, selected_kind, new_z in (
            (AUDIT_BRANCHES[0], KEEP, z_pre),
            (AUDIT_BRANCHES[1], RENEW, donor_z),
            (AUDIT_BRANCHES[2], RENEW, candidate),
        ):
            branch_cursor = _clone_audit_cursor(prefix_cursor)
            branch_cursor.lifecycles[env_index][key].z = new_z.detach().clone()
            boundaries[name] = _branch_boundary(branch_cursor, env_index)
            segment_base = len(branch_cursor.segments[env_index])
            focal_record = _apply_audit_event(
                branch_cursor, env_index=env_index, key=key,
                selected_kind=selected_kind,
                new_z=new_z, assigned_q=assigned_q, record_epoch=record_epoch,
            )
            branch_view = _AuditStreamView(streams, dict(prefix_view.positions))
            views[name] = branch_view
            branch_state = _audit_branch_state(arm.arm, replicate, profile, branch_view)
            branch = collect_trajectory(
                arm, branch_state, device=device, cursor=branch_cursor,
                deterministic=True,
            )
            if branch.cutoff or not branch.outcomes:
                if diagnostics is not None:
                    diagnostics["branch"] = name
                    diagnostics["branch_cutoff"] = bool(branch.cutoff)
                    diagnostics["branch_steps"] = int(branch.time_steps)
                raise RuntimeError(
                    f"fork {name} branch did not reach episode termination at "
                    f"(time={time}, env_index={env_index}, key={key})"
                )
            if focal_record is not None:
                branch_cursor.segments[env_index].insert(
                    _audit_focal_segment_index(
                        branch, env_index=env_index, key=key,
                        base=segment_base, leading_closes=leading_closes,
                    ),
                    focal_record,
                )
                branch = replace(
                    branch,
                    segments=tuple(
                        tuple(records) for records in branch_cursor.segments
                    ),
                )
            branch_trajectories[name] = branch
            results[name] = branch.outcomes[env_index]
    finally:
        arm.train(training_mode)

    # The natural-action branch must reproduce the collected continuation,
    # checked here on every fork rather than on sampled coordinates in a
    # test: the two branch tails carry two thirds of the reconstructed steps
    # and a drift-induced divergence there would otherwise be returned as a
    # silently corrupted advantage.
    branch_seconds = perf_counter() - branch_started
    natural_action = AUDIT_BRANCHES[0] if natural_kind == KEEP else AUDIT_BRANCHES[2]
    natural_errors = _audit_window_errors(
        branch_trajectories[natural_action], trajectory, start=time,
        excluded=(env_index, key),
    )
    natural_errors["outcome_mismatch"] = float(
        results[natural_action] != trajectory.outcomes[env_index]
    )

    if diagnostics is not None:
        diagnostics.clear()
        diagnostics.update(
            {
                "coordinate": dict(coordinate),
                "episode_id": episode_id,
                "assigned_q": assigned_q,
                "segment_id": segment_id,
                "prefix_errors": prefix_errors,
                "natural_branch_errors": natural_errors,
                # The natural branch's own segment sequence, so a caller can
                # assert the order-sensitive reproduction directly against
                # `trajectory.segments` instead of reading back the engine's
                # verdict on itself.
                "natural_branch_segments": branch_trajectories[
                    natural_action
                ].segments,
                "natural_action": natural_action,
                "boundaries": boundaries,
                "outcomes": {name: results[name] for name in results},
                "branch_terminal": {
                    name: bool(branch.terminal[-1, env_index])
                    for name, branch in branch_trajectories.items()
                },
                "branch_cutoff": {
                    name: bool(branch.cutoff)
                    for name, branch in branch_trajectories.items()
                },
                "branch_steps": {
                    name: int(branch.time_steps)
                    for name, branch in branch_trajectories.items()
                },
                "stream_positions": {
                    name: dict(view.positions) for name, view in views.items()
                },
                "stream_calls": {
                    name: dict(view.calls) for name, view in views.items()
                },
                # The realized variates each branch actually consumed. Both
                # branches read one shared stream log, so this is the direct
                # evidence for the common-randomness claim; unlike the two
                # views' generator states (which are the same objects and so
                # can never disagree), it can fail.
                "stream_values": {
                    name: {
                        stream: list(values)
                        for stream, values in view.consumed.items()
                    }
                    for name, view in views.items()
                },
                "natural_outcome": trajectory.outcomes[env_index],
                "elapsed_seconds": perf_counter() - started,
            }
        )
    if natural_errors["outcome_mismatch"] != 0.0 or natural_errors["discrete_mismatch"] != 0.0:
        raise RuntimeError(
            f"fork natural branch continuation mismatch {natural_errors} at "
            f"(time={time}, env_index={env_index}, key={key})"
        )
    if natural_errors["continuous"] > CAUSAL_AUDIT_CONTINUOUS_ATOL:
        raise RuntimeError(
            f"fork natural branch continuation exceeds the causal-audit "
            f"continuous tolerance {natural_errors} "
            f"at (time={time}, env_index={env_index}, key={key})"
        )
    positions = [views[name].positions for name in AUDIT_BRANCHES]
    consumed = [views[name].consumed for name in AUDIT_BRANCHES]
    if positions[1:] != positions[:-1] or consumed[1:] != consumed[:-1]:
        raise RuntimeError("audit branch RNG contract diverged")
    result = {
        "branches": {
            name: {"outcome": results[name], "utility": float(results[name].utility)}
            for name in AUDIT_BRANCHES
        },
        "branch_outcomes": {name: results[name] for name in AUDIT_BRANCHES},
        "natural_action": "KEEP" if natural_kind == KEEP else "RENEW",
        "natural_branch": natural_action,
        "natural_errors": natural_errors,
        "rng_contract_equal": True,
        "donor_binding_material": {
            "candidate_u": donor_u_payload,
            "candidate_z": donor_z_payload,
            "candidate_digest": _canonical_json_digest({
                "candidate_u": donor_u_payload, "candidate_z": donor_z_payload,
            }),
            "binding": deepcopy(None if donor_binding is None else dict(donor_binding)),
        },
        "telemetry": {
            "prefix_seconds": float(prefix_seconds),
            "branch_seconds": float(branch_seconds),
            "total_seconds": float(perf_counter() - started),
            "selected_state_count": 1,
            "collector_call_count": 4,
        },
    }
    result["telemetry"]["serialized_size_bytes"] = _audit_serialized_size(result)
    return result


_AUDIT_DISCRETE_FIELDS = (
    "actions", "active_mask", "orders", "terminal", "event_kind",
    "event_categorical_actions", "event_cat_mask", "event_mark_mask",
    "q_before", "membership_epoch", "segment_id",
)
_AUDIT_CONTINUOUS_FIELDS = (
    "observations", "old_log_probs", "old_values", "rewards", "hidden_before",
    "hidden_after", "prefix_counts", "primitive_z", "event_inputs", "event_u",
    "event_z_pre", "event_new_z", "candidate_u", "candidate_z",
    "event_old_cat_logp", "event_old_mark_component_logp",
    "event_old_joint_logp",
)
_AUDIT_EVENT_FIELDS = frozenset(
    {
        "event_kind", "event_categorical_actions", "event_cat_mask",
        "event_mark_mask", "q_before", "event_inputs", "event_u",
        "event_z_pre", "event_new_z", "candidate_u", "candidate_z",
        "event_old_cat_logp", "event_old_mark_component_logp",
        "event_old_joint_logp",
    }
)


def _audit_segment_mismatches(
    reconstruction: EventTrajectory,
    trajectory: EventTrajectory,
    *,
    complete: bool,
) -> tuple[str, ...]:
    """Order-sensitive per-environment `segments` comparison.

    `EventTrajectory.segments` is part of the collected continuation and
    `compare_continuations` treats it as order sensitive, so a window that
    reproduces every per-step tensor but emits its segment records in a
    different order is not a reproduction. It is also the *only* guard over
    a `SegmentRecord`'s own fields: `membership_epoch` at a RENEW is written
    from the collected record rather than from the branch lifecycle, and the
    matching per-step `membership_epoch` cell is the excluded focal
    coordinate, so a corrupted epoch on that record reaches no tensor
    comparison at all.

    A branch cursor inherits the reconstructed prefix's records, so a window
    that runs to the end of the collected episode must reproduce the whole
    per-environment sequence; a truncated prefix window reproduces a prefix
    of it (its own tail records have simply not been created yet).
    """

    left = reconstruction.segments
    right = trajectory.segments
    if len(left) != len(right):
        return ("segment_env_count",)
    failures: list[str] = []
    for env_index, (produced, expected) in enumerate(zip(left, right)):
        produced, expected = tuple(produced), tuple(expected)
        if not complete:
            expected = expected[: len(produced)]
        if produced != expected:
            failures.append(f"env{env_index}")
    return tuple(failures)


def _audit_window_errors(
    reconstruction: EventTrajectory,
    trajectory: EventTrajectory,
    *,
    start: int,
    excluded: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Compare a reconstructed window against the collected record.

    Covers every recorded per-step field over the whole collected width:
    the discrete ones exactly, and *all* recorded continuous ones under one
    maximum-absolute-error metric. The continuous set is deliberately not a
    subset -- a subset understates the reconstruction error by whichever
    field it omits, and the derived joint log-probability drifts furthest.
    The non-per-step `segments` sequence is compared too, per environment
    and order sensitively; it carries the `K` accounting and epoch
    attribution that no per-step tensor reaches.

    `excluded` names one `(env_index, key)` coordinate whose event-request
    fields are skipped on the first compared row. A branch tail starts at
    the forked step with the focal event already applied, so the collector
    does not re-request there; that one coordinate legitimately differs and
    nothing else does. It does *not* exempt that coordinate's segment
    record, which the branch is required to reproduce.
    """

    steps = int(reconstruction.time_steps)
    stop = start + steps
    mismatched: list[str] = []
    error = 0.0
    worst = ""

    def window(name: str) -> tuple[torch.Tensor, torch.Tensor]:
        left = getattr(reconstruction, name).detach().cpu()
        right = getattr(trajectory, name)[start:stop].detach().cpu()
        if excluded is not None and name in _AUDIT_EVENT_FIELDS:
            env_index, key = excluded
            left, right = left.clone(), right.clone()
            left[0, env_index, key] = 0
            right[0, env_index, key] = 0
        return left, right

    for name in _AUDIT_DISCRETE_FIELDS:
        left, right = window(name)
        if left.shape != right.shape or not torch.equal(left, right):
            mismatched.append(name)
    for name in _AUDIT_CONTINUOUS_FIELDS:
        left, right = window(name)
        if left.shape != right.shape:
            mismatched.append(name)
            continue
        value = (
            float(torch.max(torch.abs(left - right))) if left.numel() else 0.0
        )
        if value > error:
            error, worst = value, name
    segment_failures = _audit_segment_mismatches(
        reconstruction, trajectory, complete=stop >= int(trajectory.time_steps)
    )
    if segment_failures:
        mismatched.append("segments")
    return {
        "discrete_mismatch": float(bool(mismatched)),
        "mismatched_fields": tuple(mismatched),
        "continuous": error,
        "continuous_field": worst,
        "segment_mismatch": float(bool(segment_failures)),
        "segment_environments": segment_failures,
    }


def _pack_trajectory_once(trajectory: EventTrajectory, device: torch.device) -> EventTrajectory:
    """Transfer the collected tensor package once and reuse it for all epochs."""

    tensor_fields = (
        "observations", "active_mask", "orders", "actions", "old_log_probs",
        "old_values", "rewards", "terminal", "hidden_before", "hidden_after",
        "prefix_counts", "primitive_z", "event_kind", "event_inputs",
        "event_categorical_actions", "event_u", "event_new_z", "event_cat_mask",
        "event_mark_mask", "event_old_cat_logp", "event_old_mark_component_logp",
        "event_old_joint_logp", "event_z_pre", "candidate_u", "candidate_z",
        "membership_epoch", "segment_id", "q_before",
        "bootstrap_values",
    )
    return replace(
        trajectory,
        **{name: getattr(trajectory, name).to(device) for name in tensor_fields},
    )


def compute_gae(trajectory: EventTrajectory, *, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    rewards = trajectory.rewards.to(device); values = trajectory.old_values.to(device); terminal = trajectory.terminal.to(device); advantages = torch.zeros_like(rewards); running = torch.zeros(rewards.shape[1], device=device); next_value = trajectory.bootstrap_values.to(device)
    for time in reversed(range(rewards.shape[0])):
        continuation = (~terminal[time]).to(rewards.dtype); delta = rewards[time] + GAMMA * next_value * continuation - values[time]; running = delta + GAMMA * GAE_LAMBDA * continuation * running; advantages[time] = running; next_value = values[time]
    returns = advantages + values; return (advantages - advantages.mean()) / advantages.std(unbiased=False).clamp_min(1e-8), returns


def optimizer_ownership_manifest(arm: CommitmentArm) -> dict[str, Any]:
    """Canonical ordered optimizer ownership for the frozen arm architecture."""

    names = {id(parameter): name for name, parameter in arm.named_parameters()}

    def group(parameters: list[nn.Parameter]) -> list[dict[str, Any]]:
        return [
            {
                "name": names[id(parameter)],
                "shape": [int(value) for value in parameter.shape],
                "numel": int(parameter.numel()),
            }
            for parameter in parameters
        ]

    return {
        "schema_version": OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
        "arm": arm.arm,
        "groups": {
            "base": group(arm.base_optimizer_parameters()),
            "event": group(arm.event_parameters()),
        },
    }


def _gradient_summaries(
    arm: CommitmentArm, parameters: list[nn.Parameter]
) -> list[dict[str, Any]]:
    names = {id(parameter): name for name, parameter in arm.named_parameters()}
    summaries: list[dict[str, Any]] = []
    for parameter in parameters:
        gradient = parameter.grad
        present = gradient is not None
        if gradient is None:
            nonfinite = zero = 0
            squared_l2 = maxabs = 0.0
            digest = hashlib.sha256(b"").hexdigest()
            dtype = "<f4"
            payload = None
        else:
            contiguous = gradient.detach().contiguous()
            cpu = contiguous.cpu()
            array = np.asarray(
                cpu.numpy(), dtype=np.dtype(cpu.numpy().dtype).newbyteorder("<"),
                order="C",
            )
            raw = array.tobytes(order="C")
            widened = array.astype(np.float64)
            nonfinite = int((~np.isfinite(array)).sum())
            zero = int((array == 0).sum())
            squared_l2 = float(np.square(widened).sum())
            maxabs = float(np.abs(widened).max()) if array.size else 0.0
            encoded = base64.b64encode(zlib.compress(raw, level=9)).decode("ascii")
            digest = hashlib.sha256(raw).hexdigest()
            dtype = array.dtype.str
            payload = {
                "encoding": "zlib9_base64", "dtype": dtype,
                "shape": [int(value) for value in parameter.shape],
                "uncompressed_nbytes": len(raw), "data": encoded,
            }
        summaries.append({
            "name": names[id(parameter)],
            "shape": [int(value) for value in parameter.shape],
            "numel": int(parameter.numel()),
            "dtype": dtype,
            "gradient_present": bool(present),
            "nonfinite_count": nonfinite,
            "zero_count": zero,
            "squared_l2": squared_l2,
            "maxabs": maxabs,
            "preclip_gradient_digest": digest,
            "gradient_payload": payload,
        })
    return summaries


def _optimizer_pass_record(
    *, group: str, pass_index: int, step_before: int,
    loss: torch.Tensor, summaries: list[dict[str, Any]],
    loss_components: Mapping[str, float],
    unclipped_norm: torch.Tensor,
) -> dict[str, Any]:
    norm = float(unclipped_norm.detach().cpu())
    clip_coefficient = min(1.0, GRADIENT_CLIP / (norm + OPTIMIZER_CLIP_EPSILON))
    record = {
        "schema_version": OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
        "group": group,
        "pass_index": int(pass_index),
        "step_before": int(step_before),
        "step_after": int(step_before) + 1,
        "raw_loss": float(loss.detach().cpu()),
        "loss_components": dict(loss_components),
        "unclipped_norm": norm,
        "clip_coefficient": clip_coefficient,
        "parameters": summaries,
        "payload_raw_bytes": sum(
            int(value["gradient_payload"]["uncompressed_nbytes"])
            for value in summaries if value["gradient_payload"] is not None
        ),
        "payload_encoded_bytes": sum(
            len(value["gradient_payload"]["data"].encode("ascii"))
            for value in summaries if value["gradient_payload"] is not None
        ),
    }
    record["record_digest"] = _canonical_json_digest(record)
    return record


def optimize_update(
    arm: CommitmentArm,
    base_optimizer: torch.optim.Optimizer,
    event_optimizer: torch.optim.Optimizer | None,
    state: TrainingState,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, Any]:
    if trajectory.cutoff:
        raise ValueError("updates require a complete episode rollout")
    packed = _pack_trajectory_once(trajectory, device)
    arm.train()
    _validated_replay, replay_evidence = validate_replay(
        arm, packed, device=device
    )
    advantages, returns = compute_gae(packed, device=device)
    active = packed.active_mask
    old_logp = packed.old_log_probs
    old_values = packed.old_values
    event_mask = packed.event_kind.eq(CREATE) | packed.event_kind.eq(KEEP) | packed.event_kind.eq(RENEW)
    old_joint = packed.event_old_joint_logp
    has_categorical_events = bool(
        (packed.event_kind.eq(KEEP) | packed.event_kind.eq(RENEW)).any().detach().cpu()
    )
    metrics: dict[str, Any] = {
        "replay": replay_evidence,
        "base_steps": 0,
        "event_steps": 0,
        "primitive_replays": 0,
        "event_head_replays": 0,
        "packed_trajectory_count": 1,
        "base_non_none_gradients": [],
        "base_zero_gradients": [],
        "base_nonfinite_gradient_values": [],
        "base_nonfinite_loss_values": [],
        "base_nonfinite_norm_values": [],
        "event_non_none_gradients": [],
        "event_zero_gradients": [],
        "event_nonfinite_gradient_values": [],
        "event_nonfinite_loss_values": [],
        "event_nonfinite_norm_values": [],
        "ownership_manifest": optimizer_ownership_manifest(arm),
        "base_passes": [],
        "event_passes": [],
    }
    for pass_index in range(int(ppo_passes)):
        primitive = _replay_primitive(arm, packed, device=device)
        metrics["primitive_replays"] += 1
        ratio = torch.exp(primitive[0] - old_logp)
        expanded_advantage = advantages.unsqueeze(-1)
        surrogate = torch.minimum(
            ratio * expanded_advantage,
            torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP)
            * expanded_advantage,
        )
        counts = active.sum(-1).clamp_min(1)
        policy_loss = -(
            torch.where(active, surrogate, 0.0).sum(-1) / counts
        ).mean()
        entropy = (
            torch.where(active, primitive[1], 0.0).sum(-1) / counts
        ).mean()
        clipped_values = old_values + torch.clamp(
            primitive[2] - old_values, -VALUE_CLIP, VALUE_CLIP
        )
        value_loss = torch.maximum(
            (primitive[2] - returns).square(),
            (clipped_values - returns).square(),
        ).mean()
        base_loss = (
            policy_loss + VALUE_COEFFICIENT * value_loss
            - ENTROPY_COEFFICIENT * entropy
        )
        base_optimizer.zero_grad(set_to_none=True)
        base_loss.backward()
        base_parameters = arm.base_optimizer_parameters()
        base_gradient_evidence = _gradient_summaries(
            arm, base_parameters
        )
        base_norm = torch.nn.utils.clip_grad_norm_(base_parameters, GRADIENT_CLIP)
        metrics["base_nonfinite_loss_values"].append(
            int((~torch.isfinite(base_loss)).sum().detach().cpu())
        )
        metrics["base_nonfinite_norm_values"].append(
            int((~torch.isfinite(base_norm)).sum().detach().cpu())
        )
        metrics["base_non_none_gradients"].append(
            sum(parameter.grad is not None for parameter in base_parameters)
        )
        metrics["base_zero_gradients"].append(
            sum(
                parameter.grad is not None
                and bool(torch.count_nonzero(parameter.grad).eq(0).detach().cpu())
                for parameter in base_parameters
            )
        )
        metrics["base_nonfinite_gradient_values"].append(sum(
            int((~torch.isfinite(parameter.grad)).sum().detach().cpu())
            for parameter in base_parameters if parameter.grad is not None
        ))
        base_record = _optimizer_pass_record(
            group="base", pass_index=pass_index + 1,
            step_before=state.base_optimizer_steps + metrics["base_steps"],
            loss=base_loss, summaries=base_gradient_evidence,
            loss_components={
                "policy_loss": float(policy_loss.detach().cpu()),
                "value_loss": float(value_loss.detach().cpu()),
                "primitive_entropy": float(entropy.detach().cpu()),
            },
            unclipped_norm=base_norm,
        )
        metrics["base_passes"].append(base_record)
        base_optimizer.step()
        metrics["base_steps"] += 1

        if event_optimizer is not None:
            events = _replay_event_heads(
                arm, packed, device=device, contexts=None
            )
            metrics["event_head_replays"] += 1
            event_advantage = advantages.unsqueeze(-1).expand_as(event_mask)[event_mask]
            event_ratio = torch.exp(events[7][event_mask] - old_joint[event_mask])
            event_surrogate = torch.minimum(
                event_ratio * event_advantage,
                torch.clamp(event_ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP)
                * event_advantage,
            )
            categorical_mask = events[1]
            categorical_entropy = (
                events[8][categorical_mask].mean()
                if has_categorical_events
                else torch.zeros((), device=device)
            )
            event_loss = (
                -event_surrogate.mean()
                - EVENT_ENTROPY_COEFFICIENT * categorical_entropy
            )
            event_optimizer.zero_grad(set_to_none=True)
            event_loss.backward()
            event_parameters = arm.event_parameters()
            event_gradient_evidence = _gradient_summaries(
                arm, event_parameters
            )
            event_norm = torch.nn.utils.clip_grad_norm_(
                event_parameters, GRADIENT_CLIP
            )
            metrics["event_nonfinite_loss_values"].append(
                int((~torch.isfinite(event_loss)).sum().detach().cpu())
            )
            metrics["event_nonfinite_norm_values"].append(
                int((~torch.isfinite(event_norm)).sum().detach().cpu())
            )
            metrics["event_non_none_gradients"].append(
                sum(parameter.grad is not None for parameter in event_parameters)
            )
            metrics["event_zero_gradients"].append(
                sum(
                    parameter.grad is not None
                    and bool(torch.count_nonzero(parameter.grad).eq(0).detach().cpu())
                    for parameter in event_parameters
                )
            )
            metrics["event_nonfinite_gradient_values"].append(sum(
                int((~torch.isfinite(parameter.grad)).sum().detach().cpu())
                for parameter in event_parameters if parameter.grad is not None
            ))
            event_record = _optimizer_pass_record(
                group="event", pass_index=pass_index + 1,
                step_before=state.event_optimizer_steps + metrics["event_steps"],
                loss=event_loss, summaries=event_gradient_evidence,
                loss_components={
                    "event_policy_loss": float((-event_surrogate.mean()).detach().cpu()),
                    "categorical_entropy": float(categorical_entropy.detach().cpu()),
                },
                unclipped_norm=event_norm,
            )
            metrics["event_passes"].append(event_record)
            event_optimizer.step()
            metrics["event_steps"] += 1
    if metrics["primitive_replays"] != int(ppo_passes):
        raise RuntimeError("primitive replay count drift")
    all_passes = metrics["base_passes"] + metrics["event_passes"]
    encoded_bytes = sum(int(value["payload_encoded_bytes"]) for value in all_passes)
    raw_bytes = sum(int(value["payload_raw_bytes"]) for value in all_passes)
    metrics["evidence_storage"] = {
        "raw_bytes": raw_bytes,
        "encoded_bytes": encoded_bytes,
        "formal_scale_projected_encoded_bytes": encoded_bytes * FORMAL_UPDATES,
    }
    state.completed_update += 1
    state.base_optimizer_steps += int(ppo_passes)
    state.event_optimizer_steps += int(
        ppo_passes if event_optimizer is not None else 0
    )
    return metrics

def _rng_states(state: TrainingState) -> dict[str, Any]:
    if set(state.rngs) != set(RNG_NAMES):
        raise ValueError("owned-RNG key set mismatch")
    return {name: deepcopy(state.rngs[name].bit_generator.state) for name in RNG_NAMES}


def runtime_rng_snapshot() -> dict[str, Any]:
    return {
        "python": deepcopy(random.getstate()),
        "numpy": deepcopy(np.random.get_state()),
        "torch_cpu": torch.get_rng_state().clone(),
        "torch_cuda": [
            value.clone() for value in torch.cuda.get_rng_state_all()
        ] if torch.cuda.is_available() else [],
    }


def _nested_equal(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return torch.equal(left.detach().cpu(), right.detach().cpu())
    if isinstance(left, np.ndarray) and isinstance(right, np.ndarray):
        return np.array_equal(left, right)
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _nested_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        return len(left) == len(right) and all(
            _nested_equal(a, b) for a, b in zip(left, right)
        )
    return bool(left == right)


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
