from pathlib import Path

from tools.codex_context_lifecycle.project_map import validate_project_map


def test_project_map_names_control_plane_and_lifecycle(repo_root: Path) -> None:
    errors = validate_project_map(repo_root / "docs/project/PROJECT_MAP.md")
    assert errors == ()


def test_competing_codemap_is_rejected(tmp_path: Path) -> None:
    project_dir = tmp_path / "docs" / "project"
    project_dir.mkdir(parents=True)
    map_path = project_dir / "PROJECT_MAP.md"
    map_path.write_text("# empty\n", encoding="utf-8")
    (project_dir / "CODEMAP.md").write_text("# competing\n", encoding="utf-8")
    errors = validate_project_map(map_path)
    assert "competing CODEMAP.md exists" in errors
