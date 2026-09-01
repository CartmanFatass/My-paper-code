from __future__ import annotations

from dataclasses import fields, replace
from inspect import signature

import numpy as np
import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.adapters import (
    ADAPTER_CHANNEL_COUNT,
    AdapterEmission,
    DerangedCurrentnessAdapter,
    PredictiveIndexAdapter,
    RawHistoryAdapter,
    StructCurrentnessAdapter,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import EventKind
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.token import (
    ABSENT_BYTE,
    CHANNEL_COUNT,
    LITERAL_EVENT_LAYOUTS,
    LITERAL_TOKEN_CODEC,
    NEUTRAL_PAYLOAD_SOURCE,
    PrimitiveToken,
    TokenValidationError,
)


EXPECTED_MASKS = {
    EventKind.INIT_OWNER: (0x8043, 0x00),
    EventKind.INIT_SEMANTIC: (0x8103, 0x02),
    EventKind.INIT_CAPABILITY: (0xA011, 0x00),
    EventKind.INIT_BODY: (0x9E19, 0x0C),
    EventKind.OWNER: (0xC063, 0x00),
    EventKind.SEMANTIC: (0xC183, 0x03),
    EventKind.CAPABILITY: (0xE011, 0x00),
    EventKind.BODY: (0xDE19, 0x0C),
    EventKind.NOOP_OWNER: (0xC001, 0x00),
    EventKind.NOOP_SEMANTIC: (0xC001, 0x00),
    EventKind.NOOP_CAPABILITY: (0xC001, 0x00),
    EventKind.NOOP_BODY: (0xC001, 0x00),
    EventKind.DECISION: (0xFE1D, 0x7C),
    EventKind.SETTLEMENT: (0xC001, 0x00),
}


def preamble() -> tuple[PrimitiveToken, ...]:
    return (
        PrimitiveToken(EventKind.INIT_OWNER, subject_receiver=0, owner_new=16, event_order_position=0),
        PrimitiveToken(EventKind.INIT_OWNER, subject_receiver=1, owner_new=17, event_order_position=1),
        PrimitiveToken(
            EventKind.INIT_SEMANTIC,
            subject_receiver=0,
            epoch_new=32,
            event_order_position=2,
            new_need=True,
        ),
        PrimitiveToken(
            EventKind.INIT_SEMANTIC,
            subject_receiver=1,
            epoch_new=33,
            event_order_position=3,
        ),
        PrimitiveToken(
            EventKind.INIT_CAPABILITY,
            carrier=0,
            capability_receiver=0,
            event_order_position=4,
        ),
        PrimitiveToken(
            EventKind.INIT_CAPABILITY,
            carrier=1,
            capability_receiver=1,
            event_order_position=5,
        ),
        PrimitiveToken(
            EventKind.INIT_BODY,
            slot=0,
            carrier=0,
            body_owner=16,
            body_epoch=32,
            body_addressed_receiver=0,
            payload_source_receiver=0,
            event_order_position=6,
            body_content=True,
        ),
        PrimitiveToken(
            EventKind.INIT_BODY,
            slot=1,
            carrier=1,
            body_owner=17,
            body_epoch=33,
            body_addressed_receiver=1,
            payload_source_receiver=NEUTRAL_PAYLOAD_SOURCE,
            event_order_position=7,
            body_native_neutral=True,
        ),
    )


def opportunity_zero() -> tuple[PrimitiveToken, ...]:
    return (
        PrimitiveToken(EventKind.NOOP_OWNER, opportunity_index=0, event_order_position=0),
        PrimitiveToken(EventKind.NOOP_SEMANTIC, opportunity_index=0, event_order_position=1),
        PrimitiveToken(EventKind.NOOP_CAPABILITY, opportunity_index=0, event_order_position=2),
        PrimitiveToken(EventKind.NOOP_BODY, opportunity_index=0, event_order_position=3),
        PrimitiveToken(
            EventKind.DECISION,
            target_receiver=0,
            slot=0,
            carrier=0,
            body_owner=16,
            body_epoch=32,
            body_addressed_receiver=0,
            payload_source_receiver=0,
            capability_receiver=0,
            opportunity_index=0,
            event_order_position=4,
            body_content=True,
            access_gated=True,
            request_active=True,
            request_need=True,
        ),
        PrimitiveToken(EventKind.SETTLEMENT, opportunity_index=0, event_order_position=5),
    )


def every_kind_token() -> dict[EventKind, PrimitiveToken]:
    initial = preamble()
    tokens = {
        EventKind.INIT_OWNER: initial[0],
        EventKind.INIT_SEMANTIC: initial[2],
        EventKind.INIT_CAPABILITY: initial[4],
        EventKind.INIT_BODY: initial[6],
    }
    tokens.update(
        {
            EventKind.OWNER: PrimitiveToken(
                EventKind.OWNER,
                subject_receiver=0,
                owner_old=16,
                owner_new=18,
                opportunity_index=0,
                event_order_position=0,
            ),
            EventKind.SEMANTIC: PrimitiveToken(
                EventKind.SEMANTIC,
                subject_receiver=0,
                epoch_old=32,
                epoch_new=34,
                opportunity_index=0,
                event_order_position=1,
                old_need=True,
            ),
            EventKind.CAPABILITY: PrimitiveToken(
                EventKind.CAPABILITY,
                carrier=0,
                capability_receiver=1,
                opportunity_index=0,
                event_order_position=2,
            ),
            EventKind.BODY: PrimitiveToken(
                EventKind.BODY,
                slot=0,
                carrier=1,
                body_owner=16,
                body_epoch=32,
                body_addressed_receiver=0,
                payload_source_receiver=1,
                opportunity_index=0,
                event_order_position=3,
            ),
        }
    )
    tokens.update({EventKind(token.event_kind): token for token in opportunity_zero()})
    return tokens


def test_literal_codes_masks_and_every_kind_round_trip() -> None:
    assert {kind: int(kind) for kind in EventKind} == {
        kind: code
        for kind, code in zip(
            EventKind,
            (0x01, 0x02, 0x03, 0x04, 0x10, 0x11, 0x12, 0x13,
             0x14, 0x15, 0x16, 0x17, 0x20, 0x21),
        )
    }
    assert {layout.kind: (layout.bmask, layout.fmask) for layout in LITERAL_EVENT_LAYOUTS} == EXPECTED_MASKS
    tokens = every_kind_token()
    assert set(tokens) == set(EventKind)
    for kind, token in tokens.items():
        packed = LITERAL_TOKEN_CODEC.pack(token)
        assert len(packed) == 17 and packed[0] == kind
        assert LITERAL_TOKEN_CODEC.unpack(packed) == token


def test_literal_17_byte_to_136_lsb_fp32_projection() -> None:
    token = preamble()[0]
    packed = LITERAL_TOKEN_CODEC.pack(token)
    channels = LITERAL_TOKEN_CODEC.encode_float32(token)
    assert channels.shape == (CHANNEL_COUNT,) and channels.dtype == np.float32
    assert set(np.unique(channels)) <= {0.0, 1.0}
    np.testing.assert_array_equal(
        channels,
        np.array([(byte >> bit) & 1 for byte in packed for bit in range(8)], dtype=np.float32),
    )


def test_illegal_fields_flags_sentinels_and_positions_are_rejected() -> None:
    owner = every_kind_token()[EventKind.OWNER]
    with pytest.raises(TokenValidationError, match="illegal for event kind"):
        LITERAL_TOKEN_CODEC.pack(replace(owner, slot=0))
    with pytest.raises(TokenValidationError, match="flags are illegal"):
        LITERAL_TOKEN_CODEC.pack(replace(owner, request_active=True))
    with pytest.raises(TokenValidationError, match="opportunity/position"):
        LITERAL_TOKEN_CODEC.pack(replace(owner, event_order_position=4))
    with pytest.raises(TokenValidationError, match="opportunity/position"):
        LITERAL_TOKEN_CODEC.pack(replace(preamble()[0], event_order_position=1))
    with pytest.raises(TokenValidationError, match="required fields"):
        LITERAL_TOKEN_CODEC.pack(PrimitiveToken(EventKind.DECISION))
    with pytest.raises(TokenValidationError, match="neutral source"):
        replace(preamble()[-1], body_native_neutral=False)
    with pytest.raises(TokenValidationError, match="external codebook"):
        LITERAL_TOKEN_CODEC.pack(PrimitiveToken(0x30))


@pytest.mark.parametrize(
    ("kind", "expected"),
    (
        (EventKind.INIT_OWNER, bytes((1, 0, 16, 0))),
        (EventKind.INIT_SEMANTIC, bytes((0, 32, 2, 2))),
        (EventKind.INIT_CAPABILITY, bytes((3, 0, 0, 4))),
        (EventKind.INIT_BODY, bytes((0, 0, 6, 4))),
        (EventKind.OWNER, bytes((16, 18, 0, 0))),
        (EventKind.SEMANTIC, bytes((34, 0, 1, 1))),
        (EventKind.CAPABILITY, bytes((0, 1, 0, 2))),
        (EventKind.BODY, bytes((1, 0, 3, 0))),
        (EventKind.NOOP_OWNER, bytes((255, 20, 0, 0))),
        (EventKind.NOOP_SEMANTIC, bytes((255, 21, 0, 1))),
        (EventKind.NOOP_CAPABILITY, bytes((255, 22, 0, 2))),
        (EventKind.NOOP_BODY, bytes((255, 23, 0, 3))),
        (EventKind.DECISION, bytes((0, 0, 4, 116))),
        (EventKind.SETTLEMENT, bytes((255, 33, 0, 5))),
    ),
)
def test_raw_literal_append_sequence_per_kind(kind: EventKind, expected: bytes) -> None:
    emission = RawHistoryAdapter().process(every_kind_token()[kind])
    assert emission.packed == expected


def test_struct_deranged_replay_and_exact_work_parity() -> None:
    tokens = preamble() + opportunity_zero()
    struct = StructCurrentnessAdapter()
    deranged = DerangedCurrentnessAdapter()
    struct_outputs = struct.replay(tokens)
    deranged_outputs = deranged.replay(tokens)
    assert struct.state == (16, 17, 32, 33)
    assert deranged.state == (33, 32, 17, 16)
    decision_index = len(preamble()) + 4
    assert struct_outputs[decision_index].packed == bytes((16, 32, 0, 0))
    assert deranged_outputs[decision_index].packed == bytes((33, 17, 49, 49))
    assert [item.work for item in struct_outputs] == [item.work for item in deranged_outputs]
    assert struct.total_work == deranged.total_work
    assert struct_outputs[decision_index].work.byte_reads == 4
    assert struct_outputs[decision_index].work.uint8_xors == 2


def test_pi_boundary_age_and_same_opportunity_body_timing() -> None:
    pi = PredictiveIndexAdapter()
    pi.replay(preamble())
    assert pi.state == (1, 0, 0, 0)
    tokens = list(opportunity_zero())
    first = pi.process(tokens[0])
    assert first.packed == bytes((1, 1, 0, 1))
    pi.process(tokens[1])
    pi.process(tokens[2])
    body = PrimitiveToken(
        EventKind.BODY,
        slot=0,
        carrier=0,
        body_owner=16,
        body_epoch=32,
        body_addressed_receiver=0,
        payload_source_receiver=0,
        opportunity_index=0,
        event_order_position=3,
        body_content=True,
    )
    assert pi.process(body).packed == bytes((1, 0, 0, 1))
    assert pi.process(tokens[4]).packed == bytes((1, 0, 0, 1))
    assert pi.process(tokens[5]).packed == bytes((1, 0, 0, 1))


def test_adapter_outputs_are_32_lsb_fp32_and_have_no_privileged_input_surface() -> None:
    token = preamble()[0]
    prohibited = {"reward", "valid", "oracle", "future", "arm", "seed", "result"}
    for adapter_type in (
        RawHistoryAdapter,
        StructCurrentnessAdapter,
        PredictiveIndexAdapter,
        DerangedCurrentnessAdapter,
    ):
        assert tuple(signature(adapter_type.process).parameters) == ("self", "token")
        assert prohibited.isdisjoint(field.name for field in fields(AdapterEmission))
        emission = adapter_type().process(token)
        channels = emission.float32_channels()
        assert channels.shape == (ADAPTER_CHANNEL_COUNT,) and channels.dtype == np.float32
        np.testing.assert_array_equal(
            channels,
            np.array(
                [(byte >> bit) & 1 for byte in emission.packed for bit in range(8)],
                dtype=np.float32,
            ),
        )
        assert ABSENT_BYTE in adapter_type().state
