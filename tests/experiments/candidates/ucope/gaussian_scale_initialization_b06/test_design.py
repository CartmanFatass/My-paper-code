import math

import torch

from experiments.candidates.ucope.gaussian_scale_initialization_b06 import study


def optimizer_parameter_ids(optimizer):
    return {
        id(parameter)
        for group in optimizer.param_groups
        for parameter in group["params"]
    }


def test_only_initial_log_std_differs_and_both_scales_are_trainable():
    rng_before = torch.random.get_rng_state().clone()
    states = study.build_fit_states(study.Config.engineering().master)
    assert torch.equal(rng_before, torch.random.get_rng_state())

    g1, half = states["G1"], states["Ghalf"]
    assert g1["common_initial_sha256"] == half["common_initial_sha256"]
    assert g1["initial_model_sha256"] != half["initial_model_sha256"]
    torch.testing.assert_close(g1["actor"].log_std, torch.zeros(3), rtol=0, atol=0)
    torch.testing.assert_close(
        half["actor"].log_std,
        torch.full((3,), math.log(0.5)),
        rtol=0,
        atol=0,
    )
    assert g1["initial_scale"] == [1.0, 1.0, 1.0]
    torch.testing.assert_close(
        torch.tensor(half["initial_scale"]), torch.full((3,), 0.5), rtol=0, atol=0
    )
    for state in states.values():
        actor = state["actor"]
        assert actor.duration is None
        assert actor.log_std.requires_grad
        assert id(actor.log_std) in optimizer_parameter_ids(state["optimizer"])


def test_paired_fits_have_private_models_optimizers_and_equal_addressed_rng_states():
    states = study.build_fit_states(study.Config.engineering().master)
    g1, half = states["G1"], states["Ghalf"]
    assert next(g1["actor"].parameters()).data_ptr() != next(half["actor"].parameters()).data_ptr()
    assert next(g1["critic"].parameters()).data_ptr() != next(half["critic"].parameters()).data_ptr()
    assert g1["optimizer"] is not half["optimizer"]
    assert g1["velocity_rng"] is not half["velocity_rng"]
    assert g1["duration_rng"] is not half["duration_rng"]
    assert g1["velocity_rng_initial_sha256"] == half["velocity_rng_initial_sha256"]
    assert g1["duration_rng_initial_sha256"] == half["duration_rng_initial_sha256"]
    assert not g1["optimizer"].state and not half["optimizer"].state


def test_fixed_scope_rejects_unselected_or_modified_configs():
    for config in (
        study.Config(master=8940),
        study.Config(master=8941, horizon=255),
        study.Config(master=8941, train_episodes=2046),
        study.Config(master=8941, eval_episodes=63),
        study.Config(master=8941, chunk=16),
        study.Config(master=8941, watchdog_seconds=5999),
    ):
        try:
            study.require_config(config)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted modified config {config}")
    try:
        study.require_config(study.Config(master=9941, horizon=9, fixture=True))
    except ValueError as error:
        assert "fixed B06 engineering fixture" in str(error)
    else:
        raise AssertionError("accepted a modified engineering fixture")
