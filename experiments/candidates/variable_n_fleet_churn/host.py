"""Deterministic Churned Capability Matching host for VNFC-B1.

World generation is arm-independent and counter-keyed.  Opaque integer handles
exist only in the host; policies receive row features with no handle encoding.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
from typing import Iterable, Sequence

import numpy as np


CAPACITY_NORMALIZED = "CAPACITY_NORMALIZED"
TRUE_EXPANSION = "TRUE_EXPANSION"
REGIMES = (CAPACITY_NORMALIZED, TRUE_EXPANSION)
RESET = "RESET"
JOIN = "JOIN"
DROP = "DROP"
STATIC = "STATIC"
EVENT_KINDS = (RESET, JOIN, DROP)

TRAIN_SCHEDULES = (
    (3, 5, 3), (3, 5, 7), (5, 3, 5),
    (5, 7, 5), (7, 5, 3), (7, 5, 7),
)
CHURN_SCHEDULES = (
    (4, 3, 4), (4, 5, 4), (6, 5, 6),
    (6, 7, 6), (4, 6, 4), (6, 4, 6),
)
ROLE_COUNT = 4
TASK_COUNT = 3
DEMAND_VALUES = (0.55, 0.65, 0.75)


def _seed(*parts: object) -> int:
    payload = "\0".join(str(part) for part in ("VNFC-B1", *parts))
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def rng_for(*parts: object) -> np.random.Generator:
    return np.random.default_rng(_seed(*parts))


def counter_seed(*parts: object) -> int:
    """Return a stable positive 63-bit seed for non-NumPy namespaces."""
    return _seed(*parts) % (2**63 - 1)


@dataclass(frozen=True)
class World:
    base_seed: int
    split: str
    world_index: int
    regime: str
    sequence: tuple[int, int, int]
    rosters: tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]
    raw_capabilities: dict[int, tuple[float, float, float]]
    specialties: dict[int, int]
    demands: tuple[float, float, float]
    static: bool = False

    def event_kind(self, segment: int) -> str:
        if segment == 0:
            return RESET
        before = len(self.rosters[segment - 1])
        after = len(self.rosters[segment])
        if after > before:
            return JOIN
        if after < before:
            return DROP
        return STATIC

    def capacities(self, segment: int) -> dict[int, np.ndarray]:
        roster = self.rosters[segment]
        raw = np.asarray([self.raw_capabilities[handle] for handle in roster], dtype=np.float32)
        demands = np.asarray(self.demands, dtype=np.float32)
        if self.regime == CAPACITY_NORMALIZED:
            cap = 1.35 * demands[None, :] * raw / raw.sum(axis=0, keepdims=True)
        elif self.regime == TRUE_EXPANSION:
            cap = 0.42 * raw
        else:
            raise ValueError(f"unknown regime: {self.regime}")
        return {handle: cap[index] for index, handle in enumerate(roster)}


def _balanced_specialties(generator: np.random.Generator, count: int) -> list[int]:
    values: list[int] = []
    while len(values) < count:
        values.extend(int(value) for value in generator.permutation(TASK_COUNT))
    return values[:count]


def _covers(handles: Iterable[int], specialties: dict[int, int]) -> bool:
    return {specialties[handle] for handle in handles} == {0, 1, 2}


def _uniform_legal_subset(
    generator: np.random.Generator,
    candidates: Sequence[int],
    size: int,
    specialties: dict[int, int],
    *,
    required_union: Sequence[int] = (),
) -> tuple[int, ...]:
    legal = [
        tuple(combo)
        for combo in itertools.combinations(candidates, size)
        if _covers((*required_union, *combo), specialties)
    ]
    if not legal:
        raise RuntimeError("generator produced no specialty-covering roster")
    return legal[int(generator.integers(len(legal)))]


def _make_world(
    *,
    base_seed: int,
    split: str,
    world_index: int,
    regime: str,
    sequence: tuple[int, int, int],
    forced_initial: tuple[int, ...] | None = None,
    static: bool = False,
) -> World:
    generator = rng_for(base_seed, split, world_index, regime, "world")
    pool_size = max(sequence) + sum(max(0, sequence[i] - sequence[i - 1]) for i in (1, 2)) + 9
    handles = tuple(range(pool_size))
    specialty_values = _balanced_specialties(
        rng_for(base_seed, split, world_index, regime, "specialties"), pool_size
    )
    specialties = dict(zip(handles, specialty_values))
    raw_capabilities: dict[int, tuple[float, float, float]] = {}
    for handle in handles:
        capability_rng = rng_for(base_seed, split, world_index, regime, handle, "capability")
        specialty = specialties[handle]
        row = capability_rng.uniform(0.15, 0.45, size=TASK_COUNT)
        row[specialty] = capability_rng.uniform(0.80, 1.00)
        raw_capabilities[handle] = tuple(float(value) for value in row)
    demands = tuple(
        float(value)
        for value in rng_for(base_seed, split, world_index, regime, "demand").permutation(DEMAND_VALUES)
    )

    if forced_initial is None:
        initial = _uniform_legal_subset(generator, handles, sequence[0], specialties)
    else:
        initial = tuple(forced_initial)
    rosters: list[tuple[int, ...]] = [initial]
    used = set(initial)
    for segment in (1, 2):
        previous = rosters[-1]
        target_n = sequence[segment]
        if target_n > len(previous):
            add_count = target_n - len(previous)
            available = tuple(handle for handle in handles if handle not in used)
            added = _uniform_legal_subset(
                generator, available, add_count, specialties, required_union=previous
            )
            used.update(added)
            current = tuple((*previous, *added))
        elif target_n < len(previous):
            current = _uniform_legal_subset(generator, previous, target_n, specialties)
        else:
            current = previous
        rosters.append(current)

    return World(
        base_seed=base_seed,
        split=split,
        world_index=world_index,
        regime=regime,
        sequence=sequence,
        rosters=(rosters[0], rosters[1], rosters[2]),
        raw_capabilities=raw_capabilities,
        specialties=specialties,
        demands=demands,
        static=static,
    )


def _schedule_regime(index: int, base_seed: int, split: str) -> tuple[tuple[int, int, int], str]:
    block, offset = divmod(index, 12)
    cells = [(schedule, regime) for schedule in TRAIN_SCHEDULES for regime in REGIMES]
    order = rng_for(base_seed, split, block, "cell_order").permutation(len(cells))
    return cells[int(order[offset])]


def training_world(base_seed: int, episode_index: int) -> World:
    schedule, regime = _schedule_regime(episode_index, base_seed, "train")
    return _make_world(
        base_seed=base_seed, split="train", world_index=episode_index,
        regime=regime, sequence=schedule,
    )


def validation_world(base_seed: int, episode_index: int) -> World:
    schedule, regime = _schedule_regime(episode_index, base_seed, "validation")
    return _make_world(
        base_seed=base_seed, split="validation", world_index=episode_index,
        regime=regime, sequence=schedule,
    )


def static_pair(base_seed: int, regime: str, pair_index: int) -> tuple[World, World]:
    """Return nested N=4/N=6 static worlds with identical first four agents."""
    split = "test_static"
    # Select six agents jointly.  Cycling the two additions balances their
    # specialty pairs across the 48 paired pools in each regime.
    prototype = _make_world(
        base_seed=base_seed, split=split, world_index=pair_index,
        regime=regime, sequence=(6, 6, 6), static=True,
    )
    generator = rng_for(base_seed, split, pair_index, regime, "nested")
    handles = tuple(prototype.raw_capabilities)
    desired_pair = ((0, 1), (1, 2), (2, 0))[pair_index % 3]
    legal_added = [
        tuple(pair) for pair in itertools.combinations(handles, 2)
        if tuple(sorted(prototype.specialties[h] for h in pair)) == tuple(sorted(desired_pair))
    ]
    if not legal_added:
        raise RuntimeError("unable to construct nested static pair")
    added = legal_added[int(generator.integers(len(legal_added)))]
    remaining = tuple(handle for handle in handles if handle not in added)
    four = _uniform_legal_subset(generator, remaining, 4, prototype.specialties)
    six = (*four, *added)
    shared = dict(
        base_seed=base_seed,
        split=split,
        world_index=pair_index,
        regime=regime,
        raw_capabilities=prototype.raw_capabilities,
        specialties=prototype.specialties,
        demands=prototype.demands,
        static=True,
    )
    world4 = World(sequence=(4, 4, 4), rosters=(four, four, four), **shared)
    world6 = World(sequence=(6, 6, 6), rosters=(six, six, six), **shared)
    return world4, world6


def churn_world(base_seed: int, regime: str, sequence_index: int, world_index: int) -> World:
    sequence = CHURN_SCHEDULES[sequence_index]
    return _make_world(
        base_seed=base_seed,
        split=f"test_churn_{sequence_index}",
        world_index=world_index,
        regime=regime,
        sequence=sequence,
    )


def row_order(
    roster: Sequence[int], base_seed: int, split: str, world_index: int,
    regime: str, segment: int, replica: int,
) -> tuple[int, ...]:
    stable = tuple(sorted(roster))
    if replica == 0:
        return stable
    if replica == 1:
        return tuple(reversed(stable))
    values = list(stable)
    rng_for(base_seed, split, world_index, regime, segment, replica, "row_order").shuffle(values)
    return tuple(values)


def allocation_metrics(
    roster: Sequence[int], capacities: dict[int, np.ndarray], demands: Sequence[float],
    assignment: dict[int, int], previous: dict[int, int] | None,
) -> dict[str, object]:
    demand = np.asarray(demands, dtype=np.float64)
    x = np.zeros(TASK_COUNT, dtype=np.float64)
    for handle in roster:
        role = assignment[handle]
        if role < TASK_COUNT:
            x[role] += float(capacities[handle][role]) / demand[role]
    service = np.minimum(x, 1.0)
    waste = np.minimum(np.maximum(x - 1.0, 0.0), 1.0)
    survivors = tuple(handle for handle in roster if previous is not None and handle in previous)
    switch = (
        sum(assignment[handle] != previous[handle] for handle in survivors) / len(survivors)
        if survivors else 0.0
    )
    reward = float(service.mean() - 0.10 * waste.mean() - 0.04 * switch)
    return {
        "x": x.tolist(), "service": service.tolist(), "waste": waste.tolist(),
        "switch": float(switch), "reward": reward,
    }


def changed_set_stratum(world: World, segment: int) -> str:
    if segment == 0:
        return "reset"
    previous = set(world.rosters[segment - 1])
    current = set(world.rosters[segment])
    changed = previous - current if len(current) < len(previous) else current - previous
    before = world.rosters[segment - 1]
    critical = {
        max(before, key=lambda handle, task=task: world.raw_capabilities[handle][task])
        for task in range(TASK_COUNT)
    }
    if len(current) < len(previous):
        return "critical_drop" if changed & critical else "benign_drop"
    # Join relief is diagnosed when at least one joiner is the strongest active
    # raw-capability agent for a task after the event.
    after_critical = {
        max(current, key=lambda handle, task=task: world.raw_capabilities[handle][task])
        for task in range(TASK_COUNT)
    }
    return "relief_join" if changed & after_critical else "neutral_join"
