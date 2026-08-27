from __future__ import annotations

from collections import defaultdict
from itertools import product
from typing import Any


NODE_IDS = (
    "authority-current-bytes",
    "counter-address-equality",
    "host-eight-cell-support",
    "registered-reassociation",
    "resource-work-equality",
    "churn-state-ownership",
    "information-path-firewall",
    "atomic-complete-output",
)


def validate_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    strata = evidence["strata"]
    if len(strata) != 384:
        raise ValueError("S0 evidence must contain exactly 384 outer strata")

    address_groups: dict[tuple[Any, ...], set[str]] = defaultdict(set)
    accepted_by_arm = {"AUTHENTIC": 0, "REASSOCIATED": 0}
    denied = 0
    for stratum in strata:
        key = stratum["key"]
        pair_key = tuple(key[name] for name in (
            "M", "occupancy", "i", "r", "seed", "kappa", "mu", "lambda"
        ))
        address_groups[pair_key].add(stratum["paired_address_sha256"])
        worlds = stratum["worlds"]
        if len(worlds) != 8 or {
            (
                world["relevant_slot"],
                world["relevant_reservation"],
                world["decoy_reservation"],
            )
            for world in worlds
        } != set(product((0, 1), repeat=3)):
            raise ValueError("S0 eight-cell host support is incomplete")
        if key["arm"] == "REASSOCIATED":
            for block_start in (0, 4):
                block = worlds[block_start : block_start + 4]
                if {
                    (world["relevant_slot"], world["semantic_bit"])
                    for world in block
                } != set(product((0, 1), repeat=2)):
                    raise ValueError("registered reassociation table is incomplete")
        for world in worlds:
            if set(world["selector_view"]) != {"i", "r", "surface_bit", "auth_ok"}:
                raise ValueError("selector information path escaped its four fields")
            for transaction in world["transactions"]:
                if transaction["accepted"]:
                    if transaction["resource_receipt"] != {
                        "payload_reads": 1,
                        "reservation_services": 1,
                    }:
                        raise ValueError("accepted S0 work receipt drifted")
                    accepted_by_arm[key["arm"]] += 1
                else:
                    denied += 1
                    if transaction["payload_exposed"] or transaction["score_exposed"]:
                        raise ValueError("denied S0 request exposed private content")
    if len(address_groups) != 192 or any(len(values) != 1 for values in address_groups.values()):
        raise ValueError("paired arm addresses are not byte-identical")
    if accepted_by_arm != {"AUTHENTIC": 6144, "REASSOCIATED": 6144} or denied != 3072:
        raise ValueError("S0 accepted/denied transaction counts drifted")

    fixtures = evidence["churn_fixtures"]
    if len(fixtures) != 24 or any(len(row["windows"]) != 5 for row in fixtures):
        raise ValueError("S0 churn fixture panel is incomplete")
    if set(evidence["firewall"].values()) != {False} or evidence["effect_refs"]:
        raise ValueError("S0 result firewall is not closed")
    if not all(
        stratum["churn_fixture_id"]
        in {fixture["fixture_id"] for fixture in fixtures}
        for stratum in strata
    ):
        raise ValueError("S0 stratum lacks a bound churn fixture")

    return {
        "terminal_status": "TECHNICALLY_ACCEPTED",
        "nodes": [{"id": node_id, "status": "PASS"} for node_id in NODE_IDS],
    }
