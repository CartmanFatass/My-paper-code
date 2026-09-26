"""B01 trace checks (energy_relay_benchmark): post-hoc descriptive readings from the per-step
trace archives, added under "traces" in the readings JSON written by read_b01.py.

Usage: <scientific interpreter> trace_checks.py <run_dir> <readings_json>

Checks: (1) the tether as an increment (nearest-station distance at a UAV's next shield entry
minus the distance at its exit), (2) the common-window pre-entry reading of P3, (3) team QoS
by the number of UAVs within a distance of a station (distance only; the submitted dock bit is
a request, not a position), (4) team QoS by which station is occupied, (5) N's zero-service
worlds, (6) queue and waiting readings by width. Needs numpy.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

STATION_LABELS = {0: "relay anchor (.7 BS + .3 service centre)", 1: "service centre (user centroid, jittered)"}


def load(run_dir, phase, name):
    z = np.load(os.path.join(run_dir, phase, "traces", f"{name}.npz"), allow_pickle=True)
    n = max(int(k.split("_")[1]) for k in z.files if k.endswith("_seed")) + 1
    return [{k[len(f"world_{i}_"):]: z[k] for k in z.files if k.startswith(f"world_{i}_")}
            for i in range(n)]


def events(mode):
    m = mode > 0.5
    prev = np.vstack([np.zeros((1, m.shape[1]), bool), m[:-1]])
    return (m & ~prev), (~m & prev)


def med(a):
    return float(np.median(a)) if len(a) else None


def tether(run_dir, phase, name):
    d_exit, d_entry, gap = [], [], []
    n_exits = 0
    for w in load(run_dir, phase, name):
        entered, exited = events(w["mode"])
        dist = w["nearest_station_distance_m"]
        for t, u in zip(*np.nonzero(exited)):
            n_exits += 1
            later = np.flatnonzero(entered[t + 1:, u])
            if later.size:
                t2 = t + 1 + later[0]
                d_exit.append(dist[t, u]); d_entry.append(dist[t2, u]); gap.append(t2 - t)
    inc = np.array(d_entry) - np.array(d_exit) if d_exit else np.array([])
    return {"exits": n_exits, "re_entered": len(d_exit),
            "d_exit_median_m": med(d_exit), "d_entry_median_m": med(d_entry),
            "increment_median_m": med(inc),
            "increment_p25_m": float(np.percentile(inc, 25)) if len(inc) else None,
            "increment_p75_m": float(np.percentile(inc, 75)) if len(inc) else None,
            "gap_median_steps": med(gap)}


def bins(q, count, mask=None):
    rows = {}
    for label, lo, hi in (("0", 0, 0), ("1", 1, 1), ("2", 2, 2), ("3", 3, 3), ("4+", 4, 99)):
        m = (count >= lo) & (count <= hi)
        if mask is not None:
            m &= mask
        rows[label] = {"qos": float(q[m].mean()) if m.any() else None, "steps": int(m.sum())}
    return rows


def proximity(run_dir, phase, name):
    W = load(run_dir, phase, name)
    q = np.concatenate([w["qos"] for w in W])
    t = np.concatenate([np.arange(len(w["qos"])) for w in W])
    d = np.concatenate([w["nearest_station_distance_m"] for w in W])
    ch = np.concatenate([w["charging"] for w in W]) > 0.5
    fm = np.concatenate([w["mode"] for w in W]) > 0.5
    return {"within_300m": bins(q, (d < 300).sum(1)),
            "within_300m_steps_ge_1500": bins(q, (d < 300).sum(1), t >= 1500),
            "within_100m": bins(q, (d < 100).sum(1)),
            "charging_count": bins(q, ch.sum(1)),
            "F_mode_count_any_distance": bins(q, fm.sum(1)),
            "F_mode_uav_step_share": float(fm.mean()),
            "F_mode_share_beyond_1000m": float((d[fm] > 1000).mean()) if fm.any() else None,
            "F_mode_share_within_100m": float((d[fm] < 100).mean()) if fm.any() else None}


def occupancy(run_dir, phase, name):
    W = load(run_dir, phase, name)
    q = np.concatenate([w["qos"] for w in W])
    occ = np.concatenate([w["station_occupancy"] for w in W])
    s0, s1 = occ[:, 0] > 0, occ[:, 1] > 0
    cell = lambda m: {"qos": float(q[m].mean()) if m.any() else None, "steps": int(m.sum())}
    return {"none": cell(~s0 & ~s1), "only_station_0": cell(s0 & ~s1),
            "only_station_1": cell(~s0 & s1), "both": cell(s0 & s1), "labels": STATION_LABELS}


def zero_service(run_dir):
    rows = []
    for w in load(run_dir, "grid", "N_e0.00_x0.05"):
        if w["qos"].sum() < 1e-9:
            d = w["nearest_station_distance_m"]; ch = w["charging"] > 0.5
            rows.append({"seed": int(w["seed"]), "min_nearest_station_m": float(d.min()),
                         "uav_steps_within_100m": int((d < 100).sum()),
                         "charging_uav_steps": int(ch.sum()),
                         "first_charging_step": int(np.argmax(ch.any(1))) if ch.any() else None,
                         "mean_nearest_station_m": float(d.mean()),
                         "F_mode_share": float((w["mode"] > 0.5).mean())})
    return rows


def queues(run_dir, phase, name):
    W = load(run_dir, phase, name)
    qsum = np.concatenate([w["station_queue"].sum(1) for w in W])
    occ = np.concatenate([w["station_occupancy"].sum(1) for w in W])
    wait = np.concatenate([w["waiting_steps"] for w in W]).ravel()
    bat = np.concatenate([w["battery"] for w in W]).ravel()
    return {"queue_mean": float(qsum.mean()), "p_queue_ge_1": float((qsum >= 1).mean()),
            "p_queue_ge_3": float((qsum >= 3).mean()), "queue_max": int(qsum.max()),
            "occupancy_mean": float(occ.mean()), "waiting_steps_mean": float(wait.mean()),
            "battery_mean": float(bat.mean())}


def common_window(run_dir, readings):
    N = load(run_dir, "grid", "N_e0.00_x0.05"); H = load(run_dir, "grid", "H1_e0.00_x0.05")
    pn = readings["per_world"]["grid/N_e0.00_x0.05"]; ph = readings["per_world"]["grid/H1_e0.00_x0.05"]
    rows = []
    for wn, wh in zip(N, H):
        s = int(wn["seed"]); assert s == int(wh["seed"])
        win = int(min(pn["first_entry"][pn["seeds"].index(s)], ph["first_entry"][ph["seeds"].index(s)]))
        rows.append({"seed": s, "window": win, "N": float(wn["qos"][:win].mean()),
                     "H1": float(wh["qos"][:win].mean())})
    qn = np.array([r["N"] for r in rows]); qh = np.array([r["H1"] for r in rows])
    return {"window_median": float(np.median([r["window"] for r in rows])),
            "N_mean": float(qn.mean()), "N_below_0.30": int((qn < 0.30).sum()),
            "N_zero": int((qn < 1e-9).sum()), "H1_mean": float(qh.mean()),
            "H1_ge_0.60": int((qh >= 0.60).sum()), "paired_H1_minus_N_mean": float((qh - qn).mean()),
            "paired_H1_minus_N_min": float((qh - qn).min()), "worlds": rows}


def main(run_dir, readings_json):
    readings = json.load(open(readings_json))
    T = {}
    T["tether_increment"] = {f"{ph}/{n}": tether(run_dir, ph, n) for ph, n in (
        ("grid", "N_e0.00_x0.05"), ("grid", "H1_e0.00_x0.05"), ("grid", "N_e0.00_x0.25"),
        ("grid", "H1_e0.00_x0.25"), ("grid", "N_e0.20_x0.25"), ("grid", "H1_e0.20_x0.25"))}
    T["P3_common_window"] = common_window(run_dir, readings)
    T["proximity"] = {f"{ph}/{n}": proximity(run_dir, ph, n) for ph, n in (
        ("grid", "N_e0.00_x0.05"), ("grid", "N_e0.00_x0.45"), ("grid", "N_e0.20_x0.45"),
        ("grid", "H1_e0.00_x0.05"), ("grid", "H1_e0.20_x0.25"), ("reference", "Hlocal_e0.00_x0.05"))}
    T["occupancy"] = {f"{ph}/{n}": occupancy(run_dir, ph, n) for ph, n in (
        ("grid", "N_e0.00_x0.05"), ("grid", "N_e0.20_x0.45"), ("grid", "H1_e0.00_x0.05"))}
    T["N_zero_service_worlds"] = zero_service(run_dir)
    T["queues"] = {f"{ph}/{n}": queues(run_dir, ph, n) for ph, n in (
        ("grid", "N_e0.00_x0.05"), ("grid", "N_e0.00_x0.25"), ("grid", "N_e0.00_x0.45"),
        ("grid", "N_e0.00_x0.85"), ("grid", "N_e0.20_x0.45"), ("grid", "H1_e0.00_x0.05"),
        ("grid", "H1_e0.00_x0.85"))}
    readings["traces"] = T
    json.dump(readings, open(readings_json, "w"), indent=1)
    for k, v in T["tether_increment"].items():
        print("tether", k, {kk: (round(vv, 1) if isinstance(vv, float) else vv) for kk, vv in v.items()})
    cw = T["P3_common_window"]
    print("common window", {k: v for k, v in cw.items() if k != "worlds"})
    for k, v in T["proximity"].items():
        print("proximity", k, "<300m:", [round(c["qos"], 3) if c["qos"] is not None else None for c in v["within_300m"].values()],
              "late:", [round(c["qos"], 3) if c["qos"] is not None else None for c in v["within_300m_steps_ge_1500"].values()])
    for k, v in T["occupancy"].items():
        print("occupancy", k, {kk: round(vv["qos"], 3) for kk, vv in v.items() if kk != "labels" and vv["qos"] is not None})
    print("zero-service", T["N_zero_service_worlds"])
    for k, v in T["queues"].items():
        print("queues", k, {kk: round(vv, 3) for kk, vv in v.items()})
    print("written", readings_json)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
