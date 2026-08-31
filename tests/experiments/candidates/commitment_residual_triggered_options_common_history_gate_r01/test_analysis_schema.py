from pathlib import Path
from copy import deepcopy
from dataclasses import replace

import pytest

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.analysis import (
    AnalysisPolicy,
    EffectHull,
    _first_match,
    analyze,
    assess_raw_long_competence,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.config import (
    FIXED_CENSUS_METHOD,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    Budget,
    Representation,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.evaluation import (
    EvaluationSummary,
    classify_material_advantage,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.run import (
    _atomic_publish_with_executor,
    result_skeleton,
    validate_result,
)


def _effect(label: str, budget: Budget, lower: float, upper: float) -> EffectHull:
    values = (lower,) * 7 + (upper,)
    return EffectHull(
        contrast=label,
        budget=budget,
        slot_effects=values,
        descriptive_mean=sum(values) / 8,
        lower=lower,
        upper=upper,
        width=upper - lower,
        replicate_count=8,
    )


def _branch_inputs(
    *,
    rt_s: tuple[float, float],
    rt_l: tuple[float, float],
    dt_s: tuple[float, float],
    dt_l: tuple[float, float],
    rd_s: tuple[float, float] = (0.0, 0.0),
    rd_l: tuple[float, float] = (0.0, 0.0),
    raw_gain: tuple[float, float] = (0.0, 0.0),
    true_degrade: tuple[float, float] = (0.0, 0.0),
) -> tuple[tuple[EffectHull, ...], tuple[EffectHull, ...]]:
    hulls = (
        _effect("RAW_MINUS_TRUE", Budget.SHORT, *rt_s),
        _effect("RAW_MINUS_TRUE", Budget.LONG, *rt_l),
        _effect("DERANGED_MINUS_TRUE", Budget.SHORT, *dt_s),
        _effect("DERANGED_MINUS_TRUE", Budget.LONG, *dt_l),
        _effect("RAW_MINUS_DERANGED", Budget.SHORT, *rd_s),
        _effect("RAW_MINUS_DERANGED", Budget.LONG, *rd_l),
    )
    trajectories = (
        _effect("RAW_GAIN", Budget.LONG, *raw_gain),
        _effect("TRUE_DEGRADE", Budget.LONG, *true_degrade),
    )
    return hulls, trajectories


def test_exact_first_match_truth_table_and_delta_boundaries() -> None:
    assert _first_match(*_branch_inputs(
        rt_s=(.006, .007), rt_l=(.006, .007),
        dt_s=(.006, .007), dt_l=(.006, .007),
    )) == "PERSISTENT_ALIGNED_BIAS"
    assert _first_match(*_branch_inputs(
        rt_s=(.006, .007), rt_l=(.006, .007),
        dt_s=(0.0, 0.0), dt_l=(0.0, 0.0),
        rd_s=(.006, .007), rd_l=(.006, .007),
    )) == "GENERIC_PREPROCESSING"
    assert _first_match(*_branch_inputs(
        rt_s=(.006, .006), rt_l=(0.0, 0.0),
        dt_s=(.006, .006), dt_l=(0.0, 0.0), rd_l=(0.0, 0.0),
        raw_gain=(.006, .006), true_degrade=(0.0, 0.0),
    )) == "OPTIMIZATION_EXPOSURE_ONLY"
    # Gap closure caused by TRUE degradation has no optimization-only authority.
    assert _first_match(*_branch_inputs(
        rt_s=(.012, .012), rt_l=(0.0, 0.0),
        dt_s=(.012, .012), dt_l=(0.0, 0.0), rd_l=(0.0, 0.0),
        raw_gain=(.006, .006), true_degrade=(.006, .006),
    )) == "UNRESOLVED"
    # Equality at +delta is not superiority; CLOSE means no TRUE material benefit.
    assert _first_match(*_branch_inputs(
        rt_s=(.005, .005), rt_l=(.005, .005),
        dt_s=(0.0, 0.0), dt_l=(0.0, 0.0),
        rd_s=(.005, .005), rd_l=(.005, .005),
    )) == "CLOSE_TESTED_MECHANISM"


def test_branch_rejects_freely_inconsistent_contrasts() -> None:
    hulls, trajectories = _branch_inputs(
        rt_s=(.006, .006), rt_l=(.006, .006),
        dt_s=(.002, .002), dt_l=(.002, .002),
        rd_s=(.001, .001), rd_l=(.001, .001),
    )
    with pytest.raises(ValueError, match=r"x_RT=x_RD\+x_DT"):
        _first_match(hulls, trajectories)


def _summary(
    replicate: int,
    representation: Representation,
    budget: Budget,
    target_regret: float,
    *,
    raw_cell_mean: float = 0.01,
    count: int = 8,
    k8_count: int = 64,
    script_cell_mean: float = 100.0,
) -> EvaluationSummary:
    strata = {"KEEP_MATERIAL": count, "REPLAN_MATERIAL": count}
    raw_means = {"KEEP_MATERIAL": raw_cell_mean, "REPLAN_MATERIAL": raw_cell_mean}
    script_means = {
        "KEEP_MATERIAL": script_cell_mean,
        "REPLAN_MATERIAL": script_cell_mean,
    }
    return EvaluationSummary(
        replicate=replicate,
        representation=representation,
        budget=budget,
        regime_mean_regret={"K8": raw_cell_mean, "K16": target_regret,
                            "K4_TO_16": target_regret, "K16_TO_4": target_regret},
        target_equal_weight_regret=target_regret,
        row_count_by_regime={"K8": k8_count, "K16": 64, "K4_TO_16": 64, "K16_TO_4": 64},
        keep_optimal_count=1,
        zero_regret_oracle_count=0,
        logged_action_count=0,
        logged_scripted_regret_by_regime={"K8": script_cell_mean},
        oracle_regret_max_abs=0.0,
        keep_optimal_by_regime={"K8": 1},
        material_stratum_count_by_regime={"K8": strata},
        mean_regret_by_regime_and_material_stratum={"K8": raw_means},
        logged_scripted_mean_regret_by_regime_and_material_stratum={"K8": script_means},
    )


def _replicates(*, raw_cell_mean: float = 0.01, count: int = 8, k8_count: int = 64,
                script_cell_mean: float = 100.0):
    slots = []
    for replicate in range(8):
        summaries = {}
        for representation in Representation:
            for budget in Budget:
                summaries[(representation, budget)] = _summary(
                    replicate, representation, budget, 0.0,
                    raw_cell_mean=raw_cell_mean,
                    count=count,
                    k8_count=k8_count,
                    script_cell_mean=script_cell_mean,
                )
        slots.append(summaries)
    return slots


def test_frozen_policy_competence_cells_tolerance_and_script_is_not_eligibility() -> None:
    with pytest.raises(TypeError):
        AnalysisPolicy(0.02)  # type: ignore[call-arg]
    admitted = analyze(_replicates(raw_cell_mean=0.010000000001, script_cell_mean=999.0))
    assert admitted["status"] == "IDENTIFYING"
    assert admitted["interpretation"] == "CLOSE_TESTED_MECHANISM"
    assert len(admitted["effect_hulls"]) == 6
    assert len(admitted["trajectory_hulls"]) == 2
    assert all(item["joint_coverage"] == 1.0 for item in admitted["effect_hulls"])
    assert all(item["family_alpha"] is None for item in admitted["effect_hulls"])
    assert len(admitted["raw_long_competence"]["cells"]) == 16
    assert admitted["raw_long_competence"]["script_is_qualification_gate"] is False
    assert admitted["close_budget_descriptions"] == {
        "SHORT": "PRACTICAL_EQUIVALENCE", "LONG": "PRACTICAL_EQUIVALENCE",
    }
    rejected = analyze(_replicates(raw_cell_mean=0.0100000000011))
    assert rejected["interpretation"] == "STOP_RAW_LONG_INCOMPETENT"
    assert rejected["effect_hulls"] == []
    unsupported = analyze(_replicates(count=7))
    assert unsupported["interpretation"] == "NONIDENTIFYING_K8_COMPETENCE_SUPPORT"
    too_few_k8 = analyze(_replicates(k8_count=47))
    assert too_few_k8["interpretation"] == "NONIDENTIFYING_K8_COMPETENCE_SUPPORT"


def test_public_raw_long_competence_never_requires_or_inspects_residual_arms() -> None:
    slots = _replicates()
    raw_only = [slot[(Representation.RAW, Budget.LONG)] for slot in slots]
    result = assess_raw_long_competence(raw_only)
    assert result["status"] == "PASS" and result["disposition"] == "RAW_LONG_COMPETENT"
    stopped = assess_raw_long_competence([
        replace(summary, mean_regret_by_regime_and_material_stratum={
            "K8": {"KEEP_MATERIAL": 0.02, "REPLAN_MATERIAL": 0.01}
        }) if summary.replicate == 2 else summary
        for summary in raw_only
    ])
    assert stopped["disposition"] == "STOP_RAW_LONG_INCOMPETENT"
    assert stopped["report"] is not None

    negative_script = list(raw_only)
    negative_script[5] = replace(
        negative_script[5],
        logged_scripted_mean_regret_by_regime_and_material_stratum={
            "K8": {"KEEP_MATERIAL": -1e-9, "REPLAN_MATERIAL": 0.0}
        },
    )
    failed = assess_raw_long_competence(negative_script)
    assert failed["disposition"] == "NONIDENTIFYING_K8_COMPETENCE_SUPPORT"
    assert failed["report"] is None


def test_generic_structural_failure_is_not_mislabeled_as_k8_support() -> None:
    result = analyze(_replicates(), structural_failures=["RESOURCE_LEDGER_FAILED"])
    assert result["interpretation"] == "UNRESOLVED"
    assert result["failures"] == ["RESOURCE_LEDGER_FAILED"]
    assert result["effect_hulls"] == []


def test_slot_identity_and_script_report_completeness_fail_closed_without_polarity() -> None:
    permuted = _replicates()
    permuted[0], permuted[1] = permuted[1], permuted[0]
    result = analyze(permuted)
    assert result["interpretation"] == "NONIDENTIFYING_K8_COMPETENCE_SUPPORT"
    assert result["effect_hulls"] == [] and result["trajectory_hulls"] == []
    missing_slot = analyze(_replicates()[:-1])
    assert missing_slot["interpretation"] == "NONIDENTIFYING_K8_COMPETENCE_SUPPORT"

    residual_arm_permuted = _replicates()
    true_short = (Representation.TRUE_RESIDUAL, Budget.SHORT)
    residual_arm_permuted[0][true_short], residual_arm_permuted[1][true_short] = (
        residual_arm_permuted[1][true_short], residual_arm_permuted[0][true_short]
    )
    result = analyze(residual_arm_permuted)
    assert result["status"] == "NONIDENTIFYING"
    assert result["effect_hulls"] == []
    assert any("TRUE_RESIDUAL/SHORT" in failure for failure in result["failures"])

    missing_script = _replicates()
    raw_long = missing_script[3][(Representation.RAW, Budget.LONG)]
    missing_script[3][(Representation.RAW, Budget.LONG)] = replace(
        raw_long, logged_scripted_mean_regret_by_regime_and_material_stratum={
            "K8": {"KEEP_MATERIAL": 0.0}
        },
    )
    result = analyze(missing_script)
    assert result["interpretation"] == "NONIDENTIFYING_K8_COMPETENCE_SUPPORT"
    assert result["effect_hulls"] == []

    negative_base = _replicates()
    bad = negative_base[4][(Representation.TRUE_RESIDUAL, Budget.SHORT)]
    negative_base[4][(Representation.TRUE_RESIDUAL, Budget.SHORT)] = replace(
        bad, target_equal_weight_regret=-1e-9,
    )
    result = analyze(negative_base)
    assert result["status"] == "NONIDENTIFYING"
    assert "finite and nonnegative" in result["failures"][0]
    assert result["effect_hulls"] == []


def test_material_advantage_exact_tail_classification() -> None:
    assert classify_material_advantage(-0.02) == "KEEP_MATERIAL"
    assert classify_material_advantage(0.02) == "REPLAN_MATERIAL"
    assert classify_material_advantage(-0.019999999) is None
    assert classify_material_advantage(0.019999999) is None
    with pytest.raises(ValueError):
        classify_material_advantage(float("nan"))


def _analysis():
    return {
        "status": "NONIDENTIFYING",
        "interpretation": "UNRESOLVED",
        "failures": ["test admission"],
        "effect_hulls": [],
        "trajectory_hulls": [],
        "raw_long_competence": None,
        "close_budget_descriptions": None,
        "inference_method": FIXED_CENSUS_METHOD,
        "target_population": "FIXED_ADDRESSES_0_TO_7_NO_SEED_SUPERPOPULATION",
        "intervals": [],
    }


def _test_only_nonresult_evidence():
    return {
        "resource": {
            "memory_floor_pass": True,
            "available_physical_bytes": 4 * 1024**3,
            "effective_available_bytes": 4 * 1024**3,
        },
        "ledger": {
            "formula": "8*1088*256 + 16*actual_common_future_branch_count",
            "charged_full_tape_primitive_team_steps": 2_228_224,
            "common_future_steps_per_actual_branch": 16,
            "expected_common_future_branch_count": 0,
            "actual_common_future_branch_count": 0,
            "actual_common_future_steps": 0,
            "pre_result_exact": True, "within_ceiling": True,
            "actual_total_steps": 2_228_224, "ceiling": 2_596_864,
        },
        "runtime": {
            "workers": 1, "threads_per_worker": 1,
            "peak_rss_bytes": 0, "wall_seconds": 0,
        },
        "admission": {name: False for name in (
            "disjoint_panels", "matched_inputs", "derangement_valid", "common_future_valid",
            "raw_long_competent", "resource_valid", "ledger_valid", "runtime_valid",
            "calibration_valid", "k8_competence_support_valid",
        )},
    }


def test_schema_rejects_legacy_registration_and_atomic_fresh_publication(tmp_path: Path) -> None:
    payload = result_skeleton(
        analysis=_analysis(), replicates=tuple({"replicate": index} for index in range(8)),
        **_test_only_nonresult_evidence(),
    )
    validate_result(payload)
    legacy = dict(payload)
    legacy["schema_version"] = "CRTO-B1-RESULT-v4"
    with pytest.raises(Exception):
        validate_result(legacy)
    tampered = dict(payload)
    tampered["unexpected"] = True
    with pytest.raises(Exception):
        validate_result(tampered)

    output = tmp_path / "fresh-root"
    result = tmp_path / "fresh-result.json"

    def executor(stage: Path):
        (stage / "receipt.txt").write_text("non-result test", encoding="utf-8")
        return payload

    published = _atomic_publish_with_executor(output, result, executor=executor)
    assert published == payload and (output / "receipt.txt").exists() and result.exists()
    with pytest.raises(FileExistsError):
        _atomic_publish_with_executor(output, tmp_path / "other.json", executor=executor)

    identifying = result_skeleton(
        analysis={**_analysis(), "status": "IDENTIFYING", "failures": []},
        replicates=tuple({"replicate": index} for index in range(8)),
        **_test_only_nonresult_evidence(),
    )
    blocked_root = tmp_path / "blocked-root"
    blocked_result = tmp_path / "blocked-result.json"
    with pytest.raises((PermissionError, ValueError)):
        _atomic_publish_with_executor(
            blocked_root, blocked_result, executor=lambda _stage: identifying,
        )
    assert not blocked_root.exists() and not blocked_result.exists()


def test_identifying_result_requires_complete_recomputed_semantics() -> None:
    evidence = _test_only_nonresult_evidence()
    evidence["admission"] = {name: True for name in evidence["admission"]}
    payload = result_skeleton(
        analysis=analyze(_replicates()),
        replicates=tuple({"replicate": index} for index in range(8)),
        **evidence,
    )
    validate_result(payload)

    empty_hulls = deepcopy(payload)
    empty_hulls["analysis"]["effect_hulls"] = []
    with pytest.raises(ValueError, match="exact six"):
        validate_result(empty_hulls)

    wrong_branch = deepcopy(payload)
    wrong_branch["analysis"]["interpretation"] = "PERSISTENT_ALIGNED_BIAS"
    with pytest.raises(ValueError, match="first-match"):
        validate_result(wrong_branch)

    mismatched_ledger = deepcopy(payload)
    mismatched_ledger["ledger"]["expected_common_future_branch_count"] = 1
    with pytest.raises(ValueError, match="ledger_valid"):
        validate_result(mismatched_ledger)
