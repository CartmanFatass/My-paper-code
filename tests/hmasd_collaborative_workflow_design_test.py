from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md"
ROLE = ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md"
ROUTER = ROOT / "AGENTS.md"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split()).lower()


def test_wdm_plan_modes_preserve_explicit_user_dispatch_and_no_second_gate() -> None:
    skill = _flat(SKILL)
    assert "`plan-only` returns a detailed plan" in skill
    assert "explicit `plan+execute` permits execution" in skill
    assert "without a fixed second confirmation" in skill
    assert "return to root only if goal" in skill
    for drift in ("owner authority", "science/estimand", "major path family", "acceptance method", "real user choice"):
        assert drift in skill


def test_wdm_remains_the_workflow_owner_while_root_retains_user_and_git_boundaries() -> None:
    role, router = _flat(ROLE), _flat(ROUTER)
    assert "wdm owns workflow semantic design, modification and acceptance" in role
    assert "workflow_collaboration_skill=hmasd-collaborative-workflow-design" in role
    assert "root_user_interaction_authority=exclusive" in router
    assert "root_final_git_integration_authority=accepted_paths_only" in router
    assert "max_subagent_depth=2" in router


def test_direction_owners_are_scoped_and_root_relayed_without_history_status() -> None:
    router = _flat(ROUTER)
    for invariant in (
        "independent_research_explorer_scope_key_forms=direction:<id>",
        "code_project_manager_scope_key_forms=direction:<id>|shared:<component>",
        "root_cross_owner_relay_authority=exclusive",
        "root_advisory_portfolio_science_authority=",
        "root_managed_worktree_default_unit=one_writable_l1_assignment",
    ):
        assert invariant in router
