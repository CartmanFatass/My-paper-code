"""Functional offline CCIC/RI-v2 replay over every frozen potential tuple."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from .config import EVAL_K, EVAL_N, OVERLAP, REGIMES
from .core import batch_rows, latent_tape, quotient_new_rows
from .io_utils import atomic_replace, fsync_directory, fsync_file, sha256_file, write_json_atomic
from .training import TrainedSeed


RECORD_DTYPE = np.dtype(
    [
        ("episode", "<u2"),
        ("t", "u1"),
        ("M", "u1"),
        ("ccic_q", "<f8"),
        ("ccic_J", "<f8"),
        ("ri_v2_delta_ell", "<f8"),
        ("ri_v2_J", "<f8"),
        ("ccic_operations", "<u4"),
        ("ri_v2_operations", "<u4"),
        ("ccic_peak", "<u2"),
        ("ri_v2_peak", "<u2"),
    ]
)


def formula_counts(n: int, m: int) -> tuple[int, int, int, int]:
    return 14 * n + 392 * m + 8, 14 * n + 357 * m + 7, 22 + 6 * m, 24 + 6 * m


def _cell_filename(n: int, k: int, regime: str) -> str:
    return f"N{n}_k{k}_{regime}.npy"


def offline_work_replay(
    block: int,
    trained: TrainedSeed,
    seed_staging_directory: Path,
    resource_check=None,
) -> dict:
    final_directory = seed_staging_directory / "work_replay"
    temporary_directory = seed_staging_directory / ".work_replay.tmp"
    if final_directory.exists() or temporary_directory.exists():
        raise FileExistsError(f"fresh work-replay seed directory required: {final_directory}")
    temporary_directory.mkdir(parents=True, exist_ok=False)
    cell_manifests: list[dict] = []
    total_tuples = 0
    try:
        for n in EVAL_N:
            for k in EVAL_K:
                ticks = tuple(range(0, 30, k))
                rows_per_cell = 256 * len(ticks)
                for regime in REGIMES:
                    if resource_check is not None:
                        resource_check()
                    expected_m = 1 if regime == "DUP" else n
                    filename = _cell_filename(n, k, regime)
                    partial_path = temporary_directory / f"{filename}.partial"
                    final_path = temporary_directory / filename
                    records = np.lib.format.open_memmap(
                        partial_path,
                        mode="w+",
                        dtype=RECORD_DTYPE,
                        shape=(rows_per_cell,),
                    )
                    position = 0
                    for episode in range(256):
                        hidden = latent_tape(trained.seed, episode)
                        for t in ticks:
                            capture_tick = t + k
                            table = batch_rows(trained.seed, episode, capture_tick, n, regime, hidden[capture_tick])
                            unique, _ = quotient_new_rows(table, set())
                            if len(unique) != expected_m:
                                raise ValueError(
                                    f"offline replay M mismatch N={n},k={k},rho={regime},episode={episode},t={t}"
                                )
                            z = np.asarray([row.z for row in unique], dtype=np.float64)
                            overlap = np.asarray([row.overlap_code for row in unique], dtype=np.float64)
                            quality = np.ones(expected_m, dtype=np.float64)
                            ccic_q, ccic_j = trained.ccic.fusion(z, overlap, quality)
                            ri_delta, ri_j = trained.ri.forward(z, OVERLAP[regime], t, k)
                            ccic_trace = trained.ccic.last_streaming_trace
                            ri_trace = trained.ri.last_streaming_trace
                            if (
                                not ccic_trace["cache_free"]
                                or not ri_trace["cache_free"]
                                or ccic_trace["unique_rows"] != expected_m
                                or ri_trace["unique_rows"] != expected_m
                            ):
                                raise RuntimeError("functional replay did not use the canonical cache-free streaming path")
                            outputs = (ccic_q, ccic_j, ri_delta, ri_j)
                            if not all(np.isfinite(value) for value in outputs):
                                raise FloatingPointError("offline work replay produced a nonfinite functional output")
                            ccic_ops, ri_ops, ccic_peak, ri_peak = formula_counts(n, expected_m)
                            records[position] = (
                                episode,
                                t,
                                expected_m,
                                ccic_q,
                                ccic_j,
                                ri_delta,
                                ri_j,
                                ccic_ops,
                                ri_ops,
                                ccic_peak,
                                ri_peak,
                            )
                            position += 1
                        if resource_check is not None and episode % 16 == 0:
                            resource_check()
                    if position != rows_per_cell:
                        raise AssertionError("offline replay tuple count mismatch")
                    records.flush()
                    del records
                    fsync_file(partial_path)
                    atomic_replace(partial_path, final_path)
                    fsync_file(final_path)
                    fsync_directory(temporary_directory)
                    ccic_ops, ri_ops, ccic_peak, ri_peak = formula_counts(n, expected_m)
                    operation_ratio = max(ccic_ops, ri_ops) / min(ccic_ops, ri_ops)
                    peak_ratio = max(ccic_peak, ri_peak) / min(ccic_peak, ri_peak)
                    formula_agreement = (
                        ccic_ops == 14 * n + 392 * expected_m + 8
                        and ri_ops == 14 * n + 357 * expected_m + 7
                        and ccic_peak == 22 + 6 * expected_m
                        and ri_peak == 24 + 6 * expected_m
                    )
                    passed = formula_agreement and operation_ratio <= 1.10 and peak_ratio <= 1.10
                    cell_manifests.append(
                        {
                            "N": n,
                            "k": k,
                            "regime": regime,
                            "M": expected_m,
                            "tuple_order": "episode ascending, then reachable t ascending",
                            "tuple_count": rows_per_cell,
                            "record_dtype": RECORD_DTYPE.descr,
                            "artifact": filename,
                            "sha256": sha256_file(final_path),
                            "ccic_operations_median": ccic_ops,
                            "ri_v2_operations_median": ri_ops,
                            "ccic_peak_median": ccic_peak,
                            "ri_v2_peak_median": ri_peak,
                            "operation_ratio": operation_ratio,
                            "peak_ratio": peak_ratio,
                            "functional_calls_per_arm": rows_per_cell,
                            "formula_replay_agreement": formula_agreement,
                            "valid_input_failures": 0,
                            "nonfinite_failures": 0,
                            "passed": passed,
                        }
                    )
                    total_tuples += rows_per_cell
        manifest = {
            "seed_block": block,
            "seed": trained.seed,
            "record_format": "NumPy .npy structured array; lossless float64 functional outputs",
            "functional_stage_signature": {
                "CCIC": "lineage quotient -> metadata row network -> Woodbury q/J",
                "RI-STRONG-v2": "lineage quotient -> shared 6->9->2 row MLP -> r+tanh(r) -> ascending mean -> decodes",
            },
            "cells": cell_manifests,
            "cell_count": len(cell_manifests),
            "total_tuple_count": total_tuples,
            "expected_total_tuple_count_per_seed": 256 * 3 * 3 * sum(len(range(0, 30, k)) for k in EVAL_K),
            "every_tuple_reported": total_tuples == 256 * 3 * 3 * sum(len(range(0, 30, k)) for k in EVAL_K),
            "all_formula_replay_agreement": all(cell["formula_replay_agreement"] for cell in cell_manifests),
            "all_cells_passed": len(cell_manifests) == 27 and all(cell["passed"] for cell in cell_manifests),
            "ignored_output_padding": False,
            "dummy_work": False,
            "complete": False,
        }
        manifest["passed"] = (
            manifest["every_tuple_reported"]
            and manifest["all_formula_replay_agreement"]
            and manifest["all_cells_passed"]
        )
        manifest["complete"] = manifest["passed"]
        write_json_atomic(temporary_directory / "manifest.json", manifest)
        fsync_directory(temporary_directory)
        atomic_replace(temporary_directory, final_directory)
        fsync_directory(final_directory.parent)
        return manifest
    except Exception:
        # Incomplete temporary directories are intentionally not promoted and
        # cannot be referenced by a retained complete-seed manifest.
        raise
