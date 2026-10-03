"""Pure input/array/stub checks. No real host/controller/scorer/model query."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_planning_opportunity_timing.b01 import evidence, host, inputs, meter, reader, run, study


class NoMeter:
    def __init__(self, **kwargs):
        self.calls = 0
    def check(self, **kwargs):
        self.calls += 1
    def arm(self):
        pass
    def close(self):
        pass
    def record(self, **kwargs):
        return {"stubbed_resource_guard": True}


def synthetic_payload(start=40, end=80):
    count = end - start
    arrays = {"positions": np.arange((count + 1) * 24, dtype=np.float64).reshape(count + 1, 8, 3),
              "controller_estimates": np.full((count + 1, 8, 3), -0., np.float64),
              "actions": np.zeros((count, 8, 3), np.float32), "masks": np.full(count, 255, np.int64),
              "reward_components": np.zeros((count, 4), np.float64),
              "report_times": np.arange(start, end, 10, dtype=np.int64),
              "reports": np.zeros((len(range(start, end, 10)), 133), np.float32)}
    return {"arrays": arrays, "summary": {"start_t": start, "end_t": end},
            "decisions": [{"t": t, "phase": "ordinary"} for t in range(start, end)]}


def test_order_world_bindings_and_finite_counts():
    order = inputs.mission_order()
    assert order[:4] == [("audit", 29523900, a) for a in inputs.ARMS]
    assert len(order) == 68 and len(set(order)) == 68
    for i, w in enumerate(host.WORLD_IDS):
        assert order[4 + 4 * i:8 + 4 * i] == [("result", w, inputs.ARMS[(i + k) % 4]) for k in range(4)]
    # Read the already declared initial arrays, without a world/RNG constructor.
    record = json.loads(host.WORLD_FILE.read_text())
    assert record["address"] == [261003, 73]
    assert [row["world_id"] for row in record["worlds"]] == list(host.ALL_WORLD_IDS)
    assert sum(v["worker_state_mask_requests"] for v in inputs.ARM_LIMITS.values()) * 17 == 369017368
    assert sum(v["model_physical_transitions"] for v in inputs.ARM_LIMITS.values()) * 17 == 1369520
    with pytest.raises(ValueError, match="ceiling"):
        inputs.check_costs({"worker_state_mask_requests": 1891197, "model_physical_transitions": 0}, "G2")


def test_evidence_shared_payload_and_lossless_compaction(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    store = evidence.EvidenceStore(tmp_path, raw, NoMeter())
    outer = synthetic_payload()
    outer["decisions"][20]["predicted_temporal_selection"] = {"selected": "stay"}
    prefix = evidence.project_segment(outer, 40, 60, {"start_t": 40, "end_t": 60}, "prefix")
    suffix = evidence.project_segment(outer, 60, 80, {"start_t": 60, "end_t": 80}, "suffix")
    for kind, payload in (("prefix", prefix), ("suffix", suffix)):
        payload["certificate"] = {"start_t": payload["summary"]["start_t"], "end_t": payload["summary"]["end_t"]}
        store.segment_sink("ae/first/stay/t60/" + kind, payload)
    store.branch_sink("ae/first/stay/t60/outer", outer)
    inner = synthetic_payload(60, 80)
    inner["certificate"] = {"start_t": 60, "end_t": 80}
    store.segment_sink("ae/first/stay/t60/inner/stay", inner)
    branch = deepcopy(inner)
    branch["summary"]["identity"] = {"tree": "ae"}
    store.branch_sink("ae/first/stay/t60/inner/stay", branch)
    assert store.branches[-1]["raw"] == store.segments[-1]["raw"]
    catalog = store.catalog(SimpleNamespace(plans={}, selections={}, banks={}))
    path = raw / "evidence.json.gz"
    evidence.write_catalog(path, catalog)
    originals = {r["id"]: evidence.load_payload(tmp_path, r) for r in catalog["segments"]}
    removed = evidence.compact_verified_segments(tmp_path, path, catalog)
    assert len(removed["deleted"]) == 4 and removed["allocated_file_bytes_removed"] > 0
    assert all(not Path(item["path"]).exists() for item in removed["deleted"])
    parents = {r["id"]: r for r in catalog["model_branches"]}
    for row in catalog["segments"]:
        inputs.same_payload(evidence.segment_payload(tmp_path, row, parents), originals[row["id"]], "recovered segment")
    for row in catalog["model_branches"]:
        assert inputs.checked_file(tmp_path, row["raw"]).is_file()
    assert json.loads(__import__('gzip').open(path, 'rt').read()) == catalog


def test_compaction_refuses_nonidentical_payload_without_deleting(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    store = evidence.EvidenceStore(tmp_path, raw, NoMeter())
    outer = synthetic_payload()
    prefix = evidence.project_segment(outer, 40, 60, {"start_t": 40, "end_t": 60}, "prefix")
    prefix["certificate"] = {"start_t": 40, "end_t": 60}
    prefix["arrays"]["controller_estimates"][0, 0, 0] = +0.  # signed-zero tamper must not disappear.
    store.segment_sink("a2/first/stay/prefix", prefix)
    store.branch_sink("a2/first/stay/outer", outer)
    catalog = store.catalog(SimpleNamespace(plans={}, selections={}, banks={}))
    old_path = inputs.checked_file(tmp_path, catalog["segments"][0]["raw"])
    with pytest.raises(ValueError, match="bit/dtype/shape"):
        evidence.compact_verified_segments(tmp_path, raw / "evidence.json.gz", catalog)
    assert old_path.exists() and "raw" in catalog["segments"][0]


def test_admission_precedes_output_and_scientific_import(monkeypatch, tmp_path):
    import scripts.hmasd_admission as admission
    def refuse(*args, **kwargs):
        assert kwargs["direction"] == inputs.DIRECTION
        raise RuntimeError("synthetic admission refusal")
    monkeypatch.setattr(admission, "require_admission", refuse)
    out = tmp_path / "not_created"
    with pytest.raises(RuntimeError, match="synthetic admission refusal"):
        run.main(["--out", str(out), "--seed", "29523000", "--launch-sha", "a" * 40])
    assert not out.exists()
    with pytest.raises(SystemExit):
        run.parser().parse_args(["--out", str(out), "--seed", "29523000", "--launch-sha", "a" * 40, "--resume"])


def test_disk_meter_deduplicates_inodes_and_does_not_follow_links(tmp_path):
    root = tmp_path / "owned"
    root.mkdir()
    a = root / "one"
    a.write_bytes(b"x" * 8192)
    (root / "same_inode").hardlink_to(a)
    outside = tmp_path / "external"
    outside.write_bytes(b"y" * 16384)
    link = root / "link"
    link.symlink_to(outside)
    expected = sum(p.lstat().st_blocks * 512 for p in (root, a, link))
    assert meter.allocated_bytes([root, root]) == expected


@pytest.mark.parametrize("kind", ["cpu", "wall", "disk"])
def test_operation_limit_closes_before_declared_ceiling(monkeypatch, tmp_path, kind):
    usage = {"cpu_seconds": 0., "self_user_seconds": 0., "self_system_seconds": 0.,
             "children_user_seconds": 0., "children_system_seconds": 0., "peak_rss_kib": 0}
    now = [0.]
    monkeypatch.setattr(meter, "resources", lambda: usage.copy())
    monkeypatch.setattr(meter.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(meter, "local_overlap", lambda: [])
    monkeypatch.setattr(meter, "allocated_bytes", lambda roots: 0 if kind != "disk" or not now[0] else 10 * 1024**3)
    guard = meter.Meter(start_wall=0., source=tmp_path, out=tmp_path, preparation_cpu=5., limits=inputs.RESOURCE_LIMITS)
    if kind == "cpu":
        usage["cpu_seconds"] = 72000. - 300. - 5.
    now[0] = 172800. if kind == "wall" else 1.
    with pytest.raises(meter.OperationLimit):
        guard.check(force_disk=True)


def test_cpu_signal_disarms_before_retention_without_reopening_science(monkeypatch, tmp_path):
    handlers, events = {}, []
    monkeypatch.setattr(meter, "local_overlap", lambda: [])
    monkeypatch.setattr(meter, "allocated_bytes", lambda roots: 0)
    monkeypatch.setattr(meter.resource, "getrlimit", lambda kind: (-1, -1))
    monkeypatch.setattr(meter.resource, "setrlimit", lambda kind, pair: events.append(("cpu_limit", pair)))
    def install(number, handler):
        old = handlers.get(number, "original_handler")
        handlers[number] = handler
        events.append(("signal", number))
        return old
    monkeypatch.setattr(meter.signal, "signal", install)
    monkeypatch.setattr(meter.signal, "setitimer", lambda which, value: events.append(("wall_timer", value)))
    guard = meter.Meter(start_wall=meter.time.monotonic(), source=tmp_path, out=tmp_path,
                        preparation_cpu=5., limits=inputs.RESOURCE_LIMITS)
    guard.arm()
    assert guard.armed and events[2][1][0] <= 71695
    trigger = handlers[meter.signal.SIGXCPU]
    with pytest.raises(meter.OperationLimit, match="resource signal"):
        trigger(meter.signal.SIGXCPU, None)
    assert not guard.armed and handlers[meter.signal.SIGXCPU] == "original_handler"
    assert ("cpu_limit", (-1, -1)) in events
    (tmp_path / "retained-after-stop").write_text("retention remains available")
    with pytest.raises(meter.OperationLimit):
        guard.check()


def stub_scene():
    positions = np.zeros((8, 3), dtype=np.float64)
    positions[:, 2] = 50
    return SimpleNamespace(world_id=29523900, user_positions=np.zeros((50, 2), np.float64), uav_positions=positions)


class StubNative:
    def __init__(self, scene):
        self.uav_positions = scene.uav_positions.copy()
        self.sinr_matrix = np.zeros((8, 50), np.float64)
        self.connections = np.zeros((8, 50), bool)
        self.uav_sinr_matrix = np.zeros((8, 8), np.float64)
    def _local_user_entries(self, i):
        return [], None
    def _local_uav_entries(self, i):
        return [], None
    def set_transmitter_mask(self, mask):
        assert mask.all()


class StubEnv:
    def __init__(self, scene):
        self.native, self.scene, self.t, self.closed = StubNative(scene), scene, 0, False
        self.env = SimpleNamespace(env=self.native)
    def state(self):
        return reader._public_state(self.native.uav_positions, self.scene.user_positions, self.t, 500)
    def reset(self, seed):
        return np.zeros((8, 104)), {"state": self.state()}
    def step(self, command):
        assert not command.any()
        self.t += 1
        return np.zeros((8, 104)), 0., False, self.t == 500, {"next_state": self.state(),
            "reward_components": {"reward_info": dict.fromkeys(study.COMPONENTS, 0.)}}
    def close(self):
        self.closed = True


class StubPolicy:
    def __init__(self, scene, fail_at=None):
        self.controller = SimpleNamespace(positions=scene.uav_positions.copy(), users=scene.user_positions.copy(),
                                          commands=np.zeros((8, 3), np.float32), next_t=0)
        self.plans, self.selections, self.banks = {}, {}, {}
        self.second_t, self.fail_at = 50, fail_at
    def select(self, t, report, mask):
        assert t == self.controller.next_t
        if t == self.fail_at:
            raise RuntimeError("synthetic cell failure")
        if t in (40, 50):
            self.plans[t] = {"initiated": False}
            self.selections[t] = {"branches": [], "selected_branch": "stay"}
        self.controller.next_t += 1
        return self.controller.commands.copy(), mask, {"t": t, "phase": "ordinary", "old_mask": mask, "issued_mask": mask}


def patch_stub_native(monkeypatch, scene, *, fail_at=None):
    made = []
    def env(*args):
        result = StubEnv(scene)
        made.append(result)
        return result
    monkeypatch.setattr(study, "make_env", env)
    monkeypatch.setattr(study, "make_policy", lambda *args, **kwargs: StubPolicy(scene, fail_at))
    return made


def test_collector_retains_native_prefix_on_first_cell_failure(monkeypatch, tmp_path):
    scene = stub_scene()
    made = patch_stub_native(monkeypatch, scene, fail_at=17)
    with pytest.raises(RuntimeError, match="synthetic cell failure"):
        study.evaluate_episode("G_E", scene, "audit", tmp_path, NoMeter())
    folder = tmp_path / "raw" / "audit_n8_G_E_w29523900"
    status = json.loads((folder / "cell-status.json").read_text())
    assert status["complete"] is False and status["native_steps_retained"] == 17
    assert made[0].closed
    with np.load(folder / "native.npz") as raw:
        assert raw["positions"].shape == (18, 8, 3)
        assert raw["history_next_t"].tolist() == list(range(1, 18))
    assert len(inputs.load_trace(folder / "native.jsonl.gz")) == 17


def test_native_pipeline_reader_uses_saved_history_and_stops_on_tamper(monkeypatch, tmp_path):
    scene = stub_scene()
    patch_stub_native(monkeypatch, scene)
    row = study.evaluate_episode("G_E", scene, "audit", tmp_path, NoMeter())
    # All actual physics methods are stubbed; this tests collector/reader wiring only.
    monkeypatch.setattr(reader.uav_radio, "free_space_user_path_loss", lambda p, u: np.zeros((8, 50)))
    monkeypatch.setattr(reader.uav_radio, "user_sinr_from_path_loss", lambda p, **kw: np.zeros((8, 50)))
    monkeypatch.setattr(reader.uav_radio, "greedy_connection_assignment", lambda *args: np.zeros((8, 50), bool))
    monkeypatch.setattr(reader, "_native_view", lambda *args: SimpleNamespace(
        _local_user_entries=lambda i: ([], None), _local_uav_entries=lambda i: ([], None)))
    monkeypatch.setattr(reader.MultiUAVEnv, "_compute_uav_path_loss_matrix", lambda view: np.zeros((8, 8)))
    monkeypatch.setattr(reader.MultiUAVEnv, "_compute_uav_uav_sinr_matrix", lambda view: np.zeros((8, 8)))
    monkeypatch.setattr(reader.MultiUAVEnv, "_get_observation_vectorized", lambda *args: {"obs": np.zeros(104)})
    monkeypatch.setattr(reader.UAVBaseStationEnv, "_compute_reward", lambda view: setattr(view, "reward_info", dict.fromkeys(study.COMPONENTS, 0.)))
    monkeypatch.setattr(reader, "predict_next", lambda p, a: p.copy())
    monkeypatch.setattr(reader, "forecast_comparison", lambda *args: {"stub": True})
    # A synthetic all-zero assignment is inconsistent with the real capacity identity.
    # Stub aggregate metrics together, leaving history/arrays/counters checks real.
    monkeypatch.setattr(reader, "metrics", lambda *args: row["metrics"])
    row["metrics"]["capacity_identity_holds"] = True
    reading, _ = reader.read_episode(row, tmp_path, scene, NoMeter())
    assert reading["all_native_snapshots"] == 501 and reading["complete"]
    path = inputs.checked_file(tmp_path, row["raw"])
    arrays = inputs.load_arrays(path)
    arrays["history_commands"][99, 0, 0] = 1
    with path.open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    row["raw"] = inputs.artifact(path, tmp_path)
    with pytest.raises(ValueError, match="actual private history"):
        reader.read_episode(row, tmp_path, scene, NoMeter())


def test_complete_chain_runs_audits_then_result_groups_and_fails_closed(monkeypatch, tmp_path):
    events = []
    config = {"preparation": {"metered_cpu_seconds": 3.}, "resource_limits": inputs.RESOURCE_LIMITS}
    monkeypatch.setattr(study, "fixed_config", lambda: deepcopy(config))
    monkeypatch.setattr(study, "Meter", NoMeter)
    monkeypatch.setattr(study, "bound_worlds", lambda: {w: SimpleNamespace(world_id=w) for w in host.ALL_WORLD_IDS})
    monkeypatch.setattr(study, "verify_prefixes", lambda *args: None)
    monkeypatch.setattr(reader, "validate_worker", lambda *args: None)
    monkeypatch.setattr(reader, "summarize_reading", lambda *args: {"status": "COMPLETE"})
    def evaluate(arm, scene, phase, out, guard):
        events.append(("worker", phase, scene.world_id, arm))
        path = out / f"{phase}_{scene.world_id}_{arm}.json"
        path.write_text("{}")
        return {"arm": arm, "world_id": scene.world_id, "phase": phase,
                "costs": dict.fromkeys(inputs.WORKER_LIMITS, 0), "evidence_catalog": inputs.artifact(path, out)}
    def read(row, out, scene, guard):
        events.append(("reader", row["phase"], row["world_id"], row["arm"]))
        return {k: row[k] for k in ("phase", "world_id", "arm")}, {}
    monkeypatch.setattr(study, "evaluate_episode", evaluate)
    monkeypatch.setattr(reader, "read_episode", read)
    monkeypatch.setattr(study, "compact_verified_segments", lambda *args, **kwargs: {"deleted": [], "allocated_file_bytes_removed": 0})
    args = SimpleNamespace(out=tmp_path / "pass", launch_sha="a" * 40)
    result = study.run_study(args, {"command_sha256": "b" * 64}, 0.)
    assert result["status"] == "COMPLETE" and len(events) == 136
    assert [e[0] for e in events[:8]] == ["worker"] * 4 + ["reader"] * 4
    assert all(e[1] == "audit" for e in events[:8]) and all(e[1] == "result" for e in events[8:])
    assert [e[1:] for e in events if e[0] == "worker"] == inputs.mission_order()
    events.clear()
    def fail_read(*args):
        raise RuntimeError("synthetic first-reader failure")
    monkeypatch.setattr(reader, "read_episode", fail_read)
    args.out = tmp_path / "fail"
    with pytest.raises(RuntimeError, match="first-reader failure"):
        study.run_study(args, {"command_sha256": "b" * 64}, 0.)
    saved = json.loads((args.out / "summary.json").read_text())
    assert saved["status"] == "FAILED_CLOSED" and saved["failure"]["purchase_closed"]
    assert len(saved["episodes"]) == 4 and not saved["readings"] and len(events) == 4
    with pytest.raises(FileExistsError):
        study.run_study(args, {"command_sha256": "b" * 64}, 0.)


def test_unlink_failure_retains_new_catalog_binding_in_failed_summary(monkeypatch, tmp_path):
    config = {"preparation": {"metered_cpu_seconds": 3.}}
    monkeypatch.setattr(study, "fixed_config", lambda: deepcopy(config))
    monkeypatch.setattr(study, "Meter", NoMeter)
    monkeypatch.setattr(study, "bound_worlds", lambda: {w: SimpleNamespace(world_id=w) for w in host.ALL_WORLD_IDS})
    monkeypatch.setattr(study, "verify_prefixes", lambda *args: None)
    def evaluate(arm, scene, phase, out, guard):
        folder = out / "raw" / arm
        folder.mkdir(parents=True)
        store = evidence.EvidenceStore(out, folder, NoMeter())
        outer = synthetic_payload()
        prefix = evidence.project_segment(outer, 40, 60, {"start_t": 40, "end_t": 60}, "prefix")
        prefix["certificate"] = {"start_t": 40, "end_t": 60}
        store.segment_sink("a2/first/stay/prefix", prefix)
        store.branch_sink("a2/first/stay/outer", outer)
        catalog = store.catalog(SimpleNamespace(plans={}, selections={}, banks={}))
        path = folder / "evidence.json.gz"
        evidence.write_catalog(path, catalog)
        return {"arm": arm, "world_id": scene.world_id, "phase": phase,
                "costs": dict.fromkeys(inputs.WORKER_LIMITS, 0), "evidence_catalog": inputs.artifact(path, out)}
    def read(row, out, scene, guard):
        return {k: row[k] for k in ("phase", "world_id", "arm")}, inputs.load_catalog(inputs.checked_file(out, row["evidence_catalog"]))
    monkeypatch.setattr(study, "evaluate_episode", evaluate)
    monkeypatch.setattr(reader, "read_episode", read)
    original_unlink = Path.unlink
    def refuse(path, *args, **kwargs):
        if path.name == "prefix.npz":
            raise OSError("synthetic compaction unlink failure")
        return original_unlink(path, *args, **kwargs)
    monkeypatch.setattr(Path, "unlink", refuse)
    args = SimpleNamespace(out=tmp_path / "failed", launch_sha="a" * 40)
    with pytest.raises(OSError, match="compaction unlink failure"):
        study.run_study(args, {"command_sha256": "b" * 64}, 0.)
    saved = json.loads((args.out / "summary.json").read_text())
    assert saved["status"] == "FAILED_CLOSED"
    row = saved["episodes"][0]
    catalog = inputs.load_catalog(inputs.checked_file(args.out, row["evidence_catalog"]))
    assert saved["readings"][0]["retained_evidence_catalog"] == row["evidence_catalog"]
    parents = {r["id"]: r for r in catalog["model_branches"]}
    assert "derived_from_model" in catalog["segments"][0]
    for segment in catalog["segments"]:
        assert evidence.segment_payload(args.out, segment, parents)["arrays"]["actions"].shape[0] == 20
    assert saved["cleanup"][0]["replacement_catalog_published"] is True
    assert not saved["cleanup"][0]["deleted"] and len(saved["cleanup"][0]["planned_deletions"]) == 2


def test_user_gaps_retain_both_censoring_edges():
    connections = np.zeros((501, 8, 50), bool)
    connections[2:5, 0, 1] = True  # user1 served ticks1..3, not reset observation.
    result = reader.individual_continuity({"connections": connections})
    never, sometimes = result["per_user"][:2]
    assert never["served_user_ticks"] == 0 and never["longest_unserved_gap"] == 500
    assert never["gaps"] == [{"start_tick": 0, "end_tick_exclusive": 500, "length": 500,
                              "left_censored": True, "right_censored": True}]
    assert sometimes["served_user_ticks"] == 3
    assert sometimes["gaps"][0]["left_censored"] and sometimes["gaps"][-1]["right_censored"]
