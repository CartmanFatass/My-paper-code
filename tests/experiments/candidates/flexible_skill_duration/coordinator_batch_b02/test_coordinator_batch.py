"""The coordinator-batch entry: plan guard, binding, pairing with the completed reference fits, a
missing pair, and the D1280 rerun comparison.

Fake learners and fake hosts only. A fit runs the frozen collector loop for 45 rollouts and nine
panels; the reference fits are produced by the matched-information entry itself, so `reduce` is shown
to read two objects' summaries in one process.
"""
import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

_SPEC = importlib.util.spec_from_file_location(
    "fsd_batch_helpers", Path(__file__).parents[1] / "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)
r = helpers.r

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_coordinator_batch_b02 as batch  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402

fake_only = helpers.fake_only
SEEDS = sorted(batch.BLOCKS)
M_LEVELS = [.0625, -.03125, .015625, .09375, 0.]  # exact dyadic M_b
ADMISSION = {"sha": "synthetic-source", "command_sha256": "x"}


class Agent(helpers.Agent):
    def update(self, **kwargs):
        losses = super().update(**kwargs)
        self.coordinator_optimizer.step()
        return losses


@pytest.fixture(autouse=True)
def bind_fake_shared(monkeypatch, fake_only):
    monkeypatch.setattr(r, "base_summary", r.base_summary)
    monkeypatch.setattr(b01, "shared", r)
    monkeypatch.setattr(r, "HMASDAgent", Agent)
    monkeypatch.setattr(r, "EVAL_LANES", 32)
    for module in (matched, batch):
        monkeypatch.setattr(module, "shared", r)
        monkeypatch.setattr(module, "_orig_base_summary", r.base_summary)


def world_scores(arm, block_index, rollout):
    lanes = np.arange(r.EVAL_LANES, dtype=np.float64)
    worlds = .25 + .015625 * block_index + .0078125 * (rollout // 5) + .00390625 * (lanes % 4)
    if arm == "D1280":
        worlds = worlds + M_LEVELS[block_index] + .001953125 * (rollout // 5 - 9)
    return worlds


_TEMPLATES = {}


def template(tmp_path, name):
    if name not in _TEMPLATES:
        out = tmp_path / f"template_{name}"
        if name == "reference":
            assert matched.run_fit("D1280", SEEDS[0], 1, None, out, admission=ADMISSION) == 0
        else:
            assert batch.run_fit(name, SEEDS[0], out, admission=ADMISSION) == 0
        _TEMPLATES[name] = json.loads((out / "summary.json").read_text())
    return _TEMPLATES[name]


def placed(summary, arm, index):
    seed = SEEDS[index]
    evaluation_seed = batch.BLOCKS[seed]
    summary = copy.deepcopy(summary)
    summary.update(block_seed=seed, training_seed=seed, evaluation_seed=evaluation_seed,
                   training_lane_seeds=list(range(seed, seed + r.TRAIN_LANES)),
                   evaluation_lane_seeds=list(range(evaluation_seed, evaluation_seed + r.EVAL_LANES)))
    summary["learner_config"]["seed"] = seed
    summary["evaluation_config"]["seed"] = evaluation_seed
    for panel in summary["panels"]:
        values = world_scores(arm, index, panel["panel_rollouts"])
        panel["lane_seeds"] = summary["evaluation_lane_seeds"]
        panel["native_scores_J"] = [float(v) for v in values]
        panel["returns_U"] = [float(v) * r.HORIZON / r.N_UAVS for v in values]
    summary["evaluation"] = summary["panels"][-1]
    return summary


def supplied(tmp_path):
    new = [placed(template(tmp_path, "D128"), "D128", i) for i in range(5)]
    new.append(placed(template(tmp_path, "D1280"), "D1280", 0))
    references = [placed(template(tmp_path, "reference"), "D1280", i) for i in range(5)]
    return new, references


def test_plan_guard_admits_exactly_the_six_planned_fits():
    for seed in SEEDS:
        batch.plan_guard("D128", seed)
    batch.plan_guard("D1280", batch.RERUN_BLOCK)
    for arm, seed in (("D1280", SEEDS[1]), ("D128", 772603), ("CF", SEEDS[0])):
        with pytest.raises(SystemExit):
            batch.plan_guard(arm, seed)


def test_real_configs_differ_in_the_batch_size_only_and_d1280_is_the_reference_construction():
    envs = [SimpleNamespace(state_dim=119, obs_dim=104) for _ in range(16)]
    snapshot = production_shared.config_snapshot
    matched.bind()
    reference = snapshot(b01.make_config("D1280", envs, SEEDS[0]))
    batch.bind()
    large = snapshot(b01.make_config("D1280", envs, SEEDS[0]))
    small = snapshot(b01.make_config("D128", envs, SEEDS[0]))
    assert large == reference and large["coordinator_batch_size"] == 1280
    assert {k for k in large if large[k] != small[k]} == {"coordinator_batch_size"}
    assert small["coordinator_batch_size"] == 128


def test_fit_runs_the_frozen_loop_under_this_identity(tmp_path):
    summary = template(tmp_path, "D128")
    assert summary["status"] == "complete" and summary["object_id"] == batch.OBJECT_ID
    assert summary["coordinator_batch_object"] == batch.OBJECT_ID and summary["admission"] == ADMISSION
    assert summary["rollouts"] == 45 and summary["panel_rollouts"] == list(range(5, 50, 5))
    assert summary["coordinator_batch_size"] == 128 and summary["learner_config"]["coordinator_batch_size"] == 128
    assert set(batch.fit_endpoint(summary)) == set(range(5, 50, 5))
    with pytest.raises(ValueError):  # the matched-information reader does not take this object's fits
        matched.fit_endpoint(summary)
    with pytest.raises(ValueError):  # nor this one a completed reference fit
        batch.fit_endpoint(template(tmp_path, "reference"))


def test_reduce_pairs_new_fits_with_the_completed_reference_fits(tmp_path):
    new, references = supplied(tmp_path)
    paths = {"new": [], "ref": []}
    for kind, items in (("new", new), ("ref", references)):
        for i, summary in enumerate(items):
            path = tmp_path / f"{kind}_{i}.json"
            path.write_text(json.dumps(summary), encoding="utf-8")
            paths[kind].append(str(path))
    out = tmp_path / "reduce"
    assert batch.main(["reduce", "--summaries", *paths["new"], "--references", *paths["ref"],
                       "--output-root", str(out)]) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and result["object_id"] == batch.OBJECT_ID
    assert [b["pair"]["M_45"] for b in result["blocks"]] == M_LEVELS
    for index, block in enumerate(result["blocks"]):
        assert set(block["arms"]) == {"D1280", "D128"} and not block["missing_or_invalid_arms"]
        assert block["arms"]["D1280"]["object_id"] == matched.OBJECT_ID
        assert block["arms"]["D128"]["object_id"] == batch.OBJECT_ID
        expected = world_scores("D1280", index, 45) - world_scores("D128", index, 45)
        assert block["pair"]["ordered_world_differences"] == expected.tolist()
    primary = result["primary"]
    mean, sd = float(np.mean(M_LEVELS)), float(np.std(M_LEVELS, ddof=1))
    assert primary["mean"] == mean and primary["sample_sd"] == sd and primary["t_multiplier"] == 2.7764
    half = 2.7764 * sd / 5 ** .5
    assert primary["working_model_95pct_interval"] == pytest.approx([mean - half, mean + half])
    assert (primary["positive_blocks"], primary["negative_blocks"], primary["zero_blocks"]) == (3, 1, 1)
    assert set(result["curves"]) == {str(v) for v in range(5, 45, 5)}
    rerun = result["d1280_rerun"]
    assert rerun["status"] == "complete" and rerun["panel_means_reproduce_exactly"]
    assert rerun["world_scores_reproduce_exactly"] and rerun["max_abs_world_score_difference"] == 0.0


def test_a_rerun_that_differs_is_measured_and_never_replaces_the_reference(tmp_path):
    new, references = supplied(tmp_path)
    for panel in new[-1]["panels"]:
        values = [v + .0078125 for v in panel["native_scores_J"]]
        panel["native_scores_J"] = values
        panel["returns_U"] = [v * r.HORIZON / r.N_UAVS for v in values]
    result = batch.reduce_pairs(new, references)
    rerun = result["d1280_rerun"]
    assert result["status"] == "complete" and not rerun["panel_means_reproduce_exactly"]
    assert rerun["rerun_minus_reference_J45"] == pytest.approx(.0078125)
    assert rerun["max_abs_world_score_difference"] == pytest.approx(.0078125)
    assert [b["pair"]["M_45"] for b in result["blocks"]] == M_LEVELS  # the reference fit stands


def test_missing_invalid_and_duplicate_inputs(tmp_path):
    new, references = supplied(tmp_path)
    result = batch.reduce_pairs(new[1:], references)  # block 0 has no D128 fit
    assert result["status"] == "incomplete" and result["primary"]["available_blocks"] == 4
    assert result["blocks"][0]["pair"] == {"status": "incomplete", "missing_operands": ["D128"]}
    assert result["blocks"][0]["missing_or_invalid_arms"] == {"D128": "not supplied"}
    assert result["primary"]["t_multiplier"] == b01.T975[3]

    result = batch.reduce_pairs(new[:-1], references)  # no rerun: pairs complete, object incomplete
    assert result["primary"]["status"] == "complete" and result["status"] == "incomplete"
    assert result["d1280_rerun"] == {"status": "incomplete", "failure": "not supplied"}

    broken = copy.deepcopy(references)
    broken[2]["learner_config"]["lr_discoverer_actor"] *= 2  # an unplanned difference inside a pair
    result = batch.reduce_pairs(new, broken)
    assert result["blocks"][2]["pair"]["status"] == "incomplete" and result["status"] == "incomplete"

    wrong = copy.deepcopy(references)
    wrong[1]["factorial_arm"] = "CF"  # only completed D1280 fits are a reference
    result = batch.reduce_pairs(new, wrong)
    assert "D1280" in result["blocks"][1]["missing_or_invalid_arms"]

    with pytest.raises(ValueError):
        batch.reduce_pairs(new + [new[0]], references)
