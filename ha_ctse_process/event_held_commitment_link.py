"""Frozen OR/DUM/EHC event-held commitment package for noncalendar G0."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
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
    DirectPrimitiveARPolicy,
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

ArmName = Literal["OR", "DUM", "EHC"]
EVENT_INPUT_DIM = OBSERVATION_DIM + 32 + 32 + 8
MARK_DIM = 8
OPPORTUNITY_SUPPORT = np.asarray((4, 8, 12), dtype=np.int64)
CREATE, KEEP, RENEW = 1, 2, 3
EVENT_ENTROPY_COEFFICIENT = 0.01
RNG_NAMES = ("ledger", "order", "primitive", "opportunity", "event", "mark")
AUDIT_BRANCHES = (
    "KEEP_HELD_MARK",
    "RENEW_DERANGED_MARK",
    "RENEW_CANDIDATE_MARK",
)


@dataclass
class SegmentRecord:
    episode_id: int
    key: int
    membership_epoch: int
    segment_id: int
    start_active_step: int
    end_active_step: int
    censored: bool
    close_reason: str
    opportunity_count: int

    @property
    def active_lifetime(self) -> int:
        return self.end_active_step - self.start_active_step


@dataclass
class LifecycleState:
    membership_epoch: int
    z: torch.Tensor
    q: int
    segment_id: int
    segment_start_active_step: int
    active_steps: int = 0
    non_create_opportunities: int = 0
    spell_opportunity_count: int = 0
    """Running `K` (KEEP/RENEW opportunities so far) for the currently open
    spell only; reset to 0 only when a RENEW closes that spell and opens the
    next one. At CREATE (`LifecycleState` construction) it is
    zero-initialized, not reset -- there is no prior spell to reset from.
    Distinct from `non_create_opportunities`, which accumulates across all
    spells of this lifecycle and is never reset."""


@dataclass
class CollectionCursor:
    episode_ids: tuple[int, ...]
    ledgers: tuple[NoncalendarLedger, ...]
    environments: list[NoncalendarTrackingEnv]
    hidden: torch.Tensor
    lifecycles: list[dict[int, LifecycleState]]
    segments: list[list[SegmentRecord]]


@dataclass
class EventTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    orders: torch.Tensor
    actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    rewards: torch.Tensor
    terminal: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_counts: torch.Tensor
    primitive_z: torch.Tensor
    event_kind: torch.Tensor
    event_inputs: torch.Tensor
    event_categorical_actions: torch.Tensor
    event_u: torch.Tensor
    event_z_pre: torch.Tensor
    event_new_z: torch.Tensor
    candidate_u: torch.Tensor
    candidate_z: torch.Tensor
    event_cat_mask: torch.Tensor
    event_mark_mask: torch.Tensor
    event_old_cat_logp: torch.Tensor
    event_old_mark_component_logp: torch.Tensor
    event_old_joint_logp: torch.Tensor
    membership_epoch: torch.Tensor
    segment_id: torch.Tensor
    q_before: torch.Tensor
    raw_event_trace: tuple[dict[str, Any], ...]
    outcomes: tuple[TrackingOutcome, ...]
    segments: tuple[tuple[SegmentRecord, ...], ...]
    ledger_ids: tuple[int, ...]
    cutoff: bool
    bootstrap_values: torch.Tensor
    rng_audit: dict[str, Any]
    cursor: CollectionCursor | None

    @property
    def time_steps(self) -> int:
        return int(self.rewards.shape[0])


class CommitmentArm(nn.Module):
    """Ordinary source base plus the exact DUM/EHC additions."""

    def __init__(self, arm: ArmName) -> None:
        super().__init__()
        if arm not in ("OR", "DUM", "EHC"):
            raise ValueError("invalid commitment arm")
        self.arm: ArmName = arm
        self.base = DirectPrimitiveARPolicy()
        if arm != "OR":
            self.W_z = nn.Linear(MARK_DIM, ACTION_COUNT, bias=False)
            self.event_head = nn.Linear(EVENT_INPUT_DIM, 2)
            self.mark_head = nn.Linear(EVENT_INPUT_DIM, 2 * MARK_DIM)
        else:
            self.W_z = None
            self.event_head = None
            self.mark_head = None

    @property
    def treatment(self) -> int:
        return int(self.arm == "EHC")

    @property
    def base_parameter_count(self) -> int:
        return sum(p.numel() for p in self.base.parameters())

    @property
    def added_parameter_count(self) -> int:
        return sum(p.numel() for n, p in self.named_parameters() if not n.startswith("base."))

    def primitive_bias(self, z: torch.Tensor) -> torch.Tensor | None:
        if self.W_z is None:
            return None
        return self.W_z(float(self.treatment) * z.detach())

    def event_parameters(self) -> list[nn.Parameter]:
        if self.arm == "OR":
            return []
        assert self.event_head is not None and self.mark_head is not None
        return [*self.event_head.parameters(), *self.mark_head.parameters()]

    def base_optimizer_parameters(self) -> list[nn.Parameter]:
        values = list(self.base.parameters())
        if self.W_z is not None:
            values.extend(self.W_z.parameters())
        return values


@dataclass
class TrainingState:
    arm: ArmName
    replicate: int
    profile: Literal["train", "iid", "held_out"] = "train"
    seed_map: dict[str, int] = field(default_factory=dict)
    completed_update: int = 0
    next_episode_id: int = 0
    base_optimizer_steps: int = 0
    event_optimizer_steps: int = 0
    pending_cursor: CollectionCursor | None = None
    rngs: dict[str, np.random.Generator] = field(default_factory=dict)


def _seed(base: int, replicate: int) -> int:
    return int(base + 1000 * replicate)


def authoritative_seed_map(
    profile: Literal["train", "iid", "held_out"], replicate: int
) -> dict[str, int]:
    ledger_base = TRAIN_TASK_SEED if profile == "train" else (
        IID_EVAL_TASK_SEED if profile == "iid" else HELD_OUT_EVAL_TASK_SEED
    )
    return {
        "ledger": _seed(ledger_base, replicate),
        "order": _seed(TRAIN_ORDER_SEED, replicate),
        "primitive": _seed(TRAIN_ACTION_SEED, replicate),
        "opportunity": _seed(OPPORTUNITY_SEED, replicate),
        "event": _seed(EVENT_SEED, replicate),
        "mark": _seed(MARK_SEED, replicate),
    }


def make_training_state(
    arm: ArmName,
    replicate: int,
    *,
    profile: Literal["train", "iid", "held_out"] = "train",
) -> TrainingState:
    seed_map = authoritative_seed_map(profile, replicate)
    return TrainingState(
        arm=arm,
        replicate=int(replicate),
        profile=profile,
        seed_map=seed_map,
        rngs={name: np.random.default_rng(seed_map[name]) for name in RNG_NAMES},
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


def _normal_parameters(mark_output: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    mu, raw_scale = mark_output.split(MARK_DIM, dim=-1)
    return mu, 0.1 + 0.9 * torch.sigmoid(raw_scale)


def transformed_mark_component_logp(u: torch.Tensor, mu: torch.Tensor, sigma: torch.Tensor) -> torch.Tensor:
    normal = -0.5 * torch.square((u - mu) / sigma) - torch.log(sigma) - 0.5 * math.log(2.0 * math.pi)
    log_jacobian = 2.0 * (math.log(2.0) - u - F.softplus(-2.0 * u))
    return normal - log_jacobian


def _event_input(observation: torch.Tensor, h_pre: torch.Tensor, context: torch.Tensor, z_pre: torch.Tensor) -> torch.Tensor:
    value = torch.cat((observation, h_pre, context, z_pre), dim=-1).detach()
    if value.shape[-1] != EVENT_INPUT_DIM:
        raise RuntimeError("event input width mismatch")
    return value


def _new_cursor(
    state: TrainingState, episode_ids: tuple[int, ...], device: torch.device,
    *, profile: Literal["train", "iid", "held_out"],
    audit_trace: dict[str, list[dict[str, Any]]] | None = None,
) -> CollectionCursor:
    if state.profile != profile or state.seed_map != authoritative_seed_map(profile, state.replicate):
        raise ValueError("collector state/profile seed map mismatch")
    ledgers = tuple(
        make_noncalendar_ledger(
            v, profile=profile, task_seed=state.seed_map["ledger"],
            order_seed=state.seed_map["order"], audit_trace=audit_trace,
        )
        for v in episode_ids
    )
    return CollectionCursor(
        episode_ids=episode_ids,
        ledgers=ledgers,
        environments=[NoncalendarTrackingEnv(v) for v in ledgers],
        hidden=torch.zeros((len(episode_ids), MAX_LIFECYCLES, 32), device=device),
        lifecycles=[{} for _ in episode_ids],
        segments=[[] for _ in episode_ids],
    )


def _close_segment(cursor: CollectionCursor, env_index: int, key: int, *, reason: str, censored: bool) -> None:
    life = cursor.lifecycles[env_index].pop(key)
    cursor.segments[env_index].append(SegmentRecord(cursor.episode_ids[env_index], key, life.membership_epoch, life.segment_id, life.segment_start_active_step, life.active_steps, censored, reason, life.spell_opportunity_count))


def _zeros(shape: tuple[int, ...], *, dtype: torch.dtype = torch.float32) -> torch.Tensor:
    return torch.zeros(shape, dtype=dtype)


def _ledger_audit_evidence(ledger: NoncalendarLedger) -> dict[str, Any]:
    payload = {
        "episode_id": int(ledger.episode_id), "base_id": int(ledger.base_id),
        "sign_parity": int(ledger.sign_parity), "profile": ledger.profile,
        "generation_attempt": int(ledger.generation_attempt),
        "routing_permutation": list(ledger.routing_permutation),
        "initial_count": int(ledger.initial_count),
        "temporary_key": int(ledger.temporary_key),
        "terminal_key": int(ledger.terminal_key),
        "duration_streams": ledger.duration_streams.tolist(),
        "initial_targets": ledger.initial_targets.tolist(),
        "direct_frontier_priorities": ledger.direct_frontier_priorities.tolist(),
    }
    return payload | {"ledger_digest": _canonical_json_digest(payload)}


_RNG_BINDING_KEYS = frozenset({
    "schema_version", "context", "stream", "seed", "start_state",
    "draw_schedule", "draw_bytes_digest", "end_state", "binding_digest",
})
_RNG_SCHEDULE_KEYS = frozenset({
    "stream", "operation", "dtype", "shape", "coordinates"
})


def _canonical_json_digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _float32_payload(value: np.ndarray) -> dict[str, Any]:
    """Canonical exact binary32 payload without any outcome information."""

    array = np.ascontiguousarray(value, dtype=np.float32)
    encoded = array.tobytes(order="C")
    return {
        "dtype": "float32",
        "shape": [int(size) for size in array.shape],
        "values": array.tolist(),
        "bytes_b64": base64.b64encode(encoded).decode("ascii"),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _raw_event_trace_digest(row_without_digest: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        row_without_digest, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(b"HMASD_RAW_EVENT_TRACE_V1\0" + encoded).hexdigest()


def owned_rng_states(state: TrainingState) -> dict[str, Any]:
    """Return canonical, independently cloneable owned-generator states."""

    return {
        name: deepcopy(state.rngs[name].bit_generator.state)
        for name in RNG_NAMES
    }


def collection_rng_schedules(
    trajectory: EventTrajectory, *, deterministic: bool
) -> dict[str, list[dict[str, Any]]]:
    """Reconstruct the collector's exact per-stream draw calls.

    Values are deliberately absent.  A validator replays these calls from the
    canonical start state and regenerates the bytes and end state itself.
    """

    schedules = deepcopy(trajectory.rng_audit["streams"])
    if set(schedules) != set(RNG_NAMES):
        raise RuntimeError("collector RNG audit stream set mismatch")
    return schedules


def _replay_rng_schedule(
    start_state: Mapping[str, Any], schedule: list[dict[str, Any]],
    *, seed: int | None = None,
) -> tuple[str, dict[str, Any], list[np.ndarray]]:
    generator = np.random.default_rng()
    generator.bit_generator.state = deepcopy(dict(start_state))
    digest = hashlib.sha256()
    arrays: list[np.ndarray] = []
    seeded_generators: dict[tuple[Any, ...], np.random.Generator] = {}
    for entry in schedule:
        if not isinstance(entry, dict) or set(entry) != _RNG_SCHEDULE_KEYS:
            raise ValueError("RNG draw schedule schema mismatch")
        shape = tuple(int(value) for value in entry["shape"])
        if any(value < 0 for value in shape):
            raise ValueError("RNG draw schedule has a negative shape")
        dtype = np.dtype(str(entry["dtype"]))
        operation = str(entry["operation"])
        if operation.startswith("seeded_"):
            if seed is None:
                raise ValueError("seeded RNG audit operation lacks authoritative seed")
            coordinates = entry["coordinates"]
            identity = (
                int(coordinates["episode_id"]), int(coordinates["attempt"]),
                *tuple(int(value) for value in coordinates["generator_coordinates"]),
            )
            local = seeded_generators.get(identity)
            if local is None:
                local = make_rng(
                    int(seed), *tuple(
                        int(value) for value in coordinates["generator_coordinates"]
                    )
                )
                seeded_generators[identity] = local
            argument = coordinates.get("argument")
            if operation == "seeded_permutation":
                drawn = local.permutation(
                    int(argument) if isinstance(argument, int)
                    else np.asarray(argument, dtype=dtype)
                )
            elif operation == "seeded_permutation_blocks":
                expected_shape = (
                    len(coordinates["key_order"]),
                    len(coordinates["offset_order"]),
                    len(argument),
                )
                if shape != expected_shape:
                    raise ValueError("duration permutation block shape mismatch")
                drawn = np.empty(shape, dtype=dtype)
                values = np.asarray(argument, dtype=dtype)
                for key_index, _key in enumerate(coordinates["key_order"]):
                    for offset_index, _offset in enumerate(
                        coordinates["offset_order"]
                    ):
                        drawn[key_index, offset_index] = local.permutation(values)
            elif operation == "seeded_choice":
                drawn = local.choice(
                    np.asarray(argument, dtype=dtype),
                    size=shape if shape else None,
                    replace=bool(coordinates["replace"]),
                )
            elif operation == "seeded_random":
                drawn = local.random(shape, dtype=dtype)
            else:
                raise ValueError("unknown seeded RNG audit operation")
        elif operation == "random":
            drawn = generator.random(shape, dtype=dtype)
        elif operation == "standard_normal" and dtype == np.dtype(np.float64):
            drawn = generator.standard_normal(shape)
        elif operation == "choice_opportunity" and dtype == np.dtype(np.int64):
            drawn = generator.choice(OPPORTUNITY_SUPPORT, size=shape)
        else:
            raise ValueError("RNG draw schedule operation/dtype mismatch")
        array = np.asarray(drawn, dtype=dtype).reshape(shape)
        digest.update(array.tobytes(order="C"))
        arrays.append(array.copy())
    return digest.hexdigest(), deepcopy(generator.bit_generator.state), arrays


def replay_rng_schedule_end_state(
    start_state: Mapping[str, Any], schedule: list[dict[str, Any]],
    *, seed: int | None = None,
) -> dict[str, Any]:
    """Public state-only replay used to validate a Stage-2 fork coordinate."""

    return _replay_rng_schedule(start_state, schedule, seed=seed)[1]


def replay_rng_schedule_arrays(
    start_state: Mapping[str, Any], schedule: list[dict[str, Any]],
    *, seed: int | None = None,
) -> tuple[list[np.ndarray], dict[str, Any]]:
    """Replay and expose generated arrays for strict Stage-2 consumption audit."""

    _digest, end_state, arrays = _replay_rng_schedule(
        start_state, schedule, seed=seed
    )
    return arrays, end_state


def make_rng_binding(
    *, context: Mapping[str, Any], stream: str, seed: int,
    start_state: Mapping[str, Any], draw_schedule: list[dict[str, Any]],
    expected_end_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Create a context-bound record only after independent schedule replay."""

    if stream not in RNG_NAMES:
        raise ValueError("unknown owned RNG stream")
    if any(entry.get("stream") != stream for entry in draw_schedule):
        raise ValueError("RNG draw schedule stream label mismatch")
    draw_digest, end_state, _arrays = _replay_rng_schedule(
        start_state, draw_schedule, seed=seed
    )
    if end_state != dict(expected_end_state):
        raise RuntimeError(f"RNG schedule does not reach supplied {stream} end state")
    record: dict[str, Any] = {
        "schema_version": RNG_BINDING_SCHEMA_VERSION,
        "context": deepcopy(dict(context)),
        "stream": stream,
        "seed": int(seed),
        "start_state": deepcopy(dict(start_state)),
        "draw_schedule": deepcopy(draw_schedule),
        "draw_bytes_digest": draw_digest,
        "end_state": end_state,
    }
    record["binding_digest"] = _canonical_json_digest(record)
    return record


def validate_rng_binding(
    record: Any, *, expected_context: Mapping[str, Any], expected_stream: str,
    expected_seed: int, expected_start_state: Mapping[str, Any],
) -> tuple[bool, dict[str, Any] | None]:
    """Regenerate draws and state; supplied digests are never trusted."""

    try:
        if not isinstance(record, dict) or set(record) != _RNG_BINDING_KEYS:
            return False, None
        if not (
            int(record["schema_version"]) == RNG_BINDING_SCHEMA_VERSION
            and record["context"] == dict(expected_context)
            and record["stream"] == expected_stream
            and int(record["seed"]) == int(expected_seed)
            and record["start_state"] == dict(expected_start_state)
            and all(
                entry.get("stream") == expected_stream
                for entry in record["draw_schedule"]
            )
        ):
            return False, None
        draw_digest, end_state, _arrays = _replay_rng_schedule(
            record["start_state"], record["draw_schedule"],
            seed=int(expected_seed),
        )
        payload = {key: deepcopy(value) for key, value in record.items()
                   if key != "binding_digest"}
        if not (
            draw_digest == record["draw_bytes_digest"]
            and end_state == record["end_state"]
            and _canonical_json_digest(payload) == record["binding_digest"]
        ):
            return False, None
        return True, end_state
    except (KeyError, TypeError, ValueError, OverflowError):
        return False, None


@dataclass
class _AuditRowStream:
    """One fork-row replay stream with independent consumption state."""

    values: np.ndarray
    position: int = 0

    def _take(self, size: int) -> np.ndarray:
        stop = self.position + int(size)
        if stop > int(self.values.size):
            raise RuntimeError("batched fork row stream exhausted")
        result = self.values.reshape(-1)[self.position:stop].copy()
        self.position = stop
        return result

    def random(
        self, size: int | tuple[int, ...] | None = None, dtype: Any = np.float64
    ) -> np.ndarray | float:
        shape = () if size is None else ((size,) if isinstance(size, int) else tuple(size))
        count = int(np.prod(shape, dtype=np.int64)) if shape else 1
        result = self._take(count).astype(dtype, copy=False)
        return float(result[0]) if not shape else result.reshape(shape)

    def standard_normal(
        self, size: int | tuple[int, ...] | None = None
    ) -> np.ndarray | float:
        return self.random(size=size, dtype=np.float64)

    def choice(self, _support: Any, size: int | tuple[int, ...] | None = None) -> Any:
        result = self.random(size=size, dtype=np.int64)
        return int(result) if size is None else result

    def consumption_record(self, terminal_state: Mapping[str, Any]) -> dict[str, Any]:
        consumed = self.values.reshape(-1)[: self.position]
        return {
            "position": int(self.position),
            "consumed_bytes_digest": hashlib.sha256(
                consumed.tobytes(order="C")
            ).hexdigest(),
            "terminal_state": deepcopy(dict(terminal_state)),
        }


def _audit_row_draw(
    row_rngs: list[Mapping[str, _AuditRowStream]],
    requests: list[tuple[int, int, int, torch.Tensor, torch.Tensor]],
    name: str,
    *,
    width: int = 1,
    dtype: Any = np.float64,
) -> np.ndarray:
    values = np.empty((len(requests), width), dtype=dtype)
    offset = 0
    while offset < len(requests):
        env_index = int(requests[offset][0])
        stop = offset + 1
        while stop < len(requests) and int(requests[stop][0]) == env_index:
            stop += 1
        shape: int | tuple[int, int] = (
            stop - offset if width == 1 else (stop - offset, width)
        )
        method = (
            row_rngs[env_index][name].standard_normal
            if name == "mark"
            else row_rngs[env_index][name].random
        )
        drawn = np.asarray(method(shape), dtype=dtype).reshape(stop - offset, width)
        values[offset:stop] = drawn
        offset = stop
    return values[:, 0] if width == 1 else values


def _row_stable_event_heads(
    inputs: torch.Tensor,
    event_head: nn.Linear,
    mark_head: nn.Linear,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Evaluate both event heads with one row-local float32 reduction path.

    Each output coordinate is reduced only across that row's input features,
    so its binary32 result cannot depend on the number or ordering of other
    packed requests. Collection, fork collection and teacher replay all call
    this helper; there is intentionally no direct ``nn.Linear`` replay path.
    """

    if not (
        inputs.dtype == torch.float32
        and event_head.weight.dtype == torch.float32
        and mark_head.weight.dtype == torch.float32
        and event_head.bias is not None
        and mark_head.bias is not None
        and event_head.bias.dtype == torch.float32
        and mark_head.bias.dtype == torch.float32
    ):
        raise RuntimeError("event/mark heads require explicit float32 evaluation")
    row_count = int(inputs.shape[0])
    # CUDA selects a different small-outer-dimension reduction below the
    # registered 16-environment collection width. Zero-row padding keeps
    # every partition on the same reduction path while retaining the exact
    # arithmetic already used by registered collection (which has at least
    # one live request per environment). Rows remain mutually independent.
    padded_inputs = (
        F.pad(inputs, (0, 0, 0, FORMAL_NUM_ENVS - row_count))
        if row_count < FORMAL_NUM_ENVS
        else inputs
    )

    def evaluate(layer: nn.Linear) -> torch.Tensor:
        output = (
            padded_inputs.unsqueeze(1) * layer.weight.unsqueeze(0)
        ).sum(dim=-1) + layer.bias
        return output[:row_count]

    return evaluate(event_head), evaluate(mark_head)


def collect_trajectory(
    arm: CommitmentArm,
    state: TrainingState,
    *,
    device: torch.device,
    episode_ids: Iterable[int] | None = None,
    cursor: CollectionCursor | None = None,
    max_steps: int | None = None,
    deterministic: bool = False,
    profile: Literal["train", "iid", "held_out"] = "train",
    forced_event: tuple[int, int, int, int, torch.Tensor] | None = None,
    forced_events: Mapping[tuple[int, int, int], tuple[int, torch.Tensor]] | None = None,
    row_rngs: list[Mapping[str, _AuditRowStream]] | None = None,
) -> EventTrajectory:
    if state.arm != arm.arm or set(state.rngs) != set(RNG_NAMES):
        raise ValueError("collector arm or owned-RNG key set mismatch")
    rng_trace: dict[str, list[dict[str, Any]]] = {
        name: [] for name in RNG_NAMES
    }
    request_evidence: list[dict[str, Any]] = []
    raw_event_trace: list[dict[str, Any]] = []
    if cursor is None:
        ids = tuple(int(v) for v in episode_ids) if episode_ids is not None else tuple(
            range(state.next_episode_id, state.next_episode_id + FORMAL_NUM_ENVS)
        )
        if not ids:
            raise ValueError("collection requires episodes")
        cursor = _new_cursor(
            state, ids, device, profile=profile, audit_trace=rng_trace
        )
    else:
        if episode_ids is not None:
            raise ValueError("cursor continuation does not accept episode_ids")
        cursor_profile = cursor.ledgers[0].profile
        if any(ledger.profile != cursor_profile for ledger in cursor.ledgers):
            raise ValueError("mixed-profile collection cursor")
        profile = cursor_profile
        if state.profile != profile:
            raise ValueError("cursor/state profile mismatch")
    env_count = len(cursor.environments)
    ledger_evidence = tuple(_ledger_audit_evidence(value) for value in cursor.ledgers)
    if row_rngs is not None and len(row_rngs) != env_count:
        raise ValueError("fork row RNG count must match the collection width")
    remaining = HORIZON - cursor.environments[0].time
    steps = remaining if max_steps is None else min(int(max_steps), remaining)
    if steps <= 0 or any(env.time != cursor.environments[0].time for env in cursor.environments):
        raise ValueError("invalid synchronized collection cursor")

    names = (
        "observations", "active", "orders", "actions", "logp", "values", "rewards",
        "terminal", "h_before", "h_after", "prefix", "z", "kind", "event_input",
        "event_action", "event_u", "event_z_pre", "event_new_z", "candidate_u",
        "candidate_z", "cat_mask",
        "mark_mask", "old_cat", "old_mark", "old_joint", "epoch", "segment", "q",
    )
    rows: dict[str, list[torch.Tensor]] = {name: [] for name in names}
    arm.eval()
    with torch.no_grad():
        for _ in range(steps):
            time = cursor.environments[0].time
            cursor.hidden = cursor.hidden.detach().clone()
            obs_np = np.zeros((env_count, MAX_LIFECYCLES, OBSERVATION_DIM), dtype=np.float32)
            active_np = np.zeros((env_count, MAX_LIFECYCLES), dtype=np.bool_)
            views = []
            for env_index, env in enumerate(cursor.environments):
                view = env.observe()
                views.append(view)
                for row_index, key in enumerate(view.active_keys):
                    obs_np[env_index, key] = view.observations[row_index]
                    active_np[env_index, key] = True
                for key in view.membership_change.terminally_left:
                    if arm.arm != "OR":
                        _close_segment(cursor, env_index, key, reason="TERMINAL_LEAVE", censored=True)
                    cursor.hidden[env_index, key].zero_()
                if arm.arm != "OR":
                    for key in view.membership_change.rejoined:
                        life = cursor.lifecycles[env_index].get(key)
                        if life is None:
                            raise RuntimeError("REJOIN lacks owned commitment lifecycle")
                        environment_epoch = cursor.environments[env_index].members[key].membership_epoch
                        if environment_epoch != life.membership_epoch + 1:
                            raise RuntimeError("REJOIN membership epoch is not the next owned epoch")
                        life.membership_epoch = environment_epoch
                    for key in view.membership_change.joined:
                        if key in cursor.lifecycles[env_index]:
                            raise RuntimeError("JOIN reused commitment lifecycle")
                        epoch = cursor.environments[env_index].members[key].membership_epoch
                        cursor.lifecycles[env_index][key] = LifecycleState(
                            epoch, torch.zeros(MARK_DIM, device=device), -1, 0, 0
                        )

            observations = torch.as_tensor(obs_np, device=device)
            active = torch.as_tensor(active_np, device=device)
            order_np = frontier_order(cursor.ledgers, active_np, time)
            order = torch.as_tensor(order_np, device=device)
            h_before = cursor.hidden.clone()
            prepared = arm.base.prepare_step(
                observations=observations, active_mask=active, validated=True
            )

            kind = torch.zeros((env_count, MAX_LIFECYCLES), dtype=torch.long, device=device)
            event_inputs = torch.zeros((env_count, MAX_LIFECYCLES, EVENT_INPUT_DIM), device=device)
            event_actions = torch.full((env_count, MAX_LIFECYCLES), -1, dtype=torch.long, device=device)
            event_u = torch.zeros((env_count, MAX_LIFECYCLES, MARK_DIM), device=device)
            event_z_pre = torch.zeros_like(event_u)
            event_new_z = torch.zeros_like(event_u)
            candidate_u = torch.zeros_like(event_u)
            candidate_z = torch.zeros_like(event_u)
            cat_mask = torch.zeros((env_count, MAX_LIFECYCLES), dtype=torch.bool, device=device)
            mark_mask = torch.zeros_like(cat_mask)
            old_cat = torch.zeros((env_count, MAX_LIFECYCLES), device=device)
            old_mark = torch.zeros((env_count, MAX_LIFECYCLES, MARK_DIM), device=device)
            old_joint = torch.zeros((env_count, MAX_LIFECYCLES), device=device)
            epochs = torch.full((env_count, MAX_LIFECYCLES), -1, dtype=torch.long, device=device)
            segments = torch.full_like(epochs, -1)
            q_before = torch.full_like(epochs, -1)
            primitive_z = torch.zeros((env_count, MAX_LIFECYCLES, MARK_DIM), device=device)
            requests: list[tuple[int, int, int, torch.Tensor, torch.Tensor]] = []

            if arm.arm != "OR":
                for env_index, view in enumerate(views):
                    for key in view.active_keys:
                        life = cursor.lifecycles[env_index][key]
                        primitive_z[env_index, key] = life.z
                        epochs[env_index, key] = life.membership_epoch
                        segments[env_index, key] = life.segment_id
                        q_before[env_index, key] = life.q
                        request_kind = CREATE if life.q < 0 else (KEEP if life.q == 0 else 0)
                        if request_kind:
                            z_pre = life.z.detach()
                            inp = _event_input(
                                observations[env_index, key],
                                h_before[env_index, key],
                                prepared.context[env_index],
                                z_pre,
                            )
                            requests.append((env_index, key, request_kind, inp, z_pre))

            request_coordinates = [
                [int(env_index), int(key), int(request_kind)]
                for env_index, key, request_kind, _inp, _z_pre in requests
            ]
            request_evidence.append({
                "time": int(time),
                "environments": [
                    {
                        "env_index": int(env_index),
                        "episode_id": int(cursor.episode_ids[env_index]),
                        "frontier": [
                            {
                                "key": int(key),
                                "priority": float(
                                    cursor.ledgers[env_index]
                                    .direct_frontier_priorities[time, key]
                                ),
                                "q_before": (
                                    int(cursor.lifecycles[env_index][int(key)].q)
                                    if arm.arm != "OR" else None
                                ),
                            }
                            for key in order_np[env_index] if int(key) >= 0
                        ],
                    }
                    for env_index in range(env_count)
                ],
            })

            selected_kind_grid = torch.zeros_like(kind)
            request_q = np.empty(len(requests), dtype=np.int64)
            trace_payload_values: np.ndarray | None = None
            if requests:
                assert arm.event_head is not None and arm.mark_head is not None
                packed_inputs = torch.stack([value[3] for value in requests])
                packed_z_pre = torch.stack([value[4] for value in requests])
                # All collection modes and teacher replay deliberately share
                # this one row-local binary32 head evaluation.
                logits, mark_output = _row_stable_event_heads(
                    packed_inputs, arm.event_head, arm.mark_head
                )
                mu, sigma = _normal_parameters(mark_output)
                create_mask = torch.as_tensor(
                    [value[2] == CREATE for value in requests], dtype=torch.bool, device=device
                )
                if deterministic:
                    selected_cat = torch.argmax(logits, dim=-1)
                    u = mu
                else:
                    rng_trace["event"].append({
                        "stream": "event", "operation": "random",
                        "dtype": "float64", "shape": [len(requests)],
                        "coordinates": {
                            "time": int(time), "requests": request_coordinates,
                        },
                    })
                    event_values = (
                        state.rngs["event"].random(len(requests))
                        if row_rngs is None
                        else _audit_row_draw(row_rngs, requests, "event")
                    )
                    event_uniforms = torch.as_tensor(
                        event_values,
                        dtype=logits.dtype,
                        device=device,
                    )
                    selected_cat = torch.sum(
                        event_uniforms.unsqueeze(-1) > torch.cumsum(torch.softmax(logits, -1), -1),
                        dim=-1,
                    ).clamp(max=1)
                    rng_trace["mark"].append({
                        "stream": "mark", "operation": "standard_normal",
                        "dtype": "float64", "shape": [len(requests), MARK_DIM],
                        "coordinates": {
                            "time": int(time), "requests": request_coordinates,
                        },
                    })
                    mark_values = (
                        state.rngs["mark"].standard_normal(
                            (len(requests), MARK_DIM)
                        )
                        if row_rngs is None
                        else _audit_row_draw(
                            row_rngs, requests, "mark", width=MARK_DIM
                        )
                    )
                    mark_eps = torch.as_tensor(
                        mark_values,
                        dtype=mu.dtype,
                        device=device,
                    )
                    u = mu + sigma * mark_eps
                selected_kind = torch.where(create_mask, torch.full_like(selected_cat, CREATE), selected_cat + KEEP)
                active_forced: dict[tuple[int, int], tuple[int, torch.Tensor]] = {}
                if forced_event is not None and time == int(forced_event[0]):
                    active_forced[(int(forced_event[1]), int(forced_event[2]))] = (
                        int(forced_event[3]), forced_event[4]
                    )
                if forced_events is not None:
                    active_forced.update({
                        (int(env), int(key)): (int(kind), new_z)
                        for (forced_time, env, key), (kind, new_z)
                        in forced_events.items() if int(forced_time) == time
                    })
                forced_indices: list[tuple[int, torch.Tensor]] = []
                if active_forced:
                    selected_cat = selected_cat.clone()
                    selected_kind = selected_kind.clone()
                for (forced_env, forced_key), (forced_kind, forced_value) in active_forced.items():
                    matching = [
                        index for index, value in enumerate(requests)
                        if value[0] == forced_env and value[1] == forced_key
                    ]
                    if len(matching) != 1:
                        raise RuntimeError("forced event coordinate is not one request")
                    forced_index = matching[0]
                    if forced_kind not in (KEEP, RENEW) or bool(create_mask[forced_index]):
                        raise ValueError("forced event must be a non-CREATE KEEP/RENEW")
                    selected_cat[forced_index] = forced_kind - KEEP
                    selected_kind[forced_index] = forced_kind
                    forced_indices.append((forced_index, forced_value.to(device).detach()))
                derived_cat_mask = ~create_mask
                derived_mark_mask = create_mask | selected_kind.eq(RENEW)
                component_logp = transformed_mark_component_logp(u.detach(), mu, sigma)
                categorical_logp = torch.gather(
                    F.log_softmax(logits, -1), 1, selected_cat.unsqueeze(-1)
                ).squeeze(-1)
                categorical_logp = torch.where(derived_cat_mask, categorical_logp, 0.0)
                component_logp = torch.where(
                    derived_mark_mask.unsqueeze(-1), component_logp, 0.0
                )
                candidate_tanh_u = torch.tanh(u).detach()
                packed_new_z = torch.where(
                    derived_mark_mask.unsqueeze(-1), candidate_tanh_u, packed_z_pre
                )
                if forced_indices:
                    packed_new_z = packed_new_z.clone()
                    for forced_index, forced_value in forced_indices:
                        packed_new_z[forced_index] = forced_value
                joint_logp = categorical_logp + component_logp.sum(-1)
                env_indices = torch.as_tensor([v[0] for v in requests], dtype=torch.long, device=device)
                key_indices = torch.as_tensor([v[1] for v in requests], dtype=torch.long, device=device)
                kind[env_indices, key_indices] = selected_kind
                selected_kind_grid[env_indices, key_indices] = selected_kind
                event_actions[env_indices, key_indices] = torch.where(
                    derived_cat_mask, selected_cat, torch.full_like(selected_cat, -1)
                )
                event_inputs[env_indices, key_indices] = packed_inputs
                event_u[env_indices, key_indices] = torch.where(
                    derived_mark_mask.unsqueeze(-1), u.detach(), torch.zeros_like(u)
                )
                candidate_u[env_indices, key_indices] = u.detach()
                candidate_z[env_indices, key_indices] = candidate_tanh_u
                # One packed transfer captures every raw mark field at this
                # physical row.  Individual trace records are then assembled
                # from host binary32 arrays before any environment step can
                # consume reward or terminal outcome information.
                trace_payload_values = torch.stack(
                    (packed_z_pre, u.detach(), candidate_tanh_u), dim=1
                ).cpu().numpy()
                event_z_pre[env_indices, key_indices] = packed_z_pre
                event_new_z[env_indices, key_indices] = packed_new_z
                cat_mask[env_indices, key_indices] = derived_cat_mask
                mark_mask[env_indices, key_indices] = derived_mark_mask
                old_cat[env_indices, key_indices] = categorical_logp
                old_mark[env_indices, key_indices] = component_logp
                old_joint[env_indices, key_indices] = joint_logp
                primitive_z[env_indices, key_indices] = packed_new_z
                rng_trace["opportunity"].append({
                    "stream": "opportunity", "operation": "choice_opportunity",
                    "dtype": "int64", "shape": [len(requests)],
                    "coordinates": {
                        "time": int(time), "requests": request_coordinates,
                    },
                })
                request_q[:] = (
                    state.rngs["opportunity"].choice(
                        OPPORTUNITY_SUPPORT, size=len(requests)
                    )
                    if row_rngs is None
                    else _audit_row_draw(
                        row_rngs, requests, "opportunity", dtype=np.int64
                    )
                )

            if deterministic:
                primitive_kwargs: dict[str, Any] = {"deterministic": True}
            else:
                rng_trace["primitive"].append({
                    "stream": "primitive", "operation": "random",
                    "dtype": "float32",
                    "shape": [env_count, MAX_LIFECYCLES],
                    "coordinates": {
                        "time": int(time),
                        "episode_ids": [int(value) for value in cursor.episode_ids],
                        "frontier_orders": [
                            [int(value) for value in row if int(value) >= 0]
                            for row in order_np
                        ],
                    },
                })
                primitive_values = (
                    state.rngs["primitive"].random(
                        (env_count, MAX_LIFECYCLES), dtype=np.float32
                    )
                    if row_rngs is None
                    else np.stack([
                        value["primitive"].random(
                            MAX_LIFECYCLES, dtype=np.float32
                        )
                        for value in row_rngs
                    ])
                )
                uniforms = torch.as_tensor(
                    primitive_values,
                    device=device,
                )
                primitive_kwargs = {"sampling_uniforms": uniforms}
            output = arm.base.forward_step(
                observations=observations,
                active_mask=active,
                order=order,
                hidden=cursor.hidden,
                primitive_logit_bias=arm.primitive_bias(primitive_z),
                prepared=prepared,
                validated=True,
                **primitive_kwargs,
            )
            # The sole device-to-host metadata transfer for this physical row
            # contains both primitive actions and event decisions.
            host_metadata = torch.stack((output.actions, selected_kind_grid), dim=-1).cpu().numpy()
            for index, (env_index, key, request_kind, _inp, _z_pre) in enumerate(requests):
                life = cursor.lifecycles[env_index][key]
                selected_kind = int(host_metadata[env_index, key, 1])
                if request_kind == CREATE and selected_kind != CREATE:
                    raise RuntimeError("CREATE support drift")
                if request_kind != CREATE and selected_kind not in (KEEP, RENEW):
                    raise RuntimeError("opportunity support drift")
                if selected_kind in (KEEP, RENEW):
                    if trace_payload_values is None:
                        raise RuntimeError("eligible event lacks raw trace payload")
                    origin = {
                        "domain": "HMASD_RAW_EVENT_TRACE_V1",
                        "arm": arm.arm,
                        "profile": profile,
                        "replicate": int(state.replicate),
                        "episode_id": int(cursor.episode_ids[env_index]),
                        "ledger_digest": ledger_evidence[env_index]["ledger_digest"],
                    }
                    trace_row = {
                        "coordinate": {
                            "time": int(time),
                            "env_index": int(env_index),
                            "key": int(key),
                            "membership_epoch": int(life.membership_epoch),
                            "segment_id": int(life.segment_id),
                        },
                        "natural_kind": int(selected_kind),
                        "installed_z": _float32_payload(
                            trace_payload_values[index, 0]
                        ),
                        "candidate_u": _float32_payload(
                            trace_payload_values[index, 1]
                        ),
                        "candidate_z": _float32_payload(
                            trace_payload_values[index, 2]
                        ),
                        "origin_binding": origin,
                    }
                    trace_row["origin_binding"] = origin | {
                        "binding_digest": _raw_event_trace_digest(trace_row)
                    }
                    raw_event_trace.append(trace_row)
                if selected_kind != CREATE:
                    life.spell_opportunity_count += 1
                if selected_kind == RENEW:
                    cursor.segments[env_index].append(
                        SegmentRecord(
                            cursor.episode_ids[env_index], key, life.membership_epoch,
                            life.segment_id, life.segment_start_active_step,
                            life.active_steps, False, "RENEW",
                            life.spell_opportunity_count,
                        )
                    )
                    life.segment_id += 1
                    life.segment_start_active_step = life.active_steps
                    life.spell_opportunity_count = 0
                if selected_kind != CREATE:
                    life.non_create_opportunities += 1
                life.z = event_new_z[env_index, key].detach()
                life.q = int(request_q[index])
                epochs[env_index, key] = life.membership_epoch
                segments[env_index, key] = life.segment_id

            reward_np = np.zeros(env_count, dtype=np.float32)
            terminal_np = np.zeros(env_count, dtype=np.bool_)
            for env_index, (env, view) in enumerate(zip(cursor.environments, views)):
                reward, terminal_value, _ = env.step(
                    {key: int(host_metadata[env_index, key, 0]) for key in view.active_keys}
                )
                reward_np[env_index] = reward
                terminal_np[env_index] = terminal_value
                if arm.arm != "OR":
                    for key in view.active_keys:
                        life = cursor.lifecycles[env_index][key]
                        life.active_steps += 1
                        life.q -= 1
                    if terminal_value:
                        for key in tuple(cursor.lifecycles[env_index]):
                            _close_segment(
                                cursor, env_index, key,
                                reason="EPISODE_END", censored=True,
                            )

            values = {
                "observations": observations,
                "active": active,
                "orders": order,
                "actions": output.actions,
                "logp": output.token_log_probs,
                "values": output.value,
                "rewards": torch.as_tensor(reward_np, device=device),
                "terminal": torch.as_tensor(terminal_np, device=device),
                "h_before": h_before,
                "h_after": output.next_hidden,
                "prefix": output.prefix_counts,
                "z": primitive_z,
                "kind": kind,
                "event_input": event_inputs,
                "event_action": event_actions,
                "event_u": event_u,
                "event_z_pre": event_z_pre,
                "event_new_z": event_new_z,
                "candidate_u": candidate_u,
                "candidate_z": candidate_z,
                "cat_mask": cat_mask,
                "mark_mask": mark_mask,
                "old_cat": old_cat,
                "old_mark": old_mark,
                "old_joint": old_joint,
                "epoch": epochs,
                "segment": segments,
                "q": q_before,
            }
            for name, value in values.items():
                rows[name].append(value.detach())
            cursor.hidden = output.next_hidden.detach()

    finished = all(env.time == HORIZON for env in cursor.environments)
    outcomes = tuple(env.outcome() for env in cursor.environments) if finished else ()
    if finished:
        state.next_episode_id = max(cursor.episode_ids) + 1
        state.pending_cursor = None
        bootstrap = torch.zeros(env_count, device=device)
        next_cursor = None
    else:
        state.pending_cursor = cursor
        obs_np = np.zeros((env_count, MAX_LIFECYCLES, OBSERVATION_DIM), dtype=np.float32)
        active_np = np.zeros((env_count, MAX_LIFECYCLES), dtype=np.bool_)
        for env_index, env in enumerate(cursor.environments):
            clone = NoncalendarTrackingEnv.from_snapshot_state(env.snapshot_state())
            view = clone.observe()
            for row_index, key in enumerate(view.active_keys):
                obs_np[env_index, key] = view.observations[row_index]
                active_np[env_index, key] = True
        bootstrap = arm.base.prepare_step(
            observations=torch.as_tensor(obs_np, device=device),
            active_mask=torch.as_tensor(active_np, device=device),
            validated=True,
        ).value.detach()
        next_cursor = cursor
    stacked = {name: torch.stack(rows[name]) for name in names}
    return EventTrajectory(
        observations=stacked["observations"],
        active_mask=stacked["active"],
        orders=stacked["orders"],
        actions=stacked["actions"],
        old_log_probs=stacked["logp"],
        old_values=stacked["values"],
        rewards=stacked["rewards"],
        terminal=stacked["terminal"],
        hidden_before=stacked["h_before"],
        hidden_after=stacked["h_after"],
        prefix_counts=stacked["prefix"],
        primitive_z=stacked["z"],
        event_kind=stacked["kind"],
        event_inputs=stacked["event_input"],
        event_categorical_actions=stacked["event_action"],
        event_u=stacked["event_u"],
        event_z_pre=stacked["event_z_pre"],
        event_new_z=stacked["event_new_z"],
        candidate_u=stacked["candidate_u"],
        candidate_z=stacked["candidate_z"],
        event_cat_mask=stacked["cat_mask"],
        event_mark_mask=stacked["mark_mask"],
        event_old_cat_logp=stacked["old_cat"],
        event_old_mark_component_logp=stacked["old_mark"],
        event_old_joint_logp=stacked["old_joint"],
        membership_epoch=stacked["epoch"],
        segment_id=stacked["segment"],
        q_before=stacked["q"],
        raw_event_trace=tuple(raw_event_trace),
        outcomes=outcomes,
        segments=tuple(tuple(value) for value in cursor.segments),
        ledger_ids=cursor.episode_ids,
        cutoff=not finished,
        bootstrap_values=bootstrap,
        rng_audit={
            "streams": rng_trace,
            "request_evidence": request_evidence,
            "ledgers": list(ledger_evidence),
        },
        cursor=next_cursor,
    )

@dataclass
class ReplayOutput:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    hidden_after: torch.Tensor
    prefix_counts: torch.Tensor
    contexts: torch.Tensor
    event_inputs: torch.Tensor
    event_cat_mask: torch.Tensor
    event_mark_mask: torch.Tensor
    event_actions: torch.Tensor
    event_new_z: torch.Tensor
    event_cat_logp: torch.Tensor
    event_mark_component_logp: torch.Tensor
    event_joint_logp: torch.Tensor
    event_cat_entropy: torch.Tensor


def _replay_primitive(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    hidden = trajectory.hidden_before[0].to(device)
    logps: list[torch.Tensor] = []
    entropies: list[torch.Tensor] = []
    values: list[torch.Tensor] = []
    hidden_rows: list[torch.Tensor] = []
    prefixes: list[torch.Tensor] = []
    contexts: list[torch.Tensor] = []
    for time in range(trajectory.time_steps):
        reset_mask = trajectory.hidden_before[time].to(device).abs().sum(-1).eq(0.0)
        hidden = torch.where(reset_mask.unsqueeze(-1), torch.zeros_like(hidden), hidden)
        observations = trajectory.observations[time].to(device)
        active = trajectory.active_mask[time].to(device)
        prepared = arm.base.prepare_step(
            observations=observations, active_mask=active, validated=True
        )
        output = arm.base.forward_step(
            observations=observations,
            active_mask=active,
            order=trajectory.orders[time].to(device),
            hidden=hidden,
            teacher_actions=trajectory.actions[time].to(device),
            primitive_logit_bias=arm.primitive_bias(trajectory.primitive_z[time].to(device)),
            prepared=prepared,
            validated=True,
        )
        logps.append(output.token_log_probs)
        entropies.append(output.token_entropies)
        values.append(output.value)
        hidden_rows.append(output.next_hidden)
        prefixes.append(output.prefix_counts)
        contexts.append(prepared.context)
        hidden = output.next_hidden
    return (
        torch.stack(logps), torch.stack(entropies), torch.stack(values),
        torch.stack(hidden_rows), torch.stack(prefixes), torch.stack(contexts),
    )


def _replay_event_heads(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
    contexts: torch.Tensor | None,
) -> tuple[
    torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor,
    torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor,
]:
    kind = trajectory.event_kind.to(device)
    cat_mask = kind.eq(KEEP) | kind.eq(RENEW)
    mark_mask = kind.eq(CREATE) | kind.eq(RENEW)
    event_mask = cat_mask | mark_mask
    actions = torch.where(cat_mask, kind - KEEP, torch.full_like(kind, -1))
    if contexts is None:
        reconstructed_inputs = trajectory.event_inputs.to(device)
    else:
        expanded_context = contexts.unsqueeze(2).expand(
            -1, -1, MAX_LIFECYCLES, -1
        )
        reconstructed_inputs = torch.cat(
            (
                trajectory.observations.to(device),
                trajectory.hidden_before.to(device),
                expanded_context,
                trajectory.event_z_pre.to(device),
            ),
            dim=-1,
        ).detach()
    cat_logp = torch.zeros_like(trajectory.event_old_cat_logp, device=device)
    mark_component = torch.zeros_like(
        trajectory.event_old_mark_component_logp, device=device
    )
    cat_entropy = torch.zeros_like(cat_logp)
    if arm.arm != "OR":
        assert arm.event_head is not None and arm.mark_head is not None
        inputs = reconstructed_inputs[event_mask]
        logits, mark_output = _row_stable_event_heads(
            inputs, arm.event_head, arm.mark_head
        )
        log_probability = F.log_softmax(logits, dim=-1)
        probability = torch.exp(log_probability)
        cat_entropy[event_mask] = -(probability * log_probability).sum(-1)
        safe_actions = actions[event_mask].clamp(min=0)
        cat_values = torch.gather(
            log_probability, 1, safe_actions.unsqueeze(-1)
        ).squeeze(-1)
        cat_logp[event_mask] = cat_values
        mu, sigma = _normal_parameters(mark_output)
        u = trajectory.event_u.to(device)[event_mask]
        mark_component[event_mask] = transformed_mark_component_logp(u, mu, sigma)
    cat_logp = torch.where(cat_mask, cat_logp, 0.0)
    mark_component = torch.where(mark_mask.unsqueeze(-1), mark_component, 0.0)
    joint = cat_logp + mark_component.sum(-1)
    u = trajectory.event_u.to(device)
    z_pre = trajectory.event_z_pre.to(device)
    reconstructed_new_z = torch.where(
        mark_mask.unsqueeze(-1),
        torch.tanh(u),
        torch.where(cat_mask.unsqueeze(-1), z_pre, torch.zeros_like(z_pre)),
    ).detach()
    return (
        reconstructed_inputs, cat_mask, mark_mask, actions,
        reconstructed_new_z, cat_logp, mark_component, joint, cat_entropy,
    )


def replay_trajectory(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> ReplayOutput:
    primitive = _replay_primitive(arm, trajectory, device=device)
    events = _replay_event_heads(
        arm, trajectory, device=device, contexts=primitive[5]
    )
    return ReplayOutput(
        log_probs=primitive[0],
        entropies=primitive[1],
        values=primitive[2],
        hidden_after=primitive[3],
        prefix_counts=primitive[4],
        contexts=primitive[5],
        event_inputs=events[0],
        event_cat_mask=events[1],
        event_mark_mask=events[2],
        event_actions=events[3],
        event_new_z=events[4],
        event_cat_logp=events[5],
        event_mark_component_logp=events[6],
        event_joint_logp=events[7],
        event_cat_entropy=events[8],
    )


def _ordered_float32_encoding(value: np.float32) -> int:
    bits = int(value.view(np.uint32))
    return bits ^ (0xFFFFFFFF if bits & 0x80000000 else 0x80000000)


def _float32_ulp_evidence(stored: float, replayed: float) -> tuple[float, int]:
    stored32 = np.float32(stored)
    replayed32 = np.float32(replayed)
    if not np.isfinite(stored32) or not np.isfinite(replayed32):
        return float("nan"), 0
    reference = stored32 if abs(float(stored32)) >= abs(float(replayed32)) else replayed32
    direction = np.float32(np.inf if not np.signbit(reference) else -np.inf)
    neighbor = np.nextafter(reference, direction, dtype=np.float32)
    spacing = abs(float(np.float64(neighbor) - np.float64(reference)))
    distance = abs(
        _ordered_float32_encoding(stored32)
        - _ordered_float32_encoding(replayed32)
    )
    return spacing, int(distance)


def _worst_likelihood_record(
    stored: torch.Tensor,
    replayed: torch.Tensor,
    mask: torch.Tensor,
    *,
    mixed_bound_override: torch.Tensor | None = None,
    ratio_only: bool = False,
) -> dict[str, Any]:
    """Serialize the coordinate that is closest to violating either gate."""

    if not bool(mask.any()):
        return {
            "stored_value": 0.0,
            "replayed_value": 0.0,
            "absolute_error": 0.0,
            "mixed_bound": 0.0,
            "ratio_drift": 0.0,
            "ratio_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
            "float32_ulp_at_max_magnitude": 0.0,
            "ulp_distance": 0,
            "coordinate": None,
        }
    difference = replayed - stored
    absolute_error = difference.double().abs()
    mixed_bound = (
        REPLAY_LOG_COMPONENT_ATOL
        + REPLAY_LOG_COMPONENT_RTOL
        * torch.maximum(replayed.double().abs(), stored.double().abs())
        if mixed_bound_override is None
        else mixed_bound_override.double()
    )
    ratio_drift = torch.expm1(difference.double()).abs()
    severity = (
        ratio_drift / REPLAY_LOG_RATIO_DRIFT_CAP
        if ratio_only
        else torch.maximum(
            absolute_error / mixed_bound,
            ratio_drift / REPLAY_LOG_RATIO_DRIFT_CAP,
        )
    )
    finite = (
        torch.isfinite(stored)
        & torch.isfinite(replayed)
        & torch.isfinite(absolute_error)
        & torch.isfinite(mixed_bound)
        & torch.isfinite(ratio_drift)
    )
    severity = torch.where(
        mask & finite,
        severity,
        torch.where(mask, torch.full_like(severity, float("inf")), torch.full_like(severity, -float("inf"))),
    )
    flat_index = int(torch.argmax(severity.reshape(-1)).detach().cpu())
    coordinate = [int(value) for value in np.unravel_index(flat_index, stored.shape)]
    selected = torch.stack(
        (
            stored.reshape(-1)[flat_index].double(),
            replayed.reshape(-1)[flat_index].double(),
            absolute_error.reshape(-1)[flat_index],
            mixed_bound.reshape(-1)[flat_index],
            ratio_drift.reshape(-1)[flat_index],
        )
    ).detach().cpu().numpy()
    spacing, distance = _float32_ulp_evidence(float(selected[0]), float(selected[1]))
    return {
        "stored_value": float(selected[0]),
        "replayed_value": float(selected[1]),
        "absolute_error": float(selected[2]),
        "mixed_bound": float(selected[3]),
        "ratio_drift": float(selected[4]),
        "ratio_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
        "float32_ulp_at_max_magnitude": spacing,
        "ulp_distance": distance,
        "coordinate": coordinate,
    }


def replay_errors(replay: ReplayOutput, trajectory: EventTrajectory) -> dict[str, float]:
    device = replay.log_probs.device
    active = trajectory.active_mask.to(device)
    stored_cat = trajectory.event_cat_mask.to(device)
    stored_mark = trajectory.event_mark_mask.to(device)
    derived_event = replay.event_cat_mask | replay.event_mark_mask

    def maximum(value: torch.Tensor, mask: torch.Tensor | None = None) -> float:
        selected = value if mask is None else value[mask]
        return float(selected.abs().max().detach().cpu()) if selected.numel() else 0.0

    event_input_mask = derived_event.unsqueeze(-1).expand_as(replay.event_inputs)
    mark_component_mask = replay.event_mark_mask.unsqueeze(-1).expand_as(
        replay.event_mark_component_logp
    )
    # The two component checks above read the stored factors only *inside*
    # their own support, so a factor recorded non-zero outside it is invisible
    # to them; and if the stored joint is reassembled to include that value the
    # assembly check sees a self-consistent sum while the joint bound widens by
    # exactly the corruption. These two quantities look where nothing else
    # does. The collector zeroes both factors outside their support before
    # storing, so on clean data they are exactly zero by construction.
    stored_cat_logp = trajectory.event_old_cat_logp.to(device)
    stored_mark_logp = trajectory.event_old_mark_component_logp.to(device)
    categorical_support_leak = torch.where(
        replay.event_cat_mask, torch.zeros_like(stored_cat_logp), stored_cat_logp
    )
    mark_support_leak = torch.where(
        replay.event_mark_mask.unsqueeze(-1),
        torch.zeros_like(stored_mark_logp),
        stored_mark_logp,
    )
    kind = trajectory.event_kind.to(device)
    kind_support = kind.eq(0) | kind.eq(CREATE) | kind.eq(KEEP) | kind.eq(RENEW)
    action_exact = torch.equal(
        trajectory.event_categorical_actions.to(device)[replay.event_cat_mask],
        replay.event_actions[replay.event_cat_mask],
    )
    detached_exact = (
        not trajectory.event_inputs.requires_grad
        and not trajectory.event_z_pre.requires_grad
        and not trajectory.event_new_z.requires_grad
    )
    return {
        "primitive_component": maximum(
            replay.log_probs - trajectory.old_log_probs.to(device), active
        ),
        "primitive_joint": maximum(
            torch.where(
                active, replay.log_probs - trajectory.old_log_probs.to(device), 0.0
            ).sum(-1)
        ),
        "value": maximum(replay.values - trajectory.old_values.to(device)),
        "hidden": maximum(
            replay.hidden_after - trajectory.hidden_after.to(device)
        ),
        "prefix": maximum(
            replay.prefix_counts - trajectory.prefix_counts.to(device)
        ),
        "event_input": maximum(
            replay.event_inputs - trajectory.event_inputs.to(device), event_input_mask
        ),
        "categorical_component": maximum(
            replay.event_cat_logp - stored_cat_logp, replay.event_cat_mask
        ),
        "mark_component": maximum(
            replay.event_mark_component_logp - stored_mark_logp,
            mark_component_mask,
        ),
        "event_joint": maximum(
            replay.event_joint_logp - trajectory.event_old_joint_logp.to(device),
            derived_event,
        ),
        "event_new_z": maximum(
            replay.event_new_z - trajectory.event_new_z.to(device),
            derived_event.unsqueeze(-1).expand_as(replay.event_new_z),
        ),
        "primitive_event_z": maximum(
            replay.event_new_z - trajectory.primitive_z.to(device),
            derived_event.unsqueeze(-1).expand_as(replay.event_new_z),
        ),
        "mask_mismatch": float(
            not torch.equal(stored_cat, replay.event_cat_mask)
            or not torch.equal(stored_mark, replay.event_mark_mask)
        ),
        "kind_support_mismatch": float(not bool(kind_support.all())),
        "event_action_mismatch": float(not action_exact),
        "detach_mismatch": float(not detached_exact),
        "categorical_support_leak": maximum(categorical_support_leak),
        "mark_support_leak": maximum(mark_support_leak),
    }


def replay_likelihood_records(
    replay: ReplayOutput, trajectory: EventTrajectory
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Worst-coordinate mixed/ratio evidence for every likelihood factor."""

    device = replay.log_probs.device
    active = trajectory.active_mask.to(device)
    categorical_mask = replay.event_cat_mask
    mark_mask = replay.event_mark_mask.unsqueeze(-1).expand_as(
        replay.event_mark_component_logp
    )
    records = {
        "primitive_component": _worst_likelihood_record(
            trajectory.old_log_probs.to(device), replay.log_probs, active
        ),
        "categorical_component": _worst_likelihood_record(
            trajectory.event_old_cat_logp.to(device),
            replay.event_cat_logp,
            categorical_mask,
        ),
        "mark_component": _worst_likelihood_record(
            trajectory.event_old_mark_component_logp.to(device),
            replay.event_mark_component_logp,
            mark_mask,
        ),
    }
    event = _worst_likelihood_record(
        trajectory.event_old_joint_logp.to(device),
        replay.event_joint_logp,
        replay.event_cat_mask | replay.event_mark_mask,
        mixed_bound_override=torch.ones_like(replay.event_joint_logp),
        ratio_only=True,
    )
    event_ratio = {name: event[name] for name in REPLAY_EVENT_JOINT_RATIO_FIELDS}
    return records, event_ratio


def _joint_row_summary(
    *,
    error: torch.Tensor,
    component_sum: torch.Tensor,
    allowance: torch.Tensor,
    factor_count: torch.Tensor,
    assembly_residual: torch.Tensor,
    assembly_allowance: torch.Tensor,
    assembly_excess: torch.Tensor,
    exact_error: torch.Tensor,
    mask: torch.Tensor,
) -> dict[str, float]:
    """Reduce one derived joint's per-row bound check to a reportable record.

    Every argument is a per-row tensor over the same rows; `mask` selects the
    rows on which the joint is defined. The comparison that decides
    acceptance is elementwise per row -- a joint error may only be compared
    against *its own* row's bound, never against the largest bound anywhere
    in the batch -- so `excess` is the per-row maximum of `error - bound` and
    must not exceed zero. The reported `error`/`component_sum`/`allowance`/
    `bound` are all read at the row that produced the largest error, so the
    reported bound is the bound the reported error was actually tested
    against. `excess` is therefore not `error - bound` in general: it is read
    at the row that comes closest to failing, which need not be the
    largest-error row, and it always dominates `error - bound`.

    The three assembly numbers are instead all read at the row *and* side
    that decide `assembly_excess`, so in the record `assembly_excess` is
    exactly `assembly_residual - assembly_allowance`. Reporting a residual
    against an allowance that did not gate it -- for instance the smaller of
    the two sides' magnitudes -- lets a passing record show a residual larger
    than its own allowance, which reads as a contradiction.

    Every reported number is selected on device and transferred once. The
    worst-row index stays a device tensor so that locating it costs no
    synchronization of its own.
    """

    bound = component_sum + allowance
    names = REPLAY_JOINT_RECORD_FIELDS
    if not bool(mask.any()):
        return {name: 0.0 for name in names}
    selected_error = error[mask]
    selected_bound = bound[mask]
    selected_assembly_excess = assembly_excess[mask]
    worst = torch.argmax(selected_error)
    assembly_worst = torch.argmax(selected_assembly_excess)
    values = torch.stack(
        (
            selected_error[worst],
            component_sum[mask][worst],
            allowance[mask][worst],
            selected_bound[worst],
            (selected_error - selected_bound).max(),
            factor_count[mask][worst],
            exact_error[mask].max(),
            assembly_residual[mask][assembly_worst],
            assembly_allowance[mask][assembly_worst],
            selected_assembly_excess[assembly_worst],
            mask.sum().to(selected_error.dtype),
        )
    )
    return dict(zip(names, (float(value) for value in values.detach().cpu())))


def replay_joint_bounds(
    replay: ReplayOutput, trajectory: EventTrajectory
) -> dict[str, dict[str, float]]:
    """Compositional bounds for the two derived joint log probabilities.

    A joint is a sum of float32 factors, so it accumulates its factors'
    replay differences; bounding it by one factor's tolerance is a category
    error. Each joint is instead validated against a float64 recomputation
    from its own recorded factors:

    * `assembly_residual = |joint_f32 - joint_f64|` must not exceed
      `gamma_n * sum|f|` on either side. This is the check that the stored
      and replayed joints really are the sum of their recorded factors --
      an omitted or duplicated factor fails here regardless of tolerance.
    * The stored/replay joint difference then satisfies, by the triangle
      inequality over the float64 assemblies,
      `|J32_replay - J32_stored| <= sum_i|f_replay_i - f_stored_i|
       + gamma_n*(sum|f_stored| + sum|f_replay|)`,
      which is the compositional bound the contract registers. It is
      derived from the per-factor tolerance and conservative float32
      summation, never fitted to an observed number.

    `gamma_n = n*u/(1 - n*u)` with the float32 unit roundoff `u = 2**-24`.
    `n` is 9 for the event joint (categorical plus eight transformed-mark
    components) and the row's active-lifecycle count for the primitive
    joint. Per-factor differences are widened to float64 before summing, so
    the bound itself carries no float32 error of its own.

    What these two records do *not* prove, stated so that nothing here reads
    as coverage it does not provide:

    * `primitive_joint` is unfalsifiable by construction. No primitive joint
      is stored independently, so its error is `|sum(replay - stored)|`
      compared against `sum|replay - stored|` plus slack -- the triangle
      inequality, an identity. `primitive_joint_assembly` compares the
      float32 and float64 reductions of the *same* difference terms against
      a bound orders of magnitude larger, and is likewise invariant to any
      injected corruption. Real primitive coverage is
      the primitive component gates, which are adequate; these two are
      reported for continuity of the record shape, not as gates.
    * `event_joint` gates only joint *assembly* drift. Once the stored and
      replayed assembly checks hold, its rule reduces to the same triangle
      inequality, so a factor-level defect is caught by the component class
      and by `categorical_support_leak`/`mark_support_leak`, never here.
    """

    device = replay.log_probs.device
    active = trajectory.active_mask.to(device)
    stored_logp = trajectory.old_log_probs.to(device)

    # Primitive joint: the reported quantity is the float32 masked sum of
    # per-lifecycle differences, exactly as `replay_errors` computes it.
    primitive_difference = torch.where(
        active, replay.log_probs - stored_logp, 0.0
    ).sum(-1)
    primitive_terms = torch.where(
        active, (replay.log_probs - stored_logp).double(), 0.0
    )
    primitive_exact = primitive_terms.sum(-1)
    primitive_count = active.sum(-1).double()
    primitive_gamma = float32_reduction_gamma(primitive_count)
    primitive_magnitude = (
        torch.where(active, stored_logp.double().abs(), 0.0).sum(-1)
        + torch.where(active, replay.log_probs.double().abs(), 0.0).sum(-1)
    )
    primitive_rows = active.any(-1)

    # Event joint: nine recorded factors per row, each already zeroed
    # outside the row's likelihood support by both the collector and the
    # replay, so masked-out factors contribute nothing to either sum.
    stored_cat = trajectory.event_old_cat_logp.to(device)
    stored_mark = trajectory.event_old_mark_component_logp.to(device)
    stored_joint = trajectory.event_old_joint_logp.to(device)
    stored_factors = torch.cat((stored_cat.unsqueeze(-1), stored_mark), dim=-1)
    replay_factors = torch.cat(
        (replay.event_cat_logp.unsqueeze(-1), replay.event_mark_component_logp),
        dim=-1,
    )
    event_rows = replay.event_cat_mask | replay.event_mark_mask
    event_difference = replay.event_joint_logp - stored_joint
    event_component_sum = (
        (replay_factors.double() - stored_factors.double()).abs().sum(-1)
    )
    event_gamma = float32_reduction_gamma(float(EVENT_JOINT_FACTOR_COUNT))
    stored_magnitude = stored_factors.double().abs().sum(-1)
    replay_magnitude = replay_factors.double().abs().sum(-1)
    stored_exact_joint = stored_factors.double().sum(-1)
    replay_exact_joint = replay_factors.double().sum(-1)
    # Each side is checked against its own factor magnitudes: the stored
    # joint must be the float32 sum of the stored factors, and the replayed
    # joint the float32 sum of the replayed factors. Combining the two sides
    # before comparing would let a large-magnitude side cover a small one.
    stored_assembly = (stored_joint.double() - stored_exact_joint).abs()
    replay_assembly = (replay.event_joint_logp.double() - replay_exact_joint).abs()
    stored_assembly_allowance = event_gamma * stored_magnitude
    replay_assembly_allowance = event_gamma * replay_magnitude
    # The deciding side is the one furthest past its own allowance, and the
    # reported residual/allowance pair is read from that same side. Reporting
    # `max(stored, replay)` residual against `gamma * min(magnitude)` mixes
    # sides and can show a residual above its allowance on a passing record.
    stored_side = stored_assembly - stored_assembly_allowance
    replay_side = replay_assembly - replay_assembly_allowance
    stored_decides = stored_side >= replay_side
    event_assembly = torch.where(stored_decides, stored_assembly, replay_assembly)
    event_assembly_allowance = torch.where(
        stored_decides, stored_assembly_allowance, replay_assembly_allowance
    )
    event_assembly_excess = torch.where(stored_decides, stored_side, replay_side)

    return {
        "primitive_joint": _joint_row_summary(
            error=primitive_difference.double().abs(),
            component_sum=primitive_terms.abs().sum(-1),
            allowance=primitive_gamma * primitive_magnitude,
            factor_count=primitive_count,
            assembly_residual=(primitive_difference.double() - primitive_exact).abs(),
            assembly_allowance=primitive_gamma * primitive_magnitude,
            assembly_excess=(
                (primitive_difference.double() - primitive_exact).abs()
                - primitive_gamma * primitive_magnitude
            ),
            exact_error=primitive_exact.abs(),
            mask=primitive_rows,
        ),
        "event_joint": _joint_row_summary(
            error=event_difference.double().abs(),
            component_sum=event_component_sum,
            allowance=event_gamma * (stored_magnitude + replay_magnitude),
            factor_count=torch.full_like(
                stored_magnitude, float(EVENT_JOINT_FACTOR_COUNT)
            ),
            assembly_residual=event_assembly,
            assembly_allowance=event_assembly_allowance,
            assembly_excess=event_assembly_excess,
            exact_error=(replay_exact_joint - stored_exact_joint).abs(),
            mask=event_rows,
        ),
    }


def replay_report(
    replay: ReplayOutput,
    trajectory: EventTrajectory,
) -> dict[str, Any]:
    """Named per-factor errors, applied joint bounds and a pass result.

    Nothing here is collapsed into a single scalar: an omitted mark
    component and a benign reduction-order difference are different facts
    and must stay separable in the evidence.

    Every acceptance test is written in the `not (x <= limit)` form rather
    than `x > limit`. Both IEEE comparisons against NaN are false, so the
    `>` form would let a replay that produced NaN anywhere report
    `passed: True` -- the exact opposite of the fail-closed contract. Every
    numeric leaf is additionally required to be finite.
    """

    errors = replay_errors(replay, trajectory)
    joints = replay_joint_bounds(replay, trajectory)
    likelihood_components, event_joint_ratio = replay_likelihood_records(
        replay, trajectory
    )
    # The partition is the contract. A factor silently dropped from the
    # error dictionary would otherwise be reported as covered, so an
    # unclassified or missing name is a failure of the check itself.
    if set(errors) != set(
        REPLAY_EXACT_FIELDS + REPLAY_COMPONENT_FIELDS + REPLAY_JOINT_FIELDS
    ):
        raise RuntimeError(f"replay error fields do not match the contract {set(errors)}")
    if any(set(joints[name]) != set(REPLAY_JOINT_RECORD_FIELDS) for name in joints):
        raise RuntimeError(f"replay joint record fields do not match the contract {joints}")
    if (
        set(likelihood_components) != set(REPLAY_LOG_COMPONENT_FIELDS)
        or any(
            set(record) != set(REPLAY_WORST_RECORD_FIELDS)
            for record in likelihood_components.values()
        )
        or set(event_joint_ratio) != set(REPLAY_EVENT_JOINT_RATIO_FIELDS)
    ):
        raise RuntimeError("replay likelihood evidence fields do not match contract")
    failures: list[str] = sorted(
        f"non_finite:{name}"
        for name, value in (
            *errors.items(),
            *(
                (f"{joint}.{key}", number)
                for joint, record in joints.items()
                for key, number in record.items()
            ),
            *(
                (f"{component}.{key}", number)
                for component, record in likelihood_components.items()
                for key, number in record.items()
                if key != "coordinate"
            ),
            *(
                (f"event_joint_ratio.{key}", number)
                for key, number in event_joint_ratio.items()
                if key != "coordinate"
            ),
        )
        if not math.isfinite(float(value))
    )
    failures.extend(name for name in REPLAY_EXACT_FIELDS if errors[name] != 0.0)
    failures.extend(
        name for name in REPLAY_STATE_FIELDS
        if not errors[name] <= REPLAY_STATE_ATOL
    )
    failures.extend(
        name
        for name, record in likelihood_components.items()
        if not (
            float(record["absolute_error"]) <= float(record["mixed_bound"])
            and float(record["ratio_drift"]) <= REPLAY_LOG_RATIO_DRIFT_CAP
        )
    )
    has_event_rows = bool(
        (trajectory.event_kind.eq(CREATE)
         | trajectory.event_kind.eq(KEEP)
         | trajectory.event_kind.eq(RENEW)).any()
    )
    failures.extend(
        f"empty_support:{name}"
        for name, record in likelihood_components.items()
        if record["coordinate"] is None
        and (name == "primitive_component" or has_event_rows)
    )
    failures.extend(
        name for name in REPLAY_JOINT_FIELDS if not joints[name]["excess"] <= 0.0
    )
    failures.extend(
        f"{name}_assembly"
        for name in REPLAY_JOINT_FIELDS
        if not joints[name]["assembly_excess"] <= 0.0
    )
    if not float(event_joint_ratio["ratio_drift"]) <= REPLAY_LOG_RATIO_DRIFT_CAP:
        failures.append("event_joint_ratio")
    return {
        "schema_version": REPLAY_RECORD_SCHEMA_VERSION,
        "errors": errors,
        "likelihood_components": likelihood_components,
        "joints": joints,
        "event_joint_ratio": event_joint_ratio,
        "log_component_atol": REPLAY_LOG_COMPONENT_ATOL,
        "log_component_rtol": REPLAY_LOG_COMPONENT_RTOL,
        "ratio_drift_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
        "state_atol": REPLAY_STATE_ATOL,
        "failures": failures,
        "passed": not failures,
    }


def validate_replay(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> tuple[ReplayOutput, dict[str, Any]]:
    replay = replay_trajectory(arm, trajectory, device=device)
    report = replay_report(replay, trajectory)
    if not report["passed"]:
        errors = report["errors"]
        if any(name in REPLAY_EXACT_FIELDS for name in report["failures"]):
            raise RuntimeError(
                f"semantic replay exact-support mismatch {report['failures']} {errors}"
            )
        raise RuntimeError(
            f"semantic replay tolerance mismatch {report['failures']} "
            f"{errors} {report['joints']}"
        )
    return replay, report


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
