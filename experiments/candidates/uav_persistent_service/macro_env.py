"""Native finite episodes shared by training and the fixed three-arm evaluator."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import time

import gymnasium as gym
import numpy as np

from experiments.candidates.energy_relay_availability.b04.transit_hold import TransitHoldController
from experiments.candidates.energy_relay_availability.b05.runner import PairingObserver, _update_array_digest
from experiments.candidates.energy_relay_availability.runner import _cpu_seconds, _rss_kib, _sha256, _write_json
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    TRACE_FIELDS, absolute_station_xy, guard_counters, make_eval_config,
    mechanism_row, position_diagnostics, station_counts, world_row,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS, apply_feedback_params
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT, own_energy, own_positions
from experiments.candidates.uav_information_value.batch import effective_config
from experiments.candidates.uav_information_value.b02.readout import battery_reading
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_service_auxiliary.b04.evaluation import metric_row

from .constants import HORIZON, MACRO_STEPS, N_ACTIONS, POLICY_SEED, lane_seeds
from .controllers import CommitmentController, FEATURE_DIM
from .mechanisms import commitment_readings


def append_json(path, value):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")


def longest_spell(mask):
    lengths = np.diff(np.flatnonzero(np.r_[True, ~np.asarray(mask, dtype=bool), True])) - 1
    return int(lengths.max(initial=0))


class NativeEpisode:
    def __init__(self, seed, arm, *, horizon=HORIZON, controller_factory=None):
        self.started, self.cpu_started = time.monotonic(), _cpu_seconds()
        self.seed, self.arm, self.horizon = int(seed), arm, int(horizon)
        self.config = make_eval_config(self.horizon, POLICY_SEED)
        self.layout = replace(S7S2_LAYOUT, max_steps=self.horizon)
        self.env = make_env(self.config, self.seed)
        self.effective_config = effective_config(self.env, self.horizon)
        self.controller = (controller_factory(self.env, self.config) if controller_factory is not None else
                           TransitHoldController(self.env) if arm == "P" else
                           CommitmentController(self.env, self.config, arm=arm))
        self.controller.reset()
        observations, info = self.env.reset(seed=self.seed)
        self.observations = np.asarray(observations, dtype=np.float32)
        self.state = np.asarray(info["state"], dtype=np.float32)
        self.modes = np.zeros(8, dtype=bool)
        self.previous_done = np.ones(1, dtype=bool)
        self.t, self.done = 0, False
        self.station_xy = absolute_station_xy(self.observations)
        self.pairing = PairingObserver(self.env.env)
        self.pair_context = self.pairing.attach(self.controller)
        self.pair_context.__enter__()
        bs = hashlib.sha256()
        _update_array_digest(bs, "ground_bs_positions", self.env.env.ground_bs_positions)
        self.bs_sha256 = bs.hexdigest()
        self.initial_battery = self.env.env.uav_battery_ratios.copy()
        self.data = {key: [] for key in (
            "mode", "entered", "exited", "charging", "waiting_steps", "battery", "dock_bit",
            "guard_checked", "guard_blocked", "own_xyz", "return_margin", "nearest_station",
            "nearest_station_distance_m", "station_occupancy", "station_queue", "target_xy",
            "native_pre_xyz", "native_post_xyz", "native_battery", "native_load",
            "native_charger_input_wh", "native_consumed_wh", "native_positive_net_charge_wh",
            "native_charging_eligible", "native_station_occupancy", "native_station_queue",
            "proposed", "submitted", "reward", "metrics", "ends",
        )}
        self.option_data = {}
        self.macros = []
        self.feature_history = []
        self.features = self.prepare()

    def prepare(self):
        if self.arm == "P":
            return np.zeros(FEATURE_DIM, dtype=np.float32)
        return self.controller.prepare(self.observations, self.modes.copy(), self.t)

    def step_native(self):
        proposed = self.controller.propose(self.observations, self.state, self.t,
                                           self.previous_done, self.modes.copy())
        decision = apply_feedback_params(self.observations, proposed, self.modes, PRODUCTION_PARAMS)
        held = own_energy(self.observations, self.layout)
        pre = {
            "own_xyz": own_positions(self.observations, self.layout),
            "target_xy": np.asarray(self.controller.targets_xy, dtype=np.float64).copy(),
            "return_margin": decision.margins.copy(), "nearest_station": decision.selected_stations.copy(),
            "nearest_station_distance_m": decision.station_distances_m.copy(),
            "station_occupancy": station_counts(decision.selected_stations, held["charging"]),
            "station_queue": station_counts(decision.selected_stations, held["waiting_steps"] > 0),
            "native_pre_xyz": self.env.env.uav_positions.copy(),
            "proposed": np.asarray(proposed, dtype=np.float32).copy(),
            "submitted": decision.submitted_actions.copy(),
        }
        option = self.controller.commitment_snapshot() if self.arm != "P" else {}
        observations, reward, terminated, truncated, info = self.env.step(decision.submitted_actions)
        self.t += 1
        self.observations = np.asarray(observations, dtype=np.float32)
        self.state = np.asarray(info["next_state"], dtype=np.float32)
        self.modes = decision.modes
        self.done = bool(terminated or truncated)
        self.previous_done[:] = self.done
        self.pairing.on_step(t=self.t - 1)
        checked, blocked = guard_counters(self.env)
        own = own_energy(self.observations, self.layout)
        post = {
            "mode": self.modes.copy(), "entered": decision.entered.copy(), "exited": decision.exited.copy(),
            "charging": own["charging"].copy(), "waiting_steps": own["waiting_steps"].copy(),
            "battery": own["battery"].copy(), "dock_bit": decision.submitted_actions[:, 3] > .5,
            "guard_checked": checked, "guard_blocked": blocked,
            "native_post_xyz": self.env.env.uav_positions.copy(),
            "native_battery": self.env.env.uav_battery_ratios.copy(),
            "native_load": self.env.env.connections.sum(axis=1).copy(),
            "native_charger_input_wh": self.env.env.last_energy_charged_wh.copy(),
            "native_consumed_wh": self.env.env.last_energy_consumed_wh.copy(),
            "native_positive_net_charge_wh": self.env.env.last_net_energy_charged_wh.copy(),
            "native_charging_eligible": self.env.env.last_charging_eligible.copy(),
            "native_station_occupancy": self.env.env.station_occupancy.copy(),
            "native_station_queue": self.env.env.station_queue_lengths.copy(),
            "reward": float(reward), "metrics": metric_row(reward, info["reward_info"]),
            "ends": (bool(terminated), bool(truncated)),
        }
        for key, value in {**pre, **post}.items():
            self.data[key].append(value)
        for key, value in option.items():
            self.option_data.setdefault(key, []).append(np.asarray(value).copy())
        return float(reward)

    def macro_step(self, action, statistics=None):
        if self.done:
            raise RuntimeError("cannot step a finished finite world")
        start = self.t
        self.feature_history.append(self.features.copy())
        if self.arm == "P":
            if action != 0:
                raise ValueError("historical P has no scheduler action")
            choice = {"requested_action": 0, "executed_action": 0, "eligible": False}
        else:
            choice = self.controller.apply_choice(int(action))
        total = 0.0
        for _ in range(MACRO_STEPS):
            total += self.step_native()
            if self.done:
                break
        info = {"world_seed": self.seed, "macro_start": start,
                "macro_native_steps": self.t - start, "native_reward_sum": total,
                "choice": choice, "policy": statistics, "TimeLimit.truncated": False}
        self.macros.append(info)
        if self.done:
            if self.arm != "P":
                self.controller.finish(self.t, self.observations, self.modes.copy())
            self.features = np.zeros(FEATURE_DIM, dtype=np.float32)
        else:
            self.features = self.prepare()
        return self.features.copy(), total, self.done, info

    def arrays(self):
        arrays = {key: np.asarray(value) for key, value in self.data.items()}
        arrays.update({f"commit_{key}": np.asarray(value) for key, value in self.option_data.items()})
        arrays.update(self.pairing.as_arrays())
        arrays["initial_native_battery"] = self.initial_battery
        arrays["metric_fields"] = np.asarray(TRACE_FIELDS)
        arrays["macro_features"] = np.asarray(self.feature_history)
        return arrays

    def row(self):
        arrays = self.arrays()
        if not self.done or self.t != self.horizon:
            raise RuntimeError("a complete reading requires the declared native horizon")
        row = world_row(self.seed, arrays["reward"], arrays["metrics"], arrays["ends"], arrays,
                        time_step_s=float(self.config.time_step))
        row.update(mechanism_row(arrays, self.station_xy))
        row.update(position_diagnostics(arrays["metrics"], arrays,
                                        area_size_m=float(self.config.area_size),
                                        floor_m=float(self.config.height_range[0])))
        row.update(battery_reading(arrays["native_battery"]))
        qos = arrays["metrics"][:, TRACE_FIELDS.index("qos_satisfaction_ratio")]
        battery = arrays["native_battery"]
        snapshot_calls = int(self.controller.heuristic.service_snapshot_calls) if self.arm == "P" else int(
            self.controller.costs["service_snapshot_calls"])
        decisions = [] if self.arm == "P" else self.controller.diagnostics
        events = [] if self.arm == "P" else self.controller.events
        row.update(
            arm=self.arm, status="completed", effective_config=self.effective_config,
            **self.pairing.digests(), ground_bs_sha256=self.bs_sha256,
            horizon_normalized_qos=float(qos.sum() / self.horizon),
            final300_persistent_reserve_members=int(np.all(battery[-300:] <= .10, axis=0).sum()),
            longest_zero_qos_spell=longest_spell(qos <= 0),
            longest_below_half_qos_spell=longest_spell(qos < .5),
            terminal_zero_service=bool(qos[-1] <= 0),
            net_stored_energy_wh=float((battery[-1] - self.initial_battery).sum() * 160),
            actual_team_travel_m=float(np.linalg.norm(arrays["native_post_xyz"] - arrays["native_pre_xyz"], axis=2).sum()),
            service_snapshot_calls=snapshot_calls, macro_decisions=len(decisions),
            eligible_macro_decisions=sum(bool(item["eligible"]) for item in decisions),
            requested_dispatches=sum(item["requested_action"] > 0 for item in decisions),
            executed_dispatches=sum(item["executed_action"] > 0 for item in decisions),
            controller_costs=({"service_snapshot_calls": snapshot_calls} if self.arm == "P" else self.controller.costs),
            option_event_counts={kind: sum(event.get("kind") == kind for event in events)
                                 for kind in sorted({str(event.get("kind")) for event in events})},
            bins=[{"start": start, "stop": min(start + 1000, self.t),
                   "qos": float(qos[start:start + 1000].mean()),
                   "native_J": float(arrays["reward"][start:start + 1000].sum())}
                  for start in range(0, self.t, 1000)],
            worker_wall_seconds=time.monotonic() - self.started,
            worker_cpu_seconds=_cpu_seconds() - self.cpu_started, worker_peak_rss_kib=_rss_kib(),
        )
        row.update(commitment_readings(arrays, events)[1])
        return row

    def save(self, path, *, complete):
        path = Path(path)
        if path.exists():
            raise FileExistsError(path)
        np.savez_compressed(path, **self.arrays())
        decision_path = path.with_suffix(".decisions.json")
        events = [] if self.arm == "P" else self.controller.events
        _write_json(decision_path, {"complete": complete, "macros": self.macros,
                                  "events": events,
                                  "commitments": commitment_readings(self.arrays(), events)[0],
                                  "controller_costs": {} if self.arm == "P" else self.controller.costs})
        return {"raw_path": str(path), "raw_sha256": _sha256(path), "raw_bytes": path.stat().st_size,
                "decisions_path": str(decision_path), "decisions_sha256": _sha256(decision_path)}

    def close(self):
        self.pair_context.__exit__(None, None, None)
        self.env.close()


class NativeMacroEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, seeds, *, out=None, lane=0, horizon=HORIZON):
        super().__init__()
        self.started, self.cpu_started = time.monotonic(), _cpu_seconds()
        self.seeds, self.out, self.lane, self.horizon = tuple(map(int, seeds)), out, int(lane), int(horizon)
        if not self.seeds or len(set(self.seeds)) != len(self.seeds) or self.horizon % MACRO_STEPS:
            raise ValueError("finite, unique, whole-macro world schedule required")
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (FEATURE_DIM,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(N_ACTIONS)
        self.episode = None
        self.episode_index = self.native_steps = self.macro_steps = 0
        self.episodes = []
        self.exhausted = False

    def counts(self):
        return {"lane": self.lane, "native_steps": self.native_steps,
                "macro_steps": self.macro_steps, "episodes_started": self.episode_index,
                "episodes_completed": len(self.episodes), "exhausted": self.exhausted,
                "current_seed": self.episode.seed if self.episode else None,
                "current_episode_steps": self.episode.t if self.episode else 0,
                "worker_wall_seconds": time.monotonic() - self.started,
                "worker_cpu_seconds": _cpu_seconds() - self.cpu_started, "worker_peak_rss_kib": _rss_kib()}

    def _progress(self, status):
        if self.out is not None:
            _write_json(self.out / "training" / f"lane{self.lane}.progress.json", self.counts() | {"status": status})

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if self.episode is not None and not self.episode.done:
            raise RuntimeError("cannot replace an unfinished native world")
        if self.episode_index == len(self.seeds):
            self.exhausted = True
            self._progress("exhausted")
            return np.zeros(FEATURE_DIM, dtype=np.float32), {"schedule_exhausted": True}
        if self.episode is not None:
            self.episode.close()
        self.episode = NativeEpisode(self.seeds[self.episode_index], "L", horizon=self.horizon)
        self.episode_index += 1
        self._progress("running")
        return self.episode.features.copy(), {"world_seed": self.episode.seed}

    def step(self, action):
        if self.exhausted or self.episode is None:
            raise RuntimeError("step beyond the fixed world schedule")
        before = self.episode.t
        counted = False
        try:
            features, reward, done, info = self.episode.macro_step(int(action))
            self.native_steps += self.episode.t - before
            counted = True
            self.macro_steps += 1
            if self.out is not None:
                append_json(self.out / "training" / f"lane{self.lane}.macros.jsonl", info)
            if done:
                row = self.episode.row()
                if self.out is not None:
                    row.update(self.episode.save(self.out / "training" / f"world_{self.episode.seed}.npz", complete=True))
                self.episodes.append(row)
                info["native_episode"] = row
                if self.out is not None:
                    _write_json(self.out / "training" / f"lane{self.lane}.episodes.json", self.episodes)
            self._progress("completed" if done else "running")
            return features, reward, done, False, info
        except BaseException:
            if not counted:
                self.native_steps += self.episode.t - before
            if self.out is not None and self.episode.t:
                path = self.out / "training" / f"world_{self.episode.seed}.partial.npz"
                if not path.exists():
                    self.episode.save(path, complete=False)
            self._progress("failed")
            raise

    def close(self):
        if self.episode is not None:
            self.episode.close()
            self.episode = None


def make_lane(lane, out):
    import torch

    torch.set_num_threads(1)
    return NativeMacroEnv(lane_seeds(lane), out=Path(out), lane=lane)
