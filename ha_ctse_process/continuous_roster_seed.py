"""Pure seed arithmetic shared by continuous-roster experiment modules."""

from __future__ import annotations

from collections.abc import Mapping


def seed_block_from_bases(
    seed_bases: Mapping[str, int],
    replicate: int,
    *,
    formal: bool,
    nonformal_offset: int,
) -> dict[str, int]:
    offset = replicate + (0 if formal else nonformal_offset)
    return {name: base + offset for name, base in seed_bases.items()}


def bootstrap_seed_from_base(
    base: int, *, formal: bool, nonformal_offset: int
) -> int:
    return base + (0 if formal else nonformal_offset)
