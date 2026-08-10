from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.vsp_05.blind_portable_locator_dto_retained_field_admission import (
    PORTABLE_LOCATOR,
    EXPECTED_ROW_CONTAINERS,
    EXPECTED_SHA256,
    REQUIRED_SLOTS,
    SELF_DESCRIPTION_KEY,
    SELF_DESCRIPTION_KIND,
    TERMINAL_BRANCHES,
    ContractViolation,
    _branch_boundary,
    _base_result,
    _install_result_once,
    _run_component_audit,
    _validate_component_result,
    run_admission_audit,
    validate_result,
    write_result_once,
)


def _direct(path: str, declared_type: str = "string", *, nullable: bool = False) -> dict[str, object]:
    return {
        "binding_kind": "direct_field",
        "path": path,
        "declared_types": [declared_type],
        "nullable": nullable,
    }


def _described_rows(count: int = 2) -> tuple[dict[str, object], list[str]]:
    paths: list[str] = []
    groups: dict[str, dict[str, object]] = {}
    field_index = 0
    for group, slots in REQUIRED_SLOTS.items():
        groups[group] = {}
        for slot in slots:
            path = f"/retained_{field_index}"
            paths.append(path)
            groups[group][slot] = _direct(path)
            field_index += 1
    description = {
        "schema_kind": SELF_DESCRIPTION_KIND,
        "schema_version": 1,
        "row_container": "/real_frontier_rows",
        "slots": groups,
        "closed_handoff_allowlist": {
            "closed": True,
            "members": [
                {"member": "opaque_prior_flag", "binding": _direct("/allow_flag", "boolean")}
            ],
        },
    }
    rows = [
        {
            **{path[1:]: f"SECRET_SCALAR_{row_index}_{index}" for index, path in enumerate(paths)},
            "allow_flag": bool(row_index % 2),
            "opaque_number": 10_000_000 + row_index,
        }
        for row_index in range(count)
    ]
    return {SELF_DESCRIPTION_KEY: description, "real_frontier_rows": rows}, paths


def _write_registered(root: Path, payload: object) -> tuple[str, Path]:
    path = root.joinpath(*PORTABLE_LOCATOR.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest(), path


def _run_fixture(root: Path, payload: object, *, expected_rows: int = 2) -> dict[str, object]:
    digest, _ = _write_registered(root, payload)
    return _run_component_audit(
        root.resolve(), expected_sha256=digest, expected_row_containers=expected_rows
    )


def test_authenticated_complete_fixture_selects_sufficient_without_semantic_emission(tmp_path: Path) -> None:
    payload, paths = _described_rows()
    result = _run_fixture(tmp_path, payload)

    assert result["terminal_branch"] == "A4_BLIND_ADMISSION_SUFFICIENT"
    assert result["dto_binding"]["status"] == "authenticated_complete"
    assert result["counters"] == {
        "registered_admission_audits": 1,
        "locator_resolutions": 1,
        "opaque_hash_passes": 1,
        "structural_schema_passes": 1,
        "row_schema_envelopes": 2,
        "row_semantic_values_read": 0,
        "row_samples_or_presence_vectors_emitted": 0,
        "code_semantics_reads": 0,
        "new_trace_or_hypothetical_activity": 0,
        "environment_policy_executor_learning_training_optimizer_evaluation_activity": 0,
        "retry_rescue_or_fallback": 0,
    }
    encoded_result = json.dumps(result, sort_keys=True)
    assert "SECRET_SCALAR" not in encoded_result
    assert "10000000" not in encoded_result
    assert result["source_binding"]["normalized_relative_locator"] == PORTABLE_LOCATOR
    assert result["source_binding"]["absolute_path_emitted"] is False
    assert str(tmp_path) not in repr(result)
    assert {entry["path"] for entry in result["schema_presence_manifest"]} >= set(paths)


def test_missing_and_ambiguous_self_description_naturally_select_branch_three(tmp_path: Path) -> None:
    missing = _run_fixture(tmp_path / "missing", {"real_frontier_rows": [{}, {}]})
    assert missing["terminal_branch"] == "A4_DTO_SEMANTIC_BINDING_UNAVAILABLE"
    assert missing["dto_binding"]["slots"]["actual_executor"]["real primitive command"]["source_path"] is None

    payload, _ = _described_rows()
    descriptor = payload[SELF_DESCRIPTION_KEY]["slots"]["actual_executor"]["real primitive command"]
    descriptor["path"] = ["/retained_0", "/retained_1"]
    ambiguous = _run_fixture(tmp_path / "ambiguous", payload)
    assert ambiguous["terminal_branch"] == "A4_DTO_SEMANTIC_BINDING_UNAVAILABLE"
    assert "exact JSON pointer" in ambiguous["first_failure"]


def test_exact_registered_row_envelope_cap_is_counted_without_reading_values(tmp_path: Path) -> None:
    payload = {"real_frontier_rows": [{} for _ in range(EXPECTED_ROW_CONTAINERS)]}
    result = _run_fixture(tmp_path, payload, expected_rows=EXPECTED_ROW_CONTAINERS)
    assert result["terminal_branch"] == "A4_DTO_SEMANTIC_BINDING_UNAVAILABLE"
    assert result["counters"]["row_schema_envelopes"] == EXPECTED_ROW_CONTAINERS
    assert result["counters"]["row_semantic_values_read"] == 0


def test_authenticated_binding_with_partial_presence_selects_only_branch_four(tmp_path: Path) -> None:
    payload, paths = _described_rows()
    missing_path = paths[-1][1:]
    del payload["real_frontier_rows"][1][missing_path]
    result = _run_fixture(tmp_path, payload)

    assert result["terminal_branch"] == "A4_REQUIRED_RETENTION_INCOMPLETE"
    slot = next(
        receipt
        for group in result["dto_binding"]["slots"].values()
        for receipt in group.values()
        if receipt["source_path"] == paths[-1]
    )
    assert slot["presence"] == "incomplete"
    assert slot["schema_evidence"][0]["present_rows"] == 1
    assert "SECRET_SCALAR" not in json.dumps(result)


def test_explicit_subject_indexed_structure_is_admissible(tmp_path: Path) -> None:
    payload, _ = _described_rows()
    slot = payload[SELF_DESCRIPTION_KEY]["slots"]["same_subject_current_frontier"]["same-current-time hard gate G_i"]
    payload[SELF_DESCRIPTION_KEY]["slots"]["same_subject_current_frontier"]["same-current-time hard gate G_i"] = {
        "binding_kind": "subject_indexed_field",
        "path_template": "/subject_table/{subject}/gate",
        "subject_keys": ["a", "b"],
        "subject_role": "actual_persisted_incumbent",
        "declared_types": ["boolean"],
        "nullable": False,
    }
    for row in payload["real_frontier_rows"]:
        row["subject_table"] = {"a": {"gate": True}, "b": {"gate": False}}
    del slot
    result = _run_fixture(tmp_path, payload)
    assert result["terminal_branch"] == "A4_BLIND_ADMISSION_SUFFICIENT"
    receipt = result["dto_binding"]["slots"]["same_subject_current_frontier"]["same-current-time hard gate G_i"]
    assert receipt["binding_basis"] == "subject_indexed_field"
    assert len(receipt["schema_evidence"]) == 2


@pytest.mark.parametrize(
    "locator",
    [
        "/absolute/raw_result.json",
        "../raw_result.json",
        "logs\\vsp05_a1_truth_reachability_1a09bccf_r1\\raw_result.json",
        "logs/./vsp05_a1_truth_reachability_1a09bccf_r1/raw_result.json",
        "logs/alternate/raw_result.json",
        "logs//vsp05_a1_truth_reachability_1a09bccf_r1/raw_result.json",
    ],
)
def test_locator_rejects_absolute_traversal_reencoding_and_alternates(tmp_path: Path, locator: str) -> None:
    result = _run_component_audit(
        tmp_path.resolve(), portable_locator=locator, expected_sha256="0" * 64,
        expected_row_containers=0,
    )
    assert result["terminal_branch"] == "A4_IMMUTABLE_SOURCE_OR_PORTABLE_LOCATOR_INVALID"
    assert result["counters"]["opaque_hash_passes"] == 0
    assert result["counters"]["structural_schema_passes"] == 0
    assert result["source_binding"]["normalized_relative_locator"] is None


def test_relative_checkout_root_is_rejected_without_cwd_substitution(tmp_path: Path) -> None:
    result = _run_component_audit(Path("relative-root"), expected_sha256="0" * 64, expected_row_containers=0)
    assert result["terminal_branch"] == "A4_IMMUTABLE_SOURCE_OR_PORTABLE_LOCATOR_INVALID"
    assert result["source_binding"]["verified_checkout_root_supplied"] is False
    assert "cwd substitution" in result["first_failure"]


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    link = root.joinpath(*PORTABLE_LOCATOR.split("/"))
    link.parent.mkdir(parents=True)
    try:
        os.symlink(outside, link)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    result = _run_component_audit(root.resolve(), expected_sha256="0" * 64, expected_row_containers=0)
    assert result["terminal_branch"] == "A4_IMMUTABLE_SOURCE_OR_PORTABLE_LOCATOR_INVALID"
    assert "escapes checkout root" in result["first_failure"]
    assert result["counters"]["opaque_hash_passes"] == 0


def test_hash_parse_and_cardinality_fail_before_dto_binding(tmp_path: Path) -> None:
    payload, _ = _described_rows()
    digest, path = _write_registered(tmp_path / "hash", payload)
    hash_failure = _run_component_audit(
        (tmp_path / "hash").resolve(), expected_sha256="0" * 64, expected_row_containers=2
    )
    assert hash_failure["terminal_branch"] == "A4_IMMUTABLE_SOURCE_OR_PORTABLE_LOCATOR_INVALID"
    assert hash_failure["counters"]["opaque_hash_passes"] == 1
    assert hash_failure["counters"]["structural_schema_passes"] == 0
    assert hash_failure["source_binding"]["observed_sha256"] == digest
    assert hash_failure["source_binding"]["observed_sha256"] != hash_failure["source_binding"]["expected_sha256"]
    assert hash_failure["source_binding"]["parser_status"] == "not_started"

    invalid_root = tmp_path / "parse"
    invalid_digest, _ = _write_registered(invalid_root, {"real_frontier_rows": []})
    invalid_path = invalid_root.joinpath(*PORTABLE_LOCATOR.split("/"))
    invalid_path.write_bytes(b'{"real_frontier_rows":[{"x":"opaque"},{"x":SECRET}]}')
    invalid_digest = hashlib.sha256(invalid_path.read_bytes()).hexdigest()
    parse_failure = _run_component_audit(
        invalid_root.resolve(), expected_sha256=invalid_digest, expected_row_containers=2
    )
    assert parse_failure["terminal_branch"] == "A4_IMMUTABLE_SOURCE_OR_PORTABLE_LOCATOR_INVALID"
    assert parse_failure["source_binding"]["parser_status"] == "invalid"
    assert parse_failure["counters"]["structural_schema_passes"] == 1
    assert parse_failure["counters"]["row_schema_envelopes"] == 1

    cardinality = _run_component_audit(
        (tmp_path / "hash").resolve(), expected_sha256=digest, expected_row_containers=3
    )
    assert cardinality["terminal_branch"] == "A4_IMMUTABLE_SOURCE_OR_PORTABLE_LOCATOR_INVALID"
    assert cardinality["source_binding"]["observed_row_containers"] == 2
    assert cardinality["counters"]["row_schema_envelopes"] == 2


def test_scope_cap_precedence_and_claim_validation_are_tamper_evident(tmp_path: Path) -> None:
    payload, _ = _described_rows()
    result = _run_fixture(tmp_path, payload)
    over_cap_payload, _ = _described_rows(count=3)
    over_cap = _run_fixture(tmp_path / "over-cap", over_cap_payload, expected_rows=2)
    assert over_cap["terminal_branch"] == TERMINAL_BRANCHES[0]
    assert over_cap["first_failure"] == "hard cap exceeded: row_schema_envelopes"

    scope_failure = deepcopy(result)
    scope_failure["scope_violations"] = ["synthetic scope observer fired"]
    scope_failure["terminal_branch"] = TERMINAL_BRANCHES[0]
    scope_failure["first_failure"] = "synthetic scope observer fired"
    scope_failure["strongest_alternative"], scope_failure["residual_uncertainty"] = _branch_boundary(TERMINAL_BRANCHES[0])
    _validate_component_result(scope_failure, expected_row_containers=2)

    tampered = deepcopy(result)
    tampered["counters"]["row_semantic_values_read"] = 1
    tampered["attestations"]["semantic_values_read"] = 1
    tampered["terminal_branch"] = TERMINAL_BRANCHES[0]
    tampered["first_failure"] = "hard cap exceeded: row_semantic_values_read"
    with pytest.raises(ContractViolation, match="semantic-value blindness"):
        _validate_component_result(tampered, expected_row_containers=2)

    stale_branch = deepcopy(result)
    stale_branch["terminal_branch"] = TERMINAL_BRANCHES[3]
    stale_branch["first_failure"] = "fabricated"
    with pytest.raises(ContractViolation, match="terminal branch precedence"):
        _validate_component_result(stale_branch, expected_row_containers=2)

    reopened = deepcopy(result)
    reopened["attestations"]["source_reopened_after_structural_pass"] = True
    with pytest.raises(ContractViolation, match="source-reopen attestation"):
        _validate_component_result(reopened, expected_row_containers=2)

    absolute_identity = deepcopy(result)
    absolute_identity["attestations"]["environment_specific_absolute_identity_emitted"] = True
    with pytest.raises(ContractViolation, match="absolute-identity attestation"):
        _validate_component_result(absolute_identity, expected_row_containers=2)


def test_component_one_shot_installer_refuses_overwrite_after_component_validation(tmp_path: Path) -> None:
    payload, _ = _described_rows()
    result = _run_fixture(tmp_path / "input", payload)
    _validate_component_result(result, expected_row_containers=2)
    output = tmp_path / "result.json"
    _install_result_once(output, result)
    published = json.loads(output.read_text(encoding="utf-8"))
    assert published["terminal_branch"] == "A4_BLIND_ADMISSION_SUFFICIENT"
    with pytest.raises(FileExistsError, match="one-shot A4"):
        _install_result_once(output, result)


def test_production_writer_rejects_component_unrun_and_reviewer_fabrication(tmp_path: Path) -> None:
    payload, _ = _described_rows()
    component = _run_fixture(tmp_path / "component", payload)
    component_output = tmp_path / "component.json"
    with pytest.raises(ContractViolation, match="production expected SHA-256"):
        write_result_once(component_output, component)
    assert not component_output.exists()

    supplied_cardinality = deepcopy(component)
    supplied_cardinality["source_binding"]["expected_sha256"] = EXPECTED_SHA256
    supplied_cardinality["source_binding"]["observed_sha256"] = EXPECTED_SHA256
    with pytest.raises(ContractViolation, match="production expected row cardinality"):
        write_result_once(tmp_path / "supplied-cardinality.json", supplied_cardinality)

    unrun = _base_result(PORTABLE_LOCATOR)
    with pytest.raises(ContractViolation, match="not one executed registered admission audit"):
        write_result_once(tmp_path / "unrun.json", unrun)

    fabricated = _base_result(PORTABLE_LOCATOR)
    fabricated["counters"]["registered_admission_audits"] = 1
    fabricated["counters"]["locator_resolutions"] = 1
    fabricated["source_binding"]["first_failure"] = "reviewer fabricated source failure"
    fabricated["source_binding"]["parser_status"] = "valid"
    fabricated["terminal_branch"] = TERMINAL_BRANCHES[1]
    fabricated["first_failure"] = "reviewer fabricated source failure"
    fabricated["strongest_alternative"], fabricated["residual_uncertainty"] = _branch_boundary(TERMINAL_BRANCHES[1])
    with pytest.raises(ContractViolation, match="parser started without a structural pass"):
        write_result_once(tmp_path / "fabricated.json", fabricated)
    assert not (tmp_path / "fabricated.json").exists()

    tampered = deepcopy(component)
    tampered["source_binding"]["accepted_source_commit"] = "0" * 40
    with pytest.raises(ContractViolation, match="accepted source commit"):
        _validate_component_result(tampered, expected_row_containers=2)

    injected = deepcopy(component)
    injected["row_sample"] = {"forbidden": "SECRET_SCALAR"}
    with pytest.raises(ContractViolation, match="top-level result envelope"):
        _validate_component_result(injected, expected_row_containers=2)


def test_matching_frozen_hash_cannot_publish_without_structural_parser_advance(tmp_path: Path) -> None:
    fabricated = _base_result(PORTABLE_LOCATOR)
    fabricated["counters"]["registered_admission_audits"] = 1
    fabricated["counters"]["locator_resolutions"] = 1
    fabricated["counters"]["opaque_hash_passes"] = 1
    fabricated["source_binding"].update({
        "first_failure": "fabricated early stop after successful hash",
        "verified_checkout_root_supplied": True,
        "root_containment": True,
        "normalized_relative_locator": PORTABLE_LOCATOR,
        "observed_sha256": EXPECTED_SHA256,
        "opaque_bytes_read": 1,
    })
    fabricated["terminal_branch"] = TERMINAL_BRANCHES[1]
    fabricated["first_failure"] = "fabricated early stop after successful hash"
    fabricated["strongest_alternative"], fabricated["residual_uncertainty"] = _branch_boundary(TERMINAL_BRANCHES[1])
    output = tmp_path / "hash-success-parser-not-started.json"
    with pytest.raises(ContractViolation, match="matching immutable SHA must advance exactly one structural pass"):
        write_result_once(output, fabricated)
    assert not output.exists()


def test_runner_help_exposes_only_checkout_root_and_one_shot_output() -> None:
    assert list(inspect.signature(run_admission_audit).parameters) == ["checkout_root"]
    assert list(inspect.signature(validate_result).parameters) == ["result"]
    runner = Path(__file__).resolve().parents[4] / "scripts" / "run_vsp05_a4_blind_portable_locator_dto_retained_field_admission.py"
    completed = subprocess.run(
        [sys.executable, str(runner), "--help"], check=True, capture_output=True, text=True
    )
    assert "--checkout-root" in completed.stdout
    assert "--output" in completed.stdout
    assert "--input" not in completed.stdout
    assert "--locator" not in completed.stdout
