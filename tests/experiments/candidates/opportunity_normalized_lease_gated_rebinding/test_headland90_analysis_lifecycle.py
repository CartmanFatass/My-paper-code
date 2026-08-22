from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json
import math
from pathlib import Path

import pytest

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import analysis
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import controllers
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import lifecycle
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90.event_transform import (
    event_transform,
    float_bits,
)


F = Fraction


def mean_proof(value: float, coordinate: bytes = b"9:fixture|3:row"):
    return controllers.canonical_neumaier_mean([(coordinate, float(value))])


def summaries(candidates, *, mean=F(0), tail=F(0), updates=0, mean_lambda=0.0):
    proof = (
        mean_lambda
        if mean_lambda is None or isinstance(mean_lambda, controllers.CanonicalNeumaierMean)
        else mean_proof(float(mean_lambda))
    )
    return {
        candidate: controllers.CalibrationSummary(mean, tail, updates, proof)
        for candidate in candidates
    }


def passing_two_gates() -> dict[str, analysis.PositiveGate]:
    return {
        "D_S": analysis.PositiveGate(0.02, 0.001, 0.50, 0.02),
        "D_L": analysis.PositiveGate(0.02, 0.001, 0.50, 0.02),
        "Delta_mean": analysis.PositiveGate(0.02, 0.001, 0.50, 0.02),
        "Delta_tail": analysis.PositiveGate(0.05, 0.001, 0.50, 0.05),
    }


def flex_gates(*, passing: bool = True, mean_sd: float = 0.01, tail_sd: float = 0.01):
    return {
        "Delta_FLEX_mean": analysis.PositiveGate(
            0.02 if passing else 0.0, 0.001 if passing else -0.001, mean_sd, 0.02
        ),
        "Delta_FLEX_tail": analysis.PositiveGate(
            0.05 if passing else 0.0, 0.001 if passing else -0.001, tail_sd, 0.05
        ),
    }


def result_facts(**changes) -> analysis.ResultMapFacts:
    facts = analysis.ResultMapFacts(
        common_nonidentification_reason=None,
        two_is_answerable=True,
        two_nonidentification_reason=None,
        selected_q_short=F(3, 8),
        selected_q_long=F(1, 8),
        two_gates=passing_two_gates(),
        flex_adaptive_answerable=True,
        flex_global_gates=flex_gates(),
        flex_two_relation=analysis.FLEX_TWO_COMPATIBLE,
    )
    return replace(facts, **changes)


def manifest_inputs() -> dict[str, object]:
    return {
        "source_hashes": {"headland90/controllers.py": "a" * 64},
        "config_facts": {
            "card_revision": lifecycle.CARD_REVISION,
            "production_namespace": controllers.PRODUCTION_NAMESPACE,
            "canonical_controller_replicates": 9856,
            "canonical_physical_ticks": 37_847_040,
        },
        "schema_facts": {
            "coordinate_schema": controllers.coordinate_schema_facts(),
            "result_schema": {"declared_only": True},
        },
        "conformance_facts": {
            "registry_cardinality": 192,
            "registry_order_checked": True,
            "formula_checks_passed": True,
        },
    }


def test_registry_is_exact_ordered_192_member_union_and_contains_every_lookup():
    controllers.assert_registry_conformance()
    registry = controllers.CONTROLLER_REGISTRY
    assert len(registry) == len(set(registry)) == 192
    assert registry[:64] == controllers.LOOKUP_REGISTRY
    assert registry[64:] == controllers.TIMING_REGISTRY
    assert {
        (row.alpha_short, row.alpha_long) for row in controllers.LOOKUP_REGISTRY
    } == {(q_s, q_l) for q_s in range(8) for q_l in range(8)}
    first = controllers.TIMING_REGISTRY[0]
    eighth = controllers.TIMING_REGISTRY[7]
    ninth = controllers.TIMING_REGISTRY[8]
    assert controllers.coefficient_tuple(first) == (
        F(1, 8), F(1, 8), F(1, 8), F(1, 8), F(0), F(0)
    )
    assert controllers.coefficient_tuple(eighth)[2:] == (F(0), F(0), F(-1, 8), F(1, 8))
    assert controllers.coefficient_tuple(ninth)[:2] == (F(1, 8), F(3, 8))
    assert all(controllers.is_lookup(row) for row in registry[:64])
    assert all(controllers.is_timing_member(row) for row in registry[64:])


def test_exact_rate_map_clipping_event_formula_and_audit_distinctness():
    positive = controllers.TIMING_REGISTRY[0]
    assert controllers.controller_rate_fraction(positive, "S", F(1), F(1, 2)) == F(3, 16)
    assert controllers.controller_rate_fraction(positive, "L", F(0), F(1, 2)) == F(1, 16)
    steep = controllers.ControllerSpec(7, 7, 1, 1, 0, 0)
    assert controllers.controller_rate_fraction(steep, "S", F(1), F(1, 2)) == F(7, 8)
    assert controllers.event_probability(F(0), 0.25) == 0.0
    for q in controllers.Q:
        _, expected_lambda, expected_event = event_transform(q)
        assert float_bits(controllers.rate_lambda(q)) == float_bits(expected_lambda)
        assert float_bits(controllers.event_probability(q, F(1, 4))) == float_bits(expected_event)
    with pytest.raises(ValueError, match="exactly Delta_t"):
        controllers.event_probability(F(1, 2), 4.0)
    two = controllers.lookup_controller(F(1, 8), F(1, 8))
    assert controllers.algebraically_distinct(positive, two)
    assert not controllers.algebraically_distinct(two, two)


def test_global_two_and_flex_total_orders_include_every_tie_precedence():
    global_rows = summaries(controllers.CONTROLLER_REGISTRY)
    q1 = controllers.lookup_controller(F(1, 8), F(1, 8))
    q2 = controllers.lookup_controller(F(2, 8), F(2, 8))
    global_rows[q1] = controllers.CalibrationSummary(F(1), F(1, 4), 3, mean_proof(0.0))
    global_rows[q2] = controllers.CalibrationSummary(F(1), F(1, 2), 4, mean_proof(0.0))
    assert controllers.select_global(global_rows) == q2  # tail precedes updates
    global_rows[q1] = controllers.CalibrationSummary(F(1), F(1, 2), 3, mean_proof(0.0))
    assert controllers.select_global(global_rows) == q1  # updates precede q
    global_rows[q2] = controllers.CalibrationSummary(F(1), F(1, 2), 3, mean_proof(0.0))
    assert controllers.select_global(global_rows) == q1  # smallest q

    two_rows = summaries(controllers.LOOKUP_REGISTRY)
    left = controllers.lookup_controller(F(0), F(1, 8))
    right = controllers.lookup_controller(F(1, 8), F(0))
    two_rows[left] = controllers.CalibrationSummary(F(1), F(1), 2)
    two_rows[right] = controllers.CalibrationSummary(F(1), F(1), 2)
    assert controllers.select_two_stratum(two_rows) == left  # equal lambda sum; q_S then q_L
    slower = controllers.lookup_controller(F(1, 8), F(1, 8))
    two_rows[slower] = controllers.CalibrationSummary(F(1), F(1), 2)
    assert controllers.select_two_stratum(two_rows) == left  # smaller lambda sum

    flex_rows = summaries(controllers.CONTROLLER_REGISTRY, mean_lambda=1.0)
    early, late = controllers.CONTROLLER_REGISTRY[70], controllers.CONTROLLER_REGISTRY[71]
    flex_rows[early] = controllers.CalibrationSummary(F(1), F(1), 2, mean_proof(0.2))
    flex_rows[late] = controllers.CalibrationSummary(F(1), F(1), 2, mean_proof(0.1))
    assert controllers.select_flex(flex_rows) == late
    flex_rows[early] = controllers.CalibrationSummary(F(1), F(1), 2, mean_proof(0.1))
    assert controllers.select_flex(flex_rows) == min(
        (early, late), key=controllers.coefficient_tuple
    )  # exact rational coefficient tuple, not registry ordinal


def test_selector_summaries_require_exact_endpoints_and_binary64_mean_lambda():
    normalized = controllers.CalibrationSummary(1, F(1, 2), 0, mean_proof(0.0))
    assert normalized.mean_value == F(1) and normalized.tail_value == F(1, 2)
    for field in ("mean_value", "tail_value"):
        kwargs = {"mean_value": F(1, 2), "tail_value": F(1, 2), "voluntary_updates": 0}
        kwargs[field] = 0.5
        with pytest.raises(TypeError, match="exact int or Fraction"):
            controllers.CalibrationSummary(**kwargs)
    with pytest.raises(TypeError, match="proof-carrying"):
        controllers.CalibrationSummary(F(0), F(0), 0, 0)
    with pytest.raises(TypeError, match="proof-carrying"):
        controllers.CalibrationSummary(F(0), F(0), 0, 0.1)
    for invalid in (-0.0 - 0.1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="finite and nonnegative"):
            controllers.canonical_neumaier_mean([(b"row", invalid)])


def test_canonical_neumaier_mean_is_order_independent_and_compensated():
    rows = [(b"c", 1.0), (b"a", 1.0e16), (b"b", 1.0)]
    forward = controllers.canonical_neumaier_mean(rows)
    reverse = controllers.canonical_neumaier_mean(reversed(rows))
    assert forward == reverse
    assert forward.row_count == 3
    assert forward.value == (1.0e16 + 2.0) / 3
    assert forward.value != sum(value for _, value in rows) / len(rows)
    assert len(forward.order_digest) == len(forward.content_digest) == 64
    with pytest.raises(ValueError, match="unique"):
        controllers.canonical_neumaier_mean([(b"same", 0.1), (b"same", 0.2)])


def test_exact_rational_selector_ties_do_not_collapse_through_float_rounding():
    rows = summaries(controllers.CONTROLLER_REGISTRY)
    smaller = controllers.lookup_controller(F(1, 8), F(1, 8))
    larger = controllers.lookup_controller(F(2, 8), F(2, 8))
    exact_base = F(1, 2)
    exact_increment = F(1, 2**60)
    assert float(exact_base) == float(exact_base + exact_increment)
    rows[smaller] = controllers.CalibrationSummary(exact_base, F(0), 0, mean_proof(0.0))
    rows[larger] = controllers.CalibrationSummary(
        exact_base + exact_increment, F(0), 10, mean_proof(0.0)
    )
    assert controllers.select_global(rows) == larger

    flex_rows = summaries(controllers.CONTROLLER_REGISTRY, mean_lambda=1.0)
    first, second = controllers.CONTROLLER_REGISTRY[64:66]
    flex_rows[first] = controllers.CalibrationSummary(F(1), F(1), 0, mean_proof(0.1))
    flex_rows[second] = controllers.CalibrationSummary(
        F(1), F(1), 0, mean_proof(math.nextafter(0.1, 0.0))
    )
    assert controllers.select_flex(flex_rows) == second


def test_alias_ledger_preserves_all_five_logical_tags_and_exact_identity():
    global_best = controllers.lookup_controller(F(1, 8), F(1, 8))
    two = controllers.lookup_controller(F(3, 8), F(1, 8))
    ledger = controllers.identity_preserving_alias_ledger(
        global_best=global_best, two_stratum=two, flex=global_best
    )
    assert tuple(row.logical_tag for row in ledger) == controllers.LOGICAL_HELD_OUT_TAGS
    aliases = ("GLOBAL-BEST", "FLEX-CONTAIN", "C_S<-L")
    for index in (0, 2, 3):
        assert ledger[index].exact_aliases == aliases
        assert ledger[index].physical_map_id == ledger[0].physical_map_id
    assert len({row.logical_tag for row in ledger}) == 5
    assert ledger[1].physical_map_id != ledger[4].physical_map_id


def test_realized_support_keeps_duplicates_and_uses_exact_registered_thresholds():
    two = controllers.lookup_controller(F(1, 8), F(1, 8))
    flex = controllers.TIMING_REGISTRY[0]
    different = controllers.OpportunityRecord("S", F(1), F(1, 2))
    same = controllers.OpportunityRecord("S", F(1, 2), F(1, 2))
    result = controllers.realized_support_distinctness(
        flex, two, [different, different], [same] * 18
    )
    assert result.row_fraction == F(1, 10)
    assert result.time_weighted_absolute_difference == F(1, 160)
    assert not result.distinct  # frequency passes, magnitude fails
    assert not controllers.realized_support_distinctness(flex, two, [], []).distinct


def test_coordinate_schema_is_exact_and_never_accepts_materialized_words_or_cells():
    schema = controllers.coordinate_schema_facts()
    assert controllers.validate_coordinate_schema(schema) == ()
    assert tuple(schema["fields"]) == controllers.COORDINATE_FIELDS
    assert tuple(schema["streams"]) == controllers.COUNTER_STREAMS
    contaminated = dict(schema)
    contaminated["counter_words"] = [0.25]
    assert controllers.validate_coordinate_schema(contaminated) == (
        "coordinate schema differs from the frozen card",
        "coordinate schema contains materialized coordinate or random-word data",
    )


def test_endpoint_formulas_keep_exact_physical_time_weighting_and_lower_decile():
    assert analysis.service_fraction(16, 32) == F(1, 2)
    assert analysis.block_value(F(1), F(0)) == F(1, 5)
    blocks = [F(i, 20) for i in range(20)]
    endpoints = analysis.replicate_endpoints(blocks)
    assert endpoints.mean_value == F(19, 40)
    assert endpoints.tail_value == F(1, 40)  # average of 0 and 1/20
    assert analysis.lower_cvar([F(i, 10) for i in range(3)], F(1, 2)) == F(1, 30)
    panel = analysis.panel_endpoints([endpoints, endpoints])
    assert panel.mean_value == endpoints.mean_value
    assert panel.tail_value == endpoints.tail_value


def test_paired_interval_and_positive_gate_strictness_and_power_rules():
    differences = [0.0] * 64 + [0.04] * 64
    interval = analysis.paired_interval(differences)
    expected_sd = math.sqrt(128 * (0.02**2) / 127)
    assert interval.mean == pytest.approx(0.02)
    assert interval.sample_sd == pytest.approx(expected_sd)
    assert interval.lower == pytest.approx(0.02 - 1.97882 * expected_sd / math.sqrt(128))
    assert not analysis.PositiveGate(0.02, 0.0, 0.01, 0.02).passes
    gates = passing_two_gates()
    assert analysis.two_nonpass_power_adequate(gates)  # passed gates ignore high SD
    gates["D_S"] = analysis.PositiveGate(0.0, -0.01, 0.081, 0.02)
    assert not analysis.two_nonpass_power_adequate(gates)
    gates["D_S"] = analysis.PositiveGate(0.0, -0.01, 0.080, 0.02)
    assert analysis.two_nonpass_power_adequate(gates)


def test_nonharm_competence_and_response_identification_formulas():
    zero = analysis.HardSafetyFacts()
    unsafe = analysis.HardSafetyFacts(separation_breaches=1)
    assert zero.hard_safe and not unsafe.hard_safe
    assert analysis.override_fraction(384) == F(1, 10)
    assert analysis.override_ucb95([0] * 128, [0] * 128) == 0.0
    assert analysis.selected_controller_nonharm(zero, zero, 0.01)
    assert not analysis.selected_controller_nonharm(zero, unsafe, 0.0)
    support = {"S": analysis.SupportFacts(256, 256, 96), "L": analysis.SupportFacts(300, 300, 100)}
    assert analysis.global_competent(
        selected_nonharm=True,
        calibration_mean=F(19, 20),
        held_out_mean=F(1, 4),
        held_out_tail=F(1, 10),
        support_by_stratum=support,
    )
    assert analysis.rate_response_identified(
        selected_short=F(3, 8),
        selected_long=F(1, 8),
        maxima_short_cal={F(3, 8)},
        maxima_long_cal={F(1, 8)},
        maxima_short_c1={F(2, 8)},
        maxima_short_c2={F(4, 8)},
        maxima_long_c1={F(0)},
        maxima_long_c2={F(2, 8)},
    )
    containment = analysis.flex_containment_answerable(
        package_valid=True,
        global_is_competent=True,
        support_adequate=True,
        selected_nonharm=True,
        algebraically_distinct=True,
        realized_support_distinct=True,
    )
    assert analysis.flex_adaptive_answerable(
        containment_answerable=containment, timing_member=True
    )
    assert analysis.flex_global_qualifies(adaptive_answerable=True, gates=flex_gates())


@pytest.mark.parametrize(
    ("mean", "tail", "expected"),
    [
        ((0.0, -0.005, 0.005, 0.01), (0.0, -0.005, 0.005, 0.01), analysis.FLEX_TWO_COMPATIBLE),
        ((-0.02, -0.03, -0.015, 0.01), (0.0, -0.005, 0.005, 0.01), analysis.FLEX_STABLE_LOSS),
        ((0.02, -0.005, 0.03, 0.04), (0.0, -0.005, 0.005, 0.01), analysis.FLEX_RELATION_UNRESOLVED),
        ((0.02, -0.005, 0.03, 0.041), (0.0, -0.005, 0.005, 0.01), analysis.FLEX_RELATION_POWER_NONIDENTIFYING),
    ],
)
def test_flex_two_relation_branches(mean, tail, expected):
    def interval(row):
        point, lower, upper, sd = row
        return analysis.PairedInterval(point, sd, lower, upper, 128)

    assert analysis.flex_two_relation(
        interval(mean), interval(tail), flex_adaptive_answerable=True, two_is_answerable=True
    ) == expected
    assert analysis.flex_two_relation(
        interval(mean), interval(tail), flex_adaptive_answerable=False, two_is_answerable=True
    ) == analysis.FLEX_RELATION_NOT_ANSWERABLE


def test_exhaustive_result_map_common_and_two_nonidentification_branches():
    common = analysis.evaluate_result_map(
        result_facts(common_nonidentification_reason="PACKAGE_INVALID")
    )
    assert common.primary == "PACKAGE_INVALID"
    assert common.flex_global_interpretation == "FLEX_NOT_INFERENTIAL_UNDER_COMMON_NONIDENTIFICATION"
    two_missing = analysis.evaluate_result_map(
        result_facts(two_is_answerable=False, two_nonidentification_reason="RECIPROCAL_CONTROLS_INVALID")
    )
    assert two_missing.primary == "RECIPROCAL_CONTROLS_INVALID"
    assert two_missing.flex_continuous_timing_question


def test_exhaustive_result_map_positive_opposite_nonpass_power_and_no_evidence():
    registered = analysis.evaluate_result_map(result_facts())
    assert registered.primary == "REGISTERED_TWO_RATE_QUALIFIES"
    assert registered.registered_two_rate_qualifies
    assert registered.flex_two_interpretation == analysis.FLEX_TWO_COMPATIBLE

    opposite = analysis.evaluate_result_map(
        result_facts(selected_q_short=F(1, 8), selected_q_long=F(3, 8))
    )
    assert opposite.primary == "OPPOSITE_SIGN_TWO_RATE"
    assert opposite.opposite_sign_two_rate and opposite.flex_continuous_timing_question

    failed = passing_two_gates()
    failed["D_S"] = analysis.PositiveGate(0.0, -0.01, 0.081, 0.02)
    power = analysis.evaluate_result_map(
        result_facts(two_gates=failed, flex_global_gates=flex_gates(passing=False))
    )
    assert power.primary == "TWO_POWER_NONIDENTIFYING"

    failed["D_S"] = analysis.PositiveGate(0.0, -0.01, 0.080, 0.02)
    nonpass = analysis.evaluate_result_map(
        result_facts(two_gates=failed, flex_global_gates=flex_gates(passing=False))
    )
    assert nonpass.primary == "VALID_TWO_RATE_NONPASS"
    assert nonpass.no_current_timing_evidence

    equality = analysis.evaluate_result_map(
        result_facts(
            selected_q_short=F(1, 8), selected_q_long=F(1, 8),
            flex_global_gates=flex_gates(passing=False, mean_sd=0.081),
        )
    )
    assert equality.primary == "VALID_TWO_RATE_NONPASS"
    assert equality.flex_global_interpretation == "FLEX_POWER_NONIDENTIFYING"
    assert not equality.no_current_timing_evidence


def test_construction_manifest_is_deterministic_atomic_write_once_and_verifiable(tmp_path: Path):
    kwargs = manifest_inputs()
    left = lifecycle.build_construction_manifest(**kwargs)
    right = lifecycle.build_construction_manifest(**kwargs)
    assert lifecycle.canonical_json_bytes(left) == lifecycle.canonical_json_bytes(right)
    seal = lifecycle.seal_construction_manifest(
        tmp_path / "seal", allowed_root=tmp_path, **kwargs
    )
    assert seal.manifest_path.name == f"construction-manifest-{seal.sha256}.json"
    assert not (seal.artifact_root / ".construction-manifest.tmp").exists()
    verified = lifecycle.verify_construction_manifest(
        seal.artifact_root, allowed_root=tmp_path, expected_sha256=seal.sha256
    )
    assert verified == left
    assert verified["future_empirical_runner"] == {
        "present": False,
        "required_preactivity_guard": lifecycle.FUTURE_PRODUCTION_GUARD,
        "guard_invoked_by_this_lifecycle": False,
    }
    with pytest.raises(FileExistsError, match="write-once"):
        lifecycle.seal_construction_manifest(
            tmp_path / "seal", allowed_root=tmp_path, **kwargs
        )


def test_construction_manifest_detects_tamper_extras_and_root_escape(tmp_path: Path):
    kwargs = manifest_inputs()
    tampered = lifecycle.seal_construction_manifest(
        tmp_path / "tampered", allowed_root=tmp_path, **kwargs
    )
    document = json.loads(tampered.manifest_path.read_bytes())
    document["conformance_facts"]["registry_cardinality"] = 191
    tampered.manifest_path.write_bytes(lifecycle.canonical_json_bytes(document))
    with pytest.raises(lifecycle.ConstructionManifestError, match="filename authentication"):
        lifecycle.verify_construction_manifest(
            tampered.artifact_root, allowed_root=tmp_path, expected_sha256=tampered.sha256
        )

    extra = lifecycle.seal_construction_manifest(tmp_path / "extra", allowed_root=tmp_path, **kwargs)
    (extra.artifact_root / "unexpected.txt").write_text("x", encoding="utf-8")
    with pytest.raises(lifecycle.ConstructionManifestError, match="exactly one"):
        lifecycle.verify_construction_manifest(extra.artifact_root, allowed_root=tmp_path)

    with pytest.raises(lifecycle.ConstructionManifestError, match="escapes"):
        lifecycle.seal_construction_manifest(
            tmp_path.parent / "escaped-headland90-seal", allowed_root=tmp_path, **kwargs
        )
    escaping_hashes = dict(kwargs)
    escaping_hashes["source_hashes"] = {"../outside.py": "b" * 64}
    with pytest.raises(lifecycle.ConstructionManifestError, match="escapes"):
        lifecycle.build_construction_manifest(**escaping_hashes)


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("config_facts", "production_random_words", [0.1]),
        ("schema_facts", "calibration_cells", [{"replicate": 0}]),
        ("schema_facts", "held_out_cells", [{"replicate": 0}]),
        ("conformance_facts", "result", {"mean": 0.5}),
        ("conformance_facts", "empirical_results", {"mean": 0.5}),
        ("conformance_facts", "scientific_activity_started", True),
        ("conformance_facts", "controller_ticks", 1),
    ],
)
def test_lifecycle_refuses_every_activity_boundary_payload(section, key, value):
    kwargs = manifest_inputs()
    facts = dict(kwargs[section])
    facts[key] = value
    kwargs[section] = facts
    with pytest.raises(lifecycle.ConstructionManifestError, match="forbidden|empirical"):
        lifecycle.build_construction_manifest(**kwargs)
