"""Pure deterministic fixtures only: no native module, environment, RNG draw or model."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.typed_joint_skill_decision import contract as c
from experiments.candidates.typed_joint_skill_decision.data import (
    Bill, BudgetExceeded, COUNTERS, Store, Trace, allocated_bytes, hash_file, read_trace,
)
from experiments.candidates.typed_joint_skill_decision.run_b01_native import (
    NativeRuntime, verify_sources,
)


def raw(kind="kmeans_plain", k=4, x=100, served=()):
    return {"kind": kind, "k": k, "positions_xyz": [[x+i, 200+i, 100] for i in range(6)],
            "served": list(served)}


def fixture_candidates():
    return ([raw(k=k, x=100*k) for k in (4, 5, 6)] +
            [raw("subset_relay", k, 100*k+10, (0, 1)) for k in (4, 5, 6)] +
            [raw("subset_relay", 4, 777, (0,)), raw("subset_flat", 5, 888, (0, 1, 2))])


def features():
    plans, _ = c.select_menu(fixture_candidates())
    for p in plans:
        p["assigned_targets_xyz"] = p["positions_xyz"]
    return c.make_features([[10+i, 20, 100] for i in range(6)], [[i, i+1] for i in range(50)],
                           [2500, 2500, 30], plans)


def ledger(root, **prior):
    counters = dict.fromkeys(COUNTERS, 0)
    counters.update(prior)
    return {"schema": 1, "prior_counters": counters, "prior_cpu_seconds": 0,
            "prior_gpu_seconds": 0,
            "disk_roots": [str(root)]}


def store(tmp_path):
    target = tmp_path / "collector"
    return Store(target, Bill(ledger(tmp_path), target))


def test_worlds_and_exact_cumulative_ceiling():
    addresses = list(c.worlds())
    assert len(addresses) == 1152 and len({x["world"] for x in addresses}) == 1152
    assert [sum(x["block"] == b and x["split"] == "train" for x in addresses) for b in (1,2,3)] == [256]*3
    assert [sum(x["block"] == b and x["split"] == "test" for x in addresses) for b in (1,2,3)] == [128]*3
    assert 1152 * 8 * 500 + 384 * 500 + 16 * 500 == c.MAX_NATIVE_STEPS
    assert 1152 * 9 + 384 * (6000 + 1) == c.MAX_STATIC_CALLS


def test_preferred_slots_hash_ties_and_canonical_alias():
    candidates = fixture_candidates()
    # Higher served cardinality wins independently of source input order.
    candidates += [raw("subset_relay", 4, 1000, (0,1,2)), raw("subset_relay", 4, 1100, (0,1,2))]
    chosen, report = c.select_menu(candidates)
    tied = candidates[-2:]
    winner = min(tied, key=lambda p: __import__("hashlib").sha256(c.layout_bytes(p["positions_xyz"])).hexdigest())
    assert chosen[3]["positions_xyz"] == c.canonical_layout(winner["positions_xyz"])
    assert [(p["kind"], p["k"]) for p in chosen[:3]] == [("kmeans_plain", k) for k in (4,5,6)]
    assert chosen[7]["kind"] == "subset_flat" and report["legal_candidates"] == 8
    assert c.layout_bytes(candidates[0]["positions_xyz"]) == c.layout_bytes(list(reversed(candidates[0]["positions_xyz"])))
    # Exact, not rounded at 1e-6, is the additional canonical dedupe.
    perturbed = [row[:] for row in candidates[0]["positions_xyz"]]
    perturbed[0][0] += 1e-8
    assert c.layout_bytes(perturbed) != c.layout_bytes(candidates[0]["positions_xyz"])


def test_duplicate_fill_slots_and_sparse_mask():
    candidates = [raw(k=4), raw(k=5)]  # identical layouts keep slot0 only
    chosen, report = c.select_menu(candidates)
    assert len(chosen) == 1 and chosen[0]["construction_slot"] == 0
    assert report["preferred_duplicates"][0]["construction_slot"] == 1
    chosen, _ = c.select_menu(fixture_candidates() + [raw("subset_relay",4,900,(0,))])
    assert len({p["layout_sha256"] for p in chosen}) == 8
    for requested in range(8):
        assert c.fallback_slot(requested, [2,6]) == (requested if requested in (2,6) else 2)


def test_features_lossless_no_provenance_and_display_inversion():
    f = features()
    f["user_xy"][0][0] = float.fromhex("0x1.0000000000001p+0")
    encoded = c.encode_json(f)
    restored = json.loads(encoded)
    assert restored == f
    assert restored["user_xy"][0][0].hex() == f["user_xy"][0][0].hex()
    assert c.make_features(f["initial_uav_xyz"],f["user_xy"],f["bs_xyz"],f["plans"]) == c.make_features(f["initial_uav_xyz"],f["user_xy"],f["bs_xyz"],list(reversed(f["plans"])))
    for field in ("world", "Q", "static", "source_sha256"):
        with pytest.raises(ValueError):
            c.validate_features({**f, field: 1})
    with pytest.raises(ValueError):
        c.validate_features({**f, "display_order": [0]*8})
    with pytest.raises(ValueError):
        c.encode_json({"nonfinite": float("nan")})


def test_ordinary_rank_tie_and_stable_soft_target():
    plans = [{"construction_slot": 2, "max_travel_distance_m": 300, "total_travel_distance_m": 900},
             {"construction_slot": 6, "max_travel_distance_m": 150, "total_travel_distance_m": 500}]
    assert c.ordinary_choices(plans, {2:.8,6:.8}, .1) == {"static":6,"travel":6}
    assert c.soft_targets([.8,.8]) == [.5,.5]
    q = c.soft_targets([0.,1.])
    assert q[1] > 1-1e-10 and sum(q) == pytest.approx(1.)


def test_bill_failed_calls_consume_and_ceiling_refuses_before_next_call(tmp_path):
    target = tmp_path / "out"
    bill = Bill(ledger(tmp_path, native_step_calls=c.MAX_NATIVE_STEPS-1), target)
    bill.enter("native_step_calls")
    assert bill.total("native_steps_completed") == 0
    with pytest.raises(BudgetExceeded):
        bill.enter("native_step_calls")
    assert bill.total("native_step_calls") == c.MAX_NATIVE_STEPS
    bad = ledger(tmp_path)
    bad["prior_counters"].pop("reset_calls")
    with pytest.raises(ValueError):
        Bill(bad, target)


def test_stream_partial_and_fresh_output(tmp_path):
    s = store(tmp_path)
    try:
        trace = Trace(s, "raw/partial.gz", {"kind":"assigned_targets", "x":1})
        trace.write({"kind":"step_request","actions":[0,0,0]})
        record = trace.close("partial")
        assert list(read_trace(s.output / record["path"]))[-1]["kind"] == "step_request"
        assert record["steps"] == 0 and record["sha256"] == hash_file(s.output / record["path"])
        s.status("failed_partial", exception="fixture")
        progress = json.loads((s.output / "progress.json").read_bytes())
        assert "Q" not in str(progress) and progress["status"] == "failed_partial"
        with pytest.raises(FileExistsError):
            Store(s.output, s.bill)
    finally:
        s.close()


def test_source_identity_refuses_drift_without_import(tmp_path):
    with pytest.raises(FileNotFoundError):
        verify_sources(tmp_path)


# Pure fake APIs below do not import or instantiate the native host/executor. They
# exercise instrumentation, reset/target data flow, manifest and fixed query counts.
class FakeRNG:
    def get_state(self):
        return ("fixture", np.asarray([1,2], dtype=np.uint32), 0, 0, 0.)


class FakeEnv:
    def __init__(self, world):
        self.world_seed, self.np_random = world, FakeRNG()
        self.a2a_enabled = True
        self.reset(seed=world)
    def reset(self, seed=None):
        self.uav_positions = np.asarray([[10+i,20,100] for i in range(6)],dtype=float)
        self.user_positions = np.asarray([[i,i+1] for i in range(50)],dtype=float)
        self.ground_bs_positions = np.asarray([[2500,2500,30]],dtype=float)
        self.connections = np.zeros((6,50),dtype=bool)
        self.sinr_matrix = np.zeros((6,50))
        self.uav_connections = np.zeros((6,6),dtype=bool)
        self.uav_bs_connections = np.zeros((6,1),dtype=bool)
        self.uav_sinr_matrix = np.zeros((6,6))
        self.routing_paths = {}
        self.current_step = 0
        self.agents = list(range(6))
        self._transmitter_mask = np.ones(6,dtype=bool)
        self.action_clip_events_episode = 0
        self.channel_backend = "fixture"
        self._path_loss_cache_context = ("fixture",)
        self._path_loss_cache_hits, self._path_loss_cache_misses = 0,0
        return {}, {}
    def step(self, actions):
        self.uav_positions += np.asarray([actions[a] for a in self.agents])
        self.current_step += 1
        self.reward_info = {"coverage_backhauled":.4, "contract_reward":.2,
                            "frontend_capacity_with_path_mbps":1., "mean_relays_per_routed_uav":0.}
        return ({}, {a:.2/6 for a in self.agents}, {a:self.current_step==500 for a in self.agents},
                {a:False for a in self.agents}, {})


def fake_modules():
    def static(env, xyz, allow_a2a=True):
        env.uav_positions = np.asarray(xyz,dtype=float)
        return {"coverage_backhauled":.3, "contract_reward":.2}
    host = SimpleNamespace(CoupledRelayHost=FakeEnv, make_host=lambda world, area_size: FakeEnv(world), static_evaluate=static)
    planner = SimpleNamespace(assign_targets=lambda initial, targets: np.arange(6), static_evaluate=static,
                             build_candidates=lambda env, rng, allow_a2a, report: fixture_candidates(), ARRIVAL_TOL_M=1e-6,
                             user_association=lambda env: np.full(50,-1),
                             backhauled_users_mask=lambda env: np.zeros(50,dtype=bool))
    def execute(env, assigned, max_steps, allow_a2a, assignment):
        assert max_steps==500 and allow_a2a and assignment=="identity"
        env.reset(seed=env.world_seed)
        initial = env.uav_positions.tolist()
        for t in range(500):
            # Deliberately simple fake data-flow, not a replacement native executor.
            actions = np.asarray(assigned)-env.uav_positions if t==0 else np.zeros((6,3))
            env.step({a:actions[i] for i,a in enumerate(env.agents)})
        return {"steps":500,"target_permutation":list(range(6)),"targets_xyz":assigned,
                "initial_positions_xyz":initial,"final_max_distance_to_target_m":0.,
                "coverage_backhauled_mean_all":.4,
                "series":{"coverage_backhauled":[.4]*500},
                "association_changes_per_step":[0]*500,"backhaul_losses_per_step":[0]*500}
    planner.closed_loop_execute = execute
    def compute_menu(world, area_size, budget):
        assert area_size==5000 and budget==3000
        env = host.make_host(world, area_size)
        xyz = raw()["positions_xyz"]
        # Simulate two searches and the one separate metadata read; source call
        # plumbing is tested without paying 6001 real native static queries.
        for _ in range(5):
            host.static_evaluate(env, xyz, allow_a2a=True)
        planner.assign_targets(env.uav_positions, np.asarray(xyz))
        return {"positions_xyz":xyz, "m_permutation":list(range(6)),
                "initial_positions_xyz":[[10.+i,20.,100.] for i in range(6)],
                "static":{"evaluations":[2,2]}}
    return host, planner, SimpleNamespace(compute_menu=compute_menu)


def test_mock_collection_counts_and_full_reverse_identity(tmp_path):
    s = store(tmp_path)
    host, planner, menus = fake_modules()
    old_reset, old_static = host.CoupledRelayHost.reset, planner.static_evaluate
    runtime = NativeRuntime(s, host, planner, menus)
    try:
        with runtime.instrument():
            prepared = runtime.prepare_world({"block":1,"split":"train","offset":0,"world":c.BASES[0]})
            assert s.bill.delta["native_step_calls"] == 0 and s.bill.delta["static_evaluation_calls"] == 0
            runtime.collect_world(prepared)
        assert host.CoupledRelayHost.reset is old_reset and planner.static_evaluate is old_static
        assert s.bill.delta["candidate_episodes_completed"] == 8
        assert s.bill.delta["correctness_episodes_completed"] == 8
        assert s.bill.delta["native_step_calls"] == s.bill.delta["native_steps_completed"] == 8000
        assert s.bill.delta["static_evaluation_calls"] == 9
        assert s.bill.delta["matching_calls"] == 8
        # Two hosts: ctor + preparation reset + label reset + sixteen source executor resets.
        assert s.bill.delta["reset_calls"] == 20
        assert not list((s.output / "raw/audit").rglob("*.gz"))
        labels = json.loads((s.output / f"worlds/b1/train/{c.BASES[0]}/labels.json").read_bytes())
        assert labels["Q"] == [.4]*8 and labels["soft_targets"] == [.125]*8
    finally:
        s.close()


def test_mock_test_world_compute_menu_metadata_count_and_no_progress_scores(tmp_path):
    s = store(tmp_path)
    runtime = NativeRuntime(s, *fake_modules())
    try:
        with runtime.instrument():
            prepared = runtime.prepare_world({"block":1,"split":"test","offset":10000,"world":c.BASES[0]+10000})
            runtime.collect_world(prepared)
        assert s.bill.delta["native_step_calls"] == 4500
        assert s.bill.delta["static_evaluation_calls"] == 14
        assert s.bill.delta["planner_menus_completed"] == s.bill.delta["planner_episodes_completed"] == 1
        progress = (s.output/"progress.json").read_text()
        assert '"Q"' not in progress and "coverage" not in progress
    finally:
        s.close()


def test_mock_step_failure_is_charged_preserves_request_and_restores_wrappers(tmp_path):
    s = store(tmp_path)
    host, planner, menus = fake_modules()
    original = FakeEnv.step
    def fail(env, actions):
        raise RuntimeError("pure fixture native-call failure")
    FakeEnv.step = fail
    runtime = NativeRuntime(s, host, planner, menus)
    try:
        with pytest.raises(RuntimeError, match="pure fixture"):
            with runtime.instrument():
                prepared = runtime.prepare_world({"block":1,"split":"train","offset":3,"world":c.BASES[0]+3})
                runtime.collect_world(prepared)
        assert FakeEnv.step is fail
        assert s.bill.delta["native_step_calls"] == 1 and s.bill.delta["native_steps_completed"] == 0
        trace = next((s.output/"raw").rglob("*.gz"))
        assert list(read_trace(trace))[-1]["kind"] == "step_request"
        assert json.loads((s.output/"manifest.jsonl").read_text().splitlines()[-1])["status"] == "partial"
    finally:
        FakeEnv.step = original
        s.close()


def test_launcher_only_directory_is_allowed_but_scientific_reuse_refused(tmp_path):
    target = tmp_path / "launcher"
    target.mkdir()
    (target / "launch-manifest.json").write_text("{}")
    (target / "stdout.log").write_text("")
    (target / ".hmasd-launch-fixture.tmp").write_text("{}")
    s = Store(target, Bill(ledger(tmp_path), target))
    s.close()
    with pytest.raises(FileExistsError):
        Store(target, Bill(ledger(tmp_path), target))


def main_fixture(tmp_path, monkeypatch, validator):
    """Mock the admission and every native/codec surface; no real native import."""
    import sys
    from experiments.candidates.typed_joint_skill_decision import run_b01_native as runner
    from scripts import hmasd_admission
    root = Path(runner.__file__).resolve().parents[3]
    output = tmp_path / "admitted-output"
    output.mkdir()
    sha, command = "a"*40, "b"*64
    spec = {"output_root":str(output),"source_root":str(root)}
    monkeypatch.setenv(hmasd_admission.ENVIRONMENT_KEY, json.dumps(spec))
    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **kw: {"sha":sha,"command_sha256":command})
    (output/"launch-manifest.json").write_bytes(c.encode_json({**spec,"sha":sha,"direction":c.DIRECTION,"command_sha256":command}))
    budget = tmp_path/"bill.json"
    budget.write_bytes(c.encode_json(ledger(tmp_path)))
    model_root = tmp_path/"model"
    model_root.mkdir()
    token = model_root/"fixture.txt"
    token.write_text("fixture")
    assets = tmp_path/"assets.json"
    assets.write_bytes(c.encode_json({"model_root":str(model_root),"files":{"fixture.txt":{"bytes":7,"sha256":hash_file(token)}}}))
    host, planner, menus = fake_modules()
    planner.build_candidates = lambda *a, **kw: [raw()]
    monkeypatch.setitem(sys.modules, "experiments.candidates.coupled_host_joint_skills_stage1",
                        SimpleNamespace(host=host,planner=planner,menus=menus))
    monkeypatch.setitem(sys.modules, "experiments.candidates.typed_joint_skill_decision.codec",
                        SimpleNamespace(validate_native_features=validator))
    monkeypatch.setattr(runner, "verify_sources", lambda root: None)
    # This mock launch uses a tiny fixture snapshot for disk accounting, rather
    # than charging the unrelated live repository's accumulated research outputs.
    monkeypatch.setattr(runner, "Bill", lambda value, out, source_root: Bill(value,out,source_root=tmp_path))
    # Artifact-byte binding itself is separately tested below. This fixture replaces
    # it explicitly instead of constructing/copying the real 842MB model object.
    monkeypatch.setattr(runner, "verify_assets", lambda path, sha: (model_root, runner.load_bound_json(path, sha)))
    monkeypatch.setattr(c, "worlds", lambda: iter([
        {"block":1,"split":"train","offset":i,"world":c.BASES[0]+i} for i in range(2)]))
    args = ["--seed","0","--launch-sha",sha,"--out-dir",str(output),
            "--budget-ledger",str(budget),"--budget-ledger-sha256",hash_file(budget),
            "--asset-manifest",str(assets),"--asset-manifest-sha256",hash_file(assets)]
    return runner, args, output, host


def test_mock_two_pass_validates_every_world_before_any_static_or_step(tmp_path, monkeypatch):
    validations = []
    def validate(features, model_root):
        validations.append(c.digest(features))
        return {"feature_sha256":c.digest(features),"full_tokens":10}
    runner, args, output, host = main_fixture(tmp_path,monkeypatch,validate)
    static = host.static_evaluate
    def require_all_validation(*a, **kw):
        assert len(validations) == 2
        assert len(list((output/"prepared").rglob("features.json"))) == 2
        return static(*a, **kw)
    host.static_evaluate = require_all_validation
    assert runner.main(args) == 0
    summary = json.loads((output/"summary.json").read_bytes())
    assert summary["status"] == "complete"
    assert summary["bill"]["delta_counters"]["worlds_completed"] == 2
    assert summary["bill"]["delta_counters"]["native_step_calls"] == 2000
    assert summary["learning"] == {"fits":0,"optimizer_updates":0,"model_forwards":0}


def test_mock_codec_refusal_keeps_exact_input_and_generates_zero_labels(tmp_path, monkeypatch):
    def refused(features, model_root):
        raise ValueError('{"reason":"fixture truncation","full_tokens":4097}')
    runner, args, output, host = main_fixture(tmp_path,monkeypatch,refused)
    with pytest.raises(ValueError,match="fixture truncation"):
        runner.main(args)
    exact = next((output/"prepared").rglob("features.json"))
    rejection = next((output/"prepared").rglob("codec_refusal.json"))
    assert json.loads(rejection.read_bytes())["feature_sha256"] == c.digest(json.loads(exact.read_bytes()))
    failed = json.loads((output/"failure.json").read_bytes())
    assert failed["status"] == "failed_partial"
    assert failed["bill"]["delta_counters"]["native_step_calls"] == 0
    assert failed["bill"]["delta_counters"]["static_evaluation_calls"] == 0
    assert not (output/"worlds").exists()


def test_bound_external_bytes_refuse_mutation_before_parsing(tmp_path):
    from experiments.candidates.typed_joint_skill_decision.run_b01_native import load_bound_json
    path = tmp_path / "ledger.json"
    path.write_bytes(c.encode_json({"counter":0}))
    sha = hash_file(path)
    assert load_bound_json(path,sha) == {"counter":0}
    path.write_bytes(c.encode_json({"counter":1}))
    with pytest.raises(ValueError,match="external input changed"):
        load_bound_json(path,sha)


def test_asset_repository_revision_required_objects_and_byte_hash(tmp_path,monkeypatch):
    from experiments.candidates.typed_joint_skill_decision.run_b01_native import verify_assets
    path = tmp_path / "asset-manifest.json"
    base = {"schema":1,"repository":c.ASSET_REPOSITORY,"revision":c.ASSET_REVISION,
            "model_root":str(tmp_path),"files":{}}
    path.write_bytes(c.encode_json({**base,"revision":"wrong"}))
    with pytest.raises(ValueError,match="repository/revision"):
        verify_assets(path,hash_file(path))
    path.write_bytes(c.encode_json(base))
    with pytest.raises(ValueError,match="omits or changes pinned object"):
        verify_assets(path,hash_file(path))
    # Verify the full byte/hash/path rule with a tiny explicitly mocked required
    # object set, rather than downloading/loading the real model.
    fixture = tmp_path / "fixture.txt"
    fixture.write_text("fixture")
    identity = {"sha256":hash_file(fixture),"bytes":7}
    monkeypatch.setattr(c,"ASSET_FILES",{"fixture.txt":(identity["sha256"],7)})
    path.write_bytes(c.encode_json({**base,"files":{"fixture.txt":identity}}))
    assert verify_assets(path,hash_file(path))[0] == tmp_path
    fixture.write_text("changed")
    with pytest.raises(ValueError,match="pinned asset drift"):
        verify_assets(path,hash_file(path))


def test_disk_refresh_is_bounded_and_current_file_blocks_are_charged(tmp_path,monkeypatch):
    from experiments.candidates.typed_joint_skill_decision import data
    original = data.allocated_bytes
    calls = []
    def observed(roots):
        calls.append(roots)
        return original(roots)
    monkeypatch.setattr(data,"allocated_bytes",observed)
    monkeypatch.setattr(data.time,"perf_counter",lambda:100.)
    s = store(tmp_path)
    try:
        for _ in range(100):
            s.bill.check(disk=True,pending_bytes=100)
        assert len(calls) == 1
        s.write_json("record.json",{"fixture":"abc"})
        assert s.bill.disk_other + s.bill.disk_own == original([tmp_path])
    finally:
        s.close()
