"""Run the frozen VNFC controller-headroom A/RECON object."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys
import time
from typing import Sequence

if __name__ == "__main__":
    _ROOT = str(Path(__file__).resolve().parents[1])
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import (
    deterministic_general_episode,
)
from experiments.candidates.variable_n_fleet_churn_headroom.analysis import (
    TARGET_BEAM_WIDTH,
    TARGET_SEED,
    aggregate_worlds,
    prospective_cost,
    summarize_world,
    target_worlds,
)
from experiments.candidates.variable_n_fleet_churn_headroom.native_backend import (
    run_headroom_fixture,
)


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def peak_rss_bytes() -> int:
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(  # type: ignore[attr-defined]
        ctypes.windll.kernel32.GetCurrentProcess(),  # type: ignore[attr-defined]
        ctypes.byref(counters),
        counters.cb,
    )
    return int(counters.PeakWorkingSetSize) if ok else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_vnfc_controller_headroom.py")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--preflight-receipt", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=TARGET_SEED)
    parser.add_argument("--beam-width", type=int, default=TARGET_BEAM_WIDTH)
    parser.add_argument("--max-wall-seconds", type=float, default=2700.0)
    parser.add_argument("--toy", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict[str, object]:
    started = time.perf_counter()
    if args.toy:
        fixtures = ((1, 0, deterministic_general_episode(1)),)
    else:
        if args.seed != TARGET_SEED or args.beam_width != 256 or args.max_wall_seconds != 2700.0:
            raise ValueError("result run requires the frozen seed, K=256, and 2700-second cap")
        fixtures = target_worlds()
    rows: list[dict[str, object]] = []
    timed_out = False
    for zone, row, fixture in fixtures:
        rows.append(
            summarize_world(
                zone,
                row,
                run_headroom_fixture(fixture, args.beam_width),
            )
        )
        if time.perf_counter() - started >= args.max_wall_seconds:
            timed_out = True
            break
    wall = time.perf_counter() - started
    actual = {
        "beam_expansions": sum(
            depth["expansions"] for world in rows for depth in world["beam_depths"]  # type: ignore[index]
        ),
        "beam_native_ticks": sum(
            depth["native_ticks"] for world in rows for depth in world["beam_depths"]  # type: ignore[index]
        ),
        "persistent_candidates": sum(world["counts"]["persist_candidates"] for world in rows),  # type: ignore[index]
        "persistent_native_ticks": sum(world["counts"]["persist_native_ticks"] for world in rows),  # type: ignore[index]
        "bcrh_decision_calls": sum(world["counts"]["bcrh_decision_calls"] for world in rows),  # type: ignore[index]
        "bcrh_scored_candidates": sum(
            decision["candidate_count"]
            for world in rows
            for decision in world["bcrh_decisions"]  # type: ignore[index]
        ),
        "terminal_completion_native_ticks": sum(
            world["counts"]["terminal_completion_native_ticks"] for world in rows  # type: ignore[index]
        ),
    }
    if args.toy:
        result = {"branch": "TOY_COMPLETE" if not timed_out and rows[0]["validity"]["complete"] else "INCOMPLETE"}  # type: ignore[index]
    elif timed_out:
        result = {"branch": "INCOMPLETE", "reason": "machine_time_cap_between_worlds"}
    else:
        result = aggregate_worlds(rows)
    return {
        "object": "VNFC-CONTROLLER-HEADROOM-A-RECON-R01",
        "launch_sha": args.launch_sha,
        "seed": args.seed,
        "preflight_receipt": str(args.preflight_receipt),
        "beam_width": args.beam_width,
        "max_wall_seconds": args.max_wall_seconds,
        "toy": bool(args.toy),
        "prospective_cost": prospective_cost(args.beam_width, len(fixtures)),
        "actual_cost": actual,
        "exposure": {
            "learner_parameters": 0,
            "model_initialisations": 0,
            "optimizer_steps": 0,
            "training_transitions": 0,
            "checkpoints": 0,
            "parameter_displacement": "not applicable (A/RECON, no learner)",
        },
        "resources": {"wall_seconds": wall, "peak_rss_bytes": peak_rss_bytes()},
        "measured_cost": {
            "wall_seconds_per_completed_world": wall / len(rows) if rows else None,
            "wall_seconds_per_beam_expansion": (
                wall / actual["beam_expansions"] if actual["beam_expansions"] else None
            ),
            "measurement_source": "this_invocation",
            "measurement_is_result_blind_prelaunch_calibration": False,
        },
        "completed_worlds": len(rows),
        "worlds": rows,
        "result": result,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.output_root.exists():
        raise FileExistsError(f"final result destination already exists: {args.output_root}")
    args.output_root.mkdir(parents=True)
    started = time.perf_counter()
    try:
        summary = run(args)
    except Exception as error:
        summary = {
            "object": "VNFC-CONTROLLER-HEADROOM-A-RECON-R01",
            "launch_sha": args.launch_sha,
            "seed": args.seed,
            "result": {"branch": "INCOMPLETE", "reason": f"{type(error).__name__}: {error}"},
            "resources": {
                "wall_seconds": time.perf_counter() - started,
                "peak_rss_bytes": peak_rss_bytes(),
            },
        }
    (args.output_root / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if summary["result"]["branch"] not in ("INCOMPLETE",) else 2  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())
