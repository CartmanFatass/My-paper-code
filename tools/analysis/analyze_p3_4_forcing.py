"""Summarize HA-CTSE P3-4 forcing ablation runs.

This script is intentionally offline-only: point it at a downloaded cloud log
root and it reads ``metrics/train_updates.csv`` plus ``metrics/eval_episodes.csv``.
The primary success metric is the fraction of evaluation primitive steps with
``coverage == 1.0``.  If a run predates that field, the script falls back to
episode-level coverage estimates and marks the result as approximate.
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path


KNOWN_ARMS = (
    "force_disc_effect_no_gate",
    "force_effect_only",
    "force_disc_effect",
    "force_disc_only",
    "force_probe",
    "reward_pure",
)

TRAIN_TAIL_KEYS = (
    "force_gate_active",
    "force_reward_applied_steps",
    "force_reward_low_mean",
    "force_disc_acc",
    "force_shortcut_best_acc",
    "force_shortcut_margin",
    "force_disc_residual_mean",
    "force_effect_residual_mean",
    "force_duration_entropy_bonus",
    "duration_usage_entropy",
    "duration_usage_max_frac",
    "skill_usage_entropy",
    "segment_length_mean",
    "credit_full_disconnect_mean",
    "credit_recovery_rate",
    "credit_backhaul_connected_step_fraction",
    "low_approx_kl",
    "low_clip_frac",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def as_float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float]) -> float | None:
    vals = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return sum(vals) / len(vals) if vals else None


def mean_key(rows: list[dict[str, str]], key: str) -> float | None:
    vals = [as_float(row, key) for row in rows]
    return mean([v for v in vals if v is not None])


def std_key(rows: list[dict[str, str]], key: str) -> float | None:
    vals = [as_float(row, key) for row in rows]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


def frac_from_col(rows: list[dict[str, str]], key: str) -> float | None:
    return mean_key(rows, key) if rows and key in rows[0] else None


def infer_arm(name: str) -> str:
    for arm in KNOWN_ARMS:
        if arm in name:
            return arm
    return name


def infer_seed(name: str) -> str:
    marker = "_seed"
    if marker not in name:
        return ""
    rest = name.split(marker, 1)[1]
    digits = []
    for char in rest:
        if char.isdigit():
            digits.append(char)
        else:
            break
    return "".join(digits)


def latest_eval_rows(run_dir: Path) -> tuple[str, list[dict[str, str]]]:
    rows = read_csv(run_dir / "metrics" / "eval_episodes.csv")
    if not rows:
        return "", []
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("total_steps", ""))].append(row)
    latest_step = max(groups, key=lambda item: float(item or 0.0))
    return latest_step, groups[latest_step]


def summarize_eval(rows: list[dict[str, str]]) -> dict[str, float | str]:
    if not rows:
        return {
            "eval_episodes": 0.0,
            "eval_reward": 0.0,
            "eval_reward_std": 0.0,
            "eval_coverage": 0.0,
            "coverage_eq1_step_fraction": 0.0,
            "coverage_eq1_episode_fraction": 0.0,
            "coverage_final_eq1_episode_fraction": 0.0,
            "zero_throughput_episode_fraction": 0.0,
            "zero_throughput_step_fraction": 0.0,
            "throughput_gt5_step_fraction": 0.0,
            "eval_throughput": 0.0,
            "eval_qos": 0.0,
            "eval_metric_source": "missing",
        }

    coverage = mean_key(rows, "coverage_ratio") or 0.0
    throughput = mean_key(rows, "system_throughput_mbps") or 0.0
    reward = mean_key(rows, "reward") or 0.0
    reward_std = std_key(rows, "reward") or 0.0
    qos = mean_key(rows, "qos_satisfaction_ratio") or 0.0

    coverage_eq1_step = frac_from_col(rows, "coverage_eq1_step_fraction")
    coverage_eq1_episode = frac_from_col(rows, "coverage_has_eq1_step_flag")
    coverage_final_eq1_episode = frac_from_col(rows, "coverage_final_eq1_flag")
    zero_throughput_episode = frac_from_col(rows, "zero_throughput_episode_flag")
    zero_throughput_step = frac_from_col(rows, "zero_throughput_step_fraction")
    throughput_gt5_step = frac_from_col(rows, "throughput_gt5_step_fraction")
    metric_source = "step"

    if coverage_eq1_step is None:
        metric_source = "episode_fallback"
        coverage_flags = [1.0 if (as_float(row, "coverage_ratio") or 0.0) >= 0.999 else 0.0 for row in rows]
        coverage_eq1_step = mean(coverage_flags) or 0.0
        coverage_eq1_episode = coverage_eq1_step
        coverage_final_eq1_episode = coverage_eq1_step
    if coverage_eq1_episode is None:
        coverage_eq1_episode = coverage_eq1_step
    if coverage_final_eq1_episode is None:
        coverage_final_eq1_episode = coverage_eq1_step

    if zero_throughput_episode is None:
        thr_zero = [
            1.0 if (as_float(row, "system_throughput_mbps") or 0.0) <= 1e-6 else 0.0
            for row in rows
        ]
        zero_throughput_episode = mean(thr_zero) or 0.0
    if zero_throughput_step is None:
        zero_throughput_step = zero_throughput_episode

    if throughput_gt5_step is None:
        thr_gt5 = [
            1.0 if (as_float(row, "system_throughput_mbps") or 0.0) > 5.0 else 0.0
            for row in rows
        ]
        throughput_gt5_step = mean(thr_gt5) or 0.0

    return {
        "eval_episodes": float(len(rows)),
        "eval_reward": reward,
        "eval_reward_std": reward_std,
        "eval_coverage": coverage,
        "coverage_eq1_step_fraction": coverage_eq1_step,
        "coverage_eq1_episode_fraction": coverage_eq1_episode,
        "coverage_final_eq1_episode_fraction": coverage_final_eq1_episode,
        "zero_throughput_episode_fraction": zero_throughput_episode,
        "zero_throughput_step_fraction": zero_throughput_step,
        "throughput_gt5_step_fraction": throughput_gt5_step,
        "eval_throughput": throughput,
        "eval_qos": qos,
        "eval_metric_source": metric_source,
    }


def summarize_run(run_dir: Path, tail: int, target_coverage_eq1: float) -> dict[str, float | str]:
    train_rows = read_csv(run_dir / "metrics" / "train_updates.csv")
    eval_step, eval_rows = latest_eval_rows(run_dir)
    eval_summary = summarize_eval(eval_rows)
    tail_rows = train_rows[-max(int(tail), 1) :] if train_rows else []
    last = train_rows[-1] if train_rows else {}

    row: dict[str, float | str] = {
        "run": run_dir.name,
        "arm": infer_arm(run_dir.name),
        "seed": infer_seed(run_dir.name),
        "train_steps": as_float(last, "total_steps") or 0.0,
        "eval_steps": eval_step,
        **eval_summary,
    }
    for key in TRAIN_TAIL_KEYS:
        row[f"{key}_tail"] = mean_key(tail_rows, key) or 0.0

    notes = []
    arm = str(row["arm"])
    train_steps = float(row["train_steps"])
    if "force" in arm and arm != "force_probe":
        if train_steps >= 80000 and float(row["force_reward_applied_steps_tail"]) <= 0.0:
            notes.append("NO_FORCE_REWARD")
        if float(row["force_shortcut_best_acc_tail"]) >= float(row["force_disc_acc_tail"]):
            notes.append("SHORTCUT_GE_DISC")
    if float(row["duration_usage_entropy_tail"]) < 0.5:
        notes.append("DURATION_COLLAPSE")
    if float(row["coverage_eq1_step_fraction"]) >= target_coverage_eq1:
        notes.append("COVERAGE_EQ1_TARGET")
    elif float(row["coverage_eq1_step_fraction"]) <= 0.05:
        notes.append("LOW_FULL_COVERAGE")
    if float(row["zero_throughput_episode_fraction"]) >= 0.5:
        notes.append("MANY_ZERO_THR_EP")
    row["notes"] = ",".join(notes) if notes else "OK"
    return row


def fmt(value: float | str, digits: int = 4) -> str:
    if isinstance(value, str):
        return value
    if abs(value) >= 10000:
        return f"{value:.0f}"
    return f"{value:.{digits}f}"


def print_tsv(rows: list[dict[str, float | str]]) -> None:
    columns = (
        "arm",
        "seed",
        "train_steps",
        "eval_steps",
        "eval_episodes",
        "eval_reward",
        "eval_reward_std",
        "eval_coverage",
        "coverage_eq1_step_fraction",
        "coverage_eq1_episode_fraction",
        "zero_throughput_episode_fraction",
        "throughput_gt5_step_fraction",
        "eval_throughput",
        "eval_qos",
        "force_gate_active_tail",
        "force_reward_applied_steps_tail",
        "force_reward_low_mean_tail",
        "force_disc_acc_tail",
        "force_shortcut_best_acc_tail",
        "force_shortcut_margin_tail",
        "force_disc_residual_mean_tail",
        "force_effect_residual_mean_tail",
        "duration_usage_entropy_tail",
        "duration_usage_max_frac_tail",
        "skill_usage_entropy_tail",
        "segment_length_mean_tail",
        "credit_full_disconnect_mean_tail",
        "credit_recovery_rate_tail",
        "low_approx_kl_tail",
        "low_clip_frac_tail",
        "eval_metric_source",
        "notes",
        "run",
    )
    print("\t".join(columns))
    for row in rows:
        print("\t".join(fmt(row.get(col, "")) for col in columns))


def print_markdown(rows: list[dict[str, float | str]]) -> None:
    columns = (
        "arm",
        "seed",
        "train_steps",
        "eval_steps",
        "eval_coverage",
        "coverage_eq1_step_fraction",
        "zero_throughput_episode_fraction",
        "eval_throughput",
        "force_gate_active_tail",
        "force_reward_applied_steps_tail",
        "force_disc_acc_tail",
        "force_shortcut_best_acc_tail",
        "duration_usage_entropy_tail",
        "notes",
    )
    print("| " + " | ".join(columns) + " |")
    print("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        print("| " + " | ".join(fmt(row.get(col, "")) for col in columns) + " |")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize HA-CTSE P3-4 forcing ablation logs.")
    parser.add_argument("--log-root", required=True, help="Directory containing P3-4 run directories.")
    parser.add_argument("--tail", type=int, default=10, help="Number of train updates for tail means.")
    parser.add_argument("--target-coverage-eq1", type=float, default=0.5)
    parser.add_argument("--format", choices=("tsv", "markdown"), default="tsv")
    args = parser.parse_args()

    root = Path(args.log_root)
    csv_paths = sorted(root.glob("**/metrics/train_updates.csv"))
    if not csv_paths:
        print(f"No train_updates.csv found under {root}")
        return 1
    rows = [
        summarize_run(path.parents[1], tail=int(args.tail), target_coverage_eq1=float(args.target_coverage_eq1))
        for path in csv_paths
    ]
    rows.sort(key=lambda item: (str(item["arm"]), str(item["seed"]), float(item["train_steps"])))
    if args.format == "markdown":
        print_markdown(rows)
    else:
        print_tsv(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
