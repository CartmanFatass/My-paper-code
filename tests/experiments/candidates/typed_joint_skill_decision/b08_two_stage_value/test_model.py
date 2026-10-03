import numpy as np
import pytest
import torch

from experiments.candidates.typed_joint_skill_decision.b08_two_stage_value import features, model


def inputs(batch=1):
    result = {key: torch.from_numpy((np.arange(np.prod(shape), dtype=np.float32).reshape(shape) % 23) / 23.)
              .unsqueeze(0).repeat(batch, *([1] * len(shape))).contiguous()
              for key, shape in features.SHAPES.items()}
    result["U"][..., 19] = 0
    result["U"][:, 1:, 3, 19] = 1
    result["valid"] = torch.tensor([[True] * 5 + [False] * 3] * batch)
    return result


def test_parameter_map_default_reset_and_rng_isolation():
    before = torch.random.get_rng_state().clone()
    m = model.build(123)
    assert torch.equal(before, torch.random.get_rng_state())
    assert sum(p.numel() for p in m.parameters()) == 10272
    assert "readout.2.bias" not in m.state_dict()
    model.validate_state(m.state_dict())
    assert {k: tuple(v.shape) for k, v in m.state_dict().items()} == model.STATE_SHAPES
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(123)
        expected = torch.nn.Linear(20, 32, device="cpu", dtype=torch.float32)
    assert torch.equal(m.u[0].weight, expected.weight) and torch.equal(m.u[0].bias, expected.bias)
    assert model.state_digest(m.state_dict()) == model.state_digest(model.build(123).state_dict())
    assert model.state_digest(m.state_dict()) != model.state_digest(model.build(124).state_dict())


def test_shapes_gradients_and_padded_independence():
    old_threads = torch.get_num_threads(); torch.set_num_threads(1)
    try:
        m, x = model.build(17), inputs(16)
        scores = m(x)
        assert scores.shape == (16, 8) and scores.dtype == torch.float32
        scores[:, :5].sum().backward()
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters())
        assert sum(float(p.grad.abs().sum()) for p in m.parameters()) > 0
        with torch.no_grad():
            for key in features.SHAPES: x[key][:, 5:] = 999
            assert torch.equal(scores[:, :5], m(x)[:, :5])
        assert m(inputs()).shape == (1, 8)
    finally: torch.set_num_threads(old_threads)


def test_input_and_state_contract_and_movement():
    m = model.build(4); initial = model.clone_state(m)
    with torch.no_grad(): m.readout[2].weight[0, 0] += .125
    final = model.clone_state(m)
    movement = model.parameter_movement(initial, final)
    observed_delta = float(final["readout.2.weight"][0, 0].double() - initial["readout.2.weight"][0, 0].double())
    assert movement["changed_parameters"] == 1 and movement["max_abs"] == observed_delta
    assert movement["l2"] == observed_delta
    final["extra"] = torch.zeros(1)
    with pytest.raises(ValueError): model.validate_state(final)
    with pytest.raises(ValueError): m(inputs(2))
    x = inputs(); x["valid"][0, 2] = False
    with pytest.raises(ValueError): m(x)
