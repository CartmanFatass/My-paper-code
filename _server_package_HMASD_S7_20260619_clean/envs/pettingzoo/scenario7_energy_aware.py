import copy

import numpy as np
from gymnasium.spaces import Box, Dict

from envs.pettingzoo.scenario_base import UAVForcedRelayEnv


class _EnergyAwareConfigProxy:
    """Read-through config wrapper with energy-aware profile overrides."""

    def __init__(self, base_config, overrides):
        self._base_config = base_config
        self._overrides = dict(overrides)

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        if self._base_config is not None:
            return getattr(self._base_config, name)
        raise AttributeError(name)


class UAVEnergyAwareRelayEnv(UAVForcedRelayEnv):
    """
    Scenario 7: energy-aware forced-relay benchmark.

    This environment keeps the base relay communication and routing dynamics,
    then adds persistent UAV battery state, charging station contention, and
    temporary UAV failures.
    """

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "uav_energy_aware_relay_env_v0",
        "is_parallelizable": True,
    }

    VALID_STAGES = {f"S{i}" for i in range(1, 5)}

    def __init__(self, config=None, scale_mode=None, **kwargs):
        stage = kwargs.pop("energy_stage", None)
        if stage is None and config is not None:
            stage = getattr(config, "energy_stage", "S1")
        stage = str(stage or "S1").upper()
        if stage not in self.VALID_STAGES:
            raise ValueError(f"Unknown energy_stage '{stage}'. Expected one of {sorted(self.VALID_STAGES)}.")
        self.energy_stage = stage

        if scale_mode is None:
            scale_mode = kwargs.pop("scale_mode", None)
        if scale_mode is None and config is not None:
            scale_mode = getattr(config, "energy_scale_mode", "train")
        self.scale_mode = str(scale_mode or "train").lower()

        base_overrides = self._build_profile_overrides(stage, config)
        base_overrides.update(kwargs)
        base_overrides["reward_type"] = kwargs.get(
            "reward_type",
            getattr(config, "energy_reward_type", getattr(config, "reward_type", "load_balance")) if config else "load_balance",
        )

        proxy = _EnergyAwareConfigProxy(config, base_overrides)
        super().__init__(config=proxy, render_mode=kwargs.get("render_mode", None), seed=kwargs.get("seed", None))
        if self.action_space_type != "continuous":
            raise ValueError("Scenario 7 requires a continuous four-dimensional action space.")

        self.energy_stage_index = int(stage[1:]) - 1
        self.scenario7_interface_version = int(getattr(proxy, "scenario7_interface_version", 2))
        self.battery_enabled = bool(getattr(proxy, "battery_enabled", False))
        self.charging_enabled = bool(getattr(proxy, "charging_enabled", self.battery_enabled))
        self.failure_enabled = bool(getattr(proxy, "uav_failure_enabled", False))

        self.battery_capacity_wh = float(getattr(proxy, "battery_capacity_wh", 200.0))
        self.initial_battery_ratio_range = tuple(getattr(proxy, "initial_battery_ratio_range", (0.75, 1.0)))
        self.return_reserve_ratio = float(getattr(proxy, "return_reserve_ratio", 0.10))
        self.return_threshold_min = float(getattr(proxy, "return_threshold_min", 0.25))
        self.return_threshold_max = float(getattr(proxy, "return_threshold_max", 0.60))
        self.emergency_return_threshold = float(getattr(proxy, "emergency_return_threshold", 0.05))
        self.service_cutoff_threshold = float(getattr(proxy, "service_cutoff_threshold", 0.02))
        # Compatibility aliases for existing metrics and visualization code.
        self.low_battery_threshold = self.return_threshold_min
        self.critical_battery_threshold = self.emergency_return_threshold
        self.depleted_battery_threshold = 0.0

        self.max_energy_charging_stations = max(1, int(getattr(proxy, "max_energy_charging_stations", 2)))
        self.max_energy_observed_uavs = max(self.n_uavs, int(getattr(proxy, "max_observed_uavs", self.n_uavs)))
        self.n_charging_stations = int(np.clip(
            int(getattr(proxy, "n_charging_stations", self.max_energy_charging_stations)),
            1,
            self.max_energy_charging_stations,
        ))
        self.charging_radius_m = float(getattr(proxy, "charging_radius_m", 160.0))
        self.charging_capture_radius_m = float(getattr(proxy, "charging_capture_radius_m", 20.0))
        self.charging_power_w = float(getattr(proxy, "charging_power_w", 1000.0))
        self.charging_hover_speed_threshold = float(getattr(proxy, "charging_hover_speed_threshold", 1.0))
        self.docking_horizontal_speed_mps = float(getattr(proxy, "docking_horizontal_speed_mps", 3.0))
        self.docking_vertical_speed_mps = float(getattr(proxy, "docking_vertical_speed_mps", 1.0))
        self.max_vertical_speed_mps = float(getattr(proxy, "max_vertical_speed_mps", 5.0))
        self.dock_request_threshold = float(getattr(proxy, "dock_request_threshold", 0.5))
        self.limp_home_speed_mps = float(getattr(proxy, "limp_home_speed_mps", 3.0))
        self.energy_reward_delta_min = float(getattr(proxy, "energy_reward_delta_min", -0.5))
        self.energy_reward_delta_max = float(getattr(proxy, "energy_reward_delta_max", 0.25))
        self.randomize_charging_stations = bool(getattr(proxy, "randomize_charging_stations", True))
        self.charging_station_layout = str(getattr(proxy, "charging_station_layout", "service_anchored"))
        self.charging_station_margin_ratio = float(getattr(proxy, "charging_station_margin_ratio", 0.08))
        default_min_separation = max(2.0 * self.charging_radius_m, self.area_size * 0.12)
        self.charging_station_min_separation_m = float(
            getattr(proxy, "charging_station_min_separation_m", default_min_separation)
        )
        self.charging_station_jitter_m = float(getattr(proxy, "charging_station_jitter_m", self.area_size * 0.12))
        self.charging_station_capacity = self._normalize_charging_capacities(
            getattr(proxy, "charging_station_capacity", np.inf)
        )

        self.uav_failure_probability = float(getattr(proxy, "uav_failure_probability", 0.0))
        self.uav_failure_duration_range = tuple(getattr(proxy, "uav_failure_duration_range", (20, 60)))
        self.uav_failure_min_active = int(getattr(proxy, "uav_failure_min_active", max(1, self.n_uavs - 1)))

        self.w_energy_motion = float(getattr(proxy, "w_energy_motion", 0.0))
        self.w_energy_backhaul_potential = float(getattr(proxy, "w_energy_backhaul_potential", 0.20))
        self.w_energy_efficiency = float(getattr(proxy, "w_energy_efficiency", 0.0))
        self.w_low_battery = float(getattr(proxy, "w_low_battery", 0.0))
        self.w_depleted_battery = float(getattr(proxy, "w_depleted_battery", 0.0))
        self.w_charge_progress = float(getattr(proxy, "w_charge_progress", 0.0))
        self.w_charging_queue = float(getattr(proxy, "w_charging_queue", 0.0))
        self.w_station_approach = float(getattr(proxy, "w_station_approach", 0.0))
        self.w_charging_arrival = float(getattr(proxy, "w_charging_arrival", 0.0))
        self.w_energy_failure = float(getattr(proxy, "w_energy_failure", 0.0 if stage == "S1" else 0.10))
        self.w_energy_failure_event = float(getattr(proxy, "w_energy_failure_event", 0.0 if stage == "S1" else 0.20))

        self.uav_battery_ratios = np.ones(self.n_uavs, dtype=float)
        self.uav_charging = np.zeros(self.n_uavs, dtype=bool)
        self.charging_wait_steps = np.zeros(self.n_uavs, dtype=int)
        self.uav_failure_timers = np.zeros(self.n_uavs, dtype=int)
        self.uav_failed = np.zeros(self.n_uavs, dtype=bool)
        self.station_occupancy = np.zeros(self.max_energy_charging_stations, dtype=int)
        self.station_queue_lengths = np.zeros(self.max_energy_charging_stations, dtype=int)
        self.last_energy_consumed_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_motion_energy_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_energy_charged_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_min_station_distance_before = np.zeros(self.n_uavs, dtype=float)
        self.last_min_station_distance_after = np.zeros(self.n_uavs, dtype=float)
        self.last_charging_eligible = np.zeros(self.n_uavs, dtype=bool)
        self.last_charging_arrival = np.zeros(self.n_uavs, dtype=bool)
        self.uav_dock_requests = np.zeros(self.n_uavs, dtype=bool)
        self.uav_target_stations = np.full(self.n_uavs, -1, dtype=int)
        self.uav_return_threshold_ratios = np.full(self.n_uavs, self.return_threshold_min, dtype=float)
        self.uav_return_energy_margins = np.ones(self.n_uavs, dtype=float)
        self.last_actual_velocities = np.zeros((self.n_uavs, 3), dtype=float)
        self._previous_capture_mask = np.zeros(self.n_uavs, dtype=bool)
        self.last_backhaul_potential_reward = 0.0
        self.prev_energy_failure_mask = np.zeros(self.n_uavs, dtype=bool)
        self.last_energy_reward_components = {}

        self._init_charging_stations(randomize=False)
        self._extend_spaces_for_energy()

    @staticmethod
    def _build_profile_overrides(stage, config):
        overrides = {
            "reward_type": "load_balance",
            "user_distribution": "forced_relay_cluster",
            "randomize_bs": True,
            "battery_enabled": False,
            "charging_enabled": False,
            "n_charging_stations": 2,
            "max_energy_charging_stations": 2,
            "charging_station_capacity": np.inf,
            "randomize_charging_stations": True,
            "charging_station_layout": "service_anchored",
            "charging_station_margin_ratio": 0.08,
            "charging_hover_speed_threshold": 1.0,
            "charging_capture_radius_m": 20.0,
            "charging_power_w": 1000.0,
            "docking_horizontal_speed_mps": 3.0,
            "docking_vertical_speed_mps": 1.0,
            "max_vertical_speed_mps": 5.0,
            "dock_request_threshold": 0.5,
            "limp_home_speed_mps": 3.0,
            "energy_reward_delta_min": -0.5,
            "energy_reward_delta_max": 0.25,
            "w_energy_motion": 0.02,
            "w_energy_efficiency": 0.0,
            "uav_failure_enabled": False,
            "uav_failure_probability": 0.0,
            "uav_failure_duration_range": (20, 60),
            "energy_reward_type": "load_balance",
        }

        if config is not None:
            overrides.update({
                "n_agents": getattr(config, "n_agents", 8),
                "n_users": getattr(config, "n_users", 30),
                "n_ground_bs": getattr(config, "n_ground_bs", 1),
                "max_observed_uavs": max(getattr(config, "max_observed_uavs", 8), 8),
                "max_observed_users": max(getattr(config, "max_observed_users", 30), 30),
            })
        else:
            overrides.update({
                "n_agents": 8,
                "n_users": 30,
                "n_ground_bs": 1,
                "max_observed_uavs": 8,
                "max_observed_users": 30,
            })

        if stage in {"S2", "S3", "S4"}:
            overrides.update({
                "battery_enabled": True,
                "charging_enabled": True,
            })
        overrides["charging_station_capacity"] = [1, 1]
        user_speed, cluster_speed = {
            "S1": (2.0, 2.0),
            "S2": (3.0, 3.0),
            "S3": (5.0, 5.0),
            "S4": (8.0, 10.0),
        }[stage]
        overrides.update({
            "user_movement_model": "rpgm",
            "user_max_speed": user_speed,
            "cluster_migration_speed": cluster_speed,
            "cluster_pause_time_range": (0, 3) if stage == "S4" else (1, 4),
            "user_pause_time_range": (0, 2),
        })
        if stage == "S4":
            overrides.update({
                "uav_failure_enabled": True,
                "uav_failure_probability": 0.001,
                "uav_failure_duration_range": (20, 60),
            })

        return overrides

    def _normalize_charging_capacities(self, capacities):
        if np.isscalar(capacities):
            return np.full(self.max_energy_charging_stations, float(capacities), dtype=float)
        values = np.array(list(capacities), dtype=float)
        if len(values) == 0:
            values = np.array([np.inf], dtype=float)
        if len(values) < self.max_energy_charging_stations:
            values = np.pad(
                values,
                (0, self.max_energy_charging_stations - len(values)),
                constant_values=values[-1],
            )
        return values[:self.max_energy_charging_stations]

    def _init_charging_stations(self, randomize=None):
        self.charging_station_positions = np.zeros((self.max_energy_charging_stations, 3), dtype=float)
        z = float(self.height_range[0])
        if randomize is None:
            randomize = getattr(self, "randomize_charging_stations", True)

        if randomize:
            margin_ratio = float(np.clip(getattr(self, "charging_station_margin_ratio", 0.08), 0.0, 0.45))
            margin = self.area_size * margin_ratio
            low = margin
            high = self.area_size - margin
            if high <= low:
                low, high = 0.0, float(self.area_size)

            min_sep = max(0.0, float(getattr(self, "charging_station_min_separation_m", 0.0)))
            accepted = []
            for idx in range(self.max_energy_charging_stations):
                if self.charging_station_layout == "service_anchored":
                    xy = self._sample_service_anchored_station_xy(idx, accepted, low, high, min_sep)
                else:
                    xy = self._sample_charging_station_xy(accepted, low, high, min_sep)
                accepted.append(xy)
                self.charging_station_positions[idx] = [float(xy[0]), float(xy[1]), z]
            return

        if hasattr(self, "ground_bs_positions") and self.n_ground_bs > 0:
            bs_center = np.mean(self.ground_bs_positions[:, :2], axis=0)
        else:
            bs_center = np.array([self.area_size * 0.05, self.area_size * 0.05], dtype=float)

        remote = self._remote_corner_from_point(bs_center)
        anchors = [bs_center, remote]
        for idx in range(self.max_energy_charging_stations):
            if idx < len(anchors):
                xy = anchors[idx]
            else:
                t = idx / max(1, self.max_energy_charging_stations - 1)
                xy = (1.0 - t) * bs_center + t * remote
            self.charging_station_positions[idx] = [
                float(np.clip(xy[0], self.area_size * 0.05, self.area_size * 0.95)),
                float(np.clip(xy[1], self.area_size * 0.05, self.area_size * 0.95)),
                z,
            ]

    def _sample_charging_station_xy(self, accepted_points, low, high, min_sep):
        if not accepted_points or min_sep <= 0:
            return self.np_random.uniform(low, high, size=2)

        for scale in (1.0, 0.75, 0.5, 0.25, 0.0):
            effective_sep = min_sep * scale
            for _ in range(200):
                candidate = self.np_random.uniform(low, high, size=2)
                if all(np.linalg.norm(candidate - point) >= effective_sep for point in accepted_points):
                    return candidate

        return self.np_random.uniform(low, high, size=2)

    def _sample_service_anchored_station_xy(self, station_idx, accepted_points, low, high, min_sep):
        anchors = self._charging_station_anchor_points()
        anchor = anchors[min(station_idx, len(anchors) - 1)]
        jitter = max(0.0, float(getattr(self, "charging_station_jitter_m", self.area_size * 0.12)))

        for scale in (1.0, 0.75, 0.5, 0.25, 0.0):
            effective_sep = min_sep * scale
            for _ in range(120):
                offset = self.np_random.uniform(-jitter, jitter, size=2) if jitter > 0 else np.zeros(2)
                candidate = np.clip(anchor + offset, low, high)
                if all(np.linalg.norm(candidate - point) >= effective_sep for point in accepted_points):
                    return candidate

        return self._sample_charging_station_xy(accepted_points, low, high, min_sep)

    def _charging_station_anchor_points(self):
        if hasattr(self, "ground_bs_positions") and self.n_ground_bs > 0:
            bs_center = np.mean(self.ground_bs_positions[:, :2], axis=0)
        else:
            bs_center = np.array([self.area_size * 0.10, self.area_size * 0.10], dtype=float)

        if hasattr(self, "user_positions") and len(self.user_positions) > 0:
            service_center = np.mean(self.user_positions[:, :2], axis=0)
        else:
            service_center = self._remote_corner_from_point(bs_center)

        relay_anchor = 0.70 * bs_center + 0.30 * service_center
        anchors = [relay_anchor, service_center]
        for idx in range(2, self.max_energy_charging_stations):
            t = idx / max(1, self.max_energy_charging_stations - 1)
            anchors.append((1.0 - t) * relay_anchor + t * service_center)
        return anchors

    def _remote_corner_from_point(self, point):
        area_center = self.area_size / 2.0
        x = self.area_size * (0.92 if point[0] < area_center else 0.08)
        y = self.area_size * (0.92 if point[1] < area_center else 0.08)
        return np.array([x, y], dtype=float)

    def _extend_spaces_for_energy(self):
        self.action_dim = 4
        self.action_spaces = {
            agent: Box(low=-1.0, high=1.0, shape=(self.action_dim,), dtype=np.float32)
            for agent in self.possible_agents
        }

        self.energy_uav_obs_dim = 13
        self.energy_station_obs_dim = 8
        self.energy_obs_extra_dim = (
            self.max_energy_observed_uavs * self.energy_uav_obs_dim
            + self.max_energy_charging_stations * self.energy_station_obs_dim
        )
        self.obs_dim = int(self.obs_dim + self.energy_obs_extra_dim)

        self.energy_uav_state_dim = 9
        self.energy_station_state_dim = 7
        self.energy_state_extra_dim = (
            self.n_uavs * self.energy_uav_state_dim
            + self.max_energy_charging_stations * self.energy_station_state_dim
            + 4
        )
        self.state_dim = int(self.state_dim + self.energy_state_extra_dim)

        self.observation_spaces = {
            agent: Dict({
                "obs": Box(low=-float("inf"), high=float("inf"), shape=(self.obs_dim,), dtype=np.float32),
                "action_mask": Box(low=0, high=1, shape=(self.action_dim,), dtype=np.float32),
            })
            for agent in self.possible_agents
        }

    def reset(self, seed=None, options=None):
        observations, infos = super().reset(seed=seed, options=options)
        self._init_charging_stations()
        self._reset_energy_state()

        observations = {agent: self._get_observation(agent) for agent in self.agents}
        observations = self._update_observations_dict(observations)

        current_state = self._get_state()
        self.state = current_state
        for agent in self.agents:
            infos[agent]["state"] = current_state.copy()
            infos[agent]["energy_stage"] = self.energy_stage
            infos[agent]["scale_mode"] = self.scale_mode
            infos[agent]["reward_info"] = self._energy_metrics_dict()
        return observations, infos

    def _reset_energy_state(self):
        if self.battery_enabled:
            low, high = self.initial_battery_ratio_range
            self.uav_battery_ratios = self.np_random.uniform(low, high, size=self.n_uavs).astype(float)
            self.uav_battery_ratios = np.clip(self.uav_battery_ratios, 0.0, 1.0)
        else:
            self.uav_battery_ratios = np.ones(self.n_uavs, dtype=float)

        self.uav_charging = np.zeros(self.n_uavs, dtype=bool)
        self.charging_wait_steps = np.zeros(self.n_uavs, dtype=int)
        self.uav_failure_timers = np.zeros(self.n_uavs, dtype=int)
        self.uav_failed = np.zeros(self.n_uavs, dtype=bool)
        self.station_occupancy = np.zeros(self.max_energy_charging_stations, dtype=int)
        self.station_queue_lengths = np.zeros(self.max_energy_charging_stations, dtype=int)
        self.last_energy_consumed_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_motion_energy_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_energy_charged_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_min_station_distance_before = self._min_distances_to_charging_stations(self.uav_positions)
        self.last_min_station_distance_after = self.last_min_station_distance_before.copy()
        self.last_charging_eligible = np.zeros(self.n_uavs, dtype=bool)
        self.last_charging_arrival = np.zeros(self.n_uavs, dtype=bool)
        self.uav_dock_requests = np.zeros(self.n_uavs, dtype=bool)
        self.uav_target_stations = np.full(self.n_uavs, -1, dtype=int)
        self.last_actual_velocities = np.zeros((self.n_uavs, 3), dtype=float)
        self._previous_capture_mask = np.zeros(self.n_uavs, dtype=bool)
        self._update_return_energy_state()
        self.prev_energy_failure_mask = self._energy_failure_mask()
        self.last_energy_reward_components = self._calculate_energy_reward_components()

    def step(self, actions):
        self._update_uav_failures()
        self._update_return_energy_state()

        pre_positions = self.uav_positions.copy()
        backhaul_potential_before = self._backhaul_potential()
        adjusted_actions, commanded_velocities = self._prepare_energy_actions(actions)

        observations, rewards, terminations, truncations, infos = super().step(adjusted_actions)
        base_load_balance_reward = float(np.mean(list(rewards.values()))) if rewards else 0.0
        backhaul_potential_after = self._backhaul_potential()
        self.last_backhaul_potential_reward = float(np.clip(
            backhaul_potential_after - backhaul_potential_before,
            -1.0,
            1.0,
        ))

        self._apply_energy_dynamics(pre_positions, commanded_velocities)
        self._update_return_energy_state()
        components = self._calculate_energy_reward_components()
        self.last_energy_reward_components = components

        energy_management_delta_raw = self._energy_management_delta_raw(components)
        energy_efficiency_reward_delta = self._energy_efficiency_reward_delta(components, base_load_balance_reward)
        reward_delta_raw = self._energy_reward_delta_raw(components, base_load_balance_reward)
        reward_delta = self._clip_energy_reward_delta(reward_delta_raw)
        for agent in rewards:
            rewards[agent] = float(rewards[agent] + reward_delta)
        self.prev_energy_failure_mask = self._energy_failure_mask()

        all_exhausted = bool(
            self.battery_enabled
            and np.all(self.uav_battery_ratios <= 0.0)
            and not np.any(self.uav_charging)
        )
        if all_exhausted:
            terminations = {agent: True for agent in self.agents}
            truncations = {agent: False for agent in self.agents}

        observations = {agent: self._get_observation(agent) for agent in self.agents}
        observations = self._update_observations_dict(observations)
        next_state = self._get_state()
        self.state = next_state

        metrics = self._energy_metrics_dict()
        metrics.update(components)
        metrics["base_load_balance_reward"] = base_load_balance_reward
        metrics["energy_management_delta_raw"] = energy_management_delta_raw
        metrics["energy_efficiency_reward_delta"] = energy_efficiency_reward_delta
        metrics["energy_reward_delta_raw"] = reward_delta_raw
        metrics["energy_reward_delta_clipped"] = reward_delta
        metrics["energy_reward_delta"] = reward_delta

        for agent in self.agents:
            if agent not in infos:
                infos[agent] = {}
            reward_info = infos[agent].setdefault("reward_info", {})
            reward_info.update(metrics)
            reward_info["connections"] = self.connections.copy()
            reward_info["routing_paths"] = copy.deepcopy(self.routing_paths)
            infos[agent]["next_state"] = next_state.copy()
            infos[agent]["energy_stage"] = self.energy_stage
            infos[agent]["scale_mode"] = self.scale_mode

        return observations, rewards, terminations, truncations, infos

    def _update_uav_failures(self):
        if not self.failure_enabled:
            self.uav_failure_timers[:] = 0
            self.uav_failed[:] = False
            return

        for uav_idx in range(self.n_uavs):
            if self.uav_failure_timers[uav_idx] > 0:
                self.uav_failure_timers[uav_idx] -= 1

        self.uav_failed = self.uav_failure_timers > 0
        active_count = int(np.sum(~self.uav_failed))
        low, high = self.uav_failure_duration_range
        low = max(1, int(low))
        high = max(low, int(high))

        for uav_idx in range(self.n_uavs):
            if self.uav_failed[uav_idx]:
                continue
            if active_count <= self.uav_failure_min_active:
                break
            if self.np_random.random_sample() < self.uav_failure_probability:
                self.uav_failure_timers[uav_idx] = int(self.np_random.randint(low, high + 1))
                self.uav_failed[uav_idx] = True
                active_count -= 1

    def _prepare_energy_actions(self, actions):
        adjusted = {}
        commanded_velocities = np.zeros((self.n_uavs, 3), dtype=float)
        self.uav_dock_requests[:] = False
        self.uav_target_stations[:] = -1

        for agent_idx, agent in enumerate(self.agents):
            action = self._normalize_continuous_action(
                actions.get(agent, np.zeros(self.action_dim, dtype=np.float32))
            )
            requested_by_policy = bool(action[3] > self.dock_request_threshold)
            if self._is_uav_motion_disabled(agent_idx):
                desired_velocity = np.zeros(3, dtype=float)
                station_idx, _, distance = self._nearest_charging_station(agent_idx)
                if requested_by_policy and station_idx >= 0 and distance <= self.charging_capture_radius_m:
                    self.uav_dock_requests[agent_idx] = True
                    self.uav_target_stations[agent_idx] = station_idx
            elif self._is_uav_in_limp_home(agent_idx):
                station_idx, _, _ = self._nearest_charging_station(agent_idx)
                self.uav_dock_requests[agent_idx] = station_idx >= 0
                self.uav_target_stations[agent_idx] = station_idx
                desired_velocity = self._limp_home_velocity(agent_idx)
            else:
                desired_velocity = self._movement_velocity_from_action(action[:3])
                if requested_by_policy:
                    station_idx, target_vector, distance = self._nearest_charging_station(agent_idx)
                    self.uav_dock_requests[agent_idx] = station_idx >= 0
                    self.uav_target_stations[agent_idx] = station_idx
                    if station_idx >= 0 and distance <= self.charging_radius_m:
                        desired_velocity = self._docking_velocity(target_vector, distance)

            commanded_velocities[agent_idx] = desired_velocity
            adjusted[agent] = self._base_action_from_velocity(desired_velocity)

        return adjusted, commanded_velocities

    def _normalize_continuous_action(self, action):
        action_vec = np.asarray(action, dtype=np.float32)
        if action_vec.shape != (self.action_dim,):
            return np.zeros(self.action_dim, dtype=np.float32)
        return np.clip(action_vec, -1.0, 1.0).astype(np.float32)

    def _is_uav_motion_disabled(self, uav_idx):
        if bool(getattr(self, "uav_failed", np.zeros(self.n_uavs, dtype=bool))[uav_idx]):
            return True
        if not getattr(self, "battery_enabled", False):
            return False
        battery = getattr(self, "uav_battery_ratios", np.ones(self.n_uavs, dtype=float))[uav_idx]
        return bool(battery <= 0.0)

    def _is_uav_in_limp_home(self, uav_idx):
        if not getattr(self, "battery_enabled", False):
            return False
        battery = getattr(self, "uav_battery_ratios", np.ones(self.n_uavs, dtype=float))[uav_idx]
        return bool(0.0 < battery <= self.emergency_return_threshold)

    def _limp_home_action(self, uav_idx):
        return self._base_action_from_velocity(self._limp_home_velocity(uav_idx))

    def _limp_home_velocity(self, uav_idx):
        _, target_vector, distance = self._nearest_charging_station(uav_idx)
        if distance <= self.charging_capture_radius_m:
            return np.zeros(3, dtype=float)
        if distance <= self.charging_radius_m:
            return self._docking_velocity(target_vector, distance)
        speed = min(max(self.limp_home_speed_mps, 0.0), max(self.max_speed, 1e-8))
        if distance <= 1e-8:
            return np.zeros(3, dtype=float)
        speed = min(speed, distance / max(float(self.time_step), 1e-8))
        return target_vector / distance * speed

    def _movement_velocity_from_action(self, movement_action):
        movement = np.asarray(movement_action, dtype=float)
        if movement.shape != (3,):
            return np.zeros(3, dtype=float)
        horizontal = movement[:2]
        horizontal_norm = float(np.linalg.norm(horizontal))
        if horizontal_norm > 1e-8:
            horizontal_speed = min(horizontal_norm, 1.0) * self.max_speed
            horizontal_velocity = horizontal / horizontal_norm * horizontal_speed
        else:
            horizontal_velocity = np.zeros(2, dtype=float)
        return np.array([
            horizontal_velocity[0],
            horizontal_velocity[1],
            float(np.clip(movement[2], -1.0, 1.0)) * self.max_vertical_speed_mps,
        ], dtype=float)

    def _docking_velocity(self, target_vector, distance):
        if distance <= self.charging_capture_radius_m:
            return np.zeros(3, dtype=float)
        dt = max(float(self.time_step), 1e-8)
        horizontal = np.asarray(target_vector[:2], dtype=float)
        horizontal_distance = float(np.linalg.norm(horizontal))
        if horizontal_distance > 1e-8:
            horizontal_speed = min(self.docking_horizontal_speed_mps, horizontal_distance / dt)
            horizontal_velocity = horizontal / horizontal_distance * horizontal_speed
        else:
            horizontal_velocity = np.zeros(2, dtype=float)
        vertical_velocity = float(np.clip(
            target_vector[2] / dt,
            -self.docking_vertical_speed_mps,
            self.docking_vertical_speed_mps,
        ))
        return np.array([horizontal_velocity[0], horizontal_velocity[1], vertical_velocity], dtype=float)

    def _base_action_from_velocity(self, velocity):
        return np.clip(
            np.asarray(velocity, dtype=float) / max(self.max_speed, 1e-8),
            -1.0,
            1.0,
        ).astype(np.float32)

    def _nearest_discrete_limp_action(self, target_vector):
        if np.linalg.norm(target_vector) <= 1e-8:
            return 0
        best_action = 0
        best_score = -np.inf
        for action_id, velocity in self.action_to_velocity.items():
            score = float(np.dot(np.asarray(velocity, dtype=float), target_vector))
            if score > best_score:
                best_score = score
                best_action = int(action_id)
        return best_action

    def _nearest_charging_station_vector(self, uav_idx):
        _, vector, distance = self._nearest_charging_station(uav_idx)
        return vector, distance

    def _nearest_charging_station(self, uav_idx):
        if self.n_charging_stations <= 0:
            return -1, np.zeros(3, dtype=float), 0.0
        rel = self.charging_station_positions[:self.n_charging_stations] - self.uav_positions[uav_idx]
        distances = np.linalg.norm(rel, axis=1)
        nearest = int(np.argmin(distances))
        return nearest, rel[nearest], float(distances[nearest])

    def _velocity_from_action(self, action):
        action_vec = np.asarray(action, dtype=float)
        if action_vec.shape == (self.action_dim,):
            return self._movement_velocity_from_action(action_vec[:3])
        if action_vec.shape == (3,):
            return action_vec * self.max_speed
        return np.zeros(3, dtype=float)

    def _apply_energy_dynamics(self, pre_positions, commanded_velocities):
        self.last_energy_consumed_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_energy_charged_wh = np.zeros(self.n_uavs, dtype=float)
        self.uav_charging[:] = False
        self.station_occupancy[:] = 0
        self.station_queue_lengths[:] = 0
        self.last_motion_energy_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_min_station_distance_before = self._min_distances_to_charging_stations(pre_positions)
        self.last_min_station_distance_after = self._min_distances_to_charging_stations(self.uav_positions)
        self.last_charging_eligible = np.zeros(self.n_uavs, dtype=bool)
        dt = max(float(self.time_step), 1e-8)
        self.last_actual_velocities = (self.uav_positions - pre_positions) / dt

        if not self.battery_enabled:
            self.uav_battery_ratios[:] = 1.0
            self.charging_wait_steps[:] = 0
            return

        for uav_idx in range(self.n_uavs):
            actual_velocity = self.last_actual_velocities[uav_idx]
            v_xy = np.linalg.norm(actual_velocity[:2])
            v_z = actual_velocity[2]
            power_watts = self._calculate_power_consumption(v_xy, v_z)
            consumed_wh = power_watts * dt / 3600.0
            motion_power_watts = max(0.0, power_watts - (self.P0 + self.Pi))
            self.last_energy_consumed_wh[uav_idx] = consumed_wh
            self.last_motion_energy_wh[uav_idx] = motion_power_watts * dt / 3600.0
            self.uav_battery_ratios[uav_idx] -= consumed_wh / max(self.battery_capacity_wh, 1e-8)

        eligible_by_station = self._charging_candidates_by_station(self.last_actual_velocities)
        for candidates in eligible_by_station.values():
            self.last_charging_eligible[candidates] = True
        selected_by_station = self._select_charging_uavs(eligible_by_station)
        selected_uavs = set()
        for station_idx, selected in selected_by_station.items():
            selected_uavs.update(selected)
            self.station_occupancy[station_idx] = len(selected)
            self.station_queue_lengths[station_idx] = max(0, len(eligible_by_station.get(station_idx, [])) - len(selected))

        charge_wh = max(0.0, self.charging_power_w) * dt / 3600.0
        for uav_idx in range(self.n_uavs):
            if uav_idx in selected_uavs:
                missing_wh = max(0.0, 1.0 - self.uav_battery_ratios[uav_idx]) * self.battery_capacity_wh
                actual_charge_wh = min(charge_wh, missing_wh)
                self.last_energy_charged_wh[uav_idx] = actual_charge_wh
                self.uav_battery_ratios[uav_idx] += actual_charge_wh / max(self.battery_capacity_wh, 1e-8)
                self.uav_charging[uav_idx] = actual_charge_wh > 0.0
                self.charging_wait_steps[uav_idx] = 0
            elif any(uav_idx in candidates for candidates in eligible_by_station.values()):
                self.charging_wait_steps[uav_idx] += 1
            else:
                self.charging_wait_steps[uav_idx] = 0

        self.uav_battery_ratios = np.clip(self.uav_battery_ratios, 0.0, 1.0)

        capture_mask = self.last_charging_eligible.copy()
        self.last_charging_arrival = capture_mask & ~self._previous_capture_mask
        self._previous_capture_mask = capture_mask

    def _min_distances_to_charging_stations(self, positions):
        if not hasattr(self, "charging_station_positions") or self.n_charging_stations <= 0:
            return np.zeros(self.n_uavs, dtype=float)
        active_stations = self.charging_station_positions[:self.n_charging_stations]
        distances = np.linalg.norm(positions[:, np.newaxis, :] - active_stations[np.newaxis, :, :], axis=2)
        return np.min(distances, axis=1)

    def _charging_candidates_by_station(self, actual_velocities):
        eligible_by_station = {idx: [] for idx in range(self.n_charging_stations)}
        if not self.charging_enabled:
            return eligible_by_station

        for uav_idx in range(self.n_uavs):
            if self.uav_failed[uav_idx]:
                continue
            if not self.uav_dock_requests[uav_idx]:
                continue
            if np.linalg.norm(actual_velocities[uav_idx]) > self.charging_hover_speed_threshold:
                continue
            station_idx = int(self.uav_target_stations[uav_idx])
            if station_idx < 0 or station_idx >= self.n_charging_stations:
                continue
            distance = np.linalg.norm(
                self.charging_station_positions[station_idx] - self.uav_positions[uav_idx]
            )
            if distance <= self.charging_capture_radius_m:
                eligible_by_station[station_idx].append(uav_idx)

        return eligible_by_station

    def _select_charging_uavs(self, eligible_by_station):
        selected_by_station = {}
        for station_idx, candidates in eligible_by_station.items():
            if not candidates:
                selected_by_station[station_idx] = []
                continue

            cap = self.charging_station_capacity[station_idx]
            if np.isinf(cap):
                selected_by_station[station_idx] = list(candidates)
                continue

            slots = max(0, int(cap))
            ordered = sorted(
                candidates,
                key=lambda idx: (
                    self.uav_battery_ratios[idx],
                    -self.charging_wait_steps[idx],
                    idx,
                ),
            )
            selected_by_station[station_idx] = ordered[:slots]

        return selected_by_station

    def _update_return_energy_state(self):
        if not self.battery_enabled:
            self.uav_return_threshold_ratios = np.full(
                self.n_uavs, self.return_threshold_min, dtype=float
            )
            self.uav_return_energy_margins = np.ones(self.n_uavs, dtype=float)
            return

        return_power_w = self._calculate_power_consumption(self.limp_home_speed_mps, 0.0)
        thresholds = np.zeros(self.n_uavs, dtype=float)
        for uav_idx in range(self.n_uavs):
            _, _, distance = self._nearest_charging_station(uav_idx)
            return_seconds = distance / max(self.limp_home_speed_mps, 1e-8)
            required_wh = return_seconds * return_power_w / 3600.0
            required_ratio = required_wh / max(self.battery_capacity_wh, 1e-8)
            thresholds[uav_idx] = np.clip(
                required_ratio + self.return_reserve_ratio,
                self.return_threshold_min,
                self.return_threshold_max,
            )
        self.uav_return_threshold_ratios = thresholds
        self.uav_return_energy_margins = self.uav_battery_ratios - thresholds

    def _backhaul_potential(self):
        if self.n_uavs <= 0:
            return 0.0
        map_diag = max(self.area_size * np.sqrt(2.0), 1e-8)
        scores = np.zeros(self.n_uavs, dtype=float)
        connected_indices = set(getattr(self, "routing_paths", {}).keys())
        for uav_idx in range(self.n_uavs):
            if uav_idx in connected_indices:
                scores[uav_idx] = 1.0
                continue
            candidates = []
            if self.n_ground_bs > 0:
                candidates.extend(np.linalg.norm(
                    self.ground_bs_positions - self.uav_positions[uav_idx],
                    axis=1,
                ).tolist())
            if connected_indices:
                connected_positions = self.uav_positions[sorted(connected_indices)]
                candidates.extend(np.linalg.norm(
                    connected_positions - self.uav_positions[uav_idx],
                    axis=1,
                ).tolist())
            nearest = min(candidates) if candidates else map_diag
            scores[uav_idx] = 1.0 - np.clip(nearest / map_diag, 0.0, 1.0)
        return float(np.mean(scores))

    def _energy_failure_mask(self):
        if not self.battery_enabled:
            return np.zeros(self.n_uavs, dtype=bool)
        return self.uav_battery_ratios <= self.service_cutoff_threshold

    def _calculate_energy_reward_components(self):
        if not self.battery_enabled:
            return {
                "energy_penalty": 0.0,
                "energy_step_consumed_wh": 0.0,
                "energy_runtime_before_charge_steps": 0.0,
                "energy_runtime_ratio": 0.0,
                "energy_efficiency_score": 0.0,
                "energy_efficiency_amplifier": 1.0,
                "backhaul_potential_reward": self.last_backhaul_potential_reward,
                "low_battery_distance_penalty": 0.0,
                "depleted_battery_penalty": 0.0,
                "energy_failure_penalty": 0.0,
                "energy_failure_event_penalty": 0.0,
                "charge_progress_reward": 0.0,
                "charging_queue_penalty": 0.0,
                "station_approach_reward": 0.0,
                "charging_arrival_reward": 0.0,
            }

        physical_max_power = self._calculate_power_consumption(self.max_speed, self.max_vertical_speed_mps)
        max_step_wh = max(0.0, physical_max_power - (self.P0 + self.Pi)) * max(float(self.time_step), 1e-8) / 3600.0
        denom = max(self.n_uavs * max_step_wh, 1e-8)
        energy_penalty = float(np.clip(np.sum(self.last_motion_energy_wh) / denom, 0.0, 2.0))
        runtime_metrics = self._calculate_energy_runtime_metrics()

        low_mask = self.uav_battery_ratios <= self.uav_return_threshold_ratios
        if np.any(low_mask):
            risk = (
                self.uav_return_threshold_ratios[low_mask] - self.uav_battery_ratios[low_mask]
            ) / np.maximum(self.uav_return_threshold_ratios[low_mask], 1e-8)
            low_distance_penalty = float(np.clip(np.mean(risk), 0.0, 1.0))
        else:
            low_distance_penalty = 0.0

        depleted_penalty = float(np.mean(self.uav_battery_ratios <= 0.0))
        energy_failure_mask = self._energy_failure_mask()
        previous_failure_mask = getattr(self, "prev_energy_failure_mask", np.zeros(self.n_uavs, dtype=bool))
        energy_failure_penalty = float(np.mean(energy_failure_mask))
        energy_failure_event_penalty = float(np.mean(energy_failure_mask & ~previous_failure_mask))

        finite_capacities = self.charging_station_capacity[:self.n_charging_stations]
        available_slots = sum(
            self.n_uavs if np.isinf(capacity) else max(0, int(capacity))
            for capacity in finite_capacities
        )
        available_slots = min(self.n_uavs, available_slots)
        max_charge_wh = max(
            available_slots * max(self.charging_power_w, 0.0) * max(float(self.time_step), 1e-8) / 3600.0,
            1e-8,
        )
        charge_progress = float(np.clip(np.sum(self.last_energy_charged_wh) / max_charge_wh, 0.0, 1.0))
        queue_penalty = float(np.sum(self.station_queue_lengths) / max(self.n_uavs, 1))

        approach_mask = low_mask & self.uav_dock_requests
        if np.any(approach_mask):
            map_diag = max(self.area_size * np.sqrt(2.0), 1e-8)
            distance_improvement = (
                self.last_min_station_distance_before[approach_mask] -
                self.last_min_station_distance_after[approach_mask]
            ) / map_diag
            station_approach_reward = float(np.clip(np.mean(distance_improvement), -1.0, 1.0))
            charging_arrival_reward = float(np.sum(self.last_charging_arrival) / max(self.n_uavs, 1))
        else:
            station_approach_reward = 0.0
            charging_arrival_reward = 0.0

        return {
            "energy_penalty": energy_penalty,
            **runtime_metrics,
            "backhaul_potential_reward": self.last_backhaul_potential_reward,
            "low_battery_distance_penalty": low_distance_penalty,
            "depleted_battery_penalty": depleted_penalty,
            "energy_failure_penalty": energy_failure_penalty,
            "energy_failure_event_penalty": energy_failure_event_penalty,
            "charge_progress_reward": charge_progress,
            "charging_queue_penalty": queue_penalty,
            "station_approach_reward": station_approach_reward,
            "charging_arrival_reward": charging_arrival_reward,
        }

    def _calculate_energy_runtime_metrics(self):
        if not self.battery_enabled:
            return {
                "energy_step_consumed_wh": 0.0,
                "energy_runtime_before_charge_steps": 0.0,
                "energy_runtime_ratio": 0.0,
                "energy_efficiency_score": 0.0,
                "energy_efficiency_amplifier": 1.0,
            }

        dt = max(float(self.time_step), 1e-8)
        hover_step_wh = max((self.P0 + self.Pi) * dt / 3600.0, 1e-8)
        physical_max_power = self._calculate_power_consumption(self.max_speed, self.max_vertical_speed_mps)
        max_step_wh = max(physical_max_power * dt / 3600.0, hover_step_wh + 1e-8)
        active_mask = ~self.uav_failed & ~self._energy_failure_mask()

        if np.any(active_mask):
            consumed = np.maximum(self.last_energy_consumed_wh[active_mask], hover_step_wh)
            step_consumed_wh = float(np.mean(consumed))
        else:
            step_consumed_wh = max_step_wh

        usable_capacity_wh = self.battery_capacity_wh * max(0.0, 1.0 - self.low_battery_threshold)
        runtime_steps = usable_capacity_wh / max(step_consumed_wh, 1e-8)
        best_runtime_steps = usable_capacity_wh / hover_step_wh
        worst_runtime_steps = usable_capacity_wh / max_step_wh
        denom = max(best_runtime_steps - worst_runtime_steps, 1e-8)
        runtime_ratio = float(np.clip((runtime_steps - worst_runtime_steps) / denom, 0.0, 1.0))
        amplifier = 1.0 + max(0.0, self.w_energy_efficiency) * runtime_ratio

        return {
            "energy_step_consumed_wh": step_consumed_wh,
            "energy_runtime_before_charge_steps": float(runtime_steps),
            "energy_runtime_ratio": runtime_ratio,
            "energy_efficiency_score": runtime_ratio,
            "energy_efficiency_amplifier": float(amplifier),
        }

    def _energy_management_delta_raw(self, components):
        return float(
            self.w_energy_backhaul_potential * components.get("backhaul_potential_reward", 0.0)
            - self.w_energy_motion * components.get("energy_penalty", 0.0)
            - self.w_low_battery * components.get("low_battery_distance_penalty", 0.0)
            - self.w_depleted_battery * components.get("depleted_battery_penalty", 0.0)
            - self.w_energy_failure * components.get("energy_failure_penalty", 0.0)
            - self.w_energy_failure_event * components.get("energy_failure_event_penalty", 0.0)
            + self.w_charge_progress * components.get("charge_progress_reward", 0.0)
            + self.w_station_approach * components.get("station_approach_reward", 0.0)
            + self.w_charging_arrival * components.get("charging_arrival_reward", 0.0)
            - self.w_charging_queue * components.get("charging_queue_penalty", 0.0)
        )

    def _energy_efficiency_reward_delta(self, components, base_load_balance_reward):
        amplifier = components.get("energy_efficiency_amplifier", 1.0)
        return float(max(0.0, base_load_balance_reward) * max(0.0, amplifier - 1.0))

    def _energy_reward_delta_raw(self, components, base_load_balance_reward=0.0):
        return float(
            self._energy_management_delta_raw(components) +
            self._energy_efficiency_reward_delta(components, base_load_balance_reward)
        )

    def _clip_energy_reward_delta(self, reward_delta):
        low = min(self.energy_reward_delta_min, self.energy_reward_delta_max)
        high = max(self.energy_reward_delta_min, self.energy_reward_delta_max)
        return float(np.clip(reward_delta, low, high))

    def _energy_reward_delta(self, components):
        return self._clip_energy_reward_delta(self._energy_reward_delta_raw(components))

    def _energy_metrics_dict(self):
        low_count = int(np.sum(
            self.uav_battery_ratios <= self.uav_return_threshold_ratios
        )) if self.battery_enabled else 0
        depleted_count = int(np.sum(self.uav_battery_ratios <= 0.0)) if self.battery_enabled else 0
        energy_failure_count = int(np.sum(self._energy_failure_mask())) if self.battery_enabled else 0
        return {
            "energy_stage": self.energy_stage,
            "scale_mode": self.scale_mode,
            "battery_enabled": self.battery_enabled,
            "battery_mean_ratio": float(np.mean(self.uav_battery_ratios)) if self.n_uavs > 0 else 1.0,
            "battery_min_ratio": float(np.min(self.uav_battery_ratios)) if self.n_uavs > 0 else 1.0,
            "low_battery_uav_count": low_count,
            "energy_failure_uav_count": energy_failure_count,
            "critical_battery_uav_count": energy_failure_count,
            "depleted_uav_count": depleted_count,
            "charging_uav_count": int(np.sum(self.uav_charging)),
            "charging_queue_len": int(np.sum(self.station_queue_lengths)),
            "uav_failed_count": int(np.sum(self.uav_failed)),
            "n_charging_stations": int(self.n_charging_stations),
            "max_energy_charging_stations": int(self.max_energy_charging_stations),
            "charging_station_capacity": self.charging_station_capacity.copy(),
            "charging_radius_m": float(self.charging_radius_m),
            "charging_capture_radius_m": float(self.charging_capture_radius_m),
            "charging_power_w": float(self.charging_power_w),
            "charging_hover_speed_threshold": float(self.charging_hover_speed_threshold),
            "max_vertical_speed_mps": float(self.max_vertical_speed_mps),
            "limp_home_speed_mps": float(self.limp_home_speed_mps),
            "energy_reward_delta_min": float(self.energy_reward_delta_min),
            "energy_reward_delta_max": float(self.energy_reward_delta_max),
            "randomize_charging_stations": bool(self.randomize_charging_stations),
            "charging_station_layout": self.charging_station_layout,
            "uav_battery_ratios": self.uav_battery_ratios.copy(),
            "uav_charging": self.uav_charging.copy(),
            "uav_failed": self.uav_failed.copy(),
            "uav_dock_requests": self.uav_dock_requests.copy(),
            "uav_target_stations": self.uav_target_stations.copy(),
            "uav_return_threshold_ratios": self.uav_return_threshold_ratios.copy(),
            "uav_return_energy_margins": self.uav_return_energy_margins.copy(),
            "charging_station_positions": self.charging_station_positions.copy(),
            "charging_station_occupancy": self.station_occupancy.copy(),
            "charging_station_queue_lengths": self.station_queue_lengths.copy(),
        }

    def _is_uav_unavailable(self, uav_idx):
        failed = bool(getattr(self, "uav_failed", np.zeros(self.n_uavs, dtype=bool))[uav_idx])
        if failed:
            return True
        if not getattr(self, "battery_enabled", False):
            return False
        battery = getattr(self, "uav_battery_ratios", np.ones(self.n_uavs, dtype=float))[uav_idx]
        return bool(battery <= self.service_cutoff_threshold)

    def _apply_backhaul_action_guard(self, uav_idx, velocity):
        # An explicit dock/return request is a deliberate topology transition.
        # Blocking it indefinitely makes charging unreachable for serving relays.
        dock_requests = getattr(self, "uav_dock_requests", np.zeros(self.n_uavs, dtype=bool))
        target_stations = getattr(self, "uav_target_stations", np.full(self.n_uavs, -1, dtype=int))
        station_idx = int(target_stations[uav_idx])
        if bool(dock_requests[uav_idx]) and 0 <= station_idx < self.n_charging_stations:
            target_vector = self.charging_station_positions[station_idx] - self.uav_positions[uav_idx]
            if np.dot(np.asarray(velocity, dtype=float), target_vector) >= 0.0:
                return velocity
        return super()._apply_backhaul_action_guard(uav_idx, velocity)

    def _compute_sinr(self, uav_idx, user_idx):
        if self._is_uav_unavailable(uav_idx):
            return -np.inf
        return super()._compute_sinr(uav_idx, user_idx)

    def _compute_uav_to_uav_sinr(self, sender_idx, receiver_idx):
        if self._is_uav_unavailable(sender_idx) or self._is_uav_unavailable(receiver_idx):
            return -np.inf
        return super()._compute_uav_to_uav_sinr(sender_idx, receiver_idx)

    def _get_link_capacity(self, node1_type, node1_idx, node2_type, node2_idx):
        if node1_type == "uav" and self._is_uav_unavailable(node1_idx):
            return 0
        if node2_type == "uav" and self._is_uav_unavailable(node2_idx):
            return 0
        return super()._get_link_capacity(node1_type, node1_idx, node2_type, node2_idx)

    def _update_uav_connections(self):
        super()._update_uav_connections()
        unavailable = [idx for idx in range(self.n_uavs) if self._is_uav_unavailable(idx)]
        for uav_idx in unavailable:
            self.uav_connections[uav_idx, :] = False
            self.uav_connections[:, uav_idx] = False
            self.uav_bs_connections[uav_idx, :] = False

    def _get_observation(self, agent):
        observation = super()._get_observation(agent)
        obs = observation["obs"].copy()
        agent_idx = int(agent.split("_")[1])
        energy_obs = self._energy_observation(agent_idx)
        observation["obs"] = np.concatenate([obs, energy_obs]).astype(np.float32)
        observation["action_mask"] = np.ones(self.action_dim, dtype=np.float32)
        return observation

    def _energy_observation(self, agent_idx):
        uav_obs = np.zeros(
            self.max_energy_observed_uavs * self.energy_uav_obs_dim,
            dtype=float,
        )
        own_pos = self.uav_positions[agent_idx]
        height_span = max(float(self.height_range[1] - self.height_range[0]), 1.0)
        for uav_idx in range(min(self.n_uavs, self.max_energy_observed_uavs)):
            rel = self.uav_positions[uav_idx] - own_pos
            rel_normalized = np.array([
                rel[0] / max(self.area_size, 1.0),
                rel[1] / max(self.area_size, 1.0),
                rel[2] / height_span,
            ])
            target = self.uav_target_stations[uav_idx]
            target_normalized = (
                -1.0 if target < 0
                else target / max(self.max_energy_charging_stations - 1, 1)
            )
            load = float(np.sum(self.connections[uav_idx])) / max(self.n_users, 1)
            waiting = self.charging_wait_steps[uav_idx] / max(getattr(self, "max_steps", 1), 1)
            returning = self._is_uav_in_limp_home(uav_idx) or self.uav_dock_requests[uav_idx]
            record = np.array([
                *rel_normalized,
                self.uav_battery_ratios[uav_idx] if self.battery_enabled else 1.0,
                float(self.uav_charging[uav_idx]),
                float(not self._is_uav_unavailable(uav_idx)),
                float(returning),
                load,
                float(self.uav_dock_requests[uav_idx]),
                target_normalized,
                waiting,
                self.uav_return_threshold_ratios[uav_idx],
                self.uav_return_energy_margins[uav_idx],
            ])
            start = uav_idx * self.energy_uav_obs_dim
            uav_obs[start:start + self.energy_uav_obs_dim] = record

        station_obs = np.zeros(
            self.max_energy_charging_stations * self.energy_station_obs_dim,
            dtype=float,
        )
        map_diag_3d = max(
            np.sqrt(2.0 * self.area_size ** 2 + height_span ** 2),
            1.0,
        )
        for station_idx in range(self.max_energy_charging_stations):
            station_pos = self.charging_station_positions[station_idx]
            rel = station_pos - own_pos
            rel_normalized = np.array([
                rel[0] / max(self.area_size, 1.0),
                rel[1] / max(self.area_size, 1.0),
                rel[2] / height_span,
            ])
            distance_normalized = np.linalg.norm(rel) / map_diag_3d
            cap = self.charging_station_capacity[station_idx]
            if np.isinf(cap):
                capacity_ratio = 1.0
                available_ratio = 1.0
            elif cap <= 0:
                capacity_ratio = 0.0
                available_ratio = 0.0
            else:
                capacity_ratio = float(np.clip(cap / max(self.n_uavs, 1), 0.0, 1.0))
                available_ratio = float(np.clip((cap - self.station_occupancy[station_idx]) / cap, 0.0, 1.0))
            queue_ratio = float(self.station_queue_lengths[station_idx] / max(self.n_uavs, 1))
            start = station_idx * self.energy_station_obs_dim
            station_obs[start:start + self.energy_station_obs_dim] = [
                *rel_normalized,
                distance_normalized,
                capacity_ratio,
                available_ratio,
                queue_ratio,
                float(station_idx < self.n_charging_stations),
            ]

        return np.concatenate([uav_obs, station_obs])

    def _get_state(self):
        base_state = super()._get_state()

        uav_energy = np.zeros((self.n_uavs, self.energy_uav_state_dim), dtype=float)
        uav_energy[:, 0] = self.uav_battery_ratios if self.battery_enabled else 1.0
        uav_energy[:, 1] = self.uav_charging.astype(float)
        uav_energy[:, 2] = self.uav_failed.astype(float)
        uav_energy[:, 3] = np.array([
            self._is_uav_unavailable(idx) for idx in range(self.n_uavs)
        ], dtype=float)
        uav_energy[:, 4] = self.uav_dock_requests.astype(float)
        uav_energy[:, 5] = np.where(
            self.uav_target_stations < 0,
            -1.0,
            self.uav_target_stations / max(self.max_energy_charging_stations - 1, 1),
        )
        uav_energy[:, 6] = self.charging_wait_steps / max(getattr(self, "max_steps", 1), 1)
        uav_energy[:, 7] = self.uav_return_threshold_ratios
        uav_energy[:, 8] = self.uav_return_energy_margins

        station_state = np.zeros(
            (self.max_energy_charging_stations, self.energy_station_state_dim),
            dtype=float,
        )
        for station_idx in range(self.max_energy_charging_stations):
            cap = self.charging_station_capacity[station_idx]
            if np.isinf(cap):
                cap_ratio = 1.0
                occ_ratio = 0.0
            elif cap <= 0:
                cap_ratio = 0.0
                occ_ratio = 0.0
            else:
                cap_ratio = float(np.clip(cap / max(self.n_uavs, 1), 0.0, 1.0))
                occ_ratio = float(np.clip(self.station_occupancy[station_idx] / cap, 0.0, 1.0))
            station_state[station_idx] = [
                self.charging_station_positions[station_idx, 0] / max(self.area_size, 1.0),
                self.charging_station_positions[station_idx, 1] / max(self.area_size, 1.0),
                (self.charging_station_positions[station_idx, 2] - self.height_range[0])
                / max(self.height_range[1] - self.height_range[0], 1.0),
                cap_ratio,
                occ_ratio,
                self.station_queue_lengths[station_idx] / max(self.n_uavs, 1),
                float(station_idx < self.n_charging_stations),
            ]

        stage_one_hot = np.zeros(4, dtype=float)
        stage_one_hot[self.energy_stage_index] = 1.0

        return np.concatenate([
            base_state,
            uav_energy.flatten(),
            station_state.flatten(),
            stage_one_hot,
        ])
