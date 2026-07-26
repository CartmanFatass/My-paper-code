from __future__ import annotations

import hashlib

import numpy as np

from ha_ctse_process import continuous_roster_reactive_reduction_g35 as g35
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from scripts import run_continuous_roster_history_proxy_coherence_g37 as runner


def _valid_metrics() -> dict[str, bool]:
    return {
        "operational_valid": True,
        "source_valid": True,
        "g36_reference_valid": True,
        "factorized_access_pass": True,
        "factorized_access_confident_fail": False,
        "coherence_noninferior": True,
        "material_coherence_loss": False,
    }


def test_first_match_truth_table_is_exact() -> None:
    metrics = _valid_metrics()
    assert runner.select_g37_result_branch(metrics) == runner.SUFFICIENT_BRANCH
    for field, branch in (
        ("operational_valid", runner.INVALID_BRANCH),
        ("source_valid", runner.SOURCE_FAILURE_BRANCH),
        ("g36_reference_valid", runner.SOURCE_FAILURE_BRANCH),
    ):
        candidate = {**metrics, field: False}
        assert runner.select_g37_result_branch(candidate) == branch
    candidate = {**metrics, "factorized_access_pass": False, "factorized_access_confident_fail": True}
    assert runner.select_g37_result_branch(candidate) == runner.LOAD_BEARING_BRANCH
    candidate = {**metrics, "coherence_noninferior": False, "material_coherence_loss": True}
    assert runner.select_g37_result_branch(candidate) == runner.LOAD_BEARING_BRANCH
    candidate = {**metrics, "coherence_noninferior": False}
    assert runner.select_g37_result_branch(candidate) == runner.UNDERPOWERED_BRANCH


def test_configuration_freezes_inventory_and_zero_training() -> None:
    nonformal = runner._configuration(formal=False)
    assert nonformal == {
        "formal": False,
        "replicates": 1,
        "capacities": [6, 8, 12],
        "factorized_cells_per_capacity": 4,
        "total_new_cells": 12,
        "evaluation_episodes_per_cell": 8,
        "evaluation_episodes": 96,
        "horizon": 48,
        "evaluation_transitions": 4608,
        "optimizer_steps": 0,
        "bootstrap_resamples": 250,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
    }
    formal = runner._configuration(formal=True)
    assert formal["replicates"] == 3
    assert formal["total_new_cells"] == 36
    assert formal["evaluation_episodes"] == 4608
    assert formal["evaluation_transitions"] == 221184
    assert formal["bootstrap_resamples"] == 10_000
    assert formal["optimizer_steps"] == 0


def test_bootstrap_seed_and_dedicated_authority_are_frozen(tmp_path) -> None:
    plan_a = runner._bootstrap_plan(
        formal=True, replicates=3, episodes=128, repetitions=5
    )
    plan_b = runner._bootstrap_plan(
        formal=True, replicates=3, episodes=128, repetitions=5
    )
    assert all((left == right).all() for left, right in zip(plan_a, plan_b))
    try:
        runner.evaluate(
            run_root=tmp_path / "run",
            g35_root=tmp_path / "g35",
            g36_root=tmp_path / "g36",
            source_commit="a" * 40,
            formal=True,
            authorization_token="wrong",
            preflight_root=tmp_path / "preflight",
        )
    except ValueError as error:
        assert "dedicated authority token" in str(error)
    else:
        raise AssertionError("formal G37 evaluation accepted the wrong token")


def test_nonformal_action_noise_pairing_uses_exact_episode_subset() -> None:
    processes = g35.make_process_ledgers(
        replicate=0, capacity=6, episode_count=8, formal=True
    )
    noise = g32.make_action_noise(
        (row.episode_id for row in processes),
        action_seed=g35.seed_block(0, formal=True)["evaluation_action"],
        member_capacity=6,
    )
    expected = hashlib.sha256(np.ascontiguousarray(noise).tobytes()).hexdigest()
    assert runner._expected_action_noise_digest(
        replicate=0, capacity=6, episode_count=8
    ) == expected
    assert runner._expected_action_noise_digest(
        replicate=0, capacity=6, episode_count=128
    ) != expected
