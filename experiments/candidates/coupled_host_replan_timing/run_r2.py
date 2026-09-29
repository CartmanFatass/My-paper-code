#!/usr/bin/env python3
"""R2 runner (coupled_host_replan_timing): lawful-information arms unshared / shared / D, zero fits.

Per world: R1-lite's pre-event plan and shared prefix on the single-event host, then the three arms
of ``r2_info.py`` (each on its own deep copy of the snapshot at the start of step call ``t_e``).
F (full-information cold) is NOT re-run: its per-world ``post_event_mean`` is read from the R1-lite
summary given by ``--reference-run`` (sha256 recorded; budget, ``t_e`` and ``pre_event_mean`` are
checked equal to this run's, which proves the prefix is R1-lite's).  An arm that never re-planned
is KEEP and its post-event mean is checked equal to the reference KEEP's.

Writes ``worlds/<world>.json`` (full per-arm records and series) and ``summary.json`` (per-world
rows, stakes delta_share = shared - unshared, s_info_* = cold - arm, d_minus_* = D - arm; paired
mean/SD/min/max/n/n_positive overall and by routing class; timing).  Admission as in
``run_r1lite.py``; a direct invocation records ``admission = absent``.

R3 (``--arms shared,shared_wide --regression-run <r2 dev dir>``): the arms are selectable (default
unchanged); ``delta_adj = shared_wide - shared`` is added to the stakes of rows that have both arms.
With ``--regression-run`` the recomputed ``shared`` arm is compared per world with that run's
``shared`` (post_event_mean, replans, trigger_steps, exact equality); any mismatch records
``regression.ok = false`` with the differing worlds and withholds the delta_adj means (per-world
values stay, flagged).  delta_adj means are also withheld when no regression run was given.
Arms of the regression run that this run does not recompute are copied into each row under
``copied_from_regression_run`` (labelled, never used in a stake).
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
    DIRECTION,
    ROUTING_CLASSES,
    canonical_data_root,
    resolve_out,
    timed,
)

SCHEMA = 1
STAKES = ("delta_share", "s_info_unshared", "s_info_shared", "d_minus_shared", "d_minus_unshared")
ADJ_STAKE = "delta_adj"            # R3: shared_wide - shared, gated on the regression check
REGRESSION_KEYS = ("post_event_mean", "replans", "trigger_steps")
WIDE_KEYS = ("wide_links", "wide_edges_added_mean")
VALID_ARMS = ("unshared", "shared", "D", "shared_wide")   # == r2_info.ALL_ARMS (asserted after import)
ARM_KEYS = ("post_event_mean", "all_mean", "first_change_step_per_uav",
            "first_change_step_at_decision_end", "detection_step_any_uav", "trigger_steps", "replans",
            "evaluations_used", "cap_hit", "cpu_s", "routing_links", "views_over_obs_cap",
            "truth_grant_steps")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_r2.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--worlds", nargs="+", default=["1000-1031"],
                        help="world (reset) seeds: integers and inclusive ranges a-b")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--reference-run", required=True, type=Path,
                        help="R1-lite run directory holding summary.json with the cold rule "
                             "(relative paths resolve against the data root)")
    parser.add_argument("--budget", type=int, default=3000,
                        help="static-evaluation ceiling per planner search (flat and relay each)")
    parser.add_argument("--probe", type=int, default=None, help="run only the first N worlds")
    parser.add_argument("--launch-sha", default=None, help="published source sha of this launch")
    parser.add_argument("--area-size", type=int, default=5000)
    parser.add_argument("--arms", default="unshared,shared,D",
                        help="comma-separated arms from unshared, shared, D, shared_wide "
                             "(default: the R2 arms)")
    parser.add_argument("--regression-run", type=Path, default=None,
                        help="R2 run directory whose shared arm the recomputed shared arm must "
                             "equal per world (relative paths resolve against the data root)")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting existing scientific outputs in --out")
    return parser


def paired_stats(values: list[Any]) -> dict[str, Any]:
    vals = [float(v) for v in values if v is not None]
    return {**_mean_sd(vals), "n_positive": int(sum(v > 0 for v in vals)),
            "n_missing": int(sum(v is None for v in values))}


def load_reference(path: Path) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    data = (path / "summary.json").read_bytes()
    summary = json.loads(data)
    if "cold" not in summary.get("rules", []):
        raise ValueError(f"{path}/summary.json has no cold rule")
    rows = {int(row["world"]): row for row in summary["per_world"]}
    meta = {"path": str(path / "summary.json"), "sha256": hashlib.sha256(data).hexdigest(),
            "budget": int(summary["budget"]), "launch_sha": summary.get("launch_sha"),
            "tool": summary.get("tool")}
    return rows, meta


def load_regression(path: Path) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    data = (path / "summary.json").read_bytes()
    summary = json.loads(data)
    if "shared" not in summary.get("arms", []):
        raise ValueError(f"{path}/summary.json has no shared arm")
    rows = {int(row["world"]): row for row in summary["per_world"]}
    meta = {"path": str(path / "summary.json"), "sha256": hashlib.sha256(data).hexdigest(),
            "budget": int(summary["budget"]), "area_size": int(summary["area_size"]),
            "launch_sha": summary.get("launch_sha"), "arms": list(summary["arms"])}
    return rows, meta


def regression_diffs(row: dict[str, Any] | None, shared: dict[str, Any]) -> dict[str, Any]:
    """Keys of REGRESSION_KEYS where the recomputed shared arm differs from the regression row."""
    if row is None:
        return {"world": "absent from the regression run"}
    old = row["arms"]["shared"]
    fresh = json.loads(json.dumps({k: shared[k] for k in REGRESSION_KEYS}))
    return {k: {"regression": old.get(k), "recomputed": fresh[k]}
            for k in REGRESSION_KEYS if old.get(k) != fresh[k]}


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
    arms = [a.strip() for a in str(args.arms).split(",") if a.strip()]
    if not arms or len(set(arms)) != len(arms) or any(a not in VALID_ARMS for a in arms):
        parser.error(f"--arms must be distinct names from {', '.join(VALID_ARMS)}")
    if args.regression_run is not None and "shared" not in arms:
        parser.error("--regression-run needs the shared arm in --arms")

    if os.environ.get(ADMISSION_ENV):
        from scripts.hmasd_admission import require_admission

        admission: Any = dict(require_admission(__file__, direction="coupled_host_replan_timing"))
        if args.launch_sha != admission["sha"]:
            print("error: --launch-sha disagrees with the admitted sha", file=sys.stderr)
            return 2
    else:
        admission = {"status": "absent (direct invocation; zero-fit study, admission not required)"}

    started_utc, started = _utc_now(), time.perf_counter()
    import numpy as np

    from experiments.candidates.coupled_host_replan_timing import event_host as EH
    from experiments.candidates.coupled_host_replan_timing import r2_info as R2

    assert tuple(VALID_ARMS) == R2.ALL_ARMS

    out = resolve_out(Path(args.out))
    existing = [name for name in ("summary.json", "worlds") if (out / name).exists()]
    if existing and not args.force:
        print(f"error: {out} already holds {existing}; pass --force", file=sys.stderr)
        return 2
    ref_dir = Path(args.reference_run)
    if not ref_dir.is_absolute():
        ref_dir = canonical_data_root(ROOT) / ref_dir
    reference, ref_meta = load_reference(ref_dir)
    if ref_meta["budget"] != int(args.budget):
        print(f"error: reference budget {ref_meta['budget']} != --budget {args.budget}", file=sys.stderr)
        return 2
    missing = [w for w in worlds if w not in reference]
    if missing:
        print(f"error: reference run lacks worlds {missing}", file=sys.stderr)
        return 2
    regression, reg_meta = None, None
    if args.regression_run is not None:
        reg_dir = Path(args.regression_run)
        if not reg_dir.is_absolute():
            reg_dir = canonical_data_root(ROOT) / reg_dir
        regression, reg_meta = load_regression(reg_dir)
        if reg_meta["budget"] != int(args.budget) or reg_meta["area_size"] != int(args.area_size):
            print("error: regression run budget/area_size differ from this run", file=sys.stderr)
            return 2
    regression_mismatches: dict[str, Any] = {}
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for world in worlds:
        cpu0, wall0 = _cpu_seconds()["total_s"], time.perf_counter()
        env = EH.make_event_host(int(world), area_size=args.area_size)
        record = R2.run_world_r2(env, args.budget, arms=tuple(arms), timer=timed)
        record["timing"]["world_total"] = {"wall_s": time.perf_counter() - wall0,
                                           "cpu_s": _cpu_seconds()["total_s"] - cpu0}
        ref = reference[int(world)]
        if int(ref["t_e"]) != record["t_e"] or float(ref["pre_event_mean"]) != record["pre_event_mean"]:
            print(f"error: world {world}: prefix differs from the reference run", file=sys.stderr)
            return 2
        keep_ref = ref["rules"].get("keep", {}).get("post_event_mean")
        for arm, rec in record["arms"].items():
            if rec["replans"] == 0 and keep_ref is not None and rec["post_event_mean"] != keep_ref:
                print(f"error: world {world}: {arm} never re-planned but differs from KEEP",
                      file=sys.stderr)
                return 2
        cold = float(ref["rules"]["cold"]["post_event_mean"])
        post = {arm: rec["post_event_mean"] for arm, rec in record["arms"].items()}
        record["reference"] = {"cold_post_event_mean": cold, "keep_post_event_mean": keep_ref,
                               "source": ref_meta["path"], "sha256": ref_meta["sha256"]}
        record["stakes"] = R2.stakes(post, cold)
        if regression is not None:
            reg_row = regression.get(int(world))
            diffs = regression_diffs(reg_row, record["arms"]["shared"])
            record["regression"] = {"ok": not diffs, "diffs": diffs}
            if diffs:
                regression_mismatches[str(int(world))] = diffs
            if reg_row is not None:
                record["copied_from_regression_run"] = {
                    "note": "copied from the regression run for the record; not re-run, not in a stake",
                    **{arm: {"post_event_mean": rec["post_event_mean"], "replans": rec["replans"]}
                       for arm, rec in reg_row["arms"].items() if arm not in record["arms"]}}
        if ADJ_STAKE in record["stakes"] and not record.get("regression", {}).get("ok", False):
            record["delta_adj_flag"] = ("regression mismatch" if regression is not None
                                        else "no regression run")
        write_json(out / "worlds" / f"{int(world)}.json", record, indent=None)
        row = {"world": int(world), "t_e": record["t_e"], "routing_class": record["routing_class"],
               "decision_end": record["decision_end"],
               "decision_end_reason": record["decision_end_reason"],
               "reset_gateway": record["reset_gateway"],
               "deployed_layout_gateway": record["deployed_layout_gateway"],
               "arms": {arm: {k: rec[k] for k in ARM_KEYS + WIDE_KEYS if k in rec}
                        for arm, rec in record["arms"].items()},
               "reference_cold_post_event_mean": cold, "reference_keep_post_event_mean": keep_ref,
               "stakes": record["stakes"], "timing": record["timing"]}
        for key in ("regression", "copied_from_regression_run", "delta_adj_flag"):
            if key in record:
                row[key] = record[key]
        rows.append(row)
        text = " ".join(f"{a}={r['post_event_mean']:.4f}/rp{r['replans']}" for a, r in record["arms"].items())
        print(f"world={world} t_e={record['t_e']} class={record['routing_class']} "
              f"de={record['decision_end']} cold={cold:.4f} {text} "
              f"cpu={record['timing']['world_total']['cpu_s']:.1f}s", flush=True)

    regression_ok = None if regression is None else not regression_mismatches
    stake_names = [s for s in STAKES + (ADJ_STAKE,) if any(s in r["stakes"] for r in rows)]
    adj_withheld = None
    if ADJ_STAKE in stake_names and regression_ok is not True:
        adj_withheld = ("regression mismatch" if regression_ok is False else "no regression run")
    mean_stakes = [s for s in stake_names if not (s == ADJ_STAKE and adj_withheld)]
    means: dict[str, Any] = {
        "arms": {arm: {"post_event_mean": paired_stats([r["arms"][arm]["post_event_mean"] for r in rows]),
                       "replans": paired_stats([r["arms"][arm]["replans"] for r in rows]),
                       "evaluations_used": paired_stats([r["arms"][arm]["evaluations_used"] for r in rows]),
                       "cap_hits": int(sum(r["arms"][arm]["cap_hit"] for r in rows))} for arm in arms},
        "reference_cold_post_event_mean": paired_stats([r["reference_cold_post_event_mean"] for r in rows]),
        "stakes": {s: paired_stats([r["stakes"].get(s) for r in rows]) for s in mean_stakes},
        "by_routing_class": {},
    }
    for klass in ROUTING_CLASSES:
        subset = [r for r in rows if r["routing_class"] == klass]
        if subset:
            means["by_routing_class"][klass] = {
                "worlds": [r["world"] for r in subset],
                **{s: paired_stats([r["stakes"].get(s) for r in subset]) for s in mean_stakes}}
    if adj_withheld:
        means["stakes"][ADJ_STAKE] = None
        means["delta_adj_withheld"] = adj_withheld
    if "shared_wide" in arms:
        means["arms"]["shared_wide"]["wide_edges_added_mean"] = paired_stats(
            [r["arms"]["shared_wide"]["wide_edges_added_mean"] for r in rows])
    summary = {
        "schema": SCHEMA, "direction": DIRECTION, "tool": "coupled_host_replan_timing.run_r2",
        "launch_sha": args.launch_sha, "admission": admission, "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0, "worlds": worlds, "area_size": int(args.area_size),
        "budget": int(args.budget), "arms": arms,
        "information_contract": {"trigger_k": R2.TRIGGER_K, "move_threshold_m": R2.MOVE_THRESHOLD_M,
                                 "max_replans": R2.MAX_REPLANS, "forwarding_links": R2.FORWARDING_LINKS,
                                 "wide_forwarding_links": R2.WIDE_FORWARDING_LINKS,
                                 "decision_end_rule": R2.DECISION_END_RULE,
                                 "facts": "every user env._get_local_users(i) returns (uncapped)",
                                 "clock": "facts of step s (state after call s) govern call s + 1"},
        "reference_run": ref_meta,
        "regression_run": None if reg_meta is None else {
            **reg_meta, "compared_keys": list(REGRESSION_KEYS), "compared_arm": "shared",
            "regression_ok": regression_ok, "mismatch_worlds": sorted(int(w) for w in regression_mismatches),
            "mismatches": regression_mismatches},
        "regression_ok": regression_ok,
        "definitions": {
            "delta_share": "shared - unshared (post-event C_bh, per world, then paired)",
            "s_info_unshared": "cold (R1-lite F) - unshared", "s_info_shared": "cold - shared",
            "d_minus_shared": "D - shared", "d_minus_unshared": "D - unshared",
            "delta_adj": "shared_wide - shared (R3; means only when regression_ok is true)",
            "post_event_window": "series indices t_e..499; t_e from the host record, reporting only"},
        "per_world": rows, "means": means,
        "decision_end_no_routed_uav_worlds": [r["world"] for r in rows
                                              if r["decision_end_reason"] == "no routed uav"],
        "timing_totals": {"cpu_s_by_arm": {arm: float(sum(r["timing"][arm]["cpu_s"] for r in rows)) for arm in arms},
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
