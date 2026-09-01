from fractions import Fraction

import pytest

from experiments.candidates.ucope.competence_first_scout_r01.contract import (
    B1_SEEDS,
    RunBinding,
    ScoutConfig,
    context_id,
    expected_activity_totals,
    validate_host_opportunity_map,
)
from experiments.candidates.ucope.competence_first_scout_r01.host import (
    behavior_stratum,
    execute_policy_episode,
    generate_population,
    group_fold,
    validate_population,
)


def test_b1_and_assess_factories_are_exact_and_roundtrip_without_recursion():
    b1 = ScoutConfig.b1()
    assert b1.seed_ids == B1_SEEDS
    assert (b1.episodes_per_context, b1.tail_updates, b1.root_updates) == (5120, 160, 320)
    assert b1.evaluation_root_updates == (40, 80, 160, 320)
    assert ScoutConfig.from_dict(b1.to_dict()) == b1
    assess = ScoutConfig.assess()
    assert (assess.episodes_per_context, assess.tail_updates, assess.root_updates) == (320, 8, 16)
    assert assess.evaluation_root_updates == (8, 16)
    assert ScoutConfig.from_dict(assess.to_dict()) == assess
    binding = RunBinding.assess("a" * 64)
    assert RunBinding.from_value(binding.to_dict(), "ASSESS") == binding


def test_group_fold_and_behavior_schedule_are_exact():
    assert [behavior_stratum(i) for i in range(10)] == [
        ("PROBE", 1), ("PROBE", 3), ("PROBE", 5), ("PROBE", 7), ("PROBE", 9),
        ("IMMEDIATE", 1), ("IMMEDIATE", 3), ("IMMEDIATE", 5), ("IMMEDIATE", 7), ("IMMEDIATE", 9),
    ]
    assert [group_fold(i) for i in (0, 9, 10, 19, 20)] == [0, 0, 1, 1, 0]


def test_fresh_population_parity_and_activity_totals():
    config = ScoutConfig.assess()
    seed = config.seed_ids[0]
    rows = generate_population(config, seed)
    audit = validate_population(config, seed, rows)
    assert audit["episodes"] == 320 * 8
    assert audit["root_rows"] == 320 * 8
    assert audit["tail_rows"] == 160 * 8
    assert audit["transitions"] == 320 * 8 * 5
    assert all((row.displayed_short_count is None) == (row.behavior_action == "IMMEDIATE") for row in rows)
    for index in range(config.episodes_per_context):
        assert {row.fold_id for row in rows if row.episode_index == index} == {group_fold(index)}


def test_shared_environment_executor_preserves_primitive_causality_and_pairing():
    linked = ("LINKED", Fraction(17, 20), Fraction(9, 100))
    first = execute_policy_episode(
        linked, ancestry=("fresh-test",), episode_index=3, root_action="PROBE",
        tail_selector=lambda count: 2 if count >= 3 else 8, evaluation=True,
    )
    second = execute_policy_episode(
        linked, ancestry=("fresh-test",), episode_index=3, root_action="PROBE",
        tail_selector=lambda count: 2 if count >= 3 else 8, evaluation=True,
    )
    assert first == second
    assert first.external_return == pytest.approx(
        first.probe_service + first.probe_time + first.probe_energy + first.tail_service + first.tail_time + first.tail_energy
    )
    immediate = execute_policy_episode(
        linked, ancestry=("fresh-test",), episode_index=3, root_action="IMMEDIATE",
        immediate_period=4, evaluation=True,
    )
    assert (immediate.probe_service, immediate.probe_time, immediate.probe_energy) == (0.0, 0.0, 0.0)
    assert immediate.transition_count == 2 and first.transition_count == 8


def test_exact_opportunity_map_has_one_target_and_negative_direct_probe():
    assert validate_host_opportunity_map() == {
        "valid": True,
        "target_context_id": "LINKED-p17_20-c9_100",
        "contexts": 8,
    }


def test_b1_exact_activity_totals_match_pro_contract():
    totals = expected_activity_totals(ScoutConfig.b1())
    assert totals == {
        "environment_episodes": 122_880,
        "environment_transitions": 614_400,
        "root_rows": 122_880,
        "tail_rows": 61_440,
        "root_optimizer_updates": 5_760,
        "tail_optimizer_updates": 2_880,
        "root_example_exposures": 1_474_560,
        "tail_example_exposures": 737_280,
        "exact_policy_evaluations": 576,
        "sampled_evaluation_episodes": 36_864,
        "checkpoint_writes": 72,
        "policies_completed": 18,
    }
