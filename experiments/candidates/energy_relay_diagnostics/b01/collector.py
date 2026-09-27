"""A frozen policy through B02's actual collector, with one matched CPU lane.

Only the update is replaced. Real storage, reset, bootstrap and clear calls remain.
The process-local environment factory is restored on every exit. This is a fresh
single-world probe, never a replay of B02's continuous two-lane CUDA training stream.
"""

from __future__ import annotations

import resource
import tempfile
import time
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    PRODUCTION_PARAMS, apply_feedback_params,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT, own_energy, own_positions,
)
from experiments.candidates.energy_relay_benchmark.b02 import training
from experiments.candidates.energy_relay_benchmark.b02.configuration import B02Spec

from .instrumentation import ActionInputRecorder


class _NativeEpisodeEnded(Exception):
    """Stop the probe after storing an early native ending, before a second reset."""


class FrozenAgent:
    """Forward all collector effects except the one explicitly disabled PPO update."""

    def __init__(self, agent, episode_seed: int):
        self.agent = agent
        self.episode_seed = int(episode_seed)
        self.first_step = True
        self.updates_skipped = 0
        self.proposal = None
        self.stored_transitions = 0

    def __getattr__(self, name):
        return getattr(self.agent, name)

    def step(self, *args, **kwargs):
        if self.first_step:
            ev.seed_everything(self.episode_seed, torch.device(self.agent.device))
            self.first_step = False
        result = self.agent.step(*args, **kwargs)
        self.proposal = np.asarray(result[0][0], dtype=np.float32).copy()
        return result

    def update(self, **kwargs):
        self.updates_skipped += 1
        return {}

    def store_transition_batch(self, *args, **kwargs):
        result = self.agent.store_transition_batch(*args, **kwargs)
        self.stored_transitions += 1
        return result


class RecordingEnv:
    """Pass through native transitions and read the same fields as B01.evaluate_world."""

    def __init__(self, native, config, facade, recorder):
        self.native = native
        self.config = config
        self.facade = facade
        self.recorder = recorder
        self.controller = SimpleNamespace(evaluator=facade.agent)
        self.layout = replace(S7S2_LAYOUT, max_steps=int(config.max_steps))
        self.modes = np.zeros(ev.N_UAVS, dtype=bool)
        self.steps = {key: [] for key in (
            "mode", "entered", "exited", "charging", "waiting_steps", "battery", "dock_bit",
            "guard_checked", "guard_blocked", "own_xyz", "return_margin", "nearest_station",
            "nearest_station_distance_m", "station_occupancy", "station_queue", "reward",
            "metrics", "ends",
        )}
        self.station_xy = None
        self.obs = self.state = None

    def reset(self, *, seed=None):
        if (self.steps["ends"] and bool(np.asarray(self.steps["ends"][-1]).any())
                and len(self.steps["ends"]) < int(self.config.episode_length)):
            raise _NativeEpisodeEnded()
        result = self.native.reset(seed=seed)
        self.obs = np.asarray(result[0], dtype=np.float32)
        self.state = np.asarray(result[1]["state"], dtype=np.float32)
        self.modes[:] = False
        if self.station_xy is None:
            self.station_xy = ev.absolute_station_xy(self.obs)
        return result

    def step(self, submitted):
        proposal = self.facade.proposal
        decision = apply_feedback_params(self.obs, proposal, self.modes, PRODUCTION_PARAMS)
        np.testing.assert_array_equal(submitted, decision.submitted_actions)
        submitted_copy = np.asarray(submitted).copy()
        held = own_energy(self.obs, self.layout)
        self.modes = decision.modes
        before = {
            "own_xyz": own_positions(self.obs, self.layout),
            "return_margin": decision.margins,
            "nearest_station": decision.selected_stations,
            "nearest_station_distance_m": decision.station_distances_m,
            "station_occupancy": ev.station_counts(decision.selected_stations, held["charging"]),
            "station_queue": ev.station_counts(decision.selected_stations, held["waiting_steps"] > 0),
        }
        next_obs, reward, terminated, truncated, info = self.native.step(submitted)
        next_obs = np.asarray(next_obs, dtype=np.float32)
        next_state = np.asarray(info["next_state"], dtype=np.float32)
        own = own_energy(next_obs, self.layout)
        checked, blocked = ev.guard_counters(self.native)
        t = len(self.steps["reward"])
        self.recorder.on_step(
            t=t, observations_t=self.obs, state_t=self.state,
            proposal_t=proposal, submitted_t=submitted_copy,
            observations_t1=next_obs, state_t1=next_state, controller=self.controller,
        )
        values = before | {
            "mode": self.modes.copy(), "entered": decision.entered, "exited": decision.exited,
            "charging": own["charging"], "waiting_steps": own["waiting_steps"],
            "battery": own["battery"], "dock_bit": submitted_copy[:, 3] > ev.DOCK_REQUEST_THRESHOLD,
            "guard_checked": checked, "guard_blocked": blocked, "reward": float(reward),
            "metrics": ev.metric_row(reward, info["reward_info"]),
            "ends": (bool(terminated), bool(truncated)),
        }
        for key, value in values.items():
            self.steps[key].append(np.array(value, copy=True))
        self.obs, self.state = next_obs, next_state
        return next_obs, reward, terminated, truncated, info

    def close(self):
        self.native.close()


def evaluate_collector_task(task: ev.WorldTask, *, capture_inputs: bool = False):
    """One complete episode, matching B01 draw seeding but using the real storage path."""
    if task.controller != "L" or task.action_mode != "stochastic" or task.device != "cpu":
        raise ValueError("collector alignment requires L/stochastic/cpu")
    if task.draw is None or task.params != PRODUCTION_PARAMS:
        raise ValueError("collector alignment requires a draw and the production shield")
    if 957001 <= int(task.seed) <= 957032:
        raise ValueError("sealed holdout is forbidden in diagnostics")
    started = time.perf_counter()
    torch.set_num_threads(task.threads)
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("collector requires Torch FP32")
    record = ev.read_learner_record(task)
    config = ev.learner_eval_config(ev.make_eval_config(task.horizon, task.policy_seed), record)
    spec = B02Spec(seed=task.seed, lanes=1, rollouts=1,
                   rollout_length=task.horizon, episode_length=task.horizon)
    episode_seed = ev.sample_seed(task.policy_seed, task.seed, task.draw)
    with tempfile.TemporaryDirectory(prefix="diagnostics-collector-", dir=task.log_dir) as log_dir:
        agent, identity = ev.load_learner_policy(task, record, config, torch.device("cpu"), log_dir)
        agent.train(True)
        agent.reset_env_state(0)
        before = (ev.initialization_fingerprint(agent), ev.optimizer_steps(agent),
                  ev._normalizer_snapshot(agent))
        facade = FrozenAgent(agent, episode_seed)
        recorder = ActionInputRecorder(capture_inputs=capture_inputs,
                                       capture_held_snapshot=capture_inputs)
        captured = []
        factory = training.make_env

        def recorded_factory(cfg, seed):
            if captured:
                raise RuntimeError("the frozen collector must construct exactly one lane")
            env = RecordingEnv(factory(cfg, seed), cfg, facade, recorder)
            captured.append(env)
            return env

        with ev.preserved_rng(), recorder.attach(SimpleNamespace(evaluator=agent)):
            # No other world runs concurrently inside this spawned worker process.
            with patch.object(training, "make_env", recorded_factory):
                try:
                    result = training.collect_and_train(facade, config, spec, feedback=True)
                except _NativeEpisodeEnded:
                    result = None
        if (ev.initialization_fingerprint(agent) != before[0]
                or ev.optimizer_steps(agent) != before[1]
                or not ev._same_snapshot(ev._normalizer_snapshot(agent), before[2])):
            raise RuntimeError("frozen collection changed weights, optimizers or normalizers")
        if result is not None and (
                result["counts"]["native_episodes"] != 1 or facade.updates_skipped != 1):
            raise RuntimeError("probe did not complete exactly one frozen episode/rollout")
        env = captured[0]
        arrays = {key: np.asarray(value) for key, value in env.steps.items()}
        if not arrays["ends"][-1].any() or facade.stored_transitions != len(arrays["reward"]):
            raise RuntimeError("probe lacks a stored complete native episode")
        row = ev.world_row(task.seed, arrays["reward"], arrays["metrics"], arrays["ends"],
                           arrays, time_step_s=float(config.time_step))
        row.update(ev.mechanism_row(arrays, env.station_xy))
        row.update(ev.position_diagnostics(arrays["metrics"], arrays,
                                           area_size_m=float(config.area_size),
                                           floor_m=float(config.height_range[0])))
        episode = (result["rollouts"][0]["episodes_completed"][0] if result is not None else
                   {"native_J": float(sum(float(r) for r in arrays["reward"])),
                    "qos_per_step": float(sum(float(row[ev.QOS]) for row in arrays["metrics"]))
                    / len(arrays["reward"])})
        np.testing.assert_allclose(episode["native_J"], row["raw_native_J"], rtol=0, atol=1e-8)
        np.testing.assert_allclose(episode["qos_per_step"], row["qos_per_step"], rtol=0, atol=1e-12)
        row.update(
            controller="L", controller_information=ev.L_CONTROLLER_INFORMATION, failed=False,
            action_mode="stochastic", draw=int(task.draw), sample_seed=episode_seed,
            enter_margin=0.0, exit_margin=0.05, path="frozen_collector_single_lane_cpu",
            optimizer_updates=0, skipped_update_calls=facade.updates_skipped,
            collector_native_J=episode["native_J"], collector_qos_per_step=episode["qos_per_step"],
            collector_rollout_qos_per_step=(result["rollouts"][0]["lane_qos_per_step"][0]
                                           if result is not None else None),
            early_native_ending=result is None, stored_transitions=facade.stored_transitions,
            wall_seconds=time.perf_counter() - started,
            worker_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        )
        return {"row": row, "arrays": arrays, "identity": identity,
                "observation": recorder.as_arrays()}
