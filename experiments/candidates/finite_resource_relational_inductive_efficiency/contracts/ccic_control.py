"""FRRIE-owned public arity-three CCIC absorption control."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable, Mapping

from .core import ContractError

CCIC_EDGES = ((0, 1), (0, 3), (0, 5), (0, 6), (1, 2), (2, 4), (3, 7), (4, 7), (5, 7), (6, 7))
CCIC_SIGNS_A = (1, 1, -1, -1, 1, 1, -1, -1)
CCIC_SIGNS_B = tuple(-value for value in CCIC_SIGNS_A)


def _graph(signs: Mapping[Any, int] | Iterable[int], edges: Iterable[tuple[Any, Any]]) -> tuple[dict[Any, int], dict[Any, set[Any]]]:
    sign_map = dict(signs) if isinstance(signs, Mapping) else dict(enumerate(signs))
    if not sign_map or any(value not in (-1, 1) for value in sign_map.values()):
        raise ContractError("CCIC public signs must be exactly +/-1")
    neighbors = {node: set() for node in sign_map}
    seen_edges: set[frozenset[Any]] = set()
    for edge in edges:
        if not isinstance(edge, (tuple, list)) or len(edge) != 2:
            raise ContractError("CCIC edges must be endpoint pairs")
        left, right = edge
        if left == right or left not in neighbors or right not in neighbors:
            raise ContractError("CCIC edge has an invalid endpoint")
        canonical = frozenset((left, right))
        if canonical in seen_edges:
            raise ContractError("CCIC duplicate undirected edge")
        seen_edges.add(canonical)
        neighbors[left].add(right)
        neighbors[right].add(left)
    return sign_map, neighbors


def typed_wedge_count(signs: Mapping[Any, int] | Iterable[int], edges: Iterable[tuple[Any, Any]]) -> int:
    """Count public (+,degree2)-center wedges with {(+4),(-2)} neighbors."""
    sign_map, neighbors = _graph(signs, edges)
    total = 0
    for center, adjacent in neighbors.items():
        if (sign_map[center], len(adjacent)) != (1, 2):
            continue
        for left, right in combinations(adjacent, 2):
            endpoint_types = {(sign_map[left], len(neighbors[left])), (sign_map[right], len(neighbors[right]))}
            total += endpoint_types == {(1, 4), (-1, 2)}
    return int(total)


def m3_signed_contraction(signs: Mapping[Any, int] | Iterable[int], edges: Iterable[tuple[Any, Any]]) -> int:
    sign_map, neighbors = _graph(signs, edges)
    total = 0
    for center, adjacent in neighbors.items():
        for left, right in combinations(adjacent, 2):
            total += (
                sign_map[center] * len(neighbors[left]) * len(neighbors[right])
                * sign_map[left] * sign_map[right]
            )
    return total


def canonical_ccic_fixture() -> dict[str, Any]:
    result = {
        "edges": [list(edge) for edge in CCIC_EDGES],
        "A": {"signs": list(CCIC_SIGNS_A)},
        "B": {"signs": list(CCIC_SIGNS_B)},
    }
    result["A"].update(wedge=typed_wedge_count(CCIC_SIGNS_A, CCIC_EDGES), m3=m3_signed_contraction(CCIC_SIGNS_A, CCIC_EDGES))
    result["B"].update(wedge=typed_wedge_count(CCIC_SIGNS_B, CCIC_EDGES), m3=m3_signed_contraction(CCIC_SIGNS_B, CCIC_EDGES))
    if (result["A"]["wedge"], result["B"]["wedge"], result["A"]["m3"], result["B"]["m3"]) != (1, 0, 12, -12):
        raise RuntimeError("CCIC fixture drift")
    return result
