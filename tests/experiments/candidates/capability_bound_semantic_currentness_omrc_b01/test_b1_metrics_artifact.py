from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import (
    b1_metrics_artifact as metrics_artifact_module,
)

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.artifact import (
    canonical_json_bytes,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
    B1_INNOVATOR_SELECTION_REQUEST_ID,
    B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
    B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
    B1_LITERAL_BINDING_REQUEST_ID,
    B1_LITERAL_BINDING_RESPONSE_SHA256,
    B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
    B1_METRICS_ONLY_REQUEST_ID,
    B1_METRICS_ONLY_RESPONSE_SHA256,
    B1_METRICS_ONLY_SPEC_RELATIVE_PATH,
    B1Plan,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_artifact import (
    AUC_METADATA_FIELDS,
    B1_METRICS_TEST_SCHEMA,
    DIAGNOSTIC_METADATA_FIELDS,
    LITERAL_NULL_DERIVED_FIELDS,
    MetricsArtifactError,
    build_complete_artifact_inventory,
    build_prospective_artifact_inventory,
    build_metrics_only_manifest,
    canonicalize_metrics_table_order,
    conservative_formal_size_projection,
    materialize_metrics_only_tables,
    prepare_metrics_only_tables,
    publish_metrics_only_complete,
    require_parallel_module_protocols,
    validate_prospective_output_cap,
    validate_support_aggregate,
    validate_invocation_table_coverage,
    validate_metrics_only_manifest,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_mechanical import (
    b0_nonpolarity_record,
)


def _hex(character: str, length: int = 64) -> str:
    return character * length


def _null_packet() -> dict[str, object]:
    diagnostic_names = (
        "oracle_action_accuracy",
        "invalid_serve_rate",
        "missed_serve_rate",
        "unnecessary_refresh_rate",
        "missed_refresh_rate",
        "inactive_fallback_accuracy",
        "owner_twin_flip_accuracy",
        "semantic_twin_flip_accuracy",
        "correct_swapped_sensitivity",
        "capability_specificity",
        "retention_gap_effect",
        "owner_event_order_effect",
        "semantic_event_order_effect",
    )
    return {
        "derived_fields": {name: None for name in LITERAL_NULL_DERIVED_FIELDS},
        "auc_metadata": {name: None for name in AUC_METADATA_FIELDS},
        "diagnostic_metadata": {
            name: {field: None for field in DIAGNOSTIC_METADATA_FIELDS}
            for name in diagnostic_names
        },
    }


def _tables() -> dict[str, list[dict[str, object]]]:
    # Deliberately tiny TEST_ONLY fixtures.  Each row still exercises the
    # public canonical key and lossless JSONL boundary.
    return {
        "tape_transitions": [
            {"run_order": 0, "seed": 21101, "split_order": 0, "tape_id": 0,
             "transition_index": 0, "primitive_token_bytes": list(range(17))},
        ],
        "evaluator_decision_truth": [
            {"run_order": 0, "seed": 21101, "split_order": 1, "tape_id": 0,
             "opportunity_id": 0, "overall_valid_truth": True},
        ],
        "policy_decisions": [
            {"run_order": 0, "seed": 21101, "checkpoint_update": 0,
             "split_order": 1, "tape_id": 0, "opportunity_id": 0,
             "arm_order": 0, "selected_action": 0},
        ],
        "per_tape_curves": [
            {"run_order": 0, "seed": 21101, "split_order": 1, "tape_id": 0,
             "arm_order": 0, "episode_return_update_0": 0},
        ],
        "motif_twin_index": [
            {"run_order": 0, "seed": 21101, "tape_id": 0, "pair_id": 0,
             "member_role": "A"},
        ],
        "support_signature_counts": [
            {"run_order": 0, "run_name": "CBSC-OMRC-B1-THREE-SEED-SCOUT",
             "seed": 21101, "split_order": 1, "split": "EVAL_STOCHASTIC",
             "motif_family_or_null": None, "motif_side_or_null": None,
             "request_active": True, "access_gated": False,
             "presented_body_native_neutral": False, "address_match_truth": True,
             "payload_source_match_truth": True, "content_match_truth": True,
             "owner_match_truth": True, "epoch_match_truth": True,
             "capability_match_truth": True, "overall_valid_truth": True,
             "oracle_action": 0, "presented_body_age_opportunities": 0,
             "support_count": 1},
        ],
        "policy_support_signature_counts": [
            {"run_order": 0, "run_name": "CBSC-OMRC-B1-THREE-SEED-SCOUT",
             "seed": 21101, "split_order": 1, "split": "EVAL_STOCHASTIC",
             "motif_family_or_null": None, "motif_side_or_null": None,
             "request_active": True, "access_gated": False,
             "presented_body_native_neutral": False, "address_match_truth": True,
             "payload_source_match_truth": True, "content_match_truth": True,
             "owner_match_truth": True, "epoch_match_truth": True,
             "capability_match_truth": True, "overall_valid_truth": True,
             "oracle_action": 0, "presented_body_age_opportunities": 0,
             "arm_order": 0, "arm": "STRUCT-CURRENTNESS-GRU",
             "checkpoint_update": 0, "selected_action": 0, "support_count": 1},
        ],
        "motif_pair_support_counts": [
            {"run_order": 0, "seed": 21101, "motif_family": 0,
             "expected_pair_count": 1, "complete_pair_count": 1,
             "missing_pair_count": 0, "duplicate_member_count": 0},
        ],
        "training_decisions": [
            {"run_order": 0, "seed": 21101, "arm_order": 0,
             "training_episode_id": 0, "opportunity_id": 0, "selected_action": 0},
        ],
        "training_episodes": [
            {"run_order": 0, "seed": 21101, "arm_order": 0,
             "training_episode_id": 0, "episode_return": 0},
        ],
        "optimizer_steps": [
            {"run_order": 0, "seed": 21101, "arm_order": 0,
             "rollout_update": 0, "ppo_epoch": 0, "minibatch_index": 0,
             "optimizer_step_count": 1},
        ],
        "resource_admissions": [{"run_order": 0, "invocation_kind": "TRAINING_SLICE",
                                  "original_slot_index": 0, "attempt_order": 0,
                                  "seed": 21101, "arm_order": 0, "admitted": True}],
        "telemetry": [{"run_order": 0, "invocation_kind": "TRAINING_SLICE",
                       "original_slot_index": 0, "attempt_order": 0,
                       "seed": 21101, "arm_order": 0, "within_caps": True}],
        "audits": [{"run_order": 0, "attempt_order": 0, "seed_or_minus_one": -1,
                    "arm_or_minus_one": -1, "audit_code": "A", "passed": True}],
        "raw_competence": [{"seed": 21101,
                            "raw_competence_pass": True, "components": {}, "inputs": {}}],
    }


def _identity(staging: Path | None = None) -> dict[str, object]:
    spec_path = Path(B1_METRICS_ONLY_SPEC_RELATIVE_PATH)
    spec_sha = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    literal_path = Path(
        "docs/research/candidates/capability_bound_semantic_currentness/"
        "CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md"
    )
    decision_inventory = []
    for request_id, response_origin in (
        (B1_INNOVATOR_SELECTION_REQUEST_ID, B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH),
        (B1_LITERAL_BINDING_REQUEST_ID, B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH),
        (B1_METRICS_ONLY_REQUEST_ID, B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH),
    ):
        origin_root = Path(response_origin).parent
        for kind, filename in (
            ("RESPONSE", "RESPONSE.md"),
            ("TRANSPORT_FACTS", "TRANSPORT_FACTS.json"),
            ("PACKET_MANIFEST", "PACKET_MANIFEST.json"),
        ):
            source = origin_root / filename
            payload = source.read_bytes()
            relative = Path("evidence/pro-decisions") / request_id / filename
            if staging is not None:
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            decision_inventory.append({
                "request_id": request_id, "kind": kind,
                "origin_relative_path": source.as_posix(),
                "artifact_relative_path": relative.as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            })
    return {
        "attempt_id": "synthetic-attempt",
        "implementation_commit": _hex("a", 40),
        "source_conformance_sha256": _hex("b"),
        "configuration_sha256": hashlib.sha256(
            canonical_json_bytes(B1Plan().as_dict())
        ).hexdigest(),
        "literal_binding_spec_path": literal_path.as_posix(),
        "literal_binding_spec_sha256": hashlib.sha256(literal_path.read_bytes()).hexdigest(),
        "metrics_only_spec_path": spec_path.as_posix(),
        "metrics_only_spec_sha256": spec_sha,
        "metrics_only_response_sha256": B1_METRICS_ONLY_RESPONSE_SHA256,
        "literal_binding_response_sha256": (
            B1_LITERAL_BINDING_RESPONSE_SHA256
        ),
        "innovator_selection_request_id": B1_INNOVATOR_SELECTION_REQUEST_ID,
        "innovator_selection_archive_path": B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
        "innovator_selection_response_sha256": B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
        "literal_binding_request_id": B1_LITERAL_BINDING_REQUEST_ID,
        "literal_binding_archive_path": B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
        "metrics_only_request_id": B1_METRICS_ONLY_REQUEST_ID,
        "metrics_only_archive_path": B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
        "decision_evidence_inventory": decision_inventory,
    }


def _mechanical() -> dict[str, object]:
    return {
        "schema": "cbsc_omrc_b01_b1_mechanical_v1",
        "mechanical_attempt_complete": True,
        "mechanical_conformance_pass": True,
        "scientific_packet_readable": True,
        "blocking_audit_codes": [],
        "mechanical_components": {},
        "raw_competence_by_seed": [
            {"schema": "cbsc_omrc_b01_b1_raw_competence_v1", "seed": seed,
             "raw_competence_pass": True, "components": {}, "inputs": {}}
            for seed in (21101, 21121, 21143)
        ],
        "inputs": {"authority": "TEST_ARGUMENTS_ONLY"},
    }


def _b0(staging: Path | None = None) -> dict[str, object]:
    evaluation = {"heldout_return": 1.0}
    manifest_payload = canonical_json_bytes({
        "arm_records": [{"records": {"diagnostics": {"evaluation": evaluation}}}],
    }) + b"\n"
    worker_payload = canonical_json_bytes({
        "records": {"diagnostics": {"evaluation": evaluation}},
    }) + b"\n"
    inventory = [
        {"path": "manifest.json", "byte_count": len(manifest_payload),
         "sha256": hashlib.sha256(manifest_payload).hexdigest()},
        {"path": "workers/slot/result.json", "byte_count": len(worker_payload),
         "sha256": hashlib.sha256(worker_payload).hexdigest()},
    ]
    inventory_sha = hashlib.sha256(canonical_json_bytes(inventory)).hexdigest()
    leaf_sha = hashlib.sha256(canonical_json_bytes(1.0)).hexdigest()
    index = {
        "schema": "cbsc_omrc_b01_b0_nonpolarity_index_v1",
        "nonpolarity": b0_nonpolarity_record(),
        "evaluator_leaves": [{
            "source_relative_path": "manifest.json",
            "json_pointer": "/arm_records/0/records/diagnostics/evaluation/heldout_return",
            "value_canonical_sha256": leaf_sha,
            "scientific_eligible": False,
            "classifier_eligible": False,
            "threshold_tuning_eligible": False,
            "b2_trigger_eligible": False,
            "promotion_eligible": False,
        }, {
            "source_relative_path": "workers/slot/result.json",
            "json_pointer": "/records/diagnostics/evaluation/heldout_return",
            "value_canonical_sha256": leaf_sha,
            "scientific_eligible": False,
            "classifier_eligible": False,
            "threshold_tuning_eligible": False,
            "b2_trigger_eligible": False,
            "promotion_eligible": False,
        }],
    }
    index_payload = canonical_json_bytes(index) + b"\n"
    if staging is not None:
        evidence = staging / "b0-reviewed-evidence"
        evidence.mkdir(parents=True)
        (evidence / "manifest.json").write_bytes(manifest_payload)
        worker = evidence / "workers" / "slot" / "result.json"
        worker.parent.mkdir(parents=True)
        worker.write_bytes(worker_payload)
        index_path = staging / "b0-reviewed-index" / "nonpolarity-index.json"
        index_path.parent.mkdir(parents=True)
        index_path.write_bytes(index_payload)
    return {
        "manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "manifest_bytes": len(manifest_payload),
        "reviewed_receipt_sha256": _hex("2"),
        "inventory_sha256": inventory_sha,
        "file_count": 2, "total_bytes": len(manifest_payload) + len(worker_payload),
        "relative_root": "b0-reviewed-evidence",
        "copied_inventory_sha256": inventory_sha,
        "nonpolarity_index": {
            "relative_path": "b0-reviewed-index/nonpolarity-index.json",
            "sha256": hashlib.sha256(index_payload).hexdigest(),
            "byte_count": len(index_payload), "leaf_count": 2,
        },
    }


def _laws() -> dict[str, str]:
    return {name: _hex(character) for name, character in zip(
        ("environment", "adapter", "token", "analysis"), ("4", "5", "6", "7"),
        strict=True,
    )}


def test_plan_binds_metrics_only_spec_and_response_identity() -> None:
    plan = B1Plan().as_dict()
    assert plan["metrics_only_spec_path"] == B1_METRICS_ONLY_SPEC_RELATIVE_PATH
    assert plan["metrics_only_response_sha256"] == (
        "7a3bd74e12508e22ea577a1563737eda119c10560e094b25279503648d1105f7"
    )
    assert sorted(require_parallel_module_protocols()) == [
        "b1_mechanical", "b1_policy_records", "b1_shared_tables", "b1_training_records"
    ]


def test_metrics_bundle_is_lossless_create_only_and_literal_null(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    staging = tmp_path / "attempt.partial-test"
    staging.mkdir()
    b0 = _b0(staging)
    identity = _identity(staging)
    inventory = materialize_metrics_only_tables(
        staging, _tables(), allowed_root=tmp_path, allow_test_only=True
    )
    artifact_inventory = build_complete_artifact_inventory(staging)
    manifest = build_metrics_only_manifest(
        identity=identity, b0_evidence=b0, table_inventory=inventory,
        law_digests=_laws(),
        artifact_inventory=artifact_inventory,
        literal_nulls=_null_packet(), mechanical=_mechanical(),
        incident_references=[], test_only=True,
    )
    validated = validate_metrics_only_manifest(
        manifest, root=staging, allow_test_only=True
    )
    assert validated["schema"] == B1_METRICS_TEST_SCHEMA
    assert validated["convergence_required"] is False
    assert validated["decision"] == "DECISION_PENDING"
    assert validated["incident_claim"] == "ENGINEERING_INCIDENT_ONLY"
    assert validated["mechanical"]["inputs"]["authority"] == "TEST_ARGUMENTS_ONLY"
    assert "raw_competence_by_seed" in validated["mechanical"]
    assert "stable superiority" in validated["claim_boundary"]["explicit_exclusions"]
    assert all(value is None for value in validated["derived_fields"].values())
    assert [row["table"] for row in inventory] == list(_tables())
    origins = {
        Path(row["origin_relative_path"]).resolve()
        for row in identity["decision_evidence_inventory"]
    }
    original_read = Path.read_bytes

    def external_archive_unavailable(path: Path) -> bytes:
        if path.resolve() in origins:
            raise FileNotFoundError("external transport archive removed after snapshot")
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", external_archive_unavailable)
    validate_metrics_only_manifest(manifest, root=staging, allow_test_only=True)
    mechanical_drift = deepcopy(manifest)
    mechanical_drift["mechanical"]["mechanical_attempt_complete"] = False
    with pytest.raises(MetricsArtifactError, match="durable size"):
        validate_metrics_only_manifest(
            mechanical_drift, root=staging, allow_test_only=True
        )
    facts_path = staging / identity["decision_evidence_inventory"][1][
        "artifact_relative_path"
    ]
    facts_path.write_bytes(b"{}\n")
    with pytest.raises(MetricsArtifactError, match="Pro decision bytes"):
        validate_metrics_only_manifest(manifest, root=staging, allow_test_only=True)
    with pytest.raises(FileExistsError):
        materialize_metrics_only_tables(
            staging, _tables(), allowed_root=tmp_path, allow_test_only=True
        )


def test_metrics_bundle_rejects_reordered_rows_digest_drift_and_nonnull_derivation(
    tmp_path: Path,
) -> None:
    tables = _tables()
    tables["policy_decisions"] = [
        {**tables["policy_decisions"][0], "tape_id": 1},
        tables["policy_decisions"][0],
    ]
    with pytest.raises(MetricsArtifactError, match="canonical order"):
        materialize_metrics_only_tables(
            tmp_path / "bad-order", tables, allowed_root=tmp_path, allow_test_only=True
        )

    staging = tmp_path / "digest"
    staging.mkdir()
    b0 = _b0(staging)
    identity = _identity(staging)
    inventory = materialize_metrics_only_tables(
        staging, _tables(), allowed_root=tmp_path, allow_test_only=True
    )
    artifact_inventory = build_complete_artifact_inventory(staging)
    manifest = build_metrics_only_manifest(
        identity=identity, b0_evidence=b0, table_inventory=inventory,
        law_digests=_laws(),
        artifact_inventory=artifact_inventory,
        literal_nulls=_null_packet(), mechanical=_mechanical(),
        incident_references=[], test_only=True,
    )
    (staging / inventory[0]["relative_path"]).write_bytes(b"{}\n")
    with pytest.raises(MetricsArtifactError, match="digest"):
        validate_metrics_only_manifest(manifest, root=staging, allow_test_only=True)

    invalid = deepcopy(manifest)
    invalid["derived_fields"]["normalized_return_auc"] = 0
    with pytest.raises(MetricsArtifactError, match="literal null"):
        validate_metrics_only_manifest(invalid, root=staging, allow_test_only=True)
    (staging / inventory[0]["relative_path"]).write_bytes(
        canonical_json_bytes(_tables()["tape_transitions"][0]) + b"\n"
    )
    for field in ("maximum_claim", "explicit_exclusions", "bound_spec_sha256"):
        claim_drift = deepcopy(manifest)
        claim_drift["claim_boundary"][field] += "drift"
        with pytest.raises(MetricsArtifactError, match="claim boundary"):
            validate_metrics_only_manifest(
                claim_drift, root=staging, allow_test_only=True
            )
    missing_claim = deepcopy(manifest)
    del missing_claim["claim_boundary"]
    with pytest.raises(MetricsArtifactError, match="manifest fields"):
        validate_metrics_only_manifest(
            missing_claim, root=staging, allow_test_only=True
        )


def test_formal_manifest_is_fail_closed_until_full_module_integration() -> None:
    with pytest.raises(MetricsArtifactError, match="caller table injection is TEST_ONLY"):
        materialize_metrics_only_tables(
            Path("temp/formal-table-injection"), _tables(),
            allowed_root=Path("temp"), allow_test_only=False,
        )
    # Section-11 recast: the FORMAL_ANALYSIS_BOUND refusal is gone; a caller
    # formal build is still refused, now by the transaction witness alone.
    with pytest.raises(MetricsArtifactError, match="transaction witness"):
        build_metrics_only_manifest(
            identity=_identity(), b0_evidence=_b0(), table_inventory=[],
            law_digests=_laws(), artifact_inventory=[],
            literal_nulls=_null_packet(), mechanical=_mechanical(),
            incident_references=[], test_only=False,
        )


def test_gate_true_cannot_enable_caller_formal_build_or_publish(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(metrics_artifact_module, "FORMAL_ANALYSIS_BOUND", True)
    with pytest.raises(MetricsArtifactError, match="transaction witness"):
        build_metrics_only_manifest(
            identity=_identity(), b0_evidence=_b0(), table_inventory=[],
            law_digests=_laws(), artifact_inventory=[],
            literal_nulls=_null_packet(), mechanical=_mechanical(),
            incident_references=[], test_only=False,
        )
    with pytest.raises(MetricsArtifactError, match="only through"):
        publish_metrics_only_complete(
            staging=tmp_path / ".fake.partial-test", final_path=tmp_path / "fake",
            manifest={}, allowed_root=tmp_path, allow_test_only=False,
        )


def test_prospective_census_preserves_nested_manifest_and_publish_is_create_only(
    tmp_path: Path,
) -> None:
    final = tmp_path / "complete"
    staging = tmp_path / ".complete.partial-test"
    nested = staging / "workers" / "slot" / "manifest.json"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b"nested-provenance\n")
    b0 = _b0(staging)
    identity = _identity(staging)
    prepared = prepare_metrics_only_tables(_tables(), allow_test_only=True)
    prospective = build_prospective_artifact_inventory(staging, prepared)
    assert "workers/slot/manifest.json" in {
        row["relative_path"] for row in prospective
    }
    assert not (staging / "metrics").exists()
    inventory = materialize_metrics_only_tables(
        staging, _tables(), allowed_root=tmp_path, allow_test_only=True
    )
    artifact_inventory = build_complete_artifact_inventory(staging)
    manifest = build_metrics_only_manifest(
        identity=identity, b0_evidence=b0, law_digests=_laws(),
        table_inventory=inventory, artifact_inventory=artifact_inventory,
        literal_nulls=_null_packet(), mechanical=_mechanical(),
        incident_references=[], test_only=True,
    )
    estimate = validate_prospective_output_cap(
        artifact_inventory=artifact_inventory, manifest=manifest
    )
    published = publish_metrics_only_complete(
        staging=staging, final_path=final, manifest=manifest,
        allowed_root=tmp_path, allow_test_only=True,
    )
    assert published == final
    assert manifest["durable_size_bytes"] == estimate["total_bytes"]
    assert sum(path.stat().st_size for path in final.rglob("*") if path.is_file()) == (
        estimate["total_bytes"]
    )
    with pytest.raises(FileExistsError):
        publish_metrics_only_complete(
            staging=staging, final_path=final, manifest=manifest,
            allowed_root=tmp_path, allow_test_only=True,
        )


def test_prospective_cap_refuses_before_any_write() -> None:
    with pytest.raises(MetricsArtifactError, match="512 MiB"):
        validate_prospective_output_cap(
            artifact_inventory=[{
                "relative_path": "large.bin", "byte_count": 512 * 1024**2,
                "sha256": "0" * 64,
            }],
            manifest={
                "schema": "would-exceed",
                "durable_size_bytes": 512 * 1024**2 + 1,
            },
        )


def test_publication_canonicalizer_orders_mixed_support_and_numeric_motif_pairs() -> None:
    tables = _tables()
    support_null = tables["support_signature_counts"][0]
    support_integer = {
        **support_null, "motif_family_or_null": 0, "motif_side_or_null": "A"
    }
    tables["support_signature_counts"] = [support_integer, support_null]
    motif = tables["motif_twin_index"][0]
    tables["motif_twin_index"] = [
        {**motif, "pair_id": "21101:0:10", "member_role": "A"},
        {**motif, "pair_id": "21101:0:2", "member_role": "B"},
        {**motif, "pair_id": "21101:0:2", "member_role": "A"},
    ]
    ordered = canonicalize_metrics_table_order(tables)
    assert [row["motif_family_or_null"] for row in ordered["support_signature_counts"]] == [
        None, 0,
    ]
    assert [
        (row["pair_id"], row["member_role"])
        for row in ordered["motif_twin_index"]
    ] == [
        ("21101:0:2", "A"), ("21101:0:2", "B"), ("21101:0:10", "A"),
    ]

    duplicate = _tables()
    duplicate["policy_decisions"] = [
        duplicate["policy_decisions"][0], duplicate["policy_decisions"][0]
    ]
    with pytest.raises(MetricsArtifactError, match="duplicate canonical keys"):
        canonicalize_metrics_table_order(duplicate)


def test_conservative_formal_projection_is_result_blind_and_refuses_unfrozen_widths() -> None:
    projection = conservative_formal_size_projection()
    assert projection["table_row_upper_bounds"]["policy_decisions"] == 73_728
    assert projection["table_row_upper_bounds"]["support_signature_counts"] == 32_256
    assert projection["table_row_upper_bounds"]["policy_support_signature_counts"] == 73_728
    assert projection["table_row_upper_bounds"]["audits"] == 11_638
    assert projection["audit_upper_bound_derivation"]["total_rows"] == 11_638
    assert projection["non_table_inventory"]["checkpoint_envelopes"] == 48
    assert projection["depends_on_observed_or_test_bytes"] is False
    assert projection["projected_total_bytes"] is None
    assert projection["capacity_projection_pass"] is False
    assert projection["authority"] == "FROZEN_RESULT_BLIND_FORMAL_DESCRIPTOR"
    assert projection["performance_disposition"] == "REPAIR_REQUIRED"
    assert projection["unbounded_canonical_fields"]


def test_formal_support_tables_validate_aggregate_totals_not_decision_row_counts() -> None:
    tables = _tables()
    shared = tables["support_signature_counts"]
    policy = tables["policy_support_signature_counts"]
    shared[0]["support_count"] = 32_256
    policy[0]["support_count"] = 73_728
    validate_support_aggregate(
        "support_signature_counts", shared, expected_total=32_256
    )
    validate_support_aggregate(
        "policy_support_signature_counts", policy, expected_total=73_728
    )
    assert len(shared) == 1 and len(policy) == 1

    bad = deepcopy(shared)
    bad[0]["support_count"] = 0
    with pytest.raises(MetricsArtifactError, match="positive integer"):
        validate_support_aggregate(
            "support_signature_counts", bad, expected_total=32_256
        )
    wrong = deepcopy(shared)
    wrong[0]["support_count"] -= 1
    with pytest.raises(MetricsArtifactError, match="total differs"):
        validate_support_aggregate(
            "support_signature_counts", wrong, expected_total=32_256
        )


def test_variable_invocation_coverage_accepts_mixed_resume_and_rejects_drift() -> None:
    expected = [
        ("TRAINING_SLICE", 0, 21101, 0, 0, 0, 12),
        ("TRAINING_SLICE", 0, 21101, 0, 1, 12, 24),
        ("TRAINING_SLICE", 0, 21101, 0, 2, 24, 48),
        ("TRAINING_SLICE", 1, 21101, 1, 0, 0, 24),
        ("TRAINING_SLICE", 1, 21101, 1, 1, 24, 48),
        ("POLICY_REPLAY", 2, 21101, 2, 0, None, None),
    ]
    rows = [
        {
            "invocation_kind": kind, "original_slot_index": slot,
            "seed": seed, "arm_order": arm, "attempt_order": order,
            "slice_start_update": start, "slice_stop_update": stop,
        }
        for kind, slot, seed, arm, order, start, stop in expected
    ]
    validate_invocation_table_coverage(rows, deepcopy(rows), expected_invocation_keys=expected)
    with pytest.raises(MetricsArtifactError, match="coverage differs"):
        validate_invocation_table_coverage(
            rows[:-1], deepcopy(rows), expected_invocation_keys=expected
        )
    duplicate = [*rows[:-1], rows[0]]
    with pytest.raises(MetricsArtifactError, match="coverage differs"):
        validate_invocation_table_coverage(
            duplicate, deepcopy(rows), expected_invocation_keys=expected
        )
