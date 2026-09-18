"""Static run readers: turn existing result artifacts into evidence-bearing records.

Why this package exists at all: every historical result family in this checkout stores its
identity somewhere different (a legacy CSV filename, a process-core manifest, a diagnostic
evaluation report), and each one is missing a *different* part of the identity a comparison
needs.  Code that reads them ad hoc ends up filling the gaps with today's defaults, which
silently turns "the run never recorded this" into "the run used the current value".  A
reader therefore has three obligations:

1. **Detect by a named artifact, never by a directory-name pattern.**  An unknown schema is
   reported in :attr:`ReadResult.unsupported`, so an arbitrary folder can never become a
   fictitious valid run.
2. **Stay static.**  No agent or environment class is imported, nothing is unpickled, no
   checkpoint is executed, ``torch`` is never touched.  Only JSON, CSV and (if ever needed)
   ``numpy.load(..., allow_pickle=False)``.
3. **Never fabricate.**  An unreadable or absent field becomes
   ``Measured.absent(validity, reason)`` with an evidence location, never a present-day
   default and never a zero.

Outputs are read in place: no reader repairs a manifest, rewrites a historical file, or
backfills a record.  ``coverage`` is deliberately kept to plain JSON-able values (numbers,
strings, bools, lists, dicts) because :func:`tools.research_support.records.dumps` is the
only sanitiser available to callers, and a report writer must be able to embed ``coverage``
without a conversion step.

The concrete readers are imported at the *bottom* of this module: they import the shared
vocabulary from here, so the names below must already exist when they load.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence

from tools.research_support.records import (
    Measured,
    MetricRecord,
    RunRecord,
    Validity,
    content_hash,
    file_hash,
    loads,
)

#: Reader-package version.  Bumped when the normalised output of any reader changes shape,
#: so a cached normalisation can be invalidated by comparing this to its recorded value.
READERS_VERSION = "1"


# --------------------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------------------


class UnsupportedSourceError(RuntimeError):
    """No reader recognises a named artifact under this root.

    Raised instead of returning an empty result, because "there is nothing here I can
    read" and "there is a run here with no metrics" are different facts.
    """


class EpisodeIdentityError(RuntimeError):
    """The source contains rows that cannot be told apart, or lacks the identity columns.

    A duplicated episode identity would enter a mean twice and silently change a published
    number, so the reader refuses the source rather than reporting a warning and continuing.
    This is a refusal to *interpret* a recognised schema, which is why it is not an
    :class:`UnsupportedSourceError`.
    """


# --------------------------------------------------------------------------------------
# The Section 4.1 field vocabulary
# --------------------------------------------------------------------------------------

FIELD_SOURCE_SHA = "source_sha"
FIELD_SOURCE_DIRTY = "source_dirty"
FIELD_ROUTE = "route_or_agent_class"
FIELD_ALGORITHM = "algorithm_label"
FIELD_ENVIRONMENT = "environment_identity"
FIELD_DATASET = "dataset_identity"
FIELD_SPLIT = "dataset_split"
FIELD_REWARD_DEFINITION = "reward_definition"
FIELD_REWARD_SCALE = "reward_scale"
FIELD_UNIT_DEFINITION = "unit_definition"
FIELD_METRIC_SEMANTICS = "metric_semantics"
FIELD_ACTION_SCHEMA = "action_schema"
FIELD_OBSERVATION_SCHEMA = "observation_schema"
FIELD_STATE_SCHEMA = "state_schema"
FIELD_CHECKPOINT_IDENTITY = "checkpoint_identity"
FIELD_CHECKPOINT_SELECTION = "checkpoint_selection_rule"
FIELD_TRAINING_EXPOSURE = "training_exposure"
FIELD_EVALUATION_POLICY_MODE = "evaluation_policy_mode"
FIELD_INFORMATION_CONDITION = "information_condition"
FIELD_TERMINATION_DECLARED = "termination_semantics_declared"
FIELD_TERMINATION_OBSERVED = "termination_semantics_observed"
FIELD_COMPLETION_STATUS = "completion_status"
FIELD_ARTIFACT_LOCATIONS = "artifact_locations"
FIELD_HORIZON = "simulated_horizon"
FIELD_AGENT_COUNT = "agent_count"
FIELD_NORMALIZATION = "normalization"
FIELD_EVALUATION_WORLD = "evaluation_world_identity"
FIELD_EPISODE_INTERVAL = "episode_interval"
FIELD_EVENT_REALIZATION = "event_realization"
FIELD_INITIAL_WORLD_CONFIG = "initial_world_config"
FIELD_TRAINING_SEED = "training_seed"
FIELD_EVALUATION_SEED = "evaluation_seed"
FIELD_STATISTICAL_UNIT = "statistical_unit_kind"

#: Every field a run record is expected to answer, even if the answer is "not recorded".
#: A reader calls :func:`ensure_identity_fields` so a consumer never has to distinguish
#: "the reader forgot" from "the run never recorded it".
RUN_IDENTITY_FIELDS: tuple[str, ...] = (
    FIELD_SOURCE_SHA,
    FIELD_SOURCE_DIRTY,
    FIELD_ROUTE,
    FIELD_ALGORITHM,
    FIELD_ENVIRONMENT,
    FIELD_DATASET,
    FIELD_SPLIT,
    FIELD_REWARD_DEFINITION,
    FIELD_REWARD_SCALE,
    FIELD_UNIT_DEFINITION,
    FIELD_METRIC_SEMANTICS,
    FIELD_ACTION_SCHEMA,
    FIELD_OBSERVATION_SCHEMA,
    FIELD_STATE_SCHEMA,
    FIELD_CHECKPOINT_IDENTITY,
    FIELD_CHECKPOINT_SELECTION,
    FIELD_TRAINING_EXPOSURE,
    FIELD_EVALUATION_POLICY_MODE,
    FIELD_INFORMATION_CONDITION,
    FIELD_TERMINATION_DECLARED,
    FIELD_TERMINATION_OBSERVED,
    FIELD_COMPLETION_STATUS,
    FIELD_ARTIFACT_LOCATIONS,
    FIELD_HORIZON,
    FIELD_AGENT_COUNT,
    FIELD_NORMALIZATION,
    FIELD_EVALUATION_WORLD,
    FIELD_EPISODE_INTERVAL,
    FIELD_EVENT_REALIZATION,
    FIELD_INITIAL_WORLD_CONFIG,
    FIELD_TRAINING_SEED,
    FIELD_EVALUATION_SEED,
    FIELD_STATISTICAL_UNIT,
)

#: Exogenous-world identity (Section 4.1).  Pairing needs *all* of these to agree, with
#: evidence.  Equal integer seeds and equal episode numbers are explicitly not enough:
#: two runs can consume their generators differently and still print seed 7.
WORLD_IDENTITY_FIELDS: tuple[str, ...] = (
    FIELD_DATASET,
    FIELD_EPISODE_INTERVAL,
    FIELD_EVENT_REALIZATION,
    FIELD_INITIAL_WORLD_CONFIG,
)

#: Fields whose difference makes a pooled or paired summary meaningless whatever the
#: specification declares: the numbers being pooled would not be the same quantity.  A
#: declared treatment on one of these is still reported as incomparable, with the
#: declaration named in the detail, because "we meant to change the metric" does not make
#: two different metrics poolable.
INCOMPARABLE_FIELDS: tuple[str, ...] = (
    FIELD_REWARD_DEFINITION,
    FIELD_REWARD_SCALE,
    FIELD_UNIT_DEFINITION,
    FIELD_METRIC_SEMANTICS,
    FIELD_EVALUATION_WORLD,
    FIELD_SPLIT,
)

#: Always reported even when the specification names neither side of them.  A dataset
#: difference and a source-SHA difference are the two things a reader must never leave
#: silent.  Their *classification* still follows the declaration, so a SHA difference is
#: not automatically a confound; see :mod:`tools.research_support.compare`.
ALWAYS_COMPARED_FIELDS: tuple[str, ...] = INCOMPARABLE_FIELDS + (
    FIELD_SOURCE_SHA,
    FIELD_DATASET,
)


def ensure_identity_fields(
    run: RunRecord,
    *,
    reason: str = "field_not_present_in_source",
    evidence: str | None = None,
) -> None:
    """Fill every unset identity field with an explicit ``NOT_RECORDED`` status.

    Called at the end of every reader so that a missing field is a recorded fact with an
    evidence note, rather than a silently absent key that a consumer might default.
    """

    for name in RUN_IDENTITY_FIELDS:
        if name not in run.fields:
            run.set(
                name,
                Measured.not_recorded(reason),
                evidence=evidence or f"absent:{reason}",
            )


# --------------------------------------------------------------------------------------
# Read result
# --------------------------------------------------------------------------------------


@dataclass
class ReadResult:
    """Everything one reader learned from one root, including what it could not read.

    ``coverage`` holds plain JSON-able values only (see the module docstring).  It always
    carries a ``files`` list, one entry per artifact considered, with ``status`` in
    ``parsed`` / ``skipped`` / ``unsupported`` so a report can state what was *not* read.
    """

    run_records: list[RunRecord] = field(default_factory=list)
    metric_records: list[MetricRecord] = field(default_factory=list)
    coverage: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "run_records": [record.to_json() for record in self.run_records],
            "metric_records": [record.to_json() for record in self.metric_records],
            "coverage": self.coverage,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "unsupported": list(self.unsupported),
        }

    # Construction helpers ------------------------------------------------------------

    def note_file(
        self,
        path: Path | str,
        status: str,
        *,
        detail: str | None = None,
        rows: int | None = None,
        digest: str | None = None,
    ) -> None:
        """Record one artifact's fate.  ``status`` is ``parsed``/``skipped``/``unsupported``."""

        entry: dict[str, Any] = {"path": str(path), "status": status}
        if detail is not None:
            entry["detail"] = detail
        if rows is not None:
            entry["rows"] = int(rows)
        if digest is not None:
            entry["sha256"] = digest
        self.coverage.setdefault("files", []).append(entry)
        if status == "unsupported":
            self.unsupported.append(f"{path}: {detail or 'unsupported schema'}")


class Reader(Protocol):
    """Static reader contract.  ``detect`` must be cheap and must require a named artifact."""

    name: str
    version: str

    def detect(self, root: Path) -> bool: ...

    def read(self, root: Path) -> ReadResult: ...


# --------------------------------------------------------------------------------------
# Shared parsing helpers
# --------------------------------------------------------------------------------------


def default_run_id(reader_name: str, root: Path, suffix: str | None = None) -> str:
    """Deterministic, readable run id.  The directory name is the run's local identity."""

    base = root.name or str(root)
    return f"{reader_name}:{base}" + (f":{suffix}" if suffix else "")


def register_source(run: RunRecord, path: Path) -> str | None:
    """Record a file as a source of ``run`` and hash it.  Returns the digest, or ``None``.

    Hashing every file that is read is what lets a later figure point back at the exact
    bytes it came from, and lets a cache notice that the source changed underneath it.
    """

    text = str(path)
    if text not in run.source_paths:
        run.source_paths.append(text)
    try:
        digest = file_hash(text)
    except OSError as error:
        run.warnings.append(f"cannot hash {text}: {error}")
        return None
    run.source_hashes[text] = digest
    return digest


def load_json_file(path: Path) -> tuple[Any, list[str]]:
    """Parse JSON strictly, then permissively, reporting which happened.

    ``records.loads`` refuses the non-standard ``NaN``/``Infinity`` tokens, which is the
    right default for anything this suite writes.  A historical artifact that contains them
    must still be *inspectable*, so a second permissive pass is allowed; every non-finite
    number it produces becomes ``Measured.invalid("non_finite")`` downstream rather than a
    measurement, and the caller is warned that the file is not strict JSON.
    """

    raw = path.read_text(encoding="utf-8")
    try:
        return loads(raw), []
    except ValueError as strict_error:
        try:
            payload = json.loads(raw)
        except ValueError as error:
            raise ValueError(f"{path}: not parseable as JSON: {error}") from error
        return payload, [
            f"{path}: non-standard JSON constants present ({strict_error}); parsed "
            "permissively and non-finite values are reported as invalid, not as measurements"
        ]


def dig(payload: Any, dotted: str, default: Any = None) -> Any:
    """Read ``a.b.c`` out of nested mappings without raising on a missing level."""

    current = payload
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return default
        current = current[part]
    return current


def first_present(payloads: Sequence[tuple[str, Any]], dotted: str) -> tuple[Any, str | None]:
    """First ``(value, evidence)`` for ``dotted`` across ``(label, payload)`` pairs."""

    for label, payload in payloads:
        value = dig(payload, dotted, default=None)
        if value is not None:
            return value, f"{label}:{dotted}"
    return None, None


def measured_text(value: Any, *, evidence: str, absent_reason: str) -> Measured:
    """A recorded string/number/bool, or an explicit absence.  Never a default."""

    if value is None:
        return Measured.not_recorded(absent_reason, source=evidence)
    if isinstance(value, bool):
        return Measured.ok(value, source=evidence)
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            return Measured.invalid("non_finite", source=evidence)
        return Measured.ok(value, source=evidence)
    if isinstance(value, str):
        if not value.strip():
            return Measured.not_recorded(f"empty_string:{absent_reason}", source=evidence)
        return Measured.ok(value, source=evidence)
    if isinstance(value, (list, tuple)):
        if not value:
            return Measured.not_recorded(f"empty_sequence:{absent_reason}", source=evidence)
        return Measured.ok(
            "|".join(str(item) for item in value), source=evidence
        )
    if isinstance(value, Mapping):
        if not value:
            return Measured.not_recorded(f"empty_mapping:{absent_reason}", source=evidence)
        return Measured.ok(
            ";".join(f"{k}={value[k]}" for k in sorted(map(str, value.keys()))),
            source=evidence,
        )
    return Measured.unsupported(f"unsupported_value_type:{type(value).__name__}", source=evidence)


def joined_locations(paths: Iterable[str], *, limit: int = 8) -> str:
    """Compact artifact-location string; the full list stays in ``RunRecord.source_paths``."""

    items = list(paths)
    head = items[:limit]
    text = "|".join(head)
    if len(items) > limit:
        text += f"|(+{len(items) - limit} more; see source_paths)"
    return text


#: Unit hints that key names in this repository actually carry.  This is a documented
#: lower-confidence mapping, used only to label a metric record, never to convert a value.
_UNIT_SUFFIXES: tuple[tuple[str, str], ...] = (
    ("_mbit", "Mbit"),
    ("_mbps", "Mbps"),
    ("_joules", "J"),
    ("_seconds", "s"),
    ("_s", "s"),
    ("_m", "m"),
    ("_ratio", "ratio"),
    ("_fraction", "fraction"),
    ("_count", "count"),
)


def unit_from_key_name(key: str) -> str | None:
    """Unit implied by a key-name suffix, or ``None`` when the name says nothing."""

    lowered = key.lower()
    for suffix, unit in _UNIT_SUFFIXES:
        if lowered.endswith(suffix):
            return unit
        if f"{suffix}_" in lowered:
            return unit
    return None


def flatten_scalars(
    payload: Any,
    *,
    prefix: str = "",
    max_items: int = 4000,
    skip_keys: frozenset[str] = frozenset(),
) -> tuple[list[tuple[str, Any]], list[str]]:
    """Depth-first ``(dotted_path, scalar)`` pairs, plus the paths that were not scalars.

    Lists of numbers (confidence triples, traces) are *not* flattened into fake scalars:
    their paths are returned separately so a report can say "present but not expanded"
    instead of inventing an aggregate.
    """

    out: list[tuple[str, Any]] = []
    skipped: list[str] = []

    def walk(node: Any, path: str) -> None:
        if len(out) >= max_items:
            return
        if isinstance(node, Mapping):
            for key in node:
                if str(key) in skip_keys:
                    continue
                walk(node[key], f"{path}.{key}" if path else str(key))
        elif isinstance(node, (list, tuple)):
            if path:
                skipped.append(f"{path}[{len(node)}]")
        elif isinstance(node, bool) or isinstance(node, (int, float)) or node is None:
            out.append((path, node))
        elif isinstance(node, str):
            skipped.append(f"{path}(str)")
        else:
            skipped.append(f"{path}({type(node).__name__})")

    walk(payload, prefix)
    return out, skipped


# --------------------------------------------------------------------------------------
# Boundary semantics (plan Section 8.2, refs R9/R10)
# --------------------------------------------------------------------------------------

#: Declared GAE boundary switch, recorded in ``TRAINING_MANIFEST_FIELDS`` of
#: ``ha_ctse_process/standalone_manifest.py``.
BOUNDARY_DECLARED_KEY = "legacy_truncation_as_termination"

#: Runtime resolution flags written per update by
#: ``ha_ctse_process/standalone_low_update.py::_boundary_flags``.
BOUNDARY_RUNTIME_KEYS: tuple[str, ...] = (
    "low_boundary_flags_resolved",
    "low_boundary_legacy_collapse",
    "low_truncation_rows",
)


def boundary_semantics(
    found: Mapping[str, tuple[Any, str]],
) -> dict[str, Any]:
    """Declared versus observed episode-boundary semantics.

    ``found`` maps a key name to ``(value, evidence_location)`` for whichever of
    :data:`BOUNDARY_DECLARED_KEY` and :data:`BOUNDARY_RUNTIME_KEYS` the source actually
    recorded.  The asymmetry matters: the declared flag says which arithmetic the run
    *asked* for, while ``low_boundary_flags_resolved`` /
    ``low_boundary_legacy_collapse`` say which arithmetic actually ran.  A run that
    declares the corrected semantics but records no runtime flags may have silently fallen
    back to the collapsed reading, so its observed semantics are **unverified** - not
    "presumed correct".
    """

    def value_of(key: str) -> Any:
        entry = found.get(key)
        return None if entry is None else entry[0]

    def evidence_of(key: str) -> str | None:
        entry = found.get(key)
        return None if entry is None else entry[1]

    declared_value = value_of(BOUNDARY_DECLARED_KEY)
    declared: dict[str, Any] = {
        "key": BOUNDARY_DECLARED_KEY,
        "evidence": evidence_of(BOUNDARY_DECLARED_KEY),
    }
    if declared_value is None:
        declared["status"] = Validity.NOT_RECORDED.value
        declared["value"] = None
        declared["semantics"] = None
        declared["reason"] = (
            f"{BOUNDARY_DECLARED_KEY} is not recorded in this source; the run's intended "
            "boundary arithmetic is unknown"
        )
    else:
        legacy = bool(declared_value)
        declared["status"] = Validity.OK.value
        declared["value"] = legacy
        declared["semantics"] = (
            "collapsed_truncation_as_termination" if legacy else "separate_termination_and_truncation"
        )

    runtime = {key: value_of(key) for key in BOUNDARY_RUNTIME_KEYS}
    runtime_evidence = {key: evidence_of(key) for key in BOUNDARY_RUNTIME_KEYS}
    resolved = runtime["low_boundary_flags_resolved"]
    collapse = runtime["low_boundary_legacy_collapse"]

    observed: dict[str, Any] = {
        "keys": list(BOUNDARY_RUNTIME_KEYS),
        "values": runtime,
        "evidence": runtime_evidence,
    }
    notes: list[str] = []
    if resolved is None and collapse is None:
        observed["status"] = Validity.UNKNOWN.value
        observed["semantics"] = None
        observed["unverified"] = True
        observed["reason"] = (
            "no runtime boundary-resolution flag recorded; actual execution is UNVERIFIED, "
            "not automatically correct"
        )
    else:
        observed["status"] = Validity.OK.value
        observed["unverified"] = False
        if bool(collapse):
            observed["semantics"] = "collapsed_truncation_as_termination"
            notes.append(
                "runtime recorded a deliberate legacy collapse: every boundary was treated "
                "as a real terminal state"
            )
        elif resolved is not None and not bool(resolved):
            observed["semantics"] = "collapsed_fallback_flags_unresolved"
            notes.append(
                "runtime could not separate terminated from truncated and fell back to the "
                "collapsed reading; value targets used termination arithmetic at every boundary"
            )
        else:
            observed["semantics"] = "separate_termination_and_truncation"

    truncation_rows = runtime["low_truncation_rows"]
    if truncation_rows is None:
        observed["truncation_rows"] = None
        observed["truncation_rows_status"] = Validity.NOT_RECORDED.value
    else:
        observed["truncation_rows"] = truncation_rows
        observed["truncation_rows_status"] = Validity.OK.value

    agreement: str
    if declared["semantics"] is None or observed.get("semantics") is None:
        agreement = "unverified"
    elif declared["semantics"] == observed["semantics"]:
        agreement = "declared_matches_observed"
    else:
        agreement = "declared_contradicts_observed"
        notes.append(
            f"declared {declared['semantics']!r} but observed {observed['semantics']!r}: "
            "the manifest asserts semantics the recorded execution did not use"
        )

    return {
        "declared": declared,
        "observed": observed,
        "agreement": agreement,
        "unverified": bool(observed.get("unverified", True)),
        "notes": notes,
    }


def boundary_measures(semantics: Mapping[str, Any]) -> tuple[Measured, Measured]:
    """``(declared, observed)`` as :class:`Measured`, for the run record's two fields."""

    declared = semantics.get("declared", {})
    observed = semantics.get("observed", {})
    if declared.get("semantics") is None:
        declared_measured = Measured.not_recorded(
            str(declared.get("reason") or "boundary_declaration_not_recorded"),
            source=declared.get("evidence"),
        )
    else:
        declared_measured = Measured.ok(
            str(declared["semantics"]), source=declared.get("evidence")
        )
    if observed.get("semantics") is None:
        observed_measured = Measured.unknown(
            str(observed.get("reason") or "boundary_execution_unverified"),
        )
    else:
        observed_measured = Measured.ok(str(observed["semantics"]))
    return declared_measured, observed_measured


def world_identity_hash(parts: Sequence[Any]) -> str:
    """Stable identity for an exogenous-world realisation built from recorded evidence."""

    return content_hash(list(parts))


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------

from tools.research_support.readers.legacy_paper_csv import (  # noqa: E402
    LegacyPaperCsvReader,
)
from tools.research_support.readers.process_core import ProcessCoreReader  # noqa: E402
from tools.research_support.readers.service_restoration import (  # noqa: E402
    ServiceRestorationReader,
)

#: Detection order.  The process-core and service-restoration readers key off distinctive
#: file names, and the legacy reader off a distinctive glob, so the order only matters for
#: a root that deliberately holds more than one family.
READERS: tuple[Reader, ...] = (
    ProcessCoreReader(),
    ServiceRestorationReader(),
    LegacyPaperCsvReader(),
)


def reader_by_name(name: str) -> Reader:
    for reader in READERS:
        if reader.name == name:
            return reader
    known = ", ".join(sorted(item.name for item in READERS))
    raise UnsupportedSourceError(f"unknown reader {name!r}; known readers: {known}")


def detect_reader(root: Path) -> Reader | None:
    """First reader that finds its own named artifact under ``root``, or ``None``.

    ``None`` is the honest answer for an arbitrary directory: no reader may promote a
    path-name pattern into a run.
    """

    root = Path(root)
    if not root.exists():
        return None
    for reader in READERS:
        try:
            if reader.detect(root):
                return reader
        except OSError:
            continue
    return None


def read_run(root: Path, *, reader: str | None = None) -> ReadResult:
    """Read one run root.  An explicit ``reader`` name overrides detection.

    An explicit override is honoured even when detection would have chosen differently -
    that is how a caller tests a new reader against an old root - but the override still
    has to find its artifacts, so ``read`` reports the mismatch rather than inventing one.
    """

    root = Path(root)
    if reader is not None:
        chosen = reader_by_name(reader)
        result = chosen.read(root)
        result.coverage.setdefault("reader_selection", "explicit_override")
        return result
    if not root.exists():
        raise UnsupportedSourceError(f"{root} does not exist")
    detected = detect_reader(root)
    if detected is None:
        raise UnsupportedSourceError(
            f"{root} contains no artifact recognised by any reader "
            f"({', '.join(sorted(item.name for item in READERS))}); "
            "a directory is never read as a run on the strength of its name"
        )
    result = detected.read(root)
    result.coverage.setdefault("reader_selection", "detected")
    return result


__all__ = [
    "ALWAYS_COMPARED_FIELDS",
    "BOUNDARY_DECLARED_KEY",
    "BOUNDARY_RUNTIME_KEYS",
    "EpisodeIdentityError",
    "INCOMPARABLE_FIELDS",
    "LegacyPaperCsvReader",
    "ProcessCoreReader",
    "READERS",
    "READERS_VERSION",
    "RUN_IDENTITY_FIELDS",
    "ReadResult",
    "Reader",
    "ServiceRestorationReader",
    "UnsupportedSourceError",
    "WORLD_IDENTITY_FIELDS",
    "boundary_measures",
    "boundary_semantics",
    "default_run_id",
    "detect_reader",
    "dig",
    "ensure_identity_fields",
    "first_present",
    "flatten_scalars",
    "joined_locations",
    "load_json_file",
    "measured_text",
    "read_run",
    "reader_by_name",
    "register_source",
    "unit_from_key_name",
    "world_identity_hash",
]
