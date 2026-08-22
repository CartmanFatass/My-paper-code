from pathlib import Path
import shutil

import pytest

from tools.codex_context_lifecycle.doctor import collect_doctor


CONTROL_PLANE_SOURCE_IDS = (
    "decision-index",
    "app-server-observer-policy",
    "managed-actor-mailbox-policy",
    "durability-kernel-policy",
)


def _copy_project_map(repo_root: Path, destination: Path) -> None:
    map_path = destination / "docs" / "project" / "PROJECT_MAP.md"
    map_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repo_root / "docs/project/PROJECT_MAP.md", map_path)


def _write_registry(root: Path, source_ids: tuple[str, ...]) -> None:
    lines = ["schema_version = 1", "registry_revision = 1", ""]
    for source_id in source_ids:
        lines.extend(
            [
                "[[source]]",
                f'id = "{source_id}"',
                f'path = "docs/project/{source_id}.md"',
                'kind = "PROCEDURE"',
                'owner = "operational_root"',
                'actors = ["OPERATIONAL_ROOT"]',
                'load_policy = "ON_DEMAND"',
                "canonical = true",
                "",
            ]
        )
    registry_path = root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text("\n".join(lines), encoding="utf-8")


def test_doctor_reports_complete_context_foundation(repo_root: Path) -> None:
    payload = collect_doctor(repo_root)

    assert payload["current_work_valid"] is True
    assert payload["required_adr_ids_present"] is True
    assert payload["current_control_plane_sources_present"] is True
    assert payload["behavioral_hooks_disabled"] is True


@pytest.mark.parametrize(
    "config_text",
    (
        "[features]\nhooks = true\n",
        "[features]\nhooks = false\n\n[hooks]\nenabled = false\n",
    ),
)
def test_doctor_rejects_enabled_or_configured_behavioral_hooks(
    tmp_path: Path,
    repo_root: Path,
    config_text: str,
) -> None:
    _copy_project_map(repo_root, tmp_path)
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(config_text, encoding="utf-8")

    assert collect_doctor(tmp_path)["behavioral_hooks_disabled"] is False


def test_doctor_derives_foundation_absence_from_repository(
    tmp_path: Path,
    repo_root: Path,
) -> None:
    _copy_project_map(repo_root, tmp_path)

    payload = collect_doctor(tmp_path)

    assert payload["current_work_valid"] is False
    assert payload["required_adr_ids_present"] is False
    assert payload["current_control_plane_sources_present"] is False


def test_doctor_requires_exact_control_plane_ids_and_existing_files(
    tmp_path: Path,
    repo_root: Path,
) -> None:
    _copy_project_map(repo_root, tmp_path)
    project_dir = tmp_path / "docs" / "project"
    for source_id in CONTROL_PLANE_SOURCE_IDS:
        (project_dir / f"{source_id}.md").write_text(source_id, encoding="utf-8")

    _write_registry(tmp_path, CONTROL_PLANE_SOURCE_IDS[:-1])
    assert collect_doctor(tmp_path)["current_control_plane_sources_present"] is False

    _write_registry(tmp_path, CONTROL_PLANE_SOURCE_IDS)
    (project_dir / f"{CONTROL_PLANE_SOURCE_IDS[-1]}.md").unlink()
    assert collect_doctor(tmp_path)["current_control_plane_sources_present"] is False

    (project_dir / f"{CONTROL_PLANE_SOURCE_IDS[-1]}.md").write_text(
        CONTROL_PLANE_SOURCE_IDS[-1],
        encoding="utf-8",
    )
    assert collect_doctor(tmp_path)["current_control_plane_sources_present"] is True


def test_doctor_requires_every_required_adr_to_be_accepted(
    tmp_path: Path,
    repo_root: Path,
) -> None:
    _copy_project_map(repo_root, tmp_path)
    decisions_dir = tmp_path / "docs" / "project" / "decisions"
    decisions_dir.mkdir(parents=True)
    for number in range(1, 8):
        status = "superseded" if number == 7 else "accepted"
        decision_id = f"ADR-{number:04d}"
        (decisions_dir / f"{decision_id}.md").write_text(
            "\n".join(
                (
                    "+++",
                    f'decision_id = "{decision_id}"',
                    f'title = "{decision_id}"',
                    'owner = "operational_root"',
                    'scope = "shared:test"',
                    f'status = "{status}"',
                    'decision_date = "2026-08-22"',
                    "supersedes = []",
                    "canonical_sources = []",
                    "revisit_conditions = []",
                    "+++",
                    "",
                )
            ),
            encoding="utf-8",
        )

    assert collect_doctor(tmp_path)["required_adr_ids_present"] is False
