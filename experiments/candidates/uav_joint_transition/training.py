"""One fixed fit, retaining requested choices and raw native macro rewards."""

from __future__ import annotations

from functools import partial
import json
from pathlib import Path
import time
import traceback

import numpy as np
import stable_baselines3
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import SubprocVecEnv
import torch

from experiments.candidates.energy_relay_availability.runner import _cpu_seconds, _rss_kib, _sha256, _write_json
from experiments.candidates.uav_active_sensing.training import (
    fingerprint, optimizer_steps, parameter_movement, _append, _scalars, _stop_failed_children,
)
from .constants import (CLOCK, HORIZON, N_ENVS, POLICY_SEED, TRAIN_SEEDS, ROLLOUT_STEPS,
                        ROLLOUTS, TOTAL_MACRO_STEPS, OPTIMIZER_STEPS)
from .macro_env import make_lane
from .policy import PathPolicy


PPO_PARAMS = {
    "learning_rate": .0003, "n_steps": ROLLOUT_STEPS, "batch_size": 100, "n_epochs": 4,
    "gamma": 1.0, "gae_lambda": .95, "clip_range": .2, "normalize_advantage": True,
    "ent_coef": 0.0, "vf_coef": .5, "max_grad_norm": .5, "target_kl": None,
    "seed": POLICY_SEED, "device": "cpu",
}


class TrainingAudit(BaseCallback):
    def __init__(self, out):
        super().__init__()
        self.out = Path(out)
        self.rollouts = self.native_steps = self.loss_rows = self.exposure_rows = 0
        self.seeds = []

    def _record_update(self):
        steps = optimizer_steps(self.model.policy)
        if not steps:
            return
        losses = _scalars(self.model.logger.name_to_value)
        if any(value is None for key, value in losses.items()
               if key.startswith("train/") and key != "train/explained_variance"):
            raise FloatingPointError("nonfinite PPO training statistic")
        self.loss_rows += 1
        _append(self.out / "training" / "updates.jsonl", {
            "update": self.loss_rows, "optimizer_steps": steps,
            "macro_decisions": self.model.num_timesteps, "losses": losses,
        })

    def _on_rollout_start(self):
        self._record_update()
        self.rewards, self.actions = [], []

    def _on_step(self):
        infos = self.locals["infos"]
        actions = np.asarray(self.locals["actions"])
        if actions.shape != (N_ENVS, 8) or len(infos) != N_ENVS:
            raise RuntimeError("wrong training lane/action shape")
        if any(info.get("TimeLimit.truncated", False) or info["macro_native_steps"] != CLOCK
               for info in infos):
            raise RuntimeError("incomplete macro or forbidden finite-horizon bootstrap")
        with torch.no_grad():
            distribution = self.model.policy.get_distribution(self.locals["obs_tensor"])
            statistics = {key: value.cpu().numpy() for key, value in distribution.statistics().items()}
        log_probs = self.locals["log_probs"].detach().cpu().numpy()
        for lane, (action, info) in enumerate(zip(actions, infos)):
            if not np.array_equal(action, info["requested_modes"]):
                raise RuntimeError("PPO action differs from recorded requested path modes")
            if not np.array_equal(action, info["choice"]["requested_modes"]):
                raise RuntimeError("controller changed requested path modes")
            row = {"world_seed": info["world_seed"], "macro_start": info["macro_start"],
                   "requested_modes": action.tolist(), "eligible": info["choice"]["eligible"],
                   "sampled_log_probability": float(log_probs[lane]),
                   "sampled_joint_probability": float(np.exp(log_probs[lane])),
                   "probabilities": statistics["probabilities"][lane].tolist(),
                   "any_non_direct_probability": float(statistics["non_direct_probability"][lane]),
                   "joint_entropy": float(statistics["joint_entropy"][lane])}
            _append(self.out / "training" / "exposure.jsonl", row)
            self.exposure_rows += 1
        self.actions.append(actions.copy())
        self.rewards.append([info["native_reward_sum"] for info in infos])
        self.native_steps += sum(info["macro_native_steps"] for info in infos)
        return True

    def _on_rollout_end(self):
        buffer = self.model.rollout_buffer
        actions = np.asarray(self.actions, dtype=np.float32)
        rewards = np.asarray(self.rewards, dtype=np.float32)
        if not buffer.full or len(self.rewards) != ROLLOUT_STEPS:
            raise RuntimeError("incomplete PPO rollout")
        if not np.array_equal(buffer.actions, actions) or not np.array_equal(buffer.rewards, rewards):
            raise RuntimeError("requested actions or native rewards changed before PPO storage")
        if not np.asarray(self.locals["dones"]).all():
            raise RuntimeError("rollout boundary must end two finite native worlds")
        episodes = [info["native_episode"] for info in self.locals["infos"]]
        if any(row["actual_length"] != HORIZON for row in episodes):
            raise RuntimeError("incomplete training world")
        self.seeds.extend(row["seed"] for row in episodes)
        self.rollouts += 1
        _append(self.out / "training" / "rollouts.jsonl", {
            "rollout": self.rollouts, "macro_decisions": self.model.num_timesteps,
            "native_steps": self.native_steps, "seeds": [row["seed"] for row in episodes],
            "native_J": [row["raw_native_J"] for row in episodes],
            "qos_per_step": [row["qos_per_step"] for row in episodes],
            "requested_non_direct_fraction": float(np.mean(actions != 0)),
            "stored_native_rewards_exact_float32": True, "stored_requested_actions_exact": True,
            "all_finite_horizon_dones": True,
        })

    def _on_training_end(self):
        self._record_update()


def _work_lower_bound(progress):
    fields = ("service_snapshot_calls", "prediction_team_ticks")
    return {field: sum(row["completed_controller_work"].get(field, 0)
                       + row["current_controller_work"].get(field, 0) for row in progress)
            for field in fields}


def train(out):
    out = Path(out)
    (out / "training").mkdir()
    started, cpu_started = time.monotonic(), _cpu_seconds()
    result = {"status": "incomplete", "fits_started": 0,
              "sb3_version": stable_baselines3.__version__, "policy_seed": POLICY_SEED}
    vec = model = callback = None
    success = False
    try:
        torch.set_num_threads(1)
        if torch.get_default_dtype() != torch.float32:
            raise RuntimeError("fixed learner requires FP32")
        vec = SubprocVecEnv.__new__(SubprocVecEnv)
        vec.__init__([partial(make_lane, lane, str(out)) for lane in range(N_ENVS)], start_method="spawn")
        model = PPO(PathPolicy, vec, **PPO_PARAMS,
                    policy_kwargs={"net_arch": {"pi": [128, 128], "vf": [128, 128]},
                                   "activation_fn": torch.nn.Tanh, "ortho_init": True})
        model.set_logger(configure(folder=str(out / "training"), format_strings=[]))
        before = {name: value.detach().cpu().clone() for name, value in model.policy.state_dict().items()}
        result["initial_fingerprint"] = fingerprint(model.policy)
        model.save(out / "initial.zip")
        callback = TrainingAudit(out)
        result["fits_started"] = 1
        _write_json(out / "training.json", result)
        model.learn(total_timesteps=TOTAL_MACRO_STEPS, callback=callback, log_interval=1,
                    progress_bar=False)
        counts = vec.env_method("counts")
        updates = optimizer_steps(model.policy)
        per_lane = len(TRAIN_SEEDS) // N_ENVS
        if (model.num_timesteps != TOTAL_MACRO_STEPS or callback.rollouts != ROLLOUTS
                or updates != OPTIMIZER_STEPS or callback.loss_rows != ROLLOUTS
                or callback.exposure_rows != TOTAL_MACRO_STEPS
                or sorted(callback.seeds) != list(TRAIN_SEEDS)
                or any(any(row[key] != value for key, value in {
                    "lane": i, "native_steps": per_lane*HORIZON,
                    "macro_steps": per_lane*HORIZON//CLOCK, "episodes_started": per_lane,
                    "episodes_completed": per_lane, "exhausted": True,
                }.items()) for i, row in enumerate(counts))):
            raise RuntimeError("fixed training exposure/optimizer counts differ")
        model.save(out / "endpoint.zip")
        movement = parameter_movement(before, model.policy)
        if movement["actor"]["l2"] == 0 or movement["critic"]["l2"] == 0:
            raise RuntimeError("no actor or critic parameter movement")
        result.update(status="complete", lane_counts=counts, actual_native_steps=callback.native_steps,
                      macro_decisions=model.num_timesteps, rollouts=callback.rollouts,
                      exposure_records=callback.exposure_rows, optimizer_steps=updates,
                      sample_presentations=updates*PPO_PARAMS["batch_size"],
                      ppo_epochs=int(model._n_updates), parameter_movement=movement,
                      endpoint_fingerprint=fingerprint(model.policy))
        for name in ("initial", "endpoint"):
            path = out / f"{name}.zip"
            result[name] = {"checkpoint": path.name, "sha256": _sha256(path), "bytes": path.stat().st_size}
        success = True
    except BaseException as error:
        result.update(error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        if model is not None:
            result.update(observed_macro_decisions=model.num_timesteps,
                          observed_optimizer_steps=optimizer_steps(model.policy))
        if callback is not None:
            result.update(observed_rollouts=callback.rollouts, callback_native_steps=callback.native_steps)
    finally:
        if vec is not None:
            if success:
                vec.close()
            else:
                _stop_failed_children(vec)
        progress = [json.loads(path.read_text()) for path in sorted((out / "training").glob("lane*.progress.json"))]
        result.update(lane_progress=progress, recorded_native_step_lower_bound=sum(row["native_steps"] for row in progress),
                      recorded_controller_work_lower_bound=_work_lower_bound(progress),
                      worker_cpu_seconds_sum=sum(row["worker_cpu_seconds"] for row in progress),
                      worker_wall_seconds_sum=sum(row["worker_wall_seconds"] for row in progress),
                      worker_peak_rss_kib_max=max((row["worker_peak_rss_kib"] for row in progress), default=None),
                      parent_wall_seconds=time.monotonic()-started,
                      parent_cpu_seconds=_cpu_seconds()-cpu_started, parent_peak_rss_kib=_rss_kib())
        _write_json(out / "training.json", result)
    return result
