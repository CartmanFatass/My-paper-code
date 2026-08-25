from __future__ import annotations

import numpy as np
import pytest
import torch

from ha_ctse_process import runtime_capacity_continuous_roster_g32 as source
from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process.anchored_residual_g19 import (
    attach_credit_baselines,
    replay_errors,
    replay_trajectory,
)
from scripts import run_runtime_capacity_continuous_roster_g32 as runner


def test_model_state_shapes_are_capacity_independent_and_strict_loadable() -> None:
    torch.manual_seed(32001)
    cap8 = runner.make_model(8)
    state = cap8.state_dict()
    shapes = {name: tuple(row.shape) for name, row in state.items()}
    assert not any(8 in shape and name.endswith("critic.0.weight") for name, shape in shapes.items())
    for capacity in (6, 8, 12):
        model = runner.make_model(capacity)
        assert {name: tuple(row.shape) for name, row in model.state_dict().items()} == shapes
        incompatible = model.load_state_dict(state, strict=True)
        assert incompatible.missing_keys == []
        assert incompatible.unexpected_keys == []
        assert "member_capacity" not in model.state_dict()


def test_padding_pair_source_and_policy_outputs_are_exact() -> None:
    ledger8 = roster_env.make_ledger(7, master_seed=32101, profile=roster_env.PADDING_CAPACITY_8)
    ledger12 = roster_env.make_ledger(7, master_seed=32101, profile=roster_env.PADDING_CAPACITY_12)
    np.testing.assert_array_equal(ledger8.capabilities, ledger12.capabilities[:8])
    np.testing.assert_array_equal(ledger8.presentation_priority, ledger12.presentation_priority[:, :8])
    assert ledger8.temporarily_absent == ledger12.temporarily_absent
    assert ledger8.terminal_leave == ledger12.terminal_leave
    torch.manual_seed(32201)
    state = runner.make_model(8).state_dict()
    diagnostic = runner._padding_diagnostic(
        state,
        seeds={
            "model": 32201,
            "evaluation_ledger": 32101,
            "evaluation_action": 32301,
        },
    )
    assert diagnostic["lifecycle_equal"] is True
    assert diagnostic["inactive_padding_zero"] is True
    assert all(
        diagnostic[f"maximum_{name}_mismatch"] == 0.0
        for name in ("observation", "value", "action", "reward", "hidden")
    )


@pytest.mark.parametrize(
    "profile",
    (
        roster_env.PADDING_CAPACITY_8,
        roster_env.PADDING_CAPACITY_12,
        roster_env.SMALL_CAPACITY_6,
        roster_env.LARGE_CAPACITY_12,
    ),
)
def test_registered_profiles_have_exact_constructive_access(profile) -> None:
    environment = roster_env.RuntimeCapacityRosterEnv(
        roster_env.make_ledger(3, master_seed=32401, profile=profile)
    )
    for _ in range(roster_env.HORIZON):
        view = environment.observe()
        reward, _terminal, _info = environment.step(roster_env.constructive_actions(view))
        assert reward >= 1.0 - 2e-7
    outcome = environment.outcome()
    assert outcome.roster_sizes == tuple(
        count
        for count in profile.segment_counts
        for _ in range(roster_env.HORIZON // 4)
    )


def test_replay_and_lifecycle_hidden_ownership_are_exact() -> None:
    torch.manual_seed(32501)
    model = runner.make_model(8)
    raw = source.collect_trajectory(
        model,
        episode_ids=(0, 1),
        ledger_seed=32601,
        action_seed=32701,
        device=torch.device("cpu"),
    )
    trajectory = attach_credit_baselines(model, raw, device=torch.device("cpu"))
    replay = replay_trajectory(model, trajectory, device=torch.device("cpu"))
    assert max(replay_errors(replay, trajectory).values()) == 0.0
    assert torch.count_nonzero(raw.actions[~raw.active_mask]) == 0
    assert torch.count_nonzero(raw.old_log_probs[~raw.active_mask]) == 0
    assert torch.count_nonzero(raw.hidden_before[raw.terminal_hidden_reset_mask]) == 0
    for env_index, ledger in enumerate(raw.ledgers):
        for key in ledger.temporarily_absent:
            torch.testing.assert_close(
                raw.hidden_after[roster_env.EVENT_TIMES[0] - 1, env_index, key],
                raw.hidden_after[roster_env.EVENT_TIMES[1] - 1, env_index, key],
                rtol=0,
                atol=0,
            )
        for key in ledger.fresh_join:
            assert torch.count_nonzero(
                raw.hidden_before[roster_env.EVENT_TIMES[1], env_index, key]
            ) == 0


def test_empty_and_capacity_overflow_profiles_fail_closed() -> None:
    with pytest.raises(ValueError, match="positive"):
        roster_env.RosterProfile("empty", 6, 0, 1, 1, 1).validate()
    with pytest.raises(ValueError, match="exceeds runtime"):
        roster_env.RosterProfile("overflow", 6, 5, 1, 2, 1).validate()
