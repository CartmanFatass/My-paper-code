"""Counter-keyed cooperative relay-coverage host for VNFC-B2."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Mapping, Sequence

import numpy as np

from .config import C0, C1, C2, C3, EVENT_CELLS, SEEN_SCHEDULES
from .lifecycle import Authority


IDLE, PROBE_ENTITY, PROBE_ROLE, SERVE_0, SERVE_1 = range(5)
ACTION_COUNT = 5


def counter_seed(*parts: object) -> int:
    payload = "\0".join(str(part) for part in ("VNFC-B2", *parts))
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big") % (2**63 - 1)


def rng_for(*parts: object) -> np.random.Generator:
    return np.random.default_rng(counter_seed(*parts))


@dataclass(frozen=True)
class PublicEvent:
    kind: str
    same_owner: bool
    owner_generation_continuity: bool
    same_public_role: bool
    lease_continuity: bool
    absence_age: int

    def numerical(self) -> tuple[float, ...]:
        kinds = ("NONE", "CHECKPOINT", "LEAVE", "RETURN", "REBIND", "REPLACE")
        return (
            *(float(self.kind == kind) for kind in kinds),
            float(self.same_owner), float(self.owner_generation_continuity),
            float(self.same_public_role), float(self.lease_continuity),
            min(self.absence_age, 3) / 3.0, 1.0,
        )


@dataclass(frozen=True)
class World:
    base_seed: int
    split: str
    world_index: int
    initial_n: int
    cell: str
    schedule: str
    leave_tick: int
    return_tick: int
    initial: tuple[Authority, ...]
    focal_index: int
    replacement: Authority | None
    entity_facts: Mapping[tuple[str, int], int]
    lease_facts: Mapping[tuple[str, int, int, int], int]
    phases: np.ndarray
    energy: Mapping[tuple[str, int], float]

    @property
    def focal(self) -> Authority:
        return self.initial[self.focal_index]

    def active(self, tick: int) -> tuple[Authority, ...]:
        if self.cell == C0 or tick < self.leave_tick:
            return self.initial
        others = tuple(a for index, a in enumerate(self.initial) if index != self.focal_index)
        if tick < self.return_tick:
            return others
        if self.cell == C1:
            old = self.focal
            returned = Authority(old.entity, old.owner_generation, old.membership_epoch + 1,
                                 old.role, old.lease_generation)
        elif self.cell == C2:
            old = self.focal
            returned = Authority(old.entity, old.owner_generation, old.membership_epoch + 1,
                                 1 - old.role, old.lease_generation + 1)
        elif self.cell == C3:
            if self.replacement is None:
                raise RuntimeError("replacement authority missing")
            returned = self.replacement
        else:
            raise ValueError(self.cell)
        return (*others, returned)

    def returned_authority(self) -> Authority:
        if self.cell == C0:
            return self.focal
        return self.active(self.return_tick)[-1]

    def event(self, tick: int, authority: Authority) -> PublicEvent:
        focal = self.focal
        if self.cell == C0 and tick == self.leave_tick:
            return PublicEvent("CHECKPOINT", True, True, True, True, 0)
        if self.cell != C0 and tick == self.leave_tick:
            return PublicEvent("LEAVE", True, True, True, True, 0)
        if self.cell != C0 and tick == self.return_tick:
            if self.cell == C1:
                return PublicEvent("RETURN", True, True, True, True,
                                   self.return_tick - self.leave_tick)
            if self.cell == C2:
                return PublicEvent("REBIND", True, True, False, False,
                                   self.return_tick - self.leave_tick)
            return PublicEvent("REPLACE", False, False, True, False,
                               self.return_tick - self.leave_tick)
        return PublicEvent("NONE", True, True, True, True, 0)

    def departing_event(self) -> PublicEvent:
        return PublicEvent("LEAVE", True, True, True, True, 0)

    def entity_fact(self, authority: Authority) -> int:
        return int(self.entity_facts[(authority.entity, authority.owner_generation)])

    def lease_fact(self, authority: Authority) -> int:
        return int(self.lease_facts[(authority.entity, authority.owner_generation,
                                    authority.role, authority.lease_generation)])

    def public_phase(self, role: int, tick: int) -> int:
        return int(self.phases[tick, role])

    def energy_cost(self, authority: Authority, tick: int) -> float:
        return float(self.energy[(authority.entity, tick)])


def make_world(
    base_seed: int, split: str, world_index: int, initial_n: int,
    cell: str, schedule: str,
) -> World:
    if cell not in EVENT_CELLS:
        raise ValueError(cell)
    schedules = dict(SEEN_SCHEDULES, **{"S*": (5, 8)})
    leave_tick, return_tick = schedules[schedule]
    generator = rng_for(base_seed, split, world_index, initial_n, cell, schedule)
    roles = [index % 2 for index in range(initial_n)]
    generator.shuffle(roles)
    counts = [roles.count(0), roles.count(1)]
    duplicated_roles = [role for role, count in enumerate(counts) if count >= 2]
    if not duplicated_roles:
        raise RuntimeError("world lacks duplicated role")
    focal_role = duplicated_roles[int(generator.integers(len(duplicated_roles)))]
    focal_candidates = [index for index, role in enumerate(roles) if role == focal_role]
    focal_index = focal_candidates[int(generator.integers(len(focal_candidates)))]
    initial = tuple(
        Authority(
            entity=f"entity-{counter_seed(base_seed, split, world_index, index, 'entity')}",
            owner_generation=1,
            membership_epoch=1,
            role=role,
            lease_generation=1,
        )
        for index, role in enumerate(roles)
    )
    focal = initial[focal_index]
    replacement = None
    if cell == C3:
        replacement = Authority(
            entity=f"replacement-{counter_seed(base_seed, split, world_index, 'replacement')}",
            owner_generation=2, membership_epoch=1,
            role=focal.role, lease_generation=2,
        )
    authorities = [*initial]
    if cell == C2:
        authorities.append(Authority(
            focal.entity, focal.owner_generation, focal.membership_epoch + 1,
            1 - focal.role, focal.lease_generation + 1,
        ))
    if replacement is not None:
        authorities.append(replacement)
    entity_facts: dict[tuple[str, int], int] = {}
    lease_facts: dict[tuple[str, int, int, int], int] = {}
    for authority in authorities:
        entity_facts.setdefault(
            (authority.entity, authority.owner_generation),
            int(rng_for(base_seed, split, world_index, authority.entity, "entity_fact").integers(2)),
        )
        lease_facts.setdefault(
            (authority.entity, authority.owner_generation,
             authority.role, authority.lease_generation),
            int(rng_for(base_seed, split, world_index, authority.entity,
                        authority.role, authority.lease_generation, "lease_fact").integers(2)),
        )
    phases = rng_for(base_seed, split, world_index, "phases").integers(0, 2, size=(12, 2))
    entity_names = {authority.entity for authority in authorities}
    energy = {
        (entity, tick): float(rng_for(base_seed, split, world_index, entity, tick, "energy").uniform(.01, .03))
        for entity in entity_names for tick in range(12)
    }
    return World(
        base_seed=base_seed, split=split, world_index=world_index,
        initial_n=initial_n, cell=cell, schedule=schedule,
        leave_tick=leave_tick, return_tick=return_tick, initial=initial,
        focal_index=focal_index, replacement=replacement,
        entity_facts=entity_facts, lease_facts=lease_facts,
        phases=phases, energy=energy,
    )


def row_order(active: Sequence[Authority], world: World, tick: int, replica: int) -> tuple[Authority, ...]:
    stable = tuple(sorted(active, key=lambda authority: (authority.entity, authority.owner_generation)))
    if replica == 0:
        return tuple(sorted(stable, key=lambda authority: (authority.role, authority.entity)))
    if replica == 1:
        return tuple(reversed(tuple(sorted(stable, key=lambda authority: (authority.role, authority.entity)))))
    values = list(stable)
    rng_for(world.base_seed, world.split, world.world_index, tick, replica, "row_order").shuffle(values)
    return tuple(values)


def shared_reward(world: World, tick: int, active: Sequence[Authority],
                  actions: Mapping[Authority, int]) -> dict[str, object]:
    correct = [0, 0]
    wrong = probes = 0
    service_energy = 0.0
    correct_by_authority: dict[Authority, int] = {}
    for authority in active:
        expected = world.entity_fact(authority) ^ world.lease_fact(authority) ^ world.public_phase(authority.role, tick)
        correct_by_authority[authority] = expected
        action = int(actions[authority])
        if action in (PROBE_ENTITY, PROBE_ROLE):
            probes += 1
        elif action in (SERVE_0, SERVE_1):
            service_energy += world.energy_cost(authority, tick)
            if action - SERVE_0 == expected:
                correct[authority.role] += 1
            else:
                wrong += 1
    duplicate = sum(max(count - 1, 0) for count in correct)
    reward = 0.5 * sum(count >= 1 for count in correct) - .25 * wrong - .05 * duplicate - .05 * probes - service_energy
    return {
        "reward": float(reward), "correct": correct, "wrong": wrong,
        "duplicate": duplicate, "probe": probes,
        "correct_command": correct_by_authority,
    }


def oracle_actions(world: World, tick: int, active: Sequence[Authority]) -> dict[Authority, int]:
    actions = {authority: IDLE for authority in active}
    for role in (0, 1):
        candidates = [authority for authority in active if authority.role == role]
        chosen = min(candidates, key=lambda authority: world.energy_cost(authority, tick))
        command = world.entity_fact(chosen) ^ world.lease_fact(chosen) ^ world.public_phase(role, tick)
        actions[chosen] = SERVE_0 + command
    return actions
