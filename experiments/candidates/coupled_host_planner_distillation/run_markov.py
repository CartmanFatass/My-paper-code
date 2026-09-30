#!/usr/bin/env python3
"""T_M runner (coupled_host_planner_distillation, cell b01 piece 2): Markov teacher, zero fits.

Per world (``teacher_markov.run_markov_episode``): T_M (planner seed ``--seed``, budget
``--budget``) on a fresh static host for 500 host steps, the target replay check on a second fresh
host, and the reading ``tm_minus_b0 = T_M all-500 - committed b04 B0 all-500`` where the b04 dev
run holds the world (``runs/coupled_host_joint_skills_stage1/b04_b0_dev_a01/summary.json``, sha256
recorded; null elsewhere).  ``--budget 200`` is T_M-200, the compute comparator.

Dev-panel mode (default): labelled decisions carry the control seed's layout only.  Segment-A
mode (``--label-seeds 0 1 2``): every re-plan also carries the layouts of the other seeds, planned
on the same known map and positions (their CPU is reported apart from the control planner CPU).

Writes ``worlds/<world>.json`` (C_bh series, per-decision record, labelled decisions with the 168
shared features, positions and seed layouts) and ``summary.json`` (per-world rows, means, plan
counts, cache hits, hold steps, label counts, ``labels_z_all_50``, box-face counts, CPU split and
totals, projections, git_head, launch_sha, arguments, interpreter).  Admission as in
``run_teacher.py``; a direct invocation records ``admission = absent``.
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
LABEL_WORLDS_DECLARED = tuple(range(3000, 3128))       # segment A (pre-declaration item 6)
DEV_PANEL_SIZE = 32
MAX_WORLD_JSON_BYTES = 2 * 1024 * 1024
ROW_KEYS = ("all_mean", "final_100_mean", "b04_B0_all_mean", "tm_minus_b0", "planner_calls",
            "plan_steps", "cache_hits", "assignment_changes", "hold_decisions", "hold_steps",
            "evaluations_used", "users_known_terminal", "decisions", "labelled_decisions",
            "layouts_z_all_50", "layout_box_faces", "cpu_s", "replay", "world_json_bytes")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_markov.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--worlds", nargs="+", required=True,
                        help="world (reset) seeds: integers and inclusive ranges a-b")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--budget", type=int, default=3000,
                        help="static-evaluation ceiling per planner search (flat and relay each)")
    parser.add_argument("--seed", type=int, default=0,
                        help="constant planner RNG seed of the control plan (never the world id)")
    parser.add_argument("--label-seeds", type=int, nargs="+", default=None,
                        help="segment-A mode: seeds of the labelled layouts, control seed first")
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
    keys = ("step", "n_known", "hold", "replanned", "cache_hit", "assignment_changed", "evaluations")
    return {
        "world": episode["world"], "horizon": episode["horizon"], "budget": episode["budget"],
        "seed": episode["seed"], "label_seeds": episode["label_seeds"],
        "all_mean": episode["all_mean"], "final_100_mean": episode["final_100_mean"],
        "b04_B0_all_mean": b04_all,
        "tm_minus_b0": None if b04_all is None else episode["all_mean"] - b04_all,
        "teacher": episode["teacher"], "layout_box_faces": episode["layout_box_faces"],
        "layouts_z_all_50": episode["layouts_z_all_50"],
        "replay": episode["replay"], "cpu_s": episode["cpu_s"],
        "coverage_backhauled": episode["coverage_backhauled"],
        "decision_record": [{k: d[k] for k in keys} | {"targets": d["targets"]}
                            for d in episode["decisions"]],
        "labelled_layout": ("labelled[i] = {step, known (sorted user ids), features[168] "
                            "(teacher_markov.features_shared), positions[6][3] (m, UAV-indexed), "
                            "seeds, layouts[seed][site][xyz m] (planner site order; seeds[0] is "
                            "the control layout), targets[6][3] (control layout assigned)}"),
        "labelled": episode["labelled"],
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
    label_seeds = None if args.label_seeds is None else tuple(args.label_seeds)
    if label_seeds is not None and (label_seeds[0] != args.seed or len(set(label_seeds)) != len(label_seeds)):
        parser.error("--label-seeds must be distinct and start with --seed")
    label_mode = label_seeds is not None and len(label_seeds) > 1

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
    from experiments.candidates.coupled_host_planner_distillation import teacher_markov as TM

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
    if int(b04["budget"]) != int(args.budget):
        print(f"note: b04 run budget {b04['budget']} != --budget {args.budget}; tm_minus_b0 compares "
              "different planner budgets", file=sys.stderr)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for world in worlds:
        episode, timing = timed(TM.run_markov_episode, int(world), args.budget, args.seed,
                                label_seeds=label_seeds)
        b04_all = b04_by_world.get(int(world))
        payload = world_payload(episode, b04_all)
        payload["timing"] = timing
        path = out / "worlds" / f"{int(world)}.json"
        write_json(path, payload, indent=None)
        size = path.stat().st_size
        rec = episode["teacher"]
        row = {"world": int(world), "all_mean": episode["all_mean"],
               "final_100_mean": episode["final_100_mean"], "b04_B0_all_mean": b04_all,
               "tm_minus_b0": payload["tm_minus_b0"], "planner_calls": rec["planner_calls"],
               "plan_steps": rec["plan_steps"], "cache_hits": rec["cache_hits"],
               "assignment_changes": rec["assignment_changes"],
               "hold_decisions": rec["hold_decisions"], "hold_steps": rec["hold_steps"],
               "evaluations_used": rec["evaluations_used"],
               "users_known_terminal": rec["users_known_terminal"], "decisions": rec["decisions"],
               "labelled_decisions": rec["labelled_decisions"],
               "layouts_z_all_50": episode["layouts_z_all_50"],
               "layout_box_faces": episode["layout_box_faces"], "cpu_s": episode["cpu_s"],
               "replay": episode["replay"], "world_json_bytes": int(size), "timing": timing}
        rows.append(row)
        b0_text = "n/a" if b04_all is None else f"{b04_all:.4f}"
        diff_text = "n/a" if b04_all is None else f"{payload['tm_minus_b0']:+.4f}"
        faces = episode["layout_box_faces"]
        print(f"world={world} budget={args.budget} TM={episode['all_mean']:.4f} "
              f"TM_f100={episode['final_100_mean']:.4f} B0={b0_text} tm_minus_b0={diff_text} "
              f"plans={rec['planner_calls']} plan_steps={rec['plan_steps']} "
              f"cache_hits={rec['cache_hits']} assign_changes={rec['assignment_changes']} "
              f"hold_steps={rec['hold_steps']} evals={rec['evaluations_used']} "
              f"labelled={rec['labelled_decisions']}x{len(episode['label_seeds'])}seeds "
              f"z_all_50={episode['layouts_z_all_50']} "
              f"faces(x0/x1/y0/y1/z0/z1/any/n)={faces['x_low']}/{faces['x_high']}/{faces['y_low']}/"
              f"{faces['y_high']}/{faces['z_low']}/{faces['z_high']}/{faces['labels_on_any_face']}/"
              f"{faces['labels']} cpu_planner={episode['cpu_s']['planner']:.2f}s "
              f"cpu_label_planner={episode['cpu_s']['label_planner']:.2f}s "
              f"cpu_total={episode['cpu_s']['total']:.2f}s cpu_world_incl_replay={timing['cpu_s']:.2f}s "
              f"json={size / 1e6:.3f}MB replay_identical={episode['replay']['series_identical']}",
              flush=True)
        if size > MAX_WORLD_JSON_BYTES:
            print(f"warning: {path} is {size} bytes (> {MAX_WORLD_JSON_BYTES})", file=sys.stderr)

    world_cpu = [r["timing"]["cpu_s"] for r in rows]
    face_keys = ("x_low", "x_high", "y_low", "y_high", "z_low", "z_high", "labels", "labels_on_any_face")
    means: dict[str, Any] = {
        "TM_all_mean": _mean_sd([r["all_mean"] for r in rows]),
        "TM_final_100_mean": _mean_sd([r["final_100_mean"] for r in rows]),
        "tm_minus_b0": _mean_sd([r["tm_minus_b0"] for r in rows if r["tm_minus_b0"] is not None]),
        "planner_calls": _mean_sd([r["planner_calls"] for r in rows]),
        "cache_hits": _mean_sd([r["cache_hits"] for r in rows]),
        "hold_steps": _mean_sd([r["hold_steps"] for r in rows]),
        "evaluations_used": _mean_sd([r["evaluations_used"] for r in rows]),
        "labelled_decisions": _mean_sd([r["labelled_decisions"] for r in rows]),
        "cpu_planner_s": _mean_sd([r["cpu_s"]["planner"] for r in rows]),
        "cpu_label_planner_s": _mean_sd([r["cpu_s"]["label_planner"] for r in rows]),
        "cpu_teacher_total_s": _mean_sd([r["cpu_s"]["total"] for r in rows]),
        "cpu_world_incl_replay_s": _mean_sd(world_cpu),
        "world_json_bytes_max": max((r["world_json_bytes"] for r in rows), default=None),
    }
    labels_total = int(sum(r["labelled_decisions"] for r in rows))
    box_faces = {k: int(sum(r["layout_box_faces"][k] for r in rows)) for k in face_keys}
    labels_z_all_50 = bool(rows) and all(r["layouts_z_all_50"] for r in rows if r["labelled_decisions"])
    mean_world_cpu = float(np.mean(world_cpu)) if rows else None
    projection = {
        "per_world_cpu_s_incl_replay": mean_world_cpu,
        "dev_panel_worlds": DEV_PANEL_SIZE,
        "dev_panel_cpu_s": None if mean_world_cpu is None else mean_world_cpu * DEV_PANEL_SIZE,
        "label_worlds": len(LABEL_WORLDS_DECLARED),
        "label_worlds_cpu_s": None if mean_world_cpu is None else mean_world_cpu * len(LABEL_WORLDS_DECLARED),
        "note": ("probe-mean basis: per-world CPU (T_M episode, label planners in label mode and the "
                 "replay check) times the world count; applies to the mode and budget of this run"),
    }
    summary = {
        "schema": SCHEMA, "direction": DIRECTION, "cell": "b01",
        "piece": "2 (Markov teacher T_M, zero fit)", "tool": "coupled_host_planner_distillation.run_markov",
        "launch_sha": args.launch_sha, "admission": admission, "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0, "worlds": worlds, "budget": int(args.budget),
        "seed": int(args.seed), "label_seeds": None if label_seeds is None else list(label_seeds),
        "mode": "segment_A_labels" if label_mode else "dev_panel",
        "worlds_in_dev_panel": [w for w in worlds if w in DEV_WORLDS],
        "worlds_in_holdout_panel": [w for w in worlds if w in HOLDOUT_WORLDS],
        "worlds_in_label_set": [w for w in worlds if w in LABEL_WORLDS_DECLARED],
        "b04_run": {"path": str(b04_dir), "summary_sha256": hashlib.sha256(b04_bytes).hexdigest(),
                    "launch_sha": b04.get("launch_sha"), "budget": b04.get("budget")},
        "information_contract": {
            "macro_k": T.MACRO_K, "decisions_per_episode": T.N_DECISIONS,
            "min_known_for_search": B4.MIN_KNOWN_FOR_SEARCH, "pooling": TM.POOLING,
            "trigger": TM.TRIGGER, "hold_rule": TM.HOLD_RULE, "planner_cap": None,
            "planner_seed": "constant --seed (the planner's world argument is only its RNG seed)",
            "shadow_user_set": B4.SHADOW_USER_SET, "no_event_t_e": B4.NO_EVENT_T_E,
            "sightings": "every user env._get_local_users(i) returns (uncapped), read row by row"},
        "features": {"dim": TM.SHARED_FEATURE_DIM,
                     "layout": "50 x [known, x/5000, y/5000] (user index order; unknown -> 0) + "
                               "6 x [x/5000, y/5000, (z-50)/100] (teacher.features without ego)"},
        "definitions": {
            "all_mean": "mean C_bh over the 500 host steps of T_M",
            "final_100_mean": "mean C_bh over steps 400..499 of T_M",
            "b04_B0_all_mean": "committed b04 B0 all-500 C_bh (budget 3000, world-seeded planner)",
            "tm_minus_b0": "all_mean - b04_B0_all_mean (a reading, not a gate)",
            "planner_calls": "control plans (re-plans), one per distinct known set with >= 6 users",
            "cache_hits": "decisions with >= 6 known whose known set equals the last plan's set",
            "assignment_changed": TM.ASSIGNMENT_CHANGED,
            "hold_steps": "host steps whose targets are the spawn positions because no plan exists",
            "labelled_decisions": "one per re-plan; layouts for every label seed",
            "labels_z_all_50": "every z of every labelled layout (all seeds) equals 50 m exactly",
            "layout_box_faces": "labelled-layout components within 1e-9 m of each face of the box",
            "cpu_s.planner": "process CPU inside the control-seed B4.plan_on_known calls",
            "cpu_s.label_planner": "process CPU inside the extra label-seed plan_on_known calls",
            "cpu_s.assign": "process CPU inside B4.assign_targets",
            "cpu_s.rest": "episode CPU minus planner, label planner and assignment",
            "replay": "per-decision targets replayed on a second fresh host under the same 10-step "
                      "hold; C_bh and reward series asserted identical"},
        "per_world": rows, "means": means, "labels_total": labels_total,
        "labels_z_all_50": labels_z_all_50, "box_faces": box_faces, "cpu_projection": projection,
        "cpu_seconds": _cpu_seconds(), "start_utc": started_utc, "end_utc": _utc_now(),
        "wall_clock_s": time.perf_counter() - started,
        "arguments": sys.argv[1:] if argv is None else list(argv),
        "interpreter": {"executable": sys.executable, "python": platform.python_version(),
                        "numpy": np.__version__, "host": platform.node()},
    }
    write_json(out / "summary.json", summary)
    if rows:
        print(f"projection: per_world={mean_world_cpu:.2f}s dev32={projection['dev_panel_cpu_s']:.1f}s "
              f"label128={projection['label_worlds_cpu_s']:.1f}s labels_total={labels_total} "
              f"labels_z_all_50={labels_z_all_50}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
