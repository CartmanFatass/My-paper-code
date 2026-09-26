"""B01 panel reading (energy_relay_benchmark): panel means, P0–P3 and the width curves.

Usage: python read_b01.py <run_dir> <out_json>

Reads only the runner's JSON outputs (summary.json and <phase>/panels/*.json) and applies the
rules pre-registered in NOTES.md ("B01 revised", 2026-09-26): the .03 QoS/step practical
threshold, P0's τ_w rule, the co-primary rule for J, cutoff and depletion. The per-world
paired counts are printed for the record; whether they may be read is decided by τ_w.
Standard library only.
"""
from __future__ import annotations

import glob
import json
import os
import re
import statistics as st
import sys

Q = "qos_satisfaction_ratio_per_step"
J = "raw_native_J"
THRESHOLD = 0.03
COLUMNS = [
    (Q, "QoS"), (J, "J"), ("return_constraint_cost_sum", "retcost"),
    ("cutoff_event_count_sum", "cutoff"), ("depletion_event_count_sum", "depletion"),
    ("mode_uav_step_fraction", "Fmode"), ("first_entry_step", "first_entry"),
    ("first_input_step", "first_input"), ("qos_per_step_pre_entry", "QoS_pre"),
    ("qos_per_step_entry_to_input", "QoS_e2i"), ("qos_per_step_post_input", "QoS_post"),
    ("steps_pre_entry", "steps_pre"), ("steps_entry_to_input", "steps_e2i"),
    ("one_tick_spell_share", "one_tick"), ("wait_ticks_total", "wait"),
    ("guard_checked_actions", "guard_checked"), ("guard_blocked_actions", "guard_blocked"),
    ("charger_input_wh", "charger_wh"), ("min_decoded_battery", "min_battery"),
    ("feedback_entry_count", "entries"), ("mean_nearest_station_distance_m", "nearest_m"),
    ("post_exit_recapture_count", "recap_n"), ("post_exit_recapture_median_m", "recap_med_m"),
    ("zero_service", "zero_service"), ("input_before_entry", "input_before_entry"),
]
SETTINGS = ["e0.00_x0.05", "e0.00_x0.25", "e0.00_x0.45", "e0.00_x0.85",
            "e0.20_x0.25", "e0.20_x0.45", "e0.20_x0.65"]
MATCHED = [("e0.00_x0.05", "e0.20_x0.25", 0.05), ("e0.00_x0.25", "e0.20_x0.45", 0.25),
           ("e0.00_x0.45", "e0.20_x0.65", 0.45)]


def pct(values, q):
    a = sorted(values)
    k = (len(a) - 1) * q
    f = int(k)
    c = min(f + 1, len(a) - 1)
    return a[f] + (a[c] - a[f]) * (k - f)


def mean(worlds, key):
    vals = [w.get(key) for w in worlds]
    vals = [float(bool(v)) if isinstance(v, bool) else v for v in vals]
    vals = [float(v) for v in vals if v is not None]
    return st.mean(vals) if vals else None


def b09_reference(run_dir):
    """B09's recorded per-world J for the equivalence worlds, from native.py at this checkout."""
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "native.py"), encoding="utf-8").read()
    block = re.search(r"B09_N_PRIMARY_J = \{(.*?)\}", src, re.S).group(1)
    return {int(k): float(v) for k, v in re.findall(r"(\d{6}):\s*([0-9.]+)", block)}


def main(run_dir, out_json):
    summary = json.load(open(os.path.join(run_dir, "summary.json")))
    panels = {}
    for path in sorted(glob.glob(os.path.join(run_dir, "*", "panels", "*.json"))):
        d = json.load(open(path))
        panels[(path.split(os.sep)[-3], d["name"])] = d["worlds"]

    out = {"run": {k: summary.get(k) for k in ("object_id", "status", "launch_sha", "device",
                                                "workers", "threads", "wall_seconds",
                                                "planned_episodes", "selected_heuristic",
                                                "heuristic_dev_mean_J", "counts")},
           "threshold_qos_per_step": THRESHOLD}
    out["panel_means"] = {f"{ph}/{name}": {"n": len(ws), **{label: mean(ws, key)
                                                          for key, label in COLUMNS}}
                          for (ph, name), ws in panels.items()}
    print("=== panel means ===")
    print("\t".join(["panel", "n"] + [c[1] for c in COLUMNS]))
    for name, row in out["panel_means"].items():
        print("\t".join([name, str(row["n"])] + [
            "-" if row[c[1]] is None else f"{row[c[1]]:.4g}" for c in COLUMNS]))

    # P0: device null against B10's CUDA record
    null = summary["null"]["worlds"]
    adq = [abs(w["delta_qos_per_step"]) for w in null]
    tau = pct(adq, 0.95)
    out["P0_device_null"] = {
        "n": len(null), "median_abs_delta_qos": st.median(adq), "tau_w_p95": tau,
        "max_abs_delta_qos": max(adq), "exact_worlds": sum(v < 1e-6 for v in adq),
        "within_0.01": sum(v < 0.01 for v in adq), "above_0.03": sum(v > 0.03 for v in adq),
        "mean_delta_qos": st.mean(w["delta_qos_per_step"] for w in null),
        "mean_delta_J": st.mean(w["delta_J"] for w in null),
        "median_holds": st.median(adq) < 0.01, "per_world_reading_available": tau <= THRESHOLD,
        "per_world": [(w["seed"], w["delta_qos_per_step"], w["delta_J"]) for w in null]}
    print(f"\nP0: median|dQoS|={st.median(adq):.5f} tau_w={tau:.4f} "
          f"per-world reading {'available' if tau <= THRESHOLD else 'unavailable (means only)'}")

    # Equivalence: record only
    ref = b09_reference(run_dir)
    eq = panels[("equivalence", "N_e0.00_x0.05")]
    out["equivalence_record_only"] = [
        {"seed": w["seed"], "b01_cpu_J": w[J], "b09_cuda_J": ref.get(w["seed"]),
         "delta_J": (w[J] - ref[w["seed"]]) if w["seed"] in ref else None} for w in eq]
    print("equivalence:", [(r["seed"], round(r["delta_J"], 2)) for r in out["equivalence_record_only"]])

    g = lambda c, s: panels[("grid", f"{c}_{s}")]
    n05, h05 = g("N", "e0.00_x0.05"), g("H1", "e0.00_x0.05")
    hl = panels[("reference", "Hlocal_e0.00_x0.05")]
    pred = {}
    pred["P2"] = {"H_central_qos": mean(h05, Q), "holds": mean(h05, Q) >= 0.60}
    gi, gl = mean(h05, Q) - mean(hl, Q), mean(hl, Q) - mean(n05, Q)
    pred["P2prime_descriptive"] = {"H_central": mean(h05, Q), "H_local": mean(hl, Q),
                                   "N": mean(n05, Q), "gap_info": gi, "gap_learn": gl,
                                   "gap_learn_gt_gap_info": gl > gi,
                                   "J": {"H_central": mean(h05, J), "H_local": mean(hl, J),
                                         "N": mean(n05, J)}}
    pre = [w.get("qos_per_step_pre_entry") for w in n05]
    below = sum(1 for v in pre if v is not None and v < 0.30)
    pred["P3"] = {"N_pre_entry_below_0.30": below, "N_pre_entry_mean": mean(n05, "qos_per_step_pre_entry"),
                  "H_central_pre_entry_mean": mean(h05, "qos_per_step_pre_entry"),
                  "N_pre_entry_within_tau_of_0.30": sum(1 for v in pre if v is not None and abs(v - 0.30) <= tau),
                  "holds": below >= 24 and mean(h05, "qos_per_step_pre_entry") >= 0.60,
                  "N_pre_entry_sorted": sorted(v for v in pre if v is not None)}
    curves = {}
    for c in ("N", "H1"):
        base = g(c, "e0.00_x0.05")
        rows = []
        for s in SETTINGS:
            ws = g(c, s)
            dq = [a[Q] - b[Q] for a, b in zip(ws, base)]
            dj = [a[J] - b[J] for a, b in zip(ws, base)]
            rows.append({"setting": s, "qos": mean(ws, Q), "J": mean(ws, J),
                         "d_qos": mean(ws, Q) - mean(base, Q), "d_J": mean(ws, J) - mean(base, J),
                         "retcost": mean(ws, "return_constraint_cost_sum"),
                         "cutoff": mean(ws, "cutoff_event_count_sum"),
                         "depletion": mean(ws, "depletion_event_count_sum"),
                         "Fmode": mean(ws, "mode_uav_step_fraction"),
                         "QoS_e2i": mean(ws, "qos_per_step_entry_to_input"),
                         "wait": mean(ws, "wait_ticks_total"),
                         "min_battery": mean(ws, "min_decoded_battery"),
                         "charger_wh": mean(ws, "charger_input_wh"),
                         "per_world_d_qos_descriptive": {
                             "sd": st.pstdev(dq), "min": min(dq), "max": max(dq),
                             "n_above_tau": sum(v > tau for v in dq),
                             "n_below_minus_tau": sum(v < -tau for v in dq),
                             "n_above_0.03": sum(v > THRESHOLD for v in dq),
                             "n_below_minus_0.03": sum(v < -THRESHOLD for v in dq)},
                         "per_world_d_J_mean": st.mean(dj)})
        curves[c] = rows
        w45, w85 = g(c, "e0.00_x0.45"), g(c, "e0.00_x0.85")
        d45, dj45 = mean(w45, Q) - mean(base, Q), mean(w45, J) - mean(base, J)
        dcut = mean(w45, "cutoff_event_count_sum") - mean(base, "cutoff_event_count_sum")
        ddep = mean(w45, "depletion_event_count_sum") - mean(base, "depletion_event_count_sum")
        pred[f"P1[{c}]"] = {"d_qos_0.45_vs_0.05": d45, "d_J": dj45, "d_cutoff": dcut,
                            "d_depletion": ddep,
                            "holds": d45 >= THRESHOLD and dj45 >= 0 and dcut <= 0 and ddep <= 0}
        d85 = mean(w85, Q) - mean(base, Q)
        de2i = (mean(w85, "qos_per_step_entry_to_input") or 0) - (mean(base, "qos_per_step_entry_to_input") or 0)
        dw = mean(w85, "wait_ticks_total") - mean(base, "wait_ticks_total")
        pred[f"P1c[{c}]"] = {"d_qos_0.85_vs_0.05": d85, "d_qos_e2i": de2i, "d_wait": dw,
                             "holds": d85 <= 0 and de2i < 0 and dw > 0}
        pred[f"P1prime[{c}]"] = [{"width": wd, "d_qos_level0.20_minus_level0": mean(g(c, hi), Q) - mean(g(c, lo), Q),
                                  "d_J": mean(g(c, hi), J) - mean(g(c, lo), J),
                                  "holds": abs(mean(g(c, hi), Q) - mean(g(c, lo), Q)) < THRESHOLD}
                                 for lo, hi, wd in MATCHED]
    out["predictions"] = pred
    out["width_curves"] = curves
    out["per_world"] = {f"{ph}/{n}": {"seeds": [w["seed"] for w in ws], "qos": [w[Q] for w in ws],
                                      "J": [w[J] for w in ws],
                                      "first_entry": [w.get("first_entry_step") for w in ws],
                                      "qos_pre_entry": [w.get("qos_per_step_pre_entry") for w in ws]}
                        for (ph, n), ws in panels.items()}
    print("\n=== predictions ===")
    for k, v in pred.items():
        print(k, json.dumps(v if not isinstance(v, dict) or "N_pre_entry_sorted" not in v
                            else {kk: vv for kk, vv in v.items() if kk != "N_pre_entry_sorted"}))
    print("\n=== width curves (d vs (0,.05)) ===")
    for c, rows in curves.items():
        for r in rows:
            print(f"{c} {r['setting']}: QoS={r['qos']:.4f} d={r['d_qos']:+.4f} J={r['J']:.1f} dJ={r['d_J']:+.1f} "
                  f"wait={r['wait']:.0f} Fmode={r['Fmode']:.3f} per-world d>.03:{r['per_world_d_qos_descriptive']['n_above_0.03']} "
                  f"<-.03:{r['per_world_d_qos_descriptive']['n_below_minus_0.03']}")
    json.dump(out, open(out_json, "w"), indent=1)
    print("written", out_json)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
