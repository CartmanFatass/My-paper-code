"""Synthetic S_eta contracts; no registered master fit or native environment."""
import copy
import json

import numpy as np
import pytest
import torch

from experiments.candidates.tail_return_distributional_learning.b03_eta import learner, metrics, study
from experiments.candidates.tail_return_distributional_learning.trdl_b01 import learner as old
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob

torch.set_num_threads(1)


def test_models_and_explicit_streams():
    before = torch.get_rng_state().clone()
    sa, sc = learner.models(17, "S_eta")
    qa, qc = learner.models(17, "Q32")
    oq_a, oq_c = old.models(17, "Q32")
    assert torch.equal(before, torch.get_rng_state())
    assert all(torch.equal(x, y) for x, y in zip(sa.parameters(), qa.parameters()))
    assert all(torch.equal(x, y) for x, y in zip(qa.parameters(), oq_a.parameters()))
    assert all(torch.equal(x, y) for x, y in zip(qc.parameters(), oq_c.parameters()))
    assert sc.trunk[0].in_features == 138 and sc.head.out_features == 1
    assert qc.trunk[0].in_features == 137 and qc.head.out_features == 32
    for arm, episode, offset in (("S_eta", None, 21), ("Q32", None, 22),
                                 ("S_eta", 3, 3003), ("Q32", 3, 6003)):
        assert learner.action_generator(17, arm, episode).initial_seed() == 1700000 + offset
    with pytest.raises(ValueError):
        learner.action_generator(17, "SCALAR")
    with pytest.raises(ValueError):
        learner.models(17, "unknown")


def test_frozen_eta_and_four_updates():
    actor, critic = learner.models(18, "S_eta")
    rng = torch.Generator().manual_seed(781)
    rollout = dict(obs=torch.randn(16, 4, 5, 108, generator=rng),
                   hidden=torch.randn(16, 4, 5, 64, generator=rng),
                   critic=torch.randn(16, 4, 137, generator=rng),
                   u=torch.randn(16, 4, 5, 3, generator=rng), G=torch.arange(16) / 20)
    with torch.no_grad():
        mean, _ = old.recurrent_outputs(actor, rollout, 2)
        rollout["logp"] = tanh_log_prob(rollout["u"], mean, actor.log_std)
    batch = learner.frozen_batch(critic, [{k: v[i] for k, v in rollout.items()} for i in range(16)])
    assert batch["eta"] == pytest.approx(.15)
    torch.testing.assert_close(batch["critic_eta"][..., -1], batch["eta"].expand(16, 4))
    torch.testing.assert_close(batch["baseline"], critic(batch["critic_eta"]))
    torch.testing.assert_close(batch["scores"], old.tail_score(batch["G"], batch["eta"]))
    torch.testing.assert_close(batch["advantages"], batch["scores"][:, None] - batch["baseline"])
    assert all(not x.requires_grad for x in batch.values())
    initial = copy.deepcopy(batch)
    actor_start = torch.cat([p.flatten() for p in actor.parameters()]).detach().clone()
    critic_start = torch.cat([p.flatten() for p in critic.parameters()]).detach().clone()
    with torch.no_grad():
        expected_mse = float((critic(batch["critic_eta"]) - batch["scores"][:, None]).square().mean())
    counts = study.old_study.new_counts()
    updates = []
    learner.update(actor, critic, old.optimizer_for(actor, critic), batch,
                   lambda: None, counts, updates.append, chunk=2)
    assert counts["optimizer_steps"] == counts["optimizer_attempts"] == 4
    assert updates[0]["critic_loss"] == pytest.approx(expected_mse)
    assert all(row["actor_grad_norm"] > 0 and row["critic_grad_norm"] > 0 for row in updates)
    for key in ("eta", "scores", "baseline", "advantages", "critic_eta"):
        torch.testing.assert_close(batch[key], initial[key])
    assert not torch.equal(actor_start, torch.cat([p.flatten() for p in actor.parameters()]))
    assert not torch.equal(critic_start, torch.cat([p.flatten() for p in critic.parameters()]))


class NativeInfoFixture:
    def __init__(self):
        self.env = self
        self.min_sinr = 3
        self.n_users = 4
        self.closed = False

    def reset(self, seed=None):
        return None, {}

    def step(self, actions):
        connections = np.array([[True, False, False, False], [False, True, False, False]])
        sinr = np.array([[18., 0., 0., 0.], [0., 33., 0., 0.]])
        global_info = dict(connections=connections, sinr_matrix=sinr, served_users=2)
        reward = .7 * 2 / 4 + .3 * (.5 + 1) / 2
        return None, 999., False, False, dict(infos_dict={"uav_0": {"global": global_info}},
                                             rewards_dict={f"uav_{i}": reward / 5 for i in range(5)})

    def close(self):
        self.closed = True


def test_native_components_verify_factual_reward():
    env = metrics.MeasuredEnv(NativeInfoFixture())
    env.reset()
    env.step(None)
    result = env.episode_metrics()
    assert result["served_users"] == 2
    assert result["service_component"] == pytest.approx(.35)
    assert result["sinr_quality"] == pytest.approx(.75)
    assert result["sinr_component"] == pytest.approx(.225)
    env.env.n_users = 5
    with pytest.raises(ValueError, match="dimensions"):
        env.step(None)


def test_fit_order_and_incomplete_batch(tmp_path, monkeypatch):
    calls = []
    def partial(master, arm, out, sha):
        calls.append((master, arm))
        return dict(status="incomplete", counts={"train_episodes": 3}, failure="fixture stop")
    monkeypatch.setattr(study, "run_fit", partial)
    result = study.run_batch(tmp_path / "batch", "fixture-sha")
    assert calls == [(9621, "S_eta")]
    assert result["status"] == "incomplete" and "pairs" not in result
    assert json.loads((tmp_path / "batch" / "summary.json").read_text())["fits"][0]["failure"] == "fixture stop"
    with pytest.raises(ValueError, match="fixed six"):
        study.read_batch(tmp_path / "batch")


def test_launcher_directory_accepted_but_scientific_outputs_not_reused(tmp_path, monkeypatch):
    out = tmp_path / "launcher-created"
    out.mkdir()
    (out / "launch-status.json").write_text("{}")
    monkeypatch.setattr(study, "run_fit", lambda *_: dict(status="incomplete", counts={}, failure="fixture"))
    assert study.run_batch(out, "fixture-sha")["status"] == "incomplete"
    assert (out / "launch-status.json").exists()
    with pytest.raises(FileExistsError, match="already exist"):
        study.run_batch(out, "fixture-sha")


def test_reader_uses_each_policy_own_tail_and_requires_complete_streams(tmp_path):
    out = tmp_path / "batch"
    (out / "raw").mkdir(parents=True)
    study.write_json(out / "summary.json", dict(status="incomplete", launch_sha="fixture-sha",
        fits=[dict(seed=m, arm=a, status="complete") for m, a in study.ORDER]))
    for master, arm in study.ORDER:
        folder = out / "raw" / f"{master}_{arm}"
        folder.mkdir()
        movement = {group: dict(parameters=10, initial_norm=1., final_norm=1.1,
                                displacement=.1, relative_displacement=.1)
                    for group in ("common_actor", "critic", "total")}
        study.write_json(folder / "summary.json", dict(status="complete", seed=master, arm=arm,
            launch_sha="fixture-sha", counts=dict(train_episodes=512, eval_episodes=256,
            optimizer_steps=128, team_steps=study.EXPECTED_STEPS), frozen_batches=[{}] * 32,
            learner_exposure=movement))
        with (folder / "episodes.jsonl").open("w") as handle:
            for e in range(512):
                handle.write(json.dumps(dict(arm=arm, seed=master, phase="train", episode=e,
                    reset_seed=100000 * master + 1000 + e, steps=256)) + "\n")
            for e in range(256):
                # Poor worlds occur at opposite ends; paired-difference tails are not the endpoint.
                J = (.1 if e < 64 else .9) if arm == "S_eta" else (.92 if e < 192 else .12)
                handle.write(json.dumps(dict(arm=arm, seed=master, phase="eval", episode=e,
                    reset_seed=100000 * master + 2000 + e, steps=256, J=J, served_users=4,
                    service_component=.05, sinr_quality=.2, sinr_component=.06)) + "\n")
        with (folder / "updates.jsonl").open("w") as handle:
            for update in range(128):
                handle.write(json.dumps(dict(arm=arm, seed=master, batch=update // 4, epoch=update % 4,
                                             optimizer_step=update + 1)) + "\n")
    result = study.read_batch(out)
    assert result["status"] == "complete"
    assert all(pair["delta_tail"] == pytest.approx(.02) for pair in result["pairs"])
    assert result["recurrence"] == "Q32_RECURRING"
    assert result["tail_contrast"]["mean"] == pytest.approx(.02)
    # Both files can retain correct episode/update order while belonging to the other arm.
    for name in ("episodes.jsonl", "updates.jsonl"):
        left = out / "raw" / "9621_S_eta" / name
        right = out / "raw" / "9621_Q32" / name
        left_data, right_data = left.read_bytes(), right.read_bytes()
        left.write_bytes(right_data)
        right.write_bytes(left_data)
        with pytest.raises(ValueError, match="training or update"):
            study.read_batch(out)
        left.write_bytes(left_data)
        right.write_bytes(right_data)
    fit_path = out / "raw" / "9621_S_eta" / "summary.json"
    fit = json.loads(fit_path.read_text())
    fit["learner_exposure"]["critic"]["displacement"] = 0
    fit["learner_exposure"]["critic"]["relative_displacement"] = 0
    study.write_json(fit_path, fit)
    assert study.read_batch(out)["status"] == "complete"
    del fit["learner_exposure"]["critic"]["displacement"]
    study.write_json(fit_path, fit)
    with pytest.raises(ValueError, match="invalid critic displacement"):
        study.read_batch(out)
    fit["learner_exposure"]["critic"]["displacement"] = 0
    study.write_json(fit_path, fit)
    # An incomplete update stream cannot inherit a completed status label.
    (out / "raw" / "9621_S_eta" / "updates.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="training or update"):
        study.read_batch(out)


@pytest.mark.parametrize("meter_failure", ("exception", "nonfinite"))
def test_failed_movement_measurement_quarantines_endpoint(tmp_path, monkeypatch, meter_failure):
    monkeypatch.setattr(study, "ORDER", ((19, "S_eta"),))
    monkeypatch.setattr(study, "make_real", lambda _seed: NativeInfoFixture())
    if meter_failure == "exception":
        monkeypatch.setattr(study, "exposure", lambda *_: (_ for _ in ()).throw(RuntimeError("fixture meter failed")))
    else:
        movement = {group: dict(parameters=10, initial_norm=1., final_norm=1.1,
                                displacement=float("nan"), relative_displacement=.1)
                    for group in ("common_actor", "critic", "total")}
        monkeypatch.setattr(study, "exposure", lambda *_: movement)
    monkeypatch.setattr(learner, "frozen_batch", lambda *_: dict(
        eta=torch.tensor(.2), scores=torch.zeros(16),
        baseline=torch.zeros(16, 256), advantages=torch.zeros(16, 256)))
    def fake_collect(_env, _actor, reset_seed, _rng, phase, episode, _check, counts, emit):
        counts["team_steps"] += 256
        counts[f"{phase}_episodes"] += 1
        row = dict(phase=phase, episode=episode, reset_seed=reset_seed, steps=256,
                   J=.2, served_users=4, service_component=.1,
                   sinr_quality=1/3, sinr_component=.1)
        emit(row)
        return {}, row
    def fake_update(_actor, _critic, _optimizer, _batch, _check, counts, emit):
        counts["optimizer_attempts"] += 4
        counts["optimizer_steps"] += 4
        for epoch in range(4):
            emit(dict(epoch=epoch, optimizer_step=counts["optimizer_steps"] - 3 + epoch,
                      grad_norm=.1))
    monkeypatch.setattr(study, "collect_measured", fake_collect)
    monkeypatch.setattr(learner, "update", fake_update)
    result = study.run_fit(19, "S_eta", tmp_path / "fit", "fixture-sha")
    assert result["status"] == "incomplete"
    assert result["counts"]["train_episodes"] == 512
    assert result["counts"]["eval_episodes"] == 256
    assert result["counts"]["optimizer_steps"] == 128
    assert result["endpoint"]["lower_tail"] == pytest.approx(.2)
    assert ("fixture meter failed" if meter_failure == "exception" else
            "invalid common_actor displacement movement evidence") == result["learner_exposure_error"]
    assert "learner_exposure" not in result
    assert "movement evidence" in result["failure"]
    assert (tmp_path / "fit" / "episodes.jsonl").exists()


def test_own_tail_and_descriptive_training_interval():
    scalar = [0.1] * 64 + [0.9] * 192
    quantile = [0.9] * 192 + [0.12] * 64
    assert old.endpoint(quantile)["lower_tail"] - old.endpoint(scalar)["lower_tail"] == pytest.approx(.02)
    assert min(np.array(quantile) - np.array(scalar)) == pytest.approx(-.78)
    interval = study._interval([.01, .02, .03])
    assert interval["mean"] == pytest.approx(.02)
    assert interval["sd"] == pytest.approx(.01)


def test_cli_admission_precedes_import_and_output(tmp_path, monkeypatch):
    from experiments.candidates.tail_return_distributional_learning.b03_eta import run
    calls = []
    import scripts.hmasd_admission as admission
    def deny(*args, **kwargs):
        calls.append((args, kwargs))
        raise RuntimeError("fixture admission denied")
    monkeypatch.setattr(admission, "require_admission", deny)
    out = tmp_path / "absent"
    with pytest.raises(RuntimeError, match="admission denied"):
        run.main(["batch", "--out", str(out), "--launch-sha", "fixture-sha"])
    assert len(calls) == 1 and not out.exists()
