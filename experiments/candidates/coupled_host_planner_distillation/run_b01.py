#!/usr/bin/env python3
"""Student runner (coupled_host_planner_distillation, cell b01 piece 3): fit and evaluate.

``--phase fit``: S0 (seed 932201) -> S_bc (segment A, 300 epochs) -> one DAgger round on
``--dagger-worlds`` (3-seed relabelling of every forward-pass decision) -> S (A u B, fresh Adam,
150 epochs) via ``train.train_all``.  Writes ``s0/s_bc/s`` as ``.pt`` and ``.json`` (float32
state_dict + meta; the JSON is the committable copy), ``dagger/<world>.json`` and
``training.json`` (loss curves, N_A / N_B, K, CPU per phase, seeds, architecture, checkpoint
digests) with the open-loop reading: on every labelled decision of ``--dev-visited`` (the T_M dev
run, seed-0 layouts only, K = 1) the min-over-permutations loss of S, S_bc and S0, compared with
the SAME K = 1 (seed-0) metric on the training segments (the K = 3 training metric is reported
beside it, not compared).

``--phase evaluate``: S, S_bc, S0 closed loop on ``--worlds`` (500 host steps each, one host
constructor ``B4.make_static_host``), plus S with per-world permuted user indices in the feature
encoding (reading only), against the committed T_M / T_M-200 dev runs and b04's B0 and F.
Writes ``worlds/<world>.json`` and ``summary.json`` (paired all-500 statistics, per-world
negatives, online CPU, purchase-line flags exactly as declared).

Admission: one ``require_admission`` for either phase.  A direct invocation (no admission) is a
smoke: ``--out`` must lie under the checkout's ``temp/``; declared constants may then be overridden
(``--epochs-a/--epochs-b/--budget/--horizon``) and the output is marked non-decision-bearing.
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

from experiments.candidates.coupled_host_joint_skills_stage1.adapter import DEV_WORLDS  # noqa: E402
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
)

SCHEMA = 1
DIRECTION = "coupled_host_planner_distillation"
RUNS = Path("runs")
DEFAULT_TM_RUN = RUNS / DIRECTION / "b01_tm_dev_a01"
DEFAULT_TM200_RUN = RUNS / DIRECTION / "b01_tm200_dev_a01"
DEFAULT_B04_RUN = RUNS / "coupled_host_joint_skills_stage1" / "b04_b0_dev_a01"
PURCHASE = {"S_min": 0.71, "S_minus_TM_min": -0.03, "TM_min": 0.70, "band_low": 0.64}
PAIRS = (("S", "T_M"), ("S", "B0"), ("S", "S_bc"), ("S_bc", "S0"), ("S_perm", "S"),
         ("T_M200", "T_M"), ("F", "S"))
STUDENTS = (("S", "s"), ("S_bc", "s_bc"), ("S0", "s0"))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="run_b01.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--phase", required=True, choices=("fit", "evaluate"))
    p.add_argument("--out", required=True, type=Path, help="output directory")
    p.add_argument("--launch-sha", default=None, help="published source sha of this launch")
    p.add_argument("--force", action="store_true", help="allow overwriting outputs in --out")
    # fit
    p.add_argument("--segment-a", type=Path, help="run_markov label-mode run dir (K = 3)")
    p.add_argument("--dagger-worlds", nargs="+", default=["3000-3063"])
    p.add_argument("--dev-visited", type=Path, default=DEFAULT_TM_RUN,
                   help="T_M dev run (seed-0 labelled decisions) for the open-loop reading")
    p.add_argument("--epochs-a", type=int, default=None, help="smoke only (declared 300)")
    p.add_argument("--epochs-b", type=int, default=None, help="smoke only (declared 150)")
    p.add_argument("--budget", type=int, default=None, help="smoke only (declared 3000)")
    # evaluate
    p.add_argument("--checkpoints", type=Path, help="fit output dir (s0/s_bc/s .json and/or .pt)")
    p.add_argument("--worlds", nargs="+", default=["1000-1031"])
    p.add_argument("--tm-run", type=Path, default=DEFAULT_TM_RUN)
    p.add_argument("--tm200-run", type=Path, default=DEFAULT_TM200_RUN)
    p.add_argument("--b04-run", type=Path, default=DEFAULT_B04_RUN)
    p.add_argument("--horizon", type=int, default=None, help="smoke only (declared 500)")
    return p


def data_path(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else canonical_data_root(ROOT) / path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smoke_refusal(out: Path) -> str | None:
    temp_root = (canonical_data_root(ROOT) / "temp").resolve()
    resolved = out.resolve()
    if temp_root not in resolved.parents:
        return f"a direct (non-admitted) invocation needs --out under {temp_root}"
    return None


def paired(rows: list[dict[str, Any]], a: str, b: str) -> dict[str, Any]:
    import numpy as np

    diffs = [(r["world"], r[a] - r[b]) for r in rows if r.get(a) is not None and r.get(b) is not None]
    values = np.array([d for _w, d in diffs], dtype=float)
    stats = _mean_sd(values.tolist())
    stats["se"] = (stats["sd"] / float(np.sqrt(values.size))) if stats["sd"] is not None else None
    stats["n_positive"] = int(np.sum(values > 0))
    stats["negatives"] = [{"world": int(w), "diff": float(d)} for w, d in diffs if d < 0]
    return stats


# ============================================================ fit


def run_fit(args, meta: dict[str, Any], log) -> dict[str, Any]:
    import numpy as np

    from experiments.candidates.coupled_host_planner_distillation import student as S
    from experiments.candidates.coupled_host_planner_distillation import train as TR

    if args.segment_a is None:
        raise SystemExit("error: --phase fit needs --segment-a")
    dagger_worlds = parse_worlds(args.dagger_worlds)
    used = {"epochs_a": TR.EPOCHS_A if args.epochs_a is None else args.epochs_a,
            "epochs_b": TR.EPOCHS_B if args.epochs_b is None else args.epochs_b,
            "budget": TR.PLANNER_BUDGET if args.budget is None else args.budget,
            "horizon": S.HORIZON if args.horizon is None else args.horizon}
    declared = (used == {"epochs_a": TR.EPOCHS_A, "epochs_b": TR.EPOCHS_B,
                         "budget": TR.PLANNER_BUDGET, "horizon": S.HORIZON}
                and tuple(dagger_worlds) == TR.DAGGER_WORLDS)
    if meta["admitted"] and not declared:
        raise SystemExit("error: an admitted fit uses the declared constants and worlds 3000-3063 only")
    seg_dir = data_path(args.segment_a)
    result = TR.train_all(seg_dir, dagger_worlds, meta["out"], log=log, **used)
    nets = result.pop("nets")
    dev_dir = data_path(args.dev_visited)
    X_d, Y_d, dev_meta = TR.load_labelled(dev_dir, allow_panels=True)
    if dev_meta["seeds"] != [0]:
        raise ValueError(f"--dev-visited must carry seed-0 layouts only, got {dev_meta['seeds']}")
    dev = {name: TR.dataset_loss(net, X_d, Y_d) for name, net in nets.items()}
    train_ol = result["train_open_loop"]
    comparison = {}
    for name in nets:
        a_k1 = train_ol["segment_A"][name]["K1_seed0"]["mean"]
        comparison[name] = {"train_A_K1_seed0": a_k1,
                            "train_A_K_full": train_ol["segment_A"][name]["K_full"]["mean"],
                            "dev_visited_K1_seed0": dev[name]["mean"],
                            "dev_minus_train_K1": dev[name]["mean"] - a_k1}
    phases = result["phases"]
    training = {
        **meta["header"], "phase": "fit", "decision_bearing": bool(meta["admitted"] and declared),
        "declared_constants_used": declared, "architecture": S.ARCHITECTURE,
        "seeds": {"init": S.INIT_SEED, "shuffle": TR.SHUFFLE_SEED, "label_seeds": list(TR.LABEL_SEEDS)},
        "data": result["data"], "declared": result["declared"], "used": result["used"],
        "loss_curves": {"segment_A": phases["segment_A"]["epoch_loss"],
                        "segment_B": phases["segment_B"]["epoch_loss"]},
        "phases": {"segment_A": {k: v for k, v in phases["segment_A"].items() if k != "epoch_loss"},
                   "dagger": phases["dagger"],
                   "segment_B": {k: v for k, v in phases["segment_B"].items() if k != "epoch_loss"}},
        "cpu_per_phase_s": {"segment_A_fit": phases["segment_A"]["cpu_s"],
                            "dagger_rollin_and_relabel": phases["dagger"]["cpu_s"],
                            "dagger_label_planner": phases["dagger"]["label_planner_cpu_s"],
                            "segment_B_fit": phases["segment_B"]["cpu_s"]},
        "checkpoints": result["checkpoints"],
        "open_loop": {"metric": ("per-item min over permutations (and over the K layouts given) of "
                                 "the mean site squared distance, box-normalised; K1_seed0 = the "
                                 "seed-0 layout only (the dev-visited states carry seed 0 only)"),
                      "train": train_ol,
                      "dev_visited": {"dir": str(dev_dir), "n": dev_meta["n"], "K": dev_meta["K"],
                                      "files_digest_sha256": dev_meta["files_digest_sha256"],
                                      "loss": dev},
                      "train_vs_dev_K1": comparison},
    }
    write_json(meta["out"] / "training.json", training)
    for name, c in comparison.items():
        log(f"open_loop {name}: train_A_K3={c['train_A_K_full']:.5f} train_A_K1={c['train_A_K1_seed0']:.5f} "
            f"dev_K1={c['dev_visited_K1_seed0']:.5f} dev-train_K1={c['dev_minus_train_K1']:+.5f}")
    log(f"fit done: N_A={result['data']['N_A']} N_B={result['data']['N_B']} K={result['data']['K']} "
        f"A_final={phases['segment_A']['final_loss']:.5f} B_final={phases['segment_B']['final_loss']:.5f} "
        f"cpu A={phases['segment_A']['cpu_s']:.1f}s dagger={phases['dagger']['cpu_s']:.1f}s "
        f"B={phases['segment_B']['cpu_s']:.1f}s")
    return training


# ============================================================ evaluate


def _run_rows(run_dir: Path) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    raw = (run_dir / "summary.json").read_bytes()
    summary = json.loads(raw)
    rows = {int(r["world"]): r for r in summary["per_world"]}
    return rows, {"path": str(run_dir), "summary_sha256": hashlib.sha256(raw).hexdigest(),
                  "launch_sha": summary.get("launch_sha"), "budget": summary.get("budget")}


def run_evaluate(args, meta: dict[str, Any], log) -> dict[str, Any]:
    import numpy as np

    from experiments.candidates.coupled_host_planner_distillation import student as S

    if args.checkpoints is None:
        raise SystemExit("error: --phase evaluate needs --checkpoints")
    worlds = parse_worlds(args.worlds)
    horizon = S.HORIZON if args.horizon is None else int(args.horizon)
    declared = horizon == S.HORIZON
    if meta["admitted"] and not declared:
        raise SystemExit("error: an admitted evaluation uses the declared horizon 500")
    ck_dir = data_path(args.checkpoints)
    nets, ck_meta = {}, {}
    for name, stem in STUDENTS:
        nets[name], m = S.load_checkpoint(ck_dir / f"{stem}.json")
        ck_meta[name] = {"meta": m, **{ext: (sha256_file(ck_dir / f"{stem}.{ext}")
                                             if (ck_dir / f"{stem}.{ext}").exists() else None)
                                       for ext in ("json", "pt")},
                         "loaded_from": "json" if (ck_dir / f"{stem}.json").exists() else "pt"}
    tm_rows, tm_ref = _run_rows(data_path(args.tm_run))
    tm200_rows, tm200_ref = _run_rows(data_path(args.tm200_run))
    b04_rows, b04_ref = _run_rows(data_path(args.b04_run))
    out = meta["out"]
    rows = []
    finite = True
    for world in worlds:
        arms: dict[str, Any] = {}
        episodes: dict[str, Any] = {}
        for name, net in nets.items():
            episodes[name] = S.run_student_episode(world, net, horizon=horizon)
        perm = S.world_user_perm(world)
        episodes["S_perm"] = S.run_student_episode(world, nets["S"], horizon=horizon, user_perm=perm)
        for name, ep in episodes.items():
            far = ep["far_cluster_backhauled_share"]
            arms[name] = {"all_mean": ep["all_mean"], "final_100_mean": ep["final_100_mean"],
                          "far_cluster_backhauled_share_mean": far["mean_all"],
                          "far_cluster_backhauled_share_final": far["final"],
                          "forward_passes": ep["student"]["forward_passes"],
                          "cache_hits": ep["student"]["cache_hits"],
                          "hold_steps": ep["student"]["hold_steps"],
                          "users_known_terminal": ep["student"]["users_known_terminal"],
                          "forward_cpu_per_pass_s": (float(np.mean(ep["forward_cpu_s"]))
                                                     if ep["forward_cpu_s"] else None),
                          "cpu_s": ep["cpu_s"], "replay": ep["replay"]}
            finite = finite and bool(np.isfinite(ep["all_mean"]) and np.isfinite(ep["final_100_mean"]))
        tm, tm200, b04 = tm_rows.get(world), tm200_rows.get(world), b04_rows.get(world)
        row = {"world": world,
               **{n: arms[n]["all_mean"] for n in arms},
               "T_M": None if tm is None else float(tm["all_mean"]),
               "T_M200": None if tm200 is None else float(tm200["all_mean"]),
               "B0": None if b04 is None else float(b04["B0"]["all_mean"]),
               "F": None if b04 is None else float(b04["F"]["all_mean"]),
               "final_100": {**{n: arms[n]["final_100_mean"] for n in arms},
                             "T_M": None if tm is None else tm["final_100_mean"],
                             "T_M200": None if tm200 is None else tm200["final_100_mean"],
                             "B0": None if b04 is None else b04["B0"]["final_100_mean"]},
               "online_cpu_s": {**{n: arms[n]["cpu_s"]["total"] for n in arms},
                                "T_M": None if tm is None else tm["cpu_s"]["total"],
                                "T_M200": None if tm200 is None else tm200["cpu_s"]["total"]},
               "arms": arms, "user_perm": perm.tolist()}
        rows.append(row)
        write_json(out / "worlds" / f"{world}.json",
                   {"world": world, "horizon": horizon, "row": row,
                    "episodes": {n: {"coverage_backhauled": ep["coverage_backhauled"],
                                     "decision_record": ep["decisions"], "student": ep["student"],
                                     "forward_cpu_s": ep["forward_cpu_s"]}
                                 for n, ep in episodes.items()}}, indent=None)
        tm_text = "n/a" if row["T_M"] is None else f"{row['T_M']:.4f}"
        log(f"world={world} S={row['S']:.4f} S_bc={row['S_bc']:.4f} S0={row['S0']:.4f} "
            f"S_perm={row['S_perm']:.4f} TM={tm_text} "
            f"fwd(S/S_bc/S0)={arms['S']['forward_passes']}/{arms['S_bc']['forward_passes']}/"
            f"{arms['S0']['forward_passes']} fwd_cpu/pass={arms['S']['forward_cpu_per_pass_s'] or 0:.5f}s "
            f"cpu(S)={arms['S']['cpu_s']['total']:.2f}s far(S)={arms['S']['far_cluster_backhauled_share_mean']:.3f}")
    arm_names = ("S", "S_bc", "S0", "S_perm", "T_M", "T_M200", "B0", "F")
    means = {n: _mean_sd([r[n] for r in rows if r[n] is not None]) for n in arm_names}
    means_f100 = {n: _mean_sd([r["final_100"][n] for r in rows if r["final_100"].get(n) is not None])
                  for n in ("S", "S_bc", "S0", "S_perm", "T_M", "T_M200", "B0")}
    online_cpu = {n: _mean_sd([r["online_cpu_s"][n] for r in rows if r["online_cpu_s"].get(n) is not None])
                  for n in ("S", "S_bc", "S0", "S_perm", "T_M", "T_M200")}
    far = {n: {"mean_all": _mean_sd([r["arms"][n]["far_cluster_backhauled_share_mean"] for r in rows]),
               "final": _mean_sd([r["arms"][n]["far_cluster_backhauled_share_final"] for r in rows])}
           for n in ("S", "S_bc", "S0", "S_perm")}
    pairs = {f"{a}-{b}": paired(rows, a, b) for a, b in PAIRS}
    s_mean, tm_mean = means["S"]["mean"], means["T_M"]["mean"]
    s_tm = pairs["S-T_M"]["mean"]
    panel_complete = tuple(worlds) == tuple(DEV_WORLDS) and declared
    flags = {"S_ge_0.71": None if s_mean is None else s_mean >= PURCHASE["S_min"],
             "S_minus_TM_ge_-0.03": None if s_tm is None else s_tm >= PURCHASE["S_minus_TM_min"],
             "TM_ge_0.70": None if tm_mean is None else tm_mean >= PURCHASE["TM_min"]}
    purchase = all(v is True for v in flags.values())
    band = ("purchase" if purchase else
            "partial" if (s_mean is not None and s_mean >= PURCHASE["band_low"]) else "stop")
    summary = {
        **meta["header"], "phase": "evaluate", "worlds": worlds, "horizon": horizon,
        "panel_complete": panel_complete,
        "decision_bearing": bool(meta["admitted"] and panel_complete),
        "checkpoints": {"dir": str(ck_dir), **ck_meta},
        "references": {"T_M": tm_ref, "T_M200": tm200_ref, "b04": b04_ref},
        "definitions": {
            "S/S_bc/S0": "student closed loop, 500 host steps, fresh B4.make_static_host(world)",
            "S_perm": ("S with the 50 user blocks of the feature encoding permuted by "
                       "default_rng([world, 7]).permutation(50) (user u -> slot perm[u]); map and "
                       "assignment unchanged; reading only"),
            "T_M/T_M200": "committed dev runs (all_mean, final_100_mean, cpu_s.total per world)",
            "B0/F": "committed b04 run per_world B0.all_mean / F.all_mean (gate)",
            "pair a-b": "per-world a - b of all-500 C_bh: mean, SD, SE = SD/sqrt(n), n_positive, negatives",
            "far_cluster_backhauled_share": ("harness reading, students only (the T_M runs did not "
                                             "record it): share of the far cluster's users backhauled "
                                             "in the state after each host step; mean and final"),
            "online_cpu_s": ("process CPU of the closed-loop episode excluding the replay check "
                             "(students: features + forward + assignment + host steps; T_M: the "
                             "teacher episode total incl. planner)")},
        "per_world": rows, "means_all_500": means, "means_final_100": means_f100,
        "online_cpu_per_episode_s": online_cpu, "far_cluster_backhauled_share": far,
        "paired_all_500": pairs,
        "purchase_line": {"rule": ("S >= .71 and S - T_M >= -.03 with T_M >= .70 -> purchase; "
                                   ".64 <= S otherwise -> partial; S < .64 -> stop"),
                          "thresholds": PURCHASE, "flags": flags, "purchase": purchase,
                          "band": band, "valid_panel": panel_complete},
        "technical_failure": {"non_finite": not finite},
    }
    write_json(out / "summary.json", summary)
    log(f"evaluate: S={s_mean:.4f} S_bc={means['S_bc']['mean']:.4f} S0={means['S0']['mean']:.4f} "
        f"S_perm={means['S_perm']['mean']:.4f} "
        f"S-T_M={'n/a' if s_tm is None else format(s_tm, '+.4f')} band={band} purchase={purchase} "
        f"panel_complete={panel_complete}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if os.environ.get(ADMISSION_ENV):
        from scripts.hmasd_admission import require_admission

        admission: Any = dict(require_admission(__file__, direction="coupled_host_planner_distillation"))
        if args.launch_sha != admission["sha"]:
            print("error: --launch-sha disagrees with the admitted sha", file=sys.stderr)
            return 2
        admitted = True
    else:
        admission = {"status": "absent (direct invocation; smoke only, --out under temp/)"}
        admitted = False
    out = data_path(args.out)
    if not admitted:
        refusal = smoke_refusal(out)
        if refusal:
            print(f"error: {refusal}", file=sys.stderr)
            return 2
    marker = "training.json" if args.phase == "fit" else "summary.json"
    if (out / marker).exists() and not args.force:
        print(f"error: {out} already holds {marker}; pass --force", file=sys.stderr)
        return 2
    started_utc, started = _utc_now(), time.perf_counter()
    import numpy as np
    import torch

    torch.set_num_threads(1)
    out.mkdir(parents=True, exist_ok=True)
    header = {"schema": SCHEMA, "direction": DIRECTION, "cell": "b01",
              "piece": "3 (student, layout loss, segment A + one DAgger round)",
              "tool": "coupled_host_planner_distillation.run_b01", "launch_sha": args.launch_sha,
              "admission": admission, "git_head": _git("rev-parse", "HEAD"),
              "arguments": sys.argv[1:] if argv is None else list(argv),
              "interpreter": {"executable": sys.executable, "python": platform.python_version(),
                              "numpy": np.__version__, "torch": torch.__version__,
                              "torch_threads": torch.get_num_threads(), "host": platform.node()}}

    def log(text: str) -> None:
        print(text, flush=True)

    meta = {"admitted": admitted, "out": out, "header": header}
    payload = run_fit(args, meta, log) if args.phase == "fit" else run_evaluate(args, meta, log)
    payload.update({"cpu_seconds": _cpu_seconds(), "start_utc": started_utc, "end_utc": _utc_now(),
                    "wall_clock_s": time.perf_counter() - started})
    write_json(out / ("training.json" if args.phase == "fit" else "summary.json"), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
