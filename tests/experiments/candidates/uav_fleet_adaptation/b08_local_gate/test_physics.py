"""Off-panel correctness fixtures for scalar physics, reset and declared exposure."""
from dataclasses import replace

import numpy as np
import pytest

from envs.pettingzoo.uav_env import MultiUAVEnv
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.contract import CONTRASTS, FROZEN, PROGRAMS, gate_uniform
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import check_host, make_real, original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.physics import assignment, assert_radio_equal, scalar_state


def test_original_factory_one_constructor_reset_and_scalar_all_masks():
    class CountedBase(MultiUAVEnv):
        resets = 0

        def reset(self, *args, **kwargs):
            self.resets += 1
            return super().reset(*args, **kwargs)

    env = make_real(90801, base_class=CountedBase)
    try:
        assert env.env.resets == 1
        check_host(env)
        expected, users = original_layout(90801)
        np.testing.assert_array_equal(env.env.uav_positions, expected)
        np.testing.assert_array_equal(env.env.user_positions, users)
        masks = [np.ones(5, dtype=bool)]
        for i in range(5):
            mask = np.ones(5, dtype=bool)
            mask[i] = False
            masks.append(mask)
        counts = {}
        for mask in masks:
            native_rows = env._dict_to_array(env.env.set_transmitter_mask(mask))
            result = scalar_state(expected, users, mask, 0, counts=counts)
            assert_radio_equal(env.env.sinr_matrix, result["sinr"])
            assert_radio_equal(env.env.uav_sinr_matrix, result["peer_sinr"])
            np.testing.assert_array_equal(env.env.connections, result["connections"])
            np.testing.assert_allclose(native_rows, result["observations"], rtol=0, atol=1e-7)
            assert env.env._compute_reward() == pytest.approx(result["reward"], abs=2e-13)
            if not mask.all():
                np.testing.assert_array_equal(native_rows[~mask, 3:103], 0)
        assert counts["scalar_states"] == 6 and counts["user_distance_links"] == 1500
        assert counts["peer_distance_pairs"] == 60
        assert env.env.resets == 1 and env.env.current_step == 0
    finally:
        env.close()


def test_scalar_assignment_threshold_capacity_and_stable_ties():
    sinr = np.full((5, 50), -np.inf)
    sinr[0, :12] = 3.
    sinr[1, :12] = 3.
    sinr[2, 13] = np.nextafter(3., -np.inf)
    result = assignment(sinr)
    np.testing.assert_array_equal(np.flatnonzero(result[0]), np.arange(10))
    np.testing.assert_array_equal(np.flatnonzero(result[1]), [10, 11])
    assert not result[2].any() and result.sum() == 12


def test_radio_tolerance_cannot_hide_changed_silence_or_eligibility():
    base = np.array([[-np.inf, 3., 4.]])
    assert assert_radio_equal(base, base) == 0
    for bad in (np.array([[0., 3., 4.]]), np.array([[-np.inf, np.nextafter(3., -np.inf), 4.]])):
        with pytest.raises(AssertionError):
            assert_radio_equal(bad, base)


def test_fixed_full_cost_and_exact_panel_pairing():
    values = FROZEN.expected()
    assert values["complete_episodes"] == 1984 and values["native_steps"] == 507904
    assert values["motion_requests"] == 634880 and values["gate_opportunities"] == 126976
    assert values["neural_forward_ceiling"] == 532480
    assert values["standalone_helper_requests"] == 491520 and values["C_family_requests"] == 143360
    assert values["motion_draws"] == 614400 and values["gate_draws"] == 69632
    assert values["Hdirect_target_vectors"] == 81920
    assert values["native_dense_power_slots"] == 140219475
    assert len(CONTRASTS) == len(set(CONTRASTS)) == 37 and len(PROGRAMS) == 16
    for index in range(32):
        cells = FROZEN.episode_order(index)
        assert len(cells) == len(set(cells)) == 30
        for program in PROGRAMS:
            assert sum(p == program for p, _ in cells) == (1 if program.startswith("C_") else 2)
    force = [FROZEN.force_tick(i) for i in range(512)]
    assert all(force.count(tick) == 8 for tick in range(0, 256, 4))
    with pytest.raises(ValueError):
        replace(FROZEN, training_gate_root=FROZEN.training_motion_root).validate()
    for tick in range(0, 256, 4):
        r = (tick // 4) % 5
        assert gate_uniform(904, 905, tick, r) == gate_uniform(904, 905, tick, r)
        with pytest.raises(ValueError):
            gate_uniform(904, 905, tick, (r + 1) % 5)
