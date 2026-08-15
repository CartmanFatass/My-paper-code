import json

import pytest

from tools.codex_semantic_mvp.constants import (
    MAX_TYPED_JSON_BYTES,
    RETURN_END,
    RETURN_START,
)
from tools.codex_semantic_mvp.models import ReturnKind, SubagentReturnPacket
from tools.codex_semantic_mvp.protocol import (
    ProtocolError,
    extract_return_envelope,
    validate_subagent_return,
)


def valid_data() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "packet_kind": "SUBAGENT_RETURN",
        "workflow_id": "wf_01J-test",
        "task_id": "review_runtime_contract",
        "return_kind": "COMPLETED_ASSIGNMENT",
        "observed_facts": [
            {
                "object": "tools/example.py",
                "predicate": "function_present",
                "value": True,
                "evidence_ref": "tools/example.py:42",
            }
        ],
        "interpretive_claims": ["The bounded assignment was inspected."],
        "remaining_unknowns": ["Production-scale runtime was not authorized."],
        "suggested_next_actions": [
            {"owner": "/root", "action": "Perform Root intake."}
        ],
        "research_frontier": None,
        "global_disposition": "NOT_ASSERTED",
    }


def envelope(data: dict[str, object], prose: str = "") -> str:
    return f"{prose}{RETURN_START}{json.dumps(data)}{RETURN_END}"


def test_extracts_one_final_envelope_after_prose():
    data = valid_data()

    extracted = extract_return_envelope(
        envelope(data, "Analysis may contain {braces} and ordinary prose.\n")
    )

    assert extracted == data


def test_rejects_missing_marker():
    with pytest.raises(ProtocolError, match="exactly one"):
        extract_return_envelope(json.dumps(valid_data()))


def test_rejects_two_envelopes():
    message = envelope(valid_data()) + envelope(valid_data())

    with pytest.raises(ProtocolError, match="exactly one"):
        extract_return_envelope(message)


def test_accepts_replacement_character_in_python_text_outside_json():
    extracted = extract_return_envelope(envelope(valid_data(), "decoded text: �\n"))

    assert extracted["packet_kind"] == "SUBAGENT_RETURN"


def test_rejects_oversized_json_body():
    data = valid_data()
    data["remaining_unknowns"] = ["x" * MAX_TYPED_JSON_BYTES]

    with pytest.raises(ProtocolError, match="size"):
        extract_return_envelope(envelope(data))


def test_rejects_non_whitespace_trailing_text_after_end_marker():
    with pytest.raises(ProtocolError, match="trailing"):
        extract_return_envelope(envelope(valid_data()) + " trailing prose")


def test_allows_whitespace_after_end_marker():
    assert extract_return_envelope(envelope(valid_data()) + " \n\t") == valid_data()


def test_validates_frozen_typed_packet_and_enum():
    packet = validate_subagent_return(valid_data())

    assert isinstance(packet, SubagentReturnPacket)
    assert packet.return_kind is ReturnKind.COMPLETED_ASSIGNMENT
    assert packet.workflow_id == "wf_01J-test"
    assert packet.global_disposition == "NOT_ASSERTED"
    with pytest.raises(AttributeError):
        packet.task_id = "changed"


@pytest.mark.parametrize(
    "field, value",
    [
        ("packet_kind", "OTHER"),
        ("schema_version", "2.0"),
        ("global_disposition", "BLOCKED"),
        ("workflow_id", "contains whitespace"),
        ("task_id", ""),
    ],
)
def test_rejects_invalid_protocol_identity(field, value):
    data = valid_data()
    data[field] = value

    with pytest.raises(ProtocolError):
        validate_subagent_return(data)


def test_rejects_unknown_top_level_key_instead_of_discarding_it():
    data = valid_data()
    data["silent_state"] = "RETURNED"

    with pytest.raises(ProtocolError, match="unknown"):
        validate_subagent_return(data)


def test_rejects_wrong_nested_list_shapes():
    data = valid_data()
    data["observed_facts"] = [{"object": "x", "predicate": "p"}]

    with pytest.raises(ProtocolError, match="observed_facts"):
        validate_subagent_return(data)


def test_rejects_non_string_claims_and_actions():
    data = valid_data()
    data["interpretive_claims"] = [42]

    with pytest.raises(ProtocolError, match="interpretive_claims"):
        validate_subagent_return(data)


def test_validates_optional_research_frontier():
    data = valid_data()
    data["research_frontier"] = {
        "current_question": "What remains unresolved?",
        "strongest_live_alternative": "A confound remains.",
        "claim_ceiling": "Only the local observation is supported.",
        "next_discriminator": None,
        "exploration_debt": ["The production regime was not examined."],
    }

    packet = validate_subagent_return(data)

    assert packet.research_frontier is not None
    assert packet.research_frontier.next_discriminator is None
