from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = REPO_ROOT / ".omp" / "agents"
BROWSER_AGENT = AGENT_ROOT / "hmasd-browser-transport.md"
BROWSER_SKILL = (
    REPO_ROOT / ".omp" / "skills" / "hmasd-browser-transport" / "SKILL.md"
)
EXTERNAL_REVIEW_SKILL = (
    REPO_ROOT
    / ".omp"
    / "skills"
    / "hmasd-scientific-external-review"
    / "SKILL.md"
)
RESULT_SCHEMA = (
    REPO_ROOT / "scripts" / "schemas" / "hmasd_agent_result.schema.json"
)


def _frontmatter(path: Path) -> dict[str, str | list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    metadata: dict[str, str | list[str]] = {}
    index = 1
    while index < end:
        key, separator, scalar = lines[index].partition(":")
        assert separator, (path, lines[index])
        if scalar.strip():
            metadata[key] = [] if scalar.strip() == "[]" else scalar.strip()
            index += 1
            continue
        values: list[str] = []
        index += 1
        while index < end and lines[index].startswith("  - "):
            values.append(lines[index][4:])
            index += 1
        metadata[key] = values
    return metadata


def _list(metadata: dict[str, str | list[str]], key: str) -> list[str]:
    value = metadata[key]
    assert isinstance(value, list)
    return value


def test_singleton_agent_inventory_tools_and_manager_routing() -> None:
    assert BROWSER_AGENT.is_file()
    for retired in (
        "hmasd-external-pro-transport.md",
        "hmasd-external-gemini-transport.md",
    ):
        assert not (AGENT_ROOT / retired).exists()

    metadata = _frontmatter(BROWSER_AGENT)
    assert metadata["name"] == "hmasd-browser-transport"
    assert _list(metadata, "spawns") == []
    assert _list(metadata, "autoloadSkills") == ["hmasd-browser-transport"]
    tools = _list(metadata, "tools")
    assert "task" not in tools
    assert "mcp__agentify-desktop__agentify_review_query" in tools
    assert "mcp__agentify-desktop__agentify_review_observe" in tools
    assert "mcp__agentify-desktop__agentify_operator_observe" in tools
    assert "mcp__agentify-desktop__agentify_operator_act" in tools
    assert "mcp__agentify-desktop__agentify_query" not in tools
    assert (
        "mcp__agentify-desktop__agentify_review_prompt_sha256_preflight"
        not in tools
    )

    agent_text = BROWSER_AGENT.read_text(encoding="utf-8")
    assert "BrowserTransport logical identity" in agent_text
    assert "never routing or scientific authority" in agent_text

    for manager_name in ("hmasd-em", "hmasd-cm"):
        manager_path = AGENT_ROOT / f"{manager_name}.md"
        manager = _frontmatter(manager_path)
        spawns = _list(manager, "spawns")
        assert "hmasd-browser-transport" not in spawns
        assert "hmasd-external-pro-transport" not in spawns
        assert "hmasd-external-gemini-transport" not in spawns
        body = manager_path.read_text(encoding="utf-8")
        assert "`next_action.owner=TRANSPORT` through Root" in body
        assert "never spawn or contact\nBrowserTransport directly" in body


def test_service_keeps_objects_separate_and_closes_the_send_boundary() -> None:
    text = BROWSER_SKILL.read_text(encoding="utf-8")
    lower = text.lower()
    for object_name in (
        "**service**",
        "**assignment**",
        "**strict operation**",
        "**agentify operation**",
        "**provider conversation**",
        "**browser tab**",
        "**prompt file**",
        "**archive file**",
    ):
        assert object_name in lower

    assert "`observe -> interpret -> act -> verify`" in text
    assert "It sends at most once" in text
    assert "Unknown commitment\n   never resends" in text
    assert "`ZERO_SEND_FAILED` proves only" in text
    assert "it is not operation-two authority" in text
    assert (
        "`SENT_WAITING`, `COMMITMENT_UNKNOWN`, and `SENT_UNREADABLE` as\n"
        "   observe-only states"
    ) in text
    assert "Agentify strict `agentify_review_query`, once" in text
    assert "never substitute `agentify_query`" in text

    for state in (
        "PENDING",
        "ZERO_SEND_FAILED",
        "COMMITMENT_UNKNOWN",
        "SENT_WAITING",
        "COMPLETE",
        "SENT_INPUT_MISMATCH",
        "SENT_MODEL_MISMATCH",
        "SENT_UNREADABLE",
        "CONVERSATION_LOST",
        "WAIVED",
    ):
        assert f"`{state}`" in text


def test_prompt_and_archive_require_helper_fingerprint_and_archive_reread() -> None:
    text = BROWSER_SKILL.read_text(encoding="utf-8")
    command = "python scripts/hmasd_file_fingerprint.py --path"
    assert text.count(command) == 2
    assert "--require-utf8" in text
    assert "`path.absolute`" in text
    assert "`file.sha256`" in text
    assert "`file.size_bytes`" in text
    assert "`file.utf8.valid`" in text
    assert "Then reread the exact archive\n   file with `read`" in text
    assert "Return `COMPLETE` only when the helper reports success" in text
    assert "hashes and stable keys are never identity" in text
    assert "A tab\n   ID" in text and "is never conversation" in text


def test_external_review_preserves_root_mediation_and_provider_binding() -> None:
    text = EXTERNAL_REVIEW_SKILL.read_text(encoding="utf-8")
    assert "single Root-mediated\n`BrowserTransport` service" in text
    assert "`next_action.owner=TRANSPORT` through Root" in text
    assert "EM and CM never spawn or\ncontact BrowserTransport directly" in text
    assert "Pro must\n   bind `provider: chatgpt`" in text
    assert "Gemini must bind\n   `provider: gemini`" in text
    assert "Cross-provider substitution is\n   forbidden" in text
    assert "Agentify strict `agentify_review_query` as the send-capable surface" in text
    assert "`agentify_review_observe`" in text
    assert "`verifyExisting`" in text
    assert "Root alone invokes `hmasd_external_review.py`" in text
    assert "hmasd-external-pro-transport" not in text
    assert "hmasd-external-gemini-transport" not in text


def test_browser_result_is_common_v1_transport_envelope_to_root() -> None:
    text = BROWSER_SKILL.read_text(encoding="utf-8")
    match = re.search(r"```json\n(\{.*?\})\n```", text, re.DOTALL)
    assert match
    envelope = json.loads(match.group(1))
    assert envelope["schema_version"] == 1
    assert envelope["role"] == "hmasd-browser-transport"
    assert envelope["logical_identity"] == "BrowserTransport"
    assert envelope["materiality"] == "LOCAL"
    assert envelope["payload"] == {
        "kind": "transport",
        "browser_identity": "BrowserTransport",
        "transport_assignment": "<transport-assignment>",
        "requester": "EM-example-direction",
        "provider": "chatgpt",
        "mode": "INNOVATOR",
        "effect_ref": None,
        "transport_state": "COMPLETE",
        "provider_conversation_ref": "<provider-URL-and-ID>",
        "operation_ref": "<Agentify-operation-reference>",
        "archive_ref": "<verified-archive-path>",
        "handoff_ref": None,
    }
    assert "Return to Root, and only Root" in text
    assert "Do not return scientific,\nengineering, Portfolio" in text


def test_common_schema_admits_the_singleton_transport_contract() -> None:
    schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    transport = schema["$defs"]["transport_payload"]
    assert transport["additionalProperties"] is False
    assert set(transport["required"]) == {
        "kind",
        "browser_identity",
        "transport_assignment",
        "requester",
        "provider",
        "mode",
        "effect_ref",
        "transport_state",
        "provider_conversation_ref",
        "operation_ref",
        "archive_ref",
        "handoff_ref",
    }
    properties = transport["properties"]
    assert properties["browser_identity"]["const"] == "BrowserTransport"
    assert properties["kind"]["const"] == "transport"
    assert set(properties["provider"]["enum"]) == {"chatgpt", "gemini"}
    assert set(properties["mode"]["enum"]) == {
        "INNOVATOR",
        "CONVERGENCE",
        "DIVERGENT",
        "ENGINEERING",
        "MONITOR",
    }
    assert set(properties["transport_state"]["enum"]) == {
        "PENDING",
        "ZERO_SEND_FAILED",
        "COMMITMENT_UNKNOWN",
        "SENT_WAITING",
        "COMPLETE",
        "SENT_INPUT_MISMATCH",
        "SENT_MODEL_MISMATCH",
        "SENT_UNREADABLE",
        "CONVERSATION_LOST",
        "WAIVED",
    }
