"""The stage-1 readout: card section 5 quantities and the section 6 reading rule, verbatim.

Synthetic complete fits with dyadic world scores (every J45, block difference and conditional SD
below is exact in binary), plus direct checks of the label and interval boundaries, zero variance,
missing pairs and an invalid selection.
"""
import copy
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

_SPEC = importlib.util.spec_from_file_location(
    "fsd_matched_helpers", Path(__file__).parents[1] / "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)
r = helpers.r

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402

fake_only = helpers.fake_only
SELECTED = 0.5
SELECTION = {"object_id": matched.OBJECT_ID, "card": matched.CARD, "status": "complete",
             "selected_lr_multiplier": SELECTED, "stage": 0}
SEEDS = sorted(matched.STAGE1_BLOCKS)
# Exact dyadic per-block differences G_b; the last is exactly zero (a sign count, not a gate).
G_LEVELS = [.0625, .03125, -.015625, .09375, 0.]
JITTER = .0009765625  # +/- per world, mean zero over the even lane count
CURVE_STEP = .001953125  # per five rollouts, so the curves are not flat


class Agent(helpers.Agent):
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
    monkeypatch.setattr(r, "HMASDAgent", Agent)
    monkeypatch.setattr(r, "EVAL_LANES", 32)  # the card's 32 evaluation worlds
    monkeypatch.setattr(matched, "shared", r)
    monkeypatch.setattr(matched, "_orig_base_summary", r.base_summary)


def world_scores(arm, block_index, rollout):
    """Exactly representable panel scores; G_45 is G_LEVELS[b] and the curves are not flat."""
    lanes = np.arange(r.EVAL_LANES, dtype=np.float64)
    worlds = .25 + .015625 * block_index + .0078125 * (rollout // 5) + .00390625 * (lanes % 4)
    if arm == "D1280":
        worlds = (worlds + G_LEVELS[block_index] + CURVE_STEP * (rollout // 5 - 9)
                  + JITTER * np.where(lanes % 2 == 0, 1., -1.))
    return worlds


_TEMPLATES = {}


def fit_template(tmp_path, arm):
    """One real run of the frozen loop per arm, reused: the fake fit is deterministic here."""
    if arm not in _TEMPLATES:
        out = tmp_path / f"template_{arm}"
        assert matched.run_fit(arm, SEEDS[0], 1, None, out, selection=SELECTION,
                               admission={"sha": "synthetic-source", "command_sha256": "x"}) == 0
        _TEMPLATES[arm] = json.loads((out / "summary.json").read_text())
    return _TEMPLATES[arm]


def supplied_summaries(tmp_path):
    """One complete stage-1 fit per arm and block, with designed per-world panel scores."""
    templates = {arm: fit_template(tmp_path, arm) for arm in matched.ARMS}
    summaries = []
    for index, seed in enumerate(SEEDS):
        evaluation_seed = matched.STAGE1_BLOCKS[seed]
        for arm, template in templates.items():
            summary = copy.deepcopy(template)
            summary.update(block_seed=seed, training_seed=seed, evaluation_seed=evaluation_seed,
                           training_lane_seeds=list(range(seed, seed + r.TRAIN_LANES)),
                           evaluation_lane_seeds=list(range(evaluation_seed,
                                                            evaluation_seed + r.EVAL_LANES)))
            summary["learner_config"]["seed"] = seed
            summary["evaluation_config"]["seed"] = evaluation_seed
            for panel in summary["panels"]:
                rollout = panel["panel_rollouts"]
                values = world_scores(arm, index, rollout)
                panel["lane_seeds"] = summary["evaluation_lane_seeds"]
                panel["native_scores_J"] = [float(v) for v in values]
                panel["returns_U"] = [float(v) * r.HORIZON / r.N_UAVS for v in values]
            summary["evaluation"] = summary["panels"][-1]
            summaries.append(summary)
    return summaries


def write(tmp_path, summaries, selection=SELECTION):
    paths = []
    for i, summary in enumerate(summaries):
        path = tmp_path / f"fit_{i}.json"
        path.write_text(json.dumps(summary), encoding="utf-8")
        paths.append(str(path))
    selection_path = tmp_path / "SELECTION.json"
    selection_path.write_text(json.dumps(selection), encoding="utf-8")
    return paths, str(selection_path)


def test_reduce_reads_the_five_blocks_end_to_end(tmp_path):
    summaries = supplied_summaries(tmp_path)
    paths, selection_path = write(tmp_path, summaries)
    out = tmp_path / "reduce"
    assert matched.main(["reduce", "--summaries", *paths, "--selection", selection_path,
                         "--output-root", str(out)]) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and result["object_id"] == matched.OBJECT_ID
    assert result["stage"] == 1 and result["selected_lr_multiplier"] == SELECTED
    assert result["stage0_selection"] == SELECTION
    assert "J45(D1280, b) - J45(CF, b)" in result["quantity"]

    # The five G_b, the ten J45 and each block's 32 ordered world differences with SD and SE.
    assert len(result["blocks"]) == 5
    for index, block in enumerate(result["blocks"]):
        seed = SEEDS[index]
        assert block["training_seed"] == seed
        assert block["evaluation_seed"] == matched.STAGE1_BLOCKS[seed]
        assert set(block["arms"]) == {"CF", "D1280"} and not block["missing_or_invalid_arms"]
        pair = block["pair"]
        assert pair["status"] == "complete" and pair["G_45"] == G_LEVELS[index]
        expected = world_scores("D1280", index, 45) - world_scores("CF", index, 45)
        assert len(pair["ordered_world_differences"]) == 32
        np.testing.assert_allclose(pair["ordered_world_differences"], expected, rtol=0, atol=1e-15)
        assert pair["conditional_world_sd"] == pytest.approx(expected.std(ddof=1))
        assert pair["conditional_world_se"] == pytest.approx(expected.std(ddof=1) / math.sqrt(32))
        assert pair["J45"]["D1280"] - pair["J45"]["CF"] == pytest.approx(G_LEVELS[index])
        assert pair["G_by_rollout"]["45"] == pytest.approx(G_LEVELS[index])
        assert pair["G_by_rollout"]["5"] == pytest.approx(G_LEVELS[index] + CURVE_STEP * (1 - 9))
        assert block["arms"]["CF"]["lr_multiplier"] == SELECTED
        assert block["arms"]["D1280"]["lr_multiplier"] == 1.
        assert block["arms"]["CF"]["counts"]["update_stages"] == 45

    primary = result["primary"]
    sd = float(np.std(G_LEVELS, ddof=1))
    assert primary["name"] == "G_45" and primary["mei_J"] == .05 and primary["status"] == "complete"
    assert primary["available_blocks"] == primary["planned_blocks"] == 5
    assert primary["mean"] == pytest.approx(np.mean(G_LEVELS))
    assert primary["sample_sd"] == pytest.approx(sd)
    assert primary["se"] == pytest.approx(sd / math.sqrt(5))
    assert primary["t_multiplier"] == matched.T975_DF4 == 2.7764
    assert primary["working_model_95pct_interval"] == pytest.approx(
        [np.mean(G_LEVELS) - 2.7764 * sd / math.sqrt(5), np.mean(G_LEVELS) + 2.7764 * sd / math.sqrt(5)])
    assert primary["importance_label"] == "SMALL_SIGNED"  # mean .034375 inside +/- .05
    assert primary["interval_label"] == "INTERVAL_INCLUDES_ZERO"
    assert primary["interval_inside_mei"] is False
    assert primary["degenerate_zero_variance"] is False and "degenerate_note" not in primary
    assert "coverage is not validated by five blocks" in primary["working_model"]

    # Curves for r = 5 ... 40 only; the endpoint is the primary, never one of the curve readings.
    assert list(result["curves"]) == [str(v) for v in range(5, 41, 5)]
    for rollout in range(5, 41, 5):
        offset = CURVE_STEP * (rollout // 5 - 9)
        assert result["curves"][str(rollout)]["mean"] == pytest.approx(np.mean(G_LEVELS) + offset)
        assert result["curves"][str(rollout)]["available_blocks"] == 5
    # Per-arm levels are descriptive; the paired SD is not replaced by them.
    for arm in ("CF", "D1280"):
        level = result["levels"][arm]
        values = [float(world_scores(arm, i, 45).mean()) for i in range(5)]
        assert level["available_blocks"] == 5 and level["mean"] == pytest.approx(np.mean(values))
        assert level["sample_sd"] == pytest.approx(np.std(values, ddof=1))
        assert "descriptive" in level["note"]
    assert result["sign_counts"] == {
        "positive": 3, "negative": 1, "zero": 1,
        "listed": {str(seed): G_LEVELS[i] for i, seed in enumerate(SEEDS)},
        "note": "listed, never used as a pass gate"}
    assert "never pooled with older objects" in result["interpretation_limit"]


@pytest.mark.parametrize("mean,label", [
    (.0500001, "D_REFERENCE_ABOVE"), (.05, "SMALL_SIGNED"), (.0, "SMALL_SIGNED"),
    (-.05, "SMALL_SIGNED"), (-.0500001, "CF_REFERENCE_ABOVE"),
    (np.nextafter(.05, 1.), "D_REFERENCE_ABOVE"), (np.nextafter(-.05, -1.), "CF_REFERENCE_ABOVE"),
])
def test_importance_label_boundaries(mean, label):
    assert matched.importance_label(mean) == label
    assert matched.importance_label(None) is None


@pytest.mark.parametrize("interval,label", [
    ([.01, .2], "INTERVAL_POSITIVE"), ([-.2, -.01], "INTERVAL_NEGATIVE"),
    ([0., .2], "INTERVAL_INCLUDES_ZERO"),      # an endpoint exactly zero includes zero
    ([-.2, 0.], "INTERVAL_INCLUDES_ZERO"),
    ([-.2, .2], "INTERVAL_INCLUDES_ZERO"),
    ([np.nextafter(0., 1.), .2], "INTERVAL_POSITIVE"),
    ([-.2, np.nextafter(0., -1.)], "INTERVAL_NEGATIVE"),
])
def test_interval_label_boundaries(interval, label):
    assert matched.interval_label(interval) == label
    assert matched.interval_label(None) is None


@pytest.mark.parametrize("interval,inside", [
    ([-.05, .05], True), ([-.05, np.nextafter(.05, 1.)], False),
    ([np.nextafter(-.05, -1.), .05], False), ([-.01, .01], True), ([.04, .06], False),
])
def test_interval_inside_mei_boundary(interval, inside):
    statistics = dict(matched.paired_statistics([.01] * 5), working_model_95pct_interval=interval)
    assert matched.read_primary(statistics)["interval_inside_mei"] is inside


def test_zero_variance_is_reported_as_degenerate():
    statistics = matched.paired_statistics([.08] * 5)
    reading = matched.read_primary(statistics)
    assert reading["sample_sd"] == 0. and reading["se"] == 0.
    assert reading["degenerate_zero_variance"] is True
    assert reading["working_model_95pct_interval"] == [.08, .08]
    assert reading["status"] == "complete" and reading["importance_label"] == "D_REFERENCE_ABOVE"
    assert reading["interval_label"] == "INTERVAL_POSITIVE"
    assert "degenerate" in reading["degenerate_note"]
    assert (reading["positive_blocks"], reading["negative_blocks"], reading["zero_blocks"]) == (5, 0, 0)
    zeros = matched.read_primary(matched.paired_statistics([0.] * 5))
    assert zeros["importance_label"] == "SMALL_SIGNED" and zeros["interval_label"] == "INTERVAL_INCLUDES_ZERO"
    assert zeros["interval_inside_mei"] is True and zeros["zero_blocks"] == 5


@pytest.mark.parametrize("count", [0, 1, 4])
def test_fewer_than_five_pairs_reads_primary_incomplete(count):
    reading = matched.read_primary(matched.paired_statistics([.02] * count))
    assert reading["status"] == "PRIMARY_INCOMPLETE_OR_INVALID"
    assert reading["available_blocks"] == count and reading["planned_blocks"] == 5
    assert reading["importance_label"] is None and reading["interval_label"] is None
    assert "available n" in reading["incomplete_note"]
    if count == 0:
        assert reading["mean"] is None
    else:
        assert reading["mean"] == pytest.approx(.02)  # kept with its available n, never imputed
    if count < 2:
        assert reading["sample_sd"] is None and reading["se"] is None
        assert reading["working_model_95pct_interval"] is None
    else:
        assert reading["t_multiplier"] == b01.T975[count - 1]


@pytest.mark.parametrize("damage", ["missing_arm", "unplanned_config", "wrong_multiplier",
                                    "missing_panel", "nonfinite", "wrong_stage"])
def test_a_damaged_or_missing_arm_never_becomes_a_difference(tmp_path, damage):
    summaries = supplied_summaries(tmp_path)
    victim = next(s for s in summaries if s["factorial_arm"] == "CF" and s["block_seed"] == SEEDS[0])
    if damage == "missing_arm":
        summaries.remove(victim)
    elif damage == "unplanned_config":
        victim["learner_config"]["gamma"] = .5
    elif damage == "wrong_multiplier":
        victim["lr_multiplier"] = 1.0
    elif damage == "missing_panel":
        victim["panels"].pop(2)
    elif damage == "nonfinite":
        victim["panels"][-1]["native_scores_J"][0] = float("inf")
    else:
        victim["stage"] = 0
    paths, selection_path = write(tmp_path, summaries)
    out = tmp_path / "reduce"
    assert matched.main(["reduce", "--summaries", *paths, "--selection", selection_path,
                         "--output-root", str(out)]) == 1
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "incomplete"
    primary = result["primary"]
    assert primary["status"] == "PRIMARY_INCOMPLETE_OR_INVALID"
    assert primary["available_blocks"] == 4  # no filling, no imputation, no dropped block
    assert primary["importance_label"] is None and primary["interval_label"] is None
    assert primary["mean"] == pytest.approx(np.mean(G_LEVELS[1:]))
    block = result["blocks"][0]
    if damage == "unplanned_config":
        assert block["pair"]["status"] == "incomplete"
        assert block["pair"]["failure"] == "unplanned comparator difference"
        assert set(block["arms"]) == {"CF", "D1280"}  # both credible, only the pair is not
    else:
        assert block["pair"]["status"] == "incomplete"
        assert block["pair"]["missing_operands"] == ["CF"]
        assert "CF" in block["missing_or_invalid_arms"] and "D1280" in block["arms"]
    # Every other block and the D1280 level keep their real values.
    assert [b["pair"]["status"] for b in result["blocks"][1:]] == ["complete"] * 4
    assert result["levels"]["D1280"]["available_blocks"] == 5
    assert result["levels"]["CF"]["available_blocks"] == (4 if damage != "unplanned_config" else 5)
    assert result["curves"]["5"]["available_blocks"] == 4
    assert sum(result["sign_counts"][k] for k in ("positive", "negative", "zero")) == 4


def test_reduce_refuses_an_invalid_or_foreign_selection(tmp_path):
    summaries = supplied_summaries(tmp_path)
    for selection in ({"object_id": matched.OBJECT_ID, "card": matched.CARD,
                       "status": "SELECTION_INCOMPLETE", "selected_lr_multiplier": None},
                      dict(SELECTION, object_id="FSD_BASELINE_INTERRUPTION_B01"),
                      dict(SELECTION, card="other.md"),
                      dict(SELECTION, selected_lr_multiplier=1.5)):
        with pytest.raises(SystemExit):
            matched.reduce_stage1(summaries, selection)
    # The selection is the multiplier the CF fits must actually carry.
    other = matched.reduce_stage1(summaries, dict(SELECTION, selected_lr_multiplier=2.0))
    assert other["primary"]["status"] == "PRIMARY_INCOMPLETE_OR_INVALID"
    assert other["primary"]["available_blocks"] == 0
    assert all("CF" in block["missing_or_invalid_arms"] for block in other["blocks"])


def test_reduce_refuses_unplanned_or_duplicated_cells(tmp_path):
    summaries = supplied_summaries(tmp_path)
    with pytest.raises(ValueError):
        matched.reduce_stage1(summaries + [summaries[0]], SELECTION)
    stray = copy.deepcopy(summaries[0])
    stray["block_seed"] = 772603  # a stage-0 tuning block
    with pytest.raises(ValueError):
        matched.reduce_stage1(summaries + [stray], SELECTION)
    stray["block_seed"], stray["factorial_arm"] = SEEDS[0], "FLAT"
    with pytest.raises(ValueError):
        matched.reduce_stage1([stray], SELECTION)
    # A duplicated cell is refused even when the first copy was not credible.
    broken = copy.deepcopy(summaries[0])
    broken["stage"] = 0
    with pytest.raises(ValueError):
        matched.reduce_stage1([broken, summaries[0]], SELECTION)
