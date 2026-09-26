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


def within_slope(q, x, groups):
    """Fixed-effects slope of q on x within groups (demeaned per group)."""
    num = den = 0.0
    for g in np.unique(groups):
        m = groups == g
        xm = x[m] - x[m].mean()
        num += float((xm * (q[m] - q[m].mean())).sum()); den += float((xm * xm).sum())
    return num / den if den > 0 else None


def boundary_and_time(run_dir, readings, area_m=8000.0):
    """Post-hoc checks added after the internal review: boundary parking, altitude floor, the
    time confound of the proximity association, matched-time intervention, zero-service worlds
    by station, and the level effect without the zero-service worlds."""
    out = {}
    for ph, nm in (("grid", "N_e0.00_x0.05"), ("grid", "N_e0.20_x0.45"), ("grid", "H1_e0.00_x0.05"),
                   ("reference", "Hlocal_e0.00_x0.05")):
        W = load(run_dir, ph, nm); tot = bnd = etot = ebnd = atot = afl = xs = ys = 0; per = []
        for w in W:
            xyz = w["own_xyz"]; normal = w["mode"] < 0.5
            onb = ((np.abs(xyz[:, :, 0]) < 1) | (np.abs(xyz[:, :, 0] - area_m) < 1)
                   | (np.abs(xyz[:, :, 1]) < 1) | (np.abs(xyz[:, :, 1] - area_m) < 1))
            early = np.zeros_like(normal); early[:1000] = True
            e600 = np.zeros_like(normal); e600[:600] = True
            tot += normal.sum(); bnd += (onb & normal).sum()
            etot += (normal & early).sum(); ebnd += (onb & normal & early).sum()
            per.append(float((onb & normal & early).sum() / max((normal & early).sum(), 1)))
            xs += int(((np.abs(xyz[:, :, 0] - area_m) < 1) & normal).sum())
            ys += int(((np.abs(xyz[:, :, 1]) < 1) & normal).sum())
            atot += (normal & e600).sum(); afl += ((xyz[:, :, 2] <= 50.5) & normal & e600).sum()
        out[f"{ph}/{nm}"] = {"boundary_share_normal_mode": float(bnd / tot),
                             "boundary_share_before_1000": float(ebnd / etot),
                             "worlds_above_50pct_before_1000": int(sum(p > .5 for p in per)),
                             "x_east_wall_uav_steps": xs, "y_south_wall_uav_steps": ys,
                             "altitude_floor_share_before_600": float(afl / atot)}
    W = load(run_dir, "grid", "N_e0.00_x0.05")
    q = np.stack([w["qos"] for w in W]); fm = np.stack([w["mode"] > 0.5 for w in W])
    out["N_e0.00_x0.05_time_bins_300"] = [{"start": b, "qos": float(q[:, b:b + 300].mean()),
                                            "F_mode_share": float(fm[:, b:b + 300].mean())}
                                           for b in range(0, 3000, 300)]
    out["matched_time_900_1200"] = {nm: float(np.stack([w["qos"] for w in load(run_dir, "grid", nm)])[:, 900:1200].mean())
                                    for nm in ("N_e0.00_x0.05", "N_e0.00_x0.45", "N_e0.20_x0.25", "N_e0.20_x0.45")}
    qq = np.concatenate([w["qos"] for w in W])
    near = np.concatenate([(w["nearest_station_distance_m"] < 300).any(1) for w in W]).astype(float)
    t = np.concatenate([np.arange(3000)] * len(W)); wid = np.concatenate([[i] * 3000 for i in range(len(W))])
    out["proximity_slope_N_e0.00_x0.05"] = {
        "raw": float(np.polyfit(near, qq, 1)[0]), "within_world": within_slope(qq, near, wid),
        "within_300_step_bin": within_slope(qq, near, t // 300),
        "within_world_x_300_step_bin": within_slope(qq, near, wid * 100 + t // 300),
        "within_world_x_100_step_bin": within_slope(qq, near, wid * 100 + t // 100)}
    a0 = np.concatenate([((w["nearest_station_distance_m"] < 300) & (w["nearest_station"] == 0)).any(1) for w in W])
    a1 = np.concatenate([((w["nearest_station_distance_m"] < 300) & (w["nearest_station"] == 1)).any(1) for w in W])
    out["distance_only_station_cells_N_e0.00_x0.05"] = {
        "none": float(qq[~a0 & ~a1].mean()), "anchor_only": float(qq[a0 & ~a1].mean()),
        "centre_only": float(qq[~a0 & a1].mean()), "both": float(qq[a0 & a1].mean())}
    zs = []
    for w in W:
        if w["qos"].sum() < 1e-9:
            d = w["nearest_station_distance_m"][2000:]; s = w["nearest_station"][2000:]
            zs.append({"seed": int(w["seed"]), "anchor_uav_steps_after_2000": int(((d < 300) & (s == 0)).sum()),
                       "centre_uav_steps_after_2000": int(((d < 300) & (s == 1)).sum()),
                       "mean_x_at_500": float(w["own_xyz"][500, :, 0].mean()),
                       "guard_checked_total": int(w["guard_checked"].sum())})
    out["zero_service_worlds_by_station"] = zs
    pw = readings["per_world"]; z = {r["seed"] for r in zs}; lev = []
    for lo, hi in (("grid/N_e0.00_x0.05", "grid/N_e0.20_x0.25"), ("grid/N_e0.00_x0.25", "grid/N_e0.20_x0.45"),
                   ("grid/N_e0.00_x0.45", "grid/N_e0.20_x0.65")):
        a, b = pw[lo], pw[hi]
        dd = [qb - qa for s, qa, qb in zip(a["seeds"], a["qos"], b["qos"])]
        dx = [qb - qa for s, qa, qb in zip(a["seeds"], a["qos"], b["qos"]) if s not in z]
        lev.append({"pair": f"{hi} - {lo}", "mean": float(np.mean(dd)),
                    "paired_se": float(np.std(dd, ddof=1) / np.sqrt(len(dd))),
                    "mean_excluding_zero_service_worlds": float(np.mean(dx))})
    out["level_effect_matched_width"] = lev
    return out


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
    T["boundary_and_time"] = boundary_and_time(run_dir, readings)
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
    print("boundary_and_time", json.dumps(T["boundary_and_time"], indent=None)[:1200])
    print("written", readings_json)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
