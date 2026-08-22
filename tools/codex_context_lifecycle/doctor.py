"""Read-only doctor for the repository context lifecycle."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 project interpreter
    import tomli as tomllib

from tools.codex_semantic_mvp.db import DEFAULT_STATE_PATH, SCHEMA_VERSION, connect, initialize_database

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
    current_control_plane_sources_present = False
    if registry_path.is_file():
        registry = load_registry(registry_path)
        registry_valid = validate_registry(registry, root) == ()
        sources_by_id = {source.id: source for source in registry.sources}
        required_sources = [
            sources_by_id.get(source_id)
            for source_id in CURRENT_CONTROL_PLANE_SOURCE_IDS
        ]
        current_control_plane_sources_present = all(
            source is not None
            and source.canonical
            and (root / source.path).is_file()
            for source in required_sources
        )
    map_valid = validate_project_map(root / "docs/project/PROJECT_MAP.md") == ()
    index_path = root / "docs/project/DECISIONS_INDEX.md"
    decisions = collect_decisions(root)
    decisions_by_id = {record.decision_id: record for record in decisions}
    required_adr_ids_present = all(
        decision_id in decisions_by_id
        and decisions_by_id[decision_id].status == "accepted"
        for decision_id in REQUIRED_ADR_IDS
    )
    decision_index_current = False
    if index_path.is_file():
        decision_index_current = render_decision_index(decisions) == index_path.read_text(
            encoding="utf-8"
        )
    baseline = root / "docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/REPOSITORY_CONTEXT_LIFECYCLE_BASELINE.md"
    db_path = Path(state_path) if state_path else root / DEFAULT_STATE_PATH
    active_actor_count = 0
    open_promotion_count = 0
    prepared_rollover_count = 0
    archive_candidate_count = 0
    schema_version = SCHEMA_VERSION
    if db_path.exists():
        connection = connect(db_path)
        initialize_database(connection)
        schema_version = int(connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0])
        active_actor_count = connection.execute(
            "SELECT COUNT(*) FROM actor_contexts WHERE state = 'ACTIVE'"
        ).fetchone()[0]
        open_promotion_count = connection.execute(
            "SELECT COUNT(*) FROM promotion_proposals WHERE state IN ('PROPOSED', 'OWNER_ACCEPTED', 'CARRIED_FORWARD')"
        ).fetchone()[0]
        prepared_rollover_count = connection.execute(
            "SELECT COUNT(*) FROM epoch_rollovers WHERE state IN ('PREPARED', 'OWNER_CONFIRMED')"
        ).fetchone()[0]
        archive_candidate_count = connection.execute(
            "SELECT COUNT(*) FROM context_retention_marks WHERE retention_class = 'ARCHIVE_CANDIDATE'"
        ).fetchone()[0]
        connection.close()
    return {
        "schema_version": schema_version,
        "previous_plan_baseline_present": baseline.is_file(),
        "source_registry_valid": registry_valid,
        "project_map_contract_valid": map_valid,
        "current_work_valid": validate_current_work(root) == (),
        "required_adr_ids_present": required_adr_ids_present,
        "current_control_plane_sources_present": current_control_plane_sources_present,
        "behavioral_hooks_disabled": _behavioral_hooks_disabled(root),
        "decision_index_current": decision_index_current,
        "memory_authority": "none",
        "compaction_summary_authority": "none",
        "physical_deletion_enabled": False,
        "active_actor_count": active_actor_count,
        "open_promotion_count": open_promotion_count,
        "prepared_rollover_count": prepared_rollover_count,
        "archive_candidate_count": archive_candidate_count,
    }
