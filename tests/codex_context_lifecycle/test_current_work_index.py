import json
from pathlib import Path

from tools.codex_context_lifecycle.cli import main
from tools.codex_context_lifecycle.current_work import (
    CurrentWorkPointer,
    collect_current_work,
    validate_current_work,
)
from tools.codex_context_lifecycle.doctor import collect_doctor


def test_current_work_rejects_missing_pointer(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Current Work\n\n- [Missing](current-work/common/missing.md)\n",
        encoding="utf-8",
    )

    assert validate_current_work(tmp_path) == (
        "missing CURRENT_WORK target: docs/project/current-work/common/missing.md",
    )


def test_current_work_rejects_competing_canonical_project_state(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Current Work\n\n## Canonical project state\n", encoding="utf-8")

    assert validate_current_work(tmp_path) == (
        "CURRENT_WORK must not contain a Canonical project state section",
    )


def test_collects_only_strict_project_pointer_links(tmp_path: Path) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    target = tmp_path / "docs/project/current-work/common/runtime.md"
    target.parent.mkdir(parents=True)
    target.write_text("owner=operational_root\n", encoding="utf-8")
    path.write_text(
        "\n".join(
            (
                "# Current Work",
                "",
                "## Common records",
                "- [Runtime](current-work/common/runtime.md)",
                "- [Not strict](current-work/common/runtime.md) trailing",
                "- [External](https://example.test/runtime.md)",
                "",
            )
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
    assert validate_current_work(tmp_path) == ()


def test_current_work_rejects_common_record_metadata_missing_linked_record(
    tmp_path: Path,
) -> None:
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    other = tmp_path / "docs/project/current-work/common/other.md"
    runtime = tmp_path / "docs/project/current-work/common/control_plane_runtime.md"
    other.parent.mkdir(parents=True)
    other.write_text("owner=operational_root\n", encoding="utf-8")
    runtime.write_text("owner=operational_root\n", encoding="utf-8")
    path.write_text(
        "\n".join(
            (
                "# Current Work",
                "",
                "```text",
                "common_record_ids=other",
                "```",
                "",
                "## Common records",
                "- [Other](current-work/common/other.md)",
                "- [Runtime](current-work/common/control_plane_runtime.md)",
                "",
            )
        ),
        encoding="utf-8",
    )

    assert validate_current_work(tmp_path) == (
        "CURRENT_WORK common_record_ids missing linked records: control_plane_runtime",
    )


def test_repository_current_work_is_valid_and_exposed_by_doctor_and_cli(
    repo_root: Path, capsys
) -> None:
    text = (repo_root / "docs/project/CURRENT_WORK.md").read_text(encoding="utf-8")
    assert "state_updated=2026-08-22" in text
    assert "control_plane_runtime" in next(
        line for line in text.splitlines() if line.startswith("common_record_ids=")
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
