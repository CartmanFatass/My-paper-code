import copy

import numpy as np
import torch

from experiments.candidates.vap_folr_core.entity_history_b01.model import Actor
from experiments.candidates.vap_folr_core.predictive_aux_a01.artifacts import (
    PREDICTION_KEY,
    array_digest,
    write_panel,
)


def episode():
    continuation = np.ones((21, 5), dtype=bool)
    continuation[0] = False
    visible = np.eye(5, dtype=bool)[None].repeat(21, axis=0)
    event = np.zeros(21, dtype=bool)
    event[[2, 3, 20]] = True
    return {
        "entities": np.zeros((21, 5, 4), dtype=np.float32),
        "previous_action": np.zeros((21, 5, 5), dtype=np.float32),
        "entity_mask": np.zeros((21, 5), dtype=bool),
        "visible": visible,
        "obs_mask": ~visible,
        "seen": visible.copy(),
        "age": np.zeros((21, 5, 5), dtype=np.int16),
        "birth": ~continuation,
        "continuation": continuation,
        "departure": np.zeros((21, 5), dtype=bool),
        "event": event,
        "actions": np.zeros((20, 5), dtype=np.int64),
        "reward": np.arange(20, dtype=np.float32),
        "terminated": np.r_[np.zeros(19, dtype=np.float32), np.ones(1, dtype=np.float32)],
    }


def test_panel_retains_inputs_predictions_and_prediction_excluded_digest(tmp_path):
    torch.manual_seed(929)
    actor = Actor("GENERIC_RETAIN")
    with torch.random.fork_rng(devices=[]):
        predictor = torch.nn.Linear(64, 1)
    path = tmp_path / "panel.npz"
    result = write_panel(path, [episode(), episode()], actor, predictor)
    with np.load(path) as retained:
        arrays = {name: retained[name] for name in retained.files}
    assert set(arrays) >= {
        "entities", "actions", "reward", "birth", "continuation", "departure",
        "event", PREDICTION_KEY, "predictor_targets", "predictor_eligible",
    }
    assert arrays[PREDICTION_KEY].shape == (2, 18, 5)
    assert arrays["reward"].dtype == np.float32
    assert result["prediction"]["count"] == 180
    # Events at action times 2 and 3 select the union 2..5 once; terminal t=20 has no action.
    assert result["post_event_window"]["episode_tick_counts"] == [4, 4]
    assert result["post_event_window"]["episode_reward_sums"] == [14.0, 14.0]

    changed = copy.deepcopy(arrays)
    changed[PREDICTION_KEY] = changed[PREDICTION_KEY] + 1
    assert array_digest(arrays, exclude=(PREDICTION_KEY,)) == array_digest(
        changed, exclude=(PREDICTION_KEY,)
    )
    assert array_digest(arrays) != array_digest(changed)
    assert result["input_sha256"] == array_digest(arrays, exclude=(PREDICTION_KEY,))
    assert result["panel_sha256"] == array_digest(arrays)

