from __future__ import annotations

from copy import deepcopy

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_mechanical import (
    B1MechanicalError,
    b0_nonpolarity_record,
    build_mechanical_input_descriptor,
    compute_b1_mechanical,
    compute_raw_competence,
)


SEEDS = (21101, 21121, 21143)
FINITE_ZERO = "00000000"
FINITE_ONE = "3f800000"


def _ratio(numerator: int, denominator: int = 1) -> dict[str, int]:
    return {"numerator": numerator, "denominator": denominator}


def _decision(opportunity_id: int) -> dict[str, object]:
    selected = "SERVE" if opportunity_id < 20 else "REFRESH"
    return {
        "opportunity_id": opportunity_id,
        "selected_action": selected,
        "oracle_action": ("SERVE", "REFRESH", "SAFE_FALLBACK")[opportunity_id % 3],
        "request_active": True,
        "access_mode": "OPEN",
        "presented_body_native_neutral": False,
        "address_match_truth": True,
        "payload_source_match_truth": True,
        "content_match_truth": True,
        "owner_match_truth": True,
        "epoch_match_truth": True,
        "legal_action_mask": [False, True, True, True],
        "actor_logits_fp32_bits": [FINITE_ZERO, FINITE_ONE, FINITE_ZERO, FINITE_ZERO],
        "critic_value_fp32_bits": FINITE_ZERO,
        "selected_action_log_probability_fp32_bits": FINITE_ZERO,
    }


def _competence(seed: int = 21101) -> dict[str, object]:
    return {
        "seed": seed,
        "checkpoint_update": 48,
        "split": "EVAL_STOCHASTIC",
        "tapes": [
            {
                "tape_id": tape_id,
                "raw_return": _ratio(2),
                "always_refresh_return": _ratio(1),
                "always_safe_return": _ratio(0),
                "decisions": [_decision(opportunity) for opportunity in range(24)],
            }
            for tape_id in range(32)
        ],
    }


def _facts() -> dict[str, object]:
    digest_a = "a" * 64
    digest_b = "b" * 64
    return {
        "inventories": [
            {
                "name": "raw-checkpoints",
                "expected_keys": ["a", "b"],
                "observed_keys": ["a", "b"],
            }
        ],
        "resources": [
            {
                "invocation_id": "raw-21101",
                "physical_available_bytes": 5 * 1024**3,
                "effective_available_bytes": 5 * 1024**3,
                "wall_seconds": 10.0,
                "peak_rss_bytes": 1024,
                "scratch_peak_bytes": 0,
                "durable_peak_bytes": 1024,
                "measurement_complete": True,
            }
        ],
        "digest_bindings": [
            {"name": "manifest", "expected_sha256": digest_a, "observed_sha256": digest_a}
        ],
        "tape_bindings": [
            {"name": "cross-arm-tape", "expected_sha256": digest_b, "observed_sha256": digest_b}
        ],
        "work_bindings": [
            {"name": "equal-exposure", "expected_count": 97280, "observed_count": 97280}
        ],
        "fp32_records": [
            {"name": "actor-logit", "dtype": "float32", "fp32_bits": FINITE_ONE, "active_modes": []}
        ],
        "numeric_records": [{"name": "loss", "value": 1.0}],
        "reset_records": [
            {"name": "episode-h0", "expected_fp32_bits": [FINITE_ZERO], "observed_fp32_bits": [FINITE_ZERO]}
        ],
        "adaptation_records": [
            {
                "name": "heldout",
                "model_sha256_before": digest_a,
                "model_sha256_after": digest_a,
                "optimizer_sha256_before": digest_b,
                "optimizer_sha256_after": digest_b,
            }
        ],
        "checkpoint_records": [
            {
                "name": "roundtrip",
                "saved_sha256": digest_a,
                "loaded_sha256": digest_a,
                "expected_parameter_sha256": digest_b,
                "restored_parameter_sha256": digest_b,
            }
        ],
        "learner_visibility_records": [
            {"name": "decision-input", "visible_fields": ["primitive_token"], "allowed_fields": ["primitive_token"]}
        ],
        "legal_action_records": [
            {"name": "decision-0", "selected_action_index": 1, "legal_action_mask": [False, True, True, True]}
        ],
        "twin_records": [
            {"pair_id": "owner-0", "expected_members": ["A", "B"], "observed_members": ["A", "B"]}
        ],
        "literal_records": [
            {"audit_code": "TOKEN_LITERAL_MISMATCH", "expected": "token-a", "observed": "token-a"}
        ],
    }


def test_raw_competence_passes_from_exact_terminal_stochastic_records() -> None:
    result = compute_raw_competence(_competence())

    assert result["raw_competence_pass"] is True
    assert result["components"] == {
        "reference_return_pass": True,
        "easy_open_pass": True,
        "oracle_support_pass": True,
        "nonconstant_action_pass": True,
        "record_integrity_pass": True,
    }
    assert result["inputs"]["tape_ids"] == list(range(32))
    assert result["inputs"]["decision_count"] == 768
    assert result["inputs"]["easy_open_serve_fraction"] == {"numerator": 5, "denominator": 6}
    assert result["inputs"]["raw_mean_return"] == {"numerator": 2, "denominator": 1}


def test_raw_competence_tie_and_zero_easy_support_are_false() -> None:
    tie = _competence()
    for tape in tie["tapes"]:
        tape["raw_return"] = _ratio(1)
    tie_result = compute_raw_competence(tie)
    assert tie_result["components"]["reference_return_pass"] is False
    assert tie_result["raw_competence_pass"] is False

    zero_support = _competence()
    for tape in zero_support["tapes"]:
        for decision in tape["decisions"]:
            decision["request_active"] = False
    zero_result = compute_raw_competence(zero_support)
    assert zero_result["inputs"]["easy_open_eligible_count"] == 0
    assert zero_result["inputs"]["easy_open_serve_fraction"] is None
    assert zero_result["components"]["easy_open_pass"] is False
    assert zero_result["raw_competence_pass"] is False


def test_raw_competence_easy_open_threshold_is_inclusive() -> None:
    record = _competence()
    for tape in record["tapes"]:
        for opportunity, decision in enumerate(tape["decisions"]):
            decision["request_active"] = opportunity < 5
            if opportunity < 4:
                decision["selected_action"] = "SERVE"
            elif opportunity == 4:
                decision["selected_action"] = "REFRESH"
    result = compute_raw_competence(record)

    assert result["inputs"]["easy_open_serve_fraction"] == {"numerator": 4, "denominator": 5}
    assert result["components"]["easy_open_pass"] is True
    assert result["raw_competence_pass"] is True


@pytest.mark.parametrize("defect", ["missing", "duplicate", "nonfinite"])
def test_raw_competence_missing_duplicate_or_nonfinite_is_null(defect: str) -> None:
    record = _competence()
    if defect == "missing":
        record["tapes"].pop()
    elif defect == "duplicate":
        record["tapes"].append(deepcopy(record["tapes"][0]))
    else:
        record["tapes"][0]["decisions"][0]["actor_logits_fp32_bits"][1] = "7f800000"

    result = compute_raw_competence(record)

    assert result["raw_competence_pass"] is None
    assert result["components"]["record_integrity_pass"] is None
    assert (
        result["inputs"]["missing_record_count"]
        + result["inputs"]["duplicate_record_count"]
        + result["inputs"]["nonfinite_count"]
    ) > 0


def test_mechanical_fields_are_recomputed_and_caller_pass_booleans_are_rejected() -> None:
    result = compute_b1_mechanical(
        _facts(), [_competence(seed) for seed in SEEDS]
    )

    assert result["mechanical_attempt_complete"] is True
    assert result["mechanical_conformance_pass"] is True
    assert result["scientific_packet_readable"] is True
    assert result["blocking_audit_codes"] == []
    assert [row["seed"] for row in result["raw_competence_by_seed"]] == list(SEEDS)
    assert result["mechanical_components"]["fp32"] is True

    facts = _facts()
    facts["mechanical_conformance_pass"] = True
    with pytest.raises(B1MechanicalError, match="fields differ"):
        compute_b1_mechanical(facts, [_competence(seed) for seed in SEEDS])


def test_mechanical_failures_are_nonpolar_and_emit_stable_codes() -> None:
    facts = _facts()
    facts["work_bindings"][0]["observed_count"] = 97279
    facts["adaptation_records"][0]["model_sha256_after"] = "c" * 64
    facts["legal_action_records"][0]["selected_action_index"] = 0

    result = compute_b1_mechanical(facts, [_competence(seed) for seed in SEEDS])

    assert result["mechanical_attempt_complete"] is True
    assert result["mechanical_conformance_pass"] is False
    assert result["scientific_packet_readable"] is True
    assert result["blocking_audit_codes"] == [
        "UNEQUAL_WORK_EXPOSURE",
        "EVALUATION_ADAPTATION_FAILURE",
        "ILLEGAL_ACTION",
    ]
    assert "scientific_branch" not in result
    assert "scientific_polarity" not in result
    assert "b2_extension_trigger" not in result


def test_bound_mechanical_descriptor_rejects_argument_tamper_after_rehashable_summary() -> None:
    facts = _facts()
    competence = [_competence(seed) for seed in SEEDS]
    source = {
        "source_relative_path": "workers/00/result.json.gz",
        "source_file_sha256": "a" * 64,
        "json_pointer": "/raw_evidence",
    }
    descriptor = build_mechanical_input_descriptor(
        facts,
        competence,
        authority="BOUND_ARTIFACT_EVIDENCE",
        test_only=True,
        training_slot_indices=(0,),
        raw_worker_sources=((source,),),
        policy_execution_mode_sources=({**source, "json_pointer": "/execution_mode_records"},),
        table_bindings=({
            "table": "audits", "sha256": "b" * 64,
            "row_count": 1, "byte_count": 1,
        },),
        artifact_inventory_sha256="c" * 64,
    )
    assert compute_b1_mechanical(
        facts, competence, input_descriptor=descriptor
    )["inputs"] == descriptor

    tampered = deepcopy(facts)
    tampered["work_bindings"][0]["observed_count"] -= 1
    with pytest.raises(B1MechanicalError, match="digests differ from arguments"):
        compute_b1_mechanical(
            tampered, competence, input_descriptor=descriptor
        )


def test_b0_nonpolarity_marks_all_five_eligibilities_false() -> None:
    assert b0_nonpolarity_record() == {
        "schema": "cbsc_omrc_b01_b0_nonpolarity_v1",
        "b0_nonpolarity": "ABSOLUTE",
        "scientific_eligible": False,
        "classifier_eligible": False,
        "threshold_tuning_eligible": False,
        "b2_trigger_eligible": False,
        "promotion_eligible": False,
    }
