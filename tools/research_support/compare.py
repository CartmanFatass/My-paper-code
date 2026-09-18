"""Comparison contract: classify what differs between declared groups of runs.

Plan Section 8.3.  This module is **advisory software**.  It reads existing run records,
says which identity fields match with evidence and which do not, and refuses to compute a
pooled or paired summary when the evidence does not support one.  It does not decide a
scientific conclusion, it has no approval gate, and nothing here can be satisfied by
asserting a result.

The two asymmetries that motivate the whole design:

* **A different source SHA is not automatically a confound.**  It is often exactly the
  intended algorithm change.  When the specification declares ``source_sha`` a treatment
  factor, a difference is ``EXPECTED_TREATMENT_DIFFERENCE`` and pooling stays permitted as
  long as the declared controls hold.
* **An equal source SHA establishes nothing about the effective configuration.**  Two runs
  of the same commit can differ in reward scale, normalisation, horizon, evaluation world
  and information timing, all of which are recorded separately.  An equal SHA therefore
  produces a ``VERIFIED_MATCH`` on the SHA field and a standing warning, never a blanket
  "same configuration".

Pairing is held to the Section 4.1 rule: it needs real world-identity evidence - a
dataset/data hash, the episode interval, the event realisation and the initial-world
configuration.  Equal integer seeds and equal episode numbers are not sufficient, because
two runs can consume their generators differently and still print seed 7; such a comparison
is ``pairing_unverified``.

An ``allow_exploratory_display`` override may render a labelled side-by-side view of
non-identical experiments.  It attaches a persistent warning, it never changes a
classification to ``VERIFIED_MATCH``, and it never sets ``pooling_permitted``.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.research_support.readers import (
    ALWAYS_COMPARED_FIELDS,
    FIELD_EVALUATION_SEED,
    FIELD_SOURCE_SHA,
    FIELD_TRAINING_SEED,
    INCOMPARABLE_FIELDS,
    WORLD_IDENTITY_FIELDS,
    ReadResult,
    UnsupportedSourceError,
    read_run,
)
from tools.research_support.records import (
    Measured,
    MetricRecord,
    RunRecord,
    Validity,
    content_hash,
    dumps,
    loads,
)

#: Comparison report schema.
COMPARISON_SCHEMA = "research_support.comparison.1"

#: Pairing verdicts.  ``unpaired`` means the recorded worlds are demonstrably different (or
#: there is only one group); ``pairing_unverified`` means the evidence is incomplete, which
#: is the usual state of a historical record.
PAIRING_VERIFIED = "verified_world_identity"
PAIRING_UNVERIFIED = "pairing_unverified"
PAIRING_UNPAIRED = "unpaired"

ADVISORY_NOTE = (
    "This checker is advisory: it reports evidence and confounds. It does not decide the "
    "scientific conclusion and it is not an approval gate."
)


class DifferenceClass(str, Enum):
    """How one field's difference bears on a comparison."""

    EXPECTED_TREATMENT_DIFFERENCE = "EXPECTED_TREATMENT_DIFFERENCE"
    ADDITIONAL_CONFOUND = "ADDITIONAL_CONFOUND"
    INCOMPARABLE_METRIC_OR_WORLD = "INCOMPARABLE_METRIC_OR_WORLD"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    VERIFIED_MATCH = "VERIFIED_MATCH"


@dataclass
class ComparisonSpec:
    """An explicit statement of what is meant to differ and what is meant to be held fixed."""

    groups: dict[str, list[str]]
    treatment_factors: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    allow_exploratory_display: bool = False

    def __post_init__(self) -> None:
        if not self.groups:
            raise ValueError("a comparison specification needs at least one group")
        for label, roots in self.groups.items():
            if not isinstance(roots, (list, tuple)) or not roots:
                raise ValueError(f"group {label!r} lists no run root")

    @classmethod
    def from_file(cls, path: Path) -> "ComparisonSpec":
        """Load a JSON specification.  Strict: an unknown key is an error, not a default."""

        path = Path(path)
        payload = loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"{path}: comparison specification must be a JSON object")
        known = {
            "groups",
            "treatment_factors",
            "controls",
            "metrics",
            "allow_exploratory_display",
        }
        unknown = sorted(set(map(str, payload.keys())) - known)
        if unknown:
            raise ValueError(
                f"{path}: unknown specification keys {unknown}; a misspelled control would "
                "otherwise be silently dropped"
            )
        groups = payload.get("groups")
        if not isinstance(groups, Mapping):
            raise ValueError(f"{path}: 'groups' must map a group label to a list of run roots")
        return cls(
            groups={str(label): [str(root) for root in roots] for label, roots in groups.items()},
            treatment_factors=[str(name) for name in payload.get("treatment_factors", [])],
            controls=[str(name) for name in payload.get("controls", [])],
            metrics=[str(name) for name in payload.get("metrics", [])],
            allow_exploratory_display=bool(payload.get("allow_exploratory_display", False)),
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "groups": {label: list(roots) for label, roots in sorted(self.groups.items())},
            "treatment_factors": sorted(self.treatment_factors),
            "controls": sorted(self.controls),
            "metrics": sorted(self.metrics),
            "allow_exploratory_display": bool(self.allow_exploratory_display),
        }

    @property
    def spec_hash(self) -> str:
        return content_hash(self.to_json())

    def compared_fields(self) -> list[str]:
        """Declared treatments and controls, plus the fields that are always checked."""

        return sorted(
            set(self.treatment_factors) | set(self.controls) | set(ALWAYS_COMPARED_FIELDS)
        )


@dataclass
class FieldDifference:
    """One field's verdict, with the per-group evidence that produced it."""

    field: str
    classification: DifferenceClass
    values: dict[str, Any] = field(default_factory=dict)
    detail: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "classification": self.classification.value,
            "values": self.values,
            "detail": self.detail,
        }


@dataclass
class ComparisonReport:
    """What the comparison established, what it refused, and why."""

    spec_hash: str
    field_differences: list[FieldDifference] = field(default_factory=list)
    pooling_permitted: bool = False
    pairing_status: str = PAIRING_UNPAIRED
    refusals: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    runs: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    schema: str = COMPARISON_SCHEMA

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "spec_hash": self.spec_hash,
            "field_differences": [item.to_json() for item in self.field_differences],
            "pooling_permitted": bool(self.pooling_permitted),
            "pairing_status": self.pairing_status,
            "refusals": list(self.refusals),
            "warnings": list(self.warnings),
            "runs": self.runs,
        }

    def by_field(self, name: str) -> FieldDifference | None:
        for item in self.field_differences:
            if item.field == name:
                return item
        return None

    def classification_of(self, name: str) -> DifferenceClass | None:
        item = self.by_field(name)
        return None if item is None else item.classification


# --------------------------------------------------------------------------------------
# Group values
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class GroupValue:
    """One field as a whole group reports it.

    ``heterogeneous`` marks a group whose own runs disagree.  That is treated as a
    difference rather than averaged away: a group that contains two different reward scales
    cannot be one arm of a comparison.
    """

    present: bool
    value: Any = None
    heterogeneous: bool = False
    detail: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "present": self.present,
            "value": self.value,
            "heterogeneous": self.heterogeneous,
            "detail": self.detail,
        }


def group_value(records: Sequence[RunRecord], name: str) -> GroupValue:
    """Collapse one field across a group's run records without inventing agreement."""

    if not records:
        return GroupValue(present=False, detail="no readable run record in this group")
    measures: list[Measured] = [record.get(name) for record in records]
    absent = [
        f"{record.run_id}: {measure.validity.value}"
        + (f" ({measure.reason})" if measure.reason else "")
        for record, measure in zip(records, measures)
        if measure.validity is not Validity.OK
    ]
    if absent:
        return GroupValue(present=False, detail="; ".join(absent))
    values = {measure.value for measure in measures}
    if len(values) == 1:
        return GroupValue(present=True, value=next(iter(values)), detail="recorded in every run")
    ordered = sorted(str(value) for value in values)
    return GroupValue(
        present=True,
        value="|".join(ordered),
        heterogeneous=True,
        detail=f"this group's own runs disagree: {ordered}",
    )


def classify_field(
    name: str,
    values: Mapping[str, GroupValue],
    *,
    treatment_factors: Iterable[str],
    controls: Iterable[str],
) -> FieldDifference:
    """Classify one field from the per-group values and the declaration.

    Order of precedence, and why:

    1. **Missing on any side -> MISSING_EVIDENCE.**  Nothing can be concluded from a field
       one side never recorded, whatever it was declared to be.
    2. **All sides equal and evidenced -> VERIFIED_MATCH.**
    3. **Metric- or world-defining field differs -> INCOMPARABLE_METRIC_OR_WORLD**, even when
       declared a treatment factor: intending to change the metric does not make two
       different metrics poolable.  The declaration is named in the detail.
    4. **Declared treatment -> EXPECTED_TREATMENT_DIFFERENCE.**
    5. **Declared control, or undeclared -> ADDITIONAL_CONFOUND.**
    """

    treatments = set(treatment_factors)
    controlled = set(controls)
    payload = {label: value.to_json() for label, value in values.items()}
    declared = (
        "declared a treatment factor"
        if name in treatments
        else "declared a control"
        if name in controlled
        else "declared neither a treatment factor nor a control"
    )

    missing = [label for label, value in values.items() if not value.present]
    if missing:
        detail = (
            f"absent on {missing}; {declared}. No comparison can be made from a field one "
            "side never recorded: "
            + "; ".join(f"{label}={values[label].detail}" for label in missing)
        )
        return FieldDifference(name, DifferenceClass.MISSING_EVIDENCE, payload, detail)

    heterogeneous = [label for label, value in values.items() if value.heterogeneous]
    distinct = {value.value for value in values.values()}
    if len(distinct) == 1 and not heterogeneous:
        return FieldDifference(
            name,
            DifferenceClass.VERIFIED_MATCH,
            payload,
            f"equal with evidence on every side ({declared})",
        )

    difference_note = (
        f"values differ across groups; {declared}"
        if not heterogeneous
        else f"values differ, and {heterogeneous} disagree internally; {declared}"
    )
    if name in INCOMPARABLE_FIELDS:
        return FieldDifference(
            name,
            DifferenceClass.INCOMPARABLE_METRIC_OR_WORLD,
            payload,
            difference_note
            + ". This field defines what the recorded quantity or the evaluated world is, so "
            "a pooled or paired summary would combine numbers that do not mean the same thing"
            + (
                ". It was declared a treatment factor, which explains the difference but does "
                "not make the results poolable"
                if name in treatments
                else ""
            ),
        )
    if name in treatments:
        return FieldDifference(
            name,
            DifferenceClass.EXPECTED_TREATMENT_DIFFERENCE,
            payload,
            difference_note + ". This is the intended difference under test",
        )
    if name in controlled:
        return FieldDifference(
            name,
            DifferenceClass.ADDITIONAL_CONFOUND,
            payload,
            difference_note
            + ". It was proposed as a control, so the comparison carries a confound the "
            "specification did not intend",
        )
    extra = ""
    if name == FIELD_SOURCE_SHA:
        extra = (
            ". A source-SHA difference can be the intended algorithm change; declare it a "
            "treatment factor to classify it as one. It is reported, and it does not by "
            "itself block pooling"
        )
    return FieldDifference(
        name,
        DifferenceClass.ADDITIONAL_CONFOUND,
        payload,
        difference_note + ". An undeclared difference is reported as a confound" + extra,
    )


def classify_pairing(
    values_by_field: Mapping[str, Mapping[str, GroupValue]],
    *,
    group_count: int,
) -> tuple[str, str]:
    """Pairing verdict from world-identity evidence alone.

    Returns ``(status, detail)``.  A world-identity field that is present everywhere and
    differs means the groups ran different worlds, which is ``unpaired`` rather than merely
    unverified.  Complete and equal evidence on all four fields is the only route to
    ``verified_world_identity``.
    """

    if group_count < 2:
        return (
            PAIRING_UNPAIRED,
            f"{group_count} group(s): there is nothing to pair",
        )
    equal: list[str] = []
    differing: list[str] = []
    absent: list[str] = []
    for name in WORLD_IDENTITY_FIELDS:
        values = values_by_field.get(name)
        if not values:
            absent.append(name)
            continue
        if any(not value.present for value in values.values()):
            absent.append(name)
            continue
        distinct = {value.value for value in values.values()}
        if len(distinct) == 1 and not any(value.heterogeneous for value in values.values()):
            equal.append(name)
        else:
            differing.append(name)
    seed_note = (
        "equal integer seeds and equal episode numbers are never accepted as pairing "
        f"evidence ({FIELD_TRAINING_SEED}, {FIELD_EVALUATION_SEED} are reported but not used here)"
    )
    if differing:
        return (
            PAIRING_UNPAIRED,
            f"world identity differs on {differing}; these groups did not run the same world. "
            + seed_note,
        )
    if not absent:
        return (
            PAIRING_VERIFIED,
            f"all world-identity fields present and equal: {equal}",
        )
    return (
        PAIRING_UNVERIFIED,
        f"world identity incomplete: equal on {equal}, not recorded on {absent}. " + seed_note,
    )


# --------------------------------------------------------------------------------------
# Metric availability
# --------------------------------------------------------------------------------------


def _metric_profile(records: Iterable[MetricRecord], name: str) -> dict[str, Any]:
    matching = [record for record in records if record.metric_name == name]
    return {
        "n_records": len(matching),
        "units": sorted({record.unit for record in matching if record.unit}),
        "definition_ids": sorted({record.definition_id for record in matching if record.definition_id}),
        "x_kinds": sorted({record.x_kind.value for record in matching}),
        "aggregation_levels": sorted({record.aggregation_level.value for record in matching}),
        "phases": sorted({record.phase.value for record in matching}),
    }


def _classify_metric(name: str, profiles: Mapping[str, dict[str, Any]]) -> FieldDifference:
    label = f"metric:{name}"
    missing = [group for group, profile in profiles.items() if profile["n_records"] == 0]
    if missing:
        return FieldDifference(
            label,
            DifferenceClass.MISSING_EVIDENCE,
            dict(profiles),
            f"no record of this metric in {missing}",
        )
    definitions = {group: tuple(profile["definition_ids"]) for group, profile in profiles.items()}
    units = {group: tuple(profile["units"]) for group, profile in profiles.items()}
    if len(set(definitions.values())) > 1 or len(set(units.values())) > 1:
        return FieldDifference(
            label,
            DifferenceClass.INCOMPARABLE_METRIC_OR_WORLD,
            dict(profiles),
            "the metric is recorded with different definitions or units across groups, so the "
            "same name does not denote the same quantity",
        )
    return FieldDifference(
        label,
        DifferenceClass.VERIFIED_MATCH,
        dict(profiles),
        "present in every group with the same definition id and unit",
    )


# --------------------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------------------


def compare_runs(spec: ComparisonSpec) -> ComparisonReport:
    """Read every declared root and classify the differences.  Runs nothing."""

    report = ComparisonReport(spec_hash=spec.spec_hash)
    report.warnings.append(ADVISORY_NOTE)

    records_by_group: dict[str, list[RunRecord]] = {}
    metrics_by_group: dict[str, list[MetricRecord]] = {}
    for label, roots in spec.groups.items():
        records_by_group[label] = []
        metrics_by_group[label] = []
        entries: list[dict[str, Any]] = []
        for root in roots:
            entry: dict[str, Any] = {"root": str(root)}
            try:
                result: ReadResult = read_run(Path(root))
            except (UnsupportedSourceError, RuntimeError, OSError, ValueError) as error:
                entry["status"] = "error"
                entry["error"] = f"{type(error).__name__}: {error}"
                report.refusals.append(f"group {label!r}: {root} could not be read: {error}")
                entries.append(entry)
                continue
            entry["status"] = "read"
            entry["reader"] = result.run_records[0].reader if result.run_records else None
            entry["reader_version"] = (
                result.run_records[0].reader_version if result.run_records else None
            )
            entry["run_records"] = [
                {
                    "run_id": record.run_id,
                    "fields": {
                        name: record.get(name).to_json() for name in spec.compared_fields()
                    },
                    "field_status": {
                        name: record.field_status.get(name) for name in spec.compared_fields()
                    },
                }
                for record in result.run_records
            ]
            entry["n_metric_records"] = len(result.metric_records)
            entry["metrics_requested"] = {
                name: _metric_profile(result.metric_records, name) for name in spec.metrics
            }
            entry["errors"] = list(result.errors)
            entry["warnings"] = list(result.warnings)
            entry["unsupported"] = list(result.unsupported)
            entries.append(entry)
            records_by_group[label].extend(result.run_records)
            metrics_by_group[label].extend(result.metric_records)
        report.runs[label] = entries
        if not records_by_group[label]:
            report.refusals.append(
                f"group {label!r} has no readable run record; no identity can be established "
                "for it"
            )

    compared = spec.compared_fields()
    values_by_field: dict[str, dict[str, GroupValue]] = {}
    for name in compared + [f for f in WORLD_IDENTITY_FIELDS if f not in compared]:
        values_by_field[name] = {
            label: group_value(records_by_group[label], name) for label in spec.groups
        }

    for name in compared:
        report.field_differences.append(
            classify_field(
                name,
                values_by_field[name],
                treatment_factors=spec.treatment_factors,
                controls=spec.controls,
            )
        )
    for name in spec.metrics:
        report.field_differences.append(
            _classify_metric(
                name,
                {
                    label: _metric_profile(metrics_by_group[label], name)
                    for label in spec.groups
                },
            )
        )
    report.field_differences.sort(key=lambda item: item.field)

    report.pairing_status, pairing_detail = classify_pairing(
        values_by_field, group_count=len(spec.groups)
    )
    report.warnings.append(f"pairing: {pairing_detail}")

    incomparable = [
        item.field
        for item in report.field_differences
        if item.classification is DifferenceClass.INCOMPARABLE_METRIC_OR_WORLD
    ]
    missing_controls = [
        item.field
        for item in report.field_differences
        if item.classification is DifferenceClass.MISSING_EVIDENCE and item.field in set(spec.controls)
    ]
    unreadable_groups = [label for label, records in records_by_group.items() if not records]

    pooling = True
    if len(spec.groups) < 2:
        pooling = False
        report.refusals.append(
            "pooled summary refused: a single group has nothing to pool; the report is a "
            "description of one group"
        )
    if incomparable:
        pooling = False
        report.refusals.append(
            "pooled or paired summary refused: incomparable metric or world on "
            f"{incomparable}"
        )
    if missing_controls:
        pooling = False
        report.refusals.append(
            f"pooled summary refused: required control(s) {missing_controls} have no evidence "
            "on at least one side"
        )
    if unreadable_groups:
        pooling = False
        report.refusals.append(
            f"pooled summary refused: group(s) {unreadable_groups} produced no run record"
        )
    report.pooling_permitted = pooling

    if report.pairing_status != PAIRING_VERIFIED:
        report.refusals.append(
            f"paired summary refused: pairing_status={report.pairing_status}. {pairing_detail}"
        )

    sha_difference = report.by_field(FIELD_SOURCE_SHA)
    if sha_difference is not None:
        if sha_difference.classification is DifferenceClass.VERIFIED_MATCH:
            report.warnings.append(
                "equal source SHA does not establish equal effective configuration: reward "
                "scale, normalisation, horizon, information timing, evaluation world and "
                "checkpoint choice are recorded separately and are classified above"
            )
        elif sha_difference.classification is not DifferenceClass.MISSING_EVIDENCE:
            report.warnings.append(
                "a different source SHA can be the legitimate algorithm change under test; it "
                "is reported but never treated as an automatic blanket refusal"
            )

    missing_any = [
        item.field
        for item in report.field_differences
        if item.classification is DifferenceClass.MISSING_EVIDENCE
        and item.field in set(INCOMPARABLE_FIELDS)
    ]
    if missing_any and not incomparable:
        report.warnings.append(
            f"metric-defining field(s) {missing_any} have no evidence on at least one side. "
            "Pooling is not blocked by the contract because they were not declared controls, "
            "but whether the pooled numbers denote the same quantity is unverified"
        )

    if spec.allow_exploratory_display:
        if report.pooling_permitted and report.pairing_status == PAIRING_VERIFIED:
            report.warnings.append(
                "allow_exploratory_display was requested but is not needed: the comparison "
                "already holds"
            )
        else:
            report.warnings.append(
                "EXPLORATORY DISPLAY ONLY: a labelled side-by-side view of these groups is "
                "permitted for inspection. The refusals above stand, no classification is "
                "promoted to VERIFIED_MATCH, and no pooled or paired statistic may be quoted "
                "from this display"
            )
    return report


# --------------------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------------------


def _escape_cell(value: Any) -> str:
    text = "-" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _markdown(report: ComparisonReport) -> str:
    lines: list[str] = []
    lines.append("# Comparison report")
    lines.append("")
    lines.append(f"- specification hash: `{report.spec_hash}`")
    lines.append(f"- pooling permitted: **{report.pooling_permitted}**")
    lines.append(f"- pairing status: **{report.pairing_status}**")
    lines.append("")
    lines.append("## Groups")
    lines.append("")
    for label, entries in sorted(report.runs.items()):
        lines.append(f"- **{label}**")
        for entry in entries:
            status = entry.get("status")
            detail = entry.get("error") or f"reader={entry.get('reader')}"
            lines.append(
                f"  - `{entry.get('root')}` ({status}; {detail}; "
                f"{entry.get('n_metric_records', 0)} metric records)"
            )
    lines.append("")
    lines.append("## Field classification")
    lines.append("")
    lines.append("| field | classification | detail |")
    lines.append("| --- | --- | --- |")
    for item in report.field_differences:
        lines.append(
            "| {} | {} | {} |".format(
                _escape_cell(item.field),
                _escape_cell(item.classification.value),
                _escape_cell(item.detail),
            )
        )
    lines.append("")
    lines.append("## Values")
    lines.append("")
    for item in report.field_differences:
        lines.append(f"- `{item.field}`")
        for group, value in sorted(item.values.items()):
            lines.append(f"  - {group}: {_escape_cell(value)}")
    lines.append("")
    lines.append("## Refusals")
    lines.append("")
    if not report.refusals:
        lines.append("- none")
    for refusal in report.refusals:
        lines.append(f"- {refusal}")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    for warning in report.warnings:
        lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)


def write_comparison_report(report: ComparisonReport, output_dir: Path) -> Path:
    """Write ``comparison_report.json`` and ``comparison_report.md`` into a new directory."""

    output_dir = Path(output_dir)
    if output_dir.exists():
        if not output_dir.is_dir():
            raise FileExistsError(f"{output_dir} exists and is not a directory")
        if any(output_dir.iterdir()):
            raise FileExistsError(
                f"{output_dir} already exists and is not empty; choose a new directory so no "
                "existing output is overwritten"
            )
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_json()
    payload["report_content_hash"] = content_hash(payload)
    (output_dir / "comparison_report.json").write_text(
        dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "comparison_report.md").write_text(_markdown(report), encoding="utf-8")
    return output_dir


# --------------------------------------------------------------------------------------
# Read-only command line
# --------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compare",
        description=(
            "Classify differences between declared groups of existing runs. Reads artifacts "
            "only: it starts no run, imports no agent and decides no conclusion."
        ),
    )
    parser.add_argument("spec", help="JSON comparison specification")
    parser.add_argument(
        "--output", default=None, help="new directory for the comparison report"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        spec = ComparisonSpec.from_file(Path(args.spec))
    except (OSError, ValueError) as error:
        print(f"invalid specification: {error}", file=sys.stderr)
        return 2
    report = compare_runs(spec)
    if args.output is None:
        print(dumps(report.to_json(), indent=2))
        return 0
    written = write_comparison_report(report, Path(args.output))
    print(f"wrote {written / 'comparison_report.json'} and {written / 'comparison_report.md'}")
    return 0


if __name__ == "__main__":  # pragma: no cover - thin CLI wrapper
    raise SystemExit(main())
