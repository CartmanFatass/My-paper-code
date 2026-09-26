"""Per-checkpoint evaluation of a B02 learner with the B01 evaluator (controller ``L``).

Production shield (0, .05); per mode one panel ``L_c{ii}_{mode}_e0.00_x0.05``: ``deterministic``
(the B07 mean-action route) and ``stochastic`` (draw 0 of B01's ``sample_seed(policy_seed,
world, draw)`` with ``policy_seed`` = the checkpoint's training seed).  Rows carry B01's world
readings, mechanism readings and the five position diagnostics; traces as B01's.  Output under
``<run>/checkpoint-eval/`` (development) or ``<run>/checkpoint-eval/final/`` (hold-out).
"""

from __future__ import annotations

import json
import os
import resource
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import sha256_file
from experiments.candidates.uav_service_auxiliary.b09.persistence import (
    append_progress, write_summary,
)

from ..b01.evaluation import (
    ACTION_MODES, L_CONTROLLER_INFORMATION, SAMPLE_SEED_RULE, TRACE_TIMING, WorldTask, aggregate,
    run_tasks, trace_arrays,
)
from ..b01.feedback import PRODUCTION_PARAMS
from .configuration import OBJECT_ID, PROGRAMME

DEVELOPMENT_WORLDS = tuple(range(955001, 955033))
HOLDOUT_WORLDS = tuple(range(957001, 957033))   # read once, for the frozen final model only
STOCHASTIC_DRAW = 0
HORIZON = 3000


def parse_worlds(value: str) -> tuple[int, ...]:
    """``955001-955032`` or a comma list of ints / ranges."""
    worlds: list[int] = []
    for part in (item.strip() for item in str(value).split(",")):
        if not part:
            continue
        if "-" in part:
            start, stop = (int(x) for x in part.split("-", 1))
            if stop < start:
                raise ValueError(f"empty world range {part}")
            worlds.extend(range(start, stop + 1))
        else:
            worlds.append(int(part))
    if not worlds or len(set(worlds)) != len(worlds):
        raise ValueError("worlds must be a non-empty list without repeats")
    return tuple(worlds)


def check_worlds(worlds: Iterable[int], final: bool) -> None:
    worlds = tuple(int(w) for w in worlds)
    held = [w for w in worlds if w in HOLDOUT_WORLDS]
    if held and not final:
        raise ValueError(f"worlds {held[:3]}... are the once-read hold-out 957001-957032; "
                         "pass --final to read them")
    if final and len(held) != len(worlds):
        raise ValueError("--final evaluates only the hold-out worlds 957001-957032")


def read_record(checkpoint_dir: Path) -> dict[str, Any]:
    checkpoint_dir = Path(checkpoint_dir)
    record = json.loads((checkpoint_dir / "record.json").read_text(encoding="utf-8"))
    if record.get("object_id") != OBJECT_ID or record.get("programme") != PROGRAMME:
        raise ValueError("record.json is not a B02 checkpoint record")
    if record.get("checkpoint") != checkpoint_dir.name:
        raise ValueError(f"record names {record.get('checkpoint')}, directory is {checkpoint_dir.name}")
    return record


def panel_name(checkpoint: str, mode: str) -> str:
    return f"L_{checkpoint}_{mode}_{PRODUCTION_PARAMS.label}"


def evaluate_checkpoint(*, checkpoint_dir: Path, out: Path, worlds: Iterable[int],
                        modes: Iterable[str], final: bool, launch_sha: str, workers: int = 1,
                        threads: int = 2, device_name: str = "cpu", horizon: int = HORIZON,
                        argv=None) -> dict[str, Any]:
    worlds = tuple(int(w) for w in worlds)
    modes = tuple(modes)
    check_worlds(worlds, final)
    if not modes or len(set(modes)) != len(modes) or any(m not in ACTION_MODES for m in modes):
        raise ValueError(f"modes must be distinct values from {ACTION_MODES}")
    if workers < 1 or threads < 1 or workers * threads > (os.cpu_count() or 1):
        raise ValueError("workers x threads must be positive and within os.cpu_count()")
    checkpoint_dir = Path(checkpoint_dir)
    record = read_record(checkpoint_dir)
    agent_pt = checkpoint_dir / record["agent_pt"]
    if sha256_file(agent_pt) != record["agent_pt_sha256"]:
        raise ValueError("agent.pt sha256 differs from record.json")
    checkpoint = record["checkpoint"]
    policy_seed = int(record["training_seed"])
    root = Path(out) / "checkpoint-eval" / ("final" if final else "")
    run_dir = root / f"{checkpoint}_{'-'.join(modes)}"
    names = {mode: panel_name(checkpoint, mode) for mode in modes}
    existing = [p for p in [run_dir / "summary.json",
                            *(root / "panels" / f"{n}.json" for n in names.values()),
                            *(root / "traces" / f"{n}.npz" for n in names.values())] if p.exists()]
    if existing:
        raise FileExistsError(f"checkpoint evaluation output already exists: {existing}")
    for sub in (run_dir, root / "panels", root / "traces", root / "logs"):
        sub.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "programme": PROGRAMME, "status": "INCOMPLETE", "failure": None,
        "launch_sha": launch_sha, "checkpoint": checkpoint, "policy_seed": policy_seed,
        "final": bool(final), "worlds": list(worlds), "modes": list(modes),
        "counts": {"episodes_completed": 0, "steps": 0, "panels_completed": 0,
                   "failed_worlds": 0},
        "panels": {}, "artifacts": {},
    }
    write_summary(run_dir / "config.json", {
        "object_id": OBJECT_ID, "programme": PROGRAMME, "launch_sha": launch_sha,
        "argv": list(sys.argv if argv is None else argv), "checkpoint_dir": str(checkpoint_dir),
        "record": record, "worlds": list(worlds), "final": bool(final), "modes": list(modes),
        "panel_names": names, "feedback": asdict(PRODUCTION_PARAMS), "horizon": int(horizon),
        "policy_seed": policy_seed, "stochastic_draw": STOCHASTIC_DRAW,
        "sample_seed_rule": SAMPLE_SEED_RULE, "trace_timing": TRACE_TIMING,
        "controller_information": L_CONTROLLER_INFORMATION, "device": device_name,
        "workers": int(workers), "threads": int(threads), "os_cpu_count": os.cpu_count()})
    summary["artifacts"]["config.json"] = sha256_file(run_dir / "config.json")
    write_summary(run_dir / "summary.json", summary)
    try:
        for mode in modes:
            name = names[mode]
            draw = STOCHASTIC_DRAW if mode == "stochastic" else None
            panel_started = time.perf_counter()
            tasks = [WorldTask(
                controller="L", seed=seed, params=PRODUCTION_PARAMS, horizon=int(horizon),
                policy_seed=policy_seed, threads=int(threads), device=device_name,
                checkpoint=str(agent_pt), expected_checkpoint_sha256=record["agent_pt_sha256"],
                expected_policy_fingerprint=record["policy_fingerprint"],
                log_dir=str(root / "logs"), action_mode=mode, draw=draw,
                checkpoint_record=str(checkpoint_dir / "record.json")) for seed in worlds]

            def advance(result, name=name):
                row = result["row"]
                summary["counts"]["episodes_completed"] += 1
                summary["counts"]["steps"] += int(row.get("actual_length", 0))
                summary["counts"]["failed_worlds"] += int(bool(row.get("failed")))
                append_progress(run_dir, {"event": "world_end", "panel": name, "seed": row["seed"],
                                          "failed": bool(row.get("failed"))},
                                dict(summary["counts"]))

            results = run_tasks(tasks, workers, on_result=advance)
            rows = [result["row"] for result in results]
            identities = {json.dumps(result["identity"], sort_keys=True) for result in results}
            panel = {"name": name, "controller": "L", "checkpoint": checkpoint,
                     "rollout": record["rollout"], "transitions": record["transitions"],
                     "controller_information": L_CONTROLLER_INFORMATION,
                     "params": asdict(PRODUCTION_PARAMS), "action_mode": mode,
                     "draw": draw, "policy_seed": policy_seed, "final": bool(final),
                     "worlds": rows, "aggregate": aggregate(rows),
                     "failed_worlds": [row["seed"] for row in rows if row.get("failed")],
                     "policy_identity": [json.loads(item) for item in sorted(identities)],
                     "wall_seconds": time.perf_counter() - panel_started}
            if draw is not None:
                panel["sample_seeds"] = {str(row["seed"]): row.get("sample_seed") for row in rows}
            panel_path = root / "panels" / f"{name}.json"
            trace_path = root / "traces" / f"{name}.npz"
            write_summary(panel_path, panel)
            np.savez_compressed(trace_path, **trace_arrays(results))
            for path in (panel_path, trace_path):
                summary["artifacts"][str(path.relative_to(root))] = sha256_file(path)
            summary["panels"][name] = {key: panel[key] for key in panel if key != "worlds"}
            summary["counts"]["panels_completed"] += 1
            write_summary(run_dir / "summary.json", summary)
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
        write_summary(run_dir / "summary.json", summary)
