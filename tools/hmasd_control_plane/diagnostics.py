"""Read-only, cross-source diagnostics for the HMASD control plane.

This module intentionally has no repair path.  It reads only control-plane
metadata, never provider archives, prompts, responses, experiment outputs, or
scientific result files.  Source failures are returned as findings so a
partially unavailable installation remains diagnosable.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .long_effect import RUN_FILE_NAMES
from .mcp_runtime import inspect_mcp_instances


DOCTOR_SCHEMA = "HMASD_CONTROL_PLANE_DOCTOR_V1"
COMPONENTS = frozenset(
    {
        "semantic",
        "supervisor",
        "agentify",
        "long-effect",
        "research-events",
        "mcp-runtime",
    }
)
_RESEARCH_EVENTS_REL = Path(
    "docs/research/workflow-runs/2026-08-11_five-round-research-team/events_v2.jsonl"
)
_DEFAULT_LONG_EFFECT_REL = Path("runtime/hmasd-control-plane/long-effects")
_SENSITIVE_AGENTIFY_KEYS = frozenset(
    {
        "prompt",
        "prompttext",
        "prompttextmodel",
        "canonicalprompt",
        "responsetext",
        "assistantresponse",
        "assistanttext",
        "rawresponse",
        "providerprompt",
        "assistantresponsetext",
        "renderedtext",
        "renderedmessage",
        "answertext",
        "outputtext",
    }
)
_SAFE_AGENTIFY_OPERATION_KEYS = frozenset(
    {
        "ambiguousCommitment",
        "createdAt",
        "directionId",
        "failureStage",
        "firstBinding",
        "idempotencyKey",
        "noResend",
        "observeOnly",
        "operationId",
        "sendActionCount",
        "sendCount",
        "status",
        "terminalState",
        "updatedAt",
        "userMessageId",
    }
)
_SAFE_RESEARCH_INCIDENT_KEYS = frozenset(
    {
        "component",
        "direction_id",
        "exact_object",
        "first_seen",
        "incident_id",
        "last_seen",
        "local_fence",
        "observed_fact",
        "owner",
        "resolution",
        "timestamp",
    }
)


@dataclass(frozen=True)
class _SourceResult:
    name: str
    status: str
    details: dict[str, object]
    findings: tuple[dict[str, object], ...] = ()
    incidents: tuple[dict[str, object], ...] = ()
    counters: tuple[tuple[str, int], ...] = ()


def _now_iso(now: datetime | None = None) -> str:
    value = now or datetime.now(timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Agentify records JavaScript epoch milliseconds.
        seconds = float(value) / 1000.0 if abs(float(value)) > 10_000_000_000 else float(value)
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _time_text(value: object, *, fallback: str) -> str:
    parsed = _parse_time(value)
    return fallback if parsed is None else _now_iso(parsed)


def _at_or_after(value: object, since: datetime | None) -> bool:
    if since is None:
        return True
    parsed = _parse_time(value)
    # Unknown timestamps remain visible rather than being silently discarded.
    return parsed is None or parsed >= since


def _stable_id(prefix: str, *parts: object) -> str:
    canonical = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _finding(
    *,
    severity: str,
    component: str,
    exact_object: str,
    observed_fact: str,
    evidence_refs: Sequence[str],
    action_owner: str,
) -> dict[str, object]:
    return {
        "finding_id": _stable_id("finding", component, exact_object, observed_fact),
        "severity": severity,
        "component": component,
        "exact_object": exact_object,
        "observed_fact": observed_fact,
        "evidence_refs": list(evidence_refs),
        "action_owner": action_owner,
    }


def _incident(
    *,
    component: str,
    exact_object: str,
    observed_fact: str,
    local_fence: str,
    owner: str,
    evidence_refs: Sequence[str],
    generated_at: str,
    first_seen: object = None,
    last_seen: object = None,
    direction_id: object = None,
    resolution: object = None,
    incident_id: object = None,
) -> dict[str, object]:
    native_id = str(incident_id).strip() if incident_id is not None else ""
    return {
        "incident_id": native_id or _stable_id("incident", component, exact_object),
        "component": component,
        "direction_id": str(direction_id) if direction_id not in (None, "") else None,
        "exact_object": exact_object,
        "first_seen": _time_text(first_seen, fallback=generated_at),
        "last_seen": _time_text(last_seen if last_seen is not None else first_seen, fallback=generated_at),
        "observed_fact": observed_fact,
        "local_fence": local_fence,
        "owner": owner,
        "resolution": resolution,
        "evidence_refs": list(evidence_refs),
    }


def _source_unavailable(component: str, path: Path, reason: str) -> _SourceResult:
    exact = str(path.resolve(strict=False))
    fact = f"Control-plane source is unavailable ({reason}); no domain conclusion follows."
    finding = _finding(
        severity="ERROR",
        component=component,
        exact_object=exact,
        observed_fact=fact,
        evidence_refs=[exact],
        action_owner="control-plane operator",
    )
    return _SourceResult(
        name=component,
        status="UNAVAILABLE",
        details={"path": exact, "reason": reason},
        findings=(finding,),
    )


def _connect_read_only(path: Path) -> sqlite3.Connection:
    # as_uri handles drive letters and escaping without allowing SQLite to create
    # a missing file.  query_only is an additional defence against accidental DML.
    connection = sqlite3.connect(
        f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=0.0
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA busy_timeout = 0")
    return connection


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }


def _semantic_source(path: Path, since: datetime | None, generated_at: str) -> _SourceResult:
    if not path.is_file():
        return _source_unavailable("semantic", path, "missing")
    try:
        connection = _connect_read_only(path)
        try:
            tables = _table_names(connection)
            required = {"workflows", "tasks", "obligations", "events", "reports"}
            missing = sorted(required - tables)
            if missing:
                raise sqlite3.DatabaseError(f"required tables absent: {','.join(missing)}")
            obligations = connection.execute(
                """SELECT obligation_id, workflow_id, kind, owner, state, created_at,
                          resolved_at
                   FROM obligations WHERE state = 'OPEN' ORDER BY obligation_id"""
            ).fetchall()
            tasks = connection.execute(
                """SELECT task_id, workflow_id, lifecycle, created_at, returned_at
                   FROM tasks
                   WHERE lifecycle NOT IN ('INTAKEN', 'CANCELLED')
                   ORDER BY workflow_id, task_id"""
            ).fetchall()
            workflow_count = int(connection.execute("SELECT COUNT(*) FROM workflows").fetchone()[0])
            report_count = int(connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0])
            event_count = int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])
        finally:
            connection.close()
    except (OSError, sqlite3.Error) as exc:
        return _source_unavailable("semantic", path, type(exc).__name__)

    incidents: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    evidence_base = f"sqlite-ro://{path.resolve()}"
    for row in obligations:
        if not _at_or_after(row["created_at"], since):
            continue
        object_id = f"{row['workflow_id']}/obligation/{row['obligation_id']}"
        fact = (
            f"Semantic obligation remains OPEN (kind={row['kind']}); this is control-plane "
            "delivery debt only and does not imply a scientific pause or failure."
        )
        evidence = [f"{evidence_base}#obligations/{row['obligation_id']}"]
        incidents.append(
            _incident(
                component="semantic",
                exact_object=object_id,
                observed_fact=fact,
                local_fence="Preserve the obligation and its reports until an explicit intake or rollover action.",
                owner=str(row["owner"]),
                evidence_refs=evidence,
                generated_at=generated_at,
                first_seen=row["created_at"],
                last_seen=row["resolved_at"] or row["created_at"],
            )
        )
        findings.append(
            _finding(
                severity="ERROR",
                component="semantic",
                exact_object=object_id,
                observed_fact=fact,
                evidence_refs=evidence,
                action_owner=str(row["owner"]),
            )
        )
    for row in tasks:
        if not _at_or_after(row["created_at"], since):
            continue
        object_id = f"{row['workflow_id']}/task/{row['task_id']}"
        fact = (
            f"Semantic task has unresolved lifecycle={row['lifecycle']}; this is a ledger fact, "
            "not a domain disposition."
        )
        evidence = [f"{evidence_base}#tasks/{row['task_id']}"]
        incidents.append(
            _incident(
                component="semantic",
                exact_object=object_id,
                observed_fact=fact,
                local_fence="Do not infer retry, cancellation, scientific failure, or direction pause.",
                owner="operational Root",
                evidence_refs=evidence,
                generated_at=generated_at,
                first_seen=row["created_at"],
                last_seen=row["returned_at"] or row["created_at"],
            )
        )
        findings.append(
            _finding(
                severity="ERROR",
                component="semantic",
                exact_object=object_id,
                observed_fact=fact,
                evidence_refs=evidence,
                action_owner="operational Root",
            )
        )
    return _SourceResult(
        name="semantic",
        status="ATTENTION" if findings else "OK",
        details={"path": str(path.resolve()), "access": "sqlite-mode-ro"},
        findings=tuple(findings),
        incidents=tuple(incidents),
        counters=(
            ("semantic_workflows", workflow_count),
            ("semantic_reports", report_count),
            ("semantic_events", event_count),
            ("semantic_open_obligations", len(obligations)),
            ("semantic_open_tasks", len(tasks)),
        ),
    )


def _supervisor_home(repo_root: Path) -> Path:
    override = os.environ.get("HMASD_CODEX_SUPERVISOR_HOME")
    if override:
        return Path(override)
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise ValueError("LOCALAPPDATA is unset and HMASD_CODEX_SUPERVISOR_HOME is not set")
    home = Path(local) / "HMASD" / "codex-supervisor"
    try:
        home.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return home
    raise ValueError("supervisor runtime home resolves inside the repository")


def _supervisor_source(repo_root: Path, since: datetime | None, generated_at: str) -> _SourceResult:
    try:
        path = _supervisor_home(repo_root) / "state.sqlite3"
    except ValueError as exc:
        return _source_unavailable("supervisor", repo_root / "<unresolved-supervisor-home>", str(exc))
    if not path.is_file():
        return _source_unavailable("supervisor", path, "missing")
    try:
        connection = _connect_read_only(path)
        try:
            tables = _table_names(connection)
            required_tables = {
                "schema_meta",
                "managed_turn_intents",
                "wake_batches",
                "app_server_effects",
            }
            missing_tables = sorted(required_tables - tables)
            if missing_tables:
                raise sqlite3.DatabaseError(
                    f"required tables absent: {','.join(missing_tables)}"
                )
            specs = (
                ("managed_turn_intents", "turn_intent_id", "submission_state", "prepared_at"),
                ("wake_batches", "wake_batch_id", "state", "prepared_at"),
                ("app_server_effects", "effect_id", "state", "prepared_at"),
            )
            rows: list[tuple[str, sqlite3.Row, str, str, str]] = []
            for table, id_col, state_col, time_col in specs:
                if table not in tables:
                    continue
                query = (
                    f'SELECT "{id_col}" AS object_id, "{state_col}" AS object_state, '
                    f'"{time_col}" AS first_seen FROM "{table}" '
                    "WHERE incident_json IS NOT NULL OR \"" + state_col + "\" = 'INCIDENT' "
                    f'ORDER BY "{id_col}"'
                )
                rows.extend((table, row, id_col, state_col, time_col) for row in connection.execute(query))
            schema_version = int(connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] or 0)
        finally:
            connection.close()
    except (OSError, sqlite3.Error) as exc:
        return _source_unavailable("supervisor", path, type(exc).__name__)

    incidents: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    active_incident_count = 0
    evidence_base = f"sqlite-ro://{path.resolve()}"
    for table, row, _id_col, _state_col, _time_col in rows:
        if not _at_or_after(row["first_seen"], since):
            continue
        object_id = f"{table}/{row['object_id']}"
        object_state = str(row["object_state"])
        active = object_state == "INCIDENT"
        fact = (
            f"Supervisor object has active mechanical state={object_state}; "
            "no scientific or portfolio state is inferred."
            if active
            else (
                f"Supervisor object retains historical incident metadata with current "
                f"mechanical state={object_state}; it is not reported as an active error."
            )
        )
        evidence = [f"{evidence_base}#{table}/{row['object_id']}"]
        incidents.append(
            _incident(
                component="supervisor",
                exact_object=object_id,
                observed_fact=fact,
                local_fence=(
                    "Require explicit operator resolution; do not automatically resubmit the linked effect."
                    if active
                    else "No active operator fence is inferred; retain this resolved incident as history."
                ),
                owner="supervisor operator",
                evidence_refs=evidence,
                generated_at=generated_at,
                first_seen=row["first_seen"],
                resolution=None if active else {"mechanical_state": object_state},
            )
        )
        if active:
            active_incident_count += 1
            findings.append(
                _finding(
                    severity="ERROR",
                    component="supervisor",
                    exact_object=object_id,
                    observed_fact=fact,
                    evidence_refs=evidence,
                    action_owner="supervisor operator",
                )
            )
    return _SourceResult(
        name="supervisor",
        status="ATTENTION" if findings else "OK",
        details={"path": str(path.resolve()), "access": "sqlite-mode-ro", "schema_version": schema_version},
        findings=tuple(findings),
        incidents=tuple(incidents),
        counters=(
            ("supervisor_incidents", len(rows)),
            ("supervisor_active_incidents", active_incident_count),
        ),
    )


def _redacted_object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    # The transport ledger itself is the source.  Sensitive values are discarded
    # during decoding and are never retained in the object graph or diagnostics.
    return {
        key: value
        for key, value in pairs
        if key.lower().replace("_", "") not in _SENSITIVE_AGENTIFY_KEYS
    }


def _agentify_source(path: Path, since: datetime | None, generated_at: str) -> _SourceResult:
    if not path.is_file():
        return _source_unavailable("agentify", path, "missing")
    try:
        with path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream, object_pairs_hook=_redacted_object_pairs)
        operations = payload.get("operations", {}) if isinstance(payload, dict) else {}
        if not isinstance(operations, (dict, list)):
            raise ValueError("operations is neither an object nor an array")
        items = operations.items() if isinstance(operations, dict) else enumerate(operations)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _source_unavailable("agentify", path, type(exc).__name__)

    incidents: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    operation_count = 0
    for key, raw in items:
        operation_count += 1
        if not isinstance(raw, dict):
            continue
        # Admission and incident classification use a closed metadata whitelist.
        # Any future ledger field is ignored until this list is deliberately
        # expanded; prompt/response/display values cannot reach a diagnostic.
        raw = {name: raw[name] for name in _SAFE_AGENTIFY_OPERATION_KEYS if name in raw}
        terminal = str(raw.get("terminalState") or "")
        stage = str(raw.get("failureStage") or "")
        status = str(raw.get("status") or "")
        send_actions = raw.get("sendActionCount", 0)
        explicit_ambiguous = bool(raw.get("ambiguousCommitment")) or bool(raw.get("observeOnly")) or bool(raw.get("noResend"))
        completion_verified = terminal in {
            "NATURAL_COMPLETION_VERIFIED",
            "RESPONSE_COMPLETE_VERIFIED",
        }
        ambiguous = (
            explicit_ambiguous
            or terminal == "SUBMITTED_UNVERIFIED"
            or (stage == "send_occurred_or_uncertain" and not completion_verified)
        )
        timestamp = raw.get("updatedAt") or raw.get("createdAt")
        if not ambiguous or not _at_or_after(timestamp, since):
            continue
        object_id = str(key)
        fact = (
            "Agentify operation has an explicit ambiguous-submission marker "
            f"(status={status or 'unknown'}, terminal={terminal or 'unknown'}, "
            f"failure_stage={stage or 'unknown'}, send_actions={send_actions}); "
            "provider content was not inspected."
        )
        evidence = [f"{path.resolve()}#operations/{object_id}"]
        incidents.append(
            _incident(
                component="agentify",
                exact_object=object_id,
                observed_fact=fact,
                local_fence="Observe only; never resend this exact operation identity.",
                owner="Agentify workflow recovery owner",
                evidence_refs=evidence,
                generated_at=generated_at,
                first_seen=raw.get("createdAt"),
                last_seen=raw.get("updatedAt"),
                direction_id=raw.get("directionId"),
            )
        )
        findings.append(
            _finding(
                severity="ERROR",
                component="agentify",
                exact_object=object_id,
                observed_fact=fact,
                evidence_refs=evidence,
                action_owner="Agentify workflow recovery owner",
            )
        )
    return _SourceResult(
        name="agentify",
        status="ATTENTION" if findings else "OK",
        details={"path": str(path.resolve()), "provider_content_indexed": False},
        findings=tuple(findings),
        incidents=tuple(incidents),
        counters=(("agentify_operations", operation_count), ("agentify_ambiguous_operations", len(incidents))),
    )


def _research_events_source(path: Path, since: datetime | None, generated_at: str) -> _SourceResult:
    if not path.is_file():
        return _source_unavailable("research-events", path, "missing")
    incidents: list[dict[str, object]] = []
    record_count = 0
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                raw = json.loads(
                    line,
                    object_pairs_hook=lambda pairs: {
                        key: value
                        for key, value in pairs
                        if key in _SAFE_RESEARCH_INCIDENT_KEYS
                    },
                )
                if not isinstance(raw, dict):
                    raise ValueError(f"line {line_number} is not an object")
                record_count += 1
                # Routine action/outcome/treatment text is deliberately ignored.
                if not raw.get("incident_id") or not _at_or_after(raw.get("last_seen") or raw.get("timestamp"), since):
                    continue
                component = str(raw.get("component") or "research-events")
                if component not in COMPONENTS:
                    component = "research-events"
                exact_object = str(raw.get("exact_object") or raw["incident_id"])
                incidents.append(
                    _incident(
                        component=component,
                        exact_object=exact_object,
                        observed_fact=str(raw.get("observed_fact") or "Structured incident marker is present in the research event ledger."),
                        local_fence=str(raw.get("local_fence") or "No automatic scientific or portfolio consequence."),
                        owner=str(raw.get("owner") or "operational Root"),
                        evidence_refs=[f"{path.resolve()}#L{line_number}"],
                        generated_at=generated_at,
                        first_seen=raw.get("first_seen") or raw.get("timestamp"),
                        last_seen=raw.get("last_seen") or raw.get("timestamp"),
                        direction_id=raw.get("direction_id"),
                        resolution=raw.get("resolution"),
                        incident_id=raw.get("incident_id"),
                    )
                )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _source_unavailable("research-events", path, type(exc).__name__)
    return _SourceResult(
        name="research-events",
        status="OK",
        details={"path": str(path.resolve()), "indexed_fields": "explicit-incident-fields-only"},
        incidents=tuple(incidents),
        counters=(("research_event_records", record_count), ("research_event_incidents", len(incidents))),
    )


def _discover_run_roots(root: Path) -> list[Path]:
    if (root / "experiment.json").is_file() or (root / "owner.json").is_file():
        return [root]
    if not root.is_dir():
        return []
    # A long-effect collection has one level of fresh run roots.  Never recurse
    # through output references or arbitrary domain directories.
    return sorted(
        child
        for child in root.iterdir()
        if child.is_dir() and ((child / "experiment.json").is_file() or (child / "owner.json").is_file())
    )


def _load_metadata(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not an object")
    return value


def _long_effect_source(roots: Sequence[Path], since: datetime | None, generated_at: str) -> _SourceResult:
    findings: list[dict[str, object]] = []
    incidents: list[dict[str, object]] = []
    unavailable = False
    run_count = 0
    missing_terminal_count = 0
    partial_envelope_count = 0
    source_details: list[dict[str, object]] = []
    for root in roots:
        resolved = root.resolve(strict=False)
        if not root.exists():
            unavailable = True
            unavailable_result = _source_unavailable("long-effect", root, "missing")
            findings.extend(unavailable_result.findings)
            source_details.append({"path": str(resolved), "status": "UNAVAILABLE"})
            continue
        try:
            run_roots = _discover_run_roots(root)
        except OSError as exc:
            unavailable = True
            unavailable_result = _source_unavailable("long-effect", root, type(exc).__name__)
            findings.extend(unavailable_result.findings)
            source_details.append({"path": str(resolved), "status": "UNAVAILABLE"})
            continue
        source_details.append({"path": str(resolved), "status": "OK", "runs": len(run_roots)})
        for run_root in run_roots:
            run_count += 1
            experiment_path = run_root / "experiment.json"
            owner_path = run_root / "owner.json"
            terminal_path = run_root / "terminal.json"
            try:
                present_names = {
                    child.name for child in run_root.iterdir() if child.is_file()
                }
                experiment = (
                    _load_metadata(experiment_path) if experiment_path.is_file() else {}
                )
                owner = _load_metadata(owner_path) if owner_path.is_file() else None
                terminal = (
                    _load_metadata(terminal_path) if terminal_path.is_file() else None
                )
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                unavailable = True
                result = _source_unavailable("long-effect", run_root, type(exc).__name__)
                findings.extend(result.findings)
                continue
            started = (
                owner.get("acquired_at") or owner.get("started_at")
                if isinstance(owner, dict)
                else None
            )
            if not _at_or_after(started, since):
                continue
            experiment_id = str(experiment.get("experiment_id") or run_root.name)
            exact_object = f"{experiment_id}@{run_root.resolve()}"
            metadata = experiment.get("metadata")
            direction_id = (
                metadata.get("direction_id") if isinstance(metadata, dict) else None
            )
            expected_names = set(RUN_FILE_NAMES)
            missing_names = sorted(expected_names - present_names)
            extra_names = sorted(present_names - expected_names)
            owner_without_terminal_only = (
                owner is not None
                and terminal is None
                and missing_names == ["terminal.json"]
                and not extra_names
            )
            if owner_without_terminal_only:
                missing_terminal_count += 1
                fact = (
                    "Long-effect owner record exists while terminal.json is absent; host loss or an "
                    "active child remains mechanically possible, and no domain outcome is inferred."
                )
                evidence = [str(experiment_path.resolve()), str(owner_path.resolve()), str(terminal_path.resolve())]
                incidents.append(
                    _incident(
                        component="long-effect",
                        exact_object=exact_object,
                        observed_fact=fact,
                        local_fence="Do not overwrite this run root or auto-retry; any recovery must use a fresh run root.",
                        owner="long-effect operator",
                        evidence_refs=evidence,
                        generated_at=generated_at,
                        first_seen=started,
                        direction_id=direction_id,
                    )
                )
                findings.append(
                    _finding(
                        severity="ERROR",
                        component="long-effect",
                        exact_object=exact_object,
                        observed_fact=fact,
                        evidence_refs=evidence,
                        action_owner="long-effect operator",
                    )
                )
            elif missing_names or extra_names:
                partial_envelope_count += 1
                fact = (
                    "Long-effect record envelope is mechanically partial "
                    f"(missing={missing_names}, extra={extra_names}); no domain outcome is inferred."
                )
                evidence = [
                    str((run_root / name).resolve())
                    for name in sorted(expected_names | set(extra_names))
                ]
                incidents.append(
                    _incident(
                        component="long-effect",
                        exact_object=exact_object,
                        observed_fact=fact,
                        local_fence=(
                            "Do not overwrite this run root or infer completion; any recovery "
                            "must use a fresh run root."
                        ),
                        owner="long-effect operator",
                        evidence_refs=evidence,
                        generated_at=generated_at,
                        first_seen=started,
                        direction_id=direction_id,
                    )
                )
                findings.append(
                    _finding(
                        severity="ERROR",
                        component="long-effect",
                        exact_object=exact_object,
                        observed_fact=fact,
                        evidence_refs=evidence,
                        action_owner="long-effect operator",
                    )
                )
    status = "UNAVAILABLE" if unavailable else ("ATTENTION" if findings else "OK")
    return _SourceResult(
        name="long-effect",
        status=status,
        details={"roots": source_details, "output_content_indexed": False},
        findings=tuple(findings),
        incidents=tuple(incidents),
        counters=(
            ("long_effect_runs", run_count),
            ("long_effect_missing_terminals", missing_terminal_count),
            ("long_effect_partial_envelopes", partial_envelope_count),
        ),
    )


def _mcp_runtime_source(
    repo_root: Path, since: datetime | None, generated_at: str
) -> _SourceResult:
    """Index runtime-only MCP process evidence without cleaning or signalling it."""

    index = inspect_mcp_instances(repo_root)
    registry_root = str(index["registry_root"])
    if not index.get("registry_exists"):
        return _source_unavailable("mcp-runtime", Path(registry_root), "missing")
    selected: list[Mapping[str, object]] = []
    for item in index["instances"]:
        if not isinstance(item, Mapping):
            continue
        if item.get("status") == "ACTIVE" or _at_or_after(
            item.get("finished_at") or item.get("started_at"), since
        ):
            selected.append(item)

    findings: list[dict[str, object]] = []
    incidents: list[dict[str, object]] = []
    for error in index["record_errors"]:
        if not isinstance(error, Mapping):
            continue
        path = str(error.get("path") or registry_root)
        category = str(error.get("error") or "UnknownRecordError")
        fact = (
            f"MCP runtime lifecycle evidence is unreadable ({category}); "
            "no server, workflow, or scientific disposition follows."
        )
        findings.append(
            _finding(
                severity="ERROR",
                component="mcp-runtime",
                exact_object=path,
                observed_fact=fact,
                evidence_refs=[path],
                action_owner="control-plane operator",
            )
        )
        incidents.append(
            _incident(
                component="mcp-runtime",
                exact_object=path,
                observed_fact=fact,
                local_fence="Do not infer process state from the unreadable record or delete it automatically.",
                owner="control-plane operator",
                evidence_refs=[path],
                generated_at=generated_at,
            )
        )

    counts = {status: 0 for status in ("ACTIVE", "CLOSED", "STALE", "UNKNOWN")}
    for item in selected:
        status = str(item.get("status") or "UNKNOWN")
        counts[status if status in counts else "UNKNOWN"] += 1
        if status not in {"STALE", "UNKNOWN"}:
            continue
        exact = str(item.get("instance_id") or "unknown-instance")
        reason = str(item.get("reason") or "unknown")
        fact = (
            f"MCP instance is {status} ({reason}); this is process-lifecycle evidence only."
        )
        refs = [str(value) for value in item.get("evidence_refs", ())]
        findings.append(
            _finding(
                severity="WARNING",
                component="mcp-runtime",
                exact_object=exact,
                observed_fact=fact,
                evidence_refs=refs,
                action_owner="control-plane operator",
            )
        )
        incidents.append(
            _incident(
                component="mcp-runtime",
                exact_object=exact,
                observed_fact=fact,
                local_fence="Do not restart, terminate, or clean the instance automatically.",
                owner="control-plane operator",
                evidence_refs=refs,
                generated_at=generated_at,
                first_seen=item.get("started_at"),
                last_seen=item.get("finished_at") or generated_at,
            )
        )

    if counts["ACTIVE"] > 1:
        findings.append(
            _finding(
                severity="INFO",
                component="mcp-runtime",
                exact_object=registry_root,
                observed_fact=(
                    f"Observed {counts['ACTIVE']} active stdio MCP instances; "
                    "multiplicity alone is not a singleton or leak failure."
                ),
                evidence_refs=[registry_root],
                action_owner="control-plane operator",
            )
        )

    return _SourceResult(
        name="mcp-runtime",
        status="ATTENTION" if findings else "OK",
        details={"path": registry_root, "schema": index["schema"]},
        findings=tuple(findings),
        incidents=tuple(incidents),
        counters=(
            ("mcp_instances", len(selected)),
            ("mcp_instances_active", counts["ACTIVE"]),
            ("mcp_instances_closed", counts["CLOSED"]),
            ("mcp_instances_stale", counts["STALE"]),
            ("mcp_instances_unknown", counts["UNKNOWN"]),
        ),
    )


def _deduplicate_incidents(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[tuple[str, str], dict[str, object]] = {}
    for record in records:
        key = (str(record["component"]), str(record["exact_object"]))
        existing = merged.get(key)
        if existing is None:
            merged[key] = {**record, "evidence_refs": list(record["evidence_refs"])}
            continue
        first_values = [value for value in (existing.get("first_seen"), record.get("first_seen")) if isinstance(value, str)]
        last_values = [value for value in (existing.get("last_seen"), record.get("last_seen")) if isinstance(value, str)]
        existing["first_seen"] = min(first_values) if first_values else existing.get("first_seen")
        existing["last_seen"] = max(last_values) if last_values else existing.get("last_seen")
        existing["evidence_refs"] = sorted(
            set(str(value) for value in list(existing["evidence_refs"]) + list(record["evidence_refs"]))
        )
        if existing.get("resolution") is None and record.get("resolution") is not None:
            existing["resolution"] = record["resolution"]
    ordered = sorted(
        merged.values(),
        key=lambda item: (str(item["component"]), str(item["exact_object"])),
    )
    ids: dict[str, list[dict[str, object]]] = {}
    for item in ordered:
        ids.setdefault(str(item["incident_id"]), []).append(item)
    for native_id, collisions in ids.items():
        if len(collisions) <= 1:
            continue
        for item in collisions:
            item["incident_id"] = _stable_id(
                "incident",
                native_id,
                item["component"],
                item["exact_object"],
            )
    return ordered


def _collect(
    repo_root: Path,
    *,
    component: str | None,
    since: str | None,
    experiment_roots: Iterable[Path | str],
) -> tuple[dict[str, object], list[dict[str, object]], int]:
    root = Path(repo_root).resolve()
    generated_at = _now_iso()
    if component is not None and component not in COMPONENTS:
        finding = _finding(
            severity="ERROR",
            component="semantic",
            exact_object=f"component:{component}",
            observed_fact="Unknown diagnostics component; no source was read.",
            evidence_refs=[],
            action_owner="control-plane operator",
        )
        doctor = {
            "schema": DOCTOR_SCHEMA,
            "generated_at": generated_at,
            "status": "UNAVAILABLE",
            "sources": {},
            "counters": {},
            "findings": [finding],
        }
        return doctor, [], 2
    since_dt = None
    if since is not None:
        since_dt = _parse_time(since)
        if since_dt is None:
            finding = _finding(
                severity="ERROR",
                component=component or "semantic",
                exact_object=f"since:{since}",
                observed_fact="Invalid ISO-8601 --since value; no source was read.",
                evidence_refs=[],
                action_owner="control-plane operator",
            )
            doctor = {
                "schema": DOCTOR_SCHEMA,
                "generated_at": generated_at,
                "status": "UNAVAILABLE",
                "sources": {},
                "counters": {},
                "findings": [finding],
            }
            return doctor, [], 2

    selected = COMPONENTS if component is None else frozenset({component})
    results: list[_SourceResult] = []
    if "semantic" in selected:
        results.append(_semantic_source(root / "runtime/codex-semantic-mvp/state.sqlite3", since_dt, generated_at))
    if "supervisor" in selected:
        results.append(_supervisor_source(root, since_dt, generated_at))
    if "agentify" in selected:
        state_dir = Path(os.environ.get("AGENTIFY_DESKTOP_STATE_DIR", str(Path.home() / ".agentify-desktop")))
        results.append(_agentify_source(state_dir / "review-transport.json", since_dt, generated_at))
    if "research-events" in selected:
        results.append(_research_events_source(root / _RESEARCH_EVENTS_REL, since_dt, generated_at))
    if "long-effect" in selected:
        supplied = tuple(Path(value) for value in experiment_roots)
        roots = supplied or (root / _DEFAULT_LONG_EFFECT_REL,)
        results.append(_long_effect_source(roots, since_dt, generated_at))
    if "mcp-runtime" in selected:
        results.append(_mcp_runtime_source(root, since_dt, generated_at))

    findings = sorted(
        (finding for result in results for finding in result.findings),
        key=lambda item: (str(item["component"]), str(item["exact_object"]), str(item["finding_id"])),
    )
    incidents = _deduplicate_incidents(incident for result in results for incident in result.incidents)
    sources = {result.name: {"status": result.status, **result.details} for result in results}
    counters: dict[str, int] = {}
    for result in results:
        for name, value in result.counters:
            counters[name] = counters.get(name, 0) + int(value)
    unavailable = any(result.status == "UNAVAILABLE" for result in results)
    has_error = any(finding["severity"] == "ERROR" for finding in findings)
    has_attention = any(
        finding["severity"] in {"WARNING", "ERROR"} for finding in findings
    )
    status = "UNAVAILABLE" if unavailable else ("ATTENTION" if has_attention else "OK")
    exit_code = 2 if unavailable else (1 if has_error else 0)
    doctor = {
        "schema": DOCTOR_SCHEMA,
        "generated_at": generated_at,
        "status": status,
        "sources": sources,
        "counters": counters,
        "findings": findings,
    }
    return doctor, incidents, exit_code


def collect_doctor(
    repo_root: Path,
    *,
    component: str | None = None,
    since: str | None = None,
    experiment_roots: Iterable[Path | str] = (),
) -> tuple[dict[str, object], int]:
    """Collect a read-only doctor snapshot and its process exit classification."""

    doctor, _incidents, exit_code = _collect(
        repo_root,
        component=component,
        since=since,
        experiment_roots=experiment_roots,
    )
    return doctor, exit_code


def collect_incidents(
    repo_root: Path,
    *,
    component: str | None = None,
    since: str | None = None,
    experiment_roots: Iterable[Path | str] = (),
) -> tuple[list[dict[str, object]], int]:
    """Collect the stable deduplicated incident index without modifying sources."""

    _doctor, incidents, exit_code = _collect(
        repo_root,
        component=component,
        since=since,
        experiment_roots=experiment_roots,
    )
    return incidents, exit_code


def diagnostic_exit_code(doctor: Mapping[str, object]) -> int:
    """Classify an already-collected doctor payload using the public contract."""

    if doctor.get("status") == "UNAVAILABLE":
        return 2
    findings = doctor.get("findings", ())
    if isinstance(findings, Sequence) and any(
        isinstance(finding, Mapping) and finding.get("severity") == "ERROR"
        for finding in findings
    ):
        return 1
    return 0
