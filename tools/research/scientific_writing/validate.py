#!/usr/bin/env python3
"""Offline, fail-closed scientific-writing record validators.

Adapted from K-Dense-AI/scientific-agent-skills at commit
f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f, specifically:
  skills/scientific-writing/scripts/_common.py
  skills/scientific-writing/scripts/validate_manifest.py
  skills/scientific-writing/scripts/audit_claims.py
  skills/scientific-writing/scripts/check_consistency.py

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
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, TypeGuard

SCHEMA_VERSION = 1
MAX_FILE_BYTES = 5_000_000
MAX_RECORDS = 10_000
MAX_JSON_DEPTH = 50
MAX_JSON_NODES = 100_000

EVIDENCE_ID_RE = re.compile(r"^E[0-9]{3,8}$")
CLAIM_ID_RE = re.compile(r"^C[0-9]{3,8}$")
FACT_ID_RE = re.compile(r"^N[0-9]{3,8}$")
METHOD_ID_RE = re.compile(r"^M[0-9]{3,8}$")
OUTCOME_ID_RE = re.compile(r"^O[0-9]{3,8}$")
RESULT_ID_RE = re.compile(r"^R[0-9]{3,8}$")
SAFE_RECORD_ID_RE = re.compile(r"^[ECNMOR][0-9]{3,8}$")
OPAQUE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{1,127}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

SOURCE_TYPES = {
    "book",
    "chapter",
    "conference_paper",
    "dataset",
    "guideline",
    "journal_article",
    "other",
    "policy",
    "preprint",
    "registry",
    "report",
    "software",
    "webpage",
}
ANALYSIS_INTENTS = {"confirmatory", "exploratory", "descriptive"}
PROTOCOL_STATUSES = {
    "prespecified",
    "amended_before_analysis",
    "post_hoc",
    "not_applicable",
}


class InputError(ValueError):
    """A local input could not be safely interpreted."""


@dataclass(frozen=True)
class Issue:
    code: str
    locator: str
    record_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        return {
            key: value
            for key, value in asdict(self).items()
            if value is not None
        }


def _issue(code: str, locator: str, record_id: Any = None) -> Issue:
    safe_id = (
        record_id
        if isinstance(record_id, str) and SAFE_RECORD_ID_RE.fullmatch(record_id)
        else None
    )
    return Issue(code=code, locator=locator, record_id=safe_id)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(_: str) -> None:
    raise InputError("non-finite JSON number")


def _count_json_nodes(value: Any, depth: int = 0) -> int:
    if depth > MAX_JSON_DEPTH:
        raise InputError("JSON nesting limit exceeded")
    count = 1
    if isinstance(value, dict):
        for child in value.values():
            count += _count_json_nodes(child, depth + 1)
    elif isinstance(value, list):
        if len(value) > MAX_RECORDS:
            raise InputError("JSON record limit exceeded")
        for child in value:
            count += _count_json_nodes(child, depth + 1)
    if count > MAX_JSON_NODES:
        raise InputError("JSON node limit exceeded")
    return count


def _read_json(path_value: str) -> Any:
    path = Path(path_value)
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".json":
        raise InputError("input must be a regular JSON file")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise InputError("input size limit exceeded")
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InputError("invalid bounded UTF-8 JSON") from exc
    _count_json_nodes(value)
    return value


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError("expected JSON object")
    return value


def _list(value: Any) -> list[Any]:
    if not isinstance(value, list) or len(value) > MAX_RECORDS:
        raise InputError("expected bounded JSON array")
    return value


def _check_fields(
    value: dict[str, Any],
    expected: set[str],
    locator: str,
    issues: list[Issue],
    record_id: Any = None,
) -> None:
    for key in sorted(expected - set(value)):
        issues.append(_issue("MISSING_FIELD", f"{locator}.{key}", record_id))
    for _ in sorted(set(value) - expected):
        issues.append(_issue("UNKNOWN_FIELD", locator, record_id))


def _valid_nonempty(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and bool(value.strip())


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _valid_id(value: Any, pattern: re.Pattern[str]) -> TypeGuard[str]:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return not isinstance(value, float) or math.isfinite(value)


def _positive_int_or_none(value: Any) -> bool:
    return value is None or (
        isinstance(value, int) and not isinstance(value, bool) and value > 0
    )


def _report(tool: str, issues: list[Issue], summary: dict[str, int]) -> int:
    ordered = sorted(
        issues,
        key=lambda item: (item.code, item.locator, item.record_id or ""),
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": tool,
        "ok": not ordered,
        "issues": [item.to_dict() for item in ordered],
        "summary": {"issue_count": len(ordered), **summary},
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0 if not ordered else 1


def _input_error(tool: str) -> int:
    return _report(tool, [_issue("INVALID_INPUT", "$")], {})


def _validate_source_manifest_data(
    data: dict[str, Any],
) -> tuple[list[Issue], dict[str, bool]]:
    issues: list[Issue] = []
    _check_fields(
        data,
        {"schema_version", "artifact_sha256", "declarations", "sources"},
        "$",
        issues,
    )
    if data.get("schema_version") != SCHEMA_VERSION:
        issues.append(_issue("UNSUPPORTED_SCHEMA_VERSION", "$.schema_version"))
    if not _valid_hash(data.get("artifact_sha256")):
        issues.append(_issue("INVALID_ARTIFACT_HASH", "$.artifact_sha256"))
    declarations = _object(data.get("declarations"))
    _check_fields(declarations, {"authorship", "reporting"}, "$.declarations", issues)
    for declaration_name in ("authorship", "reporting"):
        locator = f"$.declarations.{declaration_name}"
        declaration = _object(declarations.get(declaration_name))
        _check_fields(declaration, {"status", "artifact_sha256"}, locator, issues)
        status = declaration.get("status")
        artifact_hash = declaration.get("artifact_sha256")
        if status not in {"recorded", "not_applicable", "unverified"}:
            issues.append(_issue("INVALID_DECLARATION_STATUS", f"{locator}.status"))
        elif status == "unverified":
            issues.append(_issue("DECLARATION_UNVERIFIED", f"{locator}.status"))
        if status == "recorded" and not _valid_hash(artifact_hash):
            issues.append(_issue("INVALID_DECLARATION_HASH", f"{locator}.artifact_sha256"))
        elif status == "not_applicable" and artifact_hash is not None:
            issues.append(_issue("UNEXPECTED_DECLARATION_HASH", f"{locator}.artifact_sha256"))
        elif (
            status == "unverified"
            and artifact_hash is not None
            and not _valid_hash(artifact_hash)
        ):
            issues.append(_issue("INVALID_DECLARATION_HASH", f"{locator}.artifact_sha256"))

    sources = _list(data.get("sources"))
    verification_by_id: dict[str, bool] = {}
    for index, raw_source in enumerate(sources):
        locator = f"$.sources[{index}]"
        source = _object(raw_source)
        evidence_id = source.get("evidence_id")
        _check_fields(
            source,
            {
                "evidence_id",
                "source_type",
                "reference_sha256",
                "locator",
                "verification",
            },
            locator,
            issues,
            evidence_id,
        )
        if not _valid_id(evidence_id, EVIDENCE_ID_RE):
            issues.append(_issue("INVALID_EVIDENCE_ID", f"{locator}.evidence_id"))
            evidence_id = None
        elif evidence_id in verification_by_id:
            issues.append(_issue("DUPLICATE_EVIDENCE_ID", locator, evidence_id))
        if source.get("source_type") not in SOURCE_TYPES:
            issues.append(_issue("INVALID_SOURCE_TYPE", f"{locator}.source_type", evidence_id))
        if not _valid_hash(source.get("reference_sha256")):
            issues.append(_issue("INVALID_REFERENCE_HASH", f"{locator}.reference_sha256", evidence_id))
        if not _valid_nonempty(source.get("locator")):
            issues.append(_issue("MISSING_SOURCE_LOCATOR", f"{locator}.locator", evidence_id))

        verification = _object(source.get("verification"))
        verification_locator = f"{locator}.verification"
        _check_fields(
            verification,
            {"status", "source_opened", "verified_by", "verified_on"},
            verification_locator,
            issues,
            evidence_id,
        )
        status = verification.get("status")
        if status not in {"verified", "unverified", "rejected"}:
            issues.append(_issue("INVALID_VERIFICATION_STATUS", f"{verification_locator}.status", evidence_id))
        if status != "verified":
            issues.append(_issue("SOURCE_UNVERIFIED", f"{verification_locator}.status", evidence_id))
        if verification.get("source_opened") is not True:
            issues.append(_issue("SOURCE_NOT_OPENED", f"{verification_locator}.source_opened", evidence_id))
        if not _valid_nonempty(verification.get("verified_by")):
            issues.append(_issue("MISSING_VERIFIER_DECLARATION", f"{verification_locator}.verified_by", evidence_id))
        if not isinstance(verification.get("verified_on"), str) or DATE_RE.fullmatch(
            verification["verified_on"]
        ) is None:
            issues.append(_issue("INVALID_VERIFICATION_DATE", f"{verification_locator}.verified_on", evidence_id))

        verified = (
            status == "verified"
            and verification.get("source_opened") is True
            and _valid_nonempty(verification.get("verified_by"))
            and isinstance(verification.get("verified_on"), str)
            and DATE_RE.fullmatch(verification["verified_on"]) is not None
        )
        if evidence_id is not None and evidence_id not in verification_by_id:
            verification_by_id[evidence_id] = verified
    return issues, verification_by_id


def validate_source_manifest(path: str) -> tuple[list[Issue], dict[str, int]]:
    data = _object(_read_json(path))
    issues, sources = _validate_source_manifest_data(data)
    return issues, {"source_count": len(sources)}


def audit_claims(claims_path: str, sources_path: str) -> tuple[list[Issue], dict[str, int]]:
    source_data = _object(_read_json(sources_path))
    issues, sources = _validate_source_manifest_data(source_data)

    data = _object(_read_json(claims_path))
    _check_fields(data, {"schema_version", "claims"}, "$", issues)
    if data.get("schema_version") != SCHEMA_VERSION:
        issues.append(_issue("UNSUPPORTED_SCHEMA_VERSION", "$.schema_version"))
    claims = _list(data.get("claims"))
    seen_claim_ids: set[str] = set()
    for index, raw_claim in enumerate(claims):
        locator = f"$.claims[{index}]"
        claim = _object(raw_claim)
        claim_id = claim.get("claim_id")
        _check_fields(
            claim,
            {"claim_id", "claim_sha256", "evidence"},
            locator,
            issues,
            claim_id,
        )
        if not _valid_id(claim_id, CLAIM_ID_RE):
            issues.append(_issue("INVALID_CLAIM_ID", f"{locator}.claim_id"))
            claim_id = None
        elif claim_id in seen_claim_ids:
            issues.append(_issue("DUPLICATE_CLAIM_ID", locator, claim_id))
        else:
            seen_claim_ids.add(claim_id)
        if not _valid_hash(claim.get("claim_sha256")):
            issues.append(_issue("INVALID_CLAIM_HASH", f"{locator}.claim_sha256", claim_id))

        mappings = _list(claim.get("evidence"))
        if not mappings:
            issues.append(_issue("UNSUPPORTED_CLAIM", f"{locator}.evidence", claim_id))
        seen_evidence_ids: set[str] = set()
        for mapping_index, raw_mapping in enumerate(mappings):
            mapping_locator = f"{locator}.evidence[{mapping_index}]"
            mapping = _object(raw_mapping)
            evidence_id = mapping.get("evidence_id")
            _check_fields(
                mapping,
                {"evidence_id", "locator"},
                mapping_locator,
                issues,
                claim_id,
            )
            if not _valid_id(evidence_id, EVIDENCE_ID_RE):
                issues.append(_issue("INVALID_CLAIM_EVIDENCE_ID", f"{mapping_locator}.evidence_id", claim_id))
                continue
            if evidence_id in seen_evidence_ids:
                issues.append(_issue("DUPLICATE_CLAIM_EVIDENCE", mapping_locator, claim_id))
            seen_evidence_ids.add(evidence_id)
            if not _valid_nonempty(mapping.get("locator")):
                issues.append(_issue("MISSING_CLAIM_EVIDENCE_LOCATOR", f"{mapping_locator}.locator", claim_id))
            if evidence_id not in sources:
                issues.append(_issue("UNKNOWN_CLAIM_SOURCE", f"{mapping_locator}.evidence_id", claim_id))
            elif not sources[evidence_id]:
                issues.append(_issue("UNVERIFIED_CLAIM_SOURCE", f"{mapping_locator}.evidence_id", claim_id))
    return issues, {"claim_count": len(claims), "source_count": len(sources)}


def _validate_id_array(
    value: Any,
    pattern: re.Pattern[str],
    locator: str,
    code: str,
    issues: list[Issue],
    record_id: Any,
) -> list[str]:
    values = _list(value)
    result: list[str] = []
    for index, item in enumerate(values):
        if not _valid_id(item, pattern):
            issues.append(_issue(code, f"{locator}[{index}]", record_id))
        else:
            result.append(item)
    return result


def validate_consistency(path: str) -> tuple[list[Issue], dict[str, int]]:
    data = _object(_read_json(path))
    issues: list[Issue] = []
    _check_fields(data, {"schema_version", "numeric_facts", "methods", "results"}, "$", issues)
    if data.get("schema_version") != SCHEMA_VERSION:
        issues.append(_issue("UNSUPPORTED_SCHEMA_VERSION", "$.schema_version"))

    facts = _list(data.get("numeric_facts"))
    seen_fact_ids: set[str] = set()
    repeated: dict[tuple[str, str], tuple[Any, ...]] = {}
    for index, raw_fact in enumerate(facts):
        locator = f"$.numeric_facts[{index}]"
        fact = _object(raw_fact)
        fact_id = fact.get("fact_id")
        _check_fields(
            fact,
            {
                "fact_id",
                "concept_id",
                "analysis_set",
                "reported_section",
                "value",
                "unit",
                "sample_size",
                "numerator",
                "denominator",
                "evidence_ids",
            },
            locator,
            issues,
            fact_id,
        )
        if not _valid_id(fact_id, FACT_ID_RE):
            issues.append(_issue("INVALID_FACT_ID", f"{locator}.fact_id"))
            fact_id = None
        elif fact_id in seen_fact_ids:
            issues.append(_issue("DUPLICATE_FACT_ID", locator, fact_id))
        else:
            seen_fact_ids.add(fact_id)

        for key in ("concept_id", "analysis_set", "reported_section", "unit"):
            if not _valid_id(fact.get(key), OPAQUE_ID_RE):
                issues.append(_issue("INVALID_FACT_FIELD", f"{locator}.{key}", fact_id))
        if not _finite_number(fact.get("value")):
            issues.append(_issue("INVALID_FACT_VALUE", f"{locator}.value", fact_id))
        if not _positive_int_or_none(fact.get("sample_size")):
            issues.append(_issue("INVALID_FACT_SAMPLE_SIZE", f"{locator}.sample_size", fact_id))
        numerator = fact.get("numerator")
        denominator = fact.get("denominator")
        if numerator is not None and not _finite_number(numerator):
            issues.append(_issue("INVALID_NUMERATOR", f"{locator}.numerator", fact_id))
        if denominator is not None and (
            not _finite_number(denominator) or denominator <= 0
        ):
            issues.append(_issue("INVALID_DENOMINATOR", f"{locator}.denominator", fact_id))
        if (numerator is None) != (denominator is None):
            issues.append(_issue("INCOMPLETE_RATIO", locator, fact_id))

        evidence_ids = _validate_id_array(
            fact.get("evidence_ids"),
            EVIDENCE_ID_RE,
            f"{locator}.evidence_ids",
            "INVALID_FACT_EVIDENCE_ID",
            issues,
            fact_id,
        )
        if not evidence_ids:
            issues.append(_issue("FACT_WITHOUT_EVIDENCE", f"{locator}.evidence_ids", fact_id))

        concept_id = fact.get("concept_id")
        analysis_set = fact.get("analysis_set")
        if (
            _valid_id(concept_id, OPAQUE_ID_RE)
            and _valid_id(analysis_set, OPAQUE_ID_RE)
            and _finite_number(fact.get("value"))
            and _valid_id(fact.get("unit"), OPAQUE_ID_RE)
            and _positive_int_or_none(fact.get("sample_size"))
            and (numerator is None or _finite_number(numerator))
            and (denominator is None or (_finite_number(denominator) and denominator > 0))
        ):
            key = (concept_id, analysis_set)
            signature = (
                fact.get("value"),
                fact.get("unit"),
                fact.get("sample_size"),
                numerator,
                denominator,
            )
            if key in repeated and repeated[key] != signature:
                issues.append(_issue("CONFLICTING_NUMERIC_FACT", locator, fact_id))
            elif key not in repeated:
                repeated[key] = signature

    methods_raw = _list(data.get("methods"))
    methods: dict[str, tuple[Any, set[str]]] = {}
    method_locators: dict[str, str] = {}
    for index, raw_method in enumerate(methods_raw):
        locator = f"$.methods[{index}]"
        method = _object(raw_method)
        method_id = method.get("method_id")
        _check_fields(
            method,
            {"method_id", "analysis_intent", "protocol_status", "outcome_ids"},
            locator,
            issues,
            method_id,
        )
        if not _valid_id(method_id, METHOD_ID_RE):
            issues.append(_issue("INVALID_METHOD_ID", f"{locator}.method_id"))
            continue
        if method_id in methods:
            issues.append(_issue("DUPLICATE_METHOD_ID", locator, method_id))
            continue
        intent = method.get("analysis_intent")
        if intent not in ANALYSIS_INTENTS:
            issues.append(_issue("INVALID_METHOD_ANALYSIS_INTENT", f"{locator}.analysis_intent", method_id))
        if method.get("protocol_status") not in PROTOCOL_STATUSES:
            issues.append(_issue("INVALID_PROTOCOL_STATUS", f"{locator}.protocol_status", method_id))
        outcomes = _validate_id_array(
            method.get("outcome_ids"),
            OUTCOME_ID_RE,
            f"{locator}.outcome_ids",
            "INVALID_METHOD_OUTCOME_ID",
            issues,
            method_id,
        )
        outcome_set = set(outcomes)
        if len(outcomes) != len(outcome_set):
            issues.append(_issue("DUPLICATE_METHOD_OUTCOME", f"{locator}.outcome_ids", method_id))
        if not outcomes:
            issues.append(_issue("METHOD_WITHOUT_OUTCOME", f"{locator}.outcome_ids", method_id))
        methods[method_id] = (intent, outcome_set)
        method_locators[method_id] = f"{locator}.outcome_ids"

    results = _list(data.get("results"))
    seen_result_ids: set[str] = set()
    observed: dict[str, set[str]] = {method_id: set() for method_id in methods}
    for index, raw_result in enumerate(results):
        locator = f"$.results[{index}]"
        result = _object(raw_result)
        result_id = result.get("result_id")
        _check_fields(
            result,
            {
                "result_id",
                "method_id",
                "outcome_id",
                "analysis_intent",
                "sample_size",
                "evidence_ids",
                "reported_sections",
            },
            locator,
            issues,
            result_id,
        )
        if not _valid_id(result_id, RESULT_ID_RE):
            issues.append(_issue("INVALID_RESULT_ID", f"{locator}.result_id"))
            result_id = None
        elif result_id in seen_result_ids:
            issues.append(_issue("DUPLICATE_RESULT_ID", locator, result_id))
        else:
            seen_result_ids.add(result_id)

        method_id = result.get("method_id")
        outcome_id = result.get("outcome_id")
        if method_id not in methods:
            issues.append(_issue("RESULT_WITHOUT_DECLARED_METHOD", f"{locator}.method_id", result_id))
        else:
            intent, expected_outcomes = methods[method_id]
            if not _valid_id(outcome_id, OUTCOME_ID_RE):
                issues.append(_issue("INVALID_RESULT_OUTCOME_ID", f"{locator}.outcome_id", result_id))
            elif outcome_id not in expected_outcomes:
                issues.append(_issue("UNDECLARED_RESULT_OUTCOME", f"{locator}.outcome_id", result_id))
            elif outcome_id in observed[method_id]:
                issues.append(_issue("DUPLICATE_METHOD_RESULT", locator, result_id))
            else:
                observed[method_id].add(outcome_id)
            if result.get("analysis_intent") != intent:
                issues.append(_issue("ANALYSIS_INTENT_MISMATCH", f"{locator}.analysis_intent", result_id))

        if not _positive_int_or_none(result.get("sample_size")) or result.get("sample_size") is None:
            issues.append(_issue("INVALID_RESULT_SAMPLE_SIZE", f"{locator}.sample_size", result_id))
        evidence_ids = _validate_id_array(
            result.get("evidence_ids"),
            EVIDENCE_ID_RE,
            f"{locator}.evidence_ids",
            "INVALID_RESULT_EVIDENCE_ID",
            issues,
            result_id,
        )
        if not evidence_ids:
            issues.append(_issue("RESULT_WITHOUT_EVIDENCE", f"{locator}.evidence_ids", result_id))
        sections = result.get("reported_sections")
        if not isinstance(sections, list) or not sections or not all(
            _valid_id(section, OPAQUE_ID_RE) for section in sections
        ):
            issues.append(_issue("RESULT_WITHOUT_REPORTED_SECTION", f"{locator}.reported_sections", result_id))

    for method_id, (_, outcomes) in sorted(methods.items()):
        for outcome_id in sorted(outcomes - observed[method_id]):
            issues.append(
                _issue(
                    "METHOD_OUTCOME_WITHOUT_RESULT",
                    method_locators[method_id],
                    outcome_id,
                )
            )

    return issues, {
        "method_count": len(methods_raw),
        "numeric_fact_count": len(facts),
        "result_count": len(results),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Offline structural validators for source, claim-evidence, and "
            "numeric/method-result scientific-writing records."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    source = subparsers.add_parser("source-manifest", help="validate one source manifest")
    source.add_argument("manifest", help="local UTF-8 JSON source manifest")

    claims = subparsers.add_parser("claims", help="audit claims against a source manifest")
    claims.add_argument("claims", help="local UTF-8 JSON claims registry")
    claims.add_argument("sources", help="local UTF-8 JSON source manifest")

    consistency = subparsers.add_parser("consistency", help="check repeated facts and method-result mappings")
    consistency.add_argument("registry", help="local UTF-8 JSON consistency registry")
    return parser


def main() -> int:
    args = _parser().parse_args()
    callbacks: dict[str, tuple[str, Callable[[], tuple[list[Issue], dict[str, int]]]]] = {
        "source-manifest": (
            "scientific_writing.source_manifest",
            lambda: validate_source_manifest(args.manifest),
        ),
        "claims": (
            "scientific_writing.claims",
            lambda: audit_claims(args.claims, args.sources),
        ),
        "consistency": (
            "scientific_writing.consistency",
            lambda: validate_consistency(args.registry),
        ),
    }
    tool, callback = callbacks[args.command]
    try:
        issues, summary = callback()
    except (InputError, OSError, TypeError, ValueError, OverflowError):
        return _input_error(tool)
    return _report(tool, issues, summary)


if __name__ == "__main__":
    raise SystemExit(main())
