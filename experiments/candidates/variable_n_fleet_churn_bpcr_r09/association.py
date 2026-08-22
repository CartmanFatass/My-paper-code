"""Row-cut and raw-record consistent-relabel conformance utilities."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Hashable, Sequence

import numpy as np


@dataclass(frozen=True)
class RowCutRecord:
    reassigned_rows: np.ndarray
    origin_for_recipient: tuple[int, ...]
    blocks: tuple[tuple[int, ...], ...]
    opportunity: int


def row_cut(
    score_rows: np.ndarray,
    partition_keys: Sequence[Hashable],
    derangement_for_block: Callable[[tuple[int, ...]], Sequence[int]],
) -> RowCutRecord:
    rows=np.asarray(score_rows,dtype=np.float64)
    if rows.ndim!=2 or rows.shape[1]!=4 or len(partition_keys)!=len(rows):
        raise ValueError("row cut requires one complete four-token row per recipient")
    groups: dict[Hashable,list[int]]=defaultdict(list)
    for index,key in enumerate(partition_keys):groups[key].append(index)
    mapping=list(range(len(rows)));blocks=[];opportunity=0
    for block_list in groups.values():
        block=tuple(block_list);blocks.append(block)
        if len(block)<2:continue
        origins=tuple(int(x) for x in derangement_for_block(block))
        if sorted(origins)!=sorted(block) or any(a==b for a,b in zip(block,origins)):
            raise ValueError("each eligible block requires a whole-row derangement")
        opportunity=1
        for recipient,origin in zip(block,origins):mapping[recipient]=origin
    cut=rows[np.asarray(mapping)]
    if sorted(map(tuple,cut.tolist()))!=sorted(map(tuple,rows.tolist())):
        raise AssertionError("row multiset was not preserved")
    return RowCutRecord(cut,tuple(mapping),tuple(sorted(blocks)),opportunity)


def inverse_map_command(command: Sequence[int | None], origin_for_recipient: Sequence[int]) -> tuple[int | None,...]:
    return tuple(None if item is None else int(item) for item in command)


def consistent_relabel(
    raw_records: np.ndarray,
    permutation: Sequence[int],
    complete_decode: Callable[[np.ndarray], Sequence[int | None]],
) -> tuple[int | None,...]:
    """Recompute from raw records and map presented indices back to physical rows."""
    records=np.asarray(raw_records);p=tuple(int(x) for x in permutation)
    if sorted(p)!=list(range(len(records))):raise ValueError("relabel must be a permutation")
    decoded=tuple(complete_decode(records[np.asarray(p)]))
    return tuple(None if item is None else p[int(item)] for item in decoded)
