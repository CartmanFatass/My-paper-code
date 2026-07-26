from __future__ import annotations

import json

import numpy as np
import pytest

from scripts import run_continuous_roster_history_proxy_free_cs_g36 as runner


def _valid_metrics() -> dict[str, bool]:
    return {
        "operational_valid": True,
        "registered_source_access_valid": True,
        "intervention_access_pass": False,
        "intervention_access_confident_fail": False,
        "proxy_noninferior": False,
        "material_proxy_loss": False,
    }


def test_first_match_truth_table_is_exact() -> None:
    row = _valid_metrics()
    assert runner.select_g36_result_branch({**row, "operational_valid": False}) == runner.INVALID_BRANCH
    assert runner.select_g36_result_branch({**row, "registered_source_access_valid": False}) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g36_result_branch({**row, "intervention_access_pass": True, "proxy_noninferior": True, "material_proxy_loss": True}) == runner.SUFFICIENT_BRANCH
    assert runner.select_g36_result_branch({**row, "intervention_access_confident_fail": True}) == runner.LOAD_BEARING_BRANCH
    assert runner.select_g36_result_branch(row) == runner.UNDERPOWERED_BRANCH


def test_configuration_freezes_all_g36_inventories_and_zero_training() -> None:
    formal = runner._configuration(formal=True)
    assert formal["replicates"] == 3
    assert formal["capacities"] == [6, 8, 12]
    assert formal["intervention_cells_per_capacity"] == 4
    assert formal["total_new_cells"] == 36
    assert formal["evaluation_episodes_per_cell"] == 128
    assert formal["evaluation_transitions"] == 221_184
    assert formal["optimizer_steps"] == 0
    assert formal["K_search"] == 0
    assert formal["hypothetical_transitions"] == 0
    exercise = runner._configuration(formal=False)
    assert exercise["evaluation_transitions"] == 4_608
    assert exercise["bootstrap_resamples"] == 250


def test_registered_arrays_use_the_exact_nonformal_episode_subset(monkeypatch) -> None:
    cells = {
        (replicate, capacity, "CS", "REGISTERED"): {
            "episodes": [
                {"utility": float(replicate * 1_000 + capacity * 100 + episode)}
                for episode in range(128)
            ]
        }
        for replicate in range(3)
        for capacity in (6, 8, 12)
    }
    monkeypatch.setattr(runner, "_g35_cells", lambda evaluation: cells)
    monkeypatch.setattr(
        runner.g34_runner, "_trace_evidence", lambda episode: episode
    )

    values = runner._registered_array(
        {}, cell_name="REGISTERED", metric="utility", replicates=1, episodes=8
    )

    assert all(array.shape == (1, 8) for array in values.values())
    assert np.array_equal(values[6][0], np.arange(600.0, 608.0))


def test_formal_preflight_rejects_summary_without_artifact_validation(
    tmp_path, monkeypatch
) -> None:
    root = tmp_path / "preflight"
    root.mkdir()
    (root / "evaluation_manifest.json").write_text(
        json.dumps({"configuration": runner._configuration(formal=False)}),
        encoding="utf-8",
    )
    (root / "analysis_result.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        runner,
        "_evaluation_errors",
        lambda run_root, evaluation, g35_root: ["tampered trace"],
    )

    with pytest.raises(ValueError, match="tampered trace"):
        runner._validate_formal_preflight(
            root, source_commit="1" * 40, g35_root=tmp_path / "g35"
        )


def test_formal_evaluate_requires_dedicated_authority_and_preflight(tmp_path) -> None:
    with pytest.raises(ValueError, match="authority"):
        runner.evaluate(
            run_root=tmp_path / "formal",
            g35_root=tmp_path / "g35",
            source_commit="1" * 40,
            formal=True,
            authorization_token=None,
            preflight_root=None,
        )
