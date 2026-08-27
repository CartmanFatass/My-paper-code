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
        "Codex task list/read is the only topology fact source",
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
