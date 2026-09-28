import json
import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b04 import deployment_readers as dr

AREA = 8000.0
CORNERS = [(300.0, 300.0), (7700.0, 300.0), (7700.0, 7700.0), (300.0, 7700.0)]


def _trace(path, motion, steps=200, n=8, qos_first=None):
    """One npz with four worlds spawned in the four corners; motion(world, agent, corner) -> velocity."""
    payload = {}
    for w, corner in enumerate(CORNERS):
        xyz = np.zeros((steps, n, 3))
        start = np.array(corner) + np.stack([np.arange(n) * 10.0, np.zeros(n)], -1)
        xyz[0, :, :2] = start
        xyz[:, :, 2] = 50.0
        for t in range(1, steps):
            for i in range(n):
                xyz[t, i, :2] = np.clip(xyz[t - 1, i, :2] + motion(w, i, corner), 0.0, AREA)
        qos = np.zeros(steps)
        if qos_first is not None:
            qos[qos_first[w]:] = 0.5
        payload[f"world_{w}_seed"] = np.int64(955001 + w)
        payload[f"world_{w}_own_xyz"] = xyz.astype(np.float32)
        payload[f"world_{w}_qos"] = qos.astype(np.float32)
    np.savez(path, **payload)
    return path


def test_planner_like_headings_have_zero_map_resultant_and_unit_spawn_resultant(tmp_path):
    def toward_centre(w, i, corner):
        direction = np.array([AREA / 2, AREA / 2]) - np.array(corner)
        return 20.0 * direction / np.linalg.norm(direction)
    worlds = dr.load_worlds(_trace(tmp_path / "planner.npz", toward_centre))
    summary = dr.heading_summary(worlds)
    assert summary["worlds"] == 4 and summary["spawn_corners_present"] == ["00", "01", "10", "11"]
    assert max(summary["R_map_per_agent"]) < 1e-6
    assert min(summary["R_spawnrel_per_agent"]) > 0.999
    assert all(abs(a - 45.0) < 1e-6 for a in summary["mean_heading_spawnrel_deg"])
    assert summary["wall_share"] == {"E": 0.0, "W": 0.0, "S": 0.0, "N": 0.0, "none": 1.0}


def test_index_keyed_headings_have_unit_map_resultant(tmp_path):
    def fixed_by_index(w, i, corner):
        angle = np.deg2rad(20.0 + 40.0 * i)
        return 2.0 * np.array([np.cos(angle), np.sin(angle)])
    worlds = dr.load_worlds(_trace(tmp_path / "indexed.npz", fixed_by_index))
    summary = dr.heading_summary(worlds)
    assert min(summary["R_map_per_agent"]) > 0.999
    assert max(summary["R_spawnrel_per_agent"]) < 0.75
    for expected, got in zip([20.0 + 40.0 * i for i in range(8)], summary["mean_heading_map_deg"]):
        assert abs(((got - expected + 180) % 360) - 180) < 1e-3


def test_blob_coherence_spread_and_first_qos(tmp_path):
    same = _trace(tmp_path / "same.npz", lambda w, i, c: np.array([2.0, 0.0]), qos_first=[5, 0, 20, 199])
    rows = [dr.blob_row(w) for w in dr.load_worlds(same)]
    assert [r["first_qos"] for r in rows] == [5, 0, 20, 199]
    assert all(r["cohere_100"] == 1.0 for r in rows)
    assert all(abs(r["spread_100"] - r["spread_t0"]) < 1e-2 for r in rows)  # rigid translation (float32 traces)
    split = _trace(tmp_path / "split.npz", lambda w, i, c: np.array([2.0 if i % 2 else -2.0, 0.0]))
    rows = [dr.blob_row(w) for w in dr.load_worlds(split)]
    assert all(r["cohere_100"] == 0.0 for r in rows)
    assert all(r["spread_300"] > r["spread_t0"] for r in rows)
    still = _trace(tmp_path / "still.npz", lambda w, i, c: np.zeros(2))
    row = dr.blob_row(dr.load_worlds(still)[0])
    assert row["first_qos"] == -1 and np.isnan(row["cohere_100"])
    summary = dr.summarise([row])
    assert summary["cohere_100"]["n"] == 0 and summary["spread_t0"]["sd"] is None


def test_wall_share_counts_parked_uavs(tmp_path):
    def park_east(w, i, corner):
        return np.array([1000.0, 0.0])  # clipped to x = AREA within a few steps
    worlds = dr.load_worlds(_trace(tmp_path / "east.npz", park_east, steps=50))
    shares = dr.wall_shares(worlds, window=50)
    assert shares["E"] > 0.9 and shares["W"] == 0.0 and abs(sum(shares.values()) - 1.0) < 1e-6


def test_cli_writes_records_and_manifest_with_sha256(tmp_path, monkeypatch):
    path = _trace(tmp_path / "L_c00_deterministic.npz", lambda w, i, c: np.array([10.0, 5.0]), qos_first=[1, 2, 3, 4])
    out = tmp_path / "out"
    monkeypatch.chdir(tmp_path)
    assert dr.main(["--group", f"A={path.name}", "--out", str(out), "--windows", "10,50"]) == 0
    blob = json.loads((out / "blob_stat.json").read_text())
    heading = json.loads((out / "heading_stat.json").read_text())
    manifest = json.loads((out / "manifest.json").read_text())
    assert blob["A"]["worlds"] == 4 and "spread_10" in blob["A"]["summary"] and "spread_50" in blob["A"]["summary"]
    assert heading["A"]["worlds"] == 4
    assert manifest["new_episodes"] == 0 and manifest["launcher"] is None
    source = manifest["groups"]["A"]["sources"][0]
    assert source["sha256"] == dr.sha256_of(str(path)) and source["worlds"] == 4
    with pytest.raises(SystemExit):
        dr.main(["--group", "B=nothing_*.npz", "--out", str(out)])
