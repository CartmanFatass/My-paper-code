"""Binding, stage guards, the tuned multiplier and the stage-0 selection rule (card sections 3, 8).

Fake learners and fake hosts only: a fit runs the frozen collector loop for 45 rollouts and nine
panels, so the loop, the panel schedule, the summary and the validators are shown to read this
object's values rather than the frozen runner's fifteen.
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
    "fsd_matched_helpers", Path(__file__).parents[1] / "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)
r = helpers.r

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402

fake_only = helpers.fake_only
STAGE0_SEED = 772603
STAGE1_SEED = 772803
COMPLETE_SELECTION = {"object_id": matched.OBJECT_ID, "card": matched.CARD, "status": "complete",
                      "selected_lr_multiplier": 2.0}


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
    monkeypatch.setattr(r, "base_summary", r.base_summary)  # restored after bind() wraps it
    monkeypatch.setattr(b01, "shared", r)
    monkeypatch.setattr(r, "HMASDAgent", PanelAgent)
    monkeypatch.setattr(matched, "shared", r)
    monkeypatch.setattr(matched, "_orig_base_summary", r.base_summary)


def run_fake_fit(tmp_path, arm, seed, stage, multiplier=None, selection=None, label=""):
    out = tmp_path / f"{arm}_{seed}_{stage}{label}"
    assert matched.run_fit(arm, seed, stage, multiplier, out, selection=selection,
                           admission={"sha": "synthetic-source", "command_sha256": "x"}) == 0
    return json.loads((out / "summary.json").read_text())


def test_binding_reaches_the_loop_panels_summary_and_validators(tmp_path):
    matched.bind()
    assert b01.OBJECT_ID == matched.OBJECT_ID and b01.CARD == matched.CARD
    assert b01.ROLLOUTS == 45 and b01.PANEL_ROLLOUTS == tuple(range(5, 46, 5))
    assert len(b01.PANEL_ROLLOUTS) == 9 and b01.BLOCKS == matched.BLOCKS and len(b01.BLOCKS) == 7
    assert b01.FLAT_ARM == "CF" and set(b01.ARMS) == {"CF", "D1280"}
    assert set(matched.TUNED_FIELDS) | {matched.CF_FLAG} <= b01.PLANNED_CONFIG_DIFFERENCES
    assert b01.make_config is matched.make_config and r.base_summary is matched.base_summary

    summary = run_fake_fit(tmp_path, "CF", STAGE0_SEED, 0, 2.0)
    assert summary["status"] == "complete" and summary["rollouts"] == 45
    assert summary["panel_rollouts"] == list(range(5, 46, 5))
    assert summary["stage"] == 0 and summary["lr_multiplier"] == 2.0
    assert summary["matched_information_object"] == matched.OBJECT_ID
    assert summary["admission"] == {"sha": "synthetic-source", "command_sha256": "x"}
    assert summary["arm"] == "CF" and summary["factorial_arm"] == "CF"
    assert summary["mei_J"] == .05 and summary["primary"] == "G_45"
    assert summary["ordinary_wall_plan_seconds"] == matched.WALL_PLANS["CF"]
    # The loop really ran 45 rollouts and nine panels, and the counts are the real exposure.
    assert summary["counts"]["update_stages"] == 45 and len(summary["training_rows"]) == 45
    assert len(summary["panels"]) == 9
    assert [p["panel_rollouts"] for p in summary["panels"]] == list(range(5, 46, 5))
    assert [p["after_update"] for p in summary["panels"]] == list(range(5, 46, 5))
    assert summary["counts"]["training_transitions"] == r.TRAIN_LANES * r.HORIZON * 45
    assert summary["counts"]["evaluation_agent_step_batches"] == 9 * r.HORIZON
    assert summary["counts"]["evaluation_episodes"] == 9 * r.EVAL_LANES
    assert summary["evaluation"] == summary["panels"][-1]
    assert all(row["relative_initialization_displacement"] for row in summary["training_rows"])
    # The validator reads the same 45 and nine.
    assert list(matched.fit_endpoint(summary)) == list(range(5, 46, 5))
    for field in ("panels", "rollouts", "update_stages"):
        damaged = copy.deepcopy(summary)
        if field == "panels":
            damaged["panels"].pop(3)
        elif field == "rollouts":
            damaged["rollouts"] = 15
        else:
            damaged["counts"]["update_stages"] = 15
        with pytest.raises(ValueError):
            matched.fit_endpoint(damaged)


def test_cf_and_d1280_construction_and_planned_differences(tmp_path):
    cf = run_fake_fit(tmp_path, "CF", STAGE1_SEED, 1, None,
                      selection=dict(COMPLETE_SELECTION, selected_lr_multiplier=0.5))
    d1280 = run_fake_fit(tmp_path, "D1280", STAGE1_SEED, 1)
    assert cf["lr_multiplier"] == 0.5 and d1280["lr_multiplier"] == 1.0
    assert cf["stage"] == d1280["stage"] == 1
    for summary, expected_flag in ((cf, True), (d1280, False)):
        for key in ("learner_config", "evaluation_config"):
            assert summary[key][matched.CF_FLAG] is expected_flag
    assert cf["learner_config"]["policy_interruption_mode"] == "off"
    assert cf["learner_config"]["n_Z"] == cf["learner_config"]["n_z"] == 1
    assert cf["learner_config"]["k"] == 10
    assert d1280["learner_config"]["policy_interruption_mode"] == "d2"
    assert d1280["learner_config"]["coordinator_batch_size"] == 1280
    # CF trains no coordinator or discriminator; D1280 keeps its standing coordinator work.
    assert all(cf["optimizer_calls"][k] == 0 for k in b01.FLAT_ONLY_ZERO)
    assert d1280["optimizer_calls"]["coordinator"] == 45
    for summary in (cf, d1280):
        assert summary["optimizer_calls"]["discoverer_actor"] > 0
        assert summary["optimizer_calls"]["discoverer_critic"] > 0
        assert not any(summary["evaluation_optimizer_calls"].values())
    differing = {k for k in set(cf["learner_config"]) | set(d1280["learner_config"])
                 if cf["learner_config"].get(k) != d1280["learner_config"].get(k)}
    assert differing <= b01.PLANNED_CONFIG_DIFFERENCES, differing
    assert matched.CF_FLAG in differing and set(matched.TUNED_FIELDS) <= differing
    assert b01.comparable_view(cf) == b01.comparable_view(d1280)
    assert list(matched.fit_endpoint(cf)) == list(matched.fit_endpoint(d1280)) == list(range(5, 46, 5))


@pytest.mark.parametrize("multiplier", [0.5, 1.0, 2.0])
def test_multiplier_applies_once_to_cf_actor_and_critic_groups_only(monkeypatch, multiplier):
    matched.bind()
    seen = []

    def fake(arm, envs, seed):
        seen.append(arm)
        return SimpleNamespace(lr_discoverer_actor=1e-4, lr_discoverer_critic=2e-4,
                               lr_coordinator=5e-4, lr_discriminator=3e-4)

    monkeypatch.setattr(matched, "_orig_make_config", fake)
    monkeypatch.setitem(matched.CURRENT, "lr_multiplier", multiplier)
    cf = matched.make_config("CF", [], STAGE0_SEED)
    assert cf.lr_discoverer_actor == 1e-4 * multiplier
    assert cf.lr_discoverer_critic == 2e-4 * multiplier
    # The never-trained groups are not tuning factors (card section 3).
    assert cf.lr_coordinator == 5e-4 and cf.lr_discriminator == 3e-4
    assert getattr(cf, matched.CF_FLAG) is True
    d1280 = matched.make_config("D1280", [], STAGE1_SEED)
    assert (d1280.lr_discoverer_actor, d1280.lr_discoverer_critic) == (1e-4, 2e-4)
    assert not getattr(d1280, matched.CF_FLAG, False)
    assert seen == ["CF", "D1280"]


def test_stage_guards():
    incomplete = {"object_id": matched.OBJECT_ID, "card": matched.CARD,
                  "status": "SELECTION_INCOMPLETE", "selected_lr_multiplier": None}
    refused = [
        ("D1280", STAGE0_SEED, 0, None, None),             # stage 0 is CF only
        ("CF", STAGE1_SEED, 0, 1.0, None),                 # stage 0 runs on the tuning blocks
        ("CF", STAGE0_SEED, 0, None, None),                # stage 0 needs an explicit multiplier
        ("CF", STAGE0_SEED, 0, 0.75, None),                # off the grid
        ("CF", STAGE0_SEED, 1, None, COMPLETE_SELECTION),  # stage 1 runs on the fresh blocks
        ("D1280", STAGE1_SEED, 1, 2.0, None),              # only CF carries a multiplier
        ("D1280", STAGE1_SEED, 1, 1.0, None),              # including the neutral one
        ("CF", STAGE1_SEED, 1, None, None),                # stage-1 CF needs the selection
        ("CF", STAGE1_SEED, 1, 1.0, COMPLETE_SELECTION),   # not the selected multiplier
        ("CF", STAGE1_SEED, 1, None, incomplete),          # no fallback from an incomplete selection
        ("CF", STAGE1_SEED, 1, None, dict(COMPLETE_SELECTION, object_id="OTHER")),
        ("CF", STAGE1_SEED, 1, None, dict(COMPLETE_SELECTION, card="other.md")),
        ("CF", STAGE1_SEED, 1, None, dict(COMPLETE_SELECTION, selected_lr_multiplier=1.5)),
        ("FLAT", STAGE1_SEED, 1, None, None),              # not an arm of this object
    ]
    for arm, seed, stage, multiplier, selection in refused:
        with pytest.raises(SystemExit):
            matched.stage_guard(arm, seed, stage, multiplier, selection)
    assert matched.stage_guard("CF", STAGE0_SEED, 0, 0.5, None) == 0.5
    assert matched.stage_guard("CF", 772703, 0, 2.0, None) == 2.0
    assert matched.stage_guard("D1280", STAGE1_SEED, 1, None, None) == 1.0
    assert matched.stage_guard("CF", STAGE1_SEED, 1, None, COMPLETE_SELECTION) == 2.0
    assert matched.stage_guard("CF", STAGE1_SEED, 1, 2.0, COMPLETE_SELECTION) == 2.0


def values(half, one, two):
    seeds = sorted(matched.STAGE0_BLOCKS)
    return {0.5: dict(zip(seeds, half)), 1.0: dict(zip(seeds, one)), 2.0: dict(zip(seeds, two))}


@pytest.mark.parametrize("half,one,two,selected,tie", [
    # A clear winner at each grid point.
    ([.40, .42], [.41, .43], [.45, .44], 2.0, False),
    ([.50, .52], [.41, .43], [.45, .44], 0.5, False),
    ([.40, .42], [.51, .53], [.45, .44], 1.0, False),
    # Every exact tie case: the fixed order 1, 0.5, 2 inside the maximal set.
    ([.40, .42], [.40, .42], [.30, .30], 1.0, True),
    ([.40, .42], [.30, .30], [.40, .42], 0.5, True),
    ([.30, .30], [.40, .42], [.40, .42], 1.0, True),
    ([.41, .41], [.41, .41], [.41, .41], 1.0, True),
    # The block mean decides, not a single block.
    ([.60, .20], [.41, .41], [.30, .30], 1.0, False),
])
def test_stage0_selection_rule_and_every_tie_case(half, one, two, selected, tie):
    result = matched.select_from_values(values(half, one, two))
    assert result["status"] == "complete"
    assert result["selected_lr_multiplier"] == selected and result["tie"] is tie
    assert result["means_J45"]["1.0"] == pytest.approx(np.mean(one))
    assert result["available_candidates"] == result["planned_candidates"] == 6
    assert not result["missing_or_invalid"] and not result["invalid_inputs"]
    assert result["selection_basis"]["mean_J45"] == pytest.approx(
        np.mean({0.5: half, 1.0: one, 2.0: two}[selected]))
    assert (len(result["maximal_set"]) > 1) is tie and selected in result["maximal_set"]


def test_stage0_selection_incomplete_has_no_fallback():
    partial = values([.40, .42], [.41, .43], [.45, .44])
    del partial[2.0][772703]
    result = matched.select_from_values(partial)
    assert result["status"] == "SELECTION_INCOMPLETE"
    assert result["selected_lr_multiplier"] is None and result["means_J45"] is None
    assert result["missing_or_invalid"] == [{"lr_multiplier": 2.0, "block_seed": 772703}]
    assert result["available_candidates"] == 5
    invalid = matched.select_from_values(values([.40, .42], [.41, .43], [.45, .44]),
                                         failures=[{"summary": "CF", "failure": "non-finite J45"}])
    assert invalid["status"] == "SELECTION_INCOMPLETE" and invalid["selected_lr_multiplier"] is None
    assert invalid["available_candidates"] == 6  # complete but not credible: still no selection
    for unusable in (result, invalid):
        with pytest.raises(SystemExit):
            matched.selected_multiplier(unusable)


def test_select_stage0_cli_reads_real_fit_summaries(tmp_path):
    """Six fake stage-0 fits through the real select-stage0 entry point."""
    scores = {(0.5, 772603): .40, (0.5, 772703): .42, (1.0, 772603): .41, (1.0, 772703): .43,
              (2.0, 772603): .45, (2.0, 772703): .44}
    template = run_fake_fit(tmp_path, "CF", 772603, 0, 1.0)
    paths, summaries = [], []
    for (multiplier, seed), value in scores.items():
        summary = copy.deepcopy(template)
        evaluation_seed = matched.STAGE0_BLOCKS[seed]
        summary.update(block_seed=seed, training_seed=seed, evaluation_seed=evaluation_seed,
                       lr_multiplier=multiplier,
                       training_lane_seeds=list(range(seed, seed + r.TRAIN_LANES)),
                       evaluation_lane_seeds=list(range(evaluation_seed,
                                                        evaluation_seed + r.EVAL_LANES)))
        summary["learner_config"]["seed"] = seed
        summary["evaluation_config"]["seed"] = evaluation_seed
        for panel in summary["panels"]:
            panel["lane_seeds"] = summary["evaluation_lane_seeds"]
            panel["native_scores_J"] = [value] * r.EVAL_LANES
            panel["returns_U"] = [value * r.HORIZON / r.N_UAVS] * r.EVAL_LANES
        summary["evaluation"] = summary["panels"][-1]
        path = tmp_path / f"cf_{multiplier}_{seed}.json"
        path.write_text(json.dumps(summary), encoding="utf-8")
        paths.append(str(path))
        summaries.append(summary)
    out = tmp_path / "selection"
    assert matched.main(["select-stage0", "--summaries", *paths, "--output-root", str(out)]) == 0
    selection = json.loads((out / "SELECTION.json").read_text())
    assert selection["status"] == "complete" and selection["selected_lr_multiplier"] == 2.0
    assert selection["per_seed_J45"]["2.0"] == pytest.approx({"772603": .45, "772703": .44})
    assert selection["object_id"] == matched.OBJECT_ID and selection["stage"] == 0
    assert selection["launch_sha"] == "synthetic-source"
    assert selection["input_summaries"] == paths
    assert matched.selected_multiplier(selection) == 2.0
    # One missing fit ends the object: no silent selection among the rest.
    assert matched.main(["select-stage0", "--summaries", *paths[:-1], "--output-root", str(out)]) == 1
    incomplete = json.loads((out / "SELECTION.json").read_text())
    assert incomplete["status"] == "SELECTION_INCOMPLETE"
    assert incomplete["missing_or_invalid"] == [{"lr_multiplier": 2.0, "block_seed": 772703}]
    # Neither a D1280 fit, nor a stage-1 fit, nor an unplanned block or multiplier is a candidate.
    for damage in ({"factorial_arm": "D1280"}, {"stage": 1}, {"block_seed": 772803},
                   {"lr_multiplier": 1.5}):
        assert matched.select_stage0([dict(summaries[0], **damage)])["status"] == \
            "SELECTION_INCOMPLETE"
    duplicated = matched.select_stage0(summaries + [summaries[0]])
    assert duplicated["status"] == "SELECTION_INCOMPLETE"
    assert "duplicate" in duplicated["invalid_inputs"][0]["failure"]
