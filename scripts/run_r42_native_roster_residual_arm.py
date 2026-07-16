"""Run one R42-IRR continuation arm from the positive R41B checkpoint."""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np

from r42_native_roster_residual import (
    R42_MODES,
    install_native_roster_residual,
    residual_parameter_drift,
    summarize_event_ledger,
)
from run_r41_official_hmasd_seed import (
    ExternalSummaryWriter,
    atomic_json,
    capture_rng,
    checkpoint_payload,
    install_optimizer_counter,
    official_argument_vector,
    restore_rng,
    runtime_manifest,
    selected_arguments,
    source_identity,
    tensor_tree_finite,
)


EXPERIMENT_ID = "EXP-20260716-r42-irr-native-roster-residual"
SOURCE_ARCHIVE = "ref/hmasd.tar"
SOURCE_CHECKPOINT_SCHEMA = "r41_official_hmasd_complete_checkpoint_v1"
R42_CHECKPOINT_SCHEMA = "r42_native_roster_residual_checkpoint_v1"
ROLLOUT_ENVS = 16
ENV_STEPS = 320_000
OUTER_UPDATES = 200
EXPECTED_OPTIMIZER_STEPS = 3_000
EVAL_EPISODES = 100


def r42_argument_vector(seed: int, preflight_only: bool = False) -> list[str]:
    arguments = official_argument_vector(seed, "r41a")

    def replace(flag: str, value: str) -> None:
        index = arguments.index(flag)
        arguments[index + 1] = value

    replace("--num_env_steps", "100" if preflight_only else str(ENV_STEPS))
    replace("--n_rollout_threads", "1" if preflight_only else str(ROLLOUT_ENVS))
    arguments.extend(
        [
            "--n_training_threads",
            "1" if preflight_only else "8",
            "--save_interval",
            "1000",
            "--log_interval",
            "10",
            "--use_eval",
        ]
    )
    return arguments


def load_source_checkpoint(
    torch_module: Any, runner: Any, checkpoint_path: Path
) -> dict[str, Any]:
    try:
        payload = torch_module.load(
            checkpoint_path, map_location="cpu", weights_only=False
        )
    except TypeError:
        payload = torch_module.load(checkpoint_path, map_location="cpu")
    if payload.get("schema") != SOURCE_CHECKPOINT_SCHEMA:
        raise RuntimeError(
            f"R42 requires {SOURCE_CHECKPOINT_SCHEMA}, got {payload.get('schema')}"
        )
    runner.h_policy.transformer.load_state_dict(payload["modules"]["high_policy"])
    runner.l_policy.actor.load_state_dict(payload["modules"]["low_actor"])
    runner.l_policy.critic.load_state_dict(payload["modules"]["low_critic"])
    runner.discri.team_discri.load_state_dict(
        payload["modules"]["team_discriminator"]
    )
    runner.discri.indi_discri.load_state_dict(
        payload["modules"]["individual_discriminator"]
    )
    runner.h_policy.optimizer.load_state_dict(payload["optimizers"]["high"])
    runner.l_policy.actor_optimizer.load_state_dict(
        payload["optimizers"]["low_actor"]
    )
    runner.l_policy.critic_optimizer.load_state_dict(
        payload["optimizers"]["low_critic"]
    )
    runner.discri.team_discri_optimizer.load_state_dict(
        payload["optimizers"]["team_discriminator"]
    )
    runner.discri.indi_discri_optimizer.load_state_dict(
        payload["optimizers"]["individual_discriminator"]
    )
    if "high" in payload["value_norms"]:
        runner.h_trainer.value_normalizer.load_state_dict(
            payload["value_norms"]["high"]
        )
    if "low" in payload["value_norms"]:
        runner.l_trainer.value_normalizer.load_state_dict(
            payload["value_norms"]["low"]
        )
    restore_rng(torch_module, payload["rng"])
    return {
        "path": str(checkpoint_path.resolve()),
        "schema": payload["schema"],
        "seed": payload.get("seed"),
        "outer_updates": payload.get("outer_updates"),
        "module_names": sorted(payload["modules"]),
        "optimizer_names": sorted(payload["optimizers"]),
        "value_norm_names": sorted(payload["value_norms"]),
    }


def save_r42_checkpoint(
    torch_module: Any,
    runner: Any,
    path: Path,
    seed: int,
    mode: str,
    outer_updates: int,
) -> dict[str, Any]:
    payload = checkpoint_payload(torch_module, runner, seed, outer_updates)
    payload["schema"] = R42_CHECKPOINT_SCHEMA
    payload["r42"] = {
        "mode": mode,
        "residual_scale": float(
            runner.h_policy.transformer.r42_residual_scale
        ),
        "incumbent_roster_replay": True,
        "native_check_interval": 50,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    torch_module.save(payload, path)
    return {
        "path": str(path.resolve()),
        "schema": payload["schema"],
        "outer_updates": outer_updates,
        "finite": tensor_tree_finite(torch_module, payload),
        "selection": "exact_continuation_final",
        "components": {
            "modules": sorted(payload["modules"]),
            "optimizers": sorted(payload["optimizers"]),
            "value_norms": sorted(payload["value_norms"]),
        },
    }


def load_r42_checkpoint(torch_module: Any, runner: Any, path: Path) -> None:
    try:
        payload = torch_module.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        payload = torch_module.load(path, map_location="cpu")
    if payload.get("schema") != R42_CHECKPOINT_SCHEMA:
        raise RuntimeError("unexpected R42 checkpoint schema")
    runner.h_policy.transformer.load_state_dict(payload["modules"]["high_policy"])
    runner.l_policy.actor.load_state_dict(payload["modules"]["low_actor"])
    runner.l_policy.critic.load_state_dict(payload["modules"]["low_critic"])
    runner.discri.team_discri.load_state_dict(
        payload["modules"]["team_discriminator"]
    )
    runner.discri.indi_discri.load_state_dict(
        payload["modules"]["individual_discriminator"]
    )
    runner.h_policy.optimizer.load_state_dict(payload["optimizers"]["high"])
    runner.l_policy.actor_optimizer.load_state_dict(
        payload["optimizers"]["low_actor"]
    )
    runner.l_policy.critic_optimizer.load_state_dict(
        payload["optimizers"]["low_critic"]
    )
    runner.discri.team_discri_optimizer.load_state_dict(
        payload["optimizers"]["team_discriminator"]
    )
    runner.discri.indi_discri_optimizer.load_state_dict(
        payload["optimizers"]["individual_discriminator"]
    )
    if "high" in payload["value_norms"]:
        runner.h_trainer.value_normalizer.load_state_dict(
            payload["value_norms"]["high"]
        )
    if "low" in payload["value_norms"]:
        runner.l_trainer.value_normalizer.load_state_dict(
            payload["value_norms"]["low"]
        )
    restore_rng(torch_module, payload["rng"])


def replay_audit(torch_module: Any, runner: Any) -> dict[str, float]:
    rng = capture_rng(torch_module)
    try:
        runner.h_trainer.prep_rollout()
        high_error = 0.0
        with torch_module.no_grad():
            for step in range(runner.h_buffer.episode_length):
                _, replayed_logp, _ = runner.h_policy.evaluate_actions(
                    np.concatenate(runner.h_buffer.share_obs[step]),
                    np.concatenate(runner.h_buffer.obs[step]),
                    np.concatenate(runner.h_buffer.actions[step]),
                    incumbent_roster=runner.h_buffer.r42_incumbent_roster[step],
                )
                old_logp = torch_module.as_tensor(
                    np.concatenate(runner.h_buffer.action_log_probs[step]),
                    dtype=replayed_logp.dtype,
                    device=replayed_logp.device,
                )
                high_error = max(
                    high_error,
                    float((replayed_logp - old_logp).abs().max().item()),
                )

        runner.l_trainer.prep_rollout()
        low_error = 0.0
        with torch_module.no_grad():
            for step in range(runner.l_buffer.episode_length):
                available_actions = None
                if runner.l_buffer.available_actions is not None:
                    available_actions = np.concatenate(
                        runner.l_buffer.available_actions[step]
                    )
                _, replayed_logp, _ = runner.l_policy.evaluate_actions(
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
                old_logp = torch_module.as_tensor(
                    np.concatenate(runner.l_buffer.action_log_probs[step]),
                    dtype=replayed_logp.dtype,
                    device=replayed_logp.device,
                )
                low_error = max(
                    low_error,
                    float((replayed_logp - old_logp).abs().max().item()),
                )
        return {
            "high_max_abs_logp_error": high_error,
            "low_max_abs_logp_error": low_error,
            "global_max_abs_logp_error": max(high_error, low_error),
        }
    finally:
        restore_rng(torch_module, rng)


def exact_r42_evaluation(
    torch_module: Any,
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
        episode_steps_rows: list[int] = []
        wins: list[int] = []
        key0_rows: list[int] = []
        key1_rows: list[int] = []
        event_rows: list[dict[str, Any]] = []
        obs, share_obs, available_actions = eval_envs.reset()
        for episode_index in range(EVAL_EPISODES):
            rnn_states = np.zeros(
                (
                    all_args.n_eval_rollout_threads,
                    runner.num_agents,
                    runner.recurrent_N,
                    runner.hidden_size,
                ),
                dtype=np.float32,
            )
            masks = np.ones(
                (all_args.n_eval_rollout_threads, runner.num_agents, 1),
                dtype=np.float32,
            )
            current_roster = None
            episode_steps = 0
            while True:
                if episode_steps % runner.skill_interval == 0:
                    runner.h_trainer.prep_rollout()
                    incumbent = (
                        np.full((1, runner.num_agents), -1, dtype=np.int64)
                        if current_roster is None
                        else current_roster.copy()
                    )
                    high_actions = runner.h_policy.act(
                        np.concatenate(share_obs),
                        np.concatenate(obs),
                        deterministic=True,
                        incumbent_roster=incumbent,
                    )
                    high_actions = np.array(
                        np.split(
                            high_actions.detach().cpu().numpy(),
                            all_args.n_eval_rollout_threads,
                        )
                    )
                    next_roster = high_actions[:, 1:, 0].astype(
                        np.int64, copy=True
                    )
                    if current_roster is not None:
                        changes = next_roster != current_roster
                        event_rows.append(
                            {
                                "episode": episode_index,
                                "step": episode_steps,
                                "pre_roster": current_roster[0].tolist(),
                                "post_roster": next_roster[0].tolist(),
                                "changes": changes[0].astype(int).tolist(),
                                "discordant": int(
                                    bool(changes[0, 0]) != bool(changes[0, 1])
                                ),
                                "full_sync_set": int(bool(changes[0].all())),
                            }
                        )
                    current_roster = next_roster
                    team_skill = np.expand_dims(high_actions[:, 0], 1).repeat(
                        runner.num_agents, 1
                    )
                    individual_skill = high_actions[:, 1:]

                runner.l_trainer.prep_rollout()
                low_actions, next_rnn_states = runner.l_policy.act(
                    np.concatenate(obs),
                    np.concatenate(team_skill),
                    np.concatenate(individual_skill),
                    np.concatenate(rnn_states),
                    np.concatenate(masks),
                    np.concatenate(available_actions),
                    deterministic=True,
                )
                low_actions = np.array(
                    np.split(
                        low_actions.detach().cpu().numpy(),
                        all_args.n_eval_rollout_threads,
                    )
                )
                rnn_states = np.array(
                    np.split(
                        next_rnn_states.detach().cpu().numpy(),
                        all_args.n_eval_rollout_threads,
                    )
                )
                obs, share_obs, _, dones, infos, available_actions = eval_envs.step(
                    low_actions
                )
                episode_steps += 1
                if bool(np.all(dones, axis=1)[0]):
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
                    episode_steps_rows.append(episode_steps)
                    break
        return {
            "evaluator": "r42_deterministic_alice_bob_with_native_roster",
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
            "average_episode_steps": float(np.mean(episode_steps_rows)),
            "episode_wins": wins,
            "episode_key0": key0_rows,
            "episode_key1": key1_rows,
            "episode_steps": episode_steps_rows,
            "renewal_events": event_rows,
        }
    finally:
        eval_envs.close()


def run_arm(
    source_archive: Path,
    source_root: Path,
    source_checkpoint: Path,
    output_root: Path,
    seed: int,
    mode: str,
    preflight_only: bool = False,
) -> dict[str, Any]:
    identity_before = source_identity(source_archive, source_root)
    official_entry = source_root / "hmasd" / "scripts" / "train" / "train_alice_and_bob.py"
    if not identity_before["archive_present"] or not official_entry.is_file():
        raise RuntimeError("fresh official HMASD source tree is unavailable")
    if not source_checkpoint.is_file():
        raise RuntimeError(f"R41B checkpoint is missing: {source_checkpoint}")
    sys.path.insert(0, str(source_root))
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
        raise RuntimeError("R42 requires CUDA")
    official_base_runner.SummaryWriter = ExternalSummaryWriter
    device = torch.device("cuda:0")
    torch.set_num_threads(8)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    parser = get_config()
    all_args = parse_args(r42_argument_vector(seed, preflight_only), parser)
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
    config = {
        "all_args": all_args,
        "envs": envs,
        "eval_envs": None,
        "num_agents": 2,
        "device": device,
        "run_dir": official_run_dir,
    }
    runner = AliceBobRunner(config)
    environment_contract = {
        "agents": len(envs.action_space),
        "obs": int(envs.observation_space[0][0]),
        "state": int(envs.share_observation_space[0][0]),
        "actions": int(envs.action_space[0].n),
        "horizon": int(all_args.episode_length),
    }
    checkpoint_source = load_source_checkpoint(
        torch, runner, source_checkpoint
    )
    parity = install_native_roster_residual(runner, mode)
    residual_module = runner.h_policy.transformer.r42_incumbent_roster_residual
    initial_residual = {
        name: value.detach().cpu().clone()
        for name, value in residual_module.state_dict().items()
    }
    initial_residual_zero_output = bool(
        torch.count_nonzero(residual_module.output.weight).item() == 0
        and torch.count_nonzero(residual_module.output.bias).item() == 0
    )
    if preflight_only:
        envs.close()
        result = {
            "experiment_id": EXPERIMENT_ID,
            "state": "preflight_complete",
            "mode": mode,
            "seed": seed,
            "source_checkpoint": checkpoint_source,
            "parity": parity,
            "initial_residual_zero_output": initial_residual_zero_output,
        }
        atomic_json(output_root / "preflight_result.json", result)
        return result

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
                "mode": mode,
                "outer_updates": telemetry["outer_updates"],
                "expected_outer_updates": OUTER_UPDATES,
                "actual_env_steps": telemetry["actual_env_steps"],
                "expected_env_steps": ENV_STEPS,
                "optimizer_steps": {
                    name: stats["steps"] for name, stats in optimizer_stats.items()
                },
                "updated_unix": time.time(),
            },
        )
        return train_info

    runner.train = instrumented_train
    started = time.time()
    try:
        runner.run()
    finally:
        envs.close()

    checkpoint_path = output_root / "checkpoints" / "exact_final.pt"
    final_checkpoint = save_r42_checkpoint(
        torch,
        runner,
        checkpoint_path,
        seed,
        mode,
        int(telemetry["outer_updates"]),
    )
    drift = residual_parameter_drift(runner, initial_residual)
    load_r42_checkpoint(torch, runner, checkpoint_path)
    final_eval = exact_r42_evaluation(
        torch, runner, make_eval_env, all_args, seed
    )
    result = {
        "experiment_id": EXPERIMENT_ID,
        "state": "completed",
        "mode": mode,
        "seed": seed,
        "source": {
            "before": identity_before,
            "after": source_identity(source_archive, source_root),
            "fresh_extract": True,
            "checkpoint": checkpoint_source,
        },
        "runtime": runtime_manifest(torch),
        "official_arguments": selected_arguments(all_args),
        "official_argument_vector": r42_argument_vector(seed),
        "environment": environment_contract,
        "algorithm_boundary": {
            "source_algorithm": "official_hmasd_native_k50_continuation",
            "mode": mode,
            "high_reward": "environment_reward_only",
            "low_reward": "0.0*environment+0.1*q_D+0.2*q_d",
            "extra_shaping": False,
            "extra_intrinsic": False,
            "task_fields_in_residual": False,
            "age_in_residual": False,
            "new_duration_action": False,
            "independent_keep_head": False,
            "team_z_resampled_each_native_check": True,
            "incumbent_roster_teacher_forced": True,
            "fresh_initialization": False,
        },
        "parity": parity,
        "initial_residual_zero_output": initial_residual_zero_output,
        "residual_drift": drift,
        "telemetry": telemetry,
        "training_renewal": summarize_event_ledger(runner.r42_event_ledger),
        "checkpoint": final_checkpoint,
        "evaluation": final_eval,
        "elapsed_seconds": time.time() - started,
    }
    atomic_json(output_root / "seed_result.json", result)
    atomic_json(
        progress_path,
        {
            "state": "completed",
            "mode": mode,
            "outer_updates": telemetry["outer_updates"],
            "expected_outer_updates": OUTER_UPDATES,
            "actual_env_steps": telemetry["actual_env_steps"],
            "expected_env_steps": ENV_STEPS,
            "win_rate": final_eval["win_rate"],
            "updated_unix": time.time(),
        },
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-archive", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--source-checkpoint", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--mode", choices=R42_MODES, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "seed_status.json"
    atomic_json(
        status_path,
        {"state": "running", "mode": args.mode, "updated_unix": time.time()},
    )
    try:
        result = run_arm(
            Path(args.source_archive).resolve(),
            Path(args.source_root).resolve(),
            Path(args.source_checkpoint).resolve(),
            output_root,
            args.seed,
            args.mode,
            args.preflight_only,
        )
        terminal = {
            "state": "completed",
            "mode": args.mode,
            "preflight_only": args.preflight_only,
            "updated_unix": time.time(),
        }
        if "evaluation" in result:
            terminal["win_rate"] = result["evaluation"]["win_rate"]
        atomic_json(status_path, terminal)
    except Exception as exc:
        atomic_json(
            status_path,
            {
                "state": "failed",
                "mode": args.mode,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "updated_unix": time.time(),
            },
        )
        raise


if __name__ == "__main__":
    main()
