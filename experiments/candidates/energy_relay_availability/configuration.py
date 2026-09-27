"""Fixed S7-S4 construction and ordinary H1 availability adaptation."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from configs.config_1 import Config
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from experiments.candidates.energy_relay_benchmark.b01.evaluation import HeuristicController
from experiments.candidates.energy_relay_benchmark.b01.heuristic import LayoutHeuristic, variant
from experiments.candidates.energy_relay_benchmark.b01.observation import own_energy
from hmasd.baselines import apply_algorithm_config


HORIZON = 3000
CONTROLLERS = ("H_local", "H_central")


def make_config(horizon: int = HORIZON) -> Config:
    """S4 equivalent of the standard one-lane S7 evaluation switches."""
    config = Config("S7-S4")
    config.num_envs = 1
    config.rollout_length = int(horizon)
    config.episode_length = int(horizon)
    config.max_steps = int(horizon)
    config.k = 10
    config.scenario7_comparison_gate_enabled = False
    config.scenario7_run_physical_feasibility_check = False
    config.seed = 0  # Environment reset receives each fixed world seed.
    config.total_timesteps = int(horizon)
    apply_algorithm_config(config, "hmasd")
    if config.energy_stage != "S4" or config.lambda_return != 2.0 or config.use_obsnorm or config.use_statenorm:
        raise ValueError("unexpected S4 native evaluation configuration")
    return config


def make_env(config: Config, seed: int, fault_on: bool) -> ParallelToArrayAdapter:
    # S4 profile overwrites config-level failure switches; constructor kwargs are applied last.
    raw = UAVEnergyAwareRelayEnv(
        config=config, seed=int(seed), uav_failure_enabled=bool(fault_on),
        uav_failure_probability=0.001 if fault_on else 0.0,
    )
    expected = {
        "energy_stage": "S4", "n_uavs": 8, "n_users": 30, "n_ground_bs": 1,
        "n_charging_stations": 2, "user_movement_model": "rpgm",
        "user_max_speed": 8.0, "cluster_migration_speed": 10.0,
        "cluster_pause_time_range": (0, 3), "user_pause_time_range": (0, 2),
        "battery_capacity_wh": 160.0, "uav_failure_duration_range": (20, 60),
        "uav_failure_min_active": 6, "max_steps": int(config.max_steps),
    }
    try:
        for key, value in expected.items():
            actual = getattr(raw, key)
            if isinstance(value, tuple):
                actual = tuple(actual)
            if actual != value:
                raise ValueError(f"effective S4 {key}: {actual!r} != {value!r}")
        if (raw.failure_enabled != bool(fault_on)
                or raw.uav_failure_probability != (0.001 if fault_on else 0.0)
                or not np.array_equal(raw.charging_station_capacity[:2], [1, 1])):
            raise ValueError("effective S4 fault or station switches disagree with panel")
        env = ParallelToArrayAdapter(raw)
        if (env.n_uavs, env.obs_dim, env.action_space.shape) != (8, 365, (8, 4)):
            raise ValueError("S4 array adapter shape differs from H1 contract")
        return env
    except BaseException:
        raw.close()
        raise


class AvailableLayoutHeuristic(LayoutHeuristic):
    """Use legal availability only at H1's scheduled 30-step target replans."""

    def plan(self, observations, modes, plan_inputs=None):
        available = own_energy(observations, self.layout)["available"]
        if available.shape != (self.params.n_uavs,):
            raise ValueError("legal availability shape changed")
        return super().plan(observations, np.asarray(modes, dtype=bool) | ~available,
                            plan_inputs)


class AvailableH1Controller(HeuristicController):
    def __init__(self, information: str, env=None):
        if information not in ("local", "central"):
            raise ValueError("information must be local or central")
        super().__init__(variant("H1", information=information), env)
        self.heuristic = AvailableLayoutHeuristic(self.heuristic.params)
