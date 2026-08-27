from __future__ import annotations

from fractions import Fraction
from typing import Any


NODE_IDS = (
    "architecture-binding",
    "schedule-arithmetic-binding",
    "separation-address-binding",
    "workload-binding",
    "evaluation-binding",
    "measurement-control-binding",
    "complete-manifest-binding",
    "result-firewall-binding",
)


def validate_binding(binding: dict[str, Any]) -> dict[str, Any]:
    architecture = binding["architecture"]
    slots = architecture["structural_terminal_slots"]
    if len(slots) != 16 or any(
        row["parameter_values"] is not None or row["checkpoint"] is not None
        for row in slots
    ):
        raise ValueError("S1 structural terminal slots materialized forbidden values")
    fixtures = binding["epsilon_contract"]["fixtures"]
    for fixture in fixtures:
        decision = fixture["completed_decisions"]
        expected = Fraction(2, 5) - Fraction(7, 20) * Fraction(decision, 1984)
        if Fraction(*fixture["epsilon"]) != expected:
            raise ValueError("S1 epsilon arithmetic drifted")
    update = binding["window_update_contract"]
    if update["parameter_values"] is not None or update["numeric_signal_values"] is not None:
        raise ValueError("S1 update schema materialized forbidden values")
    if binding["workload"]["registered_total_transactions"] != 157_696:
        raise ValueError("S1 workload arithmetic drifted")
    if set(binding["evaluation_contract"]["branches"]) != {
        "NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"
    }:
        raise ValueError("S1 evaluation branch set drifted")
    if binding["measurement_schema"]["values_materialized"]:
        raise ValueError("S1 measurement schema materialized values")
    manifest = binding["result_manifest_contract"]
    if (
        not manifest["schema_only"]
        or manifest["values_materialized"]
        or manifest["partial_commit_allowed"]
        or not manifest["atomic_final_replace_required"]
    ):
        raise ValueError("S1 result manifest is not complete-only")
    if set(binding["firewall"].values()) != {False} or binding["effect_refs"]:
        raise ValueError("S1 result firewall is not closed")
    return {
        "terminal_status": "TECHNICALLY_BOUND",
        "nodes": [{"id": node_id, "status": "PASS"} for node_id in NODE_IDS],
    }
