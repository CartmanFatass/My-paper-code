"""Identity-free rotating-beacon host and exact public encodings."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Mapping

import numpy as np

from . import rng
from .config import (
    BEACONS, CLAIM_PERIOD, EVENT_TICK, HORIZON, MAX_SPEED, SECTORS,
    SERVICE_RADIUS, beacon_positions, demands,
)


def circular_displacement(source: int, target: int) -> int:
    clockwise = (target - source) % SECTORS
    return clockwise if clockwise <= SECTORS // 2 else clockwise - SECTORS


def circular_distance(a: int, b: int) -> int:
    return abs(circular_displacement(a, b))


def sector_encoding(position: int) -> tuple[float, float]:
    angle = 2.0 * math.pi * position / SECTORS
    return math.sin(angle), math.cos(angle)


def claim_encoding(claim: int | None) -> tuple[float, float]:
    if claim is None:
        return 0.0, 0.0
    angle = 2.0 * math.pi * claim / BEACONS
    return math.sin(angle), math.cos(angle)


@dataclass
class EntityState:
    position: int
    previous_claim: int | None = None
    previous_displacement: int = 0
    newcomer: bool = False


@dataclass
class PublicState:
    tick: int
    roster_event: int
    post_boundary: int
    entities: dict[int, EntityState]
    tie_marks: dict[int, float]

    @property
    def n(self) -> int:
        return len(self.entities)

    @property
    def angular_order(self) -> tuple[int, ...]:
        return tuple(sorted(self.entities, key=lambda k: (
            self.entities[k].position, self.tie_marks[k]
        )))

    def clone(self) -> "PublicState":
        return PublicState(
            self.tick, self.roster_event, self.post_boundary,
            {k: EntityState(v.position, v.previous_claim,
                            v.previous_displacement, v.newcomer)
             for k, v in self.entities.items()},
            dict(self.tie_marks),
        )

    def canonical_bytes(self) -> bytes:
        # Internal keys anchor state evolution but are deliberately excluded.
        rows = []
        for rank, key in enumerate(self.angular_order):
            e = self.entities[key]
            rows.append([rank, e.position, e.previous_claim,
                         e.previous_displacement, int(e.newcomer),
                         self.tie_marks[key]])
        value = {
            "tick": self.tick, "roster_event": self.roster_event,
            "post_boundary": self.post_boundary, "agents": rows,
            "beacons": beacon_positions(self.tick),
            "demands": demands(self.n, self.tick),
            "future_claim_law": [
                [future, beacon_positions(future), demands(self.n, future)]
                for future in range(self.tick, HORIZON, CLAIM_PERIOD)
            ],
        }
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")

    def agent_elements(self) -> np.ndarray:
        rows = []
        for key in self.angular_order:
            e = self.entities[key]
            rows.append((*sector_encoding(e.position),
                         *claim_encoding(e.previous_claim),
                         float(e.newcomer), 2.0 * self.tie_marks[key] - 1.0))
        return np.asarray(rows, dtype=np.float64)

    def own_features(self, key: int) -> np.ndarray:
        e = self.entities[key]
        rank = self.angular_order.index(key)
        return np.asarray((
            *sector_encoding(e.position),
            rank / max(self.n - 1, 1),
            e.previous_displacement / 3.0,
            float(e.newcomer),
            *claim_encoding(e.previous_claim),
            2.0 * self.tie_marks[key] - 1.0,
        ), dtype=np.float64)


def initial_entities(root: int, cell: tuple[int, int], scenario: int,
                     phase: str) -> dict[int, EntityState]:
    label = rng.root_label(root)
    n = cell[0]
    positions = rng.ordered_without_replacement(
        range(SECTORS), n, label, "common", phase, "cell", *cell,
        "scenario", scenario, "initial-position")
    return {key: EntityState(pos) for key, pos in enumerate(positions)}


def mutate_entities(entities: dict[int, EntityState], target_n: int, root: int,
                    cell: tuple[int, int], scenario: int, phase: str) -> None:
    label = rng.root_label(root)
    current = len(entities)
    common = (label, "common", phase, "cell", *cell, "scenario", scenario,
              "event-mutation")
    if target_n < current:
        remove = rng.ordered_without_replacement(entities, current - target_n,
                                                 *common, "departure")
        for key in remove:
            del entities[key]
    elif target_n > current:
        occupied = {e.position for e in entities.values()}
        positions = rng.ordered_without_replacement(
            (x for x in range(SECTORS) if x not in occupied), target_n - current,
            *common, "arrival-position")
        next_key = max(entities, default=-1) + 1
        for offset, pos in enumerate(positions):
            entities[next_key + offset] = EntityState(pos, None, 0, True)


def tie_marks(entities: Mapping[int, EntityState], root: int,
              cell: tuple[int, int], scenario: int, tick: int,
              phase: str) -> dict[int, float]:
    label = rng.root_label(root)
    return {key: rng.uniform(label, "common", phase, "cell", *cell,
                             "scenario", scenario, "tick", tick,
                             "entity", key, "public-tie-mark")
            for key in entities}


def construct_public_state(entities: dict[int, EntityState], tick: int,
                           churn: bool, root: int, cell: tuple[int, int],
                           scenario: int, phase: str) -> PublicState:
    return PublicState(
        tick=tick,
        roster_event=int(churn and tick == EVENT_TICK),
        post_boundary=int(tick >= EVENT_TICK),
        entities=entities,
        tie_marks=tie_marks(entities, root, cell, scenario, tick, phase),
    )


def move_once(entities: dict[int, EntityState], claims: Mapping[int, int],
              tick: int) -> None:
    beacons = beacon_positions(tick)
    for key, entity in entities.items():
        delta = circular_displacement(entity.position, beacons[claims[key]])
        displacement = max(-MAX_SPEED, min(MAX_SPEED, delta))
        entity.position = (entity.position + displacement) % SECTORS
        entity.previous_displacement = displacement


def unserved(entities: Mapping[int, EntityState], tick: int) -> float:
    qs = beacon_positions(tick)
    ds = demands(len(entities), tick)
    coverage = [sum(circular_distance(e.position, q) <= SERVICE_RADIUS
                    for e in entities.values()) for q in qs]
    return sum(max(ds[j] - coverage[j], 0) for j in range(BEACONS)) / len(entities)


def fragmentation(claims: Mapping[int, int], n: int, tick: int) -> float:
    ds = demands(n, tick)
    counts = [sum(value == j for value in claims.values()) for j in range(BEACONS)]
    return sum(max(ds[j] - counts[j], 0) for j in range(BEACONS)) / n


def service_delay(position: int, beacon: int, claim_tick: int) -> int:
    delay = 0
    current = position
    for tick in range(claim_tick, min(claim_tick + CLAIM_PERIOD, HORIZON)):
        target = beacon_positions(tick)[beacon]
        delta = circular_displacement(current, target)
        current = (current + max(-MAX_SPEED, min(MAX_SPEED, delta))) % SECTORS
        delay += int(circular_distance(current, target) > SERVICE_RADIUS)
    return delay


def endpoints(unserved_values: list[float], fragments: list[float]) -> dict[str, float]:
    post = unserved_values[EVENT_TICK:]
    tau = 36.0
    for h in range(34):
        if post[h] == post[h + 1] == post[h + 2] == 0.0:
            tau = float(h)
            break
    return {
        "tau": tau,
        "U": float(sum(post) / 36.0),
        "F": float(sum(fragments) / len(fragments)),
        "Y": float(1.0 - sum(unserved_values) / HORIZON),
    }
