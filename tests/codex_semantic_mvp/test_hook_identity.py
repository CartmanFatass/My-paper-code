from tools.codex_semantic_mvp.hook_identity import (
    HookIdentity,
    normalize_hook_identity,
    normalized_session_source,
)


def test_normalize_hook_identity_preserves_only_control_fields():
    payload = {
        "hook_event_name": "PreCompact",
        "session_id": "session-1",
        "turn_id": "turn-1",
        "agent_id": "agent-1",
        "agent_type": "HMASDIndependentResearchExplorer",
        "agent_path": "/root/em_risp",
        "parent_agent_id": "root-agent",
        "parent_agent_path": "/root",
        "source": "compact",
        "transcript_path": "C:/sensitive/transcript.jsonl",
        "last_assistant_message": "BLOCKED",
    }

    identity = normalize_hook_identity(payload)

    assert identity == HookIdentity(
        event="PreCompact",
        session_id="session-1",
        turn_id="turn-1",
        agent_id="agent-1",
        agent_type="HMASDIndependentResearchExplorer",
        canonical_path="/root/em_risp",
        parent_agent_id="root-agent",
        parent_canonical_path="/root",
        source="compact",
    )


def test_normalized_session_source_accepts_known_aliases():
    assert normalized_session_source({"source": "compact"}) == "compact"
    assert normalized_session_source({"session_source": "resume"}) == "resume"
    assert normalized_session_source({"source": "startup"}) == "startup"
    assert normalized_session_source({}) == "unknown"
