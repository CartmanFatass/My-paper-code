"""TEST_ONLY: bounded, non-learning replay of the P32 adapter/projection path.

Run from the repository root with python -X faulthandler <this file>.
Synthetic public tokens only: no host RNG, scientific seed, model or evaluator.
"""

from dataclasses import replace
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.adapters import (
    AdapterWorkReceipt, RawHistoryAdapter,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import EventKind as K
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.token import (
    LITERAL_TOKEN_CODEC, LearnerProjection, PrimitiveToken as T,
)


# Literal masks independently pinned by the existing codec/adapter tests.
MASKS = {
    K.INIT_OWNER: (0x8043, 0), K.INIT_SEMANTIC: (0x8103, 2),
    K.INIT_CAPABILITY: (0xA011, 0), K.INIT_BODY: (0x9E19, 12),
    K.OWNER: (0xC063, 0), K.SEMANTIC: (0xC183, 3),
    K.CAPABILITY: (0xE011, 0), K.BODY: (0xDE19, 12),
    K.NOOP_OWNER: (0xC001, 0), K.NOOP_SEMANTIC: (0xC001, 0),
    K.NOOP_CAPABILITY: (0xC001, 0), K.NOOP_BODY: (0xC001, 0),
    K.DECISION: (0xFE1D, 124), K.SETTLEMENT: (0xC001, 0),
}


def fixture():
    preamble = (
        T(K.INIT_OWNER, subject_receiver=0, owner_new=16, event_order_position=0),
        T(K.INIT_OWNER, subject_receiver=1, owner_new=17, event_order_position=1),
        T(K.INIT_SEMANTIC, subject_receiver=0, epoch_new=32, event_order_position=2, new_need=True),
        T(K.INIT_SEMANTIC, subject_receiver=1, epoch_new=33, event_order_position=3),
        T(K.INIT_CAPABILITY, carrier=0, capability_receiver=0, event_order_position=4),
        T(K.INIT_CAPABILITY, carrier=1, capability_receiver=1, event_order_position=5),
        T(K.INIT_BODY, slot=0, carrier=0, body_owner=16, body_epoch=32,
          body_addressed_receiver=0, payload_source_receiver=0, event_order_position=6, body_content=True),
        T(K.INIT_BODY, slot=1, carrier=1, body_owner=17, body_epoch=33,
          body_addressed_receiver=1, payload_source_receiver=254, event_order_position=7, body_native_neutral=True),
    )
    active = (
        T(K.OWNER, subject_receiver=0, owner_old=16, owner_new=18, opportunity_index=0, event_order_position=0),
        T(K.SEMANTIC, subject_receiver=0, epoch_old=32, epoch_new=34, opportunity_index=0, event_order_position=1, old_need=True),
        T(K.CAPABILITY, carrier=0, capability_receiver=1, opportunity_index=0, event_order_position=2),
        T(K.BODY, slot=0, carrier=1, body_owner=16, body_epoch=32,
          body_addressed_receiver=0, payload_source_receiver=1, opportunity_index=0, event_order_position=3),
    )
    noop = tuple(T(kind, opportunity_index=0, event_order_position=i) for i, kind in enumerate(
        (K.NOOP_OWNER, K.NOOP_SEMANTIC, K.NOOP_CAPABILITY, K.NOOP_BODY)))
    decision = T(K.DECISION, target_receiver=0, slot=0, carrier=0, body_owner=16,
                 body_epoch=32, body_addressed_receiver=0, payload_source_receiver=0,
                 capability_receiver=0, opportunity_index=0, event_order_position=4,
                 body_content=True, access_gated=True, request_active=True, request_need=True)
    tokens = preamble + tuple(
        replace(token, opportunity_index=i)
        for i in range(24)
        for token in ((active if i % 2 else noop) + (decision, T(K.SETTLEMENT, opportunity_index=0, event_order_position=5)))
    )
    packed = tuple(LITERAL_TOKEN_CODEC.pack(token) for token in tokens)
    return SimpleNamespace(public_tokens=tokens, learner_tokens=lambda: tuple(LearnerProjection(p) for p in packed)), packed


def test_raw_native_replay():
    print("TEST_ONLY adapter replay start", sys.version, flush=True)
    tape, packed = fixture()
    assert len(packed) == 152 and {K(t.event_kind) for t in tape.public_tokens} == set(K)
    expected, counts, stream = [], [], bytes([255] * 4)
    for token, public in zip(tape.public_tokens, packed, strict=True):
        mask, flags = MASKS[K(token.event_kind)]
        selected = bytes(public[i] for i in range(16) if mask & (1 << i))
        selected += public[16:] if flags else b""
        stream += selected
        expected.append(stream[-4:])
        counts.append(len(selected))
    for episode in range(32):
        adapter = RawHistoryAdapter()
        emissions = adapter.replay(tape.public_tokens)
        assert tuple(e.packed for e in emissions) == tuple(expected), episode
        assert tuple(e.work for e in emissions) == tuple(AdapterWorkReceipt(appended_bytes=n) for n in counts)
        assert adapter.state == tuple(expected[-1])
        assert adapter.total_work == AdapterWorkReceipt(appended_bytes=sum(counts))
    assert tuple(LITERAL_TOKEN_CODEC.pack(t) for t in tape.public_tokens) == packed
    print("TEST_ONLY adapter bytes/work/immutability PASS: 32 x 152 tokens", flush=True)

    from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.engine import _project_panel
    import torch

    torch.set_num_threads(1)
    observations, work = _project_panel((tape,) * 32, RawHistoryAdapter)
    reference = torch.tensor([
        [(value >> bit) & 1 for value in public + history for bit in range(8)]
        for public, history in zip(packed, expected, strict=True)
    ], dtype=torch.float32)
    assert observations.shape == (32, 152, 168) and observations.dtype == torch.float32
    assert torch.equal(observations, reference.unsqueeze(0).expand(32, -1, -1))
    assert work == AdapterWorkReceipt(appended_bytes=32 * sum(counts))
    assert tuple(LITERAL_TOKEN_CODEC.pack(t) for t in tape.public_tokens) == packed
    print("TEST_ONLY projection/replay/FP32 channels PASS: 32 x 2 x 152 tokens; torch", torch.__version__, flush=True)


if __name__ == "__main__":
    test_raw_native_replay()
