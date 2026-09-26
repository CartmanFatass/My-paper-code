"""Stage 0 trace readings declared beside S0-2/S0-3 (energy_relay_benchmark): common early window,
arrival at the fixed or planned targets, normal-mode altitude, F-mode share, charging state and
the shield entries of H_park2's parked UAVs, from the trace files of `b02_s0_refs_a01` and the
B01 grid panels H1 / N of `b01_ref_a02`. Merges a ``traces`` block into the readings JSON.

Usage: python stage0_trace_checks.py <b01_run_dir> <stage0_refs_run_dir> <readings_json>
Requires numpy (traces are .npz). Nothing here is a verdict input; S0-2/S0-3 are read by read_stage0.py.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

import numpy as np

ARRIVAL_M = 50.0


def load(run_dir, phase, name):
    z = np.load(os.path.join(run_dir, phase, "traces", f"{name}.npz"), allow_pickle=True)
    n = max(int(k.split("_")[1]) for k in z.files if k.endswith("_seed")) + 1
    worlds = [{k[len(f"world_{i}_"):]: z[k] for k in z.files if k.startswith(f"world_{i}_")} for i in range(n)]
    return {int(w["seed"]): w for w in worlds}


def rows(run_dir, phase, name):
    return {w["seed"]: w for w in json.load(open(os.path.join(run_dir, phase, "panels", f"{name}.json")))["worlds"]}


def first_entry(w):
    e = np.flatnonzero((w["mode"] > 0.5).any(1))
    return int(e[0]) if e.size else int(w["mode"].shape[0])


def entries_of(mode_col):
    m = mode_col > 0.5
    return int((m[1:] & ~m[:-1]).sum() + int(m[0]))


def paired(a, b):
    d = [y - x for x, y in zip(a, b)]
    return {"n": len(d), "mean": st.mean(d), "paired_se": st.stdev(d) / len(d) ** 0.5 if len(d) > 1 else None,
            "positive": sum(x > 0 for x in d), "min": min(d), "max": max(d)}


def main():
    b01, s0, out_path = sys.argv[1:4]
    T = {"Hspawn": load(s0, "stage0-references", "Hspawn_e0.00_x0.05"),
         "Hpark2": load(s0, "stage0-references", "Hpark2_e0.00_x0.05"),
         "H1r10": load(s0, "stage0-references", "H1r10_e0.00_x0.05"),
         "H1": load(b01, "grid", "H1_e0.00_x0.05"), "N": load(b01, "grid", "N_e0.00_x0.05")}
    R = {"Hspawn": rows(s0, "stage0-references", "Hspawn_e0.00_x0.05"),
         "Hpark2": rows(s0, "stage0-references", "Hpark2_e0.00_x0.05"),
         "H1r10": rows(s0, "stage0-references", "H1r10_e0.00_x0.05"),
         "H1": rows(b01, "grid", "H1_e0.00_x0.05"), "N": rows(b01, "grid", "N_e0.00_x0.05")}
    seeds = sorted(T["Hspawn"])
    traces = {"definition": {"common_early_window": "steps before the earlier first shield entry of the two compared "
                                                     "arms in that world; team QoS/step averaged over it",
                             "arrival": f"first step with horizontal distance to the UAV's target < {ARRIVAL_M:.0f} m",
                             "altitude": "mean z over normal-mode UAV-steps", "entries": "rising edges of the F-mode flag"}}
    cw = {}
    for a, b in (("Hspawn", "Hpark2"), ("H1", "H1r10"), ("Hspawn", "N"), ("Hpark2", "N")):
        qa, qb, L = [], [], []
        for s in seeds:
            end = min(first_entry(T[a][s]), first_entry(T[b][s]))
            if end > 0:
                qa.append(float(T[a][s]["qos"][:end].mean())); qb.append(float(T[b][s]["qos"][:end].mean())); L.append(end)
        cw[f"{a}_vs_{b}"] = {"median_length": st.median(L), "min_length": min(L), a: st.mean(qa), b: st.mean(qb),
                             "paired_b_minus_a": paired(qa, qb)}
    traces["common_early_window"] = cw
    per = {}
    for n in T:
        alt, arr, parked, ent = [], [], [], []
        for s in seeds:
            w = T[n][s]; normal = w["mode"] < 0.5
            alt.append(float(w["own_xyz"][..., 2][normal].mean()))
            ent.append(sum(entries_of(w["mode"][:, u]) for u in range(w["mode"].shape[1])))
            if "target_xy" in w:
                d = np.linalg.norm(w["own_xyz"][..., :2] - w["target_xy"], axis=-1)
                for u in range(d.shape[1]):
                    hit = np.flatnonzero(d[:, u] < ARRIVAL_M); arr.append(int(hit[0]) if hit.size else None)
                if n == "Hpark2":
                    for u, station in R[n][s]["park_assignment"]:
                        hit = np.flatnonzero(d[:, u] < ARRIVAL_M)
                        parked.append({"seed": s, "uav": int(u), "station": int(station),
                                       "initial_distance_m": float(d[0, u]),
                                       "arrival_step": int(hit[0]) if hit.size else None,
                                       "shield_entries": entries_of(w["mode"][:, u])})
        block = {"mean_normal_mode_altitude_m": st.mean(alt), "shield_entries_per_world_from_traces": st.mean(ent),
                 "F_mode_share_rows": st.mean(R[n][s]["mode_uav_step_fraction"] for s in seeds),
                 "charging_uav_steps_rows": st.mean(R[n][s]["charging_uav_steps"] for s in seeds),
                 "wait_ticks_rows": st.mean(R[n][s]["wait_ticks_total"] for s in seeds)}
        if arr:
            known = [x for x in arr if x is not None]
            block["arrival_step_median"] = st.median(known) if known else None
            block["never_arrived"] = sum(x is None for x in arr); block["uav_targets"] = len(arr)
        if parked:
            block["parked_uavs"] = {"count": len(parked),
                                    "arrival_step_median": st.median(p["arrival_step"] for p in parked if p["arrival_step"] is not None),
                                    "initial_distance_m_median": st.median(p["initial_distance_m"] for p in parked),
                                    "never_arrived": sum(p["arrival_step"] is None for p in parked),
                                    "shield_entries_mean": st.mean(p["shield_entries"] for p in parked),
                                    "shield_entries_max": max(p["shield_entries"] for p in parked),
                                    "detail": parked}
        per[n] = block
    traces["per_controller"] = per
    traces["Hspawn_zero_service_seeds"] = [s for s in seeds if R["Hspawn"][s]["zero_service"]]
    readings = json.load(open(out_path))
    readings["traces"] = traces
    json.dump(readings, open(out_path, "w"), indent=1)
    for k, v in cw.items():
        print(f"{k}: {v['paired_b_minus_a']['mean']:+.4f} (SE {v['paired_b_minus_a']['paired_se']:.4f}, positive {v['paired_b_minus_a']['positive']}/{v['paired_b_minus_a']['n']}), median window {v['median_length']:.0f}")
    for n, b in per.items():
        print(n, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in b.items() if k != "parked_uavs"})
    if "parked_uavs" in per["Hpark2"]:
        p = per["Hpark2"]["parked_uavs"]; print("parked UAVs:", {k: v for k, v in p.items() if k != "detail"})
    print("written", out_path)


if __name__ == "__main__":
    main()
