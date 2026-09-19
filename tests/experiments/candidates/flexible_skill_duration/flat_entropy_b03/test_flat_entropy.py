"""The flat-entropy entry: plan guard, the single-field difference from the completed CF construction,
binding, pairing with the completed CF and D1280 fits, and missing, invalid and duplicate inputs.

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
    "fsd_entropy_helpers", Path(__file__).parents[1] / "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)
r = helpers.r

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_entropy_b03 as entropy  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402

fake_only = helpers.fake_only
SEEDS = sorted(entropy.BLOCKS)
ARMS = tuple(entropy.ENTROPY_ARMS)
ADMISSION = {"sha": "synthetic-source", "command_sha256": "x"}
SELECTION = {"object_id": matched.OBJECT_ID, "card": matched.CARD, "status": "complete",
             "selected_lr_multiplier": entropy.SELECTED_MULTIPLIER}
# Exact dyadic J45 offsets from the block base, per arm and block.
OFFSET = {"CF": [0., 0., 0.], "CF_E005": [.0625, .125, -.03125], "CF_E0005": [.03125, 0., .015625],
          "D1280": [.25, .1875, .125]}


class PanelAgent(helpers.Agent):
    """The fake learner moves the coordinator optimizer only where the arm has skills."""

    def update(self, **kwargs):
        if self.config.n_z == 1:
            saved = {name: getattr(self, name + "_optimizer").step for name in b01.FLAT_ONLY_ZERO}
            for name in saved:
                getattr(self, name + "_optimizer").step = lambda: None
            try:
                return super().update(**kwargs)
            finally:
                for name, step in saved.items():
                    getattr(self, name + "_optimizer").step = step
        losses = super().update(**kwargs)
        self.coordinator_optimizer.step()
        return losses


@pytest.fixture(autouse=True)
def bind_fake_shared(monkeypatch, fake_only):
    monkeypatch.setattr(r, "base_summary", r.base_summary)
    monkeypatch.setattr(b01, "shared", r)
    monkeypatch.setattr(r, "HMASDAgent", PanelAgent)
    monkeypatch.setattr(r, "EVAL_LANES", 32)
    for module in (matched, entropy):
        monkeypatch.setattr(module, "shared", r)
        monkeypatch.setattr(module, "_orig_base_summary", r.base_summary)


def world_scores(arm, block_index, rollout):
    lanes = np.arange(r.EVAL_LANES, dtype=np.float64)
    worlds = .25 + .015625 * block_index + .00390625 * (lanes % 4)
    return worlds + OFFSET[arm][block_index] * (rollout // 5) / 9 if rollout < 45 else worlds + OFFSET[arm][block_index]


_TEMPLATES = {}


def template(tmp_path, name):
    if name not in _TEMPLATES:
        out = tmp_path / f"template_{name}"
        if name in matched.ARMS:
            assert matched.run_fit(name, SEEDS[0], 1, None, out, selection=SELECTION, admission=ADMISSION) == 0
        else:
            assert entropy.run_fit(name, SEEDS[0], out, admission=ADMISSION) == 0
        _TEMPLATES[name] = json.loads((out / "summary.json").read_text())
    return _TEMPLATES[name]


def placed(summary, arm, index):
    seed = SEEDS[index]
    evaluation_seed = entropy.BLOCKS[seed]
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
    new = [placed(template(tmp_path, arm), arm, i) for arm in ARMS for i in range(3)]
    references = [placed(template(tmp_path, arm), arm, i) for arm in ("CF", "D1280") for i in range(3)]
    return new, references


def test_plan_guard_admits_exactly_the_six_planned_fits():
    for arm in ARMS:
        for seed in SEEDS:
            entropy.plan_guard(arm, seed)
    for arm, seed in (("CF", SEEDS[0]), ("D1280", SEEDS[0]), ("CF_E005", 773103), ("CF_E0005", 772603)):
        with pytest.raises(SystemExit):
            entropy.plan_guard(arm, seed)
    assert 0. not in entropy.ENTROPY_ARMS.values()  # the learner records no entropy at coefficient zero


def test_real_configs_are_the_selected_cf_construction_with_one_field_changed():
    envs = [SimpleNamespace(state_dim=119, obs_dim=104) for _ in range(16)]
    snapshot = production_shared.config_snapshot
    matched.bind()
    matched.CURRENT.update(lr_multiplier=entropy.SELECTED_MULTIPLIER)
    reference = snapshot(b01.make_config("CF", envs, SEEDS[0]))
    assert reference[entropy.ENTROPY_FIELD] == entropy.REFERENCE_ENTROPY
    assert not reference.get("use_entropy_targets") and not reference.get("use_entropy_annealing")
    entropy.bind()
    assert snapshot(b01.make_config("CF", envs, SEEDS[0])) == reference  # no arm: the reference itself
    for arm, value in entropy.ENTROPY_ARMS.items():
        entropy.CURRENT.update(entropy_arm=arm)
        new = snapshot(b01.make_config("CF", envs, SEEDS[0]))
        assert {k for k in reference if reference[k] != new[k]} == {entropy.ENTROPY_FIELD}
        assert new[entropy.ENTROPY_FIELD] == value


def test_the_committed_selection_is_the_multiplier_this_entry_hardcodes():
    selection = json.loads((ROOT / "runs/flexible_skill_duration/b01_s0_selection/SELECTION.json").read_text())
    assert matched.selected_multiplier(selection) == entropy.SELECTED_MULTIPLIER


def test_fit_runs_the_frozen_flat_loop_under_this_identity(tmp_path):
    summary = template(tmp_path, "CF_E005")
    assert summary["status"] == "complete" and summary["object_id"] == entropy.OBJECT_ID
    assert summary["flat_entropy_object"] == entropy.OBJECT_ID and summary["admission"] == ADMISSION
    assert summary["factorial_arm"] == "CF" and summary["entropy_arm"] == "CF_E005"
    assert summary["entropy_coefficient"] == .005 and summary["lr_multiplier"] == .5
    assert summary["learner_config"]["lambda_l"] == .005 and summary["evaluation_config"]["lambda_l"] == .005
    assert summary["optimizer_calls"]["coordinator"] == 0
    assert set(entropy.fit_endpoint(summary)) == set(range(5, 50, 5))
    assert entropy.CURRENT == {"entropy_arm": None, "admission": None}
    with pytest.raises(ValueError):  # the matched-information reader does not take this object's fits
        matched.fit_endpoint(summary)
    with pytest.raises(ValueError):  # nor this one a completed reference fit
        entropy.fit_endpoint(template(tmp_path, "CF"))
    relabelled = dict(copy.deepcopy(summary), entropy_arm="CF_E0005")
    with pytest.raises(ValueError):  # the recorded coefficient must be the arm's
        entropy.fit_endpoint(relabelled)


def test_reduce_pairs_new_fits_with_the_completed_cf_and_d1280_fits(tmp_path):
    new, references = supplied(tmp_path)
    paths = {"new": [], "ref": []}
    for kind, items in (("new", new), ("ref", references)):
        for i, summary in enumerate(items):
            path = tmp_path / f"{kind}_{i}.json"
            path.write_text(json.dumps(summary), encoding="utf-8")
            paths[kind].append(str(path))
    out = tmp_path / "reduce"
    assert entropy.main(["reduce", "--summaries", *paths["new"], "--references", *paths["ref"],
                         "--output-root", str(out)]) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and not result["invalid_inputs"]
    for block in result["blocks"]:
        assert set(block["arms"]) == {"CF_E005", "CF_E0005", "CF", "D1280"}
        assert block["arms"]["CF"]["object_id"] == matched.OBJECT_ID
        assert block["arms"]["CF_E005"]["object_id"] == entropy.OBJECT_ID
        assert set(block["arms"]["CF_E005"]["diagnostics"]) == {"1", *map(str, range(5, 50, 5))}
    for arm in ARMS:
        view = result["arms"][arm]
        assert [p["new_minus_CF_J45"] for p in view["pairs"]] == OFFSET[arm]
        assert [p["D1280_minus_new_J45"] for p in view["pairs"]] == [
            d - n for d, n in zip(OFFSET["D1280"], OFFSET[arm])]
        assert [p["D1280_minus_CF_J45"] for p in view["pairs"]] == OFFSET["D1280"]
        assert view["new_minus_CF_J45"]["mean"] == pytest.approx(float(np.mean(OFFSET[arm])))
        assert view["new_minus_CF_J45"]["t_multiplier"] == b01.T975[2]
    first, second = result["arms"]["CF_E005"], result["arms"]["CF_E0005"]
    assert (first["fits_above_CF_at_J45"], second["fits_above_CF_at_J45"]) == (2, 2)
    assert (first["fits_with_J45_at_least_J5"], second["fits_with_J45_at_least_J5"]) == (2, 3)
    assert (first["fits_with_smaller_gap_than_CF"], second["fits_with_smaller_gap_than_CF"]) == (2, 2)


def test_missing_invalid_and_duplicate_inputs(tmp_path):
    new, references = supplied(tmp_path)
    result = entropy.reduce_fits(new[1:], references)  # CF_E005 on block 0 is missing
    assert result["status"] == "incomplete" and result["arms"]["CF_E0005"]["status"] == "complete"
    assert result["arms"]["CF_E005"]["pairs"][0] == {
        "training_seed": SEEDS[0], "status": "incomplete", "missing_operands": ["CF_E005"]}
    assert result["blocks"][0]["missing_or_invalid_arms"] == {"CF_E005": "not supplied"}
    assert result["arms"]["CF_E005"]["new_minus_CF_J45"]["available_blocks"] == 2

    broken = copy.deepcopy(new)
    broken[1]["learner_config"]["lr_discoverer_actor"] *= 2  # an unplanned difference from the CF fit
    result = entropy.reduce_fits(broken, references)
    assert result["arms"]["CF_E005"]["pairs"][1]["failure"] == "unplanned difference from the CF reference"
    assert result["status"] == "incomplete"

    unselected = copy.deepcopy(references)
    unselected[0]["lr_multiplier"] = 1.0  # not the selected CF construction
    result = entropy.reduce_fits(new, unselected)
    assert "selected construction" in result["invalid_inputs"][f"{SEEDS[0]}:CF"]
    assert result["arms"]["CF_E005"]["pairs"][0]["missing_operands"] == ["CF"]

    incomplete = copy.deepcopy(new)
    incomplete[0]["status"] = "failed"
    result = entropy.reduce_fits(incomplete, references)
    assert f"{SEEDS[0]}:CF_E005" in result["invalid_inputs"] and result["status"] == "incomplete"

    with pytest.raises(ValueError, match="duplicate"):
        entropy.reduce_fits(new + [copy.deepcopy(new[0])], references)
