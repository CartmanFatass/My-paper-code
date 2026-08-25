#!/usr/bin/env python3
"""Fixed-workload equivalence and median gates for analysis I/O optimizations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import statistics
import sys
import tempfile
import time

import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ha_ctse_process.metrics_io import append_csv
from ha_ctse_process import plotting
from ha_ctse_process import uav_g0_statistics as g0


def _reference_g0_plan() -> np.ndarray:
    return np.random.Generator(np.random.PCG64(g0.BOOTSTRAP_SEED)).integers(
        0,
        len(g0.EPISODE_IDS),
        size=(g0.BOOTSTRAP_RESAMPLES, len(g0.EPISODE_IDS)),
        dtype=np.int64,
    )


def _source_fingerprint() -> str:
    digest = hashlib.sha256()
    for relative in (
        "ha_ctse_process/metrics_io.py",
        "ha_ctse_process/plotting.py",
        "ha_ctse_process/uav_g0_statistics.py",
        "tools/benchmarks/benchmark_analysis_io.py",
    ):
        digest.update(relative.encode("utf-8"))
        digest.update((REPOSITORY_ROOT / relative).read_bytes())
    return digest.hexdigest()


def _timed(callable_):
    start = time.perf_counter_ns()
    value = callable_()
    return value, (time.perf_counter_ns() - start) / 1_000_000_000.0


def _interleaved(reference, optimized, repeats: int):
    timings = {"reference": [], "optimized": []}
    for index in range(repeats):
        order = (("reference", reference), ("optimized", optimized))
        if index % 2:
            order = tuple(reversed(order))
        for name, callable_ in order:
            _, seconds = _timed(callable_)
            timings[name].append(seconds)
    return timings


def _append_eval_group(
    csv_path: Path, *, group_index: int, episodes: int, run_seed: int
) -> None:
    fields = (
        "checkpoint",
        "total_steps",
        "eval_step",
        "run_seed",
        "seed",
        "episode",
        "reward",
    )
    for episode in range(episodes):
        append_csv(
            csv_path,
            {
                "checkpoint": f"checkpoint-{group_index}.pt",
                "total_steps": group_index * 1_000,
                "eval_step": group_index * 1_000,
                "run_seed": run_seed,
                "seed": 10_000 + group_index,
                "episode": episode,
                "reward": float((group_index + episode) % 17) / 17.0,
            },
            fields,
        )


def run_benchmark(
    *, episodes_per_group: int = 8, repeats: int = 31, run_seed: int = 20_260_815
) -> dict[str, object]:
    if episodes_per_group <= 0 or repeats < 31 or repeats % 2 == 0:
        raise ValueError(
            "episodes_per_group must be positive and repeats must be an odd value >= 31"
        )
    if isinstance(run_seed, bool) or not isinstance(run_seed, int) or run_seed < 0:
        raise ValueError("run_seed must be a nonnegative integer")

    with tempfile.TemporaryDirectory(prefix="hmasd-analysis-io-benchmark-") as temp_dir:
        root = Path(temp_dir)
        reference_root = root / "reference"
        optimized_root = root / "optimized"
        reference_csv = reference_root / "metrics" / "eval_episodes.csv"
        optimized_csv = optimized_root / "metrics" / "eval_episodes.csv"
        _append_eval_group(
            reference_csv,
            group_index=0,
            episodes=episodes_per_group,
            run_seed=run_seed,
        )
        _append_eval_group(
            optimized_csv,
            group_index=0,
            episodes=episodes_per_group,
            run_seed=run_seed,
        )
        plotting._EVAL_RECORD_CACHE.clear()
        plotting._EVAL_RENDER_CACHE.clear()
        plotting.save_eval_plots(reference_root, window=5, mode="reference")
        plotting.save_eval_plots(optimized_root, window=5, mode="optimized")
        plot_timings = {"reference": [], "optimized": []}
        for sample in range(repeats):
            group_index = sample + 1
            _append_eval_group(
                reference_csv,
                group_index=group_index,
                episodes=episodes_per_group,
                run_seed=run_seed,
            )
            _append_eval_group(
                optimized_csv,
                group_index=group_index,
                episodes=episodes_per_group,
                run_seed=run_seed,
            )
            order = (
                ("reference", lambda: plotting.save_eval_plots(reference_root, window=5, mode="reference")),
                ("optimized", lambda: plotting.save_eval_plots(optimized_root, window=5, mode="optimized")),
            )
            if sample % 2:
                order = tuple(reversed(order))
            for name, callable_ in order:
                _, seconds = _timed(callable_)
                plot_timings[name].append(seconds)

        optimized_records = plotting.load_eval_plot_records(optimized_csv, mode="optimized")
        reference_records = plotting.load_eval_plot_records(reference_csv, mode="reference")
        optimized_images = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in optimized_root.glob("eval_*.png")
        }
        reference_images = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in reference_root.glob("eval_*.png")
        }
        plot_equivalent = optimized_records == reference_records and (
            optimized_images == reference_images and bool(reference_images)
        )

    reference_plan = _reference_g0_plan()
    optimized_plan = g0.make_bootstrap_index_plan()
    g0_equivalent = np.array_equal(reference_plan, optimized_plan)
    g0_timings = _interleaved(_reference_g0_plan, g0.make_bootstrap_index_plan, repeats)

    def result(timings, equivalent):
        reference_median = statistics.median(timings["reference"])
        optimized_median = statistics.median(timings["optimized"])
        return {
            "equivalent": bool(equivalent),
            "reference_median_seconds": reference_median,
            "optimized_median_seconds": optimized_median,
            "speedup": reference_median / optimized_median,
            "positive_median_gate": bool(equivalent and optimized_median < reference_median),
            "reference_samples_seconds": timings["reference"],
            "optimized_samples_seconds": timings["optimized"],
        }

    plotting_result = result(plot_timings, plot_equivalent)
    plotting_result.update(
        {
            "final_record_equivalent": optimized_records == reference_records,
            "final_png_digest_equivalent": optimized_images == reference_images,
            "final_png_count": len(reference_images),
        }
    )
    return {
        "schema_version": 1,
        "machine": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "commit": os.environ.get("HMASD_COMMIT", "UNSPECIFIED"),
        "source_sha256": _source_fingerprint(),
        "config": {
            "episodes_per_group": episodes_per_group,
            "run_seed": run_seed,
            "complete_eval_groups_per_mode": repeats + 1,
            "repeats": repeats,
            "interleaved": True,
            "warm_cache": True,
            "plot_gate": (
                "independent_files_append_one_complete_eval_group_before_each_"
                "save_eval_plots_sample_plus_final_record_and_png_digest_equivalence"
            ),
        },
        "plotting": plotting_result,
        "g0_bootstrap_plan": result(g0_timings, g0_equivalent),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes-per-group", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=31)
    parser.add_argument("--run-seed", type=int, default=20_260_815)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_benchmark(
        episodes_per_group=args.episodes_per_group,
        repeats=args.repeats,
        run_seed=args.run_seed,
    )
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if all(
        result[name]["positive_median_gate"] for name in ("plotting", "g0_bootstrap_plan")
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
