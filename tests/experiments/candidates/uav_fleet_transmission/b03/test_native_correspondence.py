"""Two constructed 13-step native tails: exactly26 native transitions per run."""
from copy import deepcopy

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b02.controller import Program
from experiments.candidates.uav_fleet_transmission.b02.host import make_env
from experiments.candidates.uav_fleet_transmission.b02.option import plan_option
from experiments.candidates.uav_fleet_transmission.b03.surrogate import simulate_continuation
from experiments.candidates.uav_fleet_transmission.control import decode_public_state
from experiments.candidates.uav_fleet_transmission.host import MatchedWorld, mask_bits


@pytest.mark.parametrize("commitment", [False, True])
def test_model_matches_constructed_native_tail_through_arrival_and_resumption(commitment):
    users = np.zeros((50, 2))
    positions = np.tile([1000., 1000., 50.], (8, 1))
    positions[7] = [0., 0., 150.]
    scene = MatchedWorld(-303, 41, 42, users, positions)
    env = make_env(scene, 53, 43)
    native = env.env.env
    try:
        env.reset(seed=43)
        native.current_step = 40
        old_mask = 127
        native.set_transmitter_mask(mask_bits(old_mask, 8))
        state = env._count_state()
        decoded, decoded_users = decode_public_state(state, 8)
        program = Program("C", 53)
        program.controller.next_t = 40
        program.controller.positions, program.controller.users = decoded.copy(), decoded_users.copy()
        program.controller.commands[:] = [1., -1., 0.]
        plan = plan_option(decoded, decoded_users, old_mask) if commitment else None
        if commitment:
            assert plan["initiated"] and plan["duration"] == 10
        result = simulate_continuation(program.controller, state, old_mask, plan, horizon=53)
        program.plan, program.option_old_mask = deepcopy(plan), old_mask
        assert result["summary"]["model_transitions"] == 13
        for index, t in enumerate(range(40, 53)):
            command, mask, decision = program.select(t, state if t % 10 == 0 else None, old_mask)
            np.testing.assert_array_equal(command, result["arrays"]["actions"][index])
            assert mask == result["arrays"]["masks"][index]
            assert decision == result["decisions"][index]
            if t % 10 == 0:
                native.set_transmitter_mask(mask_bits(mask, 8))
            _, _, terminated, truncated, info = env.step(command)
            assert bool(terminated or truncated) == (t == 52)
            state = np.asarray(info["next_state"])
            np.testing.assert_array_equal(native.uav_positions, result["arrays"]["positions"][index + 1])
            reward = info["reward_components"]["reward_info"]
            expected = [reward["total_reward"], int(native.connections.sum()),
                        reward["quality_reward"], reward["energy_penalty"]]
            np.testing.assert_array_equal(expected, result["arrays"]["reward_components"][index])
            if (t + 1) % 10 == 0 and t + 1 < 53:
                at = np.flatnonzero(result["arrays"]["report_times"] == t + 1)[0]
                np.testing.assert_array_equal(state, result["arrays"]["reports"][at])
            old_mask = mask
    finally:
        env.close()
