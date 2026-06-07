import copy
import numpy as np

from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv


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

    This environment reuses scenario4_discrete dynamics and adds staged difficulty
    profiles, BS capacity limits, user demand heterogeneity, BS failures, and a
    demand-aware coverage-balance reward.
    """

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "uav_progressive_relay_env_v0",
        "is_parallelizable": True,
    }

    VALID_STAGES = {f"S{i}" for i in range(8)}

    def __init__(self, config=None, scale_mode=None, **kwargs):
        stage = kwargs.pop("progressive_stage", None)
        if stage is None and config is not None:
            stage = getattr(config, "progressive_stage", "S0")
        stage = str(stage or "S0").upper()
        if stage not in self.VALID_STAGES:
            raise ValueError(f"Unknown progressive_stage '{stage}'. Expected one of {sorted(self.VALID_STAGES)}.")

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

        self.progressive_stage = stage
        self.scale_mode = scale_mode
        self.progressive_max_agents = int(getattr(proxy, "progressive_max_agents", 12))
        self.progressive_max_users = int(getattr(proxy, "progressive_max_users", 80))
        self.progressive_max_ground_bs = int(getattr(proxy, "progressive_max_ground_bs", 2))

        self.default_user_demand_mbps = float(getattr(proxy, "default_user_demand_mbps", 2.0))
        self.user_demand_model = getattr(proxy, "user_demand_model", "homogeneous")
        self.user_demand_lognormal_mean = float(getattr(proxy, "user_demand_lognormal_mean", 0.0))
        self.user_demand_lognormal_sigma = float(getattr(proxy, "user_demand_lognormal_sigma", 0.75))
        self.user_demand_min_mbps = float(getattr(proxy, "user_demand_min_mbps", 0.5))
        self.user_demand_max_mbps = float(getattr(proxy, "user_demand_max_mbps", 8.0))

        self.ground_bs_capacity_mbps = self._normalize_bs_capacities(
            getattr(proxy, "ground_bs_capacity_mbps", None)
        )
        self.bs_failure_enabled = bool(getattr(proxy, "bs_failure_enabled", False))
        self.bs_failure_probability = float(getattr(proxy, "bs_failure_probability", 0.0))
        self.bs_failure_duration_range = tuple(getattr(proxy, "bs_failure_duration_range", (30, 80)))

        self.ground_bs_active = np.ones(self.n_ground_bs, dtype=bool)
        self.ground_bs_failure_timers = np.zeros(self.n_ground_bs, dtype=int)
        self.user_demands_mbps = np.full(self.n_users, self.default_user_demand_mbps, dtype=float)
        self.user_throughputs_mbps = np.zeros(self.n_users, dtype=float)
        self.uav_served_throughput_mbps = np.zeros(self.n_uavs, dtype=float)
        self.uav_served_demand_mbps = np.zeros(self.n_uavs, dtype=float)
        self.ground_bs_remaining_capacity_mbps = np.zeros(self.n_ground_bs, dtype=float)
        self.demand_satisfaction_ratio = 0.0
        self.capacity_limited_throughput_mbps = 0.0

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
            "progressive_max_agents": getattr(config, "progressive_max_agents", 12) if config else 12,
            "progressive_max_users": getattr(config, "progressive_max_users", 80) if config else 80,
            "progressive_max_ground_bs": getattr(config, "progressive_max_ground_bs", 2) if config else 2,
            "default_user_demand_mbps": 2.0,
            "user_demand_model": "homogeneous",
            "ground_bs_capacity_mbps": None,
            "bs_failure_enabled": False,
            "bs_failure_probability": 0.0,
            "bs_failure_duration_range": (30, 80),
            "user_distribution": "uniform",
            "randomize_users": True,
            "randomize_bs": False,
            "n_agents": 12,
            "n_users": 80,
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
            if scale_mode == "eval":
                overrides.update({"n_agents": 12, "n_users": 80})
            else:
                overrides.update({"n_agents": 6, "n_users": 40})
            overrides.update({
                "user_distribution": "forced_relay_cluster",
                "randomize_bs": True,
                "n_clusters": 4,
                "n_remote_clusters": 1,
                "cluster_std": 120,
                "user_demand_model": "lognormal",
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

    def reset(self, seed=None, options=None):
        self.ground_bs_active = np.ones(self.n_ground_bs, dtype=bool)
        self.ground_bs_failure_timers = np.zeros(self.n_ground_bs, dtype=int)
        self.ground_bs_remaining_capacity_mbps = self._initial_remaining_capacities()
        observations, infos = super().reset(seed=seed, options=options)
        self._init_user_demands()
        self.user_throughputs_mbps = np.zeros(self.n_users, dtype=float)
        self.uav_served_throughput_mbps = np.zeros(self.n_uavs, dtype=float)
        self.uav_served_demand_mbps = np.zeros(self.n_uavs, dtype=float)
        self.demand_satisfaction_ratio = 0.0
        self.capacity_limited_throughput_mbps = 0.0

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
        return super()._get_link_capacity(node1_type, node1_idx, node2_type, node2_idx)

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
        return {
            "progressive_stage": self.progressive_stage,
            "scale_mode": self.scale_mode,
            "user_demands_mbps": self.user_demands_mbps.copy(),
            "ground_bs_active": self.ground_bs_active.copy(),
            "ground_bs_remaining_capacity_mbps": self.ground_bs_remaining_capacity_mbps.copy(),
            "demand_satisfaction_ratio": self.demand_satisfaction_ratio,
            "capacity_limited_throughput_mbps": self.capacity_limited_throughput_mbps,
            "uav_served_throughput_mbps": self.uav_served_throughput_mbps.copy(),
            "uav_served_demand_mbps": self.uav_served_demand_mbps.copy(),
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
