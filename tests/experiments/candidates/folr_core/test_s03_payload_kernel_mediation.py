from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from argparse import Namespace

import numpy as np
import pytest

from experiments.candidates.folr_core import registration as reg
from experiments.candidates.folr_core import s03_payload_kernel_mediation as probe
from scripts import run_folr_a1_s03_payload_kernel_mediation as cli


@pytest.fixture(scope="module")
def development_artifact():
    artifact = probe.run_probe(
        registration=reg.development_registration(),
        source_commit="TECHNICAL_SMOKE",
        run_id="folr_a1_development_test",
        technical_only=True,
    )
    assert artifact["technical_only"] is True
    assert artifact["scientific_terminal_admitted"] is False
    return artifact


def _must_reject(artifact, pattern: str | None = None):
    with pytest.raises(ValueError, match=pattern):
        probe.validate_artifact(artifact)


def test_development_probe_is_exactly_six_fresh_forwards_and_zero_resource(
    development_artifact,
):
    validated = probe.validate_artifact(development_artifact)
    assert validated == {
        "valid": True,
        "decision": probe.S03_PAYLOAD_MEDIATION_ACCESS_SUPPORTED,
        "arm_count": 6,
        "policy_forwards": 6,
        "environment_transitions": 0,
        "completed_admission_supported": True,
    }
    assert tuple(development_artifact["arms"]) == probe.ARM_NAMES
    counts = development_artifact["scientific_activity_counts"]
    assert counts["complete_kernel_readouts"] == 6
    assert counts["policy_forwards"] == 6
    assert counts["lifecycle_transactions_started"] == 6
    assert all(
        counts[name] == 0
        for name in (
            "environment_episodes",
            "environment_transitions",
            "hypothetical_transitions",
            "learner_calls",
            "trainer_calls",
            "optimizer_updates",
            "return_evaluations",
        )
    )


def test_branch_identity_is_metadata_only_and_payload_is_the_only_actor_difference(
    development_artifact,
):
    analysis = development_artifact["analysis"]
    assert analysis["contrasts"]["fixed_payload_nulls"] == {
        "payload_0": 0.0,
        "payload_1": 0.0,
    }
    assert all(
        value > 0.0
        for value in analysis["contrasts"]["within_branch_payload"].values()
    )
    assert analysis["contrasts"]["reset"] == 0.0
    admission = analysis["completed_admission"]
    assert admission["checks"]["one_common_source_snapshot"]
    assert admission["checks"]["one_non_s03_actor_preimage"]
    assert admission["checks"]["branch_metadata_not_in_runtime"]


def test_sentinel_prevents_action_rng_ledgers_and_a_second_forward(development_artifact):
    for arm in development_artifact["arms"].values():
        witness = arm["witnesses"]
        assert witness["sentinel_caught"]
        assert witness["kernel_capture_count"] == 1
        assert witness["kernel_producing_policy_forwards"] == 1
        assert witness["rng_states_unchanged"]
        assert witness["ledgers_unchanged"]
        assert witness["action_selection_reached"] is False
        assert witness["pending_membership_transaction_before"] is False
        assert witness["pending_membership_transaction_after"] is False


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_arm",
        "extra_arm",
        "different_common_snapshot",
        "branch_runtime_injection",
        "owner_epoch_drift",
        "clock_drift",
        "legal_mask_drift",
        "cached_crossing",
        "pending_crossing",
        "action_reached",
        "rng_crossing",
        "ledger_crossing",
        "second_forward",
        "reset_not_neutral",
        "nonzero_resource_counter",
    ),
)
def test_validator_rejects_admission_and_cap_violations(development_artifact, mutation):
    broken = deepcopy(development_artifact)
    first = probe.ARM_NAMES[0]
    second = probe.ARM_NAMES[1]
    if mutation == "missing_arm":
        broken["arms"].pop(first)
    elif mutation == "extra_arm":
        broken["arms"]["K_extra"] = deepcopy(broken["arms"][first])
    elif mutation == "different_common_snapshot":
        broken["arms"][second]["common_source_snapshot_digest"] = "different"
    elif mutation == "branch_runtime_injection":
        broken["arms"][first]["witnesses"]["branch_identity_injected_into_runtime"] = True
    elif mutation == "owner_epoch_drift":
        broken["arms"][second]["kernel"]["membership_epoch"] += 1
    elif mutation == "clock_drift":
        broken["arms"][second]["witnesses"]["clock_at_capture"]["physical_time"] += 1
    elif mutation == "legal_mask_drift":
        broken["arms"][second]["witnesses"]["complete_legal_mask"][0] = False
    elif mutation == "cached_crossing":
        broken["arms"][first]["witnesses"]["cached_action_or_kernel_crossing"] = True
    elif mutation == "pending_crossing":
        broken["arms"][first]["witnesses"]["pending_membership_transaction_after"] = True
    elif mutation == "action_reached":
        broken["arms"][first]["witnesses"]["action_selection_reached"] = True
    elif mutation == "rng_crossing":
        broken["arms"][first]["witnesses"]["rng_states_unchanged"] = False
    elif mutation == "ledger_crossing":
        broken["arms"][first]["witnesses"]["ledgers_unchanged"] = False
    elif mutation == "second_forward":
        broken["arms"][first]["witnesses"]["kernel_capture_count"] = 2
    elif mutation == "reset_not_neutral":
        broken["arms"][probe.K_RESET_0]["witnesses"]["reset_target_neutral"] = False
    elif mutation == "nonzero_resource_counter":
        broken["scientific_activity_counts"]["environment_transitions"] = 1
    _must_reject(broken)


def test_synchronized_leakage_is_a_valid_frozen_negative_terminal(
    development_artifact,
):
    leakage = deepcopy(development_artifact)
    leakage["arms"][probe.ARM_NAMES[0]]["witnesses"][
        "branch_identity_injected_into_runtime"
    ] = True
    leakage["analysis"] = probe.analyze_artifact(leakage)
    leakage["decision"] = leakage["analysis"]["decision"]

    assert leakage["decision"] == probe.BRANCH_LABEL_OR_ALTERNATE_PATH_LEAKAGE
    assert leakage["analysis"]["completed_admission"]["all_pass"] is False
    assert probe.analyze_artifact(leakage) == leakage["analysis"]
    assert probe.validate_artifact(leakage) == {
        "valid": True,
        "decision": probe.BRANCH_LABEL_OR_ALTERNATE_PATH_LEAKAGE,
        "arm_count": 6,
        "policy_forwards": 6,
        "environment_transitions": 0,
        "completed_admission_supported": False,
    }


def test_synchronized_structural_forward_overrun_remains_invalid(development_artifact):
    broken = deepcopy(development_artifact)
    broken["arms"][probe.ARM_NAMES[0]]["witnesses"]["kernel_capture_count"] = 2
    broken["arms"][probe.ARM_NAMES[0]]["witnesses"][
        "kernel_producing_policy_forwards"
    ] = 2
    broken["analysis"] = probe.analyze_artifact(broken)
    broken["decision"] = broken["analysis"]["decision"]
    _must_reject(broken, "structural invariant all_single_forward")


def test_validator_rejects_an_incomplete_probability_vector(development_artifact):
    broken = deepcopy(development_artifact)
    arm = broken["arms"][probe.ARM_NAMES[0]]
    probability = probe._decode_array(arm["kernel"]["probabilities"])
    arm["kernel"]["probabilities"] = probe._array_record(probability[:-1])
    _must_reject(broken, "complete legal-action kernel")


def test_tv_uses_complete_vectors_not_action_samples(development_artifact):
    left = np.asarray([0.1, 0.2, 0.7], dtype=np.float32)
    right = np.asarray([0.2, 0.3, 0.5], dtype=np.float32)
    expected = 0.5 * float(
        np.sum(np.abs(left.astype(np.float64) - right.astype(np.float64)))
    )
    assert probe.total_variation(left, right) == expected

    broken = deepcopy(development_artifact)
    broken["analysis"]["contrasts"]["formula"] = "sampled action frequency"
    broken["analysis"]["sample_or_monte_carlo_used"] = True
    _must_reject(broken, "not canonical")


def test_frozen_decision_precedence_is_exact():
    classify = probe.classify
    assert classify(
        prerequisite_valid=False,
        completed_admission_valid=False,
        fixed_payload_nulls=(1.0, 1.0),
        within_branch_payload_tvs=(0.0, 0.0),
        reset_tv=1.0,
    ) == probe.PREREQUISITE_UNAVAILABLE_OR_INVALID
    assert classify(
        prerequisite_valid=True,
        completed_admission_valid=False,
        fixed_payload_nulls=(0.0, 0.0),
        within_branch_payload_tvs=(1.0, 1.0),
        reset_tv=1.0,
    ) == probe.BRANCH_LABEL_OR_ALTERNATE_PATH_LEAKAGE
    assert classify(
        prerequisite_valid=True,
        completed_admission_valid=True,
        fixed_payload_nulls=(0.0, 0.0),
        within_branch_payload_tvs=(1.0, 1.0),
        reset_tv=np.nextafter(0.0, 1.0),
    ) == probe.RESET_DOES_NOT_ERASE
    assert classify(
        prerequisite_valid=True,
        completed_admission_valid=True,
        fixed_payload_nulls=(0.0, 0.0),
        within_branch_payload_tvs=(0.0, 0.0),
        reset_tv=0.0,
    ) == probe.NO_S03_PAYLOAD_EFFECT
    assert classify(
        prerequisite_valid=True,
        completed_admission_valid=True,
        fixed_payload_nulls=(0.0, 0.0),
        within_branch_payload_tvs=(np.nextafter(0.0, 1.0), 0.0),
        reset_tv=0.0,
    ) == probe.S03_PAYLOAD_MEDIATION_ACCESS_SUPPORTED


def test_invalid_production_binding_stops_before_any_readout():
    development = reg.development_registration()
    invalid = replace(development, development_only=False)
    result = probe.run_probe(
        registration=invalid,
        source_commit="not-the-head",
        run_id="invalid_prerequisite",
        technical_only=False,
    )
    assert result["decision"] == probe.PREREQUISITE_UNAVAILABLE_OR_INVALID
    assert result["arms"] == {}
    assert result["scientific_activity_counts"]["policy_forwards"] == 0
    assert result["scientific_activity_counts"]["complete_kernel_readouts"] == 0
    assert result["scientific_activity_counts"]["lifecycle_transactions_started"] == 0
    assert result["scientific_terminal_admitted"] is True
    assert result["prerequisite_admission"]["error"]
    assert result["prerequisite_admission"]["identity"]["cell_identifier"]
    assert probe.analyze_artifact(result) == result["analysis"]
    assert probe.validate_artifact(result) == {
        "valid": True,
        "decision": probe.PREREQUISITE_UNAVAILABLE_OR_INVALID,
        "arm_count": 0,
        "policy_forwards": 0,
        "environment_transitions": 0,
    }


def test_prerequisite_artifact_rejects_partial_or_nonzero_activity(development_artifact):
    development = reg.development_registration()
    zero = probe.run_probe(
        registration=replace(development, development_only=False),
        source_commit="not-the-head",
        run_id="invalid_prerequisite_shape",
        technical_only=False,
    )

    partial = deepcopy(zero)
    partial["arms"][probe.ARM_NAMES[0]] = deepcopy(
        development_artifact["arms"][probe.ARM_NAMES[0]]
    )
    with pytest.raises(ValueError, match="exact ordered six-arm roster"):
        probe.analyze_artifact(partial)
    _must_reject(partial, "six distinct arms")

    nonzero = deepcopy(zero)
    nonzero["scientific_activity_counts"]["policy_forwards"] = 1
    with pytest.raises(ValueError, match="nonzero or incomplete activity"):
        probe.analyze_artifact(nonzero)
    _must_reject(nonzero, "nonzero or incomplete activity")


def test_cli_materializes_a_prerequisite_terminal_as_success(
    development_artifact, monkeypatch
):
    development = reg.development_registration()
    zero = probe.run_probe(
        registration=replace(development, development_only=False),
        source_commit="not-the-head",
        run_id="cli_prerequisite",
        technical_only=False,
    )
    monkeypatch.setattr(cli.reg, "development_registration", lambda: development)
    monkeypatch.setattr(cli.probe, "run_probe", lambda **_kwargs: zero)

    captured = {}

    class InMemoryArtifact:
        def read_bytes(self):
            return b"canonical-prerequisite-artifact"

        def __str__(self):
            return "IN_MEMORY/prerequisite.json"

    def write_json(artifact, path):
        captured["artifact"] = deepcopy(artifact)
        captured["path"] = path
        return InMemoryArtifact()

    monkeypatch.setattr(cli.probe, "write_json", write_json)
    exit_code = cli._run(
        Namespace(
            technical_smoke=True,
            source_commit="TECHNICAL_SMOKE",
            run_id="cli_prerequisite",
            output="IN_MEMORY/prerequisite.json",
        )
    )
    assert exit_code == 0
    written = captured["artifact"]
    assert written["decision"] == probe.PREREQUISITE_UNAVAILABLE_OR_INVALID
    assert probe.validate_artifact(written)["valid"] is True
