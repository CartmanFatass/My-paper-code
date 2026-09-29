import hashlib
import io
import math

import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    Actor as BaseActor, Critic as BaseCritic, sample_actions,
)
from experiments.candidates.uav_message_content.b05 import model
from experiments.candidates.uav_message_content.b05.update import optimizers_for, update_motion
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import recurrent_outputs
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob


def _checkpoint(monkeypatch, **changes):
    source_actor, source_critic = BaseActor(), BaseCritic()
    state = dict(actor=source_actor.state_dict(), critic=source_critic.state_dict(), arm="B",
                 master=model.SOURCE_MASTER, input_size=171, critic_size=451,
                 inherited_sha256=model.SOURCE_INHERITED_SHA256)
    state.update(changes)
    buffer = io.BytesIO()
    torch.save(state, buffer)
    content = buffer.getvalue()
    digest = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(model, "SOURCE_SHA256", digest)
    return content, digest, source_actor, source_critic


def test_zero_residual_base_identity_and_forecast_isolation(monkeypatch):
    content, digest, _, _ = _checkpoint(monkeypatch)
    actor, critic = model.build_arm(19601, "M_G")
    model.load_warm_start(actor, critic, content, digest)
    base, base_critic = model.load_base(content, digest)
    x = torch.randn(1, 5, 186)
    cx = torch.randn(526)
    h = torch.randn(1, 5, 64)
    mean, recurrent, next_h, base_mean, correction = actor.components(x, h)
    old_mean, old_recurrent, old_h = base(x[..., :171], h)
    assert torch.equal(mean, old_mean)
    assert torch.equal(base_mean, old_mean)
    assert torch.equal(recurrent, old_recurrent)
    assert torch.equal(next_h, old_h)
    assert torch.count_nonzero(correction) == 0
    assert torch.equal(critic(cx), base_critic(cx[:451]))
    changed = x.clone()
    changed[..., 171:] += 10
    _, changed_recurrent, changed_h, changed_base, _ = actor.components(changed, h)
    assert torch.equal(changed_base, base_mean)
    assert torch.equal(changed_recurrent, recurrent)
    assert torch.equal(changed_h, next_h)
    eligible = torch.ones(5, dtype=torch.bool)
    sampled, sent = sample_actions(actor, mean[0], recurrent[0], eligible, 0,
                                   torch.Generator().manual_seed(9), None)
    old_sampled, old_sent = sample_actions(base, old_mean[0], old_recurrent[0], eligible, 0,
                                           torch.Generator().manual_seed(9), None)
    assert torch.equal(sampled, old_sampled)
    assert torch.equal(sent, old_sent)
    with torch.no_grad():
        actor.residual_output.bias.fill_(2)
    active_mean, active_recurrent, active_h, active_base, active_correction = actor.components(x, h)
    assert torch.equal(active_base, base_mean)
    assert torch.equal(active_recurrent, recurrent)
    assert torch.equal(active_h, next_h)
    assert torch.all(active_correction.abs() <= model.CORRECTION_BOUND)
    assert torch.allclose(active_mean - base_mean, active_correction, atol=1e-7)


def test_checkpoint_digest_metadata_and_keys(monkeypatch):
    content, digest, _, _ = _checkpoint(monkeypatch)
    with pytest.raises(ValueError, match="digest"):
        model.load_base(content + b"x", digest)
    with pytest.raises(ValueError, match="digest"):
        model.load_base(content, "0" * 64)
    bad, bad_digest, _, _ = _checkpoint(monkeypatch, master=19452)
    with pytest.raises(ValueError, match="metadata"):
        model.load_base(bad, bad_digest)
    broken, broken_digest, _, _ = _checkpoint(monkeypatch, actor={})
    with pytest.raises(ValueError, match="keys"):
        model.load_base(broken, broken_digest)


def test_pair_initialization_and_global_rng():
    torch.manual_seed(413)
    before = torch.random.get_rng_state()
    actor_g, critic_g = model.build_arm(19601, "M_G")
    assert torch.equal(torch.random.get_rng_state(), before)
    actor_o, critic_o = model.build_arm(19601, "M_O")
    for name, tensor in model.parameter_snapshot(actor_g, critic_g).items():
        assert torch.equal(tensor, model.parameter_snapshot(actor_o, critic_o)[name])
    actor_next, critic_next = model.build_arm(19602, "M_G")
    assert not torch.equal(model.parameter_snapshot(actor_g, critic_g)["residual_hidden"],
                           model.parameter_snapshot(actor_next, critic_next)["residual_hidden"])
    with pytest.raises(ValueError, match="cell"):
        model.build_arm(19604, "M_G")
    with pytest.raises(ValueError, match="cell"):
        model.build_arm(19601, "B40")


def test_motion_density_and_recurrent_replay():
    actor, _ = model.build_arm(19601, "M_G")
    with torch.no_grad():
        actor.residual_output.weight.fill_(.01)
    x = torch.randn(32, 5, 186) * .1
    h = torch.zeros(1, 5, 64)
    entry, means = [], []
    for t in range(32):
        entry.append(h[0].clone())
        mean, _, h = actor(x[t:t + 1], h)
        means.append(mean[0])
    real_mean = torch.stack(means)
    rollout = {"obs": x[None], "hidden": torch.stack(entry)[None]}
    replayed, _ = recurrent_outputs(actor, rollout, 32)
    assert torch.allclose(replayed[0], real_mean, atol=2e-7, rtol=2e-6)
    u = real_mean + torch.randn_like(real_mean) * .2
    actual_logp, entropy = model.motion_terms(actor, real_mean, u)
    replay_logp, _ = model.motion_terms(actor, replayed[0], u)
    assert torch.allclose(replay_logp, actual_logp, atol=2e-6, rtol=2e-6)
    normal = torch.distributions.Normal(real_mean, actor.log_std.clamp(-5, 2).exp())
    jacobian = 2 * (math.log(2) - u - torch.nn.functional.softplus(-2 * u))
    assert torch.allclose(actual_logp, (normal.log_prob(u) - jacobian).sum(-1), atol=2e-6)
    assert torch.equal(actual_logp, tanh_log_prob(u, real_mean, actor.log_std))
    assert entropy.shape == (32,)


def _episodes(actor):
    x = torch.randn(2, 32, 5, 186) * .1
    hidden = torch.zeros(2, 32, 5, 64)
    cx = torch.randn(2, 32, 526) * .1
    with torch.no_grad():
        mean, _ = recurrent_outputs(actor, {"obs": x, "hidden": hidden}, 32)
        u = mean + torch.randn_like(mean) * .2
        logp, _ = model.motion_terms(actor, mean, u)
    rewards = torch.randn(2, 32) * .1 + .2
    return [dict(obs=x[i], hidden=hidden[i], critic=cx[i], u=u[i],
                 logp=logp[i], value=torch.zeros(32), reward=rewards[i]) for i in range(2)]


def test_independent_updates_freeze_base_and_exposure():
    actor, critic = model.build_arm(19601, "M_G")
    actor_opt, critic_opt = optimizers_for(actor, critic)
    assert {id(parameter) for group in actor_opt.param_groups for parameter in group["params"]} == {
        id(parameter) for parameter in actor.parameters() if parameter.requires_grad}
    assert not any(parameter.requires_grad for parameter in actor.base.parameters())
    initial = model.parameter_snapshot(actor, critic)
    episodes = _episodes(actor)
    counts, records = {}, []
    update_motion(actor, critic, actor_opt, critic_opt, episodes, counts, lambda: None, records.append)
    movement = model.exposure(initial, actor, critic)
    assert movement["base_actor"]["displacement"] == 0
    assert movement["residual_output"]["displacement"] > 0
    assert movement["critic_old"]["displacement"] > 0
    assert movement["critic_forecast"]["displacement"] > 0
    assert all(parameter.grad is None for parameter in actor.base.parameters())
    assert counts["optimizer_steps"] == counts["actor_optimizer_steps"] == counts["critic_optimizer_steps"] == 4
    assert counts["ppo_actor_forward_calls"] == counts["ppo_critic_forward_calls"] == 4
    assert counts["replayed_actor_rows"] == counts["ppo_actor_forward_rows"] == 4 * 2 * 32 * 5
    assert counts["ppo_critic_forward_rows"] == 4 * 2 * 32
    assert len(records) == 4 and all(row["kind"] == "ppo" for row in records)
    assert all(math.isfinite(row["actor_grad_norm"]) and math.isfinite(row["critic_grad_norm"])
               for row in records)


def test_critic_gradient_size_cannot_scale_actor_clip():
    actor_a, critic_a = model.build_arm(19601, "M_G")
    actor_b, critic_b = model.build_arm(19601, "M_O")
    episodes = _episodes(actor_a)
    with torch.no_grad():
        for parameter in critic_b.parameters():
            parameter.mul_(20)
    a_opt, a_critic_opt = optimizers_for(actor_a, critic_a)
    b_opt, b_critic_opt = optimizers_for(actor_b, critic_b)
    a_rows, b_rows = [], []
    update_motion(actor_a, critic_a, a_opt, a_critic_opt, episodes, {}, lambda: None, a_rows.append)
    update_motion(actor_b, critic_b, b_opt, b_critic_opt, episodes, {}, lambda: None, b_rows.append)
    for a, b in zip(actor_a.parameters(), actor_b.parameters()):
        assert torch.equal(a, b)
    assert a_rows[0]["critic_grad_norm"] != b_rows[0]["critic_grad_norm"]
    assert a_rows[0]["actor_grad_norm"] == b_rows[0]["actor_grad_norm"]
