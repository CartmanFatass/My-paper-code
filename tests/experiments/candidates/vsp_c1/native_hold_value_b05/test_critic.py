"""Small deterministic critic tensors; no episode, native environment or PPO fit."""
import math

import pytest
import torch
from torch import nn

from experiments.candidates.ucope.uav_motion_prefix_b01 import policy
from experiments.candidates.vsp_c1.native_hold_value_b01 import critic, study
from experiments.candidates.vsp_c1.native_hold_value_b05.critic import WideCritic


def test_wide_copies_draw_order_counts_rng_and_initial_values():
    global_before = torch.random.get_rng_state().clone()
    common = policy.templates(8301)
    before = {k: v.clone() for k, v in common[1].state_dict().items()}
    action_rng = policy.generator(830100021)
    action_before = action_rng.get_state().clone()
    gated_actor, gated = critic.models(common, "GATED-V", 133, 830100012)
    actor, wide = critic.models(common, "MLP-V", 133, 830100012)
    ordinary_actor, ordinary = critic.models(common, "MLP-V")
    assert type(ordinary) is policy.Critic and isinstance(wide, WideCritic)
    assert torch.equal(global_before, torch.random.get_rng_state())
    assert torch.equal(action_before, action_rng.get_state())
    assert sum(p.numel() for p in wide.parameters()) == 34827
    assert sum(p.numel() for p in gated.parameters()) == 34817
    assert sum(p.numel() for p in ordinary.parameters()) == 34177
    assert all(p.requires_grad and p.dtype == torch.float32 for p in wide.parameters())
    assert [(m.in_features, m.out_features) for m in wide.network if isinstance(m, nn.Linear)] == [(136,128),(128,133),(133,1)]
    for key, value in actor.state_dict().items():
        assert torch.equal(value, gated_actor.state_dict()[key])
        assert torch.equal(value, ordinary_actor.state_dict()[key])
        assert value.data_ptr() != gated_actor.state_dict()[key].data_ptr()
    assert torch.count_nonzero(actor.duration.weight) == torch.count_nonzero(actor.duration.bias) == 0
    for key, value in common[1].state_dict().items():
        assert torch.equal(value, before[key])
    for index in (0,):
        assert torch.equal(wide.network[index].weight, ordinary.network[index].weight)
        assert torch.equal(wide.network[index].bias, ordinary.network[index].bias)
    assert torch.equal(wide.network[2].weight[:128], ordinary.network[2].weight)
    assert torch.equal(wide.network[2].bias[:128], ordinary.network[2].bias)
    assert torch.equal(wide.network[4].weight[:,:128], ordinary.network[4].weight)
    assert torch.equal(wide.network[4].bias, ordinary.network[4].bias)
    assert not torch.count_nonzero(wide.network[4].weight[:,128:])
    rng = torch.Generator(device="cpu").manual_seed(830100012)
    rows = torch.empty(5,128).uniform_(-1/math.sqrt(128),1/math.sqrt(128),generator=rng)
    biases = torch.empty(5).uniform_(-1/math.sqrt(128),1/math.sqrt(128),generator=rng)
    assert rng is not action_rng
    assert torch.equal(wide.network[2].weight[128:],rows)
    assert torch.equal(wide.network[2].bias[128:],biases)
    x = torch.linspace(-.5,.5,4*136).reshape(4,136)
    torch.testing.assert_close(wide(x),ordinary(x),rtol=1e-5,atol=1e-6)
    # Every original input remains connected through the ordinary full first layer.
    x.requires_grad_()
    wide(x).sum().backward()
    assert (x.grad.abs().sum(0)>0).all()
    default_identity=study.checkpoint_identity(study.Config(),"MLP-V","sha")
    assert "critic_architecture" not in default_identity and "critic_parameter_count" not in default_identity
    assert "second_mlp_width" not in default_identity["configuration"]


def test_appended_outputs_then_incoming_parameters_learn():
    wide=WideCritic(policy.templates(17)[1],1700012)
    x=torch.linspace(-.3,.7,3*136).reshape(3,136)
    loss=(wide(x)-torch.tensor([1.,-.7,.4])).square().mean()
    loss.backward()
    assert wide.network[4].weight.grad[:,128:].abs().sum()>0
    assert not torch.count_nonzero(wide.network[2].weight.grad[128:])
    assert not torch.count_nonzero(wide.network[2].bias.grad[128:])
    with torch.no_grad():
        for param in wide.parameters():param.add_(param.grad,alpha=-.1)
    wide.zero_grad()
    (wide(x)-torch.tensor([1.,-.7,.4])).square().mean().backward()
    assert wide.network[2].weight.grad[128:].abs().sum()>0
    assert wide.network[2].bias.grad[128:].abs().sum()>0
    before=wide.network[2].weight[128:].detach().clone()
    with torch.no_grad():wide.network[2].weight.add_(wide.network[2].weight.grad,alpha=-.1)
    assert not torch.equal(before,wide.network[2].weight[128:])


@pytest.mark.parametrize("delta,reading",[(.02,"UP"),(.01,"WITHIN"),(0.,"WITHIN"),(-.01,"WITHIN"),(-.02,"DOWN")])
def test_preserved_primary_regions_and_missing_inputs(delta,reading):
    rows=[dict(arm=arm,phase="eval",episode=0,reset_seed=1,J=value) for arm,value in (("GATED-V",delta),("MLP-V",0.),("H",0.))]
    result=study.primary_from_rows(rows,1,1)
    assert result["reading"]==reading
    assert set(k for k in result if "_minus_" in k)=={"GATED-V_minus_MLP-V","GATED-V_minus_H","MLP-V_minus_H"}
    missing=study.primary_from_rows(rows[:2],1,1)
    assert missing["complete"] and not missing["hover_complete"]
    assert not study.primary_from_rows(rows[:1],1,1)["complete"]
