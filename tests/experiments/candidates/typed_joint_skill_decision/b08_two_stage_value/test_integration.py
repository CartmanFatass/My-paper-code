"""Mock orchestration and prescribed arrays only; no native or model physics."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.typed_joint_skill_decision.b08_two_stage_value import (
    contract as c, evidence as e, execution as ex, reader, run,
)


class Budget:
    def __init__(self, *args, wall_started=0., **kwargs):
        self.wall_started, self.stage, self.case = wall_started, "initial", None

    def check(self, **kwargs):
        return {"stage": self.stage, "cpu_seconds": 0.}

    def elapsed_cpu(self):
        return 0.


@pytest.mark.parametrize("reward", [np.float64(.137), np.float64(0.)])
def test_native_scalar_reader_reconstructs_ordered_adapter_bits(monkeypatch, reward):
    """Every native formula is mocked; reject one ULP and signed-zero edits."""
    connections = np.zeros((8, 50), bool)
    sinr, peers = np.zeros((8, 50)), np.zeros((8, 8))
    monkeypatch.setattr(reader.uav_radio, "free_space_user_path_loss", lambda *a: None)
    monkeypatch.setattr(reader.uav_radio, "user_sinr_from_path_loss", lambda *a, **k: sinr.copy())
    monkeypatch.setattr(reader.uav_radio, "greedy_connection_assignment", lambda *a: connections.copy())
    monkeypatch.setattr(reader.MultiUAVEnv, "_compute_uav_path_loss_matrix", lambda v: None)
    monkeypatch.setattr(reader.MultiUAVEnv, "_compute_uav_uav_sinr_matrix", lambda v: peers.copy())
    monkeypatch.setattr(reader.MultiUAVEnv, "_get_observation_vectorized", lambda *a: {"obs": np.zeros(104, np.float32)})
    monkeypatch.setattr(reader, "_public_state", lambda *a: np.zeros(133, np.float32))

    def compute_reward(view):
        view.reward_info = dict(zip(ex.COMPONENTS, [np.float64(.1), np.float64(.2), np.float64(.03), reward]))
        return reward

    monkeypatch.setattr(reader.UAVBaseStationEnv, "_compute_reward", compute_reward)
    view = SimpleNamespace(_local_user_entries=lambda i: ([], None), _local_uav_entries=lambda i: ([], None))
    scalar = float(sum(reward / 8 for _ in range(8)) / 8)
    raw = dict(positions=np.zeros((2, 8, 3)), users=np.zeros((50, 2)), mask=np.asarray([255]),
               sinr=np.repeat(sinr[None], 2, axis=0), connections=np.repeat(connections[None], 2, axis=0),
               peer_sinr=np.repeat(peers[None], 2, axis=0), states=np.zeros((2, 133), np.float32),
               observations=np.zeros((2, 8, 104), np.float32), visible_users=np.zeros((2, 8), np.int64),
               visible_peers=np.zeros((2, 8), np.int64), components=np.asarray([[.1, .2, .03, reward]]),
               scalar_reward=np.asarray([scalar], np.float64))
    reader._verify_native_snapshot(raw, 1, view)
    raw["scalar_reward"][0] = np.nextafter(scalar, np.inf) if scalar else -0.
    with pytest.raises(ValueError, match="scalar bits"):
        reader._verify_native_snapshot(raw, 1, view)


def test_collector_one_copy_outer_and_identity_reject_changed_bytes(tmp_path):
    collector = e.Collector(tmp_path, "mock", Budget())

    def segment(start, end):
        n = end - start
        arrays = dict(positions=np.zeros((n + 1, 8, 3)), controller_estimates=np.zeros((n + 1, 8, 3)),
                      actions=np.zeros((n, 8, 3), np.float32), masks=np.zeros(n, np.int64),
                      reward_components=np.zeros((n, 4)), reports=np.zeros((n // 10, 133), np.float32),
                      report_times=np.arange(start, end, 10, dtype=np.int64))
        return dict(arrays=arrays, summary={"start_t": start, "end_t": end},
                    decisions=[{"t": t} for t in range(start, end)], certificate={"mock": True})

    left, right = segment(40, 120), segment(120, 500)
    collector.segment_sink("a2/first/stay/prefix", left)
    collector.segment_sink("a2/first/stay/suffix", right)
    arrays = {k: np.concatenate((left["arrays"][k], right["arrays"][k][1:]
                                if k in ("positions", "controller_estimates") else right["arrays"][k]))
              for k in left["arrays"]}
    decisions = deepcopy(left["decisions"] + right["decisions"])
    decisions[80]["predicted_temporal_selection"] = {"selected_branch": "stay"}
    outer = dict(arrays=arrays, decisions=decisions,
                 summary={"inner_selection": {"selected_branch": "stay"}, "identity": {"tree": "a2"}})
    collector.branch_sink("a2/first/stay/outer", outer)
    catalog = {"segments": list(collector.segments.values())}
    loaded = e.load_branch(tmp_path, catalog, collector.branches[0])
    reader._compare_payload(loaded, outer, "synthetic outer")
    assert len(list(tmp_path.rglob("*.npz"))) == 2
    with pytest.raises(ValueError, match="duplicate paid model segment"):
        collector.segment_sink("a2/first/stay/prefix", left)
    raw_path = tmp_path / collector.segments["a2/first/stay/prefix"]["raw"]["path"]
    raw_path.write_bytes(raw_path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="artifact bytes differ"):
        e.load_branch(tmp_path, catalog, collector.branches[0])


def test_execute_case_preserves_first_failure_prefix_without_retry(monkeypatch, tmp_path):
    calls = []
    world = {"world_id": 1, "runtime_seed": 3, "user_positions": np.zeros((50, 2)).tolist()}
    native = SimpleNamespace(uav_positions=np.zeros((8, 3)), sinr_matrix=np.zeros((8, 50)),
        connections=np.zeros((8, 50), bool), uav_sinr_matrix=np.zeros((8, 8)),
        _local_user_entries=lambda i: ([], None), _local_uav_entries=lambda i: ([], None),
        set_transmitter_mask=lambda mask: calls.append("mask"))

    class Environment:
        def __init__(self):
            self.env, self.steps = SimpleNamespace(env=native), 0

        def reset(self, **kwargs):
            calls.append("reset")
            return np.zeros((8, 104), np.float32), {"state": np.zeros(133, np.float32)}

        def step(self, command):
            self.steps += 1
            calls.append("step")
            if self.steps == 2:
                raise RuntimeError("prescribed native failure")
            return np.zeros((8, 104), np.float32), 0., False, False, {
                "next_state": np.zeros(133, np.float32),
                "reward_components": {"reward_info": {name: 0. for name in ex.COMPONENTS}}}

        def close(self):
            calls.append("close")

    class Policy:
        plans, selections, banks = {}, {}, {}

        def __init__(self, *args, **kwargs):
            pass

        def select(self, t, state, mask):
            return np.zeros((8, 3), np.float32), mask, {"t": t}

    monkeypatch.setattr(ex, "BudgetedProgram", Policy)
    monkeypatch.setattr(c, "scene", lambda record: None)
    monkeypatch.setattr(ex, "make_env", lambda *a: Environment())
    with pytest.raises(RuntimeError, match="prescribed native failure"):
        ex.execute_case(tmp_path, world, "A2", "train", Budget())
    row = json.loads((tmp_path / "raw/train/w1/A2/case.json").read_text())
    assert row["complete"] is False and row["steps"] == 1 and row["decisions_attempted"] == 2
    assert calls == ["reset", "mask", "step", "step", "close"]
    assert e.load_arrays(e.checked_path(tmp_path, row["raw"]))["positions"].shape == (2, 8, 3)
    assert len(e.read_gzip(e.checked_path(tmp_path, row["decisions"]))) == 2


def setup_orchestration(monkeypatch, tmp_path, fail_stage=None):
    """Replace every effect producer; keep real orchestration/persistence."""
    events = []
    monkeypatch.setattr(c, "TRAIN_IDS", (1, 2))
    monkeypatch.setattr(c, "FINAL_IDS", (3,))
    worlds = [{"world_id": w} for w in (1, 2, 3)]
    fits = [{"fit_id": i} for i in range(3)]
    monkeypatch.setattr(c, "validate_input", lambda *a: {"mock": True})
    monkeypatch.setattr(c, "load_world_input", lambda: {"worlds": worlds, "fits": fits})
    monkeypatch.setattr(c, "runtime", lambda: {"mock": True})
    monkeypatch.setattr(e, "Budget", Budget)

    def execute(out, world, arm, kind, budget, **kwargs):
        events.append((kind, world["world_id"], arm))
        if kind != "train":
            seal = json.loads((Path(out) / "seal.json").read_text())
            assert len(seal["finals"]) == 3 and sum(ev[0] == "fit_reader" for ev in events) == 3
        return {"kind": kind, "world_id": world["world_id"], "arm": arm}

    def case_reader(out, row, world, budget, **kwargs):
        events.append(("case_reader", row["kind"], row["arm"]))
        if budget.stage == fail_stage:
            raise RuntimeError("prescribed reader stop")
        return dict(row)

    def fit_one(out, bank, labels, fit, budget, source, binding):
        events.append(("fit", fit["fit_id"]))
        return {**fit, "final": {"fit_id": fit["fit_id"]}}

    def fit_reader(out, fit, bank, labels, budget, **kwargs):
        events.append(("fit_reader", fit["fit_id"]))
        assert kwargs == {"source_sha": "published", "bank_binding": {"mock_bank": True}}
        if budget.stage == fail_stage:
            raise RuntimeError("prescribed reader stop")
        return {"fit_id": fit["fit_id"]}

    def load(out, checkpoint):
        assert (Path(out) / "seal.json").exists()
        return object(), {"mock_state": checkpoint["fit_id"]}

    def child(out, world, arm, checkpoint, *args):
        row = execute(out, world, arm, "audit", None)
        path = Path(out) / f"raw/audit/w{world['world_id']}/{arm}/cold-process.json"
        e.write_json(path, {"status": "complete", "case": row, "model_restore_cpu_seconds": 0.,
                            "resources": {"self_cpu_seconds": 0., "finished_children_cpu_seconds": 0.}})

    class Process:
        def __init__(self, target, args, **kwargs):
            self.target, self.args, self.exitcode = target, args, None

        def start(self):
            self.target(*self.args)
            self.exitcode = 0

        def is_alive(self):
            return False

        def close(self):
            pass

    monkeypatch.setattr(ex, "execute_case", execute)
    monkeypatch.setattr(ex, "bank_features", lambda *a: ({}, None, {"mock_bank": True}))
    monkeypatch.setattr(ex, "fit_one", fit_one)
    monkeypatch.setattr(ex, "load_model", load)
    monkeypatch.setattr(ex, "audit_child", child)
    monkeypatch.setattr(ex.multiprocessing, "get_context", lambda name: SimpleNamespace(Process=Process))
    monkeypatch.setattr(reader, "verify_case", case_reader)
    monkeypatch.setattr(reader, "verify_fit", fit_reader)
    monkeypatch.setattr(reader, "verify_cold_identity", lambda *a: events.append(("cold_identity",)))
    monkeypatch.setattr(reader, "complete_reading", lambda *a: {"status": "complete", "cost_accounts": {}})
    return events


def test_study_seals_all_fits_before_fresh_and_does_exact_declared_cold_order(monkeypatch, tmp_path):
    events = setup_orchestration(monkeypatch, tmp_path)
    result = ex.run_study(tmp_path, "published", {"command_sha256": "command"}, Path("mock"), "hash", 0.)
    assert result["status"] == "complete"
    assert [ev for ev in events if ev[0] == "train"] == [("train", 1, "A2"), ("train", 2, "A2")]
    assert [ev[2] for ev in events if ev[0] == "final"] == list(c.ARMS)
    assert [ev[2] for ev in events if ev[0] == "audit"] == list(c.ARMS)
    assert sum(ev[0] == "fit" for ev in events) == 3
    assert sum(ev[0] == "cold_identity" for ev in events) == 7
    assert len(result["case_readings"]) == 16
    with pytest.raises(FileExistsError, match="no implicit replay"):
        ex.run_study(tmp_path, "published", {"command_sha256": "command"}, Path("mock"), "hash", 0.)


@pytest.mark.parametrize("stage, forbidden", [
    ("acquisition_reader", "fit"), ("functional_training_reader", "final"),
    ("fresh_reader", "audit"), ("audit_reader", "cold_identity"),
])
def test_first_reader_failure_stops_whole_purchase_and_preserves_summary(monkeypatch, tmp_path, stage, forbidden):
    events = setup_orchestration(monkeypatch, tmp_path, fail_stage=stage)
    with pytest.raises(RuntimeError, match="prescribed reader stop"):
        ex.run_study(tmp_path, "published", {"command_sha256": "command"}, Path("mock"), "hash", 0.)
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["status"] == "failed" and summary["stage"] == stage
    assert "prescribed reader stop" in summary["traceback"]
    assert not any(ev[0] == forbidden for ev in events)
    assert not (tmp_path / "reading.json").exists()


def test_budget_includes_finished_children_offset_and_exact_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(e, "resources", lambda: {"self_cpu_seconds": 4., "finished_children_cpu_seconds": 5.})
    monkeypatch.setattr(c, "CPU_LIMIT_SECONDS", 10.)
    budget = e.Budget  # Real type is restored outside the orchestration fixture.
    instance = budget(tmp_path / "out", tmp_path / "source", cpu_offset=1.)
    assert instance.elapsed_cpu() == 10.
    with pytest.raises(RuntimeError, match="fixed result-chain"):
        instance.check()
    assert json.loads((tmp_path / "out/progress.json").read_text())["cpu_seconds"] == 10.


def test_runner_requires_native_admission_before_any_output(monkeypatch, tmp_path):
    from scripts import hmasd_admission
    calls = []

    def refusal(filename, *, direction):
        calls.append((Path(filename).name, direction))
        raise RuntimeError("prescribed mock admission refusal")

    monkeypatch.setattr(hmasd_admission, "require_admission", refusal)
    with pytest.raises(RuntimeError, match="mock admission refusal"):
        run.main(["--out", str(tmp_path / "result"), "--seed", str(c.SEED), "--launch-sha", "published",
                  "--input-manifest", "mock.json", "--input-manifest-sha256", "hash"])
    assert calls == [("run.py", c.DIRECTION)]
    assert not (tmp_path / "result").exists()


def test_manifest_binds_worlds_runtime_and_all_declared_source_bytes(monkeypatch, tmp_path):
    source, world_file = tmp_path / "own.py", tmp_path / "worlds.json"
    source.write_text("# synthetic executable binding\n")
    world_file.write_text('{"mock":true}\n')
    monkeypatch.setattr(c, "REPO", tmp_path)
    monkeypatch.setattr(c, "WORLD_PATH", world_file)
    monkeypatch.setattr(c, "OWN_PATHS", ("own.py", "worlds.json"))
    monkeypatch.setattr(c, "runtime", lambda: {"mock_runtime": True})
    monkeypatch.setattr(c, "load_world_input", lambda: {"mock": True})
    # binding's default argument is the original root; use an explicit root
    # exactly as the actual declaration's original root would supply.
    actual_binding = c.binding
    monkeypatch.setattr(c, "binding", lambda path, base=tmp_path: actual_binding(path, base))
    manifest = {"scope": c.fixed_scope(), "runtime": c.runtime(), "frozen_sources": {},
                "sources": {p.name: c.binding(p) for p in (source, world_file)},
                "world_input": c.binding(world_file)}
    path = tmp_path / "input.json"
    e.write_json(path, manifest)
    digest = c.sha256(path)
    assert c.validate_input(path, digest) == manifest
    source.write_text("# changed executable binding\n")
    with pytest.raises(ValueError, match="source/input bytes differ"):
        c.validate_input(path, digest)
    with pytest.raises(ValueError, match="input-manifest hash"):
        c.validate_input(path, "0" * 64)


@pytest.mark.parametrize("changed", ["source_sha", "bank", "world_ids", "fit_index"])
def test_fit_reader_rejects_mixed_identity_before_forward(monkeypatch, tmp_path, changed):
    monkeypatch.setattr(c, "addressed_seed", lambda label, stream: stream)
    fit = {"fit_id": 0, "label": c.FIT_LABELS[0], "init_seed": 10, "permutation_seed": 11}
    checkpoints = [{"update": update, "fit_index": 0, "init_seed": 10, "permutation_seed": 11,
        "fit_id": {"init_seed": 10, "permutation_seed": 11}, "source_sha": "frozen", "bank": {"bank": 1},
        "world_ids": list(c.TRAIN_IDS), "epochs": 256, "batch_size": 16, "scheduled_updates": 2048}
        for update in c.CHECKPOINTS]
    fit.update(checkpoints=checkpoints, final=deepcopy(checkpoints[-1]))
    fit["checkpoints"][0][changed] = "wrong"
    monkeypatch.setattr(reader.functional, "verify", lambda *a: pytest.fail("forward must not run"))
    with pytest.raises(ValueError, match="checkpoint source/bank/world/RNG"):
        reader.verify_fit(tmp_path, fit, {}, None, Budget(), source_sha="frozen", bank_binding={"bank": 1})


def test_complete_reader_refuses_repeated_case_read_identity(tmp_path):
    def case(kind, world_id, arm):
        return {"kind": kind, "world_id": world_id, "arm": arm}

    acquisition = [case("train", world, "A2") for world in c.TRAIN_IDS]
    final = [case("final", world, c.ARMS[(i + offset) % 7])
             for i, world in enumerate(c.FINAL_IDS) for offset in range(7)]
    audits = [case("audit", c.FINAL_IDS[0], arm) for arm in c.ARMS]
    readings = deepcopy(acquisition + final + audits)
    readings[-1] = deepcopy(readings[-2])
    summary = {"acquisition": acquisition, "final": final, "audits": audits, "case_readings": readings,
               "fits": [{"fit_id": i} for i in range(3)], "functional_readings": [{"fit_id": i} for i in range(3)]}
    with pytest.raises(ValueError, match="not every paid case"):
        reader.complete_reading(tmp_path, summary, Budget())
