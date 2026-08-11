"""Consumer scenarios for the simplified research-delivery contracts.

These deliberately check owner transitions and negative authority boundaries,
not a copied list of contract sentences.  The authoritative wording stays in
the role and skill documents.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(*relative_paths: str) -> str:
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8").lower()
        for path in relative_paths
    )
    return " ".join(combined.split())


EM = ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md"
CM = ".agents/roles/CODE_PROJECT_MANAGER.md"
PRO = ".agents/roles/EXTERNAL_PRO.md"
AGILE = ".agents/skills/hmasd-agile-research-development/SKILL.md"
RESEARCH = ".agents/skills/hmasd-independent-research-exploration/SKILL.md"
DESIGN = ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md"
SESSION = "docs/project/SESSION_WORKSPACE_CONTRACT.md"
ROUTER = "AGENTS.md"
STARTUP = "docs/project/L1_STARTUP_CONTEXT.md"
ROUTES = "docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md"
VALIDATION = "docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
PRO_REVIEW = ".agents/skills/hmasd-independent-research-pro-review/SKILL.md"


def test_missing_objects_route_to_the_owner_that_can_make_them() -> None:
    em, cm, research = _text(EM), _text(CM), _text(RESEARCH)
    # Engineering absences stay productive CM work; scientific choices remain EM work.
    assert "code, runner, adapter, package, dependency" in em
    assert "pre-full recovery" in cm
    assert "are work, not park or `blocked`" in em
    assert "scientific question, candidate and comparator choice" in em
    assert "cm -> root -> same-direction em" in research


def test_accepted_run_transitions_to_operator_and_operator_failure_returns_to_cm() -> None:
    agile, cm = _text(AGILE), _text(CM)
    assert "only after cm technically accepts" in agile
    assert "operator receives only an exact run-ready assignment" in agile
    assert "operator dispatch" in cm and "pre-full recovery" in cm
    assert "never installs, repairs, changes source/configuration" in agile


def test_continuity_is_a_resume_aid_not_a_current_action_override() -> None:
    text = _text(EM, RESEARCH)
    assert "next owner/action" in text
    assert "completed installation, old hashes" in text
    assert "current action" in text


def test_plan_only_and_plan_execute_have_distinct_authorized_transitions() -> None:
    text = _text(DESIGN)
    assert "`plan-only` returns a detailed plan" in text
    assert "explicit `plan+execute` permits execution" in text
    assert "without a fixed second confirmation" in text
    for drift in ("goal", "owner authority", "science/estimand", "major path family", "irreversible external effect", "real user"):
        assert drift in text


def test_overnight_authority_is_bounded_natural_language_work_not_a_scheduler() -> None:
    session, agile = _text(SESSION), _text(AGILE)
    assert "overnight_authorization=natural_language_task_authorization_not_token" in session
    for allowed in ("managed_worktree", "tracked_edits", "exact_dependencies", "isolated_environment", "named_long_compute", "ordinary_nonforce_push"):
        assert allowed in session
    assert "force_push|history_rewrite|secret|scope_or_system_destructive_action" in session
    assert "without a repeated" in agile


def test_effect_evidence_and_publication_do_not_become_authority_gates() -> None:
    session, pro, em = _text(SESSION), _text(PRO), _text(EM)
    assert "ordinary tracked edits need no such record" in session
    assert "never permission, admission, scheduler, or retry ledger" in session
    for text in (pro, em):
        assert "ordinary non-force" in text
        assert "github-readable remote, branch, commit" in text
    assert "not a local commit" in pro
    assert "not em intake" in em
    assert "git_main_policy=user_only_never_checkout_merge_rebase_or_push" in _text(ROUTER)


def test_return_and_optional_map_installation_are_separate_interfaces() -> None:
    em, session = _text(EM), _text(SESSION)
    assert "technical-result return and scientific intake" in em
    assert "direction action map semantic-delta installation" in em
    assert "never sends a full map" in em
    assert "root alone accepts the complete direction action map" in session


def test_review_routes_and_escalation_preserve_owner_boundaries() -> None:
    em, pro, research, cm = _text(EM), _text(PRO), _text(RESEARCH), _text(CM)
    assert "explorer_project_alignment_audit" in em
    assert "code_science_alignment_audit" in cm
    assert "explorer transport" in em
    assert "exhausts applicable in-scope recovery and legal owner relay" in pro
    assert "exact pushed aggressive revision" in pro
    assert "raw response is completely archived, committed, and pushed" in pro
    assert "technical acceptance remains cm's" in pro
    assert "ordinary b has no automatic pro call" in pro
    assert "full estimand" in research and "conclusion-bearing c" in research


def test_independent_and_project_alignment_review_triggers_keep_distinct_sources() -> None:
    startup, routes, validation, review = _text(STARTUP), _text(ROUTES), _text(VALIDATION), _text(PRO_REVIEW)
    independent = "independent direction or methodology pro review"
    project = "explorer project-alignment or overnight branch-blocker external review"
    assert independent in startup and project in startup
    assert independent in routes and project in routes
    project_row = routes[routes.index(project) :]
    assert "explorer_project_validation_workflow.md" in project_row
    assert "hmasd-independent-research-pro-review/skill.md" in project_row
    assert "hmasd-explorer-project-validation/skill.md" in project_row
    assert "hmasd-independent-research-exploration/skill.md" not in project_row
    assert "hmasd-independent-research-pro-review/skill.md" in startup[startup.index(project) :]
    assert "explorer_project_validation_workflow.md" in startup[startup.index(project) :]
    # The Pro-review procedure has three branches, while validation remains the
    # semantic source for the project transition.
    assert all(branch in review for branch in ("ir_direction_review", "ir_methodology_review", "explorer_project_alignment_audit"))
    assert "does not rename, continue, or borrow" in review
    assert "before dispatch, root must have completed `publication`" in review
    assert "exact pushed **aggressive** revision" in review
    assert "github-readable remote" in review and "parent-specific registered transport" in review
    assert "raw-response archive" in review and "ordinary non-force push" in review
    assert "returns it to the original same-direction em" in review
    assert "ordinary b never creates this trigger" in review
    assert "recovery and legal owner relay are exhausted" in review
    assert "workflow design manager has no production transport role" in review
    assert "neither pro nor root authors em science" in review
    assert "root never substitutes for em scientific authorship" in validation


def test_root_relay_depth_and_git_boundaries_remain_structural_invariants() -> None:
    router, session = _text(ROUTER), _text(SESSION)
    assert "max_subagent_depth=2" in router
    assert "project scout" in router
    assert "l1_user_contact_authority=none" in router
    assert "root is the sole git integration actor" in session
