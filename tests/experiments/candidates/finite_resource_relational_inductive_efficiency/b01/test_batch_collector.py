from __future__ import annotations

import dataclasses
import json
import struct
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
from experiments.candidates.finite_resource_relational_inductive_efficiency.host import native_endpoint
from experiments.candidates.finite_resource_relational_inductive_efficiency.native.native_abi import STATE_SIZE
from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import (
    FRRIEActorCritic, LEGAL_ACTION_INDICES, TORCH_AVAILABLE,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
from experiments.candidates.finite_resource_relational_inductive_efficiency.training import rscf_batch_loss
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import batch_collector as collector
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.batch_collector import (
    actor_scalar_batch_equivalence, make_test_update_inputs,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import TEST_SEED_LABELS
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import B01ContractError
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.native_batch import (
    BatchObservation, BatchStep, BatchWorkLedger, NativePrimitives, _LEDGER_TOKEN,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.trainer import (
    assert_common_exogenous_and_work, assert_paired_episode_information,
    assert_precontact_observation_equality,
)


pytestmark = pytest.mark.skipif(not TORCH_AVAILABLE, reason="Torch is required")


def _model():
    arm, _ = initialize_paired_arms(
        AddressedRNG(b"B" * 32), "FRRIE-B01-TEST-BATCH-COLLECTOR",
    )
    return FRRIEActorCritic(arm)


def _inputs(torch, *, lanes=4, roster=9):
    observations = torch.linspace(
        -0.75, 0.75, lanes * roster * 22, dtype=torch.float32,
    ).reshape(lanes, roster, 22)
    roles = torch.tensor(
        [[0] * (roster // 3) + [1] * (roster // 3) + [2] * (roster // 3)] * lanes,
        dtype=torch.int64,
    )
    hidden = torch.linspace(
        -0.1, 0.1, lanes * roster * 64, dtype=torch.float32,
    ).reshape(lanes, roster, 64)
    uniforms = torch.linspace(
        0.01, 0.99, lanes * roster, dtype=torch.float32,
    ).reshape(lanes, roster)
    return observations, roles, hidden, uniforms


def test_batched_actor_critic_actions_and_twelve_slot_recurrence_are_bit_exact():
    import torch

    torch.set_num_threads(1)
    model = _model()
    observations, roles, batch_hidden, uniforms = _inputs(torch)
    initial = actor_scalar_batch_equivalence(
        model=model, observations=observations, roles=roles,
        hidden=batch_hidden, uniforms=uniforms,
    )
    assert initial["direct_bit_equal"] is True
    scalar_hidden = [batch_hidden[lane].clone() for lane in range(4)]
    with torch.no_grad():
        for slot in range(12):
            frame = observations + np.float32(slot / 32.0)
            batch = model.actor_step_batch(frame, roles, batch_hidden)
            batch_actions = model.actions_from_uniforms_batch(batch.probabilities, uniforms)
            scalar = [
                model.actor_step(frame[lane], roles[lane], scalar_hidden[lane])
                for lane in range(4)
            ]
            assert torch.equal(batch.hidden, torch.stack([row.hidden for row in scalar]))
            assert torch.equal(
                batch.probabilities, torch.stack([row.probabilities for row in scalar]),
            )
            assert torch.equal(
                batch_actions,
                torch.stack([
                    model.actions_from_uniforms(row.probabilities, uniforms[lane])
                    for lane, row in enumerate(scalar)
                ]),
            )
            batch_hidden = batch.hidden
            scalar_hidden = [row.hidden for row in scalar]


def test_test_and_production_seed_namespaces_reject_each_other_and_prefix_alias():
    tapes, origins = make_test_update_inputs(
        b"I" * 32, seed_label=TEST_SEED_LABELS[0], update=1,
    )
    assert len(tapes) == len(origins) == 64
    assert tuple(tape.roster for tape in tapes) == (9, 15) * 32
    with pytest.raises(B01ContractError, match="TEST-only namespace"):
        make_test_update_inputs(
            b"I" * 32, seed_label="FRRIE-B01-FRESH-BLOCK-001", update=1,
        )
    with pytest.raises(B01ContractError, match="TRAIN tape differs"):
        collector._validate_tapes(tapes, update=1)
    production_alias = list(tapes)
    production_alias[0] = dataclasses.replace(
        production_alias[0], seed_block="FRRIE-B01-FRESH-BLOCK-001",
    )
    with pytest.raises(B01ContractError, match="TRAIN tape differs"):
        collector._validate_tapes(
            production_alias, update=1, allowed_seed_labels=TEST_SEED_LABELS,
        )
    aliased = list(tapes)
    aliased[0] = dataclasses.replace(
        aliased[0], seed_block="FRRIE-B01-UNREGISTERED-ALIAS",
    )
    with pytest.raises(B01ContractError, match="TRAIN tape differs"):
        collector._validate_tapes(
            aliased, update=1, allowed_seed_labels=TEST_SEED_LABELS,
        )


class _FakeBatchEnvironment:
    """Deterministic TEST ABI double; all calls still operate on whole lanes."""

    def __init__(self, adapter, *, roster, lanes):
        del adapter
        self.roster, self.lanes = roster, lanes
        self.slots = np.zeros(lanes, dtype=np.int32)
        self.scores = np.zeros(lanes, dtype=np.int32)
        self.previous = np.full((lanes, roster), 255, dtype=np.uint8)
        self.success = np.zeros((lanes, roster), dtype=np.bool_)
        self.reset_calls = self.observe_calls = self.step_calls = self.environment_slots = 0

    def reset(self, tapes):
        assert len(tapes) == self.lanes
        self.slots.fill(0)
        self.scores.fill(0)
        self.previous.fill(255)
        self.success.fill(False)
        self.reset_calls += 1

    def _lane_bytes(self, lane):
        row = bytearray(STATE_SIZE)
        struct.pack_into("<ii", row, 0, int(self.slots[lane]), int(self.scores[lane]))
        row[8:8 + self.roster] = self.previous[lane].tobytes()
        row[32:32 + self.roster] = self.success[lane].astype(np.uint8).tobytes()
        return bytes(row)

    def snapshot(self):
        return b"".join(self._lane_bytes(lane) for lane in range(self.lanes))

    def restore(self, snapshot):
        assert len(snapshot) == STATE_SIZE * self.lanes
        for lane in range(self.lanes):
            row = snapshot[lane * STATE_SIZE:(lane + 1) * STATE_SIZE]
            self.slots[lane], self.scores[lane] = struct.unpack_from("<ii", row, 0)
            self.previous[lane] = np.frombuffer(
                row[8:8 + self.roster], dtype=np.uint8,
            )
            self.success[lane] = np.frombuffer(
                row[32:32 + self.roster], dtype=np.uint8,
            ).astype(np.bool_)

    def observe(self):
        roles = np.broadcast_to(
            np.repeat(np.arange(3, dtype=np.int64), self.roster // 3),
            (self.lanes, self.roster),
        ).copy()
        observations = np.zeros((self.lanes, self.roster, 22), dtype=np.float32)
        masks = np.zeros((self.lanes, self.roster, 6), dtype=np.bool_)
        for lane in range(self.lanes):
            observations[lane, np.arange(self.roster), roles[lane]] = 1.0
            observations[lane, :, 3] = np.float32(self.slots[lane] / 11.0)
            observations[lane, :, 4:7] = np.float32((self.roster // 3) / 7.0)
            for entity, role in enumerate(roles[lane]):
                masks[lane, entity, list(LEGAL_ACTION_INDICES[int(role)])] = True
                action = int(self.previous[lane, entity])
                if action < 6:
                    observations[lane, entity, 15 + action] = 1.0
            observations[lane, :, 21] = self.success[lane]
        self.observe_calls += 1
        return BatchObservation(
            observations, roles, masks, tuple(map(int, self.slots)),
            tuple(bool(slot == 12) for slot in self.slots),
        )

    def step(self, actions):
        values = np.asarray(actions, dtype=np.int64)
        assert values.shape == (self.lanes, self.roster)
        roles = np.repeat(np.arange(3, dtype=np.int64), self.roster // 3)
        terminals, returns, primitives = [], [], []
        for lane in range(self.lanes):
            for entity, action in enumerate(values[lane]):
                assert int(action) in LEGAL_ACTION_INDICES[int(roles[entity])]
            self.scores[lane] += int(values[lane].sum())
            self.previous[lane] = values[lane].astype(np.uint8)
            self.success[lane] = values[lane] != 5
            self.slots[lane] += 1
            terminal = self.slots[lane] == 12
            dw = min(3, int(self.scores[lane]) % 4)
            de = min(3, (int(self.scores[lane]) // 4) % 4)
            waste = float(self.scores[lane]) / max(1, self.slots[lane] * self.roster * 5)
            terminals.append(terminal)
            returns.append(native_endpoint(dw, de, waste))
            primitives.append(NativePrimitives(
                dw=dw, de=de, waste=waste, duplicate=0, expired=0,
                collision=0, empty_radio=0, radio_actions=int((values[lane] != 5).sum()),
                waste_actions=int((values[lane] == 5).sum()),
                successful_deliveries=dw + de,
            ))
        self.step_calls += 1
        self.environment_slots += self.lanes
        return BatchStep(
            tuple(terminals), tuple(returns), tuple(primitives), self.success.copy(),
        )

    def work_ledger(self):
        return BatchWorkLedger(
            _LEDGER_TOKEN, lanes=self.lanes, native_reset_calls=self.reset_calls,
            native_observe_calls=self.observe_calls, native_step_calls=self.step_calls,
            environment_slots=self.environment_slots,
        )


def test_full_fake_width32_collection_has_exact_work_and_live_graph(monkeypatch):
    import torch

    torch.set_num_threads(1)
    monkeypatch.setattr(collector, "B01NativeBatchEnvironment", _FakeBatchEnvironment)
    tapes, origins = make_test_update_inputs(
        b"C" * 32, seed_label=TEST_SEED_LABELS[0], update=1,
    )
    result = collector._collect_b01_test_arm_update(
        model=_model(), adapter=object(), tapes=tapes, origins=origins, update=1,
    )
    assert dataclasses.asdict(result.audit) == {
        "schema": "FRRIE_B01_BATCH_COLLECTION_AUDIT_V1", "update": 1,
        "factual_episodes": 64, "native_width": 32, "factual_slots": 768,
        "factual_suffix_audit_slots": 1_248, "nonfactual_suffix_slots": 2_912,
        "total_environment_slots": 4_928, "factual_suffixes_audited": 192,
        "alternative_suffixes_executed": 448, "factual_trace_direct_equal": True,
        "model_bytes_unchanged": True,
        "torch_actor_batch_calls": result.audit.torch_actor_batch_calls,
        "torch_critic_batch_calls": 2, "maximum_actor_lanes": 32,
        "shared_model_worker_count": 1,
    }
    assert result.audit.torch_actor_batch_calls > 24
    assert tuple(episode.roster_size for episode in result.batch.episodes) == (9, 15) * 32
    terms = rscf_batch_loss(result.batch.episodes)
    assert terms.loss.requires_grad and torch.isfinite(terms.loss)


def test_collector_path_paired_q_targets_use_canonical_illegal_nan_sentinel(monkeypatch):
    """Exercise the production-core TEST wrapper, not a synthetic episode fixture."""

    import torch

    torch.set_num_threads(1)
    monkeypatch.setattr(collector, "B01NativeBatchEnvironment", _FakeBatchEnvironment)
    test_root = b"P" * 32
    seed_label = TEST_SEED_LABELS[0]
    tapes, origins = make_test_update_inputs(
        test_root, seed_label=seed_label, update=1,
    )
    phy, edge = initialize_paired_arms(AddressedRNG(test_root), seed_label)
    models = {
        "PHY_TRUST": FRRIEActorCritic(phy),
        "EDGE_FLEX": FRRIEActorCritic(edge),
    }
    collected = {
        arm: collector._collect_b01_test_arm_update(
            model=model, adapter=object(), tapes=tapes, origins=origins, update=1,
        )
        for arm, model in models.items()
    }
    left = collected["PHY_TRUST"].batch
    right = collected["EDGE_FLEX"].batch
    assert_common_exogenous_and_work(left, right)
    assert_precontact_observation_equality(left, right)
    assert_paired_episode_information(left.episodes, right.episodes)

    canonical_nan_bits = torch.full(
        (3, 6), float("nan"), dtype=torch.float32,
    ).view(torch.int32)
    for batch in (left, right):
        for episode in batch.episodes:
            targets = episode.q_targets.detach().contiguous()
            legal = episode.legal_masks.detach()
            illegal = ~legal
            assert targets.dtype == torch.float32 and targets.shape == (3, 6)
            assert legal.dtype == torch.bool and legal.shape == (3, 6)
            assert torch.isfinite(targets[legal]).all()
            assert torch.isnan(targets[illegal]).all()
            assert torch.equal(
                targets.view(torch.int32)[illegal], canonical_nan_bits[illegal],
            )


def test_actual_transaction_attributes_native_then_collector_stages(tmp_path, monkeypatch):
    from experiments.candidates.finite_resource_relational_inductive_efficiency import native_adapter
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import recon

    events = []

    class FakeMonitor:
        instance = None

        def __init__(self, **kwargs):
            del kwargs
            self.current = None
            FakeMonitor.instance = self

        def start(self):
            events.append("START")

        def set_stage(self, stage):
            self.current = stage
            events.append(stage)

        def stop(self):
            events.append("STOP")
            return {"stage_order": list(events), "current_at_stop": self.current}

    artifact = (tmp_path / "preexisting-native.dll").resolve()
    artifact.write_bytes(b"TEST-NATIVE")
    vcvars = (tmp_path / "vcvars64.bat").resolve()
    compiler = (tmp_path / "cl.exe").resolve()
    vcvars.write_text("TEST", encoding="ascii")
    compiler.write_bytes(b"TEST")
    monkeypatch.setattr(recon, "_AReconProcessTreeMonitor", FakeMonitor)
    monkeypatch.setattr(native_adapter, "package_native_artifact_path", lambda: artifact)
    monkeypatch.setattr(native_adapter, "_windows_vcvars64", lambda: vcvars)
    monkeypatch.setattr(
        native_adapter, "_windows_build_environment", lambda path: (str(compiler), {}),
    )
    monkeypatch.setattr(
        native_adapter, "_validate_vcvars_compiler", lambda path, value: compiler,
    )
    monkeypatch.setattr(native_adapter, "build_package_native_artifact", lambda: artifact)
    adapter = object()
    monkeypatch.setattr(
        native_adapter, "load_package_native_adapter", lambda compute: adapter,
    )

    def fake_run(argv, **kwargs):
        del kwargs
        if "admit-memory" in argv:
            receipt_path = argv[argv.index("--out") + 1]
            with open(receipt_path, "w", encoding="utf-8") as stream:
                json.dump({"passed": True}, stream)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[:3] == ["git", "rev-parse", "HEAD"]:
            return SimpleNamespace(returncode=0, stdout="1" * 40 + "\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(collector.subprocess, "run", fake_run)

    def fake_assess(*, adapter_factory, **kwargs):
        del kwargs
        assert events == ["START", "FRESH_MEMORY_ADMISSION"]
        assert adapter_factory() is adapter
        assert FakeMonitor.instance.current == "ACTUAL_WIDTH32_ONE_UPDATE_TWO_ARMS"
        events.append("COLLECTOR_OPERATION")
        return {"complete": True}

    monkeypatch.setattr(collector, "assess_one_update_test", fake_assess)
    root = tmp_path / "actual-transaction"
    evidence = collector.run_actual_test_assessment(root=root)
    assert events == [
        "START", "FRESH_MEMORY_ADMISSION", "NATIVE_BUILD_LOAD",
        "ACTUAL_WIDTH32_ONE_UPDATE_TWO_ARMS", "COLLECTOR_OPERATION", "STOP",
    ]
    assert evidence["process_tree_telemetry"] == {
        "stage_order": events, "current_at_stop": "ACTUAL_WIDTH32_ONE_UPDATE_TWO_ARMS",
    }
    assert (root / "assessment.json").is_file()
