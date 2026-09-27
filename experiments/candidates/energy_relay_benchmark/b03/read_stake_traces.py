"""Stage 2-0 trace reader: the clock-aligned split and target diagnostics (declared in NOTES).

Reads ``<out>/stake-sizing/panels/<mode>.json`` and ``traces/<mode>.npz`` written by
``stake_sizing.py`` and computes what the summary does not hold:

- the clock-aligned pre/post split of team QoS/step at a **common** boundary per world — (A) the
  hungarian panel's ``first_entry_step`` of that world (the reference controller's clock, paired,
  exact from the per-step traces) and (B) one common step for all worlds (the rounded mean of the
  hungarian first entries; the Stage 1 convention) — with paired hungarian − free-rule differences
  (mean, SE = s_D/sqrt(n), worlds where hungarian leads) per window and the share of the pooled
  difference mass that lies in the pre window;
- per mode, from ``target_xy`` per step (positions only; the trace holds no slot ids): target
  position changes per UAV per 1,000 steps (any change > 1e-6 m between consecutive finite targets,
  which includes the centroid drift of moving users at every replan), target jumps over
  ``JUMP_M`` = 500 m per UAV per 1,000 steps (a proxy for reassignment across anchors: swaps between
  anchors closer than 500 m are not counted and a large centroid move would be), the number of
  distinct finite targets and the share of UAVs sharing a target (sampled every 10 steps), and the
  share of finite targets;
- the free-rule worlds with QoS/step below .1 (service collapse) with their panel fields.

Zero fit, read-only; the summary's own-clock phase means are not recomputed here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

MODES = ("hungarian", "identity", "independent_nearest")
FREE_RULES = ("identity", "independent_nearest")
SAMPLE_EVERY = 10
JUMP_M = 500.0
COLLAPSE_QOS = 0.1


def _paired(a: np.ndarray, b: np.ndarray) -> dict:
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    n = int(d.size)
    se = float(d.std(ddof=1) / np.sqrt(n)) if n > 1 else None
    return {"paired_mean": float(d.mean()), "paired_se": se, "n_worlds": n,
            "worlds_hungarian_leads": int((d > 0).sum())}


def _window_means(q: np.ndarray, boundaries: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-world means of q[k] before (t < b_k) and from (t >= b_k) the boundary; NaN if empty."""
    pre, post = [], []
    for k, b in enumerate(boundaries):
        b = int(b)
        pre.append(q[k, :b].mean() if b > 0 else np.nan)
        post.append(q[k, b:].mean() if b < q.shape[1] else np.nan)
    return np.asarray(pre), np.asarray(post)


def _split_block(q: dict[str, np.ndarray], boundaries: np.ndarray, definition: str) -> dict:
    means = {m: _window_means(q[m], boundaries) for m in MODES}
    block = {"definition": definition, "boundaries": [int(b) for b in boundaries],
             "per_mode_per_step_mean": {}, "differences": {}}
    for m in MODES:
        block["per_mode_per_step_mean"][m] = {"pre": float(np.nanmean(means[m][0])),
                                              "post": float(np.nanmean(means[m][1]))}
    for free in FREE_RULES:
        block["differences"][f"hungarian_minus_{free}_pre"] = _paired(means["hungarian"][0], means[free][0])
        block["differences"][f"hungarian_minus_{free}_post"] = _paired(means["hungarian"][1], means[free][1])
        diff = q["hungarian"] - q[free]
        pre_mass = float(sum(diff[k, :int(b)].sum() for k, b in enumerate(boundaries)))
        total = float(diff.sum())
        block["differences"][f"pre_window_mass_share_{free}"] = {
            "pre_mass": pre_mass, "total_mass": total,
            "share": (pre_mass / total) if total != 0.0 else None}
    return block


def _target_diagnostics(targets: np.ndarray) -> dict:
    """targets: (T, n_uav, 2) with NaN where a UAV has no target."""
    steps, n_uav = targets.shape[0], targets.shape[1]
    finite = np.isfinite(targets).all(axis=2)
    consecutive = finite[1:] & finite[:-1]
    displacement = np.linalg.norm(np.diff(targets, axis=0), axis=2)
    changed = (displacement > 1e-6) & consecutive
    jumped = (displacement > JUMP_M) & consecutive
    distinct, dup_uavs, sampled = [], 0, 0
    for t in range(0, steps, SAMPLE_EVERY):
        pts = targets[t][finite[t]]
        if pts.shape[0] == 0:
            distinct.append(0)
            continue
        _, counts = np.unique(np.round(pts, 3), axis=0, return_counts=True)
        distinct.append(int(counts.size))
        dup_uavs += int(counts[counts > 1].sum())
        sampled += 1
    per_1000 = n_uav * (steps / 1000.0)
    return {"target_position_changes_per_uav_per_1000_steps": float(changed.sum() / per_1000),
            "target_jumps_over_500m_per_uav_per_1000_steps": float(jumped.sum() / per_1000),
            "mean_distinct_targets_sampled": float(np.mean(distinct)) if distinct else None,
            "duplicate_uav_share_sampled": (dup_uavs / (n_uav * sampled)) if sampled else None,
            "finite_target_share": float(finite.mean())}


def read_stake_traces(out_dir: str | Path) -> dict:
    out = Path(out_dir)
    panels = {m: json.loads((out / "panels" / f"{m}.json").read_text(encoding="utf-8")) for m in MODES}
    rows = {m: {int(r["seed"]): r for r in panels[m]["rows"]} for m in MODES}
    worlds = sorted(rows["hungarian"])
    for m in MODES:
        if sorted(rows[m]) != worlds:
            raise ValueError(f"{m}: worlds differ from hungarian")
    q: dict[str, np.ndarray] = {}
    targets: dict[str, list[np.ndarray]] = {}
    problems: list[str] = []
    for m in MODES:
        with np.load(out / "traces" / f"{m}.npz") as tr:
            series, tg = [], []
            for k, w in enumerate(worlds):
                if int(tr[f"world_{k}_seed"]) != w:
                    raise ValueError(f"{m}: trace world {k} is not seed {w}")
                s = tr[f"world_{k}_qos"].astype(np.float64)
                if abs(float(s.mean()) - float(rows[m][w]["qos_per_step"])) > 1e-6:
                    problems.append(f"{m}:{w}: trace mean {s.mean():.8f} != panel {rows[m][w]['qos_per_step']:.8f}")
                series.append(s)
                tg.append(np.asarray(tr[f"world_{k}_target_xy"], dtype=np.float64))
        q[m] = np.stack(series)
        targets[m] = tg
    entries = np.asarray([rows["hungarian"][w]["first_entry_step"] for w in worlds], dtype=float)
    if np.isnan(entries).any():
        raise ValueError("hungarian first_entry_step missing in some world")
    common = int(round(float(entries.mean())))
    report = {
        "worlds": worlds,
        "steps": int(q["hungarian"].shape[1]),
        "trace_panel_consistency": {"tolerance": 1e-6, "problems": problems},
        "first_entry_step_mean": {m: float(np.mean([rows[m][w]["first_entry_step"] for w in worlds])) for m in MODES},
        "first_input_step_mean": {m: float(np.mean([rows[m][w]["first_input_step"] for w in worlds])) for m in MODES},
        "A_hungarian_world_clock": _split_block(q, entries, "boundary_w = hungarian first_entry_step of world w"),
        "B_common_step": _split_block(q, np.full(len(worlds), common),
                                      f"boundary = {common} for all worlds (rounded mean hungarian first entry)"),
        "trace_diagnostics": {},
        "collapse_worlds": {},
    }
    for m in MODES:
        per_world = []
        for k, w in enumerate(worlds):
            d = _target_diagnostics(targets[m][k])
            d.update({"seed": w, "qos_per_step": float(q[m][k].mean())})
            per_world.append(d)
        report["trace_diagnostics"][m] = {
            "per_world": per_world,
            "mean_target_position_changes_per_uav_per_1000_steps": float(np.mean([x["target_position_changes_per_uav_per_1000_steps"] for x in per_world])),
            "mean_target_jumps_over_500m_per_uav_per_1000_steps": float(np.mean([x["target_jumps_over_500m_per_uav_per_1000_steps"] for x in per_world])),
            "mean_distinct_targets_sampled": float(np.mean([x["mean_distinct_targets_sampled"] for x in per_world])),
            "mean_duplicate_uav_share_sampled": float(np.mean([x["duplicate_uav_share_sampled"] for x in per_world if x["duplicate_uav_share_sampled"] is not None])),
            "mean_finite_target_share": float(np.mean([x["finite_target_share"] for x in per_world])),
        }
    for free in FREE_RULES:
        report["collapse_worlds"][free] = [
            {"seed": w, "qos_per_step": rows[free][w]["qos_per_step"], "zero_service": rows[free][w]["zero_service"],
             "first_service_step": rows[free][w]["first_service_step"]}
            for w in worlds if rows[free][w]["qos_per_step"] < COLLAPSE_QOS]
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="the run's stake-sizing directory")
    parser.add_argument("--json", required=True, help="where to write the readings JSON")
    args = parser.parse_args(argv)
    report = read_stake_traces(args.out)
    Path(args.json).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for name in ("A_hungarian_world_clock", "B_common_step"):
        block = report[name]
        print(f"== {name}: {block['definition']}")
        for m in MODES:
            pm = block["per_mode_per_step_mean"][m]
            print(f"  {m:20s} pre {pm['pre']:.4f} post {pm['post']:.4f}")
        for key, val in block["differences"].items():
            print(f"  {key}: {json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in val.items()})}")
    for m in MODES:
        d = report["trace_diagnostics"][m]
        print(f"== {m}: position changes/uav/1000 {d['mean_target_position_changes_per_uav_per_1000_steps']:.2f}, "
              f"jumps>500m/uav/1000 {d['mean_target_jumps_over_500m_per_uav_per_1000_steps']:.2f}, distinct "
              f"{d['mean_distinct_targets_sampled']:.2f}, duplicate share {d['mean_duplicate_uav_share_sampled']:.3f}, "
              f"finite {d['mean_finite_target_share']:.3f}")
    print("collapse worlds:", json.dumps(report["collapse_worlds"]))
    print("trace/panel problems:", report["trace_panel_consistency"]["problems"] or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
