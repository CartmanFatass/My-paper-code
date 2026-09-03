from __future__ import annotations

import inspect
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import b1
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import b1_artifact
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.artifact import (
    canonical_json_bytes,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_artifact import (
    publish_b1_incident,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine import (
    B1_RAW_EVIDENCE_SCHEMA,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_worker import (
    WORKER_RESULT_SCHEMA,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1AttemptLedger,
    B1LedgerBinding,
    B1ResumeCheckpointBinding,
    B1SlotLedgerEntry,
    B1SlotStatus,
    B1_LEDGER_PUBLICATION_MODE,
    B1_LEDGER_SCHEMA,
    B1_RESOURCE_CAPS,
    B1_SEEDS,
    B1_SLOT_ORDER,
    B1Plan,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b0 import ARMS
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.telemetry import (
    ResourceCaps,
    TelemetryError,
)
from scripts import run_cbsc_omrc_b01_b1 as cli


def test_execution_order_is_fixed_seed_major_then_arm() -> None:
    assert b1.ARM_SEED_ORDER == tuple((seed, arm) for seed in B1_SEEDS for arm in ARMS)


def _ordered_raw_slices() -> list[dict]:
    return [
        {
            "schema": B1_RAW_EVIDENCE_SCHEMA,
            "run_name": "CBSC-OMRC-B1-THREE-SEED-SCOUT",
            "seed": seed,
            "arm": arm,
            "slice": {"start_update": start, "stop_update": stop},
            "scientific_branch": None,
        }
        for seed, arm in b1.ARM_SEED_ORDER
        for start, stop in ((0, 12), (12, 24), (24, 48))
    ]


def _b0_evidence() -> dict[str, object]:
    return {
        "manifest_sha256": b1.B0_REVIEWED_AUTHORITY["manifest_sha256"],
        "manifest_bytes": b1.B0_REVIEWED_AUTHORITY["manifest_bytes"],
        "reviewed_receipt_sha256": b1.B0_REVIEWED_RECEIPT_SHA256,
        "inventory_sha256": b1.B0_REVIEWED_AUTHORITY["inventory_sha256"],
        "file_count": b1.B0_REVIEWED_AUTHORITY["file_count"],
        "total_bytes": b1.B0_REVIEWED_AUTHORITY["total_bytes"],
    }


def _scientific_identity() -> dict[str, object]:
    plan = B1Plan()
    return {
        "object_id": plan.object_id,
        "innovator_selection_request_id": plan.innovator_selection_request_id,
        "innovator_selection_archive_path": plan.innovator_selection_archive_path,
        "innovator_selection_response_sha256": plan.innovator_selection_response_sha256,
        "literal_binding_request_id": plan.literal_binding_request_id,
        "literal_binding_archive_path": plan.literal_binding_archive_path,
        "literal_binding_response_sha256": plan.literal_binding_response_sha256,
        "metrics_only_request_id": plan.metrics_only_request_id,
        "metrics_only_archive_path": plan.metrics_only_archive_path,
        "metrics_only_response_sha256": plan.metrics_only_response_sha256,
    }


def test_raw_slice_reducer_accepts_36_contiguous_seed_major_slices() -> None:
    groups = b1._validate_raw_slice_sequence(_ordered_raw_slices())
    assert len(groups) == 12
    assert all(len(group) == 3 for group in groups)
    assert [
        (group[0]["seed"], group[0]["arm"]) for group in groups
    ] == list(b1.ARM_SEED_ORDER)


@pytest.mark.parametrize("mutation", ["interleave", "reorder", "gap", "overlap", "duplicate"])
def test_raw_slice_reducer_rejects_interleave_reorder_gap_overlap_duplicate(mutation) -> None:
    raw = _ordered_raw_slices()
    if mutation == "interleave":
        raw[1], raw[3] = raw[3], raw[1]
    elif mutation == "reorder":
        raw[:3], raw[3:6] = raw[3:6], raw[:3]
    elif mutation == "gap":
        raw[1] = {**raw[1], "slice": {"start_update": 24, "stop_update": 48}}
    elif mutation == "overlap":
        raw[1] = {**raw[1], "slice": {"start_update": 0, "stop_update": 24}}
    else:
        raw.insert(1, dict(raw[0]))
    with pytest.raises(b1.B1OrchestrationError):
        b1._validate_raw_slice_sequence(raw)


def test_checkpoint_file_validation_rejects_deleted_and_tampered_bytes(
    monkeypatch, tmp_path
) -> None:
    seed, arm = b1.ARM_SEED_ORDER[0]
    tag = b1._slot_tag(0, seed, arm)
    durable = tmp_path / "arm-seeds" / tag
    durable.mkdir(parents=True)
    checkpoints = []
    for update in (0, 12, 24, 48):
        path = durable / f"checkpoint-update-{update}.pt"
        path.write_bytes(f"checkpoint-{update}".encode("ascii"))
        checkpoints.append({
            "update": update,
            "relative_path": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "byte_count": len(path.read_bytes()),
            "digests": {"minibatch_order": f"{update:064x}"},
        })
    raw = [{"checkpoints_created": checkpoints}]

    def fake_load(path):
        update = int(Path(path).stem.rsplit("-", 1)[1])
        return {
            "binding": {
                "attempt_id": "attempt", "run_name": "CBSC-OMRC-B1-THREE-SEED-SCOUT",
                "seed": seed, "arm": arm, "completed_rollout_updates": update,
                "implementation_commit": "a" * 40,
                "source_conformance_sha256": "b" * 64,
            },
            "recurrent_ppo_checkpoint": {"minibatch_order_chain": f"{update:064x}"},
        }

    monkeypatch.setattr(b1, "load_b1_checkpoint", fake_load)
    b1._validate_slot_checkpoint_files(
        tmp_path, 0, seed, arm, raw, attempt_id="attempt",
        implementation_commit="a" * 40, source_conformance_sha256="b" * 64,
    )

    checkpoints[1]["byte_count"] += 1
    with pytest.raises(b1.B1OrchestrationError, match="byte_count"):
        b1._validate_slot_checkpoint_files(
            tmp_path, 0, seed, arm, raw, attempt_id="attempt",
            implementation_commit="a" * 40, source_conformance_sha256="b" * 64,
        )
    checkpoints[1]["byte_count"] -= 1

    target = durable / "checkpoint-update-24.pt"
    original = target.read_bytes()
    target.unlink()
    with pytest.raises(b1.B1OrchestrationError):
        b1._validate_slot_checkpoint_files(
            tmp_path, 0, seed, arm, raw, attempt_id="attempt",
            implementation_commit="a" * 40, source_conformance_sha256="b" * 64,
        )
    target.write_bytes(bytes([original[0] ^ 1]) + original[1:])
    with pytest.raises(b1.B1OrchestrationError, match="SHA"):
        b1._validate_slot_checkpoint_files(
            tmp_path, 0, seed, arm, raw, attempt_id="attempt",
            implementation_commit="a" * 40, source_conformance_sha256="b" * 64,
        )


def test_formal_entrypoints_have_no_engine_worker_preflight_monitor_or_source_injection() -> None:
    assert tuple(inspect.signature(b1.run_b1_start).parameters) == (
        "final_path", "implementation_commit", "b0_root",
    )
    assert tuple(inspect.signature(b1.run_b1_resume).parameters) == (
        "final_path", "implementation_commit", "b0_root", "incident_root",
    )
    with pytest.raises(TypeError):
        b1.run_b1_start(  # type: ignore[call-arg]
            final_path=Path("unused"), implementation_commit="a" * 40,
            b0_root=Path("unused"), engine=object(),
        )


def test_canonical_source_surface_binds_actual_factory_worker_cli_and_preflight() -> None:
    surface = set(b1.CANONICAL_SOURCE_SURFACE)
    assert len(b1.CANONICAL_SOURCE_SURFACE) == len(surface)
    assert (
        set(b1.LiteralB1ArmSeedEngine.source_paths)
        - {
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_analysis.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_evidence.py",
        }
    ) <= surface
    for relative in (
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_contract.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_engine.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_worker.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_artifact.py",
        "scripts/run_cbsc_omrc_b01_b1.py",
        "scripts/hmasd_resource_preflight.py",
    ):
        assert relative in surface
    identity = b1.canonical_engine_identity()
    assert identity["module"] == b1.CANONICAL_ENGINE_MODULE
    assert identity["factory"] == "b1_engine"
    assert identity["type"] == "LiteralB1ArmSeedEngine"
    assert identity["factory_file"] == identity["type_file"]
    assert identity["worker_module"] == b1.CANONICAL_WORKER_MODULE


def test_cli_modes_are_fixed_and_reject_injection(capsys) -> None:
    # Section-11 recast (owner decision 3, 2026-09-02): readiness no longer
    # refuses on FORMAL_ANALYSIS_BOUND / READINESS_DISPOSITION; both are
    # recorded fields.  The source and B0 bindings still refuse when supplied
    # and unsatisfied, and `start` still binds them itself.
    assert cli.main(["readiness"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert document["engine_bound"] is True
    assert document["start_authorized"] is True
    assert document["decision"] == "DECISION_PENDING"
    assert document["production_assembly"] == list(b1.PRODUCTION_ASSEMBLY)
    assert document["production_assembly_ready"] is True
    assert document["readiness_disposition"] == "READY"
    assert document["blockers"] == []
    assert document["formal_analysis_record"]["gating"] is False
    assert document["formal_analysis_record"]["formal_analysis_bound"] is False
    assert document["formal_analysis_record"]["readiness_disposition"] == "REPAIR_REQUIRED"
    for argv in (
        ["readiness", "--engine", "evil:factory"],
        ["start", "--output", "x", "--implementation-commit", "a" * 40,
         "--b0-root", "x", "--preflight-script", "evil.py"],
        ["resume", "--output", "x", "--implementation-commit", "a" * 40,
         "--b0-root", "x", "--incident-root", "x", "--python", "evil.exe"],
    ):
        with pytest.raises(SystemExit):
            cli._parser().parse_args(argv)
    with pytest.raises(SystemExit):
        cli._parser().parse_args([
            "resume", "--output", "x", "--implementation-commit", "a" * 40,
            "--b0-root", "x", "--resume-checkpoint", "bare.pt",
        ])


def test_formal_start_blocks_uncommitted_surface_before_admission_or_output(tmp_path) -> None:
    destination = b1.CONFINED_ROOT / "test-only-b1-must-not-appear"
    assert not destination.exists()
    with pytest.raises(b1.B1OrchestrationError, match="BLOCKED_UNCOMMITTED"):
        b1.run_b1_start(
            final_path=destination,
            implementation_commit="e" * 40,
            b0_root=tmp_path / "absent-b0",
        )
    assert not destination.exists()


def test_b0_locator_rejects_arbitrary_and_manifest_only_evidence_roots(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(b1, "CONFINED_ROOT", tmp_path.resolve())
    root = tmp_path / "b0"
    root.mkdir()
    manifest = root / "manifest.json"
    manifest.write_bytes(b"{}\n")
    with pytest.raises(b1.B1OrchestrationError, match="reviewed r02 authority"):
        b1.locate_b0_evidence(root)

    payload = bytearray(b"x" * int(b1.B0_REVIEWED_AUTHORITY["manifest_bytes"]))
    manifest.write_bytes(payload)
    with pytest.raises(b1.B1OrchestrationError, match="reviewed r02 authority"):
        b1.locate_b0_evidence(root)
    authority = dict(b1.B0_REVIEWED_AUTHORITY)
    authority["manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    authority["manifest_bytes"] = len(manifest.read_bytes())
    monkeypatch.setattr(b1, "B0_REVIEWED_AUTHORITY", authority)
    with pytest.raises(b1.B1OrchestrationError, match="inventory"):
        b1.locate_b0_evidence(root)
    payload[-1] ^= 1
    manifest.write_bytes(payload)
    with pytest.raises(b1.B1OrchestrationError, match="reviewed r02 authority"):
        b1.locate_b0_evidence(root)


def test_parent_supervision_kills_test_only_sleeper_and_preserves_incident(tmp_path) -> None:
    result = tmp_path / "result.json"
    with pytest.raises(TelemetryError, match="wall_seconds"):
        b1.supervise_child(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            scratch_root=tmp_path / "scratch",
            durable_root=tmp_path,
            result_path=result,
            stdout_path=tmp_path / "stdout.log",
            stderr_path=tmp_path / "stderr.log",
            caps=ResourceCaps(wall_seconds=0.15),
            interval_seconds=0.02,
        )
    assert not result.exists()
    incident = json.loads((tmp_path / "supervisor-incident.json").read_text(encoding="utf-8"))
    assert incident["reason"] == "LIVE_RESOURCE_CAP_TERMINATION"
    assert incident["cap_failures"] == ["wall_seconds"]
    assert incident["scientific_branch"] is None


def test_parent_supervision_reads_create_only_test_result_and_measures_child(tmp_path) -> None:
    result = tmp_path / "result.json"
    raw = {
        "schema": B1_RAW_EVIDENCE_SCHEMA,
        "scientific_branch": None,
        "scientific_work_transitions": 300,
        "stage_measurements": [{
            "stage": "test-only-train", "wall_seconds": 0.2,
            "cpu_seconds": 0.1, "transitions": 100,
            "transitions_per_second": 500.0,
        }, {
            "stage": "test-only-evaluation", "wall_seconds": 0.1,
            "cpu_seconds": 0.05, "transitions": 200,
            "transitions_per_second": 2000.0,
        }],
    }
    payload = {"schema": WORKER_RESULT_SCHEMA, "raw_evidence": raw, "scientific_branch": None}
    code = (
        "import json,time,pathlib\n"
        "time.sleep(0.25)\n"
        f"pathlib.Path({str(result)!r}).write_text(json.dumps({payload!r}))"
    )
    raw, telemetry = b1.supervise_child(
        [sys.executable, "-c", code],
        scratch_root=tmp_path / "scratch", durable_root=tmp_path,
        result_path=result, stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log", interval_seconds=0.02,
        caps=B1_RESOURCE_CAPS,
    )
    assert raw["schema"] == B1_RAW_EVIDENCE_SCHEMA
    assert telemetry["measurement_complete"] is True
    assert telemetry["scientific_work_transitions"] == 300
    assert telemetry["stage_measurements"] == raw["stage_measurements"]
    assert telemetry["process_tree_peak_rss_bytes"] > 0
    assert telemetry["sample_count"] >= 2


def test_parent_supervision_short_lived_canonical_result_does_not_race_telemetry(
    tmp_path,
) -> None:
    result = tmp_path / "result.json"
    raw = {
        "schema": B1_RAW_EVIDENCE_SCHEMA,
        "scientific_branch": None,
        "scientific_work_transitions": 2,
        "stage_measurements": [{
            "stage": "test-only", "wall_seconds": 0.01, "cpu_seconds": 0.001,
            "transitions": 2, "transitions_per_second": 200.0,
        }],
    }
    payload = {
        "schema": WORKER_RESULT_SCHEMA,
        "raw_evidence": raw,
        "scientific_branch": None,
    }
    code = (
        "import json,time,pathlib\n"
        "time.sleep(0.08)\n"
        f"pathlib.Path({str(result)!r}).write_text(json.dumps({payload!r}))"
    )
    observed_raw, telemetry = b1.supervise_child(
        [sys.executable, "-c", code],
        scratch_root=tmp_path / "scratch", durable_root=tmp_path,
        result_path=result, stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log", interval_seconds=0.01,
        caps=B1_RESOURCE_CAPS,
    )
    assert observed_raw == raw
    assert telemetry["sample_count"] >= 2
    assert not (tmp_path / "supervisor-incident.json").exists()


def test_parent_supervision_poll_failure_kills_child_and_publishes_incident(
    monkeypatch, tmp_path
) -> None:
    def fail_poll(self, *, caps):
        raise TelemetryError("test-only telemetry backend failure")

    monkeypatch.setattr(b1.ProcessTreeMonitor, "poll_caps", fail_poll)
    with pytest.raises(TelemetryError, match="telemetry failed during supervision"):
        b1.supervise_child(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            scratch_root=tmp_path / "scratch", durable_root=tmp_path,
            result_path=tmp_path / "result.json",
            stdout_path=tmp_path / "stdout.log",
            stderr_path=tmp_path / "stderr.log", interval_seconds=0.01,
            caps=B1_RESOURCE_CAPS,
        )
    incident = json.loads(
        (tmp_path / "supervisor-incident.json").read_text(encoding="utf-8")
    )
    assert incident["reason"] == "TELEMETRY_FAILURE"
    assert incident["measurement_complete"] is False
    assert incident["scientific_branch"] is None


def test_worker_wrapper_and_engine_raw_schema_are_exact_and_science_null() -> None:
    raw = {
        "schema": B1_RAW_EVIDENCE_SCHEMA,
        "scientific_branch": None,
        "scientific_work_transitions": 1,
        "stage_measurements": [{
            "stage": "fixture", "wall_seconds": 1.0, "cpu_seconds": 0.5,
            "transitions": 1, "transitions_per_second": 1.0,
        }],
    }
    wrapper = {
        "schema": WORKER_RESULT_SCHEMA,
        "raw_evidence": raw,
        "scientific_branch": None,
    }
    assert b1._unwrap_worker_result(wrapper) == raw
    for changed in (
        {**wrapper, "schema": "wrong"},
        {**wrapper, "scientific_branch": "LOCAL_BRANCH"},
        {**wrapper, "extra": True},
        {**wrapper, "raw_evidence": {**raw, "schema": "wrong"}},
        {**wrapper, "raw_evidence": {**raw, "scientific_branch": "LOCAL_BRANCH"}},
    ):
        with pytest.raises(b1.B1OrchestrationError):
            b1._unwrap_worker_result(changed)


def test_stage_work_sum_refuses_missing_or_nonpositive_engine_measurements() -> None:
    assert b1._validate_stage_measurements([{
        "stage": "a", "wall_seconds": 2.0, "cpu_seconds": 1.0,
        "transitions": 6, "transitions_per_second": 3.0,
    }, {
        "stage": "b", "wall_seconds": 1.0, "cpu_seconds": 0.5,
        "transitions": 4, "transitions_per_second": 4.0,
    }])[0] == 10
    for invalid in (None, {}, [], [{"stage": "x", "transitions": 0}]):
        with pytest.raises(b1.B1OrchestrationError):
            b1._validate_stage_measurements(invalid)


def test_invocation_slice_allows_checkpoint_zero_resume_but_not_bare_nonzero() -> None:
    b1._validate_invocation_slice(0, 12, Path("checkpoint-update-0.pt"))
    b1._validate_invocation_slice(12, 24, Path("checkpoint-update-12.pt"))
    with pytest.raises(b1.B1OrchestrationError, match="requires a resume"):
        b1._validate_invocation_slice(12, 24, None)


def test_production_assembly_no_longer_refuses_on_the_demoted_formal_flags(tmp_path) -> None:
    # Was: `_refuse_pending_analysis()` raised REPAIR_REQUIRED because
    # FORMAL_ANALYSIS_BOUND was false.  Under the section-11 recast the residual
    # check is only the parallel-module protocol, which holds.
    destination = tmp_path / "must-not-publish"
    b1._refuse_pending_analysis()
    assert not destination.exists()
    monkeypatched = b1._readiness_result()
    assert monkeypatched.authorized is True
    assert monkeypatched.blockers == ()


def test_resume_consumes_only_artifact_bound_canonical_incident_ledger(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(b1, "CONFINED_ROOT", tmp_path.resolve())
    configuration_sha256 = hashlib.sha256(
        canonical_json_bytes(B1Plan().as_dict())
    ).hexdigest()
    binding = B1LedgerBinding(
        attempt_id="attempt-1",
        run_name="CBSC-OMRC-B1-THREE-SEED-SCOUT",
        implementation_commit="a" * 40,
        source_conformance_sha256="b" * 64,
        configuration_sha256=configuration_sha256,
        laws_sha256="c" * 64,
        b0_manifest_sha256=b1.B0_REVIEWED_AUTHORITY["manifest_sha256"],
        b0_manifest_bytes=b1.B0_REVIEWED_AUTHORITY["manifest_bytes"],
        b0_reviewed_receipt_sha256=b1.B0_REVIEWED_RECEIPT_SHA256,
        b0_inventory_sha256=b1.B0_REVIEWED_AUTHORITY["inventory_sha256"],
        b0_file_count=b1.B0_REVIEWED_AUTHORITY["file_count"],
        b0_total_bytes=b1.B0_REVIEWED_AUTHORITY["total_bytes"],
        **_scientific_identity(),
    )
    slots = []
    for index, (seed, arm) in enumerate(B1_SLOT_ORDER):
        slots.append(B1SlotLedgerEntry(
            binding=binding, slot_index=index, seed=seed, arm=arm,
            status=B1SlotStatus.INCOMPLETE if index == 0 else B1SlotStatus.PENDING,
            incident_sha256="d" * 64 if index == 0 else None,
            resume_checkpoint=None,
        ))
    ledger = B1AttemptLedger(
        schema=B1_LEDGER_SCHEMA, publication_mode=B1_LEDGER_PUBLICATION_MODE,
        binding=binding, slots=tuple(slots),
    )
    incident = publish_b1_incident(
        staging=None, incident_root=tmp_path / "incidents",
        allowed_root=tmp_path, attempt_id="attempt-1", category="TEST_ONLY",
        detail="test-only pre-checkpoint incident", completed_arm_seeds=[],
        test_only=True, attempt_ledger=ledger,
    )
    validated = b1.validate_resume_incident(
        incident, expected_commit="a" * 40, expected_source_sha256="b" * 64,
        expected_laws_sha256="c" * 64, expected_b0_evidence=_b0_evidence(),
    )
    assert validated["resume_slot"].slot_index == 0
    assert validated["resume_checkpoint"] is None
    assert b1_artifact.materialize_b1_incident_lineage(
        validated["lineage_witness"], allowed_root=tmp_path,
        expected_binding=binding,
    ) == [{
        "attempt_id": "attempt-1",
        "incident_manifest_sha256": hashlib.sha256(
            (incident / "incident.json").read_bytes()
        ).hexdigest(),
        "attempt_ledger_sha256": json.loads(
            (incident / "incident.json").read_text(encoding="ascii")
        )["attempt_ledger"]["sha256"],
        "incident_relative_path": (incident / "incident.json").relative_to(tmp_path).as_posix(),
    }]

    original_loader = b1_artifact.load_b1_attempt_ledger_from_incident

    def mutate_after_loader_read(*args, **kwargs):
        loaded = original_loader(*args, **kwargs)
        incident_manifest = incident / "incident.json"
        document = json.loads(incident_manifest.read_text(encoding="ascii"))
        document["detail"] = "mutated between validation reads"
        incident_manifest.write_bytes(canonical_json_bytes(document) + b"\n")
        return loaded

    with monkeypatch.context() as mutation:
        mutation.setattr(
            b1_artifact, "load_b1_attempt_ledger_from_incident",
            mutate_after_loader_read,
        )
        with pytest.raises(b1.B1OrchestrationError, match="changed during validation"):
            b1.validate_resume_incident(
                incident, expected_commit="a" * 40,
                expected_source_sha256="b" * 64,
                expected_laws_sha256="c" * 64,
                expected_b0_evidence=_b0_evidence(),
            )

    publish_document = json.loads((incident / "incident.json").read_text(encoding="ascii"))
    publish_document["detail"] = "test-only pre-checkpoint incident"
    (incident / "incident.json").write_bytes(canonical_json_bytes(publish_document) + b"\n")

    with pytest.raises(b1.B1OrchestrationError, match="source/config/laws"):
        b1.validate_resume_incident(
            incident, expected_commit="a" * 40, expected_source_sha256="b" * 64,
            expected_laws_sha256="d" * 64, expected_b0_evidence=_b0_evidence(),
        )

    incident_manifest = incident / "incident.json"
    tampered = json.loads(incident_manifest.read_text(encoding="ascii"))
    tampered["attempt_ledger"]["sha256"] = "e" * 64
    incident_manifest.write_text(
        json.dumps(tampered, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="ascii",
    )
    with pytest.raises(b1.B1OrchestrationError):
        b1.validate_resume_incident(
            incident, expected_commit="a" * 40, expected_source_sha256="b" * 64,
            expected_laws_sha256="c" * 64, expected_b0_evidence=_b0_evidence(),
        )


def test_resume_loop_reuses_complete_continues_incomplete_and_runs_pending(
    monkeypatch, tmp_path
) -> None:
    binding = B1LedgerBinding(
        attempt_id="resume-attempt", run_name="CBSC-OMRC-B1-THREE-SEED-SCOUT",
        implementation_commit="a" * 40, source_conformance_sha256="b" * 64,
        configuration_sha256="c" * 64, laws_sha256="d" * 64,
        b0_manifest_sha256=b1.B0_REVIEWED_AUTHORITY["manifest_sha256"],
        b0_manifest_bytes=b1.B0_REVIEWED_AUTHORITY["manifest_bytes"],
        b0_reviewed_receipt_sha256=b1.B0_REVIEWED_RECEIPT_SHA256,
        b0_inventory_sha256=b1.B0_REVIEWED_AUTHORITY["inventory_sha256"],
        b0_file_count=b1.B0_REVIEWED_AUTHORITY["file_count"],
        b0_total_bytes=b1.B0_REVIEWED_AUTHORITY["total_bytes"],
        **_scientific_identity(),
    )
    slots = []
    for index, (seed, arm) in enumerate(B1_SLOT_ORDER):
        if index == 0:
            slots.append(B1SlotLedgerEntry(
                binding=binding, slot_index=index, seed=seed, arm=arm,
                status=B1SlotStatus.COMPLETE,
                raw_result_sha256="1" * 64, admission_sha256="2" * 64,
                telemetry_sha256="3" * 64, files_sha256="4" * 64,
            ))
        elif index == 1:
            resume = B1ResumeCheckpointBinding(
                binding=binding, slot_index=index, seed=seed, arm=arm,
                completed_rollout_updates=12,
                checkpoint_relative_path="arm-seeds/01/checkpoint-update-12.pt",
                checkpoint_sha256="5" * 64, order_chain_sha256="6" * 64,
            )
            slots.append(B1SlotLedgerEntry(
                binding=binding, slot_index=index, seed=seed, arm=arm,
                status=B1SlotStatus.INCOMPLETE, incident_sha256="7" * 64,
                resume_checkpoint=resume,
            ))
        else:
            slots.append(B1SlotLedgerEntry(
                binding=binding, slot_index=index, seed=seed, arm=arm,
                status=B1SlotStatus.PENDING,
            ))
    ledger = B1AttemptLedger(
        schema=B1_LEDGER_SCHEMA, publication_mode=B1_LEDGER_PUBLICATION_MODE,
        binding=binding, slots=tuple(slots),
    )
    original_incident = tmp_path / "original-incident"
    original_incident.mkdir()
    marker = original_incident / "immutable.txt"
    marker.write_bytes(b"unchanged")
    staging = tmp_path / "new.partial-test"
    final = tmp_path / "new-final"
    calls = []

    def fake_complete(**kwargs):
        slot = kwargs["slot"]
        calls.append(("copy", slot.slot_index, -1, None))
        digest = str(slot.slot_index) * 64
        return ([{"seed": slot.seed, "arm": slot.arm}], {"arm": slot.arm},
                {"arm": slot.arm}, {key: digest for key in (
                    "raw_result_sha256", "admission_sha256",
                    "telemetry_sha256", "files_sha256"
                )})

    def fake_load(root, index, seed, arm, **kwargs):
        digest = str(index % 10) * 64
        return ([{"seed": seed, "arm": arm}], {"arm": arm}, {"arm": arm}, {
            "raw_result_sha256": digest, "admission_sha256": digest,
            "telemetry_sha256": digest, "files_sha256": digest,
        })

    monkeypatch.setattr(b1, "create_b1_staging_directory", lambda *a, **k: (staging.mkdir() or staging))
    monkeypatch.setattr(b1, "_law_digests", lambda receipt: {
        "environment": "1" * 64, "adapter": "2" * 64,
        "token": "3" * 64, "analysis": "4" * 64,
    })
    monkeypatch.setattr(b1, "_copy_complete_slot", fake_complete)
    monkeypatch.setattr(b1, "_copy_incomplete_prefix", lambda **kwargs: (
        calls.append(("prefix", kwargs["slot"].slot_index, 12, "checkpoint"))
        or (12, Path("checkpoint-update-12.pt"))
    ))
    monkeypatch.setattr(b1, "_execute_slot", lambda **kwargs: calls.append((
        "execute", kwargs["index"], kwargs["start_update"], kwargs["resume_checkpoint"]
    )))
    monkeypatch.setattr(b1, "_load_slot_evidence", fake_load)
    monkeypatch.setattr(b1, "_validate_slot_checkpoint_files", lambda *a, **k: None)
    assembled = {}
    monkeypatch.setattr(
        b1, "_assemble_and_publish_complete",
        lambda **kwargs: (assembled.update(kwargs) or final),
    )

    lineage_witness = object()
    result = b1._execute_resume_attempt(
        final_path=final, implementation_commit="a" * 40,
        source_receipt={"source_conformance_sha256": "b" * 64},
        b0_evidence=_b0_evidence(),
        validated_incident={
            "incident_root": str(original_incident), "ledger": ledger,
            "lineage_witness": lineage_witness,
        },
    )
    assert result == final
    assert calls[0][:2] == ("copy", 0)
    assert ("execute", 1, 12, Path("checkpoint-update-12.pt")) in calls
    assert all(("execute", index, 0, None) in calls for index in range(2, 12))
    assert marker.read_bytes() == b"unchanged"
    assert assembled["incident_lineage_witness"] is lineage_witness


def test_all_complete_incident_is_publication_only_with_no_worker_or_admission(
    monkeypatch, tmp_path
) -> None:
    b0_evidence = _b0_evidence()
    binding = B1LedgerBinding(
        attempt_id="complete-attempt", run_name="CBSC-OMRC-B1-THREE-SEED-SCOUT",
        implementation_commit="a" * 40, source_conformance_sha256="b" * 64,
        configuration_sha256="c" * 64, laws_sha256="d" * 64,
        b0_manifest_sha256=b0_evidence["manifest_sha256"],
        b0_manifest_bytes=b0_evidence["manifest_bytes"],
        b0_reviewed_receipt_sha256=b0_evidence["reviewed_receipt_sha256"],
        b0_inventory_sha256=b0_evidence["inventory_sha256"],
        b0_file_count=b0_evidence["file_count"],
        b0_total_bytes=b0_evidence["total_bytes"],
        **_scientific_identity(),
    )
    slots = tuple(B1SlotLedgerEntry(
        binding=binding, slot_index=index, seed=seed, arm=arm,
        status=B1SlotStatus.COMPLETE,
        raw_result_sha256="1" * 64, admission_sha256="2" * 64,
        telemetry_sha256="3" * 64, files_sha256="4" * 64,
    ) for index, (seed, arm) in enumerate(B1_SLOT_ORDER))
    ledger = B1AttemptLedger(
        schema=B1_LEDGER_SCHEMA, publication_mode=B1_LEDGER_PUBLICATION_MODE,
        binding=binding, slots=slots,
    )
    original = tmp_path / "original"
    original.mkdir()
    (original / "immutable.txt").write_bytes(b"unchanged")
    staging = tmp_path / "new.partial"
    final = tmp_path / "new-final"
    copied = []
    assembled = {}

    def fake_copy(**kwargs):
        slot = kwargs["slot"]
        copied.append(slot.slot_index)
        return ([{"seed": slot.seed, "arm": slot.arm}], {}, {}, {
            "raw_result_sha256": "1" * 64, "admission_sha256": "2" * 64,
            "telemetry_sha256": "3" * 64, "files_sha256": "4" * 64,
        })

    monkeypatch.setattr(
        b1, "create_b1_staging_directory", lambda *a, **k: (staging.mkdir() or staging)
    )
    monkeypatch.setattr(b1, "_law_digests", lambda receipt: {})
    monkeypatch.setattr(b1, "_copy_complete_slot", fake_copy)
    monkeypatch.setattr(
        b1, "_execute_slot",
        lambda **kwargs: pytest.fail("publication-only resume invoked a worker/admission"),
    )
    monkeypatch.setattr(
        b1, "_assemble_and_publish_complete",
        lambda **kwargs: (assembled.update(kwargs) or final),
    )
    lineage_witness = object()
    assert b1._execute_resume_attempt(
        final_path=final, implementation_commit="a" * 40,
        source_receipt={"source_conformance_sha256": "b" * 64},
        b0_evidence=b0_evidence,
        validated_incident={
            "incident_root": str(original), "ledger": ledger,
            "lineage_witness": lineage_witness,
            "resume_slot": None, "resume_checkpoint": None,
        },
    ) == final
    assert copied == list(range(12))
    assert assembled["incident_lineage_witness"] is lineage_witness
    assert (original / "immutable.txt").read_bytes() == b"unchanged"


def test_fresh_attempt_publishes_empty_incident_lineage(monkeypatch, tmp_path) -> None:
    staging = tmp_path / "fresh.partial"
    final = tmp_path / "fresh-final"
    assembled = {}
    monkeypatch.setattr(
        b1, "create_b1_staging_directory", lambda *a, **k: (staging.mkdir() or staging)
    )
    monkeypatch.setattr(b1, "_law_digests", lambda receipt: {})
    monkeypatch.setattr(b1, "_execute_slot", lambda **kwargs: None)
    monkeypatch.setattr(b1, "_validate_slot_checkpoint_files", lambda *a, **k: None)

    def fake_load(root, index, seed, arm, **kwargs):
        return ([{"seed": seed, "arm": arm}], {}, {}, {
            "raw_result_sha256": "1" * 64, "admission_sha256": "2" * 64,
            "telemetry_sha256": "3" * 64, "files_sha256": "4" * 64,
        })

    monkeypatch.setattr(b1, "_load_slot_evidence", fake_load)
    monkeypatch.setattr(
        b1, "_assemble_and_publish_complete",
        lambda **kwargs: (assembled.update(kwargs) or final),
    )
    assert b1._execute_fresh_attempt(
        final_path=final, implementation_commit="a" * 40,
        source_receipt={"source_conformance_sha256": "b" * 64},
        b0_evidence=_b0_evidence(),
    ) == final
    witness = assembled["incident_lineage_witness"]
    assert type(witness) is b1_artifact.B1IncidentLineageWitness
    assert b1_artifact.materialize_b1_incident_lineage(
        witness, allowed_root=b1.CONFINED_ROOT
    ) == []


def test_corrupt_resume_checkpoint_downgrades_to_none_and_incident_still_publishes(
    monkeypatch, tmp_path
) -> None:
    staging = tmp_path / "partial"
    seed, arm = B1_SLOT_ORDER[0]
    durable = staging / "arm-seeds" / b1._slot_tag(0, seed, arm)
    durable.mkdir(parents=True)
    (durable / "checkpoint-update-0.pt").write_bytes(b"corrupt")
    captured = {}
    monkeypatch.setattr(
        b1, "load_b1_checkpoint",
        lambda path: (_ for _ in ()).throw(ValueError("corrupt checkpoint")),
    )
    monkeypatch.setattr(
        b1, "publish_b1_incident",
        lambda **kwargs: (captured.update(kwargs) or (tmp_path / "incident")),
    )
    result = b1._publish_attempt_incident(
        staging=staging, final_path=tmp_path / "final", attempt_id="attempt",
        implementation_commit="a" * 40,
        source_receipt={"source_conformance_sha256": "b" * 64}, laws={},
        completed=[], b0_evidence=_b0_evidence(), failed_index=0,
        exc=RuntimeError("test-only failure"),
    )
    assert result == tmp_path / "incident"
    assert captured["attempt_ledger"].slots[0].status is B1SlotStatus.INCOMPLETE
    assert captured["attempt_ledger"].slots[0].resume_checkpoint is None

def test_direct_script_launcher_resolves_repository_imports() -> None:
    script = Path(__file__).resolve().parents[4] / "scripts" / "run_cbsc_omrc_b01_b1.py"
    completed = subprocess.run(
        [sys.executable, str(script), "readiness"], cwd=script.parent.parent,
        capture_output=True, text=True, shell=False, timeout=60,
    )
    assert completed.returncode == 0
    document = json.loads(completed.stdout)
    assert document["engine_bound"] is True
    assert document["start_authorized"] is True


def test_single_readiness_result_never_reports_denied_while_start_is_reachable(
    monkeypatch, tmp_path
) -> None:
    source = {"source_conformance_sha256": "b" * 64}
    b0 = _b0_evidence()
    monkeypatch.setattr(b1, "CONFINED_ROOT", tmp_path.resolve())
    monkeypatch.setattr(b1, "verify_source_conformance", lambda commit: source)
    monkeypatch.setattr(b1, "locate_b0_evidence", lambda root: b0)
    monkeypatch.setattr(b1, "require_parallel_module_protocols", lambda: {})
    called = []
    monkeypatch.setattr(
        b1, "_execute_fresh_attempt",
        lambda **kwargs: (called.append(kwargs) or tmp_path / "published"),
    )

    # Section-11 recast: the value of FORMAL_ANALYSIS_BOUND no longer changes
    # authorization in either direction.  Start is reachable with the flag at
    # its recorded historical value, and the readiness document says so.
    monkeypatch.setattr(b1, "FORMAL_ANALYSIS_BOUND", False)
    document = b1.readiness_document("a" * 40, tmp_path)
    assert document["start_authorized"] is True
    assert document["resume_authorized"] is True
    assert document["readiness_disposition"] == "READY"
    assert document["formal_analysis_record"]["gating"] is False
    assert b1.run_b1_start(
        final_path=tmp_path / "ready", implementation_commit="a" * 40,
        b0_root=tmp_path,
    ) == tmp_path / "published"
    assert len(called) == 1

    monkeypatch.setattr(b1, "FORMAL_ANALYSIS_BOUND", True)
    assert b1.readiness_document("a" * 40, tmp_path)["start_authorized"] is True

    # An explicitly unsatisfied source or B0 binding still blocks.
    monkeypatch.setattr(b1, "verify_source_conformance", _raise_source)
    with pytest.raises(b1.B1OrchestrationError):
        b1.run_b1_start(
            final_path=tmp_path / "blocked", implementation_commit="a" * 40,
            b0_root=tmp_path,
        )
    assert len(called) == 1


def _raise_source(commit: str) -> dict[str, str]:
    raise b1.B1OrchestrationError("BLOCKED_UNCOMMITTED: test-only refusal")


def test_formal_orchestrator_has_no_legacy_analysis_or_caller_manifest_route() -> None:
    source = Path(b1.__file__).read_text(encoding="utf-8")
    assert "collect_complete_b1_checkpoint_records" not in source
    assert "compute_b1_analysis" not in source
    assert "def _production_assembly_seam" not in source
    assert "publish_b1_complete" not in source
    assert not any(path.endswith("/b1_analysis.py") for path in b1.CANONICAL_SOURCE_SURFACE)
    assert not any(path.endswith("/b1_evidence.py") for path in b1.CANONICAL_SOURCE_SURFACE)
    probe = subprocess.run(
        [sys.executable, "-c", (
            "import sys; "
            "import experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1; "
            "assert 'experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_analysis' not in sys.modules"
        )],
        cwd=Path(__file__).resolve().parents[4], capture_output=True, text=True,
        shell=False, timeout=60,
    )
    assert probe.returncode == 0, probe.stderr


def test_policy_replay_batch_invokes_all_slots_in_fixed_order_and_builds_witness(
    monkeypatch, tmp_path
) -> None:
    calls = []
    staging = tmp_path / "attempt"
    staging.mkdir()
    groups = [[{"attempt_id": "attempt"}] for _ in B1_SLOT_ORDER]

    def fake_prepare(**kwargs):
        index = kwargs["index"]
        calls.append(("prepare", index, kwargs["seed"], kwargs["arm"]))
        root = staging / "policy-replay" / f"{index:02d}"
        root.mkdir(parents=True)
        return (["test-child"], root / "result.json", root / "error.json",
                root / "scratch", root / "admission.json")

    def fake_supervise(command, **kwargs):
        index = int(kwargs["result_path"].parent.name)
        calls.append(("supervise", index))
        return ({}, {})

    witness = object()
    monkeypatch.setattr(b1, "_prepare_policy_replay_invocation", fake_prepare)
    monkeypatch.setattr(b1, "supervise_policy_replay_child", fake_supervise)
    monkeypatch.setattr(b1, "_atomic_create_json", lambda *a, **k: None)
    monkeypatch.setattr(
        b1, "make_b1_policy_replay_batch_witness",
        lambda **kwargs: (calls.append(("witness", kwargs["attempt_id"])) or witness),
    )
    assert b1._execute_policy_replay_batch(
        staging=staging, attempt_id="attempt", groups=groups,
        implementation_commit="a" * 40,
        source_conformance_sha256="b" * 64,
    ) is witness
    assert [item[1] for item in calls if item[0] == "prepare"] == list(range(12))
    assert [item[1] for item in calls if item[0] == "supervise"] == list(range(12))
    assert calls[-1] == ("witness", "attempt")


def test_policy_replay_supervisor_uses_result_rows_as_work_units(tmp_path) -> None:
    result = tmp_path / "result.json"
    counts = {
        "policy_decisions": 192, "policy_curves": 2,
        "execution_mode_records": 4, "evaluation_join_records": 4,
    }
    wrapper = {
        "counts": counts,
        "policy_decisions": [{} for _ in range(192)],
        "policy_curves": [{}, {}],
        "execution_mode_records": [{} for _ in range(4)],
        "evaluation_join_records": [{} for _ in range(4)],
        "scientific_branch": None, "scientific_polarity": None,
        "promotion_eligible": None, "b2_extension_trigger": None,
    }
    code = (
        "import json,pathlib,time\n"
        "time.sleep(0.1)\n"
        f"p=pathlib.Path({str(result)!r})\n"
        f"v={wrapper!r}\n"
        "p.write_bytes((json.dumps(v,ensure_ascii=True,allow_nan=False,sort_keys=True,separators=(',',':'))+'\\n').encode('ascii'))\n"
    )
    observed, measurement = b1.supervise_policy_replay_child(
        [sys.executable, "-c", code], result_path=result,
        scratch_root=tmp_path / "scratch", durable_root=tmp_path,
        stdout_path=tmp_path / "stdout.log", stderr_path=tmp_path / "stderr.log",
        test_only=True, interval_seconds=0.01,
    )
    assert observed["counts"] == counts
    assert measurement["scientific_work_transitions"] == 192
    assert measurement["stage_measurements"][0]["stage"] == (
        "policy-replay-model-forward-units"
    )


def test_policy_replay_supervisor_cap_kills_and_preserves_incident(tmp_path) -> None:
    result = tmp_path / "result.json"
    with pytest.raises(TelemetryError, match="wall_seconds"):
        b1.supervise_policy_replay_child(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            result_path=result, scratch_root=tmp_path / "scratch",
            durable_root=tmp_path, stdout_path=tmp_path / "stdout.log",
            stderr_path=tmp_path / "stderr.log", interval_seconds=0.01,
            caps=ResourceCaps(wall_seconds=0.1), test_only=True,
        )
    incident = json.loads(
        (tmp_path / "supervisor-incident.json").read_text(encoding="utf-8")
    )
    assert incident["reason"] == "LIVE_RESOURCE_CAP_TERMINATION"
    result.write_bytes(b"preexisting")
    with pytest.raises(FileExistsError, match="create-only"):
        b1.supervise_policy_replay_child(
            [sys.executable, "-c", "pass"], result_path=result,
            scratch_root=tmp_path / "scratch2", durable_root=tmp_path,
            stdout_path=tmp_path / "stdout2.log", stderr_path=tmp_path / "stderr2.log",
            test_only=True,
        )
