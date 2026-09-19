"""Final trajectory and six-endpoint publication contracts."""

import copy

import numpy as np
import pytest

from experiments.candidates.vap_folr_core.last_sighting_a01.artifacts import (
    array_digest,
    write_panel,
)
from experiments.candidates.vap_folr_core.last_sighting_a01.publication import (
    ARMS,
    EVALUATION_SEED,
    OBJECT,
    TRAINING_SEEDS,
    study_result,
)


def episode():
    return {
        "entities": np.zeros((21, 5, 4), dtype=np.float32),
        "previous_action": np.zeros((21, 5, 5), dtype=np.float32),
        "entity_mask": np.zeros((21, 5), dtype=bool),
        "visible": np.eye(5, dtype=bool)[None].repeat(21, 0),
        "obs_mask": (~np.eye(5, dtype=bool))[None].repeat(21, 0),
        "seen": np.eye(5, dtype=bool)[None].repeat(21, 0),
        "age": np.zeros((21, 5, 5), dtype=np.int16),
        "birth": np.zeros((21, 5), dtype=bool),
        "continuation": np.ones((21, 5), dtype=bool),
        "departure": np.zeros((21, 5), dtype=bool),
        "event": np.zeros(21, dtype=bool),
        "actions": np.zeros((20, 5), dtype=np.int64),
        "reward": np.arange(20, dtype=np.float32),
        "terminated": np.r_[np.zeros(19, dtype=np.float32), np.ones(1, dtype=np.float32)],
    }


def endpoint(arm, seed, value):
    return {
        "object": OBJECT,
        "arm": arm,
        "status": "complete",
        "training_seed": seed,
        "evaluation_seed": EVALUATION_SEED,
        "training_episodes": 5000,
        "training_transitions": 100000,
        "optimizer_steps": 4969,
        "evaluation_episodes": 128,
        "evaluation_transitions": 2560,
        "evaluation_optimizer_steps": 0,
        "evaluation_returns": [value] * 128,
    }


def test_panel_retains_all_arrays_and_semantic_digest(tmp_path):
    path = tmp_path / "final-panel.npz"
    result = write_panel(path, [episode(), episode()])
    with np.load(path) as retained:
        arrays = {name: retained[name] for name in retained.files}
    assert set(arrays) == set(episode())
    assert result["episodes"] == 2 and result["transitions"] == 40
    assert result["content_sha256"] == array_digest(arrays)
    changed = copy.deepcopy(arrays)
    changed["reward"][0, 0] += 1
    assert array_digest(changed) != result["content_sha256"]


def test_study_result_requires_exact_six_and_reports_signed_contrasts():
    summaries = []
    expected = []
    for index, seed in enumerate(TRAINING_SEEDS):
        generic = float(index)
        cache = generic + (index - 1) * 0.5
        summaries.extend(
            [endpoint("GENERIC_RETAIN", seed, generic), endpoint("LAST_SIGHTING", seed, cache)]
        )
        expected.append(cache - generic)
    result = study_result(reversed(summaries))
    assert [
        row["last_sighting_minus_generic"]
        for row in result["within_label_contrasts"]
    ] == expected
    assert result["contrast_mean"] == pytest.approx(0.0)
    assert result["contrast_range"] == [-0.5, 0.5]
    assert result["training_instances_per_arm"] == 3
    with pytest.raises(ValueError, match="six endpoints"):
        study_result(summaries[:-1])
    duplicate = summaries + [endpoint(ARMS[0], TRAINING_SEEDS[0], 0.0)]
    with pytest.raises(ValueError, match="duplicate endpoint"):
        study_result(duplicate)

