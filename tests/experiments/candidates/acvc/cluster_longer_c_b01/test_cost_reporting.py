"""Check the actual summary path with an already-expired clock and no learner."""
import json
import time

import pytest


@pytest.mark.parametrize("episodes,train_ticks,updates", [(512, 131072, 1024), (1024, 262144, 2048)])
def test_normal_c_cost_report_uses_requested_exposure(tmp_path, monkeypatch, episodes, train_ticks, updates):
    from scripts import run_acvc_fresh_dense_reuse_b01 as runner

    calls = []

    def forbidden_model_construction(*args, **kwargs):
        calls.append("model construction")
        raise AssertionError("This report-only test must not construct a learner")

    monkeypatch.setattr(runner, "templates", forbidden_model_construction)
    output = tmp_path / "report_only"
    code = runner.run(output, "f" * 40, time.monotonic() - 10, 1,
                      train_episodes=episodes, master=17, evaluation_namespace=19,
                      object_name="SYNTHETIC_COST_REPORT_TEST", card_path="synthetic")
    result = json.loads((output / "summary.json").read_text())
    assert code != 0 and result["status"] == "incomplete"
    assert "TimeoutError" in result["error"] and not calls
    assert result["counts"]["fresh_dense_initializations"] == 0
    assert result["counts"]["optimizer_steps"] == 0
    assert result["configuration"]["training_episodes"] == episodes
    assert result["cost_law"] == (
        f"imports+construction + {train_ticks} training team steps + {updates} full-rollout "
        "replay/backward/Adam calls + 3 checkpoint loads + 49152 evaluation team "
        "steps + C/F/dwell checks + publication and process exit"
    )
