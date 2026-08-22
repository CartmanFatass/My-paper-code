"""Read-only doctor for the repository context lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 project interpreter
    import tomli as tomllib

from tools.codex_semantic_mvp.db import DEFAULT_STATE_PATH, SCHEMA_VERSION

from .current_work import validate_current_work
from .decisions import collect_decisions, render_decision_index
from .project_map import validate_project_map
from .source_registry import load_registry, validate_registry


REQUIRED_ADR_IDS = frozenset(f"ADR-{number:04d}" for number in range(1, 8))
CURRENT_CONTROL_PLANE_SOURCE_IDS = frozenset(
    {
        "decision-index",
        "app-server-observer-policy",
        "managed-actor-mailbox-policy",
        "durability-kernel-policy",
    }
)


@dataclass(frozen=True)
class RequiredFoundationFileChecks:
    missing_required_adr_ids: tuple[str, ...]
    missing_control_plane_source_ids: tuple[str, ...]

    @property
    def required_adr_ids_present(self) -> bool:
        return not self.missing_required_adr_ids

    @property
    def current_control_plane_sources_present(self) -> bool:
        return not self.missing_control_plane_source_ids


def required_foundation_file_checks(
    root: Path,
    registry,
    decisions,
) -> RequiredFoundationFileChecks:
    """Evaluate required ADR/source presence using repository files only."""

    repo_root = Path(root)
    sources_by_id = (
        {source.id: source for source in registry.sources}
        if registry is not None
        else {}
    )
    decisions_by_id = {record.decision_id: record for record in decisions}
    missing_sources = tuple(
        source_id
        for source_id in sorted(CURRENT_CONTROL_PLANE_SOURCE_IDS)
        if (source := sources_by_id.get(source_id)) is None
        or not source.canonical
        or not (repo_root / source.path).is_file()
    )
    missing_adrs = tuple(
        decision_id
        for decision_id in sorted(REQUIRED_ADR_IDS)
        if decision_id not in decisions_by_id
        or decisions_by_id[decision_id].status != "accepted"
    )
    return RequiredFoundationFileChecks(
        missing_required_adr_ids=missing_adrs,
        missing_control_plane_source_ids=missing_sources,
    )


@dataclass(frozen=True)
class RuntimeStateFacts:
    schema_version: int
    active_actor_count: int
    open_promotion_count: int
    prepared_rollover_count: int
    archive_candidate_count: int
    status: str
    diagnostics: tuple[str, ...]


_RUNTIME_COUNT_QUERIES = (
    (
        "actor_contexts",
        "active_actor_count",
        "SELECT COUNT(*) FROM actor_contexts WHERE state = 'ACTIVE'",
    ),
    (
        "promotion_proposals",
        "open_promotion_count",
        "SELECT COUNT(*) FROM promotion_proposals "
        "WHERE state IN ('PROPOSED', 'OWNER_ACCEPTED', 'CARRIED_FORWARD')",
    ),
    (
        "epoch_rollovers",
        "prepared_rollover_count",
        "SELECT COUNT(*) FROM epoch_rollovers "
        "WHERE state IN ('PREPARED', 'OWNER_CONFIRMED')",
    ),
    (
        "context_retention_marks",
        "archive_candidate_count",
        "SELECT COUNT(*) FROM context_retention_marks "
        "WHERE retention_class = 'ARCHIVE_CANDIDATE'",
    ),
)
_MAX_RUNTIME_DIAGNOSTICS = 5
_MAX_RUNTIME_DIAGNOSTIC_BYTES = 256


def _bounded_runtime_diagnostic(value: object) -> str:
    encoded = str(value).encode("utf-8")
    return encoded[:_MAX_RUNTIME_DIAGNOSTIC_BYTES].decode(
        "utf-8",
        errors="ignore",
    )


def _read_runtime_state(db_path: Path) -> RuntimeStateFacts:
    """Inspect an existing SQLite ledger without creating, migrating, or journaling."""

    defaults = {
        "active_actor_count": 0,
        "open_promotion_count": 0,
        "prepared_rollover_count": 0,
        "archive_candidate_count": 0,
    }
    if not db_path.is_file():
        return RuntimeStateFacts(
            schema_version=SCHEMA_VERSION,
            status="ABSENT",
            diagnostics=(),
            **defaults,
        )

    diagnostics: list[str] = []
    schema_version = 0
    counts = dict(defaults)
    connection: sqlite3.Connection | None = None
    try:
        uri = f"{db_path.resolve().as_uri()}?mode=ro&immutable=1"
        connection = sqlite3.connect(uri, uri=True, isolation_level=None)
        connection.execute("PRAGMA query_only = ON")
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if "schema_meta" not in tables:
            diagnostics.append("missing table: schema_meta")
        else:
            try:
                row = connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()
                schema_version = int((row[0] if row else 0) or 0)
                if schema_version > SCHEMA_VERSION:
                    diagnostics.append(
                        f"schema version {schema_version} exceeds supported {SCHEMA_VERSION}"
                    )
            except (sqlite3.Error, TypeError, ValueError) as exc:
                diagnostics.append(f"schema_meta query unavailable: {exc}")
        for table, field, query in _RUNTIME_COUNT_QUERIES:
            if table not in tables:
                diagnostics.append(f"missing table: {table}")
                continue
            try:
                row = connection.execute(query).fetchone()
                counts[field] = int((row[0] if row else 0) or 0)
            except (sqlite3.Error, TypeError, ValueError) as exc:
                diagnostics.append(f"{table} query unavailable: {exc}")
    except (OSError, sqlite3.Error) as exc:
        diagnostics.append(f"runtime database unreadable: {exc}")
    finally:
        if connection is not None:
            connection.close()

    bounded = tuple(
        _bounded_runtime_diagnostic(item)
        for item in diagnostics[:_MAX_RUNTIME_DIAGNOSTICS]
    )
    return RuntimeStateFacts(
        schema_version=schema_version,
        status="INCOMPATIBLE" if bounded else "READ_ONLY",
        diagnostics=bounded,
        **counts,
    )


def _behavioral_hooks_disabled(root: Path) -> bool:
    config_path = Path(root) / ".codex/config.toml"
    if not config_path.is_file():
        return False
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    features = config.get("features")
    return (
        isinstance(features, dict)
        and features.get("hooks") is False
        and "hooks" not in config
    )


def collect_doctor(repo_root: Path, state_path: str | Path | None = None) -> dict[str, object]:
    root = Path(repo_root)
    registry_path = root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
    registry_valid = False
    registry = None
    if registry_path.is_file():
        registry = load_registry(registry_path)
        registry_valid = validate_registry(registry, root) == ()
    map_valid = validate_project_map(root / "docs/project/PROJECT_MAP.md") == ()
    index_path = root / "docs/project/DECISIONS_INDEX.md"
    decisions = collect_decisions(root)
    required_files = required_foundation_file_checks(
        root,
        registry,
        decisions,
    )
    decision_index_current = False
    if index_path.is_file():
        decision_index_current = render_decision_index(decisions) == index_path.read_text(
            encoding="utf-8"
        )
    baseline = root / "docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/REPOSITORY_CONTEXT_LIFECYCLE_BASELINE.md"
    db_path = Path(state_path) if state_path else root / DEFAULT_STATE_PATH
    runtime_state = _read_runtime_state(db_path)
    return {
        "schema_version": runtime_state.schema_version,
        "previous_plan_baseline_present": baseline.is_file(),
        "source_registry_valid": registry_valid,
        "project_map_contract_valid": map_valid,
        "current_work_valid": validate_current_work(root) == (),
        "required_adr_ids_present": required_files.required_adr_ids_present,
        "current_control_plane_sources_present": required_files.current_control_plane_sources_present,
        "behavioral_hooks_disabled": _behavioral_hooks_disabled(root),
        "decision_index_current": decision_index_current,
        "memory_authority": "none",
        "compaction_summary_authority": "none",
        "physical_deletion_enabled": False,
        "active_actor_count": runtime_state.active_actor_count,
        "open_promotion_count": runtime_state.open_promotion_count,
        "prepared_rollover_count": runtime_state.prepared_rollover_count,
        "archive_candidate_count": runtime_state.archive_candidate_count,
        "runtime_state_status": runtime_state.status,
        "runtime_state_diagnostics": list(runtime_state.diagnostics),
    }
