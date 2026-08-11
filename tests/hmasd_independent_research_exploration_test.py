"""Consumer-level Explorer contract checks; science remains Explorer-owned."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _flat(*paths: str) -> str:
    return " ".join("\n".join((ROOT / p).read_text(encoding="utf-8") for p in paths).split()).lower()


def test_explorer_is_direction_scoped_and_keeps_scientific_choices_with_em() -> None:
    text = _flat(".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md", ".agents/skills/hmasd-independent-research-exploration/SKILL.md", "AGENTS.md")
    assert "scope=one direction:<id>" in text
    assert "em owns a direction's scientific question, candidate and comparator choice" in text
    assert "root_cross_owner_relay_authority=exclusive" in text
    assert "cm owns code, runner, adapter, package, dependency" in text


def test_engineering_gaps_and_operator_recovery_stay_with_cm() -> None:
    text = _flat(".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md", ".agents/roles/CODE_PROJECT_MANAGER.md", ".agents/skills/hmasd-agile-research-development/SKILL.md")
    assert "code, runner, adapter, package, dependency" in text
    assert "are work, not park or `blocked`" in text
    assert "pre-full recovery" in text
    assert "operator receives only an exact run-ready assignment" in text


def test_return_and_optional_action_map_installation_are_distinct() -> None:
    text = _flat(".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md", "docs/project/SESSION_WORKSPACE_CONTRACT.md")
    assert "technical-result return and scientific intake" in text
    assert "direction action map semantic-delta installation" in text
    assert "never sends a full map" in text
    assert "root alone accepts the complete direction action map" in text


def test_review_transport_and_dispositions_do_not_transfer_owner_authority() -> None:
    text = _flat(".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md", ".agents/skills/hmasd-independent-research-exploration/SKILL.md", ".agents/roles/EXTERNAL_PRO.md")
    assert "explorer_project_alignment_audit" in text
    assert "explorer transport" in text
    assert "code_science_alignment_audit" in text
    assert "ordinary b has no automatic pro call" in text
    assert "technical acceptance remains cm's" in text
