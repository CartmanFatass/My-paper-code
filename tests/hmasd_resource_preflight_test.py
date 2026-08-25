from __future__ import annotations

import json
from pathlib import Path

from scripts import hmasd_resource_preflight as preflight


def test_capture_is_observation_only_and_does_not_require_an_estimate(tmp_path: Path) -> None:
    output = tmp_path / "host-snapshot.json"

    assert preflight.main(["capture", "--out", str(output)]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert "estimate" not in payload
    assert payload["cpu"]["logical_processors"] > 0
    assert payload["memory"]["total_bytes"] > 0
    assert payload["memory"]["available_bytes"] >= 0


def test_assess_normalizes_cgroup_bytes_and_applies_reserve_formula() -> None:
    snapshot = {
        "cpu": {"logical_processors": 8},
        "memory": {
            "total_bytes": 16 * 1024**3,
            "available_bytes": 12 * 1024**3,
            "cgroup_memory_max_bytes": 10 * 1024**3,
            "cgroup_memory_current_bytes": 2 * 1024**3,
        },
    }

    assessed = preflight.assess_snapshot(
        snapshot,
        direction_id="direction",
        run_id="run",
        workers=4,
        threads_per_worker=2,
        estimated_wall_seconds=7200,
        estimated_peak_gib=4.0,
        basis="fixture",
    )

    assert assessed["effective_limit_gib"] == 10.0
    assert assessed["cgroup_headroom_gib"] == 8.0
    assert assessed["effective_available_gib"] == 8.0
    assert assessed["reserve_gib"] == 4.0
    assert assessed["usable_gib"] == 4.0
    assert assessed["adjusted_peak_gib"] == 5.0
    assert assessed["memory_safe"] is False


def test_literal_cgroup_max_is_unbounded_and_minimum_reserve_is_four_gib() -> None:
    snapshot = {
        "cpu": {"logical_processors": 2},
        "memory": {
            "total_bytes": 8 * 1024**3,
            "available_bytes": 7 * 1024**3,
            "cgroup_memory_max_bytes": None,
            "cgroup_memory_current_bytes": None,
            "cgroup_memory_max_raw": "max",
        },
    }

    assessed = preflight.assess_snapshot(
        snapshot,
        direction_id="direction",
        run_id="run",
        workers=1,
        threads_per_worker=1,
        estimated_wall_seconds=1,
        estimated_peak_gib=2.4,
        basis="fixture",
    )

    assert assessed["effective_limit_gib"] == 8.0
    assert assessed["cgroup_headroom_gib"] is None
    assert assessed["effective_available_gib"] == 7.0
    assert assessed["reserve_gib"] == 4.0
    assert assessed["adjusted_peak_gib"] == 3.0
    assert assessed["memory_safe"] is True


def test_assess_rejects_missing_or_non_positive_estimates() -> None:
    snapshot = {
        "cpu": {"logical_processors": 2},
        "memory": {
            "total_bytes": 16 * 1024**3,
            "available_bytes": 16 * 1024**3,
            "cgroup_memory_max_bytes": None,
            "cgroup_memory_current_bytes": None,
        },
    }

    for wall, peak in ((None, 1.0), (0, 1.0), (1, None), (1, 0.0)):
        try:
            preflight.assess_snapshot(
                snapshot,
                direction_id="direction",
                run_id="run",
                workers=1,
                threads_per_worker=1,
                estimated_wall_seconds=wall,
                estimated_peak_gib=peak,
                basis="fixture",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("invalid estimates must be refused")


def test_finite_cgroup_limit_without_current_usage_fails_closed() -> None:
    snapshot = {
        "cpu": {"logical_processors": 8},
        "memory": {
            "total_bytes": 32 * 1024**3,
            "available_bytes": 24 * 1024**3,
            "cgroup_memory_max_raw": str(16 * 1024**3),
            "cgroup_memory_max_bytes": 16 * 1024**3,
            "cgroup_memory_current_raw": None,
            "cgroup_memory_current_bytes": None,
        },
    }

    try:
        preflight.assess_snapshot(
            snapshot,
            direction_id="direction",
            run_id="run",
            workers=1,
            threads_per_worker=1,
            estimated_wall_seconds=60,
            estimated_peak_gib=0.01,
            basis="fixture",
        )
    except ValueError as exc:
        assert "cgroup memory.current" in str(exc)
    else:
        raise AssertionError("bounded cgroup without observed current usage must be refused")
