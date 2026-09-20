from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.skill_information_refresh.c01.host import CrossingHost, Worlds
from experiments.candidates.skill_information_refresh.c01.learner import build_scheduler
from experiments.candidates.skill_information_refresh.c03.study import CHECKPOINTS, collect, paired
from experiments.candidates.skill_information_refresh.c04.study import Config, StageRule, run_study


@pytest.mark.parametrize("name,expected", [("ACTIVE_FIRST", [True, True, False]),
    ("APPROACH_FIRST", [True, False, False])])
def test_stage_only_truth_table_and_no_other_information(name, expected):
    model = StageRule(name)
    x = torch.arange(72, dtype=torch.float32).reshape(3, 24)
    x[:, :3] = torch.eye(3)
    assert (model(x)[0] >= 0).tolist() == expected
    x[:, 3:] = -1000 * x[:, 3:]
    assert (model(x)[0] >= 0).tolist() == expected
    assert sum(p.numel() for p in model.parameters()) == 0
    assert torch.equal(model(x)[1], torch.zeros(3))


@pytest.mark.parametrize("name", ["ACTIVE_FIRST", "APPROACH_FIRST"])
def test_stage_adapter_matches_direct_rule_and_channel_quota(name):
    torch.set_num_threads(1)
    worlds = Worlds.make(43, 0, range(4), 96)
    rows, trace = collect(CrossingHost(worlds), model=StageRule(name), retain_trace=True)
    independent = CrossingHost(worlds)
    sent = []
    while independent.t < independent.horizon:
        view = independent.view()
        expected = view.own[:, 0] < 2 if name == "ACTIVE_FIRST" else view.own[:, 0] == 0
        sent.append(view.available & (expected | view.forced))
        independent.step(expected)
    assert np.array_equal(trace["sent"], np.stack(sent, axis=1))
    for old, new in zip(independent.rows(), rows):
        assert old == {key: new[key] for key in old}
    assert all(r["packets"] == 24 and r["bytes"] == 192 and r["release_overrides"] == 0 for r in rows)
    frames = trace["sent"].reshape(4, 12, 8)
    assert (frames[:, :, ::2].sum(2) == 1).all() and (frames[:, :, 1::2].sum(2) == 1).all()


def make_checkpoints(root):
    specs = []
    for spec in CHECKPOINTS:
        path = root / spec.path
        path.parent.mkdir(parents=True, exist_ok=True)
        config = dict(seed=spec.seed, horizon=96, train_episodes=4096,
            initial_episodes=64, selection_episodes=256, final_episodes=256, batch=32, epochs=4)
        # Synthetic untrained fixture only; production uses the bound archived inputs.
        torch.save(dict(model=build_scheduler(spec.seed).state_dict(),
            launch_sha=spec.source_sha, config=config), path)
        specs.append(replace(spec, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return tuple(specs)


def test_complete_fixture_selection_primary_and_zero_learning(tmp_path):
    torch.set_num_threads(1)
    specs = make_checkpoints(tmp_path)
    out = tmp_path / "result"
    config = Config(seed=73, horizon=48, selection_episodes=2, final_episodes=3, batch=2)
    result = run_study(out, "a" * 40, tmp_path, config, specs)
    assert result["status"] == "COMPLETE"
    assert result["counts"]["started_fits"] == result["counts"]["optimizer_steps"] == 0
    assert result["counts"]["train_transitions"] == result["counts"]["evaluation_optimizer_steps"] == 0
    assert result["counts"]["selection_episodes"] == 24 and result["counts"]["eval_episodes"] == 24
    assert result["counts"]["selection_transitions"] == result["counts"]["eval_transitions"] == 24 * 48
    assert len(result["selection"]) == 12 and len(result["final"]) == 8
    candidates = [result["selected_age"]] + [r for r in result["selection"] if r["arm"] != "AGE_CHANGE"]
    selected = sorted(candidates, key=lambda r: (-r["reading"]["service"], r["arm"]))[0]["arm"]
    assert result["selected_simple_reference"] == selected
    assert (out / "updates.jsonl").read_text() == ""
    assert all(v["displacement_from_loaded"] == 0 for v in result["frozen_parameters"].values())
    assert all(v == dict(parameters=0, training_updates=0) for v in result["fixed_stage_rules"].values())
    rows = [json.loads(line) for line in (out / "episodes.jsonl").read_text().splitlines()]
    assert len(rows) == 48
    baseline = [r for r in rows if r["phase"] == "eval" and r["arm"] == selected]
    for name, comparison in result["versus_selected_simple"].items():
        actual = [r for r in rows if r["phase"] == "eval" and r["arm"] == name]
        assert comparison == paired(actual, baseline)
        assert np.array_equal(np.load(out / f"final_trace_{name}.npz")["world_ids"], np.arange(3))
    with pytest.raises(FileExistsError):
        run_study(out, "a" * 40, tmp_path, config, specs)


def test_cli_refuses_without_admission(tmp_path):
    root = Path(__file__).resolve().parents[5]
    out = tmp_path / "unadmitted"
    result = subprocess.run([sys.executable, str(root / "scripts/run_sir_c04.py"),
        "--out", str(out), "--launch-sha", "a" * 40], cwd=root,
        capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "missing HMASD admission" in result.stderr
    assert not out.exists()
