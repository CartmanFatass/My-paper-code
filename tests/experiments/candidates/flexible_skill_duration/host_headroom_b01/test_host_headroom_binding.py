"""Binding, stage-0 selection and pre-registered rule of the FSD host headroom B01 thin entry (no fits)."""
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))

import run_fsd_host_headroom_b01 as hh  # noqa: E402
import run_fsd_baseline_interruption_b01 as b01  # noqa: E402

SEEDS = sorted(hh.STAGE1_BLOCKS)


def test_binding_rebinds_identity_blocks_and_panels():
    hh.bind()
    assert b01.OBJECT_ID == "FSD_HOST_HEADROOM_B01" and b01.CARD == hh.CARD
    assert b01.ROLLOUTS == 45 and b01.PANEL_ROLLOUTS == (5, 10, 15, 20, 25, 30, 35, 40, 45)
    assert set(b01.BLOCKS) == set(hh.STAGE0_BLOCKS) | set(hh.STAGE1_BLOCKS) and len(b01.BLOCKS) == 7
    assert set(hh.TUNED_FIELDS) <= b01.PLANNED_CONFIG_DIFFERENCES
    assert b01.make_config is hh.make_config and hh.shared.base_summary is hh.base_summary


def test_multiplier_applies_to_flat_learning_rates_only(monkeypatch):
    hh.bind()
    calls = []

    def fake(arm, envs, seed):
        calls.append(arm)
        return types.SimpleNamespace(lr_discoverer_actor=1e-3, lr_discoverer_critic=2e-3, lr_coordinator=5e-4)
    monkeypatch.setattr(hh, "_orig_make_config", fake)
    hh.CURRENT.update(stage=0, lr_multiplier=2.0)
    c = hh.make_config("FLAT", [], 772603)
    assert (c.lr_discoverer_actor, c.lr_discoverer_critic, c.lr_coordinator) == (2e-3, 4e-3, 5e-4)
    c = hh.make_config("D1280", [], 772603)
    assert (c.lr_discoverer_actor, c.lr_discoverer_critic) == (1e-3, 2e-3)
    hh.CURRENT.update(stage=None, lr_multiplier=1.0)
    assert calls == ["FLAT", "D1280"]


def test_base_summary_records_stage_and_multiplier(monkeypatch):
    monkeypatch.setattr(hh, "_orig_base_summary", lambda *a, **k: {"arm": "FLAT"})
    hh.CURRENT.update(stage=1, lr_multiplier=0.5)
    s = hh.base_summary("FLAT")
    assert s["stage"] == 1 and s["lr_multiplier"] == 0.5 and s["headroom_object"] == "FSD_HOST_HEADROOM_B01"
    hh.CURRENT.update(stage=None, lr_multiplier=1.0)


def test_stage_guards():
    with pytest.raises(SystemExit):
        hh.run_fit("D1280", 772603, 0, 1.0, Path("unused"))
    with pytest.raises(SystemExit):
        hh.run_fit("FLAT", 772603, 0, 0.75, Path("unused"))
    with pytest.raises(SystemExit):
        hh.run_fit("D1280", 772803, 1, 2.0, Path("unused"))
    with pytest.raises(SystemExit):
        hh.run_fit("FLAT", 772603, 1, 1.0, Path("unused"))


def test_stage0_selection_picks_highest_mean_and_ties_go_to_default():
    v = {0.5: {772603: .40, 772703: .42}, 1.0: {772603: .41, 772703: .43}, 2.0: {772603: .45, 772703: .44}}
    r = hh.select_from_values(v)
    assert r["selected_lr_multiplier"] == 2.0 and r["tie"] is False
    v[2.0] = {772603: .43, 772703: .41}  # mean .42 == 1.0's mean .42
    r = hh.select_from_values(v)
    assert r["selected_lr_multiplier"] == 1.0 and r["tie"] is True
    with pytest.raises(ValueError):
        hh.select_from_values({0.5: {772603: .4}, 1.0: v[1.0], 2.0: v[2.0]})


@pytest.mark.parametrize("vals,s,expected", [
    ([.21, .22, .23, .24, .25], .1, "HIERARCHY_ABOVE"),          # mean .23 > 2s = .2, 5 positive
    ([.21, .22, .23, .24, -.05], .1, "UNRESOLVED"),              # 4 of 5 positive but mean .17 < 2s
    ([.30, .30, .30, .30, -.05], .1, "HIERARCHY_ABOVE"),         # mean .23 > .2, 4 positive
    ([.30, .30, .30, -.05, -.05], .1, "UNRESOLVED"),             # 3 positive only
    ([.05, -.05, .05, -.05, .05], .1, "INDISTINGUISHABLE"),      # mean .01 inside +/-1s
    ([.09, .09, .09, .09, .09], .1, "INDISTINGUISHABLE"),        # mean .09 < s
    ([.15, .15, .15, .15, .15], .1, "UNRESOLVED"),               # between 1s and 2s
    ([-.30, -.30, -.30, -.30, .05], .1, "FLAT_ABOVE"),            # mean -.23 < -2s, 4 negative
    ([.5, .5, .5, .5, .5], 0.0, "UNRESOLVED"),                   # degenerate s
    ([.5, .5, .5, .5], .1, "UNRESOLVED"),                        # wrong seed count
])
def test_rule(vals, s, expected):
    assert hh.read_rule(vals, s, hh.LABELS["H"]) == expected


def test_rule_boundaries_are_strict():
    s = .1
    zero = 0.0
    assert hh.read_rule([zero + .2] * 5, s, hh.LABELS["H"]) == "UNRESOLVED"       # mean == 2s is not above
    assert hh.read_rule([zero + .1] * 5, s, hh.LABELS["H"]) == "UNRESOLVED"       # mean == 1s is not inside
    assert hh.read_rule([zero + .2 + 1e-9] * 5, s, hh.LABELS["H"]) == "HIERARCHY_ABOVE"


def test_contrasts_from_levels_labels_and_curves():
    levels = {a: {} for a in hh.CONTRAST_ARMS}
    for i, k in enumerate(SEEDS):
        base = .40 + .01 * i
        for r in hh.PANEL_ROLLOUTS:
            levels["FLAT"][k] = levels["FLAT"].get(k, {}); levels["FLAT"][k][r] = base
            levels["D1280"][k] = levels["D1280"].get(k, {}); levels["D1280"][k][r] = base + .30
            levels["I1280"][k] = levels["I1280"].get(k, {}); levels["I1280"][k][r] = base + .31
    out = hh.contrasts_from_levels(levels)
    s = out["pooled_seed_sd_J45"]
    assert abs(s - 0.015811388300841896) < 1e-12 and out["pooled_df"] == 12
    assert out["contrasts"]["H"]["label"] == "HIERARCHY_ABOVE" and out["primary"] == "HIERARCHY_ABOVE"
    assert out["contrasts"]["SI"]["label"] == "INDISTINGUISHABLE"   # +.01 < s
    assert out["contrasts"]["H"]["working_model_95pct_interval"] == pytest.approx([.30, .30])
    assert set(out["curves"]["H"]) == {str(r) for r in hh.PANEL_ROLLOUTS}
    assert out["levels"]["D1280"]["reference_context_J"] == .67
