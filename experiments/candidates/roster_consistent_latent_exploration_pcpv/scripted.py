"""Registered public scripted policies and Stage-A episode rollout."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Mapping

from .config import CLAIM_PERIOD, EVENT_TICK, HORIZON, beacon_positions, demands
from .host import (
    EntityState, PublicState, circular_distance, construct_public_state,
    endpoints, fragmentation, initial_entities, move_once, mutate_entities,
    service_delay, unserved,
)


def coherent_claims(state: PublicState, priority: str) -> dict[int, int]:
    """Exact-demand assignment with literal CARRY or REPLAN priority."""
    if priority not in {"CARRY", "REPLAN"}:
        raise ValueError(priority)
    order = state.angular_order
    target = demands(state.n, state.tick)
    change = [[int(state.entities[key].previous_claim is not None and
                   state.entities[key].previous_claim != j)
               for j in range(4)] for key in order]
    delay = [[service_delay(state.entities[key].position, j, state.tick)
              for j in range(4)] for key in order]

    @lru_cache(None)
    def solve(index: int, remaining: tuple[int, int, int, int]):
        if index == len(order):
            return (0, 0, ())
        best = None
        for beacon in range(4):
            if remaining[beacon] == 0:
                continue
            rest = list(remaining)
            rest[beacon] -= 1
            child = solve(index + 1, tuple(rest))
            candidate = (change[index][beacon] + child[0],
                         delay[index][beacon] + child[1],
                         (beacon,) + child[2])
            key = candidate if priority == "CARRY" else (
                candidate[1], candidate[0], candidate[2])
            if best is None or key < best[0]:
                best = (key, candidate)
        assert best is not None
        return best[1]

    assignment = solve(0, target)[2]
    return dict(zip(order, assignment))


def nearest_claims(state: PublicState) -> dict[int, int]:
    qs = beacon_positions(state.tick)
    return {key: min(range(4), key=lambda j: (circular_distance(entity.position,
                                                                  qs[j]), j))
            for key, entity in state.entities.items()}


def fragmented_claims(state: PublicState, churn: bool) -> dict[int, int]:
    claims = coherent_claims(state, "CARRY")
    if churn and state.tick in (EVENT_TICK, EVENT_TICK + CLAIM_PERIOD):
        for source, destination in ((1, 0), (3, 2)):
            key = next(k for k in state.angular_order if claims[k] == source)
            claims[key] = destination
    return claims


def claims_for(package: str, state: PublicState, churn: bool) -> dict[int, int]:
    if package == "NEAREST":
        return nearest_claims(state)
    if package == "FRAGMENTED":
        return fragmented_claims(state, churn)
    if package == "REPLAN" and state.tick >= EVENT_TICK:
        return coherent_claims(state, "REPLAN")
    return coherent_claims(state, "CARRY")


def run_scripted_episode(package: str, root: int, cell: tuple[int, int],
                         scenario: int) -> tuple[dict[str, float], str | None]:
    phase = "stage-a"
    churn = cell[0] != cell[1]
    entities = initial_entities(root, cell, scenario, phase)
    u_values: list[float] = []
    f_values: list[float] = []
    event_hash = None
    claims: dict[int, int] = {}
    for tick in range(HORIZON):
        if tick % CLAIM_PERIOD == 0:
            if tick == EVENT_TICK and churn:
                mutate_entities(entities, cell[1], root, cell, scenario, phase)
            state = construct_public_state(entities, tick, churn, root, cell,
                                           scenario, phase)
            if tick == EVENT_TICK and package in {"CARRY", "REPLAN"}:
                event_hash = hashlib.sha256(state.canonical_bytes()).hexdigest()
            claims = claims_for(package, state, churn)
            if tick >= EVENT_TICK:
                f_values.append(fragmentation(claims, len(entities), tick))
            for key, entity in entities.items():
                entity.previous_claim = claims[key]
                entity.newcomer = False
        move_once(entities, claims, tick)
        u_values.append(unserved(entities, tick))
    return endpoints(u_values, f_values), event_hash
