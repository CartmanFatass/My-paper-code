#!/usr/bin/env python3
"""Generate and validate deterministic HMASD mechanism artifacts.

This bounded local implementation is substantially adapted from the object
separation, rival-prediction, falsification, and non-scoring validation patterns
in K-Dense-AI/scientific-agent-skills at commit
f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f, specifically:

* skills/hypothesis-generation/SKILL.md
* skills/hypothesis-generation/assets/hypothesis_record_template.json
* skills/hypothesis-generation/scripts/validate_hypothesis_schema.py
* skills/hypothesis-generation/assets/falsification_controls_template.json
* skills/hypothesis-generation/scripts/check_falsification_controls.py

MIT License

Copyright (c) 2025 K-Dense Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

ARTIFACT_SCHEMA_VERSION = 1
RESULT_SCHEMA_VERSION = 1
TOOL_NAME = "hypothesis_mechanisms"
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

TOP_LEVEL_FIELDS = {
    "schema_version",
    "artifact_id",
    "assignment_id",
    "gap_id",
    "task_family",
    "insight_status",
    "claim",
    "evidence_status",
    "evidence_references",
    "assumptions",
    "falsifier_or_counterexample",
    "uncertainty_limitations",
    "consequence_decision_relevance",
    "recommendation",
    "mechanism_cards",
    "no_material_insight",
    "scientific_authority",
    "scientific_status_effect",
    "lifecycle_status_effect",
}
CARD_FIELDS = {
    "card_id",
    "candidate_statement",
    "mechanism_family",
    "mechanism_statement",
    "assumptions",
    "boundary_conditions",
    "predictions",
    "rival_mechanisms",
    "discriminators",
    "falsifiers",
    "uncertainty_limitations",
    "admissible_packet_ids",
}
ASSUMPTION_FIELDS = {"assumption_id", "statement"}
PREDICTION_FIELDS = {
    "prediction_id",
    "statement",
    "observable",
    "conditions",
    "expected_pattern",
    "uncertainty",
    "falsifier_ids",
    "rival_mechanism_ids",
    "discriminator_ids",
}
RIVAL_FIELDS = {
    "rival_mechanism_id",
    "family",
    "statement",
    "contrast",
}
DISCRIMINATOR_FIELDS = {
    "discriminator_id",
    "statement",
    "prediction_ids",
    "rival_mechanism_ids",
    "indeterminate_outcome",
    "controls",
}
CONTROL_FIELDS = {"control_type", "statement"}
FALSIFIER_FIELDS = {
    "falsifier_id",
    "statement",
    "assumption_ids",
    "consequence",
}
REFERENCE_FIELDS = {"reference_id", "locator"}
NO_INSIGHT_FIELDS = {
    "sources_inspected",
    "methods_attempted",
    "why_no_material_insight",
    "residual_uncertainty",
}

Issue = dict[str, str]


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _content_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16].upper()}"


def generate_artifact(draft: Any) -> dict[str, Any]:
    """Materialize deterministic artifact and card IDs without adding content.

    The caller supplies every scientific declaration and relationship. This
    function only copies the JSON object, fixes the schema version, and replaces
    content-addressed IDs. Validation remains a separate structural operation.
    """

    if not isinstance(draft, Mapping):
        raise TypeError("generation input must be a JSON object")
    artifact = copy.deepcopy(dict(draft))
    artifact["schema_version"] = ARTIFACT_SCHEMA_VERSION
    artifact.pop("artifact_id", None)

    cards = artifact.get("mechanism_cards")
    if isinstance(cards, list):
        for card in cards:
            if isinstance(card, dict):
                card.pop("card_id", None)
                card["card_id"] = _content_id("HMC", card)

    artifact["artifact_id"] = _content_id("HMA", artifact)
    return artifact


def _issue(issues: list[Issue], path: str, code: str, message: str) -> None:
    issues.append({"path": path, "code": code, "message": message})


def _object(
    value: Any,
    path: str,
    issues: list[Issue],
    fields: set[str] | None = None,
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        _issue(issues, path, "type", "must be an object")
        return None
    if fields is not None:
        missing = sorted(fields - set(value))
        extra = sorted(set(value) - fields)
        for field in missing:
            _issue(issues, f"{path}.{field}", "required", "field is required")
        for field in extra:
            _issue(issues, f"{path}.{field}", "unknown", "field is not allowed")
    return value


def _text(value: Any, path: str, issues: list[Issue]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        _issue(issues, path, "text", "must be a non-empty string")
        return None
    return value


def _identifier(value: Any, path: str, issues: list[Issue]) -> str | None:
    text = _text(value, path, issues)
    if text is not None and IDENTIFIER.fullmatch(text) is None:
        _issue(issues, path, "identifier", "must be a bounded identifier")
        return None
    return text


def _list(value: Any, path: str, issues: list[Issue]) -> list[Any] | None:
    if not isinstance(value, list):
        _issue(issues, path, "type", "must be an array")
        return None
    return value


def _nonempty_list(value: Any, path: str, issues: list[Issue]) -> list[Any] | None:
    entries = _list(value, path, issues)
    if entries is not None and not entries:
        _issue(issues, path, "minimum", "must contain at least one item")
    return entries


def _text_list(
    value: Any,
    path: str,
    issues: list[Issue],
    *,
    nonempty: bool = True,
    identifiers: bool = False,
) -> list[str] | None:
    entries = (
        _nonempty_list(value, path, issues)
        if nonempty
        else _list(value, path, issues)
    )
    if entries is None:
        return None
    parsed: list[str] = []
    for index, entry in enumerate(entries):
        item_path = f"{path}[{index}]"
        item = (
            _identifier(entry, item_path, issues)
            if identifiers
            else _text(entry, item_path, issues)
        )
        if item is not None:
            parsed.append(item)
    if len(parsed) != len(set(parsed)):
        _issue(issues, path, "duplicate", "items must be unique")
    return parsed


def _record_ids(
    entries: list[Any] | None,
    path: str,
    id_field: str,
    fields: set[str],
    issues: list[Issue],
) -> tuple[list[dict[str, Any]], set[str]]:
    records: list[dict[str, Any]] = []
    identifiers: list[str] = []
    if entries is None:
        return records, set()
    for index, value in enumerate(entries):
        record_path = f"{path}[{index}]"
        record = _object(value, record_path, issues, fields)
        if record is None:
            continue
        records.append(record)
        identifier = _identifier(record.get(id_field), f"{record_path}.{id_field}", issues)
        if identifier is not None:
            identifiers.append(identifier)
    if len(identifiers) != len(set(identifiers)):
        _issue(issues, path, "duplicate_id", f"{id_field} values must be unique")
    return records, set(identifiers)


def _check_references(
    identifiers: list[str] | None,
    declared: set[str],
    path: str,
    issues: list[Issue],
) -> None:
    if identifiers is None:
        return
    for identifier in identifiers:
        if identifier not in declared:
            _issue(
                issues,
                path,
                "unknown_reference",
                f"{identifier!r} is not declared in this mechanism card",
            )


def _validate_references(value: Any, path: str, issues: list[Issue]) -> list[dict[str, Any]]:
    entries = _list(value, path, issues)
    records: list[dict[str, Any]] = []
    if entries is None:
        return records
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(entries):
        item_path = f"{path}[{index}]"
        record = _object(raw, item_path, issues, REFERENCE_FIELDS)
        if record is None:
            continue
        reference_id = _identifier(
            record.get("reference_id"), f"{item_path}.reference_id", issues
        )
        locator = _text(record.get("locator"), f"{item_path}.locator", issues)
        if reference_id is not None and locator is not None:
            key = (reference_id, locator)
            if key in seen:
                _issue(issues, item_path, "duplicate", "reference and locator must be unique")
            seen.add(key)
        records.append(record)
    return records


def _validate_card(card: dict[str, Any], path: str, issues: list[Issue]) -> None:
    _text(card.get("candidate_statement"), f"{path}.candidate_statement", issues)
    _text(card.get("mechanism_family"), f"{path}.mechanism_family", issues)
    _text(card.get("mechanism_statement"), f"{path}.mechanism_statement", issues)
    _text_list(card.get("boundary_conditions"), f"{path}.boundary_conditions", issues)
    _text_list(
        card.get("uncertainty_limitations"),
        f"{path}.uncertainty_limitations",
        issues,
    )
    _text_list(
        card.get("admissible_packet_ids"),
        f"{path}.admissible_packet_ids",
        issues,
        nonempty=False,
        identifiers=True,
    )

    assumptions, assumption_ids = _record_ids(
        _nonempty_list(card.get("assumptions"), f"{path}.assumptions", issues),
        f"{path}.assumptions",
        "assumption_id",
        ASSUMPTION_FIELDS,
        issues,
    )
    for index, assumption in enumerate(assumptions):
        _text(assumption.get("statement"), f"{path}.assumptions[{index}].statement", issues)

    rivals, rival_ids = _record_ids(
        _nonempty_list(
            card.get("rival_mechanisms"), f"{path}.rival_mechanisms", issues
        ),
        f"{path}.rival_mechanisms",
        "rival_mechanism_id",
        RIVAL_FIELDS,
        issues,
    )
    for index, rival in enumerate(rivals):
        rival_path = f"{path}.rival_mechanisms[{index}]"
        for field in ("family", "statement", "contrast"):
            _text(rival.get(field), f"{rival_path}.{field}", issues)

    falsifiers, falsifier_ids = _record_ids(
        _nonempty_list(card.get("falsifiers"), f"{path}.falsifiers", issues),
        f"{path}.falsifiers",
        "falsifier_id",
        FALSIFIER_FIELDS,
        issues,
    )
    for index, falsifier in enumerate(falsifiers):
        falsifier_path = f"{path}.falsifiers[{index}]"
        _text(falsifier.get("statement"), f"{falsifier_path}.statement", issues)
        assumption_refs = _text_list(
            falsifier.get("assumption_ids"),
            f"{falsifier_path}.assumption_ids",
            issues,
            identifiers=True,
        )
        _check_references(
            assumption_refs,
            assumption_ids,
            f"{falsifier_path}.assumption_ids",
            issues,
        )
        _text(falsifier.get("consequence"), f"{falsifier_path}.consequence", issues)

    predictions, prediction_ids = _record_ids(
        _nonempty_list(card.get("predictions"), f"{path}.predictions", issues),
        f"{path}.predictions",
        "prediction_id",
        PREDICTION_FIELDS,
        issues,
    )
    discriminators, discriminator_ids = _record_ids(
        _nonempty_list(
            card.get("discriminators"), f"{path}.discriminators", issues
        ),
        f"{path}.discriminators",
        "discriminator_id",
        DISCRIMINATOR_FIELDS,
        issues,
    )

    referenced_rivals: set[str] = set()
    referenced_falsifiers: set[str] = set()
    for index, prediction in enumerate(predictions):
        prediction_path = f"{path}.predictions[{index}]"
        for field in (
            "statement",
            "observable",
            "conditions",
            "expected_pattern",
            "uncertainty",
        ):
            _text(prediction.get(field), f"{prediction_path}.{field}", issues)
        falsifier_refs = _text_list(
            prediction.get("falsifier_ids"),
            f"{prediction_path}.falsifier_ids",
            issues,
            identifiers=True,
        )
        rival_refs = _text_list(
            prediction.get("rival_mechanism_ids"),
            f"{prediction_path}.rival_mechanism_ids",
            issues,
            identifiers=True,
        )
        discriminator_refs = _text_list(
            prediction.get("discriminator_ids"),
            f"{prediction_path}.discriminator_ids",
            issues,
            identifiers=True,
        )
        _check_references(
            falsifier_refs,
            falsifier_ids,
            f"{prediction_path}.falsifier_ids",
            issues,
        )
        _check_references(
            rival_refs,
            rival_ids,
            f"{prediction_path}.rival_mechanism_ids",
            issues,
        )
        _check_references(
            discriminator_refs,
            discriminator_ids,
            f"{prediction_path}.discriminator_ids",
            issues,
        )
        referenced_falsifiers.update(falsifier_refs or [])
        referenced_rivals.update(rival_refs or [])

    for index, discriminator in enumerate(discriminators):
        discriminator_path = f"{path}.discriminators[{index}]"
        _text(discriminator.get("statement"), f"{discriminator_path}.statement", issues)
        prediction_refs = _text_list(
            discriminator.get("prediction_ids"),
            f"{discriminator_path}.prediction_ids",
            issues,
            identifiers=True,
        )
        rival_refs = _text_list(
            discriminator.get("rival_mechanism_ids"),
            f"{discriminator_path}.rival_mechanism_ids",
            issues,
            identifiers=True,
        )
        _check_references(
            prediction_refs,
            prediction_ids,
            f"{discriminator_path}.prediction_ids",
            issues,
        )
        _check_references(
            rival_refs,
            rival_ids,
            f"{discriminator_path}.rival_mechanism_ids",
            issues,
        )
        referenced_rivals.update(rival_refs or [])
        _text(
            discriminator.get("indeterminate_outcome"),
            f"{discriminator_path}.indeterminate_outcome",
            issues,
        )
        controls = _nonempty_list(
            discriminator.get("controls"), f"{discriminator_path}.controls", issues
        )
        if controls is not None:
            for control_index, raw_control in enumerate(controls):
                control_path = f"{discriminator_path}.controls[{control_index}]"
                control = _object(raw_control, control_path, issues, CONTROL_FIELDS)
                if control is not None:
                    _text(control.get("control_type"), f"{control_path}.control_type", issues)
                    _text(control.get("statement"), f"{control_path}.statement", issues)

    for rival_id in sorted(rival_ids - referenced_rivals):
        _issue(
            issues,
            f"{path}.rival_mechanisms",
            "unlinked_rival",
            f"rival {rival_id!r} must be linked by a prediction or discriminator",
        )
    for falsifier_id in sorted(falsifier_ids - referenced_falsifiers):
        _issue(
            issues,
            f"{path}.falsifiers",
            "unlinked_falsifier",
            f"falsifier {falsifier_id!r} must be linked by a prediction",
        )


def validate_artifact(artifact: Any) -> list[Issue]:
    """Return deterministic structural/internal-consistency issues.

    An empty issue list means only that declarations are structurally coherent.
    It is not evidence, hypothesis selection, scientific approval, or a lifecycle
    transition.
    """

    issues: list[Issue] = []
    record = _object(artifact, "$", issues, TOP_LEVEL_FIELDS)
    if record is None:
        return issues

    if record.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        _issue(issues, "$.schema_version", "constant", "must equal 1")
    _identifier(record.get("artifact_id"), "$.artifact_id", issues)
    _identifier(record.get("assignment_id"), "$.assignment_id", issues)
    _identifier(record.get("gap_id"), "$.gap_id", issues)
    _identifier(record.get("task_family"), "$.task_family", issues)
    _text(record.get("claim"), "$.claim", issues)

    insight_status = record.get("insight_status")
    if insight_status not in {"MATERIAL_INSIGHT", "NO_MATERIAL_INSIGHT"}:
        _issue(
            issues,
            "$.insight_status",
            "enum",
            "must be MATERIAL_INSIGHT or NO_MATERIAL_INSIGHT",
        )

    evidence_status = record.get("evidence_status")
    if evidence_status not in {"reported", "not_reported"}:
        _issue(
            issues,
            "$.evidence_status",
            "enum",
            "must be reported or not_reported",
        )
    evidence_references = _validate_references(
        record.get("evidence_references"), "$.evidence_references", issues
    )
    if evidence_status == "reported" and not evidence_references:
        _issue(
            issues,
            "$.evidence_references",
            "minimum",
            "reported evidence requires at least one exact reference and locator",
        )
    if evidence_status == "not_reported" and evidence_references:
        _issue(
            issues,
            "$.evidence_references",
            "inconsistent",
            "not_reported evidence must have an empty reference list",
        )

    _text_list(record.get("assumptions"), "$.assumptions", issues)
    _text(record.get("falsifier_or_counterexample"), "$.falsifier_or_counterexample", issues)
    _text_list(
        record.get("uncertainty_limitations"), "$.uncertainty_limitations", issues
    )
    _text(
        record.get("consequence_decision_relevance"),
        "$.consequence_decision_relevance",
        issues,
    )
    _text(record.get("recommendation"), "$.recommendation", issues)

    cards = _list(record.get("mechanism_cards"), "$.mechanism_cards", issues)
    if cards is not None:
        card_ids: list[str] = []
        for index, raw_card in enumerate(cards):
            card_path = f"$.mechanism_cards[{index}]"
            card = _object(raw_card, card_path, issues, CARD_FIELDS)
            if card is None:
                continue
            card_id = _identifier(card.get("card_id"), f"{card_path}.card_id", issues)
            if card_id is not None:
                card_ids.append(card_id)
            expected_card_id = _content_id(
                "HMC", {key: value for key, value in card.items() if key != "card_id"}
            )
            if card.get("card_id") != expected_card_id:
                _issue(
                    issues,
                    f"{card_path}.card_id",
                    "content_id",
                    f"must equal deterministic content identifier {expected_card_id}",
                )
            _validate_card(card, card_path, issues)
        if len(card_ids) != len(set(card_ids)):
            _issue(issues, "$.mechanism_cards", "duplicate_id", "card IDs must be unique")

    no_insight = record.get("no_material_insight")
    if insight_status == "MATERIAL_INSIGHT":
        if no_insight is not None:
            _issue(
                issues,
                "$.no_material_insight",
                "inconsistent",
                "must be null for MATERIAL_INSIGHT",
            )
    elif insight_status == "NO_MATERIAL_INSIGHT":
        details = _object(no_insight, "$.no_material_insight", issues, NO_INSIGHT_FIELDS)
        if details is not None:
            _validate_references(
                details.get("sources_inspected"),
                "$.no_material_insight.sources_inspected",
                issues,
            )
            sources = details.get("sources_inspected")
            if isinstance(sources, list) and not sources:
                _issue(
                    issues,
                    "$.no_material_insight.sources_inspected",
                    "minimum",
                    "must record at least one inspected source",
                )
            _text_list(
                details.get("methods_attempted"),
                "$.no_material_insight.methods_attempted",
                issues,
            )
            _text(
                details.get("why_no_material_insight"),
                "$.no_material_insight.why_no_material_insight",
                issues,
            )
            _text(
                details.get("residual_uncertainty"),
                "$.no_material_insight.residual_uncertainty",
                issues,
            )

    if record.get("scientific_authority") != "EM":
        _issue(issues, "$.scientific_authority", "constant", "must remain EM")
    if record.get("scientific_status_effect") != "NONE":
        _issue(
            issues,
            "$.scientific_status_effect",
            "constant",
            "validator and generator have no scientific status effect",
        )
    if record.get("lifecycle_status_effect") != "NONE":
        _issue(
            issues,
            "$.lifecycle_status_effect",
            "constant",
            "validator and generator have no lifecycle status effect",
        )

    if isinstance(record.get("artifact_id"), str):
        expected_artifact_id = _content_id(
            "HMA", {key: value for key, value in record.items() if key != "artifact_id"}
        )
        if record["artifact_id"] != expected_artifact_id:
            _issue(
                issues,
                "$.artifact_id",
                "content_id",
                f"must equal deterministic content identifier {expected_artifact_id}",
            )

    return issues


def result_envelope(
    operation: str,
    issues: Sequence[Issue],
    *,
    artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the local v1 machine-readable tool result envelope."""

    valid = not issues
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "operation": operation,
        "technical_status": "SUCCEEDED" if valid else "VALIDATION_FAILED",
        "valid": valid,
        "issues": list(issues),
        "scientific_status_effect": "NONE",
        "lifecycle_status_effect": "NONE",
        "scientific_authority": "EM",
    }
    if artifact is not None:
        result["artifact"] = artifact
    return result


def _malformed_envelope(operation: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "operation": operation,
        "technical_status": "MALFORMED_INPUT",
        "valid": False,
        "issues": [{"path": "$", "code": "malformed_input", "message": message}],
        "scientific_status_effect": "NONE",
        "lifecycle_status_effect": "NONE",
        "scientific_authority": "EM",
    }


def _load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _emit(result: Mapping[str, Any], output: str | None) -> None:
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is None or output == "-":
        sys.stdout.write(text)
        return
    Path(output).write_text(text, encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate or validate deterministic local mechanism artifacts. "
            "Structural success is not scientific approval."
        )
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in ("generate", "validate"):
        command = subparsers.add_parser(operation)
        command.add_argument("input", help="JSON path, or - for stdin")
        command.add_argument("-o", "--output", help="result path; default stdout")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = _load_json(args.input)
        if args.operation == "generate":
            artifact = generate_artifact(payload)
            result = result_envelope("generate", validate_artifact(artifact), artifact=artifact)
        else:
            result = result_envelope("validate", validate_artifact(payload))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        result = _malformed_envelope(args.operation, str(error))
        _emit(result, args.output)
        return 2

    _emit(result, args.output)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
