"""Finite pure saved-record checks and explicitly labeled deterministic doubles.

No real controller/model/native construction, RF, forecast, tracking or shield
call occurs in these tests. DM's controller suite buys the real search/replay.
"""
import json
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_fleet_transmission.b08_anonymous_memory.controller import TRACK_DTYPE
from experiments.candidates.uav_fleet_transmission.b09_service_prediction import contract, metrics, reader
from experiments.candidates.uav_fleet_transmission.b09_service_prediction.trace import CANDIDATE_DTYPE, empty_candidate


DOUBLE_CALLS = dict(constructors=0, proposals=0, closes=0)
REAL_CALL_COST = dict(model_constructions=0, candidate_forecasts=0, model_rf_calls=0,
                      joint_forecast_ticks=0, proposals=0, associations=0, shield_calls=0)


def candidate(*, complete=True, ticks=30, rf_completed=3, rf_started=None):
    row = empty_candidate(0, 0, 0, np.tile([1000., 1000., 100.], (8, 1)), 1)
    row["ticks"] = ticks
    row["rf_completed"] = rf_completed
    row["rf_started"] = rf_completed if rf_started is None else rf_started
    row["completed"] = complete
    if complete:
        row["score"] = 1.
        row["selected"] = row["accepted"] = True
    return np.array([row], dtype=CANDIDATE_DTYPE)


@pytest.mark.parametrize("field", ["targets", "xyz", "battery", "qos", "score", "tick_digest", "rf_digest", "selected", "accepted"])
def test_rejects_every_saved_candidate_output_tamper_without_model_calls(field):
    actual = candidate()
    saved = actual.copy()
    value = saved[field]
    if value.dtype.kind == "b":
        value.flat[0] = not value.flat[0]
    else:
        value.flat[0] += 1
    with pytest.raises(AssertionError, match=field):
        reader.compare_candidate_prefix(actual, saved)
    assert not any(REAL_CALL_COST.values())


@pytest.mark.parametrize("name", ["plan_bs", "plan_bs_source", "trace_tracks", "trace_slot_merge", "decision_targets_xyz", "plan_prediction_xy"])
def test_rejects_saved_bs_track_target_and_projection_tamper(name):
    if name == "trace_tracks":
        expected = np.zeros(30, TRACK_DTYPE)
        saved = expected.copy()
        saved["birth"][0] = 10
    else:
        shapes = dict(plan_bs=(2,), plan_bs_source=(), trace_slot_merge=(8, 30),
                      decision_targets_xyz=(8, 3), plan_prediction_xy=(3, 30, 2))
        expected = np.zeros(shapes[name])
        saved = expected.copy()
        saved.flat[0] = 1
    with pytest.raises(AssertionError, match=name):
        reader.compare_records({name: np.array([saved])}, {name: expected}, 0, "actual record")


def test_bad_prefix_rejected_before_even_a_controller_double_is_created(monkeypatch):
    records = candidate(complete=False, ticks=30, rf_completed=1)
    records = np.concatenate([records, candidate()])
    monkeypatch.setattr(reader, "make_controller", lambda arm: pytest.fail("constructor after invalid prefix"))
    with pytest.raises(AssertionError, match="final prefix"):
        reader.replay_episode({"candidate_records": records}, {"arm": "F", "status": "failed"}, "engineering")


def test_partial_rf_attempt_is_preserved_without_repeating_it():
    recorded = candidate(complete=False, ticks=30, rf_completed=1, rf_started=2)
    replayed = recorded.copy()
    replayed["rf_started"] = 1
    reader.compare_candidate_prefix(replayed, recorded)
    replayed["rf_completed"] = 2
    with pytest.raises(AssertionError, match="rf_completed"):
        reader.compare_candidate_prefix(replayed, recorded)


def test_interrupted_final_plan_flags_are_preserved_without_claiming_rejection():
    recorded = candidate()
    recorded["selected"] = recorded["accepted"] = False
    actual = recorded.copy()
    actual["accepted"] = True
    with pytest.raises(AssertionError, match="accepted"):
        reader.compare_candidate_prefix(actual, recorded)
    reader.compare_candidate_prefix(actual, recorded, unverified_ranking_step=0)
    actual["rf_digest"][0, 0, 0] = 1
    with pytest.raises(AssertionError, match="rf_digest"):
        reader.compare_candidate_prefix(actual, recorded, unverified_ranking_step=0)


class PrefixControllerDouble:
    """Only the reader boundary protocol, with no actual model/controller work."""
    def __init__(self):
        DOUBLE_CALLS["constructors"] += 1
        self.heuristic = SimpleNamespace(calls=0)
        self.candidates = np.empty(0, CANDIDATE_DTYPE)
        self.counters = {}

    def reset(self):
        pass

    def propose(self, obs, truth, tick, done, modes):
        DOUBLE_CALLS["proposals"] += 1
        assert tick == 0
        assert len(self.replay_prefix) == 1
        self.candidates = self.replay_prefix.copy()
        self.candidates["rf_started"] = self.candidates["rf_completed"]
        self.counters = dict(proposals=1, candidate_forecasts=1, joint_forecast_ticks=3,
                             joint_forecast_ticks_completed=3)
        raise reader.ReplayBoundary("deterministic double: recorded nominal prefix exhausted")

    def audit_arrays(self):
        return {"candidate_records": self.candidates}

    def close(self):
        DOUBLE_CALLS["closes"] += 1


def test_incomplete_prefix_replay_stops_once_and_reports_unreplayed_attempt(monkeypatch):
    records = candidate(complete=False, ticks=3, rf_completed=0)
    raw = dict(candidate_records=records, recorded_decision_steps=np.asarray(0),
               observations=np.zeros((1, 8, 365), np.float32), plan_step=np.empty(0, np.int32))
    counts = dict(proposals=1, candidate_forecasts=1, joint_forecast_ticks=4,
                  joint_forecast_ticks_completed=3)
    monkeypatch.setattr(reader, "make_controller", lambda arm: PrefixControllerDouble())
    before = dict(DOUBLE_CALLS)
    result = reader.replay_episode(raw, dict(arm="F", status="failed", policy_counts=counts), "engineering")
    assert result["status"] == "partial-prefix-verified"
    assert result["verified_actual_proposals"] == result["verified_feedback_calls"] == 0
    assert result["inflight_proposals_replayed"] == 1
    assert result["unreplayed_attempted_or_uncertain_counts"] == {"joint_forecast_ticks": 1}
    assert result["candidate_records_checked"] == 1
    assert DOUBLE_CALLS == {key: value+1 for key, value in before.items()}
    assert not any(REAL_CALL_COST.values())


def test_no_candidate_evidence_does_not_authorize_inflight_proposal(monkeypatch):
    monkeypatch.setattr(reader, "make_controller", lambda arm: PrefixControllerDouble())
    raw = dict(candidate_records=np.empty(0, CANDIDATE_DTYPE), recorded_decision_steps=np.asarray(0),
               observations=np.zeros((1, 8, 365), np.float32), plan_step=np.empty(0, np.int32))
    before = DOUBLE_CALLS["proposals"]
    result = reader.replay_episode(raw, dict(arm="F", status="failed", policy_counts={"proposals": 1}), "engineering")
    assert DOUBLE_CALLS["proposals"] == before
    assert result["unreplayed_attempted_or_uncertain_counts"] == {"proposals": 1}


def forecast_fixture(*, arm="F", ambiguous=False, unbound=False, length=31, remembered=False):
    tracks = np.zeros(1, TRACK_DTYPE)
    tracks["birth"], tracks["last_seen"] = 5, -5 if remembered else 0
    tracks["current"], tracks["unambiguous"] = not remembered, True
    tracks["last_xy"], tracks["v"] = [100., 0.], [1., 0.]
    slots = np.full((8, 30), -1, np.int16)
    mapping = np.full((8, 30), -1, np.int64)
    if not remembered:
        # An all-missing merge has no current point; explicit singleton binding
        # is supplied below for remembered/unbound fixture cases.
        slots[0, 0], mapping[0, 0] = 0, 0
        if ambiguous:
            slots[1, 0], mapping[1, 0] = 1, 0
    events = {name: np.array([5] if name == "new" and not remembered else [], np.int64)
              for name in contract.EVENTS}
    trace = dict(tracks=tracks, raw_to_canonical=mapping,
                 kept_flat_indices=np.array([], np.int64) if remembered else np.array([0]),
                 canonical_xy=np.empty((0, 2)) if remembered else tracks["last_xy"].copy(), events=events)
    truth = np.zeros((length, 30, 3))
    truth[:, 0, 0] = 600.
    truth[:, 1, 0] = 110.  # Nearest future user is deliberately the wrong identity.
    current_x = 105. if remembered else 100.
    future_x = [current_x]*3 if arm == "H" else [current_x+tau for tau in contract.SAMPLES]
    raw = dict(trace_current_count=np.array([0 if remembered else 1]), truth_user_xyz=truth,
               plan_users=np.array([[[current_x, 0.]]]),
               plan_prediction_xy=np.array([[[[value, 0.]] for value in future_x]]))
    reading = reader.IdentityReading()
    if remembered:
        reading.bindings = {5: frozenset() if unbound else frozenset({0})}
    return raw, trace, slots, reading


@pytest.mark.parametrize("arm", ["H", "F"])
def test_origin_bound_10_20_30_predictions_use_actual_arm_and_common_current_baseline(arm):
    raw, trace, slots, reading = forecast_fixture(arm=arm, remembered=True)
    reading.step(raw, 0, trace, slots, 0, arm)
    result = reading.result()
    for tau in contract.SAMPLES:
        stats = result["per_tau"][str(tau)]
        assert stats["forecast_mean_error_m"] == (495. if arm == "H" else 495.-tau)
        assert stats["current_mean_error_m"] == 495.
        assert stats["last_seen_mean_error_m"] == 500.
        assert stats["remembered"] == stats["evaluated"] == 1
        assert stats["worst_rows"][0]["user"] == 0
    assert result["combined"]["evaluated"] == 3
    assert result["combined"]["current_sum_m"] == 1485.
    assert result["combined"]["better"] == (0 if arm == "H" else 3)


def test_forecast_ambiguity_unbound_and_per_tau_censoring_are_not_dropped():
    raw, trace, slots, reading = forecast_fixture(ambiguous=True)
    reading.step(raw, 0, trace, slots, 0, "F")
    assert reading.result()["combined"]["ambiguous"] == 3
    raw, trace, slots, reading = forecast_fixture(remembered=True, unbound=True)
    reading.step(raw, 0, trace, slots, 0, "F")
    assert reading.result()["combined"]["unbound"] == 3
    raw, trace, slots, reading = forecast_fixture(length=21)
    reading.step(raw, 0, trace, slots, 0, "F")
    result = reading.result()
    assert result["combined"]["origins"] == 3
    assert result["combined"]["evaluated"] == 2
    assert result["per_tau"]["30"]["censored"] == 1
    assert result["per_tau"]["30"]["forecast_rmse_m"] is None


def test_pooling_uses_error_sums_and_counts_instead_of_mean_of_world_means():
    first, second = reader.empty_forecast_stats(), reader.empty_forecast_stats()
    row = dict(nonzero_velocity=True, remembered=False, forecast_error_m=1.)
    reader.update_forecast_stats(first, 1., 2., 3., row)
    for unused in range(3):
        reader.update_forecast_stats(second, 5., 6., 7., dict(row, forecast_error_m=5.))
    result = reader.finish_forecast_stats(reader.pool_forecast_stats([first, second]))
    assert result["evaluated"] == 4
    assert result["forecast_mean_error_m"] == 4.
    assert result["forecast_rmse_m"] == np.sqrt(19.)


def test_first_and_later_target_changes_preserve_equal_nan_fields():
    a = np.zeros((4, 8, 3))
    a[:, 0, 0] = np.nan
    b = a.copy()
    b[2:, 1, 2] = 25.
    result = reader.change_reading(a, b)
    assert result["first_difference"] == result["first_later_difference"] == 2
    assert result["different_rows"] == result["different_later_rows"] == 2
    assert reader.first_difference(a, a.copy()) is None


def test_directed_native_route_does_not_require_bidirectional_masks():
    raw = dict(native_routes=np.full((1, 8, 9), -1, np.int16),
               native_route_capacity=np.zeros((1, 8)),
               native_peer_connections=np.zeros((1, 8, 8), bool),
               native_bs_connections=np.zeros((1, 8, 1), bool))
    raw["native_routes"][0, 0, :3] = [0, 1, 8]
    raw["native_route_capacity"][0, 0] = 123.
    reader.check_routes(raw)
    raw["native_routes"][0, 0, :3] = [0, 0, 8]
    with pytest.raises(AssertionError, match="native route topology"):
        reader.check_routes(raw)


def test_post_replay_user_path_failure_never_counts_owned_episode_as_inflight(monkeypatch, tmp_path):
    """A replay-result double exercises accounting; no policy/model is called."""
    (tmp_path / "raw").mkdir()
    (tmp_path / "reading_raw").mkdir()
    rows = []
    seed = contract.ENGINEERING_SEED
    for arm, offset in (("H", 0.), ("F", 1.)):
        arrays = dict(truth_user_xyz=np.full((2, 30, 3), offset),
                      truth_uav_xyz=np.zeros((2, 8, 3)), truth_bs_xyz=np.zeros((2, 1, 3)),
                      truth_station_xyz=np.zeros((2, 2, 3)), submitted=np.zeros((1, 8, 4)),
                      proposed=np.zeros((1, 8, 4)), decision_targets_xyz=np.zeros((1, 8, 3)),
                      observations=np.zeros((2, 8, 365), np.float32))
        path = tmp_path / "raw" / (arm + ".npz")
        np.savez(path, **arrays)
        rows.append(dict(arm=arm, seed=seed, status="completed", actual_length=1,
                         raw=dict(path="raw/" + path.name, **contract.identity(path))))
    monkeypatch.setattr(reader, "check_native", lambda *args: {"native_transitions_checked": 1})

    def replay_result_double(raw, row, phase, progress):
        counts = {"model_constructions": 1, "candidate_forecasts": 4}
        progress(dict(policy_counts=counts, shield_calls=1))
        return dict(policy_counts=counts, verified_actual_proposals=1, verified_feedback_calls=1,
                    shield_calls=1, status="verified", identity_reading=reader.IdentityReading().result())

    monkeypatch.setattr(reader, "replay_episode", replay_result_double)
    result = reader.read_world((dict(seed=seed, job_key=str(seed)), rows, str(tmp_path), "engineering"))
    assert result["status"] == "failed"
    assert "user path" in result["error"]
    assert len(result["episodes"]) == 2
    assert not result["inflight"]
    totals = contract.sum_counts(e["replay"]["policy_counts"] for e in result["episodes"])
    assert totals == {"model_constructions": 2, "candidate_forecasts": 8}
    assert not any(REAL_CALL_COST.values())


def test_manifest_tamper_rejected_before_reader_pool_or_model_setup(monkeypatch, tmp_path):
    (tmp_path / "raw").mkdir()
    binding = {"files": {}}
    monkeypatch.setattr(reader, "source_binding", lambda: binding)
    config = dict(object=contract.OBJECT, phase="engineering", launch_sha="a"*40,
                  jobs=contract.jobs("engineering"), source_binding=binding)
    summary = dict(object=contract.OBJECT, status="incomplete", launch_sha="a"*40)
    for name, value in (("config.json", config), ("summary.json", summary), ("perworld.json", [])):
        (tmp_path / name).write_text(json.dumps(value))
    manifest = dict(object=contract.OBJECT, launch_sha="a"*40,
                    artifacts={"config.json": contract.identity(tmp_path / "config.json")}, raw={})
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "config.json").write_text(json.dumps(config) + " ")
    monkeypatch.setattr(reader, "ProcessPoolExecutor", lambda **kwargs: pytest.fail("pool after tampered source"))
    with pytest.raises(AssertionError, match="artifact changed"):
        reader.read_result(tmp_path, 1)
    assert not (tmp_path / "reading_raw").exists()


def test_individual_user_and_energy_summaries_are_bound_to_observed_native_values():
    from experiments.candidates.energy_relay_benchmark.b01.evaluation import TRACE_FIELDS
    n = 3
    delivered = np.zeros((n+1, 30))
    delivered[1:, 0] = [0., 1e6, .5e6]
    raw = dict(metric_fields=np.array(TRACE_FIELDS), metrics=np.zeros((n, len(TRACE_FIELDS))),
               reward=np.zeros(n), native_battery=np.full((n+1, 8), .5),
               truth_uav_xyz=np.zeros((n+1, 8, 3)), native_consumed_wh=np.zeros((n+1, 8)),
               native_charged_wh=np.zeros((n+1, 8)), native_net_charged_wh=np.zeros((n+1, 8)),
               native_charging=np.zeros((n+1, 8), bool), native_waiting=np.zeros((n+1, 8), int),
               native_routes=np.full((n+1, 8, 9), -1), plan_step=np.array([0]),
               native_delivered_bps=delivered, native_demand_bps=np.full((n+1, 30), 1e6))
    row = metrics.episode_metrics(raw)
    reader.check_individual_summaries(raw, row)
    assert row["individual_service"]["cumulative_qos_seconds"][0] == 1.5
    assert row["individual_service"]["qos_per_planned_step"][0] == 1.5/3000
    assert row["individual_service"]["qos_per_actual_step"][0] == .5
    assert row["individual_service"]["longest_observed_zero_delivery_spell"][1] == 3
    row["individual_service"]["qos_per_planned_step"][0] = .5
    with pytest.raises(AssertionError, match="qos_per_planned_step"):
        reader.check_individual_summaries(raw, row)
