from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_SKILL = REPO_ROOT / ".omp" / "skills" / "hmasd-root-control" / "SKILL.md"
PROTOCOL = REPO_ROOT / "docs" / "project" / "HMASD_OMP_CONTROL_PLANE_PROTOCOL.md"
AGENTS = REPO_ROOT / ".omp" / "AGENTS.md"
WATCHDOG = REPO_ROOT / ".omp" / "WATCHDOG.md"


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

    for required in (
        "There is no Portfolio agent",
        "Fixed user considered set",
        "Live investments and Effects",
        "Evidence boundary",
        "Counterfactual allocation",
        "Next observation",
        "An EM recommendation is evidence, not a Portfolio action",
    ):
        assert required in skill

    actions = (
        "`NONE`",
        "`ACTIVATE`",
        "`CONTINUE`",
        "`NARROW`",
        "`PARK`",
        "`CLOSE`",
        "`FUSE`",
        "`SPINOFF`",
    )
    action_sentence = skill[skill.index("adopt exactly one action") :]
    for action in actions:
        assert action in action_sentence

    assert "Registry lifecycle is exactly `REGISTERED`, `ACTIVE`, `PARKED`, or `CLOSED`" in _flat(AGENTS)
    assert "`PARKED` is not `CLOSED`" in skill
    assert "`reactivation_condition_ref`" in skill
    assert (
        '"capacity_action": { "action": "NONE", "direction_id": null, '
        '"decision_ref": null }'
    ) in skill


def test_root_actively_refills_unpaused_capacity_and_pause_blocks_effects() -> None:
    skill = _flat(ROOT_SKILL)

    assert "Portfolio is an active allocator, not a passive all-terminal join" in skill
    assert "recompute the number of live advancing direction investments" in skill
    assert "When control is not `PAUSED` and advancing work is below authorized capacity" in skill
    assert "dispatch the best admissible successor or replacement to an exact idle EM in the same wake" in skill
    assert "do not wait for another Root prompt or for all other legs to finish" in skill
    assert "blocks active refill, new direction dispatch, fresh BrowserTransport sends, experiment launches, and all other new Effects" in skill
    assert "Root does not refill paused capacity" in skill


def test_root_preserves_role_fact_and_lifecycle_boundaries() -> None:
    skill = _flat(ROOT_SKILL)

    for required in (
        "Engineering success or failure is not science or lifecycle",
        "Transport success, failure, mismatch, loss, or waiver is not science or lifecycle",
        "Launch, process, manifest, measurement, and terminal facts are not scientific interpretation or lifecycle",
        "worktree state, commit, conflict, and push state are routing or Git facts",
        "Transport, engineering, Run, runtime, and Git facts never become lifecycle or science by inference",
    ):
        assert required in skill

    assert "Consume each terminal fact immediately" in skill
    for terminal_owner in ("An EM result", "A CM result", "A BrowserTransport result", "A Run result"):
        assert terminal_owner in skill


def test_root_mediates_the_single_browser_transport_route() -> None:
    skill = _flat(ROOT_SKILL)
    agents = _flat(AGENTS)

    for text in (skill, agents):
        assert "`BrowserTransport`" in text
        assert "`hmasd-browser-transport`" in text
        assert "next_action.owner=TRANSPORT" in text
        assert "hmasd-external-pro-transport" not in text
        assert "hmasd-external-gemini-transport" not in text

    assert "Root then serializes the request through the singleton" in skill
    assert "`COMMITMENT_UNKNOWN` never resends" in skill
    assert "EM and CM do not spawn one another" in skill


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
