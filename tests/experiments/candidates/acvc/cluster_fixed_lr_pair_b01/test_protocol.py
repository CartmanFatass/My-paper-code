import copy

import numpy as np
import pytest

from experiments.candidates.acvc.cluster_fixed_lr_pair_b01 import protocol as p


def rows(recipe):
    result = []
    for arm in p.ARMS:
        for episode in range(64):
            common = episode / 1000
            offset = {"C": 0.0, "F": .04, "dwell": .015}[arm]
            # The shared, varying common term cancels only in direct paired differences.
            value = common + offset + (0.03 if recipe == "low" else 0)
            result.append(dict(phase="eval", recipe=recipe, learning_rate=p.RECIPES[recipe],
                               arm=arm, episode=episode, base=p.MASTER,
                               evaluation_namespace=p.EVALUATION_NAMESPACE, checkpoint_episode=4096,
                               reset_seed=100000*p.EVALUATION_NAMESPACE+2000+episode,
                               steps=p.HORIZON, J=value, S=value*p.HORIZON))
    return result


def test_pair_orientation_and_covariance_preserving_world_reduction():
    result = p.paired_panel({recipe: rows(recipe) for recipe in p.RECIPES})
    assert result["complete"]
    delta = result["cross_recipe"]["low_C-reference_C"]
    assert delta["mean_J"] == pytest.approx(.03)
    assert delta["reading"] == "UP" and delta["positive"] == 64
    assert delta["conditional_SE_J"] == pytest.approx(0, abs=1e-15)
    assert np.std(result["recipes"]["low"]["arms"]["C"]["values_J"]) > .01
    for recipe in p.RECIPES:
        panel = result["recipes"][recipe]
        assert panel["contrasts"]["F-C"]["mean_J"] == pytest.approx(.04)
        assert panel["contrasts"]["F-dwell"]["mean_J"] == pytest.approx(.025)
        assert panel["contrasts"]["dwell-C"]["reading"] == "DESCRIPTIVE"
    assert result["cross_recipe"]["low_dwell-reference_dwell"]["reading"] == "DESCRIPTIVE"


@pytest.mark.parametrize("value,expected", [(.01000001,"UP"),(.01,"WITHIN"),(0,"WITHIN"),(-.01,"WITHIN"),(-.01000001,"DOWN")])
def test_primary_rule_inclusive_margin(value, expected):
    assert p.reading(value) == expected


def test_bad_identity_or_missing_world_only_removes_dependent_contrasts():
    pair = {recipe: rows(recipe) for recipe in p.RECIPES}
    pair["low"][0]["reset_seed"] += 1
    result = p.paired_panel(pair)
    assert not result["complete"]
    assert result["cross_recipe"]["low_C-reference_C"]["reading"] == "INCOMPLETE"
    assert result["recipes"]["low"]["contrasts"]["F-C"]["reading"] == "INCOMPLETE"
    assert result["recipes"]["low"]["contrasts"]["F-dwell"]["complete"]
    assert result["recipes"]["reference"]["complete"]
    for key, value in (("recipe", "reference"), ("learning_rate", 3e-4), ("checkpoint_episode", 1024)):
        changed = rows("low")
        changed[64][key] = value
        assert not p.final_panel(changed,"low")["contrasts"]["F-dwell"]["complete"]
    complete_rows = rows("low")
    assert not p.final_panel(complete_rows + [copy.deepcopy(complete_rows[-1])],"low")["complete"]
    assert not p.paired_panel({"low": complete_rows})["complete"]
