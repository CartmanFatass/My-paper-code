"""Pure replay-record merging and validation for event commitment evidence."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ha_ctse_process.noncalendar_commitment_testbed import (
    EVENT_JOINT_FACTOR_COUNT,
    REPLAY_COMPONENT_FIELDS,
    REPLAY_EVENT_JOINT_RATIO_FIELDS,
    REPLAY_EXACT_FIELDS,
    REPLAY_JOINT_FIELDS,
    REPLAY_JOINT_RECORD_FIELDS,
    REPLAY_LOG_COMPONENT_ATOL,
    REPLAY_LOG_COMPONENT_FIELDS,
    REPLAY_LOG_COMPONENT_RTOL,
    REPLAY_LOG_RATIO_DRIFT_CAP,
    REPLAY_RECORD_SCHEMA_VERSION,
    REPLAY_STATE_ATOL,
    REPLAY_STATE_FIELDS,
    REPLAY_WORST_RECORD_FIELDS,
)


REPLAY_RECORD_KEYS = frozenset(
    {
        "schema_version", "errors", "likelihood_components", "joints",
        "event_joint_ratio", "log_component_atol", "log_component_rtol",
        "ratio_drift_cap", "state_atol", "failures", "passed",
    }
)
# Relative slack for the record's own internal algebra. The reported numbers
# are float64 selections of float64 quantities, so the equalities below hold
# to a few ulps; this is a rounding allowance, never a tolerance on evidence.
RECORD_CONSISTENCY_RELATIVE = 1e-9
RECORD_CONSISTENCY_ABSOLUTE = 1e-15


def _finite_leaves(record: Any) -> bool:
    """Every numeric leaf of a replay record is finite.

    `nan > tol` and `nan > 0.0` are both false, so a record carrying NaN
    satisfies every ordinary threshold test. Non-finiteness is therefore
    checked explicitly and first, in both the validator and the merge.
    """

    def visit(value: Any, *, key: str = "") -> bool:
        if key == "coordinate":
            return value is None or (
                isinstance(value, list)
                and all(type(index) is int and index >= 0 for index in value)
            )
        if isinstance(value, dict):
            return all(visit(child, key=str(name)) for name, child in value.items())
        if isinstance(value, (list, tuple)):
            return all(visit(child) for child in value)
        if isinstance(value, bool) or value is None or isinstance(value, str):
            return True
        try:
            return math.isfinite(float(value))
        except (TypeError, ValueError):
            return False

    return isinstance(record, dict) and visit(record)


def _record_severity(record: dict[str, Any]) -> float:
    if record["coordinate"] is None:
        return -1.0
    return max(
        float(record["absolute_error"]) / max(float(record["mixed_bound"]), 1e-300),
        float(record["ratio_drift"]) / REPLAY_LOG_RATIO_DRIFT_CAP,
    )


def merge_replay_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Worst-case merge of several replay records into one, factor by factor.

    Used where one cell or one update covers several validated batches. Each
    named error keeps its own maximum; each derived joint keeps the batch
    that produced the largest joint error, so the reported bound is still
    the bound that reported error was tested against, while `excess` takes
    the maximum over every batch. The three assembly numbers move together
    from the batch with the largest `assembly_excess`, so the merged record
    keeps `assembly_excess == assembly_residual - assembly_allowance`.
    Nothing is reduced to a single scalar.

    Merging is fail-closed on non-finiteness. Python's `max(0.0, nan)`
    returns `0.0` while `max(nan, 0.0)` returns `nan`, so a plain maximum
    would launder a NaN batch out of the evidence depending on batch order.
    """

    if not records:
        raise ValueError("replay merge requires at least one record")
    non_finite = [
        index for index, record in enumerate(records) if not _finite_leaves(record)
    ]
    if non_finite:
        raise ValueError(f"replay merge received non-finite records {non_finite}")
    constant_keys = (
        "schema_version", "log_component_atol", "log_component_rtol",
        "ratio_drift_cap", "state_atol",
    )
    if any(
        any(record[key] != records[0][key] for key in constant_keys)
        for record in records[1:]
    ):
        raise ValueError("replay records disagree on schema or numerical constants")
    errors = {
        name: max(float(record["errors"][name]) for record in records)
        for name in records[0]["errors"]
    }
    joints: dict[str, dict[str, float]] = {}
    for name in REPLAY_JOINT_FIELDS:
        worst = max(records, key=lambda record: float(record["joints"][name]["error"]))
        merged = {key: float(value) for key, value in worst["joints"][name].items()}
        merged["excess"] = max(
            float(record["joints"][name]["excess"]) for record in records
        )
        merged["float64_error"] = max(
            float(record["joints"][name]["float64_error"]) for record in records
        )
        assembly = max(
            records, key=lambda record: float(record["joints"][name]["assembly_excess"])
        )
        for key in ("assembly_residual", "assembly_allowance", "assembly_excess"):
            merged[key] = float(assembly["joints"][name][key])
        merged["rows"] = float(
            sum(float(record["joints"][name]["rows"]) for record in records)
        )
        joints[name] = merged
    likelihood_components = {
        name: dict(max(records, key=lambda record: _record_severity(
            record["likelihood_components"][name]
        ))["likelihood_components"][name])
        for name in REPLAY_LOG_COMPONENT_FIELDS
    }
    event_joint_ratio = dict(max(
        records,
        key=lambda record: float(record["event_joint_ratio"]["ratio_drift"]),
    )["event_joint_ratio"])
    failures = sorted(
        {name for record in records for name in record["failures"]}
    )
    return {
        "schema_version": records[0]["schema_version"],
        "errors": errors,
        "likelihood_components": likelihood_components,
        "joints": joints,
        "event_joint_ratio": event_joint_ratio,
        "log_component_atol": records[0]["log_component_atol"],
        "log_component_rtol": records[0]["log_component_rtol"],
        "ratio_drift_cap": records[0]["ratio_drift_cap"],
        "state_atol": records[0]["state_atol"],
        "failures": failures,
        "passed": all(bool(record["passed"]) for record in records),
    }


def _consistent(left: float, right: float) -> bool:
    """`left == right` up to the record's own float64 rounding."""

    return abs(left - right) <= (
        RECORD_CONSISTENCY_ABSOLUTE
        + RECORD_CONSISTENCY_RELATIVE * max(abs(left), abs(right))
    )


def _joint_factor_error_cap(name: str, errors: dict[str, Any], joint: dict[str, Any]) -> float:
    """Largest `component_sum` the recorded per-factor errors can support.

    `component_sum` is a per-row sum of per-factor replay differences, and
    every factor of both joints is covered by a recorded per-factor maximum
    -- the event joint's out-of-support factors only because
    `categorical_support_leak`/`mark_support_leak` force them to be exactly
    zero on both sides. Without this link a record could declare an
    arbitrarily wide `bound` (`component_sum + allowance`) and validate any
    error beneath it.
    """

    if name == "event_joint":
        return float(errors["categorical_component"]) + float(
            EVENT_JOINT_FACTOR_COUNT - 1
        ) * float(errors["mark_component"])
    return float(joint["factor_count"]) * float(errors["primitive_component"])


def _ordered_float32_encoding(value: np.float32) -> int:
    bits = int(value.view(np.uint32))
    return bits ^ (0xFFFFFFFF if bits & 0x80000000 else 0x80000000)


def _recompute_ulp(stored: float, replayed: float) -> tuple[float, int]:
    stored32, replayed32 = np.float32(stored), np.float32(replayed)
    reference = stored32 if abs(float(stored32)) >= abs(float(replayed32)) else replayed32
    direction = np.float32(np.inf if not np.signbit(reference) else -np.inf)
    neighbor = np.nextafter(reference, direction, dtype=np.float32)
    return (
        abs(float(np.float64(neighbor) - np.float64(reference))),
        abs(_ordered_float32_encoding(stored32) - _ordered_float32_encoding(replayed32)),
    )


def _likelihood_record_valid(
    record: Any, *, dimensions: int, empty_allowed: bool
) -> bool:
    if not isinstance(record, dict) or set(record) != set(REPLAY_WORST_RECORD_FIELDS):
        return False
    coordinate = record.get("coordinate")
    if coordinate is None:
        return empty_allowed and all(
            float(record[name]) == 0.0
            for name in (
                "stored_value", "replayed_value", "absolute_error",
                "mixed_bound", "ratio_drift", "float32_ulp_at_max_magnitude",
                "ulp_distance",
            )
        ) and float(record["ratio_cap"]) == REPLAY_LOG_RATIO_DRIFT_CAP
    if not (
        isinstance(coordinate, list)
        and len(coordinate) == dimensions
        and all(type(index) is int and index >= 0 for index in coordinate)
    ):
        return False
    stored = float(record["stored_value"])
    replayed = float(record["replayed_value"])
    absolute_error = abs(replayed - stored)
    mixed_bound = REPLAY_LOG_COMPONENT_ATOL + REPLAY_LOG_COMPONENT_RTOL * max(
        abs(stored), abs(replayed)
    )
    ratio_drift = abs(math.expm1(replayed - stored))
    spacing, distance = _recompute_ulp(stored, replayed)
    return bool(
        _consistent(float(record["absolute_error"]), absolute_error)
        and _consistent(float(record["mixed_bound"]), mixed_bound)
        and _consistent(float(record["ratio_drift"]), ratio_drift)
        and float(record["ratio_cap"]) == REPLAY_LOG_RATIO_DRIFT_CAP
        and float(record["float32_ulp_at_max_magnitude"]) == spacing
        and int(record["ulp_distance"]) == distance
        and absolute_error <= mixed_bound
        and ratio_drift <= REPLAY_LOG_RATIO_DRIFT_CAP
    )


def _replay_record_valid(record: Any, *, event_rows_required: bool = True) -> bool:
    """Fail-closed check of one serialized replay record.

    Re-derives acceptance from the record itself rather than trusting its
    `passed` flag: every numeric leaf must be finite, exact fields must be
    exactly zero, ordinary continuous components must sit at or below the
    registered component tolerance, and each derived joint must sit at or
    below its own compositional bound and match its float64 assembly. A
    record missing any named factor, or any named key of a joint, fails.

    The joint block must also be internally consistent -- `bound` really the
    sum of its own `component_sum` and `allowance`, `excess` dominating
    `error - bound`, the assembly triple self-consistent, and
    `component_sum` no larger than the recorded per-factor errors allow --
    and must have examined a positive number of rows. `event_rows_required`
    is false only for the ordinary source arm, which carries no event head
    and therefore legitimately produces an all-zero event joint.
    """

    if not isinstance(record, dict) or set(record) != REPLAY_RECORD_KEYS:
        return False
    errors = record.get("errors")
    joints = record.get("joints")
    if not isinstance(errors, dict) or not isinstance(joints, dict):
        return False
    if set(errors) != set(
        REPLAY_EXACT_FIELDS + REPLAY_COMPONENT_FIELDS + REPLAY_JOINT_FIELDS
    ):
        return False
    if set(joints) != set(REPLAY_JOINT_FIELDS):
        return False
    if any(
        not isinstance(joints[name], dict)
        or set(joints[name]) != set(REPLAY_JOINT_RECORD_FIELDS)
        for name in REPLAY_JOINT_FIELDS
    ):
        return False
    try:
        if not _finite_leaves(record):
            return False
    except (TypeError, ValueError):
        return False
    if (
        record.get("schema_version") != REPLAY_RECORD_SCHEMA_VERSION
        or float(record.get("log_component_atol", float("nan"))) != REPLAY_LOG_COMPONENT_ATOL
        or float(record.get("log_component_rtol", float("nan"))) != REPLAY_LOG_COMPONENT_RTOL
        or float(record.get("ratio_drift_cap", float("nan"))) != REPLAY_LOG_RATIO_DRIFT_CAP
        or float(record.get("state_atol", float("nan"))) != REPLAY_STATE_ATOL
    ):
        return False
    if record.get("passed") is not True or record.get("failures"):
        return False
    if any(float(errors[name]) != 0.0 for name in REPLAY_EXACT_FIELDS):
        return False
    if any(not float(errors[name]) <= REPLAY_STATE_ATOL for name in REPLAY_STATE_FIELDS):
        return False
    likelihood_components = record.get("likelihood_components")
    if not isinstance(likelihood_components, dict) or set(likelihood_components) != set(
        REPLAY_LOG_COMPONENT_FIELDS
    ):
        return False
    if not _likelihood_record_valid(
        likelihood_components["primitive_component"], dimensions=3,
        empty_allowed=False,
    ):
        return False
    for name, dimensions in (("categorical_component", 3), ("mark_component", 4)):
        if not _likelihood_record_valid(
            likelihood_components[name], dimensions=dimensions,
            empty_allowed=not event_rows_required,
        ):
            return False
    event_ratio = record.get("event_joint_ratio")
    if not isinstance(event_ratio, dict) or set(event_ratio) != set(
        REPLAY_EVENT_JOINT_RATIO_FIELDS
    ):
        return False
    coordinate = event_ratio.get("coordinate")
    if coordinate is None:
        if event_rows_required or any(
            float(event_ratio[name]) != 0.0
            for name in ("stored_value", "replayed_value", "ratio_drift")
        ):
            return False
    elif not (
        isinstance(coordinate, list) and len(coordinate) == 3
        and all(type(index) is int and index >= 0 for index in coordinate)
    ):
        return False
    else:
        recomputed_ratio = abs(math.expm1(
            float(event_ratio["replayed_value"]) - float(event_ratio["stored_value"])
        ))
        if not (
            _consistent(float(event_ratio["ratio_drift"]), recomputed_ratio)
            and float(event_ratio["ratio_cap"]) == REPLAY_LOG_RATIO_DRIFT_CAP
            and recomputed_ratio <= REPLAY_LOG_RATIO_DRIFT_CAP
        ):
            return False
    if coordinate is None and float(event_ratio["ratio_cap"]) != REPLAY_LOG_RATIO_DRIFT_CAP:
        return False
    for name in REPLAY_JOINT_FIELDS:
        joint = {key: float(value) for key, value in joints[name].items()}
        if any(
            joint[key] < 0.0
            for key in (
                "error", "component_sum", "allowance", "bound", "factor_count",
                "float64_error", "assembly_residual", "assembly_allowance",
                "rows",
            )
        ):
            return False
        if not joint["excess"] <= 0.0 or not joint["assembly_excess"] <= 0.0:
            return False
        if not float(errors[name]) <= joint["bound"]:
            return False
        if not _consistent(joint["bound"], joint["component_sum"] + joint["allowance"]):
            return False
        # `excess` is the per-row maximum of `error - bound` while `error`
        # and `bound` are read at the largest-error row, so it dominates
        # rather than equals their difference.
        if joint["excess"] < joint["error"] - joint["bound"] - (
            RECORD_CONSISTENCY_ABSOLUTE
            + RECORD_CONSISTENCY_RELATIVE * abs(joint["bound"])
        ):
            return False
        if not _consistent(
            joint["assembly_excess"],
            joint["assembly_residual"] - joint["assembly_allowance"],
        ):
            return False
        cap = _joint_factor_error_cap(name, errors, joint)
        if joint["component_sum"] > cap + (
            RECORD_CONSISTENCY_ABSOLUTE + RECORD_CONSISTENCY_RELATIVE * abs(cap)
        ):
            return False
        if joint["rows"] <= 0.0:
            # An all-zero joint proves nothing was examined. The one lawful
            # case is the event joint of an arm with no event head, which
            # must then be all-zero rather than merely row-less.
            if name != "event_joint" or event_rows_required:
                return False
            if any(value != 0.0 for value in joint.values()):
                return False
        elif name == "event_joint" and joint["factor_count"] != float(
            EVENT_JOINT_FACTOR_COUNT
        ):
            return False
    return True
