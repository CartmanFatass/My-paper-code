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
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for world in worlds:
        cpu0, wall0 = _cpu_seconds()["total_s"], time.perf_counter()
        env = EH.make_event_host(int(world), area_size=args.area_size)
        record = R2.run_world_r2(env, args.budget, timer=timed)
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
        write_json(out / "worlds" / f"{int(world)}.json", record, indent=None)
        row = {"world": int(world), "t_e": record["t_e"], "routing_class": record["routing_class"],
               "decision_end": record["decision_end"],
               "decision_end_reason": record["decision_end_reason"],
               "reset_gateway": record["reset_gateway"],
               "deployed_layout_gateway": record["deployed_layout_gateway"],
               "arms": {arm: {k: rec[k] for k in ARM_KEYS} for arm, rec in record["arms"].items()},
               "reference_cold_post_event_mean": cold, "reference_keep_post_event_mean": keep_ref,
               "stakes": record["stakes"], "timing": record["timing"]}
        rows.append(row)
        text = " ".join(f"{a}={r['post_event_mean']:.4f}/rp{r['replans']}" for a, r in record["arms"].items())
        print(f"world={world} t_e={record['t_e']} class={record['routing_class']} "
              f"de={record['decision_end']} cold={cold:.4f} {text} "
              f"cpu={record['timing']['world_total']['cpu_s']:.1f}s", flush=True)

    arms = list(R2.ARMS)
    means: dict[str, Any] = {
        "arms": {arm: {"post_event_mean": paired_stats([r["arms"][arm]["post_event_mean"] for r in rows]),
                       "replans": paired_stats([r["arms"][arm]["replans"] for r in rows]),
                       "evaluations_used": paired_stats([r["arms"][arm]["evaluations_used"] for r in rows]),
                       "cap_hits": int(sum(r["arms"][arm]["cap_hit"] for r in rows))} for arm in arms},
        "reference_cold_post_event_mean": paired_stats([r["reference_cold_post_event_mean"] for r in rows]),
        "stakes": {s: paired_stats([r["stakes"][s] for r in rows]) for s in STAKES},
        "by_routing_class": {},
    }
    for klass in ROUTING_CLASSES:
        subset = [r for r in rows if r["routing_class"] == klass]
        if subset:
            means["by_routing_class"][klass] = {
                "worlds": [r["world"] for r in subset],
                **{s: paired_stats([r["stakes"][s] for r in subset]) for s in STAKES}}
    summary = {
        "schema": SCHEMA, "direction": DIRECTION, "tool": "coupled_host_replan_timing.run_r2",
        "launch_sha": args.launch_sha, "admission": admission, "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0, "worlds": worlds, "area_size": int(args.area_size),
        "budget": int(args.budget), "arms": arms,
        "information_contract": {"trigger_k": R2.TRIGGER_K, "move_threshold_m": R2.MOVE_THRESHOLD_M,
                                 "max_replans": R2.MAX_REPLANS, "forwarding_links": R2.FORWARDING_LINKS,
                                 "decision_end_rule": R2.DECISION_END_RULE,
                                 "facts": "every user env._get_local_users(i) returns (uncapped)",
                                 "clock": "facts of step s (state after call s) govern call s + 1"},
        "reference_run": ref_meta,
        "definitions": {
            "delta_share": "shared - unshared (post-event C_bh, per world, then paired)",
            "s_info_unshared": "cold (R1-lite F) - unshared", "s_info_shared": "cold - shared",
            "d_minus_shared": "D - shared", "d_minus_unshared": "D - unshared",
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
