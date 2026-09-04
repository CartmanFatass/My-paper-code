"""Deterministic TEST-only scripted controllers for TBCFV r04."""

from __future__ import annotations

from functools import lru_cache
from typing import Sequence

import numpy as np

SECTORS = 120
BEACONS = 6


def circular_distance(a: int, b: int) -> int:
    delta = abs(int(a) - int(b)) % SECTORS
    return min(delta, SECTORS - delta)


def angular_order(positions: Sequence[int], entry_tiebreak: Sequence[int] | None = None) -> tuple[int, ...]:
    """Current public angular rank; a tie-break never enters controller features."""

    positions_tuple = tuple(int(value) % SECTORS for value in positions)
    if entry_tiebreak is None:
        tie = tuple(range(len(positions_tuple)))
    else:
        tie = tuple(int(value) for value in entry_tiebreak)
        if len(tie) != len(positions_tuple) or len(set(tie)) != len(tie):
            raise ValueError("entry_tiebreak must be unique and align with positions")
    return tuple(sorted(range(len(positions_tuple)), key=lambda index: (positions_tuple[index], tie[index])))


def coherent_scaffold(
    positions: Sequence[int],
    beacon_positions: Sequence[int],
    demand: Sequence[int],
    *,
    previous_claims: Sequence[int] | None = None,
    survivor: Sequence[bool] | None = None,
    first_claim_or_new_epoch: bool = False,
    entry_tiebreak: Sequence[int] | None = None,
) -> np.ndarray:
    """Exact distance, survivor-change, then lexicographic assignment law."""

    positions_t = tuple(int(value) % SECTORS for value in positions)
    beacons_t = tuple(int(value) % SECTORS for value in beacon_positions)
    demand_t = tuple(int(value) for value in demand)
    n = len(positions_t)
    if len(beacons_t) != BEACONS or len(demand_t) != BEACONS:
        raise ValueError("exactly six beacon positions and six demands are required")
    if n < 1 or n > 12 or any(value < 0 for value in demand_t) or sum(demand_t) != n:
        raise ValueError("demand must be nonnegative, sum to N, and 1 <= N <= 12")
    order = angular_order(positions_t, entry_tiebreak)
    slots = tuple(beacon for beacon, count in enumerate(demand_t) for _ in range(count))

    if previous_claims is None:
        previous = tuple(-1 for _ in range(n))
    else:
        previous = tuple(int(value) for value in previous_claims)
        if len(previous) != n:
            raise ValueError("previous claims must align with current roster")
    if survivor is None:
        surviving = tuple(False for _ in range(n))
    else:
        surviving = tuple(bool(value) for value in survivor)
        if len(surviving) != n:
            raise ValueError("survivor flags must align with current roster")

    @lru_cache(maxsize=None)
    def solve(rank: int, used_mask: int) -> tuple[int, int, tuple[int, ...]]:
        if rank == n:
            return (0, 0, ())
        agent = order[rank]
        best: tuple[int, int, tuple[int, ...]] | None = None
        for slot_index, beacon in enumerate(slots):
            if used_mask & (1 << slot_index):
                continue
            tail_distance, tail_changes, tail_slots = solve(rank + 1, used_mask | (1 << slot_index))
            distance = circular_distance(positions_t[agent], beacons_t[beacon]) + tail_distance
            changed = int(
                not first_claim_or_new_epoch
                and surviving[agent]
                and previous[agent] >= 0
                and previous[agent] != beacon
            )
            candidate = (distance, changed + tail_changes, (slot_index,) + tail_slots)
            if best is None or candidate < best:
                best = candidate
        if best is None:
            raise RuntimeError("no complete coherent assignment")
        return best

    _, _, ranked_slot_indices = solve(0, 0)
    claims = np.empty(n, dtype=np.int64)
    for rank, slot_index in enumerate(ranked_slot_indices):
        claims[order[rank]] = slots[slot_index]
    return claims


def fragmented_scaffold(
    positions: Sequence[int],
    beacon_positions: Sequence[int],
    demand: Sequence[int],
    *,
    active_churn: bool,
    post_event_claim_index: int | None,
    previous_claims: Sequence[int] | None = None,
    survivor: Sequence[bool] | None = None,
    first_claim_or_new_epoch: bool = False,
    entry_tiebreak: Sequence[int] | None = None,
) -> np.ndarray:
    """Apply exactly the three-shortfall edit on post-event claim indices 0 and 1."""

    coherent = coherent_scaffold(
        positions,
        beacon_positions,
        demand,
        previous_claims=previous_claims,
        survivor=survivor,
        first_claim_or_new_epoch=first_claim_or_new_epoch,
        entry_tiebreak=entry_tiebreak,
    )
    if not active_churn or post_event_claim_index not in (0, 1):
        return coherent
    order = angular_order(positions, entry_tiebreak)
    fragmented = coherent.copy()
    for lower in (0, 2, 4):
        source = lower + 1
        claimant = next((index for index in order if coherent[index] == source), None)
        if claimant is None:
            raise ValueError(f"coherent assignment has no claimant for required beacon {source}")
        fragmented[claimant] = lower
    return fragmented


def independent_nearest(
    positions: Sequence[int],
    beacon_positions: Sequence[int],
) -> np.ndarray:
    """Nearest current beacon with lower-index resolution of exact ties."""

    beacons = tuple(int(value) % SECTORS for value in beacon_positions)
    if len(beacons) != BEACONS:
        raise ValueError("exactly six beacon positions are required")
    return np.asarray(
        [min(range(BEACONS), key=lambda beacon: (circular_distance(position, beacons[beacon]), beacon))
         for position in positions],
        dtype=np.int64,
    )

