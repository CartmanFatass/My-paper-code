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
    Block,
    BlockCensus,
    BlockEntry,
    CellEvidence,
    CloneWitness,
    SCHEMA_ACTOR_INPUT_D1,
    SCHEMA_ACTOR_INPUT_D2,
    SCHEMA_BLOCK,
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


# ---------------------------------------------------------------------------
# Observed clone identity
# ---------------------------------------------------------------------------

# Strong references to every clone object a cell was ever built from, in first
# -observation order.  Strong, not weak: the identity test below is ``is``, and
# a dropped object could otherwise have its ``id`` recycled by a later clone,
# which would make two distinct clones indistinguishable to the witness.
_OBSERVED_CLONES = []


def observe_clone(clone: Clone) -> tuple:
    """``(serial, first_use)`` for this clone OBJECT, decided by identity.

    This is the only place clone provenance is *measured* rather than named.
    D0.5 derived clone ids from each cell's labels, so sixteen constructions
    that all reused one clone object yielded sixteen distinct names; the
    resulting census passed cross-M closure, cross-Q closure, public-write
    invariance, lineage rebuild, census-key authenticity and the gate that
    claimed to check clone independence.
    """
    if type(clone) is not Clone:
        raise ContractError("exact inherited Clone required")
    for serial, seen in enumerate(_OBSERVED_CLONES):
        if seen is clone:
            return serial, False
    _OBSERVED_CLONES.append(clone)
    return len(_OBSERVED_CLONES) - 1, True


def build_target_cell(clone: Clone, writer_id: str, b: int, role: int,
                      q: int) -> tuple:
    """Construct one cell's authenticated input and its clone witness.

    Ordering is the contract: authenticate, declassify, adapt through the
    inherited D1 path, extend.  The projection gate then proves the extension
    added nothing the D1 surface can see.

    Returns ``(cell, witness)``.  The witness is produced here rather than by
    the caller so that no cell can be constructed without its clone being
    observed by identity.
    """
    serial, first_use = observe_clone(clone)
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
    key = AnalysisKey(m, 2 * b - 1, 2 * role - 1, q)
    cell = TargetCell(key, write, verification, d2)
    witness = CloneWitness(key, clone.clone_id, serial, first_use)
    return cell, witness


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


def build_block(snapshot) -> Block:
    """Build the complete sixteen-cell census as an IMMUTABLE image.

    Duplicate keys are rejected at collection time rather than silently
    overwriting, and the key census is compared to the frozen expectation.

    The return value is a frozen :class:`Block`, not the working dict.  D0.5
    returned the dict itself, which the caller then carried through the gates
    and on into evaluation; the object validated and the object evaluated were
    the same mutable mapping, so everything the gates established was
    established about a state that no longer had to hold.
    """
    cells = {}
    witnesses = {}
    for writer_id, b, role, q in BLOCK_REQUESTS:
        clone = fresh_clone(snapshot, writer_id, b, role, q)
        cell, witness = build_target_cell(clone, writer_id, b, role, q)
        key = cell.key.as_tuple()
        reject_duplicate(cells, key)
        cells[key] = cell
        witnesses[key] = witness
    expected = frozenset(
        (q, m, 2 * b - 1, 2 * role - 1)
        for m in (-1, 1) for b in BINARY for role in BINARY for q in BINARY
    )
    if frozenset(cells) != expected:
        raise ContractError("block key census mismatch")
    if len(cells) != 16:
        raise ContractError("block cardinality mismatch")
    order = sorted(cells)
    return Block(
        BLOCK_ID,
        tuple(BlockEntry(cells[key].key, cells[key]) for key in order),
        tuple(witnesses[key] for key in order),
    )


def block_cells(block: Block) -> dict:
    """Materialize a FRESH mapping from the immutable image.

    Each consumer gets its own dict, so no mapping is shared between the
    validation phase and the evaluation phase.
    """
    if type(block) is not Block:
        raise ContractError("exact Block required")
    if len(block.entries) != 16:
        raise ContractError("block image does not carry sixteen entries")
    cells = {}
    for entry in block.entries:
        if type(entry) is not BlockEntry:
            raise ContractError("exact BlockEntry required", "T1")
        key = entry.key.as_tuple()
        reject_duplicate(cells, key)
        cells[key] = entry.cell
    return cells


def block_image(block: Block) -> bytes:
    """Canonical bytes of the whole census, witnesses included."""
    return serialize_struct(SCHEMA_BLOCK, block)


def exact_key_domain_gate(cells: dict) -> None:
    """Every census key is an exact 4-tuple of exact ints in the frozen domain.

    Python's ``==``/``hash`` make ``True`` indistinguishable from ``1`` and let
    any object with a cooperating ``__eq__``/``__hash__`` stand in for a label.
    D0.5 type-checked the ints INSIDE :class:`AnalysisKey` but never the
    external dictionary keys, so set equality against the expected census and
    every ``cells[(q, m, b, r)]`` lookup admitted such substitutes.
    """
    if type(cells) is not dict:
        raise ContractError("exact dict census required")
    for key in cells:
        if type(key) is not tuple or len(key) != 4:
            raise ContractError("census key %r is not an exact 4-tuple" % (key,),
                                "T1")
        for value in key:
            if type(value) is not int:
                raise ContractError(
                    "census key %r carries a non-exact-int component" % (key,),
                    "T1")
        q, m, b, r = key
        if q not in (0, 1):
            raise ContractError("census key q out of domain: %r" % (key,), "T1")
        for value in (m, b, r):
            if value not in (-1, 1):
                raise ContractError(
                    "census key code out of domain: %r" % (key,), "T1")


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


def clone_independence_gate(block: Block) -> None:
    """Sixteen distinct clone OBJECTS, all from the one frozen source snapshot.

    The independence test is on the witnesses, which record the serial the
    clone object received when it was observed by identity at construction
    time, and whether that observation was its first use.  Sixteen distinct
    serials with sixteen first uses is the property; sixteen distinct *names*
    is not, and was what D0.5 checked.
    """
    if type(block) is not Block:
        raise ContractError("exact Block required")
    cells = block_cells(block)
    witnesses = block.witnesses
    if len(witnesses) != 16:
        raise ContractError("block image does not carry sixteen witnesses")
    serials = set()
    names = set()
    for witness in witnesses:
        if type(witness) is not CloneWitness:
            raise ContractError("exact CloneWitness required", "T1")
        if not witness.first_use:
            raise ContractError(
                "clone object reused at %r (serial %d)"
                % (witness.key.as_tuple(), witness.serial), "T1")
        key = witness.key.as_tuple()
        if key not in cells:
            raise ContractError("witness %r has no cell" % (key,), "T1")
        cell = cells[key]
        expected_name = clone_id_for(
            writer_of(cell), (cell.key.b + 1) // 2,
            (cell.key.r + 1) // 2, cell.key.q)
        if witness.clone_id != expected_name:
            raise ContractError(
                "witness clone id %r contradicts the cell labels %r"
                % (witness.clone_id, expected_name), "T1")
        if cell.write.public.writer_input.source_snapshot_digest \
                != SOURCE_SNAPSHOT_DIGEST:
            raise ContractError("cell write is not from the frozen source")
        serials.add(witness.serial)
        names.add(witness.clone_id)
    if len(serials) != 16:
        raise ContractError(
            "clones are not independent: %d distinct clone objects across "
            "sixteen cells" % (len(serials),), "T1")
    if len(names) != 16:
        raise ContractError("clone ids are not distinct across the block", "T1")


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
        rebuilt, _witness = build_target_cell(clone, writer_id, b, role, q)
        if (serialize_struct(SCHEMA_TARGET_CELL, rebuilt)
                != serialize_struct(SCHEMA_TARGET_CELL, cell)):
            raise ContractError("cell lineage rebuild mismatch at %r" % (key,),
                                "T1")


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def cell_evidence(cell: TargetCell, witness: CloneWitness) -> CellEvidence:
    """Evidence for one cell, carrying the OBSERVED clone id.

    The clone id comes from the witness rather than from a second synthesis
    out of the cell's labels: the point of the record is to report what was
    used, and a value re-derived from the labels can only ever agree with
    them.
    """
    if type(witness) is not CloneWitness:
        raise ContractError("exact CloneWitness required")
    if witness.key.as_tuple() != cell.key.as_tuple():
        raise ContractError("witness does not belong to this cell", "T1")
    return CellEvidence(
        cell.key,
        witness.clone_id,
        writer_of(cell),
        sha256_hex(serialize_struct(SCHEMA_TARGET_CELL, cell)),
        sha256_hex(serialize_struct(SCHEMA_ACTOR_INPUT_D1,
                                    strip_predicate(cell.actor_input))),
        sha256_hex(serialize_struct(SCHEMA_ACTOR_INPUT_D2, cell.actor_input)),
    )


def block_census(block: Block) -> BlockCensus:
    if type(block) is not Block:
        raise ContractError("exact Block required")
    ordered = tuple(cell_evidence(entry.cell, witness)
                    for entry, witness in zip(block.entries, block.witnesses))
    return BlockCensus(BLOCK_ID, ordered)


def block_census_digest(block: Block) -> str:
    return sha256_hex(serialize_struct(
        "BlockCensus@orbit-owner-match-d2", block_census(block)))
