"""B02 input/reader/retention checks using saved synthetic arrays and stub science."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_planning_opportunity_timing.b01 import evidence
from experiments.candidates.uav_planning_opportunity_timing.b02 import host, inputs, meter, reader, run, study


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


def test_order_source_arrays_and_all_declared_ceilings():
    order = inputs.mission_order()
    assert order[:4] == [("audit", 29524900, a) for a in inputs.ARMS]
    assert len(order) == len(set(order)) == 68
    for i, w in enumerate(host.WORLD_IDS):
        assert order[4 + 4 * i:8 + 4 * i] == [("result", w, inputs.ARMS[(i + k) % 4]) for k in range(4)]
    record = json.loads(host.WORLD_FILE.read_text())  # no world/RNG construction.
    assert record["address"] == [261003, 74]
    assert [r["world_id"] for r in record["worlds"]] == list(host.ALL_WORLD_IDS)
    for row in record["worlds"]:
        for field in ("user_positions", "uav_positions"):
            assert __import__("hashlib").sha256(np.asarray(row[field], "<f8").tobytes()).hexdigest() == row[field + "_sha256_le_f64"]
    assert list(inputs.WORKER_LIMITS.values()) == [803523292, 3023280, 884, 618800, 24752000, 7072, 7752]
    binding, _ = inputs.source_bindings()
    assert len(inputs.INHERITED_PATHS) == 55 and set(inputs.SOURCE_PATHS) == set(binding)
    assert inputs.fixed_config()["actual_opportunities"] == 204
    cost = inputs.ARM_LIMITS["A_E4"].copy()
    cost["segment_certificates"] += 1
    with pytest.raises(ValueError, match="ceiling"):
        inputs.check_costs(cost, "A_E4")


def test_frozen_source_tamper_is_refused(monkeypatch):
    original = inputs.artifact
    target = inputs.INHERITED_PATHS[0]
    def tampered(path, root):
        row = original(path, root)
        if str(Path(path).relative_to(root)) == target:
            row["sha256"] = "0" * 64
        return row
    monkeypatch.setattr(inputs, "artifact", tampered)
    with pytest.raises(ValueError, match="frozen inherited source"):
        inputs.source_bindings()


def test_forecast_scopes_do_not_assert_unmodeled_rolling_tails():
    times = [40, 90, 140, 190]
    assert reader.forecast_windows("G_E4", times) == [
        (1, 40, 90, "before_next_actual_selection"), (2, 90, 140, "before_next_actual_selection"),
        (3, 140, 190, "before_next_actual_selection"), (4, 190, 500, "complete_remaining_program")]
    assert reader.forecast_windows("A_E4", times) == [
        (1, 40, 90, "before_next_actual_selection"), (2, 90, 140, "before_next_actual_selection"),
        (3, 140, 500, "complete_remaining_program"), (3, 140, 190, "third_choice_additional_prefix_diagnostic"),
        (4, 190, 500, "complete_remaining_program")]
    assert all(end == 500 for _, _, end, _ in reader.forecast_windows("A_E", [40, 50]))
    assert all(end == 500 for _, _, end, _ in reader.forecast_windows("A2", [40, 120]))


def synthetic_payload(start=40, end=500):
    count = end - start
    return {"arrays": {"positions": np.zeros((count + 1, 8, 3), np.float64),
        "controller_estimates": np.full((count + 1, 8, 3), -0., np.float64),
        "actions": np.zeros((count, 8, 3), np.float32), "masks": np.full(count, 255, np.int64),
        "reward_components": np.zeros((count, 4), np.float64),
        "report_times": np.arange(start, end, 10), "reports": np.zeros((len(range(start, end, 10)), 133), np.float32)},
        "summary": {"start_t": start, "end_t": end},
        "decisions": [{"t": t, "phase": "ordinary"} for t in range(start, end)]}


def test_forecast_difference_is_retained_on_valid_interval(tmp_path):
    times = [40, 60, 80, 100]
    raw = {"positions": np.zeros((501, 8, 3)), "connections": np.zeros((501, 8, 50), bool),
           "actions": np.zeros((500, 8, 3), np.float32), "mask": np.full(500, 255), "components": np.zeros((500, 4))}
    catalog = {"selections": {}, "model_branches": []}
    for i, t in enumerate(times):
        payload = synthetic_payload(t)
        # Valid forecast numerical errors are reported rather than raising.
        payload["arrays"]["positions"][0, 0, 0] = .00001
        payload["arrays"]["actions"][-1, 0, 0] = 1
        payload["arrays"]["reward_components"][-1, :2] = [1., 1.]
        if i < 3:
            payload["summary"]["inner_selection"] = {"start_t": times[i + 1],
                "selected_branch": "stay", "selected_physical_identity": "stay"}
        item = dict(id=f"op{i + 1}", **evidence.save_payload(tmp_path, tmp_path / f"op{i + 1}", payload))
        catalog["model_branches"].append(item)
        catalog["selections"][str(t)] = {"selected_model_branch": item["id"], "selected_branch": "stay",
                                       "selected_physical_identity": "stay"}
    row = {"arm": "A_E4", "opportunity_times": times, "raw": {"path": "synthetic-native"}}
    result = reader.forecast_comparisons(row, catalog, raw, tmp_path)
    assert len(result) == 5
    assert result[0]["different_command_ticks"] == [] and result[0]["model_minus_native_J"] == 0
    assert result[2]["different_command_ticks"] == [499] and result[2]["model_minus_native_J"] == 1
    assert result[3]["different_command_ticks"] == [] and result[3]["end_t"] == 100
    assert all(r["max_coordinate_abs_error_m"] == .00001 for r in result)


def test_ordinal_segment_compaction_is_lossless_and_refuses_tamper(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    store = evidence.EvidenceStore(tmp_path, raw, NoMeter())
    originals = {}
    for ordinal, start in ((2, 90), (3, 140)):
        scope = f"ae/op{ordinal}/stay/t{start}/t{start + 10}"
        outer = synthetic_payload(start)
        outer["decisions"][10]["predicted_temporal_selection"] = {"selected": "stay"}
        for kind, a, b in (("prefix", start, start + 10), ("suffix", start + 10, 500)):
            piece = evidence.project_segment(outer, a, b, {"start_t": a, "end_t": b}, kind)
            piece["certificate"] = {"start_t": a, "end_t": b}
            identifier = scope + "/" + kind
            store.segment_sink(identifier, piece)
            originals[identifier] = deepcopy(piece)
        store.branch_sink(scope + "/outer", outer)
    catalog = store.catalog(SimpleNamespace(plans={}, selections={}, banks={}))
    path = raw / "catalog.json.gz"
    evidence.write_catalog(path, catalog)
    reclaimed = evidence.compact_verified_segments(tmp_path, path, catalog)
    assert len(reclaimed["deleted"]) == 8 and reclaimed["allocated_file_bytes_removed"] > 0
    parents = {r["id"]: r for r in catalog["model_branches"]}
    for item in catalog["segments"]:
        inputs.same_payload(evidence.segment_payload(tmp_path, item, parents), originals[item["id"]], "ordinal projection")
    assert all(not Path(r["path"]).exists() for r in reclaimed["deleted"])
    with pytest.raises(ValueError, match="duplicate"):
        store.segment_sink(next(iter(originals)), next(iter(originals.values())))


def test_late_stays_do_not_mask_a_changed_complete_program(tmp_path):
    rows = []
    scene = stub_scene()
    for arm in inputs.ARMS:
        folder = tmp_path / arm
        folder.mkdir()
        policy = StubPolicy(scene, arm)
        for t in range(500):
            policy.select(t, None, 255)
        for selection in policy.selections.values():
            selection["selected_model_branch"] = "ae/first/stay/t50/inner/stay"
        raw = {"positions": np.zeros((501, 8, 3)), "users": np.zeros((50, 2)),
               "actions": np.zeros((500, 8, 3), np.float32), "mask": np.full(500, 255),
               "connections": np.zeros((501, 8, 50), bool)}
        # Pure array comparison fixture: a second-selector consequence, after t50.
        if arm == "A_E4":
            raw["actions"][55, 0, 0] = 1
        native_path = folder / "native.npz"
        np.savez_compressed(native_path, **raw)
        store = evidence.EvidenceStore(tmp_path, folder, NoMeter())
        first = synthetic_payload(50)
        first["certificate"] = {"start_t": 50, "end_t": 500}
        store.segment_sink("ae/first/stay/t50/inner/stay", first)
        store.branch_sink("ae/first/stay/t50/inner/stay", first)
        store.candidate_sink("ae/first/bank", np.zeros((0, 40)))
        policy.banks["ae/first/bank"] = {"candidate_count": 0}
        catalog_path = folder / "catalog.json.gz"
        evidence.write_catalog(catalog_path, store.catalog(policy))
        rows.append({"arm": arm, "world_id": scene.world_id, "phase": "audit", "opportunity_times": policy.times,
            "raw": inputs.artifact(native_path, tmp_path), "evidence_catalog": inputs.artifact(catalog_path, tmp_path)})
    result = study.verify_prefixes(tmp_path, rows)
    assert result["AE4_AE_native_prefix_equal_until_input_t"] == 50
    assert all(not row["initiated"] for row in result["actual_choice_sequences"]["A_E4"][2:])
    contrast = result["program_comparisons"]["A_E4-A_E"]
    assert contrast["different_command_ticks"] == [55] and not contrast["all_saved_native_arrays_bits_equal"]


def test_individual_losses_survive_positive_team_averages():
    panel, read_panel = {}, {}
    for w in host.WORLD_IDS:
        for arm in ("A_E4", "A_E"):
            panel[w, arm] = {"metrics": {"J": 2 if arm == "A_E4" else 1, "served": 3 if arm == "A_E4" else 2}}
            rows = [{"user": u, "served_user_ticks": 100, "longest_unserved_gap": 10} for u in range(50)]
            read_panel[w, arm] = {"individual_continuity": {"per_user": rows}}
    read_panel[host.WORLD_IDS[0], "A_E4"]["individual_continuity"]["per_user"][0].update(
        served_user_ticks=0, longest_unserved_gap=500)
    read_panel[host.WORLD_IDS[1], "A_E"]["individual_continuity"]["per_user"][1].update(
        served_user_ticks=0, longest_unserved_gap=500)
    result = reader.individual_comparison("A_E4", "A_E", panel, read_panel)
    assert result["new_never_served"] == result["rescued_never_served"] == 1
    assert result["served_tick_negative"] == 1 and result["longest_gap_worsened"] == 1
    assert len(result["losses_with_team_positive_metric"]) == 1
    assert result["losses_with_team_positive_metric"][0]["user"] == 0


def test_admission_before_output_and_no_resume(monkeypatch, tmp_path):
    import scripts.hmasd_admission as admission
    def refuse(*args, **kwargs):
        assert kwargs["direction"] == inputs.DIRECTION
        raise RuntimeError("synthetic admission refusal")
    monkeypatch.setattr(admission, "require_admission", refuse)
    out = tmp_path / "not_created"
    with pytest.raises(RuntimeError, match="synthetic admission refusal"):
        run.main(["--out", str(out), "--seed", "29524000", "--launch-sha", "a" * 40])
    assert not out.exists()
    with pytest.raises(SystemExit):
        run.parser().parse_args(["--out", str(out), "--seed", "29524000", "--launch-sha", "a" * 40, "--resume"])


def stub_scene():
    position = np.zeros((8, 3), np.float64)
    position[:, 2] = 50
    return SimpleNamespace(world_id=29524900, user_positions=np.zeros((50, 2)), uav_positions=position)


class StubEnv:
    def __init__(self, scene):
        self.scene, self.t, self.closed = scene, 0, False
        self.native = SimpleNamespace(uav_positions=scene.uav_positions.copy(), sinr_matrix=np.zeros((8, 50)),
            connections=np.zeros((8, 50), bool), uav_sinr_matrix=np.zeros((8, 8)),
            _local_user_entries=lambda i: ([], None), _local_uav_entries=lambda i: ([], None),
            set_transmitter_mask=lambda mask: None)
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
    def __init__(self, scene, arm="G_E4", fail_at=None):
        self.controller = SimpleNamespace(positions=scene.uav_positions.copy(), users=scene.user_positions.copy(),
                                          commands=np.zeros((8, 3), np.float32), next_t=0)
        self.plans, self.selections, self.banks = {}, {}, {}
        self.times = [40, 50, 60, 70] if arm.endswith("4") else [40, 120] if arm == "A2" else [40, 50]
        self.fail_at = fail_at
    def select(self, t, report, mask):
        assert t == self.controller.next_t
        if t == self.fail_at:
            raise RuntimeError("synthetic cell failure")
        if t in self.times:
            plan = {"start_t": t, "initiated": False, "duration": 0, "arrival_t": None, "candidate_count": 0}
            self.plans[t] = plan
            self.selections[t] = {"start_t": t, "selected_plan": plan, "selected_branch": "stay",
                "selected_model_branch": f"synthetic/{t}",
                "selected_physical_identity": "stay", "original_R": {"candidate_count": 0},
                "branches": [{"id": "stay", "plan": None, "physical_identity": "stay", "modeled_execution_identity": {}, "summary": {}}]}
        self.controller.next_t += 1
        return self.controller.commands.copy(), mask, {"t": t, "phase": "ordinary", "old_mask": mask, "issued_mask": mask}


def patch_native(monkeypatch, scene, fail_at=None):
    made = []
    def env(*args):
        result = StubEnv(scene)
        made.append(result)
        return result
    monkeypatch.setattr(study, "make_env", env)
    monkeypatch.setattr(study, "make_policy", lambda arm, **kwargs: StubPolicy(scene, arm, fail_at))
    return made


def test_partial_native_failure_is_retained(monkeypatch, tmp_path):
    scene = stub_scene()
    made = patch_native(monkeypatch, scene, fail_at=17)
    with pytest.raises(RuntimeError, match="synthetic cell failure"):
        study.evaluate_episode("A_E4", scene, "audit", tmp_path, NoMeter())
    folder = tmp_path / "raw" / "audit_n8_A_E4_w29524900"
    status = json.loads((folder / "cell-status.json").read_text())
    assert status["complete"] is False and status["native_steps_retained"] == 17
    assert made[0].closed
    assert len(inputs.load_trace(folder / "native.jsonl.gz")) == 17
    with np.load(folder / "native.npz") as raw:
        assert raw["positions"].shape == (18, 8, 3)


def test_full_native_reader_reconstructs_and_refuses_history_tamper(monkeypatch, tmp_path):
    scene = stub_scene()
    patch_native(monkeypatch, scene)
    row = study.evaluate_episode("G_E4", scene, "audit", tmp_path, NoMeter())
    monkeypatch.setattr(reader.uav_radio, "free_space_user_path_loss", lambda p, u: np.zeros((8, 50)))
    monkeypatch.setattr(reader.uav_radio, "user_sinr_from_path_loss", lambda p, **kw: np.zeros((8, 50)))
    monkeypatch.setattr(reader.uav_radio, "greedy_connection_assignment", lambda *args: np.zeros((8, 50), bool))
    monkeypatch.setattr(reader, "_native_view", lambda *args: SimpleNamespace(
        _local_user_entries=lambda i: ([], None), _local_uav_entries=lambda i: ([], None)))
    monkeypatch.setattr(reader.MultiUAVEnv, "_compute_uav_path_loss_matrix", lambda v: np.zeros((8, 8)))
    monkeypatch.setattr(reader.MultiUAVEnv, "_compute_uav_uav_sinr_matrix", lambda v: np.zeros((8, 8)))
    monkeypatch.setattr(reader.MultiUAVEnv, "_get_observation_vectorized", lambda *args: {"obs": np.zeros(104)})
    monkeypatch.setattr(reader.UAVBaseStationEnv, "_compute_reward", lambda v: setattr(v, "reward_info", dict.fromkeys(study.COMPONENTS, 0.)))
    monkeypatch.setattr(reader, "predict_next", lambda p, a: p.copy())
    monkeypatch.setattr(reader, "forecast_comparisons", lambda *args: [{"synthetic": True}])
    monkeypatch.setattr(reader, "metrics", lambda *args: row["metrics"])
    row["metrics"]["capacity_identity_holds"] = True
    read, _ = reader.read_episode(row, tmp_path, scene, NoMeter())
    assert read["all_native_snapshots"] == 501 and read["opportunity_times"] == [40, 50, 60, 70]
    path = inputs.checked_file(tmp_path, row["raw"])
    arrays = inputs.load_arrays(path)
    arrays["history_commands"][99, 0, 0] = 1
    with path.open("wb") as f:
        np.savez_compressed(f, **arrays)
    row["raw"] = inputs.artifact(path, tmp_path)
    with pytest.raises(ValueError, match="actual private history"):
        reader.read_episode(row, tmp_path, scene, NoMeter())


def test_pipeline_reads_each_four_arm_group_and_closes_at_first_failure(monkeypatch, tmp_path):
    events = []
    config = {"preparation": {"metered_cpu_seconds": 3.}, "resource_limits": inputs.RESOURCE_LIMITS}
    monkeypatch.setattr(study, "fixed_config", lambda: deepcopy(config))
    monkeypatch.setattr(study, "Meter", NoMeter)
    monkeypatch.setattr(study, "bound_worlds", lambda: {w: SimpleNamespace(world_id=w) for w in host.ALL_WORLD_IDS})
    monkeypatch.setattr(study, "verify_prefixes", lambda *args: {"synthetic": True})
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
    monkeypatch.setattr(study, "compact_verified_segments", lambda *args, **kwargs: None)
    args = SimpleNamespace(out=tmp_path / "complete", launch_sha="a" * 40)
    result = study.run_study(args, {"command_sha256": "b" * 64}, 0.)
    assert result["status"] == "COMPLETE" and len(events) == 136
    assert [e[0] for e in events[:8]] == ["worker"] * 4 + ["reader"] * 4
    assert [e[1:] for e in events if e[0] == "worker"] == inputs.mission_order()
    events.clear()
    def fail_read(*args):
        raise RuntimeError("synthetic first-reader failure")
    monkeypatch.setattr(reader, "read_episode", fail_read)
    args.out = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="first-reader failure"):
        study.run_study(args, {"command_sha256": "b" * 64}, 0.)
    saved = json.loads((args.out / "summary.json").read_text())
    assert saved["status"] == "FAILED_CLOSED" and saved["failure"]["purchase_closed"]
    assert len(saved["episodes"]) == 4 and not saved["readings"] and len(events) == 4
    with pytest.raises(FileExistsError):
        study.run_study(args, {"command_sha256": "b" * 64}, 0.)


@pytest.mark.parametrize("kind", ["cpu", "wall", "disk"])
def test_b02_guards_include_launch_and_owned_scratch_with_reserves(monkeypatch, tmp_path, kind):
    use = {"cpu_seconds": 0., "self_user_seconds": 0., "self_system_seconds": 0.,
           "children_user_seconds": 0., "children_system_seconds": 0., "peak_rss_kib": 0}
    now, allocation = [0.], [0]
    monkeypatch.setattr(meter.inherited, "resources", lambda: use.copy())
    monkeypatch.setattr(meter.inherited.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(meter.inherited, "local_overlap", lambda: [])
    monkeypatch.setattr(meter.inherited, "allocated_bytes", lambda roots: allocation[0])
    out = tmp_path / "runs" / inputs.DIRECTION / "test"
    out.mkdir(parents=True)
    guard = meter.Meter(start_wall=0., source=tmp_path / "source", out=out, preparation_cpu=5., limits=inputs.RESOURCE_LIMITS)
    assert tmp_path / "temp/directions" / inputs.DIRECTION in guard.roots
    inputs.write_json(out / "formal-launch-resources.json", {"cpu_seconds": 7.})
    if kind == "cpu":
        use["cpu_seconds"] = 86400 - 600 - 5 - 7
    elif kind == "wall":
        now[0] = 172800 - 1200
    else:
        allocation[0] = 12 * 1024**3 - 128 * 1024**2
    with pytest.raises(meter.OperationLimit):
        guard.check(force_disk=True)
    with pytest.raises(meter.OperationLimit):
        guard.check()
    record = guard.record(final=True)
    assert record["formal_launcher_cpu_seconds"] == 7 and record["bound_preparation_cpu_seconds"] == 5
    assert record["hard_envelope_excess_at_sample"] == dict.fromkeys(("cpu_seconds", "wall_seconds", "allocated_bytes"), 0)


def test_paired_statistics_preserve_concentration_and_undefined_net_share():
    sample = np.tile(np.arange(16), (10000, 1))
    values = np.zeros(16)
    values[:2] = [1., -1.]
    result = reader.paired_metric(values, sample)
    assert result["signed_net_contribution_shares"] is None and result["negative"] == 1
    assert result["paired_world_percentile_95"] == [0., 0.]
    values[1] = -.5
    result = reader.paired_metric(values, sample)
    assert result["signed_net_contribution_shares"][0]["share"] == 2


def test_formal_request_wall_origin_is_not_added_twice(monkeypatch, tmp_path):
    monkeypatch.setattr(meter.inherited, "local_overlap", lambda: [])
    monkeypatch.setattr(meter.inherited, "allocated_bytes", lambda roots: 0)
    monkeypatch.setattr(meter.inherited.time, "monotonic", lambda: 200.)
    out = tmp_path / "runs" / inputs.DIRECTION / "test"
    out.mkdir(parents=True)
    guard = meter.Meter(start_wall=180., source=tmp_path, out=out, preparation_cpu=0., limits=inputs.RESOURCE_LIMITS)
    inputs.write_json(out / "formal-launch-resources.json", {"cpu_seconds": 3., "started_monotonic": 170.})
    assert guard.record()["operation_wall_seconds"] == 30
    assert guard.record()["operation_wall_seconds"] == 30
    assert guard.record()["operation_wall_origin"] == "formal_request"
    inputs.write_json(out / "formal-launch-resources.json", {"cpu_seconds": 3., "started_monotonic": 181.})
    with pytest.raises(ValueError, match="formal-request start"):
        guard.check()
