"""Evaluate the R29 on-policy counterfactual action-information target."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.low_actor_capacity_audit import (  # noqa: E402
    cluster_bootstrap_difference,
    forward_actor_snapshot,
    read_capacity_snapshot_shards,
)
from ha_ctse_process.r27_g2_runtime import (  # noqa: E402
    R27G2ContractError,
    configure_deterministic_cuda,
)
from ha_ctse_process.r29_action_information import (  # noqa: E402
    ACTIVE_MEAN_MIN,
    EXPERIMENT_ID,
    INACTIVE_ABS_MAX,
    LABEL_ENTROPY_MIN,
    MIN_RESETS,
    MIN_ROWS,
    PER_SKILL_MEAN_MIN,
    SCHEMA,
    classify_checkpoint,
    classify_family,
    evaluate_action_information,
    normalized_label_entropy,
)
from scripts.audit_r27_forced_trajectory_effect import (  # noqa: E402
    CHECKPOINT_IDS,
    REGISTERED_CHECKPOINTS,
    _configure_agent,
    _path_matches_registered,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _validate_source(args: argparse.Namespace) -> dict[str, Any]:
    registered = REGISTERED_CHECKPOINTS[str(args.checkpoint_id)]
    if str(args.device).lower() != "cuda":
        raise ValueError("R29 target calibration requires CUDA")
    if not _path_matches_registered(args.checkpoint, registered["path"]):
        raise ValueError("checkpoint path does not match the registered R25 source")
    if int(args.checkpoint_update) != int(registered["update"]):
        raise ValueError("checkpoint update does not match the registered R25 source")
    if not Path(args.checkpoint).is_file():
        raise FileNotFoundError(args.checkpoint)
    if not Path(args.snapshot_dir).is_dir():
        raise FileNotFoundError(args.snapshot_dir)
    if int(args.mc_samples) <= 0 or int(args.bootstrap_reps) <= 0:
        raise ValueError("Monte Carlo samples and bootstrap reps must be positive")
    return registered


def _all_skill_parameters(
    actor: Any,
    observations: np.ndarray,
    hidden: np.ndarray,
    *,
    inactive_film: bool,
    batch_size: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    means: list[torch.Tensor] = []
    log_stds: list[torch.Tensor] = []
    rows = int(observations.shape[0])
    for start in range(0, rows, int(batch_size)):
        stop = min(rows, start + int(batch_size))
        batch_means: list[torch.Tensor] = []
        batch_log_stds: list[torch.Tensor] = []
        for skill in range(int(actor.n_skills)):
            output = forward_actor_snapshot(
                actor,
                torch.as_tensor(observations[start:stop], device=actor.device),
                torch.full(
                    (stop - start,), skill, dtype=torch.long, device=actor.device
                ),
                torch.as_tensor(hidden[start:stop], device=actor.device),
                inactive_film=inactive_film,
            )
            batch_means.append(output.action_mean.cpu())
            batch_log_stds.append(output.action_logstd.cpu())
        means.append(torch.stack(batch_means, dim=1))
        log_stds.append(torch.stack(batch_log_stds, dim=1))
    return torch.cat(means, dim=0), torch.cat(log_stds, dim=0)


def _markdown(report: dict[str, Any]) -> str:
    interval = report["active_minus_sham_bootstrap"]
    return "\n".join(
        [
            f"# R29 Action Information: {report['checkpoint_id']}",
            "",
            f"- Status: `{report['status']}`",
            f"- Rows / resets: `{report['rows']} / {report['resets']}`",
            f"- Active reward mean: `{report['active_reward_mean']:.6f}` nats",
            f"- Minimum per-skill mean: `{report['minimum_skill_mean']:.6f}` nats",
            f"- Sham reward mean: `{report['sham_reward_mean']:.6f}` nats",
            f"- Active-minus-sham bootstrap 95% CI: "
            f"`[{interval['lower']:.6f}, {interval['upper']:.6f}]`",
            f"- Inactive maximum absolute reward: `{report['inactive_max_abs']:.3e}`",
            f"- Normalized natural-label entropy: `{report['label_entropy']:.6f}`",
            "",
        ]
    )


def run_checkpoint(args: argparse.Namespace) -> dict[str, Any]:
    registered = _validate_source(args)
    configure_deterministic_cuda(args.device)
    args.reset_id = 0
    (
        _config,
        _metadata,
        agent,
        _env_factory,
        total_steps,
        loaded_update,
        value_norm_equal,
    ) = _configure_agent(args)
    if (
        int(total_steps) != int(registered["total_steps"])
        or int(loaded_update) != int(registered["update"])
        or not bool(value_norm_equal)
    ):
        raise R27G2ContractError("R29 source checkpoint state mismatch")

    snapshots = read_capacity_snapshot_shards(Path(args.snapshot_dir))
    checkpoint_ids = set(np.asarray(snapshots.checkpoint_id, dtype=np.str_).tolist())
    checkpoint_updates = set(
        np.asarray(snapshots.checkpoint_update, dtype=np.int64).tolist()
    )
    if checkpoint_ids != {str(args.checkpoint_id)} or checkpoint_updates != {
        int(args.checkpoint_update)
    }:
        raise R27G2ContractError("R29 snapshot source identity mismatch")
    rows = int(snapshots.natural_skill.size)
    resets = int(np.unique(snapshots.reset_id).size)
    label_entropy = normalized_label_entropy(
        snapshots.natural_skill, int(agent.low.n_skills)
    )

    active_mean, active_log_std = _all_skill_parameters(
        agent.low,
        snapshots.observation,
        snapshots.actor_hidden,
        inactive_film=False,
        batch_size=int(args.batch_size),
    )
    inactive_mean, inactive_log_std = _all_skill_parameters(
        agent.low,
        snapshots.observation,
        snapshots.actor_hidden,
        inactive_film=True,
        batch_size=int(args.batch_size),
    )
    rng = np.random.default_rng(int(args.mc_seed))
    epsilon = torch.from_numpy(
        rng.standard_normal(
            size=(
                int(args.mc_samples),
                rows,
                int(agent.low.n_skills),
                int(agent.low.action_dim),
            )
        ).astype(np.float32)
    )
    active = evaluate_action_information(
        active_mean, active_log_std, epsilon=epsilon
    )
    inactive = evaluate_action_information(
        inactive_mean, inactive_log_std, epsilon=epsilon
    )
    interval = cluster_bootstrap_difference(
        active.active_by_row,
        active.sham_by_row,
        snapshots.reset_id,
        reps=int(args.bootstrap_reps),
        seed=int(args.bootstrap_seed),
    )
    active_flat = np.asarray(active.active_reward, dtype=np.float64).reshape(-1)
    inactive_max_abs = float(
        max(
            np.max(np.abs(inactive.active_reward)),
            np.max(np.abs(inactive.sham_reward)),
        )
    )
    active_by_skill = np.asarray(active.active_by_skill, dtype=np.float64)
    status, reasons = classify_checkpoint(
        rows=rows,
        resets=resets,
        label_entropy=label_entropy,
        active_mean=float(active_flat.mean()),
        minimum_skill_mean=float(active_by_skill.min()),
        active_minus_sham_lower=float(interval.lower),
        inactive_max_abs=inactive_max_abs,
    )
    report: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "schema": SCHEMA,
        "status": status,
        "reasons": reasons,
        "checkpoint_id": str(args.checkpoint_id),
        "checkpoint_update": int(loaded_update),
        "checkpoint_total_steps": int(total_steps),
        "checkpoint_path": str(Path(args.checkpoint)),
        "snapshot_dir": str(Path(args.snapshot_dir)),
        "device": str(args.device),
        "rows": rows,
        "resets": resets,
        "mc_samples": int(args.mc_samples),
        "label_entropy": label_entropy,
        "active_reward_mean": float(active_flat.mean()),
        "active_reward_quantiles": {
            "q01": float(np.quantile(active_flat, 0.01)),
            "q50": float(np.quantile(active_flat, 0.50)),
            "q99": float(np.quantile(active_flat, 0.99)),
        },
        "active_by_skill": active_by_skill.tolist(),
        "minimum_skill_mean": float(active_by_skill.min()),
        "sham_reward_mean": float(np.mean(active.sham_reward)),
        "active_minus_sham_bootstrap": {
            "mean": float(interval.mean),
            "lower": float(interval.lower),
            "upper": float(interval.upper),
        },
        "inactive_max_abs": inactive_max_abs,
        "thresholds": {
            "rows_min": MIN_ROWS,
            "resets_min": MIN_RESETS,
            "label_entropy_min": LABEL_ENTROPY_MIN,
            "active_mean_min": ACTIVE_MEAN_MIN,
            "per_skill_mean_min": PER_SKILL_MEAN_MIN,
            "active_minus_sham_bootstrap_lower": ">0",
            "inactive_abs_max": INACTIVE_ABS_MAX,
        },
        "environment_steps": 0,
        "policy_updates": 0,
        "reward_applied_steps": 0,
    }
    output_dir = Path(args.output_dir)
    json_path = output_dir / "r29_action_information.json"
    markdown_path = output_dir / "r29_action_information.md"
    _write_json(json_path, report)
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    return {**report, "json": str(json_path), "markdown": str(markdown_path)}


def run_aggregate(args: argparse.Namespace) -> dict[str, Any]:
    run_root = Path(args.run_root)
    paths = sorted(run_root.glob("arm0_*/r29_action_information.json"))
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    status, classification, next_action = classify_family(reports)
    aggregate = {
        "experiment_id": EXPERIMENT_ID,
        "schema": SCHEMA,
        "status": status,
        "classification": classification,
        "next_action": next_action,
        "checkpoint_statuses": {
            str(report.get("checkpoint_id")): str(report.get("status"))
            for report in reports
        },
        "reports": reports,
        "environment_steps": 0,
        "policy_updates": 0,
        "reward_applied_steps": 0,
    }
    json_path = run_root / "r29_action_information_aggregate.json"
    markdown_path = run_root / "r29_action_information_aggregate.md"
    _write_json(json_path, aggregate)
    markdown_path.write_text(
        "\n".join(
            [
                "# R29 Counterfactual Action-Information Target",
                "",
                f"- Status: `{status}`",
                f"- Classification: `{classification}`",
                f"- Next action: {next_action}.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {**aggregate, "json": str(json_path), "markdown": str(markdown_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="R29 on-policy counterfactual action-information target"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    checkpoint = subparsers.add_parser("checkpoint")
    checkpoint.add_argument("--checkpoint", required=True)
    checkpoint.add_argument("--checkpoint-id", required=True, choices=CHECKPOINT_IDS)
    checkpoint.add_argument("--checkpoint-update", required=True, type=int)
    checkpoint.add_argument("--snapshot-dir", required=True)
    checkpoint.add_argument("--output-dir", required=True)
    checkpoint.add_argument("--config", default="ha_ctse_process.config")
    checkpoint.add_argument("--scenario", default="energy")
    checkpoint.add_argument("--preset", default="S7-S1")
    checkpoint.add_argument("--n-agents", dest="n_agents", type=int, default=6)
    checkpoint.add_argument("--device", default="cuda")
    checkpoint.add_argument("--mc-samples", type=int, default=8)
    checkpoint.add_argument("--mc-seed", type=int, default=29001)
    checkpoint.add_argument("--bootstrap-reps", type=int, default=2_000)
    checkpoint.add_argument("--bootstrap-seed", type=int, default=29002)
    checkpoint.add_argument("--batch-size", type=int, default=1_024)
    aggregate = subparsers.add_parser("aggregate")
    aggregate.add_argument("--run-root", required=True)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main() -> None:
    args = parse_args()
    result = run_checkpoint(args) if args.command == "checkpoint" else run_aggregate(args)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
