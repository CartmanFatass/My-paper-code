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


@pytest.mark.parametrize(
    "action,payload",
    [
        ("MAILBOX_ACK", {"message_ids": ["msg_1"]}),
        ("MAILBOX_INTAKE", {"items": [{"message_id": "msg_1", "intake_kind": "READ"}]}),
        ("MANAGED_PACKET_SEND", {"packet_kind": "X", "target_alias": "root", "payload_ref": "ref", "marker": "m"}),
        ("CONTEXT_REANCHOR_ACK", {}),
    ],
)
def test_every_mutating_action_requires_complete_typed_expected_tuple(action: str, payload: dict) -> None:
    import json

    envelope = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": action,
        "payload": payload,
    }
    text = "<HMASD_MANAGED_ACTOR_COMMAND_V1>" + json.dumps(envelope) + "</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    with pytest.raises(CommandProtocolError, match="expected currentness"):
        extract_managed_command(text)
    envelope["expected"] = {
        "checkpoint_id": None,
        "state_version": 0,
        "epoch_id": None,
        "epoch_revision": None,
    }
    if action == "CONTEXT_REANCHOR_ACK":
        envelope["expected"]["checkpoint_id"] = "ctx_1"
    parsed = extract_managed_command(
        "<HMASD_MANAGED_ACTOR_COMMAND_V1>" + json.dumps(envelope) + "</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    )
    assert parsed is not None and set(parsed["expected"]) == {
        "checkpoint_id", "state_version", "epoch_id", "epoch_revision"
    }


def test_mailbox_payload_plain_text_and_duplicate_envelope_validation() -> None:
    parsed = extract_managed_command(
        """<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"MAILBOX_ACK","expected":{"checkpoint_id":null,"state_version":0,"epoch_id":null,"epoch_revision":null},"payload":{"message_ids":["msg_1"]}}
</HMASD_MANAGED_ACTOR_COMMAND_V1>"""
    )
    assert parsed["action_kind"] == "MAILBOX_ACK"
    with pytest.raises(CommandProtocolError, match="message_ids"):
        extract_managed_command(
            """<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"MAILBOX_ACK","expected":{"checkpoint_id":null,"state_version":0,"epoch_id":null,"epoch_revision":null},"payload":{}}
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
