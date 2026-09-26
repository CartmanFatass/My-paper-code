"""Original-objective S7 panels with independently rescorable trajectories."""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import torch

from hmasd.agent import HMASDAgent
from ..b01.native import (
    METRIC_FIELDS, _sync_agent, _terminal_kind, initialization_fingerprint,
    make_env, preserved_rng, seed_everything, sha256_file,
)

TRACE_FIELDS = (*METRIC_FIELDS, "return_constraint_cost_raw", "return_penalty_coefficient",
                "cutoff_event_penalty", "depletion_event_penalty", "graph_potential_delta", "scenario7_reward")


def metric_row(reward, info):
    row = np.asarray([float(info[name]) for name in TRACE_FIELDS], dtype=np.float64)
    if not np.isfinite(row).all() or not np.isfinite(reward):
        raise FloatingPointError("non-finite S7 reward or metric")
    if float(info["return_penalty_coefficient"]) != 2.0:
        raise ValueError("B04 requires the original environment return coefficient 2")
    cost = float(info["return_constraint_cost"])
    if not 0.0 <= cost <= 1.0:
        raise ValueError("B04 return constraint cost must be in [0,1]")
    expected = (float(info["qos_satisfaction_ratio"]) - 2.0 * cost
                - float(info["cutoff_event_penalty"]) - float(info["depletion_event_penalty"])
                + float(info["graph_potential_delta"]))
    if not np.isclose(reward, expected, rtol=1e-7, atol=1e-7):
        raise ValueError("native scalar reward is not the original S7 reward")
    if not np.isclose(reward, float(info["scenario7_reward"]), rtol=1e-7, atol=1e-7):
        raise ValueError("adapter reward units differ from S7 reward units")
    return row


def evaluate(agent, config, seeds, device, *, policy_seed, log_dir: Path,
             trace_path: Path):
    seeds = tuple(int(seed) for seed in seeds)
    if not seeds or config.lambda_return != 2.0:
        raise ValueError("empty panel or modified evaluation objective")
    worlds, arrays = [], {"metric_fields": np.asarray(TRACE_FIELDS)}
    original_sha = initialization_fingerprint(agent)
    with preserved_rng():
        seed_everything(policy_seed, device)
        eval_config = copy.deepcopy(config)
        eval_config.num_envs = 1
        eval_config.calculate_and_set_buffer_sizes()
        evaluator = HMASDAgent(eval_config, log_dir=str(log_dir), device=device)
        _sync_agent(agent, evaluator)
        evaluator.train(False)
        for index, seed in enumerate(seeds):
            env = make_env(eval_config, seed)
            rewards, metrics, commands, ends = [], [], [], []
            try:
                evaluator.reset_env_state(0)
                obs, info = env.reset(seed=seed)
                state = np.asarray(info["state"], dtype=np.float32)
                previous_done = np.ones(1, dtype=bool)
                for step in range(int(config.episode_length)):
                    actions, _, _ = evaluator.step(
                        state[None], obs[None], np.asarray([step]), previous_done,
                        deterministic=True, return_step_data=True, build_infos=False)
                    next_obs, reward, terminated, truncated, info = env.step(actions[0])
                    rewards.append(float(reward))
                    metrics.append(metric_row(reward, info["reward_info"]))
                    commands.append(actions[0].copy())
                    ends.append((bool(terminated), bool(truncated)))
                    obs = np.asarray(next_obs, dtype=np.float32)
                    state = np.asarray(info["next_state"], dtype=np.float32)
                    previous_done[:] = terminated or truncated
                    if previous_done[0]:
                        break
                if not previous_done[0]:
                    raise RuntimeError("evaluation did not reach native termination/truncation")
            finally:
                env.close()
            rewards, metrics = np.asarray(rewards, dtype=np.float64), np.asarray(metrics)
            length = len(rewards)
            row = {"seed": seed, "raw_native_J": float(rewards.sum()),
                   "native_J_per_step": float(rewards.mean()), "actual_length": length,
                   "terminal_type": _terminal_kind(terminated, truncated),
                   "episode_minimum_battery_ratio": float(metrics[:, TRACE_FIELDS.index("battery_min_ratio")].min())}
            for column, field in enumerate(TRACE_FIELDS):
                row[f"{field}_sum"] = float(metrics[:, column].sum())
                row[f"{field}_per_step"] = float(metrics[:, column].mean())
            worlds.append(row)
            arrays.update({f"episode_{index}_seed": np.asarray(seed),
                           f"episode_{index}_native_reward": rewards,
                           f"episode_{index}_metrics": metrics,
                           f"episode_{index}_actions": np.asarray(commands, dtype=np.float32),
                           f"episode_{index}_ends": np.asarray(ends, dtype=bool)})
    if initialization_fingerprint(agent) != original_sha:
        raise RuntimeError("evaluation changed the training policy")
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(trace_path, **arrays)
    fields = [key for key, value in worlds[0].items()
              if isinstance(value, (int, float)) and key not in {"seed", "actual_length"}]
    aggregate = {f"mean_{key}": float(np.mean([row[key] for row in worlds])) for key in fields}
    aggregate["primary_native_J_mean"] = aggregate["mean_raw_native_J"]
    aggregate["minimum_episode_battery_ratio"] = min(row["episode_minimum_battery_ratio"] for row in worlds)
    aggregate["p10_episode_minimum_battery_ratio"] = float(np.quantile(
        [row["episode_minimum_battery_ratio"] for row in worlds], .1))
    return {"worlds": worlds, "aggregate": aggregate,
            "actual_transitions": sum(row["actual_length"] for row in worlds),
            "new_optimizer_updates": 0, "evaluation_return_coefficient": 2.0,
            "policy_sha256": original_sha, "trace_sha256": sha256_file(trace_path)}
