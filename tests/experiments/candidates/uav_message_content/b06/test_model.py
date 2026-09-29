import hashlib
import io
import math

import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    Actor as BaseActor, Critic as BaseCritic, sample_actions,
)
from experiments.candidates.uav_message_content.b05 import model as b05
from experiments.candidates.uav_message_content.b06 import model
from experiments.candidates.uav_message_content.b06.update import optimizers_for, update_motion
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import recurrent_outputs
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob


def _checkpoint(monkeypatch):
    source_actor, source_critic = BaseActor(), BaseCritic()
    state = dict(actor=source_actor.state_dict(), critic=source_critic.state_dict(), arm="B",
                 master=model.SOURCE_MASTER, input_size=171, critic_size=451,
                 inherited_sha256=model.SOURCE_INHERITED_SHA256)
    buffer = io.BytesIO()
    torch.save(state, buffer)
    content = buffer.getvalue()
    digest = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(b05, "SOURCE_SHA256", digest)
    return content, digest


def test_zero_identity_shared_calibration_and_composed_density(monkeypatch):
    content, digest = _checkpoint(monkeypatch)
    actor, critic = model.build_arm(19701, "K")
    model.load_warm_start(actor, critic, content, digest)
    base, base_critic = model.load_base(content, digest)
    x = torch.randn(2, 5, model.ACTOR_SIZE)
    h = torch.randn(1, 5, 64)
    mean, recurrent, next_h, base_mean, correction = actor.components(x, h)
    old_mean, old_recurrent, old_h = base(x[..., :171], h)
    assert torch.equal(mean, old_mean)
    assert torch.equal(base_mean, old_mean)
    assert torch.equal(recurrent, old_recurrent)
    assert torch.equal(next_h, old_h)
    assert torch.count_nonzero(correction) == 0
    cx = torch.randn(526)
    assert torch.equal(critic(cx), base_critic(cx[:451]))
    rng = torch.Generator().manual_seed(7)
    sampled, sent = sample_actions(actor, mean[0], recurrent[0], torch.ones(5, dtype=torch.bool),
                                   0, rng, None)
    old_sampled, old_sent = sample_actions(base, old_mean[0], old_recurrent[0],
                                           torch.ones(5, dtype=torch.bool), 0,
                                           torch.Generator().manual_seed(7), None)
    assert torch.equal(sampled, old_sampled)
    assert torch.equal(sent, old_sent)
    with torch.no_grad():
        actor.b.copy_(torch.tensor([2., -1., .5]))
    changed = x.clone()
    changed[..., 171:] += 50
    active, _, _, active_base, delta = actor.components(changed, h)
    expected = model.CORRECTION_BOUND * actor.b.tanh()
    assert torch.equal(delta, expected.expand_as(delta))
    assert torch.all(delta.abs() <= model.CORRECTION_BOUND)
    assert torch.equal(active_base, base_mean)
    assert torch.allclose(active - active_base, delta, atol=1e-7)
    u = active[0] + torch.randn_like(active[0]) * .2
    logp, entropy = model.motion_terms(actor, active[0], u)
    normal = torch.distributions.Normal(active[0], actor.log_std.clamp(-5, 2).exp())
    jacobian = 2 * (math.log(2) - u - torch.nn.functional.softplus(-2 * u))
    assert torch.allclose(logp, (normal.log_prob(u) - jacobian).sum(-1), atol=2e-6)
    assert torch.equal(logp, tanh_log_prob(u, active[0], actor.log_std))
    assert entropy.shape == ()


def test_pair_warm_start_counts_and_rng_isolation(monkeypatch):
    content, digest = _checkpoint(monkeypatch)
    torch.manual_seed(91)
    global_before = torch.random.get_rng_state()
    motion = torch.Generator().manual_seed(1970100021)
    motion_before = motion.get_state()
    k_actor, k_critic = model.build_arm(19701, "K")
    d_actor, d_critic = model.build_arm(19701, "D")
    assert torch.equal(torch.random.get_rng_state(), global_before)
    assert torch.equal(motion.get_state(), motion_before)
    assert torch.equal(torch.randn(9, generator=motion),
                       torch.randn(9, generator=torch.Generator().manual_seed(1970100021)))
    assert type(d_actor) is b05.Actor
    fresh_k = model.parameter_snapshot(k_actor, k_critic)
    fresh_d = model.parameter_snapshot(d_actor, d_critic)
    for key in ("base_actor", "critic_old", "critic_forecast"):
        assert torch.equal(fresh_k[key], fresh_d[key])
    model.load_warm_start(k_actor, k_critic, content, digest)
    model.load_warm_start(d_actor, d_critic, content, digest)
    k = model.parameter_snapshot(k_actor, k_critic)
    d = model.parameter_snapshot(d_actor, d_critic)
    for key in ("base_actor", "critic_old", "critic_forecast"):
        assert torch.equal(k[key], d[key])
    assert k["calibration"].numel() == 3 and torch.count_nonzero(k["calibration"]) == 0
    assert d["residual_hidden"].numel() + d["residual_output"].numel() == 16259
    assert torch.count_nonzero(d["residual_output"]) == 0
    assert torch.count_nonzero(k["critic_forecast"]) == 0
    for actor, critic, expected_lr, trainable in ((k_actor, k_critic, 3e-3, 3),
                                                   (d_actor, d_critic, 3e-4, 16259)):
        actor_opt, critic_opt = optimizers_for(actor, critic)
        actor_params = [p for group in actor_opt.param_groups for p in group["params"]]
        critic_params = [p for group in critic_opt.param_groups for p in group["params"]]
        assert sum(p.numel() for p in actor_params) == trainable
        assert {id(p) for p in actor_params} == {id(p) for p in actor.parameters() if p.requires_grad}
        assert {id(p) for p in critic_params} == {id(p) for p in critic.parameters()}
        assert not any(p.requires_grad for p in actor.base.parameters())
        assert actor_opt.param_groups[0]["lr"] == expected_lr
        assert critic_opt.param_groups[0]["lr"] == 3e-4
        for opt in (actor_opt, critic_opt):
            assert len(opt.state) == 0
            group = opt.param_groups[0]
            assert group["betas"] == (.9, .999) and group["eps"] == 1e-8
            assert group["weight_decay"] == 0
    with pytest.raises(ValueError, match="cell"):
        model.build_arm(19704, "K")
    with pytest.raises(ValueError, match="cell"):
        model.build_arm(19701, "B40")


def _episodes(actor):
    motion = torch.Generator().manual_seed(109)
    rows = []
    for episode in range(2):
        x = torch.randn(32, 5, model.ACTOR_SIZE) * .1
        h = torch.zeros(1, 5, 64)
        last = torch.zeros(5, 3)
        hidden, pre_tanh, logps, values = [], [], [], []
        for t in range(32):
            x[t, :, 104:107] = last
            hidden.append(h[0].clone())
            with torch.no_grad():
                mean, _, h = actor(x[t:t + 1], h)
                u = mean[0] + torch.randn(5, 3, generator=motion) * .2
                logp, _ = model.motion_terms(actor, mean[0], u)
            pre_tanh.append(u)
            logps.append(logp)
            values.append(torch.zeros(()))
            last = u.tanh()
        rows.append(dict(obs=x, hidden=torch.stack(hidden), critic=torch.randn(32, 526) * .1,
                         u=torch.stack(pre_tanh), logp=torch.stack(logps),
                         value=torch.stack(values),
                         reward=torch.linspace(.05, .25, 32) + episode * .01))
    return rows


@pytest.mark.parametrize("arm", ["K", "D"])
def test_recurrent_replay_update_and_frozen_parent(arm):
    actor, critic = model.build_arm(19701, arm)
    episodes = _episodes(actor)
    replay, _ = recurrent_outputs(actor, {key: torch.stack([ep[key] for ep in episodes])
                                          for key in ("obs", "hidden")}, 32)
    old_logp, _ = model.motion_terms(actor, replay, torch.stack([ep["u"] for ep in episodes]))
    assert torch.allclose(old_logp, torch.stack([ep["logp"] for ep in episodes]),
                          atol=2e-6, rtol=2e-6)
    initial = model.parameter_snapshot(actor, critic)
    actor_opt, critic_opt = optimizers_for(actor, critic)
    counts, records = {}, []
    update_motion(actor, critic, actor_opt, critic_opt, episodes, counts, lambda: None,
                  records.append)
    moved = model.exposure(initial, actor, critic)
    assert moved["base_actor"]["displacement"] == 0
    assert moved["calibration" if arm == "K" else "residual_output"]["displacement"] > 0
    assert moved["critic_old"]["displacement"] > 0
    assert moved["critic_forecast"]["displacement"] > 0
    assert all(p.grad is None for p in actor.base.parameters())
    assert counts["actor_optimizer_steps"] == counts["critic_optimizer_steps"] == 4
    assert counts["replayed_actor_rows"] == counts["ppo_actor_forward_rows"] == 1280
    assert counts["ppo_critic_forward_rows"] == 256
    assert len(records) == 4
    assert all(math.isfinite(row["actor_grad_norm"]) and math.isfinite(row["critic_grad_norm"])
               for row in records)
