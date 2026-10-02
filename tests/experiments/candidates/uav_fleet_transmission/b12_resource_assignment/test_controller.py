"""One B12 finite batch: 8 streams/replays, 24 law pairs, 6 edge tables.

No environment, RF model, native transition or RNG query is constructed. Actual
analytical, supplied-edge mock, failed-attempt and independent-reference work
are separately visible in the shared TOTALS property. DM owns execution.
"""
from __future__ import annotations
import itertools
import json
import math
import numpy as np
import pytest
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT, own_positions, E_BATTERY, E_MARGIN, E_AVAILABLE,
)
from experiments.candidates.uav_information_value import controllers as original_planner
from experiments.candidates.uav_fleet_transmission.b12_resource_assignment import controller as module
from experiments.candidates.uav_fleet_transmission.b12_resource_assignment import energy
from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.trace import blank, CANDIDATE_DTYPE

class Poison:
    def __getattribute__(self, name):
        raise AssertionError("privileged input read: " + name)
    def __array__(self, *args, **kwargs):
        raise AssertionError("privileged input converted")

def frame(users=(), *, bs=None, stations=((7000., 500., 100.), (1000., 7000., 100.))):
    """Public literals encoded in the retained lawful 365-field interface."""
    layout = S7S2_LAYOUT
    xyz = np.asarray([[900., 900., 100.], [1200., 900., 100.], [1800., 1000., 100.],
                      [2400., 1000., 100.], [3200., 1400., 100.], [4500., 2500., 100.],
                      [6000., 4500., 100.], [7200., 7000., 100.]])
    obs = np.zeros((8, layout.dim), dtype=np.float32)
    obs[:, :2] = xyz[:, :2] / 8000.
    obs[:, 2] = (xyz[:, 2] - 50.) / 150.
    own = own_positions(obs)
    for slot, xy in enumerate(users):
        base = layout.users.start + slot * layout.user_fields
        obs[0, base:base + 2] = (np.asarray(xy) - own[0, :2]) / 8000.
        obs[0, base + 4] = 1.
    for observer in range(8):
        energy = obs[observer, layout.energy_uavs].reshape(8, 13)
        energy[:, :3] = (own - own[observer]) / [8000., 8000., 150.]
        energy[:, E_BATTERY] = .8
        energy[:, E_MARGIN] = .5
        energy[:, E_AVAILABLE] = 1.
        for station, position in enumerate(stations):
            if position is None:
                continue
            base = layout.energy_stations.start + station * layout.energy_station_fields
            obs[observer, base:base + 3] = (np.asarray(position) - own[observer]) / [8000., 8000., 150.]
            obs[observer, base + 3] = np.linalg.norm(np.asarray(position) - own[observer]) / 8000.
            obs[observer, base + 4:base + 6] = 1. / 8.
            obs[observer, base + 7] = 1.
        if bs is not None:
            base = layout.bs.start
            obs[observer, base:base + 2] = (np.asarray(bs) - own[observer, :2]) / 8000.
            obs[observer, base + 2] = (30. - own[observer, 2]) / 200.
            obs[observer, base + 3] = 1.
    return obs


@pytest.fixture(scope="module", autouse=True)
def measured_work(record_testsuite_property):
    module.TOTALS.clear()
    yield
    counts = json.dumps(module.TOTALS, sort_keys=True)
    record_testsuite_property("b12_scripted_analytical_counts", counts)
    print("B12 actual/mock/failed/reference counts: " + counts)
    assert module.TOTALS.get("proposals", 0) <= 976
    assert module.TOTALS.get("flight_edges", 0) <= 1728 + 24
    assert module.TOTALS.get("reference_flight_edges", 0) <= 24
    assert module.TOTALS.get("return_evaluations", 0) <= 288 + 24
    assert module.TOTALS.get("reference_return_evaluations", 0) <= 24
    assert module.TOTALS.get("permutation_evaluations", 0) <= 34560 + 4320
    assert module.TOTALS.get("mock_permutation_evaluations", 0) <= 4320
    assert module.TOTALS.get("reference_arithmetic_ticks", 0) <= 9072
    assert module.TOTALS.get("constant_power_evaluations", 0) <= 600
    assert module.TOTALS.get("model_constructions", 0) == 0
    assert module.TOTALS.get("model_rf_calls", 0) == 0
    assert module.TOTALS.get("associations", 0) == 0


@pytest.mark.parametrize("policy", ["E", "B"])
@pytest.mark.parametrize("case", range(4), ids=["full-menu", "aliases", "sparse-release-no-BS", "failed-prefix"])
def test_one_stream_and_one_saved_prefix_replay(monkeypatch, policy, case):
    def forbidden(*args, **kwargs):
        raise AssertionError("tracker/private-model construction forbidden")
    monkeypatch.setattr(module.b10, "AnonymousTracker", forbidden)
    monkeypatch.setattr(module.b10, "LawfulServiceModel", forbidden)
    if case == 1:
        def aliases(points, k, iterations):
            return np.repeat(points[:1], k, axis=0), np.ones(k, dtype=np.int64)
        monkeypatch.setattr(original_planner, "estimator_kmeans", aliases)
    if case == 3:
        name = "flight_edge" if policy == "E" else "permutation_criterion"
        original = getattr(module, name)
        def fail(*args, **kwargs):
            counts = kwargs["counters"]
            reached = counts.get("flight_edges", 0) == 72 if policy == "E" else counts.get("permutation_evaluations", 0) == 1443
            if counts["plans"] == 3 and reached:
                module.b10.bump(counts, "mock_failed_" + name + "_attempts")
                raise RuntimeError("scripted " + name + " interruption")
            return original(*args, **kwargs)
        monkeypatch.setattr(module, name, fail)
    history = []
    assign = module.b10.ProvenanceHeuristic._assign_targets
    def see_history(self, own_xy, uavs, points, targets):
        if self._assignment_call == 0:
            history.append((self.calls, self.targets_xy.copy()))
        return assign(self, own_xy, uavs, points, targets)
    monkeypatch.setattr(module.b10.ProvenanceHeuristic, "_assign_targets", see_history)
    inputs = []
    for step in range(61):
        users = [(1100. + 250*i + step, 1200. + 130*i) for i in range(6)]
        stations = ((7000., 500., 100.), (1000., 7000., 100.))
        mode = np.zeros(8, dtype=bool)
        if case == 2 and step < 30:
            users, stations = users[:1], (None, stations[1])
            mode[7] = step == 0
        obs = frame(users, stations=stations)
        if case == 2 and step > 0:
            obs[7, 0] += .01
        if case == 0:
            for observer in range(8):
                energy_rows = obs[observer, S7S2_LAYOUT.energy_uavs].reshape(8, 13)
                energy_rows[:, E_BATTERY] = [.02, .05, .08, .2, .5, .9, 0., .3]
                energy_rows[:, E_AVAILABLE] = 0.0
        inputs.append((obs, mode))
    first, replay = module.make_controller(policy), module.make_controller(policy)
    actions, snapshots, committed = [], {}, {}
    try:
        assert first.arm == "C" and first.policy_arm == policy
        assert first.tracker is None and first.model is None and first.law is None
        for step, (obs, mode) in enumerate(inputs):
            old = obs.copy()
            if case == 3 and step == 60:
                with pytest.raises(RuntimeError, match="scripted"):
                    first.propose(obs, Poison(), step, Poison(), mode)
                assert first.heuristic.calls == 60
                break
            actions.append(first.propose(obs, Poison(), step, Poison(), mode))
            np.testing.assert_array_equal(obs, old)
            assert first.heuristic.calls == step + 1
            if step % 30 == 0:
                d = first.last_decision
                snapshots[step], committed[step] = d, first.targets_xy
                assert not d["edge_fly_wh"].flags.writeable
                np.testing.assert_array_equal(first.targets_xy, first.heuristic.last_plan["targets"])
                np.testing.assert_array_equal(first.targets_xy[~d["eligible"]], d["ordinary_targets"][~d["eligible"]])
                key = lambda a: np.lexsort((a[:, 1], a[:, 0]))
                np.testing.assert_array_equal(first.targets_xy[key(first.targets_xy)], d["ordinary_targets"][key(d["ordinary_targets"])])
        raw = first.audit_arrays()
        candidates = raw["candidate_records"]
        for step, d in snapshots.items():
            m = d["m"]
            if d["fallback"]:
                assert d["candidate_count"] == d["edge_count"] == d["return_count"] == 0
                assert d["selected"] == -1
                continue
            assert d["candidate_count"] == math.factorial(m)
            assert d["edge_count"] == m*m and d["return_count"] == m
            rows = candidates[candidates["step"] == step]
            maps = [tuple(row["columns"][:m]) for row in rows]
            assert maps == sorted(maps) and len(set(maps)) == len(maps)
            assert maps.count(tuple(d["base_columns"][:m])) == 1
            selected = rows[d["selected"]]
            np.testing.assert_array_equal(np.flatnonzero(rows["selected"]), [d["selected"]])
            np.testing.assert_array_equal(d["selected_columns"], selected["columns"])
            members = d["eligible_uavs"][:m]
            local = {int(c): i for i, c in enumerate(d["target_columns"][:m])}
            expected = d["ordinary_targets"].copy()
            expected[members] = d["target_xy"][[local[int(c)] for c in selected["columns"][:m]]]
            np.testing.assert_array_equal(first.targets_xy if step == 60 else committed[step], expected)
            if case == 1:
                assert d["selected"] == d["base_index"]
                np.testing.assert_array_equal(d["edge_fly_wh"][:m,:m], np.repeat(d["edge_fly_wh"][:m,:1], m, axis=1))
        if case == 2:
            assert snapshots[0]["fallback"] == 1
            assert np.all(actions[1][7,:2] == 0.0)
            assert snapshots[30]["m"] == 6 and snapshots[30]["fallback"] == 0
            assert first.diagnostics[1]["bs_input_source"] == "absent"
        for boundary, previous in history:
            if boundary:
                np.testing.assert_array_equal(previous, committed[boundary-30])
        counts = first.counters.copy()
        assert counts["constant_power_evaluations"] == counts["constant_power_evaluations_completed"] == 3
        assert counts["law_constructions"] == 1
        replay.set_replay_prefix(raw)
        for step, (obs, mode) in enumerate(inputs):
            if case == 3 and step == 60:
                with pytest.raises(module.ReplayBoundary, match="incomplete"):
                    replay.propose(obs, Poison(), step, Poison(), mode)
                break
            actual = replay.propose(obs, Poison(), step, Poison(), mode)
            np.testing.assert_array_equal(actual, actions[step])
            if step % 30 == 0:
                for name in snapshots[step]:
                    module.b10.equal(replay.last_decision[name], snapshots[step][name], "decision/"+name)
        rebuilt = replay.audit_arrays()
        for table in raw:
            for name in raw[table].dtype.names:
                if case == 3 and name == "started":
                    continue
                module.b10.equal(rebuilt[table][name], raw[table][name], table+"/"+name)
        if case == 3:
            field = "edge_records" if policy == "E" else "candidate_records"
            assert raw[field][-1]["started"] and not raw[field][-1]["completed"]
            assert not rebuilt[field][-1]["started"] and not rebuilt[field][-1]["completed"]
            expected = counts.copy()
            expected.pop("mock_failed_flight_edge_attempts" if policy == "E" else "mock_failed_permutation_criterion_attempts")
            assert replay.counters == expected
        else:
            assert replay.counters == counts
        assert counts["proposals"] == 61 and counts["canonicalizations"] == counts["plans"] == 3
        assert counts["associations"] == 0
        # Reset checks cache survival without adding another stream or query.
        law, cold, cache = first.law, first.cold_costs, first.law._constants
        first.reset()
        assert first.law is law and first.law._constants is cache
        assert first.cold_costs == cold
        assert first.counters["constant_power_evaluations"] == 3
    finally:
        first.close()
        replay.close()


LAW_CASES = [
 ((0.,0.,100.),(0.,0.,100.)), ((0.,0.,100.),(30.,0.,100.)),
 ((0.,0.,100.),(31.,0.,100.)), ((0.,0.,100.),(300.,0.,100.)),
 ((0.,0.,50.),(0.,0.,100.)), ((0.,0.,200.),(0.,0.,100.)),
 ((0.,0.,95.),(0.,0.,100.)), ((0.,0.,96.),(0.,0.,100.)),
 ((0.,0.,50.),(30.,0.,100.)), ((0.,0.,50.),(600.,0.,100.)),
 ((0.,0.,92.),(45.,0.,100.)), ((0.,0.,91.),(60.,0.,100.)),
 ((0.,0.,100.),(.000001,0.,100.)), ((0.,0.,100.),(29.999999999999996,0.,100.)),
 ((0.,0.,100.),(30.000000000000004,0.,100.)),
 ((0.,0.,95.00000000000001),(0.,0.,100.)),
 ((0.,0.,94.99999999999999),(0.,0.,100.)),
 ((0.,0.,100.),(8000.,8000.,100.)), ((8000.,8000.,200.),(0.,0.,100.)),
 ((0.,0.,100.),(0.,0.,100.)), ((1000.,2400.,167.),(8000.,0.,100.)),
 ((0.,0.,100.1),(99.9,0.,100.)), ((0.,0.,85.),(90.,0.,100.)),
 ((0.,0.,87.5),(0.,79.5,100.)),
]


def independent_power(v, w, counts, *, constant=False):
    module.b10.bump(counts, "reference_constant_power_evaluations" if constant else "reference_power_evaluations")
    # Independent literal arithmetic; never call production power or its cache.
    blade = 79.86 * (1.0 + 3.0*v*v / (120.0*120.0))
    inner = math.sqrt(1.0 + v*v*v*v / (4.0*4.03**4)) - v*v / (2.0*4.03**2)
    rotor = 88.63 * math.sqrt(max(0.0, inner))
    drag = (.5*.6*1.225*.05*.503) * v*v*v
    return blade + rotor + drag + 15.0*abs(w)


@pytest.mark.parametrize("case", range(24))
def test_one_law_case_and_independent_arithmetic(case):
    counts = module.b10.CostDict()
    law = energy.PublicLaw(counts)
    x, target = map(lambda v: np.asarray(v,dtype=np.float64), LAW_CASES[case])
    stations = np.asarray([[0.,0.,0.], [100.,0.,100.]])
    if case == 19:
        stations = np.asarray([[0.,0.,400.], [100.,0.,100.]])
    station, back = energy.target_return(target, stations, law, counters=counts)
    ticks, wh, slack = energy.flight_edge(x, target, .05, back, law, counters=counts)
    module.b10.bump(counts, "reference_flight_edges")
    dx = math.sqrt(sum(float(target[k]-x[k])**2 for k in (0,1)))
    dz = abs(float(target[2]-x[2]))
    duration = int(math.ceil(max(dx/30.0, dz/5.0)))
    terms = []
    for tick in range(duration):
        module.b10.bump(counts, "reference_arithmetic_ticks")
        vx = min(30.0, max(0.0, dx-30.0*tick))
        vz = min(5.0, max(0.0, dz-5.0*tick))
        terms.append(independent_power(vx,vz,counts))
    module.b10.bump(counts, "reference_return_evaluations")
    distances = [math.sqrt(sum(float(target[k]-s[k])**2 for k in range(3))) for s in stations]
    expected_station = min(range(2), key=lambda k: (distances[k],k))
    reference_back = distances[expected_station]/3.0*independent_power(3.,0.,counts,constant=True)/3600.0
    reference_wh = math.fsum(terms)/3600.0
    assert ticks == duration <= 378
    assert station == expected_station
    np.testing.assert_allclose([wh,back,slack], [reference_wh,reference_back,.05-(reference_wh+reference_back)/160.-.10], rtol=5e-13,atol=1e-12)
    assert slack < 0.0  # Negative intent arrival slack is retained, never clipped.
    assert counts["flight_edges"] == counts["flight_edges_completed"] == 1
    if case == 0:
        assert ticks == 0 and wh == 0.0
    if case == 19:
        assert station == 1  # Planar nearest station0 is not 3D nearest.


@pytest.mark.parametrize("case", range(6), ids=["second-smallest", "sum-degeneracy", "minimum-before-sum", "base-tie", "lex-nonbase", "six-labelled-aliases"])
def test_one_supplied_edge_table(case):
    counts = module.b10.CostDict()
    m = [3,3,2,2,4,6][case]
    columns = np.arange(2,2+m,dtype=np.int8)
    base = columns.copy()
    fly, slack = np.ones((m,m)), np.zeros((m,m))
    if case == 0:
        fly[:], slack[:] = 100., -100.
        for i,v in enumerate((0.,1.,100.)):
            fly[i,i], slack[i,i] = 2.,v
        for i,v in enumerate((0.,2.,2.)):
            fly[i,(i+1)%3], slack[i,(i+1)%3] = 3.,v
    elif case == 1:
        fly[:] = [[3.,1.,9.],[2.,8.,1.],[1.,2.,3.]]
        slack[:] = np.asarray([.1,.5,.9])[:,None]-(fly+np.asarray([1.,3.,9.])[None,:])/160.-.10
    elif case == 2:
        fly[:] = [[10.,1.],[1.,10.]]
        slack[:] = [[0.,-1.],[100.,10.]]
    elif case == 3:
        base = columns[::-1].copy()
    elif case == 4:
        fly[0,0] = 2.
    elif case == 5:
        fly[:] = 0.
        base = columns[::-1].copy()
    rows = []
    for index, permutation in enumerate(itertools.permutations(range(m))):
        module.b10.bump(counts, "mock_permutation_evaluations")
        e, l = energy.permutation_criterion(fly,slack,permutation,counters=counts)
        row = blank(CANDIDATE_DTYPE,step=0,index=index,m=m,
            columns=module.padded(columns[list(permutation)],(6,),dtype=np.int8,fill=-1))
        row["energy"], row["slacks"] = e,module.padded(l,(6,))
        row["started"] = row["completed"] = True
        rows.append(row)
    records = np.asarray(rows,dtype=CANDIDATE_DTYPE)
    e_index, base_index = module.select_records("E",records,base,counters=counts)
    b_index, _ = module.select_records("B",records,base,counters=counts)
    e_map, b_map = tuple(records[e_index]["columns"][:m]), tuple(records[b_index]["columns"][:m])
    if case == 0:
        assert e_map == tuple(columns) and b_map == tuple(columns[[1,2,0]])
        assert records[b_index]["energy"] > records[e_index]["energy"]
        assert records[b_index]["slacks"][0] == records[e_index]["slacks"][0]
        assert records[b_index]["slacks"][1] > records[e_index]["slacks"][1]
    elif case == 1:
        sums = [math.fsum(row["slacks"][:m]) for row in records]
        assert sums[e_index] == max(sums)
        assert e_map == tuple(columns[[1,2,0]])
    elif case == 2:
        assert e_map == tuple(columns[::-1]) and b_map == tuple(columns)
        assert math.fsum(records[e_index]["slacks"][:m]) > math.fsum(records[b_index]["slacks"][:m])
    elif case in (3,5):
        assert e_index == b_index == base_index == len(records)-1
        assert e_map == b_map == tuple(base)
    else:
        assert e_map == b_map == tuple(columns[[1,0,2,3]])
    assert len(records) == math.factorial(m)
    assert counts["permutation_evaluations"] == counts["mock_permutation_evaluations"] == len(records)
