from __future__ import annotations

import copy
from collections import Counter

import torch

from ha_ctse_process import continuous_roster_native_six_coordinate_training_g39 as g39
from ha_ctse_process.anchored_residual_g19 import attach_credit_baselines


def _paired() -> dict[str, g39.G39Policy]:
    return g39.make_paired_models(8, initialization_seed=10_391_000)


def test_true_shapes_parameter_delta_derivation_and_independent_empty_adam() -> None:
    models = _paired()
    const = models[g39.CONST10_ARM]
    native = models[g39.NATIVE6_ARM]
    inventory = g39.raw_input_inventory(models)
    assert inventory == {
        "const_member_input_shape": (32, 10),
        "const_current_readout_shape": (2, 10),
        "native_member_input_shape": (32, 6),
        "native_current_readout_shape": (2, 6),
        "parameter_delta": 136,
        "const_raw_width": 10,
        "native_raw_width": 6,
        "native_has_constant_columns": False,
        "native_has_fold_path": False,
    }
    g39.verify_derived_initialization(const, native)
    g39.assert_no_shared_state(const, native)
    const_state, native_state = const.state_dict(), native.state_dict()
    for name in const_state:
        if name not in g39._raw_state_names():
            assert torch.equal(const_state[name], native_state[name]), name

    const_optimizer = torch.optim.Adam(const.parameters(), lr=1e-3)
    native_optimizer = torch.optim.Adam(native.parameters(), lr=1e-3)
    assert const_optimizer is not native_optimizer
    assert const_optimizer.state == {}
    assert native_optimizer.state == {}
    assert const_optimizer.state is not native_optimizer.state


def test_first_forward_and_first_paired_8x48_trajectory_match() -> None:
    models = _paired()
    trajectories = {
        arm: g39.collect_g39_trajectory(
            model,
            episode_ids=range(8),
            ledger_seed=10_397_000,
            action_seed=10_397_000,
            device=torch.device("cpu"),
        )
        for arm, model in models.items()
    }
    const = trajectories[g39.CONST10_ARM]
    native = trajectories[g39.NATIVE6_ARM]
    assert const.observations.shape == (48, 8, 8, 6)
    assert native.observations.shape == (48, 8, 8, 6)
    match = g39.initial_trajectory_match(const, native)
    assert match["passed"] is True, match
    noise = torch.as_tensor(
        g39.g32.make_action_noise(
            range(8), action_seed=10_397_000, member_capacity=8
        )[0]
    )
    forward = g39.initial_forward_match(
        models[g39.CONST10_ARM],
        models[g39.NATIVE6_ARM],
        observations=const.observations[0],
        active_mask=const.active_mask[0],
        critic_state=const.critic_states[0],
        sampling_noise=noise,
    )
    assert forward["passed"] is True, forward


def test_fast_and_return_to_go_analytic_gradient_identities_and_live_columns() -> None:
    models = _paired()
    raw = {
        arm: g39.collect_g39_trajectory(
            model,
            episode_ids=range(8),
            ledger_seed=10_397_000,
            action_seed=10_397_000,
            device=torch.device("cpu"),
        )
        for arm, model in models.items()
    }
    trajectories = {
        arm: attach_credit_baselines(model, raw[arm], device=torch.device("cpu"))
        for arm, model in models.items()
    }
    audit = g39.initial_gradient_audit(
        models[g39.CONST10_ARM],
        models[g39.NATIVE6_ARM],
        trajectories[g39.CONST10_ARM],
        trajectories[g39.NATIVE6_ARM],
        gamma=0.99,
    )
    assert audit["passed"] is True, audit
    for name, row in audit.items():
        if name in (
            "passed",
            "scalar_liveness",
            "registered_trainable_groups",
        ):
            continue
        assert row["finite"] is True
        assert max(row["errors"].values()) <= 1e-6
    liveness = audit["scalar_liveness"]
    assert liveness["removable_scalar_total"] == 136
    assert liveness["removable_scalar_live_count"] == 136
    assert liveness["dead_removable_scalars"] == []
    assert liveness["all_136_removable_scalars_live"] is True
    assert liveness["native_effective_bias_live_count"] == 34
    assert liveness["dead_native_effective_biases"] == []
    assert liveness["all_native_effective_biases_live"] is True
    assert all(liveness["native_gradient_norm_live"].values())
    registered = audit["registered_trainable_groups"]
    assert set(registered) == set(g39.ARMS)
    for arm in g39.ARMS:
        assert set(registered[arm]) == {*g39.REGISTERED_TRAINABLE_GROUPS, "passed"}
        assert registered[arm]["passed"] is True
        for group in g39.REGISTERED_TRAINABLE_GROUPS:
            row = registered[arm][group]
            assert row["finite"] is True
            assert row["live"] is True
            assert max(
                row["fast_objective_gradient_norm"],
                row["return_to_go_objective_gradient_norm"],
            ) > 1e-12
    assert g39.validate_initial_gradient_audit_record(audit) is True

    dead_common = copy.deepcopy(audit)
    dead_group = dead_common["registered_trainable_groups"][g39.CONST10_ARM][
        "centralized_slow_critic"
    ]
    dead_group["fast_objective_gradient_norm"] = 0.0
    dead_group["return_to_go_objective_gradient_norm"] = 0.0
    dead_group["live"] = False
    assert dead_common["scalar_liveness"]["all_136_removable_scalars_live"] is True
    assert g39.validate_initial_gradient_audit_record(dead_common) is False


def test_all_136_liveness_rejects_one_dead_scalar_despite_live_column() -> None:
    removable = {
        "member_input": [torch.ones((32, 4)), torch.ones((32, 4))],
        "current_readout": [torch.ones((2, 4)), torch.ones((2, 4))],
    }
    native_biases = {
        "member_input": [torch.ones(32), torch.ones(32)],
        "current_readout": [torch.ones(2), torch.ones(2)],
    }
    passed = g39._combined_gradient_liveness(removable, native_biases)
    assert passed["all_136_removable_scalars_live"] is True
    removable["member_input"][0][0, 0] = 0.0
    removable["member_input"][1][0, 0] = 0.0
    rejected = g39._combined_gradient_liveness(removable, native_biases)
    assert rejected["removable_scalar_live_count"] == 135
    assert rejected["dead_removable_scalars"] == ["member_input[0,6]"]
    assert rejected["all_136_removable_scalars_live"] is False
    assert bool((removable["member_input"][0][:, 0].abs() > 1e-12).any())


def test_registered_seed_law_and_process_pairing() -> None:
    assert g39.seed_block(2, formal=True) == {
        "model": 10_391_002,
        "training_ledger": 10_392_002,
        "training_action": 10_393_002,
        "evaluation_base_ledger": 10_394_002,
        "evaluation_process": 10_395_002,
        "evaluation_action": 10_396_002,
        "initial_gradient_probe": 10_397_002,
    }
    formal = g39.seed_block(0, formal=True)
    nonformal = g39.seed_block(0, formal=False)
    assert all(nonformal[name] - formal[name] == 900_000 for name in formal)
    assert g39.bootstrap_seed(formal=True) == 10_398_039
    assert g39.bootstrap_seed(formal=False) == 11_298_039
    rows = g39.make_process_ledgers(
        replicate=0, capacity=8, episode_count=64, formal=True
    )
    assert len(rows) == 64
    assert len({row.signature for row in rows}) == 64
    assert len({row.event_times for row in rows}) == 64
    assert Counter(row.event_order for row in rows) == {
        ("L", "R", "J", "T"): 22,
        ("L", "J", "R", "T"): 21,
        ("J", "L", "R", "T"): 21,
    }
    assert all(sorted(row.event_order) == ["J", "L", "R", "T"] for row in rows)
    for replicate, extra in enumerate(g39.g34.EVENT_ORDERS):
        assigned = g39._balanced_64_assignments(
            g39.g34.EVENT_ORDERS,
            replicate=replicate,
            capacity=8,
            process_seed=10_395_000 + replicate,
            stream=1,
        )
        counts = Counter(assigned)
        assert counts[extra] == 22
        assert sorted(counts.values()) == [21, 21, 22]
