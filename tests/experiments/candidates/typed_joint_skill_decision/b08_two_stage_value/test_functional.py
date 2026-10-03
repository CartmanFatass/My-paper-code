import numpy as np
import pytest
import torch

from experiments.candidates.typed_joint_skill_decision.b08_two_stage_value import features, functional, model


def menu(scale):
    x = {k: np.ascontiguousarray(((np.arange(np.prod(s), dtype=np.float32).reshape(s) % 29) - 14) * scale)
         for k, s in features.SHAPES.items()}
    x["U"][..., 19] = 0
    for candidate in range(1, 8): x["U"][candidate, candidate, 19] = 1
    x["valid"] = np.array([True] * 6 + [False] * 2)
    return x


@pytest.mark.parametrize("scale", [0., .03, 3., 1e-10])
def test_independent_bits_reference_bounds_and_discrete_ranking(scale, monkeypatch):
    old_threads = torch.get_num_threads(); torch.set_num_threads(1)
    try:
        x, m = menu(scale), model.build(23)
        with torch.no_grad(): deployed = m(functional.menu_tensors(x))[0].numpy().copy()
        state = model.clone_state(m)
        monkeypatch.setattr(model.Scorer, "forward", lambda *a: (_ for _ in ()).throw(AssertionError("deployed forward called")))
        rebuilt = functional.reconstruct(state, x)
        np.testing.assert_array_equal(deployed.view(np.uint32), rebuilt.view(np.uint32))
        result = functional.verify(state, x, deployed)
        assert result["fp32_bits_equal"] and result["within_bounds"]
        assert len(result["prediction_bits"]) == 8
        assert np.all(np.asarray(result["absolute_error"]) <= result["forward_error_bound"])
        # Synthetic stationary ties are resolved outside the scorer; bit equality
        # reproduces a strict descending top-two rule, excluding padding/stay.
        stationarity = [(0., 0., -1., -10, -i, -i) for i in range(8)]
        def shortlist(scores):
            return sorted(range(1, 6), key=lambda i: (float(scores[i]), stationarity[i]), reverse=True)[:2]
        assert shortlist(deployed) == shortlist(rebuilt)
    finally: torch.set_num_threads(old_threads)


def test_reader_rejects_any_padded_bit_mismatch_and_invalid_state():
    x, m = menu(.03), model.build(3)
    state = model.clone_state(m)
    scores = functional.reconstruct(state, x)
    bad = scores.copy(); bad.view(np.uint32)[7] ^= np.uint32(1)
    with pytest.raises(ArithmeticError, match="bits"): functional.verify(state, x, bad)
    state["u.0.weight"] = state["u.0.weight"].double()
    with pytest.raises(ValueError): functional.reconstruct(state, x)


def test_fp64_uses_fp32_numbers_and_standard_gamma_with_underflow_guard():
    x, m = menu(0.), model.build(7)
    state = model.clone_state(m)
    for value in state.values(): value.zero_()
    # Constant hidden features give an independently hand-computable readout.
    state["readout.1.bias"].fill_(.25)
    state["readout.2.weight"].fill_(.5)
    exact, bound = functional.reference(state, x)
    np.testing.assert_array_equal(exact, np.full(8, 4., dtype=np.float64))
    assert np.all(bound > 0)
    assert functional.gamma(32) == (32*2**-24)/(1-32*2**-24)
    scores = functional.reconstruct(state, x)
    assert functional.verify(state, x, scores)["within_bounds"]
    state["readout.1.bias"].fill_(2. ** -149)
    _, bounds = functional.reference(state, x)
    assert functional.verify(state, x, functional.reconstruct(state, x))["within_bounds"]
    assert np.all(bounds > 0)
