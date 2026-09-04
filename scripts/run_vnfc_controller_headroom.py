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
    OBJECT,
    TARGET_BEAM_WIDTH,
    TARGET_SEED,
    accepted_k256_worlds,
    aggregate_worlds,
    prospective_cost,
    summarize_world,
    target_worlds,
)
from experiments.candidates.variable_n_fleet_churn_headroom.native_backend import (
    run_headroom_fixture,
)


class _ProcessMemoryCountersEx(ctypes.Structure):
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
        ("PrivateUsage", ctypes.c_size_t),
    ]


def peak_rss_bytes() -> int:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ProcessMemoryCountersEx),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = _ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    ok = psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    )
    return int(counters.PeakWorkingSetSize) if ok else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_vnfc_controller_headroom.py")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--preflight-receipt", type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=TARGET_SEED)
    parser.add_argument("--beam-width", type=int, default=TARGET_BEAM_WIDTH)
    parser.add_argument("--max-wall-seconds", type=float, default=2700.0)
    parser.add_argument("--toy", action="store_true")
    parser.add_argument("--capacity-pilot", action="store_true")
    return parser


_TWO_GIB = 2 * 1024 * 1024 * 1024


def _resource_facts(native: dict[str, object], wall_seconds: float) -> dict[str, object]:
    peak = peak_rss_bytes()
    storage = native["search_storage"]  # type: ignore[assignment]
    fixed = int(storage["conservative_fixed_storage_allowance_bytes"])  # type: ignore[index]
    dynamic = int(storage["max_total_owned_bytes_high_water"])  # type: ignore[index]
    conservative_rss_bound = peak + fixed
    return {
        "wall_seconds": wall_seconds,
        "peak_rss_bytes": peak,
        "os_rss_positive": peak > 0,
        "dynamic_search_owned_bytes_high_water": dynamic,
        "conservative_fixed_storage_allowance_bytes": fixed,
        "peak_rss_plus_fixed_allowance_bytes": conservative_rss_bound,
        "strictly_below_2_gib": (
            peak > 0
            and conservative_rss_bound < _TWO_GIB
            and dynamic + fixed < _TWO_GIB
        ),
    }


def _capacity_pilot(args: argparse.Namespace) -> dict[str, object]:
    started = time.perf_counter()
    native = run_headroom_fixture(deterministic_general_episode(1), TARGET_BEAM_WIDTH)
    wall = time.perf_counter() - started
    storage = native["search_storage"]  # type: ignore[assignment]
    depths = native["beam_depths"]  # type: ignore[assignment]
    resource = _resource_facts(native, wall)
    current_filled = max(
        depth["current_frontier"]["nodes_high_water"] for depth in depths  # type: ignore[index]
    ) == TARGET_BEAM_WIDTH
    next_filled = max(
        depth["next_selector"]["nodes_high_water"] for depth in depths  # type: ignore[index]
    ) == TARGET_BEAM_WIDTH
    replacements = int(storage["replacement_count"])  # type: ignore[index]
    capacity_conformant = (
        current_filled
        and next_filled
        and replacements > 0
        and storage["max_current_frontier_capacity"] <= TARGET_BEAM_WIDTH  # type: ignore[index]
        and storage["max_next_selector_capacity"] <= TARGET_BEAM_WIDTH  # type: ignore[index]
        and storage["max_live_nodes_high_water"] <= 2 * TARGET_BEAM_WIDTH + 1  # type: ignore[index]
    )
    if not capacity_conformant:
        branch = "BLOCKED_SEMANTIC_CONFORMANCE"
    elif not resource["strictly_below_2_gib"]:
        branch = "BLOCKED_RESOURCE_ADMISSION"
    else:
        branch = "PILOT_ADMITTED"
    return {
        "object": OBJECT,
        "launch_sha": args.launch_sha,
        "beam_width": TARGET_BEAM_WIDTH,
        "capacity_pilot": True,
        "capacity": {
            "current_frontier_filled": current_filled,
            "next_frontier_filled": next_filled,
            "replacement_count": replacements,
            "max_live_nodes_high_water": storage["max_live_nodes_high_water"],  # type: ignore[index]
            "max_current_frontier_capacity": storage["max_current_frontier_capacity"],  # type: ignore[index]
            "max_next_selector_capacity": storage["max_next_selector_capacity"],  # type: ignore[index]
            "max_total_owned_bytes_high_water": storage["max_total_owned_bytes_high_water"],  # type: ignore[index]
            "fixed_enumerator_scratch_bytes": storage["fixed_enumerator_scratch_bytes"],  # type: ignore[index]
            "conservative_fixed_storage_allowance_bytes": storage["conservative_fixed_storage_allowance_bytes"],  # type: ignore[index]
        },
        "resources": resource,
        "result": {"branch": branch},
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.capacity_pilot:
        if args.toy or args.beam_width != TARGET_BEAM_WIDTH:
            raise ValueError("capacity pilot requires the frozen K=1024 synthetic path")
        return _capacity_pilot(args)
    started = time.perf_counter()
    if args.toy:
        fixtures = ((1, 0, deterministic_general_episode(1)),)
        accepted = {}
    else:
        if (
            args.seed != TARGET_SEED
            or args.beam_width != TARGET_BEAM_WIDTH
            or args.max_wall_seconds != 2700.0
            or args.preflight_receipt is None
        ):
            raise ValueError(
                "result run requires the frozen seed, K=1024, 2700-second cap, and preflight receipt"
            )
        fixtures = target_worlds()
        accepted = accepted_k256_worlds()
    rows: list[dict[str, object]] = []
    timed_out = False
    for zone, row, fixture in fixtures:
        world_started = time.perf_counter()
        native = run_headroom_fixture(fixture, args.beam_width)
        world = summarize_world(
            zone, row, native, accepted.get((zone, row))
        )
        resources = _resource_facts(native, time.perf_counter() - world_started)
        world["resources"] = resources
        world["validity"]["resource"] = resources["strictly_below_2_gib"]  # type: ignore[index]
        world["validity"]["complete"] = (  # type: ignore[index]
            world["validity"]["complete_except_resource"]  # type: ignore[index]
            and resources["strictly_below_2_gib"]
        )
        rows.append(world)
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
        result = {
            "branch": (
                "TOY_COMPLETE"
                if not timed_out and rows[0]["validity"]["complete"]  # type: ignore[index]
                else "INCOMPLETE"
            )
        }
    elif timed_out:
        result = {
            "branch": "MB1024-INCOMPLETE",
            "reason": "machine_time_cap_between_worlds",
        }
    else:
        result = aggregate_worlds(rows)
    return {
        "object": OBJECT,
        "launch_sha": args.launch_sha,
        "seed": args.seed,
        "preflight_receipt": (
            str(args.preflight_receipt) if args.preflight_receipt is not None else None
        ),
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
        "resources": {
            "wall_seconds": wall,
            "peak_rss_bytes": peak_rss_bytes(),
            "all_world_resource_checks_passed": all(
                world["validity"]["resource"] for world in rows  # type: ignore[index]
            ),
        },
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


def _render_with_final_resources(
    summary: dict[str, object], started: float
) -> str:
    # The first render makes the full literal BCRH record surface resident before
    # the process high-water measurement used by the final resource decision.
    json.dumps(summary, indent=2, sort_keys=True)
    peak = peak_rss_bytes()
    resources = summary.setdefault("resources", {})  # type: ignore[assignment]
    resources["peak_rss_bytes"] = peak  # type: ignore[index]
    resources["wall_seconds"] = time.perf_counter() - started  # type: ignore[index]
    worlds = summary.get("worlds", ())
    if worlds:
        fixed = max(
            int(world["search_storage"]["conservative_fixed_storage_allowance_bytes"])
            for world in worlds  # type: ignore[index]
        )
        dynamic = max(
            int(world["search_storage"]["max_total_owned_bytes_high_water"])
            for world in worlds  # type: ignore[index]
        )
        resource_valid = (
            peak > 0
            and peak + fixed < _TWO_GIB
            and dynamic + fixed < _TWO_GIB
        )
        for world in worlds:  # type: ignore[assignment]
            world["resources"]["peak_rss_bytes"] = peak
            world["resources"]["os_rss_positive"] = peak > 0
            world["resources"]["peak_rss_plus_fixed_allowance_bytes"] = peak + fixed
            world["resources"]["strictly_below_2_gib"] = resource_valid
            world["validity"]["resource"] = resource_valid
            world["validity"]["complete"] = (
                world["validity"]["complete_except_resource"] and resource_valid
            )
        resources["all_world_resource_checks_passed"] = resource_valid  # type: ignore[index]
        if (
            not summary.get("toy")
            and summary["result"]["branch"] != "MB1024-INCOMPLETE"  # type: ignore[index]
        ):
            summary["result"] = aggregate_worlds(worlds)  # type: ignore[arg-type]
    return json.dumps(summary, indent=2, sort_keys=True) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.output_root.exists():
        raise FileExistsError(f"final result destination already exists: {args.output_root}")
    args.output_root.mkdir(parents=True)
    started = time.perf_counter()
    try:
        summary = run(args)
    except Exception as error:
        incomplete = "INCOMPLETE" if args.toy or args.capacity_pilot else "MB1024-INCOMPLETE"
        summary = {
            "object": OBJECT,
            "launch_sha": args.launch_sha,
            "seed": args.seed,
            "result": {
                "branch": incomplete,
                "reason": f"{type(error).__name__}: {error}",
            },
            "resources": {
                "wall_seconds": time.perf_counter() - started,
                "peak_rss_bytes": peak_rss_bytes(),
            },
        }
    rendered = (
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
        if args.capacity_pilot or "worlds" not in summary
        else _render_with_final_resources(summary, started)
    )
    (args.output_root / "summary.json").write_text(rendered, encoding="utf-8")
    return (
        0
        if summary["result"]["branch"]  # type: ignore[index]
        not in (
            "INCOMPLETE",
            "MB1024-INCOMPLETE",
            "BLOCKED_RESOURCE_ADMISSION",
            "BLOCKED_SEMANTIC_CONFORMANCE",
        )
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
