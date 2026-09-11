import json
import math
import time

import pytest

from scripts import run_dish_ground_source_point_a02 as runner


def synthetic_point():
    point = runner.backend._B01PreparedTick()
    state = point.state
    state.initialized = 1; state.schedule = 1; state.route_speed = 4
    state.reflection = 1; state.mask_enabled = 1
    state.p[:] = [128.0, 0.0, 0.0, 256.0]
    point.physics.gx = 0.0; point.physics.gy = 0.0
    point.physics.radio[0] = 6.0; point.physics.radio[1] = -12.0
    return point


def test_derived_samples_follow_float64_equation_and_strict_clearance():
    sample = runner.clearance_sample([0, 0, 0], [128, 256, 90], 1, 8, -1)
    expected_terrain = (135 * math.exp(-(1 / 75)**2 - (-2 / 220)**4)
                        + 55 * math.exp(-((1 - 90) / 35)**2 - ((-2 + 40) / 85)**2))
    assert sample["xyz"] == [1.0, 2.0, 90 / 128]
    assert abs(sample["terrain_height"] - expected_terrain) <= 1e-12
    assert abs(sample["terrain_plus_clearance"] - (expected_terrain + 8)) <= 1e-12
    reverse = runner.clearance_sample([128, 256, 90], [0, 0, 0], 127, 5, -1)
    assert reverse["xyz"] == sample["xyz"]
    assert abs(reverse["terrain_plus_clearance"] - (expected_terrain + 5)) <= 1e-12
    assert not sample["strict_clearance_pass"] and not reverse["strict_clearance_pass"]
    z = runner.terrain(0.0, 0.0) + 8.0
    equal = runner.clearance_sample([0, 0, z], [0, 0, z], 1, 8, 1)
    assert not equal["strict_clearance_pass"]


def test_reading_keeps_noisy_eligibility_separate_from_clearance_witness():
    point = synthetic_point(); original = bytes(point)
    result = runner.read_point(point, runner.study.panel()[0])
    assert bytes(point) == original
    assert result["result"] == "A02-ENDPOINT-CLEARANCE-WITNESS"
    hops = result["receivers"]
    assert hops[0]["native"]["send_margin_eligible"] is True
    assert hops[1]["native"]["send_margin_eligible"] is False
    assert hops[0]["native"]["source_hop_margin_db"] == 6.0
    assert abs(hops[0]["derived"]["source_hop_distance"] - math.sqrt(128**2 + 90**2)) <= 1e-12
    point.physics.camera_present[1] = 1
    assert runner.read_point(point, runner.study.panel()[0])["result"] == "A02-POINT-DISCREPANCY"
    point.physics.camera_present[1] = 0; point.state.tick = 1
    assert runner.read_point(point, runner.study.panel()[0])["result"] == "A02-POINT-DISCREPANCY"
    point.physics.radio[0] = float("nan")
    with pytest.raises(RuntimeError, match="incomplete A02"):
        runner.read_point(point, runner.study.panel()[0])


def test_synthetic_publication_smoke_never_calls_native_point(tmp_path, monkeypatch, capsys):
    started = time.perf_counter()
    def forbidden(*args, **kwargs):
        raise AssertionError("carded reset/native point must never run in tests")
    monkeypatch.setattr(runner.backend, "native_batch_from_rows", forbidden)
    monkeypatch.setattr(runner.study, "seed_master", forbidden)
    point = synthetic_point(); before = bytes(point)
    monkeypatch.setattr(runner, "native_point", lambda: (point, runner.study.panel()[0]))
    receipt = tmp_path / "admission.json"
    receipt.write_text(json.dumps({"passed": True, "physical_floor_pass": True,
                                  "effective_floor_pass": True, "available_physical_bytes": 2**33,
                                  "effective_available_bytes": 2**33}), encoding="utf-8")
    output = tmp_path / "published"
    assert runner.main(["run", "--seed", "11", "--admission", str(receipt), "--out", str(output)]) == 0
    published = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert published == json.loads(capsys.readouterr().out)
    assert published["result"] == "A02-ENDPOINT-CLEARANCE-WITNESS"
    assert published["new_exposure"]["completed_native_ticks"] == 0
    assert published["new_exposure"]["parameter_displacement"] is None
    assert published["wall_seconds"] > 0 and published["measured_cost"]["seconds_per_point"] > 0
    assert published["peak_rss_bytes"] > 0 or published["resources_unmeasured"]
    assert bytes(point) == before
    assert runner.project_cost()["projected_seconds"] == 15
    assert time.perf_counter() - started < 60
