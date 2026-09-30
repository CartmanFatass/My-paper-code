#!/usr/bin/env python3
"""Cell b04 runner (coupled_host_joint_skills_stage1): arm B0, lawful sensing from spawn, zero fits.

Per world (``b04_lawful_sensing.run_world_b04``): (1) regression rollout of the frozen planner
with the global map on a fresh static host, asserted equal to the sealed gate record
``<gate-run>/worlds/<w>.json`` (relay layout, whole C_bh series, all-500 and final-100 means;
file sha256 recorded); (2) arm B0 on its own fresh static host.  Stakes: ``s_info0 = F - B0``
(all-500 C_bh) and ``s_info0_final100`` (final-100), F = the gate closed-loop P_relay values.

Writes ``worlds/<world>.json`` and ``summary.json`` (per-world rows; paired mean/SD/min/max/n/
n_positive; cpu_seconds, wall_clock_s, git_head, launch_sha, arguments, interpreter,
definitions).  Admission as in ``coupled_host_replan_timing/run_r2.py``; a direct invocation
records ``admission = absent``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.coupled_host_joint_skills_stage1.run_gate import (  # noqa: E402
    _cpu_seconds,
    _git,
    _mean_sd,
    _utc_now,
    parse_worlds,
    write_json,
)
from experiments.candidates.coupled_host_replan_timing.run_r1lite import (  # noqa: E402
    ADMISSION_ENV,
    canonical_data_root,
    resolve_out,
    timed,
)

SCHEMA = 1
DIRECTION = "coupled_host_joint_skills_stage1"
DEFAULT_GATE_RUN = Path("runs") / DIRECTION / "b01_gate_dev_a01"
STAKES = ("s_info0", "s_info0_final100")
B0_ROW_KEYS = ("all_mean", "final_100_mean", "users_known", "clusters_known", "never_seen_clusters",
               "never_seen_users", "replans", "trigger_steps", "evaluations_used", "cap_hit",
               "cap_hit_trigger_steps", "hold_steps_before_first_plan", "views_over_obs_cap",
               "cpu_s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_b04.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--worlds", nargs="+", default=["1000-1031"],
                        help="world (reset) seeds: integers and inclusive ranges a-b")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--budget", type=int, default=3000,
                        help="static-evaluation ceiling per planner search (flat and relay each)")
    parser.add_argument("--probe", type=int, default=None, help="run only the first N worlds")
    parser.add_argument("--launch-sha", default=None, help="published source sha of this launch")
    parser.add_argument("--area-size", type=int, default=5000)
    parser.add_argument("--max-replans", type=int, default=None,
                        help="cap on planner calls per world, the first plan included "
                             "(default: b04_lawful_sensing.MAX_REPLANS)")
    parser.add_argument("--gate-run", type=Path, default=DEFAULT_GATE_RUN,
                        help="sealed gate run directory with worlds/<w>.json (relative paths "
                             "resolve against the data root)")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting existing scientific outputs in --out")
    return parser


def paired_stats(values: list[Any]) -> dict[str, Any]:
    vals = [float(v) for v in values if v is not None]
    return {**_mean_sd(vals), "n_positive": int(sum(v > 0 for v in vals)),
            "n_missing": int(sum(v is None for v in values))}


def load_gate_world(gate_dir: Path, world: int) -> tuple[dict[str, Any], dict[str, Any]]:
    path = gate_dir / "worlds" / f"{int(world)}.json"
    data = path.read_bytes()
    record = json.loads(data)
    if int(record["world"]) != int(world):
        raise ValueError(f"{path} holds world {record['world']}")
    return record, {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        worlds = parse_worlds(args.worlds)
    except ValueError as exc:
        parser.error(str(exc))
    if args.probe is not None:
        if args.probe < 1:
            parser.error("--probe must be >= 1")
        worlds = worlds[: args.probe]
    if args.budget < 4:
        parser.error("--budget must be >= 4")
    if args.max_replans is not None and args.max_replans < 1:
        parser.error("--max-replans must be >= 1")

    if os.environ.get(ADMISSION_ENV):
        from scripts.hmasd_admission import require_admission

        admission: Any = dict(require_admission(__file__, direction="coupled_host_joint_skills_stage1"))
        if args.launch_sha != admission["sha"]:
            print("error: --launch-sha disagrees with the admitted sha", file=sys.stderr)
            return 2
    else:
        admission = {"status": "absent (direct invocation; zero-fit study, admission not required)"}

    started_utc, started = _utc_now(), time.perf_counter()
    import numpy as np

    from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
    if args.max_replans is None:
        args.max_replans = B4.MAX_REPLANS

    out = resolve_out(Path(args.out))
    existing = [name for name in ("summary.json", "worlds") if (out / name).exists()]
    if existing and not args.force:
        print(f"error: {out} already holds {existing}; pass --force", file=sys.stderr)
        return 2
    gate_dir = Path(args.gate_run)
    if not gate_dir.is_absolute():
        gate_dir = canonical_data_root(ROOT) / gate_dir
    gate_summary_bytes = (gate_dir / "summary.json").read_bytes()
    gate_summary = json.loads(gate_summary_bytes)
    if int(gate_summary["budget"]) != int(args.budget) or int(gate_summary["area_size"]) != int(args.area_size):
        print(f"error: gate run budget/area_size {gate_summary['budget']}/{gate_summary['area_size']} "
              f"!= --budget/--area-size {args.budget}/{args.area_size}", file=sys.stderr)
        return 2
    missing = [w for w in worlds if not (gate_dir / "worlds" / f"{w}.json").exists()]
    if missing:
        print(f"error: gate run lacks worlds {missing}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for world in worlds:
        cpu0, wall0 = _cpu_seconds()["total_s"], time.perf_counter()
        gate, gate_meta = load_gate_world(gate_dir, world)
        record = B4.run_world_b04(int(world), args.budget, area_size=args.area_size, gate=gate,
                                  timer=timed, max_replans=args.max_replans)
        record["timing"]["world_total"] = {"wall_s": time.perf_counter() - wall0,
                                           "cpu_s": _cpu_seconds()["total_s"] - cpu0}
        record["gate_file"] = gate_meta
        write_json(out / "worlds" / f"{int(world)}.json", record, indent=None)
        b0 = record["B0"]
        row = {"world": int(world), "F": record["F"], "B0": {k: b0[k] for k in B0_ROW_KEYS},
               "stakes": record["stakes"], "gate_file_sha256": gate_meta["sha256"],
               "timing": record["timing"]}
        rows.append(row)
        print(f"world={world} F={record['F']['all_mean']:.4f} B0={b0['all_mean']:.4f} "
              f"B0_f100={b0['final_100_mean']:.4f} S_info0={record['stakes']['s_info0']:+.4f} "
              f"known={b0['users_known']} clusters={b0['clusters_known']} "
              f"never_seen={b0['never_seen_clusters']} replans={b0['replans']} "
              f"evals={b0['evaluations_used']} cpu={record['timing']['world_total']['cpu_s']:.1f}s",
              flush=True)

    means: dict[str, Any] = {
        "stakes": {s: paired_stats([r["stakes"][s] for r in rows]) for s in STAKES},
        "F_all_mean": paired_stats([r["F"]["all_mean"] for r in rows]),
        "F_final_100_mean": paired_stats([r["F"]["final_100_mean"] for r in rows]),
        "B0_all_mean": paired_stats([r["B0"]["all_mean"] for r in rows]),
        "B0_final_100_mean": paired_stats([r["B0"]["final_100_mean"] for r in rows]),
        "B0_replans": paired_stats([r["B0"]["replans"] for r in rows]),
        "B0_evaluations_used": paired_stats([r["B0"]["evaluations_used"] for r in rows]),
        "B0_cap_hits": int(sum(r["B0"]["cap_hit"] for r in rows)),
        "B0_users_known": {k: paired_stats([r["B0"]["users_known"][k] for r in rows])
                           for k in rows[0]["B0"]["users_known"]} if rows else {},
        "B0_clusters_known": {k: paired_stats([r["B0"]["clusters_known"][k] for r in rows])
                              for k in rows[0]["B0"]["clusters_known"]} if rows else {},
        "worlds_with_never_seen_cluster": [r["world"] for r in rows if r["B0"]["never_seen_clusters"]],
    }
    summary = {
        "schema": SCHEMA, "direction": DIRECTION, "cell": "b04", "arm": "B0",
        "tool": "coupled_host_joint_skills_stage1.run_b04",
        "launch_sha": args.launch_sha, "admission": admission, "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0, "worlds": worlds, "area_size": int(args.area_size),
        "budget": int(args.budget),
        "gate_run": {"path": str(gate_dir), "summary_sha256": hashlib.sha256(gate_summary_bytes).hexdigest(),
                     "launch_sha": gate_summary.get("launch_sha")},
        "regression_equals_gate_all_worlds": all(r["F"]["regression_equals_gate"] for r in rows),
        "information_contract": {
            "trigger_new_known": B4.TRIGGER_NEW_KNOWN, "max_replans": int(args.max_replans),
            "max_replans_default": B4.MAX_REPLANS,
            "min_known_for_search": B4.MIN_KNOWN_FOR_SEARCH, "pooling": B4.POOLING,
            "shadow_user_set": B4.SHADOW_USER_SET, "clock": B4.CLOCK, "hold_rule": B4.HOLD_RULE,
            "no_event_t_e": B4.NO_EVENT_T_E,
            "sightings": "every user env._get_local_users(i) returns (uncapped), read row by row"},
        "definitions": {
            "F": "gate closed_loop_relay coverage_backhauled_mean_all (frozen planner, global map); "
                 "the same-run regression rollout is asserted equal (layout, series, means)",
            "F_final100": "gate closed_loop_relay coverage_backhauled_mean_final100",
            "B0_all_mean": "mean C_bh over the 500 steps of arm B0",
            "B0_final_100_mean": "mean C_bh over steps 400..499 of arm B0",
            "s_info0": "F - B0_all_mean (per world, then paired)",
            "s_info0_final100": "F_final100 - B0_final_100_mean",
            "users_known": "team-map size at steps 0/100/250/500 (see information_contract.clock)",
            "clusters_known": "generating clusters (user index // 10) with >= 1 known user",
            "never_seen_clusters": "clusters with no user in the team map after the terminal pooling",
            "replans": "planner calls, the first plan included (cap max_replans)",
            "cap_hit": "a trigger condition held while at the cap (not executed)",
            "evaluations_used": "static evaluations of all B0 planner calls (flat + relay)"},
        "per_world": rows, "means": means,
        "timing_totals": {"cpu_s_b0": float(sum(r["timing"]["b0"]["cpu_s"] for r in rows)),
                          "cpu_s_regression": float(sum(r["timing"]["regression"]["cpu_s"] for r in rows)),
                          "cpu_s_worlds": float(sum(r["timing"]["world_total"]["cpu_s"] for r in rows))},
        "cpu_seconds": _cpu_seconds(), "start_utc": started_utc, "end_utc": _utc_now(),
        "wall_clock_s": time.perf_counter() - started,
        "arguments": sys.argv[1:] if argv is None else list(argv),
        "interpreter": {"executable": sys.executable, "python": platform.python_version(),
                        "numpy": np.__version__, "host": platform.node()},
    }
    write_json(out / "summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
