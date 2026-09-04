import json
from pathlib import Path
import threading

import pytest

from experiments.candidates.ucope.competence_first_scout_r01 import RunBinding, ScoutConfig
from experiments.candidates.ucope.competence_first_scout_r01.artifact import (
    ASSESS_FORMAT as CORE_ASSESS_FORMAT,
    ASSESS_ACTIVITY_FIELDS,
)
from scripts import run_ucope_competence_first_scout_r01 as runner


def _sample(cpu, read, write, other, rss=100, threads=2):
    return runner._ProcessSample((123, 456), rss, cpu, read, write, other, threads)


def _resource_record():
    return {
        "measurement_complete": True,
        "measurement_source": "fixture",
        "sample_interval_seconds": 0.05,
        "sample_count": 3,
        "wall_seconds": 2.0,
        "cpu_seconds": 1.0,
        "cpu_core_equivalents": 0.5,
        "host_cpu_occupancy": 0.01,
        "peak_rss_bytes": 128 * 1024**2,
        "peak_process_count": 1,
        "peak_thread_count": 3,
        "worker_count": 1,
        "accelerator": "NOT_APPLICABLE_CPU_ONLY",
        "peak_accelerator_memory_bytes": 0,
        "io_read_bytes": 10,
        "io_write_bytes": 20,
        "io_other_bytes": 30,
        "aggregate_io_bytes": 60,
        "scratch_peak_bytes": 1024,
        "durable_peak_bytes": 2048,
    }


def _core_assessment():
    activity = {field: 0 for field in ASSESS_ACTIVITY_FIELDS}
    activity["parameter_count"] = {}
    activity["per_policy"] = {}
    return {
        "format": CORE_ASSESS_FORMAT,
        "schema_version": 1,
        "mode": "A/RECON",
        "config": ScoutConfig.assess().to_dict(),
        "work": {},
        "activity": activity,
        "stage_times": [
            {"stage": "fresh_data", "wall_seconds": 1.0, "cpu_seconds": 0.5},
            {
                "stage": "policy",
                "arm_id": "MT-XF-FLEX",
                "seed_id": ScoutConfig.assess().seed_ids[0],
                "fold_id": 0,
                "wall_seconds": 2.0,
                "cpu_seconds": 1.0,
                "root_updates": 16,
                "tail_updates": 8,
            },
        ],
        "source_refs": [],
        "runtime_refs": {"torch_intraop_threads": 8, "torch_interop_threads": 8},
        "run_binding": RunBinding.assess(
            runner._source_fence()["aggregate_sha256"]
        ).to_dict(),
    }


def test_process_tree_monitor_uses_deltas_and_filesystem_high_water(tmp_path, monkeypatch):
    samples = iter(
        [
            (_sample(10.0, 100, 200, 300),),
            (_sample(11.5, 110, 220, 330, rss=200, threads=3),),
            (_sample(12.0, 115, 225, 335, rss=150, threads=2),),
        ]
    )
    monkeypatch.setattr(runner, "_windows_process_tree", lambda: next(samples))
    monkeypatch.setattr(runner.os, "name", "nt")
    scratch, durable = tmp_path / "scratch", tmp_path / "durable"
    scratch.mkdir(); durable.mkdir()
    monitor = runner.ProcessTreeMonitor(scratch, durable)
    monitor._observe()
    (scratch / "work.bin").write_bytes(b"x" * 17)
    (durable / "receipt.bin").write_bytes(b"y" * 19)
    monitor._observe()
    result = monitor.finish()
    assert result["measurement_complete"] is True
    assert result["sample_count"] == 3
    assert result["peak_rss_bytes"] == 200
    assert result["peak_thread_count"] == 3
    assert result["cpu_seconds"] == pytest.approx(2.0)
    assert result["io_read_bytes"] == 15
    assert result["io_write_bytes"] == 25
    assert result["io_other_bytes"] == 35
    assert result["aggregate_io_bytes"] == 75
    assert result["scratch_peak_bytes"] == 17
    assert result["durable_peak_bytes"] == 19


def test_durable_rename_is_serialized_with_directory_walk_and_preserves_high_water(
    tmp_path, monkeypatch,
):
    monkeypatch.setattr(
        runner, "_windows_process_tree", lambda: (_sample(1.0, 1, 2, 3),),
    )
    monkeypatch.setattr(runner.os, "name", "nt")
    scratch, source, destination = (
        tmp_path / "scratch", tmp_path / ".complete-staging-a1",
        tmp_path / ".complete-postvalidated-a1",
    )
    scratch.mkdir(); source.mkdir()
    (scratch / "work.bin").write_bytes(b"x" * 17)
    (source / "checkpoints").mkdir()
    (source / "checkpoints" / "state.bin").write_bytes(b"y" * 19)
    real_directory_size = runner._directory_size
    walk_entered = threading.Event()
    release_walk = threading.Event()

    def blocking_directory_size(root, *, require_exists=False):
        if Path(root) == source and threading.current_thread().name == "walker":
            walk_entered.set()
            assert release_walk.wait(timeout=5)
        return real_directory_size(Path(root), require_exists=require_exists)

    monkeypatch.setattr(runner, "_directory_size", blocking_directory_size)
    monitor = runner.ProcessTreeMonitor(scratch, source, sample_seconds=100)
    errors = []
    walker = threading.Thread(
        target=lambda: _capture_thread_error(errors, monitor._observe), name="walker",
    )
    mover_started = threading.Event()

    def move():
        mover_started.set()
        _capture_thread_error(
            errors, lambda: monitor.rename_durable_root(source, destination),
        )

    mover = threading.Thread(target=move, name="mover")
    walker.start()
    assert walk_entered.wait(timeout=5)
    mover.start()
    assert mover_started.wait(timeout=5)
    assert source.is_dir() and not destination.exists()
    release_walk.set()
    walker.join(timeout=5); mover.join(timeout=5)
    assert not walker.is_alive() and not mover.is_alive() and not errors
    assert not source.exists() and destination.is_dir()
    assert monitor.durable_root == destination
    assert monitor.durable_peak_bytes >= 19
    assert monitor.finish()["durable_peak_bytes"] >= 19


def _capture_thread_error(errors, callback):
    try:
        callback()
    except BaseException as exc:  # surfaced in the main test thread
        errors.append(exc)


def test_monitor_refuses_a_missing_bound_root_instead_of_recording_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner, "_windows_process_tree", lambda: (_sample(1.0, 1, 2, 3),),
    )
    monkeypatch.setattr(runner.os, "name", "nt")
    scratch, durable = tmp_path / "scratch", tmp_path / "durable"
    scratch.mkdir(); durable.mkdir()
    monitor = runner.ProcessTreeMonitor(scratch, durable)
    durable.rmdir()
    with pytest.raises(runner.RunnerRefusal, match="resource root disappeared"):
        monitor._observe()
    assert monitor.durable_peak_bytes == 0


def test_central_memory_admission_requires_both_exact_four_gib_floors(tmp_path, monkeypatch):
    receipt = tmp_path / "admit.json"

    def fake_run(command, **kwargs):
        assert command[1:3] == [str(runner.RESOURCE_PREFLIGHT), "admit-memory"]
        payload = {
            "passed": True,
            "physical_floor_pass": True,
            "effective_floor_pass": True,
            "available_physical_bytes": 5 * 1024**3,
            "effective_available_bytes": 4 * 1024**3,
        }
        Path(command[-1]).write_text(json.dumps(payload), encoding="utf-8")
        return type("Completed", (), {"returncode": 0, "stderr": ""})()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    assert runner._run_memory_admission(receipt)["passed"] is True
    value = json.loads(receipt.read_text(encoding="utf-8"))
    value["effective_available_bytes"] = 4 * 1024**3 - 1
    receipt.unlink()

    def low_run(command, **kwargs):
        Path(command[-1]).write_text(json.dumps(value), encoding="utf-8")
        return type("Completed", (), {"returncode": 0, "stderr": ""})()

    monkeypatch.setattr(runner.subprocess, "run", low_run)
    with pytest.raises(runner.RunnerRefusal, match="both 4 GiB"):
        runner._run_memory_admission(receipt)


def test_assessment_is_source_runtime_bound_and_has_no_science_surface():
    core = _core_assessment()
    resources = _resource_record()
    admission = {"passed": True}
    value = runner._assessment_document(core, admission, resources)
    assert runner.validate_assessment(value) == value
    assert value["claim_ceiling"] == "RESOURCE_AND_ENGINEERING_FACTS_ONLY_NO_ALGORITHM_EFFECT"
    assert value["projection"]["data_scale"] == 48
    assert value["projection"]["policy_work_scale"] == 60
    assert value["projection"]["storage_scale"] == 96
    assert set(value["projection"]["resource_cap"]) == {
        "wall_seconds", "peak_rss_bytes", "scratch_bytes", "durable_bytes", "workers",
        "processes", "threads", "torch_intraop_threads", "torch_interop_threads",
    }
    assert value["projection"]["resource_cap"]["processes"] == 1
    assert value["projection"]["resource_cap"]["threads"] >= resources["peak_thread_count"]
    tampered = json.loads(json.dumps(value))
    tampered["core_assessment"]["activity"]["competence_pass"] = True
    with pytest.raises((ValueError, runner.RunnerRefusal)):
        runner.validate_assessment(tampered)


def test_rss_projection_covers_quarantined_full_load_resource_envelope():
    resources = _resource_record()
    resources["peak_thread_count"] = 29
    projection = runner._projection(_core_assessment(), resources)
    calibration = projection["resource_only_b1_rss_calibration"]
    observed = 455_176_192
    required_guard = (observed * 5 + 3) // 4
    assert calibration == {
        "attempt_id": "ucope-scout-r01-b1-20260901-01",
        "complete": False,
        "scientific_object_consumed": False,
        "observed_peak_rss_bytes": observed,
        "headroom_numerator": 5,
        "headroom_denominator": 4,
        "guarded_peak_rss_bytes": required_guard,
    }
    assert projection["guarded_projected_peak_rss_bytes"] >= required_guard
    assert projection["resource_cap"]["peak_rss_bytes"] == 576 * 1024**2
    assert projection["resource_cap"]["peak_rss_bytes"] > observed
    runner._validate_resource_cap(
        {
            "wall_seconds": 122.8474525000056,
            "peak_rss_bytes": observed,
            "scratch_peak_bytes": 10_630_135,
            "durable_peak_bytes": 10_629_120,
            "worker_count": 1,
            "peak_process_count": 1,
            "peak_thread_count": 29,
        },
        projection["resource_cap"],
    )


def test_result_commands_call_central_preflight_and_keep_namespaces_separate():
    source = runner.RUNNER_PATH.read_text(encoding="utf-8")
    body = source[source.index("def run_b1(") : source.index("def _parser(")]
    assert body.index("_run_memory_admission") < body.index("work.mkdir")
    assert 'output / "work"' in body
    assert 'output / "complete"' in body
    assert 'control / "failure-receipts"' in body
    assert 'control / "admissions"' in body
    assert '.complete-staging-' in body
    assert '.complete-postvalidated-' in body
    assert '.publication-scratch-' in body
    assert "publication_monitor.rename_durable_root(staging, postvalidated)" in body
    assert "os.replace(postvalidated, complete)" in body
    assert "os.replace(staging, complete)" not in body
    assert "run_workload(" in body and "config = ScoutConfig.b1()" in body
    assert "run_binding=run_binding" in body
    assert "validate_b1_preterminal_tree(staging" in body
    assert "validate_b1_preterminal_tree(postvalidated" in body
    assert body.index("publication_monitor = ProcessTreeMonitor") < body.index('atomic_create_json(staging / "resource-ledger.json"')
    assert "ProcessTreeMonitor(publication_scratch, staging)" in body
    assert "ProcessTreeMonitor(work, output)" not in body
    assert body.index("validate_b1_preterminal_tree(staging") < body.index("publication_monitor.rename_durable_root(staging, postvalidated)")
    assert body.index("publication_monitor.rename_durable_root(staging, postvalidated)") < body.index("validate_b1_preterminal_tree(postvalidated")
    assert body.index("validate_b1_preterminal_tree(postvalidated") < body.index("publication_monitor.finish")
    assert body.index("publication_monitor.finish") < body.index('kind="PUBLICATION_TERMINAL"')
    assert body.index("atomic_create_json(terminal_path") < body.index('kind="PUBLICATION_TERMINAL"')
    assert body.index('kind="PUBLICATION_TERMINAL"') < body.index("os.replace(postvalidated, complete)")
    assert body.index("_recover_pending_publication(") < body.index("_run_memory_admission")


def _b1_binding():
    return RunBinding.b1(manifest_digest="1" * 64, source_aggregate="2" * 64, assessment_digest="3" * 64)


def _admission_record():
    return {
        "passed": True,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 5 * 1024**3,
        "effective_available_bytes": 5 * 1024**3,
    }


def _checkpoint_snapshot(sequence=1):
    return {
        "sample_count": sequence,
        "wall_seconds": float(sequence),
        "cpu_seconds": float(sequence),
        "peak_rss_bytes": 100,
        "peak_process_count": 1,
        "peak_thread_count": 2,
        "scratch_peak_bytes": 10,
        "durable_peak_bytes": 20,
        "io_read_bytes": sequence,
        "io_write_bytes": sequence,
        "io_other_bytes": sequence,
        "aggregate_io_bytes": 3 * sequence,
    }


def _manifest(tmp_path):
    binding = _b1_binding()
    control = ".ucope-scout-r01-control-0123456789abcdef"
    return {
        "format": runner.B1_MANIFEST_FORMAT,
        "schema_version": 1,
        "object_id": runner.OBJECT_ID,
        "config": ScoutConfig.b1().to_dict(),
        "source_fence": {},
        "runtime_fence": {},
        "assessment_path": str(tmp_path / "assessment.json"),
        "assessment_sha256": "3" * 64,
        "resource_cap": {
            "wall_seconds": 10000, "peak_rss_bytes": 10**10, "scratch_bytes": 10**10,
            "durable_bytes": 10**10, "workers": 2, "processes": 2, "threads": 128,
            "torch_intraop_threads": 1, "torch_interop_threads": 1,
        },
        "publication": {
            "control_namespace": control,
            "complete_namespace": "complete",
            "complete_result": "complete/result.json",
            "terminal_receipt": "complete/terminal-receipt.json",
            "resource_ledger": "complete/resource-ledger.json",
        },
        "run_binding": binding.to_dict(),
    }


def test_admission_failure_writes_control_receipt_without_scientific_output(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    manifest = _manifest(tmp_path)
    monkeypatch.setattr(runner, "_validate_b1_manifest", lambda value, path: manifest)
    monkeypatch.setattr(runner, "_run_memory_admission", lambda path: (_ for _ in ()).throw(runner.RunnerRefusal("low memory")))
    output = tmp_path / "scientific-output"
    with pytest.raises(runner.RunnerRefusal, match="low memory"):
        runner.run_b1(manifest_path, output, resume=False)
    assert not output.exists()
    control = tmp_path / manifest["publication"]["control_namespace"]
    receipts = list((control / "failure-receipts").glob("*.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
    runner.validate_failure_receipt(receipt, config=ScoutConfig.b1(), run_binding=_b1_binding())
    assert receipt["phase"] == "CENTRAL_MEMORY_ADMISSION"
    assert receipt["admission"] is None and receipt["resources"] is None
    assert receipt["run_binding"] == manifest["run_binding"]
    entries = runner._load_resource_journal(control, config=ScoutConfig.b1(), run_binding=_b1_binding())
    assert [row["kind"] for row in entries] == ["ADMISSION", "CORE_TERMINAL"]
    assert entries[0]["payload"]["passed"] is False


def test_existing_complete_refuses_before_admission_or_journal_mutation(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    manifest = _manifest(tmp_path)
    monkeypatch.setattr(runner, "_validate_b1_manifest", lambda value, path: manifest)
    monkeypatch.setattr(
        runner, "_run_memory_admission",
        lambda path: (_ for _ in ()).throw(AssertionError("admission must not run for an immutable complete tree")),
    )
    output = tmp_path / "scientific-output"
    (output / "complete").mkdir(parents=True)
    with pytest.raises(runner.RunnerRefusal, match="already exists"):
        runner.run_b1(manifest_path, output, resume=True)
    control = tmp_path / manifest["publication"]["control_namespace"]
    assert not (control / "resource-journal").exists()


def test_resource_journal_merges_resume_attempts_and_exact_checkpoint_sequence(tmp_path):
    control = tmp_path / "control"
    config = ScoutConfig.b1()
    binding = _b1_binding()
    expected = runner._expected_checkpoint_sequence(config)
    resources = _resource_record()
    for attempt, identities, status in (("a1", expected[:20], "FAILED"), ("a2", expected[20:], "COMPLETE")):
        runner._append_resource_journal(
            control, config=config, run_binding=binding, attempt_id=attempt, kind="ADMISSION",
            payload={"passed": True, "receipt": _admission_record(), "error": None},
        )
        for number, identity in enumerate(identities, 1):
            runner._append_resource_journal(
                control, config=config, run_binding=binding, attempt_id=attempt, kind="CHECKPOINT",
                payload={"identity": identity, "resources": _checkpoint_snapshot(number)},
            )
        runner._append_resource_journal(
            control, config=config, run_binding=binding, attempt_id=attempt, kind="CORE_TERMINAL",
            payload={"status": status, "phase": "TEST", "resources": resources, "stage_events": [], "error": None if status == "COMPLETE" else "interrupted"},
        )
        if status == "COMPLETE":
            runner._append_resource_journal(
                control, config=config, run_binding=binding, attempt_id=attempt, kind="PUBLICATION_TERMINAL",
                payload={"status": "COMPLETE", "phase": "TEST", "resources": resources, "error": None},
            )
    entries = runner._load_resource_journal(control, config=config, run_binding=binding)
    inventory = [{"locator": f"checkpoints/{index}.pt"} for index in range(72)]
    ledger = runner._resource_ledger(config=config, run_binding=binding, cap=_manifest(tmp_path)["resource_cap"], entries=entries, checkpoint_inventory=inventory)
    assert len(ledger["admissions"]) == 2 and len(ledger["attempts"]) == 2
    assert ledger["checkpoint_sequence"] == expected
    assert ledger["aggregate_resources"]["attempt_count"] == 2
    assert ledger["journal_aggregate_sha256"] == runner._journal_aggregate(entries)


def test_internal_checkpoint_callback_is_projected_before_terminal_journal(tmp_path):
    control = tmp_path / "control"
    config = ScoutConfig.b1()
    binding = _b1_binding()
    runner._append_resource_journal(
        control, config=config, run_binding=binding, attempt_id="a1", kind="ADMISSION",
        payload={"passed": True, "receipt": _admission_record(), "error": None},
    )
    internal = {
        "stage": "checkpoint", "arm_id": config.arms[0], "seed_id": config.seed_ids[0],
        "fold_id": 0, "root_update": config.evaluation_root_updates[0],
        "activity": {"regret": 123, "sampled_evaluation_transitions": 456},
    }
    projected = runner._outcome_free_stage_event(internal)
    assert projected == {
        "stage": "checkpoint", "arm_id": config.arms[0], "seed_id": config.seed_ids[0],
        "fold_id": 0, "root_update": config.evaluation_root_updates[0],
    }
    runner._append_resource_journal(
        control, config=config, run_binding=binding, attempt_id="a1", kind="CORE_TERMINAL",
        payload={
            "status": "FAILED", "phase": "TEST", "resources": _resource_record(),
            "stage_events": [projected], "error": "test interruption",
        },
    )
    entries = runner._load_resource_journal(control, config=config, run_binding=binding)
    assert entries[-1]["payload"]["stage_events"] == [projected]


def test_orphaned_or_unobserved_admitted_attempt_permanently_refuses_resume(tmp_path):
    control = tmp_path / "control"
    config = ScoutConfig.b1()
    binding = _b1_binding()
    runner._append_resource_journal(
        control, config=config, run_binding=binding, attempt_id="a1", kind="ADMISSION",
        payload={"passed": True, "receipt": _admission_record(), "error": None},
    )
    live = runner._load_resource_journal(
        control, config=config, run_binding=binding, live_attempt_id="*",
    )
    with pytest.raises(runner.RunnerRefusal, match="cannot resume"):
        runner._validate_resumable_prior_journal(live)

    runner._append_resource_journal(
        control, config=config, run_binding=binding, attempt_id="a1", kind="CORE_TERMINAL",
        payload={
            "status": "FAILED", "phase": "MONITOR_START", "resources": None,
            "stage_events": [], "error": "telemetry unavailable",
        },
    )
    terminalized = runner._load_resource_journal(control, config=config, run_binding=binding)
    with pytest.raises(runner.RunnerRefusal, match="cannot resume"):
        runner._validate_resumable_prior_journal(terminalized)
    complete_but_unobserved = _complete_entries(config, binding)
    with pytest.raises(runner.RunnerRefusal, match="publication terminal telemetry"):
        runner._validate_resumable_prior_journal(complete_but_unobserved)
    complete_but_unobserved[-1]["payload"]["resources"] = None
    with pytest.raises(runner.RunnerRefusal, match="terminal resource telemetry"):
        runner._journal_summary(complete_but_unobserved, config)


def test_monitor_snapshot_and_finish_are_locked_idempotent(tmp_path, monkeypatch):
    samples = iter([
        (_sample(1.0, 1, 2, 3),),
        (_sample(2.0, 2, 4, 6, rss=200),),
        (_sample(3.0, 3, 6, 9, rss=150),),
    ])
    monkeypatch.setattr(runner, "_windows_process_tree", lambda: next(samples))
    monkeypatch.setattr(runner.os, "name", "nt")
    scratch, durable = tmp_path / "scratch", tmp_path / "durable"
    scratch.mkdir(); durable.mkdir()
    monitor = runner.ProcessTreeMonitor(scratch, durable, sample_seconds=100).start()
    snapshot = monitor.snapshot()
    assert snapshot["sample_count"] == 2 and snapshot["cpu_seconds"] == pytest.approx(1.0)
    final = monitor.finish()
    assert final["sample_count"] == 3 and final["peak_rss_bytes"] == 200
    assert monitor.finish() == final and monitor.snapshot() == final


def _complete_entries(config, binding):
    entries = [{
        "format": runner.RESOURCE_JOURNAL_FORMAT, "schema_version": 1, "sequence": 0,
        "kind": "ADMISSION", "attempt_id": "a1", "config": config.to_dict(),
        "run_binding": binding.to_dict(),
        "payload": {"passed": True, "receipt": _admission_record(), "error": None},
    }]
    for number, identity in enumerate(runner._expected_checkpoint_sequence(config), 1):
        entries.append({
            "format": runner.RESOURCE_JOURNAL_FORMAT, "schema_version": 1, "sequence": len(entries),
            "kind": "CHECKPOINT", "attempt_id": "a1", "config": config.to_dict(),
            "run_binding": binding.to_dict(), "payload": {"identity": identity, "resources": _checkpoint_snapshot(number)},
        })
    entries.append({
        "format": runner.RESOURCE_JOURNAL_FORMAT, "schema_version": 1, "sequence": len(entries),
        "kind": "CORE_TERMINAL", "attempt_id": "a1", "config": config.to_dict(),
        "run_binding": binding.to_dict(),
        "payload": {"status": "COMPLETE", "phase": "TEST", "resources": _resource_record(), "stage_events": [], "error": None},
    })
    return entries


def _publication_entry(entries, config, binding, *, attempt_id="a1", status="COMPLETE", resources=None):
    return {
        "format": runner.RESOURCE_JOURNAL_FORMAT,
        "schema_version": 1,
        "sequence": len(entries),
        "kind": "PUBLICATION_TERMINAL",
        "attempt_id": attempt_id,
        "config": config.to_dict(),
        "run_binding": binding.to_dict(),
        "payload": {
            "status": status,
            "phase": "TEST_PUBLICATION",
            "resources": _resource_record() if resources is None else resources,
            "error": None if status == "COMPLETE" else "publication interrupted",
        },
    }


def _append_fixture_row(entries, config, binding, *, attempt_id, kind, payload):
    entries.append({
        "format": runner.RESOURCE_JOURNAL_FORMAT,
        "schema_version": 1,
        "sequence": len(entries),
        "kind": kind,
        "attempt_id": attempt_id,
        "config": config.to_dict(),
        "run_binding": binding.to_dict(),
        "payload": payload,
    })


def test_publication_failure_resources_survive_resume_and_enter_terminal_aggregate(tmp_path):
    config, binding = ScoutConfig.b1(), _b1_binding()
    entries = _complete_entries(config, binding)
    failed_publication = _resource_record()
    failed_publication["wall_seconds"] = 3.0
    _append_fixture_row(
        entries, config, binding, attempt_id="a1", kind="PUBLICATION_TERMINAL",
        payload={
            "status": "FAILED", "phase": "TEST_PUBLICATION", "resources": failed_publication,
            "error": "publication interrupted",
        },
    )
    runner._validate_resumable_prior_journal(entries)
    _append_fixture_row(
        entries, config, binding, attempt_id="a2", kind="ADMISSION",
        payload={"passed": True, "receipt": _admission_record(), "error": None},
    )
    _append_fixture_row(
        entries, config, binding, attempt_id="a2", kind="CORE_TERMINAL",
        payload={
            "status": "COMPLETE", "phase": "TEST_CORE", "resources": _resource_record(),
            "stage_events": [], "error": None,
        },
    )
    inventory = [{"locator": f"checkpoints/{index}.pt"} for index in range(72)]
    cap = _manifest(tmp_path)["resource_cap"]
    ledger = runner._resource_ledger(
        config=config, run_binding=binding, cap=cap, entries=entries,
        checkpoint_inventory=inventory,
    )
    succeeding_publication = _resource_record()
    succeeding_publication["wall_seconds"] = 5.0
    current_publication = _publication_entry(
        entries, config, binding, attempt_id="a2", resources=succeeding_publication,
    )
    preterminal = {
        "config": config.to_dict(), "run_binding": binding.to_dict(), "resource_ledger": ledger,
        "result_record": {"locator": "result.json", "size_bytes": 1, "sha256": "1" * 64},
        "resource_ledger_record": {"locator": "resource-ledger.json", "size_bytes": 1, "sha256": "2" * 64},
        "checkpoint_count": 72, "checkpoint_inventory_aggregate_sha256": "3" * 64,
        "journal_aggregate_sha256": ledger["journal_aggregate_sha256"],
        "manifest_record": {"name": "manifest.json", "size_bytes": 1, "sha256": "4" * 64},
    }
    terminal, _ = runner._terminal_receipt_from_preterminal(
        preterminal=preterminal, publication_terminal_entry=current_publication, cap=cap,
    )
    assert terminal["publication_resources"]["publication_attempt_count"] == 2
    assert terminal["publication_resources"]["wall_seconds"] == pytest.approx(8.0)
    assert terminal["combined_resources"]["publication_attempt_count"] == 2
    assert terminal["full_journal_aggregate_sha256"] == runner._journal_aggregate(
        [*entries, current_publication]
    )


@pytest.mark.parametrize("terminal_written", [False, True])
def test_prepublication_or_terminal_before_journal_residue_is_permanently_refused(
    tmp_path, terminal_written,
):
    config, binding = ScoutConfig.b1(), _b1_binding()
    entries = _complete_entries(config, binding)
    output = tmp_path / "output"
    hidden = output / ".complete-postvalidated-a1"
    hidden.mkdir(parents=True)
    if terminal_written:
        (hidden / "terminal-receipt.json").write_text("prospective", encoding="utf-8")
    with pytest.raises(runner.RunnerRefusal, match="quarantined"):
        runner._recover_pending_publication(
            output=output, complete=output / "complete",
            manifest_path=tmp_path / "manifest.json", entries=entries,
        )
    assert hidden.exists() and not (output / "complete").exists()


def test_publication_journal_after_terminal_permanently_refuses_hidden_tree(
    tmp_path, monkeypatch,
):
    config, binding = ScoutConfig.b1(), _b1_binding()
    entries = _complete_entries(config, binding)
    publication_entry = _publication_entry(entries, config, binding)
    entries.append(publication_entry)
    output = tmp_path / "output"
    hidden = output / ".complete-postvalidated-a1"
    hidden.mkdir(parents=True)
    (hidden / "result.json").write_text("same-bytes", encoding="utf-8")
    monkeypatch.setattr(
        runner, "validate_b1_complete_tree",
        lambda *args, **kwargs: pytest.fail("cross-invocation recovery must not validate or promote"),
    )
    with pytest.raises(runner.RunnerRefusal, match="cannot resume"):
        runner._recover_pending_publication(
            output=output, complete=output / "complete",
            manifest_path=tmp_path / "manifest.json", entries=entries,
        )
    assert hidden.is_dir()
    assert not (output / "complete").exists()


def test_publication_recovery_refuses_any_extra_unbound_residue(tmp_path, monkeypatch):
    config, binding = ScoutConfig.b1(), _b1_binding()
    entries = _complete_entries(config, binding)
    publication_entry = _publication_entry(entries, config, binding)
    entries.append(publication_entry)
    output = tmp_path / "output"
    hidden = output / ".complete-postvalidated-a1"
    hidden.mkdir(parents=True)
    (output / ".publication-scratch-a1").mkdir()
    monkeypatch.setattr(
        runner, "validate_b1_complete_tree",
        lambda *args, **kwargs: pytest.fail("ambiguous residue must be refused before validation"),
    )
    with pytest.raises(runner.RunnerRefusal, match="cannot resume"):
        runner._recover_pending_publication(
            output=output, complete=output / "complete",
            manifest_path=tmp_path / "manifest.json", entries=entries,
        )
    assert hidden.exists() and not (output / "complete").exists()


def test_complete_tree_refuses_terminal_and_ledger_tamper(tmp_path, monkeypatch):
    root = tmp_path / "complete"
    root.mkdir()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    manifest = _manifest(tmp_path)
    config, binding = ScoutConfig.b1(), _b1_binding()
    inventory = []
    for index, identity in enumerate(runner._expected_checkpoint_sequence(config)):
        locator = f"checkpoints/cp-{index:02d}.pt"
        path = root / locator
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"checkpoint")
        inventory.append({**identity, "locator": locator, "size_bytes": path.stat().st_size, "sha256": runner._sha256_file(path), "format": "fixture"})
    entries = _complete_entries(config, binding)
    ledger = runner._resource_ledger(config=config, run_binding=binding, cap=manifest["resource_cap"], entries=entries, checkpoint_inventory=inventory)
    runner.atomic_create_json(root / "resource-ledger.json", ledger)
    result = {
        "runtime_refs": {"resource": {
            "resource_ledger": runner._file_record(root / "resource-ledger.json", root),
            "terminal_receipt_locator": "terminal-receipt.json",
            "journal_aggregate_sha256": ledger["journal_aggregate_sha256"],
            "manifest_sha256": runner._sha256_file(manifest_path),
        }},
        "checkpoints": inventory,
    }
    runner.atomic_create_json(root / "result.json", result)
    monkeypatch.setattr(runner, "_validate_b1_manifest", lambda value, path: manifest)
    monkeypatch.setattr(runner, "validate_complete_tree", lambda *args, **kwargs: None)
    preterminal = runner.validate_b1_preterminal_tree(root, manifest_path)
    publication_entry = _publication_entry(entries, config, binding)
    journal_root = tmp_path / manifest["publication"]["control_namespace"] / "resource-journal"
    journal_root.mkdir(parents=True)
    for row in [*entries, publication_entry]:
        runner.atomic_create_json(journal_root / f"entry-{row['sequence']:06d}.json", row)
    terminal, terminal_bytes = runner._terminal_receipt_from_preterminal(
        preterminal=preterminal, publication_terminal_entry=publication_entry,
        cap=manifest["resource_cap"],
    )
    reservation = terminal["terminal_receipt_reservation"]
    assert reservation["size_bytes"] == len(terminal_bytes)
    assert reservation["aggregate_io_bytes"] == 2 * len(terminal_bytes)
    core_resources = ledger["aggregate_resources"]
    combined = terminal["combined_resources"]
    assert combined["wall_seconds"] == pytest.approx(core_resources["wall_seconds"] + _resource_record()["wall_seconds"])
    assert combined["io_write_bytes"] == (
        core_resources["io_write_bytes"] + _resource_record()["io_write_bytes"]
        + len(terminal_bytes) + terminal["post_monitor_journal_reservation"]["io_write_bytes"]
    )
    assert combined["durable_peak_bytes"] == (
        max(core_resources["durable_peak_bytes"], _resource_record()["durable_peak_bytes"])
        + len(terminal_bytes) + terminal["post_monitor_journal_reservation"]["durable_bytes"]
    )
    runner.atomic_create_json(root / "terminal-receipt.json", terminal)
    assert (root / "terminal-receipt.json").read_bytes() == terminal_bytes
    runner.validate_b1_complete_tree(root, manifest_path)

    publication_journal_path = journal_root / f"entry-{publication_entry['sequence']:06d}.json"
    bad_publication_entry = json.loads(json.dumps(publication_entry))
    bad_publication_entry["payload"]["phase"] = "TAMPERED_BUT_SCHEMA_VALID"
    publication_journal_path.write_bytes(runner.canonical_json_bytes(bad_publication_entry))
    with pytest.raises(runner.RunnerRefusal, match="persistent full resource journal"):
        runner.validate_b1_complete_tree(root, manifest_path)
    publication_journal_path.write_bytes(runner.canonical_json_bytes(publication_entry))

    bad_terminal = dict(terminal)
    bad_terminal["result"] = dict(terminal["result"], sha256="0" * 64)
    (root / "terminal-receipt.json").write_bytes(runner.canonical_json_bytes(bad_terminal))
    with pytest.raises(runner.RunnerRefusal, match="terminal receipt"):
        runner.validate_b1_complete_tree(root, manifest_path)
    (root / "terminal-receipt.json").write_bytes(runner.canonical_json_bytes(terminal))

    bad_ledger = dict(ledger, journal_aggregate_sha256="0" * 64)
    (root / "resource-ledger.json").write_bytes(runner.canonical_json_bytes(bad_ledger))
    with pytest.raises(runner.RunnerRefusal):
        runner.validate_b1_complete_tree(root, manifest_path)
