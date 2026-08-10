from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import io
import json
from pathlib import Path

import pytest

from experiments.candidates.ec4g_r1 import execution_digest_census as census
from scripts import run_ec4g_a1_execution_digest_census as project_runner


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


def _project_program(
    command: str, *, supplied_digest: str | None = None
) -> census.CanonicalExecutionProgram:
    branch = census.ExecutionBranch(
        branch_id="no-receipt/donor-none",
        receipt_id="NO_RECEIPT",
        donor_id="NO_DONOR",
        command=command,
        command_parameters=(("parameter", "fixed"),),
        timing="event-conditioned",
        receipt_access="none",
        donor_operation="identity",
        donor_arguments=(("payload", "preserved"),),
        downstream_payload_rule="preserve",
        fallback="fixed-fallback",
        resources=(("cpu", "0"),),
        charged_cost=Decimal("0"),
        randomization_kernel="deterministic-delta",
    )
    return census.CanonicalExecutionProgram((branch,), supplied_digest)


def _complete_project_binding(
    rows: tuple[census.ProjectCensusRow, ...],
) -> census.ProjectCensusBinding:
    bindings = tuple(
        census.FrozenObjectBinding(
            object_id=object_id,
            identity=f"sha256:{index:064x}",
            source_locator=f"project://{object_id}",
            frozen=True,
            total=True,
            coherent=True,
            detail="focused complete object",
        )
        for index, object_id in enumerate(census.REQUIRED_PROJECT_OBJECTS, start=1)
    )
    return census.ProjectCensusBinding(
        source_revision="a" * 40,
        run_id="focused-project-census",
        object_order=census.REQUIRED_PROJECT_OBJECTS,
        object_bindings=bindings,
        row_order=tuple(row.row_key for row in rows),
        rows=rows,
    )


def _project_row(
    *,
    ec4g_program: census.CanonicalExecutionProgram,
    direct_program: census.CanonicalExecutionProgram,
    ec4g_label: str = "EC4G-LABEL",
    direct_label: str = "DIRECT-LABEL",
    supported: bool = True,
    mass: str = "1",
) -> census.ProjectCensusRow:
    return census.ProjectCensusRow(
        row_key="k0",
        ec4g_label=ec4g_label,
        direct_tau_label=direct_label,
        ec4g_program=ec4g_program,
        direct_tau_program=direct_program,
        supported=supported,
        deployed_mass=Decimal(mass),
    )


def test_registered_project_binding_fails_closed_with_exact_missing_objects():
    binding = census.build_registered_project_binding(
        source_revision="b" * 40,
        run_id="ec4g-a1-registered",
    )

    result = census.run_project_census(binding)
    payload = json.loads(result.to_bytes())

    assert result.terminal_branch is census.ProjectCensusBranch.INCOMPLETE_CONTRACT
    assert result.contract_complete is False
    assert result.rows == ()
    assert result.summary["D_A"] is None
    assert result.vacuous_active_domain is None
    assert tuple(
        witness.object_id for witness in result.missing_object_witnesses[:14]
    ) == census.REQUIRED_PROJECT_OBJECTS
    assert all(
        witness.failure == "INVALID_OR_INCOMPLETE_OBJECT"
        for witness in result.missing_object_witnesses[:14]
    )
    assert tuple(
        witness.failure for witness in result.missing_object_witnesses[14:]
    ) == ("EMPTY_DECISION_CELL_REGISTRY", "MASS_NOT_NORMALIZED")
    assert payload["schema_version"] == census.PROJECT_RESULT_SCHEMA_VERSION
    assert payload["document_kind"] == "ec4g_a1_execution_digest_census_result"
    assert payload["terminal_branch"] == "INCOMPLETE_CONTRACT"
    assert payload["freeze_manifest"]["object_order"] == list(
        census.REQUIRED_PROJECT_OBJECTS
    )
    assert tuple(item["object_id"] for item in payload["object_bindings"]) == (
        census.REQUIRED_PROJECT_OBJECTS
    )
    assert payload["activity_counts"] == {
        "environment_transitions": 0,
        "learner_calls": 0,
        "model_fits": 0,
        "optimizer_updates": 0,
        "policy_calls": 0,
        "registered_census_runs": 1,
        "return_evaluations": 0,
        "trainer_calls": 0,
    }


def test_project_terminal_precedence_and_exact_discordance_mass():
    left = _project_program("EC4G-COMMAND")
    right = _project_program("DIRECT-COMMAND")
    row = _project_row(ec4g_program=left, direct_program=right)
    complete = _complete_project_binding((row,))

    positive = census.run_project_census(complete)
    incomplete = census.run_project_census(replace(complete, object_bindings=()))

    assert positive.terminal_branch is (
        census.ProjectCensusBranch.SUPPORTED_POSITIVE_MASS_BEHAVIORAL_DISCORDANCE
    )
    assert positive.summary["D_A"] == "1"
    assert positive.summary["active_behavioral_discordance_count"] == 1
    assert len(positive.summary["domain_checksum"]) == 64
    assert len(positive.summary["mass_checksum"]) == 64
    assert all(item["coherent"] for item in positive.object_bindings)
    assert positive.rows[0]["ec4g_program"]["branches"]
    assert positive.rows[0]["direct_tau_program"]["branches"]
    assert incomplete.terminal_branch is census.ProjectCensusBranch.INCOMPLETE_CONTRACT
    assert incomplete.summary["D_A"] is None


def test_empty_declared_registry_is_incomplete_not_vacuously_equivalent():
    result = census.run_project_census(_complete_project_binding(()))

    assert result.terminal_branch is census.ProjectCensusBranch.INCOMPLETE_CONTRACT
    assert result.contract_complete is False
    assert result.summary["D_A"] is None
    assert result.vacuous_active_domain is None
    witnesses = {
        (witness.object_id, witness.failure, witness.detail)
        for witness in result.missing_object_witnesses
    }
    assert (
        "decision_cell_registry",
        "EMPTY_DECISION_CELL_REGISTRY",
        "a complete project census requires at least one frozen decision row",
    ) in witnesses
    assert (
        "prospective_deployed_mass_registry",
        "MASS_NOT_NORMALIZED",
        "exact total deployed mass is 0, expected 1",
    ) in witnesses


def test_label_only_execution_equivalent_and_vacuous_branches():
    program = _project_program("SAME-COMMAND")
    label_only = census.run_project_census(
        _complete_project_binding(
            (_project_row(ec4g_program=program, direct_program=program),)
        )
    )
    equivalent = census.run_project_census(
        _complete_project_binding(
            (
                _project_row(
                    ec4g_program=program,
                    direct_program=program,
                    ec4g_label="SAME",
                    direct_label="SAME",
                ),
            )
        )
    )
    vacuous = census.run_project_census(
        _complete_project_binding(
            (
                _project_row(
                    ec4g_program=_project_program("UNSUPPORTED-LEFT"),
                    direct_program=_project_program("UNSUPPORTED-RIGHT"),
                    supported=False,
                ),
            )
        )
    )

    assert label_only.terminal_branch is census.ProjectCensusBranch.LABEL_ONLY_DIFFERENCE
    assert label_only.summary["D_A"] == "0"
    assert equivalent.terminal_branch is census.ProjectCensusBranch.EXECUTION_EQUIVALENT
    assert equivalent.vacuous_active_domain is False
    assert vacuous.terminal_branch is census.ProjectCensusBranch.EXECUTION_EQUIVALENT
    assert vacuous.vacuous_active_domain is True
    assert vacuous.summary["unsupported_or_zero_mass_difference_count"] == 1
    assert vacuous.rows[0]["row_class"] == "AUDIT_ONLY_OUTSIDE_ACTIVE_DOMAIN"


def test_complete_program_equality_overrides_a_supplied_digest_collision():
    collision = "c" * 64
    left = _project_program("LEFT-COMMAND", supplied_digest=collision)
    right = _project_program("RIGHT-COMMAND", supplied_digest=collision)

    result = census.run_project_census(
        _complete_project_binding(
            (
                _project_row(
                    ec4g_program=left,
                    direct_program=right,
                    ec4g_label="SAME-LABEL",
                    direct_label="SAME-LABEL",
                ),
            )
        )
    )

    assert result.terminal_branch is (
        census.ProjectCensusBranch.SUPPORTED_POSITIVE_MASS_BEHAVIORAL_DISCORDANCE
    )
    assert result.rows[0]["supplied_digest_collision"] is True
    assert result.rows[0]["execution_difference"] is True


def test_runner_source_freeze_and_one_shot_output_are_fail_closed():
    project_runner._require_source_revision("a" * 40, "a" * 40)
    with pytest.raises(ValueError, match="source revision mismatch"):
        project_runner._require_source_revision("a" * 40, "b" * 40)

    class RetainedBytesIO(io.BytesIO):
        def close(self):
            pass

    class FakeOneShotPath:
        def __init__(self):
            self.handle = RetainedBytesIO()
            self.open_count = 0

        def open(self, mode):
            assert mode == "xb"
            self.open_count += 1
            if self.open_count > 1:
                raise FileExistsError("already exists")
            return self.handle

        def __str__(self):
            return "fake-one-shot.json"

    output = FakeOneShotPath()
    project_runner._write_new(output, b"{}\n")
    assert output.handle.getvalue() == b"{}\n"
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        project_runner._write_new(output, b"second\n")


def test_runner_existing_output_preflight_never_constructs_or_analyzes(monkeypatch):
    calls = {"binding": 0, "analyzer": 0}

    def binding_spy(**kwargs):
        calls["binding"] += 1
        raise AssertionError("binding construction must not run")

    def analyzer_spy(binding):
        calls["analyzer"] += 1
        raise AssertionError("analyzer must not run")

    monkeypatch.setattr(project_runner, "_source_revision", lambda: "a" * 40)
    monkeypatch.setattr(project_runner, "build_registered_project_binding", binding_spy)
    monkeypatch.setattr(project_runner, "run_project_census", analyzer_spy)
    existing_output = Path(__file__).resolve()

    with pytest.raises(SystemExit, match="refusing to overwrite one-shot result"):
        project_runner.main(
            [
                "--source-revision",
                "a" * 40,
                "--run-id",
                "preflight-existing-output",
                "--output",
                str(existing_output),
            ]
        )

    assert calls == {"binding": 0, "analyzer": 0}
