"""Fail-closed DEARS-B1 receipt verifier and fixed reference decoder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .domain import Action, INTERLEAVINGS, Event, LeaseUpdate, OwnerUpdate, Receipt, Version


@dataclass(frozen=True)
class Verification:
    live: bool
    content: int | None
    rejection: str | None


def reject(reason: str) -> Verification:
    return Verification(False, None, reason)


def _verify(
    events: Sequence[object], *, final_owner: Version, final_lease: Version,
    decision_time: int = 0,
) -> Verification:
    """Apply the frozen precedence; malformed or ambiguous input returns bottom."""
    if not isinstance(events, Sequence) or len(events) != 5:
        return reject("event_count")
    if any(not isinstance(row, (Receipt, OwnerUpdate, LeaseUpdate)) for row in events):
        return reject("malformed_event")
    receipts = [row for row in events if isinstance(row, Receipt)]
    owners = [row for row in events if isinstance(row, OwnerUpdate)]
    leases = [row for row in events if isinstance(row, LeaseUpdate)]
    if len(receipts) != 1:
        return reject("receipt_count")
    receipt = receipts[0]
    if events[0] is not receipt:
        return reject("receipt_position")
    event_times = [int(row.event_time) for row in events]
    if any(timestamp >= int(decision_time) for timestamp in event_times):
        return reject("event_not_before_decision")
    if any(right <= left for left, right in zip(event_times, event_times[1:])):
        return reject("event_chronology")
    update_order = tuple(
        f"O{row.edge}" if isinstance(row, OwnerUpdate) else f"L{row.edge}"
        for row in events[1:]
    )
    if update_order not in INTERLEAVINGS:
        return reject("update_interleaving")
    if receipt.displayed_bit not in (0, 1):
        return reject("content")
    if not receipt.tag_ok:
        return reject("bad_tag")
    if not receipt.issuer_allowed:
        return reject("foreign_issuer")
    if len(owners) != 2 or sorted(row.edge for row in owners) != [1, 2]:
        return reject("owner_update_shape")
    tip = receipt.owner_anchor
    for row in owners:
        if row.from_version != tip:
            return reject("owner_chain")
        tip = row.to_version
    if tip != final_owner:
        return reject("owner_final")
    if len(leases) != 2 or sorted(row.edge for row in leases) != [1, 2]:
        return reject("lease_update_shape")
    tip = receipt.lease_anchor
    previous_until = receipt.valid_until
    for row in leases:
        if row.from_version != tip:
            return reject("lease_chain")
        if row.valid_from - previous_until > 0:
            return reject("coverage_gap")
        if row.valid_from != row.event_time or row.valid_until < row.valid_from:
            return reject("lease_interval")
        tip = row.to_version
        previous_until = row.valid_until
    if tip != final_lease:
        return reject("lease_final")
    if not (leases[-1].valid_from <= decision_time <= leases[-1].valid_until):
        return reject("final_coverage")
    return Verification(True, receipt.displayed_bit, None)


def verify(
    events: Sequence[object], *, final_owner: Version, final_lease: Version,
    decision_time: int = 0,
) -> Verification:
    """Public fail-closed boundary for both semantic and malformed inputs."""
    try:
        return _verify(
            events, final_owner=final_owner, final_lease=final_lease,
            decision_time=decision_time,
        )
    except (AttributeError, TypeError, ValueError, OverflowError):
        return reject("malformed_input")


def rule_dual(verification: Verification) -> Action:
    if not verification.live or verification.content is None:
        return Action.RESET
    return Action.USE_1 if verification.content else Action.USE_0


def verify_example(example: object) -> Verification:
    try:
        events = getattr(example, "events")
        final_owner = getattr(example, "final_owner")
        final_lease = getattr(example, "final_lease")
    except (AttributeError, TypeError, ValueError, OverflowError):
        return reject("malformed_input")
    return verify(events, final_owner=final_owner, final_lease=final_lease)
