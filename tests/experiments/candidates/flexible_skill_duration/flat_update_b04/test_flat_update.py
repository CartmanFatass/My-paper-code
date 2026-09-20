"""The flat-update entry: plan guard, the declared difference from the completed CF_E0005 construction,
binding, the step-count check and pairing with the completed CF_E0005 and D1280 fits.

Fake learners and fake hosts only (the real step law is in `test_flat_update_real_tiny.py`). The reference fits are produced by the
flat-entropy and matched-information entries themselves, so `reduce` reads three objects in one process.
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
    "fsd_update_helpers", Path(__file__).parents[1] / "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)
r = helpers.r

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_entropy_b03 as entropy  # noqa: E402
import run_fsd_flat_update_b04 as update  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402

fake_only = helpers.fake_only
SEEDS = sorted(update.BLOCKS)
ARMS = tuple(update.UPDATE_ARMS)
ADMISSION = {"sha": "synthetic-source", "command_sha256": "x"}
# Exact dyadic offsets from the block base, per arm and block; every panel of a fit carries them.
OFFSET = {"CF_E0005": [0., 0., 0.], "CF_M1": [.0625, -.03125, 0.], "CF_M5": [.125, .0625, .03125],
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


@pytest.fixture
def fakes(monkeypatch, fake_only):
    monkeypatch.setattr(r, "base_summary", r.base_summary)
    monkeypatch.setattr(b01, "shared", r)
    monkeypatch.setattr(r, "HMASDAgent", PanelAgent)
    monkeypatch.setattr(r, "EVAL_LANES", 32)
    for module in (matched, entropy, update):
        monkeypatch.setattr(module, "shared", r)
        monkeypatch.setattr(module, "_orig_base_summary", r.base_summary)
    monkeypatch.setattr(update, "expected_low_level_steps", lambda config: _FAKE_STEPS[0])
    monkeypatch.setattr(update, "LOW_LEVEL_OPTIMIZERS", ("discoverer_actor",))


def world_scores(arm, block_index):
    lanes = np.arange(r.EVAL_LANES, dtype=np.float64)
    return .25 + .015625 * block_index + .00390625 * (lanes % 4) + OFFSET[arm][block_index]


_TEMPLATES = {}
_FAKE_STEPS = [-1]  # what the fake learner takes; the step law is checked on the real one


def template(tmp_path, monkeypatch, name):
    if name not in _TEMPLATES:
        out = tmp_path / f"template_{name}"
        if name in matched.ARMS:
            assert matched.run_fit(name, SEEDS[0], 1, None, out, admission=ADMISSION) == 0
        elif name in entropy.ENTROPY_ARMS:
            assert entropy.run_fit(name, SEEDS[0], out, admission=ADMISSION) == 0
        else:
            assert update.run_fit(name, SEEDS[0], out, admission=ADMISSION) == 0
        _TEMPLATES[name] = json.loads((out / "summary.json").read_text())
        if name in ARMS:
            _FAKE_STEPS[:] = [_TEMPLATES[name]["optimizer_calls"]["discoverer_actor"]]
    return _TEMPLATES[name]


def placed(summary, arm, index):
    seed = SEEDS[index]
    evaluation_seed = update.BLOCKS[seed]
    summary = copy.deepcopy(summary)
    summary.update(block_seed=seed, training_seed=seed, evaluation_seed=evaluation_seed,
                   training_lane_seeds=list(range(seed, seed + r.TRAIN_LANES)),
                   evaluation_lane_seeds=list(range(evaluation_seed, evaluation_seed + r.EVAL_LANES)))
    summary["learner_config"]["seed"] = seed
    summary["evaluation_config"]["seed"] = evaluation_seed
    for panel in summary["panels"]:
        values = world_scores(arm, index)
        panel["lane_seeds"] = summary["evaluation_lane_seeds"]
        panel["native_scores_J"] = [float(v) for v in values]
        panel["returns_U"] = [float(v) * r.HORIZON / r.N_UAVS for v in values]
    summary["evaluation"] = summary["panels"][-1]
    return summary


def supplied(tmp_path, monkeypatch):
    new = [placed(template(tmp_path, monkeypatch, arm), arm, i) for arm in ARMS for i in range(3)]
    references = [placed(template(tmp_path, monkeypatch, arm), arm, i)
                  for arm in ("CF_E0005", "D1280") for i in range(3)]
    return new, references


def test_plan_guard_admits_exactly_the_six_planned_fits():
    for arm in ARMS:
        for seed in SEEDS:
            update.plan_guard(arm, seed)
    for arm, seed in (("CF", SEEDS[0]), ("CF_E0005", SEEDS[0]), ("CF_M1", 773103), ("CF_M5", 772603)):
        with pytest.raises(SystemExit):
            update.plan_guard(arm, seed)


def test_real_configs_are_cf_e0005_with_the_declared_package_changed():
    envs = [SimpleNamespace(state_dim=119, obs_dim=104) for _ in range(16)]
    snapshot = production_shared.config_snapshot
    entropy.bind()
    entropy.CURRENT.update(entropy_arm="CF_E0005")
    reference = snapshot(b01.make_config("CF", envs, SEEDS[0]))
    entropy.CURRENT.update(entropy_arm=None)
    update.bind()
    plain = b01.make_config("CF", envs, SEEDS[0])
    assert snapshot(plain) == reference and not hasattr(plain, "sequence_batch_size")
    base = reference["lr_discoverer_actor"] / entropy.SELECTED_MULTIPLIER
    for arm, multiplier in update.UPDATE_ARMS.items():
        update.CURRENT.update(update_arm=arm)
        config = b01.make_config("CF", envs, SEEDS[0])
        new = snapshot(config)
        assert {k for k in reference if reference[k] != new[k]} == set(matched.TUNED_FIELDS)
        assert new["lr_discoverer_actor"] == new["lr_discoverer_critic"] == pytest.approx(base * multiplier)
        assert config.sequence_batch_size == 1200
        assert update.expected_low_level_steps(new) == 15 * 4 * 45


def test_fit_runs_the_frozen_flat_loop_under_this_identity(tmp_path, monkeypatch, fakes):
    summary = template(tmp_path, monkeypatch, "CF_M5")
    assert summary["status"] == "complete" and summary["object_id"] == update.OBJECT_ID
    assert summary["flat_update_object"] == update.OBJECT_ID and summary["admission"] == ADMISSION
    assert summary["factorial_arm"] == "CF" and summary["update_arm"] == "CF_M5"
    assert summary["lr_multiplier"] == 5. and summary["sequence_batch_size"] == 1200
    assert summary["learner_config"]["lambda_l"] == .0005
    assert update.CURRENT == {"update_arm": None, "admission": None}
    assert set(update.fit_endpoint(summary)) == set(range(5, 50, 5))
    monkeypatch.setattr(update, "expected_low_level_steps", lambda config: 2700)
    with pytest.raises(ValueError, match="low-level steps"):  # the default minibatch would not pass
        update.fit_endpoint(summary)
    with pytest.raises(ValueError):  # the flat-entropy reader does not take this object's fits
        entropy.fit_endpoint(summary)
    with pytest.raises(ValueError):  # nor this one a completed reference fit
        update.fit_endpoint(template(tmp_path, monkeypatch, "CF_E0005"))


def test_reduce_pairs_new_fits_with_the_completed_flat_and_d1280_fits(tmp_path, monkeypatch, fakes):
    new, references = supplied(tmp_path, monkeypatch)
    paths = {"new": [], "ref": []}
    for kind, items in (("new", new), ("ref", references)):
        for i, summary in enumerate(items):
            path = tmp_path / f"{kind}_{i}.json"
            path.write_text(json.dumps(summary), encoding="utf-8")
            paths[kind].append(str(path))
    out = tmp_path / "reduce"
    assert update.main(["reduce", "--summaries", *paths["new"], "--references", *paths["ref"],
                        "--output-root", str(out)]) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and not result["invalid_inputs"]
    for block in result["blocks"]:
        assert set(block["arms"]) == {"CF_M1", "CF_M5", "CF_E0005", "D1280"}
        assert block["arms"]["CF_E0005"]["object_id"] == entropy.OBJECT_ID
        assert block["arms"]["D1280"]["object_id"] == matched.OBJECT_ID
        assert "mean_policy_loss" in block["arms"]["CF_M1"]["diagnostics"]
    for arm in ARMS:
        view = result["arms"][arm]
        for name in ("J45", "late"):  # every panel carries the same offset, so both readings agree
            assert [p[f"new_minus_flat_{name}"] for p in view["pairs"]] == OFFSET[arm]
            assert [p[f"D1280_minus_new_{name}"] for p in view["pairs"]] == [
                d - n for d, n in zip(OFFSET["D1280"], OFFSET[arm])]
        assert [p["late_minus_early_window"] for p in view["pairs"]] == [0., 0., 0.]
        assert view["new_minus_flat_late"]["mean"] == pytest.approx(float(np.mean(OFFSET[arm])))
    assert result["arms"]["CF_M1"]["blocks_above_flat_in_late_window"] == 1
    assert result["arms"]["CF_M5"]["blocks_above_flat_in_late_window"] == 3


def test_missing_invalid_and_duplicate_inputs(tmp_path, monkeypatch, fakes):
    new, references = supplied(tmp_path, monkeypatch)
    result = update.reduce_fits(new[1:], references)  # CF_M1 on block 0 is missing
    assert result["status"] == "incomplete" and result["arms"]["CF_M5"]["status"] == "complete"
    assert result["arms"]["CF_M1"]["pairs"][0]["missing_operands"] == ["CF_M1"]
    assert result["blocks"][0]["missing_or_invalid_arms"] == {"CF_M1": "not supplied"}

    broken = copy.deepcopy(new)
    broken[1]["learner_config"]["lambda_e"] = .5  # an unplanned difference from the CF_E0005 fit
    result = update.reduce_fits(broken, references)
    assert result["arms"]["CF_M1"]["pairs"][1]["failure"] == "unplanned difference from the CF_E0005 reference"

    other_flat = copy.deepcopy(references)
    other_flat[0]["entropy_arm"] = "CF_E005"  # not the declared flat reference
    result = update.reduce_fits(new, other_flat)
    assert result["arms"]["CF_M1"]["pairs"][0]["missing_operands"] == ["CF_E0005"]
    assert result["invalid_inputs"]

    with pytest.raises(ValueError, match="duplicate"):
        update.reduce_fits(new + [copy.deepcopy(new[0])], references)
