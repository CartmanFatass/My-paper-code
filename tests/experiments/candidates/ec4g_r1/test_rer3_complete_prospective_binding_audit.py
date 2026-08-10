from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.ec4g_r1.rer3_complete_prospective_binding_audit import (
    AuditBranch,
    BINDING_PATH,
    C0_COMMIT,
    C0_CONTRACT_BLOB_OID,
    C0_CONTRACT_SHA256,
    CONTRACT_PATH,
    MappingSnapshotReader,
    PostFreezeEvent,
    ROLE_ORDER,
    _scientific_issues,
    audit_frozen_pair,
    canonical_json_bytes,
    derive_binding_record,
    derive_binding_record_bytes,
    freeze_snapshot_pair,
    git_blob_oid,
    parse_strict_json,
)


C1_COMMIT = "a" * 40
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def _contract_bytes() -> bytes:
    # The Windows checkout may be CRLF-smudged; the immutable Git C0 blob is LF.
    raw = (REPOSITORY_ROOT / CONTRACT_PATH).read_bytes()
    return raw.replace(b"\r\n", b"\n")


def _contract() -> dict[str, object]:
    value = parse_strict_json(_contract_bytes())
    assert isinstance(value, dict)
    return value


def _binding() -> dict[str, object]:
    value = parse_strict_json((REPOSITORY_ROOT / BINDING_PATH).read_bytes(), require_canonical=True)
    assert isinstance(value, dict)
    return value


def _pair(*, contract_bytes: bytes | None = None, binding_bytes: bytes | None = None):
    contract_bytes = _contract_bytes() if contract_bytes is None else contract_bytes
    binding_bytes = (
        derive_binding_record_bytes(parse_strict_json(contract_bytes))
        if binding_bytes is None
        else binding_bytes
    )
    return freeze_snapshot_pair(
        MappingSnapshotReader(C0_COMMIT, {CONTRACT_PATH: contract_bytes}),
        MappingSnapshotReader(C1_COMMIT, {BINDING_PATH: binding_bytes}),
        expected_c1_commit=C1_COMMIT,
    )


def _audit(frozen=None, **kwargs) -> dict[str, object]:
    return audit_frozen_pair(
        _pair() if frozen is None else frozen,
        run_id="fixture-a3-run",
        **kwargs,
    ).payload()


def _mutated_binding(mutator) -> bytes:
    record = derive_binding_record(_contract())
    mutator(record)
    return canonical_json_bytes(record) + b"\n"


def test_c0_worktree_materialization_normalizes_to_the_exact_read_only_blob_identity():
    content = _contract_bytes()

    assert hashlib.sha256(content).hexdigest() == C0_CONTRACT_SHA256
    assert git_blob_oid(content) == C0_CONTRACT_BLOB_OID
    assert derive_binding_record_bytes(_contract()) == (REPOSITORY_ROOT / BINDING_PATH).read_bytes()


def test_binding_record_is_exact_canonical_deterministic_fourteen_row_derivation():
    record = _binding()

    assert len(record["bindings"]) == 14
    assert record["role_order"] == list(ROLE_ORDER)
    assert "c1_commit" not in record
    assert all(row["ordinal"] == ordinal for ordinal, row in enumerate(record["bindings"]))
    assert all(row["json_pointer"].startswith("/") for row in record["bindings"])
    assert all(row["source_commit"] == C0_COMMIT and row["total"] is True for row in record["bindings"])
    assert all(row["coherence"] == record["coherence"] for row in record["bindings"])


def test_complete_pair_inspects_exact_counts_and_never_executes_forbidden_activity():
    payload = _audit()

    assert payload["terminal_branch"] == AuditBranch.COMPLETE_PROSPECTIVE_CONTRACT_BINDING.value
    assert payload["first_failure"] is None
    assert len(payload["role_witness_table"]) == 14
    assert {row["status"] for row in payload["role_witness_table"]} == {"BOUND"}
    counts = payload["activity_counts"]
    assert counts["inventory_freezes"] == 1
    assert counts["scientific_inventory_blobs"] == 2
    assert counts["role_inspections"] == 14
    assert counts["declared_cells"] == 3
    assert counts["declared_arms"] == 21
    assert counts["declared_outcome_support_points"] == 243
    for key in (
        "environment_transitions",
        "policy_calls",
        "learner_calls",
        "trainer_calls",
        "optimizer_updates",
        "return_evaluations",
        "model_fits",
        "stochastic_calls",
        "map_calls",
        "program_compilations",
        "program_comparisons",
        "d_rer3_calculations",
        "sweeps",
        "retries",
        "rescues",
        "rescans",
    ):
        assert counts[key] == 0


@pytest.mark.parametrize(
    "binding_bytes",
    (
        b'\xff{"schema_version":1}\n',
        b'{"bindings":[],"bindings":[],"schema_version":1}\n',
        b'{"bindings":[],"schema_version":NaN}\n',
        b'{ "bindings": [], "schema_version": 1 }\n',
    ),
)
def test_strict_utf8_duplicate_nonfinite_and_canonical_mutations_invalidate_freeze(binding_bytes):
    payload = _audit(_pair(binding_bytes=binding_bytes))

    assert payload["terminal_branch"] == AuditBranch.FREEZE_PAIR_INVALID.value
    assert payload["activity_counts"]["role_inspections"] == 0
    assert payload["freeze_witnesses"][0]["code"] == "C1_BINDING_JSON_INVALID"


def test_any_c0_byte_mutation_fails_the_exact_blob_and_sha_identity_before_inspection():
    payload = _audit(_pair(contract_bytes=_contract_bytes() + b" "))

    assert payload["terminal_branch"] == AuditBranch.FREEZE_PAIR_INVALID.value
    assert payload["activity_counts"]["role_inspections"] == 0
    assert {item["code"] for item in payload["freeze_witnesses"]} >= {
        "C0_CONTRACT_BLOB_MISMATCH",
        "C0_CONTRACT_SHA256_MISMATCH",
    }


def test_c1_self_reference_invalidates_the_freeze_pair():
    encoded = _mutated_binding(lambda record: record.update(containing_commit=C1_COMMIT))
    payload = _audit(_pair(binding_bytes=encoded))

    assert payload["terminal_branch"] == AuditBranch.FREEZE_PAIR_INVALID.value
    assert payload["freeze_witnesses"][0]["code"] == "C1_SELF_REFERENCE"


def test_post_freeze_change_precedes_all_role_inspection():
    event = PostFreezeEvent("IMPORT_PATH", "attempted post-freeze substitute", "docs/substitute.json")
    payload = _audit(_pair(), post_freeze_events=(event,))

    assert payload["terminal_branch"] == AuditBranch.POST_FREEZE_CHANGE_OR_IMPORT.value
    assert payload["first_failure"] == event.payload()
    assert payload["activity_counts"]["role_inspections"] == 0


def test_ambiguous_binding_precedes_missing_and_retains_both_witness_sets():
    def mutate(record):
        record["bindings"].append(deepcopy(record["bindings"][0]))
        record["bindings"] = [row for row in record["bindings"] if row["role"] != "deployed_measure_m"]

    payload = _audit(_pair(binding_bytes=_mutated_binding(mutate)))

    assert payload["terminal_branch"] == AuditBranch.AMBIGUOUS_ROLE_BINDING.value
    assert payload["first_failure"]["role"] == "objective_contract"
    assert [item["role"] for item in payload["missing_witnesses"]] == ["deployed_measure_m"]


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    (
        ("total", False, "BINDING_FIELD_MISMATCH"),
        ("json_pointer", "/objective_contract", "BINDING_FIELD_MISMATCH"),
        ("source_commit", "b" * 40, "BINDING_FIELD_MISMATCH"),
        ("source_blob_oid", "0" * 40, "BINDING_FIELD_MISMATCH"),
        ("source_blob_sha256", "0" * 64, "BINDING_FIELD_MISMATCH"),
        ("subtree_sha256", "0" * 64, "SUBTREE_SHA256_MISMATCH"),
    ),
)
def test_each_protected_binding_mutation_fails_closed_without_repair(field, value, expected_code):
    def mutate(record):
        record["bindings"][4][field] = value

    payload = _audit(_pair(binding_bytes=_mutated_binding(mutate)))
    codes = {item["code"] for item in payload["incoherent_witnesses"]}

    assert payload["terminal_branch"] == AuditBranch.PARTIAL_OR_SCIENTIFICALLY_INCOHERENT_CONTRACT.value
    assert expected_code in codes
    assert payload["route_status"] == "STOPPED_WITHOUT_REPAIR_RETRY_RESCAN_IMPUTATION_OR_SUBSTITUTE"


def test_coherence_mutation_is_rejected_at_row_and_cross_record_levels():
    def mutate(record):
        record["bindings"][9]["coherence"]["domain_id"] = "other-domain"

    payload = _audit(_pair(binding_bytes=_mutated_binding(mutate)))
    codes = {item["code"] for item in payload["incoherent_witnesses"]}

    assert payload["terminal_branch"] == AuditBranch.PARTIAL_OR_SCIENTIFICALLY_INCOHERENT_CONTRACT.value
    assert "BINDING_FIELD_MISMATCH" in codes


def test_row_reordering_or_unrecognized_extra_row_is_never_accepted_as_exact_fourteen_order():
    def reorder(record):
        record["bindings"][0], record["bindings"][1] = record["bindings"][1], record["bindings"][0]

    reordered = _audit(_pair(binding_bytes=_mutated_binding(reorder)))
    assert reordered["terminal_branch"] == AuditBranch.PARTIAL_OR_SCIENTIFICALLY_INCOHERENT_CONTRACT.value
    assert "BINDING_ROW_ORDER_MISMATCH" in {item["code"] for item in reordered["incoherent_witnesses"]}

    def append_unknown(record):
        row = deepcopy(record["bindings"][0])
        row.update(role="unknown_role", object_id="unknown", ordinal=14, json_pointer="/objective_contract")
        record["bindings"].append(row)

    extra = _audit(_pair(binding_bytes=_mutated_binding(append_unknown)))
    assert extra["terminal_branch"] == AuditBranch.PARTIAL_OR_SCIENTIFICALLY_INCOHERENT_CONTRACT.value
    assert "BINDING_ROW_ORDER_MISMATCH" in {item["code"] for item in extra["incoherent_witnesses"]}


@pytest.mark.parametrize(
    ("mutator", "expected_code"),
    (
        (lambda value: value["seven_arm_mean_and_covariance"]["noise"].update(probabilities=["0.25", "0.50", "0.24"]), "OUTCOME_SUPPORT_MISMATCH"),
        (lambda value: value["seven_arm_mean_and_covariance"]["covariance"].update(diagonal=["-0.5", "0.5", "0.5", "0.5", "0", "0", "0"]), "COVARIANCE_NOT_DECLARED_PSD"),
        (lambda value: value["cost_object"]["net_mean_by_cell_in_arm_order"]["k_join"].__setitem__(1, 13), "ONE_TIME_COST_SUBTRACTION_MISMATCH"),
        (lambda value: value["support_predicate_s"].update(map_independent=False), "TOTAL_DEFINITION_MISMATCH"),
        (lambda value: value["deployed_measure_m"]["values"].update(k_join="0.49"), "DEPLOYED_MEASURE_MISMATCH"),
    ),
)
def test_scientific_literal_validators_reject_probability_psd_cost_support_and_mass_mutations(mutator, expected_code):
    contract = deepcopy(_contract())
    mutator(contract)

    issues, _checks, _normalization, _counts = _scientific_issues(contract)

    assert expected_code in {item["code"] for item in issues}


def test_result_retains_two_source_identities_locators_and_pending_cpm_owned_ids():
    payload = _audit()

    assert payload["frozen_pair"]["c0_commit"] == C0_COMMIT
    assert payload["frozen_pair"]["c1_commit"] == C1_COMMIT
    assert len(payload["frozen_pair"]["entries"]) == 2
    assert payload["public_locators"]["contract"].endswith(CONTRACT_PATH)
    assert payload["public_locators"]["binding_record"].endswith(BINDING_PATH)
    assert payload["technical_acceptance"]["owner"] == "code_project_manager"
    assert payload["technical_acceptance"]["status"].startswith("pending_")
    assert payload["execution_readiness"]["status"].startswith("pending_")
    assert payload["result_id"].startswith("ec4g-a3-")


def test_runner_preflights_existing_output_before_source_or_snapshot_inspection(monkeypatch, tmp_path):
    from scripts import run_ec4g_a3_rer3_complete_prospective_binding_audit as runner

    output = tmp_path / "existing.json"
    output.write_text("existing", encoding="utf-8")
    monkeypatch.setattr(runner, "_actual_c1_commit", lambda: pytest.fail("source inspection forbidden"))
    monkeypatch.setattr(runner, "freeze_repository_pair", lambda *_args: pytest.fail("freeze forbidden"))

    with pytest.raises(SystemExit, match="refusing to overwrite"):
        runner.main(["--c1-commit", C1_COMMIT, "--run-id", "fixture", "--output", str(output)])
    assert output.read_text(encoding="utf-8") == "existing"


def test_runner_rejects_declared_c1_that_is_not_the_actual_checkout(monkeypatch, tmp_path):
    from scripts import run_ec4g_a3_rer3_complete_prospective_binding_audit as runner

    monkeypatch.setattr(runner, "_actual_c1_commit", lambda: C1_COMMIT)
    monkeypatch.setattr(runner, "freeze_repository_pair", lambda *_args: pytest.fail("freeze forbidden"))

    with pytest.raises(SystemExit, match="C1 commit mismatch"):
        runner.main(["--c1-commit", "b" * 40, "--run-id", "fixture", "--output", str(tmp_path / "new.json")])


def test_runner_writes_one_canonical_registered_result(monkeypatch, tmp_path):
    from scripts import run_ec4g_a3_rer3_complete_prospective_binding_audit as runner

    output = tmp_path / "result.json"
    frozen = _pair()
    monkeypatch.setattr(runner, "_actual_c1_commit", lambda: C1_COMMIT)
    monkeypatch.setattr(runner, "freeze_repository_pair", lambda _root, _c1: frozen)

    assert runner.main(["--c1-commit", C1_COMMIT, "--run-id", "fixture", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["terminal_branch"] == AuditBranch.COMPLETE_PROSPECTIVE_CONTRACT_BINDING.value
    assert payload["activity_counts"]["registered_audit_runs"] == 1
    assert output.read_bytes() == canonical_json_bytes(payload) + b"\n"
