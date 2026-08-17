from pathlib import Path

from tools.codex_semantic_mvp.hook_identity import normalize_hook_identity
from tools.codex_semantic_mvp.topology_probe import (
    append_probe_record,
    load_probe_records,
    probe_record,
    summarize_probe,
)


def _payload(**extra: object) -> dict[str, object]:
    value: dict[str, object] = {
        "hook_event_name": "PreCompact",
        "session_id": "session-1",
        "turn_id": "turn-1",
        "source": "compact",
        "transcript_path": "C:/sensitive/transcript.jsonl",
        "last_assistant_message": "BLOCKED",
        "tool_input": {"secret": "do-not-record"},
    }
    value.update(extra)
    return value


def test_probe_record_excludes_transcript_and_prose(tmp_path: Path) -> None:
    path = tmp_path / "topology-probe.jsonl"
    payload = _payload()
    append_probe_record(path, normalize_hook_identity(payload), payload)
    raw = path.read_text(encoding="utf-8")
    assert "transcript.jsonl" not in raw
    assert "BLOCKED" not in raw
    assert "do-not-record" not in raw
    assert "secret" not in raw
    record = load_probe_records(path)[0]
    assert set(record) == {
        "timestamp",
        "event",
        "source",
        "session_id",
        "turn_id",
        "agent_id",
        "agent_type",
        "canonical_path",
        "parent_agent_id",
        "parent_canonical_path",
        "payload_key_names",
    }
    assert "transcript_path" in record["payload_key_names"]
    assert "last_assistant_message" in record["payload_key_names"]
    built = probe_record(normalize_hook_identity(payload), payload, timestamp="t0")
    assert "transcript_path" not in built
    assert built["event"] == "PreCompact"


def test_capability_summary_distinguishes_session_root_and_subagent_identity() -> None:
    records = [
        {
            "event": "PreCompact",
            "source": "compact",
            "session_id": "session-1",
            "turn_id": "turn-1",
            "agent_id": "",
            "canonical_path": "",
            "parent_agent_id": "",
        },
        {
            "event": "PostCompact",
            "source": "compact",
            "session_id": "session-1",
            "turn_id": "turn-2",
            "agent_id": "",
            "canonical_path": "",
            "parent_agent_id": "",
        },
        {
            "event": "SubagentStart",
            "source": "unknown",
            "session_id": "session-1",
            "turn_id": "turn-3",
            "agent_id": "em-1",
            "canonical_path": "",
            "parent_agent_id": "root-1",
        },
        {
            "event": "SubagentStart",
            "source": "unknown",
            "session_id": "session-1",
            "turn_id": "turn-4",
            "agent_id": "cm-1",
            "canonical_path": "",
            "parent_agent_id": "root-1",
        },
        {
            "event": "SubagentStop",
            "source": "unknown",
            "session_id": "session-1",
            "turn_id": "turn-5",
            "agent_id": "em-1",
            "canonical_path": "",
            "parent_agent_id": "root-1",
        },
        {
            "event": "SubagentStop",
            "source": "unknown",
            "session_id": "session-1",
            "turn_id": "turn-6",
            "agent_id": "cm-1",
            "canonical_path": "",
            "parent_agent_id": "root-1",
        },
    ]
    summary = summarize_probe(records)
    assert summary["session_root_compaction_identity"] is True
    assert summary["subagent_start_identity"] is True
    assert summary["subagent_stop_identity"] is True
    assert summary["subagent_compaction_identity"] is False
    assert summary["automatic_root_rehydration"] is True
    assert summary["automatic_portfolio_rehydration"] is True
    assert summary["automatic_l1_rehydration"] is False
    assert summary["automatic_leaf_rehydration"] is False
    assert summary["narrow_pretool_matcher_verified"] is False


def test_capability_summary_never_claims_l1_rehydration_without_agent_identity() -> None:
    records = [
        {
            "event": "PreCompact",
            "source": "compact",
            "session_id": "session-1",
            "turn_id": "turn-1",
            "agent_id": "",
            "canonical_path": "/root/em_risp",
            "parent_agent_id": "",
        },
        {
            "event": "PostCompact",
            "source": "compact",
            "session_id": "session-1",
            "turn_id": "turn-2",
            "agent_id": "",
            "canonical_path": "/root/em_risp",
            "parent_agent_id": "",
        },
    ]
    summary = summarize_probe(records)
    assert summary["session_root_compaction_identity"] is True
    assert summary["subagent_compaction_identity"] is False
    assert summary["automatic_l1_rehydration"] is False
    assert summary["automatic_leaf_rehydration"] is False


def test_single_ambiguous_row_does_not_enable_any_capability() -> None:
    summary = summarize_probe(
        [
            {
                "event": "PreCompact",
                "source": "compact",
                "session_id": "session-1",
                "turn_id": "turn-1",
                "agent_id": "maybe-agent",
                "canonical_path": "/maybe",
                "parent_agent_id": "maybe-parent",
            }
        ]
    )
    assert summary["session_root_compaction_identity"] is False
    assert summary["subagent_compaction_identity"] is False
    assert summary["canonical_path_available"] is False
    assert summary["automatic_l1_rehydration"] is False
    assert summary["narrow_pretool_matcher_verified"] is False
