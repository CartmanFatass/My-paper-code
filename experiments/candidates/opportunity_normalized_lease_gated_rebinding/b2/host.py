"""Isolated B2 two-agent host, boundary semantics, and auditable ledgers."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import time
from typing import Protocol

import numpy as np

from .config import ACTIONS, ARMS, HORIZON, IID_SCHEDULE, LEASE_TICKS, ROLES
from .rng import counter_bernoulli, counter_bit, counter_u64, counter_uniform


def schedule_intervals(name: str) -> tuple[int, ...]:
    if name == IID_SCHEDULE:
        raise ValueError("IID intervals are drawn only after the current boundary")
    if name.startswith("CONST-"):
        return (int(name.split("-")[1]),)
    if name.startswith("MID-"):
        parts = name.split("-")
        return int(parts[1]), int(parts[3])
    raise ValueError(f"unknown B2 schedule: {name}")


def schedule_boundaries(name: str, horizon: int = HORIZON) -> tuple[int, ...]:
    intervals = schedule_intervals(name)
    if len(intervals) == 1:
        return tuple(range(0, horizon, intervals[0]))
    boundaries: list[int] = []
    for start, end, interval in ((0, horizon // 2, intervals[0]), (horizon // 2, horizon, intervals[1])):
        tick = start
        while tick < end:
            boundaries.append(tick)
            tick = min(tick + interval, end)
    return tuple(boundaries)


@dataclass(frozen=True)
class ExogenousEpisode:
    seed: int
    episode_index: int
    namespace: str
    schedule: str
    mode: np.ndarray
    sensors: np.ndarray
    preroll: np.ndarray
    initial_bindings: tuple[int, int]
    initial_plan_ages: tuple[int, int]
    safety_agent: int | None
    safety_tick: int | None
    routine_boundaries: tuple[int, ...]


def generate_episode(
    *, seed: int, episode_index: int, namespace: str, schedule: str,
    horizon: int = HORIZON, safety: bool = False,
) -> ExogenousEpisode:
    mode_value = counter_bit("INITIAL_MODE", namespace, seed, episode_index)
    mode = np.empty(horizon, dtype=np.int8)
    sensors = np.empty((horizon, 2), dtype=np.int8)
    for tick in range(horizon):
        if counter_uniform("MODE_FLIP", namespace, seed, episode_index, tick) < 1.0 / 48.0:
            mode_value ^= 1
        mode[tick] = mode_value
        for role in range(2):
            sensors[tick, role] = mode_value ^ counter_bernoulli(
                0.15, "SENSOR_NOISE", namespace, seed, episode_index, tick, role,
            )
    preroll = np.empty((8, 2), dtype=np.int8)
    for tick in range(8):
        for role in range(2):
            preroll[tick, role] = int(mode[0]) ^ counter_bernoulli(
                0.15, "SENSOR_PREROLL", namespace, seed, episode_index, tick, role,
            )
    rotation = counter_u64("INITIAL_AGE_ROTATION", namespace, seed) % 4
    ages = tuple((0, 8, 16, 24)[(episode_index + 2 * role + rotation) % 4] for role in range(2))
    safety_agent = episode_index % 2 if safety else None
    safety_tick = None
    if safety:
        safety_rotation = counter_u64("SAFETY_TICK_ROTATION", namespace, seed) % 192
        safety_tick = 32 + ((safety_rotation + 12 * episode_index) % 192)
    return ExogenousEpisode(
        seed=seed, episode_index=episode_index, namespace=namespace, schedule=schedule,
        mode=mode, sensors=sensors, preroll=preroll,
        initial_bindings=(
            counter_bit("INITIAL_BINDING", namespace, seed, episode_index, 0),
            counter_bit("INITIAL_BINDING", namespace, seed, episode_index, 1),
        ),
        initial_plan_ages=ages, safety_agent=safety_agent, safety_tick=safety_tick,
        routine_boundaries=((0,) if schedule == IID_SCHEDULE else schedule_boundaries(schedule, horizon)),
    )


class LearnerPolicy(Protocol):
    def policy(self, features: np.ndarray, exposure: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]: ...
    def value(self, features: np.ndarray) -> float: ...
    def joint_log_probability(
        self, features: np.ndarray, exposure: np.ndarray,
        actions: np.ndarray, policy_mask: np.ndarray,
    ) -> float: ...


@dataclass
class BoundaryTrainingRecord:
    tick: int
    actor_features: np.ndarray
    critic_features: np.ndarray
    exposure: np.ndarray
    actions: np.ndarray
    policy_mask: np.ndarray
    behavior_joint_log_prob: float
    behavior_value: float
    duration: int = 0
    segment_reward: float = 0.0


@dataclass(frozen=True)
class BoundaryIdentity:
    episode_id: str
    agent_role: str
    owner_epoch: int
    own_boundary_index: int
    behavior_version: str
    cause: str
    action: str
    initial_anchor_action: bool

    @property
    def key(self) -> tuple[str, str, int, int, str]:
        return self.episode_id, self.agent_role, self.owner_epoch, self.own_boundary_index, self.behavior_version


@dataclass
class EpisodeResult:
    arm: str
    schedule: str
    episode_index: int
    normalized_return: float
    service: float
    action_cost: float
    physics_ticks: int
    actor_calls: int
    critic_calls: int
    messages: int
    transmitted_bits: int
    optimizer_behavior_version: str
    routine_boundary_ticks: tuple[int, ...]
    iid_interval_draws: tuple[int, ...]
    iid_draw_records: tuple[tuple[int, int, int, bool], ...]
    iid_terminal_censored_duration: int | None
    poststartup_legal_rows: tuple[int, int]
    poststartup_stochastic_actions: tuple[tuple[int, int, int], tuple[int, int, int]]
    masked_routine_rows: tuple[int, int]
    eligible_exposure: tuple[int, int]
    event_free_survival_rows: tuple[tuple[int, int, bool], ...]
    voluntary_event_ticks: tuple[tuple[int, ...], tuple[int, ...]]
    inter_event_dwells: tuple[tuple[int, ...], tuple[int, ...]]
    rate_rows: tuple[dict[str, object], ...]
    safety_forced_count: int
    safety_tick: int | None
    safety_coincident_routine: bool
    safety_affected_agent: int | None
    safety_expected_action: int | None
    safety_affected_action: int | None
    safety_unaffected_action: int | None
    safety_policy_score_factors: int
    safety_affected_clock_advanced: bool
    safety_unaffected_clock_advanced: bool
    safety_violations: int
    identity_rows: tuple[BoundaryIdentity, ...]
    identity_unique: bool
    reward_service_cost_exact: bool
    segment_ownership_exact: bool
    terminal_boundary_absent: bool
    stale_binding_ticks: int
    plan_age_sum: int
    downtime_ticks: int
    decision_latencies_ns: tuple[int, ...]
    physics_ledger: tuple[tuple[object, ...], ...]
    dummy_call_ledger: tuple[tuple[int, str, int], ...]
    training_records: list[BoundaryTrainingRecord] = field(default_factory=list)


def timing_features(
    *, age: int, lease_expiry: int, busy: int, tick: int, cause: str,
    delta: int, exposure: int,
) -> np.ndarray:
    return np.asarray([
        min(max(age, 0), 64) / 64.0,
        min(max(lease_expiry - tick, 0), LEASE_TICKS) / LEASE_TICKS,
        min(max(busy, 0), 2) / 2.0,
        float(cause == "ROUTINE_CALLBACK"),
        float(cause == "SAFETY_BYPASS"),
        min(max(delta, 0), 32) / 32.0,
        min(max(exposure, 0), 32) / 32.0,
    ], dtype=np.float64)


def critic_features(
    *, mode: int, timing_rows: np.ndarray, bindings: list[int], ages: list[int],
    leases: list[int], busy: list[int], histories: list[deque[int]], tick: int,
) -> np.ndarray:
    # 14 timing + mode + 2 bindings + 2 ages + 2 leases + 2 busy + 16 sensor bits = 39.
    return np.asarray([
        *timing_rows.reshape(-1).tolist(), float(mode), *map(float, bindings),
        *(min(age, 64) / 64.0 for age in ages),
        *(min(max(lease - tick, 0), LEASE_TICKS) / LEASE_TICKS for lease in leases),
        *(min(value, 2) / 2.0 for value in busy),
        *(float(bit) for history in histories for bit in history),
    ], dtype=np.float64)


def eligible_exposure(previous_boundary: int, lease_expiry: int, tick: int) -> int:
    return max(0, tick - max(previous_boundary + 1, lease_expiry) + 1)


def sample_action(event_probability: float, episode: ExogenousEpisode, tick: int, role: int) -> int:
    event_uniform = counter_uniform(
        "ACTION_EVENT_UNIFORM", episode.namespace, episode.seed, episode.episode_index, tick, role,
    )
    if event_uniform >= event_probability:
        return 0
    mark_uniform = counter_uniform(
        "ACTION_MARK_UNIFORM", episode.namespace, episode.seed, episode.episode_index, tick, role,
    )
    return 1 if mark_uniform < 0.5 else 2


def _next_iid_interval(episode: ExogenousEpisode, ordinal: int) -> int:
    uniform = counter_uniform(
        "RAND_IID_NEXT_K", episode.seed, episode.episode_index, ordinal,
    )
    return 4 if uniform < 1.0 / 3.0 else 16 if uniform < 2.0 / 3.0 else 32


def run_episode(
    episode: ExogenousEpisode, *, arm: str, learner: LearnerPolicy,
    collect_training: bool = False, force_keep: bool = False,
    owner_epoch: int = 0, behavior_version: str | None = None,
) -> EpisodeResult:
    if arm not in ARMS:
        raise ValueError(f"unknown B2 arm: {arm}")
    iid = episode.schedule == IID_SCHEDULE
    boundaries = {0} if iid else set(episode.routine_boundaries)
    histories = [deque((int(v) for v in episode.preroll[:, role]), maxlen=8) for role in range(2)]
    bindings = list(episode.initial_bindings)
    ages = list(episode.initial_plan_ages)
    busy = [0, 0]
    leases = [-8, -8]
    previous_boundary = [-8, -8]
    own_boundary_index = [0, 0]
    behavior = behavior_version or f"{arm}:epoch-{owner_epoch}"
    rewards = np.zeros(len(episode.mode), dtype=np.float64)
    services = np.zeros(len(episode.mode), dtype=np.float64)
    training: list[BoundaryTrainingRecord] = []
    actual_boundaries: list[int] = []
    routine_ticks: list[int] = []
    iid_draws: list[int] = []
    iid_draw_records: list[tuple[int, int, int, bool]] = []
    iid_ordinal = 0
    censored: int | None = None
    post_legal = [0, 0]
    post_actions = [[0, 0, 0], [0, 0, 0]]
    masked = [0, 0]
    exposure_totals = [0, 0]
    survival_rows: list[tuple[int, int, bool]] = []
    rate_rows: list[dict[str, object]] = []
    event_ticks: list[list[int]] = [[], []]
    dwells: list[list[int]] = [[], []]
    last_event: list[int | None] = [None, None]
    identities: list[BoundaryIdentity] = []
    actor_calls = critic_calls = 0
    action_cost = 0.0
    forced_count = safety_violations = safety_score_factors = 0
    safety_expected = safety_affected_action = safety_unaffected_action = None
    safety_affected_clock = safety_unaffected_clock = False
    latency: list[int] = []
    stale = plan_age_sum = downtime = 0
    dummy_calls: list[tuple[int, str, int]] = []
    physics_ledger: list[tuple[object, ...]] = []

    for tick in range(len(episode.mode)):
        for role in range(2):
            histories[role].append(int(episode.sensors[tick, role]))
        routine = tick in boundaries
        safety = episode.safety_tick == tick
        if routine or safety:
            actual_boundaries.append(tick)
            if routine:
                routine_ticks.append(tick)
            cause = "SAFETY_BYPASS" if safety else "ROUTINE_CALLBACK"
            delta = [tick - previous_boundary[role] for role in range(2)]
            exposures = [eligible_exposure(previous_boundary[role], leases[role], tick) for role in range(2)]
            timing = np.stack([
                timing_features(
                    age=ages[role], lease_expiry=leases[role], busy=busy[role], tick=tick,
                    cause=cause, delta=delta[role], exposure=exposures[role],
                ) for role in range(2)
            ])
            critic_row = critic_features(
                mode=int(episode.mode[tick]), timing_rows=timing, bindings=bindings,
                ages=ages, leases=leases, busy=busy, histories=histories, tick=tick,
            )
            behavior_value = learner.value(critic_row)
            critic_calls += 1
            started = time.perf_counter_ns()
            logits, rates, probabilities = learner.policy(timing, np.asarray(exposures, dtype=np.float64))
            latency.append(time.perf_counter_ns() - started)
            actor_calls += 2
            actions = np.zeros(2, dtype=np.int64)
            masks = np.zeros(2, dtype=bool)
            if safety:
                dummy_calls.extend((tick, "SAFETY_BYPASS", role) for role in range(2))
                affected = int(episode.safety_agent)
                safety_expected = 2 if bindings[affected] != int(episode.mode[tick]) else 1
                actions[affected] = safety_expected
                safety_affected_action = safety_expected
                safety_unaffected_action = 0
                forced_count += 1
            else:
                for role in range(2):
                    exposure_totals[role] += exposures[role]
                    if exposures[role] <= 0:
                        masked[role] += 1
                        dummy_calls.append((tick, "LEASE_MASKED", role))
                    else:
                        if tick > 0:
                            post_legal[role] += 1
                        actions[role] = 0 if force_keep else sample_action(
                            float(probabilities[role]), episode, tick, role,
                        )
                        if not force_keep:
                            masks[role] = True
                            if tick > 0:
                                post_actions[role][int(actions[role])] += 1
                    survival_rows.append((int(exposures[role]), int(actions[role]), tick == 0))
            for role in range(2):
                rate_rows.append({
                    "tick": tick, "role": ROLES[role], "cause": cause,
                    "timing_features": tuple(float(value) for value in timing[role]),
                    "effective_actor_input": tuple(
                        0.0 if arm == "RATE-CONST" else float(value) for value in timing[role]
                    ),
                    "exposure": int(exposures[role]), "logit": float(logits[role]),
                    "lambda": float(rates[role]), "event_probability": float(probabilities[role]),
                    "policy_score": bool(masks[role]), "forced": bool(safety and role == episode.safety_agent),
                })
            behavior_log = (
                learner.joint_log_probability(timing, np.asarray(exposures), actions, masks)
                if bool(masks.any()) else 0.0
            )

            execution_roles = {int(episode.safety_agent)} if safety else {0, 1}
            before_previous = tuple(previous_boundary)
            for role in execution_roles:
                action = int(actions[role])
                if action > 0:
                    if not safety:
                        if last_event[role] is not None:
                            dwells[role].append(tick - int(last_event[role]))
                        last_event[role] = tick
                        event_ticks[role].append(tick)
                    if action == 1:
                        ages[role] = 0
                        busy[role] = 1
                        action_cost += 0.02
                    else:
                        bindings[role] ^= 1
                        ages[role] = 0
                        busy[role] = 2
                        action_cost += 0.04
                    leases[role] = tick + LEASE_TICKS
                previous_boundary[role] = tick
            if safety:
                affected = int(episode.safety_agent)
                safety_affected_clock = previous_boundary[affected] == tick
                safety_unaffected_clock = previous_boundary[1 - affected] != before_previous[1 - affected]
            else:
                previous_boundary = [tick, tick]

            # The global routine ordinal advances even when coincident safety suppresses its action.
            if iid and routine:
                interval = _next_iid_interval(episode, iid_ordinal)
                iid_draws.append(interval)
                iid_draw_records.append((iid_ordinal, tick, interval, safety))
                iid_ordinal += 1
                next_tick = tick + interval
                if next_tick < len(episode.mode):
                    boundaries.add(next_tick)
                else:
                    censored = len(episode.mode) - tick

            identity_roles = (int(episode.safety_agent),) if safety else (0, 1)
            for role in identity_roles:
                identities.append(BoundaryIdentity(
                    episode_id=f"{episode.namespace}:{episode.seed}:{episode.episode_index}",
                    agent_role=ROLES[role], owner_epoch=owner_epoch,
                    own_boundary_index=own_boundary_index[role], behavior_version=behavior,
                    cause=cause, action=ACTIONS[int(actions[role])], initial_anchor_action=tick == 0,
                ))
                own_boundary_index[role] += 1
            if collect_training:
                training.append(BoundaryTrainingRecord(
                    tick=tick, actor_features=timing.copy(), critic_features=critic_row.copy(),
                    exposure=np.asarray(exposures, dtype=np.float64), actions=actions.copy(),
                    policy_mask=masks.copy(), behavior_joint_log_prob=behavior_log,
                    behavior_value=behavior_value,
                ))

        service = int(
            bindings[0] == int(episode.mode[tick]) and bindings[1] == int(episode.mode[tick])
            and busy[0] == 0 and busy[1] == 0
        ) * max(0.0, 1.0 - (ages[0] + ages[1]) / 128.0)
        tick_cost = 0.0
        if routine or safety:
            tick_cost = sum(0.02 if action == 1 else 0.04 if action == 2 else 0.0 for action in actions)
        services[tick] = service
        rewards[tick] = service - tick_cost
        stale += int(any(bindings[role] != int(episode.mode[tick]) for role in range(2)))
        plan_age_sum += sum(ages)
        downtime += int(any(value > 0 for value in busy))
        physics_ledger.append((
            tick, int(episode.mode[tick]), int(episode.sensors[tick, 0]), int(episode.sensors[tick, 1]),
            bindings[0], bindings[1], ages[0], ages[1], busy[0], busy[1],
            leases[0], leases[1], float(service), float(rewards[tick]), routine,
        ))
        for role in range(2):
            if busy[role] > 0:
                busy[role] -= 1
            ages[role] = min(64, ages[role] + 1)

    for index, row in enumerate(training):
        end = training[index + 1].tick if index + 1 < len(training) else len(rewards)
        row.duration = end - row.tick
        discount = 1.0
        for reward in rewards[row.tick:end]:
            row.segment_reward += discount * float(reward)
            discount *= 0.99 ** (1.0 / 8.0)
    segment_exact = bool(
        actual_boundaries and actual_boundaries[0] == 0
        and sum(row.duration for row in training) == len(rewards) if training else actual_boundaries[0] == 0
    )
    if episode.safety_tick is not None:
        safety_violations += int(forced_count != 1)
        safety_violations += int(safety_affected_action != safety_expected)
        safety_violations += int(safety_unaffected_action != 0)
        safety_violations += int(not safety_affected_clock or safety_unaffected_clock)
        safety_violations += int(safety_score_factors != 0)
    direct_return = float(rewards.sum(dtype=np.float64) / len(rewards))
    recomposed = float(services.sum(dtype=np.float64) / len(rewards) - action_cost / len(rewards))
    return EpisodeResult(
        arm=arm, schedule=episode.schedule, episode_index=episode.episode_index,
        normalized_return=direct_return, service=float(services.sum() / len(rewards)),
        action_cost=float(action_cost / len(rewards)), physics_ticks=len(rewards),
        actor_calls=actor_calls, critic_calls=critic_calls, messages=2 * len(rewards),
        transmitted_bits=4 * len(rewards), optimizer_behavior_version=behavior,
        routine_boundary_ticks=tuple(routine_ticks), iid_interval_draws=tuple(iid_draws),
        iid_draw_records=tuple(iid_draw_records), iid_terminal_censored_duration=censored,
        poststartup_legal_rows=tuple(post_legal),
        poststartup_stochastic_actions=tuple(tuple(values) for values in post_actions),
        masked_routine_rows=tuple(masked), eligible_exposure=tuple(exposure_totals),
        event_free_survival_rows=tuple(survival_rows),
        voluntary_event_ticks=tuple(tuple(values) for values in event_ticks),
        inter_event_dwells=tuple(tuple(values) for values in dwells), rate_rows=tuple(rate_rows),
        safety_forced_count=forced_count, safety_tick=episode.safety_tick,
        safety_coincident_routine=bool(episode.safety_tick in routine_ticks),
        safety_affected_agent=episode.safety_agent, safety_expected_action=safety_expected,
        safety_affected_action=safety_affected_action, safety_unaffected_action=safety_unaffected_action,
        safety_policy_score_factors=safety_score_factors,
        safety_affected_clock_advanced=safety_affected_clock,
        safety_unaffected_clock_advanced=safety_unaffected_clock,
        safety_violations=safety_violations, identity_rows=tuple(identities),
        identity_unique=len(identities) == len({identity.key for identity in identities}),
        reward_service_cost_exact=abs(direct_return - recomposed) <= 1e-12,
        segment_ownership_exact=segment_exact, terminal_boundary_absent=len(rewards) not in actual_boundaries,
        stale_binding_ticks=stale, plan_age_sum=plan_age_sum, downtime_ticks=downtime,
        decision_latencies_ns=tuple(latency), physics_ledger=tuple(physics_ledger),
        dummy_call_ledger=tuple(dummy_calls), training_records=training,
    )
