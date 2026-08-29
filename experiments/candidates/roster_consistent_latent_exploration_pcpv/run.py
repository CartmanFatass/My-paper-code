"""One-shot staged CLI for RCLE-PCPV R02."""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import subprocess
import time
import traceback
from typing import Callable, Iterable

from .config import (
    CHURN_CELLS, CLAMP_EPISODES, EVAL_CELLS, HORIZON, LEARNED_ARMS,
    GAMMA_GLOBAL, MAX_EPISODES, MAX_TICKS, NATURAL_EVAL_EPISODES,
    REGISTERED_TAILS, RESULT_ROOT_PARTS, RNG_DOMAIN, ROOT_LABELS,
    SCIENCE_REVISION, SCRIPTED_EPISODES, SCRIPTED_PACKAGES, T_CRITICAL,
    TRAIN_CELLS, TRAIN_EPISODES, cell_name,
)
from .inference import complete_inference, stage_a_inference
from .models import paired_policies, parameter_count
from .scripted import run_scripted_episode
from .training import rollout, train_arm


class WallLimitExceeded(RuntimeError):
    pass


class WallDeadline:
    """Acceptance-critical monotonic deadline with an injectable fixture clock."""

    def __init__(self, max_seconds: float, clock: Callable[[], float] = time.monotonic,
                 start: float | None = None):
        if not math.isfinite(max_seconds) or max_seconds <= 0.0:
            raise ValueError("max wall seconds must be finite and positive")
        self.clock = clock
        self.start = clock() if start is None else start
        self.limit = self.start + max_seconds

    def check(self) -> None:
        if self.clock() >= self.limit:
            raise WallLimitExceeded("monotonic wall deadline reached")

    def remaining(self) -> float:
        return max(0.0, self.limit - self.clock())


class WorkCounter:
    """Literal stage-aware episode/tick accounting enforcer."""

    def __init__(self):
        self.episodes = 0
        self.ticks = 0

    def add(self, episodes: int) -> None:
        if episodes < 0:
            raise ValueError("negative work")
        self.episodes += episodes
        self.ticks += episodes * HORIZON
        if self.episodes > MAX_EPISODES or self.ticks > MAX_TICKS:
            raise RuntimeError("frozen maximum work exceeded")

    def require(self, expected_episodes: int) -> None:
        if self.episodes != expected_episodes or self.ticks != expected_episodes * HORIZON:
            raise RuntimeError(
                f"work mismatch: {self.episodes}/{self.ticks}, expected "
                f"{expected_episodes}/{expected_episodes * HORIZON}")


def validate_output_path(output: str | Path, cwd: str | Path | None = None) -> Path:
    base = Path.cwd() if cwd is None else Path(cwd)
    resolved = (base / output).resolve() if not Path(output).is_absolute() else Path(output).resolve()
    allowed = base.resolve().joinpath(*RESULT_ROOT_PARTS)
    if resolved.parent != allowed or resolved.name != "result.json":
        raise ValueError(f"output must be exactly {allowed / 'result.json'}")
    return resolved


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _mean_endpoint(sums: dict[str, float], count: int) -> dict[str, float]:
    return {key: value / count for key, value in sums.items()}


def _stage_a_root(args):
    root, absolute_deadline = args
    deadline = WallDeadline(1.0, start=absolute_deadline - 1.0)
    deadline.limit = absolute_deadline
    panel = {}
    hashes = {}
    for package in SCRIPTED_PACKAGES:
        package_panel = {}
        for cell in EVAL_CELLS:
            sums = {"tau": 0.0, "U": 0.0, "F": 0.0, "Y": 0.0}
            for scenario in range(512):
                deadline.check()
                result, event_hash = run_scripted_episode(package, root, cell,
                                                           scenario)
                for key in sums:
                    sums[key] += result[key]
                if package in {"CARRY", "REPLAN"}:
                    hashes[(package, cell, scenario)] = event_hash
            package_panel[cell_name(cell)] = _mean_endpoint(sums, 512)
        panel[package] = package_panel
    mismatches = sum(
        hashes[("CARRY", cell, scenario)] != hashes[("REPLAN", cell, scenario)]
        for cell in EVAL_CELLS for scenario in range(512)
    )
    return ROOT_LABELS[root], panel, mismatches


def _evaluate(policy, arm, root, cells, clamp, absolute_deadline):
    deadline = WallDeadline(1.0, start=absolute_deadline - 1.0)
    deadline.limit = absolute_deadline
    out = {}
    import torch
    with torch.no_grad():
        for cell in cells:
            sums = {"tau": 0.0, "U": 0.0, "F": 0.0, "Y": 0.0}
            for scenario in range(512):
                deadline.check()
                result, _ = rollout(policy, arm, root, cell, scenario,
                                    "stage-b-evaluation", clamp=clamp)
                for key in sums:
                    sums[key] += result[key]
            out[cell_name(cell)] = _mean_endpoint(sums, 512)
    return out


def _stage_b_root(args):
    root, absolute_deadline = args
    import torch
    torch.set_num_threads(1)
    deadline = WallDeadline(1.0, start=absolute_deadline - 1.0)
    deadline.limit = absolute_deadline
    keep, flex = paired_policies(root)
    if parameter_count(keep) != 26_545 or parameter_count(flex) != 26_545:
        raise RuntimeError("architecture parameter count changed")
    training = {
        "KEEP": train_arm(keep, "KEEP", root, deadline),
        "FLEX": train_arm(flex, "FLEX", root, deadline),
    }
    panel = {
        "KEEP": _evaluate(keep, "KEEP", root, EVAL_CELLS, False,
                          absolute_deadline),
        "FLEX": _evaluate(flex, "FLEX", root, EVAL_CELLS, False,
                          absolute_deadline),
        "CLAMP": _evaluate(flex, "FLEX", root, CHURN_CELLS, True,
                           absolute_deadline),
    }
    return ROOT_LABELS[root], panel, training


def _parallel_map(function, arguments, workers: int, deadline: WallDeadline):
    if workers == 1:
        return [function(argument) for argument in arguments]
    context = mp.get_context("spawn")
    pool = context.Pool(processes=workers)
    try:
        pending = pool.map_async(function, arguments)
        results = pending.get(timeout=deadline.remaining())
        pool.close()
        pool.join()
        return results
    except mp.TimeoutError as error:
        pool.terminate()
        pool.join()
        raise WallLimitExceeded("parallel stage exceeded monotonic deadline") from error
    except BaseException:
        pool.terminate()
        pool.join()
        raise


def _git_identity() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True,
            text=True).stdout.strip()
    except Exception:
        return "UNAVAILABLE"


def _rss_bytes() -> int | None:
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss + sum(
            child.memory_info().rss for child in process.children(recursive=True)
            if child.is_running())
    except Exception:
        return None


def _training_complete(training: dict) -> bool:
    if set(training) != set(ROOT_LABELS):
        return False
    for root in ROOT_LABELS:
        if set(training[root]) != set(LEARNED_ARMS):
            return False
        for arm in LEARNED_ARMS:
            facts = training[root][arm]
            if facts.get("updates") != 256 or facts.get("episodes") != 8192:
                return False
    return True


def _endpoint_complete(value: object) -> bool:
    return (isinstance(value, dict) and set(value) == {"tau", "U", "F", "Y"}
            and all(isinstance(x, (int, float)) and math.isfinite(float(x))
                    for x in value.values()))


def _stage_a_panel_complete(panel: dict) -> bool:
    if set(panel) != set(ROOT_LABELS):
        return False
    expected_cells = {cell_name(cell) for cell in EVAL_CELLS}
    for root in ROOT_LABELS:
        if set(panel[root]) != set(SCRIPTED_PACKAGES):
            return False
        for package in SCRIPTED_PACKAGES:
            cells = panel[root][package]
            if set(cells) != expected_cells or not all(
                    _endpoint_complete(value) for value in cells.values()):
                return False
    return True


def _stage_b_panel_complete(panel: dict) -> bool:
    if set(panel) != set(ROOT_LABELS):
        return False
    natural_cells = {cell_name(cell) for cell in EVAL_CELLS}
    clamp_cells = {cell_name(cell) for cell in CHURN_CELLS}
    for root in ROOT_LABELS:
        if set(panel[root]) != {"KEEP", "FLEX", "CLAMP"}:
            return False
        for arm in LEARNED_ARMS:
            cells = panel[root][arm]
            if set(cells) != natural_cells or not all(
                    _endpoint_complete(value) for value in cells.values()):
                return False
        cells = panel[root]["CLAMP"]
        if set(cells) != clamp_cells or not all(
                _endpoint_complete(value) for value in cells.values()):
            return False
    return True


def _conformance(
    *, mismatch_count: int, observed_tails: int, expected_tails: int,
    work: WorkCounter, expected_work: int, stage_b_reached: bool,
    reached_stage_complete: bool, training: dict | None = None,
) -> dict:
    counts_pass = (work.episodes == expected_work and
                   work.ticks == expected_work * HORIZON)
    if stage_b_reached:
        counts_pass = counts_pass and training is not None and _training_complete(training)
    checks = {
        "event_state_hash_equality": {
            "mismatches": mismatch_count, "pass": mismatch_count == 0,
        },
        "frozen_counts": {
            "stage_a_episodes": SCRIPTED_EPISODES,
            "stage_b_training_episodes": TRAIN_EPISODES if stage_b_reached else None,
            "stage_b_natural_evaluation_episodes": (
                NATURAL_EVAL_EPISODES if stage_b_reached else None),
            "stage_b_clamp_evaluation_episodes": (
                CLAMP_EPISODES if stage_b_reached else None),
            "pass": bool(counts_pass),
        },
        "registered_tails": {
            "observed": observed_tails, "expected_reached": expected_tails,
            "pass": observed_tails == expected_tails,
        },
        "architecture": {
            "scalars_per_arm": 26_545, "dtype": "float64",
            "pass": True,
        },
        "rng_domain": {
            "observed": RNG_DOMAIN, "expected": "RCLE-PCPV-R02-20260829",
            "root_count": len(ROOT_LABELS),
            "pass": (RNG_DOMAIN == "RCLE-PCPV-R02-20260829" and
                     ROOT_LABELS == tuple(
                         f"RCLE-PCPV-R02-ROOT-{i:02d}" for i in range(16))),
        },
        "reached_stage_completeness": {
            "stage_b_reached": stage_b_reached,
            "pass": reached_stage_complete,
        },
        "work_equality": {
            "observed_episodes": work.episodes,
            "expected_episodes": expected_work,
            "observed_ticks": work.ticks,
            "expected_ticks": expected_work * HORIZON,
            "pass": (work.episodes == expected_work and
                     work.ticks == expected_work * HORIZON),
        },
    }
    checks["all_pass"] = all(
        value["pass"] for value in checks.values() if isinstance(value, dict)
    )
    return checks


def _invalid_conformance(reason: str, work: WorkCounter) -> dict:
    return {
        "event_state_hash_equality": {"mismatches": None, "pass": False},
        "frozen_counts": {"pass": False},
        "registered_tails": {"observed": None, "expected_reached": None,
                             "pass": False},
        "architecture": {"scalars_per_arm": 26_545, "dtype": "float64",
                         "pass": True},
        "rng_domain": {"observed": RNG_DOMAIN,
                       "expected": "RCLE-PCPV-R02-20260829", "pass": True},
        "reached_stage_completeness": {"reason": reason, "pass": False},
        "work_equality": {"observed_episodes": work.episodes,
                          "observed_ticks": work.ticks, "pass": False},
        "all_pass": False,
    }


def execute(workers: int, max_wall_seconds: float, output: Path) -> dict:
    if workers < 1 or workers > 4:
        raise ValueError("workers must be in [1,4]")
    started_wall = time.time()
    started_mono = time.monotonic()
    deadline = WallDeadline(max_wall_seconds, start=started_mono)
    work = WorkCounter()
    base = {
        "science_revision": SCIENCE_REVISION,
        "source_commit": _git_identity(),
        "stage_request": "all",
        "workers": workers,
        "max_wall_seconds": max_wall_seconds,
        "started_unix_seconds": started_wall,
        "frozen_contract": {
            "rng_domain": RNG_DOMAIN,
            "root_labels": ROOT_LABELS,
            "training_cells": [cell_name(cell) for cell in TRAIN_CELLS],
            "evaluation_cells": [cell_name(cell) for cell in EVAL_CELLS],
            "registered_one_sided_tails": REGISTERED_TAILS,
            "student_t_critical": T_CRITICAL,
            "gamma_global": GAMMA_GLOBAL,
            "maximum_episodes": MAX_EPISODES,
            "maximum_ticks": MAX_TICKS,
            "tensor_scalars_per_arm": 26_545,
            "dtype": "float64",
        },
    }
    try:
        stage_a_rows = _parallel_map(
            _stage_a_root, [(root, deadline.limit) for root in range(16)],
            workers, deadline)
        stage_a_panel = {root: panel for root, panel, _ in stage_a_rows}
        stage_a_complete = _stage_a_panel_complete(stage_a_panel)
        mismatch_count = sum(mismatches for _, _, mismatches in stage_a_rows)
        work.add(SCRIPTED_EPISODES)
        work.require(SCRIPTED_EPISODES)
        stage_a_stats = stage_a_inference(stage_a_panel)
        stage_a_conformance = _conformance(
            mismatch_count=mismatch_count,
            observed_tails=len(stage_a_stats["tails"]), expected_tails=32,
            work=work, expected_work=SCRIPTED_EPISODES,
            stage_b_reached=False, reached_stage_complete=stage_a_complete)
        stage_a_valid = stage_a_conformance["all_pass"]
        stage_a = {
            "status": "COMPLETE", "episodes": SCRIPTED_EPISODES,
            "ticks": SCRIPTED_EPISODES * HORIZON,
            "event_state_hash_mismatches": mismatch_count,
            "root_cell_package_endpoints": stage_a_panel,
            "inference": stage_a_stats,
        }
        gates_pass = (stage_a_valid and stage_a_stats["assay_sensitivity"] and
                      stage_a_stats["public_scaffold"] and
                      stage_a_stats["physical_persistence_opportunity"])
        if not gates_pass:
            branch = (stage_a_stats["branch"] if stage_a_valid else
                      "INVALID_OR_INCOMPLETE")
            downstream_status = ("PROSPECTIVELY_NOT_REQUIRED" if stage_a_valid
                                 else "INVALID_OR_INCOMPLETE")
            result = {**base, "terminal_status": "COMPLETE",
                      "technical_validity": "VALID" if stage_a_valid else "INVALID",
                      "downstream_status": downstream_status,
                      "stage_a": stage_a, "branch": branch,
                      "conformance": stage_a_conformance,
                      "accounting": {"episodes": work.episodes, "ticks": work.ticks}}
        else:
            stage_b_rows = _parallel_map(
                _stage_b_root, [(root, deadline.limit) for root in range(16)],
                workers, deadline)
            learned_panel = {root: panel for root, panel, _ in stage_b_rows}
            training = {root: facts for root, _, facts in stage_b_rows}
            stage_b_complete = (_stage_b_panel_complete(learned_panel) and
                                _training_complete(training))
            work.add(TRAIN_EPISODES + NATURAL_EVAL_EPISODES + CLAMP_EPISODES)
            work.require(MAX_EPISODES)
            inference = complete_inference(
                stage_a_panel, learned_panel,
                stage_a_stats["physical_winning_paths"], valid=True)
            complete_conformance = _conformance(
                mismatch_count=mismatch_count,
                observed_tails=len(inference["tails"]), expected_tails=70,
                work=work, expected_work=MAX_EPISODES,
                stage_b_reached=True, reached_stage_complete=stage_b_complete,
                training=training)
            result = {
                **base, "terminal_status": "COMPLETE",
                "technical_validity": ("VALID" if complete_conformance["all_pass"]
                                       else "INVALID"),
                "downstream_status": ("COMPLETE" if complete_conformance["all_pass"]
                                      else "INVALID_OR_INCOMPLETE"),
                "stage_a": stage_a,
                "stage_b": {
                    "status": "COMPLETE",
                    "training_episodes": TRAIN_EPISODES,
                    "natural_evaluation_episodes": NATURAL_EVAL_EPISODES,
                    "clamp_evaluation_episodes": CLAMP_EPISODES,
                    "root_training_facts": training,
                    "root_cell_arm_endpoints": learned_panel,
                    "inference": inference,
                },
                "branch": (inference["branch"] if complete_conformance["all_pass"]
                           else "INVALID_OR_INCOMPLETE"),
                "conformance": complete_conformance,
                "accounting": {"episodes": work.episodes, "ticks": work.ticks},
            }
        result["runtime"] = {
            "wall_seconds": time.monotonic() - started_mono,
            "finished_unix_seconds": time.time(),
            "terminal_process_group_working_set_bytes_observed": _rss_bytes(),
        }
        deadline.check()
        return result
    except BaseException as error:
        return {
            **base,
            "terminal_status": "WALL_STOP" if isinstance(error, WallLimitExceeded)
            else "EXCEPTION",
            "technical_validity": "INVALID",
            "downstream_status": "INVALID_OR_INCOMPLETE",
            "branch": "INVALID_OR_INCOMPLETE",
            "accounting": {"episodes": work.episodes, "ticks": work.ticks},
            "conformance": _invalid_conformance(str(error), work),
            "runtime": {"wall_seconds": time.monotonic() - started_mono,
                        "finished_unix_seconds": time.time(),
                        "terminal_process_group_working_set_bytes_observed": _rss_bytes()},
            "error": {"type": type(error).__name__, "message": str(error),
                      "traceback": traceback.format_exc(limit=20)},
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("all",), required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--max-wall-seconds", type=float, required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = validate_output_path(args.output)
    result = execute(args.workers, args.max_wall_seconds, output)
    atomic_json(output, result)
    return 0 if (result["terminal_status"] == "COMPLETE" and
                 result["technical_validity"] == "VALID") else 2


if __name__ == "__main__":
    raise SystemExit(main())
