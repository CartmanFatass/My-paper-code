from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools" / "research" / "scientific_writing" / "validate.py"
HASH_A = "a" * 64
HASH_B = "b" * 64


def _write_json(path: Path, payload: Any) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run(*args: Path | str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, "-B", str(CLI), *(str(arg) for arg in args)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.stderr == ""
    return completed, json.loads(completed.stdout)


def _valid_source_manifest() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_sha256": HASH_A,
        "declarations": {
            "authorship": {"status": "recorded", "artifact_sha256": HASH_A},
            "reporting": {"status": "not_applicable", "artifact_sha256": None},
        },
        "sources": [
            {
                "evidence_id": "E001",
                "source_type": "journal_article",
                "reference_sha256": HASH_B,
                "locator": "page-4-table-2",
                "verification": {
                    "status": "verified",
                    "source_opened": True,
                    "verified_by": "local-verifier-17",
                    "verified_on": "2026-08-29",
                },
            }
        ],
    }


def _valid_claims() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "claims": [
            {
                "claim_id": "C001",
                "claim_sha256": HASH_A,
                "evidence": [
                    {"evidence_id": "E001", "locator": "page-4-table-2"}
                ],
            }
        ],
    }


def _valid_consistency_registry() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "numeric_facts": [
            {
                "fact_id": "N001",
                "concept_id": "primary_rate",
                "analysis_set": "intention_to_treat",
                "reported_section": "abstract",
                "value": 12.5,
                "unit": "percent",
                "sample_size": 80,
                "numerator": 10,
                "denominator": 80,
                "evidence_ids": ["E001"],
            },
            {
                "fact_id": "N002",
                "concept_id": "primary_rate",
                "analysis_set": "intention_to_treat",
                "reported_section": "results",
                "value": 12.5,
                "unit": "percent",
                "sample_size": 80,
                "numerator": 10,
                "denominator": 80,
                "evidence_ids": ["E001"],
            },
        ],
        "methods": [
            {
                "method_id": "M001",
                "analysis_intent": "confirmatory",
                "protocol_status": "prespecified",
                "outcome_ids": ["O001"],
            }
        ],
        "results": [
            {
                "result_id": "R001",
                "method_id": "M001",
                "outcome_id": "O001",
                "analysis_intent": "confirmatory",
                "sample_size": 80,
                "evidence_ids": ["E001"],
                "reported_sections": ["results"],
            }
        ],
    }


def _codes(report: dict[str, Any]) -> set[str]:
    return {issue["code"] for issue in report["issues"]}


def test_valid_manifests_and_registries_pass_offline_deterministically(
    tmp_path: Path,
) -> None:
    sources = _write_json(tmp_path / "sources.json", _valid_source_manifest())
    claims = _write_json(tmp_path / "claims.json", _valid_claims())
    consistency = _write_json(
        tmp_path / "consistency.json", _valid_consistency_registry()
    )

    source_run, source_report = _run("source-manifest", sources)
    repeated_source_run, repeated_source_report = _run("source-manifest", sources)
    claims_run, claims_report = _run("claims", claims, sources)
    consistency_run, consistency_report = _run("consistency", consistency)

    assert source_run.returncode == claims_run.returncode == consistency_run.returncode == 0
    assert source_report == {
        "issues": [],
        "ok": True,
        "schema_version": 1,
        "summary": {"issue_count": 0, "source_count": 1},
        "tool": "scientific_writing.source_manifest",
    }
    assert claims_report["ok"] is True
    assert claims_report["summary"] == {
        "claim_count": 1,
        "issue_count": 0,
        "source_count": 1,
    }
    assert consistency_report["ok"] is True
    assert consistency_report["summary"] == {
        "issue_count": 0,
        "method_count": 1,
        "numeric_fact_count": 2,
        "result_count": 1,
    }
    assert repeated_source_run.stdout == source_run.stdout
    assert repeated_source_report == source_report


def test_unsupported_claim_and_missing_evidence_locator_fail_closed(
    tmp_path: Path,
) -> None:
    sources = _write_json(tmp_path / "sources.json", _valid_source_manifest())
    payload = _valid_claims()
    payload["claims"].append(
        {"claim_id": "C002", "claim_sha256": HASH_B, "evidence": []}
    )
    payload["claims"][0]["evidence"][0]["locator"] = ""
    claims = _write_json(tmp_path / "claims.json", payload)

    completed, report = _run("claims", claims, sources)

    assert completed.returncode == 1
    assert report["ok"] is False
    assert {"UNSUPPORTED_CLAIM", "MISSING_CLAIM_EVIDENCE_LOCATOR"} <= _codes(
        report
    )
    assert {
        (issue["code"], issue["locator"], issue.get("record_id"))
        for issue in report["issues"]
    } >= {
        ("UNSUPPORTED_CLAIM", "$.claims[1].evidence", "C002"),
        (
            "MISSING_CLAIM_EVIDENCE_LOCATOR",
            "$.claims[0].evidence[0].locator",
            "C001",
        ),
    }


def test_unverified_source_fails_manifest_and_claim_audit(tmp_path: Path) -> None:
    source_payload = _valid_source_manifest()
    source_payload["sources"][0]["verification"] = {
        "status": "unverified",
        "source_opened": False,
        "verified_by": "local-verifier-17",
        "verified_on": "2026-08-29",
    }
    sources = _write_json(tmp_path / "sources.json", source_payload)
    claims = _write_json(tmp_path / "claims.json", _valid_claims())

    source_run, source_report = _run("source-manifest", sources)
    claim_run, claim_report = _run("claims", claims, sources)

    assert source_run.returncode == claim_run.returncode == 1
    assert {"SOURCE_UNVERIFIED", "SOURCE_NOT_OPENED"} <= _codes(source_report)
    assert {
        "SOURCE_UNVERIFIED",
        "SOURCE_NOT_OPENED",
        "UNVERIFIED_CLAIM_SOURCE",
    } <= _codes(claim_report)


def test_duplicate_ids_and_conflicting_repeated_numeric_facts_fail(
    tmp_path: Path,
) -> None:
    payload = _valid_consistency_registry()
    duplicate = deepcopy(payload["numeric_facts"][0])
    duplicate["reported_section"] = "supplement"
    conflict = deepcopy(payload["numeric_facts"][0])
    conflict.update(
        {
            "fact_id": "N003",
            "reported_section": "discussion",
            "value": 15.0,
            "numerator": 12,
        }
    )
    payload["numeric_facts"].extend([duplicate, conflict])
    registry = _write_json(tmp_path / "consistency.json", payload)

    completed, report = _run("consistency", registry)

    assert completed.returncode == 1
    assert {"DUPLICATE_FACT_ID", "CONFLICTING_NUMERIC_FACT"} <= _codes(report)
    assert {
        (issue["code"], issue["locator"], issue.get("record_id"))
        for issue in report["issues"]
    } >= {
        ("DUPLICATE_FACT_ID", "$.numeric_facts[2]", "N001"),
        ("CONFLICTING_NUMERIC_FACT", "$.numeric_facts[3]", "N003"),
    }


def test_method_result_mismatch_fails_with_structural_locator(tmp_path: Path) -> None:
    payload = _valid_consistency_registry()
    payload["results"][0]["analysis_intent"] = "exploratory"
    payload["results"][0]["outcome_id"] = "O002"
    registry = _write_json(tmp_path / "consistency.json", payload)

    completed, report = _run("consistency", registry)

    assert completed.returncode == 1
    assert {
        "ANALYSIS_INTENT_MISMATCH",
        "UNDECLARED_RESULT_OUTCOME",
        "METHOD_OUTCOME_WITHOUT_RESULT",
    } <= _codes(report)


def test_diagnostics_do_not_echo_sensitive_values_or_invalid_ids(
    tmp_path: Path,
) -> None:
    secret_locator = "UNPUBLISHED-MANUSCRIPT-SENTENCE-DO-NOT-ECHO"
    secret_verifier = "PERSONAL-NAME-DO-NOT-ECHO"
    secret_invalid_id = "RESTRICTED-SOURCE-TEXT-DO-NOT-ECHO"
    secret_unknown_key = "PROPRIETARY-FIELD-NAME-DO-NOT-ECHO"
    payload = _valid_source_manifest()
    payload["sources"][0]["evidence_id"] = secret_invalid_id
    payload["sources"][0]["locator"] = secret_locator
    payload["sources"][0]["verification"]["verified_by"] = secret_verifier
    payload["sources"][0][secret_unknown_key] = "another sensitive value"
    sources = _write_json(tmp_path / "sources.json", payload)

    completed, report = _run("source-manifest", sources)

    assert completed.returncode == 1
    assert {"INVALID_EVIDENCE_ID", "UNKNOWN_FIELD"} <= _codes(report)
    serialized = json.dumps(report, sort_keys=True)
    for secret in (
        secret_locator,
        secret_verifier,
        secret_invalid_id,
        secret_unknown_key,
        "another sensitive value",
    ):
        assert secret not in serialized


def test_malformed_or_duplicate_key_json_returns_safe_invalid_input(
    tmp_path: Path,
) -> None:
    malformed = tmp_path / "sources.json"
    malformed.write_text(
        '{"schema_version":1,"schema_version":1,"private":"DO-NOT-ECHO"}',
        encoding="utf-8",
    )

    completed, report = _run("source-manifest", malformed)

    assert completed.returncode == 1
    assert report == {
        "issues": [{"code": "INVALID_INPUT", "locator": "$"}],
        "ok": False,
        "schema_version": 1,
        "summary": {"issue_count": 1},
        "tool": "scientific_writing.source_manifest",
    }
    assert "DO-NOT-ECHO" not in completed.stdout
