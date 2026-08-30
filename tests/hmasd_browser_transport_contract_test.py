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


def _assert_semantics(text: str, fragments: tuple[str, ...]) -> None:
    normalized = " ".join(text.split())
    for fragment in fragments:
        assert " ".join(fragment.split()) in normalized, fragment


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
        _assert_semantics(
            body,
            (
                "`next_action.owner=TRANSPORT` through Root",
                "never spawn or contact BrowserTransport directly",
            ),
        )


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

    _assert_semantics(
        text,
        (
            "`observe -> interpret -> act -> verify`",
            "It sends at most once",
            "Unknown commitment never resends",
            "`ZERO_SEND_FAILED` proves only that this Agentify operation did not send",
            "it is not operation-two authority",
            "`SENT_WAITING`, `COMMITMENT_UNKNOWN`, and `SENT_UNREADABLE` as "
            "observe-only states",
            "Agentify strict `agentify_review_query`, once",
            "never substitute `agentify_query`",
        ),
    )

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
    _assert_semantics(
        text,
        (
            "--require-utf8",
            "`path.absolute`",
            "`file.sha256`",
            "`file.size_bytes`",
            "`file.utf8.valid`",
            "Then reread the exact archive file with `read`",
            "Return `COMPLETE` only when the helper reports success",
            "hashes and stable keys are never identity",
            "A tab ID, current page, or open-tab count is never conversation",
        ),
    )


def test_external_review_delegates_transport_mechanics_to_root_and_browser_skill() -> None:
    review = EXTERNAL_REVIEW_SKILL.read_text(encoding="utf-8")
    _assert_semantics(
        review,
        (
            "All provider work uses the singleton Root-mediated `BrowserTransport`",
            "EM and CM never spawn, contact, or invoke it directly",
            "Every request returned through Root with `next_action.owner=TRANSPORT`",
            "Bind `provider: chatgpt`, the exact Pro model",
            "Only the strict Agentify review surface may send",
            "Root validates and records archive bytes through the external-review CLI",
            "Agentify is the sole submission ledger",
        ),
    )
    assert "hmasd-external-pro-transport" not in review
    assert "hmasd-external-gemini-transport" not in review

    transport = BROWSER_SKILL.read_text(encoding="utf-8")
    _assert_semantics(
        transport,
        (
            "provider (`chatgpt` or `gemini`)",
            "provider/model-mismatched assignment",
            "Agentify strict `agentify_review_query`, once",
            "exact existing Agentify operation for observe-only work",
            "Agentify alone owns its strict-operation ledger",
        ),
    )


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
    _assert_semantics(
        text,
        (
            "Return to Root, and only Root",
            "Do not return scientific, engineering, Portfolio, capacity, approval, "
            "or lifecycle conclusions",
        ),
    )


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
