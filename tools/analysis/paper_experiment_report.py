#!/usr/bin/env python3
"""Aggregate HMASD paper experiment CSV files into tables and figures."""

import argparse
import os
from pathlib import Path

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


def _summarize(df, group_cols, metrics):
    rows = []
    for group_key, group in df.groupby(group_cols, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        base = dict(zip(group_cols, group_key))
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
                "count": int(len(values)),
                "mean": float(values.mean()),
                "std": std,
                "min": float(values.min()),
                "max": float(values.max()),
                "ci95": float(ci95),
            })
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
        labels = metric_df[label_col].astype(str).tolist()
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

    group_cols = [col for col in ["preset", "scenario_label", "seed"] if col in episodes.columns]
    per_seed_summary = _summarize(episodes, group_cols, args.metrics)
    per_seed_summary.to_csv(Path(args.output) / "paper_eval_summary_by_seed.csv", index=False)

    group_cols_no_seed = [col for col in ["preset", "scenario_label"] if col in episodes.columns]
    overall_summary = _summarize(episodes, group_cols_no_seed, args.metrics)
    overall_summary.to_csv(Path(args.output) / "paper_eval_summary_overall.csv", index=False)

    _plot_metric_bars(overall_summary, args.output, args.metrics)

    print(f"Loaded {len(episodes)} episode rows from {args.root}")
    print(f"Wrote summaries and figures to {args.output}")


if __name__ == "__main__":
    main()
