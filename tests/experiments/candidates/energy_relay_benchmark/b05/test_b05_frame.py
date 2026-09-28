"""SW frame rule, G4 round trips on real layouts (b) and adapter block coverage (f)."""

from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.evaluation import make_eval_config
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.energy_relay_benchmark.b05 import frame as fr
from experiments.candidates.uav_geometric_generalization.b01 import study as dm4_study
from experiments.candidates.uav_geometric_generalization.b01.symmetry import D4
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

# Dev worlds with known spawn corners (team-mean reset own xy): W,S / W,N / E,S / E,N.
CORNER_WORLDS = {955001: "W,S", 955002: "W,N", 955003: "E,S", 955005: "E,N"}
EXPECTED = {"W,S": D4.IDENTITY, "W,N": D4.MIRROR_Y, "E,S": D4.MIRROR_X, "E,N": D4.ROT180}


def _reset(seed):
    env = make_env(make_eval_config(8, 925031), seed)
    try:
        obs, info = env.reset(seed=seed)
        return np.asarray(obs, dtype=np.float32), np.asarray(info["state"], dtype=np.float32)
    finally:
        env.close()


@pytest.fixture(scope="module")
def resets():
    return {seed: _reset(seed) for seed in CORNER_WORLDS}


@pytest.mark.parametrize("xy,corner", [((.1, .1), "W,S"), ((.1, .9), "W,N"), ((.9, .1), "E,S"),
                                       ((.9, .9), "E,N"), ((.5, .1), "E,S"), ((.4999, .5), "W,N")])
def test_sw_rule_constructed(xy, corner):
    obs = np.zeros((8, 365), dtype=np.float32)
    obs[:, :2] = xy
    assert fr.spawn_corner(obs) == corner
    assert fr.sw_frame(obs) is EXPECTED[corner]
    # The mapped team mean lands in SW; DM4's NE rule on the same input is the SW element
    # composed with ROT180 (both rules are the same corner partition).
    mapped, _ = fr.canonical_inputs(obs, np.zeros(306, dtype=np.float32), fr.sw_frame(obs))
    assert fr.spawn_corner(mapped) == "W,S" or .5 in xy   # the centre line maps to itself
    assert dm4_study.northeast_frame(obs) is D4.ROT180.compose(fr.sw_frame(obs))


def test_sw_rule_real_resets_and_group(resets):
    for seed, corner in CORNER_WORLDS.items():
        obs, state = resets[seed]
        assert fr.spawn_corner(obs) == corner
        frame = fr.sw_frame(obs)
        assert frame is EXPECTED[corner]
        canonical, _ = fr.canonical_inputs(obs, state, frame)
        assert fr.spawn_corner(canonical) == "W,S"
    for element in fr.G4:
        assert element.inverse() is element and element.compose(element) is D4.IDENTITY
        for other in fr.G4:
            assert element.compose(other) in fr.G4


def test_identity_is_plain_copy(resets):
    obs, state = resets[955001]
    obs_c, state_c = fr.canonical_inputs(obs, state, D4.IDENTITY)
    assert obs_c is not obs and state_c is not state
    assert obs_c.dtype == obs.dtype and state_c.dtype == state.dtype
    assert obs_c.tobytes() == obs.tobytes() and state_c.tobytes() == state.tobytes()
    action = np.random.default_rng(1).uniform(-1, 1, (8, 4)).astype(np.float32)
    assert fr.physical_actions(action, D4.IDENTITY).tobytes() == action.tobytes()


@pytest.mark.parametrize("seed", sorted(CORNER_WORLDS))
def test_round_trips_on_real_layouts(resets, seed):
    """(b) G4 round trips on the real (8, 365) observation, (306,) state and (8, 4) action."""
    obs, state = resets[seed]
    action = np.random.default_rng(seed).uniform(-1, 1, (8, 4)).astype(np.float32)
    for element in fr.G4:
        obs_c, state_c = fr.canonical_inputs(obs, state, element)
        back_obs, back_state = fr.canonical_inputs(obs_c, state_c, element)   # involution
        # Absolute entries go x -> 1 - x in float32: equal to rounding, not bitwise.
        np.testing.assert_allclose(back_obs, obs, rtol=0, atol=2e-7)
        np.testing.assert_allclose(back_state, state, rtol=0, atol=2e-7)
        # Actions are relative (signed permutation): exact.
        assert fr.physical_actions(fr.canonical_actions(action, element), element).tobytes() \
            == action.tobytes()
        np.testing.assert_array_equal(fr.physical_actions(action, element)[:, 2:], action[:, 2:])
        assert obs_c.dtype == np.float32 and state_c.dtype == np.float32


def test_full_horizontal_touches_only_nonzero_xy():
    """(h) C_SW_FULL rescaling: horizontal only, only when non-zero; z and dock unchanged."""
    action = np.array([[.3, -.4, .7, .9], [0., 0., -.5, .1], [1., 0., .2, 0.],
                       [-.06, .08, 0., .6], [.6, .8, -1., 1.], [1e-6, 0., .3, .3],
                       [-1., -1., 1., 0.], [.2, .1, .0, .0]], dtype=np.float32)
    original = action.copy()
    full = fr.full_horizontal(action)
    np.testing.assert_array_equal(action, original)
    np.testing.assert_array_equal(full[:, 2:], action[:, 2:])
    np.testing.assert_array_equal(full[1, :2], [0., 0.])
    norms = np.linalg.norm(full[:, :2].astype(np.float64), axis=-1)
    moving = np.linalg.norm(action[:, :2], axis=-1) > 0
    np.testing.assert_allclose(norms[moving], 1.0, atol=1e-7)
    direction = action[moving, :2] / np.linalg.norm(action[moving, :2], axis=-1, keepdims=True)
    np.testing.assert_allclose(full[moving, :2], direction, atol=1e-7)
    np.testing.assert_array_equal(full[[2, 4], :2], action[[2, 4], :2])   # already unit
    assert full.dtype == np.float32
    for element in fr.G4:   # the norm commutes with G4: before or after the inverse agree
        np.testing.assert_allclose(fr.physical_actions(fr.full_horizontal(action), element),
                                   fr.full_horizontal(fr.physical_actions(action, element)), atol=0)


def _xy_blocks():
    """(name, start index, absolute) of every xy pair of the local observation."""
    layout = S7S2_LAYOUT
    blocks = [("own", layout.own.start, True), ("nearest_uav", layout.nearest_uav.start + 1, False),
              ("self_state_bs", layout.self_state.stop - 2, False)]
    for name, section, slots, fields in (
        ("users", layout.users, layout.user_slots, layout.user_fields),
        ("uavs", layout.uavs, layout.uav_slots, layout.uav_fields),
        ("bs", layout.bs, layout.bs_slots, layout.bs_fields),
        ("overloaded", layout.overloaded, layout.overloaded_slots, layout.overloaded_fields),
        ("energy_uavs", layout.energy_uavs, layout.energy_uav_records, layout.energy_uav_fields),
        ("energy_stations", layout.energy_stations, layout.energy_station_records,
         layout.energy_station_fields),
    ):
        for slot in range(slots):
            blocks.append((f"{name}[{slot}]", section.start + slot * fields, False))
    return blocks


EXPECTED_XY = {  # element: (x', y') for relative (x, y); absolute adds 1 where the sign flips
    D4.IDENTITY: lambda x, y: (x, y), D4.MIRROR_X: lambda x, y: (-x, y),
    D4.MIRROR_Y: lambda x, y: (x, -y), D4.ROT180: lambda x, y: (-x, -y)}


@pytest.mark.parametrize("element", fr.G4, ids=lambda e: e.name)
def test_adapter_block_coverage(element):
    """(f) Every xy pair of the local observation (the overloaded block included) and of the state
    is mapped by the element; every other entry is unchanged."""
    layout = S7S2_LAYOUT
    rng = np.random.default_rng(955)
    obs = rng.uniform(.05, .45, (8, 365)).astype(np.float32)
    state = rng.uniform(.05, .45, 306).astype(np.float32)
    obs_c, state_c = fr.canonical_inputs(obs, state, element)
    touched = np.zeros(365, dtype=bool)
    for name, start, absolute in _xy_blocks():
        x, y = obs[:, start], obs[:, start + 1]
        ex, ey = EXPECTED_XY[element](x, y)
        if absolute:
            ex = ex + (1.0 if element in (D4.MIRROR_X, D4.ROT180) else 0.0)
            ey = ey + (1.0 if element in (D4.MIRROR_Y, D4.ROT180) else 0.0)
        np.testing.assert_allclose(obs_c[:, start], ex, atol=1e-7, err_msg=name)
        np.testing.assert_allclose(obs_c[:, start + 1], ey, atol=1e-7, err_msg=name)
        touched[start:start + 2] = True
    # The overloaded block (routed_core.py 4188-4232: rel x, rel y, load) is covered, load kept.
    over = layout.overloaded
    assert touched[over.start] and touched[over.start + 1] and not touched[over.start + 2]
    np.testing.assert_array_equal(obs_c[:, over.start + 2::3][:, :3], obs[:, over.start + 2::3][:, :3])
    np.testing.assert_array_equal(obs_c[:, ~touched], obs[:, ~touched])
    assert int(touched.sum()) == 2 * (3 + layout.user_slots + layout.uav_slots + layout.bs_slots
                                      + layout.overloaded_slots + layout.energy_uav_records
                                      + layout.energy_station_records)
    # State: UAV xy (absolute), user xy (absolute) and velocity (relative), BS xy, station xy.
    state_touched = np.zeros(306, dtype=bool)
    absolute_pairs = [slot * 3 for slot in range(8)] + [32 + slot * 6 for slot in range(30)] \
        + [212] + [288 + slot * 7 for slot in range(2)]
    relative_pairs = [32 + slot * 6 + 2 for slot in range(30)]
    for start, absolute in [(s, True) for s in absolute_pairs] + [(s, False) for s in relative_pairs]:
        ex, ey = EXPECTED_XY[element](state[start], state[start + 1])
        if absolute:
            ex = ex + (1.0 if element in (D4.MIRROR_X, D4.ROT180) else 0.0)
            ey = ey + (1.0 if element in (D4.MIRROR_Y, D4.ROT180) else 0.0)
        np.testing.assert_allclose(state_c[start:start + 2], [ex, ey], atol=1e-7)
        state_touched[start:start + 2] = True
    np.testing.assert_array_equal(state_c[~state_touched], state[~state_touched])


def test_adapter_record_pins_file():
    record = fr.adapter_record()
    assert record["adapter"] == "experiments/candidates/uav_geometric_generalization/b01/symmetry.py"
    assert record["adapter_sha256"] == fr._sha256(fr.ADAPTER_PATH)
    assert record["elements"] == {"W,S": "IDENTITY", "W,N": "MIRROR_Y", "E,S": "MIRROR_X",
                                  "E,N": "ROT180"}
