from pathlib import Path

import pytest

from tools.codex_context_lifecycle.models import (
    ContextSource,
    ContextSourceKind,
    ContextSourceRegistry,
    LoadPolicy,
)
from tools.codex_context_lifecycle.source_registry import (
    RegistryError,
    load_registry,
    sources_for_actor,
    validate_registry,
)
from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.epochs import plan_epoch_current, plan_epoch_open


def _registry(repo_root: Path):
    return load_registry(repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml")


def registry_with_source(
    *,
    actors: tuple[str, ...],
    load_policy: str,
    direction_id: str | None = None,
    scope_key: str | None = None,
) -> ContextSourceRegistry:
    return ContextSourceRegistry(
        schema_version=1,
        registry_revision=1,
        sources=(
            ContextSource(
                id="source-x",
                path="docs/project/source-x.md",
                kind=ContextSourceKind.CANONICAL_OWNER_ARTIFACT,
                owner="test-owner",
                actors=actors,
                load_policy=LoadPolicy(load_policy),
                canonical=False,
                direction_id=direction_id,
                scope_key=scope_key,
            ),
        ),
    )


def test_registry_contains_current_context_foundation_sources(repo_root: Path) -> None:
    registry = load_registry(
        repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
    )
    ids = {item.id for item in registry.sources}
    assert {
        "decision-index",
        "app-server-observer-policy",
        "managed-actor-mailbox-policy",
        "durability-kernel-policy",
    } <= ids


def test_registry_parses_optional_direction_and_scope_fields(tmp_path: Path) -> None:
    path = tmp_path / "registry.toml"
    path.write_text(
        """
schema_version = 1
registry_revision = 1
[[source]]
id = "source-x"
path = "docs/project/source-x.md"
kind = "CANONICAL_OWNER_ARTIFACT"
owner = "test-owner"
actors = ["EM"]
load_policy = "ASSIGNMENT_REFERENCED"
canonical = false
direction_id = "direction:alpha"
scope_key = "scope:one"
""",
        encoding="utf-8",
    )

    source = load_registry(path).sources[0]

    assert source.direction_id == "direction:alpha"
    assert source.scope_key == "scope:one"


def test_direction_scoped_source_is_not_selected_for_other_direction() -> None:
    registry = registry_with_source(
        actors=("EM",),
        direction_id="direction:alpha",
        load_policy="ASSIGNMENT_REFERENCED",
    )
    assert sources_for_actor(
        registry,
        "EM",
        direction_id="direction:beta",
        requested_source_ids=("source-x",),
    ) == ()


def test_scope_scoped_source_is_not_selected_for_other_scope() -> None:
    registry = registry_with_source(
        actors=("EM",),
        scope_key="scope:alpha",
        load_policy="ASSIGNMENT_REFERENCED",
    )
    assert sources_for_actor(
        registry,
        "EM",
        scope_key="scope:beta",
        requested_source_ids=("source-x",),
    ) == ()


def test_operational_root_projection_excludes_em_cm_internals(repo_root: Path) -> None:
    registry = _registry(repo_root)
    assert validate_registry(registry, repo_root) == ()
    sources = sources_for_actor(registry, ActorKind.OPERATIONAL_ROOT)
    ids = {source.id for source in sources}
    assert {
        "root-router",
        "root-role",
        "current-work-index",
        "project-map",
        "portfolio-contract",
    } <= ids
    assert "em-role" not in ids
    assert "cm-role" not in ids
    assert "em-procedure" not in ids
    assert "agent-runtime-context" not in ids


def test_portfolio_projection_excludes_runtime_map(repo_root: Path) -> None:
    registry = _registry(repo_root)
    sources = sources_for_actor(registry, ActorKind.PORTFOLIO)
    ids = {source.id for source in sources}
    assert {
        "root-router",
        "root-role",
        "portfolio-contract",
    } <= ids
    assert "project-map" not in ids
    assert "current-work-index" not in ids
    assert "agent-runtime-context" not in ids
    requested = sources_for_actor(
        registry,
        ActorKind.PORTFOLIO,
        requested_source_ids=("portfolio-reconciliation", "portfolio-handoff-procedure"),
    )
    requested_ids = {source.id for source in requested}
    assert "portfolio-reconciliation" in requested_ids
    assert "portfolio-handoff-procedure" in requested_ids


def test_em_projection_is_assignment_local(repo_root: Path) -> None:
    registry = _registry(repo_root)
    sources = sources_for_actor(registry, ActorKind.EM)
    ids = {source.id for source in sources}
    assert {"root-router", "em-role"} <= ids
    assert "root-role" not in ids
    assert "portfolio-contract" not in ids
    assert "project-map" not in ids
    with_procedure = sources_for_actor(
        registry, ActorKind.EM, requested_source_ids=("em-procedure",)
    )
    assert any(source.id == "em-procedure" for source in with_procedure)


def test_cm_projection_needs_assigned_runtime_and_science_refs(repo_root: Path) -> None:
    registry = _registry(repo_root)
    sources = sources_for_actor(registry, ActorKind.CM)
    ids = {source.id for source in sources}
    assert {"root-router", "cm-role", "project-map"} <= ids
    assert "agent-runtime-context" not in ids
    assigned = sources_for_actor(
        registry,
        ActorKind.CM,
        requested_source_ids=("agent-runtime-context",),
    )
    assert any(source.id == "agent-runtime-context" for source in assigned)


def test_leaf_receives_router_only_until_assignment_refs(repo_root: Path) -> None:
    registry = _registry(repo_root)
    sources = sources_for_actor(registry, ActorKind.LEAF)
    ids = {source.id for source in sources}
    assert ids == {"root-router"}


def test_registry_rejects_duplicate_and_absolute_paths(tmp_path: Path) -> None:
    path = tmp_path / "registry.toml"
    path.write_text(
        """
schema_version = 1
registry_revision = 1
[[source]]
id = "dup"
path = "AGENTS.md"
kind = "ROUTER"
owner = "operational_root"
actors = ["OPERATIONAL_ROOT"]
load_policy = "AUTO_ROUTER"
canonical = true
[[source]]
id = "dup"
path = "C:/Windows/AGENTS.md"
kind = "ROUTER"
owner = "operational_root"
actors = ["OPERATIONAL_ROOT"]
load_policy = "AUTO_ROUTER"
canonical = true
""",
        encoding="utf-8",
    )
    with pytest.raises(RegistryError, match="duplicate source id"):
        load_registry(path)


def test_registry_revision_is_diagnostic_only(repo_root: Path, tmp_path: Path) -> None:
    original = (repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml").read_text(
        encoding="utf-8"
    )
    bumped = original.replace("registry_revision = 1", "registry_revision = 99", 1)
    copy = tmp_path / "CONTEXT_SOURCE_REGISTRY.toml"
    copy.write_text(bumped, encoding="utf-8")
    first = load_registry(repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml")
    second = load_registry(copy)
    assert first.registry_revision != second.registry_revision
    assert [source.id for source in first.sources] == [source.id for source in second.sources]
    root_first = [source.id for source in sources_for_actor(first, ActorKind.OPERATIONAL_ROOT)]
    root_second = [source.id for source in sources_for_actor(second, ActorKind.OPERATIONAL_ROOT)]
    assert root_first == root_second
    assert plan_epoch_current is not None
    assert plan_epoch_open is not None


def test_router_contains_memory_nonauthority_pointer(repo_root: Path) -> None:
    text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "retrieval hints only" in text
    assert "docs/project/CONTEXT_PRECEDENCE.md" in text
    assert text.count("retrieval hints only") == 1


def test_assignment_and_epoch_policies_stay_conditional(repo_root: Path) -> None:
    registry = _registry(repo_root)
    source = next(item for item in registry.sources if item.id == "em-procedure")
    assert source.load_policy is LoadPolicy.EPOCH_REFERENCED
    assert sources_for_actor(registry, ActorKind.EM) == sources_for_actor(
        registry, "EM"
    )
