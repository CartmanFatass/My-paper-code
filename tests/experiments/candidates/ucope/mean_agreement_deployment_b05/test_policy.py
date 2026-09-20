import numpy as np
import torch

from experiments.candidates.ucope.mean_agreement_deployment_b05 import study
from experiments.candidates.ucope.reactive_rate_b03.scalar import scalar_actor
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import arm_copy, templates


def actors():
    common = templates(study.Config.engineering().master)
    b_actor, _ = scalar_actor(common)
    g_actor, _ = arm_copy(common, False)
    return b_actor, g_actor


def inputs():
    return (
        torch.zeros(5, 3),
        torch.zeros(5, 64),
        np.zeros((5, 3), dtype=np.float32),
        np.zeros(5, dtype=bool),
        torch.ones(5, 3),
        torch.full((5,), 0.5),
    )


def test_mean_agreement_ties_keep_and_forced_fresh_becomes_eligible():
    b_actor, _ = actors()
    mean, recurrent, previous, _eligible, gaussian, uniform = inputs()
    assert study.keep_from_distances([1.0, 2.0], [1.0, 1.0]).tolist() == [True, False]

    forced = study.command_step(
        b_actor, "C", mean, recurrent, previous, np.zeros(5, dtype=bool), gaussian, uniform
    )
    assert (forced["branch"] == study.FORCED_FRESH).all()
    assert forced["fresh"].all() and forced["next_eligible"].all()
    assert np.isnan(forced["d_keep"]).all()

    tied = study.command_step(
        b_actor, "C", mean, recurrent, previous, np.ones(5, dtype=bool), gaussian, uniform
    )
    assert (tied["branch"] == study.KEEP).all()
    assert not tied["fresh"].any() and not tied["next_eligible"].any()
    assert (tied["d_keep"] == 0).all()
    assert (tied["d_fresh"] > 0).all()
    assert tied["gate_uniforms_used"] == 0


def test_b_end_stays_eligible_and_keep_forces_the_next_tick_fresh():
    b_actor, _ = actors()
    mean, recurrent, previous, _eligible, gaussian, uniform = inputs()
    eligible = np.ones(5, dtype=bool)
    with torch.no_grad():
        b_actor.duration.logits[:] = torch.tensor([-100.0, 100.0])
    ended = study.command_step(
        b_actor, "B", mean, recurrent, previous, eligible, gaussian, uniform
    )
    assert (ended["branch"] == study.END).all()
    assert ended["fresh"].all() and ended["next_eligible"].all()
    assert ended["gate_uniforms_used"] == 5

    with torch.no_grad():
        b_actor.duration.logits[:] = torch.tensor([100.0, -100.0])
    kept = study.command_step(
        b_actor, "B", mean, recurrent, previous, eligible, gaussian, uniform
    )
    assert (kept["branch"] == study.KEEP).all()
    assert not kept["fresh"].any() and not kept["next_eligible"].any()


def test_both_g_modes_are_always_phase_zero_and_use_the_named_execution():
    _, g_actor = actors()
    mean, recurrent, previous, _eligible, gaussian, uniform = inputs()
    mean[:] = torch.tensor([0.2, -0.4, 0.1])
    supplied_wrong_phase = np.ones(5, dtype=bool)
    sampled = study.command_step(
        g_actor, "G_sampled", mean, recurrent, previous,
        supplied_wrong_phase, gaussian, uniform,
    )
    mean_mode = study.command_step(
        g_actor, "G_mean", mean, recurrent, previous,
        supplied_wrong_phase, gaussian, uniform,
    )
    assert not sampled["eligible"].any() and not sampled["next_eligible"].any()
    assert not mean_mode["eligible"].any() and not mean_mode["next_eligible"].any()
    np.testing.assert_allclose(mean_mode["sent"], mean.tanh().numpy(), rtol=0, atol=0)
    expected_sampled = (mean + g_actor.log_std.clamp(-5, 2).exp() * gaussian).tanh()
    np.testing.assert_allclose(sampled["sent"], expected_sampled.detach().numpy(), rtol=0, atol=0)
    assert sampled["gaussian_vectors_used"] == 5
    assert mean_mode["gaussian_vectors_used"] == 0
    assert sampled["gate_uniforms_used"] == mean_mode["gate_uniforms_used"] == 0


def test_private_fixed_slots_do_not_consume_global_rng_and_are_branch_invariant():
    base = 100000 * study.Config.engineering().master
    before = torch.random.get_rng_state().clone()
    gaussian_a, uniforms_a = study.episode_slots(base, 0, 6)
    gaussian_b, uniforms_b = study.episode_slots(base, 0, 6)
    gaussian_next, uniforms_next = study.episode_slots(base, 1, 6)
    assert torch.equal(before, torch.random.get_rng_state())
    assert torch.equal(gaussian_a, gaussian_b) and torch.equal(uniforms_a, uniforms_b)
    assert not torch.equal(gaussian_a, gaussian_next)
    assert not torch.equal(uniforms_a, uniforms_next)
    assert gaussian_a.shape == (6, 5, 3) and uniforms_a.shape == (6, 5)
