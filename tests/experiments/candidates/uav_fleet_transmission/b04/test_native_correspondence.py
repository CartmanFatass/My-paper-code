"""Constructed second-opportunity native check: 26 transitions per suite invocation."""
from copy import deepcopy

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b02.host import make_env
from experiments.candidates.uav_fleet_transmission.b04.option import enumerate_champions
from experiments.candidates.uav_fleet_transmission.b04.surrogate import OptionProgram, simulate_segment
from experiments.candidates.uav_fleet_transmission.control import decode_public_state
from experiments.candidates.uav_fleet_transmission.host import MatchedWorld, mask_bits


@pytest.mark.parametrize("commitment", [False, True])
def test_second_opportunity_model_native_arrival_and_resumption(commitment):
    users = np.zeros((50, 2))
    positions = np.tile([1000., 1000., 50.], (8, 1))
    positions[7] = [0., 0., 150.]
    scene = MatchedWorld(-404, 41, 42, users, positions)
    env = make_env(scene, 500, 43)
    native = env.env.env
    try:
        env.reset(seed=43)
        native.current_step = 120
        old_mask = 127
        native.set_transmitter_mask(mask_bits(old_mask, 8))
        state = env._count_state()
        decoded, decoded_users = decode_public_state(state, 8)
        program = OptionProgram("C", 500)
        program.controller.next_t = 120
        program.controller.positions, program.controller.users = decoded.copy(), decoded_users.copy()
        program.controller.commands[:] = [1., -1., 0.]
        plan = enumerate_champions(decoded, decoded_users, old_mask, 120)["original_R"] if commitment else None
        if commitment:
            assert plan["initiated"] and plan["duration"] == 10 and plan["arrival_t"] == 130
        result = simulate_segment(program.controller, state, old_mask, plan, start_t=120, end_t=133)
        program.plan, program.option_old_mask = deepcopy(plan), old_mask
        assert result["summary"]["model_transitions"] == 13
        for index, t in enumerate(range(120, 133)):
            command, mask, decision = program.select(t, state if t % 10 == 0 else None, old_mask)
            np.testing.assert_array_equal(command, result["arrays"]["actions"][index])
            assert mask == result["arrays"]["masks"][index]
            assert decision == result["decisions"][index]
            if t % 10 == 0:
                native.set_transmitter_mask(mask_bits(mask, 8))
            _, _, terminated, truncated, info = env.step(command)
            assert not (terminated or truncated)
            state = np.asarray(info["next_state"])
            np.testing.assert_array_equal(native.uav_positions, result["arrays"]["positions"][index + 1])
            reward = info["reward_components"]["reward_info"]
            expected = [reward["total_reward"], int(native.connections.sum()),
                        reward["quality_reward"], reward["energy_penalty"]]
            np.testing.assert_array_equal(expected, result["arrays"]["reward_components"][index])
            if (t + 1) % 10 == 0:
                at = np.flatnonzero(result["arrays"]["report_times"] == t + 1)[0]
                np.testing.assert_array_equal(state, result["arrays"]["reports"][at])
            old_mask = mask
    finally:
        env.close()
