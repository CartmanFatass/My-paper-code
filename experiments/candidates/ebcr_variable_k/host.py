from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

import numpy as np

from .config import K_MAX, K_MIN, ORDINARY_CAP, PENDING_WINDOW, TOTAL_CAP
from .rng import counter_bernoulli, counter_bit, counter_u64, counter_uniform, stationary_ready

ROLES = ("T", "R")


@dataclass(frozen=True)
class ExogenousEpisode:
    seed: int
    episode: int
    namespace: str
    cell: str
    joint_mismatch: bool
    durations: tuple[int, ...]
    noise: float
    latent: np.ndarray
    observations: np.ndarray
    readiness: np.ndarray
    boundary: np.ndarray
    changed: np.ndarray
    preroll: np.ndarray
    safety_agent: int | None = None
    safety_tick: int | None = None
    balance_coordinates: tuple[int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0)

    @property
    def horizon(self) -> int:
        return int(self.latent.shape[0])


def majority(bits: list[int] | np.ndarray) -> int:
    return int(sum(int(value) for value in bits) >= 2)


def generate_episode(
    *, seed: int, episode: int, namespace: str, cell: str,
    durations: tuple[int, ...], noise: float, joint_mismatch: bool,
    horizon: int = 128, safety: bool = False,
) -> ExogenousEpisode:
    if not durations or min(durations) <= 0:
        raise ValueError("phase durations must be positive")
    latent = np.empty((horizon, 2), dtype=np.int8)
    observations = np.empty((horizon, 2), dtype=np.int8)
    readiness = np.empty((horizon, 2), dtype=np.int8)
    boundary = np.zeros(horizon, dtype=np.int8)
    changed = np.zeros((horizon, 2), dtype=np.int8)
    latent_pair = (episode + counter_u64("latent_initial", namespace, seed, cell) % 4) % 4
    z = np.array(((latent_pair >> 1) & 1, latent_pair & 1), dtype=np.int8)
    phase_end = 0
    phase_index = 0
    duration_rotation = (
        episode + counter_u64("phase_schedule_rotation", namespace, seed, cell) % len(durations)
    ) % len(durations)
    current_duration = durations[duration_rotation]
    last_phase_start = 0
    ready_state = [
        stationary_ready("readiness_initial", namespace, seed, episode, role)
        for role in range(2)
    ]
    for tick in range(horizon):
        if tick == phase_end and tick > 0:
            boundary[tick] = 1
            if joint_mismatch:
                changed[tick, :] = 1
                z ^= 1
            else:
                changed_role = (
                    episode + phase_index
                    + counter_bit("phase_changed_role_offset", namespace, seed, cell)
                ) % 2
                changed[tick, changed_role] = 1
                z[changed_role] ^= 1
            phase_index += 1
            duration_index = (duration_rotation + phase_index) % len(durations)
            current_duration = durations[duration_index]
            last_phase_start = tick
        if tick == phase_end:
            phase_end += current_duration
        latent[tick] = z
        for role in range(2):
            transition_probability = 0.90 if ready_state[role] else 0.50
            ready_state[role] = counter_bernoulli(
                transition_probability, "readiness_chain", namespace, seed, episode, role, tick
            )
            readiness[tick, role] = ready_state[role]
            flip = counter_bernoulli(
                noise, "observation_noise", namespace, seed, episode, role, tick
            )
            observations[tick, role] = int(z[role]) ^ flip
    preroll = np.empty((3, 2), dtype=np.int8)
    initial = latent[0]
    for pre in range(3):
        for role in range(2):
            preroll[pre, role] = int(initial[role]) ^ counter_bernoulli(
                noise, "observation_preroll", namespace, seed, episode, role, pre
            )
    safety_agent = None
    safety_tick = None
    if safety:
        safety_agent = episode % 2
        # Across the registered 32-episode seed panel this is an injective,
        # seed-rotated spread through ticks 32..95 with 16 events per role.
        safety_tick = 32 + ((17 * episode + counter_u64(
            "safety_events", namespace, seed
        )) % 64)
        if not 0 <= safety_tick < horizon:
            raise ValueError("safety horizon must include registered ticks 32..95")
    return ExogenousEpisode(
        seed=seed, episode=episode, namespace=namespace, cell=cell,
        joint_mismatch=joint_mismatch, durations=durations, noise=noise,
        latent=latent, observations=observations, readiness=readiness,
        boundary=boundary, changed=changed, preroll=preroll,
        safety_agent=safety_agent, safety_tick=safety_tick,
        balance_coordinates=(
            duration_rotation, int(initial[0]) * 2 + int(initial[1]), episode % 2,
            episode % 4, (episode // 4) % 4, horizon - last_phase_start,
        ),
    )


def balance_report(episodes: list[ExogenousEpisode]) -> dict[str, object]:
    if not episodes:
        return {"episodes": 0, "balanced": False}
    from collections import Counter
    durations = episodes[0].durations
    duration_counts = Counter(row.balance_coordinates[0] for row in episodes)
    latent_counts = Counter(row.balance_coordinates[1] for row in episodes)
    change_starts = Counter(row.balance_coordinates[2] for row in episodes)
    readiness_slots = Counter(row.balance_coordinates[3] for row in episodes)
    noise_slots = Counter(row.balance_coordinates[4] for row in episodes)
    terminal_by_rotation: dict[str, Counter[int]] = {}
    for rotation in range(len(durations)):
        terminal_by_rotation[str(rotation)] = Counter(
            row.balance_coordinates[5] for row in episodes
            if row.balance_coordinates[0] == rotation
        )
    changed_counts = [
        int(sum(int(row.changed[:, role].sum()) for row in episodes)) for role in range(2)
    ]
    def spread(counter: Counter[int], expected: int) -> int:
        values = [counter[index] for index in range(expected)]
        return max(values) - min(values)
    balanced = (
        spread(duration_counts, len(durations)) <= 1
        and spread(latent_counts, 4) <= 1
        and spread(change_starts, 2) <= 1
        and spread(readiness_slots, 4) <= 1
        and spread(noise_slots, 4) <= 1
        and (episodes[0].joint_mismatch or abs(changed_counts[0] - changed_counts[1]) <= 1)
    )
    return {
        "episodes": len(episodes), "duration_support": list(durations),
        "duration_rotation_counts": dict(sorted(duration_counts.items())),
        "initial_latent_pair_counts": dict(sorted(latent_counts.items())),
        "off_changed_agent_start_counts": dict(sorted(change_starts.items())),
        "actual_changed_agent_counts": changed_counts,
        "readiness_namespace_slot_counts": dict(sorted(readiness_slots.items())),
        "noise_namespace_slot_counts": dict(sorted(noise_slots.items())),
        "terminal_truncation_position_counts_by_duration_rotation": {
            key: dict(sorted(value.items())) for key, value in terminal_by_rotation.items()
        },
        "balance_rule": "categorical counts differ by at most one; OFF actual change counts differ by at most one",
        "balanced": balanced,
    }


class HazardActor(Protocol):
    def probabilities(self, features: np.ndarray) -> np.ndarray: ...


@dataclass
class TickTrainingRecord:
    actor_features: np.ndarray
    critic_features: np.ndarray
    actions: np.ndarray
    old_log_probs: np.ndarray
    policy_mask: np.ndarray
    reward: float
    value: float
    entropy: np.ndarray


@dataclass
class EpisodeResult:
    arm: str
    normalized_return: float
    packet_successes: int
    stale_ticks: int
    renewal_downtime: int
    renewal_cost: float
    unsafe_normal_renewal_cost: float
    ordinary_renewals: tuple[int, int]
    forced_max_renewals: tuple[int, int]
    emergency_renewals: tuple[int, int]
    total_renewals: tuple[int, int]
    renewal_times: tuple[tuple[int, ...], tuple[int, ...]]
    ordinary_times: tuple[tuple[int, ...], tuple[int, ...]]
    ordinary_periods: tuple[tuple[int, ...], tuple[int, ...]]
    renewals_ready: tuple[int, int]
    pending_delays: tuple[int, ...]
    simultaneous_renewal_ticks: int
    boundary_delays: tuple[int, ...]
    request_counts: tuple[int, int]
    eligible_request_counts: tuple[int, int]
    forced_event_counts: tuple[int, int]
    actor_forward_calls: int
    messages: int
    transmitted_bits: int
    physics_ticks: int
    emergency_immediate: bool
    cap_violation: bool
    training_records: list[TickTrainingRecord] = field(default_factory=list)


def actor_features(
    *, role: int, age: int, history: list[int], skill: int, ready: int,
    tick: int, horizon: int, ordinary_remaining: int, pending_age: int,
    previous_partner_bits: tuple[int, int], coord: bool,
) -> np.ndarray:
    partner = previous_partner_bits if coord else (0, 0)
    return np.asarray([
        1.0 if role == 0 else 0.0,
        1.0 if role == 1 else 0.0,
        age / 32.0,
        sum(value != skill for value in history[-3:]) / 3.0,
        1.0 if ready else -1.0,
        tick / max(1, horizon - 1),
        ordinary_remaining / 31.0,
        max(0, pending_age) / 2.0,
        float(partner[0]),
        float(partner[1]),
    ], dtype=np.float32)


def critic_features(
    exogenous: ExogenousEpisode, tick: int, skills: list[int], ages: list[int],
    pending: list[int], ordinary_remaining: list[int],
) -> np.ndarray:
    return np.asarray([
        *exogenous.latent[tick].tolist(), *exogenous.observations[tick].tolist(),
        *skills, *(age / 32.0 for age in ages),
        *exogenous.readiness[tick].tolist(),
        *(max(0, age) / 2.0 for age in pending),
        *(remaining / 31.0 for remaining in ordinary_remaining),
        tick / max(1, exogenous.horizon - 1),
    ], dtype=np.float32)


def validate_schedule(
    exogenous: ExogenousEpisode,
    schedule: tuple[tuple[int, ...], tuple[int, ...]],
) -> tuple[bool, str]:
    ages = [0, 0]
    ordinary = [0, 0]
    total = [0, 0]
    scheduled = [set(schedule[0]), set(schedule[1])]
    if any(len(times) != len(set(times)) for times in schedule):
        return False, "duplicate schedule tick"
    for tick in range(exogenous.horizon):
        for role in range(2):
            safety = exogenous.safety_agent == role and exogenous.safety_tick == tick
            max_forced = ages[role] >= K_MAX and not safety
            if tick in scheduled[role]:
                if safety or max_forced:
                    return False, "ordinary schedule collides with forced renewal"
                if ages[role] < K_MIN:
                    return False, "ordinary schedule violates k_min"
                ordinary[role] += 1
                total[role] += 1
                ages[role] = 0
            elif safety or max_forced:
                total[role] += 1
                ages[role] = 0
            if ordinary[role] > ORDINARY_CAP or total[role] > TOTAL_CAP:
                return False, "schedule violates renewal cap"
        ages = [age + 1 for age in ages]
    return True, "eligible"


def run_episode(
    exogenous: ExogenousEpisode, *, arm: str,
    actor: HazardActor | None = None,
    critic_value: Callable[[np.ndarray], float] | None = None,
    schedule: tuple[tuple[int, ...], tuple[int, ...]] | None = None,
    collect_training: bool = False,
) -> EpisodeResult:
    learned = arm in {"LOCAL", "COORD"}
    coord = arm == "COORD"
    fixed_k = int(arm.split("-")[1]) if arm.startswith("FIXED-") else None
    oracle = arm == "STAGE-ORACLE"
    if learned and actor is None:
        raise ValueError("learned arm requires actor")
    if schedule is not None:
        eligible, reason = validate_schedule(exogenous, schedule)
        if not eligible:
            raise ValueError(reason)
    histories = [[int(value) for value in exogenous.preroll[:, role]] for role in range(2)]
    skills = [majority(history) for history in histories]
    ages = [0, 0]
    pending = [-1, -1]
    ordinary_remaining = [ORDINARY_CAP, ORDINARY_CAP]
    previous_bits = [(0, 0), (0, 0)]
    renewal_times: list[list[int]] = [[], []]
    ordinary_times: list[list[int]] = [[], []]
    realized_ordinary_periods: list[list[int]] = [[], []]
    ordinary_count = [0, 0]
    forced_max = [0, 0]
    emergency = [0, 0]
    renewals_ready = [0, 0]
    requests = [0, 0]
    eligible_requests = [0, 0]
    pending_delays: list[int] = []
    reward_sum = 0.0
    packets = stale = downtime = unsafe_normal = simultaneous = 0
    records: list[TickTrainingRecord] = []
    outstanding_boundaries: list[list[int]] = [[], []]
    boundary_delays: list[int] = []
    oracle_pending = [False, False]
    oracle_joint = False
    scheduled_sets = [set(schedule[0]), set(schedule[1])] if schedule else [set(), set()]
    for tick in range(exogenous.horizon):
        ready = [int(value) for value in exogenous.readiness[tick]]
        for role in range(2):
            histories[role].append(int(exogenous.observations[tick, role]))
            if exogenous.changed[tick, role]:
                outstanding_boundaries[role].append(tick)
                if oracle:
                    oracle_pending[role] = True
        if oracle and exogenous.boundary[tick] and exogenous.joint_mismatch:
            oracle_joint = True
        features = np.stack([
            actor_features(
                role=role, age=ages[role], history=histories[role], skill=skills[role],
                ready=ready[role], tick=tick, horizon=exogenous.horizon,
                ordinary_remaining=ordinary_remaining[role], pending_age=pending[role],
                previous_partner_bits=previous_bits[1 - role], coord=coord,
            ) for role in range(2)
        ])
        critic_input = critic_features(
            exogenous, tick, skills, ages, pending, ordinary_remaining
        )
        predecision_value = float(critic_value(critic_input)) if critic_value else 0.0
        forced_kind: list[str | None] = [None, None]
        for role in range(2):
            if exogenous.safety_agent == role and exogenous.safety_tick == tick:
                forced_kind[role] = "safety"
            elif ages[role] >= K_MAX:
                forced_kind[role] = "max"
        # One (2, 10) shared-network invocation at each physical tick is two
        # actor-sized per-agent forwards.  Non-learned arms ignore the output.
        network_probabilities = (
            np.asarray(actor.probabilities(features), dtype=np.float64)
            if actor is not None else np.full(2, 0.5, dtype=np.float64)
        )
        probabilities = network_probabilities if learned else np.full(2, 0.5, dtype=np.float64)
        if probabilities.shape != (2,):
            raise ValueError("actor must return two probabilities")
        probabilities = np.clip(probabilities, 1e-7, 1.0 - 1e-7)
        actions = np.zeros(2, dtype=np.float32)
        log_probs = np.zeros(2, dtype=np.float32)
        masks = np.zeros(2, dtype=np.float32)
        entropies = -(probabilities * np.log(probabilities) + (1 - probabilities) * np.log(1 - probabilities))
        broadcast = [(0, ready[0]), (0, ready[1])]
        if learned:
            for role in range(2):
                if forced_kind[role] is None:
                    request = int(counter_uniform(
                        "hazard_uniform", exogenous.namespace, exogenous.seed,
                        exogenous.episode, tick, role
                    ) < probabilities[role])
                    actions[role] = request
                    masks[role] = 1.0
                    log_probs[role] = np.log(probabilities[role] if request else 1 - probabilities[role])
                    requests[role] += request
                    broadcast[role] = (request, ready[role])
                    if request and ages[role] >= K_MIN and ordinary_remaining[role] > 0:
                        eligible_requests[role] += 1
                        if pending[role] < 0:
                            pending[role] = 0
        renew = [False, False]
        renewal_kind: list[str | None] = [None, None]
        for role in range(2):
            if forced_kind[role] is not None:
                renew[role] = True
                renewal_kind[role] = forced_kind[role]
                pending[role] = -1
                if oracle:
                    oracle_pending[role] = False
        if fixed_k is not None:
            for role in range(2):
                if not renew[role] and ages[role] >= fixed_k:
                    renew[role] = True
                    renewal_kind[role] = "ordinary"
        elif schedule is not None:
            for role in range(2):
                if not renew[role] and tick in scheduled_sets[role]:
                    renew[role] = True
                    renewal_kind[role] = "ordinary"
                    broadcast[role] = (1, ready[role])
        elif oracle:
            if oracle_joint and not all(oracle_pending):
                # A host-forced renewal may resolve one side of a formerly
                # joint change.  The still-stale side then takes its own
                # earliest legal ready renewal rather than waiting for a pair
                # that no longer needs renewal.
                oracle_joint = False
            if oracle_joint and all(oracle_pending) and all(ready) and all(age >= K_MIN for age in ages):
                for role in range(2):
                    if not renew[role]:
                        renew[role] = True
                        renewal_kind[role] = "ordinary"
                        oracle_pending[role] = False
                oracle_joint = False
            if not oracle_joint:
                for role in range(2):
                    if (not renew[role] and oracle_pending[role] and ready[role]
                            and ages[role] >= K_MIN):
                        renew[role] = True
                        renewal_kind[role] = "ordinary"
                        oracle_pending[role] = False
        elif arm == "LOCAL":
            for role in range(2):
                if not renew[role] and pending[role] >= 0 and (ready[role] or pending[role] >= PENDING_WINDOW):
                    renew[role] = True
                    renewal_kind[role] = "ordinary"
        elif arm == "COORD":
            if all(value >= 0 for value in pending) and all(ready) and not any(renew):
                renew = [True, True]
                renewal_kind = ["ordinary", "ordinary"]
            else:
                for role in range(2):
                    if not renew[role] and pending[role] >= PENDING_WINDOW:
                        renew[role] = True
                        renewal_kind[role] = "ordinary"
        for role in range(2):
            if not renew[role]:
                continue
            renewal_times[role].append(tick)
            renewals_ready[role] += ready[role]
            if renewal_kind[role] == "ordinary":
                if ordinary_remaining[role] <= 0:
                    raise RuntimeError("ordinary renewal cap exhausted")
                ordinary_remaining[role] -= 1
                ordinary_count[role] += 1
                ordinary_times[role].append(tick)
                realized_ordinary_periods[role].append(ages[role])
                if pending[role] >= 0:
                    pending_delays.append(pending[role])
                if not ready[role]:
                    unsafe_normal += 1
            elif renewal_kind[role] == "max":
                if ordinary_remaining[role] <= 0:
                    raise RuntimeError("max-age ordinary token unavailable")
                ordinary_remaining[role] -= 1
                ordinary_count[role] += 1
                forced_max[role] += 1
            elif renewal_kind[role] == "safety":
                emergency[role] += 1
            pending[role] = -1
            skills[role] = majority(histories[role][-3:])
            ages[role] = 0
            if outstanding_boundaries[role]:
                boundary_delays.extend(tick - boundary_tick for boundary_tick in outstanding_boundaries[role])
                outstanding_boundaries[role].clear()
        if all(renew):
            simultaneous += 1
        packet = int(not any(renew) and all(skills[role] == int(exogenous.latent[tick, role]) for role in range(2)))
        packets += packet
        stale += int(any(skills[role] != int(exogenous.latent[tick, role]) for role in range(2)))
        downtime += int(any(renew))
        reward = packet - 0.02 * sum(renew) - 0.10 * sum(
            renewal_kind[role] == "ordinary" and not ready[role] for role in range(2)
        )
        reward_sum += reward
        if collect_training:
            records.append(TickTrainingRecord(
                actor_features=features, critic_features=critic_input, actions=actions,
                old_log_probs=log_probs, policy_mask=masks, reward=float(reward),
                value=predecision_value, entropy=entropies.astype(np.float32),
            ))
        previous_bits = broadcast
        for role in range(2):
            if pending[role] >= 0:
                pending[role] += 1
            ages[role] += 1
    total = [ordinary_count[role] + emergency[role] for role in range(2)]
    cap_violation = any(ordinary_count[role] > ORDINARY_CAP or total[role] > TOTAL_CAP for role in range(2))
    emergency_immediate = exogenous.safety_agent is None or (
        emergency[exogenous.safety_agent] == 1
        and exogenous.safety_tick in renewal_times[exogenous.safety_agent]
        and emergency[1 - exogenous.safety_agent] == 0
    )
    periods = tuple(tuple(periods) for periods in realized_ordinary_periods)
    return EpisodeResult(
        arm=arm, normalized_return=reward_sum / exogenous.horizon,
        packet_successes=packets, stale_ticks=stale, renewal_downtime=downtime,
        renewal_cost=0.02 * sum(total), unsafe_normal_renewal_cost=0.10 * unsafe_normal,
        ordinary_renewals=tuple(ordinary_count), forced_max_renewals=tuple(forced_max),
        emergency_renewals=tuple(emergency), total_renewals=tuple(total),
        renewal_times=tuple(tuple(times) for times in renewal_times),
        ordinary_times=tuple(tuple(times) for times in ordinary_times),
        ordinary_periods=periods, renewals_ready=tuple(renewals_ready),
        pending_delays=tuple(pending_delays), simultaneous_renewal_ticks=simultaneous,
        boundary_delays=tuple(boundary_delays), request_counts=tuple(requests),
        eligible_request_counts=tuple(eligible_requests), forced_event_counts=tuple(
            forced_max[role] + emergency[role] for role in range(2)
        ), actor_forward_calls=2 * exogenous.horizon, messages=2 * exogenous.horizon,
        transmitted_bits=4 * exogenous.horizon, physics_ticks=exogenous.horizon,
        emergency_immediate=emergency_immediate, cap_violation=cap_violation,
        training_records=records,
    )
