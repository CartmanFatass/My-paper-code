"""Admission ordering, source/input refusal and saved-Adam corruption checks."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import FROZEN as OLD
from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import CountStudent, make_optimizer, checkpoint
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets import run
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.assets import checked_path
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.fit_reading import _optimizer
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.targets import soft_cross_entropy


def test_hash_binding_and_path_escape(tmp_path):
    root = tmp_path / "inputs"; root.mkdir()
    path = root / "source.bin"; path.write_bytes(b"fixed source")
    binding = dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert checked_path(root, "source.bin", binding) == path
    path.write_bytes(b"other source")
    with pytest.raises(ValueError): checked_path(root, "source.bin", binding)
    with pytest.raises(ValueError): checked_path(root, "../source.bin", binding)


def test_missing_admission_has_no_output_or_worker_effect(tmp_path, monkeypatch):
    import scripts.hmasd_admission as admission
    def refuse(*args, **kwargs): raise RuntimeError("missing admission")
    monkeypatch.setattr(admission, "require_admission", refuse)
    out = tmp_path / "forbidden"
    with pytest.raises(RuntimeError, match="missing admission"):
        run.main(["--out", str(out), "--launch-sha", "abc", "--seed", "29711000"])
    assert not out.exists()


def test_wrong_sha_has_no_output(tmp_path, monkeypatch):
    import scripts.hmasd_admission as admission
    monkeypatch.setattr(admission, "require_admission", lambda *a, **k: {"sha": "other"})
    out = tmp_path / "forbidden"
    with pytest.raises(RuntimeError, match="source differs"):
        run.main(["--out", str(out), "--launch-sha", "abc", "--seed", "29711000"])
    assert not out.exists()


def test_mocked_admission_worker_then_complete_reader(tmp_path, monkeypatch):
    import scripts.hmasd_admission as admission
    from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets import study, read
    events = []
    def admit(*args, **kwargs): events.append("admission"); return {"sha": "abc"}
    def worker(out, sha, **kwargs):
        assert events[-1] == "deterministic" and kwargs["admission"] == {"sha": "abc"}
        events.append("worker"); out.mkdir(); return {"state": "COMPLETE"}
    def reader(out, repo):
        assert events[-1] == "worker"; events.append("reader"); return {"status": "VERIFIED"}
    monkeypatch.setattr(admission, "require_admission", admit)
    monkeypatch.setattr(torch, "set_num_threads", lambda n: events.append("threads"))
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: events.append("interop"))
    monkeypatch.setattr(torch, "use_deterministic_algorithms", lambda b: events.append("deterministic"))
    monkeypatch.setattr(study, "run_batch", worker); monkeypatch.setattr(read, "read_result", reader)
    out = tmp_path / "admitted"
    result = run.main(["--out", str(out), "--launch-sha", "abc", "--seed", "29711000"])
    assert result["state"] == "COMPLETE" and events == ["admission", "threads", "interop", "deterministic", "worker", "reader"]
    assert (out / "reading.json").is_file()


def test_exclusive_reader_reservation_and_loser_cannot_publish(tmp_path, monkeypatch):
    from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets import read
    barrier = Barrier(2)
    def enter():
        barrier.wait()
        try:
            read._reserve_reader(tmp_path)
        except FileExistsError:
            return False
        return True
    with ThreadPoolExecutor(max_workers=2) as pool:
        left, right = pool.submit(enter), pool.submit(enter)
        assert sorted((left.result(), right.result())) == [False, True]
    marker = tmp_path / "reading-progress.json"
    before = marker.read_bytes()
    assert json.loads(before)["reservation"] == "exclusive-reader"
    def forbidden(*args, **kwargs): raise AssertionError("loser began reconstruction")
    monkeypatch.setattr(read, "verify_inputs", forbidden)
    with pytest.raises(FileExistsError):
        read.read_result(tmp_path, tmp_path)
    assert marker.read_bytes() == before and not (tmp_path / "reading.json").exists()


def test_archive_failure_keeps_completed_and_interrupted_cost_prefix(monkeypatch, tmp_path):
    from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets import read
    class C:
        def __init__(self, n):
            self.counters = dict(requests=0, misses=0, trajectories=0, model_ticks=0, candidate_links=0, setup_links=0)
        def query(self):
            for key, value in dict(requests=1, misses=1, trajectories=27, model_ticks=108, candidate_links=108, setup_links=1).items():
                self.counters[key] += value
    class Helper:
        def __init__(self, n):
            self.counters = dict(requests=0, misses=0, helper_calls=0, helper_setup_links=0, helper_extreme_links=0)
        def query(self):
            for key, value in dict(requests=1, misses=1, helper_calls=1, helper_setup_links=1, helper_extreme_links=2).items():
                self.counters[key] += value
    expected_c = dict(requests=1, misses=1, trajectories=27, model_ticks=108, candidate_links=108, setup_links=1)
    manifest = {"rows": [dict(id=name, phase=0, raw={"path": name}, expert_counts=expected_c) for name in ("first", "second")]}
    monkeypatch.setattr(read, "MemoC", C); monkeypatch.setattr(read, "FeatureMemo", Helper)
    monkeypatch.setattr(read, "checked_path", lambda *args: tmp_path)
    monkeypatch.setattr(read, "_load_raw", lambda *args: {})
    monkeypatch.setattr(read, "check_episode", lambda *args: dict(saved_native_steps=1, decision_rows=1))
    def episode(raw, dataset, targets, parent, counts, teachers, helpers, offset, scores):
        teachers[0].query(); helpers[0].query()
        counts["C_requests"] += 1; counts["helper_requests"] += 1
        if offset == 1:
            raise RuntimeError("synthetic second-episode mismatch")
        return offset + 1, 0., 0.
    monkeypatch.setattr(read, "_archive_episode", episode)
    work, record = {}, {}
    counts = dict(saved_files=0, saved_ticks=0, decision_rows=0, archive_target_rows=0, C_requests=0, helper_requests=0)
    with pytest.raises(RuntimeError, match="second-episode"):
        read.check_archive(manifest, None, None, None, counts, lambda value: None, work=work, record=record)
    assert counts["saved_files"] == 1 and record["records"][0]["id"] == "first"
    assert work["C_costs"] == {key: 2 * value for key, value in expected_c.items()}
    assert work["helper_costs"]["helper_setup_links"] == 2 and work["helper_costs"]["helper_extreme_links"] == 4
    assert work["scopes_started"] == 2 and work["scopes_completed"] == work["scopes_failed"] == 1
    assert work["last_scope"]["id"] == "second" and work["last_scope"]["status"] == "FAILED"
    assert work["inflight"] is None


@pytest.mark.parametrize("change", [None, "steps", "moment", "count_moment", "ordering", "lr"])
def test_saved_adam_contract(change):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(8111); actor = CountStudent()
    optimizer = make_optimizer(actor, OLD)
    x = torch.linspace(-1, 1, 228).reshape(2, 114)
    loss = soft_cross_entropy(actor(x, torch.full((2,), 5, dtype=torch.int64)), torch.full((2, 27), 1 / 27, dtype=torch.float64))
    loss.backward(); optimizer.step()
    saved = checkpoint(actor, optimizer)
    if change == "steps": saved["optimizer"]["state"][0]["step"] += .5
    elif change == "moment": saved["optimizer"]["state"][1]["exp_avg_sq"].fill_(-1)
    elif change == "count_moment": saved["optimizer"]["state"][0]["exp_avg"].fill_(1)
    elif change == "ordering": saved["optimizer"]["param_groups"][0]["params"].reverse()
    elif change == "lr": saved["optimizer"]["param_groups"][0]["lr"] = 1.
    if change is None:
        _optimizer(saved, actor, 1)
    else:
        with pytest.raises(ValueError): _optimizer(saved, actor, 1)
