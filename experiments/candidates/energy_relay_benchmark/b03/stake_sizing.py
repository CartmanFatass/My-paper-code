"""Stage 2-0 zero-fit stake sizing: H_central under three assignment modes (CPU, deterministic).

H_central as Stage 1 ran it (``heuristic_params("H1", B01Spec())``: central information, 6 + 2
anchors, replan 30, 100 m, hysteresis 300 m; production shield enter 0.00 / exit 0.05; horizon
and evaluator seed from ``B01Spec``) on the development worlds 955001-955032, once per mode of
``ASSIGNMENT_MODES``.  ``evaluate_stake_task`` is ``b01.evaluation.evaluate_task``'s heuristic
branch step for step with the controller replaced by ``AssignmentModeController``; every helper
is imported from ``b01/evaluation.py`` and ``b01/native.py`` unchanged.

Outputs under ``<out>/stake-sizing/``: ``panels/<mode>.json``, ``traces/<mode>.npz``,
``progress.jsonl``, ``config.json`` and ``summary.json`` (paired readings against ``hungarian``,
the stake ``S`` against the better coordination-free rule, and the consistency check of the
hungarian panel against the recorded Stage 1 H_central panel on the same worlds).
"""

from __future__ import annotations

import json
import multiprocessing
import os
import resource
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import torch

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    CONTROLLER_INFORMATION,
    PLAN_SOURCE,
    REFERENCE_INFORMATION,
    TRACE_TIMING,
    UnobservedRegime,
    aggregate,
    evaluate_world,
    make_env,
    make_eval_config,
    sha256_file,
    trace_arrays,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    PRODUCTION_PARAMS,
    FeedbackParams,
)
from experiments.candidates.energy_relay_benchmark.b01.heuristic import HeuristicParams
from experiments.candidates.energy_relay_benchmark.b01.native import (
    HOLDOUT_WORLD_FLOOR,
    B01Spec,
    _progress,
    check_resources,
    heuristic_params,
)
from experiments.candidates.uav_service_auxiliary.b09.persistence import write_summary

from .assignment_modes import ASSIGNMENT_MODES, AssignmentModeController

OBJECT_ID = "ENERGY-RELAY-BENCHMARK-B03-STAGE2-0"
STAKE_PHASE = "stake-sizing"
STAKE_WORLDS = tuple(range(955001, 955033))
STAKE_CONTROLLER = "H1"
# Horizon, evaluator seed and default threads exactly as Stage 1's ``run_native`` used them
# (``B01Spec`` defaults; recorded in b01_ref_a02/config.json ``spec``).
STAKE_SPEC = B01Spec()
FREE_RULES = ("identity", "independent_nearest")
READING_FIELDS = ("qos_per_step", "raw_native_J", "native_J_per_step", "qos_per_step_pre_entry",
                  "qos_per_step_entry_to_input", "qos_per_step_post_input")
PAIRED_FIELDS = ("qos_per_step", "raw_native_J")
PHASE_DIFFERENCE_FIELDS = ("qos_per_step_pre_entry", "qos_per_step_post_input")
REPO_ROOT = Path(__file__).resolve().parents[4]
# Stage 1's H_central panel on 955001-955032 (B01 grid phase, production margins, CPU, wsl_4070,
# launch e1fdbe72f53a1597c34c1d32c89ac6700251dca0).  heuristic-dev/ holds 956001-956008 only.
RECORDED_PANEL = "runs/energy_relay_benchmark/b01_ref_a02/grid/panels/H1_e0.00_x0.05.json"
CONSISTENCY_TOLERANCE = 1e-9
MODE_RULES = {
    "hungarian": ("base LayoutHeuristic._assign_targets: distance cost minus the 300 m "
                  "previous-target hysteresis, Hungarian (scipy linear_sum_assignment)"),
    "identity": ("j-th available UAV (ascending index) takes priority slot j "
                 "(relays first, then centroids by descending user count); no cost"),
    "independent_nearest": ("base cost matrix (distance minus hysteresis), row-wise argmin per "
                            "available UAV; duplicates allowed, unclaimed anchors unserved"),
}


@dataclass(frozen=True)
class StakeTask:
    """Picklable description of one world under one assignment mode."""

    seed: int
    params: FeedbackParams
    horizon: int
    policy_seed: int
    threads: int
    heuristic: HeuristicParams
    mode: str
    log_dir: str | None = None
    controller: str = STAKE_CONTROLLER


def evaluate_stake_task(task: StakeTask) -> dict[str, Any]:
    """Module-level worker: ``evaluate_task``'s heuristic branch with the mode's controller."""
    started = time.perf_counter()
    torch.set_num_threads(int(task.threads))
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("B01 requires Torch FP32 default dtype")
    config = make_eval_config(task.horizon, task.policy_seed)
    with tempfile.TemporaryDirectory(prefix="b01-agent-logs-", dir=task.log_dir):
        env = make_env(config, task.seed)
        try:
            if task.heuristic is None:
                raise ValueError("heuristic controller requires HeuristicParams")
            controller = AssignmentModeController(task.heuristic, env, task.mode)
            labels = dict(
                controller_information=REFERENCE_INFORMATION.get(
                    task.controller, CONTROLLER_INFORMATION[task.heuristic.information]),
                plan_source=(PLAN_SOURCE if task.heuristic.information == "central"
                             else "legal-observation"),
            )
            try:
                row, arrays = evaluate_world(controller, env, config, task.seed, task.params)
            except UnobservedRegime as exc:
                # Recorded, never silently skipped: the world is marked failed.
                row, arrays = {"seed": int(task.seed), "failed": True,
                               "failure": f"UnobservedRegime: {exc}", **labels}, {}
            else:
                row.update(
                    failed=False, **labels,
                    plan_input_steps=len(controller.plan_input_steps),
                    search_replans=len(controller.search_replan_steps),
                    replans=-(-row["actual_length"] // task.heuristic.replan_period),
                )
        finally:
            env.close()
    row.update(controller=task.controller, enter_margin=task.params.enter_margin,
               exit_margin=task.params.exit_margin,
               wall_seconds=time.perf_counter() - started,
               worker_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
               action_mode="deterministic")
    row["assignment_mode"] = task.mode
    return {"row": row, "arrays": arrays}


def run_stake_tasks(tasks: Iterable[StakeTask], workers: int, *,
                    on_result: Callable[[dict[str, Any]], None] | None = None
                    ) -> list[dict[str, Any]]:
    """``run_tasks`` over ``evaluate_stake_task``: serial or spawn pool; ordered by seed."""
    tasks = list(tasks)
    results = []
    if int(workers) <= 1 or len(tasks) <= 1:
        for task in tasks:
            result = evaluate_stake_task(task)
            results.append(result)
            if on_result is not None:
                on_result(result)
    else:
        context = multiprocessing.get_context("spawn")
        with context.Pool(processes=min(int(workers), len(tasks))) as pool:
            for result in pool.imap(evaluate_stake_task, tasks, chunksize=1):
                results.append(result)
                if on_result is not None:
                    on_result(result)
    return sorted(results, key=lambda item: item["row"]["seed"])


# ----------------------------------------------------------------------------- readings

def _value(row: dict[str, Any] | None, field: str):
    if row is None or row.get("failed"):
        return None
    value = row.get(field)
    return None if value is None else float(value)


def _by_seed(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(row["seed"]): row for row in rows}


def _mean(values: list[float]):
    return float(np.mean(values)) if values else None


def _paired_differences(rows_a, rows_b, worlds, field):
    """Per-world a - b (None where either side is missing), aligned with ``worlds``."""
    a, b = _by_seed(rows_a), _by_seed(rows_b)
    result = []
    for seed in worlds:
        x, y = _value(a.get(int(seed)), field), _value(b.get(int(seed)), field)
        result.append(None if x is None or y is None else x - y)
    return result


def paired_block(differences: list, *, count_label: str, count_sign: str) -> dict[str, Any]:
    """Paired mean, SE (sd ddof 1 / sqrt(n)) and the count of worlds on ``count_sign`` of 0."""
    values = np.asarray([d for d in differences if d is not None], dtype=np.float64)
    n = int(values.size)
    counted = (values < 0.0) if count_sign == "negative" else (values > 0.0)
    return {
        "paired_mean": float(values.mean()) if n else None,
        "paired_se": float(values.std(ddof=1) / np.sqrt(n)) if n >= 2 else None,
        "n_worlds": n,
        count_label: int(counted.sum()),
        "per_world": list(differences),
    }


def mode_block(rows: list[dict[str, Any]], worlds) -> dict[str, Any]:
    by_seed = _by_seed(rows)
    block: dict[str, Any] = {"failed_worlds": [int(row["seed"]) for row in rows
                                               if row.get("failed")]}
    for field in READING_FIELDS:
        per_world = [_value(by_seed.get(int(seed)), field) for seed in worlds]
        observed = [value for value in per_world if value is not None]
        block[field] = {"mean": _mean(observed), "n_worlds": len(observed),
                        "per_world": per_world}
    return block


def stake_readings(rows_by_mode: dict[str, list[dict[str, Any]]], worlds) -> dict[str, Any]:
    """Per-mode readings, differences against hungarian, better free rule and the stake S."""
    worlds = [int(seed) for seed in worlds]
    hungarian = rows_by_mode["hungarian"]
    readings: dict[str, Any] = {
        "worlds": worlds,
        "per_mode": {mode: mode_block(rows, worlds) for mode, rows in rows_by_mode.items()},
        "versus_hungarian": {},
    }
    for mode in FREE_RULES:
        if mode not in rows_by_mode:
            continue
        block: dict[str, Any] = {"sign": f"{mode} - hungarian"}
        for field in PAIRED_FIELDS:
            block[field] = paired_block(
                _paired_differences(rows_by_mode[mode], hungarian, worlds, field),
                count_label="worlds_difference_below_zero", count_sign="negative")
        for field in PHASE_DIFFERENCE_FIELDS:
            differences = _paired_differences(rows_by_mode[mode], hungarian, worlds, field)
            observed = [d for d in differences if d is not None]
            block[f"{field}_difference"] = {"mean": _mean(observed), "n_worlds": len(observed)}
        readings["versus_hungarian"][f"{mode}_minus_hungarian"] = block
    free = [mode for mode in FREE_RULES if mode in rows_by_mode]
    means = {mode: readings["per_mode"][mode]["qos_per_step"]["mean"] for mode in free}
    ranked = [mode for mode in free if means[mode] is not None]
    # Higher 32-world mean QoS/step; an exact tie goes to the earlier rule in FREE_RULES.
    better = max(ranked, key=lambda mode: (means[mode], -FREE_RULES.index(mode))) if ranked else None
    readings["better_free_rule"] = better
    readings["free_rule_mean_qos_per_step"] = means
    if better is not None:
        readings["S"] = {"sign": f"hungarian - {better}"}
        for field in PAIRED_FIELDS:
            readings["S"][field] = paired_block(
                _paired_differences(hungarian, rows_by_mode[better], worlds, field),
                count_label="worlds_hungarian_leads", count_sign="positive")
    else:
        readings["S"] = None
    return readings


def consistency_check(hungarian_rows: list[dict[str, Any]], worlds, heuristic: HeuristicParams,
                      recorded_path: Path) -> dict[str, Any]:
    """Hungarian panel vs the recorded Stage 1 H_central panel, per world, within 1e-9.

    Record only: a mismatch (or a missing/unverifiable recorded panel) gives
    ``hungarian_matches_recorded: false`` with the reason; it never raises.
    """
    recorded_path = Path(recorded_path)
    result: dict[str, Any] = {"recorded_panel": RECORDED_PANEL, "recorded_panel_path":
                              str(recorded_path), "tolerance": CONSISTENCY_TOLERANCE,
                              "fields": list(PAIRED_FIELDS)}
    try:
        recorded = json.loads(recorded_path.read_text(encoding="utf-8"))
        result["recorded_panel_sha256"] = sha256_file(recorded_path)
    except (OSError, ValueError) as exc:
        return result | {"hungarian_matches_recorded": False,
                         "reason": f"recorded panel unreadable: {type(exc).__name__}: {exc}"}
    recorded_rows = recorded.get("worlds", [])
    recorded_worlds = [int(row["seed"]) for row in recorded_rows]
    identity_problems = []
    if recorded.get("controller") != STAKE_CONTROLLER:
        identity_problems.append(f"controller {recorded.get('controller')!r}")
    if recorded.get("params") != asdict(PRODUCTION_PARAMS):
        identity_problems.append(f"params {recorded.get('params')}")
    if recorded.get("heuristic_params") != heuristic.record():
        identity_problems.append("heuristic_params differ from H_central's record")
    if recorded_worlds != [int(seed) for seed in worlds]:
        identity_problems.append(f"recorded worlds {recorded_worlds[:3]}... (n={len(recorded_worlds)}) "
                                 f"!= evaluated worlds (n={len(list(worlds))})")
    result["recorded_identity_problems"] = identity_problems
    ours, theirs = _by_seed(hungarian_rows), _by_seed(recorded_rows)
    differing, max_abs = [], {field: 0.0 for field in PAIRED_FIELDS}
    for seed in worlds:
        mine, other = ours.get(int(seed)), theirs.get(int(seed))
        entry: dict[str, Any] = {"seed": int(seed)}
        bad = False
        for field in PAIRED_FIELDS:
            x, y = _value(mine, field), _value(other, field)
            entry[field] = {"stake": x, "recorded": y}
            if x is None or y is None:
                bad = True
                continue
            delta = abs(x - y)
            max_abs[field] = max(max_abs[field], delta)
            bad = bad or not delta <= CONSISTENCY_TOLERANCE
        if bad:
            differing.append(entry)
    result.update(max_abs_difference=max_abs, differing_worlds=differing,
                  compared_worlds=len(list(worlds)),
                  hungarian_matches_recorded=not identity_problems and not differing)
    return result


# ----------------------------------------------------------------------------- runner phase

def _git_head() -> str | None:
    try:
        completed = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
                                   capture_output=True, text=True, check=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout.strip() or None


def _stake_heuristic() -> HeuristicParams:
    heuristic = heuristic_params(STAKE_CONTROLLER, STAKE_SPEC)
    expected = {"information": "central", "n_service": 6, "replan_period": 30,
                "height_m": 100.0, "switch_margin_m": 300.0}
    observed = {key: getattr(heuristic, key) for key in expected}
    if observed != expected:
        raise RuntimeError(f"H1 parameters {observed} are not Stage 1's H_central {expected}")
    return heuristic


def run_stake_sizing(*, out: Path, launch_sha: str, workers: int, threads: int,
                     worlds=STAKE_WORLDS, modes=ASSIGNMENT_MODES, argv=None) -> dict[str, Any]:
    worlds = tuple(int(seed) for seed in worlds)
    modes = tuple(modes)
    if not worlds or len(set(worlds)) != len(worlds):
        raise ValueError("worlds must be a non-empty tuple of distinct seeds")
    held = [seed for seed in worlds if seed >= HOLDOUT_WORLD_FLOOR]
    if held:
        raise ValueError(f"stake sizing may not evaluate hold-out worlds {held}")
    if (len(set(modes)) != len(modes) or "hungarian" not in modes
            or any(mode not in ASSIGNMENT_MODES for mode in modes)):
        raise ValueError(f"modes must be distinct members of {ASSIGNMENT_MODES} incl. hungarian")
    spec = replace(STAKE_SPEC, workers=int(workers), threads=int(threads))
    check_resources(spec)
    heuristic = _stake_heuristic()
    params = PRODUCTION_PARAMS
    root = Path(out) / STAKE_PHASE
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"stake-sizing output already exists: {root}")
    for name in ("panels", "traces", "logs"):
        (root / name).mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    planned = len(modes) * len(worlds)
    config = {
        "object_id": OBJECT_ID, "phase": STAKE_PHASE, "launch_sha": launch_sha,
        "git_head": _git_head(), "argv": list(sys.argv if argv is None else argv),
        "controller": STAKE_CONTROLLER, "modes": list(modes), "mode_rules": MODE_RULES,
        "worlds": list(worlds), "horizon": spec.horizon, "policy_seed": spec.policy_seed,
        "workers": spec.workers, "threads": spec.threads, "os_cpu_count": os.cpu_count(),
        "device": "cpu", "action_mode": "deterministic", "planned_episodes": planned,
        "heuristic": heuristic.record(), "params": asdict(params),
        "params_label": params.label, "plan_source": PLAN_SOURCE,
        "recorded_panel": RECORDED_PANEL, "consistency_tolerance": CONSISTENCY_TOLERANCE,
        "trace_timing": TRACE_TIMING,
        "horizon_policy_seed_source": "B01Spec defaults, as b01_ref_a02 config.json spec",
    }
    write_summary(root / "config.json", config)
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "phase": STAKE_PHASE, "status": "INCOMPLETE", "failure": None,
        "launch_sha": launch_sha, "modes": list(modes), "worlds": list(worlds),
        "planned_episodes": planned, "workers": spec.workers, "threads": spec.threads,
        "counts": {"episodes_completed": 0, "steps": 0, "failed_worlds": 0, "new_fits": 0},
        "panels": {}, "artifacts": {"config.json": sha256_file(root / "config.json")},
    }
    write_summary(root / "summary.json", summary)
    _progress(root, {"event": "run_start", "phase": STAKE_PHASE, "modes": list(modes),
                     "worlds": len(worlds), "workers": spec.workers, "threads": spec.threads})
    rows_by_mode: dict[str, list[dict[str, Any]]] = {}
    try:
        for mode in modes:
            _progress(root, {"event": "mode_start", "mode": mode, "worlds": len(worlds)})
            mode_started = time.perf_counter()
            tasks = [StakeTask(seed=seed, params=params, horizon=spec.horizon,
                               policy_seed=spec.policy_seed, threads=spec.threads,
                               heuristic=heuristic, mode=mode, log_dir=str(root / "logs"))
                     for seed in worlds]

            def advance(result, mode=mode):
                row = result["row"]
                summary["counts"]["episodes_completed"] += 1
                summary["counts"]["steps"] += int(row.get("actual_length", 0))
                summary["counts"]["failed_worlds"] += int(bool(row.get("failed")))
                _progress(root, {"event": "world_end", "mode": mode, "seed": row["seed"],
                                 "failed": bool(row.get("failed")),
                                 "qos_per_step": row.get("qos_per_step"),
                                 "wall": row.get("wall_seconds"),
                                 "episodes_completed": summary["counts"]["episodes_completed"]})

            results = run_stake_tasks(tasks, spec.workers, on_result=advance)
            rows = [result["row"] for result in results]
            rows_by_mode[mode] = rows
            panel = {"controller": STAKE_CONTROLLER, "assignment_mode": mode,
                     "assignment_rule": MODE_RULES[mode], "params": asdict(params),
                     "heuristic": heuristic.record(), "worlds": list(worlds), "rows": rows,
                     "aggregate": aggregate(rows),
                     "failed_worlds": [row["seed"] for row in rows if row.get("failed")],
                     "wall_seconds": time.perf_counter() - mode_started}
            panel_path = root / "panels" / f"{mode}.json"
            write_summary(panel_path, panel)
            trace_path = root / "traces" / f"{mode}.npz"
            np.savez_compressed(trace_path, **trace_arrays(results))
            for path in (panel_path, trace_path):
                summary["artifacts"][str(path.relative_to(root))] = sha256_file(path)
            summary["panels"][mode] = {
                "mean_qos_per_step": panel["aggregate"].get("mean_qos_per_step"),
                "mean_raw_native_J": panel["aggregate"].get("mean_raw_native_J"),
                "failed_worlds": panel["failed_worlds"], "wall_seconds": panel["wall_seconds"]}
            write_summary(root / "summary.json", summary)
            _progress(root, {"event": "mode_end", "mode": mode,
                             "wall_seconds": panel["wall_seconds"],
                             "mean_qos_per_step": summary["panels"][mode]["mean_qos_per_step"]})
        summary["readings"] = stake_readings(rows_by_mode, worlds)
        summary["consistency_check"] = consistency_check(
            rows_by_mode["hungarian"], worlds, heuristic, REPO_ROOT / RECORDED_PANEL)
        summary["hungarian_matches_recorded"] = \
            summary["consistency_check"]["hungarian_matches_recorded"]
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        summary.update(wall_seconds=time.perf_counter() - started,
                       peak_rss_kib={"runner": int(own.ru_maxrss),
                                     "largest_worker": int(children.ru_maxrss)},
                       torch_threads_parent=torch.get_num_threads())
        write_summary(root / "summary.json", summary)
        _progress(root, {"event": "run_end", "status": summary["status"],
                         "failure": summary["failure"], "wall_seconds": summary["wall_seconds"]})
