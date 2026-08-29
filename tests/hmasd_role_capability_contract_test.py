from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


ROLE_MARKERS = {
    "ROOT.md": (
        "original observable outcome", "protected invariants", "safe reproduction",
        "discriminating hypothesis", "end-to-end acceptance", "existing obligation",
        "authority classification", "conflicting propositions", "fixed diff/base",
        "material finding", "same unfinished WORK", "unconsumed result",
    ),
    "PORTFOLIO.md": (
        "scientific quality floor", "complementarity", "common failure risk",
        "transport availability", "shared assumptions", "premature homogenization",
        "globally comparable qualitative priority", "unused capacity",
        "historical decision note", "`FUSE`", "`SPINOFF`", "lifecycle",
        "Before dispatch", "current `PORTFOLIO.md` authority", "precede every native send",
    ),
    "EM.md": (
        "ALGORITHM_PRINCIPLES.md", "estimand", "strongest simple null",
        "semi-Markov", "information", "credit flow", "owns the complete Pro prompt",
        "neutral grounding", "favored answer", "NO_MATERIAL_INSIGHT", "unused evidence",
        "same-source agreement", "`INNOVATOR`", "`CONVERGENCE`", "may omit CM",
        "negative or ambiguous observation", "Self-critique alone",
        "aggregate no-material-change", "Before `HANDOFF_READY`", "durable scientific authority",
        "preserve the scientific stage actually reached", "direction-owned terminal-gap note",
    ),
    "CM.md": (
        "question-relevant output", "engineering failure", "hmasd_run.py",
        "hmasd_resource_preflight.py", "CPP_BATCHED_ENVIRONMENT_PRODUCTION_POLICY_V1.md",
        "semantic Implementer", "routine Implementer", "serial Python scaffold",
        "few changed lines never make a semantic change routine", "inbound acceptance",
        "protected semantics", "fixed diff/base", "material finding", "exceptional Verifier",
        "Report the current stage, not the last failed attempt",
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
        "complete transport skill", "optional tool-argument reference", "Do not invent another UI",
    ),
    "ENGINEERING_TRANSPORT.md": (
        "parent-frozen question", "hmasd-agentify-transport", "technical acceptance",
        "complete transport skill", "optional tool-argument reference", "Do not invent another UI",
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


TOP_LEVEL_SKILLS = {
    "ROOT.md": "hmasd-root-task",
    "PORTFOLIO.md": "hmasd-portfolio-task",
    "EM.md": "hmasd-em-task",
    "CM.md": "hmasd-cm-task",
}


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_every_current_role_has_owned_method_and_local_recovery() -> None:
    for filename, markers in ROLE_MARKERS.items():
        if filename in TOP_LEVEL_SKILLS:
            text = _read(f".agents/skills/{TOP_LEVEL_SKILLS[filename]}/SKILL.md")
        else:
            text = _read(f".agents/roles/{filename}")
        for heading in ("## Mission", "## Normal path", "## Bounded recovery", "## Stop and return"):
            assert heading in text, f"{filename} lacks {heading}"
        assert "Conclusion first" in text
        normalized = _flat(text)
        for marker in markers:
            assert marker in normalized, f"{filename} lacks {marker}"


def test_top_level_skills_are_self_contained_role_methods() -> None:
    agents = _read("AGENTS.md")
    assert "only entry pointers" not in agents
    assert "complete role-local method" in agents

    for own_role, skill_name in TOP_LEVEL_SKILLS.items():
        text = _read(f".agents/skills/{skill_name}/SKILL.md")
        assert ".agents/roles/" not in text
        assert "../../../AGENTS.md" in text
        assert "../../../docs/project/WORKFLOW_PROTOCOL.md" in text
        for heading in ("## Mission", "## Normal path", "## Bounded recovery", "## Stop and return"):
            assert heading in text, f"{skill_name} lacks {heading}"
        skill_dir = ROOT / ".agents" / "skills" / skill_name
        for relative in ("../../../AGENTS.md", "../../../docs/project/WORKFLOW_PROTOCOL.md"):
            assert (skill_dir / relative).resolve().is_file(), f"broken skill reference: {relative}"

    for retired_role in TOP_LEVEL_SKILLS:
        assert not (ROOT / ".agents" / "roles" / retired_role).exists()

    assert "Portfolio fan-out and join" in _flat(_read(
        ".agents/skills/hmasd-portfolio-task/SKILL.md"
    ))
    assert "Portfolio fan-out and join" not in _flat(_read(
        ".agents/skills/hmasd-cm-task/SKILL.md"
    ))
    portfolio_skill = _flat(_read(".agents/skills/hmasd-portfolio-task/SKILL.md"))
    em_skill = _flat(_read(".agents/skills/hmasd-em-task/SKILL.md"))
    cm_skill = _flat(_read(".agents/skills/hmasd-cm-task/SKILL.md"))
    assert "Portfolio ↔ EM" in portfolio_skill
    assert "EM ↔ CM" not in portfolio_skill
    assert "Portfolio ↔ EM" in em_skill and "EM ↔ CM" in em_skill
    assert "EM ↔ CM" in cm_skill
    assert "Portfolio ↔ EM" not in cm_skill
    assert "Dispatch and task creation" not in cm_skill


def test_agentify_skill_owns_strict_mechanics_not_scientific_prompt_authoring() -> None:
    skill = _read(".agents/skills/hmasd-agentify-transport/SKILL.md")
    manual = _read("docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md")
    agents = _read("AGENTS.md")
    for marker in (
        "agentify_review_query", "promptPath", "verifyExisting",
        "agentify_review_observe", "input-mismatch state", "natural completion",
        "provider-visible user turn", "exact frozen prompt file", "responsePath",
        "tab is not a conversation", "new provider conversation",
        "cannot authorize a replacement", "separately authorized strict operation",
    ):
        assert marker in skill
    assert "../../../docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md" in skill
    skill_dir = ROOT / ".agents" / "skills" / "hmasd-agentify-transport"
    manual_ref = skill_dir / "../../../docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md"
    assert manual_ref.resolve().is_file()
    assert "agentify_query` as the Send path" not in skill
    assert "transport must not compose" in skill
    assert "tool-local" in skill
    assert "task identity" in skill
    assert "This file is a compact reference for the current Agentify call surface" in manual
    assert "complete HMASD transport method" in manual
    assert "caller normally omits `promptSha256`" in manual
    for leaked_owner_term in (
        "top-level WORK", "material cycle", "Portfolio action", "Scientific status",
        "Engineering status", "replacement strict operation",
    ):
        assert leaked_owner_term not in skill
        assert leaked_owner_term not in manual
    assert "at most one automatic replacement" in agents
    assert "same top-level WORK" in agents


def test_em_transport_exhaustion_preserves_the_scientific_stage_reached() -> None:
    em = _flat(_read(".agents/skills/hmasd-em-task/SKILL.md"))
    agents = _flat(_read("AGENTS.md"))
    assert "before any valid synthesis, end with the unsynthesized gap" in em
    assert "after `SYNTHESIS_READY`, retain the bounded synthesis" in em
    assert "direction-owned terminal-gap note" in em
    assert "returns no lifecycle recommendation" in em
    assert "end without synthesis" not in em
    assert "owner's actually reached role fields and no lifecycle recommendation" in agents


def test_zero_send_recovery_is_causal_not_a_fixed_retry_gate() -> None:
    agents = _flat(_read("AGENTS.md"))
    em = _flat(_read(".agents/skills/hmasd-em-task/SKILL.md"))
    transport = _flat(_read(".agents/skills/hmasd-agentify-transport/SKILL.md"))
    assert "concrete non-sending repair changes the proven failure premise" in agents
    assert "There is no fixed attempt counter" in agents
    assert "same failure without a new fact stops" in agents
    assert "original assignment authorizes ordinary page-local recovery" in agents
    assert "does not create a Root or Portfolio decision" in agents
    assert "observable page and provider facts" in transport
    assert "tool failure predicate is diagnostic" in transport
    assert "owns ordinary page-local recovery" in transport
    assert "without returning to EM for each action" in transport
    assert "A clear failure predicate proves only that the automation path reported failure" in transport
    assert "current rendered content" in transport
    assert "decides whether to continue Send preparation" in transport
    assert "failed clear action proves only that the chosen action did not mutate" not in transport
    assert "elapsed time alone" in transport
    assert "does not impose an attempt count" in transport
    assert "same unchanged failure returns `ZERO_SEND_FAILED` again without a Send" in transport
    assert "has no fixed attempt count" in em
    assert "does not perform or micromanage browser actions" in em
    assert "parent supplies a concrete evidence-changing non-sending repair" not in transport
    assert "permits one bounded repair" not in agents


def test_cm_observer_gate_depends_on_proof_not_implementation_novelty() -> None:
    cm = _flat(_read(".agents/skills/hmasd-cm-task/SKILL.md"))
    assert "acceptance materially depends on a runtime observer/enforcer" in cm
    assert "current focused tests or preflight do not already prove" in cm
    assert "new or changed runtime observer" not in cm


def test_role_documents_do_not_import_other_role_methods_or_global_enums() -> None:
    role_names = set(ROLE_MARKERS) - set(TOP_LEVEL_SKILLS)
    top_level_fields = (
        "Outcome: DONE | WAITING | FAILED | CANCELLED",
        "Direction actions:",
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
    em = _read(".agents/skills/hmasd-em-task/SKILL.md")
    portfolio = _read(".agents/skills/hmasd-portfolio-task/SKILL.md")
    for marker in (
        "genuinely different approach families",
        "same scope without EM's favored answer",
        "reopen a blocked route only for a genuinely new mechanism",
        "unused evidence and unasked answer-changing questions",
        "send a meaning-complete WORK to CM before `SYNTHESIS_READY`",
        "Program, test, or command success is never scientific acceptance",
        "same-source agreement", "search coverage",
        "primary evidence", "direct CM observation", "concrete counterexample",
        "specific Pro objection", "Self-critique alone", "aggregate no-material-change",
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
