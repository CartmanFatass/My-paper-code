"""B03 credit-diagnostics: removal probe observer, probe pieces, readings, bit identity, runner."""

from __future__ import annotations

import copy
import json
import math
import time
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.native import B01Spec, heuristic_params
from experiments.candidates.energy_relay_benchmark.b03 import credit_diagnostics as cd
from experiments.candidates.energy_relay_benchmark.b03 import stake_sizing as ss
from scripts import run_energy_relay_benchmark_b03 as entry

H1 = heuristic_params("H1", B01Spec())
VOLATILE = {"wall_seconds", "worker_peak_rss_kib"}
CREDIT_FIELDS = {"probe_every", "probe_steps", "baseline_mismatch_steps", "probe_wall_mean_s",
                 "collection_wall_mean_s"}


def test_declared_constants_and_reuse():
    assert (cd.CREDIT_PHASE, cd.PROBE_EVERY, cd.PROBE_MODE) == ("credit-diagnostics", 10,
                                                                "hungarian")
    assert (cd.BIT_IDENTITY_WORLD, cd.SPARSITY_THRESHOLD) == (955001, 0.01)
    assert cd.STAKE_WORLDS is ss.STAKE_WORLDS and cd.RECORDED_PANEL == ss.RECORDED_PANEL
    assert cd.consistency_check is ss.consistency_check and cd.paired_block is ss.paired_block
    assert cd.RULE_THRESHOLDS == {"relay_hop_share": (0.10, 0.25), "relay_ratio_R1": 2.0,
                                  "sparsity_available": 0.80}


# ----------------------------------------------------------------------------- live observer

def _snapshot(raw):
    return {"routing_paths": copy.deepcopy(raw.routing_paths),
            "uav_battery_ratios": raw.uav_battery_ratios.copy(),
            "user_serving_sets": copy.deepcopy(raw.user_serving_sets),
            "connections": raw.connections.copy(),
            "uav_connections": raw.uav_connections.copy(),
            "uav_positions": raw.uav_positions.copy(),
            "last_delivered_traffic_bps": raw.last_delivered_traffic_bps.copy(),
            "rng": raw.np_random.get_state()[1].copy()}


def _assert_same_snapshot(before, after):
    assert before["routing_paths"] == after["routing_paths"]
    assert before["user_serving_sets"] == after["user_serving_sets"]
    for key in ("uav_battery_ratios", "connections", "uav_connections", "uav_positions",
                "last_delivered_traffic_bps", "rng"):
        np.testing.assert_array_equal(before[key], after[key], err_msg=key)


def test_observer_on_a_tiny_world(tiny_config):
    env = ev.make_env(tiny_config, 955001)
    try:
        env.reset(seed=955001)
        raw = env.env
        observer = cd.RemovalProbeObserver(env, probe_every=2)
        assert observer.raw is raw and observer.attach(None).__enter__() is None
        controller = SimpleNamespace(heuristic=SimpleNamespace(last_plan=None))
        rng = np.random.default_rng(5)
        for step in range(7):
            if step == 3:
                raw.uav_battery_ratios[5] = 0.0   # UAV 5 unavailable from step 3 on
            action = rng.uniform(-1, 1, size=(8, 4)).astype(np.float32)
            action[:, 3] = 0.0
            env.step(action)
            before = _snapshot(raw)
            observer.on_step(t=step, controller=controller, observations_t=None, state_t=None)
            _assert_same_snapshot(before, _snapshot(raw))
            # the stored backhaul is the routing capacity of the path the reward used
            backhaul = raw.last_backhaul_capacities_bps
            for uav in np.flatnonzero(backhaul > 0):
                assert raw.routing_paths[int(uav)][1] == backhaul[uav]
        arrays = observer.as_arrays()
    finally:
        env.close()
    np.testing.assert_array_equal(arrays["probe_step"], [0, 2, 4, 6])
    for key in cd.UAV_KEYS:
        assert arrays[key].shape == (4, 8), key
    for key in cd.STEP_KEYS:
        assert arrays[key].shape == (4,), key
    assert arrays["collection_wall_s"].shape == (7,)
    assert math.isnan(arrays["collection_wall_s"][0])
    assert np.all(np.isfinite(arrays["collection_wall_s"][1:]))
    assert np.all(arrays["probe_wall_s"] > 0)
    # the deep-copy recompute reproduces the reward's QoS bitwise at every probe
    assert np.array_equal(arrays["qos_copy_baseline"], arrays["qos_live"])
    assert observer.baseline_mismatch_steps == 0
    unavailable = ~arrays["available"]
    assert unavailable[2:, 5].all() and not unavailable[:2, 5].any()
    assert np.all(arrays["D"][unavailable] == 0.0)
    np.testing.assert_array_equal(arrays["qos_removed"][unavailable],
                                  np.broadcast_to(arrays["qos_copy_baseline"][:, None],
                                                  unavailable.shape)[unavailable])
    np.testing.assert_array_equal(arrays["D"], arrays["qos_live"][:, None] - arrays["qos_removed"])
    assert not arrays["relay_slot"].any()      # no plan
    assert not arrays["path_hops"][unavailable].any()
    assert np.all(arrays["served_traffic_bps"].sum(axis=1)
                  <= arrays["total_delivered_bps"] * (1 + 1e-12))


def test_credit_task_equals_stake_task_and_probes_every_kth_step(tmp_path):
    """The observer does not move the trajectory: row and arrays equal the stake worker's."""
    common = dict(seed=955001, params=PRODUCTION_PARAMS, horizon=40, policy_seed=925031,
                  threads=1, heuristic=H1, log_dir=str(tmp_path))
    stake = ss.evaluate_stake_task(ss.StakeTask(mode="hungarian", **common))
    credit = cd.evaluate_credit_task(cd.CreditTask(probe_every=7, **common))
    assert set(credit) == {"row", "arrays", "probe"}
    row = credit["row"]
    assert (row["probe_every"], row["probe_steps"]) == (7, 6)
    assert row["baseline_mismatch_steps"] == int(np.sum(
        credit["probe"]["qos_copy_baseline"] != credit["probe"]["qos_live"]))
    assert row["probe_wall_mean_s"] > 0 and row["collection_wall_mean_s"] > 0
    assert {k: v for k, v in row.items() if k not in VOLATILE | CREDIT_FIELDS} == \
           {k: v for k, v in stake["row"].items() if k not in VOLATILE}
    assert set(credit["arrays"]) == set(stake["arrays"])
    for key, value in stake["arrays"].items():
        np.testing.assert_array_equal(credit["arrays"][key], value, err_msg=key)
    probe = credit["probe"]
    np.testing.assert_array_equal(probe["probe_step"], [0, 7, 14, 21, 28, 35])
    assert probe["collection_wall_s"].shape == (40,)
    # every probe after the first replan carries a plan: R2 flags only UAVs on relay rows
    assert probe["relay_slot"][1:].sum(axis=1).max() <= 2


# ----------------------------------------------------------------------------- probe pieces

def _synthetic_capacities():
    access = np.asarray([[2e6, 2e6, 0, 0, 0],
                         [0, 0, 4e6, 0, 0],
                         [0, 1e6, 0, 1e6, 0],
                         [0, 0, 0, 0, 5e6]])
    backhaul = np.asarray([5e6, 3e6, 2e6, 0.0])
    paths = {0: ([("uav", 0), ("ground_bs", 0)], 5e6),
             1: ([("uav", 1), ("uav", 0), ("ground_bs", 0)], 3e6),
             2: ([("uav", 2), ("uav", 1), ("uav", 0), ("ground_bs", 1)], 2e6)}   # UAV 3: none
    return access, backhaul, paths


def test_path_access_backhaul_pieces_on_a_synthetic_fixture():
    access, backhaul, paths = _synthetic_capacities()
    delivered = cd.delivered_by_uav(access, backhaul)
    np.testing.assert_allclose(delivered[1], [0, 0, 3e6, 0, 0])   # scale 3/4
    assert not delivered[3].any()                                    # backhaul 0
    servers = cd.user_servers(delivered)
    np.testing.assert_array_equal(servers, [0, 0, 1, 2, -1])
    np.testing.assert_array_equal(cd.user_servers(np.asarray([[1.0, 0.0], [1.0, 0.0]])), [0, -1])
    hops, intermediate = cd.path_structure(paths, 4)
    np.testing.assert_array_equal(hops, [1, 2, 3, 0])
    np.testing.assert_array_equal(intermediate, [True, True, False, False])
    traffic = np.minimum(delivered.max(axis=0), 2.5e6)            # [2, 2, 2.5, 1, 0] Mbps
    shares = cd.relay_hop_shares(traffic, servers, hops)
    assert shares["relay_hop_traffic_share"] == pytest.approx(3.5 / 7.5)
    assert shares["relay_hop_user_share"] == pytest.approx(0.5)
    assert (shares["relay_hop_users"], shares["delivered_users"]) == (2, 4)
    assert shares["total_delivered_bps"] == pytest.approx(7.5e6)
    np.testing.assert_allclose(cd.served_traffic(traffic, servers, 4), [4e6, 2.5e6, 1e6, 0])
    empty = cd.relay_hop_shares(np.zeros(3), np.full(3, -1), hops)
    assert math.isnan(empty["relay_hop_traffic_share"])
    assert math.isnan(empty["relay_hop_user_share"])


def test_relay_slot_on_a_synthetic_plan():
    plan = {"priority": np.asarray([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0], [4.0, 4.0]]),
            "kinds": ["relay", "relay", "service", "service"],
            "targets": np.asarray([[1.0, 1.0], [3.0, 3.0], [np.nan, np.nan], [2.0, 2.0],
                                   [2.0, 2.0 + 1e-9], [4.0, 4.0]])}
    np.testing.assert_array_equal(cd.relay_slot_mask(plan, 6),
                                  [True, False, False, True, False, False])
    assert not cd.relay_slot_mask(None, 6).any()
    no_relay = dict(plan, kinds=["service"] * 4)
    assert not cd.relay_slot_mask(no_relay, 6).any()


class _FakeRaw:
    """Four UAVs with fixed delivered_by_uav; a UAV with battery 0 delivers nothing."""

    def __init__(self):
        access, backhaul, paths = _synthetic_capacities()
        self.n_uavs = 4
        self.routing_paths = paths
        self.last_access_capacity_bps = access
        self.last_backhaul_capacities_bps = backhaul
        self.uav_battery_ratios = np.asarray([0.9, 0.8, 0.7, 0.0])
        self._delivered = cd.delivered_by_uav(access, backhaul)
        self.demand = np.full(5, 2.5e6)
        self.last_user_demand_bps = self.demand.copy()
        self.last_delivered_traffic_bps = np.minimum(self._rates(), self.demand)

    def _rates(self):
        return np.max(self._delivered * (self.uav_battery_ratios > 0)[:, None], axis=0)

    def _communication_unavailable_mask(self):
        return self.uav_battery_ratios <= 0.0

    def _update_channel_state(self):
        pass

    _update_uav_connections = _compute_routing_paths = _update_channel_state

    def _calculate_end_to_end_user_rates(self):
        return self._rates(), None, None

    def _current_user_qos_demand_bps(self):
        return self.demand.copy()


def test_probe_raw_removal_differences_on_a_fake_env():
    raw = _FakeRaw()
    battery = raw.uav_battery_ratios.copy()
    record = cd.probe_raw(raw, SimpleNamespace(heuristic=SimpleNamespace(last_plan=None)), 30)
    np.testing.assert_array_equal(raw.uav_battery_ratios, battery)     # original untouched
    assert record["probe_step"] == 30
    assert record["qos_live"] == pytest.approx(0.6)
    assert record["qos_copy_baseline"] == record["qos_live"]
    np.testing.assert_allclose(record["qos_removed"], [0.36, 0.40, 0.52, 0.6])
    np.testing.assert_allclose(record["D"], [0.24, 0.20, 0.08, 0.0], atol=1e-15)
    assert record["D"][3] == 0.0 and not record["available"][3]
    np.testing.assert_array_equal(record["path_hops"], [1, 2, 3, 0])
    assert record["relay_hop_traffic_share"] == pytest.approx(3.5 / 7.5)


# ----------------------------------------------------------------------------- readings

def _probe(qos_live, D, *, available=None, r1=None, r2=None, baseline=None, total=None,
           relay_traffic=None, users=None, relay_users=None, probe_wall=None,
           collection=(math.nan, 0.04)):
    D = np.asarray(D, dtype=np.float64)
    n = len(D)
    zeros = np.zeros((n, 8), dtype=bool)
    total = np.asarray(total if total is not None else np.ones(n), dtype=np.float64)
    relay_traffic = np.asarray(relay_traffic if relay_traffic is not None else np.zeros(n),
                               dtype=np.float64)
    users = np.asarray(users if users is not None else np.ones(n), dtype=np.int64)
    relay_users = np.asarray(relay_users if relay_users is not None else np.zeros(n),
                             dtype=np.int64)
    qos_live = np.asarray(qos_live, dtype=np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        traffic_share = np.where(total > 0, relay_traffic / total, np.nan)
        user_share = np.where(users > 0, relay_users / users, np.nan)
    return {"probe_step": np.arange(n) * 10, "qos_live": qos_live,
            "qos_copy_baseline": np.asarray(baseline if baseline is not None else qos_live,
                                            dtype=np.float64),
            "qos_removed": qos_live[:, None] - D, "D": D,
            "available": np.asarray(available if available is not None else ~zeros),
            "served_traffic_bps": np.zeros((n, 8)), "path_hops": np.zeros((n, 8), np.int64),
            "is_intermediate": np.asarray(r1 if r1 is not None else zeros),
            "relay_slot": np.asarray(r2 if r2 is not None else zeros),
            "relay_hop_traffic_share": traffic_share, "relay_hop_user_share": user_share,
            "total_delivered_bps": total, "relay_hop_traffic_bps": relay_traffic,
            "relay_hop_users": relay_users, "delivered_users": users,
            "probe_wall_s": np.asarray(probe_wall if probe_wall is not None else np.full(n, .1)),
            "collection_wall_s": np.asarray(collection, dtype=np.float64)}


def _synthetic_worlds():
    available = np.ones((2, 8), dtype=bool)
    available[1, 6] = False
    r1 = np.zeros((2, 8), dtype=bool)
    r1[0, 0] = True
    r2 = np.zeros((2, 8), dtype=bool)
    r2[0, 1] = r2[1, 1] = r2[1, 6] = True
    world_a = _probe([0.5, 0.4], [[0.2, 0.005, 0, 0, 0, 0, 0, -0.02], [0.1, 0, 0, 0, 0, 0, 0, 0]],
                     available=available, r1=r1, r2=r2, baseline=[0.5, 0.41], total=[100, 50],
                     relay_traffic=[20, 0], users=[10, 5], relay_users=[2, 0],
                     probe_wall=[0.1, 0.1], collection=[math.nan, 0.04, 0.04, 0.04])
    world_b = _probe([0.0], [[0.0] * 8], total=[0.0], relay_traffic=[0.0], users=[0],
                     relay_users=[0], probe_wall=[0.3], collection=[math.nan, 0.02])
    return [world_a, world_b, None], (1, 2, 3)


def test_readings_arithmetic_on_synthetic_arrays():
    probes, worlds = _synthetic_worlds()
    r = cd.credit_readings(probes, worlds)
    json.dumps(r, allow_nan=False)
    assert r["failed_worlds"] == [3] and r["n_probe_steps"] == 3
    share = r["relay_hop_traffic_share"]
    assert share["pooled_traffic_weighted"] == pytest.approx(20 / 150)
    assert share["per_world_step_mean"]["per_world"] == [pytest.approx(0.1), None, None]
    assert share["per_world_step_mean"]["n_worlds"] == 1
    assert share["per_world_step_mean"]["se"] is None
    assert r["relay_hop_user_share"]["pooled_user_weighted"] == pytest.approx(2 / 15)
    assert r["r1_any_share"]["pooled"] == pytest.approx(1 / 3)
    assert r["r1_any_share"]["per_world_step_mean"]["mean"] == pytest.approx(0.25)
    assert r["r1_any_share"]["per_world_step_mean"]["se"] == pytest.approx(0.25)
    assert r["r1_mean_count"]["pooled"] == pytest.approx(1 / 3)
    avail = r["abs_D"]["available"]["pooled"]
    assert avail["n_uav_steps"] == 23
    assert avail["mean_abs"] == pytest.approx(0.325 / 23)
    assert avail["sparsity"] == pytest.approx(20 / 23)
    assert avail["fraction_negative"] == pytest.approx(1 / 23)
    assert avail["median_abs"] == 0.0
    every = r["abs_D"]["all"]["pooled"]
    assert every["n_uav_steps"] == 24 and every["sparsity"] == pytest.approx(21 / 24)
    assert every["q99_abs"] == pytest.approx(np.quantile(
        np.abs([0.2, 0.005, 0.02, 0.1] + [0.0] * 20), 0.99))
    assert r["abs_D"]["available"]["per_world_sparsity"]["per_world"] == \
        [pytest.approx(12 / 15), 1.0, None]
    r1 = r["relay_R1"]["pooled"]
    assert (r1["relay_uav_steps"], r1["other_available_uav_steps"]) == (1, 22)
    assert r1["mean_abs_relay"] == pytest.approx(0.2)
    assert r1["mean_abs_other_available"] == pytest.approx(0.125 / 22)
    assert r1["ratio"] == pytest.approx(0.2 / (0.125 / 22))
    assert r1["d_mass_share"] == pytest.approx(0.2 / 0.325)
    r2 = r["relay_R2"]["pooled"]
    assert (r2["relay_uav_steps"], r2["flagged_unavailable_uav_steps"]) == (2, 1)
    assert r2["mean_abs_relay"] == pytest.approx(0.0025)
    assert r2["mean_abs_other_available"] == pytest.approx(0.32 / 21)
    assert r2["d_mass_share"] == pytest.approx(0.005 / 0.325)
    assert r["relay_R2"]["per_world_ratio"]["per_world"][1] is None   # world B: no relay steps
    rho = r["additive_residual_rho"]
    assert rho["n_probe_steps"] == 2                                   # qos_live 0 excluded
    assert rho["median"] == pytest.approx(-0.69) and rho["mean"] == pytest.approx(-0.69)
    assert (rho["q25"], rho["q75"]) == (pytest.approx(-0.72), pytest.approx(-0.66))
    assert rho["iqr"] == pytest.approx(0.06) and rho["fraction_abs_above"] == 1.0
    assert rho["per_world_median"]["per_world"] == [pytest.approx(-0.69), None, None]
    cost = r["cost"]
    assert cost["mean_probe_wall_s"] == pytest.approx(0.5 / 3)
    assert cost["mean_collection_wall_s_per_step"] == pytest.approx(0.035)
    assert cost["slowdown_per_step_probe"] == pytest.approx(1 + (0.5 / 3) / 0.035)
    assert cost["slowdown_every_10"] == pytest.approx(1 + (0.5 / 3) / 0.35)
    assert cost["declared_max_slowdown"] == 1.5
    assert r["baseline_mismatch_steps"] == 1
    rules = r["rule_inputs"]
    assert rules["relay_hop_share"]["thresholds"] == [0.10, 0.25]
    assert rules["relay_hop_share"]["observed_pooled_traffic_weighted"] == pytest.approx(20 / 150)
    assert rules["relay_ratio_R1"] == {"observed_pooled": pytest.approx(r1["ratio"]),
                                       "observed_per_world_mean": pytest.approx(0.2 / (0.125 / 14)),
                                       "threshold": 2.0}
    assert rules["sparsity_available"]["observed_pooled"] == pytest.approx(20 / 23)
    assert rules["sparsity_available"]["threshold"] == 0.80
    assert "verdict" not in json.dumps(r)


def test_credit_trace_arrays_pad_and_mark_failed_worlds():
    probes, _ = _synthetic_worlds()
    results = [{"row": {"seed": 11, "failed": False}, "probe": probes[0]},
               {"row": {"seed": 12, "failed": True}, "probe": None}]
    arrays = cd.credit_trace_arrays(results, (11, 12, 13), horizon=4, probe_every=2)
    np.testing.assert_array_equal(arrays["worlds"], [11, 12, 13])
    np.testing.assert_array_equal(arrays["failed"], [False, True, True])
    np.testing.assert_array_equal(arrays["probe_count"], [2, 0, 0])
    assert arrays["D"].shape == (3, 2, 8) and arrays["D"].dtype == np.float32
    assert arrays["probe_step"].dtype == np.int32 and arrays["path_hops"].dtype == np.int8
    assert arrays["available"].dtype == np.bool_ and arrays["probe_wall_s"].dtype == np.float64
    assert arrays["collection_wall_s"].shape == (3, 4)
    assert np.isnan(arrays["D"][1:]).all() and (arrays["probe_step"][1:] == -1).all()
    assert not arrays["available"][1:].any()
    np.testing.assert_array_equal(arrays["probe_step"][0], [0, 10])
    np.testing.assert_allclose(arrays["D"][0], probes[0]["D"].astype(np.float32))


def test_trajectory_comparison():
    reward = np.arange(5, dtype=np.float64)
    xyz = np.zeros((5, 8, 3))
    same = cd.trajectory_comparison({"reward": reward, "own_xyz": xyz},
                                    {"reward": reward.copy(), "own_xyz": xyz.copy()})
    assert same["identical"] is True and same["reward"]["first_differing_step"] is None
    moved = xyz.copy()
    moved[2, 3, 1] = 0.5
    moved[4, 0, 0] = -1.5
    diff = cd.trajectory_comparison({"reward": reward, "own_xyz": xyz},
                                    {"reward": reward, "own_xyz": moved})
    assert diff["identical"] is False and diff["reward"]["identical"] is True
    assert diff["own_xyz"]["first_differing_step"] == 2
    assert diff["own_xyz"]["max_abs_difference"] == 1.5
    short = cd.trajectory_comparison({"reward": reward, "own_xyz": xyz},
                                     {"reward": reward[:3], "own_xyz": xyz[:3]})
    assert short["reward"]["first_differing_step"] == 3 and short["identical"] is False
    json.dumps([same, diff, short], allow_nan=False)


# ----------------------------------------------------------------------------- runner

def test_runner_credit_arguments():
    args = entry.parse_args(["credit-diagnostics", "--out", "o", "--launch-sha", "s"])
    assert (args.command, args.workers, args.threads) == ("credit-diagnostics", 8, 2)
    for bad in (["credit-diagnostics", "--out", "o"],
                ["credit-diagnostics", "--launch-sha", "s"],
                ["credit-diagnostics", "--out", "o", "--launch-sha", "s", "--mode", "identity"],
                ["credit-diagnostics", "--out", "o", "--launch-sha", "s", "--worlds", "955001"]):
        with pytest.raises(SystemExit):
            entry.parse_args(bad)


def test_runner_admission_precedes_credit_diagnostics(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    def refuse(*args, **kwargs):
        raise RuntimeError("no admission")

    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    target = tmp_path / "never-created"
    with pytest.raises(RuntimeError, match="no admission"):
        entry.main(["credit-diagnostics", "--out", str(target), "--launch-sha", "s"])
    assert not target.exists()
    order = []
    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda *args, **kwargs: order.append("admission") or {"sha": "s"})
    monkeypatch.setattr(cd, "run_credit_diagnostics", lambda **kwargs: order.append(kwargs) or {})
    entry.main(["credit-diagnostics", "--out", str(target), "--launch-sha", "s", "--workers", "4",
                "--threads", "1"])
    assert order[0] == "admission"
    assert {k: v for k, v in order[1].items() if k != "argv"} == \
           {"out": target, "launch_sha": "s", "workers": 4, "threads": 1}
    with pytest.raises(RuntimeError, match="admission"):
        entry.main(["credit-diagnostics", "--out", str(target), "--launch-sha", "other"])


def test_run_refuses_existing_output_and_holdout_worlds(tmp_path):
    out = tmp_path / "run"
    (out / cd.CREDIT_PHASE).mkdir(parents=True)
    (out / cd.CREDIT_PHASE / "summary.json").write_text("{}")
    with pytest.raises(FileExistsError):
        cd.run_credit_diagnostics(out=out, launch_sha="s", workers=1, threads=1, worlds=(955001,))
    for kwargs in ({"worlds": (957001,)}, {"worlds": (955001, 957003)},
                   {"worlds": (955001, 955001)}, {"worlds": ()}, {"workers": 64}):
        target = tmp_path / f"bad_{len(list(tmp_path.iterdir()))}"
        values = {"worlds": (955001,), "workers": 1} | kwargs
        with pytest.raises(ValueError):
            cd.run_credit_diagnostics(out=target, launch_sha="s", threads=1, **values)
        assert not target.exists()


def test_tiny_end_to_end_through_the_runner(tmp_path, monkeypatch):
    """Monkeypatched: STAKE_SPEC horizon 3000 -> 20, worlds -> 955001-2, PROBE_EVERY -> 5."""
    from scripts import hmasd_admission

    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: {"sha": "sha-e2e"})
    monkeypatch.setattr(ss, "STAKE_SPEC", replace(B01Spec(), horizon=20))
    monkeypatch.setattr(cd, "PROBE_EVERY", 5)
    original = cd.run_credit_diagnostics
    monkeypatch.setattr(cd, "run_credit_diagnostics",
                        lambda **kwargs: original(worlds=(955001, 955002), **kwargs))
    out = tmp_path / "e2e"
    started = time.perf_counter()
    summary = entry.main(["credit-diagnostics", "--out", str(out), "--launch-sha", "sha-e2e",
                          "--workers", "2", "--threads", "1"])
    print(f"tiny end-to-end wall {time.perf_counter() - started:.1f} s")
    root = out / cd.CREDIT_PHASE
    for name in ("config.json", "summary.json", "progress.jsonl", "panels/hungarian.json",
                 "traces/hungarian.npz", "traces/credit_hungarian.npz", "bit_identity.json"):
        assert (root / name).is_file(), name
    assert summary["status"] == "COMPLETE"
    written = json.loads((root / "summary.json").read_text())
    config = json.loads((root / "config.json").read_text())
    assert written["status"] == "COMPLETE" and written["failure"] is None
    assert written["counts"] == {"episodes_completed": 2, "steps": 40, "failed_worlds": 0,
                                 "new_fits": 0, "probe_steps": 8,
                                 "baseline_mismatch_steps":
                                     written["readings"]["baseline_mismatch_steps"],
                                 "bit_identity_episodes": 2}
    assert written["readings"] == json.loads(json.dumps(summary["readings"]))
    assert config["horizon"] == 20 and config["probe_every"] == 5
    assert config["policy_seed"] == 925031 and config["assignment_mode"] == "hungarian"
    assert config["heuristic"] == H1.record() and config["launch_sha"] == "sha-e2e"
    assert (config["workers"], config["threads"]) == (2, 1)
    panel = json.loads((root / "panels" / "hungarian.json").read_text())
    assert [row["seed"] for row in panel["rows"]] == [955001, 955002]
    assert all(row["assignment_mode"] == "hungarian" and row["probe_steps"] == 4
               and row["probe_every"] == 5 for row in panel["rows"])
    with np.load(root / "traces" / "hungarian.npz") as trace:
        assert trace["world_1_target_xy"].shape == (20, 8, 2)
    with np.load(root / "traces" / "credit_hungarian.npz") as credit:
        assert credit["D"].shape == (2, 4, 8) and credit["collection_wall_s"].shape == (2, 20)
        np.testing.assert_array_equal(credit["probe_step"], [[0, 5, 10, 15]] * 2)
        np.testing.assert_array_equal(credit["worlds"], [955001, 955002])
    events = [json.loads(line) for line in (root / "progress.jsonl").read_text().splitlines()]
    assert [e["event"] for e in events] == ["run_start", "world_end", "world_end",
                                            "bit_identity_start", "bit_identity_end", "run_end"]
    assert all({"seed", "probe_steps", "baseline_mismatch_steps", "wall"} <= set(e)
               for e in events if e["event"] == "world_end")
    bit = json.loads((root / "bit_identity.json").read_text())
    assert written["bit_identity"] == bit and bit["record_only"] is True
    # tiny horizon and two worlds: layer (a) runs, reports false, and never aborts
    assert bit["hungarian_matches_recorded"] is False
    assert bit["panel_consistency"]["recorded_identity_problems"]
    # layer (b): the deep-copy probe leaves 955001's trajectory bitwise unchanged
    assert bit["world"]["world"] == 955001 and "one world" in bit["world"]["scope"]
    assert bit["deepcopy_probe_trajectory_neutral"] is True
    assert bit["world"]["deepcopy_probe_comparison"]["own_xyz"]["max_abs_difference"] == 0.0
    assert isinstance(bit["raw_probe_trajectory_neutral"], bool)
    assert bit["world"]["raw_probe_calls"] == 8 * 20
