"""Single-run inspection report: what a run actually recorded, and what it did not.

Plan Section 8.2.  The report answers one question honestly - "what can be established
about this run from its own artifacts?" - and it is deliberately unhelpful about anything
else.  Three design choices carry the weight:

* **Declared and observed boundary semantics are separate rows.**  A manifest that declares
  ``legacy_truncation_as_termination`` tells us which arithmetic the run *asked* for; only
  ``low_boundary_flags_resolved`` / ``low_boundary_legacy_collapse`` /
  ``low_truncation_rows`` tell us which arithmetic *ran*.  When the runtime flags are absent
  the observed semantics are reported as UNVERIFIED, never as "presumably correct".
* **Metric summaries count invalid rows.**  ``n_valid`` and ``n_invalid`` are printed side by
  side, so a mean over 40 of 48 episodes cannot be mistaken for a mean over 48.
* **Writing a report never touches a run directory.**  :func:`write_run_report` creates a new
  directory and refuses a non-empty existing one, because a normalised report is
  reproducible and dispensable while a historical run directory is not.

Static only: the report is built from a reader, and readers parse text.  Nothing here
imports an agent or an environment, and no checkpoint is opened.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from tools.research_support.readers import (
    BOUNDARY_DECLARED_KEY,
    BOUNDARY_RUNTIME_KEYS,
    ReadResult,
    UnsupportedSourceError,
    boundary_semantics,
    read_run,
)
from tools.research_support.records import (
    MetricRecord,
    RunRecord,
    Validity,
    content_hash,
    dumps,
)

#: Report schema, so a consumer can tell two generations of report apart.
RUN_REPORT_SCHEMA = "research_support.run_report.1"

#: Extra files listed under the root beyond the ones a reader consumed.  Bounded so that
#: inspecting a tree with thousands of files stays a report rather than a directory dump.
MAX_LISTED_EXTRA_FILES = 50


@dataclass
class RunReport:
    """One run's identity, boundary semantics, artifacts, metric coverage and gaps."""

    run_record: RunRecord
    boundary_semantics: dict[str, Any] = field(default_factory=dict)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    metric_summary: list[dict[str, Any]] = field(default_factory=list)
    coverage: dict[str, Any] = field(default_factory=dict)
    schema: str = RUN_REPORT_SCHEMA

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "run_record": self.run_record.to_json(),
            "boundary_semantics": self.boundary_semantics,
            "artifacts": self.artifacts,
            "metric_summary": self.metric_summary,
            "coverage": self.coverage,
        }


def _file_kind(path: Path) -> str:
    name = path.name.lower()
    if name.endswith("manifest.json"):
        return "manifest"
    if name == "analysis_result.json":
        return "analysis"
    if name.startswith("paper_eval_episodes_step_"):
        # The step number belongs to the run's identity, not to the file kind.
        return "legacy_episode_csv"
    if name.endswith(".json"):
        return "json"
    if name.endswith(".csv"):
        return "csv"
    if name.endswith(".pt"):
        return "checkpoint_not_read"
    return path.suffix.lstrip(".") or "file"


def _artifact_entry(path: Path, *, status: str, digest: str | None, detail: str | None) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": str(path),
        "kind": _file_kind(path),
        "status": status,
        "readable": False,
        "bytes": None,
        "sha256": digest,
    }
    try:
        stat = path.stat()
    except OSError as error:
        entry["detail"] = f"cannot stat: {error}"
        return entry
    entry["bytes"] = int(stat.st_size)
    entry["readable"] = path.is_file()
    if detail is not None:
        entry["detail"] = detail
    return entry


def _collect_artifacts(root: Path, result: ReadResult, run: RunRecord) -> list[dict[str, Any]]:
    """Every file a reader touched, plus what else sits next to it, with hashes."""

    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for note in result.coverage.get("files", []) or []:
        path = Path(str(note.get("path")))
        digest = note.get("sha256") or run.source_hashes.get(str(path))
        entry = _artifact_entry(
            path,
            status=str(note.get("status", "unknown")),
            digest=digest,
            detail=note.get("detail"),
        )
        if note.get("rows") is not None:
            entry["rows"] = note["rows"]
        entries.append(entry)
        seen.add(str(path))
    for text, digest in sorted(run.source_hashes.items()):
        if text in seen:
            continue
        entries.append(_artifact_entry(Path(text), status="parsed", digest=digest, detail=None))
        seen.add(text)

    if root.is_dir():
        extra: list[Path] = []
        for path in sorted(root.iterdir()):
            if not path.is_file() or str(path) in seen:
                continue
            extra.append(path)
        for path in extra[:MAX_LISTED_EXTRA_FILES]:
            entries.append(
                _artifact_entry(
                    path,
                    status="not_read",
                    digest=None,
                    detail="present in the run directory; no reader consumed it",
                )
            )
        if len(extra) > MAX_LISTED_EXTRA_FILES:
            entries.append(
                {
                    "path": str(root),
                    "kind": "listing_truncated",
                    "status": "not_read",
                    "readable": True,
                    "bytes": None,
                    "sha256": None,
                    "detail": (
                        f"{len(extra) - MAX_LISTED_EXTRA_FILES} further unread files in this "
                        "directory are not listed"
                    ),
                }
            )
    return entries


def _summarise_metrics(records: Iterable[MetricRecord]) -> list[dict[str, Any]]:
    """Per (run, metric, phase, level) counts and value range, keeping invalid rows visible."""

    buckets: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for record in records:
        key = (
            record.run_id,
            record.metric_name,
            record.phase.value,
            record.aggregation_level.value,
        )
        bucket = buckets.setdefault(
            key,
            {
                "run_id": record.run_id,
                "metric_name": record.metric_name,
                "phase": record.phase.value,
                "aggregation_level": record.aggregation_level.value,
                "n_rows": 0,
                "n_valid": 0,
                "n_invalid": 0,
                "n_absent": 0,
                "x_kind": set(),
                "units": set(),
                "validity_counts": {},
                "_min": None,
                "_max": None,
                "example_source": record.source_path,
            },
        )
        bucket["n_rows"] += 1
        bucket["x_kind"].add(record.x_kind.value)
        if record.unit or record.value.unit:
            bucket["units"].add(record.unit or record.value.unit)
        validity = record.value.validity
        bucket["validity_counts"][validity.value] = (
            bucket["validity_counts"].get(validity.value, 0) + 1
        )
        if validity is Validity.OK:
            bucket["n_valid"] += 1
            value = record.value.value
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                number = float(value)
                bucket["_min"] = number if bucket["_min"] is None else min(bucket["_min"], number)
                bucket["_max"] = number if bucket["_max"] is None else max(bucket["_max"], number)
        elif validity is Validity.INVALID:
            bucket["n_invalid"] += 1
        else:
            bucket["n_absent"] += 1

    summary: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        low, high = bucket.pop("_min"), bucket.pop("_max")
        bucket["x_kind"] = sorted(bucket["x_kind"])
        bucket["units"] = sorted(bucket["units"])
        bucket["range"] = None if low is None or high is None else [low, high]
        summary.append(bucket)
    return summary


def inspect_run(root: Path, *, reader: str | None = None) -> RunReport:
    """Read one run root and describe it, without repairing or executing anything.

    A source that yields more than one run record (the service-restoration report has one
    per rule controller) reports the first as ``run_record`` and carries the rest in
    ``coverage["additional_run_records"]``; nothing is merged, because a merged identity
    would be a record no run ever had.
    """

    root = Path(root)
    result = read_run(root, reader=reader)
    if not result.run_records:
        raise UnsupportedSourceError(
            f"{root} was recognised but produced no run record; see coverage: {result.coverage}"
        )
    primary = result.run_records[0]
    semantics = result.coverage.get("boundary_semantics")
    if not isinstance(semantics, dict):
        semantics = boundary_semantics({})
        semantics["notes"] = list(semantics.get("notes", [])) + [
            "this source family records neither the declared boundary switch "
            f"({BOUNDARY_DECLARED_KEY}) nor the runtime resolution flags "
            f"({', '.join(BOUNDARY_RUNTIME_KEYS)})"
        ]
    coverage: dict[str, Any] = {
        "reader": primary.reader,
        "reader_version": primary.reader_version,
        "root": str(root),
        "run_record_count": len(result.run_records),
        "metric_record_count": len(result.metric_records),
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "unsupported": list(result.unsupported),
        "reader_coverage": result.coverage,
    }
    if len(result.run_records) > 1:
        coverage["additional_run_records"] = [
            record.to_json() for record in result.run_records[1:]
        ]
        coverage["warnings"].append(
            f"{len(result.run_records)} run records were read from this root; the report's "
            "run_record is the first and the others are listed under "
            "coverage.additional_run_records"
        )
    return RunReport(
        run_record=primary,
        boundary_semantics=semantics,
        artifacts=_collect_artifacts(root, result, primary),
        metric_summary=_summarise_metrics(result.metric_records),
        coverage=coverage,
    )


# --------------------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------------------


def _escape_cell(value: Any) -> str:
    text = "-" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _markdown(report: RunReport) -> str:
    run = report.run_record
    lines: list[str] = []
    lines.append(f"# Run report: {run.run_id}")
    lines.append("")
    lines.append(f"- reader: `{run.reader}` version `{run.reader_version}`")
    lines.append(f"- root: `{report.coverage.get('root')}`")
    lines.append(f"- run records read: {report.coverage.get('run_record_count')}")
    lines.append(f"- metric records read: {report.coverage.get('metric_record_count')}")
    lines.append("")
    lines.append(
        "Every field below is either a recorded value or an explicit absence with a reason. "
        "An absence is never filled from a present-day default."
    )
    lines.append("")
    lines.append("## Identity")
    lines.append("")
    lines.append("| field | value | validity | unit | evidence |")
    lines.append("| --- | --- | --- | --- | --- |")
    for name in sorted(run.fields):
        measured = run.fields[name]
        value = measured.value if measured.validity is Validity.OK else measured.reason
        lines.append(
            "| {} | {} | {} | {} | {} |".format(
                _escape_cell(name),
                _escape_cell(value),
                _escape_cell(measured.validity.value),
                _escape_cell(measured.unit),
                _escape_cell(run.field_status.get(name)),
            )
        )
    lines.append("")
    lines.append("## Boundary semantics (declared vs observed)")
    lines.append("")
    declared = report.boundary_semantics.get("declared", {}) or {}
    observed = report.boundary_semantics.get("observed", {}) or {}
    lines.append(
        f"- declared: `{declared.get('semantics')}` "
        f"(status `{declared.get('status')}`, evidence `{declared.get('evidence')}`)"
    )
    lines.append(
        f"- observed: `{observed.get('semantics')}` "
        f"(status `{observed.get('status')}`, unverified={observed.get('unverified')})"
    )
    lines.append(f"- agreement: `{report.boundary_semantics.get('agreement')}`")
    lines.append(f"- truncation rows: `{observed.get('truncation_rows')}` "
                 f"(status `{observed.get('truncation_rows_status')}`)")
    if report.boundary_semantics.get("unverified"):
        lines.append(
            "- **actual execution is UNVERIFIED**: no runtime boundary-resolution flag is "
            "recorded. This is not evidence that the corrected arithmetic ran."
        )
    for note in report.boundary_semantics.get("notes", []) or []:
        lines.append(f"- note: {note}")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("| path | kind | status | bytes | sha256 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for artifact in report.artifacts:
        lines.append(
            "| {} | {} | {} | {} | {} |".format(
                _escape_cell(artifact.get("path")),
                _escape_cell(artifact.get("kind")),
                _escape_cell(artifact.get("status")),
                _escape_cell(artifact.get("bytes")),
                _escape_cell(artifact.get("sha256")),
            )
        )
    lines.append("")
    lines.append("## Metric coverage")
    lines.append("")
    if not report.metric_summary:
        lines.append("No metric record was read from this run.")
    else:
        lines.append("| metric | phase | level | x | n_rows | n_valid | n_invalid | n_absent | range |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for row in report.metric_summary:
            lines.append(
                "| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                    _escape_cell(row.get("metric_name")),
                    _escape_cell(row.get("phase")),
                    _escape_cell(row.get("aggregation_level")),
                    _escape_cell(",".join(row.get("x_kind", []))),
                    row.get("n_rows"),
                    row.get("n_valid"),
                    row.get("n_invalid"),
                    row.get("n_absent"),
                    _escape_cell(row.get("range")),
                )
            )
    lines.append("")
    lines.append("## Errors, warnings and unsupported input")
    lines.append("")
    for label, key in (("error", "errors"), ("warning", "warnings"), ("unsupported", "unsupported")):
        items = report.coverage.get(key) or []
        if not items:
            lines.append(f"- no {label}")
            continue
        for item in items:
            lines.append(f"- {label}: {item}")
    lines.append("")
    return "\n".join(lines)


def _refuse_existing_output(output_dir: Path) -> None:
    """A report directory is created, never merged into an existing one."""

    if not output_dir.exists():
        return
    if not output_dir.is_dir():
        raise FileExistsError(f"{output_dir} exists and is not a directory")
    if any(output_dir.iterdir()):
        raise FileExistsError(
            f"{output_dir} already exists and is not empty; choose a new directory. A report "
            "is reproducible and dispensable, a run directory is not, so nothing here "
            "overwrites existing output."
        )


def write_run_report(report: RunReport, output_dir: Path) -> Path:
    """Write ``run_report.json`` and ``run_report.md`` into a new directory.

    Returns the directory.  Refuses a non-empty existing directory so a historical run
    directory can never be used as an output location by accident.
    """

    output_dir = Path(output_dir)
    _refuse_existing_output(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_json()
    payload["report_content_hash"] = content_hash(payload)
    json_path = output_dir / "run_report.json"
    json_path.write_text(dumps(payload, indent=2) + "\n", encoding="utf-8")
    (output_dir / "run_report.md").write_text(_markdown(report), encoding="utf-8")
    return output_dir


# --------------------------------------------------------------------------------------
# Read-only command line
# --------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inspect_run",
        description=(
            "Static inventory of one existing run directory. Imports no agent or "
            "environment, opens no checkpoint and starts no process."
        ),
    )
    parser.add_argument("root", help="run directory to inspect")
    parser.add_argument(
        "--reader",
        default=None,
        help="force a reader by name instead of detecting one",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="new directory for run_report.json and run_report.md (never an existing run directory)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = inspect_run(Path(args.root), reader=args.reader)
    except UnsupportedSourceError as error:
        print(f"unsupported source: {error}", file=sys.stderr)
        return 2
    if args.output is None:
        print(dumps(report.to_json(), indent=2))
        return 0
    written = write_run_report(report, Path(args.output))
    print(f"wrote {written / 'run_report.json'} and {written / 'run_report.md'}")
    return 0


if __name__ == "__main__":  # pragma: no cover - thin CLI wrapper
    raise SystemExit(main())
