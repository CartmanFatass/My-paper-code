import pytest

from tools.codex_supervisor.command_protocol import CommandProtocolError, extract_from_completed_item, extract_managed_command


@pytest.mark.parametrize(
    "payload",
    (
        '{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"NO_CONTROL_ACTION","actor_context_id":"root"}',
        '{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"NO_CONTROL_ACTION","source_kind":"USER_AUTHORITY"}',
        '{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"NO_CONTROL_ACTION","payload":{"owner_actor_context_id":"portfolio"}}',
    ),
)
def test_spoofed_identity_keys_are_rejected(payload: str) -> None:
    with pytest.raises(CommandProtocolError, match="forbidden"):
        extract_managed_command(f"<HMASD_MANAGED_ACTOR_COMMAND_V1>\n{payload}\n</HMASD_MANAGED_ACTOR_COMMAND_V1>")


def test_deltas_and_incomplete_items_are_rejected() -> None:
    text = """<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"NO_CONTROL_ACTION","payload":{}}
</HMASD_MANAGED_ACTOR_COMMAND_V1>"""
    with pytest.raises(CommandProtocolError, match="not completed"):
        extract_from_completed_item(item_type="agentMessage", lifecycle="STARTED", text=text)
    with pytest.raises(CommandProtocolError, match="agentMessage"):
        extract_from_completed_item(item_type="reasoning", lifecycle="COMPLETED", text=text)
