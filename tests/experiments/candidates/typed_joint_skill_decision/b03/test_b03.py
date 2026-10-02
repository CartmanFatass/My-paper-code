"""Pure arithmetic, literal streams and mocks; no actual host, RNG draw, fit or native query."""
from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import threading
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.typed_joint_skill_decision.b02 import evidence as e, search as old
from experiments.candidates.typed_joint_skill_decision.b03 import budget, prefix, reader, run


def candidate(i=0, reward=0.):
    return {"index": i, "kind": "subset_relay", "k": 5,
            "positions_xyz": [[0., 0., 50.] for _ in range(6)], "contract_reward": reward,
            "coverage_backhauled": .2, "potential": 100000.}


def fake_planner(mode):
    calls = []
    env = SimpleNamespace(n_uavs=6, area_size=5000, last=None)
    def clip(env, x):
        x = x.copy()
        x[:, :2] = np.clip(x[:, :2], 0, 5000)
        x[:, 2] = np.clip(x[:, 2], 50, 150)
        return x
    def score(env, x, allow_a2a):
        x = np.asarray(x, dtype=float)
        env.last = x.copy()
        calls.append(x.tolist())
        reward = float(x[:, 0].sum()) / 100000 if mode == "reward" else 0.
        return {"contract_reward": reward, "coverage_backhauled": .2, "uav_connection_count": 0}
    def potential(env, allow):
        return 100000. - float(env.last[:, 1].sum()) if mode == "plateau" else 100000.
    p = SimpleNamespace(XY_STEPS_M=(100., 50., 25.), Z_STEP_M=50., IMPROVEMENT_TOL=1e-12,
                        POTENTIAL_TOL=1e-9, _clip_positions=clip, static_evaluate=score, plateau_potential=potential)
    return env, p, calls


@pytest.mark.parametrize("mode", ["reward", "plateau", "constant"])
@pytest.mark.parametrize("share", [0, 17, 36, 41, 137])
def test_suspended_mid_sweep_matches_original_branch(mode, share):
    env, p, calls = fake_planner(mode)
    c = candidate()
    state = prefix.new_state(c, 0, share, 3)
    gen = prefix.suspended_branch(env, p, state)
    prefix.advance(gen, 36)
    snapshot = deepcopy(e.plain(state))
    # Switching branches mutates the last trial; resumed acceptance may not read it.
    other = prefix.new_state(candidate(1), 1, 41, 3)
    prefix.advance(prefix.suspended_branch(env, p, other), 36)
    other_calls = len(calls)
    list(gen)
    prefix_calls = calls[:snapshot["used"]] + calls[other_calls:]
    reference_env, reference_p, reference_calls = fake_planner(mode)
    positions, record, history = old.branch(reference_env, reference_p, c, 0, share, 3)
    assert prefix_calls == reference_calls
    assert e.plain(state["positions_xyz"]) == positions.tolist()
    assert prefix.record(state, p) == record
    assert state["history"] == history
    assert state["done"]
    assert snapshot["used"] <= 36
    if mode == "reward" and share > 36:
        assert snapshot["moved"] and snapshot["move_index"] != 5
        assert state["accepted_descent"] > 0
    if mode == "plateau" and share > 36:
        assert state["accepted_plateau"] > 0


def test_suspension_against_actual_upstream_loop_with_mock_evaluator(monkeypatch):
    from experiments.candidates.coupled_host_joint_skills_stage1 import planner as source
    env, p, calls = fake_planner("plateau")
    def build(env, rng, allow, report):
        report["fixture"] = True
        return [candidate(i) for i in range(3)]
    monkeypatch.setattr(source, "build_candidates", build)
    monkeypatch.setattr(source, "static_evaluate", p.static_evaluate)
    monkeypatch.setattr(source, "plateau_potential", p.plateau_potential)
    monkeypatch.setattr(source, "_clip_positions", p._clip_positions)
    monkeypatch.setattr(source, "link_ranges", lambda env: {})
    # Opaque token satisfies the explicit-RNG API; no generator is created or drawn.
    result = source.search_placement(env, True, 414, object())
    full = deepcopy(calls)
    calls.clear()
    states = [prefix.new_state(c, r, result.starts[r]["share"], 3) for r, c in enumerate(result.candidates)]
    gens = [prefix.suspended_branch(env, p, s) for s in states]
    for g in gens:
        prefix.advance(g, 36)
    for g in gens:
        list(g)
    for r, state in enumerate(states):
        source_record = result.starts[r]
        for key, value in prefix.record(state, p).items():
            if key not in ("began_at_evaluation", "ended_at_evaluation"):
                assert value == source_record[key]
        start = source_record["began_at_evaluation"]
        expected = reader.old.path_signature(result.history, r, start)
        assert reader.old.path_signature(state["history"], r, 3) == expected
    assert len(calls) == len(full) - 3


def reference_fixture():
    starts = [{"start": r, "candidate_index": r, "start_reward": .3, "final_reward": .3,
               "share": 50, "evaluations": n, "began_at_evaluation": 3 + sum([40, 45, 20][:r])}
              for r, n in enumerate([40, 45, 20])]
    ref = {"flat": {"evaluations": 2}, "relay": {"candidates_evaluated": 3, "starts": starts,
           "candidates": [candidate(r, .3) for r in range(3)], "history": []}}
    tape = [{"positions_xyz": candidate()["positions_xyz"], "allow_a2a": True,
             "info": {"marker": i}} for i in range(111)]
    return ref, tape


def test_query_sequence_counts_and_rejected_trial_tamper():
    ref, tape = reference_fixture()
    q = {"arm": "Q", "requested_rank": 1, "positions_xyz": candidate()["positions_xyz"]}
    sequence = reader.query_sequence(ref, tape, q)
    # fullflat+initial +36+36+early20 +chosen45-36 +metadata
    assert len(sequence) == 2 + 3 + 36 + 36 + 20 + 9 + 1
    assert sequence[5:41] == tape[5:41]
    assert sequence[41:77] == tape[45:81]
    assert sequence[97:106] == tape[81:90]
    diagnostics = []
    tampered = deepcopy(sequence[12])
    tampered["info"]["marker"] += 1
    with pytest.raises(AssertionError, match="exact mismatch"):
        reader.exact(tampered, sequence[12], "rejected static result", diagnostics)
    assert diagnostics[-1]["passed"] is False
    assert reader.q_projection(ref)["rank"] == 0  # exact prefix tie picks lower original rank


def test_signed_zero_and_permutation_are_not_aliases():
    positive = np.zeros((6, 3))
    negative = positive.copy()
    negative[0, 0] = -0.
    assert np.array_equal(positive, negative)
    assert reader.f64_digest(positive) != reader.f64_digest(negative)
    with pytest.raises(AssertionError):
        reader.exact(list(range(6)), [1, 0, 2, 3, 4, 5], "permutation", [])
    with pytest.raises(ValueError):
        reader.f64_digest([[float("nan")] * 3] * 6)


def make_bill(tmp_path):
    roots = [tmp_path / k for k in ("source", "prior", "out")]
    for p in roots:
        p.mkdir()
    return budget.Bill([0] * len(budget.COUNTERS), threading.Lock(), roots), roots


@pytest.mark.parametrize("counter,cap", [("fits", 0), ("native_steps", 4500), ("static_calls", 1155699)])
def test_attempt_caps_and_immutable_b02_limits(tmp_path, counter, cap):
    bill, roots = make_bill(tmp_path)
    before = deepcopy(e.LIMITS)
    bill.values[budget.COUNTERS.index(counter)] = cap
    with pytest.raises(RuntimeError, match="limit exceeded"):
        bill.charge(counter)
    assert bill.snapshot()["counters"][counter] == cap + 1
    assert e.LIMITS == before


def test_cpu_disk_and_lossless_gzip_binding(tmp_path, monkeypatch):
    bill, roots = make_bill(tmp_path)
    monkeypatch.setattr(e, "cpu", lambda: {"total_seconds": 1800.01})
    with pytest.raises(RuntimeError, match="CPU"):
        bill.check()
    monkeypatch.setattr(e, "cpu", lambda: {"total_seconds": 0.})
    bill.disk_peak = budget.LIMITS["disk_bytes"] - 5
    with pytest.raises(RuntimeError, match="disk"):
        bill.check(sample_disk=False, pending=6)
    bill.disk_peak = 0
    store = e.Store(roots[-1], bill)
    data = [{"passed": False, "error": "all adverse evidence", "negative_zero": -0.0}]
    path = store.write_gzip("raw/reader/checks.json.gz", data)
    assert gzip.decompress(path.read_bytes()) == e.encoded(data)
    assert store.files["raw/reader/checks.json.gz"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_prior_membership_and_byte_tamper(tmp_path):
    prior = reader.Prior.__new__(reader.Prior)
    prior.root, prior.files, prior.used = tmp_path, {}, {}
    with pytest.raises(ValueError, match="unlisted"):
        prior.bytes("selection.json")
    path = tmp_path / "selection.json"
    path.write_bytes(b"{}\n")
    prior.files["selection.json"] = {"bytes": 3, "sha256": e.sha(path)}
    assert prior.json("selection.json") == {}
    path.write_bytes(b"[]\n")
    with pytest.raises(ValueError, match="byte mismatch"):
        prior.bytes("selection.json")


def test_child_rejects_future_information_before_any_import(tmp_path):
    with pytest.raises(RuntimeError, match="legal-only"):
        run.checked_child({"alias_rows": [], "parent_pid": os.getppid()})


def test_real_launcher_guard_and_admission_refusal_before_effects(tmp_path, monkeypatch):
    from scripts.hmasd_launch import _validate_guard_contract, OUTPUT_ARGUMENTS
    _validate_guard_contract(Path(run.__file__), "typed_joint_skill_decision")
    assert "--out" in OUTPUT_ARGUMENTS
    from scripts import hmasd_admission
    def refuse(*args, **kwargs):
        raise RuntimeError("fixture admission refusal")
    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    monkeypatch.setattr(run, "threads", lambda: pytest.fail("effect before admission"))
    with pytest.raises(RuntimeError, match="admission refusal"):
        run.main(["--out", str(tmp_path / "out"), "--launch-sha", "a" * 40, "--seed", "0",
                  "--input-manifest", str(tmp_path / "input"), "--input-manifest-sha256", "b" * 64])
    assert not (tmp_path / "out").exists()


def test_complete_count_assertion_rejects_missing_or_extra_attempt():
    counts = {k: 0 for k in budget.COUNTERS}
    with pytest.raises(AssertionError, match="exact work"):
        run.complete_counts(counts, [])


def test_complete_alias_reader_rejects_rng_and_keeps_adverse_fields(tmp_path):
    bill, roots = make_bill(tmp_path)
    positions = [[100. + i * 300, 200., 100.] for i in range(6)]
    info = {"contract_reward": .08, "coverage_backhauled": .16, "throughput_term": 0.,
            "frontend_capacity_with_path_mbps": 0., "mean_relays_per_routed_uav": 0.}
    state = {"positions_xyz": positions, "current_step": 0, "user_association": [0] * 8 + [-1] * 42,
             "routing_paths": {"0": [["uav", 0], ["ground_bs", 0]]},
             "backhauled_users_mask": [True] * 8 + [False] * 42, "reward_info": info}
    reset = {"native_rng_sha256": "literal-constant", "agents": [str(i) for i in range(6)],
             "transmitter_mask": [True] * 6, "state": state}
    decision = {"world": 107100001, "arm": "Q", "target_permutation": list(range(6)), "assigned_targets_xyz": positions}
    initial = {"type": "initial", "world": decision["world"], "arm": "L", "reset": reset,
               "target_permutation": list(range(6)), "assigned_targets_xyz": positions}
    rows = [initial] + [{"type": "step", "t": t, "state": {**state, "current_step": t + 1},
                        "actions": [[0., 0., 0.]] * 6, "native_rng_sha256": "literal-constant",
                        "rewards": {str(i): .08 / 6 for i in range(6)},
                        "terminations": {str(i): t == 499 for i in range(6)},
                        "truncations": {str(i): False for i in range(6)}} for t in range(500)]
    path = roots[-1] / "alias.gz"
    def save():
        path.write_bytes(gzip.compress(b"".join(e.encoded(r) for r in rows), mtime=0))
    save()
    result = {"steps": 500, "arrival_step": 0, "final_max_distance_to_target_m": 0.,
              "series": {k: [info[k]] * 500 for k in reader.SERIES},
              "association_changes_per_step": [0] * 500, "backhaul_losses_per_step": [0] * 500}
    for k in reader.SERIES:
        result[k + "_mean_all"] = result[k + "_mean_final100"] = info[k]
    result_read = reader.reaggregate(path, decision, result, [], reset, bill)
    assert result_read["contract_reward"]["mean_all"] == pytest.approx(.08)
    assert bill.snapshot()["counters"]["static_calls"] == 0
    rows[32]["native_rng_sha256"] = "different"
    save()
    diagnostics = []
    with pytest.raises(AssertionError, match="RNG"):
        reader.reaggregate(path, decision, result, diagnostics, reset, bill)
    assert diagnostics[-1]["passed"] is False


def test_failed_child_is_not_retried_and_partial_stream_is_bound(tmp_path):
    bill, roots = make_bill(tmp_path)
    store = e.Store(roots[-1], bill)
    relative = "raw/main/107100000/G/search-queries.jsonl.gz"
    path = e.relative_path(store.root, relative)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"partial gzip retained")
    messages = [{"kind": "failed", "paths": [relative], "error": "literal interrupted child"}]
    class Connection:
        def poll(self, timeout=0):
            return bool(messages)
        def recv(self):
            return messages.pop(0)
        def close(self):
            pass
    starts = []
    class Process:
        pid = None
        exitcode = 1
        def start(self):
            starts.append(True)
        def is_alive(self):
            return False
        def join(self):
            pass
    ctx = SimpleNamespace(Pipe=lambda **kw: (Connection(), Connection()), Process=lambda **kw: Process())
    with pytest.raises(RuntimeError, match="without retry"):
        run.spawn_case(ctx, {}, bill, store, None, [], 107100000, "G")
    assert len(starts) == 1 and bill.snapshot()["counters"]["spawn_completed"] == 0
    assert store.files[relative]["sha256"] == e.sha(path)
    assert json.loads((store.root / "progress.json").read_bytes())["phase"] == "child_failed"


def test_q_common_construction_and_all_request_streams_match_saved_reference(monkeypatch):
    from experiments.candidates.coupled_host_joint_skills_stage1 import planner as source
    env, p, calls = fake_planner("plateau")
    env.uav_positions = np.asarray(candidate()["positions_xyz"])
    env.user_positions = np.asarray([[i * 10., i * 20.] for i in range(50)])
    env.ground_bs_positions = np.array([[2500., 2500., 30.]])
    tape = []
    def build(env, rng, allow, report):
        report["fixture"] = True
        return [candidate(i) for i in range(3)]
    def static(env, x, allow_a2a):
        info = p.static_evaluate(env, x, allow_a2a)
        tape.append({"positions_xyz": e.plain(x), "allow_a2a": allow_a2a, "info": info})
        return info
    monkeypatch.setattr(source, "build_candidates", build)
    monkeypatch.setattr(source, "static_evaluate", static)
    monkeypatch.setattr(source, "plateau_potential", p.plateau_potential)
    monkeypatch.setattr(source, "_clip_positions", p._clip_positions)
    monkeypatch.setattr(source, "link_ranges", lambda env: {})
    monkeypatch.setattr(np.random, "default_rng", lambda *args: object())
    flat = source.search_placement(env, False, 3000, object())
    relay = source.search_placement(env, True, 3000, object(), extra_candidates=[flat.positions_xyz])
    static(env, relay.positions_xyz, True)
    reference = {"flat": old.search_json(flat), "relay": old.search_json(relay)}
    saved = deepcopy(tape)
    tape.clear()
    decision = prefix.choose(env, source, 107100000, "Q")
    expected = reader.query_sequence(reference, saved, decision)
    assert e.encoded(tape) == e.encoded(expected)
    projected = reader.q_projection(reference)
    assert decision["requested_rank"] == projected["rank"]
    assert decision["prefix_rewards"] == projected["prefix_rewards"]
    assert decision["positions_xyz"] == projected["positions_xyz"]
    assert decision["relay"]["evaluations"] + decision["flat"]["evaluations"] + 1 == len(tape)
