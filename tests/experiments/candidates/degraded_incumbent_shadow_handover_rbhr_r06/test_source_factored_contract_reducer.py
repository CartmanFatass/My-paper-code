from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_contract import (
    CLAIM_ROWS, OBJECT_ID, PREVALENCE_REJECTION_THRESHOLD, ROOT_BYTES, ROOT_COUNT,
    RUNNER_MASTER_POLICY, TRANSACTION_SUBSTRATE_ID, ResourceCeilings,
    complete_claim_inventory, complete_contract, prevalence_inference_contract,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_reducer import (
    MATERIAL_MARGINS, NONINFERIORITY_MARGINS, SIGNS, CompleteClaimAccounting,
    EndpointRows, NonharmObservation, ReplayContainmentEvidence, RootAxisIndicators,
    SourceFactoredReducerError, TypedTerminalRecord, WeightingSensitivity,
    exact_prevalence_preview, reduce_root_axis, signed_benefit,
    terminal_indicator_dependencies,
)


CELL_SHAPE = (2, 3, 3)
BENEFIT_SHAPE = (*CELL_SHAPE, 4)


def _competence() -> np.ndarray:
    return np.full(CELL_SHAPE, 0.9, dtype=np.float64)


def _triggers() -> np.ndarray:
    return np.full(CELL_SHAPE, 8, dtype=np.int64)


def _value_benefits() -> np.ndarray:
    values = np.zeros(BENEFIT_SHAPE, dtype=np.float64)
    values[:, :, 1, 0] = MATERIAL_MARGINS["MEAN"]
    return values


def _no_material_benefits() -> np.ndarray:
    values = np.zeros(BENEFIT_SHAPE, dtype=np.float64)
    values[:, :, :, 0] = np.nextafter(MATERIAL_MARGINS["MEAN"], 0.0)
    return values


def _reduce_axis(
    *, axis: str, benefits: np.ndarray, root_index: int = 0,
    assignment_complete: bool = True, protocol_complete: bool = True,
    transaction_complete: bool = True, competence: np.ndarray | None = None,
    trigger_counts: np.ndarray | None = None, nonharm_pass: bool = True,
    separation_diagnostic_pass: bool | None = True,
    shadow_retain_benefits: np.ndarray | None = None,
    shadow_retain_nonharm_pass: bool | None = None,
    terminal_records: tuple[TypedTerminalRecord, ...] = (),
) -> RootAxisIndicators:
    return reduce_root_axis(
        root_index=root_index, root=bytes([root_index]) * ROOT_BYTES, axis=axis,
        assignment_complete=assignment_complete, protocol_complete=protocol_complete,
        transaction_complete=transaction_complete,
        competence=_competence() if competence is None else competence,
        trigger_counts=_triggers() if trigger_counts is None else trigger_counts,
        signed_benefits=benefits, nonharm_pass=nonharm_pass,
        separation_diagnostic_pass=separation_diagnostic_pass,
        shadow_retain_signed_benefits=shadow_retain_benefits,
        shadow_retain_nonharm_pass=shadow_retain_nonharm_pass,
        terminal_records=terminal_records,
    )


def _root_indicator(
    *, root_index: int, axis: str, value: int = 0, no_material: int = 0,
    assignment_complete: bool = True,
) -> RootAxisIndicators:
    root = bytes(32) if root_index in (0, 1) else bytes([root_index]) * ROOT_BYTES
    return RootAxisIndicators(
        root_index=root_index, root=root, axis=axis,
        assignment_complete=assignment_complete,
        value_indicator=value if assignment_complete else None,
        no_material_indicator=no_material if assignment_complete else None,
        diagnostics=() if value or no_material else ("MIXED",),
        qualifying_witnesses=((
            "MEAN" if root_index % 2 == 0 else "TAIL",
            (4, 6, 8)[root_index % 3],
        ),) if value else (),
    )


def _panel_rows(
    *, copy_value: int = 18, copy_no_material: int = 0,
    shadow_value: int = 0, shadow_no_material: int = 18,
    incomplete: tuple[int, str] | None = None,
) -> list[RootAxisIndicators]:
    rows: list[RootAxisIndicators] = []
    for root_index in range(ROOT_COUNT):
        for axis, value_count, no_material_count in (
            ("COPY-RETAIN", copy_value, copy_no_material),
            ("SHADOW-COPY", shadow_value, shadow_no_material),
        ):
            rows.append(_root_indicator(
                root_index=root_index, axis=axis,
                value=int(root_index < value_count),
                no_material=int(value_count <= root_index < value_count + no_material_count),
                assignment_complete=incomplete != (root_index, axis),
            ))
    return rows


def _weighting(*, copy_flip: bool = False, shadow_flip: bool = False) -> WeightingSensitivity:
    return WeightingSensitivity(
        block_first_complete=True, event_first_complete=True,
        copy_retain_sign_or_materiality_flip=copy_flip,
        shadow_copy_sign_or_materiality_flip=shadow_flip,
    )


def _complete_replay() -> ReplayContainmentEvidence:
    return ReplayContainmentEvidence(
        all_endpoint_rows_covered=True, post_cas_native_state_equal=True,
        policy_state_equal=True, welford_state_equal=True, rng_state_equal=True,
        hundred_tick_twin_equal=True, deadline_met=True,
    )


def _assert_preview_has_no_true_authority(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if "authority" in str(key).lower():
                assert child is not True
            _assert_preview_has_no_true_authority(child)
    elif isinstance(value, list):
        for child in value:
            _assert_preview_has_no_true_authority(child)


def _resource_limited_replay() -> ReplayContainmentEvidence:
    return ReplayContainmentEvidence(
        all_endpoint_rows_covered=True, post_cas_native_state_equal=True,
        policy_state_equal=True, welford_state_equal=True, rng_state_equal=True,
        hundred_tick_twin_equal=True, deadline_met=False,
    )


def test_r02_contract_freezes_root_law_four_tests_and_no_mean_authority() -> None:
    rows = complete_claim_inventory()
    assert len(rows) == CLAIM_ROWS == 6_912
    assert len({row.key() for row in rows}) == 6_912
    assert OBJECT_ID == "DISH-BLOCK-CERTIFICATE-PREVALENCE-R02"
    assert TRANSACTION_SUBSTRATE_ID == "DISH-PROMOTION-SOURCE-FORK-R01"

    inference = prevalence_inference_contract()
    assert inference["root_law"] == {
        "count": 24, "root_bytes": 32, "distribution": "IID_UNIFORM_256_BIT",
        "duplicates_retained": True, "canonical_local_address_map": "F(U_b)",
        "global_block_index_role": "STORAGE_AND_ORDER_ONLY",
        "global_block_index_in_rng_address": False,
    }
    assert inference["within_root_census"] == {
        "packages": 2, "schedules": 3, "speeds": 3, "slots": 16, "rows": 288,
        "rows_are_independent_samples": False,
    }
    assert [row["id"] for row in inference["tests"]] == [
        "COPY-RETAIN/VALUE", "COPY-RETAIN/NO_MATERIAL",
        "SHADOW-COPY/VALUE", "SHADOW-COPY/NO_MATERIAL",
    ]
    assert all(row["alpha"] == {"numerator": 1, "denominator": 80} for row in inference["tests"])
    assert all(row["reject_when_count_at_least"] == 18 for row in inference["tests"])
    assert inference["legacy_24_block_bootstrap_allowed"] is False
    assert inference["no_alpha_recycling"] is True
    assert inference["endpoint_anchor_scope"] == "ROOT_LOCAL_EXISTENTIAL_MAY_VARY"
    assert inference["fixed_endpoint_anchor_prevalence_authority"] is False
    assert inference["indicator_rule_precommitted"] is True
    assert inference["classification_selection_after_counts_allowed"] is False
    assert inference["future_stochastic_address_law"] == {
        "physical_exogenous_evaluation_tape_shared_across_branches": True,
        "counter_frontier_shared_across_branches": True,
        "branch_id_in_scientific_rng_address": False,
        "branch_label_non_rng_roles": [
            "TRANSACTION", "OUTPUT_METADATA", "DETERMINISTIC_INTERVENTION_STATE",
        ],
    }
    assert inference["panel_retry_law"] == {
        "create_only_root_panel": True,
        "failure_before_panel_creation": "FRESH_PANEL_ALLOWED",
        "technical_failure_after_panel_creation": "REUSE_SAME_24_ROOTS_OUTCOME_BLIND_FROM_START",
        "redraw_after_panel_creation": False,
        "predefined_runtime_or_hard_event": "SCIENTIFIC_ZERO_OR_HARM_NOT_TECHNICAL_INCOMPLETE",
    }
    assert inference["claim_authority"] == {
        "algorithmic_root_certificate_prevalence": True,
        "expected_or_mean_return": False, "natural_prevalence": False,
        "generic_transfer": False, "unique_information_or_necessity": False,
        "safety_deployment_or_flight": False,
    }

    contract = complete_contract()
    assert contract["schema"] == "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_CONTRACT_V2"
    assert contract["scientific_object_id"] == OBJECT_ID
    assert contract["transaction_substrate_id"] == TRANSACTION_SUBSTRATE_ID
    assert RUNNER_MASTER_POLICY == "RUNNER_GENERATE_ONCE_IID_UNIFORM_256_BIT_ROOT_PANEL_24"
    assert contract["legacy_24_block_bootstrap_allowed"] is False
    assert "inference_resamples" not in contract
    assert ResourceCeilings().io_gib == 68.14
    contract["estimands"]["COPY-RETAIN"]["treatment"] = "CALLER_MUTATION"
    assert complete_contract()["estimands"]["COPY-RETAIN"]["treatment"] == "TRANSFER_COPY"


def test_source_factored_complete_inventory_preserves_no_trigger_rows() -> None:
    accounting = CompleteClaimAccounting()
    for index, row in enumerate(complete_claim_inventory()):
        accounting.put(row, trigger_present=index % 17 == 0)
    sealed = accounting.seal_scaffold()
    assert sealed["row_count"] == 6_912
    assert sealed["no_trigger_rows"] > 0
    assert sealed["question_relevant_output"] is False


def test_source_factored_endpoint_signs_margins_and_nonharm() -> None:
    service = np.ones((10, 100), dtype=np.int8); service[0, :20] = 0
    endpoint = EndpointRows(service).reduce()
    assert tuple(endpoint) == ("MEAN", "TAIL", "DEFICIT", "DELAY")
    assert SIGNS == {"MEAN": 1, "TAIL": 1, "DEFICIT": -1, "DELAY": -1}
    assert MATERIAL_MARGINS == {"MEAN": .03, "TAIL": .05, "DEFICIT": .25, "DELAY": .5}
    assert NONINFERIORITY_MARGINS == {"MEAN": .01, "TAIL": .02, "DEFICIT": .25, "DELAY": .5}
    assert signed_benefit({"MEAN": 1, "TAIL": 1, "DEFICIT": 0, "DELAY": 0},
                          {"MEAN": 0, "TAIL": 0, "DEFICIT": 1, "DELAY": 1}) == {
                              "MEAN": 1.0, "TAIL": 1.0, "DEFICIT": 1.0, "DELAY": 1.0}
    assert NonharmObservation(0, 0, 0, 0, 0, 0, 0, 15.0, -.01, True).passes()


def test_root_indicator_value_and_strict_no_material_are_disjoint() -> None:
    value = _reduce_axis(axis="COPY-RETAIN", benefits=_value_benefits())
    assert (value.value_indicator, value.no_material_indicator) == (1, 0)
    assert value.qualifying_witnesses == (("MEAN", 6),)
    assert value.diagnostics == ()
    no_material = _reduce_axis(axis="COPY-RETAIN", benefits=_no_material_benefits())
    assert (no_material.value_indicator, no_material.no_material_indicator) == (0, 1)

    multiple = np.zeros(BENEFIT_SHAPE, dtype=np.float64)
    multiple[:, :, 0, 0] = MATERIAL_MARGINS["MEAN"]
    multiple[:, :, 1, 0] = MATERIAL_MARGINS["MEAN"]
    multiple[:, :, 2, 1] = MATERIAL_MARGINS["TAIL"]
    multi_row = _reduce_axis(axis="COPY-RETAIN", benefits=multiple)
    assert multi_row.qualifying_witnesses == (
        ("MEAN", 4), ("MEAN", 6), ("TAIL", 8),
    )


def test_shadow_value_requires_total_safeguard_but_epsilon_separation_is_diagnostic_only() -> None:
    safe_total = np.zeros(BENEFIT_SHAPE, dtype=np.float64)
    value = _reduce_axis(
        axis="SHADOW-COPY", benefits=_value_benefits(),
        shadow_retain_benefits=safe_total, shadow_retain_nonharm_pass=True,
        separation_diagnostic_pass=False,
    )
    assert (value.value_indicator, value.no_material_indicator) == (1, 0)
    assert value.diagnostics == ("EPSILON_SEPARATION_DIAGNOSTIC_FAILED",)
    unsafe_total = safe_total.copy(); unsafe_total[0, 0, 0, 0] = -0.011
    unsafe = _reduce_axis(
        axis="SHADOW-COPY", benefits=_value_benefits(),
        shadow_retain_benefits=unsafe_total, shadow_retain_nonharm_pass=True,
    )
    assert (unsafe.value_indicator, unsafe.no_material_indicator) == (0, 0)
    assert "SHADOW_RETAIN_TOTAL_SAFEGUARD_FAILED" in unsafe.diagnostics


@pytest.mark.parametrize("gate", ["competence", "trigger"])
def test_scientifically_valid_common_gate_failure_is_retained_as_zero_not_incomplete(gate: str) -> None:
    competence = _competence(); triggers = _triggers()
    if gate == "competence":
        competence[0, 0, 0] = np.nextafter(0.85, 0.0)
    else:
        triggers[0, 0, 0] = 1
    row = _reduce_axis(
        axis="COPY-RETAIN", benefits=_value_benefits(),
        competence=competence, trigger_counts=triggers,
    )
    assert row.assignment_complete is True
    assert (row.value_indicator, row.no_material_indicator) == (0, 0)
    assert "COMMON_GATE_FAILED" in row.diagnostics


def test_missing_protocol_or_shadow_safeguard_is_incomplete_not_a_bernoulli_zero() -> None:
    protocol = _reduce_axis(
        axis="COPY-RETAIN", benefits=_value_benefits(), protocol_complete=False,
    )
    assert protocol.assignment_complete is False
    assert protocol.value_indicator is None and protocol.no_material_indicator is None
    assert protocol.diagnostics == ("INCOMPLETE_ASSIGNMENT",)
    shadow = _reduce_axis(axis="SHADOW-COPY", benefits=_value_benefits())
    assert shadow.assignment_complete is False
    assert shadow.diagnostics == ("INCOMPLETE_ASSIGNMENT",)

    impossible_competence = _competence(); impossible_competence[0, 0, 0] = 1.01
    impossible_trigger = _triggers(); impossible_trigger[0, 0, 0] = 17
    for row in (
        _reduce_axis(
            axis="COPY-RETAIN", benefits=_value_benefits(),
            competence=impossible_competence,
        ),
        _reduce_axis(
            axis="COPY-RETAIN", benefits=_value_benefits(),
            trigger_counts=impossible_trigger,
        ),
    ):
        assert row.assignment_complete is False
        assert row.diagnostics == ("INCOMPLETE_ASSIGNMENT",)


def test_typed_runtime_harm_is_scientific_zero_but_nonfinite_endpoint_invalidates_panel() -> None:
    worst_case = np.full(BENEFIT_SHAPE, -1.0, dtype=np.float64)
    hard_event = _reduce_axis(
        axis="COPY-RETAIN", benefits=worst_case, nonharm_pass=False,
    )
    assert hard_event.assignment_complete is True
    assert (hard_event.value_indicator, hard_event.no_material_indicator) == (0, 0)
    assert "NONHARM_FAILURE" in hard_event.diagnostics

    nonfinite = _value_benefits(); nonfinite[0, 0, 0, 0] = np.nan
    invalid = _reduce_axis(axis="COPY-RETAIN", benefits=nonfinite, root_index=17)
    assert invalid.assignment_complete is False
    assert invalid.value_indicator is None and invalid.no_material_indicator is None
    assert invalid.diagnostics == ("INCOMPLETE_ASSIGNMENT",)

    rows = _panel_rows(copy_value=18)
    rows[next(index for index, row in enumerate(rows)
              if row.root_index == 17 and row.axis == "COPY-RETAIN")] = invalid
    report = exact_prevalence_preview(rows, weighting=_weighting())
    assert report["status"] == "TEST_ONLY_NOT_READY"
    assert report["preview_input_status"] == "INCOMPLETE_ASSIGNMENT"
    assert report["prevalence_tests_executed"] is False
    assert report["scientific_tests_executed"] is False
    assert report["production_result_authority"] is False
    assert report["question_relevant_output"] is False
    assert "tests" not in report


def test_typed_terminal_records_have_frozen_branch_dependency_and_untyped_conversion_is_forbidden() -> None:
    def record(branch: str, *, stage: str = "FUTURE_TICKS") -> TypedTerminalRecord:
        return TypedTerminalRecord(
            root_index=0, package="TARGET_VISUAL_MASK", schedule="K8", speed=4, slot=0,
            branch=branch, stage=stage, kind="ALGORITHM_RUNTIME_OR_NONFINITE",
            producer_schema="DISH_R02_BRANCH_PRODUCER_TERMINAL_V1",
            phase="BEFORE_MEASUREMENT_AND_REDUCTION",
            finite_worst_case_materialized=True, hard_event_flag=True,
        )

    assert terminal_indicator_dependencies((record("RETAIN"),)) == {
        "COPY-RETAIN": True, "SHADOW-COPY": False, "SHADOW-RETAIN-TOTAL": True,
    }
    assert terminal_indicator_dependencies((record("TRANSFER_COPY"),)) == {
        "COPY-RETAIN": True, "SHADOW-COPY": True, "SHADOW-RETAIN-TOTAL": True,
    }
    assert terminal_indicator_dependencies((record("TRANSFER_SHADOW"),)) == {
        "COPY-RETAIN": False, "SHADOW-COPY": True, "SHADOW-RETAIN-TOTAL": True,
    }
    with pytest.raises(ValueError, match="typed terminal kind differs"):
        TypedTerminalRecord(
            root_index=0, package="TARGET_VISUAL_MASK", schedule="K8", speed=4, slot=0,
            branch="RETAIN", stage="FUTURE_TICKS", kind="UNKNOWN_NONFINITE",
            producer_schema="DISH_R02_BRANCH_PRODUCER_TERMINAL_V1",
            phase="BEFORE_MEASUREMENT_AND_REDUCTION",
            finite_worst_case_materialized=True, hard_event_flag=True,
        )
    with pytest.raises(ValueError, match="typed terminal materialization differs"):
        TypedTerminalRecord(
            root_index=0, package="TARGET_VISUAL_MASK", schedule="K8", speed=4, slot=0,
            branch="RETAIN", stage="FUTURE_TICKS", kind="ALGORITHM_RUNTIME_OR_NONFINITE",
            producer_schema="DISH_R02_BRANCH_PRODUCER_TERMINAL_V1",
            phase="BEFORE_MEASUREMENT_AND_REDUCTION",
            finite_worst_case_materialized=False, hard_event_flag=True,
        )
    for forbidden_stage in ("AFTER_OUTCOME", "REDUCER"):
        with pytest.raises(ValueError, match="typed terminal stage differs"):
            record("RETAIN", stage=forbidden_stage)
    with pytest.raises(ValueError, match="typed terminal producer provenance differs"):
        TypedTerminalRecord(
            root_index=0, package="TARGET_VISUAL_MASK", schedule="K8", speed=4, slot=0,
            branch="RETAIN", stage="APPLICATION_POLICY_FORWARD",
            kind="ALGORITHM_RUNTIME_OR_NONFINITE", producer_schema="CALLER_ASSERTION",
            phase="BEFORE_MEASUREMENT_AND_REDUCTION",
            finite_worst_case_materialized=True, hard_event_flag=True,
        )

    retain = record("RETAIN")
    copy = record("TRANSFER_COPY")
    shadow = record("TRANSFER_SHADOW")
    assert _reduce_axis(
        axis="COPY-RETAIN", benefits=_value_benefits(), terminal_records=(retain,),
    ).value_indicator == 0
    assert _reduce_axis(
        axis="COPY-RETAIN", benefits=_value_benefits(), terminal_records=(shadow,),
    ).value_indicator == 1
    assert _reduce_axis(
        axis="SHADOW-COPY", benefits=_value_benefits(), terminal_records=(copy,),
        shadow_retain_benefits=np.zeros(BENEFIT_SHAPE), shadow_retain_nonharm_pass=True,
    ).value_indicator == 0


def test_exact_prevalence_preview_computes_frozen_rationals_without_result_authority() -> None:
    report = exact_prevalence_preview(
        _panel_rows(), weighting=_weighting(shadow_flip=True), replay=_complete_replay(),
    )
    assert report["schema"] == "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_REDUCER_PREVIEW_V2"
    assert report["status"] == "TEST_ONLY_NOT_READY"
    assert report["preview_input_status"] == "COMPLETE_SYNTHETIC_INPUT"
    assert report["scientific_object_consumed"] is False
    assert report["question_relevant_output"] is False
    assert report["production_result_authority"] is False
    assert report["scientific_tests_executed"] is False
    assert report["preview_tests_computed"] is True
    assert "claim_authority" not in report
    _assert_preview_has_no_true_authority(report)
    assert report["axes"]["COPY-RETAIN"]["disposition"] == "ROOT_PREVALENCE_VALUE"
    assert report["axes"]["SHADOW-COPY"]["disposition"] == "ROOT_PREVALENCE_NO_MATERIAL"
    assert report["combined"] == "SHADOW_COPY_ROOT_PREVALENCE_NO_MATERIAL + COPY_RETAIN_ROOT_PREVALENCE_VALUE"
    assert report["tests"]["COPY-RETAIN/VALUE"] == {
        "count": 18, "root_count": 24, "null": "p<=1/2",
        "alpha": {"numerator": 1, "denominator": 80},
        "reject_when_count_at_least": PREVALENCE_REJECTION_THRESHOLD, "rejected": True,
        "exact_null_tail": {"numerator": 190051, "denominator": 16777216},
    }
    assert report["familywise_error_bound"] == {"numerator": 190051, "denominator": 4194304}
    assert report["planning_power_at_p_0_8"] == {
        "numerator": 48343602127962112, "denominator": 59604644775390625,
    }
    assert report["threshold_cp_lower_98_75_percent"] == pytest.approx(0.503888100451766)
    assert len(report["fixed_panel"]["roots"]) == 24
    assert report["fixed_panel"]["descriptive_only"] is True
    assert report["fixed_panel"]["superpopulation_mean_authority"] is False
    copy_witnesses = [row["axes"]["COPY-RETAIN"] for row in report["fixed_panel"]["roots"][:2]]
    assert copy_witnesses == [
        {"value": 1, "no_material": 0, "diagnostics": [],
         "qualifying_witnesses": [["MEAN", 4]]},
        {"value": 1, "no_material": 0, "diagnostics": [],
         "qualifying_witnesses": [["TAIL", 6]]},
    ]
    assert report["fixed_panel"]["weighting_sensitivity"] == {
        "block_first": {
            "complete": True, "prospective_weighting_rule": True,
            "scientific_evidence_authority": False,
        },
        "event_first": {
            "complete": True, "sensitivity_only": True,
            "scientific_evidence_authority": False,
        },
        "sign_or_materiality_flip": {"COPY-RETAIN": False, "SHADOW-COPY": True},
    }
    assert report["duplicate_roots_retained"] is True
    assert report["endpoint_anchor_scope"] == "ROOT_LOCAL_EXISTENTIAL_MAY_VARY"
    assert report["fixed_endpoint_anchor_prevalence_authority"] is False


def test_nonrejection_of_value_does_not_create_no_material_and_alpha_is_not_recycled() -> None:
    report = exact_prevalence_preview(
        _panel_rows(copy_value=17, shadow_no_material=0),
        weighting=_weighting(), replay=_resource_limited_replay(),
    )
    assert report["axes"]["COPY-RETAIN"]["disposition"] == "ROOT_PREVALENCE_UNRESOLVED"
    assert report["axes"]["SHADOW-COPY"]["disposition"] == "ROOT_PREVALENCE_UNRESOLVED"
    assert all(row["alpha"] == {"numerator": 1, "denominator": 80}
               for row in report["tests"].values())
    assert report["no_alpha_recycling"] is True


def test_replay_is_shadow_modifier_and_preserves_both_prevalence_dispositions() -> None:
    report = exact_prevalence_preview(_panel_rows(), weighting=_weighting(), replay=_complete_replay())
    assert report["axes"]["COPY-RETAIN"]["disposition"] == "ROOT_PREVALENCE_VALUE"
    assert report["axes"]["SHADOW-COPY"]["disposition"] == "ROOT_PREVALENCE_NO_MATERIAL"
    assert report["replay_scope"] == ["SHADOW-COPY"]
    assert report["replay_containment_complete"] is True
    assert report["modifiers"] == ["SHADOW_REPLAY_CONTAINED"]


def test_replay_resource_limited_is_distinct_from_invalid_or_absent_replay() -> None:
    limited = exact_prevalence_preview(
        _panel_rows(), weighting=_weighting(), replay=_resource_limited_replay(),
    )
    assert limited["status"] == "TEST_ONLY_NOT_READY"
    assert limited["replay_status"] == "RESOURCE_LIMITED"
    assert limited["replay_containment_complete"] is False
    assert limited["modifiers"] == ["SHADOW_REPLAY_RESOURCE_LIMITED"]

    structurally_invalid = ReplayContainmentEvidence(
        all_endpoint_rows_covered=True, post_cas_native_state_equal=True,
        policy_state_equal=False, welford_state_equal=True, rng_state_equal=True,
        hundred_tick_twin_equal=True, deadline_met=True,
    )
    for replay in (None, structurally_invalid):
        invalid = exact_prevalence_preview(
            _panel_rows(), weighting=_weighting(), replay=replay,
        )
        assert invalid["status"] == "TEST_ONLY_NOT_READY"
        assert invalid["preview_input_status"] == "INCOMPLETE_ASSIGNMENT"
        assert invalid["scientific_object_consumed"] is False
        assert invalid["prevalence_tests_executed"] is False
        assert invalid["replay_status"] == "INVALID_OR_INCOMPLETE"
        assert "tests" not in invalid


def test_incomplete_axis_or_missing_weighting_observation_does_not_consume_object() -> None:
    report = exact_prevalence_preview(
        _panel_rows(incomplete=(3, "SHADOW-COPY")),
        weighting=_weighting(), replay=_complete_replay(),
    )
    assert report["status"] == "TEST_ONLY_NOT_READY"
    assert report["preview_input_status"] == "INCOMPLETE_ASSIGNMENT"
    assert report["scientific_object_consumed"] is False
    assert report["prevalence_tests_executed"] is False
    assert "tests" not in report
    with pytest.raises(SourceFactoredReducerError, match="weighting sensitivity is incomplete"):
        exact_prevalence_preview(
            _panel_rows(),
            weighting=WeightingSensitivity(
                block_first_complete=True, event_first_complete=False,
                copy_retain_sign_or_materiality_flip=False,
                shadow_copy_sign_or_materiality_flip=False,
            ),
            replay=_complete_replay(),
        )
