"""Focused contracts for compact, action-triggered L1 startup context."""

from __future__ import annotations

import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "AGENTS.md"
HOOKS = ROOT / ".codex" / "hooks.json"
CODEX_CONFIG = ROOT / ".codex" / "config.toml"
STARTUP_CONTEXT = ROOT / "docs" / "project" / "L1_STARTUP_CONTEXT.md"
EXPLORER_POINTER = (
    ROOT / "docs" / "project" / "current-work" / "common"
    / "independent_research_explorer_pointer.md"
)


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
L1_REGISTRATION = {
    "wdm": ("HMASDWorkflowDesignManager", "hmasd-workflow-design-manager"),
    "cpm": ("HMASDCodeProjectManager", "hmasd-code-project-manager"),
    "explorer": ("HMASDIndependentResearchExplorer", "hmasd-independent-research-explorer"),
}
STANDARD_L1_PROFILE_KEYS = {
    "name",
    "description",
    "model",
    "model_reasoning_effort",
    "sandbox_mode",
    "approval_policy",
    "nickname_candidates",
    "developer_instructions",
}
REJECTED_L1_PROFILE_KEYS = {"role", "role_pointer", "registered_child_pointers"}


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
        assert "root" in text, name
        assert "action" in text, name
    assert index.count("default_core=agents.md|exact_root_assignment|profile|role") == 3
    assert "control_plane_document_routes=docs/project/control_plane_document_routes.md" in index
    assert "control_plane_document_routes_not=task_state|history|hash|receipt|queue|admission|acceptance" in index
    assert "route table is a stable lazy relationship map" in index
    assert "unclear row is escalated to the bounded auditor" in index


def test_explorer_keeps_scope_conditioned_compact_continuity_and_lazy_context() -> None:
    index = _normalized((STARTUP_CONTEXT,))
    pointer = _normalized((EXPLORER_POINTER,))
    assert "scope=direction:<id>" in index
    assert "startup_context=one_named_direction_and_named_direction_pointers_only" in index
    assert "portfolio_l1=forbidden" in index
    assert "root_compact_direction_packets|lazy_direction_pointers" in pointer
    assert "continuity_format=compact_revision_2" in pointer
    assert "lazy_portfolio_pointer_1=" in pointer
    assert "lazy_portfolio_pointer_2=" in pointer
    assert "historical_handoffs=lazy_only" in pointer
    assert "portfolio pointer semantics" in pointer
    assert "there is no portfolio l1" in pointer


def test_explorer_startup_is_scope_keyed_and_does_not_preload_unowned_context() -> None:
    explorer = _normalized((STARTUP_CONTEXT, EXPLORER_POINTER))
    for required in (
        "direction:<id>",
        "scope=direction:<id>",
        "macro/portfolio",
        "exact assignment",
        "direction pointer",
        "compact continuity",
        "lazy_direction_pointers",
        "cross-direction comparison",
        "root_science_authority=macro_portfolio_advisory",
        "portfolio_l1=forbidden",
    ):
        assert required in explorer, required
    assert "scope_kinds=direction:<id>" in explorer
    assert "scope_kinds=direction:<id>|portfolio:<group>" not in explorer

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


def test_explorer_review_triggers_keep_methodology_and_project_alignment_distinct() -> None:
    index = _normalized((STARTUP_CONTEXT,))
    assert "independent direction or methodology pro review" in index
    assert "hmasd-independent-research-pro-review/skill.md" in index
    assert "explorer project-alignment or overnight branch-blocker external review" in index
    assert "hmasd-explorer-project-validation/skill.md" in index
    assert "explorer_project_validation_workflow.md" in index


def test_l1_registration_pointers_are_static_and_runtime_unproven() -> None:
    """Static checks only; they do not prove runtime registration/live spawn or repair completion."""
    with CODEX_CONFIG.open("rb") as stream:
        config = tomllib.load(stream)
    agents = config["agents"]
    for owner, (table_name, profile_name) in L1_REGISTRATION.items():
        role_path, profile_path = L1_SURFACES[owner]
        assert role_path.is_file()
        assert profile_path.is_file()
        assert agents[table_name]["config_file"] == f"./agents/{profile_name}.toml"
        with profile_path.open("rb") as stream:
            profile = tomllib.load(stream)
        assert profile["name"] == profile_name
        assert set(profile) <= STANDARD_L1_PROFILE_KEYS
        assert not set(profile).intersection(REJECTED_L1_PROFILE_KEYS)
        instructions = " ".join(str(profile["developer_instructions"]).split()).lower()
        role = " ".join(role_path.read_text(encoding="utf-8").split()).lower()
        assert ".agents/roles/" in instructions
        assert "agent_tree_level=1" in instructions or "agent_tree_level=1" in role
        assert "parent=root" in instructions or "parent=root" in role
        if owner in {"wdm", "explorer"}:
            assert "root" in instructions and "fork_turns=1" in instructions


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
    assert "scope=one direction:<id>" in explorer
