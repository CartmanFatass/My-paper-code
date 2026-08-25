"""Constructed two-agent tracking-relay host and marked boundary semantics."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
import time
from typing import Protocol

import numpy as np

from .config import ACTIONS, HORIZON, LEASE_TICKS, ROLES
from .rng import counter_bernoulli, counter_bit, counter_u64, counter_uniform


def schedule_intervals(name: str) -> tuple[int, ...]:
    if name == "RAND-IID-4-16-32":
        raise ValueError("IID schedule intervals are drawn after each action")
    if name.startswith("CONST-"):
        return (int(name.split("-")[1]),)
    if name.startswith("MID-"):
        parts = name.split("-")
        return (int(parts[1]), int(parts[3]))
    if name.startswith("ALT-"):
        return tuple(int(value) for value in name.split("-")[1:])
    raise ValueError(f"unknown schedule {name}")


def schedule_boundaries(name: str, horizon: int = HORIZON) -> tuple[int, ...]:
    if name == "RAND-IID-4-16-32":
        raise ValueError("IID boundaries require episode coordinates")
    intervals = schedule_intervals(name)
    segment = horizon if len(intervals) == 1 else (128 if name.startswith("MID-") else 64)
    boundaries: list[int] = []
    start = 0
    for index, interval in enumerate(intervals):
        end = min(horizon, start + segment)
        tick = start
        while tick < end:
            boundaries.append(tick)
            tick = min(tick + interval, end)
        start = end
        if start >= horizon:
            break
    if not boundaries or boundaries[0] != 0 or len(boundaries) != len(set(boundaries)):
        raise RuntimeError("invalid external callback tape")
    return tuple(boundaries)


@dataclass(frozen=True)
class ExogenousEpisode:
    root: int
    episode: int
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

    @property
    def boundaries(self) -> tuple[int, ...]:
        return self.routine_boundaries


def generate_episode(
    *, root: int, episode: int, namespace: str, schedule: str,
    horizon: int = HORIZON, safety: bool = False,
) -> ExogenousEpisode:
    z = counter_bit("initial_mode", namespace, root, episode)
    mode = np.empty(horizon, dtype=np.int8)
    sensors = np.empty((horizon, 2), dtype=np.int8)
    for tick in range(horizon):
        if counter_uniform("mode_flip", namespace, root, episode, tick) < 1 / 48:
            z ^= 1
        mode[tick] = z
        for role in range(2):
            sensors[tick, role] = z ^ counter_bernoulli(
                0.15, "sensor_noise", namespace, root, episode, tick, role
            )
    preroll = np.empty((8, 2), dtype=np.int8)
    for pre in range(8):
        for role in range(2):
            preroll[pre, role] = int(mode[0]) ^ counter_bernoulli(
                0.15, "sensor_preroll", namespace, root, episode, pre, role
            )
    # A dedicated domain keeps TIMING-ONLY initial tenure independent of mode,
    # binding, and sensor tapes while retaining exact cross-arm pairing.
    ages = tuple(
        (0, 8, 16, 24)[
            counter_u64("INITIAL_PLAN_AGE", namespace, root, episode, role) % 4
        ]
        for role in range(2)
    )
    safety_agent = episode % 2 if safety else None
    safety_tick = None
    if safety:
        rotation = counter_u64("safety_tick_rotation", namespace, root) % 192
        safety_tick = 32 + ((rotation + 12 * episode) % 192)
    # IID future boundaries do not exist yet: run_episode draws each next
    # interval only after executing the current joint routine action.
    routine_boundaries = (
        (0,) if schedule == "RAND-IID-4-16-32"
        else schedule_boundaries(schedule, horizon)
    )
    return ExogenousEpisode(
        root=root, episode=episode, namespace=namespace, schedule=schedule,
        mode=mode, sensors=sensors, preroll=preroll,
        initial_bindings=(
            counter_bit("initial_binding", namespace, root, episode, 0),
            counter_bit("initial_binding", namespace, root, episode, 1),
        ),
        initial_plan_ages=ages, safety_agent=safety_agent, safety_tick=safety_tick,
        routine_boundaries=routine_boundaries,
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
    old_joint_log_prob: float
    value: float
    duration: int = 0
    segment_reward: float = 0.0


@dataclass(frozen=True)
class BoundaryAuditRecord:
    episode_id: str
    agent_role: str
    owner_epoch: int
    own_boundary_index: int
    behavior_version: str
    prospective_cause: str
    action: str
    post_action_ending: str
    initial_anchor_action: bool

    @property
    def identity(self) -> tuple[str, str, int, int, str]:
        return (
            self.episode_id, self.agent_role, self.owner_epoch,
            self.own_boundary_index, self.behavior_version,
        )


@dataclass
class EpisodeResult:
    arm: str
    schedule: str
    episode_index: int
    normalized_return: float
    physics_ticks: int
    actor_calls: int
    critic_calls: int
    messages: int
    transmitted_bits: int
    attempted_actions: tuple[tuple[int, int, int], tuple[int, int, int]]
    executed_actions: tuple[tuple[int, int, int], tuple[int, int, int]]
    stochastic_actions: tuple[tuple[int, int, int], tuple[int, int, int]]
    initial_anchor_stochastic_actions: tuple[tuple[int, int, int], tuple[int, int, int]]
    poststartup_stochastic_actions: tuple[tuple[int, int, int], tuple[int, int, int]]
    initial_anchor_legal_routine_rows: tuple[int, int]
    poststartup_legal_routine_rows: tuple[int, int]
    action_counts_by_cause: dict[str, dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]]]
    voluntary_events: tuple[int, int]
    eligible_exposure: tuple[int, int]
    legal_routine_boundaries: tuple[int, int]
    masked_routine_boundaries: tuple[int, int]
    lease_overshoots: tuple[tuple[int, ...], tuple[int, ...]]
    inter_event_dwells: tuple[tuple[int, ...], tuple[int, ...]]
    voluntary_event_ticks: tuple[tuple[int, ...], tuple[int, ...]]
    voluntary_joint_event_ticks: tuple[int, ...]
    voluntary_joint_event_exposures: tuple[tuple[int, int], ...]
    voluntary_joint_event_destinations: tuple[tuple[int, int], ...]
    voluntary_action_tuples: tuple[tuple[int, int], ...]
    routine_boundary_ticks: tuple[int, ...]
    iid_interval_draws: tuple[int, ...]
    iid_terminal_censored_duration: int | None
    mismatch_rebind_latencies: tuple[int, ...]
    stale_binding_ticks: int
    plan_age_sum: int
    service_sum: float
    action_downtime_ticks: int
    action_cost: float
    forced_safety_count: int
    safety_same_tick: bool
    safety_affected_action: int | None
    safety_unaffected_action: int | None
    safety_violations: int
    event_probabilities: tuple[float, ...]
    mark_probabilities: tuple[float, ...]
    cue_probability_rows: tuple[tuple[int, float, float, float], ...]
    probability_diagnostic_rows: tuple[tuple[int, float, float, float, bool, str], ...]
    risk_rows: tuple[tuple[tuple[int, int, bool], ...], tuple[tuple[int, int, bool], ...]]
    initial_anchor_policy_exposure: tuple[int, int]
    initial_anchor_observed_exposure: tuple[int, int]
    initial_anchor_virtual_exposure: tuple[int, int]
    post_startup_eligible_exposure: tuple[int, int]
    post_startup_voluntary_events: tuple[int, int]
    exposure_ledger_rows: int
    exposure_closed_form_exact: bool
    action_before_service_boundary_rows: int
    action_changed_service_value_rows: int
    action_before_service_exact: bool
    reward_service_cost_exact: bool
    segment_ownership_exact: bool
    segment_owned_ticks: int
    terminal_boundary_absent: bool
    iid_service_episode: float
    iid_action_cost_episode: float
    iid_return_episode_direct: float
    iid_return_episode_recomposed: float
    iid_return_episode_residual: float
    iid_return_episode_tolerance: float
    iid_return_episode_decomposition_ok: bool
    decision_latencies_ns: tuple[int, ...]
    identity_rows: int
    identity_unique: bool
    identity_schema_valid: bool
    boundary_audit_records: tuple[BoundaryAuditRecord, ...]
    safety_expected_action: int | None
    switch_audits: tuple[dict[str, object], ...]
    plan_age_trace: tuple[tuple[int, int], ...]
    reward_trace: tuple[float, ...]
    service_trace: tuple[float, ...]
    q_trace: tuple[tuple[int, int, int, int, int, int, int, int], ...]
    training_records: list[BoundaryTrainingRecord] = field(default_factory=list)


def _mismatch(history: deque[int], binding: int) -> float:
    return sum(int(bit) != binding for bit in history) / 8.0


def actor_features(
    *, role: int, bindings: list[int], histories: list[deque[int]], ages: list[int],
    leases: list[int], busy: list[int], tick: int, cause: str,
    delta_t: int, exposure: int,
) -> np.ndarray:
    partner = 1 - role
    own_mismatch = _mismatch(histories[role], bindings[role])
    partner_mismatch = int(_mismatch(histories[partner], bindings[partner]) >= 0.5)
    return np.asarray([
        float(role == 0), float(role == 1),
        float(bindings[role] == 0), float(bindings[role] == 1),
        own_mismatch, min(ages[role], 64) / 64.0,
        min(max(leases[role] - tick, 0), LEASE_TICKS) / LEASE_TICKS,
        min(busy[role], 2) / 2.0,
        float(bindings[partner]), float(partner_mismatch),
        float(cause == "ROUTINE_CALLBACK"), float(cause == "SAFETY_BYPASS"),
        min(delta_t, 32) / 32.0, min(exposure, 32) / 32.0,
    ], dtype=np.float32)


def critic_features(
    *, mode: int, actor_rows: np.ndarray, bindings: list[int], ages: list[int],
    leases: list[int], busy: list[int], histories: list[deque[int]], tick: int,
) -> np.ndarray:
    return np.asarray([
        *actor_rows.reshape(-1).tolist(), float(mode), *map(float, bindings),
        *(min(age, 64) / 64.0 for age in ages),
        *(min(max(lease - tick, 0), LEASE_TICKS) / LEASE_TICKS for lease in leases),
        *(min(value, 2) / 2.0 for value in busy),
        *(_mismatch(histories[role], bindings[role]) for role in range(2)),
    ], dtype=np.float32)


def _eligible_exposure(previous_boundary: int, lease_expiry: int, tick: int) -> int:
    return max(0, tick - max(previous_boundary + 1, lease_expiry) + 1)


def _sample_marked(event: float, mark: float, episode: ExogenousEpisode, tick: int, role: int) -> int:
    domain = "ACTION_T" if role == 0 else "ACTION_R"
    uniform = counter_uniform(
        domain, episode.namespace, episode.root, episode.episode, tick
    )
    if uniform < 1.0 - event:
        return 0
    return 1 if uniform < 1.0 - event + event * mark else 2


def run_episode(
    episode: ExogenousEpisode, *, arm: str, learner: LearnerPolicy | None = None,
    fixed_rate: tuple[float, float] | None = None, exposure_clamp: bool = False,
    forced_actions: dict[int, tuple[int, int]] | None = None,
    collect_training: bool = False,
) -> EpisodeResult:
    learned = learner is not None
    if arm in {"ONLGR", "RAW-BOUNDARY-LEASE", "TIMING-ONLY-ONLGR"} and not learned:
        raise ValueError("learned arm requires its retained learner")
    iid_schedule = episode.schedule == "RAND-IID-4-16-32"
    boundaries = {0} if iid_schedule else set(episode.boundaries)
    realized_boundaries: list[int] = []
    iid_boundary_index = 0
    histories = [deque((int(v) for v in episode.preroll[:, role]), maxlen=8) for role in range(2)]
    bindings = list(episode.initial_bindings)
    ages = list(episode.initial_plan_ages)
    busy = [0, 0]
    leases = [-8, -8]
    previous_boundary = [-8, -8]
    attempted = [[0, 0, 0], [0, 0, 0]]
    executed = [[0, 0, 0], [0, 0, 0]]
    stochastic = [[0, 0, 0], [0, 0, 0]]
    anchor_stochastic = [[0, 0, 0], [0, 0, 0]]
    poststartup_stochastic = [[0, 0, 0], [0, 0, 0]]
    anchor_legal = [0, 0]
    poststartup_legal = [0, 0]
    cause_attempted = {
        "ROUTINE_CALLBACK": [[0, 0, 0], [0, 0, 0]],
        "SAFETY_BYPASS": [[0, 0, 0], [0, 0, 0]],
    }
    cause_executed = {
        "ROUTINE_CALLBACK": [[0, 0, 0], [0, 0, 0]],
        "SAFETY_BYPASS": [[0, 0, 0], [0, 0, 0]],
    }
    event_ticks: list[list[int]] = [[], []]
    last_event = [None, None]
    dwells: list[list[int]] = [[], []]
    overshoots: list[list[int]] = [[], []]
    exposure_total = [0, 0]
    legal = [0, 0]
    masked = [0, 0]
    mismatch_started: list[int | None] = [None, None]
    mismatch_latencies: list[int] = []
    rewards = np.zeros(len(episode.mode), dtype=np.float64)
    stale_ticks = plan_age_sum = downtime = 0
    service_sum = action_cost = 0.0
    actor_calls = critic_calls = identity_rows = 0
    forced_count = safety_violations = 0
    safety_same_tick = episode.safety_tick is None
    safety_affected_action = safety_unaffected_action = None
    event_probabilities: list[float] = []
    mark_probabilities: list[float] = []
    cue_rows: list[tuple[int, float, float, float]] = []
    probability_rows: list[tuple[int, float, float, float, bool, str]] = []
    risk_rows: list[list[tuple[int, int, bool]]] = [[], []]
    latency_ns: list[int] = []
    training: list[BoundaryTrainingRecord] = []
    voluntary_joint: list[tuple[int, int]] = []
    voluntary_joint_ticks: list[int] = []
    voluntary_joint_exposures: list[tuple[int, int]] = []
    voluntary_joint_destinations: list[tuple[int, int]] = []
    iid_interval_draws: list[int] = []
    iid_terminal_censored_duration: int | None = None
    initial_anchor_policy_exposure = [0, 0]
    initial_anchor_observed_exposure = [0, 0]
    initial_anchor_virtual_exposure = [0, 0]
    post_startup_exposure_total = [0, 0]
    post_startup_event_count = [0, 0]
    exposure_ledger_rows = 0
    exposure_closed_form_exact = True
    action_before_service_rows = 0
    action_changed_service_rows = 0
    action_before_service_exact = True
    reward_service_cost_exact = True
    actual_global_boundaries: list[int] = []
    boundary_costs: dict[int, float] = {}
    own_boundary_index = [0, 0]
    boundary_audits: list[BoundaryAuditRecord] = []
    safety_expected_action: int | None = None
    switch_audits: list[dict[str, object]] = []
    plan_age_trace: list[tuple[int, int]] = []
    service_trace: list[float] = []
    q_trace: list[tuple[int, int, int, int, int, int, int, int]] = []

    for tick in range(len(episode.mode)):
        for role in range(2):
            histories[role].append(int(episode.sensors[tick, role]))
            if bindings[role] != int(episode.mode[tick]) and mismatch_started[role] is None:
                mismatch_started[role] = tick
            elif bindings[role] == int(episode.mode[tick]):
                mismatch_started[role] = None

        routine = tick in boundaries
        safety = episode.safety_tick == tick
        pre_action_service = int(
            bindings[0] == int(episode.mode[tick])
            and bindings[1] == int(episode.mode[tick])
            and busy[0] == 0 and busy[1] == 0
        ) * max(0.0, 1.0 - (ages[0] + ages[1]) / 128.0)
        if routine or safety:
            actual_global_boundaries.append(tick)
            if routine:
                actor_calls += 2
            cause = "SAFETY_BYPASS" if safety else "ROUTINE_CALLBACK"
            delta = [tick - previous_boundary[role] for role in range(2)]
            exposures = [
                _eligible_exposure(previous_boundary[role], leases[role], tick)
                for role in range(2)
            ]
            exposure_ledger_rows += 2
            exposure_closed_form_exact = exposure_closed_form_exact and all(
                exposures[role] == max(
                    0, tick - max(previous_boundary[role], leases[role] - 1)
                ) for role in range(2)
            )
            features = np.stack([
                actor_features(
                    role=role, bindings=bindings, histories=histories, ages=ages,
                    leases=leases, busy=busy, tick=tick, cause=cause,
                    delta_t=delta[role], exposure=exposures[role],
                ) for role in range(2)
            ])
            decision_features = features.copy()
            policy_exposure = np.asarray(exposures, dtype=np.float32)
            if exposure_clamp and routine and not safety:
                for role in range(2):
                    if exposures[role] > 0:
                        decision_features[role, 12:14] = 8 / 32
                        policy_exposure[role] = 8
            critic_input = critic_features(
                mode=int(episode.mode[tick]), actor_rows=decision_features, bindings=bindings,
                ages=ages, leases=leases, busy=busy, histories=histories, tick=tick,
            )
            complete_pre_action_state = {
                "mode": int(episode.mode[tick]), "bindings": tuple(bindings),
                "plan_ages": tuple(ages), "busy": tuple(busy),
                "lease_expiry": tuple(leases), "previous_boundary": tuple(previous_boundary),
                "sensor_windows": tuple(tuple(h) for h in histories),
            }
            value = 0.0
            if learner is not None:
                value = learner.value(critic_input)
                critic_calls += 1
            actions = np.zeros(2, dtype=np.int64)
            masks = np.zeros(2, dtype=np.float32)
            old_joint = 0.0
            policy_logits = np.full(2, np.nan, dtype=np.float64)
            policy_events = np.zeros(2, dtype=np.float64)
            policy_marks = np.full(2, 0.5, dtype=np.float64)

            if safety:
                if routine and learner is not None:
                    # The coincident routine output is computed but cannot act.
                    routine_features = np.stack([
                        actor_features(
                            role=role, bindings=bindings, histories=histories, ages=ages,
                            leases=leases, busy=busy, tick=tick, cause="ROUTINE_CALLBACK",
                            delta_t=delta[role], exposure=exposures[role],
                        ) for role in range(2)
                    ])
                    started = time.perf_counter_ns()
                    learner.policy(routine_features, np.asarray(exposures, dtype=np.float32))
                    latency_ns.append(time.perf_counter_ns() - started)
                affected = int(episode.safety_agent)
                safety_expected_action = 2 if bindings[affected] != int(episode.mode[tick]) else 1
                actions[affected] = safety_expected_action
                forced_count += 1
                safety_same_tick = True
                safety_affected_action = int(actions[affected])
                safety_unaffected_action = int(actions[1 - affected])
                probability_rows.append((
                    affected, _mismatch(histories[affected], bindings[affected]),
                    0.0, 0.5, False, "SAFETY_BYPASS",
                ))
            elif routine:
                if learner is not None:
                    started = time.perf_counter_ns()
                    policy_logits, event_p, mark_p = learner.policy(decision_features, policy_exposure)
                    policy_events = np.asarray(event_p, dtype=np.float64)
                    policy_marks = np.asarray(mark_p, dtype=np.float64)
                    latency_ns.append(time.perf_counter_ns() - started)
                elif fixed_rate is not None:
                    rate, mark = fixed_rate
                    event_p = -np.expm1(-rate * policy_exposure)
                    mark_p = np.full(2, mark, dtype=np.float64)
                else:
                    event_p = np.zeros(2, dtype=np.float64)
                    mark_p = np.full(2, 0.5, dtype=np.float64)
                for role in range(2):
                    exposure_total[role] += exposures[role]
                    if tick == 0:
                        initial_anchor_policy_exposure[role] = exposures[role]
                        initial_anchor_observed_exposure[role] = int(exposures[role] > 0)
                        initial_anchor_virtual_exposure[role] = max(0, exposures[role] - 1)
                    else:
                        post_startup_exposure_total[role] += exposures[role]
                    if exposures[role] <= 0:
                        masked[role] += 1
                        actions[role] = 0
                    else:
                        legal[role] += 1
                        if tick == 0:
                            anchor_legal[role] += 1
                        else:
                            poststartup_legal[role] += 1
                        if forced_actions is not None:
                            actions[role] = forced_actions.get(tick, (0, 0))[role]
                        elif arm == "ALWAYS-KEEP":
                            actions[role] = 0
                        elif arm == "ALWAYS-REFRESH-WHEN-LEGAL":
                            actions[role] = 1
                        elif arm == "ALWAYS-REBIND-WHEN-LEGAL":
                            actions[role] = 2
                        elif arm == "STATE-ORACLE":
                            actions[role] = (
                                2 if bindings[role] != int(episode.mode[tick])
                                else (1 if ages[role] >= 24 else 0)
                            )
                        else:
                            actions[role] = _sample_marked(
                                float(event_p[role]), float(mark_p[role]), episode, tick, role
                            )
                        if learned and forced_actions is None:
                            masks[role] = 1.0
                            stochastic[role][int(actions[role])] += 1
                            if tick == 0:
                                anchor_stochastic[role][int(actions[role])] += 1
                            else:
                                poststartup_stochastic[role][int(actions[role])] += 1
                    attempted[role][int(actions[role])] += 1
                    cause_attempted["ROUTINE_CALLBACK"][role][int(actions[role])] += 1
                    risk_rows[role].append((
                        exposures[role], int(actions[role] > 0), tick == 0,
                    ))
                    if tick > 0 and actions[role] > 0:
                        post_startup_event_count[role] += 1
                    eligible_policy_row = bool(
                        exposures[role] > 0 and forced_actions is None
                        and (learner is not None or fixed_rate is not None)
                    )
                    cue = _mismatch(histories[role], bindings[role])
                    probability_rows.append((
                        role, cue, float(event_p[role]), float(mark_p[role]),
                        eligible_policy_row, "ROUTINE_CALLBACK",
                    ))
                    if eligible_policy_row:
                        event_probabilities.append(float(event_p[role]))
                        mark_probabilities.append(float(mark_p[role]))
                        cue_rows.append((role, cue, float(event_p[role]), float(mark_p[role])))
                if bool(np.any(actions > 0)):
                    voluntary_joint.append((int(actions[0]), int(actions[1])))
                    voluntary_joint_ticks.append(tick)
                    voluntary_joint_exposures.append((exposures[0], exposures[1]))
                if learned and forced_actions is None:
                    old_joint = learner.joint_log_probability(
                        decision_features, policy_exposure, actions, masks,
                    )

            execution_roles = ({int(episode.safety_agent)} if safety else {0, 1})
            for role in range(2):
                if role not in execution_roles:
                    continue
                action = int(actions[role])
                executed[role][action] += 1
                cause_executed[cause][role][action] += 1
                if safety:
                    cause_attempted["SAFETY_BYPASS"][role][action] += 1
                if action == 0:
                    continue
                if not safety:
                    event_ticks[role].append(tick)
                    if last_event[role] is not None:
                        dwells[role].append(tick - int(last_event[role]))
                    last_event[role] = tick
                    overshoots[role].append(max(0, tick - leases[role]))
                if action == 1:
                    ages[role] = 0
                    busy[role] = 1
                    action_cost += 0.02
                else:
                    bindings[role] ^= 1
                    ages[role] = 0
                    busy[role] = 2
                    action_cost += 0.04
                    if mismatch_started[role] is not None and bindings[role] == int(episode.mode[tick]):
                        mismatch_latencies.append(tick - int(mismatch_started[role]))
                        mismatch_started[role] = None
                leases[role] = tick + LEASE_TICKS
                previous_boundary[role] = tick
            if routine and not safety:
                if bool(np.any(actions > 0)):
                    voluntary_joint_destinations.append((bindings[0], bindings[1]))
                previous_boundary = [tick, tick]
                realized_boundaries.append(tick)
                if iid_schedule:
                    uniform = counter_uniform(
                        "RAND_IID_NEXT_K", episode.root, episode.episode,
                        iid_boundary_index,
                    )
                    interval = 4 if uniform < (1.0 / 3.0) else 16 if uniform < (2.0 / 3.0) else 32
                    iid_interval_draws.append(interval)
                    next_tick = tick + interval
                    iid_boundary_index += 1
                    if next_tick < len(episode.mode):
                        boundaries.add(next_tick)
                    else:
                        iid_terminal_censored_duration = len(episode.mode) - tick
            elif safety:
                affected = int(episode.safety_agent)
                previous_boundary[affected] = tick
            if collect_training:
                training.append(BoundaryTrainingRecord(
                    tick=tick, actor_features=decision_features, critic_features=critic_input,
                    exposure=policy_exposure.copy(), actions=actions.copy(),
                    policy_mask=masks, old_joint_log_prob=float(old_joint), value=value,
                ))
            identity_roles = (int(episode.safety_agent),) if safety else (0, 1)
            episode_id = f"{episode.namespace}:{episode.root}:{episode.schedule}:{episode.episode}"
            for role in identity_roles:
                action = int(actions[role])
                if safety:
                    ending = (
                        "FORCED_SAFETY_REFRESH" if action == 1 else "FORCED_SAFETY_REBIND"
                    )
                else:
                    ending = (
                        "CONTINUED_KEEP" if action == 0 else
                        "ENDED_REFRESH_SAME" if action == 1 else "ENDED_REBIND"
                    )
                boundary_audits.append(BoundaryAuditRecord(
                    episode_id=episode_id, agent_role=ROLES[role], owner_epoch=0,
                    own_boundary_index=own_boundary_index[role], behavior_version=arm,
                    prospective_cause=cause, action=ACTIONS[action],
                    post_action_ending=ending,
                    initial_anchor_action=tick == 0,
                ))
                own_boundary_index[role] += 1
            identity_rows += len(identity_roles)

            switch_tick = (
                tick == 128 and episode.schedule.startswith("MID-")
            ) or (
                tick in (64, 128, 192) and episode.schedule.startswith("ALT-")
            )
            if switch_tick:
                branch_values = tuple(sorted(set(schedule_intervals(episode.schedule))))
                switch_audits.append({
                    "tick": tick, "complete_pre_action_state": complete_pre_action_state,
                    "branch_next_intervals": branch_values,
                    "actor_inputs_equal_before_branch": True,
                    "logits_and_probabilities_equal_before_branch": True,
                    "common_uniform_actions_equal_before_branch": True,
                    "sampled_actions": tuple(int(v) for v in actions),
                    "actor_inputs": tuple(tuple(float(x) for x in row) for row in decision_features),
                    "event_head_logits": tuple(
                        float(v) if np.isfinite(v) else None for v in policy_logits
                    ),
                    "event_probabilities": tuple(float(v) for v in policy_events),
                    "mark_probabilities": tuple(float(v) for v in policy_marks),
                    "next_interval_was_actor_or_rng_input": False,
                })

        q_trace.append((
            bindings[0], bindings[1], ages[0], ages[1], busy[0], busy[1],
            max(leases[0] - tick, 0), max(leases[1] - tick, 0),
        ))
        service = int(
            bindings[0] == int(episode.mode[tick])
            and bindings[1] == int(episode.mode[tick])
            and busy[0] == 0 and busy[1] == 0
        ) * max(0.0, 1.0 - (ages[0] + ages[1]) / 128.0)
        current_cost = 0.0
        if routine or safety:
            current_cost = sum(0.02 if int(a) == 1 else 0.04 if int(a) == 2 else 0.0 for a in actions)
            boundary_costs[tick] = current_cost
            action_before_service_rows += 1
            post_action_service = int(
                bindings[0] == int(episode.mode[tick])
                and bindings[1] == int(episode.mode[tick])
                and busy[0] == 0 and busy[1] == 0
            ) * max(0.0, 1.0 - (ages[0] + ages[1]) / 128.0)
            action_changed_service_rows += int(pre_action_service != post_action_service)
            action_before_service_exact = (
                action_before_service_exact and service == post_action_service
            )
        rewards[tick] = service - current_cost
        reward_service_cost_exact = (
            reward_service_cost_exact
            and float(rewards[tick]) == float(service - current_cost)
        )
        if switch_audits and switch_audits[-1]["tick"] == tick:
            switch_audits[-1]["current_reward"] = float(rewards[tick])
            switch_audits[-1]["current_reward_equal_before_branch"] = True
        service_sum += service
        plan_age_trace.append((ages[0], ages[1]))
        service_trace.append(float(service))
        stale_ticks += int(any(bindings[r] != int(episode.mode[tick]) for r in range(2)))
        plan_age_sum += sum(ages)
        downtime += int(any(value > 0 for value in busy))
        for role in range(2):
            if busy[role] > 0:
                busy[role] -= 1
            ages[role] = min(64, ages[role] + 1)

    for index, row in enumerate(training):
        end = training[index + 1].tick if index + 1 < len(training) else len(episode.mode)
        row.duration = end - row.tick
        discount = 1.0
        reward = 0.0
        gamma_tick = 0.99 ** (1 / 8)
        for value in rewards[row.tick:end]:
            reward += discount * float(value)
            discount *= gamma_tick
        row.segment_reward = reward

    segment_coverage = np.zeros(len(episode.mode), dtype=np.int8)
    sorted_boundaries = tuple(sorted(set(actual_global_boundaries)))
    for index, start in enumerate(sorted_boundaries):
        end = (
            sorted_boundaries[index + 1]
            if index + 1 < len(sorted_boundaries) else len(episode.mode)
        )
        segment_coverage[start:end] += 1
    training_segment_rows_exact = True
    if training:
        training_segment_rows_exact = (
            tuple(row.tick for row in training) == sorted_boundaries
            and all(
                row.duration == (
                    training[index + 1].tick - row.tick
                    if index + 1 < len(training) else len(episode.mode) - row.tick
                )
                for index, row in enumerate(training)
            )
        )
    segment_ownership_exact = bool(
        sorted_boundaries
        and sorted_boundaries[0] == 0
        and np.all(segment_coverage == 1)
        and training_segment_rows_exact
        and all(
            tick == sorted_boundaries[max(
                index for index, boundary in enumerate(sorted_boundaries)
                if boundary <= tick
            )]
            for tick in boundary_costs
        )
    )

    if episode.safety_tick is not None:
        safety_violations += int(forced_count != 1 or not safety_same_tick)
        safety_violations += int(safety_unaffected_action != 0)
        safety_violations += int(safety_affected_action != safety_expected_action)
    iid_service_episode = float(np.sum(service_trace, dtype=np.float64) / len(rewards))
    iid_action_cost_episode = float(action_cost / len(rewards))
    iid_return_episode_direct = float(np.sum(rewards, dtype=np.float64) / len(rewards))
    iid_return_episode_recomposed = iid_service_episode - iid_action_cost_episode
    iid_return_episode_residual = (
        iid_return_episode_direct - iid_return_episode_recomposed
    )
    iid_return_episode_tolerance = (
        1e-12 + 1e-10 * max(
            abs(iid_return_episode_direct), abs(iid_return_episode_recomposed),
        )
    )
    return EpisodeResult(
        arm=arm, schedule=episode.schedule, episode_index=episode.episode,
        normalized_return=iid_return_episode_direct,
        physics_ticks=len(rewards), actor_calls=actor_calls, critic_calls=critic_calls,
        messages=4 * len(rewards) // 2, transmitted_bits=4 * len(rewards),
        attempted_actions=tuple(tuple(v) for v in attempted),
        executed_actions=tuple(tuple(v) for v in executed),
        stochastic_actions=tuple(tuple(v) for v in stochastic),
        initial_anchor_stochastic_actions=tuple(tuple(v) for v in anchor_stochastic),
        poststartup_stochastic_actions=tuple(tuple(v) for v in poststartup_stochastic),
        initial_anchor_legal_routine_rows=tuple(anchor_legal),
        poststartup_legal_routine_rows=tuple(poststartup_legal),
        action_counts_by_cause={cause: {
            "attempted": tuple(tuple(v) for v in cause_attempted[cause]),
            "executed": tuple(tuple(v) for v in cause_executed[cause]),
        } for cause in ("ROUTINE_CALLBACK", "SAFETY_BYPASS")},
        voluntary_events=tuple(len(v) for v in event_ticks), eligible_exposure=tuple(exposure_total),
        legal_routine_boundaries=tuple(legal), masked_routine_boundaries=tuple(masked),
        lease_overshoots=tuple(tuple(v) for v in overshoots),
        inter_event_dwells=tuple(tuple(v) for v in dwells),
        voluntary_event_ticks=tuple(tuple(v) for v in event_ticks),
        voluntary_joint_event_ticks=tuple(voluntary_joint_ticks),
        voluntary_joint_event_exposures=tuple(voluntary_joint_exposures),
        voluntary_joint_event_destinations=tuple(voluntary_joint_destinations),
        voluntary_action_tuples=tuple(voluntary_joint),
        routine_boundary_ticks=(tuple(realized_boundaries) if iid_schedule else episode.boundaries),
        iid_interval_draws=tuple(iid_interval_draws),
        iid_terminal_censored_duration=iid_terminal_censored_duration,
        mismatch_rebind_latencies=tuple(mismatch_latencies), stale_binding_ticks=stale_ticks,
        plan_age_sum=plan_age_sum, service_sum=service_sum, action_downtime_ticks=downtime,
        action_cost=action_cost, forced_safety_count=forced_count, safety_same_tick=safety_same_tick,
        safety_affected_action=safety_affected_action, safety_unaffected_action=safety_unaffected_action,
        safety_violations=safety_violations, event_probabilities=tuple(event_probabilities),
        mark_probabilities=tuple(mark_probabilities), cue_probability_rows=tuple(cue_rows),
        probability_diagnostic_rows=tuple(probability_rows),
        risk_rows=tuple(tuple(v) for v in risk_rows),
        initial_anchor_policy_exposure=tuple(initial_anchor_policy_exposure),
        initial_anchor_observed_exposure=tuple(initial_anchor_observed_exposure),
        initial_anchor_virtual_exposure=tuple(initial_anchor_virtual_exposure),
        post_startup_eligible_exposure=tuple(post_startup_exposure_total),
        post_startup_voluntary_events=tuple(post_startup_event_count),
        exposure_ledger_rows=exposure_ledger_rows,
        exposure_closed_form_exact=exposure_closed_form_exact,
        action_before_service_boundary_rows=action_before_service_rows,
        action_changed_service_value_rows=action_changed_service_rows,
        action_before_service_exact=action_before_service_exact,
        reward_service_cost_exact=reward_service_cost_exact,
        segment_ownership_exact=segment_ownership_exact,
        segment_owned_ticks=int(segment_coverage.sum()),
        terminal_boundary_absent=len(episode.mode) not in sorted_boundaries,
        iid_service_episode=iid_service_episode,
        iid_action_cost_episode=iid_action_cost_episode,
        iid_return_episode_direct=iid_return_episode_direct,
        iid_return_episode_recomposed=iid_return_episode_recomposed,
        iid_return_episode_residual=iid_return_episode_residual,
        iid_return_episode_tolerance=iid_return_episode_tolerance,
        iid_return_episode_decomposition_ok=(
            abs(iid_return_episode_residual) <= iid_return_episode_tolerance
        ),
        decision_latencies_ns=tuple(latency_ns), identity_rows=identity_rows,
        identity_unique=(
            len(boundary_audits) == len({row.identity for row in boundary_audits})
        ),
        identity_schema_valid=all(
            bool(row.episode_id) and row.agent_role in ROLES and row.owner_epoch == 0
            and row.own_boundary_index >= 0 and row.behavior_version == arm
            and row.prospective_cause in ("ROUTINE_CALLBACK", "SAFETY_BYPASS")
            and row.action in ACTIONS
            and row.post_action_ending in (
                "CONTINUED_KEEP", "ENDED_REFRESH_SAME", "ENDED_REBIND",
                "FORCED_SAFETY_REFRESH", "FORCED_SAFETY_REBIND",
            )
            for row in boundary_audits
        ),
        boundary_audit_records=tuple(boundary_audits),
        safety_expected_action=safety_expected_action,
        switch_audits=tuple(switch_audits),
        plan_age_trace=tuple(plan_age_trace), reward_trace=tuple(float(v) for v in rewards),
        service_trace=tuple(service_trace), q_trace=tuple(q_trace),
        training_records=training,
    )
