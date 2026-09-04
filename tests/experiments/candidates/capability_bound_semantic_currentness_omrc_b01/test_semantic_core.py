from __future__ import annotations

from dataclasses import fields, replace
from fractions import Fraction

import numpy as np
import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import (
    ABSENT_BYTE,
    CHANNEL_COUNT,
    EPISODE_TRANSITIONS,
    NEUTRAL_PAYLOAD_SOURCE,
    AccessMode,
    Action,
    BodySlot,
    ByteField,
    CanonicalTokenCodec,
    Carrier,
    CarrierState,
    Controller,
    DecisionPrimitive,
    EventKindLayout,
    FlagField,
    HostState,
    OpportunityPosition,
    PayloadRole,
    PrimitiveKind,
    PrimitiveToken,
    Receiver,
    ReceiverState,
    TokenValidationError,
    apply_native_action,
    evaluator_oracle_action,
    evaluator_valid,
    legal_action_mask,
    make_decision,
    native_ledger,
    transition_body,
    transition_capability,
    transition_owner,
    transition_semantic,
    validate_preactivation_order,
)


def initial_state() -> HostState:
    return HostState(
        receivers=(ReceiverState(16, 32, True), ReceiverState(17, 33, False)),
        bodies=(None, None),
        carriers=(CarrierState(Receiver.R0), CarrierState(Receiver.R1)),
    )


def test_clock_entities_actions_and_masks_are_exact() -> None:
    assert EPISODE_TRANSITIONS == 8 + 24 * 6 == 152
    assert tuple(Controller) == (Controller.C0,)
    assert tuple(Action) == (
        Action.WAIT,
        Action.SERVE,
        Action.REFRESH,
        Action.SAFE_FALLBACK,
    )
    assert legal_action_mask(PrimitiveKind.OWNER) == (True, False, False, False)
    assert legal_action_mask(PrimitiveKind.SETTLEMENT) == (True, False, False, False)
    assert legal_action_mask(PrimitiveKind.DECISION) == (False, True, True, True)
    assert OpportunityPosition.DECISION == 4
    assert OpportunityPosition.SETTLEMENT == 5
    validate_preactivation_order(
        (PrimitiveKind.BODY, PrimitiveKind.OWNER, PrimitiveKind.CAPABILITY, PrimitiveKind.SEMANTIC)
    )
    with pytest.raises(ValueError, match="exactly once"):
        validate_preactivation_order(
            (PrimitiveKind.BODY, PrimitiveKind.OWNER, PrimitiveKind.OWNER, PrimitiveKind.SEMANTIC)
        )


def test_pure_owner_semantic_capability_and_body_rules() -> None:
    state = initial_state()
    owner_state, owner_event = transition_owner(state, Receiver.R0, 18)
    assert state.receivers[0].current_owner == 16
    assert owner_event.old_owner == 16 and owner_state.receivers[0].current_owner == 18
    semantic_state, semantic_event = transition_semantic(owner_state, Receiver.R0, 34, False)
    assert semantic_event.old_need is True and semantic_event.new_need is False
    capability_state, _ = transition_capability(semantic_state, Carrier.C0, Receiver.R1)
    assert capability_state.carriers[0].permitted_receiver is Receiver.R1

    correct_state, _ = transition_body(
        capability_state, BodySlot.S0, Receiver.R0, Carrier.C0, PayloadRole.CORRECT
    )
    correct = correct_state.body(BodySlot.S0)
    assert (correct.issuance_owner, correct.issuance_epoch) == (18, 34)
    assert correct.payload_source_receiver is Receiver.R0 and correct.content is False

    swapped_state, _ = transition_body(
        correct_state, BodySlot.S1, Receiver.R0, Carrier.C1, PayloadRole.SWAPPED
    )
    swapped = swapped_state.body(BodySlot.S1)
    assert swapped.payload_source_receiver is Receiver.R1 and swapped.content is False

    neutral_state, _ = transition_body(
        swapped_state, BodySlot.S1, Receiver.R1, Carrier.C1, PayloadRole.NEUTRAL
    )
    neutral = neutral_state.body(BodySlot.S1)
    assert neutral.payload_source_receiver is None and neutral.native_neutral
    assert neutral.content is False


def valid_current_state() -> tuple[HostState, DecisionPrimitive]:
    state, _ = transition_body(
        initial_state(), BodySlot.S0, Receiver.R0, Carrier.C0, PayloadRole.CORRECT
    )
    decision = make_decision(
        state,
        opportunity_index=0,
        presented_slot=BodySlot.S0,
        target_receiver=Receiver.R0,
        access_mode=AccessMode.GATED,
        request_active=True,
    )
    return state, decision


def test_exact_capability_causal_twin_is_valid_open_and_invalid_gated() -> None:
    state, decision = valid_current_state()
    mismatch, _ = transition_capability(state, Carrier.C0, Receiver.R1)
    open_twin = replace(decision, access_mode=AccessMode.OPEN)
    gated_twin = replace(decision, access_mode=AccessMode.GATED)
    assert evaluator_valid(mismatch, open_twin)
    assert not evaluator_valid(mismatch, gated_twin)
    assert evaluator_oracle_action(mismatch, open_twin) is Action.SERVE
    assert evaluator_oracle_action(mismatch, gated_twin) is Action.REFRESH


def test_evaluator_valid_covers_currentness_receiver_content_and_neutrality() -> None:
    state, decision = valid_current_state()
    assert evaluator_valid(state, decision)
    stale_owner, _ = transition_owner(state, Receiver.R0, 18)
    assert not evaluator_valid(stale_owner, decision)
    stale_epoch, _ = transition_semantic(state, Receiver.R0, 34, True)
    assert not evaluator_valid(stale_epoch, decision)
    wrong_target = replace(decision, target_receiver=Receiver.R1, request_need=False)
    assert not evaluator_valid(state, wrong_target)
    neutral, _ = transition_body(
        state, BodySlot.S0, Receiver.R0, Carrier.C0, PayloadRole.NEUTRAL
    )
    assert not evaluator_valid(neutral, decision)
    with pytest.raises(ValueError, match="request_need"):
        evaluator_valid(state, replace(decision, request_need=False))


@pytest.mark.parametrize(
    ("active", "valid", "action", "decision_reward", "settlement_reward"),
    (
        (True, True, Action.SERVE, Fraction(1), Fraction(0)),
        (True, False, Action.SERVE, Fraction(-3, 10), Fraction(0)),
        (False, False, Action.SERVE, Fraction(-1, 10), Fraction(0)),
        (True, True, Action.REFRESH, Fraction(-2, 5), Fraction(1)),
        (False, False, Action.REFRESH, Fraction(-2, 5), Fraction(0)),
        (True, True, Action.SAFE_FALLBACK, Fraction(1, 5), Fraction(0)),
        (False, False, Action.SAFE_FALLBACK, Fraction(0), Fraction(0)),
    ),
)
def test_native_decision_and_settlement_ledger_is_exact_and_nonpersistent(
    active, valid, action, decision_reward, settlement_reward
) -> None:
    state, decision = valid_current_state()
    if not valid:
        state, _ = transition_capability(state, Carrier.C0, Receiver.R1)
    decision = replace(
        decision,
        request_active=active,
        request_need=state.receiver(Receiver.R0).current_need,
    )
    ledger = native_ledger(state, decision, action)
    assert ledger.decision_reward == decision_reward
    assert ledger.settlement_reward == settlement_reward
    assert ledger.undiscounted_total == decision_reward + settlement_reward
    next_state, applied = apply_native_action(state, decision, action)
    assert next_state is state and applied == ledger
    if action is Action.REFRESH:
        assert next_state.bodies == state.bodies


def test_wait_is_rejected_at_decision_and_oracle_is_unique() -> None:
    state, decision = valid_current_state()
    with pytest.raises(ValueError, match="WAIT"):
        native_ledger(state, decision, Action.WAIT)
    assert evaluator_oracle_action(state, decision) is Action.SERVE
    assert evaluator_oracle_action(state, replace(decision, request_active=False)) is Action.SAFE_FALLBACK


def explicit_codec() -> CanonicalTokenCodec:
    return CanonicalTokenCodec(
        (
            EventKindLayout(
                PrimitiveKind.OWNER,
                1,
                required_byte_fields=frozenset(
                    {
                        ByteField.SUBJECT_RECEIVER,
                        ByteField.OWNER_OLD,
                        ByteField.OWNER_NEW,
                        ByteField.OPPORTUNITY_INDEX,
                        ByteField.EVENT_ORDER_POSITION,
                    }
                ),
            ),
            EventKindLayout(
                PrimitiveKind.BODY,
                4,
                required_byte_fields=frozenset(
                    {
                        ByteField.SLOT,
                        ByteField.CARRIER,
                        ByteField.BODY_OWNER,
                        ByteField.BODY_EPOCH,
                        ByteField.BODY_ADDRESSED_RECEIVER,
                        ByteField.PAYLOAD_SOURCE_RECEIVER,
                        ByteField.OPPORTUNITY_INDEX,
                        ByteField.EVENT_ORDER_POSITION,
                    }
                ),
                allowed_flag_fields=frozenset(
                    {FlagField.BODY_CONTENT, FlagField.BODY_NATIVE_NEUTRAL}
                ),
            ),
        )
    )


def test_canonical_token_is_16_bytes_plus_flags_and_136_lsb_first_fp32_channels() -> None:
    codec = explicit_codec()
    token = PrimitiveToken(
        event_kind=1,
        subject_receiver=Receiver.R0,
        owner_old=16,
        owner_new=17,
        opportunity_index=0,
        event_order_position=2,
    )
    packed = codec.pack(token)
    assert len(packed) == 17
    assert packed[0] == 1
    assert packed[2] == ABSENT_BYTE
    channels = codec.encode_float32(token)
    assert channels.shape == (CHANNEL_COUNT,) and channels.dtype == np.float32
    np.testing.assert_array_equal(channels[:8], np.array([1, 0, 0, 0, 0, 0, 0, 0], np.float32))
    np.testing.assert_array_equal(
        channels[16:24], np.ones(8, dtype=np.float32)  # absent target byte is 255
    )
    assert codec.unpack(packed) == token


def test_token_sentinels_reserved_flag_and_event_kind_fields_are_strict() -> None:
    codec = explicit_codec()
    neutral = PrimitiveToken(
        event_kind=4,
        slot=0,
        carrier=0,
        body_owner=16,
        body_epoch=32,
        body_addressed_receiver=0,
        payload_source_receiver=NEUTRAL_PAYLOAD_SOURCE,
        opportunity_index=0,
        event_order_position=0,
        body_native_neutral=True,
    )
    assert codec.unpack(codec.pack(neutral)) == neutral
    with pytest.raises(TokenValidationError, match="neutral source"):
        replace(neutral, body_native_neutral=False)
    with pytest.raises(TokenValidationError, match="reserved_zero"):
        PrimitiveToken(event_kind=1, reserved_zero=True)
    illegal_owner = PrimitiveToken(
        event_kind=1,
        subject_receiver=0,
        owner_old=16,
        owner_new=17,
        slot=0,
        opportunity_index=0,
        event_order_position=0,
    )
    with pytest.raises(TokenValidationError, match="illegal for event kind"):
        codec.pack(illegal_owner)
    with pytest.raises(TokenValidationError, match="required fields"):
        codec.pack(PrimitiveToken(event_kind=1))
    with pytest.raises(TokenValidationError, match="external codebook"):
        codec.pack(PrimitiveToken(event_kind=7))


def test_external_layout_cannot_override_frozen_kind_clock_positions() -> None:
    position = frozenset({ByteField.EVENT_ORDER_POSITION})
    codec = CanonicalTokenCodec(
        (
            EventKindLayout(PrimitiveKind.PREAMBLE, 10, required_byte_fields=position),
            EventKindLayout(PrimitiveKind.OWNER, 11, required_byte_fields=position),
            EventKindLayout(PrimitiveKind.SEMANTIC, 12, required_byte_fields=position),
            EventKindLayout(PrimitiveKind.CAPABILITY, 13, required_byte_fields=position),
            EventKindLayout(PrimitiveKind.BODY, 14, required_byte_fields=position),
            EventKindLayout(PrimitiveKind.DECISION, 15, required_byte_fields=position),
            EventKindLayout(PrimitiveKind.SETTLEMENT, 16, required_byte_fields=position),
        )
    )
    accepted = ((10, 7), (11, 0), (12, 1), (13, 2), (14, 3), (15, 4), (16, 5))
    for code, event_position in accepted:
        codec.pack(PrimitiveToken(event_kind=code, event_order_position=event_position))
    rejected = ((11, 7), (12, 4), (13, 5), (14, 6), (15, 3), (16, 4))
    for code, event_position in rejected:
        with pytest.raises(TokenValidationError, match="illegal for"):
            codec.pack(PrimitiveToken(event_kind=code, event_order_position=event_position))
    with pytest.raises(TokenValidationError, match="invalid present value"):
        PrimitiveToken(event_kind=10, event_order_position=8)


def test_learner_projection_has_no_valid_oracle_reward_future_or_result_surface() -> None:
    codec = explicit_codec()
    token = PrimitiveToken(
        event_kind=1,
        subject_receiver=0,
        owner_old=16,
        owner_new=17,
        opportunity_index=0,
        event_order_position=0,
    )
    projection = codec.project_for_learner(token)
    assert tuple(field.name for field in fields(projection)) == ("packed",)
    prohibited = {
        "valid",
        "owner_live",
        "semantic_current",
        "receiver_correct",
        "capability_permitted",
        "oracle_action",
        "reward",
        "future_event",
        "arm",
        "seed",
        "result",
    }
    assert prohibited.isdisjoint(vars(token))
    assert prohibited.isdisjoint(vars(projection))
    assert set(np.unique(projection.float32_channels())) <= {0.0, 1.0}
