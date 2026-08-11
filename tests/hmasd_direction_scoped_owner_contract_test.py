"""Stable central contracts for direction-scoped EM/CM routing."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "AGENTS.md"
SESSION = ROOT / "docs/project/SESSION_WORKSPACE_CONTRACT.md"
WORKFLOW_MAP = ROOT / "docs/project/WORKFLOW_MAP.md"
STARTUP = ROOT / "docs/project/L1_STARTUP_CONTEXT.md"
POINTER = ROOT / "docs/project/current-work/common/independent_research_explorer_pointer.md"
ASSIGNMENT_SKILL = ROOT / ".agents/skills/hmasd-writing-agent-assignments/SKILL.md"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split()).lower()


def _fields(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        if re.fullmatch(r"[a-z0-9_]+", key):
            fields[key] = value
    return fields


def test_root_macro_owner_and_direction_scopes_are_keyed() -> None:
    router = _fields(ROUTER)
    session = _fields(SESSION)
    pointer = _fields(POINTER)
    startup = _fields(STARTUP)

    assert router["root_semantic_owner_authority"] == "macro_portfolio_advisory"
    assert router["root_advisory_portfolio_science_authority"] == (
        "cross_direction_compare|rank|pause_continue|dependencies|complete_map_acceptance"
    )
    assert router["independent_research_explorer_scope_key_forms"] == "direction:<id>"
    assert router["code_project_manager_scope_key_forms"] == "direction:<id>|shared:<component>"
    assert session["root_macro_portfolio_owner"] == "Root"
    assert session["root_macro_portfolio_science_authority"].startswith("cross_direction_compare|")
    assert session["l1_em_scope_key_forms"] == "direction:<id>"
    assert session["l1_cm_scope_key_forms"] == "direction:<id>|shared:<component>"
    assert pointer["scope_kinds"] == "direction:<id>"
    assert pointer["macro_portfolio_owner"] == "root"
    assert pointer["direction_owner"] == "independent_research_explorer(direction:<id>)"
    assert pointer["portfolio_l1"] == "forbidden"
    assert startup["macro_portfolio_owner"] == "Root"
    assert startup["portfolio_preload"] == "forbidden"


def test_scope_atoms_reject_unsafe_direction_and_shared_values() -> None:
    pattern = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
    safe = ("a", "direction-1", "v2.alpha", "x_" + "a" * 62)
    unsafe = ("", "A", "a:b", "a/b", "a\\b", "a b", "..", "a..b", "a" * 65)
    valid = lambda value: bool(pattern.fullmatch(value)) and ".." not in value
    assert all(valid(value) for value in safe)
    assert not any(valid(value) for value in unsafe)
    assert "shared_all" in _flat(ROUTER)
    assert "shared_all" in _flat(SESSION)
    for path in (ROUTER, SESSION, POINTER, STARTUP, WORKFLOW_MAP, ASSIGNMENT_SKILL):
        text = _flat(path)
        assert "[a-z0-9][a-z0-9._-]{0,63}" in text


def test_domain_slices_have_final_cm_acceptance_and_mechanical_root_union() -> None:
    surfaces = " ".join(_flat(path) for path in (ROUTER, SESSION, WORKFLOW_MAP, ASSIGNMENT_SKILL))
    for required in (
        "direction_shared_slice_acceptance=owning_cm_final_for_slice",
        "direction_shared_root_integration=root_mechanical_only",
        "direction_shared_union_checks=root_union_tests_and_static",
        "direction_shared_conflict_route=owning_cm_or_temporary_named_shared_cm",
        "portfolio_scope|integration_scope|shared_all",
        "no standalone portfolio or integration",
        "standing/fresh domain-convergence lane",
        "extra union reviewer",
        "formal/project-canonical science remains",
    ):
        assert required in surfaces
    assert "fresh convergence wdm" in surfaces
    assert "workflow_convergence_owner=wdm_only_explicit_workflow_convergence" in surfaces


def test_direction_reverse_intake_and_multidirection_split_are_root_bound() -> None:
    session = _flat(SESSION)
    workflow_map = _flat(WORKFLOW_MAP)
    for required in (
        "the em authors and semantically accepts only one small `direction:<id>` row/delta",
        "root alone accepts the complete direction action map",
        "cross-direction relations, unselected rows, table/map consistency and portfolio continuity",
    ):
        assert required in session
    for required in (
        "root splits the request into separate exact `direction:<id>` assignments",
        "no one cm handles a multi-direction request or result",
        "each cm result binds one `direction:<id>` or one named `shared:<component>`",
        "cross-direction relations return to root",
        "em authors and accepts only its own exact `direction:<id>` row/delta",
    ):
        assert required in workflow_map


def test_pointer_history_locators_remain_lazy_and_pointer_only() -> None:
    pointer = _flat(POINTER)
    for locator in (
        "local_research/portfolio/2026-08-10_direction_action_map_v2.md",
        "local_research/portfolio/2026-08-10_cross_direction_evidence_index_v2.md",
        "historical_handoffs=lazy_only",
        "scientific_state_replication=forbidden",
        "project_state_replication=forbidden",
    ):
        assert locator in pointer
    assert "scope_kinds=direction:<id>|portfolio:<group>" not in pointer
