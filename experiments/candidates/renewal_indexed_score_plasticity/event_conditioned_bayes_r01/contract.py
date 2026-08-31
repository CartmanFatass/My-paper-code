"""Frozen structural contract for RISP event-conditioned Bayes R01.

This module contains data and validation only.  It deliberately has no import
of controller, host, analysis, or artifact code, so the pre-result ``describe``
and ``check`` commands cannot evaluate registered actions or returns.
"""

from __future__ import annotations

import copy
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DIRECTION_ID = "renewal_indexed_score_plasticity"
SPEC_SCHEMA = "RISP-ECR-R01-SPEC-V1"
PUBLIC_HISTORY_SCHEMA = "RISP-ECR-R01-PUBLIC-HISTORY-V1"
TWIN_CENSUS_SCHEMA = "RISP-ECR-R01-TWIN-CENSUS-V1"
COMPLETE_RESULT_SCHEMA = "RISP-ECR-R01-COMPLETE-RESULT-V1"
CHECK_SCHEMA = "RISP-ECR-R01-STRUCTURAL-CHECK-V1"
DESCRIPTION_SCHEMA = "RISP-ECR-R01-DESCRIPTION-V1"
NATIVE_REGISTRY_KEY = "RISP_ECR_R01_EXACT_EVENT_HOST_V1"
RESULT_NAME = "RISP_ECR_R01_COMPLETE.json"

REGISTERED_BINDING = "REGISTERED"
TEST_ONLY_BINDING = "TEST_ONLY"
ACTIONS = ("LEFT", "CENTER", "RIGHT")
ACKS = ("+", "-")
CONTROLLERS = (
    "RAW_HISTORY_BAYES",
    "FULL_BAYES_K",
    "FULL_BAYES_K_ERASED",
    "LAST_ACK_BAYES",
    "LAST_ACK_G",
)
ALLOWED_DURATIONS = (4, 8, 12)
EVENT_ORDER = (
    "HOLD_COMPLETION",
    "MOTION",
    "ACK",
    "PRIVATE_UPDATE",
    "NEXT_ACTION",
)
CERTIFIED_STATUS = "CERTIFIED_RENEWAL_INDEXED_BAYES_WITNESS"
INVALID_STATUS = "INVALID_CERTIFICATE"
TEST_COMPLETE_STATUS = "TEST_ONLY_COMPLETE_CONFORMANCE"

MAX_SPEC_BYTES = 1 << 20
MAX_EVENTS_PER_HISTORY = 8
MAX_HISTORIES = 8
MAX_WALL_SECONDS = 600
MAX_RSS_BYTES = 1 << 30
MAX_DURABLE_BYTES = 256 << 20

SCHEMA_DIRECTORY = Path(__file__).resolve().parent / "schemas"
SCHEMA_FILES = {
    SPEC_SCHEMA: "spec.schema.json",
    PUBLIC_HISTORY_SCHEMA: "public_history.schema.json",
    TWIN_CENSUS_SCHEMA: "twin_census.schema.json",
    COMPLETE_RESULT_SCHEMA: "complete_result.schema.json",
}


class ContractError(ValueError):
    """A specification or public-history document violates the frozen ABI."""


def canonical_json_bytes(value: object) -> bytes:
    """Return the sole canonical JSON encoding used by the package."""

    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def fraction_pair(value: Fraction | int) -> list[int]:
    exact = value if isinstance(value, Fraction) else Fraction(value)
    return [exact.numerator, exact.denominator]


def parse_fraction_pair(value: object, field: str) -> Fraction:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
    ):
        raise ContractError(f"{field} must be a [numerator, denominator] integer pair")
    numerator, denominator = value
    if denominator <= 0:
        raise ContractError(f"{field} denominator must be positive")
    if math.gcd(numerator, denominator) != 1:
        raise ContractError(f"{field} rational pair must be reduced")
    return Fraction(numerator, denominator)


def _event(renewal: int, start: int, duration: int, action: str, ack: str) -> dict[str, object]:
    return {
        "renewal_index": renewal,
        "primitive_start": start,
        "primitive_end": start + duration,
        "completed_duration": duration,
        "action": action,
        "ack": ack,
        "action_event_index": 5 * renewal,
        "hold_completion_event_index": 5 * renewal + 1,
        "motion_event_index": 5 * renewal + 2,
        "ack_event_index": 5 * renewal + 3,
        "private_update_event_index": 5 * renewal + 4,
    }


def _history(
    history_id: str,
    durations: Sequence[int],
    actions: Sequence[str],
    acks: Sequence[str],
    *,
    binding_class: str = REGISTERED_BINDING,
) -> dict[str, object]:
    if not (len(durations) == len(actions) == len(acks)):
        raise AssertionError("internal frozen history arity mismatch")
    events: list[dict[str, object]] = []
    primitive_time = 0
    for renewal, (duration, action, ack) in enumerate(zip(durations, actions, acks)):
        events.append(_event(renewal, primitive_time, duration, action, ack))
        primitive_time += duration
    next_duration = 4
    return {
        "schema": PUBLIC_HISTORY_SCHEMA,
        "history_id": history_id,
        "binding_class": binding_class,
        "initial_belief": [[1, 3], [1, 3], [1, 3]],
        "events": events,
        "decision": {
            "renewal_index": len(events),
            "primitive_time": primitive_time,
            "next_duration": next_duration,
            "next_action_event_index": 5 * len(events),
            "next_hold_credit": {
                "primitive_start": primitive_time,
                "primitive_end": primitive_time + next_duration,
            },
        },
    }


def registered_spec() -> dict[str, object]:
    """Return a fresh copy of the machine-exact registered R01 specification.

    The histories below are literal registered data.  No runtime search,
    filtering, or witness substitution is used to construct them.
    """

    prior_actions = ("CENTER", "CENTER", "LEFT")
    duration_actions = ("CENTER", "CENTER", "CENTER", "LEFT")
    value: dict[str, object] = {
        "schema": SPEC_SCHEMA,
        "direction_id": DIRECTION_ID,
        "binding_class": REGISTERED_BINDING,
        "native_registry_key": NATIVE_REGISTRY_KEY,
        "zero_learning": {
            "scientific_rng_draws": 0,
            "seeds": [],
            "optimizers": 0,
            "updates": 0,
            "checkpoints": 0,
            "sampling": 0,
        },
        "actions": list(ACTIONS),
        "acks": list(ACKS),
        "tie_order": list(ACTIONS),
        "controllers": list(CONTROLLERS),
        "host": {
            "sector_count": 3,
            "initial_belief": [[1, 3], [1, 3], [1, 3]],
            "allowed_durations": list(ALLOWED_DURATIONS),
            "transition_law": "1/3*J+(15/16)^k*(I-1/3*J)",
            "ack_match_positive_probability": [4, 5],
            "ack_mismatch_positive_probability": [1, 5],
            "utility": "completed_duration*ack_sign",
            "native_value": "k*(-3/5+(6/5)*(belief*P_k)[action])",
            "event_order": list(EVENT_ORDER),
        },
        "support": {
            "reference_action_law": [[1, 3], [1, 3], [1, 3]],
            "full_support_required": True,
            "twin_side_weight": [1, 2],
            "twins": [
                {
                    "twin_id": "PRIOR_HISTORY_ACK_TWIN",
                    "coarsened_controller": "LAST_ACK_BAYES",
                    "rows": [
                        {
                            "side": "A",
                            "population_weight": [1, 2],
                            "expected_raw_action": "CENTER",
                            "history": _history(
                                "PRIOR_HISTORY_ACK_TWIN_A",
                                (4, 4, 4),
                                prior_actions,
                                ("+", "+", "+"),
                            ),
                        },
                        {
                            "side": "B",
                            "population_weight": [1, 2],
                            "expected_raw_action": "LEFT",
                            "history": _history(
                                "PRIOR_HISTORY_ACK_TWIN_B",
                                (4, 4, 4),
                                prior_actions,
                                ("+", "-", "+"),
                            ),
                        },
                    ],
                },
                {
                    "twin_id": "DURATION_ORDER_TWIN",
                    "coarsened_controller": "FULL_BAYES_K_ERASED",
                    "rows": [
                        {
                            "side": "A",
                            "population_weight": [1, 2],
                            "expected_raw_action": "LEFT",
                            "history": _history(
                                "DURATION_ORDER_TWIN_A",
                                (4, 4, 12, 8),
                                duration_actions,
                                ("+", "+", "+", "+"),
                            ),
                        },
                        {
                            "side": "B",
                            "population_weight": [1, 2],
                            "expected_raw_action": "CENTER",
                            "history": _history(
                                "DURATION_ORDER_TWIN_B",
                                (4, 12, 4, 8),
                                duration_actions,
                                ("+", "+", "+", "+"),
                            ),
                        },
                    ],
                },
            ],
        },
        "acceptance": {
            "success_status": CERTIFIED_STATUS,
            "failure_status": INVALID_STATUS,
            "require_unique_actions": True,
            "require_positive_exact_path_mass": True,
            "require_raw_full_rowwise_equality": True,
            "require_equal_twin_weights": True,
            "require_positive_erased_regret": True,
            "forbid_replacement_history_search": True,
        },
        "resources": {
            "cpu_threads": 1,
            "gpu": False,
            "network": False,
            "wall_seconds_upper": MAX_WALL_SECONDS,
            "rss_bytes_upper": MAX_RSS_BYTES,
            "durable_output_bytes_upper": MAX_DURABLE_BYTES,
        },
        "artifact": {
            "schema": COMPLETE_RESULT_SCHEMA,
            "result_name": RESULT_NAME,
            "publication": "ATOMIC_COMPLETE_ONLY_NO_OVERWRITE",
            "retry": False,
            "resume": False,
        },
    }
    return copy.deepcopy(value)


def make_test_history(
    history_id: str,
    durations: Sequence[int],
    actions: Sequence[str],
    acks: Sequence[str],
) -> dict[str, object]:
    """Build a bounded synthetic history that is permanently TEST_ONLY."""

    if not history_id.startswith("TEST_ONLY_"):
        raise ContractError("TEST_ONLY history id must begin with TEST_ONLY_")
    return _history(
        history_id,
        durations,
        actions,
        acks,
        binding_class=TEST_ONLY_BINDING,
    )


def _strict_object(pairs: Iterable[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def strict_json_loads(payload: bytes, *, label: str) -> object:
    try:
        text = payload.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ContractError(f"{label} contains non-finite JSON token {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"{label} is not strict UTF-8 JSON") from error


def load_json_document(path: Path, *, max_bytes: int = MAX_SPEC_BYTES) -> object:
    try:
        size = path.stat().st_size
    except OSError as error:
        raise ContractError(f"input document is unavailable: {path}") from error
    if size <= 0 or size > max_bytes:
        raise ContractError(f"input document size must be in [1,{max_bytes}] bytes")
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise ContractError(f"input document cannot be read: {path}") from error
    return strict_json_loads(payload, label=str(path))


def load_schema(schema_name: str) -> dict[str, object]:
    filename = SCHEMA_FILES.get(schema_name)
    if filename is None:
        raise ContractError(f"unknown schema name: {schema_name}")
    value = load_json_document(SCHEMA_DIRECTORY / filename)
    if not isinstance(value, dict):
        raise ContractError(f"schema {schema_name} is not an object")
    return value


def validate_schema_instance(value: object, schema_name: str) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:
        raise ContractError("jsonschema is required for contract validation") from error
    schema = load_schema(schema_name)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "<root>"
        raise ContractError(f"{schema_name} validation failed at {location}: {first.message}")


def validate_public_history(
    value: object,
    *,
    expected_binding: str | None = None,
) -> Mapping[str, object]:
    validate_schema_instance(value, PUBLIC_HISTORY_SCHEMA)
    if not isinstance(value, dict):
        raise ContractError("public history must be an object")
    binding = value["binding_class"]
    if expected_binding is not None and binding != expected_binding:
        raise ContractError(f"public history binding must be {expected_binding}")
    belief = value["initial_belief"]
    assert isinstance(belief, list)
    exact_belief = [parse_fraction_pair(item, f"initial_belief[{index}]") for index, item in enumerate(belief)]
    if sum(exact_belief, Fraction()) != 1 or any(item <= 0 for item in exact_belief):
        raise ContractError("initial belief must be a positive normalized law")
    events = value["events"]
    assert isinstance(events, list)
    if not 1 <= len(events) <= MAX_EVENTS_PER_HISTORY:
        raise ContractError("public history event count is outside the bounded host")
    primitive_time = 0
    for renewal, event in enumerate(events):
        assert isinstance(event, dict)
        duration = event["completed_duration"]
        expected_indices = {
            "action_event_index": 5 * renewal,
            "hold_completion_event_index": 5 * renewal + 1,
            "motion_event_index": 5 * renewal + 2,
            "ack_event_index": 5 * renewal + 3,
            "private_update_event_index": 5 * renewal + 4,
        }
        if event["renewal_index"] != renewal:
            raise ContractError("renewal indices must be consecutive from zero")
        if duration not in ALLOWED_DURATIONS:
            raise ContractError("completed duration is outside frozen support")
        if event["primitive_start"] != primitive_time:
            raise ContractError("primitive holds must be contiguous")
        if event["primitive_end"] != primitive_time + duration:
            raise ContractError("primitive end must equal start plus completed duration")
        if any(event[field] != expected for field, expected in expected_indices.items()):
            raise ContractError("action/hold/motion/ACK/update event order is invalid")
        primitive_time += duration
    decision = value["decision"]
    assert isinstance(decision, dict)
    next_duration = decision["next_duration"]
    if next_duration not in ALLOWED_DURATIONS:
        raise ContractError("next action-visible duration is outside frozen support")
    if (
        decision["renewal_index"] != len(events)
        or decision["primitive_time"] != primitive_time
        or decision["next_action_event_index"] != 5 * len(events)
    ):
        raise ContractError("decision clock does not follow the final private update")
    credit = decision["next_hold_credit"]
    assert isinstance(credit, dict)
    if (
        credit["primitive_start"] != primitive_time
        or credit["primitive_end"] != primitive_time + next_duration
    ):
        raise ContractError("next-hold credit endpoint is inconsistent")
    return value


def _iter_registered_rows(spec: Mapping[str, object]) -> Iterable[Mapping[str, object]]:
    support = spec["support"]
    assert isinstance(support, dict)
    twins = support["twins"]
    assert isinstance(twins, list)
    for twin in twins:
        assert isinstance(twin, dict)
        rows = twin["rows"]
        assert isinstance(rows, list)
        yield from rows


def validate_registered_spec(value: object) -> Mapping[str, object]:
    """Validate and byte-semantically bind the sole registered specification."""

    validate_schema_instance(value, SPEC_SCHEMA)
    if not isinstance(value, dict):
        raise ContractError("registered spec must be an object")
    if value != registered_spec():
        raise ContractError("spec does not equal the exact registered RISP-ECR-R01 identity")
    rows = list(_iter_registered_rows(value))
    if len(rows) != 4 or len(rows) > MAX_HISTORIES:
        raise ContractError("registered census must contain exactly four histories")
    for index, row in enumerate(rows):
        weight = parse_fraction_pair(row["population_weight"], f"row[{index}].population_weight")
        if weight != Fraction(1, 2):
            raise ContractError("twin sides must retain exact equal weight")
        validate_public_history(row["history"], expected_binding=REGISTERED_BINDING)
    return value


def load_registered_spec(path: Path) -> Mapping[str, object]:
    return validate_registered_spec(load_json_document(path))


def schema_versions() -> list[str]:
    """Return literal schema/version labels; these are not admission hashes."""

    return sorted(SCHEMA_FILES)


def structural_check(spec: Mapping[str, object]) -> dict[str, object]:
    """Return a pre-result structural receipt without importing action logic."""

    validate_registered_spec(spec)
    return {
        "schema": CHECK_SCHEMA,
        "binding_class": REGISTERED_BINDING,
        "status": "STRUCTURALLY_VALID_PRE_RESULT_ONLY",
        "spec_schema": SPEC_SCHEMA,
        "exact_registered_spec_match": True,
        "schema_versions": schema_versions(),
        "registered_history_count": 4,
        "registered_twin_count": 2,
        "controller_actions_evaluated": 0,
        "controller_returns_evaluated": 0,
        "scientific_rng_draws": 0,
        "result_bearing": False,
        "certification_executed": False,
    }


def description() -> dict[str, object]:
    """Describe the frozen interface without evaluating the registered census."""

    spec = registered_spec()
    return {
        "schema": DESCRIPTION_SCHEMA,
        "direction_id": DIRECTION_ID,
        "spec": spec,
        "spec_schema": SPEC_SCHEMA,
        "schemas": schema_versions(),
        "pre_result_commands": ["describe", "check"],
        "result_bearing_command": "certify",
        "registered_actions_evaluated": 0,
        "registered_returns_evaluated": 0,
        "no_history_search": True,
    }


__all__ = [
    "ACKS",
    "ACTIONS",
    "ALLOWED_DURATIONS",
    "CERTIFIED_STATUS",
    "CHECK_SCHEMA",
    "COMPLETE_RESULT_SCHEMA",
    "CONTROLLERS",
    "ContractError",
    "DESCRIPTION_SCHEMA",
    "DIRECTION_ID",
    "EVENT_ORDER",
    "INVALID_STATUS",
    "MAX_DURABLE_BYTES",
    "MAX_HISTORIES",
    "MAX_RSS_BYTES",
    "MAX_SPEC_BYTES",
    "MAX_WALL_SECONDS",
    "NATIVE_REGISTRY_KEY",
    "PUBLIC_HISTORY_SCHEMA",
    "REGISTERED_BINDING",
    "RESULT_NAME",
    "SPEC_SCHEMA",
    "TEST_COMPLETE_STATUS",
    "TEST_ONLY_BINDING",
    "TWIN_CENSUS_SCHEMA",
    "canonical_json_bytes",
    "description",
    "fraction_pair",
    "load_registered_spec",
    "make_test_history",
    "parse_fraction_pair",
    "registered_spec",
    "schema_versions",
    "structural_check",
    "validate_public_history",
    "validate_registered_spec",
    "validate_schema_instance",
]
