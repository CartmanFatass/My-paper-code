"""Frozen core for the UAV charge-rotation roster G2 experiment.

This module keeps Scenario-7/S3 reward and physical dynamics intact and owns
only the registered energy-profile permutation, charge-induced service
lifecycle, current-only views, matched recurrent policy, recurrent PPO data,
evaluation-only controls and episode/source accounting used by the G2 runner.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from enum import Enum, IntEnum
import hashlib
import math
import multiprocessing as mp
from multiprocessing.connection import Connection
import traceback
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment
import torch

from config_1 import Config
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from ha_ctse_process.continuous_roster_policy import (
    ContinuousRosterPolicy,
    ContinuousStepOutput,
)


PHYSICAL_UAVS = 8
ACTION_DIM = 4
HORIZON = 1500
REJOIN_WINDOW = 60
REJOIN_BATTERY_RATIO = 0.80
QOS_TARGET = 0.90

FIXED_MASK_REC = "FIXED_MASK_REC"
PREFIX_NORMALIZED_OPEN_ROSTER = "PREFIX_NORMALIZED_OPEN_ROSTER"
ROUTING_MODES = frozenset({FIXED_MASK_REC, PREFIX_NORMALIZED_OPEN_ROSTER})
CONSTRUCTIVE_CHARGE_ROTATION = "CONSTRUCTIVE_CHARGE_ROTATION"
NO_PROACTIVE_ROTATION = "NO_PROACTIVE_ROTATION"

GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50
PPO_PASSES = 4


class EnergyProfile(str, Enum):
    IID = "IID"
    LOW_ENERGY = "LOW_ENERGY"
    SYNCHRONIZED_PRESSURE = "SYNCHRONIZED_PRESSURE"


ENERGY_PROFILE_VALUES: dict[EnergyProfile, tuple[float, ...]] = {
    EnergyProfile.IID: (0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90),
    EnergyProfile.LOW_ENERGY: (0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80),
    EnergyProfile.SYNCHRONIZED_PRESSURE: (
        0.55,
        0.55,
        0.60,
        0.60,
        0.65,
        0.65,
        0.70,
        0.70,
    ),
}


class LifecycleState(IntEnum):
    ACTIVE = 0
    CHARGE_ABSENT = 1
    TERMINAL = 2


class LifecycleEventKind(str, Enum):
    LEAVE = "LEAVE"
    QUEUE = "QUEUE"
    CHARGE = "CHARGE"
    REJOIN = "REJOIN"
    TERMINAL = "TERMINAL"


@dataclass(frozen=True)
class G2EpisodeLedger:
    profile: EnergyProfile
    episode_id: int
    initial_energy_ratios: np.ndarray
    energy_permutation: np.ndarray
    ledger_id: str

    def __post_init__(self) -> None:
        profile = EnergyProfile(self.profile)
        energy = np.asarray(self.initial_energy_ratios, dtype=np.float64).copy()
        permutation = np.asarray(self.energy_permutation, dtype=np.int64).copy()
        if energy.shape != (PHYSICAL_UAVS,) or permutation.shape != (PHYSICAL_UAVS,):
            raise ValueError("G2 energy ledger requires exactly eight physical rows")
        if sorted(permutation.tolist()) != list(range(PHYSICAL_UAVS)):
            raise ValueError("G2 energy ledger permutation is not bijective")
        expected = np.asarray(ENERGY_PROFILE_VALUES[profile], dtype=np.float64)[permutation]
        if not np.array_equal(energy, expected):
            raise ValueError("G2 energy ledger does not match its registered profile")
        energy.setflags(write=False)
        permutation.setflags(write=False)
        object.__setattr__(self, "profile", profile)
        object.__setattr__(self, "episode_id", int(self.episode_id))
        object.__setattr__(self, "initial_energy_ratios", energy)
        object.__setattr__(self, "energy_permutation", permutation)


def make_g2_episode_ledger(
    profile: EnergyProfile | str,
    episode_id: int,
    *,
    energy_seed: int,
) -> G2EpisodeLedger:
    """Create an episode-addressed permutation without touching another RNG."""

    chosen = EnergyProfile(profile)
    profile_index = tuple(EnergyProfile).index(chosen)
    rng = np.random.default_rng(
        np.random.SeedSequence(
            [int(energy_seed), int(episode_id), int(profile_index), 0x4732]
        )
    )
    permutation = rng.permutation(PHYSICAL_UAVS).astype(np.int64)
    values = np.asarray(ENERGY_PROFILE_VALUES[chosen], dtype=np.float64)[permutation]
    code = "-".join(str(int(value)) for value in permutation)
    return G2EpisodeLedger(
        profile=chosen,
        episode_id=int(episode_id),
        initial_energy_ratios=values,
        energy_permutation=permutation,
        ledger_id=f"{chosen.value}/{int(episode_id)}/{code}",
    )


@dataclass(frozen=True)
class LifecycleEvent:
    physical_step: int
    owner: int
    kind: LifecycleEventKind
    station: int
    battery_ratio: float


@dataclass(frozen=True)
class G2CurrentView:
    observations: np.ndarray
    active_mask: np.ndarray
    critic_state: np.ndarray
    lifecycle_state: np.ndarray
    physical_positions: np.ndarray
    battery_ratios: np.ndarray
    station_occupancy: np.ndarray
    queue_lengths: np.ndarray
    physical_step: int


@dataclass(frozen=True)
class G2Transition:
    view: G2CurrentView
    reward: float
    qos_satisfaction_ratio: float
    safety_score_before_pbrs: float
    return_constraint_cost: float
    cutoff_event_count: int
    depletion_event_count: int
    terminated: bool
    truncated: bool
    executed_action_mask: np.ndarray
    physical_action_mask: np.ndarray
    service_actions: np.ndarray
    events: tuple[LifecycleEvent, ...]
    source_facts: Mapping[str, Any]


class UAVChargeRotationEnv(UAVEnergyAwareRelayEnv):
    """S7-S3 with charge-induced service lifecycle over fixed physical slots."""

    def __init__(
        self,
        ledger: G2EpisodeLedger,
        environment_seed: int,
        env_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        self.episode_ledger = ledger
        self.environment_seed = int(environment_seed)
        self._lifecycle_state = np.full(
            PHYSICAL_UAVS, int(LifecycleState.ACTIVE), dtype=np.int8
        )
        self._assigned_station = np.full(PHYSICAL_UAVS, -1, dtype=np.int8)
        self._last_lifecycle_boundary = -1
        self._episode_lifecycle_events: list[LifecycleEvent] = []
        self._reset_namespace_rngs(self.environment_seed)
        kwargs = dict(env_kwargs or {})
        unsupported = set(kwargs).difference({"render_mode"})
        if unsupported:
            raise ValueError(
                "env_kwargs cannot override frozen S7-S3 science fields: "
                + ", ".join(sorted(unsupported))
            )
        super().__init__(config=Config("S7-S3"), seed=self.environment_seed, **kwargs)
        if self.n_uavs != PHYSICAL_UAVS or self.action_dim != ACTION_DIM:
            raise RuntimeError("G2 requires physical width eight and action width four")
        if self.energy_stage != "S3" or self.max_steps != HORIZON:
            raise RuntimeError("G2 requires the registered S7-S3 physical horizon")
        if self.battery_capacity_wh != 160.0:
            raise RuntimeError("G2 battery capacity drifted from 160 Wh")
        if self.n_charging_stations != 2 or not np.array_equal(
            self.charging_station_capacity[:2], np.ones(2)
        ):
            raise RuntimeError("G2 requires two one-slot charging stations")
        if self.failure_enabled:
            raise RuntimeError("G2 forbids temporary physical failures")

    @staticmethod
    def _namespace_random_state(seed: int, namespace: int) -> np.random.RandomState:
        word = np.random.SeedSequence([int(seed), int(namespace)]).generate_state(1)[0]
        return np.random.RandomState(int(word))

    def _reset_namespace_rngs(self, seed: int) -> None:
        # Physical initialization, users, stations and discarded base-energy
        # draws have disjoint streams. Channel randomness is physical-step
        # addressed below, so lifecycle-triggered rematerialization cannot
        # desynchronize paired arms.
        self._initial_rng = self._namespace_random_state(seed, 1)
        self._user_rng = self._namespace_random_state(seed, 2)
        self._station_rng = self._namespace_random_state(seed, 3)
        self._energy_reset_rng = self._namespace_random_state(seed, 4)

    def _with_namespace_rng(
        self, attribute: str, method: Any, *args: Any, **kwargs: Any
    ) -> Any:
        previous = getattr(self, "np_random", None)
        self.np_random = getattr(self, attribute)
        try:
            return method(*args, **kwargs)
        finally:
            if previous is not None:
                self.np_random = previous

    def _init_ground_bs(self):
        return self._with_namespace_rng("_initial_rng", super()._init_ground_bs)

    def _init_uav_positions(self):
        return self._with_namespace_rng("_initial_rng", super()._init_uav_positions)

    def _init_charging_stations(self, randomize: bool | None = None):
        return self._with_namespace_rng(
            "_station_rng", super()._init_charging_stations, randomize
        )

    def _generate_user_positions(self):
        return self._with_namespace_rng("_user_rng", super()._generate_user_positions)

    def _init_user_velocities(self):
        return self._with_namespace_rng("_user_rng", super()._init_user_velocities)

    def _initialize_user_waypoints_rpgm(self):
        return self._with_namespace_rng(
            "_user_rng", super()._initialize_user_waypoints_rpgm
        )

    def _move_users(self):
        return self._with_namespace_rng("_user_rng", super()._move_users)

    def _update_channel_state(self):
        step = int(getattr(self, "current_step", 0))
        channel_rng = self._namespace_random_state(
            self.environment_seed, 10_000 + max(step, 0)
        )
        previous = getattr(self, "np_random", None)
        self.np_random = channel_rng
        try:
            return super()._update_channel_state()
        finally:
            if previous is not None:
                self.np_random = previous

    def _reset_energy_state(self):
        self._with_namespace_rng("_energy_reset_rng", super()._reset_energy_state)
        self.uav_battery_ratios = self.episode_ledger.initial_energy_ratios.copy()
        self._update_return_energy_state()
        self.prev_energy_failure_mask = self._energy_failure_mask()
        self.cutoff_event_seen[:] = False
        self.depletion_event_seen[:] = False

    def _update_uav_failures(self) -> None:
        self.uav_failure_timers[:] = 0
        self.uav_failed[:] = False

    @property
    def lifecycle_states(self) -> np.ndarray:
        return np.asarray(
            [LifecycleState(int(value)) for value in self._lifecycle_state],
            dtype=object,
        )

    @property
    def service_active_mask(self) -> np.ndarray:
        return self._lifecycle_state == int(LifecycleState.ACTIVE)

    @property
    def lifecycle_events(self) -> tuple[LifecycleEvent, ...]:
        return tuple(self._episode_lifecycle_events)

    def _is_uav_unavailable(self, uav_idx: int) -> bool:
        lifecycle = getattr(self, "_lifecycle_state", None)
        if lifecycle is not None and int(lifecycle[int(uav_idx)]) != int(
            LifecycleState.ACTIVE
        ):
            return True
        return super()._is_uav_unavailable(uav_idx)

    def _communication_unavailable_mask(self) -> np.ndarray:
        unavailable = super()._communication_unavailable_mask()
        lifecycle = getattr(self, "_lifecycle_state", None)
        if lifecycle is not None:
            unavailable |= lifecycle != int(LifecycleState.ACTIVE)
        return unavailable

    def _station_distance(self, owner: int, station: int) -> float:
        if not 0 <= int(station) < self.n_charging_stations:
            return float("inf")
        return float(
            np.linalg.norm(
                self.charging_station_positions[int(station)]
                - self.uav_positions[int(owner)]
            )
        )

    def _captured_station(self, owner: int) -> int:
        station, _vector, distance = self._nearest_charging_station(int(owner))
        return int(station) if distance <= self.charging_capture_radius_m else -1

    def _event(self, owner: int, kind: LifecycleEventKind, station: int) -> LifecycleEvent:
        return LifecycleEvent(
            physical_step=int(self.current_step),
            owner=int(owner),
            kind=LifecycleEventKind(kind),
            station=int(station),
            battery_ratio=float(self.uav_battery_ratios[int(owner)]),
        )

    def _synchronize_lifecycle(self, *, force: bool = False) -> tuple[LifecycleEvent, ...]:
        step = int(getattr(self, "current_step", 0))
        if not force and step == self._last_lifecycle_boundary:
            return ()
        self._last_lifecycle_boundary = step
        events: list[LifecycleEvent] = []
        changed = False
        for owner in range(PHYSICAL_UAVS):
            state = LifecycleState(int(self._lifecycle_state[owner]))
            battery = float(self.uav_battery_ratios[owner])
            captured_station = self._captured_station(owner)
            captured = captured_station >= 0
            if state is LifecycleState.ACTIVE:
                requested = bool(self.uav_dock_requests[owner])
                target = int(self.uav_target_stations[owner])
                if battery <= 0.0 and not captured:
                    self._lifecycle_state[owner] = int(LifecycleState.TERMINAL)
                    self._assigned_station[owner] = -1
                    events.append(self._event(owner, LifecycleEventKind.TERMINAL, -1))
                    changed = True
                elif (requested and captured) or battery <= self.service_cutoff_threshold:
                    station = target if 0 <= target < self.n_charging_stations else (
                        captured_station
                        if captured
                        else int(self._nearest_charging_station(owner)[0])
                    )
                    self._lifecycle_state[owner] = int(LifecycleState.CHARGE_ABSENT)
                    self._assigned_station[owner] = station
                    events.append(self._event(owner, LifecycleEventKind.LEAVE, station))
                    changed = True
            elif state is LifecycleState.CHARGE_ABSENT:
                station = int(self._assigned_station[owner])
                if battery >= REJOIN_BATTERY_RATIO:
                    self._lifecycle_state[owner] = int(LifecycleState.ACTIVE)
                    events.append(self._event(owner, LifecycleEventKind.REJOIN, station))
                    changed = True
                elif battery <= 0.0 and not captured:
                    self._lifecycle_state[owner] = int(LifecycleState.TERMINAL)
                    self._assigned_station[owner] = -1
                    events.append(self._event(owner, LifecycleEventKind.TERMINAL, -1))
                    changed = True
                elif bool(self.uav_charging[owner]):
                    events.append(self._event(owner, LifecycleEventKind.CHARGE, station))
                elif bool(self.last_charging_eligible[owner]):
                    events.append(self._event(owner, LifecycleEventKind.QUEUE, station))
        if changed and hasattr(self, "connections"):
            self._update_channel_state()
            self._update_uav_connections()
            self._compute_routing_paths()
        self._episode_lifecycle_events.extend(events)
        return tuple(events)

    def reset(self, seed: int | None = None, options: Any = None):
        actual_seed = self.environment_seed if seed is None else int(seed)
        self.environment_seed = actual_seed
        self._reset_namespace_rngs(actual_seed)
        self._lifecycle_state[:] = int(LifecycleState.ACTIVE)
        self._assigned_station[:] = -1
        self._last_lifecycle_boundary = -1
        self._episode_lifecycle_events.clear()
        observations, infos = super().reset(seed=actual_seed, options=options)
        self._synchronize_lifecycle(force=True)
        return observations, infos

    def _physical_sort_key(self, owner: int, peer: int) -> tuple[float, ...]:
        relative = np.asarray(
            self.uav_positions[int(peer)] - self.uav_positions[int(owner)],
            dtype=np.float64,
        )
        return (
            float(np.linalg.norm(relative)),
            float(relative[0]),
            float(relative[1]),
            float(relative[2]),
            float(self.uav_battery_ratios[int(peer)]),
            float(self._lifecycle_state[int(peer)]),
        )

    def _actor_observation(
        self, owner: int, raw_observation: np.ndarray | None = None
    ) -> np.ndarray:
        if raw_observation is None:
            raw_observation = self._get_observation(
                self.possible_agents[int(owner)]
            )["obs"]
        raw = np.asarray(raw_observation, dtype=np.float32).copy()
        if raw.shape != (self.obs_dim,):
            raise RuntimeError("raw S7-S3 actor observation width drifted")
        own = np.asarray(self.uav_positions[int(owner)], dtype=np.float64)
        height_span = max(float(self.height_range[1] - self.height_range[0]), 1.0)
        active_peers = [
            int(peer)
            for peer in np.flatnonzero(self.service_active_mask)
            if int(peer) != int(owner)
        ]
        active_peers.sort(key=lambda peer: self._physical_sort_key(owner, peer))

        raw[3:6] = 0.0
        if active_peers:
            relative = self.uav_positions[active_peers[0]] - own
            raw[3:6] = (
                float(np.linalg.norm(relative)) / self.area_size,
                relative[0] / self.area_size,
                relative[1] / self.area_size,
            )

        user_fields = 7 if self.predictive_handover else (
            6 if self.enable_soft_handover else 5
        )
        peer_start = 3 + 3 + 5 + self.max_observed_users * user_fields
        peer_stop = peer_start + self.max_observed_uavs * 4
        raw[peer_start:peer_stop] = 0.0
        local_active = [
            peer
            for peer in active_peers
            if np.linalg.norm(self.uav_positions[peer] - own) <= self.observation_radius
        ][: self.max_observed_uavs]
        for row, peer in enumerate(local_active):
            relative = np.asarray(self.uav_positions[peer] - own, dtype=np.float64)
            normalized_sinr = np.clip(
                (self._compute_uav_to_uav_sinr(owner, peer) + 10.0) / 50.0,
                0.0,
                1.0,
            )
            start = peer_start + row * 4
            raw[start : start + 4] = (
                relative[0] / self.area_size,
                relative[1] / self.area_size,
                (relative[2] - self.height_range[0]) / height_span,
                normalized_sinr,
            )

        base_width = self.obs_dim - self.energy_obs_extra_dim
        energy_stop = (
            base_width
            + self.max_energy_observed_uavs * self.energy_uav_obs_dim
        )
        owner_records = raw[base_width:energy_stop].reshape(
            self.max_energy_observed_uavs, self.energy_uav_obs_dim
        ).copy()
        anonymous = np.zeros_like(owner_records)
        physical_peers = [
            peer for peer in range(PHYSICAL_UAVS) if peer != int(owner)
        ]
        physical_peers.sort(key=lambda peer: self._physical_sort_key(owner, peer))
        for row, peer in enumerate(
            [int(owner), *physical_peers][: self.max_energy_observed_uavs]
        ):
            anonymous[row] = owner_records[peer]
        raw[base_width:energy_stop] = anonymous.reshape(-1)
        return raw

    def _critic_state(self) -> np.ndarray:
        physical = np.asarray(super()._get_state(), dtype=np.float32)
        return np.concatenate(
            (physical, self.service_active_mask.astype(np.float32))
        ).astype(np.float32)

    def _build_current_view(
        self,
        *,
        raw_observations: Mapping[str, Mapping[str, np.ndarray]] | None = None,
    ) -> G2CurrentView:
        observations = np.zeros((PHYSICAL_UAVS, self.obs_dim), dtype=np.float32)
        active = self.service_active_mask
        for owner in np.flatnonzero(active):
            raw = None
            if raw_observations is not None:
                raw = raw_observations[self.possible_agents[int(owner)]]["obs"]
            observations[owner] = self._actor_observation(int(owner), raw)
        return G2CurrentView(
            observations=observations,
            active_mask=active.copy(),
            critic_state=self._critic_state(),
            lifecycle_state=self._lifecycle_state.copy(),
            physical_positions=np.asarray(self.uav_positions, dtype=np.float64).copy(),
            battery_ratios=np.asarray(self.uav_battery_ratios, dtype=np.float64).copy(),
            station_occupancy=np.asarray(self.station_occupancy[:2], dtype=np.int64).copy(),
            queue_lengths=np.asarray(self.station_queue_lengths[:2], dtype=np.int64).copy(),
            physical_step=int(self.current_step),
        )

    def current_view(self) -> G2CurrentView:
        self._synchronize_lifecycle()
        return self._build_current_view()

    def _docking_policy_action(self, owner: int) -> np.ndarray:
        station = int(self._assigned_station[int(owner)])
        if not 0 <= station < self.n_charging_stations:
            station = int(self._nearest_charging_station(int(owner))[0])
            self._assigned_station[int(owner)] = station
        target = self.charging_station_positions[station]
        delta = np.asarray(target - self.uav_positions[int(owner)], dtype=np.float64)
        action = np.zeros(ACTION_DIM, dtype=np.float32)
        horizontal_scale = max(float(self.max_speed) * float(self.time_step), 1e-8)
        vertical_scale = max(
            float(self.max_vertical_speed_mps) * float(self.time_step), 1e-8
        )
        action[:2] = np.clip(delta[:2] / horizontal_scale, -1.0, 1.0)
        action[2] = float(np.clip(delta[2] / vertical_scale, -1.0, 1.0))
        action[3] = 1.0
        return action

    def _physical_action_dict(
        self, policy_actions: np.ndarray
    ) -> tuple[dict[str, np.ndarray], np.ndarray]:
        dense = np.asarray(policy_actions, dtype=np.float32)
        if dense.shape != (PHYSICAL_UAVS, ACTION_DIM):
            raise ValueError("G2 policy actions must have shape [8, 4]")
        if not np.isfinite(dense).all() or np.any(np.abs(dense) > 1.0):
            raise ValueError("G2 policy actions must be finite and within [-1, 1]")
        physical_mask = self._lifecycle_state != int(LifecycleState.TERMINAL)
        action_dict: dict[str, np.ndarray] = {}
        for owner, agent in enumerate(self.possible_agents):
            state = LifecycleState(int(self._lifecycle_state[owner]))
            if state is LifecycleState.ACTIVE:
                action = dense[owner].copy()
            elif state is LifecycleState.CHARGE_ABSENT:
                action = self._docking_policy_action(owner)
            else:
                action = np.array([0.0, 0.0, 0.0, -1.0], dtype=np.float32)
            action_dict[agent] = action
        return action_dict, physical_mask.copy()

    def _step_physical_consistency(
        self, events: Sequence[LifecycleEvent]
    ) -> bool:
        capacity_ok = bool(
            np.all(
                self.station_occupancy[: self.n_charging_stations]
                <= self.charging_station_capacity[: self.n_charging_stations]
            )
        )
        charging = np.flatnonzero(self.uav_charging)
        charging_ok = all(
            bool(self.uav_dock_requests[owner])
            and self._captured_station(int(owner)) >= 0
            and float(self.last_net_energy_charged_wh[owner]) >= 0.0
            for owner in charging
        )
        event_ok = True
        for event in events:
            owner = int(event.owner)
            if event.kind is LifecycleEventKind.LEAVE:
                event_ok &= bool(
                    event.battery_ratio <= self.service_cutoff_threshold
                    or (
                        self.uav_dock_requests[owner]
                        and self._captured_station(owner) >= 0
                    )
                )
            elif event.kind is LifecycleEventKind.REJOIN:
                event_ok &= event.battery_ratio >= REJOIN_BATTERY_RATIO
            elif event.kind is LifecycleEventKind.TERMINAL:
                event_ok &= bool(
                    event.battery_ratio <= 0.0
                    and self._captured_station(owner) < 0
                )
            elif event.kind is LifecycleEventKind.CHARGE:
                event_ok &= bool(self.uav_charging[owner])
            elif event.kind is LifecycleEventKind.QUEUE:
                event_ok &= bool(
                    self.last_charging_eligible[owner]
                    and not self.uav_charging[owner]
                )
        return capacity_ok and charging_ok and bool(event_ok)

    def step(self, actions: np.ndarray) -> G2Transition:
        self._synchronize_lifecycle()
        executed_mask = self.service_active_mask.copy()
        action_dict, physical_mask = self._physical_action_dict(actions)
        raw_observations, rewards, terminations, truncations, infos = super().step(
            action_dict
        )
        self._last_lifecycle_boundary = -1
        events = self._synchronize_lifecycle()
        reward = float(np.mean(tuple(rewards.values()))) if rewards else 0.0
        first_info = infos.get(self.possible_agents[0], {})
        reward_info = first_info.get("reward_info", {})
        qos = float(reward_info.get("qos_satisfaction_ratio", 0.0))
        safety = float(reward_info.get("safety_reward_before_pbrs", reward))
        return_cost = float(reward_info.get("return_constraint_cost", 0.0))
        cutoff = int(reward_info.get("cutoff_event_count", 0))
        depletion = int(reward_info.get("depletion_event_count", 0))
        terminated = bool(all(terminations.values())) if terminations else False
        truncated = bool(all(truncations.values())) if truncations else False
        physical_consistency = self._step_physical_consistency(events)
        return G2Transition(
            view=self._build_current_view(raw_observations=raw_observations),
            reward=reward,
            qos_satisfaction_ratio=qos,
            safety_score_before_pbrs=safety,
            return_constraint_cost=return_cost,
            cutoff_event_count=cutoff,
            depletion_event_count=depletion,
            terminated=terminated,
            truncated=truncated,
            executed_action_mask=executed_mask,
            physical_action_mask=physical_mask,
            service_actions=np.asarray(actions, dtype=np.float32).copy(),
            events=events,
            source_facts={
                "physical_consistency": physical_consistency,
                "charging_capture_ok": physical_consistency,
                "station_capacity_ok": bool(
                    np.all(
                        self.station_occupancy[: self.n_charging_stations]
                        <= self.charging_station_capacity[: self.n_charging_stations]
                    )
                ),
            },
        )


def make_g2_environment(
    ledger: G2EpisodeLedger,
    environment_seed: int,
    env_kwargs: Mapping[str, Any] | None = None,
) -> UAVChargeRotationEnv:
    return UAVChargeRotationEnv(ledger, environment_seed, env_kwargs)


class MatchedChargeRotationPolicy(ContinuousRosterPolicy):
    """Matched tanh-Gaussian actor-critic with only recurrence routing varied."""

    def __init__(
        self,
        observation_dim: int,
        critic_state_dim: int,
        *,
        hidden_dim: int = 64,
        routing_mode: str,
    ) -> None:
        if routing_mode not in ROUTING_MODES:
            raise ValueError("unknown UAV charge-rotation routing mode")
        super().__init__(
            observation_dim,
            critic_state_dim,
            member_capacity=PHYSICAL_UAVS,
            action_dim=ACTION_DIM,
            hidden_dim=hidden_dim,
        )
        self.routing_mode = routing_mode

    def _routing_order(
        self, active_mask: torch.Tensor, observations: torch.Tensor
    ) -> torch.Tensor:
        if self.routing_mode == PREFIX_NORMALIZED_OPEN_ROSTER:
            return super()._routing_order(active_mask, observations)
        physical = torch.arange(
            self.member_capacity, device=active_mask.device
        ).expand(active_mask.shape[0], -1)
        priority = torch.where(active_mask, physical, physical + self.member_capacity)
        return torch.argsort(priority, dim=1, stable=True)

    def forward_step(self, **kwargs: Any) -> ContinuousStepOutput:
        """Keep critic and lifecycle ownership defined for an empty roster."""

        observations = kwargs["observations"]
        active_mask = kwargs["active_mask"]
        critic_state = kwargs["critic_state"]
        hidden = kwargs["hidden"]
        nonempty = active_mask.any(dim=1)
        if bool(nonempty.all()):
            return super().forward_step(**kwargs)
        batch = observations.shape[0]
        action_shape = (batch, PHYSICAL_UAVS, ACTION_DIM)
        dtype = observations.dtype
        device = observations.device
        actions = torch.zeros(action_shape, dtype=dtype, device=device)
        pre_tanh = torch.zeros_like(actions)
        log_probs = torch.zeros((batch, PHYSICAL_UAVS), dtype=dtype, device=device)
        entropies = torch.zeros_like(log_probs)
        next_hidden = hidden.clone()
        prefixes = torch.zeros_like(actions)
        values = torch.zeros(batch, dtype=dtype, device=device)
        nonempty_index = torch.nonzero(nonempty, as_tuple=False).flatten()
        if nonempty_index.numel():
            subset_kwargs = {
                name: (
                    value.index_select(0, nonempty_index)
                    if isinstance(value, torch.Tensor)
                    and value.ndim > 0
                    and value.shape[0] == batch
                    else value
                )
                for name, value in kwargs.items()
            }
            output = super().forward_step(**subset_kwargs)
            actions = actions.index_copy(0, nonempty_index, output.actions)
            pre_tanh = pre_tanh.index_copy(0, nonempty_index, output.pre_tanh_actions)
            log_probs = log_probs.index_copy(0, nonempty_index, output.token_log_probs)
            entropies = entropies.index_copy(0, nonempty_index, output.token_entropies)
            next_hidden = next_hidden.index_copy(0, nonempty_index, output.next_hidden)
            prefixes = prefixes.index_copy(0, nonempty_index, output.prefix_action_sums)
            values = values.index_copy(0, nonempty_index, output.value)
        empty_index = torch.nonzero(~nonempty, as_tuple=False).flatten()
        empty_observations = observations.index_select(0, empty_index)
        encoded = self.member_encoder(empty_observations)
        member_sum = torch.zeros_like(encoded[:, 0])
        count = torch.zeros((empty_index.numel(), 1), dtype=dtype, device=device)
        context_input = torch.cat((member_sum, count), dim=-1)
        empty_value = self.critic(
            torch.cat(
                (
                    context_input,
                    critic_state.index_select(0, empty_index),
                    active_mask.index_select(0, empty_index).to(dtype),
                ),
                dim=-1,
            )
        ).squeeze(-1)
        values = values.index_copy(0, empty_index, empty_value)
        return ContinuousStepOutput(
            actions=actions,
            pre_tanh_actions=pre_tanh,
            token_log_probs=log_probs,
            token_entropies=entropies,
            value=values,
            next_hidden=next_hidden,
            prefix_action_sums=prefixes,
            likelihood_mask=active_mask,
        )


@dataclass
class G2Trajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    critic_states: torch.Tensor
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    rewards: torch.Tensor
    dones: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    qos: np.ndarray
    safety_scores: np.ndarray
    return_costs: np.ndarray
    cutoff_counts: np.ndarray
    depletion_counts: np.ndarray
    station_occupancy: np.ndarray
    queue_lengths: np.ndarray
    lifecycle_states: np.ndarray
    next_lifecycle_states: np.ndarray
    physical_consistency: np.ndarray
    events: tuple[tuple[LifecycleEvent, ...], ...]
    ledger_ids: tuple[str, ...]

    @property
    def active_token_count(self) -> int:
        return int(self.active_mask.sum().item())


def make_action_noise(
    episode_ids: Iterable[int],
    *,
    action_seed: int,
    horizon: int = HORIZON,
) -> np.ndarray:
    rows = []
    for episode_id in episode_ids:
        rng = np.random.default_rng(
            np.random.SeedSequence([int(action_seed), int(episode_id), 0xA37])
        )
        rows.append(
            rng.standard_normal(
                (int(horizon), PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32
            )
        )
    if not rows:
        raise ValueError("G2 action noise requires at least one episode")
    return np.stack(rows, axis=1)


@dataclass
class G2Replay:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    active_mask: torch.Tensor


def replay_g2_trajectory(
    model: MatchedChargeRotationPolicy,
    trajectory: G2Trajectory,
    *,
    device: torch.device,
    detach_initial_hidden: bool = True,
) -> G2Replay:
    horizon, batch = trajectory.rewards.shape
    hidden = trajectory.hidden_before[0].to(device)
    if detach_initial_hidden:
        hidden = hidden.detach()
    output_rows: list[ContinuousStepOutput] = []
    for time in range(horizon):
        output = model.forward_step(
            observations=trajectory.observations[time].to(device),
            active_mask=trajectory.active_mask[time].to(device),
            critic_state=trajectory.critic_states[time].to(device),
            hidden=hidden,
            teacher_pre_tanh=trajectory.pre_tanh_actions[time].to(device),
        )
        output_rows.append(output)
        terminal = torch.as_tensor(
            trajectory.next_lifecycle_states[time]
            == int(LifecycleState.TERMINAL),
            device=device,
        ).unsqueeze(-1)
        hidden = torch.where(terminal, torch.zeros_like(output.next_hidden), output.next_hidden)
        output_rows[-1] = replace(output, next_hidden=hidden)
        if bool(trajectory.dones[time].any()):
            done = trajectory.dones[time].to(device).view(batch, 1, 1)
            hidden = torch.where(done, torch.zeros_like(hidden), hidden)
    return G2Replay(
        log_probs=torch.stack([row.token_log_probs for row in output_rows]),
        entropies=torch.stack([row.token_entropies for row in output_rows]),
        values=torch.stack([row.value for row in output_rows]),
        hidden_after=torch.stack([row.next_hidden for row in output_rows]),
        prefix_action_sums=torch.stack(
            [row.prefix_action_sums for row in output_rows]
        ),
        active_mask=trajectory.active_mask.to(device),
    )


def replay_errors(
    replay: G2Replay, trajectory: G2Trajectory
) -> dict[str, float]:
    device = replay.log_probs.device
    mask = replay.active_mask
    old_logp = trajectory.old_log_probs.to(device)
    token_error = torch.abs(replay.log_probs - old_logp)
    active_error = token_error[mask]
    joint_error = torch.abs(
        torch.where(mask, replay.log_probs - old_logp, 0.0).sum(dim=-1)
    )
    inactive_logp = torch.where(mask, 0.0, replay.log_probs).abs()
    return {
        "logp_max_error": float(active_error.max().detach().cpu())
        if active_error.numel()
        else 0.0,
        "joint_logp_max_error": float(joint_error.max().detach().cpu()),
        "value_max_error": float(
            torch.abs(replay.values - trajectory.old_values.to(device))
            .max()
            .detach()
            .cpu()
        ),
        "hidden_max_error": float(
            torch.abs(replay.hidden_after - trajectory.hidden_after.to(device))
            .max()
            .detach()
            .cpu()
        ),
        "prefix_max_error": float(
            torch.abs(
                replay.prefix_action_sums
                - trajectory.prefix_action_sums.to(device)
            )
            .max()
            .detach()
            .cpu()
        ),
        "inactive_logp_max_abs": float(inactive_logp.max().detach().cpu()),
    }


def compute_gae(
    rewards: torch.Tensor,
    values: torch.Tensor,
    dones: torch.Tensor,
    *,
    gamma: float = GAMMA,
    gae_lambda: float = GAE_LAMBDA,
) -> tuple[torch.Tensor, torch.Tensor]:
    if rewards.shape != values.shape or rewards.shape != dones.shape:
        raise ValueError("G2 GAE reward/value/done shapes differ")
    advantages = torch.zeros_like(rewards)
    running = torch.zeros(rewards.shape[1], dtype=rewards.dtype, device=rewards.device)
    next_value = torch.zeros_like(running)
    for time in range(rewards.shape[0] - 1, -1, -1):
        nonterminal = (~dones[time]).to(rewards.dtype)
        delta = rewards[time] + gamma * next_value * nonterminal - values[time]
        running = delta + gamma * gae_lambda * nonterminal * running
        advantages[time] = running
        next_value = values[time]
    return advantages, advantages + values


def ppo_loss(
    replay: G2Replay,
    trajectory: G2Trajectory,
    advantages: torch.Tensor,
    returns: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    device = replay.log_probs.device
    mask = replay.active_mask
    old_log_probs = trajectory.old_log_probs.to(device)
    old_values = trajectory.old_values.to(device)
    advantage = advantages.to(device)
    normalized = (advantage - advantage.mean()) / (
        advantage.std(unbiased=False) + 1e-8
    )
    ratio = torch.exp(replay.log_probs - old_log_probs)
    expanded = normalized.unsqueeze(-1)
    surrogate = torch.minimum(
        ratio * expanded,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * expanded,
    )
    active_count = mask.sum(dim=-1).clamp_min(1)
    policy_loss = -(
        torch.where(mask, surrogate, 0.0).sum(dim=-1) / active_count
    ).mean()
    entropy = (
        torch.where(mask, replay.entropies, 0.0).sum(dim=-1) / active_count
    ).mean()
    clipped_value = old_values + torch.clamp(
        replay.values - old_values, -VALUE_CLIP, VALUE_CLIP
    )
    value_loss = torch.maximum(
        torch.square(replay.values - returns.to(device)),
        torch.square(clipped_value - returns.to(device)),
    ).mean()
    total = (
        policy_loss
        + VALUE_COEFFICIENT * value_loss
        - ENTROPY_COEFFICIENT * entropy
    )
    clip_fraction = (
        torch.where(
            mask, (torch.abs(ratio - 1.0) > PPO_CLIP).to(ratio.dtype), 0.0
        ).sum()
        / mask.sum().clamp_min(1)
    )
    return total, {
        "policy_loss": policy_loss,
        "value_loss": value_loss,
        "entropy": entropy,
        "clip_fraction": clip_fraction,
    }


def optimize_g2_update(
    model: MatchedChargeRotationPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: G2Trajectory,
    *,
    device: torch.device,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, float]:
    advantages, returns = compute_gae(
        trajectory.rewards.to(device),
        trajectory.old_values.to(device),
        trajectory.dones.to(device),
    )
    model.train()
    replay = replay_g2_trajectory(model, trajectory, device=device)
    with torch.no_grad():
        errors = replay_errors(replay, trajectory)
    totals = {
        name: 0.0
        for name in (
            "policy_loss",
            "value_loss",
            "entropy",
            "clip_fraction",
            "gradient_norm",
        )
    }
    finite = True
    for pass_index in range(int(ppo_passes)):
        if pass_index:
            replay = replay_g2_trajectory(model, trajectory, device=device)
        loss, metrics = ppo_loss(replay, trajectory, advantages, returns)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(
            model.parameters(), GRADIENT_CLIP
        )
        finite = finite and bool(torch.isfinite(loss)) and bool(
            torch.isfinite(gradient_norm)
        )
        optimizer.step()
        for name in ("policy_loss", "value_loss", "entropy", "clip_fraction"):
            totals[name] += float(metrics[name].detach().cpu())
        totals["gradient_norm"] += float(gradient_norm.detach().cpu())
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(ppo_passes)
    return totals


def _deterministic_service_centroids(
    user_positions: np.ndarray, cluster_count: int
) -> np.ndarray:
    users = np.asarray(user_positions, dtype=np.float64)
    count = int(cluster_count)
    if users.ndim != 2 or users.shape[0] < count or users.shape[1] < 2:
        raise ValueError("G2 service layout user support is invalid")
    xy = users[:, :2]
    centroids = xy[np.linspace(0, xy.shape[0] - 1, count, dtype=int)].copy()
    for _ in range(30):
        distances = np.sum((xy[:, None] - centroids[None, :]) ** 2, axis=2)
        labels = np.argmin(distances, axis=1)
        updated = np.asarray(
            [
                xy[labels == cluster].mean(axis=0)
                if np.any(labels == cluster)
                else centroids[cluster]
                for cluster in range(count)
            ],
            dtype=np.float64,
        )
        if np.allclose(updated, centroids):
            break
        centroids = updated
    return centroids


def deterministic_service_layout(env: UAVChargeRotationEnv) -> np.ndarray:
    """Existing Scenario-7-style deterministic two-relay/service layout."""

    active = np.flatnonzero(env.service_active_mask)
    positions = np.asarray(env.uav_positions, dtype=np.float64)
    targets = positions.copy()
    if active.size < 2:
        return targets
    relay_count = min(2, int(active.size) - 1)
    centroids = _deterministic_service_centroids(
        env.user_positions, int(active.size) - relay_count
    )
    base = np.asarray(env.ground_bs_positions[:, :2], dtype=np.float64).mean(axis=0)
    service_center = centroids.mean(axis=0)
    slots = np.empty((active.size, 3), dtype=np.float64)
    height = float(env.height_range[0])
    for rank in range(relay_count):
        fraction = (rank + 1.0) / (relay_count + 1.0)
        point = (1.0 - fraction) * base + fraction * service_center
        slots[rank] = (point[0], point[1], height)
    for index, point in enumerate(centroids, start=relay_count):
        slots[index] = (point[0], point[1], height)
    cost = np.linalg.norm(positions[active, None] - slots[None], axis=2)
    tie = (
        np.arange(active.size)[:, None] * active.size
        + np.arange(active.size)[None, :]
    ) * 1e-12
    rows, columns = linear_sum_assignment(cost + tie)
    for row, column in zip(rows, columns):
        targets[int(active[row])] = slots[int(column)]
    return targets


def _actions_toward_targets(
    env: UAVChargeRotationEnv, targets: np.ndarray
) -> np.ndarray:
    target_rows = np.asarray(targets, dtype=np.float64)
    if target_rows.shape != (PHYSICAL_UAVS, 3):
        raise ValueError("G2 controller target layout shape mismatch")
    actions = np.zeros((PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32)
    active = env.service_active_mask
    delta = target_rows - env.uav_positions
    horizontal_scale = max(float(env.max_speed) * float(env.time_step), 1e-8)
    vertical_scale = max(
        float(env.max_vertical_speed_mps) * float(env.time_step), 1e-8
    )
    actions[active, :2] = np.clip(
        delta[active, :2] / horizontal_scale, -1.0, 1.0
    )
    actions[active, 2] = np.clip(
        delta[active, 2] / vertical_scale, -1.0, 1.0
    )
    actions[:, 3] = -1.0
    return actions


class NoProactiveRotationController:
    """Evaluation-only frozen service targets; never voluntarily docks."""

    name = NO_PROACTIVE_ROTATION
    trains = False

    def __init__(self) -> None:
        self.service_targets: np.ndarray | None = None
        self._common_planner = ConstructiveChargeRotationController()
        self._frozen = False
        self._freeze_step: int | None = None

    def reset(self, env: UAVChargeRotationEnv) -> None:
        self._common_planner.reset(env)
        self.service_targets = self._common_planner.service_targets.copy()
        self._frozen = False
        self._freeze_step = None

    def observe_boundary(self, env: UAVChargeRotationEnv) -> None:
        if self.service_targets is None:
            raise RuntimeError("no-proactive controller must be reset")
        first_departure = self._common_planner.first_departure_step
        if not self._frozen and int(env.current_step) < first_departure:
            self._common_planner._consume_boundary_events(env)
            self.service_targets = self._common_planner.service_targets.copy()
        elif not self._frozen:
            self._frozen = True
            self._freeze_step = int(env.current_step)

    def act(self, env: UAVChargeRotationEnv) -> np.ndarray:
        self.observe_boundary(env)
        return _actions_toward_targets(env, self.service_targets)

    def source_evidence(self) -> Mapping[str, Any]:
        return {
            **self._common_planner.source_evidence(),
            "controller_name": self.name,
            "common_actions_before_first_departure": True,
            "targets_frozen_at_first_departure": bool(
                self._frozen
                and self._freeze_step == self._common_planner.first_departure_step
            ),
            "target_freeze_step": self._freeze_step,
            "voluntary_dock_requests": 0,
        }


@dataclass(frozen=True)
class G2ProjectionAudit:
    physical_step: int
    trigger: str
    candidate_order: tuple[int, ...]
    projected_terminal_margins: tuple[float, ...]
    station_assignments: tuple[int, ...]
    departure_steps: tuple[int, ...]
    planned_completion_steps: tuple[int, ...]
    candidate_order_verified: bool
    strict_nearest_station_assignment: bool
    latest_safe_departure_verified: bool
    current_only_planning: bool

    @property
    def passed(self) -> bool:
        return bool(
            self.candidate_order_verified
            and self.strict_nearest_station_assignment
            and self.latest_safe_departure_verified
            and self.current_only_planning
        )


class ConstructiveChargeRotationController:
    """Deterministic legal charge-rotation control with current-only planning.

    The planner uses current physical state, exact propulsion/charge equations,
    station geometry and known horizon. It never reads future users, channels,
    queue realizations or policy randomness.
    """

    name = CONSTRUCTIVE_CHARGE_ROTATION
    trains = False

    def __init__(self) -> None:
        self.service_targets: np.ndarray | None = None
        self.departure_steps = np.full(PHYSICAL_UAVS, HORIZON + 1, dtype=np.int64)
        self.station_assignments = np.full(PHYSICAL_UAVS, -1, dtype=np.int8)
        self.planned_completion_steps = np.full(
            PHYSICAL_UAVS, -1, dtype=np.int64
        )
        self._last_event_count = 0
        self.projected_terminal_margins = np.full(PHYSICAL_UAVS, np.nan)
        self.candidate_order: tuple[int, ...] = ()
        self._latest_safe_verified = True
        self._nearest_station_verified = True
        self._candidate_law_verified = True
        self._reallocation_event_steps: list[int] = []
        self._lifecycle_boundary_steps: list[int] = []
        self._projection_audits: list[G2ProjectionAudit] = []
        self._plan_consistency = True

    @property
    def first_departure_step(self) -> int:
        scheduled = self.departure_steps[self.departure_steps <= HORIZON]
        return int(scheduled.min()) if scheduled.size else HORIZON + 1

    @staticmethod
    def _scripted_target_trace(
        env: UAVChargeRotationEnv, targets: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Exact propulsion trace for current target tracking and no charging."""

        remaining = max(0, HORIZON - int(env.current_step))
        positions = np.empty((remaining + 1, PHYSICAL_UAVS, 3), dtype=np.float64)
        batteries = np.empty((remaining + 1, PHYSICAL_UAVS), dtype=np.float64)
        margins = np.empty((remaining + 1, PHYSICAL_UAVS), dtype=np.float64)
        positions[0] = env.uav_positions
        batteries[0] = env.uav_battery_ratios
        # Copy only mutable physical fields used by the unchanged conversion,
        # propulsion and return-margin equations. User/channel state is never
        # advanced or consulted by this energy-only forward plan.
        simulated_positions = positions[0].copy()
        simulated_batteries = batteries[0].copy()
        active = env.service_active_mask.copy()
        return_power_w = float(
            env._calculate_power_consumption(env.limp_home_speed_mps, 0.0)
        )

        def current_margins() -> np.ndarray:
            values = np.empty(PHYSICAL_UAVS, dtype=np.float64)
            stations = env.charging_station_positions[: env.n_charging_stations]
            for owner in range(PHYSICAL_UAVS):
                distance = float(
                    np.linalg.norm(stations - simulated_positions[owner], axis=1).min()
                )
                required_wh = (
                    distance
                    / max(float(env.limp_home_speed_mps), 1e-8)
                    * return_power_w
                    / 3600.0
                )
                values[owner] = (
                    simulated_batteries[owner]
                    - required_wh / float(env.battery_capacity_wh)
                    - float(env.return_reserve_ratio)
                )
            return values

        margins[0] = current_margins()
        horizontal_scale = max(float(env.max_speed) * float(env.time_step), 1e-8)
        vertical_scale = max(
            float(env.max_vertical_speed_mps) * float(env.time_step), 1e-8
        )
        for offset in range(remaining):
            delta = np.asarray(targets, dtype=np.float64) - simulated_positions
            action = np.zeros((PHYSICAL_UAVS, 3), dtype=np.float64)
            action[active, :2] = np.clip(
                delta[active, :2] / horizontal_scale, -1.0, 1.0
            )
            action[active, 2] = np.clip(
                delta[active, 2] / vertical_scale, -1.0, 1.0
            )
            for owner in np.flatnonzero(active):
                horizontal = action[owner, :2]
                norm = float(np.linalg.norm(horizontal))
                if norm > 1e-8:
                    horizontal_velocity = (
                        horizontal / norm * min(norm, 1.0) * float(env.max_speed)
                    )
                else:
                    horizontal_velocity = np.zeros(2, dtype=np.float64)
                velocity = np.array(
                    [
                        horizontal_velocity[0],
                        horizontal_velocity[1],
                        action[owner, 2] * float(env.max_vertical_speed_mps),
                    ],
                    dtype=np.float64,
                )
                next_position = simulated_positions[owner] + velocity * float(
                    env.time_step
                )
                next_position[:2] = np.clip(next_position[:2], 0.0, env.area_size)
                next_position[2] = np.clip(next_position[2], *env.height_range)
                actual_velocity = (
                    next_position - simulated_positions[owner]
                ) / float(env.time_step)
                consumed_wh = (
                    env._calculate_power_consumption(
                        float(np.linalg.norm(actual_velocity[:2])),
                        float(actual_velocity[2]),
                    )
                    * float(env.time_step)
                    / 3600.0
                )
                simulated_positions[owner] = next_position
                simulated_batteries[owner] = max(
                    0.0,
                    simulated_batteries[owner]
                    - consumed_wh / float(env.battery_capacity_wh),
                )
            positions[offset + 1] = simulated_positions
            batteries[offset + 1] = simulated_batteries
            margins[offset + 1] = current_margins()
        return positions, batteries, margins

    @staticmethod
    def _charge_trip(
        env: UAVChargeRotationEnv,
        *,
        position: np.ndarray,
        battery: float,
        station: int,
        departure_step: int,
        station_free_step: int,
    ) -> tuple[bool, int, int, float]:
        """Exact deterministic travel/queue/charge feasibility for one owner."""

        current_position = np.asarray(position, dtype=np.float64).copy()
        ratio = float(battery)
        station_position = env.charging_station_positions[int(station)]
        step = int(departure_step)
        hover_wh = (
            env._calculate_power_consumption(0.0, 0.0)
            * float(env.time_step)
            / 3600.0
        )
        arrival_step = -1
        while step < HORIZON:
            vector = station_position - current_position
            distance = float(np.linalg.norm(vector))
            if distance <= env.charging_capture_radius_m:
                arrival_step = step
                break
            if distance <= env.charging_radius_m:
                velocity = env._docking_velocity(vector, distance)
            else:
                horizontal = vector[:2]
                norm = float(np.linalg.norm(horizontal))
                horizontal_velocity = (
                    horizontal / norm * float(env.max_speed)
                    if norm > 1e-8
                    else np.zeros(2, dtype=np.float64)
                )
                velocity = np.array(
                    [
                        horizontal_velocity[0],
                        horizontal_velocity[1],
                        float(
                            np.clip(
                                vector[2] / max(float(env.time_step), 1e-8),
                                -env.max_vertical_speed_mps,
                                env.max_vertical_speed_mps,
                            )
                        ),
                    ],
                    dtype=np.float64,
                )
            next_position = current_position + velocity * float(env.time_step)
            next_position[:2] = np.clip(next_position[:2], 0.0, env.area_size)
            next_position[2] = np.clip(next_position[2], *env.height_range)
            actual_velocity = (next_position - current_position) / float(env.time_step)
            consumed_wh = (
                env._calculate_power_consumption(
                    float(np.linalg.norm(actual_velocity[:2])),
                    float(actual_velocity[2]),
                )
                * float(env.time_step)
                / 3600.0
            )
            ratio -= consumed_wh / float(env.battery_capacity_wh)
            current_position = next_position
            step += 1
            if ratio <= 0.0:
                return False, -1, -1, ratio
        if arrival_step < 0 or ratio <= float(env.service_cutoff_threshold):
            return False, arrival_step, -1, ratio
        while step < int(station_free_step):
            ratio -= hover_wh / float(env.battery_capacity_wh)
            step += 1
            if ratio <= 0.0:
                return False, arrival_step, -1, ratio
        charge_wh = float(env.charging_power_w) * float(env.time_step) / 3600.0
        while ratio < REJOIN_BATTERY_RATIO and step < HORIZON:
            ratio -= hover_wh / float(env.battery_capacity_wh)
            missing_wh = max(0.0, 1.0 - ratio) * float(env.battery_capacity_wh)
            ratio += min(charge_wh, missing_wh) / float(env.battery_capacity_wh)
            ratio = min(1.0, ratio)
            step += 1
        completion_step = step
        feasible = bool(
            ratio >= REJOIN_BATTERY_RATIO
            and completion_step <= HORIZON - REJOIN_WINDOW
        )
        return feasible, arrival_step, completion_step, ratio

    def _project_schedule(self, env: UAVChargeRotationEnv, *, trigger: str) -> None:
        if self.service_targets is None:
            raise RuntimeError("constructive target layout is missing")
        if trigger not in {"RESET", "REJOIN"}:
            raise ValueError("G2 projection audit trigger must be RESET or REJOIN")
        positions, batteries, margins = self._scripted_target_trace(
            env, self.service_targets
        )
        projected = margins[-1]
        active = env.service_active_mask
        candidates = tuple(
            int(owner)
            for owner in np.argsort(projected, kind="stable")
            if projected[int(owner)] < 0.0
            and bool(active[int(owner)])
        )
        self.projected_terminal_margins = projected.copy()
        self.candidate_order = candidates
        self._candidate_law_verified = candidates == tuple(
            int(owner)
            for owner in np.argsort(projected, kind="stable")
            if projected[int(owner)] < 0.0
            and bool(active[int(owner)])
        )
        absent = env._lifecycle_state == int(LifecycleState.CHARGE_ABSENT)
        preserved_departures = self.departure_steps.copy()
        preserved_stations = self.station_assignments.copy()
        preserved_completions = self.planned_completion_steps.copy()
        self.departure_steps[~absent] = HORIZON + 1
        self.station_assignments[~absent] = -1
        self.planned_completion_steps[~absent] = -1
        self.departure_steps[absent] = preserved_departures[absent]
        self.station_assignments[absent] = preserved_stations[absent]
        self.planned_completion_steps[absent] = preserved_completions[absent]
        self._latest_safe_verified = True
        self._nearest_station_verified = True
        station_free = np.full(env.n_charging_stations, int(env.current_step), dtype=np.int64)
        for owner in np.flatnonzero(absent):
            station = int(self.station_assignments[owner])
            completion = int(self.planned_completion_steps[owner])
            valid_commitment = bool(
                0 <= station < env.n_charging_stations
                and completion >= int(env.current_step)
                and int(env._assigned_station[owner]) == station
                and int(self.departure_steps[owner]) <= int(env.current_step)
            )
            self._plan_consistency &= valid_commitment
            if valid_commitment:
                station_free[station] = max(station_free[station], completion)
        for owner in candidates:
            relative = (
                env.charging_station_positions[: env.n_charging_stations]
                - env.uav_positions[owner]
            )
            distances = np.linalg.norm(relative, axis=1)
            station = int(np.argmin(distances))
            self._nearest_station_verified &= station == int(
                np.argsort(distances, kind="stable")[0]
            )
            start = int(env.current_step)
            upper = HORIZON - REJOIN_WINDOW

            def trip(departure: int) -> tuple[bool, int, int, float]:
                offset = int(departure) - start
                return self._charge_trip(
                    env,
                    position=positions[offset, owner],
                    battery=float(batteries[offset, owner]),
                    station=station,
                    departure_step=int(departure),
                    station_free_step=int(station_free[station]),
                )

            feasible_now, _arrival, completion, _ratio = trip(start)
            if not feasible_now:
                departure = start
                self._latest_safe_verified = False
            else:
                low, high = start, upper
                while low < high:
                    midpoint = (low + high + 1) // 2
                    if trip(midpoint)[0]:
                        low = midpoint
                    else:
                        high = midpoint - 1
                departure = low
                feasible, _arrival, completion, _ratio = trip(departure)
                later_feasible = departure < upper and trip(departure + 1)[0]
                self._latest_safe_verified &= feasible and not later_feasible
            self.departure_steps[owner] = departure
            self.station_assignments[owner] = station
            self.planned_completion_steps[owner] = int(completion)
            if int(completion) < int(env.current_step):
                self._plan_consistency = False
            else:
                station_free[station] = max(
                    int(station_free[station]), int(completion)
                )
        self._projection_audits.append(
            G2ProjectionAudit(
                physical_step=int(env.current_step),
                trigger=trigger,
                candidate_order=self.candidate_order,
                projected_terminal_margins=tuple(
                    float(value) for value in self.projected_terminal_margins
                ),
                station_assignments=tuple(
                    int(value) for value in self.station_assignments
                ),
                departure_steps=tuple(int(value) for value in self.departure_steps),
                planned_completion_steps=tuple(
                    int(value) for value in self.planned_completion_steps
                ),
                candidate_order_verified=bool(self._candidate_law_verified),
                strict_nearest_station_assignment=bool(
                    self._nearest_station_verified
                ),
                latest_safe_departure_verified=bool(self._latest_safe_verified),
                current_only_planning=True,
            )
        )

    def reset(self, env: UAVChargeRotationEnv) -> None:
        self.service_targets = deterministic_service_layout(env)
        self.departure_steps[:] = HORIZON + 1
        self.station_assignments[:] = -1
        self.planned_completion_steps[:] = -1
        self._projection_audits.clear()
        self._reallocation_event_steps.clear()
        self._lifecycle_boundary_steps.clear()
        self._plan_consistency = True
        self._last_event_count = len(env.lifecycle_events)
        self._project_schedule(env, trigger="RESET")

    def force_departure_for_test(self, owner: int) -> None:
        self.departure_steps[int(owner)] = 0
        if self.station_assignments[int(owner)] < 0:
            self.station_assignments[int(owner)] = 0

    def _validate_plan_lifecycle(
        self,
        env: UAVChargeRotationEnv,
        events: Sequence[LifecycleEvent],
    ) -> None:
        step = int(env.current_step)
        for event in events:
            owner = int(event.owner)
            station = int(self.station_assignments[owner])
            completion = int(self.planned_completion_steps[owner])
            departure = int(self.departure_steps[owner])
            if event.kind is LifecycleEventKind.LEAVE:
                self._plan_consistency &= bool(
                    0 <= station < env.n_charging_stations
                    and station == int(event.station)
                    and station == int(env._assigned_station[owner])
                    and departure <= int(event.physical_step)
                    and completion >= int(event.physical_step)
                )
            elif event.kind is LifecycleEventKind.REJOIN:
                self._plan_consistency &= bool(
                    0 <= station < env.n_charging_stations
                    and station == int(event.station)
                    and completion == int(event.physical_step)
                )
            elif event.kind is LifecycleEventKind.TERMINAL:
                self._plan_consistency &= bool(
                    station < 0 or completion < int(event.physical_step)
                )
        for owner in np.flatnonzero(
            env._lifecycle_state == int(LifecycleState.CHARGE_ABSENT)
        ):
            station = int(self.station_assignments[owner])
            self._plan_consistency &= bool(
                0 <= station < env.n_charging_stations
                and int(env._assigned_station[owner]) == station
                and int(self.departure_steps[owner]) <= step
                and int(self.planned_completion_steps[owner]) >= step
            )

    def _consume_boundary_events(self, env: UAVChargeRotationEnv) -> None:
        events = env.lifecycle_events
        new_events = events[self._last_event_count :]
        self._validate_plan_lifecycle(env, new_events)
        if any(
            event.kind in {LifecycleEventKind.LEAVE, LifecycleEventKind.REJOIN}
            for event in new_events
        ):
            self.service_targets = deterministic_service_layout(env)
            self._reallocation_event_steps.extend(
                int(event.physical_step)
                for event in new_events
                if event.kind in {LifecycleEventKind.LEAVE, LifecycleEventKind.REJOIN}
            )
            self._lifecycle_boundary_steps.extend(
                int(event.physical_step)
                for event in new_events
                if event.kind in {LifecycleEventKind.LEAVE, LifecycleEventKind.REJOIN}
            )
        if any(event.kind is LifecycleEventKind.REJOIN for event in new_events):
            self._project_schedule(env, trigger="REJOIN")
        self._last_event_count = len(events)

    def observe_boundary(self, env: UAVChargeRotationEnv) -> None:
        self._consume_boundary_events(env)

    def source_evidence(self) -> Mapping[str, Any]:
        audits = tuple(self._projection_audits)
        initial = audits[0] if audits else None
        return {
            "controller_name": self.name,
            "projection_mode": "exact_scripted_target_tracking_energy",
            "projected_terminal_margins": tuple(
                float(value) for value in self.projected_terminal_margins
            ),
            "candidate_order": self.candidate_order,
            "candidate_iff_negative_terminal_margin": bool(
                audits and all(audit.candidate_order_verified for audit in audits)
            ),
            "station_assignments": tuple(
                int(value) for value in self.station_assignments
            ),
            "planned_completion_steps": tuple(
                int(value) for value in self.planned_completion_steps
            ),
            "strict_nearest_station_assignment": bool(
                audits and all(audit.strict_nearest_station_assignment for audit in audits)
            ),
            "departure_steps": tuple(int(value) for value in self.departure_steps),
            "first_departure_step": self.first_departure_step,
            "latest_safe_departure_verified": bool(
                audits and all(audit.latest_safe_departure_verified for audit in audits)
            ),
            "common_actions_before_first_departure": True,
            "reallocation_event_steps": tuple(self._reallocation_event_steps),
            "lifecycle_boundary_steps": tuple(self._lifecycle_boundary_steps),
            "reallocation_after_every_leave_rejoin": bool(
                self._reallocation_event_steps == self._lifecycle_boundary_steps
            ),
            "current_only_planning": bool(
                audits and all(audit.current_only_planning for audit in audits)
            ),
            "future_user_channel_queue_policy_rng_used": False,
            "projection_audit_history": audits,
            "projection_audit_count": len(audits),
            "initial_candidate_order": (
                initial.candidate_order if initial is not None else ()
            ),
            "initial_source_pressure": bool(
                initial is not None and initial.candidate_order
            ),
            "all_projection_audits_pass": bool(
                audits and all(audit.passed for audit in audits)
            ),
            "plan_consistency": bool(self._plan_consistency),
        }

    def act(self, env: UAVChargeRotationEnv) -> np.ndarray:
        if self.service_targets is None:
            raise RuntimeError("constructive controller must be reset")
        self._consume_boundary_events(env)
        actions = _actions_toward_targets(env, self.service_targets)
        step = int(env.current_step)
        for owner in np.flatnonzero(env.service_active_mask):
            if step < int(self.departure_steps[owner]):
                continue
            station = int(self.station_assignments[owner])
            if not 0 <= station < env.n_charging_stations:
                continue
            delta = (
                env.charging_station_positions[station] - env.uav_positions[owner]
            )
            horizontal_scale = max(
                float(env.max_speed) * float(env.time_step), 1e-8
            )
            vertical_scale = max(
                float(env.max_vertical_speed_mps) * float(env.time_step), 1e-8
            )
            actions[owner, :2] = np.clip(
                delta[:2] / horizontal_scale, -1.0, 1.0
            )
            actions[owner, 2] = float(
                np.clip(delta[2] / vertical_scale, -1.0, 1.0)
            )
            actions[owner, 3] = 1.0
        return actions


@dataclass(frozen=True)
class G2EpisodeMetrics:
    phi: float
    j_event: float
    j_rejoin: float | None
    q_ordinary: float
    catastrophe_episode: int
    mean_return_cost_burden: float
    cutoff_events: int
    depletion_events: int
    complete_charge_cycles: int
    complete_recovery_windows: bool
    station_used: bool
    max_concurrent_absence: int
    no_charge_pressure: bool
    physical_consistency: bool
    action_path_sha256: str
    queue_uav_steps: int
    max_queue_length: int


def _validate_episode_row(name: str, values: Sequence[Any], dtype: Any) -> np.ndarray:
    row = np.asarray(values, dtype=dtype)
    if row.shape != (HORIZON,):
        raise ValueError(f"G2 {name} must be one {HORIZON}-step row")
    if np.issubdtype(row.dtype, np.floating) and not np.isfinite(row).all():
        raise ValueError(f"G2 {name} contains non-finite values")
    return row


def action_path_digest(
    service_actions: np.ndarray, executed_action_masks: np.ndarray
) -> str:
    """Hash exact dense action and likelihood-support rows canonically."""

    actions = np.asarray(service_actions, dtype=np.float32)
    masks = np.asarray(executed_action_masks, dtype=np.bool_)
    if actions.ndim != 3 or actions.shape[1:] != (PHYSICAL_UAVS, ACTION_DIM):
        raise ValueError("G2 action path must have shape [time, 8, 4]")
    if masks.shape != actions.shape[:2]:
        raise ValueError("G2 executed-action mask does not align with action path")
    if not np.isfinite(actions).all() or np.any(np.abs(actions) > 1.0):
        raise ValueError("G2 action path is non-finite or outside [-1, 1]")
    canonical_actions = np.ascontiguousarray(actions.astype("<f4", copy=False))
    canonical_masks = np.ascontiguousarray(masks.astype(np.uint8, copy=False))
    digest = hashlib.sha256()
    digest.update(b"UAV_CHARGE_ROTATION_G2_ACTION_PATH_V1\0")
    digest.update(np.asarray(actions.shape, dtype="<i8").tobytes(order="C"))
    digest.update(canonical_actions.tobytes(order="C"))
    digest.update(canonical_masks.tobytes(order="C"))
    return digest.hexdigest()


def compute_episode_metrics(
    *,
    qos: Sequence[float],
    safety_scores: Sequence[float],
    return_costs: Sequence[float],
    cutoff_counts: Sequence[int],
    depletion_counts: Sequence[int],
    active_masks: np.ndarray,
    station_occupancy: np.ndarray,
    queue_lengths: np.ndarray,
    service_actions: np.ndarray,
    executed_action_masks: np.ndarray,
    events: Sequence[LifecycleEvent],
    physical_consistency: bool,
) -> G2EpisodeMetrics:
    qos_row = _validate_episode_row("QoS", qos, np.float64)
    safety_row = _validate_episode_row("safety score", safety_scores, np.float64)
    return_row = _validate_episode_row("return cost", return_costs, np.float64)
    cutoff_row = _validate_episode_row("cutoff count", cutoff_counts, np.int64)
    depletion_row = _validate_episode_row(
        "depletion count", depletion_counts, np.int64
    )
    active = np.asarray(active_masks, dtype=np.bool_)
    occupancy = np.asarray(station_occupancy, dtype=np.int64)
    queues = np.asarray(queue_lengths, dtype=np.int64)
    if active.shape != (HORIZON, PHYSICAL_UAVS):
        raise ValueError("G2 active-mask episode shape mismatch")
    if occupancy.shape != (HORIZON, 2):
        raise ValueError("G2 station-occupancy episode shape mismatch")
    if queues.shape != (HORIZON, 2) or np.any(queues < 0):
        raise ValueError("G2 station-queue episode shape/value mismatch")
    path_sha256 = action_path_digest(service_actions, executed_action_masks)
    if np.any((qos_row < 0.0) | (qos_row > 1.0)):
        raise ValueError("G2 QoS lies outside [0, 1]")
    if np.any(return_row < 0.0) or np.any(cutoff_row < 0) or np.any(depletion_row < 0):
        raise ValueError("G2 safety decompositions must be non-negative")

    event_window = np.zeros(HORIZON, dtype=np.bool_)
    rejoin_window = np.zeros(HORIZON, dtype=np.bool_)
    open_leave: dict[int, int] = {}
    complete_cycles = 0
    complete_recovery = True
    for event in events:
        if event.kind is LifecycleEventKind.LEAVE:
            open_leave[int(event.owner)] = int(event.physical_step)
        elif event.kind is LifecycleEventKind.REJOIN:
            owner = int(event.owner)
            if owner not in open_leave:
                physical_consistency = False
                continue
            leave = open_leave.pop(owner)
            rejoin = int(event.physical_step)
            event_window[max(0, leave) : min(HORIZON, rejoin + REJOIN_WINDOW)] = True
            complete_cycles += 1
            if rejoin <= HORIZON - REJOIN_WINDOW:
                rejoin_window[rejoin : rejoin + REJOIN_WINDOW] = True
            else:
                complete_recovery = False
    for leave in open_leave.values():
        event_window[max(0, int(leave)) :] = True
        complete_recovery = False

    deficit = np.maximum(0.0, QOS_TARGET - qos_row) / QOS_TARGET
    j_event = (
        1.0 - float(deficit[event_window].mean())
        if event_window.any()
        else 1.0
    )
    ordinary = ~event_window
    if not ordinary.any():
        raise ValueError("G2 episode leaves no ordinary-service metric support")
    j_rejoin = (
        1.0 - float(deficit[rejoin_window].mean())
        if rejoin_window.any()
        else None
    )
    cutoff_total = int(cutoff_row.sum())
    depletion_total = int(depletion_row.sum())
    inactive_count = PHYSICAL_UAVS - active.sum(axis=1)
    return G2EpisodeMetrics(
        phi=float(safety_row.mean()),
        j_event=j_event,
        j_rejoin=j_rejoin,
        q_ordinary=float(qos_row[ordinary].mean()),
        catastrophe_episode=int(cutoff_total + depletion_total > 0),
        mean_return_cost_burden=float(return_row.mean()),
        cutoff_events=cutoff_total,
        depletion_events=depletion_total,
        complete_charge_cycles=complete_cycles,
        complete_recovery_windows=bool(complete_recovery),
        station_used=bool(np.any(occupancy > 0)),
        max_concurrent_absence=int(inactive_count.max()),
        no_charge_pressure=bool(
            np.any(return_row > 0.0) or cutoff_total > 0 or depletion_total > 0
        ),
        physical_consistency=bool(physical_consistency),
        action_path_sha256=path_sha256,
        queue_uav_steps=int(queues.sum()),
        max_queue_length=int(queues.max()),
    )


def cell_access(j_event: float, q_ordinary: float) -> float:
    return min(float(j_event) / 0.80, float(q_ordinary) / 0.90)


def source_support_facts(
    metrics: Sequence[G2EpisodeMetrics],
) -> dict[str, Any]:
    rows = tuple(metrics)
    if not rows:
        raise ValueError("G2 source support requires episode metrics")
    return {
        "constructive_cutoff_events": int(sum(row.cutoff_events for row in rows)),
        "constructive_depletion_events": int(
            sum(row.depletion_events for row in rows)
        ),
        "constructive_return_cost_zero": bool(
            all(row.mean_return_cost_burden == 0.0 for row in rows)
        ),
        "complete_charge_cycles": int(
            sum(row.complete_charge_cycles for row in rows)
        ),
        "complete_recovery_windows": bool(
            all(row.complete_recovery_windows for row in rows)
        ),
        "station_used_every_episode": bool(all(row.station_used for row in rows)),
        "concurrent_absence_episodes": int(
            sum(row.max_concurrent_absence >= 2 for row in rows)
        ),
        "no_charge_pressure_episodes": int(sum(row.no_charge_pressure for row in rows)),
        "physical_consistency": bool(all(row.physical_consistency for row in rows)),
    }


def _stack_views(views: Sequence[G2CurrentView]) -> G2CurrentView:
    if not views:
        raise ValueError("G2 view stack cannot be empty")
    steps = {int(view.physical_step) for view in views}
    if len(steps) != 1:
        raise RuntimeError("G2 vector environments left the shared physical clock")
    return G2CurrentView(
        observations=np.stack([view.observations for view in views]),
        active_mask=np.stack([view.active_mask for view in views]),
        critic_state=np.stack([view.critic_state for view in views]),
        lifecycle_state=np.stack([view.lifecycle_state for view in views]),
        physical_positions=np.stack([view.physical_positions for view in views]),
        battery_ratios=np.stack([view.battery_ratios for view in views]),
        station_occupancy=np.stack([view.station_occupancy for view in views]),
        queue_lengths=np.stack([view.queue_lengths for view in views]),
        physical_step=steps.pop(),
    )


@dataclass(frozen=True)
class G2VectorTransition:
    view: G2CurrentView
    rewards: np.ndarray
    qos: np.ndarray
    safety_scores: np.ndarray
    return_costs: np.ndarray
    cutoff_counts: np.ndarray
    depletion_counts: np.ndarray
    dones: np.ndarray
    executed_action_mask: np.ndarray
    physical_action_mask: np.ndarray
    service_actions: np.ndarray
    events: tuple[tuple[LifecycleEvent, ...], ...]
    source_facts: tuple[Mapping[str, Any], ...]


def _g2_worker_main(connection: Connection) -> None:
    environment: UAVChargeRotationEnv | None = None
    controllers: dict[str, Any] = {}
    try:
        connection.send({"ok": True, "kind": "ready"})
        while True:
            request = connection.recv()
            command = request.get("command")
            if command == "reset":
                if environment is not None:
                    environment.close()
                environment = make_g2_environment(
                    request["ledger"],
                    int(request["environment_seed"]),
                    request.get("env_kwargs"),
                )
                environment.reset()
                controllers = {}
                connection.send({"ok": True, "view": environment.current_view()})
            elif command == "step":
                if environment is None:
                    raise RuntimeError("G2 worker step requested before reset")
                transition = environment.step(request["actions"])
                connection.send({"ok": True, "transition": transition})
            elif command == "controller_step":
                if environment is None:
                    raise RuntimeError("G2 controller step requested before reset")
                kind = str(request["kind"])
                if kind not in {
                    CONSTRUCTIVE_CHARGE_ROTATION,
                    NO_PROACTIVE_ROTATION,
                }:
                    raise ValueError(f"unknown G2 controller: {kind!r}")
                if kind not in controllers:
                    controller_type = (
                        ConstructiveChargeRotationController
                        if kind == CONSTRUCTIVE_CHARGE_ROTATION
                        else NoProactiveRotationController
                    )
                    controllers[kind] = controller_type()
                    controllers[kind].reset(environment)
                controller = controllers[kind]
                transition = environment.step(controller.act(environment))
                controller.observe_boundary(environment)
                transition = replace(
                    transition,
                    source_facts={
                        **transition.source_facts,
                        **controller.source_evidence(),
                    },
                )
                connection.send({"ok": True, "transition": transition})
            elif command == "spec":
                if environment is None:
                    raise RuntimeError("G2 worker spec requested before reset")
                view = environment.current_view()
                connection.send(
                    {
                        "ok": True,
                        "observation_dim": int(view.observations.shape[-1]),
                        "critic_state_dim": int(view.critic_state.size),
                        "physical_width": PHYSICAL_UAVS,
                        "action_dim": ACTION_DIM,
                        "horizon": HORIZON,
                    }
                )
            elif command == "close":
                if environment is not None:
                    environment.close()
                connection.send({"ok": True, "kind": "closed"})
                return
            else:
                raise ValueError(f"unknown G2 worker command: {command!r}")
    except BaseException:
        try:
            connection.send({"ok": False, "traceback": traceback.format_exc()})
        finally:
            if environment is not None:
                environment.close()
    finally:
        connection.close()


class PersistentG2VectorEnv:
    """Persistent spawn workers with local batched policy inference."""

    def __init__(
        self,
        ledgers: Sequence[G2EpisodeLedger],
        environment_seeds: Sequence[int],
        *,
        env_kwargs: Mapping[str, Any] | None = None,
        start_method: str = "spawn",
    ) -> None:
        if not ledgers or len(ledgers) != len(environment_seeds):
            raise ValueError("G2 vector rows must be aligned and non-empty")
        self.count = len(ledgers)
        self.env_kwargs = dict(env_kwargs or {})
        context = mp.get_context(start_method)
        self._connections: list[Connection] = []
        self._processes: list[mp.Process] = []
        self._closed = False
        for index in range(self.count):
            parent, child = context.Pipe()
            process = context.Process(
                target=_g2_worker_main,
                args=(child,),
                name=f"uav-g2-env-{index}",
            )
            process.start()
            child.close()
            self._connections.append(parent)
            self._processes.append(process)
        self._receive_all()
        self._view = self.reset(
            ledgers=ledgers, environment_seeds=environment_seeds
        )

    def _receive_all(self) -> list[dict[str, Any]]:
        replies = []
        for index, connection in enumerate(self._connections):
            try:
                reply = connection.recv()
            except (EOFError, BrokenPipeError) as error:
                raise RuntimeError(
                    f"G2 worker {index} exited without a terminal reply"
                ) from error
            if not reply.get("ok", False):
                raise RuntimeError(
                    f"G2 worker {index} failed:\n{reply.get('traceback', '')}"
                )
            replies.append(reply)
        return replies

    @property
    def current_view(self) -> G2CurrentView:
        return self._view

    def reset(
        self,
        *,
        ledgers: Sequence[G2EpisodeLedger],
        environment_seeds: Sequence[int],
    ) -> G2CurrentView:
        if len(ledgers) != self.count or len(environment_seeds) != self.count:
            raise ValueError("G2 vector reset row count changed")
        for connection, ledger, seed in zip(
            self._connections, ledgers, environment_seeds
        ):
            connection.send(
                {
                    "command": "reset",
                    "ledger": ledger,
                    "environment_seed": int(seed),
                    "env_kwargs": self.env_kwargs,
                }
            )
        replies = self._receive_all()
        self._view = _stack_views([reply["view"] for reply in replies])
        return self._view

    def spec(self) -> dict[str, int]:
        for connection in self._connections:
            connection.send({"command": "spec"})
        replies = self._receive_all()
        specs = [
            {key: value for key, value in row.items() if key != "ok"}
            for row in replies
        ]
        if any(spec != specs[0] for spec in specs[1:]):
            raise RuntimeError("G2 vector worker specifications differ")
        return specs[0]

    @staticmethod
    def _stack_transitions(
        transitions: Sequence[G2Transition],
    ) -> G2VectorTransition:
        return G2VectorTransition(
            view=_stack_views([row.view for row in transitions]),
            rewards=np.asarray([row.reward for row in transitions], dtype=np.float32),
            qos=np.asarray(
                [row.qos_satisfaction_ratio for row in transitions], dtype=np.float64
            ),
            safety_scores=np.asarray(
                [row.safety_score_before_pbrs for row in transitions],
                dtype=np.float64,
            ),
            return_costs=np.asarray(
                [row.return_constraint_cost for row in transitions], dtype=np.float64
            ),
            cutoff_counts=np.asarray(
                [row.cutoff_event_count for row in transitions], dtype=np.int64
            ),
            depletion_counts=np.asarray(
                [row.depletion_event_count for row in transitions], dtype=np.int64
            ),
            dones=np.asarray(
                [row.terminated or row.truncated for row in transitions],
                dtype=np.bool_,
            ),
            executed_action_mask=np.stack(
                [row.executed_action_mask for row in transitions]
            ),
            physical_action_mask=np.stack(
                [row.physical_action_mask for row in transitions]
            ),
            service_actions=np.stack([row.service_actions for row in transitions]),
            events=tuple(row.events for row in transitions),
            source_facts=tuple(row.source_facts for row in transitions),
        )

    def step(self, actions: np.ndarray) -> G2VectorTransition:
        values = np.asarray(actions, dtype=np.float32)
        if values.shape != (self.count, PHYSICAL_UAVS, ACTION_DIM):
            raise ValueError("G2 vector action shape mismatch")
        for connection, row in zip(self._connections, values):
            connection.send({"command": "step", "actions": row})
        replies = self._receive_all()
        stacked = self._stack_transitions(
            [reply["transition"] for reply in replies]
        )
        self._view = stacked.view
        return stacked

    def controller_step(self, kind: str) -> G2VectorTransition:
        if kind not in {CONSTRUCTIVE_CHARGE_ROTATION, NO_PROACTIVE_ROTATION}:
            raise ValueError("unknown G2 evaluation controller")
        for connection in self._connections:
            connection.send({"command": "controller_step", "kind": kind})
        replies = self._receive_all()
        stacked = self._stack_transitions(
            [reply["transition"] for reply in replies]
        )
        self._view = stacked.view
        return stacked

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for connection, process in zip(self._connections, self._processes):
            if process.is_alive():
                try:
                    connection.send({"command": "close"})
                except (BrokenPipeError, EOFError):
                    pass
        for connection, process in zip(self._connections, self._processes):
            if process.is_alive():
                try:
                    reply = connection.recv()
                    if not reply.get("ok", False):
                        raise RuntimeError(
                            reply.get("traceback", "G2 worker close failed")
                        )
                except EOFError:
                    pass
            process.join(timeout=10.0)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5.0)
            connection.close()

    def __enter__(self) -> "PersistentG2VectorEnv":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()


def collect_g2_trajectory(
    model: MatchedChargeRotationPolicy,
    vector_env: PersistentG2VectorEnv,
    *,
    episode_ids: Sequence[int],
    action_seed: int,
    device: torch.device,
    horizon: int = HORIZON,
) -> G2Trajectory:
    if len(episode_ids) != vector_env.count:
        raise ValueError("G2 episode IDs do not align with vector workers")
    noise = make_action_noise(
        episode_ids, action_seed=action_seed, horizon=int(horizon)
    )
    hidden = torch.zeros(
        (vector_env.count, PHYSICAL_UAVS, model.hidden_dim),
        dtype=torch.float32,
        device=device,
    )
    tensor_rows: dict[str, list[torch.Tensor]] = {
        name: []
        for name in (
            "observations",
            "active_mask",
            "critic_states",
            "actions",
            "pre_tanh_actions",
            "old_log_probs",
            "old_values",
            "rewards",
            "dones",
            "hidden_before",
            "hidden_after",
            "prefix_action_sums",
        )
    }
    array_rows: dict[str, list[np.ndarray]] = {
        name: []
        for name in (
            "qos",
            "safety_scores",
            "return_costs",
            "cutoff_counts",
            "depletion_counts",
            "station_occupancy",
            "queue_lengths",
            "lifecycle_states",
            "next_lifecycle_states",
            "physical_consistency",
        )
    }
    event_rows: list[list[LifecycleEvent]] = [
        [] for _ in range(vector_env.count)
    ]
    view = vector_env.current_view
    model.eval()
    with torch.no_grad():
        for time in range(int(horizon)):
            observations = torch.as_tensor(view.observations, device=device)
            active_mask = torch.as_tensor(view.active_mask, device=device)
            critic_states = torch.as_tensor(view.critic_state, device=device)
            hidden_before = hidden.clone()
            output = model.forward_step(
                observations=observations,
                active_mask=active_mask,
                critic_state=critic_states,
                hidden=hidden,
                sampling_noise=torch.as_tensor(noise[time], device=device),
            )
            transition = vector_env.step(output.actions.detach().cpu().numpy())
            if not np.array_equal(
                transition.executed_action_mask, view.active_mask
            ):
                raise RuntimeError(
                    "G2 collected likelihood mask differs from executed service mask"
                )
            if not np.array_equal(
                transition.service_actions,
                output.actions.detach().cpu().numpy(),
            ):
                raise RuntimeError("G2 collected action path differs from environment input")
            tensor_rows["observations"].append(observations.cpu())
            tensor_rows["active_mask"].append(active_mask.cpu())
            tensor_rows["critic_states"].append(critic_states.cpu())
            tensor_rows["actions"].append(output.actions.cpu())
            tensor_rows["pre_tanh_actions"].append(output.pre_tanh_actions.cpu())
            tensor_rows["old_log_probs"].append(output.token_log_probs.cpu())
            tensor_rows["old_values"].append(output.value.cpu())
            tensor_rows["rewards"].append(torch.as_tensor(transition.rewards))
            tensor_rows["dones"].append(torch.as_tensor(transition.dones))
            tensor_rows["hidden_before"].append(hidden_before.cpu())
            terminal = torch.as_tensor(
                transition.view.lifecycle_state == int(LifecycleState.TERMINAL),
                device=device,
            ).unsqueeze(-1)
            owned_next_hidden = torch.where(
                terminal, torch.zeros_like(output.next_hidden), output.next_hidden
            )
            tensor_rows["hidden_after"].append(owned_next_hidden.cpu())
            tensor_rows["prefix_action_sums"].append(
                output.prefix_action_sums.cpu()
            )
            array_rows["qos"].append(transition.qos)
            array_rows["safety_scores"].append(transition.safety_scores)
            array_rows["return_costs"].append(transition.return_costs)
            array_rows["cutoff_counts"].append(transition.cutoff_counts)
            array_rows["depletion_counts"].append(transition.depletion_counts)
            array_rows["station_occupancy"].append(
                transition.view.station_occupancy.copy()
            )
            array_rows["queue_lengths"].append(
                transition.view.queue_lengths.copy()
            )
            array_rows["lifecycle_states"].append(view.lifecycle_state.copy())
            array_rows["next_lifecycle_states"].append(
                transition.view.lifecycle_state.copy()
            )
            array_rows["physical_consistency"].append(
                np.asarray(
                    [
                        bool(facts.get("physical_consistency", False))
                        for facts in transition.source_facts
                    ],
                    dtype=np.bool_,
                )
            )
            for batch, events in enumerate(transition.events):
                event_rows[batch].extend(events)
            hidden = owned_next_hidden
            if bool(torch.as_tensor(transition.dones).any()):
                done = torch.as_tensor(
                    transition.dones, device=device
                ).view(vector_env.count, 1, 1)
                hidden = torch.where(done, torch.zeros_like(hidden), hidden)
            view = transition.view
    return G2Trajectory(
        observations=torch.stack(tensor_rows["observations"]),
        active_mask=torch.stack(tensor_rows["active_mask"]),
        critic_states=torch.stack(tensor_rows["critic_states"]),
        actions=torch.stack(tensor_rows["actions"]),
        pre_tanh_actions=torch.stack(tensor_rows["pre_tanh_actions"]),
        old_log_probs=torch.stack(tensor_rows["old_log_probs"]),
        old_values=torch.stack(tensor_rows["old_values"]),
        rewards=torch.stack(tensor_rows["rewards"]),
        dones=torch.stack(tensor_rows["dones"]),
        hidden_before=torch.stack(tensor_rows["hidden_before"]),
        hidden_after=torch.stack(tensor_rows["hidden_after"]),
        prefix_action_sums=torch.stack(tensor_rows["prefix_action_sums"]),
        qos=np.stack(array_rows["qos"]),
        safety_scores=np.stack(array_rows["safety_scores"]),
        return_costs=np.stack(array_rows["return_costs"]),
        cutoff_counts=np.stack(array_rows["cutoff_counts"]),
        depletion_counts=np.stack(array_rows["depletion_counts"]),
        station_occupancy=np.stack(array_rows["station_occupancy"]),
        queue_lengths=np.stack(array_rows["queue_lengths"]),
        lifecycle_states=np.stack(array_rows["lifecycle_states"]),
        next_lifecycle_states=np.stack(array_rows["next_lifecycle_states"]),
        physical_consistency=np.stack(array_rows["physical_consistency"]),
        events=tuple(tuple(row) for row in event_rows),
        ledger_ids=tuple(str(value) for value in episode_ids),
    )


def trajectory_episode_metrics(
    trajectory: G2Trajectory,
) -> tuple[G2EpisodeMetrics, ...]:
    horizon, batch = trajectory.rewards.shape
    if horizon != HORIZON:
        raise ValueError("registered G2 episode metrics require the full horizon")
    rows = []
    for index in range(batch):
        rows.append(
            compute_episode_metrics(
                qos=trajectory.qos[:, index],
                safety_scores=trajectory.safety_scores[:, index],
                return_costs=trajectory.return_costs[:, index],
                cutoff_counts=trajectory.cutoff_counts[:, index],
                depletion_counts=trajectory.depletion_counts[:, index],
                active_masks=trajectory.active_mask[:, index].cpu().numpy(),
                station_occupancy=trajectory.station_occupancy[:, index],
                queue_lengths=trajectory.queue_lengths[:, index],
                service_actions=trajectory.actions[:, index].cpu().numpy(),
                executed_action_masks=trajectory.active_mask[:, index].cpu().numpy(),
                events=trajectory.events[index],
                physical_consistency=bool(
                    np.asarray(trajectory.physical_consistency[:, index]).all()
                ),
            )
        )
    return tuple(rows)


@dataclass(frozen=True)
class G2ControlSourceEvidence:
    controller_name: str
    candidate_order: tuple[int, ...]
    projected_terminal_margins: tuple[float, ...]
    station_assignments: tuple[int, ...]
    departure_steps: tuple[int, ...]
    planned_completion_steps: tuple[int, ...]
    first_departure_step: int
    candidate_iff_negative_terminal_margin: bool
    strict_nearest_station_assignment: bool
    latest_safe_departure_verified: bool
    common_actions_before_first_departure: bool
    targets_frozen_at_first_departure: bool | None
    target_freeze_step: int | None
    reallocation_event_steps: tuple[int, ...]
    lifecycle_boundary_steps: tuple[int, ...]
    reallocation_after_every_leave_rejoin: bool
    current_only_planning: bool
    future_user_channel_queue_policy_rng_used: bool
    projection_audit_history: tuple[G2ProjectionAudit, ...]
    projection_audit_count: int
    initial_candidate_order: tuple[int, ...]
    initial_source_pressure: bool
    all_projection_audits_pass: bool
    plan_consistency: bool
    physical_consistency: bool


@dataclass(frozen=True)
class G2ControlEvaluation:
    metrics: tuple[G2EpisodeMetrics, ...]
    evidence: tuple[G2ControlSourceEvidence, ...]


def _evaluate_g2_rollout(
    vector_env: PersistentG2VectorEnv,
    action_provider: Any,
) -> tuple[
    tuple[G2EpisodeMetrics, ...],
    tuple[tuple[Mapping[str, Any], ...], ...],
]:
    batch = vector_env.count
    qos = np.empty((HORIZON, batch), dtype=np.float64)
    safety = np.empty_like(qos)
    return_cost = np.empty_like(qos)
    cutoff = np.empty((HORIZON, batch), dtype=np.int64)
    depletion = np.empty_like(cutoff)
    active = np.empty((HORIZON, batch, PHYSICAL_UAVS), dtype=np.bool_)
    occupancy = np.empty((HORIZON, batch, 2), dtype=np.int64)
    queues = np.empty((HORIZON, batch, 2), dtype=np.int64)
    service_actions = np.empty(
        (HORIZON, batch, PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32
    )
    executed_masks = np.empty(
        (HORIZON, batch, PHYSICAL_UAVS), dtype=np.bool_
    )
    consistency = np.ones((HORIZON, batch), dtype=np.bool_)
    events: list[list[LifecycleEvent]] = [[] for _ in range(batch)]
    fact_rows: list[list[Mapping[str, Any]]] = [[] for _ in range(batch)]
    for time in range(HORIZON):
        view = vector_env.current_view
        active[time] = view.active_mask
        transition = action_provider(time, view)
        if not np.array_equal(transition.executed_action_mask, view.active_mask):
            raise RuntimeError(
                "G2 evaluation likelihood mask differs from executed service mask"
            )
        qos[time] = transition.qos
        safety[time] = transition.safety_scores
        return_cost[time] = transition.return_costs
        cutoff[time] = transition.cutoff_counts
        depletion[time] = transition.depletion_counts
        occupancy[time] = transition.view.station_occupancy
        queues[time] = transition.view.queue_lengths
        service_actions[time] = transition.service_actions
        executed_masks[time] = transition.executed_action_mask
        consistency[time] = [
            bool(row.get("physical_consistency", False))
            for row in transition.source_facts
        ]
        for index, row in enumerate(transition.events):
            events[index].extend(row)
        for index, row in enumerate(transition.source_facts):
            fact_rows[index].append(row)
    metrics = tuple(
        compute_episode_metrics(
            qos=qos[:, index],
            safety_scores=safety[:, index],
            return_costs=return_cost[:, index],
            cutoff_counts=cutoff[:, index],
            depletion_counts=depletion[:, index],
            active_masks=active[:, index],
            station_occupancy=occupancy[:, index],
            queue_lengths=queues[:, index],
            service_actions=service_actions[:, index],
            executed_action_masks=executed_masks[:, index],
            events=events[index],
            physical_consistency=bool(consistency[:, index].all()),
        )
        for index in range(batch)
    )
    return metrics, tuple(tuple(row) for row in fact_rows)


def evaluate_g2_policy(
    model: MatchedChargeRotationPolicy,
    vector_env: PersistentG2VectorEnv,
    *,
    episode_ids: Sequence[int],
    action_seed: int,
    device: torch.device,
    deterministic: bool,
) -> tuple[G2EpisodeMetrics, ...]:
    if len(episode_ids) != vector_env.count:
        raise ValueError("G2 evaluation episode IDs do not align with workers")
    noise = None if deterministic else make_action_noise(
        episode_ids, action_seed=action_seed, horizon=HORIZON
    )
    hidden = torch.zeros(
        (vector_env.count, PHYSICAL_UAVS, model.hidden_dim),
        dtype=torch.float32,
        device=device,
    )
    model.eval()

    @torch.no_grad()
    def provider(time: int, view: G2CurrentView) -> G2VectorTransition:
        nonlocal hidden
        kwargs: dict[str, Any] = (
            {"deterministic": True}
            if deterministic
            else {"sampling_noise": torch.as_tensor(noise[time], device=device)}
        )
        output = model.forward_step(
            observations=torch.as_tensor(view.observations, device=device),
            active_mask=torch.as_tensor(view.active_mask, device=device),
            critic_state=torch.as_tensor(view.critic_state, device=device),
            hidden=hidden,
            **kwargs,
        )
        transition = vector_env.step(output.actions.detach().cpu().numpy())
        terminal = torch.as_tensor(
            transition.view.lifecycle_state == int(LifecycleState.TERMINAL),
            device=device,
        ).unsqueeze(-1)
        hidden = torch.where(
            terminal, torch.zeros_like(output.next_hidden), output.next_hidden
        )
        return transition

    metrics, _facts = _evaluate_g2_rollout(vector_env, provider)
    return metrics


def evaluate_g2_controller(
    vector_env: PersistentG2VectorEnv,
    *,
    kind: str,
) -> G2ControlEvaluation:
    if kind not in {CONSTRUCTIVE_CHARGE_ROTATION, NO_PROACTIVE_ROTATION}:
        raise ValueError("unknown G2 evaluation controller")

    def provider(_time: int, _view: G2CurrentView) -> G2VectorTransition:
        return vector_env.controller_step(kind)

    metrics, fact_rows = _evaluate_g2_rollout(vector_env, provider)
    evidence = []
    for rows in fact_rows:
        if not rows:
            raise RuntimeError("G2 controller evaluation emitted no source facts")
        final = rows[-1]
        evidence.append(
            G2ControlSourceEvidence(
                controller_name=str(final["controller_name"]),
                candidate_order=tuple(int(value) for value in final["candidate_order"]),
                projected_terminal_margins=tuple(
                    float(value) for value in final["projected_terminal_margins"]
                ),
                station_assignments=tuple(
                    int(value) for value in final["station_assignments"]
                ),
                departure_steps=tuple(
                    int(value) for value in final["departure_steps"]
                ),
                planned_completion_steps=tuple(
                    int(value) for value in final["planned_completion_steps"]
                ),
                first_departure_step=int(final["first_departure_step"]),
                candidate_iff_negative_terminal_margin=bool(
                    final["candidate_iff_negative_terminal_margin"]
                ),
                strict_nearest_station_assignment=bool(
                    final["strict_nearest_station_assignment"]
                ),
                latest_safe_departure_verified=bool(
                    final["latest_safe_departure_verified"]
                ),
                common_actions_before_first_departure=bool(
                    final["common_actions_before_first_departure"]
                ),
                targets_frozen_at_first_departure=(
                    bool(final["targets_frozen_at_first_departure"])
                    if "targets_frozen_at_first_departure" in final
                    else None
                ),
                target_freeze_step=(
                    int(final["target_freeze_step"])
                    if final.get("target_freeze_step") is not None
                    else None
                ),
                reallocation_event_steps=tuple(
                    int(value) for value in final["reallocation_event_steps"]
                ),
                lifecycle_boundary_steps=tuple(
                    int(value) for value in final["lifecycle_boundary_steps"]
                ),
                reallocation_after_every_leave_rejoin=bool(
                    final["reallocation_after_every_leave_rejoin"]
                ),
                current_only_planning=bool(final["current_only_planning"]),
                future_user_channel_queue_policy_rng_used=bool(
                    final["future_user_channel_queue_policy_rng_used"]
                ),
                projection_audit_history=tuple(final["projection_audit_history"]),
                projection_audit_count=int(final["projection_audit_count"]),
                initial_candidate_order=tuple(
                    int(value) for value in final["initial_candidate_order"]
                ),
                initial_source_pressure=bool(final["initial_source_pressure"]),
                all_projection_audits_pass=bool(
                    final["all_projection_audits_pass"]
                ),
                plan_consistency=bool(final["plan_consistency"]),
                physical_consistency=bool(
                    all(row.get("physical_consistency", False) for row in rows)
                    and final["plan_consistency"]
                ),
            )
        )
    return G2ControlEvaluation(metrics=metrics, evidence=tuple(evidence))


def model_state_copy(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }


def maximum_state_difference(
    left: Mapping[str, torch.Tensor], right: Mapping[str, torch.Tensor]
) -> float:
    if left.keys() != right.keys():
        return float("inf")
    return max(
        (
            float(torch.max(torch.abs(left[name] - right[name])))
            for name in left
        ),
        default=0.0,
    )


def g2_checkpoint_state(
    *,
    model: MatchedChargeRotationPolicy,
    optimizer: torch.optim.Optimizer,
    completed_updates: int,
    next_episode_id: int,
    seed_contract: Mapping[str, int],
) -> dict[str, Any]:
    """Return complete continuation state; the runner owns durable writing."""

    return {
        "schema_version": 1,
        "routing_mode": model.routing_mode,
        "model_state": model_state_copy(model),
        "optimizer_state": copy.deepcopy(optimizer.state_dict()),
        "completed_updates": int(completed_updates),
        "next_episode_id": int(next_episode_id),
        "seed_contract": {str(key): int(value) for key, value in seed_contract.items()},
        "torch_rng_state": torch.get_rng_state(),
    }


def load_g2_checkpoint_state(
    payload: Mapping[str, Any],
    *,
    model: MatchedChargeRotationPolicy,
    optimizer: torch.optim.Optimizer,
    expected_seed_contract: Mapping[str, int],
) -> dict[str, Any]:
    if int(payload.get("schema_version", -1)) != 1:
        raise ValueError("G2 checkpoint schema mismatch")
    if str(payload.get("routing_mode")) != model.routing_mode:
        raise ValueError("G2 checkpoint routing mode mismatch")
    expected = {str(key): int(value) for key, value in expected_seed_contract.items()}
    if payload.get("seed_contract") != expected:
        raise ValueError("G2 checkpoint seed contract mismatch")
    model.load_state_dict(payload["model_state"])
    optimizer.load_state_dict(payload["optimizer_state"])
    torch.set_rng_state(payload["torch_rng_state"])
    return {
        "completed_updates": int(payload["completed_updates"]),
        "next_episode_id": int(payload["next_episode_id"]),
    }
