"""Deterministic, bounded experimental schedule construction.

This is a minimal adaptation of the design principles in K-Dense Inc.'s
``skills/experimental-design/scripts/randomization.py`` and
``skills/experimental-design/scripts/doe_designs.py`` at commit
``f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f``.  It intentionally uses only the
Python standard library: its bounded blocked-arm and full-factorial operations
do not warrant optional NumPy, pandas, or pyDOE3 activation.

MIT License

Copyright (c) 2025 K-Dense Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

MAX_UNITS = 10_000
MAX_ARMS = 16
MAX_FACTORS = 12
MAX_LEVELS_PER_FACTOR = 32
MAX_FACTORIAL_RUNS = 4_096

_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))


class DesignValidationError(ValueError):
    """Raised when a frozen experimental-design request is invalid or unsafe."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _required_mapping(request: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = request.get(name)
    if not isinstance(value, Mapping):
        raise DesignValidationError(f"{name} must be an object")
    return value


def _nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DesignValidationError(f"{name} must be a non-empty string")
    return value


def _seed(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DesignValidationError("seed must be a non-negative integer; global RNG is never used")
    return value


def _unique_strings(values: Any, name: str, *, maximum: int | None = None) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        raise DesignValidationError(f"{name} must be a non-empty list of strings")
    result = [_nonempty_string(value, f"{name} entry") for value in values]
    if len(set(result)) != len(result):
        raise DesignValidationError(f"{name} must not contain duplicates")
    if maximum is not None and len(result) > maximum:
        raise DesignValidationError(f"{name} has {len(result)} entries, exceeding maximum of {maximum}")
    return result


def _validate_unit(request: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    unit = _required_mapping(request, "unit")
    unit_level = _nonempty_string(unit.get("randomization_level"), "unit.randomization_level")
    randomization_level = _nonempty_string(
        request.get("randomization_level"), "randomization_level"
    )
    if unit_level != randomization_level:
        raise DesignValidationError(
            "randomization_level must exactly match unit.randomization_level; "
            "otherwise the schedule could pseudoreplicate units"
        )
    units = unit.get("units")
    if not isinstance(units, Sequence) or isinstance(units, (str, bytes)) or not units:
        raise DesignValidationError("unit.units must be a non-empty list")
    if len(units) > MAX_UNITS:
        raise DesignValidationError(f"unit.units has {len(units)} entries, exceeding maximum of {MAX_UNITS}")

    normalized: list[dict[str, Any]] = []
    unit_ids: set[str] = set()
    for position, raw_unit in enumerate(units, start=1):
        if not isinstance(raw_unit, Mapping):
            raise DesignValidationError(f"unit.units[{position}] must be an object")
        unit_id = _nonempty_string(raw_unit.get("id"), f"unit.units[{position}].id")
        if unit_id in unit_ids:
            raise DesignValidationError("unit.units ids must be unique at the randomization level")
        unit_ids.add(unit_id)
        normalized.append(dict(raw_unit))
    return randomization_level, normalized


def _validate_grouping(
    request: Mapping[str, Any], units: Sequence[Mapping[str, Any]], name: str
) -> str | None:
    grouping = request.get(name)
    if grouping is None:
        return None
    if not isinstance(grouping, Mapping):
        raise DesignValidationError(f"{name} must be null or an object with field")
    field = _nonempty_string(grouping.get("field"), f"{name}.field")
    for position, unit in enumerate(units, start=1):
        if field not in unit:
            raise DesignValidationError(f"unit.units[{position}] is missing {name} field {field!r}")
        if not isinstance(unit[field], _JSON_SCALAR_TYPES):
            raise DesignValidationError(f"unit.units[{position}].{field} must be a JSON scalar")
    return field


def _validate_common(request: Mapping[str, Any]) -> tuple[int, str, list[dict[str, Any]], str | None, str | None]:
    _nonempty_string(request.get("protocol_id"), "protocol_id")
    _nonempty_string(request.get("protocol_version"), "protocol_version")
    seed = _seed(request.get("seed"))
    randomization_level, units = _validate_unit(request)

    sample_structure = _required_mapping(request, "sample_structure")
    if _nonempty_string(sample_structure.get("independent_unit"), "sample_structure.independent_unit") != randomization_level:
        raise DesignValidationError(
            "sample_structure.independent_unit must match randomization_level"
        )
    if sample_structure.get("unit_count") != len(units):
        raise DesignValidationError("sample_structure.unit_count must equal len(unit.units)")

    _unique_strings(request.get("outcome_branches"), "outcome_branches")
    return seed, randomization_level, units, _validate_grouping(request, units, "blocking"), _validate_grouping(request, units, "stratification")


def _validate_arms(design: Mapping[str, Any]) -> tuple[list[str], list[int]]:
    arms = _unique_strings(design.get("arms"), "factor_design.arms", maximum=MAX_ARMS)
    raw_ratio = design.get("ratio")
    if not isinstance(raw_ratio, Sequence) or isinstance(raw_ratio, (str, bytes)) or len(raw_ratio) != len(arms):
        raise DesignValidationError("factor_design.ratio must have one positive integer per arm")
    ratio: list[int] = []
    for value in raw_ratio:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise DesignValidationError("factor_design.ratio must have one positive integer per arm")
        ratio.append(value)
    if sum(ratio) > MAX_UNITS:
        raise DesignValidationError(
            "factor_design.ratio total exceeds the maximum safe allocation block size "
            f"of {MAX_UNITS}"
        )
    return arms, ratio


def _group_key(unit: Mapping[str, Any], block_field: str | None, stratum_field: str | None) -> tuple[Any, ...]:
    return tuple(unit[field] for field in (block_field, stratum_field) if field is not None)


def _balance_summary(
    rows: Sequence[Mapping[str, Any]], group_fields: Sequence[str], arms: Sequence[str], ratio: Sequence[int]
) -> dict[str, Any]:
    grouped: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[tuple(row[field] for field in group_fields)][str(row["arm"])] += 1
    ratio_total = sum(ratio)
    groups: list[dict[str, Any]] = []
    maximum_deviation = 0.0
    for key, counts in grouped.items():
        total = sum(counts.values())
        expected = {arm: total * weight / ratio_total for arm, weight in zip(arms, ratio)}
        deviations = {arm: abs(counts[arm] - expected[arm]) for arm in arms}
        maximum_deviation = max(maximum_deviation, *deviations.values())
        groups.append(
            {
                "group": dict(zip(group_fields, key)),
                "counts": {arm: counts[arm] for arm in arms},
                "expected_counts": expected,
                "maximum_absolute_deviation": max(deviations.values()),
            }
        )
    return {"groups": groups, "maximum_absolute_deviation": maximum_deviation}


def _build_blocked_arms(request: Mapping[str, Any]) -> dict[str, Any]:
    seed, randomization_level, units, block_field, stratum_field = _validate_common(request)
    design = _required_mapping(request, "factor_design")
    if design.get("kind") != "blocked_arms":
        raise DesignValidationError("factor_design.kind must be 'blocked_arms'")
    arms, ratio = _validate_arms(design)
    checks = _required_mapping(request, "balance_checks")
    tolerance = checks.get("maximum_absolute_deviation")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or tolerance < 0:
        raise DesignValidationError("balance_checks.maximum_absolute_deviation must be a non-negative number")

    rng = random.Random(seed)
    template = [arm for arm, weight in zip(arms, ratio) for _ in range(weight)]
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        grouped[_group_key(unit, block_field, stratum_field)].append(unit)

    rows: list[dict[str, Any]] = []
    group_fields = [field for field in (block_field, stratum_field) if field is not None]
    for group_units in grouped.values():
        assignments: list[str] = []
        while len(assignments) < len(group_units):
            block = template.copy()
            rng.shuffle(block)
            assignments.extend(block)
        for unit, arm in zip(group_units, assignments):
            row = {"schedule_index": len(rows) + 1, "unit_id": unit["id"], "arm": arm}
            row.update({field: unit[field] for field in group_fields})
            rows.append(row)

    balance = _balance_summary(rows, group_fields, arms, ratio)
    if balance["maximum_absolute_deviation"] > tolerance:
        raise DesignValidationError(
            "balance check failed: maximum absolute deviation "
            f"{balance['maximum_absolute_deviation']} exceeds declared tolerance {tolerance}"
        )
    return {
        "artifact_type": "hmasd.experimental_design.schedule.v1",
        "protocol_id": request["protocol_id"],
        "protocol_version": request["protocol_version"],
        "seed": seed,
        "randomization_level": randomization_level,
        "design_kind": "blocked_arms",
        "factor_design": {"kind": "blocked_arms", "arms": arms, "ratio": ratio},
        "input_hash": _sha256(request),
        "balance": balance,
        "rows": rows,
    }


def _validate_factors(design: Mapping[str, Any]) -> tuple[list[str], list[list[Any]], int]:
    factors = design.get("factors")
    if not isinstance(factors, Mapping) or not factors:
        raise DesignValidationError("factor_design.factors must be a non-empty object")
    if len(factors) > MAX_FACTORS:
        raise DesignValidationError(
            f"factor_design.factors has {len(factors)} entries, exceeding maximum of {MAX_FACTORS}"
        )
    names: list[str] = []
    levels: list[list[Any]] = []
    for name, raw_levels in factors.items():
        names.append(_nonempty_string(name, "factor_design factor name"))
        if not isinstance(raw_levels, Sequence) or isinstance(raw_levels, (str, bytes)) or not raw_levels:
            raise DesignValidationError(f"factor {name!r} levels must be a non-empty list")
        if len(raw_levels) > MAX_LEVELS_PER_FACTOR:
            raise DesignValidationError(
                f"factor {name!r} has {len(raw_levels)} levels, exceeding maximum of {MAX_LEVELS_PER_FACTOR}"
            )
        if not all(isinstance(level, _JSON_SCALAR_TYPES) for level in raw_levels):
            raise DesignValidationError(f"factor {name!r} levels must be JSON scalars")
        canonical_levels = [_canonical_json(level) for level in raw_levels]
        if len(set(canonical_levels)) != len(canonical_levels):
            raise DesignValidationError(f"factor {name!r} levels must not contain duplicates")
        levels.append(list(raw_levels))
    replicates = design.get("replicates")
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates <= 0:
        raise DesignValidationError("factor_design.replicates must be a positive integer")
    runs = replicates
    for factor_levels in levels:
        runs *= len(factor_levels)
        if runs > MAX_FACTORIAL_RUNS:
            raise DesignValidationError(
                f"full factorial requires {runs} runs, exceeding maximum of {MAX_FACTORIAL_RUNS}"
            )
    return names, levels, replicates


def _build_full_factorial(request: Mapping[str, Any]) -> dict[str, Any]:
    seed, randomization_level, units, block_field, stratum_field = _validate_common(request)
    if block_field is not None or stratum_field is not None:
        raise DesignValidationError("full_factorial supports only null blocking and stratification")
    design = _required_mapping(request, "factor_design")
    if design.get("kind") != "full_factorial":
        raise DesignValidationError("factor_design.kind must be 'full_factorial'")
    names, levels, replicates = _validate_factors(design)
    product_rows = list(itertools.product(*levels))
    rows_without_units = [dict(zip(names, values)) for values in product_rows for _ in range(replicates)]
    if len(rows_without_units) != len(units):
        raise DesignValidationError(
            "full_factorial run count must equal sample_structure.unit_count so every run has one independent randomized unit"
        )

    rng = random.Random(seed)
    rng.shuffle(rows_without_units)
    rows = [
        {"run_order": index, "unit_id": units[index - 1]["id"], **factors}
        for index, factors in enumerate(rows_without_units, start=1)
    ]
    return {
        "artifact_type": "hmasd.experimental_design.schedule.v1",
        "protocol_id": request["protocol_id"],
        "protocol_version": request["protocol_version"],
        "seed": seed,
        "randomization_level": randomization_level,
        "design_kind": "full_factorial",
        "factor_design": {
            "kind": "full_factorial",
            "factors": {name: factor_levels for name, factor_levels in zip(names, levels)},
            "replicates": replicates,
        },
        "input_hash": _sha256(request),
        "balance": None,
        "rows": rows,
    }


def build_schedule(request: object) -> dict[str, Any]:
    """Validate a frozen request and return its deterministic schedule artifact.

    The supplied seed is consumed by a private ``random.Random`` instance only.
    This function neither launches an experiment nor interprets the schedule or
    any outcome.
    """
    if not isinstance(request, Mapping):
        raise DesignValidationError("request must be an object")
    frozen_request = cast(Mapping[str, Any], request)
    design = _required_mapping(frozen_request, "factor_design")
    kind = design.get("kind")
    if kind == "blocked_arms":
        artifact = _build_blocked_arms(frozen_request)
    elif kind == "full_factorial":
        artifact = _build_full_factorial(frozen_request)
    else:
        raise DesignValidationError("factor_design.kind must be 'blocked_arms' or 'full_factorial'")
    artifact["schedule_hash"] = _sha256(artifact)
    return artifact


def validate_schedule(artifact: object) -> None:
    """Raise ``DesignValidationError`` unless an emitted schedule is intact."""
    if not isinstance(artifact, Mapping):
        raise DesignValidationError("schedule artifact must be an object")
    schedule = cast(Mapping[str, Any], artifact)
    expected_hash = schedule.get("schedule_hash")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise DesignValidationError("schedule artifact is missing a SHA-256 schedule_hash")
    unsigned = dict(schedule)
    unsigned.pop("schedule_hash", None)
    actual_hash = _sha256(unsigned)
    if actual_hash != expected_hash:
        raise DesignValidationError("schedule_hash does not match schedule contents")
    rows = schedule.get("rows")
    if not isinstance(rows, list) or not rows:
        raise DesignValidationError("schedule artifact rows must be a non-empty list")
    unit_ids = [row.get("unit_id") for row in rows if isinstance(row, Mapping)]
    if len(unit_ids) != len(rows) or len(set(unit_ids)) != len(unit_ids):
        raise DesignValidationError("schedule artifact must contain one unique unit_id per run")


def _csv_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    first = list(rows[0])
    remaining = sorted({key for row in rows for key in row}.difference(first))
    return first + remaining


def write_schedule(
    artifact: Mapping[str, Any], *, json_path: str | Path | None = None, csv_path: str | Path | None = None
) -> None:
    """Write requested JSON and/or CSV schedule artifacts after integrity validation."""
    validate_schedule(artifact)
    if json_path is None and csv_path is None:
        raise DesignValidationError("at least one of json_path or csv_path is required")
    if json_path is not None:
        Path(json_path).write_text(_canonical_json(artifact) + "\n", encoding="utf-8")
    if csv_path is not None:
        rows = artifact["rows"]
        assert isinstance(rows, list)  # Established by validate_schedule above.
        columns = _csv_columns(rows)
        with Path(csv_path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
