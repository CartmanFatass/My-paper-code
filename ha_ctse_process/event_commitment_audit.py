"""Direct owner of event-held commitment causal auditing."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import base64
import hashlib
import json
from time import perf_counter
from typing import Any, Iterable, Literal, Mapping

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_testbed import MAX_LIFECYCLES
from ha_ctse_process.event_commitment_rng import (
    OPPORTUNITY_SUPPORT,
    RNG_NAMES,
    _canonical_json_digest,
    _float32_payload,
    authoritative_seed_map,
    make_training_state,
)
from ha_ctse_process.event_commitment_types import (
    ArmName,
    CollectionCursor,
    CommitmentArm,
    EventTrajectory,
    LifecycleState,
    MARK_DIM,
    SegmentRecord,
    TrainingState,
)
from ha_ctse_process.event_commitment_collector import (
    KEEP,
    RENEW,
    _AuditRowStream,
    collect_trajectory,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    CAUSAL_AUDIT_CONTINUOUS_ATOL,
    FORMAL_NUM_ENVS,
    NoncalendarLedger,
    NoncalendarTrackingEnv,
    make_noncalendar_ledger,
    make_rng,
)

AUDIT_BRANCHES = (
    "KEEP_HELD_MARK",
    "RENEW_DERANGED_MARK",
    "RENEW_CANDIDATE_MARK",
)


def _rng_states(state: TrainingState) -> dict[str, Any]:
    if set(state.rngs) != set(RNG_NAMES):
        raise ValueError("owned-RNG key set mismatch")
    return {name: deepcopy(state.rngs[name].bit_generator.state) for name in RNG_NAMES}



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
