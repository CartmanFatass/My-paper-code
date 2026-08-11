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
            "user workflow change or workflow defect requiring a plan",
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
        "exact assignment and named control-plane references to observe",
        "ability to design, dispatch, reconcile, accept or reject",
        "judgment about material plan drift, authority, path, acceptance and irreversible-effect changes",
        "one simple, reversible fallback for a local failure",
        "exact changed paths plus focused verification as completion evidence",
    ):
        assert capability in role
    assert "a child adds no design, routing, Git or acceptance authority" in role
    assert "hmasd-writing-agent-assignments" in role


def test_wdm_owns_workflow_semantics_without_a_singleton_scope() -> None:
    role = ROLE_PATH.read_text(encoding="utf-8")
    skill = SKILL_PATH.read_text(encoding="utf-8")
    normalized_role = " ".join(role.split()).lower()
    normalized_skill = " ".join(skill.split())
    for token in (
        "workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces",
        "workflow_modification_authority=exclusive_for_all_workflow_control_plane_surfaces",
        "workflow_acceptance_authority=exclusive_for_all_workflow_control_plane_surfaces",
        "workflow_git_authority=none",
        "workflow_final_git_mechanics=root_only_after_WDM_semantic_acceptance",
    ):
        assert token in role
    assert "WDM owns workflow semantic design, modification and acceptance" in role
    assert "a child adds no design, routing, git or acceptance authority" in normalized_role
    assert "root owns user interaction, task-tree lifecycle, physical application" in normalized_role
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
    assert "workflow_child_edit_worktree=assignment_owned_paths_in_invoking_l1_worktree_for_tracked_writer_or_task_workspace_when_exempt" in role
    assert "`AGENTS.md` as `modify` or `unchanged-valid`" in normalized_skill
    assert "workflow_scope_key" in normalized_role
    assert "multiple active wdms" in normalized_role
    assert "disjoint frozen scopes" in normalized_role


def test_user_changes_and_advisory_defects_use_distinct_nonblocking_lanes() -> None:
    role = " ".join(ROLE_PATH.read_text(encoding="utf-8").split())
    skill = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())
    assert "workflow_input_lanes=USER_REQUESTED_CHANGE|REPORTED_WORKFLOW_DEFECT" in skill
    assert "workflow_incident_log=" in role
    assert "does not serialize unrelated work" not in role
    assert "workflow_defect_repair_authority=autonomous_within_accepted_stable_contract" in role
    assert "workflow_defect_repair_authority=autonomous_within_accepted_stable_contract" in role
    assert "Otherwise move the item to the user-requested lane" in skill


def test_tracked_writers_use_root_managed_worktrees_without_ticket_identity() -> None:
    router = ROUTER_PATH.read_text(encoding="utf-8")
    role = ROLE_PATH.read_text(encoding="utf-8")
    skill = SKILL_PATH.read_text(encoding="utf-8")
    audit = (REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md").read_text(
        encoding="utf-8"
    )
    normalized_router = " ".join(router.split()).lower()
    normalized_role = " ".join(role.split()).lower()
    normalized_skill = " ".join(skill.split())
    normalized_audit = " ".join(audit.split())
    assert "tracked writer" in normalized_router
    assert "root-managed worktree" in normalized_router
    for exemption in ("read-only", "ignored-only", "temporary-only"):
        assert exemption in normalized_router
    assert "mandatory_ticket_identity=forbidden_for_subagent_authority" in normalized_router
    for text in (normalized_router, normalized_role, normalized_skill, normalized_audit):
        assert "resolved ticket worktree path" not in text
        assert "scripts/hmasd_workspace_ticket.py" not in text
        assert "git rev-parse --show-toplevel" not in text
    assert "receipt" in normalized_router
    assert "root alone" in normalized_router
    assert "root-provisioned managed worktree" in normalized_role
    assert "children never invoke" in normalized_role
    assert "one writable l1 assignment" in normalized_router
    assert "one root-managed worktree" in normalized_router
    assert "parallel implementers" in normalized_role
    assert "same frozen base" in normalized_role
    assert "exact disjoint paths" in normalized_role
    assert "one l1 slice candidate" in normalized_role
    assert "root commits/records only after all children complete" in normalized_role
    assert "independent candidate/release lifecycle means a new l1" in normalized_router
    assert "distinct concurrent wdm/cpm l1 assignments" in normalized_router
    assert "integration/convergence uses a distinct worktree" in normalized_router
    assert "disjoint l2 writers share one l1 worktree" in normalized_role
    assert "l2 never has its own worktree lifecycle" in normalized_role


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
    assert "only when no listed specialist can perform an exact bounded temporary task may wdm invoke one native default child" in normalized_role
    assert 'agent_type="default"' in normalized_role
    assert 'model="gpt-5.6-luna"' in normalized_role
    assert 'reasoning_effort="high"' in normalized_role
    assert 'fork_turns="1"' in normalized_role
    assert "never gains durable, git, routing, science, runtime or acceptance authority" in normalized_role
    assert "it never writes canonical state or contacts another owner directly" in normalized_role
    assert "workflow implementer" in normalized_role
    for text in (normalized_collaboration, normalized_audit, normalized_map):
        assert "parallel-first" in text
    assert "dispatch read-only auditor/scout concurrently with already-freezable implementation slices" in normalized_collaboration
    assert "run disjoint implementer file families concurrently" in normalized_collaboration
    assert "serialize only actual information dependencies or same-file writers" in normalized_collaboration
    assert "same writable path" in normalized_role
    assert "shared unfrozen semantic contract" in normalized_role
    assert "workflow reviewer" in normalized_role
    assert "advisory" in normalized_role
    assert "cannot accept" in normalized_role
    assert "pure design or authority decisions without file mutation remain wdm-local" in normalized_map
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


def test_scoped_slice_evidence_and_fresh_union_acceptance_are_distinct() -> None:
    role = " ".join(ROLE_PATH.read_text(encoding="utf-8").split()).lower()
    router = " ".join(ROUTER_PATH.read_text(encoding="utf-8").split()).lower()
    audit = " ".join(
        (REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md")
        .read_text(encoding="utf-8")
        .split()
    ).lower()
    surfaces = " ".join((role, router, audit))

    for required in (
        "accepts only its slice",
        "candidate-ready evidence",
        "root records/integrates candidates",
        "fresh convergence",
        "integrated union",
        "union acceptance",
        "workflow reviewer",
        "advisory",
        "acceptance_authority=none",
    ):
        assert required in surfaces, required
    # The current slice may be accepted before a later convergence pass; this
    # test checks the ownership boundary, not execution of either pass.
    assert "current slice requires reviewer" not in surfaces
    assert "current slice requires convergence" not in surfaces


def test_direction_scoped_owner_topology_is_keyed_and_pending() -> None:
    lessons = (
        REPO / "docs/H_read/2026-08-11_subagent_worktree_workflow_lessons.md"
    ).read_text(encoding="utf-8")
    router = ROUTER_PATH.read_text(encoding="utf-8")

    for required in (
        "direction_owner_topology=root_advisory_macro_portfolio_science",
        "em_scope_key=direction:<id>",
        "explorer_scope_key=direction:<id>",
        "cm_scope_key=direction:<id>|shared:<component>",
        "code_scope_key=direction:<id>|shared:<component>",
        "portfolio_em=forbidden",
        "integration_scope_key=forbidden",
        "convergence_cm=forbidden",
        "union_reviewer=forbidden",
        "forbidden_scope_keys=portfolio:<group>|integration:<group>|convergence:<group>|shared:all",
        "root_candidate_integration=mechanical_candidate_integration_only",
        "root_union_validation=mechanical_tests_static_only",
        "root_union_pass=mechanical_evidence_only",
        "root_conflict_return=owning_cm_or_exact_shared_cm",
        "cm_acceptance=final_for_its_scope_only",
        "wdm_union_convergence=kept_unchanged",
        "shared_scope_key=shared:<component>",
        "shared_all_scope=forbidden",
        "tracked_writer_worktree=one_writable_l1_worktree_shared_by_disjoint_l2_writers",
        "tracked_writer_exemptions=read-only|ignored-only|temporary-only",
        "root_user_external_formal_boundaries=preserved",
        "direction_flow=EM->CM->Experiment->publish/reverse->external-review",
        "direction_flow_status=PENDING",
        "research_execution=false",
        "science_state_changed=false",
        "historical_scientific_conclusions=preserved_not_rewritten",
    ):
        assert required in lessons, required

    assert "direction_flow_status=COMPLETED" not in lessons
    assert "direction_flow_status=COMPLETE" not in lessons

    for boundary in (
        "root_user_interaction_authority=exclusive",
        "root_cross_owner_relay_authority=exclusive",
    ):
        assert boundary in router, boundary
