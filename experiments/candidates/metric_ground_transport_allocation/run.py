"""Exact sequential MGTAP B1 revision-04 production runner."""

from __future__ import annotations

import os

# Set numerical limits before importing NumPy/Torch native runtimes.
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "4"

import argparse
import ctypes
import json
import time
from pathlib import Path
from ctypes import wintypes

import numpy as np
import torch

from .actor import Actor, HADAMARD, metric_map
from .analysis import analyze
from .artifacts import create_temp_root, install, json_write, tree_bytes, validate_seed_packet, validate_tree, write_npz
from .certificate import deterministic_certificate
from .config import (
    ARMS, BINDINGS, CALIBRATION_SEEDS, EVAL_SIZES, FINAL_SEEDS, GRID,
    LOADS, ORDERED_PAIRS, REVISION, TRUE_UTILITY, DISPLAYED_COORDINATES,
    EXPECTED_COUNTS,
)
from .evaluation import combine_fits, evaluate_fit
from .trainer import calibration_fit, conclusion_fit


WALL_CAP_SECONDS = 8 * 60 * 60
CPU_CAP_SECONDS = 32 * 60 * 60
RSS_CAP_BYTES = 4 * 1024**3
DISK_CAP_BYTES = 8 * 1024**3


def _peak_rss_bytes() -> int:
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
    )
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo failed")
    return int(counters.PeakWorkingSetSize)


class Guard:
    def __init__(self, temp_root: Path) -> None:
        self.started_wall = time.perf_counter()
        self.started_cpu = time.process_time()
        self.temp_root = temp_root

    def facts(self) -> dict[str, float | int]:
        return {
            "wall_seconds": time.perf_counter() - self.started_wall,
            "cpu_seconds": time.process_time() - self.started_cpu,
            "peak_rss_bytes": _peak_rss_bytes(),
            "artifact_bytes": tree_bytes(self.temp_root),
        }

    def check(self) -> dict[str, float | int]:
        facts = self.facts()
        if facts["wall_seconds"] >= WALL_CAP_SECONDS:
            raise RuntimeError("MGTAP wall cap exhausted")
        if facts["cpu_seconds"] > CPU_CAP_SECONDS:
            raise RuntimeError("MGTAP CPU-core-hour cap exhausted")
        if facts["peak_rss_bytes"] >= RSS_CAP_BYTES:
            raise RuntimeError("MGTAP RSS cap exhausted")
        if facts["artifact_bytes"] >= DISK_CAP_BYTES:
            raise RuntimeError("MGTAP disk frontier exhausted")
        return facts


def _common_addresses() -> np.ndarray:
    rows = []
    key = 0
    for n in EVAL_SIZES:
        for pair_index, _ in enumerate(ORDERED_PAIRS):
            for load_index, _ in enumerate(LOADS):
                for epoch in (1, 2):
                    for tape in range(64):
                        rows.append((key, n, pair_index, load_index, tape, epoch))
                        key += 1
    return np.asarray(rows, dtype=np.int32)


def _select_calibration(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    selected = np.empty(4, dtype=np.int8)
    slopes = np.empty(4, dtype=np.float64)
    valid = np.empty(4, dtype=np.int8)
    for cell in range(4):
        scores = values[cell, :, :, 1].mean(axis=1)
        index = max(range(len(GRID)), key=lambda i: (scores[i], -GRID[i].learning_rate, GRID[i].weight_decay))
        selected[cell] = index
        v32 = values[cell, index, :, 0].mean()
        v64 = values[cell, index, :, 1].mean()
        slopes[cell] = (v64 - v32) / 32.0
        on_lr_boundary = GRID[index].learning_rate in (0.01, 0.10)
        on_lambda_boundary = GRID[index].weight_decay in (0.0, 0.0001)
        valid[cell] = not ((on_lr_boundary or on_lambda_boundary) and abs(v64 - v32) > 0.005)
    return selected, slopes, valid


def _free_identity(packet: dict[str, np.ndarray]) -> None:
    params = packet["checkpoint_parameters"]
    if not np.array_equal(params[2], params[3]):
        raise RuntimeError("FREE intact/cut checkpoints differ")
    mask_i = (packet["arm"] == 1) & (packet["binding"] == 0)
    mask_k = (packet["arm"] == 1) & (packet["binding"] == 1)
    for key in ("sampled_step_actions", "coupling_X", "idle_iota", "unmet_mu", "reward", "normalized_endpoint"):
        if not np.array_equal(packet[key][mask_i], packet[key][mask_k]):
            raise RuntimeError(f"FREE intact/cut output leakage: {key}")


def production(output: Path) -> None:
    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    temp = create_temp_root(output)
    activity_marker = output.with_name(output.name + "_activity_started.json")
    if activity_marker.exists():
        prior = json.loads(activity_marker.read_text(encoding="utf-8"))
        if prior.get("revision") != REVISION or prior.get("scientific_activity_started") is not True:
            raise RuntimeError("existing activity marker does not match frozen revision")
    os.environ["MGTAP_ACTIVITY_MARKER"] = str(activity_marker)
    guard = Guard(temp)
    certificate, panel_arrays, panel_lookup = deterministic_certificate()
    if not certificate["passed"]:
        raise RuntimeError(f"deterministic certificate failed: {certificate}")

    cells = [(arm, binding) for arm in ARMS for binding in BINDINGS]
    calibration_values = np.empty((4, len(GRID), len(CALIBRATION_SEEDS), 2), dtype=np.float64)
    calibration_gradients = np.empty((4, len(GRID), len(CALIBRATION_SEEDS)), dtype=np.float64)
    for cell_index, (arm, binding) in enumerate(cells):
        for grid_index, hyper in enumerate(GRID):
            for seed_index, seed in enumerate(CALIBRATION_SEEDS):
                fit = calibration_fit(arm, binding, seed, hyper)
                calibration_values[cell_index, grid_index, seed_index] = (fit.validation[32], fit.validation[64])
                calibration_gradients[cell_index, grid_index, seed_index] = fit.gradient_norm_max
                guard.check()
        print(json.dumps({"phase": "calibration_cell_complete", "arm": arm, "binding": binding}), flush=True)
    selected, slopes, optimization_valid = _select_calibration(calibration_values)
    if selected[2] != selected[3] or not np.array_equal(calibration_values[2], calibration_values[3]):
        raise RuntimeError("FREE intact/cut calibration leakage")

    tables = dict(panel_arrays)
    tables.update({
        "edge_maps": np.asarray((metric_map("INTACT"), metric_map("CUT"), HADAMARD)),
        "true_utility": np.asarray(TRUE_UTILITY, dtype=np.float64),
        "displayed_coordinates": np.asarray((DISPLAYED_COORDINATES["INTACT"], DISPLAYED_COORDINATES["CUT"]), dtype=np.float64),
        "ordered_pairs": np.asarray(ORDERED_PAIRS, dtype=np.int8),
        "common_addresses": _common_addresses(),
        "calibration_values": calibration_values,
        "calibration_gradient_norm_max": calibration_gradients,
        "selected_grid_index": selected,
        "selected_learning_rate": np.asarray([GRID[i].learning_rate for i in selected]),
        "selected_weight_decay": np.asarray([GRID[i].weight_decay for i in selected]),
        "calibration_slope_32": slopes,
        "optimization_valid": optimization_valid,
    })
    write_npz(temp / "tables.npz", tables)
    guard.check()

    for seed in FINAL_SEEDS:
        fit_packets = []
        parameters = []
        selected_hyper = []
        for cell_index, (arm, binding) in enumerate(cells):
            hyper = GRID[int(selected[cell_index])]
            fitted = conclusion_fit(arm, binding, seed, hyper)
            actor = Actor(arm, binding)
            actor.load_parameter_vector(fitted.parameters)
            fit_packets.append(evaluate_fit(actor, seed, 0 if arm == "METRIC" else 1, 0 if binding == "INTACT" else 1, panel_lookup))
            parameters.append(fitted.parameters)
            selected_hyper.append((hyper.learning_rate, hyper.weight_decay))
            guard.check()
        packet = combine_fits(fit_packets, np.asarray(parameters), np.asarray(selected_hyper))
        _free_identity(packet)
        seed_path = temp / f"seed_{seed}.npz"
        write_npz(seed_path, packet)
        validate_seed_packet(seed_path, seed)
        guard.check()
        print(json.dumps({"phase": "seed_complete", "seed": seed}), flush=True)

    analysis = analyze(temp, structural_valid=True, optimization_valid=bool(np.all(optimization_valid)))
    resources = guard.facts()
    manifest = {
        "artifact_kind": "MGTAP_B1_ATOMIC_RESULT",
        "revision": REVISION,
        "arms": list(ARMS), "bindings": list(BINDINGS),
        "training_sizes": [4, 8], "heldout_sizes": [6, 12],
        "calibration_seeds": list(CALIBRATION_SEEDS), "final_seeds": list(FINAL_SEEDS),
        "selected_grid_index": selected.tolist(),
        "selected_hyperparameters": [[GRID[i].learning_rate, GRID[i].weight_decay] for i in selected],
        "calibration_slope_32": slopes.tolist(),
        "optimization_valid": optimization_valid.astype(bool).tolist(),
        "deterministic_certificate": certificate,
        "expected_and_actual_work": EXPECTED_COUNTS,
        "codes": {"arm": {"0": "METRIC", "1": "FREE"}, "binding": {"0": "INTACT", "1": "CUT"}, "load": {"0": "SLACK", "1": "OVERLOAD"}},
        "activity_boundary_crossed": True,
    }
    summary = {
        "revision": REVISION,
        "question_relevant_output_exists": True,
        "analysis": analysis,
        "resources": resources,
        "material_technical_anomalies": [],
    }
    json_write(temp / "manifest.json", manifest)
    json_write(temp / "summary.json", summary)
    guard.check()
    validate_tree(temp)
    guard.check()
    # Refresh terminal resource facts after complete validation and immediately
    # before the single atomic rename.
    summary["resources"] = guard.facts()
    json_write(temp / "summary.json", summary)
    guard.check()
    install(temp, output, prevalidated=True)
    print(json.dumps({"phase": "complete", "output": str(output), "branch": analysis["branch"]}), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--certificate", action="store_true")
    args = parser.parse_args()
    if args.certificate:
        certificate, _, _ = deterministic_certificate()
        print(json.dumps(certificate, indent=2, sort_keys=True))
        if not certificate["passed"]:
            raise SystemExit(1)
        return
    if args.output is None:
        parser.error("--output is required for production")
    production(args.output.resolve())


if __name__ == "__main__":
    main()
