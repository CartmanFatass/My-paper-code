from __future__ import annotations

from collections.abc import Mapping
from typing import Any


RESOURCE_CAP = {"payload_reads": 1, "reservation_services": 1}


def accepted_receipt(
    records: Mapping[int, int], open_slot: int, lane_action: int
) -> dict[str, Any]:
    """Independently validate one technical open/service boundary request."""

    if open_slot not in (0, 1) or lane_action not in (0, 1):
        raise ValueError("S0 accepts only one binary open and one binary lane action")
    if set(records) != {0, 1} or set(records.values()) - {0, 1}:
        raise ValueError("S0 records must contain exactly two one-bit payloads")
    payload = records[open_slot]
    return {
        "accepted": True,
        "open_slot": open_slot,
        "lane_action": lane_action,
        "resource_receipt": dict(RESOURCE_CAP),
        "payload_bit": payload,
        "oracle_payload_match": payload == records[open_slot],
    }


def denied_open_both_receipt() -> dict[str, Any]:
    return {
        "accepted": False,
        "request": "OPEN_BOTH",
        "required_resources": {"payload_reads": 2, "reservation_services": 1},
        "resource_cap": dict(RESOURCE_CAP),
        "payload_exposed": False,
        "score_exposed": False,
    }
