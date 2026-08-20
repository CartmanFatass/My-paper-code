#!/usr/bin/env python3
"""Aggregate HMASD paper experiment CSV files into tables and figures."""

import argparse
import os
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DEFAULT_METRICS = [
    "reward",
    "coverage_ratio_final",
    "effective_connected_users_final",
    "system_throughput_mbps_final",
    "load_balance_score_final",
    "demand_satisfaction_ratio_final",
    "relay_route_loss_ratio_final",
    "backhaul_outage_ratio_final",
    "avg_hops_final",
]


def _read_episode_files(root):
    files = sorted(Path(root).rglob("paper_eval_episodes_step_*.csv"))
    frames = []
    for path in files:
        df = pd.read_csv(path)
        df["source_file"] = str(path)
        if "seed" not in df.columns:
            seed = _infer_seed(path)
            df["seed"] = seed
        if "run_seed" not in df.columns:
            inferred = _infer_seed(path)
            # Explicit legacy migration: historical paper rows used ``seed``
            # for the trained run.  New rows keep evaluation-block ``seed``
            # separate from ``run_seed``.
            df["run_seed"] = inferred if inferred != "" else df["seed"]
        if "eval_step" not in df.columns:
            match = re.search(r"paper_eval_episodes_step_(\d+)\.csv$", path.name)
            if match is None:
                raise ValueError(f"cannot infer eval_step from {path}")
            df["eval_step"] = int(match.group(1))
        if "checkpoint" not in df.columns:
            df["checkpoint"] = f"step_{int(df['eval_step'].iloc[0])}"
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _infer_seed(path):
    for part in Path(path).parts:
        if part.startswith("seed_"):
            try:
                return int(part.split("_", 1)[1])
            except ValueError:
                return part
    return ""


def _require_episode_identity(df, group_cols):
    required = [*group_cols, "checkpoint", "eval_step", "run_seed", "seed"]
    episode_col = "episode_id" if "episode_id" in df.columns else "episode" if "episode" in df.columns else None
    if episode_col is None:
        raise ValueError("paper episode rows require episode or episode_id")
    required.append(episode_col)
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"paper episode rows are missing identifiers: {missing}")
    nulls = [col for col in required if df[col].isna().any() or (df[col].astype(str) == "").any()]
    if nulls:
        raise ValueError(f"paper episode identifiers contain missing values: {nulls}")
    identity = [
        *group_cols,
        "checkpoint",
        "eval_step",
        "run_seed",
        "seed",
        episode_col,
    ]
    duplicates = df.duplicated(identity, keep=False)
    if duplicates.any():
        sample = df.loc[duplicates, identity].head(3).to_dict("records")
        raise ValueError(f"duplicate paper episode identities: {sample}")
    return episode_col


def _summarize_per_seed(df, group_cols, metrics):
    rows = []
    seed_group_cols = [*group_cols, "checkpoint", "eval_step", "run_seed"]
    for group_key, group in df.groupby(seed_group_cols, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        base = dict(zip(seed_group_cols, group_key))
        for metric in metrics:
            if metric not in group.columns:
                continue
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            if values.empty:
                continue
            std = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            ci95 = 1.96 * std / np.sqrt(len(values)) if len(values) > 1 else 0.0
            rows.append({
                **base,
                "metric": metric,
                "episode_count": int(len(values)),
                "mean": float(values.mean()),
                "std": std,
                "min": float(values.min()),
                "max": float(values.max()),
                "ci95": float(ci95),
            })
    return pd.DataFrame(rows)


def _summarize(df, group_cols, metrics):
    """Compute confidence intervals over seed means, never episode rows."""

    _require_episode_identity(df, group_cols)
    per_seed = _summarize_per_seed(df, group_cols, metrics)
    rows = []
    aggregate_cols = [*group_cols, "checkpoint", "eval_step", "metric"]
    for group_key, group in per_seed.groupby(aggregate_cols, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        means = group["mean"].to_numpy(dtype=float)
        counts = group["episode_count"].to_numpy(dtype=int)
        std = float(np.std(means, ddof=1)) if len(means) > 1 else 0.0
        ci95 = 1.96 * std / np.sqrt(len(means)) if len(means) > 1 else 0.0
        rows.append(
            {
                **dict(zip(aggregate_cols, group_key)),
                "count": int(len(means)),
                "n_seeds": int(len(means)),
                "episode_count": int(np.sum(counts)),
                "episodes_per_seed_min": int(np.min(counts)),
                "episodes_per_seed_max": int(np.max(counts)),
                "mean": float(np.mean(means)),
                "std": std,
                "min": float(np.min(means)),
                "max": float(np.max(means)),
                "ci95": float(ci95),
            }
        )
    return pd.DataFrame(rows)


def _plot_metric_bars(summary, output_dir, metrics):
    if summary.empty:
        return
    label_col = "scenario_label" if "scenario_label" in summary.columns else "preset"
    if label_col not in summary.columns:
        return

    for metric in metrics:
        metric_df = summary[summary["metric"] == metric].copy()
        if metric_df.empty:
            continue
        metric_df = metric_df.sort_values(label_col)
        labels = [
            f"{row[label_col]} | {row['checkpoint']} @ {row['eval_step']}"
            for _, row in metric_df.iterrows()
        ]
        means = metric_df["mean"].to_numpy(dtype=float)
        errors = metric_df["ci95"].to_numpy(dtype=float)

        plt.figure(figsize=(max(7, len(labels) * 1.1), 4.5))
        bars = plt.bar(labels, means, yerr=errors, capsize=4)
        plt.title(metric.replace("_", " ").title())
        plt.ylabel("Mean +/- 95% CI")
        plt.xticks(rotation=30, ha="right")
        plt.grid(axis="y", alpha=0.25)
        for bar, mean in zip(bars, means):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{mean:.3g}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        plt.tight_layout()
        out = Path(output_dir) / f"{metric}_comparison.png"
        plt.savefig(out, dpi=200, bbox_inches="tight")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description="Aggregate HMASD paper experiment results.")
    parser.add_argument("--root", default="../tf-logs", help="Root directory containing experiment logs.")
    parser.add_argument("--output", default="paper_results", help="Output directory for summary tables and figures.")
    parser.add_argument("--metrics", nargs="*", default=DEFAULT_METRICS, help="Metrics to summarize and plot.")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    episodes = _read_episode_files(args.root)
    if episodes.empty:
        raise SystemExit(f"No paper_eval_episodes_step_*.csv files found under {args.root}")

    episodes_path = Path(args.output) / "paper_eval_episodes_all.csv"
    episodes.to_csv(episodes_path, index=False)

    group_cols = [col for col in ["preset", "scenario_label"] if col in episodes.columns]
    if not group_cols:
        raise ValueError("paper episode rows require preset or scenario_label")
    _require_episode_identity(episodes, group_cols)
    per_seed_summary = _summarize_per_seed(episodes, group_cols, args.metrics)
    per_seed_summary.to_csv(Path(args.output) / "paper_eval_summary_by_seed.csv", index=False)

    overall_summary = _summarize(episodes, group_cols, args.metrics)
    overall_summary.to_csv(Path(args.output) / "paper_eval_summary_overall.csv", index=False)

    _plot_metric_bars(overall_summary, args.output, args.metrics)

    print(f"Loaded {len(episodes)} episode rows from {args.root}")
    print(f"Wrote summaries and figures to {args.output}")


if __name__ == "__main__":
    main()
