"""Pure bookkeeping and mocked trace checks: no actual RF/G/NN/world draws."""
import ast
from contextlib import nullcontext
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_decision_generalization.b05_request_schedule import reader as r


class Meter:
    def __init__(self):
        self.counts = {}

    def add(self, name, amount=1):
        self.counts[name] = self.counts.get(name, 0) + amount

    def check(self):
        return self.report()

    def report(self):
        return {"counts": dict(self.counts), "cumulative_cpu_seconds": 0., "phase_cpu_seconds": 0.}


@pytest.fixture(autouse=True)
def forbid_scientific_calls(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("actual RF/G/NN/world reconstruction is outside implementation checks")
    for name in ("physical_state", "motion", "predict_g", "geometry", "future_arrivals"):
        monkeypatch.setattr(r, name, forbidden)
    monkeypatch.setattr(r.FrozenModels, "infer", forbidden)


def synthetic_public(tick=1180):
    return {"world": 0, "tick": tick, "users": np.full((50, 2), 2500, dtype=np.int32),
            "rates": np.asarray([6, 3, 2, 1], dtype=np.uint8),
            "positions": np.tile([2500., 2500., 100.], (6, 1)),
            "ack": np.zeros(50, dtype=bool), "counts": np.asarray([1, 0, 0, 0]),
            "progress": np.zeros(4, dtype=np.int64), "slots": np.arange(6, dtype=np.uint8),
            "pairs": np.arange(6, dtype=np.uint8).reshape(3, 2)}


def state_row(state, tick=None):
    row = np.zeros((), dtype=r.STATE_DTYPE)
    for name in ("positions", "counts", "progress", "slots"):
        row[name] = state[name]
    row["tick"] = state["tick"] if tick is None else tick
    row["routes"] = -1
    row["ack"] = r.packed(state["ack"])
    return row


def g_row(state, costs=None):
    row = np.zeros((), dtype=r.G_DTYPE)
    for name in ("positions", "counts", "progress", "slots", "tick"):
        row[name] = state[name]
    row["ack"] = r.packed(state["ack"])
    row["costs"] = np.full(4, 260.) if costs is None else costs
    row["complete"] = 1
    return row


def empty_rollout():
    arrays = {name: np.zeros(shape, dtype=dtype) for name, (shape, dtype) in r.R_SHAPES.items()}
    for name in ("g_links", "branch_action", "branch_tape", "tape_times", "cohort_reuse", "cohort_branches"):
        arrays[name][:] = -1
    return arrays


def terminal_rollout(monkeypatch):
    """Four mocked20-step branches, followed by three exact empty-tape reuses."""
    state = synthetic_public()
    arrays = empty_rollout()
    arrays["initial"][0] = state_row(state)
    arrays["g"][0] = g_row(state)
    rotation = (state["world"] + state["tick"] // 20) % 4
    order = np.roll(np.arange(4), -rotation)
    branch_ids = np.argsort(order)
    for branch, action in enumerate(order):
        arrays["rows"][branch] = 21
        arrays["branch_action"][branch] = action
        arrays["branch_tape"][branch] = 0
        arrays["branch_complete"][branch] = 1
        arrays["branch_cost"][branch] = 260.
        arrays["tick_cost"][branch, :20] = 1
        for offset in range(21):
            arrays["states"][branch, offset] = state_row(state, 1180 + offset)
    arrays["tape_complete"][:] = 1
    arrays["cohort_complete"][:] = 1
    arrays["cohort_reuse"][:] = [-1, 0, 0, 0]
    arrays["cohort_costs"][:] = 260.
    arrays["cohort_branches"][:] = branch_ids
    key = r.wire_key(state, np.empty(0, dtype=np.int64), np.empty((0, 4), dtype=bool), "mock-source")
    arrays["cohort_input_sha256"][:] = np.frombuffer(bytes.fromhex(key), dtype=np.uint8)
    arrays["cohort_ready_ns"][:] = [2000, 3000, 4000, 5000]
    stats = {name: 0 for name in r.R_STATS}
    stats.update(initial_attempts=1, initial_complete=1, clone_attempts=4, clones=4,
                 native_attempts=80, native_complete=80, g_attempts=1, g_complete=1,
                 g_reserved_candidate_ticks=80, g_complete_candidate_ticks=80,
                 tape_attempts=4, tape_draws=4, cohorts_complete=4, cohorts_reused=3)
    arrays["stats"][:] = [stats[name] for name in r.R_STATS]
    events = {name: 0 for name in r.c.NATIVE_EVENT_NAMES}
    events.update(native_step_calls=80, native_steps=80)
    arrays["native_events"][:] = [events[name] for name in r.c.NATIVE_EVENT_NAMES]
    cohorts = [{"tape": index, "times": [], "bits": [], "input_sha256": key,
                "reused_cohort": None if index == 0 else 0,
                "branches": branch_ids.tolist(), "costs": [260.] * 4} for index in range(4)]
    timing = {"start_ns": 1000, "deadline_ns": 20_000_001_000, "command_fixed_ns": 10000,
              "reaped_ns": 10000, "deadline_expired": False, "completed_request": True,
              "messages": [{"type": "fallback", "ready_ns": 1100, "received_ns": 1101, "eligible": True}]
              + [{"type": "cohort", "ready_ns": time + 1, "received_ns": time + 2, "eligible": True}
                 for time in (2000, 3000, 4000, 5000)]
              + [{"type": "done", "ready_ns": 9000, "received_ns": 9001, "eligible": True}]}
    physical_calls = []
    def mocked_physical(positions, users):
        physical_calls.append(1)
        return {"connections": np.zeros((6, 50), dtype=bool),
                "uav_connections": np.zeros((6, 6), dtype=bool),
                "bs_connections": np.zeros((6, 1), dtype=bool),
                "routes": np.full((6, 7), -1), "route_lengths": np.zeros(6, dtype=int)}
    monkeypatch.setattr(r, "physical_state", mocked_physical)
    monkeypatch.setattr(r, "motion", lambda positions, raw: (raw, positions.copy(), 0))
    monkeypatch.setattr(r, "future_arrivals", lambda *_args:
                        (np.empty(0, dtype=np.int64), np.empty((0, 4), dtype=bool)))
    return arrays, state, {"timing": timing, "cohorts": cohorts}, physical_calls


def test_fixed_roster_shapes_and_no_parent_thread_setters():
    roster = r.expected_roster()
    assert len(roster) == len(set(roster)) == 1708
    assert sum(label.startswith("train/") for label, _ in roster) == 1536
    assert sum(label.endswith("/R") for label, _ in roster) == 35
    assert roster[0] == ("train/fit0", 109250000)
    assert roster[1536:1541] == [("main/" + name, 109253000) for name in ("G", "R", "L0", "L1", "L2")]
    module = ast.parse(Path(r.__file__).read_text())
    setters = [node.func.attr for node in ast.walk(module) if isinstance(node, ast.Call)
               and isinstance(node.func, ast.Attribute) and node.func.attr in
               ("set_num_threads", "set_num_interop_threads", "use_deterministic_algorithms")]
    assert setters == []
    assert r.MISSION_SHAPES["states"][0] == (1201,)
    assert r.MISSION_SHAPES["initial_audit_complete"][0] == (60,)


def test_actual_native_reward_counts_follow_two_inherited_dispatches():
    root = Path(r.__file__).resolve().parents[4]
    for filename, classname in (("uav_env.py", "MultiUAVEnv"),
                                ("scenario2.py", "UAVCooperativeNetworkEnv")):
        tree = ast.parse((root / "envs/pettingzoo" / filename).read_text())
        host_class = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                          and node.name == classname)
        step = next(node for node in host_class.body if isinstance(node, ast.FunctionDef)
                    and node.name == "step")
        calls = [node for node in ast.walk(step) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and node.func.attr == "_compute_reward"]
        assert len(calls) == 1
    adapter = root / "experiments/candidates/uav_decision_generalization/b03_joint_window/adapter.py"
    tree = ast.parse(adapter.read_text())
    host_class = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                      and node.name == "RegisteredHost")
    reward = next(node for node in host_class.body if isinstance(node, ast.FunctionDef)
                  and node.name == "_compute_reward")
    increments = [node.target.slice.value for node in ast.walk(reward)
                  if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Subscript)
                  and isinstance(node.target.slice, ast.Constant) and isinstance(node.value, ast.Constant)
                  and node.value.value == 1]
    assert increments == ["dense_reward_entries", "parent_reward_entries"]
    events = dict.fromkeys(r.c.NATIVE_EVENT_NAMES, 0)
    events.update(constructor_calls=1, reset_calls=1, registry_calls=1,
                  native_step_calls=1200, native_steps=1200, dense_reward_entries=2400,
                  parent_reward_entries=2400, constructor_topology_restorations=1)
    r.check_actual_native_events(events)
    with pytest.raises(AssertionError, match="dense_reward_entries"):
        r.check_actual_native_events({**events, "dense_reward_entries": 1200})


def test_scalar_FIFO_residence_interruption_twentieth_tick_and_unknown_ages():
    ledger = r.FIFO()
    qualified = np.zeros(50, dtype=bool)
    qualified[10:18] = True
    for tick in range(20):
        ledger.arrive(tick, [tick == 0, False, False, False])
        assert ledger.charge() == 1
        ledger.service(tick, qualified)
    assert ledger.area == 20 and ledger.counts[0] == 0
    assert ledger.completions == [{"request": {"request_id": 0, "cluster": 0, "arrival_tick": 0},
                                   "completion_tick": 20}]
    ledger.arrive(20, [True, False, False, False])
    ledger.charge()
    ledger.service(20, qualified)
    ledger.service(21, np.zeros(50, dtype=bool))
    assert ledger.progress[0] == 0 and ledger.interruptions[0] == 1
    model = r.FIFO([2, 0, 0, 0], [19, 0, 0, 0])
    assert all(item["arrival_tick"] is None and item["request_id"] is None for item in model.queues[0])
    model.charge()
    model.service(1180, qualified)
    assert model.counts[0] == 1 and model.progress[0] == 0


def test_packing_float64_ties_and_typed_hash_known_bytes():
    bits = np.zeros(50, dtype=bool)
    bits[[0, 49]] = True
    np.testing.assert_array_equal(r.unpack(r.packed(bits), (50,)), bits)
    corrupt = r.packed(bits)
    corrupt[-1] |= 128
    with pytest.raises(AssertionError, match="padding"):
        r.unpack(corrupt, (50,))
    raw = np.asarray([0., 8., 7., 1.])
    assert r.greedy(np.asarray([1 + 1e-10, 1., 1., 2.]), raw) == 2
    assert r.compose(raw, np.zeros(4, dtype=np.float32)).dtype == np.float64
    left, right = np.zeros((1, 2), dtype=np.float32), np.asarray([3.], dtype=np.float64)
    row = (left, right, 0, 1, None, None, True)
    digest = hashlib.sha256()
    digest.update(b"list1")
    r.hash_replay_row(digest, row)
    literal = (b"list1tuple7array<f4(1, 2)" + left.tobytes() + b"array<f8(1,)" + right.tobytes()
               + b"int0;int1;NoneTypeNone;NoneTypeNone;boolTrue;")
    assert digest.hexdigest() == hashlib.sha256(literal).hexdigest()
    state = synthetic_public()
    empty_times, empty_tape = np.empty(0, dtype=np.int64), np.empty((0, 4), dtype=bool)
    original = r.wire_key(state, empty_times, empty_tape, "source")
    assert original != r.wire_key({**state, "world": 1}, empty_times, empty_tape, "source")
    assert original != r.wire_key(state, empty_times, empty_tape, "changed-source")


def test_complete_R_duplicate_base_once_empty_tape_exact_reuse_and_counts(monkeypatch):
    arrays, state, selected, physical_calls = terminal_rollout(monkeypatch)
    audit = r.Audit(Meter(), "mock-source")
    answer = r.rollout_read(arrays, state, arrays["g"][0], selected, audit)
    assert len(physical_calls) == 81  # one shared initial,80 paid successors,not4 cloned resets.
    assert audit.counts["R_initial_physical_states"] == 1
    assert audit.counts["R_prefix_physical_states"] == 80
    assert audit.counts["G_duplicate_R_base_records"] == 1
    assert audit.counts.get("G_attempts", 0) == 0
    assert answer["committed_cohorts"] == answer["selected_cohorts"] == 4
    assert answer["reused_cohorts"] == 3
    assert all(branch["cost"] == 260 for branch in answer["branches"])
    assert answer["commit_counter_gaps"] == dict(tapes=0, G=0, native=0, cohorts=0)


def test_late_complete_work_and_unused_candidates_are_read(monkeypatch):
    arrays, state, selected, _ = terminal_rollout(monkeypatch)
    selected["cohorts"] = []
    selected["timing"].update(deadline_expired=True, completed_request=False,
                             command_fixed_ns=20_000_001_010, reaped_ns=20_000_001_100)
    selected["timing"]["messages"] = selected["timing"]["messages"][:1]
    arrays["tape_complete"][1:] = 0
    arrays["cohort_complete"][:] = 0
    for name, value in dict(tape_attempts=1, tape_draws=1, cohorts_complete=0, cohorts_reused=0).items():
        arrays["stats"][r.R_STATS.index(name)] = value
    answer = r.rollout_read(arrays, state, arrays["g"][0], selected, r.Audit(Meter(), "mock-source"))
    assert answer["committed_cohorts"] == answer["selected_cohorts"] == 0
    assert answer["completed_unused_branches"] == [0, 1, 2, 3]
    assert len(answer["branches"]) == 4
    assert r.marker_gap(10, 9, True, "cancel") == 1
    with pytest.raises(AssertionError):
        r.marker_gap(10, 9, False, "complete")
    with pytest.raises(AssertionError):
        r.marker_gap(10, 11, True, "counter ahead")


def test_reader_bounds_refuse_before_any_reconstruction(monkeypatch):
    meter, state = Meter(), synthetic_public()
    audit = r.Audit(meter, "mock-source")
    for role, maximum in (("native", 2051308), ("R_prefix", 4424000), ("R_initial", 2100)):
        audit.counts[role + "_physical_attempts"] = maximum
        with pytest.raises(AssertionError, match="exposure bound"):
            audit.physics(state_row(state), state["users"], role)
    audit.counts["G_reserved_candidate_ticks"] = 292844160
    with pytest.raises(AssertionError, match="exposure bound"):
        audit.g(g_row(state), state, "mock")
    frozen = r.FrozenModels.__new__(r.FrozenModels)
    frozen.audit = audit
    audit.counts["neural_attempted_rows"] = 24480
    # Bind the real method; autouse guard otherwise prevents accidental calls.
    infer_source = ast.parse(Path(r.__file__).read_text())
    assert any(isinstance(node, ast.Constant) and node.value == 24480 for node in ast.walk(infer_source))
    with pytest.raises(AssertionError, match="exposure bound"):
        audit.reserve("neural_attempted_rows", 24480, 4)


def cancelled_selection(selected, cohorts):
    selected["cohorts"] = selected["cohorts"][:cohorts]
    selected["timing"].update(deadline_expired=True, completed_request=False,
                             command_fixed_ns=20_000_001_010, reaped_ns=20_000_001_100)
    selected["timing"]["messages"] = selected["timing"]["messages"][:1 + cohorts]


def test_cancelled_marker_gap_cannot_precede_later_committed_work(monkeypatch):
    arrays, state, selected, _ = terminal_rollout(monkeypatch)
    cancelled_selection(selected, 3)
    arrays["cohort_complete"][3] = 0
    for name, value in dict(tape_draws=3, cohorts_complete=3, cohorts_reused=2).items():
        arrays["stats"][r.R_STATS.index(name)] = value
    result = r.rollout_read(arrays, state, arrays["g"][0], selected, r.Audit(Meter(), "mock-source"))
    assert result["commit_counter_gaps"]["tapes"] == 1
    arrays["cohort_complete"][3] = 1
    with pytest.raises(AssertionError, match="tape counter gap must be final"):
        r.rollout_read(arrays, state, arrays["g"][0], selected, r.Audit(Meter(), "mock-source"))

    arrays, state, selected, _ = terminal_rollout(monkeypatch)
    cancelled_selection(selected, 0)
    arrays["tape_complete"][1:] = 0
    arrays["cohort_complete"][:] = 0
    arrays["branch_complete"][3] = 0
    for name, value in dict(tape_attempts=1, tape_draws=1, native_complete=79,
                           cohorts_complete=0, cohorts_reused=0).items():
        arrays["stats"][r.R_STATS.index(name)] = value
    result = r.rollout_read(arrays, state, arrays["g"][0], selected, r.Audit(Meter(), "mock-source"))
    assert result["commit_counter_gaps"]["native"] == 1
    arrays["branch_complete"][3] = 1
    with pytest.raises(AssertionError, match="native counter gap"):
        r.rollout_read(arrays, state, arrays["g"][0], selected, r.Audit(Meter(), "mock-source"))
    arrays["branch_complete"][0] = 0
    with pytest.raises(AssertionError, match="only the last started"):
        r.rollout_read(arrays, state, arrays["g"][0], selected, r.Audit(Meter(), "mock-source"))

    arrays, state, selected, _ = terminal_rollout(monkeypatch)
    cancelled_selection(selected, 2)
    arrays["tape_complete"][3] = 0
    arrays["cohort_complete"][3] = 0
    for name, value in dict(tape_attempts=3, tape_draws=3, cohorts_complete=2, cohorts_reused=2).items():
        arrays["stats"][r.R_STATS.index(name)] = value
    result = r.rollout_read(arrays, state, arrays["g"][0], selected, r.Audit(Meter(), "mock-source"))
    assert result["commit_counter_gaps"]["cohorts"] == 1
    arrays["tape_complete"][3] = 1
    arrays["stats"][r.R_STATS.index("tape_attempts")] = 4
    arrays["stats"][r.R_STATS.index("tape_draws")] = 4
    with pytest.raises(AssertionError, match="cohort counter gap"):
        r.rollout_read(arrays, state, arrays["g"][0], selected, r.Audit(Meter(), "mock-source"))


def test_arrays_bound_hash_path_and_finite_validation(tmp_path):
    path = tmp_path / "trace.npz"
    np.savez(path, vector=np.arange(4, dtype=np.float64))
    arrays = r.load_arrays(path, {"vector": ((4,), "float64")})
    np.testing.assert_array_equal(arrays["vector"], np.arange(4))
    with pytest.raises(AssertionError, match="shape/dtype"):
        r.load_arrays(path, {"vector": ((4,), "float32")})
    with pytest.raises(AssertionError, match="roster"):
        r.load_arrays(path, {"other": ((4,), "float64")})
    np.savez(path, vector=np.asarray([0., 1., np.nan, 3.]))
    with pytest.raises(AssertionError, match="nonfinite"):
        r.load_arrays(path, {"vector": ((4,), "float64")})
    with pytest.raises(AssertionError, match="contained"):
        r.contained(tmp_path, "../escape")
    assert r.file_hash(path) == hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_checks_every_required_hash_and_preserves_roster(tmp_path, monkeypatch):
    record = {"label": "train/fit0", "world": 0, "npz": "trace.npz", "metadata": "trace.json",
              "status": "COMPLETE", "completed_native_steps": 1200}
    names = {"trace.npz", "trace.json", "endpoint-counts.json"}
    names |= {f"fit{fit}.json" for fit in range(3)}
    names |= {f"checkpoints/fit{fit}_{endpoint}.pt" for fit in range(3)
              for endpoint in ("initial", "final", "training")}
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]" if name == "endpoint-counts.json" else "pure-mock-bytes")
    files = {name: {"bytes": (tmp_path / name).stat().st_size, "sha256": r.file_hash(tmp_path / name)}
             for name in names}
    fits = [{"fit": fit} for fit in range(3)]
    manifest = dict(schema=1, records=[record], fits=fits, endpoint_counts=[], files=files)
    summary = dict(schema=1, status="COMPLETE", object="B05_request_schedule", missions=1708,
                   source_identity="mock-source", fits=fits, endpoint_counts=[],
                   cost={"counts": {"actual_native_steps": 2049600}})
    monkeypatch.setattr(r, "expected_roster", lambda: [("train/fit0", 0)])
    meter = Meter()
    assert r.validate_manifest(tmp_path, manifest, summary, "mock-source", meter) == [record]
    assert meter.counts["reader_file_hashes"] == len(names)
    (tmp_path / "trace.npz").write_text("corrupt-same-bytes")
    with pytest.raises(AssertionError, match="file/size|byte hash"):
        r.validate_manifest(tmp_path, manifest, summary, "mock-source", Meter())


def test_saved_deadline_selection_uses_receipt_not_reader_speed():
    timing = {"start_ns": 100, "deadline_ns": 20_000_000_100,
              "command_fixed_ns": 20_000_000_200, "reaped_ns": 20_000_000_300,
              "completed_request": True, "deadline_expired": True,
              "messages": [{"type": "result", "ready_ns": 20_000_000_090,
                            "received_ns": 20_000_000_150, "eligible": False}]}
    assert r.check_timing(timing) == []
    timing["messages"][0]["eligible"] = True
    with pytest.raises(AssertionError, match="eligibility"):
        r.check_timing(timing)


def test_conditional_t_summary_dimensions():
    result = r.paired_t(np.arange(32, dtype=float), "fixed32worldmock")
    assert result["n"] == 32 and result["df"] == 31
    assert result["mean"] == 15.5 and result["confidence"] == .95
    assert result["interval"][0] < 15.5 < result["interval"][1]
    fits = r.paired_t(np.asarray([1., 2., 3.]), "samepanel")
    assert fits["n"] == 3 and fits["df"] == 2


def test_training_reader_warmup_terminal_mask_and_separate_mocked_streams(monkeypatch):
    streams = []
    class Random:
        def __init__(self, address):
            self.address, self.samples = address, []
            streams.append(self)
        def random(self):
            return .5
        def choice(self, population, *, size, replace):
            assert replace is False and size == 128
            self.samples.append(population)
            return np.arange(128)
    # No actual random draw: the mock retains the declared SeedSequence address.
    monkeypatch.setattr(r.np.random, "PCG64", lambda sequence: sequence.entropy)
    monkeypatch.setattr(r.np.random, "Generator", Random)
    reading = r.TrainingRead(2, {"initial": 0, "target": 0})
    assert [stream.address for stream in streams] == [[109259999, 10, 2], [109259999, 11, 2]]
    arrays = {name: np.zeros(shape, dtype=dtype) for name, (shape, dtype) in r.MISSION_SHAPES.items()}
    arrays["reports"]["complete"] = 1
    arrays["nn_complete"][:] = True
    arrays["exploration_draw"][:] = .5
    arrays["exploratory_action"][:] = -1
    arrays["update_samples"][:] = -1
    reading.decisions(arrays)
    for episode in range(4):
        reading.transitions_from(episode, arrays)
    assert reading.transitions == 240 and reading.updates == 0
    arrays["update_number"][16:] = np.arange(1, 45)
    arrays["update_samples"][16:] = np.arange(128)
    arrays["update_values"][16:, 5] = 126  # terminal indices59/119 excluded from next networks.
    reading.transitions_from(4, arrays)
    assert reading.transitions == 300 and reading.updates == 44
    assert streams[0].samples == [] and streams[1].samples == list(range(257, 301))
    assert reading.nonterminal_batches == 44 and reading.nonterminal_rows == 44 * 126
    assert reading.curves[-1]["terminal_sample_rows"] == 88
    arrays["update_samples"][0] = np.arange(128)
    arrays["update_number"][0] = 45
    arrays["update_values"][0, 5] = 128
    with pytest.raises(AssertionError, match="terminal samples have no next"):
        reading.transitions_from(5, arrays)


def test_mock_full_entry_writes_all_checks_and_failure_is_not_retried(tmp_path, monkeypatch):
    records = [{"label": label, "world": world} for label, world in r.expected_roster()]
    meter = Meter()
    fits = [{"fit": fit, "acquisition_cost": {"cpu_seconds": 0.}} for fit in range(3)]
    endpoints = [{"name": f"train{fit}", "counts": {"frozen_nn_rows": 0}} for fit in range(3)]
    endpoints += [{"name": f"initial{fit}", "counts": {"offline_audit_rows": 240, "frozen_nn_rows": 0}}
                  for fit in range(3)]
    endpoints += [{"name": f"L{fit}", "counts": {"frozen_nn_rows": 7920}} for fit in range(3)]
    worker_root = tmp_path / "worker"
    worker_root.mkdir()
    worker_config = dict(mode="worker", seed=109259999, launch_sha="worker-source",
                         source_identity="mock-source", contract=r.c.frozen_contract())
    r.write_json(worker_root / "config.json", worker_config)
    manifest = dict(files={"config.json": {}}, records=records, fits=fits, endpoint_counts=endpoints)
    summary = dict(launch_sha="worker-source")
    context = dict(meter=meter, manifest=manifest, worker_root=worker_root,
                   worker_summary=summary, worker_config=worker_config, source_identity="mock-source")
    monkeypatch.setattr(r, "validate_manifest", lambda *_args: records)
    fake_state = {"counters": {}, "forward_counts": {}}
    monkeypatch.setattr(r, "FrozenModels", lambda *_args: SimpleNamespace(
        torch=SimpleNamespace(load=lambda *_a, **_k: copy.deepcopy(fake_state))))
    class FakeTraining:
        def __init__(self, fit, state):
            self.state, self.curves, self.fit = state, [], fit
        def finish(self, *_args):
            return {"fit": self.fit}
    monkeypatch.setattr(r, "TrainingRead", FakeTraining)
    calls = []
    def mocked_mission(record, worker_root, manifest, audit, models, training):
        calls.append(record)
        kind, _ = r.policy_kind(record["label"])
        audit.add("native_physical_states", 1201)
        audit.add("native_motion_steps", 1200)
        audit.add("missions")
        audit.add("training_missions" if kind == "train" else "frozen_missions")
        if kind in ("L", "initial"):
            audit.add("neural_rows", 240)
            audit.add("neural_initial_rows" if kind == "initial" else "neural_final_rows", 240)
        return {**record, "policy_cache_missingness":
                [{"neural_cache_missing": kind == "L"}] if kind in ("G", "L") else [],
                "rollout_checks": [{"mock": True}] * (60 if kind == "R" else 0)}
    monkeypatch.setattr(r, "read_mission", mocked_mission)
    monkeypatch.setattr(r, "compare_panel", lambda *_args: {"pure_mock": True})
    out = tmp_path / "read"
    r.run(tmp_path, out, SimpleNamespace(launch_sha="reader-source"), context)
    result = json.loads((out / "reading.json").read_text())
    assert result["status"] == "COMPLETE" and result["counts"]["missions"] == 1708
    assert len(list((out / "checks").rglob("*.json"))) == 1708
    assert result["counts"]["neural_rows"] == 24480  # mocked counters,zero real neural rows.
    assert result["missing_policy_cache_decisions"] == 134
    assert result["missing_neural_cache_decisions"] == 99  # excludes35 ordinary G misses.
    assert len(calls) == 1708
    calls.clear()
    def fail_once(*_args):
        calls.append(1)
        raise RuntimeError("mock trace defect")
    monkeypatch.setattr(r, "read_mission", fail_once)
    with pytest.raises(RuntimeError, match="trace defect"):
        r.run(tmp_path, tmp_path / "failed-read", SimpleNamespace(launch_sha="reader-source"), context)
    assert calls == [1]
    assert json.loads((tmp_path / "failed-read" / "reading.json").read_text())["status"] == "FAILED"
