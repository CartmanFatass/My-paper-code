from __future__ import annotations

import numpy as np
import pytest

from ha_ctse_process.delayed_battery_roster_g18 import (
    CAPACITY,
    HORIZON,
    PASS_BRANCH,
    BatteryRosterEnv,
    constructive_actions,
    counterfactual_first_action,
    make_ledger,
    myopic_equal_actions,
    run_controller,
    run_information_gate,
)


def test_information_gate_separates_delayed_service_from_myopic_control() -> None:
    result = run_information_gate()

    assert result["branch"] == PASS_BRANCH
    assert result["constructive_minimum_utility"] == 1.0
    assert result["myopic_maximum_utility"] < 0.90
    assert result["minimum_constructive_minus_myopic"] > 0.10
    assert result["slot_permutation_invariant"] is True
    assert result["roster_sizes"] == [4] * 6 + [2] * 4 + [4] * 2


def test_sequence_intervention_is_immediately_equal_but_future_bearing() -> None:
    ledger = make_ledger((0, 1, 2, 3, 4, 5))
    natural = BatteryRosterEnv(ledger)
    intervened = BatteryRosterEnv(ledger)

    natural_view = natural.observe()
    intervention_view = intervened.observe()
    natural_reward, _, natural_info = natural.step(
        constructive_actions(natural_view)
    )
    intervention_reward, _, intervention_info = intervened.step(
        counterfactual_first_action(intervention_view)
    )

    assert natural_reward == intervention_reward == 1.0
    assert natural_info["served"] == intervention_info["served"]
    persistent_key = ledger.persistent_keys[0]
    rotating_key = ledger.rotating_keys[0]
    assert natural.battery[persistent_key] > intervened.battery[persistent_key]
    assert natural.battery[rotating_key] < intervened.battery[rotating_key]

    while natural.time < HORIZON:
        natural.step(constructive_actions(natural.observe()))
        intervened.step(constructive_actions(intervened.observe()))

    assert natural.outcome().utility == 1.0
    assert intervened.outcome().utility < natural.outcome().utility
    assert intervened.outcome().future_service_deficit > 0.0


def test_lifecycle_state_is_owned_and_inactive_actions_fail_closed() -> None:
    ledger = make_ledger((3, 5, 0, 4, 1, 2))
    env = BatteryRosterEnv(ledger)
    roster_sizes = []
    for _ in range(HORIZON):
        view = env.observe()
        roster_sizes.append(int(view.active_mask.sum()))
        assert np.count_nonzero(constructive_actions(view)[~view.active_mask]) == 0
        if view.time == 10:
            assert view.membership_change.rejoined == ledger.rotating_keys
            assert view.membership_change.joined == (ledger.fresh_key,)
            assert view.membership_change.terminally_left == (
                ledger.terminal_leave_key,
            )
            assert env.battery[ledger.fresh_key] == 1.0
            assert env.previous_effort[ledger.fresh_key] == 0.0
        env.step(constructive_actions(view))

    assert roster_sizes == [4] * 6 + [2] * 4 + [4] * 2
    assert env.outcome().utility == 1.0

    invalid = BatteryRosterEnv(ledger)
    view = invalid.observe()
    actions = constructive_actions(view)
    actions[np.flatnonzero(~view.active_mask)[0], 0] = 1.0
    with pytest.raises(ValueError, match="inactive lifecycle"):
        invalid.step(actions)


def test_myopic_controller_uses_no_rotation_or_future_role_information() -> None:
    ledger = make_ledger((5, 2, 4, 1, 3, 0))
    env = BatteryRosterEnv(ledger)
    for _ in range(6):
        view = env.observe()
        actions = myopic_equal_actions(view)
        active_effort = (actions[view.active_mask, 0] + 1.0) / 2.0
        np.testing.assert_array_equal(
            active_effort,
            np.full(active_effort.shape, view.demand / active_effort.size),
        )
        env.step(actions)

    outcome = run_controller(ledger, myopic_equal_actions)
    assert outcome.utility < 0.90
    assert outcome.minimum_step_utility == 0.0
