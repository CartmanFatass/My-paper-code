from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_clerk_instruction_has_direction_neutral_semantic_table_and_dispatch_barrier() -> None:
    text = (ROOT / ".codex/prompts/hmasd-workflow-clerk.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(text.split()).casefold()

    for required in (
        "## Topology snapshot",
        "## Direction-neutral semantic table",
        "REQUEST_EM",
        "REQUEST_CM",
        "REQUEST_PORTFOLIO",
        "REQUEST_USER",
        "FAILED",
        "dispatch all independent ready envelopes before ending the turn",
        "do not wait for ordinary RETURNs in the same turn",
        "never copy one direction's objective, evidence, failure, or lifecycle",
        "Codex task list/read for task topology and native message delivery",
        "Portfolio registry/authority for direction lifecycle",
        "native automation state for resource heartbeats",
        "Portfolio is a decision participant, not a coordinator",
        "immutable RETURN files are never rewritten",
        "full commit SHA, remote/ref, and push outcome",
    ):
        assert required.casefold() in normalized


def test_clerk_instruction_keeps_resource_retry_out_of_direction_routing() -> None:
    text = (ROOT / ".codex/prompts/hmasd-workflow-clerk.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(text.split()).casefold()

    assert "resource_memory_admission" in normalized
    assert "one active heartbeat per direction/run_id" in normalized
    assert "attached to the exact recipient task" in normalized
    assert "never root or workflow-clerk by default" in normalized
    assert "delete that heartbeat after prepared" in normalized
    assert "must not create an operator" in normalized
    assert "does not require user approval merely because" in normalized
    assert "estimated at no more than 7200 seconds" in normalized


def test_clerk_instruction_requires_one_live_owner_or_explicit_terminal_state() -> None:
    text = (ROOT / ".codex/prompts/hmasd-workflow-clerk.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(text.split()).casefold()

    for required in (
        "## direction liveness invariant",
        "owned work",
        "resource wait",
        "user pause",
        "terminal",
        "owner session",
        "next event",
        "idle without one of these facts is a workflow defect",
        "classification priority",
        "portfolio registry",
        "configured heartbeat",
        "closed",
        "parked",
    ):
        assert required in normalized


def test_clerk_does_not_route_direction_owned_preparation_to_root() -> None:
    text = (ROOT / ".codex/prompts/hmasd-workflow-clerk.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(text.split()).casefold()

    assert "direction-owned git candidate and manifest preparation belong to cm" in normalized
    assert "root is not the routine preparation owner" in normalized
    assert "shared-core" in normalized
    assert "cross-direction git integration" in normalized
    assert "protocol question" in normalized


def test_clerk_case_manual_routes_common_gaps_without_root_escalation() -> None:
    text = (ROOT / ".codex/prompts/hmasd-workflow-clerk.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(text.split()).casefold()

    assert "## responsibility case manual" in normalized
    for required in (
        "direction scientific meaning",
        "direction code, dependency, path, git, candidate, dossier, manifest, or prepare",
        "missing implementation or operator",
        "cross-direction priority, investment, or lifecycle",
        "pro external review",
        "agentify external transport",
        "resource admission",
        "authority-covered local command at or below 7200 seconds",
        "true user material choice",
        "shared-core",
        "unknown external commitment",
    ):
        assert required in normalized

    assert "do not notify root merely because" in normalized


def test_clerk_assignments_preserve_manager_leaf_interfaces() -> None:
    text = (ROOT / ".codex/prompts/hmasd-workflow-clerk.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(text.split()).casefold()

    assert "every em assignment references `.codex/prompts/hmasd-em.md`" in normalized
    assert "every cm assignment references `.codex/prompts/hmasd-cm.md`" in normalized
    assert "never blanket-ban subagents in an em or cm assignment" in normalized
    assert "may forbid a result-bearing command without forbidding" in normalized
    assert "implementer, reviewer, verifier, or research review leaves" in normalized
