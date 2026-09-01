from dataclasses import replace
from types import SimpleNamespace

import pytest

from experiments.candidates.ucope.competence_first_scout_r01.artifact import (
    ASSESS_POLICY_ACTIVITY_FIELDS,
    POLICY_ACTIVITY_FIELDS,
    _validate_complete_policy_activity,
    sanitize_assess_result,
    validate_assess_artifact,
)
from experiments.candidates.ucope.competence_first_scout_r01.checkpoint import expected_policy_activity
from experiments.candidates.ucope.competence_first_scout_r01.contract import ARM_IDS, RunBinding, ScoutConfig
from experiments.candidates.ucope.competence_first_scout_r01.evaluation import PolicyEvaluation
from experiments.candidates.ucope.competence_first_scout_r01.gates import apply_gates


def _evaluation(arm, seed, fold, *, competent=True, acquisition=True):
    return PolicyEvaluation(
        arm, seed, fold, 320, {}, {}, {}, {}, {}, True, True, True, 0.0, 1.0,
        0.1 if acquisition else -0.1, -0.05, competent, competent and acquisition, 8, 512, 1024, 0.0, {},
    )


def test_gate_precedence_and_bc_only_count_raw_lock():
    seeds = ("s0", "s1", "s2")
    complete = [_evaluation(arm, seed, fold, competent=arm == "FT-XF-BC", acquisition=arm == "FT-XF-BC") for arm in ARM_IDS for seed in seeds for fold in (0, 1)]
    assert apply_gates(complete, seed_ids=seeds, final_root_update=320)["count_raw_status"] == "LOCKED"
    flex = [_evaluation(arm, seed, fold, competent=arm == "FT-XF-FLEX", acquisition=arm == "FT-XF-FLEX") for arm in ARM_IDS for seed in seeds for fold in (0, 1)]
    assert apply_gates(flex, seed_ids=seeds, final_root_update=320)["count_raw_status"] == "UNLOCK_SEPARATE_B_DESIGN"
    invalid = apply_gates(flex, seed_ids=seeds, final_root_update=320, valid_attempt=False)
    assert invalid["branch"] == "INVALID_OR_INCOMPLETE" and invalid["count_raw_status"] == "LOCKED"


def test_assess_sanitizer_projects_out_all_learning_outcomes():
    policy_activity = {
        "root_inventory": 1280, "tail_inventory": 640,
        "root_optimizer_updates": 16, "tail_optimizer_updates": 8,
        "root_example_exposures": 4096, "tail_example_exposures": 2048,
        "target_refresh_events": 16, "target_refresh_rows": 2048,
        "target_materialization_events": 0, "target_materialization_rows": 0,
        "root_clipping_events": 2, "tail_clipping_events": 1,
        "root_gradient_norm_sum": 3.0, "tail_gradient_norm_sum": 2.0,
        "root_gradient_norm_max": 2.0, "tail_gradient_norm_max": 1.5,
        "nonfinite_events": 0, "exact_policy_evaluations": 16,
        "sampled_evaluation_episodes": 128,
        "sampled_evaluation_transitions": 256,
    }
    activity = {
        "environment_episodes": 2560, "environment_transitions": 12800,
        "root_rows": 2560, "tail_rows": 1280,
        **policy_activity, "parameter_count": {arm: 1 for arm in ARM_IDS},
        "checkpoint_writes": 12, "policies_completed": 6,
        "per_policy": {"one": policy_activity},
    }
    result = SimpleNamespace(
        config=ScoutConfig.assess(), run_binding=RunBinding.assess("d" * 64), work={"seed_count": 1}, activity=activity,
        stage_times=(), source_refs=("safe.py",), runtime_refs={"worker_count": 1},
        internal_result={"evaluations": [{"regret": 1.0}], "gates": {"competence": False}},
    )
    artifact = sanitize_assess_result(result)
    rendered = str(artifact["activity"]).lower()
    assert "gradient" not in rendered and "clipping" not in rendered
    assert "sampled_evaluation_transitions" not in artifact["activity"]
    assert all("sampled_evaluation_transitions" not in row for row in artifact["activity"]["per_policy"].values())
    assert "internal_result" not in artifact and "checkpoints" not in artifact
    validate_assess_artifact(artifact)
    poisoned = dict(artifact)
    poisoned["activity"] = dict(artifact["activity"], regret=0.0)
    with pytest.raises(ValueError):
        validate_assess_artifact(poisoned)


def test_b1_transition_counter_is_required_but_remains_absent_from_assess_schema():
    config = ScoutConfig.b1()
    assert "sampled_evaluation_transitions" not in ASSESS_POLICY_ACTIVITY_FIELDS
    assert "sampled_evaluation_transitions" in POLICY_ACTIVITY_FIELDS
    rows = {}
    for arm in config.arms:
        for seed in config.seed_ids:
            for fold in (0, 1):
                row = expected_policy_activity(
                    config, arm, fold, config.root_updates, config.tail_updates,
                )
                row.update({
                    "root_clipping_events": 0,
                    "tail_clipping_events": 0,
                    "root_gradient_norm_sum": 0.0,
                    "tail_gradient_norm_sum": 0.0,
                    "root_gradient_norm_max": 0.0,
                    "tail_gradient_norm_max": 0.0,
                    "sampled_evaluation_transitions": 1,
                })
                assert set(row) == POLICY_ACTIVITY_FIELDS
                rows[f"{arm}|{seed}|fold-{fold}"] = row
    summed = (
        "root_optimizer_updates", "tail_optimizer_updates", "root_example_exposures",
        "tail_example_exposures", "target_refresh_events", "target_refresh_rows",
        "target_materialization_events", "target_materialization_rows",
        "root_clipping_events", "tail_clipping_events", "root_gradient_norm_sum",
        "tail_gradient_norm_sum", "nonfinite_events", "exact_policy_evaluations",
        "sampled_evaluation_episodes", "sampled_evaluation_transitions",
    )
    activity = {field: sum(row[field] for row in rows.values()) for field in summed}
    activity.update({
        "root_gradient_norm_max": 0.0,
        "tail_gradient_norm_max": 0.0,
        "per_policy": rows,
    })
    _validate_complete_policy_activity(activity, config)

    missing = {key: dict(row) for key, row in rows.items()}
    missing[next(iter(missing))].pop("sampled_evaluation_transitions")
    with pytest.raises(ValueError, match="per-policy exact activity mismatch"):
        _validate_complete_policy_activity({**activity, "per_policy": missing}, config)

    tampered = {key: dict(row) for key, row in rows.items()}
    tampered[next(iter(tampered))]["root_optimizer_updates"] -= 1
    with pytest.raises(ValueError, match="per-policy exact activity mismatch"):
        _validate_complete_policy_activity({**activity, "per_policy": tampered}, config)
