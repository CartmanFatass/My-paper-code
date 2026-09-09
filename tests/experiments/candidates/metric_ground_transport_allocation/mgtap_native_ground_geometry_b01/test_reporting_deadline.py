import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01 import runner
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def summary(seed, delta):
    return {"seed": seed, "mode": "UAV_B_EXPLORE",
            "configuration": {"eval_episodes": 32, "horizon": 256, "train_episodes": 512},
            "arms": {a: {"fit_complete": True} for a in ("REL", "DENSE")},
            "rows": [{"pair_master": seed, "phase": "eval", "arm": arm,
                      "episode": e, "J": value, "steps": 256}
                     for arm, value in (("REL", delta), ("DENSE", 0.), ("H", 1.))
                     for e in range(32)]}


@pytest.mark.parametrize("delta,reading", [(.02, "REL_ABOVE_MEI"),
    (.01, "INSIDE_MEI"), (-.01, "INSIDE_MEI"), (-.02, "REL_ADVERSE")])
def test_fixed_master_mean_and_mei(delta, reading):
    result = runner.aggregate([summary(8202, delta), summary(8201, delta)])
    assert result["primary"]["mean"] == delta
    assert result["primary"]["reading"] == reading
    assert all(len(p["primary"]["J"]["H"]) == 32 for p in result["pairs"])


def test_opposite_master_effects_are_retained():
    result = runner.aggregate([summary(8201, .04), summary(8202, -.06)])
    assert result["primary"]["pair_means"] == {"8201": .04, "8202": -.06}
    assert result["primary"]["mean"] == pytest.approx(-.01)
    assert result["primary"]["reading"] == "INSIDE_MEI"


@pytest.mark.parametrize("defect", ["missing_master", "duplicate_master", "missing_episode",
    "duplicate_episode", "nan", "null", "wrong_master", "unfinished_fit", "bad_rows", "short_episode"])
def test_missing_or_corrupt_primary_never_gets_polarity(defect):
    values = [summary(8201, .04), summary(8202, .04)]
    if defect == "missing_master": values.pop()
    elif defect == "duplicate_master": values[1] = copy.deepcopy(values[0])
    elif defect == "missing_episode": values[1]["rows"].pop(0)
    elif defect == "duplicate_episode": values[1]["rows"].append(values[1]["rows"][0])
    elif defect == "nan": values[1]["rows"][0]["J"] = float("nan")
    elif defect == "null": values[1]["rows"][0]["J"] = None
    elif defect == "wrong_master": values[1]["rows"][0]["pair_master"] = 999
    elif defect == "unfinished_fit": values[1]["arms"]["REL"]["fit_complete"] = False
    elif defect == "short_episode": values[1]["rows"][0]["steps"] = 2
    else: values[1]["rows"] = [None]
    result = runner.aggregate(values)
    assert result["primary"]["reading"] == "INCOMPLETE"
    assert result["primary"]["mean"] is None
    assert result["pairs"][0]["primary"]["J"]["REL"] == [.04] * 32


def test_hover_missing_does_not_erase_primary_and_bad_files_do(tmp_path):
    values = [summary(8201, .02), summary(8202, .02)]
    values[1]["rows"] = [r for r in values[1]["rows"] if r["arm"] != "H"]
    assert runner.aggregate(values)["primary"]["complete"]
    good = tmp_path / "good.json"
    good.write_text(json.dumps(values[0]))
    bad = tmp_path / "bad.json"
    bad.write_text("{broken")
    for path in (bad, tmp_path / "missing.json"):
        result = runner.aggregate_files([good, path])
        assert result["primary"]["reading"] == "INCOMPLETE"
        assert result["pairs"][0]["primary"]["hover_complete"]


class Clock:
    now = 0.
    def __call__(self): return self.now


def test_import_time_is_charged_before_model_or_factory(tmp_path, monkeypatch):
    clock = Clock()
    clock.now = 1801.
    def forbidden(*args): pytest.fail("expired process constructed model/environment")
    monkeypatch.setattr(runner, "build_pair", forbidden)
    result = runner.run_pair(8201, tmp_path, fixture=True, horizon=2,
                            train_episodes=2, eval_episodes=1, start=0., clock=clock,
                            factory=forbidden)
    assert result["status"] == "CAP_BREACH"
    assert result["pair_elapsed_wall"] == 1801.
    assert result["counts"]["team_steps"] == 0
    assert json.loads((tmp_path / "summary.json").read_text())["cap_breach"]


def test_partial_step_counts_survive_deadline(tmp_path):
    clock = Clock()
    class Slow(SyntheticAdapter):
        def step(self, action):
            result = super().step(action)
            clock.now = 1801.
            return result
    result = runner.run_pair(8201, tmp_path, fixture=True, horizon=2,
                            train_episodes=2, eval_episodes=1, start=0., clock=clock,
                            factory=lambda seed: Slow(seed, horizon=2))
    assert result["status"] == "CAP_BREACH"
    assert result["counts"]["partial_episode_steps"] == 1
    assert result["rows"] == []
    assert "DENSE" not in result["arms"]


def test_publication_is_charged_to_dense_and_pair(tmp_path):
    clock = Clock()
    def slow_publish(path, result):
        runner.write_summary(path, result)
        clock.now = 3601.
    result = runner.run_pair(8201, tmp_path, fixture=True, horizon=2,
                            train_episodes=2, eval_episodes=1, start=0., clock=clock,
                            publish=slow_publish)
    saved = json.loads((tmp_path / "summary.json").read_text())
    assert saved["status"] == result["status"] == "CAP_BREACH"
    assert saved["primary"]["complete"] and saved["primary"]["hover_complete"]
    assert saved["pair_elapsed_wall"] == 3601.
    assert saved["arms"]["DENSE"]["elapsed_wall"] == 3601.


def test_controls_precede_torch_import_in_clean_process():
    code = """import builtins, os
original = builtins.__import__
seen = []
def checked(name, *args, **kwargs):
    if name == 'torch' and not seen:
        assert os.environ['OMP_NUM_THREADS'] == '1'
        assert os.environ['OPENBLAS_NUM_THREADS'] == '1'
        assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
        seen.append(True)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
import experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01
import torch
assert seen and torch.get_num_threads() == torch.get_num_interop_threads() == 1
assert torch.get_default_dtype() == torch.float32
assert torch.empty(1).device.type == 'cpu'
"""
    env = dict(os.environ, OMP_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8")
    subprocess.run([sys.executable, "-c", code], check=True, env=env, timeout=30)
