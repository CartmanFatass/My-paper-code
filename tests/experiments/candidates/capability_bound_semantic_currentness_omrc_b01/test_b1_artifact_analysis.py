from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b0 import ARMS
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1_CHECKPOINT_UPDATES,
    B1_LEDGER_PUBLICATION_MODE,
    B1_LEDGER_SCHEMA,
    B1_RUN_NAME,
    B1_SEEDS,
    B1_SLOT_ORDER,
    B1AttemptLedger,
    B1LedgerBinding,
    B1Plan,
    B1ResumeCheckpointBinding,
    B1SlotLedgerEntry,
    B1SlotStatus,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import Action
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.evaluator import (
    evaluate_episode,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import DynamicHost
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_analysis import (
    B1AnalysisError,
    FORMAL_ANALYSIS_BOUND,
    compute_b1_analysis,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_artifact import (
    B1ArtifactError,
    B1_RESULT_SCHEMA,
    B1_TEST_RESULT_SCHEMA,
    create_b1_staging_directory,
    load_b1_attempt_ledger,
    load_b1_attempt_ledger_from_incident,
    make_b1_incident_lineage_witness,
    materialize_b1_incident_lineage,
    publish_b1_complete,
    publish_b1_incident,
    publish_b1_attempt_ledger,
    validate_b1_attempt_ledger_document,
    validate_b1_complete_manifest,
    validate_b1_incident_lineage,
)


def _ratio(value: Fraction | int) -> dict[str, int | float]:
    exact = Fraction(value)
    return {
        "numerator": exact.numerator,
        "denominator": exact.denominator,
        "float": float(exact),
    }


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _raw_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for arm_index, arm in enumerate(ARMS):
        for seed_index, seed in enumerate(B1_SEEDS):
            for update in B1_CHECKPOINT_UPDATES:
                episodes: list[dict[str, object]] = []
                for panel in ("EVAL_STOCHASTIC", "EVAL_MOTIF"):
                    for episode_id in range(32):
                        value = Fraction(update + arm_index + seed_index, 10)
                        episodes.append(
                            {
                                "identity": {
                                    "run_name": B1_RUN_NAME,
                                    "seed": seed,
                                    "split": panel,
                                    "episode_id": episode_id,
                                },
                                "return": _ratio(value),
                                "oracle_return": _ratio(20),
                                "oracle_regret": _ratio(Fraction(20, 1) - value),
                                "action_counts": {
                                    "SERVE": 8,
                                    "REFRESH": 8,
                                    "SAFE_FALLBACK": 8,
                                },
                                "diagnostic_counts": {
                                    "oracle_action_correct": 8,
                                    "invalid_serve": 1,
                                    "missed_serve": 2,
                                    "unnecessary_refresh": 3,
                                    "missed_refresh": 4,
                                    "inactive_fallback": 5,
                                },
                                # These are evaluator facts, preserved rather than
                                # aggregated until the pending literal analysis law.
                                "decisions": [
                                    {
                                        "opportunity_index": opportunity,
                                        "action": ("SERVE", "REFRESH", "SAFE_FALLBACK")[
                                            opportunity % 3
                                        ],
                                        "oracle_action": "SERVE",
                                        "valid": opportunity % 2 == 0,
                                        "request_active": opportunity % 4 != 0,
                                        "decision_reward": _ratio(0),
                                        "settlement_reward": _ratio(0),
                                        "regret": _ratio(0),
                                        "motif_family": episode_id if panel == "EVAL_MOTIF" else None,
                                        "motif_side": ("A", "B")[episode_id % 2]
                                        if panel == "EVAL_MOTIF"
                                        else None,
                                        "designated_comparison": panel == "EVAL_MOTIF",
                                    }
                                    for opportunity in range(24)
                                ],
                            }
                        )
                records.append(
                    {
                        "schema": "cbsc_omrc_b01_b1_raw_checkpoint_evaluation_v1",
                        "run_name": B1_RUN_NAME,
                        "arm": arm,
                        "seed": seed,
                        "checkpoint_update": update,
                        "checkpoint_identity": f"{arm}-{seed}-update-{update}",
                        "numerical_finite": True,
                        "invalid_masking_count": 0,
                        "episodes": episodes,
                    }
                )
    return records


def _test_manifest(analysis: dict[str, object]) -> dict[str, object]:
    plan = B1Plan()
    arm_seed_records = []
    admissions = []
    telemetry = []
    checkpoint_identities = []
    for arm in ARMS:
        for seed in B1_SEEDS:
            identities = [f"{arm}-{seed}-update-{update}" for update in B1_CHECKPOINT_UPDATES]
            checkpoint_identities.extend(identities)
            arm_seed_records.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "counts": plan.counts_per_arm_seed,
                    "checkpoint_identities": identities,
                    "complete": True,
                }
            )
            admissions.append({"arm": arm, "seed": seed, "admitted": True})
            telemetry.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "within_caps": True,
                    "process_tree_peak_rss_bytes": 1,
                    "scratch_high_water_bytes": 0,
                    "durable_high_water_bytes": 1,
                    "wall_seconds": 1.0,
                }
            )
    return {
        "schema": B1_TEST_RESULT_SCHEMA,
        "test_only": True,
        "object_id": "CBSC-OMRC-B01",
        "clarification_id": "cbsc-online-b-innovator-20260901-02",
        "run_name": B1_RUN_NAME,
        "implementation_commit": "a" * 40,
        "source_conformance_sha256": "b" * 64,
        "b0_evidence": {
            "manifest_sha256": "9" * 64,
            "manifest_bytes": 12_807_274,
            "reviewed_receipt_sha256": "8" * 64,
            "inventory_sha256": "184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5",
            "file_count": 33,
            "total_bytes": 12_807_274,
        },
        "pinned_evidence_ref": "c" * 40,
        "evidence_sha256": _canonical_sha256(analysis["raw_checkpoint_records"]),
        "configuration_sha256": _canonical_sha256(plan.as_dict()),
        "law_digests": {
            "environment": "1" * 64,
            "adapter": "2" * 64,
            "token": "3" * 64,
            "analysis": "4" * 64,
        },
        "arms": list(ARMS),
        "seeds": list(B1_SEEDS),
        "checkpoint_updates": list(B1_CHECKPOINT_UPDATES),
        "checkpoint_identities": checkpoint_identities,
        "counts": {
            "arm_seed_count": 12,
            "per_arm_seed": plan.counts_per_arm_seed,
        },
        "arm_seed_records": arm_seed_records,
        "analysis": analysis,
        "resource_caps": plan.resource_caps.as_dict(),
        "resource_admissions": admissions,
        "telemetry": telemetry,
        "parity_audits": {
            "primitive_history": True,
            "parameter_update": True,
            "evaluation": True,
            "exposure": True,
        },
        "numerical_finiteness_audit": True,
        "incident_references": [],
        "durable_size_bytes": 1,
        "scientific_branch": None,
        "scientific_claim": None,
        "decision": "DECISION_PENDING",
        "claim_ceiling": "ENGINEERING_EVIDENCE_ONLY_DECISION_PENDING",
    }


def _minimal_pending_analysis() -> dict[str, object]:
    return {
        "schema": "cbsc_omrc_b01_b1_raw_analysis_v1",
        "decision": "DECISION_PENDING",
        "decision_reasons": [
            "AUC_DEFINITION_PENDING",
            "DIAGNOSTIC_AGGREGATION_PENDING",
            "SCIENTIFIC_BRANCH_CLASSIFIER_PENDING",
        ],
        "normalized_return_auc": None,
        "diagnostic_aggregates": None,
        "scientific_branch": None,
        "raw_checkpoint_records": [{} for _ in range(48)],
        "per_seed_curves": [{} for _ in range(12)],
    }


def _ledger_binding(**changes: object) -> B1LedgerBinding:
    plan = B1Plan()
    values: dict[str, object] = {
        "attempt_id": "artifact-ledger-test-01",
        "run_name": B1_RUN_NAME,
        "implementation_commit": "a" * 40,
        "source_conformance_sha256": "b" * 64,
        "configuration_sha256": "c" * 64,
        "laws_sha256": "d" * 64,
        "b0_manifest_sha256": "9" * 64,
        "b0_manifest_bytes": 12_807_274,
        "b0_reviewed_receipt_sha256": "8" * 64,
        "b0_inventory_sha256": "184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5",
        "b0_file_count": 33,
        "b0_total_bytes": 12_807_274,
        "object_id": plan.object_id,
        "innovator_selection_request_id": plan.innovator_selection_request_id,
        "innovator_selection_archive_path": plan.innovator_selection_archive_path,
        "innovator_selection_response_sha256": plan.innovator_selection_response_sha256,
        "literal_binding_request_id": plan.literal_binding_request_id,
        "literal_binding_archive_path": plan.literal_binding_archive_path,
        "literal_binding_response_sha256": plan.literal_binding_response_sha256,
        "metrics_only_request_id": plan.metrics_only_request_id,
        "metrics_only_archive_path": plan.metrics_only_archive_path,
        "metrics_only_response_sha256": plan.metrics_only_response_sha256,
        "object_id": "CBSC-OMRC-B01",
        "innovator_selection_request_id": "cbsc-online-b-innovator-20260901-01",
        "innovator_selection_archive_path": (
            "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
            "capability_bound_semantic_currentness/"
            "cbsc-online-b-innovator-20260901-01/RESPONSE.md"
        ),
        "innovator_selection_response_sha256": (
            "94f163f8ba777950c9c19ffac1acca3c697f09642d4713ef13b1e66d9f04d778"
        ),
        "literal_binding_request_id": "cbsc-online-b-innovator-20260901-02",
        "literal_binding_archive_path": (
            "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
            "capability_bound_semantic_currentness/"
            "cbsc-online-b-innovator-20260901-02/RESPONSE.md"
        ),
        "literal_binding_response_sha256": (
            "e96df981f7cdb40a6206f2fddcc989a05783491a1fa422e7b0ca673344a05844"
        ),
        "metrics_only_request_id": "cbsc-online-b-innovator-20260901-03",
        "metrics_only_archive_path": (
            "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
            "capability_bound_semantic_currentness/"
            "cbsc-online-b-innovator-20260901-03/RESPONSE.md"
        ),
        "metrics_only_response_sha256": (
            "7a3bd74e12508e22ea577a1563737eda119c10560e094b25279503648d1105f7"
        ),
    }
    values.update(changes)
    return B1LedgerBinding(**values)  # type: ignore[arg-type]


def _attempt_ledger(
    *, incomplete: bool = False, binding: B1LedgerBinding | None = None,
) -> B1AttemptLedger:
    binding = _ledger_binding() if binding is None else binding
    slots = []
    for index, (seed, arm) in enumerate(B1_SLOT_ORDER):
        if incomplete and index == 0:
            resume = B1ResumeCheckpointBinding(
                binding=binding,
                slot_index=index,
                seed=seed,
                arm=arm,
                completed_rollout_updates=12,
                checkpoint_relative_path="slots/00/checkpoint-update-12.pt",
                checkpoint_sha256="5" * 64,
                order_chain_sha256="6" * 64,
            )
            slots.append(
                B1SlotLedgerEntry(
                    binding=binding,
                    slot_index=index,
                    seed=seed,
                    arm=arm,
                    status=B1SlotStatus.INCOMPLETE,
                    incident_sha256="7" * 64,
                    resume_checkpoint=resume,
                )
            )
        elif index == 0:
            slots.append(
                B1SlotLedgerEntry(
                    binding=binding,
                    slot_index=index,
                    seed=seed,
                    arm=arm,
                    status=B1SlotStatus.COMPLETE,
                    raw_result_sha256="1" * 64,
                    admission_sha256="2" * 64,
                    telemetry_sha256="3" * 64,
                    files_sha256="4" * 64,
                )
            )
        else:
            slots.append(
                B1SlotLedgerEntry(
                    binding=binding,
                    slot_index=index,
                    seed=seed,
                    arm=arm,
                    status=B1SlotStatus.PENDING,
                )
            )
    return B1AttemptLedger(
        schema=B1_LEDGER_SCHEMA,
        publication_mode=B1_LEDGER_PUBLICATION_MODE,
        binding=binding,
        slots=tuple(slots),
    )


def test_analysis_preserves_complete_raw_records_and_fails_closed_on_pending_laws() -> None:
    raw = _raw_records()
    analysis = compute_b1_analysis(raw)

    assert analysis["schema"] == "cbsc_omrc_b01_b1_raw_analysis_v1"
    assert analysis["decision"] == "DECISION_PENDING"
    assert analysis["decision_reasons"] == [
        "AUC_DEFINITION_PENDING",
        "DIAGNOSTIC_AGGREGATION_PENDING",
        "SCIENTIFIC_BRANCH_CLASSIFIER_PENDING",
    ]
    assert analysis["normalized_return_auc"] is None
    assert analysis["diagnostic_aggregates"] is None
    assert analysis["scientific_branch"] is None
    assert len(analysis["raw_checkpoint_records"]) == 48
    assert len(analysis["per_seed_curves"]) == 12
    assert len(analysis["paired_heldout_differences"]) == 3 * 3 * 4 * 64
    struct = next(
        curve
        for curve in analysis["per_seed_curves"]
        if curve["arm"] == ARMS[0] and curve["seed"] == 21101
    )
    assert [point["update"] for point in struct["points"]] == [0, 12, 24, 48]
    assert struct["terminal_return"]["numerator"] == 24
    assert struct["terminal_return"]["denominator"] == 5


def test_analysis_rejects_incomplete_duplicate_non_b1_and_nonfinite_records() -> None:
    raw = _raw_records()
    with pytest.raises(B1AnalysisError, match="complete 48"):
        compute_b1_analysis(raw[:-1])

    duplicate = deepcopy(raw)
    duplicate[-1] = deepcopy(duplicate[0])
    with pytest.raises(B1AnalysisError, match="duplicate|coverage"):
        compute_b1_analysis(duplicate)

    b0 = deepcopy(raw)
    b0[0]["run_name"] = "CBSC-OMRC-B0-INSTRUMENT"
    with pytest.raises(B1AnalysisError, match="B1 run identity"):
        compute_b1_analysis(b0)

    nonfinite = deepcopy(raw)
    nonfinite[0]["episodes"][0]["return"]["float"] = float("nan")
    with pytest.raises(B1AnalysisError, match="finite|exact ratio"):
        compute_b1_analysis(nonfinite)


def test_analysis_accepts_only_the_current_canonical_evaluator_decision_surface() -> None:
    raw = _raw_records()
    compute_b1_analysis(raw)

    invented = deepcopy(raw)
    invented[0]["episodes"][0]["decisions"][0]["retention_gap"] = 1
    with pytest.raises(B1AnalysisError, match="raw diagnostic surface"):
        compute_b1_analysis(invented)


def test_raw_schema_matches_the_current_canonical_evaluator_surface() -> None:
    tape = DynamicHost(B1_RUN_NAME, B1_SEEDS[0]).build_stochastic(
        addressing.EVAL_STOCHASTIC, 0
    )
    actual = evaluate_episode(tape, [Action.SAFE_FALLBACK] * 24)
    fixture = _raw_records()[0]["episodes"][0]
    assert set(fixture) == set(actual)
    assert set(fixture["decisions"][0]) == set(actual["decisions"][0])


def test_manifest_validator_accepts_only_complete_pending_test_schema() -> None:
    manifest = _test_manifest(_minimal_pending_analysis())
    validated = validate_b1_complete_manifest(manifest, allow_test_only=True)
    assert validated["decision"] == "DECISION_PENDING"
    assert validated["b0_evidence"] == {
        "manifest_sha256": "9" * 64,
        "manifest_bytes": 12_807_274,
        "reviewed_receipt_sha256": "8" * 64,
        "inventory_sha256": "184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5",
        "file_count": 33,
        "total_bytes": 12_807_274,
    }

    with pytest.raises(B1ArtifactError, match="TEST_ONLY"):
        validate_b1_complete_manifest(manifest)

    for field, value in (
        ("scientific_branch", "NULL_AT_THIS_BUDGET"),
        ("scientific_claim", "positive"),
        ("decision", "FORMED"),
    ):
        invalid = deepcopy(manifest)
        invalid[field] = value
        with pytest.raises(B1ArtifactError):
            validate_b1_complete_manifest(invalid, allow_test_only=True)

    missing = deepcopy(manifest)
    missing["resource_admissions"].pop()
    with pytest.raises(B1ArtifactError, match="admission"):
        validate_b1_complete_manifest(missing, allow_test_only=True)

    missing_b0 = deepcopy(manifest)
    del missing_b0["b0_evidence"]
    with pytest.raises(B1ArtifactError, match="b0_evidence|missing"):
        validate_b1_complete_manifest(missing_b0, allow_test_only=True)
    for field, bad in (
        ("manifest_sha256", "9" * 63),
        ("manifest_bytes", 0),
        ("manifest_bytes", True),
        ("reviewed_receipt_sha256", 7),
        ("inventory_sha256", "1" * 63),
        ("file_count", 0),
        ("file_count", True),
        ("total_bytes", 0),
        ("total_bytes", True),
    ):
        invalid_b0 = deepcopy(manifest)
        invalid_b0["b0_evidence"][field] = bad
        with pytest.raises(B1ArtifactError, match="B0|b0|evidence"):
            validate_b1_complete_manifest(invalid_b0, allow_test_only=True)
    for missing_field in ("inventory_sha256", "file_count", "total_bytes"):
        missing_inventory = deepcopy(manifest)
        del missing_inventory["b0_evidence"][missing_field]
        with pytest.raises(B1ArtifactError, match="B0|b0|evidence"):
            validate_b1_complete_manifest(missing_inventory, allow_test_only=True)

    stale_evidence = deepcopy(manifest)
    stale_evidence["analysis"]["raw_checkpoint_records"][0] = {"mutated": True}
    with pytest.raises(B1ArtifactError, match="evidence_sha256|raw checkpoint"):
        validate_b1_complete_manifest(stale_evidence, allow_test_only=True)
    wrong_configuration = deepcopy(manifest)
    wrong_configuration["configuration_sha256"] = "0" * 64
    with pytest.raises(B1ArtifactError, match="configuration_sha256|configuration"):
        validate_b1_complete_manifest(wrong_configuration, allow_test_only=True)

    resumed = deepcopy(manifest)
    resumed["incident_references"] = [
        {
            "attempt_id": "artifact-ledger-test-01",
            "incident_manifest_sha256": "6" * 64,
            "attempt_ledger_sha256": "7" * 64,
            "incident_relative_path": "incidents/one/incident.json",
        }
    ]
    assert validate_b1_complete_manifest(
        resumed, allow_test_only=True
    )["incident_references"] == resumed["incident_references"]
    multiple = deepcopy(resumed)
    second = deepcopy(multiple["incident_references"][0])
    second["incident_manifest_sha256"] = "5" * 64
    second["incident_relative_path"] = "incidents/two/incident.json"
    multiple["incident_references"].append(second)
    assert len(validate_b1_complete_manifest(
        multiple, allow_test_only=True
    )["incident_references"]) == 2
    duplicate = deepcopy(resumed)
    duplicate["incident_references"].append(deepcopy(duplicate["incident_references"][0]))
    with pytest.raises(B1ArtifactError, match="incident reference"):
        validate_b1_complete_manifest(duplicate, allow_test_only=True)
    for mutation in ("missing", "extra", "wrong_type"):
        invalid_reference = deepcopy(resumed)
        reference = invalid_reference["incident_references"][0]
        if mutation == "missing":
            del reference["attempt_ledger_sha256"]
        elif mutation == "extra":
            reference["extra"] = "incidents/locator-only"
        else:
            reference["incident_manifest_sha256"] = 6
        with pytest.raises(B1ArtifactError, match="incident reference"):
            validate_b1_complete_manifest(invalid_reference, allow_test_only=True)


def test_test_only_complete_and_incident_publication_are_create_only(
    monkeypatch, tmp_path: Path
) -> None:
    allowed = tmp_path / "direction"
    final = allowed / "exp" / "test-b1"
    staging = create_b1_staging_directory(final, allowed_root=allowed)
    # Publication mechanics do not duplicate the large raw fixture; complete
    # raw-analysis behavior is exercised independently above.
    manifest = _test_manifest(_minimal_pending_analysis())
    published = publish_b1_complete(
        staging,
        final,
        manifest,
        allowed_root=allowed,
        allow_test_only=True,
    )
    assert json.loads((published / "manifest.json").read_text())["test_only"] is True
    with pytest.raises(FileExistsError):
        create_b1_staging_directory(final, allowed_root=allowed)

    formal_final = allowed / "exp" / "formal-must-not-publish"
    formal_staging = create_b1_staging_directory(formal_final, allowed_root=allowed)
    formal_manifest = deepcopy(manifest)
    formal_manifest["schema"] = B1_RESULT_SCHEMA
    formal_manifest["test_only"] = False
    with pytest.raises(B1ArtifactError, match="permanently TEST_ONLY"):
        publish_b1_complete(
            formal_staging,
            formal_final,
            formal_manifest,
            allowed_root=allowed,
        )
    assert not formal_final.exists()

    partial = create_b1_staging_directory(
        allowed / "exp" / "never-published", allowed_root=allowed
    )
    (partial / "raw.bin").write_bytes(b"preserved")
    incident = publish_b1_incident(
        staging=partial,
        incident_root=allowed / "exp" / "incidents",
        allowed_root=allowed,
        attempt_id="test-attempt",
        category="TEST_ONLY_FAILURE",
        detail="synthetic test-only incident",
        completed_arm_seeds=((ARMS[0], 21101),),
        test_only=True,
    )
    payload = json.loads((incident / "incident.json").read_text())
    assert payload["test_only"] is True
    assert payload["scientific_object_consumed"] is False
    assert payload["scientific_branch"] is None
    assert payload["incident_references"] == []
    assert (incident / "raw.bin").read_bytes() == b"preserved"


def test_attempt_ledger_roundtrip_is_create_only_canonical_and_sha_bound(tmp_path: Path) -> None:
    allowed = tmp_path / "direction"
    path = allowed / "attempts" / "attempt-ledger-01.json"
    ledger = _attempt_ledger(incomplete=True)

    file_sha256 = publish_b1_attempt_ledger(path, ledger, allowed_root=allowed)
    original_bytes = path.read_bytes()
    loaded = load_b1_attempt_ledger(
        path,
        allowed_root=allowed,
        expected_sha256=file_sha256,
        expected_binding=ledger.binding,
    )
    assert loaded == ledger
    assert loaded.binding.b0_manifest_sha256 == "9" * 64
    assert loaded.binding.b0_manifest_bytes == 12_807_274
    assert loaded.binding.b0_reviewed_receipt_sha256 == "8" * 64
    assert loaded.binding.b0_inventory_sha256 == (
        "184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5"
    )
    assert loaded.binding.b0_file_count == 33
    assert loaded.binding.b0_total_bytes == 12_807_274
    assert loaded.binding.innovator_selection_response_sha256 == (
        "94f163f8ba777950c9c19ffac1acca3c697f09642d4713ef13b1e66d9f04d778"
    )
    assert path.read_bytes() == original_bytes
    assert loaded.slots[0].resume_checkpoint.completed_rollout_updates == 12

    with pytest.raises(FileExistsError):
        publish_b1_attempt_ledger(path, ledger, allowed_root=allowed)
    assert path.read_bytes() == original_bytes
    with pytest.raises(B1ArtifactError, match="SHA"):
        load_b1_attempt_ledger(
            path,
            allowed_root=allowed,
            expected_sha256="0" * 64,
        )
    with pytest.raises(B1ArtifactError, match="binding|cross-source"):
        load_b1_attempt_ledger(
            path,
            allowed_root=allowed,
            expected_sha256=file_sha256,
            expected_binding=_ledger_binding(source_conformance_sha256="8" * 64),
        )


def test_attempt_ledger_document_rejects_cross_source_slot_mix() -> None:
    complete = validate_b1_attempt_ledger_document(_attempt_ledger().as_dict())
    assert complete.slots[0].raw_result_sha256 == "1" * 64
    assert complete.slots[0].admission_sha256 == "2" * 64
    assert complete.slots[0].telemetry_sha256 == "3" * 64
    assert complete.slots[0].files_sha256 == "4" * 64

    missing_b0 = _attempt_ledger().as_dict()
    del missing_b0["binding"]["b0_manifest_sha256"]
    with pytest.raises(B1ArtifactError, match="binding"):
        validate_b1_attempt_ledger_document(missing_b0)
    wrong_b0_type = _attempt_ledger().as_dict()
    wrong_b0_type["binding"]["b0_manifest_bytes"] = True
    with pytest.raises(B1ArtifactError, match="binding|contract"):
        validate_b1_attempt_ledger_document(wrong_b0_type)
    missing_selection = _attempt_ledger().as_dict()
    del missing_selection["binding"]["innovator_selection_request_id"]
    with pytest.raises(B1ArtifactError, match="binding"):
        validate_b1_attempt_ledger_document(missing_selection)
    cross_selection = _attempt_ledger(incomplete=True).as_dict()
    cross_selection["slots"][0]["resume_checkpoint"]["binding"][
        "innovator_selection_response_sha256"
    ] = "0" * 64
    with pytest.raises(B1ArtifactError, match="binding|identity|contract"):
        validate_b1_attempt_ledger_document(cross_selection)
    for field, bad in (
        ("b0_inventory_sha256", "1" * 63),
        ("b0_file_count", True),
        ("b0_total_bytes", 0),
    ):
        wrong_inventory = _attempt_ledger().as_dict()
        wrong_inventory["binding"][field] = bad
        with pytest.raises(B1ArtifactError, match="binding|contract"):
            validate_b1_attempt_ledger_document(wrong_inventory)

    document = _attempt_ledger().as_dict()
    document["slots"][0]["binding"]["source_conformance_sha256"] = "8" * 64
    with pytest.raises(B1ArtifactError, match="cross-source|binding"):
        validate_b1_attempt_ledger_document(document)


def test_incident_is_the_authority_for_resume_ledger_path_sha_and_binding(
    tmp_path: Path,
) -> None:
    allowed = tmp_path / "direction"
    never_final = allowed / "exp" / "never-final"
    staging = create_b1_staging_directory(never_final, allowed_root=allowed)
    (staging / "partial.bin").write_bytes(b"partial evidence")
    ledger = _attempt_ledger(incomplete=True)
    incident = publish_b1_incident(
        staging=staging,
        incident_root=allowed / "exp" / "incidents",
        allowed_root=allowed,
        attempt_id=ledger.binding.attempt_id,
        category="TEST_ONLY_RESUME_INCIDENT",
        detail="synthetic provenance closure",
        completed_arm_seeds=(),
        test_only=True,
        attempt_ledger=ledger,
    )
    manifest_path = incident / "incident.json"
    manifest_bytes = manifest_path.read_bytes()
    ledger_path = incident / "attempt-ledger.json"
    ledger_bytes = ledger_path.read_bytes()
    incident_manifest = json.loads(manifest_bytes)
    assert incident_manifest["attempt_binding"]["b0_manifest_sha256"] == "9" * 64
    assert incident_manifest["attempt_ledger"]["binding"]["b0_manifest_bytes"] == 12_807_274
    assert (
        incident_manifest["attempt_ledger"]["binding"]["b0_reviewed_receipt_sha256"]
        == "8" * 64
    )
    assert incident_manifest["attempt_binding"]["b0_inventory_sha256"] == (
        "184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5"
    )
    assert incident_manifest["attempt_ledger"]["binding"]["b0_file_count"] == 33
    assert incident_manifest["attempt_ledger"]["binding"]["b0_total_bytes"] == 12_807_274
    assert load_b1_attempt_ledger_from_incident(
        manifest_path, allowed_root=allowed
    ) == ledger

    tampered_manifest = json.loads(manifest_bytes)
    tampered_manifest["attempt_ledger"]["sha256"] = "0" * 64
    manifest_path.write_bytes(
        (json.dumps(
            tampered_manifest,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n").encode("ascii")
    )
    with pytest.raises(B1ArtifactError, match="SHA"):
        load_b1_attempt_ledger_from_incident(manifest_path, allowed_root=allowed)

    manifest_path.write_bytes(manifest_bytes)
    ledger_path.write_bytes(ledger_bytes + b" ")
    with pytest.raises(B1ArtifactError, match="SHA"):
        load_b1_attempt_ledger_from_incident(manifest_path, allowed_root=allowed)


def test_incident_ancestor_chain_survives_two_failures_and_third_success(
    tmp_path: Path,
) -> None:
    allowed = tmp_path / "direction"
    manifest = _test_manifest(_minimal_pending_analysis())
    binding = _ledger_binding(
        configuration_sha256=manifest["configuration_sha256"],
        laws_sha256=_canonical_sha256(manifest["law_digests"]),
    )
    ledger = _attempt_ledger(incomplete=True, binding=binding)

    def reference(incident: Path) -> dict[str, str]:
        document = json.loads((incident / "incident.json").read_text(encoding="ascii"))
        return {
            "attempt_id": binding.attempt_id,
            "incident_manifest_sha256": hashlib.sha256(
                (incident / "incident.json").read_bytes()
            ).hexdigest(),
            "attempt_ledger_sha256": document["attempt_ledger"]["sha256"],
            "incident_relative_path": (incident / "incident.json").relative_to(
                allowed
            ).as_posix(),
        }

    incident_root = allowed / "exp" / "incidents"
    first = publish_b1_incident(
        staging=None, incident_root=incident_root, allowed_root=allowed,
        attempt_id=binding.attempt_id, category="TEST_ONLY_FIRST_FAILURE",
        detail="first", completed_arm_seeds=(), test_only=True,
        attempt_ledger=ledger,
    )
    first_bytes = (first / "incident.json").read_bytes()
    ref1 = reference(first)
    first_witness = make_b1_incident_lineage_witness(
        [ref1], allowed_root=allowed, expected_binding=binding
    )
    second = publish_b1_incident(
        staging=None, incident_root=incident_root, allowed_root=allowed,
        attempt_id=binding.attempt_id, category="TEST_ONLY_RESUME_FAILURE",
        detail="second", completed_arm_seeds=(), test_only=True,
        attempt_ledger=ledger, incident_lineage_witness=first_witness,
    )
    second_bytes = (second / "incident.json").read_bytes()
    ref2 = reference(second)
    lineage = [ref1, ref2]
    assert validate_b1_incident_lineage(
        lineage, allowed_root=allowed, expected_binding=binding
    ) == lineage
    with pytest.raises(B1ArtifactError, match="exact validated witness"):
        materialize_b1_incident_lineage(  # type: ignore[arg-type]
            lineage, allowed_root=allowed, expected_binding=binding
        )

    manifest["incident_references"] = lineage
    final = allowed / "exp" / "third-success"
    staging = create_b1_staging_directory(final, allowed_root=allowed)
    assert publish_b1_complete(
        staging, final, manifest, allowed_root=allowed, allow_test_only=True
    ) == final
    assert json.loads((final / "manifest.json").read_text())["incident_references"] == lineage
    assert (first / "incident.json").read_bytes() == first_bytes
    assert (second / "incident.json").read_bytes() == second_bytes

    with pytest.raises(B1ArtifactError, match="cycle|duplicate"):
        validate_b1_incident_lineage(
            [ref1, ref1], allowed_root=allowed, expected_binding=binding
        )
    with pytest.raises(B1ArtifactError):
        validate_b1_incident_lineage(
            [ref2, ref1], allowed_root=allowed, expected_binding=binding
        )
    missing = deepcopy(ref1)
    missing["incident_relative_path"] = "exp/incidents/missing/incident.json"
    with pytest.raises((B1ArtifactError, OSError)):
        validate_b1_incident_lineage(
            [missing], allowed_root=allowed, expected_binding=binding
        )
