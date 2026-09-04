from __future__ import annotations

from dataclasses import fields, replace
from fractions import Fraction

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.addressing import (
    B0_RUN,
    EVAL_MOTIF,
    EVAL_STOCHASTIC,
    INITIAL_DRAW_LABELS,
    OBJECT_ID,
    OPPORTUNITY_DRAW_LABELS,
    TRAIN,
    action_address,
    canonical_json,
    digest,
    env_address,
    fisher_yates,
    order_address,
    parameter_address,
    u64,
    uniform,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import (
    AccessMode,
    Action,
    EventKind,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import (
    EventFamily,
    DynamicHost,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.token import (
    LITERAL_EVENT_LAYOUTS,
    LITERAL_TOKEN_CODEC,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.tapes import (
    build_b0_panel,
    build_motif_panel,
    motif_descriptor,
    primitive_history_parity,
)


def host() -> DynamicHost:
    return DynamicHost(B0_RUN, 21001)


EventCode = EventKind
EVENT_SCHEMAS = {layout.kind: layout for layout in LITERAL_EVENT_LAYOUTS}


def test_canonical_sha256_u64_uniform_and_all_address_forms_are_literal() -> None:
    address = env_address(
        B0_RUN, 21001, TRAIN, 0, 0, "OWNER", "OWNER_OCCURS", 0, 0
    )
    assert canonical_json(address) == (
        b'["CBSC-OMRC-B01","ENV","CBSC-OMRC-B0-INSTRUMENT",21001,'
        b'"TRAIN",0,0,"OWNER","OWNER_OCCURS",0,0]'
    )
    assert digest(address).hex() == (
        "bb180b3d0becce4344a8d93b4d8e508a3c64e8f150ee9f8184c35606e62de22f"
    )
    assert u64(address) == 13481537841354559043
    assert uniform(address) == Fraction(26963075682709118087, 36893488147419103232)
    assert action_address(B0_RUN, 21001, 7, 23) == (
        OBJECT_ID,
        "ACTION",
        B0_RUN,
        21001,
        TRAIN,
        7,
        23,
    )
    assert parameter_address(21001, "input.weight", 9) == (
        OBJECT_ID,
        "PARAM",
        21001,
        "input.weight",
        9,
    )
    assert order_address(B0_RUN, 21001, 0, 3, 7, 2) == (
        OBJECT_ID,
        "ORDER",
        B0_RUN,
        21001,
        0,
        3,
        7,
        2,
    )
    assert all("ARM" not in canonical_json(item).decode() for item in (address, action_address(B0_RUN, 21001, 0, 0)))


def test_literal_codebook_masks_and_token_clock_hold_for_a_complete_tape() -> None:
    tape = host().build_stochastic(TRAIN, 0)
    assert set(EventCode) == set(EVENT_SCHEMAS)
    assert [token.event_order_position for token in tape.public_tokens[:8]] == list(range(8))
    for token in tape.public_tokens:
        schema = LITERAL_TOKEN_CODEC.validate(token)
        assert schema is EVENT_SCHEMAS[EventCode(token.event_kind)]
        assert len(LITERAL_TOKEN_CODEC.pack(token)) == 17
    for opportunity in range(24):
        block = tape.public_tokens[8 + 6 * opportunity : 8 + 6 * (opportunity + 1)]
        assert [token.event_order_position for token in block] == [0, 1, 2, 3, 4, 5]
        assert block[4].event_kind == EventCode.DECISION
        assert block[5].event_kind == EventCode.SETTLEMENT


def _family_for_code(code: int) -> EventFamily:
    event = EventCode(code)
    if event in {EventCode.OWNER, EventCode.NOOP_OWNER}:
        return EventFamily.OWNER
    if event in {EventCode.SEMANTIC, EventCode.NOOP_SEMANTIC}:
        return EventFamily.SEMANTIC
    if event in {EventCode.CAPABILITY, EventCode.NOOP_CAPABILITY}:
        return EventFamily.CAPABILITY
    if event in {EventCode.BODY, EventCode.NOOP_BODY}:
        return EventFamily.BODY
    raise AssertionError("not a pre-action family")


def test_event_order_occurrence_probabilities_and_potential_addresses_are_stable() -> None:
    tape = host().build_stochastic(TRAIN, 0)
    occurrence = {
        EventFamily.OWNER: ("OWNER", "OWNER_OCCURS", Fraction(1, 5), EventCode.OWNER),
        EventFamily.SEMANTIC: (
            "SEMANTIC",
            "SEMANTIC_OCCURS",
            Fraction(1, 5),
            EventCode.SEMANTIC,
        ),
        EventFamily.CAPABILITY: (
            "CAPABILITY",
            "CAPABILITY_OCCURS",
            Fraction(1, 4),
            EventCode.CAPABILITY,
        ),
        EventFamily.BODY: ("BODY", "BODY_OCCURS", Fraction(1, 2), EventCode.BODY),
    }
    for opportunity in range(24):
        block = tape.public_tokens[8 + 6 * opportunity : 12 + 6 * opportunity]
        expected_order = fisher_yates(
            tuple(EventFamily),
            lambda position, retry: env_address(
                B0_RUN,
                21001,
                TRAIN,
                0,
                opportunity,
                "EVENT_ORDER",
                "EVENT_PERM",
                position,
                retry,
            ),
        )
        assert tuple(_family_for_code(token.event_kind) for token in block) == expected_order
        for token, family in zip(block, expected_order):
            address_family, label, threshold, realized_code = occurrence[family]
            expected_realized = uniform(
                env_address(
                    B0_RUN,
                    21001,
                    TRAIN,
                    0,
                    opportunity,
                    address_family,
                    label,
                )
            ) < threshold
            assert (token.event_kind == realized_code) is expected_realized
    labels_by_opportunity = {
        opportunity: {
            address[-3]
            for address in tape.generation_audit.draw_addresses
            if address[6] == opportunity
        }
        for opportunity in range(24)
    }
    assert all(set(OPPORTUNITY_DRAW_LABELS) <= labels for labels in labels_by_opportunity.values())
    initial_labels = {
        address[-3]
        for address in tape.generation_audit.draw_addresses
        if address[6] == -1
    }
    assert set(INITIAL_DRAW_LABELS) <= initial_labels


def test_stochastic_tape_is_deterministic_split_separated_and_learner_clean() -> None:
    first = host().build_stochastic(TRAIN, 3)
    second = host().build_stochastic(TRAIN, 3)
    heldout = host().build_stochastic(EVAL_STOCHASTIC, 3)
    assert first.primitive_digest == second.primitive_digest
    assert first.generation_audit.draw_digest == second.generation_audit.draw_digest
    assert first.primitive_digest != heldout.primitive_digest
    assert not (
        set(first.generation_audit.draw_addresses)
        & set(heldout.generation_audit.draw_addresses)
    )
    assert first.transition_count == 152 and first.decision_count == 24
    assert first.generation_audit.owner_tokens_consumed <= 26
    assert first.generation_audit.epoch_tokens_consumed <= 26
    projections = first.learner_tokens()
    assert len(projections) == 152
    assert tuple(field.name for field in fields(projections[0])) == ("packed",)
    assert not hasattr(projections[0], "valid")
    assert not hasattr(projections[0], "oracle_action")
    assert not hasattr(projections[0], "ledger")
    assert first.evaluator().truth(0).decision.opportunity_index == 0


def test_episode_tape_rejects_divergent_public_and_packed_token_sources() -> None:
    tape = host().build_stochastic(TRAIN, 0)
    corrupted = list(tape._packed_tokens)
    corrupted[0] = bytes(
        [corrupted[0][0], corrupted[0][1] ^ 1, *corrupted[0][2:]]
    )
    with pytest.raises(ValueError, match="canonical public tokens"):
        replace(tape, _packed_tokens=tuple(corrupted))


def test_actions_change_only_evaluator_ledger_and_never_later_tape_state() -> None:
    tape = host().build_stochastic(TRAIN, 4)
    digest_before = tape.primitive_digest
    evaluator = tape.evaluator()
    ledgers = tuple(evaluator.ledger(0, action) for action in Action if action is not Action.WAIT)
    assert len(set(ledgers)) >= 2
    assert tape.primitive_digest == digest_before
    assert evaluator.truth(1).state is evaluator.truth(1).state


def test_all_32_motifs_have_exact_id_order_and_bounded_pool_consumption() -> None:
    panel = build_motif_panel(host())
    assert tuple(t.motif.tape_id for t in panel) == tuple(range(32))
    assert tuple(t.identity.episode_id for t in panel) == tuple(range(32))
    for tape_id, tape in enumerate(panel):
        descriptor = motif_descriptor(tape_id)
        assert tape.identity.split == EVAL_MOTIF
        assert tape.motif == descriptor
        assert descriptor.tape_id == 4 * descriptor.family + 2 * descriptor.target_receiver + descriptor.presented_slot
        assert tape.transition_count == 152 and tape.decision_count == 24
        assert tape.generation_audit.owner_tokens_consumed <= 26
        assert tape.generation_audit.epoch_tokens_consumed <= 26
    assert panel[20].generation_audit.owner_tokens_consumed == 26
    assert panel[24].generation_audit.epoch_tokens_consumed == 26


def test_motif_templates_preserve_currentness_causal_edges() -> None:
    owner_order = host().build_motif(20).evaluator()  # m=5, r=0, s=0
    assert owner_order.truth(0).preaction_codes == (
        EventCode.OWNER,
        EventCode.BODY,
        EventCode.CAPABILITY,
        EventCode.NOOP_SEMANTIC,
    )
    assert owner_order.truth(1).preaction_codes == (
        EventCode.BODY,
        EventCode.OWNER,
        EventCode.CAPABILITY,
        EventCode.NOOP_SEMANTIC,
    )
    assert owner_order.truth(0).valid
    assert not owner_order.truth(1).valid

    semantic_order = host().build_motif(24).evaluator()  # m=6, r=0, s=0
    assert semantic_order.truth(0).valid
    assert not semantic_order.truth(1).valid
    assert semantic_order.truth(0).preaction_codes[:2] == (
        EventCode.SEMANTIC,
        EventCode.BODY,
    )
    assert semantic_order.truth(1).preaction_codes[:2] == (
        EventCode.BODY,
        EventCode.SEMANTIC,
    )


def test_owner_semantic_capability_content_active_and_retention_motifs_are_exact() -> None:
    owner = host().build_motif(0).evaluator()
    assert owner.truth(0).valid and not owner.truth(1).valid
    semantic = host().build_motif(4).evaluator()
    assert semantic.truth(0).valid and not semantic.truth(1).valid

    capability = host().build_motif(8).evaluator()
    assert capability.truth(0).decision.access_mode is AccessMode.OPEN
    assert capability.truth(0).valid
    assert capability.truth(1).decision.access_mode is AccessMode.GATED
    assert not capability.truth(1).valid

    content = host().build_motif(12).evaluator()
    assert content.truth(0).valid and not content.truth(1).valid

    active = host().build_motif(16).evaluator()
    assert active.truth(0).decision.request_active
    assert not active.truth(1).decision.request_active
    assert active.truth(1).oracle_action is Action.SAFE_FALLBACK

    retention = host().build_motif(28).evaluator()
    for base in (0, 8, 16):
        assert retention.truth(base).motif_side == "SETUP"
        assert retention.truth(base + 1).motif_side == "GAP1"
        assert retention.truth(base + 1).designated_comparison
        assert retention.truth(base + 6).motif_side == "GAP6"
        assert retention.truth(base + 6).designated_comparison
        assert not retention.truth(base + 2).designated_comparison


def test_b0_roots_counts_heldout_separation_and_arm_parity_are_exact() -> None:
    panel = build_b0_panel(host())
    assert panel.execution_count == 16
    assert sum(t.transition_count for t in panel.train) == 8 * 152
    assert sum(t.decision_count for t in panel.train) == 8 * 24
    assert tuple(t.identity.split for t in panel.train) == (TRAIN,) * 8
    assert tuple(t.identity.split for t in panel.eval_stochastic) == (EVAL_STOCHASTIC,) * 4
    assert tuple(t.identity.split for t in panel.eval_motif) == (EVAL_MOTIF,) * 4
    parity = primitive_history_parity(
        {
            "STRUCT": panel.train,
            "RAW": tuple(host().build_stochastic(TRAIN, index) for index in range(8)),
            "PI": tuple(host().build_stochastic(TRAIN, index) for index in range(8)),
            "DERANGED": tuple(host().build_stochastic(TRAIN, index) for index in range(8)),
        }
    )
    assert parity.passed and parity.episode_count == 8 and not parity.mismatches
