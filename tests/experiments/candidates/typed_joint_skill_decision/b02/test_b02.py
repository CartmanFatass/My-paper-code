"""Pure/synthetic/mock regressions only: no native host, radio call, real archive fit, or RNG draw."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.typed_joint_skill_decision.b02 import evidence, model, reader, run, search


def geometry():
    initial = np.array([[300 + 700 * i, 200 + 400 * (i % 3), 60 + 10 * i] for i in range(6)], dtype=float)
    sites = np.array([[600 + 550 * i, 900 + 350 * (i % 3), 100] for i in range(6)], dtype=float)
    users = np.array([[50 + 91 * i, 80 + 47 * i] for i in range(50)], dtype=float)
    return initial, sites, users


def candidate(index, reward=.3):
    return {"index": index, "kind": "subset_relay", "k": 5, "positions_xyz": geometry()[1].tolist(),
            "contract_reward": reward, "coverage_backhauled": .4, "potential": 123.0}


def make_bill(tmp_path):
    roots = [tmp_path / "source", tmp_path / "input", tmp_path / "out"]
    for p in roots:
        p.mkdir()
    return evidence.Bill([0] * len(evidence.COUNTERS), threading.Lock(), roots), roots[-1]


def test_three_shares_and_ties_before_selection():
    cs = [candidate(i, reward) for i, reward in enumerate([.2, .7, .7, .3])]
    ranked, shares = search.ranked_shares(cs, budget=15)
    assert ranked == [1, 2, 3]
    assert shares == [4, 4, 3]
    assert model.choose_rank([.7, .7, .3], [0, 0, .4]) == 0
    assert model.fallback(.5 - 2e-12, .5)
    assert not model.fallback(.5 - .5e-12, .5)


@pytest.mark.parametrize("duplicates", [False, True])
def test_independent_matching_same_float64_tie_arithmetic(duplicates):
    from experiments.candidates.coupled_host_joint_skills_stage1.planner import assign_targets
    initial, sites, users = geometry()
    if duplicates:
        sites[1] = sites[0]
        sites[3] = sites[2]
        initial[1] = initial[0] + [1e-11, -1e-11, 0]
    expected = assign_targets(initial, sites)
    assert list(reader.independent_assignment(initial, sites)) == expected.tolist()
    c = candidate(0)
    c["positions_xyz"] = sites.tolist()
    np.testing.assert_allclose(model.features(c, 2, initial, users, [2500, 2500, 30], assign_targets),
                               reader.independent_features(c, 2, initial, users, [2500, 2500, 30]), rtol=1e-10, atol=1e-10)


def test_feature_permutation_invariance_and_future_exclusion():
    from experiments.candidates.coupled_host_joint_skills_stage1.planner import assign_targets
    initial, sites, users = geometry()
    c = candidate(0)
    first = model.features(c, 1, initial, users, [2500, 2500, 30], assign_targets)
    c["positions_xyz"] = sites[::-1].tolist()
    c.update(final_reward=999, evaluations=999, accepted_descent=999)
    second = model.features(c, 1, initial[::-1], users[::-1], [2500, 2500, 30], assign_targets)
    np.testing.assert_allclose(first, second, rtol=1e-10, atol=1e-10)
    c["kind"] = "future_kind"
    with pytest.raises(ValueError, match="undeclared kind"):
        model.features(c, 0, initial, users, [2500, 2500, 30], assign_targets)


def test_single_synthetic_ridge_unpenalized_intercept_train_only_scaling(monkeypatch):
    # Literal arithmetic fixture, not the real archive and no random generator.
    x = np.asarray([[((i * (j + 3)) % 29) / 29 if j != 4 else 1.0 for j in range(15)] for i in range(192)])
    rows = [{"features": row.tolist(), "target_gain": float(.2 + .03 * row[0])} for row in x]
    original = np.linalg.solve
    calls = []
    def solve(a, b):
        calls.append((a.copy(), b.copy()))
        return original(a, b)
    monkeypatch.setattr(np.linalg, "solve", solve)
    state = model.fit_once(rows)
    assert len(calls) == 1 and len(state["coefficients"]) == 136
    assert state["base_sd"][4] == 1
    a = reader.independent_transform(x, state)
    w = np.asarray(state["coefficients"])
    residual = a.T @ (a @ w - np.asarray([r["target_gain"] for r in rows])) + np.r_[0.0, w[1:]]
    assert np.linalg.norm(residual) < 1e-8
    assert state["training_mse_final"] < state["training_mse_initial"]
    assert model.predict(x, state, initial=True).tolist() == [0.0] * 192
    old = deepcopy(state)
    model.predict([[1e6] * 15], state)
    assert state == old  # test contexts cannot update either standardizer.


def mock_planner(monkeypatch):
    from experiments.candidates.coupled_host_joint_skills_stage1 import planner as p
    env = SimpleNamespace(n_uavs=6, area_size=5000, height_range=(50, 150),
                          uav_positions=np.zeros((6, 3)))
    cs = []
    for i in range(3):
        c = candidate(i)
        c["positions_xyz"] = np.array([[1000 + 100 * i, 1000, 100] for _ in range(6)], dtype=float)
        cs.append(c)
    def build(*args, **kwargs):
        return deepcopy(cs)
    def static(host, positions, **kwargs):
        host.uav_positions = np.asarray(positions).copy()
        return {"contract_reward": float(.5 - np.sum((host.uav_positions[:, 0] - 1150) ** 2) / 1e7),
                "coverage_backhauled": .4, "uav_connection_count": 0}
    monkeypatch.setattr(p, "build_candidates", build)
    monkeypatch.setattr(p, "static_evaluate", static)
    monkeypatch.setattr(p, "plateau_potential", lambda *args: 0.0)
    monkeypatch.setattr(p, "link_ranges", lambda *args: {})
    return p, env


@pytest.mark.parametrize("rank", [0, 1, 2])
def test_adapter_exact_original_share_path_against_mocked_full_function(monkeypatch, rank):
    p, env = mock_planner(monkeypatch)
    full = p.search_placement(env, True, budget=94, rng=object(), n_starts=3)
    selected = full.starts[rank]
    c = full.candidates[selected["candidate_index"]]
    positions, got, history = search.branch(env, p, c, rank, selected["share"], full.candidates_evaluated)
    for key in ("share", "evaluations", "final_reward", "converged", "accepted_descent", "accepted_plateau", "final_xy_step_m"):
        assert got[key] == selected[key]
    np.testing.assert_array_equal(positions, reader.endpoint(search.search_json(full), rank))
    assert reader.path_signature(history, rank, got["began_at_evaluation"]) == reader.path_signature(full.history, rank, selected["began_at_evaluation"])


def test_constant_reward_plateau_stopping_clipping(monkeypatch):
    p, env = mock_planner(monkeypatch)
    def static(host, position, **kwargs):
        host.uav_positions = np.asarray(position).copy()
        return {"contract_reward": .5, "coverage_backhauled": .4, "uav_connection_count": 0}
    monkeypatch.setattr(p, "static_evaluate", static)
    monkeypatch.setattr(p, "plateau_potential", lambda host, *_: float(np.sum(np.abs(host.uav_positions[:, 0]))))
    c = candidate(0, .5)
    c["positions_xyz"] = np.array([[0, 0, 50]] * 6, dtype=float)
    c["potential"] = 0
    pos, record, _history = search.branch(env, p, c, 2, 500, 10)
    assert record["converged"] and record["final_xy_step_m"] == 25
    assert record["accepted_descent"] == record["accepted_plateau"] == 0
    assert record["evaluations"] < 500
    assert np.array_equal(pos, c["positions_xyz"])


@pytest.mark.parametrize("arm", ["G", "P"])
def test_ordinary_online_programs_omit_learned_features(monkeypatch, arm):
    p, env = mock_planner(monkeypatch)
    initial, _sites, users = geometry()
    env.uav_positions, env.user_positions = initial.copy(), users.copy()
    env.ground_bs_positions = np.array([[2500, 2500, 30]], dtype=float)
    monkeypatch.setattr(np.random, "default_rng", lambda *args: object())  # no actual RNG instantiated/drawn
    def forbidden(*args, **kwargs):
        raise AssertionError("ordinary path paid learned features")
    monkeypatch.setattr(model, "features", forbidden)
    decision = search.prepare_and_choose(env, p, 107100000, arm, None)
    assert decision["features"] is decision["predicted_gains"] is None
    assert decision["timing"]["learned_features_matching_seconds"] is None


def test_reader_checks_every_static_query_including_rejected_path(tmp_path):
    bill, out = make_bill(tmp_path)
    queries = [{"positions_xyz": [[i, 0, 100]] * 6, "allow_a2a": bool(i), "info": {"contract_reward": i / 10}}
               for i in range(6)]
    flat = SimpleNamespace(evaluations=1)
    relay = SimpleNamespace(candidates_evaluated=3, starts=[{"began_at_evaluation": 3, "evaluations": 1}])
    decision = {"arm": "G", "requested_rank": 0, "positions_xyz": queries[4]["positions_xyz"],
                "case_counts": {"static_calls": 6, "static_completed": 6}}
    expected = queries[:4] + queries[4:5] + [queries[4]]
    trace = evidence.Trace(out / "queries.gz", bill)
    for q in expected:
        trace.write(q)
    trace.close()
    assert reader.query_reader(out / "queries.gz", decision, flat, relay, queries) == 6
    decision["case_counts"]["static_calls"] = 5
    with pytest.raises(AssertionError, match="counter count"):
        reader.query_reader(out / "queries.gz", decision, flat, relay, queries)


def test_guard_out_and_admission_failure_precede_science(monkeypatch, tmp_path):
    from scripts.hmasd_launch import _validate_guard_contract
    from scripts import hmasd_admission
    _validate_guard_contract(Path(run.__file__), "typed_joint_skill_decision")
    def refuse(*args, **kwargs):
        raise RuntimeError("fixture admission refused")
    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    out = tmp_path / "not-created"
    with pytest.raises(RuntimeError, match="fixture admission refused"):
        run.main(["--out", str(out), "--launch-sha", "a" * 40, "--seed", "0",
                  "--input-root", str(tmp_path), "--input-manifest", "missing.json", "--input-manifest-sha256", "b" * 64])
    assert not out.exists()


def test_attempts_limits_trace_hashes_and_bound_members(tmp_path):
    bill, out = make_bill(tmp_path)
    store = evidence.Store(out, bill)
    bill.charge("static_calls")
    assert bill.snapshot()["counters"]["static_completed"] == 0
    path = store.write("raw/fixture.json", {"literal": 2})
    evidence.verify_outputs(out, store.files)
    with pytest.raises(ValueError, match="unbound"):
        evidence.load_output(out, store.files, "raw/unlisted.json")
    path.write_text('{"literal":3}\n')
    with pytest.raises(ValueError, match="changed"):
        evidence.verify_outputs(out, store.files)
    bill.values[evidence.COUNTERS.index("fits")] = 1
    with pytest.raises(RuntimeError, match="fits=2"):
        bill.charge("fits")
    trace = evidence.Trace(out / "trace.gz", bill)
    trace.write({"type": "fixture", "exact": .17})
    trace.close()
    assert list(evidence.read_trace(out / "trace.gz")) == [{"type": "fixture", "exact": .17}]
    with pytest.raises(ValueError, match="relative"):
        evidence.relative_path(out, "../outside")


def test_child_failure_not_retried_retains_partial_bill(monkeypatch, tmp_path):
    bill, out = make_bill(tmp_path)
    store = evidence.Store(out, bill)
    calls = []
    message = {"kind": "failed", "paths": [], "error": "synthetic child exception"}
    class Pipe:
        def poll(self, *args):
            return bool(calls)
        def recv(self):
            calls.pop()
            return message
        def close(self):
            pass
    class Process:
        pid, exitcode = 42, 1
        def start(self):
            calls.append("one start")
        def is_alive(self):
            return False
        def join(self):
            pass
    ctx = SimpleNamespace(Pipe=lambda **_: (Pipe(), Pipe()), Process=lambda **_: Process())
    with pytest.raises(RuntimeError, match="failed without retry"):
        run.spawn_case(ctx, {}, bill, store, 107100000, "G")
    assert bill.snapshot()["counters"]["spawn_attempts"] == 1
    assert bill.snapshot()["counters"]["spawn_completed"] == 0
    assert json.loads((out / "progress.json").read_bytes())["phase"] == "child_failed"


def test_native_kinematic_reader_uses_pinned_state_calls_not_saved_means(monkeypatch, tmp_path):
    # A deliberately malformed literal stream is refused before calling any radio code.
    bill, out = make_bill(tmp_path)
    trace = evidence.Trace(out / "malformed.gz", bill)
    trace.write({"type": "initial", "world": 9, "arm": "G"})
    trace.close()
    with pytest.raises(AssertionError, match="trace identity"):
        reader.trace_reader(out / "malformed.gz", None, None, {"world": 10, "arm": "G"}, {}, [], {})


def test_complete_500_frame_reader_with_mocked_physics_rejects_aggregate_tamper(tmp_path):
    bill, out = make_bill(tmp_path)
    _initial, sites, _users = geometry()
    connections = np.zeros((6, 50), dtype=bool)
    connections[0, :8] = True
    bs_links = np.zeros((6, 1), dtype=bool)
    bs_links[0, 0] = True
    info = {"contract_reward": .08, "coverage_backhauled": .16,
            "frontend_capacity_with_path_mbps": 0.0, "mean_relays_per_routed_uav": 0.0}
    routing = {0: [("uav", 0), ("ground_bs", 0)]}
    env = SimpleNamespace(current_step=0, uav_positions=sites.copy(), connections=connections,
                          uav_connections=np.zeros((6, 6), dtype=bool), uav_bs_connections=bs_links,
                          routing_paths=routing, reward_info=info)
    literal_state = {"positions_xyz": sites.tolist(), "current_step": 0,
                     "user_association": [0] * 8 + [-1] * 42, "backhauled_users_mask": [True] * 8 + [False] * 42,
                     "connections": connections.tolist(), "uav_connections": env.uav_connections.tolist(),
                     "uav_bs_connections": bs_links.tolist(), "routing_paths": evidence.plain(routing), "reward_info": info}
    path = out / "literal-500.gz"
    trace = evidence.Trace(path, bill)
    agents = [str(i) for i in range(6)]
    trace.write({"type": "initial", "world": 10, "arm": "G", "target_permutation": list(range(6)),
                 "reset": {"native_rng_sha256": "mock-constant", "agents": agents, "transmitter_mask": [True] * 6,
                           "state": literal_state}})
    for t in range(500):
        row_state = {**literal_state, "current_step": t + 1}
        trace.write({"type": "step", "t": t, "state": row_state, "actions": [[0, 0, 0]] * 6,
                     "native_rng_sha256": "mock-constant", "rewards": {str(i): .08 / 6 for i in range(6)},
                     "terminations": {str(i): t == 499 for i in range(6)}, "truncations": {str(i): False for i in range(6)}})
    trace.close()
    def mock_static(host, positions, **kwargs):
        bill.charge("static_calls")
        host.uav_positions = np.asarray(positions)
        bill.charge("static_completed")
        return info
    native = SimpleNamespace(bill=bill, host=SimpleNamespace(static_evaluate=mock_static))
    decision = {"world": 10, "arm": "G", "initial_positions_xyz": sites.tolist(), "user_positions_xy": [], "bs_xyz": [2500, 2500, 30],
                "assigned_targets_xyz": sites.tolist(), "target_permutation": list(range(6))}
    reference = {**decision, "native_rng_sha256": "mock-constant", "agents": agents, "transmitter_mask": [True] * 6, "current_step": 0}
    result = {"steps": 500, "series": {k: [v] * 500 for k, v in info.items()},
              "association_changes_per_step": [0] * 500, "backhaul_losses_per_step": [0] * 500}
    for k, v in info.items():
        result[k + "_mean_all"] = result[k + "_mean_final100"] = v
    checked = reader.trace_reader(path, env, native, decision, result, [], reference)
    assert checked["state_checks"] == 501 and bill.snapshot()["counters"]["static_calls"] == 501
    result["coverage_backhauled_mean_all"] = .5
    with pytest.raises(AssertionError, match="native aggregate"):
        reader.trace_reader(path, env, native, decision, result, [], reference)


@pytest.mark.parametrize("field", ["world", "initial_positions_xyz", "user_positions_xy", "bs_xyz", "native_rng_sha256"])
def test_fresh_reference_rejects_cross_world_mutated_geometry_and_rng(field):
    initial, sites, users = geometry()
    reference = {"world": 107100000, "initial_positions_xyz": initial.tolist(), "user_positions_xy": users.tolist(),
                 "bs_xyz": [2500, 2500, 30], "native_rng_sha256": "literal-fresh-rng", "agents": [str(i) for i in range(6)],
                 "transmitter_mask": [True] * 6, "current_step": 0}
    decision = {k: deepcopy(reference[k]) for k in ("world", "initial_positions_xyz", "user_positions_xy", "bs_xyz")}
    reset = {k: deepcopy(reference[k]) for k in ("native_rng_sha256", "agents", "transmitter_mask")}
    reset["state"] = {"current_step": 0, "positions_xyz": initial.tolist()}
    reader.verify_world_identity(decision, reset, reference)
    if field == "native_rng_sha256":
        reset[field] = "different-stored-rng"
    elif field == "world":
        decision[field] += 1
    elif field == "bs_xyz":
        decision[field][0] += 1
    else:
        decision[field][0][0] += 1
    with pytest.raises(AssertionError, match="fresh reference"):
        reader.verify_world_identity(decision, reset, reference)


def test_world_uncertainty_retains_adverse_tails_and_is_one_fit():
    result = reader.paired([-.2] + [.1] * 63)
    assert result["n"] == 64 and result["negative"] == 1 and result["min"] == -.2
    assert result["t63_95_interval"] is not None
    assert "one fitted asset" in result["uncertainty_scope"]


def test_lossless_deterministic_json_gzip_manifest_and_actual_byte_reservation(monkeypatch, tmp_path):
    bill, out = make_bill(tmp_path)
    store = evidence.Store(out, bill)
    diagnostics = [{"check": "full literal diagnostic", "passed": False, "actual": .17,
                    "expected": .18, "failure": "retained without aggregation", "fields": [None, True, 0]}] * 500
    raw = evidence.encoded(diagnostics)
    compressed = gzip.compress(raw, compresslevel=1, mtime=0)
    reservations = []
    original_check = bill.check
    def checked(**kwargs):
        reservations.append(kwargs["pending"])
        original_check(**kwargs)
    monkeypatch.setattr(bill, "check", checked)
    first = store.write_gzip("raw/checks.json.gz", diagnostics)
    second = store.write_gzip("raw/same-checks.json.gz", diagnostics)
    assert gzip.decompress(first.read_bytes()) == raw
    assert first.read_bytes() == second.read_bytes() == compressed
    assert first.read_bytes()[4:8] == b"\x00\x00\x00\x00"
    assert reservations == [len(compressed) + 65536] * 2
    assert len(compressed) < len(raw)
    metadata = store.files["raw/checks.json.gz"]
    assert metadata == {"sha256": evidence.sha(first), "bytes": len(compressed), "content_format": "gzip-json",
                        "uncompressed_bytes": len(raw), "record_count": 500}
    evidence.verify_outputs(out, store.files)
    assert json.loads((out / "artifact-manifest.json").read_bytes())["files"]["raw/checks.json.gz"] == metadata
    with pytest.raises(FileExistsError):
        store.write_gzip("raw/checks.json.gz", diagnostics)
    def refuse(**kwargs):
        assert kwargs["pending"] == len(compressed) + 65536
        raise RuntimeError("fixture disk budget refusal")
    monkeypatch.setattr(bill, "check", refuse)
    with pytest.raises(RuntimeError, match="disk budget refusal"):
        store.write_gzip("refused/checks.json.gz", diagnostics)
    assert not (out / "refused").exists()
    assert gzip.decompress(first.read_bytes()) == raw
