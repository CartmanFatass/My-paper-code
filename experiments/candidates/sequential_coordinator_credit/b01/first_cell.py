"""``first-cell`` orchestration: trainings, snapshot readings, regret, artifacts.

Two training configurations: the declared binding corner (beta = .9, s = 1, sigma = .2) and the
DM's host-matched configuration (``--host-matched``; refused if equal to the corner).  For each
configuration x arm (E1, E3, E4, E3*, E4*) x entropy setting x seed one training of ``updates``
updates; each E1 training keeps its policy snapshots at ``READING_SNAPSHOTS`` (those <= updates),
which are then read for every arm (phase 2).  Seeds are 1..N (see ``SEED_BASE``).

Random streams (all ``np.random.default_rng``):
contexts and every noise draw ``[config_index, seed]`` (common to arms and entropy settings);
policy samples, E3 continuations and minibatch permutations
``[config_index, arm_index, entropy_index, seed]``; E3 reading batches
``[7, config_index, entropy_index, seed, snapshot]``.

Outputs under ``<out>/first-cell/``: ``config.json``, ``summary.json``, ``progress.jsonl`` and
``regret.npz`` (per-seed arrays, including the per-seed snapshot readings).
"""

from __future__ import annotations

import hashlib
import json
import math
import multiprocessing
import os
import resource
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

from . import calibration as cal
from . import chain_bandit as cb
from . import estimators as est
from . import learner as ln
from . import readings as rd

OBJECT_ID = "SEQUENTIAL-COORDINATOR-CREDIT-B01-FIRST-CELL"
PHASE = "first-cell"
SEED_BASE = 1          # seeds are 1..N: seed 0 would make [config_index, 0, 0, 0] (policy key)
                       # equal the zero-padded context key [config_index, 0] (SeedSequence pads)
DEFAULT_SEEDS = 100
DEFAULT_WORKERS = 8
CONFIG_ROLES = ("binding_corner", "host_matched")
REPO_ROOT = Path(__file__).resolve().parents[4]
THREAD_VARIABLES = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")


# ----------------------------------------------------------------------------- records

def _clean(value):
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return _clean(value.tolist())
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (float, np.floating)):
        value = float(value)
        return value if math.isfinite(value) else None
    return value


def write_json(path: Path, value: dict) -> None:
    """Atomic replace after successful serialisation (non-finite floats become null)."""
    path = Path(path)
    payload = json.dumps(_clean(value), allow_nan=False, separators=(",", ":")) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=".summary-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def progress(root: Path, event: dict) -> None:
    with (Path(root) / "progress.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_clean({"time": time.time(), **event}), allow_nan=False,
                                separators=(",", ":")) + "\n")
        handle.flush()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def prepare_root(root: Path) -> Path:
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"output already exists: {root}")
    root.mkdir(parents=True, exist_ok=True)
    return root


def finish(root: Path, summary: dict, started: float) -> None:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    summary.update(wall_seconds=time.perf_counter() - started,
                   peak_rss_kib={"runner": int(own.ru_maxrss),
                                 "largest_worker": int(children.ru_maxrss)})
    write_json(root / "summary.json", summary)
    progress(root, {"event": "run_end", "status": summary["status"],
                    "failure": summary["failure"], "wall_seconds": summary["wall_seconds"]})


def base_config() -> dict:
    """Every constant of the L0 (host, learner, estimators, readings, streams)."""
    return {
        "K": cb.K, "labels": list(cb.LABELS), "clusters": cb.C, "B_relayed": cb.B_RELAYED,
        "b0_rule": "(1 - beta) * B", "n_contexts": cb.N_CONTEXTS, "n_joints": cb.N_JOINTS,
        "demand_range": list(cb.DEMAND_RANGE), "quality_range": list(cb.QUALITY_RANGE),
        "demand_clip": list(cb.DEMAND_CLIP), "eval_noise_draws": cb.N_NOISE_DRAWS,
        "betas": list(cb.BETAS), "substitutability": list(cb.SUBSTITUTABILITY),
        "sigmas": list(cb.SIGMAS),
        "masks": {str(s): [[cb.LABELS[label] for label in (cb.IDLE,) + labels]
                           for labels in cb.MASK_LABELS[s]] for s in cb.SUBSTITUTABILITY},
        "configurations": [{"config_index": i, **c.record()}
                           for i, c in enumerate(cb.CONFIGURATIONS)],
        "configuration_order": "beta outer, s, sigma inner",
        "binding_corner": list(cb.BINDING_CORNER),
        "joint_order": "joint = sum_i z_i * 4**(K-1-i) (agent 0 most significant); greedy ties "
                       "to the lowest joint index",
        "reward": "sum_c min(d_c, access_c, backhaul); backhaul = B if any effective RELAY else "
                  "b0; masked labels count as IDLE",
        "noise": "d_c <- clip(d_c + sigma * xi, .05, 1) per (update, context, sample)",
        "exact_quantities_noise": ("J, J*, grad J, greedy-optimal joint and the exact readings "
                                   "average R over the context's fixed evaluation noise set "
                                   "(32 draws when sigma > 0, one otherwise); J* = mean_x "
                                   "max_z of that mean; oracle arms in training use the "
                                   "sample's realised demands"),
        "samples_per_context": ln.SAMPLES_PER_CONTEXT, "ppo_epochs": ln.PPO_EPOCHS,
        "minibatch": ln.MINIBATCH, "learning_rate": ln.LEARNING_RATE,
        "adam_betas": list(ln.ADAM_BETAS), "adam_eps": ln.ADAM_EPS, "clip_eps": ln.CLIP_EPS,
        "value_ema_rate": ln.VALUE_RATE,
        "value_rule": "V_0 = batch mean of update 0; V_u = V_{u-1} + .1 (batch mean_u - "
                      "V_{u-1}); V_u used at update u",
        "normalisation": "joint over the whole update batch (1024 x 4 agent + 1024 team "
                         "advantages): (A - mean) / (std(ddof=1) + 1e-8)",
        "entropy_settings": [{"label": label, "start": start, "end": end}
                             for label, start, end in ln.ENTROPY_SETTINGS],
        "entropy_schedule": "lambda_h(u) = start + (end - start) * u / U",
        "default_updates": ln.UPDATES, "arms": list(est.ARMS),
        "ridge_lambda": est.RIDGE_LAMBDA, "ridge_intercept_penalised": False,
        "continuations_L": est.N_CONTINUATIONS,
        "reading_snapshots": list(rd.READING_SNAPSHOTS), "e3_reading_draws": rd.E3_READING_DRAWS,
        "calibrations": list(rd.CALIBRATIONS), "reading_metrics": list(rd.METRICS),
        "regret": "(1/U) sum_{u=0}^{U-1} (J* - J(pi_u)), pi_u the policy before update u",
        "calibration": {"seed": cal.CALIBRATION_SEED, "policies": list(cal.POLICIES),
                        "targets": cal.TARGETS, "scales": cal.SCALES,
                        "sparsity_threshold": cal.SPARSITY_THRESHOLD},
        "seed_base": SEED_BASE,
        "streams": {"contexts_and_noise": "[config_index, seed]",
                    "policy": "[config_index, arm_index, entropy_index, seed]",
                    "e3_readings": "[7, config_index, entropy_index, seed, snapshot]"},
    }


# ----------------------------------------------------------------------------- workers

def run_training(task: ln.TrainingTask) -> dict:
    result = ln.train(task)
    result["task"] = asdict(task)
    return result


def run_reading(job: dict) -> dict:
    started = time.perf_counter()
    contexts, _ = cb.make_contexts(job["config_index"], job["seed"])
    rng = rd.reading_stream(job["config_index"], job["entropy_index"], job["seed"],
                            job["snapshot"])
    reading = rd.snapshot_readings(job["theta"], contexts, rng)
    return {"key": (job["config_index"], job["entropy_index"], job["seed"], job["snapshot"]),
            "reading": reading, "wall_seconds": time.perf_counter() - started}


def _pool_map(function, items, workers: int, on_result):
    items = list(items)
    if int(workers) <= 1 or len(items) <= 1:
        for item in items:
            on_result(function(item))
        return
    saved = {name: os.environ.get(name) for name in THREAD_VARIABLES}
    try:
        for name in THREAD_VARIABLES:
            os.environ[name] = "1"
        context = multiprocessing.get_context("spawn")
        with context.Pool(processes=min(int(workers), len(items))) as pool:
            for result in pool.imap_unordered(function, items, chunksize=1):
                on_result(result)
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


# ----------------------------------------------------------------------------- aggregation

def mean_se(values) -> dict:
    values = np.asarray(values, dtype=np.float64).ravel()
    values = values[np.isfinite(values)]
    n = int(values.size)
    return {"mean": float(values.mean()) if n else None,
            "se": float(values.std(ddof=1) / np.sqrt(n)) if n > 1 else None, "n": n}


def training_configurations(host_matched) -> list[tuple[str, int]]:
    corner = cb.config_index(cb.BINDING_CORNER)
    host = cb.config_index(host_matched)
    if host == corner:
        raise ValueError("host-matched configuration equals the binding corner; the two "
                         "training configurations must differ")
    return [("binding_corner", corner), ("host_matched", host)]


def _reading_arrays(readings: dict, configs, seeds, snapshots) -> dict[str, np.ndarray]:
    """Per-seed reading arrays [config, entropy, snapshot, arm, seed] per calibration x metric."""
    arrays = {}
    shape = (len(configs), len(ln.ENTROPY_SETTINGS), len(snapshots), len(est.ARMS), len(seeds))
    for which in rd.CALIBRATIONS:
        for metric in rd.METRICS + ("cosine_se", "projection_se"):
            arrays[f"reading__{which}__{metric}"] = np.full(shape, np.nan)
    for c, (_, ci) in enumerate(configs):
        for e in range(len(ln.ENTROPY_SETTINGS)):
            for t, snap in enumerate(snapshots):
                for s, seed in enumerate(seeds):
                    reading = readings.get((ci, e, seed, snap))
                    if reading is None:
                        continue
                    for a, arm in enumerate(est.ARMS):
                        for which in rd.CALIBRATIONS:
                            for metric, value in reading["arms"][arm][which].items():
                                key = f"reading__{which}__{metric}"
                                if key in arrays:
                                    arrays[key][c, e, t, a, s] = value
    return arrays


def aggregate_readings(readings: dict, configs, seeds, snapshots) -> dict:
    out = {}
    for role, ci in configs:
        per_entropy = {}
        for e, (label, _, _) in enumerate(ln.ENTROPY_SETTINGS):
            per_snapshot = {}
            for snap in snapshots:
                items = [readings[(ci, e, seed, snap)] for seed in seeds
                         if (ci, e, seed, snap) in readings]
                if not items:
                    continue
                arms = {}
                for arm in est.ARMS:
                    arms[arm] = {which: {metric: mean_se([item["arms"][arm][which][metric]
                                                          for item in items])
                                         for metric in items[0]["arms"][arm][which]
                                         if metric != "draws"}
                                 for which in rd.CALIBRATIONS}
                shapley = {key: np.mean([np.asarray(item["shapley"][key], dtype=np.float64)
                                         for item in items], axis=0)
                           for key in items[0]["shapley"]}
                per_snapshot[f"update_{snap}"] = {
                    "seeds": len(items), "J": mean_se([item["J"] for item in items]),
                    "grad_J_norm": mean_se([item["grad_J_norm"] for item in items]),
                    "arms": arms, "shapley_seed_mean": shapley}
            per_entropy[label] = per_snapshot
        out[role] = per_entropy
    return out


def aggregate_regret(arrays: dict, configs) -> tuple[dict, dict]:
    blocks = {}
    rule = {}
    for c, (role, ci) in enumerate(configs):
        per_entropy = {}
        for e, (label, _, _) in enumerate(ln.ENTROPY_SETTINGS):
            arms = {}
            for a, arm in enumerate(est.ARMS):
                arms[arm] = {key: mean_se(arrays[key][c, a, e])
                             for key in ("regret", "final_J", "relay_fraction",
                                         "greedy_optimal_fraction", "greedy_optimal_mass")}
            paired = {}
            for (a, first), (b, second) in combinations(enumerate(est.ARMS), 2):
                paired[f"{first}-{second}"] = {
                    key: mean_se(arrays[key][c, a, e] - arrays[key][c, b, e])
                    for key in ("regret", "final_J")}
            e4, e3 = est.ARMS.index("E4"), est.ARMS.index("E3")
            e4_minus_e3 = {key: mean_se(arrays[key][c, e4, e] - arrays[key][c, e3, e])
                           for key in ("regret", "final_J")}
            paired["E4-E3"] = e4_minus_e3
            per_entropy[label] = {"J_star": mean_se(arrays["J_star"][c]), "arms": arms,
                                  "paired_differences": paired}
            if role == "binding_corner":
                rule[label] = e4_minus_e3
        blocks[role] = {"config_index": ci, **cb.CONFIGURATIONS[ci].record(),
                        "entropy": per_entropy}
    return blocks, rule


# ----------------------------------------------------------------------------- phase

def run_first_cell(*, out: Path, launch_sha: str, seeds: int = DEFAULT_SEEDS,
                   updates: int = ln.UPDATES, workers: int = DEFAULT_WORKERS,
                   host_matched=None, argv=None) -> dict:
    if host_matched is None:
        raise ValueError("first-cell requires the host-matched configuration (beta, s, sigma)")
    configs = training_configurations(host_matched)
    seeds, updates, workers = int(seeds), int(updates), int(workers)
    if seeds < 1 or updates < 1:
        raise ValueError("seeds and updates must be positive")
    cpus = os.cpu_count() or 1
    if workers < 1 or workers > cpus:
        raise ValueError(f"workers must be in [1, os.cpu_count() = {cpus}]")
    seed_list = list(range(SEED_BASE, SEED_BASE + seeds))
    snapshots = tuple(u for u in rd.READING_SNAPSHOTS if u <= updates)
    absent = [u for u in rd.READING_SNAPSHOTS if u > updates]
    root = prepare_root(Path(out) / PHASE)
    started = time.perf_counter()
    config = {**base_config(), "object_id": OBJECT_ID, "phase": PHASE, "launch_sha": launch_sha,
              "git_head": git_head(), "argv": list(sys.argv if argv is None else argv),
              "training_configurations": [{"role": role, "config_index": ci,
                                           **cb.CONFIGURATIONS[ci].record()}
                                          for role, ci in configs],
              "seeds": seed_list, "updates": updates, "workers": workers,
              "os_cpu_count": cpus, "snapshots_read": list(snapshots),
              "snapshots_absent": absent}
    write_json(root / "config.json", config)
    planned = len(configs) * len(est.ARMS) * len(ln.ENTROPY_SETTINGS) * seeds
    counts = {"planned_trainings": planned, "started_trainings": 0, "completed_trainings": 0,
              "updates_per_training": updates, "seeds": seeds, "snapshot_readings": 0,
              "training_wall_seconds_total": 0.0, "reading_wall_seconds_total": 0.0,
              "training_phase_wall_seconds": None, "reading_phase_wall_seconds": None}
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "phase": PHASE, "status": "INCOMPLETE", "failure": None,
        "launch_sha": launch_sha, "configurations": config["training_configurations"],
        "seeds": seed_list, "updates": updates, "workers": workers,
        "snapshots_read": list(snapshots), "snapshots_absent": absent, "counts": counts,
        "artifacts": {"config.json": sha256_file(root / "config.json")}}
    write_json(root / "summary.json", summary)
    progress(root, {"event": "run_start", "phase": PHASE, "planned_trainings": planned,
                    "seeds": seeds, "updates": updates, "workers": workers,
                    "configurations": [ci for _, ci in configs]})
    try:
        tasks = [ln.TrainingTask(config_index=ci, arm_index=a, entropy_index=e, seed=seed,
                                 updates=updates,
                                 snapshots=snapshots if est.ARMS[a] == "E1" else ())
                 for seed in seed_list for _, ci in configs
                 for a in range(len(est.ARMS)) for e in range(len(ln.ENTROPY_SETTINGS))]
        counts["started_trainings"] = len(tasks)
        index_of = {ci: c for c, (_, ci) in enumerate(configs)}
        shape = (len(configs), len(est.ARMS), len(ln.ENTROPY_SETTINGS), seeds)
        arrays = {"J_curve": np.full(shape + (updates + 1,), np.nan),
                  "regret": np.full(shape, np.nan), "final_J": np.full(shape, np.nan),
                  "relay_fraction": np.full(shape, np.nan),
                  "greedy_optimal_fraction": np.full(shape, np.nan),
                  "greedy_optimal_mass": np.full(shape, np.nan),
                  "training_wall_seconds": np.full(shape, np.nan),
                  "J_star": np.full((len(configs), seeds), np.nan)}
        per_seed_done = {seed: 0 for seed in seed_list}
        per_seed_total = len(tasks) // seeds
        reading_jobs = []

        def on_training(result):
            task = result["task"]
            c, a, e = index_of[task["config_index"]], task["arm_index"], task["entropy_index"]
            s = task["seed"] - SEED_BASE
            arrays["J_curve"][c, a, e, s] = result["J"]
            for key in ("regret", "final_J", "relay_fraction", "greedy_optimal_fraction",
                        "greedy_optimal_mass"):
                arrays[key][c, a, e, s] = result[key]
            arrays["training_wall_seconds"][c, a, e, s] = result["wall_seconds"]
            arrays["J_star"][c, s] = result["J_star"]
            counts["completed_trainings"] += 1
            counts["training_wall_seconds_total"] += result["wall_seconds"]
            for snap, theta in result["snapshots"].items():
                reading_jobs.append({"config_index": task["config_index"],
                                     "entropy_index": e, "seed": task["seed"],
                                     "snapshot": int(snap), "theta": theta})
            per_seed_done[task["seed"]] += 1
            if per_seed_done[task["seed"]] == per_seed_total:
                progress(root, {"event": "seed_end", "seed": task["seed"],
                                "completed_trainings": counts["completed_trainings"]})

        phase_started = time.perf_counter()
        _pool_map(run_training, tasks, workers, on_training)
        counts["training_phase_wall_seconds"] = time.perf_counter() - phase_started
        write_json(root / "summary.json", summary)

        readings = {}

        def on_reading(result):
            readings[tuple(result["key"])] = result["reading"]
            counts["snapshot_readings"] += 1
            counts["reading_wall_seconds_total"] += result["wall_seconds"]

        reading_jobs.sort(key=lambda job: (job["config_index"], job["entropy_index"],
                                           job["seed"], job["snapshot"]))
        progress(root, {"event": "readings_start", "jobs": len(reading_jobs)})
        phase_started = time.perf_counter()
        _pool_map(run_reading, reading_jobs, workers, on_reading)
        counts["reading_phase_wall_seconds"] = time.perf_counter() - phase_started
        progress(root, {"event": "readings_end", "jobs": counts["snapshot_readings"],
                        "wall_seconds": counts["reading_phase_wall_seconds"]})

        arrays.update(_reading_arrays(readings, configs, seed_list, snapshots))
        arrays["seeds"] = np.asarray(seed_list)
        arrays["config_indices"] = np.asarray([ci for _, ci in configs])
        arrays["snapshots"] = np.asarray(snapshots, dtype=np.int64)
        npz = root / "regret.npz"
        np.savez_compressed(npz, **arrays)
        summary["artifacts"]["regret.npz"] = sha256_file(npz)
        summary["array_axes"] = {
            "training": "[configuration, arm, entropy, seed] (J_curve adds update 0..U)",
            "J_star": "[configuration, seed]",
            "reading": "[configuration, entropy, snapshot, arm, seed]",
            "arms": list(est.ARMS), "entropy": [label for label, _, _ in ln.ENTROPY_SETTINGS],
            "configurations": [role for role, _ in configs]}
        summary["readings"] = aggregate_readings(readings, configs, seed_list, snapshots)
        summary["regret"], summary["E4_minus_E3_binding_corner"] = aggregate_regret(arrays,
                                                                                    configs)
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        finish(root, summary, started)
