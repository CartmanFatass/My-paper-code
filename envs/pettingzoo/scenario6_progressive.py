import copy
import numpy as np

from envs.pettingzoo.scenario_base import UAVForcedRelayEnv


class _ProgressiveConfigProxy:
    """Read-through config wrapper with scenario-profile overrides."""

    def __init__(self, base_config, overrides):
        self._base_config = base_config
        self._overrides = dict(overrides)

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        if self._base_config is not None:
            return getattr(self._base_config, name)
        raise AttributeError(name)


class UAVProgressiveRelayEnv(UAVForcedRelayEnv):
    """
    Scenario 6: progressive forced-relay benchmark.

    This environment reuses scenario_base dynamics and adds staged difficulty
    profiles, BS capacity limits, user demand heterogeneity, BS failures, and a
    demand-aware coverage-balance reward.
    """

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "uav_progressive_relay_env_v0",
        "is_parallelizable": True,
    }

    VALID_STAGES = {f"S{i}" for i in range(11)}

    def __init__(self, config=None, scale_mode=None, **kwargs):
        stage = kwargs.pop("progressive_stage", None)
        if stage is None and config is not None:
            stage = getattr(config, "progressive_stage", "S0")
        stage = str(stage or "S0").upper()
        if stage not in self.VALID_STAGES:
            raise ValueError(f"Unknown progressive_stage '{stage}'. Expected one of {sorted(self.VALID_STAGES)}.")
        self.progressive_stage = stage

        if scale_mode is None:
            scale_mode = kwargs.pop("scale_mode", None)
        if scale_mode is None and config is not None:
            scale_mode = getattr(config, "progressive_scale_mode", "train")
        scale_mode = str(scale_mode or "train").lower()

        base_overrides = self._build_profile_overrides(stage, scale_mode, config)
        base_overrides.update(kwargs)

        # Scenario6 owns its default reward. Use scenario6_reward_type to select
        # another reward without inheriting scenario4 config defaults accidentally.
        reward_type = None
        if config is not None:
            reward_type = getattr(config, "scenario6_reward_type", None)
        reward_type = kwargs.get("reward_type", reward_type)
        base_overrides["reward_type"] = reward_type or "progressive_coverage_balance"

        proxy = _ProgressiveConfigProxy(config, base_overrides)
        super().__init__(config=proxy, render_mode=kwargs.get("render_mode", None), seed=kwargs.get("seed", None))

        self.scale_mode = scale_mode
        self.progressive_max_agents = int(getattr(proxy, "progressive_max_agents", 6))
        self.progressive_max_users = int(getattr(proxy, "progressive_max_users", 30))
        self.progressive_max_ground_bs = max(
            3,
            self.n_ground_bs,
            int(getattr(proxy, "progressive_max_ground_bs", max(2, self.n_ground_bs))),
        )

        self.default_user_demand_mbps = float(getattr(proxy, "default_user_demand_mbps", 2.0))
        self.user_demand_model = getattr(proxy, "user_demand_model", "homogeneous")
        self.user_demand_lognormal_mean = float(getattr(proxy, "user_demand_lognormal_mean", 0.0))
        self.user_demand_lognormal_sigma = float(getattr(proxy, "user_demand_lognormal_sigma", 0.75))
        self.user_demand_min_mbps = float(getattr(proxy, "user_demand_min_mbps", 0.5))
        self.user_demand_max_mbps = float(getattr(proxy, "user_demand_max_mbps", 8.0))

        self.ground_bs_capacity_mbps = self._normalize_bs_capacities(
            getattr(proxy, "ground_bs_capacity_mbps", None)
        )
        self.bs_capacity_skew_enabled = bool(getattr(proxy, "bs_capacity_skew_enabled", False))
        self.bs_failure_enabled = bool(getattr(proxy, "bs_failure_enabled", False))
        self.bs_failure_probability = float(getattr(proxy, "bs_failure_probability", 0.0))
        self.bs_failure_duration_range = tuple(getattr(proxy, "bs_failure_duration_range", (30, 80)))

        self.hotspot_mobility_enabled = bool(getattr(proxy, "hotspot_mobility_enabled", False))
        self.hotspot_path_mode = str(getattr(proxy, "hotspot_path_mode", "linear")).lower()
        self.hotspot_speed_mps = float(getattr(proxy, "hotspot_speed_mps", 8.0))
        self.hotspot_high_demand_ratio = float(getattr(proxy, "hotspot_high_demand_ratio", 0.35))
        self.hotspot_cluster_count = int(getattr(proxy, "hotspot_cluster_count", max(3, self.n_clusters)))
        self.hotspot_moving_cluster_count = int(getattr(proxy, "hotspot_moving_cluster_count", 2))
        self.hotspot_std = float(getattr(proxy, "hotspot_std", getattr(self, "cluster_std", 100)))

        self.relay_corridor_enabled = bool(getattr(proxy, "relay_corridor_enabled", False))
        self.relay_corridor_width = float(getattr(proxy, "relay_corridor_width", 450.0))
        self.corridor_loss_penalty_db = float(getattr(proxy, "corridor_loss_penalty_db", 0.0))
        self.off_corridor_loss_penalty_db = float(getattr(proxy, "off_corridor_loss_penalty_db", 12.0))

        self.ground_bs_active = np.ones(self.n_ground_bs, dtype=bool)
        self.ground_bs_failure_timers = np.zeros(self.n_ground_bs, dtype=int)
        self.user_demands_mbps = np.full(self.n_users, self.default_user_demand_mbps, dtype=float)
        self.user_throughputs_mbps = np.zeros(self.n_users, dtype=float)
        self.uav_served_throughput_mbps = np.zeros(self.n_uavs, dtype=float)
        self.uav_served_demand_mbps = np.zeros(self.n_uavs, dtype=float)
        self.ground_bs_requested_mbps = np.zeros(self.n_ground_bs, dtype=float)
        self.ground_bs_allocated_mbps = np.zeros(self.n_ground_bs, dtype=float)
        self.ground_bs_remaining_capacity_mbps = np.zeros(self.n_ground_bs, dtype=float)
        self.demand_satisfaction_ratio = 0.0
        self.capacity_limited_throughput_mbps = 0.0
        self.bs_load_jain_score = 0.0

        self.hotspot_centers = np.zeros((0, 2), dtype=float)
        self.hotspot_start_centers = np.zeros((0, 2), dtype=float)
        self.hotspot_target_centers = np.zeros((0, 2), dtype=float)
        self.hotspot_cluster_velocities = np.zeros((0, 2), dtype=float)
        self.hotspot_user_offsets = np.zeros((self.n_users, 2), dtype=float)
        self.hotspot_user_mask = np.zeros(self.n_users, dtype=bool)
        self.hotspot_moving_cluster_mask = np.zeros(0, dtype=bool)

        self.state_dim = (
            self.progressive_max_agents * 3
            + self.progressive_max_agents
            + self.progressive_max_users * 6
            + self.progressive_max_ground_bs * 3
            + 1
        )

    @staticmethod
    def _build_profile_overrides(stage, scale_mode, config):
        overrides = {
            "progressive_max_agents": getattr(config, "progressive_max_agents", 6) if config else 6,
            "progressive_max_users": getattr(config, "progressive_max_users", 30) if config else 30,
            "progressive_max_ground_bs": max(3, getattr(config, "progressive_max_ground_bs", 3)) if config else 3,
            "max_observed_bs": max(3, getattr(config, "max_observed_bs", 3)) if config else 3,
            "default_user_demand_mbps": 2.0,
            "user_demand_model": "homogeneous",
            "ground_bs_capacity_mbps": None,
            "bs_capacity_skew_enabled": False,
            "bs_failure_enabled": False,
            "bs_failure_probability": 0.0,
            "bs_failure_duration_range": (30, 80),
            "hotspot_mobility_enabled": False,
            "hotspot_path_mode": "linear",
            "hotspot_speed_mps": 8.0,
            "hotspot_high_demand_ratio": 0.35,
            "relay_corridor_enabled": False,
            "relay_corridor_width": 450.0,
            "corridor_loss_penalty_db": 0.0,
            "off_corridor_loss_penalty_db": 12.0,
            "user_distribution": "uniform",
            "randomize_users": True,
            "randomize_bs": False,
            "n_agents": 6,
            "n_users": 30,
            "n_ground_bs": 1,
            "n_remote_clusters": 0,
        }

        if stage in {"S1", "S2", "S3"}:
            overrides["randomize_bs"] = True
        if stage == "S2":
            overrides["ground_bs_capacity_mbps"] = [80.0]
        elif stage == "S3":
            overrides.update({"n_agents": 6, "max_hops": 5, "randomize_bs": True})
        elif stage in {"S4", "S5", "S6"}:
            overrides.update({
                "user_distribution": "forced_relay_cluster",
                "randomize_bs": True,
                "n_clusters": 4,
                "n_remote_clusters": 1,
                "cluster_std": 120,
            })
            if stage in {"S5", "S6"}:
                overrides["user_demand_model"] = "lognormal"
            if stage == "S6":
                overrides.update({
                    "n_ground_bs": 2,
                    "ground_bs_capacity_mbps": [80.0, 80.0],
                    "bs_failure_enabled": True,
                    "bs_failure_probability": 0.002,
                    "bs_failure_duration_range": (30, 80),
                })
        elif stage == "S7":
            if getattr(config, "progressive_fixed_agent_count", False):
                fixed_agents = int(getattr(config, "progressive_s7_agents", overrides["progressive_max_agents"]))
                if scale_mode == "eval":
                    overrides.update({"n_agents": fixed_agents, "n_users": 30})
                else:
                    overrides.update({"n_agents": fixed_agents, "n_users": 30})
            elif scale_mode == "eval":
                overrides.update({"n_agents": 6, "n_users": 30})
            else:
                overrides.update({"n_agents": 6, "n_users": 30})
            overrides.update({
                "user_distribution": "forced_relay_cluster",
                "randomize_bs": True,
                "n_clusters": 4,
                "n_remote_clusters": 1,
                "cluster_std": 120,
                "user_demand_model": "lognormal",
            })
        elif stage == "S8":
            overrides.update({
                "user_distribution": "dynamic_hotspot_cluster",
                "user_movement_model": "stationary",
                "randomize_bs": True,
                "n_clusters": 4,
                "n_remote_clusters": 1,
                "cluster_std": 100,
                "hotspot_mobility_enabled": True,
                "hotspot_path_mode": "linear",
                "hotspot_speed_mps": 8.0,
                "hotspot_high_demand_ratio": 0.35,
                "hotspot_cluster_count": 4,
                "hotspot_moving_cluster_count": 2,
                "hotspot_std": 95,
                "user_demand_model": "lognormal",
            })
        elif stage == "S9":
            overrides.update({
                "user_distribution": "forced_relay_cluster",
                "randomize_bs": False,
                "n_ground_bs": 3,
                "progressive_max_ground_bs": max(
                    3, getattr(config, "progressive_max_ground_bs", 3) if config else 3
                ),
                "max_observed_bs": max(3, getattr(config, "max_observed_bs", 3) if config else 3),
                "n_clusters": 4,
                "n_remote_clusters": 1,
                "cluster_std": 120,
                "user_demand_model": "lognormal",
                "ground_bs_capacity_mbps": [40.0, 80.0, 140.0],
                "bs_capacity_skew_enabled": True,
                "bs_failure_enabled": False,
            })
        elif stage == "S10":
            overrides.update({
                "user_distribution": "coverage_hole",
                "randomize_bs": False,
                "n_ground_bs": 1,
                "n_clusters": 4,
                "n_remote_clusters": 2,
                "cluster_std": 110,
                "remote_cluster_std": 130,
                "user_demand_model": "lognormal",
                "relay_corridor_enabled": True,
                "relay_corridor_width": 450.0,
                "corridor_loss_penalty_db": 0.0,
                "off_corridor_loss_penalty_db": 12.0,
                "max_hops": 5,
            })

        return overrides

    def _normalize_bs_capacities(self, capacities):
        if capacities is None:
            return np.full(self.n_ground_bs, np.inf, dtype=float)
        if np.isscalar(capacities):
            return np.full(self.n_ground_bs, float(capacities), dtype=float)
        values = np.array(list(capacities), dtype=float)
        if len(values) < self.n_ground_bs:
            pad_value = values[-1] if len(values) > 0 else np.inf
            values = np.pad(values, (0, self.n_ground_bs - len(values)), constant_values=pad_value)
        return values[:self.n_ground_bs]

    def _init_ground_bs(self):
        if getattr(self, "progressive_stage", None) == "S9":
            self.ground_bs_positions = np.zeros((self.n_ground_bs, 3), dtype=float)
            layout = np.array([
                [0.14, 0.14, 30.0],  # near, low capacity
                [0.55, 0.12, 30.0],  # mid-range, medium capacity
                [0.92, 0.92, 30.0],  # far, high capacity
            ], dtype=float)

            for idx in range(self.n_ground_bs):
                if idx < len(layout):
                    self.ground_bs_positions[idx] = [
                        layout[idx, 0] * self.area_size,
                        layout[idx, 1] * self.area_size,
                        layout[idx, 2],
                    ]
                else:
                    edge_pos = 0.08 + 0.84 * ((idx - len(layout) + 1) / max(1, self.n_ground_bs - len(layout) + 1))
                    self.ground_bs_positions[idx] = [edge_pos * self.area_size, self.area_size * 0.95, 30.0]
            return

        super()._init_ground_bs()

    def _generate_user_positions(self):
        if not getattr(self, "hotspot_mobility_enabled", False):
            return super()._generate_user_positions()
        return self._generate_dynamic_hotspot_positions()

    def _generate_dynamic_hotspot_positions(self):
        user_positions = np.zeros((self.n_users, 3), dtype=float)
        cluster_count = max(1, min(int(self.n_clusters), int(self.hotspot_cluster_count)))
        moving_count = int(np.clip(self.hotspot_moving_cluster_count, 1, cluster_count))

        bs_center = (
            np.mean(self.ground_bs_positions[:, :2], axis=0)
            if self.n_ground_bs > 0 and hasattr(self, "ground_bs_positions")
            else np.array([self.area_size * 0.05, self.area_size * 0.05])
        )
        remote_corner = self._remote_corner_from_point(bs_center)

        centers = np.zeros((cluster_count, 2), dtype=float)
        starts = np.zeros_like(centers)
        targets = np.zeros_like(centers)
        moving_mask = np.zeros(cluster_count, dtype=bool)

        for cluster_idx in range(cluster_count):
            if cluster_idx < moving_count:
                side_y = (0.25 + 0.50 * (cluster_idx / max(1, moving_count - 1))) * self.area_size
                start_x = self.area_size * (0.18 if bs_center[0] < self.area_size / 2 else 0.82)
                start = np.array([start_x, side_y], dtype=float)
                target_offset = self.np_random.uniform(-0.08, 0.08, size=2) * self.area_size
                target = np.clip(remote_corner + target_offset, self.area_size * 0.08, self.area_size * 0.92)
                moving_mask[cluster_idx] = True
            else:
                central = self.area_size * self.np_random.uniform(0.30, 0.70, size=2)
                start = central
                target = central
            centers[cluster_idx] = start
            starts[cluster_idx] = start
            targets[cluster_idx] = target

        self.hotspot_centers = centers
        self.hotspot_start_centers = starts
        self.hotspot_target_centers = targets
        self.hotspot_moving_cluster_mask = moving_mask
        self.hotspot_cluster_velocities = np.zeros((cluster_count, 2), dtype=float)
        self.hotspot_user_offsets = np.zeros((self.n_users, 2), dtype=float)
        self.hotspot_user_mask = np.zeros(self.n_users, dtype=bool)
        self._refresh_hotspot_cluster_velocities()

        base_users_per_cluster = self.n_users // cluster_count
        remaining_users = self.n_users % cluster_count
        cluster_user_counts = [base_users_per_cluster] * cluster_count
        for idx in range(remaining_users):
            cluster_user_counts[idx] += 1

        user_idx = 0
        for cluster_idx, count in enumerate(cluster_user_counts):
            for _ in range(count):
                offset = self.np_random.normal(0.0, self.hotspot_std, size=2)
                pos_2d = np.clip(centers[cluster_idx] + offset, 10, self.area_size - 10)
                user_positions[user_idx] = [pos_2d[0], pos_2d[1], 1.5]
                self.hotspot_user_offsets[user_idx] = pos_2d - centers[cluster_idx]
                self.user_cluster_assignments[user_idx] = cluster_idx
                self.hotspot_user_mask[user_idx] = bool(moving_mask[cluster_idx])
                user_idx += 1

        if self.cluster_centers_history.shape[0] >= cluster_count:
            self.cluster_centers_history[:cluster_count] = centers

        return user_positions

    def _move_users(self):
        if not getattr(self, "hotspot_mobility_enabled", False):
            return super()._move_users()
        self._move_hotspot_users()

    def _move_hotspot_users(self):
        if self.hotspot_centers.size == 0:
            self.user_positions = self._generate_dynamic_hotspot_positions()
            return

        previous_centers = self.hotspot_centers.copy()
        moving_indices = np.where(self.hotspot_moving_cluster_mask)[0]
        for cluster_idx in moving_indices:
            current = self.hotspot_centers[cluster_idx]
            target = self.hotspot_target_centers[cluster_idx]
            direction = target - current
            distance = np.linalg.norm(direction)
            max_step = self.hotspot_speed_mps * self.time_step

            if distance <= max_step:
                self.hotspot_centers[cluster_idx] = target
                if self.hotspot_path_mode == "waypoint":
                    self.hotspot_target_centers[cluster_idx] = self.np_random.uniform(
                        self.area_size * 0.12,
                        self.area_size * 0.88,
                        size=2,
                    )
            elif distance > 1e-8:
                self.hotspot_centers[cluster_idx] = current + (direction / distance) * max_step

        self._refresh_hotspot_cluster_velocities(previous_centers=previous_centers)
        self._apply_hotspot_user_positions()

    def _refresh_hotspot_cluster_velocities(self, previous_centers=None):
        if self.hotspot_centers.size == 0:
            return
        if previous_centers is not None:
            self.hotspot_cluster_velocities = (self.hotspot_centers - previous_centers) / max(self.time_step, 1e-8)
            return

        self.hotspot_cluster_velocities = np.zeros_like(self.hotspot_centers)
        moving_indices = np.where(self.hotspot_moving_cluster_mask)[0]
        for cluster_idx in moving_indices:
            direction = self.hotspot_target_centers[cluster_idx] - self.hotspot_centers[cluster_idx]
            distance = np.linalg.norm(direction)
            if distance > 1e-8:
                self.hotspot_cluster_velocities[cluster_idx] = (direction / distance) * self.hotspot_speed_mps

    def _apply_hotspot_user_positions(self):
        if self.hotspot_centers.size == 0:
            return
        for user_idx in range(self.n_users):
            cluster_idx = int(self.user_cluster_assignments[user_idx])
            cluster_idx = int(np.clip(cluster_idx, 0, len(self.hotspot_centers) - 1))
            pos_2d = np.clip(
                self.hotspot_centers[cluster_idx] + self.hotspot_user_offsets[user_idx],
                10,
                self.area_size - 10,
            )
            self.user_positions[user_idx, :2] = pos_2d
            self.user_positions[user_idx, 2] = 1.5
            self.user_velocities[user_idx, :2] = self.hotspot_cluster_velocities[cluster_idx]
            self.user_velocities[user_idx, 2] = 0.0

        cluster_count = min(len(self.hotspot_centers), self.cluster_centers_history.shape[0])
        if cluster_count > 0:
            self.cluster_centers_history[:cluster_count] = self.hotspot_centers[:cluster_count]

    def _remote_corner_from_point(self, point):
        area_center = self.area_size / 2
        x = self.area_size * (0.92 if point[0] < area_center else 0.08)
        y = self.area_size * (0.92 if point[1] < area_center else 0.08)
        return np.array([x, y], dtype=float)

    def reset(self, seed=None, options=None):
        self.ground_bs_active = np.ones(self.n_ground_bs, dtype=bool)
        self.ground_bs_failure_timers = np.zeros(self.n_ground_bs, dtype=int)
        self.ground_bs_remaining_capacity_mbps = self._initial_remaining_capacities()
        observations, infos = super().reset(seed=seed, options=options)
        self._init_user_demands()
        if self.hotspot_mobility_enabled:
            self._apply_hotspot_high_demands()
            self._apply_hotspot_user_positions()
        self.user_throughputs_mbps = np.zeros(self.n_users, dtype=float)
        self.uav_served_throughput_mbps = np.zeros(self.n_uavs, dtype=float)
        self.uav_served_demand_mbps = np.zeros(self.n_uavs, dtype=float)
        self.ground_bs_requested_mbps = np.zeros(self.n_ground_bs, dtype=float)
        self.ground_bs_allocated_mbps = np.zeros(self.n_ground_bs, dtype=float)
        self.demand_satisfaction_ratio = 0.0
        self.capacity_limited_throughput_mbps = 0.0
        self.bs_load_jain_score = 0.0

        current_state = self._get_state()
        self.state = current_state
        for agent in self.agents:
            infos[agent]["state"] = current_state.copy()
            infos[agent]["progressive_stage"] = self.progressive_stage
            infos[agent]["scale_mode"] = self.scale_mode
        return observations, infos

    def step(self, actions):
        self._update_bs_failures()
        observations, rewards, terminations, truncations, infos = super().step(actions)

        if self.reward_type in {"progressive_coverage_balance", "coverage_balance"}:
            reward, components = self._calculate_selected_balance_reward()
            for agent in self.agents:
                rewards[agent] = reward
                if agent in infos and "reward_info" in infos[agent]:
                    infos[agent]["reward_info"].update(components)
                    infos[agent]["reward_info"].update(self._progressive_metrics_dict())

        for agent in self.agents:
            if agent in infos:
                infos[agent]["progressive_stage"] = self.progressive_stage
                infos[agent]["scale_mode"] = self.scale_mode
                if "reward_info" in infos[agent]:
                    infos[agent]["reward_info"].update(self._progressive_metrics_dict())

        return observations, rewards, terminations, truncations, infos

    def _init_user_demands(self):
        if self.user_demand_model == "lognormal":
            demands = self.np_random.lognormal(
                mean=self.user_demand_lognormal_mean,
                sigma=self.user_demand_lognormal_sigma,
                size=self.n_users,
            ) * self.default_user_demand_mbps
            self.user_demands_mbps = np.clip(
                demands, self.user_demand_min_mbps, self.user_demand_max_mbps
            ).astype(float)
        else:
            self.user_demands_mbps = np.full(self.n_users, self.default_user_demand_mbps, dtype=float)

    def _apply_hotspot_high_demands(self):
        if not self.hotspot_mobility_enabled or self.n_users <= 0:
            return

        target_count = int(np.ceil(self.n_users * np.clip(self.hotspot_high_demand_ratio, 0.0, 1.0)))
        if target_count <= 0:
            self.hotspot_user_mask[:] = False
            return

        candidate_users = np.where(self.hotspot_user_mask)[0]
        if len(candidate_users) < target_count:
            remaining = np.setdiff1d(np.arange(self.n_users), candidate_users, assume_unique=True)
            candidate_users = np.concatenate([candidate_users, remaining])

        selected_users = candidate_users[:target_count]
        self.hotspot_user_mask[:] = False
        self.hotspot_user_mask[selected_users] = True

        high_demand = min(self.user_demand_max_mbps, self.default_user_demand_mbps * 3.0)
        self.user_demands_mbps[selected_users] = np.maximum(self.user_demands_mbps[selected_users], high_demand)

    def _initial_remaining_capacities(self):
        remaining = np.zeros(self.n_ground_bs, dtype=float)
        for idx, cap in enumerate(self.ground_bs_capacity_mbps):
            remaining[idx] = -1.0 if np.isinf(cap) else cap
        return remaining

    def _update_bs_failures(self):
        if not self.bs_failure_enabled:
            self.ground_bs_active[:] = True
            return

        low, high = self.bs_failure_duration_range
        for bs_idx in range(self.n_ground_bs):
            if self.ground_bs_failure_timers[bs_idx] > 0:
                self.ground_bs_failure_timers[bs_idx] -= 1

            if self.ground_bs_failure_timers[bs_idx] > 0:
                self.ground_bs_active[bs_idx] = False
                continue

            self.ground_bs_active[bs_idx] = True
            if self.np_random.random_sample() < self.bs_failure_probability:
                self.ground_bs_failure_timers[bs_idx] = int(self.np_random.randint(low, high + 1))
                self.ground_bs_active[bs_idx] = False

    def _get_link_capacity(self, node1_type, node1_idx, node2_type, node2_idx):
        if node1_type == "ground_bs" and not self.ground_bs_active[node1_idx]:
            return 0
        if node2_type == "ground_bs" and not self.ground_bs_active[node2_idx]:
            return 0
        capacity = super()._get_link_capacity(node1_type, node1_idx, node2_type, node2_idx)
        if capacity <= 0:
            return capacity

        penalty_db = self._corridor_link_penalty_db(node1_type, node1_idx, node2_type, node2_idx)
        if penalty_db <= 0:
            return capacity
        return capacity * (10 ** (-penalty_db / 10.0))

    def _corridor_link_penalty_db(self, node1_type, node1_idx, node2_type, node2_idx):
        if not self.relay_corridor_enabled:
            return 0.0
        if node1_type not in {"uav", "ground_bs"} or node2_type not in {"uav", "ground_bs"}:
            return 0.0

        pos1 = self._node_position_for_corridor(node1_type, node1_idx)
        pos2 = self._node_position_for_corridor(node2_type, node2_idx)
        if pos1 is None or pos2 is None:
            return 0.0

        mid = (pos1[:2] + pos2[:2]) / 2.0
        half_width = max(1e-6, self.relay_corridor_width / 2.0)
        distances = [
            self._distance_to_relay_corridor(pos1[:2]),
            self._distance_to_relay_corridor(pos2[:2]),
            self._distance_to_relay_corridor(mid),
        ]
        if max(distances) <= half_width:
            return self.corridor_loss_penalty_db
        return self.off_corridor_loss_penalty_db

    def _node_position_for_corridor(self, node_type, node_idx):
        if node_type == "uav" and 0 <= node_idx < self.n_uavs:
            return self.uav_positions[node_idx]
        if node_type == "ground_bs" and 0 <= node_idx < self.n_ground_bs:
            return self.ground_bs_positions[node_idx]
        return None

    def _distance_to_relay_corridor(self, point_2d):
        start, end = self._relay_corridor_endpoints()
        segment = end - start
        seg_len_sq = float(np.dot(segment, segment))
        if seg_len_sq <= 1e-8:
            return float(np.linalg.norm(point_2d - start))
        t = float(np.clip(np.dot(point_2d - start, segment) / seg_len_sq, 0.0, 1.0))
        projection = start + t * segment
        return float(np.linalg.norm(point_2d - projection))

    def _relay_corridor_endpoints(self):
        if self.n_ground_bs > 0 and hasattr(self, "ground_bs_positions"):
            start = self.ground_bs_positions[0, :2].astype(float)
        else:
            start = np.array([self.area_size * 0.05, self.area_size * 0.05], dtype=float)
        end = self._remote_corner_from_point(start)
        return start, end

    def _calculate_system_throughput(self):
        records = []
        bs_requested = np.zeros(self.n_ground_bs, dtype=float)

        self.user_throughputs_mbps = np.zeros(self.n_users, dtype=float)
        self.uav_served_throughput_mbps = np.zeros(self.n_uavs, dtype=float)
        self.uav_served_demand_mbps = np.zeros(self.n_uavs, dtype=float)

        for uav_idx, (path, bottleneck_capacity) in self.routing_paths.items():
            bs_idx = self._path_terminal_bs(path)
            if bs_idx is None or not self.ground_bs_active[bs_idx]:
                continue

            connected_users = np.where(self.connections[uav_idx])[0]
            if len(connected_users) == 0:
                continue

            frontend_capacity = self._compute_uav_frontend_capacity(uav_idx, connected_users)
            physical_mbps = min(frontend_capacity, bottleneck_capacity) / 1e6
            demand_mbps = float(np.sum(self.user_demands_mbps[connected_users]))
            requested_mbps = max(0.0, min(physical_mbps, demand_mbps))

            records.append({
                "uav_idx": uav_idx,
                "bs_idx": bs_idx,
                "users": connected_users,
                "requested_mbps": requested_mbps,
                "demand_mbps": demand_mbps,
            })
            bs_requested[bs_idx] += requested_mbps

        bs_allocated = np.zeros(self.n_ground_bs, dtype=float)
        for bs_idx in range(self.n_ground_bs):
            if not self.ground_bs_active[bs_idx]:
                continue
            cap = self.ground_bs_capacity_mbps[bs_idx]
            bs_allocated[bs_idx] = bs_requested[bs_idx] if np.isinf(cap) else min(cap, bs_requested[bs_idx])

        for record in records:
            bs_idx = record["bs_idx"]
            requested = record["requested_mbps"]
            if requested <= 0 or bs_requested[bs_idx] <= 0:
                continue
            allocation = requested * (bs_allocated[bs_idx] / bs_requested[bs_idx])
            uav_idx = record["uav_idx"]
            users = record["users"]
            demands = self.user_demands_mbps[users]
            demand_sum = float(np.sum(demands))

            self.uav_served_throughput_mbps[uav_idx] += allocation
            self.uav_served_demand_mbps[uav_idx] += demand_sum

            if demand_sum > 0:
                user_allocations = allocation * (demands / demand_sum)
            else:
                user_allocations = np.full(len(users), allocation / len(users))
            self.user_throughputs_mbps[users] += user_allocations

        self.ground_bs_requested_mbps = bs_requested
        self.ground_bs_allocated_mbps = bs_allocated
        self.bs_load_jain_score = self._calculate_bs_load_jain(bs_allocated)

        total_throughput_mbps = float(np.sum(bs_allocated))
        served_users = int(np.sum(self.user_throughputs_mbps > 1e-9))
        avg_throughput_per_user_mbps = total_throughput_mbps / served_users if served_users > 0 else 0.0

        with np.errstate(divide="ignore", invalid="ignore"):
            satisfaction = np.minimum(
                self.user_throughputs_mbps / np.maximum(self.user_demands_mbps, 1e-8),
                1.0,
            )
        self.demand_satisfaction_ratio = float(np.mean(satisfaction)) if self.n_users > 0 else 0.0
        self.capacity_limited_throughput_mbps = total_throughput_mbps

        remaining = np.zeros(self.n_ground_bs, dtype=float)
        for bs_idx, cap in enumerate(self.ground_bs_capacity_mbps):
            if not self.ground_bs_active[bs_idx]:
                remaining[bs_idx] = 0.0
            elif np.isinf(cap):
                remaining[bs_idx] = -1.0
            else:
                remaining[bs_idx] = max(0.0, cap - bs_allocated[bs_idx])
        self.ground_bs_remaining_capacity_mbps = remaining

        if hasattr(self, "reward_info") and isinstance(self.reward_info, dict):
            self.reward_info.update(self._progressive_metrics_dict())

        return total_throughput_mbps, avg_throughput_per_user_mbps

    def _calculate_bs_load_jain(self, bs_allocated):
        if self.n_ground_bs <= 1:
            return 0.0
        loads = np.asarray(bs_allocated, dtype=float)
        finite_caps = np.asarray(self.ground_bs_capacity_mbps, dtype=float)
        finite_mask = np.isfinite(finite_caps) & (finite_caps > 0)
        if np.any(finite_mask):
            normalized = np.zeros_like(loads)
            normalized[finite_mask] = loads[finite_mask] / finite_caps[finite_mask]
            loads = normalized
        return self._jain(loads)

    @staticmethod
    def _path_terminal_bs(path):
        if not path:
            return None
        node_type, node_idx = path[-1]
        return node_idx if node_type == "ground_bs" else None

    def _calculate_selected_balance_reward(self):
        if self.reward_type == "coverage_balance":
            coverage_ratio = self.reward_info.get("coverage_ratio", 0.0) if hasattr(self, "reward_info") else 0.0
            loads = np.array([
                np.sum(self.connections[uav_idx])
                for uav_idx in self.routing_paths.keys()
            ], dtype=float)
            balance_score = self._jain(loads)
            reward = float(coverage_ratio * balance_score)
            return reward, {
                "coverage_balance_reward": reward,
                "load_balance_score": balance_score,
                "load_balance_basis": "served_user_count",
            }

        loads = self.uav_served_throughput_mbps[
            list(self.routing_paths.keys())
        ] if self.routing_paths else np.array([], dtype=float)
        balance_score = self._jain(loads)
        reward = float(self.demand_satisfaction_ratio * balance_score)
        return reward, {
            "progressive_coverage_balance_reward": reward,
            "load_balance_score": balance_score,
            "load_balance_basis": "served_throughput_mbps",
        }

    @staticmethod
    def _jain(loads):
        loads = np.asarray(loads, dtype=float)
        total = float(np.sum(loads))
        if len(loads) <= 1 or total <= 0:
            return 0.0
        score = (total ** 2) / (len(loads) * float(np.sum(loads ** 2)) + 1e-8)
        return float(np.clip(score, 0.0, 1.0))

    def _progressive_metrics_dict(self):
        reward_info = getattr(self, "reward_info", {}) if isinstance(getattr(self, "reward_info", {}), dict) else {}
        metrics = {
            "progressive_stage": self.progressive_stage,
            "scale_mode": self.scale_mode,
            "user_demands_mbps": self.user_demands_mbps.copy(),
            "ground_bs_active": self.ground_bs_active.copy(),
            "ground_bs_requested_mbps": self.ground_bs_requested_mbps.copy(),
            "ground_bs_allocated_mbps": self.ground_bs_allocated_mbps.copy(),
            "ground_bs_remaining_capacity_mbps": self.ground_bs_remaining_capacity_mbps.copy(),
            "bs_load_jain_score": self.bs_load_jain_score,
            "demand_satisfaction_ratio": self.demand_satisfaction_ratio,
            "capacity_limited_throughput_mbps": self.capacity_limited_throughput_mbps,
            "uav_served_throughput_mbps": self.uav_served_throughput_mbps.copy(),
            "uav_served_demand_mbps": self.uav_served_demand_mbps.copy(),
            "service_drop_ratio": reward_info.get("service_drop_ratio", 0.0),
            "avg_serving_backhaul_bottleneck_mbps": reward_info.get("avg_serving_backhaul_bottleneck_mbps", 0.0),
            "min_serving_backhaul_bottleneck_mbps": reward_info.get("min_serving_backhaul_bottleneck_mbps", 0.0),
            "relay_route_loss_ratio": reward_info.get("relay_route_loss_ratio", 0.0),
        }
        metrics.update(self._hotspot_metrics_dict())
        metrics.update(self._role_metrics_dict())
        metrics.update(self._corridor_metrics_dict())
        return metrics

    def _hotspot_metrics_dict(self):
        if not self.hotspot_mobility_enabled or self.n_users <= 0:
            return {
                "hotspot_coverage_ratio": 0.0,
                "hotspot_demand_satisfaction_ratio": 0.0,
                "hotspot_user_count": 0,
                "hotspot_centers": self.hotspot_centers.copy(),
            }

        mask = self.hotspot_user_mask.astype(bool)
        hotspot_count = int(np.sum(mask))
        if hotspot_count == 0:
            return {
                "hotspot_coverage_ratio": 0.0,
                "hotspot_demand_satisfaction_ratio": 0.0,
                "hotspot_user_count": 0,
                "hotspot_centers": self.hotspot_centers.copy(),
            }

        serviced = self.user_serviced_status[mask] if len(self.user_serviced_status) == self.n_users else np.zeros(hotspot_count, dtype=bool)
        with np.errstate(divide="ignore", invalid="ignore"):
            satisfaction = np.minimum(
                self.user_throughputs_mbps[mask] / np.maximum(self.user_demands_mbps[mask], 1e-8),
                1.0,
            )

        return {
            "hotspot_coverage_ratio": float(np.mean(serviced)),
            "hotspot_demand_satisfaction_ratio": float(np.mean(satisfaction)) if hotspot_count > 0 else 0.0,
            "hotspot_user_count": hotspot_count,
            "hotspot_centers": self.hotspot_centers.copy(),
        }

    def _role_metrics_dict(self):
        serving_uavs_count = 0
        pure_relay_uavs_count = 0
        weighted_serving_score = 0.0

        for uav_idx in self.routing_paths:
            user_count = int(np.sum(self.connections[uav_idx]))
            if user_count > 0:
                serving_uavs_count += 1
                weighted_serving_score += float(np.log1p(user_count))
            else:
                pure_relay_uavs_count += 1

        return {
            "serving_uavs_count": serving_uavs_count,
            "pure_relay_uavs_count": pure_relay_uavs_count,
            "weighted_serving_score": weighted_serving_score,
        }

    def _corridor_metrics_dict(self):
        if not self.relay_corridor_enabled or self.n_uavs <= 0:
            return {
                "corridor_utilization_ratio": 0.0,
                "corridor_width_m": self.relay_corridor_width,
            }

        half_width = max(1e-6, self.relay_corridor_width / 2.0)
        in_corridor = [
            self._distance_to_relay_corridor(self.uav_positions[uav_idx, :2]) <= half_width
            for uav_idx in range(self.n_uavs)
        ]
        return {
            "corridor_utilization_ratio": float(np.mean(in_corridor)),
            "corridor_width_m": self.relay_corridor_width,
        }

    def _get_observation(self, agent):
        observation = super()._get_observation(agent)
        obs = observation["obs"].copy()
        agent_idx = int(agent.split("_")[1])

        user_dim = 7 if self.predictive_handover else (6 if self.enable_soft_handover else 5)
        bs_start = (
            3
            + 3
            + 5
            + self.max_observed_users * user_dim
            + self.max_observed_uavs * 4
        )

        local_bs = self._get_local_bs(agent_idx)
        slot = 0
        for bs_idx, _ in local_bs:
            if slot >= self.max_observed_bs:
                break
            obs[bs_start + slot * 4 + 3] = self._bs_capacity_ratio(bs_idx)
            slot += 1

        if slot < self.max_observed_bs and len(self.global_bs_cache) > 0:
            observed = {bs_idx for bs_idx, _ in local_bs}
            for bs_idx in self.global_bs_cache:
                if slot >= self.max_observed_bs:
                    break
                if bs_idx in observed:
                    continue
                obs[bs_start + slot * 4 + 3] = self._bs_capacity_ratio(bs_idx)
                slot += 1

        observation["obs"] = obs
        return observation

    def _bs_capacity_ratio(self, bs_idx):
        if bs_idx >= self.n_ground_bs or not self.ground_bs_active[bs_idx]:
            return 0.0
        cap = self.ground_bs_capacity_mbps[bs_idx]
        if np.isinf(cap) or cap <= 0:
            return 1.0
        remaining = self.ground_bs_remaining_capacity_mbps[bs_idx]
        return float(np.clip(remaining / cap, 0.0, 1.0))

    def _get_state(self):
        state_components = []

        uav_positions = np.zeros((self.progressive_max_agents, 3), dtype=float)
        active_uav_positions = self.uav_positions.copy()
        active_uav_positions[:, :2] /= self.area_size
        active_uav_positions[:, 2] = (
            (active_uav_positions[:, 2] - self.height_range[0])
            / (self.height_range[1] - self.height_range[0])
        )
        uav_positions[:self.n_uavs] = active_uav_positions
        state_components.append(uav_positions.flatten())

        uav_loads = np.zeros(self.progressive_max_agents, dtype=float)
        uav_loads[:self.n_uavs] = np.sum(self.connections, axis=1) / max(self.max_connections, 1)
        state_components.append(uav_loads)

        user_info = np.zeros((self.progressive_max_users, 6), dtype=float)
        for user_idx in range(self.n_users):
            user_pos = self.user_positions[user_idx]
            user_info[user_idx, 0] = user_pos[0] / self.area_size
            user_info[user_idx, 1] = user_pos[1] / self.area_size

            user_vel = self.user_velocities[user_idx]
            speed_norm = max(self.user_max_speed, 1e-8)
            user_info[user_idx, 2] = user_vel[0] / speed_norm
            user_info[user_idx, 3] = user_vel[1] / speed_norm

            is_effectively_connected = False
            best_sinr = -np.inf
            for uav_idx in range(self.n_uavs):
                if self.connections[uav_idx, user_idx]:
                    best_sinr = max(best_sinr, self.sinr_matrix[uav_idx, user_idx])
                    if uav_idx in self.routing_paths and self.routing_paths[uav_idx][0]:
                        is_effectively_connected = True
            user_info[user_idx, 4] = 1.0 if is_effectively_connected else 0.0
            user_info[user_idx, 5] = np.clip((best_sinr + 10) / 50, 0, 1) if best_sinr > -np.inf else 0.0
        state_components.append(user_info.flatten())

        bs_positions = np.zeros((self.progressive_max_ground_bs, 3), dtype=float)
        normalized_bs = self.ground_bs_positions.copy()
        normalized_bs[:, :2] /= self.area_size
        normalized_bs[:, 2] /= self.height_range[1]
        bs_positions[:self.n_ground_bs] = normalized_bs
        state_components.append(bs_positions.flatten())

        state_components.append(np.array([self.current_step / self.max_steps], dtype=float))
        return np.concatenate(state_components)

    def get_current_state(self):
        state = super().get_current_state()
        state.update({
            "progressive_stage": self.progressive_stage,
            "scale_mode": self.scale_mode,
            "ground_bs_active": self.ground_bs_active.copy(),
            "user_demands_mbps": self.user_demands_mbps.copy(),
        })
        return state
