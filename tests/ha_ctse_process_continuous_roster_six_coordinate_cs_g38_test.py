from __future__ import annotations

from dataclasses import fields
import numpy as np
import pytest
import torch

from ha_ctse_process import continuous_roster_six_coordinate_cs_g38 as g38
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from ha_ctse_process.anchored_residual_g19 import attach_credit_baselines


def _paired() -> dict[str, g38.G38FoldableMatchedCSPolicy]:
    return g38.make_paired_models(8, initialization_seed=10_381_000)


def _install_fold_stress_weights(model: g38.G38FoldableMatchedCSPolicy) -> None:
    constants = torch.tensor(g38.CONSTANT_COORDINATES)
    pattern = torch.tensor((1.0, -1.0, 1.0, -1.0)) * 1_000_000.0
    with torch.no_grad():
        for affine in (model.member_input, model.current_readout):
            retained = torch.linspace(
                -0.25,
                0.25,
                affine.out_features * g38.RETAINED_OBSERVATION_DIM,
            ).reshape(affine.out_features, g38.RETAINED_OBSERVATION_DIM)
            signs = torch.where(
                torch.arange(affine.out_features) % 2 == 0, 1.0, -1.0
            ).unsqueeze(-1)
            affine.weight[:, : g38.RETAINED_OBSERVATION_DIM].copy_(retained)
            affine.weight[:, g38.RETAINED_OBSERVATION_DIM :].copy_(signs * pattern)
            affine.bias.copy_(
                -_test_last_four_linear(
                    constants,
                    affine.weight[:, g38.RETAINED_OBSERVATION_DIM :],
                )
            )


def _test_last_four_linear(
    coordinates: torch.Tensor, weight: torch.Tensor
) -> torch.Tensor:
    products = coordinates.unsqueeze(-2) * weight
    return (products[..., 0] + products[..., 1]) + (
        products[..., 2] + products[..., 3]
    )


def test_constant_constructor_reads_six_coordinates_and_zeros_inactive_rows() -> None:
    retained = torch.arange(3 * 4 * 6, dtype=torch.float32).reshape(3, 4, 6)
    active = torch.tensor(
        [[True, False, True, False], [False, True, True, False], [True, True, False, False]]
    )
    actual = g38.build_g38_constant_actor_input(retained, active)
    assert actual.shape == (3, 4, 10)
    torch.testing.assert_close(actual[..., :6][active], retained[active])
    torch.testing.assert_close(
        actual[..., 6:][active],
        torch.tensor(g38.CONSTANT_COORDINATES).expand(int(active.sum()), 4),
        rtol=0,
        atol=0,
    )
    assert torch.count_nonzero(actual[~active]) == 0
    assert g38.source_controls()["fold6_actual_history_read_counts"] == {
        "actual_age_read_count": 0,
        "actual_previous_action_read_count": 0,
        "actual_actor_time_read_count": 0,
        "donor_or_proxy_read_count": 0,
    }


def test_common_graph_state_initialization_and_zero_carry_are_exact() -> None:
    models = _paired()
    full, fold = models[g38.FULL10_ARM], models[g38.FOLD6_ARM]
    g38.assert_parameter_match(full, fold, require_byte_identity=True)
    inventory = g38.raw_input_inventory(full)
    assert inventory == {
        "member_input_shape": (32, 10),
        "current_readout_shape": (2, 10),
        "raw_affine_module_paths": (
            "member_encoder.0",
            "current_observation_residual",
        ),
        "only_two_raw_affines": True,
        "carry_mode": "CS",
    }
    assert full.input_mode == g38.FULL10_INPUT
    assert fold.input_mode == g38.FOLD6_INPUT
    assert "input_mode" not in full.state_dict()
    assert "actual_history_read_counts" not in full.state_dict()
    assert isinstance(full.policy.delayed_residual, torch.nn.Sequential)
    assert full.policy.delayed_residual[0].in_features == 34
    assert tuple(full.state_dict()) == tuple(fold.state_dict())

    ledgers = tuple(
        g32.make_ledger(
            episode,
            master_seed=10_387_000,
            profile=g32.TRAIN_PROFILES[episode % len(g32.TRAIN_PROFILES)],
        )
        for episode in range(2)
    )
    views = tuple(g32.RuntimeCapacityRosterEnv(row).observe() for row in ledgers)
    retained = torch.as_tensor(np.stack([row.observations[:, :6] for row in views]))
    active = torch.as_tensor(np.stack([row.active_mask for row in views]))
    critic = torch.as_tensor(np.stack([row.critic_state for row in views]))
    noise = torch.as_tensor(
        g32.make_action_noise(range(2), action_seed=10_387_000, member_capacity=8)[0]
    )
    clamped = g38.build_g38_constant_actor_input(retained, active)
    for full_affine, fold_affine in (
        (full.member_input, fold.member_input),
        (full.current_readout, fold.current_readout),
    ):
        assert torch.equal(full_affine(clamped), fold_affine(clamped))
    errors = g38.forced_initial_equality(
        full,
        fold,
        retained_observations=retained,
        active_mask=active,
        critic_state=critic,
        sampling_noise=noise,
    )
    assert max(errors.values()) <= g38.INITIAL_EQUALITY_TOLERANCE


def test_fold6_model_rejects_ten_and_collection_replay_stays_six_wide(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _paired()[g38.FOLD6_ARM]
    active = torch.ones((1, 8), dtype=torch.bool)
    with pytest.raises(ValueError, match="observation width mismatch"):
        model.forward_step(
            observations=torch.zeros((1, 8, 10)),
            active_mask=active,
            critic_state=torch.zeros((1, 6)),
            hidden=torch.zeros((1, 8, g38.HIDDEN_DIM)),
            deterministic=True,
        )
    raw = g38.collect_g38_trajectory(
        model,
        episode_ids=range(2),
        ledger_seed=10_387_000,
        action_seed=10_387_000,
        device=torch.device("cpu"),
    )
    assert raw.observations.shape == (48, 2, 8, 6)
    anchored = attach_credit_baselines(model, raw, device=torch.device("cpu"))
    assert anchored.observations.shape[-1] == 6
    widths: list[int] = []
    original = model.forward_step

    def record_width(**kwargs: object) -> object:
        observations = kwargs["observations"]
        assert isinstance(observations, torch.Tensor)
        widths.append(int(observations.shape[-1]))
        return original(**kwargs)

    monkeypatch.setattr(model, "forward_step", record_width)
    g38.g35.replay_trajectory(model, anchored, device=torch.device("cpu"))
    assert widths == [6] * g38.g32.HORIZON


def test_g38_collector_preserves_the_exact_full10_g32_trajectory() -> None:
    left = _paired()[g38.FULL10_ARM]
    right = _paired()[g38.FULL10_ARM]
    expected = g32.collect_trajectory(
        left,
        episode_ids=range(2),
        ledger_seed=10_387_000,
        action_seed=10_387_000,
        device=torch.device("cpu"),
    )
    actual = g38.collect_g38_trajectory(
        right,
        episode_ids=range(2),
        ledger_seed=10_387_000,
        action_seed=10_387_000,
        device=torch.device("cpu"),
    )
    for field in (
        "observations",
        "active_mask",
        "critic_states",
        "actions",
        "pre_tanh_actions",
        "old_log_probs",
        "old_values",
        "rewards",
        "hidden_before",
        "hidden_after",
        "prefix_action_sums",
        "terminal_hidden_reset_mask",
    ):
        assert torch.equal(getattr(actual, field), getattr(expected, field)), field
    assert actual.outcomes == expected.outcomes
    for actual_ledger, expected_ledger in zip(actual.ledgers, expected.ledgers):
        for field in fields(actual_ledger):
            left_value = getattr(actual_ledger, field.name)
            right_value = getattr(expected_ledger, field.name)
            if isinstance(left_value, np.ndarray):
                np.testing.assert_array_equal(left_value, right_value)
            else:
                assert left_value == right_value


def test_exact_two_bias_fold_removes_136_weights_and_copies_every_other_tensor() -> None:
    model = _paired()[g38.FOLD6_ARM]
    with torch.no_grad():
        model.member_input.weight.copy_(
            torch.arange(model.member_input.weight.numel(), dtype=torch.float32).reshape_as(
                model.member_input.weight
            )
            / 1000
        )
        model.member_input.bias.copy_(torch.linspace(-0.2, 0.2, 32))
        model.current_readout.weight.copy_(
            torch.arange(model.current_readout.weight.numel(), dtype=torch.float32).reshape_as(
                model.current_readout.weight
            )
            / 100
        )
        model.current_readout.bias.copy_(torch.tensor([-0.3, 0.4]))
    member_weight = model.member_input.weight.detach().clone()
    member_bias = model.member_input.bias.detach().clone()
    readout_weight = model.current_readout.weight.detach().clone()
    readout_bias = model.current_readout.bias.detach().clone()
    constants = torch.tensor(g38.CONSTANT_COORDINATES)
    before = {name: row.detach().clone() for name, row in model.state_dict().items()}
    folded = g38.fold_g38_constant_actor_checkpoint(model)
    assert model.parameter_count - folded.parameter_count == 136
    torch.testing.assert_close(folded.member_input.weight, member_weight[:, :6], rtol=0, atol=0)
    torch.testing.assert_close(
        folded.member_input.bias,
        member_bias + _test_last_four_linear(constants, member_weight[:, 6:]),
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(folded.current_readout.weight, readout_weight[:, :6], rtol=0, atol=0)
    torch.testing.assert_close(
        folded.current_readout.bias,
        readout_bias + _test_last_four_linear(constants, readout_weight[:, 6:]),
        rtol=0,
        atol=0,
    )
    changed = {
        "policy.member_encoder.0.weight",
        "policy.member_encoder.0.bias",
        "policy.current_observation_residual.weight",
        "policy.current_observation_residual.bias",
    }
    assert all(
        torch.equal(before[name], folded.state_dict()[name])
        for name in before
        if name not in changed
    )


def test_fold6_and_folded_share_six_wide_effective_bias_kernel_under_stress() -> None:
    full = g38.make_model(
        12, input_mode=g38.FULL10_INPUT, initialization_seed=10_381_000
    )
    pre = g38.make_model(
        12, input_mode=g38.FOLD6_INPUT, initialization_seed=10_381_000
    )
    _install_fold_stress_weights(pre)
    folded = g38.fold_g38_constant_actor_checkpoint(pre)
    retained = torch.linspace(-0.75, 0.75, 3 * 12 * 6).reshape(3, 12, 6)
    active = torch.ones((3, 12), dtype=torch.bool)
    constructed = g38.build_g38_constant_actor_input(retained, active)
    constants = torch.tensor(g38.CONSTANT_COORDINATES)

    for pre_affine, folded_affine in (
        (pre.member_input, folded.member_input),
        (pre.current_readout, folded.current_readout),
    ):
        effective_bias = (
            pre_affine.bias
            + _test_last_four_linear(
                constants,
                pre_affine.weight[:, g38.RETAINED_OBSERVATION_DIM :],
            )
        )
        expected = torch.nn.functional.linear(
            retained,
            pre_affine.weight[:, : g38.RETAINED_OBSERVATION_DIM],
            None,
        ) + effective_bias
        actual = pre_affine(constructed)
        legacy_ten_wide = torch.nn.functional.linear(
            constructed, pre_affine.weight, pre_affine.bias
        )
        assert torch.equal(actual, expected)
        assert torch.equal(folded_affine(retained), expected)
        assert float((legacy_ten_wide - expected).abs().max()) > 1e-6

    full_input = torch.linspace(-1.0, 1.0, 3 * 12 * 10).reshape(3, 12, 10)
    for affine in (full.member_input, full.current_readout):
        retained_term = torch.nn.functional.linear(
            full_input[..., : g38.RETAINED_OBSERVATION_DIM],
            affine.weight[:, : g38.RETAINED_OBSERVATION_DIM],
            None,
        )
        expected = retained_term + (
            affine.bias
            + _test_last_four_linear(
                full_input[..., g38.RETAINED_OBSERVATION_DIM :],
                affine.weight[:, g38.RETAINED_OBSERVATION_DIM :],
            )
        )
        assert torch.equal(affine(full_input), expected)

    processes = g38.make_process_ledgers(
        replicate=0, capacity=12, episode_count=8, formal=True
    )
    _, lifecycle, audit = g38.verify_g38_fold_equivalence(
        pre,
        folded,
        processes=processes,
        action_seed=10_386_000,
        process_kind="random",
        deterministic=False,
    )
    assert lifecycle is True
    assert audit["passed"] is True
    assert audit["environment_trajectories_per_episode"] == 1
    assert audit["membership_edit_checks"] == 8 * g38.g32.HORIZON
    assert all(error == 0.0 for error in audit["maximum_errors"].values())


def test_removable_columns_have_live_actual_objective_gradients() -> None:
    for arm, model in _paired().items():
        raw = g38.collect_g38_trajectory(
            model,
            episode_ids=range(8),
            ledger_seed=10_387_000,
            action_seed=10_387_000,
            device=torch.device("cpu"),
        )
        trajectory = attach_credit_baselines(model, raw, device=torch.device("cpu"))
        audit = g38.g38_initial_gradient_audit(model, trajectory, gamma=0.99)
        assert audit["passed"] is True, arm
        for affine in ("member_input", "current_readout"):
            for column in g38.REMOVABLE_COLUMNS:
                row = audit[f"{affine}_column_{column}"]
                assert row["finite"] is True
                assert row["live"] is True
                assert max(
                    row["fast_objective_gradient_max_abs"],
                    row["return_to_go_objective_gradient_max_abs"],
                ) > g38.GRADIENT_LIVE_TOLERANCE


def test_folded_actor_is_lockstep_equivalent_on_one_environment_trajectory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pre = _paired()[g38.FOLD6_ARM]
    folded = g38.fold_g38_constant_actor_checkpoint(pre)
    processes = g38.make_process_ledgers(
        replicate=0, capacity=8, episode_count=2, formal=True
    )
    for deterministic in (True, False):
        episodes, lifecycle, audit = g38.verify_g38_fold_equivalence(
            pre,
            folded,
            processes=processes,
            action_seed=10_386_000,
            process_kind="random",
            deterministic=deterministic,
        )
        assert len(episodes) == 2
        assert lifecycle is True
        assert audit["passed"] is True
        assert audit["environment_trajectories_per_episode"] == 1
        assert audit["reward_comparisons"] == 2 * g38.g32.HORIZON
        assert audit["membership_edit_checks"] == 2 * g38.g32.HORIZON
        assert audit["summary_comparisons"] == 20
        assert audit["maximum_errors"]["pre_tanh_mean"] <= 1e-6
        assert audit["maximum_errors"]["actions"] <= 1e-6
        assert audit["maximum_errors"]["prefix_action_sums"] <= 1e-6
        assert audit["maximum_errors"]["token_log_probability"] <= 1e-5
        assert all(audit["exact"].values())

    original = g38._expected_membership_change

    def wrong_membership(
        process: object, *, process_kind: str, time: int
    ) -> g38.g32.MembershipChange:
        del process, process_kind, time
        return g38.g32.MembershipChange(joined=(999,))

    monkeypatch.setattr(g38, "_expected_membership_change", wrong_membership)
    _, _, failed = g38.verify_g38_fold_equivalence(
        pre,
        folded,
        processes=processes[:1],
        action_seed=10_386_000,
        process_kind="random",
        deterministic=True,
    )
    assert failed["membership_edit_checks"] == g38.g32.HORIZON
    assert failed["exact"]["membership_edits"] is False
    assert failed["passed"] is False
    monkeypatch.setattr(g38, "_expected_membership_change", original)

    reward_function = g38.g38_immediate_reward
    reward_call = 0

    def biased_pre_fold_reward(
        env: object, view: object, actions: np.ndarray
    ) -> float:
        nonlocal reward_call
        value = reward_function(env, view, actions)  # type: ignore[arg-type]
        phase = reward_call % 3
        reward_call += 1
        return value + (2e-4 if phase == 0 else 0.0)

    monkeypatch.setattr(g38, "g38_immediate_reward", biased_pre_fold_reward)
    _, _, reward_failed = g38.verify_g38_fold_equivalence(
        pre,
        folded,
        processes=processes[:1],
        action_seed=10_386_000,
        process_kind="random",
        deterministic=True,
    )
    assert reward_failed["maximum_errors"]["reward_trace"] >= 1e-4
    assert reward_failed["maximum_errors"]["summary"] >= 1e-4
    assert reward_failed["passed"] is False


def test_seeded_g32_g34_exposure_is_fresh_paired_and_bounded() -> None:
    formal = g38.make_process_ledgers(
        replicate=2, capacity=12, episode_count=8, formal=True
    )
    nonformal = g38.make_process_ledgers(
        replicate=2, capacity=12, episode_count=8, formal=False
    )
    assert len({row.signature for row in formal}) == 8
    assert [row.signature for row in formal] != [row.signature for row in nonformal]
    formal_seeds = g38.seed_block(2, formal=True)
    nonformal_seeds = g38.seed_block(2, formal=False)
    assert formal_seeds == {
        "model": 10_381_002,
        "training_ledger": 10_382_002,
        "training_action": 10_383_002,
        "evaluation_base_ledger": 10_384_002,
        "evaluation_process": 10_385_002,
        "evaluation_action": 10_386_002,
        "initial_gradient_probe": 10_387_002,
    }
    assert all(
        nonformal_seeds[name] - formal_seeds[name] == g38.NONFORMAL_SEED_OFFSET
        for name in formal_seeds
    )
    assert g38.bootstrap_seed(formal=True) == 10_388_038
    assert g38.bootstrap_seed(formal=False) == 11_288_038
