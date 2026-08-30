"""Phase 0 RED tests for HMASD durable state contracts.

These tests intentionally describe the contract before the implementation exists.
They are kept narrow so later phases can reuse the fixtures without importing
workflow behavior.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_state.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hmasd_phase0"
KINDS = (
    "portfolio_registry",
    "research_state",
    "engineering_state",
    "external_review_index",
    "run_manifest",
    "accepted_result",
    "external_archive",
    "agent_result",
    "runtime_agents",
    "runtime_worktrees",
)

SCHEMA_KINDS = (*KINDS, "runtime_browser_assignments")


def fixture(kind: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{kind}.json").read_text(encoding="utf-8"))

def historical_archive(document: dict[str, Any], seed: str) -> dict[str, Any]:
    question = hashlib.sha256(f"question-{seed}".encode()).hexdigest()
    evidence = hashlib.sha256(f"evidence-{seed}".encode()).hexdigest()
    canonical_round_id = hashlib.sha256(
        (
            document["direction_id"]
            + "\n"
            + question
            + "\n"
            + evidence
            + "\n"
            + document["workflow_version"]
        ).encode("utf-8")
    ).hexdigest()[:20]
    observed_round_id = hashlib.sha256(f"observed-{seed}".encode()).hexdigest()[:20]
    provider = "chatgpt"
    return {
        "classification": "CROSS_SWAPPED_ROUND_ID",
        "observed_round_id": observed_round_id,
        "canonical_round_id": canonical_round_id,
        "question_sha256": question,
        "evidence_set_sha256": evidence,
        "review_stage": "pro_innovator",
        "provider": provider,
        "stable_key": f"stable-{seed}",
        "operation_id": f"operation-{seed}",
        "idempotency_key": f"idempotency-{seed}",
        "request_fingerprint": hashlib.sha256(f"request-{seed}".encode()).hexdigest(),
        "prompt_sha256": hashlib.sha256(f"prompt-{seed}".encode()).hexdigest(),
        "session_id": f"session-{seed}",
        "terminal_state": "NATURAL_COMPLETION_VERIFIED",
        "completed_at": "2026-08-24T00:05:00Z",
        "legacy_archive_ref": {
            "path": (
                f"docs/external-review/directions/{document['direction_id']}/"
                f"{observed_round_id}/{provider}/NATURAL_COMPLETION_ARCHIVE.json"
            ),
            "sha256": hashlib.sha256(f"archive-{seed}".encode()).hexdigest(),
        },
        "response_ref": {
            "path": (
                f"docs/research/candidates/{document['direction_id']}/"
                f"RESPONSE_{seed}.md"
            ),
            "sha256": hashlib.sha256(f"response-{seed}".encode()).hexdigest(),
        },
    }


def run_cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def test_all_eleven_schema_contracts_are_present_and_strict() -> None:
    schema_dir = ROOT / "scripts" / "schemas"
    for kind in SCHEMA_KINDS:
        schema = json.loads(
            (schema_dir / f"hmasd_{kind}.schema.json").read_text(encoding="utf-8")
        )
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"]


def test_external_review_schema_encodes_versioned_history_shape() -> None:
    schema = json.loads(
        (ROOT / "scripts" / "schemas" / "hmasd_external_review_index.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema["oneOf"] == [
        {
            "properties": {"schema_version": {"const": 2}},
            "not": {"required": ["historical_archives"]},
        },
        {
            "properties": {"schema_version": {"const": 3}},
            "required": ["historical_archives"],
        },
    ]


def test_valid_phase0_fixtures_validate() -> None:
    for kind in KINDS:
        path = FIXTURES / f"{kind}.json"
        result = run_cli("validate", "--kind", kind, "--path", str(path))
        assert result.returncode == 0, (kind, result.stderr)


def test_external_review_v2_status_transitions_use_the_exact_pro_pair(
    tmp_path: Path,
) -> None:
    current = fixture("external_review_index")
    assert set(current["rounds"][0]["prompt_refs"]) == {
        "pro_innovator",
        "pro_convergence",
    }
    assert set(current["rounds"][0]["providers"]) == {
        "pro_innovator",
        "pro_convergence",
    }
    target = tmp_path / "external-review-index.json"
    source = tmp_path / "external-review-initial.json"
    source.write_text(json.dumps(current, sort_keys=True), encoding="utf-8")
    initialized = run_cli(
        "initialize",
        "--kind",
        "external_review_index",
        "--path",
        str(target),
        "--writer",
        current["writer"],
        "--input",
        str(source),
    )
    assert initialized.returncode == 0, initialized.stderr

    for revision, status in enumerate(
        (
            "INNOVATOR_RUNNING",
            "LOCAL_RESEARCH",
            "SYNTHESIS_READY",
            "CONVERGENCE_RUNNING",
            "COMPLETE",
        ),
        start=2,
    ):
        replacement = copy.deepcopy(current)
        replacement["revision"] = revision
        replacement["rounds"][0]["status"] = status
        if status == "COMPLETE":
            replacement["rounds"][0]["completed_at"] = "2026-08-24T00:05:00Z"
        replacement_path = tmp_path / f"external-review-r{revision}.json"
        replacement_path.write_text(
            json.dumps(replacement, sort_keys=True),
            encoding="utf-8",
        )
        result = run_cli(
            "replace",
            "--kind",
            "external_review_index",
            "--path",
            str(target),
            "--writer",
            current["writer"],
            "--expected-revision",
            str(current["revision"]),
            "--input",
            str(replacement_path),
        )
        assert result.returncode == 0, (status, result.stdout, result.stderr)
        current = replacement


def test_external_review_v2_rejects_old_three_stage_fields(tmp_path: Path) -> None:
    document = fixture("external_review_index")
    review_round = document["rounds"][0]
    innovator_prompt = review_round["prompt_refs"]["pro_innovator"]
    review_round["prompt_refs"] = {
        "gemini_divergent": innovator_prompt,
        "pro_divergent": innovator_prompt,
        "pro_convergence": None,
    }
    review_round["providers"] = {
        "gemini_divergent": None,
        "pro_divergent": None,
        "pro_convergence": None,
    }
    review_round["status"] = "DIVERGENT_PENDING"
    path = tmp_path / "external-review-v1-fields.json"
    path.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")

    result = run_cli(
        "validate",
        "--kind",
        "external_review_index",
        "--path",
        str(path),
    )

    assert result.returncode == 2


def test_external_review_v3_recomputes_history_and_rejects_synthetic_rounds(
    tmp_path: Path,
) -> None:
    document = fixture("external_review_index")
    unexpected_history = copy.deepcopy(document)
    unexpected_history["historical_archives"] = []
    unexpected_history_path = tmp_path / "external-review-v2-with-history.json"
    unexpected_history_path.write_text(json.dumps(unexpected_history), encoding="utf-8")
    assert run_cli(
        "validate",
        "--kind",
        "external_review_index",
        "--path",
        str(unexpected_history_path),
    ).returncode == 2

    missing_history = copy.deepcopy(document)
    missing_history["schema_version"] = 3
    missing_history_path = tmp_path / "external-review-v3-without-history.json"
    missing_history_path.write_text(json.dumps(missing_history), encoding="utf-8")
    assert run_cli(
        "validate",
        "--kind",
        "external_review_index",
        "--path",
        str(missing_history_path),
    ).returncode == 2

    document["schema_version"] = 3
    record = historical_archive(document, "one")
    document["historical_archives"] = [record]
    valid = tmp_path / "external-review-v3.json"
    valid.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    result = run_cli(
        "validate",
        "--kind",
        "external_review_index",
        "--path",
        str(valid),
    )
    assert result.returncode == 0, result.stderr

    wrong_canonical = copy.deepcopy(document)
    wrong_canonical["historical_archives"][0]["canonical_round_id"] = "0" * 20
    wrong_path = tmp_path / "external-review-v3-wrong-canonical.json"
    wrong_path.write_text(json.dumps(wrong_canonical), encoding="utf-8")
    assert run_cli(
        "validate",
        "--kind",
        "external_review_index",
        "--path",
        str(wrong_path),
    ).returncode == 2

    duplicate = copy.deepcopy(document)
    duplicate["historical_archives"].append(copy.deepcopy(record))
    duplicate_path = tmp_path / "external-review-v3-duplicate.json"
    duplicate_path.write_text(json.dumps(duplicate), encoding="utf-8")
    assert run_cli(
        "validate",
        "--kind",
        "external_review_index",
        "--path",
        str(duplicate_path),
    ).returncode == 2

    synthetic = copy.deepcopy(document)
    synthetic_round = synthetic["rounds"][0]
    synthetic_round["round_id"] = record["canonical_round_id"]
    synthetic_round["question_sha256"] = record["question_sha256"]
    synthetic_round["evidence_set_sha256"] = record["evidence_set_sha256"]
    synthetic_path = tmp_path / "external-review-v3-synthetic-round.json"
    synthetic_path.write_text(json.dumps(synthetic), encoding="utf-8")
    assert run_cli(
        "validate",
        "--kind",
        "external_review_index",
        "--path",
        str(synthetic_path),
    ).returncode == 2


def test_checked_in_external_review_identity_recovery_is_exact_and_reciprocal() -> None:
    expected_records = {
        "semigroup_consistent_duration_model_policy": {
            "canonical_round_id": "211d583818335dd612c7",
            "classification": "CROSS_SWAPPED_ROUND_ID",
            "completed_at": "2026-08-29T23:52:48.022Z",
            "evidence_set_sha256": (
                "29bccb94957be0a4c87bf919195dc054417337be0f322f337cef3846451c9539"
            ),
            "idempotency_key": (
                "scdmp-opportunity-law-r02-pro-convergence-20260829-strict-01"
            ),
            "legacy_archive_ref": {
                "path": (
                    "docs/external-review/directions/"
                    "semigroup_consistent_duration_model_policy/"
                    "9f48f4a6bcace75fddeb/chatgpt/NATURAL_COMPLETION_ARCHIVE.json"
                ),
                "sha256": (
                    "299c25b8fb5aa3f48744e6ba42fc5758aa68f89d3669ef8098583f5afb2e58b2"
                ),
            },
            "observed_round_id": "9f48f4a6bcace75fddeb",
            "operation_id": "499b71d6-ca35-42d6-9aee-4c1202a7a82d",
            "prompt_sha256": (
                "a8dff6d04f5b7f8d2c5d43658773deab7c5b2f3d0ae5df7c29d118b4897de10b"
            ),
            "provider": "chatgpt",
            "question_sha256": (
                "7506749d50500afe5c7108634aaa97e5975854ee8be239a53834be08a4116c55"
            ),
            "request_fingerprint": (
                "f7ff3f3088493379da96aaf99f9bc7b9a63d8482bb91dd115d209e4edd3fb475"
            ),
            "response_ref": {
                "path": (
                    "docs/research/candidates/"
                    "semigroup_consistent_duration_model_policy/"
                    "SCDMP_OPPORTUNITY_LAW_GPT56_PRO_CONVERGENCE_RESPONSE_20260829.md"
                ),
                "sha256": (
                    "b8b00486f55499bca574dbbd1a3ee90e23042a0aca76544e024f4d2e6ef0336f"
                ),
            },
            "review_stage": "pro_convergence",
            "session_id": "6a93307b-6410-83e8-b9e5-1ab428de2fc6",
            "stable_key": "scdmp-opportunity-law-r02-pro-convergence",
            "terminal_state": "NATURAL_COMPLETION_VERIFIED",
        },
        "voronoi_quadrature_field_policy": {
            "canonical_round_id": "9f48f4a6bcace75fddeb",
            "classification": "CROSS_SWAPPED_ROUND_ID",
            "completed_at": "2026-08-29T23:53:06.893Z",
            "evidence_set_sha256": (
                "26a7f19034b41aad3c029932e501e46c0519783ef983f3b95d83190adf268da9"
            ),
            "idempotency_key": (
                "vqfp-proof-sized-association-gate-r01-pro-innovator-"
                "resume-20260829-strict-03"
            ),
            "legacy_archive_ref": {
                "path": (
                    "docs/external-review/directions/voronoi_quadrature_field_policy/"
                    "211d583818335dd612c7/chatgpt/NATURAL_COMPLETION_ARCHIVE.json"
                ),
                "sha256": (
                    "4df09776b114da27e1e27a8434ebe8125639a3d8ffbae18beae376425e11f47c"
                ),
            },
            "observed_round_id": "211d583818335dd612c7",
            "operation_id": "be82f31d-a7cc-4757-9dcb-1393653250fb",
            "prompt_sha256": (
                "4c9e2df6b994a532892bb0877c2f7be6aee77fc06c6666bb5fa9eb415dc04833"
            ),
            "provider": "chatgpt",
            "question_sha256": (
                "74d33eeb9525c4e9472ce35e0283ce46214a90b95699b1a638c3e940b46ad1b9"
            ),
            "request_fingerprint": (
                "b22a9ae15c03521e5454c42d276e60878d8f3812b83feaa414e67f724f48119e"
            ),
            "response_ref": {
                "path": (
                    "docs/research/candidates/voronoi_quadrature_field_policy/"
                    "VQFP_PROOF_SIZED_ASSOCIATION_GATE_R01_PRO_INNOVATOR_"
                    "RESPONSE_20260829.md"
                ),
                "sha256": (
                    "c5f6724fc5a656a6a02b968d4d6969b9c87e8bba25d09695d4b73913379fe162"
                ),
            },
            "review_stage": "pro_innovator",
            "session_id": "6a933040-034c-83e8-9e8c-9e83eed1c1fa",
            "stable_key": "vqfp-proof-sized-association-gate-r01-pro-innovator",
            "terminal_state": "NATURAL_COMPLETION_VERIFIED",
        },
    }

    recovered: dict[str, dict[str, Any]] = {}
    for direction_id, expected_record in expected_records.items():
        index_path = (
            ROOT
            / "docs"
            / "research"
            / "candidates"
            / direction_id
            / "workflow"
            / "external-review"
            / "index.json"
        )
        index = json.loads(index_path.read_text(encoding="utf-8"))
        assert index == {
            "direction_id": direction_id,
            "historical_archives": [expected_record],
            "revision": 3,
            "rounds": [],
            "schema_version": 3,
            "updated_at": "2026-08-30T01:57:56Z",
            "workflow_version": "hmasd-external-review-v1",
            "writer": f"EM-{direction_id}",
        }

        record = index["historical_archives"][0]
        canonical_material = "\n".join(
            (
                direction_id,
                record["question_sha256"],
                record["evidence_set_sha256"],
                index["workflow_version"],
            )
        ).encode("utf-8")
        assert hashlib.sha256(canonical_material).hexdigest()[:20] == record[
            "canonical_round_id"
        ]

        archive_path = ROOT / record["legacy_archive_ref"]["path"]
        response_path = ROOT / record["response_ref"]["path"]
        archive_bytes = archive_path.read_bytes()
        response_bytes = response_path.read_bytes()
        assert hashlib.sha256(archive_bytes).hexdigest() == record["legacy_archive_ref"][
            "sha256"
        ]
        assert hashlib.sha256(response_bytes).hexdigest() == record["response_ref"][
            "sha256"
        ]

        archive = json.loads(archive_bytes)
        assert archive["schema"] == "agentify_review_natural_completion_archive_v1"
        assert archive["operationId"] == record["operation_id"]
        assert archive["idempotencyKey"] == record["idempotency_key"]
        assert archive["stableKey"] == record["stable_key"]
        assert archive["provider"] == record["provider"]
        assert archive["model"] == "Pro"
        assert archive["conversationId"] == record["session_id"]
        assert archive["conversationUrl"] == (
            f"https://chatgpt.com/c/{record['session_id']}"
        )
        assert archive["terminalState"] == record["terminal_state"]
        assert archive["sendCount"] == 1
        assert archive["sendActionCount"] == 1
        assert archive["userMessageId"]
        assert archive["assistantMessageId"]
        assert archive["completedAt"] == record["completed_at"]
        assert archive["responseSha256"] == record["response_ref"]["sha256"]
        assert archive["responseText"].encode("utf-8") == response_bytes
        recovered[direction_id] = record

    scdmp = recovered["semigroup_consistent_duration_model_policy"]
    vqfp = recovered["voronoi_quadrature_field_policy"]
    assert scdmp["observed_round_id"] == vqfp["canonical_round_id"]
    assert vqfp["observed_round_id"] == scdmp["canonical_round_id"]


def test_external_review_v2_to_v3_migration_adds_no_facts_and_history_is_append_only(
    tmp_path: Path,
) -> None:
    original = fixture("external_review_index")
    target = tmp_path / "external-review-index.json"
    target.write_text(json.dumps(original, sort_keys=True), encoding="utf-8")
    stale_before = target.read_bytes()
    stale = run_cli(
        "migrate",
        "--kind",
        "external_review_index",
        "--path",
        str(target),
        "--writer",
        original["writer"],
        "--expected-revision",
        "99",
        "--to-version",
        "3",
    )
    assert stale.returncode == 4
    assert target.read_bytes() == stale_before

    attempted_bump = copy.deepcopy(original)
    attempted_bump["schema_version"] = 3
    attempted_bump["revision"] += 1
    attempted_bump["historical_archives"] = [
        historical_archive(attempted_bump, "during-schema-bump")
    ]
    attempted_bump_path = tmp_path / "external-review-bump-with-history.json"
    attempted_bump_path.write_text(json.dumps(attempted_bump), encoding="utf-8")
    no_facts_before = target.read_bytes()
    refused_bump = run_cli(
        "replace",
        "--kind",
        "external_review_index",
        "--path",
        str(target),
        "--writer",
        original["writer"],
        "--expected-revision",
        str(original["revision"]),
        "--input",
        str(attempted_bump_path),
    )
    assert refused_bump.returncode == 6
    assert target.read_bytes() == no_facts_before

    migrated_result = run_cli(
        "migrate",
        "--kind",
        "external_review_index",
        "--path",
        str(target),
        "--writer",
        original["writer"],
        "--expected-revision",
        str(original["revision"]),
        "--to-version",
        "3",
    )
    assert migrated_result.returncode == 0, migrated_result.stderr
    migrated = json.loads(target.read_text(encoding="utf-8"))
    assert migrated["schema_version"] == 3
    assert migrated["revision"] == original["revision"] + 1
    assert migrated["rounds"] == original["rounds"]
    assert migrated["historical_archives"] == []

    first = copy.deepcopy(migrated)
    first["revision"] += 1
    first["historical_archives"].append(historical_archive(first, "first"))
    first_path = tmp_path / "external-review-first-history.json"
    first_path.write_text(json.dumps(first), encoding="utf-8")
    appended = run_cli(
        "replace",
        "--kind",
        "external_review_index",
        "--path",
        str(target),
        "--writer",
        original["writer"],
        "--expected-revision",
        str(migrated["revision"]),
        "--input",
        str(first_path),
    )
    assert appended.returncode == 0, appended.stderr

    second = copy.deepcopy(first)
    second["revision"] += 1
    second["historical_archives"].append(historical_archive(second, "second"))
    second_path = tmp_path / "external-review-second-history.json"
    second_path.write_text(json.dumps(second), encoding="utf-8")
    appended_again = run_cli(
        "replace",
        "--kind",
        "external_review_index",
        "--path",
        str(target),
        "--writer",
        original["writer"],
        "--expected-revision",
        str(first["revision"]),
        "--input",
        str(second_path),
    )
    assert appended_again.returncode == 0, appended_again.stderr

    rewritten = copy.deepcopy(second)
    rewritten["revision"] += 1
    rewritten["historical_archives"][0]["response_ref"]["sha256"] = "0" * 64
    rewritten_path = tmp_path / "external-review-rewritten-history.json"
    rewritten_path.write_text(json.dumps(rewritten), encoding="utf-8")
    immutable_before = target.read_bytes()
    refused = run_cli(
        "replace",
        "--kind",
        "external_review_index",
        "--path",
        str(target),
        "--writer",
        original["writer"],
        "--expected-revision",
        str(second["revision"]),
        "--input",
        str(rewritten_path),
    )
    assert refused.returncode == 6
    assert target.read_bytes() == immutable_before


def test_portfolio_payload_is_root_owned_after_manager_merge(tmp_path: Path) -> None:
    document = fixture("agent_result")
    document.update(
        {
            "assignment_id": "root-portfolio-wake",
            "logical_identity": "Root",
            "materiality": "PORTFOLIO",
            "payload": {
                "kind": "portfolio",
                "direction_actions": [],
                "capacity_action": {
                    "action": "NONE",
                    "direction_id": None,
                    "decision_ref": None,
                },
                "portfolio_ref": {
                    "path": "docs/research/portfolio/PORTFOLIO.md",
                    "sha256": "a" * 64,
                },
                "registry_revision": 1,
            },
            "role": "root",
            "summary": "Root reconciled portfolio lifecycle.",
        }
    )
    path = tmp_path / "root-portfolio.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 0, result.stderr

    document["role"] = "hmasd-portfolio"
    document["logical_identity"] = "Portfolio"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2


def test_unknown_version_extra_key_and_invalid_path_are_refused_without_rewrite(
    tmp_path: Path,
) -> None:
    source = fixture("research_state")
    path = tmp_path / "state.json"
    path.write_bytes(json.dumps(source, indent=2, sort_keys=True).encode() + b"\n")

    original = path.read_bytes()
    unknown = dict(source, schema_version=3)
    unknown_path = tmp_path / "unknown.json"
    unknown_path.write_bytes(json.dumps(unknown, indent=2, sort_keys=True).encode() + b"\n")
    result = run_cli("validate", "--kind", "research_state", "--path", str(unknown_path))
    assert result.returncode == 3
    assert unknown_path.read_bytes() == original.replace(b'"schema_version": 2', b'"schema_version": 3')

    extra_path = tmp_path / "extra.json"
    extra_path.write_bytes(
        json.dumps(dict(source, unexpected=True), indent=2, sort_keys=True).encode() + b"\n"
    )
    result = run_cli("validate", "--kind", "research_state", "--path", str(extra_path))
    assert result.returncode == 2
    assert extra_path.read_bytes().endswith(b"\n")

    invalid_path = dict(source)
    invalid_path["direction_ref"] = dict(source["direction_ref"], path="../outside.md")
    invalid_path_file = tmp_path / "invalid-path.json"
    invalid_path_file.write_bytes(
        json.dumps(invalid_path, indent=2, sort_keys=True).encode() + b"\n"
    )
    result = run_cli("validate", "--kind", "research_state", "--path", str(invalid_path_file))
    assert result.returncode == 2


def test_writer_and_path_ownership_are_enforced(tmp_path: Path) -> None:
    state = fixture("research_state")
    wrong_writer = tmp_path / "wrong-writer.json"
    wrong_writer.write_bytes(json.dumps(dict(state, writer="CM-example-direction")).encode())
    result = run_cli("validate", "--kind", "research_state", "--path", str(wrong_writer))
    assert result.returncode == 5

    wrong_ref = tmp_path / "wrong-ref.json"
    bad = dict(state)
    bad["direction_ref"] = dict(state["direction_ref"], path="docs/research/candidates/other/DIRECTION.md")
    wrong_ref.write_bytes(json.dumps(bad).encode())
    result = run_cli("validate", "--kind", "research_state", "--path", str(wrong_ref))
    assert result.returncode == 5


def test_replace_refuses_cross_writer_and_immutable_record_rewrites(tmp_path: Path) -> None:
    """A CAS replacement may advance facts, never reassign their durable record."""

    def assert_refused(
        label: str,
        kind: str,
        current: dict[str, Any],
        replacement: dict[str, Any],
        writer: str,
        expected_code: int,
    ) -> None:
        target = tmp_path / f"{label}.json"
        initial_path = tmp_path / f"{label}-initial.json"
        replacement_path = tmp_path / f"{label}-replacement.json"
        initial_path.write_text(json.dumps(current, sort_keys=True), encoding="utf-8")
        initialized = run_cli(
            "initialize",
            "--kind",
            kind,
            "--path",
            str(target),
            "--writer",
            current["writer"],
            "--input",
            str(initial_path),
        )
        assert initialized.returncode == 0, initialized.stderr
        before = target.read_bytes()
        replacement_path.write_text(json.dumps(replacement, sort_keys=True), encoding="utf-8")
        result = run_cli(
            "replace",
            "--kind",
            kind,
            "--path",
            str(target),
            "--writer",
            writer,
            "--expected-revision",
            "1",
            "--input",
            str(replacement_path),
        )
        assert result.returncode == expected_code, (label, result.stdout, result.stderr)
        assert target.read_bytes() == before

    direction_current = fixture("research_state")
    direction_replacement = copy.deepcopy(direction_current)
    direction_replacement.update(
        {
            "revision": 2,
            "writer": "EM-other-direction",
            "direction_id": "other-direction",
        }
    )
    direction_replacement["direction_ref"]["path"] = (
        "docs/research/candidates/other-direction/DIRECTION.md"
    )
    assert_refused(
        "direction-takeover",
        "research_state",
        direction_current,
        direction_replacement,
        "EM-other-direction",
        5,
    )

    run_current = fixture("run_manifest")
    run_replacement = copy.deepcopy(run_current)
    run_replacement.update(
        {
            "revision": 2,
            "run_id": "other-run",
            "command": ["python3", "evaluate.py", "--seed", "7"],
        }
    )
    run_replacement["command_sha256"] = hashlib.sha256(
        "\0".join(run_replacement["command"]).encode("utf-8")
    ).hexdigest()
    assert_refused(
        "run-command",
        "run_manifest",
        run_current,
        run_replacement,
        "Operator-example-run",
        6,
    )

    operator_replacement = copy.deepcopy(run_current)
    operator_replacement.update(
        {
            "revision": 2,
            "writer": "Operator-other-run",
            "operator_identity": "Operator-other-run",
        }
    )
    assert_refused(
        "operator-takeover",
        "run_manifest",
        run_current,
        operator_replacement,
        "Operator-other-run",
        5,
    )

    external_current = fixture("external_review_index")
    provider = {
        "operation_id": "operation-a",
        "idempotency_key": "idempotency-a",
        "session_ref": "session-a",
        "terminal_state": "COMPLETED",
        "archive_ref": None,
        "handoff_ref": None,
        "completed_at": "2026-08-24T00:01:00Z",
    }
    external_current["rounds"][0]["providers"]["pro_innovator"] = provider
    external_replacement = copy.deepcopy(external_current)
    external_replacement["revision"] = 2
    external_replacement["rounds"][0]["providers"]["pro_innovator"]["operation_id"] = "operation-b"
    assert_refused(
        "external-operation",
        "external_review_index",
        external_current,
        external_replacement,
        "EM-example-direction",
        6,
    )

    external_round_replacement = copy.deepcopy(external_current)
    external_round_replacement["revision"] = 2
    external_round_replacement["rounds"][0]["question_sha256"] = "e" * 64
    external_round_replacement["rounds"][0]["round_id"] = hashlib.sha256(
        (
            external_round_replacement["direction_id"]
            + "\n"
            + external_round_replacement["rounds"][0]["question_sha256"]
            + "\n"
            + external_round_replacement["rounds"][0]["evidence_set_sha256"]
            + "\n"
            + external_round_replacement["workflow_version"]
        ).encode("utf-8")
    ).hexdigest()[:20]
    assert_refused(
        "external-round",
        "external_review_index",
        external_current,
        external_round_replacement,
        "EM-example-direction",
        6,
    )

    result_current = fixture("accepted_result")
    result_replacement = copy.deepcopy(result_current)
    result_replacement.update(
        {
            "revision": 2,
            "result_id": "other-result",
            "conclusion_path": "docs/research/candidates/example-direction/results/other-result.md",
        }
    )
    assert_refused(
        "result-identity",
        "accepted_result",
        result_current,
        result_replacement,
        "EM-example-direction",
        6,
    )

    terminal_current = copy.deepcopy(run_current)
    terminal_current["status"] = "SUCCEEDED"
    terminal_current["process"].update(
        {
            "execution_token": "token-a",
            "pid": 123,
            "process_group_id": 123,
            "linux_boot_id": "boot-a",
            "proc_start_ticks": 99,
            "started_at": "2026-08-24T00:00:00Z",
            "ended_at": "2026-08-24T00:01:00Z",
            "exit_code": 0,
            "terminal_reason": "CHILD_EXIT_0",
        }
    )
    terminal_replacement = copy.deepcopy(terminal_current)
    terminal_replacement["revision"] = 2
    terminal_replacement["process"]["terminal_reason"] = "REWRITTEN"
    assert_refused(
        "terminal-provenance",
        "run_manifest",
        terminal_current,
        terminal_replacement,
        "Operator-example-run",
        6,
    )

    worktree_current = fixture("runtime_worktrees")
    worktree_replacement = copy.deepcopy(worktree_current)
    worktree_replacement["revision"] = 2
    worktree_replacement["worktrees"][0]["canonical_absolute_path"] = "/tmp/other-worktree"
    assert_refused(
        "worktree-target",
        "runtime_worktrees",
        worktree_current,
        worktree_replacement,
        "Root",
        6,
    )

    worktree_ref_replacement = copy.deepcopy(worktree_current)
    worktree_ref_replacement["revision"] = 2
    worktree_ref_replacement["worktrees"][0]["worktree_ref"] = "wt-other"
    assert_refused(
        "worktree-ref",
        "runtime_worktrees",
        worktree_current,
        worktree_ref_replacement,
        "Root",
        6,
    )

    runtime_agents_current = fixture("runtime_agents")
    runtime_agents_replacement = copy.deepcopy(runtime_agents_current)
    runtime_agents_replacement["revision"] = 2
    runtime_agents_replacement["agents"][0]["runtime_ref"] = "runtime-other-em"
    assert_refused(
        "runtime-agent-ref",
        "runtime_agents",
        runtime_agents_current,
        runtime_agents_replacement,
        "Root",
        6,
    )


def test_registry_enforces_uniqueness_dependencies_and_active_limit(tmp_path: Path) -> None:
    registry = fixture("portfolio_registry")
    registry["directions"] = registry["directions"] * 9
    for index, direction in enumerate(registry["directions"]):
        direction["id"] = f"direction-{index}"
        direction["abbreviation"] = f"D{index}"
        direction["path"] = f"docs/research/candidates/direction-{index}"
        direction["lifecycle_decision_ref"]["heading"] = f"Direction direction-{index}"
        direction["agent"]["logical_identity"] = f"EM-direction-{index}"
        direction["agent"]["job_name"] = f"EMDirection{index}"
        direction["research_state_path"] = f"docs/research/candidates/direction-{index}/workflow/research/state.json"
        direction["engineering_state_path"] = f"docs/research/candidates/direction-{index}/workflow/engineering/state.json"
        direction["external_review_index_path"] = f"docs/research/candidates/direction-{index}/workflow/external-review/index.json"
        direction["lifecycle"] = "ACTIVE"
        direction["dependencies"] = []
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(path))
    assert result.returncode == 2

    cyclic = fixture("portfolio_registry")
    cyclic["directions"][0]["dependencies"] = ["example-direction"]
    cyclic["directions"].append(dict(cyclic["directions"][0], id="second-direction", dependencies=["example-direction"]))
    cyclic["directions"][0]["dependencies"] = ["second-direction"]
    cyclic_path = tmp_path / "cyclic.json"
    cyclic_path.write_text(json.dumps(cyclic), encoding="utf-8")
    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(cyclic_path))
    assert result.returncode == 2


def test_foreign_archive_has_native_schema_and_exact_completion_hash(tmp_path: Path) -> None:
    archive = fixture("external_archive")
    assert "schema_version" not in archive
    assert "revision" not in archive
    assert "writer" not in archive
    archive_path = tmp_path / "archive.json"
    archive_path.write_text(json.dumps(archive), encoding="utf-8")
    result = run_cli("validate", "--kind", "external_archive", "--path", str(archive_path))
    assert result.returncode == 0, result.stderr

    archive["responseText"] = "tampered"
    archive_path.write_text(json.dumps(archive), encoding="utf-8")
    result = run_cli("validate", "--kind", "external_archive", "--path", str(archive_path))
    assert result.returncode == 2


def test_initialize_replace_and_migrate_are_revision_cas_and_byte_preserving(
    tmp_path: Path,
) -> None:
    source = FIXTURES / "research_state.json"
    target = tmp_path / "state.json"
    result = run_cli(
        "initialize",
        "--kind",
        "research_state",
        "--path",
        str(target),
        "--writer",
        "EM-example-direction",
        "--input",
        str(source),
    )
    assert result.returncode == 0, result.stderr
    original = target.read_bytes()

    replacement = fixture("research_state")
    replacement["revision"] = 2
    replacement["next_action"] = {"kind": "WAIT", "owner": "ROOT", "input_refs": []}
    replacement_path = tmp_path / "replacement.json"
    replacement_path.write_text(json.dumps(replacement), encoding="utf-8")
    stale = run_cli(
        "replace",
        "--kind",
        "research_state",
        "--path",
        str(target),
        "--writer",
        "EM-example-direction",
        "--expected-revision",
        "99",
        "--input",
        str(replacement_path),
    )
    assert stale.returncode == 4
    assert target.read_bytes() == original

    unsupported = fixture("research_state")
    unsupported["schema_version"] = 2
    unsupported_path = tmp_path / "unsupported.json"
    unsupported_path.write_text(json.dumps(unsupported), encoding="utf-8")
    migrate = run_cli(
        "migrate",
        "--kind",
        "research_state",
        "--path",
        str(unsupported_path),
        "--writer",
        "EM-example-direction",
        "--expected-revision",
        "1",
        "--to-version",
        "3",
    )
    assert migrate.returncode == 3
    assert unsupported_path.read_text(encoding="utf-8") == unsupported_path.read_text(encoding="utf-8")

    legacy = fixture("research_state")
    legacy["schema_version"] = 1
    legacy["next_action"].pop("owner")
    legacy_path = tmp_path / "legacy.json"
    legacy_input = tmp_path / "legacy-input.json"
    legacy_input.write_text(json.dumps(legacy), encoding="utf-8")
    initialize_legacy = run_cli(
        "initialize",
        "--kind",
        "research_state",
        "--path",
        str(legacy_path),
        "--writer",
        "EM-example-direction",
        "--input",
        str(legacy_input),
    )
    assert initialize_legacy.returncode == 3, initialize_legacy.stderr
    assert not legacy_path.exists()
    legacy_path.write_text(json.dumps(legacy), encoding="utf-8")
    migrate_legacy = run_cli(
        "migrate",
        "--kind",
        "research_state",
        "--path",
        str(legacy_path),
        "--writer",
        "EM-example-direction",
        "--expected-revision",
        "1",
        "--to-version",
        "2",
    )
    assert migrate_legacy.returncode == 0, migrate_legacy.stderr
    migrated = json.loads(legacy_path.read_text(encoding="utf-8"))
    assert migrated["schema_version"] == 2
    assert migrated["revision"] == 2
    assert migrated["next_action"]["owner"] == "EM"


def test_replace_repairs_only_stale_current_research_direction_ref(
    tmp_path: Path, monkeypatch
) -> None:
    spec = importlib.util.spec_from_file_location("hmasd_state_live_ref", SCRIPT)
    assert spec is not None and spec.loader is not None
    state = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state)

    isolated_root = tmp_path / "root"
    direction_ref = "docs/research/candidates/example-direction/DIRECTION.md"
    authority = isolated_root / direction_ref
    authority.parent.mkdir(parents=True)
    authority.write_text("# current authority\n", encoding="utf-8")
    live_sha = hashlib.sha256(authority.read_bytes()).hexdigest()
    registry_path = isolated_root / "docs/research/portfolio/workflow/registry.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "directions": [
                    {
                        "id": "example-direction",
                        "path": "docs/research/candidates/example-direction",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(state, "ROOT", isolated_root)

    current = fixture("research_state")
    current["direction_ref"]["sha256"] = "a" * 64
    target = tmp_path / "state.json"
    target.write_text(json.dumps(current), encoding="utf-8")
    candidate = copy.deepcopy(current)
    candidate["direction_ref"]["sha256"] = live_sha
    candidate["revision"] = 2

    with pytest.raises(state.ValidationError, match="research direction_ref SHA"):
        state.validate_document("research_state", current, writer=current["writer"])
    assert state.validate_document("research_state", candidate, writer=candidate["writer"]) == candidate

    before = target.read_bytes()
    stale_candidate = copy.deepcopy(candidate)
    stale_candidate["direction_ref"]["sha256"] = "b" * 64
    with pytest.raises(state.ValidationError, match="research direction_ref SHA"):
        state.replace(
            "research_state",
            target,
            candidate["writer"],
            expected_revision=1,
            input=stale_candidate,
        )
    assert target.read_bytes() == before

    with pytest.raises(state.RevisionConflictError, match="expected revision 2, observed 1"):
        state.replace(
            "research_state",
            target,
            candidate["writer"],
            expected_revision=2,
            input=candidate,
        )
    assert target.read_bytes() == before

    assert state.replace(
        "research_state",
        target,
        candidate["writer"],
        expected_revision=1,
        input=candidate,
    ) == candidate
    assert json.loads(target.read_text(encoding="utf-8")) == candidate

def test_concurrent_initialize_has_one_winner_and_losers_preserve_bytes(tmp_path: Path) -> None:
    source = FIXTURES / "research_state.json"
    target = tmp_path / "concurrent.json"

    def initialize() -> int:
        return run_cli(
            "initialize",
            "--kind",
            "research_state",
            "--path",
            str(target),
            "--writer",
            "EM-example-direction",
            "--input",
            str(source),
        ).returncode

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: initialize(), range(2)))
    assert sorted(outcomes) == [0, 4]
    assert target.read_bytes() == source.read_bytes()


def test_ignore_query_exposes_tracked_contracts_and_keeps_runtime_ignored() -> None:
    tracked = (
        ".omp/WATCHDOG.md",
        ".omp/RULES.md",
        ".omp/skills/hmasd-root-control/SKILL.md",
        "docs/research/portfolio/PORTFOLIO.md",
        "docs/research/portfolio/workflow/registry.json",
        "docs/external-review/directions/example/round/PRO_INNOVATOR_PROMPT.md",
    )
    ignored = (".omp/runtime/agents.json", "temp/directions/example/manifest.json")
    for path in tracked:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (path, result.stdout, result.stderr)
    for path in ignored:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (path, result.stdout, result.stderr)
