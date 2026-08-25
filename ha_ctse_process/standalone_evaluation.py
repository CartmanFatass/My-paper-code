"""Standalone evaluation helpers for the HA-CTSE process core."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch

from ha_ctse_process.env_factory import normalize_scenario
from ha_ctse_process.checkpoint_io import (
    capture_global_rng_state,
    restore_global_rng_state,
)
from ha_ctse_process.metrics_io import append_csv
from ha_ctse_process.plotting import EVAL_FIELDS, extract_uav_metrics, save_eval_plots
from ha_ctse_process.standalone_agent import StandaloneProcessAgent
from ha_ctse_process.standalone_segments import SegmentManager
from ha_ctse_process.standalone_cli import create_env
from ha_ctse_process.standalone_metrics import emit
from ha_ctse_process.topology_viz import capture_topology_frame, save_topology_artifacts


def numeric_metric(value) -> float | None:
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        return None
    return float(np.mean(arr))

def extract_eval_metrics(info: dict[str, Any]) -> dict[str, float]:
    metrics = extract_uav_metrics(info)
    if "coverage_ratio" in metrics:
        metrics["coverage"] = metrics["coverage_ratio"]
    if "qos_satisfaction_ratio" in metrics:
        metrics["qos"] = metrics["qos_satisfaction_ratio"]
    if "system_throughput_mbps" in metrics:
        metrics["throughput"] = metrics["system_throughput_mbps"]
    if "battery_min_ratio" in metrics:
        metrics["battery_min"] = metrics["battery_min_ratio"]
    if "energy_failure_uav_count" in metrics:
        metrics["energy_failures"] = metrics["energy_failure_uav_count"]
    return metrics


def format_optional_metric(metrics: dict[str, float], *names: str) -> str:
    """Format the first observed finite metric without inventing a zero."""

    for name in names:
        value = metrics.get(name)
        if value is not None and np.isfinite(float(value)):
            return f"{float(value):.6f}"
    return "NA"

def evaluate(
    agent: StandaloneProcessAgent,
    config,
    args: argparse.Namespace,
    episodes: int,
    total_steps: int,
) -> dict[str, float]:
    """Run evaluation without advancing any process-global RNG stream."""

    rng_state = capture_global_rng_state()
    try:
        return _evaluate_impl(agent, config, args, episodes, total_steps)
    finally:
        restore_global_rng_state(rng_state)


def _evaluate_impl(
    agent: StandaloneProcessAgent,
    config,
    args: argparse.Namespace,
    episodes: int,
    total_steps: int,
) -> dict[str, float]:
    """Run standalone eval without changing training segments."""

    lifecycle_backup = agent.standalone_lifecycle_state_dict()
    env = create_env(config, config.scenario, int(args.seed) + 100000, rank=0, scale_mode="eval")
    deterministic_eval = str(getattr(args, "eval_action_mode", "deterministic")) == "deterministic"
    active_backup = agent.active_skills.copy()
    active_duration_indices_backup = agent.active_duration_indices.copy()
    duration_backup = agent.duration_remaining.copy()
    age_backup = agent.skill_age.copy()
    has_active_backup = agent.has_active_skill.copy()
    team_code_backup = agent.active_team_codes.copy()
    team_intent_remaining_backup = getattr(agent, "team_intent_remaining", None)
    if team_intent_remaining_backup is not None:
        team_intent_remaining_backup = team_intent_remaining_backup.copy()
    team_intent_age_backup = getattr(agent, "team_intent_age", None)
    if team_intent_age_backup is not None:
        team_intent_age_backup = team_intent_age_backup.copy()
    low_actor_hxs_backup = agent.low_actor_hxs.copy()
    low_critic_hxs_backup = agent.low_critic_hxs.copy()
    episode_steps_backup = agent.episode_steps.copy()
    episode_ids_backup = agent.episode_ids.copy()
    steps_to_check_backup = agent.steps_to_check.copy()
    high_check_buffer_backup = agent.high_check_buffer
    if bool(getattr(agent, "r30_enabled", False)):
        agent.high_check_buffer = type(high_check_buffer_backup)(
            agent.num_envs, agent.n_agents, agent.gamma
        )
    last_low_context_backup = list(agent._last_low_context)
    segments_backup = agent.segments
    agent.segments = SegmentManager(agent.num_envs, agent.n_agents)

    rewards: list[float] = []
    lengths: list[int] = []
    metric_values: dict[str, list[float]] = {}
    eval_records: list[dict[str, Any]] = []
    save_topology = bool(getattr(args, "save_topology", False))
    topology_interval = max(1, int(getattr(args, "topology_interval", 25)))
    topology_episodes = max(0, int(getattr(args, "topology_episodes", 1)))
    topology_max_frames = max(1, int(getattr(args, "topology_max_frames", 160)))
    is_alice_bob = normalize_scenario(config.scenario) == "alice_bob_asymmetric_cycles"
    eval_seed_blocks = tuple(
        int(token.strip())
        for token in str(getattr(args, "eval_seed_blocks", "")).split(",")
        if token.strip()
    )
    episodes_per_seed = int(getattr(args, "eval_episodes_per_seed", 0))
    if eval_seed_blocks:
        if episodes_per_seed <= 0:
            raise ValueError("eval_seed_blocks requires eval_episodes_per_seed > 0")
        expected_episodes = len(eval_seed_blocks) * episodes_per_seed
        if int(episodes) != expected_episodes:
            raise ValueError(
                f"fixed eval seed blocks require {expected_episodes} episodes, got {episodes}"
            )
    checkpoint_identity = str(
        getattr(args, "eval_checkpoint_name", "")
        or f"in_training_step_{int(total_steps)}"
    )
    base_eval_seed = int(args.seed) + 100000

    def alice_bob_joint_cell(state_value) -> tuple[int, int, int, int] | None:
        if state_value is None:
            return None
        positions = np.asarray(state_value, dtype=np.float32).reshape(-1)[:4]
        if positions.size != 4 or not np.all(np.isfinite(positions)):
            return None
        return tuple(
            np.clip(np.floor(positions * 5.0), 0, 4)
            .astype(np.int64)
            .tolist()
        )

    try:
        for episode_idx in range(max(int(episodes), 1)):
            if eval_seed_blocks:
                block_index = episode_idx // episodes_per_seed
                within_block = episode_idx % episodes_per_seed
                block_seed = eval_seed_blocks[block_index]
                reset_seed = block_seed * 1000 + within_block
                if within_block == 0:
                    random.seed(block_seed)
                    np.random.seed(block_seed)
                    torch.manual_seed(block_seed)
                    if torch.cuda.is_available():
                        torch.cuda.manual_seed_all(block_seed)
                evaluation_seed = block_seed
            else:
                evaluation_seed = base_eval_seed
                reset_seed = evaluation_seed + episode_idx
            obs, info = env.reset(seed=reset_seed)
            state = info.get("state")
            agent.reset_env_state(0)
            episode_reward = 0.0
            episode_length = 0
            last_info = info
            backhaul_connected_steps: list[float] = []
            backhaul_observed_for_all_steps = True
            throughput_when_backhaul_connected_steps: list[float] = []
            coverage_eq1_steps: list[float] = []
            coverage_positive_steps: list[float] = []
            joint_position_cells: set[tuple[int, int, int, int]] = set()
            initial_joint_cell = alice_bob_joint_cell(state) if is_alice_bob else None
            if initial_joint_cell is not None:
                joint_position_cells.add(initial_joint_cell)
            zero_throughput_steps: list[float] = []
            throughput_gt5_steps: list[float] = []
            capture_topology = save_topology and episode_idx < topology_episodes
            topology_frames = []
            if capture_topology:
                topology_frames.append(
                    capture_topology_frame(
                        env,
                        info,
                        agent,
                        episode=episode_idx,
                        step=episode_length,
                        reward=episode_reward,
                        metrics={},
                    )
                )
            while True:
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=episode_length,
                    k=int(args.skill_interval),
                    env_id=0,
                    deterministic=deterministic_eval,
                )
                actions, _, _ = agent.act_low(obs, env_id=0, deterministic=deterministic_eval, state=state)
                obs, reward, terminated, truncated, last_info = env.step(actions)
                state = last_info.get("next_state", state)
                joint_cell = alice_bob_joint_cell(state) if is_alice_bob else None
                if joint_cell is not None:
                    joint_position_cells.add(joint_cell)
                episode_reward += float(reward)
                episode_length += 1
                step_metrics = extract_eval_metrics(last_info)
                backhaul_flag = numeric_metric(
                    step_metrics.get("backhaul_connected_flag")
                )
                if backhaul_flag is None:
                    backhaul_observed_for_all_steps = False
                else:
                    backhaul_connected_steps.append(backhaul_flag)
                step_throughput = step_metrics.get("throughput")
                step_coverage = step_metrics.get("coverage", step_metrics.get("coverage_ratio"))
                if step_coverage is not None:
                    coverage_value = float(step_coverage)
                    coverage_eq1_steps.append(1.0 if coverage_value >= 0.999 else 0.0)
                    coverage_positive_steps.append(1.0 if coverage_value > 1e-6 else 0.0)
                if step_throughput is not None:
                    throughput_value = float(step_throughput)
                    zero_throughput_steps.append(1.0 if throughput_value <= 1e-6 else 0.0)
                    throughput_gt5_steps.append(1.0 if throughput_value > 5.0 else 0.0)
                if (
                    backhaul_flag is not None
                    and backhaul_flag >= 0.5
                    and step_throughput is not None
                ):
                    throughput_when_backhaul_connected_steps.append(float(step_throughput))
                done = bool(terminated or truncated)
                hit_step_cap = int(args.eval_max_steps) > 0 and episode_length >= int(args.eval_max_steps)
                agent.record_environment_step(
                    0,
                    reward=float(reward),
                    next_obs=obs,
                    next_state=state,
                    done=bool(done or hit_step_cap),
                )
                if capture_topology and len(topology_frames) < topology_max_frames:
                    should_capture = (
                        episode_length % topology_interval == 0
                        or done
                        or hit_step_cap
                    )
                    if should_capture:
                        topology_frames.append(
                            capture_topology_frame(
                                env,
                                last_info,
                                agent,
                                episode=episode_idx,
                                step=episode_length,
                                reward=episode_reward,
                                metrics=extract_eval_metrics(last_info),
                            )
                        )
                if done or hit_step_cap:
                    break
            rewards.append(episode_reward)
            lengths.append(episode_length)
            episode_metrics = extract_eval_metrics(last_info)
            if is_alice_bob:
                episode_metrics["alice_bob_joint_position_coverage_ratio"] = float(
                    len(joint_position_cells) / 625.0
                )
                targets_completed = numeric_metric(
                    episode_metrics.get("alice_bob_targets_completed")
                )
                if targets_completed is not None:
                    episode_metrics["alice_bob_zero_cycle_episode_flag"] = float(
                        targets_completed <= 0.0
                    )
            if backhaul_observed_for_all_steps and backhaul_connected_steps:
                episode_metrics["backhaul_connected_step_fraction"] = float(np.mean(backhaul_connected_steps))
            if coverage_eq1_steps:
                episode_metrics["coverage_eq1_step_fraction"] = float(np.mean(coverage_eq1_steps))
                episode_metrics["coverage_has_eq1_step_flag"] = float(np.max(coverage_eq1_steps))
                episode_metrics["coverage_episode_all_eq1_flag"] = float(np.min(coverage_eq1_steps))
            if coverage_positive_steps:
                episode_metrics["coverage_positive_step_fraction"] = float(np.mean(coverage_positive_steps))
            final_coverage = episode_metrics.get("coverage", episode_metrics.get("coverage_ratio"))
            if final_coverage is not None:
                episode_metrics["coverage_final_eq1_flag"] = 1.0 if float(final_coverage) >= 0.999 else 0.0
            if zero_throughput_steps:
                episode_metrics["zero_throughput_step_fraction"] = float(np.mean(zero_throughput_steps))
                episode_metrics["zero_throughput_episode_flag"] = float(np.min(zero_throughput_steps))
            if throughput_gt5_steps:
                episode_metrics["throughput_gt5_step_fraction"] = float(np.mean(throughput_gt5_steps))
                episode_metrics["throughput_gt5_episode_flag"] = float(np.max(throughput_gt5_steps))
            if (
                backhaul_observed_for_all_steps
                and throughput_when_backhaul_connected_steps
            ):
                episode_metrics["throughput_when_backhaul_connected_mbps"] = float(
                    np.mean(throughput_when_backhaul_connected_steps)
                )
            else:
                episode_metrics.pop("throughput_when_backhaul_connected_mbps", None)
            eval_record = {
                "checkpoint": checkpoint_identity,
                "total_steps": int(total_steps),
                "eval_step": int(total_steps),
                "run_seed": int(args.seed),
                "seed": int(evaluation_seed),
                "episode": episode_idx,
                "reset_seed": reset_seed,
                "action_mode_code": 0.0 if deterministic_eval else 1.0,
                "reward": episode_reward,
                "length": episode_length,
                "terminated_flag": float(bool(terminated)),
                "truncated_flag": float(bool(truncated)),
                **episode_metrics,
            }
            eval_records.append(eval_record)
            if getattr(args, "log_dir", None):
                append_csv(
                    Path(args.log_dir) / "metrics" / "eval_episodes.csv",
                    eval_record,
                    EVAL_FIELDS,
                )
            for key, value in episode_metrics.items():
                if value is None or not np.isfinite(float(value)):
                    continue
                metric_values.setdefault(key, []).append(value)
            if capture_topology and topology_frames:
                try:
                    artifacts = save_topology_artifacts(
                        topology_frames,
                        args.log_dir,
                        total_steps=total_steps,
                        episode=episode_idx,
                        checkpoint_name=checkpoint_identity,
                    )
                    if artifacts:
                        artifact_text = " ".join(f"{key}={value}" for key, value in artifacts.items())
                        emit(
                            args,
                            "standalone_topology "
                            f"total_steps={int(total_steps)} episode={episode_idx} frames={len(topology_frames)} "
                            f"{artifact_text}",
                        )
                except Exception as exc:
                    emit(
                        args,
                        "standalone_topology_failed "
                        f"total_steps={int(total_steps)} episode={episode_idx} error={exc}",
                    )
    finally:
        env.close()
        agent.load_standalone_lifecycle_state_dict(lifecycle_backup)
        agent.segments = segments_backup
        agent.active_skills = active_backup
        agent.active_duration_indices = active_duration_indices_backup
        agent.duration_remaining = duration_backup
        agent.skill_age = age_backup
        agent.has_active_skill = has_active_backup
        agent.active_team_codes = team_code_backup
        if team_intent_remaining_backup is not None:
            agent.team_intent_remaining = team_intent_remaining_backup
        if team_intent_age_backup is not None:
            agent.team_intent_age = team_intent_age_backup
        agent.low_actor_hxs = low_actor_hxs_backup
        agent.low_critic_hxs = low_critic_hxs_backup
        agent.episode_steps = episode_steps_backup
        agent.episode_ids = episode_ids_backup
        agent.steps_to_check = steps_to_check_backup
        agent.high_check_buffer = high_check_buffer_backup
        agent._last_low_context = last_low_context_backup

    metrics = {
        "reward_mean": float(np.mean(rewards)) if rewards else 0.0,
        "reward_std": float(np.std(rewards)) if rewards else 0.0,
        "length_mean": float(np.mean(lengths)) if lengths else 0.0,
        "action_mode_code": 0.0 if deterministic_eval else 1.0,
    }
    completed_episode_count = len(rewards)
    for key, values in metric_values.items():
        # A cross-episode summary is only defined when every episode observed
        # the field; otherwise retain absence rather than silently changing the
        # denominator from metric to metric.
        if completed_episode_count > 0 and len(values) == completed_episode_count:
            metrics[key] = float(np.mean(values))
    if "coverage_has_eq1_step_flag" in metrics:
        metrics["coverage_eq1_episode_fraction"] = float(metrics["coverage_has_eq1_step_flag"])
    if "coverage_final_eq1_flag" in metrics:
        metrics["coverage_final_eq1_episode_fraction"] = float(metrics["coverage_final_eq1_flag"])
    if "zero_throughput_episode_flag" in metrics:
        metrics["zero_throughput_episode_fraction"] = float(metrics["zero_throughput_episode_flag"])
    if "throughput_gt5_episode_flag" in metrics:
        metrics["throughput_gt5_episode_fraction"] = float(metrics["throughput_gt5_episode_flag"])
    if eval_records and getattr(args, "log_dir", None):
        save_eval_plots(
            args.log_dir,
            window=max(1, int(getattr(args, "eval_episodes", 1))),
        )

    emit(
        args,
        "standalone_eval "
        f"total_steps={int(total_steps)} episodes={max(int(episodes), 1)} "
        f"action_mode={getattr(args, 'eval_action_mode', 'deterministic')} "
        f"reward_mean={metrics['reward_mean']:.6f} "
        f"reward_std={metrics['reward_std']:.6f} "
        f"length_mean={metrics['length_mean']:.1f} "
        f"coverage={format_optional_metric(metrics, 'coverage')} "
        f"qos={format_optional_metric(metrics, 'qos')} "
        f"throughput={format_optional_metric(metrics, 'throughput')} "
        f"backhaul_connected_frac={format_optional_metric(metrics, 'backhaul_connected_step_fraction', 'backhaul_connected_flag')} "
        f"throughput_when_backhaul_connected={format_optional_metric(metrics, 'throughput_when_backhaul_connected_mbps')} "
        f"battery_min={format_optional_metric(metrics, 'battery_min')} "
        f"coverage_eq1_step_frac={format_optional_metric(metrics, 'coverage_eq1_step_fraction')} "
        f"coverage_eq1_ep_frac={format_optional_metric(metrics, 'coverage_eq1_episode_fraction')} "
        f"zero_throughput_ep_frac={format_optional_metric(metrics, 'zero_throughput_episode_fraction')} "
        f"throughput_gt5_step_frac={format_optional_metric(metrics, 'throughput_gt5_step_fraction')}"
    )
    return metrics
