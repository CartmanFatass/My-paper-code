"""One fixed SB3 PPO fit. No custom learner or model-based transition is used."""

from __future__ import annotations

from functools import partial
import hashlib
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

from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds, _rss_kib, _sha256, _write_json,
)

from .macro_env import HORIZON, N_ENVS, POLICY_SEED, make_lane


ROLLOUT_STEPS = 100
ROLLOUTS = 40
TOTAL_MACRO_STEPS = N_ENVS * ROLLOUT_STEPS * ROLLOUTS
OPTIMIZER_STEPS = 1600
PPO_PARAMS = {
    "learning_rate": .0003, "n_steps": ROLLOUT_STEPS, "batch_size": 100, "n_epochs": 10,
    "gamma": 1.0, "gae_lambda": .95, "clip_range": .2, "normalize_advantage": True,
    "ent_coef": .01, "vf_coef": .5, "max_grad_norm": .5,
    "target_kl": None, "seed": POLICY_SEED, "device": "cpu",
}


def fingerprint(policy):
    digest = hashlib.sha256()
    for name, value in sorted(policy.state_dict().items()):
        array = value.detach().cpu().numpy()
        digest.update(name.encode("utf-8"))
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def optimizer_steps(policy):
    counts = [int(state["step"].item()) for state in policy.optimizer.state.values() if "step" in state]
    if counts and len(set(counts)) != 1:
        raise RuntimeError("PPO optimizer parameters have inconsistent update counts")
    return counts[0] if counts else 0


def _scalars(mapping):
    return {key: float(value) if np.isfinite(float(value)) else None
            for key, value in mapping.items() if np.isscalar(value)}


def _append(path, row):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")


class TrainingAudit(BaseCallback):
    """Verify requested-action/reward storage and complete native rollouts in situ."""

    def __init__(self, out: Path):
        super().__init__()
        self.out = out
        self.rollouts = 0
        self.native_steps = 0
        self.loss_rows = 0

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
        actions = np.asarray(self.locals["actions"]).reshape(-1)
        if len(infos) != N_ENVS or any(info.get("TimeLimit.truncated", False) for info in infos):
            raise RuntimeError("wrong lane count or forbidden finite-horizon bootstrap")
        if any(info["macro_native_steps"] != 30 for info in infos):
            raise RuntimeError("incomplete native macro")
        if any(int(action) != info["choice"]["requested"] for action, info in zip(actions, infos)):
            raise RuntimeError("PPO did not execute its recorded requested action")
        self.rewards.append([info["native_reward_sum"] for info in infos])
        self.actions.append(actions.copy())
        self.native_steps += sum(info["macro_native_steps"] for info in infos)
        return True

    def _on_rollout_end(self):
        buffer = self.model.rollout_buffer
        expected_reward = np.asarray(self.rewards, dtype=np.float32)
        expected_action = np.asarray(self.actions, dtype=np.float32)[..., None]
        if not buffer.full or len(self.rewards) != ROLLOUT_STEPS:
            raise RuntimeError("PPO rollout is incomplete")
        if not np.array_equal(buffer.rewards, expected_reward):
            raise RuntimeError("native macro rewards changed before PPO storage")
        if not np.array_equal(buffer.actions, expected_action):
            raise RuntimeError("requested actions replaced by fallbacks in PPO storage")
        if not np.asarray(self.locals["dones"]).all():
            raise RuntimeError("rollout boundary does not end four finite native worlds")
        episodes = [info["native_episode"] for info in self.locals["infos"]]
        if any(row["actual_length"] != HORIZON for row in episodes):
            raise RuntimeError("training episode did not finish the fixed horizon")
        self.rollouts += 1
        _append(self.out / "training" / "rollouts.jsonl", {
            "rollout": self.rollouts, "macro_decisions": self.model.num_timesteps,
            "native_steps": self.native_steps, "seeds": [row["seed"] for row in episodes],
            "native_J": [row["raw_native_J"] for row in episodes],
            "qos_per_step": [row["qos_per_step"] for row in episodes],
            "requested_service_fraction": float(np.mean(expected_action == 0)),
            "stored_native_rewards_exact_float32": True,
            "stored_requested_actions_exact": True,
            "all_finite_horizon_dones": True,
        })

    def _on_training_end(self):
        self._record_update()


def parameter_movement(before, policy):
    groups = {"all": [], "actor": [], "critic": []}
    for name, value in policy.state_dict().items():
        difference = value.detach().cpu().double() - before[name].double()
        squared = float(torch.sum(difference ** 2))
        maximum = float(torch.max(torch.abs(difference)))
        groups["all"].append((squared, maximum))
        group = "actor" if "policy_net" in name or "action_net" in name else "critic"
        groups[group].append((squared, maximum))
    return {key: {"l2": float(np.sqrt(sum(row[0] for row in rows))),
                  "max_absolute": max((row[1] for row in rows), default=0.0)}
            for key, rows in groups.items()}


def _stop_failed_children(vec):
    # These are only this fit's subprocesses. Do not hang in VecEnv.close after EOF.
    processes = getattr(vec, "processes", [])
    for process in processes:
        if process.is_alive():
            process.terminate()
    for process in processes:
        process.join(timeout=10)
        if process.is_alive():
            process.kill()
            process.join(timeout=10)
    for remote in getattr(vec, "remotes", []):
        remote.close()


def train(out: Path):
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out = Path(out)
    (out / "training").mkdir()
    result = {"status": "incomplete", "fits_started": 0,
              "sb3_version": stable_baselines3.__version__, "policy_seed": POLICY_SEED}
    vec, model, callback = None, None, None
    success = False
    try:
        torch.set_num_threads(1)
        if torch.get_default_dtype() != torch.float32:
            raise RuntimeError("the fixed learner requires native FP32")
        # Keep the object reference even if startup fails partway through __init__.
        vec = SubprocVecEnv.__new__(SubprocVecEnv)
        vec.__init__([partial(make_lane, lane, str(out)) for lane in range(N_ENVS)], start_method="spawn")
        model = PPO("MlpPolicy", vec, **PPO_PARAMS,
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
        steps = optimizer_steps(model.policy)
        if (model.num_timesteps != TOTAL_MACRO_STEPS or callback.rollouts != ROLLOUTS
                or steps != OPTIMIZER_STEPS or callback.loss_rows != ROLLOUTS
                or any(any(row[key] != value for key, value in {
                    "lane": i, "native_steps": 120000, "macro_steps": 4000,
                    "episodes_started": 40, "episodes_completed": 40, "exhausted": True,
                }.items()) for i, row in enumerate(counts))):
            raise RuntimeError("fixed training schedule/optimizer counts differ")
        model.save(out / "endpoint.zip")
        movement = parameter_movement(before, model.policy)
        if movement["actor"]["l2"] == 0 or movement["critic"]["l2"] == 0:
            raise RuntimeError("PPO endpoint has no actor or critic parameter movement")
        result.update(status="complete", lane_counts=counts,
                      actual_native_steps=callback.native_steps,
                      macro_decisions=model.num_timesteps, rollouts=callback.rollouts,
                      optimizer_steps=steps, ppo_epochs=int(model._n_updates),
                      parameter_movement=movement, endpoint_fingerprint=fingerprint(model.policy))
        for arm, filename in (("L0", "initial.zip"), ("L1", "endpoint.zip")):
            result[arm] = {"checkpoint": filename, "sha256": _sha256(out / filename),
                           "bytes": (out / filename).stat().st_size}
        success = True
    except BaseException as error:
        result.update(error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        if model is not None:
            result.update(observed_macro_decisions=model.num_timesteps,
                          observed_optimizer_steps=optimizer_steps(model.policy))
        if callback is not None:
            result.update(observed_rollouts=callback.rollouts,
                          callback_native_steps=callback.native_steps)
    finally:
        if vec is not None:
            if success:
                vec.close()
            else:
                _stop_failed_children(vec)
        progress = [json.loads(path.read_text()) for path in sorted((out / "training").glob("lane*.progress.json"))]
        result.update(lane_progress=progress,
                      recorded_native_step_lower_bound=sum(row["native_steps"] for row in progress),
                      worker_cpu_seconds_sum=sum(row["worker_cpu_seconds"] for row in progress),
                      worker_wall_seconds_sum=sum(row["worker_wall_seconds"] for row in progress),
                      worker_peak_rss_kib_max=max((row["worker_peak_rss_kib"] for row in progress), default=None),
                      parent_wall_seconds=time.monotonic() - started,
                      parent_cpu_seconds=_cpu_seconds() - cpu_started,
                      parent_peak_rss_kib=_rss_kib())
        _write_json(out / "training.json", result)
    return result
