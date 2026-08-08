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
    assert "Workflow Reviewer by default" in skill
    assert "parallel reviewers only for genuinely" in skill
    assert "batch-scoped rather than per implementer" in skill
    assert "no automatic second review" in skill
    assert "simple_operation_new_gate_state_identity_or_recovery=forbidden" in skill
    assert "simple_operation_control=one_line_runtime_checklist_only" in skill
    assert "theoretical_safety_hardening=reject_by_default" in skill
    assert "simple_operation_active_engineering_budget_minutes=20" in skill
    assert "simple_operation_failed_probe_budget=2" in skill
    assert "Pro transport/recovery" not in skill


def test_cpm_mechanical_child_is_file_bound_and_non_scientific() -> None:
    router = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    session = (REPO / "docs/project/SESSION_WORKSPACE_CONTRACT.md").read_text(
        encoding="utf-8"
    )
    session_normalized = " ".join(session.split())
    workflow_map = (REPO / "docs/project/WORKFLOW_MAP.md").read_text(encoding="utf-8")
    incidents = (
        REPO / "docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md"
    ).read_text(encoding="utf-8")

    for required in (
        "cpm_mechanical_child=hmasd-cpm-mechanical",
        "cpm_mechanical_parent=code_project_manager",
        "cpm_mechanical_assignment=CPM_MECHANICAL_TASK_ASSIGNMENT",
        "cpm_mechanical_assignment_fields=spec_path|result_path",
        "cpm_mechanical_result=CPM_MECHANICAL_TASK_RESULT",
        "cpm_mechanical_result_fields=status|result_path|error",
        "cpm_mechanical_terminal_status=COMPLETE|ERROR",
        "cpm_mechanical_wait_visibility=silent_until_terminal_native_final",
        "cpm_mechanical_write_scope=assignment_named_temporary_outputs_only",
        "cpm_mechanical_acceptance_authority=none",
        "cpm_mechanical_git_authority=none",
        "cpm_mechanical_scientific_authority=none",
        "cpm_mechanical_runtime_authority=no_experiment_no_readiness_no_agentify",
        "cpm_mechanical_finalize_owner=code_project_manager",
        "cpm_mechanical_activation=after_fresh_profile_reload",
        "cpm_mechanical_active_research_state_effect=none",
        "hmasd_python_interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
    ):
        assert required in router

    for required in (
        "CPM_MECHANICAL_TASK_ASSIGNMENT",
        "CPM_MECHANICAL_TASK_RESULT",
        "spec_path|result_path",
        "status|result_path|error",
        "silent until one native terminal return",
        "no active research-state effect",
    ):
        assert required in session_normalized

    for required in (
        "hmasd-cpm-mechanical",
        "cpm_mechanical_assignment=CPM_MECHANICAL_TASK_ASSIGNMENT",
        "cpm_mechanical_result=CPM_MECHANICAL_TASK_RESULT",
        "typed temporary receipt returns to CPM",
        "no active research-state effect",
    ):
        assert required in workflow_map

    for required in (
        "EXPLORER_MECHANICAL_OVERLOAD",
        "TICKET_MODEL_OUTPUT_TRUNCATION",
        "NONBLOCKING",
        "closed by this accepted batch",
        "CLOSED",
    ):
        assert required in incidents


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
