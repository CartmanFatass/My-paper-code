"""Numerical/isolation checks on synthetic cached rows and H8 groups only."""
import copy

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b09_focal_response.context import PeerHistory, pack_context
from experiments.candidates.uav_fleet_adaptation.b09_focal_response.learning import (
    Critic, ResponseHead, fresh_critic, make_optimizers, update_group,
)


@pytest.fixture(scope="module", autouse=True)
def counted_costs():
    """Report actual successful forward rows, backward rows and Adam steps."""
    counts = dict(head_forward_rows=0, head_forward_attempts=0, head_backward_rows=0,
                  critic_forward_rows=0, critic_backward_rows=0,
                  head_optimizer_steps=0, critic_optimizer_steps=0,
                  tracker_ingests=0, tracker_pair_gates=0)
    old_head, old_critic, old_step, old_ingest = ResponseHead.forward, Critic.forward, torch.optim.Adam.step, PeerHistory.ingest
    threads = torch.get_num_threads()
    torch.set_num_threads(1)
    def counted_head(self, *args, **kwargs):
        counts["head_forward_attempts"] += 1
        output = old_head(self, *args, **kwargs)
        counts["head_forward_rows"] += 1
        if output.requires_grad:
            output.register_hook(lambda gradient: increment("head_backward_rows", 1, gradient))
        return output
    def counted_critic(self, *args, **kwargs):
        output = old_critic(self, *args, **kwargs)
        counts["critic_forward_rows"] += output.numel()
        if output.requires_grad:
            output.register_hook(lambda gradient: increment("critic_backward_rows", output.numel(), gradient))
        return output
    def increment(key, amount, value):
        counts[key] += amount
        return value
    def counted_step(self, *args, **kwargs):
        output = old_step(self, *args, **kwargs)
        key = "head_optimizer_steps" if len(self.param_groups[0]["params"]) == 2 else "critic_optimizer_steps"
        counts[key] += 1
        return output
    def counted_ingest(self, *args, **kwargs):
        before = self.counters["pair_gates"]
        output = old_ingest(self, *args, **kwargs)
        counts["tracker_ingests"] += 1
        counts["tracker_pair_gates"] += self.counters["pair_gates"] - before
        return output
    ResponseHead.forward, Critic.forward, torch.optim.Adam.step, PeerHistory.ingest = counted_head, counted_critic, counted_step, counted_ingest
    yield counts
    ResponseHead.forward, Critic.forward, torch.optim.Adam.step, PeerHistory.ingest = old_head, old_critic, old_step, old_ingest
    torch.set_num_threads(threads)
    print("B09 learning check costs:", counts, "Student/native/C requests=0")


def group(head, critic):
    rng = np.random.default_rng(41)
    episodes = []
    for index in range(2):
        context = rng.normal(size=(2, 259)).astype(np.float32)
        base = rng.normal(size=(2, 27)).astype(np.float32)
        cx = rng.normal(size=(2, 136)).astype(np.float32)
        with torch.no_grad():
            logits = np.stack([head(torch.from_numpy(x), torch.from_numpy(z)).numpy().copy()
                               for x, z in zip(context, base)])
            values = critic(torch.from_numpy(cx)).numpy().copy()
        z = logits.astype(np.float64)
        p = np.exp(z-z.max(axis=-1, keepdims=True))
        p /= p.sum(axis=-1, keepdims=True)
        actions = np.array([index*2, index*2+1], dtype=np.int64)
        logp = np.log(p[np.arange(2), actions])
        episodes.append(dict(contexts=context, base_logits=base, logits=logits,
                             probabilities=p, action_index=actions, logp=logp,
                             critic_features=cx, values=values,
                             macro_rewards=np.array([1+index*10, 2+index*10], dtype=np.float64)))
    return episodes


def target_advantage(episodes):
    target = np.array([[np.sum(e["macro_rewards"][t:].astype(np.float32), dtype=np.float32)/8
                        for t in range(2)] for e in episodes], dtype=np.float32)
    raw = target - np.stack([e["values"] for e in episodes])
    return target, (raw-raw.mean())/(raw.std(ddof=0)+np.float32(1e-8))


def test_zero_head_identity_shape_rng_and_optimizer_conventions():
    before = torch.random.get_rng_state().clone()
    head, critic = ResponseHead(), fresh_critic(81)
    assert torch.equal(before, torch.random.get_rng_state())
    assert sum(p.numel() for p in head.parameters()) == 7020
    assert sum(p.numel() for p in critic.parameters()) == 34177
    other = fresh_critic(81)
    assert all(torch.equal(p, q) and p.data_ptr() != q.data_ptr() for p, q in zip(critic.parameters(), other.parameters()))
    context = torch.linspace(-10, 10, 259)
    z = torch.linspace(-20, 20, 27)
    assert torch.equal(head(context, z), z)
    assert not head.W.any() and not head.b.any()
    aopt, copt = make_optimizers(head, critic)
    for opt in (aopt, copt):
        assert not opt.state
        for key, value in dict(lr=3e-4, betas=(.9,.999), eps=1e-8, weight_decay=0,
                               amsgrad=False, foreach=False, fused=False).items():
            assert opt.defaults[key] == value


def test_extreme_finite_shifted_density_and_bounded_residual():
    head = ResponseHead()
    with torch.no_grad(): head.b.copy_(torch.linspace(-100, 100, 27))
    z = torch.linspace(-1000, 1000, 27)
    output = head(torch.zeros(259), z)
    assert torch.isfinite(output).all() and (output-z).abs().max() <= .5
    weights = torch.exp(output.double()-output.double().max())
    p = weights/weights.sum()
    assert torch.isfinite(p).all() and p.sum() == 1 and torch.isfinite(p[-1].log())


def test_same_current_context_changed_lawful_history_changes_head():
    def row(dx, t):
        value = np.zeros(104, dtype=np.float32)
        value[:3] = (.5,.5,.5)
        value[63:67] = (dx,0,0,1)
        value[-1] = t/256
        return value
    left, right = PeerHistory(), PeerHistory()
    left.ingest(row(.1,0), 0)
    right.ingest(row(.08,0), 0)
    current = row(.1,1)
    dleft, dright = left.ingest(current,1)["descriptor"], right.ingest(current,1)["descriptor"]
    f, h = np.zeros(114, dtype=np.float32), np.zeros(128, dtype=np.float32)
    a, b = pack_context(f,h,1,dleft), pack_context(f,h,1,dright)
    np.testing.assert_array_equal(a[:243], b[:243])
    head = ResponseHead()
    with torch.no_grad(): head.W[0,243] = 1
    z = torch.zeros(27)
    assert head(torch.from_numpy(a),z)[0] == 0
    assert head(torch.from_numpy(b),z)[0] > .2


def test_update_ego_loss_targets_clipping_order_counts_and_continuity():
    head, critic = ResponseHead(), fresh_critic(81)
    aopt, copt = make_optimizers(head, critic)
    episodes = group(head, critic)
    # Zero initialization leaves cached logits identical, while this synthetic
    # scale makes later epochs exercise both sides of the PPO clipping branch.
    for episode in episodes:
        episode["contexts"] *= 16
    original = copy.deepcopy(episodes)
    targets, adv = target_advantage(episodes)
    logits, predictions, steps = [], [], []
    hh = head.register_forward_hook(lambda m,i,o: logits.append(o.detach().numpy().copy()))
    ch = critic.register_forward_hook(lambda m,i,o: predictions.append(o.detach().numpy().copy()))
    astep, cstep = aopt.step, copt.step
    aopt.step = lambda: (steps.append("head"), astep())[1]
    copt.step = lambda: (steps.append("critic"), cstep())[1]
    counts = dict(head_optimizer_steps=11, critic_optimizer_steps=17,
                  head_replay_rows=23, critic_replay_rows=29, density_identity_rows=31, unrelated=101)
    record = {}
    result = update_group(head, critic, aopt, copt, episodes, counts, horizon=8, live_record=record)
    hh.remove(); ch.remove()
    assert result is record and result["status"] == "COMPLETE"
    assert steps == ["head","critic"]*4
    assert counts == dict(head_optimizer_steps=15, critic_optimizer_steps=21,
                          head_replay_rows=39, critic_replay_rows=45, density_identity_rows=35, unrelated=101)
    assert result["initial_identity"]["logits_exact"] and result["initial_identity"]["rows"] == 4
    assert result["initial_identity"]["max_ratio_from_one"] < 1e-10
    assert result["target_summary"]["dtype"] == "torch.float32"
    assert result["target_summary"]["mean"] == pytest.approx(targets.mean())
    assert result["advantage_summary"]["std"] == pytest.approx(1.,abs=1e-6)
    action = np.stack([e["action_index"] for e in episodes])
    old = np.take_along_axis(np.stack([e["probabilities"] for e in episodes]), action[...,None],-1)[...,0]
    for epoch, row in enumerate(result["epochs"]):
        z = np.stack(logits[epoch*4:(epoch+1)*4]).reshape(2,2,27).astype(np.float64)
        p = np.exp(z-z.max(-1,keepdims=True)); p /= p.sum(-1,keepdims=True)
        ratio = np.take_along_axis(p,action[...,None],-1)[...,0]/old
        expected = -np.minimum(ratio*adv,np.clip(ratio,.8,1.2)*adv).mean()
        assert row["head_loss"] == pytest.approx(expected,abs=1e-7)
        if epoch: assert abs(row["head_loss"]-expected*5) > 1e-4
        assert row["critic_loss"] == pytest.approx(.5*np.square(predictions[epoch]-targets).mean(),abs=1e-6)
        assert row["head_clipped_grad_norm"] <= .500001
        assert row["critic_clipped_grad_norm"] <= .500001
        assert row["head_optimizer_step_values"] == [epoch+1]*2
    assert result["head_movement_l2"] > 0 and result["critic_movement_l2"] > 0
    assert any(r["clip_fraction"] > 0 for r in result["epochs"][1:])
    for e,o in zip(episodes,original):
        for key in e: np.testing.assert_array_equal(e[key],o[key])
    moment = aopt.state[head.W]["exp_avg"].clone()
    recollected = group(head,critic)
    # Distinguish collection/replay numerical identity before optimizer work.
    for e in recollected:
        for x,z,expected in zip(e["contexts"],e["base_logits"],e["logits"]):
            actual = head(torch.tensor(x),torch.tensor(z)).detach().numpy()
            np.testing.assert_array_equal(actual,expected)
            with torch.inference_mode():
                deployed = head(torch.from_numpy(x),torch.from_numpy(z)).numpy()
            np.testing.assert_array_equal(deployed,expected)
            strided = torch.empty(518,dtype=torch.float32)[::2]
            strided.copy_(torch.from_numpy(x))
            np.testing.assert_array_equal(head(strided,torch.from_numpy(z)).detach().numpy(),expected)
    second = update_group(head,critic,aopt,copt,recollected,counts,horizon=8)
    assert second["head_optimizer_step_values"] == [8]*2
    assert second["critic_optimizer_step_values"] == [8]*6
    assert not torch.equal(aopt.state[head.W]["exp_avg"],moment)


def test_first_head_gradient_matches_hand_score_without_five_agent_factor():
    head, critic = ResponseHead(), fresh_critic(81)
    episodes = group(head,critic)
    _, adv = target_advantage(episodes)
    p = np.stack([e["probabilities"] for e in episodes]).reshape(4,27)
    action = np.concatenate([e["action_index"] for e in episodes])
    score = np.eye(27)[action]-p
    dz = -adv.reshape(4,1).astype(np.float64)*score/4
    context = np.concatenate([e["contexts"] for e in episodes]).astype(np.float64)
    expected_w, expected_b = (.5*dz.T@context).astype(np.float32), (.5*dz.sum(0)).astype(np.float32)
    norm = np.sqrt(np.square(expected_w.astype(np.float64)).sum()+np.square(expected_b.astype(np.float64)).sum())
    scale = min(1.,.5/(norm+1e-6))
    aopt,copt = make_optimizers(head,critic)
    captured = []
    step = aopt.step
    def capture():
        if not captured: captured.extend([head.W.grad.clone(),head.b.grad.clone()])
        return step()
    aopt.step = capture
    update_group(head,critic,aopt,copt,episodes,{},horizon=8)
    torch.testing.assert_close(captured[0],torch.from_numpy(expected_w*scale),rtol=3e-5,atol=2e-7)
    torch.testing.assert_close(captured[1],torch.from_numpy(expected_b*scale),rtol=3e-5,atol=2e-7)


@pytest.mark.parametrize("case", ["logits", "probability", "logp", "dtype", "shape", "action", "nan", "single", "horizon", "count", "optimizer"])
def test_invalid_group_has_no_optimizer_effect(case):
    head,critic = ResponseHead(),fresh_critic(81)
    aopt,copt = make_optimizers(head,critic)
    episodes = group(head,critic)
    counts, record, horizon = {},{},8
    if case == "logits": episodes[0]["logits"][0,0] += .1
    elif case == "probability":
        episodes[0]["probabilities"][0,25] += 1e-8
        episodes[0]["probabilities"][0,26] -= 1e-8
    elif case == "logp": episodes[0]["logp"][0] += 1e-7
    elif case == "dtype": episodes[0]["base_logits"] = episodes[0]["base_logits"].astype(np.float64)
    elif case == "shape": episodes[0]["contexts"] = episodes[0]["contexts"][:1]
    elif case == "action": episodes[0]["action_index"][0] = 27
    elif case == "nan": episodes[0]["macro_rewards"][0] = np.nan
    elif case == "single": episodes = episodes[:1]
    elif case == "horizon": horizon = 6
    elif case == "count": counts["head_optimizer_steps"] = np.nan
    else: aopt.param_groups[0]["params"] = list(critic.parameters())
    initial = [p.detach().clone() for m in (head,critic) for p in m.parameters()]
    with pytest.raises((ValueError,FloatingPointError)):
        update_group(head,critic,aopt,copt,episodes,counts,horizon=horizon,live_record=record)
    assert not aopt.state and not copt.state
    assert counts.get("head_optimizer_steps",0) in (0,np.nan) or np.isnan(counts["head_optimizer_steps"])
    assert counts.get("critic_optimizer_steps",0) == 0
    assert all(torch.equal(p,q) for p,q in zip((p for m in (head,critic) for p in m.parameters()),initial))
    if case in ("logits","probability"):
        assert record["initial_identity"]["rows"] == 4 and counts["head_replay_rows"] == 4


@pytest.mark.parametrize("side", ["head", "critic"])
def test_nonfinite_gradient_keeps_partial_paid_evidence(side):
    head,critic = ResponseHead(),fresh_critic(81)
    aopt,copt = make_optimizers(head,critic)
    episodes = group(head,critic)
    model = head if side == "head" else critic
    hook = next(model.parameters()).register_hook(lambda grad: grad*float("inf"))
    counts,record = {},{}
    with pytest.raises(RuntimeError,match="non-finite"):
        update_group(head,critic,aopt,copt,episodes,counts,horizon=8,live_record=record)
    hook.remove()
    assert record["status"] == "INCOMPLETE" and len(record["epochs"]) == 1
    assert counts["head_replay_rows"] == counts["density_identity_rows"] == 4
    assert counts.get("head_optimizer_steps",0) == (side == "critic")
    assert counts.get("critic_optimizer_steps",0) == 0
    assert record["head_optimizer_step_values"] == [int(side == "critic")]*2
    assert record["critic_optimizer_step_values"] == [0.]*6


def test_detached_private_rollout_no_trunk_or_peer_gradient_or_buffer_borrowing():
    head,critic = ResponseHead(),fresh_critic(81)
    peer_head, peer_critic = ResponseHead(),fresh_critic(81)
    trunk = torch.nn.Linear(114,128)
    protected = [p.detach().clone() for m in (peer_head,peer_critic,trunk) for p in m.parameters()]
    aopt,copt = make_optimizers(head,critic)
    episodes = group(head,critic)
    for episode in episodes:
        for key,value in list(episode.items()):
            episode[key] = torch.tensor(value)
            if episode[key].is_floating_point(): episode[key].requires_grad_(True)
    astep = aopt.step
    def mutate_source_cache():
        result = astep()
        with torch.no_grad(): episodes[0]["contexts"].fill_(float("nan"))
        return result
    aopt.step = mutate_source_cache
    result = update_group(head,critic,aopt,copt,episodes,{},horizon=8)
    assert result["status"] == "COMPLETE"  # Replay owns a detached private copy.
    assert all(value.grad is None for e in episodes for value in e.values())
    for p,old in zip((p for m in (peer_head,peer_critic,trunk) for p in m.parameters()),protected):
        assert p.grad is None and torch.equal(p,old)
    assert set(head.parameters()).isdisjoint(set(peer_head.parameters()))


def test_fp32_rounding_precedes_suffix_and_zero_advantages_are_finite():
    head,critic = ResponseHead(),fresh_critic(81)
    aopt,copt = make_optimizers(head,critic)
    episodes = group(head,critic)
    episodes[0]["macro_rewards"] = np.array([1+2**-24,2**-24],dtype=np.float64)
    episodes[1]["macro_rewards"] = np.zeros(2,dtype=np.float64)
    result = update_group(head,critic,aopt,copt,episodes,{},horizon=8)
    assert result["target_summary"]["max"] == .125
    assert np.float32(episodes[0]["macro_rewards"].sum()/8) > .125
    episodes = group(head,critic)
    for e in episodes:
        e["macro_rewards"].fill(0); e["values"].fill(0)
    result = update_group(head,critic,aopt,copt,episodes,{},horizon=8)
    assert result["advantage_summary"]["std"] == 0
    assert all(r["head_loss"] == 0 for r in result["epochs"])


def test_extreme_density_update_retains_finite_chosen_ratios():
    head,critic = ResponseHead(),fresh_critic(81)
    aopt,copt = make_optimizers(head,critic)
    episodes = group(head,critic)
    for e in episodes:
        e["base_logits"][:] = np.linspace(-1000,1000,27,dtype=np.float32)
        e["logits"][:] = e["base_logits"]
        z = e["logits"].astype(np.float64)
        p = np.exp(z-z.max(-1,keepdims=True)); p /= p.sum(-1,keepdims=True)
        e["probabilities"][:] = p
        e["action_index"].fill(26); e["logp"][:] = np.log(p[:,-1])
    counts = {}
    result = update_group(head,critic,aopt,copt,episodes,counts,horizon=8)
    assert result["status"] == "COMPLETE"
    assert result["initial_identity"]["max_probability_abs"] < 5e-14
    assert all(r["ratio_min"] == r["ratio_max"] == 1 for r in result["epochs"])
    assert counts == dict(head_replay_rows=16,critic_replay_rows=16,
                          density_identity_rows=4,head_optimizer_steps=4,critic_optimizer_steps=4)


@pytest.mark.parametrize("case", ["shape", "dtype", "nan", "overflow"])
def test_head_rejects_malformed_and_overflowing_rows(case):
    head = ResponseHead()
    x,z = torch.zeros(259),torch.zeros(27)
    if case == "shape": x = x[None]
    elif case == "dtype": z = z.double()
    elif case == "nan": x[0] = float("nan")
    else:
        with torch.no_grad(): head.W.fill_(torch.finfo(torch.float32).max)
        x.fill_(2)
    with pytest.raises((ValueError,FloatingPointError)): head(x,z)
