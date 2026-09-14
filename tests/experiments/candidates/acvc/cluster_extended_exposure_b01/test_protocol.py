import copy

import pytest

from experiments.candidates.acvc.cluster_extended_exposure_b01 import protocol as p


def rows():
    result = []
    for checkpoint in p.CHECKPOINTS:
        exposure = 0 if checkpoint == 1024 else 1
        for arm in p.ARMS:
            for episode in range(64):
                common = episode / 1000
                offset = {"C": 0.0, "F": .02 + .02 * exposure,
                          "dwell": .01 + .01 * exposure}[arm]
                value = common + offset
                result.append({
                    "phase": "eval", "checkpoint_episode": checkpoint, "arm": arm,
                    "episode": episode, "base": p.MASTER,
                    "evaluation_namespace": p.EVALUATION_NAMESPACE,
                    "reset_seed": 100000 * p.EVALUATION_NAMESPACE + 2000 + episode,
                    "steps": p.HORIZON, "J": value, "S": value * p.HORIZON,
                })
    return result


def test_endpoints_and_direct_covariance_preserving_changes():
    result = p.final_panel(rows())
    assert result["complete"]
    assert result["endpoints"]["1024"]["contrasts"]["F-C"]["reading"] == "UP"
    assert result["endpoints"]["1024"]["contrasts"]["F-dwell"]["reading"] == "WITHIN"
    assert result["endpoints"]["1024"]["contrasts"]["dwell-C"]["reading"] == "DESCRIPTIVE"
    change = result["changes"]["G_dwell"]
    assert change["mean_J"] == pytest.approx(.01)
    assert change["conditional_SE_J"] == pytest.approx(0.0, abs=1e-15)
    assert change["reading"] == "WITHIN"
    assert len(change["paired_difference_of_differences_J"]) == 64
    assert result["changes"]["G_C"]["mean_J"] == pytest.approx(.02)
    assert result["changes"]["G_C"]["reading"] == "INCREASE"
    # Endpoint observations vary across worlds, yet their paired change is constant.
    assert result["endpoints"]["1024"]["arms"]["F"]["maximum_J"] \
        > result["endpoints"]["1024"]["arms"]["F"]["minimum_J"]


@pytest.mark.parametrize("value,expected", [
    (.01000001, "INCREASE"), (.01, "WITHIN"), (0.0, "WITHIN"),
    (-.01, "WITHIN"), (-.01000001, "DECREASE"),
])
def test_change_threshold_is_inclusive_at_the_margin(value, expected):
    assert p.change_reading(value) == expected


def test_missing_wrong_or_duplicate_rows_only_remove_dependent_outputs():
    base = rows()
    missing = [row for row in base
               if not (row["checkpoint_episode"] == 1024 and row["arm"] == "C" and row["episode"] == 3)]
    result = p.final_panel(missing)
    assert not result["complete"]
    assert not result["endpoints"]["1024"]["contrasts"]["F-C"]["complete"]
    assert not result["endpoints"]["1024"]["contrasts"]["dwell-C"]["complete"]
    assert result["endpoints"]["1024"]["contrasts"]["F-dwell"]["complete"]
    assert not result["changes"]["G_C"]["complete"]
    assert result["changes"]["G_dwell"]["complete"]

    wrong_stage = copy.deepcopy(base)
    wrong_stage[0]["checkpoint_episode"] = 777
    assert not p.final_panel(wrong_stage)["complete"]
    wrong_reset = copy.deepcopy(base)
    wrong_reset[64]["reset_seed"] += 1
    assert not p.final_panel(wrong_reset)["endpoints"]["1024"]["contrasts"]["F-C"]["complete"]
    duplicate = base + [copy.deepcopy(base[-1])]
    assert not p.final_panel(duplicate)["complete"]
