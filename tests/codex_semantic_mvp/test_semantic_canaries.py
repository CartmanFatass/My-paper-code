import json

import pytest

from tools.codex_semantic_mvp.constants import RETURN_END, RETURN_START
from tools.codex_semantic_mvp.protocol import (
    extract_return_envelope,
    semantic_hazard_terms,
    validate_subagent_return,
)


RAW_PHRASES = [
    "BLOCKED",
    "fatal error; stop",
    "the direction should be retired",
    "I cannot proceed",
    "released",
]


def valid_data() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "packet_kind": "SUBAGENT_RETURN",
        "workflow_id": "wf_01J-test",
        "task_id": "review_runtime_contract",
        "return_kind": "COMPLETED_ASSIGNMENT",
        "observed_facts": [],
        "interpretive_claims": [],
        "remaining_unknowns": [],
        "suggested_next_actions": [],
        "research_frontier": None,
        "global_disposition": "NOT_ASSERTED",
    }


def typed_message(raw_phrase: str) -> str:
    return (
        f"{raw_phrase}. This is advisory prose.\n"
        f"{RETURN_START}{json.dumps(valid_data())}{RETURN_END}"
    )


@pytest.mark.parametrize("raw_phrase", RAW_PHRASES)
def test_raw_hazard_words_are_advisory_and_do_not_create_state(raw_phrase):
    terms = semantic_hazard_terms(raw_phrase)

    assert isinstance(terms, tuple)
    assert all(isinstance(term, str) for term in terms)
    assert not any(
        term in {
            "lifecycle",
            "obligation",
            "workflow",
            "scientific",
            "technical",
            "portfolio",
        }
        for term in terms
    )


def test_replacing_raw_hazard_prose_keeps_typed_packet_identical():
    blocked = validate_subagent_return(extract_return_envelope(typed_message("BLOCKED")))
    boundary = validate_subagent_return(
        extract_return_envelope(typed_message("LOCAL_AUTHORITY_BOUNDARY"))
    )

    assert blocked == boundary
    assert blocked.global_disposition == "NOT_ASSERTED"
    assert blocked.return_kind.value == "COMPLETED_ASSIGNMENT"


def test_hazard_annotation_has_no_state_transition_api():
    terms = semantic_hazard_terms("BLOCKED; the direction should be retired")

    assert terms == ("blocked", "retired")
