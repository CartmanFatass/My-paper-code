import pytest

from tools.codex_supervisor.command_protocol import CommandProtocolError, extract_managed_command


def test_extracts_stage3_command() -> None:
    text = """agent prose
<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"CONTEXT_REANCHOR_ACK","expected":{"checkpoint_id":"ctx_1","state_version":1,"epoch_id":null,"epoch_revision":null},"payload":{}}
</HMASD_MANAGED_ACTOR_COMMAND_V1>
"""
    command = extract_managed_command(text)
    assert command["action_kind"] == "CONTEXT_REANCHOR_ACK"


def test_rejects_identity_keys_and_stage4_actions() -> None:
    with pytest.raises(CommandProtocolError, match="forbidden"):
        extract_managed_command(
            """<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"NO_CONTROL_ACTION","binding_id":"x"}
</HMASD_MANAGED_ACTOR_COMMAND_V1>"""
        )
    parsed = extract_managed_command(
        """<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"MAILBOX_ACK","payload":{"message_ids":["msg_1"]}}
</HMASD_MANAGED_ACTOR_COMMAND_V1>"""
    )
    assert parsed["action_kind"] == "MAILBOX_ACK"
    with pytest.raises(CommandProtocolError, match="message_ids"):
        extract_managed_command(
            """<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"MAILBOX_ACK","payload":{}}
</HMASD_MANAGED_ACTOR_COMMAND_V1>"""
        )
    assert extract_managed_command("plain agent text") is None
    with pytest.raises(CommandProtocolError, match="more than one"):
        extract_managed_command(
            """<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"NO_CONTROL_ACTION","payload":{}}
</HMASD_MANAGED_ACTOR_COMMAND_V1>
<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"NO_CONTROL_ACTION","payload":{}}
</HMASD_MANAGED_ACTOR_COMMAND_V1>"""
        )
