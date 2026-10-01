"""Declared synthetic B10 unit exposure; do not run before DM declaration.

Successful full-file invocation: Student1, JointActor1142, Critic146209 forward
rows; actor500 and critic88 backward rows;23 actor/20 critic Adam steps.
Constructors:35 Student,36 JointActor,31 Critic146 (all isolated/restored RNG),
plus one actor deepcopy with no RNG. All features/actions/uniforms are fixed;
there are no NumPy RNG draws, canonical assets, native or controller calls.
Runtime counters report actual partial costs if a check fails early.
"""
import copy
import math

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import Student, make_student
from experiments.candidates.uav_fleet_adaptation.b10_joint_control import learning as L


@pytest.fixture(scope="module", autouse=True)
def costs():
    counts = dict(student_forward_rows=0, actor_forward_rows=0, actor_forward_attempts=0,
                  critic_forward_rows=0, actor_backward_rows=0, critic_backward_rows=0,
                  actor_optimizer_steps=0, critic_optimizer_steps=0,
                  student_constructors=0, actor_constructors=0, critic_constructors=0,
                  numpy_density_rows=0, torch_density_rows=0, cdf_calls=0)
    saved = []
    threads = torch.get_num_threads()
    torch.set_num_threads(1)
    def replace(obj, name, value):
        saved.append((obj,name,getattr(obj,name)))
        setattr(obj,name,value)
    def increment(key, amount, value):
        counts[key] += amount
        return value
    for cls,name in ((Student,"student"),(L.JointActor,"actor"),(L.Critic146,"critic")):
        init, forward = cls.__init__, cls.forward
        def counted_init(self,*args,_init=init,_name=name,**kwargs):
            _init(self,*args,**kwargs)
            counts[_name+"_constructors"] += 1
        def counted_forward(self,*args,_forward=forward,_name=name,**kwargs):
            if _name == "actor": counts["actor_forward_attempts"] += 1
            result = _forward(self,*args,**kwargs)
            rows = result.numel() // (54 if _name == "actor" else 27 if _name == "student" else 1)
            counts[_name+"_forward_rows"] += rows
            if _name in ("actor","critic") and result.requires_grad:
                result.register_hook(lambda gradient,_key=_name+"_backward_rows",_rows=rows:
                                     increment(_key,_rows,gradient))
            return result
        replace(cls,"__init__",counted_init)
        replace(cls,"forward",counted_forward)
    original_step = torch.optim.Adam.step
    def step(self,*args,**kwargs):
        result = original_step(self,*args,**kwargs)
        parameters = self.param_groups[0]["params"]
        key = "actor" if parameters[-1].numel() == 54 else "critic"
        counts[key+"_optimizer_steps"] += 1
        return result
    replace(torch.optim.Adam,"step",step)
    original_numpy,original_torch,original_cdf = L.joint_probabilities,L.torch_probabilities,L.categorical_index54
    def numpy_density(*args,**kwargs):
        result = original_numpy(*args,**kwargs)
        counts["numpy_density_rows"] += 1
        return result
    def torch_density(*args,**kwargs):
        result = original_torch(*args,**kwargs)
        counts["torch_density_rows"] += result.numel()//54
        return result
    def cdf(*args,**kwargs):
        counts["cdf_calls"] += 1
        return original_cdf(*args,**kwargs)
    replace(L,"joint_probabilities",numpy_density)
    replace(L,"torch_probabilities",torch_density)
    replace(L,"categorical_index54",cdf)
    yield counts
    for obj,name,value in reversed(saved): setattr(obj,name,value)
    torch.set_num_threads(threads)
    print("B10 ACTUAL synthetic unit exposure:",counts,"native/controller/canonical queries=0")


def parent():
    model = make_student(17)
    # Fixed positive body activations avoid accidental dead-unit test coverage.
    with torch.no_grad():
        model.network[0].weight.fill_(.01); model.network[0].bias.fill_(.1)
        model.network[2].weight.fill_(.01); model.network[2].bias.fill_(.1)
        model.network[4].weight.copy_(torch.linspace(-.02,.02,27*128).reshape(27,128))
        model.network[4].bias.copy_(torch.linspace(-.1,.1,27))
    return model


def models():
    inherited = parent()
    actor,critic = L.make_actor(inherited,seed=51),L.fresh_critic(52)
    return inherited,actor,critic


def episodes(actor,critic):
    """Exactly2 H8 caches:20 actor and4 critic collection forward rows."""
    result = []
    for episode in range(2):
        x = (.5+.3*np.sin(np.arange(2*5*114).reshape(2,5,114)*.013+episode)).astype(np.float32)
        x[...,-1] = (np.arange(10).reshape(2,5)+episode)%2
        cx = (.3*np.cos(np.arange(2*146).reshape(2,146)*.023+episode)).astype(np.float32)
        eligible = np.zeros((2,5),dtype=np.bool_)
        eligible[np.arange(2),np.arange(2)%5] = True
        prior = np.ones((2,5,2),dtype=np.float64)
        prior[0,0] = (.9,.1); prior[1,1] = (.1,.9)
        # Distinct ON actions and both gate categories use fixed indices.
        actions = ((np.arange(10).reshape(2,5)*3+episode)%27).astype(np.int64)
        actions[1,1] += 27
        with torch.inference_mode():
            z = np.stack([actor(torch.from_numpy(row).reshape(1,114))[0].numpy().copy()
                          for row in x.reshape(-1,114)]).reshape(2,5,54)
            values = critic(torch.from_numpy(cx)).numpy().copy()
        p = np.stack([L.joint_probabilities(raw,q,bool(e)) for raw,q,e in
                      zip(z.reshape(-1,54),prior.reshape(-1,2),eligible.reshape(-1))]).reshape(2,5,54)
        logp = np.log(np.take_along_axis(p,actions[...,None],-1)[...,0])
        result.append(dict(features=x,logits=z,prior=prior,eligible=eligible,probabilities=p,
                           action_index=actions,logp=logp,critic_features=cx,values=values,
                           macro_rewards=np.array([1+10*episode,2+10*episode],dtype=np.float64)))
    return result


def scalar_density(raw,prior,eligible):
    active = range(54 if eligible else 27)
    maximum = max(float(raw[i]) for i in active)
    weights = [math.exp(float(raw[i])-maximum)*(float(prior[i//27]) if eligible else 1.)
               if i in active else 0. for i in range(54)]
    total = sum(weights)
    return np.array([w/total for w in weights],dtype=np.float64)


def reference_targets(eps):
    target = np.array([[np.sum(e["macro_rewards"][t:].astype(np.float32),dtype=np.float32)/8
                        for t in range(2)] for e in eps],dtype=np.float32)
    raw = target-np.stack([e["values"] for e in eps])
    return target,(raw-raw.mean())/(raw.std(ddof=0)+np.float32(1e-8))


def test_warm_copy_rng_parameters_and_mathematical_product_law():
    before = torch.random.get_rng_state().clone()
    inherited = parent()
    actor,other = L.JointActor(inherited,seed=51),L.make_actor(inherited,seed=53)
    critic,critic2 = L.fresh_critic(52),L.fresh_critic(52)
    assert torch.equal(before,torch.random.get_rng_state())
    assert sum(p.numel() for p in actor.parameters()) == 38198
    assert sum(p.numel() for p in critic.parameters()) == 35457
    assert len(list(actor.parameters())) == len(list(critic.parameters())) == 6
    assert all(p.requires_grad and p.dtype == torch.float32 and p.device.type == "cpu" for p in actor.parameters())
    for index in (0,2):
        for name in ("weight","bias"):
            a,p = getattr(actor.network[index],name),getattr(inherited.network[index],name)
            assert torch.equal(a,p) and a.data_ptr() != p.data_ptr()
    assert torch.equal(actor.network[4].weight,inherited.network[4].weight.repeat(2,1))
    assert torch.equal(actor.network[4].bias,inherited.network[4].bias.repeat(2))
    assert all(torch.equal(a,b) and a.data_ptr() != b.data_ptr() for a,b in zip(actor.parameters(),other.parameters()))
    assert all(torch.equal(a,b) and a.data_ptr() != b.data_ptr() for a,b in zip(critic.parameters(),critic2.parameters()))
    x = torch.linspace(-.2,1.,114).reshape(1,114)
    with torch.inference_mode():
        p0 = inherited(x)[0].numpy().copy()
        raw = actor(x)[0].numpy().copy()
        assert torch.equal(other(x),torch.from_numpy(raw).reshape(1,54))
        assert critic(torch.zeros((1,146))).shape == (1,)
    # Equal copied tensors imply the product law mathematically; do not claim
    # bitwise identity of a27-output and54-output Linear numerical program.
    np.testing.assert_allclose(raw[:27],p0,rtol=2e-6,atol=2e-7)
    np.testing.assert_allclose(raw[27:],p0,rtol=2e-6,atol=2e-7)
    base = np.exp(p0.astype(np.float64)-p0.max()); base /= base.sum()
    for eligible,prior in ((True,np.array([.9,.1])),(False,np.ones(2))):
        expected = np.concatenate((base*(.9 if eligible else 1.),base*.1 if eligible else np.zeros(27)))
        p = L.joint_probabilities(raw,prior,eligible)
        np.testing.assert_allclose(p,expected,rtol=2e-6,atol=2e-8)
        q = L.torch_probabilities(torch.from_numpy(raw),torch.from_numpy(prior),torch.tensor(eligible)).numpy()
        np.testing.assert_allclose(q,p,rtol=3e-15,atol=5e-17)
    aopt,copt = L.make_optimizers(actor,critic)
    assert not aopt.state and not copt.state and aopt is not copt
    for opt in (aopt,copt):
        for key,value in L.ADAM_OPTIONS.items(): assert opt.defaults[key] == value
    with pytest.raises(ValueError): L.make_actor(object(),seed=1)


@pytest.mark.parametrize("case",["on_prior","off_prior","ineligible","tiny","extreme","masked_extreme","zero_logits"])
def test_density_matches_independent_scalar_law_and_prior_is_frozen(case):
    raw = np.linspace(-2,2,54,dtype=np.float32)
    eligible,prior = True,np.array([.9,.1],dtype=np.float64)
    if case == "off_prior": prior = prior[::-1].copy()
    elif case == "ineligible": eligible,prior = False,np.ones(2)
    elif case == "tiny": raw[0] = -700
    elif case == "extreme": raw[:] = np.linspace(-1000,1000,54,dtype=np.float32)
    elif case == "masked_extreme":
        eligible,prior = False,np.ones(2); raw[27:] = np.finfo(np.float32).max
    elif case == "zero_logits": raw.fill(0)
    p = L.joint_probabilities(raw,prior,eligible)
    expected = scalar_density(raw,prior,eligible)
    np.testing.assert_allclose(p,expected,rtol=3e-15,atol=5e-17)
    z = torch.tensor(raw,requires_grad=True)
    frozen = torch.tensor(prior,requires_grad=True)
    q = L.torch_probabilities(z,frozen,torch.tensor(eligible))
    np.testing.assert_allclose(q.detach().numpy(),expected,rtol=3e-15,atol=5e-17)
    assert q.dtype == torch.float64 and torch.isfinite(q).all()
    (q*torch.arange(54,dtype=torch.float64)).sum().backward()
    assert frozen.grad is None and torch.isfinite(z.grad).all()
    if not eligible:
        assert not p[27:].any() and not z.grad[27:].any()
    if case == "tiny": assert p[0] > 0


def test_cdf_tiny_mass_exact_boundaries_flat_gaps_and_masked_rounding_tail():
    tiny = 2.**-100
    p = np.zeros(54,dtype=np.float64)
    p[0],p[1],p[26] = tiny,.25,.75
    for u,expected in ((0.,0),(np.nextafter(tiny,0.),0),(tiny,1),
                       (np.nextafter(.25,0.),1),(.25,26),(np.nextafter(1.,0.),26)):
        assert L.categorical_index54(p,u) == expected
    p[26] -= 5e-13
    assert L.categorical_index54(p,np.nextafter(1.,0.)) == 26
    p.fill(0); p[0] = p[27] = .5
    for u,expected in ((np.nextafter(.5,0.),0),(.5,27),(np.nextafter(1.,0.),27)):
        assert L.categorical_index54(p,u) == expected


@pytest.mark.parametrize("case",["raw_shape","raw_dtype","raw_nan","prior_shape","prior_dtype","prior_nan","prior_value","sentinel","eligible_type"])
def test_malformed_density_rejected(case):
    raw,prior,eligible = np.zeros(54,dtype=np.float32),np.array([.9,.1]),True
    if case == "raw_shape": raw = raw[:-1]
    elif case == "raw_dtype": raw = raw.astype(np.float64)
    elif case == "raw_nan": raw[0] = np.nan
    elif case == "prior_shape": prior = np.ones(3)
    elif case == "prior_dtype": prior = prior.astype(np.float32)
    elif case == "prior_nan": prior[0] = np.nan
    elif case == "prior_value": prior[:] = (.8,.2)
    elif case == "sentinel": eligible = False
    else: eligible = 1
    with pytest.raises((ValueError,FloatingPointError)): L.joint_probabilities(raw,prior,eligible)
    with pytest.raises((ValueError,FloatingPointError)):
        L.torch_probabilities(torch.from_numpy(raw),torch.from_numpy(prior),torch.tensor(eligible))


@pytest.mark.parametrize("case",["shape","negative","nan","zero_mass","uniform","uniform_bool"])
def test_malformed_cdf_rejected(case):
    p,u = np.full(54,1/54,dtype=np.float64),.5
    if case == "shape": p = p[:-1]
    elif case == "negative": p[0] = -.1
    elif case == "nan": p[0] = np.nan
    elif case == "zero_mass": p.fill(0)
    elif case == "uniform": u = 1.
    else: u = True
    with pytest.raises(ValueError): L.categorical_index54(p,u)


@pytest.mark.parametrize("case",["shape","dtype","nan","batch","parameter"])
def test_actor_rejects_bad_inputs_and_nonfinite_parameters(case):
    actor = L.make_actor(parent(),seed=51)
    x = torch.zeros((1,114))
    if case == "shape": x = x[0]
    elif case == "dtype": x = x.double()
    elif case == "nan": x[0,0] = float("nan")
    elif case == "batch": x = x.repeat(2,1)
    else:
        with torch.no_grad(): actor.network[4].bias[0] = float("nan")
    with pytest.raises((ValueError,FloatingPointError)): actor(x)


def test_all_five_sum_surrogate_targets_order_and_two_group_adam_continuity():
    _,actor,critic = models()
    aopt,copt = L.make_optimizers(actor,critic)
    eps = episodes(actor,critic)
    targets,adv = reference_targets(eps)
    original = copy.deepcopy(eps)
    actual_logits,predictions,order,norm_evidence = [],[],[],[]
    ah = actor.register_forward_hook(lambda m,i,o: actual_logits.append(o.detach().numpy().copy()))
    ch = critic.register_forward_hook(lambda m,i,o: predictions.append(o.detach().numpy().copy()))
    astep,cstep = aopt.step,copt.step
    def step_boundary(model,side,step):
        gradients = [p.grad.detach() for p in model.parameters() if p.grad is not None]
        norm64 = float(torch.linalg.vector_norm(torch.cat([g.double().reshape(-1) for g in gradients])))
        norm32 = L.b04._norm(gradients)
        norm_evidence.append(dict(side=side,fp64=norm64,inherited_fp32=norm32,
                                  fp64_excess_over_half=max(0.,norm64-.5)))
        # Clipping itself uses FP32 parameter norms; distinguish their rounding
        # from the separate concatenated FP32 diagnostic's accumulation error.
        assert norm64 <= .5*(1+32*np.finfo(np.float32).eps)
        order.append(side)
        return step()
    aopt.step = lambda: step_boundary(actor,"actor",astep)
    copt.step = lambda: step_boundary(critic,"critic",cstep)
    counts,record = {},{}
    result = L.update_group(actor,critic,aopt,copt,eps,counts,horizon=8,live_record=record)
    ah.remove(); ch.remove()
    assert result is record and result["status"] == "COMPLETE"
    assert order == ["actor","critic"]*4
    assert counts == dict(actor_replay_rows=80,critic_replay_rows=16,density_identity_rows=20,
                          actor_optimizer_steps=4,critic_optimizer_steps=4)
    assert result["initial_identity"]["logits_exact"]
    assert result["target_summary"]["mean"] == pytest.approx(targets.mean(),abs=1e-7)
    assert result["advantage_summary"]["std"] == pytest.approx(1.,abs=1e-6)
    old = np.stack([e["probabilities"] for e in eps])
    actions = np.stack([e["action_index"] for e in eps])
    prior,eligible = np.stack([e["prior"] for e in eps]),np.stack([e["eligible"] for e in eps])
    old_chosen = np.take_along_axis(old,actions[...,None],-1)[...,0]
    wrong_losses = []
    for epoch,row in enumerate(result["epochs"]):
        raw = np.concatenate(actual_logits[epoch*20:(epoch+1)*20]).reshape(2,2,5,54)
        p = np.stack([scalar_density(z,q,bool(e)) for z,q,e in
                      zip(raw.reshape(-1,54),prior.reshape(-1,2),eligible.reshape(-1))]).reshape(raw.shape)
        ratios = np.take_along_axis(p,actions[...,None],-1)[...,0]/old_chosen
        expected = -np.minimum(ratios*adv[...,None],np.clip(ratios,.8,1.2)*adv[...,None]).sum(-1).mean()
        joint = ratios.prod(-1)
        wrong_losses.append(abs(expected-(-np.minimum(joint*adv,np.clip(joint,.8,1.2)*adv).mean())))
        assert row["actor_loss"] == pytest.approx(expected,abs=3e-6)
        assert row["critic_loss"] == pytest.approx(.5*np.square(predictions[epoch]-targets).mean(),abs=1e-6)
        assert row["actor_optimizer_step_values"] == row["critic_optimizer_step_values"] == [epoch+1]*6
        diagnostic_limit = .5*(1+64*np.finfo(np.float32).eps)
        assert row["actor_clipped_grad_norm"] <= diagnostic_limit
        assert row["critic_clipped_grad_norm"] <= diagnostic_limit
        assert row["actor_clipped_grad_norm"] == norm_evidence[2*epoch]["inherited_fp32"]
        assert row["critic_clipped_grad_norm"] == norm_evidence[2*epoch+1]["inherited_fp32"]
    assert max(wrong_losses[1:]) > 1e-3
    assert result["actor_movement_l2"] > 0 and result["critic_movement_l2"] > 0
    for e,old in zip(eps,original):
        for key in e: np.testing.assert_array_equal(e[key],old[key])
    old_moment = aopt.state[next(actor.parameters())]["exp_avg"].clone()
    second = L.update_group(actor,critic,aopt,copt,episodes(actor,critic),counts,horizon=8)
    assert second["initial_identity"]["logits_exact"]
    assert second["initial_identity"]["max_ratio_from_one"] < 1e-10
    assert second["actor_optimizer_step_values"] == second["critic_optimizer_step_values"] == [8]*6
    assert not torch.equal(aopt.state[next(actor.parameters())]["exp_avg"],old_moment)
    assert counts["actor_optimizer_steps"] == counts["critic_optimizer_steps"] == 8
    print("B10 step-boundary clipping evidence:",norm_evidence)
    print("B10 clipping maxima:",dict(fp64=max(e["fp64"] for e in norm_evidence),
                                      inherited_fp32=max(e["inherited_fp32"] for e in norm_evidence),
                                      fp64_excess_over_half=max(e["fp64_excess_over_half"] for e in norm_evidence)))


def test_first_gradient_independent_log_score_private_buffers_and_gradient_isolation():
    inherited,actor,critic = models()
    aopt,copt = L.make_optimizers(actor,critic)
    eps = episodes(actor,critic)
    protected = [p.detach().clone() for p in inherited.parameters()]
    reference = copy.deepcopy(actor)  # No constructor and no random draw.
    targets,adv = reference_targets(eps)
    features = torch.tensor(np.stack([e["features"] for e in eps]))
    raw = torch.stack([reference(x.reshape(1,114))[0] for x in features.reshape(-1,114)]).reshape(2,2,5,54).double()
    prior = torch.tensor(np.stack([e["prior"] for e in eps]))
    eligible = torch.tensor(np.stack([e["eligible"] for e in eps]))
    factors = torch.repeat_interleave(prior,27,dim=-1)
    # Independent weighted-log-softmax score, using -inf only in this reference
    # mask; production raw logits remain finite and stored separately.
    weighted = raw+factors.log()
    active = torch.cat((torch.ones_like(raw[...,:27],dtype=torch.bool),eligible[...,None].expand(2,2,5,27)),-1)
    lp = weighted.masked_fill(~active,-float("inf")).log_softmax(-1)
    actions = torch.tensor(np.stack([e["action_index"] for e in eps]))
    old_lp = torch.tensor(np.stack([e["logp"] for e in eps]))
    chosen_lp = lp.gather(-1,actions[...,None]).squeeze(-1)
    loss = -((chosen_lp-old_lp).exp()*torch.tensor(adv)[...,None]).sum(-1).mean()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(reference.parameters(),.5,foreach=False)
    for e in eps:
        for key,value in list(e.items()):
            e[key] = torch.tensor(value)
            if e[key].is_floating_point(): e[key].requires_grad_(True)
    observed = []
    astep,cstep = aopt.step,copt.step
    def actor_step():
        if not observed:
            assert all(p.grad is None for p in critic.parameters())
            observed.extend(p.grad.clone() for p in actor.parameters())
            assert all(p.grad is not None and torch.count_nonzero(p.grad) for p in actor.parameters())
        result = astep()
        with torch.no_grad(): eps[0]["features"].fill_(float("nan"))
        return result
    def critic_step():
        before = [p.grad.clone() for p in actor.parameters()]
        result = cstep()
        assert all(torch.equal(p.grad,g) for p,g in zip(actor.parameters(),before))
        return result
    aopt.step,copt.step = actor_step,critic_step
    result = L.update_group(actor,critic,aopt,copt,eps,{},horizon=8)
    assert result["status"] == "COMPLETE"
    for got,p in zip(observed,reference.parameters()):
        torch.testing.assert_close(got,p.grad,rtol=3e-5,atol=3e-7)
    assert all(v.grad is None for e in eps for v in e.values())
    assert all(p.grad is None and torch.equal(p,old) for p,old in zip(inherited.parameters(),protected))


@pytest.mark.parametrize("case",["logits","density","prior","eligible_shape","ineligible_action","negative_action","large_action","masked_density","chosen_zero","logp","dtype","critic_shape","nan","missing","single","horizon","count","optimizer_ownership","optimizer_type","optimizer_options","optimizer_maximize"])
def test_invalid_group_has_no_optimizer_effect(case):
    _,actor,critic = models()
    aopt,copt = L.make_optimizers(actor,critic)
    eps = episodes(actor,critic)
    counts,record,horizon = {},{},8
    if case == "logits": eps[0]["logits"][0,0,0] += .1
    elif case == "density":
        eps[0]["probabilities"][0,2,10] += 1e-8; eps[0]["probabilities"][0,2,11] -= 1e-8
    elif case == "prior": eps[0]["prior"][0,0] = (.8,.2)
    elif case == "eligible_shape": eps[0]["eligible"] = eps[0]["eligible"][:1]
    elif case == "ineligible_action": eps[0]["action_index"][0,2] = 27
    elif case == "negative_action": eps[0]["action_index"][0,0] = -1
    elif case == "large_action": eps[0]["action_index"][0,0] = 54
    elif case == "masked_density":
        eps[0]["probabilities"][0,2,27] = 1e-8; eps[0]["probabilities"][0,2,10] -= 1e-8
    elif case == "chosen_zero":
        p = eps[0]["probabilities"][0,0]
        p[1] += p[0]; p[0] = 0
    elif case == "logp": eps[0]["logp"][0,0] += 1e-7
    elif case == "dtype": eps[0]["features"] = eps[0]["features"].astype(np.float64)
    elif case == "critic_shape": eps[0]["critic_features"] = eps[0]["critic_features"][:,:145]
    elif case == "nan": eps[0]["macro_rewards"][0] = np.nan
    elif case == "missing": del eps[0]["values"]
    elif case == "single": eps = eps[:1]
    elif case == "horizon": horizon = 6
    elif case == "count": counts["actor_optimizer_steps"] = True
    elif case == "optimizer_ownership": aopt.param_groups[0]["params"] = list(critic.parameters())
    elif case == "optimizer_options": aopt.param_groups[0]["lr"] = 1e-3
    elif case == "optimizer_maximize": aopt.param_groups[0]["maximize"] = True
    else: aopt = object()
    before = [p.detach().clone() for m in (actor,critic) for p in m.parameters()]
    with pytest.raises((ValueError,FloatingPointError)):
        L.update_group(actor,critic,aopt,copt,eps,counts,horizon=horizon,live_record=record)
    if isinstance(aopt,torch.optim.Optimizer): assert not aopt.state
    assert not copt.state and not counts.get("critic_optimizer_steps",0)
    assert counts.get("actor_optimizer_steps",0) == (case == "count")
    assert all(torch.equal(p,q) for p,q in zip((p for m in (actor,critic) for p in m.parameters()),before))
    if case in ("logits","density"):
        assert counts["actor_replay_rows"] == counts["density_identity_rows"] == 20
        assert record["initial_identity"]["rows"] == 20


@pytest.mark.parametrize("side",["actor","critic","critic_step","parameter"])
def test_failure_keeps_completed_counts_steps_and_movement(side):
    _,actor,critic = models()
    aopt,copt = L.make_optimizers(actor,critic)
    eps = episodes(actor,critic)
    hook = None
    if side in ("actor","critic"):
        model = actor if side == "actor" else critic
        hook = next(model.parameters()).register_hook(lambda gradient: gradient*float("inf"))
    elif side == "critic_step":
        def fail(): raise RuntimeError("synthetic critic step failure")
        copt.step = fail
    else:
        step = aopt.step
        def corrupt():
            result = step()
            with torch.no_grad(): next(actor.parameters()).view(-1)[0] = float("inf")
            return result
        aopt.step = corrupt
    counts,record = {},{}
    with pytest.raises((RuntimeError,FloatingPointError)):
        L.update_group(actor,critic,aopt,copt,eps,counts,horizon=8,live_record=record)
    if hook is not None: hook.remove()
    completed_actor = int(side != "actor")
    assert record["status"] == "INCOMPLETE" and len(record["epochs"]) == 1
    assert record["completed_counts"]["actor_optimizer_steps"] == completed_actor
    assert record["completed_counts"]["critic_optimizer_steps"] == 0
    assert record["actor_optimizer_step_values"] == [completed_actor]*6
    assert record["critic_optimizer_step_values"] == [0.]*6
    assert counts["actor_replay_rows"] == counts["density_identity_rows"] == 20
    assert counts.get("critic_replay_rows",0) == (4 if side in ("critic","critic_step") else 0)
    if side == "parameter": assert record["actor_movement_l2"] is None


@pytest.mark.parametrize("case",["rounding","zero"])
def test_fp32_suffix_conversion_and_zero_population_variance(case):
    _,actor,critic = models()
    aopt,copt = L.make_optimizers(actor,critic)
    eps = episodes(actor,critic)
    for e in eps: e["macro_rewards"].fill(0); e["values"].fill(0)
    if case == "rounding": eps[0]["macro_rewards"][:] = (1+2**-24,2**-24)
    result = L.update_group(actor,critic,aopt,copt,eps,{},horizon=8)
    if case == "rounding":
        assert result["target_summary"]["max"] == .125
        assert np.float32(eps[0]["macro_rewards"].sum()/8) > .125
    else:
        assert result["advantage_summary"]["std"] == 0
        assert all(e["actor_loss"] == 0 for e in result["epochs"])
