"""Standalone training entrypoint for the HA-CTSE process-core algorithm.

This file is deliberately not a wrapper around ``train_multiproc_config_1.py``
or ``hmasd.agent``.  It owns the new algorithm's train/eval/checkpoint flow and
only reuses the shared environment/config infrastructure.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch

try:
    from torch.utils.tensorboard import SummaryWriter
except ModuleNotFoundError:
    SummaryWriter = None

from ha_ctse_process.env_factory import EnvSpec, make_env, normalize_scenario
from ha_ctse_process.collectors import SubprocEnvCollector, SyncEnvCollector
from ha_ctse_process.plotting import (
    EVAL_FIELDS,
    UPDATE_FIELDS,
    append_csv,
    extract_uav_metrics,
    save_eval_plots,
    save_update_plots,
)
from ha_ctse_process.standalone_agent import (
    Rollout,
    SegmentManager,
    StandaloneProcessAgent,
)
from ha_ctse_process.topology_viz import capture_topology_frame, save_topology_artifacts


ALGORITHM_MANIFEST_FIELDS = (
    "algorithm",
    "policy_update_mode",
    "allow_off_policy_policy_updates",
    "process_segment_replay_enabled",
    "n_z",
    "skill_lifetime_candidates",
    "process_segment_mode",
    "allow_early_duration_termination",
    "opt_compact_dim",
    "opt_num_prototypes",
    "opt_use_sparsemax",
    "opt_cd_coef",
    "opt_cmi_coef",
    "team_bridge_type",
    "team_code_dim",
    "num_team_codes",
    "process_encoder_embedding_dim",
    "lr_process_encoder",
    "process_contrast_coef",
    "process_outcome_coef",
    "process_reward_coef",
    "process_reward_contrast_coef",
    "process_reward_outcome_coef",
    "process_reward_clip",
    "normalize_process_outcomes",
    "use_process_reward_for_discoverer",
    "use_process_posterior_mi",
    "process_posterior_condition_on_team",
    "process_prior_coef",
    "edit_penalty_alpha",
    "switch_penalty_beta",
)

TRAINING_MANIFEST_FIELDS = (
    "gamma",
    "clip_epsilon",
    "high_entropy_coef",
    "low_entropy_coef",
    "lr",
    "lr_actor",
    "lr_critic",
    "lr_high",
    "batch_size",
    "minibatch_size",
    "ppo_epochs",
    "rollout_length",
    "total_timesteps",
    "eval_interval",
)

MODEL_MANIFEST_FIELDS = (
    "hidden_size",
    "embedding_dim",
    "n_heads",
    "n_encoder_layers",
    "n_decoder_layers",
    "gru_hidden_size",
    "state_dim",
    "obs_dim",
    "action_dim",
    "n_agents",
    "n_uavs",
)

PHYSICAL_MANIFEST_FIELDS = (
    "scenario",
    "experiment_preset",
    "area_size",
    "max_steps",
    "episode_length",
    "n_users",
    "n_uavs",
    "n_agents",
    "n_ground_bs",
    "max_connections",
    "coverage_radius",
    "communication_range",
    "uav_communication_range",
    "ground_bs_communication_range",
    "bandwidth",
    "carrier_frequency",
    "tx_power",
    "noise_power",
    "routing_protocol",
    "max_hops",
    "backhaul_margin_target_mbps",
    "backhaul_guard_min_capacity_mbps",
    "enable_backhaul_action_guard",
    "battery_enabled",
    "battery_capacity_wh",
    "initial_battery_ratio",
    "low_battery_threshold",
    "critical_battery_threshold",
    "depleted_battery_threshold",
    "n_charging_stations",
    "max_energy_charging_stations",
    "charging_radius_m",
    "scenario7_reward_model",
    "scenario7_reward_variant",
    "scenario7_experiment_arm",
    "return_cost_cap",
    "lambda_return",
    "cutoff_event_penalty",
    "depletion_event_penalty",
)


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def pick_attrs(obj: Any, names: tuple[str, ...]) -> dict[str, Any]:
    result = {}
    for name in names:
        if hasattr(obj, name):
            result[name] = jsonable(getattr(obj, name))
    return result


def export_run_manifest(
    args: argparse.Namespace,
    config,
    env: Any | None = None,
    agent: StandaloneProcessAgent | None = None,
    total_steps: int = 0,
    update_idx: int = 0,
    mode: str = "train",
) -> None:
    """Write the experiment parameters that explain the scalar plots."""

    metadata_dir = Path(args.log_dir) / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    env_state = {}
    if env is not None and hasattr(env, "get_current_state"):
        try:
            env_state = env.get_current_state() or {}
        except Exception:
            env_state = {}
    manifest = {
        "mode": mode,
        "total_steps": int(total_steps),
        "update_idx": int(update_idx),
        "args": jsonable(vars(args)),
        "algorithm_config": pick_attrs(config, ALGORITHM_MANIFEST_FIELDS),
        "training_config": pick_attrs(config, TRAINING_MANIFEST_FIELDS),
        "model_config": pick_attrs(config, MODEL_MANIFEST_FIELDS),
        "physical_env_config": pick_attrs(config, PHYSICAL_MANIFEST_FIELDS),
        "env_runtime_spec": {},
        "agent_runtime_spec": {},
    }
    if env is not None:
        for name in ("obs_dim", "state_dim", "action_dim", "n_uavs", "n_agents", "n_users"):
            if hasattr(env, name):
                manifest["env_runtime_spec"][name] = jsonable(getattr(env, name))
    if env_state:
        for name in (
            "area_size",
            "max_steps",
            "n_charging_stations",
            "charging_radius_m",
            "battery_enabled",
            "energy_stage",
        ):
            if name in env_state:
                manifest["env_runtime_spec"][name] = jsonable(env_state[name])
    if agent is not None:
        manifest["agent_runtime_spec"] = {
            "obs_dim": int(agent.obs_dim),
            "action_dim": int(agent.action_dim),
            "n_agents": int(agent.n_agents),
            "n_skills": int(agent.n_skills),
            "duration_candidates": jsonable(agent.duration_candidates),
            "action_space_type": str(agent.action_space_type),
            "device": str(agent.device),
        }
    with (metadata_dir / "run_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)


def emit(args: argparse.Namespace, message: str) -> None:
    print(message)
    log_dir = Path(getattr(args, "log_dir", "logs/ha_ctse_process_standalone"))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "standalone_train.log").open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


def load_config(config_name: str, preset: str | None):
    module = importlib.import_module(config_name)
    return module.Config(preset=preset) if preset else module.Config()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train or evaluate the standalone HA-CTSE process-core algorithm."
    )
    parser.add_argument("--mode", choices=("train", "eval"), default="train")
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--preset", default="")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--log_dir", default="logs/ha_ctse_process_standalone")
    parser.add_argument("--dry_run_env_steps", type=int, default=0)
    parser.add_argument("--total_timesteps", type=int, default=320000)
    parser.add_argument("--rollout_length", type=int, default=500)
    parser.add_argument("--skill_interval", type=int, default=10)
    parser.add_argument("--num_envs", type=int, default=1)
    parser.add_argument("--n_agents", type=int, default=0)
    parser.add_argument("--collector_backend", choices=("sync", "subproc"), default="sync")
    parser.add_argument("--collector_start_method", choices=("spawn", "forkserver", "fork"), default="spawn")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--save_interval", type=int, default=10)
    parser.add_argument("--checkpoint_keep_last", type=int, default=3)
    parser.add_argument("--resume_from", default="")
    parser.add_argument("--eval_interval", type=int, default=0)
    parser.add_argument("--eval_episodes", type=int, default=3)
    parser.add_argument("--eval_max_steps", type=int, default=0)
    parser.add_argument("--save_topology", action="store_true")
    parser.add_argument("--topology_interval", type=int, default=25)
    parser.add_argument("--topology_episodes", type=int, default=1)
    parser.add_argument("--topology_max_frames", type=int, default=160)
    parser.add_argument("--plot_interval", type=int, default=1)
    parser.add_argument("--skill_lifetime_candidates", default="")
    parser.add_argument("--team_bridge_type", choices=("none", "deterministic", "stochastic"), default="")
    parser.add_argument("--opt_compact_dim", type=int, default=0)
    parser.add_argument("--opt_num_prototypes", type=int, default=0)
    parser.add_argument("--process_reward_coef", type=float, default=None)
    parser.add_argument("--process_reward_clip", type=float, default=None)
    parser.add_argument("--process_contrast_coef", type=float, default=None)
    parser.add_argument("--process_outcome_coef", type=float, default=None)
    parser.add_argument("--process_reward_contrast_coef", type=float, default=None)
    parser.add_argument("--process_reward_outcome_coef", type=float, default=None)
    parser.add_argument("--process_prior_coef", type=float, default=None)
    parser.add_argument("--high_entropy_coef", type=float, default=None)
    parser.add_argument("--low_entropy_coef", type=float, default=None)
    parser.add_argument("--edit_penalty_alpha", type=float, default=None)
    parser.add_argument("--switch_penalty_beta", type=float, default=None)
    parser.add_argument("--opt_cd_coef", type=float, default=None)
    parser.add_argument("--opt_cmi_coef", type=float, default=None)
    parser.add_argument("--disable_process_reward", action="store_true")
    parser.add_argument("--disable_process_posterior_mi", action="store_true")
    return parser.parse_args()


def parse_int_tuple(text: str) -> tuple[int, ...]:
    values = []
    for chunk in str(text or "").replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        values.append(int(chunk))
    return tuple(values)


def apply_standalone_overrides(config, args: argparse.Namespace) -> None:
    if int(args.n_agents) > 0:
        config.n_agents = int(args.n_agents)
        config.n_uavs = int(args.n_agents)
        config.max_observed_uavs = max(int(args.n_agents), int(getattr(config, "max_observed_uavs", args.n_agents)))
    candidates = parse_int_tuple(args.skill_lifetime_candidates)
    if candidates:
        config.skill_lifetime_candidates = candidates
    if args.team_bridge_type:
        config.team_bridge_type = args.team_bridge_type
    if int(args.opt_compact_dim) > 0:
        config.opt_compact_dim = int(args.opt_compact_dim)
    if int(args.opt_num_prototypes) > 0:
        config.opt_num_prototypes = int(args.opt_num_prototypes)
    optional_scalars = (
        "process_reward_coef",
        "process_reward_clip",
        "process_contrast_coef",
        "process_outcome_coef",
        "process_reward_contrast_coef",
        "process_reward_outcome_coef",
        "process_prior_coef",
        "high_entropy_coef",
        "low_entropy_coef",
        "edit_penalty_alpha",
        "switch_penalty_beta",
        "opt_cd_coef",
        "opt_cmi_coef",
    )
    for name in optional_scalars:
        value = getattr(args, name)
        if value is not None:
            setattr(config, name, value)
    if args.disable_process_reward:
        config.use_process_reward_for_discoverer = False
    if args.disable_process_posterior_mi:
        config.use_process_posterior_mi = False


def resolve_device(requested: str) -> str:
    if requested == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return requested


def create_env(config, scenario: str, seed: int, rank: int, scale_mode: str):
    return make_env(
        config,
        EnvSpec(
            scenario=normalize_scenario(scenario),
            seed=int(seed),
            rank=int(rank),
            scale_mode=scale_mode,
        ),
    )()


def create_envs(config, args: argparse.Namespace, scale_mode: str, num_envs: int):
    return [
        create_env(
            config,
            scenario=config.scenario,
            seed=int(args.seed),
            rank=env_id,
            scale_mode=scale_mode,
        )
        for env_id in range(max(int(num_envs), 1))
    ]


def create_collector(config, args: argparse.Namespace, scale_mode: str, num_envs: int):
    if args.collector_backend == "subproc":
        return SubprocEnvCollector(
            config=config,
            scenario=config.scenario,
            seed=int(args.seed),
            num_envs=max(int(num_envs), 1),
            scale_mode=scale_mode,
            start_method=args.collector_start_method,
        )
    return SyncEnvCollector(create_envs(config, args, scale_mode=scale_mode, num_envs=num_envs))


def action_space_details(env) -> tuple[str, Any, Any]:
    action_dtype = getattr(env.action_space, "dtype", np.int64)
    action_space_type = "continuous" if np.issubdtype(action_dtype, np.floating) else "discrete"
    action_low = env.action_space.low[0] if action_space_type == "continuous" else None
    action_high = env.action_space.high[0] if action_space_type == "continuous" else None
    return action_space_type, action_low, action_high


def create_agent(
    config,
    args: argparse.Namespace,
    env,
    num_envs: int,
    state_dim: int | None = None,
) -> StandaloneProcessAgent:
    action_space_type, action_low, action_high = action_space_details(env)
    return StandaloneProcessAgent(
        obs_dim=int(env.obs_dim),
        action_dim=int(env.action_dim),
        n_agents=int(env.n_uavs),
        config=config,
        device=resolve_device(args.device),
        action_space_type=action_space_type,
        action_low=action_low,
        action_high=action_high,
        num_envs=max(int(num_envs), 1),
        state_dim=state_dim or getattr(env, "state_dim", None),
    )


def checkpoint_payload(
    agent: StandaloneProcessAgent,
    args: argparse.Namespace,
    config,
    total_steps: int,
    update_idx: int,
) -> dict[str, Any]:
    return {
        "high": agent.high.state_dict(),
        "compact": agent.compact.state_dict(),
        "bridge": agent.bridge.state_dict(),
        "low": agent.low.state_dict(),
        "process": agent.process.state_dict(),
        "process_posterior": agent.process_posterior.state_dict(),
        "high_opt": agent.high_opt.state_dict(),
        "low_opt": agent.low_opt.state_dict(),
        "process_opt": agent.process_opt.state_dict(),
        "total_steps": int(total_steps),
        "update_idx": int(update_idx),
        "config_name": args.config,
        "preset": args.preset,
        "scenario": config.scenario,
        "action_space_type": agent.action_space_type,
        "action_dim": agent.action_dim,
        "n_agents": agent.n_agents,
        "n_skills": agent.n_skills,
        "duration_candidates": agent.duration_candidates,
        "algorithm": "ha_ctse_process_standalone",
    }


def save_checkpoint(
    path: Path,
    agent: StandaloneProcessAgent,
    args: argparse.Namespace,
    config,
    total_steps: int,
    update_idx: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint_payload(agent, args, config, total_steps, update_idx), path)


def prune_periodic_checkpoints(log_dir: str | Path, keep_last: int) -> None:
    keep_last = int(keep_last)
    if keep_last <= 0:
        return
    paths = sorted(
        Path(log_dir).glob("standalone_process_core_update_*.pt"),
        key=lambda path: path.stat().st_mtime,
    )
    for path in paths[:-keep_last]:
        try:
            path.unlink()
        except OSError:
            pass


def load_checkpoint(
    path: str | Path,
    agent: StandaloneProcessAgent,
    load_optimizers: bool = True,
) -> tuple[int, int]:
    checkpoint = torch.load(Path(path), map_location=agent.device)
    agent.high.load_state_dict(checkpoint["high"])
    if "compact" in checkpoint:
        agent.compact.load_state_dict(checkpoint["compact"])
    if "bridge" in checkpoint:
        agent.bridge.load_state_dict(checkpoint["bridge"])
    agent.low.load_state_dict(checkpoint["low"])
    agent.process.load_state_dict(checkpoint["process"])
    if "process_posterior" in checkpoint:
        agent.process_posterior.load_state_dict(checkpoint["process_posterior"])
    if load_optimizers:
        if "high_opt" in checkpoint:
            try:
                agent.high_opt.load_state_dict(checkpoint["high_opt"])
            except ValueError:
                pass
        if "low_opt" in checkpoint:
            agent.low_opt.load_state_dict(checkpoint["low_opt"])
        if "process_opt" in checkpoint:
            try:
                agent.process_opt.load_state_dict(checkpoint["process_opt"])
            except ValueError:
                pass
    return int(checkpoint.get("total_steps", 0)), int(checkpoint.get("update_idx", 0))


def load_checkpoint_metadata(path: str | Path) -> dict[str, Any]:
    checkpoint = torch.load(Path(path), map_location="cpu")
    return {
        "duration_candidates": checkpoint.get("duration_candidates"),
        "n_agents": checkpoint.get("n_agents"),
        "n_skills": checkpoint.get("n_skills"),
        "preset": checkpoint.get("preset"),
        "scenario": checkpoint.get("scenario"),
        "total_steps": checkpoint.get("total_steps"),
        "update_idx": checkpoint.get("update_idx"),
    }


def apply_checkpoint_structure(config, args: argparse.Namespace, metadata: dict[str, Any]) -> None:
    duration_candidates = metadata.get("duration_candidates")
    if duration_candidates:
        config.skill_lifetime_candidates = tuple(int(v) for v in duration_candidates)

    checkpoint_agents = metadata.get("n_agents")
    if checkpoint_agents is not None:
        checkpoint_agents = int(checkpoint_agents)
        requested_agents = int(getattr(args, "n_agents", 0) or 0)
        if requested_agents > 0 and requested_agents != checkpoint_agents:
            raise ValueError(
                "--n_agents does not match checkpoint: "
                f"requested={requested_agents}, checkpoint={checkpoint_agents}"
            )
        config.n_agents = checkpoint_agents
        config.n_uavs = checkpoint_agents
        config.max_observed_uavs = max(
            checkpoint_agents,
            int(getattr(config, "max_observed_uavs", checkpoint_agents)),
        )


def run_env_dry_check(config, args: argparse.Namespace) -> None:
    """Check the standalone env path without touching HMASD training code."""

    env = create_env(config, config.scenario, args.seed, rank=0, scale_mode="train")
    try:
        obs, info = env.reset(seed=args.seed)
        state = np.asarray(info["state"], dtype=np.float32)
        emit(
            args,
            "standalone_env_reset "
            f"scenario={normalize_scenario(args.scenario)} "
            f"state_shape={tuple(state.shape)} obs_shape={tuple(obs.shape)} "
            f"action_space={env.action_space}"
        )

        for step in range(int(args.dry_run_env_steps)):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated)
            emit(
                args,
                "standalone_env_step "
                f"step={step + 1} reward={float(reward):.6f} done={done}"
            )
            if done:
                obs, info = env.reset()
    finally:
        env.close()


def numeric_metric(value) -> float | None:
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if arr.size == 0:
        return None
    scalar = float(np.nanmean(arr))
    return scalar if np.isfinite(scalar) else None


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


def evaluate(
    agent: StandaloneProcessAgent,
    config,
    args: argparse.Namespace,
    episodes: int,
    total_steps: int,
) -> dict[str, float]:
    """Run deterministic standalone eval without changing training segments."""

    env = create_env(config, config.scenario, int(args.seed) + 100000, rank=0, scale_mode="eval")
    active_backup = agent.active_skills.copy()
    duration_backup = agent.duration_remaining.copy()
    age_backup = agent.skill_age.copy()
    has_active_backup = agent.has_active_skill.copy()
    segments_backup = agent.segments
    agent.segments = SegmentManager(agent.num_envs, agent.n_agents)

    rewards: list[float] = []
    lengths: list[int] = []
    metric_values: dict[str, list[float]] = {}
    eval_records: list[dict[str, float]] = []
    save_topology = bool(getattr(args, "save_topology", False))
    topology_interval = max(1, int(getattr(args, "topology_interval", 25)))
    topology_episodes = max(0, int(getattr(args, "topology_episodes", 1)))
    topology_max_frames = max(1, int(getattr(args, "topology_max_frames", 160)))
    try:
        for episode_idx in range(max(int(episodes), 1)):
            obs, info = env.reset(seed=int(args.seed) + 100000 + episode_idx)
            state = info.get("state")
            agent.reset_env_state(0)
            episode_reward = 0.0
            episode_length = 0
            last_info = info
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
                    deterministic=True,
                )
                actions, _, _ = agent.act_low(obs, env_id=0, deterministic=True)
                obs, reward, terminated, truncated, last_info = env.step(actions)
                state = last_info.get("next_state", state)
                episode_reward += float(reward)
                episode_length += 1
                done = bool(terminated or truncated)
                hit_step_cap = int(args.eval_max_steps) > 0 and episode_length >= int(args.eval_max_steps)
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
            eval_record = {
                "checkpoint": str(getattr(args, "eval_checkpoint_name", "")),
                "total_steps": int(total_steps),
                "episode": episode_idx,
                "reward": episode_reward,
                "length": episode_length,
                **episode_metrics,
            }
            eval_records.append(eval_record)
            append_csv(Path(args.log_dir) / "metrics" / "eval_episodes.csv", eval_record, EVAL_FIELDS)
            for key, value in episode_metrics.items():
                metric_values.setdefault(key, []).append(value)
            if capture_topology and topology_frames:
                try:
                    artifacts = save_topology_artifacts(
                        topology_frames,
                        args.log_dir,
                        total_steps=total_steps,
                        episode=episode_idx,
                        checkpoint_name=str(getattr(args, "eval_checkpoint_name", "")),
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
        agent.segments = segments_backup
        agent.active_skills = active_backup
        agent.duration_remaining = duration_backup
        agent.skill_age = age_backup
        agent.has_active_skill = has_active_backup

    metrics = {
        "reward_mean": float(np.mean(rewards)) if rewards else 0.0,
        "reward_std": float(np.std(rewards)) if rewards else 0.0,
        "length_mean": float(np.mean(lengths)) if lengths else 0.0,
    }
    for key, values in metric_values.items():
        metrics[key] = float(np.mean(values)) if values else 0.0
    if eval_records:
        save_eval_plots(args.log_dir, window=max(1, int(getattr(args, "eval_episodes", 1))))

    emit(
        args,
        "standalone_eval "
        f"total_steps={int(total_steps)} episodes={max(int(episodes), 1)} "
        f"reward_mean={metrics['reward_mean']:.6f} "
        f"reward_std={metrics['reward_std']:.6f} "
        f"length_mean={metrics['length_mean']:.1f} "
        f"coverage={metrics.get('coverage', 0.0):.6f} "
        f"qos={metrics.get('qos', 0.0):.6f} "
        f"throughput={metrics.get('throughput', 0.0):.6f} "
        f"battery_min={metrics.get('battery_min', 0.0):.6f}"
    )
    return metrics


def log_train_metrics(writer, total_steps: int, episode_rewards, process_metrics, low_metrics) -> None:
    if writer is None:
        return
    env_reward_mean = float(np.mean(episode_rewards)) if episode_rewards else 0.0
    writer.add_scalar("Train/EnvRewardMean", env_reward_mean, total_steps)
    writer.add_scalar("Process/Segments", process_metrics["process_segments"], total_steps)
    writer.add_scalar("Process/Loss", process_metrics["process_loss"], total_steps)
    writer.add_scalar("Process/OutcomeLoss", process_metrics.get("process_outcome_loss", 0.0), total_steps)
    writer.add_scalar("Process/ContrastiveLoss", process_metrics.get("process_contrastive_loss", 0.0), total_steps)
    writer.add_scalar("Process/PriorLoss", process_metrics.get("process_prior_loss", 0.0), total_steps)
    writer.add_scalar("Process/PosteriorAcc", process_metrics.get("process_posterior_acc", 0.0), total_steps)
    writer.add_scalar("Process/MIEstimateMean", process_metrics.get("process_mi_estimate_mean", 0.0), total_steps)
    writer.add_scalar("Process/LogQMean", process_metrics.get("process_log_q_mean", 0.0), total_steps)
    writer.add_scalar("Process/LogPMean", process_metrics.get("process_log_p_mean", 0.0), total_steps)
    writer.add_scalar("Process/RewardMean", process_metrics["process_reward_mean"], total_steps)
    writer.add_scalar("Process/OutcomeAvailableMean", process_metrics["outcome_available_mean"], total_steps)
    writer.add_scalar("Process/OutcomeAbsMean", process_metrics["outcome_abs_mean"], total_steps)
    writer.add_scalar("Process/DurationOnlyAccuracy", process_metrics.get("duration_only_accuracy", 0.0), total_steps)
    writer.add_scalar("Process/SegmentLengthMean", process_metrics.get("segment_length_mean", 0.0), total_steps)
    writer.add_scalar("Process/SegmentLengthMax", process_metrics.get("segment_length_max", 0.0), total_steps)
    writer.add_scalar("Process/DurationTargetMean", process_metrics.get("duration_target_mean", 0.0), total_steps)
    writer.add_scalar("Process/SkillSwitchRate", process_metrics.get("skill_switch_rate", 0.0), total_steps)
    writer.add_scalar("Process/InitialAssignmentRate", process_metrics.get("initial_assignment_rate", 0.0), total_steps)
    writer.add_scalar("Collapse/SkillUsageEntropy", process_metrics.get("skill_usage_entropy", 0.0), total_steps)
    writer.add_scalar("Collapse/SkillUsageMaxFrac", process_metrics.get("skill_usage_max_frac", 0.0), total_steps)
    writer.add_scalar("Collapse/DurationUsageEntropy", process_metrics.get("duration_usage_entropy", 0.0), total_steps)
    writer.add_scalar("Collapse/DurationUsageMaxFrac", process_metrics.get("duration_usage_max_frac", 0.0), total_steps)
    writer.add_scalar("Collapse/SkillDurationMI", process_metrics.get("skill_duration_mi", 0.0), total_steps)
    writer.add_scalar("Collapse/TeamCodeUsageEntropy", process_metrics.get("team_code_usage_entropy", 0.0), total_steps)
    writer.add_scalar("Collapse/TeamCodeUsageMaxFrac", process_metrics.get("team_code_usage_max_frac", 0.0), total_steps)
    writer.add_scalar("Collapse/TeamCodeSkillMI", process_metrics.get("team_code_skill_mi", 0.0), total_steps)
    writer.add_scalar("High/Loss", process_metrics["high_loss"], total_steps)
    writer.add_scalar("High/PolicyLoss", process_metrics.get("high_policy_loss", 0.0), total_steps)
    writer.add_scalar("High/ValueLoss", process_metrics.get("high_value_loss", 0.0), total_steps)
    writer.add_scalar("High/EntropyLoss", process_metrics.get("high_entropy_loss", 0.0), total_steps)
    writer.add_scalar("High/AuxLoss", process_metrics.get("high_aux_loss", 0.0), total_steps)
    writer.add_scalar("High/Entropy", process_metrics["high_entropy"], total_steps)
    writer.add_scalar("High/ReturnMean", process_metrics["high_return_mean"], total_steps)
    writer.add_scalar("High/TeamCodeEntropy", process_metrics.get("team_code_entropy", 0.0), total_steps)
    writer.add_scalar("High/CompactNormMean", process_metrics.get("compact_norm_mean", 0.0), total_steps)
    writer.add_scalar("High/OPTCDLoss", process_metrics.get("opt_cd_loss", 0.0), total_steps)
    writer.add_scalar("High/OPTCMILoss", process_metrics.get("opt_cmi_loss", 0.0), total_steps)
    writer.add_scalar("High/OPTAggregationEntropy", process_metrics.get("opt_aggregation_entropy", 0.0), total_steps)
    writer.add_scalar("Low/Loss", low_metrics["low_loss"], total_steps)
    writer.add_scalar("Low/PolicyLoss", low_metrics.get("low_policy_loss", 0.0), total_steps)
    writer.add_scalar("Low/ValueLoss", low_metrics.get("low_value_loss", 0.0), total_steps)
    writer.add_scalar("Low/EntropyLoss", low_metrics.get("low_entropy_loss", 0.0), total_steps)
    writer.add_scalar("Low/Entropy", low_metrics["low_entropy"], total_steps)
    writer.add_scalar("Low/ReturnMean", low_metrics["return_mean"], total_steps)
    writer.flush()


def export_update_metrics(
    args: argparse.Namespace,
    update_idx: int,
    total_steps: int,
    env_reward_mean: float,
    process_metrics: dict[str, float],
    low_metrics: dict[str, float],
) -> None:
    row = {
        "update": int(update_idx),
        "total_steps": int(total_steps),
        "env_reward_mean": float(env_reward_mean),
        **{key: float(value) for key, value in process_metrics.items()},
        **{key: float(value) for key, value in low_metrics.items()},
    }
    append_csv(Path(args.log_dir) / "metrics" / "train_updates.csv", row, UPDATE_FIELDS)
    if int(getattr(args, "plot_interval", 1)) > 0 and update_idx % int(args.plot_interval) == 0:
        save_update_plots(args.log_dir)


def log_eval_metrics(writer, total_steps: int, metrics: dict[str, float]) -> None:
    if writer is None:
        return
    for key, value in metrics.items():
        writer.add_scalar(f"Eval/{key}", value, total_steps)
    writer.flush()


def train_loop(config, args: argparse.Namespace, writer) -> tuple[StandaloneProcessAgent, int, int]:
    num_envs = max(int(args.num_envs), 1)
    collector = create_collector(config, args, scale_mode="train", num_envs=num_envs)
    try:
        observations, states, _infos = collector.reset_all(seed=int(args.seed))
        env = SimpleNamespace(**collector.spec)
        action_space_type, _, _ = action_space_details(env)
        state_dim = int(collector.spec.get("state_dim") or 0) or (
            int(np.asarray(states[0], dtype=np.float32).reshape(-1).size)
            if states and states[0] is not None
            else None
        )
        agent = create_agent(config, args, env, num_envs=num_envs, state_dim=state_dim)

        total_steps = 0
        update_idx = 0
        if args.resume_from:
            total_steps, update_idx = load_checkpoint(args.resume_from, agent, load_optimizers=True)
            emit(
                args,
                "standalone_resume "
                f"path={args.resume_from} total_steps={total_steps} update_idx={update_idx}"
            )

        export_run_manifest(
            args,
            config,
            env=env,
            agent=agent,
            total_steps=total_steps,
            update_idx=update_idx,
            mode="train",
        )
        emit(
            args,
            "standalone_train_start "
            f"scenario={config.scenario} preset={args.preset or 'none'} "
            f"num_envs={num_envs} n_agents={env.n_uavs} obs_dim={env.obs_dim} action_dim={env.action_dim} "
            f"action_space_type={action_space_type} collector={args.collector_backend} "
            f"policy_update=on_policy "
            f"duration_candidates={tuple(getattr(config, 'skill_lifetime_candidates', ())) } "
            f"rollout_length={args.rollout_length} total_timesteps={args.total_timesteps} "
            f"save_interval={args.save_interval} checkpoint_keep_last={args.checkpoint_keep_last}"
        )

        last_eval_step = int(total_steps)
        while total_steps < int(args.total_timesteps):
            rollout = Rollout()
            episode_rewards = []
            for _local_step in range(int(args.rollout_length)):
                pre_obs = []
                pre_actions = []
                pre_logp = []
                pre_values = []
                pre_rollout_indices = []
                for env_id in range(num_envs):
                    obs = observations[env_id]
                    rollout_idx = len(rollout.rewards) + len(pre_rollout_indices)
                    agent.maybe_assign_skills(
                        obs,
                        state=states[env_id],
                        step=rollout_idx,
                        k=int(args.skill_interval),
                        env_id=env_id,
                    )
                    actions, logp, values = agent.act_low(obs, env_id=env_id)
                    pre_obs.append(obs)
                    pre_actions.append(actions)
                    pre_logp.append(logp)
                    pre_values.append(values)
                    pre_rollout_indices.append(rollout_idx)

                step_results = collector.step(pre_actions)
                for env_id, result in enumerate(step_results):
                    obs = pre_obs[env_id]
                    actions = pre_actions[env_id]
                    logp = pre_logp[env_id]
                    values = pre_values[env_id]
                    rollout_idx = pre_rollout_indices[env_id]
                    next_obs = result.obs
                    reward = result.reward
                    terminated = result.terminated
                    truncated = result.truncated
                    info = result.info
                    done = bool(terminated or truncated)
                    reward_components = info.get("reward_components", {})
                    individual_rewards = np.asarray(
                        reward_components.get(
                            "individual_rewards",
                            [float(reward)] * int(env.n_uavs),
                        ),
                        dtype=np.float32,
                    )
                    if individual_rewards.shape[0] != int(env.n_uavs):
                        individual_rewards = np.full(int(env.n_uavs), float(reward), dtype=np.float32)

                    agent.segments.append(
                        env_id,
                        obs,
                        actions,
                        individual_rewards,
                        next_obs,
                        rollout_idx,
                        reward_info=info.get("reward_info", {}),
                    )
                    rollout.obs.append(np.asarray(obs, dtype=np.float32))
                    rollout.skills.append(agent.active_skills[env_id].copy())
                    rollout.actions.append(actions.copy())
                    rollout.logp.append(logp.copy())
                    rollout.values.append(values.copy())
                    rollout.rewards.append(individual_rewards.copy())
                    rollout.dones.append(done)
                    episode_rewards.append(float(np.mean(individual_rewards)))

                    total_steps += 1
                    observations[env_id] = next_obs
                    states[env_id] = info.get("next_state", states[env_id])
                    if done:
                        agent.segments.flush(env_id)
                        observations[env_id], info = collector.reset_one(env_id)
                        states[env_id] = info.get("state")
                        agent.reset_env_state(env_id)
                if total_steps >= int(args.total_timesteps):
                    break

            agent.segments.flush()
            process_metrics = agent.process_update(rollout)
            low_metrics = agent.update_low(rollout)
            update_idx += 1
            env_reward_mean = float(np.mean(episode_rewards)) if episode_rewards else 0.0
            emit(
                args,
                "standalone_update "
                f"update={update_idx} total_steps={total_steps} "
                f"env_reward_mean={env_reward_mean:.6f} "
                f"process_segments={process_metrics['process_segments']:.0f} "
                f"process_loss={process_metrics['process_loss']:.6f} "
                f"process_mi={process_metrics.get('process_mi_estimate_mean', 0.0):.6f} "
                f"posterior_acc={process_metrics.get('process_posterior_acc', 0.0):.3f} "
                f"process_reward_mean={process_metrics['process_reward_mean']:.6f} "
                f"outcome_available={process_metrics['outcome_available_mean']:.3f} "
                f"outcome_abs_mean={process_metrics['outcome_abs_mean']:.6f} "
                f"duration_only_acc={process_metrics.get('duration_only_accuracy', 0.0):.3f} "
                f"switch_rate={process_metrics.get('skill_switch_rate', 0.0):.3f} "
                f"seg_len_mean={process_metrics.get('segment_length_mean', 0.0):.2f} "
                f"high_loss={process_metrics['high_loss']:.6f} "
                f"high_value_loss={process_metrics.get('high_value_loss', 0.0):.6f} "
                f"high_entropy={process_metrics['high_entropy']:.6f} "
                f"high_return_mean={process_metrics['high_return_mean']:.6f} "
                f"skill_entropy={process_metrics.get('skill_usage_entropy', 0.0):.3f} "
                f"duration_entropy={process_metrics.get('duration_usage_entropy', 0.0):.3f} "
                f"g_entropy={process_metrics.get('team_code_usage_entropy', 0.0):.3f} "
                f"g_skill_mi={process_metrics.get('team_code_skill_mi', 0.0):.3f} "
                f"low_loss={low_metrics['low_loss']:.6f} "
                f"low_value_loss={low_metrics.get('low_value_loss', 0.0):.6f} "
                f"return_mean={low_metrics['return_mean']:.6f}"
            )
            log_train_metrics(writer, total_steps, episode_rewards, process_metrics, low_metrics)
            export_update_metrics(args, update_idx, total_steps, env_reward_mean, process_metrics, low_metrics)
            agent.reset_all_policy_state()

            if int(args.save_interval) > 0 and update_idx % int(args.save_interval) == 0:
                save_checkpoint(
                    Path(args.log_dir) / f"standalone_process_core_update_{update_idx}.pt",
                    agent,
                    args,
                    config,
                    total_steps,
                    update_idx,
                )
                prune_periodic_checkpoints(args.log_dir, int(args.checkpoint_keep_last))

            if int(args.eval_interval) > 0 and total_steps - last_eval_step >= int(args.eval_interval):
                eval_metrics = evaluate(
                    agent,
                    config,
                    args,
                    episodes=int(args.eval_episodes),
                    total_steps=total_steps,
                )
                log_eval_metrics(writer, total_steps, eval_metrics)
                last_eval_step = int(total_steps)

        save_checkpoint(
            Path(args.log_dir) / "standalone_process_core_final.pt",
            agent,
            args,
            config,
            total_steps,
            update_idx,
        )
        export_run_manifest(
            args,
            config,
            env=env,
            agent=agent,
            total_steps=total_steps,
            update_idx=update_idx,
            mode="train",
        )
        return agent, total_steps, update_idx
    finally:
        collector.close()


def eval_loop(config, args: argparse.Namespace, writer) -> None:
    if not args.resume_from:
        raise ValueError("--mode eval requires --resume_from pointing to a standalone checkpoint")
    env = create_env(config, config.scenario, args.seed, rank=0, scale_mode="eval")
    try:
        _obs, info = env.reset(seed=args.seed)
        state_dim = int(np.asarray(info.get("state"), dtype=np.float32).reshape(-1).size) if info.get("state") is not None else None
        agent = create_agent(config, args, env, num_envs=1, state_dim=state_dim)
    finally:
        env.close()
    total_steps, update_idx = load_checkpoint(args.resume_from, agent, load_optimizers=False)
    export_run_manifest(
        args,
        config,
        env=env,
        agent=agent,
        total_steps=total_steps,
        update_idx=update_idx,
        mode="eval",
    )
    emit(
        args,
        "standalone_eval_start "
        f"path={args.resume_from} total_steps={total_steps} update_idx={update_idx} "
        f"duration_candidates={tuple(getattr(config, 'skill_lifetime_candidates', ())) }"
    )
    args.eval_checkpoint_name = Path(args.resume_from).name
    metrics = evaluate(
        agent,
        config,
        args,
        episodes=int(args.eval_episodes),
        total_steps=total_steps,
    )
    log_eval_metrics(writer, total_steps, metrics)


def main() -> None:
    args = parse_args()
    Path(args.log_dir).mkdir(parents=True, exist_ok=True)
    writer = SummaryWriter(args.log_dir) if SummaryWriter is not None else None
    config = load_config(args.config, args.preset or None)
    config.scenario = normalize_scenario(args.scenario)
    apply_standalone_overrides(config, args)
    if args.resume_from:
        metadata = load_checkpoint_metadata(args.resume_from)
        apply_checkpoint_structure(config, args, metadata)

    try:
        if args.dry_run_env_steps > 0:
            run_env_dry_check(config, args)
            return
        if args.mode == "eval":
            eval_loop(config, args, writer)
        else:
            train_loop(config, args, writer)
    finally:
        if writer is not None:
            writer.close()


if __name__ == "__main__":
    main()
