"""Pure binding/publication checks; no model, RNG, native or optimizer construction."""
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from experiments.candidates.tail_return_distributional_learning.trdl_b01 import learner, study


@pytest.mark.parametrize("master,plan", ((9601, 900), (9602, 300)))
@pytest.mark.parametrize("arm", learner.ARMS)
def test_registered_arm_binding_stops_before_construction(tmp_path, monkeypatch, master, plan, arm):
    calls = []

    def stop_before_models(actual_master, actual_arm):
        calls.append((actual_master, actual_arm))
        raise RuntimeError("controlled binding stop before construction")

    monkeypatch.setattr(study, "models", stop_before_models)
    out = tmp_path / "intercepted"
    result = study.run_arm(arm, master, out, "pure-binding-fixture", 900, time.monotonic())
    assert calls == [(master, arm)]
    assert result["failure"] == "RuntimeError: controlled binding stop before construction"
    assert result["status"] == "incomplete"
    assert result["seed"] == master and result["initial_ordinary_runtime_plan_seconds"] == plan
    assert not any(result["counts"].values())
    assert not (out / "checkpoint.pt").exists()
    assert json.loads((out / "summary.json").read_text())["seed"] == master


def test_unsupported_master_rejected_before_output_or_input(tmp_path):
    with pytest.raises(ValueError, match="registered master"):
        study.run_arm("SCALAR", 9603, tmp_path / "absent", "fixture", 900, time.monotonic())
    assert not (tmp_path / "absent").exists()
    with pytest.raises(ValueError, match="unregistered pair master"):
        study.publish_pair(tmp_path / "missing-s", tmp_path / "missing-q",
                           tmp_path / "absent.json", "fixture", master=9603)
    assert not (tmp_path / "absent.json").exists()


def test_cli_selected_master_own_tail_and_wrong_pair_rejection(tmp_path):
    # Opposite poor worlds make the tail of paired differences a wrong primary.
    values = ([.1] * 64 + [.9] * 192, [.92] * 192 + [.12] * 64)
    paths = [tmp_path / f"{arm}.json" for arm in learner.ARMS]
    for arm, returns, path in zip(learner.ARMS, values, paths):
        study.write_json(path, dict(arm=arm, seed=9602, status="complete",
            counts=dict(train_episodes=512, eval_episodes=256, optimizer_steps=128),
            endpoint=learner.endpoint(returns), wall_seconds_through_closeout=2))
    output = tmp_path / "pair.json"
    runner = Path(__file__).resolve().parents[5] / "scripts" / "run_trdl_b01.py"
    command = [sys.executable, str(runner), "pair", "--seed", "9602",
               "--scalar", str(paths[0]), "--quantile", str(paths[1]),
               "--out", str(output), "--launch-sha", "pure-publication-fixture"]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    saved = json.loads(output.read_text())
    assert "Q32_ABOVE_MEI" in completed.stdout
    assert saved["seed"] == 9602 and saved["delta_tail"] == pytest.approx(.02)
    assert len(saved["SCALAR"]["returns"]) == len(saved["Q32"]["returns"]) == 256
    prior = output.read_bytes()
    for old_indices in ((0,), (0, 1)):
        for index in old_indices:
            row = json.loads(paths[index].read_text())
            row["seed"] = 9601
            study.write_json(paths[index], row)
        with pytest.raises(ValueError, match="requested master"):
            study.publish_pair(*paths, output, "fixture", master=9602)
        assert output.read_bytes() == prior
    # Default publication remains the historical9601 interface, not an implicit9602 selection.
    legacy = study.publish_pair(*paths, tmp_path / "legacy.json", "fixture")
    assert legacy["seed"] == 9601 and legacy["delta_tail"] == pytest.approx(.02)
