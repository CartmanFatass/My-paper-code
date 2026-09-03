from __future__ import annotations

from dataclasses import asdict
import hashlib
from pathlib import Path

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine import (
    B1CheckpointBinding,
    B1_RAW_EVIDENCE_SCHEMA,
    capture_b1_checkpoint,
    save_b1_checkpoint,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_policy_assembly import (
    B1MetricsPolicyAssemblyError,
    TEST_ONLY_POLICY_PROFILE_SCHEMA,
    assemble_b1_metrics_policy_tables,
    validate_execution_mode_records,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_runtime_audit import (
    B1RuntimeAuditError,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.checkpoint import (
    model_parameter_digest_from_state,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import (
    DynamicHost,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.model import (
    CommonRecurrentActorCritic,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import (
    PPOConfig,
    PPOCounters,
    RecurrentPPOTrainer,
    config_digest,
    make_adam,
)


RUN = "CBSC-OMRC-B1-THREE-SEED-SCOUT"
SEEDS = (21101, 21121, 21143)
ARM = "RAW-GRU"
ATTEMPT = "test-policy-assembly"
COMMIT = "4" * 40
SOURCE = "5" * 64


def _fixture(staging: Path) -> tuple[tuple[dict, ...], tuple[object, ...]]:
    groups: list[tuple[dict, ...]] = []
    tapes: list[object] = []
    for slot_index, seed in zip((1, 5, 9), SEEDS, strict=True):
        tag = f"{slot_index:02d}-seed-{seed}-{ARM}"
        durable = staging / "arm-seeds" / tag
        durable.mkdir(parents=True)
        model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
        checkpoints = []
        for update in (0, 12, 24, 48):
            trainer = RecurrentPPOTrainer(
                model,
                run_name=RUN,
                seed=seed,
                optimizer=make_adam(model),
                address_u64=addressing.u64,
            )
            trainer.counters = PPOCounters(
                rollout_updates=update,
                adam_steps=update * 16,
                train_episodes=update * 8,
                train_transitions=update * 8 * 152,
                train_decisions=update * 8 * 24,
            )
            binding = B1CheckpointBinding(
                object_id="CBSC-OMRC-B01",
                attempt_id=ATTEMPT,
                run_name=RUN,
                arm=ARM,
                seed=seed,
                completed_rollout_updates=update,
                train_episode_ids_sha256="1" * 64,
                full_training_tape_digest="2" * 64,
                full_action_uniform_digest="3" * 64,
                ppo_configuration_digest=config_digest(PPOConfig()),
                implementation_commit=COMMIT,
                source_conformance_sha256=SOURCE,
            )
            envelope = capture_b1_checkpoint(trainer, binding)
            path = durable / f"checkpoint-update-{update}.pt"
            save_b1_checkpoint(path, envelope)
            payload = path.read_bytes()
            inner = envelope["recurrent_ppo_checkpoint"]
            checkpoints.append(
                {
                    "update": update,
                    "relative_path": path.name,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "byte_count": len(payload),
                    "binding": asdict(binding),
                    "counters": dict(inner["counters"]),
                    "digests": dict(inner["digests"]),
                    "model_parameter_digest": model_parameter_digest_from_state(
                        inner["model_state"]
                    ),
                }
            )
        groups.append(({
            "schema": B1_RAW_EVIDENCE_SCHEMA,
            "attempt_id": ATTEMPT,
            "run_name": RUN,
            "arm": ARM,
            "seed": seed,
            "slice": {"start_update": 0, "stop_update": 48},
            "full_bindings": {
                "implementation_commit": COMMIT,
                "source_conformance_sha256": SOURCE,
            },
            "checkpoints_created": checkpoints,
            "scientific_branch": None,
        },))
        host = DynamicHost(RUN, seed)
        tapes.extend((
            host.build_stochastic(addressing.EVAL_STOCHASTIC, 0),
            host.build_motif(0),
        ))
    return tuple(groups), tuple(tapes)


def test_test_only_assembly_binds_four_checkpoint_models_and_exact_raw_coverage(
    tmp_path: Path,
) -> None:
    grouped, tapes = _fixture(tmp_path)

    packet = assemble_b1_metrics_policy_tables(
        staging_root=tmp_path,
        grouped_raw_slices=grouped,
        heldout_tapes=tapes,
        expected_attempt_id=ATTEMPT,
        expected_implementation_commit=COMMIT,
        expected_source_conformance_sha256=SOURCE,
        literal_binding_spec_sha256="6" * 64,
        test_only=True,
    )

    assert packet["test_only"] is True
    assert packet["profile_schema"] == TEST_ONLY_POLICY_PROFILE_SCHEMA
    assert packet["formal_policy_coverage_satisfied"] is False
    assert packet["formal_readiness_authority"] is False
    assert packet["counts"] == {
        "arm_seed_slots": 3,
        "checkpoints": 12,
        "heldout_tapes": 6,
        "execution_mode_records": 12,
        "policy_decisions": 576,
        "policy_curves": 6,
        "policy_support_total": 576,
    }
    assert len(packet["policy_decisions"]) == 576
    assert len(packet["policy_curves"]) == 6
    assert packet["execution_mode_records"] == [
        {
            "run_order": 0,
            "seed": seed,
            "arm_order": 1,
            "checkpoint_update": update,
            "active_modes": [],
        }
        for seed in SEEDS
        for update in (0, 12, 24, 48)
    ]
    assert sum(
        row["support_count"]
        for row in packet["policy_support_signature_counts"]
    ) == 576

    with pytest.raises(B1MetricsPolicyAssemblyError, match="coverage"):
        validate_execution_mode_records(
            packet["execution_mode_records"][:-1], test_only=True
        )
    tampered = [dict(row) for row in packet["execution_mode_records"]]
    tampered[0]["active_modes"] = ["float32-matmul-precision:high"]
    with pytest.raises(B1MetricsPolicyAssemblyError, match="prohibited"):
        validate_execution_mode_records(tampered, test_only=True)


def test_assembly_rejects_checkpoint_bytes_changed_after_raw_inventory(
    tmp_path: Path,
) -> None:
    grouped, tapes = _fixture(tmp_path)
    checkpoint = (
        tmp_path
        / "arm-seeds"
        / f"05-seed-21121-{ARM}"
        / "checkpoint-update-24.pt"
    )
    checkpoint.write_bytes(checkpoint.read_bytes() + b"drift")

    with pytest.raises(B1MetricsPolicyAssemblyError, match="checkpoint.*bytes|SHA"):
        assemble_b1_metrics_policy_tables(
            staging_root=tmp_path,
            grouped_raw_slices=grouped,
            heldout_tapes=tapes,
            expected_attempt_id=ATTEMPT,
            expected_implementation_commit=COMMIT,
            expected_source_conformance_sha256=SOURCE,
            literal_binding_spec_sha256="6" * 64,
            test_only=True,
        )


def test_assembly_refuses_prohibited_directly_observed_mode_before_policy_output(
    tmp_path: Path,
) -> None:
    grouped, tapes = _fixture(tmp_path)
    original = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        with pytest.raises(B1RuntimeAuditError, match="prohibited active execution modes"):
            assemble_b1_metrics_policy_tables(
                staging_root=tmp_path,
                grouped_raw_slices=grouped,
                heldout_tapes=tapes,
                expected_attempt_id=ATTEMPT,
                expected_implementation_commit=COMMIT,
                expected_source_conformance_sha256=SOURCE,
                literal_binding_spec_sha256="6" * 64,
                test_only=True,
            )
    finally:
        torch.set_default_dtype(original)
