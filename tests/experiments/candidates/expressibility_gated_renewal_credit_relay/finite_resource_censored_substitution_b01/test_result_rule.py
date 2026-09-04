from __future__ import annotations

import json
import time

import pytest

from experiments.candidates.expressibility_gated_renewal_credit_relay.finite_resource_censored_substitution_b01 import config as C
from experiments.candidates.expressibility_gated_renewal_credit_relay.finite_resource_censored_substitution_b01.experiment import _check_deadlines, classify_branch, run_experiment


def arm(c_q: int, rmse: float, gradient_error: float, utility: float) -> dict[str, float | int]:
    return {
        "c_q": c_q,
        "rmse_q": rmse,
        "source_gradient_l2_error": gradient_error,
        "exact_expected_bounded_utility": utility,
    }


def test_first_matching_result_rule() -> None:
    generic = arm(8, 0.3, 0.2, 0.4)
    factor_gain = arm(8, 0.2, 0.1, 0.5)
    factor_estimation = arm(8, 0.2, 0.1, 0.4)
    factor_worse = arm(8, 0.4, 0.3, 0.3)
    factor_mixed = arm(8, 0.2, 0.3, 0.5)
    assert classify_branch(generic, factor_gain, False) == "FRCS-INVALID-INCOMPLETE"
    assert classify_branch(arm(7, 0.3, 0.2, 0.4), factor_gain) == "FRCS-E-GENERIC-UNDEREXPOSED"
    assert classify_branch(generic, factor_gain) == "FRCS-A-FACTORIZED-ENDPOINT-GAIN"
    assert classify_branch(generic, factor_estimation) == "FRCS-B-ESTIMATION-ONLY"
    assert classify_branch(generic, factor_worse) == "FRCS-C-GENERIC-MATCHES-OR-BEATS"
    assert classify_branch(generic, factor_mixed) == "FRCS-D-MIXED"


def test_frozen_counts_exposure_and_static_cost_are_exact() -> None:
    payload = C.project_cost_payload()
    assert payload["counts"] == {
        "training_episodes": 192,
        "training_environment_transitions": 576,
        "optimizer_updates_per_learned_arm": 128,
        "minibatch_size": 32,
        "optimizer_example_exposures_per_learned_arm": 4096,
        "evaluation_episodes_per_arm_or_reference": 256,
        "evaluation_environment_transitions_per_arm_or_reference": 768,
        "exact_evaluation_cells_per_arm_or_reference": 48,
        "trainable_parameters_per_learned_arm": 32,
    }
    assert payload["cost_law"]["projected_seconds_per_learned_arm"] == 119.64
    serialized = json.dumps(payload, sort_keys=True)
    assert '"projected_seconds_per_learned_arm": 119.64' in serialized
    assert "119.64000000000001" not in serialized
    assert payload["cost_law"]["arm_wall_cap_seconds"] == 600.0
    assert payload["exposure_line"] == (
        "updates=128; adam_lr=0.01; nominal_lr_exposure=1.28; "
        "init_half_range=0.05; nominal_exposure_over_init_half_range=25.6"
    )
    assert payload["creates_trajectories_models_optimizers_or_results"] is False
    assert payload["benchmarks_runtime"] is False


@pytest.mark.parametrize(
    "seed,overrides",
    [
        (17, {}),
        (C.SCIENTIFIC_SEED, {"train_episodes": C.TRAIN_EPISODES - 1}),
        (C.SCIENTIFIC_SEED, {"updates": C.UPDATES - 1}),
        (C.SCIENTIFIC_SEED, {"batch_size": C.BATCH_SIZE - 1}),
        (C.SCIENTIFIC_SEED, {"evaluation_episodes": C.EVALUATION_EPISODES - 1}),
    ],
)
def test_direct_scientific_misuse_is_rejected_before_execution(
    seed: int,
    overrides: dict[str, int],
) -> None:
    summary = run_experiment(seed, profile="scientific", **overrides)
    assert summary["branch"] is None
    assert summary["result_rule_applied"] is False
    assert summary["technical_outcome"] == "NON_FROZEN_SCIENTIFIC_REQUEST_REJECTED"
    assert summary["integrity"]["scientific_contract_exact"] is False
    assert summary["integrity"]["scientific_integrity_applicable"] is False
    assert summary["integrity"]["trajectories_models_optimizers_created"] is False


def test_cooperative_deadline_check_stops_crossed_caps() -> None:
    now = time.perf_counter()
    with pytest.raises(TimeoutError, match="invocation wall cap"):
        _check_deadlines(now - 1.0, phase="test")
    with pytest.raises(TimeoutError, match="learned-arm wall cap"):
        _check_deadlines(now + 10.0, arm_deadline=now - 1.0, phase="test")
