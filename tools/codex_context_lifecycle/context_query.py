"""Bounded, deterministic, read-only repository context-foundation queries."""

from __future__ import annotations

from pathlib import Path

from .current_work import collect_current_work, validate_current_work
from .decisions import (
    ALLOWED_STATUSES,
    INDEX_PATH,
    collect_decisions,
    render_decision_index,
)
from .doctor import required_foundation_file_checks
from .models import DecisionRecord
from .project_map import validate_project_map
from .source_registry import (
    DEFAULT_REGISTRY_PATH,
    KNOWN_ACTORS,
    load_registry,
    sources_for_actor,
    validate_registry,
)


PROJECT_MAP_PATH = Path("docs/project/PROJECT_MAP.md")
MAX_ITEMS = 500
MAX_ERRORS = 100
MAX_TEXT_BYTES = 8192
MAX_FIELD_BYTES = 1024
MAX_IDENTIFIER_BYTES = 256


def _bounded_text(value: object, limit: int = MAX_FIELD_BYTES) -> str:
    encoded = str(value).encode("utf-8")
    if len(encoded) <= limit:
        return str(value)
    return encoded[:limit].decode("utf-8", errors="ignore")


def _bounded_errors(errors: tuple[str, ...] | list[str]) -> list[str]:
    return [_bounded_text(error) for error in list(errors)[:MAX_ERRORS]]


def _repository_path(root: Path, path: str) -> str:
    candidate = Path(path).resolve().relative_to(Path(root).resolve())
    return _bounded_text(candidate.as_posix())


def _decision_payload(root: Path, record: DecisionRecord) -> dict[str, object]:
    return {
        "found": True,
        "decision_id": _bounded_text(record.decision_id, MAX_IDENTIFIER_BYTES),
        "title": _bounded_text(record.title),
        "owner": _bounded_text(record.owner, MAX_IDENTIFIER_BYTES),
        "scope": _bounded_text(record.scope),
        "status": _bounded_text(record.status, MAX_IDENTIFIER_BYTES),
        "decision_date": _bounded_text(record.decision_date, MAX_IDENTIFIER_BYTES),
        "supersedes": [
            _bounded_text(item, MAX_IDENTIFIER_BYTES)
            for item in record.supersedes[:MAX_ITEMS]
        ],
        "canonical_sources": [
            _bounded_text(item) for item in record.canonical_sources[:MAX_ITEMS]
        ],
        "revisit_conditions": [
            _bounded_text(item) for item in record.revisit_conditions[:MAX_ITEMS]
        ],
        "path": _repository_path(root, record.path),
    }


def decision_list(root: Path, status: str | None = None) -> list[dict[str, object]]:
    """Return bounded ADR metadata, optionally filtered by exact status."""

    if status is not None and status not in ALLOWED_STATUSES:
        raise ValueError(f"unknown decision status: {_bounded_text(status)}")
    records = collect_decisions(Path(root))
    selected = [record for record in records if status is None or record.status == status]
    return [_decision_payload(Path(root), record) for record in selected[:MAX_ITEMS]]


def decision_get(root: Path, decision_id: str) -> dict[str, object]:
    """Return one exact ADR metadata record without opening a runtime store."""

    bounded_id = _bounded_text(decision_id, MAX_IDENTIFIER_BYTES)
    if bounded_id != decision_id or not decision_id:
        raise ValueError("decision_id must be a non-empty identifier of at most 256 bytes")
    for record in collect_decisions(Path(root)):
        if record.decision_id == decision_id:
            return _decision_payload(Path(root), record)
    return {
        "found": False,
        "decision_id": decision_id,
        "path": None,
    }


def project_map_validate(root: Path) -> dict[str, object]:
    """Return PROJECT_MAP validation findings without changing the map."""

    path = Path(root) / PROJECT_MAP_PATH
    if not path.is_file():
        errors = ("missing PROJECT_MAP: docs/project/PROJECT_MAP.md",)
    else:
        errors = validate_project_map(path)
    return {
        "valid": not errors,
        "path": PROJECT_MAP_PATH.as_posix(),
        "errors": _bounded_errors(errors),
    }


def _bounded_section(text: str) -> str:
    return _bounded_text(text, MAX_TEXT_BYTES)


def project_map_resolve_anchor(root: Path, anchor: str) -> dict[str, object]:
    """Resolve one exact H2 heading and return its bounded section."""

    bounded_anchor = _bounded_text(anchor, MAX_IDENTIFIER_BYTES)
    if bounded_anchor != anchor or not anchor:
        raise ValueError("anchor must be a non-empty heading of at most 256 bytes")
    path = Path(root) / PROJECT_MAP_PATH
    if not path.is_file():
        return {"found": False, "heading": anchor, "line": None, "section_text": ""}

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    expected = f"## {anchor}"
    start: int | None = None
    for index, line in enumerate(lines):
        if line.rstrip("\r\n") == expected:
            start = index
            break
    if start is None:
        return {"found": False, "heading": anchor, "line": None, "section_text": ""}

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return {
        "found": True,
        "heading": anchor,
        "line": start + 1,
        "section_text": _bounded_section("".join(lines[start:end])),
    }


def current_work_index(root: Path) -> list[dict[str, object]]:
    """Return bounded CURRENT_WORK pointers in repository order."""

    return [
        {
            "title": _bounded_text(pointer.title),
            "path": _bounded_text(pointer.path),
            "section": _bounded_text(pointer.section),
        }
        for pointer in collect_current_work(Path(root))[:MAX_ITEMS]
    ]


def context_sources_for_actor(
    root: Path,
    actor: str,
    requested_ids: tuple[str, ...],
) -> list[dict[str, object]]:
    """Return bounded registry sources selected for one exact actor kind."""

    if actor not in KNOWN_ACTORS:
        raise ValueError(f"unknown actor: {_bounded_text(actor)}")
    if len(requested_ids) > MAX_ITEMS:
        raise ValueError(f"requested_ids must contain at most {MAX_ITEMS} items")
    for source_id in requested_ids:
        if not source_id or len(source_id.encode("utf-8")) > MAX_IDENTIFIER_BYTES:
            raise ValueError("requested source IDs must be non-empty and at most 256 bytes")
    registry = load_registry(Path(root) / DEFAULT_REGISTRY_PATH)
    selected = sources_for_actor(
        registry,
        actor,
        requested_source_ids=requested_ids,
    )
    return [
        {
            "id": _bounded_text(source.id, MAX_IDENTIFIER_BYTES),
            "path": _bounded_text(source.path),
            "kind": source.kind.value,
            "owner": _bounded_text(source.owner, MAX_IDENTIFIER_BYTES),
            "actors": list(source.actors[:MAX_ITEMS]),
            "load_policy": source.load_policy.value,
            "canonical": source.canonical,
            "direction_id": _bounded_text(source.direction_id) if source.direction_id else None,
            "scope_key": _bounded_text(source.scope_key) if source.scope_key else None,
        }
        for source in selected[:MAX_ITEMS]
    ]


def context_foundation_health(root: Path) -> dict[str, object]:
    """Derive repository foundation health solely from read-only file checks."""

    repo_root = Path(root)
    components: dict[str, dict[str, object]] = {}
    registry = None
    records = ()

    try:
        registry = load_registry(repo_root / DEFAULT_REGISTRY_PATH)
        registry_errors = validate_registry(registry, repo_root)
        components["context_source_registry"] = {
            "valid": not registry_errors,
            "errors": _bounded_errors(registry_errors),
            "source_count": min(len(registry.sources), MAX_ITEMS),
        }
    except (OSError, ValueError) as exc:
        components["context_source_registry"] = {
            "valid": False,
            "errors": [_bounded_text(exc)],
            "source_count": 0,
        }

    try:
        records = collect_decisions(repo_root)
        decision_errors: list[str] = []
        index_path = repo_root / INDEX_PATH
        if not index_path.is_file():
            decision_errors.append("missing decision index: docs/project/DECISIONS_INDEX.md")
        elif index_path.read_text(encoding="utf-8") != render_decision_index(records):
            decision_errors.append("decision index does not match repository ADRs")
        components["decisions"] = {
            "valid": not decision_errors,
            "errors": _bounded_errors(decision_errors),
            "decision_count": min(len(records), MAX_ITEMS),
        }
    except (OSError, ValueError) as exc:
        components["decisions"] = {
            "valid": False,
            "errors": [_bounded_text(exc)],
            "decision_count": 0,
        }

    required_files = required_foundation_file_checks(repo_root, registry, records)
    required_file_errors: list[str] = []
    if required_files.missing_required_adr_ids:
        required_file_errors.append(
            "required accepted ADRs missing: "
            + ", ".join(required_files.missing_required_adr_ids)
        )
    if required_files.missing_control_plane_source_ids:
        required_file_errors.append(
            "required canonical control-plane sources missing: "
            + ", ".join(required_files.missing_control_plane_source_ids)
        )
    components["required_foundation_files"] = {
        "valid": not required_file_errors,
        "errors": _bounded_errors(required_file_errors),
        "required_adr_ids_present": required_files.required_adr_ids_present,
        "current_control_plane_sources_present": (
            required_files.current_control_plane_sources_present
        ),
    }

    components["project_map"] = project_map_validate(repo_root)
    try:
        current_work_errors = validate_current_work(repo_root)
        pointer_count = len(collect_current_work(repo_root))
        components["current_work"] = {
            "valid": not current_work_errors,
            "errors": _bounded_errors(current_work_errors),
            "pointer_count": min(pointer_count, MAX_ITEMS),
        }
    except (OSError, ValueError) as exc:
        components["current_work"] = {
            "valid": False,
            "errors": [_bounded_text(exc)],
            "pointer_count": 0,
        }

    valid = all(component["valid"] for component in components.values())
    return {
        "status": "OK" if valid else "ERROR",
        "valid": valid,
        "components": components,
    }
