import numpy as np

from ha_ctse_process.dynamic_roster_testbed import (
    EXPECTED_SHORT_REQUIREMENT,
    HORIZON,
    GenericShortDynamicRosterEnv,
    constructive_actions,
    make_dynamic_roster_ledger,
)


def test_generic_short_dynamic_roster_contract():
    first = make_dynamic_roster_ledger(7)
    replay = make_dynamic_roster_ledger(7)
    assert first.temporary_leave == replay.temporary_leave
    assert first.terminal_leave == replay.terminal_leave
    assert first.wave_arrivals == replay.wave_arrivals
    assert np.array_equal(first.owner_priorities, replay.owner_priorities)

    environment = GenericShortDynamicRosterEnv(first)
    observations = []
    while environment.time < HORIZON:
        view = environment.observe()
        observations.append(view.observations)
        environment.step(constructive_actions(environment, view))
    outcome = environment.outcome()

    assert outcome.persistent_score == 1.0
    assert outcome.short_score == 1.0
    assert outcome.utility == 1.0
    assert outcome.short_required_total == EXPECTED_SHORT_REQUIREMENT
    assert outcome.roster_sizes == (4,) * 20 + (2,) * 20 + (6,) * 20 + (4,) * 20
    assert outcome.reward_trace[:-1] == (0.0,) * (HORIZON - 1)
    assert outcome.reward_trace[-1] == 1.0
    assert all(row.shape[1] == 15 for row in observations)
