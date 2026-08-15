"""Strict typed-envelope parsing and advisory lexical annotations.

Raw child prose remains evidence. Only the validated JSON envelope is allowed
to produce a typed protocol object.
"""

import json
import re
from collections.abc import Mapping

from .constants import MAX_TYPED_JSON_BYTES, RETURN_END, RETURN_START
from .models import (
    ObservedFact,
    ResearchFrontier,
    ReturnKind,
    SubagentReturnPacket,
    SuggestedNextAction,
)


class ProtocolError(ValueError):
    """Raised when a typed envelope is absent, malformed, or out of contract."""


_IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_RETURN_KEYS = frozenset(
    {
        "schema_version",
        "packet_kind",
        "workflow_id",
        "task_id",
        "return_kind",
        "observed_facts",
        "interpretive_claims",
        "remaining_unknowns",
        "suggested_next_actions",
        "research_frontier",
        "global_disposition",
    }
)
_FACT_KEYS = frozenset({"object", "predicate", "value", "evidence_ref"})
_ACTION_KEYS = frozenset({"owner", "action"})
_FRONTIER_KEYS = frozenset(
    {
        "current_question",
        "strongest_live_alternative",
        "claim_ceiling",
        "next_discriminator",
        "exploration_debt",
    }
)


def extract_return_envelope(message: str) -> dict[str, object]:
    """Extract the sole final JSON envelope without changing the raw message."""
    if not isinstance(message, str):
        raise ProtocolError("message must be text")
    if message.count(RETURN_START) != 1 or message.count(RETURN_END) != 1:
        raise ProtocolError("message must contain exactly one start and end marker")

    start = message.index(RETURN_START)
    body_start = start + len(RETURN_START)
    end = message.index(RETURN_END)
    if end < body_start:
        raise ProtocolError("end marker precedes start marker")
    trailing = message[end + len(RETURN_END) :]
    if trailing.strip():
        raise ProtocolError("non-whitespace trailing text after end marker")

    body = message[body_start:end]
    if len(body.encode("utf-8")) > MAX_TYPED_JSON_BYTES:
        raise ProtocolError("typed JSON exceeds maximum size")
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ProtocolError(f"invalid typed JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ProtocolError("typed envelope must decode to a JSON object")
    return data


def _require_string(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ProtocolError(f"{key} must be a string")
    return value


def _require_exact_keys(data: Mapping[str, object], expected: frozenset[str], label: str) -> None:
    unknown = set(data) - expected
    missing = expected - set(data)
    if unknown:
        raise ProtocolError(f"unknown {label} key(s): {sorted(unknown)}")
    if missing:
        raise ProtocolError(f"missing {label} key(s): {sorted(missing)}")


def _parse_facts(value: object) -> tuple[ObservedFact, ...]:
    if not isinstance(value, list):
        raise ProtocolError("observed_facts must be a list")
    facts: list[ObservedFact] = []
    for item in value:
        if not isinstance(item, dict):
            raise ProtocolError("observed_facts entries must be exact objects")
        _require_exact_keys(item, _FACT_KEYS, "observed_facts")
        facts.append(
            ObservedFact(
                object=_require_string(item, "object"),
                predicate=_require_string(item, "predicate"),
                value=item["value"],
                evidence_ref=_require_string(item, "evidence_ref"),
            )
        )
    return tuple(facts)


def _parse_strings(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ProtocolError(f"{label} must be a list of strings")
    return tuple(value)


def _parse_actions(value: object) -> tuple[SuggestedNextAction, ...]:
    if not isinstance(value, list):
        raise ProtocolError("suggested_next_actions must be a list")
    actions: list[SuggestedNextAction] = []
    for item in value:
        if not isinstance(item, dict):
            raise ProtocolError("suggested_next_actions entries must be exact objects")
        _require_exact_keys(item, _ACTION_KEYS, "suggested_next_action")
        actions.append(
            SuggestedNextAction(
                owner=_require_string(item, "owner"),
                action=_require_string(item, "action"),
            )
        )
    return tuple(actions)


def _parse_frontier(value: object) -> ResearchFrontier | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ProtocolError("research_frontier must be an object or null")
    _require_exact_keys(value, _FRONTIER_KEYS, "research_frontier")
    next_discriminator = value["next_discriminator"]
    if next_discriminator is not None and not isinstance(next_discriminator, str):
        raise ProtocolError("research_frontier.next_discriminator must be a string or null")
    return ResearchFrontier(
        current_question=_require_string(value, "current_question"),
        strongest_live_alternative=_require_string(value, "strongest_live_alternative"),
        claim_ceiling=_require_string(value, "claim_ceiling"),
        next_discriminator=next_discriminator,
        exploration_debt=_parse_strings(value["exploration_debt"], "exploration_debt"),
    )


def validate_subagent_return(data: Mapping[str, object]) -> SubagentReturnPacket:
    """Validate and freeze a SUBAGENT_RETURN mapping."""
    if not isinstance(data, Mapping):
        raise ProtocolError("typed envelope must be a mapping")
    _require_exact_keys(data, _RETURN_KEYS, "envelope")
    if data["schema_version"] != "1.0":
        raise ProtocolError("schema_version must be 1.0")
    if data["packet_kind"] != "SUBAGENT_RETURN":
        raise ProtocolError("packet_kind must be SUBAGENT_RETURN")
    workflow_id = _require_string(data, "workflow_id")
    task_id = _require_string(data, "task_id")
    if not _IDENTIFIER.fullmatch(workflow_id) or not _IDENTIFIER.fullmatch(task_id):
        raise ProtocolError("workflow_id and task_id must match the identifier pattern")
    try:
        return_kind = ReturnKind(data["return_kind"])
    except (ValueError, TypeError) as exc:
        raise ProtocolError("return_kind is not recognized") from exc
    if data["global_disposition"] != "NOT_ASSERTED":
        raise ProtocolError("global_disposition must be NOT_ASSERTED")

    return SubagentReturnPacket(
        schema_version="1.0",
        packet_kind="SUBAGENT_RETURN",
        workflow_id=workflow_id,
        task_id=task_id,
        return_kind=return_kind,
        observed_facts=_parse_facts(data["observed_facts"]),
        interpretive_claims=_parse_strings(data["interpretive_claims"], "interpretive_claims"),
        remaining_unknowns=_parse_strings(data["remaining_unknowns"], "remaining_unknowns"),
        suggested_next_actions=_parse_actions(data["suggested_next_actions"]),
        research_frontier=_parse_frontier(data["research_frontier"]),
        global_disposition="NOT_ASSERTED",
    )


_HAZARD_PATTERN = re.compile(
    r"fatal error|cannot proceed|blocked|retired|released|stop", re.IGNORECASE
)


def semantic_hazard_terms(message: str) -> tuple[str, ...]:
    """Advisory observability only. The result must never drive a state transition."""
    if not isinstance(message, str):
        return ()
    seen: set[str] = set()
    terms: list[str] = []
    for match in _HAZARD_PATTERN.finditer(message):
        term = match.group(0).lower()
        if term not in seen:
            seen.add(term)
            terms.append(term)
    return tuple(terms)
