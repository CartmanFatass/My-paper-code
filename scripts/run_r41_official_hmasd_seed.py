"""Run the original-source HMASD Alice-and-Bob local access pilot.

This module is deliberately an external wrapper.  It imports the untouched
official source tree, records optimizer/replay evidence, saves complete exact
checkpoints, and evaluates those checkpoints with the official deterministic
evaluator semantics.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import platform
import random
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "EXP-20260716-r41a-hmasd-alice-bob-local-pilot"
SOURCE_ARCHIVE = "ref/hmasd.tar"
SOURCE_TREE_LAYOUT = "hmasd/"
EXPECTED_OUTER_UPDATES = 937
EXPECTED_ENV_STEPS = 1_499_200
EXPECTED_OPTIMIZER_STEPS = 14_055
EVAL_EPISODES = 100


class ExternalSummaryWriter:
    """Logging-only sink that avoids TensorBoard worker queues."""

    def __init__(self, log_dir: str) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def add_scalars(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def export_scalars_to_json(self, path: str) -> None:
        Path(path).write_text("{}\n", encoding="utf-8")

    def close(self) -> None:
        return None


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(payload, indent=2, sort_keys=True, default=json_default)
    temporary.write_text(text, encoding="utf-8")
    for attempt in range(10):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 9:
                path.write_text(text, encoding="utf-8")
                try:
                    temporary.unlink(missing_ok=True)
                except PermissionError:
                    pass
                return
            time.sleep(0.05)


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"cannot JSON-encode {type(value).__name__}")


def source_identity(source_archive: Path, source_root: Path) -> dict[str, Any]:
    required_entry = source_root / "hmasd" / "scripts" / "train" / "train_alice_and_bob.py"
    return {
        "archive_repo_relative": SOURCE_ARCHIVE,
        "archive_path": str(source_archive.resolve()),
        "archive_present": source_archive.is_file(),
        "tree_root": str(source_root.resolve()),
        "tree_layout": SOURCE_TREE_LAYOUT,
        "required_entry_present": required_entry.is_file(),
    }


def capture_rng(torch_module: Any) -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch_module.get_rng_state(),
        "torch_cuda": torch_module.cuda.get_rng_state_all(),
    }


def restore_rng(torch_module: Any, state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch_module.set_rng_state(state["torch_cpu"])
    torch_module.cuda.set_rng_state_all(state["torch_cuda"])


def tensor_tree_finite(torch_module: Any, value: Any) -> bool:
    if torch_module.is_tensor(value):
        if value.is_floating_point() or value.is_complex():
            return bool(torch_module.isfinite(value).all().item())
        return True
    if isinstance(value, dict):
        return all(tensor_tree_finite(torch_module, item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(tensor_tree_finite(torch_module, item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def checkpoint_payload(torch_module: Any, runner: Any, seed: int, outer_updates: int) -> dict[str, Any]:
    value_norms: dict[str, Any] = {}
    if runner.h_trainer.value_normalizer is not None:
        value_norms["high"] = runner.h_trainer.value_normalizer.state_dict()
    if runner.l_trainer.value_normalizer is not None:
        value_norms["low"] = runner.l_trainer.value_normalizer.state_dict()
    return {
        "schema": "r41_official_hmasd_complete_checkpoint_v1",
        "source_archive": SOURCE_ARCHIVE,
        "seed": seed,
        "outer_updates": outer_updates,
        "modules": {
            "high_policy": runner.h_policy.transformer.state_dict(),
            "low_actor": runner.l_policy.actor.state_dict(),
            "low_critic": runner.l_policy.critic.state_dict(),
            "team_discriminator": runner.discri.team_discri.state_dict(),
            "individual_discriminator": runner.discri.indi_discri.state_dict(),
        },
        "optimizers": {
            "high": runner.h_policy.optimizer.state_dict(),
            "low_actor": runner.l_policy.actor_optimizer.state_dict(),
            "low_critic": runner.l_policy.critic_optimizer.state_dict(),
            "team_discriminator": runner.discri.team_discri_optimizer.state_dict(),
            "individual_discriminator": runner.discri.indi_discri_optimizer.state_dict(),
        },
        "value_norms": value_norms,
        "rng": capture_rng(torch_module),
    }


def save_complete_checkpoint(
    torch_module: Any,
    runner: Any,
    path: Path,
    seed: int,
    outer_updates: int,
) -> dict[str, Any]:
    payload = checkpoint_payload(torch_module, runner, seed, outer_updates)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch_module.save(payload, path)
    component_names = {
        "modules": sorted(payload["modules"]),
        "optimizers": sorted(payload["optimizers"]),
        "value_norms": sorted(payload["value_norms"]),
    }
    return {
        "path": str(path.resolve()),
        "schema": payload["schema"],
        "outer_updates": outer_updates,
        "components": component_names,
        "finite": tensor_tree_finite(torch_module, payload),
        "selection": "zero_step" if outer_updates == 0 else "exact_final",
    }


def load_complete_checkpoint(torch_module: Any, runner: Any, path: Path) -> None:
    try:
        payload = torch_module.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        payload = torch_module.load(path, map_location="cpu")
    runner.h_policy.transformer.load_state_dict(payload["modules"]["high_policy"])
    runner.l_policy.actor.load_state_dict(payload["modules"]["low_actor"])
    runner.l_policy.critic.load_state_dict(payload["modules"]["low_critic"])
    runner.discri.team_discri.load_state_dict(payload["modules"]["team_discriminator"])
    runner.discri.indi_discri.load_state_dict(payload["modules"]["individual_discriminator"])
    runner.h_policy.optimizer.load_state_dict(payload["optimizers"]["high"])
    runner.l_policy.actor_optimizer.load_state_dict(payload["optimizers"]["low_actor"])
    runner.l_policy.critic_optimizer.load_state_dict(payload["optimizers"]["low_critic"])
    runner.discri.team_discri_optimizer.load_state_dict(
        payload["optimizers"]["team_discriminator"]
    )
    runner.discri.indi_discri_optimizer.load_state_dict(
        payload["optimizers"]["individual_discriminator"]
    )
    if "high" in payload["value_norms"]:
        runner.h_trainer.value_normalizer.load_state_dict(payload["value_norms"]["high"])
    if "low" in payload["value_norms"]:
        runner.l_trainer.value_normalizer.load_state_dict(payload["value_norms"]["low"])
    restore_rng(torch_module, payload["rng"])


def install_optimizer_counter(torch_module: Any, optimizer: Any, name: str) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "steps": 0,
        "gradient_checks": 0,
        "all_checked_gradients_finite": True,
        "ever_nonzero_gradient": False,
        "first_nonzero_gradient_norm": None,
    }
    original_step = optimizer.step

    def counted_step(*args: Any, **kwargs: Any) -> Any:
        stats["steps"] += 1
        if not stats["ever_nonzero_gradient"] and stats["gradient_checks"] < 100:
            stats["gradient_checks"] += 1
            gradients = [
                parameter.grad.detach()
                for group in optimizer.param_groups
                for parameter in group["params"]
                if parameter.grad is not None
            ]
            finite = bool(gradients) and all(
                bool(torch_module.isfinite(gradient).all().item())
                for gradient in gradients
            )
            stats["all_checked_gradients_finite"] = bool(
                stats["all_checked_gradients_finite"] and finite
            )
            if finite:
                squared_norm = sum(
                    float(gradient.float().pow(2).sum().item())
                    for gradient in gradients
                )
                norm = math.sqrt(squared_norm)
                if norm > 0.0:
                    stats["ever_nonzero_gradient"] = True
                    stats["first_nonzero_gradient_norm"] = norm
        return original_step(*args, **kwargs)

    optimizer.step = counted_step
    stats["name"] = name
    return stats


def replay_audit(torch_module: Any, runner: Any) -> dict[str, float]:
    rng = capture_rng(torch_module)
    try:
        runner.h_trainer.prep_rollout()
        high_error = 0.0
        # Preserve the collection batch geometry; PPO minibatch repacking changes
        # the floating-point kernel and is not a replay of the behavior call.
        with torch_module.no_grad():
            for step in range(runner.h_buffer.episode_length):
                _, high_replayed_logp, _ = runner.h_policy.evaluate_actions(
                    np.concatenate(runner.h_buffer.share_obs[step]),
                    np.concatenate(runner.h_buffer.obs[step]),
                    np.concatenate(runner.h_buffer.actions[step]),
                )
                high_old = torch_module.as_tensor(
                    np.concatenate(runner.h_buffer.action_log_probs[step]),
                    dtype=high_replayed_logp.dtype,
                    device=high_replayed_logp.device,
                )
                high_error = max(
                    high_error,
                    float((high_replayed_logp - high_old).abs().max().item()),
                )

        runner.l_trainer.prep_rollout()
        low_error = 0.0
        # Each step reuses the exact env-agent order and recurrent state used by
        # l_collect, so this measures stored-likelihood parity rather than chunking.
        with torch_module.no_grad():
            for step in range(runner.l_buffer.episode_length):
                available_actions = None
                if runner.l_buffer.available_actions is not None:
                    available_actions = np.concatenate(
                        runner.l_buffer.available_actions[step]
                    )
                _, low_replayed_logp, _ = runner.l_policy.evaluate_actions(
                    np.concatenate(runner.l_buffer.share_obs[step]),
                    np.concatenate(runner.l_buffer.obs[step]),
                    np.concatenate(runner.l_buffer.team_skill[step]),
                    np.concatenate(runner.l_buffer.indi_skill[step]),
                    np.concatenate(runner.l_buffer.rnn_states[step]),
                    np.concatenate(runner.l_buffer.rnn_states_critic[step]),
                    np.concatenate(runner.l_buffer.actions[step]),
                    np.concatenate(runner.l_buffer.masks[step]),
                    available_actions,
                    np.concatenate(runner.l_buffer.active_masks[step]),
                )
                low_old = torch_module.as_tensor(
                    np.concatenate(runner.l_buffer.action_log_probs[step]),
                    dtype=low_replayed_logp.dtype,
                    device=low_replayed_logp.device,
                )
                low_error = max(
                    low_error,
                    float((low_replayed_logp - low_old).abs().max().item()),
                )
        return {
            "high_max_abs_logp_error": high_error,
            "low_max_abs_logp_error": low_error,
            "global_max_abs_logp_error": max(high_error, low_error),
        }
    finally:
        restore_rng(torch_module, rng)


def exact_official_evaluation(
    torch_module: Any,
    np_module: Any,
    runner: Any,
    make_eval_env: Any,
    all_args: Any,
    seed: int,
) -> dict[str, Any]:
    eval_envs = make_eval_env(all_args)
    try:
        won = 0
        key0 = 0
        key1 = 0
        steps: list[int] = []
        wins: list[int] = []
        key0_rows: list[int] = []
        key1_rows: list[int] = []
        obs, share_obs, available_actions = eval_envs.reset()
        for _ in range(EVAL_EPISODES):
            rnn_states = np_module.zeros(
                (
                    all_args.n_eval_rollout_threads,
                    runner.num_agents,
                    runner.recurrent_N,
                    runner.hidden_size,
                ),
                dtype=np_module.float32,
            )
            masks = np_module.ones(
                (all_args.n_eval_rollout_threads, runner.num_agents, 1),
                dtype=np_module.float32,
            )
            episode_steps = 0
            while True:
                if episode_steps % runner.skill_interval == 0:
                    runner.h_trainer.prep_rollout()
                    high_actions = runner.h_policy.act(
                        np_module.concatenate(share_obs),
                        np_module.concatenate(obs),
                        deterministic=True,
                    )
                    high_actions = np_module.array(
                        np_module.split(
                            high_actions.detach().cpu().numpy(),
                            all_args.n_eval_rollout_threads,
                        )
                    )
                    team_skill = high_actions[:, 0]
                    team_skill = np_module.expand_dims(team_skill, 1).repeat(
                        runner.num_agents, 1
                    )
                    individual_skill = high_actions[:, 1:]

                runner.l_trainer.prep_rollout()
                low_actions, next_rnn_states = runner.l_policy.act(
                    np_module.concatenate(obs),
                    np_module.concatenate(team_skill),
                    np_module.concatenate(individual_skill),
                    np_module.concatenate(rnn_states),
                    np_module.concatenate(masks),
                    np_module.concatenate(available_actions),
                    deterministic=True,
                )
                low_actions = np_module.array(
                    np_module.split(
                        low_actions.detach().cpu().numpy(),
                        all_args.n_eval_rollout_threads,
                    )
                )
                rnn_states = np_module.array(
                    np_module.split(
                        next_rnn_states.detach().cpu().numpy(),
                        all_args.n_eval_rollout_threads,
                    )
                )
                obs, share_obs, _, dones, infos, available_actions = eval_envs.step(
                    low_actions
                )
                episode_steps += 1
                if bool(np_module.all(dones, axis=1)[0]):
                    info = infos[0][0]
                    episode_won = int(bool(info["battle_won"]))
                    episode_key0 = int(bool(info["key0"]))
                    episode_key1 = int(bool(info["key1"]))
                    won += episode_won
                    key0 += episode_key0
                    key1 += episode_key1
                    wins.append(episode_won)
                    key0_rows.append(episode_key0)
                    key1_rows.append(episode_key1)
                    steps.append(episode_steps)
                    break
        return {
            "evaluator": "official_deterministic_alice_bob_semantics",
            "episodes": EVAL_EPISODES,
            "eval_threads": all_args.n_eval_rollout_threads,
            "high_deterministic": True,
            "low_deterministic": True,
            "reset_stream": {
                "construction_seed": seed * 50_000,
                "rank_stride": 10_000,
                "episode_indices": list(range(EVAL_EPISODES)),
            },
            "win_rate": won / EVAL_EPISODES,
            "key0_rate": key0 / EVAL_EPISODES,
            "key1_rate": key1 / EVAL_EPISODES,
            "average_episode_steps": float(np_module.mean(steps)),
            "episode_wins": wins,
            "episode_key0": key0_rows,
            "episode_key1": key1_rows,
            "episode_steps": steps,
        }
    finally:
        eval_envs.close()


def runtime_manifest(torch_module: Any) -> dict[str, Any]:
    try:
        packages = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except Exception as exc:  # pragma: no cover - diagnostic only
        packages = [f"pip-freeze-error: {exc}"]
    distributions = {}
    for name in (
        "numpy",
        "gym",
        "tensorboardX",
        "wandb",
        "opencv-python",
        "matplotlib",
        "absl-py",
        "setproctitle",
    ):
        try:
            distributions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            distributions[name] = None
    return {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "torch": torch_module.__version__,
        "cuda_available": bool(torch_module.cuda.is_available()),
        "torch_cuda": torch_module.version.cuda,
        "cudnn": torch_module.backends.cudnn.version(),
        "gpu": torch_module.cuda.get_device_name(0),
        "selected_packages": distributions,
        "pip_freeze": packages,
    }


def official_argument_vector(seed: int) -> list[str]:
    return [
        "--game_version", "0",
        "--env_name", "alice_and_bob",
        "--algorithm_name", "hmasd",
        "--seed", str(seed),
        "--num_env_steps", "1499200",
        "--episode_length", "100",
        "--n_rollout_threads", "16",
        "--skill_type", "Discrete",
        "--skill_interval", "50",
        "--team_skill_dim", "2",
        "--indi_skill_dim", "4",
        "--use_recurrent_discri", "0",
        "--d_epoch", "15",
        "--skill_last_layer", "1",
        "--intri_rew_exp", "0",
        "--h_entropy_coef", "0.1",
        "--h_lr", "0.0005",
        "--h_critic_lr", "0.0005",
        "--l_lr", "0.0005",
        "--l_critic_lr", "0.0005",
        "--d_team_lr", "0.0005",
        "--d_indi_lr", "0.0005",
        "--policy_use_both_skill", "0",
        "--lambda_team", "0.1",
        "--lambda_indi", "0.2",
        "--lambda_env", "0.0",
        "--eval_episodes", "100",
    ]


def selected_arguments(all_args: Any) -> dict[str, Any]:
    names = (
        "game_version", "env_name", "algorithm_name", "experiment_name",
        "seed", "num_env_steps", "episode_length", "n_rollout_threads",
        "n_eval_rollout_threads", "n_training_threads", "skill_type",
        "skill_interval", "team_skill_dim", "indi_skill_dim",
        "use_recurrent_discri", "d_epoch", "d_num_mini_batch",
        "skill_last_layer", "intri_rew_exp", "h_entropy_coef", "h_lr",
        "h_critic_lr", "l_lr", "l_critic_lr", "d_team_lr", "d_indi_lr",
        "policy_use_both_skill", "lambda_env", "lambda_team", "lambda_indi",
        "eval_episodes", "h_ppo_epoch", "h_num_mini_batch", "l_ppo_epoch",
        "l_num_mini_batch", "hidden_size", "n_embd", "n_block", "n_head",
        "use_valuenorm", "use_eval", "model_dir",
    )
    return {name: getattr(all_args, name) for name in names}


def run_seed(
    source_archive: Path,
    source_root: Path,
    output_root: Path,
    seed: int,
) -> dict[str, Any]:
    identity_before = source_identity(source_archive, source_root)
    if not identity_before["archive_present"]:
        raise RuntimeError(f"official HMASD source archive is missing: {source_archive}")

    official_root = source_root
    if not (official_root / "hmasd" / "scripts" / "train" / "train_alice_and_bob.py").is_file():
        raise RuntimeError(f"official HMASD source tree missing under {official_root}")
    sys.path.insert(0, str(official_root))
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("WANDB_MODE", "disabled")

    import torch
    from hmasd.config import get_config
    import hmasd.runner.shared.base_runner as official_base_runner
    from hmasd.runner.shared.alice_and_bob_runner import AliceBobRunner
    from hmasd.scripts.train.train_alice_and_bob import (
        make_eval_env,
        make_train_env,
        parse_args,
    )

    if not torch.cuda.is_available():
        raise RuntimeError("R41 formal reproduction requires CUDA")
    official_base_runner.SummaryWriter = ExternalSummaryWriter
    device = torch.device("cuda:0")
    torch.set_num_threads(16)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    parser = get_config()
    all_args = parse_args(official_argument_vector(seed), parser)
    if all_args.model_dir is not None:
        raise RuntimeError("R41 must start from fresh initialization")

    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    official_run_dir = output_root / "official_runner"
    official_run_dir.mkdir(parents=True, exist_ok=True)
    all_args.run_dir = official_run_dir
    envs = make_train_env(all_args)
    eval_envs = make_eval_env(all_args) if all_args.use_eval else None
    config = {
        "all_args": all_args,
        "envs": envs,
        "eval_envs": eval_envs,
        "num_agents": 2,
        "device": device,
        "run_dir": official_run_dir,
    }
    runner = AliceBobRunner(config)

    env_contract = {
        "agents": len(envs.action_space),
        "obs": int(envs.observation_space[0][0]),
        "state": int(envs.share_observation_space[0][0]),
        "actions": int(envs.action_space[0].n),
        "horizon": int(all_args.episode_length),
    }

    optimizers = {
        "high": runner.h_policy.optimizer,
        "low_actor": runner.l_policy.actor_optimizer,
        "low_critic": runner.l_policy.critic_optimizer,
        "team_discriminator": runner.discri.team_discri_optimizer,
        "individual_discriminator": runner.discri.indi_discri_optimizer,
    }
    optimizer_stats = {
        name: install_optimizer_counter(torch, optimizer, name)
        for name, optimizer in optimizers.items()
    }
    telemetry: dict[str, Any] = {
        "outer_updates": 0,
        "actual_env_steps": 0,
        "replay": None,
        "optimizers": optimizer_stats,
    }
    progress_path = output_root / "progress.json"
    original_train = runner.train

    def instrumented_train() -> dict[str, Any]:
        if telemetry["outer_updates"] == 0:
            telemetry["replay"] = replay_audit(torch, runner)
        train_info = original_train()
        telemetry["outer_updates"] += 1
        telemetry["actual_env_steps"] = (
            telemetry["outer_updates"]
            * all_args.episode_length
            * all_args.n_rollout_threads
        )
        atomic_json(
            progress_path,
            {
                "state": "training",
                "seed": seed,
                "outer_updates": telemetry["outer_updates"],
                "expected_outer_updates": EXPECTED_OUTER_UPDATES,
                "actual_env_steps": telemetry["actual_env_steps"],
                "expected_env_steps": EXPECTED_ENV_STEPS,
                "optimizer_steps": {
                    name: stats["steps"] for name, stats in optimizer_stats.items()
                },
                "updated_unix": time.time(),
            },
        )
        return train_info

    runner.train = instrumented_train

    checkpoint_root = output_root / "checkpoints"
    zero_checkpoint_path = checkpoint_root / "zero_step.pt"
    final_checkpoint_path = checkpoint_root / "exact_final.pt"
    zero_checkpoint = save_complete_checkpoint(
        torch, runner, zero_checkpoint_path, seed, 0
    )
    load_complete_checkpoint(torch, runner, zero_checkpoint_path)
    zero_eval = exact_official_evaluation(
        torch, np, runner, make_eval_env, all_args, seed
    )
    load_complete_checkpoint(torch, runner, zero_checkpoint_path)

    started = time.time()
    try:
        runner.run()
    finally:
        envs.close()
        if eval_envs is not None and eval_envs is not envs:
            eval_envs.close()

    final_checkpoint = save_complete_checkpoint(
        torch,
        runner,
        final_checkpoint_path,
        seed,
        int(telemetry["outer_updates"]),
    )
    load_complete_checkpoint(torch, runner, final_checkpoint_path)
    final_eval = exact_official_evaluation(
        torch, np, runner, make_eval_env, all_args, seed
    )
    identity_after = source_identity(source_archive, source_root)

    if hasattr(runner, "writter"):
        runner.writter.export_scalars_to_json(
            str(Path(runner.log_dir) / "summary.json")
        )
        runner.writter.close()

    result = {
        "experiment_id": EXPERIMENT_ID,
        "seed": seed,
        "state": "completed",
        "source": {
            "before": identity_before,
            "after": identity_after,
            "archive_repo_relative": SOURCE_ARCHIVE,
            "tree_layout": SOURCE_TREE_LAYOUT,
            "fresh_extract": True,
        },
        "runtime": runtime_manifest(torch),
        "official_arguments": selected_arguments(all_args),
        "official_argument_vector": official_argument_vector(seed),
        "environment": env_contract,
        "algorithm_boundary": {
            "source_algorithm": "official_fixed_k_hmasd",
            "high_reward": "environment_reward_only",
            "low_reward": "0.0*environment+0.1*q_D+0.2*q_d",
            "extra_shaping": False,
            "extra_intrinsic": False,
            "current_repo_process_path": False,
            "fresh_initialization": True,
            "logging_sink": "external_synchronous_noop",
        },
        "telemetry": telemetry,
        "checkpoints": {
            "zero_step": zero_checkpoint,
            "exact_final": final_checkpoint,
        },
        "evaluations": {
            "zero_step": zero_eval,
            "exact_final": final_eval,
        },
        "elapsed_seconds": time.time() - started,
    }
    atomic_json(output_root / "seed_result.json", result)
    atomic_json(
        progress_path,
        {
            "state": "completed",
            "seed": seed,
            "outer_updates": telemetry["outer_updates"],
            "expected_outer_updates": EXPECTED_OUTER_UPDATES,
            "actual_env_steps": telemetry["actual_env_steps"],
            "expected_env_steps": EXPECTED_ENV_STEPS,
            "zero_win_rate": zero_eval["win_rate"],
            "final_win_rate": final_eval["win_rate"],
            "updated_unix": time.time(),
        },
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-archive", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--seed", required=True, type=int, choices=range(1, 6))
    args = parser.parse_args()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "seed_status.json"
    atomic_json(
        status_path,
        {
            "state": "running",
            "seed": args.seed,
            "source_archive": SOURCE_ARCHIVE,
            "started_unix": time.time(),
        },
    )
    try:
        result = run_seed(
            Path(args.source_archive).resolve(),
            Path(args.source_root).resolve(),
            output_root,
            args.seed,
        )
    except Exception as exc:
        atomic_json(
            status_path,
            {
                "state": "failed",
                "seed": args.seed,
                "source_archive": SOURCE_ARCHIVE,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "finished_unix": time.time(),
            },
        )
        raise
    atomic_json(
        status_path,
        {
            "state": "completed",
            "seed": args.seed,
            "source_archive": SOURCE_ARCHIVE,
            "final_win_rate": result["evaluations"]["exact_final"]["win_rate"],
            "finished_unix": time.time(),
        },
    )


if __name__ == "__main__":
    main()
