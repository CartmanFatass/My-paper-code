from __future__ import annotations

import numpy as np

from experiments.candidates.ebcr_variable_k.config import (
    BASE_SEEDS, DECLARED_BUDGETS, PRODUCTION_CONFIG,
)
from experiments.candidates.ebcr_variable_k.host import generate_episode, run_episode
from experiments.candidates.ebcr_variable_k.run import _registered_budget_facts


class ConstantActor:
    def __init__(self, probability: float) -> None:
        self.probability = probability

    def probabilities(self, features: np.ndarray) -> np.ndarray:
        return np.full(features.shape[0], self.probability, dtype=np.float64)


def test_local_partner_slots_are_zero_and_coord_receives_only_delayed_bits():
    exogenous = generate_episode(
        seed=17, episode=0, namespace="mask", cell="ID_ON",
        durations=(128,), noise=0.0, joint_mismatch=True, horizon=8,
    )
    local = run_episode(
        exogenous, arm="LOCAL", actor=ConstantActor(1.0),
        critic_value=lambda _: 0.0, collect_training=True,
    )
    coord = run_episode(
        exogenous, arm="COORD", actor=ConstantActor(1.0),
        critic_value=lambda _: 0.0, collect_training=True,
    )
    assert np.array_equal(local.training_records[1].actor_features[:, -2:], np.zeros((2, 2)))
    assert np.array_equal(
        coord.training_records[1].actor_features[0, -2:],
        np.asarray([1.0, exogenous.readiness[0, 1]], dtype=np.float32),
    )
    assert np.array_equal(
        coord.training_records[1].actor_features[1, -2:],
        np.asarray([1.0, exogenous.readiness[0, 0]], dtype=np.float32),
    )


def test_max_age_is_policy_masked_but_remains_in_critic_return_trajectory():
    exogenous = generate_episode(
        seed=17, episode=0, namespace="max", cell="LONG_OFF",
        durations=(128,), noise=0.0, joint_mismatch=False, horizon=34,
    )
    row = run_episode(
        exogenous, arm="LOCAL", actor=ConstantActor(0.0),
        critic_value=lambda _: 0.0, collect_training=True,
    )
    assert tuple(row.training_records[32].policy_mask) == (0.0, 0.0)
    assert row.training_records[32].reward <= 0.0
    assert row.forced_max_renewals == (1, 1)
    assert len(row.training_records) == 34


def test_safety_is_immediate_single_agent_clock_reset_and_caps_hold():
    exogenous = generate_episode(
        seed=17, episode=0, namespace="safety", cell="ID_OFF",
        durations=(12, 20, 28), noise=0.05, joint_mismatch=False,
        horizon=128, safety=True,
    )
    row = run_episode(exogenous, arm="FIXED-4", actor=ConstantActor(0.5))
    affected = exogenous.safety_agent
    assert affected is not None and exogenous.safety_tick is not None
    assert row.emergency_renewals[affected] == 1
    assert row.emergency_renewals[1 - affected] == 0
    assert exogenous.safety_tick in row.renewal_times[affected]
    assert row.emergency_immediate and not row.cap_violation
    assert max(row.total_renewals) <= 32


def test_nonlearned_arm_executes_two_actor_sized_rows_on_every_tick():
    class CountingActor(ConstantActor):
        def __init__(self):
            super().__init__(0.5)
            self.rows = 0
            self.invocations = 0

        def probabilities(self, features: np.ndarray) -> np.ndarray:
            self.rows += features.shape[0]
            self.invocations += 1
            return super().probabilities(features)

    exogenous = generate_episode(
        seed=17, episode=0, namespace="calls", cell="ID_OFF",
        durations=(128,), noise=0.0, joint_mismatch=False, horizon=12,
    )
    actor = CountingActor()
    row = run_episode(exogenous, arm="STAGE-ORACLE", actor=actor)
    assert actor.invocations == 12
    assert actor.rows == row.actor_forward_calls == 24


def test_registered_counts_caps_and_defaults_are_exact():
    assert BASE_SEEDS == (17, 31, 47, 61, 79, 97)
    assert PRODUCTION_CONFIG.training_episodes == 512
    assert PRODUCTION_CONFIG.primary_episodes_per_cell == 64
    assert PRODUCTION_CONFIG.safety_episodes_per_cell == 4
    facts = _registered_budget_facts(PRODUCTION_CONFIG)
    assert facts == {
        "training_team_ticks": 786432,
        "fixed_selection_team_ticks": 262144,
        "maximum_panel_team_ticks": 3760128,
        "maximum_evaluation_team_ticks": 4022272,
        "maximum_total_team_ticks": 4808704,
    }
    assert facts["training_team_ticks"] == DECLARED_BUDGETS["training_team_ticks"]
    assert facts["maximum_evaluation_team_ticks"] <= 5_000_000
    assert facts["maximum_total_team_ticks"] <= 6_000_000


def test_registered_safety_manifest_balances_role_and_spreads_unique_event_ticks():
    episodes = [
        generate_episode(
            seed=17, episode=index, namespace="safety_balance", cell="panel",
            durations=(12, 20, 28), noise=0.05, joint_mismatch=bool(index % 2),
            safety=True,
        ) for index in range(32)
    ]
    assert [sum(row.safety_agent == role for row in episodes) for role in range(2)] == [16, 16]
    ticks = [row.safety_tick for row in episodes]
    assert len(set(ticks)) == 32
    assert min(ticks) >= 32 and max(ticks) <= 95
