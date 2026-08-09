from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/hmasd-writing-agent-assignments/SKILL.md"
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


def test_skill_trigger_and_task_model_recipe_are_explicit() -> None:
    text = _normalized(SKILL)
    assert "designing a subagent or cross-session interface" in text
    assert "writing a concrete assignment or message" in text
    assert "reviewing whether an existing interface preserves enough meaning and capability" in text
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


def test_scheduler_native_handle_is_a_factual_tail_not_task_context() -> None:
    text = _normalized(SKILL)
    assert "prose-first" in text
    assert "exact native desktop handle `{threadid, hostid}`" in text
    assert "lifecycle/routing identity" in text
    assert "canonical files are artifacts or continuity only" in text
    assert "never proof of llm identity" in text


def test_scheduler_write_ownership_is_explicit_and_file_identity_is_not_required() -> None:
    text = _normalized(SKILL)
    for cue in (
        "exact cooperative write paths",
        "direction owner writes/returns only",
        "portfolio explorer alone writes shared portfolio continuity/capsule state",
        "treatment cpm owner writes only its ticket worktree",
        "integration cpm owner writes the shared mainline integration surface",
        "writers of one exact file serialize",
        "disjoint exact files may overlap",
        "does not relay semantic results, scan tasks or maintain a queue/monitor/registry",
    ):
        assert cue in text
    for stale in ("handshake", "binding-ready", "identity_observation", "session binding"):
        assert stale not in text
