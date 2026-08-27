from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return " ".join(
        (ROOT / path).read_text(encoding="utf-8").split()
    ).casefold()


def test_code_review_is_a_top_level_engineering_seam_not_a_generic_trigger() -> None:
    text = _read(".agents/skills/code-review/SKILL.md")
    frontmatter = text.split("---", 2)[1]

    assert "top-level hmasd cm or root" in frontmatter
    assert "use when the user wants" not in frontmatter
    assert "only a top-level hmasd cm or root" in text
    assert "never use this skill for em scientific review" in text
    assert "never invoke it from a leaf" in text
    assert "setup-matt-pocock-skills" not in text
    assert "issue-tracker.md" not in text


def test_code_review_spawns_exactly_two_direct_reviewer_leaves() -> None:
    text = _read(".agents/skills/code-review/SKILL.md")

    assert "exactly two direct `hmasd-reviewer` leaves" in text
    assert "standards axis" in text
    assert "spec axis" in text
    assert "never invoke `code-review`" in text
    assert "never spawn or delegate" in text
    assert "return only to the spawning cm or root" in text


def test_reviewer_leaf_cannot_reenter_code_review_or_delegate() -> None:
    text = _read(".codex/agents/hmasd-reviewer.toml")

    assert "never invoke or load the `code-review` skill" in text
    assert "perform the assigned standards or spec axis directly" in text
    assert "never spawn or delegate another agent" in text


def test_cm_owns_two_axis_code_review_but_em_science_does_not() -> None:
    cm_skill = _read(".agents/skills/hmasd-cm-task/SKILL.md")
    cm_prompt = _read(".codex/prompts/hmasd-cm.md")
    em_skill = _read(".agents/skills/hmasd-em-task/SKILL.md")
    em_prompt = _read(".codex/prompts/hmasd-em.md")

    assert "`code-review`" in cm_prompt
    assert "standards" in cm_prompt
    assert "spec" in cm_prompt
    assert "two direct" in cm_prompt
    assert "hmasd-reviewer" in cm_prompt
    assert ".codex/prompts/hmasd-cm.md" in cm_skill
    assert "top-level review seams" in cm_skill

    assert "never invokes `code-review`" in em_prompt
    assert "research critic" in em_prompt
    assert "agentify" in em_prompt
    assert ".codex/prompts/hmasd-em.md" in em_skill
    assert "direct leaf interfaces" in em_skill
