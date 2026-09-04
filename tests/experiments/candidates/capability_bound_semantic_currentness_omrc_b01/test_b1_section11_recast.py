"""Section-11 recast of CBSC-OMRC-B01 (owner decisions 3 and 7, 2026-09-02).

Provenance:
  docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md A.4
  docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md
  docs/research/candidates/capability_bound_semantic_currentness/
    CBSC_OMRC_B01_SECTION11_RECAST_INTAKE_20260902.md

Five properties are asserted here:

  (i)   the former publication flags are recorded and block nothing;
  (ii)  descriptive curves are present and non-null in a smoke-scale artifact;
  (iii) the mechanical RAW-competence gate still computes and is published;
  (iv)  missing or failed resource telemetry downgrades to
        ``resources_unmeasured`` and does not quarantine;
  (v)   learner-side instrumentation failure still quarantines (§6.2).
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import struct

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import b1
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1_RESOURCE_CAPS,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_descriptive import (
    B1DescriptiveError,
    B1_DESCRIPTIVE_SCHEMA,
    DESCRIPTIVE_STATUS_PUBLISHED,
    DESCRIPTIVE_STATUS_UNAVAILABLE,
    compute_b1_descriptive_curves,
    unavailable_descriptive_curves,
    validate_descriptive_curves,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_mechanical import (
    compute_b1_mechanical,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_artifact import (
    FORMAL_ANALYSIS_BOUND,
    FORMAL_ANALYSIS_GATES_PUBLICATION,
    READINESS_DISPOSITION,
    build_complete_artifact_inventory,
    build_metrics_only_manifest,
    formal_analysis_record,
    materialize_metrics_only_tables,
    validate_metrics_only_manifest,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.telemetry import (
    ResourceCaps,
    assess_resource_telemetry,
)

from tests.experiments.candidates.capability_bound_semantic_currentness_omrc_b01.test_b1_mechanical import (
    SEEDS,
    _competence,
    _facts,
)
from tests.experiments.candidates.capability_bound_semantic_currentness_omrc_b01.test_b1_metrics_artifact import (
    _b0,
    _identity,
    _laws,
    _mechanical,
    _null_packet,
    _tables,
)


ARMS = ("STRUCT-CURRENTNESS-GRU", "RAW-GRU", "PI-GRU", "DERANGED-CURRENTNESS-GRU")


def _fraction_record(numerator: int, denominator: int = 1) -> dict[str, int]:
    value = Fraction(numerator, denominator)
    return {"numerator": value.numerator, "denominator": value.denominator}


def _fp32_bits(value: float) -> int:
    return int(struct.unpack(">I", struct.pack(">f", value))[0])


def _smoke_descriptive_inputs() -> dict[str, list[dict[str, object]]]:
    """A two-arm, one-seed, two-tape smoke sample of the published tables."""

    per_tape_curves = []
    policy_decisions = []
    training_episodes = []
    optimizer_steps = []
    for arm_order in (0, 1):
        for tape_id in (0, 1):
            curve = {
                "run_order": 0, "seed": 21101, "split_order": 1,
                "tape_id": tape_id, "arm_order": arm_order,
            }
            for update in (0, 12, 24, 48):
                curve[f"episode_return_update_{update}"] = _fraction_record(
                    update + tape_id + arm_order, 4
                )
                curve[f"episode_decision_reward_sum_update_{update}"] = (
                    _fraction_record(update, 8)
                )
                curve[f"episode_settlement_reward_sum_update_{update}"] = (
                    _fraction_record(update, 8)
                )
            per_tape_curves.append(curve)
            for update in (0, 12, 24, 48):
                for opportunity_id in range(3):
                    policy_decisions.append({
                        "run_order": 0, "seed": 21101,
                        "checkpoint_update": update, "split_order": 1,
                        "tape_id": tape_id, "opportunity_id": opportunity_id,
                        "arm_order": arm_order,
                        "selected_action": (opportunity_id + arm_order) % 3,
                    })
        for episode in range(2):
            training_episodes.append({
                "run_order": 0, "run_name": "CBSC-OMRC-B1-THREE-SEED-SCOUT",
                "seed": 21101, "arm_order": arm_order, "arm": ARMS[arm_order],
                "training_episode_id": episode, "rollout_update": 0,
                "policy_version": 0, "episode_return": 1.5 + episode,
                "action_count_serve": 10 + episode,
                "action_count_refresh": 8,
                "action_count_safe_fallback": 6,
            })
        for step in range(1, 3):
            optimizer_steps.append({
                "run_order": 0, "run_name": "CBSC-OMRC-B1-THREE-SEED-SCOUT",
                "seed": 21101, "arm_order": arm_order, "arm": ARMS[arm_order],
                "rollout_update": 0, "ppo_epoch": 0, "minibatch_index": step - 1,
                "ordered_episode_ids": [0, 1],
                "actor_loss_fp32_bits": _fp32_bits(0.25),
                "value_loss_fp32_bits": _fp32_bits(0.5),
                "entropy_fp32_bits": _fp32_bits(1.0),
                "total_loss_fp32_bits": _fp32_bits(0.75),
                "preclip_gradient_norm_fp32_bits": _fp32_bits(0.4),
                "postclip_gradient_norm_fp32_bits": _fp32_bits(0.1 * step),
                "optimizer_step_count": step,
                "parameter_sha256_after_step": f"{arm_order}{step}".ljust(64, "a"),
            })
    raw_competence = [
        record for record in (
            compute_b1_mechanical(_facts(), [_competence(seed) for seed in SEEDS])
        )["raw_competence_by_seed"]
    ]
    return {
        "per_tape_curves": per_tape_curves,
        "policy_decisions": policy_decisions,
        "training_episodes": training_episodes,
        "optimizer_steps": optimizer_steps,
        "raw_competence": raw_competence,
    }


# (i) the demoted flags are recorded and block nothing ------------------------


def test_demoted_formal_flags_are_recorded_and_gate_nothing() -> None:
    record = formal_analysis_record()
    assert record["formal_analysis_bound"] is FORMAL_ANALYSIS_BOUND is False
    assert record["readiness_disposition"] == READINESS_DISPOSITION == "REPAIR_REQUIRED"
    assert record["gating"] is FORMAL_ANALYSIS_GATES_PUBLICATION is False
    assert "section 11.4" in record["demoted_by"]
    assert record["decision_record"].endswith(
        "2026-09-02-first-wave-section11-recast.md"
    )
    assert record["recast_intake"].endswith(
        "CBSC_OMRC_B01_SECTION11_RECAST_INTAKE_20260902.md"
    )

    readiness = b1._readiness_result()
    assert readiness.authorized is True
    assert readiness.blockers == ()
    assert readiness.disposition == "READY"

    document = b1.readiness_document()
    assert document["start_authorized"] is True
    assert document["formal_analysis_record"] == record

    # The two former publication raises no longer exist in the source.
    production = Path(
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/"
        "b1_metrics_production.py"
    ).read_text(encoding="utf-8")
    assert 'raise B1MetricsProductionError(\n            "REPAIR_REQUIRED' not in production


# (ii) descriptive curves are published, non-null -----------------------------


def test_descriptive_curves_are_computed_from_the_runners_own_tables() -> None:
    packet = compute_b1_descriptive_curves(**_smoke_descriptive_inputs())
    validate_descriptive_curves(packet)

    assert packet["schema"] == B1_DESCRIPTIVE_SCHEMA
    assert packet["status"] == DESCRIPTIVE_STATUS_PUBLISHED

    curves = packet["heldout_return_curves"]
    assert len(curves) == 2
    for curve in curves:
        assert curve["tape_count"] == 2
        assert [point["checkpoint_update"] for point in curve["points"]] == [0, 12, 24, 48]
        for point in curve["points"]:
            for field in (
                "mean_episode_return", "min_episode_return", "max_episode_return"
            ):
                assert point[field] is not None
                assert set(point[field]) == {"numerator", "denominator", "float"}
    # arm 0, tapes 0 and 1 at update 48: (48+0+0)/4 and (48+1+0)/4 -> mean 97/8
    first = curves[0]["points"][-1]["mean_episode_return"]
    assert Fraction(first["numerator"], first["denominator"]) == Fraction(97, 8)

    actions = packet["heldout_action_counts"]
    assert len(actions) == 8
    for row in actions:
        assert row["decision_count"] == 6
        assert sum(row["action_counts"].values()) == 6
        assert row["serve_rate"] is not None
        assert row["distinct_action_count"] >= 2

    exposure = packet["exposure_line"]
    assert len(exposure) == 2
    for row in exposure:
        assert row["optimizer_step_count"] == 2
        assert row["parameters_moved"] is True
        assert row["postclip_gradient_norm_max"] > 0.0

    training = packet["training_episode_action_counts"]
    assert len(training) == 2
    for row in training:
        assert row["episode_count"] == 2
        assert row["action_counts"]["SERVE"] == 21


def test_published_manifest_carries_descriptive_curves_and_keeps_derived_nulls(
    tmp_path: Path,
) -> None:
    staging = tmp_path / "attempt.partial-test"
    staging.mkdir()
    b0 = _b0(staging)
    identity = _identity(staging)
    inventory = materialize_metrics_only_tables(
        staging, _tables(), allowed_root=tmp_path, allow_test_only=True
    )
    artifact_inventory = build_complete_artifact_inventory(staging)
    descriptive = compute_b1_descriptive_curves(**_smoke_descriptive_inputs())
    manifest = build_metrics_only_manifest(
        identity=identity, b0_evidence=b0, table_inventory=inventory,
        law_digests=_laws(), artifact_inventory=artifact_inventory,
        literal_nulls=_null_packet(), mechanical=_mechanical(),
        incident_references=[], test_only=True,
        descriptive_curves=descriptive,
    )
    validated = validate_metrics_only_manifest(
        manifest, root=staging, allow_test_only=True
    )

    published = validated["descriptive_curves"]
    assert published["status"] == DESCRIPTIVE_STATUS_PUBLISHED
    assert published["heldout_return_curves"], "descriptive curves must not be empty"
    assert published["exposure_line"], "the exposure line must be published"
    assert published["raw_competence_flags"], "competence flags must be published"

    # The recast publishes descriptives; it does not invent an interpretation.
    assert validated["scientific_branch"] is None
    assert validated["scientific_polarity"] is None
    assert validated["promotion_eligible"] is None
    assert validated["b2_extension_trigger"] is None
    assert all(value is None for value in validated["derived_fields"].values())
    assert validated["formal_analysis_record"]["gating"] is False

    tampered = deepcopy(manifest)
    tampered["descriptive_curves"]["status"] = "SOMETHING_ELSE"
    with pytest.raises(Exception):
        validate_metrics_only_manifest(
            tampered, root=staging, allow_test_only=True
        )


def test_unavailable_descriptive_summary_records_its_reason() -> None:
    packet = unavailable_descriptive_curves("no optimizer steps were recorded")
    validate_descriptive_curves(packet)
    assert packet["status"] == DESCRIPTIVE_STATUS_UNAVAILABLE
    assert packet["reason"] == "no optimizer steps were recorded"
    with pytest.raises(B1DescriptiveError):
        unavailable_descriptive_curves("   ")


# (iii) the mechanical RAW-competence gate still computes and is published ----


def test_raw_competence_gate_still_computes_and_is_published() -> None:
    mechanical = compute_b1_mechanical(
        _facts(), [_competence(seed) for seed in SEEDS]
    )
    by_seed = mechanical["raw_competence_by_seed"]
    assert [row["seed"] for row in by_seed] == list(SEEDS)
    assert all(row["raw_competence_pass"] is True for row in by_seed)

    packet = compute_b1_descriptive_curves(**_smoke_descriptive_inputs())
    flags = packet["raw_competence_flags"]
    assert [row["seed"] for row in flags] == list(SEEDS)
    for row in flags:
        assert row["raw_competence_pass"] is True
        assert row["components"]["reference_return_pass"] is True
        assert row["easy_open_serve_fraction"] is not None
        assert row["raw_action_counts"]
        assert row["mask_violation_count"] == 0


def test_raw_competence_failure_is_still_a_blocking_mechanical_fact() -> None:
    competence = [_competence(seed) for seed in SEEDS]
    # Tie with ALWAYS_REFRESH on every tape: the gate requires a strict excess.
    for tape in competence[0]["tapes"]:
        tape["raw_return"] = {"numerator": 1, "denominator": 1}
    mechanical = compute_b1_mechanical(_facts(), competence)
    assert mechanical["raw_competence_by_seed"][0]["raw_competence_pass"] is False
    assert "RAW_COMPETENCE_FAILURE" in mechanical["blocking_audit_codes"]
    # The gate stays a §4.2 integrity item: it is a published blocking fact,
    # not a mechanical conformance component and not mechanism polarity.
    assert mechanical["mechanical_conformance_pass"] is True
    assert "scientific_branch" not in mechanical


# (iv) missing resource telemetry downgrades, never quarantines ---------------


def _measurement(**overrides: object) -> dict[str, object]:
    wall = 10.0
    transitions = 1520
    record = {
        "measurement_complete": True, "measurement_source": "TEST_ONLY",
        "sample_interval_seconds": 0.05, "sample_count": 2,
        "end_to_end_wall_seconds": wall, "end_to_end_cpu_seconds": wall,
        "cpu_core_equivalents": 1.0, "cpu_occupancy_fraction": 1.0,
        "process_tree_peak_rss_bytes": 1024, "peak_process_count": 1,
        "peak_thread_count": 1, "worker_count": 1, "threads_per_worker": 1,
        "io_read_bytes": 0, "io_write_bytes": 0,
        "scratch_high_water_bytes": 0, "durable_high_water_bytes": 1024,
        "scientific_work_transitions": transitions,
        "scientific_work_transitions_per_second": transitions / wall,
        "stage_measurements": [{
            "stage": "train", "wall_seconds": wall, "cpu_seconds": wall,
            "transitions": transitions,
            "transitions_per_second": transitions / wall,
        }],
    }
    record.update(overrides)
    return record


def test_missing_resource_telemetry_downgrades_and_does_not_quarantine() -> None:
    absent = assess_resource_telemetry(None, caps=B1_RESOURCE_CAPS)
    assert absent["resources_unmeasured"] is True
    assert absent["unmeasured_reasons"] == ["telemetry_missing"]
    assert absent["stop_run"] is False
    assert absent["measurement"] is None

    broken = assess_resource_telemetry({"measurement_complete": True}, caps=B1_RESOURCE_CAPS)
    assert broken["resources_unmeasured"] is True
    assert broken["unmeasured_reasons"]
    assert broken["unmeasured_reasons"][0].startswith("telemetry_measurement_failed")
    assert broken["stop_run"] is False

    not_a_record = assess_resource_telemetry(["not", "a", "record"], caps=B1_RESOURCE_CAPS)
    assert not_a_record["resources_unmeasured"] is True
    assert not_a_record["stop_run"] is False


def test_measured_cap_exceedance_is_recorded_and_only_the_wall_cap_stops() -> None:
    caps = ResourceCaps(
        wall_seconds=20.0,
        process_tree_peak_rss_bytes=512,
        scratch_high_water_bytes=0,
        durable_high_water_bytes=512,
    )
    over = assess_resource_telemetry(_measurement(), caps=caps)
    assert over["resources_unmeasured"] is False
    assert over["cap_exceedances"] == [
        "process_tree_peak_rss_bytes", "durable_high_water_bytes",
    ]
    assert over["stopping_cap_exceedances"] == []
    assert over["stop_run"] is False

    wall_over = assess_resource_telemetry(
        _measurement(), caps=ResourceCaps(wall_seconds=1.0)
    )
    assert wall_over["cap_exceedances"] == ["wall_seconds"]
    assert wall_over["stop_run"] is True

    inside = assess_resource_telemetry(_measurement(), caps=B1_RESOURCE_CAPS)
    assert inside["resources_unmeasured"] is False
    assert inside["cap_exceedances"] == []
    assert inside["stop_run"] is False


def test_slot_evidence_records_unmeasured_resources_without_refusing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        b1, "_slot_paths",
        lambda root, index, seed, arm: {
            "raw": [tmp_path / "result.json"],
            "admission": [tmp_path / "admission.json"],
            "telemetry": [],
        },
    )
    monkeypatch.setattr(
        b1, "_unwrap_worker_result",
        lambda wrapper: {
            "attempt_id": "attempt-1", "seed": 21101, "arm": "RAW-GRU",
            "full_bindings": {"implementation_commit": "a" * 40},
        },
    )
    monkeypatch.setattr(b1, "validate_bound_admission", lambda value, **kwargs: value)
    monkeypatch.setattr(b1, "_inventory_digest", lambda root, paths: "d" * 64)
    monkeypatch.setattr(
        b1, "_slot_file_digest", lambda root, index, seed, arm: "e" * 64
    )
    (tmp_path / "result.json").write_text("{}", encoding="utf-8")
    (tmp_path / "admission.json").write_text("{}", encoding="utf-8")

    _, _, telemetry_record, _ = b1._load_slot_evidence(
        tmp_path, 0, 21101, "RAW-GRU",
        expected_attempt_id="attempt-1", expected_commit="a" * 40,
    )
    assert telemetry_record["resources_unmeasured"] is True
    assert telemetry_record["unmeasured_reasons"] == ["telemetry_missing"]
    assert telemetry_record["recorded_cap_exceedances"] == []
    assert telemetry_record["invocations"] == []


# (v) learner-side instrumentation failure still quarantines ------------------


def test_learner_side_instrumentation_failure_still_quarantines() -> None:
    facts = _facts()
    facts["learner_visibility_records"][0]["visible_fields"] = [
        "primitive_token", "overall_valid_truth",
    ]
    facts["checkpoint_records"][0]["restored_parameter_sha256"] = "f" * 64
    facts["reset_records"][0]["observed_fp32_bits"] = ["3f800000"]

    mechanical = compute_b1_mechanical(facts, [_competence(seed) for seed in SEEDS])

    assert mechanical["mechanical_conformance_pass"] is False
    for code in (
        "RECURRENT_RESET_FAILURE",
        "CHECKPOINT_ROUNDTRIP_FAILURE",
        "LEARNER_LEAKAGE",
    ):
        assert code in mechanical["blocking_audit_codes"]
    # Non-polar: no branch, polarity or trigger is invented by the failure.
    assert "scientific_branch" not in mechanical
    assert "scientific_polarity" not in mechanical
    assert "b2_extension_trigger" not in mechanical


def test_absent_worker_result_still_refuses_at_the_slot_boundary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        b1, "_slot_paths",
        lambda root, index, seed, arm: {
            "raw": [], "admission": [], "telemetry": [],
        },
    )
    with pytest.raises(b1.B1OrchestrationError):
        b1._load_slot_evidence(
            tmp_path, 0, 21101, "RAW-GRU",
            expected_attempt_id="attempt-1", expected_commit="a" * 40,
        )
