from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-root-control" / "SKILL.md"
PROTOCOL = REPO_ROOT / "docs" / "project" / "HMASD_OMP_CONTROL_PLANE_PROTOCOL.md"
AGENTS = REPO_ROOT / ".omp" / "AGENTS.md"
WATCHDOG = REPO_ROOT / ".omp" / "WATCHDOG.md"
RULES = REPO_ROOT / ".omp" / "RULES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    return " ".join(_read(path).split())


def test_human_protocol_covers_the_layered_omp_control_plane() -> None:
    protocol = _flat(PROTOCOL)

    for required in (
        "Root executes the Portfolio subflow itself",
        "there is no Portfolio agent",
        "Portfolio allocation is active",
        "`REGISTERED`",
        "`ACTIVE`",
        "`PARKED`",
        "`CLOSED`",
        "`FRESH_MATERIAL_CYCLE`",
        "`CONTINUATION`",
        "`CM_RESULT_INTERPRETATION`",
        "`EVIDENCE_INTAKE`",
        "`TERMINAL_GAP_DISPOSITION`",
        "CM is contract-first",
        "Root-mediated logical service",
        "agent type `hmasd-browser-transport`",
        "common v1 result envelope",
        ".omp/runtime/agents.json",
        ".omp/runtime/worktrees.json",
        "`omp/workflow`",
        "`hmasd-workflow-recovery-manager`",
    ):
        assert required in protocol

    for path_fragment in (
        "`<cycle-id>-scope-freeze.md`",
        "`<cycle-id>-local-route-<route-id>.md`",
        "`<cycle-id>-synthesis.md`",
        "`<cycle-id>-terminal-gap.md`",
        "`<cycle-id>-handoff.md`",
        "`<cycle-id>-innovator-prompt.md`",
        "`<cycle-id>-convergence-prompt.md`",
        "`<cycle-id>-convergence-disposition.md`",
        "`workflow/research/engineering-request.md`",
        "`<cycle-id>-contract.md`",
        "`<cycle-id>-implementation.md`",
        "`<cycle-id>-review.md`",
        "`<cycle-id>-verification.md`",
        "`<cycle-id>-result.md`",
    ):
        assert path_fragment in protocol

    for meaning_section in (
        "Objective and decision relevance",
        "Authorities, inputs, and evidence boundary",
        "Scope, protected non-goals, and preserved semantics",
        "Requested role work and role-owned judgment",
        "Authorized Effects and ownership",
        "Acceptance evidence and stop condition",
        "Return route, durable references, and reentry",
    ):
        assert meaning_section in protocol


def test_root_executes_the_complete_portfolio_decision_frame() -> None:
    skill = _flat(ROOT_SKILL)
    agents = _flat(AGENTS)

    for role_anchor in (
        "Root is the one user-facing controller",
        "`Portfolio` is a durable authority name, not an agent",
        "### 2. State the Portfolio decision frame",
    ):
        assert role_anchor in skill

    for frame_anchor in (
        "**User decision and fixed set:**",
        "allocation question",
        "every considered direction",
        "authorized capacity",
        "**Live investments:**",
        "unfinished joins",
        "committed Effects",
        "**Evidence boundary:**",
        "valid comparative science",
        "excluded transport/engineering/measurement facts",
        "supported claim ceiling",
        "**Counterfactual allocation:**",
        "strongest real alternative",
        "decision leverage",
        "reversibility",
        "stop rule",
        "**Next observation:**",
        "smallest discriminator that could change allocation",
        "action each outcome would change",
    ):
        assert frame_anchor in skill

    assert "EM supplies scientific status, bounded claim, decision impact, evidence" in skill
    assert "Root makes the comparative Portfolio action" in skill

    for action in (
        "`NONE`",
        "`ACTIVATE`",
        "`CONTINUE`",
        "`NARROW`",
        "`PARK`",
        "`CLOSE`",
        "`FUSE`",
        "`SPINOFF`",
    ):
        assert action in skill

    assert (
        "Registry lifecycle is exactly `REGISTERED`, `ACTIVE`, `PARKED`, or `CLOSED`"
        in agents
    )
    assert "`PARKED` is not `CLOSED`" in skill
    assert "`reactivation_condition_ref`" in skill
    assert (
        '`kind: "portfolio"` with one structured action for every fixed-set direction'
        in skill
    )
    assert "the capacity action" in skill
    assert "exact `PORTFOLIO.md` reference, and registry revision" in skill

    assert (
        "establish the exact Root-owned `omp/workflow` checkpoint before any dispatch "
        "that depends on the decision"
    ) in skill
    assert "Checkpoint only material milestones:" in skill
    for material_milestone in (
        "completed research or engineering rounds",
        "accepted-result or terminal-run evidence promotion",
        "external prompt/archive readiness",
        "Portfolio lifecycle changes",
        "schema migrations",
    ):
        assert material_milestone in skill


def test_root_routes_direction_science_through_em_and_bounds_portfolio_leaves() -> None:
    skill = _flat(ROOT_SKILL)
    agents = _flat(AGENTS)
    protocol = _flat(PROTOCOL)

    for text in (skill, protocol):
        assert "direction-scoped" in text
        assert "EM" in text
        assert "never" in text
        assert "direct" in text
        for category in (
            "Shared-assumption audit",
            "Complement/substitute analysis",
            "Option-value analysis",
            "Cross-direction risk analysis",
        ):
            assert category in text

    for routing_anchor in (
        "Direction-scoped science always goes to the responsible EM",
        "Root never bypasses that EM by invoking a scientific leaf",
        "Counts follow gaps, never a fixed leaf quota, wave size, utilization target, vote, majority, or quorum",
        "First-wave packets contain no favored answer, desired `PASS`, sibling conclusion, vote tally, allocation preference, or other result leakage",
        "each remains blind to sibling results until it returns a substantive product or `NO_MATERIAL_INSIGHT`",
        "These rules add no scheduler, authority role, lifecycle state, result schema, or registry",
    ):
        assert routing_anchor in agents

    for skill_anchor in (
        "These are the only Portfolio analytical leaf categories",
        "Root synthesizes cited mechanisms and dependencies, never votes, majorities, confidence tallies, leaf counts, or quorum",
        "It rides in the existing role payload of the unchanged common v1 carrier",
        "`NO_MATERIAL_INSIGHT` is a successful terminal, negative-complete product",
        "This is task routing through existing OMP carriers, not a scheduler, registry, lifecycle, or authority layer",
    ):
        assert skill_anchor in skill


def test_root_actively_refills_unpaused_capacity_and_pause_blocks_effects() -> None:
    skill = _flat(ROOT_SKILL)

    for allocation_anchor in (
        "Portfolio is an active allocator, not an all-terminal join",
        "One terminal advancing leg releases its capacity slot",
        "When not `PAUSED`, recompute live advancing investments after each material fact",
        "If below authorized capacity",
        "screen the strongest authorized fixed-set candidates",
        "dispatch the best admissible successor or replacement to an exact idle EM in the same wake",
        "Do not wait for another Root prompt",
        "Wait only when all authorized slots have live advancing work or no admissible candidate survives comparison",
    ):
        assert allocation_anchor in skill

    for pause_anchor in (
        "`PAUSE` retains assignments",
        "non-sending observation needed to bring already-committed Effects to safe facts",
        "blocks refill, new direction work, fresh transport sends, experiment launches, and every other new Effect",
        "Root never refills paused capacity",
    ):
        assert pause_anchor in skill


def test_root_preserves_role_fact_and_lifecycle_boundaries() -> None:
    skill = _flat(ROOT_SKILL)

    for fact_anchor in (
        "EM supplies scientific status, bounded claim, decision impact, evidence",
        "CM supplies independent engineering, observation, and verification status",
        "BrowserTransport supplies provider, conversation, operation, archive, commitment, and transport facts",
        "Experiment Operator supplies observed process, manifest, measurement, and terminal facts",
        "OMP liveness, runtime, worktree, conflict, commit, and push observations are routing or Git facts",
        "Engineering, transport, Run, runtime, and Git facts never imply science or lifecycle",
        "Treat transport availability only as evidence availability",
    ):
        assert fact_anchor in skill

    assert "Consume each terminal EM, CM, Transport, or Run fact immediately" in skill
    assert "Retain every nonterminal leg and route each terminal consequence" in skill


def test_root_mediates_the_single_browser_transport_route() -> None:
    skill = _flat(ROOT_SKILL)
    agents = _flat(AGENTS)
    rules = _flat(RULES)

    for shared_anchor in (
        "`BrowserTransport` is the singleton logical service",
        "implemented by agent type `hmasd-browser-transport`",
        "return `next_action.owner=TRANSPORT` to Root",
    ):
        assert shared_anchor in agents

    for root_anchor in (
        "BrowserTransport is one Root-mediated logical service",
        "Root validates requester, direction/stage, provider, mode, operation identity",
        "prompt path/hash, response path, model requirement, authorization, and commitment state",
        "serializes the operation through `hmasd-browser-transport`",
        "validates the exact returned archive bytes",
        "returns the common v1 transport fact to the same requester",
        "BrowserTransport transports only",
        "does not interpret content, adopt lifecycle, write owner state, or choose follow-up",
        "EM and CM never spawn or contact one another directly",
    ):
        assert root_anchor in skill

    assert "unknown commitment never resends" in rules
    for retired_role in (
        "hmasd-external-pro-transport",
        "hmasd-external-gemini-transport",
    ):
        assert retired_role not in skill
        assert retired_role not in agents


def test_agents_and_watchdog_publish_only_the_omp_native_topology() -> None:
    agents = _flat(AGENTS)
    watchdog = _flat(WATCHDOG)

    assert "There is no Portfolio agent" in agents
    assert "There are no workflow-designer or design-reviewer project roles" in agents
    assert "hmasd-workflow-designer" not in agents
    assert "hmasd-design-reviewer" not in agents
    assert "Every cross-role dispatch uses an OMP `task` or Hub carrier" in agents
    assert "They are not OMP routing authority" in agents
    assert "Root-mediated BrowserTransport serialization" in agents
    assert "routing and runtime reconciliation" in agents
    assert "external archive validation" in agents
    assert "shared Git integration" in agents

    assert "only `hmasd-implementer` and `hmasd-implementer-terra` retain an engineering Advisor" in watchdog
    assert "BrowserTransport (`hmasd-browser-transport`)" in watchdog
    assert "BrowserTransport (`hmasd-browser-transport`), Reviewer" in watchdog
    assert "all other roles -> no Advisor" in watchdog
