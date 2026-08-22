"""Strict repository context-source registry.

The registry points at existing canonical files. It never copies Role, Skill,
science-card, or portfolio content into SQLite.
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 project interpreter
    import tomli as tomllib

from tools.codex_semantic_mvp.actor_models import ActorKind

from .models import (
    ContextSource,
    ContextSourceKind,
    ContextSourceRegistry,
    LoadPolicy,
)

KNOWN_ACTORS = {member.value for member in ActorKind}
AUTHORITY_KINDS = {
    ContextSourceKind.USER_AUTHORITY,
    ContextSourceKind.ROUTER,
    ContextSourceKind.ROLE_CONTRACT,
    ContextSourceKind.STAGE_OR_PORTFOLIO_CONTRACT,
}
CONDITIONAL_POLICIES = {
    LoadPolicy.ASSIGNMENT_ONLY,
    LoadPolicy.ASSIGNMENT_REFERENCED,
    LoadPolicy.EPOCH_REFERENCED,
}
CONDITIONAL_KINDS = {ContextSourceKind.EXPLICIT_USER_CONTROL_PLANE_CORRECTION}

DEFAULT_REGISTRY_PATH = Path("docs/project/CONTEXT_SOURCE_REGISTRY.toml")


class RegistryError(ValueError):
    """Raised when the context-source registry is invalid."""


def _require_relative(path_text: str) -> str:
    value = str(path_text).replace("\\", "/")
    if Path(value).is_absolute() or value.startswith("/") or (len(value) > 1 and value[1] == ":"):
        raise RegistryError(f"absolute path is forbidden: {path_text}")
    parts = Path(value).parts
    if ".." in parts:
        raise RegistryError(f"parent traversal is forbidden: {path_text}")
    return value


def load_registry(path: Path) -> ContextSourceRegistry:
    raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    sources: list[ContextSource] = []
    seen: set[str] = set()
    for item in raw.get("source") or []:
        source_id = str(item.get("id") or "")
        if not source_id:
            raise RegistryError("source id is required")
        if source_id in seen:
            raise RegistryError(f"duplicate source id: {source_id}")
        seen.add(source_id)
        try:
            kind = ContextSourceKind(str(item.get("kind")))
        except ValueError as exc:
            raise RegistryError(f"unknown source kind: {item.get('kind')}") from exc
        try:
            policy = LoadPolicy(str(item.get("load_policy")))
        except ValueError as exc:
            raise RegistryError(f"unknown load policy: {item.get('load_policy')}") from exc
        actors = tuple(str(actor) for actor in (item.get("actors") or ()))
        unknown = [actor for actor in actors if actor not in KNOWN_ACTORS]
        if unknown:
            raise RegistryError(f"unknown actor names: {', '.join(unknown)}")
        sources.append(
            ContextSource(
                id=source_id,
                path=_require_relative(str(item.get("path") or "")),
                kind=kind,
                owner=str(item.get("owner") or ""),
                actors=actors,
                load_policy=policy,
                canonical=bool(item.get("canonical")),
                direction_id=(
                    str(item["direction_id"]) if "direction_id" in item else None
                ),
                scope_key=str(item["scope_key"]) if "scope_key" in item else None,
            )
        )
    return ContextSourceRegistry(
        schema_version=int(raw.get("schema_version") or 0),
        registry_revision=int(raw.get("registry_revision") or 0),
        sources=tuple(sources),
    )


def validate_registry(registry: ContextSourceRegistry, repo_root: Path) -> tuple[str, ...]:
    errors: list[str] = []
    root = Path(repo_root)
    for source in registry.sources:
        if source.kind in AUTHORITY_KINDS and not source.canonical:
            errors.append(f"{source.id}: authority/role/contract sources must be canonical")
        if source.canonical:
            target = root / source.path
            if not target.is_file():
                errors.append(f"{source.id}: missing canonical file {source.path}")
    return tuple(errors)


def sources_for_actor(
    registry: ContextSourceRegistry,
    actor_kind: ActorKind | str,
    direction_id: str | None = None,
    scope_key: str | None = None,
    requested_source_ids: tuple[str, ...] | list[str] = (),
) -> tuple[ContextSource, ...]:
    kind = actor_kind.value if isinstance(actor_kind, ActorKind) else str(actor_kind)
    requested = set(requested_source_ids)
    selected: list[ContextSource] = []
    for source in registry.sources:
        if kind not in source.actors:
            continue
        if source.direction_id is not None and source.direction_id != direction_id:
            continue
        if source.scope_key is not None and source.scope_key != scope_key:
            continue
        if (
            (source.load_policy in CONDITIONAL_POLICIES or source.kind in CONDITIONAL_KINDS)
            and source.id not in requested
        ):
            continue
        selected.append(source)
    return tuple(selected)
