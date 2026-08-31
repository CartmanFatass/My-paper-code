import json
import struct
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
from experiments.candidates.finite_resource_relational_inductive_efficiency.analysis import (
    CheckpointBytesUnvalidated, validate_complete_panel,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.checkpoint import (
    learned_arm_state_bytes, serialize_checkpoint, write_checkpoint_atomic,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core import (
    LEARNED_ARMS, expected_block_checkpoint_path, manifest_packet_contract,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.evaluator import (
    ALL_ARMS, ALL_ROSTERS,
    CompleteOnlyEvaluationTransaction, decision_probability_pairs,
    complete_panel_result, episode_record, evaluation_cell,
    evaluation_opportunities, probability_vector_tv, uniform_legal_probabilities,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.orchestration import (
    OriginCoordinate, TestOnlyExternalEnvironment, assert_paired_initialization,
    capture_rscf_episode, production_training_schedule,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import (
    TORCH_AVAILABLE, make_actor_critic,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
from experiments.candidates.finite_resource_relational_inductive_efficiency.lifecycle import claim_fresh_roots
from experiments.candidates.finite_resource_relational_inductive_efficiency.native_adapter import expected_native_contract
from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import (
    OPTIMIZER_PAYLOAD_BYTE_COUNT, OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.work import checkpoint_cumulative_work


def test_schedule_is_exact_512_and_arm_independent():
    tapes = [[f"tape-{update}-{episode}" for episode in range(64)] for update in range(512)]
    origins = [[f"origin-{update}-{episode}" for episode in range(64)] for update in range(512)]
    schedule = production_training_schedule(tapes, origins)
    assert len(schedule) == 512
    assert schedule[0].update == 1 and schedule[-1].update == 512
    assert schedule[0].roster_order == (9, 15) * 32
    assert not hasattr(schedule[0], "arm")

    origins[1][0] = origins[0][0]
    with pytest.raises(ValueError, match="unique origin"):
        production_training_schedule(tapes, origins)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="CPU Torch not installed")
def test_factual_origin_all_legal_suffix_has_training_shapes():
    class CountingModel:
        def __init__(self, model):
            self.model = model
            self.actor_steps = 0

        def __getattr__(self, name):
            return getattr(self.model, name)

        def actor_step(self, *args, **kwargs):
            self.actor_steps += 1
            return self.model.actor_step(*args, **kwargs)

    phy, edge = initialize_paired_arms(
        AddressedRNG(b"O" * 32), "FRRIE-TEST-ONLY-ORCHESTRATION-V2"
    )
    models = {"PHY_TRUST": make_actor_critic(phy), "EDGE_FLEX": make_actor_critic(edge)}
    assert_paired_initialization(models)
    counted_model = CountingModel(models["PHY_TRUST"])
    environment = TestOnlyExternalEnvironment(9)
    audit = {}
    episode = capture_rscf_episode(
        model=counted_model, environment=environment,
        environment_tape={"TEST_ONLY": True},
        action_uniforms=np.full((12, 9), np.float32(0.5), dtype=np.float32),
        origins=(OriginCoordinate(0, 0, 0), OriginCoordinate(1, 0, 3), OriginCoordinate(2, 0, 6)),
        audit_out=audit,
    )
    assert tuple(episode.selected_probabilities.shape) == (3, 6)
    assert tuple(episode.q_targets.shape) == (3, 6)
    assert tuple(episode.all_probabilities.shape) == (12, 9, 6)
    assert episode.q_targets[episode.legal_masks].isfinite().all()
    assert environment.observe().terminal is True
    assert audit == {
        "alternative_suffixes_executed": 7,
        "factual_suffixes_audited": 3,
        "factual_trace_direct_equal": True,
        "factual_audit_actor_steps": 33,
        "new_rng_addresses": 0,
        "preupdate_model_bit_equal": True,
    }
    # 12 factual + 3*(11 future-only audit) + 7*(11 alternative future)
    # actor calls.  The three origin decisions are retained, never recomputed.
    assert counted_model.actor_steps == 122


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="CPU Torch not installed")
def test_factual_trace_mismatch_is_structural_and_not_retried():
    class CorruptingReplayEnvironment(TestOnlyExternalEnvironment):
        def __init__(self, roster):
            super().__init__(roster)
            self.restore_calls = 0

        def restore(self, snapshot):
            super().restore(snapshot)
            self.restore_calls += 1
            self._score += 1

    phy, _ = initialize_paired_arms(
        AddressedRNG(b"M" * 32), "FRRIE-TEST-ONLY-FACTUAL-AUDIT-MISMATCH"
    )
    environment = CorruptingReplayEnvironment(9)
    with pytest.raises(ValueError, match="retained origin decision trace differs"):
        capture_rscf_episode(
            model=make_actor_critic(phy), environment=environment,
            environment_tape={"TEST_ONLY": True},
            action_uniforms=np.full((12, 9), np.float32(0.5), dtype=np.float32),
            origins=(
                OriginCoordinate(0, 0, 0), OriginCoordinate(1, 0, 3),
                OriginCoordinate(2, 0, 6),
            ),
        )
    assert environment.restore_calls == 1


def test_eval_schedule_reuses_tapes_across_cuts_and_tv_shape():
    tape_ids = {(roster, episode): f"t-{roster}-{episode}" for roster in (9, 15, 6, 21) for episode in range(2)}
    schedule = evaluation_opportunities(tape_ids, episodes_per_cell=2)
    intact = {(row.roster, row.episode): row.tape_identity for row in schedule if row.intervention == "INTACT"}
    rotated = {(row.roster, row.episode): row.tape_identity for row in schedule if row.intervention == "SEMANTIC_COLUMN_ROTATE"}
    assert intact == rotated
    roles = [0, 1, 2]
    probabilities = [uniform_legal_probabilities(role) for role in roles]
    assert probability_vector_tv(probabilities, probabilities, roles) == [0.0, 0.0, 0.0]


def test_probability_pairs_have_fixed_slots_entities_and_complete_only_publish(tmp_path):
    roster = 6
    roles = [entity // 2 for _slot in range(12) for entity in range(roster)]
    vectors = [uniform_legal_probabilities(role) for role in roles]
    pairs = decision_probability_pairs(roster=roster, intact=vectors, shadow=vectors, roles=roles)
    assert len(pairs) == 72
    assert pairs[0]["slot"] == 0 and pairs[-1]["slot"] == 11
    target = tmp_path / "panel.json"
    transaction = CompleteOnlyEvaluationTransaction(
        target, b"TEST_ONLY_UPDATE_512", test_only=True,
    )
    transaction.stage_complete_panel({"complete": True, "cells": [], "TEST_ONLY": True})
    assert not target.exists()
    transaction.publish()
    assert target.is_file()


def test_episode_record_binds_literal_same_index_tape():
    tape = {
        "schema": "FRRIE_ADDRESSED_TAPE_V1", "seed_block": "TEST-BLOCK",
        "purpose": "EVALUATE", "roster": 6, "update": 512, "episode": 4,
    }
    record = episode_record(
        episode=4, tape_contract=tape, dw=1, de=2, waste=0.25,
        decision_pairs=None,
    )
    assert record["episode"] == 4 and record["tape_contract"] == tape
    with pytest.raises(ValueError, match="same-index"):
        episode_record(
            episode=3, tape_contract=tape, dw=1, de=2, waste=0.25,
            decision_pairs=None,
        )


def test_interrupted_eval_exposes_no_target_and_can_restart_from_checkpoint(tmp_path):
    target = tmp_path / "panel.json"
    transaction = CompleteOnlyEvaluationTransaction(
        target, b"READ_ONLY_CHECKPOINT_512", test_only=True,
    )
    transaction.stage_complete_panel({"complete": True, "cells": [], "TEST_ONLY": True})
    assert not target.exists()
    transaction.abort()
    assert not target.exists()
    restarted = CompleteOnlyEvaluationTransaction(
        target, transaction.checkpoint512, test_only=True,
    )
    assert restarted.checkpoint512 == b"READ_ONLY_CHECKPOINT_512"


def test_production_evaluation_rejects_absent_exact_checkpoint_file(manifest_factory):
    manifest = manifest_factory()
    packet, native_contract, checkpoints, output_root, seed_block = (
        _production_evaluation_inputs(manifest)
    )
    expected_block_checkpoint_path(manifest, manifest["seed_blocks"][-1]).unlink()
    with pytest.raises(ValueError, match="exact read-only"):
        CompleteOnlyEvaluationTransaction(
            output_root / "absent-panel.json", checkpoints,
            manifest=manifest, seed_packet_contract=packet,
            seed_packet_path=manifest["sealed_seed_packet"]["path"],
            expected_seed_block=seed_block, native_contract=native_contract,
        )


def test_production_evaluation_rejects_supplied_bytes_different_from_file(manifest_factory):
    manifest = manifest_factory()
    packet, native_contract, checkpoints, output_root, seed_block = (
        _production_evaluation_inputs(manifest)
    )
    different = dict(checkpoints)
    different[manifest["seed_blocks"][0]] = checkpoints[manifest["seed_blocks"][1]]
    with pytest.raises(ValueError, match="exact read-only"):
        CompleteOnlyEvaluationTransaction(
            output_root / "different-panel.json", different,
            manifest=manifest, seed_packet_contract=packet,
            seed_packet_path=manifest["sealed_seed_packet"]["path"],
            expected_seed_block=seed_block, native_contract=native_contract,
        )
def _production_evaluation_inputs(manifest):
    packet = {
        "schema": "FRRIE_SEALED_SEED_PACKET_V2",
        "version": 2,
        "manifest_contract": manifest_packet_contract(manifest),
        "blocks": list(manifest["seed_blocks"]),
        "addressed_rng_roots": [f"{index:064x}" for index in range(1, 25)],
        "generation_provenance": "TEST_ONLY_EVALUATION_CHECKPOINT_BINDING",
        "no_prior_use": True,
        "sealed": True,
        "complete": True,
    }
    Path(manifest["sealed_seed_packet"]["path"]).write_text(
        json.dumps(packet), encoding="utf-8"
    )
    phy, edge = initialize_paired_arms(
        AddressedRNG(b"E" * 32), "FRRIE-TEST-ONLY-EVALUATION-CHECKPOINT"
    )
    arm_state = learned_arm_state_bytes({"PHY_TRUST": phy, "EDGE_FLEX": edge})
    optimizer_payload = (
        b"\0" * (OPTIMIZER_PAYLOAD_BYTE_COUNT - 8) + struct.pack("<Q", 512)
    )
    optimizer_blob = struct.pack(
        "<8sII", OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
        len(optimizer_payload),
    ) + optimizer_payload
    native_contract = asdict(expected_native_contract(manifest["compute"]))
    seed_block = manifest["seed_blocks"][0]
    checkpoints = {
        block: serialize_checkpoint(
            manifest_contract=manifest,
            native_contract=native_contract,
            seed_packet_contract=packet,
            seed_packet_path=manifest["sealed_seed_packet"]["path"],
            seed_block=block,
            update=512,
            frontiers={
                "training_update": 512,
                "minibatch_cursor": 0,
                "factual_episode_cursor": 512 * 64,
                "factual_environment_slot_cursor": 393_216,
                "alternative_suffix_environment_slot_cursor": 1_490_944,
                "evaluation_checkpoint_cursor": 0,
            },
            arm_state_bytes=arm_state,
            optimizer_state_bytes={arm: optimizer_blob for arm in LEARNED_ARMS},
            work_receipts=checkpoint_cumulative_work(manifest["compute"]),
            rng_frontier={
                "schema": "FRRIE_STATELESS_RNG_FRONTIER_V1",
                "stateless": True,
                "tape_contract": {
                    "schema": "TEST_ONLY_EVALUATION_TAPE_FRONTIER", "block": block,
                },
            },
        )
        for block in manifest["seed_blocks"]
    }
    output_root, _ = claim_fresh_roots(manifest)
    for block, data in checkpoints.items():
        write_checkpoint_atomic(expected_block_checkpoint_path(manifest, block), data)
    return packet, native_contract, checkpoints, output_root, seed_block


def test_production_evaluation_accepts_only_fully_bound_update512_checkpoint(
    manifest_factory,
):
    manifest = manifest_factory()
    packet, native_contract, checkpoints, output_root, seed_block = (
        _production_evaluation_inputs(manifest)
    )
    transaction = CompleteOnlyEvaluationTransaction(
        output_root / "complete-panel.json",
        checkpoints,
        manifest=manifest,
        seed_packet_contract=packet,
        seed_packet_path=manifest["sealed_seed_packet"]["path"],
        expected_seed_block=seed_block,
        native_contract=native_contract,
    )
    assert transaction.checkpoint512 == checkpoints
    cells = [
        evaluation_cell(
            manifest=manifest,
            checkpoint_inventory=transaction.checkpoint_inventory,
            seed_block=block, arm=arm, roster=roster, intervention=intervention,
            episode_records=None, support_valid=False,
            support_reason="TEST_ONLY_DIRECT_UNSUPPORTED_ENDPOINT",
        )
        for block in manifest["seed_blocks"]
        for arm in ALL_ARMS
        for roster in ALL_ROSTERS
        for intervention in manifest["evaluation"]["interventions"]
    ]
    panel = complete_panel_result(
        manifest=manifest,
        checkpoint_inventory=transaction.checkpoint_inventory,
        cells=cells,
        support_valid=False,
        support_reason="TEST_ONLY_DIRECT_UNSUPPORTED_ENDPOINT",
    )
    transaction.stage_complete_panel(panel)
    assert not (output_root / "complete-panel.json").exists()
    transaction.abort()
    expected_block_checkpoint_path(manifest, seed_block).unlink()
    with pytest.raises(CheckpointBytesUnvalidated, match="independently restored"):
        validate_complete_panel(panel, manifest)
    write_checkpoint_atomic(
        expected_block_checkpoint_path(manifest, seed_block),
        checkpoints[manifest["seed_blocks"][1]],
    )
    with pytest.raises(CheckpointBytesUnvalidated, match="independently restored"):
        validate_complete_panel(panel, manifest)
