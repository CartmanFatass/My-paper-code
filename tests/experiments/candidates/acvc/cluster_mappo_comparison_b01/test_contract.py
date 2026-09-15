"""Synthetic-only checks of the new numerical, information and publication paths."""
import copy
import json
import os
import sys

import pytest

from scripts import run_acvc_fresh_dense_reuse_b01 as shared
from scripts import run_acvc_cluster_mappo_comparison_b01 as runner
from experiments.candidates.acvc.cluster_mappo_comparison_b01 import protocol as p
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter

sys.path.insert(0, os.environ["HMASD_ON_POLICY_ROOT"])
from experiments.candidates.acvc.cluster_mappo_comparison_b01 import mappo as m

np, torch = m.np, m.torch


def fixture_policy(horizon=32):
    args, _ = m.configuration()
    args.episode_length = horizon
    policy, spaces = m.make_policy(args)
    return args, policy, m.make_buffer(args, spaces)


def test_joint_density_is_scalar_stable_and_head_is_optimized():
    _, policy, buffer = fixture_policy()
    head = policy.actor.act
    x = torch.zeros(2, 64)
    raw = torch.tensor([[.2, -.4, .8], [30., -30., .1]])
    logp, entropy = head.evaluate_actions(x, raw)
    expected = m.tanh_log_prob(raw, head.mean(x), head.log_std).unsqueeze(-1)
    assert logp.shape == (2, 1) and buffer.action_log_probs.shape[-1] == 1
    assert torch.equal(logp, expected) and torch.isfinite(logp).all()
    assert entropy.item() == pytest.approx(3 * .5 * np.log(2 * np.pi * np.e))
    parameters = {id(v) for group in policy.actor_optimizer.param_groups for v in group["params"]}
    assert parameters == {id(v) for v in policy.actor.parameters()}
    assert all(id(v) in parameters for v in head.parameters())
    (-logp.mean()).backward()
    assert all(torch.isfinite(v.grad).all() for v in head.parameters())


def test_private_actor_and_own_recurrent_state_do_not_receive_global_or_other_rows():
    _, policy, _ = fixture_policy()
    obs, info = SyntheticAdapter(8).reset(9)
    own, global_a = m.features(obs, info["state"], np.zeros((5, 3), np.float32))
    _, global_b = m.features(obs, info["state"] + 17, np.zeros((5, 3), np.float32))
    hidden, masks = np.zeros((5, 1, 64), np.float32), np.ones((5, 1), np.float32)
    with torch.no_grad():
        a = policy.get_actions(global_a, own, hidden, hidden, masks, deterministic=True)
        b = policy.get_actions(global_b, own, hidden, hidden, masks, deterministic=True)
        changed = own.copy()
        changed[3] += .4
        h_changed = hidden.copy()
        h_changed[3] = .5
        c, _ = policy.act(changed, h_changed, masks, deterministic=True)
    assert torch.equal(a[1], b[1]) and not torch.equal(a[0], b[0])
    assert torch.equal(a[1][[0, 1, 2, 4]], c[[0, 1, 2, 4]])
    assert not torch.equal(a[1][3], c[3])


def test_native_tuple_adapter_terminal_gae_and_chunk_replay_likelihood():
    args, policy, buffer = fixture_policy(64)
    trainer = m.R_MAPPO(args, policy)
    rows, counts = [], shared._counts()
    envs = [SyntheticAdapter(10 + i, horizon=64) for i in range(2)]
    m.fill_rollout(policy, buffer, envs, (0, 1), counts, rows.append)
    assert counts["train_episodes"] == 2 and counts["train_team_steps"] == 128
    assert [r["reset_seed"] for r in rows] == [100000 * p.MASTER + 1000 + i for i in range(2)]
    assert not buffer.masks[0].any() and not buffer.masks[-1].any()
    assert buffer.masks[1:-1].all() and not buffer.rnn_states[-1].any()
    assert np.allclose(buffer.obs[1:, :, :, -4:-1], np.tanh(buffer.actions), atol=1e-7)
    assert not buffer.obs[..., -1].any()
    # A terminal next value cannot enter GAE, even if an erroneous large value is supplied.
    buffer.compute_returns(np.full((2, 5, 1), 12345., np.float32), trainer.value_normalizer)
    assert np.allclose(buffer.returns[-2], buffer.rewards[-1], atol=1e-5)
    assert np.allclose(buffer.rewards[:, :, 0], buffer.rewards[:, :, 4])
    sample = next(buffer.recurrent_generator(np.zeros_like(buffer.rewards), 1, 32))
    with torch.no_grad():
        _, logp, _ = policy.evaluate_actions(*sample[:5], sample[7], sample[11], sample[8])
    assert logp.shape == (640, 1)
    assert np.allclose(logp.numpy(), sample[9], atol=3e-6, rtol=3e-6)


def test_all_80_chunks_keep_lane_agent_time_and_pre_observation_state():
    _, _, buffer = fixture_policy(256)
    for t in range(256):
        for lane in range(2):
            for agent in range(5):
                address = 10000 * lane + 1000 * agent + t
                buffer.obs[t, lane, agent, 0] = address
                buffer.rnn_states[t, lane, agent, 0, 0] = address
                buffer.masks[t, lane, agent, 0] = t != 0
    sample = next(buffer.recurrent_generator(np.zeros_like(buffer.rewards), 1, 32))
    chunks = sample[1][:, 0].reshape(32, 80)
    assert np.all(np.diff(chunks, axis=0) == 1)
    assert len(set(chunks[0])) == 80
    assert np.array_equal(chunks[0], sample[2][:, 0, 0])
    assert np.array_equal(sample[7][:, 0].reshape(32, 80)[0], (chunks[0] % 1000) != 0)


def test_actual_separate_updates_checkpoint_and_actor_only_evaluation(tmp_path, monkeypatch):
    args, policy, buffer = fixture_policy()
    trainer = m.R_MAPPO(args, policy)
    counts, rows = shared._counts(), []
    initial = m.parameter_snapshot(policy)
    m.count_steps(policy.actor_optimizer, counts, "actor_optimizer_steps")
    m.count_steps(policy.critic_optimizer, counts, "critic_optimizer_steps")
    m.fill_rollout(policy, buffer, [SyntheticAdapter(i, horizon=32) for i in (1, 2)], (0, 1), counts, rows.append)
    buffer.compute_returns(np.zeros((2, 5, 1), np.float32), trainer.value_normalizer)
    trainer.prep_training()
    info = trainer.train(buffer)
    assert counts["optimizer_steps"] == 8
    assert counts["actor_optimizer_steps"] == counts["critic_optimizer_steps"] == 4
    assert all(float(value) == pytest.approx(float(value)) for value in info.values())
    exposure = m.parameter_exposure(initial, policy)
    assert all(v["finite"] and v["displacement"] > 0 for v in exposure.values())
    saved = dict(actor=policy.actor.state_dict(), critic=policy.critic.state_dict(),
                 value_normalizer=trainer.value_normalizer.state_dict())
    torch.save(saved, tmp_path / "final.pt")
    checkpoint = torch.load(tmp_path / "final.pt", weights_only=True)
    with torch.no_grad():
        next(policy.actor.parameters()).add_(1)
    policy.actor.load_state_dict(checkpoint["actor"])
    policy.critic.load_state_dict(checkpoint["critic"])
    trainer.value_normalizer.load_state_dict(checkpoint["value_normalizer"])
    assert all(torch.equal(v, policy.actor.state_dict()[k]) for k, v in checkpoint["actor"].items())
    norm_before = copy.deepcopy(trainer.value_normalizer.state_dict())
    monkeypatch.setattr(policy.critic, "forward", lambda *_a, **_k: pytest.fail("critic used in execution"))

    class PrivateOnly(SyntheticAdapter):
        def reset(self, seed=None):
            obs, _ = super().reset(seed)
            return obs, {}

        def step(self, action):
            obs, scalar, terminal, trunc, info = super().step(action)
            del info["next_state"]
            return obs, scalar, terminal, trunc, info

    m.evaluate(policy, PrivateOnly(5, horizon=8), 0, counts, rows.append, horizon=8)
    assert counts["eval_team_steps"] == 8 and counts["optimizer_steps"] == 8
    assert all(torch.equal(v, trainer.value_normalizer.state_dict()[k]) for k, v in norm_before.items())
    assert rows[-1]["J"] == rows[-1]["S"] / 8


def test_c_reuse_keeps_selected_learning_calls_and_three_final_loads(tmp_path, monkeypatch):
    from experiments.candidates.acvc.cluster_mappo_comparison_b01 import c_fit

    monkeypatch.setattr(c_fit, "TRAIN_EPISODES", 2)
    monkeypatch.setattr(c_fit, "EVAL_EPISODES", 1)
    monkeypatch.setattr(c_fit, "HORIZON", 32)
    monkeypatch.setattr(c_fit, "make_cluster", lambda seed: SyntheticAdapter(seed, horizon=32))
    original_collect, original_update = shared.collect_episode, shared.update

    def collect(*args, **kwargs):
        assert kwargs == dict(real=True, diagnostics=False, ratio_grouping="agent_compound", value_moments=None,
                              renewal=False, duration_support=(1, 4), velocity_mode="sampled")
        return original_collect(*args, **kwargs)

    def update(*args, **kwargs):
        assert args[4] == 32 and args[2].param_groups[0]["lr"] == 3e-4
        assert args[2].param_groups[0]["eps"] == 1e-8
        assert kwargs == dict(ratio_grouping="agent_compound", entropy_coef=.01, value_moments=None)
        return original_update(*args, **kwargs)

    monkeypatch.setattr(shared, "collect_episode", collect)
    monkeypatch.setattr(shared, "update", update)
    summary = dict(counts=shared._counts(), configuration={}, limits=[])
    rows, updates = [], []
    c_fit.execute(tmp_path, summary, rows.append, updates.append, lambda: None)
    assert summary["fit_complete"] and summary["counts"]["optimizer_steps"] == 4
    assert summary["counts"]["final_checkpoints"] == 1 and summary["counts"]["post_fit_loads"] == 3
    assert [r["arm"] for r in rows if r["phase"] == "eval"] == ["C", "F", "dwell"]
    assert len(updates) == 4


def bound_summary(fit):
    counts = dict(train_episodes=4096, train_team_steps=1048576, rollouts=2048, final_checkpoints=1,
                  optimizer_steps=8192 if fit == "C" else 16384, actor_optimizer_steps=8192, critic_optimizer_steps=8192)
    panels = {arm: dict(complete=True, scores_J=[0.] * 64) for arm in p.ARMS[fit]}
    return dict(object=p.OBJECT, master=p.MASTER, evaluation_namespace=p.EVALUATION_NAMESPACE,
                arm=fit, fit_complete=True, counts=counts, panels=panels)


@pytest.mark.parametrize("value,label", [(.010001, "F_ABOVE_MEI"), (.01, "WITHIN_MEI"),
                                       (0., "WITHIN_MEI"), (-.01, "WITHIN_MEI"), (-.010001, "M_ABOVE_MEI")])
def test_unrounded_strict_primary_and_inclusive_mei(value, label):
    assert p.contrast([value] * 64, [0.] * 64, primary=True)["reading"] == label


def test_offline_publication_preserves_adverse_worlds_and_independent_partial_operands(tmp_path):
    c, m_summary = bound_summary("C"), bound_summary("M")
    c["panels"]["F"]["scores_J"] = [-.2] + [.03] * 63
    input_path = tmp_path / "c.json"
    input_path.write_text(json.dumps(c), encoding="utf-8")
    assert runner.main(["--mode", "reduce", "--c-summary", str(input_path), "--output", str(tmp_path / "reduce")]) == 0
    partial = json.loads((tmp_path / "reduce" / "summary.json").read_text())
    assert partial["contrasts"]["F-M"]["reading"] == "INCOMPLETE"
    assert partial["contrasts"]["F-C"]["complete"] and partial["contrasts"]["F-dwell"]["complete"]
    result = p.reduce_pair({"C": c, "M": m_summary})
    assert result["contrasts"]["F-M"]["adverse"] == 1
    assert result["contrasts"]["F-M"]["minimum_J"] == -.2
    m_summary["counts"]["actor_optimizer_steps"] -= 1
    assert p.reduce_pair({"C": c, "M": m_summary})["contrasts"]["F-M"]["reading"] == "INCOMPLETE"


@pytest.mark.parametrize("defect", ["duplicate", "wrong_seed", "wrong_snapshot", "short", "nonfinite"])
def test_panel_rejects_incomplete_bound_evaluation_operand(defect):
    rows = [dict(phase="eval", arm="M", episode=i, master=p.MASTER, evaluation_namespace=p.EVALUATION_NAMESPACE,
                 checkpoint_episode=4096, reset_seed=100000 * p.EVALUATION_NAMESPACE + 2000 + i,
                 steps=256, S=25.6, J=.1) for i in range(64)]
    assert p.panel(rows, "M")["complete"]
    if defect == "duplicate":
        rows[-1] = rows[0].copy()
    elif defect == "wrong_seed":
        rows[0]["reset_seed"] += 1
    elif defect == "wrong_snapshot":
        rows[0]["checkpoint_episode"] = 1024
    elif defect == "short":
        rows[0]["steps"] = 255
    else:
        rows[0]["S"] = float("nan")
    assert not p.panel(rows, "M")["complete"]
