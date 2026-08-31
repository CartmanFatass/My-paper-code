from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from experiments.candidates.ucope.contextual_paid_acquisition_r01 import analysis as analysis_module
from experiments.candidates.ucope.contextual_paid_acquisition_r01.analysis import (
    analyze_acquisition,
    minimum_signed_specificity,
    validate_analysis,
)
from experiments.candidates.ucope.contextual_paid_acquisition_r01.artifact import _atomic_create_bytes, build_complete_result, validate_complete_result
from experiments.candidates.ucope.contextual_paid_acquisition_r01.contract import (
    CONTRACT_ID,
    FEATURE_NAMES,
    K_TRAIN,
    MODEL_SPEC,
    OPTIMIZER_SPEC,
    PRODUCTION_MODE,
    SCHEMA_VERSION,
    SEED_SLOTS,
    default_manifest,
)
from experiments.candidates.ucope.contextual_paid_acquisition_r01.evaluation import audit_discrete_policy, validate_competence
from experiments.candidates.ucope.contextual_paid_acquisition_r01.oracle import construct_flip_certificate
from experiments.candidates.ucope.contextual_paid_acquisition_r01.schema import SeedEvaluation
from experiments.candidates.ucope.contextual_paid_acquisition_r01.rng import rng_contract


FORBIDDEN_FIELDS = {
    "contract_spec_digest", "manifest_digest", "tape_digest", "dataset_digest", "support_digest",
    "artifact_digest", "state_digest", "checkpoint_digests", "rng_contract_digest",
}


def _production_preflight_record():
    manifest = default_manifest()
    size = manifest["episodes_per_context"]
    unit = size // 10
    strata = [f"{action}:{period}" for action in ("PROBE", "IMMEDIATE") for period in K_TRAIN]
    base, remainder = divmod(5 * unit, 7)
    files = {}
    counts = {}
    for seed_index, seed in enumerate(SEED_SLOTS):
        for cell_index, cell in enumerate(manifest["context_ids"]):
            key = f"{seed}|{cell}"
            linked = cell.startswith("LINKED-")
            files[key] = {"filename": f"cell-{seed_index:02d}-{cell_index:02d}.jsonl.gz", "rows": size}
            counts[key] = {
                "episodes": size,
                "root": {"PROBE": 5 * unit, **{f"IMMEDIATE:{k}": unit for k in K_TRAIN}},
                "tail_conditional_probe": {str(k): unit for k in K_TRAIN},
                "regimes": {"LONG": size // 2, "SHORT": size // 2},
                "displayed_short_count": {str(n): base + (n < remainder) for n in range(7)},
                "action_stratified_regimes": {name: {"LONG": unit // 2, "SHORT": unit // 2} for name in strata},
                "actual_display_joint": {
                    name: ({"LONG|LONG": unit // 2, "SHORT|SHORT": unit // 2} if linked else {
                        "LONG|LONG": unit // 4, "LONG|SHORT": unit // 4,
                        "SHORT|LONG": unit // 4, "SHORT|SHORT": unit // 4,
                    }) for name in strata
                },
            }
    return {
        "schema_version": SCHEMA_VERSION, "contract_id": CONTRACT_ID, "mode": PRODUCTION_MODE,
        "episodes_per_context": manifest["episodes_per_context"], "seed_slots": list(SEED_SLOTS),
        "context_ids": list(manifest["context_ids"]), "contract_spec": deepcopy(manifest["contract_spec"]),
        "materialized_files": files, "seed_context_counts": counts,
        "complete": True, "optimizer_updates": 0,
    }


def _checkpoint_record(seed):
    return {
        "format": "UCOPE_CPA_SINGLE_SHARED_CHECKPOINT_V2", "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID, "seed_slot": seed, "feature_names": list(FEATURE_NAMES),
        "train_periods": list(K_TRAIN), "model_spec": deepcopy(MODEL_SPEC),
        "optimizer_spec": deepcopy(OPTIMIZER_SPEC), "completed_batches": 640, "total_batches": 640,
        "optimizer_updates": 640, "mode": PRODUCTION_MODE,
        "contract_spec": deepcopy(default_manifest()["contract_spec"]),
        "support_record": _production_preflight_record(),
        "rng_contract": rng_contract(),
    }


def _oracle_selected_actions():
    return {
        cell.context_id: max((value, label) for label, value in cell.test_root_values.items())[1]
        for cell in construct_flip_certificate().cells
    }


def _oracle_tail_policy():
    return {cell.context_id: dict(cell.test_tail_optima) for cell in construct_flip_certificate().cells}


def _evaluation(seed, *, root_selected=None, tail_selected=None, **changes):
    root_selected = deepcopy(root_selected if root_selected is not None else _oracle_selected_actions())
    tail_selected = deepcopy(tail_selected if tail_selected is not None else _oracle_tail_policy())
    audit = audit_discrete_policy(root_selected, tail_selected)
    root_scores = {
        cell: {label: (2.0 if label == selected else 0.0) for label in {"PROBE", "IMMEDIATE:2", "IMMEDIATE:4", "IMMEDIATE:6", "IMMEDIATE:8"}}
        for cell, selected in root_selected.items()
    }
    tail_scores = {
        cell: {count: {str(k): (2.0 if k == selected else 0.0) for k in (2, 4, 6, 8)} for count, selected in policy.items()}
        for cell, policy in tail_selected.items()
    }
    value = SeedEvaluation(
        seed_slot=seed, checkpoint_record=_checkpoint_record(seed), result_eligible=True,
        action_vector=audit["action_vector"], root_selected_actions=root_selected,
        tail_selected_periods=tail_selected, root_scores=root_scores, tail_scores=tail_scores,
        cell_evidence=audit["cell_evidence"], oracle_action_vector=audit["oracle_action_vector"],
        max_regret=audit["max_regret"], forced_probe_tail_agreement=audit["forced_probe_tail_agreement"],
        cell_tail_agreement=audit["cell_tail_agreement"], root_unique=True, min_root_margin=2.0,
        tail_unique=True, min_tail_margin=2.0, target_flip=audit["target_flip"],
        minimum_seed_signed_specificity=audit["minimum_seed_signed_specificity"],
    )
    return replace(value, **changes)


def _evaluations():
    return tuple(_evaluation(seed) for seed in SEED_SLOTS)


def _build_result():
    evaluations = _evaluations()
    checkpoints = {item.seed_slot: item.checkpoint_record for item in evaluations}
    return build_complete_result(
        preflight_record=_production_preflight_record(), checkpoint_records=checkpoints, seed_evaluations=evaluations,
    )


def _all_mapping_keys(value):
    if isinstance(value, dict):
        yield from value
        for item in value.values():
            yield from _all_mapping_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _all_mapping_keys(item)


def test_fixed_panel_exact_signed_minimum_strict_zero_and_negative_law():
    evidence = deepcopy(_evaluation(SEED_SLOTS[0]).cell_evidence)
    baseline = minimum_signed_specificity(evidence)
    assert baseline > 0
    target = "LINKED-p17_20-c9_100"
    evidence[target]["Gamma"] = {"numerator": 0, "denominator": 1}
    assert minimum_signed_specificity(evidence) == 0
    evidence[target]["Gamma"] = {"numerator": -1, "denominator": 1000}
    assert minimum_signed_specificity(evidence) < 0
    evidence["unexpected"] = evidence.pop(next(cell for cell in evidence if cell != target))
    with pytest.raises(ValueError):
        minimum_signed_specificity(evidence)


@pytest.mark.parametrize("numerator", [0, -1])
def test_fixed_panel_zero_or_negative_stops_acquisition_after_competence(tmp_path, monkeypatch, numerator):
    evaluations = list(_evaluations())
    first = evaluations[0]
    evidence = deepcopy(first.cell_evidence)
    evidence["LINKED-p17_20-c9_100"]["Gamma"] = {"numerator": numerator, "denominator": 1000}
    minimum = minimum_signed_specificity(evidence)
    evaluations[0] = replace(
        first,
        cell_evidence=evidence,
        minimum_seed_signed_specificity={"numerator": minimum.numerator, "denominator": minimum.denominator},
    )
    competence = {"competent_seed_count": 10, "competence_pass": True, "per_seed": {seed: True for seed in SEED_SLOTS}}
    monkeypatch.setattr(analysis_module, "validate_competence", lambda items: competence)
    result = analyze_acquisition(tuple(evaluations))
    assert result["acquisition_all_flips"] is True
    assert result["acquisition_pass"] is False
    assert result["fixed_panel_disposition"] == "STOP_FIXED_PANEL_ACQUISITION"
    competence["competence_pass"] = False
    competence["competent_seed_count"] = 8
    assert analyze_acquisition(tuple(evaluations))["fixed_panel_disposition"] == "STOP_FIXED_PANEL_COMPETENCE"


def test_competence_requires_exact_policy_per_cell_floor_and_no_ties():
    baseline = list(_evaluations())
    assert validate_competence(baseline)["competence_pass"] is True
    for change in ({"root_unique": False}, {"min_root_margin": 0.0}, {"tail_unique": False}, {"min_tail_margin": 0.0}):
        evaluations = list(baseline)
        evaluations[0] = replace(evaluations[0], **change)
        assert validate_competence(evaluations)["per_seed"][SEED_SLOTS[0]] is False
    cell = next(iter(baseline[0].cell_tail_agreement))
    bad_tail = _oracle_tail_policy()
    bad_tail[cell] = {str(count): 2 for count in range(7)}
    evaluations = list(baseline)
    evaluations[0] = _evaluation(SEED_SLOTS[0], tail_selected=bad_tail)
    assert min(evaluations[0].cell_tail_agreement.values()) < 0.95
    assert validate_competence(evaluations)["per_seed"][SEED_SLOTS[0]] is False


def test_analysis_binds_seed_slots_independent_of_input_order():
    evaluations = _evaluations()
    assert validate_analysis(tuple(reversed(evaluations)))["competence_pass"] is True
    with pytest.raises(ValueError):
        validate_analysis((evaluations[0], *evaluations[1:-1], evaluations[0]))
    result = analyze_acquisition(evaluations)
    assert result["acquisition_all_flips"] is True
    assert Fraction(
        result["panel_min_signed_specificity"]["numerator"],
        result["panel_min_signed_specificity"]["denominator"],
    ) > 0
    assert result["acquisition_pass"] is True
    assert result["fixed_panel_disposition"] == "FIXED_PANEL_ACQUISITION_SUPPORTED"



def test_complete_result_binds_explicit_production_preflight_and_checkpoint_records():
    value = _build_result()
    validated = validate_complete_result(value)
    assert set(value) == {"format", "result"}
    assert value["result"]["preflight_record"] == _production_preflight_record()
    assert value["result"]["preflight_mode"] == "PRODUCTION"
    assert set(value["result"]["checkpoint_records"]) == set(SEED_SLOTS)
    assert FORBIDDEN_FIELDS.isdisjoint(set(_all_mapping_keys(value)))
    assert validated["result"]["representation_conclusion"] == "NONE"
    assert validated["result"]["claim_ceiling"] == "TEN_FIXED_SEED_SLOTS_FINITE_HOST_ONLY_NO_SEED_SUPERPOPULATION"
    assert validated["result"]["fixed_panel_disposition"] == "FIXED_PANEL_ACQUISITION_SUPPORTED"
    legacy = deepcopy(value)
    legacy["format"] = "UCOPE_CPA_COMPLETE_BELIEF_RESULT_V1"
    with pytest.raises(ValueError):
        validate_complete_result(legacy)
    legacy = deepcopy(value)
    legacy["result"]["specificity_t_df9_critical"] = 1.833112932653633
    with pytest.raises(ValueError):
        validate_complete_result(legacy)


@pytest.mark.parametrize("mutation", [
    lambda r: r["preflight_record"].update(mode="TEST_ONLY"),
    lambda r: r["checkpoint_records"].pop(SEED_SLOTS[0]),
    lambda r: r["checkpoint_records"][SEED_SLOTS[0]].update(seed_slot=SEED_SLOTS[1]),
    lambda r: r["checkpoint_records"][SEED_SLOTS[0]].update(completed_batches=0),
    lambda r: r["checkpoint_records"][SEED_SLOTS[0]].update(format="DRIFT"),
    lambda r: r["checkpoint_records"][SEED_SLOTS[0]].update(rng_contract={}),
    lambda r: r["seed_evaluations"][0].update(max_regret=float("nan")),
    lambda r: r["seed_evaluations"][0].update(forced_probe_tail_agreement=1.01),
    lambda r: r["seed_evaluations"][0].update(cell_tail_agreement={}),
    lambda r: r["seed_evaluations"][0].update(root_unique=1),
    lambda r: r["seed_evaluations"][0].update(min_root_margin=0.0),
    lambda r: r["seed_evaluations"][0].update(min_root_margin=float("nan")),
    lambda r: r["seed_evaluations"][0].update(target_flip=False),
    lambda r: r["seed_evaluations"][0].update(minimum_seed_signed_specificity={"numerator": 0, "denominator": 1}),
    lambda r: r["seed_evaluations"][0].update(extra=True),
    lambda r: r.update(complete=False),
    lambda r: r.update(representation_conclusion="COUNT_WINS"),
    lambda r: r.update(claim_ceiling="BROADER_THAN_FROZEN_HOST"),
    lambda r: r.update(panel_min_signed_specificity={"numerator": 0, "denominator": 1}),
    lambda r: r.update(fixed_panel_disposition="FIXED_PANEL_ACQUISITION_SUPPORTED-ish"),
])
def test_complete_result_strictly_rejects_partial_or_forged_payloads(mutation):
    value = deepcopy(_build_result())
    mutation(value["result"])
    with pytest.raises(ValueError):
        validate_complete_result(value)


def test_seed_evaluation_schema_has_only_prespecified_fields():
    assert set(SeedEvaluation.__dataclass_fields__) == {
        "seed_slot", "checkpoint_record", "result_eligible", "action_vector", "root_selected_actions",
        "tail_selected_periods", "root_scores", "tail_scores", "cell_evidence", "oracle_action_vector",
        "max_regret", "forced_probe_tail_agreement", "cell_tail_agreement", "root_unique",
        "min_root_margin", "tail_unique", "min_tail_margin", "target_flip", "minimum_seed_signed_specificity",
    }


def test_synthetic_cell_evidence_has_exact_fraction_decomposition_and_external_values():
    evaluation = _evaluation(SEED_SLOTS[0])
    assert evaluation.cell_evidence == audit_discrete_policy(evaluation.root_selected_actions, evaluation.tail_selected_periods)["cell_evidence"]
    for evidence in evaluation.cell_evidence.values():
        assert set(evidence) == {"B", "A0", "A", "I", "D", "Gamma", "J", "G", "V_star", "regret", "tail_agreement"}
        values = {name: Fraction(item["numerator"], item["denominator"]) for name, item in evidence.items()}
        assert values["A0"] - values["B"] == values["D"]
        assert values["A"] - values["A0"] == values["I"]
        assert values["Gamma"] == values["I"] + values["D"] == values["A"] - values["B"]
        assert values["G"] == values["J"] - values["B"]
        assert values["regret"] == values["V_star"] - values["J"] >= 0
        assert 0 <= values["tail_agreement"] <= 1


@pytest.mark.parametrize("field", ["B", "A0", "A", "I", "D", "Gamma", "J", "G", "V_star"])
def test_result_validator_recomputes_and_rejects_forged_exact_cell_evidence(field):
    value = deepcopy(_build_result())
    cell = next(iter(value["result"]["seed_evaluations"][0]["cell_evidence"]))
    value["result"]["seed_evaluations"][0]["cell_evidence"][cell][field] = {"numerator": 999, "denominator": 1}
    with pytest.raises(ValueError):
        validate_complete_result(value)


def test_result_rejects_seed_to_checkpoint_record_mismatch():
    value = deepcopy(_build_result())
    value["result"]["checkpoint_records"][SEED_SLOTS[0]] = _checkpoint_record(SEED_SLOTS[1])
    with pytest.raises(ValueError):
        validate_complete_result(value)


def test_test_only_checkpoint_evaluation_is_result_ineligible():
    evaluations = list(_evaluations())
    test_record = deepcopy(evaluations[0].checkpoint_record)
    test_record["mode"] = "TEST_ONLY"
    evaluations[0] = replace(evaluations[0], checkpoint_record=test_record, result_eligible=False)
    checkpoints = {item.seed_slot: item.checkpoint_record for item in evaluations}
    with pytest.raises(ValueError):
        build_complete_result(
            preflight_record=_production_preflight_record(), checkpoint_records=checkpoints,
            seed_evaluations=evaluations,
        )


def test_complete_result_with_learned_ties_is_publishable_structure_but_incompetent():
    tied = []
    for evaluation in _evaluations():
        root_scores = deepcopy(evaluation.root_scores)
        target = "LINKED-p17_20-c9_100"
        root_scores[target]["IMMEDIATE:2"] = root_scores[target]["PROBE"]
        tied.append(replace(evaluation, root_scores=root_scores, root_unique=False, min_root_margin=0.0))
    value = build_complete_result(
        preflight_record=_production_preflight_record(),
        checkpoint_records={item.seed_slot: item.checkpoint_record for item in tied},
        seed_evaluations=tied,
    )
    assert value["result"]["complete"] is True
    assert value["result"]["competence_pass"] is False
    assert value["result"]["acquisition_pass"] is False
    assert value["result"]["fixed_panel_disposition"] == "STOP_FIXED_PANEL_COMPETENCE"
    assert validate_complete_result(value) == value


def test_removed_seed_superpopulation_inference_surface_is_absent():
    source = "\n".join(
        Path(path).read_text(encoding="utf-8").lower()
        for path in (
            "experiments/candidates/ucope/contextual_paid_acquisition_r01/contract.py",
            "experiments/candidates/ucope/contextual_paid_acquisition_r01/analysis.py",
            "experiments/candidates/ucope/contextual_paid_acquisition_r01/schema.py",
            "experiments/candidates/ucope/contextual_paid_acquisition_r01/artifact.py",
        )
    )
    for forbidden in ("specificity_lower_bound", "student", "t_df9", "one_sided_95"):
        assert forbidden not in source


def test_atomic_create_bytes_never_replaces_a_concurrent_winner(tmp_path):
    destination = tmp_path / "create-only.bin"
    payloads = (b"first-complete-payload", b"second-complete-payload")
    def attempt(payload):
        try:
            _atomic_create_bytes(destination, payload)
            return "CREATED"
        except FileExistsError:
            return "EXISTS"
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(attempt, payloads))
    assert sorted(outcomes) == ["CREATED", "EXISTS"]
    assert destination.read_bytes() in payloads
    assert not list(tmp_path.glob("*.tmp"))
