"""Read-only opportunity-authority and behavior-use audit.

This module consumes the frozen supplied-executor checkpoints and existing
runtime APIs.  It never creates an optimizer, samples a policy action, mutates a
checkpoint, or changes the behavior path.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from itertools import product
import json
from pathlib import Path
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_clean_process_testbed import (
    CleanProcessDynamicRosterEnv,
    make_clean_process_dynamic_roster_ledger,
)
from ha_ctse_process.dynamic_roster_supplied_executor import (
    ACTION_SEED,
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    EVALUATION_TASK_SEED,
    FORMAL_EVAL_EPISODES,
    FRONTIER_STREAM_ID,
    FROZEN_HIGH_ARM,
    LEARNED_HIGH_ARM,
    OPPORTUNITY_FRONTIER_SEED,
    OPPORTUNITY_STREAM_ID,
    ORACLE_ARM,
    SuppliedExecutorVectorRuntime,
    clone_high_state,
    high_state_l2_drift,
    load_high_state,
    make_model_owner,
    paired_bootstrap_ci95,
)
from ha_ctse_process.dynamic_roster_testbed import (
    EXPECTED_SHORT_REQUIREMENT,
    HORIZON,
    IDLE,
    MAX_LIFECYCLES,
    PERSIST,
    PERSISTENT_TARGET,
    SHORT,
    SHORT_STREAK_TARGET,
    SHORT_WINDOW,
    WAVE_CANDIDATES,
    constructive_actions,
)
from ha_ctse_process.variable_roster_event import (
    JOIN,
    REJOIN,
    TEMPORARY_LEAVE,
    TERMINAL_LEAVE,
)


PACKAGE_NAME = "clean_supplied_executor_opportunity_authority_audit"
PACKAGE_SCHEMA_VERSION = 1
REGISTERED_FLOOR = 0.95
CONTRIBUTION_CLASSES = (
    "PREWAVE_SHORT",
    "POSTWAVE_SINGLETON",
    "POSTWAVE_MULTIOWNER_FIRST",
    "POSTWAVE_MULTIOWNER_LATER",
    "OTHER_OR_NO_TIMELY_OPPORTUNITY",
)
INVALID_STATUS = "INVALID_OPPORTUNITY_AUTHORITY_AUDIT"
UNREACHABLE_STATUS = "HINDSIGHT_OPPORTUNITY_FLOOR_UNREACHABLE"
PREPOSITION_STATUS = "HINDSIGHT_REACHABLE_PREPOSITIONING_REDUCTION"
PREFIX_STATUS = "HINDSIGHT_REACHABLE_MULTIOWNER_PREFIX_CANDIDATE"
MIXED_STATUS = "HINDSIGHT_REACHABLE_MIXED_OR_UNIDENTIFIED"


@dataclass(frozen=True)
class AuditMembershipEvent:
    kind: str
    keys: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.kind not in {JOIN, TEMPORARY_LEAVE, REJOIN, TERMINAL_LEAVE}:
            raise ValueError("audit membership event kind mismatch")
        if len(self.keys) != len(set(self.keys)):
            raise ValueError("audit membership event repeats a lifecycle")


@dataclass(frozen=True)
class OpportunityAuthorityLedger:
    episode_id: int
    horizon: int
    lifecycle_count: int
    persistent_target: int
    short_window: int
    short_streak_target: int
    membership_events: tuple[tuple[AuditMembershipEvent, ...], ...]
    active_keys: tuple[tuple[int, ...], ...]
    frontiers: tuple[tuple[int, ...], ...]
    wave_arrivals: tuple[int, ...]
    owner_priorities: tuple[tuple[float, ...], ...]
    presentation_orders: tuple[tuple[int, ...], ...]

    def validate(self) -> None:
        if self.horizon <= 0 or self.lifecycle_count <= 0:
            raise ValueError("audit ledger dimensions must be positive")
        if self.persistent_target <= 0 or self.short_window <= 0:
            raise ValueError("audit ledger target/window must be positive")
        if self.short_streak_target <= 0:
            raise ValueError("audit ledger streak target must be positive")
        for name in (
            "membership_events",
            "active_keys",
            "frontiers",
            "owner_priorities",
            "presentation_orders",
        ):
            if len(getattr(self, name)) != self.horizon:
                raise ValueError(f"audit ledger {name} length mismatch")
        for time in range(self.horizon):
            active = self.active_keys[time]
            frontier = self.frontiers[time]
            order = self.presentation_orders[time]
            if len(active) != len(set(active)) or any(
                key < 0 or key >= self.lifecycle_count for key in active
            ):
                raise ValueError("audit ledger active set is invalid")
            if len(frontier) != len(set(frontier)) or not set(frontier).issubset(active):
                raise ValueError("audit ledger frontier is not active-only")
            if set(order) != set(active) or len(order) != len(active):
                raise ValueError("audit ledger presentation order mismatch")
            if len(self.owner_priorities[time]) != self.lifecycle_count:
                raise ValueError("audit ledger owner-priority width mismatch")
        if any(time < 0 or time >= self.horizon for time in self.wave_arrivals):
            raise ValueError("audit ledger wave arrival lies outside horizon")
        if len(self.wave_arrivals) != len(set(self.wave_arrivals)):
            raise ValueError("audit ledger wave arrivals overlap")

    @property
    def short_required_total(self) -> int:
        return sum(len(self.active_keys[time]) - 1 for time in self.wave_arrivals)


@dataclass(frozen=True)
class _DPControl:
    skills: tuple[int, ...]
    persistent_owner: int
    wave_index: int
    wave_completed: int
    short_streaks: tuple[int, ...]
    contributed_mask: int


@dataclass(frozen=True)
class EpisodeReachableSet:
    episode_id: int
    persistent_target: int
    short_required_total: int
    outcome_pairs: tuple[tuple[int, int], ...]
    explored_control_states: int

    def normalized_outcomes(self) -> tuple[tuple[float, float, float], ...]:
        return tuple(
            (
                min(float(persistent) / float(self.persistent_target), 1.0),
                float(short) / float(self.short_required_total),
                0.5
                * (
                    min(float(persistent) / float(self.persistent_target), 1.0)
                    + float(short) / float(self.short_required_total)
                ),
            )
            for persistent, short in self.outcome_pairs
        )


def _pareto_pairs(values: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    unique = sorted(set((int(p), int(s)) for p, s in values), key=lambda x: (x[1], x[0]))
    kept: list[tuple[int, int]] = []
    best_persistent = -1
    for persistent, short in reversed(unique):
        if persistent > best_persistent:
            kept.append((persistent, short))
            best_persistent = persistent
    return tuple(sorted(kept))


def _apply_membership(
    control: _DPControl,
    events: Sequence[AuditMembershipEvent],
) -> _DPControl:
    skills = list(control.skills)
    streaks = list(control.short_streaks)
    owner = control.persistent_owner
    mask = int(control.contributed_mask)
    for event in events:
        for key in event.keys:
            if event.kind == JOIN:
                skills[key] = -1
                streaks[key] = 0
                mask &= ~(1 << key)
            elif event.kind == REJOIN:
                streaks[key] = 0
                mask &= ~(1 << key)
            elif event.kind in {TEMPORARY_LEAVE, TERMINAL_LEAVE}:
                streaks[key] = 0
                mask &= ~(1 << key)
                if owner == key:
                    owner = -1
                if event.kind == TERMINAL_LEAVE:
                    skills[key] = -1
    return _DPControl(
        skills=tuple(skills),
        persistent_owner=owner,
        wave_index=control.wave_index,
        wave_completed=control.wave_completed,
        short_streaks=tuple(streaks),
        contributed_mask=mask,
    )


def _open_wave(
    control: _DPControl,
    *,
    time: int,
    ledger: OpportunityAuthorityLedger,
) -> _DPControl:
    if time not in ledger.wave_arrivals:
        return control
    return _DPControl(
        skills=control.skills,
        persistent_owner=control.persistent_owner,
        wave_index=ledger.wave_arrivals.index(time),
        wave_completed=0,
        short_streaks=tuple(0 for _ in range(ledger.lifecycle_count)),
        contributed_mask=0,
    )


def _choice_controls(
    control: _DPControl,
    frontier: Sequence[int],
) -> Iterable[_DPControl]:
    for selected in product((IDLE, PERSIST, SHORT), repeat=len(frontier)):
        skills = list(control.skills)
        for key, action in zip(frontier, selected):
            skills[int(key)] = int(action)
        yield _DPControl(
            skills=tuple(skills),
            persistent_owner=control.persistent_owner,
            wave_index=control.wave_index,
            wave_completed=control.wave_completed,
            short_streaks=control.short_streaks,
            contributed_mask=control.contributed_mask,
        )


def _primitive_transition(
    control: _DPControl,
    *,
    time: int,
    ledger: OpportunityAuthorityLedger,
) -> tuple[_DPControl, int, int]:
    active = ledger.active_keys[time]
    if any(control.skills[key] not in (IDLE, PERSIST, SHORT) for key in active):
        raise ValueError("active lifecycle lacks a frontier-supplied skill")

    owner = control.persistent_owner
    persistent_increment = int(
        owner in active and owner >= 0 and control.skills[owner] == PERSIST
    )
    if not persistent_increment:
        candidates = tuple(key for key in active if control.skills[key] == PERSIST)
        owner = (
            min(candidates, key=lambda key: ledger.owner_priorities[time][key])
            if candidates
            else -1
        )

    streaks = list(control.short_streaks)
    mask = int(control.contributed_mask)
    wave_completed = int(control.wave_completed)
    short_increment = 0
    if control.wave_index >= 0:
        required = len(active) - 1
        for key in ledger.presentation_orders[time]:
            if mask & (1 << key):
                continue
            if control.skills[key] == SHORT:
                streaks[key] = min(
                    ledger.short_streak_target, streaks[key] + 1
                )
            else:
                streaks[key] = 0
            if streaks[key] == ledger.short_streak_target:
                mask |= 1 << key
                if wave_completed < required:
                    wave_completed += 1
                    short_increment += 1
    else:
        for key in active:
            streaks[key] = 0

    wave_index = control.wave_index
    if wave_index >= 0:
        arrival = ledger.wave_arrivals[wave_index]
        if time + 1 >= arrival + ledger.short_window:
            wave_index = -1
            wave_completed = 0
            streaks = [0 for _ in range(ledger.lifecycle_count)]
            mask = 0

    return (
        _DPControl(
            skills=control.skills,
            persistent_owner=owner,
            wave_index=wave_index,
            wave_completed=wave_completed,
            short_streaks=tuple(streaks),
            contributed_mask=mask,
        ),
        persistent_increment,
        short_increment,
    )


def _advance_control(
    control: _DPControl,
    *,
    time: int,
    ledger: OpportunityAuthorityLedger,
) -> Iterable[tuple[_DPControl, int, int]]:
    prepared = _apply_membership(control, ledger.membership_events[time])
    prepared = _open_wave(prepared, time=time, ledger=ledger)
    frontier = ledger.frontiers[time]
    if not set(frontier).issubset(ledger.active_keys[time]):
        raise ValueError("hindsight action attempted outside the realized frontier")
    for selected in _choice_controls(prepared, frontier):
        yield _primitive_transition(selected, time=time, ledger=ledger)


def solve_frontier_hindsight_episode(
    ledger: OpportunityAuthorityLedger,
) -> EpisodeReachableSet:
    """Exact per-episode DP with future-state-safe Pareto pruning."""

    ledger.validate()
    initial = _DPControl(
        skills=tuple(-1 for _ in range(ledger.lifecycle_count)),
        persistent_owner=-1,
        wave_index=-1,
        wave_completed=0,
        short_streaks=tuple(0 for _ in range(ledger.lifecycle_count)),
        contributed_mask=0,
    )
    states: dict[_DPControl, tuple[tuple[int, int], ...]] = {initial: ((0, 0),)}
    explored = 1
    for time in range(ledger.horizon):
        pending: dict[_DPControl, list[tuple[int, int]]] = defaultdict(list)
        for control, labels in states.items():
            for next_control, persistent_inc, short_inc in _advance_control(
                control, time=time, ledger=ledger
            ):
                for persistent, short in labels:
                    pending[next_control].append(
                        (
                            min(
                                ledger.persistent_target,
                                int(persistent) + int(persistent_inc),
                            ),
                            int(short) + int(short_inc),
                        )
                    )
        states = {
            control: _pareto_pairs(labels) for control, labels in pending.items()
        }
        explored += len(states)
    outcomes = _pareto_pairs(
        pair for labels in states.values() for pair in labels
    )
    return EpisodeReachableSet(
        episode_id=ledger.episode_id,
        persistent_target=ledger.persistent_target,
        short_required_total=ledger.short_required_total,
        outcome_pairs=outcomes,
        explored_control_states=explored,
    )


def solve_frontier_hindsight_bruteforce(
    ledger: OpportunityAuthorityLedger,
) -> EpisodeReachableSet:
    """Unpruned tiny-ledger reference used only by the focused test."""

    ledger.validate()
    total_tokens = sum(len(frontier) for frontier in ledger.frontiers)
    if total_tokens > 12:
        raise ValueError("brute-force reference is limited to twelve frontier tokens")
    initial = _DPControl(
        skills=tuple(-1 for _ in range(ledger.lifecycle_count)),
        persistent_owner=-1,
        wave_index=-1,
        wave_completed=0,
        short_streaks=tuple(0 for _ in range(ledger.lifecycle_count)),
        contributed_mask=0,
    )
    outcomes: list[tuple[int, int]] = []
    explored = 0

    def visit(time: int, control: _DPControl, persistent: int, short: int) -> None:
        nonlocal explored
        explored += 1
        if time == ledger.horizon:
            outcomes.append((persistent, short))
            return
        for next_control, persistent_inc, short_inc in _advance_control(
            control, time=time, ledger=ledger
        ):
            visit(
                time + 1,
                next_control,
                min(ledger.persistent_target, persistent + persistent_inc),
                short + short_inc,
            )

    visit(0, initial, 0, 0)
    return EpisodeReachableSet(
        episode_id=ledger.episode_id,
        persistent_target=ledger.persistent_target,
        short_required_total=ledger.short_required_total,
        outcome_pairs=_pareto_pairs(outcomes),
        explored_control_states=explored,
    )


def solve_frontier_hindsight_pareto(
    ledgers: Sequence[OpportunityAuthorityLedger],
) -> dict[str, Any]:
    """Compute the registered joint episode-level hindsight ceiling."""

    if not ledgers:
        raise ValueError("hindsight authority requires at least one episode")
    episode_sets = [solve_frontier_hindsight_episode(ledger) for ledger in ledgers]
    if len({item.persistent_target for item in episode_sets}) != 1 or len(
        {item.short_required_total for item in episode_sets}
    ) != 1:
        raise ValueError("joint hindsight requires common score denominators")
    aggregate: tuple[tuple[int, int], ...] = ((0, 0),)
    for item in episode_sets:
        aggregate = _pareto_pairs(
            (p0 + p1, s0 + s1)
            for p0, s0 in aggregate
            for p1, s1 in item.outcome_pairs
        )
    count = len(episode_sets)
    persistent_denominator = count * episode_sets[0].persistent_target
    short_denominator = count * episode_sets[0].short_required_total
    scored = []
    for persistent_sum, short_sum in aggregate:
        persistent_mean = persistent_sum / persistent_denominator
        short_mean = short_sum / short_denominator
        utility_mean = 0.5 * (persistent_mean + short_mean)
        scored.append(
            (
                min(persistent_mean, short_mean, utility_mean),
                persistent_mean,
                short_mean,
                utility_mean,
                persistent_sum,
                short_sum,
            )
        )
    best = max(scored)
    return {
        "g_h": float(best[0]),
        "persistent_mean": float(best[1]),
        "short_mean": float(best[2]),
        "utility_mean": float(best[3]),
        "persistent_sum": int(best[4]),
        "short_sum": int(best[5]),
        "floor": REGISTERED_FLOOR,
        "floor_feasible": bool(best[0] >= REGISTERED_FLOOR),
        "aggregate_pareto_size": len(aggregate),
        "episode_pareto_sizes": [len(item.outcome_pairs) for item in episode_sets],
        "episode_explored_control_states": [
            item.explored_control_states for item in episode_sets
        ],
        "episode_sets": episode_sets,
    }


def make_tiny_authority_ledger() -> OpportunityAuthorityLedger:
    """Small deterministic ledger for exact DP/brute-force comparison."""

    ledger = OpportunityAuthorityLedger(
        episode_id=0,
        horizon=4,
        lifecycle_count=2,
        persistent_target=3,
        short_window=3,
        short_streak_target=2,
        membership_events=(
            (AuditMembershipEvent(JOIN, (0, 1)),),
            (),
            (),
            (),
        ),
        active_keys=((0, 1),) * 4,
        frontiers=((0, 1), (), (0,), (1,)),
        wave_arrivals=(1,),
        owner_priorities=((0.1, 0.2),) * 4,
        presentation_orders=((0, 1),) * 4,
    )
    ledger.validate()
    return ledger


def _membership_events_from_transaction(transaction: Any) -> tuple[AuditMembershipEvent, ...]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for delta in transaction.atomic_membership_delta:
        grouped[str(delta.kind)].append(int(delta.lifecycle_key))
    return tuple(
        AuditMembershipEvent(kind, tuple(values))
        for kind in (JOIN, TEMPORARY_LEAVE, REJOIN, TERMINAL_LEAVE)
        if (values := grouped.get(kind))
    )


def _pre_policy_skills(core: Any, transaction: Any) -> dict[int, int | None]:
    joined = {
        int(delta.lifecycle_key)
        for delta in transaction.atomic_membership_delta
        if delta.kind == JOIN
    }
    values: dict[int, int | None] = {}
    for raw_key in transaction.post_membership_pre_policy_snapshot.keys:
        key = int(raw_key)
        record = core.records.get(str(key))
        values[key] = (
            None
            if key in joined or record is None or record.active_skill is None
            else int(record.active_skill)
        )
    return values


def _classify_source_event(
    *,
    arrival_skill: int | None,
    source_event: Mapping[str, Any] | None,
) -> str:
    if arrival_skill == SHORT and source_event is None:
        return "PREWAVE_SHORT"
    if source_event is None:
        return "OTHER_OR_NO_TIMELY_OPPORTUNITY"
    frontier_size = int(source_event["frontier_size"])
    token_position = int(source_event["token_position"])
    if frontier_size == 1:
        return "POSTWAVE_SINGLETON"
    if token_position == 0:
        return "POSTWAVE_MULTIOWNER_FIRST"
    return "POSTWAVE_MULTIOWNER_LATER"


def classify_short_contributions(
    contributions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate and aggregate already-causal, uniquely classified work units."""

    counts = Counter({name: 0 for name in CONTRIBUTION_CLASSES})
    seen: set[tuple[int, int]] = set()
    valid = True
    for raw in contributions:
        row = dict(raw)
        key = (int(row["wave_index"]), int(row["owner"]))
        name = str(row["class"])
        valid &= key not in seen and name in CONTRIBUTION_CLASSES
        seen.add(key)
        if name in CONTRIBUTION_CLASSES:
            counts[name] += 1
    return {
        "valid": bool(valid and sum(counts.values()) == len(contributions)),
        "counts": {name: int(counts[name]) for name in CONTRIBUTION_CLASSES},
        "completed_units": len(contributions),
    }


def _episode_trace_template(episode_id: int) -> dict[str, Any]:
    return {
        "episode_id": int(episode_id),
        "steps": [],
        "contributions": [],
        "waves": {},
        "persistent_recovery_delays": [],
        "frontier_action_valid": True,
        "primitive_identity_valid": True,
        "classification_valid": True,
        "token_rows": [],
        "contribution_source_tokens": set(),
        "recovery_source_tokens": set(),
        "last_short_set": {},
        "none_start": None,
    }


def _finish_trace(trace: dict[str, Any]) -> dict[str, Any]:
    wave_rows = []
    for index in sorted(trace["waves"]):
        wave = trace["waves"][index]
        active_count = len(wave["active_keys"])
        prewave_short = sum(
            int(value == SHORT) for value in wave["arrival_skills"].values()
        )
        leads = [
            int(wave["arrival"] - value)
            for value in wave["prewave_last_short_set"].values()
            if value is not None
        ]
        wave_rows.append(
            {
                "wave_index": int(index),
                "arrival": int(wave["arrival"]),
                "active_count": active_count,
                "prewave_short_count": prewave_short,
                "prewave_short_share": (
                    float(prewave_short) / float(active_count) if active_count else 0.0
                ),
                "timely_opportunity_owners": sorted(wave["timely_owners"]),
                "timely_opportunity_coverage": (
                    float(len(wave["timely_owners"])) / float(active_count)
                    if active_count
                    else 0.0
                ),
                "within_wave_set_to_short": int(wave["set_to_short_count"]),
                "prewave_short_set_leads": leads,
            }
        )
    classification = classify_short_contributions(trace["contributions"])
    return {
        "episode_id": trace["episode_id"],
        "steps": trace["steps"],
        "contributions": trace["contributions"],
        "contribution_counts": classification["counts"],
        "classification_valid": classification["valid"],
        "waves": wave_rows,
        "persistent_recovery_delays": trace["persistent_recovery_delays"],
        "frontier_action_valid": bool(trace["frontier_action_valid"]),
        "primitive_identity_valid": bool(trace["primitive_identity_valid"]),
        "token_rows": trace["token_rows"],
        "contribution_source_tokens": trace["contribution_source_tokens"],
        "recovery_source_tokens": trace["recovery_source_tokens"],
    }


def replay_behavior_arm(
    *,
    arm: str,
    high_state: Mapping[str, Any],
    episode_ids: Sequence[int],
    batch_size: int,
    device: str | torch.device,
) -> dict[str, Any]:
    """Replay one frozen deterministic arm and capture audit-owned traces."""

    ids = tuple(int(value) for value in episode_ids)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("behavior replay requires distinct episode IDs")
    if arm not in {LEARNED_HIGH_ARM, FROZEN_HIGH_ARM, ORACLE_ARM}:
        raise ValueError("behavior replay arm mismatch")
    if int(batch_size) <= 0:
        raise ValueError("behavior replay batch size must be positive")

    owner = make_model_owner(device)
    load_high_state(owner, high_state)
    before = clone_high_state(owner)
    owner.commitment_model.eval()
    owner.event_critic.eval()
    outcomes: list[dict[str, float]] = []
    finished_traces: list[dict[str, Any]] = []

    with torch.no_grad():
        for start in range(0, len(ids), int(batch_size)):
            batch_ids = ids[start : start + int(batch_size)]
            runtime = SuppliedExecutorVectorRuntime.create(
                arm=arm,
                model_owner=owner,
                episode_ids=batch_ids,
                task_seed=EVALUATION_TASK_SEED,
                deterministic_high=True,
            )
            traces = [_episode_trace_template(value) for value in batch_ids]
            ledger_offsets = [0 for _ in batch_ids]
            for time in range(HORIZON):
                pre_rows: list[dict[str, Any]] = []
                for index, (core, transaction, adapter) in enumerate(
                    zip(runtime.cores, runtime.current_transactions, runtime.collector.envs)
                ):
                    if transaction is None or adapter.environment is None:
                        raise RuntimeError("behavior replay lost an active boundary")
                    environment = adapter.environment
                    wave = deepcopy(environment.current_wave)
                    active_order = tuple(int(key) for key in environment.active_keys)
                    pre_lifecycles = {
                        key: (
                            int(environment.lifecycles[key].short_streak),
                            bool(environment.lifecycles[key].contributed_current_wave),
                        )
                        for key in active_order
                    }
                    pre_rows.append(
                        {
                            "transaction": deepcopy(transaction),
                            "membership_events": _membership_events_from_transaction(
                                transaction
                            ),
                            "pre_policy_skills": _pre_policy_skills(core, transaction),
                            "active_order": active_order,
                            "wave": wave,
                            "pre_lifecycles": pre_lifecycles,
                            "pre_persistent_owner": environment.persistent_owner,
                            "pre_wave_completed": (
                                0 if wave is None else int(wave.completed_work)
                            ),
                            "ledger_offset": ledger_offsets[index],
                        }
                    )
                    trace = traces[index]
                    if wave is not None and int(wave.arrival_time) == time:
                        arrival_skills = pre_rows[-1]["pre_policy_skills"]
                        trace["waves"][int(wave.index)] = {
                            "arrival": time,
                            "active_keys": active_order,
                            "arrival_skills": dict(arrival_skills),
                            "set_events": defaultdict(list),
                            "timely_owners": set(),
                            "set_to_short_count": 0,
                            "prewave_last_short_set": {
                                key: trace["last_short_set"].get(key)
                                for key, value in arrival_skills.items()
                                if value == SHORT
                            },
                        }
                runtime.advance_one()

                for index, (core, adapter, prepared) in enumerate(
                    zip(runtime.cores, runtime.collector.envs, pre_rows)
                ):
                    if adapter.environment is None:
                        raise RuntimeError("behavior replay lost its environment")
                    environment = adapter.environment
                    trace = traces[index]
                    decision = dict(runtime.decision_trace[index][-1])
                    primitive = {
                        int(key): int(value)
                        for key, value in runtime.primitive_action_trace[index][-1].items()
                    }
                    token_rows = list(core.high_ledger[prepared["ledger_offset"] :])
                    ledger_offsets[index] = len(core.high_ledger)
                    frontier = tuple(int(value) for value in decision["frontier"])
                    expected = dict(prepared["pre_policy_skills"])
                    for row in token_rows:
                        row_key = int(row.owner_lifecycle_key)
                        trace["frontier_action_valid"] &= (
                            row_key in frontier
                            and row_key in prepared["active_order"]
                            and bool(np.asarray(row.exact_legal_mask, dtype=bool).all())
                        )
                        expected[row_key] = int(row.combined_action)
                    trace["primitive_identity_valid"] &= (
                        set(primitive) == set(expected)
                        and all(expected[key] == primitive[key] for key in primitive)
                    )

                    wave = prepared["wave"]
                    wave_context = (
                        None
                        if wave is None
                        else trace["waves"].get(int(wave.index))
                    )
                    membership_boundary = bool(prepared["membership_events"])
                    for row in token_rows:
                        key = int(row.owner_lifecycle_key)
                        token_key = (
                            int(row.physical_event_time),
                            key,
                            int(row.token_position),
                        )
                        event = {
                            "time": int(row.physical_event_time),
                            "owner": key,
                            "frontier_size": len(row.frontier),
                            "token_position": int(row.token_position),
                            "action": int(row.combined_action),
                            "action_kind": str(row.action_kind),
                            "membership_boundary": membership_boundary,
                            "token_key": token_key,
                        }
                        trace["token_rows"].append(row)
                        if row.action_kind == "SET" and int(row.combined_action) == SHORT:
                            trace["last_short_set"][key] = time
                            if wave_context is not None:
                                wave_context["set_events"][key].append(event)
                                wave_context["set_to_short_count"] += 1
                    if wave_context is not None and time <= int(wave.arrival_time) + 2:
                        wave_context["timely_owners"].update(frontier)

                    if wave is not None and wave_context is not None:
                        slots = int(wave.required_work) - int(prepared["pre_wave_completed"])
                        for key in prepared["active_order"]:
                            streak, contributed = prepared["pre_lifecycles"][key]
                            qualifies = (
                                not contributed
                                and primitive[key] == SHORT
                                and streak + 1 >= SHORT_STREAK_TARGET
                            )
                            if not qualifies or slots <= 0:
                                continue
                            slots -= 1
                            events = wave_context["set_events"].get(key, [])
                            source_event = events[-1] if events else None
                            contribution_class = _classify_source_event(
                                arrival_skill=wave_context["arrival_skills"].get(key),
                                source_event=source_event,
                            )
                            contribution = {
                                "episode_id": trace["episode_id"],
                                "wave_index": int(wave.index),
                                "time": time,
                                "owner": key,
                                "class": contribution_class,
                                "source_token": (
                                    None
                                    if source_event is None
                                    else source_event["token_key"]
                                ),
                            }
                            trace["contributions"].append(contribution)
                            if source_event is not None:
                                trace["contribution_source_tokens"].add(
                                    source_event["token_key"]
                                )

                    pre_owner = prepared["pre_persistent_owner"]
                    if pre_owner is None and trace["none_start"] is None:
                        trace["none_start"] = time
                    post_owner = environment.persistent_owner
                    if post_owner is not None and trace["none_start"] is not None:
                        trace["persistent_recovery_delays"].append(
                            int(time - trace["none_start"])
                        )
                        for row in token_rows:
                            if (
                                int(row.owner_lifecycle_key) == int(post_owner)
                                and row.action_kind == "SET"
                                and int(row.combined_action) == PERSIST
                            ):
                                trace["recovery_source_tokens"].add(
                                    (
                                        int(row.physical_event_time),
                                        int(row.owner_lifecycle_key),
                                        int(row.token_position),
                                    )
                                )
                        trace["none_start"] = None
                    elif post_owner is None and trace["none_start"] is None:
                        trace["none_start"] = time

                    trace["steps"].append(
                        {
                            "time": time,
                            "membership_events": prepared["membership_events"],
                            "active_keys": prepared["active_order"],
                            "frontier": frontier,
                            "primitive_actions": primitive,
                            "wave_index": None if wave is None else int(wave.index),
                            "wave_arrival": (
                                None if wave is None else int(wave.arrival_time)
                            ),
                        }
                    )

            outcomes.extend(runtime.outcomes())
            finished_traces.extend(_finish_trace(trace) for trace in traces)
            runtime.close()

    after = clone_high_state(owner)
    return {
        "arm": arm,
        "episode_ids": list(ids),
        "outcomes": outcomes,
        "traces": finished_traces,
        "persistent": [row["persistent"] for row in outcomes],
        "short": [row["short"] for row in outcomes],
        "utility": [row["utility"] for row in outcomes],
        "persistent_mean": float(np.mean([row["persistent"] for row in outcomes])),
        "short_mean": float(np.mean([row["short"] for row in outcomes])),
        "utility_mean": float(np.mean([row["utility"] for row in outcomes])),
        "optimizer_steps": 0,
        "high_tensor_drift": high_state_l2_drift(before, after),
        "no_grad": True,
    }


def materialize_exogenous_frontiers(
    replay: Mapping[str, Any],
) -> tuple[OpportunityAuthorityLedger, ...]:
    """Materialize immutable solver ledgers from a completed causal replay."""

    ledgers: list[OpportunityAuthorityLedger] = []
    for trace in replay["traces"]:
        steps = list(trace["steps"])
        if len(steps) != HORIZON:
            raise ValueError("frontier materialization requires a complete episode")
        episode_id = int(trace["episode_id"])
        task = make_clean_process_dynamic_roster_ledger(
            episode_id, master_seed=EVALUATION_TASK_SEED
        )
        active = tuple(tuple(int(key) for key in row["active_keys"]) for row in steps)
        membership = tuple(tuple(row["membership_events"]) for row in steps)
        frontiers = tuple(tuple(int(key) for key in row["frontier"]) for row in steps)
        presentation = tuple(
            tuple(
                sorted(
                    active[time],
                    key=lambda key: float(task.presentation_priorities[time, key]),
                )
            )
            for time in range(HORIZON)
        )
        ledger = OpportunityAuthorityLedger(
            episode_id=episode_id,
            horizon=HORIZON,
            lifecycle_count=MAX_LIFECYCLES,
            persistent_target=PERSISTENT_TARGET,
            short_window=SHORT_WINDOW,
            short_streak_target=SHORT_STREAK_TARGET,
            membership_events=membership,
            active_keys=active,
            frontiers=frontiers,
            wave_arrivals=tuple(int(value) for value in task.wave_arrivals),
            owner_priorities=tuple(
                tuple(float(value) for value in task.owner_priorities[time])
                for time in range(HORIZON)
            ),
            presentation_orders=presentation,
        )
        ledger.validate()
        if ledger.short_required_total != EXPECTED_SHORT_REQUIREMENT:
            raise ValueError("materialized ledger short requirement mismatch")
        ledgers.append(ledger)
    return tuple(ledgers)


def _frontier_signatures(replay: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(
        tuple(tuple(step["frontier"]) for step in trace["steps"])
        for trace in replay["traces"]
    )


def verify_current_result_reproduction(
    *,
    replay: Mapping[str, Any],
    source_arm: Mapping[str, Any],
    tolerance: float = 1.0e-12,
) -> dict[str, Any]:
    source_ids = [int(value) for value in source_arm["episode_ids"]]
    index = {episode_id: row for row, episode_id in enumerate(source_ids)}
    requested = [int(value) for value in replay["episode_ids"]]
    if any(value not in index for value in requested):
        raise ValueError("source result omits a requested episode")
    errors: dict[str, float] = {}
    for metric in ("persistent", "short", "utility"):
        expected = np.asarray(
            [source_arm[metric][index[value]] for value in requested],
            dtype=np.float64,
        )
        actual = np.asarray(replay[metric], dtype=np.float64)
        errors[metric] = float(np.max(np.abs(actual - expected)))
    return {
        "valid": bool(max(errors.values()) <= float(tolerance)),
        "max_absolute_error": errors,
        "tolerance": float(tolerance),
        "episode_ids": requested,
    }


def paired_contribution_dominance(
    learned: Mapping[str, Any],
    oracle: Mapping[str, Any],
) -> dict[str, Any]:
    if learned["episode_ids"] != oracle["episode_ids"]:
        raise ValueError("contribution comparison requires paired episode IDs")
    learned_rows = {
        int(trace["episode_id"]): trace["contribution_counts"]
        for trace in learned["traces"]
    }
    oracle_rows = {
        int(trace["episode_id"]): trace["contribution_counts"]
        for trace in oracle["traces"]
    }
    ids = [int(value) for value in learned["episode_ids"]]
    excess = np.asarray(
        [
            [
                int(learned_rows[episode_id][name])
                - int(oracle_rows[episode_id][name])
                for name in CONTRIBUTION_CLASSES
            ]
            for episode_id in ids
        ],
        dtype=np.float64,
    )
    pairwise: dict[str, dict[str, list[float]]] = {}
    decisive: list[str] = []
    for left_index, left in enumerate(CONTRIBUTION_CLASSES):
        pairwise[left] = {}
        all_positive = True
        for right_index, right in enumerate(CONTRIBUTION_CLASSES):
            if left == right:
                continue
            ci = paired_bootstrap_ci95(
                excess[:, left_index] - excess[:, right_index],
                seed=BOOTSTRAP_SEED,
            )
            pairwise[left][right] = ci
            all_positive &= float(ci[0]) > 0.0
        if all_positive:
            decisive.append(left)
    return {
        "episode_ids": ids,
        "learned_minus_oracle_mean": {
            name: float(excess[:, index].mean())
            for index, name in enumerate(CONTRIBUTION_CLASSES)
        },
        "pairwise_bootstrap_ci95": pairwise,
        "decisive_classes": decisive,
        "decisive_class": decisive[0] if len(decisive) == 1 else None,
        "unique_decisive_class": len(decisive) == 1,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_resamples": BOOTSTRAP_REPETITIONS,
    }


def read_working_vs_initial_distributions(
    *,
    learned_replay: Mapping[str, Any],
    learned_high_state: Mapping[str, Any],
    device: str | torch.device,
) -> dict[str, Any]:
    """Read F1 working/initial probabilities without sampling or state change."""

    owner = make_model_owner(device)
    load_high_state(owner, learned_high_state)
    owner.commitment_model.eval()
    owner.event_critic.eval()
    before = clone_high_state(owner)
    rows: list[dict[str, Any]] = []
    with torch.no_grad():
        for trace in learned_replay["traces"]:
            associated = set(trace["contribution_source_tokens"]) | set(
                trace["recovery_source_tokens"]
            )
            for token in trace["token_rows"]:
                if len(token.frontier) <= 1 or int(token.token_position) <= 0:
                    continue
                working = owner.replay_token_distribution(
                    token, summary_source="working"
                )
                initial = owner.replay_token_distribution(
                    token, summary_source="initial"
                )
                token_key = (
                    int(token.physical_event_time),
                    int(token.owner_lifecycle_key),
                    int(token.token_position),
                )
                owner_index = token.active_lifecycle_keys.index(
                    token.owner_lifecycle_key
                )
                skills = np.asarray(token.pre_token_working_skills, dtype=np.int64)
                duplicate_persist = any(
                    int(value) == PERSIST
                    for index, value in enumerate(skills)
                    if index != owner_index
                )
                wave_active = bool(
                    np.asarray(token.active_observations, dtype=np.float64)[
                        owner_index, 4
                    ]
                    > 0.5
                )
                missing_short = wave_active and int(np.sum(skills == SHORT)) < max(
                    0, len(skills) - 1
                )
                duplicate_reduction = (
                    float(initial[PERSIST] - working[PERSIST])
                    if duplicate_persist
                    else 0.0
                )
                missing_short_increase = (
                    float(working[SHORT] - initial[SHORT]) if missing_short else 0.0
                )
                directional = duplicate_reduction + missing_short_increase
                rows.append(
                    {
                        "episode_id": int(trace["episode_id"]),
                        "time": int(token.physical_event_time),
                        "owner": int(token.owner_lifecycle_key),
                        "frontier_size": len(token.frontier),
                        "token_position": int(token.token_position),
                        "tv": float(0.5 * np.abs(working - initial).sum()),
                        "duplicate_persist": bool(duplicate_persist),
                        "duplicate_persist_reduction": duplicate_reduction,
                        "missing_short": bool(missing_short),
                        "missing_short_increase": missing_short_increase,
                        "directional_shift": directional,
                        "completion_or_recovery_associated": token_key in associated,
                    }
                )
    after = clone_high_state(owner)
    associated_rows = [
        row for row in rows if row["completion_or_recovery_associated"]
    ]
    positive_associated = [
        row for row in associated_rows if float(row["directional_shift"]) > 0.0
    ]

    def mean(name: str, selected: Sequence[Mapping[str, Any]]) -> float:
        return (
            float(np.mean([float(row[name]) for row in selected]))
            if selected
            else 0.0
        )

    return {
        "row_count": len(rows),
        "mean_tv": mean("tv", rows),
        "mean_duplicate_persist_reduction": mean(
            "duplicate_persist_reduction",
            [row for row in rows if row["duplicate_persist"]],
        ),
        "mean_missing_short_increase": mean(
            "missing_short_increase", [row for row in rows if row["missing_short"]]
        ),
        "associated_row_count": len(associated_rows),
        "positive_associated_row_count": len(positive_associated),
        "associated_directional_mean": mean("directional_shift", associated_rows),
        "positive_directional_shift": bool(
            associated_rows and mean("directional_shift", associated_rows) > 0.0
        ),
        "completion_or_recovery_association": bool(positive_associated),
        "optimizer_steps": 0,
        "high_tensor_drift": high_state_l2_drift(before, after),
        "rows": rows,
    }


def simulate_frontier_action_plan(
    ledger: OpportunityAuthorityLedger,
    actions_by_time: Sequence[Mapping[int, int]],
) -> tuple[int, int]:
    """Apply one legal frontier action plan through the audit transition model."""

    ledger.validate()
    if len(actions_by_time) != ledger.horizon:
        raise ValueError("frontier action plan length mismatch")
    control = _DPControl(
        skills=tuple(-1 for _ in range(ledger.lifecycle_count)),
        persistent_owner=-1,
        wave_index=-1,
        wave_completed=0,
        short_streaks=tuple(0 for _ in range(ledger.lifecycle_count)),
        contributed_mask=0,
    )
    persistent = 0
    short = 0
    for time, raw_actions in enumerate(actions_by_time):
        prepared = _apply_membership(control, ledger.membership_events[time])
        prepared = _open_wave(prepared, time=time, ledger=ledger)
        actions = {int(key): int(value) for key, value in raw_actions.items()}
        if set(actions) != set(ledger.frontiers[time]):
            raise ValueError("frontier action plan changes a non-frontier owner")
        skills = list(prepared.skills)
        for key, action in actions.items():
            if action not in (IDLE, PERSIST, SHORT):
                raise ValueError("frontier action plan uses an invalid action")
            skills[key] = action
        selected = _DPControl(
            skills=tuple(skills),
            persistent_owner=prepared.persistent_owner,
            wave_index=prepared.wave_index,
            wave_completed=prepared.wave_completed,
            short_streaks=prepared.short_streaks,
            contributed_mask=prepared.contributed_mask,
        )
        control, persistent_inc, short_inc = _primitive_transition(
            selected, time=time, ledger=ledger
        )
        persistent = min(ledger.persistent_target, persistent + persistent_inc)
        short += short_inc
    return persistent, short


def full_step_constructive_control(episode_id: int = 0) -> dict[str, Any]:
    """Show that full-step frontier authority reproduces constructive behavior."""

    task = make_clean_process_dynamic_roster_ledger(
        int(episode_id), master_seed=EVALUATION_TASK_SEED
    )
    environment = CleanProcessDynamicRosterEnv(task)
    active_rows: list[tuple[int, ...]] = []
    event_rows: list[tuple[AuditMembershipEvent, ...]] = []
    action_rows: list[dict[int, int]] = []
    for _time in range(HORIZON):
        view = environment.observe()
        change = view.membership_change
        events = tuple(
            event
            for event in (
                AuditMembershipEvent(JOIN, tuple(change.joined)),
                AuditMembershipEvent(TEMPORARY_LEAVE, tuple(change.temporarily_left)),
                AuditMembershipEvent(REJOIN, tuple(change.rejoined)),
                AuditMembershipEvent(TERMINAL_LEAVE, tuple(change.terminally_left)),
            )
            if event.keys
        )
        actions = constructive_actions(environment, view)
        active_rows.append(tuple(int(key) for key in view.active_keys))
        event_rows.append(events)
        action_rows.append({int(key): int(value) for key, value in actions.items()})
        environment.step(actions)
    ledger = OpportunityAuthorityLedger(
        episode_id=int(episode_id),
        horizon=HORIZON,
        lifecycle_count=MAX_LIFECYCLES,
        persistent_target=PERSISTENT_TARGET,
        short_window=SHORT_WINDOW,
        short_streak_target=SHORT_STREAK_TARGET,
        membership_events=tuple(event_rows),
        active_keys=tuple(active_rows),
        frontiers=tuple(active_rows),
        wave_arrivals=tuple(int(value) for value in task.wave_arrivals),
        owner_priorities=tuple(
            tuple(float(value) for value in task.owner_priorities[time])
            for time in range(HORIZON)
        ),
        presentation_orders=tuple(active_rows),
    )
    actual = (int(environment.persistent_units), int(environment.short_completed_total))
    replayed = simulate_frontier_action_plan(ledger, action_rows)
    return {
        "valid": actual == replayed,
        "environment": list(actual),
        "audit_simulator": list(replayed),
    }


def load_frozen_audit_inputs(
    *,
    update_zero_path: str | Path,
    latest_path: str | Path,
    device: str | torch.device,
) -> dict[str, Any]:
    update_path = Path(update_zero_path)
    learned_path = Path(latest_path)
    frozen = torch.load(update_path, map_location=device, weights_only=False)
    latest = torch.load(learned_path, map_location=device, weights_only=False)
    if not isinstance(frozen, Mapping) or set(frozen) != {
        "commitment_model",
        "event_critic",
    }:
        raise ValueError("update-zero checkpoint schema mismatch")
    if not isinstance(latest, Mapping):
        raise ValueError("latest high-only checkpoint is not a mapping")
    required = {
        "checkpoint_schema_version",
        "package",
        "package_schema_version",
        "architecture_mode",
        "runtime_mode",
        "arm",
        "seed_contract",
        "shape_contract",
        "model_state",
        "optimizer_state",
        "runtime_cores",
        "collector_snapshot",
        "current_transactions",
        "runtime_diagnostics",
        "counters",
        "torch_rng_state",
        "event_architecture_schema_version",
    }
    if set(latest) != required:
        raise ValueError("latest high-only checkpoint field mismatch")
    counters = dict(latest["counters"])
    seed_contract = dict(latest["seed_contract"])
    exact = bool(
        latest["architecture_mode"] == "f1"
        and latest["runtime_mode"] == "supplied_executor"
        and latest["arm"] == LEARNED_HIGH_ARM
        and int(counters["high_optimizer_steps"]) == 1_000
        and int(counters["environment_transitions"]) == 320_000
        and int(counters["episodes_completed"]) == 4_000
        and seed_contract["evaluation_task"] == EVALUATION_TASK_SEED
        and seed_contract["opportunity_frontier"] == OPPORTUNITY_FRONTIER_SEED
        and seed_contract["opportunity_stream"] == OPPORTUNITY_STREAM_ID
        and seed_contract["frontier_stream"] == FRONTIER_STREAM_ID
        and seed_contract["action"] == ACTION_SEED
        and seed_contract["bootstrap"] == BOOTSTRAP_SEED
    )
    if not exact:
        raise ValueError("frozen audit checkpoint contract mismatch")
    return {
        "frozen_high_state": deepcopy(dict(frozen)),
        "learned_high_state": deepcopy(dict(latest["model_state"])),
        "checkpoint_contract_exact": True,
        "source_optimizer_steps": int(counters["high_optimizer_steps"]),
        "audit_optimizer_steps": 0,
        "update_zero_path": str(update_path.resolve()),
        "latest_path": str(learned_path.resolve()),
    }


def _public_trace(trace: Mapping[str, Any]) -> dict[str, Any]:
    steps = []
    for row in trace["steps"]:
        steps.append(
            {
                **{key: value for key, value in row.items() if key != "membership_events"},
                "membership_events": [
                    {"kind": event.kind, "keys": list(event.keys)}
                    for event in row["membership_events"]
                ],
            }
        )
    return {
        "episode_id": int(trace["episode_id"]),
        "steps": steps,
        "contributions": [
            {
                **dict(row),
                "source_token": (
                    None if row["source_token"] is None else list(row["source_token"])
                ),
            }
            for row in trace["contributions"]
        ],
        "contribution_counts": dict(trace["contribution_counts"]),
        "classification_valid": bool(trace["classification_valid"]),
        "waves": deepcopy(trace["waves"]),
        "persistent_recovery_delays": list(trace["persistent_recovery_delays"]),
        "frontier_action_valid": bool(trace["frontier_action_valid"]),
        "primitive_identity_valid": bool(trace["primitive_identity_valid"]),
    }


def _public_replay(replay: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(replay[key])
        for key in (
            "arm",
            "episode_ids",
            "outcomes",
            "persistent",
            "short",
            "utility",
            "persistent_mean",
            "short_mean",
            "utility_mean",
            "optimizer_steps",
            "high_tensor_drift",
            "no_grad",
        )
    } | {"traces": [_public_trace(trace) for trace in replay["traces"]]}


def classify_audit_result(
    *,
    implementation_valid: bool,
    hindsight: Mapping[str, Any] | None,
    dominance: Mapping[str, Any],
    working_initial: Mapping[str, Any],
) -> str:
    if not implementation_valid:
        return INVALID_STATUS
    if hindsight is None:
        raise ValueError("valid formal audit requires a hindsight result")
    if float(hindsight["g_h"]) < REGISTERED_FLOOR:
        return UNREACHABLE_STATUS
    decisive = dominance["decisive_class"]
    directional = bool(working_initial["positive_directional_shift"])
    associated = bool(working_initial["completion_or_recovery_association"])
    if decisive == "PREWAVE_SHORT" and not (directional and associated):
        return PREPOSITION_STATUS
    if (
        decisive == "POSTWAVE_MULTIOWNER_LATER"
        and directional
        and associated
    ):
        return PREFIX_STATUS
    return MIXED_STATUS


def run_read_only_opportunity_authority_and_use_audit(
    *,
    source_result_path: str | Path,
    update_zero_path: str | Path,
    latest_path: str | Path,
    device: str | torch.device,
    episode_ids: Sequence[int] | None = None,
    batch_size: int = 16,
    solve_hindsight: bool = True,
    formal: bool = True,
) -> dict[str, Any]:
    """Run the accepted evaluation-only audit without optimizer construction."""

    stage_started = time.perf_counter()
    source = json.loads(Path(source_result_path).read_text(encoding="utf-8"))
    ids = (
        tuple(range(FORMAL_EVAL_EPISODES))
        if episode_ids is None
        else tuple(int(value) for value in episode_ids)
    )
    if formal and ids != tuple(range(FORMAL_EVAL_EPISODES)):
        raise ValueError("formal audit requires evaluation episode IDs 0..255")
    source_header_exact = bool(
        source.get("status")
        == "INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT"
        and source.get("formal_evidence") is True
        and source.get("implementation_valid") is True
        and source["evaluation"]["learned"]["episode_ids"]
        == source["evaluation"]["frozen"]["episode_ids"]
        == source["evaluation"]["oracle"]["episode_ids"]
        == list(range(FORMAL_EVAL_EPISODES))
        and int(source["contract"]["actual"]["high_optimizer_steps"]) == 1_000
        and int(source["training"]["counts"]["low_optimizer_steps"]) == 0
        and int(source["contract"]["formal"]["bootstrap_resamples"])
        == BOOTSTRAP_REPETITIONS
    )
    if not source_header_exact:
        raise ValueError("frozen source-result contract mismatch")
    inputs = load_frozen_audit_inputs(
        update_zero_path=update_zero_path,
        latest_path=latest_path,
        device=device,
    )
    stage_wall_seconds = {"input_validation": time.perf_counter() - stage_started}
    stage_started = time.perf_counter()
    learned = replay_behavior_arm(
        arm=LEARNED_HIGH_ARM,
        high_state=inputs["learned_high_state"],
        episode_ids=ids,
        batch_size=batch_size,
        device=device,
    )
    stage_wall_seconds["learned_replay"] = time.perf_counter() - stage_started
    stage_started = time.perf_counter()
    frozen = replay_behavior_arm(
        arm=FROZEN_HIGH_ARM,
        high_state=inputs["frozen_high_state"],
        episode_ids=ids,
        batch_size=batch_size,
        device=device,
    )
    stage_wall_seconds["frozen_replay"] = time.perf_counter() - stage_started
    stage_started = time.perf_counter()
    oracle = replay_behavior_arm(
        arm=ORACLE_ARM,
        high_state=inputs["learned_high_state"],
        episode_ids=ids,
        batch_size=batch_size,
        device=device,
    )
    stage_wall_seconds["oracle_replay"] = time.perf_counter() - stage_started
    reference = source["evaluation"]
    reproduction = {
        "learned": verify_current_result_reproduction(
            replay=learned, source_arm=reference["learned"]
        ),
        "frozen": verify_current_result_reproduction(
            replay=frozen, source_arm=reference["frozen"]
        ),
        "oracle": verify_current_result_reproduction(
            replay=oracle, source_arm=reference["oracle"]
        ),
    }
    frontier_equal = (
        _frontier_signatures(learned)
        == _frontier_signatures(frozen)
        == _frontier_signatures(oracle)
    )
    ledgers = materialize_exogenous_frontiers(learned)
    stage_started = time.perf_counter()
    hindsight = solve_frontier_hindsight_pareto(ledgers) if solve_hindsight else None
    stage_wall_seconds["hindsight_solver"] = time.perf_counter() - stage_started
    stage_started = time.perf_counter()
    dominance = paired_contribution_dominance(learned, oracle)
    working_initial = read_working_vs_initial_distributions(
        learned_replay=learned,
        learned_high_state=inputs["learned_high_state"],
        device=device,
    )
    tiny_dp = solve_frontier_hindsight_episode(make_tiny_authority_ledger())
    tiny_brute = solve_frontier_hindsight_bruteforce(make_tiny_authority_ledger())
    full_step = full_step_constructive_control(ids[0])
    stage_wall_seconds["behavior_diagnostics_and_controls"] = (
        time.perf_counter() - stage_started
    )
    traces = [*learned["traces"], *frozen["traces"], *oracle["traces"]]
    audit = {
        "source_result_exact": all(row["valid"] for row in reproduction.values()),
        "frontier_order_ledgers_equal": frontier_equal,
        "frontier_action_constraint": all(
            bool(trace["frontier_action_valid"]) for trace in traces
        ),
        "primitive_action_identity": all(
            bool(trace["primitive_identity_valid"]) for trace in traces
        ),
        "future_ledger_solver_only": True,
        "tiny_dp_bruteforce_equal": (
            tiny_dp.outcome_pairs == tiny_brute.outcome_pairs
        ),
        "full_step_constructive_reproduced": bool(full_step["valid"]),
        "unique_contribution_classification": all(
            bool(trace["classification_valid"]) for trace in traces
        ),
        "zero_optimizer_steps": (
            int(learned["optimizer_steps"])
            == int(frozen["optimizer_steps"])
            == int(oracle["optimizer_steps"])
            == int(working_initial["optimizer_steps"])
            == int(inputs["audit_optimizer_steps"])
            == 0
        ),
        "zero_parameter_drift": max(
            float(learned["high_tensor_drift"]),
            float(frozen["high_tensor_drift"]),
            float(oracle["high_tensor_drift"]),
            float(working_initial["high_tensor_drift"]),
        )
        == 0.0,
        "checkpoint_contract_exact": bool(inputs["checkpoint_contract_exact"]),
        "frozen_source_header_exact": source_header_exact,
        "registered_headers_exact": bool(
            EVALUATION_TASK_SEED == 97_057
            and OPPORTUNITY_FRONTIER_SEED == 77_057
            and OPPORTUNITY_STREAM_ID == 0
            and FRONTIER_STREAM_ID == 1
            and ACTION_SEED == 87_057
            and BOOTSTRAP_SEED == 107_057
            and BOOTSTRAP_REPETITIONS == 10_000
            and HORIZON == 80
            and EXPECTED_SHORT_REQUIREMENT == 24
            and SHORT_WINDOW == 4
            and SHORT_STREAK_TARGET == 2
        ),
    }
    implementation_valid = all(bool(value) for value in audit.values())
    scientific_status = (
        classify_audit_result(
            implementation_valid=implementation_valid,
            hindsight=hindsight,
            dominance=dominance,
            working_initial=working_initial,
        )
        if solve_hindsight
        else None
    )
    status = scientific_status if formal else (
        "SMOKE_COMPLETE" if implementation_valid else INVALID_STATUS
    )
    hindsight_public = None
    if hindsight is not None:
        hindsight_public = {
            key: deepcopy(value)
            for key, value in hindsight.items()
            if key != "episode_sets"
        }
    return {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "package": PACKAGE_NAME,
        "status": status,
        "scientific_status": scientific_status,
        "formal_evidence": bool(formal),
        "implementation_valid": implementation_valid,
        "audit": audit,
        "contract": {
            "episode_ids": list(ids),
            "horizon": HORIZON,
            "floor": REGISTERED_FLOOR,
            "opportunity_gap": [1, 19],
            "wave_candidates": [list(values) for values in WAVE_CANDIDATES],
            "short_window": SHORT_WINDOW,
            "short_streak_target": SHORT_STREAK_TARGET,
            "short_required_total": EXPECTED_SHORT_REQUIREMENT,
            "seeds": {
                "evaluation_task": EVALUATION_TASK_SEED,
                "opportunity_frontier": OPPORTUNITY_FRONTIER_SEED,
                "opportunity_stream": OPPORTUNITY_STREAM_ID,
                "frontier_stream": FRONTIER_STREAM_ID,
                "action": ACTION_SEED,
                "bootstrap": BOOTSTRAP_SEED,
            },
            "bootstrap_resamples": BOOTSTRAP_REPETITIONS,
            "optimizer_steps": {"high": 0, "low": 0},
            "checkpoints": {
                "update_zero": inputs["update_zero_path"],
                "latest_high_only": inputs["latest_path"],
            },
        },
        "reproduction": reproduction,
        "hindsight": hindsight_public,
        "behavior_use": {
            "learned": _public_replay(learned),
            "frozen": _public_replay(frozen),
            "oracle": _public_replay(oracle),
            "dominance": dominance,
        },
        "working_vs_initial": working_initial,
        "controls": {
            "tiny_dp_outcomes": [list(value) for value in tiny_dp.outcome_pairs],
            "tiny_bruteforce_outcomes": [
                list(value) for value in tiny_brute.outcome_pairs
            ],
            "full_step_constructive": full_step,
        },
        "stage_wall_seconds": stage_wall_seconds,
        "runner_selects_successor": False,
    }
