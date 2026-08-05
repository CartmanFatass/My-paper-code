"""Cell construction and the executable closure theorem.

This module builds actor INPUTS and proves closure properties over them.  It
never evaluates the actor, the nulls, the controls or the mutants -- it does
not even import them.  That separation is deliberate: it is what lets the
freeze claim "cells constructed, discriminator not executed" be checked by
reading the import graph rather than by trusting a sentence.

Round-6 validation found the accepted cross-M closure theorem was simply
absent from D0.4.  The per-cell projection check proved only
``strip_predicate(extend(base, p)) == base`` for the *same* base, which is a
tautology about one cell; it said nothing about whether the W1-derived and
W2-derived bases are equal to each other.  Since the whole design rests on
"the only actor-visible difference between matched owner-match states is the
sanctioned predicate", that was the load-bearing missing proof.

The gates here supply it:

``cross_m_closure_gate``
    For every matched ``(b, role, q)``, the two cells with opposite
    owner-match states have byte-identical D1 actor inputs and raw-bit
    identical float fields, and differ in exactly one D2 field.
``cross_q_closure_gate``
    For every ``(m, b, role)``, the two q aliases have byte-identical actor
    inputs (the inherited adapter is q-blind; this pins that inheritance).
``clone_independence_gate``
    Distinct clone ids, all restored from the one frozen source snapshot.
``lineage_rebuild_gate``
    Every cell equals what the canonical builder produces from the cell's own
    recorded inputs.  This is the dynamic half of the provenance argument in
    :mod:`trust`: a fabricated predicate cannot survive, because rebuilding
    recomputes ``owner_match`` from the binding rather than copying it.

Block size note.  The census is the sixteen ``M x B x role x Q`` cells fixed
by the accepted design.  The round-6 text asks for a "complete matched
32-cell census"; 32 is the size of the *identity-crossover contingency*
design named by terminal T2, not of the frozen sixteen-cell block.  The
sixteen-cell census is built here and the discrepancy is flagged for
adjudication rather than silently resolved either way.
"""

from __future__ import annotations

import struct as _structmod

from experiments.candidates.orbit_shadow_read.eight_cell_audit import (
    ActorInput,
    Clone,
    restore_clone,
    serialize_snapshot,
)

from experiments.candidates.orbit_owner_match.canon import (
    ContractError,
    serialize_struct,
    sha256_hex,
)
from experiments.candidates.orbit_owner_match.records import (
    AnalysisKey,
    BlockCensus,
    CellEvidence,
    SCHEMA_ACTOR_INPUT_D1,
    SCHEMA_ACTOR_INPUT_D2,
    SCHEMA_TARGET_CELL,
    TargetCell,
)
from experiments.candidates.orbit_owner_match.trust import (
    EXPECTED_OWNER_BINDING,
    SOURCE_SNAPSHOT_DIGEST,
    build_d1_actor_input,
    build_write_d2_with_b,
    declassify,
    extend_d1_actor_input,
    strip_predicate,
    verify_write_d2,
)


WRITER_IDS = ("W1", "W2")
BINARY = (0, 1)

# The frozen census: sixteen (writer, b, role, q) construction requests.
BLOCK_REQUESTS = tuple(
    (writer_id, b, role, q)
    for writer_id in WRITER_IDS
    for b in BINARY
    for role in BINARY
    for q in BINARY
)

BLOCK_ID = "orbit-owner-match-d2-sixteen-cell-v1"


# ---------------------------------------------------------------------------
# Raw-bit float discipline
# ---------------------------------------------------------------------------


def raw_bits(value: float) -> bytes:
    """Exact binary64 bits, with no canonicalization.

    The canonical DATA serializer folds ``-0.0`` into ``+0.0`` so that equal
    values serialize equally.  That is right for canonical bytes and wrong
    for a closure comparison, where the question is whether two floats are
    the *same float*.  Closure gates therefore compare raw bits.
    """
    if type(value) is not float:
        raise ContractError("exact float required for raw-bit comparison")
    return _structmod.pack(">d", value)


def raw_bits_tuple(values: tuple) -> bytes:
    if type(values) is not tuple:
        raise ContractError("exact tuple required")
    return b"".join(raw_bits(value) for value in values)


def actor_input_raw_bits(actor_input: ActorInput) -> bytes:
    """Raw-bit image of every float-bearing field of a D1 actor input."""
    if type(actor_input) is not ActorInput:
        raise ContractError("exact inherited ActorInput required")
    return (raw_bits_tuple(actor_input.actor_tensor)
            + b"|" + raw_bits_tuple(actor_input.recurrent_state))


# ---------------------------------------------------------------------------
# Cell construction (inputs only; the actor is never called here)
# ---------------------------------------------------------------------------


def clone_id_for(writer_id: str, b: int, role: int, q: int) -> str:
    if type(writer_id) is not str:
        raise ContractError("exact str writer_id required")
    for name, value in (("b", b), ("role", role), ("q", q)):
        if type(value) is not int or value not in BINARY:
            raise ContractError("exact binary int required for %s" % name)
    return "clone-%s-b%d-r%d-q%d" % (writer_id, b, role, q)


def fresh_clone(snapshot, writer_id: str, b: int, role: int, q: int) -> Clone:
    source = serialize_snapshot(snapshot)
    if sha256_hex(source) != SOURCE_SNAPSHOT_DIGEST:
        raise ContractError("snapshot is not the frozen source fixture")
    return restore_clone(source, clone_id_for(writer_id, b, role, q))


def build_target_cell(clone: Clone, writer_id: str, b: int, role: int,
                      q: int) -> TargetCell:
    """Construct one cell's authenticated input.

    Ordering is the contract: authenticate, declassify, adapt through the
    inherited D1 path, extend.  The projection gate then proves the extension
    added nothing the D1 surface can see.
    """
    write = build_write_d2_with_b(clone.snapshot, writer_id, b)
    verification = verify_write_d2(clone, write)
    predicate = declassify(verification)
    base = build_d1_actor_input(clone, write, role, q)
    d2 = extend_d1_actor_input(base, predicate)
    if (serialize_struct(SCHEMA_ACTOR_INPUT_D1, strip_predicate(d2))
            != serialize_struct(SCHEMA_ACTOR_INPUT_D1, base)):
        raise ContractError("D1 projection inequality", "T1")
    if actor_input_raw_bits(strip_predicate(d2)) != actor_input_raw_bits(base):
        raise ContractError("D1 projection raw-bit inequality", "T1")
    if int(d2.actor_tensor[-2]) != b:
        raise ContractError("label mapping: tensor B mismatch")
    if int(d2.actor_tensor[-1]) != role:
        raise ContractError("label mapping: tensor role mismatch")
    if write.public.writer_input.b != b:
        raise ContractError("label mapping: writer b mismatch")
    m = 1 if d2.verified_owner_match else -1
    if (m == 1) != (writer_id == EXPECTED_OWNER_BINDING.expected_owner_id):
        raise ContractError("label mapping: predicate/expected-owner mismatch")
    return TargetCell(AnalysisKey(m, 2 * b - 1, 2 * role - 1, q), write,
                      verification, d2)


def reject_duplicate(collected: dict, key: tuple) -> None:
    """Refuse a repeated analysis key at collection time.

    Assignment into a dict silently overwrites, which would turn a duplicated
    construction request into a quietly smaller census that still passes a
    cardinality check performed afterwards.
    """
    if type(collected) is not dict:
        raise ContractError("exact dict census required")
    if key in collected:
        raise ContractError("duplicate analysis key %r in block" % (key,))


def build_block(snapshot) -> dict:
    """Build the complete sixteen-cell census keyed by ``(q, m, b, r)``.

    Duplicate keys are rejected at collection time rather than silently
    overwriting, and the key census is compared to the frozen expectation.
    """
    cells = {}
    for writer_id, b, role, q in BLOCK_REQUESTS:
        clone = fresh_clone(snapshot, writer_id, b, role, q)
        cell = build_target_cell(clone, writer_id, b, role, q)
        key = cell.key.as_tuple()
        reject_duplicate(cells, key)
        cells[key] = cell
    expected = frozenset(
        (q, m, 2 * b - 1, 2 * role - 1)
        for m in (-1, 1) for b in BINARY for role in BINARY for q in BINARY
    )
    if frozenset(cells) != expected:
        raise ContractError("block key census mismatch")
    if len(cells) != 16:
        raise ContractError("block cardinality mismatch")
    return cells


def writer_of(cell: TargetCell) -> str:
    return cell.write.sidecar.writer_id


# ---------------------------------------------------------------------------
# Closure gates
# ---------------------------------------------------------------------------


def census_key_authenticity_gate(cells: dict) -> None:
    """Every census key equals the cell's own analysis label.

    The accumulators weight each cell by its DICT KEY, so a cell filed under
    a key whose ``m`` contradicts its own ``AnalysisKey`` silently rescales
    the three-factor contrast -- swapping the two ``m`` labels at a fixed
    ``(b, r)`` for both aliases halves it.  Nothing else in the block suite
    catches this: the closure gates compare cells to each other and the
    census gate compares only the key SET, so a relabelled block passes all
    of them.
    """
    if type(cells) is not dict:
        raise ContractError("exact dict census required")
    for key, cell in cells.items():
        if type(cell) is not TargetCell:
            raise ContractError("exact TargetCell required in census", "T1")
        if key != cell.key.as_tuple():
            raise ContractError(
                "census key %r contradicts the cell label %r"
                % (key, cell.key.as_tuple()), "T1")


def cross_m_closure_gate(cells: dict) -> None:
    """The owner-match states differ in exactly the sanctioned field.

    For each matched ``(q, b, r)`` the two cells with ``m = +1`` and
    ``m = -1`` must have byte-identical and raw-bit-identical D1 actor
    inputs, and their D2 serializations must differ (otherwise the predicate
    carries no signal at all).
    """
    for q in BINARY:
        for b in (-1, 1):
            for r in (-1, 1):
                plus = cells[(q, 1, b, r)]
                minus = cells[(q, -1, b, r)]
                base_plus = strip_predicate(plus.actor_input)
                base_minus = strip_predicate(minus.actor_input)
                if (serialize_struct(SCHEMA_ACTOR_INPUT_D1, base_plus)
                        != serialize_struct(SCHEMA_ACTOR_INPUT_D1, base_minus)):
                    raise ContractError(
                        "cross-M D1 actor inputs differ in canonical bytes",
                        "T1")
                if (actor_input_raw_bits(base_plus)
                        != actor_input_raw_bits(base_minus)):
                    raise ContractError(
                        "cross-M D1 actor inputs differ in raw bits", "T1")
                if (plus.actor_input.verified_owner_match
                        is minus.actor_input.verified_owner_match):
                    raise ContractError(
                        "cross-M pair does not differ in the predicate", "T1")
                if (serialize_struct(SCHEMA_ACTOR_INPUT_D2, plus.actor_input)
                        == serialize_struct(SCHEMA_ACTOR_INPUT_D2,
                                            minus.actor_input)):
                    raise ContractError(
                        "cross-M D2 actor inputs are indistinguishable", "T1")
                if writer_of(plus) == writer_of(minus):
                    raise ContractError(
                        "cross-M pair shares a writer identity", "T1")


def cross_q_closure_gate(cells: dict) -> None:
    """The q alias is actor-invisible, as inherited from D1."""
    for m in (-1, 1):
        for b in (-1, 1):
            for r in (-1, 1):
                first = cells[(0, m, b, r)]
                second = cells[(1, m, b, r)]
                if (serialize_struct(SCHEMA_ACTOR_INPUT_D2, first.actor_input)
                        != serialize_struct(SCHEMA_ACTOR_INPUT_D2,
                                            second.actor_input)):
                    raise ContractError(
                        "q aliases produce different actor inputs", "T1")
                if (actor_input_raw_bits(strip_predicate(first.actor_input))
                        != actor_input_raw_bits(
                            strip_predicate(second.actor_input))):
                    raise ContractError(
                        "q aliases differ in raw bits", "T1")


def clone_independence_gate(cells: dict) -> None:
    """Sixteen distinct clones, all from the one frozen source snapshot."""
    clone_ids = set()
    for cell in cells.values():
        write = cell.write.public
        if write.writer_input.source_snapshot_digest != SOURCE_SNAPSHOT_DIGEST:
            raise ContractError("cell write is not from the frozen source")
        clone_ids.add(clone_id_for(
            writer_of(cell),
            (cell.key.b + 1) // 2,
            (cell.key.r + 1) // 2,
            cell.key.q))
    if len(clone_ids) != 16:
        raise ContractError("clones are not independent across the block")


def public_write_invariance_gate(cells: dict) -> None:
    """A fixed ``b`` yields one public write, whichever writer produced it."""
    by_b = {}
    for cell in cells.values():
        b = (cell.key.b + 1) // 2
        image = serialize_struct(
            "SiblingWrite_D1@orbit-shadow-read-d1", cell.write.public)
        if b in by_b:
            if by_b[b] != image:
                raise ContractError(
                    "public writes differ across writers for a fixed b", "T1")
        else:
            by_b[b] = image
    if len(by_b) != 2:
        raise ContractError("block does not cover both b values")


def lineage_rebuild_gate(snapshot, cells: dict) -> None:
    """Every cell equals the builder's output from its own recorded inputs.

    This is what makes predicate provenance extensional.  A cell carrying a
    fabricated ``verified_owner_match`` fails here, because the rebuild
    recomputes the match from the trusted binding and the cell's own writer
    identity instead of copying the claimed value.
    """
    for key, cell in cells.items():
        writer_id = writer_of(cell)
        b = (cell.key.b + 1) // 2
        role = (cell.key.r + 1) // 2
        q = cell.key.q
        clone = fresh_clone(snapshot, writer_id, b, role, q)
        rebuilt = build_target_cell(clone, writer_id, b, role, q)
        if (serialize_struct(SCHEMA_TARGET_CELL, rebuilt)
                != serialize_struct(SCHEMA_TARGET_CELL, cell)):
            raise ContractError("cell lineage rebuild mismatch at %r" % (key,),
                                "T1")


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def cell_evidence(cell: TargetCell) -> CellEvidence:
    return CellEvidence(
        cell.key,
        clone_id_for(writer_of(cell), (cell.key.b + 1) // 2,
                     (cell.key.r + 1) // 2, cell.key.q),
        writer_of(cell),
        sha256_hex(serialize_struct(SCHEMA_TARGET_CELL, cell)),
        sha256_hex(serialize_struct(SCHEMA_ACTOR_INPUT_D1,
                                    strip_predicate(cell.actor_input))),
        sha256_hex(serialize_struct(SCHEMA_ACTOR_INPUT_D2, cell.actor_input)),
    )


def block_census(cells: dict) -> BlockCensus:
    ordered = tuple(cell_evidence(cells[key]) for key in sorted(cells))
    return BlockCensus(BLOCK_ID, ordered)


def block_census_digest(cells: dict) -> str:
    return sha256_hex(serialize_struct(
        "BlockCensus@orbit-owner-match-d2", block_census(cells)))
