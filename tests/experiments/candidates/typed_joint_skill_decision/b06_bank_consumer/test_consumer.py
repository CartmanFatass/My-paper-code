"""Pure control-plane checks only. No numerical/scientific imports or process execution."""
from __future__ import annotations
import ast
import copy
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import pytest
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import contract as c
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import billing, commitment, evidence, run, worker

ROOT = Path(__file__).resolve().parents[5]
LEDGER = {"scientific_calls": 0, "process_execs": 0, "opaque_callbacks": 0, "mock_failures": 0}


@pytest.fixture(scope="module", autouse=True)
def price(record_testsuite_property):
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    yield
    end = resource.getrusage(resource.RUSAGE_SELF)
    reaped = resource.getrusage(resource.RUSAGE_CHILDREN)
    value = {**LEDGER, "cpu_seconds": (end.ru_utime + end.ru_stime - own.ru_utime - own.ru_stime
             + reaped.ru_utime + reaped.ru_stime - children.ru_utime - children.ru_stime),
             "wall_seconds": time.monotonic() - started,
             "scratch_scope": "pytest tmp_path only; no real bank/model/native assets",
             "external_support_cpu": "unknown, not zero"}
    record_testsuite_property("b06_pure_mock_counts", json.dumps(value, sort_keys=True))
    assert value["scientific_calls"] == value["process_execs"] == 0


def test_fixed_order_and_source_identity():
    jobs = list(c.jobs())
    assert len(jobs) == 1160
    assert [job["fit"] for job in jobs[:6]] == list(c.FITS)
    assert jobs[6]["stage"] == "endpoint" and jobs[-1]["stage"] == "reader"
    assert sum(job["gpu"] for job in jobs) == 775
    for offset in range(128):
        local = jobs[7 + 9 * offset:7 + 9 * (offset + 1)]
        assert [job["world"] for job in local] == [109420000 + offset] * 9
        assert [job["arm"] for job in local] == list(c.ARMS)[offset % 9:] + list(c.ARMS)[:offset % 9]
    for name, expected in c.FROZEN_DIGESTS.items():
        assert c.sha(ROOT / name) == expected
    assert c.sha(ROOT / "docs/research/candidates/typed_joint_skill_decision/B04_INPUT.json") == c.SCIENCE_INPUT


@pytest.mark.parametrize("binding", [None, {}, {"status": "pending"}, {"status": "partial"},
    {"status": "unknown"}, {"status": "complete_compatible_bank", "mock_pass": True}])
def test_pending_interface_never_certifies(binding):
    with pytest.raises(c.PendingCertification):
        c.certify_bank(binding)


@pytest.mark.parametrize("value", [None, {}, {"selected": False}, {"selected": True},
    {"selected": True, "limits": {"cpu_seconds": 28800}}])
def test_no_forecast_budget_defaults(value):
    with pytest.raises(c.PendingCertification):
        c.investment(value)


def test_explicit_investment_and_hash_refusal(tmp_path):
    limits = {"cpu_seconds": 7, "gpu_child_seconds": 9, "wall_seconds": 11, "disk_bytes": 12345}
    assert c.investment({"selected": True, "limits": limits}) == limits
    with pytest.raises(ValueError):
        c.investment({"selected": True, "limits": {**limits, "cpu_seconds": float("nan")}})
    path = tmp_path / "small.json"
    path.write_bytes(c.encoded({"source": "producer", "input": "producer-input"}))
    digest = c.sha(path)
    assert c.bound_json(path, digest)["source"] == "producer"
    path.write_bytes(b"changed")
    with pytest.raises(ValueError):
        c.bound_json(path, digest)
    with pytest.raises(ValueError):
        c.scientific_binding({"scientific_source_sha": c.SCIENCE_SHA,
                              "scientific_input_sha256": c.SCIENCE_INPUT,
                              "frozen_sources": {name: "0" * 64 for name in c.SCIENCE_FILES}}, ROOT)


class NoScienceBill:
    def check(self, **kwargs):
        pass
    def snapshot(self):
        return {"scientific_calls": 0}


def test_exclusive_store_and_merge(tmp_path):
    parent = evidence.ParentStore(tmp_path)
    job = next(c.jobs())
    job["new_stream"] = True
    child = evidence.ChildStore(tmp_path, NoScienceBill(), job)
    name = "raw/fit/" + job["fit"]["id"] + "/tiny.json"
    child.write(name, {"opaque": "not weights"})
    manifest_name = child.finish()
    manifest = json.loads((tmp_path / manifest_name).read_bytes())
    parent.merge(job, manifest)
    assert parent.load(name)["opaque"] == "not weights"
    with pytest.raises(ValueError):
        parent.merge(job, manifest)
    with pytest.raises((ValueError, FileExistsError)):
        child.write(name, {})
    with pytest.raises(ValueError):
        child.write("raw/main/1/P/stolen.json", {})
    assert not (tmp_path / "raw/main").exists()
    (tmp_path / name).write_bytes(b"mutated")
    with pytest.raises(ValueError):
        parent.seal()


@pytest.mark.parametrize("name", ["../escape", "/absolute", "./ambiguous", "a/../b"])
def test_path_refusal(tmp_path, name):
    with pytest.raises(ValueError):
        c.relative(tmp_path, name)


def test_symlink_alias_refusal(tmp_path):
    (tmp_path / "first").mkdir()
    (tmp_path / "second").symlink_to(tmp_path / "first", target_is_directory=True)
    with pytest.raises(ValueError):
        c.relative(tmp_path, "second/alias")


def test_reader_ownership_and_partial_prefix(tmp_path):
    parent = evidence.ParentStore(tmp_path)
    reader_job = list(c.jobs())[-1]
    child = evidence.ChildStore(tmp_path, NoScienceBill(), reader_job)
    child.write("raw/functional/x.json", {"synthetic": True})
    parent.merge(reader_job, {"schema": 1, "job": reader_job, "files": child.local})
    cold = list(c.jobs())[7]
    name = "raw/main/" + str(cold["world"]) + "/" + cold["arm"] + "/queries.jsonl.gz"
    raw = evidence.c.relative(tmp_path, name)
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"unparseable partial gzip preserved")
    parent.failure_prefix(cold)
    assert parent.files[name]["failed_prefix"]
    assert raw.read_bytes() == b"unparseable partial gzip preserved"
    assert not evidence.allowed(cold, name.replace("queries.jsonl.gz", "decision.json"))


def synthetic_reference(world=109420000):
    identity = {"world": world, "initial_positions_xyz": [[1., 2., 3.]], "user_positions_xy": [[4., 5.]],
                "bs_xyz": [6., 7., 8.], "native_rng_sha256": "opaque-rng", "agents": ["opaque-agent"],
                "transmitter_mask": [True], "current_step": 0}
    layout = [[9., 10., 11.]]
    record = {"identity": identity, "layouts_xyz": [layout], "construction": {"opaque": True}}
    reference = commitment.make(record, {"opaque_features": True}, {fit["id"]: 0 for fit in c.FITS})
    assert not any(key in reference for key in ("J", "infos", "best", "labels", "layouts_xyz"))
    return reference, layout


def synthetic_decision(world, arm):
    reference, layout = synthetic_reference(world)
    identity = copy.deepcopy(reference["identity"])
    decision = {"world": world, "arm": arm, "initial_positions_xyz": identity["initial_positions_xyz"],
        "user_positions_xy": identity["user_positions_xy"], "bs_xyz": identity["bs_xyz"],
        "construction_identity": identity, "positions_xyz": layout, "chosen_raw_index": 0,
        "feature_sha256": reference["feature_sha256"], "construction_sha256": reference["construction_sha256"],
        "source_sha": "consumer-source", "input_sha256": c.SCIENCE_INPUT,
        "reset_identity": {key: identity[key] for key in ("native_rng_sha256", "agents", "transmitter_mask")},
        "timing": {}, "selection_counts": {"static_calls": 0}}
    decision["reset_identity"]["state"] = {"current_step": 0, "positions_xyz": identity["initial_positions_xyz"]}
    return decision


@pytest.mark.parametrize("corruption", ["pose", "mask", "step", "layout", "GPU", "source", "feature"])
def test_cold_commitment_exact_rejection(corruption):
    world, arm = 109420000, c.FITS[0]["id"]
    reference, _ = synthetic_reference(world)
    decision = synthetic_decision(world, arm)
    if corruption == "pose":
        decision["initial_positions_xyz"] = [[1., 2., 3.00000000000001]]
    elif corruption == "mask":
        decision["reset_identity"]["transmitter_mask"] = [False]
    elif corruption == "step":
        decision["reset_identity"]["state"]["current_step"] = 1
    elif corruption == "layout":
        decision["positions_xyz"] = [[9., 10., 11.00000000000001]]
    elif corruption == "GPU":
        reference["gpu_choices"][arm] = 1
    elif corruption == "source":
        decision["source_sha"] = "producer-not-consumer"
    elif corruption == "feature":
        decision["feature_sha256"] = "changed"
    with pytest.raises(AssertionError):
        commitment.verify(decision, reference, world=world, arm=arm,
                          launch_sha="consumer-source", input_sha256=c.SCIENCE_INPUT)


class MemoryStore:
    """Opaque callback test storage: no real worlds/labels/weights or 16k bank allocation."""
    def __init__(self):
        self.root = Path("/opaque-output")
        self.values, self.files, self.events = {}, {}, []
    def write(self, name, value):
        assert name not in self.files
        self.values[name] = copy.deepcopy(value)
        self.files[name] = {"sha256": commitment.digest(value), "bytes": len(c.encoded(value))}
        self.events.append(("write", name))
    def check(self, name, digest=None):
        assert name in self.files and (digest is None or self.files[name]["sha256"] == digest)
    def load(self, name):
        self.check(name)
        self.events.append(("read", name))
        return copy.deepcopy(self.values[name])
    def selection(self, name, digest):
        self.check(name, digest)
        self.events.append(("selection", name))
        return copy.deepcopy(self.values[name])
    def seal(self, name="artifact-manifest.json"):
        self.write(name, {"files": dict(self.files)})
        return self.files[name]["sha256"]
    def failure_prefix(self, job):
        self.events.append(("partial", job["id"]))


class MockBill(NoScienceBill):
    def __init__(self):
        self.counts = {"spawn_attempts": 0, "spawn_completed": 0}
    def charge(self, key, n=1):
        self.counts[key] = self.counts.get(key, 0) + n
    def counter_snapshot(self):
        return dict(self.counts)
    def snapshot(self):
        return {"counters": dict(self.counts), "scientific_calls": 0}
    def seal_counts(self, store):
        if "shared-counters.bin" not in store.files:
            store.write("shared-counters.bin", {"opaque": "mock counters"})


def mock_pipeline(monkeypatch, *, fail=None):
    store, bill, called = MemoryStore(), MockBill(), []
    parent = {"launch_sha": "consumer-source", "consumer_input_sha256": "consumer-input"}
    bank = {"root": "/opaque-bank", "files": {"raw/bank/train/0000.npz": {}, "raw/bank/fresh/0000.npz": {}},
            "producer_source_sha": "actual-producer", "producer_input_sha256": "actual-producer-input",
            "manifest_sha256": "actual-bank-manifest", "prior_cost": {"prior": True}}
    completed_checks = []
    monkeypatch.setattr(billing, "count_complete", lambda counts, cases: completed_checks.append((counts, len(cases))))
    def opaque(job, request, on_ready):
        LEDGER["opaque_callbacks"] += 1
        called.append(job["id"])
        if fail == job["id"]:
            LEDGER["mock_failures"] += 1
            raise RuntimeError("opaque first technical failure")
        if job["stage"] == "fit":
            assert all(name.startswith("raw/bank/train/") for name in request["bank"]["files"])
            assert request["bank"]["producer_source_sha"] == "actual-producer"
            stream = job["fit"]["stream"]
            initials = dict(request["initial_hashes"])
            initials[stream] = "actual-initial-" + str(stream)
            if job["new_stream"]:
                store.write("raw/initial/stream" + str(stream) + ".pt", {"opaque_initial": stream})
            path = "raw/fit/" + job["fit"]["id"] + "/final.pt"
            store.write(path, {"opaque_final": True, "optimizer": "retained opaque"})
            return {"asset": {"fit": job["fit"], "path": path, "sha256": store.files[path]["sha256"],
                              "initial_sha256": initials[stream], "final_sha256": "opaque"}, "initial_hashes": initials}
        if job["stage"] == "endpoint":
            assert len(request["assets"]) == 6
            store.check(request["final_seal"]["path"], request["final_seal"]["sha256"])
            assert not any(event[0] == "read" for event in store.events)
            for world in range(109420000, 109420128):
                reference, _ = synthetic_reference(world)
                store.write("commitments/" + str(world) + ".json", reference)
            return {"opaque_endpoint": True}
        if job["stage"] == "cold":
            assert not any(key in request for key in ("bank", "fresh", "endpoints", "commitments", "inherited_files"))
            name = "raw/main/" + str(job["world"]) + "/" + job["arm"] + "/selection.json"
            decision = synthetic_decision(job["world"], job["arm"])
            store.write(name, decision)
            message = {"selection": name, "sha256": store.files[name]["sha256"], "cpu": {"total_seconds": 0}}
            permission = on_ready(message)
            assert permission == {"kind": "verified", "sha256": message["sha256"]}
            assert store.events[-2:] == [("selection", name), ("read", "commitments/" + str(job["world"]) + ".json")]
            return {"kind": "complete", "case_counts": {}, "cpu": {"total_seconds": 0}, "matched_endpoint": {"opaque": True}}
        assert len(request["cases"]) == 1152
        return {"summary": {"status": "complete"}, "diagnostics": {"opaque": True}}
    return store, bill, called, bank, parent, opaque, completed_checks


def test_entire_stage_handshake_with_opaque_callbacks(monkeypatch):
    store, bill, called, bank, parent, opaque, checked = mock_pipeline(monkeypatch)
    summary = run.run_pipeline(store, bill, opaque, parent, bank, {"opaque_original_input": True})
    assert len(called) == 1160 and bill.counts == {"spawn_attempts": 1160, "spawn_completed": 1160}
    assert checked == [(bill.counts, 1152)]
    assert summary["bank_producer_source_sha"] == "actual-producer"
    assert summary["checkpoint_input_sha256"] == c.SCIENCE_INPUT
    assert "artifact-manifest.json" in store.files


@pytest.mark.parametrize("failure_index", [0, 6, 7, 1159])
def test_first_failure_never_retries_or_continues(monkeypatch, failure_index):
    job = list(c.jobs())[failure_index]
    store, bill, called, bank, parent, opaque, _ = mock_pipeline(monkeypatch, fail=job["id"])
    with pytest.raises(RuntimeError, match="first technical failure"):
        run.run_pipeline(store, bill, opaque, parent, bank, {})
    assert len(called) == failure_index + 1
    assert bill.counts == {"spawn_attempts": failure_index + 1, "spawn_completed": failure_index}
    assert store.values["failure.json"]["retry"] is False
    assert "summary.json" not in store.files
    assert "shared-counters.bin" in store.values["artifact-manifest.json"]["files"]


def test_initializer_hashes_survive_process_boundaries(monkeypatch):
    store, bill, called, bank, parent, opaque, _ = mock_pipeline(monkeypatch)
    def wrong(job, request, on_ready):
        result = opaque(job, request, on_ready)
        if job["id"] == "fit-R16000s0":
            result["initial_hashes"][0] = "changed-in-another-process"
            result["asset"]["initial_sha256"] = "changed-in-another-process"
        return result
    with pytest.raises(AssertionError, match="same-stream"):
        run.run_pipeline(store, bill, wrong, parent, bank, {})
    assert called == [job["id"] for job in list(c.jobs())[:3]]


def test_shared_counters_caps_and_failure_prefix(tmp_path):
    path = tmp_path / "counts.bin"
    shared = billing.Shared(path, create=True)
    try:
        shared.charge("fits")
        shared.charge("static_calls", 2)
        shared.charge("static_completed")
        with pytest.raises(RuntimeError):
            shared.charge("bank_worlds")
    finally:
        shared.close()
    reopened = billing.Shared(path)
    try:
        assert reopened.get("fits") == 1 and reopened.get("static_calls") == 2
        assert reopened.get("static_completed") == 1 and reopened.get("refused_effects") == 1
    finally:
        reopened.close()
    assert billing.CAPS["static_calls"] == 1383760 and billing.CAPS["bank_worlds"] == 0


def test_source_admission_and_no_science_before_gates():
    tree = ast.parse((ROOT / "experiments/candidates/typed_joint_skill_decision/b06_bank_consumer/run.py").read_text())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    calls = sorted((node.lineno, ast.unparse(node.func)) for node in ast.walk(main) if isinstance(node, ast.Call))
    before = {name: min(line for line, actual in calls if actual == name)
              for name in ("require_admission", "c.investment", "c.certify_bank", "e.ParentStore", "run_pipeline")}
    assert before["require_admission"] < before["c.investment"] < before["c.certify_bank"] < before["e.ParentStore"] < before["run_pipeline"]
    source = (ROOT / "experiments/candidates/typed_joint_skill_decision/b06_bank_consumer/worker.py").read_text()
    worker = ast.parse(source)
    main = next(node for node in worker.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    calls = sorted((node.lineno, ast.unparse(node.func)) for node in ast.walk(main) if isinstance(node, ast.Call))
    assert next(line for line, name in calls if name == "checked_context") < min(line for line, name in calls if name in ("c.threads", "scientific_stage"))
    assert "training.fit_once" in source and "training.endpoint" in source and "reader.complete" in source and "case_main(wire" in source
    assert "build_bank(" not in source and "rebuild_bank(" not in source and "engineering_static(" not in source
    assert "optimizer" not in source  # Full checkpoints passed untouched; no crop/replay path.
    assert "torch" not in sys.modules


def test_complete_actual_candidates_may_be_below_maximum():
    # Artificial cost table, no callbacks/effects. Only training physical slots are fixed.
    counts = {key: 0 for key in billing.COUNTERS}
    counts.update(fits=6, fits_completed=6, updates=24576, updates_completed=24576,
        training_world_presentations=786432, training_candidate_presentations=12582912,
        training_completed_candidates=12582912, native_steps=584000, native_completed=584000,
        main_episodes=1152, audit_episodes=16, spawn_attempts=1160, spawn_completed=1160,
        reader_state_checks=585168, functional_contexts=6144, endpoint_contexts=6144,
        cold_contexts=768, engineering_contexts=16, hosts=2464, hosts_completed=2464,
        resets=4784, resets_completed=4784, raw_constructions=1536, raw_completed=1536,
        matching_calls=2464, matching_completed=2464, static_calls=586320, static_completed=586320)
    for phase in ("endpoint", "functional_reader", "cold", "engineering"):
        counts[phase + "_candidate_presentations"] = 10
        counts[phase + "_completed_candidates"] = 10
    counts["all_candidate_presentations"] = 12582952
    cases = [{"selection_counts": {"static_calls": 0}}] * 1152
    billing.count_complete(counts, cases)
    with pytest.raises(AssertionError, match="identity mismatch"):
        billing.count_complete({**counts, "all_candidate_presentations": 12582953}, cases)
    with pytest.raises(AssertionError, match="incomplete"):
        billing.count_complete({**counts, "cold_completed_candidates": 9}, cases)


def test_terminal_accounting_is_post_seal_and_nonrecursive(tmp_path):
    store = evidence.ParentStore(tmp_path)
    store.write("summary.json", {"status": "synthetic-only"})
    digest = store.seal()
    class TerminalBill(NoScienceBill):
        def snapshot(self):
            return {"synthetic_cpu": "actual timing measured by fixture"}
    run.terminal_resources(store, TerminalBill(), None)
    value = json.loads((tmp_path / "terminal-resource.json").read_bytes())
    assert value["manifest_sha256"] == digest
    assert "terminal-resource.json" not in store.files
    assert c.sha(tmp_path / "artifact-manifest.json") == digest
    assert "unmeasured" in value["final_record_write_and_counter_close_tail"]


@pytest.mark.parametrize("exit_code", [0, 7])
def test_exec_transport_cost_and_reap_with_mock_popen(tmp_path, monkeypatch, exit_code):
    # Real small files/pipes only; no child process is started, even a stdlib smoke child.
    store = evidence.ParentStore(tmp_path)
    shared = billing.Shared(tmp_path / "shared-counters.bin", create=True)
    bill = billing.Bill(shared, {"limits": {"cpu_seconds": 300, "gpu_child_seconds": 300,
        "wall_seconds": 300, "disk_bytes": 20 * 1024 ** 2}, "disk_roots": [str(tmp_path)],
        "started_monotonic": time.monotonic(), "prior_bank_cost": {"opaque": True},
        "prior_preparation_cost": synthetic_preparation()})
    job = next(c.jobs())
    job["new_stream"] = True
    class Process:
        pid = 123456789
        returncode = exit_code
        def poll(self):
            return exit_code
        def wait(self, **kwargs):
            return exit_code
        def terminate(self):
            raise AssertionError("mock child is already reaped")
    def opaque_popen(*args, **kwargs):
        LEDGER["opaque_callbacks"] += 1
        assert "--request-sha256" in args[0]
        if exit_code == 0:
            child = evidence.ChildStore(tmp_path, NoScienceBill(), job)
            child.write("children/" + job["id"] + "/outcome.json", {"opaque": True})
            child.finish()
        return Process()
    monkeypatch.setattr(run.subprocess, "Popen", opaque_popen)
    try:
        transport = run.ExecTransport(store, bill)
        if exit_code:
            LEDGER["mock_failures"] += 1
            with pytest.raises(RuntimeError, match="terminal failure"):
                transport(job, {"opaque_request": True}, lambda message: pytest.fail("unexpected handshake"))
        else:
            assert transport(job, {"opaque_request": True}, lambda message: pytest.fail("unexpected handshake")) == {"opaque": True}
        cost = store.load("children/" + job["id"] + "/stage-cost.json")
        assert cost["reaped_child_cpu_seconds"] == 0  # No real process under this opaque transport test.
        assert cost["parent_cpu_seconds"] >= 0 and cost["wall_seconds_including_parent_manifest_merge"] >= 0
        assert cost["gpu_child_seconds"] >= 0 and cost["gpu_phase_seconds"] == 0
        assert cost["exit_code"] == exit_code
        assert transport.active is None and cost["before_counters"]["fits"] == cost["after_counters"]["fits"] == 0
    finally:
        shared.close()


def test_cold_endpoint_stops_at_message_arrival(monkeypatch):
    # Opaque times isolate arrival from post-commit validation without real execution.
    store, bill, called, bank, parent, opaque, _ = mock_pipeline(monkeypatch)
    clock = {"wall": 0., "cpu": 0.}
    monkeypatch.setattr(run.time, "monotonic", lambda: clock["wall"])
    monkeypatch.setattr(run.time, "process_time", lambda: clock["cpu"])
    select, load = store.selection, store.load
    def delayed_selection(*args):
        clock["wall"] += 20.
        clock["cpu"] += 3.
        return select(*args)
    def delayed_reference(*args):
        clock["wall"] += 30.
        clock["cpu"] += 7.
        return load(*args)
    store.selection, store.load = delayed_selection, delayed_reference
    def delayed_message(job, request, on_ready):
        if job["stage"] == "cold":
            clock["wall"] += 1.
            clock["cpu"] += .25
        return opaque(job, request, on_ready)
    run.run_pipeline(store, bill, delayed_message, parent, bank, {})
    decisions = [value for name, value in store.values.items() if name.endswith("/decision.json")]
    assert len(decisions) == 1152
    for value in decisions:
        assert value["parent_cold_selection_seconds"] == 1.
        assert value["selection_parent_cpu_seconds"] == .25
        assert value["parent_case_wall_seconds"] == 51.


def synthetic_preparation(scope="separate_from_consumer_cpu_limit"):
    return {"known_cpu_seconds": 5., "cpu_limit_scope": scope,
            "evidence": [{"path": "opaque-preparation.json", "sha256": "0" * 64, "bytes": 0}],
            "unmetered_support": "unknown_not_zero"}


@pytest.mark.parametrize("fault", [None, "prctl", "ppid", "identity"])
def test_parent_death_binding_before_science(monkeypatch, fault):
    events = []
    class Libc:
        def prctl(self, *args):
            events.append(("prctl", args))
            return -1 if fault == "prctl" else 0
    monkeypatch.setattr(worker.ctypes, "CDLL", lambda *args, **kwargs: Libc())
    monkeypatch.setattr(worker.ctypes, "get_errno", lambda: 22)
    monkeypatch.setattr(worker.os, "getppid", lambda: 99 if fault == "ppid" else 42)
    monkeypatch.setattr(c, "process_identity", lambda pid: events.append(("identity", pid)) or
                        {"pid": pid, "start_ticks": 8 if fault == "identity" else 7})
    expected = {"pid": 42, "start_ticks": 7}
    if fault:
        with pytest.raises((OSError, RuntimeError)):
            worker.parent_death(expected)
    else:
        worker.parent_death(expected)
    assert events[0] == ("prctl", (1, worker.signal.SIGKILL, 0, 0, 0))
    source = (ROOT / "experiments/candidates/typed_joint_skill_decision/b06_bank_consumer/worker.py").read_text()
    tree = ast.parse(source)
    check = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "checked_context")
    calls = {ast.unparse(n.func): n.lineno for n in ast.walk(check) if isinstance(n, ast.Call)}
    assert calls["parent_death"] < calls["c.scientific_binding"]
    assert "torch" not in sys.modules


def test_paid_preparation_binding_and_cap_scope(tmp_path, monkeypatch):
    with pytest.raises(c.PendingCertification):
        c.preparation_cost(None)
    prep = synthetic_preparation()
    record = tmp_path / prep["evidence"][0]["path"]
    record.write_bytes(b"synthetic already-paid record")
    prep["evidence"][0].update(sha256=c.sha(record), bytes=record.stat().st_size)
    assert c.preparation_cost(prep, tmp_path) == prep
    with pytest.raises(ValueError):
        c.preparation_cost({**prep, "cpu_limit_scope": "unspecified"})
    with pytest.raises(ValueError):
        c.preparation_cost({**prep, "known_cpu_seconds": 0})
    monkeypatch.setattr(billing.old, "cpu", lambda: {"total_seconds": 2.})
    shared = billing.Shared(tmp_path / "counts.bin", create=True)
    deployment = {"limits": {"cpu_seconds": 6., "gpu_child_seconds": 100., "wall_seconds": 100.,
                            "disk_bytes": 20 * 1024 ** 2}, "disk_roots": [str(tmp_path)],
                  "started_monotonic": time.monotonic(), "prior_bank_cost": {"paid_elsewhere": True},
                  "prior_preparation_cost": prep}
    try:
        bill = billing.Bill(shared, deployment)
        value = bill.snapshot()
        assert value["known_consumer_cpu_seconds_including_preparation"] == 7.
        assert value["cpu_seconds_charged_to_selected_limit"] == 2.
        assert value["prior_bank_cost"] == {"paid_elsewhere": True}
        with pytest.raises(RuntimeError, match="investment exhausted"):
            billing.Bill(shared, {**deployment, "prior_preparation_cost": {
                **prep, "cpu_limit_scope": "inside_consumer_cpu_limit"}})
    finally:
        shared.close()


@pytest.mark.parametrize("wrong_runner", [False, True])
def test_consumed_admission_reaches_pending_bank(tmp_path, monkeypatch, wrong_runner):
    # Real stdlib input/hash gates plus an opaque single-use grant; no launcher/worker.
    import types
    out = tmp_path / "out"
    out.mkdir()
    identity = {"pid": run.os.getpid(), "start_ticks": 77}
    grant = {"sha": "a" * 40, "command_sha256": "b" * 64, "direction": c.DIRECTION,
             "child_pid": identity["pid"], "parent_pid": run.os.getppid()}
    launch = {"sha": grant["sha"], "command_sha256": grant["command_sha256"],
              "source_root": str(ROOT), "output_root": str(out), "direction": c.DIRECTION,
              "runner_process": {"identity": {**identity, "start_ticks": 78 if wrong_runner else 77}},
              "process": {"identity": {"pid": grant["parent_pid"]}}}
    (out / "launch-manifest.json").write_bytes(c.encoded(launch))
    prep_file = tmp_path / "already-paid.json"
    prep_file.write_bytes(c.encoded({"synthetic_preparation_cpu": 5.}))
    prep = synthetic_preparation()
    prep["evidence"] = [{"path": str(prep_file.relative_to(ROOT)), "sha256": c.sha(prep_file),
                         "bytes": prep_file.stat().st_size}]
    binding = {"investment": {"selected": True, "limits": {"cpu_seconds": 300., "gpu_child_seconds": 300.,
               "wall_seconds": 300., "disk_bytes": 20 * 1024 ** 2}}, "preparation_cost": prep,
               "scientific_source_sha": c.SCIENCE_SHA, "scientific_input_sha256": c.SCIENCE_INPUT,
               "frozen_sources": c.FROZEN_DIGESTS, "bank": {"status": "pending"}}
    input_path = tmp_path / "input.json"
    input_path.write_bytes(c.encoded(binding))
    monkeypatch.setenv("HMASD_ADMISSION_V1", c.encoded({"single_use": True}).decode())
    calls = []
    def admitted(path, *, direction):
        calls.append((path, direction))
        assert run.os.environ.pop("HMASD_ADMISSION_V1")
        return dict(grant)
    monkeypatch.setitem(sys.modules, "scripts.hmasd_admission", types.SimpleNamespace(require_admission=admitted))
    monkeypatch.setattr(c, "process_identity", lambda pid: dict(identity))
    argv = ["--out", str(out), "--seed", "0", "--launch-sha", grant["sha"],
            "--input-manifest", str(input_path), "--input-manifest-sha256", c.sha(input_path)]
    expected = ValueError if wrong_runner else c.PendingCertification
    message = "runner/source/output" if wrong_runner else "B05 complete producer certification"
    with pytest.raises(expected, match=message):
        run.main(argv)
    assert len(calls) == 1 and "HMASD_ADMISSION_V1" not in run.os.environ
    assert list(out.iterdir()) == [out / "launch-manifest.json"]
    assert "torch" not in sys.modules
