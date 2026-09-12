"""Changed public-row/adapter/ledger/publication contracts; no model or host RNG."""
from dataclasses import asdict
from fractions import Fraction
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.adapters import (
    RawHistoryAdapter, StructCurrentnessAdapter,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import B1_RUN_NAME
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import (
    Action, AccessMode, BodySlot, Carrier, EventKind, Receiver,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import DecisionTruth
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.state import (
    BodyRecord, CarrierState, HostState, ReceiverState, make_decision,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.tapes import EpisodeTape
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.token import (
    LITERAL_TOKEN_CODEC, PrimitiveToken,
)
from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04.direct_public import (
    DirectPublicHost, adapter_rows, native_record, pack_public, project_panel, request_only,
)
from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04.run import (
    native_record as original_native_record, pair_results, write_read,
)


def fixed_stream():
    """Hand-constructed legal stream; never calls build_stochastic or an RNG."""
    state = HostState(
        (ReceiverState(16, 20, False), ReceiverState(17, 21, True)),
        (BodyRecord(16, 20, Carrier.C0, Receiver.R0, Receiver.R0, False, False),
         BodyRecord(17, 21, Carrier.C1, Receiver.R1, Receiver.R1, True, False)),
        (CarrierState(Receiver.R0), CarrierState(Receiver.R1)),
    )
    host = DirectPublicHost(B1_RUN_NAME, -1)
    tokens = [
        PrimitiveToken(EventKind.INIT_OWNER, subject_receiver=r, owner_new=16+r,
                       event_order_position=r) for r in range(2)
    ] + [
        PrimitiveToken(EventKind.INIT_SEMANTIC, subject_receiver=r, epoch_new=20+r,
                       event_order_position=2+r, new_need=bool(r)) for r in range(2)
    ] + [
        PrimitiveToken(EventKind.INIT_CAPABILITY, carrier=c, capability_receiver=c,
                       event_order_position=4+c) for c in range(2)
    ] + [host._body_token(state, BodySlot(s), True, -1, 6+s) for s in range(2)]
    truth = []
    for q in range(24):
        codes = (EventKind.NOOP_OWNER, EventKind.NOOP_SEMANTIC,
                 EventKind.NOOP_CAPABILITY, EventKind.NOOP_BODY)
        tokens.extend(PrimitiveToken(kind, opportunity_index=q, event_order_position=p)
                      for p, kind in enumerate(codes))
        decision = make_decision(
            state, opportunity_index=q, presented_slot=BodySlot(q % 2),
            target_receiver=Receiver(q % 2),
            access_mode=AccessMode.GATED if q % 3 else AccessMode.OPEN,
            request_active=q % 2 == 0,
        )
        tokens.extend((host._decision_token(state, decision), host._settlement(q)))
        truth.append(DecisionTruth(state, decision, codes))
    direct = host._finish(
        "TRAIN", 0, tokens, truth,
        SimpleNamespace(owner_cursor=2, epoch_cursor=2),
        SimpleNamespace(addresses=(), audit_digest=lambda: "fixed-nonrandom-fixture"),
    )
    return tuple(tokens), direct


def test_public_rows_and_all_literal_event_forms():
    tokens, direct = fixed_stream()
    extra = (
        PrimitiveToken(EventKind.OWNER, subject_receiver=0, owner_old=16, owner_new=18,
                       opportunity_index=0, event_order_position=0),
        PrimitiveToken(EventKind.SEMANTIC, subject_receiver=1, epoch_old=21, epoch_new=22,
                       opportunity_index=0, event_order_position=1, old_need=True, new_need=False),
        PrimitiveToken(EventKind.CAPABILITY, carrier=0, capability_receiver=1,
                       opportunity_index=0, event_order_position=2),
        PrimitiveToken(EventKind.BODY, slot=0, carrier=1, body_owner=18, body_epoch=22,
                       body_addressed_receiver=0, payload_source_receiver=254,
                       opportunity_index=0, event_order_position=3, body_native_neutral=True),
    )
    for token in tokens + extra:
        assert pack_public(token) == LITERAL_TOKEN_CODEC.pack(token)
    assert {int(t.event_kind) for t in tokens + extra} == set(
        range(1, 5)) | set(range(0x10, 0x18)) | {0x20, 0x21}
    assert direct.public_rows == tuple(pack_public(token) for token in tokens)
    with pytest.raises(ValueError, match="presence"):
        pack_public(PrimitiveToken(EventKind.OWNER, subject_receiver=0,
                                   opportunity_index=0, event_order_position=0))
    with pytest.raises(ValueError, match="flag"):
        pack_public(PrimitiveToken(EventKind.NOOP_BODY, opportunity_index=0,
                                   event_order_position=3, request_active=True))


@pytest.mark.parametrize("arm,reference", [
    ("RAW-GRU", RawHistoryAdapter), ("STRUCT-CURRENTNESS-GRU", StructCurrentnessAdapter),
])
def test_adapter_bits_tensor_ownership_and_episode_reset(arm, reference):
    tokens, direct = fixed_stream()
    expected_adapter = reference()
    expected = tuple(expected_adapter.process(token) for token in tokens)
    emitted, work = adapter_rows(direct.public_rows, arm)
    assert emitted == tuple(row.packed for row in expected)
    assert work == expected_adapter.total_work
    changed = tokens[:8] + (
        PrimitiveToken(EventKind.OWNER, subject_receiver=0, owner_old=16, owner_new=18,
                       opportunity_index=0, event_order_position=0),
        PrimitiveToken(EventKind.SEMANTIC, subject_receiver=1, epoch_old=21, epoch_new=22,
                       opportunity_index=0, event_order_position=1, old_need=True),
        tokens[12], tokens[18],
    )
    updated_reference = reference()
    updated_expected = tuple(updated_reference.process(token).packed for token in changed)
    updated_actual, updated_work = adapter_rows(tuple(pack_public(t) for t in changed), arm)
    assert updated_actual == updated_expected
    assert updated_work == updated_reference.total_work
    # Projection receives only public rows: there is no evaluator attribute to read.
    public_only = SimpleNamespace(public_rows=direct.public_rows)
    actual, panel_work = project_panel((public_only,) * 8, arm)
    expected_rows = []
    for token, adapter in zip(tokens, expected, strict=True):
        raw = LITERAL_TOKEN_CODEC.project_for_learner(token).float32_channels().tolist()
        expected_rows.append(raw + adapter.float32_channels().tolist())
    reference_tensor = torch.tensor(expected_rows, dtype=torch.float32)
    assert actual.shape == (8, 152, 168) and actual.dtype == torch.float32
    assert actual.device.type == "cpu"
    for batch in range(8):
        assert torch.equal(actual[batch], reference_tensor)
    assert panel_work == sum((work for _ in range(8)), start=type(work)())
    saved_rows = direct.public_rows
    actual[0].fill_(9)
    assert torch.equal(actual[1], reference_tensor)
    assert direct.public_rows is saved_rows


def test_native_ledger_settlement_and_public_rule():
    tokens, direct = fixed_stream()
    canonical = EpisodeTape(direct.identity, tokens, direct.public_rows,
                            direct._decision_truth, direct.generation_audit)
    names = [("SERVE", "REFRESH", "SAFE_FALLBACK")[q % 3] for q in range(24)]
    result = native_record(direct, names)
    assert result == original_native_record(canonical, names)
    expected_decision = Fraction(0)
    expected_settlement = Fraction(0)
    for q, name in enumerate(names):
        active = q % 2 == 0
        expected_decision += (
            (Fraction(1) if active else Fraction(-1, 10)) if name == "SERVE"
            else Fraction(-2, 5) if name == "REFRESH"
            else Fraction(1, 5) if active else Fraction(0)
        )
        if name == "REFRESH" and active:
            expected_settlement += 1
    assert result["decision_sum"]["float"] == float(expected_decision)
    assert result["settlement_sum"]["float"] == float(expected_settlement)
    assert result["native_return"]["float"] == float(expected_decision + expected_settlement)
    assert request_only(direct.public_rows) == ["REFRESH", "SAFE_FALLBACK"] * 12
    refresh = native_record(direct, ["REFRESH"] * 24)
    assert refresh["contributions"][-1]["decision_reward"]["float"] == -0.4
    assert refresh["contributions"][-1]["settlement_reward"]["float"] == 0.0
    with pytest.raises(ValueError):
        native_record(direct, ["WAIT"] * 24)


def test_new_native_records_survive_pair_publication(tmp_path):
    _, tape = fixed_stream()
    raw_rows = [native_record(tape, ["REFRESH"] * 24) for _ in range(32)]
    struct_rows = [native_record(tape, request_only(tape.public_rows)) for _ in range(32)]
    for e, (raw, struct) in enumerate(zip(raw_rows, struct_rows, strict=True)):
        raw["identity"]["episode_id"] = e
        struct["identity"]["episode_id"] = e
    common = {
        "object": "PUBLIC_STREAM_FIXTURE_ONLY", "seed": -1, "rng_namespace": B1_RUN_NAME,
        "profile": "NONLEARNING_CONTRACT_CHECK", "configuration": {},
        "initialization_digest": "no-model", "training_tape_digest": "no-training",
        "evaluation_tape_digest": "constructed", "updates": 48, "eval_episodes": 32,
        "counters": {"adam_steps": 0}, "minibatch_order_digest": "no-rng",
        "action_uniform_digest": "no-rng", "context": {}, "curve": [],
        "request_only_comparison": {}, "launch_sha": "fixture-only",
    }
    raw = {**common, "arm": "RAW-GRU", "evaluations": [{"update": 48, "episodes": raw_rows}]}
    struct = {**common, "arm": "STRUCT-CURRENTNESS-GRU",
              "evaluations": [{"update": 48, "episodes": struct_rows}]}
    paired = pair_results(raw, struct)
    reread = write_read(tmp_path / "paired_summary.json", paired)
    assert len(reread["differences"]) == 32
    assert reread["mean_difference"]["float"] == 4.8
    assert [r["identity"]["episode_id"] for r in reread["differences"]] == list(range(32))
    struct["evaluations"][0]["episodes"][31]["identity"]["episode_id"] = 100
    with pytest.raises(ValueError, match="endpoint tapes"):
        pair_results(raw, struct)
