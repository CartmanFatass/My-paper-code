from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO / ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md"
UI_PATH = SKILL_PATH.parent / "agents/openai.yaml"
ROLE_PATH = REPO / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md"


def test_collaborative_skill_is_the_only_design_collaboration_skill() -> None:
    assert SKILL_PATH.is_file()
    assert not (
        REPO / ".agents/skills/hmasd-deliberate-workflow-design/SKILL.md"
    ).exists()
    assert "name: hmasd-collaborative-workflow-design" in SKILL_PATH.read_text(encoding="utf-8")

    skill = SKILL_PATH.read_text(encoding="utf-8").lower()
    for retired_mechanism in (
        "decision map",
        "fog",
        "freeze",
        "high-amplification risk gate",
    ):
        assert retired_mechanism not in skill


def test_read_only_and_fully_specified_requests_take_short_paths() -> None:
    skill = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())
    assert "without plan confirmation" in skill
    assert "zero-question path" in skill
    assert "changes at least one named plan field" in skill
    assert "one question at a time" in skill
    assert "recommend the smallest answer" in skill


def test_nontrivial_execution_reuses_one_plan_without_a_new_gate() -> None:
    router = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    skill = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())
    assert "nontrivial_task_strategy=bounded_reconnaissance_then_frozen_execution_plan" in router
    assert "plan_first_user_confirmation_effect=none_inside_active_grant" in router
    assert "do not add a second plan artifact or confirmation" in skill
    assert "stop only that branch" in skill


def test_mutation_requires_one_visible_confirmed_plan() -> None:
    skill = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())
    for field in (
        "Requirements understanding",
        "Goal and non-goals",
        "Exact paths",
        "Intended changes",
        "Verification and risks",
    ):
        assert field in skill
    assert "Perform no mutation until" in skill
    assert "confirms the complete plan in natural language" in skill
    assert "present the complete revised plan" in skill


def test_role_routes_mutations_through_collaboration_before_audit() -> None:
    role = ROLE_PATH.read_text(encoding="utf-8")
    skill = SKILL_PATH.read_text(encoding="utf-8")
    assert "workflow_collaboration_skill=hmasd-collaborative-workflow-design" in role
    assert "workflow_zero_question_path=fully_specified_mutations" in skill
    assert "workflow_decision_question_condition=changes_named_plan_field" in skill
    assert "workflow_plan_confirmation=required_before_mutation" in skill
    assert "workflow_zero_question_path=" not in role
    assert "workflow_decision_question_condition=" not in role
    assert role.index("$hmasd-collaborative-workflow-design") < role.index(
        "$hmasd-workflow-change-audit"
    )


def test_wdm_is_the_single_workflow_owner_and_executes_after_confirmation() -> None:
    role = ROLE_PATH.read_text(encoding="utf-8")
    skill = SKILL_PATH.read_text(encoding="utf-8")
    normalized_skill = " ".join(skill.split())
    for token in (
        "workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces",
        "workflow_modification_authority=exclusive_for_all_workflow_control_plane_surfaces",
        "workflow_acceptance_authority=exclusive_for_all_workflow_control_plane_surfaces",
        "workflow_git_authority=exclusive_for_workflow_control_plane_surfaces",
        "Automatic continuous execution",
    ):
        assert token in role
    assert "invoked only by Workflow Design Manager" in skill
    assert "without per-action approval" in normalized_skill
    assert "workflow_hash_validation=forbidden" in role
    assert "workflow_mechanism_budget_unit=one_new_or_expanded_gate_or_recovery_branch" in role
    assert "Git revision identifiers remain source locators only" in role
    assert "workflow_router_consistency_check=required_for_every_workflow_change" in role
    assert "workflow_implementer_parallelism=min(disjoint_owned_path_families,available_native_slots_minus_integrator)" in role
    assert "workflow_child_edit_worktree=resolved_ticket_worktree_path|pre_edit_git_rev_parse_toplevel_exact_match" in role
    assert "`AGENTS.md` as `modify` or `unchanged-valid`" in normalized_skill


def test_user_changes_and_advisory_defects_use_distinct_nonblocking_lanes() -> None:
    role = " ".join(ROLE_PATH.read_text(encoding="utf-8").split())
    skill = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())
    assert "workflow_input_lanes=USER_REQUESTED_CHANGE|REPORTED_WORKFLOW_DEFECT" in skill
    assert "workflow_incident_log=" in role
    assert "does not serialize unrelated work" in role
    assert "without user confirmation only when" in role
    assert "Otherwise move the item to the user-requested lane" in skill


def test_edit_children_pin_ticket_worktree_before_mutation() -> None:
    role = ROLE_PATH.read_text(encoding="utf-8")
    skill = SKILL_PATH.read_text(encoding="utf-8")
    audit = (REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md").read_text(
        encoding="utf-8"
    )
    for text in (role, skill, audit):
        text = " ".join(text.split())
        assert "resolved ticket worktree path" in text
        assert "git rev-parse --show-toplevel" in text
        assert "stops" in text


def test_skill_cannot_be_invoked_implicitly() -> None:
    assert "allow_implicit_invocation: false" in UI_PATH.read_text(encoding="utf-8")


def test_wdm_owns_workflow_without_a_parallel_explorer_path_registry() -> None:
    role = ROLE_PATH.read_text(encoding="utf-8")
    assert "workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces" in role
    assert "centralized_explorer_workflow_paths=" not in role
    assert "centralized_explorer_workflow_acceptance_owner=" not in role
    assert "centralized_explorer_workspace_cleanup_write_authority=none" in role
