"""One real tiny-host execution of the flat-update entry: the minibatch size reaches the sampler.

Two lanes, twenty-step episodes, the real Scenario 1 environment and the real agent. Technical check,
no result. Kept apart from the fake-learner tests, whose helper forbids real construction.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_update_b04 as update  # noqa: E402

SEEDS = sorted(update.BLOCKS)
ADMISSION = {"sha": "tiny-technical-check", "command_sha256": "x"}


def test_real_tiny_fit_takes_the_steps_of_the_declared_minibatch_size(tmp_path, monkeypatch):
    """Real stack, two lanes, twenty-step episodes: 2 x 6 x 2 = 24 ten-step sequences per rollout."""
    shared = b01.shared
    monkeypatch.setattr(shared, "TRAIN_LANES", 2)
    monkeypatch.setattr(shared, "EVAL_LANES", 2)
    monkeypatch.setattr(shared, "HORIZON", 20)
    monkeypatch.setattr(shared, "PROCESS_START", shared.time.perf_counter())
    monkeypatch.setattr(update, "ROLLOUTS", 2)
    monkeypatch.setattr(update, "PANEL_ROLLOUTS", (1, 2))
    monkeypatch.setattr(update, "SEQUENCE_BATCH_SIZE", 8)  # three minibatches where the default 32 gives one
    out = tmp_path / "tiny"
    assert update.run_fit("CF_M5", SEEDS[0], out, admission=ADMISSION) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "complete" and summary["failure"] is None
    epochs = summary["learner_config"]["ppo_epochs"]
    assert summary["optimizer_calls"]["discoverer_actor"] == epochs * 3 * 2
    assert summary["optimizer_calls"]["discoverer_critic"] == epochs * 3 * 2
    assert update.expected_low_level_steps(summary["learner_config"]) == epochs * 3 * 2
    assert list(update.fit_endpoint(summary)) == [1, 2]
    assert summary["learner_config"]["lr_discoverer_actor"] == pytest.approx(5e-4)
