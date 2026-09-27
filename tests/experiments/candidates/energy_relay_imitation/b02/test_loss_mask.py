"""B02 fixture checks use short unrelated worlds and no scientific panel."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_imitation.b01 import study as b01
from experiments.candidates.energy_relay_imitation.b02 import study as b02


def _episode(config, length: int = 4):
    return {"observations_t": np.zeros((length, 8, config.obs_dim), np.float32),
            "state_t": np.zeros((length, config.state_dim), np.float32),
            "proposal_t": np.full((length, 8, 4), .25, np.float32),
            "submitted_t": np.full((length, 8, 4), -.5, np.float32),
            "mode": np.broadcast_to((np.arange(length) % 4 != 3)[:, None],
                                     (length, 8)).copy()}


def _source_fixture(tmp_path):
    from experiments.candidates.energy_relay_benchmark.b02.training import new_agent

    torch.set_num_threads(1)
    root = tmp_path / "b01"
    (root / "checkpoints").mkdir(parents=True)
    (root / "logs").mkdir()
    config = b01.make_config(horizon=12)
    agent, _ = new_agent(config, device=torch.device("cpu"), log_dir=root / "logs",
                         seed=b01.MODEL_SEED)
    initial = b01._save_checkpoint(agent, config, root, "initial", b02.SOURCE_SHA, 0, 0)
    panels = {}
    train, evaluation = (41, 42), (43, 44)
    for panel, worlds in (("teacher_train", train), ("teacher_eval", evaluation),
                          ("initial_eval", evaluation), ("final_eval", evaluation)):
        rows = []
        for seed in worlds:
            row = {"seed": seed, "actual_length": 12, "failed": False,
                   "qos_per_step": .1, "raw_native_J": 10.0,
                   "return_constraint_cost_raw_sum": 1.0,
                   "episode_minimum_battery_ratio": .3,
                   "cutoff_event_penalty_sum": 0.0,
                   "depletion_event_penalty_sum": 0.0,
                   "zero_service": False}
            if panel.startswith("teacher"):
                directory = root / "raw" / panel
                directory.mkdir(parents=True, exist_ok=True)
                raw = directory / f"{seed}.npz"
                np.savez_compressed(raw, **_episode(config, length=12))
                row["raw"] = b01._artifact(raw, root)
            rows.append(row)
        panels[panel] = {"planned": len(worlds), "completed": len(worlds), "rows": rows}
    baseline = {"status": "COMPLETE", "launch_sha": b02.SOURCE_SHA,
                "panels": panels, "checkpoints": {"initial": initial}}
    b01._write_json(root / "summary.json", baseline)
    pins = b02.SourcePins(summary_sha256=b01.sha256_file(root / "summary.json"),
                          initial_sha256=initial["record"]["agent_pt_sha256"],
                          initial_fingerprint=initial["record"]["policy_fingerprint"])
    return root, pins, train, evaluation, config


def test_pinned_source_validation_and_raw_rejection(tmp_path):
    root, pins, train, evaluation, _config = _source_fixture(tmp_path)
    _baseline, receipt = b02.validate_source(root, pins=pins, train_worlds=train,
                                               eval_worlds=evaluation, horizon=12)
    assert receipt["summary"]["sha256"] == pins.summary_sha256
    assert receipt["initial_checkpoint"]["sha256"] == pins.initial_sha256
    assert len(receipt["raw_inputs"]["teacher_train"]) == len(train)
    raw = root / "raw" / "teacher_train" / f"{train[0]}.npz"
    with raw.open("ab") as handle:
        handle.write(b"corrupt")
    with pytest.raises(ValueError, match="byte count changed"):
        b02.validate_source(root, pins=pins, train_worlds=train,
                            eval_worlds=evaluation, horizon=12)


def test_source_checkpoint_and_summary_refusal_before_output(tmp_path):
    root, pins, train, evaluation, _config = _source_fixture(tmp_path)
    path = root / "checkpoints" / "initial" / "agent.pt"
    with path.open("ab") as handle:
        handle.write(b"corrupt")
    with pytest.raises(ValueError, match="byte count changed"):
        b02.validate_source(root, pins=pins, train_worlds=train,
                            eval_worlds=evaluation, horizon=12)
    output = tmp_path / "uncreated-b02"
    with pytest.raises(ValueError, match="summary is incomplete|summary is incomplete or"):
        # A correctly hashed but incomplete fixture is also refused before study output.
        bad = copy.deepcopy(json.loads((root / "summary.json").read_text()))
        bad["status"] = "INCOMPLETE"
        b01._write_json(tmp_path / "incomplete.json", bad)
        bad_pins = b02.SourcePins(summary_sha256=b01.sha256_file(tmp_path / "incomplete.json"),
                                  initial_sha256=pins.initial_sha256,
                                  initial_fingerprint=pins.initial_fingerprint)
        alternative = tmp_path / "other-b01"
        alternative.mkdir()
        (alternative / "summary.json").write_bytes((tmp_path / "incomplete.json").read_bytes())
        b02.validate_source(alternative, pins=bad_pins, train_worlds=train,
                            eval_worlds=evaluation, horizon=12)
    assert not output.exists()


def test_masked_fit_matches_manual_selected_mse_and_carries_hidden(tmp_path, monkeypatch):
    from experiments.candidates.energy_relay_benchmark.b02.training import new_agent

    torch.set_num_threads(1)
    config = b01.make_config(horizon=12)
    seeds = (41, 42, 43, 44)
    monkeypatch.setattr(b01, "TRAIN_WORLDS", seeds)
    monkeypatch.setattr(b01, "EPOCHS", 1)
    monkeypatch.setattr(b01, "CHUNK", 2)
    source = tmp_path / "source"
    raw = source / "raw" / "teacher_train"
    raw.mkdir(parents=True)
    for seed in seeds:
        np.savez_compressed(raw / f"{seed}.npz", **_episode(config))
    out = tmp_path / "b02"
    out.mkdir()
    (out / "logs").mkdir()
    manual, _ = new_agent(config, device=torch.device("cpu"), log_dir=out / "logs",
                          seed=b01.MODEL_SEED)
    fitted, _ = new_agent(config, device=torch.device("cpu"), log_dir=out / "logs",
                          seed=b01.MODEL_SEED)
    order = np.random.default_rng(b01.ORDER_SEED).permutation(seeds)
    group = [b01._load_episode(raw / f"{seed}.npz") for seed in order]
    hidden = b01._initial_hidden(config, 4, torch.device("cpu"))
    actor = manual.skill_discoverer.actor
    actor.train(True)
    observations, _target, valid, active = b01._chunk(group, 0, 2, torch.device("cpu"))
    _actions, hidden = b01._actor_forward(actor, observations, hidden, reset=True)
    assert int((valid * (1 - active)).sum()) == 0
    manual.discoverer_actor_optimizer.zero_grad(set_to_none=True)
    hidden = hidden.detach()
    observations, target, valid, active = b01._chunk(group, 2, 4, torch.device("cpu"))
    actions, _hidden = b01._actor_forward(actor, observations, hidden, reset=False)
    selected = valid * (1 - active)
    assert int(selected.sum()) == 32
    manual_loss = (((actions - target) ** 2) * selected.unsqueeze(-1)).sum() / (32 * 4)
    manual.discoverer_actor_optimizer.zero_grad(set_to_none=True)
    manual_loss.backward()
    torch.nn.utils.clip_grad_norm_(manual.discoverer_actor_optimizer.param_groups[0]["params"],
                                   config.max_grad_norm)
    manual.discoverer_actor_optimizer.step()

    summary = {"counts": {"optimizer_updates": 0, "agent_transition_exposures": 0,
                          "selected_loss_agent_exposures": 0, "skipped_optimizer_chunks": 0}}
    fit = b01._fit(fitted, config, out, summary, input_root=source,
                   loss_mask="shield_inactive")
    assert fit["updates"] == 1 and fit["skipped_optimizer_chunks"] == 1
    assert fit["agent_transition_exposures"] == 128
    assert fit["selected_loss_agent_exposures"] == 32
    assert fit["mean_chunk_loss_weighted_by_selected_agent_steps"] == pytest.approx(
        manual_loss.item(), abs=1e-9)
    for name, param in actor.named_parameters():
        assert torch.equal(param, dict(fitted.skill_discoverer.actor.named_parameters())[name])
    assert fit["logstd_unchanged"] and fit["critic_coordinator_normalizers_unchanged"]

    # The one new final checkpoint uses the unchanged B01 evaluator loader contract.
    from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
    (out / "checkpoints").mkdir()
    saved = b02._save_final(fitted, config, out, "a" * 40, fit,
                            {"initial_checkpoint": {"sha256": "b" * 64}})
    record = saved["record"]
    task = ev.WorldTask(controller="L", seed=41, params=b01.PRODUCTION_PARAMS, horizon=12,
                        policy_seed=b01.MODEL_SEED, threads=1,
                        checkpoint=str(out / "checkpoints" / "final" / "agent.pt"),
                        checkpoint_record=str(out / "checkpoints" / "final" / "record.json"))
    eval_config = ev.learner_eval_config(ev.make_eval_config(12, b01.MODEL_SEED), record)
    restored, identity = ev.load_learner_policy(task, record, eval_config, torch.device("cpu"),
                                                 str(out / "logs"))
    assert identity["policy_fingerprint"] == record["policy_fingerprint"]
    assert b01.optimizer_steps(restored)["low_actor"] == 1


def test_paired_reading_retains_adverse_worlds():
    def row(seed, qos, reward, cost, zero):
        return {"seed": seed, "qos_per_step": qos, "raw_native_J": reward,
                "return_constraint_cost_raw_sum": cost,
                "episode_minimum_battery_ratio": .2, "cutoff_event_penalty_sum": 0.,
                "depletion_event_penalty_sum": 0., "cutoff_event_count_sum": 0.,
                "depletion_event_count_sum": 0., "zero_service": zero, "failed": False,
                "charger_input_wh": 0., "charging_uav_steps": 0,
                "feedback_mode_uav_steps": 0, "feedback_entry_count": 0,
                "feedback_exit_count": 0, "guard_checked_actions": 0,
                "guard_blocked_actions": 0, "first_service_step": None,
                "first_entry_step": None, "first_input_step": None,
                "steps_pre_entry": 12, "steps_entry_to_input": 0,
                "steps_post_input": 0, "qos_per_step_pre_entry": qos,
                "qos_per_step_entry_to_input": None, "qos_per_step_post_input": None}
    worlds = (41, 42)
    baseline = {"panels": {
        "teacher_eval": {"rows": [row(41,.5,50.,3.,False), row(42,.4,40.,3.,False)]},
        "initial_eval": {"rows": [row(41,.1,10.,1.,False), row(42,.1,10.,1.,False)]},
        "final_eval": {"rows": [row(41,.2,20.,2.,False), row(42,.3,30.,2.,False)]}}}
    revised = {"panels": {"final_eval": {"rows": [row(41,.3,25.,4.,False),
                                                   row(42,0.,-5.,3.,True)]}}}
    reading = b02._paired(baseline, revised, worlds)
    assert reading["new_zero_service_worlds"] == [42]
    assert reading["service_loss_worlds"] == [42]
    assert reading["J_loss_worlds"] == [42]
    assert reading["return_cost_increase_worlds"] == [41, 42]
    assert reading["worlds"][1]["revised_minus_b01_bc_qos_per_step"] == pytest.approx(-.3)


def test_admission_then_thread_caps_before_study(tmp_path, monkeypatch):
    from experiments.candidates.energy_relay_imitation import run_b02
    import scripts.hmasd_admission as admission

    sha = "a" * 40
    observed = []
    def admit(*_args, **_kwargs):
        observed.append("admission")
        return {"sha": sha}
    monkeypatch.setattr(admission, "require_admission", admit)
    for name in b01.THREAD_ENV:
        monkeypatch.setenv(name, "8")
    def study_run(**kwargs):
        observed.append("study")
        assert kwargs["seed"] == b01.MODEL_SEED
        assert all(__import__("os").environ[name] == "1" for name in b01.THREAD_ENV)
        return {"status": "COMPLETE"}
    monkeypatch.setattr(b02, "run_batch", study_run)
    assert run_b02.main(["--out", str(tmp_path / "out"), "--launch-sha", sha]) == 0
    assert observed == ["admission", "study"]
    assert not (tmp_path / "out").exists()
