"""The single fixed direct PPO fit, with requested-action and native reward audits."""

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
from experiments.candidates.uav_active_sensing.training import fingerprint, optimizer_steps, parameter_movement, _stop_failed_children
from .constants import HORIZON, N_ENVS, POLICY_SEED, ROLLOUTS, ROLLOUT_STEPS, OPTIMIZER_STEPS
from .macro_env import append_json, make_lane
from .policy import CommitmentPolicy

TOTAL_MACRO_STEPS = N_ENVS * ROLLOUT_STEPS * ROLLOUTS
PPO_PARAMS = dict(learning_rate=.0003, n_steps=ROLLOUT_STEPS, batch_size=100, n_epochs=10,
                  gamma=1., gae_lambda=.95, clip_range=.2, normalize_advantage=True,
                  ent_coef=0., vf_coef=.5, max_grad_norm=.5, target_kl=None,
                  seed=POLICY_SEED, device="cpu")
POLICY_KWARGS = dict(net_arch=dict(pi=[128, 128], vf=[128, 128]),
                     activation_fn=torch.nn.Tanh, ortho_init=True)


def attach_gradient_audit(policy, path):
    state = {"pre_step_records": 0, "maximum_post_clip_norm": 0.0}
    def inspect(optimizer, args, kwargs):
        gradients = [parameter.grad.detach() for parameter in policy.parameters() if parameter.grad is not None]
        if not gradients or any(not torch.isfinite(gradient).all() for gradient in gradients):
            raise FloatingPointError("missing or nonfinite gradient before optimizer step")
        norm = float(torch.sqrt(sum(torch.sum(gradient.double()**2) for gradient in gradients)))
        state["pre_step_records"] += 1
        state["maximum_post_clip_norm"] = max(state["maximum_post_clip_norm"], norm)
        append_json(path, dict(pre_step=state["pre_step_records"], finite=True,
                               post_clip_l2=norm, tensors=len(gradients),
                               nonzero_tensors=sum(bool(torch.count_nonzero(g)) for g in gradients)))
    handle = policy.optimizer.register_step_pre_hook(inspect)
    return state, handle


class TrainingAudit(BaseCallback):
    def __init__(self, out):
        super().__init__()
        self.out = Path(out)
        self.rollouts = self.native_steps = self.loss_rows = self.exposure_rows = 0

    def _record_update(self):
        steps = optimizer_steps(self.model.policy)
        if not steps:
            return
        losses = {key: float(value) if np.isfinite(float(value)) else None
                  for key, value in self.model.logger.name_to_value.items() if np.isscalar(value)}
        if any(value is None for key, value in losses.items()
               if key.startswith("train/") and key != "train/explained_variance"):
            raise FloatingPointError("nonfinite PPO statistic")
        self.loss_rows += 1
        append_json(self.out / "training" / "updates.jsonl",
                    dict(update=self.loss_rows, optimizer_steps=steps,
                         macro_decisions=self.model.num_timesteps, losses=losses))

    def _on_rollout_start(self):
        self._record_update()
        self.rewards, self.actions = [], []

    def _on_step(self):
        infos = self.locals["infos"]
        actions = np.asarray(self.locals["actions"]).reshape(-1)
        if len(infos) != N_ENVS or any(info.get("TimeLimit.truncated", False) for info in infos):
            raise RuntimeError("wrong lanes or forbidden finite-horizon bootstrap")
        if any(info["macro_native_steps"] != 30 for info in infos):
            raise RuntimeError("incomplete native macro")
        if any(int(action) != info["choice"]["requested_action"] for action, info in zip(actions, infos)):
            raise RuntimeError("requested PPO action changed")
        with torch.no_grad():
            law = self.model.policy.get_distribution(self.locals["obs_tensor"])
            statistics = {key: value.cpu().numpy() for key, value in law.statistics().items()}
            probabilities = law.distribution.probs.cpu().numpy()
        logp = self.locals["log_probs"].detach().cpu().numpy()
        for lane, (action, info) in enumerate(zip(actions, infos)):
            append_json(self.out / "training" / "exposure.jsonl", {
                "world_seed": info["world_seed"], "macro_start": info["macro_start"],
                **info["choice"], "sampled_log_probability": float(logp[lane]),
                "sampled_joint_probability": float(np.exp(logp[lane])),
                "probabilities": probabilities[lane].tolist(),
                **{key: float(value[lane]) for key, value in statistics.items()},
            })
            self.exposure_rows += 1
        self.rewards.append([info["native_reward_sum"] for info in infos])
        self.actions.append(actions.copy())
        self.native_steps += sum(info["macro_native_steps"] for info in infos)
        return True

    def _on_rollout_end(self):
        buffer = self.model.rollout_buffer
        rewards = np.asarray(self.rewards, dtype=np.float32)
        actions = np.asarray(self.actions, dtype=np.float32)[..., None]
        if not buffer.full or len(self.rewards) != ROLLOUT_STEPS:
            raise RuntimeError("incomplete PPO rollout")
        if not np.array_equal(buffer.rewards, rewards) or not np.array_equal(buffer.actions, actions):
            raise RuntimeError("stored requested actions or native summed rewards differ")
        if not np.asarray(self.locals["dones"]).all():
            raise RuntimeError("rollout must end all four finite worlds")
        episodes = [info["native_episode"] for info in self.locals["infos"]]
        if any(row["actual_length"] != HORIZON for row in episodes):
            raise RuntimeError("wrong native training horizon")
        self.rollouts += 1
        append_json(self.out / "training" / "rollouts.jsonl", {
            "rollout": self.rollouts, "macro_decisions": self.model.num_timesteps,
            "native_steps": self.native_steps, "seeds": [row["seed"] for row in episodes],
            "native_J": [row["raw_native_J"] for row in episodes],
            "qos_per_step": [row["qos_per_step"] for row in episodes],
            "requested_service_fraction": float(np.mean(actions == 0)),
            "stored_native_rewards_exact_float32": True,
            "stored_requested_actions_exact": True, "all_finite_horizon_dones": True,
        })

    def _on_training_end(self):
        self._record_update()


def train(out):
    out = Path(out)
    (out / "training").mkdir()
    started, cpu_started = time.monotonic(), _cpu_seconds()
    result = dict(status="incomplete", fits_started=0,
                  sb3_version=stable_baselines3.__version__, policy_seed=POLICY_SEED)
    vec = model = callback = gradient_handle = None
    gradient_state = {}
    success = False
    try:
        torch.set_num_threads(1)
        if torch.get_default_dtype() != torch.float32:
            raise RuntimeError("FP32 learner required")
        vec = SubprocVecEnv.__new__(SubprocVecEnv)
        vec.__init__([partial(make_lane, lane, str(out)) for lane in range(N_ENVS)], start_method="spawn")
        model = PPO(CommitmentPolicy, vec, **PPO_PARAMS, policy_kwargs=POLICY_KWARGS)
        model.set_logger(configure(folder=str(out / "training"), format_strings=[]))
        before = {name: value.detach().cpu().clone() for name, value in model.policy.state_dict().items()}
        result["initial_fingerprint"] = fingerprint(model.policy)
        # Initialization is evidence, never a scored fourth arm or checkpoint selector.
        model.save(out / "initial.zip")
        callback = TrainingAudit(out)
        gradient_state, gradient_handle = attach_gradient_audit(model.policy, out/"training"/"gradients.jsonl")
        result["fits_started"] = 1
        _write_json(out / "training.json", result)
        model.learn(total_timesteps=TOTAL_MACRO_STEPS, callback=callback, log_interval=1, progress_bar=False)
        counts = vec.env_method("counts")
        steps = optimizer_steps(model.policy)
        expected = dict(native_steps=48000, macro_steps=1600,
                        episodes_started=16, episodes_completed=16, exhausted=True)
        if (model.num_timesteps != TOTAL_MACRO_STEPS or callback.rollouts != ROLLOUTS
                or steps != OPTIMIZER_STEPS or callback.loss_rows != ROLLOUTS
                or callback.exposure_rows != TOTAL_MACRO_STEPS
                or gradient_state["pre_step_records"] != OPTIMIZER_STEPS
                or any(row["lane"] != i or any(row[key] != value for key, value in expected.items())
                       for i, row in enumerate(counts))):
            raise RuntimeError("fixed training schedule or optimizer counts differ")
        model.save(out / "endpoint.zip")
        movement = parameter_movement(before, model.policy)
        result.update(status="complete", lane_counts=counts, actual_native_steps=callback.native_steps,
                      macro_decisions=model.num_timesteps, rollouts=callback.rollouts,
                      exposure_records=callback.exposure_rows, optimizer_steps=steps,
                      ppo_epochs=int(model._n_updates), parameter_movement=movement,
                      endpoint_fingerprint=fingerprint(model.policy))
        for label, filename in (("initial", "initial.zip"), ("endpoint", "endpoint.zip")):
            result[label] = dict(checkpoint=filename, sha256=_sha256(out / filename), bytes=(out / filename).stat().st_size)
        success = True
    except BaseException as error:
        result.update(error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        if model is not None:
            result.update(observed_macro_decisions=model.num_timesteps,
                          observed_optimizer_steps=optimizer_steps(model.policy))
        if callback is not None:
            result.update(observed_rollouts=callback.rollouts, callback_native_steps=callback.native_steps)
    finally:
        if gradient_handle is not None:
            gradient_handle.remove()
        if vec is not None:
            vec.close() if success else _stop_failed_children(vec)
        progress = [json.loads(path.read_text()) for path in sorted((out / "training").glob("lane*.progress.json"))]
        result.update(lane_progress=progress, gradient_health=gradient_state,
                      recorded_native_step_lower_bound=sum(row["native_steps"] for row in progress),
                      worker_cpu_seconds_sum=sum(row["worker_cpu_seconds"] for row in progress),
                      worker_wall_seconds_sum=sum(row["worker_wall_seconds"] for row in progress),
                      worker_peak_rss_kib_max=max((row["worker_peak_rss_kib"] for row in progress), default=None),
                      parent_wall_seconds=time.monotonic()-started,
                      parent_cpu_seconds=_cpu_seconds()-cpu_started, parent_peak_rss_kib=_rss_kib())
        _write_json(out / "training.json", result)
    return result
