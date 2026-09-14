"""Bounded engineering checks; the native factory is never invoked here."""
import copy
import json

import numpy as np
import pytest
import torch

from experiments.candidates.learned_counterfactual_agent_credit.lcac_b01 import learner, policy, study
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import recurrent_outputs


torch.set_num_threads(1)


class ToyAdapter:
    """Deliberately disagree with adapter scalar reward to check native reward binding."""
    def __init__(self, seed, horizon=4):
        self.horizon, self.commands, self.seeds = horizon, [], []
        self.closed = False

    def reset(self, seed=None):
        self.tick = 0
        self.seeds.append(seed)
        return self.observations(), {"state": self.state()}

    def observations(self):
        obs = np.zeros((5, 104), np.float32)
        obs[:, 0] = np.arange(5) / 10 + self.tick / 100
        return obs

    def state(self):
        result = np.zeros(116, np.float32)
        result[2:15:3] = 80
        result[-1] = self.tick / self.horizon
        return result

    def step(self, commands):
        self.commands.append(commands.copy())
        self.tick += 1
        reward = {f"uav_{i}": float(1 + commands[i, 0] * .2 + commands[i, 2] * .1)
                  for i in range(5)}
        return self.observations(), -999., False, self.tick == self.horizon, {
            "next_state": self.state(), "rewards_dict": reward}

    def close(self):
        self.closed = True


def episodes(actor):
    counts = learner.new_counts()
    env = ToyAdapter(1)
    rows = []
    data = [learner.collect_episode(env, actor, 4, 201 + i, 301 + i,
                                   dict(arm="Q", phase="train", episode=i),
                                   counts, rows.append, native=False) for i in range(2)]
    return data, counts, rows, env


def test_initialization_and_prefit_v_q_equivalence():
    before = torch.get_rng_state().clone()
    pair = policy.build_pair(19)
    assert torch.equal(before, torch.get_rng_state())
    av, v = pair["V"]
    aq, q = pair["Q"]
    for a, b in zip(av.parameters(), aq.parameters()):
        assert torch.equal(a, b) and a.data_ptr() != b.data_ptr()
    assert sum(p.numel() for p in v.parameters()) == 34177
    assert sum(p.numel() for p in q.parameters()) == 38657
    states = torch.linspace(-1, 1, 3 * 136).reshape(3, 136)
    actions = torch.arange(15).reshape(3, 5) % 7
    probs = torch.arange(1, 8).float().expand(3, 5, 7) / 28
    b, factual = policy.counterfactual_baseline(q, states, actions, probs)
    torch.testing.assert_close(factual, v(states), atol=2e-6, rtol=1e-5)
    torch.testing.assert_close(b, v(states)[:, None].expand(-1, 5), atol=2e-6, rtol=1e-5)


class AnalyticQ:
    def __init__(self):
        self.rows = 0

    def __call__(self, inputs):
        self.rows += inputs.numel() // 171
        onehot = inputs[..., 136:].reshape(*inputs.shape[:-1], 5, 7)
        assert torch.all(onehot.sum(-1) == 1)
        actions = (onehot * torch.arange(7)).sum(-1)
        return inputs[..., 0] + (actions.square() * torch.arange(1, 6)).sum(-1) + actions[..., 0] * actions[..., 1] * .3


def test_focal_enumeration_matches_independent_action_sum():
    states = torch.zeros(2, 136)
    states[:, 0] = torch.tensor([2., 9.])
    actions = torch.tensor([[0, 1, 2, 3, 4], [6, 5, 4, 3, 2]])
    probs = torch.arange(1, 71).float().reshape(2, 5, 7)
    probs /= probs.sum(-1, keepdim=True)
    critic = AnalyticQ()
    baseline, factual = policy.counterfactual_baseline(critic, states, actions, probs)
    assert critic.rows == 70
    expected = torch.zeros(2, 5)
    for row in range(2):
        for focal in range(5):
            for replacement in range(7):
                a = actions[row].tolist()
                a[focal] = replacement
                value = states[row, 0] + sum((i + 1) * x * x for i, x in enumerate(a)) + .3 * a[0] * a[1]
                expected[row, focal] += probs[row, focal, replacement] * value
    torch.testing.assert_close(baseline, expected)
    torch.testing.assert_close(factual, AnalyticQ()(policy.factual_inputs(states, actions)))
    altered = actions.clone()
    altered[:, 3] = (altered[:, 3] + 2) % 7
    alternative, _ = policy.counterfactual_baseline(AnalyticQ(), states, altered, probs)
    torch.testing.assert_close(alternative[:, 3], baseline[:, 3])


def test_seven_command_mapping_and_independent_draws(monkeypatch):
    torch.testing.assert_close(policy.COMMANDS, torch.tensor([
        [0, 0, 0], [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], dtype=torch.float32))
    seen = []
    def draws(shape, generator):
        seen.append(shape)
        return torch.tensor([[.01], [.2], [.4], [.6], [.99]])
    monkeypatch.setattr(torch, "rand", draws)
    actions, probs, logp = policy.sample_actions(torch.zeros(5, 7), torch.Generator())
    assert seen == [(5, 1)] and actions.tolist() == [0, 1, 2, 4, 6]
    torch.testing.assert_close(probs, torch.full((5, 7), 1 / 7))
    torch.testing.assert_close(logp, torch.full((5,), -np.log(7), dtype=torch.float32))


def test_collection_own_previous_command_and_native_reward():
    actor = policy.build_pair(21)["V"][0]
    data, counts, rows, env = episodes(actor)
    assert counts["native_transitions"] == 0 and counts["action_draws"] == 40
    assert counts["train_steps"] == 8
    for ep in range(2):
        assert torch.all(data[ep]["hidden"][0] == 0)
        assert torch.all(data[ep]["obs"][0, :, -4:] == 0)
        for tick in range(1, 4):
            np.testing.assert_array_equal(data[ep]["obs"][tick, :, -4:-1], env.commands[4 * ep + tick - 1])
        assert rows[ep]["J"] != -999 and rows[ep]["reward_sum"] == pytest.approx(float(data[ep]["reward"].sum()))
    paired, _, _, _ = episodes(copy.deepcopy(actor))
    for x, y in zip(data, paired):
        assert torch.equal(x["actions"], y["actions"])


def test_recurrent_chunk_order_and_private_initial_states():
    class Recurrence:
        def __call__(self, obs, hidden):
            outputs = []
            h = hidden.clone()
            for frame in obs:
                h = h + frame[:, :1]
                outputs.append(h[0].clone())
            values = torch.stack(outputs)
            return values[..., :7], values, h
    obs = torch.arange(2 * 4 * 5 * 108).reshape(2, 4, 5, 108).float() / 100
    hidden = torch.arange(2 * 4 * 5 * 64).reshape(2, 4, 5, 64).float()
    actual, _ = recurrent_outputs(Recurrence(), {"obs": obs, "hidden": hidden}, 2)
    expected = torch.empty(2, 4, 5, 7)
    for ep in range(2):
        for start in (0, 2):
            result, _, _ = Recurrence()(obs[ep, start:start + 2], hidden[ep, start][None])
            expected[ep, start:start + 2] = result
    torch.testing.assert_close(actual, expected)


def test_four_epochs_keep_prefit_detached_advantages_and_separate_clips(monkeypatch):
    actor, critic = policy.build_pair(23)["Q"]
    data, counts, _, _ = episodes(actor)
    original_prepare = learner.prepare_rollout
    prepared = []
    def prepare(*args):
        rollout, record = original_prepare(*args)
        prepared.append((rollout, rollout["advantage"].clone(), rollout["baseline"].clone()))
        return rollout, record
    monkeypatch.setattr(learner, "prepare_rollout", prepare)
    original_clip = torch.nn.utils.clip_grad_norm_
    groups = []
    def clip(parameters, bound):
        parameters = list(parameters)
        groups.append({id(p) for p in parameters})
        return original_clip(parameters, bound)
    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", clip)
    result = learner.update(actor, critic, learner.optimizer_for(actor, critic), data, "Q", counts, chunk=2)
    assert len(prepared) == 1 and len(groups) == 8
    assert groups[0].isdisjoint(groups[1])
    assert all(groups[i] == groups[i % 2] for i in range(8))
    rollout, old_adv, old_b = prepared[0]
    assert not rollout["advantage"].requires_grad
    assert torch.equal(old_adv, rollout["advantage"]) and torch.equal(old_b, rollout["baseline"])
    assert counts["optimizer_steps"] == 4 and counts["q_baseline_rows"] == 280
    assert counts["critic_fit_rows"] == 32
    assert result["movement"]["actor"]["displacement"] > 0
    assert result["movement"]["critic"]["displacement"] > 0
    assert all(e["critic_preclip_norm"] > 0 for e in result["epochs"])
    # The actor-only objective must not introduce critic gradients.
    critic.zero_grad(set_to_none=True)
    actor.zero_grad(set_to_none=True)
    logits, _ = recurrent_outputs(actor, rollout, 2)
    logp, _ = policy.action_terms(logits, rollout["actions"])
    learner.policy_loss(logp, rollout["logp"], rollout["advantage"]).backward()
    assert all(p.grad is None for p in critic.parameters())


def test_per_agent_mean_not_joint_ratio_or_agent_sum():
    ratio = torch.tensor([[[.5, 1., 1.5, 2., .9]]])
    adv = torch.tensor([[[1., -1., 2., -2., 3.]]])
    expected = -sum(min(float(r * a), float(torch.clamp(r, .8, 1.2) * a))
                    for r, a in zip(ratio.flatten(), adv.flatten())) / 5
    assert float(learner.policy_loss(ratio.log(), torch.zeros_like(ratio), adv)) == pytest.approx(expected)


def test_primary_all_worlds_units_and_pairing():
    rows = [dict(arm=a, phase="eval", episode=i, reset_seed=100 + i, action_seed=200 + i,
                 steps=256, J=2. + (i - 15) * .001 * (a == "Q"),
                 reward_sum=256 * (2. + (i - 15) * .001 * (a == "Q")))
            for a in ("V", "Q") for i in range(32)]
    result = study.primary(rows)
    assert result["delta"] == pytest.approx(.0005)
    assert result["adverse_worlds"] == 15 and len(result["differences"]) == 32
    assert result["reading"] == "WITHIN_MEI"
    with pytest.raises(ValueError):
        study.primary(rows[:-1])
    broken = copy.deepcopy(rows)
    broken[-1]["action_seed"] += 1
    with pytest.raises(ValueError):
        study.primary(broken)
    broken = copy.deepcopy(rows)
    broken[0]["J"] = float("nan")
    with pytest.raises(ValueError):
        study.primary(broken)
    broken = copy.deepcopy(rows)
    broken[0]["reward_sum"] = 0
    with pytest.raises(ValueError):
        study.primary(broken)


def test_complete_engineering_chain_counts_and_publication(tmp_path):
    from scripts.run_lcac_b02 import PLAN
    path = tmp_path / "pair"
    fixture = dict(PLAN, seed=29, env_factory=ToyAdapter, horizon=4,
                   train_episodes=2, eval_episodes=2, chunk=2, native=False)
    result = study.run_pair(path, **fixture)
    assert result["complete"], result.get("error")
    published = json.loads((path / "summary.json").read_text())
    assert published["complete"] and published["mode"] == "ENGINEERING_CHECK"
    assert published["object"] == PLAN["object_id"] and published["card"] == PLAN["card_path"]
    assert published["seed_offsets"]["eval_reset"] == 3000
    final = [json.loads(row) for row in (path / "episodes.jsonl").read_text().splitlines()
             if json.loads(row)["phase"] == "eval"]
    assert all(row["reset_seed"] == 100000 * 29 + 3000 + row["episode"] for row in final)
    assert len((path / "episodes.jsonl").read_text().splitlines()) == 8
    for arm in ("V", "Q"):
        assert (path / f"final_{arm}.pt").exists()
        c = result["arms"][arm]["counts"]
        assert c["native_transitions"] == 0 and c["train_steps"] == c["eval_steps"] == 8
        assert c["optimizer_steps"] == 4
    assert result["arms"]["Q"]["counts"]["q_baseline_rows"] == 280
    assert result["arms"]["V"]["counts"]["v_baseline_rows"] == 8


def test_b02_frozen_endpoint_is_disjoint_and_b01_defaults_remain():
    import inspect
    from scripts.run_lcac_b02 import PLAN
    assert PLAN["seed"] == 9412 and PLAN["train_episodes"] == 1024 and PLAN["eval_episodes"] == 32
    training = set(range(1000, 1000 + PLAN["train_episodes"]))
    final = set(range(PLAN["eval_reset_offset"], PLAN["eval_reset_offset"] + PLAN["eval_episodes"]))
    assert len(training & set(range(2000, 2032))) == 24
    assert training.isdisjoint(final)
    assert set(range(10000, 11024)).isdisjoint(range(20000, 20032))
    assert 2 * (len(training) + len(final)) * 256 == 540672
    defaults = inspect.signature(study.run_pair).parameters
    assert defaults["seed"].default == 9411 and defaults["train_episodes"].default == 256
    assert defaults["eval_reset_offset"].default == 2000
    assert defaults["object_id"].default == "LCAC_B01_256" and defaults["card_path"].default == study.CARD
