from __future__ import annotations

import importlib.util
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
    skill = (
        REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "actionable_finding_requires=supported_normal_path_reproduction" in reviewer
    assert "hypothetical_or_hostile_input_finding=residual_risk_only" in reviewer
    assert "review_passes_per_reviewer=1" in reviewer
    assert "review_objective=contract_fidelity_and_net_workflow_value" in reviewer
    assert "finding_cost_test=expected_benefit_exceeds_complexity_time_and_maintenance_cost" in reviewer
    normalized_skill = " ".join(skill.split())
    assert "integrated reviewer follows the complete integrated batch and reviews it once by default" in normalized_skill.lower()
    assert "parallel reviewers only for genuinely independent questions" in normalized_skill
    assert "Their advice cannot create a second pass" in normalized_skill
    assert "review_default=one_independent_reviewer" in reviewer
    assert "simple_operation_new_gate_state_identity_or_recovery=forbidden" in skill
    assert "simple_operation_control=one_line_runtime_checklist_only" in skill
    assert "theoretical_safety_hardening=reject_by_default" in skill
    assert "simple_operation_active_engineering_budget_minutes=20" in skill
    assert "simple_operation_failed_probe_budget=2" in skill
    assert "Pro transport/recovery" not in skill


def test_execution_policy_is_subagent_default_with_explicit_wdm_exception() -> None:
    router = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    manager = (REPO / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md").read_text(encoding="utf-8")
    collaboration = (
        REPO / ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md"
    ).read_text(encoding="utf-8")
    audit = (REPO / ".agents/skills/hmasd-workflow-change-audit/SKILL.md").read_text(
        encoding="utf-8"
    )
    workflow_map = (REPO / "docs/project/WORKFLOW_MAP.md").read_text(encoding="utf-8")
    normalized = " ".join("\n".join((router, manager, collaboration, audit, workflow_map)).split()).lower()

    assert "workflow_change_execution=subagent_workflow_by_default" in router
    assert "workflow_subagent_parallelism=parallel_first_with_dependency_order" in router
    assert "wdm_direct_modification=only_when_user_explicitly_instructs_wdm_to_modify_directly" in router.lower()
    assert "ordinary workflow changes use the registered auditor/scout, implementer and integrated reviewer stages with parallel-first scheduling and dependency order" in normalized
    assert "direct user instruction explicitly naming wdm direct modification" in normalized
    assert "generic workflow-change requests remain on the subagent route" in normalized
    assert "pure wdm design or authority decisions without file mutation remain wdm-local" in normalized
    assert "mechanism and simple-operation budgets constrain" in audit.lower()
    assert "never decide delegate-vs-local routing" in audit.lower()
    assert "task size, complexity, local feasibility, context cost, path count and benefit estimates never alter it" in " ".join(audit.split()).lower()
    assert "dispatch read-only auditor/scout concurrently with already-freezable implementation slices" in normalized
    assert "run disjoint implementer file families concurrently" in normalized
    assert "serialize only actual information dependencies or same-file writers" in normalized
    assert "integrated reviewer follows the complete integrated batch" in normalized
    assert "ordinary workflow changes use the registered auditor/scout -> implementer -> reviewer" not in normalized

    for stale in (
        "wdm may use",
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
    assert "cpm_mechanical_child=hmasd-cpm-mechanical" in router
    assert "cpm_mechanical_parent=code_project_manager" in router
    assert "cpm_mechanical_assignment=" not in router
    assert "cpm_mechanical_result_fields=" not in router
    assert "authority=one_exact_CPM_MECHANICAL_TASK_ASSIGNMENT" in role_normalized
    assert "assignment_fields=spec_path|result_path" in role_normalized
    assert "terminal_values=COMPLETE|ERROR" in role_normalized
    assert "never launches an experiment, readiness, Agentify or Git action" in role_normalized
    assert "CPM_MECHANICAL_TASK_RESULT" in mechanical_skill
    assert "docs/project/SESSION_WORKSPACE_CONTRACT.md" in router_normalized
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
