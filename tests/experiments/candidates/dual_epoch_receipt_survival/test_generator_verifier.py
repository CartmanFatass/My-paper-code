from __future__ import annotations

from collections import Counter
from dataclasses import replace

import pytest

from experiments.candidates.dual_epoch_receipt_survival.domain import (
    EXAMPLE_COUNTS, INTERLEAVINGS, LeaseUpdate, OwnerUpdate, Receipt,
)
from experiments.candidates.dual_epoch_receipt_survival.generator import (
    generate_examples, panel_contract,
)
from experiments.candidates.dual_epoch_receipt_survival.verifier import (
    rule_dual, verify, verify_example,
)


@pytest.mark.parametrize("split", ["train", "validation", "test"])
def test_generator_has_exact_complete_balanced_matched_superblocks(split):
    rows = generate_examples(13, split)
    assert len(rows) == EXAMPLE_COUNTS[split]
    grouped = {superblock: [row for row in rows if row.superblock == superblock]
               for superblock in {row.superblock for row in rows}}
    assert all(len(block) == 16 for block in grouped.values())
    assert all({row.core_index for row in block} == set(range(16)) for block in grouped.values())
    for block in grouped.values():
        assert len({row.final_owner for row in block}) == 1
        assert len({row.final_lease for row in block}) == 1
        assert len({row.order for row in block}) == 1
        assert len({event.nonce for row in block for event in row.events if isinstance(event, Receipt)}) == 16
    assert set(Counter(row.order for row in rows)) == set(INTERLEAVINGS)
    assert {row.authentication_detail for row in rows} == {
        "GENUINE", "PAYLOAD_FLIP_BAD_TAG", "FOREIGN_ISSUER"
    }
    assert {row.owner_detail for row in rows} == {"SURVIVES", "BREAK_EDGE_1", "BREAK_EDGE_2"}
    assert {row.lease_detail for row in rows} == {
        "SURVIVES", "REFERENCE_BREAK_EDGE_1", "REFERENCE_BREAK_EDGE_2",
        "GAP_EDGE_1", "GAP_EDGE_2",
    }
    assert len({row.refined_cell for row in rows}) == 90


def test_opaque_values_are_rejection_sampled_nonzero_u32_and_split_disjoint():
    report = panel_contract(29)
    assert report["rejection_sampled_full_nonzero_u32"] is True
    assert report["split_overlap_counts"] == {
        "train:validation": 0, "train:test": 0, "validation:test": 0,
    }
    assert report["split_opaque_value_counts"] == {
        "train": 11_520, "validation": 3_840, "test": 11_520,
    }


def test_event_times_and_offsets_obey_chronology_chain_and_held_out_domains():
    rows = generate_examples(43, "test")
    assert {abs(row.handoff_offset) for row in rows} == {1, 3, 5, 7, 9, 11}
    for row in rows:
        times = [event.event_time for event in row.events]
        assert times == sorted(times) and len(set(times)) == 5 and times[-1] < 0
        owners = sorted((event for event in row.events if isinstance(event, OwnerUpdate)), key=lambda x: x.edge)
        leases = sorted((event for event in row.events if isinstance(event, LeaseUpdate)), key=lambda x: x.edge)
        assert [event.edge for event in owners] == [1, 2]
        assert [event.edge for event in leases] == [1, 2]
        assert leases[-1].valid_from <= 0 <= leases[-1].valid_until


def test_verifier_matches_all_generated_labels_and_forges_are_bottom():
    for split in ("train", "validation", "test"):
        for row in generate_examples(13, split):
            result = verify_example(row)
            assert result.live == row.live
            assert result.content == (row.displayed_bit if row.live else None)
            assert rule_dual(result) == row.correct_action
            if not row.authentication:
                assert not result.live and result.content is None


def test_verifier_fails_closed_for_malformed_ambiguous_duplicate_and_broken_inputs():
    row = next(row for row in generate_examples(13, "test") if row.live)
    receipt = row.events[0]
    assert isinstance(receipt, Receipt)
    assert verify([], final_owner=row.final_owner, final_lease=row.final_lease).rejection == "event_count"
    malformed = (*row.events[:-1], object())
    assert verify(malformed, final_owner=row.final_owner, final_lease=row.final_lease).rejection == "malformed_event"
    duplicate_receipt = (receipt, receipt, *row.events[2:])
    assert verify(duplicate_receipt, final_owner=row.final_owner, final_lease=row.final_lease).rejection == "receipt_count"
    bad_tag = (replace(receipt, tag_ok=False), *row.events[1:])
    rejected = verify(bad_tag, final_owner=row.final_owner, final_lease=row.final_lease)
    assert (rejected.live, rejected.content, rejected.rejection) == (False, None, "bad_tag")
    foreign = (replace(receipt, issuer_allowed=False), *row.events[1:])
    assert verify(foreign, final_owner=row.final_owner, final_lease=row.final_lease).rejection == "foreign_issuer"
    owner_updates = [event for event in row.events if isinstance(event, OwnerUpdate)]
    first_owner = owner_updates[0]
    broken_owner = tuple(
        replace(event, from_version=row.final_owner) if event is first_owner else event for event in row.events
    )
    assert verify(broken_owner, final_owner=row.final_owner, final_lease=row.final_lease).rejection == "owner_chain"
    lease_updates = [event for event in row.events if isinstance(event, LeaseUpdate)]
    first_lease = lease_updates[0]
    gap = tuple(
        replace(event, valid_from=receipt.valid_until + 1, event_time=receipt.valid_until + 1)
        if event is first_lease else event for event in row.events
    )
    assert verify(gap, final_owner=row.final_owner, final_lease=row.final_lease).rejection == "coverage_gap"


def test_verifier_fails_closed_for_reversed_updates_and_illegal_interleavings():
    row = next(row for row in generate_examples(13, "test") if row.live)
    receipt = row.events[0]
    owners = sorted(
        (event for event in row.events if isinstance(event, OwnerUpdate)), key=lambda event: event.edge
    )
    leases = sorted(
        (event for event in row.events if isinstance(event, LeaseUpdate)), key=lambda event: event.edge
    )
    # Give the reversed records monotone timestamps so rejection cannot rely on
    # timestamps alone: within-lineage order and the six legal interleavings are
    # part of the fail-closed parse contract.
    reversed_owner = (
        receipt,
        replace(owners[1], event_time=-80),
        replace(owners[0], event_time=-65),
        replace(leases[0], event_time=-50, valid_from=-50),
        replace(leases[1], event_time=-35, valid_from=-35),
    )
    rejected = verify(reversed_owner, final_owner=row.final_owner, final_lease=row.final_lease)
    assert (rejected.live, rejected.content, rejected.rejection) == (
        False, None, "update_interleaving"
    )


def test_verifier_fails_closed_for_event_at_or_after_decision_time():
    row = next(row for row in generate_examples(13, "test") if row.live)
    mutated = list(row.events)
    owner_index = next(index for index, event in enumerate(mutated) if isinstance(event, OwnerUpdate))
    mutated[owner_index] = replace(mutated[owner_index], event_time=5)
    rejected = verify(mutated, final_owner=row.final_owner, final_lease=row.final_lease)
    assert (rejected.live, rejected.content, rejected.rejection) == (
        False, None, "event_not_before_decision"
    )


def test_verifier_fails_closed_when_receipt_timestamp_follows_prior_updates():
    row = next(row for row in generate_examples(13, "test") if row.live)
    receipt = row.events[0]
    mutated = (replace(receipt, event_time=-1), *row.events[1:])
    rejected = verify(mutated, final_owner=row.final_owner, final_lease=row.final_lease)
    assert (rejected.live, rejected.content, rejected.rejection) == (
        False, None, "event_chronology"
    )


def test_verifier_fails_closed_when_receipt_is_not_first_even_with_one_receipt():
    row = next(row for row in generate_examples(13, "test") if row.live)
    reordered = (row.events[1], row.events[0], *row.events[2:])
    rejected = verify(reordered, final_owner=row.final_owner, final_lease=row.final_lease)
    assert (rejected.live, rejected.content, rejected.rejection) == (
        False, None, "receipt_position"
    )


def test_public_verifier_boundary_converts_malformed_typed_fields_to_bottom():
    row = next(row for row in generate_examples(13, "test") if row.live)
    receipt = row.events[0]
    malformed = (replace(receipt, event_time="not-an-int"), *row.events[1:])
    rejected = verify(malformed, final_owner=row.final_owner, final_lease=row.final_lease)
    assert (rejected.live, rejected.content, rejected.rejection) == (
        False, None, "malformed_input"
    )
