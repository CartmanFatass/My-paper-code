"""Validate ``CURRENT_WORK.md`` as a repository pointer index."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


_CURRENT_WORK_PATH = Path("docs/project/CURRENT_WORK.md")
_LINK = re.compile(r"^- \[([^\]]+)\]\(([^)]+)\)\s*$")
_CANONICAL_PROJECT_STATE = re.compile(r"^## Canonical project state\s*$")
_METADATA_ENTRY = re.compile(r"^([a-z][a-z0-9_]*)=(.*)$")
_TEXT_FENCE = re.compile(r"^```text\s*\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)
_FENCE_START = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_RECORD_ID = re.compile(r"^[a-z0-9_]+$")
_REQUIRED_METADATA_FIELDS = (
    "document_kind",
    "schema_version",
    "index_owner",
    "state_updated",
    "session_record_ids",
    "common_record_ids",
    "legacy_snapshot",
)
_REQUIRED_SESSION_RECORD_IDS = frozenset({"code_project_manager"})
_REQUIRED_COMMON_RECORD_IDS = frozenset(
    {
        "formal_toy_research",
        "uav_validation",
        "explorer_project_validation",
        "independent_research_explorer_pointer",
        "control_plane_runtime",
    }
)


@dataclass(frozen=True)
class CurrentWorkPointer:
    title: str
    path: str
    section: str


def _managed_pointer_path(target: str) -> str | None:
    """Return the repository-relative path for a managed index target."""

    value = target.replace("\\", "/")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value) is not None
    ):
        return None
    if value.startswith("docs/project/"):
        candidate = value
    else:
        candidate = f"docs/project/{value}"
    if not candidate.startswith("docs/project/"):
        return None
    return candidate


def _unfenced_markdown_lines(text: str) -> tuple[str, ...]:
    """Return Markdown source lines while excluding fenced code blocks."""

    lines: list[str] = []
    fence_character = ""
    fence_length = 0
    for line in text.splitlines():
        if fence_character:
            if re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}\s*", line
            ):
                fence_character = ""
                fence_length = 0
            continue
        match = _FENCE_START.match(line)
        if match is not None:
            marker = match.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
            continue
        lines.append(line)
    return tuple(lines)


def collect_current_work(root: Path) -> tuple[CurrentWorkPointer, ...]:
    """Collect strict Markdown-link pointers managed by ``CURRENT_WORK``."""

    index_path = Path(root) / _CURRENT_WORK_PATH
    if not index_path.is_file():
        return ()

    pointers: list[CurrentWorkPointer] = []
    section = ""
    for line in _unfenced_markdown_lines(index_path.read_text(encoding="utf-8")):
        if line.startswith("## "):
            section = line[3:].strip()
        match = _LINK.fullmatch(line)
        if match is None:
            continue
        path = _managed_pointer_path(match.group(2))
        if path is None:
            continue
        pointers.append(
            CurrentWorkPointer(title=match.group(1), path=path, section=section)
        )
    return tuple(pointers)


def _metadata_contract(text: str) -> tuple[dict[str, str], list[str]]:
    """Parse the one required fenced CURRENT_WORK metadata contract."""

    candidates = [
        block.splitlines()
        for block in _TEXT_FENCE.findall(text)
        if any(
            (match := _METADATA_ENTRY.fullmatch(line)) is not None
            and match.group(1) in _REQUIRED_METADATA_FIELDS
            for line in block.splitlines()
        )
    ]
    if not candidates:
        return {}, ["CURRENT_WORK missing fenced metadata contract"]

    errors: list[str] = []
    if len(candidates) != 1:
        errors.append("CURRENT_WORK contains multiple fenced metadata contracts")

    entries: dict[str, list[str]] = {}
    for block in candidates:
        for line in block:
            match = _METADATA_ENTRY.fullmatch(line)
            if match is not None and match.group(1) in _REQUIRED_METADATA_FIELDS:
                entries.setdefault(match.group(1), []).append(match.group(2))

    metadata: dict[str, str] = {}
    for field in _REQUIRED_METADATA_FIELDS:
        values = entries.get(field, [])
        if not values:
            errors.append(f"CURRENT_WORK metadata missing required field: {field}")
            continue
        if len(values) != 1:
            errors.append(f"CURRENT_WORK metadata field is duplicated: {field}")
            continue
        metadata[field] = values[0]

    if metadata.get("document_kind") not in (None, "current_work_index"):
        errors.append("CURRENT_WORK metadata document_kind must be current_work_index")
    if (value := metadata.get("schema_version")) is not None and not value.isdecimal():
        errors.append("CURRENT_WORK metadata schema_version must be an integer")
    if (value := metadata.get("index_owner")) is not None and not value:
        errors.append("CURRENT_WORK metadata index_owner must not be empty")
    if (value := metadata.get("state_updated")) is not None and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", value
    ) is None:
        errors.append("CURRENT_WORK metadata state_updated must use YYYY-MM-DD")
    if (value := metadata.get("legacy_snapshot")) is not None and not value:
        errors.append("CURRENT_WORK metadata legacy_snapshot must not be empty")
    return metadata, errors


def _validate_record_ids(
    metadata: dict[str, str],
    pointers: tuple[CurrentWorkPointer, ...],
    *,
    field: str,
    section: str,
    directory: str,
    required: frozenset[str],
) -> list[str]:
    errors: list[str] = []
    value = metadata.get(field)
    parts = value.split("|") if value else []
    invalid = sorted({part for part in parts if _RECORD_ID.fullmatch(part) is None})
    if invalid:
        errors.append(
            f"CURRENT_WORK {field} contain invalid record IDs: " + ", ".join(invalid)
        )
    duplicates = sorted(
        record_id for record_id, count in Counter(parts).items() if count > 1
    )
    if duplicates:
        errors.append(
            f"CURRENT_WORK {field} contain duplicate record IDs: "
            + ", ".join(duplicates)
        )
    declared = {part for part in parts if _RECORD_ID.fullmatch(part) is not None}

    ids: list[str] = []
    linked_ids: list[str] = []
    managed_paths: list[str] = []
    expected_parent = PurePosixPath(f"docs/project/current-work/{directory}")
    for pointer in pointers:
        path = PurePosixPath(pointer.path)
        if path != expected_parent and expected_parent not in path.parents:
            continue
        managed_paths.append(pointer.path)
        if path.parent != expected_parent or path.suffix != ".md":
            errors.append(
                f"CURRENT_WORK {field} link is not an exact record path: "
                f"{pointer.path}"
            )
            continue
        ids.append(path.stem)
        if pointer.section != section:
            errors.append(
                f"CURRENT_WORK {field} link is outside {section} section: "
                f"{pointer.path}"
            )
        else:
            linked_ids.append(path.stem)
    duplicate_paths = sorted(
        path for path, count in Counter(managed_paths).items() if count > 1
    )
    for path in duplicate_paths:
        errors.append(f"CURRENT_WORK duplicate managed pointer path: {path}")
    duplicates = sorted(
        record_id for record_id, count in Counter(ids).items() if count > 1
    )
    if duplicates:
        errors.append(
            f"CURRENT_WORK {field} contain duplicate linked records: "
            + ", ".join(duplicates)
        )
    linked = set(linked_ids)
    missing_required = sorted(required - declared)
    unexpected = sorted(declared - required)
    missing_linked = sorted(linked - declared)
    unlinked = sorted(declared - linked)
    if missing_required:
        errors.append(
            f"CURRENT_WORK {field} missing required records: "
            + ", ".join(missing_required)
        )
    if unexpected:
        errors.append(
            f"CURRENT_WORK {field} reference undeclared records: "
            + ", ".join(unexpected)
        )
    if missing_linked:
        errors.append(
            f"CURRENT_WORK {field} missing linked records: "
            + ", ".join(missing_linked)
        )
    if unlinked:
        errors.append(
            f"CURRENT_WORK {field} reference unlinked records: "
            + ", ".join(unlinked)
        )
    return errors


def _validate_legacy_snapshot(root: Path, metadata: dict[str, str]) -> list[str]:
    value = metadata.get("legacy_snapshot")
    if not value:
        return []
    normalized = value.replace("\\", "/")
    relative = PurePosixPath(normalized)
    unsafe = (
        relative.is_absolute()
        or ".." in relative.parts
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", normalized) is not None
    )
    if unsafe:
        return [
            "CURRENT_WORK legacy_snapshot is not a safe repository-relative path: "
            + value
        ]

    repo_root = Path(root).resolve()
    target = (repo_root / Path(*relative.parts)).resolve()
    try:
        target.relative_to(repo_root)
    except ValueError:
        return [
            "CURRENT_WORK legacy_snapshot is not a safe repository-relative path: "
            + value
        ]
    if not target.is_file():
        return [
            "CURRENT_WORK legacy_snapshot is not an existing regular file: " + value
        ]
    return []


def validate_current_work(root: Path) -> tuple[str, ...]:
    """Return pointer-index contract violations without changing repository state."""

    index_path = Path(root) / _CURRENT_WORK_PATH
    if not index_path.is_file():
        return ("missing CURRENT_WORK index: docs/project/CURRENT_WORK.md",)

    text = index_path.read_text(encoding="utf-8")
    metadata, errors = _metadata_contract(text)
    markdown_lines = _unfenced_markdown_lines(text)
    if any(_CANONICAL_PROJECT_STATE.fullmatch(line) for line in markdown_lines):
        errors.append("CURRENT_WORK must not contain a Canonical project state section")
    errors.extend(_validate_legacy_snapshot(Path(root), metadata))
    pointers = collect_current_work(root)
    errors.extend(
        _validate_record_ids(
            metadata,
            pointers,
            field="session_record_ids",
            section="Session records",
            directory="sessions",
            required=_REQUIRED_SESSION_RECORD_IDS,
        )
    )
    errors.extend(
        _validate_record_ids(
            metadata,
            pointers,
            field="common_record_ids",
            section="Common records",
            directory="common",
            required=_REQUIRED_COMMON_RECORD_IDS,
        )
    )
    for pointer in pointers:
        if not (Path(root) / pointer.path).is_file():
            errors.append(f"missing CURRENT_WORK target: {pointer.path}")
    return tuple(errors)
