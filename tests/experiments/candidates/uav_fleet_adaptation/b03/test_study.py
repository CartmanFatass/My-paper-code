"""Complete synthetic recurrence, retained provenance, and failed-exposure checks."""
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.read import read_batch as read_original
from experiments.candidates.uav_fleet_adaptation.b02.study import run_batch as run_original
from experiments.candidates.uav_fleet_adaptation.b03.contract import FROZEN, NEW_ARMS
from experiments.candidates.uav_fleet_adaptation.b03.read import read_batch
from experiments.candidates.uav_fleet_adaptation.b03.retained import BINDING
from experiments.candidates.uav_fleet_adaptation.b03.study import run_batch
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from tests.experiments.candidates.uav_fleet_adaptation.b02.test_study import SMALL, Synthetic


NEW = replace(FROZEN, training_worlds=((121, 122), (123,), (124,)), evaluation_worlds=SMALL.evaluation_worlds,
              init_seed=321, shuffle_root=322, sampling_root=SMALL.sampling_root,
              horizon=8, epochs=(1, 1, 1), batch_size=10)


@pytest.fixture(scope="module")
def retained(tmp_path_factory):
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    root = tmp_path_factory.mktemp("b03-old-synthetic") / "result"
    sha = "old-synthetic-fixture"
    admission = dict(schema_version=1, sha=sha, direction="uav_fleet_adaptation", command_sha256="fixture-command",
                     parent_pid=901, child_pid=902)
    batch = run_original(root, sha, protocol=SMALL, factory=Synthetic, admission=admission)
    write_json(root / "reading.json", read_original(root, permit_fixture=True))
    write_json(root / "launch-manifest.json", dict(
        schema_version=1, acceptance="accepted", sha=sha, direction="uav_fleet_adaptation",
        command_sha256=admission["command_sha256"], host_identity=batch["environment"]["host"],
        process=dict(pid=901, identity="fixture-supervisor"),
        runner_process=dict(pid=902, identity="fixture-worker"), output_root=str(root)))
    write_json(root / "process-exit.json", dict(
        schema_version=1, status="exited", termination="process_exit", exit_code=0,
        pid=902, process_identity="fixture-worker", supervisor_identity="fixture-supervisor"))
    binding = dict(launch_sha=sha, files={})
    for name in BINDING["files"]:
        identity = file_identity(root / name)
        binding["files"][name] = {key: identity[key] for key in ("bytes", "sha256")}
    yield root, binding, batch
    torch.set_num_threads(previous)


@pytest.fixture(scope="module")
def study(retained, tmp_path_factory):
    old_root, binding, old = retained
    out = tmp_path_factory.mktemp("b03-new-synthetic") / "result"
    result = run_batch(out, "new-synthetic-fixture", retained_out=old_root, protocol=NEW,
                       factory=Synthetic, fixture_binding=binding)
    return out, result, old


def test_production_envelope_and_admission_boundary(tmp_path):
    expected = FROZEN.expected()
    assert expected["native_steps"] == 98304 and expected["complete_episodes"] == 384
    assert expected["evaluation_episodes"] == 128 and expected["evaluation_native_steps"] == 32768
    assert expected["datasets"] == [40960, 61440, 81920]
    assert expected["optimizer_updates"] == 8000 and expected["sample_presentations"] == 4096000
    assert expected["full_C_requests"] == 81920 and expected["C7_requests"] == 0
    assert expected["helper_request_ceiling"] == 122880 and expected["neural_rollout_row_ceiling"] == 81920
    assert expected["retained_evaluation_episodes"] == 64 and expected["retained_native_steps"] == 16384
    with pytest.raises(ValueError, match="admitted"):
        run_batch(tmp_path / "native", "bad", retained_out=tmp_path / "old")
    with pytest.raises(ValueError, match="nonproduction"):
        run_batch(tmp_path / "injected", "bad", retained_out=tmp_path / "old", factory=Synthetic)
    assert not (tmp_path / "native").exists() and not (tmp_path / "injected").exists()


def test_complete_fresh_lineage_and_saved_only_mixed_reader(study, monkeypatch):
    out, result, old = study
    assert result["status"] == "COMPLETE" and result["actual_learning"]
    assert result["actual"]["native_steps"] == 96 and result["actual"]["complete_episodes"] == 12
    assert result["actual"]["optimizer_steps"] == 9 and result["actual"]["sample_presentations"] == 90
    assert result["actual"]["fit_started"] == 1
    assert [p["adam_step_values"][0] for p in result["phases"]] == [2, 5, 9]
    assert {r["arm"] for r in result["rows"] if r["kind"] == "evaluation"} == set(NEW_ARMS)
    assert len(result["retained"]["rows"]) == 4 and result["retained"]["new_native_steps"] == 0
    assert result["costs"]["full_C"]["requests"] == 40 and result["costs"]["C7"] == {}
    assert result["costs"]["neural"]["sampled_draws"] == 20
    assert result["assets"]["S0"]["state_sha256"] != old["assets"]["S0"]["state_sha256"]
    assert result["reading"]["recurrence"]["training_lineages_observed"] == 2
    assert result["reading"]["recurrence"]["previous_screens"] == old["reading"]["screens"]

    def forbidden(*args, **kwargs):
        raise AssertionError("saved-data reader made an undeclared scientific call")
    from experiments.candidates.uav_fleet_adaptation.b02 import controllers, model
    monkeypatch.setattr(controllers.original, "_power", forbidden)
    monkeypatch.setattr(controllers.MemoC, "query", forbidden)
    monkeypatch.setattr(model.Student, "forward", forbidden)
    monkeypatch.setattr(Synthetic, "step", forbidden)
    reading = read_batch(out, permit_fixture=True)
    assert reading["status"] == "VERIFIED" and reading["raw_files"] == 16
    assert reading["new_raw_files"] == 12 and reading["retained_raw_files"] == 4
    assert reading["native_ticks_verified"] == 96 and reading["retained_native_ticks_verified"] == 32
    assert reading["decisions_verified"] == 120 and reading["retained_decisions_verified"] == 40
    assert sum(row["provenance"] == "retained_B02" for row in reading["per_row"]) == 4
    assert not any(reading["reader_calls"].values())
    with pytest.raises(ValueError, match="fixed scientific"):
        read_batch(out)
    with pytest.raises(FileExistsError):
        run_batch(out, "fixture", retained_out=Path(result["retained"]["root"]),
                  protocol=NEW, factory=Synthetic, fixture_binding=result["retained"]["binding"])


def test_reader_rejects_rehashed_wrong_draw_and_endpoint(study, tmp_path):
    src, _, _ = study
    out = tmp_path / "mutated"
    shutil.copytree(src, out)
    summary = json.loads((out / "summary.json").read_text())
    row = next(r for r in summary["rows"] if r["arm"] == "S_sampled")
    path = out / row["raw"]["path"]
    with np.load(path, allow_pickle=False) as archive:
        raw = {key: archive[key] for key in archive.files}
    raw["innovation"][0, 0] = .123456789
    np.savez_compressed(path, **raw)
    identity = file_identity(path); identity["path"] = row["raw"]["path"]; row["raw"] = identity
    write_json(out / "summary.json", summary)
    with pytest.raises(AssertionError, match="fresh addressed"):
        read_batch(out, permit_fixture=True)
    row["policy_sha256"] = summary["assets"]["S0"]["state_sha256"]
    write_json(out / "summary.json", summary)
    with pytest.raises(AssertionError, match="wrong behavior"):
        read_batch(out, permit_fixture=True)


def test_retained_rejection_precedes_constructor_and_fit(retained, tmp_path):
    old_root, binding, _ = retained
    binding = json.loads(json.dumps(binding))
    binding["files"]["summary.json"]["sha256"] = "0" * 64
    calls = []

    def factory(seed):
        calls.append(seed)
        return Synthetic(seed)

    out = tmp_path / "rejected"
    with pytest.raises(AssertionError):
        run_batch(out, "fixture", retained_out=old_root, protocol=NEW, factory=factory, fixture_binding=binding)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "INCOMPLETE" and summary["rows"] == [] and calls == []
    assert not any(summary["actual"].values())


def test_reset_mismatch_keeps_completed_new_exposure(retained, tmp_path):
    old_root, binding, _ = retained

    class ChangedReset(Synthetic):
        def reset(self, seed):
            result = super().reset(seed)
            if seed in NEW.evaluation_worlds:
                self.positions[0, 0] += 1.
                return self.obs(), self.info()
            return result

    out = tmp_path / "reset-failure"
    with pytest.raises(AssertionError, match="reset differs"):
        run_batch(out, "fixture", retained_out=old_root, protocol=NEW,
                  factory=ChangedReset, fixture_binding=binding)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "INCOMPLETE"
    assert summary["actual"]["native_steps"] == 40 and summary["actual"]["complete_episodes"] == 5
    assert summary["actual"]["fit_started"] == 1 and summary["actual"]["optimizer_steps"] == 9
    assert len(summary["rows"]) == 5 and summary["rows"][-1]["arm"] == "S0"
    assert summary["costs"]["full_C"]["requests"] == 40 and "partial_episode" not in summary
    with pytest.raises(ValueError, match="incomplete/failed"):
        read_batch(out, permit_fixture=True)


def test_failed_worker_keeps_partial_new_exposure(retained, tmp_path):
    old_root, binding, _ = retained

    class Failing(Synthetic):
        def step(self, commands):
            if self.tick == 3:
                raise RuntimeError("fixture failure")
            return super().step(commands)

    out = tmp_path / "partial-failure"
    with pytest.raises(RuntimeError, match="fixture failure"):
        run_batch(out, "fixture", retained_out=old_root, protocol=NEW, factory=Failing, fixture_binding=binding)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "INCOMPLETE" and summary["rows"] == []
    assert summary["actual"]["native_step_calls"] == 4 and summary["actual"]["native_steps"] == 3
    assert summary["actual"]["fit_started"] == 0 and summary["actual"]["complete_episodes"] == 0
    assert summary["actual"]["expert_label_requests"] == 5
    assert summary["costs"]["full_C"]["requests"] == 5 and summary["costs"]["helper"]["helper_calls"] == 5
    assert summary["costs"]["incomplete"] and summary["partial_episode"]["world"] == 121
    with pytest.raises(ValueError, match="incomplete/failed"):
        read_batch(out, permit_fixture=True)


def test_cli_requires_admission_before_scientific_effect(tmp_path):
    from experiments.candidates.uav_fleet_adaptation.b03 import run
    command = [sys.executable, str(Path(run.__file__).resolve()), "--out", str(tmp_path / "forbidden"),
               "--launch-sha", "x", "--seed", "29344001"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "admission" in result.stderr.lower()
    assert not (tmp_path / "forbidden").exists()
    source = Path(run.__file__).read_text()
    assert source.index("admission = require_admission") < source.index("    import torch")


def test_cli_uses_only_source_bound_canonical_controls(tmp_path, monkeypatch):
    from experiments.candidates.uav_fleet_adaptation.b03 import run, study as worker
    from scripts import hmasd_admission
    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **kw: {"sha": "fixture"})
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS"):
        monkeypatch.setenv(name, "1")
    for name in ("set_num_threads", "set_num_interop_threads", "use_deterministic_algorithms"):
        monkeypatch.setattr(torch, name, lambda *a, **kw: None)
    called = []
    monkeypatch.setattr(worker, "run_batch", lambda *a, **kw: called.append((a, kw)) or {"status": "COMPLETE"})
    args = ["--out", str(tmp_path / "uncreated"), "--launch-sha", "fixture", "--seed", "29344001"]
    assert run.main(args)["status"] == "COMPLETE"
    assert called[0][1]["retained_out"] == Path(
        "/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01")
    assert called[0][1]["scientific_invocation"] is True and not (tmp_path / "uncreated").exists()
    with pytest.raises(SystemExit):
        run.main(args + ["--retained-out", str(tmp_path / "different")])
