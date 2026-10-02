"""Source-identical four Raw8 selection primitives from B01 61a2dfa9cde0.
Original complete file SHA256 71c5eb1d904370cbb853ce1cbfbde652391bb78b25b3a42c4ecebaeb653d82fe.
Only source_index is used by B04; canonical coordinates are never executed.
"""
from __future__ import annotations
import hashlib
import math
from typing import Any
KINDS = ("kmeans_plain", "subset_relay", "subset_flat")
AREA, MAX_MENU = 5000, 8

def rows(value: Any, n: int, width: int) -> list[list[float]]:
    if len(value) != n or any(len(row) != width for row in value):
        raise ValueError(f"expected {n} x {width} coordinates")
    result = []
    for row in value:
        if any(isinstance(x, bool) for x in row):
            raise ValueError("boolean coordinate")
        converted = [float(x) for x in row]
        if not all(math.isfinite(x) for x in converted):
            raise ValueError("non-finite coordinate")
        result.append([0.0 if x == 0 else x for x in converted])
    return result

def canonical_layout(value: Any) -> list[list[float]]:
    return sorted(rows(value, 6, 3))

def layout_bytes(value: Any) -> bytes:
    """The frozen tie/dedup key: numerically sorted XYZ rows, .17g decimal triples."""
    return ("\n".join(",".join(format(x, ".17g") for x in row)
                      for row in canonical_layout(value)) + "\n").encode("ascii")

def select_menu(raw: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Choose preferred slots, canonical dedupe, then fill holes relay/flat/plain.

    The source build_candidates has already applied its own rounded, row-sensitive
    dedupe. This layer adds the reviewed exact, row-insensitive dedupe; it does not
    modify that imported generator or insert any scored planner layout.
    """
    pool = []
    for index, candidate in enumerate(raw):
        kind, k = candidate["kind"], int(candidate["k"])
        if kind not in KINDS or k not in (4, 5, 6):
            raise ValueError("unexpected raw candidate metadata")
        xyz = canonical_layout(candidate["positions_xyz"])
        if any(not (0 <= x <= AREA and 0 <= y <= AREA and 50 <= z <= 150)
               for x, y, z in xyz):
            raise ValueError("illegal raw layout")
        key = layout_bytes(xyz)
        pool.append({"kind": kind, "k": k, "positions_xyz": xyz,
                     "source_index": int(candidate.get("index", index)),
                     "served": list(candidate.get("served", [])),
                     "layout_sha256": hashlib.sha256(key).hexdigest(), "_key": key})
    def rank(c):
        return (-len(c["served"]), c["layout_sha256"], c["source_index"])
    def first(kind, k=None, excluded=()):
        return next(iter(sorted((c for c in pool if c["kind"] == kind
                                 and (k is None or c["k"] == k)
                                 and c["_key"] not in excluded), key=rank)), None)
    preferred = [first("kmeans_plain", k) for k in (4, 5, 6)]
    preferred += [first("subset_relay", k) for k in (4, 5, 6)]
    relay_keys = {c["_key"] for c in preferred[3:] if c is not None}
    preferred += [first("subset_relay", excluded=relay_keys), first("subset_flat")]
    selected, seen, dropped = {}, set(), []
    for slot, c in enumerate(preferred):
        if c is None:
            continue
        if c["_key"] in seen:
            dropped.append({"construction_slot": slot, "layout_sha256": c["layout_sha256"]})
        else:
            selected[slot] = (c, "preferred")
            seen.add(c["_key"])
    fill = [c for kind in ("subset_relay", "subset_flat", "kmeans_plain")
            for c in sorted((c for c in pool if c["kind"] == kind), key=rank)]
    for slot in range(MAX_MENU):
        if slot in selected:
            continue
        c = next((c for c in fill if c["_key"] not in seen), None)
        if c is not None:
            selected[slot] = (c, "fill")
            seen.add(c["_key"])
    if not selected:
        raise ValueError("empty legal menu")
    menu = [{**{key: value for key, value in c.items() if key != "_key"},
             "construction_slot": slot, "slot_origin": origin}
            for slot, (c, origin) in sorted(selected.items())]
    return menu, {"source_candidates": len(raw), "canonical_distinct":
                  len({c["_key"] for c in pool}), "preferred_duplicates": dropped,
                  "legal_candidates": len(menu)}
