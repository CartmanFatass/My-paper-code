"""Unchanged noncalendar G0 ledger/environment and EHC result contract."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

import numpy as np
import torch
from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    HORIZON,
    MAX_LIFECYCLES,
    OBSERVATION_DIM,
)
from ha_ctse_process.variable_roster_event import (
    JOIN,
    MembershipDelta,
    REJOIN,
    TEMPORARY_LEAVE,
    TERMINAL_LEAVE,
)


Profile = Literal["train", "iid", "held_out"]

THRUST_BY_ACTION = np.asarray((-1, 0, 1), dtype=np.int64)
STATE_MIN = -2
STATE_MAX = 2
TARGET_STREAK = 2
SHARED_RENEWAL_PERIOD = 4

COMMON_FIELD_COUNT = 8
PARAMETER_COUNT = 14_980
ADDED_PARAMETER_COUNT = 1_608

MODEL_INITIALIZATION_SEED = 58_058
TRAIN_TASK_SEED = 68_058
TRAIN_ORDER_SEED = 78_058
TRAIN_ACTION_SEED = 88_058
OPPORTUNITY_SEED = 90_058
EVENT_SEED = 92_058
MARK_SEED = 94_058
IID_EVAL_TASK_SEED = 98_058
HELD_OUT_EVAL_TASK_SEED = 99_058
BOOTSTRAP_SEED = 108_058

FORMAL_NUM_ENVS = 16
FORMAL_UPDATES = 250
FORMAL_TRAIN_EPISODES = 4_000
FORMAL_TRANSITIONS_PER_ARM = 320_000
FORMAL_OPTIMIZER_STEPS_PER_ARM = 1_000
FORMAL_EVAL_EPISODES = 256
BOOTSTRAP_REPETITIONS = 10_000

TRAIN_DURATION_SUPPORT = (5, 9, 13)
HELD_OUT_DURATION_SUPPORT = (5, 7, 9)

NOT_JOINED = "not_joined"
ACTIVE = "active"
TEMPORARILY_ABSENT = "temporarily_absent"
TERMINAL = "terminal"

CHECKPOINT_SCHEMA_VERSION = 7
CHECKPOINT_KIND = "event_held_commitment_link_g0"
REGISTERED_CONTRACT = "EVENT_HELD_COMMITMENT_LINK_G0"
ACCESS_FLOOR = 0.78
GAIN_THRESHOLD = 0.10
LIFETIME_BIN_THRESHOLD = 0.10
INTERVENTION_THRESHOLD = 0.10
IDENTIFIABILITY_OPPORTUNITIES = 1_000
IDENTIFIABILITY_LIFECYCLES = 250
SUPPORT_FLOOR = 128
# Replacement C -- natural event-decision consequence. Both directions are
# gated, and both are required: a one-sided pass is not sufficient and is not
# expressible, because `select_result_branch` conjoins them and takes both as
# required arguments. `LCB_95 > 0` is the interval gate; the point-estimate
# floors are frozen here so they cannot be tuned after a result is seen.
A_KEEP_LCB_FLOOR = 0.0
A_RENEW_LCB_FLOOR = 0.0
A_KEEP_MEAN_FLOOR = 0.02
A_RENEW_MEAN_FLOOR = 0.02
# The sole registered form of the fork budget. Full per-opportunity forking is
# not the default. A replicate that cannot supply the quota for either natural
# action makes the run non-identifiable; the quota is never lowered and rows are
# never pooled across replicates to reach it, which is why
# `select_result_branch` takes per-replicate counts and no pooled total.
NATURAL_FORK_ACTIONS = ("KEEP", "RENEW")
NATURAL_FORK_QUOTA_PER_ACTION = 32
NATURAL_FORK_REPLICATES = 5
NATURAL_FORK_PAIRS = (
    NATURAL_FORK_QUOTA_PER_ACTION * len(NATURAL_FORK_ACTIONS) * NATURAL_FORK_REPLICATES
)
# Dedicated deterministic selection stream. It is derived from the registered
# bootstrap seed under its own namespace coordinate, so it is distinct from the
# bootstrap resample stream (`default_rng(BOOTSTRAP_SEED)`, i.e.
# `SeedSequence(BOOTSTRAP_SEED)` with no coordinate) and from every owned
# collector and fork stream (all seeded from `seed_map`, never from the
# bootstrap seed). Registering the namespace fixes the stream identity before
# any selection code exists.
NATURAL_FORK_SELECTION_NAMESPACE = "natural_fork_selection"
NATURAL_FORK_SELECTION_COORDINATE = 1
# Registered execution backends. CPU is admitted as a first-class backend
# because this workload is kernel-launch bound (14,980 parameters, batch 16,
# ~480 sequential tiny calls per epoch): a full three-arm update measures 6.16s
# on single-thread CPU against 20.10s on CUDA, and CPU scales to 5.94x across 15
# concurrent workers where one card saturates near 2.0x. Admitting CPU is not a
# fallback: an unavailable requested backend raises rather than substituting
# another.
REGISTERED_EXECUTION_BACKENDS = ("cuda", "cpu")
# The backend the formal run is registered on, and therefore the backend the
# focused suite exercises. Both entries of `REGISTERED_EXECUTION_BACKENDS` are
# admitted, but one run uses exactly one of them.
FORMAL_EXECUTION_BACKEND = "cuda"
# One thread configuration for the whole run. Single-thread is measured faster
# than 14 threads on collection (0.419s against 0.629s) because the tensors are
# too small for thread synchronization to pay for itself, and pinning it makes
# the recorded thread count a registered constant rather than a machine
# property, so a checkpoint stays loadable on another host with a different
# core count.
REGISTERED_TORCH_THREADS = 1
GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
PRIMITIVE_ENTROPY_COEFFICIENT = 0.01
EVENT_ENTROPY_COEFFICIENT = 0.01
MARK_ENTROPY_COEFFICIENT = 0.0
GRADIENT_CLIP = 0.50
LEARNING_RATE = 3e-4
ADAM_EPSILON = 1e-5
WEIGHT_DECAY = 0.0
PPO_PASSES = 4
RNG_BINDING_SCHEMA_VERSION = 2
OPTIMIZER_EVIDENCE_SCHEMA_VERSION = 2
# ``clip_grad_norm_`` derives its multiplier as max_norm/(norm + 1e-6),
# clamped to one.  The evidence validator repeats that arithmetic and admits
# only float serialization rounding at this fixed comparison.
OPTIMIZER_NORM_ATOL = 1e-6
OPTIMIZER_NORM_RTOL = 1e-6
OPTIMIZER_CLIP_EPSILON = 1e-6
OPTIMIZER_LOSS_ATOL = 1e-7
OPTIMIZER_LOSS_RTOL = 1e-7
# Replay portability contract. One scalar cannot bound both a single
# continuous quantity and a sum of nine of them: a derived joint accumulates
# its summands' errors, so it needs the summands' allowance plus the float32
# reduction error of the sum itself. Four classes, not one number.
REPLAY_LOG_COMPONENT_ATOL = 1e-6
REPLAY_LOG_COMPONENT_RTOL = 8.0 * 2.0**-24
REPLAY_LOG_RATIO_DRIFT_CAP = 1e-4
REPLAY_STATE_ATOL = 1e-6
REPLAY_RECORD_SCHEMA_VERSION = 3
FLOAT32_UNIT_ROUNDOFF = 2.0**-24
# Categorical factor plus the eight transformed-mark components. Fixed at 9
# for every event row: factors outside a row's support are exactly zero and
# so contribute nothing to either the sum or its magnitude bound.
EVENT_JOINT_FACTOR_COUNT = 9
# Compared for exact equality; any non-zero value is a defect, never drift.
# `categorical_support_leak`/`mark_support_leak` close the one blind spot the
# masked component checks structurally cannot see. `categorical_component` is
# read only inside `event_cat_mask` and `mark_component` only inside
# `event_mark_mask`, so a factor recorded non-zero *outside* its own support is
# invisible to both, and if the stored joint is reassembled to include it the
# joint's own bound widens by exactly the corruption (the joint rule reduces to
# the triangle inequality once the assembly checks hold, so it can never fire
# first). The collector zeroes every factor outside its support before storing
# it, so both quantities are exactly zero by construction on clean data and any
# non-zero value is a support leak, never drift.
REPLAY_EXACT_FIELDS = (
    "mask_mismatch",
    "kind_support_mismatch",
    "event_action_mismatch",
    "detach_mismatch",
    "categorical_support_leak",
    "mark_support_leak",
)
# Actual likelihood factors use the mixed absolute-relative and ratio gates.
REPLAY_LOG_COMPONENT_FIELDS = (
    "primitive_component",
    "categorical_component",
    "mark_component",
)
# Ordinary continuous state remains absolute-only.
REPLAY_STATE_FIELDS = (
    "value",
    "hidden",
    "prefix",
    "event_input",
    "event_new_z",
    "primitive_event_z",
)
REPLAY_COMPONENT_FIELDS = REPLAY_LOG_COMPONENT_FIELDS + REPLAY_STATE_FIELDS
# Derived sums, gated by their own compositional bound.
REPLAY_JOINT_FIELDS = ("primitive_joint", "event_joint")
# The complete per-joint record. A serialized joint reduced to the three keys
# a validator happens to read would otherwise pass while carrying no evidence,
# so the full set is required rather than a readable subset.
REPLAY_JOINT_RECORD_FIELDS = (
    "error",
    "component_sum",
    "allowance",
    "bound",
    "excess",
    "factor_count",
    "float64_error",
    "assembly_residual",
    "assembly_allowance",
    "assembly_excess",
    "rows",
)
REPLAY_WORST_RECORD_FIELDS = (
    "stored_value",
    "replayed_value",
    "absolute_error",
    "mixed_bound",
    "ratio_drift",
    "ratio_cap",
    "float32_ulp_at_max_magnitude",
    "ulp_distance",
    "coordinate",
)
REPLAY_EVENT_JOINT_RATIO_FIELDS = (
    "stored_value",
    "replayed_value",
    "ratio_drift",
    "ratio_cap",
    "coordinate",
)
# Same-checkpoint continuation, a different invariant from replay
# portability, and deliberately unchanged by the replay-bound correction.
RESUME_TOLERANCE = 1e-7
OPPORTUNITY_SUPPORT = (4, 8, 12)


_ACTIVE_EXECUTION_BACKEND: str | None = None


def require_registered_backend(device_name: str) -> "torch.device":
    """Activate one registered execution backend for this process.

    Replaces the retired CUDA-only gate. `cuda` and `cpu` are both registered
    backends; anything else, and any registered backend that is not actually
    available, raises. Nothing is ever substituted -- an unavailable CUDA
    request does not become a CPU run.

    Activation is what makes the same-backend constraint structural rather
    than documented. It pins the intra-op thread count to
    `REGISTERED_TORCH_THREADS` and records the backend process-wide, and
    `registered_contract()` reads that record. The contract is embedded in
    every checkpoint and `load_checkpoint` rejects on contract inequality, so
    a checkpoint written under one backend or thread configuration cannot be
    loaded or continued under another. A second activation naming a different
    backend raises, so one process cannot straddle two backends and let a
    device-dependent optimization trajectory become an arm or replicate
    confound.
    """

    global _ACTIVE_EXECUTION_BACKEND
    if device_name not in REGISTERED_EXECUTION_BACKENDS:
        raise ValueError(
            f"{device_name!r} is not a registered execution backend; "
            f"registered backends are {list(REGISTERED_EXECUTION_BACKENDS)}"
        )
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "the requested cuda backend is unavailable; substituting another "
            "backend is forbidden"
        )
    if (
        _ACTIVE_EXECUTION_BACKEND is not None
        and _ACTIVE_EXECUTION_BACKEND != device_name
    ):
        raise RuntimeError(
            f"execution backend {_ACTIVE_EXECUTION_BACKEND!r} is already active; "
            f"every arm and every paired replicate of one run executes on one "
            f"backend, so activating {device_name!r} is refused"
        )
    torch.set_num_threads(REGISTERED_TORCH_THREADS)
    if int(torch.get_num_threads()) != REGISTERED_TORCH_THREADS:
        raise RuntimeError(
            f"intra-op thread pin did not take effect: "
            f"{torch.get_num_threads()} != {REGISTERED_TORCH_THREADS}"
        )
    _ACTIVE_EXECUTION_BACKEND = device_name
    return torch.device(device_name)


def active_execution_backend() -> str:
    """The backend activated for this process.

    Fail-closed: a contract cannot be built, and therefore no checkpoint can
    be written or read, before a backend has been explicitly registered.
    Defaulting here would let a run record an execution environment it is not
    actually using.
    """

    if _ACTIVE_EXECUTION_BACKEND is None:
        raise RuntimeError(
            "no registered execution backend is active; call "
            "require_registered_backend('cuda') or "
            "require_registered_backend('cpu') first"
        )
    return _ACTIVE_EXECUTION_BACKEND


def require_active_backend_device(device: "torch.device") -> None:
    """Refuse a device that disagrees with the activated backend."""

    backend = active_execution_backend()
    if device.type != backend:
        raise RuntimeError(
            f"device {device!r} does not belong to the active execution "
            f"backend {backend!r}"
        )


def float32_reduction_gamma(factor_count: Any) -> Any:
    """Standard `gamma_n = n*u/(1 - n*u)` float32 summation growth factor.

    `u = 2**-24` is the float32 unit roundoff. Summing `n` float32 values in
    any order gives a result within `gamma_{n-1} * sum|x_i|` of the exact
    sum; using `gamma_n` is the conservative form. Accepts a Python number
    or a tensor/array of per-row factor counts and returns the same kind.
    """

    scaled = factor_count * FLOAT32_UNIT_ROUNDOFF
    return scaled / (1.0 - scaled)


def make_rng(seed: int, *coordinates: int) -> np.random.Generator:
    """Create the registered explicit PCG64/SeedSequence stream."""

    return np.random.Generator(
        np.random.PCG64(
            np.random.SeedSequence([int(seed), *(int(v) for v in coordinates)])
        )
    )


def _profile_contract(profile: Profile) -> tuple[tuple[int, ...], int, int, int]:
    if profile in ("train", "iid"):
        return TRAIN_DURATION_SUPPORT, 20, 40, 60
    if profile == "held_out":
        return HELD_OUT_DURATION_SUPPORT, 12, 36, 68
    raise ValueError(f"unsupported profile {profile!r}")


@dataclass(frozen=True)
class NoncalendarLedger:
    episode_id: int
    base_id: int
    sign_parity: int
    profile: Profile
    routing_permutation: tuple[int, ...]
    initial_count: int
    temporary_key: int
    terminal_key: int
    duration_streams: np.ndarray
    initial_targets: np.ndarray
    direct_frontier_priorities: np.ndarray
    generation_attempt: int

    @property
    def duration_support(self) -> tuple[int, ...]:
        return _profile_contract(self.profile)[0]

    @property
    def temporary_leave_time(self) -> int:
        return _profile_contract(self.profile)[1]

    @property
    def rejoin_time(self) -> int:
        return _profile_contract(self.profile)[2]

    @property
    def terminal_leave_time(self) -> int:
        return _profile_contract(self.profile)[3]

    @property
    def joined_key(self) -> int:
        return int(self.routing_permutation[self.initial_count])

    def validate(self) -> None:
        if self.episode_id < 0 or self.base_id != self.episode_id // 2:
            raise ValueError("ledger episode/base identity mismatch")
        if self.sign_parity != self.episode_id % 2:
            raise ValueError("ledger sign parity mismatch")
        if tuple(sorted(self.routing_permutation)) != tuple(range(MAX_LIFECYCLES)):
            raise ValueError("routing keys must be one permutation of six keys")
        allowed_initial = (3, 4) if self.profile in ("train", "iid") else (2, 5)
        if self.initial_count not in allowed_initial:
            raise ValueError("initial membership count violates profile")
        initial = set(self.routing_permutation[: self.initial_count])
        if self.temporary_key not in initial:
            raise ValueError("temporary leave must select an initial lifecycle")
        active_at_terminal = initial | {self.joined_key}
        if self.terminal_key not in active_at_terminal:
            raise ValueError("terminal leave must select an active lifecycle")
        if self.duration_streams.shape != (MAX_LIFECYCLES, 30):
            raise ValueError("duration stream shape mismatch")
        support = set(self.duration_support)
        if set(int(v) for v in np.unique(self.duration_streams)) != support:
            raise ValueError("duration stream support mismatch")
        for key in range(MAX_LIFECYCLES):
            for offset in range(0, self.duration_streams.shape[1], 3):
                if set(int(v) for v in self.duration_streams[key, offset : offset + 3]) != support:
                    raise ValueError("duration block is not a support permutation")
        if self.initial_targets.shape != (MAX_LIFECYCLES,):
            raise ValueError("initial-target shape mismatch")
        if not set(int(v) for v in self.initial_targets).issubset({-2, 2}):
            raise ValueError("initial target must be -2 or +2")
        if self.direct_frontier_priorities.shape != (HORIZON, MAX_LIFECYCLES):
            raise ValueError("presentation/order table shape mismatch")
        if not np.isfinite(self.direct_frontier_priorities).all():
            raise ValueError("presentation/order table contains non-finite values")

    def membership_deltas(self, time: int) -> tuple[MembershipDelta, ...]:
        if int(time) == 0:
            return tuple(
                MembershipDelta(JOIN, str(key), 0)
                for key in self.routing_permutation[: self.initial_count]
            )
        if int(time) == self.temporary_leave_time:
            return (MembershipDelta(TEMPORARY_LEAVE, str(self.temporary_key), 0),)
        if int(time) == self.rejoin_time:
            return (
                MembershipDelta(REJOIN, str(self.temporary_key), 0),
                MembershipDelta(JOIN, str(self.joined_key), 0),
            )
        if int(time) == self.terminal_leave_time:
            return (MembershipDelta(TERMINAL_LEAVE, str(self.terminal_key), 0),)
        return ()


def _duration_streams(
    rng: np.random.Generator,
    support: tuple[int, ...],
    *,
    audit_trace: list[dict[str, Any]] | None = None,
    audit_coordinates: Mapping[str, Any] | None = None,
) -> np.ndarray:
    rows = np.empty((MAX_LIFECYCLES, 30), dtype=np.int64)
    values = np.asarray(support, dtype=np.int64)
    for key in range(MAX_LIFECYCLES):
        for offset in range(0, rows.shape[1], 3):
            rows[key, offset : offset + 3] = rng.permutation(values)
    if audit_trace is not None:
        audit_trace.append({
            "stream": "ledger",
            "operation": "seeded_permutation_blocks",
            "dtype": "int64",
            "shape": [MAX_LIFECYCLES, rows.shape[1] // 3, len(values)],
            "coordinates": dict(audit_coordinates or {}) | {
                "purpose": "duration_blocks",
                "key_order": list(range(MAX_LIFECYCLES)),
                "offset_order": list(range(0, rows.shape[1], 3)),
                "argument": values.tolist(),
            },
        })
    return rows


def _membership_active_keys(ledger: NoncalendarLedger, time: int) -> tuple[int, ...]:
    initial = list(ledger.routing_permutation[: ledger.initial_count])
    active = set(initial)
    if ledger.temporary_leave_time <= time < ledger.rejoin_time:
        active.remove(ledger.temporary_key)
    if time >= ledger.rejoin_time:
        active.add(ledger.joined_key)
    if time >= ledger.terminal_leave_time:
        active.remove(ledger.terminal_key)
    return tuple(sorted(active))


def ledger_active_row_count(ledger: NoncalendarLedger) -> int:
    return sum(len(_membership_active_keys(ledger, time)) for time in range(HORIZON))


def heterogeneity_support(ledger: NoncalendarLedger) -> dict[str, Any]:
    """Audit the registered held-out lifetime heterogeneity without actions."""

    remaining = np.zeros(MAX_LIFECYCLES, dtype=np.int64)
    duration_index = np.zeros(MAX_LIFECYCLES, dtype=np.int64)
    started = np.zeros(MAX_LIFECYCLES, dtype=np.bool_)
    transitions = np.zeros(MAX_LIFECYCLES, dtype=np.int64)
    differing_steps = 0
    for time in range(HORIZON):
        active = _membership_active_keys(ledger, time)
        for key in active:
            if not started[key]:
                started[key] = True
                remaining[key] = ledger.duration_streams[key, 0]
        if len(active) >= 2:
            active_remaining = remaining[np.asarray(active, dtype=np.int64)]
            if int(active_remaining.max() - active_remaining.min()) >= 2:
                differing_steps += 1
        for key in active:
            remaining[key] -= 1
            if remaining[key] == 0:
                transitions[key] += 1
                duration_index[key] += 1
                remaining[key] = ledger.duration_streams[key, duration_index[key]]
    transitioned_lifecycles = int(np.sum(transitions >= 1))
    return {
        "differing_remaining_steps": int(differing_steps),
        "transitioned_lifecycles": transitioned_lifecycles,
        "valid": bool(differing_steps >= 20 and transitioned_lifecycles >= 3),
    }


def make_noncalendar_ledger(
    episode_id: int,
    *,
    profile: Profile,
    task_seed: int,
    order_seed: int,
    audit_trace: dict[str, list[dict[str, Any]]] | None = None,
) -> NoncalendarLedger:
    """Materialize one sign-paired task ledger with no causal future input."""

    episode_id = int(episode_id)
    base_id = episode_id // 2
    sign_parity = episode_id % 2
    support = _profile_contract(profile)[0]
    for attempt in range(10_000):
        rng = make_rng(task_seed, base_id, attempt)
        coordinates = {
            "episode_id": episode_id, "base_id": base_id,
            "attempt": attempt, "generator_coordinates": [base_id, attempt],
        }
        routing = tuple(int(v) for v in rng.permutation(MAX_LIFECYCLES))
        if audit_trace is not None:
            audit_trace["ledger"].append({
                "stream": "ledger", "operation": "seeded_permutation",
                "dtype": "int64", "shape": [MAX_LIFECYCLES],
                "coordinates": coordinates | {
                    "purpose": "routing", "argument": MAX_LIFECYCLES,
                },
            })
        initial_count = int(rng.choice((3, 4) if profile in ("train", "iid") else (2, 5)))
        if audit_trace is not None:
            audit_trace["ledger"].append({
                "stream": "ledger", "operation": "seeded_choice",
                "dtype": "int64", "shape": [],
                "coordinates": coordinates | {
                    "purpose": "initial_count",
                    "argument": list((3, 4) if profile in ("train", "iid") else (2, 5)),
                    "replace": True,
                },
            })
        temporary_key = int(rng.choice(np.asarray(routing[:initial_count], dtype=np.int64)))
        if audit_trace is not None:
            audit_trace["ledger"].append({
                "stream": "ledger", "operation": "seeded_choice",
                "dtype": "int64", "shape": [],
                "coordinates": coordinates | {
                    "purpose": "temporary_key",
                    "argument": list(routing[:initial_count]), "replace": True,
                },
            })
        terminal_candidates = np.asarray((*routing[:initial_count], routing[initial_count]), dtype=np.int64)
        terminal_key = int(rng.choice(terminal_candidates))
        if audit_trace is not None:
            audit_trace["ledger"].append({
                "stream": "ledger", "operation": "seeded_choice",
                "dtype": "int64", "shape": [],
                "coordinates": coordinates | {
                    "purpose": "terminal_key",
                    "argument": terminal_candidates.tolist(), "replace": True,
                },
            })
        durations = _duration_streams(
            rng, support,
            audit_trace=None if audit_trace is None else audit_trace["ledger"],
            audit_coordinates=coordinates,
        )
        base_targets = rng.choice(
            np.asarray((-2, 2), dtype=np.int64), size=MAX_LIFECYCLES, replace=True
        )
        if audit_trace is not None:
            audit_trace["ledger"].append({
                "stream": "ledger", "operation": "seeded_choice",
                "dtype": "int64", "shape": [MAX_LIFECYCLES],
                "coordinates": coordinates | {
                    "purpose": "initial_targets", "argument": [-2, 2],
                    "replace": True,
                },
            })
        if sign_parity:
            base_targets = -base_targets
        order_rng = make_rng(order_seed, base_id, 0)
        priorities = order_rng.random((HORIZON, MAX_LIFECYCLES))
        if audit_trace is not None:
            audit_trace["order"].append({
                "stream": "order", "operation": "seeded_random",
                "dtype": "float64", "shape": [HORIZON, MAX_LIFECYCLES],
                "coordinates": {
                    "episode_id": episode_id, "base_id": base_id,
                    "attempt": attempt, "generator_coordinates": [base_id, 0],
                    "purpose": "frontier_priorities",
                },
            })
        ledger = NoncalendarLedger(
            episode_id=episode_id,
            base_id=base_id,
            sign_parity=sign_parity,
            profile=profile,
            routing_permutation=routing,
            initial_count=initial_count,
            temporary_key=temporary_key,
            terminal_key=terminal_key,
            duration_streams=durations,
            initial_targets=np.asarray(base_targets, dtype=np.int64),
            direct_frontier_priorities=priorities,
            generation_attempt=attempt,
        )
        ledger.validate()
        if profile != "held_out" or heterogeneity_support(ledger)["valid"]:
            return ledger
    raise RuntimeError("failed to materialize a valid held-out heterogeneity ledger")


def paired_ledgers_equal_except_targets(left: NoncalendarLedger, right: NoncalendarLedger) -> bool:
    if left.base_id != right.base_id or left.sign_parity == right.sign_parity:
        return False
    scalar_names = (
        "profile", "routing_permutation", "initial_count", "temporary_key",
        "terminal_key", "generation_attempt",
    )
    if any(getattr(left, name) != getattr(right, name) for name in scalar_names):
        return False
    return bool(
        np.array_equal(left.duration_streams, right.duration_streams)
        and np.array_equal(left.direct_frontier_priorities, right.direct_frontier_priorities)
        and np.array_equal(left.initial_targets, -right.initial_targets)
    )


def relabel_ledger(
    ledger: NoncalendarLedger, permutation: Sequence[int]
) -> NoncalendarLedger:
    """Synchronously rename opaque lifecycle routing keys."""

    mapping = tuple(int(v) for v in permutation)
    if tuple(sorted(mapping)) != tuple(range(MAX_LIFECYCLES)):
        raise ValueError("anonymous relabeling requires one six-key permutation")
    durations = np.empty_like(ledger.duration_streams)
    targets = np.empty_like(ledger.initial_targets)
    priorities = np.empty_like(ledger.direct_frontier_priorities)
    for old, new in enumerate(mapping):
        durations[new] = ledger.duration_streams[old]
        targets[new] = ledger.initial_targets[old]
        priorities[:, new] = ledger.direct_frontier_priorities[:, old]
    value = NoncalendarLedger(
        episode_id=ledger.episode_id,
        base_id=ledger.base_id,
        sign_parity=ledger.sign_parity,
        profile=ledger.profile,
        routing_permutation=tuple(mapping[key] for key in ledger.routing_permutation),
        initial_count=ledger.initial_count,
        temporary_key=mapping[ledger.temporary_key],
        terminal_key=mapping[ledger.terminal_key],
        duration_streams=durations,
        initial_targets=targets,
        direct_frontier_priorities=priorities,
        generation_attempt=ledger.generation_attempt,
    )
    value.validate()
    return value


@dataclass
class TrackingMemberState:
    key: int
    status: str = NOT_JOINED
    membership_epoch: int = 0
    x: int = 0
    previous_thrust: int = 0
    action_run: int = 0
    target: int = 2
    remaining: int = 0
    streak: int = 0
    active_steps: int = 0
    duration_index: int = 0
    target_changed: bool = False


@dataclass(frozen=True)
class TrackingMembershipChange:
    joined: tuple[int, ...] = ()
    temporarily_left: tuple[int, ...] = ()
    rejoined: tuple[int, ...] = ()
    terminally_left: tuple[int, ...] = ()


@dataclass(frozen=True)
class TrackingView:
    time: int
    active_keys: tuple[int, ...]
    observations: np.ndarray
    membership_change: TrackingMembershipChange


@dataclass(frozen=True)
class TrackingOutcome:
    tracking: float
    completion: float
    utility: float
    terminal_reward: float
    tracking_quarter_units: int
    active_rows: int
    completed_segments: int
    eligible_segments: int
    roster_sizes: tuple[int, ...]
    reward_trace: tuple[float, ...]

    @property
    def persistent_score(self) -> float:
        return self.tracking

    @property
    def short_score(self) -> float:
        return self.completion


class NoncalendarTrackingEnv:
    """Exact finite-state primitive tracking environment for one ledger."""

    def __init__(self, ledger: NoncalendarLedger):
        ledger.validate()
        self.ledger = ledger
        self.members = {key: TrackingMemberState(key=key) for key in range(MAX_LIFECYCLES)}
        self.time = 0
        self.tracking_quarter_units = 0
        self.active_rows = 0
        self.completed_segments = 0
        self.eligible_segments = 0
        self.roster_sizes: list[int] = []
        self.reward_trace: list[float] = []
        self._prepared_time: int | None = None
        self._membership_change = TrackingMembershipChange()
        self._terminated = False

    @property
    def active_keys(self) -> tuple[int, ...]:
        active = tuple(key for key, state in self.members.items() if state.status == ACTIVE)
        if self.time >= HORIZON:
            return tuple(sorted(active))
        priorities = self.ledger.direct_frontier_priorities[self.time]
        return tuple(sorted(active, key=lambda key: float(priorities[key])))

    def _genuine_join(self, key: int) -> None:
        state = self.members[key]
        if state.status != NOT_JOINED:
            raise RuntimeError("genuine JOIN attempted to reuse a lifecycle")
        state.status = ACTIVE
        state.membership_epoch = 0
        state.x = 0
        state.previous_thrust = 0
        state.action_run = 0
        state.target = int(self.ledger.initial_targets[key])
        state.remaining = int(self.ledger.duration_streams[key, 0])
        state.streak = 0
        state.active_steps = 0
        state.duration_index = 0
        state.target_changed = True

    def _apply_membership(self) -> TrackingMembershipChange:
        joined: tuple[int, ...] = ()
        temporarily_left: tuple[int, ...] = ()
        rejoined: tuple[int, ...] = ()
        terminally_left: tuple[int, ...] = ()
        if self.time == 0:
            joined = tuple(self.ledger.routing_permutation[: self.ledger.initial_count])
            for key in joined:
                self._genuine_join(key)
        elif self.time == self.ledger.temporary_leave_time:
            key = self.ledger.temporary_key
            if self.members[key].status != ACTIVE:
                raise RuntimeError("temporary LEAVE selected a non-active lifecycle")
            self.members[key].status = TEMPORARILY_ABSENT
            temporarily_left = (key,)
        elif self.time == self.ledger.rejoin_time:
            key = self.ledger.temporary_key
            if self.members[key].status != TEMPORARILY_ABSENT:
                raise RuntimeError("REJOIN selected a non-absent lifecycle")
            self.members[key].status = ACTIVE
            self.members[key].membership_epoch += 1
            rejoined = (key,)
            joined = (self.ledger.joined_key,)
            self._genuine_join(self.ledger.joined_key)
        elif self.time == self.ledger.terminal_leave_time:
            key = self.ledger.terminal_key
            if self.members[key].status != ACTIVE:
                raise RuntimeError("terminal LEAVE selected a non-active lifecycle")
            self.members[key].status = TERMINAL
            del self.members[key]
            terminally_left = (key,)
        return TrackingMembershipChange(
            joined=joined,
            temporarily_left=temporarily_left,
            rejoined=rejoined,
            terminally_left=terminally_left,
        )

    def _prepare(self) -> None:
        if self._terminated or self.time >= HORIZON:
            raise RuntimeError("cannot prepare a terminated environment")
        if self._prepared_time == self.time:
            return
        self._membership_change = self._apply_membership()
        self._prepared_time = self.time
        self.roster_sizes.append(len(self.active_keys))

    def _raw_observations(self) -> np.ndarray:
        keys = self.active_keys
        states = [self.members[key] for key in keys]
        n = len(states)
        if n <= 0:
            raise RuntimeError("tracking environment has an empty active roster")
        xs = np.asarray([state.x for state in states], dtype=np.float64)
        targets = np.asarray([state.target for state in states], dtype=np.float64)
        changes = np.asarray([state.target_changed for state in states], dtype=np.float64)
        boundary_keys = set(self._membership_change.joined) | set(self._membership_change.rejoined)
        common = np.asarray(
            (
                self.time / 80.0,
                np.log1p(n) / np.log(7.0),
                float(np.mean(xs / 2.0)),
                float(np.mean(targets / 2.0)),
                float(np.mean((targets - xs) / 4.0)),
                float(np.mean(np.abs(targets - xs) / 4.0)),
                float(np.mean(changes)),
                float(sum(key in boundary_keys for key in keys) / n),
            ),
            dtype=np.float32,
        )
        rows = np.zeros((n, OBSERVATION_DIM), dtype=np.float32)
        for row, (key, state) in enumerate(zip(keys, states)):
            event_code = 1.0 if key in self._membership_change.joined else (
                -1.0 if key in self._membership_change.rejoined else 0.0
            )
            rows[row, :COMMON_FIELD_COUNT] = common
            rows[row, 8:] = np.asarray(
                (
                    state.x / 2.0,
                    state.target / 2.0,
                    (state.target - state.x) / 4.0,
                    float(state.target_changed),
                    event_code,
                    float(state.previous_thrust),
                    min(state.action_run, 16) / 16.0,
                ),
                dtype=np.float32,
            )
        return rows

    def observe(self) -> TrackingView:
        self._prepare()
        observations = self._raw_observations()
        return TrackingView(
            time=self.time,
            active_keys=self.active_keys,
            observations=observations,
            membership_change=self._membership_change,
        )

    def step(self, actions: Mapping[int, int]) -> tuple[float, bool, dict[str, Any]]:
        self._prepare()
        active = self.active_keys
        if set(int(k) for k in actions) != set(active):
            raise ValueError("primitive action map must equal the active roster")
        for key in active:
            action = int(actions[key])
            if not 0 <= action < ACTION_COUNT:
                raise ValueError("primitive action is outside {0,1,2}")
            thrust = int(THRUST_BY_ACTION[action])
            state = self.members[key]
            new_x = int(np.clip(state.x + thrust, STATE_MIN, STATE_MAX))
            self.tracking_quarter_units += 4 - abs(new_x - state.target)
            new_streak = min(state.streak + 1, TARGET_STREAK) if new_x == state.target else 0
            state.action_run = min(state.action_run + 1, 16) if thrust == state.previous_thrust else 1
            state.previous_thrust = thrust
            state.x = new_x
            state.active_steps += 1
            state.remaining -= 1
            self.active_rows += 1
            if state.remaining == 0:
                self.eligible_segments += 1
                if new_streak == TARGET_STREAK:
                    self.completed_segments += 1
                state.duration_index += 1
                state.target = -state.target
                state.remaining = int(self.ledger.duration_streams[key, state.duration_index])
                state.streak = 0
                state.target_changed = True
            else:
                state.streak = int(new_streak)
                state.target_changed = False

        terminal = self.time == HORIZON - 1
        reward = 0.0
        if terminal:
            outcome = self._make_outcome(terminal_reward=0.0)
            reward = outcome.utility
        self.reward_trace.append(float(reward))
        self.time += 1
        self._prepared_time = None
        self._membership_change = TrackingMembershipChange()
        self._terminated = terminal
        return float(reward), terminal, {
            "tracking_quarter_units": self.tracking_quarter_units,
            "completed_segments": self.completed_segments,
            "eligible_segments": self.eligible_segments,
        }

    def _make_outcome(self, *, terminal_reward: float) -> TrackingOutcome:
        if self.active_rows <= 0 or self.eligible_segments <= 0:
            raise RuntimeError("episode lacks a valid tracking or completion denominator")
        tracking = self.tracking_quarter_units / float(4 * self.active_rows)
        completion = self.completed_segments / float(self.eligible_segments)
        utility = float(np.sqrt(tracking * completion))
        return TrackingOutcome(
            tracking=float(tracking),
            completion=float(completion),
            utility=float(utility),
            terminal_reward=float(terminal_reward),
            tracking_quarter_units=int(self.tracking_quarter_units),
            active_rows=int(self.active_rows),
            completed_segments=int(self.completed_segments),
            eligible_segments=int(self.eligible_segments),
            roster_sizes=tuple(self.roster_sizes),
            reward_trace=tuple(self.reward_trace),
        )

    def outcome(self) -> TrackingOutcome:
        if not self._terminated or self.time != HORIZON or len(self.reward_trace) != HORIZON:
            raise RuntimeError("outcome is available only after the terminal transition")
        value = self._make_outcome(terminal_reward=self.reward_trace[-1])
        if abs(value.terminal_reward - value.utility) > 1e-12:
            raise RuntimeError("terminal reward does not equal utility")
        if any(abs(v) > 0.0 for v in value.reward_trace[:-1]):
            raise RuntimeError("nonterminal reward must be exactly zero")
        return value

    def snapshot_state(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "ledger": deepcopy(self.ledger),
            "members": deepcopy(self.members),
            "time": self.time,
            "tracking_quarter_units": self.tracking_quarter_units,
            "active_rows": self.active_rows,
            "completed_segments": self.completed_segments,
            "eligible_segments": self.eligible_segments,
            "roster_sizes": list(self.roster_sizes),
            "reward_trace": list(self.reward_trace),
            "prepared_time": self._prepared_time,
            "membership_change": deepcopy(self._membership_change),
            "terminated": self._terminated,
        }

    @classmethod
    def from_snapshot_state(cls, value: Mapping[str, Any]) -> "NoncalendarTrackingEnv":
        required = {
            "schema_version", "ledger", "members", "time",
            "tracking_quarter_units", "active_rows", "completed_segments",
            "eligible_segments", "roster_sizes", "reward_trace", "prepared_time",
            "membership_change", "terminated",
        }
        payload = dict(value)
        if set(payload) != required or int(payload["schema_version"]) != 1:
            raise ValueError("tracking environment snapshot schema mismatch")
        env = cls(deepcopy(payload["ledger"]))
        env.members = deepcopy(payload["members"])
        env.time = int(payload["time"])
        env.tracking_quarter_units = int(payload["tracking_quarter_units"])
        env.active_rows = int(payload["active_rows"])
        env.completed_segments = int(payload["completed_segments"])
        env.eligible_segments = int(payload["eligible_segments"])
        env.roster_sizes = list(payload["roster_sizes"])
        env.reward_trace = list(payload["reward_trace"])
        env._prepared_time = payload["prepared_time"]
        env._membership_change = deepcopy(payload["membership_change"])
        env._terminated = bool(payload["terminated"])
        return env




def profile_seeds(profile: Profile) -> tuple[int, int]:
    if profile == "train":
        return TRAIN_TASK_SEED, TRAIN_ORDER_SEED
    if profile == "iid":
        return IID_EVAL_TASK_SEED, TRAIN_ORDER_SEED
    if profile == "held_out":
        return HELD_OUT_EVAL_TASK_SEED, TRAIN_ORDER_SEED
    raise ValueError(f"unsupported profile {profile!r}")


def frontier_order(
    ledgers: Sequence[NoncalendarLedger], active_masks: np.ndarray, time: int
) -> np.ndarray:
    rows: list[np.ndarray] = []
    for ledger, mask in zip(ledgers, active_masks):
        active = np.flatnonzero(mask)
        ordered = active[np.argsort(ledger.direct_frontier_priorities[time, active])]
        row = np.full(MAX_LIFECYCLES, -1, dtype=np.int64)
        row[: len(ordered)] = ordered
        rows.append(row)
    return np.stack(rows)


def _checked_interval(name: str, interval: Sequence[float]) -> tuple[float, float]:
    """One two-sided confidence interval, low bound first.

    An inverted interval is an analyzer defect, not a numerical pattern, and
    would silently invert a `LCB > 0` gate into something else. It raises.
    """

    if len(interval) != 2:
        raise ValueError(f"{name} must be a (lcb, ucb) pair; got {interval!r}")
    low, high = float(interval[0]), float(interval[1])
    if not low <= high:
        raise ValueError(f"{name} is inverted: {low} > {high}")
    return low, high


def select_result_branch(
    *,
    operational_valid: bool,
    non_create_opportunities: int,
    multi_opportunity_lifecycles: int,
    eligible_keep_rows: int,
    eligible_renew_rows: int,
    natural_keep_rows_by_replicate: Sequence[int],
    natural_renew_rows_by_replicate: Sequence[int],
    utility_ci: Mapping[str, tuple[float, float]],
    g_ci: tuple[float, float],
    k_bin_cis: Sequence[tuple[float, float]],
    intervention_ci: tuple[float, float],
    a_keep_ci: Sequence[float],
    a_renew_ci: Sequence[float],
    a_keep_mean: float,
    a_renew_mean: float,
) -> str:
    """Apply the frozen eight-branch first-match precedence.

    `P_KEEP`/`P_RENEW` gate nothing: usage rates were replaced by the
    `eligible_keep_rows`/`eligible_renew_rows` support floors (precedence
    position 2). Lifetime evidence is policy-determined `K`-bins
    (`K==1`, `K==2`, `K>=3` over complete spells), not `CV(T)` or
    physical-time bins, which mix policy timing with exogenous gap variance
    and are reported only as descriptive diagnostics elsewhere.

    Replacement C joins position 5. Both directions are required --
    `LCB(A_KEEP) > 0` **and** `LCB(A_RENEW) > 0`, with the frozen point
    floors `mean(A_KEEP) >= 0.02` and `mean(A_RENEW) >= 0.02`. A one-sided
    pass is not expressible: the two gates are conjoined and both are
    required arguments, so there is no input that reaches
    `COMMITMENT_SUPPORTED` on one direction alone.

    The registered fork budget arrives as per-replicate counts, never as a
    pooled total. A replicate short of `NATURAL_FORK_QUOTA_PER_ACTION`
    eligible rows for either natural action resolves at position 2 to
    `BENCHMARK_NON_IDENTIFIABLE`, and because no pooled total is an input,
    the shortfall cannot be repaired by pooling rows across replicates or by
    lowering the quota.

    "Behavior confidently fails" stays the *exact statistical dual* of the
    pass rule: at least one required interval condition has `UCB <=` its
    registered threshold, now including `UCB(A_KEEP) <= 0` and
    `UCB(A_RENEW) <= 0`. The two point-estimate floors deliberately take no
    part in the dual -- a point estimate carries no interval statement, so a
    run that clears both `LCB` gates but misses a mean floor neither passes
    nor confidently fails and lands in the underpowered branch.
    """

    if len(k_bin_cis) != 3:
        raise ValueError(
            "k_bin_cis must have exactly 3 entries (K==1, K==2, K>=3); "
            f"got {len(k_bin_cis)}"
        )
    for name, counts in (
        ("natural_keep_rows_by_replicate", natural_keep_rows_by_replicate),
        ("natural_renew_rows_by_replicate", natural_renew_rows_by_replicate),
    ):
        if len(counts) != NATURAL_FORK_REPLICATES:
            raise ValueError(
                f"{name} must carry one count per replicate "
                f"({NATURAL_FORK_REPLICATES}); got {len(counts)}"
            )
    a_keep_low, a_keep_high = _checked_interval("a_keep_ci", a_keep_ci)
    a_renew_low, a_renew_high = _checked_interval("a_renew_ci", a_renew_ci)
    if not operational_valid:
        return "INVALID_OPERATIONAL"
    if (
        non_create_opportunities < IDENTIFIABILITY_OPPORTUNITIES
        or multi_opportunity_lifecycles < IDENTIFIABILITY_LIFECYCLES
        or eligible_keep_rows < SUPPORT_FLOOR
        or eligible_renew_rows < SUPPORT_FLOOR
        or min(natural_keep_rows_by_replicate) < NATURAL_FORK_QUOTA_PER_ACTION
        or min(natural_renew_rows_by_replicate) < NATURAL_FORK_QUOTA_PER_ACTION
    ):
        return "BENCHMARK_NON_IDENTIFIABLE"
    maximum_ucb = max(interval[1] for interval in utility_ci.values())
    maximum_lcb = max(interval[0] for interval in utility_ci.values())
    if maximum_ucb < ACCESS_FLOOR:
        return "NO_ACCESS_THIS_BENCHMARK"
    if maximum_lcb < ACCESS_FLOOR:
        return "UNDERPOWERED_ACCESS"
    behavior_passes = bool(
        sum(ci[0] > LIFETIME_BIN_THRESHOLD for ci in k_bin_cis) >= 2
        and intervention_ci[0] > INTERVENTION_THRESHOLD
    )
    consequence_passes = bool(
        a_keep_low > A_KEEP_LCB_FLOOR
        and a_renew_low > A_RENEW_LCB_FLOOR
        and float(a_keep_mean) >= A_KEEP_MEAN_FLOOR
        and float(a_renew_mean) >= A_RENEW_MEAN_FLOOR
    )
    if g_ci[0] > GAIN_THRESHOLD and behavior_passes and consequence_passes:
        return "COMMITMENT_SUPPORTED"
    confidently_fails = bool(
        sum(ci[1] > LIFETIME_BIN_THRESHOLD for ci in k_bin_cis) < 2
        or intervention_ci[1] <= INTERVENTION_THRESHOLD
        or a_keep_high <= A_KEEP_LCB_FLOOR
        or a_renew_high <= A_RENEW_LCB_FLOOR
    )
    if g_ci[0] > GAIN_THRESHOLD and confidently_fails:
        return "REPRESENTATION_ONLY"
    if g_ci[1] <= GAIN_THRESHOLD:
        return "ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED"
    return "MIXED_UNDERPOWERED"


def registered_contract() -> dict[str, Any]:
    """The frozen contract, embedded in every checkpoint and artifact.

    The `execution` block is the structural form of the same-backend
    constraint. It carries the backend actually activated for this process
    and the live intra-op thread count, and `load_checkpoint` compares the
    whole dictionary for equality, so a checkpoint written under one
    execution environment is unloadable under another. Requiring an
    activated backend, rather than defaulting to one, is what keeps the
    recorded value honest.
    """

    return {
        "name": REGISTERED_CONTRACT,
        "horizon": HORIZON,
        "execution": {
            "backend": active_execution_backend(),
            "registered_backends": list(REGISTERED_EXECUTION_BACKENDS),
            "torch_threads": int(torch.get_num_threads()),
            "uniformity_rule": (
                "every arm and every paired replicate of one run executes on "
                "one backend and one thread configuration; the backend and "
                "thread count recorded here are compared for equality by "
                "load_checkpoint, so a checkpoint written under one execution "
                "environment cannot be loaded or continued under another"
            ),
            "fallback_rule": (
                "an unavailable requested backend raises; no other backend is "
                "ever substituted"
            ),
        },
        "evidence_streaming": {
            "layout": "root_immutable_index_generation_update_shard_and_cell_reference_v2",
            "train_manifest_schema": 6,
            "train_index_schema": 2,
            "train_update_schema": 2,
            "evaluation_manifest_schema": 4,
            "evaluation_cell_schema": 7,
            "digest": "sha256",
            "path_rule": "strict_root_relative_contained",
            "publication": "same_directory_fsync_atomic_replace",
        },
        "maximum_lifecycles": MAX_LIFECYCLES,
        "observation_width": OBSERVATION_DIM,
        "arms": ["OR", "DUM", "EHC"],
        "base_parameters": PARAMETER_COUNT,
        "added_parameters": {"DUM": ADDED_PARAMETER_COUNT, "EHC": ADDED_PARAMETER_COUNT},
        "num_envs": FORMAL_NUM_ENVS,
        "outer_updates": FORMAL_UPDATES,
        "transitions_per_arm": FORMAL_TRANSITIONS_PER_ARM,
        "training_episodes_per_arm": FORMAL_TRAIN_EPISODES,
        "optimizer_steps": {
            "base": FORMAL_OPTIMIZER_STEPS_PER_ARM,
            "event_DUM_EHC": FORMAL_OPTIMIZER_STEPS_PER_ARM,
            "event_OR": 0,
        },
        "eval_episodes_per_cell": FORMAL_EVAL_EPISODES,
        "evaluation_cells": [
            "iid_deterministic",
            "iid_stochastic",
            "held_out_deterministic",
            "held_out_stochastic",
        ],
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "duration_support": {
            "train": list(TRAIN_DURATION_SUPPORT),
            "iid": list(TRAIN_DURATION_SUPPORT),
            "held_out": list(HELD_OUT_DURATION_SUPPORT),
        },
        "seeds": {
            "initialization": MODEL_INITIALIZATION_SEED,
            "ledger": TRAIN_TASK_SEED,
            "order": TRAIN_ORDER_SEED,
            "primitive": TRAIN_ACTION_SEED,
            "opportunity": OPPORTUNITY_SEED,
            "event": EVENT_SEED,
            "mark": MARK_SEED,
            "iid_evaluation": IID_EVAL_TASK_SEED,
            "held_out_evaluation": HELD_OUT_EVAL_TASK_SEED,
            "bootstrap": BOOTSTRAP_SEED,
            "replicate_stride": 1000,
        },
        "thresholds": {
            "access": ACCESS_FLOOR,
            "gain": GAIN_THRESHOLD,
            "support_floor": SUPPORT_FLOOR,
            "k_bin": LIFETIME_BIN_THRESHOLD,
            "intervention": INTERVENTION_THRESHOLD,
            "identifiability_opportunities": IDENTIFIABILITY_OPPORTUNITIES,
            "identifiability_lifecycles": IDENTIFIABILITY_LIFECYCLES,
            "a_keep_lcb": A_KEEP_LCB_FLOOR,
            "a_renew_lcb": A_RENEW_LCB_FLOOR,
            "a_keep_mean_floor": A_KEEP_MEAN_FLOOR,
            "a_renew_mean_floor": A_RENEW_MEAN_FLOOR,
        },
        "k_bins": ["K==1", "K==2", "K>=3"],
        "intervention_metric": "primitive_action_total_variation",
        "natural_fork": {
            "actions": list(NATURAL_FORK_ACTIONS),
            "quota_per_action_per_replicate": NATURAL_FORK_QUOTA_PER_ACTION,
            "replicates": NATURAL_FORK_REPLICATES,
            "pairs": NATURAL_FORK_PAIRS,
            "budget_rule": (
                "32 natural KEEP and 32 natural RENEW opportunities per "
                "replicate, 320 fork pairs across five replicates. This is the "
                "sole registered form; full per-opportunity forking is not the "
                "default."
            ),
            "shortfall_rule": (
                "a replicate supplying fewer than the quota of eligible rows "
                "for either natural action makes the run "
                "BENCHMARK_NON_IDENTIFIABLE; it is not repairable by lowering "
                "the quota, by pooling rows across replicates, or by "
                "post-result top-up"
            ),
            "gate_rule": (
                "LCB_95>0 for A_KEEP and for A_RENEW, both required, with "
                "frozen point floors mean(A_KEEP)>=0.02 and "
                "mean(A_RENEW)>=0.02. A one-sided pass is not sufficient and "
                "is not expressible."
            ),
            "confident_failure_dual": (
                "the exact statistical dual of the interval gates: "
                "UCB(A_KEEP)<=0 or UCB(A_RENEW)<=0. The two point floors are "
                "point estimates and take no part in the dual."
            ),
            "selection_stream": {
                "namespace": NATURAL_FORK_SELECTION_NAMESPACE,
                "base_seed": BOOTSTRAP_SEED,
                "coordinate": NATURAL_FORK_SELECTION_COORDINATE,
                "rule": (
                    "PCG64 over SeedSequence([bootstrap_seed, coordinate, ...]) "
                    "-- a dedicated deterministic stream under its own "
                    "namespace coordinate"
                ),
                "distinct_from": [
                    "bootstrap_resample",
                    "ledger",
                    "order",
                    "primitive",
                    "opportunity",
                    "event",
                    "mark",
                ],
            },
        },
        "optimization": {
            "gamma": GAMMA,
            "gae_lambda": GAE_LAMBDA,
            "ppo_clip": PPO_CLIP,
            "value_clip": VALUE_CLIP,
            "value_coefficient": VALUE_COEFFICIENT,
            "primitive_entropy_coefficient": PRIMITIVE_ENTROPY_COEFFICIENT,
            "event_entropy_coefficient": EVENT_ENTROPY_COEFFICIENT,
            "mark_entropy_coefficient": MARK_ENTROPY_COEFFICIENT,
            "gradient_clip": GRADIENT_CLIP,
            "learning_rate": LEARNING_RATE,
            "adam_epsilon": ADAM_EPSILON,
            "weight_decay": WEIGHT_DECAY,
            "ppo_passes": PPO_PASSES,
            "resume_tolerance": RESUME_TOLERANCE,
            "opportunity_support": list(OPPORTUNITY_SUPPORT),
            "evidence_schema_version": OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
            "norm_atol": OPTIMIZER_NORM_ATOL,
            "norm_rtol": OPTIMIZER_NORM_RTOL,
            "clip_epsilon": OPTIMIZER_CLIP_EPSILON,
            "loss_atol": OPTIMIZER_LOSS_ATOL,
            "loss_rtol": OPTIMIZER_LOSS_RTOL,
            "gradient_payload": "zlib9_base64_little_endian",
        },
        "rng_binding": {
            "schema_version": RNG_BINDING_SCHEMA_VERSION,
            "generator": "numpy.random.PCG64",
            "digest": "sha256",
            "training_chain": ["replicate", "arm", "stream", "update"],
            "evaluation_chain": [
                "replicate", "arm", "cell", "stream", "batch"
            ],
            "stage2_context": [
                "fork_id", "episode_id", "time", "key",
                "membership_epoch", "segment_id", "natural_action",
                "branch_action",
            ],
        },
        "replay_tolerances": {
            "exact_fields": list(REPLAY_EXACT_FIELDS),
            "log_component_fields": list(REPLAY_LOG_COMPONENT_FIELDS),
            "state_fields": list(REPLAY_STATE_FIELDS),
            "joint_fields": list(REPLAY_JOINT_FIELDS),
            "joint_record_fields": list(REPLAY_JOINT_RECORD_FIELDS),
            "worst_record_fields": list(REPLAY_WORST_RECORD_FIELDS),
            "event_joint_ratio_fields": list(REPLAY_EVENT_JOINT_RATIO_FIELDS),
            "log_component_atol": REPLAY_LOG_COMPONENT_ATOL,
            "log_component_rtol": REPLAY_LOG_COMPONENT_RTOL,
            "log_ratio_drift_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
            "state_atol": REPLAY_STATE_ATOL,
            "primitive_joint_rule": "component_sum_plus_float32_reduction",
            "event_joint_rule": (
                "categorical_plus_8_marks_plus_float32_reduction"
            ),
            "event_joint_factor_count": EVENT_JOINT_FACTOR_COUNT,
            "primitive_joint_factor_count": "active_lifecycles_per_row",
            "float32_unit_roundoff": FLOAT32_UNIT_ROUNDOFF,
            "support_leak_fields": [
                "categorical_support_leak",
                "mark_support_leak",
            ],
            "support_leak_rule": (
                "stored_factor_outside_its_own_mask_must_be_exactly_zero"
            ),
            # What each class does and does not prove, stated rather than
            # implied. A gate that cannot fire must not read as coverage.
            "primitive_joint_gating": (
                "non_gating: there is no independently stored primitive joint, "
                "so the error |sum(replay-stored)| is bounded by "
                "sum|replay-stored| plus slack -- the triangle inequality, an "
                "identity. Real primitive coverage is the mixed and ratio "
                "gate on primitive_component."
            ),
            "primitive_joint_assembly_gating": (
                "non_gating: compares float32 and float64 reductions of the "
                "identical difference terms against a bound orders of "
                "magnitude larger; invariant to injected corruption."
            ),
            "event_joint_gating": (
                "gates only joint assembly drift: once the stored and replayed "
                "assembly checks hold the joint rule is the triangle "
                "inequality. Factor-level coverage comes from the component "
                "and support-leak classes, not from this bound."
            ),
            "joint_record_internal_consistency": (
                "bound == component_sum + allowance; "
                "excess >= error - bound (excess is the row maximum of "
                "error-bound and the reported error/bound are read at the "
                "largest-error row, so equality is not an invariant); "
                "assembly_excess == assembly_residual - assembly_allowance, "
                "all three read at the deciding row and side; "
                "component_sum <= sum of the recorded per-factor component "
                "errors over the joint's factors; rows > 0 for any arm "
                "carrying the head that produces the joint."
            ),
            "correlated_bias_sensitivity": (
                "per-factor gating is ~9x weaker than the retired single "
                "scalar against a bias correlated across all nine event "
                "factors: the compositional rule can admit correlated drift, "
                "while each factor and the final event joint remain capped "
                "at replay-only ratio drift 1e-4."
            ),
            "non_finite_rule": "any_non_finite_leaf_fails_closed",
        },
    }
