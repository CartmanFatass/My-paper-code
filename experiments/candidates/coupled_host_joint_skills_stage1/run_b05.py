#!/usr/bin/env python3
"""Cell b05 runner (coupled_host_joint_skills_stage1): arms B0 / L / D_100, zero fits.

Per world (``b05_sighting_ceiling.run_world_b05``): (1) the b04 regression rollout of the frozen
planner with the global map, asserted equal to the sealed gate record ``<gate-run>/worlds/<w>.json``;
(2) arm B0 (b04's code), asserted equal to the committed b04 reference run
``<reference-run>/worlds/<w>.json`` (all-500 series, all-500 mean, first_known_step); (3) arm L
(B0 + clock re-plans at calls 100/200/300/400); (4) arm D_100 (L + a one-time privileged grant of
all users' true positions at the decision for call 100).  Each arm runs on its own fresh static
host.  Stakes: ``c_ceil = D100 - L`` (primary), ``delta_l = L - B0``, ``f_minus_d100 = F - D100``,
all-500 and final-100; F = the gate closed-loop P_relay values.

Writes ``worlds/<world>.json`` and ``summary.json`` (per-world rows; paired mean/SD/min/max/n/
n_positive overall, by the reader-side split flag and on the four focus worlds; information
contract; cpu_seconds, wall_clock_s, git_head, launch_sha, arguments, interpreter, definitions).
Admission as in ``run_b04.py``; a direct invocation records ``admission = absent``.
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

from experiments.candidates.coupled_host_joint_skills_stage1.run_b04 import (  # noqa: E402
    DEFAULT_GATE_RUN,
    load_gate_world,
    paired_stats,
)
from experiments.candidates.coupled_host_joint_skills_stage1.run_gate import (  # noqa: E402
    _cpu_seconds,
    _git,
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
DEFAULT_REFERENCE_RUN = Path("runs") / DIRECTION / "b04_b0_dev_a01"
STAKES = ("c_ceil", "delta_l", "f_minus_d100", "c_ceil_final100", "delta_l_final100",
          "f_minus_d100_final100")
ARM_ROW_KEYS = ("all_mean", "final_100_mean", "plans", "replans", "replans_by_kind",
                "evaluations_used", "cap_hit", "cpu_s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_b05.py", description=__doc__,
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
                        help="cap on planner calls per world and arm, trigger and clock calls "
                             "together, the first plan included (default: b05 MAX_REPLANS = 20)")
    parser.add_argument("--gate-run", type=Path, default=DEFAULT_GATE_RUN,
                        help="sealed gate run directory with worlds/<w>.json (relative paths "
                             "resolve against the data root)")
    parser.add_argument("--reference-run", type=Path, default=DEFAULT_REFERENCE_RUN,
                        help="committed b04 B0 run with worlds/<w>.json (relative paths resolve "
                             "against the data root)")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting existing scientific outputs in --out")
    return parser


def load_reference_world(reference_dir: Path, world: int) -> tuple[dict[str, Any], dict[str, Any]]:
    path = reference_dir / "worlds" / f"{int(world)}.json"
    data = path.read_bytes()
    record = json.loads(data)
    if int(record["world"]) != int(world):
        raise ValueError(f"{path} holds world {record['world']}")
    return record, {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}


def stake_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {s: paired_stats([r["stakes"][s] for r in rows]) for s in STAKES}


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
    from experiments.candidates.coupled_host_joint_skills_stage1 import b05_sighting_ceiling as B5
    if args.max_replans is None:
        args.max_replans = B5.MAX_REPLANS

    out = resolve_out(Path(args.out))
    existing = [name for name in ("summary.json", "worlds") if (out / name).exists()]
    if existing and not args.force:
        print(f"error: {out} already holds {existing}; pass --force", file=sys.stderr)
        return 2
    gate_dir = Path(args.gate_run)
    if not gate_dir.is_absolute():
        gate_dir = canonical_data_root(ROOT) / gate_dir
    reference_dir = Path(args.reference_run)
    if not reference_dir.is_absolute():
        reference_dir = canonical_data_root(ROOT) / reference_dir
    gate_summary_bytes = (gate_dir / "summary.json").read_bytes()
    gate_summary = json.loads(gate_summary_bytes)
    gate_sha = hashlib.sha256(gate_summary_bytes).hexdigest()
    if int(gate_summary["budget"]) != int(args.budget) or int(gate_summary["area_size"]) != int(args.area_size):
        print(f"error: gate run budget/area_size {gate_summary['budget']}/{gate_summary['area_size']} "
              f"!= --budget/--area-size {args.budget}/{args.area_size}", file=sys.stderr)
        return 2
    ref_summary_bytes = (reference_dir / "summary.json").read_bytes()
    ref_summary = json.loads(ref_summary_bytes)
    ref_cap = int(ref_summary["information_contract"]["max_replans"])
    if (int(ref_summary["budget"]) != int(args.budget)
            or int(ref_summary["area_size"]) != int(args.area_size)
            or ref_cap != int(args.max_replans)):
        print(f"error: reference run budget/area_size/max_replans {ref_summary['budget']}/"
              f"{ref_summary['area_size']}/{ref_cap} != {args.budget}/{args.area_size}/"
              f"{args.max_replans}", file=sys.stderr)
        return 2
    if ref_summary.get("gate_run", {}).get("summary_sha256") != gate_sha:
        print("error: the reference run was made against a different gate summary", file=sys.stderr)
        return 2
    missing = [w for w in worlds if not (gate_dir / "worlds" / f"{w}.json").exists()]
    missing_ref = [w for w in worlds if not (reference_dir / "worlds" / f"{w}.json").exists()]
    if missing or missing_ref:
        print(f"error: gate run lacks worlds {missing}; reference run lacks {missing_ref}",
              file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for world in worlds:
        cpu0, wall0 = _cpu_seconds()["total_s"], time.perf_counter()
        gate, gate_meta = load_gate_world(gate_dir, world)
        reference, ref_meta = load_reference_world(reference_dir, world)
        record = B5.run_world_b05(int(world), args.budget, gate=gate,
                                  reference_world_record=reference, area_size=args.area_size,
                                  timer=timed, max_replans=args.max_replans)
        record["timing"]["world_total"] = {"wall_s": time.perf_counter() - wall0,
                                           "cpu_s": _cpu_seconds()["total_s"] - cpu0}
        record["gate_file"] = gate_meta
        record["reference_file"] = ref_meta
        write_json(out / "worlds" / f"{int(world)}.json", record, indent=None)
        arms = record["arms"]
        row = {"world": int(world), "F": record["F"],
               "arms": {a: {k: arms[a][k] for k in ARM_ROW_KEYS} for a in B5.ARMS},
               "D100_privileged_grant": arms["D100"]["record"]["privileged_grant"],
               "stakes": record["stakes"], "split": record["split"],
               "focus_world": record["focus_world"],
               "b0_equals_reference": record["b0_equals_reference"],
               "gate_file_sha256": gate_meta["sha256"], "reference_file_sha256": ref_meta["sha256"],
               "timing": record["timing"]}
        rows.append(row)
        kinds = " ".join(f"{a}={arms[a]['replans_by_kind']['trigger']}t+{arms[a]['replans_by_kind']['clock']}c"
                         for a in B5.ARMS)
        print(f"world={world} F={record['F']['all_mean']:.4f} B0={arms['B0']['all_mean']:.4f} "
              f"L={arms['L']['all_mean']:.4f} D100={arms['D100']['all_mean']:.4f} "
              f"c_ceil={record['stakes']['c_ceil']:+.4f} delta_l={record['stakes']['delta_l']:+.4f} "
              f"f_minus_d100={record['stakes']['f_minus_d100']:+.4f} plans[{kinds}] "
              f"split_ge5={record['split']['f_backhauls_ge5_never_sighted']} "
              f"cpu={record['timing']['world_total']['cpu_s']:.1f}s", flush=True)

    flagged = [r for r in rows if r["split"]["f_backhauls_ge5_never_sighted"]]
    unflagged = [r for r in rows if not r["split"]["f_backhauls_ge5_never_sighted"]]
    focus = [r for r in rows if r["world"] in B5.FOCUS_WORLDS]
    means: dict[str, Any] = {
        "stakes": stake_block(rows),
        "stakes_split_f_backhauls_ge5_never_sighted": {
            "true": {"worlds": [r["world"] for r in flagged], **stake_block(flagged)},
            "false": {"worlds": [r["world"] for r in unflagged], **stake_block(unflagged)}},
        "stakes_focus_worlds": {"worlds": [r["world"] for r in focus], **stake_block(focus)},
        "F_all_mean": paired_stats([r["F"]["all_mean"] for r in rows]),
        "F_final_100_mean": paired_stats([r["F"]["final_100_mean"] for r in rows]),
        **{f"{a}_{k}": paired_stats([r["arms"][a][k] for r in rows])
           for a in B5.ARMS for k in ("all_mean", "final_100_mean", "replans", "evaluations_used")},
        **{f"{a}_replans_{kind}": paired_stats([r["arms"][a]["replans_by_kind"][kind] for r in rows])
           for a in B5.ARMS for kind in ("trigger", "clock")},
        "cap_hits": {a: int(sum(r["arms"][a]["cap_hit"] for r in rows)) for a in B5.ARMS},
    }
    summary = {
        "schema": SCHEMA, "direction": DIRECTION, "cell": "b05", "arms": list(B5.ARMS),
        "tool": "coupled_host_joint_skills_stage1.run_b05",
        "launch_sha": args.launch_sha, "admission": admission, "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0, "worlds": worlds, "area_size": int(args.area_size),
        "budget": int(args.budget),
        "gate_run": {"path": str(gate_dir), "summary_sha256": gate_sha,
                     "launch_sha": gate_summary.get("launch_sha")},
        "reference_run": {"path": str(reference_dir),
                          "summary_sha256": hashlib.sha256(ref_summary_bytes).hexdigest(),
                          "launch_sha": ref_summary.get("launch_sha")},
        "regression_equals_gate_all_worlds": all(r["F"]["regression_equals_gate"] for r in rows),
        "b0_equals_reference_all_worlds": all(r["b0_equals_reference"] for r in rows),
        "information_contract": {
            "b0": "b04_lawful_sensing.B0Arm, unchanged (see the reference run's information_contract)",
            "clock_steps": list(B5.CLOCK_STEPS), "clock_plan_rule": B5.CLOCK_PLAN_RULE,
            "grant_step": B5.GRANT_STEP, "grant_rule": B5.GRANT_RULE,
            "max_replans": int(args.max_replans), "max_replans_default": B5.MAX_REPLANS,
            "trigger_new_known": B4.TRIGGER_NEW_KNOWN,
            "min_known_for_search": B4.MIN_KNOWN_FOR_SEARCH, "pooling": B4.POOLING,
            "shadow_user_set": B4.SHADOW_USER_SET, "clock": B4.CLOCK, "hold_rule": B4.HOLD_RULE,
            "no_event_t_e": B4.NO_EVENT_T_E, "split_rule": B5.SPLIT_RULE,
            "split_min_never_sighted": B5.SPLIT_MIN_NEVER_SIGHTED,
            "focus_worlds": list(B5.FOCUS_WORLDS),
            "reference_run_summary_sha256": hashlib.sha256(ref_summary_bytes).hexdigest()},
        "definitions": {
            "F": "gate closed_loop_relay coverage_backhauled_mean_all (frozen planner, global map); "
                 "the same-run regression rollout is asserted equal (layout, series, means)",
            "B0/L/D100 all_mean": "mean C_bh over the 500 steps of the arm on its own static host",
            "final_100_mean": "mean C_bh over steps 400..499",
            "c_ceil": "D100_all_mean - L_all_mean (per world, then paired); primary",
            "delta_l": "L_all_mean - B0_all_mean",
            "f_minus_d100": "F - D100_all_mean",
            "*_final100": "the same differences of final-100 means",
            "replans_by_kind": "planner calls by kind (trigger / clock), one call per decision",
            "cap_hit": "a call (either kind) was due while at the cap (not executed)",
            "split": "reader-side only (information_contract.split_rule)",
            "pre_clock_identity": "B0, L and D100 series asserted identical before call 100"},
        "per_world": rows, "means": means,
        "timing_totals": {
            **{f"cpu_s_{k}": float(sum(r["timing"][k]["cpu_s"] for r in rows))
               for k in ("regression", "b0", "L", "D100", "world_total")}},
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
