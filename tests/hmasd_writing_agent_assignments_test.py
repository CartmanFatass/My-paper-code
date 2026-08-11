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


def _opening_semantic_meaning_is_sufficient(message: str) -> bool:
    """Test-only semantic probe; this is not a runtime message validator."""

    blocks = message.strip().split("\n\n")
    opening = blocks[0]
    if len(blocks) > 1 and not any(
        cue in opening.lower()
        for cue in ("combined", "brought together", "must", "requested", "changed")
    ):
        # A heading may be present, but it is never required or prescribed.
        opening = blocks[1]
    normalized = opening.lower()
    return (
        any(cue in normalized for cue in ("combined", "brought together", "must", "requested", "changed"))
        and any(cue in normalized for cue in ("agents.md", "session_workspace_contract.md"))
        and any(cue in normalized for cue in ("two files", "both files", "relationship"))
        and any(cue in normalized for cue in ("wdm", "owner", "responsible", "next"))
        and any(cue in normalized for cue in ("conflict", "resolved", "cannot accept"))
    )


def _task_relevant_factual_tail_is_present(message: str) -> bool:
    """Check only broad evidence layers; do not prescribe a packet or field list."""

    if "\n\n" not in message:
        return False
    tail = message.strip().split("\n\n")[-1].lower()
    return (
        any(cue in tail for cue in ("paths", ".md", "artifact", "scope"))
        and any(cue in tail for cue in ("action", "status", "changed", "terminal"))
        and any(cue in tail for cue in ("command", "evidence", "checked", "observed"))
        and any(cue in tail for cue in ("wdm", "root", "next", "unresolved", "uncertain"))
    )


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


def test_plain_language_first_contract_keeps_meaning_before_technical_detail() -> None:
    text = _normalized(SKILL)
    for cue_group in (
        ("requested or happened", "requested outcome"),
        ("why it matters", "why the outcome matters"),
        ("who acts next", "next responsible actor"),
        ("concrete objects", "concrete files, objects or decisions"),
        ("their relationship", "how they relate", "causal relationship"),
        (
            "responsible owner",
            "who owns each action",
            "owner of the relevant action",
            "owner of each action or decision",
        ),
        ("consequence", "what breaks"),
        ("non-obvious task-local term", "non-obvious task-local term when it first appears"),
        (
            "paths, fields, abbreviations, commands, statuses, or evidence",
            "fields, paths, abbreviations, commands or evidence",
            "paths, commands, statuses and evidence",
            "exact fields or other mechanical anchors",
        ),
    ):
        assert any(cue in text for cue in cue_group), cue_group

    result_section = _normalized_text(_section(SKILL, "## Results and recovery"))
    conclusion_markers = ("outcome-first prose", "what was found or changed")
    conclusion_positions = [
        result_section.index(marker)
        for marker in conclusion_markers
        if marker in result_section
    ]
    assert conclusion_positions
    assert min(conclusion_positions) < result_section.index("paths, commands, statuses and evidence")
    for cue_group in (
        ("assignment", "scope", "owned paths"),
        ("artifact", "files", "paths"),
        ("action", "status", "changed"),
        ("commands", "evidence", "observed"),
        ("unresolved", "next", "owner"),
        ("residual uncertainty", "remains uncertain", "unfinished"),
    ):
        assert any(cue in text for cue in cue_group), cue_group


def test_varied_openings_preserve_meaning_and_factual_tail_layers() -> None:
    valid = (
        "Root combined the frozen edits to `AGENTS.md` and "
        "`docs/project/SESSION_WORKSPACE_CONTRACT.md`. The two files must describe "
        "the same plain-language rule; WDM owns resolving any disagreement, and Root "
        "cannot accept the combined change until that conflict is resolved. This is "
        "the union-semantics check."
    )
    alternate_valid = (
        "Root brought together the edits to `AGENTS.md` and "
        "`docs/project/SESSION_WORKSPACE_CONTRACT.md`. Both files explain one rule, "
        "WDM resolves a disagreement, and Root waits when the conflict is unresolved."
    )
    varied_valid = (
        "The requested union change updates `AGENTS.md` and "
        "`docs/project/SESSION_WORKSPACE_CONTRACT.md` so both files describe one rule. "
        "WDM is responsible for the disagreement, and Root acts next after the conflict "
        "is resolved."
    )
    ambiguous = "Union semantics are complete; run integration."
    missing_owner = (
        "Root combined edits to `AGENTS.md` and `docs/project/SESSION_WORKSPACE_CONTRACT.md`. "
        "The two files must describe one rule, but the conflict remains unresolved."
    )
    missing_relationship = (
        "Root combined the edits to `AGENTS.md` and `docs/project/SESSION_WORKSPACE_CONTRACT.md`. "
        "WDM owns the result, and Root cannot accept it until the conflict is resolved."
    )
    valid_with_tail = (
        valid
        + "\n\n"
        + "Paths/artifacts: `AGENTS.md` and `docs/project/SESSION_WORKSPACE_CONTRACT.md`; "
        "action/status: changed and ready; command/evidence: focused checks observed; "
        "WDM is next owner and no unresolved uncertainty remains."
    )
    headed_valid = (
        "Integration outcome\n\n"
        + valid
        + "\n\n"
        + "Paths/artifacts: `AGENTS.md` and `docs/project/SESSION_WORKSPACE_CONTRACT.md`; "
        "action/status: changed and ready; command/evidence: focused checks observed; "
        "WDM is next owner and no unresolved uncertainty remains."
    )
    narrative_only = (
        "Root combined the two files because they must describe one rule. WDM resolves "
        "any disagreement, and Root waits when the conflict is unresolved."
    )
    fields_only_tail = (
        "status=TERMINAL; paths=`AGENTS.md`; command=integration; evidence=pending; "
        "owner=WDM."
    )
    fields_only = "Technical details only follow.\n\n" + fields_only_tail

    assert _opening_semantic_meaning_is_sufficient(valid)
    assert _opening_semantic_meaning_is_sufficient(alternate_valid)
    assert _opening_semantic_meaning_is_sufficient(varied_valid)
    assert not _opening_semantic_meaning_is_sufficient(ambiguous)
    assert not _opening_semantic_meaning_is_sufficient(missing_owner)
    assert not _opening_semantic_meaning_is_sufficient(missing_relationship)
    assert _opening_semantic_meaning_is_sufficient(valid_with_tail)
    assert _task_relevant_factual_tail_is_present(valid_with_tail)
    assert _opening_semantic_meaning_is_sufficient(headed_valid)
    assert _task_relevant_factual_tail_is_present(headed_valid)
    assert not _task_relevant_factual_tail_is_present(narrative_only)
    assert not _opening_semantic_meaning_is_sufficient(fields_only)
    assert _task_relevant_factual_tail_is_present(fields_only)
    assert not (
        _opening_semantic_meaning_is_sufficient(narrative_only)
        and _task_relevant_factual_tail_is_present(narrative_only)
    )
    assert not (
        _opening_semantic_meaning_is_sufficient(fields_only)
        and _task_relevant_factual_tail_is_present(fields_only)
    )


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
    contract = _text(SESSION_CONTRACT)
    contract_match = re.search(
        r"(?m)^workflow_progress_event_names=(?P<events>[A-Z_]+(?:\|[A-Z_]+){4})\s*$",
        contract,
    )
    assert contract_match is not None
    events = tuple(contract_match.group("events").split("|"))
    assert events == (
        "DISPATCHED",
        "WRITES_COMPLETE",
        "TESTS_COMPLETE",
        "REVIEW_READY",
        "TERMINAL",
    )
    # Read only the Skill's canonical first paragraph.  Later mechanical
    # tokens (for example a `COMPLETE` marker) are not progress events.
    first_paragraph = section.split("### Progress-event communication", 1)[1].strip().split("\n\n", 1)[0]
    assert tuple(re.findall(r"`([A-Z_]+)`", first_paragraph)) == events
    for cue in (
        "five session-defined names",
        "single reporting source",
        "status-only, non-accepting observation",
        "emit each named observation at most once",
        "adjacent relevant observations may share one outcome-first report",
        "workflow_progress_event_emission=each_relevant_event_at_most_once|adjacent_observations_may_share_one_report",
        "never acceptance",
        "scheduler",
        "queue",
        "ledger",
        "background callback",
        "retry state",
        "admission",
        "not a second state machine",
        "do not create continuity",
        "background-context isolation",
        "not zero context",
        "event name never replaces the explanation",
        "no named heading or fixed record shape is required",
    ):
        assert cue in text
    for cue in (
        "workflow_progress_event_owner=wdm",
        "workflow_progress_event_meanings=dispatched:actions_started|writes_complete:all_writers_terminal_and_exact_changed_paths_frozen|tests_complete:required_test_layers_completed_with_evidence|review_ready:exact_union_and_evidence_frozen_for_one_reviewer|terminal:terminal_conclusion_returned_to_root",
        "workflow_progress_event_semantics=status_observations_only|not_scheduler|not_queue|not_ledger|not_background_callback|not_retry_state|not_admission|not_acceptance_token",
        "workflow_progress_event_transport=root_task_or_report_boundary_only",
        "workflow_terminal_event_not_acceptance=true",
    ):
        assert cue in _normalized(SESSION_CONTRACT)


def test_risk_reviewer_and_manager_capacity_guidance_is_explicit() -> None:
    text = _normalized_text(
        _section(SKILL, "### Risk, reviewer and manager-capacity guidance")
    )
    contract = _normalized(SESSION_CONTRACT)
    high_start = text.index("`high`")
    bounded_start = text.index("`bounded_contract`")
    high_clause = text[high_start:bounded_start]
    assert all(
        consequence in high_clause
        for consequence in ("authority", "topology", "cross-owner", "shared-contract")
    )
    assert "requires the registered read-only auditor" in high_clause
    assert "may skip" not in high_clause
    for cue in (
        "classify the assignment package by semantic consequence before dispatch",
        "never by file count",
        "`high` covers authority, topology, cross-owner or shared-contract impact",
        "requires the registered read-only auditor",
        "`bounded_contract` covers a stable cross-file contract within one owner",
        "a clear route may skip a new auditor when wdm records its rationale",
        "`low_causal_repair` covers wording, a recognizer or one bounded assertion family",
        "wdm may skip the auditor with rationale",
        "routing choice, not an admission state, gate or second owner",
        "workflow_change_risk_tiers",
        "workflow_route_table_policy",
        "missing, ambiguous, conflicting or authority-crossing route uses the bounded registered auditor",
        "exactly one integrated advisory reviewer",
        "dispatched only after the paths and direct evidence are frozen",
        "reviewer is read-only and advisory",
        "its review cannot accept the package or replace wdm/root ownership",
        "skipping the auditor never means skipping this reviewer",
        "paths and direct evidence are frozen",
        "manager capacity is an actionability check",
        "useful owned work",
        "useful action or matching leaf capacity",
        "not a quota, reservation, scheduler or pool",
    ):
        assert cue in text
    for cue in (
        "workflow_auditor_policy=high_requires_auditor|bounded_contract_clear_route_may_skip_with_wdm_rationale|low_causal_repair_may_skip_with_wdm_rationale|missing_ambiguous_conflicting_or_authority_crossing_route_requires_auditor",
        "workflow_auditor_skip_evidence=concrete_wdm_rationale|focused_causal_evidence_on_all_frozen_consumed_bytes",
        "workflow_integrated_review=exactly_one_advisory_reviewer_after_tests_complete_and_review_ready",
        "workflow_reviewer_authority=advice_only_no_acceptance",
        "workflow_root_l1_start_guidance_not=quota|reservation|scheduler|admission_gate|pool|runtime_authorization",
    ):
        assert cue in contract
    naming_and_boundary = _normalized(SKILL)
    for cue in (
        "wm_<purpose>",
        "em_<direction>",
        "cm_<purpose_or_direction>",
        "session contract and registered roles define the shared worktree, child git, routing and acceptance boundaries",
    ):
        assert cue in naming_and_boundary
    for cue in (
        "managed_worktree_allocation=one_writable_l1_assignment_one_root_managed_worktree",
        "shared_l1_worktree_conditions=same_frozen_base|exact_disjoint_paths|no_l2_git|one_shared_l1_slice_candidate|root_records_after_all_children_finish",
    ):
        assert cue in contract


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
        "no named heading or token is required",
        "no named heading, field list, record shape",
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


def test_result_shape_has_semantic_conclusion_and_compact_factual_tail() -> None:
    text = _normalized(SKILL)
    for cue_group in (
        ("what was found or changed", "what was found or changed"),
        ("why it satisfies", "why that matters"),
        ("who acts next", "next responsible actor"),
        ("direct consequence", "consequence"),
        ("residual uncertainty", "remains uncertain"),
        ("compact factual tail", "factual tail"),
        ("paths", "artifact"),
        ("commands", "statuses"),
        ("evidence", "observed"),
    ):
        assert any(cue in text for cue in cue_group), cue_group
    assert "terminal token is useful only as an anchor" in text
    assert "no named heading or token is required" in text or "no named heading, field list, record shape" in text


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
