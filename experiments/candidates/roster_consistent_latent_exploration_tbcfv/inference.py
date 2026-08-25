"""Fail-closed, fixture-only inference surface for RCLE-TBCFV r04.

This module constructs the frozen 72-tail analyzer.  It deliberately accepts
only twenty records explicitly labelled as synthetic, non-scientific fixture
data.  It is not an empirical result reader.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any, Mapping, Sequence

from scipy.stats import t as student_t

from .config import LEARNED_PACKAGES, SCIENCE_REVISION, SCRIPTED_PACKAGES

ANALYZER_SCHEMA_VERSION = "rcle-tbcfv-r04-synthetic-analyzer-v2"
BLOCK_COUNT = 20
DEGREES_OF_FREEDOM = 19
TAIL_COUNT = 72
GAMMA_GLOBAL = 1.0 - 0.05 / TAIL_COUNT

PATHS = ("8_to_12", "12_to_8")
ROSTER_PATHS = ("8_to_8", "12_to_12", *PATHS)
EVENT_CONDITIONS = ("active_continuation", "new_epoch")
TRAINING_CELLS = tuple(
    f"{path}.{event}"
    for path in ("6_to_6", "10_to_10", "6_to_10", "10_to_6")
    for event in ("ACTIVE_CONTINUATION", "NEW_EPOCH")
)
HELDOUT_CELLS = tuple(
    f"{path}.{event}"
    for path in ("8_to_8", "12_to_12", "8_to_12", "12_to_8")
    for event in ("ACTIVE_CONTINUATION", "NEW_EPOCH")
)
FIXTURE_HOST_COMPONENT = "rcle.tbcfv.r04.synthetic_fixture_host"
_HEX_DIGEST = re.compile(r"[0-9a-f]{64}")
CONSTRUCTION_GUARD_KEYS = (
    "complete_construction",
    "host_component",
    "host_source_digest",
    "treatment_fidelity",
    "analytic_containment",
    "evaluation_adaptation",
    "forbidden_information",
    "unregistered_coordinate",
    "learned_arms",
    "scripted_packages",
    "training_cells",
    "heldout_cells",
)

OPPORTUNITY_VARIABLES = tuple(
    f"opportunity.{quantity}.{path}"
    for path in PATHS
    for quantity in ("time", "loss")
)
SCAFFOLD_VARIABLES = tuple(
    f"scaffold.{quantity}.{path}.{event}"
    for path in ROSTER_PATHS
    for event in EVENT_CONDITIONS
    for quantity in ("time", "loss")
)
FLEX_VARIABLES = tuple(
    f"flex.{quantity}.{path}.{event}"
    for path in ROSTER_PATHS
    for event in EVENT_CONDITIONS
    for quantity in ("time_gap", "loss_gap", "loss_cap")
)
PREREQUISITE_VARIABLES = OPPORTUNITY_VARIABLES + SCAFFOLD_VARIABLES + FLEX_VARIABLES

DIRECT_VALUE_VARIABLES = tuple(
    f"{quantity}.{path}" for path in PATHS for quantity in ("time", "loss")
)
MECHANISM_VARIABLES = tuple(
    f"{quantity}.{path}"
    for path in PATHS
    for quantity in (
        "churn_specificity",
        "fragmentation",
        "commonality",
        "persistence",
        "bundle",
    )
)

assert len(PREREQUISITE_VARIABLES) == 44
assert len(DIRECT_VALUE_VARIABLES) == 4
assert len(MECHANISM_VARIABLES) == 10

BRANCHES = (
    "INVALID_OR_INCOMPLETE",
    "TARGET_OPPORTUNITY_NOT_ESTABLISHED",
    "COMMON_SCAFFOLD_NOT_ESTABLISHED",
    "FLEX_COMPETENCE_NOT_ESTABLISHED",
    "C1P1_COMBINED_COMMITMENT_SUPPORTED",
    "C1P1_NARROW_COMPONENT_SUPPORTED",
    "C1P1_GENERIC_HELDOUT_SCALE_VALUE",
    "C1P1_TARGET_PACKAGE_ONLY",
    "FLEX_CONTAINING_SUPERIOR",
    "FRAGMENTATION_CHANGE_WITHOUT_DIRECT_VALUE",
    "TARGET_SPECIFIC_NO_MATERIAL",
    "TARGET_UNRESOLVED",
)


@dataclass(frozen=True)
class Bound:
    mean: float
    standard_deviation: float
    lower: float
    upper: float


@dataclass(frozen=True)
class LowerBound:
    mean: float
    standard_deviation: float
    lower: float


@dataclass(frozen=True)
class ReducedInference:
    branch: str
    gates: Mapping[str, bool]
    predicates: Mapping[str, Any]


@dataclass(frozen=True)
class AnalyzerOutcome:
    """A construction-fixture disposition, never a scientific result."""

    branch: str
    scientific_branch: str | None
    valid_complete_fixture: bool
    fixture_only: bool
    non_scientific: bool
    schema_version: str
    revision: str
    source_digest: str | None
    gamma_global: float
    degrees_of_freedom: int
    registered_tail_count: int
    bounds: Mapping[str, Mapping[str, Bound | LowerBound]]
    gates: Mapping[str, bool]
    predicates: Mapping[str, Any]
    failure_reason: str | None = None


class FixtureSchemaError(ValueError):
    """Raised internally for input that cannot enter the branch reducer."""


def _invalid(reason: str) -> AnalyzerOutcome:
    return AnalyzerOutcome(
        branch=BRANCHES[0],
        scientific_branch=None,
        valid_complete_fixture=False,
        fixture_only=True,
        non_scientific=True,
        schema_version=ANALYZER_SCHEMA_VERSION,
        revision=SCIENCE_REVISION,
        source_digest=None,
        gamma_global=GAMMA_GLOBAL,
        degrees_of_freedom=DEGREES_OF_FREEDOM,
        registered_tail_count=TAIL_COUNT,
        bounds={},
        gates={},
        predicates={},
        failure_reason=reason,
    )


def _finite_float(value: object, location: str) -> float:
    if isinstance(value, bool):
        raise FixtureSchemaError(f"{location} must be a finite real number")
    try:
        converted = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError) as exc:
        raise FixtureSchemaError(f"{location} must be a finite real number") from exc
    if not math.isfinite(converted):
        raise FixtureSchemaError(f"{location} must be finite")
    return converted


def _group(
    record: Mapping[str, object], group_name: str, expected_names: tuple[str, ...], block: int
) -> dict[str, float]:
    raw = record.get(group_name)
    if not isinstance(raw, Mapping):
        raise FixtureSchemaError(f"block {block} has no mapping {group_name!r}")
    if set(raw) != set(expected_names):
        missing = sorted(set(expected_names) - set(raw))
        extra = sorted(set(raw) - set(expected_names))
        raise FixtureSchemaError(
            f"block {block} {group_name} schema mismatch; missing={missing}, extra={extra}"
        )
    return {
        name: _finite_float(raw[name], f"block {block} {group_name}.{name}")
        for name in expected_names
    }


def _validate_records(
    records: Sequence[Mapping[str, object]], expected_source_digest: str | None
) -> tuple[dict[str, list[float]], dict[str, list[float]], dict[str, list[float]]]:
    if (
        not isinstance(expected_source_digest, str)
        or not _HEX_DIGEST.fullmatch(expected_source_digest)
    ):
        raise FixtureSchemaError("a lowercase expected source SHA-256 digest is required")
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise FixtureSchemaError("records must be a sequence")
    if len(records) != BLOCK_COUNT:
        raise FixtureSchemaError(f"exactly {BLOCK_COUNT} complete fixture blocks are required")

    accumulated = (
        {name: [] for name in PREREQUISITE_VARIABLES},
        {name: [] for name in DIRECT_VALUE_VARIABLES},
        {name: [] for name in MECHANISM_VARIABLES},
    )
    groups = (
        ("prerequisite", PREREQUISITE_VARIABLES, accumulated[0]),
        ("direct_value", DIRECT_VALUE_VARIABLES, accumulated[1]),
        ("mechanism", MECHANISM_VARIABLES, accumulated[2]),
    )
    expected_top = {
        "schema_version",
        "revision",
        "source_digest",
        "fixture_only",
        "non_scientific",
        "construction_guards",
        *(name for name, _, _ in groups),
    }
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise FixtureSchemaError(f"block {index} is not a mapping")
        if set(record) != expected_top:
            raise FixtureSchemaError(f"block {index} top-level schema is not exact")
        if record["fixture_only"] is not True or record["non_scientific"] is not True:
            raise FixtureSchemaError(f"block {index} is not explicitly fixture-only/non-scientific")
        if record["schema_version"] != ANALYZER_SCHEMA_VERSION:
            raise FixtureSchemaError(f"block {index} analyzer schema version mismatch")
        if record["revision"] != SCIENCE_REVISION:
            raise FixtureSchemaError(f"block {index} revision mismatch")
        if record["source_digest"] != expected_source_digest:
            raise FixtureSchemaError(f"block {index} source identity mismatch")
        guards = record["construction_guards"]
        if not isinstance(guards, Mapping) or set(guards) != set(CONSTRUCTION_GUARD_KEYS):
            raise FixtureSchemaError(f"block {index} construction guard schema is not exact")
        expected_guards = {
            "complete_construction": True,
            "host_component": FIXTURE_HOST_COMPONENT,
            "host_source_digest": expected_source_digest,
            "treatment_fidelity": True,
            "analytic_containment": True,
            "evaluation_adaptation": False,
            "forbidden_information": False,
            "unregistered_coordinate": False,
            "learned_arms": list(LEARNED_PACKAGES),
            "scripted_packages": list(SCRIPTED_PACKAGES),
            "training_cells": list(TRAINING_CELLS),
            "heldout_cells": list(HELDOUT_CELLS),
        }
        if dict(guards) != expected_guards:
            raise FixtureSchemaError(f"block {index} construction guard failed or mismatched")
        for group_name, names, destination in groups:
            values = _group(record, group_name, names, index)
            for name, value in values.items():
                destination[name].append(value)
    return accumulated


def _bounds(
    values_by_name: Mapping[str, list[float]], *, one_sided_lower: bool
) -> dict[str, Bound | LowerBound]:
    quantile = float(student_t.ppf(GAMMA_GLOBAL, df=DEGREES_OF_FREEDOM))
    if not math.isfinite(quantile):
        raise FixtureSchemaError("Student-t quantile is nonfinite")
    result: dict[str, Bound | LowerBound] = {}
    for name, values in values_by_name.items():
        mean = math.fsum(values) / BLOCK_COUNT
        squared = math.fsum((value - mean) ** 2 for value in values)
        standard_deviation = math.sqrt(squared / DEGREES_OF_FREEDOM)
        half_width = quantile * standard_deviation / math.sqrt(BLOCK_COUNT)
        lower = mean if standard_deviation == 0.0 else mean - half_width
        upper = mean if standard_deviation == 0.0 else mean + half_width
        if not all(math.isfinite(value) for value in (mean, standard_deviation, lower, upper)):
            raise FixtureSchemaError(f"computed nonfinite endpoint for {name}")
        result[name] = (
            LowerBound(mean, standard_deviation, lower)
            if one_sided_lower
            else Bound(mean, standard_deviation, lower, upper)
        )
    return result


def compute_registered_bounds(
    prerequisite_values: Mapping[str, list[float]],
    direct_values: Mapping[str, list[float]],
    mechanism_values: Mapping[str, list[float]],
) -> tuple[
    dict[str, Bound | LowerBound],
    dict[str, Bound | LowerBound],
    dict[str, Bound | LowerBound],
]:
    """Compute the one frozen 72-tail family after caller-owned admission."""

    if set(prerequisite_values) != set(PREREQUISITE_VARIABLES):
        raise FixtureSchemaError("prerequisite value inventory is not exact")
    if set(direct_values) != set(DIRECT_VALUE_VARIABLES):
        raise FixtureSchemaError("direct-value inventory is not exact")
    if set(mechanism_values) != set(MECHANISM_VARIABLES):
        raise FixtureSchemaError("mechanism inventory is not exact")
    for family in (prerequisite_values, direct_values, mechanism_values):
        if any(len(values) != BLOCK_COUNT for values in family.values()):
            raise FixtureSchemaError("every registered variable requires exactly twenty values")
        if any(not math.isfinite(value) for values in family.values() for value in values):
            raise FixtureSchemaError("registered values must be finite")
    return (
        _bounds(prerequisite_values, one_sided_lower=True),
        _bounds(direct_values, one_sided_lower=False),
        _bounds(mechanism_values, one_sided_lower=False),
    )


def reduce_complete_bounds(
    prerequisite: Mapping[str, Bound | LowerBound],
    direct: Mapping[str, Bound | LowerBound],
    mechanism: Mapping[str, Bound | LowerBound],
) -> ReducedInference:
    """Apply the literal r04 thresholds and twelve-branch first-match law."""

    if set(prerequisite) != set(PREREQUISITE_VARIABLES):
        raise FixtureSchemaError("prerequisite bound inventory is not exact")
    if set(direct) != set(DIRECT_VALUE_VARIABLES):
        raise FixtureSchemaError("direct-value bound inventory is not exact")
    if set(mechanism) != set(MECHANISM_VARIABLES):
        raise FixtureSchemaError("mechanism bound inventory is not exact")
    if any(not isinstance(bound, LowerBound) for bound in prerequisite.values()):
        raise FixtureSchemaError("prerequisite bounds must be one-sided lower bounds")
    if any(not isinstance(bound, Bound) for bound in (*direct.values(), *mechanism.values())):
        raise FixtureSchemaError("value and mechanism bounds must be two-sided")

    opportunity_pass = all(prerequisite[name].lower > 0.0 for name in OPPORTUNITY_VARIABLES)
    scaffold_pass = all(prerequisite[name].lower > 0.0 for name in SCAFFOLD_VARIABLES)
    flex_pass = all(prerequisite[name].lower > 0.0 for name in FLEX_VARIABLES)

    value_winning_paths: list[str] = []
    flex_winning_paths: list[str] = []
    for path in PATHS:
        other = PATHS[1] if path == PATHS[0] else PATHS[0]
        if (
            direct[f"time.{path}"].lower > 4.0
            and direct[f"time.{other}"].lower > -2.0
            and all(direct[f"loss.{candidate}"].lower > -0.02 for candidate in PATHS)
        ):
            value_winning_paths.append(path)
        if (
            direct[f"time.{path}"].upper < -4.0
            and direct[f"time.{other}"].upper < 2.0
            and all(direct[f"loss.{candidate}"].upper < 0.02 for candidate in PATHS)
        ):
            flex_winning_paths.append(path)

    target_no_material = all(
        -2.0 <= direct[f"time.{path}"].lower <= direct[f"time.{path}"].upper <= 2.0
        and -0.02 <= direct[f"loss.{path}"].lower <= direct[f"loss.{path}"].upper <= 0.02
        for path in PATHS
    )

    combined_paths: list[str] = []
    narrow_paths: dict[str, str] = {}
    churn_resolved_not_present: dict[str, bool] = {}
    fragmentation_changed_paths: list[str] = []
    mechanism_passes: dict[str, dict[str, bool]] = {}
    for path in PATHS:
        passes = {
            "churn_specificity": mechanism[f"churn_specificity.{path}"].lower > 2.0,
            "fragmentation": mechanism[f"fragmentation.{path}"].lower > 0.05,
            "commonality": mechanism[f"commonality.{path}"].lower > 2.0,
            "persistence": mechanism[f"persistence.{path}"].lower > 2.0,
            "bundle": mechanism[f"bundle.{path}"].lower > 4.0,
        }
        mechanism_passes[path] = passes
        churn_resolved_not_present[path] = mechanism[f"churn_specificity.{path}"].upper <= 2.0
        if path in value_winning_paths:
            if all(passes.values()):
                combined_paths.append(path)
            elif (
                passes["churn_specificity"]
                and passes["fragmentation"]
                and passes["bundle"]
                and (passes["commonality"] != passes["persistence"])
            ):
                narrow_paths[path] = "commonality" if passes["commonality"] else "persistence"
        fragmentation_bound = mechanism[f"fragmentation.{path}"]
        if fragmentation_bound.lower > 0.05 or fragmentation_bound.upper < -0.05:
            fragmentation_changed_paths.append(path)

    if not opportunity_pass:
        branch = BRANCHES[1]
    elif not scaffold_pass:
        branch = BRANCHES[2]
    elif not flex_pass:
        branch = BRANCHES[3]
    elif combined_paths:
        branch = BRANCHES[4]
    elif narrow_paths:
        branch = BRANCHES[5]
    elif value_winning_paths and all(churn_resolved_not_present[p] for p in value_winning_paths):
        branch = BRANCHES[6]
    elif value_winning_paths:
        branch = BRANCHES[7]
    elif flex_winning_paths:
        branch = BRANCHES[8]
    elif target_no_material and fragmentation_changed_paths:
        branch = BRANCHES[9]
    elif target_no_material:
        branch = BRANCHES[10]
    else:
        branch = BRANCHES[11]

    return ReducedInference(
        branch=branch,
        gates={
            "target_opportunity": opportunity_pass,
            "common_scaffold": scaffold_pass,
            "flex_competence": flex_pass,
        },
        predicates={
            "c1p1_target_win": bool(value_winning_paths),
            "value_winning_paths": tuple(value_winning_paths),
            "flex_target_win": bool(flex_winning_paths),
            "flex_winning_paths": tuple(flex_winning_paths),
            "target_no_material": target_no_material,
            "combined_commitment_paths": tuple(combined_paths),
            "narrow_component_paths": dict(narrow_paths),
            "churn_specificity_resolved_not_present": churn_resolved_not_present,
            "mechanism_passes": mechanism_passes,
            "fragmentation_changed_paths": tuple(fragmentation_changed_paths),
        },
    )


def analyze_fixture_records(
    records: Sequence[Mapping[str, object]], *, expected_source_digest: str | None = None
) -> AnalyzerOutcome:
    """Analyze exactly twenty complete, explicitly synthetic run-block records.

    Malformed, incomplete, or nonfinite inputs return the non-scientific
    ``INVALID_OR_INCOMPLETE`` disposition with no bounds or predicates exposed.
    """

    try:
        prerequisite_values, direct_values, mechanism_values = _validate_records(
            records, expected_source_digest
        )
        prerequisite, direct, mechanism = compute_registered_bounds(
            prerequisite_values, direct_values, mechanism_values
        )
        reduced = reduce_complete_bounds(prerequisite, direct, mechanism)
    except (FixtureSchemaError, ArithmeticError, KeyError, TypeError) as exc:
        return _invalid(str(exc))

    return AnalyzerOutcome(
        branch=reduced.branch,
        scientific_branch=None,
        valid_complete_fixture=True,
        fixture_only=True,
        non_scientific=True,
        schema_version=ANALYZER_SCHEMA_VERSION,
        revision=SCIENCE_REVISION,
        source_digest=expected_source_digest,
        gamma_global=GAMMA_GLOBAL,
        degrees_of_freedom=DEGREES_OF_FREEDOM,
        registered_tail_count=TAIL_COUNT,
        bounds={"prerequisite": prerequisite, "direct_value": direct, "mechanism": mechanism},
        gates=reduced.gates,
        predicates=reduced.predicates,
    )


__all__ = [
    "AnalyzerOutcome",
    "ANALYZER_SCHEMA_VERSION",
    "BLOCK_COUNT",
    "BRANCHES",
    "Bound",
    "DEGREES_OF_FREEDOM",
    "DIRECT_VALUE_VARIABLES",
    "GAMMA_GLOBAL",
    "HELDOUT_CELLS",
    "LowerBound",
    "MECHANISM_VARIABLES",
    "PREREQUISITE_VARIABLES",
    "ReducedInference",
    "SCIENCE_REVISION",
    "TAIL_COUNT",
    "TRAINING_CELLS",
    "analyze_fixture_records",
    "compute_registered_bounds",
    "reduce_complete_bounds",
]
