#!/usr/bin/env python3
"""R1-lite runner (coupled_host_replan_timing): zero fits, deterministic given the world seed.

Two passes, both on the single-event coupled host (``event_host.py``; rules in ``rules.py``):

* ``--rules keep,cold,warm,seeded`` (default; any subset): per world the D2 pre-event plan, the
  shared pre-event prefix (executed once, branched by deep copy at the start of step ``t_e``) and
  the ordinary rules.  Writes ``worlds/<world>.json`` and ``summary.json`` (per-world rows, per-rule
  window means and the paired per-world stakes S_switch = warm - KEEP, S_cold = warm - cold and
  S_seeded = seeded - KEEP on the post-event window, overall and split by the relocated cluster's
  pre-event routing class).
* ``--rules grid``: the departure small grid (2^6 departing subsets x delay {0, 20, 50}, the
  departing set leaves together) over an existing warm result read from ``--warm-run`` (default:
  ``--out``); writes ``grid/<world>.json`` and ``grid_summary.json`` with room = grid best - best
  ordinary rule of the input run (paired per world), and the sha256 of every input world file.

Every per-world quantity is a window mean of that world first; cross-world means weight worlds
equally and paired SDs are the SDs of per-world differences from this run only.  Wall and process
CPU seconds are recorded per world and per component (pre-event plan, pre-event prefix, each
rule's plan and rollout including state copies, the un-branched KEEP check, the grid total).

Admission: when launched through ``scripts/hmasd_launch.py`` (the ``HMASD_ADMISSION_V1``
environment is present) the runner consumes it before any environment import or output and
requires ``--launch-sha`` to equal the admitted sha; a direct invocation records
``admission = absent``.  Relative ``--out`` resolves against this checkout's root (the code root);
relative ``--warm-run`` resolves against the data root (the checkout, mapped back from a
``--snapshot`` source worktree), so runs/ inputs are found under a snapshot launch.
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

DIRECTION = "coupled_host_replan_timing"
SCHEMA = 1
SNAPSHOT_PARENT = "hmasd-launch-sources"
ADMISSION_ENV = "HMASD_ADMISSION_V1"
ORDINARY = ("keep", "cold", "warm", "seeded")
ROUTING_CLASSES = ("chain", "direct", "unrouted", "shared_only", "unserved")


def canonical_data_root(path: Path) -> Path:
    """Map ``<checkout>/.git/hmasd-launch-sources/<id>`` back to ``<checkout>``; else unchanged."""
    path = Path(path)
    parents = path.parents
    if len(parents) >= 3 and parents[0].name == SNAPSHOT_PARENT and parents[1].name == ".git":
        return parents[2]
    return path


def parse_rules(text: str) -> tuple[str, ...]:
    rules = tuple(part.strip() for part in str(text).split(",") if part.strip())
    if not rules or len(set(rules)) != len(rules):
        raise ValueError("--rules must list distinct rules")
    if "grid" in rules:
        if rules != ("grid",):
            raise ValueError("--rules grid is a separate pass over an existing warm result")
        return rules
    unknown = set(rules) - set(ORDINARY)
    if unknown:
        raise ValueError(f"unknown rules {sorted(unknown)}; choose from {ORDINARY} or grid")
    return tuple(r for r in ORDINARY if r in rules)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_r1lite.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--worlds", nargs="+", default=["1000-1031"],
                        help="world (reset) seeds: integers and inclusive ranges a-b")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--budget", type=int, default=3000,
                        help="static-evaluation ceiling per planner search (pre-event, cold: "
                             "flat and relay each; warm's restricted descent; seeded)")
    parser.add_argument("--probe", type=int, default=None, help="run only the first N worlds")
    parser.add_argument("--rules", default="keep,cold,warm,seeded",
                        help="subset of keep,cold,warm,seeded; or 'grid' alone (separate pass)")
    parser.add_argument("--warm-run", type=Path, default=None,
                        help="grid pass: directory holding worlds/<w>.json of a warm run "
                             "(default --out); relative paths resolve against the data root")
    parser.add_argument("--launch-sha", default=None, help="published source sha of this launch")
    parser.add_argument("--area-size", type=int, default=5000)
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting existing scientific outputs in --out")
    return parser


def timed(function, *args, **kwargs):
    cpu0 = _cpu_seconds()["total_s"]
    wall0 = time.perf_counter()
    value = function(*args, **kwargs)
    return value, {"wall_s": time.perf_counter() - wall0, "cpu_s": _cpu_seconds()["total_s"] - cpu0}


def stats(values: list[Any]) -> dict[str, Any]:
    return _mean_sd([float(v) for v in values if v is not None])


def paired(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """Mean / SD / n of the per-world differences ``key`` (a stake or the grid room)."""
    return stats([row["stakes"][key] if key in row.get("stakes", {}) else row[key] for row in rows])


def ordinary_summary(rows: list[dict[str, Any]], rules: tuple[str, ...]) -> dict[str, Any]:
    means: dict[str, Any] = {"rules": {}, "stakes": {}, "by_routing_class": {}}
    for rule in rules:
        means["rules"][rule] = {
            key: stats([row["rules"][rule][key] for row in rows])
            for key in ("post_event_mean", "all_mean", "pre_event_mean", "transition_loss_steps",
                        "arrival_step")}
    for stake in ("S_switch", "S_cold", "S_seeded"):
        if all(row["stakes"][stake] is not None for row in rows):
            means["stakes"][stake] = paired(rows, stake)
    for klass in ROUTING_CLASSES:
        subset = [row for row in rows if row["routing_class"] == klass]
        if not subset:
            continue
        entry = {"worlds": [row["world"] for row in subset],
                 "post_event_mean": {rule: stats([row["rules"][rule]["post_event_mean"] for row in subset])
                                     for rule in rules}}
        for stake in means["stakes"]:
            entry[stake] = paired(subset, stake)
        means["by_routing_class"][klass] = entry
    means["far_near"] = {"far": "routing class 'chain' (chain-served before the event)",
                         "near": "routing class 'direct'",
                         "other_classes_reported_separately": ["unrouted", "shared_only", "unserved"]}
    return means


def resolve_out(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        worlds = parse_worlds(args.worlds)
        rules = parse_rules(args.rules)
    except ValueError as exc:
        parser.error(str(exc))
    if args.probe is not None:
        if args.probe < 1:
            parser.error("--probe must be >= 1")
        worlds = worlds[: args.probe]
    if args.budget < 4:
        parser.error("--budget must be >= 4")

    if os.environ.get(ADMISSION_ENV):
        # Admission precedes environment imports and any output.
        from scripts.hmasd_admission import require_admission

        admission: Any = dict(require_admission(__file__, direction="coupled_host_replan_timing"))
        if args.launch_sha != admission["sha"]:
            print("error: --launch-sha disagrees with the admitted sha", file=sys.stderr)
            return 2
    else:
        admission = {"status": "absent (direct invocation; zero-fit study, admission not required)"}

    started_utc, started = _utc_now(), time.perf_counter()
    import numpy as np

    from experiments.candidates.coupled_host_replan_timing import rules as R
    from experiments.candidates.coupled_host_replan_timing.event_host import (
        EVENT_DRAW_ORDER,
        make_event_host,
    )

    out = resolve_out(Path(args.out))
    out.mkdir(parents=True, exist_ok=True)
    grid_pass = rules == ("grid",)
    outputs = ("grid_summary.json", "grid") if grid_pass else ("summary.json", "worlds")
    existing = [name for name in outputs if (out / name).exists()]
    if existing and not args.force:
        print(f"error: {out} already holds {existing}; pass --force", file=sys.stderr)
        return 2

    common = {
        "schema": SCHEMA,
        "direction": DIRECTION,
        "launch_sha": args.launch_sha,
        "admission": admission,
        "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0,
        "worlds": worlds,
        "area_size": int(args.area_size),
        "budget": int(args.budget),
        "event_law": {"rng": "numpy.random.default_rng([world, 3])", "draw_order": list(EVENT_DRAW_ORDER),
                      "timing": "applied inside step() of the call with current_step == t_e, before "
                                "that call's actions; series index t_e is the first post-event value; "
                                "every rule reacts from its decision for step t_e (full information)"},
        "rng_derivations": {"planner": "numpy.random.default_rng(world), fresh instance per search "
                                       "(D2 run_gate rule), for the pre-event, cold and seeded searches",
                            "event": "numpy.random.default_rng([world, 3])"},
        "windows": {"pre_event": "series indices 0..t_e-1", "post_event": "series indices t_e..499 "
                    "(primary)", "all": "0..499", "cross_world": "per-world window means first, "
                    "then equal-weight means across worlds; paired SDs over per-world differences"},
        "arguments": sys.argv[1:] if argv is None else list(argv),
        "interpreter": {"executable": sys.executable, "python": platform.python_version(),
                        "numpy": np.__version__, "host": platform.node()},
    }

    if grid_pass:
        warm_dir = Path(args.warm_run) if args.warm_run is not None else out
        if not warm_dir.is_absolute():
            warm_dir = canonical_data_root(ROOT) / warm_dir
        rows, inputs = [], {}
        for world in worlds:
            path = warm_dir / "worlds" / f"{int(world)}.json"
            data = path.read_bytes()
            inputs[str(world)] = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}
            record = json.loads(data)
            if "warm" not in record["rules"]:
                print(f"error: {path} has no warm result", file=sys.stderr)
                return 2
            if int(record["budget"]) != int(args.budget) or int(record["world"]) != int(world):
                print(f"error: {path} is for another world/budget", file=sys.stderr)
                return 2
            cpu0, wall0 = _cpu_seconds()["total_s"], time.perf_counter()
            env = make_event_host(int(world), area_size=args.area_size)
            grid = R.run_grid(env, record)
            grid["timing"] = {"grid_total": {"wall_s": time.perf_counter() - wall0,
                                             "cpu_s": _cpu_seconds()["total_s"] - cpu0},
                              "rollouts_executed": grid["unique_rollouts"]}
            grid["routing_class"] = record["event_info"]["routing_class"]
            write_json(out / "grid" / f"{int(world)}.json", grid, indent=None)
            rows.append({"world": int(world), "routing_class": grid["routing_class"],
                         "t_e": grid["t_e"], "room": grid["room"], "best": grid["best"],
                         "unique_rollouts": grid["unique_rollouts"], "timing": grid["timing"]})
            print(f"world={world} grid best={grid['best']['post_event_mean']:.4f} "
                  f"room={grid['room']:+.4f} rollouts={grid['unique_rollouts']} "
                  f"wall={grid['timing']['grid_total']['wall_s']:.1f}s", flush=True)
        by_class = {}
        for klass in ROUTING_CLASSES:
            subset = [row for row in rows if row["routing_class"] == klass]
            if subset:
                by_class[klass] = {"worlds": [r["world"] for r in subset], "room": paired(subset, "room")}
        summary = {
            **common, "tool": "coupled_host_replan_timing.run_r1lite grid",
            "rules": ["grid"], "grid": {"name": "small-grid best", "subsets": 64,
                                         "delays": list(R.GRID_DELAYS),
                                         "departing_set": "leaves together at t_e + delay; others hold"},
            "inputs": inputs,
            "per_world": rows,
            "means": {"room": paired(rows, "room"), "by_routing_class": by_class,
                      "best_grid_post_event_mean": stats([r["best"]["post_event_mean"] for r in rows])},
            "timing_per_world": {"grid_total": {k: stats([r["timing"]["grid_total"][k] for r in rows])
                                                for k in ("wall_s", "cpu_s")},
                                 "rollouts_executed": stats([r["unique_rollouts"] for r in rows])},
            "cpu_seconds": _cpu_seconds(), "start_utc": started_utc, "end_utc": _utc_now(),
            "wall_clock_s": time.perf_counter() - started,
        }
        write_json(out / "grid_summary.json", summary)
        return 0

    rows = []
    for world in worlds:
        cpu0, wall0 = _cpu_seconds()["total_s"], time.perf_counter()
        env = make_event_host(int(world), area_size=args.area_size)
        record = R.run_world(env, args.budget, rules, timer=timed)
        record["timing"]["world_total"] = {"wall_s": time.perf_counter() - wall0,
                                           "cpu_s": _cpu_seconds()["total_s"] - cpu0}
        write_json(out / "worlds" / f"{int(world)}.json", record, indent=None)
        event = record["event_info"]
        row = {"world": int(world), "t_e": record["t_e"], "cluster": event["cluster"],
               "routing_class": event["routing_class"], "chain_served": event["chain_served"],
               "cluster_is_gate_far": event["cluster_is_gate_far"],
               "routing_actual_equals_static": event["routing_actual_equals_static"],
               "pre_event_mean": record["pre_event"]["pre_event_mean"],
               "rules": {rule: {key: record["rules"][rule][key] for key in (
                   "post_event_mean", "all_mean", "pre_event_mean", "transition_loss_steps",
                   "arrival_step")} for rule in rules},
               "stakes": record["stakes"], "timing": record["timing"]}
        if "warm" in rules:
            warm = record["rules"]["warm"]
            row["warm"] = {"movable_source": warm["movable_source"],
                           "movable_uavs": warm["movable_uavs"],
                           "warm_equals_keep": warm["warm_equals_keep"],
                           "warm_equals_keep_reason": warm["warm_equals_keep_reason"],
                           "evaluations": warm["evaluations"]}
        rows.append(row)
        post = " ".join(f"{rule}={record['rules'][rule]['post_event_mean']:.4f}" for rule in rules)
        print(f"world={world} t_e={record['t_e']} class={event['routing_class']} {post} "
              f"wall={record['timing']['world_total']['wall_s']:.1f}s", flush=True)

    components = sorted({key for row in rows for key in row["timing"]})

    def timing_stats(component: str) -> dict[str, Any]:
        values = [row["timing"][component] for row in rows if component in row["timing"]]
        if values and "wall_s" not in values[0]:  # {"plan": {...}, "rollout": {...}}
            return {part: {k: stats([v[part][k] for v in values]) for k in ("wall_s", "cpu_s")}
                    for part in values[0]}
        return {k: stats([v[k] for v in values]) for k in ("wall_s", "cpu_s")}

    summary = {
        **common, "tool": "coupled_host_replan_timing.run_r1lite", "rules": list(rules),
        "definitions": {
            "S_switch": "warm - keep (post-event C_bh, per world, then paired across worlds)",
            "S_cold": "warm - cold (post-event C_bh, per world, then paired across worlds)",
            "transition_loss_steps": "post-event steps with C_bh below the world's pre-event mean",
            "arrival_step": "first step >= t_e at which every UAV sat on the rule's final targets",
            "S_seeded": "seeded - keep (post-event C_bh, per world, then paired across worlds)",
            "warm": "held re-placement only (non-movable UAVs keep their targets); empty movable "
                    "set -> single-UAV fallback at 500 evaluations per candidate, adopted only "
                    "above the held layout's static reward, else warm == KEEP",
            "seeded": "cold relay search seeded with the pre-event sites; all UAVs may move",
        },
        "per_world": rows,
        "means": ordinary_summary(rows, rules),
        "timing_per_world": {component: timing_stats(component) for component in components},
        "cpu_seconds": _cpu_seconds(), "start_utc": started_utc, "end_utc": _utc_now(),
        "wall_clock_s": time.perf_counter() - started,
    }
    write_json(out / "summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
