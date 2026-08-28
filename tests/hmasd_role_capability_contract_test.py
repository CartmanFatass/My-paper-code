from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


ROLE_MARKERS = {
    "ROOT.md": (
        "original observable outcome", "protected invariants", "safe reproduction",
        "discriminating hypothesis", "end-to-end acceptance",
    ),
    "PORTFOLIO.md": (
        "scientific quality floor", "complementarity", "common failure risk",
        "transport availability", "shared assumptions", "premature homogenization",
        "`FUSE`", "`SPINOFF`", "lifecycle",
    ),
    "EM.md": (
        "ALGORITHM_PRINCIPLES.md", "estimand", "strongest simple null",
        "semi-Markov", "information", "credit flow", "owns the complete Pro prompt",
        "neutral grounding", "favored answer", "NO_MATERIAL_INSIGHT", "unused evidence",
        "same-source agreement", "`INNOVATOR`", "`CONVERGENCE`", "may omit CM",
        "negative or ambiguous observation", "Self-critique alone",
        "explicit no-change judgment",
    ),
    "CM.md": (
        "question-relevant output", "engineering failure", "hmasd_run.py",
        "hmasd_resource_preflight.py", "CPP_BATCHED_ENVIRONMENT_PRODUCTION_POLICY_V1.md",
        "semantic Implementer", "routine Implementer", "serial Python scaffold",
        "few changed lines never make a semantic change routine",
    ),
    "CM_SCOUT.md": (
        "symbols", "callers", "state ownership", "tensor shapes", "reopen one",
    ),
    "RESEARCH_SCOUT.md": (
        "source facts", "inference", "PDF", "fidelity recheck", "uncertainty",
    ),
    "RESEARCH_CRITIC.md": (
        "passive noise", "optimizer exposure", "partner co-adaptation", "recheck one",
    ),
    "REVIEWER.md": (
        "normal-path likelihood", "material effect", "repair cost", "residual risk", "reread one",
    ),
    "VERIFIER.md": (
        "proof root", "same process handle", "observation bound", "duplicate launch",
    ),
    "EXPERIMENT_OPERATOR.md": (
        "hmasd_run.py", "exact command", "foreground handle", "terminal witness",
    ),
    "GENERAL_LEAF.md": (
        "weakly coupled", "owner judgment", "safe alternative", "assigned output",
    ),
    "PRO_TRANSPORT.md": (
        "one exact frozen prompt file", "hmasd-agentify-transport", "scientific judgment",
        "single mechanics reference", "Do not invent another UI",
    ),
    "ENGINEERING_TRANSPORT.md": (
        "parent-frozen question", "hmasd-agentify-transport", "technical acceptance",
        "single mechanics reference", "Do not invent another UI",
    ),
    "RESEARCH_INNOVATOR.md": (
        "mechanism family", "strongest simple null", "observable prediction",
        "retirement condition", "independent",
    ),
    "RESEARCH_PRINCIPLES_ANALYST.md": (
        "stochastic game", "information sets", "semi-Markov clocks",
        "identity ownership", "optimizer exposure",
    ),
    "IMPLEMENTER.md": (
        "probability", "gradient", "RNG", "checkpoint", "production-capable",
    ),
    "ROUTINE_IMPLEMENTER.md": (
        "behavior-preserving", "reversible", "focused tests", "owned paths",
    ),
}


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_every_current_role_has_owned_method_and_local_recovery() -> None:
    for filename, markers in ROLE_MARKERS.items():
        text = _read(f".agents/roles/{filename}")
        for heading in ("## Mission", "## Normal path", "## Bounded recovery", "## Stop and return"):
            assert heading in text, f"{filename} lacks {heading}"
        assert "Conclusion first" in text
        normalized = _flat(text)
        for marker in markers:
            assert marker in normalized, f"{filename} lacks {marker}"


def test_top_level_skills_point_to_their_own_role_only() -> None:
    mapping = {
        "hmasd-root-task": "ROOT.md",
        "hmasd-portfolio-task": "PORTFOLIO.md",
        "hmasd-em-task": "EM.md",
        "hmasd-cm-task": "CM.md",
    }
    for skill_name, own_role in mapping.items():
        text = _read(f".agents/skills/{skill_name}/SKILL.md")
        assert f".agents/roles/{own_role}" in text
        for other_role in set(mapping.values()) - {own_role}:
            assert f".agents/roles/{other_role}" not in text
        assert "read only" in text.lower()
    assert "Portfolio fan-out and join" in _read(
        ".agents/skills/hmasd-portfolio-task/SKILL.md"
    )
    assert "Portfolio fan-out and join" not in _read(
        ".agents/skills/hmasd-cm-task/SKILL.md"
    )
    portfolio_skill = _read(".agents/skills/hmasd-portfolio-task/SKILL.md")
    em_skill = _read(".agents/skills/hmasd-em-task/SKILL.md")
    cm_skill = _read(".agents/skills/hmasd-cm-task/SKILL.md")
    assert "Portfolio ↔ EM" in portfolio_skill
    assert "EM ↔ CM" not in portfolio_skill
    assert "Portfolio ↔ EM" in em_skill and "EM ↔ CM" in em_skill
    assert "EM ↔ CM" in cm_skill
    assert "Portfolio ↔ EM" not in cm_skill
    assert "Dispatch and task creation" not in cm_skill


def test_agentify_skill_owns_strict_mechanics_not_scientific_prompt_authoring() -> None:
    skill = _read(".agents/skills/hmasd-agentify-transport/SKILL.md")
    manual = _read("docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md")
    combined = f"{skill}\n{manual}"
    for marker in (
        "agentify_review_query", "promptPath", "verifyExisting",
        "agentify_review_observe", "input-mismatch state", "natural completion",
        "provider-visible user turn", "exact frozen prompt file",
    ):
        assert marker in combined
    assert "agentify_query` as the Send path" not in combined
    assert "transport must not compose" in combined
    assert "tool-local" in combined
    assert "task identity" in combined
    assert "Renaming the WORK, assignment, operation, key, conversation, leaf, or task" in manual


def test_role_documents_do_not_import_other_role_methods_or_global_enums() -> None:
    role_names = set(ROLE_MARKERS)
    top_level_fields = (
        "Outcome: DONE | WAITING | FAILED | CANCELLED",
        "Portfolio action: NONE |",
        "Scientific status: IN_PROGRESS |",
        "Engineering status: IN_PROGRESS |",
        "Innovation status: CANDIDATE |",
        "Principles status: DEFECTS |",
        "Implementation observation: IMPLEMENTED |",
        "Routine implementation observation: IMPLEMENTED |",
    )
    for filename in role_names:
        text = _read(f".agents/roles/{filename}")
        for other in role_names - {filename}:
            assert f".agents/roles/{other}" not in text
        assert all(field not in text for field in top_level_fields)


def test_external_research_mechanisms_have_current_role_owners() -> None:
    em = _read(".agents/roles/EM.md")
    portfolio = _read(".agents/roles/PORTFOLIO.md")
    for marker in (
        "genuinely different approach families",
        "same scope without EM's favored answer",
        "reopen a blocked route only for a genuinely new mechanism",
        "unused evidence and unasked answer-changing questions",
        "send a meaning-complete WORK to CM before `SYNTHESIS_READY`",
        "Program, test, or command success is never scientific acceptance",
        "same-source agreement", "search coverage",
        "primary evidence", "direct CM observation", "concrete counterexample",
        "specific Pro objection", "Self-critique alone", "explicit no-change judgment",
    ):
        assert marker in _flat(em)
    assert "whether positive, negative, or null" in _flat(em)
    assert "EM independently interprets every leaf result" in _flat(em)
    assert "A route must return" not in em
    for marker in (
        "scientific quality floor", "shared assumptions", "relatively independent validation",
        "premature homogenization", "Do not manufacture numeric VOI", "Elo", "vote",
    ):
        assert marker in _flat(portfolio)
