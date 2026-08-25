"""Counter-keyed matched panel generator with disjoint opaque split pools."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import itertools
import random
from typing import Iterable

from .domain import (
    EXAMPLE_COUNTS, INTERLEAVINGS, OFFSETS, SUPERBLOCK_COUNTS, Example,
    LeaseUpdate, OwnerUpdate, Receipt, Version, correct_action,
)


NAMESPACE_CONTRACT = {
    "world_template": "dears-b1/world-template/v1",
    "opaque_values": "dears-b1/opaque-values/v1",
    "tags_nonces": "dears-b1/tags-nonces/v1",
    "minibatch_order": "dears-b1/minibatch-order/v1",
    "model_initialization": "dears-b1/model-initialization/v1",
}


def counter_seed(namespace: str, base_seed: int, *parts: object) -> int:
    digest = hashlib.blake2b(digest_size=16, person=b"DEARS-B1-v1")
    digest.update(namespace.encode("utf-8"))
    digest.update(int(base_seed).to_bytes(8, "little", signed=True))
    for part in parts:
        encoded = repr(part).encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "little"))
        digest.update(encoded)
    return int.from_bytes(digest.digest(), "little")


def _rng(namespace: str, base_seed: int, *parts: object) -> random.Random:
    return random.Random(counter_seed(namespace, base_seed, *parts))


def _schedule(split: str, base_seed: int) -> tuple[tuple[object, ...], ...]:
    if split not in OFFSETS:
        raise ValueError(f"unknown split {split!r}")
    repetitions = 2 if split == "train" else 1
    schedule = list(itertools.product(
        range(repetitions), INTERLEAVINGS,
        ("PAYLOAD_FLIP_BAD_TAG", "FOREIGN_ISSUER"),
        (1, 2), ("REFERENCE_BREAK", "GAP"), (1, 2), OFFSETS[split],
    ))
    if len(schedule) != SUPERBLOCK_COUNTS[split]:
        raise AssertionError("frozen superblock schedule count drift")
    _rng(NAMESPACE_CONTRACT["world_template"], base_seed, split, "schedule").shuffle(schedule)
    return tuple(schedule)


@lru_cache(maxsize=16)
def _opaque_blueprints(base_seed: int) -> dict[str, tuple[tuple[Version, ...], ...]]:
    """Allocate all splits together by rejection sampling over the full u32 domain."""
    rng = _rng(NAMESPACE_CONTRACT["opaque_values"], base_seed, "all-splits")
    used: set[int] = set()

    def value() -> int:
        while True:
            candidate = rng.getrandbits(32)
            if candidate and candidate not in used:
                used.add(candidate)
                return candidate

    result: dict[str, tuple[tuple[Version, ...], ...]] = {}
    # The ordering is an allocator convention, not a numeric split convention:
    # every candidate remains an unconstrained rejection-sampled nonzero u32.
    for split in ("train", "validation", "test"):
        rows = []
        for _ in range(SUPERBLOCK_COUNTS[split]):
            rows.append(tuple(Version(value(), value()) for _ in range(10)))
        result[split] = tuple(rows)
    return result


def split_value_sets(base_seed: int) -> dict[str, set[int]]:
    return {
        split: {component for row in rows for version in row
                for component in (version.handle, version.epoch)}
        for split, rows in _opaque_blueprints(base_seed).items()
    }


def _make_example(
    *, base_seed: int, split: str, superblock: int, core_index: int,
    versions: tuple[Version, ...], schedule_row: tuple[object, ...],
) -> Example:
    repetition, order, forge, owner_locus, lease_mode, lease_locus, timely_offset = schedule_row
    del repetition
    order = tuple(order)  # type: ignore[arg-type]
    forge = str(forge)
    owner_locus = int(owner_locus)
    lease_mode = str(lease_mode)
    lease_locus = int(lease_locus)
    timely_offset = int(timely_offset)
    authentication = bool((core_index >> 3) & 1)
    owner_survives = bool((core_index >> 2) & 1)
    lease_survives = bool((core_index >> 1) & 1)
    bit = int(core_index & 1)

    oa, o1, ofinal, obad1, obad2, la, l1, lfinal, lbad1, lbad2 = versions
    event_times = {name: -80 + 15 * position for position, name in enumerate(order)}
    owner_from1 = oa if owner_survives or owner_locus != 1 else obad1
    owner_from2 = o1 if owner_survives or owner_locus != 2 else obad2
    owner_detail = "SURVIVES" if owner_survives else f"BREAK_EDGE_{owner_locus}"

    if lease_survives:
        designated_offset = timely_offset
        lease_detail = "SURVIVES"
    elif lease_mode == "REFERENCE_BREAK":
        designated_offset = timely_offset
        lease_detail = f"REFERENCE_BREAK_EDGE_{lease_locus}"
    else:
        designated_offset = -timely_offset
        lease_detail = f"GAP_EDGE_{lease_locus}"
    edge1_offset = designated_offset if lease_locus == 1 else -2
    edge2_offset = designated_offset if lease_locus == 2 else -2
    lease_from1 = la if lease_survives or lease_mode != "REFERENCE_BREAK" or lease_locus != 1 else lbad1
    lease_from2 = l1 if lease_survives or lease_mode != "REFERENCE_BREAK" or lease_locus != 2 else lbad2
    receipt_until = event_times["L1"] - edge1_offset
    lease1_until = event_times["L2"] - edge2_offset
    nonce_rng = _rng(NAMESPACE_CONTRACT["tags_nonces"], base_seed, split, superblock, core_index)
    authentication_detail = "GENUINE" if authentication else forge
    tag_ok = authentication or forge == "FOREIGN_ISSUER"
    issuer_allowed = authentication or forge == "PAYLOAD_FLIP_BAD_TAG"
    receipt = Receipt(
        displayed_bit=bit, owner_anchor=oa, lease_anchor=la, event_time=-100,
        valid_from=-100, valid_until=receipt_until, tag_ok=tag_ok,
        issuer_allowed=issuer_allowed, nonce=nonce_rng.getrandbits(64),
    )
    updates = {
        "O1": OwnerUpdate(1, owner_from1, o1, event_times["O1"]),
        "O2": OwnerUpdate(2, owner_from2, ofinal, event_times["O2"]),
        "L1": LeaseUpdate(1, lease_from1, l1, event_times["L1"], event_times["L1"], lease1_until),
        "L2": LeaseUpdate(2, lease_from2, lfinal, event_times["L2"], event_times["L2"], 20),
    }
    events = (receipt, *(updates[name] for name in order))
    live = authentication and owner_survives and lease_survives
    return Example(
        seed=base_seed, split=split, superblock=superblock, core_index=core_index,
        events=events, final_owner=ofinal, final_lease=lfinal,
        final_valid_from=event_times["L2"], final_valid_until=20,
        authentication=authentication, owner_survives=owner_survives,
        lease_survives=lease_survives, displayed_bit=bit,
        authentication_detail=authentication_detail, owner_detail=owner_detail,
        lease_detail=lease_detail, handoff_offset=designated_offset, order=order,
        correct_action=correct_action(live, bit),
    )


def iter_examples(base_seed: int, split: str) -> Iterable[Example]:
    schedule = _schedule(split, base_seed)
    opaque = _opaque_blueprints(base_seed)[split]
    for superblock, (schedule_row, versions) in enumerate(zip(schedule, opaque, strict=True)):
        for core_index in range(16):
            yield _make_example(
                base_seed=base_seed, split=split, superblock=superblock,
                core_index=core_index, versions=versions, schedule_row=schedule_row,
            )


def generate_examples(base_seed: int, split: str) -> list[Example]:
    rows = list(iter_examples(base_seed, split))
    if len(rows) != EXAMPLE_COUNTS[split]:
        raise AssertionError("frozen example count drift")
    return rows


def panel_contract(base_seed: int) -> dict[str, object]:
    sets = split_value_sets(base_seed)
    overlap = {
        f"{left}:{right}": len(sets[left] & sets[right])
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
    }
    offset_sets = {
        split: {value for magnitude in magnitudes for value in (magnitude, -magnitude)}
        for split, magnitudes in OFFSETS.items()
    }
    offset_overlap = {
        f"{left}:{right}": sorted(offset_sets[left] & offset_sets[right])
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
    }
    return {
        "superblocks": dict(SUPERBLOCK_COUNTS),
        "examples": dict(EXAMPLE_COUNTS),
        "variants_per_superblock": 16,
        "split_opaque_value_counts": {key: len(value) for key, value in sets.items()},
        "split_overlap_counts": overlap,
        "split_offset_domains": {key: sorted(value) for key, value in offset_sets.items()},
        "split_offset_overlaps": offset_overlap,
        "rejection_sampled_full_nonzero_u32": True,
        "counter_keyed_namespaces": dict(NAMESPACE_CONTRACT),
    }
