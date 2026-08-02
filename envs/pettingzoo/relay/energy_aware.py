import numpy as np
from gymnasium.spaces import Box, Dict

from envs.pettingzoo.relay.routed_core import UAVForcedRelayEnv


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

        # Scenario 7 adds energy state after the base transition, so the base
        # observations/state would be immediately discarded and rebuilt.
        self._defer_base_view_materialization = True
        proxy = _EnergyAwareConfigProxy(config, base_overrides)
        super().__init__(config=proxy, render_mode=kwargs.get("render_mode", None), seed=kwargs.get("seed", None))
        if self.action_space_type != "continuous":
            raise ValueError("Scenario 7 requires a continuous four-dimensional action space.")

        self.energy_stage_index = int(stage[1:]) - 1
        self.scenario7_interface_version = int(getattr(proxy, "scenario7_interface_version", 3))
        self.scenario7_reward_model = str(getattr(
            proxy,
            "scenario7_reward_model",
            "constrained_qos_safety_pbrs_v2",
        ))
        self.scenario7_reward_variant = str(getattr(
            proxy,
            "scenario7_reward_variant",
            "qos_fixed_safety_graph_pbrs",
        ))
        self.user_qos_rate_mbps = float(getattr(proxy, "user_qos_rate_mbps", 1.0))
        self.qos_target_ratio = float(getattr(proxy, "qos_target_ratio", 0.90))
        self.use_graph_pbrs = bool(getattr(proxy, "use_graph_pbrs", True))
        self.reward_discount_gamma = float(getattr(proxy, "gamma", 0.99))
        self.return_margin_scale = float(getattr(proxy, "return_margin_scale", 0.05))
        return_cost_cap = getattr(proxy, "return_cost_cap", 1.0)
        self.return_cost_cap = (
            None if return_cost_cap is None else float(return_cost_cap)
        )
        self.lambda_return = float(getattr(proxy, "lambda_return", 2.0))
        self.cutoff_event_penalty = float(getattr(proxy, "cutoff_event_penalty", 5.0))
        self.depletion_event_penalty = float(getattr(proxy, "depletion_event_penalty", 10.0))
        self.safety_dual = float(getattr(proxy, "safety_dual_initial", 0.0))
        self.battery_enabled = bool(getattr(proxy, "battery_enabled", False))
        self.charging_enabled = bool(getattr(proxy, "charging_enabled", self.battery_enabled))
        self.failure_enabled = bool(getattr(proxy, "uav_failure_enabled", False))

        self.battery_capacity_wh = float(getattr(proxy, "battery_capacity_wh", 160.0))
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
        self.last_net_energy_charged_wh = np.zeros(self.n_uavs, dtype=float)
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
        self.cutoff_event_seen = np.zeros(self.n_uavs, dtype=bool)
        self.depletion_event_seen = np.zeros(self.n_uavs, dtype=bool)
        self.previous_charging_mask = np.zeros(self.n_uavs, dtype=bool)
        self.last_effective_charging_session_count = 0
        self.episode_qos_utility_sum = 0.0
        self.episode_return_constraint_cost_sum = 0.0
        self.episode_return_risk_penalty_sum = 0.0
        self.episode_return_risk_steps = 0
        self.episode_max_return_deficit = 0.0
        self.episode_cutoff_event_count = 0
        self.episode_depletion_event_count = 0
        self.episode_charging_session_count = 0
        self.episode_first_effective_charge_step = -1
        self.episode_charging_uav_steps = 0
        self.episode_energy_charged_wh = 0.0
        self.episode_graph_pbrs_sum = 0.0
        self.last_energy_reward_components = {}
        self.current_graph_potential = 0.0
        self.current_euclidean_potential = 0.0
        self.last_user_rates_mbps = np.zeros(self.n_users, dtype=float)
        self.last_user_demand_bps = np.full(
            self.n_users,
            max(self.user_qos_rate_mbps * 1e6, 1e-8),
            dtype=float,
        )
        self.last_delivered_traffic_bps = np.zeros(self.n_users, dtype=float)
        self.last_reward_demand_bps = self.last_user_demand_bps.copy()
        self.last_graph_potential_demand_bps = self.last_user_demand_bps.copy()
        self.last_access_capacity_bps = np.zeros((self.n_uavs, self.n_users), dtype=float)
        self.last_backhaul_capacities_bps = np.zeros(self.n_uavs, dtype=float)
        self.last_widest_backhaul_capacities_bps = np.zeros(self.n_uavs, dtype=float)
        self.last_constrained_reward_metrics = {}

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
            "scenario7_interface_version": 3,
            "scenario7_reward_model": (
                getattr(
                    config,
                    "scenario7_reward_model",
                    "constrained_qos_safety_pbrs_v2",
                )
                if config is not None
                else "constrained_qos_safety_pbrs_v2"
            ),
            "scenario7_reward_variant": (
                getattr(config, "scenario7_reward_variant", "qos_fixed_safety_graph_pbrs")
                if config is not None
                else "qos_fixed_safety_graph_pbrs"
            ),
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
        reset_metrics = self._energy_metrics_dict()
        reset_metrics.update(self._episode_safety_metrics())
        reset_metrics.update({
            "scenario7_reward_model": self.scenario7_reward_model,
            "scenario7_reward_variant": self.scenario7_reward_variant,
            "return_penalty_coefficient": float(self._return_penalty_coefficient()),
            "safety_dual": float(self.safety_dual),
            "qos_target_ratio": float(self.qos_target_ratio),
            "graph_potential": float(self.current_graph_potential),
            "euclidean_potential": float(self.current_euclidean_potential),
        })
        for agent in self.agents:
            infos[agent]["state"] = current_state.copy()
            infos[agent]["energy_stage"] = self.energy_stage
            infos[agent]["scale_mode"] = self.scale_mode
            infos[agent]["reward_info"] = dict(reset_metrics)
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
        self.last_net_energy_charged_wh = np.zeros(self.n_uavs, dtype=float)
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
        self.cutoff_event_seen = np.zeros(self.n_uavs, dtype=bool)
        self.depletion_event_seen = np.zeros(self.n_uavs, dtype=bool)
        self.previous_charging_mask = np.zeros(self.n_uavs, dtype=bool)
        self.last_effective_charging_session_count = 0
        self.episode_qos_utility_sum = 0.0
        self.episode_return_constraint_cost_sum = 0.0
        self.episode_return_risk_penalty_sum = 0.0
        self.episode_return_risk_steps = 0
        self.episode_max_return_deficit = 0.0
        self.episode_cutoff_event_count = 0
        self.episode_depletion_event_count = 0
        self.episode_charging_session_count = 0
        self.episode_first_effective_charge_step = -1
        self.episode_charging_uav_steps = 0
        self.episode_energy_charged_wh = 0.0
        self.episode_graph_pbrs_sum = 0.0
        self.last_energy_reward_components = self._calculate_energy_reward_components()
        self.current_graph_potential = (
            self._graph_service_potential()
            if self.scenario7_reward_variant in {
                "qos_fixed_safety_graph_pbrs",
                "qos_fixed_safety_unbounded_graph_pbrs",
                "qos_adaptive_safety_graph_pbrs",
            }
            else 0.0
        )
        self.current_euclidean_potential = 0.0
        self.last_user_rates_mbps = np.zeros(self.n_users, dtype=float)
        self.last_user_demand_bps = self._current_user_qos_demand_bps().copy()
        self.last_delivered_traffic_bps = np.zeros(self.n_users, dtype=float)
        self.last_reward_demand_bps = self.last_user_demand_bps.copy()
        self.last_graph_potential_demand_bps = self.last_user_demand_bps.copy()
        self.last_access_capacity_bps = np.zeros((self.n_uavs, self.n_users), dtype=float)
        self.last_backhaul_capacities_bps = np.zeros(self.n_uavs, dtype=float)
        self.last_widest_backhaul_capacities_bps = np.zeros(self.n_uavs, dtype=float)
        self.last_constrained_reward_metrics = {}

    def step(self, actions):
        self._update_uav_failures()
        self._update_return_energy_state()

        pre_positions = self.uav_positions.copy()
        graph_potential_before = float(self.current_graph_potential)
        euclidean_potential_before = float(self.current_euclidean_potential)
        legacy_backhaul_potential_before = (
            self._backhaul_potential()
            if self.scenario7_reward_variant == "legacy_engineering"
            else 0.0
        )
        adjusted_actions, commanded_velocities = self._prepare_energy_actions(actions)

        observations, rewards, terminations, truncations, infos = super().step(adjusted_actions)
        base_load_balance_reward = float(np.mean(list(rewards.values()))) if rewards else 0.0
        if self.scenario7_reward_variant == "legacy_engineering":
            self.last_backhaul_potential_reward = float(np.clip(
                self._backhaul_potential() - legacy_backhaul_potential_before,
                -1.0,
                1.0,
            ))

        self._apply_energy_dynamics(pre_positions, commanded_velocities)
        self._update_return_energy_state()
        components = self._calculate_energy_reward_components()
        self.last_energy_reward_components = components
        self.prev_energy_failure_mask = self._energy_failure_mask()

        all_exhausted = bool(
            self.battery_enabled
            and np.all(self.uav_battery_ratios <= 0.0)
            and not np.any(self.uav_charging)
        )
        if all_exhausted:
            terminations = {agent: True for agent in self.agents}
            truncations = {agent: False for agent in self.agents}

        graph_potential_after = (
            self._graph_service_potential()
            if self.scenario7_reward_variant in {
                "qos_fixed_safety_graph_pbrs",
                "qos_fixed_safety_unbounded_graph_pbrs",
                "qos_adaptive_safety_graph_pbrs",
            }
            else 0.0
        )
        euclidean_potential_after = 0.0
        episode_done = bool(
            all(terminations.get(agent, False) or truncations.get(agent, False) for agent in self.agents)
        )
        reward_metrics = self._calculate_constrained_safety_reward(
            graph_potential_before=graph_potential_before,
            graph_potential_after=graph_potential_after,
            euclidean_potential_before=euclidean_potential_before,
            euclidean_potential_after=euclidean_potential_after,
            terminal=episode_done,
            base_load_balance_reward=base_load_balance_reward,
            energy_components=components,
        )
        self._update_episode_safety_statistics(reward_metrics)
        reward_metrics.update(self._episode_safety_metrics())
        shared_reward = float(reward_metrics["scenario7_reward"])
        rewards = {agent: shared_reward for agent in self.agents}
        self.current_graph_potential = graph_potential_after
        self.current_euclidean_potential = euclidean_potential_after
        if self.scenario7_reward_variant != "legacy_engineering":
            self.last_backhaul_potential_reward = float(
                reward_metrics["graph_potential_delta"]
            )
        self.last_constrained_reward_metrics = reward_metrics

        self._prepare_next_boundary_view()
        observations = {agent: self._get_observation(agent) for agent in self.agents}
        observations = self._update_observations_dict(observations)
        next_state = self._get_state()
        self.state = next_state

        metrics = self._energy_metrics_dict()
        metrics.update(components)
        metrics.update(reward_metrics)
        metrics["base_load_balance_reward"] = base_load_balance_reward
        metrics["rt_final_health_score"] = shared_reward
        metrics["pure_team_reward"] = shared_reward

        for agent in self.agents:
            if agent not in infos:
                infos[agent] = {}
            reward_info = infos[agent].setdefault("reward_info", {})
            reward_info.update(metrics)
            infos[agent]["next_state"] = next_state.copy()
            infos[agent]["energy_stage"] = self.energy_stage
            infos[agent]["scale_mode"] = self.scale_mode

        return observations, rewards, terminations, truncations, infos

    def _prepare_next_boundary_view(self):
        """Source hook after transition accounting and before one view materialization."""
        return None

    def set_scenario7_safety_dual(self, safety_dual):
        """Update the rollout-frozen safety multiplier for the adaptive ablation."""
        self.safety_dual = max(0.0, float(safety_dual))
        return {"safety_dual": self.safety_dual}

    def _return_penalty_coefficient(self):
        if self.scenario7_reward_variant == "qos_adaptive_safety_graph_pbrs":
            return max(0.0, float(self.safety_dual))
        return max(0.0, float(self.lambda_return))

    def _consume_safety_events(self):
        cutoff_mask = self._energy_failure_mask()
        depleted_mask = (
            self.uav_battery_ratios <= self.depleted_battery_threshold
            if self.battery_enabled
            else np.zeros(self.n_uavs, dtype=bool)
        )
        new_cutoff = cutoff_mask & ~self.cutoff_event_seen
        new_depletion = depleted_mask & ~self.depletion_event_seen
        self.cutoff_event_seen |= cutoff_mask
        self.depletion_event_seen |= depleted_mask
        return new_cutoff, new_depletion

    def _update_episode_safety_statistics(self, reward_metrics):
        self.episode_qos_utility_sum += float(
            reward_metrics.get("task_utility", 0.0)
        )
        return_cost = float(reward_metrics.get("return_constraint_cost", 0.0))
        self.episode_return_constraint_cost_sum += return_cost
        self.episode_return_risk_penalty_sum += float(
            reward_metrics.get("return_risk_penalty", 0.0)
        )
        if float(reward_metrics.get("return_constraint_cost_raw", 0.0)) > 0.0:
            self.episode_return_risk_steps += 1
        self.episode_max_return_deficit = max(
            self.episode_max_return_deficit,
            float(reward_metrics.get("return_deficit_max", 0.0)),
        )
        self.episode_cutoff_event_count += int(
            reward_metrics.get("cutoff_event_count", 0)
        )
        self.episode_depletion_event_count += int(
            reward_metrics.get("depletion_event_count", 0)
        )
        self.episode_charging_session_count += int(
            self.last_effective_charging_session_count
        )
        if (
            self.last_effective_charging_session_count > 0
            and self.episode_first_effective_charge_step < 0
        ):
            self.episode_first_effective_charge_step = int(self.current_step)
        self.episode_charging_uav_steps += int(np.sum(self.uav_charging))
        self.episode_energy_charged_wh += float(
            np.sum(self.last_net_energy_charged_wh)
        )
        self.episode_graph_pbrs_sum += float(
            reward_metrics.get("graph_potential_delta", 0.0)
        )

    def _episode_safety_metrics(self):
        steps = max(int(self.current_step), 1)
        return {
            "effective_charging_session_count": int(
                self.last_effective_charging_session_count
            ),
            "episode_qos_utility_sum": float(self.episode_qos_utility_sum),
            "episode_qos_utility_mean": float(
                self.episode_qos_utility_sum / steps
            ),
            "episode_return_constraint_cost_sum": float(
                self.episode_return_constraint_cost_sum
            ),
            "episode_return_risk_penalty_sum": float(
                self.episode_return_risk_penalty_sum
            ),
            "episode_return_risk_steps": int(self.episode_return_risk_steps),
            "episode_max_return_deficit": float(
                self.episode_max_return_deficit
            ),
            "episode_cutoff_event_count": int(
                self.episode_cutoff_event_count
            ),
            "episode_depletion_event_count": int(
                self.episode_depletion_event_count
            ),
            "episode_charging_session_count": int(
                self.episode_charging_session_count
            ),
            "episode_first_effective_charge_step": int(
                self.episode_first_effective_charge_step
            ),
            "episode_charging_uav_steps": int(
                self.episode_charging_uav_steps
            ),
            "episode_energy_charged_wh": float(
                self.episode_energy_charged_wh
            ),
            "episode_graph_pbrs_sum": float(self.episode_graph_pbrs_sum),
            "episode_final_min_return_margin": float(
                np.min(self._raw_return_energy_margins())
                if self.n_uavs > 0
                else 0.0
            ),
        }

    def _calculate_constrained_safety_reward(
        self,
        graph_potential_before,
        graph_potential_after,
        euclidean_potential_before,
        euclidean_potential_after,
        terminal,
        base_load_balance_reward,
        energy_components,
    ):
        user_rates_bps, access_capacities_bps, backhaul_capacities_bps = (
            self._calculate_end_to_end_user_rates()
        )
        user_demand_bps = self._current_user_qos_demand_bps()
        self.last_reward_demand_bps = user_demand_bps.copy()
        delivered_traffic_bps = np.minimum(user_rates_bps, user_demand_bps)
        qos_satisfaction = delivered_traffic_bps / user_demand_bps
        qos_satisfaction_ratio = float(np.mean(qos_satisfaction)) if self.n_users > 0 else 0.0
        qos_met_fraction = float(
            np.mean(delivered_traffic_bps >= user_demand_bps)
        ) if self.n_users > 0 else 0.0

        normalized_energy, consumed_wh = self._normalized_step_energy()
        return_margins = self._raw_return_energy_margins()
        return_violations = np.maximum(0.0, -return_margins)
        return_constraint_cost_raw = (
            float(np.max(return_violations) / max(self.return_margin_scale, 1e-8))
            if return_violations.size
            else 0.0
        )
        return_constraint_cost = (
            return_constraint_cost_raw
            if self.return_cost_cap is None
            else min(return_constraint_cost_raw, self.return_cost_cap)
        )
        return_violation_fraction = float(np.mean(return_margins < 0.0)) if return_margins.size else 0.0
        new_cutoff, new_depletion = self._consume_safety_events()
        cutoff_event_count = int(np.sum(new_cutoff))
        depletion_event_count = int(np.sum(new_depletion))
        return_penalty_coefficient = self._return_penalty_coefficient()
        return_risk_penalty = return_penalty_coefficient * return_constraint_cost
        cutoff_penalty = self.cutoff_event_penalty * cutoff_event_count
        depletion_penalty = self.depletion_event_penalty * depletion_event_count

        variant = self.scenario7_reward_variant
        potential_type = "none"
        shaping_potential_before = 0.0
        shaping_potential_after = 0.0
        if variant in {
            "qos_fixed_safety_graph_pbrs",
            "qos_fixed_safety_unbounded_graph_pbrs",
            "qos_adaptive_safety_graph_pbrs",
        }:
            potential_type = "graph"
            shaping_potential_before = graph_potential_before
            shaping_potential_after = graph_potential_after

        potential_delta = self._graph_potential_reward(
            shaping_potential_before,
            shaping_potential_after,
            terminal,
            enabled=potential_type != "none",
        )

        energy_management_delta_raw = self._energy_management_delta_raw(energy_components)
        energy_efficiency_reward_delta = self._energy_efficiency_reward_delta(
            energy_components,
            base_load_balance_reward,
        )
        legacy_energy_delta_raw = self._energy_reward_delta_raw(
            energy_components,
            base_load_balance_reward,
        )
        legacy_energy_delta = self._clip_energy_reward_delta(legacy_energy_delta_raw)

        if variant == "legacy_engineering":
            safety_reward_before_pbrs = base_load_balance_reward + legacy_energy_delta
        elif variant == "qos_only":
            safety_reward_before_pbrs = qos_satisfaction_ratio
        elif variant == "qos_depletion_penalty":
            safety_reward_before_pbrs = qos_satisfaction_ratio - depletion_penalty
        else:
            safety_reward_before_pbrs = (
                qos_satisfaction_ratio
                - return_risk_penalty
                - cutoff_penalty
                - depletion_penalty
            )
        scenario7_reward = safety_reward_before_pbrs + potential_delta

        total_rate_bps = float(np.sum(user_rates_bps))
        consumed_joules = consumed_wh * 3600.0
        bits_per_joule = total_rate_bps * max(float(self.time_step), 1e-8) / max(
            consumed_joules,
            1e-8,
        )

        self.last_user_rates_mbps = user_rates_bps / 1e6
        self.last_user_demand_bps = user_demand_bps.copy()
        self.last_delivered_traffic_bps = delivered_traffic_bps.copy()
        self.last_access_capacity_bps = access_capacities_bps
        self.last_backhaul_capacities_bps = backhaul_capacities_bps

        return {
            "scenario7_reward_model": self.scenario7_reward_model,
            "scenario7_reward_variant": variant,
            "scenario7_reward": float(scenario7_reward),
            "safety_reward_before_pbrs": float(safety_reward_before_pbrs),
            "task_utility": qos_satisfaction_ratio,
            "qos_satisfaction_ratio": qos_satisfaction_ratio,
            "qos_met_fraction": qos_met_fraction,
            "qos_target_ratio": float(self.qos_target_ratio),
            "mean_user_rate_mbps": float(np.mean(self.last_user_rates_mbps)) if self.n_users else 0.0,
            "std_user_rate_mbps": float(np.std(self.last_user_rates_mbps)) if self.n_users else 0.0,
            "min_user_rate_mbps": float(np.min(self.last_user_rates_mbps)) if self.n_users else 0.0,
            "p10_user_rate_mbps": float(np.percentile(self.last_user_rates_mbps, 10)) if self.n_users else 0.0,
            "median_user_rate_mbps": float(np.median(self.last_user_rates_mbps)) if self.n_users else 0.0,
            "p90_user_rate_mbps": float(np.percentile(self.last_user_rates_mbps, 90)) if self.n_users else 0.0,
            "max_user_rate_mbps": float(np.max(self.last_user_rates_mbps)) if self.n_users else 0.0,
            "effective_end_to_end_throughput_mbps": total_rate_bps / 1e6,
            "delivered_end_to_end_throughput_mbps": float(
                np.sum(delivered_traffic_bps) / 1e6
            ),
            "mean_user_demand_mbps": float(
                np.mean(user_demand_bps) / 1e6
            ) if self.n_users else 0.0,
            "normalized_propulsion_energy": float(normalized_energy),
            "step_propulsion_energy_wh": float(consumed_wh),
            "instantaneous_bits_per_joule": float(bits_per_joule),
            "return_margin_scale": float(self.return_margin_scale),
            "return_cost_cap": (
                float(self.return_cost_cap)
                if self.return_cost_cap is not None
                else float("inf")
            ),
            "return_penalty_coefficient": float(return_penalty_coefficient),
            "safety_dual": float(self.safety_dual),
            "return_constraint_cost_raw": float(return_constraint_cost_raw),
            "return_constraint_cost": float(return_constraint_cost),
            "return_risk_penalty": float(return_risk_penalty),
            "return_deficit_max": (
                float(np.max(return_violations))
                if return_violations.size
                else 0.0
            ),
            "cutoff_event_count": cutoff_event_count,
            "depletion_event_count": depletion_event_count,
            "cutoff_event_penalty": float(cutoff_penalty),
            "depletion_event_penalty": float(depletion_penalty),
            "return_margin_mean": float(np.mean(return_margins)) if return_margins.size else 0.0,
            "return_margin_min": float(np.min(return_margins)) if return_margins.size else 0.0,
            "return_violation_fraction": return_violation_fraction,
            "graph_potential": float(graph_potential_after),
            "graph_potential_before": float(graph_potential_before),
            "graph_potential_delta": float(
                potential_delta if potential_type == "graph" else 0.0
            ),
            "euclidean_potential": float(euclidean_potential_after),
            "euclidean_potential_before": float(euclidean_potential_before),
            "euclidean_potential_delta": float(
                potential_delta if potential_type == "euclidean" else 0.0
            ),
            "shaping_potential": float(shaping_potential_after),
            "shaping_potential_delta": float(potential_delta),
            "energy_management_delta_raw": float(energy_management_delta_raw),
            "energy_efficiency_reward_delta": float(energy_efficiency_reward_delta),
            "energy_reward_delta_raw": float(legacy_energy_delta_raw),
            "energy_reward_delta_clipped": float(legacy_energy_delta),
            "energy_reward_delta": float(legacy_energy_delta),
        }

    def _graph_potential_reward(self, potential_before, potential_after, terminal, enabled=None):
        if enabled is None:
            enabled = self.use_graph_pbrs
        if not enabled:
            return 0.0
        potential_next = 0.0 if terminal else float(potential_after)
        return float(
            self.reward_discount_gamma * potential_next - float(potential_before)
        )

    def _current_user_qos_demand_bps(self):
        """Current per-user task demand; the base path remains scalar-equivalent.

        Source-specific environments override this one seam.  Raw radio rates,
        association, bandwidth allocation and routing never consume it.
        """
        return np.full(
            self.n_users,
            max(self.user_qos_rate_mbps * 1e6, 1e-8),
            dtype=float,
        )

    def _calculate_end_to_end_user_rates(self):
        access_capacities = np.zeros((self.n_uavs, self.n_users), dtype=float)
        backhaul_capacities = np.zeros(self.n_uavs, dtype=float)
        current_unavailable = self._communication_unavailable_mask()
        can_reuse_sinr = self._sinr_matrix_matches_current_state(
            current_unavailable
        )

        for uav_idx in range(self.n_uavs):
            if current_unavailable[uav_idx]:
                continue
            connected_users = np.flatnonzero(self.connections[uav_idx])
            if connected_users.size == 0:
                continue

            access_bandwidth = (
                self.bandwidth / max(self.n_uavs, 1)
                if self.use_fdma
                else self.bandwidth
            )
            bandwidth_per_user = access_bandwidth / connected_users.size
            for user_idx in connected_users:
                access_capacities[uav_idx, user_idx] = self._access_capacity_bps(
                    uav_idx,
                    int(user_idx),
                    bandwidth_per_user,
                    relaxed=False,
                    current_unavailable=current_unavailable,
                    can_reuse_sinr=can_reuse_sinr,
                )

            path_record = self.routing_paths.get(uav_idx)
            if path_record and path_record[0]:
                backhaul_capacities[uav_idx] = max(0.0, float(path_record[1]))

        delivered_by_uav = np.zeros_like(access_capacities)
        for uav_idx in range(self.n_uavs):
            access_sum = float(np.sum(access_capacities[uav_idx]))
            if access_sum <= 0.0 or backhaul_capacities[uav_idx] <= 0.0:
                continue
            scale = min(1.0, backhaul_capacities[uav_idx] / max(access_sum, 1e-8))
            delivered_by_uav[uav_idx] = scale * access_capacities[uav_idx]

        user_rates = (
            np.max(delivered_by_uav, axis=0)
            if self.n_uavs > 0
            else np.zeros(self.n_users, dtype=float)
        )
        return user_rates, access_capacities, backhaul_capacities

    def _sinr_matrix_matches_current_state(self, current_unavailable):
        return (
            not bool(getattr(self, "_disable_sinr_matrix_reuse", False))
            and hasattr(self, "_sinr_uav_positions")
            and np.array_equal(self.uav_positions, self._sinr_uav_positions)
            and np.array_equal(self.user_positions, self._sinr_user_positions)
            and np.array_equal(current_unavailable, self._sinr_unavailable)
        )

    def _access_capacity_bps(
        self,
        uav_idx,
        user_idx,
        bandwidth_hz,
        relaxed,
        *,
        current_unavailable=None,
        can_reuse_sinr=None,
    ):
        if current_unavailable is None:
            if bool(getattr(self, "_disable_graph_radio_reuse", False)):
                current_unavailable = np.asarray(
                    [self._is_uav_unavailable(index) for index in range(self.n_uavs)],
                    dtype=bool,
                )
            else:
                current_unavailable = self._communication_unavailable_mask()
        if current_unavailable[uav_idx] or bandwidth_hz <= 0.0:
            return 0.0
        if can_reuse_sinr is None:
            can_reuse_sinr = self._sinr_matrix_matches_current_state(
                current_unavailable
            )
        if can_reuse_sinr:
            sinr_db = float(self.sinr_matrix[uav_idx, user_idx])
        else:
            uav_pos = self.uav_positions[uav_idx]
            user_pos = self.user_positions[user_idx]
            path_loss = self._compute_air_to_ground_path_loss(uav_pos, user_pos)
            rx_power = self.tx_power - path_loss
            sinr_db = self._compute_uav_to_user_sinr(uav_idx, user_idx, rx_power)
        if not relaxed and sinr_db < self.min_sinr:
            return 0.0
        spectral_efficiency = self._spectral_efficiency(sinr_db, relaxed=relaxed)
        return max(0.0, float(bandwidth_hz) * spectral_efficiency)

    def _spectral_efficiency(self, sinr_db, relaxed):
        if not np.isfinite(sinr_db):
            return 0.0
        if not relaxed:
            return float(self._get_spectral_efficiency_from_sinr(sinr_db))
        sinr_linear = 10.0 ** (float(np.clip(sinr_db, -40.0, 60.0)) / 10.0)
        shannon_efficiency = np.log2(1.0 + sinr_linear)
        max_efficiency = max(float(entry[1]) for entry in self.mcs_table)
        return float(np.clip(shannon_efficiency, 0.0, max_efficiency))

    def _relaxed_backhaul_capacity_bps(
        self, sender_idx, receiver_type, receiver_idx, *, current_unavailable=None
    ):
        disable_reuse = bool(getattr(self, "_disable_graph_radio_reuse", False))
        if current_unavailable is None and not disable_reuse:
            current_unavailable = self._communication_unavailable_mask()
        sender_unavailable = (
            self._is_uav_unavailable(sender_idx)
            if current_unavailable is None
            else bool(current_unavailable[sender_idx])
        )
        if sender_unavailable:
            return 0.0
        pos1 = self.uav_positions[sender_idx]
        if receiver_type == "uav":
            receiver_unavailable = (
                self._is_uav_unavailable(receiver_idx)
                if current_unavailable is None
                else bool(current_unavailable[receiver_idx])
            )
            if sender_idx == receiver_idx or receiver_unavailable:
                return 0.0
            pos2 = self.uav_positions[receiver_idx]
            path_loss = self._compute_air_to_air_path_loss(pos1, pos2)
            rx_power = self.tx_power - path_loss
        else:
            pos2 = self.ground_bs_positions[receiver_idx]
            path_loss = self._compute_air_to_ground_path_loss(pos1, pos2)
            rx_power = self.tx_power - path_loss

        sinr_args = (
            "uav",
            sender_idx,
            receiver_type,
            receiver_idx,
            rx_power,
        )
        sinr_db = (
            self._compute_link_sinr(*sinr_args)
            if disable_reuse
            else self._cached_link_sinr(*sinr_args)
        )
        link_bandwidth = (
            self.bandwidth / max(self.n_uavs, 1)
            if self.use_fdma
            else self.bandwidth
        )
        return link_bandwidth * self._spectral_efficiency(sinr_db, relaxed=True)

    def _widest_backhaul_capacities(self, *, current_unavailable=None):
        if self.n_uavs <= 0 or self.n_ground_bs <= 0:
            return np.zeros(self.n_uavs, dtype=float)
        if (
            current_unavailable is None
            and not bool(getattr(self, "_disable_graph_radio_reuse", False))
        ):
            current_unavailable = self._communication_unavailable_mask()

        uav_edges = np.zeros((self.n_uavs, self.n_uavs), dtype=float)
        bs_edges = np.zeros((self.n_uavs, self.n_ground_bs), dtype=float)
        for sender_idx in range(self.n_uavs):
            for receiver_idx in range(self.n_uavs):
                if sender_idx != receiver_idx:
                    uav_edges[sender_idx, receiver_idx] = self._relaxed_backhaul_capacity_bps(
                        sender_idx,
                        "uav",
                        receiver_idx,
                        current_unavailable=current_unavailable,
                    )
            for bs_idx in range(self.n_ground_bs):
                bs_edges[sender_idx, bs_idx] = self._relaxed_backhaul_capacity_bps(
                    sender_idx,
                    "ground_bs",
                    bs_idx,
                    current_unavailable=current_unavailable,
                )

        widest = np.max(bs_edges, axis=1)
        for _ in range(max(self.n_uavs - 1, 0)):
            updated = widest.copy()
            for sender_idx in range(self.n_uavs):
                via_uav = np.minimum(uav_edges[sender_idx], widest)
                updated[sender_idx] = max(updated[sender_idx], float(np.max(via_uav)))
            if np.allclose(updated, widest, rtol=1e-7, atol=1e-6):
                widest = updated
                break
            widest = updated
        return widest

    def _graph_service_potential(self):
        if self.n_users <= 0 or self.n_uavs <= 0:
            return 0.0
        disable_reuse = bool(getattr(self, "_disable_graph_radio_reuse", False))
        current_unavailable = (
            None if disable_reuse else self._communication_unavailable_mask()
        )
        can_reuse_sinr = (
            None
            if current_unavailable is None
            else self._sinr_matrix_matches_current_state(current_unavailable)
        )
        widest_backhaul = self._widest_backhaul_capacities(
            current_unavailable=current_unavailable
        )
        self.last_widest_backhaul_capacities_bps = widest_backhaul
        nominal_users_per_uav = max(1, int(np.ceil(self.n_users / max(self.n_uavs, 1))))
        access_bandwidth = (
            self.bandwidth / max(self.n_uavs, 1)
            if self.use_fdma
            else self.bandwidth
        )
        candidate_bandwidth = access_bandwidth / nominal_users_per_uav
        user_demand_bps = self._current_user_qos_demand_bps()
        self.last_graph_potential_demand_bps = user_demand_bps.copy()

        relaxed_service = np.zeros(self.n_users, dtype=float)
        for user_idx in range(self.n_users):
            best_capacity = 0.0
            for uav_idx in range(self.n_uavs):
                access_capacity = self._access_capacity_bps(
                    uav_idx,
                    user_idx,
                    candidate_bandwidth,
                    relaxed=True,
                    current_unavailable=current_unavailable,
                    can_reuse_sinr=can_reuse_sinr,
                )
                end_to_end_capacity = min(access_capacity, widest_backhaul[uav_idx])
                best_capacity = max(best_capacity, end_to_end_capacity)
            relaxed_service[user_idx] = np.clip(
                best_capacity / user_demand_bps[user_idx], 0.0, 1.0
            )
        return float(np.mean(relaxed_service))

    def _euclidean_service_potential(self):
        """Distance-only PBRS baseline used in the paper ablation."""
        if self.n_users <= 0 or self.n_uavs <= 0 or self.n_ground_bs <= 0:
            return 0.0
        height_span = max(float(self.height_range[1] - self.height_range[0]), 1.0)
        map_diag_3d = max(
            np.sqrt(2.0 * self.area_size ** 2 + height_span ** 2),
            1.0,
        )
        user_distances = np.linalg.norm(
            self.user_positions[:, None, :] - self.uav_positions[None, :, :],
            axis=2,
        )
        user_proximity = 1.0 - np.clip(
            np.min(user_distances, axis=1) / map_diag_3d,
            0.0,
            1.0,
        )
        bs_distances = np.linalg.norm(
            self.uav_positions[:, None, :] - self.ground_bs_positions[None, :, :],
            axis=2,
        )
        bs_proximity = 1.0 - np.clip(
            np.min(bs_distances, axis=1) / map_diag_3d,
            0.0,
            1.0,
        )
        return float(0.5 * np.mean(user_proximity) + 0.5 * np.mean(bs_proximity))

    def estimate_heuristic_qos_feasibility(self):
        """
        Construct deterministic relay/service layouts and report the best QoS value.

        This is a lower-bound feasibility check: failure does not prove physical
        impossibility, but a passing layout demonstrates that the configured QoS
        target is reachable without changing reward coefficients.
        """
        if self.n_uavs < 3 or self.n_users <= 0 or self.n_ground_bs <= 0:
            return {
                "feasible": False,
                "qos_satisfaction_ratio": 0.0,
                "qos_met_fraction": 0.0,
                "throughput_mbps": 0.0,
            }

        user_xy = np.asarray(self.user_positions[:, :2], dtype=float)
        bs_xy = np.mean(self.ground_bs_positions[:, :2], axis=0)
        best = {
            "feasible": False,
            "qos_satisfaction_ratio": 0.0,
            "qos_met_fraction": 0.0,
            "throughput_mbps": 0.0,
            "service_uavs": 0,
            "height_m": 0.0,
        }
        best_positions = None

        for service_uavs in sorted({
            max(1, self.n_uavs - 2),
            max(1, self.n_uavs - 3),
        }, reverse=True):
            relay_uavs = self.n_uavs - service_uavs
            seed_indices = np.linspace(
                0,
                self.n_users - 1,
                service_uavs,
                dtype=int,
            )
            centroids = user_xy[seed_indices].copy()
            for _ in range(30):
                distances = np.sum(
                    (user_xy[:, None, :] - centroids[None, :, :]) ** 2,
                    axis=2,
                )
                labels = np.argmin(distances, axis=1)
                updated = np.array([
                    np.mean(user_xy[labels == cluster_idx], axis=0)
                    if np.any(labels == cluster_idx)
                    else centroids[cluster_idx]
                    for cluster_idx in range(service_uavs)
                ])
                if np.allclose(updated, centroids):
                    break
                centroids = updated

            service_center = np.mean(centroids, axis=0)
            candidate_heights = (
                float(self.height_range[0]),
                float(np.mean(self.height_range)),
                float(self.height_range[1]),
            )
            for height in candidate_heights:
                for relay_idx in range(relay_uavs):
                    fraction = (relay_idx + 1) / (relay_uavs + 1)
                    xy = (1.0 - fraction) * bs_xy + fraction * service_center
                    self.uav_positions[relay_idx] = [xy[0], xy[1], height]
                for service_idx in range(service_uavs):
                    xy = centroids[service_idx]
                    self.uav_positions[relay_uavs + service_idx] = [
                        xy[0],
                        xy[1],
                        height,
                    ]

                self._update_channel_state()
                self._update_uav_connections()
                self._compute_routing_paths()
                rates_bps, _, _ = self._calculate_end_to_end_user_rates()
                qos_rate_bps = max(self.user_qos_rate_mbps * 1e6, 1e-8)
                qos_ratio = float(np.mean(np.clip(rates_bps / qos_rate_bps, 0.0, 1.0)))
                qos_met = float(np.mean(rates_bps >= qos_rate_bps))
                if qos_ratio > best["qos_satisfaction_ratio"]:
                    best = {
                        "feasible": qos_ratio >= self.qos_target_ratio,
                        "qos_satisfaction_ratio": qos_ratio,
                        "qos_met_fraction": qos_met,
                        "throughput_mbps": float(np.sum(rates_bps) / 1e6),
                        "service_uavs": int(service_uavs),
                        "height_m": float(height),
                    }
                    best_positions = self.uav_positions.copy()
        if best_positions is not None:
            self.uav_positions = best_positions
            self._update_channel_state()
            self._update_uav_connections()
            self._compute_routing_paths()
            self._heuristic_best_layout_positions = best_positions.copy()
        return best

    def estimate_no_charge_safety_pressure(self):
        """Estimate end-of-episode return feasibility for a static service layout."""
        if not hasattr(self, "_heuristic_best_layout_positions"):
            self.estimate_heuristic_qos_feasibility()
        hover_wh = (
            self._calculate_power_consumption(0.0, 0.0)
            * self.max_steps
            * self.time_step
            / 3600.0
        )
        return_power_w = self._calculate_power_consumption(
            self.limp_home_speed_mps,
            0.0,
        )
        end_margins = np.zeros(self.n_uavs, dtype=float)
        for uav_idx in range(self.n_uavs):
            _, _, distance = self._nearest_charging_station(uav_idx)
            return_wh = (
                distance
                / max(self.limp_home_speed_mps, 1e-8)
                * return_power_w
                / 3600.0
            )
            end_margins[uav_idx] = (
                self.uav_battery_ratios[uav_idx]
                - (hover_wh + return_wh)
                / max(self.battery_capacity_wh, 1e-8)
                - self.return_reserve_ratio
            )
        return {
            "episode_requires_charging": bool(np.any(end_margins < 0.0)),
            "unsafe_uav_fraction": float(np.mean(end_margins < 0.0)),
            "minimum_end_return_margin": float(np.min(end_margins)),
            "mean_end_return_margin": float(np.mean(end_margins)),
        }

    def _static_qos_with_unavailable_uavs(self, unavailable):
        saved_batteries = self.uav_battery_ratios.copy()
        try:
            if unavailable:
                self.uav_battery_ratios[list(unavailable)] = 0.0
            self._update_channel_state()
            self._update_uav_connections()
            self._compute_routing_paths()
            rates_bps, _, _ = self._calculate_end_to_end_user_rates()
            qos_rate_bps = max(self.user_qos_rate_mbps * 1e6, 1e-8)
            return float(np.mean(np.clip(
                rates_bps / qos_rate_bps,
                0.0,
                1.0,
            )))
        finally:
            self.uav_battery_ratios = saved_batteries
            self._update_channel_state()
            self._update_uav_connections()
            self._compute_routing_paths()

    def estimate_rotation_charging_feasibility(self, top_up_ratio=0.25):
        """
        Build a static-layout, earliest-deadline charging certificate.

        UAV movement, station contention, propulsion energy, net charging power,
        and temporary service loss are included. User positions remain fixed so
        this is a physical feasibility certificate, not a learned-policy score.
        """
        layout = self.estimate_heuristic_qos_feasibility()
        no_charge = self.estimate_no_charge_safety_pressure()
        full_qos = self._static_qos_with_unavailable_uavs(())
        no_charge_end_margins = []
        hover_power = self._calculate_power_consumption(0.0, 0.0)
        hover_wh = hover_power * self.max_steps * self.time_step / 3600.0
        return_power = self._calculate_power_consumption(
            self.limp_home_speed_mps,
            0.0,
        )
        return_required_wh = np.zeros(self.n_uavs, dtype=float)
        for uav_idx in range(self.n_uavs):
            _, _, distance = self._nearest_charging_station(uav_idx)
            return_required_wh[uav_idx] = (
                distance
                / max(self.limp_home_speed_mps, 1e-8)
                * return_power
                / 3600.0
                + self.return_reserve_ratio * self.battery_capacity_wh
            )
            no_charge_end_margins.append(
                self.uav_battery_ratios[uav_idx]
                - (hover_wh + return_required_wh[uav_idx])
                / max(self.battery_capacity_wh, 1e-8)
            )

        candidates = [
            int(idx)
            for idx in np.argsort(no_charge_end_margins)
            if no_charge_end_margins[idx] < 0.0
        ]
        if not candidates and self.n_uavs > 0:
            candidates = [int(np.argmin(no_charge_end_margins))]
        station_available = np.zeros(self.n_charging_stations, dtype=float)
        schedule = []
        net_charge_power = max(
            self.charging_power_w - hover_power,
            1e-8,
        )
        nominal_charge_wh = (
            max(0.0, float(top_up_ratio)) * self.battery_capacity_wh
        )
        charge_buffer_wh = 2.0
        cruise_power = self._calculate_power_consumption(self.max_speed, 0.0)
        docking_power = self._calculate_power_consumption(
            self.docking_horizontal_speed_mps,
            0.0,
        )

        for uav_idx in candidates:
            station_idx, _, distance = self._nearest_charging_station(uav_idx)
            outer_distance = max(0.0, distance - self.charging_radius_m)
            inner_distance = min(distance, self.charging_radius_m)
            outer_time = outer_distance / max(self.max_speed, 1e-8)
            inner_time = inner_distance / max(
                self.docking_horizontal_speed_mps,
                1e-8,
            )
            travel_time = outer_time + inner_time
            travel_wh = (
                outer_time * cruise_power + inner_time * docking_power
            ) / 3600.0
            departure = max(0.0, station_available[station_idx] - travel_time)
            arrival = departure + travel_time
            charge_start = max(arrival, station_available[station_idx])
            charge_wh = nominal_charge_wh + charge_buffer_wh
            charge_seconds = charge_wh * 3600.0 / net_charge_power
            charge_end = charge_start + charge_seconds
            return_end = charge_end + travel_time
            station_available[station_idx] = charge_end

            initial_wh = (
                self.uav_battery_ratios[uav_idx]
                * self.battery_capacity_wh
            )
            wait_wh = max(0.0, charge_start - arrival) * hover_power / 3600.0
            pre_charge_wh = (
                departure * hover_power / 3600.0
                + travel_wh
                + wait_wh
            )
            post_charge_wh = (
                travel_wh
                + max(0.0, self.max_steps - return_end)
                * hover_power
                / 3600.0
            )
            final_wh = initial_wh - pre_charge_wh + charge_wh - post_charge_wh
            schedule.append({
                "uav_idx": uav_idx,
                "station_idx": station_idx,
                "departure": departure,
                "charge_start": charge_start,
                "charge_end": charge_end,
                "return_end": return_end,
                "pre_charge_wh": pre_charge_wh,
                "final_wh": final_wh,
                "return_required_wh": return_required_wh[uav_idx],
            })

        qos_cache = {(): full_qos}
        qos_sum = 0.0
        for step in range(self.max_steps):
            unavailable = tuple(sorted(
                item["uav_idx"]
                for item in schedule
                if item["departure"] <= step < item["return_end"]
            ))
            if unavailable not in qos_cache:
                qos_cache[unavailable] = self._static_qos_with_unavailable_uavs(
                    unavailable
                )
            qos_sum += qos_cache[unavailable]

        schedule_within_horizon = all(
            item["return_end"] <= self.max_steps for item in schedule
        )
        depletion_free = all(
            item["pre_charge_wh"]
            < self.uav_battery_ratios[item["uav_idx"]]
            * self.battery_capacity_wh
            and item["final_wh"] >= item["return_required_wh"]
            for item in schedule
        )
        effective_charging = bool(schedule) and charge_wh > 0.0
        mean_qos = qos_sum / max(self.max_steps, 1)
        return {
            **layout,
            **no_charge,
            "effective_charging": effective_charging,
            "charging_session_count": len(schedule),
            "schedule_within_horizon": bool(schedule_within_horizon),
            "depletion_free": bool(depletion_free),
            "rotation_qos_satisfaction_ratio": float(mean_qos),
            "full_layout_qos_satisfaction_ratio": float(full_qos),
            "charge_top_up_ratio": float(top_up_ratio),
            "charge_buffer_wh": float(charge_buffer_wh),
            "nominal_charge_duration_steps": float(
                nominal_charge_wh * 3600.0 / net_charge_power
            ),
            "charge_duration_steps": float(
                (nominal_charge_wh + charge_buffer_wh)
                * 3600.0
                / net_charge_power
            ),
            "schedule": schedule,
        }

    def _normalized_step_energy(self):
        dt = max(float(self.time_step), 1e-8)
        if self.battery_enabled:
            consumed_wh = float(np.sum(self.last_energy_consumed_wh))
        else:
            consumed_wh = 0.0
            for velocity in self.last_actual_velocities:
                consumed_wh += (
                    self._calculate_power_consumption(
                        np.linalg.norm(velocity[:2]),
                        velocity[2],
                    )
                    * dt
                    / 3600.0
                )
        max_power = self._calculate_power_consumption(
            self.max_speed,
            self.max_vertical_speed_mps,
        )
        max_team_step_wh = max(
            self.n_uavs * max_power * dt / 3600.0,
            1e-8,
        )
        return float(np.clip(consumed_wh / max_team_step_wh, 0.0, 1.0)), consumed_wh

    def _raw_return_energy_margins(self):
        if not self.battery_enabled:
            return np.ones(self.n_uavs, dtype=float)
        return_power_w = self._calculate_power_consumption(self.limp_home_speed_mps, 0.0)
        margins = np.zeros(self.n_uavs, dtype=float)
        for uav_idx in range(self.n_uavs):
            _, _, distance = self._nearest_charging_station(uav_idx)
            return_seconds = distance / max(self.limp_home_speed_mps, 1e-8)
            required_ratio = (
                return_seconds * return_power_w / 3600.0
            ) / max(self.battery_capacity_wh, 1e-8)
            margins[uav_idx] = (
                self.uav_battery_ratios[uav_idx]
                - required_ratio
                - self.return_reserve_ratio
            )
        return margins

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
        charging_before = self.uav_charging.copy()
        self.last_energy_consumed_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_energy_charged_wh = np.zeros(self.n_uavs, dtype=float)
        self.last_net_energy_charged_wh = np.zeros(self.n_uavs, dtype=float)
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
            self.previous_charging_mask = charging_before
            self.last_effective_charging_session_count = 0
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
                self.last_net_energy_charged_wh[uav_idx] = max(
                    0.0,
                    actual_charge_wh - self.last_energy_consumed_wh[uav_idx],
                )
                self.uav_battery_ratios[uav_idx] += actual_charge_wh / max(self.battery_capacity_wh, 1e-8)
                self.uav_charging[uav_idx] = actual_charge_wh > 0.0
                self.charging_wait_steps[uav_idx] = 0
            elif any(uav_idx in candidates for candidates in eligible_by_station.values()):
                self.charging_wait_steps[uav_idx] += 1
            else:
                self.charging_wait_steps[uav_idx] = 0

        self.uav_battery_ratios = np.clip(self.uav_battery_ratios, 0.0, 1.0)
        new_sessions = (
            self.uav_charging
            & ~charging_before
            & (self.last_net_energy_charged_wh > 0.0)
        )
        self.last_effective_charging_session_count = int(np.sum(new_sessions))
        self.previous_charging_mask = self.uav_charging.copy()

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
        raw_margins = np.zeros(self.n_uavs, dtype=float)
        for uav_idx in range(self.n_uavs):
            _, _, distance = self._nearest_charging_station(uav_idx)
            return_seconds = distance / max(self.limp_home_speed_mps, 1e-8)
            required_wh = return_seconds * return_power_w / 3600.0
            required_ratio = required_wh / max(self.battery_capacity_wh, 1e-8)
            raw_margins[uav_idx] = (
                self.uav_battery_ratios[uav_idx]
                - required_ratio
                - self.return_reserve_ratio
            )
            thresholds[uav_idx] = np.clip(
                required_ratio + self.return_reserve_ratio,
                self.return_threshold_min,
                self.return_threshold_max,
            )
        self.uav_return_threshold_ratios = thresholds
        self.uav_return_energy_margins = raw_margins

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
            "step_charger_input_wh": float(
                np.sum(self.last_energy_charged_wh)
            ),
            "step_net_energy_charged_wh": float(
                np.sum(self.last_net_energy_charged_wh)
            ),
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

    def _communication_unavailable_mask(self):
        failed = np.asarray(self.uav_failed, dtype=bool)
        if not self.battery_enabled:
            return failed.copy()
        return failed | (
            np.asarray(self.uav_battery_ratios) <= self.service_cutoff_threshold
        )

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

    def _update_channel_state(self):
        super()._update_channel_state()
        self._sinr_uav_positions = self.uav_positions.copy()
        self._sinr_user_positions = self.user_positions.copy()
        self._sinr_unavailable = np.asarray(
            [self._is_uav_unavailable(index) for index in range(self.n_uavs)],
            dtype=bool,
        )

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
