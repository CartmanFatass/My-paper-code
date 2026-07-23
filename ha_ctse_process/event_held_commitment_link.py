"""Frozen OR/DUM/EHC event-held commitment package for noncalendar G0."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field, replace
import binascii
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
    DirectPrimitiveAuditCapture,
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


TYPED_CAUSAL_AUDIT_SCHEMA = "event_held_commitment_link_g0.causal_audit.v2"

CAUSAL_STRUCTURAL_FIELDS = (
    "actions", "active_mask", "orders", "terminal", "event_kind",
    "event_categorical_actions", "event_cat_mask", "event_mark_mask",
    "q_before", "membership_epoch", "segment_id",
)
CAUSAL_FLOAT_FIELDS = (
    "observations", "rewards", "hidden_before", "hidden_after",
    "prefix_counts", "primitive_z", "event_inputs", "event_u",
    "event_z_pre", "event_new_z", "candidate_u", "candidate_z",
)
DERIVED_RECORD_FIELDS = (
    "old_values", "old_log_probs", "event_old_cat_logp",
    "event_old_mark_component_logp", "event_old_joint_logp",
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
    causal_audit_calls: tuple[dict[str, Any], ...]
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

def _native_payload(value: np.ndarray) -> dict[str, Any]:
    """Exact native tensor payload, including signed zero and NaN payload bits."""

    array = np.ascontiguousarray(value)
    encoded = array.tobytes(order="C")
    return {
        "dtype": array.dtype.str,
        "shape": [int(size) for size in array.shape],
        "bytes_b64": base64.b64encode(encoded).decode("ascii"),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _decode_native_payload(value: Mapping[str, Any]) -> np.ndarray:
    if set(value) != {"dtype", "shape", "bytes_b64", "sha256"}:
        raise ValueError("native payload keys mismatch")
    dtype = np.dtype(str(value["dtype"]))
    shape = tuple(int(size) for size in value["shape"])
    encoded = base64.b64decode(str(value["bytes_b64"]), validate=True)
    if hashlib.sha256(encoded).hexdigest() != value["sha256"]:
        raise ValueError("native payload digest mismatch")
    expected = int(np.prod(shape, dtype=np.int64)) * dtype.itemsize
    if len(encoded) != expected:
        raise ValueError("native payload byte count mismatch")
    return np.frombuffer(encoded, dtype=dtype).reshape(shape)


def native_bitwise_finite_comparison(
    left: Mapping[str, Any], right: Mapping[str, Any], *, field: str
) -> dict[str, Any]:
    """Compare exact native bytes and reject every non-finite float leaf."""

    try:
        left_array = _decode_native_payload(left)
        right_array = _decode_native_payload(right)
    except (TypeError, ValueError, KeyError) as exc:
        return {
            "field": field, "passed": False, "malformed": True,
            "finite": False, "dtype_shape_equal": False, "bytes_equal": False,
            "first_coordinate": None, "magnitude": None, "ulp_distance": None,
            "detail": str(exc),
            "source_payload": deepcopy(dict(left)),
            "natural_payload": deepcopy(dict(right)),
        }
    dtype_shape_equal = (
        left_array.dtype == right_array.dtype
        and left_array.shape == right_array.shape
    )
    left_finite = (
        bool(np.isfinite(left_array).all())
        if np.issubdtype(left_array.dtype, np.floating) else True
    )
    right_finite = (
        bool(np.isfinite(right_array).all())
        if np.issubdtype(right_array.dtype, np.floating) else True
    )
    finite = left_finite and right_finite
    bytes_equal = dtype_shape_equal and left["bytes_b64"] == right["bytes_b64"]
    coordinate: list[int] | None = None
    magnitude: float | None = None
    ulp_distance: int | None = None
    if dtype_shape_equal and left_array.size and not finite:
        nonfinite = np.zeros(left_array.shape, dtype=np.bool_)
        if np.issubdtype(left_array.dtype, np.floating):
            nonfinite |= ~np.isfinite(left_array)
            nonfinite |= ~np.isfinite(right_array)
        flat = int(np.flatnonzero(nonfinite.reshape(-1))[0])
        coordinate = [
            int(v) for v in np.unravel_index(flat, left_array.shape)
        ]
    if dtype_shape_equal and left_array.size and not bytes_equal and coordinate is None:
        item_bytes = left_array.dtype.itemsize
        left_items = left_array.reshape(-1).view(np.uint8).reshape(-1, item_bytes)
        right_items = right_array.reshape(-1).view(np.uint8).reshape(-1, item_bytes)
        flat = int(np.flatnonzero(np.any(left_items != right_items, axis=1))[0])
        coordinate = [int(v) for v in np.unravel_index(flat, left_array.shape)]
        if np.issubdtype(left_array.dtype, np.floating):
            left_value = float(left_array.reshape(-1)[flat])
            right_value = float(right_array.reshape(-1)[flat])
            magnitude = abs(left_value - right_value)
            unsigned = np.dtype(f"u{item_bytes}")
            left_bits = int(left_array.reshape(-1)[flat:flat + 1].view(unsigned)[0])
            right_bits = int(right_array.reshape(-1)[flat:flat + 1].view(unsigned)[0])
            sign = 1 << (8 * item_bytes - 1)
            left_ordered = (~left_bits & (2 * sign - 1)) if left_bits & sign else left_bits | sign
            right_ordered = (~right_bits & (2 * sign - 1)) if right_bits & sign else right_bits | sign
            ulp_distance = abs(left_ordered - right_ordered)
    return {
        "field": field,
        "passed": bool(finite and dtype_shape_equal and bytes_equal),
        "malformed": False,
        "finite": bool(finite),
        "dtype_shape_equal": bool(dtype_shape_equal),
        "bytes_equal": bool(bytes_equal),
        "first_coordinate": coordinate,
        "magnitude": magnitude,
        "ulp_distance": ulp_distance,
        "detail": None,
        "source_payload": deepcopy(dict(left)),
        "natural_payload": deepcopy(dict(right)),
    }


def _parameter_payload_digest(payloads: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256(b"HMASD_EXECUTED_KERNEL_PARAMETERS_V2\0")
    for payload in payloads:
        array = _decode_native_payload(payload)
        digest.update(array.dtype.str.encode("ascii"))
        digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _parameter_payload_evidence(arm: CommitmentArm) -> dict[str, Any]:
    modules = {
        "event": (arm.event_head,),
        "mark": (arm.mark_head,),
        "primitive": (arm.base.action_head, arm.W_z),
    }
    families: dict[str, Any] = {}
    for family, family_modules in modules.items():
        payloads = [
            _native_payload(parameter.detach().cpu().contiguous().numpy())
            for module in family_modules
            if module is not None
            for parameter in module.parameters()
        ]
        families[family] = {
            "parameters": payloads,
            "digest": _parameter_payload_digest(payloads),
        }
    return families


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


def _materialize_executed_calls(
    arm: CommitmentArm,
    event_records: list[dict[str, Any]],
    primitive_records: list[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Materialize canonical family-specific records from the executed calls."""

    calls: list[dict[str, Any]] = []
    parameters = _parameter_payload_evidence(arm)

    def append_call(
        *, family: str, call_site: str, call_id: int, packed_width: int,
        row: int, coordinate: dict[str, Any], physical_rows: list[Any],
        input_payload: Any, payload: dict[str, Any],
    ) -> None:
        identity = {
            "sampler_family": family,
            "call_site": call_site,
            "call_id": int(call_id),
            "packed_width": int(packed_width),
            "row": int(row),
            "scientific_coordinate": coordinate,
            "input_digest": _canonical_json_digest(input_payload),
            "parameter_digest": parameters[family]["digest"],
            "payload_digest": _canonical_json_digest(payload),
        }
        calls.append({
            "identity": identity,
            "input": input_payload,
            "payload": payload,
            "physical_rows": physical_rows,
            "identity_digest": _canonical_json_digest(identity),
        })

    for record in event_records:
        names = (
            "inputs", "logits", "probabilities", "cdf", "converted_uniform",
            "mu", "sigma", "noise", "u", "tanh_u", "candidate_mark", "z_pre",
        )
        host = {
            name: record[name].detach().cpu().contiguous().numpy()
            for name in names
        }
        actions = torch.stack(
            (record["pre_force_action"], record["final_action"]), dim=-1
        ).detach().cpu().contiguous().numpy()
        for request_row, raw_coordinate in enumerate(record["request_coordinates"]):
            env_index, key, request_kind = (int(value) for value in raw_coordinate)
            coordinate = {
                "time": int(record["time"]),
                "episode_id": int(record["episode_ids"][env_index]),
                "environment_row": env_index,
                "lifecycle_key": key,
                "membership_epoch": int(record["membership_epoch"][request_row]),
                "segment_id": int(record["segment_id"][request_row]),
                "request_kind": request_kind,
            }
            input_payload = _native_payload(host["inputs"][request_row])
            if request_kind != CREATE:
                append_call(
                    family="event",
                    call_site="collect_trajectory.event_categorical",
                    call_id=int(record["event_call_id"]),
                    packed_width=int(record["packed_width"]),
                    row=request_row,
                    coordinate=deepcopy(coordinate),
                    physical_rows=deepcopy(record["request_coordinates"]),
                    input_payload=deepcopy(input_payload),
                    payload={
                        "logits": _native_payload(host["logits"][request_row]),
                        "probabilities": _native_payload(
                            host["probabilities"][request_row]
                        ),
                        "cdf": _native_payload(host["cdf"][request_row]),
                        "converted_uniform": _native_payload(
                            host["converted_uniform"][request_row:request_row + 1]
                        ),
                        "pre_force_action": int(actions[request_row, 0]),
                        "final_action": int(actions[request_row, 1]),
                    },
                )
            append_call(
                family="mark",
                call_site="collect_trajectory.candidate_mark",
                call_id=int(record["mark_call_id"]),
                packed_width=int(record["packed_width"]),
                row=request_row,
                coordinate=deepcopy(coordinate),
                physical_rows=deepcopy(record["request_coordinates"]),
                input_payload=deepcopy(input_payload),
                payload={
                    "mu": _native_payload(host["mu"][request_row]),
                    "sigma": _native_payload(host["sigma"][request_row]),
                    "noise": _native_payload(host["noise"][request_row]),
                    "u": _native_payload(host["u"][request_row]),
                    "tanh_u": _native_payload(host["tanh_u"][request_row]),
                    "candidate_mark": _native_payload(
                        host["candidate_mark"][request_row]
                    ),
                    "installed_z_pre": _native_payload(host["z_pre"][request_row]),
                },
            )

    for record in primitive_records:
        context = record["call_identity"]
        rows = record["row"].detach().cpu().contiguous().numpy()
        focal_keys = record["focal_key"].detach().cpu().contiguous().numpy()
        epochs = context["membership_epoch"].detach().cpu().numpy()
        segments = context["segment_id"].detach().cpu().numpy()
        host = {
            name: record[name].detach().cpu().contiguous().numpy()
            for name in (
                "action_input", "logits", "probabilities", "cdf",
                "converted_uniform", "selected_action",
            )
        }
        bias = (
            None if record["primitive_bias"] is None
            else record["primitive_bias"].detach().cpu().contiguous().numpy()
        )
        for index, (raw_row, raw_key) in enumerate(
            zip(rows, focal_keys, strict=True)
        ):
            env_row, key = int(raw_row), int(raw_key)
            input_payload = {
                "action_input": _native_payload(host["action_input"][index]),
                "primitive_bias": (
                    None if bias is None else _native_payload(bias[index])
                ),
            }
            append_call(
                family="primitive",
                call_site=str(context["call_site"]),
                call_id=int(context["call_id"]),
                packed_width=int(record["packed_width"]),
                row=env_row,
                coordinate={
                    "time": int(context["time"]),
                    "episode_id": int(context["episode_ids"][env_row]),
                    "environment_row": env_row,
                    "lifecycle_key": key,
                    "membership_epoch": int(epochs[env_row, key]),
                    "segment_id": int(segments[env_row, key]),
                    "autoregressive_position": int(
                        record["autoregressive_position"]
                    ),
                },
                physical_rows=list(range(int(record["packed_width"]))),
                input_payload=input_payload,
                payload={
                    "logits": _native_payload(host["logits"][index]),
                    "probabilities": _native_payload(host["probabilities"][index]),
                    "cdf": _native_payload(host["cdf"][index]),
                    "converted_uniform": _native_payload(
                        host["converted_uniform"][index:index + 1]
                    ),
                    "selected_action": int(host["selected_action"][index]),
                },
            )
    calls.sort(key=lambda call: (
        int(call["identity"]["call_id"]),
        int(call["identity"]["row"]),
        str(call["identity"]["sampler_family"]),
    ))
    return tuple(calls)


def _raw_trace_from_executed_calls(
    calls: tuple[dict[str, Any], ...],
    *,
    arm: CommitmentArm,
    profile: str,
    replicate: int,
    ledger_evidence: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    marks = {
        _decision_coordinate_key(call): call
        for call in calls
        if call["identity"]["sampler_family"] == "mark"
    }
    for call in calls:
        identity = call["identity"]
        if identity["sampler_family"] != "event":
            continue
        final_action = int(call["payload"]["final_action"])
        if final_action not in (KEEP, RENEW):
            continue
        scientific = identity["scientific_coordinate"]
        env_index = int(scientific["environment_row"])
        mark = marks[_decision_coordinate_key(call)]
        origin = {
            "domain": "HMASD_RAW_EVENT_TRACE_V1",
            "arm": arm.arm,
            "profile": profile,
            "replicate": int(replicate),
            "episode_id": int(scientific["episode_id"]),
            "ledger_digest": ledger_evidence[env_index]["ledger_digest"],
        }
        trace_row = {
            "coordinate": {
                "time": int(scientific["time"]),
                "env_index": env_index,
                "key": int(scientific["lifecycle_key"]),
                "membership_epoch": int(scientific["membership_epoch"]),
                "segment_id": int(scientific["segment_id"]),
            },
            "natural_kind": final_action,
            "installed_z": _float32_payload(
                _decode_native_payload(mark["payload"]["installed_z_pre"])
            ),
            "candidate_u": _float32_payload(
                _decode_native_payload(mark["payload"]["u"])
            ),
            "candidate_z": _float32_payload(
                _decode_native_payload(mark["payload"]["candidate_mark"])
            ),
            "origin_binding": origin,
        }
        trace_row["origin_binding"] = origin | {
            "binding_digest": _raw_event_trace_digest(trace_row)
        }
        rows.append(trace_row)
    return tuple(rows)


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
    causal_audit_evidence: bool = False,
) -> EventTrajectory:
    if state.arm != arm.arm or set(state.rngs) != set(RNG_NAMES):
        raise ValueError("collector arm or owned-RNG key set mismatch")
    if causal_audit_evidence and deterministic:
        raise ValueError("causal audit evidence requires executed stochastic samplers")
    audit_event_records: list[dict[str, Any]] | None = (
        [] if causal_audit_evidence else None
    )
    primitive_audit_records: list[dict[str, Any]] | None = (
        [] if causal_audit_evidence else None
    )
    causal_call_id = 0
    rng_trace: dict[str, list[dict[str, Any]]] = {
        name: [] for name in RNG_NAMES
    }
    request_evidence: list[dict[str, Any]] = []
    raw_event_trace: tuple[dict[str, Any], ...] = ()
    causal_audit_calls: tuple[dict[str, Any], ...] = ()
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
            event_call_id: int | None = None
            mark_call_id: int | None = None
            if requests:
                event_call_id = causal_call_id
                mark_call_id = causal_call_id + 1
                causal_call_id += 2
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
                    event_uniforms = torch.zeros(
                        len(requests), dtype=logits.dtype, device=device
                    )
                    mark_eps = torch.zeros_like(mu)
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
                    event_probability = torch.softmax(logits, -1)
                    event_cdf = torch.cumsum(event_probability, -1)
                    selected_cat = torch.sum(
                        event_uniforms.unsqueeze(-1) > event_cdf,
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
                if audit_event_records is not None:
                    pre_force_selected_cat = selected_cat
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
                if audit_event_records is not None:
                    assert event_call_id is not None and mark_call_id is not None
                    audit_event_records.append({
                        "event_call_id": int(event_call_id),
                        "mark_call_id": int(mark_call_id),
                        "time": int(time),
                        "packed_width": len(requests),
                        "request_coordinates": deepcopy(request_coordinates),
                        "episode_ids": tuple(int(v) for v in cursor.episode_ids),
                        "membership_epoch": tuple(
                            int(cursor.lifecycles[env][key].membership_epoch)
                            for env, key, _kind, _inp, _z in requests
                        ),
                        "segment_id": tuple(
                            int(cursor.lifecycles[env][key].segment_id)
                            for env, key, _kind, _inp, _z in requests
                        ),
                        "inputs": packed_inputs.detach(),
                        "logits": logits.detach(),
                        "probabilities": event_probability.detach(),
                        "cdf": event_cdf.detach(),
                        "converted_uniform": event_uniforms.detach(),
                        "pre_force_action": pre_force_selected_cat.detach(),
                        "final_action": selected_kind.detach(),
                        "mu": mu.detach(),
                        "sigma": sigma.detach(),
                        "noise": mark_eps.detach(),
                        "u": u.detach(),
                        "tanh_u": candidate_tanh_u.detach(),
                        "candidate_mark": candidate_tanh_u.detach(),
                        "z_pre": packed_z_pre.detach(),
                    })
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
            primitive_bias = arm.primitive_bias(primitive_z)
            primitive_capture: DirectPrimitiveAuditCapture | None = None
            if primitive_audit_records is not None:
                primitive_capture = DirectPrimitiveAuditCapture(
                    call_identity={
                        "call_site": "collect_trajectory.primitive",
                        "call_id": int(causal_call_id),
                        "time": int(time),
                        "episode_ids": tuple(int(v) for v in cursor.episode_ids),
                        "membership_epoch": epochs.detach(),
                        "segment_id": segments.detach(),
                    },
                    records=primitive_audit_records,
                )
                causal_call_id += 1
            output = arm.base.forward_step(
                observations=observations,
                active_mask=active,
                order=order,
                hidden=cursor.hidden,
                primitive_logit_bias=primitive_bias,
                prepared=prepared,
                audit_capture=primitive_capture,
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
    if audit_event_records is not None and primitive_audit_records is not None:
        causal_audit_calls = _materialize_executed_calls(
            arm, audit_event_records, primitive_audit_records
        )
        raw_event_trace = _raw_trace_from_executed_calls(
            causal_audit_calls,
            arm=arm,
            profile=profile,
            replicate=int(state.replicate),
            ledger_evidence=ledger_evidence,
        )
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
        causal_audit_calls=causal_audit_calls,
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
    required_support = {
        "primitive_component": True,
        "categorical_component": bool(trajectory.event_cat_mask.any()),
        "mark_component": bool(trajectory.event_mark_mask.any()),
    }
    failures.extend(
        f"empty_support:{name}"
        for name, record in likelihood_components.items()
        if record["coordinate"] is None and required_support[name]
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


def _isolate_audit_cursor(
    cursor: CollectionCursor, env_index: int
) -> CollectionCursor:
    return CollectionCursor(
        episode_ids=(int(cursor.episode_ids[env_index]),),
        ledgers=(deepcopy(cursor.ledgers[env_index]),),
        environments=[NoncalendarTrackingEnv.from_snapshot_state(
            cursor.environments[env_index].snapshot_state()
        )],
        hidden=cursor.hidden[env_index:env_index + 1].detach().clone(),
        lifecycles=[deepcopy(cursor.lifecycles[env_index])],
        segments=[deepcopy(cursor.segments[env_index])],
    )


def _combine_audit_cursors(cursors: list[CollectionCursor]) -> CollectionCursor:
    if not cursors or any(len(cursor.environments) != 1 for cursor in cursors):
        raise ValueError("batched fork cursors must each own one environment")
    times = {cursor.environments[0].time for cursor in cursors}
    if len(times) != 1:
        raise ValueError("batched fork cursor group must share physical time")
    return CollectionCursor(
        episode_ids=tuple(cursor.episode_ids[0] for cursor in cursors),
        ledgers=tuple(deepcopy(cursor.ledgers[0]) for cursor in cursors),
        environments=[NoncalendarTrackingEnv.from_snapshot_state(
            cursor.environments[0].snapshot_state()
        ) for cursor in cursors],
        hidden=torch.cat([cursor.hidden for cursor in cursors], dim=0),
        lifecycles=[deepcopy(cursor.lifecycles[0]) for cursor in cursors],
        segments=[deepcopy(cursor.segments[0]) for cursor in cursors],
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


def _tensor_payload(value: torch.Tensor) -> dict[str, Any]:
    return _native_payload(value.detach().cpu().contiguous().numpy())


def _call_coordinate_key(call: Mapping[str, Any]) -> tuple[Any, ...]:
    identity = call["identity"]
    coordinate = identity["scientific_coordinate"]
    family = str(identity["sampler_family"])
    base = (
        family,
        int(coordinate["time"]),
        int(coordinate["episode_id"]),
        int(coordinate["lifecycle_key"]),
        int(coordinate["membership_epoch"]),
        int(coordinate["segment_id"]),
    )
    if family in ("event", "mark"):
        return base + (int(coordinate["request_kind"]),)
    if family == "primitive":
        return base + (int(coordinate["autoregressive_position"]),)
    raise ValueError("unknown sampler family")


def _decision_coordinate_key(call: Mapping[str, Any]) -> tuple[int, ...]:
    coordinate = call["identity"]["scientific_coordinate"]
    return (
        int(coordinate["time"]),
        int(coordinate["episode_id"]),
        int(coordinate["lifecycle_key"]),
        int(coordinate["membership_epoch"]),
        int(coordinate["segment_id"]),
        int(coordinate["request_kind"]),
    )


def _selected_executed_calls(
    trajectory: EventTrajectory, *, row: int, start: int,
) -> list[dict[str, Any]]:
    return [
        call for call in trajectory.causal_audit_calls
        if int(
            call["identity"]["scientific_coordinate"]["environment_row"]
        ) == int(row)
        and int(call["identity"]["scientific_coordinate"]["time"]) >= int(start)
    ]


def _comparison_failure(
    comparisons: Iterable[Mapping[str, Any]], *, evidence_class: str
) -> dict[str, Any] | None:
    for comparison in comparisons:
        if not bool(comparison.get("passed")):
            return {
                "class": evidence_class,
                "field": comparison.get("field"),
                "coordinate": comparison.get("first_coordinate"),
                "magnitude": comparison.get("magnitude"),
                "ulp_distance": comparison.get("ulp_distance"),
                "detail": comparison.get("detail"),
            }
    return None


_REPLAY_RECORD_KEYS = frozenset({
    "schema_version", "errors", "likelihood_components", "joints",
    "event_joint_ratio", "log_component_atol", "log_component_rtol",
    "ratio_drift_cap", "state_atol", "failures", "passed",
})
_RECORD_CONSISTENCY_RELATIVE = 1e-9
_RECORD_CONSISTENCY_ABSOLUTE = 1e-15


def _finite_numeric_leaves(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_numeric_leaves(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_numeric_leaves(item) for item in value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return math.isfinite(float(value))
    return True


def _record_consistent(left: float, right: float) -> bool:
    return abs(left - right) <= (
        _RECORD_CONSISTENCY_ABSOLUTE
        + _RECORD_CONSISTENCY_RELATIVE * max(abs(left), abs(right))
    )


def _replay_joint_factor_error_cap(
    name: str, errors: Mapping[str, Any], joint: Mapping[str, float],
) -> float:
    if name == "event_joint":
        return float(errors["categorical_component"]) + float(
            EVENT_JOINT_FACTOR_COUNT - 1
        ) * float(errors["mark_component"])
    return float(joint["factor_count"]) * float(errors["primitive_component"])


def _serialized_likelihood_record_valid(
    record: Any, *, dimensions: int, empty_allowed: bool,
) -> bool:
    if not isinstance(record, Mapping) or set(record) != set(REPLAY_WORST_RECORD_FIELDS):
        return False
    coordinate = record["coordinate"]
    if coordinate is None:
        return bool(
            empty_allowed
            and all(
                float(record[name]) == 0.0
                for name in (
                    "stored_value", "replayed_value", "absolute_error",
                    "mixed_bound", "ratio_drift",
                    "float32_ulp_at_max_magnitude", "ulp_distance",
                )
            )
            and float(record["ratio_cap"]) == REPLAY_LOG_RATIO_DRIFT_CAP
        )
    if not (
        isinstance(coordinate, list)
        and len(coordinate) == dimensions
        and all(type(index) is int and index >= 0 for index in coordinate)
    ):
        return False
    stored = float(record["stored_value"])
    replayed = float(record["replayed_value"])
    absolute_error = abs(replayed - stored)
    mixed_bound = REPLAY_LOG_COMPONENT_ATOL + REPLAY_LOG_COMPONENT_RTOL * max(
        abs(stored), abs(replayed)
    )
    ratio_drift = abs(math.expm1(replayed - stored))
    spacing, distance = _float32_ulp_evidence(stored, replayed)
    return bool(
        _record_consistent(float(record["absolute_error"]), absolute_error)
        and _record_consistent(float(record["mixed_bound"]), mixed_bound)
        and _record_consistent(float(record["ratio_drift"]), ratio_drift)
        and float(record["ratio_cap"]) == REPLAY_LOG_RATIO_DRIFT_CAP
        and float(record["float32_ulp_at_max_magnitude"]) == spacing
        and int(record["ulp_distance"]) == distance
        and absolute_error <= mixed_bound
        and ratio_drift <= REPLAY_LOG_RATIO_DRIFT_CAP
    )


def validate_serialized_replay_report(
    report: Any, *, event_rows_required: bool = True,
    categorical_rows_required: bool | None = None,
    mark_rows_required: bool | None = None,
) -> bool:
    """Authoritative fail-closed validator for serialized replay evidence."""
    categorical_required = (
        event_rows_required
        if categorical_rows_required is None else categorical_rows_required
    )
    mark_required = (
        event_rows_required if mark_rows_required is None else mark_rows_required
    )

    if not isinstance(report, Mapping) or set(report) != _REPLAY_RECORD_KEYS:
        return False
    errors = report.get("errors")
    components = report.get("likelihood_components")
    joints = report.get("joints")
    ratio = report.get("event_joint_ratio")
    if not (
        isinstance(errors, Mapping)
        and set(errors)
        == set(REPLAY_EXACT_FIELDS + REPLAY_COMPONENT_FIELDS + REPLAY_JOINT_FIELDS)
        and isinstance(components, Mapping)
        and set(components) == set(REPLAY_LOG_COMPONENT_FIELDS)
        and isinstance(joints, Mapping)
        and set(joints) == set(REPLAY_JOINT_FIELDS)
        and all(
            isinstance(joints[name], Mapping)
            and set(joints[name]) == set(REPLAY_JOINT_RECORD_FIELDS)
            for name in REPLAY_JOINT_FIELDS
        )
        and isinstance(ratio, Mapping)
        and set(ratio) == set(REPLAY_EVENT_JOINT_RATIO_FIELDS)
        and _finite_numeric_leaves(report)
    ):
        return False
    if (
        report["schema_version"] != REPLAY_RECORD_SCHEMA_VERSION
        or float(report["log_component_atol"]) != REPLAY_LOG_COMPONENT_ATOL
        or float(report["log_component_rtol"]) != REPLAY_LOG_COMPONENT_RTOL
        or float(report["ratio_drift_cap"]) != REPLAY_LOG_RATIO_DRIFT_CAP
        or float(report["state_atol"]) != REPLAY_STATE_ATOL
        or report["passed"] is not True
        or report["failures"] != []
        or any(float(errors[name]) != 0.0 for name in REPLAY_EXACT_FIELDS)
        or any(float(errors[name]) > REPLAY_STATE_ATOL for name in REPLAY_STATE_FIELDS)
    ):
        return False
    if not _serialized_likelihood_record_valid(
        components["primitive_component"], dimensions=3, empty_allowed=False,
    ):
        return False
    for name, dimensions, required in (
        ("categorical_component", 3, categorical_required),
        ("mark_component", 4, mark_required),
    ):
        if not _serialized_likelihood_record_valid(
            components[name], dimensions=dimensions,
            empty_allowed=not required,
        ):
            return False
    coordinate = ratio["coordinate"]
    if coordinate is None:
        if (
            event_rows_required
            or any(
                float(ratio[name]) != 0.0
                for name in ("stored_value", "replayed_value", "ratio_drift")
            )
            or float(ratio["ratio_cap"]) != REPLAY_LOG_RATIO_DRIFT_CAP
        ):
            return False
    elif not (
        isinstance(coordinate, list)
        and len(coordinate) == 3
        and all(type(index) is int and index >= 0 for index in coordinate)
    ):
        return False
    else:
        recomputed_ratio = abs(math.expm1(
            float(ratio["replayed_value"]) - float(ratio["stored_value"])
        ))
        if not (
            _record_consistent(float(ratio["ratio_drift"]), recomputed_ratio)
            and float(ratio["ratio_cap"]) == REPLAY_LOG_RATIO_DRIFT_CAP
            and recomputed_ratio <= REPLAY_LOG_RATIO_DRIFT_CAP
        ):
            return False
    for name in REPLAY_JOINT_FIELDS:
        joint = {key: float(value) for key, value in joints[name].items()}
        if any(
            joint[key] < 0.0
            for key in (
                "error", "component_sum", "allowance", "bound", "factor_count",
                "float64_error", "assembly_residual", "assembly_allowance", "rows",
            )
        ):
            return False
        if (
            joint["excess"] > 0.0
            or joint["assembly_excess"] > 0.0
            or float(errors[name]) > joint["bound"]
            or not _record_consistent(
                joint["bound"], joint["component_sum"] + joint["allowance"]
            )
            or joint["excess"] < joint["error"] - joint["bound"] - (
                _RECORD_CONSISTENCY_ABSOLUTE
                + _RECORD_CONSISTENCY_RELATIVE * abs(joint["bound"])
            )
            or not _record_consistent(
                joint["assembly_excess"],
                joint["assembly_residual"] - joint["assembly_allowance"],
            )
        ):
            return False
        cap = _replay_joint_factor_error_cap(name, errors, joint)
        if joint["component_sum"] > cap + (
            _RECORD_CONSISTENCY_ABSOLUTE
            + _RECORD_CONSISTENCY_RELATIVE * abs(cap)
        ):
            return False
        if joint["rows"] <= 0.0:
            if (
                name != "event_joint"
                or event_rows_required
                or any(value != 0.0 for value in joint.values())
            ):
                return False
        elif (
            name == "event_joint"
            and joint["factor_count"] != float(EVENT_JOINT_FACTOR_COUNT)
        ):
            return False
    return True

def _validate_replay_report_evidence(
    report: Mapping[str, Any], *, event_rows_required: bool = True,
    categorical_rows_required: bool | None = None,
    mark_rows_required: bool | None = None,
) -> tuple[bool, bool, bool]:
    valid = validate_serialized_replay_report(
        report,
        event_rows_required=event_rows_required,
        categorical_rows_required=categorical_rows_required,
        mark_rows_required=mark_rows_required,
    )
    return valid, valid, valid


def _trajectory_environment_slice(
    trajectory: EventTrajectory, env_index: int
) -> EventTrajectory:
    """Isolate one replay row so counterfactual packed neighbors cannot gate it."""

    tensor_replacements: dict[str, torch.Tensor] = {}
    env_count = len(trajectory.ledger_ids)
    for name in trajectory.__dataclass_fields__:
        value = getattr(trajectory, name)
        if not isinstance(value, torch.Tensor):
            continue
        if name == "bootstrap_values":
            tensor_replacements[name] = value[env_index:env_index + 1]
        elif value.ndim >= 2 and int(value.shape[1]) == env_count:
            tensor_replacements[name] = value[:, env_index:env_index + 1]
    return replace(
        trajectory,
        **tensor_replacements,
        raw_event_trace=(),
        causal_audit_calls=(),
        outcomes=(trajectory.outcomes[env_index],),
        segments=(trajectory.segments[env_index],),
        ledger_ids=(trajectory.ledger_ids[env_index],),
        cursor=None,
    )


def _derived_reference_trajectory(
    branch: EventTrajectory,
    branch_index: int,
    original: EventTrajectory,
    original_env: int,
    *,
    start: int,
) -> EventTrajectory:
    replacements: dict[str, torch.Tensor] = {}
    for name in DERIVED_RECORD_FIELDS:
        target = getattr(branch, name).clone()
        target[:, branch_index] = getattr(original, name)[
            start:, original_env
        ].to(target.device)
        replacements[name] = target
    return replace(branch, **replacements)


_CALL_KEYS = frozenset({
    "identity", "physical_rows", "input", "payload", "identity_digest",
})
_CALL_IDENTITY_KEYS = frozenset({
    "sampler_family", "call_site", "call_id", "packed_width", "row",
    "scientific_coordinate", "input_digest", "parameter_digest",
    "payload_digest",
})
_CALL_PAYLOAD_KEYS = {
    "event": frozenset({
        "logits", "probabilities", "cdf", "converted_uniform",
        "pre_force_action", "final_action",
    }),
    "mark": frozenset({
        "mu", "sigma", "noise", "u", "tanh_u", "candidate_mark",
        "installed_z_pre",
    }),
    "primitive": frozenset({
        "logits", "probabilities", "cdf", "converted_uniform",
        "selected_action",
    }),
}
_CALL_SITES = {
    "event": "collect_trajectory.event_categorical",
    "mark": "collect_trajectory.candidate_mark",
    "primitive": "collect_trajectory.primitive",
}


def _native_payload_tree_valid(value: Any) -> bool:
    if isinstance(value, Mapping):
        if set(value) == {"dtype", "shape", "bytes_b64", "sha256"}:
            try:
                _decode_native_payload(value)
            except (KeyError, TypeError, ValueError):
                return False
            return True
        return all(_native_payload_tree_valid(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_native_payload_tree_valid(item) for item in value)
    return isinstance(value, (str, int, float, bool, type(None)))


def _parameter_evidence_valid(parameters: Any) -> bool:
    if not isinstance(parameters, Mapping) or set(parameters) != {
        "event", "mark", "primitive",
    }:
        return False
    for family in ("event", "mark", "primitive"):
        record = parameters[family]
        if (
            not isinstance(record, Mapping)
            or set(record) != {"parameters", "digest"}
            or not isinstance(record["parameters"], list)
            or not all(_native_payload_tree_valid(row) for row in record["parameters"])
        ):
            return False
        try:
            digest = _parameter_payload_digest(record["parameters"])
        except (KeyError, TypeError, ValueError):
            return False
        if record["digest"] != digest:
            return False
    return True


def _canonical_call_valid(
    call: Any, *, parameter_evidence: Mapping[str, Any],
) -> bool:
    if not isinstance(call, Mapping) or set(call) != _CALL_KEYS:
        return False
    identity = call["identity"]
    if not isinstance(identity, Mapping) or set(identity) != _CALL_IDENTITY_KEYS:
        return False
    family = identity["sampler_family"]
    coordinate = identity["scientific_coordinate"]
    if family not in _CALL_PAYLOAD_KEYS or not isinstance(coordinate, Mapping):
        return False
    coordinate_keys = {
        "time", "episode_id", "environment_row", "lifecycle_key",
        "membership_epoch", "segment_id",
        "autoregressive_position" if family == "primitive" else "request_kind",
    }
    payload = call["payload"]
    physical_rows = call["physical_rows"]
    if (
        set(coordinate) != coordinate_keys
        or not isinstance(physical_rows, list)
        or len(physical_rows) != int(identity["packed_width"])
        or not isinstance(payload, Mapping)
        or set(payload) != _CALL_PAYLOAD_KEYS[family]
        or identity["call_site"] != _CALL_SITES[family]
        or type(identity["call_id"]) is not int
        or int(identity["call_id"]) < 0
        or type(identity["packed_width"]) is not int
        or int(identity["packed_width"]) <= 0
        or type(identity["row"]) is not int
        or not 0 <= int(identity["row"]) < int(identity["packed_width"])
        or not _native_payload_tree_valid(call["input"])
        or not _native_payload_tree_valid(payload)
        or identity["input_digest"] != _canonical_json_digest(call["input"])
        or identity["payload_digest"] != _canonical_json_digest(payload)
        or identity["parameter_digest"]
        != parameter_evidence[family]["digest"]
        or call["identity_digest"] != _canonical_json_digest(identity)
    ):
        return False
    if family == "primitive":
        return bool(
            int(identity["packed_width"]) == FORMAL_NUM_ENVS
            and physical_rows == list(range(FORMAL_NUM_ENVS))
            and int(physical_rows[int(identity["row"])])
            == int(coordinate["environment_row"])
        )
    request_kind = int(coordinate["request_kind"])
    try:
        physical_coordinate = [
            int(value) for value in physical_rows[int(identity["row"])]
        ]
    except (TypeError, ValueError):
        return False
    return bool(
        request_kind in (CREATE, KEEP)
        and physical_coordinate == [
            int(coordinate["environment_row"]),
            int(coordinate["lifecycle_key"]),
            request_kind,
        ]
        and (family != "event" or request_kind != CREATE)
    )


def _paired_comparison(
    source: Mapping[str, Any], natural: Mapping[str, Any], *,
    field: str, pair_coordinate: list[Any],
) -> dict[str, Any]:
    return native_bitwise_finite_comparison(
        source, natural, field=field,
    ) | {"pair_coordinate": deepcopy(pair_coordinate)}


def _call_input_comparisons(
    source: Mapping[str, Any], natural: Mapping[str, Any], *,
    family: str, pair_coordinate: list[Any],
) -> list[dict[str, Any]]:
    if family != "primitive":
        return [_paired_comparison(
            source, natural, field=f"{family}.input",
            pair_coordinate=pair_coordinate,
        )]
    names = ("action_input", "primitive_bias")
    if any(source[name] is None or natural[name] is None for name in names):
        raise ValueError("primitive typed input requires action input and bias")
    return [
        _paired_comparison(
            source[name], natural[name],
            field=f"primitive.input.{name}",
            pair_coordinate=pair_coordinate,
        )
        for name in names
    ]


def _runtime_provenance() -> dict[str, Any]:
    execution = registered_contract()["execution"]
    return {
        "registered_backend": execution["backend"],
        "torch_version": str(torch.__version__),
        "thread_count": int(torch.get_num_threads()),
        "contract_version": TYPED_CAUSAL_AUDIT_SCHEMA,
    }


def _typed_rng_provenance(
    material: Mapping[str, Mapping[str, Any]],
    streams: Mapping[str, _AuditRowStream],
    *, replicate: int, source_environment: int,
) -> dict[str, Any]:
    seeds = authoritative_seed_map("held_out", replicate)
    records: dict[str, Any] = {}
    for name in RNG_NAMES:
        stream = streams.get(name)
        consumed = (
            np.empty(0, dtype=np.uint8)
            if stream is None
            else np.ascontiguousarray(
                stream.values.reshape(-1)[:stream.position]
            )
        )
        payload = _native_payload(consumed)
        records[name] = {
            "seed": int(seeds[name]),
            "start_state": deepcopy(material[name]["start_state"]),
            "schedule": deepcopy(material[name]["draw_schedule"]),
            "consumption_position": 0 if stream is None else int(stream.position),
            "consumed_payload": payload,
            "consumed_payload_digest": payload["sha256"],
            "end_state": deepcopy(material[name]["end_state"]),
        }
    evidence = {
        "source_environment": int(source_environment),
        "streams": records,
        "realized_variates_exact": True,
        "passed": True,
    }
    return evidence


def _expected_row_consumption(
    *, stream: str, arrays: list[np.ndarray],
    schedule: list[Mapping[str, Any]], environment: int,
) -> np.ndarray:
    selected: list[np.ndarray] = []
    for array, entry in zip(arrays, schedule, strict=True):
        if stream in ("event", "mark", "opportunity"):
            requests = entry["coordinates"]["requests"]
            mask = np.asarray(
                [int(request[0]) == int(environment) for request in requests],
                dtype=np.bool_,
            )
            selected.append(np.asarray(array)[mask].reshape(-1))
        elif stream == "primitive":
            selected.append(np.asarray(array)[int(environment)].reshape(-1))
    if selected:
        return np.ascontiguousarray(np.concatenate(selected))
    return np.empty(0, dtype=np.uint8)


def _typed_rng_evidence_valid(evidence: Any) -> bool:
    if not isinstance(evidence, Mapping) or set(evidence) != {
        "source_environment", "streams", "realized_variates_exact", "passed",
    }:
        return False
    streams = evidence["streams"]
    if not isinstance(streams, Mapping) or tuple(streams) != RNG_NAMES:
        return False
    environment = int(evidence["source_environment"])
    valid = True
    for name in RNG_NAMES:
        row = streams[name]
        if not isinstance(row, Mapping) or set(row) != {
            "seed", "start_state", "schedule", "consumption_position",
            "consumed_payload", "consumed_payload_digest", "end_state",
        }:
            return False
        try:
            _digest, end_state, arrays = _replay_rng_schedule(
                row["start_state"], row["schedule"], seed=int(row["seed"]),
            )
            consumed = _decode_native_payload(row["consumed_payload"])
            expected = _expected_row_consumption(
                stream=name, arrays=arrays, schedule=row["schedule"],
                environment=environment,
            )
        except (KeyError, TypeError, ValueError, IndexError):
            return False
        valid = valid and bool(
            end_state == row["end_state"]
            and int(row["consumption_position"]) == int(expected.size)
            and consumed.dtype == expected.dtype
            and consumed.shape == expected.shape
            and consumed.tobytes(order="C") == expected.tobytes(order="C")
            and row["consumed_payload_digest"]
            == hashlib.sha256(consumed.tobytes(order="C")).hexdigest()
        )
    return bool(valid)


def _first_typed_failure(
    evidence_order: Iterable[tuple[str, Mapping[str, Any]]], *,
    report: Mapping[str, Any],
) -> dict[str, Any] | None:
    for evidence_class, evidence in evidence_order:
        if bool(evidence["passed"]):
            continue
        comparisons = evidence.get("fields", evidence.get("comparisons", ()))
        failure = _comparison_failure(
            comparisons, evidence_class=evidence_class,
        )
        if failure is not None:
            comparison = next(
                row for row in comparisons if not bool(row.get("passed"))
            )
            if "pair_coordinate" in comparison:
                failure["coordinate"] = {
                    "pair": deepcopy(comparison["pair_coordinate"]),
                    "payload": comparison.get("first_coordinate"),
                }
            return failure
        return {
            "class": evidence_class,
            "field": None,
            "coordinate": None,
            "magnitude": None,
            "ulp_distance": None,
            "detail": (
                {
                    "critic_record_valid": False,
                    "likelihood_components_valid": False,
                    "joint_record_valid": False,
                    "replay_failures": deepcopy(report.get("failures")),
                }
                if evidence_class == "derived" else None
            ),
        }
    return None
def _typed_natural_audit(
    arm: CommitmentArm,
    branch: EventTrajectory,
    branch_index: int,
    original: EventTrajectory,
    original_env: int,
    *,
    start: int,
    audit_id: str,
    replicate: int,
    batch_index: int,
    focal_key: int,
    natural_action: str,
    natural_branch: str,
    rng_binding_material: Mapping[str, Mapping[str, Any]],
    consumed_streams: Mapping[str, _AuditRowStream],
) -> dict[str, Any]:
    structural_comparisons = [
        native_bitwise_finite_comparison(
            _tensor_payload(getattr(original, name)[start:, original_env]),
            _tensor_payload(getattr(branch, name)[:, branch_index]),
            field=name,
        )
        for name in CAUSAL_STRUCTURAL_FIELDS
    ]
    causal_comparisons = [
        native_bitwise_finite_comparison(
            _tensor_payload(getattr(original, name)[start:, original_env]),
            _tensor_payload(getattr(branch, name)[:, branch_index]),
            field=name,
        )
        for name in CAUSAL_FLOAT_FIELDS
    ]
    structural_evidence = {
        "fields": structural_comparisons,
        "passed": all(row["passed"] for row in structural_comparisons),
    }

    source_segments = [vars(value) for value in original.segments[original_env]]
    natural_segments = [vars(value) for value in branch.segments[branch_index]]
    segment_evidence = {
        "source": source_segments,
        "natural": natural_segments,
        "passed": source_segments == natural_segments,
    }
    reward_comparison = native_bitwise_finite_comparison(
        _tensor_payload(original.rewards[start:, original_env]),
        _tensor_payload(branch.rewards[:, branch_index]),
        field="rewards",
    )
    source_outcome = vars(original.outcomes[original_env])
    natural_outcome = vars(branch.outcomes[branch_index])
    outcome_evidence = {
        "source": source_outcome,
        "natural": natural_outcome,
        "reward_comparison": reward_comparison,
        "passed": source_outcome == natural_outcome and reward_comparison["passed"],
    }

    source_calls = _selected_executed_calls(
        original, row=original_env, start=start,
    )
    natural_calls = _selected_executed_calls(
        branch, row=branch_index, start=start,
    )
    focal_source_coordinates = [
        call["identity"]["scientific_coordinate"]
        for call in source_calls
        if (
            call["identity"]["sampler_family"] == "event"
            and int(call["identity"]["scientific_coordinate"]["time"])
            == int(start)
            and int(
                call["identity"]["scientific_coordinate"]["lifecycle_key"]
            ) == int(focal_key)
        )
    ]
    focal_source_coordinate = (
        focal_source_coordinates[0]
        if len(focal_source_coordinates) == 1
        else {
            "membership_epoch": int(
                original.membership_epoch[start, original_env, focal_key]
            ),
            "segment_id": int(
                original.segment_id[start, original_env, focal_key]
            ),
        }
    )
    source_by_key = {_call_coordinate_key(call): call for call in source_calls}
    natural_by_key = {_call_coordinate_key(call): call for call in natural_calls}
    duplicate_source = len(source_by_key) != len(source_calls)
    duplicate_natural = len(natural_by_key) != len(natural_calls)
    expected_keys = sorted(set(source_by_key) | set(natural_by_key))
    parameter_evidence = _parameter_payload_evidence(arm)
    pair_records: list[dict[str, Any]] = []
    event_comparisons: list[dict[str, Any]] = []
    mark_comparisons: list[dict[str, Any]] = []
    primitive_comparisons: list[dict[str, Any]] = []
    event_actions_exact = True
    primitive_actions_exact = True
    realized_variates_exact = True
    expected_final = KEEP if natural_action == "KEEP" else RENEW

    for key in expected_keys:
        source = source_by_key.get(key)
        natural = natural_by_key.get(key)
        coordinate = list(key)
        pair_passed = source is not None and natural is not None
        pair: dict[str, Any] = {
            "coordinate": coordinate,
            "continuation_offset": int(key[1]) - int(start),
            "source_call": deepcopy(source),
            "natural_call": deepcopy(natural),
            "pair_digest": None,
            "passed": False,
        }
        if pair_passed:
            assert source is not None and natural is not None
            source_identity = source["identity"]
            natural_identity = natural["identity"]
            source_scientific = dict(source_identity["scientific_coordinate"])
            natural_scientific = dict(natural_identity["scientific_coordinate"])
            source_scientific.pop("environment_row")
            natural_scientific.pop("environment_row")
            pair_passed = bool(
                source_identity["sampler_family"]
                == natural_identity["sampler_family"]
                and source_identity["call_site"] == natural_identity["call_site"]
                and source_scientific == natural_scientific
                and source_identity["parameter_digest"]
                == natural_identity["parameter_digest"]
            )
            family = str(source_identity["sampler_family"])
            causal_comparisons.extend(_call_input_comparisons(
                source["input"], natural["input"], family=family,
                pair_coordinate=coordinate,
            ))
            source_payload = source["payload"]
            natural_payload = natural["payload"]
            if family == "event":
                for name in ("cdf", "converted_uniform"):
                    comparison = _paired_comparison(
                        source_payload[name], natural_payload[name],
                        field=f"event.{name}", pair_coordinate=coordinate,
                    )
                    event_comparisons.append(comparison)
                    if name == "converted_uniform":
                        realized_variates_exact &= bool(comparison["passed"])
                scientific = source_identity["scientific_coordinate"]
                focal = (
                    int(scientific["time"]) == int(start)
                    and int(scientific["lifecycle_key"]) == int(focal_key)
                )
                actions_pass = (
                    int(source_payload["pre_force_action"])
                    == int(natural_payload["pre_force_action"])
                    and int(source_payload["final_action"])
                    == int(natural_payload["final_action"])
                    and (
                        not focal
                        or int(source_payload["final_action"]) == expected_final
                    )
                )
                event_actions_exact &= bool(actions_pass)
            elif family == "mark":
                for name in (
                    "mu", "sigma", "noise", "u", "tanh_u", "candidate_mark",
                ):
                    comparison = _paired_comparison(
                        source_payload[name], natural_payload[name],
                        field=f"mark.{name}", pair_coordinate=coordinate,
                    )
                    mark_comparisons.append(comparison)
                    if name == "noise":
                        realized_variates_exact &= bool(comparison["passed"])
            elif family == "primitive":
                for name in ("cdf", "converted_uniform"):
                    comparison = _paired_comparison(
                        source_payload[name], natural_payload[name],
                        field=f"primitive.{name}", pair_coordinate=coordinate,
                    )
                    primitive_comparisons.append(comparison)
                    if name == "converted_uniform":
                        realized_variates_exact &= bool(comparison["passed"])
                primitive_actions_exact &= bool(
                    int(source_payload["selected_action"])
                    == int(natural_payload["selected_action"])
                )
            pair_digest_material = {
                "schema": TYPED_CAUSAL_AUDIT_SCHEMA,
                "audit_id": audit_id,
                "replicate": int(replicate),
                "batch_index": int(batch_index),
                "source_episode": int(original.ledger_ids[original_env]),
                "source_environment": int(original_env),
                "focal_time": int(start),
                "focal_key": int(focal_key),
                "natural_action": natural_action,
                "natural_branch": natural_branch,
                "continuation_offset": int(key[1]) - int(start),
                "coordinate": coordinate,
                "source_call": source,
                "natural_call": natural,
            }
            pair["pair_digest"] = _canonical_json_digest(pair_digest_material)
        pair["passed"] = bool(pair_passed)
        pair_records.append(pair)

    source_family_counts = Counter(
        call["identity"]["sampler_family"] for call in source_calls
    )
    natural_family_counts = Counter(
        call["identity"]["sampler_family"] for call in natural_calls
    )
    expected_family_counts = {
        "event": int(original.event_cat_mask[start:, original_env].sum()),
        "mark": int(original.event_kind[start:, original_env].ne(0).sum()),
        "primitive": int(original.active_mask[start:, original_env].sum()),
    }
    binding_passed = bool(
        source_calls
        and len(focal_source_coordinates) == 1
        and not duplicate_source
        and not duplicate_natural
        and len(source_calls) == len(natural_calls)
        and all(pair["passed"] for pair in pair_records)
        and dict(source_family_counts) == expected_family_counts
        and dict(natural_family_counts) == expected_family_counts
    )
    binding_evidence = {
        "audit_id": audit_id,
        "replicate": int(replicate),
        "batch_index": int(batch_index),
        "source_episode": int(original.ledger_ids[original_env]),
        "focal_time": int(start),
        "source_environment": int(original_env),
        "focal_key": int(focal_key),
        "membership_epoch": int(focal_source_coordinate["membership_epoch"]),
        "segment_id": int(focal_source_coordinate["segment_id"]),
        "natural_action": natural_action,
        "natural_branch": natural_branch,
        "parameter_evidence": parameter_evidence,
        "expected_family_counts": expected_family_counts,
        "expected_pairs": len(expected_keys),
        "source_call_count": len(source_calls),
        "natural_call_count": len(natural_calls),
        "duplicate_source": duplicate_source,
        "duplicate_natural": duplicate_natural,
        "pairs": pair_records,
        "passed": binding_passed,
    }

    event_expected = expected_family_counts["event"]
    mark_expected = expected_family_counts["mark"]
    primitive_expected = expected_family_counts["primitive"]
    event_kernel = {
        "expected_call_count": event_expected,
        "comparisons": event_comparisons,
        "selected_actions_exact": bool(event_actions_exact),
        "parameter_exact": all(
            pair["source_call"]["identity"]["parameter_digest"]
            == pair["natural_call"]["identity"]["parameter_digest"]
            for pair in pair_records
            if pair["source_call"] is not None
            and pair["source_call"]["identity"]["sampler_family"] == "event"
        ),
    }
    event_kernel["passed"] = bool(
        len(event_comparisons) == 2 * event_expected
        and all(row["passed"] for row in event_comparisons)
        and event_kernel["selected_actions_exact"]
        and event_kernel["parameter_exact"]
    )
    mark_kernel = {
        "expected_call_count": mark_expected,
        "comparisons": mark_comparisons,
    }
    mark_kernel["passed"] = bool(
        len(mark_comparisons) == 6 * mark_expected
        and all(row["passed"] for row in mark_comparisons)
    )
    primitive_kernel = {
        "expected_call_count": primitive_expected,
        "comparisons": primitive_comparisons,
        "selected_actions_exact": bool(primitive_actions_exact),
        "parameter_exact": all(
            pair["source_call"]["identity"]["parameter_digest"]
            == pair["natural_call"]["identity"]["parameter_digest"]
            for pair in pair_records
            if pair["source_call"] is not None
            and pair["source_call"]["identity"]["sampler_family"] == "primitive"
        ),
    }
    primitive_kernel["passed"] = bool(
        len(primitive_comparisons) == 2 * primitive_expected
        and all(row["passed"] for row in primitive_comparisons)
        and primitive_kernel["selected_actions_exact"]
        and primitive_kernel["parameter_exact"]
    )
    kernel_evidence = {
        "event": event_kernel,
        "mark": mark_kernel,
        "primitive": primitive_kernel,
    }
    causal_field_evidence = {
        "fields": causal_comparisons,
        "passed": all(row["passed"] for row in causal_comparisons),
    }
    rng_evidence = _typed_rng_provenance(
        rng_binding_material, consumed_streams,
        replicate=replicate, source_environment=original_env,
    )
    rng_evidence["realized_variates_exact"] = bool(realized_variates_exact)
    rng_evidence["passed"] = bool(
        realized_variates_exact and _typed_rng_evidence_valid(rng_evidence)
    )

    natural_replay_trajectory = _trajectory_environment_slice(
        branch, branch_index
    )
    derived_reference = _derived_reference_trajectory(
        natural_replay_trajectory, 0, original, original_env, start=start
    )
    replay = replay_trajectory(
        arm, natural_replay_trajectory, device=branch.rewards.device
    )
    report = replay_report(replay, derived_reference)
    categorical_rows_required = bool(
        natural_replay_trajectory.event_cat_mask.any()
    )
    mark_rows_required = bool(
        natural_replay_trajectory.event_mark_mask.any()
    )
    critic_valid, likelihood_valid, joint_valid = (
        _validate_replay_report_evidence(
            report,
            event_rows_required=(
                categorical_rows_required or mark_rows_required
            ),
            categorical_rows_required=categorical_rows_required,
            mark_rows_required=mark_rows_required,
        )
    )
    derived_passed = critic_valid and likelihood_valid and joint_valid
    derived_evidence = {
        "replay_report": report,
        "critic_record_valid": critic_valid,
        "likelihood_components_valid": likelihood_valid,
        "joint_record_valid": joint_valid,
        "passed": derived_passed,
    }
    causal_identity_passed = bool(
        binding_evidence["passed"]
        and structural_evidence["passed"]
        and causal_field_evidence["passed"]
        and segment_evidence["passed"]
        and outcome_evidence["passed"]
        and rng_evidence["passed"]
        and event_kernel["passed"]
        and mark_kernel["passed"]
        and primitive_kernel["passed"]
    )
    evidence_order = (
        ("binding", binding_evidence),
        ("structural", structural_evidence),
        ("causal_field", causal_field_evidence),
        ("segment", segment_evidence),
        ("outcome", outcome_evidence),
        ("rng", rng_evidence),
        ("event_kernel", event_kernel),
        ("mark_kernel", mark_kernel),
        ("primitive_kernel", primitive_kernel),
        ("derived", derived_evidence),
    )
    first_failure = _first_typed_failure(evidence_order, report=report)
    comparison_rows = [
        *causal_comparisons, *event_comparisons, *mark_comparisons,
        *primitive_comparisons,
    ]
    finite_comparison_failure = bool(
        comparison_rows
        and all(not row["malformed"] and row["finite"] for row in comparison_rows)
        and any(not row["passed"] for row in comparison_rows)
    )
    unavailable = bool(
        binding_evidence["passed"]
        and structural_evidence["passed"]
        and segment_evidence["passed"]
        and outcome_evidence["passed"]
        and rng_evidence["passed"]
        and derived_evidence["passed"]
        and event_kernel["selected_actions_exact"]
        and event_kernel["parameter_exact"]
        and primitive_kernel["selected_actions_exact"]
        and primitive_kernel["parameter_exact"]
        and finite_comparison_failure
    )
    if causal_identity_passed and derived_passed:
        status, reason_code = "complete", None
    elif unavailable:
        status = "unavailable"
        reason_code = "natural_branch_causal_identity_failed"
    else:
        raise RuntimeError(
            f"INVALID_OPERATIONAL typed natural audit {first_failure}"
        )
    record = {
        "schema": TYPED_CAUSAL_AUDIT_SCHEMA,
        "status": status,
        "reason_code": reason_code,
        "causal_identity_passed": causal_identity_passed,
        "derived_record_fidelity_passed": derived_passed,
        "runtime_provenance": _runtime_provenance(),
        "binding_evidence": binding_evidence,
        "structural_evidence": structural_evidence,
        "causal_field_evidence": causal_field_evidence,
        "segment_evidence": segment_evidence,
        "outcome_evidence": outcome_evidence,
        "rng_evidence": rng_evidence,
        "kernel_evidence": kernel_evidence,
        "derived_evidence": derived_evidence,
        "first_failure": first_failure,
        "attempted_rows": 1,
        "completed_rows": int(status == "complete"),
    }
    if not validate_typed_natural_audit(record):
        raise RuntimeError(
            "INVALID_OPERATIONAL typed natural audit self-validation failed"
        )
    return record


_TYPED_NATURAL_AUDIT_KEYS = frozenset({
    "schema", "status", "reason_code", "causal_identity_passed",
    "derived_record_fidelity_passed", "runtime_provenance",
    "binding_evidence", "structural_evidence", "causal_field_evidence",
    "segment_evidence", "outcome_evidence", "rng_evidence",
    "kernel_evidence", "derived_evidence", "first_failure",
    "attempted_rows", "completed_rows",
})


def validate_typed_natural_audit(record: Mapping[str, Any]) -> bool:
    """Recompute the complete typed contract from serialized natural evidence."""

    try:
        if (
            not isinstance(record, Mapping)
            or set(record) != _TYPED_NATURAL_AUDIT_KEYS
            or record["schema"] != TYPED_CAUSAL_AUDIT_SCHEMA
            or record["status"] not in ("complete", "unavailable")
            or type(record["attempted_rows"]) is not int
            or int(record["attempted_rows"]) != 1
            or record["runtime_provenance"] != _runtime_provenance()
        ):
            return False

        def comparison_valid(row: Mapping[str, Any]) -> bool:
            expected = native_bitwise_finite_comparison(
                row["source_payload"], row["natural_payload"],
                field=str(row["field"]),
            )
            if "pair_coordinate" in row:
                expected["pair_coordinate"] = deepcopy(row["pair_coordinate"])
            return dict(row) == expected

        binding = record["binding_evidence"]
        binding_keys = {
            "audit_id", "replicate", "batch_index", "source_episode",
            "focal_time", "source_environment", "focal_key",
            "membership_epoch", "segment_id", "natural_action",
            "natural_branch", "parameter_evidence",
            "expected_family_counts", "expected_pairs",
            "source_call_count", "natural_call_count", "duplicate_source",
            "duplicate_natural", "pairs", "passed",
        }
        if (
            not isinstance(binding, Mapping)
            or set(binding) != binding_keys
            or binding["natural_action"] not in ("KEEP", "RENEW")
            or binding["natural_branch"] != (
                AUDIT_BRANCHES[0]
                if binding["natural_action"] == "KEEP"
                else AUDIT_BRANCHES[2]
            )
            or not _parameter_evidence_valid(binding["parameter_evidence"])
            or not isinstance(binding["pairs"], list)
        ):
            return False
        parameters = binding["parameter_evidence"]
        pairs = binding["pairs"]
        source_calls: list[Mapping[str, Any]] = []
        natural_calls: list[Mapping[str, Any]] = []
        pair_valid = True
        for pair in pairs:
            if not isinstance(pair, Mapping) or set(pair) != {
                "coordinate", "continuation_offset", "source_call",
                "natural_call", "pair_digest", "passed",
            }:
                return False
            source = pair["source_call"]
            natural = pair["natural_call"]
            if not (
                _canonical_call_valid(source, parameter_evidence=parameters)
                and _canonical_call_valid(natural, parameter_evidence=parameters)
            ):
                return False
            source_calls.append(source)
            natural_calls.append(natural)
            source_identity = source["identity"]
            natural_identity = natural["identity"]
            source_scientific = dict(source_identity["scientific_coordinate"])
            natural_scientific = dict(natural_identity["scientific_coordinate"])
            source_environment = int(source_scientific.pop("environment_row"))
            natural_scientific.pop("environment_row")
            coordinate = list(_call_coordinate_key(source))
            expected_digest = _canonical_json_digest({
                "schema": TYPED_CAUSAL_AUDIT_SCHEMA,
                "audit_id": binding["audit_id"],
                "replicate": int(binding["replicate"]),
                "batch_index": int(binding["batch_index"]),
                "source_episode": int(binding["source_episode"]),
                "source_environment": int(binding["source_environment"]),
                "focal_time": int(binding["focal_time"]),
                "focal_key": int(binding["focal_key"]),
                "natural_action": binding["natural_action"],
                "natural_branch": binding["natural_branch"],
                "continuation_offset": int(pair["continuation_offset"]),
                "coordinate": coordinate,
                "source_call": source,
                "natural_call": natural,
            })
            actual = bool(
                pair["coordinate"] == coordinate
                and tuple(coordinate) == _call_coordinate_key(natural)
                and source_identity["sampler_family"]
                == natural_identity["sampler_family"]
                and source_identity["call_site"] == natural_identity["call_site"]
                and source_identity["parameter_digest"]
                == natural_identity["parameter_digest"]
                and source_scientific == natural_scientific
                and source_environment == int(binding["source_environment"])
                and int(source_scientific["episode_id"])
                == int(binding["source_episode"])
                and int(pair["continuation_offset"])
                == int(source_scientific["time"]) - int(binding["focal_time"])
                and pair["pair_digest"] == expected_digest
            )
            pair_valid &= actual and bool(pair["passed"]) == actual

        if [pair["coordinate"] for pair in pairs] != sorted(
            pair["coordinate"] for pair in pairs
        ):
            return False
        focal_source_coordinates = [
            call["identity"]["scientific_coordinate"]
            for call in source_calls
            if (
                call["identity"]["sampler_family"] == "event"
                and int(call["identity"]["scientific_coordinate"]["time"])
                == int(binding["focal_time"])
                and int(
                    call["identity"]["scientific_coordinate"]["lifecycle_key"]
                ) == int(binding["focal_key"])
            )
        ]
        focal_coordinate_valid = bool(
            len(focal_source_coordinates) == 1
            and int(focal_source_coordinates[0]["membership_epoch"])
            == int(binding["membership_epoch"])
            and int(focal_source_coordinates[0]["segment_id"])
            == int(binding["segment_id"])
        )

        def call_ids_valid(calls: list[Mapping[str, Any]]) -> bool:
            signatures: dict[int, tuple[Any, ...]] = {}
            times: dict[int, set[int]] = {}
            for call in calls:
                identity = call["identity"]
                call_id = int(identity["call_id"])
                signature = (
                    identity["sampler_family"], identity["call_site"],
                    int(identity["packed_width"]),
                    _canonical_json_digest(call["physical_rows"]),
                    int(identity["scientific_coordinate"]["time"]),
                )
                if call_id in signatures and signatures[call_id] != signature:
                    return False
                signatures[call_id] = signature
                times.setdefault(
                    int(identity["scientific_coordinate"]["time"]), set()
                ).add(call_id)
            previous = -1
            for time in sorted(times):
                current = sorted(times[time])
                if current[0] <= previous:
                    return False
                previous = current[-1]
            return True

        structural_rows = record["structural_evidence"]["fields"]
        if (
            tuple(row["field"] for row in structural_rows)
            != CAUSAL_STRUCTURAL_FIELDS
            or not all(comparison_valid(row) for row in structural_rows)
        ):
            return False
        structural_passed = all(bool(row["passed"]) for row in structural_rows)
        structural_sources = {
            row["field"]: _decode_native_payload(row["source_payload"])
            for row in structural_rows
        }
        expected_family_counts = {
            "event": int(np.asarray(structural_sources["event_cat_mask"]).sum()),
            "mark": int(
                (
                    np.asarray(structural_sources["event_kind"]).astype(np.int64)
                    != 0
                ).sum()
            ),
            "primitive": int(
                np.asarray(structural_sources["active_mask"]).sum()
            ),
        }
        source_family_counts = dict(Counter(
            call["identity"]["sampler_family"] for call in source_calls
        ))
        natural_family_counts = dict(Counter(
            call["identity"]["sampler_family"] for call in natural_calls
        ))
        binding_passed = bool(
            pairs
            and pair_valid
            and focal_coordinate_valid
            and not bool(binding["duplicate_source"])
            and not bool(binding["duplicate_natural"])
            and int(binding["expected_pairs"]) == len(pairs)
            and int(binding["source_call_count"]) == len(source_calls)
            and int(binding["natural_call_count"]) == len(natural_calls)
            and binding["expected_family_counts"] == expected_family_counts
            and source_family_counts == expected_family_counts
            and natural_family_counts == expected_family_counts
            and call_ids_valid(source_calls)
            and call_ids_valid(natural_calls)
        )

        expected_input_rows = [
            comparison
            for pair in pairs
            for comparison in _call_input_comparisons(
                pair["source_call"]["input"],
                pair["natural_call"]["input"],
                family=pair["source_call"]["identity"]["sampler_family"],
                pair_coordinate=pair["coordinate"],
            )
        ]
        causal_rows = record["causal_field_evidence"]["fields"]
        if (
            tuple(row["field"] for row in causal_rows[:len(CAUSAL_FLOAT_FIELDS)])
            != CAUSAL_FLOAT_FIELDS
            or causal_rows[len(CAUSAL_FLOAT_FIELDS):] != expected_input_rows
            or not all(comparison_valid(row) for row in causal_rows)
        ):
            return False
        causal_passed = all(bool(row["passed"]) for row in causal_rows)
        segment_passed = (
            record["segment_evidence"]["source"]
            == record["segment_evidence"]["natural"]
        )
        outcome = record["outcome_evidence"]
        reward_comparison = native_bitwise_finite_comparison(
            outcome["reward_comparison"]["source_payload"],
            outcome["reward_comparison"]["natural_payload"],
            field="rewards",
        )
        if reward_comparison != outcome["reward_comparison"]:
            return False
        outcome_passed = bool(
            outcome["source"] == outcome["natural"]
            and reward_comparison["passed"]
        )

        family_pairs = {
            family: [
                pair for pair in pairs
                if pair["source_call"]["identity"]["sampler_family"] == family
            ]
            for family in ("event", "mark", "primitive")
        }
        expected_comparisons: dict[str, list[dict[str, Any]]] = {
            "event": [],
            "mark": [],
            "primitive": [],
        }
        event_actions_exact = True
        primitive_actions_exact = True
        expected_final = (
            KEEP if binding["natural_action"] == "KEEP" else RENEW
        )
        for family, rows in family_pairs.items():
            names = (
                ("cdf", "converted_uniform") if family != "mark"
                else ("mu", "sigma", "noise", "u", "tanh_u", "candidate_mark")
            )
            for pair in rows:
                source = pair["source_call"]
                natural = pair["natural_call"]
                for name in names:
                    expected_comparisons[family].append(_paired_comparison(
                        source["payload"][name], natural["payload"][name],
                        field=f"{family}.{name}",
                        pair_coordinate=pair["coordinate"],
                    ))
                if family == "event":
                    coordinate = source["identity"]["scientific_coordinate"]
                    focal = (
                        int(coordinate["time"]) == int(binding["focal_time"])
                        and int(coordinate["lifecycle_key"])
                        == int(binding["focal_key"])
                    )
                    event_actions_exact &= bool(
                        int(source["payload"]["pre_force_action"])
                        == int(natural["payload"]["pre_force_action"])
                        and int(source["payload"]["final_action"])
                        == int(natural["payload"]["final_action"])
                        and (
                            not focal
                            or int(source["payload"]["final_action"])
                            == expected_final
                        )
                    )
                elif family == "primitive":
                    primitive_actions_exact &= bool(
                        int(source["payload"]["selected_action"])
                        == int(natural["payload"]["selected_action"])
                    )

        kernels = record["kernel_evidence"]
        if not isinstance(kernels, Mapping) or set(kernels) != {
            "event", "mark", "primitive",
        }:
            return False
        event_parameter_exact = all(
            pair["source_call"]["identity"]["parameter_digest"]
            == pair["natural_call"]["identity"]["parameter_digest"]
            for pair in family_pairs["event"]
        )
        primitive_parameter_exact = all(
            pair["source_call"]["identity"]["parameter_digest"]
            == pair["natural_call"]["identity"]["parameter_digest"]
            for pair in family_pairs["primitive"]
        )
        family_passed: dict[str, bool] = {}
        for family in ("event", "mark", "primitive"):
            kernel = kernels[family]
            expected_keys = (
                {"expected_call_count", "comparisons", "passed"}
                if family == "mark"
                else {
                    "expected_call_count", "comparisons",
                    "selected_actions_exact", "parameter_exact", "passed",
                }
            )
            if (
                not isinstance(kernel, Mapping)
                or set(kernel) != expected_keys
                or int(kernel["expected_call_count"])
                != expected_family_counts[family]
                or kernel["comparisons"] != expected_comparisons[family]
                or not all(comparison_valid(row) for row in kernel["comparisons"])
            ):
                return False
            actual = all(
                bool(row["passed"]) for row in expected_comparisons[family]
            )
            if family == "event":
                actual &= event_actions_exact and event_parameter_exact
                if (
                    bool(kernel["selected_actions_exact"]) != event_actions_exact
                    or bool(kernel["parameter_exact"]) != event_parameter_exact
                ):
                    return False
            elif family == "primitive":
                actual &= primitive_actions_exact and primitive_parameter_exact
                if (
                    bool(kernel["selected_actions_exact"])
                    != primitive_actions_exact
                    or bool(kernel["parameter_exact"])
                    != primitive_parameter_exact
                ):
                    return False
            family_passed[family] = bool(actual)

        realized_rows = [
            row
            for family in ("event", "mark", "primitive")
            for row in expected_comparisons[family]
            if row["field"].endswith("converted_uniform")
            or row["field"] == "mark.noise"
        ]
        realized_exact = all(bool(row["passed"]) for row in realized_rows)
        rng_passed = _typed_rng_evidence_valid(record["rng_evidence"])
        if (
            bool(record["rng_evidence"]["realized_variates_exact"])
            != realized_exact
        ):
            return False
        rng_passed &= realized_exact
        categorical_rows_required = bool(
            np.asarray(structural_sources["event_cat_mask"]).any()
        )
        mark_rows_required = bool(
            np.asarray(structural_sources["event_mark_mask"]).any()
        )
        critic, likelihood, joint = _validate_replay_report_evidence(
            record["derived_evidence"]["replay_report"],
            event_rows_required=(
                categorical_rows_required or mark_rows_required
            ),
            categorical_rows_required=categorical_rows_required,
            mark_rows_required=mark_rows_required,
        )
        derived_passed = critic and likelihood and joint
        summaries = (
            (binding["passed"], binding_passed),
            (record["structural_evidence"]["passed"], structural_passed),
            (record["causal_field_evidence"]["passed"], causal_passed),
            (record["segment_evidence"]["passed"], segment_passed),
            (record["outcome_evidence"]["passed"], outcome_passed),
            (record["rng_evidence"]["passed"], rng_passed),
            (kernels["event"]["passed"], family_passed["event"]),
            (kernels["mark"]["passed"], family_passed["mark"]),
            (kernels["primitive"]["passed"], family_passed["primitive"]),
            (record["derived_evidence"]["critic_record_valid"], critic),
            (record["derived_evidence"]["likelihood_components_valid"], likelihood),
            (record["derived_evidence"]["joint_record_valid"], joint),
            (record["derived_evidence"]["passed"], derived_passed),
        )
        if any(bool(stored) != bool(actual) for stored, actual in summaries):
            return False
        causal_identity = bool(
            binding_passed and structural_passed and causal_passed
            and segment_passed and outcome_passed and rng_passed
            and all(family_passed.values())
        )
        if (
            bool(record["causal_identity_passed"]) != causal_identity
            or bool(record["derived_record_fidelity_passed"]) != derived_passed
        ):
            return False
        actual_evidence_order = (
            ("binding", {"passed": binding_passed}),
            ("structural", {
                "passed": structural_passed, "fields": structural_rows,
            }),
            ("causal_field", {
                "passed": causal_passed, "fields": causal_rows,
            }),
            ("segment", {"passed": segment_passed}),
            ("outcome", {"passed": outcome_passed}),
            ("rng", {"passed": rng_passed}),
            ("event_kernel", {
                "passed": family_passed["event"],
                "comparisons": expected_comparisons["event"],
            }),
            ("mark_kernel", {
                "passed": family_passed["mark"],
                "comparisons": expected_comparisons["mark"],
            }),
            ("primitive_kernel", {
                "passed": family_passed["primitive"],
                "comparisons": expected_comparisons["primitive"],
            }),
            ("derived", {"passed": derived_passed}),
        )
        expected_first_failure = _first_typed_failure(
            actual_evidence_order,
            report=record["derived_evidence"]["replay_report"],
        )
        if record["first_failure"] != expected_first_failure:
            return False
        if record["status"] == "complete":
            return bool(
                causal_identity
                and derived_passed
                and record["reason_code"] is None
                and expected_first_failure is None
                and int(record["completed_rows"]) == 1
            )
        comparison_rows = [
            *causal_rows,
            *expected_comparisons["event"],
            *expected_comparisons["mark"],
            *expected_comparisons["primitive"],
        ]
        finite_comparison_failure = bool(
            comparison_rows
            and all(
                comparison_valid(row)
                and not bool(row["malformed"])
                and bool(row["finite"])
                for row in comparison_rows
            )
            and any(not bool(row["passed"]) for row in comparison_rows)
        )
        return bool(
            binding_passed and structural_passed and segment_passed
            and outcome_passed and rng_passed and derived_passed
            and finite_comparison_failure
            and event_actions_exact and event_parameter_exact
            and primitive_actions_exact and primitive_parameter_exact
            and not causal_identity
            and record["reason_code"]
            == "natural_branch_causal_identity_failed"
            and int(record["completed_rows"]) == 0
        )
    except (
        KeyError, TypeError, ValueError, OverflowError, IndexError,
        binascii.Error,
    ):
        return False

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
    """Audit selected rows lazily in deterministic order at physical width 16."""

    if arm.arm == "OR" or not selected_states:
        return []
    total_started = perf_counter()
    prefix_seconds = 0.0
    branch_seconds = 0.0
    prefix_collector_calls = 0
    branch_collector_calls = 0
    physical_selected_state_count = 0
    padding_row_count = 0
    prefix_cache: dict[tuple[int, int], tuple[CollectionCursor, TrainingState]] = {}
    ordered_results: list[dict[str, Any]] = []
    selected_index = 0
    stop = False
    while selected_index < len(selected_states) and not stop:
        first = selected_states[selected_index]
        cell = (int(first["batch_index"]), int(first["time"]))
        chunk: list[dict[str, Any]] = []
        while (
            selected_index < len(selected_states)
            and len(chunk) < 5
            and (
                int(selected_states[selected_index]["batch_index"]),
                int(selected_states[selected_index]["time"]),
            ) == cell
        ):
            chunk.append(selected_states[selected_index])
            selected_index += 1

        prefix_started = perf_counter()
        cached = prefix_cache.get(cell)
        if cached is None:
            origin = deepcopy(chunk[0]["origin_state"])
            trajectory = chunk[0]["trajectory"]
            prefix = collect_trajectory(
                arm,
                origin,
                device=device,
                episode_ids=trajectory.ledger_ids,
                max_steps=cell[1],
                deterministic=False,
                profile=origin.profile,
            )
            if prefix.cursor is None:
                raise RuntimeError("batched audit prefix unexpectedly terminated")
            cached = (prefix.cursor, origin)
            prefix_cache[cell] = cached
            prefix_collector_calls += 1
        prefix_seconds += perf_counter() - prefix_started
        prefix_cursor, prefix_state = cached

        prepared: list[dict[str, Any]] = []
        for record in chunk:
            trajectory = record["trajectory"]
            env_index = int(record["env_index"])
            streams, end_rng_states, rng_material = _audit_row_scripts(
                trajectory, prefix_state.rngs,
                time=int(record["time"]), env_index=env_index,
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
                "cursor": _isolate_audit_cursor(prefix_cursor, env_index),
                "streams": streams,
                "end_rng_states": end_rng_states,
                "rng_binding_material": rng_material,
                "donor_u_tensor": donor_u,
                "donor_z_tensor": donor_z,
                "donor_candidate_u_payload": donor_u_payload,
                "donor_candidate_z_payload": donor_z_payload,
            })

        branches: list[dict[str, Any]] = []
        for pair in prepared:
            time = int(pair["time"])
            env_index = int(pair["env_index"])
            key = int(pair["key"])
            for branch_name, kind, new_z in (
                (
                    AUDIT_BRANCHES[0], KEEP,
                    pair["trajectory"].event_z_pre[time, env_index, key],
                ),
                (AUDIT_BRANCHES[1], RENEW, pair["donor_z_tensor"]),
                (
                    AUDIT_BRANCHES[2], RENEW,
                    pair["trajectory"].candidate_z[time, env_index, key],
                ),
            ):
                branches.append({
                    "pair": pair,
                    "branch_name": branch_name,
                    "kind": kind,
                    "new_z": new_z,
                    "cursor": _clone_audit_cursor(pair["cursor"]),
                    "streams": deepcopy(pair["streams"]),
                    "padding": False,
                })
        while len(branches) < FORMAL_NUM_ENVS:
            duplicate = deepcopy(branches[0])
            duplicate["padding"] = True
            branches.append(duplicate)
        physical_selected_state_count += len(prepared)
        padding_row_count += FORMAL_NUM_ENVS - 3 * len(prepared)
        combined = _combine_audit_cursors([
            value["cursor"] for value in branches
        ])
        forced = {
            (cell[1], index, int(value["pair"]["key"])): (
                int(value["kind"]), value["new_z"],
            )
            for index, value in enumerate(branches)
        }
        state = make_training_state(
            arm.arm, int(prepared[0]["replicate"]), profile="held_out"
        )
        branch_started = perf_counter()
        branch_trajectory = collect_trajectory(
            arm,
            state,
            device=device,
            cursor=combined,
            deterministic=False,
            forced_events=forced,
            row_rngs=[value["streams"] for value in branches],
            causal_audit_evidence=True,
        )
        branch_seconds += perf_counter() - branch_started
        branch_collector_calls += 1

        chunk_results: dict[str, dict[str, Any]] = {}
        for index, value in enumerate(branches):
            if value["padding"]:
                continue
            pair = value["pair"]
            audit_id = str(pair["audit_id"])
            time = int(pair["time"])
            env_index = int(pair["env_index"])
            key = int(pair["key"])
            natural_kind = int(
                pair["trajectory"].event_kind[time, env_index, key]
            )
            natural_branch = (
                AUDIT_BRANCHES[0] if natural_kind == KEEP else AUDIT_BRANCHES[2]
            )
            supplied_natural = pair.get("natural_action", natural_branch)
            if supplied_natural not in (
                natural_branch,
                "KEEP" if natural_kind == KEEP else "RENEW",
            ):
                raise ValueError(
                    "selected-state natural action contradicts trace"
                )
            result = chunk_results.setdefault(audit_id, {
                "audit_id": audit_id,
                "natural_action": (
                    "KEEP" if natural_kind == KEEP else "RENEW"
                ),
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
                    "env_index": env_index,
                    "key": key,
                })),
                "branches": {},
            })
            stream_positions = {
                name: int(stream.position)
                for name, stream in value["streams"].items()
            }
            outcome = branch_trajectory.outcomes[index]
            result["branches"][value["branch_name"]] = {
                "outcome": outcome,
                "utility": float(outcome.utility),
                "stream_positions": stream_positions,
                "stream_consumption": {
                    name: stream.consumption_record(
                        pair["end_rng_states"][name]
                    )
                    for name, stream in value["streams"].items()
                },
            }
            if debug:
                result["branches"][value["branch_name"]][
                    "trajectory"
                ] = branch_trajectory
                result["branches"][value["branch_name"]][
                    "branch_index"
                ] = index
            if value["branch_name"] == natural_branch:
                result["natural_audit"] = _typed_natural_audit(
                    arm,
                    branch_trajectory,
                    index,
                    pair["trajectory"],
                    env_index,
                    start=time,
                    audit_id=audit_id,
                    replicate=int(pair["replicate"]),
                    batch_index=int(pair["batch_index"]),
                    focal_key=key,
                    natural_action=(
                        "KEEP" if natural_kind == KEEP else "RENEW"
                    ),
                    natural_branch=natural_branch,
                    rng_binding_material=pair["rng_binding_material"],
                    consumed_streams=value["streams"],
                )

        for pair in prepared:
            result = chunk_results[str(pair["audit_id"])]
            branch_rows = [
                result["branches"][name] for name in AUDIT_BRANCHES
            ]
            positions = [row["stream_positions"] for row in branch_rows]
            consumptions = [row["stream_consumption"] for row in branch_rows]
            if (
                positions[1:] != positions[:-1]
                or consumptions[1:] != consumptions[:-1]
            ):
                raise RuntimeError("batched audit branch RNG contract diverged")
            result["branch_outcomes"] = {
                name: result["branches"][name]["outcome"]
                for name in AUDIT_BRANCHES
            }
            result["rng_contract_equal"] = True
            ordered_results.append(result)
            if result["natural_audit"]["status"] == "unavailable":
                stop = True
                break

    telemetry = {
        "prefix_seconds": float(prefix_seconds),
        "branch_seconds": float(branch_seconds),
        "total_seconds": float(perf_counter() - total_started),
        "selected_state_count": len(ordered_results),
        "physical_selected_state_count": physical_selected_state_count,
        "padding_row_count": padding_row_count,
        "collector_call_count": (
            prefix_collector_calls + branch_collector_calls
        ),
    }
    for result in ordered_results:
        result["telemetry"] = deepcopy(telemetry)
        result["telemetry"]["serialized_size_bytes"] = _audit_serialized_size(
            result
        )
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
    prefix_support = _typed_support_window(
        arm, prefix, trajectory, start=0
    )
    if not all((
        prefix_support["structural_exact"],
        prefix_support["causal_float_exact"],
        prefix_support["segment_exact"],
        prefix_support["derived_record_fidelity_passed"],
    )):
        raise RuntimeError(f"stochastic fork prefix mismatch {prefix_support}")
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

    natural_support = _typed_support_window(
        arm, branches[natural_action], trajectory, start=time
    )
    natural_outcome_mismatch = (
        branches[natural_action].outcomes[env_index]
        != trajectory.outcomes[env_index]
    )
    if natural_outcome_mismatch or not all((
        natural_support["structural_exact"],
        natural_support["causal_float_exact"],
        natural_support["segment_exact"],
        natural_support["derived_record_fidelity_passed"],
    )):
        raise RuntimeError(
            "stochastic fork natural branch continuation mismatch "
            f"{natural_support}"
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
            "prefix_support": prefix_support,
            "natural_branch_support": natural_support,
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
        "natural_support_evidence": natural_support,
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
    replay of a width-16 collection is not bitwise exact, and the residual
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
        prefix_support = _typed_support_window(
            arm, prefix, trajectory, start=0
        )
        if not all((
            prefix_support["structural_exact"],
            prefix_support["causal_float_exact"],
            prefix_support["segment_exact"],
            prefix_support["derived_record_fidelity_passed"],
        )):
            if diagnostics is not None:
                diagnostics["prefix_support"] = prefix_support
            raise RuntimeError(
                f"fork prefix reconstruction mismatch {prefix_support} at "
                f"(time={time}, env_index={env_index}, key={key})"
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
    natural_support = _typed_support_window(
        arm,
        branch_trajectories[natural_action],
        trajectory,
        start=time,
        excluded=(env_index, key),
    )
    natural_outcome_mismatch = (
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
                "prefix_support": prefix_support,
                "natural_branch_support": natural_support,
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
    if natural_outcome_mismatch or not all((
        natural_support["structural_exact"],
        natural_support["causal_float_exact"],
        natural_support["segment_exact"],
        natural_support["derived_record_fidelity_passed"],
    )):
        raise RuntimeError(
            f"fork natural branch continuation mismatch {natural_support} at "
            f"(time={time}, env_index={env_index}, key={key})"
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
        "natural_support_evidence": natural_support,
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


def _typed_support_window(
    arm: CommitmentArm,
    reconstruction: EventTrajectory,
    trajectory: EventTrajectory,
    *,
    start: int,
    excluded: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Typed non-evidence support check shared by both sequential oracles."""

    steps = int(reconstruction.time_steps)
    stop = start + steps

    def window(name: str) -> tuple[torch.Tensor, torch.Tensor]:
        natural = getattr(reconstruction, name)
        source = getattr(trajectory, name)[start:stop].to(natural.device)
        if excluded is not None and name in _AUDIT_EVENT_FIELDS:
            env_index, key = excluded
            natural, source = natural.clone(), source.clone()
            natural[0, env_index, key] = 0
            source[0, env_index, key] = 0
        return source, natural

    structural = [
        native_bitwise_finite_comparison(
            _tensor_payload(window(name)[0]),
            _tensor_payload(window(name)[1]),
            field=name,
        )
        for name in CAUSAL_STRUCTURAL_FIELDS
    ]
    causal = [
        native_bitwise_finite_comparison(
            _tensor_payload(window(name)[0]),
            _tensor_payload(window(name)[1]),
            field=name,
        )
        for name in CAUSAL_FLOAT_FIELDS
    ]
    segment_failures = _audit_segment_mismatches(
        reconstruction, trajectory, complete=stop >= int(trajectory.time_steps)
    )
    derived_replacements: dict[str, torch.Tensor] = {}
    for name in DERIVED_RECORD_FIELDS:
        source, natural = window(name)
        derived_replacements[name] = source
    expected = replace(reconstruction, **derived_replacements)
    replay = replay_trajectory(
        arm, reconstruction, device=reconstruction.rewards.device
    )
    derived_report = replay_report(replay, expected)
    critic, likelihood, joint = _validate_replay_report_evidence(
        derived_report,
        event_rows_required=bool(reconstruction.event_kind.ne(0).any()),
        categorical_rows_required=bool(
            reconstruction.event_cat_mask.any()
        ),
        mark_rows_required=bool(reconstruction.event_mark_mask.any()),
    )
    return {
        "structural_fields": structural,
        "causal_fields": causal,
        "segment_environments": list(segment_failures),
        "derived_report": derived_report,
        "structural_exact": all(row["passed"] for row in structural),
        "causal_float_exact": all(row["passed"] for row in causal),
        "segment_exact": not segment_failures,
        "derived_record_fidelity_passed": bool(
            critic and likelihood and joint
        ),
        "real_path_binding_claimed": False,
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
