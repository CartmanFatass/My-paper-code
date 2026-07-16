"""Run one reset-censored R43-NRC continuation arm from the R41B checkpoint."""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np

from r43_native_renewal import (
    KEEP,
    RENEW,
    R43_FIXED,
    R43_MODES,
    R43_TREATMENT,
    evaluate_r43_factors,
    install_native_renewal,
    module_parameter_drift,
    module_state_snapshot,
    sample_r43_actions,
    summarize_renewal_ledger,
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


EXPERIMENT_ID = "EXP-20260716-r43-nrc-k50"
SOURCE_CHECKPOINT_SCHEMA = "r41_official_hmasd_complete_checkpoint_v1"
R43_CHECKPOINT_SCHEMA = "r43_native_renewal_checkpoint_v1"
ROLLOUT_ENVS = 16
ENV_STEPS = 320_000
OUTER_UPDATES = 200
EXPECTED_OPTIMIZER_STEPS = 3_000
EVAL_EPISODES = 100


def r43_argument_vector(seed: int, preflight_only: bool = False) -> list[str]:
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
            f"R43 requires {SOURCE_CHECKPOINT_SCHEMA}, got {payload.get('schema')}"
        )
    runner.h_policy.transformer.load_state_dict(payload["modules"]["high_policy"])
    runner.l_policy.actor.load_state_dict(payload["modules"]["low_actor"])
    runner.l_policy.critic.load_state_dict(payload["modules"]["low_critic"])
    runner.discri.team_discri.load_state_dict(payload["modules"]["team_discriminator"])
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


def save_r43_checkpoint(
    torch_module: Any,
    runner: Any,
    path: Path,
    seed: int,
    mode: str,
    outer_updates: int,
) -> dict[str, Any]:
    payload = checkpoint_payload(torch_module, runner, seed, outer_updates)
    payload["schema"] = R43_CHECKPOINT_SCHEMA
    payload["r43"] = {
        "mode": mode,
        "controller_clock": "source_global_k50_reset_censored",
        "current_team": None
        if runner._r43_current_team is None
        else runner._r43_current_team.copy(),
        "current_roster": None
        if runner._r43_current_roster is None
        else runner._r43_current_roster.copy(),
        "age": None
        if getattr(runner, "_r43_age", None) is None
        else runner._r43_age.copy(),
        "initialized": None
        if getattr(runner, "_r43_initialized", None) is None
        else runner._r43_initialized.copy(),
        "fixed_initialized": bool(
            getattr(runner, "_r43_fixed_initialized", False)
        ),
        "clock_ledger": runner.r43_clock_ledger,
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
            "controller_carry": True,
        },
    }


def load_r43_checkpoint(torch_module: Any, runner: Any, path: Path) -> None:
    try:
        payload = torch_module.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        payload = torch_module.load(path, map_location="cpu")
    if payload.get("schema") != R43_CHECKPOINT_SCHEMA:
        raise RuntimeError("unexpected R43 checkpoint schema")
    runner.h_policy.transformer.load_state_dict(payload["modules"]["high_policy"])
    runner.l_policy.actor.load_state_dict(payload["modules"]["low_actor"])
    runner.l_policy.critic.load_state_dict(payload["modules"]["low_critic"])
    runner.discri.team_discri.load_state_dict(payload["modules"]["team_discriminator"])
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
    carry = payload["r43"]
    if carry.get("current_team") is not None:
        runner._r43_current_team = np.asarray(carry["current_team"]).copy()
    if carry.get("current_roster") is not None:
        runner._r43_current_roster = np.asarray(carry["current_roster"]).copy()
    if carry.get("age") is not None:
        runner._r43_age = np.asarray(carry["age"], dtype=np.float32).copy()
    if carry.get("initialized") is not None:
        runner._r43_initialized = np.asarray(carry["initialized"], dtype=bool).copy()
    if hasattr(runner, "_r43_fixed_initialized"):
        runner._r43_fixed_initialized = bool(carry.get("fixed_initialized", True))
    restore_rng(torch_module, payload["rng"])


def replay_audit(
    torch_module: Any, runner: Any, mode: str, *, audit_low: bool
) -> dict[str, float]:
    rng = capture_rng(torch_module)
    try:
        runner.h_trainer.prep_rollout()
        high_error = 0.0
        factor_error = 0.0
        value_error = 0.0
        prefix_error = 0.0
        with torch_module.no_grad():
            for step in range(runner.h_buffer.episode_length):
                if mode == R43_FIXED:
                    replayed_values, replayed_logp, _ = runner.h_policy.evaluate_actions(
                        np.concatenate(runner.h_buffer.share_obs[step]),
                        np.concatenate(runner.h_buffer.obs[step]),
                        np.concatenate(runner.h_buffer.actions[step]),
                    )
                    old_logp = torch_module.as_tensor(
                        np.concatenate(runner.h_buffer.action_log_probs[step]),
                        dtype=replayed_logp.dtype,
                        device=replayed_logp.device,
                    )
                    old_values = torch_module.as_tensor(
                        np.concatenate(runner.h_buffer.value_preds[step]),
                        dtype=replayed_values.dtype,
                        device=replayed_values.device,
                    )
                    high_error = max(
                        high_error,
                        float((replayed_logp - old_logp).abs().max().item()),
                    )
                    value_error = max(
                        value_error,
                        float((replayed_values - old_values).abs().max().item()),
                    )
                else:
                    evaluated = evaluate_r43_factors(
                        runner.h_policy,
                        np.concatenate(runner.h_buffer.share_obs[step]),
                        np.concatenate(runner.h_buffer.obs[step]),
                        runner.h_buffer.actions[step],
                        runner.h_buffer.r43_pre_roster[step],
                        runner.h_buffer.r43_pre_age[step],
                        runner.h_buffer.r43_active_mask[step],
                        runner.h_buffer.r43_renew_token[step],
                        runner.h_buffer.r43_renew_valid[step],
                        runner.h_buffer.r43_skill_valid[step],
                        runner.h_buffer.r43_working_prefix[step],
                    )
                    old_combined = torch_module.as_tensor(
                        runner.h_buffer.action_log_probs[step, :, :, 0],
                        dtype=evaluated["combined_logp"].dtype,
                        device=evaluated["combined_logp"].device,
                    )
                    high_error = max(
                        high_error,
                        float(
                            (evaluated["combined_logp"] - old_combined)
                            .abs()
                            .max()
                            .item()
                        ),
                    )
                    renew_old = torch_module.as_tensor(
                        runner.h_buffer.r43_renew_old_logp[step],
                        dtype=evaluated["renew_logp"].dtype,
                        device=evaluated["renew_logp"].device,
                    )
                    renew_mask = torch_module.as_tensor(
                        runner.h_buffer.r43_renew_valid[step],
                        dtype=evaluated["renew_logp"].dtype,
                        device=evaluated["renew_logp"].device,
                    )
                    skill_old = torch_module.as_tensor(
                        runner.h_buffer.r43_skill_old_logp[step],
                        dtype=evaluated["skill_logp"].dtype,
                        device=evaluated["skill_logp"].device,
                    )
                    skill_mask = torch_module.as_tensor(
                        runner.h_buffer.r43_skill_valid[step],
                        dtype=evaluated["skill_logp"].dtype,
                        device=evaluated["skill_logp"].device,
                    )
                    factor_error = max(
                        factor_error,
                        float(
                            ((evaluated["renew_logp"] - renew_old) * renew_mask)
                            .abs()
                            .max()
                            .item()
                        ),
                        float(
                            ((evaluated["skill_logp"] - skill_old) * skill_mask)
                            .abs()
                            .max()
                            .item()
                        ),
                    )
                    old_values = torch_module.as_tensor(
                        runner.h_buffer.value_preds[step],
                        dtype=evaluated["source_values"].dtype,
                        device=evaluated["source_values"].device,
                    )
                    value_error = max(
                        value_error,
                        float(
                            (evaluated["source_values"] - old_values)
                            .abs()
                            .max()
                            .item()
                        ),
                    )
                    prefix_error = max(
                        prefix_error, float(evaluated["prefix_mismatch"].item())
                    )

        low_error = 0.0
        if audit_low:
            runner.l_trainer.prep_rollout()
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
            "factor_max_abs_logp_error": factor_error,
            "high_max_abs_value_error": value_error,
            "prefix_mismatch_count": prefix_error,
            "low_max_abs_logp_error": low_error,
            "global_max_abs_logp_error": max(high_error, factor_error, low_error),
        }
    finally:
        restore_rng(torch_module, rng)


def merge_replay_maximum(
    aggregate: dict[str, float] | None, current: dict[str, float]
) -> dict[str, float]:
    if aggregate is None:
        return dict(current)
    return {name: max(float(aggregate.get(name, 0.0)), float(value)) for name, value in current.items()}


def exact_r43_evaluation(
    torch_module: Any,
    runner: Any,
    make_eval_env: Any,
    all_args: Any,
    seed: int,
    mode: str,
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
            current_roster = np.full((1, runner.num_agents), -1, dtype=np.int64)
            current_age = np.zeros((1, runner.num_agents), dtype=np.float32)
            current_team = None
            episode_steps = 0
            episode_event = {
                "episode": episode_index,
                "eligible": False,
                "step": None,
                "renew_token": [0, 0],
                "discordant": 0,
                "full_sync_renew": 0,
                "pre_roster": None,
                "post_roster": None,
            }
            while True:
                if episode_steps % runner.skill_interval == 0:
                    runner.h_trainer.prep_rollout()
                    structural = episode_steps == 0
                    pre_roster = current_roster.copy()
                    if mode == R43_TREATMENT:
                        sampled = sample_r43_actions(
                            runner.h_policy,
                            np.concatenate(share_obs),
                            np.concatenate(obs),
                            current_roster,
                            current_age,
                            np.ones_like(current_age, dtype=np.float32),
                            structural=structural,
                            deterministic=True,
                        )
                        high_actions = sampled["actions"].cpu().numpy()
                        current_roster = sampled["post_roster"].cpu().numpy()
                        current_age = sampled["post_age"].cpu().numpy()
                        renew_tokens = sampled["renew_token"].cpu().numpy()[0]
                    else:
                        high_actions_flat = runner.h_policy.act(
                            np.concatenate(share_obs),
                            np.concatenate(obs),
                            deterministic=True,
                        )
                        high_actions = np.array(
                            np.split(
                                high_actions_flat.detach().cpu().numpy(),
                                all_args.n_eval_rollout_threads,
                            )
                        )
                        current_roster = high_actions[:, 1:, 0].astype(
                            np.int64, copy=True
                        )
                        current_age[:] = 0.0
                        renew_tokens = np.full(runner.num_agents, RENEW, dtype=np.int64)
                    current_team = high_actions[:, 0]
                    team_skill = np.expand_dims(current_team, 1).repeat(
                        runner.num_agents, 1
                    )
                    individual_skill = high_actions[:, 1:]
                    if not structural:
                        episode_event = {
                            "episode": episode_index,
                            "eligible": True,
                            "step": episode_steps,
                            "renew_token": renew_tokens.astype(int).tolist(),
                            "discordant": int(
                                bool(renew_tokens[0] == RENEW)
                                != bool(renew_tokens[1] == RENEW)
                            ),
                            "full_sync_renew": int(
                                bool((renew_tokens == RENEW).all())
                            ),
                            "pre_roster": pre_roster[0].astype(int).tolist(),
                            "post_roster": current_roster[0].astype(int).tolist(),
                        }

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
                current_age += 1.0
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
                    event_rows.append(episode_event)
                    break
        return {
            "evaluator": "r43_deterministic_alice_bob_reset_aligned_episode",
            "mode": mode,
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
        raise RuntimeError("R43 requires CUDA")
    official_base_runner.SummaryWriter = ExternalSummaryWriter
    device = torch.device("cuda:0")
    torch.set_num_threads(8)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    parser = get_config()
    all_args = parse_args(r43_argument_vector(seed, preflight_only), parser)
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
    checkpoint_source = load_source_checkpoint(torch, runner, source_checkpoint)
    installation = install_native_renewal(runner, mode)
    initial_modules = module_state_snapshot(runner)
    if preflight_only:
        envs.close()
        result = {
            "experiment_id": EXPERIMENT_ID,
            "state": "preflight_complete",
            "mode": mode,
            "seed": seed,
            "source_checkpoint": checkpoint_source,
            "installation": installation,
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
        "high_replay_updates_checked": 0,
        "low_replay_updates_checked": 0,
        "optimizers": optimizer_stats,
    }
    progress_path = output_root / "progress.json"
    original_train = runner.train

    def instrumented_train() -> dict[str, Any]:
        audit = replay_audit(
            torch,
            runner,
            mode,
            audit_low=telemetry["outer_updates"] == 0,
        )
        telemetry["replay"] = merge_replay_maximum(telemetry["replay"], audit)
        telemetry["high_replay_updates_checked"] += 1
        if telemetry["outer_updates"] == 0:
            telemetry["low_replay_updates_checked"] += 1
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
                "env_check_rows": runner.r43_clock_ledger["env_check_rows"],
                "auto_resets": runner.r43_clock_ledger["auto_resets"],
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
    final_checkpoint = save_r43_checkpoint(
        torch,
        runner,
        checkpoint_path,
        seed,
        mode,
        int(telemetry["outer_updates"]),
    )
    drift = module_parameter_drift(runner, initial_modules)
    gradient_stats = getattr(runner.h_trainer, "r43_gradient_stats", None)
    load_r43_checkpoint(torch, runner, checkpoint_path)
    final_eval = exact_r43_evaluation(
        torch, runner, make_eval_env, all_args, seed, mode
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
        "official_argument_vector": r43_argument_vector(seed),
        "environment": environment_contract,
        "algorithm_boundary": {
            "source_algorithm": "official_hmasd_native_k50_continuation",
            "mode": mode,
            "controller_clock": "source_global_k50_reset_censored",
            "high_reward": "environment_reward_only",
            "low_reward": "0.0*environment+0.1*q_D+0.2*q_d",
            "extra_shaping": False,
            "extra_intrinsic": False,
            "task_fields_in_controller": False,
            "team_z_source_path_unchanged": True,
            "auto_reset_high_action": False,
            "assignment_spell_crosses_reset": True,
            "execution_fragment_censored_at_reset": True,
            "incumbent_and_age_cross_update": mode == R43_TREATMENT,
            "conditional_same_label_masked": mode == R43_TREATMENT,
            "single_combined_high_optimizer": True,
            "fresh_initialization": False,
        },
        "installation": installation,
        "module_drift": drift,
        "gradient_stats": gradient_stats,
        "telemetry": telemetry,
        "training_clock": summarize_renewal_ledger(runner.r43_clock_ledger),
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
            "env_check_rows": runner.r43_clock_ledger["env_check_rows"],
            "auto_resets": runner.r43_clock_ledger["auto_resets"],
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
    parser.add_argument("--mode", choices=R43_MODES, required=True)
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
