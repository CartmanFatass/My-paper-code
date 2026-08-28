from __future__ import annotations

from typing import Any, Mapping, Sequence


NODE_IDS = (
    "current-byte-inputs",
    "nonregistered-fixture-boundary",
    "exact-learner-and-update",
    "checkpoint-resume-no-repeat",
    "branch-resource-contract",
    "complete-only-result",
    "resource-envelope",
    "registered-scientific-firewall",
)


def validate_acceptance(
    acceptance: Mapping[str, Any],
    orchestration: Mapping[str, Any],
    branches: Sequence[Mapping[str, Any]],
    technical_result: Mapping[str, Any],
) -> dict[str, Any]:
    if orchestration.get("terminal_status") != "TECHNICAL_COMPLETE":
        raise ValueError("S2 orchestration is incomplete")
    ledger = orchestration.get("update_ledger")
    if not isinstance(ledger, list) or len(ledger) != 8 or len(set(ledger)) != 8:
        raise ValueError("S2 update ledger is incomplete or repeated")
    if (
        orchestration.get("registered_seed_or_arm_used") is not False
        or orchestration.get("cross_arm_or_seed_state") is not False
    ):
        raise ValueError("S2 orchestration escaped its nonregistered boundary")
    if len(branches) != 8 or any(
        row.get("resource_receipt") != [1, 1]
        or row.get("updates_parameters") is not False
        or row.get("question_relevant_values") is not None
        for row in branches
    ):
        raise ValueError("S2 branch contract is incomplete")
    if (
        technical_result.get("complete") is not True
        or technical_result.get("registered_manifest") is not False
        or technical_result.get("question_relevant_values") is not None
        or technical_result.get("effect_refs") != []
    ):
        raise ValueError("S2 technical result is not complete-only")
    if set(acceptance["firewall"].values()) != {False} or acceptance["effect_refs"]:
        raise ValueError("S2 registered/scientific firewall is open")
    projection = acceptance["complete_transaction_projection"]
    if (
        projection["workers"] != 1
        or projection["wall_seconds"]["high"] > 600
        or projection["hard_caps"]["peak_memory_bytes"] > 1_073_741_824
        or projection["hard_caps"]["scratch_bytes"] > 536_870_912
    ):
        raise ValueError("S2 projection exceeds the accepted envelope")
    return {
        "terminal_status": "TECHNICALLY_ACCEPTED",
        "nodes": [{"id": node_id, "status": "PASS"} for node_id in NODE_IDS],
    }
