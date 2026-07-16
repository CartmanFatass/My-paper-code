"""Run one R44 frozen-source native-renewal arm from the R41B checkpoint."""

from __future__ import annotations

import argparse
import copy
import math
import os
import random
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np

from r43_native_renewal import R43_TREATMENT, evaluate_r43_factors, sample_r43_actions
from r44_frozen_source_nrc import (
    R44_CONTROL,
    R44_MODES,
    R44_TREATMENT,
    factor_parameter_drift,
    factor_state_snapshot,
    install_frozen_source_nrc,
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
from run_r43_native_renewal_arm import (
    load_source_checkpoint,
    merge_replay_maximum,
    replay_audit,
)


EXPERIMENT_ID = "EXP-20260716-r44-fsnrc-k50"
R44_CHECKPOINT_SCHEMA = "r44_frozen_source_nrc_checkpoint_v1"
ROLLOUT_ENVS = 16
ENV_STEPS = 320_000
OUTER_UPDATES = 200
EXPECTED_FACTOR_STEPS = 3_000
EVAL_EPISODES = 100


def r44_argument_vector(seed: int, outer_updates: int = OUTER_UPDATES) -> list[str]:
    arguments = official_argument_vector(seed, "r41a")

    def replace(flag: str, value: str) -> None:
        index = arguments.index(flag)
        arguments[index + 1] = value

    replace("--num_env_steps", str(outer_updates * 100 * ROLLOUT_ENVS))
    replace("--n_rollout_threads", str(ROLLOUT_ENVS))
    arguments.extend(
        [
            "--n_training_threads",
            "8",
            "--save_interval",
            "1000",
            "--log_interval",
            "10",
            "--use_eval",
        ]
    )
    return arguments


def _snapshot_tree(value: Any) -> Any:
    try:
        import torch

        if torch.is_tensor(value):
            return value.detach().cpu().clone()
    except ImportError:
        pass
    if isinstance(value, np.ndarray):
        return value.copy()
    if isinstance(value, dict):
        return {key: _snapshot_tree(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_snapshot_tree(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_snapshot_tree(item) for item in value)
    return copy.deepcopy(value)


def source_state_snapshot(runner: Any) -> dict[str, Any]:
    value_norms: dict[str, Any] = {}
    if runner.h_trainer.value_normalizer is not None:
        value_norms["high"] = _snapshot_tree(
            runner.h_trainer.value_normalizer.state_dict()
        )
    if runner.l_trainer.value_normalizer is not None:
        value_norms["low"] = _snapshot_tree(
            runner.l_trainer.value_normalizer.state_dict()
        )
    return {
        "modules": {
            "high_policy": _snapshot_tree(runner.h_policy.transformer.state_dict()),
            "low_actor": _snapshot_tree(runner.l_policy.actor.state_dict()),
            "low_critic": _snapshot_tree(runner.l_policy.critic.state_dict()),
            "team_discriminator": _snapshot_tree(
                runner.discri.team_discri.state_dict()
            ),
            "individual_discriminator": _snapshot_tree(
                runner.discri.indi_discri.state_dict()
            ),
        },
        "optimizers": {
            "high": _snapshot_tree(runner.h_policy.optimizer.state_dict()),
            "low_actor": _snapshot_tree(
                runner.l_policy.actor_optimizer.state_dict()
            ),
            "low_critic": _snapshot_tree(
                runner.l_policy.critic_optimizer.state_dict()
            ),
            "team_discriminator": _snapshot_tree(
                runner.discri.team_discri_optimizer.state_dict()
            ),
            "individual_discriminator": _snapshot_tree(
                runner.discri.indi_discri_optimizer.state_dict()
            ),
        },
        "value_norms": value_norms,
    }


def _tree_drift(before: Any, after: Any) -> dict[str, Any]:
    import torch

    maximum = 0.0
    unequal = 0
    compared = 0

    def visit(left: Any, right: Any) -> None:
        nonlocal maximum, unequal, compared
        if torch.is_tensor(left):
            compared += 1
            if not torch.is_tensor(right) or tuple(left.shape) != tuple(right.shape):
                unequal += 1
                maximum = math.inf
                return
            right_cpu = right.detach().cpu()
            if left.is_floating_point() or left.is_complex():
                delta = (right_cpu - left).abs()
                value = float(delta.max().item()) if delta.numel() else 0.0
                maximum = max(maximum, value)
                unequal += int(value != 0.0)
            else:
                equal = bool(torch.equal(left, right_cpu))
                unequal += int(not equal)
                if not equal:
                    maximum = math.inf
            return
        if isinstance(left, np.ndarray):
            compared += 1
            if not isinstance(right, np.ndarray) or left.shape != right.shape:
                unequal += 1
                maximum = math.inf
                return
            if np.issubdtype(left.dtype, np.number):
                delta = np.abs(right.astype(np.float64) - left.astype(np.float64))
                value = float(delta.max()) if delta.size else 0.0
                maximum = max(maximum, value)
                unequal += int(value != 0.0)
            else:
                equal = bool(np.array_equal(left, right))
                unequal += int(not equal)
                if not equal:
                    maximum = math.inf
            return
        if isinstance(left, dict):
            if not isinstance(right, dict) or set(left) != set(right):
                unequal += 1
                maximum = math.inf
                return
            for key in left:
                visit(left[key], right[key])
            return
        if isinstance(left, (list, tuple)):
            if not isinstance(right, type(left)) or len(left) != len(right):
                unequal += 1
                maximum = math.inf
                return
            for left_item, right_item in zip(left, right):
                visit(left_item, right_item)
            return
        compared += 1
        equal = left == right
        unequal += int(not equal)
        if not equal:
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                maximum = max(maximum, abs(float(right) - float(left)))
            else:
                maximum = math.inf

    visit(before, after)
    return {
        "max_abs": maximum,
        "unequal_leaves": unequal,
        "compared_leaves": compared,
        "exact": unequal == 0,
    }


def source_state_drift(runner: Any, initial: dict[str, Any]) -> dict[str, Any]:
    high_state = runner.h_policy.transformer.state_dict()
    initial_high = initial["modules"]["high_policy"]
    current = source_state_snapshot(runner)
    current["modules"]["high_policy"] = {
        name: high_state[name] for name in initial_high
    }
    sections: dict[str, Any] = {}
    global_max = 0.0
    unequal = 0
    for category in ("modules", "optimizers", "value_norms"):
        sections[category] = {}
        for name, before in initial[category].items():
            drift = _tree_drift(before, current[category][name])
            sections[category][name] = drift
            global_max = max(global_max, float(drift["max_abs"]))
            unequal += int(drift["unequal_leaves"])
    return {
        **sections,
        "global_max_abs": global_max,
        "global_unequal_leaves": unequal,
        "exact": unequal == 0,
    }


def save_r44_checkpoint(
    torch_module: Any,
    runner: Any,
    path: Path,
    seed: int,
    mode: str,
    outer_updates: int,
) -> dict[str, Any]:
    payload = checkpoint_payload(torch_module, runner, seed, outer_updates)
    payload["schema"] = R44_CHECKPOINT_SCHEMA
    payload["factor_optimizer"] = runner.r44_factor_optimizer.state_dict()
    payload["r44"] = {
        "mode": mode,
        "controller_clock": "source_global_k50_reset_censored",
        "current_team": runner._r43_current_team.copy(),
        "current_roster": runner._r43_current_roster.copy(),
        "age": runner._r43_age.copy(),
        "initialized": runner._r43_initialized.copy(),
        "clock_ledger": _snapshot_tree(runner.r43_clock_ledger),
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
            "source_optimizers": sorted(payload["optimizers"]),
            "factor_optimizer": True,
            "value_norms": sorted(payload["value_norms"]),
            "controller_carry": True,
        },
    }


def load_r44_checkpoint(torch_module: Any, runner: Any, path: Path) -> None:
    try:
        payload = torch_module.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        payload = torch_module.load(path, map_location="cpu")
    if payload.get("schema") != R44_CHECKPOINT_SCHEMA:
        raise RuntimeError("unexpected R44 checkpoint schema")
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
        runner.h_trainer.value_normalizer.load_state_dict(payload["value_norms"]["high"])
    if "low" in payload["value_norms"]:
        runner.l_trainer.value_normalizer.load_state_dict(payload["value_norms"]["low"])
    runner.r44_factor_optimizer.load_state_dict(payload["factor_optimizer"])
    carry = payload["r44"]
    runner._r43_current_team = np.asarray(carry["current_team"]).copy()
    runner._r43_current_roster = np.asarray(carry["current_roster"]).copy()
    runner._r43_age = np.asarray(carry["age"], dtype=np.float32).copy()
    runner._r43_initialized = np.asarray(carry["initialized"], dtype=bool).copy()
    runner.r43_clock_ledger = copy.deepcopy(carry["clock_ledger"])
    restore_rng(torch_module, payload["rng"])


def conditional_ratio_audit(torch_module: Any, runner: Any) -> float:
    rng = capture_rng(torch_module)
    maximum = 0.0
    try:
        runner.h_trainer.prep_rollout()
        with torch_module.no_grad():
            for step in range(runner.h_buffer.episode_length):
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
                mask = torch_module.as_tensor(
                    runner.h_buffer.r43_skill_valid[step],
                    dtype=evaluated["skill_logp"].dtype,
                    device=evaluated["skill_logp"].device,
                )
                old = torch_module.as_tensor(
                    runner.h_buffer.r43_skill_old_logp[step],
                    dtype=evaluated["skill_logp"].dtype,
                    device=evaluated["skill_logp"].device,
                )
                if bool((mask > 0).any()):
                    ratio = torch_module.exp(evaluated["skill_logp"] - old)
                    maximum = max(
                        maximum,
                        float((ratio[mask > 0] - 1.0).abs().max().item()),
                    )
        return maximum
    finally:
        restore_rng(torch_module, rng)


def exact_r44_evaluation(
    torch_module: Any,
    runner: Any,
    make_eval_env: Any,
    all_args: Any,
    seed: int,
    mode: str,
    episodes: int,
) -> dict[str, Any]:
    eval_envs = make_eval_env(all_args)
    try:
        wins: list[int] = []
        key0_rows: list[int] = []
        key1_rows: list[int] = []
        episode_steps_rows: list[int] = []
        high_traces: list[list[dict[str, Any]]] = []
        low_traces: list[list[list[int]]] = []
        event_rows: list[dict[str, Any]] = []
        obs, share_obs, available_actions = eval_envs.reset()
        for episode_index in range(episodes):
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
            episode_steps = 0
            episode_high: list[dict[str, Any]] = []
            episode_low: list[list[int]] = []
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
                    high_actions = sampled["actions"].detach().cpu().numpy()
                    current_roster = sampled["post_roster"].detach().cpu().numpy()
                    current_age = sampled["post_age"].detach().cpu().numpy()
                    renew_tokens = sampled["renew_token"].detach().cpu().numpy()[0]
                    team_skill = np.expand_dims(high_actions[:, 0], 1).repeat(
                        runner.num_agents, 1
                    )
                    individual_skill = high_actions[:, 1:]
                    episode_high.append(
                        {
                            "step": episode_steps,
                            "team": int(high_actions[0, 0, 0]),
                            "roster": current_roster[0].astype(int).tolist(),
                        }
                    )
                    if not structural:
                        episode_event = {
                            "episode": episode_index,
                            "eligible": True,
                            "step": episode_steps,
                            "renew_token": renew_tokens.astype(int).tolist(),
                            "discordant": int(
                                bool(renew_tokens[0] == 1)
                                != bool(renew_tokens[1] == 1)
                            ),
                            "full_sync_renew": int(bool((renew_tokens == 1).all())),
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
                episode_low.append(low_actions[0, :, 0].astype(int).tolist())
                obs, share_obs, _, dones, infos, available_actions = eval_envs.step(
                    low_actions
                )
                current_age += 1.0
                episode_steps += 1
                if bool(np.all(dones, axis=1)[0]):
                    info = infos[0][0]
                    wins.append(int(bool(info["battle_won"])))
                    key0_rows.append(int(bool(info["key0"])))
                    key1_rows.append(int(bool(info["key1"])))
                    episode_steps_rows.append(episode_steps)
                    high_traces.append(episode_high)
                    low_traces.append(episode_low)
                    event_rows.append(episode_event)
                    break
        return {
            "evaluator": "r44_deterministic_alice_bob_exact_trace",
            "mode": mode,
            "episodes": episodes,
            "eval_threads": all_args.n_eval_rollout_threads,
            "high_deterministic": True,
            "low_deterministic": True,
            "reset_stream": {
                "construction_seed": seed * 50_000,
                "rank_stride": 10_000,
                "episode_indices": list(range(episodes)),
            },
            "win_rate": float(np.mean(wins)),
            "key0_rate": float(np.mean(key0_rows)),
            "key1_rate": float(np.mean(key1_rows)),
            "average_episode_steps": float(np.mean(episode_steps_rows)),
            "episode_wins": wins,
            "episode_key0": key0_rows,
            "episode_key1": key1_rows,
            "episode_steps": episode_steps_rows,
            "high_action_traces": high_traces,
            "low_action_traces": low_traces,
            "renewal_events": event_rows,
        }
    finally:
        eval_envs.close()


def _evaluate_without_rng_effect(
    torch_module: Any,
    runner: Any,
    make_eval_env: Any,
    all_args: Any,
    seed: int,
    mode: str,
    episodes: int,
) -> dict[str, Any]:
    rng = capture_rng(torch_module)
    try:
        return exact_r44_evaluation(
            torch_module, runner, make_eval_env, all_args, seed, mode, episodes
        )
    finally:
        restore_rng(torch_module, rng)


def run_arm(
    source_archive: Path,
    source_root: Path,
    source_checkpoint: Path,
    output_root: Path,
    seed: int,
    mode: str,
    outer_updates: int = OUTER_UPDATES,
    eval_episodes: int = EVAL_EPISODES,
    install_only: bool = False,
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
        raise RuntimeError("R44 requires CUDA")
    official_base_runner.SummaryWriter = ExternalSummaryWriter
    device = torch.device("cuda:0")
    torch.set_num_threads(8)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    all_args = parse_args(r44_argument_vector(seed, outer_updates), get_config())
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
    initial_source = source_state_snapshot(runner)
    installation = install_frozen_source_nrc(runner, mode)
    initial_factors = factor_state_snapshot(runner)
    zero_eval = _evaluate_without_rng_effect(
        torch, runner, make_eval_env, all_args, seed, mode, eval_episodes
    )
    if install_only:
        envs.close()
        result = {
            "experiment_id": EXPERIMENT_ID,
            "state": "install_only_complete",
            "mode": mode,
            "seed": seed,
            "source_checkpoint": checkpoint_source,
            "installation": installation,
            "zero_step_evaluation": zero_eval,
        }
        atomic_json(output_root / "install_only_result.json", result)
        return result

    source_optimizers = {
        "high": runner.h_policy.optimizer,
        "low_actor": runner.l_policy.actor_optimizer,
        "low_critic": runner.l_policy.critic_optimizer,
        "team_discriminator": runner.discri.team_discri_optimizer,
        "individual_discriminator": runner.discri.indi_discri_optimizer,
    }
    source_optimizer_stats = {
        name: install_optimizer_counter(torch, optimizer, name)
        for name, optimizer in source_optimizers.items()
    }
    factor_optimizer_stats = install_optimizer_counter(
        torch, runner.r44_factor_optimizer, "factor"
    )
    telemetry: dict[str, Any] = {
        "outer_updates": 0,
        "actual_env_steps": 0,
        "replay": None,
        "conditional_skill_ratio_max_deviation": 0.0,
        "high_replay_updates_checked": 0,
        "low_replay_updates_checked": 0,
        "source_optimizers": source_optimizer_stats,
        "factor_optimizer": factor_optimizer_stats,
    }
    progress_path = output_root / "progress.json"
    factor_train = runner.train

    def instrumented_train() -> dict[str, Any]:
        audit = replay_audit(
            torch,
            runner,
            R43_TREATMENT,
            audit_low=telemetry["outer_updates"] == 0,
        )
        telemetry["replay"] = merge_replay_maximum(telemetry["replay"], audit)
        telemetry["conditional_skill_ratio_max_deviation"] = max(
            telemetry["conditional_skill_ratio_max_deviation"],
            conditional_ratio_audit(torch, runner),
        )
        telemetry["high_replay_updates_checked"] += 1
        if telemetry["outer_updates"] == 0:
            telemetry["low_replay_updates_checked"] += 1
        train_info = factor_train()
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
                "expected_outer_updates": outer_updates,
                "actual_env_steps": telemetry["actual_env_steps"],
                "expected_env_steps": outer_updates * 100 * ROLLOUT_ENVS,
                "env_check_rows": runner.r43_clock_ledger["env_check_rows"],
                "auto_resets": runner.r43_clock_ledger["auto_resets"],
                "source_optimizer_steps": {
                    name: stats["steps"]
                    for name, stats in source_optimizer_stats.items()
                },
                "factor_optimizer_steps": factor_optimizer_stats["steps"],
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
    final_checkpoint = save_r44_checkpoint(
        torch, runner, checkpoint_path, seed, mode, telemetry["outer_updates"]
    )
    frozen_drift = source_state_drift(runner, initial_source)
    factor_drift = factor_parameter_drift(runner, initial_factors)
    gradient_stats = copy.deepcopy(runner.r44_factor_gradient_stats)
    load_r44_checkpoint(torch, runner, checkpoint_path)
    final_eval = _evaluate_without_rng_effect(
        torch, runner, make_eval_env, all_args, seed, mode, eval_episodes
    )
    result = {
        "experiment_id": EXPERIMENT_ID,
        "state": "completed",
        "scope": "formal" if outer_updates == OUTER_UPDATES else "focused_smoke",
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
        "official_argument_vector": r44_argument_vector(seed, outer_updates),
        "environment": environment_contract,
        "algorithm_boundary": {
            "source_algorithm": "frozen_r41b_hmasd_skill_system",
            "mode": mode,
            "controller_clock": "source_global_k50_reset_censored",
            "renewal_return": "next_50_external_reward_steps_reset_censored",
            "conditional_skill": "frozen_source_non_incumbent_distribution",
            "low_executor": "frozen_r41b_low_actor",
            "source_optimizer_updates": False,
            "factor_optimizer_modules": ["renewal_actor", "renewal_critic"],
            "renewal_actor_enabled": mode == R44_TREATMENT,
            "renewal_entropy": False,
            "extra_shaping": False,
            "extra_intrinsic": False,
            "task_fields_in_controller": False,
            "discriminators_read_only": True,
            "auto_reset_high_action": False,
            "assignment_spell_crosses_reset": True,
            "execution_fragment_censored_at_reset": True,
            "fresh_initialization": False,
        },
        "installation": installation,
        "source_frozen_drift": frozen_drift,
        "factor_drift": factor_drift,
        "factor_gradient_stats": gradient_stats,
        "telemetry": telemetry,
        "training_clock": runner.r43_clock_ledger,
        "checkpoint": final_checkpoint,
        "zero_step_evaluation": zero_eval,
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
            "expected_outer_updates": outer_updates,
            "actual_env_steps": telemetry["actual_env_steps"],
            "expected_env_steps": outer_updates * 100 * ROLLOUT_ENVS,
            "env_check_rows": runner.r43_clock_ledger["env_check_rows"],
            "factor_optimizer_steps": factor_optimizer_stats["steps"],
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
    parser.add_argument("--mode", choices=R44_MODES, required=True)
    parser.add_argument("--outer-updates", type=int, default=OUTER_UPDATES)
    parser.add_argument("--eval-episodes", type=int, default=EVAL_EPISODES)
    parser.add_argument("--install-only", action="store_true")
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
            args.outer_updates,
            args.eval_episodes,
            args.install_only,
        )
        terminal = {
            "state": "completed",
            "mode": args.mode,
            "install_only": args.install_only,
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
