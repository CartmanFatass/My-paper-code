"""Focused contracts for compact, action-triggered L1 startup context."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "AGENTS.md"
HOOKS = ROOT / ".codex" / "hooks.json"
CODEX_CONFIG = ROOT / ".codex" / "config.toml"
STARTUP_CONTEXT = ROOT / "docs" / "project" / "L1_STARTUP_CONTEXT.md"


L1_SURFACES = {
    "wdm": (
        ROOT / ".agents" / "roles" / "WORKFLOW_DESIGN_MANAGER.md",
        ROOT / ".codex" / "agents" / "hmasd-workflow-design-manager.toml",
    ),
    "cpm": (
        ROOT / ".agents" / "roles" / "CODE_PROJECT_MANAGER.md",
        ROOT / ".codex" / "agents" / "hmasd-code-project-manager.toml",
    ),
    "explorer": (
        ROOT / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md",
        ROOT / ".codex" / "agents" / "hmasd-independent-research-explorer.toml",
    ),
}


def _normalized(paths: tuple[Path, ...]) -> str:
    return " ".join(" ".join(path.read_text(encoding="utf-8").split()) for path in paths).lower()


def test_wdm_cpm_and_explorer_start_compact_and_action_triggered() -> None:
    index = _normalized((STARTUP_CONTEXT,))
    assert "document_kind=l1_startup_context_pointer_index" in index
    assert "startup_preload=core_inputs_only" in index
    assert "this is a concise pointer index" in index
    assert "expands only when an action trigger names a skill or reference" in index
    for owner, surface in (
        (
            "## workflow design manager (wdm)",
            ".agents/skills/hmasd-collaborative-workflow-design/skill.md",
        ),
        (
            "## code project manager (cpm)",
            ".agents/skills/hmasd-agile-research-development/skill.md",
        ),
        (
            "## independent research explorer (explorer)",
            ".agents/skills/hmasd-independent-research-exploration/skill.md",
        ),
    ):
        assert owner in index
        assert surface in index

    for name, paths in L1_SURFACES.items():
        text = _normalized(paths)
        assert "startup" in text, name
        assert "action" in text, name
    assert index.count("default_core=agents.md|exact_root_assignment|profile|role") == 3


def test_explorer_keeps_scope_conditioned_compact_continuity_and_lazy_context() -> None:
    explorer = _normalized(L1_SURFACES["explorer"])
    assert "task_identity=real_user_visible_explorer_l1_task|research_scope_key" in explorer
    assert "direction_startup=registered_profile|role_core|exact_root_assignment|named_direction_pointers" in explorer
    assert "portfolio_startup=registered_profile|role_core|exact_root_assignment|compact_accepted_continuity|lazy_direction_pointers" in explorer
    assert "direction_context_exclusion=whole_portfolio|project_runtime_corpus|implicit_global_continuity" in explorer
    assert "portfolio_context=compact_continuity_plus_lazy_direction_pointers_only" in explorer
    assert "continuity_format=compact_revision_2" in explorer
    assert "lazy_portfolio_pointer_1=" in explorer
    assert "lazy_portfolio_pointer_2=" in explorer
    assert "historical_handoffs=lazy_only" in explorer
    assert "continuity_entry=assignment_named_scope_compact_continuity_pointer" in explorer
    assert "do not preload campaign direction/history, action references or historical handoffs" in explorer


def test_explorer_startup_is_scope_keyed_and_does_not_preload_unowned_context() -> None:
    explorer = _normalized(L1_SURFACES["explorer"])
    for required in (
        "research_scope_key",
        "direction:<id>",
        "portfolio:<group>",
        "direction scope",
        "portfolio scope",
        "exact assignment",
        "direction pointer",
        "compact accepted direction",
        "compact continuity",
        "lazy direction pointer",
        "cross-direction comparison",
        "advisory portfolio",
    ):
        assert required in explorer, required

    for stale in (
        "runtime_concurrency=three_unit_cpm_capacity_pool",
        "runtime_capacity_units_total=3",
        "runtime_capacity_admission_owner=code_project_manager",
        "runtime_admission_judgment=admit|up-class|pending_runtime_capacity",
        "fixed unit pool",
        "reservation ledger",
        "hash admission",
    ):
        assert stale not in explorer, stale


def test_hooks_are_empty_disabled_and_non_authoritative() -> None:
    hooks = json.loads(HOOKS.read_text(encoding="utf-8"))
    assert hooks["hooks"] == {}
    router = _normalized((ROUTER,))
    assert "hook posture is disabled and non-authoritative" in router
    assert "empty hook map" in router


def test_thread_depth_and_external_science_boundaries_remain_unchanged() -> None:
    config = _normalized((CODEX_CONFIG,))
    router = _normalized((ROUTER,))
    explorer = _normalized(L1_SURFACES["explorer"])
    assert "max_threads = 20" in config
    assert "max_depth = 2" in config
    assert "max_subagent_depth=2" in router
    assert "external pro (non-agent, outside the cli tree)" in router
    assert "historical handoffs" in explorer
