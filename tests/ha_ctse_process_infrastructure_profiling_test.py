from __future__ import annotations

import json
from pathlib import Path

import pytest

from ha_ctse_process.infrastructure_profiling import (
    PROFILE_CATEGORIES,
    InfrastructureProfiler,
)


def test_profile_rows_are_non_overlapping_and_emit_at_configured_updates(tmp_path):
    ticks = iter((1.0, 3.0, 4.0, 9.0, 10.0, 14.0, 20.0, 21.0))
    synchronizations = []
    profiler = InfrastructureProfiler(
        tmp_path,
        2,
        clock=lambda: next(ticks),
        cuda_synchronize=lambda: synchronizations.append("sync"),
    )

    profiler.start("inference", torch_phase=True)
    profiler.stop(torch_phase=True)
    profiler.start("collector_env")
    profiler.stop()
    profiler.finish_update(update=1, total_steps=10)
    assert not (tmp_path / "diagnostics").exists()

    profiler.start("update", torch_phase=True)
    profiler.stop(torch_phase=True)
    profiler.start("metrics")
    profiler.stop()
    profiler.finish_update(update=2, total_steps=20)

    rows = [
        json.loads(line)
        for line in (tmp_path / "diagnostics" / "infrastructure_profile.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert rows == [
        {
            "schema_version": 1,
            "update": 2,
            "total_steps": 20,
            "durations_seconds": {
                "inference": 0.0,
                "collector_env": 0.0,
                "transition_ledger_pack": 0.0,
                "update": 4.0,
                "metrics": 1.0,
                "checkpoint_eval": 0.0,
            },
        }
    ]
    assert set(rows[0]["durations_seconds"]) == set(PROFILE_CATEGORIES)
    assert synchronizations == ["sync", "sync", "sync", "sync"]


def test_disabled_or_invalid_profiler_never_touches_clock_sync_or_disk(tmp_path):
    calls = []
    with pytest.raises(ValueError, match="positive"):
        InfrastructureProfiler(
            tmp_path,
            0,
            clock=lambda: calls.append("clock"),
            cuda_synchronize=lambda: calls.append("sync"),
        )
    assert calls == []
    assert not (tmp_path / "diagnostics").exists()


def test_cuda_sync_is_restricted_to_explicit_torch_phases(tmp_path):
    calls = []
    profiler = InfrastructureProfiler(
        tmp_path,
        1,
        clock=lambda: 1.0,
        cuda_synchronize=lambda: calls.append("sync"),
    )
    for category in PROFILE_CATEGORIES:
        profiler.start(category, torch_phase=category in {"inference", "update"})
        profiler.stop(torch_phase=category in {"inference", "update"})
    assert calls == ["sync", "sync", "sync", "sync"]


def test_diagnostic_path_is_exactly_under_the_supplied_log_directory(tmp_path):
    log_dir = tmp_path / "run-log"
    profiler = InfrastructureProfiler(log_dir, 1, clock=lambda: 1.0)
    profiler.start("metrics")
    profiler.stop()
    profiler.finish_update(update=1, total_steps=1)
    assert (log_dir / "diagnostics" / "infrastructure_profile.jsonl").is_file()


def test_diagnostic_references_are_limited_to_profiler_and_runner_wiring():
    package_root = Path(__file__).resolve().parents[1] / "ha_ctse_process"
    references = {
        path.name
        for path in package_root.glob("*.py")
        if "infrastructure_profile" in path.read_text(encoding="utf-8")
    }
    assert references == {
        "infrastructure_profiling.py",
        "standalone_train_runner.py",
        "standalone_variable_roster_runner.py",
    }
