from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.preflight import (
    PreflightError,
    preflight_run,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.resources import (
    ContinuousResourceMonitor,
    ResourceLimits,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.runner import (
    A_PILOT_PERFORMANCE_DISPOSITION,
    RUN_01_PERFORMANCE_DISPOSITION,
    ResultExecutionDisabled,
    preflight_only,
    run_result,
)


FOUR_GIB = 4 * 1024**3


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
         "available_memory_bytes": FOUR_GIB},
        {"process_tree_rss_bytes": 250, "cpu_seconds": 2.5, "process_count": 2, "thread_count": 5,
         "available_memory_bytes": FOUR_GIB - 1},
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
    assert monitor.finalize(exit_status=0).failure_reasons == ("telemetry_missing",)

    with pytest.raises(ValueError, match="clock"):
        ContinuousResourceMonitor(
            scratch_root=tmp_path,
            durable_root=tmp_path,
            clock=lambda: bad,
            autostart=False,
        )
