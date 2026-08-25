from __future__ import annotations

import numpy as np
import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (
    ACTIVE_CONTINUATION,
    C0P0,
    C0P1,
    C1P0,
    C1P1,
    FLEX,
    NEW_EPOCH,
    REGISTERED,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (
    DeterministicZeroLinear,
    TBCFVModel,
    apply_affine_fixture_uniforms,
    apply_registered_block_update,
    averaged_episode_score,
    exact_advantage_loss,
    make_conformance_fixture_model,
    make_paired_conformance_models,
    make_pointer_inputs,
    registered_plain_sgd_step,
    required_affine_fixture_uniforms,
    selected_claim_log_probability,
    stopped_actor_plan,
    stopped_normal_inverse_cdf,
    stopped_normal_log_density,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.packages import (
    FixtureDrawBank,
    initialize_plans,
    transition_plans,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.scripted import (
    coherent_scaffold,
    fragmented_scaffold,
    independent_nearest,
)


def _v(a: float, b: float = 0.0, c: float = 0.0, d: float = 0.0) -> torch.Tensor:
    return torch.tensor([a, b, c, d], dtype=torch.float64)


def _pointer_fixture(plans: torch.Tensor) -> torch.Tensor:
    n = plans.shape[0]
    pooled = torch.zeros((n, 64), dtype=torch.float64)
    own = torch.zeros((n, 5), dtype=torch.float64)
    context = torch.zeros((n, 4), dtype=torch.float64)
    candidate = torch.zeros((n, 6, 4), dtype=torch.float64)
    candidate[:, :, 0] = torch.tensor([-1.0, -0.6, -0.2, 0.2, 0.6, 1.0], dtype=torch.float64)
    candidate[:, :, 3] = torch.tensor([-0.8, -0.4, 0.0, 0.4, 0.8, 0.2], dtype=torch.float64)
    return make_pointer_inputs(pooled, own, context, candidate, plans)


def test_exact_inventory_set_encoders_and_construction_preserve_torch_rng() -> None:
    before = torch.random.get_rng_state().clone()
    zero = TBCFVModel()
    model = make_conformance_fixture_model()
    after = torch.random.get_rng_state().clone()
    assert torch.equal(before, after)
    assert zero.parameter_count == REGISTERED.parameters_per_arm == 26_161
    assert model.parameter_count == 26_161

    one_agent = torch.tensor([[[0.4, -0.3, 1.0]]], dtype=torch.float64)
    repeated_agents = one_agent.expand(1, 7, 3).clone()
    beacon = torch.tensor(
        [[[0.0, 1.0, 0.5], [0.5, 0.5, 0.5], [1.0, 0.0, 1.0],
          [0.0, -1.0, 0.5], [-0.5, -0.5, 1.0], [-1.0, 0.0, 0.5]]],
        dtype=torch.float64,
    )
    context = torch.tensor([[7.0 / 12.0, 0.0, 0.0, 0.0]], dtype=torch.float64)
    one_summary = model.manager(one_agent, beacon, context).pooled_summary[..., :32]
    repeated_summary = model.manager(repeated_agents, beacon, context).pooled_summary[..., :32]
    assert torch.equal(one_summary, repeated_summary)

    permuted = beacon[:, torch.tensor([4, 0, 5, 2, 1, 3])]
    assert torch.allclose(
        model.manager(repeated_agents, beacon, context).pooled_summary,
        model.manager(repeated_agents, permuted, context).pooled_summary,
        atol=1.0e-16,
        rtol=0.0,
    )
    manager = model.manager(repeated_agents, beacon, context)
    assert manager.mean.shape == (1, 4)
    assert bool(torch.all(manager.log_scale > -2.0))
    assert bool(torch.all(manager.log_scale < 0.0))


def test_stopped_normal_score_actor_and_flex_gradient_boundaries() -> None:
    sample = torch.tensor([[0.3, -0.2, 0.4, 0.1]], dtype=torch.float64, requires_grad=True)
    mean = torch.tensor([[0.0, 0.1, -0.1, 0.2]], dtype=torch.float64, requires_grad=True)
    raw = torch.tensor([[0.2, -0.4, 0.3, -0.1]], dtype=torch.float64, requires_grad=True)
    stopped_normal_log_density(sample, mean, raw).sum().backward()
    assert sample.grad is None
    assert mean.grad is not None and torch.count_nonzero(mean.grad) > 0
    assert raw.grad is not None and torch.count_nonzero(raw.grad) > 0

    actor_model = make_conformance_fixture_model()
    actor_plan = torch.tensor([[0.2, 0.0, 0.0, 0.0]], dtype=torch.float64, requires_grad=True)
    actor_probabilities = actor_model.claim_probabilities(_pointer_fixture(stopped_actor_plan(actor_plan)))
    selected_claim_log_probability(actor_probabilities, torch.tensor([5])).sum().backward()
    assert actor_plan.grad is None
    assert actor_model.pointer_first.weight.grad is not None
    assert torch.count_nonzero(actor_model.pointer_first.weight.grad) > 0

    flex_model = make_conformance_fixture_model()
    with torch.no_grad():
        flex_model.common_update_final.weight[0, 0] = 0.60
        flex_model.agent_update_final.weight[0, 0] = 0.40
        flex_model.agent_update_final.weight[0, 1] = -0.25
    base = torch.tensor(
        [[0.2, 0.0, 0.0, 0.0], [0.2, 0.0, 0.0, 0.0]],
        dtype=torch.float64,
        requires_grad=True,
    )
    event = torch.zeros((2, 68), dtype=torch.float64)
    event[:, 0] = torch.tensor([0.5, 0.5], dtype=torch.float64)
    physical = torch.tensor(
        [[0.7, 0.2, 0.0, 0.0, 0.0], [-0.6, 0.8, 1.0, 0.0, 1.0]],
        dtype=torch.float64,
    )
    noise = torch.tensor(
        [[0.1, 0.2, 0.3, 0.4], [-0.4, -0.3, -0.2, -0.1]],
        dtype=torch.float64,
        requires_grad=True,
    )
    flex_plan, common_delta, agent_delta = flex_model.event_plan(FLEX, base, event, physical, noise)
    assert common_delta is not None and agent_delta is not None
    loss = -torch.log(flex_model.claim_probabilities(_pointer_fixture(flex_plan))[:, 5]).sum()
    loss.backward()
    assert base.grad is None
    assert noise.grad is None
    assert flex_model.common_update_final.weight.grad is not None
    assert torch.count_nonzero(flex_model.common_update_final.weight.grad) > 0
    assert flex_model.common_update_hidden.weight.grad is not None
    assert torch.count_nonzero(flex_model.common_update_hidden.weight.grad) > 0
    assert flex_model.agent_update_final.weight.grad is not None
    assert torch.count_nonzero(flex_model.agent_update_final.weight.grad) > 0
    assert flex_model.agent_update_hidden.weight.grad is not None
    assert torch.count_nonzero(flex_model.agent_update_hidden.weight.grad) > 0


def test_affine_fixture_transform_and_complete_five_arm_copy_are_rng_neutral() -> None:
    before = torch.random.get_rng_state().clone()
    template = TBCFVModel()
    required = required_affine_fixture_uniforms(template)
    uniforms: dict[str, torch.Tensor] = {}
    for name, shape in required.items():
        values = torch.full(shape, 0.25, dtype=torch.float64)
        values.reshape(-1)[0] = 0.0
        values.reshape(-1)[-1] = 1.0
        uniforms[name] = values
    models = make_paired_conformance_models(uniforms)
    after = torch.random.get_rng_state().clone()
    assert torch.equal(before, after)
    assert tuple(models) == (C1P1, FLEX, C1P0, C0P1, C0P0)

    reference_state = models[C1P1].state_dict()
    for arm, model in models.items():
        assert model.parameter_count == 26_161, arm
        for name, tensor in model.state_dict().items():
            assert torch.equal(tensor, reference_state[name]), (arm, name)
        for name, module in model.named_modules():
            if not isinstance(module, DeterministicZeroLinear):
                continue
            assert torch.count_nonzero(module.bias) == 0
            if name in ("common_update_final", "agent_update_final"):
                assert torch.count_nonzero(module.weight) == 0
            else:
                bound = (6.0 / (module.in_features + module.out_features)) ** 0.5
                assert float(module.weight.min()) == pytest.approx(-bound, abs=1.0e-15)
                assert float(module.weight.max()) == pytest.approx(bound, abs=1.0e-15)

    malformed = dict(uniforms)
    malformed.pop(next(iter(malformed)))
    with pytest.raises(ValueError, match="keys mismatch"):
        apply_affine_fixture_uniforms(TBCFVModel(), malformed)


def test_stopped_normal_inverse_cdf_uses_only_caller_fixture_uniforms() -> None:
    before = torch.random.get_rng_state().clone()
    uniforms = torch.tensor(
        [[0.5, 0.8413447460685429, 0.15865525393145707, 0.5]], dtype=torch.float64
    )
    mean = torch.zeros((1, 4), dtype=torch.float64, requires_grad=True)
    raw = torch.zeros((1, 4), dtype=torch.float64, requires_grad=True)
    plan = stopped_normal_inverse_cdf(uniforms, mean, raw)
    after = torch.random.get_rng_state().clone()
    expected_scale = torch.exp(torch.tensor(-1.0, dtype=torch.float64))
    assert torch.allclose(
        plan,
        torch.tensor([[0.0, expected_scale, -expected_scale, 0.0]], dtype=torch.float64),
        atol=2.0e-16,
        rtol=0.0,
    )
    assert not plan.requires_grad
    assert mean.grad is None and raw.grad is None
    assert torch.equal(before, after)
    with pytest.raises(ValueError, match=r"strictly inside \(0,1\)"):
        stopped_normal_inverse_cdf(torch.zeros_like(uniforms), mean, raw)


def test_episode_score_averages_exact_64_advantage_loss_and_unused_no_score_path() -> None:
    ell_z, ell_a, ell = averaged_episode_score(
        torch.tensor([1.0, 3.0], dtype=torch.float64),
        torch.tensor([2.0, 4.0, 6.0], dtype=torch.float64),
    )
    assert float(ell_z) == 2.0
    assert float(ell_a) == 4.0
    assert float(ell) == 6.0

    cells = torch.arange(8, dtype=torch.int64).repeat_interleave(8)
    returns = (cells.to(torch.float64) + 1.0).requires_grad_()
    baselines = torch.arange(8, dtype=torch.float64).requires_grad_()
    used_mean = torch.zeros((1, 4), dtype=torch.float64, requires_grad=True)
    used_raw = torch.zeros((1, 4), dtype=torch.float64, requires_grad=True)
    unused_mean = torch.ones((1, 4), dtype=torch.float64, requires_grad=True)
    unused_raw = torch.ones((1, 4), dtype=torch.float64, requires_grad=True)
    used_sample = torch.tensor([[0.2, -0.1, 0.3, -0.2]], dtype=torch.float64)
    used_density = stopped_normal_log_density(used_sample, used_mean, used_raw).reshape(1)
    plan_terms = [used_density for _ in range(64)]
    claim_terms = [torch.tensor([-0.2, -0.4], dtype=torch.float64) for _ in range(64)]
    loss = exact_advantage_loss(returns, cells, baselines, plan_terms, claim_terms)
    expected_score = used_density.detach()[0] - 0.3
    assert torch.allclose(loss.detach(), -expected_score, atol=1.0e-15, rtol=0.0)
    loss.backward()
    assert returns.grad is None and baselines.grad is None
    assert used_mean.grad is not None and torch.count_nonzero(used_mean.grad) > 0
    assert used_raw.grad is not None and torch.count_nonzero(used_raw.grad) > 0
    # These fixture draws were banked but unused; they have no forward or score path.
    assert unused_mean.grad is None and unused_raw.grad is None

    with pytest.raises(ValueError, match="exactly eight"):
        exact_advantage_loss(returns, torch.zeros(64, dtype=torch.int64), baselines, plan_terms, claim_terms)


def _flat_parameters(model: TBCFVModel) -> torch.Tensor:
    return torch.cat([parameter.detach().reshape(-1) for parameter in model.parameters()])


def test_whole_tensor_zero_nonzero_sgd_and_post_update_baseline_order() -> None:
    zero_model = TBCFVModel()
    zero_before = _flat_parameters(zero_model).clone()
    zero_audit = registered_plain_sgd_step(zero_model)
    assert not zero_audit.nonzero
    assert zero_audit.parameter_delta_norm == 0.0
    assert torch.equal(_flat_parameters(zero_model), zero_before)

    model = TBCFVModel()
    first_parameter = next(model.parameters())
    first_parameter.grad = torch.arange(
        1, first_parameter.numel() + 1, dtype=torch.float64
    ).reshape_as(first_parameter)
    before = _flat_parameters(model).clone()
    cells = torch.arange(8, dtype=torch.int64).repeat_interleave(8)
    returns = cells.to(torch.float64) + 2.0
    block = apply_registered_block_update(
        model,
        torch.arange(8, dtype=torch.float64),
        returns,
        cells,
    )
    delta = _flat_parameters(model) - before
    assert block.event_order == ("parameter_update", "baseline_update")
    assert block.parameter_update.nonzero
    assert block.parameter_update.direction_norm == 0.05
    assert block.parameter_update.parameter_delta_norm == pytest.approx(0.0005, abs=1.0e-18)
    assert float(torch.linalg.vector_norm(delta)) == pytest.approx(0.0005, abs=1.0e-15)
    expected_baselines = 0.95 * torch.arange(8, dtype=torch.float64) + 0.05 * returns[::8]
    assert torch.allclose(block.updated_baselines, expected_baselines, atol=1.0e-15, rtol=0.0)
    assert not block.updated_baselines.requires_grad


def test_zero_final_containment_and_output_connected_strict_extension() -> None:
    model = make_conformance_fixture_model()
    base = torch.tensor(
        [[0.25, 0.0, 0.0, 0.0], [0.25, 0.0, 0.0, 0.0]], dtype=torch.float64
    )
    event = torch.zeros((2, 68), dtype=torch.float64)
    event[:, 0] = 0.5
    physical = torch.tensor(
        [[0.8, 0.2, 0.0, 0.0, 0.0], [-0.7, 0.6, 1.0, 0.0, 1.0]], dtype=torch.float64
    )
    noise = torch.tensor(
        [[0.1, 0.2, 0.3, 0.4], [-0.1, -0.2, -0.3, -0.4]], dtype=torch.float64
    )
    treatment_plan, treatment_common, treatment_agent = model.event_plan(
        C1P1, base, event, physical, noise
    )
    flex_plan, common_zero, agent_zero = model.event_plan(FLEX, base, event, physical, noise)
    assert treatment_common is None and treatment_agent is None
    assert common_zero is not None and agent_zero is not None
    assert torch.count_nonzero(common_zero) == 0
    assert torch.count_nonzero(agent_zero) == 0
    treatment_probabilities = model.claim_probabilities(_pointer_fixture(treatment_plan))
    assert torch.equal(treatment_plan, flex_plan)
    assert torch.equal(treatment_probabilities, model.claim_probabilities(_pointer_fixture(flex_plan)))

    with torch.no_grad():
        model.common_update_final.weight[0, 0] = 0.65
        model.agent_update_final.weight[0, 0] = 0.45
        model.agent_update_final.weight[0, 1] = -0.30
    strict_plan, strict_common, strict_agent = model.event_plan(FLEX, base, event, physical, noise)
    assert strict_common is not None and torch.count_nonzero(strict_common) > 0
    assert strict_agent is not None
    assert not torch.equal(strict_agent[0], strict_agent[1])
    strict_probabilities = model.claim_probabilities(_pointer_fixture(strict_plan))
    assert not torch.equal(strict_probabilities, treatment_probabilities)
    # Treatment is hard-masked and remains unchanged after FLEX-only final weights change.
    unchanged_treatment, _, _ = model.event_plan(C1P1, base, event, physical, noise)
    assert torch.equal(
        model.claim_probabilities(_pointer_fixture(unchanged_treatment)), treatment_probabilities
    )


def test_five_package_draw_tying_renewal_and_physical_survivor_transport() -> None:
    draws = FixtureDrawBank(
        epoch_common=_v(1.0),
        epoch_private={"alpha": _v(11.0), "bravo": _v(12.0)},
        active_common_refresh=_v(2.0),
        active_private_refresh={"bravo": _v(21.0), "charlie": _v(22.0)},
        newcomer_private={"charlie": _v(13.0)},
        new_epoch_common=_v(3.0),
        new_epoch_private={"bravo": _v(31.0), "charlie": _v(32.0)},
        flex_event_noise={"bravo": _v(0.1), "charlie": _v(-0.1)},
    )

    for arm in (C1P1, FLEX, C1P0):
        initial = initialize_plans(arm, ("alpha", "bravo"), draws)
        assert torch.equal(initial.plans[0], initial.plans[1])
        assert initial.used_draws == ("epoch_common",)
        assert initial.score_draws == (("epoch_common", None),)
    for arm in (C0P1, C0P0):
        initial = initialize_plans(arm, ("alpha", "bravo"), draws)
        assert torch.equal(initial.plans[:, 0], torch.tensor([11.0, 12.0], dtype=torch.float64))
        assert initial.score_draws == (("epoch_private", "alpha"), ("epoch_private", "bravo"))

    c1p1 = initialize_plans(C1P1, ("alpha", "bravo"), draws)
    persistent = transition_plans(c1p1.state, ("bravo", "charlie"), ACTIVE_CONTINUATION, draws)
    assert torch.equal(persistent.plans[:, 0], torch.tensor([1.0, 1.0], dtype=torch.float64))
    assert persistent.common_delta is None and persistent.agent_delta is None
    assert persistent.score_draws == ()

    c1p0 = initialize_plans(C1P0, ("alpha", "bravo"), draws)
    refreshed_common = transition_plans(c1p0.state, ("bravo", "charlie"), ACTIVE_CONTINUATION, draws)
    assert torch.equal(refreshed_common.plans[:, 0], torch.tensor([2.0, 2.0], dtype=torch.float64))
    assert refreshed_common.score_draws == (("active_common_refresh", None),)

    c0p1 = initialize_plans(C0P1, ("alpha", "bravo"), draws)
    transported = transition_plans(c0p1.state, ("charlie", "bravo"), ACTIVE_CONTINUATION, draws)
    assert torch.equal(transported.plans[:, 0], torch.tensor([13.0, 12.0], dtype=torch.float64))
    assert transported.used_draws == ("survivor_private_transport", "newcomer_private")
    assert transported.score_draws == (("newcomer_private", "charlie"),)
    assert transported.plans.shape == (2, 4)  # no physical key or fixed roster slot is actor-visible

    c0p0 = initialize_plans(C0P0, ("alpha", "bravo"), draws)
    refreshed_private = transition_plans(c0p0.state, ("bravo", "charlie"), ACTIVE_CONTINUATION, draws)
    assert torch.equal(refreshed_private.plans[:, 0], torch.tensor([21.0, 22.0], dtype=torch.float64))
    assert refreshed_private.score_draws == (
        ("active_private_refresh", "bravo"),
        ("active_private_refresh", "charlie"),
    )

    for arm, start in ((C1P1, c1p1), (C1P0, c1p0)):
        new_epoch = transition_plans(start.state, ("bravo", "charlie"), NEW_EPOCH, draws)
        assert torch.equal(new_epoch.plans[:, 0], torch.tensor([3.0, 3.0], dtype=torch.float64))
    new_private_epoch = transition_plans(c0p1.state, ("bravo", "charlie"), NEW_EPOCH, draws)
    assert torch.equal(new_private_epoch.plans[:, 0], torch.tensor([31.0, 32.0], dtype=torch.float64))
    new_private_epoch_c0p0 = transition_plans(c0p0.state, ("bravo", "charlie"), NEW_EPOCH, draws)
    assert torch.equal(
        new_private_epoch_c0p0.plans[:, 0], torch.tensor([31.0, 32.0], dtype=torch.float64)
    )

    flex = initialize_plans(FLEX, ("alpha", "bravo"), draws)
    flex_epoch = transition_plans(
        flex.state,
        ("bravo", "charlie"),
        NEW_EPOCH,
        draws,
        model=make_conformance_fixture_model(),
        public_event_summary=torch.zeros(68, dtype=torch.float64),
        physical_features=torch.zeros((2, 5), dtype=torch.float64),
    )
    assert torch.equal(flex_epoch.plans[:, 0], torch.tensor([3.0, 3.0], dtype=torch.float64))
    assert flex_epoch.used_draws == ("new_epoch_common", "flex_event_noise")
    assert flex_epoch.score_draws == (("new_epoch_common", None),)


def test_flex_package_uses_only_caller_fixture_noise_and_has_zero_unused_paths() -> None:
    model = make_conformance_fixture_model()
    draws = FixtureDrawBank(
        epoch_common=_v(1.0),
        flex_event_noise={"a": _v(0.1, 0.2), "b": _v(-0.1, -0.2)},
    )
    initial = initialize_plans(FLEX, ("a", "b"), draws)
    event = torch.zeros(68, dtype=torch.float64)
    physical = torch.tensor(
        [[0.5, 0.5, 0.0, 0.0, 0.0], [-0.5, 0.5, 1.0, 0.0, 1.0]], dtype=torch.float64
    )
    transition = transition_plans(
        initial.state,
        ("a", "b"),
        ACTIVE_CONTINUATION,
        draws,
        model=model,
        public_event_summary=event,
        physical_features=physical,
    )
    assert transition.used_draws == ("common_physical_transport", "flex_event_noise")
    assert transition.score_draws == ()
    assert transition.common_delta is not None and torch.count_nonzero(transition.common_delta) == 0
    assert transition.agent_delta is not None and torch.count_nonzero(transition.agent_delta) == 0
    assert torch.equal(transition.plans, initial.plans)


def test_coherent_assignment_distance_change_and_lexicographic_laws() -> None:
    positions = [10, 10, 10, 10, 10, 10]
    beacons = [0, 20, 40, 60, 80, 100]
    demand = [1, 1, 1, 1, 1, 1]

    first = coherent_scaffold(
        positions,
        beacons,
        demand,
        first_claim_or_new_epoch=True,
        entry_tiebreak=[0, 1, 2, 3, 4, 5],
    )
    assert first.tolist() == [0, 1, 2, 3, 4, 5]

    reversed_previous = [5, 4, 3, 2, 1, 0]
    survivor_priority = coherent_scaffold(
        positions,
        beacons,
        demand,
        previous_claims=reversed_previous,
        survivor=[True] * 6,
        entry_tiebreak=[0, 1, 2, 3, 4, 5],
    )
    assert survivor_priority.tolist() == reversed_previous

    reordered = coherent_scaffold(
        positions,
        beacons,
        demand,
        first_claim_or_new_epoch=True,
        entry_tiebreak=[5, 4, 3, 2, 1, 0],
    )
    assert reordered.tolist() == [5, 4, 3, 2, 1, 0]


def test_fragmented_first_two_post_event_edits_and_independent_nearest_tie() -> None:
    positions = [10, 10, 10, 10, 10, 10]
    beacons = [0, 20, 40, 60, 80, 100]
    demand = [1, 1, 1, 1, 1, 1]
    coherent = coherent_scaffold(
        positions, beacons, demand, first_claim_or_new_epoch=True, entry_tiebreak=range(6)
    )
    expected_fragmented = np.asarray([0, 0, 2, 2, 4, 4], dtype=np.int64)
    for claim_index in (0, 1):
        fragmented = fragmented_scaffold(
            positions,
            beacons,
            demand,
            active_churn=True,
            post_event_claim_index=claim_index,
            first_claim_or_new_epoch=True,
            entry_tiebreak=range(6),
        )
        assert np.array_equal(fragmented, expected_fragmented)
        coherent_counts = np.bincount(coherent, minlength=6)
        fragmented_counts = np.bincount(fragmented, minlength=6)
        assert (fragmented_counts - coherent_counts).tolist() == [1, -1, 1, -1, 1, -1]

    assert np.array_equal(
        fragmented_scaffold(
            positions,
            beacons,
            demand,
            active_churn=True,
            post_event_claim_index=2,
            first_claim_or_new_epoch=True,
            entry_tiebreak=range(6),
        ),
        coherent,
    )
    assert np.array_equal(
        fragmented_scaffold(
            positions,
            beacons,
            demand,
            active_churn=False,
            post_event_claim_index=0,
            first_claim_or_new_epoch=True,
            entry_tiebreak=range(6),
        ),
        coherent,
    )
    assert independent_nearest([10, 30, 110], beacons).tolist() == [0, 1, 0]


def test_malformed_surfaces_fail_closed() -> None:
    model = TBCFVModel()
    with pytest.raises(ValueError, match="six"):
        model.claim_probabilities(torch.zeros((2, 5, 81), dtype=torch.float64))
    with pytest.raises(ValueError, match="dimension 81"):
        model.pointer_logits(torch.zeros((2, 6, 80), dtype=torch.float64))
    with pytest.raises(ValueError, match="absent"):
        initialize_plans(C1P1, ("a",), FixtureDrawBank())
    with pytest.raises(ValueError, match="sum to N"):
        coherent_scaffold([0] * 6, [0, 20, 40, 60, 80, 100], [1, 1, 1, 1, 1, 0])
