#!/usr/bin/env python3
"""Teacher runner (coupled_host_planner_distillation, cell b01 piece 1): T_10 closed loop, zero fits.

Per world (``teacher.run_teacher_episode``): T_10 on a fresh static host for 500 host steps (50
macro decisions), the label replay check on a second fresh host, and the reading
``t10_minus_b0 = T_10 all-500 - committed b04 B0 all-500`` where the b04 dev run holds the world
(``runs/coupled_host_joint_skills_stage1/b04_b0_dev_a01/summary.json``, sha256 recorded; null
elsewhere).

Writes ``worlds/<world>.json`` (features [50][6][174] and labels [50][6][3] as lists, the C_bh
series, the per-decision record) and ``summary.json`` (per-world rows, means, planner calls, CPU
split planner / assignment / rest, the 64-world CPU projection, git_head, launch_sha, arguments,
interpreter).  Admission as in ``coupled_host_joint_skills_stage1/run_b04.py``; a direct invocation
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

from experiments.candidates.coupled_host_joint_skills_stage1.adapter import (  # noqa: E402
    DEV_WORLDS,
    HOLDOUT_WORLDS,
)
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
    timed,
)

SCHEMA = 1
DIRECTION = "coupled_host_planner_distillation"
DEFAULT_B04_RUN = Path("runs") / "coupled_host_joint_skills_stage1" / "b04_b0_dev_a01"
TRAINING_WORLDS_DECLARED = tuple(range(3000, 3064))
MAX_WORLD_JSON_BYTES = 2 * 1024 * 1024
ROW_KEYS = ("all_mean", "final_100_mean", "b04_B0_all_mean", "t10_minus_b0", "planner_calls",
            "evaluations_used", "cap_hit", "trigger_steps", "hold_decisions_before_first_plan",
            "users_known_terminal", "decisions", "samples", "cpu_s", "label_box_faces",
            "replay", "world_json_bytes")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_teacher.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--worlds", nargs="+", required=True,
                        help="world (reset) seeds: integers and inclusive ranges a-b")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--budget", type=int, default=3000,
                        help="static-evaluation ceiling per planner search (flat and relay each)")
    parser.add_argument("--probe", type=int, default=None, help="run only the first N worlds")
    parser.add_argument("--launch-sha", default=None, help="published source sha of this launch")
    parser.add_argument("--b04-run", type=Path, default=DEFAULT_B04_RUN,
                        help="committed b04 B0 run directory (relative paths resolve against the "
                             "data root)")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting existing scientific outputs in --out")
    return parser


def resolve_out(path: Path) -> Path:
    return path if path.is_absolute() else canonical_data_root(ROOT) / path


def world_payload(episode: dict[str, Any], b04_all: float | None) -> dict[str, Any]:
    decisions = episode["decisions"]
    return {
        "world": episode["world"], "horizon": episode["horizon"], "budget": episode["budget"],
        "all_mean": episode["all_mean"], "final_100_mean": episode["final_100_mean"],
        "b04_B0_all_mean": b04_all,
        "t10_minus_b0": None if b04_all is None else episode["all_mean"] - b04_all,
        "teacher": episode["teacher"], "label_box_faces": episode["label_box_faces"],
        "replay": episode["replay"], "cpu_s": episode["cpu_s"],
        "coverage_backhauled": episode["coverage_backhauled"],
        "decision_record": [{k: d[k] for k in ("step", "n_known", "newly_known_since_plan", "planned",
                                                "cap_hit", "evaluations", "planner_calls")}
                            for d in decisions],
        "features_layout": "features[decision][ego][174] (teacher.features); labels[decision][uav][xyz m]",
        "features": [d["features"] for d in decisions],
        "labels": episode["labels"],
    }


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

        admission: Any = dict(require_admission(__file__, direction="coupled_host_planner_distillation"))
        if args.launch_sha != admission["sha"]:
            print("error: --launch-sha disagrees with the admitted sha", file=sys.stderr)
            return 2
    else:
        admission = {"status": "absent (direct invocation; zero-fit study, admission not required)"}

    started_utc, started = _utc_now(), time.perf_counter()
    import numpy as np

    from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
    from experiments.candidates.coupled_host_planner_distillation import teacher as T

    out = resolve_out(Path(args.out))
    existing = [name for name in ("summary.json", "worlds") if (out / name).exists()]
    if existing and not args.force:
        print(f"error: {out} already holds {existing}; pass --force", file=sys.stderr)
        return 2
    b04_dir = Path(args.b04_run)
    if not b04_dir.is_absolute():
        b04_dir = canonical_data_root(ROOT) / b04_dir
    b04_bytes = (b04_dir / "summary.json").read_bytes()
    b04 = json.loads(b04_bytes)
    b04_by_world = {int(r["world"]): float(r["B0"]["all_mean"]) for r in b04["per_world"]}
    b04_cpu_per_world = float(b04["timing_totals"]["cpu_s_b0"]) / len(b04["per_world"])
    if int(b04["budget"]) != int(args.budget):
        print(f"note: b04 run budget {b04['budget']} != --budget {args.budget}; t10_minus_b0 is "
              "not interface-matched", file=sys.stderr)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for world in worlds:
        episode, timing = timed(T.run_teacher_episode, int(world), args.budget)
        b04_all = b04_by_world.get(int(world))
        payload = world_payload(episode, b04_all)
        payload["timing"] = timing
        path = out / "worlds" / f"{int(world)}.json"
        write_json(path, payload, indent=None)
        size = path.stat().st_size
        rec = episode["teacher"]
        row = {"world": int(world), "all_mean": episode["all_mean"],
               "final_100_mean": episode["final_100_mean"], "b04_B0_all_mean": b04_all,
               "t10_minus_b0": payload["t10_minus_b0"], "planner_calls": rec["planner_calls"],
               "evaluations_used": rec["evaluations_used"], "cap_hit": rec["cap_hit"],
               "trigger_steps": rec["trigger_steps"],
               "hold_decisions_before_first_plan": rec["hold_decisions_before_first_plan"],
               "users_known_terminal": rec["users_known_terminal"], "decisions": rec["decisions"],
               "samples": rec["decisions"] * T.N_UAVS, "cpu_s": episode["cpu_s"],
               "label_box_faces": episode["label_box_faces"], "replay": episode["replay"],
               "world_json_bytes": int(size), "timing": timing}
        rows.append(row)
        b0_text = "n/a" if b04_all is None else f"{b04_all:.4f}"
        diff_text = "n/a" if b04_all is None else f"{payload['t10_minus_b0']:+.4f}"
        print(f"world={world} T10={episode['all_mean']:.4f} T10_f100={episode['final_100_mean']:.4f} "
              f"B0={b0_text} t10_minus_b0={diff_text} planner_calls={rec['planner_calls']} "
              f"trigger_steps={rec['trigger_steps']} evals={rec['evaluations_used']} "
              f"cpu_planner={episode['cpu_s']['planner']:.2f}s cpu_total={episode['cpu_s']['total']:.2f}s "
              f"cpu_world_incl_replay={timing['cpu_s']:.2f}s decisions={rec['decisions']} "
              f"features={rec['decisions']}x{T.N_UAVS}x{T.FEATURE_DIM} labels={rec['decisions']}x{T.N_UAVS}x3 "
              f"z_low_labels={episode['label_box_faces']['z_low']}/{episode['label_box_faces']['labels']} "
              f"json={size / 1e6:.2f}MB replay_identical={episode['replay']['series_identical']}",
              flush=True)
        if size > MAX_WORLD_JSON_BYTES:
            print(f"warning: {path} is {size} bytes (> {MAX_WORLD_JSON_BYTES})", file=sys.stderr)

    n_train = len(TRAINING_WORLDS_DECLARED)
    world_cpu = [r["timing"]["cpu_s"] for r in rows]
    means: dict[str, Any] = {
        "T10_all_mean": _mean_sd([r["all_mean"] for r in rows]),
        "T10_final_100_mean": _mean_sd([r["final_100_mean"] for r in rows]),
        "t10_minus_b0": _mean_sd([r["t10_minus_b0"] for r in rows if r["t10_minus_b0"] is not None]),
        "planner_calls": _mean_sd([r["planner_calls"] for r in rows]),
        "evaluations_used": _mean_sd([r["evaluations_used"] for r in rows]),
        "cpu_planner_s": _mean_sd([r["cpu_s"]["planner"] for r in rows]),
        "cpu_teacher_total_s": _mean_sd([r["cpu_s"]["total"] for r in rows]),
        "cpu_world_incl_replay_s": _mean_sd(world_cpu),
        "cap_hits": int(sum(r["cap_hit"] for r in rows)),
        "world_json_bytes_max": max((r["world_json_bytes"] for r in rows), default=None),
        "label_components_on_z_low": int(sum(r["label_box_faces"]["z_low"] for r in rows)),
        "labels": int(sum(r["label_box_faces"]["labels"] for r in rows)),
    }
    projection = {
        "training_worlds": n_train,
        "probe_mean_basis_cpu_s": (float(np.mean(world_cpu)) * n_train) if rows else None,
        "b04_mean_basis_cpu_s": b04_cpu_per_world * n_train,
        "b04_cpu_s_per_world": b04_cpu_per_world,
        "note": ("teacher trajectories only (segment A data, replay check included in the probe "
                 "basis); the b04 basis is B0's per-world CPU (pooling every host step, no replay) "
                 "on the 32 dev worlds, a cross-check"),
    }
    summary = {
        "schema": SCHEMA, "direction": DIRECTION, "cell": "b01", "piece": "1 (teacher T_10, zero fit)",
        "tool": "coupled_host_planner_distillation.run_teacher",
        "launch_sha": args.launch_sha, "admission": admission, "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0, "worlds": worlds, "budget": int(args.budget),
        "worlds_in_dev_panel": [w for w in worlds if w in DEV_WORLDS],
        "worlds_in_holdout_panel": [w for w in worlds if w in HOLDOUT_WORLDS],
        "b04_run": {"path": str(b04_dir), "summary_sha256": hashlib.sha256(b04_bytes).hexdigest(),
                    "launch_sha": b04.get("launch_sha"), "budget": b04.get("budget")},
        "information_contract": {
            "macro_k": T.MACRO_K, "decisions_per_episode": T.N_DECISIONS,
            "trigger_new_known": B4.TRIGGER_NEW_KNOWN, "max_replans": B4.MAX_REPLANS,
            "min_known_for_search": B4.MIN_KNOWN_FOR_SEARCH, "pooling": T.POOLING,
            "hold_rule": T.HOLD_RULE, "shadow_user_set": B4.SHADOW_USER_SET,
            "no_event_t_e": B4.NO_EVENT_T_E,
            "sightings": "every user env._get_local_users(i) returns (uncapped), read row by row"},
        "features": {"dim": T.FEATURE_DIM,
                     "layout": "50 x [known, x/5000, y/5000] (user index order; unknown -> 0) + "
                               "6 x [x/5000, y/5000, (z-50)/100] + ego one-hot(6)"},
        "labels": "held targets in box coordinates (m), UAV-indexed, one row per decision",
        "definitions": {
            "all_mean": "mean C_bh over the 500 host steps of T_10",
            "final_100_mean": "mean C_bh over steps 400..499 of T_10",
            "b04_B0_all_mean": "committed b04 B0 all-500 C_bh (per-step pooling and trigger)",
            "t10_minus_b0": "all_mean - b04_B0_all_mean (a reading, not a gate)",
            "cpu_s.planner": "process CPU inside B4.plan_on_known (flat + relay searches)",
            "cpu_s.assign": "process CPU inside B4.assign_targets",
            "cpu_s.rest": "teacher episode CPU minus planner and assignment (host steps, pooling, features)",
            "replay": "labels replayed on a second fresh host under the same 10-step hold; C_bh and "
                      "reward series asserted identical",
            "label_box_faces": "label components within 1e-9 m of each face of the target box"},
        "per_world": rows, "means": means, "cpu_projection": projection,
        "cpu_seconds": _cpu_seconds(), "start_utc": started_utc, "end_utc": _utc_now(),
        "wall_clock_s": time.perf_counter() - started,
        "arguments": sys.argv[1:] if argv is None else list(argv),
        "interpreter": {"executable": sys.executable, "python": platform.python_version(),
                        "numpy": np.__version__, "host": platform.node()},
    }
    write_json(out / "summary.json", summary)
    print(f"projection_64_worlds: probe_basis={projection['probe_mean_basis_cpu_s']:.1f}s "
          f"b04_basis={projection['b04_mean_basis_cpu_s']:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
