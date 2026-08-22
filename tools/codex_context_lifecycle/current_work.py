"""Validate ``CURRENT_WORK.md`` as a repository pointer index."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re


_CURRENT_WORK_PATH = Path("docs/project/CURRENT_WORK.md")
_LINK = re.compile(r"^- \[([^\]]+)\]\(([^)]+)\)\s*$")
_CANONICAL_PROJECT_STATE = re.compile(r"^## Canonical project state\s*$")
_COMMON_RECORD_IDS = re.compile(r"^common_record_ids=(.*)$")


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


def collect_current_work(root: Path) -> tuple[CurrentWorkPointer, ...]:
    """Collect strict Markdown-link pointers managed by ``CURRENT_WORK``."""

    index_path = Path(root) / _CURRENT_WORK_PATH
    if not index_path.is_file():
        return ()

    pointers: list[CurrentWorkPointer] = []
    section = ""
    for line in index_path.read_text(encoding="utf-8").splitlines():
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


def validate_current_work(root: Path) -> tuple[str, ...]:
    """Return pointer-index contract violations without changing repository state."""

    index_path = Path(root) / _CURRENT_WORK_PATH
    if not index_path.is_file():
        return ("missing CURRENT_WORK index: docs/project/CURRENT_WORK.md",)

    text = index_path.read_text(encoding="utf-8")
    errors: list[str] = []
    if any(_CANONICAL_PROJECT_STATE.fullmatch(line) for line in text.splitlines()):
        errors.append("CURRENT_WORK must not contain a Canonical project state section")
    pointers = collect_current_work(root)
    metadata_match = next(
        (
            match
            for line in text.splitlines()
            if (match := _COMMON_RECORD_IDS.fullmatch(line)) is not None
        ),
        None,
    )
    if metadata_match is not None:
        declared = {
            record_id
            for record_id in metadata_match.group(1).split("|")
            if record_id
        }
        linked = {
            Path(pointer.path).stem
            for pointer in pointers
            if pointer.section == "Common records"
        }
        missing = sorted(linked - declared)
        extra = sorted(declared - linked)
        if missing:
            errors.append(
                "CURRENT_WORK common_record_ids missing linked records: "
                + ", ".join(missing)
            )
        if extra:
            errors.append(
                "CURRENT_WORK common_record_ids reference unlinked records: "
                + ", ".join(extra)
            )
    for pointer in pointers:
        if not (Path(root) / pointer.path).is_file():
            errors.append(f"missing CURRENT_WORK target: {pointer.path}")
    return tuple(errors)
