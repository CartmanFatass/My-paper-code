"""Synthetic recovery identity and fail-closed checks; no native environment calls."""

from collections import defaultdict
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    Actor as BaseActor, Critic as BaseCritic,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import AGENTS, SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.uav_message_content.b05 import model as base_model
from experiments.candidates.uav_message_content.b06 import model, recovery, recover_eval, study


class NativeInfoFixture(SyntheticAdapter):
    def step(self, actions):
        raw, reward, terminated, truncated, info = super().step(actions)
        connections = np.zeros((5, 50), dtype=bool)
        connections[0, :7] = True
        sinr = np.full((5, 50), 20., dtype=np.float64)
        for agent in AGENTS:
            info["infos_dict"][agent]["global"].update(connections=connections.copy(), sinr_matrix=sinr.copy())
        return raw, reward, terminated, truncated, info


@pytest.fixture
def parent(monkeypatch, tmp_path):
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(887)
        actor, critic = BaseActor(), BaseCritic()
    content = io.BytesIO()
    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), arm="B", master=19451,
                    input_size=171, critic_size=451, inherited_sha256=model.SOURCE_INHERITED_SHA256), content)
    value = content.getvalue()
    digest = hashlib.sha256(value).hexdigest()
    for module in (base_model, model, study, recovery):
        monkeypatch.setattr(module, "SOURCE_SHA256", digest)
    path = tmp_path / "parent.pt"
    path.write_bytes(value)
    return path, digest


def row_identity(master, arm, episode):
    return dict(master=master, arm=arm, phase="final_eval", episode=episode, steps=recovery.HORIZON,
                reset_seed=study.EVAL_BASE + 2000 + episode,
                channel_seed=study.EVAL_BASE + 7000 + episode,
                motion_seed=study.EVAL_BASE + 3000 + episode)


@pytest.fixture
def original(parent, monkeypatch, tmp_path):
    # Miniature fixed slots are patched in tests only; the CLI exposes no size/factory bypass.
    monkeypatch.setattr(recovery, "HORIZON", 32)
    monkeypatch.setattr(recovery, "TRAIN", 2)
    monkeypatch.setattr(recovery, "EVALUATION", 2)
    monkeypatch.setattr(recovery, "D_EPISODES", (1,))
    monkeypatch.setattr(recovery, "B40_EPISODES", (0, 1))
    path, digest = parent
    out = tmp_path / "original"
    out.mkdir()
    cells = []
    for master in study.MASTERS:
        for arm in study.ARMS:
            directory = out / str(master) / arm
            directory.mkdir(parents=True)
            actor, critic = model.build_arm(master, arm)
            model.load_warm_start(actor, critic, path.read_bytes(), digest)
            initial = study.save_checkpoint(directory / "initial.pt", actor, critic, arm, master,
                                            recovery.ORIGINAL_SOURCE)
            with torch.no_grad():
                if arm == "D":
                    actor.residual_output.bias.copy_(torch.tensor([.8, -.4, .2]))
                    actor.residual_hidden.weight.add_(.01)
                    critic.network[0].weight.add_(.02)
                else:
                    actor.b.copy_(torch.tensor([.8, -.4, .2]))
            final = study.save_checkpoint(directory / "final.pt", actor, critic, arm, master,
                                          recovery.ORIGINAL_SOURCE)
            n = 1 if (master, arm) == (19703, "D") else 2
            rows = [row_identity(master, arm, e) for e in range(n)]
            cell = dict(master=master, arm=arm, directory=str(directory), launch_sha=recovery.ORIGINAL_SOURCE,
                        status="INCOMPLETE" if n == 1 else "COMPLETE", rows=rows, limits=[],
                        counts=study.expected_counts(arm, 32, 2, n), initial_checkpoint=initial,
                        final_checkpoint=final, final_tensor_sha256=recovery.parameter_hashes(actor, critic))
            study.write_json(directory / "summary.json", cell)
            records = [dict(master=master, arm=arm, phase="train", episode=e) for e in range(2)] + rows
            (directory / "episodes.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
            (directory / "updates.jsonl").write_text("synthetic-original-update-witness\n")
            cells.append(cell)
    batch = dict(launch_sha=recovery.ORIGINAL_SOURCE, source_sha=recovery.ORIGINAL_SOURCE,
                 status="INCOMPLETE", active_cell="19703/D", b40=None, cells=cells[:-1])
    study.write_json(out / "summary.json", batch)
    study.write_json(out / "process-exit.json", dict(status="exited", exit_code=-15, termination="signal"))
    study.write_json(out / "launch-manifest.json", dict(sha=recovery.ORIGINAL_SOURCE, node="local_linux"))
    monkeypatch.setattr(recovery, "ORIGINAL_SUMMARY_SHA", study.sha256(out / "summary.json"))
    monkeypatch.setattr(recovery, "D_SUMMARY_SHA", study.sha256(out / "19703/D/summary.json"))
    monkeypatch.setattr(recovery, "D_CHECKPOINT_SHA", study.sha256(out / "19703/D/final.pt"))
    inv = recovery.inventory(out)
    monkeypatch.setattr(recovery, "ORIGINAL_INVENTORY", inv["sha256"])
    monkeypatch.setattr(recovery, "ORIGINAL_FILES", inv["files"])
    return out, path, digest


def collect(env, actor, critic, arm, e, out):
    rows = []
    recovery.collect_episode(env, actor, critic, arm, 32, study.EVAL_BASE + 2000 + e,
                             study.EVAL_BASE + 7000 + e, generator(study.EVAL_BASE + 3000 + e),
                             row_identity(19703 if arm == "D" else 19451, arm, e),
                             defaultdict(int), rows.append, raw_path=out)
    return rows[0]


def equivalent(first, second):
    # Paths and ZIP container bytes are not scientific trace semantics.
    with np.load(first["raw"], allow_pickle=False) as a, np.load(second["raw"], allow_pickle=False) as b:
        assert a.files == b.files
        for name in a.files:
            np.testing.assert_array_equal(a[name], b[name], err_msg=name)
    assert {k: v for k, v in first.items() if k not in ("raw", "raw_sha256")} == {
        k: v for k, v in second.items() if k not in ("raw", "raw_sha256")}


def test_nonzero_d_split_reload_is_exact(original, tmp_path):
    out, parent_path, digest = original
    bound = recovery.load_original_bindings(out, parent_path, digest)
    cell = bound["unfinished_d"]
    saved = Path(cell["final_checkpoint"]["path"]).read_bytes()
    actor, critic = recovery.load_final_d(saved, cell)
    assert torch.count_nonzero(actor.residual_output.bias) == 3
    uninterrupted = NativeInfoFixture(1970301000, 32)
    collect(uninterrupted, actor, critic, "D", 0, tmp_path / "prefix.npz")
    expected = collect(uninterrupted, actor, critic, "D", 1, tmp_path / "uninterrupted.npz")
    reloaded_actor, reloaded_critic = recovery.load_final_d(saved, cell)
    recovered = collect(NativeInfoFixture(1970301000, 32), reloaded_actor, reloaded_critic,
                        "D", 1, tmp_path / "recovered.npz")
    equivalent(expected, recovered)
    assert recovery.parameter_hashes(reloaded_actor, reloaded_critic) == cell["final_tensor_sha256"]
    assert recovery.inventory(out) == bound["original"]["inventory"]


def test_b40_unchanged_branch_exact(parent, tmp_path):
    path, digest = parent
    cell = study.run_cell(19451, "B40", tmp_path / "baseline", path.read_bytes(), digest,
                          factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=0,
                          evaluation=2, launch_sha="synthetic-source", checkpoint_path=path)
    assert cell["status"] == "COMPLETE", cell["limits"]
    actor, critic = model.load_base(path.read_bytes(), digest)
    for e in (0, 1):
        fresh = collect(NativeInfoFixture(study.EVAL_BASE + 2000, 32), actor, critic,
                        "B40", e, tmp_path / f"baseline_fresh_{e}.npz")
        equivalent(cell["rows"][e], fresh)


def test_miniature_recovery_no_optimizer_original_unchanged(original, monkeypatch, tmp_path):
    out, path, digest = original
    inv = recovery.inventory(out)

    def forbidden(*args, **kwargs):
        pytest.fail("recovery attempted an optimizer/training call")

    monkeypatch.setattr(study, "optimizers_for", forbidden)
    monkeypatch.setattr(study, "update_motion", forbidden)
    monkeypatch.setattr(torch.optim, "Adam", forbidden)
    monkeypatch.setattr(study, "make_real", lambda seed: NativeInfoFixture(seed, 32))
    result = recovery.run_recovery(tmp_path / "recovery", "synthetic-source", out, path, digest)
    assert result["status"] == "COMPLETE", result["limits"]
    assert result["actual"]["final_eval_episodes"] == 3
    assert result["actual"]["team_steps"] == 96
    assert result["actual"]["motion_samples"] == 480
    assert result["actual"]["constructors"] == 2
    assert result["actual"]["fit_started"] == result["actual"]["optimizer_steps"] == 0
    assert result["coverage"]["original_evaluation_episodes"] == 11
    assert len(list((tmp_path / "recovery").rglob("*.npz"))) == 3
    assert not list((tmp_path / "recovery").rglob("*.pt"))
    assert result["original_inventory_after"] == inv == recovery.inventory(out)
    assert recovery.read_json(out / "summary.json")["status"] == "INCOMPLETE"
    assert result["original"]["exit"]["exit_code"] == -15
    bound = recovery.load_original_bindings(out, path, digest)
    for field in ("episode", "motion_seed", "steps"):
        bad = copy.deepcopy(result)
        bad["recovered_d"]["rows"][0][field] += 1
        with pytest.raises(ValueError, match="coverage|binding"):
            recovery.validate_recovery(bad, bound)
    bad = copy.deepcopy(result)
    bad["actual"]["optimizer_steps"] = 1
    with pytest.raises(ValueError, match="aggregate"):
        recovery.validate_recovery(bad, bound)
    with pytest.raises(FileExistsError, match="already exists"):
        recovery.run_recovery(tmp_path / "recovery", "synthetic-source", out, path, digest)


@pytest.mark.parametrize("failure", ["source", "parent", "inventory", "exit", "coverage", "input"])
def test_mismatches_stop_before_native_work(original, failure, monkeypatch, tmp_path):
    out, path, digest = original
    calls = []
    monkeypatch.setattr(study, "make_real", lambda *a: calls.append(a))
    if failure == "source":
        monkeypatch.setattr(recovery, "FROZEN_SOURCE_HASHES", {"experiments/AGENTS.md": "bad"})
    elif failure == "parent":
        path.write_bytes(b"wrong-parent")
    elif failure == "inventory":
        (out / "extra-file").write_text("changed original")
    else:
        if failure == "exit":
            p = out / "process-exit.json"
            value = recovery.read_json(p)
            value["exit_code"] = 0
        else:
            p = out / "19703/D/summary.json"
            value = recovery.read_json(p)
            value["rows"][0]["episode" if failure == "coverage" else "motion_seed"] += 1
            study.write_json(p, value)
            monkeypatch.setattr(recovery, "D_SUMMARY_SHA", study.sha256(p))
        study.write_json(p, value)
        monkeypatch.setattr(recovery, "ORIGINAL_INVENTORY", recovery.inventory(out)["sha256"])
    with pytest.raises(ValueError):
        recovery.run_recovery(tmp_path / "bad", "synthetic-source", out, path, digest)
    assert calls == []
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("failure", ["metadata", "dtype", "hash"])
def test_d_checkpoint_contract_fails_before_environment(original, failure, monkeypatch, tmp_path):
    out, path, digest = original
    bound = recovery.load_original_bindings(out, path, digest)
    cell = copy.deepcopy(bound["unfinished_d"])
    saved = Path(cell["final_checkpoint"]["path"]).read_bytes()
    if failure == "hash":
        cell["final_tensor_sha256"]["residual_output"] = "bad"
    else:
        state = torch.load(io.BytesIO(saved), map_location="cpu", weights_only=True)
        if failure == "metadata":
            state["master"] = 19702
        else:
            state["actor"]["residual_output.bias"] = state["actor"]["residual_output.bias"].double()
        content = io.BytesIO()
        torch.save(state, content)
        saved = content.getvalue()
        monkeypatch.setattr(recovery, "D_CHECKPOINT_SHA", hashlib.sha256(saved).hexdigest())
    calls = []
    monkeypatch.setattr(study, "make_real", lambda *a: calls.append(a))
    result = recovery.run_d(tmp_path / "bad-D", "synthetic-source", saved, cell, lambda: None)
    assert result["status"] == "INCOMPLETE"
    assert result["counts"]["constructors"] == 0
    assert calls == []


def test_cpu_stop_preserves_partial_without_b40(original, monkeypatch, tmp_path):
    out, path, digest = original
    monkeypatch.setattr(study, "make_real", lambda seed: NativeInfoFixture(seed, 32))
    original_collect = recovery.collect_episode

    def stop_after_episode(*args, **kwargs):
        original_collect(*args, **kwargs)
        raise TimeoutError("test ceiling after one persisted episode")

    monkeypatch.setattr(recovery, "collect_episode", stop_after_episode)
    inv = recovery.inventory(out)
    result = recovery.run_recovery(tmp_path / "partial", "synthetic-source", out, path, digest)
    assert result["status"] == "INCOMPLETE"
    assert result["actual"]["final_eval_episodes"] == 1
    assert result["b40"] is None
    assert (tmp_path / "partial/19703/D/raw/final_01.npz").is_file()
    assert recovery.inventory(out) == inv
    monkeypatch.setattr(recovery, "CPU_LIMIT_SECONDS", 0)
    with pytest.raises(TimeoutError, match="ceiling"):
        recovery.run_recovery(tmp_path / "zero", "synthetic-source", out, path, digest)
    assert not (tmp_path / "zero").exists()


def test_entry_admission_precedes_checkpoint_effects(monkeypatch, tmp_path):
    from scripts import hmasd_admission

    def deny(*args, **kwargs):
        raise RuntimeError("admission test refusal")

    monkeypatch.setattr(hmasd_admission, "require_admission", deny)
    monkeypatch.setattr(recovery, "run_recovery", lambda *a, **k: pytest.fail("ran before admission"))
    out = tmp_path / "runs/uav_message_content/new"
    with pytest.raises(RuntimeError, match="admission test refusal"):
        recover_eval.main(["--out", str(out), "--launch-sha", "fixture", "--seed", "19701",
                           "--original-tag", "b06_calibration", "--checkpoint",
                           str(tmp_path / "absent-parent"), "--checkpoint-sha256",
                           "34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2"])
    assert not out.exists()


def entry_args(out, checkpoint, tag="b06_calibration"):
    return ["--out", str(out), "--launch-sha", "fixture", "--seed", "19701",
            "--original-tag", tag, "--checkpoint", str(checkpoint), "--checkpoint-sha256",
            "34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2"]


def test_admitted_snapshot_entry_uses_canonical_output_sibling(monkeypatch, tmp_path):
    from scripts import hmasd_admission, hmasd_launch

    author = tmp_path / "author"
    snapshot = author / ".git/hmasd-launch-sources/fixture"
    out = author / "runs/uav_message_content/b06_eval_recovery_a02"
    checkpoint = tmp_path / "external-parent.pt"
    runner_relative = Path("experiments/candidates/uav_message_content/b06/recover_eval.py")
    snapshot_runner = snapshot / runner_relative
    snapshot_runner.parent.mkdir(parents=True)
    snapshot_runner.write_bytes(Path(recover_eval.__file__).read_bytes())
    (snapshot / "scripts").mkdir()
    (snapshot / "scripts/hmasd_admission.py").write_text("# Fixture bootstrap identity only.\n")
    # Compact tracked evidence exists in the snapshot, but the original bulk does not.
    snapshot_original = snapshot / "runs/uav_message_content/b06_calibration"
    snapshot_original.mkdir(parents=True)
    (snapshot_original / "summary.json").write_text('{"status":"INCOMPLETE"}\n')
    (author / ".codex").mkdir()
    (author / ".codex/hmasd-compute.toml").write_text(
        'status = "active"\n[nodes.fixture]\n' +
        f"python = {json.dumps(sys.executable)}\nproject_root = {json.dumps(str(author))}\n")
    monkeypatch.setattr(hmasd_launch, "_git_root", lambda path: author)
    monkeypatch.setattr(hmasd_launch, "_git_common_dir", lambda path: author / ".git")
    monkeypatch.setattr(hmasd_launch, "_run_git", lambda *a, **k: SimpleNamespace(returncode=0))
    monkeypatch.setattr(hmasd_launch, "_require_policy", lambda *a, **k: None)
    monkeypatch.setattr(hmasd_launch, "_validate_publication", lambda *a, **k: None)
    monkeypatch.setattr(hmasd_launch.hmasd_source_snapshot, "prepare", lambda *a: snapshot)
    launch = argparse.Namespace(direction="uav_message_content", lead="fixture", sha="f" * 40,
                                output=str(out), source_root=str(author), node="fixture", remote="origin",
                                snapshot=True, runner_argv=[str(runner_relative), *entry_args(out, checkpoint)])
    paths, _, _, _, runner_args = hmasd_launch._prepare_paths_and_config(launch)
    assert paths.runner == snapshot_runner and paths.output_root == out
    assert runner_args[runner_args.index("--out") + 1] == str(out)
    assert runner_args[runner_args.index("--original-tag") + 1] == "b06_calibration"
    # Reconstruct the actual old failure boundary using the same launcher function.
    previous = copy.deepcopy(launch)
    i = previous.runner_argv.index("--original-tag")
    previous.runner_argv[i:i + 2] = ["--original", str(author / "runs/uav_message_content/b06_calibration")]
    _, _, _, _, old_args = hmasd_launch._prepare_paths_and_config(previous)
    assert old_args[old_args.index("--original") + 1] == str(snapshot_original)
    monkeypatch.setattr(recover_eval, "ROOT", snapshot)
    events = []

    def admit(*args, **kwargs):
        events.append("admitted")
        return {"sha": "fixture"}  # require_admission does not return control_root.

    def run(*args, **kwargs):
        events.append("run")
        assert args[:4] == (out, "fixture", author / "runs/uav_message_content/b06_calibration", checkpoint)
        assert snapshot not in args[2].parents
        return {"status": "COMPLETE"}

    monkeypatch.setattr(hmasd_admission, "require_admission", admit)
    monkeypatch.setattr(torch, "set_num_threads", lambda n: None)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: None)
    monkeypatch.setattr(recovery, "run_recovery", run)
    assert recover_eval.main(runner_args) == {"status": "COMPLETE"}
    assert events == ["admitted", "run"]
    assert not out.exists() and not checkpoint.exists()


@pytest.mark.parametrize("tag", ["other", "../b06_calibration", "/abs/b06_calibration"])
def test_original_tag_cannot_change_or_escape(monkeypatch, tmp_path, tag):
    from scripts import hmasd_admission

    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: pytest.fail("invalid tag admitted"))
    monkeypatch.setattr(recovery, "run_recovery", lambda *a, **k: pytest.fail("invalid tag ran"))
    with pytest.raises(SystemExit) as error:
        recover_eval.main(entry_args(tmp_path / "runs/uav_message_content/new", tmp_path / "parent.pt", tag))
    assert error.value.code == 2


@pytest.mark.parametrize("layout", ["relative", "runs/other/new", "other/uav_message_content/new"])
def test_output_requires_absolute_direction_layout(monkeypatch, tmp_path, layout):
    from scripts import hmasd_admission

    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: pytest.fail("invalid output admitted"))
    out = Path(layout) if layout == "relative" else tmp_path / layout
    with pytest.raises(SystemExit) as error:
        recover_eval.main(entry_args(out, tmp_path / "parent.pt"))
    assert error.value.code == 2
