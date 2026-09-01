from __future__ import annotations

import hashlib
import inspect
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

import scripts.run_vnfc_bpcr_b_explore as runner
import experiments.candidates.variable_n_fleet_churn_b_explore.process_telemetry as telemetry_module

from experiments.candidates.variable_n_fleet_churn_b_explore.process_telemetry import (
    ExactStorageContract,
    ProcessSample,
    ProcessTelemetryError,
    ProcessTreeTelemetrySink,
    STAGES,
    TELEMETRY_FIELDS,
    TELEMETRY_SCHEMA,
    sample_windows_process_tree,
)


NOW = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)


def receipt(**updates: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "captured_at": "2026-09-01T11:59:00Z",
        "assessed_at": "2026-09-01T11:59:01Z",
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 6 * 1024**3,
        "effective_available_bytes": 5 * 1024**3,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
    }
    value.update(updates)
    return value


class AdvancingSampler:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(
        self, _tracked: object = None
    ) -> tuple[ProcessSample, ...]:
        self.calls += 1
        n = self.calls
        return (
            ProcessSample(10, 100, 1000 + n, float(n), 10 * n, 20 * n, 3 * n, 2),
            ProcessSample(11, 101, 2000 + n, float(2 * n), 5 * n, 7 * n, n, 3),
        )


class AdvancingClock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        self.value += 0.25
        return self.value


class SingleAdvancingSampler:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, _tracked: object = None) -> tuple[ProcessSample, ...]:
        self.calls += 1
        n = self.calls
        return (ProcessSample(10, 100, 1000 + n, float(n), 10 * n, 20 * n, 3 * n, 2),)


def counters() -> dict[str, object]:
    return {
        "native_integrated_ticks": 400,
        "scientific_work_transitions": 1200,
        "worker_count": 2,
        "threads_per_worker": 1,
        "parameter_count_by_arm": {"MAPR": 11, "DIRECT": 12},
        "forward_calls_by_arm": {"MAPR": 21, "DIRECT": 22},
        "backward_calls_by_arm": {"MAPR": 7, "DIRECT": 8},
        "flop_exposure_by_arm": {"MAPR": 31.0, "DIRECT": 32.0},
    }


def exact_counters() -> dict[str, object]:
    value = counters()
    value["worker_count"] = 1
    value["threads_per_worker"] = 1
    return value


def ledger() -> dict[str, object]:
    return {
        "primary_host_calls": 20,
        "shadow_host_calls": 20,
    }


def exact_contract(native_path: Path) -> ExactStorageContract:
    return ExactStorageContract(
        frozen_native_artifacts={
            str(native_path.resolve()): hashlib.sha256(native_path.read_bytes()).hexdigest()
        },
        scratch_not_shared_with_children_or_loaders=True,
        durable_root_is_new_namespace=True,
        durable_writes_use_create_once_recorder_only=True,
        serial_no_child_processes=True,
        source_stage_loads_frozen_native_without_build=True,
    )


def make_sink(tmp_path: Path, **updates: object) -> ProcessTreeTelemetrySink:
    scratch = tmp_path / "scratch"
    durable = tmp_path / "durable"
    scratch.mkdir(parents=True, exist_ok=True)
    durable.mkdir(parents=True, exist_ok=True)
    args: dict[str, object] = {
        "preflight_receipt": receipt(),
        "scratch_root": scratch,
        "durable_root": durable,
        "now": NOW,
        "sample_interval_seconds": 3600.0,
        "sampler": AdvancingSampler(),
        "clock": AdvancingClock(),
        "logical_processor_count": 8,
        "test_mode": True,
    }
    args.update(updates)
    return ProcessTreeTelemetrySink(**args)  # type: ignore[arg-type]


def observe_all_stages(sink: ProcessTreeTelemetrySink) -> None:
    for stage in STAGES:
        with sink.stage(stage):
            pass


def make_exact_sink(tmp_path: Path) -> tuple[ProcessTreeTelemetrySink, Path, Path, Path]:
    native = tmp_path / "frozen-native.dll"
    native.write_bytes(b"frozen-native-v1")
    scratch = tmp_path / "exact-scratch"
    durable = tmp_path / "exact-durable"
    scratch.mkdir()
    durable.mkdir()
    sink = ProcessTreeTelemetrySink(
        preflight_receipt=receipt(),
        scratch_root=scratch,
        durable_root=durable,
        now=NOW,
        sample_interval_seconds=3600.0,
        sampler=SingleAdvancingSampler(),
        logical_processor_count=8,
        exact_storage_contract=exact_contract(native),
    ).start()
    return sink, scratch, durable, native


def test_terminal_matches_runner_schema_and_binds_separate_counters(tmp_path: Path) -> None:
    sink = make_sink(tmp_path).start()
    (tmp_path / "scratch" / "work.bin").write_bytes(b"x" * 17)
    for name in STAGES:
        with sink.stage(name):
            if name == "serialization":
                (tmp_path / "durable" / "artifact.bin").write_bytes(b"y" * 23)
    payload = sink.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())

    assert TELEMETRY_FIELDS <= set(payload)
    assert payload["telemetry_schema"] == TELEMETRY_SCHEMA
    assert payload["telemetry_terminal"] is False
    assert payload["performance_evidence"] is False
    assert payload["implementation_ready"] is False
    assert payload["performance_readiness"] == "REPAIR_REQUIRED"
    assert payload["storage_high_water_disposition"] == "SAMPLED_LOWER_BOUND_NOT_EXACT"
    assert payload["measurement_source"] == "INJECTED_TEST_ONLY_NOT_PERFORMANCE_EVIDENCE"
    assert set(payload["stage_wall_seconds"]) == set(STAGES)  # type: ignore[arg-type]
    assert set(payload["stage_cpu_seconds"]) == set(STAGES)  # type: ignore[arg-type]
    assert payload["process_tree_peak_rss_bytes"] >= 3000
    assert payload["peak_process_count"] == 2
    assert payload["peak_thread_count"] == 5
    assert payload["scratch_peak_bytes"] == 17
    assert payload["durable_peak_bytes"] == 23
    assert payload["available_physical_bytes"] == 6 * 1024**3
    assert payload["effective_available_bytes"] == 5 * 1024**3
    assert payload["parameter_count_by_arm"] == counters()["parameter_count_by_arm"]
    assert payload["primary_host_calls"] == ledger()["primary_host_calls"]
    assert payload["scientific_work_transitions_per_second"] > 0
    assert TELEMETRY_FIELDS == runner.REQUIRED_TELEMETRY_FIELDS
    runner.validate_telemetry_sink(sink)
    with pytest.raises(ProcessTelemetryError, match="test-mode"):
        sink.emit(payload)
    with pytest.raises(ProcessTelemetryError, match="not active"):
        sink.finish(scientific_counters=counters(), host_call_ledger=ledger())


def test_retarget_carries_durable_high_water_across_root_change(tmp_path: Path) -> None:
    old = tmp_path / "old"
    new = tmp_path / "new"
    scratch = tmp_path / "scratch"
    old.mkdir()
    new.mkdir()
    scratch.mkdir()
    (old / "old.bin").write_bytes(b"a" * 41)
    sink = make_sink(
        tmp_path,
        scratch_root=scratch,
        durable_root=old,
    ).start()
    sink.retarget_durable_root(new)
    (new / "new.bin").write_bytes(b"b" * 13)
    for stage in STAGES:
        with sink.stage(stage):
            pass
    payload = sink.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())
    assert payload["durable_peak_bytes"] == 41


@pytest.mark.parametrize(
    "updates, message",
    [
        ({"effective_available_bytes": 3 * 1024**3}, "admission did not pass"),
        ({"passed": False}, "admission did not pass"),
        ({"captured_at": "2026-09-01T11:00:00Z"}, "not fresh"),
    ],
)
def test_preflight_binding_fails_closed(
    tmp_path: Path, updates: dict[str, object], message: str
) -> None:
    with pytest.raises(ProcessTelemetryError, match=message):
        make_sink(tmp_path, preflight_receipt=receipt(**updates))


def test_any_control_override_forces_non_evidentiary_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = AdvancingSampler()
    monkeypatch.setattr(
        telemetry_module,
        "sample_windows_process_tree",
        lambda root_pid=None, tracked_identities=(): fake(tracked_identities),
    )
    live_now = datetime.now(timezone.utc)
    live_receipt = receipt(captured_at=live_now.isoformat(), assessed_at=live_now.isoformat())
    cases = (
        ("now", receipt(), {"now": NOW}),
        ("logical", live_receipt, {"logical_processor_count": 1}),
        ("interval", live_receipt, {"sample_interval_seconds": 3600.0}),
        (
            "combined",
            receipt(),
            {
                "now": NOW,
                "logical_processor_count": 1,
                "sample_interval_seconds": 3600.0,
            },
        ),
    )
    for label, preflight, overrides in cases:
        scratch = tmp_path / label / "scratch"
        durable = tmp_path / label / "durable"
        scratch.mkdir(parents=True)
        durable.mkdir()
        sink = ProcessTreeTelemetrySink(
            preflight_receipt=preflight,
            scratch_root=scratch,
            durable_root=durable,
            test_mode=False,
            **overrides,
        ).start()
        for stage in STAGES:
            with sink.stage(stage):
                pass
        payload = sink.finish(scientific_counters=counters(), host_call_ledger=ledger())
        assert payload["telemetry_terminal"] is False
        assert payload["performance_evidence"] is False
        with pytest.raises(ProcessTelemetryError, match="test-mode"):
            sink.emit(payload)


def test_sampler_error_and_counter_regression_fail_closed(tmp_path: Path) -> None:
    def broken(_tracked: object) -> tuple[ProcessSample, ...]:
        raise OSError("sample failure")

    with pytest.raises(ProcessTelemetryError, match="sample failure"):
        make_sink(tmp_path, sampler=broken).start()

    rows = iter(
        (
            (ProcessSample(10, 100, 10, 5.0, 5, 5, 5, 1),),
            (ProcessSample(10, 100, 10, 4.0, 5, 5, 5, 1),),
        )
    )
    sink = make_sink(tmp_path, sampler=lambda _tracked: next(rows)).start()
    with pytest.raises(ProcessTelemetryError, match="regressed"):
        sink.snapshot()
    sink.abort()


def test_late_descendant_and_pid_reuse_use_creation_identity(tmp_path: Path) -> None:
    rows = iter(
        (
            (ProcessSample(10, 100, 10, 100.0, 100, 100, 100, 1),),
            (
                ProcessSample(10, 100, 10, 101.0, 101, 102, 103, 1),
                ProcessSample(11, 200, 10, 7.0, 8, 9, 10, 1),
            ),
            (
                ProcessSample(10, 100, 10, 102.0, 102, 104, 106, 1),
                ProcessSample(11, 201, 10, 9.0, 10, 11, 12, 1),
            ),
        )
    )
    sink = make_sink(tmp_path, sampler=lambda _tracked: next(rows)).start()
    first = sink.snapshot()
    second = sink.snapshot()
    # Root delta 2 + first child 7 + reused-PID child 9.  The two child
    # lifetimes are not merged because creation time participates in identity.
    assert second["cpu_seconds"] == 18.0
    assert first["cpu_seconds"] == 8.0
    sink.abort()


def test_discovered_grandchild_identity_survives_parent_exit(tmp_path: Path) -> None:
    class ParentExitSequence:
        def __init__(self) -> None:
            self.calls = 0
            self.tracked: list[set[tuple[int, int]]] = []

        def __call__(
            self, tracked: object
        ) -> tuple[ProcessSample, ...]:
            self.calls += 1
            self.tracked.append(set(tracked))  # type: ignore[arg-type]
            root = ProcessSample(10, 100, 10, 10.0 + self.calls, 1, 1, 1, 1)
            grandchild = ProcessSample(12, 300, 30, 30.0 + self.calls, 3, 3, 3, 1)
            if self.calls == 1:
                parent = ProcessSample(11, 200, 20, 20.0, 2, 2, 2, 1)
                return root, parent, grandchild
            return root, grandchild

    sequence = ParentExitSequence()
    sink = make_sink(tmp_path, sampler=sequence).start()
    snapshot = sink.snapshot()
    assert (11, 200) in sequence.tracked[1]
    assert (12, 300) in sequence.tracked[1]
    assert snapshot["peak_process_count"] == 3
    assert snapshot["cpu_seconds"] == 2.0
    sink.abort()


def test_stage_inventory_and_external_payload_are_not_forgeable(tmp_path: Path) -> None:
    sink = make_sink(tmp_path).start()
    with sink.stage("source_binding"):
        pass
    with pytest.raises(ProcessTelemetryError, match="all four"):
        sink.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())
    sink.abort()

    other = make_sink(tmp_path).start()
    for stage in STAGES:
        with other.stage(stage):
            pass
    payload = other.finish(scientific_counters=counters(), host_call_ledger=ledger())
    forged = dict(payload)
    forged["process_tree_peak_rss_bytes"] = 1
    with pytest.raises(ProcessTelemetryError, match="test-mode"):
        other.emit(forged)


def test_stage_state_machine_rejects_out_of_order_and_repeat(tmp_path: Path) -> None:
    out_of_order = make_sink(tmp_path / "out").start()
    with pytest.raises(ProcessTelemetryError, match="order/exact-once"):
        with out_of_order.stage("serialization"):
            pass
    with pytest.raises(ProcessTelemetryError, match="stage sequence failed"):
        out_of_order.finish(scientific_counters=counters(), host_call_ledger=ledger())
    out_of_order.abort()

    repeated = make_sink(tmp_path / "repeat").start()
    with repeated.stage("source_binding"):
        pass
    with pytest.raises(ProcessTelemetryError, match="order/exact-once"):
        with repeated.stage("source_binding"):
            pass
    with pytest.raises(ProcessTelemetryError, match="stage sequence failed"):
        repeated.finish(scientific_counters=counters(), host_call_ledger=ledger())
    repeated.abort()


@pytest.mark.parametrize("invalid", [True, float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize(
    "field",
    [
        "parameter_count_by_arm",
        "forward_calls_by_arm",
        "backward_calls_by_arm",
        "flop_exposure_by_arm",
    ],
)
def test_every_per_arm_counter_rejects_bool_and_nonfinite(
    tmp_path: Path, field: str, invalid: object
) -> None:
    sink = make_sink(tmp_path).start()
    for stage in STAGES:
        with sink.stage(stage):
            pass
    bad = counters()
    bad[field] = {"MAPR": invalid, "DIRECT": 1}
    with pytest.raises(ProcessTelemetryError, match="nonpositive"):
        sink.finish(scientific_counters=bad, host_call_ledger=ledger())
    sink.abort()


@pytest.mark.parametrize(
    "field, invalid",
    [
        ("native_integrated_ticks", True),
        ("native_integrated_ticks", float("nan")),
        ("scientific_work_transitions", float("inf")),
        ("worker_count", True),
        ("threads_per_worker", float("-inf")),
    ],
)
def test_every_scalar_scientific_counter_is_strict(
    tmp_path: Path, field: str, invalid: object
) -> None:
    sink = make_sink(tmp_path).start()
    for stage in STAGES:
        with sink.stage(stage):
            pass
    bad = counters()
    bad[field] = invalid
    with pytest.raises(ProcessTelemetryError, match="positive integer"):
        sink.finish(scientific_counters=bad, host_call_ledger=ledger())
    sink.abort()


@pytest.mark.parametrize("interval", [True, float("nan"), float("inf")])
def test_sample_interval_override_is_finite_and_positive(tmp_path: Path, interval: object) -> None:
    with pytest.raises(ProcessTelemetryError, match="sample interval"):
        make_sink(tmp_path, sample_interval_seconds=interval)


def test_exact_r01_create_once_closes_storage_peak(tmp_path: Path) -> None:
    sink, scratch, durable, _native = make_exact_sink(tmp_path)
    observe_all_stages(sink)
    with sink.observe_create_once("nested/result.json") as path:
        path.parent.mkdir()
        path.write_bytes(b"result")
    with sink.observe_create_once("receipt.json") as receipt_path:
        receipt_path.write_bytes(b"receipt")
    payload = sink.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())

    assert payload["storage_high_water_disposition"] == "EXACT_R01_MONOTONIC_CREATE_ONLY"
    assert payload["implementation_ready"] is True
    assert payload["performance_readiness"] == "READY"
    assert payload["execution_topology"] == "SERIAL_NO_CHILD_PROCESSES"
    assert payload["source_native_admission"] == "PREBUILT_FROZEN_LOAD_ONLY_NO_COMPILE"
    assert payload["telemetry_terminal"] is False  # injected controls force test mode
    assert payload["scratch_peak_bytes"] == 0
    assert payload["durable_peak_bytes"] == len(b"result") + len(b"receipt")
    assert payload["durable_directory_total_bytes"] == payload["durable_peak_bytes"]
    assert [row["relative_path"] for row in payload["durable_artifact_inventory"]] == [  # type: ignore[index]
        "nested/result.json",
        "receipt.json",
    ]
    assert list(scratch.iterdir()) == []
    with pytest.raises(ProcessTelemetryError, match="test-mode"):
        sink.emit(payload)


def test_explicit_measurement_boundary_seals_body_then_observer_bundle(tmp_path: Path) -> None:
    sink, _scratch, durable, _native = make_exact_sink(tmp_path)
    with sink.observe_create_once("RESULT_BODY.json") as body_path:
        body_path.write_bytes(b"result-body")
    observe_all_stages(sink)
    payload = sink.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())
    scientific_bytes = len(b"result-body")
    assert payload["durable_peak_bytes"] == scientific_bytes
    assert payload["observer_publication_required"] is True
    assert payload["valid_artifact_bundle"] == (
        "RESULT_BODY_PLUS_TELEMETRY_TERMINAL_PLUS_VALID_CLAIM"
    )

    publication = tmp_path / "observer-publication"
    publication.mkdir()
    receipt_value = sink.publish_observer_bundle(
        publication,
        namespace="vnfc/b-explore/debug/2026090101",
        scientific_body_relative_path="RESULT_BODY.json",
        publication_root_is_new_namespace=True,
    )
    telemetry_bytes = (publication / "TELEMETRY_TERMINAL.json").read_bytes()
    claim_bytes = (publication / "VALID_CLAIM.json").read_bytes()
    document = json.loads(telemetry_bytes)
    assert set(document) == {
        "schema", "namespace", "scientific_body", "scientific_storage_seal", "telemetry"
    }
    assert document["schema"] == "VNFC_BPCR_BEXP_R01_TELEMETRY_TERMINAL_V1"
    assert document["telemetry"] == json.loads(json.dumps(payload))
    claim = json.loads(claim_bytes)
    assert set(claim) == {
        "schema",
        "namespace",
        "scientific_body_relative_path",
        "scientific_body_size_bytes",
        "scientific_body_sha256",
        "scientific_storage_seal_sha256",
        "telemetry_relative_path",
        "telemetry_size_bytes",
        "telemetry_sha256",
    }
    assert claim["schema"] == "VNFC_BPCR_BEXP_R01_VALID_CLAIM_V1"
    assert claim["namespace"] == "vnfc/b-explore/debug/2026090101"
    assert claim["telemetry_sha256"] == hashlib.sha256(telemetry_bytes).hexdigest()
    assert claim["scientific_body_sha256"] == hashlib.sha256(b"result-body").hexdigest()
    assert payload["durable_peak_bytes"] == scientific_bytes
    assert receipt_value["telemetry_publication_bytes"] == len(telemetry_bytes) + len(claim_bytes)
    assert receipt_value["observer_publication_overhead_excluded_from_scientific_measurement"] is True
    seal = sink.verify_storage_seal()
    assert seal["durable_directory_total_bytes"] == scientific_bytes
    assert sink.verify_observer_publication()["valid"] is True
    assert "telemetry_builder" not in inspect.signature(sink.publish_observer_bundle).parameters
    assert "claim_builder" not in inspect.signature(sink.publish_observer_bundle).parameters
    with pytest.raises(ProcessTelemetryError, match="already sealed"):
        with sink.observe_create_once("late.json"):
            pass
    (publication / "late.bin").write_bytes(b"late")
    with pytest.raises(ProcessTelemetryError, match="INCOMPLETE"):
        sink.verify_observer_publication()


@pytest.mark.parametrize("mutation", ["unknown_file", "unknown_directory", "scratch"])
def test_exact_storage_rejects_unknown_or_scratch_mutation(
    tmp_path: Path, mutation: str
) -> None:
    sink, scratch, durable, _native = make_exact_sink(tmp_path)
    observe_all_stages(sink)
    if mutation == "unknown_file":
        (durable / "unknown.bin").write_bytes(b"unknown")
    elif mutation == "unknown_directory":
        (durable / "unknown-directory").mkdir()
    else:
        (scratch / "forbidden.bin").write_bytes(b"forbidden")
    with pytest.raises(ProcessTelemetryError, match="INCOMPLETE"):
        sink.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())
    sink.abort()


def test_posthoc_registration_seam_is_absent_and_transient_write_cannot_be_laundered(
    tmp_path: Path,
) -> None:
    sink, _scratch, durable, _native = make_exact_sink(tmp_path)
    assert not hasattr(sink, "register_durable_artifact")
    transient = durable / "artifact.bin"
    transient.write_bytes(b"x" * 1024**2)
    transient.unlink()
    transient.write_bytes(b"x")
    observe_all_stages(sink)
    with pytest.raises(ProcessTelemetryError, match="INCOMPLETE"):
        sink.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())
    sink.abort()


def test_manifest_failure_freezes_partial_then_allows_monotonic_incomplete_quarantine(
    tmp_path: Path,
) -> None:
    sink, _scratch, durable, _native = make_exact_sink(tmp_path)
    for stage in STAGES[:3]:
        with sink.stage(stage):
            pass

    class ManifestFailure(RuntimeError):
        pass

    with pytest.raises(ManifestFailure):
        with sink.stage("serialization"):
            with sink.observe_create_once("RESULT_BODY.json") as body:
                body.write_bytes(b"body-complete")
            with sink.observe_create_once("MANIFEST.json") as manifest:
                manifest.write_bytes(b"partial-manifest")
                raise ManifestFailure("manifest sibling failed")

    assert (durable / "RESULT_BODY.json").read_bytes() == b"body-complete"
    assert (durable / "MANIFEST.json").read_bytes() == b"partial-manifest"
    with sink.observe_incomplete_create_once(
        "INCOMPLETE.json", reason="manifest sibling failed after RESULT_BODY"
    ) as quarantine:
        quarantine.write_bytes(b'{"status":"INCOMPLETE"}')

    payload = sink.finish_incomplete(
        scientific_counters=exact_counters(), host_call_ledger=ledger()
    )
    assert payload["attempt_disposition"] == "INCOMPLETE"
    assert payload["scientific_result_valid"] is False
    assert payload["valid_artifact_bundle"] == (
        "INCOMPLETE_BODY_PLUS_TELEMETRY_TERMINAL_PLUS_INCOMPLETE_CLAIM"
    )
    assert [row["relative_path"] for row in payload["durable_artifact_inventory"]] == [  # type: ignore[index]
        "INCOMPLETE.json",
        "MANIFEST.json",
        "RESULT_BODY.json",
    ]
    publication = tmp_path / "incomplete-publication"
    publication.mkdir()
    receipt_value = sink.publish_observer_bundle(
        publication,
        namespace="vnfc/b-explore/debug/2026090101/incomplete",
        scientific_body_relative_path="INCOMPLETE.json",
        publication_root_is_new_namespace=True,
    )
    assert receipt_value["claim_disposition"] == "INCOMPLETE"
    assert not (publication / "VALID_CLAIM.json").exists()
    claim = json.loads((publication / "INCOMPLETE_CLAIM.json").read_bytes())
    assert claim["schema"] == "VNFC_BPCR_BEXP_R01_INCOMPLETE_CLAIM_V1"
    assert claim["attempt_disposition"] == "INCOMPLETE"
    assert sink.verify_storage_seal()["valid"] is True
    assert sink.verify_observer_publication()["valid"] is True
    with pytest.raises(ProcessTelemetryError, match="already sealed"):
        with sink.observe_incomplete_create_once("late.json", reason="late"):
            pass


def test_serial_exact_contract_rejects_any_observed_descendant(tmp_path: Path) -> None:
    native = tmp_path / "native.dll"
    native.write_bytes(b"native")
    scratch = tmp_path / "scratch"
    durable = tmp_path / "durable"
    scratch.mkdir()
    durable.mkdir()
    sink = ProcessTreeTelemetrySink(
        preflight_receipt=receipt(),
        scratch_root=scratch,
        durable_root=durable,
        now=NOW,
        sampler=AdvancingSampler(),  # returns root plus one observed child
        exact_storage_contract=exact_contract(native),
    )
    with pytest.raises(ProcessTelemetryError, match="SERIAL_NO_CHILD_PROCESSES"):
        sink.start()
    sink.abort()


@pytest.mark.parametrize("mutation", ["overwrite", "size_decrease", "delete"])
def test_exact_storage_rejects_change_to_registered_artifact(
    tmp_path: Path, mutation: str
) -> None:
    sink, _scratch, durable, _native = make_exact_sink(tmp_path)
    with sink.observe_create_once("artifact.bin") as path:
        path.write_bytes(b"original-long")
    observe_all_stages(sink)
    target = durable / "artifact.bin"
    if mutation == "overwrite":
        target.write_bytes(b"changed-value")
    elif mutation == "size_decrease":
        target.write_bytes(b"x")
    else:
        target.unlink()
    with pytest.raises(ProcessTelemetryError, match="INCOMPLETE"):
        sink.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())
    sink.abort()


def test_exact_storage_rejects_frozen_native_drift_and_retarget(tmp_path: Path) -> None:
    sink, _scratch, durable, native = make_exact_sink(tmp_path)
    with sink.observe_create_once("artifact.bin") as path:
        path.write_bytes(b"artifact")
    observe_all_stages(sink)
    native.write_bytes(b"native-drift")
    with pytest.raises(ProcessTelemetryError, match="INCOMPLETE"):
        sink.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())
    sink.abort()

    other_root = tmp_path / "other-case"
    other_root.mkdir()
    other, _scratch, _durable, _native = make_exact_sink(other_root)
    replacement = other_root / "replacement"
    replacement.mkdir()
    with pytest.raises(ProcessTelemetryError, match="INCOMPLETE"):
        other.retarget_durable_root(replacement)
    other.abort()


def test_exact_storage_requires_empty_roots_and_at_least_one_valid_artifact(tmp_path: Path) -> None:
    native = tmp_path / "native.dll"
    native.write_bytes(b"native")
    scratch = tmp_path / "scratch"
    durable = tmp_path / "durable"
    scratch.mkdir()
    durable.mkdir()
    (durable / "prior.bin").write_bytes(b"prior")
    sink = ProcessTreeTelemetrySink(
        preflight_receipt=receipt(),
        scratch_root=scratch,
        durable_root=durable,
        now=NOW,
        sampler=AdvancingSampler(),
        exact_storage_contract=exact_contract(native),
    )
    with pytest.raises(ProcessTelemetryError, match="INCOMPLETE"):
        sink.start()
    sink.abort()

    clean_root = tmp_path / "clean"
    clean_root.mkdir()
    empty, _scratch, _durable, _native = make_exact_sink(clean_root)
    observe_all_stages(empty)
    with pytest.raises(ProcessTelemetryError, match="INCOMPLETE"):
        empty.finish(scientific_counters=exact_counters(), host_call_ledger=ledger())
    empty.abort()


@pytest.mark.skipif(os.name != "nt", reason="Windows-only production sampler")
def test_bounded_real_self_process_readiness_probe(tmp_path: Path) -> None:
    rows = sample_windows_process_tree(os.getpid())
    root = [row for row in rows if row.pid == os.getpid()]
    assert len(root) == 1
    assert root[0].creation_time_100ns > 0
    assert root[0].rss_bytes > 0
    assert root[0].thread_count > 0

    scratch = tmp_path / "real-scratch"
    durable = tmp_path / "real-durable"
    scratch.mkdir()
    durable.mkdir()
    live_now = datetime.now(timezone.utc)
    live_receipt = receipt(
        captured_at=live_now.isoformat(),
        assessed_at=live_now.isoformat(),
    )
    sink = ProcessTreeTelemetrySink(
        preflight_receipt=live_receipt,
        scratch_root=scratch,
        durable_root=durable,
    ).start()
    for stage in STAGES:
        with sink.stage(stage):
            # Outcome-free bounded CPU activity gives the process counter a
            # chance to advance without launching an endpoint or model.
            sum(index * index for index in range(20_000))
    payload = sink.finish(scientific_counters=counters(), host_call_ledger=ledger())
    assert payload["process_tree_peak_rss_bytes"] > 0
    assert payload["sample_count"] >= 10
    assert payload["measurement_source"].startswith("Windows")
    assert payload["telemetry_terminal"] is False
    assert payload["performance_readiness"] == "REPAIR_REQUIRED"
    with pytest.raises(ProcessTelemetryError, match="REPAIR_REQUIRED"):
        sink.emit(payload)
