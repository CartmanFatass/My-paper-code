from __future__ import annotations

import dataclasses

import numpy as np

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import CHECKPOINTS
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.tapes import (
    B01EvaluationAddress, B01EvaluationRNG, evaluation_tape,
)


def test_evaluation_tape_is_common_across_arm_intervention_and_checkpoint_metadata():
    tape = evaluation_tape(
        b"T" * 32, seed_label="FRRIE-B01-FRESH-BLOCK-001", roster=6, episode=17,
    )
    direct = tape.direct_bytes()
    bindings = [tape.binding(checkpoint) for checkpoint in CHECKPOINTS]
    assert all(tape.direct_bytes() == direct for _ in bindings)
    assert {row["checkpoint"] for row in bindings} == set(CHECKPOINTS)
    assert all(row["checkpoint_role"] == "METADATA_ONLY" for row in bindings)
    assert all(row["arm_independent"] and row["intervention_independent"] for row in bindings)


def test_evaluation_address_has_no_checkpoint_arm_or_intervention_coordinate():
    fields = set(dataclasses.asdict(B01EvaluationAddress(
        seed_label="FRRIE-B01-FRESH-BLOCK-001", roster=6, episode=0,
        kind="event_time", basin=0, event_ordinal=0,
    )))
    assert "checkpoint" not in fields
    assert "arm" not in fields
    assert "intervention" not in fields


def test_top24_tape_is_repeatable_readonly_and_native_padded():
    left = evaluation_tape(
        b"T" * 32, seed_label="FRRIE-B01-FRESH-BLOCK-002", roster=21, episode=255,
    )
    right = evaluation_tape(
        b"T" * 32, seed_label="FRRIE-B01-FRESH-BLOCK-002", roster=21, episode=255,
    )
    assert left.direct_bytes() == right.direct_bytes()
    assert not left.action_uniform.flags.writeable
    assert left.action_uniform.min() >= 0.0
    assert left.action_uniform.max() < 1.0
    payload = left.native_environment_payload()
    assert payload.roster == 21
    assert payload.uplink_uniforms.shape == (12, 21, 21)


def test_top24_value_is_exactly_first_three_bytes_over_two_pow_24():
    rng = B01EvaluationRNG(b"T" * 32)
    address = B01EvaluationAddress(
        seed_label="FRRIE-B01-FRESH-BLOCK-001", roster=6, episode=3,
        kind="action_uniform", slot=7, public_role=2, role_local_index=1, sender=5,
    ).validate()
    numerator = int.from_bytes(rng.block(address)[:3], "big")
    value = rng.uniform_float32(address)
    assert value == numerator / 2**24
    assert np.float32(value).tobytes() == np.asarray(numerator / 2**24, dtype=np.float32).tobytes()
