from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/hmasd-writing-agent-assignments/SKILL.md"
SESSION_CONTRACT = ROOT / "docs/project/SESSION_WORKSPACE_CONTRACT.md"
REFERENCES = SKILL.parent / "references"
AGILE = ROOT / ".agents/skills/hmasd-agile-research-development/SKILL.md"
CODE_GUIDE = (
    ROOT / ".agents/skills/hmasd-agile-research-development/references/code-context-guide.md"
)
OLD_BOOTSTRAP = (
    ROOT
    / ".agents/skills/hmasd-agile-research-development/references/project-cognition-bootstrap-prompt.md"
)
OLD_EXAMPLES = (
    ROOT
    / ".agents/skills/hmasd-agile-research-development/references/assignment-brief-examples.md"
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_text(path).split()).lower()


def _normalized_text(text: str) -> str:
    return " ".join(text.split()).lower()


def _section(path: Path, heading: str) -> str:
    """Return one markdown section without coupling tests to line wrapping."""

    text = _text(path)
    start = text.index(heading)
    end = text.find("\n### ", start + len(heading))
    if end == -1:
        end = len(text)
    return text[start:end]


def test_skill_trigger_and_task_model_recipe_are_explicit() -> None:
    text = _normalized(SKILL)
    assert "designing a task-scoped subagent or root-relayed owner interface" in text
    assert "writing a concrete assignment or message" in text
    assert "reviewing whether an existing interface preserves enough meaning and capability" in text
    assert "self-contained natural-language model" in text
    assert "without reconstructing parent history" in text
    assert 'fork_turns="1"' in text
    assert "one forked turn is background only" in text
    assert "fork_turns=none" in text
    assert "never excuses omitting a self-contained brief" in text
    assert "do not encode direct sibling contact" in text
    assert "manager-session or replacement-task continuity" in text
    for cue in (
        "why the task exists now",
        "concrete failure, conflict or limitation",
        "how the named modules, people, pages, files or sessions interact",
        "decisions already frozen",
        "protected meaning, invariants, exclusions",
        "ordinary local judgment",
        "bounded recovery",
        "evidence that demonstrates the requested outcome",
    ):
        assert cue in text
    assert "parent is a context compiler" in text


def test_native_payload_and_file_backed_assignment_boundary_is_explicit() -> None:
    section = _normalized_text(
        _section(SKILL, "### Native payload and file-backed assignment boundary")
    )
    for cue in (
        "no assignment-file locator",
        "complete native payload",
        "exact authoritative assignment",
        "must not search for, reconstruct or infer an assignment file",
        "fails closed to the parent",
        "file-backed assignment",
        "exact path, hash and authority",
        "locator or integrity fact",
        "not a workflow admission, acceptance or continuity mechanism",
        "mandatory role/skill immediate references",
        "distinct from assignment reconstruction",
        "`rg` remains",
        "explicitly named fields or evidence locators",
        "unsourced assignment discovery",
    ):
        assert cue in section


def test_child_briefs_name_validation_scope_and_evidence_ownership() -> None:
    text = _normalized(SKILL)
    section = _normalized_text(
        _section(SKILL, "### Validation ownership and evidence scope")
    )
    for cue in (
        "validation layer",
        "exact paths",
        "smallest direct evidence",
        "later evidence",
        "wdm or root",
        "direct postcondition",
        "integrated diff",
        "cross-slice conclusion",
        "whole suite",
        "smallest focused checks",
    ):
        assert cue in section
    # Semantic brief contents remain distinct from a mechanical schema or
    # admission rule.
    assert "not a second schema or admission gate" in section


def test_progress_events_are_the_exact_wdm_observation_vocabulary() -> None:
    section = _section(SKILL, "### Progress-event communication")
    text = _normalized_text(section)
    events = (
        "DISPATCHED",
        "WRITES_COMPLETE",
        "TESTS_COMPLETE",
        "REVIEW_READY",
        "TERMINAL",
    )
    vocabulary_prefix = section.split("WDM publishes", 1)[0]
    assert tuple(re.findall(r"`([A-Z_]+)`", vocabulary_prefix)) == events
    for cue in (
        "wdm-owned status observation",
        "owner and meaning",
        "workflow_progress_event_owner",
        "workflow_progress_event_meanings",
        "defining contract",
        "reporting procedure",
        "status-only observations",
        "never acceptance",
        "scheduler",
        "queue",
        "ledger",
        "background callback",
        "retry state",
        "admission",
        "only that the owner returned its terminal conclusion",
        "background-context isolation",
        "not zero context",
    ):
        assert cue in text


def test_risk_reviewer_and_manager_capacity_guidance_is_explicit() -> None:
    text = _normalized_text(
        _section(SKILL, "### Risk, reviewer and manager-capacity guidance")
    )
    for cue in (
        "high-risk",
        "authority",
        "topology",
        "cross-owner",
        "shared-contract",
        "read-only auditor",
        "low-risk",
        "one-file wording",
        "test-only",
        "concrete rationale",
        "exactly one integrated advisory reviewer",
        "paths and direct evidence are frozen",
        "useful owned work",
        "useful action or matching leaf capacity",
        "not a quota, reservation, scheduler or pool",
    ):
        assert cue in text
    naming_and_boundary = _normalized(SKILL)
    for cue in (
        "wm_<purpose>",
        "em_<direction>",
        "cm_<purpose_or_direction>",
        "one root-managed worktree",
        "exact-disjoint l2 writers",
        "child git, routing and acceptance authority remain forbidden",
    ):
        assert cue in naming_and_boundary


def test_skill_points_l1_display_labels_to_the_shared_contract() -> None:
    skill = _normalized(SKILL)
    contract = _normalized(SESSION_CONTRACT)
    assert "l1_user_facing_display_contract" in skill
    assert "docs/project/session_workspace_contract.md" in skill
    assert "l1 user-facing display names" in skill
    for cue in (
        "wm_<purpose>",
        "em_<direction>",
        "cm_<purpose_or_direction>",
        "immutable internal task ids",
        "research_execution=false",
        "science_state_changed=false",
    ):
        assert cue in skill
        assert cue in contract


def test_skill_preserves_semantics_without_a_schema_or_second_gate() -> None:
    text = _normalized(SKILL)
    for cue in (
        "not a schema",
        "another authority",
        "do not require fixed headings, field names, a record schema",
        "not a checklist admission gate",
        "packet validator",
        "not a queue",
        "not a ledger",
        "second acceptance owner",
    ):
        assert cue in text
    assert "never as mandatory templates" in text


def test_skill_requires_action_capability_and_rejects_false_completion() -> None:
    skill = _normalized(SKILL)
    examples = _normalized(REFERENCES / "assignment-brief-examples.md")
    for cue in (
        "tool recognition",
        "action-capability evidence",
        "current state",
        "permitted transition action",
        "post-action observation",
        "actual answer, artifact, changed file, sent request",
        "model strength",
        "assignment quality",
        "file-only communication",
        "low-semantic communication",
        "fork_turns=none",
        "zero context",
        "deterministic script",
        "semantic sufficiency",
    ):
        assert cue in skill
    for cue in (
        "non-code transport",
        "observable conflict",
        "red baseline",
        "do not infer completion from a",
        "response fragment",
        "actual answer",
        "selected model label",
        "open the model picker, select pro",
        "composer visibly shows pro after the selection",
        "proof that the question was actually sent and answered",
    ):
        assert cue in examples


def test_result_shape_starts_with_natural_language_conclusion() -> None:
    text = _normalized(SKILL)
    assert "begins with a natural-language conclusion" in text
    assert "compact factual tail" in text
    assert "terminal token is useful only as an anchor" in text
    assert "fixed headings, field names" in text


def test_reference_ownership_moves_general_material_out_of_agile_skill() -> None:
    assert SKILL.is_file()
    bootstrap = REFERENCES / "project-cognition-bootstrap-prompt.md"
    examples = REFERENCES / "assignment-brief-examples.md"
    assert bootstrap.is_file()
    assert examples.is_file()
    assert not OLD_BOOTSTRAP.exists()
    assert not OLD_EXAMPLES.exists()
    agile = _normalized(AGILE)
    guide = _normalized(CODE_GUIDE)
    assert "hmasd-writing-agent-assignments" in agile
    assert "hmasd-writing-agent-assignments" in guide
    assert "references/code-context-guide.md" in agile
    assert ".agents/skills/hmasd-agile-research-development/references/project-cognition-bootstrap-prompt.md" not in agile
    assert ".agents/skills/hmasd-agile-research-development/references/assignment-brief-examples.md" not in agile
    assert "code context" in guide
    assert "focused on code context" in guide


def test_reverse_intake_brief_forbids_full_map_transport_and_semantic_writer_inference() -> None:
    text = _normalized(SKILL)
    for cue in (
        "small semantic delta rather than the full map",
        "canonical source locator",
        "candidate-target locator",
        "git revision locator",
        "exact old/new text or unified patch",
        "frozen semantics and consequences",
        "assignment-specific temporary `.patch`",
        "payload-presence and utf-8/lf checks",
        "must not load explorer mechanical",
        "normalize or merge text",
        "infer a target or interpret scientific meaning",
        "full-map message",
        "split/encoded payload",
        "git revision is only a source locator",
        "large message truncation is payload transport",
        "newline or pipe damage is serialization",
        "not a dispatcher, queue or automatic recovery mechanism",
    ):
        assert cue in text, cue
