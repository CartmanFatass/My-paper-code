"""Frozen P0 demand source for the G33 UAV source-witness audit.

This module owns only the episode-addressed demand ledger and the source-local
Scenario-7 view.  It deliberately contains no controller, oracle, learner,
optimizer, runner, or result branch.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

import numpy as np
from gymnasium.spaces import Box, Dict

from config_1 import Config
from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv


PHYSICAL_UAVS = 8
N_USERS = 30
ORDINARY_DEMAND_BPS = 1.0e6
_ONSET_NAMESPACE = 101
_DURATION_NAMESPACE = 102
_MULTIPLIER_NAMESPACE = 103
_CENTER_NAMESPACE = 104


class BurstProfile(str, Enum):
    NO_BURST = "NO_BURST"
    IID_BURST = "IID_BURST"
    EARLY_LONG = "EARLY_LONG"
    REMOTE_STRONG = "REMOTE_STRONG"


@dataclass(frozen=True)
class G33EpisodeLedger:
    """Immutable episode-addressed burst draws, independent of physical RNG."""

    profile: BurstProfile
    episode_id: int
    onset: int | None
    duration: int
    multiplier: float
    center_selector: int
    ledger_id: str

    def __post_init__(self) -> None:
        profile = BurstProfile(self.profile)
        onset = self.onset
        duration = int(self.duration)
        multiplier = float(self.multiplier)
        selector = int(self.center_selector)
        if profile is BurstProfile.NO_BURST:
            if onset is not None or duration != 0 or multiplier != 1.0 or selector != -1:
                raise ValueError("NO_BURST ledger fields are not canonical")
        elif profile is BurstProfile.IID_BURST:
            if onset not in range(140, 261) or duration not in range(40, 81):
                raise ValueError("IID_BURST onset or duration is outside the frozen law")
            if multiplier not in {1.5, 2.0} or selector not in range(N_USERS):
                raise ValueError("IID_BURST multiplier or center selector drifted")
        elif profile is BurstProfile.EARLY_LONG:
            if onset not in range(60, 121) or duration not in range(90, 121):
                raise ValueError("EARLY_LONG onset or duration is outside the frozen law")
            if multiplier != 2.25 or selector not in range(N_USERS):
                raise ValueError("EARLY_LONG multiplier or center selector drifted")
        elif profile is BurstProfile.REMOTE_STRONG:
            if onset not in range(180, 261) or duration not in range(70, 111):
                raise ValueError("REMOTE_STRONG onset or duration is outside the frozen law")
            if multiplier != 2.5 or selector not in range(8):
                raise ValueError("REMOTE_STRONG multiplier or center selector drifted")
        object.__setattr__(self, "profile", profile)
        object.__setattr__(self, "episode_id", int(self.episode_id))
        object.__setattr__(self, "duration", duration)
        object.__setattr__(self, "multiplier", multiplier)
        object.__setattr__(self, "center_selector", selector)


def make_g33_episode_ledger(
    profile: BurstProfile | str,
    episode_id: int,
    *,
    burst_seed: int,
) -> G33EpisodeLedger:
    """Draw a registered ledger without consuming environment, channel, or policy RNG."""

    chosen = BurstProfile(profile)
    profile_index = tuple(BurstProfile).index(chosen)
    def field_rng(namespace: int) -> np.random.Generator:
        return np.random.default_rng(
            np.random.SeedSequence(
                [int(burst_seed), int(episode_id), profile_index, 0x473333, namespace]
            )
        )
    if chosen is BurstProfile.NO_BURST:
        return G33EpisodeLedger(chosen, episode_id, None, 0, 1.0, -1, f"{chosen.value}/{episode_id}")
    if chosen is BurstProfile.IID_BURST:
        onset = int(field_rng(_ONSET_NAMESPACE).integers(140, 261))
        duration = int(field_rng(_DURATION_NAMESPACE).integers(40, 81))
        multiplier = float((1.5, 2.0)[int(field_rng(_MULTIPLIER_NAMESPACE).integers(0, 2))])
        selector = int(field_rng(_CENTER_NAMESPACE).integers(0, N_USERS))
    elif chosen is BurstProfile.EARLY_LONG:
        onset = int(field_rng(_ONSET_NAMESPACE).integers(60, 121))
        duration = int(field_rng(_DURATION_NAMESPACE).integers(90, 121))
        multiplier, selector = 2.25, int(field_rng(_CENTER_NAMESPACE).integers(0, N_USERS))
    else:
        onset = int(field_rng(_ONSET_NAMESPACE).integers(180, 261))
        duration = int(field_rng(_DURATION_NAMESPACE).integers(70, 111))
        multiplier, selector = 2.5, int(field_rng(_CENTER_NAMESPACE).integers(0, 8))
    return G33EpisodeLedger(
        chosen,
        int(episode_id),
        onset,
        duration,
        multiplier,
        selector,
        f"{chosen.value}/{int(episode_id)}/{onset}/{duration}/{multiplier:g}/{selector}",
    )


class UAVLocalizedDemandBurstEnv(UAVEnergyAwareRelayEnv):
    """S7-S1 with current demand only; all radio and physical equations stay base-owned."""

    actor_user_record_width = 7
    critic_user_record_width = 7

    def __init__(
        self,
        ledger: G33EpisodeLedger,
        environment_seed: int,
        env_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        self.episode_ledger = ledger
        self.environment_seed = int(environment_seed)
        self.current_user_demand_bps = np.full(N_USERS, ORDINARY_DEMAND_BPS, dtype=np.float64)
        self._affected_cohort = np.empty(0, dtype=np.int64)
        self._burst_center_user = -1
        self._onset_visibility: dict[str, Any] | None = None
        self._reset_namespace_rngs(self.environment_seed)
        kwargs = dict(env_kwargs or {})
        unsupported = set(kwargs).difference({"render_mode"})
        if unsupported:
            raise ValueError("env_kwargs cannot override frozen S7-S1 fields: " + ", ".join(sorted(unsupported)))
        super().__init__(config=Config("S7-S1"), seed=self.environment_seed, **kwargs)
        if self.n_uavs != PHYSICAL_UAVS or self.n_users != N_USERS or self.max_steps != 500:
            raise RuntimeError("G33 P0 requires S7-S1 width, users, and horizon")
        if self.battery_enabled or self.charging_enabled or self.failure_enabled:
            raise RuntimeError("G33 P0 requires battery, charging, and failure disabled")
        self._ordinary_obs_dim = int(self.obs_dim)
        self._ordinary_state_dim = int(self.state_dim)
        self._ordinary_base_obs_dim = self._ordinary_obs_dim - self.energy_obs_extra_dim
        self._ordinary_base_state_dim = self._ordinary_state_dim - self.energy_state_extra_dim
        self._ordinary_actor_user_width = 7 if self.predictive_handover else (6 if self.enable_soft_handover else 5)
        self.obs_dim = self._ordinary_obs_dim + self.max_observed_users * (
            self.actor_user_record_width - self._ordinary_actor_user_width
        ) - 1
        self.state_dim = self._ordinary_state_dim + self.n_users - 1
        self.observation_spaces = {
            agent: Dict({
                "obs": Box(low=-float("inf"), high=float("inf"), shape=(self.obs_dim,), dtype=np.float32),
                "action_mask": Box(low=0, high=1, shape=(self.action_dim,), dtype=np.float32),
            })
            for agent in self.possible_agents
        }

    @staticmethod
    def _namespace_random_state(seed: int, namespace: int) -> np.random.RandomState:
        word = np.random.SeedSequence([int(seed), int(namespace)]).generate_state(1)[0]
        return np.random.RandomState(int(word))

    def _reset_namespace_rngs(self, seed: int) -> None:
        self._initial_rng = self._namespace_random_state(seed, 1)
        self._user_rng = self._namespace_random_state(seed, 2)
        self._station_rng = self._namespace_random_state(seed, 3)
        self._energy_reset_rng = self._namespace_random_state(seed, 4)

    def _with_namespace_rng(self, attribute: str, method: Any, *args: Any, **kwargs: Any) -> Any:
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
        return self._with_namespace_rng("_station_rng", super()._init_charging_stations, randomize)

    def _generate_user_positions(self):
        return self._with_namespace_rng("_user_rng", super()._generate_user_positions)

    def _init_user_velocities(self):
        return self._with_namespace_rng("_user_rng", super()._init_user_velocities)

    def _initialize_user_waypoints_rpgm(self):
        return self._with_namespace_rng("_user_rng", super()._initialize_user_waypoints_rpgm)

    def _move_users(self):
        return self._with_namespace_rng("_user_rng", super()._move_users)

    def _reset_energy_state(self):
        return self._with_namespace_rng("_energy_reset_rng", super()._reset_energy_state)

    def _update_channel_state(self):
        step = int(getattr(self, "current_step", 0))
        channel_rng = self._namespace_random_state(self.environment_seed, 10_000 + max(step, 0))
        previous = getattr(self, "np_random", None)
        self.np_random = channel_rng
        try:
            return super()._update_channel_state()
        finally:
            if previous is not None:
                self.np_random = previous

    @property
    def affected_cohort(self) -> np.ndarray:
        return self._affected_cohort.copy()

    @property
    def burst_center_user(self) -> int:
        return int(self._burst_center_user)

    def _current_user_qos_demand_bps(self) -> np.ndarray:
        demand = np.asarray(self.current_user_demand_bps, dtype=np.float64)
        if demand.shape != (self.n_users,) or not np.all(np.isfinite(demand)) or np.any(demand <= 0.0):
            raise RuntimeError("G33 current demand is not a finite positive per-user vector")
        return demand.copy()

    def reset(self, seed: int | None = None, options: Any = None):
        actual_seed = self.environment_seed if seed is None else int(seed)
        self.environment_seed = actual_seed
        self._reset_namespace_rngs(actual_seed)
        self.current_user_demand_bps = np.full(self.n_users, ORDINARY_DEMAND_BPS, dtype=np.float64)
        self._affected_cohort = np.empty(0, dtype=np.int64)
        self._burst_center_user = -1
        self._onset_visibility = None
        observations, infos = super().reset(seed=actual_seed, options=options)
        self.sync_burst_pre_action()
        for agent in self.agents:
            infos[agent]["g33_source"] = self.source_diagnostics()
        return observations, infos

    def step(self, actions):
        # The demand for boundary t is installed before action t.  The parent
        # reward and graph potential use exactly this vector for that transition.
        self.sync_burst_pre_action()
        observations, rewards, terminations, truncations, infos = super().step(actions)
        for agent in self.agents:
            infos[agent]["g33_source"] = self.source_diagnostics()
        return observations, rewards, terminations, truncations, infos

    def _prepare_next_boundary_view(self) -> None:
        """Install q(t+1) before the parent's single returned-view materialization."""

        transition_graph_demand = self.last_graph_potential_demand_bps.copy()
        self.sync_burst_pre_action()
        self.current_graph_potential = self._graph_service_potential()
        # Keep the audit telemetry bound to the just-completed transition; the
        # current demand vector owns the newly prepared boundary potential.
        self.last_graph_potential_demand_bps = transition_graph_demand

    def sync_burst_pre_action(self) -> None:
        """Install q(t), freezing the selected cohort at the pre-action onset."""

        ledger = self.episode_ledger
        if ledger.profile is BurstProfile.NO_BURST:
            self.current_user_demand_bps.fill(ORDINARY_DEMAND_BPS)
            return
        if int(self.current_step) == int(ledger.onset) and self._affected_cohort.size == 0:
            self._affected_cohort, self._burst_center_user = self._resolve_onset_cohort()
            self._onset_visibility = self._collective_onset_visibility()
        active = int(ledger.onset) <= int(self.current_step) < int(ledger.onset) + int(ledger.duration)
        self.current_user_demand_bps.fill(ORDINARY_DEMAND_BPS)
        if active:
            if self._affected_cohort.size == 0:
                raise RuntimeError("G33 burst reached onset without a frozen affected cohort")
            self.current_user_demand_bps[self._affected_cohort] = ORDINARY_DEMAND_BPS * ledger.multiplier

    def _resolve_onset_cohort(self) -> tuple[np.ndarray, int]:
        indices = np.arange(self.n_users, dtype=np.int64)
        if self.episode_ledger.profile is BurstProfile.REMOTE_STRONG:
            distances = np.min(
                np.linalg.norm(
                    self.user_positions[:, None, :2] - self.ground_bs_positions[None, :, :2], axis=2
                ),
                axis=1,
            )
            candidates = np.lexsort((indices, -distances))[:8]
            cohort_size = 10
        else:
            candidates = indices
            cohort_size = 8 if self.episode_ledger.profile is BurstProfile.IID_BURST else 10
        center = int(candidates[self.episode_ledger.center_selector])
        center_position = self.user_positions[center, :2]
        distances = np.linalg.norm(self.user_positions[:, :2] - center_position, axis=1)
        cohort = np.lexsort((indices, distances))[:cohort_size].astype(np.int64)
        return cohort, center

    def _collective_onset_visibility(self) -> dict[str, Any]:
        visible = set()
        for owner in range(self.n_uavs):
            visible.update(int(user) for user, _sinr in self._get_local_users(owner))
        missing = tuple(int(user) for user in self._affected_cohort if int(user) not in visible)
        return {
            "onset_step": int(self.current_step),
            "affected_cohort": tuple(int(user) for user in self._affected_cohort),
            "collectively_visible": not missing,
            "missing_users": missing,
        }

    def _actor_user_rows(self, owner: int) -> np.ndarray:
        own_position = self.uav_positions[int(owner)]
        rows: list[tuple[tuple[float, float, float, float], np.ndarray]] = []
        for user, sinr_db in self._get_local_users(int(owner)):
            user_position = self.user_positions[int(user)]
            relative = (user_position[:2] - own_position[:2]) / self.area_size
            demand = float(self._normalized_current_demand()[int(user)])
            row = np.array((
                relative[0],
                relative[1],
                np.clip((sinr_db + 10.0) / 50.0, 0.0, 1.0),
                float(self.connections[int(owner), int(user)]),
                float(self.user_serviced_status[int(user)]),
                demand,
                1.0,
            ), dtype=np.float32)
            key = (float(np.linalg.norm(user_position - own_position)), float(relative[0]), float(relative[1]), demand)
            rows.append((key, row))
        rows.sort(key=lambda value: value[0])
        result = np.zeros((self.max_observed_users, self.actor_user_record_width), dtype=np.float32)
        for index, (_key, row) in enumerate(rows[: self.max_observed_users]):
            result[index] = row
        return result

    def _get_observation(self, agent: str):
        ordinary = super()._get_observation(agent)["obs"]
        base = ordinary[: self._ordinary_base_obs_dim]
        energy = ordinary[self._ordinary_base_obs_dim :]
        prefix_width = 3 + 3 + 5
        ordinary_user_width = self.max_observed_users * self._ordinary_actor_user_width
        prefix = base[:prefix_width]
        tail_without_time = base[prefix_width + ordinary_user_width : -1]
        actor_rows = self._actor_user_rows(int(agent.split("_")[1])).reshape(-1)
        observation = np.concatenate((prefix, actor_rows, tail_without_time, energy)).astype(np.float32)
        if observation.shape != (self.obs_dim,):
            raise RuntimeError("G33 actor observation width drifted")
        return {"obs": observation, "action_mask": np.ones(self.action_dim, dtype=np.float32)}

    def _get_state(self) -> np.ndarray:
        ordinary = super()._get_state()
        base = ordinary[: self._ordinary_base_state_dim]
        energy = ordinary[self._ordinary_base_state_dim :]
        prefix_width = self.n_uavs * 3 + self.n_uavs
        ordinary_user_width = self.n_users * 6
        prefix = base[:prefix_width]
        users = base[prefix_width : prefix_width + ordinary_user_width].reshape(self.n_users, 6)
        users_with_demand = np.concatenate(
            (users, self._normalized_current_demand()[:, None]), axis=1
        ).reshape(-1)
        tail_without_time = base[prefix_width + ordinary_user_width : -1]
        state = np.concatenate((prefix, users_with_demand, tail_without_time, energy)).astype(np.float32)
        if state.shape != (self.state_dim,):
            raise RuntimeError("G33 critic state width drifted")
        return state

    def _normalized_current_demand(self) -> np.ndarray:
        return np.clip(
            (self.current_user_demand_bps / ORDINARY_DEMAND_BPS - 1.0) / 1.5,
            0.0,
            1.0,
        ).astype(np.float64)

    def source_diagnostics(self) -> dict[str, Any]:
        return {
            "ledger_id": self.episode_ledger.ledger_id,
            "physical_step": int(self.current_step),
            "affected_cohort": tuple(int(user) for user in self._affected_cohort),
            "burst_center_user": int(self._burst_center_user),
            "collective_onset_visibility": self._onset_visibility,
            "actor_has_physical_time": False,
            "critic_has_physical_time": False,
            "future_ledger_exposed": False,
            "assignment_exposed": False,
            "current_normalized_demand": self._normalized_current_demand().copy(),
        }

    def demand_only_invariance_diagnostic(self, proposed_demand_bps: np.ndarray) -> dict[str, bool]:
        """Check the required separation without changing physical state or RNG ownership."""

        proposed = np.asarray(proposed_demand_bps, dtype=np.float64)
        if proposed.shape != (self.n_users,) or np.any(proposed <= 0.0) or not np.all(np.isfinite(proposed)):
            raise ValueError("proposed demand must be a finite positive per-user vector")
        original = self.current_user_demand_bps.copy()
        telemetry = {
            name: deepcopy(getattr(self, name))
            for name in (
                "last_user_rates_mbps", "last_user_demand_bps", "last_delivered_traffic_bps",
                "last_reward_demand_bps", "last_graph_potential_demand_bps",
                "last_access_capacity_bps", "last_backhaul_capacities_bps",
                "last_widest_backhaul_capacities_bps", "last_constrained_reward_metrics",
                "last_energy_reward_components", "prev_energy_failure_mask",
                "cutoff_event_seen", "depletion_event_seen",
            )
        }
        rng_states = {
            name: deepcopy(getattr(self, name).get_state())
            for name in ("np_random", "_initial_rng", "_user_rng", "_station_rng", "_energy_reset_rng")
        }
        raw_before, _access_before, _backhaul_before = self._calculate_end_to_end_user_rates()
        positions_before = self.uav_positions.copy()
        connections_before = self.connections.copy()
        routes_before = {owner: (tuple(path), capacity) for owner, (path, capacity) in self.routing_paths.items()}
        delivered_before = np.minimum(raw_before, original)
        try:
            self.current_user_demand_bps = proposed.copy()
            raw_after, _access_after, _backhaul_after = self._calculate_end_to_end_user_rates()
            delivered_after = np.minimum(raw_after, proposed)
            self._calculate_constrained_safety_reward(0.0, 0.0, 0.0, 0.0, False, 0.0, {})
            self._graph_service_potential()
            reward_demand = self.last_reward_demand_bps.copy()
            potential_demand = self.last_graph_potential_demand_bps.copy()
            routes_after = {owner: (tuple(path), capacity) for owner, (path, capacity) in self.routing_paths.items()}
            physical_unchanged = bool(
                np.array_equal(positions_before, self.uav_positions)
                and np.array_equal(connections_before, self.connections)
                and routes_before == routes_after
            )
        finally:
            self.current_user_demand_bps = original
            for name, value in telemetry.items():
                setattr(self, name, value)
            for name, value in rng_states.items():
                getattr(self, name).set_state(value)
        return {
            "raw_physics_equal": bool(
                np.array_equal(raw_before, raw_after)
                and physical_unchanged
            ),
            "delivered_traffic_changed": bool(not np.array_equal(delivered_before, delivered_after)),
            "same_demand_vector_for_reward_and_potential": bool(
                np.array_equal(reward_demand, proposed)
                and np.array_equal(potential_demand, proposed)
            ),
        }
