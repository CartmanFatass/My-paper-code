from pathlib import Path

import pytest

from tools.codex_context_lifecycle.project_map import validate_project_map


def write_minimal_valid_project_map(tmp_path: Path) -> Path:
    map_path = tmp_path / "docs" / "project" / "PROJECT_MAP.md"
    map_path.parent.mkdir(parents=True)
    map_path.write_text(
        "\n".join(
            (
                "# Project Map",
                "## Stable lineages",
                "## Agent context control plane",
                "## Low-intrusion control-plane route",
                "## Codex App Server runtime plane",
                "## Repository context lifecycle",
                "## Maintenance Protocol",
                "tools/codex_semantic_mvp/",
                "tools/codex_context_lifecycle/",
                "runtime/codex-semantic-mvp/",
                "tests/codex_semantic_mvp/",
                "tests/codex_context_lifecycle/",
                "docs/project/CONTEXT_SOURCE_REGISTRY.toml",
                "docs/project/DECISIONS_INDEX.md",
                "tools/hmasd_control_plane/",
                "tools/codex_supervisor/",
                "tests/codex_supervisor/",
                "docs/project/PROJECT_REQUIREMENTS.toml",
                "docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md",
                "docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md",
                "docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md",
                "docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md",
                "runtime SQLite is noncanonical",
                "supervisor runtime SQLite is noncanonical",
                "supervisor does not write canonical repository artifacts",
                "PROJECT_MAP is the stable codemap",
                "CURRENT_WORK is the current-work index",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return map_path


def test_project_map_names_control_plane_and_lifecycle(repo_root: Path) -> None:
    errors = validate_project_map(repo_root / "docs/project/PROJECT_MAP.md")
    assert errors == ()


def test_project_map_rejects_repo_root_codemap(tmp_path: Path) -> None:
    project_dir = tmp_path / "docs" / "project"
    project_dir.mkdir(parents=True)
    map_path = project_dir / "PROJECT_MAP.md"
    map_path.write_text("# empty\n", encoding="utf-8")
    (tmp_path / "CODEMAP.md").write_text("# competing\n", encoding="utf-8")
    errors = validate_project_map(map_path)
    assert "competing CODEMAP.md exists" in errors


def test_competing_codemap_is_rejected(tmp_path: Path) -> None:
    project_dir = tmp_path / "docs" / "project"
    project_dir.mkdir(parents=True)
    map_path = project_dir / "PROJECT_MAP.md"
    map_path.write_text("# empty\n", encoding="utf-8")
    (project_dir / "CODEMAP.md").write_text("# competing\n", encoding="utf-8")
    errors = validate_project_map(map_path)
    assert "competing CODEMAP.md exists" in errors


@pytest.mark.parametrize(
    ("surface", "expected_error"),
    (
        ("tools/hmasd_control_plane/", "missing path: tools/hmasd_control_plane/"),
        ("tools/codex_supervisor/", "missing path: tools/codex_supervisor/"),
        (
            "docs/project/PROJECT_REQUIREMENTS.toml",
            "missing path: docs/project/PROJECT_REQUIREMENTS.toml",
        ),
        (
            "docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md",
            "missing path: docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md",
        ),
        (
            "docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md",
            "missing path: docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md",
        ),
    ),
)
def test_project_map_requires_current_control_plane_surfaces(
    tmp_path: Path, surface: str, expected_error: str
) -> None:
    map_path = write_minimal_valid_project_map(tmp_path)
    text = map_path.read_text(encoding="utf-8").replace(surface, "")
    map_path.write_text(text, encoding="utf-8")
    assert expected_error in validate_project_map(map_path)


def test_project_map_requires_app_server_runtime_heading(tmp_path: Path) -> None:
    map_path = write_minimal_valid_project_map(tmp_path)
    text = map_path.read_text(encoding="utf-8").replace(
        "## Codex App Server runtime plane\n", ""
    )
    map_path.write_text(text, encoding="utf-8")
    assert "missing heading: Codex App Server runtime plane" in validate_project_map(
        map_path
    )
