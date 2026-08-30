from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tools.research.experimental_design import (
    DesignValidationError,
    build_schedule,
    validate_schedule,
    write_schedule,
)


def _blocked_request() -> dict[str, object]:
    return {
        "protocol_id": "blocked-arm-protocol-v1",
        "protocol_version": "v1",
        "seed": 918273,
        "randomization_level": "animal",
        "unit": {
            "randomization_level": "animal",
            "units": [
                {"id": "animal-01", "batch": "A"},
                {"id": "animal-02", "batch": "A"},
                {"id": "animal-03", "batch": "A"},
                {"id": "animal-04", "batch": "A"},
                {"id": "animal-05", "batch": "B"},
                {"id": "animal-06", "batch": "B"},
                {"id": "animal-07", "batch": "B"},
                {"id": "animal-08", "batch": "B"},
            ],
        },
        "blocking": {"field": "batch"},
        "stratification": None,
        "sample_structure": {"independent_unit": "animal", "unit_count": 8},
        "factor_design": {
            "kind": "blocked_arms",
            "arms": ["control", "treatment"],
            "ratio": [1, 1],
        },
        "balance_checks": {"maximum_absolute_deviation": 0},
        "outcome_branches": ["positive", "negative", "null", "ambiguous"],
    }


def _factorial_request() -> dict[str, object]:
    return {
        "protocol_id": "factorial-protocol-v1",
        "protocol_version": "v1",
        "seed": 81,
        "randomization_level": "sample",
        "unit": {
            "randomization_level": "sample",
            "units": [
                {"id": "sample-01"},
                {"id": "sample-02"},
                {"id": "sample-03"},
                {"id": "sample-04"},
            ],
        },
        "blocking": None,
        "stratification": None,
        "sample_structure": {"independent_unit": "sample", "unit_count": 4},
        "factor_design": {
            "kind": "full_factorial",
            "factors": {"temperature_C": [20, 40], "catalyst": ["A", "B"]},
            "replicates": 1,
        },
        "balance_checks": {"maximum_absolute_deviation": 0},
        "outcome_branches": ["positive", "negative", "null", "ambiguous"],
    }


def test_seeded_schedule_replays_exactly_and_has_a_stable_hash() -> None:
    request = _blocked_request()

    first = build_schedule(request)
    second = build_schedule(deepcopy(request))

    assert first == second
    assert first["input_hash"]
    assert first["schedule_hash"]
    validate_schedule(first)


def test_blocked_arm_schedule_preserves_unit_and_balance_invariants() -> None:
    schedule = build_schedule(_blocked_request())

    assert {row["unit_id"] for row in schedule["rows"]} == {
        f"animal-{number:02d}" for number in range(1, 9)
    }
    assert schedule["balance"]["maximum_absolute_deviation"] == 0
    for group in schedule["balance"]["groups"]:
        assert group["counts"] == {"control": 2, "treatment": 2}
        assert group["expected_counts"] == {"control": 2.0, "treatment": 2.0}


def test_malformed_or_unsafe_designs_fail_with_explicit_validation_errors() -> None:
    missing_seed = _blocked_request()
    missing_seed.pop("seed")
    with pytest.raises(DesignValidationError, match="seed"):
        build_schedule(missing_seed)

    wrong_level = _blocked_request()
    wrong_level["randomization_level"] = "cell"
    with pytest.raises(DesignValidationError, match="randomization_level"):
        build_schedule(wrong_level)

    oversized_factor = _factorial_request()
    oversized_factor["factor_design"] = {
        "kind": "full_factorial",
        "factors": {"temperature_C": list(range(33))},
        "replicates": 1,
    }
    oversized_factor["unit"] = {
        "randomization_level": "sample",
        "units": [{"id": f"sample-{number}"} for number in range(33)],
    }
    oversized_factor["sample_structure"] = {"independent_unit": "sample", "unit_count": 33}
    with pytest.raises(DesignValidationError, match="exceeding maximum"):
        build_schedule(oversized_factor)


def test_small_full_factorial_writes_reconstructable_json_and_csv(tmp_path: Path) -> None:
    schedule = build_schedule(_factorial_request())
    json_path = tmp_path / "schedule.json"
    csv_path = tmp_path / "schedule.csv"

    write_schedule(schedule, json_path=json_path, csv_path=csv_path)

    assert json.loads(json_path.read_text(encoding="utf-8")) == schedule
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert {(row["temperature_C"], row["catalyst"]) for row in rows} == {
        ("20", "A"),
        ("20", "B"),
        ("40", "A"),
        ("40", "B"),
    }
    assert [int(row["run_order"]) for row in rows] == [1, 2, 3, 4]
