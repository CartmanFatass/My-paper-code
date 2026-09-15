"""One real tiny-host execution per arm class: the actual HMASD stack under the FLAT and D2 configurations.

Two lanes, twenty-step episodes, the real Scenario 1 environment and the real agent. This checks that
the FLAT configuration (single constant skill, no coordinator/discriminator training) runs through
the collector, fifteen updates and three panels; it is a technical check, never a scientific result.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
for directory in (ROOT, ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
import run_fsd_baseline_interruption_b01 as baseline

shared = baseline.shared


@pytest.fixture
def tiny(monkeypatch):
    monkeypatch.setattr(shared, "TRAIN_LANES", 2)
    monkeypatch.setattr(shared, "EVAL_LANES", 2)
    monkeypatch.setattr(shared, "HORIZON", 20)
    monkeypatch.setattr(shared, "PROCESS_START", shared.time.perf_counter())


@pytest.mark.parametrize("arm", ["FLAT", "D1280"])
def test_real_tiny_fit_completes_with_expected_learning(tmp_path, tiny, arm):
    out = tmp_path / arm
    assert baseline.main(["fit", "--arm", arm, "--seed", "772203", "--output-root", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "complete" and summary["counts"]["update_stages"] == 15
    assert summary["counts"]["model_constructions"] == 2 and len(summary["panels"]) == 3
    assert all(panel["status"] == "complete" and panel["completed_episodes"] == 2 for panel in summary["panels"])
    calls = summary["optimizer_calls"]
    assert calls["discoverer_actor"] > 0 and calls["discoverer_critic"] > 0
    if arm == "FLAT":
        assert all(calls[k] == 0 for k in baseline.FLAT_ONLY_ZERO)
        assert summary["learner_config"]["n_Z"] == summary["learner_config"]["n_z"] == 1
        assert summary["learner_config"]["k"] == 10 and summary["learner_config"]["policy_interruption_mode"] == "off"
    else:
        assert calls["coordinator"] > 0 and summary["learner_config"]["coordinator_batch_size"] == 1280
    assert not any(summary["evaluation_optimizer_calls"].values())
    displacement = summary["training_rows"][-1]["relative_initialization_displacement"]
    assert displacement["discoverer_actor"] > 0 and displacement["discoverer_critic"] > 0
    if arm == "FLAT":
        assert displacement["coordinator"] in (None, 0.0)
    else:
        assert displacement["coordinator"] > 0
    assert list(baseline.arm_panels(summary)) == [5, 10, 15]
