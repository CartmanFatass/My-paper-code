"""Offline forced-behavior audit for R24 assignment-to-behavior checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.r24_behavior_audit import (  # noqa: E402
    R24AuditRecord,
    action_feature_distance,
    effect_distance,
    summarize_audit_records,
    write_audit_csv,
)


def _parse_horizons(text: str) -> tuple[int, ...]:
    values: list[int] = []
    for chunk in str(text or "").replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        value = int(chunk)
        if value <= 0:
            raise ValueError("horizons must be positive integers")
        values.append(value)
    if not values:
        raise ValueError("at least one horizon is required")
    return tuple(dict.fromkeys(values))


def _rollout_action_from_features(action_features, action_space_type: str):
    features = np.asarray(action_features)
    if str(action_space_type) == "discrete":
        rows = features.reshape(1, -1) if features.ndim == 1 else features.reshape(features.shape[0], -1)
        return np.argmax(rows, axis=-1).astype(np.int64)
    return features.astype(np.float32, copy=False)


def _state_from_info(info: dict[str, Any], previous_state=None) -> np.ndarray:
    state = info.get("next_state", info.get("state", previous_state))
    return np.asarray(state, dtype=np.float32).reshape(-1)


def _label_values(count: int, max_labels: int) -> list[int]:
    count = int(max(count, 1))
    limit = count if int(max_labels) <= 0 else min(count, int(max_labels))
    return list(range(limit))


def _train_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        seed=int(args.seed),
        n_agents=int(args.n_agents),
        device=str(args.device),
        config=str(args.config),
        preset=str(args.preset),
        scenario=str(args.scenario),
        log_dir=str(args.out_dir),
    )


def _set_eval_mode(agent) -> None:
    seen: set[int] = set()
    for value in vars(agent).values():
        if id(value) in seen:
            continue
        seen.add(id(value))
        eval_fn = getattr(value, "eval", None)
        if callable(eval_fn):
            eval_fn()


def _force_xi(agent, label: int, horizon: int) -> None:
    env_id = 0
    label = int(np.clip(label, 0, int(agent.n_skills) - 1))
    agent.active_skills[env_id, :] = label
    agent.active_duration_indices[env_id, :] = 0
    agent.duration_remaining[env_id, :] = int(max(horizon, 1)) + 1
    agent.skill_age[env_id, :] = 0
    agent.has_active_skill[env_id, :] = True
    if hasattr(agent, "active_team_codes"):
        agent.active_team_codes[env_id] = 0
    if hasattr(agent, "team_intent_remaining"):
        agent.team_intent_remaining[env_id] = int(max(horizon, 1)) + 1
    if hasattr(agent, "team_intent_age"):
        agent.team_intent_age[env_id] = 0


def _force_z_assignment(agent, obs, state, label: int, skill_interval: int, horizon: int) -> None:
    env_id = 0
    label = int(np.clip(label, 0, int(agent.num_team_codes) - 1))
    agent.active_team_codes[env_id] = label
    if hasattr(agent, "team_intent_remaining"):
        agent.team_intent_remaining[env_id] = int(max(horizon, 1)) + 1
    if hasattr(agent, "team_intent_age"):
        agent.team_intent_age[env_id] = 0
    agent.maybe_assign_skills(
        obs,
        state=state,
        step=0,
        k=int(max(skill_interval, 1)),
        env_id=env_id,
        deterministic=True,
    )
    agent.active_team_codes[env_id] = label
    if hasattr(agent, "team_intent_remaining"):
        agent.team_intent_remaining[env_id] = int(max(horizon, 1)) + 1


def _apply_forced_label(
    agent,
    obs,
    state,
    forced_kind: str,
    label: int,
    skill_interval: int,
    horizon: int,
) -> None:
    agent.reset_env_state(0)
    if forced_kind == "xi":
        _force_xi(agent, label, horizon)
        return
    if forced_kind == "z":
        _force_z_assignment(agent, obs, state, label, skill_interval, horizon)
        return
    raise ValueError(f"unknown forced_kind={forced_kind!r}")


def _forced_action_features(agent, obs) -> np.ndarray:
    env_id = 0
    skills = np.asarray(agent.active_skills[env_id], dtype=np.int64)
    team_codes = np.full(int(agent.n_agents), int(agent.active_team_codes[env_id]), dtype=np.int64)
    agent_ids = np.arange(int(agent.n_agents), dtype=np.int64)
    features, _entropy = agent._low_actor_forced_skill_outputs(
        np.asarray(obs, dtype=np.float32),
        skills,
        team_codes,
        agent_ids,
    )
    return np.asarray(features, dtype=np.float32)


def _trace_forced_rollout(
    env,
    agent,
    reset_seed: int,
    forced_kind: str,
    label: int,
    max_horizon: int,
    skill_interval: int,
) -> tuple[np.ndarray, list[np.ndarray], np.ndarray]:
    obs, info = env.reset(seed=int(reset_seed))
    state = _state_from_info(info)
    _apply_forced_label(agent, obs, state, forced_kind, label, skill_interval, max_horizon)
    first_features = _forced_action_features(agent, obs)
    states = [state]
    current_state = state
    for _step in range(int(max_horizon)):
        features = _forced_action_features(agent, obs)
        actions = _rollout_action_from_features(features, agent.action_space_type)
        obs, _reward, terminated, truncated, info = env.step(actions)
        current_state = _state_from_info(info, previous_state=current_state)
        states.append(current_state)
        if bool(terminated or truncated):
            break
    return first_features, states, state


def _state_at(states: list[np.ndarray], horizon: int) -> np.ndarray:
    if not states:
        return np.zeros(1, dtype=np.float32)
    index = min(int(horizon), len(states) - 1)
    return states[index]


def _audit_kind(
    env,
    agent,
    forced_kind: str,
    labels: list[int],
    horizons: tuple[int, ...],
    n_resets: int,
    seed: int,
    skill_interval: int,
) -> list[R24AuditRecord]:
    base_label = 0
    max_horizon = max(horizons)
    records: list[R24AuditRecord] = []
    for reset_idx in range(int(n_resets)):
        reset_seed = int(seed) + int(reset_idx)
        base_features, base_states, base_start = _trace_forced_rollout(
            env,
            agent,
            reset_seed=reset_seed,
            forced_kind=forced_kind,
            label=base_label,
            max_horizon=max_horizon,
            skill_interval=skill_interval,
        )
        for label in labels:
            forced_features, forced_states, forced_start = _trace_forced_rollout(
                env,
                agent,
                reset_seed=reset_seed,
                forced_kind=forced_kind,
                label=int(label),
                max_horizon=max_horizon,
                skill_interval=skill_interval,
            )
            action_distance = action_feature_distance(forced_features, base_features)
            for horizon in horizons:
                records.append(
                    R24AuditRecord(
                        horizon=int(horizon),
                        forced_kind=forced_kind,
                        action_distance=float(action_distance),
                        effect_distance=effect_distance(
                            base_start,
                            _state_at(base_states, horizon),
                            forced_start,
                            _state_at(forced_states, horizon),
                        ),
                        label=int(label),
                    )
                )
    return records


def run_r24_behavior_audit(args: argparse.Namespace) -> dict[str, float]:
    from ha_ctse_process import train as train_mod

    horizons = _parse_horizons(args.horizons)
    internal_args = _train_args(args)
    config = train_mod.load_config(args.config, args.preset or None)
    config.scenario = train_mod.normalize_scenario(args.scenario)
    if int(args.n_agents) > 0:
        config.n_agents = int(args.n_agents)
        config.n_uavs = int(args.n_agents)
        config.max_observed_uavs = max(
            int(args.n_agents),
            int(getattr(config, "max_observed_uavs", args.n_agents)),
        )
    metadata = train_mod.load_checkpoint_metadata(args.checkpoint)
    train_mod.apply_checkpoint_structure(config, internal_args, metadata)

    env = train_mod.create_env(config, config.scenario, int(args.seed), rank=0, scale_mode="eval")
    try:
        _obs, info = env.reset(seed=int(args.seed))
        state_dim = (
            int(np.asarray(info.get("state"), dtype=np.float32).reshape(-1).size)
            if info.get("state") is not None
            else None
        )
        agent = train_mod.create_agent(config, internal_args, env, num_envs=1, state_dim=state_dim)
        train_mod.load_checkpoint(args.checkpoint, agent, load_optimizers=False)
        _set_eval_mode(agent)

        max_labels = int(args.max_labels)
        records: list[R24AuditRecord] = []
        records.extend(
            _audit_kind(
                env,
                agent,
                forced_kind="z",
                labels=_label_values(int(agent.num_team_codes), max_labels),
                horizons=horizons,
                n_resets=int(args.n_resets),
                seed=int(args.seed),
                skill_interval=int(args.skill_interval),
            )
        )
        records.extend(
            _audit_kind(
                env,
                agent,
                forced_kind="xi",
                labels=_label_values(int(agent.n_skills), max_labels),
                horizons=horizons,
                n_resets=int(args.n_resets),
                seed=int(args.seed),
                skill_interval=int(args.skill_interval),
            )
        )
        metrics = summarize_audit_records(records)
        out_dir = Path(args.out_dir)
        write_audit_csv(out_dir / "r24_behavior_audit.csv", metrics)
        return metrics
    finally:
        env.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the R24 offline forced behavior audit.")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--preset", default="S7-S1")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--n_agents", type=int, default=0)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--horizons", default="10,20,50")
    parser.add_argument("--n_resets", type=int, default=16)
    parser.add_argument("--max_labels", type=int, default=6)
    parser.add_argument("--skill_interval", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    metrics = run_r24_behavior_audit(parse_args())
    for key in sorted(metrics):
        print(f"{key}={metrics[key]}")


if __name__ == "__main__":
    main()
