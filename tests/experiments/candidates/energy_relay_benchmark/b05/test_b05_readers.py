"""(i) b05 readers on a tiny synthetic trace: inward displacement sign, decomposition, persistence."""

from __future__ import annotations

import json

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b05 import readers as rd

T, N = 121, 2


def _world(start, velocity, *, proposal=.5, submitted=.4, mode_steps=(), zigzag=False):
    """Two UAVs from ``start`` [N, 2] m with a constant per-step velocity [N, 2] m (UAV 1 zigzags
    when ``zigzag``: +v / -v alternating, zero net)."""
    xyz = np.zeros((T, N, 3), dtype=np.float32)
    xyz[0, :, :2] = start
    for t in range(1, T):
        step = np.array(velocity, dtype=np.float64)
        if zigzag:
            step[1] = step[1] * (1 if t % 2 else -1)
        xyz[t, :, :2] = xyz[t - 1, :, :2] + step
    xyz[..., 2] = 100.0
    mode = np.zeros((T, N), dtype=np.float32)
    for t in mode_steps:
        mode[t] = 1.0
    prop = np.zeros((T, N, 4), dtype=np.float32)
    prop[..., 0] = proposal
    sub = np.zeros((T, N, 4), dtype=np.float32)
    sub[..., 0] = submitted
    qos = np.zeros(T, dtype=np.float32)
    qos[30:] = .5
    return {"own_xyz": xyz, "mode": mode, "proposal": prop, "submitted": sub, "qos": qos}


def _write(tmp_path, worlds, seeds, access):
    (tmp_path / "panels").mkdir()
    (tmp_path / "traces").mkdir()
    arrays = {}
    for index, (world, seed) in enumerate(zip(worlds, seeds)):
        arrays[f"world_{index}_seed"] = np.asarray(seed, dtype=np.int64)
        for key, value in world.items():
            arrays[f"world_{index}_{key}"] = value
    np.savez_compressed(tmp_path / "traces" / "P.npz", **arrays)
    rows = [{"seed": s, "qos_per_step": .3 + .01 * i, "raw_native_J": 1.0 * i,
             "boundary_share_normal_mode": .1 * i, "users_in_access_range_t0": a,
             "first_service_step": 30, "episode_minimum_battery_ratio": .5,
             "return_constraint_cost_sum": 0.0}
            for i, (s, a) in enumerate(zip(seeds, access))]
    (tmp_path / "panels" / "P.json").write_text(json.dumps({"worlds": rows}))
    return tmp_path / "panels" / "P.json", rows


def test_inward_displacement_sign_and_corner():
    # SW spawn at (100, 100): moving +x+y is inward, -x is outward.
    xyz = _world([[100, 100], [100, 100]], [[10, 10], [-1, 0]])["own_xyz"]
    inward = rd.inward_displacement(xyz, steps=100)
    assert inward[0] == pytest.approx(1000 * np.sqrt(2), rel=1e-5)
    assert inward[1] == pytest.approx(-100 / np.sqrt(2), rel=1e-4)
    assert rd.corner_label(xyz) == "W,S"
    ne = _world([[7900, 7900], [7900, 7800]], [[-10, -10], [0, 0]])["own_xyz"]
    assert rd.corner_label(ne) == "E,N"
    assert rd.inward_displacement(ne)[0] > 0 and rd.inward_displacement(ne)[1] == 0


def test_readers_on_synthetic_panel(tmp_path):
    worlds = [
        # W,S: UAV 0 straight inward at 10 m/step (free space after the first steps),
        # UAV 1 zigzags along x at a wall (x stays near 30 m): persistence ~ 0, displacement 5 m.
        _world([[200, 200], [30, 4000]], [[10, 0], [0, 5]], zigzag=True, mode_steps=range(5)),
        # E,N: both still at the NE wall corner.
        _world([[7990, 7990], [7995, 7995]], [[0, 0], [0, 0]], proposal=.0, submitted=.0),
    ]
    panel, _ = _write(tmp_path, worlds, [11, 12], [0, 3])
    reading, loaded = rd.read_panel(panel)
    assert [w["corner"] for w in loaded] == ["W,S", "E,N"]
    inward = reading["inward"]
    assert inward["by_corner"]["W,S"]["n"] == 2 and inward["by_corner"]["E,N"]["median"] == 0.0
    assert inward["by_corner"]["W,S"]["q75"] > 0
    full = reading["decomposition"]["full"]["pooled"]
    # Normal-mode free-space steps belong to UAV 0 of world 11 (t >= 5, beyond the first 60 m).
    free = full["normal_free"]
    assert free["actual_displacement_m"]["median"] == pytest.approx(10.0)
    assert free["raw_proposal_norm"]["median"] == pytest.approx(.5)
    assert free["post_shield_norm"]["median"] == pytest.approx(.4, rel=1e-6)
    wall = full["all_wall"]
    assert wall["actual_displacement_m"]["median"] in (0.0, 5.0)
    assert full["all"]["uav_steps"] == 2 * 2 * (T - 1)
    assert full["normal_free"]["uav_steps"] + full["normal_wall"]["uav_steps"] == 2 * 2 * (T - 1) - 5 * 2
    window = reading["decomposition"]["window"]
    assert window["window"] == rd.DECOMPOSITION_WINDOW   # trace shorter than the window
    persistence = reading["persistence"]["full"]
    by = persistence["all_windows"]["by_corner"]["W,S"]
    # UAV 0 straight: R = 1 in every window; UAV 1 zigzag: R = 0.  E,N never moves: no window.
    assert by["n"] == 2 * ((T - 1) // rd.PERSISTENCE_STEPS)
    assert by["q75"] == pytest.approx(1.0) and by["q25"] == pytest.approx(0.0, abs=1e-12)
    assert persistence["all_windows"]["by_corner"]["E,N"]["n"] == 0
    normal = persistence["normal_mode_windows"]["by_corner"]["W,S"]["n"]
    assert normal == by["n"] - 2   # the first window holds the shield-mode steps
    assert reading["first_service"]["served"] == 2
    assert reading["first_service_conditional"]["no_user_in_access_range_t0_worlds"] == 1
    assert reading["speed_saturation"]["saturated_uav_steps"] == 0


def test_pairs_by_corner_and_references(tmp_path):
    worlds = [_world([[200, 200], [300, 300]], [[10, 0], [0, 10]]),
              _world([[7990, 7990], [7995, 7995]], [[0, 0], [0, 0]])]
    (tmp_path / "a").mkdir()
    panel, _ = _write(tmp_path / "a", worlds, [21, 22], [1, 1])
    reference = tmp_path / "block2.json"
    reference.write_text(json.dumps({"local_id_rows": [
        {"seed": 21, "qos_per_step": .25, "raw_native_J": 0.0, "boundary_share_normal_mode": .0,
         "first_service_step": 40, "episode_minimum_battery_ratio": .4,
         "return_constraint_cost_sum": 1.0},
        {"seed": 22, "qos_per_step": .40, "raw_native_J": 2.0, "boundary_share_normal_mode": .5,
         "first_service_step": None, "episode_minimum_battery_ratio": .6,
         "return_constraint_cost_sum": 0.0}]}))
    payload = rd.read(tmp_path / "out", panels={"C": str(panel)}, references={"R": str(reference)},
                      pairs={"F_same_evaluator": ("C", "R")})
    pair = payload["pairs"]["F_same_evaluator"]
    qos = pair["metrics"]["qos_per_step"]
    assert qos["overall"]["n"] == 2
    assert qos["by_corner"]["W,S"]["mean"] == pytest.approx(.30 - .25)
    assert qos["by_corner"]["E,N"]["mean"] == pytest.approx(.31 - .40)
    assert pair["worlds_a_below_b_qos"] == [22]
    assert pair["metrics"]["first_service_step"]["overall"]["n"] == 1   # None excluded
    assert pair["boundary_share_normal_mode_by_corner"]["b"]["E,N"]["mean"] == .5
    assert pair["b_source"]["traced"] is False
    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert manifest["new_episodes"] == 0 and set(manifest["sources"]) == {"C", "R"}
    with pytest.raises(FileExistsError):
        rd.read(tmp_path / "out", panels={"C": str(panel)})
