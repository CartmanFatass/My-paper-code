"""Focused owner-transition scenarios for research delivery."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(*relative_paths: str) -> str:
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8").lower() for path in relative_paths)
    return " ".join(combined.split())


EM = ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md"
CM = ".agents/roles/CODE_PROJECT_MANAGER.md"
PRO = ".agents/roles/EXTERNAL_PRO.md"
AGILE = ".agents/skills/hmasd-agile-research-development/SKILL.md"
RESEARCH = ".agents/skills/hmasd-independent-research-exploration/SKILL.md"
VALIDATION = "docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
PRO_REVIEW = ".agents/skills/hmasd-independent-research-pro-review/SKILL.md"
ROUTER = "AGENTS.md"


def test_missing_objects_route_to_the_owner_that_can_make_them() -> None:
    em, cm, research = _text(EM), _text(CM), _text(RESEARCH)
    assert "code, runner, adapter, package, dependency" in em
    assert "pre-full recovery" in cm
    assert "scientific question, candidate and comparator choice" in em
    assert "cm -> root -> same-direction em" in research


def test_accepted_run_transitions_to_operator_and_failure_returns_to_cm() -> None:
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


def test_publication_keeps_root_and_main_boundaries() -> None:
    router, pro, em = _text(ROUTER), _text(PRO), _text(EM)
    for text in (pro, em):
        assert "ordinary non-force" in text
        assert "github-readable remote, branch, commit" in text
    assert "`main` is user-only" in router
    assert "never force-push" in router


def test_return_and_optional_map_installation_are_separate_interfaces() -> None:
    text = _text(EM, VALIDATION)
    assert "technical-result return and scientific intake" in text
    assert "direction action map semantic-delta installation" in text
    assert "never sends a full map" in text
    assert "root" in text and "full-map" in text


def test_external_review_preserves_owner_boundaries() -> None:
    text = _text(EM, CM, PRO, PRO_REVIEW, VALIDATION)
    assert "explorer_project_alignment_audit" in text
    assert "code_science_alignment_audit" in text
    assert "ordinary b has no automatic pro call" in text
    assert "technical acceptance remains cm's" in text
    assert "neither pro nor root authors em science" in text


def test_direct_router_keeps_relay_and_depth_bounded() -> None:
    router = _text(ROUTER)
    assert "max_subagent_depth=2" in router
    assert "same-direction direct channel" in router
    assert "cross-direction relay remains root-only" in router
    assert "root alone contacts the user" in router
