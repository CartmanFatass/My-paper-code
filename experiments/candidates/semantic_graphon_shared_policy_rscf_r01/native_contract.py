"""Fail-closed TEST-only ABI contract for the RSCF full-suffix host.

This module contains no production coordinate generator and no scientific
identity.  The deterministic factories below are deliberately named TEST and
materialize synthetic arrays without an RNG or a seed.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
import hashlib
import math
from typing import Mapping

import numpy as np


ABI_VERSION = "SGSP_RSCF_NATIVE_ABI_V4_FP32"
HOST_KIND = "RIDGEGATE_2Z_RSCF_FACTUAL_TRACE_AND_FULL_SUFFIX_CPU_TEST_V4_FP32"
NATIVE_THREADS = 1
LANGUAGE_STANDARD = "C++17"
ALLOWED_ROSTERS = (6, 9, 15, 21)
ALLOWED_WIDTHS = (32, 64, 128, 256)
MAX_AGENTS = 21
HORIZON = 12
N_ROLES = 3
N_ACTIONS = 6
OBS_DIM = 22
MESSAGE_DIM = 32
HIDDEN_DIM = 64
ACTOR_INPUT_DIM = 55
FIFO_CAPACITY = 4
MAX_SCHEDULED = 32
METRIC_DIM = 8

ROLE_WEST = 0
ROLE_EAST = 1
ROLE_RELAY = 2

ACTION_SCAN = 0
ACTION_UPLINK = 1
ACTION_LISTEN_WEST = 2
ACTION_LISTEN_EAST = 3
ACTION_FORWARD_BASE = 4
ACTION_HOLD = 5

LEGAL_ACTIONS = {
    ROLE_WEST: (ACTION_SCAN, ACTION_UPLINK, ACTION_HOLD),
    ROLE_EAST: (ACTION_SCAN, ACTION_UPLINK, ACTION_HOLD),
    ROLE_RELAY: (
        ACTION_LISTEN_WEST,
        ACTION_LISTEN_EAST,
        ACTION_FORWARD_BASE,
        ACTION_HOLD,
    ),
}

SCHEDULE_UPLINK = 1
SCHEDULE_BASE = 2

METRIC_NEW_TIMELY = 0
METRIC_DUPLICATE_ARRIVALS = 1
METRIC_EXPIRED_ARRIVALS = 2
METRIC_COLLISION_LOSS = 3
METRIC_EMPTY_ACTIONS = 4
METRIC_RADIO_ACTIONS = 5
METRIC_WASTE_ACTIONS = 6
METRIC_DECODED_ARRIVALS = 7

MODE_INTACT = "INTACT"
MODE_FULL_ROTATED = "FULL_ROTATED"
ROTATED_PHYSICAL_SOURCE_COLUMN = (2, 0, 1)


def _readonly(array: np.ndarray) -> np.ndarray:
    array = np.ascontiguousarray(array)
    array.setflags(write=False)
    return array


def _synthetic_values(shape: tuple[int, ...], scale: float, phase: float) -> np.ndarray:
    count = math.prod(shape)
    index = np.arange(1, count + 1, dtype=np.float32)
    values = scale * (
        np.sin(index * 0.17320508075688773 + phase)
        + 0.5 * np.cos(index * 0.113 + 0.7 * phase)
    )
    return _readonly(values.reshape(shape))


@dataclass(frozen=True)
class ActorParameters:
    encoder_w1: np.ndarray
    encoder_b1: np.ndarray
    encoder_w2: np.ndarray
    encoder_b2: np.ndarray
    beta: np.ndarray
    gru_w: np.ndarray
    gru_u: np.ndarray
    gru_b: np.ndarray
    actor_w: np.ndarray
    actor_b: np.ndarray

    def as_native_dict(self) -> dict[str, np.ndarray]:
        validate_actor_parameters(self)
        return {field.name: getattr(self, field.name) for field in fields(self)}

    @property
    def digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(ABI_VERSION.encode("ascii"))
        for field in fields(self):
            value = getattr(self, field.name)
            digest.update(field.name.encode("ascii"))
            digest.update(str(value.shape).encode("ascii"))
            digest.update(value.dtype.str.encode("ascii"))
            digest.update(value.tobytes(order="C"))
        return digest.hexdigest()


@dataclass(frozen=True)
class SuffixBatch:
    n_agents: np.ndarray
    origin_slot: np.ndarray
    focal_agent: np.ndarray
    roles: np.ndarray
    fifo_basin: np.ndarray
    fifo_ordinal: np.ndarray
    fifo_birth: np.ndarray
    scheduled_count: np.ndarray
    scheduled_kind: np.ndarray
    scheduled_due: np.ndarray
    scheduled_sender: np.ndarray
    scheduled_receiver: np.ndarray
    scheduled_basin: np.ndarray
    scheduled_ordinal: np.ndarray
    scheduled_birth: np.ndarray
    delivered: np.ndarray
    metrics: np.ndarray
    previous_action: np.ndarray
    previous_success: np.ndarray
    event_schedule: np.ndarray
    post_gru_hidden: np.ndarray
    current_observations: np.ndarray
    current_messages: np.ndarray
    current_legal_probabilities: np.ndarray
    factual_joint_action: np.ndarray
    focal_intervention: np.ndarray
    factual_terminal: np.ndarray
    detection_uniform: np.ndarray
    uplink_uniform: np.ndarray
    base_uniform: np.ndarray
    action_uniform: np.ndarray

    @property
    def width(self) -> int:
        return int(self.n_agents.shape[0])

    def as_native_dict(self) -> dict[str, np.ndarray]:
        validate_suffix_batch(self)
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def replaced(self, **changes: np.ndarray) -> "SuffixBatch":
        frozen = {name: _readonly(np.asarray(value).copy()) for name, value in changes.items()}
        updated = replace(self, **frozen)
        validate_suffix_batch(updated)
        return updated


@dataclass(frozen=True)
class NativeSuffixResult:
    terminal_target: np.ndarray
    final_delivered: np.ndarray
    final_metrics: np.ndarray
    counters: np.ndarray
    common_tape_digest: np.ndarray
    audit_digest: np.ndarray
    factual_suffix_candidate: np.ndarray
    factual_suffix_identity: np.ndarray
    active: np.ndarray
    parameter_digest: str
    abi_version: str = ABI_VERSION


@dataclass(frozen=True)
class FactualEpisodeBatch:
    n_agents: np.ndarray
    roles: np.ndarray
    event_schedule: np.ndarray
    selector_slot: np.ndarray
    selector_local_index: np.ndarray
    detection_uniform: np.ndarray
    uplink_uniform: np.ndarray
    base_uniform: np.ndarray
    action_uniform: np.ndarray

    @property
    def width(self) -> int:
        return int(self.n_agents.shape[0])

    def as_native_dict(self) -> dict[str, np.ndarray]:
        validate_factual_episode_batch(self)
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True)
class FactualTrajectory:
    observations: np.ndarray
    messages: np.ndarray
    role_summaries: np.ndarray
    denominators: np.ndarray
    incoming_hidden: np.ndarray
    post_gru_hidden: np.ndarray
    legal_probabilities: np.ndarray
    factual_actions: np.ndarray
    fifo_basin: np.ndarray
    fifo_ordinal: np.ndarray
    fifo_birth: np.ndarray
    scheduled_count: np.ndarray
    delivered: np.ndarray
    metrics: np.ndarray
    previous_action: np.ndarray
    previous_success: np.ndarray
    snapshot_digest: np.ndarray
    origin_slot: np.ndarray
    origin_agent: np.ndarray
    origin_snapshot_digest: np.ndarray
    terminal_return: np.ndarray
    final_delivered: np.ndarray
    final_metrics: np.ndarray
    common_tape_digest: np.ndarray
    trajectory_digest: np.ndarray
    active: np.ndarray
    parameter_digest: str
    mode: str
    abi_version: str = ABI_VERSION


@dataclass(frozen=True)
class ShadowTrajectory:
    role_summaries: np.ndarray
    denominators: np.ndarray
    post_gru_hidden: np.ndarray
    legal_probabilities: np.ndarray
    snapshot_digest: np.ndarray
    active: np.ndarray
    parameter_digest: str
    abi_version: str = ABI_VERSION


_ACTOR_SHAPES = {
    "encoder_w1": (64, 22),
    "encoder_b1": (64,),
    "encoder_w2": (32, 64),
    "encoder_b2": (32,),
    "beta": (3, 3, 2),
    "gru_w": (3, 64, 55),
    "gru_u": (3, 64, 64),
    "gru_b": (3, 64),
    "actor_w": (6, 64),
    "actor_b": (6,),
}


def _require_array(
    name: str,
    value: np.ndarray,
    dtype: np.dtype,
    shape: tuple[int, ...],
    *,
    readonly: bool = True,
) -> None:
    if not isinstance(value, np.ndarray):
        raise TypeError(f"{name} must be a numpy.ndarray")
    if value.dtype != np.dtype(dtype):
        raise TypeError(f"{name} dtype must be {np.dtype(dtype)}, got {value.dtype}")
    if value.shape != shape:
        raise ValueError(f"{name} shape must be {shape}, got {value.shape}")
    if not value.flags.c_contiguous:
        raise ValueError(f"{name} must be C-contiguous")
    if readonly and value.flags.writeable:
        raise ValueError(f"{name} must be immutable/read-only")


def validate_actor_parameters(parameters: ActorParameters) -> None:
    for name, shape in _ACTOR_SHAPES.items():
        value = getattr(parameters, name)
        _require_array(name, value, np.float32, shape)
        if not np.isfinite(value).all():
            raise ValueError(f"{name} contains a nonfinite value")


def _batch_shapes(width: int) -> Mapping[str, tuple[np.dtype, tuple[int, ...]]]:
    return {
        "n_agents": (np.dtype(np.int64), (width,)),
        "origin_slot": (np.dtype(np.int64), (width,)),
        "focal_agent": (np.dtype(np.int64), (width,)),
        "roles": (np.dtype(np.int64), (width, MAX_AGENTS)),
        "fifo_basin": (np.dtype(np.int64), (width, MAX_AGENTS, FIFO_CAPACITY)),
        "fifo_ordinal": (np.dtype(np.int64), (width, MAX_AGENTS, FIFO_CAPACITY)),
        "fifo_birth": (np.dtype(np.int64), (width, MAX_AGENTS, FIFO_CAPACITY)),
        "scheduled_count": (np.dtype(np.int64), (width,)),
        "scheduled_kind": (np.dtype(np.int64), (width, MAX_SCHEDULED)),
        "scheduled_due": (np.dtype(np.int64), (width, MAX_SCHEDULED)),
        "scheduled_sender": (np.dtype(np.int64), (width, MAX_SCHEDULED)),
        "scheduled_receiver": (np.dtype(np.int64), (width, MAX_SCHEDULED)),
        "scheduled_basin": (np.dtype(np.int64), (width, MAX_SCHEDULED)),
        "scheduled_ordinal": (np.dtype(np.int64), (width, MAX_SCHEDULED)),
        "scheduled_birth": (np.dtype(np.int64), (width, MAX_SCHEDULED)),
        "delivered": (np.dtype(np.int64), (width, 2, 3)),
        "metrics": (np.dtype(np.int64), (width, METRIC_DIM)),
        "previous_action": (np.dtype(np.int64), (width, MAX_AGENTS)),
        "previous_success": (np.dtype(np.int64), (width, MAX_AGENTS)),
        "event_schedule": (np.dtype(np.int64), (width, 2, 3)),
        "post_gru_hidden": (np.dtype(np.float32), (width, MAX_AGENTS, HIDDEN_DIM)),
        "current_observations": (np.dtype(np.float32), (width, MAX_AGENTS, OBS_DIM)),
        "current_messages": (np.dtype(np.float32), (width, MAX_AGENTS, MESSAGE_DIM)),
        "current_legal_probabilities": (np.dtype(np.float32), (width, MAX_AGENTS, N_ACTIONS)),
        "factual_joint_action": (np.dtype(np.int64), (width, MAX_AGENTS)),
        "focal_intervention": (np.dtype(np.int64), (width,)),
        "factual_terminal": (np.dtype(np.float32), (width,)),
        "detection_uniform": (np.dtype(np.float32), (width, HORIZON, MAX_AGENTS)),
        "uplink_uniform": (
            np.dtype(np.float32),
            (width, HORIZON, MAX_AGENTS, MAX_AGENTS),
        ),
        "base_uniform": (np.dtype(np.float32), (width, HORIZON, MAX_AGENTS)),
        "action_uniform": (np.dtype(np.float32), (width, HORIZON, MAX_AGENTS)),
    }


def validate_suffix_batch(batch: SuffixBatch) -> None:
    width = batch.width
    if width not in ALLOWED_WIDTHS:
        raise ValueError(f"batch width must be one of {ALLOWED_WIDTHS}, got {width}")
    for name, (dtype, shape) in _batch_shapes(width).items():
        value = getattr(batch, name)
        _require_array(name, value, dtype, shape)
        if dtype == np.dtype(np.float32) and not np.isfinite(value).all():
            raise ValueError(f"{name} contains a nonfinite value")

    for lane, n_agents in enumerate(batch.n_agents.tolist()):
        if n_agents == 0:
            continue
        if n_agents not in ALLOWED_ROSTERS:
            raise ValueError(f"lane {lane}: unsupported roster {n_agents}")
        slot = int(batch.origin_slot[lane])
        focal = int(batch.focal_agent[lane])
        if not 0 <= slot < HORIZON:
            raise ValueError(f"lane {lane}: origin_slot outside [0,11]")
        if not 0 <= focal < n_agents:
            raise ValueError(f"lane {lane}: focal_agent outside active roster")
        active_roles = batch.roles[lane, :n_agents]
        counts = tuple(int(np.count_nonzero(active_roles == role)) for role in range(N_ROLES))
        if counts != (n_agents // 3,) * 3:
            raise ValueError(f"lane {lane}: roles are not balanced: {counts}")
        if np.any((active_roles < 0) | (active_roles >= N_ROLES)):
            raise ValueError(f"lane {lane}: invalid role")
        count = int(batch.scheduled_count[lane])
        if not 0 <= count <= MAX_SCHEDULED:
            raise ValueError(f"lane {lane}: scheduled_count outside capacity")
        if count != 0:
            raise ValueError(
                f"lane {lane}: a documented pretransition origin has already processed "
                "all latency-one arrivals; scheduled_count must therefore be zero"
            )
        if np.any((batch.delivered[lane] < 0) | (batch.delivered[lane] > 1)):
            raise ValueError(f"lane {lane}: delivered identities must be binary")
        if np.any(batch.metrics[lane] < 0):
            raise ValueError(f"lane {lane}: metrics must be nonnegative")
        if batch.metrics[lane, METRIC_WASTE_ACTIONS] > batch.metrics[lane, METRIC_RADIO_ACTIONS]:
            raise ValueError(f"lane {lane}: waste count exceeds radio-action count")
        if batch.metrics[lane, METRIC_NEW_TIMELY] != int(batch.delivered[lane].sum()):
            raise ValueError(f"lane {lane}: new-timely metric disagrees with delivered identities")
        for agent in range(n_agents):
            role = int(batch.roles[lane, agent])
            action = int(batch.factual_joint_action[lane, agent])
            if action not in LEGAL_ACTIONS[role]:
                raise ValueError(f"lane {lane}: illegal factual action for agent {agent}")
            probs = batch.current_legal_probabilities[lane, agent]
            legal = LEGAL_ACTIONS[role]
            if np.any(probs < 0.0) or abs(float(probs.sum(dtype=np.float32)) - 1.0) > 1.0e-5:
                raise ValueError(f"lane {lane}: invalid current legal distribution")
            illegal = tuple(action_index for action_index in range(N_ACTIONS) if action_index not in legal)
            if any(probs[action_index] != 0.0 for action_index in illegal):
                raise ValueError(f"lane {lane}: illegal action has nonzero probability")
            if any(probs[action_index] < 0.04 / len(legal) for action_index in legal):
                raise ValueError(f"lane {lane}: legal probability violates the 0.04 floor")
            previous = int(batch.previous_action[lane, agent])
            if slot == 0:
                if previous != -1:
                    raise ValueError(f"lane {lane}: slot-zero previous action must be absent")
            elif previous not in legal:
                raise ValueError(f"lane {lane}: invalid previous action for agent {agent}")
            if int(batch.previous_success[lane, agent]) not in (0, 1):
                raise ValueError(f"lane {lane}: previous success must be binary")
            capacity = 4 if role == ROLE_RELAY else 2
            seen_empty = False
            for position in range(FIFO_CAPACITY):
                packet = (
                    int(batch.fifo_basin[lane, agent, position]),
                    int(batch.fifo_ordinal[lane, agent, position]),
                    int(batch.fifo_birth[lane, agent, position]),
                )
                if packet == (-1, -1, -1):
                    seen_empty = True
                    continue
                if position >= capacity or seen_empty:
                    raise ValueError(f"lane {lane}: FIFO is not compact within role capacity")
                basin, ordinal, birth = packet
                if basin not in (0, 1) or not 0 <= ordinal < 3:
                    raise ValueError(f"lane {lane}: invalid FIFO packet identity")
                if role != ROLE_RELAY and basin != role:
                    raise ValueError(f"lane {lane}: surveyor FIFO basin mismatches its role")
                if int(batch.event_schedule[lane, basin, ordinal]) != birth:
                    raise ValueError(f"lane {lane}: FIFO birth disagrees with event schedule")
                if not 0 <= slot - birth <= 3:
                    raise ValueError(f"lane {lane}: pretransition FIFO contains future/expired packet")
        focal_role = int(batch.roles[lane, focal])
        if int(batch.focal_intervention[lane]) not in LEGAL_ACTIONS[focal_role]:
            raise ValueError(f"lane {lane}: illegal focal intervention")
        events = batch.event_schedule[lane]
        for basin in range(2):
            row = events[basin]
            if len(set(int(value) for value in row)) != 3 or np.any((row < 0) | (row > 7)):
                raise ValueError(f"lane {lane}: invalid event schedule")
        for field_name in ("detection_uniform", "uplink_uniform", "base_uniform", "action_uniform"):
            values = getattr(batch, field_name)[lane]
            if np.any((values < 0.0) | (values >= 1.0)):
                raise ValueError(f"lane {lane}: {field_name} must lie in [0,1)")


def _episode_shapes(width: int) -> Mapping[str, tuple[np.dtype, tuple[int, ...]]]:
    return {
        "n_agents": (np.dtype(np.int64), (width,)),
        "roles": (np.dtype(np.int64), (width, MAX_AGENTS)),
        "event_schedule": (np.dtype(np.int64), (width, 2, 3)),
        "selector_slot": (np.dtype(np.int64), (width, N_ROLES)),
        "selector_local_index": (np.dtype(np.int64), (width, N_ROLES)),
        "detection_uniform": (np.dtype(np.float32), (width, HORIZON, MAX_AGENTS)),
        "uplink_uniform": (
            np.dtype(np.float32),
            (width, HORIZON, MAX_AGENTS, MAX_AGENTS),
        ),
        "base_uniform": (np.dtype(np.float32), (width, HORIZON, MAX_AGENTS)),
        "action_uniform": (np.dtype(np.float32), (width, HORIZON, MAX_AGENTS)),
    }


def validate_factual_episode_batch(batch: FactualEpisodeBatch) -> None:
    width = batch.width
    if width not in ALLOWED_WIDTHS:
        raise ValueError(f"episode width must be one of {ALLOWED_WIDTHS}")
    for name, (dtype, shape) in _episode_shapes(width).items():
        value = getattr(batch, name)
        _require_array(name, value, dtype, shape)
        if dtype == np.dtype(np.float32) and not np.isfinite(value).all():
            raise ValueError(f"{name} contains a nonfinite value")
    for lane, n_agents in enumerate(batch.n_agents.tolist()):
        if n_agents == 0:
            continue
        if n_agents not in ALLOWED_ROSTERS:
            raise ValueError(f"lane {lane}: unsupported roster {n_agents}")
        active_roles = batch.roles[lane, :n_agents]
        counts = tuple(int(np.count_nonzero(active_roles == role)) for role in range(N_ROLES))
        if counts != (n_agents // 3,) * 3:
            raise ValueError(f"lane {lane}: roles are not balanced")
        for basin in range(2):
            row = batch.event_schedule[lane, basin]
            if len(set(int(value) for value in row)) != 3 or np.any((row < 0) | (row > 7)):
                raise ValueError(f"lane {lane}: invalid event schedule")
        for role in range(N_ROLES):
            slot = int(batch.selector_slot[lane, role])
            local = int(batch.selector_local_index[lane, role])
            if not 0 <= slot < HORIZON or not 0 <= local < n_agents // 3:
                raise ValueError(f"lane {lane}: invalid TEST selector origin")
        for field_name in (
            "detection_uniform",
            "uplink_uniform",
            "base_uniform",
            "action_uniform",
        ):
            values = getattr(batch, field_name)[lane]
            if np.any((values < 0.0) | (values >= 1.0)):
                raise ValueError(f"lane {lane}: {field_name} must lie in [0,1)")


def make_test_factual_episode_batch(
    width: int, active_lanes: int | None = None
) -> FactualEpisodeBatch:
    """Materialize reset episodes using literal TEST tapes and selectors."""

    if width not in ALLOWED_WIDTHS:
        raise ValueError(f"width must be one of {ALLOWED_WIDTHS}")
    active = width if active_lanes is None else int(active_lanes)
    if not 0 <= active <= width:
        raise ValueError("active_lanes must lie in [0,width]")
    n_agents = np.zeros(width, dtype=np.int64)
    roles = np.full((width, MAX_AGENTS), -1, dtype=np.int64)
    event_schedule = np.zeros((width, 2, 3), dtype=np.int64)
    selector_slot = np.zeros((width, N_ROLES), dtype=np.int64)
    selector_local_index = np.zeros((width, N_ROLES), dtype=np.int64)
    detection_uniform = np.zeros((width, HORIZON, MAX_AGENTS), dtype=np.float32)
    uplink_uniform = np.zeros(
        (width, HORIZON, MAX_AGENTS, MAX_AGENTS), dtype=np.float32
    )
    base_uniform = np.zeros((width, HORIZON, MAX_AGENTS), dtype=np.float32)
    action_uniform = np.zeros((width, HORIZON, MAX_AGENTS), dtype=np.float32)
    tape_values = np.asarray((0.10, 0.34, 0.63, 0.89), dtype=np.float32)
    action_values = np.asarray((0.11, 0.30, 0.49, 0.68, 0.87), dtype=np.float32)
    for lane in range(active):
        roster = ALLOWED_ROSTERS[lane % len(ALLOWED_ROSTERS)]
        per_role = roster // 3
        n_agents[lane] = roster
        roles[lane, :roster] = _role_layout(roster)
        event_schedule[lane, 0] = _event_times(lane, 0)
        event_schedule[lane, 1] = _event_times(lane, 1)
        for role in range(N_ROLES):
            selector_slot[lane, role] = (5 * lane + 3 * role + 2) % HORIZON
            selector_local_index[lane, role] = (lane + role) % per_role
        for slot in range(HORIZON):
            for sender in range(roster):
                detection_uniform[lane, slot, sender] = tape_values[
                    (lane + slot + sender) % 4
                ]
                base_uniform[lane, slot, sender] = tape_values[
                    (lane + 2 * slot + sender + 1) % 4
                ]
                action_uniform[lane, slot, sender] = action_values[
                    (lane + slot + 2 * sender) % len(action_values)
                ]
                for receiver in range(roster):
                    uplink_uniform[lane, slot, sender, receiver] = tape_values[
                        (lane + slot + sender + 2 * receiver) % 4
                    ]
    batch = FactualEpisodeBatch(
        **{
            name: _readonly(value)
            for name, value in locals().items()
            if name in _episode_shapes(width)
        }
    )
    validate_factual_episode_batch(batch)
    return batch


def make_test_actor_parameters() -> ActorParameters:
    """Return immutable synthetic TEST parameters, never a model initialization."""

    parameters = ActorParameters(
        encoder_w1=_synthetic_values((64, 22), 0.018, 0.1),
        encoder_b1=_synthetic_values((64,), 0.006, 0.2),
        encoder_w2=_synthetic_values((32, 64), 0.016, 0.3),
        encoder_b2=_synthetic_values((32,), 0.005, 0.4),
        beta=_synthetic_values((3, 3, 2), 0.07, 0.5),
        gru_w=_synthetic_values((3, 64, 55), 0.012, 0.6),
        gru_u=_synthetic_values((3, 64, 64), 0.011, 0.7),
        gru_b=_synthetic_values((3, 64), 0.004, 0.8),
        actor_w=_synthetic_values((6, 64), 0.014, 0.9),
        actor_b=_synthetic_values((6,), 0.004, 1.0),
    )
    validate_actor_parameters(parameters)
    return parameters


def _role_layout(n_agents: int) -> np.ndarray:
    per_role = n_agents // 3
    return np.repeat(np.arange(3, dtype=np.int64), per_role)


def _event_times(lane: int, basin: int) -> tuple[int, int, int]:
    # Three distinct literal TEST slots, without an RNG or seed identity.
    tables = (
        (0, 3, 6),
        (1, 4, 7),
        (0, 4, 7),
        (1, 3, 6),
        (2, 5, 7),
        (0, 2, 5),
    )
    return tables[(lane + 2 * basin) % len(tables)]


def suffix_batch_from_factual_trajectory(
    episode: FactualEpisodeBatch,
    trajectory: FactualTrajectory,
    selected_role: np.ndarray | None = None,
    alternative_offset: int = 1,
) -> SuffixBatch:
    """Bind each suffix lane to one exact snapshot in its factual trajectory."""

    validate_factual_episode_batch(episode)
    width = episode.width
    roles_to_use = (
        np.arange(width, dtype=np.int64) % N_ROLES
        if selected_role is None
        else np.asarray(selected_role, dtype=np.int64)
    )
    if roles_to_use.shape != (width,) or np.any((roles_to_use < 0) | (roles_to_use >= 3)):
        raise ValueError("selected_role must be a width-vector in {0,1,2}")
    n_agents = episode.n_agents.copy()
    origin_slot = np.zeros(width, dtype=np.int64)
    focal_agent = np.zeros(width, dtype=np.int64)
    fifo_basin = np.full((width, MAX_AGENTS, FIFO_CAPACITY), -1, dtype=np.int64)
    fifo_ordinal = np.full_like(fifo_basin, -1)
    fifo_birth = np.full_like(fifo_basin, -1)
    delivered = np.zeros((width, 2, 3), dtype=np.int64)
    metrics = np.zeros((width, METRIC_DIM), dtype=np.int64)
    previous_action = np.full((width, MAX_AGENTS), -1, dtype=np.int64)
    previous_success = np.zeros((width, MAX_AGENTS), dtype=np.int64)
    post_gru_hidden = np.zeros((width, MAX_AGENTS, HIDDEN_DIM), dtype=np.float32)
    current_observations = np.zeros((width, MAX_AGENTS, OBS_DIM), dtype=np.float32)
    current_messages = np.zeros((width, MAX_AGENTS, MESSAGE_DIM), dtype=np.float32)
    current_legal_probabilities = np.zeros(
        (width, MAX_AGENTS, N_ACTIONS), dtype=np.float32
    )
    factual_joint_action = np.full((width, MAX_AGENTS), -1, dtype=np.int64)
    focal_intervention = np.full(width, -1, dtype=np.int64)
    for lane in range(width):
        n = int(n_agents[lane])
        if n == 0:
            continue
        role = int(roles_to_use[lane])
        slot = int(trajectory.origin_slot[lane, role])
        focal = int(trajectory.origin_agent[lane, role])
        if trajectory.origin_snapshot_digest[lane, role] != trajectory.snapshot_digest[lane, slot]:
            raise ValueError("selector origin does not bind to its exact factual snapshot")
        origin_slot[lane] = slot
        focal_agent[lane] = focal
        fifo_basin[lane] = trajectory.fifo_basin[lane, slot]
        fifo_ordinal[lane] = trajectory.fifo_ordinal[lane, slot]
        fifo_birth[lane] = trajectory.fifo_birth[lane, slot]
        delivered[lane] = trajectory.delivered[lane, slot]
        metrics[lane] = trajectory.metrics[lane, slot]
        previous_action[lane] = trajectory.previous_action[lane, slot]
        previous_success[lane] = trajectory.previous_success[lane, slot]
        post_gru_hidden[lane] = trajectory.post_gru_hidden[lane, slot]
        current_observations[lane] = trajectory.observations[lane, slot]
        current_messages[lane] = trajectory.messages[lane, slot]
        current_legal_probabilities[lane] = trajectory.legal_probabilities[lane, slot]
        factual_joint_action[lane] = trajectory.factual_actions[lane, slot]
        legal = LEGAL_ACTIONS[int(episode.roles[lane, focal])]
        factual = int(factual_joint_action[lane, focal])
        focal_intervention[lane] = legal[
            (legal.index(factual) + alternative_offset) % len(legal)
        ]
    scheduled_count = np.zeros(width, dtype=np.int64)
    scheduled_kind = np.zeros((width, MAX_SCHEDULED), dtype=np.int64)
    scheduled_due = np.full((width, MAX_SCHEDULED), -1, dtype=np.int64)
    scheduled_sender = np.full_like(scheduled_due, -1)
    scheduled_receiver = np.full_like(scheduled_due, -1)
    scheduled_basin = np.full_like(scheduled_due, -1)
    scheduled_ordinal = np.full_like(scheduled_due, -1)
    scheduled_birth = np.full_like(scheduled_due, -1)
    batch = SuffixBatch(
        n_agents=_readonly(n_agents),
        origin_slot=_readonly(origin_slot),
        focal_agent=_readonly(focal_agent),
        roles=episode.roles,
        fifo_basin=_readonly(fifo_basin),
        fifo_ordinal=_readonly(fifo_ordinal),
        fifo_birth=_readonly(fifo_birth),
        scheduled_count=_readonly(scheduled_count),
        scheduled_kind=_readonly(scheduled_kind),
        scheduled_due=_readonly(scheduled_due),
        scheduled_sender=_readonly(scheduled_sender),
        scheduled_receiver=_readonly(scheduled_receiver),
        scheduled_basin=_readonly(scheduled_basin),
        scheduled_ordinal=_readonly(scheduled_ordinal),
        scheduled_birth=_readonly(scheduled_birth),
        delivered=_readonly(delivered),
        metrics=_readonly(metrics),
        previous_action=_readonly(previous_action),
        previous_success=_readonly(previous_success),
        event_schedule=episode.event_schedule,
        post_gru_hidden=_readonly(post_gru_hidden),
        current_observations=_readonly(current_observations),
        current_messages=_readonly(current_messages),
        current_legal_probabilities=_readonly(current_legal_probabilities),
        factual_joint_action=_readonly(factual_joint_action),
        focal_intervention=_readonly(focal_intervention),
        factual_terminal=_readonly(trajectory.terminal_return.copy()),
        detection_uniform=episode.detection_uniform,
        uplink_uniform=episode.uplink_uniform,
        base_uniform=episode.base_uniform,
        action_uniform=episode.action_uniform,
    )
    validate_suffix_batch(batch)
    return batch


def with_factual_actions(batch: SuffixBatch) -> SuffixBatch:
    interventions = np.asarray(
        [
            batch.factual_joint_action[lane, batch.focal_agent[lane]]
            if batch.n_agents[lane] > 0
            else -1
            for lane in range(batch.width)
        ],
        dtype=np.int64,
    )
    return batch.replaced(focal_intervention=interventions)


def with_factual_terminal(batch: SuffixBatch, terminal: np.ndarray) -> SuffixBatch:
    terminal_array = np.asarray(terminal, dtype=np.float32)
    if terminal_array.shape != (batch.width,) or not np.isfinite(terminal_array).all():
        raise ValueError("terminal must be a finite width-vector")
    return batch.replaced(factual_terminal=terminal_array)


def make_test_suffix_batch(width: int, active_lanes: int | None = None) -> SuffixBatch:
    """Build TEST suffixes only from exact slots of one completed factual trace."""

    episode = make_test_factual_episode_batch(width, active_lanes=active_lanes)
    parameters = make_test_actor_parameters()
    from .native_loader import native_factual_trajectory

    trajectory = native_factual_trajectory(episode, parameters, mode=MODE_INTACT)
    return suffix_batch_from_factual_trajectory(episode, trajectory)
