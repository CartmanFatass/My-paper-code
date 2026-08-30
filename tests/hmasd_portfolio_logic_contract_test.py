from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-root-control" / "SKILL.md"
PROTOCOL = REPO_ROOT / "docs" / "project" / "HMASD_OMP_CONTROL_PLANE_PROTOCOL.md"
AGENTS = REPO_ROOT / ".omp" / "AGENTS.md"
WATCHDOG = REPO_ROOT / ".omp" / "WATCHDOG.md"
RULES = REPO_ROOT / ".omp" / "RULES.md"
DECISION = (
    REPO_ROOT
    / "docs"
    / "research"
    / "portfolio"
    / "decisions"
    / "2026-08-29-user-authorized-four-direction-expansion.md"
)


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
        "common v2 result envelope",
        ".omp/runtime/agents.json",
        ".omp/runtime/worktrees.json",
        "`omp/workflow`",
        "`hmasd-workflow-recovery-manager`",
    ):
        assert required in protocol

    for root_projection_anchor in (
        "R1_SINGLE_CONTROLLER",
        "R2_FINITE_EVENT_SNAPSHOT",
        "R3_EXACTLY_ONCE_CONSUMPTION",
        "R4_UNIQUE_NODE",
        "R5_EXACT_EDGE",
        "R6_ACCEPTANCE_BEFORE_RELEASE",
        "R7_CAPACITY_SEPARATION",
        "R8_MAXIMAL_DISPATCH",
        "R9_PAUSE",
        "R10_LOCKS_NOT_AUTHORITY",
        "R11_NO_POLL_LOOP",
        "R12_CHECKPOINT_PROOF",
        "`NodeKey` is",
        "next_actions",
        "has no `next_action` compatibility alias",
    ):
        assert root_projection_anchor in protocol

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

    assert "freeze the complete desired registry bytes" in skill
    assert "wait for the exact accepted registry receipt and Root-owned integrated SHA" in skill
    assert "only Clerk performs the CAS and Git mechanics" in skill
    assert "Checkpoint only material milestones:" in skill
    for material_milestone in (
        "completed research or engineering rounds",
        "accepted-result or terminal-run evidence promotion",
        "external prompt/archive readiness",
        "Portfolio lifecycle changes",
        "current-schema cutovers",
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
        "It rides in the role payload of the common v2 carrier with required `next_actions`",
        "`NO_MATERIAL_INSIGHT` is a successful terminal, negative-complete product",
        "This is task routing through existing OMP carriers, not a scheduler, registry, lifecycle, or authority layer",
    ):
        assert skill_anchor in skill


def test_root_projection_is_event_driven_maximal_and_strictly_wait_gated() -> None:
    skill = _flat(ROOT_SKILL)

    for invariant in (
        "R1_SINGLE_CONTROLLER",
        "R2_FINITE_EVENT_SNAPSHOT",
        "R3_EXACTLY_ONCE_CONSUMPTION",
        "R4_UNIQUE_NODE",
        "R5_EXACT_EDGE",
        "R6_ACCEPTANCE_BEFORE_RELEASE",
        "R7_CAPACITY_SEPARATION",
        "R8_MAXIMAL_DISPATCH",
        "R9_PAUSE",
        "R10_LOCKS_NOT_AUTHORITY",
        "R11_NO_POLL_LOOP",
        "R12_CHECKPOINT_PROOF",
    ):
        assert invariant in skill

    for event_anchor in (
        "snapshot all currently queued deliveries with a finite cutoff",
        "Delivery identity and result identity are separate",
        "Job settlement is never result acceptance",
        "exactly one causal consumption for every accepted or refused terminal result across resume/compaction",
        "`NodeKey` is `(logical_identity, generation, assignment_id)`",
        "dispatch the maximal admissible independent set in the same wake",
        "A slow child cannot block an independent node or successor",
        "reconcile every per-item receipt",
        "Never retry the whole batch",
        "separate R7 resource classes",
        "one canonical `omp/workflow` target mutator",
    ):
        assert event_anchor in skill

    for checkpoint_anchor in (
        "Portfolio authorized/live/free capacity",
        "OMP running/queued limits",
        "queued delivery IDs",
        "unconsumed and consumed result keys/digests",
        "runnable and inflight `NodeKey`s",
        "exact blocked dependency/resource edges",
        "current target-mutating operation ID/lock key",
        "Run, Transport, worktree, and external refs",
        "`NOT_CONFIGURED` is valid and non-gating",
    ):
        assert checkpoint_anchor in skill

    for wait_anchor in (
        "queued_deliveries = empty AND delivered_unconsumed_results = empty",
        "runnable_after_admission = empty AND unfinished_screening = empty",
        "unrouted_consequences = empty",
        "An invalid or unconsumed result",
        "runnable non-scientific operation",
        "makes wait illegal",
        "Use broad coordination wait",
        "whose holder is observed live/committed",
        "never wait for the first child or an all-terminal barrier",
        "a timeout is not a new wake",
    ):
        assert wait_anchor in skill


def test_pause_validates_deliveries_but_creates_no_new_work() -> None:
    skill = _flat(ROOT_SKILL)

    for pause_anchor in (
        "`PAUSE` blocks every new Effect and task, including Clerk, CAS, Git, provider send, result run, refill, and manager revival",
        "Root may validate delivered facts",
        "observe only already-committed Effects through their existing exact owner",
        "return `PAUSED/IDLE` rather than wait",
        "never create a replacement observer or enter Hub wait",
    ):
        assert pause_anchor in skill


def test_historical_four_result_join_is_explicitly_nonoperative() -> None:
    decision = _flat(DECISION)

    assert "Portfolio joins all four terminal results before its next lifecycle audit" in decision
    assert "preserved as historical wording but is **nonoperative**" in decision
    assert "creates no four-result join, all-terminal barrier, wait reason, or successor edge" in decision
    assert "A slow direction never blocks independent Transport, Portfolio, Clerk" in decision


def test_root_preserves_role_fact_and_lifecycle_boundaries() -> None:
    skill = _flat(ROOT_SKILL)

    for fact_anchor in (
        "EM supplies scientific status, bounded claim, decision impact, evidence",
        "CM supplies independent engineering, observation, and verification status",
        "BrowserTransport supplies provider, conversation, operation, archive, commitment, and transport facts",
        "Experiment Operator supplies observed process, manifest, measurement, and terminal facts",
        "OMP liveness, runtime, worktree, conflict, commit, and push observations are routing or Git facts",
        "Engineering, transport, Run, runtime, Clerk, and Git facts never imply science or lifecycle",
        "Treat transport availability only as evidence availability",
    ):
        assert fact_anchor in skill

    assert "drain the finite delivery snapshot, validate every result" in skill
    assert "Retain every nonterminal leg and route each terminal consequence" in skill


def test_root_mediates_the_single_browser_transport_route() -> None:
    skill = _flat(ROOT_SKILL)
    agents = _flat(AGENTS)
    rules = _flat(RULES)

    for shared_anchor in (
        "`BrowserTransport` is the singleton logical service",
        "implemented by agent type `hmasd-browser-transport`",
        "emit a `next_actions` item with `owner: TRANSPORT`",
        "strict dependencies",
    ):
        assert shared_anchor in agents

    for root_anchor in (
        "BrowserTransport is one Root-mediated logical service",
        "Root validates requester, direction/stage, provider, mode, immutable operation/idempotency/fingerprint",
        "prompt path/hash, raw response path, and the separate `product_model` and `reasoning_effort` axes",
        "serializes the exact operation through `hmasd-browser-transport`",
        "fingerprints and rereads raw `response.md`",
        "separately validates immutable current `operation_ref.json`",
        "returns the common v2 transport fact to the same requester",
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

def test_common_actions_and_clerk_authority_are_closed_and_explicit() -> None:
    agents = _flat(AGENTS)
    skill = _flat(ROOT_SKILL)

    for action_anchor in (
        "requires `next_actions` as an array",
        "has no singular `next_action` alias",
        "`action_id`, `kind`, `owner` (including `CLERK`), `input_refs`, strict `dependencies`, `authorized_effect_ref`, and `stop_or_reentry_ref`",
        "Independent simultaneous obligations are separate items",
        "array order creates no dependency",
    ):
        assert action_anchor in agents

    for clerk_anchor in (
        "Packet presence is inert",
        "fresh nonblocking `hmasd-clerk` task",
        "without reconstructing, completing, choosing, or rewriting any packet field",
        "A raw watcher, daemon, auto-executing inbox, or global parked Clerk is forbidden",
        "Clerk returns observed mechanical facts only to Root",
        "preserves accepted manager semantics",
    ):
        assert clerk_anchor in skill



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
