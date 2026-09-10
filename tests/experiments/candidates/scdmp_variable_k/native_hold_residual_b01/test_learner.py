import copy

import pytest
import torch

from experiments.candidates.scdmp_variable_k.native_hold_residual_b01 import learner
from experiments.candidates.ucope.uav_motion_prefix_b01 import learner as source, policy
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.study import new_counts


def test_pair_mask_episode_reward_interval_and_both_gradients():
    cx = torch.zeros(2, 8, 136)
    cx[0, 1:4, 119] = torch.tensor([.75, .5, .25])
    cx[0, 1:4, 123] = 1  # Multiple holders still produce one team pair.
    cx[1, 2, 135] = .25
    cx[:, 5, 119] = 1  # Out-of-opening support is excluded.
    reward = torch.tensor([[1., 2., 3., 4., 100., 6., 7., 8.],
                           [10., 20., 30., 40., 1000., 60., 70., 80.]])
    indices, interval = learner.segment_pairs(dict(critic=cx, reward=reward))
    assert indices.tolist() == [[0,1], [0,2], [0,3], [1,2]]
    assert interval.tolist() == [9,7,4,70]
    values = torch.zeros(2,8,requires_grad=True)
    loss = learner.residual_loss(values, indices, interval)
    assert loss.item() == pytest.approx((81+49+16+4900)/4)
    loss.backward()
    expected = torch.zeros(2,8)
    expected[0,1:4] = torch.tensor([-4.5,-3.5,-2.])
    expected[0,4] = 10
    expected[1,2], expected[1,4] = -35,35
    torch.testing.assert_close(values.grad, expected)
    targets = source.returns_to_go(reward)
    for (e,t), r in zip(indices, interval):
        assert targets[e,t] == r + targets[e,4]


def test_no_pair_zero():
    indices, interval = learner.segment_pairs(dict(critic=torch.zeros(2,8,136), reward=torch.ones(2,8)))
    values = torch.ones(2,8,requires_grad=True)
    loss = learner.residual_loss(values,indices,interval)
    assert loss.item() == 0 and len(indices) == 0
    loss.backward()
    assert not values.grad.any()


def recorded_rollout():
    actor, critic = policy.arm_copy(policy.templates(9001), True)
    episodes=[]
    for e in range(2):
        episodes.append(source.collect_episode(SyntheticAdapter(10),actor,critic,8,20+e,
            policy.generator(30+e),policy.generator(40+e),dict(arm="fixture",phase="train",episode=e),
            lambda:None,new_counts(),lambda row:None,lambda row:None,[],ratio_grouping="agent_compound"))
    return actor,critic,episodes


def test_full_mc_comparator_matches_source_and_fixed_advantages(monkeypatch):
    torch.set_num_threads(1)
    actor,critic,episodes=recorded_rollout()
    a2,c2=copy.deepcopy((actor,critic))
    source_counts,new=new_counts(),new_counts()
    original=source.update(actor,critic,source.optimizer_for(actor,critic),episodes,8,lambda:None,
                           source_counts,ratio_grouping="agent_compound")
    seen=[]
    def observe(logp,old,advantages,mask):
        seen.append(advantages.clone())
        assert not advantages.requires_grad
        return source.clipped_policy_loss(logp,old,advantages,mask)
    monkeypatch.setattr(learner,"clipped_policy_loss",observe)
    actual=learner.update(a2,c2,source.optimizer_for(a2,c2),episodes,8,lambda:None,new,residual=False)
    for x,y in zip(list(actor.parameters())+list(critic.parameters()),list(a2.parameters())+list(c2.parameters())):
        torch.testing.assert_close(x,y,rtol=0,atol=0)
    for x,y in zip(original,actual):
        assert all(x[k]==y[k] for k in x)
    rewards=torch.stack([e["reward"] for e in episodes])
    raw=source.returns_to_go(rewards)-torch.stack([e["value"] for e in episodes])
    expected=(raw-raw.mean())/(raw.std(unbiased=False)+1e-8)
    assert len(seen)==4 and new["optimizer_steps"]==source_counts["optimizer_steps"]==4
    for v in seen: torch.testing.assert_close(v,expected)
    assert sum(p.numel() for p in list(a2.parameters())+list(c2.parameters()))==66441


def test_treatment_actor_terms_fixed_advantages_and_forward_count(monkeypatch):
    torch.set_num_threads(1)
    actor,critic,episodes=recorded_rollout()
    for ep in episodes: ep["critic"][1:4,119]=torch.tensor([.75,.5,.25])
    a2,c2=copy.deepcopy((actor,critic))
    seen=[]
    def observe(logp,old,advantages,mask):
        seen.append((advantages.clone(),mask.clone()))
        return source.clipped_policy_loss(logp,old,advantages,mask)
    monkeypatch.setattr(learner,"clipped_policy_loss",observe)
    calls=[]
    handle=critic.register_forward_hook(lambda *args:calls.append(1))
    records=learner.update(actor,critic,source.optimizer_for(actor,critic),episodes,8,lambda:None,new_counts(),residual=True)
    handle.remove()
    baseline=learner.update(a2,c2,source.optimizer_for(a2,c2),episodes,8,lambda:None,new_counts(),residual=False)
    assert len(calls)==4 and all(r["eligible_pairs"]==r["residual_terms"]==6 for r in records)
    assert records[0]["policy_loss"]==baseline[0]["policy_loss"]
    assert records[0]["entropy"]==baseline[0]["entropy"]
    assert records[0]["value_loss"]==baseline[0]["value_loss"]
    for adv,mask in seen:
        torch.testing.assert_close(adv,seen[0][0])
        assert torch.equal(mask,seen[0][1])
    assert any(not torch.equal(x,y) for x,y in zip(critic.parameters(),c2.parameters()))
