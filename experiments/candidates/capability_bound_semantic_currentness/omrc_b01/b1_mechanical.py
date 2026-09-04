"""Nonpolar B1 mechanical conformance and terminal RAW competence.

The functions in this module accept observations rather than caller-supplied
``*_pass`` assertions.  They deliberately do not produce AUCs, diagnostic
rates, scientific polarity, branches, or a B2 decision.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from .b1_contract import B1_SEEDS


class B1MechanicalError(ValueError):
    """Raised when a mechanical input uses a non-frozen public shape."""


B1_MECHANICAL_SCHEMA = "cbsc_omrc_b01_b1_mechanical_v1"
MECHANICAL_INPUT_DESCRIPTOR_SCHEMA = "cbsc_omrc_b01_b1_mechanical_inputs_v1"
RAW_COMPETENCE_SCHEMA = "cbsc_omrc_b01_b1_raw_competence_v1"
B0_NONPOLARITY_SCHEMA = "cbsc_omrc_b01_b0_nonpolarity_v1"

_GIB = 1024**3
_MIB = 1024**2
_SCIENTIFIC_ACTIONS = ("SERVE", "REFRESH", "SAFE_FALLBACK")
_ACTION_INDEX = {"SERVE": 1, "REFRESH": 2, "SAFE_FALLBACK": 3}
_DECISION_MASK = (False, True, True, True)
_EXPECTED_TAPES = tuple(range(32))
_EXPECTED_OPPORTUNITIES = tuple(range(24))

_FACT_FIELDS = frozenset(
    {
        "inventories",
        "resources",
        "digest_bindings",
        "tape_bindings",
        "work_bindings",
        "fp32_records",
        "numeric_records",
        "reset_records",
        "adaptation_records",
        "checkpoint_records",
        "learner_visibility_records",
        "legal_action_records",
        "twin_records",
        "literal_records",
    }
)
_COMPETENCE_FIELDS = frozenset({"seed", "checkpoint_update", "split", "tapes"})
_TAPE_FIELDS = frozenset(
    {
        "tape_id",
        "raw_return",
        "always_refresh_return",
        "always_safe_return",
        "decisions",
    }
)
_DECISION_FIELDS = frozenset(
    {
        "opportunity_id",
        "selected_action",
        "oracle_action",
        "request_active",
        "access_mode",
        "presented_body_native_neutral",
        "address_match_truth",
        "payload_source_match_truth",
        "content_match_truth",
        "owner_match_truth",
        "epoch_match_truth",
        "legal_action_mask",
        "actor_logits_fp32_bits",
        "critic_value_fp32_bits",
        "selected_action_log_probability_fp32_bits",
    }
)

_BLOCKING_ORDER = (
    "MISSING_OR_DUPLICATE_INVENTORY",
    "RESOURCE_ADMISSION_FAILURE",
    "RESOURCE_CAP_BREACH",
    "PUBLICATION_DIGEST_FAILURE",
    "TAPE_CONFORMANCE_FAILURE",
    "UNEQUAL_WORK_EXPOSURE",
    "FP32_CONFORMANCE_FAILURE",
    "NONFINITE_VALUE",
    "RECURRENT_RESET_FAILURE",
    "EVALUATION_ADAPTATION_FAILURE",
    "CHECKPOINT_ROUNDTRIP_FAILURE",
    "LEARNER_LEAKAGE",
    "ILLEGAL_ACTION",
    "INCOMPLETE_TWIN",
    "LITERAL_CONFORMANCE_FAILURE",
    "RAW_COMPETENCE_FAILURE",
    "RAW_COMPETENCE_UNESTABLISHED",
)

_INPUT_SOURCE_FIELDS = frozenset(
    {"source_relative_path", "source_file_sha256", "json_pointer"}
)
_INPUT_DESCRIPTOR_FIELDS = frozenset(
    {
        "schema",
        "authority",
        "test_only",
        "training_slot_indices",
        "raw_worker_sources",
        "policy_execution_mode_sources",
        "table_bindings",
        "artifact_inventory_sha256",
        "raw_facts_sha256",
        "raw_competence_inputs_sha256",
    }
)


def _canonical_sha256(value: object) -> str:
    try:
        payload = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise B1MechanicalError("mechanical input is not canonical JSON") from exc
    return hashlib.sha256(payload).hexdigest()


def _validate_input_source(value: object, name: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or frozenset(value) != _INPUT_SOURCE_FIELDS:
        raise B1MechanicalError(f"{name} source fields differ")
    relative = value["source_relative_path"]
    pointer = value["json_pointer"]
    if (
        type(relative) is not str
        or not relative
        or "\\" in relative
        or relative.startswith("/")
        or any(part in {"", ".", ".."} for part in relative.split("/"))
        or type(pointer) is not str
        or not pointer.startswith("/")
    ):
        raise B1MechanicalError(f"{name} source path/pointer differs")
    return {
        "source_relative_path": relative,
        "source_file_sha256": _digest(value["source_file_sha256"], f"{name} source SHA"),
        "json_pointer": pointer,
    }


def build_mechanical_input_descriptor(
    raw_facts: Mapping[str, Any],
    raw_competence_inputs: Sequence[Mapping[str, Any]],
    *,
    authority: str,
    test_only: bool,
    training_slot_indices: Sequence[int],
    raw_worker_sources: Sequence[Sequence[Mapping[str, str]]],
    policy_execution_mode_sources: Sequence[Mapping[str, str]],
    table_bindings: Sequence[Mapping[str, Any]],
    artifact_inventory_sha256: str | None,
) -> dict[str, Any]:
    """Bind compact evidence locators to the exact mechanical arguments."""

    if authority not in {"BOUND_ARTIFACT_EVIDENCE", "TEST_ARGUMENTS_ONLY"}:
        raise B1MechanicalError("mechanical input descriptor authority differs")
    if type(test_only) is not bool:
        raise B1MechanicalError("mechanical input descriptor test_only differs")
    if (
        not isinstance(training_slot_indices, Sequence)
        or isinstance(training_slot_indices, (str, bytes, bytearray))
        or any(type(index) is not int or not 0 <= index < 12 for index in training_slot_indices)
        or len(set(training_slot_indices)) != len(training_slot_indices)
    ):
        raise B1MechanicalError("mechanical training slot indices differ")
    worker_groups: list[list[dict[str, str]]] = []
    for group in raw_worker_sources:
        if not isinstance(group, Sequence) or isinstance(group, (str, bytes, bytearray)):
            raise B1MechanicalError("raw worker source group differs")
        worker_groups.append(
            [_validate_input_source(source, "raw worker") for source in group]
        )
    mode_sources = [
        _validate_input_source(source, "policy execution mode")
        for source in policy_execution_mode_sources
    ]
    bindings: list[dict[str, Any]] = []
    for row in table_bindings:
        if not isinstance(row, Mapping) or set(row) != {
            "table", "sha256", "row_count", "byte_count"
        }:
            raise B1MechanicalError("mechanical table binding fields differ")
        if (
            type(row["table"]) is not str
            or not row["table"]
            or type(row["row_count"]) is not int
            or row["row_count"] < 0
            or type(row["byte_count"]) is not int
            or row["byte_count"] < 0
        ):
            raise B1MechanicalError("mechanical table binding values differ")
        bindings.append(
            {
                "table": row["table"],
                "sha256": _digest(row["sha256"], "mechanical table SHA"),
                "row_count": row["row_count"],
                "byte_count": row["byte_count"],
            }
        )
    if authority == "BOUND_ARTIFACT_EVIDENCE":
        if (
            len(worker_groups) != len(training_slot_indices)
            or not all(worker_groups)
            or any(
                not source["source_relative_path"].endswith("/result.json.gz")
                for group in worker_groups for source in group
            )
            or not mode_sources
            or (
                not test_only and any(
                    not source["source_relative_path"].endswith("/result.json.gz")
                    for source in mode_sources
                )
            )
            or not bindings
            or artifact_inventory_sha256 is None
        ):
            raise B1MechanicalError("bound mechanical evidence descriptor is incomplete")
    artifact_sha = (
        None
        if artifact_inventory_sha256 is None
        else _digest(artifact_inventory_sha256, "artifact inventory SHA")
    )
    return {
        "schema": MECHANICAL_INPUT_DESCRIPTOR_SCHEMA,
        "authority": authority,
        "test_only": test_only,
        "training_slot_indices": list(training_slot_indices),
        "raw_worker_sources": worker_groups,
        "policy_execution_mode_sources": mode_sources,
        "table_bindings": bindings,
        "artifact_inventory_sha256": artifact_sha,
        "raw_facts_sha256": _canonical_sha256(raw_facts),
        "raw_competence_inputs_sha256": _canonical_sha256(raw_competence_inputs),
    }


def _validate_mechanical_input_descriptor(
    value: object,
    *,
    raw_facts: Mapping[str, Any],
    raw_competence_inputs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or frozenset(value) != _INPUT_DESCRIPTOR_FIELDS:
        raise B1MechanicalError("mechanical input descriptor fields differ")
    rebuilt = build_mechanical_input_descriptor(
        raw_facts,
        raw_competence_inputs,
        authority=value["authority"],
        test_only=value["test_only"],
        training_slot_indices=value["training_slot_indices"],
        raw_worker_sources=value["raw_worker_sources"],
        policy_execution_mode_sources=value["policy_execution_mode_sources"],
        table_bindings=value["table_bindings"],
        artifact_inventory_sha256=value["artifact_inventory_sha256"],
    )
    if rebuilt != dict(value):
        raise B1MechanicalError("mechanical input descriptor digests differ from arguments")
    return rebuilt


def _exact_fields(value: object, fields: frozenset[str], name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or frozenset(value) != fields:
        raise B1MechanicalError(f"{name} fields differ")
    return value


def _records(value: object, name: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or not value:
        raise B1MechanicalError(f"{name} must be a nonempty list")
    if any(not isinstance(record, Mapping) for record in value):
        raise B1MechanicalError(f"{name} contains a non-record")
    return list(value)


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise B1MechanicalError(f"{name} must be an integer >= {minimum}")
    return value


def _number(value: object, name: str) -> int | float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise B1MechanicalError(f"{name} must be a finite number")
    return value


def _digest(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise B1MechanicalError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _fp32_bits(value: object) -> tuple[bool, bool]:
    """Return ``(well_formed, finite)`` for one raw IEEE-754 binary32 word."""

    if (
        type(value) is not str
        or len(value) != 8
        or any(character not in "0123456789abcdef" for character in value)
    ):
        return False, False
    word = int(value, 16)
    return True, ((word >> 23) & 0xFF) != 0xFF


def _fraction(value: object) -> Fraction | None:
    if not isinstance(value, Mapping) or set(value) != {"numerator", "denominator"}:
        return None
    numerator = value["numerator"]
    denominator = value["denominator"]
    if type(numerator) is not int or type(denominator) is not int or denominator == 0:
        return None
    return Fraction(numerator, denominator)


def _ratio_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _easy_open(decision: Mapping[str, Any]) -> bool:
    return (
        decision["request_active"] is True
        and decision["access_mode"] == "OPEN"
        and decision["presented_body_native_neutral"] is False
        and decision["address_match_truth"] is True
        and decision["payload_source_match_truth"] is True
        and decision["content_match_truth"] is True
        and decision["owner_match_truth"] is True
        and decision["epoch_match_truth"] is True
    )


def compute_raw_competence(record: Mapping[str, Any]) -> dict[str, Any]:
    """Recompute one B1 RAW seed's exact checkpoint-48 competence predicate."""

    raw = _exact_fields(record, _COMPETENCE_FIELDS, "RAW competence")
    seed = raw["seed"]
    if type(seed) is not int or seed not in B1_SEEDS:
        raise B1MechanicalError("RAW competence seed differs from frozen B1 seeds")
    if raw["checkpoint_update"] != 48 or raw["split"] != "EVAL_STOCHASTIC":
        raise B1MechanicalError("RAW competence requires checkpoint 48 EVAL_STOCHASTIC")
    if not isinstance(raw["tapes"], list):
        raise B1MechanicalError("RAW competence tapes must be a list")

    tape_counts: Counter[int] = Counter()
    indexed_tapes: dict[int, Mapping[str, Any]] = {}
    malformed_records = 0
    for tape in raw["tapes"]:
        if not isinstance(tape, Mapping) or frozenset(tape) != _TAPE_FIELDS:
            malformed_records += 1
            continue
        tape_id = tape["tape_id"]
        if type(tape_id) is not int or tape_id not in _EXPECTED_TAPES:
            malformed_records += 1
            continue
        tape_counts[tape_id] += 1
        indexed_tapes.setdefault(tape_id, tape)

    missing_count = malformed_records + sum(
        1 for tape_id in _EXPECTED_TAPES if tape_id not in indexed_tapes
    )
    malformed_records = 0
    duplicate_count = sum(max(0, count - 1) for count in tape_counts.values())
    nonfinite_count = 0
    mask_violation_count = 0
    raw_returns: list[Fraction] = []
    refresh_returns: list[Fraction] = []
    safe_returns: list[Fraction] = []
    selected_counts: Counter[str] = Counter()
    oracle_counts: Counter[str] = Counter()
    easy_eligible_count = 0
    easy_serve_count = 0
    decision_count = 0

    for tape_id in _EXPECTED_TAPES:
        tape = indexed_tapes.get(tape_id)
        if tape is None:
            continue
        fractions = tuple(
            _fraction(tape[field])
            for field in ("raw_return", "always_refresh_return", "always_safe_return")
        )
        if any(value is None for value in fractions):
            missing_count += sum(value is None for value in fractions)
        else:
            raw_return, refresh_return, safe_return = fractions
            raw_returns.append(raw_return)
            refresh_returns.append(refresh_return)
            safe_returns.append(safe_return)

        decisions = tape["decisions"]
        if not isinstance(decisions, list):
            missing_count += 24
            continue
        opportunity_counts: Counter[int] = Counter()
        indexed_decisions: dict[int, Mapping[str, Any]] = {}
        for decision in decisions:
            if not isinstance(decision, Mapping) or frozenset(decision) != _DECISION_FIELDS:
                malformed_records += 1
                continue
            opportunity = decision["opportunity_id"]
            if type(opportunity) is not int or opportunity not in _EXPECTED_OPPORTUNITIES:
                malformed_records += 1
                continue
            opportunity_counts[opportunity] += 1
            indexed_decisions.setdefault(opportunity, decision)
        missing_count += malformed_records
        malformed_records = 0
        missing_count += sum(
            1 for opportunity in _EXPECTED_OPPORTUNITIES if opportunity not in indexed_decisions
        )
        duplicate_count += sum(max(0, count - 1) for count in opportunity_counts.values())

        for opportunity in _EXPECTED_OPPORTUNITIES:
            decision = indexed_decisions.get(opportunity)
            if decision is None:
                continue
            decision_count += 1
            selected = decision["selected_action"]
            oracle = decision["oracle_action"]
            if selected not in _SCIENTIFIC_ACTIONS:
                mask_violation_count += 1
            else:
                selected_counts[selected] += 1
            if oracle not in _SCIENTIFIC_ACTIONS:
                missing_count += 1
            else:
                oracle_counts[oracle] += 1

            mask = decision["legal_action_mask"]
            if (
                not isinstance(mask, list)
                or tuple(mask) != _DECISION_MASK
                or selected not in _ACTION_INDEX
                or not mask[_ACTION_INDEX[selected]]
            ):
                mask_violation_count += 1

            bit_words = decision["actor_logits_fp32_bits"]
            if not isinstance(bit_words, list) or len(bit_words) != 4:
                missing_count += 1
            else:
                for word in bit_words:
                    formed, finite = _fp32_bits(word)
                    if not formed:
                        missing_count += 1
                    elif not finite:
                        nonfinite_count += 1
            for field in (
                "critic_value_fp32_bits",
                "selected_action_log_probability_fp32_bits",
            ):
                formed, finite = _fp32_bits(decision[field])
                if not formed:
                    missing_count += 1
                elif not finite:
                    nonfinite_count += 1

            truth_values = (
                decision["request_active"],
                decision["presented_body_native_neutral"],
                decision["address_match_truth"],
                decision["payload_source_match_truth"],
                decision["content_match_truth"],
                decision["owner_match_truth"],
                decision["epoch_match_truth"],
            )
            if any(type(value) is not bool for value in truth_values) or decision[
                "access_mode"
            ] not in ("OPEN", "GATED"):
                missing_count += 1
            elif _easy_open(decision):
                easy_eligible_count += 1
                easy_serve_count += int(selected == "SERVE")

    complete_returns = (
        len(raw_returns) == len(refresh_returns) == len(safe_returns) == 32
    )
    reference_pass: bool | None
    raw_mean: Fraction | None = None
    refresh_mean: Fraction | None = None
    safe_mean: Fraction | None = None
    if complete_returns and missing_count == 0 and duplicate_count == 0:
        raw_mean = sum(raw_returns, Fraction(0)) / 32
        refresh_mean = sum(refresh_returns, Fraction(0)) / 32
        safe_mean = sum(safe_returns, Fraction(0)) / 32
        reference_pass = raw_mean > refresh_mean and raw_mean > safe_mean
    else:
        reference_pass = None

    decision_coverage_complete = decision_count == 768 and missing_count == 0 and duplicate_count == 0
    easy_fraction = (
        Fraction(easy_serve_count, easy_eligible_count)
        if easy_eligible_count > 0
        else None
    )
    easy_pass = (
        easy_eligible_count > 0 and easy_fraction >= Fraction(4, 5)
        if decision_coverage_complete
        else None
    )
    oracle_pass = (
        all(oracle_counts[action] > 0 for action in _SCIENTIFIC_ACTIONS)
        if decision_coverage_complete
        else None
    )
    nonconstant_pass = (
        sum(count > 0 for count in selected_counts.values()) >= 2
        if decision_coverage_complete
        else None
    )
    if missing_count or duplicate_count or nonfinite_count:
        integrity_pass: bool | None = None
        raw_competence_pass: bool | None = None
    else:
        integrity_pass = mask_violation_count == 0
        raw_competence_pass = all(
            component is True
            for component in (
                reference_pass,
                easy_pass,
                oracle_pass,
                nonconstant_pass,
                integrity_pass,
            )
        )

    return {
        "schema": RAW_COMPETENCE_SCHEMA,
        "seed": seed,
        "raw_competence_pass": raw_competence_pass,
        "components": {
            "reference_return_pass": reference_pass,
            "easy_open_pass": easy_pass,
            "oracle_support_pass": oracle_pass,
            "nonconstant_action_pass": nonconstant_pass,
            "record_integrity_pass": integrity_pass,
        },
        "inputs": {
            "checkpoint_update": 48,
            "split": "EVAL_STOCHASTIC",
            "tape_ids": sorted(tape_counts.elements()),
            "decision_count": decision_count,
            "raw_per_tape_returns": [_ratio_record(value) for value in raw_returns],
            "always_refresh_per_tape_returns": [
                _ratio_record(value) for value in refresh_returns
            ],
            "always_safe_per_tape_returns": [_ratio_record(value) for value in safe_returns],
            "raw_mean_return": _ratio_record(raw_mean) if raw_mean is not None else None,
            "always_refresh_mean_return": (
                _ratio_record(refresh_mean) if refresh_mean is not None else None
            ),
            "always_safe_mean_return": (
                _ratio_record(safe_mean) if safe_mean is not None else None
            ),
            "easy_open_eligible_count": easy_eligible_count,
            "easy_open_serve_count": easy_serve_count,
            "easy_open_serve_fraction": (
                _ratio_record(easy_fraction) if easy_fraction is not None else None
            ),
            "oracle_action_counts": {
                action: oracle_counts[action] for action in _SCIENTIFIC_ACTIONS
            },
            "raw_action_counts": {
                action: selected_counts[action] for action in _SCIENTIFIC_ACTIONS
            },
            "mask_violation_count": mask_violation_count,
            "nonfinite_count": nonfinite_count,
            "missing_record_count": missing_count,
            "duplicate_record_count": duplicate_count,
            "terminal_stochastic_records": deepcopy(raw["tapes"]),
        },
    }


def _named_records(facts: Mapping[str, Any], name: str, fields: set[str]) -> list[Mapping[str, Any]]:
    rows = _records(facts[name], name)
    for row in rows:
        if set(row) != fields:
            raise B1MechanicalError(f"{name} fields differ")
    return rows


def _compute_mechanical_components(facts: Mapping[str, Any]) -> dict[str, bool | None]:
    inventories = _named_records(
        facts, "inventories", {"name", "expected_keys", "observed_keys"}
    )
    inventory_pass = True
    for row in inventories:
        expected, observed = row["expected_keys"], row["observed_keys"]
        if not isinstance(expected, list) or not isinstance(observed, list):
            raise B1MechanicalError("inventory keys must be lists")
        inventory_pass = inventory_pass and len(expected) == len(set(expected))
        inventory_pass = inventory_pass and len(observed) == len(set(observed))
        inventory_pass = inventory_pass and set(expected) == set(observed)

    resources = _named_records(
        facts,
        "resources",
        {
            "invocation_id",
            "physical_available_bytes",
            "effective_available_bytes",
            "wall_seconds",
            "peak_rss_bytes",
            "scratch_peak_bytes",
            "durable_peak_bytes",
        },
    )
    admission_pass = True
    resource_cap_pass = True
    for row in resources:
        physical = _integer(row["physical_available_bytes"], "physical available bytes")
        effective = _integer(row["effective_available_bytes"], "effective available bytes")
        admission_pass = admission_pass and physical >= 4 * _GIB and effective >= 4 * _GIB
        for field, cap in (("wall_seconds", 7200), ("peak_rss_bytes", 4 * _GIB),
                           ("scratch_peak_bytes", 2 * _GIB), ("durable_peak_bytes", 512 * _MIB)):
            measured = row[field]
            if measured is None:
                if resource_cap_pass is True:
                    resource_cap_pass = None
            elif _number(measured, field) > cap:
                resource_cap_pass = False

    digest_rows = _named_records(
        facts,
        "digest_bindings",
        {"name", "expected_sha256", "observed_sha256"},
    )
    digest_pass = all(
        _digest(row["expected_sha256"], "expected digest")
        == _digest(row["observed_sha256"], "observed digest")
        for row in digest_rows
    )
    tape_rows = _named_records(
        facts, "tape_bindings", {"name", "expected_sha256", "observed_sha256"}
    )
    tape_pass = all(
        _digest(row["expected_sha256"], "expected tape digest")
        == _digest(row["observed_sha256"], "observed tape digest")
        for row in tape_rows
    )
    work_rows = _named_records(
        facts, "work_bindings", {"name", "expected_count", "observed_count"}
    )
    work_pass = all(
        _integer(row["expected_count"], "expected work count")
        == _integer(row["observed_count"], "observed work count")
        for row in work_rows
    )

    fp32_rows = _named_records(
        facts, "fp32_records", {"name", "dtype", "fp32_bits", "active_modes"}
    )
    fp32_pass = True
    for row in fp32_rows:
        formed, finite = _fp32_bits(row["fp32_bits"])
        modes = row["active_modes"]
        if not isinstance(modes, list):
            raise B1MechanicalError("FP32 active modes must be a list")
        fp32_pass = fp32_pass and row["dtype"] == "float32" and not modes and formed and finite

    numeric_rows = _named_records(facts, "numeric_records", {"name", "value"})
    finite_pass = all(
        type(row["value"]) in (int, float) and math.isfinite(row["value"])
        for row in numeric_rows
    )

    reset_rows = _named_records(
        facts,
        "reset_records",
        {"name", "expected_fp32_bits", "observed_fp32_bits"},
    )
    reset_pass = True
    for row in reset_rows:
        expected, observed = row["expected_fp32_bits"], row["observed_fp32_bits"]
        if not isinstance(expected, list) or not isinstance(observed, list):
            raise B1MechanicalError("reset FP32 records must be lists")
        reset_pass = reset_pass and bool(expected) and all(word == "00000000" for word in expected)
        reset_pass = reset_pass and expected == observed
        reset_pass = reset_pass and all(_fp32_bits(word) == (True, True) for word in observed)

    adaptation_rows = _named_records(
        facts,
        "adaptation_records",
        {
            "name",
            "model_sha256_before",
            "model_sha256_after",
            "optimizer_sha256_before",
            "optimizer_sha256_after",
        },
    )
    adaptation_pass = all(
        _digest(row["model_sha256_before"], "model digest before")
        == _digest(row["model_sha256_after"], "model digest after")
        and _digest(row["optimizer_sha256_before"], "optimizer digest before")
        == _digest(row["optimizer_sha256_after"], "optimizer digest after")
        for row in adaptation_rows
    )

    checkpoint_rows = _named_records(
        facts,
        "checkpoint_records",
        {
            "name",
            "saved_sha256",
            "loaded_sha256",
            "expected_parameter_sha256",
            "restored_parameter_sha256",
        },
    )
    checkpoint_pass = all(
        _digest(row["saved_sha256"], "saved checkpoint digest")
        == _digest(row["loaded_sha256"], "loaded checkpoint digest")
        and _digest(row["expected_parameter_sha256"], "expected parameter digest")
        == _digest(row["restored_parameter_sha256"], "restored parameter digest")
        for row in checkpoint_rows
    )

    visibility_rows = _named_records(
        facts,
        "learner_visibility_records",
        {"name", "visible_fields", "allowed_fields"},
    )
    leakage_pass = True
    for row in visibility_rows:
        visible, allowed = row["visible_fields"], row["allowed_fields"]
        if not isinstance(visible, list) or not isinstance(allowed, list):
            raise B1MechanicalError("learner visibility fields must be lists")
        leakage_pass = leakage_pass and len(visible) == len(set(visible))
        leakage_pass = leakage_pass and set(visible) <= set(allowed)

    legal_rows = _named_records(
        facts,
        "legal_action_records",
        {"name", "selected_action_index", "legal_action_mask"},
    )
    legal_pass = True
    for row in legal_rows:
        action = row["selected_action_index"]
        mask = row["legal_action_mask"]
        if type(action) is not int or not isinstance(mask, list) or len(mask) != 4 or any(
            type(value) is not bool for value in mask
        ):
            raise B1MechanicalError("legal action record differs")
        legal_pass = legal_pass and tuple(mask) == _DECISION_MASK and 0 <= action < 4 and mask[action]

    twin_rows = _named_records(
        facts, "twin_records", {"pair_id", "expected_members", "observed_members"}
    )
    twin_pass = True
    for row in twin_rows:
        expected, observed = row["expected_members"], row["observed_members"]
        if not isinstance(expected, list) or not isinstance(observed, list):
            raise B1MechanicalError("twin members must be lists")
        twin_pass = twin_pass and len(expected) == len(set(expected))
        twin_pass = twin_pass and len(observed) == len(set(observed))
        twin_pass = twin_pass and set(expected) == set(observed)

    literal_rows = _named_records(
        facts, "literal_records", {"audit_code", "expected", "observed"}
    )
    literal_pass = all(
        type(row["expected"]) is not bool
        and type(row["observed"]) is not bool
        and row["expected"] == row["observed"]
        for row in literal_rows
    )

    return {
        "inventory": inventory_pass,
        "resource_admission": admission_pass,
        "resource_caps": resource_cap_pass,
        "publication_digests": digest_pass,
        "tape": tape_pass,
        "work": work_pass,
        "fp32": fp32_pass,
        "finite": finite_pass,
        "recurrent_reset": reset_pass,
        "adaptation_free_evaluation": adaptation_pass,
        "checkpoint_roundtrip": checkpoint_pass,
        "learner_leakage": leakage_pass,
        "legal_actions": legal_pass,
        "twins": twin_pass,
        "literal_laws": literal_pass,
    }


def _missing_competence(seed: int, *, duplicates: int = 0) -> dict[str, Any]:
    return {
        "schema": RAW_COMPETENCE_SCHEMA,
        "seed": seed,
        "raw_competence_pass": None,
        "components": {
            "reference_return_pass": None,
            "easy_open_pass": None,
            "oracle_support_pass": None,
            "nonconstant_action_pass": None,
            "record_integrity_pass": None,
        },
        "inputs": {
            "checkpoint_update": 48,
            "split": "EVAL_STOCHASTIC",
            "tape_ids": [],
            "decision_count": 0,
            "raw_per_tape_returns": [],
            "always_refresh_per_tape_returns": [],
            "always_safe_per_tape_returns": [],
            "raw_mean_return": None,
            "always_refresh_mean_return": None,
            "always_safe_mean_return": None,
            "easy_open_eligible_count": 0,
            "easy_open_serve_count": 0,
            "easy_open_serve_fraction": None,
            "oracle_action_counts": {action: 0 for action in _SCIENTIFIC_ACTIONS},
            "raw_action_counts": {action: 0 for action in _SCIENTIFIC_ACTIONS},
            "mask_violation_count": 0,
            "nonfinite_count": 0,
            "missing_record_count": 1,
            "duplicate_record_count": duplicates,
            "terminal_stochastic_records": [],
        },
    }


def compute_b1_mechanical(
    raw_facts: Mapping[str, Any],
    raw_competence_inputs: Sequence[Mapping[str, Any]],
    *,
    input_descriptor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Recompute B1 mechanical fields and all three nonpolar RAW gates."""

    facts = _exact_fields(raw_facts, _FACT_FIELDS, "mechanical fact")
    if not isinstance(raw_competence_inputs, Sequence) or isinstance(
        raw_competence_inputs, (str, bytes, bytearray)
    ):
        raise B1MechanicalError("RAW competence inputs must be a sequence")
    descriptor = (
        build_mechanical_input_descriptor(
            facts,
            raw_competence_inputs,
            authority="TEST_ARGUMENTS_ONLY",
            test_only=True,
            training_slot_indices=(),
            raw_worker_sources=(),
            policy_execution_mode_sources=(),
            table_bindings=(),
            artifact_inventory_sha256=None,
        )
        if input_descriptor is None
        else _validate_mechanical_input_descriptor(
            input_descriptor,
            raw_facts=facts,
            raw_competence_inputs=raw_competence_inputs,
        )
    )
    components = _compute_mechanical_components(facts)

    by_seed: dict[int, list[Mapping[str, Any]]] = {seed: [] for seed in B1_SEEDS}
    for record in raw_competence_inputs:
        if not isinstance(record, Mapping):
            raise B1MechanicalError("RAW competence input is not a record")
        seed = record.get("seed")
        if type(seed) is not int or seed not in by_seed:
            raise B1MechanicalError("RAW competence input seed differs")
        by_seed[seed].append(record)
    competence: list[dict[str, Any]] = []
    for seed in B1_SEEDS:
        records = by_seed[seed]
        if len(records) != 1:
            competence.append(_missing_competence(seed, duplicates=max(0, len(records) - 1)))
        else:
            competence.append(compute_raw_competence(records[0]))

    codes: list[str] = []
    component_codes = {
        "inventory": "MISSING_OR_DUPLICATE_INVENTORY",
        "resource_admission": "RESOURCE_ADMISSION_FAILURE",
        "resource_caps": "RESOURCE_CAP_BREACH",
        "publication_digests": "PUBLICATION_DIGEST_FAILURE",
        "tape": "TAPE_CONFORMANCE_FAILURE",
        "work": "UNEQUAL_WORK_EXPOSURE",
        "fp32": "FP32_CONFORMANCE_FAILURE",
        "finite": "NONFINITE_VALUE",
        "recurrent_reset": "RECURRENT_RESET_FAILURE",
        "adaptation_free_evaluation": "EVALUATION_ADAPTATION_FAILURE",
        "checkpoint_roundtrip": "CHECKPOINT_ROUNDTRIP_FAILURE",
        "learner_leakage": "LEARNER_LEAKAGE",
        "legal_actions": "ILLEGAL_ACTION",
        "twins": "INCOMPLETE_TWIN",
        "literal_laws": "LITERAL_CONFORMANCE_FAILURE",
    }
    codes.extend(code for name, code in component_codes.items()
                 if name != "resource_caps" and not components[name])
    competence_values = [row["raw_competence_pass"] for row in competence]
    if any(value is False for value in competence_values):
        codes.append("RAW_COMPETENCE_FAILURE")
    if any(value is None for value in competence_values):
        codes.append("RAW_COMPETENCE_UNESTABLISHED")
    codes = [code for code in _BLOCKING_ORDER if code in codes]

    competence_integrity = all(
        row["components"]["record_integrity_pass"] is not None for row in competence
    )
    attempt_complete = (
        components["inventory"]
        and components["resource_admission"]
        and components["publication_digests"]
        and components["finite"]
        and competence_integrity
    )
    packet_readable = (
        components["inventory"]
        and components["publication_digests"]
        and components["finite"]
        and competence_integrity
    )
    mechanical_conformance = attempt_complete and all(
        value for name, value in components.items() if name != "resource_caps"
    )
    return {
        "schema": B1_MECHANICAL_SCHEMA,
        "mechanical_attempt_complete": attempt_complete,
        "mechanical_conformance_pass": mechanical_conformance,
        "scientific_packet_readable": packet_readable,
        "blocking_audit_codes": codes,
        "mechanical_components": components,
        "raw_competence_by_seed": competence,
        "inputs": descriptor,
    }


def b0_nonpolarity_record() -> dict[str, Any]:
    """Return the absolute B0 exclusion record fixed by clarification ``.03``."""

    return {
        "schema": B0_NONPOLARITY_SCHEMA,
        "b0_nonpolarity": "ABSOLUTE",
        "scientific_eligible": False,
        "classifier_eligible": False,
        "threshold_tuning_eligible": False,
        "b2_trigger_eligible": False,
        "promotion_eligible": False,
    }


__all__ = [
    "B0_NONPOLARITY_SCHEMA",
    "B1_MECHANICAL_SCHEMA",
    "B1MechanicalError",
    "MECHANICAL_INPUT_DESCRIPTOR_SCHEMA",
    "RAW_COMPETENCE_SCHEMA",
    "b0_nonpolarity_record",
    "build_mechanical_input_descriptor",
    "compute_b1_mechanical",
    "compute_raw_competence",
]
