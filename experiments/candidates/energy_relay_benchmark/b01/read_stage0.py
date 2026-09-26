"""Stage 0 reading (energy_relay_benchmark, revised B02): the sampled-action N check (S0-1) and
the three fixed references (S0-2, S0-3), each against the B01 `b01_ref_a02` panels.

Usage: python read_stage0.py --b01 <b01_run_dir> --stage0 <run_dir> [<run_dir> ...] --out <json>

Rules are those declared in NOTES.md ("DM response to both reviews ... Stage 0 declared"):
S0-1: sampled-action panel mean within .03 QoS/step of the deterministic N and boundary share
above .30 -> the deficit belongs to the learned policy; sampled mean >= deterministic + .05 or
boundary share below .15 -> the deterministic evaluation misrepresents the learned behaviour;
otherwise both are reported. "Panel mean" is read as the mean over all sampled-action episodes
(both draws pooled, equal sizes); each draw's own verdict is printed beside it so a split between
draws is visible, and the draw-to-draw spread is reported, not tested. S0-2: H_park2 - H_spawn is a package effect (expected >= +.10, a
level, not a pass mark). S0-3: |H_central@10 - H_central| < .03 reads "period sensitivity below
the practical threshold for this H". Standard library only.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st

Q = "qos_satisfaction_ratio_per_step"
J = "raw_native_J"
COLS = [Q, J, "return_constraint_cost_sum", "cutoff_event_count_sum", "depletion_event_count_sum",
        "min_decoded_battery", "mode_uav_step_fraction", "first_entry_step", "first_input_step",
        "qos_per_step_pre_entry", "charger_input_wh", "wait_ticks_total", "guard_blocked_actions",
        "boundary_share_normal_mode", "altitude_floor_share_normal_mode",
        "anchor_uav_steps_within_300m", "centre_uav_steps_within_300m", "first_service_step",
        "zero_service"]


def b01_trace_diagnostics(run_dir, phase, name, area_m=8000.0, floor_m=50.0):
    """Recompute the five position diagnostics (added to rows at 8d88f72d0) for a B01 panel from its
    trace file, with the definitions of evaluation.position_diagnostics (boundary |x|,|y|,|x-area|,
    |y-area| < 1 m in normal mode; altitude z <= floor + .5 m; nearest station < 300 m by index;
    first step with team QoS > 0). Returns {} when numpy or the trace file is unavailable."""
    path = os.path.join(run_dir, phase, "traces", f"{name}.npz")
    try:
        import numpy as np
    except ImportError:
        return {}
    if not os.path.exists(path):
        return {}
    z = np.load(path, allow_pickle=True)
    n = max(int(k.split("_")[1]) for k in z.files if k.endswith("_seed")) + 1
    out = {}
    for i in range(n):
        w = {k[len(f"world_{i}_"):]: z[k] for k in z.files if k.startswith(f"world_{i}_")}
        xyz = w["own_xyz"].astype(np.float64)
        normal = w["mode"] < 0.5
        x, y, zc = xyz[..., 0], xyz[..., 1], xyz[..., 2]
        boundary = (np.abs(x) < 1.0) | (np.abs(x - area_m) < 1.0) | (np.abs(y) < 1.0) | (np.abs(y - area_m) < 1.0)
        floor = zc <= floor_m + 0.5
        nc = int(normal.sum())
        near = w["nearest_station_distance_m"].astype(np.float64) < 300.0
        st_idx = w["nearest_station"]
        served = np.flatnonzero(w["qos"] > 0.0)
        out[int(w["seed"])] = {
            "boundary_share_normal_mode": float((boundary & normal).sum() / nc) if nc else None,
            "altitude_floor_share_normal_mode": float((floor & normal).sum() / nc) if nc else None,
            "anchor_uav_steps_within_300m": int((near & (st_idx == 0)).sum()),
            "centre_uav_steps_within_300m": int((near & (st_idx == 1)).sum()),
            "first_service_step": int(served[0]) if served.size else None}
    return out


def load_panels(run_dir):
    out = {}
    for path in sorted(glob.glob(os.path.join(run_dir, "*", "panels", "*.json"))):
        d = json.load(open(path))
        out[(path.split(os.sep)[-3], d["name"])] = {w["seed"]: w for w in d["worlds"]}
    return out


def mean(rows, key):
    vals = [float(bool(r[key])) if isinstance(r.get(key), bool) else r.get(key) for r in rows]
    vals = [float(v) for v in vals if v is not None]
    return st.mean(vals) if vals else None


def summarise(rows):
    return {k: mean(rows, k) for k in COLS} | {"n": len(rows),
                                               "zero_service_worlds": sum(1 for r in rows if r.get("zero_service"))}


def paired(a, b, key):
    """b - a per world (aligned by seed), mean and paired SE."""
    seeds = [s for s in a if s in b and a[s].get(key) is not None and b[s].get(key) is not None]
    d = [float(b[s][key]) - float(a[s][key]) for s in seeds]
    if not d:
        return None
    se = st.stdev(d) / len(d) ** 0.5 if len(d) > 1 else None
    return {"n": len(d), "mean": st.mean(d), "paired_se": se, "min": min(d), "max": max(d)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b01", required=True)
    ap.add_argument("--stage0", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    b01 = load_panels(args.b01)
    det = b01[("grid", "N_e0.00_x0.05")]
    h1 = b01[("grid", "H1_e0.00_x0.05")]
    hl = b01[("reference", "Hlocal_e0.00_x0.05")]
    recomputed = {}
    for (ph, name), rows in ((("grid", "N_e0.00_x0.05"), det), (("grid", "H1_e0.00_x0.05"), h1),
                             (("reference", "Hlocal_e0.00_x0.05"), hl)):
        diag = b01_trace_diagnostics(args.b01, ph, name)
        recomputed[name] = bool(diag)
        for seed, extra in diag.items():
            if seed in rows:
                rows[seed].update({k: v for k, v in extra.items() if k not in rows[seed]})
    s0 = {}
    for run in args.stage0:
        s0.update(load_panels(run))
    out = {"b01_position_diagnostics_recomputed_from_traces": recomputed,
           "b01_reference_panels": {"N_deterministic": summarise(list(det.values())),
                                    "H_central": summarise(list(h1.values())),
                                    "H_local": summarise(list(hl.values()))}}
    print("B01 deterministic N: QoS %.4f J %.1f boundary %.3f floor %.3f" % (
        out["b01_reference_panels"]["N_deterministic"][Q], out["b01_reference_panels"]["N_deterministic"][J],
        out["b01_reference_panels"]["N_deterministic"]["boundary_share_normal_mode"] or float("nan"),
        out["b01_reference_panels"]["N_deterministic"]["altitude_floor_share_normal_mode"] or float("nan")))

    # S0-1: sampled-action N
    draws = sorted((k, v) for k, v in s0.items() if k[0] == "stochastic-check")
    if draws:
        per_draw = {}
        for (ph, name), rows in draws:
            per_draw[name] = {"summary": summarise(list(rows.values())),
                              "paired_vs_deterministic": {k: paired(det, rows, k) for k in
                                                          (Q, J, "boundary_share_normal_mode",
                                                           "altitude_floor_share_normal_mode",
                                                           "first_service_step")}}
            s = per_draw[name]["summary"]
            print(f"{name}: QoS {s[Q]:.4f} J {s[J]:.1f} boundary {s['boundary_share_normal_mode']:.3f} "
                  f"floor {s['altitude_floor_share_normal_mode']:.3f} zero-service {s['zero_service_worlds']} "
                  f"retcost {s['return_constraint_cost_sum']:.3f} cutoff {s['cutoff_event_count_sum']:.2f} "
                  f"deplet {s['depletion_event_count_sum']:.2f} minBat {s['min_decoded_battery']:.3f}")
        def verdict_of(dq, bshare):
            if abs(dq) < 0.03 and bshare > 0.30:
                return "policy: sampled N within .03 of deterministic N and still on the walls"
            if dq >= 0.05 or bshare < 0.15:
                return "evaluation mode: deterministic evaluation misrepresents the learned behaviour"
            return "between: both reported; evaluation mode becomes a declared axis of Stage 1"
        det_q0 = out["b01_reference_panels"]["N_deterministic"][Q]
        for n_, d_ in per_draw.items():
            d_["own_verdict"] = verdict_of(d_["summary"][Q] - det_q0, d_["summary"]["boundary_share_normal_mode"])
            print(f"  {n_} alone: delta {d_['summary'][Q] - det_q0:+.4f} -> {d_['own_verdict']}")
        names = list(per_draw)
        pooled_q = st.mean(per_draw[n]["summary"][Q] for n in names)
        pooled_b = st.mean(per_draw[n]["summary"]["boundary_share_normal_mode"] for n in names)
        pooled_j = st.mean(per_draw[n]["summary"][J] for n in names)
        det_q = out["b01_reference_panels"]["N_deterministic"][Q]
        delta = pooled_q - det_q
        spread = None
        if len(names) >= 2:
            a, b = s0[("stochastic-check", names[0])], s0[("stochastic-check", names[1])]
            spread = paired(a, b, Q)
        verdict = verdict_of(delta, pooled_b)
        out["S0_1_sampled_N"] = {"per_draw": per_draw, "pooled_qos": pooled_q, "pooled_J": pooled_j,
                                 "pooled_boundary_share": pooled_b, "delta_qos_vs_deterministic": delta,
                                 "delta_J_vs_deterministic": pooled_j - out["b01_reference_panels"]["N_deterministic"][J],
                                 "draw_to_draw_qos": spread, "verdict": verdict}
        print(f"S0-1: pooled sampled QoS {pooled_q:.4f} (delta {delta:+.4f}), boundary {pooled_b:.3f} -> {verdict}")

    # S0-2 / S0-3: fixed references
    refs = {name: rows for (ph, name), rows in s0.items() if ph == "stage0-references"}
    if refs:
        out["references"] = {name: summarise(list(rows.values())) for name, rows in refs.items()}
        for name, s in out["references"].items():
            print(f"{name}: QoS {s[Q]:.4f} J {s[J]:.1f} pre-entry {s['qos_per_step_pre_entry'] if s['qos_per_step_pre_entry'] is None else round(s['qos_per_step_pre_entry'],3)} "
                  f"Fmode {s['mode_uav_step_fraction']:.3f} retcost {s['return_constraint_cost_sum']:.3f} boundary {s['boundary_share_normal_mode']:.3f} "
                  f"anchor {s['anchor_uav_steps_within_300m']:.0f} centre {s['centre_uav_steps_within_300m']:.0f} zero-service {s['zero_service_worlds']}")
        sp = next((n for n in refs if n.startswith("Hspawn")), None)
        pk = next((n for n in refs if n.startswith("Hpark2")), None)
        r10 = next((n for n in refs if n.startswith("H1r10")), None)
        if sp and pk:
            out["S0_2_park2_minus_spawn"] = {k: paired(refs[sp], refs[pk], k) for k in (Q, J, "return_constraint_cost_sum")}
            print(f"S0-2: H_park2 - H_spawn QoS {out['S0_2_park2_minus_spawn'][Q]['mean']:+.4f} (SE {out['S0_2_park2_minus_spawn'][Q]['paired_se']:.4f}) J {out['S0_2_park2_minus_spawn'][J]['mean']:+.1f}")
        if r10:
            out["S0_3_H1r10_minus_H1"] = {k: paired(h1, refs[r10], k) for k in (Q, J, "return_constraint_cost_sum")}
            d = out["S0_3_H1r10_minus_H1"][Q]["mean"]
            print(f"S0-3: H_central@10 - H_central QoS {d:+.4f} (SE {out['S0_3_H1r10_minus_H1'][Q]['paired_se']:.4f}) J {out['S0_3_H1r10_minus_H1'][J]['mean']:+.1f} -> {'below the practical threshold' if abs(d) < 0.03 else 'at or above the practical threshold'}")
    json.dump(out, open(args.out, "w"), indent=1)
    print("written", args.out)


if __name__ == "__main__":
    main()
