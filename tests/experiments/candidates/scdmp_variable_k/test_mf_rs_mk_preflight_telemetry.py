from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
import stat
import threading
import time
from types import SimpleNamespace

import pytest

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.preflight import (
    PreflightError,
    preflight_run,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.resources import (
    ContinuousResourceMonitor,
    MeasurementIncident,
    ResourceLimits,
    ResourceTelemetry,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import resources as resources_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.runner import (
    A_PILOT_PERFORMANCE_DISPOSITION,
    RUN_01_PERFORMANCE_DISPOSITION,
    ResultExecutionDisabled,
    preflight_only,
    run_result,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import runner as runner_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import assessment as assessment_module


FOUR_GIB = 4 * 1024**3


class _ScandirRows:
    def __init__(self, rows):
        self.rows = tuple(rows)

    def __enter__(self):
        return iter(self.rows)

    def __exit__(self, *_args):
        return False


class _ScandirEntry:
    def __init__(self, name, stat_source):
        self.name = name
        self._stat_source = stat_source

    def stat(self, *, follow_symlinks):
        assert follow_symlinks is False
        return self._stat_source()


def test_tree_bytes_tolerates_only_enumerated_ephemeral_disappearance(tmp_path, monkeypatch) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    vanished = root / "ephemeral.tmp"
    incidents = []
    monkeypatch.setattr(
        os, "scandir",
        lambda path: _ScandirRows((_ScandirEntry(
            vanished.name, lambda: (_ for _ in ()).throw(FileNotFoundError(2, "gone")),
        ),)),
    )
    assert resources_module._tree_bytes(root, incident_sink=incidents.append) == 0
    assert incidents == [MeasurementIncident(
        "TOLERATED", "EPHEMERAL_DESCENDANT_DISAPPEARED", "FileNotFoundError",
        "tree_descendant_stat", resources_module._path_summary(root, vanished), 2,
        None,
    )]
    with pytest.raises(FileNotFoundError):
        resources_module._tree_bytes(tmp_path / "missing-root")


def test_tree_bytes_root_loss_after_initial_stat_is_fatal(tmp_path, monkeypatch) -> None:
    root = tmp_path / "root-loss"
    root.mkdir()

    def remove_then_enumerate(_path):
        root.rmdir()
        return _ScandirRows(())

    monkeypatch.setattr(os, "scandir", remove_then_enumerate)
    with pytest.raises(FileNotFoundError):
        resources_module.tree_bytes(root)


def test_tree_bytes_root_identity_replacement_is_fatal(tmp_path, monkeypatch) -> None:
    root = tmp_path / "root-replaced"
    root.mkdir()
    original_stat = Path.stat
    calls = 0

    def changed_identity(path, *args, **kwargs):
        nonlocal calls
        observed = original_stat(path, *args, **kwargs)
        if path != root:
            return observed
        calls += 1
        if calls == 1:
            return observed
        values = list(observed)
        values[1] = int(observed.st_ino) + 1
        return os.stat_result(values)

    monkeypatch.setattr(Path, "stat", changed_identity)
    monkeypatch.setattr(os, "scandir", lambda _path: _ScandirRows(()))
    with pytest.raises(OSError, match="identity changed"):
        resources_module.tree_bytes(root)


def test_tree_bytes_missing_filesystem_identity_is_fail_closed(tmp_path, monkeypatch) -> None:
    root = tmp_path / "identity-none"
    root.mkdir()
    monkeypatch.setattr(Path, "stat", lambda self, *args, **kwargs: SimpleNamespace(
        st_mode=stat.S_IFDIR, st_size=0, st_dev=0, st_ino=0, st_file_attributes=0,
    ))
    with pytest.raises(OSError, match="no stable filesystem identity"):
        resources_module.tree_bytes(root)


@pytest.mark.parametrize("kind", ("permission", "other_errno", "symlink"))
def test_tree_bytes_other_stat_or_file_type_errors_fail_closed(tmp_path, monkeypatch, kind) -> None:
    root = tmp_path / "tree-fatal"
    root.mkdir()
    child = root / "child"
    def injected():
        if kind == "permission":
            raise PermissionError(13, "denied")
        if kind == "other_errno":
            raise OSError(5, "io")
        return SimpleNamespace(
            st_mode=stat.S_IFLNK, st_size=0, st_dev=1, st_ino=2,
            st_file_attributes=0,
        )

    monkeypatch.setattr(
        os, "scandir", lambda _path: _ScandirRows((_ScandirEntry(child.name, injected),)),
    )
    with pytest.raises((PermissionError, OSError)):
        resources_module._tree_bytes(root)


@pytest.mark.parametrize("error", (
    PermissionError(13, "denied"), FileNotFoundError(2, "directory gone"), OSError(5, "io"),
))
def test_descendant_scandir_errors_are_fatal_even_with_real_bytes(
    tmp_path, monkeypatch, error,
) -> None:
    root = tmp_path / "scandir-fatal"
    denied = root / "denied"
    denied.mkdir(parents=True)
    (root / "actual.bin").write_bytes(b"x" * 123)
    original_scandir = os.scandir

    def injected(path):
        if Path(path) == denied:
            raise error
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", injected)
    with pytest.raises(type(error)):
        resources_module.tree_bytes(root)


def test_runner_and_assessment_tail_use_shared_robust_tree_traversal(tmp_path, monkeypatch) -> None:
    root = tmp_path / "shared-tree"
    root.mkdir()
    calls = []

    def shared(path):
        calls.append(path)
        return 17

    monkeypatch.setattr(runner_module, "tree_bytes", shared)
    monkeypatch.setattr(assessment_module, "tree_bytes", shared)
    assert runner_module._tree_bytes(root) == 17
    assert assessment_module._tree_bytes(root) == 17
    assert calls == [root, root]
    monkeypatch.setattr(runner_module, "tree_bytes", resources_module.tree_bytes)
    monkeypatch.setattr(assessment_module, "tree_bytes", resources_module.tree_bytes)
    with pytest.raises(FileNotFoundError):
        runner_module._tree_bytes(tmp_path / "missing")
    with pytest.raises(FileNotFoundError):
        assessment_module._tree_bytes(tmp_path / "missing")


def test_monitor_persists_typed_fatal_measurement_incident(tmp_path) -> None:
    root = tmp_path / "fatal-size"
    root.mkdir()
    cpu = iter((0.0, 1.0))
    monitor = ContinuousResourceMonitor(
        scratch_root=root, durable_root=root,
        snapshot_source=lambda: {
            "process_tree_rss_bytes": 1, "cpu_seconds": next(cpu),
            "process_count": 1, "thread_count": 1, "available_memory_bytes": FOUR_GIB,
        },
        size_source=lambda _s, _d: (_ for _ in ()).throw(PermissionError(13, "denied")),
        clock=iter((0.0, 1.0)).__next__, autostart=False,
    )
    monitor.sample_now()
    observed = monitor.finalize(exit_status=0)
    assert observed.failure_reasons == ("telemetry_missing", "telemetry_measurement_failed")
    assert observed.measurement_incidents == (MeasurementIncident(
        "FATAL", "MEASUREMENT_ABORTED", "PermissionError", "sample_now",
        "measurement-root", 13, None,
    ),)


def test_open_process_failure_only_tolerates_known_exited_child_codes() -> None:
    exited = OSError("child exited")
    exited.winerror = 87
    tolerated = resources_module._classify_open_process_failure(
        pid=200, root_pid=100, error=exited,
    )
    assert tolerated is not None
    assert tolerated.severity == "TOLERATED"
    assert tolerated.disposition == "CHILD_EXITED_BEFORE_OPEN_PROCESS"
    assert resources_module._classify_open_process_failure(
        pid=100, root_pid=100, error=exited,
    ) is None
    denied = PermissionError("denied")
    denied.winerror = 5
    assert resources_module._classify_open_process_failure(
        pid=200, root_pid=100, error=denied,
    ) is None
    during = OSError("gone during sample")
    during.winerror = 6
    row = resources_module._classify_process_sampling_failure(
        phase="windows_process_times", pid=200, root_pid=100, error=during,
    )
    assert row is not None and row.disposition == "CHILD_EXITED_DURING_PROCESS_SAMPLING"
    assert resources_module._classify_process_sampling_failure(
        phase="windows_process_times", pid=100, root_pid=100, error=during,
    ) is None
    assert resources_module._classify_process_sampling_failure(
        phase="windows_process_times", pid=200, root_pid=100, error=denied,
    ) is None


def test_snapshot_fatal_incident_is_preserved_without_generic_duplicate(tmp_path) -> None:
    primary = MeasurementIncident(
        "FATAL", "ROOT_PROCESS_OPEN_FAILED", "PermissionError",
        "windows_open_process", "process-root", None, 5,
    )
    monitor = ContinuousResourceMonitor(
        scratch_root=tmp_path, durable_root=tmp_path,
        snapshot_source=lambda: {
            "process_tree_rss_bytes": 1, "cpu_seconds": 0.1,
            "process_count": 1, "thread_count": 1, "available_memory_bytes": FOUR_GIB,
            "measurement_incidents": [primary],
        },
        clock=iter((0.0, 1.0)).__next__, autostart=False,
    )
    monitor.sample_now()
    observed = monitor.finalize(exit_status=1)
    assert observed.measurement_incidents == (primary,)
    assert observed.failure_reasons == ("telemetry_missing", "telemetry_measurement_failed")


def test_default_tree_and_windows_measurement_failures_preserve_exact_phase(tmp_path, monkeypatch) -> None:
    scratch = tmp_path / "phase-scratch"
    durable = tmp_path / "phase-durable"
    scratch.mkdir()
    durable.mkdir()

    def denied(path, **_kwargs):
        if path == scratch:
            raise PermissionError(13, "denied")
        return 0

    monkeypatch.setattr(resources_module, "tree_bytes", denied)
    monitor = ContinuousResourceMonitor(
        scratch_root=scratch, durable_root=durable,
        snapshot_source=lambda: {
            "process_tree_rss_bytes": 1, "cpu_seconds": 0.1,
            "process_count": 1, "thread_count": 1, "available_memory_bytes": FOUR_GIB,
        }, clock=iter((0.0, 1.0)).__next__, autostart=False,
    )
    monitor.sample_now()
    observed = monitor.finalize(exit_status=1)
    assert len(observed.measurement_incidents) == 1
    incident = observed.measurement_incidents[0]
    assert incident.exception_class == "PermissionError"
    assert incident.phase == "scratch_tree_measurement"

    primary = PermissionError(13, "root process")
    primary.winerror = 5
    failure = resources_module._measurement_failure(
        primary, disposition="PROCESS_TIMES_FAILED", phase="windows_process_times",
        path_summary="process-root",
    )
    monitor = ContinuousResourceMonitor(
        scratch_root=scratch, durable_root=durable,
        snapshot_source=lambda: (_ for _ in ()).throw(failure),
        clock=iter((0.0, 1.0)).__next__, autostart=False,
    )
    monitor.sample_now()
    observed = monitor.finalize(exit_status=1)
    assert observed.measurement_incidents == (failure.incident,)


def test_windows_cleanup_failure_appends_after_primary_without_replacing_it(tmp_path) -> None:
    primary_error = PermissionError(13, "memory primary")
    primary_error.winerror = 5
    primary = resources_module._measurement_failure(
        primary_error, disposition="PROCESS_MEMORY_FAILED", phase="windows_process_memory",
        path_summary="process-root",
    )
    close_error = OSError("close failed")
    close_error.winerror = 6
    cleanup = resources_module._measurement_failure(
        close_error, disposition="PROCESS_HANDLE_CLOSE_FAILED",
        phase="windows_process_handle_close", path_summary="process-root",
    )
    merged = resources_module._preserve_primary_with_cleanup(primary, cleanup)
    assert merged is primary
    assert merged.primary is primary_error
    assert [row.phase for row in merged.incidents] == [
        "windows_process_memory", "windows_process_handle_close",
    ]

    monitor = ContinuousResourceMonitor(
        scratch_root=tmp_path, durable_root=tmp_path,
        snapshot_source=lambda: (_ for _ in ()).throw(merged),
        clock=iter((0.0, 1.0)).__next__, autostart=False,
    )
    monitor.sample_now()
    observed = monitor.finalize(exit_status=1)
    assert tuple(row.phase for row in observed.measurement_incidents) == (
        "windows_process_memory", "windows_process_handle_close",
    )
    assert observed.measurement_incidents[0].exception_class == "PermissionError"


def test_concurrent_atomic_writer_and_real_size_traversal_is_nonzero_and_complete(tmp_path) -> None:
    scratch = tmp_path / "stress-scratch"
    durable = tmp_path / "stress-durable"
    scratch.mkdir()
    durable.mkdir()
    state = {"cpu": 0.0}
    state_lock = threading.Lock()

    def snapshot():
        with state_lock:
            state["cpu"] += 0.01
            cpu = state["cpu"]
        return {
            "process_tree_rss_bytes": 1024, "cpu_seconds": cpu,
            "process_count": 1, "thread_count": 2, "available_memory_bytes": FOUR_GIB,
        }

    monitor = ContinuousResourceMonitor(
        scratch_root=scratch, durable_root=durable, snapshot_source=snapshot,
        interval_seconds=0.001, limits=ResourceLimits(1024**2, 1024**2, 1024**2, 10.0),
    )

    def writer():
        for index in range(250):
            temporary = scratch / f".{index}.tmp"
            linked = durable / f"{index}.bin"
            with temporary.open("wb") as stream:
                stream.write(b"x" * 257)
                stream.flush()
                os.fsync(stream.fileno())
            monitor.observe_scratch_path(temporary)
            os.link(temporary, linked)
            temporary.unlink()

    thread = threading.Thread(target=writer)
    thread.start()
    thread.join(timeout=20)
    assert not thread.is_alive()
    observed = monitor.finalize(exit_status=0)
    assert observed.sample_count > 0
    assert observed.scratch_high_water_bytes >= 257
    assert observed.durable_high_water_bytes > 0
    assert "telemetry_missing" not in observed.failure_reasons
    assert "telemetry_measurement_failed" not in observed.failure_reasons
    assert all(row.disposition == "EPHEMERAL_DESCENDANT_DISAPPEARED"
               for row in observed.measurement_incidents)


def test_measurement_incident_roundtrip_and_old_generic_telemetry_do_not_invent_class(tmp_path) -> None:
    incident = MeasurementIncident(
        "TOLERATED", "EPHEMERAL_DESCENDANT_DISAPPEARED", "FileNotFoundError",
        "tree_descendant_stat", "descendant-sha256:0123456789abcdef", 2,
        2 if os.name == "nt" else None,
    )
    telemetry = ResourceTelemetry(
        True, (), 1, 1, 1, 1, 1.0, 1.0, 1.0, 1, 1,
        FOUR_GIB, FOUR_GIB, 0, measurement_incidents=(incident,),
    )
    path = tmp_path / "telemetry.json"
    path.write_text(json.dumps(asdict(telemetry)), encoding="utf-8")
    assert runner_module._load_telemetry(path).measurement_incidents == (incident,)
    old = asdict(telemetry)
    old.pop("measurement_incidents")
    path.write_text(json.dumps(old), encoding="utf-8")
    assert runner_module._load_telemetry(path).measurement_incidents == ()


def _fake_admission(path: Path, *, physical: int = FOUR_GIB, effective: int = FOUR_GIB):
    def execute(command, **_kwargs):
        assert command[-2:] == ["--out", str(path)]
        path.write_text(json.dumps({
            "minimum_available_bytes": FOUR_GIB,
            "available_physical_bytes": physical,
            "effective_available_bytes": effective,
            "physical_floor_pass": physical >= FOUR_GIB,
            "effective_floor_pass": effective >= FOUR_GIB,
            "passed": physical >= FOUR_GIB and effective >= FOUR_GIB,
        }), encoding="utf-8")
        return SimpleNamespace(returncode=0 if physical >= FOUR_GIB and effective >= FOUR_GIB else 1)
    return execute


def test_preflight_validates_fresh_physical_and_effective_floor_without_result_root(tmp_path) -> None:
    receipt = tmp_path / "admit.json"
    result_root = tmp_path / "scientific-result"

    observed = preflight_only(
        receipt=receipt,
        result_root=result_root,
        command_runner=_fake_admission(receipt),
    )

    assert observed.passed is True
    assert observed.available_physical_bytes == FOUR_GIB
    assert observed.effective_available_bytes == FOUR_GIB
    assert receipt.is_file()
    assert not result_root.exists()


def test_preflight_refuses_missing_floor_or_existing_scientific_root(tmp_path) -> None:
    receipt = tmp_path / "admit.json"
    with pytest.raises(PreflightError, match="4 GiB"):
        preflight_run(receipt, command_runner=_fake_admission(receipt, effective=FOUR_GIB - 1))
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    with pytest.raises(PreflightError, match="must not exist"):
        preflight_only(
            receipt=tmp_path / "second.json",
            result_root=occupied,
            command_runner=_fake_admission(tmp_path / "second.json"),
        )


def test_continuous_monitor_tracks_process_tree_and_high_waters_fail_closed(tmp_path) -> None:
    scratch = tmp_path / "scratch"
    durable = tmp_path / "durable"
    scratch.mkdir()
    durable.mkdir()
    snapshots = iter((
        {"process_tree_rss_bytes": 100, "cpu_seconds": 1.0, "process_count": 1, "thread_count": 2,
         "available_memory_bytes": FOUR_GIB, "foreground_io_read_bytes": 10,
         "foreground_io_write_bytes": 20},
        {"process_tree_rss_bytes": 250, "cpu_seconds": 2.5, "process_count": 2, "thread_count": 5,
         "available_memory_bytes": FOUR_GIB - 1, "foreground_io_read_bytes": 110,
         "foreground_io_write_bytes": 220},
    ))
    sizes = iter(((10, 4), (30, 12)))
    clock = iter((10.0, 11.0, 12.0))
    monitor = ContinuousResourceMonitor(
        scratch_root=scratch,
        durable_root=durable,
        snapshot_source=lambda: next(snapshots),
        size_source=lambda _s, _d: next(sizes),
        clock=lambda: next(clock),
        limits=ResourceLimits(300, 40, 20, 5.0),
        autostart=False,
    )
    monitor.sample_now()
    monitor.sample_now()
    result = monitor.finalize(exit_status=0)

    assert result.passed is True
    assert result.sample_count == 2
    assert result.process_tree_peak_rss_bytes == 250
    assert result.scratch_high_water_bytes == 30
    assert result.durable_high_water_bytes == 12
    assert result.max_process_count == 2
    assert result.max_thread_count == 5
    assert result.cpu_seconds == pytest.approx(1.5)
    assert result.wall_seconds == pytest.approx(2.0)
    assert result.cpu_utilization_fraction == pytest.approx(0.75)
    assert result.foreground_io_read_bytes == 100
    assert result.foreground_io_write_bytes == 200


def test_missing_or_over_cap_telemetry_is_invalid_and_result_entry_is_disabled(tmp_path) -> None:
    assert A_PILOT_PERFORMANCE_DISPOSITION == "PILOT_ONLY"
    assert RUN_01_PERFORMANCE_DISPOSITION == "REPAIR_REQUIRED"
    monitor = ContinuousResourceMonitor(
        scratch_root=tmp_path,
        durable_root=tmp_path,
        snapshot_source=lambda: {
            "process_tree_rss_bytes": 301,
            "cpu_seconds": 0.0,
            "process_count": 1,
            "thread_count": 1,
            "available_memory_bytes": FOUR_GIB,
        },
        size_source=lambda _s, _d: (0, 0),
        clock=iter((0.0, 1.0)).__next__,
        limits=ResourceLimits(300, 40, 20, 5.0),
        autostart=False,
    )
    monitor.sample_now()
    result = monitor.finalize(exit_status=0)
    assert result.passed is False
    assert result.failure_reasons == (
        "process_tree_peak_rss_exceeded", "telemetry_zero_work",
    )

    empty = ContinuousResourceMonitor(
        scratch_root=tmp_path,
        durable_root=tmp_path,
        autostart=False,
    )
    assert empty.finalize(exit_status=0).failure_reasons == ("telemetry_missing",)
    with pytest.raises(ResultExecutionDisabled, match="RUN-01"):
        run_result(result_root=tmp_path / "forbidden")


def test_default_monitor_observes_the_real_current_process_tree_without_optional_packages(tmp_path) -> None:
    monitor = ContinuousResourceMonitor(
        scratch_root=tmp_path,
        durable_root=tmp_path,
        limits=ResourceLimits(2 * 1024**3, 256 * 1024**2, 256 * 1024**2, 30.0),
        autostart=False,
    )
    monitor.sample_now()
    observed = monitor.finalize(exit_status=0)
    assert observed.passed is False
    assert observed.failure_reasons == ("telemetry_zero_work",)
    assert observed.sample_count == 1
    assert observed.process_tree_peak_rss_bytes > 0
    assert observed.max_process_count >= 1
    assert observed.max_thread_count >= 1
    assert observed.start_available_memory_bytes is not None


def test_atomic_scratch_observer_retains_short_lived_high_water(tmp_path) -> None:
    monitor = ContinuousResourceMonitor(
        scratch_root=tmp_path,
        durable_root=tmp_path,
        snapshot_source=lambda: {
            "process_tree_rss_bytes": 1,
            "cpu_seconds": 0.0,
            "process_count": 1,
            "thread_count": 1,
            "available_memory_bytes": FOUR_GIB,
        },
        size_source=lambda _s, _d: (0, 0),
        clock=iter((0.0, 1.0)).__next__,
        limits=ResourceLimits(100, 40, 100, 5.0),
        autostart=False,
    )
    temporary = tmp_path / "short-lived.tmp"
    temporary.write_bytes(b"x" * 50)
    monitor.observe_scratch_path(temporary)
    temporary.unlink()
    monitor.sample_now()
    observed = monitor.finalize(exit_status=0)
    assert observed.scratch_high_water_bytes == 50
    assert "scratch_high_water_exceeded" in observed.failure_reasons
    assert "telemetry_zero_work" in observed.failure_reasons


@pytest.mark.parametrize("bad", (float("nan"), float("inf")))
def test_monitor_rejects_nonfinite_cpu_and_clock_fail_closed(tmp_path, bad) -> None:
    monitor = ContinuousResourceMonitor(
        scratch_root=tmp_path,
        durable_root=tmp_path,
        snapshot_source=lambda: {
            "process_tree_rss_bytes": 1,
            "cpu_seconds": bad,
            "process_count": 1,
            "thread_count": 1,
            "available_memory_bytes": FOUR_GIB,
        },
        size_source=lambda _s, _d: (0, 0),
        clock=iter((0.0, 1.0)).__next__,
        autostart=False,
    )
    monitor.sample_now()
    assert monitor.finalize(exit_status=0).failure_reasons == (
        "telemetry_missing", "telemetry_measurement_failed",
    )

    with pytest.raises(ValueError, match="clock"):
        ContinuousResourceMonitor(
            scratch_root=tmp_path,
            durable_root=tmp_path,
            clock=lambda: bad,
            autostart=False,
        )


def test_process_identity_accumulator_retains_exited_child_cpu_and_io(tmp_path) -> None:
    snapshots = iter((
        {
            "process_tree_rss_bytes": 100, "cpu_seconds": 10.5,
            "process_count": 2, "thread_count": 3, "available_memory_bytes": FOUR_GIB,
            "foreground_io_read_bytes": 100, "foreground_io_write_bytes": 200,
            "process_records": [
                {"identity": "root:1", "pid": os.getpid(), "cpu_seconds": 10.0,
                 "io_read_bytes": 100, "io_write_bytes": 200},
                {"identity": "child:7", "pid": os.getpid() + 10_000, "cpu_seconds": 0.5,
                 "io_read_bytes": 30, "io_write_bytes": 40},
            ],
        },
        {
            "process_tree_rss_bytes": 80, "cpu_seconds": 11.0,
            "process_count": 1, "thread_count": 2, "available_memory_bytes": FOUR_GIB,
            "foreground_io_read_bytes": 150, "foreground_io_write_bytes": 260,
            "process_records": [
                {"identity": "root:1", "pid": os.getpid(), "cpu_seconds": 11.0,
                 "io_read_bytes": 150, "io_write_bytes": 260},
            ],
        },
    ))
    monitor = ContinuousResourceMonitor(
        scratch_root=tmp_path, durable_root=tmp_path,
        snapshot_source=lambda: next(snapshots), size_source=lambda _s, _d: (0, 0),
        clock=iter((0.0, 1.0, 2.0)).__next__, autostart=False,
    )
    monitor.sample_now()
    monitor.sample_now()
    result = monitor.finalize(exit_status=0)
    assert result.cpu_seconds == pytest.approx(1.5)
    assert result.process_tree_io_read_bytes == 80
    assert result.process_tree_io_write_bytes == 100
    assert result.foreground_io_read_bytes == 50
    assert result.foreground_io_write_bytes == 60
