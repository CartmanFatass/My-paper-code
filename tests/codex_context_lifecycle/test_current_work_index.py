import json
from pathlib import Path

import pytest

from tools.codex_context_lifecycle.cli import main
from tools.codex_context_lifecycle.current_work import (
    CurrentWorkPointer,
    collect_current_work,
    validate_current_work,
)
from tools.codex_context_lifecycle.doctor import collect_doctor


_METADATA = (
    "document_kind=current_work_index",
    "schema_version=4",
    "index_owner=root",
    "state_updated=2026-08-22",
    "session_record_ids=code_project_manager",
    "common_record_ids=formal_toy_research|uav_validation|"
    "explorer_project_validation|independent_research_explorer_pointer|"
    "control_plane_runtime",
    "legacy_snapshot=docs/project/archive/CURRENT_WORK_LEGACY_2026-08-01.md",
)
_COMMON_RECORD_IDS = (
    "formal_toy_research",
    "uav_validation",
    "explorer_project_validation",
    "independent_research_explorer_pointer",
    "control_plane_runtime",
)


def _current_work_text(*body: str, metadata: tuple[str, ...] = _METADATA) -> str:
    return "\n".join(
        (
            "# Current Work",
            "",
            "```text",
            *metadata,
            "```",
            "",
            *body,
            "",
        )
    )


def _canonical_record_sections(
    root: Path, *, missing_targets: frozenset[str] = frozenset()
) -> tuple[str, ...]:
    legacy = root / "docs/project/archive/CURRENT_WORK_LEGACY_2026-08-01.md"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("# Legacy snapshot\n", encoding="utf-8")
    records = (
        ("sessions", "code_project_manager", "Code Project Manager"),
        *(
            ("common", record_id, record_id.replace("_", " ").title())
            for record_id in _COMMON_RECORD_IDS
        ),
    )
    for directory, record_id, _title in records:
        if record_id in missing_targets:
            continue
        target = root / f"docs/project/current-work/{directory}/{record_id}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("owner=test\n", encoding="utf-8")
    return (
        "## Session records",
        "- [Code Project Manager](current-work/sessions/code_project_manager.md)",
        "",
        "## Common records",
        *(
            f"- [{title}](current-work/common/{record_id}.md)"
            for _directory, record_id, title in records[1:]
        ),
    )


def test_current_work_rejects_missing_pointer(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    path.parent.mkdir(parents=True)
    sections = _canonical_record_sections(
        tmp_path, missing_targets=frozenset({"control_plane_runtime"})
    )
    path.write_text(
        _current_work_text(*sections),
        encoding="utf-8",
    )

    assert validate_current_work(tmp_path) == (
        "missing CURRENT_WORK target: docs/project/current-work/common/control_plane_runtime.md",
    )


def test_current_work_rejects_competing_canonical_project_state(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    path.parent.mkdir(parents=True)
    sections = _canonical_record_sections(tmp_path)
    path.write_text(
        _current_work_text("## Canonical project state", *sections), encoding="utf-8"
    )

    assert validate_current_work(tmp_path) == (
        "CURRENT_WORK must not contain a Canonical project state section",
    )


def test_collects_only_strict_project_pointer_links(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    target = tmp_path / "docs/project/current-work/common/runtime.md"
    target.parent.mkdir(parents=True)
    target.write_text("owner=operational_root\n", encoding="utf-8")
    path.write_text(
        _current_work_text(
            "## Common records",
            "- [Runtime](current-work/common/runtime.md)",
            "- [Not strict](current-work/common/runtime.md) trailing",
            "- [External](https://example.test/runtime.md)",
            metadata=tuple(
                "common_record_ids=runtime"
                if line.startswith("common_record_ids=")
                else line
                for line in _METADATA
            ),
        ),
        encoding="utf-8",
    )

    assert collect_current_work(tmp_path) == (
        CurrentWorkPointer(
            title="Runtime",
            path="docs/project/current-work/common/runtime.md",
            section="Common records",
        ),
    )


def test_current_work_rejects_common_record_metadata_missing_linked_record(
    tmp_path: Path,
) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    sections = _canonical_record_sections(tmp_path)
    declared = "|".join(
        record_id for record_id in _COMMON_RECORD_IDS if record_id != "control_plane_runtime"
    )
    path.write_text(
        _current_work_text(
            *sections,
            metadata=tuple(
                f"common_record_ids={declared}"
                if line.startswith("common_record_ids=")
                else line
                for line in _METADATA
            ),
        ),
        encoding="utf-8",
    )

    errors = validate_current_work(tmp_path)
    assert (
        "CURRENT_WORK common_record_ids missing required records: "
        "control_plane_runtime" in errors
    )
    assert (
        "CURRENT_WORK common_record_ids missing linked records: "
        "control_plane_runtime" in errors
    )


def test_current_work_rejects_header_only_document(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Current Work\n", encoding="utf-8")

    errors = validate_current_work(tmp_path)

    assert "CURRENT_WORK missing fenced metadata contract" in errors


@pytest.mark.parametrize(
    "missing_key",
    (
        "document_kind",
        "schema_version",
        "index_owner",
        "state_updated",
        "session_record_ids",
        "common_record_ids",
        "legacy_snapshot",
    ),
)
def test_current_work_rejects_each_missing_metadata_line(
    tmp_path: Path, missing_key: str
) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    path.parent.mkdir(parents=True)
    metadata = tuple(
        line for line in _METADATA if not line.startswith(f"{missing_key}=")
    )
    path.write_text(_current_work_text(metadata=metadata), encoding="utf-8")

    assert (
        f"CURRENT_WORK metadata missing required field: {missing_key}"
        in validate_current_work(tmp_path)
    )


def test_current_work_rejects_duplicate_metadata_line(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        _current_work_text(metadata=(*_METADATA, "common_record_ids=")),
        encoding="utf-8",
    )

    assert (
        "CURRENT_WORK metadata field is duplicated: common_record_ids"
        in validate_current_work(tmp_path)
    )


def test_current_work_rejects_session_record_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    sections = _canonical_record_sections(tmp_path)
    path.write_text(
        _current_work_text(
            *sections,
            metadata=tuple(
                "session_record_ids=other_session"
                if line.startswith("session_record_ids=")
                else line
                for line in _METADATA
            ),
        ),
        encoding="utf-8",
    )

    errors = validate_current_work(tmp_path)
    assert (
        "CURRENT_WORK session_record_ids missing required records: "
        "code_project_manager" in errors
    )
    assert (
        "CURRENT_WORK session_record_ids reference undeclared records: "
        "other_session" in errors
    )
    assert (
        "CURRENT_WORK session_record_ids missing linked records: "
        "code_project_manager" in errors
    )
    assert (
        "CURRENT_WORK session_record_ids reference unlinked records: "
        "other_session" in errors
    )


@pytest.mark.parametrize(
    ("declared", "expected"),
    (
        (
            "formal_toy_research|uav_validation|explorer_project_validation|"
            "independent_research_explorer_pointer",
            "CURRENT_WORK common_record_ids missing linked records: "
            "control_plane_runtime",
        ),
        (
            "formal_toy_research|uav_validation|explorer_project_validation|"
            "independent_research_explorer_pointer|control_plane_runtime|extra",
            "CURRENT_WORK common_record_ids reference unlinked records: extra",
        ),
    ),
)
def test_current_work_rejects_partial_or_extra_common_record_ids(
    tmp_path: Path, declared: str, expected: str
) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    sections = _canonical_record_sections(tmp_path)
    path.write_text(
        _current_work_text(
            *sections,
            metadata=tuple(
                f"common_record_ids={declared}"
                if line.startswith("common_record_ids=")
                else line
                for line in _METADATA
            ),
        ),
        encoding="utf-8",
    )

    assert expected in validate_current_work(tmp_path)


def test_current_work_rejects_required_record_removed_from_metadata_and_links(
    tmp_path: Path,
) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    sections = tuple(
        line
        for line in _canonical_record_sections(tmp_path)
        if "control_plane_runtime" not in line
    )
    declared = "|".join(
        record_id
        for record_id in _COMMON_RECORD_IDS
        if record_id != "control_plane_runtime"
    )
    path.write_text(
        _current_work_text(
            *sections,
            metadata=tuple(
                f"common_record_ids={declared}"
                if line.startswith("common_record_ids=")
                else line
                for line in _METADATA
            ),
        ),
        encoding="utf-8",
    )

    assert (
        "CURRENT_WORK common_record_ids missing required records: "
        "control_plane_runtime" in validate_current_work(tmp_path)
    )


def test_current_work_ignores_headings_and_links_inside_code_fences(
    tmp_path: Path,
) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    sections = list(_canonical_record_sections(tmp_path))
    session_link = sections.pop(1)
    sections[1:1] = (
        "```markdown",
        "## Common records",
        "- [Ghost](current-work/common/ghost.md)",
        "```",
        session_link,
    )
    path.write_text(_current_work_text(*sections), encoding="utf-8")

    assert validate_current_work(tmp_path) == ()
    assert all(pointer.title != "Ghost" for pointer in collect_current_work(tmp_path))


def test_current_work_rejects_managed_pointer_in_wrong_section(
    tmp_path: Path,
) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    sections = list(_canonical_record_sections(tmp_path))
    runtime_link = next(line for line in sections if "control_plane_runtime" in line)
    sections.remove(runtime_link)
    sections.insert(2, runtime_link)
    path.write_text(_current_work_text(*sections), encoding="utf-8")

    assert (
        "CURRENT_WORK common_record_ids link is outside Common records section: "
        "docs/project/current-work/common/control_plane_runtime.md"
        in validate_current_work(tmp_path)
    )


def test_current_work_rejects_correct_and_wrong_section_duplicate(
    tmp_path: Path,
) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    sections = list(_canonical_record_sections(tmp_path))
    sections.insert(
        2,
        "- [Runtime duplicate](current-work/common/control_plane_runtime.md)",
    )
    path.write_text(_current_work_text(*sections), encoding="utf-8")

    errors = validate_current_work(tmp_path)
    assert (
        "CURRENT_WORK duplicate managed pointer path: "
        "docs/project/current-work/common/control_plane_runtime.md" in errors
    )
    assert (
        "CURRENT_WORK common_record_ids contain duplicate linked records: "
        "control_plane_runtime" in errors
    )


@pytest.mark.parametrize(
    "legacy_snapshot",
    (
        "https://example.test/snapshot.md",
        "C:/outside/snapshot.md",
        "../outside/snapshot.md",
    ),
)
def test_current_work_rejects_unsafe_legacy_snapshot(
    tmp_path: Path, legacy_snapshot: str
) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    sections = _canonical_record_sections(tmp_path)
    metadata = tuple(
        f"legacy_snapshot={legacy_snapshot}"
        if line.startswith("legacy_snapshot=")
        else line
        for line in _METADATA
    )
    path.write_text(_current_work_text(*sections, metadata=metadata), encoding="utf-8")

    assert (
        f"CURRENT_WORK legacy_snapshot is not a safe repository-relative path: "
        f"{legacy_snapshot}" in validate_current_work(tmp_path)
    )


def test_current_work_rejects_missing_legacy_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    sections = _canonical_record_sections(tmp_path)
    legacy = "docs/project/archive/missing-current-work-snapshot.md"
    metadata = tuple(
        f"legacy_snapshot={legacy}"
        if line.startswith("legacy_snapshot=")
        else line
        for line in _METADATA
    )
    path.write_text(_current_work_text(*sections, metadata=metadata), encoding="utf-8")

    assert (
        f"CURRENT_WORK legacy_snapshot is not an existing regular file: {legacy}"
        in validate_current_work(tmp_path)
    )


def test_repository_current_work_is_valid_and_exposed_by_doctor_and_cli(
    repo_root: Path, capsys
) -> None:
    text = (repo_root / "docs/project/CURRENT_WORK.md").read_text(encoding="utf-8")
    assert "state_updated=2026-08-22" in text
    assert "control_plane_runtime" in next(
        line for line in text.splitlines() if line.startswith("common_record_ids=")
    )
    assert "session_record_ids=code_project_manager" in text
    assert {
        "formal_toy_research",
        "uav_validation",
        "explorer_project_validation",
        "independent_research_explorer_pointer",
        "control_plane_runtime",
    } == set(
        next(
            line.split("=", 1)[1]
            for line in text.splitlines()
            if line.startswith("common_record_ids=")
        ).split("|")
    )
    assert validate_current_work(repo_root) == ()
    assert collect_doctor(repo_root)["current_work_valid"] is True

    assert main(["current-work", "--repo-root", str(repo_root)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert {
        "title": "Control-plane runtime",
        "path": "docs/project/current-work/common/control_plane_runtime.md",
        "section": "Common records",
    } in payload
