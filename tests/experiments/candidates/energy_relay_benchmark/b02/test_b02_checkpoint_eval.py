"""B02 round trip: tiny SET fit -> checkpoints -> controller L in the B01 evaluator."""

from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b02 import checkpoint_eval as ce
from experiments.candidates.energy_relay_benchmark.b02 import configuration as cfg
from experiments.candidates.energy_relay_benchmark.b02.training import run_training
from scripts import run_energy_relay_benchmark_b02 as entry

WORLDS = (317801, 317802)
HORIZON = 30
VOLATILE = {"wall_seconds", "worker_peak_rss_kib"}


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    """Preset architecture (the evaluator rebuilds it), 2 lanes x 20 steps x 2 rollouts."""
    out = tmp_path_factory.mktemp("b02_fit") / "run"
    spec = replace(cfg.B02Spec(), seed=317753, rollouts=2, rollout_length=20, episode_length=20,
                   checkpoint_every_transitions=40)
    torch.set_num_threads(2)
    summary = run_training(out=out, launch_sha="test", spec=spec, device_name="cpu", threads=2,
                           argv=["test"])
    return out, summary


def _task(out, index, tmp_path, **changes):
    root = out / "checkpoints" / f"c{index:02d}"
    record = json.loads((root / "record.json").read_text())
    values = dict(controller="L", seed=WORLDS[0], params=PRODUCTION_PARAMS, horizon=HORIZON,
                  policy_seed=record["training_seed"], threads=1, checkpoint=str(root / "agent.pt"),
                  checkpoint_record=str(root / "record.json"), log_dir=str(tmp_path))
    return ev.WorldTask(**(values | changes))


def test_training_writes_config_checkpoints_records_and_summary(trained):
    out, summary = trained
    assert summary["status"] == "COMPLETE" and summary["counts"]["transitions"] == 80
    assert summary["checkpoint_rollouts"] == [1, 2] and sorted(summary["checkpoints"]) == \
        ["c00", "c01", "c02"]
    assert [summary["checkpoints"][c]["transitions"] for c in ("c00", "c01", "c02")] == [0, 40, 80]
    config = json.loads((out / "config.json").read_text())
    assert config["programme"] == "SET-shield-on-1.2M" and config["actor_input_width"] == 3599
    assert config["training_feedback"]["params"] == {"enter_margin": 0.0, "exit_margin": 0.05}
    for index in range(3):
        record = json.loads((out / "checkpoints" / f"c{index:02d}" / "record.json").read_text())
        assert record["checkpoint"] == f"c{index:02d}" and record["config"]["k"] == 10
        assert record["agent_pt_sha256"] == ce.sha256_file(
            out / "checkpoints" / f"c{index:02d}" / "agent.pt")
    rows = [json.loads(line) for line in (out / "progress.jsonl").read_text().splitlines()]
    assert [row["event"]["event"] for row in rows].count("rollout") == 2
    rollout = summary["rollouts"][-1]
    assert rollout["ppo"]["approx_kl"] is None and rollout["ppo"]["action_entropy"] is not None
    assert rollout["optimizer_steps"]["low_actor"] > 0 and rollout["optimizer_steps"]["high"] == 0
    for key in ("shield_mapping_share", "f_mode_uav_step_share", "lane_native_J",
                "lane_qos_per_step", "episodes_completed"):
        assert key in rollout


def test_loaded_learner_equals_saved_and_has_the_set_width(trained, tmp_path):
    out, _ = trained
    task = _task(out, 2, tmp_path)
    record = ev.read_learner_record(task)
    config = ev.learner_eval_config(ev.make_eval_config(HORIZON, task.policy_seed), record)
    agent, identity = ev.load_learner_policy(task, record, config, torch.device("cpu"), str(tmp_path))
    stored = torch.load(task.checkpoint, map_location="cpu", weights_only=False)
    for name in ("skill_coordinator", "skill_discoverer"):
        saved, loaded = stored[name], getattr(agent, name).state_dict()
        assert saved.keys() == loaded.keys()
        for key in saved:
            torch.testing.assert_close(loaded[key], saved[key], rtol=0, atol=0)
    assert identity["policy_fingerprint"] == record["policy_fingerprint"]
    assert agent.skill_discoverer.central_input_dim + config.obs_dim == 3599
    assert agent.skill_discoverer.actor.base.mlp[0].in_features == 3599


def test_loader_rejects_records_that_disagree(trained, tmp_path):
    out, _ = trained
    source = out / "checkpoints" / "c01"

    def tampered(label, edit=None, data=False):
        root = tmp_path / label / "c01"
        shutil.copytree(source, root)
        if edit is not None:
            record = json.loads((root / "record.json").read_text())
            edit(record)
            (root / "record.json").write_text(json.dumps(record))
        if data:
            with (root / "agent.pt").open("ab") as handle:
                handle.write(b"\0")
        return replace(_task(out, 1, tmp_path), checkpoint=str(root / "agent.pt"),
                       checkpoint_record=str(root / "record.json"))

    with pytest.raises(ValueError, match="sha256"):
        ev.evaluate_task(tampered("bytes", data=True))
    with pytest.raises(ValueError, match="sha256"):
        ev.evaluate_task(tampered("sha", lambda r: r.update(agent_pt_sha256="0" * 64)))
    with pytest.raises(ValueError, match="recorded learner config disagrees"):
        ev.evaluate_task(tampered("gamma", lambda r: r["config"].update(gamma=0.5)))
    with pytest.raises(ValueError, match="recorded learner config disagrees"):
        ev.evaluate_task(tampered("hidden", lambda r: r["config"].update(hidden_size=64)))
    with pytest.raises(ValueError, match="SET"):
        ev.evaluate_task(tampered("flag", lambda r: r["config"].update(
            use_central_snapshot_in_flat_actor=False)))
    with pytest.raises(ValueError, match="fingerprint"):
        ev.evaluate_task(tampered("fp", lambda r: r.update(policy_fingerprint="0" * 64)))
    with pytest.raises(ValueError, match="checkpoint and its record"):
        ev.evaluate_task(replace(_task(out, 1, tmp_path), checkpoint_record=None))


def test_holdout_worlds_need_final(trained, tmp_path):
    out, _ = trained
    assert ce.parse_worlds("955001-955032") == ce.DEVELOPMENT_WORLDS
    assert ce.parse_worlds("957001-957003,317801") == (957001, 957002, 957003, 317801)
    ce.check_worlds(ce.DEVELOPMENT_WORLDS, False)
    ce.check_worlds(ce.HOLDOUT_WORLDS, True)
    for worlds, final in (((955001, 957001), False), (ce.HOLDOUT_WORLDS, False),
                          ((955001,), True), ((957001, 955001), True)):
        with pytest.raises(ValueError):
            ce.check_worlds(worlds, final)
    target = tmp_path / "never"
    with pytest.raises(ValueError, match="hold-out"):
        ce.evaluate_checkpoint(checkpoint_dir=out / "checkpoints" / "c02", out=target,
                               worlds=(957001,), modes=("deterministic",), final=False,
                               launch_sha="test", horizon=HORIZON)
    assert not target.exists()


def test_round_trip_both_modes_repeat_deterministically(trained, tmp_path):
    out, _ = trained
    results = []
    for label in ("first", "again"):
        summary = ce.evaluate_checkpoint(
            checkpoint_dir=out / "checkpoints" / "c02", out=tmp_path / label, worlds=WORLDS,
            modes=("deterministic", "stochastic"), final=False, launch_sha="test",
            workers=1, threads=1, horizon=HORIZON, argv=["test"])
        assert summary["status"] == "COMPLETE" and summary["counts"]["episodes_completed"] == 4
        panels = {}
        for mode in ("deterministic", "stochastic"):
            name = f"L_c02_{mode}_e0.00_x0.05"
            path = tmp_path / label / "checkpoint-eval" / "panels" / f"{name}.json"
            assert (tmp_path / label / "checkpoint-eval" / "traces" / f"{name}.npz").exists()
            panels[mode] = json.loads(path.read_text())
        results.append(panels)
    first, again = results
    for mode in ("deterministic", "stochastic"):
        strip = lambda rows: [{k: v for k, v in row.items() if k not in VOLATILE} for row in rows]
        assert strip(first[mode]["worlds"]) == strip(again[mode]["worlds"])
    det, sto = first["deterministic"], first["stochastic"]
    record = json.loads((out / "checkpoints" / "c02" / "record.json").read_text())
    for row in sto["worlds"]:
        assert row["draw"] == 0 and row["action_mode"] == "stochastic"
        assert row["sample_seed"] == ev.sample_seed(record["training_seed"], row["seed"], 0)
        assert row["controller"] == "L" and row["controller_information"] == ev.L_CONTROLLER_INFORMATION
    for row in det["worlds"]:
        assert row["actual_length"] == HORIZON and row["action_mode"] == "deterministic"
        for key in ("boundary_share_normal_mode", "altitude_floor_share_normal_mode",
                    "anchor_uav_steps_within_300m", "centre_uav_steps_within_300m",
                    "first_service_step"):
            assert key in row
    assert det["policy_identity"][0]["checkpoint_sha256"] == record["agent_pt_sha256"]
    with pytest.raises(FileExistsError):
        ce.evaluate_checkpoint(checkpoint_dir=out / "checkpoints" / "c02", out=tmp_path / "first",
                               worlds=WORLDS, modes=("deterministic",), final=False,
                               launch_sha="test", horizon=HORIZON)


@pytest.mark.parametrize("argv", [
    ["train", "--seed", "925031", "--launch-sha", "fixture", "--out", "{target}"],
    ["evaluate-checkpoint", "--checkpoint", "{target}", "--launch-sha", "fixture",
     "--out", "{target}"],
])
def test_admission_precedes_candidate_import_and_output(tmp_path, monkeypatch, argv):
    from scripts import hmasd_admission

    target = tmp_path / "never-created"
    def refuse(*args, **kwargs):
        raise RuntimeError("no admission")
    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    with pytest.raises(RuntimeError, match="no admission"):
        entry.main([item.replace("{target}", str(target)) for item in argv])
    assert not target.exists()


def test_entry_arguments():
    args = entry.parse_args(["evaluate-checkpoint", "--checkpoint", "c", "--out", "o",
                             "--launch-sha", "s", "--modes", "stochastic"])
    assert args.modes == ("stochastic",) and args.worlds == "955001-955032" and not args.final
    assert entry.parse_args(["train", "--seed", "925031", "--launch-sha", "s",
                             "--out", "o"]).seed == cfg.TRAINING_SEED
    assert entry.TRAINING_SEEDS == cfg.TRAINING_SEEDS
    for bad in (["train", "--seed", "915031", "--launch-sha", "s", "--out", "o"],
                ["train", "--launch-sha", "s", "--out", "o"],
                ["evaluate-checkpoint", "--checkpoint", "c", "--out", "o", "--launch-sha", "s",
                 "--modes", "sampled"]):
        with pytest.raises(SystemExit):
            entry.parse_args(bad)


def test_learner_config_builds_the_same_world_as_the_n_and_h_config(trained):
    """L's env comes from the SET config; it must be N's / H's world bit for bit."""
    import numpy as np
    from experiments.candidates.uav_service_auxiliary.b01.native import make_env

    out, _ = trained
    record = json.loads((out / "checkpoints" / "c01" / "record.json").read_text())
    plain = ev.make_eval_config(HORIZON, 925031)
    learner = ev.learner_eval_config(ev.make_eval_config(HORIZON, 925031), record)
    rng = np.random.default_rng(7)
    actions = rng.uniform(-1, 1, size=(12, 8, 4)).astype(np.float32)
    for seed in (955001, 317801):
        envs = [make_env(plain, seed), make_env(learner, seed)]
        try:
            (obs_a, info_a), (obs_b, info_b) = (env.reset(seed=seed) for env in envs)
            np.testing.assert_array_equal(obs_a, obs_b)
            np.testing.assert_array_equal(info_a["state"], info_b["state"])
            for action in actions:
                a, b = (env.step(action.copy()) for env in envs)
                np.testing.assert_array_equal(a[0], b[0])
                assert a[1:4] == b[1:4]
                np.testing.assert_array_equal(a[4]["next_state"], b[4]["next_state"])
        finally:
            for env in envs:
                env.close()


def test_final_holdout_layout(trained, tmp_path, monkeypatch):
    """The once-only --final path, exercised on a stand-in hold-out world."""
    out, _ = trained
    monkeypatch.setattr(ce, "HOLDOUT_WORLDS", (317803,))
    summary = ce.evaluate_checkpoint(checkpoint_dir=out / "checkpoints" / "c02", out=tmp_path,
                                     worlds=(317803,), modes=("deterministic",), final=True,
                                     launch_sha="test", horizon=10)
    root = tmp_path / "checkpoint-eval" / "final"
    assert summary["final"] is True and summary["status"] == "COMPLETE"
    assert (root / "panels" / "L_c02_deterministic_e0.00_x0.05.json").exists()
    assert (root / "traces" / "L_c02_deterministic_e0.00_x0.05.npz").exists()
    assert (root / "c02_deterministic" / "summary.json").exists()
    assert not (tmp_path / "checkpoint-eval" / "panels").exists()
