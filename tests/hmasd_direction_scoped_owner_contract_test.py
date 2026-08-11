"""Focused contracts for Root, direction-scoped research, and code routing."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "AGENTS.md"
EXPLORER = ROOT / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md"
CODE = ROOT / ".agents/roles/CODE_PROJECT_MANAGER.md"
POINTER = ROOT / "docs/project/current-work/common/independent_research_explorer_pointer.md"
VALIDATION = ROOT / "docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split()).lower()


def test_root_and_domain_owner_boundaries_are_direct() -> None:
    router = _flat(ROUTER)
    assert "root owns cross-direction comparison" in router
    assert "scope=direction:<id>" in router
    assert "scope=direction:<id>|shared:<component>" in router
    assert "there is no separate workflow-design" in router


def test_scope_atoms_reject_unsafe_values() -> None:
    pattern = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
    safe = ("a", "direction-1", "v2.alpha", "x_" + "a" * 62)
    unsafe = ("", "A", "a:b", "a/b", "a\\b", "a b", "..", "a..b", "a" * 65)
    valid = lambda value: bool(pattern.fullmatch(value)) and ".." not in value
    assert all(valid(value) for value in safe)
    assert not any(valid(value) for value in unsafe)


def test_cm_acceptance_and_root_relay_remain_explicit() -> None:
    surfaces = " ".join((_flat(ROUTER), _flat(CODE), _flat(EXPLORER), _flat(VALIDATION)))
    assert "code project manager owns technical/runtime acceptance" in surfaces
    assert "root relays results between research and code" in surfaces
    assert "em->root->cm->operator->root->same-direction em" in surfaces
    assert "formal project-canonical scientific acceptance" in surfaces


def test_direction_pointer_stays_lazy_and_pointer_only() -> None:
    pointer = _flat(POINTER)
    for locator in (
        "local_research/portfolio/2026-08-10_direction_action_map_v2.md",
        "local_research/portfolio/2026-08-10_cross_direction_evidence_index_v2.md",
        "historical_handoffs=lazy_only",
        "scientific_state_replication=forbidden",
        "project_state_replication=forbidden",
    ):
        assert locator in pointer
