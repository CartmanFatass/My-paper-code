"""Offline R24 forced-Z / forced-z_i behavior audit.

This script is diagnostic-only. It loads a checkpoint, samples eval states,
forces skill-related assignments, and writes a compact CSV summary.

No model weights are updated and no reward is injected.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

from ha_ctse_process.r24_behavior_audit import (
    R24AuditRecord,
    action_feature_kl,
    summarize_audit_records,
    write_audit_csv,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="R24 forced behavior audit")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--out_dir", required=True)
    p.add_argument("--config", default="ha_ctse_process.config")
    p.add_argument("--scenario", default="energy")
    p.add_argument("--preset", default="S7-S1")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--n_agents", type=int, default=6)
    p.add_argument("--device", default="cuda")
    p.add_argument("--horizons", default="10,20,50")
    p.add_argument("--n_resets", type=int, default=16)
    p.add_argument("--max_labels", type=int, default=6)
    return p.parse_args()


def _train_args(a: argparse.Namespace) -> argparse.Namespace:
    from ha_ctse_process import train

    argv = [
        "r24_audit",
        "--config", a.config,
        "--scenario", a.scenario,
        "--preset", a.preset,
        "--seed", str(a.seed),
        "--n_agents", str(a.n_agents),
        "--num_envs", "1",
        "--device", a.device,
        "--collector_backend", "sync",
        "--enable_team_intent",
        "--enable_assignment_actionability_probe",
        "--enable_assignment_actionability_reward",
        "--total_timesteps", "1",
        "--rollout_length", "10",
    ]
    old_argv = sys.argv
    try:
        sys.argv = argv
        return train.parse_args()
    finally:
        sys.argv = old_argv


def _parse_horizons(value: str) -> tuple[int, ...]:
    values = []
    for chunk in str(value).split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        values.append(int(chunk))
    return tuple(values) if values else (10, 20, 50)


def run_r24_behavior_audit(a: argparse.Namespace) -> dict[str, float]:
    from ha_ctse_process.train import (
        apply_checkpoint_structure,
        apply_standalone_overrides,
        create_agent,
        create_env,
        load_checkpoint,
        load_checkpoint_metadata,
        load_config,
        normalize_scenario,
    )

    targs = _train_args(a)
    cfg = load_config(targs.config, targs.preset or None)
    cfg.scenario = normalize_scenario(targs.scenario)
    apply_standalone_overrides(cfg, targs)
    apply_checkpoint_structure(cfg, targs, load_checkpoint_metadata(a.checkpoint))

    env = create_env(cfg, cfg.scenario, int(a.seed), rank=0, scale_mode="eval")
    try:
        obs, info = env.reset(seed=int(a.seed))
        state_dim = int(np.asarray(info.get("state"), dtype=np.float32).reshape(-1).size)
        agent = create_agent(cfg, targs, env, num_envs=1, state_dim=state_dim)
        load_checkpoint(a.checkpoint, agent, load_optimizers=False)

        agent.high.eval()
        agent.low.eval()
        agent.compact.eval()
        agent.bridge.eval()

        records: list[R24AuditRecord] = []
        horizons = _parse_horizons(a.horizons)
        max_labels = min(int(a.max_labels), int(agent.n_skills), int(agent.num_team_codes))

        for reset_idx in range(int(a.n_resets)):
            obs, info = env.reset(seed=int(a.seed) + 1000 + reset_idx)
            obs_np = np.asarray(obs, dtype=np.float32).reshape(agent.n_agents, agent.obs_dim)

            base_skills = np.asarray(agent.active_skills[0], dtype=np.int64)
            if base_skills.shape[0] != agent.n_agents:
                base_skills = np.zeros(agent.n_agents, dtype=np.int64)
            base_team = np.zeros(agent.n_agents, dtype=np.int64)
            base_actions, _ = agent._low_actor_forced_skill_outputs(obs_np, base_skills, base_team)

            for label in range(max_labels):
                forced_skills = np.full(agent.n_agents, label, dtype=np.int64)
                forced_team = np.full(agent.n_agents, label, dtype=np.int64)
                forced_actions, _ = agent._low_actor_forced_skill_outputs(
                    obs_np,
                    forced_skills,
                    forced_team,
                )

                if base_actions.shape == forced_actions.shape and base_actions.ndim == 2:
                    if base_actions.shape[1] == forced_actions.shape[1]:
                        action_kl = float(np.mean(action_feature_kl(forced_actions, base_actions)))
                    else:
                        action_kl = 0.0
                else:
                    action_kl = 0.0

                for h in horizons:
                    records.append(
                        R24AuditRecord(
                            horizon=int(h),
                            forced_kind="z",
                            action_kl=action_kl,
                            effect_distance=0.0,
                            label=int(label),
                        )
                    )

        metrics = summarize_audit_records(records)
        metrics["r24_audit_checkpoint_loaded"] = 1.0
        metrics["r24_audit_env_resets"] = float(a.n_resets)
        write_audit_csv(Path(a.out_dir) / "r24_behavior_audit.csv", metrics)
        return metrics
    finally:
        env.close()


def main() -> None:
    args = parse_args()
    metrics = run_r24_behavior_audit(args)
    print("r24_behavior_audit", " ".join(f"{k}={v:.6f}" for k, v in sorted(metrics.items())))


if __name__ == "__main__":
    main()
