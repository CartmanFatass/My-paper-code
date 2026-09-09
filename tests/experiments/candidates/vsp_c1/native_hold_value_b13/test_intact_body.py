"""Offline FP32 critic correspondence; no episode or optimizer fit."""
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import policy
from experiments.candidates.vsp_c1.native_hold_value_b01 import critic


def test_complete_common_body_zero_gate_and_separate_mutable_parameters():
    torch.set_num_threads(1)
    before = torch.random.get_rng_state().clone()
    common = policy.templates(8601)
    original = {k: v.clone() for k, v in common[1].state_dict().items()}
    behavior_rng = policy.generator(860100021)
    behavior_before = behavior_rng.get_state().clone()
    ga, gated = critic.models(common, "GATED-V", 133, 860100012, intact_body=True)
    ma, ordinary = critic.models(common, "MLP-V", 133, 860100012, intact_body=True)
    assert torch.equal(before, torch.random.get_rng_state())
    assert torch.equal(behavior_before, behavior_rng.get_state())
    assert sum(p.numel() for p in gated.parameters()) == 35467
    assert sum(p.numel() for p in ordinary.parameters()) == 34827
    assert gated.gate.shape == (128, 5) and torch.count_nonzero(gated.gate) == 0
    for model in (gated, ordinary):
        assert model.network[2].weight.shape == (133, 128)
        assert model.network[2].bias.shape == (133,)
        assert model.network[4].weight.shape == (1, 133)
        assert torch.count_nonzero(model.network[4].weight[:, 128:]) == 0
        assert all(p.dtype == torch.float32 and p.requires_grad for p in model.parameters())
    for g, m in ((gated.network, ordinary.network), (ga, ma)):
        for key, value in g.state_dict().items():
            assert torch.equal(value, m.state_dict()[key])
            assert value.data_ptr() != m.state_dict()[key].data_ptr()
    assert all(torch.equal(value, original[key]) for key, value in common[1].state_dict().items())
    assert torch.count_nonzero(ordinary.network[2].weight[128:]) > 0
    inputs = torch.linspace(-2., 2., 12 * 136).reshape(12, 136)
    inputs[:, critic.R_COLUMNS] = torch.tensor([0., .25, .5, .75, 0.])
    torch.testing.assert_close(gated(inputs), ordinary(inputs), rtol=1e-5, atol=1e-6)
    with torch.no_grad():
        gated.network[2].weight[-1, 0] += 1
    assert not torch.equal(gated.network[2].weight, ordinary.network[2].weight)
    # Gate remains trainable through the intact body under nonzero remaining hold.
    gated(inputs).sum().backward()
    assert gated.gate.grad is not None and gated.gate.grad.abs().sum() > 0
