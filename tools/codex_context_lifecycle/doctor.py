"""Read-only doctor for the repository context lifecycle."""

from __future__ import annotations

from pathlib import Path

from tools.codex_semantic_mvp.db import DEFAULT_STATE_PATH, SCHEMA_VERSION, connect, initialize_database

from .decisions import collect_decisions, render_decision_index
from .project_map import validate_project_map
from .source_registry import load_registry, validate_registry


def collect_doctor(repo_root: Path, state_path: str | Path | None = None) -> dict[str, object]:
    root = Path(repo_root)
    registry_path = root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
    registry_valid = False
    if registry_path.is_file():
        registry = load_registry(registry_path)
        registry_valid = validate_registry(registry, root) == ()
    map_valid = validate_project_map(root / "docs/project/PROJECT_MAP.md") == ()
    index_path = root / "docs/project/DECISIONS_INDEX.md"
    decision_index_current = False
    if index_path.is_file():
        decision_index_current = render_decision_index(collect_decisions(root)) == index_path.read_text(
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
        "decision_index_current": decision_index_current,
        "memory_authority": "none",
        "compaction_summary_authority": "none",
        "physical_deletion_enabled": False,
        "active_actor_count": active_actor_count,
        "open_promotion_count": open_promotion_count,
        "prepared_rollover_count": prepared_rollover_count,
        "archive_candidate_count": archive_candidate_count,
    }
