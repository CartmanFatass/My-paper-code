"""Batch-evaluate standalone HA-CTSE process-core checkpoints.

This utility is intentionally separate from training. It loads one checkpoint at
a time, runs deterministic eval, and writes a summary sorted by Scenario 7
service metrics so checkpoint selection is not based on reward alone.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from ha_ctse_process.env_factory import normalize_scenario
from ha_ctse_process.plotting import append_csv, write_csv
from ha_ctse_process.train import (
    apply_checkpoint_structure,
    apply_standalone_overrides,
    create_agent,
    create_env,
    evaluate,
    load_checkpoint,
    load_checkpoint_metadata,
    load_config,
)


SUMMARY_FIELDS = (
    "rank",
    "checkpoint",
    "update_idx",
    "total_steps",
    "service_score",
    "reward_mean",
    "reward_std",
    "length_mean",
    "coverage",
    "qos",
    "throughput",
    "battery_min",
    "checkpoint_path",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate standalone process-core checkpoints.")
    parser.add_argument("--checkpoint_dir", required=True)
    parser.add_argument("--log_dir", required=True)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--preset", default="")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--n_agents", type=int, default=0)
    parser.add_argument("--skill_interval", type=int, default=10)
    parser.add_argument("--skill_lifetime_candidates", default="")
    parser.add_argument("--eval_episodes", type=int, default=10)
    parser.add_argument("--eval_max_steps", type=int, default=1500)
    parser.add_argument("--updates", default="", help="Comma-separated updates, e.g. 20,40,60,80,final.")
    parser.add_argument("--update_stride", type=int, default=10)
    parser.add_argument("--no_final", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def ensure_training_override_defaults(args: argparse.Namespace) -> None:
    defaults = {
        "team_bridge_type": "",
        "opt_compact_dim": 0,
        "opt_num_prototypes": 0,
        "process_reward_coef": None,
        "process_reward_clip": None,
        "process_contrast_coef": None,
        "process_outcome_coef": None,
        "process_reward_contrast_coef": None,
        "process_reward_outcome_coef": None,
        "process_prior_coef": None,
        "high_entropy_coef": None,
        "low_entropy_coef": None,
        "edit_penalty_alpha": None,
        "switch_penalty_beta": None,
        "opt_cd_coef": None,
        "opt_cmi_coef": None,
        "disable_process_reward": False,
        "disable_process_posterior_mi": False,
    }
    for key, value in defaults.items():
        if not hasattr(args, key):
            setattr(args, key, value)


def checkpoint_update(path: Path) -> int | None:
    match = re.search(r"standalone_process_core_update_(\d+)\.pt$", path.name)
    if match:
        return int(match.group(1))
    return None


def parse_update_filter(text: str) -> tuple[set[int], bool] | None:
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


def discover_checkpoints(args: argparse.Namespace) -> list[Path]:
    checkpoint_dir = Path(args.checkpoint_dir)
    update_paths = sorted(
        checkpoint_dir.glob("standalone_process_core_update_*.pt"),
        key=lambda path: checkpoint_update(path) or -1,
    )
    final_path = checkpoint_dir / "standalone_process_core_final.pt"
    selected: list[Path] = []
    update_filter = parse_update_filter(args.updates)
    if update_filter is not None:
        requested, want_final = update_filter
        selected.extend(path for path in update_paths if checkpoint_update(path) in requested)
        if want_final and final_path.exists():
            selected.append(final_path)
    else:
        stride = int(args.update_stride)
        if stride > 0:
            selected.extend(path for path in update_paths if (checkpoint_update(path) or 0) % stride == 0)
        else:
            selected.extend(update_paths)
        if not args.no_final and final_path.exists():
            selected.append(final_path)
    seen = set()
    unique = []
    for path in selected:
        resolved = str(path.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    if not unique:
        raise FileNotFoundError(f"No checkpoints selected from {checkpoint_dir}")
    return unique


def build_agent_for_checkpoint(path: Path, base_args: argparse.Namespace):
    config = load_config(base_args.config, base_args.preset or None)
    config.scenario = normalize_scenario(base_args.scenario)
    apply_standalone_overrides(config, base_args)
    apply_checkpoint_structure(config, base_args, load_checkpoint_metadata(path))

    env = create_env(config, config.scenario, int(base_args.seed), rank=0, scale_mode="eval")
    try:
        _obs, info = env.reset(seed=int(base_args.seed))
        state_dim = (
            int(np.asarray(info.get("state"), dtype=np.float32).reshape(-1).size)
            if info.get("state") is not None
            else None
        )
        agent = create_agent(config, base_args, env, num_envs=1, state_dim=state_dim)
    finally:
        env.close()
    total_steps, update_idx = load_checkpoint(path, agent, load_optimizers=False)
    return config, agent, total_steps, update_idx


def service_score(metrics: dict[str, float]) -> float:
    coverage = float(metrics.get("coverage", 0.0))
    qos = float(metrics.get("qos", 0.0))
    throughput = float(metrics.get("throughput", 0.0))
    battery_min = float(metrics.get("battery_min", 0.0))
    return coverage + qos + throughput / 100.0 + 0.1 * battery_min


def main() -> None:
    args = parse_args()
    ensure_training_override_defaults(args)
    log_dir = Path(args.log_dir)
    if args.overwrite and log_dir.exists():
        for path in (
            log_dir / "standalone_train.log",
            log_dir / "metrics" / "eval_episodes.csv",
            log_dir / "metrics" / "checkpoint_eval_summary.csv",
            log_dir / "metrics" / "checkpoint_eval_raw.csv",
        ):
            if path.exists():
                path.unlink()
    log_dir.mkdir(parents=True, exist_ok=True)

    checkpoints = discover_checkpoints(args)
    rows: list[dict[str, Any]] = []
    for path in checkpoints:
        eval_args = SimpleNamespace(**vars(args))
        eval_args.log_dir = str(log_dir)
        eval_args.resume_from = str(path)
        eval_args.eval_checkpoint_name = path.name
        config, agent, total_steps, update_idx = build_agent_for_checkpoint(path, eval_args)
        metrics = evaluate(
            agent,
            config,
            eval_args,
            episodes=int(args.eval_episodes),
            total_steps=total_steps,
        )
        row = {
            "checkpoint": path.name,
            "update_idx": int(update_idx),
            "total_steps": int(total_steps),
            "service_score": service_score(metrics),
            "reward_mean": float(metrics.get("reward_mean", 0.0)),
            "reward_std": float(metrics.get("reward_std", 0.0)),
            "length_mean": float(metrics.get("length_mean", 0.0)),
            "coverage": float(metrics.get("coverage", 0.0)),
            "qos": float(metrics.get("qos", 0.0)),
            "throughput": float(metrics.get("throughput", 0.0)),
            "battery_min": float(metrics.get("battery_min", 0.0)),
            "checkpoint_path": str(path),
        }
        rows.append(row)
        append_csv(log_dir / "metrics" / "checkpoint_eval_raw.csv", row, SUMMARY_FIELDS[1:])

    ranked = sorted(rows, key=lambda item: item["service_score"], reverse=True)
    for rank, row in enumerate(ranked, start=1):
        row["rank"] = rank
    write_csv(log_dir / "metrics" / "checkpoint_eval_summary.csv", ranked, SUMMARY_FIELDS)
    if ranked:
        best = ranked[0]
        print(
            "best_checkpoint "
            f"rank=1 checkpoint={best['checkpoint']} "
            f"score={best['service_score']:.6f} "
            f"reward={best['reward_mean']:.6f} "
            f"coverage={best['coverage']:.6f} "
            f"qos={best['qos']:.6f} "
            f"throughput={best['throughput']:.6f}"
        )


if __name__ == "__main__":
    main()
