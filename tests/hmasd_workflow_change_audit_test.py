from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO
    / ".agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py"
)
SPEC = importlib.util.spec_from_file_location("check_hmasd_agent_harness", CHECKER_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def _keyed_field(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}=(.+)$", text)
    assert match, f"missing keyed contract field: {name}"
    return match.group(1)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_repo(root: Path) -> Path:
    _write(
        root / ".codex/config.toml",
        '[agents]\nmax_threads = 1\n\n[agents."Worker"]\n'
        'config_file = "./agents/worker.toml"\n',
    )
    _write(
        root / ".codex/agents/worker.toml",
        'name = "worker"\n'
        'model = "gpt-test"\n'
        'model_reasoning_effort = "low"\n'
        'sandbox_mode = "read-only"\n'
        'approval_policy = "never"\n'
        'developer_instructions = "Read .agents/roles/WORKER.md."\n',
    )
    _write(
        root / ".agents/roles/WORKER.md",
        "```text\nrole=worker\ncallable_agent_type=worker\n```\n",
    )
    _write(
        root / ".agents/skills/demo/SKILL.md",
        "---\nname: demo\n---\n# Demo\n",
    )
    _write(
        root / "AGENTS.md",
        "Use `.agents/roles/WORKER.md` and `.agents/skills/demo/SKILL.md`.\n"
        "superpowers_execution=disabled\nworkflow_hash_validation=disabled\n",
    )
    return root


def test_maintainability_contract_replaces_numeric_admission_gates() -> None:
    manager = (REPO / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md").read_text(encoding="utf-8")
    collaboration = (
        REPO / ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md"
    ).read_text(encoding="utf-8")
    audit = (REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md").read_text(
        encoding="utf-8"
    )
    harness = CHECKER_PATH.read_text(encoding="utf-8")
    workflow_text = "\n".join((manager, collaboration, audit, harness))
    normalized_workflow_text = " ".join(workflow_text.split())

    retired = (
        "_".join(("single", "mechanism", "line", "budget")),
        "_".join(("wdm", "core", "control", "plane", "line", "budget")),
        "_".join(("workflow", "net", "line", "growth", "default")),
        "_".join(("net", "active", "line", "growth", "default")),
        "_".join(("workflow", "recovery", "path", "line", "share")),
        "_".join(("CONTROL", "PLANE", "LINE", "BUDGET")),
        "_".join(("CONTROL", "PLANE", "BUDGET", "PATHS")),
        "-".join(("control", "plane")) + " " + " ".join(("line", "budget", "exceeded")),
        " ".join(("net", "active-line", "change")),
        " ".join(("at", "most", "five", "lines")),
    )
    for retired in retired:
        assert retired not in workflow_text

    for dimension in (
        "interface quality",
        "coherent responsibility",
        "dependency direction",
        "state ownership",
        "decoupling",
        "complexity isolation",
        "change locality",
        "focused contract evidence",
    ):
        assert dimension in normalized_workflow_text

    assert "single_mechanism_terminal_state_budget=3" in workflow_text
    assert "simple_operation_active_engineering_budget_minutes=20" in workflow_text
    assert "simple_operation_failed_probe_budget=2" in workflow_text


def test_harness_has_no_physical_line_gate() -> None:
    assert not hasattr(CHECKER, "_".join(("CONTROL", "PLANE", "LINE", "BUDGET")))
    assert not hasattr(CHECKER, "_".join(("CONTROL", "PLANE", "BUDGET", "PATHS")))
    assert ("split" + "lines()") not in CHECKER_PATH.read_text(encoding="utf-8")


def test_live_repository_harness_is_closed() -> None:
    assert CHECKER.audit_repo(REPO) == []


def test_default_scan_stays_inside_workflow_design_surfaces() -> None:
    assert "docs/project/CURRENT_WORK.md" not in CHECKER.DEFAULT_ACTIVE_PATHS
    assert "docs/project/AGENT_CONTEXT.md" not in CHECKER.DEFAULT_ACTIVE_PATHS


def test_workflow_review_is_one_pass_normal_path_advice() -> None:
    reviewer = (REPO / ".agents/roles/WORKFLOW_REVIEWER.md").read_text(encoding="utf-8")
    session = (REPO / "docs/project/SESSION_WORKSPACE_CONTRACT.md").read_text(
        encoding="utf-8"
    )
    skill = (
        REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "actionable_finding_requires=supported_normal_path_reproduction" in reviewer
    assert "hypothetical_or_hostile_input_finding=residual_risk_only" in reviewer
    assert "review_passes_per_reviewer=1" in reviewer
    assert "review_objective=contract_fidelity_and_net_workflow_value" in reviewer
    assert "finding_cost_test=expected_benefit_exceeds_complexity_time_and_maintenance_cost" in reviewer
    normalized_skill = " ".join(skill.split())
    assert "review" in normalized_skill.lower()
    assert _keyed_field(session, "workflow_integrated_review") == (
        "exactly_one_advisory_Reviewer_after_TESTS_COMPLETE_and_REVIEW_READY"
    )
    assert _keyed_field(session, "workflow_integrated_review_followup") == (
        "one_pass_no_second_review"
    )
    assert _keyed_field(session, "workflow_reviewer_authority") == "advice_only_no_acceptance"
    assert "review_default=one_independent_reviewer" in reviewer
    assert "acceptance_authority=none" in reviewer
    assert "simple_operation_new_gate_state_identity_or_recovery=forbidden" in skill
    assert "simple_operation_control=one_line_runtime_checklist_only" in skill
    assert "theoretical_safety_hardening=reject_by_default" in skill
    assert "simple_operation_active_engineering_budget_minutes=20" in skill
    assert "simple_operation_failed_probe_budget=2" in skill
    assert "Pro transport/recovery" not in skill


def test_execution_policy_is_parallel_slice_first_with_root_convergence() -> None:
    router = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    manager = (REPO / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md").read_text(encoding="utf-8")
    collaboration = (
        REPO / ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md"
    ).read_text(encoding="utf-8")
    audit = (REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md").read_text(
        encoding="utf-8"
    )
    session = (REPO / "docs/project/SESSION_WORKSPACE_CONTRACT.md").read_text(
        encoding="utf-8"
    )
    workflow_map = (REPO / "docs/project/WORKFLOW_MAP.md").read_text(encoding="utf-8")
    normalized = " ".join("\n".join((router, manager, collaboration, audit, workflow_map)).split()).lower()

    assert "workflow_design_manager_workflow_modification_authority=exclusive_via_assigned_L2" in router
    assert "workflow_subagent_parallelism=parallel_first_with_dependency_order" in router
    assert "native default child" in normalized
    assert "exact bounded temporary task" in normalized
    assert "pure wdm design or authority decisions without file mutation remain wdm-local" in normalized
    assert "mechanism and simple-operation budgets constrain" in audit.lower()
    assert "never decide delegate-vs-local routing" in audit.lower()
    assert "task size, complexity, local feasibility, context cost, path count and benefit estimates never alter it" in " ".join(audit.split()).lower()
    assert _keyed_field(session, "workflow_l1_parallelism") == (
        "disjoint_frozen_workflow_scopes_only"
    )
    assert _keyed_field(session, "workflow_slice_result") == (
        "wdm_accepts_exact_slice_then_returns_candidate_ready_packet"
    )
    assert _keyed_field(session, "workflow_candidate_integration") == (
        "Root_records_and_integrates_candidate_set_after_all_children_finish"
    )
    assert _keyed_field(session, "workflow_union_convergence") == (
        "fresh_wdm_on_exact_integrated_union_arranges_advisory_review_and_owns_union_acceptance"
    )
    assert _keyed_field(session, "workflow_reviewer_authority") == "advice_only_no_acceptance"
    assert "ordinary workflow changes use the registered auditor/scout -> implementer -> reviewer" not in normalized

    for stale in (
        "wdm direct modification",
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
        assert stale not in normalized


def test_direction_topology_keeps_wdm_convergence_and_forbids_cm_convergence() -> None:
    lessons = (
        REPO / "docs/H_read/2026-08-11_subagent_worktree_workflow_lessons.md"
    ).read_text(encoding="utf-8")
    session = (REPO / "docs/project/SESSION_WORKSPACE_CONTRACT.md").read_text(
        encoding="utf-8"
    )

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
        "shared_scope_key=shared:<component>",
        "shared_all_scope=forbidden",
        "direction_flow_status=PENDING",
        "research_execution=false",
        "science_state_changed=false",
    ):
        assert required in lessons, required

    assert _keyed_field(lessons, "wdm_union_convergence") == "kept_unchanged"
    assert _keyed_field(lessons, "convergence_cm") == "forbidden"
    assert _keyed_field(lessons, "union_reviewer") == "forbidden"
    assert _keyed_field(lessons, "direction_flow_status") == "PENDING"
    assert _keyed_field(session, "workflow_union_convergence") == (
        "fresh_wdm_on_exact_integrated_union_arranges_advisory_review_and_owns_union_acceptance"
    )
    assert "direction_flow_status=COMPLETED" not in lessons


def test_cpm_mechanical_child_is_file_bound_and_non_scientific() -> None:
    router = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    session = (REPO / "docs/project/SESSION_WORKSPACE_CONTRACT.md").read_text(
        encoding="utf-8"
    )
    mechanical_role = (REPO / ".agents/roles/CPM_MECHANICAL_OPERATOR.md").read_text(
        encoding="utf-8"
    )
    mechanical_skill = (
        REPO
        / ".agents/skills/hmasd-agile-research-development/scripts/hmasd_cpm_mechanical.py"
    ).read_text(encoding="utf-8")
    router_normalized = " ".join(router.split())
    session_normalized = " ".join(session.split())
    role_normalized = " ".join(mechanical_role.split())
    assert "callable_agent_type=hmasd-cpm-mechanical" in role_normalized
    assert "parent=code_project_manager" in role_normalized
    assert "cpm_mechanical_assignment=" not in router
    assert "cpm_mechanical_result_fields=" not in router
    assert "authority=one_exact_CPM_MECHANICAL_TASK_ASSIGNMENT" in role_normalized
    assert "assignment_fields=spec_path|result_path" in role_normalized
    assert "terminal_values=COMPLETE|ERROR" in role_normalized
    assert "never launches an experiment, readiness, Agentify or Git action" in role_normalized
    assert "CPM_MECHANICAL_TASK_RESULT" in mechanical_skill
    assert "document_kind=session_workspace_contract" in session_normalized
    assert "CPM_MECHANICAL_TASK_ASSIGNMENT" in session_normalized


@pytest.mark.parametrize("breakage, expected", [
    ("missing_role", "references missing role"),
    ("orphan_profile", "unregistered profile"),
    ("orphan_role", "unrouted role charter"),
    ("orphan_skill", "unrouted Skill"),
    ("forbidden_marker", "forbidden active marker"),
    ("broken_script", "broken active path reference"),
    ("broken_skill_script", "broken active path reference"),
])
def test_checker_fails_closed_on_cross_surface_omissions(
    tmp_path: Path, breakage: str, expected: str
) -> None:
    repo = _fixture_repo(tmp_path)
    if breakage == "missing_role":
        (repo / ".agents/roles/WORKER.md").unlink()
    elif breakage == "orphan_profile":
        _write(repo / ".codex/agents/orphan.toml", 'name = "orphan"\n')
    elif breakage == "orphan_role":
        _write(repo / ".agents/roles/ORPHAN.md", "```text\nrole=orphan\n```\n")
    elif breakage == "orphan_skill":
        _write(repo / ".agents/skills/orphan/SKILL.md", "---\nname: orphan\n---\n")
    elif breakage == "forbidden_marker":
        with (repo / "AGENTS.md").open("a", encoding="utf-8") as handle:
            handle.write("superpowers_execution=enabled\n")
    elif breakage == "broken_script":
        with (repo / "AGENTS.md").open("a", encoding="utf-8") as handle:
            handle.write("Use `scripts/missing_harness.py`.\n")
    else:
        with (repo / ".agents/skills/demo/SKILL.md").open("a", encoding="utf-8") as handle:
            handle.write("Use `scripts/missing_skill.py`.\n")

    errors = CHECKER.audit_repo(repo)
    assert any(expected in error for error in errors), errors
