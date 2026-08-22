from __future__ import annotations

from dataclasses import replace

import pytest

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import analysis
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import contracts


def _interval(mean, sd, lower):
    return analysis.PairedInterval(mean, sd, lower, mean + 0.01, 128)


def _facts(**updates):
    value = analysis.ResultMapFacts(
        package_valid=True,
        sham_valid=True,
        common_host_valid=True,
        pairing_valid=True,
        endpoint_audit_valid=True,
        common_package_nonidentification_reason=None,
        never_is_competent=True,
        action_shell_support=True,
        effective_payload_support=True,
        road_is_nonharmful=True,
        road_nonharm_failure_fact=None,
        gate_statuses={name: "PASS" for name in analysis.GATE_NAMES},
    )
    return replace(value, **updates)


def test_paired_interval_requires_all_128_pairs():
    interval = analysis.paired_interval([0.02] * 128)
    assert interval.mean == pytest.approx(0.02)
    assert interval.sample_sd == 0.0
    assert interval.lower == pytest.approx(0.02)
    with pytest.raises(ValueError):
        analysis.paired_interval([0.02] * 127)


def test_gate_statuses_follow_exact_precedence_and_sd_limits():
    assert analysis.gate_status(_interval(0.02, 0.5, 0.001), endpoint="mean") == "PASS"
    assert (
        analysis.gate_status(_interval(0.019, 0.001, 0.018), endpoint="mean")
        == "MATERIALITY_RULE_NONPASS"
    )
    assert (
        analysis.gate_status(_interval(0.02, 0.080, 0.0), endpoint="mean")
        == "SIGN_PRECISE_NONPASS"
    )
    assert (
        analysis.gate_status(_interval(0.02, 0.081, 0.0), endpoint="mean")
        == "SIGN_POWER_NONIDENTIFYING"
    )
    assert (
        analysis.gate_status(_interval(0.05, 0.200, 0.0), endpoint="tail")
        == "SIGN_PRECISE_NONPASS"
    )


def test_full_panel_inference_has_four_gates_and_descriptive_raw_only():
    values = {
        contracts.NEVER_UPDATE: [analysis.ReplicateEndpoints(0.30, 0.20)] * 128,
        contracts.OVERHEAD_SHAM: [analysis.ReplicateEndpoints(0.30, 0.20)] * 128,
        contracts.RAW_ESTIMATE_PATCH: [analysis.ReplicateEndpoints(0.33, 0.23)] * 128,
        contracts.ROAD_TRACK_ESTIMATE_PATCH: [analysis.ReplicateEndpoints(0.36, 0.27)] * 128,
    }
    bundle = analysis.full_panel_inference(values)
    assert set(bundle.gate_statuses) == set(analysis.GATE_NAMES)
    assert set(bundle.intervals) == {
        "AN_MEAN", "AN_TAIL", "AH_MEAN", "AH_TAIL", "AR_MEAN", "AR_TAIL"
    }
    assert all(status == "PASS" for status in bundle.gate_statuses.values())


def test_support_competence_nonharm_and_observability_contracts():
    scheduled = {arm: 5120 for arm in contracts.ARMS}
    shells = {
        contracts.NEVER_UPDATE: 0,
        contracts.OVERHEAD_SHAM: 5120,
        contracts.RAW_ESTIMATE_PATCH: 5120,
        contracts.ROAD_TRACK_ESTIMATE_PATCH: 5120,
    }
    assert analysis.action_shell_support_ok(
        scheduled_t0_by_arm=scheduled, action_shell_by_arm=shells
    )
    assert analysis.effective_road_patch_support_ok(encounters=512, replicates_with_any=96)
    safe = analysis.HardSafetyFacts()
    assert analysis.never_competent(
        package_valid=True, hard_safety=safe, mean_value=0.25, tail_value=0.10
    )
    assert analysis.road_nonharm(hard_safety=safe, override_differences=[0.0] * 128)
    road_fit = analysis.RoadFitAuditFacts(True, True, True, True, True, True, True)
    package = analysis.PackageValidityFacts(
        True, True, True, True, True, True, True, True, True, True, road_fit
    )
    sham = analysis.ShamValidityFacts(True, True, True, True, True, True, True)
    assert package.valid and sham.valid


def test_ordered_result_map_all_nine_branches_and_first_match_precedence():
    invalid = _facts(
        package_valid=False,
        common_package_nonidentification_reason="COMMON_PACKAGE_ENDPOINT_AUDIT_INVALID",
        never_is_competent=False,
    )
    assert analysis.evaluate_result_map(invalid).branch == "COMMON_PACKAGE_ENDPOINT_AUDIT_INVALID"
    assert (
        analysis.evaluate_result_map(_facts(never_is_competent=False)).branch
        == "NEVER_UPDATE_COMPARATOR_NONIDENTIFIED"
    )
    assert (
        analysis.evaluate_result_map(_facts(action_shell_support=False)).branch
        == "ROAD_PATCH_ACTION_SUPPORT_NONIDENTIFIED"
    )
    assert (
        analysis.evaluate_result_map(
            _facts(
                road_is_nonharmful=False,
                road_nonharm_failure_fact="terrain_penetrations=1",
            )
        ).branch
        == "ROAD_PATCH_EXACT_PACKAGE_NONHARM_FAILED"
    )
    qualifies = analysis.evaluate_result_map(_facts())
    assert qualifies.branch == "ROAD_PATCH_DIRECT_UTILITY_QUALIFIES"
    assert qualifies.timing_question_portfolio_eligible
    power = {name: "PASS" for name in analysis.GATE_NAMES}
    power["AH_TAIL"] = "SIGN_POWER_NONIDENTIFYING"
    assert (
        analysis.evaluate_result_map(_facts(gate_statuses=power)).branch
        == "ROAD_PATCH_POWER_NONIDENTIFYING"
    )
    net_only = {name: "PASS" for name in analysis.GATE_NAMES}
    net_only["AH_MEAN"] = "MATERIALITY_RULE_NONPASS"
    assert (
        analysis.evaluate_result_map(_facts(gate_statuses=net_only)).branch
        == "NET_VALUE_WITHOUT_PAYLOAD_ISOLATION"
    )
    payload_only = {name: "PASS" for name in analysis.GATE_NAMES}
    payload_only["AN_TAIL"] = "SIGN_PRECISE_NONPASS"
    assert (
        analysis.evaluate_result_map(_facts(gate_statuses=payload_only)).branch
        == "PAYLOAD_BENEFIT_WITHOUT_MATERIAL_NET_UTILITY"
    )
    mixed = {name: "MATERIALITY_RULE_NONPASS" for name in analysis.GATE_NAMES}
    assert (
        analysis.evaluate_result_map(_facts(gate_statuses=mixed)).branch
        == "VALID_ROAD_PATCH_DIRECT_UTILITY_NONPASS"
    )
