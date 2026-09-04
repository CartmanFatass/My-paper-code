from __future__ import annotations

from fractions import Fraction

from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.host import (
    context,
    decode_cell,
    panel,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.support import (
    Address,
    Purpose,
    Split,
)


def test_cell_last_axis_fastest_and_complete() -> None:
    assert decode_cell(0).payload.value == "RECEIVER_CORRECT"
    assert decode_cell(1).payload.value == "SWAPPED"
    assert decode_cell(2).payload.value == "NATIVE_NEUTRAL"
    assert decode_cell(3).access.value == "BINDING_GATED"
    assert decode_cell(6).binding.value == "WHOLE_CARRIER_REASSOCIATED"
    assert decode_cell(12).semantic.value == "REFRESH"
    assert decode_cell(24).owner.value == "BROKEN"


def test_codebook_literals_and_train_eval_nonce_separation() -> None:
    train = context(Address(Purpose.MAIN, 7, Split.TRAIN, 0, 13))
    evaluation = context(Address(Purpose.MAIN, 7, Split.EVAL, 0, 13))
    assert train.fields["physical_receiver"] == 1
    assert train.fields["carrier_nonce"] == 68
    assert train.fields["body_nonce"] == 103
    assert evaluation.fields["carrier_nonce"] == 68
    assert evaluation.fields["body_nonce"] == 111
    assert train.fields["presentation_slot"] == 129
    assert train.fields["public_phase"] == 147
    changed = {name for name in train.fields if train.fields[name] != evaluation.fields[name]}
    assert changed == {"body_nonce"}


def test_full_q_targets_are_exact_and_unique_on_entire_panel() -> None:
    contexts = panel(Purpose.MAIN, 0, Split.EVAL)
    assert len(contexts) == 768
    allowed = {
        (Fraction(3, 4), Fraction(1, 8), Fraction(-1, 4)),
        (Fraction(-5, 4), Fraction(1, 8), Fraction(-1, 4)),
        (Fraction(-3, 4), Fraction(1, 8), Fraction(-1, 4)),
        (Fraction(-3, 4), Fraction(-7, 8), Fraction(-1, 4)),
    }
    assert {row.target_q for row in contexts}.issubset(allowed)
    assert all(sum(value == max(row.target_q) for value in row.target_q) == 1 for row in contexts)


def test_receiver_and_presentation_twins_preserve_oracle_action_and_value() -> None:
    contexts = panel(Purpose.MAIN, 2, Split.EVAL)
    by_key = {(row.address.cell, row.address.slot): row for row in contexts}
    for row in contexts:
        receiver_twin = by_key[(row.address.cell, row.address.slot ^ 1)]
        presentation_twin = by_key[(row.address.cell, row.address.slot ^ 2)]
        assert receiver_twin.target_q == row.target_q
        assert receiver_twin.oracle_action == row.oracle_action
        assert presentation_twin.target_q == row.target_q
        assert presentation_twin.oracle_action == row.oracle_action


def test_train_eval_tuple_support_is_disjoint_but_marginals_match() -> None:
    train = panel(Purpose.MAIN, 9, Split.TRAIN)
    evaluation = panel(Purpose.MAIN, 9, Split.EVAL)
    for name in ("carrier_nonce", "body_nonce"):
        assert {row.fields[name] for row in train} == {row.fields[name] for row in evaluation}
    train_tuples = {(row.address.cell, row.fields["carrier_nonce"], row.fields["body_nonce"]) for row in train}
    eval_tuples = {(row.address.cell, row.fields["carrier_nonce"], row.fields["body_nonce"]) for row in evaluation}
    assert train_tuples.isdisjoint(eval_tuples)
