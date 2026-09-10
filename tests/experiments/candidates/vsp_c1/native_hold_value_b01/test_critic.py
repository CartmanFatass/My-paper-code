import numpy as np
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import critic_features
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import templates, snapshot
from experiments.candidates.vsp_c1.native_hold_value_b01.critic import (
    GatedCritic, R_COLUMNS, X_COLUMNS, models, movement)


def test_columns_initialization_counts_shapes_and_storage():
    common = templates(9001)
    rng = torch.random.get_rng_state().clone()
    actor, gated = models(common, "GATED-V")
    other, mlp = models(common, "MLP-V")
    assert torch.equal(rng, torch.random.get_rng_state())
    assert sum(p.numel() for p in actor.parameters()) == 32264
    assert sum(p.numel() for p in mlp.parameters()) == 34177
    assert sum(p.numel() for p in gated.parameters()) == 34817
    for a, b in zip(actor.parameters(), other.parameters()):
        assert torch.equal(a, b) and a.data_ptr() != b.data_ptr()
    assert actor.duration is not None and other.duration is not None
    assert torch.count_nonzero(actor.duration.weight) == 0
    assert torch.count_nonzero(actor.duration.bias) == 0
    for a, b in zip(gated.network.parameters(), mlp.network.parameters()):
        assert torch.equal(a, b) and a.data_ptr() != b.data_ptr()
    for shape in ((136,), (8, 136), (2, 8, 136)):
        x = torch.rand(shape, generator=torch.Generator().manual_seed(3))
        assert gated(x).shape == x.shape[:-1]
        torch.testing.assert_close(gated(x), mlp(x), rtol=1e-5, atol=1e-6)
    state = np.zeros(116, dtype=np.float32)
    last = np.arange(15, dtype=np.float32).reshape(5, 3)
    remaining = np.arange(5)
    features = critic_features(state, last, remaining)
    np.testing.assert_equal(features[list(R_COLUMNS)], remaining / 4)
    np.testing.assert_equal(features[116:].reshape(5, 4)[:, :3], last)
    assert len(X_COLUMNS) == 131 and set(X_COLUMNS).isdisjoint(R_COLUMNS)


def test_gate_contribution_gradient_and_absolute_exposure():
    actor, critic = models(templates(9001), "GATED-V")
    initial = snapshot(actor, critic)
    x = torch.ones(2, 136) * .25
    x[..., R_COLUMNS] = 0
    before = critic(x).detach()
    critic(x).sum().backward()
    assert torch.count_nonzero(critic.gate.grad) == 0
    with torch.no_grad():
        critic.gate.fill_(.2)
    torch.testing.assert_close(critic(x), before)
    x[..., R_COLUMNS] = .75
    assert not torch.allclose(critic(x), GatedCritic(templates(9001)[1])(x))
    critic.zero_grad()
    critic(x).sum().backward()
    assert torch.count_nonzero(critic.gate.grad) > 0
    result = movement(initial, actor, critic)
    assert result["gate"]["relative_displacement"] is None
    assert result["gate"]["displacement"] == result["gate"]["final_norm"] > 0
    for name in ("common_actor", "critic", "total"):
        assert np.isfinite(result[name]["relative_displacement"])
    assert "duration" in result
