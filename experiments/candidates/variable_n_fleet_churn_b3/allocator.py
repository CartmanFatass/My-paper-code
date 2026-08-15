from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil, log2
import struct
import sys
from typing import Mapping, Sequence

import numpy as np

DUMMY = 3


@dataclass(frozen=True, slots=True)
class Edge:
    agent: int
    task: int
    key: float
    tie_rank: int


@dataclass(slots=True)
class AllocationCounters:
    n: int
    free_agents: int
    edges: int = 0
    edge_key_evaluations: int = 0
    heap_build_records: int = 0
    heap_pops: int = 0
    heap_key_comparisons: int = 0
    residual_updates: int = 0
    peak_live_edge_records: int = 0
    peak_live_edge_machine_words: int = 0
    dynamic_edge_insertions: int = 0
    surviving_edge_rekeys: int = 0
    repeated_all_edge_passes: int = 0
    heap_builds: int = 0
    exact_searches: int = 0
    beam_tree_searches: int = 0
    nxn_allocator_object: bool = False
    nxn_learned_object: bool = False
    exact_fallbacks: int = 0
    trajectory_rollouts: int = 0

    def guards(self) -> dict[str, bool]:
        e = self.edges
        comparison_limit = 8 * e * ceil(log2(max(e, 2)))
        return {
            "edges_le_3n": e <= 3 * self.n,
            "edges_le_3u": e <= 3 * self.free_agents,
            "key_evaluations_equal_edges": self.edge_key_evaluations == e,
            "heap_build_records_equal_edges": self.heap_build_records == e,
            "heap_built_exactly_once": self.heap_builds == 1,
            "heap_pops_equal_edges": self.heap_pops == e,
            "heap_comparisons_within_bound": self.heap_key_comparisons <= comparison_limit,
            "residual_updates_le_n": self.residual_updates <= self.n,
            "live_edges_le_3n": self.peak_live_edge_records <= 3 * self.n,
            "no_dynamic_insertions": self.dynamic_edge_insertions == 0,
            "no_rekeys": self.surviving_edge_rekeys == 0,
            "no_rescans": self.repeated_all_edge_passes == 0,
            "no_nxn_object": not (self.nxn_allocator_object or self.nxn_learned_object),
            "no_exact_fallback": self.exact_fallbacks == 0,
            "no_exact_search": self.exact_searches == 0,
            "no_beam_tree_search": self.beam_tree_searches == 0,
            "no_trajectory_search": self.trajectory_rollouts == 0,
        }

    def checked(self) -> dict:
        guards = self.guards()
        if not all(guards.values()):
            failed = [name for name, ok in guards.items() if not ok]
            raise RuntimeError(f"SP-RDA complexity guard failed: {failed}")
        return {**asdict(self), "guards": guards}


class _MaxHeap:
    """One-shot Floyd heap with explicit immutable-record comparison accounting."""

    def __init__(self, records: list[Edge], counters: AllocationCounters):
        self.data = records
        self.counters = counters
        counters.heap_build_records = len(records)
        counters.heap_builds = 1
        counters.peak_live_edge_records = len(records)
        word = struct.calcsize("P")
        edge_bytes = sys.getsizeof(records)
        for record in records:
            edge_bytes += sys.getsizeof(record)
            edge_bytes += sys.getsizeof(record.agent) + sys.getsizeof(record.task)
            edge_bytes += sys.getsizeof(record.key) + sys.getsizeof(record.tie_rank)
        counters.peak_live_edge_machine_words = ceil(edge_bytes / word)
        for parent in range(len(records) // 2 - 1, -1, -1):
            self._sift_down(parent)

    def _better(self, left: Edge, right: Edge) -> bool:
        self.counters.heap_key_comparisons += 1
        if left.key != right.key:
            return left.key > right.key
        if left.task != right.task:
            return left.task < right.task
        return left.tie_rank < right.tie_rank

    def _sift_down(self, root: int) -> None:
        size = len(self.data)
        while True:
            child = 2 * root + 1
            if child >= size:
                return
            if child + 1 < size and self._better(self.data[child + 1], self.data[child]):
                child += 1
            if not self._better(self.data[child], self.data[root]):
                return
            self.data[root], self.data[child] = self.data[child], self.data[root]
            root = child

    def pop(self) -> Edge:
        self.counters.heap_pops += 1
        root = self.data[0]
        tail = self.data.pop()
        if self.data:
            self.data[0] = tail
            self._sift_down(0)
        return root

    def __bool__(self) -> bool:
        return bool(self.data)


def zero_bids(capacities: np.ndarray, demand: np.ndarray) -> np.ndarray:
    del demand
    return np.zeros_like(capacities, dtype=np.float64)


def frozen_bids(capacities: np.ndarray, demand: np.ndarray) -> np.ndarray:
    values = np.clip(capacities / (demand[None, :] + 1e-6), 0.0, 1.0)
    out = np.empty_like(values)
    for task in range(3):
        alternatives = np.delete(values, task, axis=1)
        out[:, task] = values[:, task] - alternatives.max(axis=1)
    return out


def handoff_bids(
    handles: Sequence[str], capacities: np.ndarray, demand: np.ndarray,
    previous_roles: Mapping[str, int], new_handles: set[str] | frozenset[str],
) -> np.ndarray:
    """Registered three-tick history/handoff-aware fixed priority."""
    eta = np.full_like(capacities, 2.0 / 3.0, dtype=np.float64)
    for row, handle in enumerate(handles):
        if handle in new_handles:
            eta[row, :] = 1.0
        elif handle in previous_roles and int(previous_roles[handle]) in (0, 1, 2):
            eta[row, int(previous_roles[handle])] = 1.0
    values = np.clip(eta * capacities / (demand[None, :] + 1e-6), 0.0, 1.0)
    out = np.empty_like(values)
    for task in range(3):
        out[:, task] = values[:, task] - np.delete(values, task, axis=1).max(axis=1)
    return out


def sp_rda(
    handles: Sequence[str],
    capacities: np.ndarray,
    demand: np.ndarray,
    bids: np.ndarray,
    tie_ranks: Mapping[str, int],
    leased_roles: Mapping[str, int] | None = None,
    *,
    learned_nxn_object: bool = False,
) -> tuple[dict[str, int], dict]:
    """Allocate from immutable entry keys and pop every heap record exactly once."""
    n = len(handles)
    if capacities.shape != (n, 3) or bids.shape != (n, 3) or demand.shape != (3,):
        raise ValueError("SP-RDA expects capacities/bids [N,3] and demand [3]")
    if not np.isfinite(capacities).all() or not np.isfinite(bids).all() or not np.isfinite(demand).all():
        raise ValueError("non-finite allocator input")
    if np.any(capacities < 0) or np.any(demand <= 0) or np.any(bids < -1.000001) or np.any(bids > 1.000001):
        raise ValueError("allocator input outside registered bounds")
    leased_roles = dict(leased_roles or {})
    handle_to_row = {handle: row for row, handle in enumerate(handles)}
    if len(handle_to_row) != n or set(tie_ranks) != set(handles):
        raise ValueError("handles and stable tie ranks must be one-to-one")
    assignment: dict[str, int] = {}
    leased_mass = np.zeros(3, dtype=np.float64)
    for handle, role in leased_roles.items():
        if handle not in handle_to_row or role not in (0, 1, 2):
            raise ValueError("invalid lease")
        assignment[handle] = role
        leased_mass[role] += capacities[handle_to_row[handle], role]
    free = [row for row, handle in enumerate(handles) if handle not in leased_roles]
    counters = AllocationCounters(n=n, free_agents=len(free), nxn_learned_object=learned_nxn_object)
    delta0 = np.maximum(demand - leased_mass, 0.0)
    freecap0 = capacities[free].sum(axis=0) if free else np.zeros(3)
    lambda0 = np.clip(delta0 / (freecap0 + 1e-6), 0.0, 1.0)
    records: list[Edge] = []
    for row in free:  # sole candidate-edge pass
        for task in range(3):
            capacity = float(capacities[row, task])
            if capacity > 0.0 and delta0[task] > 0.0:
                fill0 = min(capacity, float(delta0[task])) / (float(delta0[task]) + 1e-6)
                key = float(bids[row, task]) + float(lambda0[task]) * fill0
                records.append(Edge(row, task, key, int(tie_ranks[handles[row]])))
    counters.edges = len(records)
    counters.edge_key_evaluations = len(records)
    heap = _MaxHeap(records, counters)
    delta = delta0.copy()
    assigned_rows = set(handle_to_row[h] for h in leased_roles)
    while heap:  # deliberately exhaust: no early exit after residuals become zero
        edge = heap.pop()
        if edge.agent not in assigned_rows and delta[edge.task] > 0.0:
            assignment[handles[edge.agent]] = edge.task
            assigned_rows.add(edge.agent)
            delta[edge.task] = max(float(delta[edge.task]) - float(capacities[edge.agent, edge.task]), 0.0)
            counters.residual_updates += 1
    for row, handle in enumerate(handles):
        assignment.setdefault(handle, DUMMY)
    if len(assignment) != n:
        raise RuntimeError("allocator failed total action addressability")
    return assignment, counters.checked()
