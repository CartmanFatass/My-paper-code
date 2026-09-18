"""Read-only report on a prepared dataset: what is in it, and what is missing from it.

A prepared dataset is the one artifact a scientific claim inherits silently. If a cache
is half written, if a declared field is absent from every record, if two records share an
identity, or if an unobserved cell is read as a demand of zero, every number computed
downstream is wrong in a way no amount of later analysis can detect. This module opens the
files, reads them, and says what it found.

Three rules give the report its value:

* **Missing is missing.** An absent record, an unobserved cell and an explicit ``null`` are
  reported as :class:`~tools.research_support.records.Validity` absences with a reason, never
  as ``0``. A measured zero (an observed cell whose activity really is ``0.0``) stays a
  measurement and is counted separately.
* **Declared and observed are separate columns.** The dataset's own ``metadata.json`` or
  sidecar schema says what *should* be there; this report says what *is* there, and the
  disagreement is a finding rather than something to reconcile.
* **No substitution, ever.** A path that does not exist, or that holds no recognised dataset
  form, raises :class:`~tools.research_support.cli.CliError`. It is never replaced by a
  fixture, a sample or a synthetic stand-in, because a report about a fixture that was asked
  about real data is worse than no report.

Nothing here writes into the dataset, executes a checkpoint, constructs an environment,
imports torch or performs an optimizer update. Arrays are opened with
``numpy.load(..., mmap_mode="r", allow_pickle=False)``: a prepared cache is data, not code.

Recognised forms, each detected by a **named artifact** rather than a path-name pattern:

``uav_service_restoration_prepared_cache``
    The directory written by ``envs.uav_service_restoration.preprocess_milan``: a
    ``metadata.json`` declaring the prepared schema version, five ``.npy`` arrays,
    ``splits.json``, ``quality_report.json`` and the completion marker.
``record_table_json`` / ``record_table_jsonl`` / ``record_table_csv``
    A table of records: a JSON array of objects, a JSON object carrying a named record
    list, one JSON object per line, or a header-row CSV. An optional ``<stem>.schema.json``
    sidecar (or an in-document ``schema``/``fields``/``units`` block) declares the schema
    this report checks the records against.
``episode_seed_list``
    The ``--episodes-file`` form consumed by
    ``scripts/uav_service_restoration/evaluate_baselines.py``: a JSON list of integer seeds,
    or an object with ``episode_seeds``/``seeds``. Seeds of one configuration are episodes of
    **one** scenario, not independent replicates, and the report says so.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from .cli import CliError
from .records import Measured, Validity, content_hash, dumps, file_hash

#: Report schema, so a consumer can tell two generations of report apart.
DATASET_REPORT_SCHEMA = "research_support.dataset_report.1"

#: Prepared-cache contract, mirrored from ``envs/uav_service_restoration/demand.py``.
#: It is mirrored rather than imported so that a *reading* command never imports an
#: environment package; ``test_dataset_report.py`` asserts equality with the environment's
#: own constants, so drift fails a test instead of silently mislabelling a cache.
PREPARED_SCHEMA_VERSION = "uav_service_restoration_v0.prepared_dataset.1"
PREPARED_COMPLETION_MARKER = "_PREPARED_COMPLETE.json"
PREPARED_ARRAYS: tuple[str, ...] = (
    "timestamps_utc_ms.npy",
    "cell_ids.npy",
    "positions_m.npy",
    "activity.npy",
    "observed_mask.npy",
)

#: Provenance vocabulary. ``recorded`` and ``unknown`` match ``inspect_env.py``;
#: ``observed_in_data`` is its read-only analogue of ``verified_runtime`` - the value was
#: verified by reading the bytes, and calling that "runtime" would imply something ran.
PROV_RECORDED = "recorded"
PROV_OBSERVED = "observed_in_data"
PROV_UNKNOWN = "unknown"

#: Hashing a multi-gigabyte array turns an inspection into a long job. Above this size the
#: digest is reported as absent with the reason, which is not the same as "verified".
MAX_HASH_BYTES = 512 * 1024 * 1024

#: Bounds that keep a report a report. Each one, when it bites, is stated in the output.
MAX_LISTED_FILES = 200
MAX_PROFILED_RECORDS = 100_000
MAX_REPORTED_FIELDS = 300
MAX_EXAMPLES = 20

_RECORD_LIST_KEYS = ("records", "episodes", "rows", "data", "items")
_SEED_LIST_KEYS = ("episode_seeds", "seeds")
_KEY_FIELD_CANDIDATES = (
    "episode_id",
    "record_id",
    "id",
    "key",
    "uid",
    "episode_index",
)


# --------------------------------------------------------------------------------------
# Report structures
# --------------------------------------------------------------------------------------


@dataclass
class FileEntry:
    """One file of the dataset, with its identity and the declaration it is checked against."""

    path: str
    exists: bool
    bytes: int | None
    mtime_utc: str | None
    sha256: str | None
    sha256_status: str
    declared_sha256: str | None = None
    hash_agreement: str = "not_declared"

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "exists": bool(self.exists),
            "bytes": self.bytes,
            "mtime_utc": self.mtime_utc,
            "sha256": self.sha256,
            "sha256_status": self.sha256_status,
            "declared_sha256": self.declared_sha256,
            "hash_agreement": self.hash_agreement,
        }


@dataclass
class FieldReport:
    """Coverage and range of one field, with the meaning of an absence spelled out.

    ``n_missing`` counts records that carry no value for this field. ``missing_treated_as``
    names the :class:`Validity` a consumer must use for those records: the count is a
    measurement, the absent values are not zeros.
    """

    name: str
    declared: bool
    observed: bool
    dtype: str | None
    unit: str | None
    unit_source: str
    n_records: int
    n_present: int
    n_missing: int
    n_null: int
    n_non_finite: int
    missing_treated_as: str
    minimum: Measured
    maximum: Measured
    provenance: str
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "declared": bool(self.declared),
            "observed": bool(self.observed),
            "dtype": self.dtype,
            "unit": self.unit,
            "unit_source": self.unit_source,
            "n_records": int(self.n_records),
            "n_present": int(self.n_present),
            "n_missing": int(self.n_missing),
            "n_null": int(self.n_null),
            "n_non_finite": int(self.n_non_finite),
            "missing_treated_as": self.missing_treated_as,
            "minimum": self.minimum.to_json(),
            "maximum": self.maximum.to_json(),
            "provenance": self.provenance,
            "notes": list(self.notes),
        }


@dataclass
class DatasetReport:
    """Everything this inspection established about one dataset, and what it could not."""

    dataset_path: str
    form: str
    form_evidence: str
    identity: dict[str, Any] = field(default_factory=dict)
    declared: dict[str, Any] = field(default_factory=dict)
    observed: dict[str, Any] = field(default_factory=dict)
    counts: dict[str, Any] = field(default_factory=dict)
    fields: list[FieldReport] = field(default_factory=list)
    duplicates: dict[str, Any] = field(default_factory=dict)
    splits: dict[str, Any] = field(default_factory=dict)
    consistency: list[dict[str, Any]] = field(default_factory=list)
    statistical_units: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    schema: str = DATASET_REPORT_SCHEMA

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "dataset_path": self.dataset_path,
            "form": self.form,
            "form_evidence": self.form_evidence,
            "identity": self.identity,
            "declared": self.declared,
            "observed": self.observed,
            "counts": self.counts,
            "fields": [item.to_json() for item in self.fields],
            "duplicates": self.duplicates,
            "splits": self.splits,
            "consistency": self.consistency,
            "statistical_units": self.statistical_units,
            "notes": list(self.notes),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    def check(self, name: str, *, declared: Any, observed: Any, agrees: bool | None) -> None:
        """Record one declared-vs-observed comparison, including one that could not be made."""

        self.consistency.append(
            {
                "check": name,
                "declared": declared,
                "observed": observed,
                "agreement": (
                    "unverifiable" if agrees is None else ("match" if agrees else "mismatch")
                ),
            }
        )
        if agrees is False:
            self.warnings.append(
                f"declared/observed mismatch in {name}: declared {declared!r}, observed "
                f"{observed!r}"
            )


# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------


def _mtime_utc(path: Path) -> str | None:
    try:
        stamp = path.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat()


def _file_entry(path: Path, *, declared_hashes: Mapping[str, Any] | None = None) -> FileEntry:
    """Identity of one file: size, mtime and digest, with a declared digest checked."""

    name = path.name
    declared = None
    if declared_hashes and name in declared_hashes:
        raw = declared_hashes[name]
        declared = str(raw) if raw is not None else None
    if not path.is_file():
        return FileEntry(
            path=str(path),
            exists=False,
            bytes=None,
            mtime_utc=None,
            sha256=None,
            sha256_status="missing_artifact",
            declared_sha256=declared,
            hash_agreement="declared_but_absent" if declared else "not_declared",
        )
    size = int(path.stat().st_size)
    if size > MAX_HASH_BYTES:
        return FileEntry(
            path=str(path),
            exists=True,
            bytes=size,
            mtime_utc=_mtime_utc(path),
            sha256=None,
            sha256_status=f"not_hashed_over_{MAX_HASH_BYTES}_bytes",
            declared_sha256=declared,
            hash_agreement="unverifiable" if declared else "not_declared",
        )
    digest = file_hash(str(path))
    bare = digest.split(":", 1)[1]
    agreement = "not_declared"
    if declared is not None:
        agreement = "match" if declared in (digest, bare) else "mismatch"
    return FileEntry(
        path=str(path),
        exists=True,
        bytes=size,
        mtime_utc=_mtime_utc(path),
        sha256=digest,
        sha256_status="hashed",
        declared_sha256=declared,
        hash_agreement=agreement,
    )


def _manifest_identity(entries: Sequence[FileEntry]) -> dict[str, Any]:
    """Dataset identity: the per-file digests plus one content hash over their manifest."""

    manifest = [
        {"path": Path(entry.path).name, "bytes": entry.bytes, "sha256": entry.sha256}
        for entry in sorted(entries, key=lambda item: Path(item.path).name)
    ]
    return {
        "files": [entry.to_json() for entry in entries],
        "manifest": manifest,
        "manifest_content_hash": content_hash(manifest),
        "manifest_rule": (
            "sha256 over the sorted (file name, size, file digest) manifest; it changes when "
            "any listed file changes, and an unhashed file contributes a null digest"
        ),
    }


def _measured_min_max(
    values: Sequence[float] | np.ndarray,
    *,
    unit: str | None,
    empty_reason: str,
    empty_validity: Validity = Validity.NOT_RECORDED,
) -> tuple[Measured, Measured]:
    """Range over present values only. No present value means absent, never ``0``."""

    array = np.asarray(values, dtype=np.float64).reshape(-1)
    finite = array[np.isfinite(array)] if array.size else array
    if finite.size == 0:
        absent = Measured.absent(empty_validity, empty_reason, unit=unit)
        return absent, absent
    return (
        Measured.ok(float(finite.min()), unit=unit, source=PROV_OBSERVED),
        Measured.ok(float(finite.max()), unit=unit, source=PROV_OBSERVED),
    )


def _read_json(path: Path, report: DatasetReport) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        report.errors.append(f"{path.name}: unreadable ({error})")
        return None
    except json.JSONDecodeError as error:
        report.errors.append(f"{path.name}: invalid JSON ({error})")
        return None
    if not isinstance(payload, Mapping):
        report.errors.append(f"{path.name}: expected a JSON object, found {type(payload).__name__}")
        return None
    return dict(payload)


def _duplicate_examples(values: Iterable[Any]) -> tuple[int, list[Any]]:
    """Count duplicated values and keep a bounded list of examples."""

    seen: dict[Any, int] = {}
    for value in values:
        key = value if isinstance(value, (str, int, float, bool, type(None))) else repr(value)
        seen[key] = seen.get(key, 0) + 1
    duplicated = {key: count for key, count in seen.items() if count > 1}
    examples = [
        {"value": key, "occurrences": count}
        for key, count in sorted(duplicated.items(), key=lambda item: -item[1])[:MAX_EXAMPLES]
    ]
    return len(duplicated), examples


# --------------------------------------------------------------------------------------
# Form detection
# --------------------------------------------------------------------------------------


def _reader_hint(path: Path) -> str:
    """Name the run reader that recognises this directory, if any, for the refusal text."""

    try:
        from .readers import detect_reader
    except ImportError:  # pragma: no cover - the readers package ships with the suite
        return ""
    try:
        reader = detect_reader(path)
    except OSError:
        return ""
    if reader is None:
        return ""
    return (
        f" This directory is recognised by the {reader.name!r} run reader: it is a run "
        "output, not a prepared dataset. Use `inspect-run --run` for it."
    )


def _detect_directory_form(path: Path) -> tuple[str, str]:
    metadata_path = path / "metadata.json"
    if metadata_path.is_file():
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CliError(
                f"{metadata_path} could not be parsed ({error}); a prepared dataset is "
                "identified by its own metadata.json and nothing is guessed from the "
                "directory name"
            ) from error
        version = payload.get("schema_version") if isinstance(payload, Mapping) else None
        if version == PREPARED_SCHEMA_VERSION:
            return "uav_service_restoration_prepared_cache", "metadata.json:schema_version"
        raise CliError(
            f"{metadata_path} declares schema_version {version!r}; this report understands "
            f"{PREPARED_SCHEMA_VERSION!r}. Nothing is read speculatively, and no fixture is "
            "substituted for the dataset you asked about."
        )
    raise CliError(
        f"{path} is a directory with no metadata.json, so no dataset form was recognised. A "
        f"prepared cache is identified by metadata.json declaring {PREPARED_SCHEMA_VERSION!r}; "
        "a record table is a .json, .jsonl/.ndjson or .csv file."
        + _reader_hint(path)
    )


def _detect_file_form(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix in (".jsonl", ".ndjson"):
        return "record_table_jsonl", f"file suffix {suffix}"
    if suffix == ".csv":
        return "record_table_csv", "file suffix .csv"
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CliError(f"{path} is not parseable as JSON: {error}") from error
        if isinstance(payload, list):
            if payload and all(isinstance(item, Mapping) for item in payload):
                return "record_table_json", "top-level JSON array of objects"
            if payload and all(isinstance(item, (int, float)) and not isinstance(item, bool)
                               for item in payload):
                return "episode_seed_list", "top-level JSON array of numbers"
            if not payload:
                raise CliError(
                    f"{path} holds an empty JSON array, so the dataset form cannot be "
                    "identified; an empty file is not assumed to be any particular form"
                )
            raise CliError(
                f"{path} holds a JSON array that is neither all objects (a record table) nor "
                "all numbers (an episode seed list); the form is not recognised"
            )
        if isinstance(payload, Mapping):
            for key in _SEED_LIST_KEYS:
                if isinstance(payload.get(key), list):
                    return "episode_seed_list", f"object key {key!r}"
            for key in _RECORD_LIST_KEYS:
                if isinstance(payload.get(key), list):
                    return "record_table_json", f"object key {key!r}"
            raise CliError(
                f"{path} is a JSON object with no record list under any of "
                f"{list(_RECORD_LIST_KEYS)} and no seed list under {list(_SEED_LIST_KEYS)}; "
                "the form is not recognised and nothing is inferred from the file name"
            )
        raise CliError(f"{path} holds a JSON scalar; that is not a dataset form")
    raise CliError(
        f"{path} has suffix {suffix or '(none)'}, which is not a recognised dataset form. "
        "Supported: a prepared-cache directory, or a .json / .jsonl / .ndjson / .csv record "
        "table."
    )


def detect_form(dataset_path: Path) -> tuple[str, str]:
    """``(form, evidence)`` for a dataset path, or :class:`CliError` explaining the refusal."""

    path = Path(dataset_path)
    if not path.exists():
        raise CliError(
            f"dataset path does not exist: {path}. Nothing is substituted for it - no "
            "fixture, no sample and no synthetic stand-in - because a report about "
            "different data than the one asked for is worse than no report."
        )
    if path.is_dir():
        return _detect_directory_form(path)
    if path.is_file():
        return _detect_file_form(path)
    raise CliError(f"{path} is neither a file nor a directory; no dataset form was recognised")


# --------------------------------------------------------------------------------------
# Prepared cache
# --------------------------------------------------------------------------------------


def _load_prepared_arrays(
    root: Path, report: DatasetReport
) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for name in PREPARED_ARRAYS:
        path = root / name
        if not path.is_file():
            report.errors.append(f"prepared cache is missing the declared array {name}")
            continue
        try:
            # Read-only memory map, no pickle: a cache is data and is never executed.
            arrays[name] = np.load(path, mmap_mode="r", allow_pickle=False)
        except (OSError, ValueError) as error:
            report.errors.append(f"{name}: not loadable as a plain .npy array ({error})")
    return arrays


def _prepared_content_hash(arrays: Mapping[str, np.ndarray]) -> tuple[str | None, str]:
    """Recompute the cache's declared ``content_sha256`` the way the writer computed it."""

    if set(arrays) != set(PREPARED_ARRAYS):
        return None, "not_all_arrays_readable"
    total = sum(int(np.asarray(value).nbytes) for value in arrays.values())
    if total > MAX_HASH_BYTES:
        return None, f"arrays_exceed_{MAX_HASH_BYTES}_bytes"
    digest = hashlib.sha256()
    digest.update(PREPARED_SCHEMA_VERSION.encode("ascii"))
    for name in sorted(arrays):
        digest.update(name.encode("ascii"))
        digest.update(np.ascontiguousarray(arrays[name]).tobytes())
    return digest.hexdigest(), "recomputed"


def _analyse_prepared_cache(root: Path, report: DatasetReport) -> None:
    metadata = _read_json(root / "metadata.json", report) or {}
    quality = (
        _read_json(root / "quality_report.json", report)
        if (root / "quality_report.json").is_file()
        else None
    )
    splits_doc = (
        _read_json(root / "splits.json", report) if (root / "splits.json").is_file() else None
    )
    if quality is None:
        report.warnings.append(
            "quality_report.json is absent or unreadable; the preparation's own quality "
            "counters cannot be checked against what this report observed"
        )
    if splits_doc is None:
        report.warnings.append(
            "splits.json is absent or unreadable; split membership is unknown, which is not "
            "the same as 'one split holds everything'"
        )

    declared_hashes = metadata.get("file_sha256") if isinstance(metadata, Mapping) else None
    declared_hashes = declared_hashes if isinstance(declared_hashes, Mapping) else {}

    listed = [root / name for name in PREPARED_ARRAYS]
    listed += [
        root / "metadata.json",
        root / "splits.json",
        root / "quality_report.json",
        root / PREPARED_COMPLETION_MARKER,
    ]
    known = {path.name for path in listed}
    extra = [p for p in sorted(root.iterdir()) if p.is_file() and p.name not in known]
    entries = [_file_entry(path, declared_hashes=declared_hashes) for path in listed]
    entries += [_file_entry(path) for path in extra[: max(0, MAX_LISTED_FILES - len(entries))]]
    if len(extra) > MAX_LISTED_FILES - len(listed):
        report.notes.append(
            f"{len(extra)} files in this directory are not part of the prepared-cache "
            "contract; the listing above is truncated"
        )
    report.identity = _manifest_identity(entries)
    report.identity["dataset_root"] = str(root)

    mismatched = [e.path for e in entries if e.hash_agreement == "mismatch"]
    if mismatched:
        report.errors.append(
            "declared file_sha256 does not match the bytes on disk for: "
            + ", ".join(Path(p).name for p in mismatched)
            + ". The cache was modified or a different version was substituted; the "
            "environment's reader refuses a cache in this state."
        )

    marker_present = (root / PREPARED_COMPLETION_MARKER).is_file()
    if not marker_present:
        report.errors.append(
            f"{PREPARED_COMPLETION_MARKER} is absent: the cache is incomplete or still being "
            "written. Every count below describes the bytes that exist now, and the "
            "environment's reader refuses a cache without the marker."
        )

    report.declared = {
        "schema_version": metadata.get("schema_version"),
        "kind": metadata.get("kind"),
        "is_real_activity_data": metadata.get("is_real_activity_data"),
        "dataset_version": metadata.get("dataset_version"),
        "description": metadata.get("description"),
        "source_url": metadata.get("source_url"),
        "license_note": metadata.get("license_note"),
        "activity_field": metadata.get("activity_field"),
        "interval_duration_ms": metadata.get("interval_duration_ms"),
        "activity_reference_scale": metadata.get("activity_reference_scale"),
        "reference_scale_rule": metadata.get("reference_scale_rule"),
        "aggregation_rule": metadata.get("aggregation_rule"),
        "duplicate_key_rule": metadata.get("duplicate_key_rule"),
        "missing_data_policy": metadata.get("missing_data_policy"),
        "spatial_discretization": metadata.get("spatial_discretization"),
        "crs": metadata.get("crs"),
        "region_selection_rule": metadata.get("region_selection_rule"),
        "content_sha256": metadata.get("content_sha256"),
        "completion_marker_present": marker_present,
        "quality_report": quality,
        "declared_arrays": list(PREPARED_ARRAYS),
        "declared_units": {
            "timestamps_utc_ms.npy": "ms since the Unix epoch, UTC",
            "cell_ids.npy": "source grid cell identifier (categorical)",
            "positions_m.npy": "m in the projected local frame",
            "activity.npy": str(metadata.get("activity_field") or "activity")
            + " activity units (NOT Mbps, NOT a device count, NOT a population)",
            "observed_mask.npy": "boolean coverage mask",
        },
    }

    arrays = _load_prepared_arrays(root, report)
    timestamps = arrays.get("timestamps_utc_ms.npy")
    cell_ids = arrays.get("cell_ids.npy")
    positions = arrays.get("positions_m.npy")
    activity = arrays.get("activity.npy")
    observed = arrays.get("observed_mask.npy")

    report.observed = {
        "arrays": {
            name: {"shape": list(np.asarray(value).shape), "dtype": str(np.asarray(value).dtype)}
            for name, value in sorted(arrays.items())
        },
        "arrays_missing": [name for name in PREPARED_ARRAYS if name not in arrays],
    }

    recomputed, hash_status = _prepared_content_hash(arrays)
    report.observed["content_sha256"] = recomputed
    report.observed["content_sha256_status"] = hash_status
    report.check(
        "content_sha256",
        declared=metadata.get("content_sha256"),
        observed=recomputed,
        agrees=(
            None
            if recomputed is None or metadata.get("content_sha256") is None
            else recomputed == str(metadata.get("content_sha256"))
        ),
    )

    if timestamps is not None and np.asarray(timestamps).size:
        stamps = np.asarray(timestamps).reshape(-1)
        report.observed["first_interval_utc"] = datetime.fromtimestamp(
            int(stamps[0]) / 1000.0, tz=timezone.utc
        ).isoformat()
        report.observed["last_interval_utc"] = datetime.fromtimestamp(
            int(stamps[-1]) / 1000.0, tz=timezone.utc
        ).isoformat()

    n_intervals = int(np.asarray(timestamps).shape[0]) if timestamps is not None else 0
    n_cells = int(np.asarray(cell_ids).shape[0]) if cell_ids is not None else 0
    n_cell_intervals = n_intervals * n_cells
    report.counts = {
        "n_intervals": n_intervals,
        "n_aggregate_demand_points": n_cells,
        "n_cell_interval_records": n_cell_intervals,
        "record_definition": (
            "one record is one (interval, aggregate demand point) pair; an aggregate demand "
            "point is a source grid cell, not a person, a subscriber or a device"
        ),
    }

    # Shapes: the environment's reader refuses a cache whose arrays disagree; a report says so.
    if activity is not None:
        expected = (n_intervals, n_cells)
        got = tuple(int(v) for v in np.asarray(activity).shape)
        report.check("activity.npy shape", declared=list(expected), observed=list(got),
                     agrees=got == expected)
    if observed is not None and activity is not None:
        got_observed = tuple(int(v) for v in np.asarray(observed).shape)
        got_activity = tuple(int(v) for v in np.asarray(activity).shape)
        report.check("observed_mask.npy shape", declared=list(got_activity),
                     observed=list(got_observed), agrees=got_observed == got_activity)
    if positions is not None:
        expected_positions = (n_cells, 2)
        got_positions = tuple(int(v) for v in np.asarray(positions).shape)
        report.check("positions_m.npy shape", declared=list(expected_positions),
                     observed=list(got_positions), agrees=got_positions == expected_positions)

    _prepared_fields(report, timestamps, cell_ids, positions, activity, observed, metadata)
    _prepared_duplicates(report, timestamps, cell_ids)
    _prepared_splits(report, timestamps, splits_doc)
    _prepared_quality_checks(report, quality, activity, observed)

    report.statistical_units = {
        "unit_of_analysis": "one prepared dataset",
        "n_statistical_units": 1,
        "dispersion_across_units": Measured.absent(
            Validity.NOT_APPLICABLE,
            "n=1 prepared dataset: a standard deviation across datasets does not exist; it "
            "is absent, not zero",
        ).to_json(),
        "note": (
            "cell-intervals are not independent replicates: neighbouring cells and adjacent "
            "intervals are correlated by construction, so a count of cell-intervals is not a "
            "sample size for any inference about a method"
        ),
    }
    report.notes.append(
        "ground entities in this dataset are AGGREGATE DEMAND POINTS - one per source grid "
        "cell - and never individual people, subscribers or devices"
    )
    report.notes.append(
        "activity values are source activity units mapped to a simulated demand proxy by "
        "d = alpha * a / s_train; they are not measured Mbps"
    )
    if metadata.get("is_real_activity_data") is False:
        report.notes.append(
            "this cache declares is_real_activity_data = false: it is NOT real activity data "
            "and must never be presented as such"
        )
    historical = (quality or {}).get("historical_period_note")
    if historical:
        report.notes.append(f"declared by the preparation: {historical}")


def _prepared_fields(
    report: DatasetReport,
    timestamps: np.ndarray | None,
    cell_ids: np.ndarray | None,
    positions: np.ndarray | None,
    activity: np.ndarray | None,
    observed: np.ndarray | None,
    metadata: Mapping[str, Any],
) -> None:
    """One :class:`FieldReport` per declared array, with the coverage mask applied."""

    def absent_field(name: str, unit: str | None, reason: str) -> FieldReport:
        absent = Measured.absent(Validity.MISSING_ARTIFACT, reason, unit=unit)
        return FieldReport(
            name=name,
            declared=True,
            observed=False,
            dtype=None,
            unit=unit,
            unit_source=PROV_RECORDED,
            n_records=0,
            n_present=0,
            n_missing=0,
            n_null=0,
            n_non_finite=0,
            missing_treated_as=Validity.MISSING_ARTIFACT.value,
            minimum=absent,
            maximum=absent,
            provenance=PROV_UNKNOWN,
            notes=[reason],
        )

    if timestamps is None:
        report.fields.append(
            absent_field("timestamps_utc_ms", "ms_utc", "declared array is absent from the cache")
        )
    else:
        values = np.asarray(timestamps)
        low, high = _measured_min_max(
            values.astype(np.float64), unit="ms_utc", empty_reason="array is empty"
        )
        report.fields.append(
            FieldReport(
                name="timestamps_utc_ms",
                declared=True,
                observed=True,
                dtype=str(values.dtype),
                unit="ms_utc",
                unit_source=PROV_RECORDED,
                n_records=int(values.shape[0]),
                n_present=int(values.shape[0]),
                n_missing=0,
                n_null=0,
                n_non_finite=0,
                missing_treated_as=Validity.MISSING_ARTIFACT.value,
                minimum=low,
                maximum=high,
                provenance=PROV_OBSERVED,
                notes=["one entry per source interval; every entry exists by construction"],
            )
        )

    if cell_ids is None:
        report.fields.append(
            absent_field("cell_ids", None, "declared array is absent from the cache")
        )
    else:
        values = np.asarray(cell_ids)
        low, high = _measured_min_max(
            values.astype(np.float64), unit=None, empty_reason="array is empty"
        )
        report.fields.append(
            FieldReport(
                name="cell_ids",
                declared=True,
                observed=True,
                dtype=str(values.dtype),
                unit=None,
                unit_source=PROV_RECORDED,
                n_records=int(values.shape[0]),
                n_present=int(values.shape[0]),
                n_missing=0,
                n_null=0,
                n_non_finite=0,
                missing_treated_as=Validity.MISSING_ARTIFACT.value,
                minimum=low,
                maximum=high,
                provenance=PROV_OBSERVED,
                notes=[
                    "categorical source grid cell identifier; the min/max are the identifier "
                    "range and carry no magnitude meaning"
                ],
            )
        )

    if positions is None:
        report.fields.append(absent_field("positions_m", "m", "declared array is absent"))
    else:
        values = np.asarray(positions, dtype=np.float64)
        for axis, label in ((0, "positions_m.x"), (1, "positions_m.y")):
            column = values[:, axis] if values.ndim == 2 and values.shape[1] > axis else values[:0]
            finite = np.isfinite(column)
            low, high = _measured_min_max(
                column[finite], unit="m", empty_reason="no finite coordinate in the array"
            )
            report.fields.append(
                FieldReport(
                    name=label,
                    declared=True,
                    observed=True,
                    dtype=str(values.dtype),
                    unit="m",
                    unit_source=PROV_RECORDED,
                    n_records=int(column.shape[0]),
                    n_present=int(finite.sum()),
                    n_missing=int((~finite).sum()),
                    n_null=0,
                    n_non_finite=int((~finite).sum()),
                    missing_treated_as=Validity.INVALID.value,
                    minimum=low,
                    maximum=high,
                    provenance=PROV_OBSERVED,
                    notes=[
                        "metres in the projected local frame declared by metadata.crs; a "
                        "non-finite coordinate is invalid, not an origin"
                    ],
                )
            )

    if activity is None or observed is None:
        report.fields.append(
            absent_field(
                "activity",
                "activity_units",
                "activity.npy or observed_mask.npy is absent, so coverage cannot be measured",
            )
        )
        return

    values = np.asarray(activity, dtype=np.float64)
    mask = np.asarray(observed, dtype=bool)
    if values.shape != mask.shape:
        report.errors.append(
            f"activity {values.shape} and observed_mask {mask.shape} disagree; per-field "
            "coverage cannot be computed and is reported as unknown rather than assumed"
        )
        report.fields.append(
            absent_field("activity", "activity_units", "coverage mask shape disagrees")
        )
        return

    n_records = int(values.size)
    n_present = int(mask.sum())
    n_missing = n_records - n_present
    present_values = values[mask]
    non_finite = int((~np.isfinite(present_values)).sum()) if present_values.size else 0
    low, high = _measured_min_max(
        present_values,
        unit="activity_units",
        empty_reason="no observed cell-interval in this cache",
    )
    zeros = int((present_values == 0.0).sum()) if present_values.size else 0
    unit_label = str(metadata.get("activity_field") or "activity") + "_activity_units"
    report.fields.append(
        FieldReport(
            name="activity",
            declared=True,
            observed=True,
            dtype=str(values.dtype),
            unit=unit_label,
            unit_source=PROV_RECORDED,
            n_records=n_records,
            n_present=n_present,
            n_missing=n_missing,
            n_null=0,
            n_non_finite=non_finite,
            missing_treated_as=Validity.NOT_RECORDED.value,
            minimum=low,
            maximum=high,
            provenance=PROV_OBSERVED,
            notes=[
                f"{n_missing} of {n_records} cell-intervals have no source record; they are "
                "NOT_RECORDED, not activity of zero",
                f"{zeros} observed cell-intervals carry a measured activity of exactly 0.0; "
                "those are measurements and are counted as present",
                "activity units are not Mbps and not a device or population count",
            ],
        )
    )
    observed_fraction = float(n_present / n_records) if n_records else None
    report.fields.append(
        FieldReport(
            name="observed_mask",
            declared=True,
            observed=True,
            dtype=str(mask.dtype),
            unit="boolean",
            unit_source=PROV_RECORDED,
            n_records=n_records,
            n_present=n_records,
            n_missing=0,
            n_null=0,
            n_non_finite=0,
            missing_treated_as=Validity.MISSING_ARTIFACT.value,
            minimum=Measured.ok(0 if n_missing else 1, source=PROV_OBSERVED),
            maximum=Measured.ok(1 if n_present else 0, source=PROV_OBSERVED),
            provenance=PROV_OBSERVED,
            notes=[
                "the coverage mask itself is complete; it is the activity values it gates "
                "that are missing"
            ],
        )
    )
    report.observed["observed_fraction"] = (
        Measured.ok(observed_fraction, unit="ratio", source=PROV_OBSERVED).to_json()
        if observed_fraction is not None
        else Measured.absent(
            Validity.NOT_APPLICABLE, "the cache holds no cell-interval"
        ).to_json()
    )
    report.observed["n_missing_cell_intervals"] = n_missing
    if mask.size:
        fully_unobserved_cells = int((~mask).all(axis=0).sum())
        fully_unobserved_intervals = int((~mask).all(axis=1).sum())
        report.observed["n_aggregate_demand_points_never_observed"] = fully_unobserved_cells
        report.observed["n_intervals_never_observed"] = fully_unobserved_intervals
        if fully_unobserved_cells:
            report.warnings.append(
                f"{fully_unobserved_cells} aggregate demand points are unobserved in every "
                "interval; their demand is unknown for the whole cache, not zero"
            )
        if fully_unobserved_intervals:
            report.warnings.append(
                f"{fully_unobserved_intervals} intervals have no observed cell at all; an "
                "episode window covering them carries no demand evidence"
            )


def _prepared_duplicates(
    report: DatasetReport, timestamps: np.ndarray | None, cell_ids: np.ndarray | None
) -> None:
    duplicates: dict[str, Any] = {
        "key_rule": (
            "the cache key is (timestamps_utc_ms, cell_ids): timestamps must be strictly "
            "increasing and cell identifiers unique, or a record is ambiguous"
        )
    }
    if cell_ids is None:
        duplicates["cell_ids"] = {"status": "unknown", "reason": "array absent"}
    else:
        values = np.asarray(cell_ids).reshape(-1).tolist()
        count, examples = _duplicate_examples(values)
        duplicates["cell_ids"] = {
            "status": "checked",
            "n_duplicated_values": count,
            "examples": examples,
        }
        if count:
            report.errors.append(
                f"{count} grid cell identifiers occur more than once; two columns of the "
                "activity array claim the same aggregate demand point"
            )
    if timestamps is None:
        duplicates["timestamps_utc_ms"] = {"status": "unknown", "reason": "array absent"}
        report.duplicates = duplicates
        return
    values = np.asarray(timestamps).reshape(-1)
    count, examples = _duplicate_examples(values.tolist())
    diffs = np.diff(values) if values.size > 1 else np.asarray([], dtype=np.int64)
    non_increasing = int((diffs <= 0).sum())
    duplicates["timestamps_utc_ms"] = {
        "status": "checked",
        "n_duplicated_values": count,
        "examples": examples,
        "n_non_increasing_steps": non_increasing,
        "strictly_increasing": bool(non_increasing == 0),
    }
    if non_increasing:
        report.errors.append(
            f"{non_increasing} interval steps are not strictly increasing; the cache's time "
            "axis is ambiguous and the environment's reader refuses it"
        )
    report.duplicates = duplicates


def _prepared_splits(
    report: DatasetReport, timestamps: np.ndarray | None, splits_doc: Mapping[str, Any] | None
) -> None:
    if splits_doc is None:
        report.splits = {
            "status": "missing_artifact",
            "reason": "splits.json is absent or unreadable; split membership is unknown",
        }
        return
    declared = splits_doc.get("splits")
    if not isinstance(declared, Mapping):
        report.splits = {
            "status": "invalid",
            "reason": "splits.json holds no 'splits' object",
        }
        report.errors.append("splits.json holds no 'splits' object")
        return

    date_to_split: dict[str, str] = {}
    overlaps: list[dict[str, str]] = []
    per_split: dict[str, dict[str, Any]] = {}
    for split, dates in declared.items():
        labels = [str(value) for value in (dates or [])]
        per_split[str(split)] = {"n_dates": len(labels), "dates": labels[:MAX_EXAMPLES]}
        for label in labels:
            if label in date_to_split and date_to_split[label] != str(split):
                overlaps.append(
                    {"date": label, "splits": f"{date_to_split[label]}+{split}"}
                )
            date_to_split[label] = str(split)
    if overlaps:
        report.errors.append(
            "splits.json assigns the same date to more than one split; the splits overlap "
            f"({overlaps[:MAX_EXAMPLES]}) and any train/test separation claim over them is void"
        )

    interval_counts: dict[str, int] = {name: 0 for name in per_split}
    unassigned = 0
    if timestamps is not None:
        for value in np.asarray(timestamps).reshape(-1).tolist():
            label = datetime.fromtimestamp(int(value) / 1000.0, tz=timezone.utc).strftime(
                "%Y-%m-%d"
            )
            split = date_to_split.get(label)
            if split is None:
                unassigned += 1
            else:
                interval_counts[split] = interval_counts.get(split, 0) + 1
        for name, count in interval_counts.items():
            per_split[name]["n_intervals"] = count
    else:
        for name in per_split:
            per_split[name]["n_intervals"] = None

    report.splits = {
        "status": "checked",
        "rule": splits_doc.get("rule"),
        "splits": per_split,
        "overlapping_dates": overlaps,
        "n_intervals_in_no_split": unassigned if timestamps is not None else None,
        "n_intervals_in_no_split_status": (
            "observed_in_data" if timestamps is not None else "unknown"
        ),
        "split_membership_rule": (
            "an interval belongs to the split of its UTC date, matching "
            "envs/uav_service_restoration/preprocess_milan.py:utc_date_label"
        ),
    }
    empty = [name for name, info in per_split.items() if not info["n_dates"]]
    if empty:
        report.warnings.append(
            f"these splits are declared but empty: {', '.join(sorted(empty))}; an episode can "
            "never be sampled from them"
        )
    if unassigned:
        report.warnings.append(
            f"{unassigned} intervals fall on a date in no split; they exist in the cache and "
            "are unreachable by episode sampling"
        )


def _prepared_quality_checks(
    report: DatasetReport,
    quality: Mapping[str, Any] | None,
    activity: np.ndarray | None,
    observed: np.ndarray | None,
) -> None:
    """Compare the preparation's own declared counters against what this report observed."""

    if quality is None:
        report.check(
            "quality_report.observed_fraction", declared=None, observed=None, agrees=None
        )
        return
    if observed is None:
        report.check(
            "quality_report.observed_fraction",
            declared=quality.get("observed_fraction"),
            observed=None,
            agrees=None,
        )
        return
    mask = np.asarray(observed, dtype=bool)
    declared_fraction = quality.get("observed_fraction")
    observed_fraction = float(mask.mean()) if mask.size else None
    report.check(
        "quality_report.observed_fraction",
        declared=declared_fraction,
        observed=observed_fraction,
        agrees=(
            None
            if declared_fraction is None or observed_fraction is None
            else math.isclose(float(declared_fraction), observed_fraction, rel_tol=0.0, abs_tol=1e-9)
        ),
    )
    declared_rows = quality.get("aggregated_rows")
    report.check(
        "quality_report.aggregated_rows",
        declared=declared_rows,
        observed=int(mask.sum()),
        agrees=None if declared_rows is None else int(declared_rows) == int(mask.sum()),
    )
    coverage = quality.get("temporal_coverage") or {}
    declared_intervals = coverage.get("n_intervals") if isinstance(coverage, Mapping) else None
    observed_intervals = int(mask.shape[0]) if mask.ndim == 2 else None
    report.check(
        "quality_report.temporal_coverage.n_intervals",
        declared=declared_intervals,
        observed=observed_intervals,
        agrees=(
            None
            if declared_intervals is None or observed_intervals is None
            else int(declared_intervals) == observed_intervals
        ),
    )
    declared_cells = quality.get("n_valid_cells")
    observed_cells = int(mask.shape[1]) if mask.ndim == 2 else None
    report.check(
        "quality_report.n_valid_cells",
        declared=declared_cells,
        observed=observed_cells,
        agrees=(
            None
            if declared_cells is None or observed_cells is None
            else int(declared_cells) == observed_cells
        ),
    )
    if activity is not None and observed is not None:
        values = np.asarray(activity, dtype=np.float64)
        if values.shape == mask.shape and mask.any():
            quantiles = quality.get("activity_quantiles") or {}
            declared_max = quantiles.get("max") if isinstance(quantiles, Mapping) else None
            observed_max = float(values[mask].max())
            report.check(
                "quality_report.activity_quantiles.max",
                declared=declared_max,
                observed=observed_max,
                agrees=(
                    None
                    if declared_max is None
                    else math.isclose(float(declared_max), observed_max, rel_tol=1e-12, abs_tol=0.0)
                ),
            )


# --------------------------------------------------------------------------------------
# Record tables
# --------------------------------------------------------------------------------------


def _sidecar_schema(path: Path, report: DatasetReport) -> dict[str, Any] | None:
    sidecar = path.with_suffix(path.suffix + ".schema.json")
    alternative = path.with_name(path.stem + ".schema.json")
    for candidate in (sidecar, alternative):
        if candidate.is_file():
            payload = _read_json(candidate, report)
            if payload is not None:
                payload.setdefault("_schema_source", str(candidate))
                return payload
    return None


def _declared_fields(schema: Mapping[str, Any] | None) -> tuple[list[str], dict[str, str]]:
    """Field names and units a schema declares, in whichever of the accepted shapes."""

    if not schema:
        return [], {}
    names: list[str] = []
    units: dict[str, str] = {}
    fields = schema.get("fields") or schema.get("columns") or schema.get("schema")
    if isinstance(fields, Mapping):
        for name, spec in fields.items():
            names.append(str(name))
            if isinstance(spec, Mapping) and spec.get("unit"):
                units[str(name)] = str(spec["unit"])
    elif isinstance(fields, (list, tuple)):
        for item in fields:
            if isinstance(item, Mapping) and item.get("name"):
                names.append(str(item["name"]))
                if item.get("unit"):
                    units[str(item["name"])] = str(item["unit"])
            elif isinstance(item, str):
                names.append(item)
    declared_units = schema.get("units")
    if isinstance(declared_units, Mapping):
        for name, unit in declared_units.items():
            units[str(name)] = str(unit)
            if str(name) not in names:
                names.append(str(name))
    return names, units


def _read_jsonl(path: Path, report: DatasetReport) -> tuple[list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    total = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            total += 1
            if len(records) >= MAX_PROFILED_RECORDS:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as error:
                report.errors.append(f"line {line_number}: invalid JSON ({error})")
                continue
            if isinstance(payload, Mapping):
                records.append(dict(payload))
            else:
                report.errors.append(
                    f"line {line_number}: expected a JSON object, found "
                    f"{type(payload).__name__}"
                )
    return records, total


def _read_csv(path: Path, report: DatasetReport) -> tuple[list[dict[str, Any]], int, list[str]]:
    """CSV rows as records. An empty cell is a missing value, never a zero."""

    records: list[dict[str, Any]] = []
    total = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        for row in reader:
            total += 1
            if len(records) >= MAX_PROFILED_RECORDS:
                continue
            record: dict[str, Any] = {}
            for name in header:
                value = row.get(name)
                if value is None or value == "":
                    # Absent on purpose: an empty cell says nothing was recorded.
                    continue
                record[name] = value
            extra = row.get(None)
            if extra:
                report.warnings.append(
                    "a row carries more cells than the header declares; the extras are not "
                    "reported as fields"
                )
            records.append(record)
    if not header:
        report.errors.append("the CSV has no header row, so no field name is declared")
    return records, total, header


def _profile_records(
    report: DatasetReport,
    records: Sequence[Mapping[str, Any]],
    *,
    declared_names: Sequence[str],
    declared_units: Mapping[str, str],
    total_records: int,
) -> None:
    n = len(records)
    observed_names: list[str] = []
    seen: set[str] = set()
    for record in records:
        for key in record:
            name = str(key)
            if name not in seen:
                seen.add(name)
                observed_names.append(name)
    all_names = list(declared_names) + [n for n in observed_names if n not in declared_names]
    truncated = len(all_names) > MAX_REPORTED_FIELDS
    if truncated:
        report.notes.append(
            f"{len(all_names)} distinct fields were seen; the first {MAX_REPORTED_FIELDS} in "
            "declaration-then-first-seen order are reported"
        )
    for name in all_names[:MAX_REPORTED_FIELDS]:
        declared = name in declared_names
        present: list[Any] = []
        n_null = 0
        n_missing = 0
        dtypes: set[str] = set()
        for record in records:
            if name not in record:
                n_missing += 1
                continue
            value = record[name]
            if value is None:
                n_null += 1
                continue
            present.append(value)
            dtypes.add(type(value).__name__)
        numeric: list[float] = []
        n_non_finite = 0
        for value in present:
            if isinstance(value, bool):
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(number):
                numeric.append(number)
            else:
                n_non_finite += 1
        if numeric:
            low, high = _measured_min_max(
                numeric,
                unit=declared_units.get(name),
                empty_reason="no numeric value present",
            )
        elif n_non_finite:
            low = Measured.absent(
                Validity.INVALID,
                f"every numeric value of this field is non-finite ({n_non_finite} of "
                f"{len(present)} present values)",
                unit=declared_units.get(name),
            )
            high = low
        elif present:
            low = Measured.absent(
                Validity.NOT_APPLICABLE,
                "no value of this field is numeric; the range is not applicable",
                unit=declared_units.get(name),
            )
            high = low
        else:
            # A field the schema promised and no record carries is a missing artifact; a
            # field nothing declared is simply not recorded. Neither one is a zero.
            low = Measured.absent(
                Validity.MISSING_ARTIFACT if declared else Validity.NOT_RECORDED,
                (
                    "declared by the schema and present in no record"
                    if declared
                    else "no record carries this field"
                ),
                unit=declared_units.get(name),
            )
            high = low
        unit = declared_units.get(name)
        unit_source = PROV_RECORDED if unit else PROV_UNKNOWN
        if unit is None:
            inferred = _inferred_unit(name)
            if inferred is not None:
                unit, unit_source = inferred, "inferred_from_field_name"
        notes: list[str] = []
        if declared and not present:
            notes.append(
                "declared by the schema and present in no record; this is a missing artifact, "
                "not a value of zero"
            )
        if not declared and declared_names:
            notes.append("present in the data but not declared by the schema")
        if n_null:
            notes.append(f"{n_null} records carry an explicit null for this field")
        if len(dtypes) > 1:
            notes.append(f"mixed value types across records: {sorted(dtypes)}")
        report.fields.append(
            FieldReport(
                name=name,
                declared=declared,
                observed=bool(present) or (n_null > 0),
                dtype="/".join(sorted(dtypes)) if dtypes else None,
                unit=unit,
                unit_source=unit_source,
                n_records=n,
                n_present=len(present),
                n_missing=n_missing,
                n_null=n_null,
                n_non_finite=n_non_finite,
                missing_treated_as=(
                    Validity.MISSING_ARTIFACT.value
                    if declared and not present
                    else Validity.NOT_RECORDED.value
                ),
                minimum=low,
                maximum=high,
                provenance=PROV_OBSERVED if present else PROV_UNKNOWN,
                notes=notes,
            )
        )
    report.observed["observed_fields"] = observed_names[:MAX_REPORTED_FIELDS]
    report.observed["n_observed_fields"] = len(observed_names)
    report.observed["declared_fields_absent_from_every_record"] = [
        name
        for name in declared_names
        if all(name not in record or record[name] is None for record in records)
    ][:MAX_REPORTED_FIELDS]
    report.observed["fields_not_declared"] = [
        name for name in observed_names if declared_names and name not in declared_names
    ][:MAX_REPORTED_FIELDS]
    report.counts = {
        "n_records": total_records,
        "n_records_profiled": n,
        "profile_complete": total_records == n,
        "record_definition": "one record is one row/object of the table",
    }
    if total_records != n:
        report.warnings.append(
            f"{total_records} records exist; coverage counts above describe the first {n} "
            "profiled records only"
        )


def _inferred_unit(name: str) -> str | None:
    """Unit implied by a field name, reusing the readers' shared suffix table."""

    try:
        from .readers import unit_from_key_name
    except ImportError:  # pragma: no cover - the readers package ships with the suite
        return None
    return unit_from_key_name(name)


def _record_duplicates(
    report: DatasetReport,
    records: Sequence[Mapping[str, Any]],
    *,
    declared_keys: Sequence[str],
) -> None:
    key_fields = [name for name in declared_keys if name]
    key_source = "declared by the schema"
    if not key_fields:
        for candidate in _KEY_FIELD_CANDIDATES:
            if records and all(candidate in record for record in records):
                key_fields = [candidate]
                key_source = f"detected: every record carries {candidate!r}"
                break
    if not key_fields:
        serialised = [json.dumps(dict(sorted(record.items())), default=str) for record in records]
        count, examples = _duplicate_examples(serialised)
        report.duplicates = {
            "key_fields": [],
            "key_source": (
                "none: the table declares no key and carries no field present in every "
                "record, so only byte-identical records can be called duplicates"
            ),
            "n_duplicated_keys": count,
            "n_identical_records": count,
            "examples": [{"occurrences": item["occurrences"]} for item in examples],
        }
        if count:
            report.warnings.append(
                f"{count} groups of identical records were found; with no key field this "
                "report cannot say whether they are duplicates or legitimate repeats"
            )
        return
    keys = [
        "|".join(str(record.get(name)) for name in key_fields)
        for record in records
        if all(name in record for name in key_fields)
    ]
    incomplete = len(records) - len(keys)
    count, examples = _duplicate_examples(keys)
    report.duplicates = {
        "key_fields": key_fields,
        "key_source": key_source,
        "n_duplicated_keys": count,
        "n_records_missing_a_key_component": incomplete,
        "examples": examples,
    }
    if count:
        report.errors.append(
            f"{count} key values occur more than once under {key_fields}; a duplicated "
            "identity enters an average twice and silently changes any number computed from "
            "this table"
        )
    if incomplete:
        report.warnings.append(
            f"{incomplete} records lack part of the key {key_fields}; they cannot be checked "
            "for duplication and are not assumed unique"
        )


def _record_splits(report: DatasetReport, records: Sequence[Mapping[str, Any]]) -> None:
    field_name = next(
        (name for name in ("split", "dataset_split", "fold") if any(name in r for r in records)),
        None,
    )
    if field_name is None:
        report.splits = {
            "status": "not_recorded",
            "reason": (
                "no record carries a split field; split membership is unknown, which is not "
                "the same as a single pooled split"
            ),
        }
        return
    per_split: dict[str, int] = {}
    unassigned = 0
    for record in records:
        value = record.get(field_name)
        if value is None:
            unassigned += 1
            continue
        per_split[str(value)] = per_split.get(str(value), 0) + 1
    key_fields = report.duplicates.get("key_fields") or []
    leakage: list[dict[str, Any]] = []
    if key_fields:
        seen: dict[str, str] = {}
        for record in records:
            if any(name not in record for name in key_fields):
                continue
            key = "|".join(str(record.get(name)) for name in key_fields)
            split = str(record.get(field_name))
            if key in seen and seen[key] != split:
                leakage.append({"key": key, "splits": f"{seen[key]}+{split}"})
            seen[key] = split
    report.splits = {
        "status": "checked",
        "split_field": field_name,
        "counts": per_split,
        "n_records_without_a_split": unassigned,
        "keys_in_more_than_one_split": leakage[:MAX_EXAMPLES],
    }
    if leakage:
        report.errors.append(
            f"{len(leakage)} record keys appear in more than one split; the splits are not "
            "disjoint and any held-out claim over them is void"
        )


def _analyse_record_table(path: Path, form: str, report: DatasetReport) -> None:
    schema: dict[str, Any] | None = _sidecar_schema(path, report)
    header: list[str] = []
    if form == "record_table_jsonl":
        records, total = _read_jsonl(path, report)
    elif form == "record_table_csv":
        records, total, header = _read_csv(path, report)
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            raw = payload
        else:
            key = next(k for k in _RECORD_LIST_KEYS if isinstance(payload.get(k), list))
            raw = payload[key]
            if schema is None:
                inline = {
                    name: payload[name]
                    for name in ("schema", "fields", "columns", "units", "key_fields")
                    if name in payload
                }
                schema = inline or None
        records = [dict(item) for item in raw if isinstance(item, Mapping)]
        total = len(raw)
        skipped = total - len(records)
        if skipped:
            report.errors.append(
                f"{skipped} entries of the record list are not JSON objects and were not "
                "profiled; they are not counted as empty records"
            )

    declared_names, declared_units = _declared_fields(schema)
    if form == "record_table_csv" and header and not declared_names:
        declared_names = list(header)
        report.notes.append(
            "the CSV header row is treated as the declared field list; an empty cell is a "
            "missing value for that declared field"
        )
    report.declared = {
        "schema_source": (schema or {}).get("_schema_source", "in-document" if schema else None),
        "schema_status": "declared" if schema or declared_names else "absent",
        "declared_fields": declared_names,
        "declared_units": declared_units,
        "key_fields": list((schema or {}).get("key_fields") or []),
    }
    if not declared_names:
        report.warnings.append(
            "this table declares no schema, so declared-versus-observed cannot be checked; "
            "every field below is reported as observed only"
        )
    report.identity = _manifest_identity([_file_entry(path)])
    report.observed.setdefault("record_count_source", "counted while reading")

    _profile_records(
        report,
        records,
        declared_names=declared_names,
        declared_units=declared_units,
        total_records=total,
    )
    _record_duplicates(report, records, declared_keys=report.declared.get("key_fields") or [])
    _record_splits(report, records)
    if not records:
        report.warnings.append(
            "the table holds no record; every coverage count below is a measured zero over an "
            "empty table, which is not evidence about any field"
        )
    report.statistical_units = {
        "unit_of_analysis": "one record of this table",
        "n_statistical_units": total,
        "note": (
            "a record count is not a replicate count: rows produced by one configuration, one "
            "seed or one training run are repeated measurements of that unit, and only the "
            "table's own identity fields can say which"
        ),
    }
    report.notes.append(
        "ground-entity rows, if this table carries any, describe AGGREGATE DEMAND POINTS "
        "rather than people; check the producing code before reading a count as a population"
    )


def _analyse_seed_list(path: Path, report: DatasetReport) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        key = next(k for k in _SEED_LIST_KEYS if isinstance(payload.get(k), list))
        values = payload[key]
        evidence = f"object key {key!r}"
    else:
        values = payload
        evidence = "top-level array"
    seeds: list[int] = []
    invalid = 0
    for value in values:
        try:
            seeds.append(int(value))
        except (TypeError, ValueError):
            invalid += 1
    if invalid:
        report.errors.append(
            f"{invalid} entries are not integer seeds; they are not counted as episodes"
        )
    report.identity = _manifest_identity([_file_entry(path)])
    report.declared = {
        "schema_status": "implicit",
        "declared_fields": ["episode_seed"],
        "declared_units": {"episode_seed": "rng seed (categorical)"},
        "evidence": evidence,
        "consumer": (
            "scripts/uav_service_restoration/evaluate_baselines.py --episodes-file, which "
            "reads a list or an object with episode_seeds/seeds"
        ),
    }
    low, high = _measured_min_max(
        [float(seed) for seed in seeds],
        unit=None,
        empty_reason="the file lists no integer seed",
    )
    count, examples = _duplicate_examples(seeds)
    report.counts = {
        "n_records": len(seeds),
        "n_records_profiled": len(seeds),
        "profile_complete": True,
        "record_definition": "one record is one episode seed",
    }
    report.fields = [
        FieldReport(
            name="episode_seed",
            declared=True,
            observed=bool(seeds),
            dtype="int",
            unit=None,
            unit_source=PROV_RECORDED,
            n_records=len(values),
            n_present=len(seeds),
            n_missing=invalid,
            n_null=0,
            n_non_finite=0,
            missing_treated_as=Validity.INVALID.value,
            minimum=low,
            maximum=high,
            provenance=PROV_OBSERVED if seeds else PROV_UNKNOWN,
            notes=["a seed is an identifier; its min/max carry no magnitude meaning"],
        )
    ]
    report.duplicates = {
        "key_fields": ["episode_seed"],
        "key_source": "the seed is the episode identity",
        "n_duplicated_keys": count,
        "examples": examples,
    }
    if count:
        report.errors.append(
            f"{count} seeds are repeated; a repeated seed replays the same episode and is not "
            "a second independent observation"
        )
    report.splits = {
        "status": "not_applicable",
        "reason": "a seed list carries no split; the split comes from the scenario config",
    }
    report.statistical_units = {
        "unit_of_analysis": "one evaluation episode of one scenario configuration",
        "n_statistical_units": len(seeds),
        "n_scenario_configurations": Measured.absent(
            Validity.NOT_RECORDED,
            "a seed list names no configuration; the scenario comes from the config passed "
            "beside it",
        ).to_json(),
        "note": (
            "these seeds are episodes of ONE scenario configuration, not independent "
            "replicates of a method: a dispersion computed over them describes within-scenario "
            "variation only"
        ),
    }


# --------------------------------------------------------------------------------------
# Inspection entry point
# --------------------------------------------------------------------------------------


def inspect_dataset(dataset_path: Path) -> DatasetReport:
    """Read a dataset and describe it. Opens files; writes, executes and trains nothing."""

    path = Path(dataset_path)
    form, evidence = detect_form(path)
    report = DatasetReport(
        dataset_path=str(path.resolve()),
        form=form,
        form_evidence=evidence,
    )
    if form == "uav_service_restoration_prepared_cache":
        _analyse_prepared_cache(path, report)
    elif form == "episode_seed_list":
        _analyse_seed_list(path, report)
    else:
        _analyse_record_table(path, form, report)
    report.notes.append(
        "this report opened files to read them; it wrote nothing into the dataset, executed "
        "no checkpoint, constructed no environment and performed zero optimizer updates"
    )
    return report


def dataset_identity_summary(dataset_path: Path) -> dict[str, Any]:
    """Compact identity block for another report that references a dataset.

    Failure is returned as a payload rather than raised: a scenario report that names a
    dataset it cannot read must still be written, saying exactly that.
    """

    path = Path(dataset_path)
    try:
        form, evidence = detect_form(path)
    except CliError as error:
        return {
            "path": str(path),
            "status": "unreadable",
            "form": None,
            "reason": str(error),
        }
    summary: dict[str, Any] = {"path": str(path.resolve()), "status": "read", "form": form,
                               "form_evidence": evidence}
    if form == "uav_service_restoration_prepared_cache":
        metadata_path = path / "metadata.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            summary["status"] = "unreadable"
            summary["reason"] = f"metadata.json: {error}"
            return summary
        summary.update(
            {
                "kind": metadata.get("kind"),
                "is_real_activity_data": metadata.get("is_real_activity_data"),
                "dataset_version": metadata.get("dataset_version"),
                "content_sha256": metadata.get("content_sha256"),
                "activity_reference_scale": metadata.get("activity_reference_scale"),
                "interval_duration_ms": metadata.get("interval_duration_ms"),
                "completion_marker_present": (path / PREPARED_COMPLETION_MARKER).is_file(),
            }
        )
    else:
        summary["sha256"] = _file_entry(path).sha256
    return summary


# --------------------------------------------------------------------------------------
# Self-contained HTML
# --------------------------------------------------------------------------------------

#: One inline stylesheet, shared by this module and ``scenario_report``. No font, image,
#: script or stylesheet is ever fetched: a diagnostic page that phones out is not a
#: diagnostic page.
HTML_STYLE = """
:root { color-scheme: light; }
body { font-family: "Segoe UI", Arial, Helvetica, sans-serif; margin: 0 auto; max-width: 1180px;
       padding: 24px; color: #1b1b1b; background: #ffffff; line-height: 1.45; }
h1 { font-size: 1.6rem; margin-bottom: 0.2rem; }
h2 { font-size: 1.2rem; margin-top: 1.8rem; border-bottom: 2px solid #1b1b1b; padding-bottom: 4px; }
.meta { font-size: 0.86rem; color: #333333; }
.banner { background: #ffe9b0; border: 2px solid #7a0000; color: #7a0000; font-weight: 700;
          padding: 10px 14px; margin: 14px 0; letter-spacing: 0.03em; }
.notes { background: #f4f4f4; border-left: 5px solid #8c8c8c; padding: 10px 14px; margin: 14px 0; }
.errors { background: #fff7f7; border-left: 5px solid #7a0000; padding: 10px 14px; margin: 14px 0; }
.notes ul, .errors ul { margin: 6px 0 0 18px; padding: 0; }
table { border-collapse: collapse; margin: 10px 0; width: 100%; }
td, th { border: 1px solid #dddddd; padding: 3px 8px; text-align: left; vertical-align: top;
         font-size: 0.84rem; }
th { background: #f0f0f0; }
td.absent { color: #7a0000; font-style: italic; }
footer { margin-top: 30px; font-size: 0.8rem; color: #555555; border-top: 1px solid #cccccc;
         padding-top: 10px; }
"""


def escape_cell(value: Any) -> str:
    """HTML-escape a value and neutralise any URL scheme it contains.

    A declared ``source_url`` is data the report displays, not a resource the page loads.
    Escaping the colon keeps the text readable in a browser while leaving no literal
    ``http://`` or ``https://`` in the file, so "this page fetches nothing" stays checkable
    with a plain search of the bytes.
    """

    text = "" if value is None else str(value)
    return html.escape(text, quote=True).replace("://", "&#58;//")


def measured_cell(measured: Measured | Mapping[str, Any] | None) -> str:
    """Render a :class:`Measured` so an absence never looks like a number."""

    if measured is None:
        return '<td class="absent">not reported</td>'
    payload = measured.to_json() if isinstance(measured, Measured) else dict(measured)
    if payload.get("validity") == Validity.OK.value:
        unit = f" {payload['unit']}" if payload.get("unit") else ""
        return f"<td>{escape_cell(payload.get('value'))}{escape_cell(unit)}</td>"
    return (
        f'<td class="absent">{escape_cell(payload.get("validity"))}: '
        f'{escape_cell(payload.get("reason"))}</td>'
    )


def html_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Table from pre-rendered ``<td>`` cells, so a cell can carry its own class."""

    parts = ["<table><thead><tr>"]
    parts += [f"<th>{escape_cell(name)}</th>" for name in headers]
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>" + "".join(row) + "</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def html_document(
    *,
    title: str,
    subtitle: str,
    banners: Sequence[str],
    sections: Sequence[tuple[str, str]],
    data_link: str | None,
    footer: str,
) -> str:
    """One self-contained page: inline style, no script, no fetched resource."""

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{escape_cell(title)}</title>",
        f"<style>{HTML_STYLE}</style>",
        "</head>",
        "<body>",
        f"<h1>{escape_cell(title)}</h1>",
        f'<p class="meta">{escape_cell(subtitle)}</p>',
    ]
    for banner in banners:
        parts.append(f'<p class="banner">{escape_cell(banner)}</p>')
    for heading, body in sections:
        parts.append(f"<h2>{escape_cell(heading)}</h2>")
        parts.append(body)
    if data_link:
        parts.append(
            f'<p class="meta">Machine-readable report: '
            f'<a href="{escape_cell(data_link)}">{escape_cell(data_link)}</a> '
            "(a file beside this one; this page loads nothing over a network).</p>"
        )
    parts.append(f"<footer>{escape_cell(footer)}</footer></body></html>")
    return "\n".join(parts)


def bullet_list(items: Sequence[str], *, css_class: str, empty: str) -> str:
    if not items:
        return f'<p class="meta">{escape_cell(empty)}</p>'
    body = "".join(f"<li>{escape_cell(item)}</li>" for item in items)
    return f'<div class="{css_class}"><ul>{body}</ul></div>'


def _key_value_table(payload: Mapping[str, Any]) -> str:
    rows = []
    for key, value in payload.items():
        if isinstance(value, (Mapping, list, tuple)):
            rendered = json.dumps(value, default=str)[:600]
        else:
            rendered = value
        rows.append([f"<td>{escape_cell(key)}</td>", f"<td>{escape_cell(rendered)}</td>"])
    return html_table(["key", "value"], rows)


def _render_dataset_html(report: DatasetReport, *, data_link: str) -> str:
    banners: list[str] = []
    if report.declared.get("is_real_activity_data") is False:
        banners.append(
            "THIS DATASET DECLARES ITSELF NOT REAL ACTIVITY DATA - it must never be "
            "presented as measured traffic, measured Mbps or a population count"
        )
    if report.errors:
        banners.append(
            "THIS DATASET HAS UNRESOLVED DEFECTS - see the errors section; none of them is "
            "repaired by this report"
        )

    field_rows = []
    for item in report.fields:
        field_rows.append(
            [
                f"<td>{escape_cell(item.name)}</td>",
                f"<td>{escape_cell('yes' if item.declared else 'no')}</td>",
                f"<td>{escape_cell(item.dtype)}</td>",
                f"<td>{escape_cell(item.unit)} <span class='meta'>({escape_cell(item.unit_source)})</span></td>",
                f"<td>{escape_cell(item.n_records)}</td>",
                f"<td>{escape_cell(item.n_present)}</td>",
                (
                    f"<td class='absent'>{escape_cell(item.n_missing)} "
                    f"({escape_cell(item.missing_treated_as)})</td>"
                    if item.n_missing
                    else "<td>0 (none missing)</td>"
                ),
                measured_cell(item.minimum),
                measured_cell(item.maximum),
            ]
        )
    consistency_rows = [
        [
            f"<td>{escape_cell(item.get('check'))}</td>",
            f"<td>{escape_cell(item.get('declared'))}</td>",
            f"<td>{escape_cell(item.get('observed'))}</td>",
            (
                f"<td class='absent'>{escape_cell(item.get('agreement'))}</td>"
                if item.get("agreement") != "match"
                else f"<td>{escape_cell(item.get('agreement'))}</td>"
            ),
        ]
        for item in report.consistency
    ]
    file_rows = [
        [
            f"<td>{escape_cell(Path(entry['path']).name)}</td>",
            f"<td>{escape_cell(entry['bytes'])}</td>",
            f"<td>{escape_cell(entry['mtime_utc'])}</td>",
            f"<td>{escape_cell(entry['sha256'] or entry['sha256_status'])}</td>",
            (
                f"<td>{escape_cell(entry['hash_agreement'])}</td>"
                if entry["hash_agreement"] in ("match", "not_declared")
                else f"<td class='absent'>{escape_cell(entry['hash_agreement'])}</td>"
            ),
        ]
        for entry in report.identity.get("files", [])
    ]

    sections = [
        (
            "Identity",
            _key_value_table(
                {
                    "dataset path": report.dataset_path,
                    "form": report.form,
                    "form evidence": report.form_evidence,
                    "manifest content hash": report.identity.get("manifest_content_hash"),
                }
            )
            + html_table(
                ["file", "bytes", "mtime (UTC)", "sha256", "declared hash"], file_rows
            ),
        ),
        ("Declared", _key_value_table(report.declared)),
        ("Counts", _key_value_table(report.counts)),
        (
            "Fields: coverage and missingness",
            html_table(
                [
                    "field",
                    "declared",
                    "type",
                    "unit",
                    "records",
                    "present",
                    "missing",
                    "minimum",
                    "maximum",
                ],
                field_rows,
            )
            + '<p class="meta">A missing value is an absence with a reason. It is never read '
            "as zero, and a measured zero is counted as present.</p>",
        ),
        ("Declared versus observed", html_table(
            ["check", "declared", "observed", "agreement"], consistency_rows)),
        ("Duplicate keys", _key_value_table(report.duplicates)),
        ("Splits", _key_value_table(report.splits)),
        ("Statistical units", _key_value_table(report.statistical_units)),
        ("Notes", bullet_list(report.notes, css_class="notes", empty="no note")),
        ("Warnings", bullet_list(report.warnings, css_class="notes", empty="no warning")),
        ("Errors", bullet_list(report.errors, css_class="errors", empty="no error")),
    ]
    return html_document(
        title=f"Dataset report: {Path(report.dataset_path).name}",
        subtitle=f"{report.form} - read-only inspection, {DATASET_REPORT_SCHEMA}",
        banners=banners,
        sections=sections,
        data_link=data_link,
        footer=(
            "Generated by tools.research_support.dataset_report. Files were opened for "
            "reading only: nothing was written into the dataset, no checkpoint was executed, "
            "no environment was constructed and zero optimizer updates were performed."
        ),
    )


def write_dataset_report(report: DatasetReport, output_dir: Path) -> Path:
    """Write ``dataset_report.json`` and ``dataset_report.html``; return the HTML path."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    payload = report.to_json()
    payload["report_content_hash"] = content_hash(payload)
    (directory / "dataset_report.json").write_text(dumps(payload, indent=2) + "\n", encoding="utf-8")
    html_path = directory / "dataset_report.html"
    html_path.write_text(
        _render_dataset_html(report, data_link="dataset_report.json"), encoding="utf-8"
    )
    return html_path


def dataset_report(dataset_path: Path, output_dir: Path) -> Path:
    """Inspect one prepared dataset and write the report. Returns the HTML path.

    Raises :class:`~tools.research_support.cli.CliError` when the path does not exist or
    holds no recognised dataset form. There is no fallback to a fixture or a sample.
    """

    return write_dataset_report(inspect_dataset(Path(dataset_path)), Path(output_dir))


__all__ = [
    "DATASET_REPORT_SCHEMA",
    "DatasetReport",
    "FieldReport",
    "FileEntry",
    "dataset_identity_summary",
    "dataset_report",
    "detect_form",
    "inspect_dataset",
    "write_dataset_report",
]
