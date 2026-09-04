"""Exact all-seed CCIC-B1 revision-06 production runner."""

from __future__ import annotations

import argparse
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

# Each of the at most eight seed workers gets one numerical-kernel thread, so
# the process remains inside the frozen eight-thread ceiling.
for _thread_variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_thread_variable] = "1"

import numpy as np

from .certificate import build_preactivity_certificate
from .checks import (
    activity_panel,
    calibration_panel,
    collision_fixtures,
    exact_copy_check,
    scaling_projection,
    work_replay_projection,
)
from .config import (
    COARSE_GRID,
    FINE_GRID,
    MASTER_SEED_BASE,
    MASTER_SEED_STEP,
    REVISION,
    SEED_BLOCKS,
    ExperimentConfig,
)
from .evaluation import evaluate_seed
from .inference import inference_families
from .io_utils import atomic_replace, fsync_directory, write_json_atomic
from .reference import NumericalReference
from .resources import ResourceBudgetExceeded, ResourceMonitor
from .training import train_seed
from .work_replay import offline_work_replay


def _run_seed(block: int, fine: NumericalReference, output_root: Path, on_activity_start, resource_check) -> dict:
    seed = MASTER_SEED_BASE + MASTER_SEED_STEP * block
    staging_directory = output_root / ".seed_staging" / f"seed_{block:02d}"
    staging_directory.mkdir(parents=True, exist_ok=False)
    trained = train_seed(seed, fine, on_activity_start=on_activity_start, resource_check=resource_check)
    cells, copy_records = evaluate_seed(trained, fine, resource_check=resource_check)
    calibration = calibration_panel(trained, resource_check=resource_check)
    activity = activity_panel(trained, fine, resource_check=resource_check)
    collision = collision_fixtures()
    exact_copy = exact_copy_check(copy_records)
    work_replay = offline_work_replay(block, trained, staging_directory, resource_check=resource_check)
    if not work_replay["passed"]:
        raise RuntimeError(f"seed {block} functional offline work replay failed")
    return {
        "complete": True,
        "block": block,
        "seed": seed,
        "training": trained.state(),
        "cells": cells,
        "calibration": calibration,
        "activity": activity,
        "collision": collision,
        "exact_copy": exact_copy,
        "offline_work_replay": work_replay,
    }


def _pooled_gates(seed_results: list[dict]) -> dict:
    calibration_passes = sum(int(result["calibration"]["seed_pass"]) for result in seed_results)
    named_means: dict[str, float] = {}
    for n in (2, 5, 8):
        for regime in ("DUP", "CORR", "IND"):
            key = f"N={n}|rho={regime}"
            for metric in ("E_diag", "E_off", "E_J", "E_q"):
                named_means[f"{key}|{metric}"] = float(
                    np.mean([result["calibration"]["cells"][key][metric] for result in seed_results], dtype=np.float64)
                )
    eligible_counts = {result["activity"]["eligible_count"] for result in seed_results}
    if len(eligible_counts) != 1:
        raise AssertionError("eligible activity set changed across seeds")
    denominator_per_seed = eligible_counts.pop()
    monotone = sum(result["activity"]["monotone_count"] for result in seed_results)
    large_gap = sum(result["activity"]["large_gap_count"] for result in seed_results)
    nonfinite = sum(result["activity"]["nonfinite_count"] for result in seed_results)
    denominator = 32 * denominator_per_seed
    activity_seed_passes = sum(int(result["activity"]["seed_pass"]) for result in seed_results)
    return {
        "calibration": {
            "seed_passes": calibration_passes,
            "required": 29,
            "equal_seed_named_cell_error_means": named_means,
            "passed": calibration_passes >= 29 and all(value <= 0.10 for value in named_means.values()),
        },
        "activity": {
            "seed_passes": activity_seed_passes,
            "required": 29,
            "denominator": denominator,
            "monotone_count": monotone,
            "large_gap_count": large_gap,
            "nonfinite_count": nonfinite,
            "passed": (
                activity_seed_passes >= 29
                and nonfinite == 0
                and monotone / denominator >= 0.80
                and large_gap / denominator >= 0.25
            ),
        },
        "exact_copy": {
            "all_seed_pass": all(result["exact_copy"]["passed"] for result in seed_results),
            "deterministic_four_contrasts": [[0.0, 0.0]] * 4
            if all(result["exact_copy"]["passed"] for result in seed_results)
            else None,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--max-workers", required=True, type=int, choices=range(1, 9))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = ExperimentConfig(max_workers=args.max_workers)
    config.validate()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise FileExistsError(f"fresh output root required; refusing existing path: {output_root}")
    output_root.mkdir(parents=True, exist_ok=False)
    (output_root / ".seed_staging").mkdir(exist_ok=False)
    (output_root / "seed_blocks").mkdir(exist_ok=False)
    monitor = ResourceMonitor()
    write_json_atomic(output_root / "config.json", config.machine_record())

    fine = NumericalReference(FINE_GRID, resource_check=monitor.check)
    coarse = NumericalReference(COARSE_GRID, resource_check=monitor.check)
    try:
        certificate = build_preactivity_certificate(fine, coarse)
        monitor.check()
    except ResourceBudgetExceeded as error:
        write_json_atomic(output_root / "terminal.json", {
            "revision": REVISION,
            "scientific_activity_started": False,
            "reason": "resource_ceiling_exceeded",
            "error": str(error),
            "resource": {"peak_process_rss_bytes": monitor.peak_rss_bytes},
        })
        return 4
    write_json_atomic(output_root / "preactivity_certificate.json", certificate)
    if not certificate["passed"]:
        write_json_atomic(
            output_root / "terminal.json",
            {"revision": REVISION, "scientific_activity_started": False, "reason": "preactivity_certificate_failed"},
        )
        return 2

    activity_lock = threading.Lock()
    activity_started = threading.Event()

    def record_activity_start() -> None:
        with activity_lock:
            if activity_started.is_set():
                return
            write_json_atomic(
                output_root / "activity_start.json",
                {
                    "revision": REVISION,
                    "scientific_activity_started": True,
                    "criterion": "first optimizer update using frozen generated training data",
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                },
            )
            activity_started.set()

    seed_results: list[dict | None] = [None] * SEED_BLOCKS
    failures: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [
            executor.submit(_run_seed, block, fine, output_root, record_activity_start, monitor.check)
            for block in range(SEED_BLOCKS)
        ]
        # Consume and atomically retain only complete blocks in fixed block
        # order. A partial worker result has no retained seed artifact and is
        # never eligible for any inference input.
        for block, future in enumerate(futures):
            try:
                result = future.result()
            except Exception as error:
                failures.append({"block": block, "seed": MASTER_SEED_BASE + MASTER_SEED_STEP * block, "error": repr(error)})
            else:
                if result.get("complete") is not True or result.get("block") != block:
                    failures.append({"block": block, "seed": MASTER_SEED_BASE + MASTER_SEED_STEP * block, "error": "incomplete_seed_block"})
                    continue
                try:
                    staging_directory = output_root / ".seed_staging" / f"seed_{block:02d}"
                    retained_directory = output_root / "seed_blocks" / f"seed_{block:02d}"
                    write_json_atomic(staging_directory / "result.json", result)
                    fsync_directory(staging_directory)
                    atomic_replace(staging_directory, retained_directory)
                    fsync_directory(retained_directory.parent)
                except Exception as error:
                    failures.append({"block": block, "seed": MASTER_SEED_BASE + MASTER_SEED_STEP * block, "error": f"retention_failure:{error!r}"})
                else:
                    seed_results[block] = result
    if failures or any(result is None for result in seed_results):
        write_json_atomic(
            output_root / "terminal.json",
            {
                "revision": REVISION,
                "scientific_activity_started": activity_started.is_set(),
                "complete_seed_blocks": sum(result is not None for result in seed_results),
                "seed_substitution": False,
                "failures": failures,
                "efficacy_inference_available": False,
                "partial_blocks_excluded_from_inference": True,
            },
        )
        return 3

    complete = [result for result in seed_results if result is not None]
    if [result["block"] for result in complete] != list(range(SEED_BLOCKS)):
        raise AssertionError("inference requires complete retained blocks 0..31 in fixed order")
    try:
        summary = {
            "revision": REVISION,
            "complete_seed_blocks": 32,
            "seed_substitution": False,
            "pooled_gates": _pooled_gates(complete),
            "work_replay": work_replay_projection(),
            "functional_offline_work_replay": {
                "seed_blocks": 32,
                "total_tuple_count": sum(result["offline_work_replay"]["total_tuple_count"] for result in complete),
                "expected_total_tuple_count": 32 * 256 * 3 * 3 * sum(len(range(0, 30, k)) for k in (1, 3, 5)),
                "all_seed_manifests_passed": all(result["offline_work_replay"]["passed"] for result in complete),
                "retained_artifacts": "seed_blocks/seed_XX/work_replay/{manifest.json,27 lossless .npy tuple chunks}",
            },
            "scaling_projection": scaling_projection(),
            "inference": inference_families([result["cells"] for result in complete], resource_check=monitor.check),
            "resource": monitor.record(),
            "technical_interpretation_performed": False,
            "partial_blocks_excluded_from_inference": True,
            "answerability_paths": {
                "reference_headroom": "reported_fail_closed",
                "covariance_calibration": "reported_all_rosters",
                "actor_activity": "reported_fixed_E",
                "clock_interventions": "reported_shared_actor",
                "RI_STRONG_v2": "trained_and_deployed_functionally",
                "useful_work": "all_27_cells_required",
            },
        }
        write_json_atomic(output_root / "summary.json", summary)
        write_json_atomic(
            output_root / "terminal.json",
            {
                "revision": REVISION,
                "scientific_activity_started": activity_started.is_set(),
                "complete_seed_blocks": 32,
                "seed_substitution": False,
                "efficacy_inference_available": True,
            },
        )
    except Exception as error:
        write_json_atomic(
            output_root / "terminal.json",
            {
                "revision": REVISION,
                "scientific_activity_started": activity_started.is_set(),
                "complete_seed_blocks": 32,
                "seed_substitution": False,
                "efficacy_inference_available": False,
                "reason": "inference_or_finalization_failure",
                "error": repr(error),
                "peak_process_rss_bytes": monitor.peak_rss_bytes,
            },
        )
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
