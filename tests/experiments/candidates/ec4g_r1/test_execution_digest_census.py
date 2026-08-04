from __future__ import annotations

from dataclasses import replace
import json

import pytest

from experiments.candidates.ec4g_r1 import execution_digest_census as census


def _domain(cell: census.Cell) -> census.FrozenCensus:
    return census.FrozenCensus((cell.cell_id,), (cell,))


def _cell() -> census.Cell:
    return census.build_synthetic_witness().cells[0]


def test_exact_single_cell_witness_is_supported_behavioral_discordance():
    frozen = census.build_synthetic_witness()

    result = census.run_census(frozen)
    comparison = result.comparisons[0]
    values = comparison.contrasts

    assert result.classification is census.CensusClassification.BEHAVIORAL_DISCORDANCE
    assert result.issues == ()
    assert comparison.supported is True
    assert comparison.executor_measure == 1.0
    assert comparison.direct_tau.action is census.Action.PROBE
    assert comparison.ec4g.action is census.Action.ABSTAIN
    assert comparison.behavior_equal is False
    assert comparison.direct_tau.digest != comparison.ec4g.digest
    assert (values.tau_t.lower, values.tau_t.upper) == pytest.approx((0.08, 0.12))
    assert (values.tau_c.lower, values.tau_c.upper) == pytest.approx((-0.06, -0.02))
    assert (values.tau_v.lower, values.tau_v.upper) == pytest.approx((-0.035, -0.005))
    assert values.tau_t.point == pytest.approx(
        values.tau_b.point + values.tau_a.point + values.tau_c.point
    )
    assert values.tau_v.point == pytest.approx(
        values.tau_a.point + values.tau_c.point
    )
    assert comparison.point_difference == pytest.approx(-0.10)
    assert comparison.confidence_upper_bound == pytest.approx(-0.08)
    decision = json.loads(result.to_bytes())["cells"][0]["direct_tau"]
    assert decision == {
        "action": "P",
        "body_hex": comparison.direct_tau.body.hex(),
        "continuation_digest": comparison.direct_tau.digest,
        "delivery_channel": "synthetic-channel",
        "envelope_bytes_hex": b"GOOD".hex(),
        "envelope_id": "public-envelope-v1",
        "execution_path": "probe",
        "external_cost": 0.0,
        "receipt_variant": "RV",
    }


def test_census_returns_all_four_and_only_four_terminal_classes():
    cell = _cell()
    incomplete = census.run_census(
        _domain(replace(cell, receipts=replace(cell.receipts, authorized=False)))
    )

    both_probe = replace(
        cell,
        measured_means=(0.0, 0.30, 0.10, 0.15, 0.0, 0.0, 0.0),
    )
    equivalent = census.run_census(_domain(both_probe))

    probe, no_probe, fallback = cell.continuations
    label_only_probe = replace(fallback, action=probe.action)
    label_only = census.run_census(
        _domain(replace(cell, continuations=(label_only_probe, no_probe, fallback)))
    )
    behavioral = census.run_census(_domain(cell))

    assert incomplete.classification is census.CensusClassification.INCOMPLETE_CONTRACT
    assert equivalent.classification is census.CensusClassification.EQUIVALENCE
    assert label_only.classification is census.CensusClassification.LABEL_ONLY_DIFFERENCE
    assert label_only.comparisons[0].label_equal is False
    assert label_only.comparisons[0].behavior_equal is True
    assert label_only_probe.action is not fallback.action
    assert behavioral.classification is census.CensusClassification.BEHAVIORAL_DISCORDANCE
    assert {item.value for item in census.CensusClassification} == {
        "INCOMPLETE_CONTRACT",
        "EQUIVALENCE",
        "LABEL_ONLY_DIFFERENCE",
        "BEHAVIORAL_DISCORDANCE",
    }


def test_body_and_cost_only_clone_is_still_behaviorally_different():
    cell = _cell()
    probe, no_probe, fallback = cell.continuations
    values = (
        probe.execution_path, probe.receipt_variant, probe.delivery_channel,
        probe.envelope_id, probe.envelope_bytes, fallback.body, fallback.external_cost,
    )
    clone = replace(
        probe, body=fallback.body, external_cost=fallback.external_cost,
        digest=census.continuation_digest(*values),
    )

    result = census.run_census(_domain(replace(
        cell, continuations=(clone, no_probe, fallback),
    )))

    assert result.classification is census.CensusClassification.BEHAVIORAL_DISCORDANCE
    assert result.comparisons[0].behavior_equal is False


def test_both_gate_branch_tables_cover_unsupported_probe_no_probe_and_abstain():
    cell = _cell()
    unsupported = replace(
        cell,
        support_gates=((census.GATES[0], False), *cell.support_gates[1:]),
    )
    both_probe = replace(
        cell,
        measured_means=(0.0, 0.30, 0.10, 0.15, 0.0, 0.0, 0.0),
    )
    both_no_probe = replace(
        cell,
        measured_means=(0.0, -0.10, 0.0, 0.0, 0.0, 0.0, 0.0),
    )
    both_abstain = replace(
        cell,
        measured_means=(0.0, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0),
    )

    assert census.ec4g_gate(unsupported).action is census.Action.ABSTAIN
    assert census.direct_tau_gate(unsupported).action is census.Action.ABSTAIN
    assert census.ec4g_gate(both_probe).action is census.Action.PROBE
    assert census.direct_tau_gate(both_probe).action is census.Action.PROBE
    assert census.ec4g_gate(both_no_probe).action is census.Action.NO_PROBE
    assert census.direct_tau_gate(both_no_probe).action is census.Action.NO_PROBE
    assert census.ec4g_gate(both_abstain).action is census.Action.ABSTAIN
    assert census.direct_tau_gate(both_abstain).action is census.Action.ABSTAIN
    assert census.ec4g_gate(cell).action is census.Action.ABSTAIN
    assert census.direct_tau_gate(cell).action is census.Action.PROBE
    assert census.run_census(_domain(unsupported)).classification is (
        census.CensusClassification.INCOMPLETE_CONTRACT
    )


@pytest.mark.parametrize(
    ("supported", "measure"),
    ((False, 1.0), (True, 0.0), (True, -1.0), (True, float("inf")), (True, float("nan"))),
)
def test_every_expected_row_must_be_supported_with_positive_finite_mass(
    supported, measure,
):
    first = _cell()
    gates = tuple((name, supported) for name in census.GATES)
    second = replace(first, cell_id="x1", support_gates=gates, executor_measure=measure)
    result = census.run_census(census.FrozenCensus(("x0", "x1"), (first, second)))

    assert result.classification is census.CensusClassification.INCOMPLETE_CONTRACT
    assert result.comparisons == ()
    expected = "fully supported" if not supported else "finite and strictly positive"
    assert any(expected in issue for issue in result.issues)


def test_whole_positive_domain_classifies_all_rows_without_filtering():
    first = _cell()
    second = replace(
        first, cell_id="x1", executor_measure=0.5,
        measured_means=(0.0, 0.30, 0.10, 0.15, 0.0, 0.0, 0.0),
    )
    result = census.run_census(census.FrozenCensus(("x0", "x1"), (first, second)))

    assert result.classification is census.CensusClassification.BEHAVIORAL_DISCORDANCE
    assert tuple(item.cell_id for item in result.comparisons) == ("x0", "x1")


def test_same_cell_object_reaches_both_maps_and_output_is_byte_stable(monkeypatch):
    frozen = census.build_synthetic_witness()
    seen: list[tuple[str, int]] = []
    real_ec4g = census.ec4g_gate
    real_direct = census.direct_tau_gate

    def ec4g_spy(cell):
        seen.append(("EC4G", id(cell)))
        return real_ec4g(cell)

    def direct_spy(cell):
        seen.append(("Direct-tau", id(cell)))
        return real_direct(cell)

    monkeypatch.setattr(census, "ec4g_gate", ec4g_spy)
    monkeypatch.setattr(census, "direct_tau_gate", direct_spy)

    first = census.run_census(frozen)
    second = census.run_census(frozen)

    expected_id = id(frozen.cells[0])
    assert seen == [
        ("EC4G", expected_id),
        ("Direct-tau", expected_id),
        ("EC4G", expected_id),
        ("Direct-tau", expected_id),
    ]
    assert first.to_bytes() == second.to_bytes()


def test_cost_is_subtracted_once_and_pseudo_arms_are_report_only():
    cell = _cell()
    cost_adjusted = replace(
        cell,
        measured_means=(0.0, 0.15, 0.12, 0.14, 9.0, -9.0, 4.0),
        external_costs=(0.0, 0.05, 0.0, 0.0, 8.0, 2.0, 1.0),
    )

    result = census.run_census(_domain(cost_adjusted))
    comparison = result.comparisons[0]

    assert comparison.nu == pytest.approx((0.0, 0.10, 0.12, 0.14, 1.0, -11.0, 3.0))
    assert comparison.ec4g.action is census.Action.ABSTAIN
    assert comparison.direct_tau.action is census.Action.PROBE
    assert result.classification is census.CensusClassification.BEHAVIORAL_DISCORDANCE


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (lambda c: replace(c, receipts=replace(c.receipts, schema_id="other")), "schema/executor/source/version"),
        (lambda c: replace(c, receipts=replace(c.receipts, executor_id="other")), "schema/executor/source/version"),
        (lambda c: replace(c, receipts=replace(c.receipts, source_id="other")), "schema/executor/source/version"),
        (lambda c: replace(c, receipts=replace(c.receipts, source_version="v2")), "schema/executor/source/version"),
        (lambda c: replace(c, receipts=replace(c.receipts, latency_class="slow")), "latency/timestamp/delivery channel"),
        (lambda c: replace(c, receipts=replace(c.receipts, timestamp_representation="float")), "latency/timestamp/delivery channel"),
        (lambda c: replace(c, receipts=replace(c.receipts, delivery_channel="other")), "latency/timestamp/delivery channel"),
        (lambda c: replace(c, receipts=replace(c.receipts, payload_support_id="other")), "payload support/byte-length/safe-action mask"),
        (lambda c: replace(c, receipts=replace(c.receipts, byte_length_class="bytes:5")), "payload support/byte-length/safe-action mask"),
        (lambda c: replace(c, receipts=replace(c.receipts, safe_action_mask_digest="0" * 64)), "payload support/byte-length/safe-action mask"),
        (lambda c: replace(c, receipts=replace(c.receipts, visible_payload=b"FAKE")), "exact RV/RB/RS payloads"),
        (lambda c: replace(c, receipts=replace(c.receipts, blinded_payload=b"FAIL")), "exact RV/RB/RS payloads"),
        (lambda c: replace(c, receipts=replace(c.receipts, shuffled_payload=b"FAKE")), "exact RV/RB/RS payloads"),
        (lambda c: replace(c, receipts=replace(c.receipts, blinded_payload=c.receipts.shuffled_payload)), "blinded and shuffled variants must differ"),
        (lambda c: replace(c, receipts=replace(c.receipts, assignment_visible=True)), "exact event/donor relation"),
        (lambda c: replace(c, receipts=replace(c.receipts, donor_event_id=c.receipts.event_id)), "exact event/donor relation"),
        (lambda c: replace(c, receipts=replace(c.receipts, donor_trajectory_id=c.receipts.trajectory_id)), "exact event/donor relation"),
        (lambda c: replace(c, receipts=replace(c.receipts, donor_source_id="other")), "exact event/donor relation"),
        (lambda c: replace(c, receipts=replace(c.receipts, registered_donors=())), "exact event/donor relation"),
        (lambda c: replace(c, receipts=replace(c.receipts, donor_time=float("nan"))), "donor time must be finite"),
    ),
)
def test_exact_receipt_registry_rejects_each_mismatch(mutate, message):
    result = census.run_census(_domain(mutate(_cell())))

    assert result.classification is census.CensusClassification.INCOMPLETE_CONTRACT
    assert any(message in issue for issue in result.issues)
    assert result.comparisons == ()


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (lambda c: replace(c, covariance=((-1.0, *c.covariance[0][1:]), *c.covariance[1:])), "positive semidefinite"),
        (lambda c: replace(c, continuations=(replace(c.continuations[0], digest="0" * 64), *c.continuations[1:])), "digest mismatch"),
    ),
)
def test_other_contract_failures_return_incomplete_contract(mutate, message):
    result = census.run_census(_domain(mutate(_cell())))

    assert result.classification is census.CensusClassification.INCOMPLETE_CONTRACT
    assert any(message in issue for issue in result.issues)
    assert result.comparisons == ()


def test_continuation_digest_binds_cost_and_bytes_and_fallback_binding():
    cell = _cell()
    item = cell.continuations[0]
    values = [
        item.execution_path, item.receipt_variant, item.delivery_channel,
        item.envelope_id, item.envelope_bytes, item.body, item.external_cost,
    ]
    digest = census.continuation_digest(*values)
    alternatives = [
        "fallback", "RB", "other-channel", "other-envelope", b"FAKE", b"other", 1.0,
    ]
    assert digest == item.digest
    for index, replacement in enumerate(alternatives):
        changed = values.copy()
        changed[index] = replacement
        assert census.continuation_digest(*changed) != digest

    malformed = replace(cell, fallback_digest="f" * 64)
    result = census.run_census(_domain(malformed))

    assert result.classification is census.CensusClassification.INCOMPLETE_CONTRACT
    assert any("does not bind fallback" in issue for issue in result.issues)
