"""Block 0 of b04_geometry_probe_a01: legacy invariance and the new reader arithmetic."""
import hashlib
import json

import numpy as np

from experiments.candidates.energy_relay_benchmark.b04 import deployment_readers as dr

# sha256 of the legacy outputs below, computed with deployment_readers.py at 6dfbc9731 (before
# the Block 0 additions); the published b04_deployment_reading_a01 used these functions.
LEGACY_DIGEST = "4b54920c0c9252da106d9ba73211aa2755ca758bd5c068367dd589a4dee5487e"


def legacy_fixture_worlds():
    rng = np.random.RandomState(20260928)
    corners = [(300.0, 300.0), (7700.0, 300.0), (7700.0, 7700.0), (300.0, 7700.0)]
    worlds = []
    for w, corner in enumerate(corners):
        steps, n = 400, 8
        xyz = np.zeros((steps, n, 3))
        xyz[0, :, :2] = np.array(corner) + rng.uniform(-150, 150, size=(n, 2))
        xyz[:, :, 2] = 50.0
        heading = rng.uniform(-np.pi, np.pi, size=n)
        for t in range(1, steps):
            step = 25.0 * np.stack([np.cos(heading + 0.01 * t), np.sin(heading + 0.01 * t)], -1)
            xyz[t, :, :2] = np.clip(xyz[t - 1, :, :2] + step, 0.0, 8000.0)
        qos = np.zeros(steps)
        first = [3, -1, 150, 0][w]
        if first >= 0:
            qos[first:] = 0.25
        worlds.append({"seed": 955001 + w, "xyz": xyz.astype(np.float32).astype(np.float64),
                       "qos": qos.astype(np.float32).astype(np.float64)})
    return worlds


def test_legacy_outputs_are_unchanged():
    worlds = legacy_fixture_worlds()
    rows = [dr.blob_row(w) for w in worlds]
    payload = {"rows": rows, "summary": dr.summarise(rows), "heading": dr.heading_summary(worlds)}
    text = json.dumps(payload, indent=1, sort_keys=True)
    assert hashlib.sha256(text.encode()).hexdigest() == LEGACY_DIGEST


def _world(seed, start, velocity, steps=150, n=2, qos_first=-1):
    xyz = np.zeros((steps, n, 3))
    xyz[0, :, :2] = start
    for t in range(1, steps):
        xyz[t, :, :2] = xyz[t - 1, :, :2] + velocity(t)
    qos = np.zeros(steps)
    if qos_first >= 0:
        qos[qos_first:] = 1.0
    return {"seed": seed, "xyz": xyz, "qos": qos}


def test_first_service_fix_counts_windows_inclusively_and_censors_misses():
    worlds = [_world(1, [[100, 100], [120, 100]], lambda t: 0.0, qos_first=q) for q in (0, 60, 61, -1)]
    summary = dr.first_service_summary(worlds)
    assert summary["never_served"] == 1 and summary["served"] == 3
    assert summary["mean_served"] == round((0 + 60 + 61) / 3, 3)
    assert summary["censored_mean"] == round((0 + 60 + 61 + 150) / 4, 3)
    assert summary["served_within_60"] == {"count": 2, "share_of_served": round(2 / 3, 4), "share_of_all": 0.5}
    assert summary["served_within_120"]["count"] == 3
    conditional = dr.conditional_first_service(worlds, {1: 0})
    assert conditional["joined_worlds"] == 4 and conditional["no_user_in_access_range_t0_worlds"] == 4


def test_stratified_headings_exclusion_prewall_and_corner_weights():
    east = lambda t: np.array([[10.0, 0.0], [0.1, 0.0]])        # agent 1 moves 14.9 m: excluded
    worlds = [_world(1, [[100, 100], [100, 200]], east), _world(2, [[7900 - 100, 100], [7800, 200]], east)]
    samples, corners = dr.heading_samples(worlds)
    assert corners.tolist() == [[0, 0], [1, 0]]
    assert np.allclose(samples["net"][:, 0], 0.0) and np.isnan(samples["net"][:, 1]).all()
    assert np.allclose(samples["stepwise"][:, 0], 0.0)
    # world 2 agent 0 starts 200 m from the east wall: contact (<= 60 m) at x >= 7940 -> t = 14
    assert np.isclose(samples["net_prewall"][1, 0], 0.0) and np.isclose(samples["net_prewall"][0, 0], 0.0)
    summary = dr.stratified_heading_summary(worlds)
    net = summary["net"]
    assert net["all"]["n"] == 2 and net["excluded"] == 2 and net["all"]["R_map"] == 1.0
    assert net["all"]["R_spawnrel"] == 0.0                     # east corner mirrored to the west
    assert net["by_corner"]["10"]["n"] == 1 and net["corner_equal_weight"]["corners"] == 2
    assert net["by_index"]["1"]["n"] == 0
    near_wall = [_world(3, [[30, 1000], [4000, 4000]], lambda t: np.array([[10.0, 0.0], [10.0, 0.0]]))]
    prewall = dr.stratified_heading_summary(near_wall)["net"]["pre_wall_contact"]
    assert prewall["by_index"]["0"]["n"] == 0 and prewall["by_index"]["1"]["n"] == 1


def test_speed_saturation_uses_normal_mode_steps_only():
    world = _world(1, [[100, 100], [100, 200]], lambda t: np.array([[30.0, 0.0], [5.0, 0.0]]), steps=11)
    modes = np.zeros((11, 2), dtype=bool)
    modes[:5, 0] = True
    result = dr.speed_saturation([world], [modes])
    assert result["normal_uav_steps"] == 5 + 10 and result["saturated_uav_steps"] == 5
    assert result["share"] == round(5 / 15, 4)


def test_block0_group_list_adds_c02_to_the_published_groups():
    names = [name for name, _ in dr.BLOCK0_GROUPS]
    assert "SET_c02_det" in names and len(names) == 9
