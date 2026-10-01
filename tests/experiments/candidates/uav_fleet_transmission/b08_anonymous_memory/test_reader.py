"""Synthetic reader/admission checks; no native construction, transition or policy replay."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.evaluation import TRACE_FIELDS
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_fleet_transmission.b08_anonymous_memory import capture, contract, metrics, reader, run
from experiments.candidates.uav_fleet_transmission.b08_anonymous_memory.controller import TRACK_DTYPE


def test_declared_addresses_and_balanced_order_are_not_free_cli_choices():
    plan = contract.jobs("scientific")
    assert len(plan) == 96
    assert [p["arm"] for p in plan[:9]] == ["C", "M", "V", "M", "V", "C", "V", "C", "M"]
    assert {p["seed"] for p in plan} == set(range(29880001, 29880033))
    assert all(p["limit"] == 3000 for p in plan)
    engineering = contract.jobs("engineering")
    assert [p["arm"] for p in engineering] == ["REFERENCE", "C", "M", "V"]
    assert {p["seed"] for p in engineering}.isdisjoint({p["seed"] for p in plan})
    assert sum(p["limit"] for p in engineering) == 244


def test_refused_admission_precedes_output_or_scientific_setup(monkeypatch, tmp_path):
    import scripts.hmasd_admission as admission
    def refused(*args, **kwargs):
        raise PermissionError("synthetic admission refusal")
    monkeypatch.setattr(admission, "require_admission", refused)
    out = tmp_path / "not-created"
    with pytest.raises(PermissionError, match="synthetic"):
        run.main(["--out", str(out), "--launch-sha", "a" * 40, "--seed", "29880000",
                  "--phase", "scientific", "--workers", "4", "--reader-workers", "2"])
    assert not out.exists()


def test_early_terminal_endpoints_use_actual_sums_and_fixed_planned_denominator():
    values = np.zeros((3, len(TRACE_FIELDS)))
    values[:, TRACE_FIELDS.index("qos_satisfaction_ratio")] = [.25, .5, .75]
    raw = dict(metric_fields=np.asarray(TRACE_FIELDS), metrics=values, reward=np.array([1., -2., 3.]),
               native_battery=np.full((4, 8), .5), truth_uav_xyz=np.zeros((4, 8, 3)),
               native_consumed_wh=np.zeros((4, 8)), native_charged_wh=np.zeros((4, 8)),
               native_net_charged_wh=np.zeros((4, 8)), native_charging=np.zeros((4, 8), bool),
               native_routes=np.full((4, 8, 9), -1), plan_step=np.array([0]))
    row = metrics.episode_metrics(raw)
    assert row["actual_length"] == 3
    assert row["J_total"] == 2.
    assert row["J_per_planned_step"] == 2. / 3000
    assert row["cumulative_qos"] == 1.5
    assert row["qos_per_planned_step"] == 1.5 / 3000
    assert row["service_equivalent_user_seconds"] == 45.
    assert metrics.longest([False, True, True, False, True]) == 2


def test_paired_uncertainty_keeps_all_signed_worlds():
    result = metrics.paired([-1., 0., 1.], [10, 11, 12])
    assert result["positive"] == result["negative"] == result["ties"] == 1
    assert result["by_world"] == {"10": -1., "11": 0., "12": 1.}
    assert result["mean"] == 0.
    np.testing.assert_allclose(result["t95"], [-2.484137711719546, 2.484137711719546])


def slot_fixture():
    own = np.tile([1000., 1000., 100.], (8, 1))
    users = np.tile([7900., 7900., 1.5], (30, 1))
    users[:3] = [[990., 1000., 1.5], [1010., 1000., 1.5], [1000., 1020., 1.5]]
    obs = np.zeros((8, 365), np.float32)
    records = obs[:, S7S2_LAYOUT.users].reshape(8, 30, 6)
    records[:, :3, :2] = (users[None, :3, :2] - own[:, None, :2]) / 8000.
    records[:, :3, 2] = .5
    return dict(observations=obs[None], truth_uav_xyz=own[None], truth_user_xyz=users[None],
                native_connections=np.zeros((1, 8, 30), bool), native_serviced=np.zeros((1, 30), bool),
                native_serving_set_count=np.zeros((1, 30), np.int16))


def test_truth_binding_uses_original_stable_slot_order_not_spatial_guessing():
    raw = slot_fixture()
    ids, silent = reader.bind_slots(raw, 0)
    np.testing.assert_array_equal(ids[:, :3], np.tile([0, 1, 2], (8, 1)))
    assert silent == 0
    records = raw["observations"][0, :, S7S2_LAYOUT.users].reshape(8, 30, 6)
    records[0, :2] = records[0, [1, 0]]
    with pytest.raises(AssertionError, match="relative position"):
        reader.bind_slots(raw, 0)


def forecast_fixture(ambiguous=False, length=16):
    tracks = np.zeros(1, TRACK_DTYPE)
    tracks["birth"], tracks["last_seen"], tracks["current"], tracks["unambiguous"] = 5, 0, True, True
    tracks["last_xy"], tracks["v"] = [100., 0.], [1., 0.]
    slots = np.full((8, 30), -1, np.int16)
    mapping = np.full((8, 30), -1, np.int64)
    slots[0, 0], mapping[0, 0] = 0, 0
    if ambiguous:
        slots[1, 0], mapping[1, 0] = 1, 0
    events = {name: np.array([5] if name == "new" else [], np.int64) for name in contract.EVENTS}
    trace = dict(tracks=tracks, raw_to_canonical=mapping, kept_flat_indices=np.array([0]),
                 canonical_xy=tracks["last_xy"].copy(), events=events)
    truth = np.zeros((length, 30, 3))
    truth[:, 0, 0] = 600.
    truth[:, 1, 0] = 115.  # Nearest future user is deliberately the wrong identity.
    raw = dict(trace_current_count=np.array([1]), truth_user_xyz=truth,
               plan_users=np.array([[[115., 0.]]]))
    return raw, trace, slots


def test_forecast_errors_keep_origin_identity_ambiguity_and_censoring_denominators():
    raw, trace, slots = forecast_fixture()
    reading = reader.IdentityReading()
    reading.step(raw, 0, trace, slots, 0, "V")
    result = reading.result()
    assert result["forecast_mean_error_m"] == 485.
    assert result["held_mean_error_m"] == 500.
    assert result["counts"]["forecast_evaluated"] == 1
    raw, trace, slots = forecast_fixture(ambiguous=True)
    reading = reader.IdentityReading()
    reading.step(raw, 0, trace, slots, 0, "V")
    assert reading.result()["counts"]["forecast_ambiguous"] == 1
    assert reading.result()["counts"]["forecast_evaluated"] == 0
    raw, trace, slots = forecast_fixture(length=10)
    reading = reader.IdentityReading()
    reading.step(raw, 0, trace, slots, 0, "V")
    assert reading.result()["counts"]["forecast_future_censored"] == 1


def test_harness_end_flag_never_changes_the_native_ending():
    class Recorder:
        native_steps, limit = 60, 61
        submitted = np.zeros((61, 8, 4), np.float32)
        def transition(self, obs, reward, terminated, truncated, info, raw):
            self.native_steps += 1
            self.native_flags = terminated, truncated
    class Adapter:
        env = object()
        def step(self, action):
            return np.zeros((8, 365), np.float32), 0., False, False, {}
    recorder = Recorder()
    wrapper = capture.CaptureEnv(Adapter(), recorder, engineering=True)
    _, _, terminated, truncated, _ = wrapper.step(np.zeros((8, 4), np.float32))
    assert not terminated and truncated
    assert recorder.native_flags == (False, False)


def test_source_binding_preserves_all_selected_original_host_bytes():
    binding = contract.source_binding()
    assert binding["original_source_sha"] == "d6151ff5155d8bf3f3289bba727ee5148f6b76a6"
    assert "envs/pettingzoo/relay/energy_aware.py" in binding["files"]
    assert len(binding["files"]) >= 20


def test_capture_accepts_native_ground_bs_route_label():
    fields = {source: np.zeros(1) for source in capture.RAW_FIELDS.values()}
    fields.update({name: 0. for name in capture.PARAMETERS})
    fields.update(user_serving_sets=[[] for _ in range(30)], height_range=[50., 200.],
                  charging_station_capacity=np.array([4, 4]), routing_protocol="widest_path",
                  enable_soft_handover=False, predictive_handover=False)
    raw = SimpleNamespace(**fields)
    state = {source: np.zeros(1) for source in capture.STATE_FIELDS.values()}
    state["routing_paths"] = {0: ([("uav", 0), ("ground_bs", 0)], 123.)}
    recorder = capture.Recorder(1, "C")
    recorder.boundary(0, np.zeros((8, 365), np.float32), {"state_info": state}, raw)
    np.testing.assert_array_equal(recorder.boundaries["native_routes"][0, 0],
                                  [0, 8, -1, -1, -1, -1, -1, -1, -1])
    assert recorder.boundaries["native_route_capacity"][0, 0] == 123.


def test_directed_route_need_not_have_bidirectional_connection_mask():
    raw = dict(native_routes=np.full((1, 8, 9), -1, np.int16),
               native_route_capacity=np.zeros((1, 8)),
               native_peer_connections=np.zeros((1, 8, 8), bool),
               native_bs_connections=np.zeros((1, 8, 1), bool))
    raw["native_routes"][0, 0, :3] = [0, 1, 8]
    raw["native_route_capacity"][0, 0] = 123.
    reader.check_routes(raw)
    raw["native_route_capacity"][0, 0] = 0.
    with pytest.raises(AssertionError, match="native route topology"):
        reader.check_routes(raw)
    raw["native_route_capacity"][0, 0] = 123.
    raw["native_routes"][0, 0, :3] = [0, 0, 8]
    with pytest.raises(AssertionError, match="native route topology"):
        reader.check_routes(raw)
