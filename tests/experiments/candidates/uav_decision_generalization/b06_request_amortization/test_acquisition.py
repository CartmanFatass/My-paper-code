"""Fabricated data and fake numerical backends only; zero scientific calls."""
import ast
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_decision_generalization.b06_request_amortization import acquisition as a


class Meter:
    def __init__(self):
        self.counts, self.events, self.refuse = {}, [], None
    def check(self):
        self.events.append(("check",))
    def add(self, name, amount=1):
        self.counts[name] = self.counts.get(name, 0) + amount
        self.events.append(("complete", name, amount))
    def reserve(self, name, amount=1):
        self.events.append(("reserve", name, amount))
        if self.refuse == name:
            raise RuntimeError("mock budget stop")
        self.counts[name] = self.counts.get(name, 0) + amount


@pytest.fixture(autouse=True)
def forbid_scientific_defaults(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("actual scorer/optimizer or coefficient solve is outside mocked checks")
    monkeypatch.setattr(a, "TorchBackend", forbidden)
    monkeypatch.setattr(a.np.linalg, "solve", forbidden)


def bank():
    raw = np.tile(np.asarray([0., 3., 2., 1.]), (2100, 1))
    teacher = raw + np.asarray([0., -1., 1., 2.])
    return a.Bank(np.zeros((2100, 4, 303), dtype=np.float32), raw, teacher,
                  tuple((world, decision) for world in a.WORLDS for decision in range(60)), {"fabricated": True})


class FakeBackend:
    """Toy arrays and counters; no real neural/optimizer implementation."""
    def __init__(self, *, fail=None):
        self.weights, self.steps, self.calls, self.fail = np.zeros(4, dtype=np.float32), 0, [], fail
        self.saved = {}
    def parameters(self):
        return {"fabricated_head": self.weights.copy()}
    def optimizer_state(self):
        return {"fabricated_step": self.steps}
    def zero_head(self):
        return bool(not self.weights.any())
    def forward(self, rows, *, training):
        self.calls.append((len(rows), training))
        if self.fail == "forward":
            raise RuntimeError("mock forward failure")
        return np.tile(self.weights, (len(rows) // 4, 1))
    def loss(self, raw, teacher, residual):
        return float(np.mean(a.relative_errors(a.compose_q(raw, residual), raw, teacher) ** 2))
    def zero_grad(self):
        pass
    def backward(self, loss):
        if self.fail == "backward":
            raise RuntimeError("mock backward failure")
    def clip(self):
        return 2., 2.
    def step(self):
        if self.fail == "optimizer":
            raise RuntimeError("mock optimizer failure")
        self.steps += 1
        self.weights[0] += np.float32(.00001)
    def validate_optimizer_steps(self, expected):
        assert self.steps == expected
    def save(self, path, payload):
        self.saved[str(path)] = copy.deepcopy(payload)
        Path(path).write_text(a.digest(payload))
    def load(self, payload):
        self.weights[:] = payload["parameters"]["fabricated_head"]


def test_import_is_lazy_and_fixed_source_loss_and_adam_contract():
    module = ast.parse(Path(a.__file__).read_text())
    eager = [node for node in module.body if isinstance(node, (ast.Import, ast.ImportFrom)) and
             (getattr(node, "module", "") == "torch" or
              any(alias.name == "torch" for alias in getattr(node, "names", [])))]
    assert eager == []
    loss = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "anchored_loss")
    assert not any(isinstance(node, ast.Attribute) and node.attr == "detach" for node in ast.walk(loss))
    backend = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "TorchBackend")
    adam = next(node for node in ast.walk(backend) if isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and node.func.attr == "Adam")
    values = {kw.arg: ast.literal_eval(kw.value) for kw in adam.keywords}
    assert values == dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                         amsgrad=False, foreach=False, fused=False, maximize=False)
    clip = next(node for node in ast.walk(backend) if isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and node.func.attr == "clip_grad_norm_")
    assert ast.literal_eval(clip.args[1]) == 10.


def test_fixed_shuffle_all_contexts_last52_separate_seed_with_fake_rng():
    class Random:
        def __init__(self):
            self.calls = 0
        def permutation(self, size):
            assert size == 2100
            self.calls += 1
            return np.roll(np.arange(size), self.calls)
    rng = Random()
    batches = list(a.shuffle_batches(2, rng=rng))
    assert len(batches) == 2112 and rng.calls == 64
    for epoch in range(64):
        rows = batches[epoch * 33:(epoch + 1) * 33]
        assert [len(indices) for _, _, indices in rows] == [64] * 32 + [52]
        np.testing.assert_array_equal(np.sort(np.concatenate([indices for _, _, indices in rows])), np.arange(2100))
    with pytest.raises(ValueError, match="fit index"):
        list(a.shuffle_batches(True, rng=rng))


def test_float64_composition_anchor_in_loss_and_exact_tie_rule():
    raw = np.asarray([[0., 8., 7., 1.]])
    residual = np.asarray([[1., .5, .5, 2.]], dtype=np.float32)
    q = a.compose_q(raw, residual)
    np.testing.assert_array_equal(q, raw / 1200. + residual.astype(np.float64))
    assert int(a.greedy(np.asarray([[1 + 1e-10, 1., 1., 2.]]), raw)[0]) == 2
    errors = a.relative_errors(q, raw, raw)
    assert errors[0, 0] == 0. and np.mean(errors ** 2) == np.sum(errors ** 2) / 4.

    class Tensor:
        def __init__(self, value): self.value = np.asarray(value)
        def __truediv__(self, value): return Tensor(self.value / value)
        def __add__(self, other): return Tensor(self.value + other.value)
        def __sub__(self, other): return Tensor(self.value - other.value)
        def to(self, _dtype): return Tensor(self.value.astype(np.float64))
        def __getitem__(self, key): return Tensor(self.value[key])
        def gather(self, dimension, indices): return Tensor(np.take_along_axis(self.value, indices.value, dimension))
        def square(self): return Tensor(self.value ** 2)
        def mean(self): return float(self.value.mean())
    fake_torch = SimpleNamespace(float64=np.float64, int64=np.int64,
                                 as_tensor=lambda value, dtype, device: Tensor(np.asarray(value, dtype=dtype)))
    actual = a.anchored_loss(raw, raw, Tensor(residual), fake_torch)
    assert actual == np.mean(errors ** 2)


def trace_fixture():
    from experiments.candidates.uav_decision_generalization.b05_request_schedule.storage import R_SHAPES
    names = ("cohort_complete", "cohort_reuse", "cohort_costs", "cohort_branches", "cohort_input_sha256",
             "cohort_ready_ns", "tape_complete", "tape_lengths", "tape_times", "tapes", "branch_complete",
             "branch_action", "branch_tape", "branch_cost", "stats")
    trace = {name: np.zeros(R_SHAPES[name][0], dtype=R_SHAPES[name][1]) for name in names}
    trace["cohort_complete"][:] = trace["tape_complete"][:] = 1
    trace["cohort_reuse"][:] = [-1, 0, 0, 0]
    trace["cohort_costs"][:] = [1., 3., 4., 2.]
    trace["cohort_branches"][:] = np.arange(4)
    trace["branch_complete"][:4] = 1
    trace["branch_action"][:4] = np.arange(4)
    trace["branch_cost"][:4] = [1., 3., 4., 2.]
    selected = [{"tape": index, "costs": [1., 3., 4., 2.], "branches": [0, 1, 2, 3],
                 "input_sha256": "00" * 32, "times": [], "bits": [],
                 "reused_cohort": None if index == 0 else 0} for index in range(4)]
    return trace, selected


def test_label_reconstruction_preserves_four_aliases_and_rejects_corruption():
    trace, selected = trace_fixture()
    np.testing.assert_array_equal(a.cohort_mean(trace, selected), [1., 3., 4., 2.])
    trace["cohort_reuse"][3] = 1
    with pytest.raises(ValueError, match="reuse alias"):
        a.cohort_mean(trace, selected)
    trace["cohort_reuse"][3] = 0
    trace["branch_action"][2] = 1
    with pytest.raises(ValueError, match="action/score"):
        a.cohort_mean(trace, selected)


def test_constant_ordered_bordered_system_with_fake_solver():
    data, meter, seen = bank(), Meter(), []
    def solver(H, rhs):
        seen.append((H.copy(), rhs.copy()))
        # The fixture correction has sum0 after removing its common offset.
        return np.asarray([-.5, -1.5, .5, 1.5, 0.])
    result = a.solve_constant(data, meter=meter, solver=solver)
    expected_H = 2100 * np.asarray([[3., -1., -1., -1.], [-1., 1., 0., 0.],
                                    [-1., 0., 1., 0.], [-1., 0., 0., 1.]])
    np.testing.assert_array_equal(result["H"], expected_H)
    np.testing.assert_array_equal(result["z"], [-4200., -2100., 2100., 4200.])
    np.testing.assert_array_equal(result["normal_residual"], np.zeros(4))
    assert result["constraint_residual"] == 0 and len(seen) == 1
    np.testing.assert_array_equal(seen[0][0][:4, 4], np.ones(4))
    np.testing.assert_array_equal(seen[0][0][4, :4], np.ones(4))
    meter.refuse = "b06_constant_verification_solve_attempts"
    with pytest.raises(RuntimeError, match="budget stop"):
        a.solve_constant(data, meter=meter, solver=solver, phase="constant_verification")
    assert len(seen) == 1


def test_endpoint_only_exact33_batches_and_failed_attempt_counts():
    data, backend, meter = bank(), FakeBackend(), Meter()
    result = a.evaluate_endpoint(data, backend, phase="reader_initial_bank", meter=meter)
    assert backend.calls == [(256, False)] * 32 + [(208, False)]
    assert result["counts"] == dict(forward_attempts=33, forward_attempted_rows=8400, forward_calls=33, forward_rows=8400)
    np.testing.assert_array_equal(result["residual"], np.zeros((2100, 4), dtype=np.float32))
    failed = FakeBackend(fail="forward")
    with pytest.raises(RuntimeError) as caught:
        a.evaluate_endpoint(data, failed, phase="reader_final_bank", meter=meter)
    assert caught.value.b06_partial_counts["reader_final_bank"] == dict(forward_attempts=1, forward_attempted_rows=256)
    assert failed.calls == [(256, False)]


def test_callback_quarantine_no_recursive_notification():
    calls = []
    def sink(event, counts):
        calls.append((event, counts))
        raise RuntimeError("mock sink failure")
    counts = a.Counts("fake", Meter(), sink)
    with pytest.raises(RuntimeError, match="sink failure"):
        counts.event("forward.attempt", "forward_attempts", attempt=True)
    counts.event("failure", "failures")
    assert len(calls) == 1 and counts.counts == dict(forward_attempts=1, failures=1)


def test_fixed_full_fit_fake_evidence_and_failure_prefix(tmp_path):
    data, backend, meter = bank(), FakeBackend(), Meter()
    result = a.fit_endpoint(data, 1, tmp_path / "complete", source_identity="fabricated-source",
                            launch_sha="fabricated-launch", meter=meter, backend=backend)
    assert result["status"] == "COMPLETE" and backend.steps == 2112
    assert result["counts"]["forward_rows"] == 537600
    assert backend.calls[:33] == backend.calls[-33:] == [(256, False)] * 32 + [(208, False)]
    training = [rows for rows, flag in backend.calls if flag]
    assert training == ([256] * 32 + [208]) * 64
    journal = [json.loads(line) for line in (tmp_path / "complete/updates.jsonl").read_text().splitlines()]
    assert len(journal) == 4224 and sum(row["completed"] for row in journal) == 2112
    assert journal[-1]["counts"]["updates"] == 2112
    epochs = json.loads((tmp_path / "complete/epochs.json").read_text())
    assert len(epochs) == 64 and all(not row["fixed_endpoint_evaluation"] for row in epochs)
    assert a.file_identity(result["final"]["path"])["sha256"] == result["final"]["sha256"]
    failed = FakeBackend(fail="backward")
    with pytest.raises(RuntimeError, match="backward failure"):
        a.fit_endpoint(data, 0, tmp_path / "failed", source_identity="fabricated-source",
                       launch_sha="fabricated-launch", meter=Meter(), backend=failed)
    partial = json.loads((tmp_path / "failed/fit.json").read_text())
    assert partial["status"] == "FAILED" and partial["counts"]["backward_attempts"] == 1
    assert partial["counts"].get("optimizer_steps", 0) == 0 and partial["partial"]["bytes"] > 0
    assert len(failed.calls) == 34 and failed.steps == 0
    with pytest.raises(ValueError, match="replay"):
        a.fit_endpoint(data, 0, tmp_path / "failed", source_identity="fabricated-source",
                       launch_sha="fabricated-launch", backend=FakeBackend())


def test_checkpoint_binding_stage_source_and_no_forward(tmp_path, monkeypatch):
    backend, seed = FakeBackend(), a.SEEDS[2]
    payload = a.checkpoint_payload(backend, 2, "initial", "source", "launch", "bank", a.digest(backend.parameters()))
    path = tmp_path / "checkpoint.pt"
    backend.save(path, payload)
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(load=lambda *_args, **_kwargs: copy.deepcopy(payload)))
    monkeypatch.setattr(a, "TorchBackend", lambda constructor_seed, training: FakeBackend())
    loaded = a.load_scorer(path, a.file_identity(path), fit_index=2, stage="initial",
                           source_identity="source", bank_identity="bank", meter=Meter())
    assert loaded.calls == [] and loaded.zero_head() and loaded.payload["init_seed"] == seed
    with pytest.raises(ValueError, match="lineage"):
        a.load_scorer(path, a.file_identity(path), fit_index=2, stage="final", source_identity="source", bank_identity="bank")
    path.write_text("corruption")
    with pytest.raises(ValueError, match="byte identity"):
        a.load_scorer(path, {"sha256": "bad", "bytes": 10}, fit_index=2, stage="initial", source_identity="source", bank_identity="bank")


def test_full_fabricated_bank_binding_hashes2170_files_without_reading_outcomes(tmp_path, monkeypatch):
    from experiments.candidates.uav_decision_generalization.b05_request_schedule.storage import G_DTYPE, R_STATS
    trace, selected = trace_fixture()
    trace["stats"][R_STATS.index("cohorts_complete")] = 4
    statistics = {name: int(trace["stats"][index]) for index, name in enumerate(R_STATS)}
    reports = np.zeros(60, dtype=G_DTYPE)
    reports["tick"] = np.arange(60) * 20
    reports["complete"][:] = 1
    reports["costs"][:] = [5., 4., 3., 2.]
    features = np.zeros((60, 4, 303), dtype=np.float32)
    accessed = []
    class Archive:
        def __init__(self, path): self.path = Path(path)
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def __getitem__(self, key):
            accessed.append(key)
            if self.path.name.startswith("mission"):
                return {"features": features, "reports": reports}[key].copy()
            return trace[key].copy()
    monkeypatch.setattr(a.np, "load", lambda path, allow_pickle: Archive(path))
    files, records = {}, []
    def save(relative, value):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, dict):
            a.write_json(path, value)
        else:
            path.write_bytes(value)
        files[relative] = a.file_identity(path)
    for world in a.WORLDS:
        label = "main/R" if world < 109253900 else f"audit{world - 109253900}/R"
        rollout_traces = []
        for decision in range(60):
            relative = f"rollout/{world}_{decision}.npz"
            save(relative, b"fabricated-archive")
            rollout_traces.append(dict(decision=decision, path=relative, stats=statistics))
        metadata_name, npz_name = f"mission{world}.json", f"mission{world}.npz"
        messages = [dict(type="cohort", eligible=True, ready_ns=1, received_ns=2) for _ in range(4)]
        metadata = dict(status="COMPLETE", label=label, world=world, completed_decisions=60,
                        completed_native_steps=1200, rollout_traces=rollout_traces,
                        decisions=[dict(cohorts=selected, timing=dict(messages=messages, deadline_ns=3)) for _ in range(60)])
        save(metadata_name, metadata)
        save(npz_name, b"fabricated-mission-archive")
        records.append(dict(status="COMPLETE", label=label, world=world, completed_native_steps=1200,
                            metadata=metadata_name, npz=npz_name))
    originals = dict(config={"source_identity": "fabricated-old"},
                     summary={"source_identity": "fabricated-old", "status": "COMPLETE", "missions": 1708},
                     manifest={"schema": 1, "records": list(reversed(records)), "files": files})
    for name, value in originals.items():
        a.write_json(tmp_path / (name + ".json"), value)
    reader = dict(source_identity="fabricated-old", status="COMPLETE", missions=1708,
                  input_identities={name + "_identity": a.file_identity(tmp_path / (name + ".json"))
                                    for name in originals})
    a.write_json(tmp_path / "reader.json", reader)
    hashes = {name + ".json": a.file_identity(tmp_path / (name + ".json"))["sha256"] for name in originals}
    hashes["reader_summary"] = a.file_identity(tmp_path / "reader.json")["sha256"]
    monkeypatch.setattr(a, "OLD_HASHES", hashes)
    meter = Meter()
    result = a.binding_bank(tmp_path, tmp_path / "reader.json", meter=meter)
    assert result.keys == tuple((world, decision) for world in a.WORLDS for decision in range(60))
    assert len(result.provenance["files"]) == 2170
    assert meter.counts["b06_bank_worker_file_hashes"] == 2174
    assert meter.counts["b06_bank_worker_label_contexts"] == 2100
    np.testing.assert_array_equal(result.teacher, np.tile([1., 3., 4., 2.], (2100, 1)))
    assert not result.features.flags.writeable
    assert not {"total_q", "arrival_tape", "macro_cost", "residual", "requests", "completions"}.intersection(accessed)
    (tmp_path / records[0]["npz"]).write_bytes(b"corruption")
    with pytest.raises(ValueError, match="manifested teacher file identity"):
        a.binding_bank(tmp_path, tmp_path / "reader.json", meter=Meter(), phase="bank_reader")
