from __future__ import annotations

import inspect
from copy import deepcopy
from dataclasses import asdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import b1
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1_SLOT_ORDER,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine import (
    B1_RAW_EVIDENCE_SCHEMA, B1CheckpointBinding, capture_b1_checkpoint,
    save_b1_checkpoint,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_artifact import (
    make_b1_incident_lineage_witness,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.artifact import (
    canonical_json_bytes,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.checkpoint import (
    model_parameter_digest_from_state,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.model import (
    CommonRecurrentActorCritic,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import (
    DynamicHost,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import (
    PPOConfig, PPOCounters, RecurrentPPOTrainer, config_digest, make_adam,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_production import (
    B1MetricsProductionError,
    _direct_invocation_groups,
    _materialized_audit_authority_records,
    _require_checkpoint_manifest_identity,
    _require_raw_manifest_identity,
    _require_reconstructed_rows,
    _validate_relocated_training_admission,
    _resolve_descriptor_source,
    _compress_result_dumps,
    _remove_uncompressed_result_dumps,
    assemble_and_publish_b1_metrics,
    assemble_and_publish_b1_metrics_test_only,
    reconstruct_b1_mechanical_from_artifact,
    reread_materialized_digest_records,
    stage_reviewed_b0_evidence,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_artifact import (
    _validate_materialized_b0,
    MetricsArtifactError,
    TABLE_KEY_FIELDS,
    validate_metrics_only_manifest,
    validate_prospective_output_cap,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_training_assembly import (
    assemble_b1_metrics_training,
    finalize_audit_table_bindings,
)
from tests.experiments.candidates.capability_bound_semantic_currentness_omrc_b01.test_b1_metrics_rehydrate import (
    ATTEMPT_ID,
)
from tests.experiments.candidates.capability_bound_semantic_currentness_omrc_b01.test_b1_metrics_training_assembly import (
    _admission as training_admission,
    _raw_slice as training_raw_slice,
    _shared_policy_tables,
    _telemetry as training_telemetry,
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(
        value, ensure_ascii=True, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii") + b"\n")


def test_mechanical_source_descriptor_rejects_sha_and_pointer_tamper(
    tmp_path: Path,
) -> None:
    source = tmp_path / "worker.json"
    _write_json(source, {"raw_evidence": {"value": 7}})
    descriptor = {
        "source_relative_path": "worker.json",
        "source_file_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "json_pointer": "/raw_evidence",
    }
    assert _resolve_descriptor_source(tmp_path, descriptor) == {"value": 7}

    bad_sha = {**descriptor, "source_file_sha256": "0" * 64}
    with pytest.raises(B1MetricsProductionError, match="source SHA differs"):
        _resolve_descriptor_source(tmp_path, bad_sha)
    bad_pointer = {**descriptor, "json_pointer": "/raw_evidence/missing"}
    with pytest.raises(B1MetricsProductionError, match="pointer is absent"):
        _resolve_descriptor_source(tmp_path, bad_pointer)


def test_consumer_rejects_coordinated_rehash_identity_resource_replay_and_checkpoint_classes() -> None:
    identity = {
        "attempt_id": "attempt-1",
        "implementation_commit": "1" * 40,
        "source_conformance_sha256": "2" * 64,
    }
    raw = {
        "attempt_id": "attempt-1",
        "seed": 21101,
        "arm": "STRUCT-CURRENTNESS-GRU",
        "full_bindings": {
            "implementation_commit": "1" * 40,
            "source_conformance_sha256": "2" * 64,
        },
    }
    _require_raw_manifest_identity(raw, identity)
    attacker_rehashed_raw = deepcopy(raw)
    attacker_rehashed_raw["attempt_id"] = "attempt-2"
    with pytest.raises(B1MetricsProductionError, match="manifest source identity"):
        _require_raw_manifest_identity(attacker_rehashed_raw, identity)

    for evidence_class in (
        "training admission", "training telemetry", "policy replay wrapper",
        "policy replay admission", "policy replay raw receipt",
    ):
        published = [{"identity": evidence_class, "sha256": "a" * 64, "value": 1}]
        attacker_rehashed = [{
            "identity": evidence_class, "sha256": "b" * 64, "value": 2,
        }]
        with pytest.raises(B1MetricsProductionError, match="reopened evidence"):
            _require_reconstructed_rows(
                evidence_class, attacker_rehashed, published
            )

    binding = {
        "attempt_id": "attempt-1",
        "implementation_commit": "1" * 40,
        "source_conformance_sha256": "2" * 64,
        "seed": 21101,
        "arm": "STRUCT-CURRENTNESS-GRU",
        "completed_rollout_updates": 48,
    }
    record = {"binding": dict(binding), "update": 48}
    _require_checkpoint_manifest_identity(binding, raw, record, identity)
    attacker_rehashed_binding = {
        **binding, "source_conformance_sha256": "3" * 64,
    }
    attacker_rehashed_record = {
        "binding": dict(attacker_rehashed_binding), "update": 48,
    }
    with pytest.raises(B1MetricsProductionError, match="checkpoint envelope"):
        _require_checkpoint_manifest_identity(
            attacker_rehashed_binding, raw, attacker_rehashed_record, identity
        )


def test_relocated_training_admission_revalidates_after_atomic_root_rename(
    tmp_path: Path,
) -> None:
    old_root = tmp_path / ".artifact.partial-old"
    final_root = tmp_path / "artifact"
    admission_path = final_root / "admissions" / "slot-admission.json"
    admission_path.parent.mkdir(parents=True)
    historical_bound = old_root / "admissions" / admission_path.name
    historical_raw = historical_bound.with_name(
        f".{historical_bound.name}.raw-test.json"
    )
    relocated_raw = admission_path.parent / historical_raw.name
    receipt = {
        "passed": True,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "available_physical_bytes": 5 * 1024**3,
        "effective_available_bytes": 5 * 1024**3,
    }
    _write_json(relocated_raw, receipt)
    executable = Path(os.path.abspath(sys.executable))
    preflight = b1.CANONICAL_PREFLIGHT
    bound = {
        "schema": b1.B1_BOUND_ADMISSION_SCHEMA,
        "attempt_id": "attempt-1",
        "run_name": b1.B1_RUN_NAME,
        "arm": "STRUCT-CURRENTNESS-GRU",
        "seed": 21101,
        "implementation_commit": "1" * 40,
        "source_conformance_sha256": "2" * 64,
        "bound_receipt_path": str(historical_bound.resolve(strict=False)),
        "raw_output_path": str(historical_raw.resolve(strict=False)),
        "python_executable": str(executable),
        "python_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "preflight_script": str(preflight),
        "preflight_script_sha256": hashlib.sha256(preflight.read_bytes()).hexdigest(),
        "exact_command": [
            str(executable), str(preflight), "admit-memory", "--out",
            str(historical_raw.resolve(strict=False)),
        ],
        "raw_receipt_sha256": hashlib.sha256(relocated_raw.read_bytes()).hexdigest(),
        "receipt": receipt,
    }
    _write_json(admission_path, bound)
    validated = _validate_relocated_training_admission(
        admission_path,
        bound,
        attempt_id="attempt-1",
        arm="STRUCT-CURRENTNESS-GRU",
        seed=21101,
        implementation_commit="1" * 40,
        source_conformance_sha256="2" * 64,
    )
    assert validated["bound_receipt_path"] != str(admission_path)

    relocated_raw.write_bytes(b"{}\n")
    with pytest.raises(B1MetricsProductionError, match="relocated training raw"):
        _validate_relocated_training_admission(
            admission_path,
            bound,
            attempt_id="attempt-1",
            arm="STRUCT-CURRENTNESS-GRU",
            seed=21101,
            implementation_commit="1" * 40,
            source_conformance_sha256="2" * 64,
        )


def test_unified_test_profile_fixture_carries_complete_rollout_inventory() -> None:
    training = training_raw_slice()
    assert training["slice"] == {"start_update": 0, "stop_update": 48}
    assert len(training["rollouts"]) == 48
    assert [row["update_before"] for row in training["rollouts"]] == list(range(48))
    assert [row["update_after"] for row in training["rollouts"]] == list(range(1, 49))


def _b0_source(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    source = tmp_path / "reviewed-b0-source"
    worker = source / "workers" / "slot-00" / "result.json"
    evaluation = {"heldout": {"return": 1.25, "count": 2}}
    arm = {"records": {"diagnostics": {"evaluation": evaluation}}}
    _write_json(worker, arm)
    _write_json(source / "manifest.json", {
        "schema": "reviewed-b0-test", "arm_records": [arm],
    })
    files = sorted(
        (path for path in source.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(source).as_posix(),
    )
    inventory = [{
        "path": path.relative_to(source).as_posix(),
        "byte_count": len(path.read_bytes()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    } for path in files]
    manifest = source / "manifest.json"
    return source, {
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "manifest_bytes": len(manifest.read_bytes()),
        "reviewed_receipt_sha256": "4" * 64,
        "inventory_sha256": hashlib.sha256(
            json.dumps(inventory, ensure_ascii=True, allow_nan=False, sort_keys=True,
                       separators=(",", ":")).encode("ascii")
        ).hexdigest(),
        "file_count": len(files),
        "total_bytes": sum(len(path.read_bytes()) for path in files),
    }


def _add_checkpoint_slot(staging: Path, raw: dict, index: int) -> None:
    seed, arm = raw["seed"], raw["arm"]
    durable = staging / "arm-seeds" / f"{index:02d}-seed-{seed}-{arm}"
    durable.mkdir(parents=True)
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    checkpoints = []
    for update in (0, 12, 24, 48):
        trainer = RecurrentPPOTrainer(
            model, run_name=raw["run_name"], seed=seed,
            optimizer=make_adam(model), address_u64=addressing.u64,
        )
        trainer.counters = PPOCounters(
            # Checkpoint envelopes preserve the frozen PPO contract even when
            # the surrounding TEST_ONLY publication uses one episode/update.
            rollout_updates=update, adam_steps=update * 16,
            train_episodes=update * 8, train_transitions=update * 8 * 152,
            train_decisions=update * 8 * 24,
        )
        full = raw["full_bindings"]
        binding = B1CheckpointBinding(
            object_id="CBSC-OMRC-B01", attempt_id=ATTEMPT_ID,
            run_name=raw["run_name"], arm=arm, seed=seed,
            completed_rollout_updates=update,
            train_episode_ids_sha256=full["train_episode_ids_sha256"],
            full_training_tape_digest=full["full_training_tape_digest"],
            full_action_uniform_digest=full["full_action_uniform_digest"],
            ppo_configuration_digest=config_digest(PPOConfig()),
            implementation_commit="1" * 40,
            source_conformance_sha256="2" * 64,
        )
        envelope = capture_b1_checkpoint(trainer, binding)
        path = durable / f"checkpoint-update-{update}.pt"
        save_b1_checkpoint(path, envelope)
        payload = path.read_bytes()
        inner = envelope["recurrent_ppo_checkpoint"]
        checkpoints.append({
            "update": update, "relative_path": path.name,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "byte_count": len(payload), "binding": asdict(binding),
            "counters": dict(inner["counters"]), "digests": dict(inner["digests"]),
            "model_parameter_digest": model_parameter_digest_from_state(inner["model_state"]),
        })
    raw["checkpoints_created"] = checkpoints
    raw["scientific_branch"] = None


def _write_direct_invocations(
    staging: Path, raw_group: list[dict[str, object]], slot_index: int = 0,
) -> None:
    seed, arm = raw_group[0]["seed"], raw_group[0]["arm"]
    tag = f"{slot_index:02d}-seed-{seed}-{arm}"
    for order, raw in enumerate(raw_group):
        interval = raw["slice"]
        invocation = f"slice-{interval['start_update']:02d}-{interval['stop_update']:02d}"
        admission = training_admission(order)
        _write_json(
            staging / "admissions" / f"{tag}-{invocation}-admission.json",
            {**admission, "receipt": {
                "available_physical_bytes": admission["available_physical_bytes"],
                "effective_available_bytes": admission["effective_available_bytes"],
            }},
        )
        _write_json(
            staging / "workers" / tag / invocation / "telemetry.json",
            training_telemetry(
                interval["start_update"], interval["stop_update"], order
            )["measurement"],
        )
        _write_json(
            staging / "workers" / tag / invocation / "result.json",
            {"raw_evidence": raw},
        )
    _compress_result_dumps(staging)
    _remove_uncompressed_result_dumps(staging)


def test_formal_production_api_accepts_no_tables_models_fact_booleans_or_factories() -> None:
    parameters = set(inspect.signature(assemble_and_publish_b1_metrics).parameters)
    assert not parameters & {
        "tables", "shared_tables", "policy_tables", "training_tables",
        "models", "model", "factory", "fact_booleans", "mechanical",
        "implementation_commit", "source_conformance_sha256", "b0_evidence",
        "law_digests", "test_only",
    }
    assert {
        "staging_root", "final_path", "grouped_raw_slices",
        "authority_witness", "incident_lineage_witness", "policy_replay_witness",
        "allowed_root",
    } == parameters


def test_formal_entry_refuses_before_mutation_and_runtime_surface_is_bound(
    tmp_path: Path,
) -> None:
    # Section-11 recast (owner decision 3, 2026-09-02): the two
    # `REPAIR_REQUIRED: formal metrics publication awaits whole-pipeline CLEAN
    # review` raises are removed.  The formal entry still refuses a caller that
    # supplies no canonical authority witness, and still mutates nothing first.
    staging = tmp_path / ".result.partial-test"
    staging.mkdir()
    before = list(staging.rglob("*"))
    with pytest.raises((B1MetricsProductionError, TypeError, ValueError)):
        assemble_and_publish_b1_metrics(
            staging_root=staging,
            final_path=tmp_path / "result",
            grouped_raw_slices=(),
            authority_witness=None,
            incident_lineage_witness=make_b1_incident_lineage_witness(
                [], allowed_root=tmp_path
            ),
            policy_replay_witness=None,
            allowed_root=tmp_path,
        )
    assert list(staging.rglob("*")) == before
    assert not (tmp_path / "result").exists()
    for name in (
        "b1_metrics_rehydrate.py", "b1_metrics_policy_assembly.py",
        "b1_metrics_training_assembly.py", "b1_metrics_production.py",
    ):
        assert any(path.endswith(name) for path in b1.CANONICAL_SOURCE_SURFACE)


def test_orchestrator_complete_assembly_refuses_empty_evidence_and_cannot_publish(
    tmp_path: Path,
) -> None:
    # Was gated by `_refuse_pending_analysis()`; that gate is demoted.  The
    # assembly still refuses an empty raw-slice sequence and publishes nothing.
    staging = tmp_path / ".formal.partial-test"
    staging.mkdir()
    with pytest.raises(b1.B1OrchestrationError):
        b1._assemble_and_publish_complete(
            staging=staging,
            final_path=tmp_path / "formal",
            implementation_commit="1" * 40,
            source_receipt={"source_conformance_sha256": "2" * 64},
            b0_evidence={}, raw_slices=[], admissions=[], telemetry_records=[],
            laws={}, incident_lineage_witness=make_b1_incident_lineage_witness(
                [], allowed_root=b1.CONFINED_ROOT
            ),
        )
    assert not (tmp_path / "formal").exists()
    assert list(staging.rglob("*")) == []


@pytest.mark.parametrize(
    "intervals",
    [((0, 12), (12, 24), (24, 48)), ((0, 24), (24, 48))],
    ids=("fresh-three", "resume-two"),
)
def test_direct_invocation_groups_bind_attempt_order_and_feed_training_assembly(
    tmp_path: Path, intervals: tuple[tuple[int, int], ...],
) -> None:
    raw_group = [training_raw_slice(start, stop) for start, stop in intervals]
    _write_direct_invocations(tmp_path, raw_group)
    admissions, telemetry, sources = _direct_invocation_groups(
        tmp_path, [raw_group], [0]
    )
    assert [row["attempt_order"] for row in admissions[0]] == list(range(len(intervals)))
    assert [row["attempt_order"] for row in telemetry[0]] == list(range(len(intervals)))
    shared, policy = _shared_policy_tables()
    packet = assemble_b1_metrics_training(
        raw_slice_groups=[raw_group], admission_groups=admissions,
        telemetry_groups=telemetry, shared_tables=shared,
        policy_tables=policy, raw_source_groups=sources, test_only=True,
    )
    assert [row["attempt_order"] for row in packet["tables"]["resource_admissions"]] == list(
        range(len(intervals))
    )
    assert [
        (row["slice_start_update"], row["slice_stop_update"])
        for row in packet["tables"]["telemetry"]
    ] == list(intervals)


def test_materialized_reread_exposes_table_checkpoint_and_inventory_drift(
    tmp_path: Path,
) -> None:
    table = tmp_path / "metrics" / "raw" / "tape_transitions.jsonl"
    checkpoint = tmp_path / "arm-seeds" / "slot" / "checkpoint-update-0.pt"
    table.parent.mkdir(parents=True)
    checkpoint.parent.mkdir(parents=True)
    table.write_bytes(b"{}\n")
    checkpoint.write_bytes(b"checkpoint")
    table_sha = hashlib.sha256(table.read_bytes()).hexdigest()
    checkpoint_sha = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    table_inventory = [{
        "table": "tape_transitions",
        "relative_path": "metrics/raw/tape_transitions.jsonl",
        "sha256": table_sha, "byte_count": 3,
    }]
    artifact_inventory = [{
        "relative_path": "metrics/raw/tape_transitions.jsonl",
        "sha256": table_sha, "byte_count": 3,
    }, {
        "relative_path": "arm-seeds/slot/checkpoint-update-0.pt",
        "sha256": checkpoint_sha, "byte_count": len(b"checkpoint"),
    }]
    clean = reread_materialized_digest_records(
        tmp_path, table_inventory=table_inventory,
        artifact_inventory=artifact_inventory,
    )
    assert all(row["expected_sha256"] == row["actual_sha256"] for row in clean["tables"])

    table.write_bytes(b"tampered\n")
    drift = reread_materialized_digest_records(
        tmp_path, table_inventory=table_inventory,
        artifact_inventory=artifact_inventory,
    )
    assert drift["tables"][0]["expected_sha256"] != drift["tables"][0]["actual_sha256"]
    checkpoint.write_bytes(b"checkpoint-drift")
    drift = reread_materialized_digest_records(
        tmp_path, table_inventory=table_inventory,
        artifact_inventory=artifact_inventory,
    )
    assert drift["checkpoints"][0]["expected_byte_count"] != drift["checkpoints"][0]["actual_byte_count"]
    table.unlink()
    with pytest.raises(B1MetricsProductionError, match="absent"):
        reread_materialized_digest_records(
            tmp_path, table_inventory=table_inventory,
            artifact_inventory=artifact_inventory,
        )


def test_typed_audit_authority_is_bound_only_after_materialized_reread(
    tmp_path: Path,
) -> None:
    rows = [{"run_order": 0, "seed": 1}, {"run_order": 0, "seed": 2}]
    payload = b"".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode("ascii") + b"\n"
        for row in rows
    )
    path = tmp_path / "metrics" / "raw" / "training_episodes.jsonl"
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    audit = {
        "run_order": 0, "attempt_order": 0, "seed_or_minus_one": -1,
        "arm_or_minus_one": -1, "audit_code": "TABLE:training_episodes",
        "authority_type": "CANONICAL_TABLE_AUTHORITY",
        "source_table": "training_episodes",
        "source_key_range": {
            "key_fields": ["run_order", "seed"], "first_key": [0, 1],
            "last_key": [0, 2],
        },
        "source_raw_slice": None, "fact_name": None,
        "expected": {"row_count": 2}, "observed": None,
        "expected_sha256": hashlib.sha256(payload).hexdigest(),
        "actual_sha256": None,
        "binding_status": "PENDING_MATERIALIZED_TABLE_REREAD",
        "source_relative_path": None, "json_pointer": None,
        "source_file_sha256": None, "payload_shape": None,
        "payload_dtype": None, "payload_nonzero_count": None,
    }
    inventory = [{
        "table": "training_episodes",
        "relative_path": "metrics/raw/training_episodes.jsonl",
        "sha256": hashlib.sha256(payload).hexdigest(), "byte_count": len(payload),
    }]
    reread = _materialized_audit_authority_records(
        tmp_path, audit_rows=[audit], table_inventory=inventory
    )
    final = finalize_audit_table_bindings([audit], reread)
    assert final[0]["binding_status"] == "BOUND_MATERIALIZED_TABLE_REREAD"
    assert final[0]["observed"] == {"row_count": 2}
    path.write_bytes(
        payload + json.dumps(
            {"run_order": 0, "seed": 3}, sort_keys=True, separators=(",", ":")
        ).encode("ascii") + b"\n"
    )
    tampered = _materialized_audit_authority_records(
        tmp_path, audit_rows=[audit], table_inventory=inventory
    )
    with pytest.raises(ValueError, match="materialized table reread binding differs"):
        finalize_audit_table_bindings([audit], tampered)
    path.unlink()
    with pytest.raises(B1MetricsProductionError, match="absent after stage one"):
        _materialized_audit_authority_records(
            tmp_path, audit_rows=[audit], table_inventory=inventory
        )


def test_reviewed_b0_is_copied_losslessly_and_every_evaluator_leaf_is_nonpolar(
    tmp_path: Path,
) -> None:
    source, authority = _b0_source(tmp_path)
    staging = tmp_path / ".b0.partial-test"
    staging.mkdir()
    descriptor = stage_reviewed_b0_evidence(
        source_root=source, staging_root=staging, expected=authority,
        allowed_root=tmp_path, test_only=True,
    )


def test_reviewed_b0_source_is_snapshotted_once_before_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, authority = _b0_source(tmp_path)
    source_files = {
        path.resolve() for path in source.rglob("*") if path.is_file()
    }
    original = Path.read_bytes
    reads: dict[Path, int] = {}

    def unstable_read(path: Path) -> bytes:
        resolved = path.resolve()
        if resolved in source_files:
            reads[resolved] = reads.get(resolved, 0) + 1
            if reads[resolved] > 1:
                return b"outcome-informed-source-mutation\n"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", unstable_read)
    staging = tmp_path / ".b0-snapshot.partial-test"
    staging.mkdir()
    descriptor = stage_reviewed_b0_evidence(
        source_root=source, staging_root=staging, expected=authority,
        allowed_root=tmp_path, test_only=True,
    )
    _validate_materialized_b0(staging, descriptor)
    assert reads == {path: 1 for path in source_files}
    _validate_materialized_b0(staging, descriptor)
    index = json.loads(
        (staging / descriptor["nonpolarity_index"]["relative_path"]).read_text(
            encoding="ascii"
        )
    )
    assert len(index["evaluator_leaves"]) == 4
    assert all(
        row[flag] is False
        for row in index["evaluator_leaves"]
        for flag in (
            "scientific_eligible", "classifier_eligible",
            "threshold_tuning_eligible", "b2_trigger_eligible", "promotion_eligible",
        )
    )


def test_result_dumps_publish_as_deterministic_gzip_with_decoded_locators(
    tmp_path: Path,
) -> None:
    roots = (tmp_path / "a", tmp_path / "b")
    payloads = {}
    for root in roots:
        worker = root / "workers/slot/slice-00-48/result.json"
        replay = root / "policy-replay/00/result.json"
        _write_json(worker, {"raw_evidence": {"value": 1}})
        _write_json(replay, {"policy_decisions": [{"value": 2}]})
        payloads[root] = worker.read_bytes()
        _compress_result_dumps(root)
    first = roots[0] / "workers/slot/slice-00-48/result.json.gz"
    second = roots[1] / "workers/slot/slice-00-48/result.json.gz"
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes()[3] & 0x08 == 0  # empty gzip filename
    assert first.read_bytes()[4:8] == b"\0\0\0\0"  # mtime=0
    assert gzip.decompress(first.read_bytes()) == payloads[roots[0]]
    descriptor = {
        "source_relative_path": first.relative_to(roots[0]).as_posix(),
        "source_file_sha256": hashlib.sha256(payloads[roots[0]]).hexdigest(),
        "json_pointer": "/raw_evidence",
    }
    assert _resolve_descriptor_source(roots[0], descriptor) == {"value": 1}
    _remove_uncompressed_result_dumps(roots[0])
    assert not (roots[0] / "workers/slot/slice-00-48/result.json").exists()
    assert first.is_file()


def test_unified_test_profile_runs_canonical_a_b_c_and_publishes_15_tables(
    tmp_path: Path,
) -> None:
    training = training_raw_slice()
    training.update({
        "schema": B1_RAW_EVIDENCE_SCHEMA, "attempt_id": ATTEMPT_ID,
        "scientific_branch": None, "train_tapes": [],
    })
    training["full_bindings"].update({
        "train_episode_ids_sha256": hashlib.sha256(
            canonical_json_bytes(list(range(48)))
        ).hexdigest(),
        "implementation_commit": "1" * 40,
        "source_conformance_sha256": "2" * 64,
    })
    heldout_records = {}
    for seed in sorted({seed for seed, _ in B1_SLOT_ORDER}):
        host = DynamicHost(addressing.B1_RUN, seed)
        heldout_records[seed] = [{
            "identity": asdict(tape.identity),
            "primitive_digest_observed": tape.primitive_digest,
            "draw_digest_observed": tape.generation_audit.draw_digest,
            "draw_count_observed": tape.generation_audit.draw_count,
        } for tape in (
            host.build_stochastic(addressing.EVAL_STOCHASTIC, 0),
            host.build_motif(0),
        )]
    groups = tuple(({
        "schema": B1_RAW_EVIDENCE_SCHEMA, "attempt_id": ATTEMPT_ID,
        "run_name": addressing.B1_RUN, "seed": seed, "arm": arm,
        "scientific_branch": None,
        "slice": {"start_update": 0, "stop_update": 48},
        "full_bindings": deepcopy(training["full_bindings"]),
        "train_tapes": [], "evaluation_tapes": deepcopy(heldout_records[seed]),
    },) for seed, arm in B1_SLOT_ORDER)
    training["evaluation_tapes"] = deepcopy(heldout_records[training["seed"]])
    groups = ((training,), *groups[1:])
    staging = tmp_path / ".metrics.partial-test"
    staging.mkdir()
    for index in (1, 5, 9):
        _add_checkpoint_slot(staging, groups[index][0], index)
    _add_checkpoint_slot(staging, groups[0][0], 0)

    tag = "00-seed-21101-STRUCT-CURRENTNESS-GRU"
    invocation = "slice-00-48"
    admission = {
        "attempt_id": ATTEMPT_ID,
        "run_name": groups[0][0]["run_name"],
        "seed": 21101, "arm": "STRUCT-CURRENTNESS-GRU",
        "receipt": {
            "available_physical_bytes": 5 * 1024**3,
            "effective_available_bytes": 5 * 1024**3,
        },
    }
    _write_json(
        staging / "admissions" / f"{tag}-{invocation}-admission.json", admission
    )
    _write_json(
        staging / "workers" / tag / invocation / "telemetry.json",
        training_telemetry()["measurement"],
    )
    _write_json(
        staging / "workers" / tag / invocation / "result.json",
        {
            "schema": "cbsc_omrc_b01_test_only_worker_result_v1",
            "raw_evidence": groups[0][0],
            "scientific_branch": None,
        },
    )
    b0_root, b0_authority = _b0_source(tmp_path)
    published = assemble_and_publish_b1_metrics_test_only(
        staging_root=staging, final_path=tmp_path / "metrics",
        grouped_raw_slices=groups,
        implementation_commit="1" * 40,
        source_conformance_sha256="2" * 64,
        b0_root=b0_root, b0_evidence=b0_authority,
        law_digests={name: value * 64 for name, value in (
            ("environment", "6"), ("adapter", "7"),
            ("token", "8"), ("analysis", "9"),
        )},
        incident_lineage_witness=make_b1_incident_lineage_witness(
            [], allowed_root=tmp_path
        ),
        allowed_root=tmp_path,
    )
    manifest = json.loads((published / "manifest.json").read_text(encoding="ascii"))
    assert len(manifest["table_inventory"]) == 15
    counts = {row["table"]: row["row_count"] for row in manifest["table_inventory"]}
    assert counts["training_episodes"] == 48
    assert counts["training_decisions"] == 48 * 24
    assert counts["optimizer_steps"] == 48 * 4
    assert counts["tape_transitions"] == 3 * 2 * 152
    assert counts["evaluator_decision_truth"] == 3 * 2 * 24
    assert manifest["schema"].endswith("test_only_v1")
    assert manifest["convergence_required"] is False
    assert manifest["formal_analysis_bound"] is False
    assert manifest["scientific_branch"] is None
    inputs = manifest["mechanical"]["inputs"]
    assert inputs["authority"] == "BOUND_ARTIFACT_EVIDENCE"
    assert inputs["raw_worker_sources"]
    assert all(
        source["source_relative_path"].endswith("/result.json.gz")
        for group in inputs["raw_worker_sources"] for source in group
    )
    summary = json.loads((published / "summary.json").read_text(encoding="ascii"))
    assert summary["schema"] == "cbsc_omrc_b01_b1_result_rule_summary_v1"
    assert (published / "summary.json").read_bytes() == canonical_json_bytes(summary) + b"\n"
    assert summary["descriptive_curves"]["raw_competence_flags"]
    assert not list(published.glob("workers/*/slice-*/result.json"))
    assert not list(published.glob("policy-replay/*/result.json"))
    assert list(published.glob("workers/*/slice-*/result.json.gz"))
    for group in inputs["raw_worker_sources"]:
        for source in group:
            assert _resolve_descriptor_source(published, source)
    audit_rows = [
        json.loads(line) for line in
        (published / "metrics/raw/audits.jsonl").read_text(encoding="ascii").splitlines()
    ]
    direct_audits = [
        row for row in audit_rows
        if str(row["authority_type"]).startswith("DIRECT_RAW_FACT")
    ]
    assert direct_audits
    assert all(
        row["source_relative_path"].endswith("/result.json.gz")
        for row in direct_audits
    )
    assert all(
        (published / row["source_relative_path"]).is_file()
        for row in direct_audits
    )
    published_tables = {
        descriptor["table"]: [
            json.loads(line) for line in
            (published / descriptor["relative_path"]).read_text(
                encoding="ascii"
            ).splitlines()
        ]
        for descriptor in manifest["table_inventory"]
    }
    assert manifest["mechanical"]["mechanical_components"]["work"] is True
    assert manifest["mechanical"]["mechanical_components"]["finite"] is True
    assert len(list(published.glob("arm-seeds/*/checkpoint-update-*.pt"))) == 16
    assert [row["table"] for row in manifest["table_inventory"]] == list(TABLE_KEY_FIELDS)
    for descriptor in manifest["table_inventory"]:
        assert len(published_tables[descriptor["table"]]) == descriptor["row_count"]
    assert list((published / "b0-reviewed-evidence").rglob("*"))
    assert list((published / "admissions").glob("*.json"))
    assert list(published.glob("workers/*/slice-*/telemetry.json"))
    actual_bytes = sum(path.stat().st_size for path in published.rglob("*") if path.is_file())
    prospective = validate_prospective_output_cap(
        artifact_inventory=manifest["artifact_inventory"], manifest=manifest
    )
    assert prospective["total_bytes"] <= 536_870_912
    assert actual_bytes == manifest["durable_size_bytes"]
    assert actual_bytes <= 536_870_912
    assert manifest["formal_capacity_projection"]["performance_disposition"] == "REPAIR_REQUIRED"
    assert manifest["formal_capacity_projection"]["depends_on_observed_or_test_bytes"] is False

    # Pin the retained RAW calculation directly, without a consumer launch gate.
    from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_training_assembly import (
        reconstruct_raw_competence_from_tables,
    )
    calculated_raw = reconstruct_raw_competence_from_tables(published_tables, test_only=True)
    assert calculated_raw == published_tables["raw_competence"]
    altered_tables = dict(published_tables)
    altered_tables["raw_competence"] = deepcopy(published_tables["raw_competence"])
    altered_tables["raw_competence"][0]["raw_competence_pass"] = not bool(
        altered_tables["raw_competence"][0]["raw_competence_pass"]
    )
    assert reconstruct_raw_competence_from_tables(altered_tables, test_only=True) == calculated_raw
    assert calculated_raw != altered_tables["raw_competence"]

    # Existing readback still detects changed table and summary bytes separately.
    raw_path = published / "metrics/raw/raw_competence.jsonl"
    original_raw = raw_path.read_bytes()
    raw_path.write_bytes(b"".join(
        canonical_json_bytes(row) + b"\n" for row in altered_tables["raw_competence"]
    ))
    with pytest.raises(MetricsArtifactError, match="table byte count/digest differs"):
        validate_metrics_only_manifest(manifest, root=published, allow_test_only=True)
    raw_path.write_bytes(original_raw)
    summary_path = published / "summary.json"
    original_summary = summary_path.read_bytes()
    summary["descriptive_curves"]["raw_competence_flags"][0]["raw_competence_pass"] = (
        altered_tables["raw_competence"][0]["raw_competence_pass"]
    )
    summary_path.write_bytes(canonical_json_bytes(summary) + b"\n")
    with pytest.raises(MetricsArtifactError):
        validate_metrics_only_manifest(manifest, root=published, allow_test_only=True)
    summary_path.write_bytes(original_summary)


def test_replay_resource_projection_keeps_partial_status_and_original_receipt(tmp_path):
    from types import SimpleNamespace
    from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import b1_metrics_production as production
    from tests.experiments.candidates.capability_bound_semantic_currentness_omrc_b01.test_b1_section11_recast import _measurement

    raw = tmp_path / "policy-replay/00/.admission.json.raw-original.json"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b'{"original":true}\n')
    raw_digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    admission = {"raw_output_path": "C:/old/pub_r05/policy-replay/00/" + raw.name,
                 "raw_receipt_sha256": raw_digest,
                 "receipt": {"available_physical_bytes": 5 * 1024**3,
                             "effective_available_bytes": 5 * 1024**3}}
    payload = canonical_json_bytes(admission)
    slot = SimpleNamespace(
        admission_bytes=payload,
        telemetry_bytes=canonical_json_bytes({"measurement": _measurement(measurement_complete=False)}),
        raw_receipt_relative_path=raw.relative_to(tmp_path).as_posix(),
        raw_receipt_sha256=raw_digest, original_slot_index=0, seed=21101,
        arm="STRUCT-CURRENTNESS-GRU", admission_sha256=hashlib.sha256(payload).hexdigest(),
        admission_relative_path="policy-replay/00/admission.json",
        telemetry_relative_path="policy-replay/00/telemetry.json", telemetry_sha256=None,
    )
    witness = SimpleNamespace(slots=(slot,), attempt_id="test-original")
    _, telemetry, resources = production._policy_replay_resource_authority(witness, allowed_root=tmp_path)
    assert slot.admission_bytes == payload
    assert json.loads(payload)["raw_output_path"].startswith("C:/old/")
    assert resources[0]["measurement_complete"] is False
    assert resources[0]["peak_rss_bytes"] == 1024
    assert telemetry[0]["measurement"]["resources_unmeasured"] is True
    raw.write_bytes(b'{"different":true}\n')
    with pytest.raises(B1MetricsProductionError, match="raw admission receipt differs"):
        production._policy_replay_resource_authority(witness, allowed_root=tmp_path)
