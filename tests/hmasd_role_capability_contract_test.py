from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


ROLE_MARKERS = {
    "ROOT.md": (
        "original observable outcome", "protected invariants", "safe reproduction",
        "discriminating hypothesis", "end-to-end acceptance", "existing obligation",
        "authority classification", "conflicting propositions", "same unfinished WORK",
        "unconsumed result", "no authority to design", "workflow-control-plane",
        "hmasd-workflow-designer", "hmasd-design-reviewer", "exact approved design",
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
    "BROWSER_TRANSPORT.md": (
        "one long-lived Luna/xhigh Browser Transport task", "multiple EM or CM owners",
        "observe → interpret → act → verify", "ordinary page problems", "causal assistant turn",
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
    "WORKFLOW_DESIGNER.md": (
        "one future HMASD workflow", "exact scope", "protected invariants",
        "real-page usability", "INCOMPLETE",
    ),
    "DESIGN_REVIEWER.md": (
        "one frozen workflow", "independent", "named existing end-to-end witness",
        "must never send", "composer-adjacent Pro", "review_model_mismatch",
        "zero-send", "APPROVED", "REJECTED", "UNDERSPECIFIED", "rereview",
    ),
}


TOP_LEVEL_SKILLS = {
    "ROOT.md": "hmasd-root-task",
    "PORTFOLIO.md": "hmasd-portfolio-task",
    "EM.md": "hmasd-em-task",
    "CM.md": "hmasd-cm-task",
    "BROWSER_TRANSPORT.md": "hmasd-browser-conversation",
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


def test_browser_conversation_skill_owns_semantic_browser_use_not_owner_judgment() -> None:
    skill = _flat(_read(".agents/skills/hmasd-browser-conversation/SKILL.md"))
    agents = _read("AGENTS.md")
    for marker in (
        "Agentify strict review", "exact frozen prompt path", "exact response path",
        "full response is written", "provider-visible user turn",
        "exclusive writer ownership", "causal assistant turn",
        "browser tab is a replaceable local view", "New conversation action",
        "screenshots and the installed", "ordinary page-local recovery",
    ):
        assert marker in skill
    assert "ordinary query as a substitute" in skill
    assert "Never compose" in skill
    assert "tool-local" in skill
    assert "task identity" in skill
    for leaked_owner_term in (
        "Portfolio action:", "Scientific status:", "Engineering status:",
        "Recommendation:", "Capacity action:",
    ):
        assert leaked_owner_term not in skill
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


def test_zero_send_recovery_is_causal_and_owner_budgeted() -> None:
    agents = _flat(_read("AGENTS.md"))
    em = _flat(_read(".agents/skills/hmasd-em-task/SKILL.md"))
    transport = _flat(_read(".agents/skills/hmasd-browser-conversation/SKILL.md"))
    assert "permits ordinary page-local non-sending repair" in agents
    assert "shared zero-send rule never expands an owner-frozen operation budget" in agents
    assert "The same failure without a new fact always stops" in agents
    assert "later exact owner message after repair" in agents
    assert "actual page and current conversation stage" in transport
    assert "tool predicate is evidence about one automation path" in transport
    assert "ordinary page-local recovery" in transport
    assert "not escalation to the owner" in transport
    assert "failed clear call is not proof that content remains" in transport
    assert "rendered composer fact decides the next step" in transport
    assert "elapsed time alone" in transport
    assert "Do not loop an unchanged failure" in transport
    assert "Treat the exact inbound `Acceptance` as the complete operation budget" in transport
    assert "exact inbound `[BROWSER WORK] Acceptance` still has unused operation authority" in em
    assert "later exact owner message for the same assignment locator" in em
    assert "does not perform or micromanage browser actions" in em
    assert "parent supplies a concrete evidence-changing non-sending repair" not in transport
    assert "permits one bounded repair" not in agents


def test_transport_separates_model_identity_from_optional_reasoning_controls() -> None:
    transport = _flat(_read(".agents/skills/hmasd-browser-conversation/SKILL.md"))
    assert "separate reasoning control matters only when the owner explicitly froze it" in transport
    assert "owner terms `GPT-5.6 Pro` and `GPT-5.6 Sol Pro`" in transport
    assert "account-plan/profile label" in transport
    assert "Exact existing prompt content may be retained and sent in place" in transport


def test_portfolio_is_an_active_allocator_and_refills_terminal_legs() -> None:
    portfolio = _flat(_read(".agents/skills/hmasd-portfolio-task/SKILL.md")).lower()
    protocol = _flat(_read("docs/project/WORKFLOW_PROTOCOL.md")).lower()

    for marker in (
        "active allocator, not a passive join waiter",
        "consume each terminal em result immediately",
        "recommendation is evidence, not the action",
        "one terminal leg releases its advancing slot",
        "update portfolio authority before dispatch",
        "recompute the live advancing count",
        "screen the strongest authorized candidates",
        "all authorized slots already have live work",
        "no admissible candidate remains after comparison",
    ):
        assert marker in portfolio
    assert "return barrier, not a refill barrier" in protocol
    assert "其他 join legs 仍 nonterminal" in protocol


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


def test_workflow_design_and_review_are_pure_local_slices() -> None:
    agents = _flat(_read("AGENTS.md"))
    root = _flat(_read(".agents/skills/hmasd-root-task/SKILL.md"))
    designer = _flat(_read(".agents/roles/WORKFLOW_DESIGNER.md"))
    design_reviewer = _flat(_read(".agents/roles/DESIGN_REVIEWER.md"))
    reviewer = _flat(_read(".agents/roles/REVIEWER.md"))

    assert "Root has no authority to design workflow" in agents
    assert "Root must not author the design" in root
    assert "APPROVED_WITH_AMENDMENTS" not in f"{agents} {root} {design_reviewer}"
    assert "one minimal meaning-complete design" in designer
    assert "must never send a provider request" in design_reviewer
    sequence = (
        "observe → recognize unique visible actionable composer-adjacent Pro while excluding profile Pro "
        "→ stage exact owner prompt → send once → wait natural completion → archive full reply "
        "→ close/reopen by conversation ID"
    )
    assert sequence in design_reviewer
    assert "Schema, unit tests, or same-source narrative cannot substitute" in design_reviewer
    assert "workflow, control-plane, protocol, role, or skill topology design" in reviewer.lower()
