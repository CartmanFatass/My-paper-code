from __future__ import annotations

from dataclasses import replace

import pytest

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import (
    BCRHFixture,
    all_bcrh_fixtures,
    deterministic_general_bcrh,
    deterministic_maximum_bcrh,
    deterministic_general_episode,
    deterministic_sensitivity_fixture,
    deterministic_host_fixture,
)
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import GeneralAgentState
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import (
    NativeInteractiveBatch,
    NativeBackendError,
    checker_detects_scorer_perturbation,
    native_artifact_identity,
    probe_bcrh_over_cap_rejection,
    require_cpp_batched_backend,
    run_native_fixture_batch,
    run_native_bcrh_batch,
    run_native_episode_batch,
    run_native_sensitivity_batch,
    run_native_host_batch,
    run_native_clearance_batch,
    run_native_first_prehistory_batch,
)


@pytest.mark.parametrize("width", [1, 8, 32])
def test_native_reset_to_terminal_widths(width: int) -> None:
    fixtures = tuple(deterministic_host_fixture(1 + index % 2) for index in range(width))
    rows = run_native_host_batch(fixtures)
    assert len(rows) == width
    for fixture, row in zip(fixtures, rows):
        assert row["integrated_ticks"] == 240
        assert row["decision_count"] == 12
        assert not row["safety_violation"]
        assert not row["exclusivity_violation"]
        if fixture.failed_zone == 1:
            assert row["failed_rank"] == 1
            assert row["fail_endpoint"] == (24, 120)
            assert row["total_endpoint"] == (204, 480)
        else:
            assert row["failed_rank"] == 2
            assert row["fail_endpoint"] == (4, 120)
            assert row["total_endpoint"] == (184, 480)
        assert row["intact_endpoint"] == (120, 240)


@pytest.mark.parametrize("width",[1,8,32])
def test_interactive_native_reset_six_observation_conditioned_steps_terminal(width:int)->None:
    fixtures=tuple(deterministic_general_episode(1+i%2) for i in range(width))
    oracle=run_native_episode_batch(fixtures)
    batch=NativeInteractiveBatch(fixtures)
    try:
        observations=tuple(row["next_observation"] for row in batch.initial)
        assert all(row is not None and row["epoch"]==0 for row in observations)
        for expected_epoch in range(6):
            commands=tuple(fixture.post_commands[int(observation["epoch"])] for fixture,observation in zip(fixtures,observations))
            rows=batch.step(commands)
            assert all(row["epoch"]==expected_epoch+1 for row in rows)
            observations=tuple(row["next_observation"] for row in rows)
        assert all(row["terminal"] and row["next_observation"] is None for row in rows)
        for interactive,expected in zip(rows,oracle):
            assert interactive["integrated_ticks"]==240
            assert interactive["fail_endpoint"]==expected["fail_endpoint"]
            assert interactive["total_endpoint"]==expected["total_endpoint"]
            assert interactive["intact_endpoint"]==expected["intact_endpoint"]
            assert not interactive["safety_violation"] and not interactive["exclusivity_violation"]
        with pytest.raises(NativeBackendError):batch.step(tuple((None,None,None,None) for _ in range(width)))
    finally:
        batch.close()


def test_all_64_bcrh_scorer_checker_fixtures() -> None:
    rows = run_native_fixture_batch(all_bcrh_fixtures())
    assert len(rows) == 64
    assert all(row["scorer_checker_equal"] for row in rows)
    assert all(row["independent_enumerator_equal"] for row in rows)
    assert all(row["witness_present"] for row in rows)
    assert all(row["post60_reduced_verified"] for row in rows)
    assert all(0 < row["candidate_count"] <= 1961 for row in rows)
    assert all(row["selected_floor"][0] * 30 >= row["selected_floor"][1] for row in rows)
    assert all(row["selected_event_count"] <= 18 * 8 for row in rows)
    assert all(row["selected_reward_record_count"] <= 288 for row in rows)


@pytest.mark.parametrize("width", [1, 8, 32])
def test_bcrh_batch_widths_are_deterministic(width: int) -> None:
    fixture=BCRHFixture(1,2,2,1,1,1)
    rows=run_native_fixture_batch((fixture,)*width)
    assert len(rows)==width
    assert all(row==rows[0] for row in rows)


def test_native_abi_exports_and_sizes_are_verified() -> None:
    identity = native_artifact_identity()
    assert identity["schema"] == "VNFC-BPCR-R09-NATIVE-ARTIFACT-IDENTITY-v1"
    assert identity["abi_version"] == 1
    assert identity["abi_sizes"] == {
        "fixture_input":40,"fixture_output":80,"host_input":408,"host_output":112,
        "general_agent_input":52,"episode_input":920,"decision_trace":3144,
        "episode_output":19040,"bcrh_input":504,"bcrh_output":235472,
        "bcrh_candidate_record":120,
        "sensitivity_input":552,"sensitivity_output":52,
        "interactive_output":6464,"clearance_input":16,"clearance_output":8,"prehistory_output":20,
    }
    assert identity["full_reset_step_cpp"]
    assert identity["bcrh_scorer_checker_cpp"]
    assert not identity["python_fallback"]
    with pytest.raises(ValueError):
        require_cpp_batched_backend(build_root="forbidden")


@pytest.mark.parametrize("width",[1,8,32])
def test_general_native_episode_internal_prehistory_observability(width:int)->None:
    fixtures=tuple(deterministic_general_episode(1+index%2) for index in range(width))
    rows=run_native_episode_batch(fixtures)
    assert len(rows)==width
    for fixture,row in zip(fixtures,rows):
        assert row["integrated_ticks"]==240
        assert row["prehistory_decisions"]==row["post_decisions"]==6
        assert row["prehistory_commands"]==((1,2,5,6),)*6
        assert row["failed_rank"]==(1 if fixture.failed_zone==1 else 5)
        assert row["fail_endpoint"]==(0,120)
        assert row["total_endpoint"]==(40,480)
        assert row["intact_endpoint"]==(40,240)
        assert not row["safety_violation"] and not row["exclusivity_violation"]
        assert len(row["traces"])==6
        assert all(len(trace["agent_rows"])==7*38 for trace in row["traces"])
        assert all(len(trace["zone_rows"])==2*15 for trace in row["traces"])
        assert all(len(trace["globals"])==4 for trace in row["traces"])
        assert all(len(trace["legality"])==7*4 for trace in row["traces"])
        # At t=20 the replacement is on the second edge of its multiedge route.
        replacement_index=fixture.post_presentations[1].index(3)
        start=replacement_index*38
        replacement_row=row["traces"][1]["agent_rows"][start:start+38]
        expected_edge_index=10 if fixture.failed_zone==1 else 12
        expected_remaining=0.25 if fixture.failed_zone==1 else 0.125
        assert replacement_row[expected_edge_index]==1.0
        assert replacement_row[18]==expected_remaining


@pytest.mark.parametrize("width",[1,8,32])
def test_general_bcrh_arbitrary_epoch_batches(width:int)->None:
    fixtures=tuple(deterministic_general_bcrh(index%6) for index in range(width))
    rows=run_native_bcrh_batch(fixtures)
    for fixture,row in zip(fixtures,rows):
        assert 0<row["candidate_count"]<=1961
        assert row["scorer_command"]==row["checker_command"]
        assert row["scorer_checker_equal"] and row["independent_enumerator_equal"]
        assert row["objective_limbs"]==row["checker_objective_limbs"]
        assert row["candidate_digest"]==row["checker_digest"]
        assert row["post60_reduced"]==(fixture.epoch>=3)
        assert row["floor"]==(0,1) if fixture.epoch>=3 else row["floor"][1]>0


def test_general_bcrh_exposes_every_scorer_checker_comparison() -> None:
    row=run_native_bcrh_batch((deterministic_general_bcrh(0),),include_candidate_records=True)[0]
    records=row["candidate_records"]
    assert len(records)==row["candidate_count"]
    assert all(record["exact_match"] for record in records)
    assert all(record["floor"]==record["checker_floor"] for record in records)
    assert all(record["objective_limbs"]==record["checker_objective_limbs"] for record in records)


def test_bcrh_exact_candidate_cap_and_active_n8_output_canary()->None:
    maximum=run_native_bcrh_batch((deterministic_maximum_bcrh(),),include_candidate_records=True)[0]
    assert maximum["candidate_count"]==1961 and len(maximum["candidate_records"])==1961
    assert maximum["scorer_checker_equal"] and maximum["independent_enumerator_equal"] and all(row["exact_match"] for row in maximum["candidate_records"])
    rejected=probe_bcrh_over_cap_rejection()
    assert rejected=={"active_count":8,"unconstrained_command_count":3393,"candidate_cap":1961,"status":21,"output_unchanged":True}


def test_independent_checker_detects_scorer_only_derived_perturbation() -> None:
    fixtures=tuple(deterministic_general_bcrh(epoch) for epoch in range(6))
    assert checker_detects_scorer_perturbation(fixtures)==(True,)*6


def test_acquired_relay_is_replaceable_and_both_stationary_states_clear() -> None:
    fixture=deterministic_general_episode(1)
    agents=tuple(replace(agent,node=1,destination_node=1,token=1,token_state=2,acquisition_elapsed=4,energy_fifths=600) if agent.rank==8 else agent for agent in fixture.agents)
    command=run_native_first_prehistory_batch((replace(fixture,agents=agents),))[0]
    by_rank={agent.rank:agent for agent in agents}
    assert command[1]!=8 and command[1] is not None and by_rank[command[1]].radio==2
    assert run_native_clearance_batch((1,2))==(1,1)


def test_interactive_malformed_batch_fails_before_any_session_advances() -> None:
    fixtures=tuple(deterministic_general_episode(1+i%2) for i in range(8));batch=NativeInteractiveBatch(fixtures)
    try:
        malformed=list(fixture.post_commands[0] for fixture in fixtures);malformed[-1]=(3,3,None,None)
        with pytest.raises(NativeBackendError):batch.step(malformed)
        rows=batch.step(tuple(fixture.post_commands[0] for fixture in fixtures))
        assert all(row["epoch"]==1 for row in rows)
        with pytest.raises(ValueError):batch.step(((None,None,None,None),))
    finally:batch.close()
    batch.close()


@pytest.mark.parametrize("width",[1,8,32])
def test_native_all_command_action_sensitivity(width:int)->None:
    rows=run_native_sensitivity_batch((deterministic_sensitivity_fixture(),)*width)
    assert len(rows)==width and all(row==rows[0] for row in rows)
    row=rows[0]
    assert row["candidate_count"]>1
    assert row["sensitive"]==(row["max_c60"]-row["min_c60"]>=6)


def test_malformed_and_empty_batches_fail_closed() -> None:
    with pytest.raises(ValueError):
        run_native_host_batch(())
    with pytest.raises(ValueError):
        run_native_fixture_batch(())
    with pytest.raises(ValueError):
        run_native_episode_batch(())
    with pytest.raises(ValueError):
        run_native_bcrh_batch(())
    with pytest.raises(ValueError):
        run_native_sensitivity_batch(())
    with pytest.raises(ValueError):
        NativeInteractiveBatch(())
    invalid = replace(deterministic_host_fixture(1), commands=((1, 1, 2, 3),) * 12)
    with pytest.raises(ValueError):
        run_native_host_batch((invalid,))
    with pytest.raises(NativeBackendError):
        run_native_fixture_batch((BCRHFixture(0, 1, 1, 0, 0, 0),))
