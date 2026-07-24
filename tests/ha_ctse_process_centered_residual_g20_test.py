from __future__ import annotations

import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    maximum_state_difference,
    optimize_fast_anchor_update,
    replay_errors,
    replay_trajectory,
)
from ha_ctse_process.centered_residual_g20 import (
    ActiveSetCenteredResidualPolicy,
    center_active_residuals,
    optimize_centered_delayed_update,
)
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from ha_ctse_process.separated_credit_g18 import collect_battery_trajectory
from scripts import screen_active_set_centered_residual_g20 as screen


def _battery_model() -> ActiveSetCenteredResidualPolicy:
    model = ActiveSetCenteredResidualPolicy(
        battery_source.OBSERVATION_DIM,
        battery_source.CRITIC_STATE_DIM,
        member_capacity=battery_source.CAPACITY,
        action_dim=battery_source.ACTION_DIM,
        hidden_dim=16,
    )
    with torch.no_grad():
        model.log_std.fill_(-1.0)
    return model


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


def test_centering_is_active_only_permutation_equivariant_and_padding_independent() -> None:
    proposals = torch.tensor(
        [
            [[1.0, 5.0], [3.0, 1.0], [8.0, 7.0], [2.0, 0.0]],
            [[4.0, 1.0], [6.0, 3.0], [2.0, 8.0], [9.0, 9.0]],
        ]
    )
    mask = torch.tensor(
        [[True, True, False, True], [False, True, True, False]]
    )
    centered = center_active_residuals(proposals, mask)
    torch.testing.assert_close(
        centered.sum(dim=1), torch.zeros(2, 2), rtol=0, atol=1e-7
    )
    assert torch.count_nonzero(centered[~mask]) == 0

    permutation = torch.tensor([2, 0, 3, 1])
    permuted = center_active_residuals(
        proposals[:, permutation], mask[:, permutation]
    )
    torch.testing.assert_close(
        permuted, centered[:, permutation], rtol=0, atol=0
    )

    padded_proposals = torch.cat((proposals, torch.randn(2, 3, 2)), dim=1)
    padded_mask = torch.cat(
        (mask, torch.zeros(2, 3, dtype=torch.bool)), dim=1
    )
    padded = center_active_residuals(padded_proposals, padded_mask)
    torch.testing.assert_close(padded[:, :4], centered, rtol=0, atol=0)
    assert torch.count_nonzero(padded[:, 4:]) == 0


def test_zero_centered_residual_exactly_matches_base_policy_in_all_modes() -> None:
    torch.manual_seed(2020000)
    base = ContinuousRosterPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    centered = ActiveSetCenteredResidualPolicy(
        5,
        4,
        member_capacity=3,
        action_dim=2,
        hidden_dim=8,
        current_observation_residual=True,
    )
    missing, unexpected = centered.policy.load_state_dict(
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
    noise = torch.randn(2, 3, 2)
    base_sample = base.forward_step(**arguments, sampling_noise=noise)
    centered_sample = centered.policy.forward_step(
        **arguments, sampling_noise=noise
    )
    _assert_step_equal(base_sample, centered_sample)
    _assert_step_equal(
        base.forward_step(**arguments, deterministic=True),
        centered.policy.forward_step(**arguments, deterministic=True),
    )
    _assert_step_equal(
        base.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
        centered.policy.forward_step(
            **arguments, teacher_pre_tanh=base_sample.pre_tanh_actions
        ),
    )
    assert centered.maximum_centering_error == 0.0


def test_battery_updates_keep_anchor_exact_and_center_residual() -> None:
    torch.manual_seed(2020001)
    model = _battery_model()
    fast = collect_battery_trajectory(
        model,
        episode_ids=(0, 1),
        action_seed=2030001,
        device=torch.device("cpu"),
    )
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters()
        + tuple(model.credit_baselines.parameters()),
        lr=1e-3,
    )
    assert optimize_fast_anchor_update(
        model,
        fast_optimizer,
        fast,
        device=torch.device("cpu"),
        ppo_passes=1,
    )["finite_update"] == 1.0
    anchor = model.anchor_state()
    model.begin_delayed_phase()
    delayed = collect_battery_trajectory(
        model,
        episode_ids=(2, 3),
        action_seed=2030002,
        device=torch.device("cpu"),
    )
    metrics = optimize_centered_delayed_update(
        model,
        torch.optim.SGD(model.residual_parameters(), lr=1e-3),
        torch.optim.Adam(model.critic_parameters(), lr=1e-3),
        delayed,
        device=torch.device("cpu"),
        ppo_passes=2,
        gamma=0.99,
    )
    assert metrics["finite_update"] == 1.0
    assert metrics["maximum_centering_error"] <= 1e-6
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0
    assert model.residual_output_layer_maximum_absolute_value() > 0.0
    assert all(
        value == 0.0
        for name, value in metrics.items()
        if (name.endswith("_error") or name.endswith("_max_abs"))
        and name != "maximum_centering_error"
    )


def test_g17_fast_and_centered_updates_replay_and_preserve_anchor() -> None:
    torch.manual_seed(2020002)
    model = ActiveSetCenteredResidualPolicy(
        g17_source.OBSERVATION_DIM,
        g17_source.CRITIC_STATE_DIM,
        member_capacity=g17_source.CAPACITY,
        action_dim=g17_source.ACTION_DIM,
        hidden_dim=16,
    )
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=2029002,
        action_seed=2039002,
        device=torch.device("cpu"),
    )
    fast = attach_credit_baselines(model, raw, device=torch.device("cpu"))
    assert all(
        value == 0.0
        for value in replay_errors(
            replay_trajectory(model, fast, device=torch.device("cpu")), fast
        ).values()
    )
    assert optimize_fast_anchor_update(
        model,
        torch.optim.Adam(
            model.fast_actor_parameters()
            + tuple(model.credit_baselines.parameters()),
            lr=1e-3,
        ),
        fast,
        device=torch.device("cpu"),
        ppo_passes=1,
    )["finite_update"] == 1.0
    anchor = model.anchor_state()
    model.begin_delayed_phase()
    raw = g17_source.collect_trajectory(
        model,
        episode_ids=(2, 3),
        ledger_seed=2029002,
        action_seed=2039002,
        device=torch.device("cpu"),
    )
    delayed = attach_credit_baselines(model, raw, device=torch.device("cpu"))
    metrics = optimize_centered_delayed_update(
        model,
        torch.optim.SGD(model.residual_parameters(), lr=1e-3),
        torch.optim.Adam(model.critic_parameters(), lr=1e-3),
        delayed,
        device=torch.device("cpu"),
        ppo_passes=1,
        gamma=0.99,
    )
    assert metrics["finite_update"] == 1.0
    assert metrics["maximum_centering_error"] <= 1e-6
    assert maximum_state_difference(anchor, model.anchor_state()) == 0.0


def test_g20_result_precedence_is_first_match() -> None:
    passing = {
        "operational_valid": True,
        "g17_final_iid_utility": 0.93,
        "g17_final_heldout_utility": 0.92,
        "g17_gain": 0.20,
        "g17_minimum_episode": 0.85,
        "g17_effort_correlation": 0.95,
        "g17_mix_correlation": 0.96,
        "g17_effort_mae": 0.03,
        "g17_mix_mae": 0.02,
        "g18_final_utility": 0.97,
        "g18_gain_over_anchor": 0.15,
        "g18_spike_utility": 0.94,
        "g18_rotating_effort_share": 0.82,
    }
    assert screen.select_result_branch(passing) == screen.PROMISING_BRANCH
    assert screen.select_result_branch(
        passing
        | {
            "g17_mix_correlation": 0.89,
            "g18_final_utility": 0.1,
        }
    ) == screen.NO_G17_BRANCH
    assert screen.select_result_branch(
        passing | {"g18_gain_over_anchor": 0.09}
    ) == screen.NO_G18_ACCESS_BRANCH
    assert screen.select_result_branch(
        passing | {"g18_rotating_effort_share": 0.74}
    ) == screen.NO_G18_MECHANISM_BRANCH
    assert screen.select_result_branch(
        passing | {"operational_valid": False}
    ) == screen.INVALID_BRANCH


def test_g20_screen_configuration_is_frozen() -> None:
    configuration = screen._configuration()
    assert configuration["g17_fast_updates"] == 100
    assert configuration["g17_delayed_updates"] == 100
    assert configuration["g18_fast_updates"] == 100
    assert configuration["g18_delayed_updates"] == 300
    assert configuration["delayed_residual_optimizer"] == "sgd"
    assert (
        configuration["delayed_residual_geometry"]
        == "active_set_centered_pre_squash_mean"
    )
