"""Fail-closed complete-panel empirical analyzer for RCLE-TBCFV r04.

This surface accepts only the exact twenty technically completed empirical
block aggregates bound to one immutable production identity.  Synthetic and
fixture records are rejected before bindings or aggregate values are read.
The mathematical bound and branch reducer is shared with :mod:`inference`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence

from .config import LEARNED_PACKAGES, SCIENCE_REVISION, SCRIPTED_PACKAGES
from .empirical_artifacts import (
    ANALYZER_OUTPUT_SCHEMA,
    BLOCK_COUNT,
    BLOCK_COUNTS,
    EMPIRICAL_OBJECT,
    REGISTERED_TAIL_COUNT,
    REGISTERED_TAIL_NAMES,
    EmpiricalArtifactError,
    EmpiricalBindings,
)
from .inference import (
    BRANCHES,
    DEGREES_OF_FREEDOM,
    DIRECT_VALUE_VARIABLES,
    GAMMA_GLOBAL,
    HELDOUT_CELLS,
    MECHANISM_VARIABLES,
    PREREQUISITE_VARIABLES,
    TAIL_COUNT,
    TRAINING_CELLS,
    Bound,
    LowerBound,
    compute_registered_bounds,
    reduce_complete_bounds,
)


EMPIRICAL_ANALYZER_INPUT_SCHEMA = "RCLE_TBCFV_R04_EMPIRICAL_ANALYZER_INPUT_V1"
EMPIRICAL_RECORD_CLASS = "EMPIRICAL_COMPLETE_BLOCK"
SYNTHETIC_TEST_ONLY = "SYNTHETIC_TEST_ONLY"
TRAINING_EPISODES_PER_CELL = 800 * 8
HELDOUT_EPISODES_PER_CELL = 2_048
_HEX = re.compile(r"[0-9a-f]{64}")

assert BLOCK_COUNT == 20
assert TAIL_COUNT == REGISTERED_TAIL_COUNT == 72


class EmpiricalInferenceError(ValueError):
    """The complete empirical analyzer admission contract was not satisfied."""


@dataclass(frozen=True)
class EmpiricalAnalysisOutcome:
    admitted_empirical: bool
    branch: str
    scientific_branch: str | None
    schema: str
    science_revision: str
    empirical_object: str
    block_count: int
    gamma_global: float
    degrees_of_freedom: int
    registered_tail_count: int
    bounds: Mapping[str, Mapping[str, Bound | LowerBound]]
    gates: Mapping[str, bool]
    predicates: Mapping[str, Any]
    analyzer_payload: bytes | None
    failure_reason: str | None


def _invalid(reason: str) -> EmpiricalAnalysisOutcome:
    return EmpiricalAnalysisOutcome(
        admitted_empirical=False,
        branch=BRANCHES[0],
        scientific_branch=None,
        schema=ANALYZER_OUTPUT_SCHEMA,
        science_revision=SCIENCE_REVISION,
        empirical_object=EMPIRICAL_OBJECT,
        block_count=BLOCK_COUNT,
        gamma_global=GAMMA_GLOBAL,
        degrees_of_freedom=DEGREES_OF_FREEDOM,
        registered_tail_count=REGISTERED_TAIL_COUNT,
        bounds={},
        gates={},
        predicates={},
        analyzer_payload=None,
        failure_reason=reason,
    )


def _exact_mapping(value: object, keys: Sequence[str], location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise EmpiricalInferenceError(f"{location} inventory differs from the frozen schema")
    return value


def _finite(value: object, location: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EmpiricalInferenceError(f"{location} must be a finite real number")
    converted = float(value)
    if not math.isfinite(converted):
        raise EmpiricalInferenceError(f"{location} must be finite")
    return converted


def _exact_count_mapping(
    value: object, keys: Sequence[str], expected: int, location: str
) -> None:
    mapping = _exact_mapping(value, keys, location)
    if any(
        isinstance(mapping[key], bool)
        or not isinstance(mapping[key], int)
        or mapping[key] != expected
        for key in keys
    ):
        raise EmpiricalInferenceError(f"{location} counts differ from the complete panel")


def _validate_complete_inventories(record: Mapping[str, object], block_index: int) -> None:
    if record["learned_arms"] != list(LEARNED_PACKAGES):
        raise EmpiricalInferenceError(f"block {block_index} learned-arm inventory differs")
    if record["scripted_packages"] != list(SCRIPTED_PACKAGES):
        raise EmpiricalInferenceError(f"block {block_index} scripted-package inventory differs")
    if record["training_cells"] != list(TRAINING_CELLS):
        raise EmpiricalInferenceError(f"block {block_index} training-cell inventory differs")
    if record["heldout_cells"] != list(HELDOUT_CELLS):
        raise EmpiricalInferenceError(f"block {block_index} heldout-cell inventory differs")
    _exact_count_mapping(record["updates_completed"], LEARNED_PACKAGES, 800, "updates_completed")

    training = _exact_mapping(
        record["training_cell_episodes"], LEARNED_PACKAGES, "training_cell_episodes"
    )
    learned = _exact_mapping(
        record["learned_heldout_episodes"], LEARNED_PACKAGES, "learned_heldout_episodes"
    )
    scripted = _exact_mapping(
        record["scripted_heldout_episodes"], SCRIPTED_PACKAGES, "scripted_heldout_episodes"
    )
    for arm in LEARNED_PACKAGES:
        _exact_count_mapping(
            training[arm], TRAINING_CELLS, TRAINING_EPISODES_PER_CELL, f"training.{arm}"
        )
        _exact_count_mapping(
            learned[arm], HELDOUT_CELLS, HELDOUT_EPISODES_PER_CELL, f"heldout.{arm}"
        )
    for package in SCRIPTED_PACKAGES:
        _exact_count_mapping(
            scripted[package],
            HELDOUT_CELLS,
            HELDOUT_EPISODES_PER_CELL,
            f"scripted.{package}",
        )

    counts = _exact_mapping(record["counts"], tuple(BLOCK_COUNTS), "block counts")
    if dict(counts) != BLOCK_COUNTS:
        raise EmpiricalInferenceError(f"block {block_index} exact work counts differ")


def _read_aggregates(
    value: object, block_index: int
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    groups = _exact_mapping(
        value, ("prerequisite", "direct_value", "mechanism"), f"block {block_index} aggregates"
    )
    result: list[dict[str, float]] = []
    for group_name, names in (
        ("prerequisite", PREREQUISITE_VARIABLES),
        ("direct_value", DIRECT_VALUE_VARIABLES),
        ("mechanism", MECHANISM_VARIABLES),
    ):
        group = _exact_mapping(groups[group_name], names, f"block {block_index}.{group_name}")
        result.append(
            {
                name: _finite(group[name], f"block {block_index}.{group_name}.{name}")
                for name in names
            }
        )
    return result[0], result[1], result[2]


_RECORD_KEYS = (
    "schema",
    "science_revision",
    "empirical_object",
    "record_class",
    "empirical_record",
    "fixture_only",
    "synthetic_test_only",
    "block_index",
    "block_complete_sha256",
    "aggregate_sha256",
    "bindings",
    "technical_complete",
    "complete_marker_bound",
    "treatment_fidelity",
    "analytic_containment",
    "selection_or_adaptation",
    "evaluation_adaptation",
    "forbidden_information",
    "registered_coordinate",
    "learned_arms",
    "scripted_packages",
    "training_cells",
    "heldout_cells",
    "updates_completed",
    "training_cell_episodes",
    "learned_heldout_episodes",
    "scripted_heldout_episodes",
    "counts",
    "aggregates",
)


def _admit_records(
    records: Sequence[Mapping[str, object]], expected_bindings: EmpiricalBindings
) -> tuple[dict[str, list[float]], dict[str, list[float]], dict[str, list[float]]]:
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise EmpiricalInferenceError("empirical records must be a sequence")
    if len(records) != BLOCK_COUNT:
        raise EmpiricalInferenceError("exactly twenty complete empirical blocks are required")
    if not isinstance(expected_bindings, EmpiricalBindings):
        raise EmpiricalInferenceError("expected empirical bindings are required")
    expected_bindings.validate()
    binding_mapping = asdict(expected_bindings)

    accumulated = (
        {name: [] for name in PREREQUISITE_VARIABLES},
        {name: [] for name in DIRECT_VALUE_VARIABLES},
        {name: [] for name in MECHANISM_VARIABLES},
    )
    seen_blocks: set[int] = set()
    seen_markers: set[str] = set()
    for position, record in enumerate(records):
        if not isinstance(record, Mapping) or set(record) != set(_RECORD_KEYS):
            raise EmpiricalInferenceError(f"record {position} schema is incomplete or extra")

        # This fence deliberately precedes access to binding or aggregate values.
        if (
            record["record_class"] != EMPIRICAL_RECORD_CLASS
            or record["empirical_record"] is not True
            or record["fixture_only"] is not False
            or record["synthetic_test_only"] is not False
        ):
            raise EmpiricalInferenceError("fixture or synthetic record cannot enter empirical analysis")

        block_index = record["block_index"]
        if (
            isinstance(block_index, bool)
            or not isinstance(block_index, int)
            or not 0 <= block_index < BLOCK_COUNT
            or block_index in seen_blocks
        ):
            raise EmpiricalInferenceError("empirical block indices must be unique and exactly 0..19")
        seen_blocks.add(block_index)
        if (
            record["schema"] != EMPIRICAL_ANALYZER_INPUT_SCHEMA
            or record["science_revision"] != SCIENCE_REVISION
            or record["empirical_object"] != EMPIRICAL_OBJECT
            or record["bindings"] != binding_mapping
        ):
            raise EmpiricalInferenceError(f"block {block_index} revision or immutable binding differs")
        marker = record["block_complete_sha256"]
        aggregate_digest = record["aggregate_sha256"]
        if (
            not isinstance(marker, str)
            or not _HEX.fullmatch(marker)
            or marker in seen_markers
            or not isinstance(aggregate_digest, str)
            or not _HEX.fullmatch(aggregate_digest)
        ):
            raise EmpiricalInferenceError(f"block {block_index} completion/aggregate digest is invalid")
        seen_markers.add(marker)
        if (
            record["technical_complete"] is not True
            or record["complete_marker_bound"] is not True
            or record["treatment_fidelity"] is not True
            or record["analytic_containment"] is not True
            or record["selection_or_adaptation"] is not False
            or record["evaluation_adaptation"] is not False
            or record["forbidden_information"] is not False
            or record["registered_coordinate"] is not True
        ):
            raise EmpiricalInferenceError(f"block {block_index} technical or scientific guard failed")
        _validate_complete_inventories(record, block_index)
        prerequisite, direct, mechanism = _read_aggregates(record["aggregates"], block_index)
        actual_aggregate_digest = hashlib.sha256(
            _canonical_json(record["aggregates"])
        ).hexdigest()
        if aggregate_digest != actual_aggregate_digest:
            raise EmpiricalInferenceError(f"block {block_index} aggregate digest differs")
        for name, aggregate in prerequisite.items():
            accumulated[0][name].append(aggregate)
        for name, aggregate in direct.items():
            accumulated[1][name].append(aggregate)
        for name, aggregate in mechanism.items():
            accumulated[2][name].append(aggregate)
    if seen_blocks != set(range(BLOCK_COUNT)):
        raise EmpiricalInferenceError("complete empirical block inventory is not exactly 0..19")
    return accumulated


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        + b"\n"
    )


def _bound_payload(bound: Bound | LowerBound) -> Mapping[str, float]:
    result = {
        "mean": bound.mean,
        "standard_deviation": bound.standard_deviation,
        "lower": bound.lower,
    }
    if isinstance(bound, Bound):
        result["upper"] = bound.upper
    return result


def analyze_empirical_complete_panel(
    records: Sequence[Mapping[str, object]], *, expected_bindings: EmpiricalBindings
) -> EmpiricalAnalysisOutcome:
    """Admit and analyze one indivisible twenty-block empirical panel.

    On any malformed, incomplete, synthetic, nonfinite, or binding-mismatched
    input, no endpoint or scientific branch is released.
    """

    try:
        prerequisite_values, direct_values, mechanism_values = _admit_records(
            records, expected_bindings
        )
        prerequisite, direct, mechanism = compute_registered_bounds(
            prerequisite_values, direct_values, mechanism_values
        )
        reduced = reduce_complete_bounds(prerequisite, direct, mechanism)
        payload_body = {
            "bindings": asdict(expected_bindings),
            "gamma_global": GAMMA_GLOBAL,
            "degrees_of_freedom": DEGREES_OF_FREEDOM,
            "bounds": {
                "prerequisite": {
                    name: _bound_payload(prerequisite[name]) for name in PREREQUISITE_VARIABLES
                },
                "direct_value": {
                    name: _bound_payload(direct[name]) for name in DIRECT_VALUE_VARIABLES
                },
                "mechanism": {
                    name: _bound_payload(mechanism[name]) for name in MECHANISM_VARIABLES
                },
            },
            "gates": dict(reduced.gates),
            "predicates": dict(reduced.predicates),
            "complete": True,
            "partial_interpretation_permitted": False,
        }
        analyzer_payload = _canonical_json(
            {
                "schema": ANALYZER_OUTPUT_SCHEMA,
                "science_revision": SCIENCE_REVISION,
                "empirical_object": EMPIRICAL_OBJECT,
                "block_count": BLOCK_COUNT,
                "registered_tail_count": REGISTERED_TAIL_COUNT,
                "registered_tail_names": list(REGISTERED_TAIL_NAMES),
                "branch": reduced.branch,
                "payload": payload_body,
            }
        )
    except (
        EmpiricalInferenceError,
        EmpiricalArtifactError,
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        return _invalid(str(exc))

    return EmpiricalAnalysisOutcome(
        admitted_empirical=True,
        branch=reduced.branch,
        scientific_branch=reduced.branch,
        schema=ANALYZER_OUTPUT_SCHEMA,
        science_revision=SCIENCE_REVISION,
        empirical_object=EMPIRICAL_OBJECT,
        block_count=BLOCK_COUNT,
        gamma_global=GAMMA_GLOBAL,
        degrees_of_freedom=DEGREES_OF_FREEDOM,
        registered_tail_count=REGISTERED_TAIL_COUNT,
        bounds={"prerequisite": prerequisite, "direct_value": direct, "mechanism": mechanism},
        gates=reduced.gates,
        predicates=reduced.predicates,
        analyzer_payload=analyzer_payload,
        failure_reason=None,
    )


__all__ = [
    "EMPIRICAL_ANALYZER_INPUT_SCHEMA",
    "EMPIRICAL_RECORD_CLASS",
    "EmpiricalAnalysisOutcome",
    "EmpiricalInferenceError",
    "SYNTHETIC_TEST_ONLY",
    "analyze_empirical_complete_panel",
]
