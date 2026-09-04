from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .allocator import DUMMY


@dataclass(frozen=True)
class PhysicalOutcome:
    J: float
    Trec: int
    survivor_switch_fraction: float
    dummy_fraction: float
    service: list[list[float]]
    waste: list[list[float]]
    assignment: dict[str, int]

    def as_dict(self) -> dict:
        return {
            "J": self.J,
            "Trec": self.Trec,
            "survivor_switch_fraction": self.survivor_switch_fraction,
            "dummy_fraction": self.dummy_fraction,
            "service": self.service,
            "waste": self.waste,
            "assignment": self.assignment,
        }


def evaluate_physical(
    handles: Sequence[str], capacities: np.ndarray, demand: np.ndarray,
    previous_roles: Mapping[str, int], assignment: Mapping[str, int],
) -> PhysicalOutcome:
    if set(assignment) != set(handles):
        raise ValueError("physical action must address every active handle")
    service = np.zeros((3, 3), dtype=np.float64)
    waste = np.zeros((3, 3), dtype=np.float64)
    totals = np.zeros((3, 3), dtype=np.float64)
    survivor_switches = 0
    for row, handle in enumerate(handles):
        role = int(assignment[handle])
        if role not in (0, 1, 2, DUMMY):
            raise ValueError("invalid physical role")
        survived = handle in previous_roles
        if survived and role != int(previous_roles[handle]):
            survivor_switches += 1
        if role == DUMMY:
            continue
        switched = survived and role != int(previous_roles[handle])
        for tick in range(3):
            if not (switched and tick == 0):
                totals[tick, role] += capacities[row, role]
    ratio = totals / demand[None, :]
    service[:, :] = np.minimum(ratio, 1.0)
    waste[:, :] = np.minimum(np.maximum(ratio - 1.0, 0.0), 1.0)
    utility = service.mean(axis=1) - 0.10 * waste.mean(axis=1)
    trec = next((tick for tick in range(3) if bool(np.all(service[tick] >= 0.90))), 3)
    survivor_count = len(previous_roles)
    return PhysicalOutcome(
        J=float(utility.mean()),
        Trec=trec,
        survivor_switch_fraction=float(survivor_switches / survivor_count) if survivor_count else 0.0,
        dummy_fraction=float(sum(assignment[h] == DUMMY for h in handles) / len(handles)),
        service=service.tolist(), waste=waste.tolist(), assignment=dict(assignment),
    )
