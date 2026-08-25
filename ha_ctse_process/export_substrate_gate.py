"""Diagnostic-only Round-12 substrate gate exporter.

This module replays stored HA-CTSE checkpoints and dumps compact OPT context
and topology-role rows for offline gate analysis. It does not train, update
optimizers, or depend on training-time topology-role probe flags.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch

from ha_ctse_process.plotting import extract_uav_metrics
from ha_ctse_process.standalone_segments import SegmentManager
from ha_ctse_process.topology_role import TOPOLOGY_ROLE_NAMES, TopologyRoleExtractor


STEP_FIELDS = (
    "checkpoint",
    "update_idx",
    "total_steps",
    "episode",
    "step",
    "reward_so_far",
    "omega_argmax",
    "omega_entropy",
    "compact_norm",
    "compact_dim",
    "compact_json",
    "omega_dim",
    "omega_json",
    "delta_omega_l1",
    "coverage_positive_step",
    "coverage_eq1_step",
    "zero_throughput_step",
    "throughput_gt5_step",
    "backhaul_connected_step",
    "throughput",
    "coverage",
)

ROLE_FIELDS = (
    "checkpoint",
    "update_idx",
    "total_steps",
    "episode",
    "step",
    "agent_id",
    "omega_argmax",
    "role_label",
    "role_available",
    "role_name",
    "role_score_idle",
    "role_score_relay",
    "role_score_service",
    "role_score_relay_service",
)

OPTIONAL_SCALAR_DEFAULTS = {
    "process_reward_coef": None,
    "process_reward_clip": None,
    "process_contrast_coef": None,
    "process_outcome_coef": None,
    "process_reward_contrast_coef": None,
    "process_reward_outcome_coef": None,
    "process_prior_coef": None,
    "process_shortcut_coef": None,
    "context_shortcut_coef": None,
    "process_shortcut_margin": None,
    "process_shortcut_margin_coef": None,
    "transition_skill_coef": None,
    "transition_skill_prior_coef": None,
    "transition_context_shortcut_coef": None,
    "transition_skill_reward_coef": None,
    "transition_skill_reward_clip": None,
    "outcome_residual_coef": None,
    "outcome_residual_reward_coef": None,
    "outcome_residual_reward_clip": None,
    "topology_role_coef": None,
    "topology_role_min_score": None,
    "topology_role_reward_coef": None,
    "topology_role_reward_clip": None,
    "semantic_shortcut_hard_stop_margin": None,
    "g_info_coef_skill": None,
    "g_info_coef_duration": None,
    "g_info_coef_edit": None,
    "intrinsic_segment_gate_margin": None,
    "intrinsic_segment_gate_min_residual_mi": None,
    "intrinsic_segment_gate_min_posterior_acc": None,
    "high_entropy_coef": None,
    "low_entropy_coef": None,
    "high_max_grad_norm": None,
    "low_max_grad_norm": None,
    "low_value_loss_coef": None,
    "low_clip_epsilon": None,
    "smdp_bootstrap_coef": None,
    "edit_penalty_alpha": None,
    "switch_penalty_beta": None,
    "opt_cd_coef": None,
    "opt_cmi_coef": None,
    "p2_recovery_reward_coef": None,
    "p2_recovery_reward_clip": None,
}

TRAINING_OVERRIDE_DEFAULTS = {
    "team_bridge_type": "",
    "low_level_architecture": "",
    "opt_compact_dim": 0,
    "opt_num_prototypes": 0,
    "process_reward_mode": "",
    "process_reward_injection": "",
    "process_reward_warmup_steps": -1,
    "transition_skill_reward_warmup_steps": -1,
    "transition_skill_max_samples": 0,
    "outcome_residual_horizon": 0,
    "outcome_residual_hidden_dim": 0,
    "outcome_residual_injection": "",
    "topology_role_hidden_dim": 0,
    "topology_role_injection": "",
    "p2_recovery_reward_level": None,
    "semantic_shortcut_hard_stop_min_segments": 0,
    "g_intervention_kl_max_segments": 0,
    "g_info_warmup_steps": -1,
    "g_info_anneal_steps": -1,
    "g_info_max_segments": 0,
    "intrinsic_phase_bins": 0,
    "intrinsic_segment_gate_min_segments": 0,
    "low_rnn_hidden_size": 0,
    "low_sequence_length": 0,
    "low_sequence_batch_size": 0,
    "low_ppo_epochs": 0,
    "disable_process_reward": False,
    "disable_process_posterior_mi": False,
    "disable_residual_process_posterior": False,
    "disable_context_skill_shortcut": False,
    "disable_transition_skill_discriminator": False,
    "disable_transition_skill_team_conditioning": False,
    "disable_outcome_residual_probe": False,
    "disable_outcome_residual_norm": False,
    "disable_topology_role_probe": False,
    "enable_p2_recovery_compute": False,
    "enable_p2_recovery_reward": False,
    "disable_semantic_shortcut_hard_stop": False,
    "semantic_shortcut_hard_stop_raise": False,
    "disable_g_intervention_kl_diagnostic": False,
    "disable_g_info_diagnostic": False,
    "enable_g_info_objective": False,
    "disable_intrinsic_segment_gate": False,
    "enable_intrinsic_reward_norm": False,
    "disable_smdp_discounted_high_return": False,
    "disable_smdp_bootstrap": False,
    "disable_high_value_norm": False,
    "disable_recurrent_low_level": False,
    "disable_low_value_norm": False,
    "enable_low_actor_team_code": False,
    **OPTIONAL_SCALAR_DEFAULTS,
}


def _train_helpers():
    from ha_ctse_process.checkpoint_io import (
        apply_checkpoint_structure,
        load_checkpoint,
        load_checkpoint_metadata,
    )
    from ha_ctse_process.standalone_cli import (
        apply_standalone_overrides,
        create_agent,
        create_env,
        load_config,
    )

    return SimpleNamespace(
        apply_checkpoint_structure=apply_checkpoint_structure,
        apply_standalone_overrides=apply_standalone_overrides,
        create_agent=create_agent,
        create_env=create_env,
        load_checkpoint=load_checkpoint,
        load_checkpoint_metadata=load_checkpoint_metadata,
        load_config=load_config,
    )


def _append_csv(path: Path, row: dict[str, Any], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    if exists:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = tuple(next(reader, ()))
        if header != fields:
            raise ValueError(
                f"CSV header mismatch for {path}: "
                f"expected={list(fields)} actual={list(header)}"
            )
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})


def _vector_json(values: np.ndarray) -> str:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.all(np.isfinite(array)):
        raise ValueError("cannot serialize non-finite vector")
    return json.dumps([float(value) for value in array], separators=(",", ":"))


def _checkpoint_update(path: Path) -> int | None:
    match = re.search(r"standalone_process_core_update_(\d+)\.pt$", path.name)
    if match:
        return int(match.group(1))
    return None


def _parse_update_filter(text: str) -> tuple[set[int], bool] | None:
    if not str(text or "").strip():
        return None
    updates: set[int] = set()
    include_final = False
    for chunk in str(text).replace(";", ",").split(","):
        chunk = chunk.strip().lower()
        if not chunk:
            continue
        if chunk == "final":
            include_final = True
        else:
            updates.add(int(chunk))
    return updates, include_final


def discover_checkpoints(
    checkpoint_dir: Path,
    updates: str,
    update_stride: int,
    no_final: bool,
) -> list[Path]:
    update_paths = sorted(
        checkpoint_dir.glob("standalone_process_core_update_*.pt"),
        key=lambda path: _checkpoint_update(path) or -1,
    )
    final_path = checkpoint_dir / "standalone_process_core_final.pt"
    selected: list[Path] = []
    update_filter = _parse_update_filter(updates)
    if update_filter is not None:
        requested, want_final = update_filter
        found_updates = {
            int(update)
            for update in (_checkpoint_update(path) for path in update_paths)
            if update is not None
        }
        missing = sorted(update for update in requested if update not in found_updates)
        if missing:
            missing_text = ",".join(str(update) for update in missing)
            raise FileNotFoundError(f"Missing requested checkpoint updates in {checkpoint_dir}: {missing_text}")
        selected.extend(path for path in update_paths if _checkpoint_update(path) in requested)
        if want_final and final_path.exists() and not no_final:
            selected.append(final_path)
    else:
        stride = int(update_stride)
        if stride > 0:
            selected.extend(path for path in update_paths if (_checkpoint_update(path) or 0) % stride == 0)
        else:
            selected.extend(update_paths)
        if final_path.exists() and not no_final:
            selected.append(final_path)

    seen: set[str] = set()
    unique: list[Path] = []
    for path in selected:
        resolved = str(path.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _ensure_training_override_defaults(args: argparse.Namespace) -> None:
    for key, value in TRAINING_OVERRIDE_DEFAULTS.items():
        if not hasattr(args, key):
            setattr(args, key, value)


def _state_info(info: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(info, dict):
        return {}
    state_info = info.get("state_info")
    if isinstance(state_info, dict):
        return dict(state_info)
    return {
        key: value
        for key, value in info.items()
        if key not in {"reward_info", "reward_components", "infos_dict", "terminations_dict", "truncations_dict"}
    }


def _reward_info(info: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(info, dict):
        return {}
    reward = {
        key: value
        for key, value in info.items()
        if key not in {"state_info", "reward_info", "reward_components", "infos_dict", "terminations_dict", "truncations_dict"}
    }
    reward_components = info.get("reward_components")
    if isinstance(reward_components, dict):
        reward.update(reward_components)
        nested = reward_components.get("reward_info")
        if isinstance(nested, dict):
            reward.update(nested)
    reward_info = info.get("reward_info")
    if isinstance(reward_info, dict):
        reward.update(reward_info)
    return reward


def _metric_flags(reward_info: dict[str, Any]) -> dict[str, float]:
    metrics = extract_uav_metrics(reward_info)
    if "coverage_ratio" in metrics and "coverage" not in metrics:
        metrics["coverage"] = metrics["coverage_ratio"]
    if "system_throughput_mbps" in metrics and "throughput" not in metrics:
        metrics["throughput"] = metrics["system_throughput_mbps"]
    coverage = float(metrics.get("coverage", 0.0))
    throughput = float(metrics.get("throughput", 0.0))
    return {
        "coverage_positive_step": 1.0 if coverage > 1e-6 else 0.0,
        "coverage_eq1_step": 1.0 if coverage >= 0.999 else 0.0,
        "zero_throughput_step": 1.0 if throughput <= 1e-6 else 0.0,
        "throughput_gt5_step": 1.0 if throughput > 5.0 else 0.0,
        "backhaul_connected_step": float(metrics.get("backhaul_connected_flag", 0.0)),
        "throughput": throughput,
        "coverage": coverage,
    }


def _compact_row(agent, state: Any, obs: Any) -> tuple[np.ndarray, np.ndarray, float, float]:
    state_arr = agent._state_array(state, agent._joint_obs_array(obs))
    joint_obs = agent._joint_obs_array(obs)
    state_t = torch.as_tensor(state_arr, dtype=torch.float32, device=agent.device).reshape(1, -1)
    joint_t = torch.as_tensor(joint_obs, dtype=torch.float32, device=agent.device).reshape(
        1,
        agent.n_agents,
        agent.obs_dim,
    )
    with torch.no_grad():
        compact, _cd_loss, _cmi_loss, weights, entropy = agent.compact(state_t, joint_t)
    compact_np = compact.detach().cpu().numpy().reshape(-1).astype(np.float64)
    weights_np = weights.detach().cpu().numpy().reshape(-1).astype(np.float64)
    entropy_value = float(entropy.detach().cpu().numpy().reshape(-1)[0])
    compact_norm = float(np.linalg.norm(compact_np))
    return compact_np, weights_np, entropy_value, compact_norm


def _reward_vector(reward: Any, n_agents: int) -> np.ndarray:
    arr = np.asarray(reward, dtype=np.float32).reshape(-1)
    if arr.size == int(n_agents):
        return arr
    if arr.size == 1:
        return np.full(int(n_agents), float(arr[0]), dtype=np.float32)
    fitted = np.zeros(int(n_agents), dtype=np.float32)
    count = min(fitted.size, arr.size)
    if count > 0:
        fitted[:count] = arr[:count]
    return fitted


def _segment_omega_argmax(agent, segment) -> int:
    state = getattr(segment, "high_state", None)
    joint_obs = getattr(segment, "high_joint_obs", None)
    if joint_obs is None:
        joint_obs = getattr(segment, "high_obs", None)
    _compact_np, weights_np, _entropy_value, _compact_norm = _compact_row(agent, state, joint_obs)
    return int(np.argmax(weights_np)) if weights_np.size else 0


def _segment_role_row(
    agent,
    extractor: TopologyRoleExtractor,
    checkpoint_name: str,
    update_idx: int,
    total_steps: int,
    episode: int,
    segment,
) -> dict[str, Any]:
    sample = extractor.extract(segment)
    role_scores = np.asarray(sample.role_scores, dtype=np.float64).reshape(-1)
    label = int(sample.label)
    role_name = TOPOLOGY_ROLE_NAMES[label] if 0 <= label < len(TOPOLOGY_ROLE_NAMES) else ""
    return {
        "checkpoint": checkpoint_name,
        "update_idx": int(update_idx),
        "total_steps": int(total_steps),
        "episode": int(episode),
        "step": int(getattr(segment, "start_step", 0)),
        "agent_id": int(getattr(segment, "agent_id", 0)),
        "omega_argmax": _segment_omega_argmax(agent, segment),
        "role_label": label,
        "role_available": 1 if bool(sample.available) else 0,
        "role_name": role_name,
        "role_score_idle": float(role_scores[0]) if role_scores.size > 0 else 0.0,
        "role_score_relay": float(role_scores[1]) if role_scores.size > 1 else 0.0,
        "role_score_service": float(role_scores[2]) if role_scores.size > 2 else 0.0,
        "role_score_relay_service": float(role_scores[3]) if role_scores.size > 3 else 0.0,
    }


def _export_completed_segments(
    agent,
    extractor: TopologyRoleExtractor,
    role_path: Path,
    checkpoint_name: str,
    update_idx: int,
    total_steps: int,
    episode: int,
) -> list[int]:
    labels: list[int] = []
    for segment in agent.segments.pop_completed():
        row = _segment_role_row(
            agent,
            extractor,
            checkpoint_name,
            update_idx,
            total_steps,
            episode,
            segment,
        )
        _append_csv(role_path, row, ROLE_FIELDS)
        if int(row["role_available"]) > 0:
            labels.append(int(row["role_label"]))
    return labels


def _assert_role_label_variance(labels: list[int]) -> None:
    if not labels:
        raise ValueError("--require_role_label_variance requested but no role labels were exported")
    arr = np.asarray(labels, dtype=np.int64)
    variance = float(np.var(arr.astype(np.float64)))
    _, counts = np.unique(arr, return_counts=True)
    max_fraction = float(np.max(counts) / arr.size)
    if variance <= 0.0 or max_fraction >= 0.95:
        raise ValueError(
            "role label variance check failed: "
            f"variance={variance:.6g} max_label_fraction={max_fraction:.6g}"
        )


def _build_agent_for_checkpoint(config, args: argparse.Namespace, checkpoint_path: Path):
    train = _train_helpers()
    metadata = train.load_checkpoint_metadata(checkpoint_path)
    train.apply_checkpoint_structure(config, args, metadata)
    env = train.create_env(config, config.scenario, int(args.seed), rank=0, scale_mode="eval")
    try:
        _obs, info = env.reset(seed=int(args.seed))
        state = info.get("state")
        state_dim = int(np.asarray(state, dtype=np.float32).reshape(-1).size) if state is not None else None
        agent = train.create_agent(config, args, env, num_envs=1, state_dim=state_dim)
    finally:
        env.close()
    total_steps, update_idx = train.load_checkpoint(checkpoint_path, agent, load_optimizers=False)
    return agent, total_steps, update_idx


def export_checkpoint(config, args: argparse.Namespace, checkpoint_path: Path) -> list[int]:
    agent, total_steps, update_idx = _build_agent_for_checkpoint(config, args, checkpoint_path)
    train = _train_helpers()
    env = train.create_env(config, config.scenario, int(args.seed) + 100000, rank=0, scale_mode="eval")
    step_path = Path(args.log_dir) / "substrate_steps.csv"
    role_path = Path(args.log_dir) / "substrate_roles.csv"
    extractor = TopologyRoleExtractor(
        n_agents=agent.n_agents,
        min_score=float(getattr(config, "topology_role_min_score", 1e-6)),
    )
    exported_labels: list[int] = []

    active_backup = agent.active_skills.copy()
    duration_backup = agent.duration_remaining.copy()
    age_backup = agent.skill_age.copy()
    has_active_backup = agent.has_active_skill.copy()
    team_code_backup = agent.active_team_codes.copy()
    low_actor_hxs_backup = agent.low_actor_hxs.copy()
    low_critic_hxs_backup = agent.low_critic_hxs.copy()
    segments_backup = agent.segments
    agent.segments = SegmentManager(agent.num_envs, agent.n_agents)

    try:
        for episode in range(max(int(args.eval_episodes), 1)):
            obs, info = env.reset(seed=int(args.seed) + 100000 + int(episode))
            info = info if isinstance(info, dict) else {}
            state = info.get("state")
            agent.reset_env_state(0)
            reward_so_far = 0.0
            prev_omega: np.ndarray | None = None
            for step in range(max(int(args.eval_max_steps), 1)):
                pre_obs = obs
                pre_info = info if isinstance(info, dict) else {}
                pre_state = state
                pre_state_info = _state_info(pre_info)
                pre_reward_info = _reward_info(pre_info)
                agent.maybe_assign_skills(
                    pre_obs,
                    state=pre_state,
                    step=int(step),
                    k=int(args.skill_interval),
                    env_id=0,
                    deterministic=True,
                )
                exported_labels.extend(
                    _export_completed_segments(
                        agent,
                        extractor,
                        role_path,
                        checkpoint_path.name,
                        int(update_idx),
                        int(total_steps),
                        int(episode),
                    )
                )
                if int(step) % int(args.dump_interval) == 0:
                    compact_np, weights_np, entropy_value, compact_norm = _compact_row(agent, pre_state, pre_obs)
                    if prev_omega is None:
                        delta = 0.0
                    else:
                        common = min(prev_omega.size, weights_np.size)
                        delta = float(np.sum(np.abs(weights_np[:common] - prev_omega[:common])))
                        if prev_omega.size != weights_np.size:
                            delta += float(np.sum(np.abs(weights_np[common:])))
                            delta += float(np.sum(np.abs(prev_omega[common:])))
                    prev_omega = weights_np.copy()
                    omega_argmax = int(np.argmax(weights_np)) if weights_np.size else 0
                    row = {
                        "checkpoint": checkpoint_path.name,
                        "update_idx": int(update_idx),
                        "total_steps": int(total_steps),
                        "episode": int(episode),
                        "step": int(step),
                        "reward_so_far": float(reward_so_far),
                        "omega_argmax": omega_argmax,
                        "omega_entropy": entropy_value,
                        "compact_norm": compact_norm,
                        "compact_dim": int(compact_np.size),
                        "compact_json": _vector_json(compact_np),
                        "omega_dim": int(weights_np.size),
                        "omega_json": _vector_json(weights_np),
                        "delta_omega_l1": delta,
                        **_metric_flags(pre_reward_info),
                    }
                    _append_csv(step_path, row, STEP_FIELDS)
                actions, _logp, _values = agent.act_low(pre_obs, env_id=0, deterministic=True, state=pre_state)
                next_obs, reward, terminated, truncated, next_info = env.step(actions)
                next_info = next_info if isinstance(next_info, dict) else {}
                next_state = next_info.get("next_state", pre_state)
                done = bool(terminated or truncated)
                agent.segments.append(
                    env_id=0,
                    obs=pre_obs,
                    actions=actions,
                    rewards=_reward_vector(reward, agent.n_agents),
                    next_obs=next_obs,
                    rollout_idx=int(step),
                    reward_info=_reward_info(next_info),
                    state_info=_state_info(next_info),
                    next_state=next_state,
                    done=done,
                    pre_state_info=pre_state_info,
                    pre_reward_info=pre_reward_info,
                )
                exported_labels.extend(
                    _export_completed_segments(
                        agent,
                        extractor,
                        role_path,
                        checkpoint_path.name,
                        int(update_idx),
                        int(total_steps),
                        int(episode),
                    )
                )
                obs = next_obs
                info = next_info
                state = next_state
                reward_so_far += float(np.sum(np.asarray(reward, dtype=np.float64)))
                if done:
                    break
            agent.segments.flush(env_id=0)
            exported_labels.extend(
                _export_completed_segments(
                    agent,
                    extractor,
                    role_path,
                    checkpoint_path.name,
                    int(update_idx),
                    int(total_steps),
                    int(episode),
                )
            )
    finally:
        env.close()
        agent.segments = segments_backup
        agent.active_skills = active_backup
        agent.duration_remaining = duration_backup
        agent.skill_age = age_backup
        agent.has_active_skill = has_active_backup
        agent.active_team_codes = team_code_backup
        agent.low_actor_hxs = low_actor_hxs_backup
        agent.low_critic_hxs = low_critic_hxs_backup
    return exported_labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export R12 substrate-gate diagnostic rows.")
    parser.add_argument("--checkpoint_dir", required=True)
    parser.add_argument("--log_dir", required=True)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--preset", default="")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--n_agents", type=int, default=0)
    parser.add_argument("--skill_interval", type=int, default=10)
    parser.add_argument("--skill_lifetime_candidates", default="")
    parser.add_argument("--updates", default="20,40,60,final")
    parser.add_argument("--update_stride", type=int, default=20)
    parser.add_argument("--no_final", action="store_true")
    parser.add_argument("--eval_episodes", type=int, default=4)
    parser.add_argument("--eval_max_steps", type=int, default=500)
    parser.add_argument("--dump_interval", type=int, default=10)
    parser.add_argument("--require_role_label_variance", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _ensure_training_override_defaults(args)
    if int(args.dump_interval) <= 0:
        raise ValueError("--dump_interval must be positive")
    if int(args.eval_max_steps) <= 0:
        raise ValueError("--eval_max_steps must be positive")

    log_dir = Path(args.log_dir)
    if args.overwrite:
        for name in ("substrate_steps.csv", "substrate_roles.csv"):
            path = log_dir / name
            if path.exists():
                path.unlink()
    log_dir.mkdir(parents=True, exist_ok=True)

    checkpoints = discover_checkpoints(
        Path(args.checkpoint_dir),
        updates=str(args.updates),
        update_stride=int(args.update_stride),
        no_final=bool(args.no_final),
    )
    if not checkpoints:
        raise FileNotFoundError(f"No checkpoints selected from {args.checkpoint_dir}")

    print(f"r12_export_selected checkpoints={len(checkpoints)}")
    for checkpoint in checkpoints:
        print(f"r12_export_selected checkpoint={checkpoint}")

    train = _train_helpers()
    for checkpoint in checkpoints:
        print(f"r12_export checkpoint={checkpoint}")
        checkpoint_config = train.load_config(args.config, args.preset or None)
        checkpoint_config.scenario = str(args.scenario)
        train.apply_standalone_overrides(checkpoint_config, args)
        checkpoint_labels = export_checkpoint(checkpoint_config, args, checkpoint)
        if bool(args.require_role_label_variance):
            try:
                _assert_role_label_variance(checkpoint_labels)
            except ValueError as exc:
                raise ValueError(f"{checkpoint.name}: {exc}") from exc
    print(f"r12_export_done checkpoints={len(checkpoints)} log_dir={log_dir}")


if __name__ == "__main__":
    main()
