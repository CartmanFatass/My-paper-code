"""Proof-sized acceptance for the G26 prefix-contextual diagnostic."""

from __future__ import annotations

import torch

from ha_ctse_process import delayed_battery_roster_g18 as source
from ha_ctse_process.anchored_residual_g19 import maximum_state_difference
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from ha_ctse_process.prefix_contextual_residual_g26 import (
    PrefixContextualResidualContinuousRosterPolicy,
    PrefixContextualResidualPolicy,
)
from scripts import probe_prefix_contextual_residual_expressivity_g26 as probe


def _assert_step_equal(left: object, right: object) -> None:
    for name in (
        "actions",
        "pre_tanh_actions",
        "token_log_probs",
        "token_entropies",
        "value",
        "next_hidden",
        "prefix_action_sums",
        "likelihood_mask",
    ):
        torch.testing.assert_close(
            getattr(left, name), getattr(right, name), rtol=0, atol=0
        )


def _generic_pair() -> tuple[
    ContinuousRosterPolicy, PrefixContextualResidualPolicy, dict[str, torch.Tensor]
]:
    torch.manual_seed(3_611_001)
    base = ContinuousRosterPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    residual = PrefixContextualResidualPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    missing, unexpected = residual.policy.load_state_dict(
        base.state_dict(), strict=False
    )
    assert unexpected == []
    assert all(name.startswith("delayed_residual.") for name in missing)
    arguments = {
        "observations": torch.randn(2, 3, 5),
        "active_mask": torch.tensor(
            [[True, True, False], [True, False, True]]
        ),
        "critic_state": torch.randn(2, 4),
        "hidden": torch.randn(2, 3, 8),
    }
    return base, residual, arguments


def test_zero_residual_exactly_matches_base_in_all_execution_modes() -> None:
    base, residual, arguments = _generic_pair()
    noise = torch.randn(2, 3, 2)
    sampled = base.forward_step(**arguments, sampling_noise=noise)
    _assert_step_equal(
        sampled,
        residual.policy.forward_step(**arguments, sampling_noise=noise),
    )
    _assert_step_equal(
        base.forward_step(**arguments, deterministic=True),
        residual.policy.forward_step(**arguments, deterministic=True),
    )
    _assert_step_equal(
        base.forward_step(
            **arguments, teacher_pre_tanh=sampled.pre_tanh_actions
        ),
        residual.policy.forward_step(
            **arguments, teacher_pre_tanh=sampled.pre_tanh_actions
        ),
    )


def test_proposal_reads_direct_context_and_live_prefix() -> None:
    core = PrefixContextualResidualContinuousRosterPolicy(
        3,
        2,
        member_capacity=3,
        action_dim=1,
        hidden_dim=4,
    )
    first = core.delayed_residual[0]
    final = core.delayed_residual[-1]
    assert isinstance(first, torch.nn.Linear)
    assert isinstance(final, torch.nn.Linear)
    with torch.no_grad():
        first.weight.zero_()
        first.bias.zero_()
        final.weight.zero_()
        final.bias.zero_()
        first.weight[0, core.hidden_dim] = 0.75
        first.weight[0, 3 * core.hidden_dim] = 1.25
        final.weight[0, 0] = 1.0
    arguments = {
        "encoded_member": torch.zeros(2, 4),
        "context": torch.zeros(2, 4),
        "hidden": torch.zeros(2, 4),
        "prefix_fraction": torch.zeros(2, 1),
        "observation": torch.zeros(2, 3),
    }
    baseline = core.residual_proposal(**arguments)
    context_changed = core.residual_proposal(
        **(arguments | {"context": torch.ones(2, 4)})
    )
    prefix_changed = core.residual_proposal(
        **(arguments | {"prefix_fraction": torch.ones(2, 1)})
    )
    assert torch.count_nonzero(context_changed - baseline) == 2
    assert torch.count_nonzero(prefix_changed - baseline) == 2


def test_proposal_is_permutation_equivariant_and_padding_independent() -> None:
    torch.manual_seed(3_611_002)
    core = PrefixContextualResidualContinuousRosterPolicy(
        3,
        2,
        member_capacity=3,
        action_dim=2,
        hidden_dim=4,
    )
    final = core.delayed_residual[-1]
    assert isinstance(final, torch.nn.Linear)
    with torch.no_grad():
        torch.nn.init.normal_(final.weight, std=0.1)
        torch.nn.init.normal_(final.bias, std=0.1)
    encoded = torch.randn(2, 3, 4)
    context = torch.randn(2, 1, 4).expand(-1, 3, -1)
    hidden = torch.randn(2, 3, 4)
    prefix = torch.randn(2, 3, 2)
    observations = torch.randn(2, 3, 3)
    direct = core.residual_proposal(
        encoded_member=encoded,
        context=context,
        hidden=hidden,
        prefix_fraction=prefix,
        observation=observations,
    )
    permutation = torch.tensor([2, 0, 1])
    permuted = core.residual_proposal(
        encoded_member=encoded[:, permutation],
        context=context[:, permutation],
        hidden=hidden[:, permutation],
        prefix_fraction=prefix[:, permutation],
        observation=observations[:, permutation],
    )
    torch.testing.assert_close(
        permuted, direct[:, permutation], rtol=0, atol=1e-7
    )

    padded = PrefixContextualResidualContinuousRosterPolicy(
        3,
        2,
        member_capacity=5,
        action_dim=2,
        hidden_dim=4,
    )
    padded.delayed_residual.load_state_dict(core.delayed_residual.state_dict())
    padded_output = padded.residual_proposal(
        encoded_member=torch.cat((encoded, torch.randn(2, 2, 4)), dim=1),
        context=torch.cat((context, torch.randn(2, 2, 4)), dim=1),
        hidden=torch.cat((hidden, torch.randn(2, 2, 4)), dim=1),
        prefix_fraction=torch.cat((prefix, torch.randn(2, 2, 2)), dim=1),
        observation=torch.cat((observations, torch.randn(2, 2, 3)), dim=1),
    )
    torch.testing.assert_close(
        padded_output[:, :3], direct, rtol=0, atol=1e-7
    )


def test_full_routed_actions_permute_with_unique_anonymous_content() -> None:
    torch.manual_seed(3_611_003)
    core = PrefixContextualResidualContinuousRosterPolicy(
        5,
        3,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    final = core.delayed_residual[-1]
    assert isinstance(final, torch.nn.Linear)
    with torch.no_grad():
        torch.nn.init.normal_(final.weight, std=0.1)
        torch.nn.init.normal_(final.bias, std=0.1)
    observations = torch.tensor(
        [
            [
                [0.1, 0.2, 0.3, -0.4, 0.2],
                [0.7, -0.2, 0.1, 0.5, -0.1],
                [-0.4, 0.8, -0.5, 0.1, 0.6],
            ]
        ]
    )
    hidden = torch.randn(1, 3, 8)
    active_mask = torch.ones(1, 3, dtype=torch.bool)
    critic_state = torch.randn(1, 3)
    direct = core.forward_step(
        observations=observations,
        active_mask=active_mask,
        critic_state=critic_state,
        hidden=hidden,
        deterministic=True,
    )
    permutation = torch.tensor([2, 0, 1])
    permuted = core.forward_step(
        observations=observations[:, permutation],
        active_mask=active_mask[:, permutation],
        critic_state=critic_state,
        hidden=hidden[:, permutation],
        deterministic=True,
    )
    for name in ("actions", "pre_tanh_actions", "next_hidden"):
        torch.testing.assert_close(
            getattr(permuted, name),
            getattr(direct, name)[:, permutation],
            rtol=0,
            atol=1e-7,
        )


def test_routed_residual_never_acts_on_inactive_rows() -> None:
    base, residual, arguments = _generic_pair()
    final = residual.policy.delayed_residual[-1]
    assert isinstance(final, torch.nn.Linear)
    with torch.no_grad():
        final.bias.fill_(0.25)
    output = residual.policy.forward_step(**arguments, deterministic=True)
    inactive = ~arguments["active_mask"].unsqueeze(-1).expand_as(output.actions)
    assert torch.count_nonzero(output.actions[inactive]) == 0
    assert torch.count_nonzero(output.pre_tanh_actions[inactive]) == 0


def test_constructive_dataset_closes_exact_source_rows() -> None:
    dataset = probe.constructive_dataset()
    controls = probe.dataset_contract(dataset)
    assert controls == {
        "row_count": 36,
        "row_count_exact": True,
        "slot_order_counts_exact": True,
        "time_coverage_exact": True,
        "finite": True,
        "inactive_targets_exact_zero": True,
    }
    assert dataset["observations"].shape == (
        36,
        source.CAPACITY,
        source.OBSERVATION_DIM,
    )
    assert dataset["actions"].shape == (36, source.CAPACITY, source.ACTION_DIM)
    assert source.run_information_gate()["branch"] == source.PASS_BRANCH


def test_fit_step_owns_only_residual_and_preserves_anchor() -> None:
    probe.runtime.configure_runtime(probe.MODEL_SEED)
    model = probe.make_model()
    model.begin_delayed_phase()
    dataset = probe.constructive_dataset()
    optimizer = probe.residual_optimizer(model)
    assert probe.optimizer_owns_only_residual(model, optimizer)
    anchor = probe.frozen_state(model)
    residual_before = tuple(
        parameter.detach().clone() for parameter in model.residual_parameters()
    )
    loss, actions = probe.pointwise_loss(model, dataset, torch.arange(36))
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.residual_parameters(), probe.GRADIENT_CLIP)
    optimizer.step()
    assert maximum_state_difference(anchor, probe.frozen_state(model)) == 0.0
    assert any(
        not torch.equal(before, after.detach())
        for before, after in zip(residual_before, model.residual_parameters())
    )
    inactive = torch.where(
        dataset["active_mask"].unsqueeze(-1), torch.zeros_like(actions), actions
    )
    assert torch.count_nonzero(inactive) == 0


def test_result_precedence_is_fail_closed() -> None:
    passing = {
        "operational_valid": True,
        "final_mse": 0.0009,
        "final_to_initial_ratio": 0.09,
        "final_utility": 0.96,
        "gain_over_anchor": 0.11,
        "spike_utility": 0.91,
        "rotating_effort_share": 0.76,
    }
    assert probe.select_result_branch(passing) == probe.PASS_BRANCH
    assert (
        probe.select_result_branch(passing | {"operational_valid": False})
        == probe.INVALID_BRANCH
    )
    assert (
        probe.select_result_branch(passing | {"final_mse": 0.0010001})
        == probe.NO_POINTWISE_BRANCH
    )
    assert (
        probe.select_result_branch(passing | {"final_to_initial_ratio": 0.100001})
        == probe.NO_POINTWISE_BRANCH
    )
    assert (
        probe.select_result_branch(passing | {"spike_utility": 0.899999})
        == probe.NO_CLOSED_LOOP_BRANCH
    )


def test_probe_contract_is_nonformal_and_reuses_registered_g18_gates() -> None:
    assert probe.FIT_STEPS == 200
    assert probe.FIT_BATCH_SIZE == 36
    assert probe.LEARNING_RATE == 1e-3
    assert probe.ABSOLUTE_MSE_CEILING == 1e-3
    assert probe.RELATIVE_MSE_CEILING == 0.10
    assert probe.g19.G18_UTILITY_FLOOR == 0.95
    assert probe.g19.G18_SPIKE_UTILITY_FLOOR == 0.90
    assert "constructive" not in probe.make_model().policy.__class__.__module__
