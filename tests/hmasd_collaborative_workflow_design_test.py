from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO / ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md"
UI_PATH = SKILL_PATH.parent / "agents/openai.yaml"
ROLE_PATH = REPO / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md"
ROUTER_PATH = REPO / "AGENTS.md"


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
    normalized_router = " ".join(router.split())
    for trigger, owner_surface in (
        (
            "user change or workflow defect requiring a plan",
            ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md",
        ),
        (
            "designing an assignment/interface",
            "`hmasd-writing-agent-assignments` and named contract",
        ),
        (
            "confirmed plan implementation or verification",
            ".agents/skills/hmasd-workflow-change-audit/SKILL.md",
        ),
        (
            "stable owner/interface/dependency edge",
            "docs/project/WORKFLOW_MAP.md",
        ),
        (
            "canonical status/continuity reload",
            "the exact owner record named by Root",
        ),
    ):
        assert trigger in normalized_router
        assert owner_surface in normalized_router
    assert "| L2, depth 2 | registered leaf | exact assignment, its profile, named Role and immediate references |" in router
    assert "After natural-language confirmation, load" in skill
    assert "this requirements Skill does not duplicate post-confirmation execution" in skill


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
    role_normalized = " ".join(role.split()).lower()
    assert "the collaborative skill owns requirements, planning and user confirmation" in role_normalized
    assert "the audit skill owns post-confirmation" in role_normalized


def test_assignment_writing_skill_is_required_at_design_dispatch_boundary() -> None:
    role = " ".join(ROLE_PATH.read_text(encoding="utf-8").split())
    skill = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())
    router = " ".join(ROUTER_PATH.read_text(encoding="utf-8").split())
    for text in (role, skill, router):
        assert "hmasd-writing-agent-assignments" in text
    assert "required sub-skill" in skill
    assert "design a reusable child or cross-session interface" in skill
    assert "compile each concrete file-backed assignment" in skill
    for capability in (
        "owned outcome",
        "necessary observations",
        "permitted actions",
        "role-local judgment",
        "bounded recovery",
        "completion evidence",
    ):
        assert capability in role
    assert "child assignment meaning is owned by" in role.lower()
    assert "hmasd-writing-agent-assignments" in role


def test_wdm_is_the_single_workflow_owner_and_executes_after_confirmation() -> None:
    role = ROLE_PATH.read_text(encoding="utf-8")
    skill = SKILL_PATH.read_text(encoding="utf-8")
    normalized_role = " ".join(role.split())
    normalized_skill = " ".join(skill.split())
    for token in (
        "workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces",
        "workflow_modification_authority=exclusive_for_all_workflow_control_plane_surfaces",
        "workflow_acceptance_authority=exclusive_for_all_workflow_control_plane_surfaces",
        "workflow_git_authority=none",
        "workflow_final_git_mechanics=root_only_after_WDM_semantic_acceptance",
    ):
        assert token in role
    assert "WDM is the semantic owner and acceptance owner" in role
    assert "exclusive workflow modification authority is exercised through the registered Auditor/Scout, Implementer and integrated Reviewer stages" in normalized_role
    assert "workflow-file edits remain on the registered L2 route" in normalized_role
    assert "Root performs the physical application" in normalized_role
    assert "Root owns task-tree lifecycle, user interaction, physical application of accepted proposals and final Git mechanics" in normalized_role
    assert "This Skill is invoked only by the Root-assigned Workflow Design Manager L1" in skill
    assert "without plan confirmation" in normalized_skill
    assert "workflow_git_authority=exclusive_for_workflow_control_plane_surfaces" not in role
    assert "workflow_hash_validation=forbidden" not in role
    assert "workflow_hash_validation=forbidden" in (
        REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "workflow_mechanism_budget_unit=one_new_or_expanded_gate_or_recovery_branch" not in role
    assert "Git revision identifiers are source locators" in (
        REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "workflow_router_consistency_check=required_for_every_workflow_change" in role
    assert "workflow_implementer_parallelism=" not in role
    assert "workflow_child_edit_worktree=assignment_owned_paths_in_current_task_workspace" in role
    assert "`AGENTS.md` as `modify` or `unchanged-valid`" in normalized_skill


def test_user_changes_and_advisory_defects_use_distinct_nonblocking_lanes() -> None:
    role = " ".join(ROLE_PATH.read_text(encoding="utf-8").split())
    skill = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())
    assert "workflow_input_lanes=USER_REQUESTED_CHANGE|REPORTED_WORKFLOW_DEFECT" in skill
    assert "workflow_incident_log=" in role
    assert "does not serialize unrelated work" not in role
    assert "workflow_defect_repair_authority=autonomous_within_accepted_stable_contract" in role
    assert "workflow_defect_repair_authority=autonomous_within_accepted_stable_contract" in role
    assert "Otherwise move the item to the user-requested lane" in skill


def test_edit_children_use_assigned_paths_without_ticket_worktree_prerequisite() -> None:
    router = ROUTER_PATH.read_text(encoding="utf-8")
    role = ROLE_PATH.read_text(encoding="utf-8")
    skill = SKILL_PATH.read_text(encoding="utf-8")
    audit = (REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md").read_text(
        encoding="utf-8"
    )
    normalized_router = " ".join(router.split())
    normalized_role = " ".join(role.split())
    normalized_skill = " ".join(skill.split())
    normalized_audit = " ".join(audit.split())
    assert "workflow_child_edit_worktree=assignment_owned_paths_in_current_task_workspace" in role
    assert "ticket_worktree_precondition=none" in router
    assert "isolated_worktree_identity=optional_provenance_only" in router
    assert "mandatory_ticket_identity=forbidden_for_subagent_authority" in router
    assert "mandatory_ticket_identity=forbidden" in role
    assert "no external workspace identity is required" in normalized_skill
    assert "no external workspace identity precondition" in normalized_audit
    for text in (normalized_router, normalized_role, normalized_skill, normalized_audit):
        assert "resolved ticket worktree path" not in text
        assert "git rev-parse --show-toplevel" not in text


def test_skill_cannot_be_invoked_implicitly() -> None:
    assert "allow_implicit_invocation: false" in UI_PATH.read_text(encoding="utf-8")


def test_wdm_owns_workflow_without_a_parallel_explorer_path_registry() -> None:
    role = ROLE_PATH.read_text(encoding="utf-8")
    assert "workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces" in role
    assert "centralized_explorer_workflow_paths=" not in role
    assert "centralized_explorer_workflow_acceptance_owner=" not in role
    assert "centralized_explorer_workspace_cleanup_write_authority=none" in role


def test_default_execution_policy_is_parallel_first_with_direct_exception() -> None:
    router = ROUTER_PATH.read_text(encoding="utf-8")
    role = ROLE_PATH.read_text(encoding="utf-8")
    collaboration = SKILL_PATH.read_text(encoding="utf-8")
    audit = (REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md").read_text(
        encoding="utf-8"
    )
    workflow_map = (REPO / "docs/project/WORKFLOW_MAP.md").read_text(encoding="utf-8")
    normalized_router = " ".join(router.split()).lower()
    normalized_role = " ".join(role.split()).lower()
    normalized_collaboration = " ".join(collaboration.split()).lower()
    normalized_audit = " ".join(audit.split()).lower()
    normalized_map = " ".join(workflow_map.split()).lower()

    assert "workflow_subagent_parallelism=parallel_first_with_dependency_order" in router
    assert "workflow_change_execution=subagent_workflow_by_default" not in normalized_router
    assert "wdm_direct_modification=" not in normalized_router
    assert "as a narrow temporary-task exception" in normalized_router
    assert "only when no listed specialist leaf can perform the bounded task" in normalized_router
    assert "only when no listed specialist leaf can perform the exact bounded task may wdm invoke one native default child as an l2" in normalized_role
    assert 'agent_type="default"' in normalized_role
    assert 'model="gpt-5.6-luna"' in normalized_role
    assert 'reasoning_effort="high"' in normalized_role
    assert 'fork_turns="1"' in normalized_role
    assert "the native default exception below is a caller action and creates no registered child" in normalized_role
    assert "direct user instruction may change the semantic scope, but it does not grant wdm physical write authority" in normalized_role
    for text in (normalized_role, normalized_collaboration, normalized_audit, normalized_map):
        assert "ordinary workflow changes use the registered auditor/scout, implementer and integrated reviewer stages with parallel-first scheduling and dependency order" in text
    assert "dispatch read-only auditor/scout concurrently with already-freezable implementation slices" in normalized_collaboration
    assert "run disjoint implementer file families concurrently" in normalized_collaboration
    assert "serialize only actual information dependencies or same-file writers" in normalized_collaboration
    assert "integrated reviewer follows the complete integrated batch" in normalized_collaboration
    assert "pure design or authority decisions without file mutation remain wdm-local" in normalized_role
    assert "mechanism and simple-operation budgets constrain" in normalized_audit
    assert "never decide delegate-vs-local routing" in normalized_audit
    assert "task size, complexity, local feasibility, context cost, path count and benefit estimates never alter it" in normalized_audit
    assert "ordinary workflow changes use the registered auditor/scout -> implementer -> reviewer" not in "\n".join((router, role, collaboration, audit, workflow_map)).lower()

    for stale in (
        "workflow_change_execution=subagent_workflow_by_default",
        "wdm_direct_modification=",
        "resolved ticket worktree path",
        "git rev-parse --show-toplevel",
        "after confirmation, wdm may use",
        "when implementers were used",
        "delegation is judgment-guided",
        "bounded slices may use registered children",
        "no mandatory pipeline",
        "cost-aware delegation path",
        "local feasibility threshold",
        "task size threshold",
        "complexity threshold",
    ):
        assert stale not in "\n".join((router, role, collaboration, audit, workflow_map)).lower()
