"""Exploratory complete-panel reductions; three fits remain three units."""
from __future__ import annotations

import math

from experiments.candidates.uav_fleet_transmission.b10_service_assignment.metrics import (
    COMPARISON_FIELDS, describe, paired,
)
from .contract import FINAL_WORLDS


def summarize_finals(rows, selection):
    indexed = {(r["seed"], r["arm"]): r for r in rows}
    arms = ("C", "H_T") + (() if selection["final_identity_alias"] else ("T_star",)) + ("L0", "L1", "L2")
    if len(indexed) != len(rows) or set(indexed) != {(s, a) for s in FINAL_WORLDS for a in arms}:
        raise AssertionError("fixed distinct final panel incomplete")
    if any(r["status"] != "completed" for r in rows):
        raise AssertionError("failed final cannot be reduced as a complete result")
    tstar = selection["final_identity_alias"] or "T_star"
    fields = COMPARISON_FIELDS + ("native_cpu_seconds", "reset_cpu_seconds", "configuration_cpu_seconds")
    levels = {arm: {field: describe([indexed[s, arm][field] for s in FINAL_WORLDS]) for field in fields}
              for arm in arms}
    contrasts = {}
    for left, right in [("H_T", "C"), (tstar, "C"), (tstar, "H_T")] + [
            (left, right) for left in ("L0", "L1", "L2") for right in dict.fromkeys((tstar, "C", "H_T"))]:
        if left == right:
            continue
        contrasts[left+"-"+right] = {field: paired(
            [indexed[s, left][field]-indexed[s, right][field] for s in FINAL_WORLDS], FINAL_WORLDS)
            for field in fields}
    by_fit = [math.fsum(indexed[s, f"L{fit}"]["J_total"]-indexed[s, tstar]["J_total"]
                       for s in FINAL_WORLDS)/len(FINAL_WORLDS) for fit in range(3)]
    training_units = paired(by_fit, ("L0", "L1", "L2"))
    training_units["by_fit"] = training_units.pop("by_world")
    return dict(levels=levels, contrasts=contrasts, T_star_executable=tstar,
                dependent_T_star_alias=selection["final_identity_alias"],
                primary_three_fit_J_effect=training_units, training_replication_units=3,
                uncertainty="world t95 df31 conditional on each fixed fit; fit-mean t95 df2 conditional on the common32world panel, weak small-n/normality precision; exploration only",
                interpretation_scope="complete learned package; no unique long-horizon mechanism, safety/default adoption or optimal ordinary-rule claim")
