from __future__ import annotations

from collections import defaultdict
from math import sqrt
from typing import Callable, Iterable

import numpy as np
from scipy.stats import t

from .config import CHURNS, EVAL_SCHEDULES, EXECUTABLE_ARMS, GEOMETRIES, MASSES, SEEDS


def paired_summary(values: Iterable[float]) -> dict:
    values = [float(x) for x in values]
    if len(values) != 8:
        raise ValueError(f"registered analysis requires eight paired seeds, got {len(values)}")
    mean = float(np.mean(values)); sd = float(np.std(values, ddof=1)); se = sd / sqrt(8)
    return {"paired_seed_values": values, "mean": mean, "sd": sd,
            "ci95": [mean - float(t.ppf(.975, 7)) * se, mean + float(t.ppf(.975, 7)) * se],
            "ci90": [mean - float(t.ppf(.95, 7)) * se, mean + float(t.ppf(.95, 7)) * se]}


def _world_map(rows: list[dict]) -> dict[tuple, dict[str, dict]]:
    worlds: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        key = (row["seed"], row["schedule_index"], row["raw_index"], row["mass"], row["geometry"], row["churn"])
        worlds[key][row["arm"]] = row
    if any(set(arms) != set(EXECUTABLE_ARMS) for arms in worlds.values()):
        raise ValueError("paired world is missing a Stage-1 executable arm")
    return worlds


def _contrast(worlds: dict, left: str, right: str, predicate: Callable[[dict], bool], metric: str = "J") -> dict:
    seed_values = []
    for seed in SEEDS:
        values = [float(arms[left][metric]) - float(arms[right][metric]) for key, arms in worlds.items()
                  if key[0] == seed and predicate(arms[left])]
        if not values: raise ValueError(f"empty contrast {left}-{right} seed={seed}")
        seed_values.append(float(np.mean(values)))
    return paired_summary(seed_values)


def _ceiling_gap(worlds: dict, arm: str, predicate: Callable[[dict], bool]) -> dict:
    seed_values = []
    for seed in SEEDS:
        values = [float(arms[arm]["ceiling_J"]) - float(arms[arm]["J"]) for key, arms in worlds.items()
                  if key[0] == seed and predicate(arms[arm])]
        if not values: raise ValueError(f"empty ceiling gap {arm} seed={seed}")
        seed_values.append(float(np.mean(values)))
    return paired_summary(seed_values)


def analyze_stage1(rows: list[dict], evaluation_reports: list[dict], training_reports: list[dict],
                   audit: dict, peak_rss_bytes: int) -> dict:
    worlds = _world_map(rows)
    primary = lambda r: r["n"] == 15 and r["geometry"] == "COUPLED"
    fixed = lambda r: primary(r) and r["mass"] == "FIXED_MASS"
    switch = lambda r: primary(r) and r["churn"] == "SWITCH_REQUIRED"
    keep = lambda r: primary(r) and r["churn"] == "KEEP_OPTIMAL"
    l15 = _contrast(worlds, "G-RELEASE", "HANDOFF-RDA", primary)
    fixed_effect = _contrast(worlds, "G-RELEASE", "HANDOFF-RDA", fixed)
    switch_effect = _contrast(worlds, "G-RELEASE", "HANDOFF-RDA", switch)
    keep_effect = _contrast(worlds, "G-RELEASE", "HANDOFF-RDA", keep)
    g_zero = _contrast(worlds, "G-RELEASE", "ZERO-RDA", primary)
    g_frozen = _contrast(worlds, "G-RELEASE", "FROZEN-RDA", primary)
    g_permute = _contrast(worlds, "G-RELEASE", "G-PERMUTE", primary)
    headroom = _ceiling_gap(worlds, "HANDOFF-RDA", primary)

    q_cells: list[dict] = []
    opportunity_complete = True; assignments_available = True
    for seed in SEEDS:
        for schedule_index in (2, 3):
            schedule = EVAL_SCHEDULES[schedule_index]
            for mass in MASSES:
                for churn in CHURNS:
                    selected = [arms for key, arms in worlds.items() if key[0] == seed and key[1] == schedule_index
                                and key[3] == mass and key[4] == "COUPLED" and key[5] == churn]
                    contested = [arms for arms in selected if arms["G-RELEASE"]["contested"]]
                    opportunity_complete &= len(contested) >= 16
                    rates = {}
                    for other in ("ZERO-RDA", "FROZEN-RDA", "HANDOFF-RDA", "G-PERMUTE"):
                        values = [arms["G-RELEASE"].get(f"disagree_G_{other}") for arms in contested]
                        if any(value is None for value in values) or not values:
                            assignments_available = False; rates[other] = None
                        else:
                            rates[other] = float(np.mean(values))
                    q_cells.append({"seed": seed, "schedule": f"{schedule[0]}->{schedule[1]}",
                                    "mass": mass, "churn": churn, "denominator": len(contested), "rates": rates})
    aggregate_rates: dict[str, dict] = {}
    for other in ("ZERO-RDA", "FROZEN-RDA", "HANDOFF-RDA", "G-PERMUTE"):
        all_values = [cell["rates"][other] for cell in q_cells if cell["rates"][other] is not None]
        aggregate_rates[other] = {
            "overall_equal_cell_rate": float(np.mean(all_values)) if len(all_values) == len(q_cells) else None,
            "churn_equal_cell_rates": {churn: (float(np.mean([cell["rates"][other] for cell in q_cells
                if cell["churn"] == churn])) if all(cell["rates"][other] is not None for cell in q_cells if cell["churn"] == churn)
                else None) for churn in CHURNS},
        }
    assignment_gate = assignments_available and opportunity_complete and all(
        item["overall_equal_cell_rate"] >= .20 and min(item["churn_equal_cell_rates"].values()) >= .10
        for item in aggregate_rates.values())

    audit_gate = bool(audit["all_gates_except_process_rss"] and peak_rss_bytes <= 2 * 1024**3)
    release_conditions = {
        "1_PRIMARY_L15_G_MINUS_HANDOFF": l15["mean"] >= .05 and l15["ci95"][0] > 0,
        "2_FIXED_MASS_G_MINUS_HANDOFF": fixed_effect["mean"] >= .03 and fixed_effect["ci95"][0] > 0,
        "3_SWITCH_SUPERIOR_KEEP_NONINFERIOR": switch_effect["mean"] >= .03 and switch_effect["ci95"][0] > 0
            and keep_effect["ci90"][0] > -.03,
        "4_BID_CHANNEL_VALUE": g_zero["mean"] >= .05 and g_zero["ci95"][0] > 0
            and g_frozen["mean"] >= .03 and g_frozen["ci95"][0] > 0
            and g_permute["mean"] >= .03 and g_permute["ci95"][0] > 0,
        "5_CONTESTED_ASSIGNMENT_CHANGE": assignment_gate,
        "6_RC_MIP_HEADROOM_OVER_HANDOFF": headroom["mean"] >= .05 and headroom["ci95"][0] > 0,
        "7_OPERATION_MEMORY_RSS_LATENCY": audit_gate,
    }

    cell_contrasts = []
    for schedule_index, schedule in enumerate(EVAL_SCHEDULES):
        for mass in MASSES:
            for geometry in GEOMETRIES:
                for churn in CHURNS:
                    predicate = lambda r, si=schedule_index, m=mass, g=geometry, c=churn: (
                        r["schedule_index"] == si and r["mass"] == m and r["geometry"] == g and r["churn"] == c)
                    cell_contrasts.append({"schedule": f"{schedule[0]}->{schedule[1]}", "mass": mass,
                        "geometry": geometry, "churn": churn,
                        **{f"G_minus_{arm}": _contrast(worlds, "G-RELEASE", arm, predicate)
                           for arm in ("ZERO-RDA", "FROZEN-RDA", "HANDOFF-RDA", "G-PERMUTE")},
                        **{f"RC_MIP_minus_{arm}": _ceiling_gap(worlds, arm, predicate)
                           for arm in EXECUTABLE_ARMS}})

    n12 = _contrast(worlds, "G-RELEASE", "HANDOFF-RDA",
                    lambda r: r["n"] == 12 and r["geometry"] == "COUPLED")
    range_change = paired_summary([a - b for a, b in zip(l15["paired_seed_values"], n12["paired_seed_values"])])
    separable = _contrast(worlds, "G-RELEASE", "HANDOFF-RDA",
                          lambda r: r["n"] == 15 and r["geometry"] == "SEPARABLE")
    geometry = paired_summary([a - b for a, b in zip(l15["paired_seed_values"], separable["paired_seed_values"])])

    observables = []
    for schedule_index, schedule in enumerate(EVAL_SCHEDULES):
        for mass in MASSES:
            for geometry_name in GEOMETRIES:
                for churn in CHURNS:
                    for arm in EXECUTABLE_ARMS:
                        selected = [r for r in rows if r["schedule_index"] == schedule_index and r["mass"] == mass
                                    and r["geometry"] == geometry_name and r["churn"] == churn and r["arm"] == arm]
                        observables.append({"schedule": f"{schedule[0]}->{schedule[1]}", "mass": mass,
                            "geometry": geometry_name, "churn": churn, "arm": arm,
                            **{metric: float(np.mean([r[metric] for r in selected]))
                               for metric in ("J", "GAP", "Trec", "survivor_switch_fraction", "dummy_fraction")},
                            "service_by_tick_task": np.mean([r["service"] for r in selected], 0).tolist(),
                            "waste_by_tick_task": np.mean([r["waste"] for r in selected], 0).tolist()})

    activity = {
        "checkpoint_and_training": len(training_reports) == 8 and all(r.get("final_update") == 32
            and r.get("trials") == 4096 and r.get("optimizer_steps") == 4096 for r in training_reports),
        "complete_five_arm_panel": len(rows) == 8 * 768 * 5,
        "tagged_conclusion_ceilings": sum(r["tagged_certificate_ceilings"] for r in evaluation_reports) == 6144,
        "row_mapping_complete": all(not r["row_order_invariance_failures"] for r in evaluation_reports),
        "contested_opportunity_complete": opportunity_complete,
        "assignment_rates_available": assignments_available,
        "scaling_audit_complete": len(audit["records"]) == 20,
    }
    activity["full_stage1_release_boundary_crossed"] = all(activity.values())
    return {
        "estimand_activity": {"L15": activity["complete_five_arm_panel"],
            "fixed_mass": activity["complete_five_arm_panel"], "churn_subgroups": activity["complete_five_arm_panel"],
            "bid_interventions": activity["complete_five_arm_panel"],
            "assignment_change": activity["assignment_rates_available"] and activity["contested_opportunity_complete"],
            "headroom": activity["tagged_conclusion_ceilings"], "engineering": activity["scaling_audit_complete"]},
        "activity_boundary": activity,
        "stage2_released": activity["full_stage1_release_boundary_crossed"] and all(release_conditions.values()),
        "release_conditions": release_conditions,
        "primary_estimands": {"L15_G_minus_HANDOFF": l15, "FIXED_MASS_G_minus_HANDOFF": fixed_effect,
            "SWITCH_G_minus_HANDOFF": switch_effect, "KEEP_G_minus_HANDOFF": keep_effect,
            "G_minus_ZERO": g_zero, "G_minus_FROZEN": g_frozen, "G_minus_PERMUTE": g_permute,
            "RC_MIP_minus_HANDOFF": headroom, "L12_G_minus_HANDOFF": n12,
            "D_range": range_change, "D_geometry": geometry},
        "geometry_modifier_support": geometry["mean"] >= .03 and geometry["ci95"][0] > 0,
        "assignment_change": {"cells": q_cells, "equal_cell_rates": aggregate_rates},
        "cell_contrasts": cell_contrasts, "observable_cells": observables,
    }
