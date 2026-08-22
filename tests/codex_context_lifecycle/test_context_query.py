from __future__ import annotations

from pathlib import Path
import shutil

from tools.codex_context_lifecycle.context_query import (
    context_foundation_health,
    context_sources_for_actor,
    current_work_index,
    decision_get,
    decision_list,
    project_map_resolve_anchor,
    project_map_validate,
)
from tools.codex_context_lifecycle.decisions import collect_decisions, render_decision_index


REQUIRED_CONTROL_PLANE_SOURCE_IDS = (
    "decision-index",
    "app-server-observer-policy",
    "managed-actor-mailbox-policy",
    "durability-kernel-policy",
)


def _write_required_registry(root: Path, source_ids: tuple[str, ...]) -> None:
    lines = ["schema_version = 1", "registry_revision = 1", ""]
    for source_id in source_ids:
        lines.extend(
            (
                "[[source]]",
                f'id = "{source_id}"',
                f'path = "docs/project/{source_id}.md"',
                'kind = "PROCEDURE"',
                'owner = "operational_root"',
                'actors = ["OPERATIONAL_ROOT"]',
                'load_policy = "ON_DEMAND"',
                "canonical = true",
                "",
            )
        )
    registry = root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
    registry.write_text("\n".join(lines), encoding="utf-8")


def _copy_minimal_healthy_foundation(repo_root: Path, destination: Path) -> None:
    project = destination / "docs/project"
    project.mkdir(parents=True)
    shutil.copyfile(repo_root / "docs/project/PROJECT_MAP.md", project / "PROJECT_MAP.md")
    shutil.copytree(repo_root / "docs/project/decisions", project / "decisions")
    shutil.copyfile(
        repo_root / "docs/project/DECISIONS_INDEX.md",
        project / "DECISIONS_INDEX.md",
    )
    shutil.copyfile(
        repo_root / "docs/project/CURRENT_WORK.md", project / "CURRENT_WORK.md"
    )
    legacy_snapshot = "archive/CURRENT_WORK_LEGACY_2026-08-01.md"
    legacy_target = project / legacy_snapshot
    legacy_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repo_root / "docs/project" / legacy_snapshot, legacy_target)
    for relative_path in (
        "current-work/sessions/code_project_manager.md",
        "current-work/common/formal_toy_research.md",
        "current-work/common/uav_validation.md",
        "current-work/common/explorer_project_validation.md",
        "current-work/common/independent_research_explorer_pointer.md",
        "current-work/common/control_plane_runtime.md",
    ):
        target = project / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_root / "docs/project" / relative_path, target)
    for decision in collect_decisions(repo_root):
        for source in decision.canonical_sources:
            target = destination / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo_root / source, target)
    for source_id in REQUIRED_CONTROL_PLANE_SOURCE_IDS:
        (project / f"{source_id}.md").write_text(source_id, encoding="utf-8")
    _write_required_registry(destination, REQUIRED_CONTROL_PLANE_SOURCE_IDS)


def test_decision_get_returns_repository_path(repo_root: Path) -> None:
    payload = decision_get(repo_root, "ADR-0001")
    assert payload["decision_id"] == "ADR-0001"
    assert payload["path"].startswith("docs/project/decisions/")


def test_project_map_resolve_anchor_is_exact(repo_root: Path) -> None:
    payload = project_map_resolve_anchor(
        repo_root,
        "Codex App Server runtime plane",
    )
    assert payload["found"] is True
    assert payload["heading"] == "Codex App Server runtime plane"
    assert payload["line"] == 129
    assert len(payload["section_text"].encode("utf-8")) <= 8192

    near_match = project_map_resolve_anchor(
        repo_root,
        "Codex App Server runtime",
    )
    assert near_match == {
        "found": False,
        "heading": "Codex App Server runtime",
        "line": None,
        "section_text": "",
    }


def test_project_map_resolve_anchor_bounds_utf8_and_stops_at_next_h2(
    tmp_path: Path,
) -> None:
    map_path = tmp_path / "docs/project/PROJECT_MAP.md"
    map_path.parent.mkdir(parents=True)
    map_path.write_text(
        "# Map\n\n## Exact anchor\n" + ("界" * 4000) + "\n## Next anchor\nSECRET\n",
        encoding="utf-8",
    )
    payload = project_map_resolve_anchor(tmp_path, "Exact anchor")
    section = payload["section_text"]
    assert payload["line"] == 3
    assert len(section.encode("utf-8")) <= 8192
    assert "Next anchor" not in section
    assert "SECRET" not in section


def test_context_queries_are_bounded_and_deterministic(repo_root: Path) -> None:
    accepted = decision_list(repo_root, "accepted")
    assert accepted == decision_list(repo_root, "accepted")
    assert all(item["status"] == "accepted" for item in accepted)

    sources = context_sources_for_actor(repo_root, "CM", ())
    assert sources == context_sources_for_actor(repo_root, "CM", ())
    assert all(item["path"] for item in sources)

    work = current_work_index(repo_root)
    assert work == current_work_index(repo_root)
    assert all(item["path"].startswith("docs/project/") for item in work)

    map_payload = project_map_validate(repo_root)
    assert map_payload["valid"] is True
    assert map_payload["errors"] == []

    health = context_foundation_health(repo_root)
    assert health["status"] == "OK"
    assert health["valid"] is True


def test_context_health_rejects_missing_required_accepted_adr(
    tmp_path: Path,
    repo_root: Path,
) -> None:
    _copy_minimal_healthy_foundation(repo_root, tmp_path)
    adr = tmp_path / "docs/project/decisions/ADR-0007-file-anchored-project-map-dispatch.md"
    text = adr.read_text(encoding="utf-8")
    adr.write_text(text.replace('status = "accepted"', 'status = "superseded"'), encoding="utf-8")
    index = tmp_path / "docs/project/DECISIONS_INDEX.md"
    index.write_text(render_decision_index(collect_decisions(tmp_path)), encoding="utf-8")

    health = context_foundation_health(tmp_path)

    assert health["valid"] is False
    assert health["components"]["required_foundation_files"] == {
        "valid": False,
        "errors": ["required accepted ADRs missing: ADR-0007"],
        "required_adr_ids_present": False,
        "current_control_plane_sources_present": True,
    }


def test_context_health_rejects_missing_required_control_plane_source(
    tmp_path: Path,
    repo_root: Path,
) -> None:
    _copy_minimal_healthy_foundation(repo_root, tmp_path)
    _write_required_registry(tmp_path, REQUIRED_CONTROL_PLANE_SOURCE_IDS[:-1])

    health = context_foundation_health(tmp_path)

    assert health["valid"] is False
    assert health["components"]["required_foundation_files"] == {
        "valid": False,
        "errors": ["required canonical control-plane sources missing: durability-kernel-policy"],
        "required_adr_ids_present": True,
        "current_control_plane_sources_present": False,
    }


def test_context_health_file_checks_do_not_open_runtime_state(
    tmp_path: Path,
    repo_root: Path,
    monkeypatch,
) -> None:
    _copy_minimal_healthy_foundation(repo_root, tmp_path)

    def forbidden_runtime_access(*args, **kwargs):
        raise AssertionError("context health must not open or initialize runtime state")

    monkeypatch.setattr(
        "tools.codex_context_lifecycle.doctor.sqlite3.connect",
        forbidden_runtime_access,
    )

    assert context_foundation_health(tmp_path)["valid"] is True
