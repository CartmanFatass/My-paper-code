from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import inspect
from pathlib import Path

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1_BOUND_ADMISSION_SCHEMA,
    B1_CHECKPOINT_UPDATES,
    B1_EVAL_MOTIF_IDS,
    B1_EVAL_STOCHASTIC_IDS,
    B1_RESOURCE_CAPS,
    B1_TRAIN_EPISODE_IDS,
    B1ArmSeedRequest,
    B1Plan,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine import (
    B1CheckpointBinding,
    B1EngineError,
    audit_b1_checkpoint,
    b1_engine,
    capture_b1_checkpoint,
    load_b1_checkpoint,
    restore_b1_checkpoint,
    save_b1_checkpoint,
    b1_slice_counts,
    b1_slice_checkpoint_updates,
    build_stage_measurements,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.model import (
    INPUT_DIM,
    CommonRecurrentActorCritic,
    greedy_action,
    model_parameter_digest,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_runtime_audit import (
    B1RuntimeAuditError,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import (
    EPISODE_TRANSITIONS,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import (
    RecurrentPPOTrainer,
    make_adam,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_worker import (
    WORKER_RESULT_SCHEMA,
    WORKER_REQUEST_SCHEMA,
    encode_worker_request,
    load_worker_request,
    wrap_worker_result,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.artifact import (
    canonical_json_bytes,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.telemetry import (
    validate_telemetry,
)


def _request(tmp_path: Path, *, source: str = "2" * 64) -> B1ArmSeedRequest:
    receipt = tmp_path / "admission.json"
    receipt.write_bytes(b"result-blind-admission\n")
    return B1ArmSeedRequest(
        plan=B1Plan(),
        attempt_id="b1-test-attempt",
        arm="STRUCT-CURRENTNESS-GRU",
        seed=21101,
        train_episode_ids=B1_TRAIN_EPISODE_IDS,
        checkpoint_updates=B1_CHECKPOINT_UPDATES,
        eval_stochastic_ids=B1_EVAL_STOCHASTIC_IDS,
        eval_motif_ids=B1_EVAL_MOTIF_IDS,
        scratch_root=(tmp_path / "scratch").resolve(),
        durable_root=(tmp_path / "durable").resolve(),
        admission_schema=B1_BOUND_ADMISSION_SCHEMA,
        admission_receipt_path=receipt.resolve(),
        admission_receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
        implementation_commit="1" * 40,
        source_conformance_sha256=source,
        resource_caps=B1_RESOURCE_CAPS,
    )


def _trainer(seed: int = 21101) -> RecurrentPPOTrainer:
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    return RecurrentPPOTrainer(
        model,
        run_name=addressing.B1_RUN,
        seed=seed,
        optimizer=make_adam(model),
        address_u64=addressing.u64,
    )


def test_b1_factory_is_fixed_and_exposes_canonical_worker_surface() -> None:
    import experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine as module

    signature = inspect.signature(b1_engine)
    assert not signature.parameters
    engine = b1_engine()
    assert engine.worker_count == 1
    assert engine.threads_per_worker == 1
    assert engine.checkpoint_updates == B1_CHECKPOINT_UPDATES
    declared = set(engine.source_paths)
    for suffix in (
        "b1_contract.py",
        "b1_engine.py",
        "b1_runtime_audit.py",
        "b1_worker.py",
        "host.py",
        "adapters.py",
        "model.py",
        "ppo.py",
        "checkpoint.py",
        "evaluator.py",
    ):
        assert any(path.endswith(suffix) for path in declared)
    source = inspect.getsource(module)
    assert "RecurrentQLearner" not in source
    assert "BoundedReplay" not in source
    assert "OnlineQTrainer" not in source
    assert '"audits"' not in source
    assert '"scientific_branch": None' in source


def test_b1_checkpoint_roundtrip_restores_exact_persistent_state_only(tmp_path: Path) -> None:
    request = _request(tmp_path)
    trainer = _trainer()
    binding = B1CheckpointBinding.from_request(
        request,
        completed_rollout_updates=0,
        full_training_tape_digest="3" * 64,
        full_action_uniform_digest="4" * 64,
    )
    envelope = capture_b1_checkpoint(trainer, binding)
    assert set(envelope) == {"schema", "binding", "recurrent_ppo_checkpoint"}
    assert not any(
        forbidden in repr(envelope).lower()
        for forbidden in ("adapter_state", "recurrent_state", "hidden_state")
    )
    destination = tmp_path / "checkpoint-update-0.pt"
    save_b1_checkpoint(destination, envelope)
    before = destination.read_bytes()
    loaded = load_b1_checkpoint(destination)
    assert destination.read_bytes() == before

    restored = _trainer()
    restore_b1_checkpoint(
        loaded,
        restored,
        request=request,
        expected_update=0,
        full_training_tape_digest="3" * 64,
        full_action_uniform_digest="4" * 64,
    )
    assert restored.counters.rollout_updates == 0
    assert restored.minibatch_order_digest == trainer.minibatch_order_digest
    observations = torch.zeros((1, EPISODE_TRANSITIONS, INPUT_DIM), dtype=torch.float32)
    decision_mask = torch.zeros((EPISODE_TRANSITIONS,), dtype=torch.bool)
    decision_mask[12::6] = True
    with torch.no_grad():
        fresh_sequence = trainer.model.forward_episode(observations)
        restored_sequence = restored.model.forward_episode(observations)
        fresh_actions = greedy_action(
            fresh_sequence.logits.reshape(-1, 4), decision_mask
        ).actions
        restored_actions = greedy_action(
            restored_sequence.logits.reshape(-1, 4), decision_mask
        ).actions
    assert torch.equal(restored_actions, fresh_actions)
    assert loaded["binding"]["completed_rollout_updates"] == 0
    assert destination.read_bytes() == before
    production_model_before = model_parameter_digest(trainer.model)
    production_counters_before = dict(vars(trainer.counters))
    rng_before = torch.random.get_rng_state().clone()
    audit = audit_b1_checkpoint(
        destination,
        saved_bytes=before,
        request=request,
        expected_update=0,
        full_training_tape_digest="3" * 64,
        full_action_uniform_digest="4" * 64,
        expected_trainer=trainer,
    )
    assert set(audit) == {
        "name",
        "saved_sha256",
        "loaded_sha256",
        "expected_parameter_sha256",
        "restored_parameter_sha256",
    }
    assert audit["saved_sha256"] == audit["loaded_sha256"]
    assert audit["expected_parameter_sha256"] == audit["restored_parameter_sha256"]
    assert model_parameter_digest(trainer.model) == production_model_before
    assert dict(vars(trainer.counters)) == production_counters_before
    assert torch.equal(torch.random.get_rng_state(), rng_before)

    corrupted = tmp_path / "checkpoint-corrupted.pt"
    corrupted.write_bytes(before[:-1] + bytes((before[-1] ^ 0xFF,)))
    with pytest.raises(B1RuntimeAuditError, match="checkpoint"):
        audit_b1_checkpoint(
            corrupted,
            saved_bytes=before,
            request=request,
            expected_update=0,
            full_training_tape_digest="3" * 64,
            full_action_uniform_digest="4" * 64,
            expected_trainer=trainer,
        )
    with pytest.raises(B1RuntimeAuditError, match="checkpoint"):
        audit_b1_checkpoint(
            destination,
            saved_bytes=before,
            request=replace(request, arm="RAW-GRU"),
            expected_update=0,
            full_training_tape_digest="3" * 64,
            full_action_uniform_digest="4" * 64,
            expected_trainer=trainer,
        )
    with pytest.raises(FileExistsError):
        save_b1_checkpoint(destination, envelope)


def test_checkpoint_capture_and_restore_bind_all_three_scientific_authorities(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    trainer = _trainer()
    binding = B1CheckpointBinding.from_request(
        request,
        completed_rollout_updates=0,
        full_training_tape_digest="3" * 64,
        full_action_uniform_digest="4" * 64,
    )
    envelope = capture_b1_checkpoint(trainer, binding)
    assert envelope["binding"]["object_id"] == "CBSC-OMRC-B01"
    assert envelope["binding"]["innovator_selection_request_id"] == (
        "cbsc-online-b-innovator-20260901-01"
    )
    assert envelope["binding"]["innovator_selection_response_sha256"] == (
        "94f163f8ba777950c9c19ffac1acca3c697f09642d4713ef13b1e66d9f04d778"
    )
    assert envelope["binding"]["literal_binding_request_id"] == (
        "cbsc-online-b-innovator-20260901-02"
    )
    assert envelope["binding"]["literal_binding_response_sha256"] == (
        "e96df981f7cdb40a6206f2fddcc989a05783491a1fa422e7b0ca673344a05844"
    )
    assert envelope["binding"]["metrics_only_request_id"] == (
        "cbsc-online-b-innovator-20260901-03"
    )
    assert envelope["binding"]["metrics_only_response_sha256"] == (
        "7a3bd74e12508e22ea577a1563737eda119c10560e094b25279503648d1105f7"
    )

    for field, mutation in (
        ("innovator_selection_request_id", "missing"),
        ("innovator_selection_archive_path", "unbound/RESPONSE.md"),
        ("innovator_selection_response_sha256", "0" * 64),
        ("literal_binding_response_sha256", "0" * 64),
        ("metrics_only_response_sha256", "0" * 64),
    ):
        tampered = deepcopy(envelope)
        if mutation == "missing":
            del tampered["binding"][field]
        else:
            tampered["binding"][field] = mutation
        with pytest.raises(B1EngineError, match="checkpoint|binding|identity"):
            restore_b1_checkpoint(
                tampered,
                _trainer(),
                request=request,
                expected_update=0,
                full_training_tape_digest="3" * 64,
                full_action_uniform_digest="4" * 64,
            )


@pytest.mark.parametrize("update", B1_CHECKPOINT_UPDATES)
def test_every_frozen_checkpoint_boundary_has_an_exact_binding(
    tmp_path: Path, update: int
) -> None:
    binding = B1CheckpointBinding.from_request(
        _request(tmp_path),
        completed_rollout_updates=update,
        full_training_tape_digest="3" * 64,
        full_action_uniform_digest="4" * 64,
    )
    assert binding.completed_rollout_updates == update


def test_resume_rejects_source_update_and_full_panel_binding_mismatch(tmp_path: Path) -> None:
    request = _request(tmp_path)
    trainer = _trainer()
    envelope = capture_b1_checkpoint(
        trainer,
        B1CheckpointBinding.from_request(
            request,
            completed_rollout_updates=0,
            full_training_tape_digest="3" * 64,
            full_action_uniform_digest="4" * 64,
        ),
    )
    for changed_request, update, tape, action, match in (
        (replace(request, source_conformance_sha256="9" * 64), 0, "3" * 64, "4" * 64, "source"),
        (request, 12, "3" * 64, "4" * 64, "update"),
        (request, 0, "8" * 64, "4" * 64, "training tape"),
        (request, 0, "3" * 64, "8" * 64, "action uniform"),
    ):
        with pytest.raises(B1EngineError, match=match):
            restore_b1_checkpoint(
                envelope,
                _trainer(),
                request=changed_request,
                expected_update=update,
                full_training_tape_digest=tape,
                full_action_uniform_digest=action,
            )


def test_slice_guards_fail_before_constructing_a_formal_run(tmp_path: Path) -> None:
    request = _request(tmp_path)
    engine = b1_engine()
    with pytest.raises(B1EngineError, match="fresh.*update 0"):
        engine.run_slice(
            request,
            start_update=12,
            stop_update=24,
            resume_checkpoint=None,
        )
    with pytest.raises(B1EngineError, match="checkpoint boundaries"):
        engine.run_slice(
            request,
            start_update=0,
            stop_update=13,
            resume_checkpoint=None,
        )


def test_worker_request_codec_is_strict_and_preserves_resume_seam(tmp_path: Path) -> None:
    request = _request(tmp_path)
    root = tmp_path.resolve()
    resume = (request.durable_root / "checkpoint-update-12.pt").resolve()
    payload = encode_worker_request(
        request,
        attempt_root=root,
        start_update=12,
        stop_update=24,
        resume_checkpoint=resume,
    )
    assert payload["schema"] == WORKER_REQUEST_SCHEMA
    assert payload["resume_checkpoint"] == str(resume)
    path = root / "worker-request.json"
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    decoded = load_worker_request(path)
    assert decoded.request == request
    assert decoded.start_update == 12
    assert decoded.stop_update == 24
    assert decoded.resume_checkpoint == resume

    payload["engine_factory"] = "untrusted:factory"
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    with pytest.raises(ValueError, match="incomplete or extended"):
        load_worker_request(path)


@pytest.mark.parametrize(
    ("start", "stop", "fresh", "train_transitions", "evaluation_transitions"),
    (
        (0, 12, True, 12 * 8 * 152, 2 * 64 * 152),
        (0, 24, True, 24 * 8 * 152, 3 * 64 * 152),
        (0, 48, True, 48 * 8 * 152, 4 * 64 * 152),
        (0, 12, False, 12 * 8 * 152, 2 * 64 * 152),
        (12, 24, False, 12 * 8 * 152, 1 * 64 * 152),
        (12, 48, False, 36 * 8 * 152, 2 * 64 * 152),
        (24, 48, False, 24 * 8 * 152, 1 * 64 * 152),
    ),
)
def test_each_fresh_and_resume_slice_counts_only_new_work(
    start: int,
    stop: int,
    fresh: bool,
    train_transitions: int,
    evaluation_transitions: int,
) -> None:
    counts = b1_slice_counts(start, stop, fresh=fresh)
    assert counts.train_transitions == train_transitions
    assert counts.evaluation_transitions == evaluation_transitions
    assert counts.scientific_work_transitions == train_transitions + evaluation_transitions


def test_resume_zero_and_fresh_zero_share_checkpoint_evaluation_schedule() -> None:
    assert b1_slice_checkpoint_updates(0, 12, fresh=True) == (0, 12)
    assert b1_slice_checkpoint_updates(0, 12, fresh=False) == (0, 12)
    assert b1_slice_checkpoint_updates(12, 24, fresh=False) == (24,)
    assert b1_slice_checkpoint_updates(24, 48, fresh=False) == (48,)


def test_stage_measurements_are_monitor_validatable_and_use_slice_counts() -> None:
    counts = b1_slice_counts(12, 24, fresh=False)
    stages = build_stage_measurements(
        counts,
        train_wall_seconds=2.0,
        train_cpu_seconds=1.5,
        evaluation_wall_seconds=1.0,
        evaluation_cpu_seconds=0.75,
    )
    assert isinstance(stages, list)
    assert stages == [
        {
            "stage": "train",
            "wall_seconds": 2.0,
            "cpu_seconds": 1.5,
            "transitions": 12 * 8 * 152,
            "transitions_per_second": 12 * 8 * 152 / 2.0,
        },
        {
            "stage": "evaluate",
            "wall_seconds": 1.0,
            "cpu_seconds": 0.75,
            "transitions": 64 * 152,
            "transitions_per_second": 64 * 152 / 1.0,
        },
    ]
    validated = validate_telemetry(
        {
            "measurement_complete": True,
            "measurement_source": "bounded-test-process-tree",
            "sample_interval_seconds": 0.05,
            "sample_count": 2,
            "end_to_end_wall_seconds": 3.0,
            "end_to_end_cpu_seconds": 2.25,
            "cpu_core_equivalents": 0.75,
            "cpu_occupancy_fraction": 0.75,
            "process_tree_peak_rss_bytes": 1,
            "peak_process_count": 1,
            "peak_thread_count": 1,
            "worker_count": 1,
            "threads_per_worker": 1,
            "io_read_bytes": 0,
            "io_write_bytes": 0,
            "scratch_high_water_bytes": 0,
            "durable_high_water_bytes": 0,
            "scientific_work_transitions": counts.scientific_work_transitions,
            "scientific_work_transitions_per_second": (
                counts.scientific_work_transitions / 3.0
            ),
            "stage_measurements": stages,
        }
    )
    assert validated["stage_measurements"] == stages


def test_worker_result_wrapper_has_independent_schema_and_null_science() -> None:
    raw = {
        "schema": "cbsc_omrc_b01_b1_arm_seed_slice_raw_evidence_v1",
        "stage_measurements": [{"stage": "train"}],
        "scientific_branch": None,
    }
    wrapped = wrap_worker_result(raw)
    assert set(wrapped) == {"schema", "raw_evidence", "scientific_branch"}
    assert wrapped["schema"] == WORKER_RESULT_SCHEMA
    assert wrapped["raw_evidence"] is raw
    assert wrapped["scientific_branch"] is None
    with pytest.raises(ValueError, match="raw evidence"):
        wrap_worker_result({**raw, "scientific_branch": "CONTINUE"})
