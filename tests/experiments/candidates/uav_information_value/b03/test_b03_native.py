from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world, make_eval_config
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_information_value.b03.batch import make_controller
from experiments.candidates.uav_information_value.b03.observer import AnchorObserver
from experiments.candidates.uav_service_auxiliary.b01.native import make_env


@pytest.mark.parametrize("arm", ("H_BS", "P_BS", "S0_BS"))
def test_native_observer_is_read_only_and_serializes_numeric_trace(tmp_path, arm):
    config = make_eval_config(31, 0)
    outputs = []
    for observe in (False, True):
        env = make_env(config, 17)
        observer = AnchorObserver(arm, env.env) if observe else None
        try:
            row, native = evaluate_world(make_controller(arm), env, config, 17,
                                         PRODUCTION_PARAMS, observer=observer)
            outputs.append((row, native))
            if observer is not None:
                trace = observer.arrays()
                assert len(trace["info_bs_present"]) == row["actual_length"] == 31
                assert trace["info_native_pre_xyz"].shape == (31, 8, 3)
                np.testing.assert_array_equal(trace["info_native_delta_xyz"],
                                              trace["info_native_post_xyz"] - trace["info_native_pre_xyz"])
                np.testing.assert_array_equal(trace["info_native_pre_xyz"][1:],
                                              trace["info_native_post_xyz"][:-1])
                assert trace["info_controller_proposal"].shape == trace["info_shield_submitted"].shape == (31, 8, 4)
                assert trace["info_native_battery"].shape == (31, 8)
                assert trace["info_held_plan_source"].shape == (31,)
                assert trace["info_plan_bs_input_xy"].shape[1] == 2
                assert observer.reading()["native_minimum_battery_ratio"] == row["episode_minimum_battery_ratio"]
                path = tmp_path / f"{arm}.npz"
                np.savez_compressed(path, **native, **trace)
                with np.load(path, allow_pickle=False) as loaded:
                    assert loaded["info_native_delta_xyz"].shape == (31, 8, 3)
        finally:
            env.close()
    off_row, off_native = outputs[0]
    on_row, on_native = outputs[1]
    assert off_row == on_row
    assert off_native.keys() == on_native.keys()
    for key in off_native:
        np.testing.assert_array_equal(off_native[key], on_native[key])
