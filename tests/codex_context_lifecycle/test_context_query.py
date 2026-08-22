from __future__ import annotations

from pathlib import Path

from tools.codex_context_lifecycle.context_query import (
    context_foundation_health,
    context_sources_for_actor,
    current_work_index,
    decision_get,
    decision_list,
    project_map_resolve_anchor,
    project_map_validate,
)


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
