"""Finite native episodes exposed as 30-step Gym actions, without timeout bootstrap."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import time

import gymnasium as gym
import numpy as np

from experiments.candidates.energy_relay_availability.runner import _cpu_seconds, _rss_kib, _sha256, _write_json
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    DOCK_REQUEST_THRESHOLD, TRACE_FIELDS, absolute_station_xy, guard_counters,
    make_eval_config, mechanism_row, position_diagnostics, station_counts, world_row,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    N_UAVS, PRODUCTION_PARAMS, apply_feedback_params,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT, own_energy, own_positions,
)
from experiments.candidates.uav_information_value.batch import effective_config
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_service_auxiliary.b04.evaluation import metric_row

from .controllers import N_ACTIONS, REPLAN_STEPS, SensingController


HORIZON = 3000
POLICY_SEED = 28130001
TRAIN_SEEDS = tuple(range(28132001, 28132161))
EVAL_SEEDS = tuple(range(28133001, 28133017))
N_ENVS = 4


def lane_seeds(lane: int) -> tuple[int, ...]:
    if lane not in range(N_ENVS):
        raise ValueError("training lane is outside the fixed four-lane schedule")
    return TRAIN_SEEDS[lane::N_ENVS]


class NativeMacroEnv(gym.Env):
    """One isolated RNG process per lane; reset ignores SB3's policy-seed schedule.

    The only states supplied to the actor/critic are produced by the legal controller.
    Native state and reward diagnostics remain in this environment/recorder.
    """

    metadata = {"render_modes": []}

    def __init__(self, seeds, *, out: Path | None = None, lane: int = 0,
                 horizon: int = HORIZON):
        super().__init__()
        self.started, self.cpu_started = time.monotonic(), _cpu_seconds()
        self.seeds = tuple(map(int, seeds))
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("one nonempty, unique world schedule is required")
        if horizon < REPLAN_STEPS or horizon % REPLAN_STEPS:
            raise ValueError("finite horizon must consist of complete 30-step macros")
        self.horizon, self.out, self.lane = int(horizon), out, int(lane)
        self.controller = SensingController("L")
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.controller.feature_dim,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(N_ACTIONS)
        self.config = make_eval_config(self.horizon, POLICY_SEED)
        self.layout = replace(S7S2_LAYOUT, max_steps=self.horizon)
        self.native = None
        self.episode_index = 0
        self.native_steps = 0
        self.macro_steps = 0
        self.done = True
        self.exhausted = False
        self.episodes = []
        self.macros = []
        self.features = np.zeros(self.observation_space.shape, dtype=np.float32)

    def _progress(self, status):
        if self.out is not None:
            _write_json(self.out / "training" / f"lane{self.lane}.progress.json", {
                "lane": self.lane, "status": status, "native_steps": self.native_steps,
                "macro_steps": self.macro_steps, "episodes_started": self.episode_index,
                "episodes_completed": len(self.episodes),
                "current_seed": getattr(self, "world_seed", None),
                "current_episode_steps": getattr(self, "step_index", 0),
                "worker_wall_seconds": time.monotonic() - self.started,
                "worker_cpu_seconds": _cpu_seconds() - self.cpu_started,
                "worker_peak_rss_kib": _rss_kib(),
            })

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if not self.done:
            raise RuntimeError("a scheduled native world cannot be reset before its end")
        if self.episode_index == len(self.seeds):
            # VecEnv automatically resets terminal lanes, including the final rollout.
            # This inert observation is never stepped and cannot create another world.
            self.exhausted = True
            self.features = np.zeros(self.observation_space.shape, dtype=np.float32)
            self._progress("exhausted")
            return self.features.copy(), {"schedule_exhausted": True}
        self.world_seed = self.seeds[self.episode_index]
        # BS geometry is seeded only in the native constructor, not reset(seed).
        # Reconstruct each scheduled world just as the fixed evaluator does.
        if self.native is not None:
            self.native.close()
        self.native = make_env(self.config, self.world_seed)
        self.effective_config = effective_config(self.native, self.horizon)
        self.controller.reset()
        observations, _ = self.native.reset(seed=self.world_seed)
        self.observations = np.asarray(observations, dtype=np.float32)
        self.modes = np.zeros(N_UAVS, dtype=bool)
        self.step_index = 0
        self.episode_index += 1
        self.done = False
        self.rewards, self.metrics, self.ends = [], [], []
        self.steps = {key: [] for key in (
            "mode", "entered", "exited", "charging", "waiting_steps", "battery", "dock_bit",
            "guard_checked", "guard_blocked", "own_xyz", "return_margin", "nearest_station",
            "nearest_station_distance_m", "station_occupancy", "station_queue", "target_xy",
        )}
        self.station_xy = absolute_station_xy(self.observations)
        self.features = self.controller.prepare(self.observations, self.modes, 0)
        self._progress("running")
        return self.features.copy(), {"world_seed": self.world_seed}

    def _native_step(self):
        proposed = self.controller.act(self.observations)
        decision = apply_feedback_params(self.observations, proposed, self.modes, PRODUCTION_PARAMS)
        held = own_energy(self.observations, self.layout)
        self.steps["own_xyz"].append(own_positions(self.observations, self.layout))
        self.steps["target_xy"].append(self.controller.targets_xy)
        self.steps["return_margin"].append(decision.margins)
        self.steps["nearest_station"].append(decision.selected_stations)
        self.steps["nearest_station_distance_m"].append(decision.station_distances_m)
        self.steps["station_occupancy"].append(station_counts(decision.selected_stations, held["charging"]))
        self.steps["station_queue"].append(station_counts(decision.selected_stations, held["waiting_steps"] > 0))
        self.modes = decision.modes
        observations, reward, terminated, truncated, info = self.native.step(decision.submitted_actions)
        # Count the native transition before validation can raise, preserving cost on failure.
        self.native_steps += 1
        self.step_index += 1
        self.observations = np.asarray(observations, dtype=np.float32)
        self.rewards.append(float(reward))
        self.metrics.append(metric_row(reward, info["reward_info"]))
        self.ends.append((bool(terminated), bool(truncated)))
        checked, blocked = guard_counters(self.native)
        own = own_energy(self.observations, self.layout)
        self.steps["mode"].append(self.modes.copy())
        self.steps["entered"].append(decision.entered)
        self.steps["exited"].append(decision.exited)
        self.steps["charging"].append(own["charging"])
        self.steps["waiting_steps"].append(own["waiting_steps"])
        self.steps["battery"].append(own["battery"])
        self.steps["dock_bit"].append(decision.submitted_actions[:, 3] > DOCK_REQUEST_THRESHOLD)
        self.steps["guard_checked"].append(checked)
        self.steps["guard_blocked"].append(blocked)
        return float(reward), bool(terminated), bool(truncated)

    def _finish(self):
        arrays = {key: np.asarray(value) for key, value in self.steps.items()}
        arrays.update(reward=np.asarray(self.rewards, dtype=np.float64),
                      metrics=np.asarray(self.metrics, dtype=np.float64),
                      ends=np.asarray(self.ends, dtype=bool))
        row = world_row(self.world_seed, arrays["reward"], arrays["metrics"], arrays["ends"],
                        arrays, time_step_s=float(self.config.time_step))
        row.update(mechanism_row(arrays, self.station_xy))
        row.update(position_diagnostics(arrays["metrics"], arrays,
                                        area_size_m=float(self.config.area_size),
                                        floor_m=float(self.config.height_range[0])))
        row.update(lane=self.lane, episode=self.episode_index,
                   status="completed" if self.step_index == self.horizon else "incomplete",
                   reserve10_uav_step_fraction=float(np.mean(arrays["battery"] < .10)),
                   macro_count=len(self.controller.diagnostics))
        if self.out is not None:
            path = self.out / "training" / f"world_{self.world_seed}.npz"
            if path.exists():
                raise FileExistsError(path)
            np.savez_compressed(path, **arrays, metric_fields=np.asarray(TRACE_FIELDS))
            row.update(raw_path=str(path.relative_to(self.out)), raw_sha256=_sha256(path),
                       raw_bytes=path.stat().st_size)
        self.episodes.append(row)
        if self.out is not None:
            _write_json(self.out / "training" / f"lane{self.lane}.episodes.json", self.episodes)
        return row

    def step(self, action):
        if self.done or self.exhausted:
            raise RuntimeError("step after a finite world/schedule ended")
        choice = np.asarray(action)
        if choice.size != 1 or not np.issubdtype(choice.dtype, np.integer):
            raise ValueError("PPO action must be one discrete integer")
        diagnostic = self.controller.apply_choice(int(choice.item()))
        macro_start = self.step_index
        total_reward, terminated, truncated = 0.0, False, False
        try:
            for _ in range(REPLAN_STEPS):
                reward, terminated, truncated = self._native_step()
                total_reward += reward
                if terminated or truncated:
                    break
            self.macro_steps += 1
            self.done = terminated or truncated
            if self.step_index >= self.horizon and not self.done:
                raise RuntimeError("native host did not end at the fixed scientific horizon")
            info = {"world_seed": self.world_seed, "macro_start": macro_start,
                    "macro_native_steps": self.step_index - macro_start,
                    "native_reward_sum": total_reward, "native_terminated": terminated,
                    "native_truncated": truncated, "choice": diagnostic,
                    "TimeLimit.truncated": False}
            self.macros.append(info)
            if self.done:
                info["native_episode"] = self._finish()
                self.features = np.zeros(self.observation_space.shape, dtype=np.float32)
                if self.step_index != self.horizon:
                    # Preserve the real early end but never substitute new worlds or steps.
                    self.exhausted = True
                    raise RuntimeError("native early end makes the fixed exposure contract incomplete")
            else:
                self.features = self.controller.prepare(self.observations, self.modes, self.step_index)
            if self.out is not None:
                with (self.out / "training" / f"lane{self.lane}.macros.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(info, allow_nan=False, sort_keys=True) + "\n")
            self._progress("completed" if self.done else "running")
            # Native horizon truncation is TERMINAL for this finite scientific objective.
            return self.features.copy(), total_reward, self.done, False, info
        except BaseException:
            self._progress("failed")
            raise

    def counts(self):
        return {"lane": self.lane, "native_steps": self.native_steps,
                "macro_steps": self.macro_steps, "episodes_started": self.episode_index,
                "episodes_completed": len(self.episodes), "exhausted": self.exhausted,
                "worker_wall_seconds": time.monotonic() - self.started,
                "worker_cpu_seconds": _cpu_seconds() - self.cpu_started,
                "worker_peak_rss_kib": _rss_kib()}

    def close(self):
        if self.native is not None:
            self.native.close()


def make_lane(lane: int, out: str):
    import torch

    torch.set_num_threads(1)
    return NativeMacroEnv(lane_seeds(lane), out=Path(out), lane=lane)
