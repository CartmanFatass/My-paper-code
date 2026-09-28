"""Fixed native worlds exposed as thirty-step finite-horizon PPO actions."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import time

import gymnasium as gym
import numpy as np

from experiments.candidates.energy_relay_availability.runner import _cpu_seconds, _rss_kib, _write_json
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    DOCK_REQUEST_THRESHOLD, absolute_station_xy, guard_counters, make_eval_config,
    mechanism_row, position_diagnostics, station_counts, world_row,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS, apply_feedback_params
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT, own_energy, own_positions
from experiments.candidates.uav_radio_placement.b01.runner import PlacementObserver, _plain
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_service_auxiliary.b04.evaluation import metric_row

from .constants import CLOCK, HORIZON, POLICY_SEED, lane_seeds
from .controllers import TransitionController, FEATURE_DIM
from .records import save_world


class NativeMacroEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, seeds, *, out=None, lane=0, horizon=HORIZON):
        super().__init__()
        self.seeds = tuple(map(int, seeds))
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("unique nonempty world schedule required")
        if horizon < CLOCK or horizon % CLOCK:
            raise ValueError("horizon must contain whole thirty-step decisions")
        self.horizon, self.out, self.lane = int(horizon), None if out is None else Path(out), int(lane)
        self.action_space = gym.spaces.MultiDiscrete(np.full(8, 4))
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (FEATURE_DIM,), dtype=np.float32)
        self.config = make_eval_config(self.horizon, POLICY_SEED)
        self.layout = replace(S7S2_LAYOUT, max_steps=self.horizon)
        self.started, self.cpu_started = time.monotonic(), _cpu_seconds()
        self.native = self.model_env = self.controller = self.observer = self.observer_context = None
        self.episode_index = self.native_steps = self.macro_steps = 0
        self.done, self.exhausted = True, False
        self.episodes = []
        self.features = np.zeros(FEATURE_DIM, dtype=np.float32)

    def counts(self):
        return {"lane": self.lane, "native_steps": self.native_steps,
                "macro_steps": self.macro_steps, "episodes_started": self.episode_index,
                "episodes_completed": len(self.episodes), "exhausted": self.exhausted,
                "worker_wall_seconds": time.monotonic()-self.started,
                "worker_cpu_seconds": _cpu_seconds()-self.cpu_started,
                "worker_peak_rss_kib": _rss_kib()}

    def _progress(self, status):
        if self.out is not None:
            current_finished = any(row["seed"] == getattr(self, "world_seed", None) for row in self.episodes)
            current = self.controller.work_counts() if self.controller is not None and not current_finished else {}
            _write_json(self.out / "training" / f"lane{self.lane}.progress.json", {
                **self.counts(), "status": status, "current_seed": getattr(self, "world_seed", None),
                "current_episode_steps": getattr(self, "step_index", 0),
                "current_controller_work": current,
                "completed_controller_work": {
                    field: sum(row.get(field, 0) for row in self.episodes)
                    for field in ("service_snapshot_calls", "prediction_team_ticks")},
            })

    def _close_world(self):
        if self.observer_context is not None:
            self.observer_context.__exit__(None, None, None)
            self.observer_context = None
        for env in (self.native, self.model_env):
            if env is not None:
                env.close()
        self.native = self.model_env = None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if not self.done:
            raise RuntimeError("cannot reset an unfinished scientific world")
        if self.episode_index == len(self.seeds):
            self.exhausted = True
            self.features.fill(0)
            self._progress("exhausted")
            return self.features.copy(), {"schedule_exhausted": True}
        self._close_world()
        self.world_seed = self.seeds[self.episode_index]
        self.native = make_env(self.config, self.world_seed)
        self.model_env = make_env(self.config, 0)
        self.model_env.reset(seed=0)
        self.controller = TransitionController("L", self.native, self.model_env)
        self.controller.reset()
        observations, info = self.native.reset(seed=self.world_seed)
        self.observations = np.asarray(observations, dtype=np.float32)
        self.state = np.asarray(info["state"], dtype=np.float32)
        self.previous_done = np.ones(1, dtype=bool)
        self.modes = np.zeros(8, dtype=bool)
        self.step_index = 0
        self.episode_index += 1
        self.done = False
        self.rewards, self.metrics, self.ends = [], [], []
        self.steps = {key: [] for key in (
            "mode", "entered", "exited", "charging", "waiting_steps", "battery", "dock_bit",
            "guard_checked", "guard_blocked", "own_xyz", "return_margin", "nearest_station",
            "nearest_station_distance_m", "station_occupancy", "station_queue", "target_xy")}
        self.station_xy = absolute_station_xy(self.observations)
        self.observer = PlacementObserver(self.native.env)
        self.observer_context = self.observer.attach(self.controller)
        self.observer_context.__enter__()
        self.features = self.controller.prepare_clock(self.observations, self.modes.copy(), 0)
        self._progress("running")
        return self.features.copy(), {"world_seed": self.world_seed}

    def _native_step(self):
        t = self.step_index
        proposed = self.controller.propose(self.observations, self.state, t,
                                           self.previous_done, self.modes.copy())
        self.steps["target_xy"].append(self.controller.targets_xy)
        decision = apply_feedback_params(self.observations, proposed, self.modes, PRODUCTION_PARAMS)
        held = own_energy(self.observations, self.layout)
        for key, value in {
            "own_xyz": own_positions(self.observations, self.layout), "return_margin": decision.margins,
            "nearest_station": decision.selected_stations, "nearest_station_distance_m": decision.station_distances_m,
            "station_occupancy": station_counts(decision.selected_stations, held["charging"]),
            "station_queue": station_counts(decision.selected_stations, held["waiting_steps"] > 0),
        }.items():
            self.steps[key].append(value)
        self.modes = decision.modes
        next_obs, reward, terminated, truncated, info = self.native.step(decision.submitted_actions)
        self.native_steps += 1
        self.step_index += 1
        checked, blocked = guard_counters(self.native)
        self.rewards.append(float(reward))
        self.metrics.append(metric_row(reward, info["reward_info"]))
        self.ends.append((bool(terminated), bool(truncated)))
        next_obs = np.asarray(next_obs, dtype=np.float32)
        own = own_energy(next_obs, self.layout)
        for key, value in {
            "mode": self.modes.copy(), "entered": decision.entered, "exited": decision.exited,
            "charging": own["charging"], "waiting_steps": own["waiting_steps"], "battery": own["battery"],
            "dock_bit": decision.submitted_actions[:, 3] > DOCK_REQUEST_THRESHOLD,
            "guard_checked": checked, "guard_blocked": blocked,
        }.items():
            self.steps[key].append(value)
        self.observer.on_step(t=t, proposal_t=proposed, submitted_t=decision.submitted_actions)
        self.observations = next_obs
        self.state = np.asarray(info["next_state"], dtype=np.float32)
        self.previous_done[:] = bool(terminated or truncated)
        return float(reward), bool(terminated), bool(truncated)

    def _finish(self):
        arrays = {key: np.asarray(value) for key, value in self.steps.items()}
        arrays.update(reward=np.asarray(self.rewards, dtype=np.float64),
                      metrics=np.asarray(self.metrics, dtype=np.float64), ends=np.asarray(self.ends, dtype=bool))
        row = world_row(self.world_seed, arrays["reward"], arrays["metrics"], arrays["ends"], arrays,
                        time_step_s=float(self.config.time_step))
        row.update(mechanism_row(arrays, self.station_xy))
        row.update(position_diagnostics(arrays["metrics"], arrays, area_size_m=float(self.config.area_size),
                                        floor_m=float(self.config.height_range[0])))
        row.update(status="completed" if self.step_index == self.horizon else "incomplete",
                   seed=self.world_seed, arm="L_train", lane=self.lane, episode=self.episode_index)
        if self.out is not None:
            path = self.out / "training" / f"world_{self.world_seed}.npz"
            row = save_world(path, row, arrays, self.observer, self.controller, "L")
            row["raw_path"] = str(path.relative_to(self.out))
        self.episodes.append(row)
        if self.out is not None:
            _write_json(self.out / "training" / f"lane{self.lane}.episodes.json", self.episodes)
        return row

    def step(self, action):
        if self.done or self.exhausted:
            raise RuntimeError("step after fixed world schedule ended")
        requested = np.asarray(action)
        if requested.shape != (8,) or not np.issubdtype(requested.dtype, np.integer):
            raise ValueError("eight integer path modes required")
        self.controller.set_modes(requested)
        macro_start = self.step_index
        total, terminated, truncated = 0.0, False, False
        try:
            for _ in range(CLOCK):
                reward, terminated, truncated = self._native_step()
                total += reward
                if terminated or truncated:
                    break
            self.macro_steps += 1
            self.done = terminated or truncated
            if self.step_index >= self.horizon and not self.done:
                raise RuntimeError("native environment failed to end at its declared horizon")
            info = {"world_seed": self.world_seed, "macro_start": macro_start,
                    "macro_native_steps": self.step_index-macro_start, "native_reward_sum": total,
                    "native_terminated": terminated, "native_truncated": truncated,
                    "requested_modes": requested.tolist(),
                    "choice": _plain(self.controller.decision_records[-1]), "TimeLimit.truncated": False}
            if self.done:
                info["native_episode"] = self._finish()
                self.features = np.zeros(FEATURE_DIM, dtype=np.float32)
                if self.step_index != self.horizon:
                    self.exhausted = True
                    raise RuntimeError("native early end retained; fixed exposure incomplete")
            else:
                self.features = self.controller.prepare_clock(self.observations, self.modes.copy(), self.step_index)
            self._progress("completed" if self.done else "running")
            return self.features.copy(), total, self.done, False, info
        except BaseException:
            self._progress("failed")
            if self.out is not None:
                path = self.out / "training" / f"world_{self.world_seed}_partial.npz"
                if not path.exists():
                    np.savez_compressed(path, **self.observer.as_arrays(),
                                        reward=np.asarray(self.rewards, dtype=np.float64),
                                        planner_records_json=np.asarray(json.dumps(_plain(self.controller.decision_records))))
            raise

    def close(self):
        self._close_world()


def make_lane(lane, out):
    import torch
    torch.set_num_threads(1)
    return NativeMacroEnv(lane_seeds(lane), out=out, lane=lane)
