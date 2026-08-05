"""Authentication, declassification, and the executable closure theorem."""

from dataclasses import replace

import pytest

from experiments.candidates.orbit_shadow_read.eight_cell_audit import (
    build_snapshot,
    restore_clone,
    serialize_snapshot,
)

from experiments.candidates.orbit_owner_match import block
from experiments.candidates.orbit_owner_match import canon
from experiments.candidates.orbit_owner_match import records
from experiments.candidates.orbit_owner_match import trust


@pytest.fixture(scope="module")
def snapshot():
    return build_snapshot()


@pytest.fixture(scope="module")
def clone(snapshot):
    return restore_clone(serialize_snapshot(snapshot), "test-clone")


@pytest.fixture(scope="module")
def blk(snapshot):
    return block.build_block(snapshot)


@pytest.fixture(scope="module")
def cells(blk):
    return block.block_cells(blk)


def test_snapshot_digest_matches_the_frozen_literal(snapshot):
    """Rejects: a fixture drift that would silently invalidate the binding."""
    digest = canon.sha256_hex(serialize_snapshot(snapshot))
    assert digest == trust.SOURCE_SNAPSHOT_DIGEST


def test_inherited_source_is_the_pinned_blob():
    """Rejects: running against a different inherited D1 implementation."""
    trust.inherited_source_gate()


def test_public_write_is_writer_independent(snapshot):
    """Rejects: leaking writer identity into the public write.

    If the public bytes differed by writer, M would be aliased with
    provenance and the design would identify the writer channel rather than
    owner match -- the exact confound round 3 flagged.
    """
    w1 = trust.build_write_d2_with_b(snapshot, "W1", 1)
    w2 = trust.build_write_d2_with_b(snapshot, "W2", 1)
    schema = records.SCHEMA_SIBLING_WRITE_D1
    assert (canon.serialize_struct(schema, w1.public)
            == canon.serialize_struct(schema, w2.public))
    assert w1.sidecar.mac != w2.sidecar.mac


def test_mac_covers_writer_schema(snapshot, clone):
    """Rejects: a MAC over only the fields verify_sibling happens to check.

    The inherited verifier never inspects ``writer_schema``, so a MAC that
    excluded it would let a schema swap pass authenticated.
    """
    write = trust.build_write_d2_with_b(snapshot, "W1", 1)
    swapped_input = replace(write.public.writer_input,
                            writer_schema="orbit-sibling-writer-v2")
    swapped = replace(write.public, writer_input=swapped_input)
    tampered = records.SiblingWrite_D2(swapped, write.sidecar)
    with pytest.raises(canon.ContractError):
        trust.verify_write_d2(clone, tampered)


def test_forged_writer_identity_is_rejected(snapshot, clone):
    """Rejects: trusting the sidecar's claimed writer id."""
    honest = trust.build_write_d2_with_b(snapshot, "W2", 1)
    forged = records.SiblingWrite_D2(
        honest.public, records.AuthSidecar_D2("W1", "K1", honest.sidecar.mac))
    with pytest.raises(canon.ContractError):
        trust.verify_write_d2(clone, forged)


def test_owner_match_follows_the_binding(snapshot, clone):
    """Rejects: an owner-match value supplied by the caller."""
    w1 = trust.build_write_d2_with_b(snapshot, "W1", 0)
    w2 = trust.build_write_d2_with_b(snapshot, "W2", 0)
    assert trust.verify_write_d2(clone, w1).owner_match is True
    assert trust.verify_write_d2(clone, w2).owner_match is False


def test_declassify_requires_successful_authentication():
    """Rejects: a declassifier that reads owner_match off a failed result."""
    failed = records.VerificationResult(False, True, "W1", "0" * 64)
    with pytest.raises(canon.ContractError):
        trust.declassify(failed)


def test_block_is_the_complete_sixteen_cell_census(cells):
    assert len(cells) == 16
    expected = {(q, m, b, r)
                for q in (0, 1) for m in (-1, 1)
                for b in (-1, 1) for r in (-1, 1)}
    assert set(cells) == expected


def test_cross_m_closure_holds(cells):
    """The load-bearing theorem: matched cells differ only in the predicate."""
    block.cross_m_closure_gate(cells)


def test_cross_m_closure_would_catch_an_actor_visible_difference(cells):
    """Rejects: a closure gate that only compares one cell to itself.

    D0.4's per-cell projection check could not see a difference BETWEEN the
    W1- and W2-derived bases; this shows the new gate can.
    """
    victim = (0, -1, 1, 1)
    cell = cells[victim]
    poisoned_input = replace(cell.actor_input, age=cell.actor_input.age + 1)
    tampered = dict(cells)
    tampered[victim] = replace(cell, actor_input=poisoned_input)
    with pytest.raises(canon.ContractError):
        block.cross_m_closure_gate(tampered)


def test_cross_q_closure_holds(cells):
    block.cross_q_closure_gate(cells)


def test_lineage_rebuild_kills_a_forged_predicate(snapshot, cells):
    """Rejects: provenance enforced only by exact-class gates.

    ``VerifiedOwnerPredicate(True)`` is constructible by anyone, so type
    checks cannot prove origin.  Rebuilding recomputes the match from the
    trusted binding, so a cell claiming an unearned match fails.
    """
    victim = (0, -1, 1, 1)
    cell = cells[victim]
    forged_input = replace(cell.actor_input, verified_owner_match=True)
    tampered = dict(cells)
    tampered[victim] = replace(cell, actor_input=forged_input)
    with pytest.raises(canon.ContractError):
        block.lineage_rebuild_gate(snapshot, tampered)


def test_lineage_rebuild_accepts_the_honest_block(snapshot, cells):
    block.lineage_rebuild_gate(snapshot, cells)


def test_relabelled_census_is_rejected(snapshot, cells):
    """Rejects: authenticating cells but not the keys they are filed under.

    The accumulators weight each cell by its DICT KEY, so swapping the two
    ``m`` labels at a fixed ``(b, r)`` for both aliases halves the
    three-factor contrast.  Every other block gate -- key census, cross-M,
    cross-Q, clone independence, public-write invariance, lineage rebuild --
    passes on the relabelled census, because each cell is individually
    honest and only its filing is wrong.
    """
    relabelled = dict(cells)
    for q in (0, 1):
        plus_key = (q, 1, 1, 1)
        minus_key = (q, -1, 1, 1)
        relabelled[plus_key], relabelled[minus_key] = (
            cells[minus_key], cells[plus_key])

    # The other gates really do pass -- this is what makes the hole subtle.
    block.cross_q_closure_gate(cells)
    block.public_write_invariance_gate(relabelled)
    block.lineage_rebuild_gate(snapshot, relabelled)
    assert set(relabelled) == set(cells)

    with pytest.raises(canon.ContractError):
        block.census_key_authenticity_gate(relabelled)
    block.census_key_authenticity_gate(cells)


def test_clone_independence_and_public_write_invariance(blk, cells):
    block.clone_independence_gate(blk)
    block.public_write_invariance_gate(cells)


def test_one_reused_clone_is_rejected(snapshot):
    """Rejects: sixteen cells built from ONE clone object.

    D0.5 derived clone ids from each cell's labels, so this census produced
    sixteen distinct names and passed every block gate -- including the one
    named for clone independence -- while the "sixteen distinct clones"
    proposition was false.  The witness observes the object by identity.
    """
    from experiments.candidates.orbit_owner_match.records import (
        Block, BlockEntry,
    )
    shared = restore_clone(serialize_snapshot(snapshot), "shared")
    cells, witnesses = {}, {}
    for writer_id, b, role, q in block.BLOCK_REQUESTS:
        cell, witness = block.build_target_cell(shared, writer_id, b, role, q)
        key = cell.key.as_tuple()
        cells[key] = cell
        witnesses[key] = witness
    order = sorted(cells)
    forged = Block(
        block.BLOCK_ID,
        tuple(BlockEntry(cells[k].key, cells[k]) for k in order),
        tuple(witnesses[k] for k in order))

    # Everything else still passes: that is what made the hole invisible.
    materialized = block.block_cells(forged)
    block.census_key_authenticity_gate(materialized)
    block.exact_key_domain_gate(materialized)
    block.cross_m_closure_gate(materialized)
    block.cross_q_closure_gate(materialized)
    block.public_write_invariance_gate(materialized)
    block.lineage_rebuild_gate(snapshot, materialized)

    with pytest.raises(canon.ContractError):
        block.clone_independence_gate(forged)


def test_boolean_census_key_is_rejected(cells):
    """Rejects: ``True`` standing in for ``1`` in an external census key.

    Python set and dict semantics make ``True == 1`` and ``hash(True) ==
    hash(1)``, so D0.5's key-set comparison and every ``cells[(q, m, b, r)]``
    lookup admitted a boolean-typed label.
    """
    forged = dict(cells)
    victim = (1, 1, 1, 1)
    forged[(True, 1, 1, 1)] = forged.pop(victim)
    with pytest.raises(canon.ContractError):
        block.exact_key_domain_gate(forged)


def test_raw_bit_comparison_sees_signed_zero():
    """Rejects: closure comparisons that rely on the canonical encoder.

    The canonical encoder merges -0.0 and +0.0 by design, so a closure gate
    built only on it would call two different floats equal.
    """
    assert block.raw_bits(0.0) != block.raw_bits(-0.0)
    assert (canon._enc_float(0.0) == canon._enc_float(-0.0))


def test_duplicate_analysis_key_is_rejected(snapshot):
    """Rejects: collection that silently overwrites a repeated key."""
    key = (0, 1, 1, 1)
    block.reject_duplicate({}, key)
    with pytest.raises(canon.ContractError):
        block.reject_duplicate({key: object()}, key)


def test_block_rejects_a_foreign_snapshot():
    """Rejects: building cells on a fixture the binding does not cover."""
    foreign = replace(build_snapshot(), snapshot_id="not-the-frozen-fixture")
    with pytest.raises(canon.ContractError):
        block.fresh_clone(foreign, "W1", 0, 0, 0)
