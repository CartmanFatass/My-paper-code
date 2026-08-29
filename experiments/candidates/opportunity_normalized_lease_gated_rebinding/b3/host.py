"""B3-local reproduction of the protected B2 fixed-policy host and counter semantics."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
from typing import Protocol

import numpy as np

from .config import ACTIONS, HORIZON, IID_SCHEDULE, LEASE_TICKS, ROLES

_COUNTER_PREFIX = "ONLGR_B2_REV02"


def counter_u64(domain: str, *coordinates: object) -> int:
    payload = "\x1f".join((_COUNTER_PREFIX, domain, *(str(v) for v in coordinates))).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def counter_uniform(domain: str, *coordinates: object) -> float:
    return ((counter_u64(domain, *coordinates) >> 11) + 0.5) / float(1 << 53)


def counter_bit(domain: str, *coordinates: object) -> int:
    return int(counter_u64(domain, *coordinates) & 1)


def counter_bernoulli(probability: float, domain: str, *coordinates: object) -> int:
    return int(counter_uniform(domain, *coordinates) < probability)


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
    safety_agent: None
    safety_tick: None
    routine_boundaries: tuple[int, ...]


def generate_episode(
    *, seed: int, episode_index: int, namespace: str, schedule: str = IID_SCHEDULE,
    horizon: int = HORIZON, safety: bool = False,
) -> ExogenousEpisode:
    if safety:
        raise ValueError("B3 has no safety panel")
    if schedule != IID_SCHEDULE:
        raise ValueError("B3 permits only RAND-IID-4-16-32")
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
    return ExogenousEpisode(
        seed=seed, episode_index=episode_index, namespace=namespace, schedule=schedule,
        mode=mode, sensors=sensors, preroll=preroll,
        initial_bindings=(
            counter_bit("INITIAL_BINDING", namespace, seed, episode_index, 0),
            counter_bit("INITIAL_BINDING", namespace, seed, episode_index, 1),
        ),
        initial_plan_ages=ages, safety_agent=None, safety_tick=None, routine_boundaries=(0,),
    )


class FixedPolicyProtocol(Protocol):
    policy_id: str
    force_keep: bool
    def policy(self, features: np.ndarray, exposure: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]: ...
    def value(self, features: np.ndarray) -> float: ...
    def joint_log_probability(
        self, features: np.ndarray, exposure: np.ndarray,
        actions: np.ndarray, policy_mask: np.ndarray,
    ) -> float: ...


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


@dataclass(frozen=True)
class EpisodeResult:
    policy_id: str
    namespace: str
    seed: int
    episode_index: int
    normalized_return: float
    service: float
    action_cost: float
    physics_ticks: int
    routine_boundary_ticks: tuple[int, ...]
    iid_interval_draws: tuple[int, ...]
    iid_draw_records: tuple[tuple[int, int, int, bool], ...]
    iid_terminal_censored_duration: int | None
    legal_action_rows: tuple[tuple[int, int, int, bool], ...]
    rate_rows: tuple[dict[str, object], ...]
    identity_rows: tuple[BoundaryIdentity, ...]
    identity_unique: bool
    reward_service_cost_exact: bool
    segment_ownership_exact: bool
    terminal_boundary_absent: bool
    plan_age_sum: int
    physics_ledger: tuple[tuple[object, ...], ...]


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


def next_iid_interval(episode: ExogenousEpisode, ordinal: int) -> int:
    # This intentionally reproduces B2's protected coordinate list and post-action draw order.
    uniform = counter_uniform("RAND_IID_NEXT_K", episode.seed, episode.episode_index, ordinal)
    return 4 if uniform < 1.0 / 3.0 else 16 if uniform < 2.0 / 3.0 else 32


def run_episode(
    episode: ExogenousEpisode, *, policy: FixedPolicyProtocol,
    retain_detailed_ledgers: bool = True,
) -> EpisodeResult:
    if episode.schedule != IID_SCHEDULE or len(episode.mode) != HORIZON:
        raise ValueError("B3 episode is not on the frozen host coordinate")
    boundaries = {0}
    histories = [deque((int(v) for v in episode.preroll[:, role]), maxlen=8) for role in range(2)]
    bindings = list(episode.initial_bindings)
    ages = list(episode.initial_plan_ages)
    busy = [0, 0]
    leases = [-8, -8]
    previous_boundary = [-8, -8]
    own_boundary_index = [0, 0]
    rewards = np.zeros(HORIZON, dtype=np.float64)
    services = np.zeros(HORIZON, dtype=np.float64)
    routine_ticks: list[int] = []
    iid_draws: list[int] = []
    iid_records: list[tuple[int, int, int, bool]] = []
    legal_rows: list[tuple[int, int, int, bool]] = []
    rate_rows: list[dict[str, object]] = []
    identities: list[BoundaryIdentity] = []
    physics: list[tuple[object, ...]] = []
    iid_ordinal = 0
    censored: int | None = None
    action_cost = 0.0
    plan_age_sum = 0

    for tick in range(HORIZON):
        for role in range(2):
            histories[role].append(int(episode.sensors[tick, role]))
        routine = tick in boundaries
        actions = np.zeros(2, dtype=np.int64)
        if routine:
            routine_ticks.append(tick)
            delta = [tick - previous_boundary[role] for role in range(2)]
            exposures = [eligible_exposure(previous_boundary[role], leases[role], tick) for role in range(2)]
            timing = np.stack([
                timing_features(
                    age=ages[role], lease_expiry=leases[role], busy=busy[role], tick=tick,
                    cause="ROUTINE_CALLBACK", delta=delta[role], exposure=exposures[role],
                ) for role in range(2)
            ])
            critic_row = critic_features(
                mode=int(episode.mode[tick]), timing_rows=timing, bindings=bindings,
                ages=ages, leases=leases, busy=busy, histories=histories, tick=tick,
            )
            policy.value(critic_row)
            logits, rates, probabilities = policy.policy(timing, np.asarray(exposures, dtype=np.float64))
            for role in range(2):
                exposure = int(exposures[role])
                if exposure > 0:
                    actions[role] = 0 if policy.force_keep else sample_action(
                        float(probabilities[role]), episode, tick, role,
                    )
                    legal_rows.append((exposure, int(actions[role]), role, tick == 0))
                if retain_detailed_ledgers:
                    rate_rows.append({
                        "tick": tick, "role": ROLES[role], "cause": "ROUTINE_CALLBACK",
                        "timing_features": tuple(float(value) for value in timing[role]),
                        "exposure": exposure, "logit": float(logits[role]),
                        "lambda": float(rates[role]), "event_probability": float(probabilities[role]),
                        "policy_score": exposure > 0 and not policy.force_keep, "forced": False,
                        "action": ACTIONS[int(actions[role])],
                    })
            for role in range(2):
                action = int(actions[role])
                if action == 1:
                    ages[role] = 0
                    busy[role] = 1
                    action_cost += 0.02
                    leases[role] = tick + LEASE_TICKS
                elif action == 2:
                    bindings[role] ^= 1
                    ages[role] = 0
                    busy[role] = 2
                    action_cost += 0.04
                    leases[role] = tick + LEASE_TICKS
                previous_boundary[role] = tick
                identities.append(BoundaryIdentity(
                    episode_id=f"{episode.namespace}:{episode.seed}:{episode.episode_index}",
                    agent_role=ROLES[role], owner_epoch=0,
                    own_boundary_index=own_boundary_index[role], behavior_version=policy.policy_id,
                    cause="ROUTINE_CALLBACK", action=ACTIONS[action], initial_anchor_action=tick == 0,
                ))
                own_boundary_index[role] += 1

            interval = next_iid_interval(episode, iid_ordinal)
            iid_draws.append(interval)
            iid_records.append((iid_ordinal, tick, interval, False))
            iid_ordinal += 1
            next_tick = tick + interval
            if next_tick < HORIZON:
                boundaries.add(next_tick)
            else:
                censored = HORIZON - tick

        service = int(
            bindings[0] == int(episode.mode[tick]) and bindings[1] == int(episode.mode[tick])
            and busy[0] == 0 and busy[1] == 0
        ) * max(0.0, 1.0 - (ages[0] + ages[1]) / 128.0)
        tick_cost = sum(0.02 if action == 1 else 0.04 if action == 2 else 0.0 for action in actions) if routine else 0.0
        services[tick] = service
        rewards[tick] = service - tick_cost
        plan_age_sum += sum(ages)
        if retain_detailed_ledgers:
            physics.append((
                tick, int(episode.mode[tick]), int(episode.sensors[tick, 0]), int(episode.sensors[tick, 1]),
                bindings[0], bindings[1], ages[0], ages[1], busy[0], busy[1], leases[0], leases[1],
                float(service), float(rewards[tick]), routine,
            ))
        for role in range(2):
            if busy[role] > 0:
                busy[role] -= 1
            ages[role] = min(64, ages[role] + 1)

    direct_return = float(rewards.sum(dtype=np.float64) / HORIZON)
    mean_service = float(services.sum(dtype=np.float64) / HORIZON)
    mean_cost = float(action_cost / HORIZON)
    return EpisodeResult(
        policy_id=policy.policy_id, namespace=episode.namespace, seed=episode.seed,
        episode_index=episode.episode_index, normalized_return=direct_return,
        service=mean_service, action_cost=mean_cost, physics_ticks=HORIZON,
        routine_boundary_ticks=tuple(routine_ticks), iid_interval_draws=tuple(iid_draws),
        iid_draw_records=tuple(iid_records), iid_terminal_censored_duration=censored,
        legal_action_rows=tuple(legal_rows), rate_rows=tuple(rate_rows), identity_rows=tuple(identities),
        identity_unique=len(identities) == len({identity.key for identity in identities}),
        reward_service_cost_exact=abs(direct_return - (mean_service - mean_cost)) <= 1e-12,
        segment_ownership_exact=bool(routine_ticks and routine_ticks[0] == 0),
        terminal_boundary_absent=HORIZON not in boundaries, plan_age_sum=plan_age_sum,
        physics_ledger=tuple(physics),
    )
