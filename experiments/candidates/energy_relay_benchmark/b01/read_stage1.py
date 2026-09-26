"""Stage 1 reading (energy_relay_benchmark B02): the SET development fit's checkpoint curve against
the fixed comparators, by the declaration in NOTES ("Stage 1, revised to Pro's preferred form" and
the Stage 0 item 1 result: the evaluation mode is an axis).

Usage: python read_stage1.py --b01 <b01_ref_a02> --refs <b02_s0_refs_a01> --train <b02_s1_set_a01>
                             --evals <eval run dir> [...] --out <json>

Readings, separately and never as a pass mark: (1) the curve c00..c06 per evaluation mode
(QoS/step and the co-primaries J, return cost, cutoff/depletion events, minimum battery, plus the
five position diagnostics and the phase split); (2) the .60 milestone, labelled "H_local's level";
(3) improvement over the model's own initialisation c00, paired by world; (4) the gaps to H_central
(.774) and H_local (.597) and, beside them, to the package references H_spawn, H_park2 and N,
paired by world; (5) service-versus-risk conflicts (service up while return cost, events or the
minimum-battery tail are worse than the comparator) reported as conflicts; (6) the training curve
from progress.jsonl (per-rollout J, QoS/step, shield-mapping share, F-mode share, entropy, live
lanes at the boundary, wall) and (7) Pro's pre-registered failure-explanation table, filled with the
observable proxies only (non-exclusive candidates; no rescue is selected here). Standard library.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics as st

Q = "qos_satisfaction_ratio_per_step"
J = "raw_native_J"
MILESTONE = 0.60           # H_local's level on 955001-955032 (.597), labelled so
THRESHOLD = 0.03           # the practical QoS/step threshold of B01
COLS = [Q, J, "return_constraint_cost_sum", "cutoff_event_count_sum", "depletion_event_count_sum",
        "min_decoded_battery", "mode_uav_step_fraction", "first_entry_step", "first_input_step",
        "qos_per_step_pre_entry", "qos_per_step_entry_to_input", "qos_per_step_post_input",
        "charger_input_wh", "wait_ticks_total", "guard_blocked_actions", "guard_checked_actions",
        "feedback_entry_count", "boundary_share_normal_mode", "altitude_floor_share_normal_mode",
        "anchor_uav_steps_within_300m", "centre_uav_steps_within_300m", "first_service_step", "zero_service"]
RISK = ("return_constraint_cost_sum", "cutoff_event_count_sum", "depletion_event_count_sum")
PANEL_RE = re.compile(r"^L_(c\d\d)_(deterministic|stochastic)_e0\.00_x0\.05$")


def load_panel(path):
    d = json.load(open(path))
    return d, {w["seed"]: w for w in d["worlds"]}


def mean(rows, key):
    vals = [r.get(key) for r in rows]
    vals = [float(v) for v in vals if v is not None]
    return st.mean(vals) if vals else None


def summarise(rows):
    out = {k: mean(rows, k) for k in COLS}
    out["n"] = len(rows)
    out["zero_service_worlds"] = sum(1 for r in rows if r.get("zero_service"))
    out["failed_worlds"] = sum(1 for r in rows if r.get("failed"))
    out["min_battery_p10"] = (sorted(float(r["min_decoded_battery"]) for r in rows if r.get("min_decoded_battery") is not None)
                              [max(0, len(rows) // 10 - 1)] if rows else None)
    out["guard_blocked_share"] = (out["guard_blocked_actions"] / out["guard_checked_actions"]
                                  if out.get("guard_checked_actions") else None)
    return out


def paired(a, b, key):
    """b - a per world on the common seeds: mean, paired SE, count positive, range."""
    seeds = [s for s in a if s in b and a[s].get(key) is not None and b[s].get(key) is not None]
    d = [float(b[s][key]) - float(a[s][key]) for s in seeds]
    if not d:
        return None
    return {"n": len(d), "mean": st.mean(d), "paired_se": st.stdev(d) / len(d) ** 0.5 if len(d) > 1 else None,
            "positive": sum(x > 0 for x in d), "min": min(d), "max": max(d)}


def gap_block(learner, comparator):
    """Learner minus comparator on the co-primaries, with the service-vs-risk conflict flag."""
    block = {k: paired(comparator, learner, k) for k in (Q, J) + RISK + ("min_decoded_battery",)}
    q = block[Q]
    worse_risk = [k for k in RISK if block[k] and block[k]["mean"] > 0]
    if block["min_decoded_battery"] and block["min_decoded_battery"]["mean"] < 0:
        worse_risk.append("min_decoded_battery")
    block["conflict"] = ("service higher but risk worse: " + ", ".join(worse_risk)
                         if q and q["mean"] > 0 and worse_risk else None)
    return block


def training_curve(train_dir):
    path = os.path.join(train_dir, "progress.jsonl")
    rows, checkpoints = [], []
    if not os.path.exists(path):
        return {"available": False}
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        ev = rec.get("event", rec)
        if isinstance(ev, dict) and ev.get("event") == "rollout":
            keep = {k: ev.get(k) for k in ("rollout", "transitions", "lane_native_J", "lane_qos_per_step",
                                            "shield_mapping_share", "f_mode_uav_step_share",
                                            "live_lanes_at_boundary", "collection_seconds", "update_seconds",
                                            "action_entropy", "discoverer_policy_loss", "discoverer_value_loss")}
            if isinstance(keep.get("lane_qos_per_step"), list) and keep["lane_qos_per_step"]:
                keep["qos_per_step"] = st.mean(keep["lane_qos_per_step"])
            if isinstance(keep.get("lane_native_J"), list) and keep["lane_native_J"]:
                keep["native_J"] = st.mean(keep["lane_native_J"])
            rows.append(keep)
        elif isinstance(ev, dict) and ev.get("event") == "checkpoint":
            checkpoints.append({k: ev.get(k) for k in ("checkpoint", "rollout", "transitions", "wall_seconds")})
    out = {"available": True, "rollouts": rows, "checkpoints": checkpoints, "n_rollouts": len(rows)}
    if rows:
        walls = [(r.get("collection_seconds") or 0) + (r.get("update_seconds") or 0) for r in rows]
        out["seconds_per_rollout_mean"] = st.mean(walls)
        out["seconds_per_rollout_first_two"] = walls[:2]
        out["projected_total_hours_at_mean_rate"] = st.mean(walls) * 200 / 3600
        out["live_lane_boundaries"] = sum(1 for r in rows if (r.get("live_lanes_at_boundary") or 0) > 0)
        out["mapping_share_mean"] = mean(rows, "shield_mapping_share")
        out["qos_per_step_first_five"] = [r.get("qos_per_step") for r in rows[:5]]
        out["qos_per_step_last_five"] = [r.get("qos_per_step") for r in rows[-5:]]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b01", required=True)
    ap.add_argument("--refs", required=True)
    ap.add_argument("--train", required=True)
    ap.add_argument("--evals", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    comps = {"H_central": load_panel(os.path.join(args.b01, "grid", "panels", "H1_e0.00_x0.05.json"))[1],
             "H_local": load_panel(os.path.join(args.b01, "reference", "panels", "Hlocal_e0.00_x0.05.json"))[1],
             "N_deterministic": load_panel(os.path.join(args.b01, "grid", "panels", "N_e0.00_x0.05.json"))[1],
             "H_spawn": load_panel(os.path.join(args.refs, "stage0-references", "panels", "Hspawn_e0.00_x0.05.json"))[1],
             "H_park2": load_panel(os.path.join(args.refs, "stage0-references", "panels", "Hpark2_e0.00_x0.05.json"))[1]}
    panels, final_panels = {}, {}
    for run in args.evals:
        for path in sorted(glob.glob(os.path.join(run, "checkpoint-eval", "panels", "L_*.json"))):
            d, rows = load_panel(path)
            m = PANEL_RE.match(d["name"])
            if m:
                panels[(m.group(1), m.group(2))] = (d, rows)
        for path in sorted(glob.glob(os.path.join(run, "checkpoint-eval", "final", "panels", "L_*.json"))):
            d, rows = load_panel(path)
            m = PANEL_RE.match(d["name"])
            if m:
                final_panels[(m.group(1), m.group(2))] = (d, rows)
    out = {"comparators": {k: summarise(list(v.values())) for k, v in comps.items()},
           "milestone": {"level": MILESTONE, "label": "H_local's level on 955001-955032 (.597), not a pass mark"},
           "training": training_curve(args.train), "checkpoints": {}, "final_holdout": {}}
    identities = {}
    for (cid, mode), (d, rows) in sorted(panels.items()):
        rl = list(rows.values())
        s = summarise(rl)
        entry = {"summary": s, "record": {k: d.get(k) for k in ("checkpoint", "transitions", "policy_seed", "draw",
                                                                  "policy_identity", "controller_information")},
                 "milestone_reached": s[Q] is not None and s[Q] >= MILESTONE,
                 "worlds_at_or_above_milestone": sum(1 for r in rl if r.get(Q) is not None and r[Q] >= MILESTONE)}
        identities[(cid, mode)] = d.get("policy_identity")
        c00 = panels.get(("c00", mode))
        if c00 and cid != "c00":
            entry["vs_c00"] = gap_block(rows, c00[1])
        entry["gaps"] = {name: gap_block(rows, comp) for name, comp in comps.items()}
        out["checkpoints"][f"{cid}_{mode}"] = entry
    for (cid, mode), (d, rows) in sorted(final_panels.items()):
        out["final_holdout"][f"{cid}_{mode}"] = {"summary": summarise(list(rows.values())),
                                                 "note": "957001-957032, read once, frozen final model only"}
    # curves in reading order
    curves = {}
    for mode in ("deterministic", "stochastic"):
        seq = [(cid, out["checkpoints"][f"{cid}_{mode}"]["summary"]) for (cid, m) in sorted(panels) if m == mode]
        if seq:
            curves[mode] = {"checkpoints": [c for c, _ in seq], Q: [s[Q] for _, s in seq], J: [s[J] for _, s in seq],
                            "return_cost": [s["return_constraint_cost_sum"] for _, s in seq],
                            "min_battery": [s["min_decoded_battery"] for _, s in seq],
                            "boundary_share": [s["boundary_share_normal_mode"] for _, s in seq],
                            "first_service_step": [s["first_service_step"] for _, s in seq],
                            "zero_service_worlds": [s["zero_service_worlds"] for _, s in seq]}
            q = curves[mode][Q]
            curves[mode]["last_step_delta"] = (q[-1] - q[-2]) if len(q) >= 2 else None
            curves[mode]["still_improving_at_end"] = (len(q) >= 3 and q[-1] - q[-2] > THRESHOLD / 2
                                                     and q[-2] - q[-3] > 0)
            curves[mode]["best_checkpoint"] = max(range(len(q)), key=lambda i: q[i] if q[i] is not None else -1)
    out["curves"] = curves
    # Pro's failure-explanation table, filled with observable proxies (no rescue selected)
    last = None
    for mode in ("deterministic", "stochastic"):
        if mode in curves:
            last = out["checkpoints"][f"{curves[mode]['checkpoints'][-1]}_{mode}"]["summary"]; break
    tr = out["training"]
    hc = out["comparators"]["H_central"]
    table = []
    if last:
        table = [
            {"observation": "users seen late / access late / little useful service exposure in training",
             "proxies": {"first_service_step_last": last["first_service_step"], "qos_pre_entry_last": last["qos_per_step_pre_entry"],
                         "training_qos_first_five": tr.get("qos_per_step_first_five"), "mapping_share_mean": tr.get("mapping_share_mean")},
             "would_strengthen": "insufficient opportunity to reach useful states", "would_not_follow": "an identified exploration defect; that a curriculum works"},
            {"observation": "users and paths present, delivery not held or improved",
             "proxies": {"first_service_step_last": last["first_service_step"], "qos_last": last[Q], "curve": {m: c[Q] for m, c in curves.items()}},
             "would_strengthen": "signal use, optimisation, return trade-off or credit assignment as candidates", "would_not_follow": "credit assignment proven the bottleneck"},
            {"observation": "early service good, gap widens after F / recharging",
             "proxies": {"learner_pre_entry": last["qos_per_step_pre_entry"], "learner_post_input": last["qos_per_step_post_input"],
                         "H_central_pre_entry": hc["qos_per_step_pre_entry"], "H_central_post_input": hc["qos_per_step_post_input"]},
             "would_strengthen": "deployment and recovery under feedback worth attention", "would_not_follow": "retune the exit threshold or change the scheduler"},
            {"observation": "targets not reached, non-zero proposals often guard-blocked",
             "proxies": {"guard_blocked_share_last": last["guard_blocked_share"], "H_central_guard_blocked_share": hc["guard_blocked_share"],
                         "boundary_share_last": last["boundary_share_normal_mode"]},
             "would_strengthen": "action filtering under specific geometry may limit execution", "would_not_follow": "H's global blocked share diagnoses SET"},
            {"observation": "still improving at the end with a large gap",
             "proxies": {"still_improving_at_end": {m: c["still_improving_at_end"] for m, c in curves.items()},
                         "gap_to_H_central_last": {m: out["checkpoints"][f"{c['checkpoints'][-1]}_{m}"]["gaps"]["H_central"][Q]["mean"] for m, c in curves.items()}},
             "would_strengthen": "the exposure may not describe the plateau", "would_not_follow": "extend this fit after the scores (a longer recipe is a new declared study)"},
            {"observation": "low plateau, technical execution normal",
             "proxies": {"live_lane_boundaries": tr.get("live_lane_boundaries"), "failed_worlds_last": last["failed_worlds"],
                         "identity_per_panel_present": all(v for v in identities.values()), "curve_flat": {m: (max(x for x in c[Q] if x is not None) - min(x for x in c[Q] if x is not None)) < THRESHOLD for m, c in curves.items()}},
             "would_strengthen": "this fixed programme performs limitedly at this exposure", "would_not_follow": "central information insufficient, MARL useless, or joint skills required"}]
    out["failure_explanations_pro_table"] = {"non_exclusive": True, "rows": table}
    json.dump(out, open(args.out, "w"), indent=1)
    for mode, c in curves.items():
        print(f"{mode}: " + " ".join(f"{cid} {q:.3f}" for cid, q in zip(c["checkpoints"], c[Q]) if q is not None)
              + f" | best {c['checkpoints'][c['best_checkpoint']]} | still improving {c['still_improving_at_end']}")
        last_key = f"{c['checkpoints'][-1]}_{mode}"; e = out["checkpoints"][last_key]
        print(f"  {last_key}: milestone {'reached' if e['milestone_reached'] else 'not reached'} ({e['worlds_at_or_above_milestone']}/32 worlds ≥ .60)"
              + (f"; vs c00 {e['vs_c00'][Q]['mean']:+.3f} (SE {e['vs_c00'][Q]['paired_se']:.3f}, {e['vs_c00'][Q]['positive']}/32 positive)" if e.get("vs_c00") else ""))
        for name in ("H_central", "H_local", "H_park2", "H_spawn", "N_deterministic"):
            g = e["gaps"][name]
            print(f"    vs {name}: QoS {g[Q]['mean']:+.3f} (SE {g[Q]['paired_se']:.3f}) J {g[J]['mean']:+.0f} retcost {g['return_constraint_cost_sum']['mean']:+.1f}" + (f"  CONFLICT: {g['conflict']}" if g["conflict"] else ""))
    if tr.get("available"):
        print(f"training: {tr['n_rollouts']} rollouts, {tr.get('seconds_per_rollout_mean', 0):.0f} s/rollout, projected {tr.get('projected_total_hours_at_mean_rate', 0):.1f} h, live-lane boundaries {tr.get('live_lane_boundaries')}")
    print("written", args.out)


if __name__ == "__main__":
    main()
