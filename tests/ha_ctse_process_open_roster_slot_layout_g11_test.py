from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch

from ha_ctse_process.dynamic_roster_direct import (
    collect_direct_trajectory,
    make_action_uniforms,
)
from ha_ctse_process.dynamic_roster_testbed import HORIZON, constructive_actions
from ha_ctse_process.open_roster_high_churn_g9 import (
    HighChurnEnv,
    expected_roster_schedule,
    high_churn_lifecycle_contract_valid,
)
from ha_ctse_process.open_roster_slot_layout_g11 import (
    DENSE_LAYOUT,
    LAYOUTS,
    LOGICAL_CAPACITY,
    SlotLayout,
    make_layout_factory,
    make_layout_ledger,
    remap_uniforms,
)
from scripts import run_open_roster_slot_layout_g11 as runner


def test_layout_ledgers_are_isomorphic_and_constructively_solvable() -> None:
    dense = make_layout_ledger(3, master_seed=runner.LEDGER_SEED, layout=DENSE_LAYOUT)
    dense_schedule = expected_roster_schedule(dense.profile)
    for layout in LAYOUTS:
        layout.validate()
        ledger = make_layout_ledger(3, master_seed=runner.LEDGER_SEED, layout=layout)
        assert ledger.wave_arrivals == dense.wave_arrivals
        assert expected_roster_schedule(ledger.profile) == dense_schedule
        for field in (
            "owner_priorities",
            "presentation_priorities",
            "direct_frontier_priorities",
        ):
            for logical, physical in enumerate(layout.logical_to_physical):
                assert np.array_equal(
                    getattr(ledger, field)[:, physical],
                    getattr(dense, field)[:, logical],
                )
        environment = HighChurnEnv(ledger)
        while environment.time < HORIZON:
            view = environment.observe()
            environment.step(constructive_actions(environment, view))
        assert environment.outcome().utility == 1.0


def test_layout_and_uniform_mapping_fail_closed() -> None:
    duplicate = SlotLayout("duplicate", 48, (0,) * LOGICAL_CAPACITY)
    with pytest.raises(ValueError, match="injective"):
        duplicate.validate()
    out_of_range = SlotLayout("bad", 48, tuple(range(47)) + (48,))
    with pytest.raises(ValueError, match="capacity"):
        out_of_range.validate()

    logical = make_action_uniforms(
        (0, 1),
        lifecycle_capacity=LOGICAL_CAPACITY,
        action_seed=runner.ACTION_SEED_BASE,
    )
    for layout in LAYOUTS:
        physical = remap_uniforms(logical, layout)
        assert physical.shape == (HORIZON, 2, layout.capacity)
        for source, target in enumerate(layout.logical_to_physical):
            assert np.array_equal(physical[:, :, target], logical[:, :, source])
    with pytest.raises(ValueError, match="shape"):
        remap_uniforms(logical[:, :, :-1], DENSE_LAYOUT)


def test_sparse_padding_preserves_lifecycle_state_contract() -> None:
    padded = LAYOUTS[-1]
    trajectory = collect_direct_trajectory(
        runner._model(),
        ledger_ids=(0,),
        ledger_seed=runner.LEDGER_SEED,
        action_seed=runner.ACTION_SEED_BASE,
        device=torch.device("cpu"),
        ledger_factory=make_layout_factory(padded),
        environment_factory=HighChurnEnv,
    )
    assert trajectory.observations.shape[:3] == (HORIZON, 1, padded.capacity)
    assert high_churn_lifecycle_contract_valid(
        trajectory,
        ledger_seed=runner.LEDGER_SEED,
        ledger_factory=make_layout_factory(padded),
    )


def test_g11_contract_keeps_g8_policy_and_reduced_eval_budget() -> None:
    assert runner.ALGORITHM_ID == "SLOT_LAYOUT_INVARIANCE_G11"
    assert runner.FORMAL_EVAL_EPISODES == 64
    assert runner.core.G8_EVAL_EPISODES == 128
    assert runner.core.FORMAL_EVAL_EPISODES == 64
    assert runner._model().roster_representation == {
        "autoregressive_prefix": "active_fraction"
    }


def test_nonformal_full_path_and_tamper_rejection(tmp_path: Path) -> None:
    run_root = tmp_path / "exercise"
    result = runner.exercise(run_root=run_root)
    assert result["operational_valid"] is True
    assert result["branch"] == "NONFORMAL_SLOT_LAYOUT_G11_EXERCISE_COMPLETE"
    assert all(
        int(result["metrics"][f"{layout.name}_paired_outcome_mismatch_count"])
        >= 0
        for layout in LAYOUTS[1:]
    )
    training = runner._read_json(run_root / "train_manifest.json")
    evaluation = runner._read_json(run_root / "evaluation_manifest.json")
    assert training["optimizer_steps"] == 0
    assert len(evaluation["cells"]) == 8
    assert all(cell["model_state_unchanged_exact"] for cell in evaluation["cells"])

    nonformal_as_formal = deepcopy(training)
    nonformal_as_formal["formal"] = True
    runner._write_json(run_root / "train_manifest.json", nonformal_as_formal)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert rejected["branch"] == runner.INVALID_BRANCH

    runner._write_json(run_root / "train_manifest.json", training)
    tampered = deepcopy(evaluation)
    tampered["source_controls"]["rows"][0]["mapping"][0] = 47
    runner._write_json(run_root / "evaluation_manifest.json", tampered)
    rejected = runner.analyze(run_root=run_root)
    assert "slot-layout source-control row mismatch" in rejected["operational_errors"]


def test_formal_contract_and_first_match_boundaries(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="authorization token"):
        runner.train(
            run_root=tmp_path / "wrong_token",
            source_commit="a" * 40,
            formal=True,
            authorization_token="WRONG",
            g8_run_root=runner.DEFAULT_G8_RUN_ROOT,
            replicates=runner.FORMAL_REPLICATES,
            eval_episodes=runner.FORMAL_EVAL_EPISODES,
        )

    passing = {
        "dense48_deterministic_utility_ci95": [runner.DENSE_ACCESS_FLOOR, 0.95, 1.0],
        "reverse48_paired_outcome_mismatch_count": 0,
        "sparse96_paired_outcome_mismatch_count": 0,
        "affine_padded128_paired_outcome_mismatch_count": 0,
        "layout_min_replicate_mean": runner.MINIMUM_LAYOUT_REPLICATE_FLOOR,
        "layout_stochastic_mean": runner.LAYOUT_STOCHASTIC_MEAN_FLOOR,
    }
    assert runner.select_result_branch(passing) == "SLOT_LAYOUT_INVARIANT_G11"

    values = deepcopy(passing)
    values["dense48_deterministic_utility_ci95"][0] = np.nextafter(
        runner.DENSE_ACCESS_FLOOR, 0.0
    )
    assert runner.select_result_branch(values) == "NO_DENSE_LAYOUT_ACCESS_G11"
    mismatch_cases = (
        ("reverse48", "REVERSE_SLOT_DEPENDENCE_G11"),
        ("sparse96", "SPARSE_SLOT_DEPENDENCE_G11"),
        ("affine_padded128", "PADDING_SLOT_DEPENDENCE_G11"),
    )
    for layout, expected in mismatch_cases:
        values = deepcopy(passing)
        values[f"{layout}_paired_outcome_mismatch_count"] = 1
        assert runner.select_result_branch(values) == expected
    values = deepcopy(passing)
    values["layout_min_replicate_mean"] = np.nextafter(
        runner.MINIMUM_LAYOUT_REPLICATE_FLOOR, 0.0
    )
    assert runner.select_result_branch(values) == "UNSTABLE_SLOT_LAYOUT_G11"
