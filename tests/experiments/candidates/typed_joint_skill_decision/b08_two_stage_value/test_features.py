from copy import deepcopy

import numpy as np
import pytest

from experiments.candidates.typed_joint_skill_decision.b08_two_stage_value import features


def case(mask=5):
    report = np.zeros(133, dtype=np.float32)
    report[:24] = np.linspace(.1, .9, 24, dtype=np.float32)
    report[24:32] = 1.
    report[32:132] = np.linspace(0, 1, 100, dtype=np.float32)
    report[-1] = .08
    positions = report[:24].reshape(8, 3).astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
    commands = np.zeros((8, 3), dtype=np.float32); commands[7] = [1, -1, 0]
    tail = dict(J=.35, served=20, quality=.7, energy_penalty=.025)
    layout = ["member", "site", "kx", "ky", "descent_ticks", "duration", "mask", "total_J",
              "total_served", "path", "transit_J", "transit_served", "tail_J", "tail_served",
              "tail_quality", "tail_energy_penalty"] + [f"destination_{i}_{axis}" for i in range(8) for axis in "xyz"]
    original = dict(initiated=False, member=None, site=None, offsets=None, commands=[], duration=0,
                    arrival_t=None, predicted_destination=positions.tolist(), predicted_mask=None,
                    predicted_total_J=161., predicted_total_served=9200.,
                    stay_score=tail.copy(), stay_total_J=161., stay_total_served=9200., selected=None,
                    candidate_digest="0"*64, digest_layout=layout, candidate_count=(8-mask.bit_count())*100,
                    counts={})
    plans = [None]
    for member in range(8):
        if mask & (1 << member):
            continue
        dest = positions.copy(); dest[member] = [500, 600, 50]
        # Frozen B04's t40 delegate returns B03 _plan dictionaries without
        # start_t; t120's separate implementation adds that field.
        command_rows = np.zeros((20, 8, 3), dtype=np.float32)
        command_rows[:2, member, 0] = -1; command_rows[:3, member, 1] = 1
        command_rows[:2, member, 2] = -1
        detail = dict(offsets=[-2, 3], descent_ticks=2, unrounded_duration=3, duration=20,
                      transit_J=6., transit_served=400., path=200., member=member, site=member+50,
                      predicted_mask=mask | (1 << member), tail_score=tail.copy(),
                      predicted_total_J=160. - member, predicted_total_served=9190. - member,
                      predicted_destination=dest.tolist(), arrival_t=60)
        plans.append(dict(initiated=True, member=member, site=member + 50,
                          offsets=[-2, 3], commands=command_rows.tolist(), duration=20, arrival_t=60,
                          predicted_destination=dest.tolist(), predicted_mask=mask | (1 << member),
                          predicted_total_J=160. - member, predicted_total_served=9190. - member,
                          stay_score=tail.copy(), stay_total_J=161., stay_total_served=9200., selected=detail,
                          candidate_digest="0"*64, digest_layout=layout.copy(),
                          candidate_count=original["candidate_count"], counts={}))
    if len(plans) > 1: original["selected"] = deepcopy(plans[1]["selected"])
    return report, commands, mask, plans, dict(original_R=original, champions=plans[1:])


def test_original_t40_schema_without_start_time_is_accepted_without_mutation():
    args = case()
    before = deepcopy(args)
    assert all("start_t" not in plan for plan in args[3][1:])
    expected_keys = {"initiated", "member", "site", "offsets", "commands", "duration", "arrival_t",
                     "predicted_destination", "predicted_mask", "predicted_total_J", "predicted_total_served",
                     "stay_score", "stay_total_J", "stay_total_served", "selected", "candidate_digest",
                     "digest_layout", "candidate_count", "counts"}
    assert set(args[4]["original_R"]) == expected_keys
    assert all(set(plan) == expected_keys for plan in args[3][1:])
    original = features.build_features(*args)
    assert args[3] == before[3] and args[4] == before[4]
    explicit = deepcopy(args)
    for plan in explicit[3][1:]: plan["start_t"] = 40
    tagged = features.build_features(*explicit)
    for key in original:
        np.testing.assert_array_equal(original[key], tagged[key])
    explicit[3][1]["start_t"] = 120
    with pytest.raises(ValueError, match="t40"):
        features.build_features(*explicit)


def test_exact_dimensions_rights_axes_and_stationary_scalars():
    report, commands, mask, plans, bank = case()
    x = features.build_features(report, commands, mask, plans, bank)
    for key, shape in features.SHAPES.items():
        assert x[key].shape == shape and x[key].dtype == np.float32 and x[key].flags.c_contiguous
        assert np.count_nonzero(x[key][7:]) == 0
    assert x["valid"].dtype == np.bool_ and x["valid"].tolist() == [True] * 7 + [False]
    np.testing.assert_array_equal(x["U"][0, :, :3], report[:24].reshape(8, 3))
    np.testing.assert_array_equal(x["U"][1, :, 3:6], commands)
    np.testing.assert_array_equal(x["U"][1, :, 6], [1, 0, 1, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(x["U"][1, :, 7:15], np.eye(8, dtype=np.float32))
    np.testing.assert_array_equal(x["U"][1, :, 19], [0, 1, 0, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(x["Y"][1], report[32:132].reshape(50, 2))
    # UAV0's peers are1..7; UAV2's peers are0,1,3..7, and edge rights
    # refer to the *other* member rather than the receiving member.
    np.testing.assert_array_equal(x["E_UU"][1, 0, :, 8], [1, 0, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(x["E_UU"][1, 2, :, 6], [1, 0, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(x["E_UY"][1, 1, :, 8], np.ones(50, dtype=np.float32))
    np.testing.assert_allclose(x["S"][1, :9], [0, .5, -2/34, 3/34, .5,
                            200/(1200*np.sqrt(3)), -2/460, -11/23000, .35], rtol=1e-7)
    # Frozen energy_penalty is the height penalty: .025/.1 = .25.
    assert x["S"][0, 11] == np.float32(.25)
    np.testing.assert_array_equal(x["S"][0, 1:8], np.zeros(7, dtype=np.float32))
    np.testing.assert_array_equal(x["S"][0, 12:14], np.zeros(2, dtype=np.float32))
    assert x["S"][0, 14] == report[-1] and x["S"][0, 15] == np.float32(6/7)
    assert x["S"][0, 16] == .25
    positions = report[:24].reshape(8, 3).astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
    expected = ((positions[2] - positions[[0, 1, 3, 4, 5, 6, 7]]) / [1000, 1000, 100]).astype(np.float32)
    np.testing.assert_array_equal(x["E_UU"][0, 2, :, :3], expected)


def test_singleton_and_zero_displacement_alias_remain_initiated():
    maximum = features.build_features(*case(1))
    assert maximum["valid"].tolist() == [True] * 8
    assert maximum["S"][7, 15] == 1. and maximum["U"][7, 7, 19] == 1.
    x = features.build_features(*case(255))
    assert x["valid"].tolist() == [True] + [False] * 7
    args = case(253)  # only member1 muted
    positions = args[0][:24].reshape(8, 3).astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
    args[3][1]["predicted_destination"] = positions.tolist()
    original = features.build_features(*args)
    args[3][1]["site"] = 99
    alias = features.build_features(*args)
    for key in original:
        np.testing.assert_array_equal(original[key], alias[key])
    assert original["S"][1, 0] == 0 and original["S"][1, 1] == .5
    assert original["U"][1, 1, 19] == 1


@pytest.mark.parametrize("mutation", ["validity", "dtype", "mask", "order", "peer_move"])
def test_reject_illegal_report_or_menu(mutation):
    args = list(deepcopy(case()))
    if mutation == "validity": args[0][24] = 0
    if mutation == "dtype": args[0] = args[0].astype(np.float64)
    if mutation == "mask": args[2] = 0
    if mutation == "order": args[3][1:3] = args[3][2:0:-1]
    if mutation == "peer_move": args[3][1]["predicted_destination"][0][0] += 1
    with pytest.raises(ValueError): features.build_features(*args)
