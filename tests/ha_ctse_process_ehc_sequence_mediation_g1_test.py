from __future__ import annotations

from dataclasses import asdict
import json

import pytest

from ha_ctse_process.ehc_sequence_mediation_g1 import (
    CONTROLLERS,
    analyze_prototype,
    collect_natural_episode,
    primitive_logits,
    run_event_intervention,
    run_mark_intervention,
)
from ha_ctse_process.temporal_duty_g1 import HORIZON, make_episode_spec


SEEDS = {"event": 123, "mark": 456, "action": 789}


def _spec():
    return make_episode_spec("fitting", 2, 6, 1, 0)


def _episode(controller: str, seeds: dict[str, int] | None = None):
    return collect_natural_episode(_spec(), controller, seeds or SEEDS)


def _slot_rows(episode: dict[str, object], slot: int = 0):
    return [row for row in episode["rows"] if row["slot"] == slot]


def test_primitive_logits_adds_only_the_frozen_treatment_path():
    assert primitive_logits((1.0, 2.0, 3.0), 1, 1) == (-3.0, 2.0, 7.0)
    assert primitive_logits((1.0, 2.0, 3.0), 1, -1) == (5.0, 2.0, -1.0)
    assert primitive_logits((1.0, 2.0, 3.0), 0, 1) == (1.0, 2.0, 3.0)


def test_registered_controller_order_is_frozen():
    assert CONTROLLERS == (
        "MECHANISM_CONTROL",
        "RANDOM_USE",
        "EXOGENOUS_LIFETIME",
        "LOGIT_WITHOUT_BEHAVIOR",
        "RECURRENT_CONTROL",
        "DUM_CONTROL",
    )


def test_dum_receives_mechanism_events_and_marks_but_m_is_zero():
    mechanism_rows = _episode("MECHANISM_CONTROL")["rows"]
    dum_rows = _episode("DUM_CONTROL")["rows"]
    assert [(row["event"], row["mark"]) for row in dum_rows] == [
        (row["event"], row["mark"]) for row in mechanism_rows
    ]
    assert {row["treatment"] for row in dum_rows} == {0}
    assert {row["primitive_logits"] for row in dum_rows} == {(0.0, 0.0, 0.0)}
    assert {row["action"] for row in dum_rows} == {-1}


def test_recurrent_control_uses_no_event_or_mark_path_and_remembers_cue():
    rows = _slot_rows(_episode("RECURRENT_CONTROL"))
    assert {row["event"] for row in rows} == {"NONE"}
    assert {row["mark"] for row in rows} == {0}
    assert {row["treatment"] for row in rows} == {0}
    assert rows[2]["observation"][0] == 0.0
    assert rows[2]["action"] == 1


def test_random_use_is_nondegenerate_and_marks_persist_between_renewals():
    rows = _slot_rows(_episode("RANDOM_USE"))
    events = [row["event"] for row in rows]
    assert "KEEP" in events and "RENEW" in events
    for previous, current in zip(rows, rows[1:]):
        if current["event"] == "KEEP":
            assert current["mark"] == previous["mark"]


def test_random_use_initializes_independent_mark_when_first_event_is_keep():
    negative_mark = _episode(
        "RANDOM_USE", {"event": 2, "mark": 1, "action": 789}
    )
    positive_mark = _episode(
        "RANDOM_USE", {"event": 2, "mark": 2, "action": 789}
    )
    negative_rows = _slot_rows(negative_mark)
    positive_rows = _slot_rows(positive_mark)

    assert negative_rows[0]["event"] == positive_rows[0]["event"] == "KEEP"
    assert negative_rows[0]["observation"][0] == positive_rows[0]["observation"][0] == 1.0
    assert negative_rows[0]["mark"] == -1
    assert positive_rows[0]["mark"] == 1
    assert [row["event"] for row in negative_mark["rows"]] == [
        row["event"] for row in positive_mark["rows"]
    ]


def test_exogenous_lifetime_renews_every_fourth_active_opportunity():
    rows = _slot_rows(_episode("EXOGENOUS_LIFETIME"))
    renew_opportunities = [
        row["controller_opportunity"] for row in rows if row["event"] == "RENEW"
    ]
    assert renew_opportunities == list(range(0, len(rows), 4))
    assert rows[0]["mark"] == 1


def test_logit_without_behavior_has_only_one_step_mark_influence():
    rows = _slot_rows(_episode("LOGIT_WITHOUT_BEHAVIOR"))
    first_segment = rows[:6]
    assert first_segment[0]["event"] == "RENEW"
    assert first_segment[0]["primitive_logits"] == (-4.0, 0.0, 4.0)
    assert first_segment[0]["action"] == 1
    assert all(row["event"] == "KEEP" for row in first_segment[1:])
    assert all(row["mark"] == 1 for row in first_segment[1:])
    assert all(row["treatment"] == 0 for row in first_segment[1:])
    assert all(row["primitive_logits"] == (0.0, 0.0, 0.0) for row in first_segment[1:])
    assert all(row["action"] == -1 for row in first_segment[1:])


def test_greedy_ties_choose_lowest_action_index_and_action_rng_draws_zero():
    episode = _episode("DUM_CONTROL")
    assert episode["rng_draws"]["action"] == 0
    assert {row["action"] for row in episode["rows"]} == {-1}
    assert {row["action_rng_draws"] for row in episode["rows"]} == {0}


def test_natural_rows_carry_unforced_controller_and_manifest_provenance():
    episode = _episode("MECHANISM_CONTROL")
    assert episode["controller"] == "MECHANISM_CONTROL"
    assert episode["spec"] == asdict(_spec())
    assert episode["seeds"] == SEEDS
    assert len(episode["rows"]) == _spec().action_denominator
    assert all(row["provenance"] == "natural" for row in episode["rows"])
    assert all(row["forced"] is False for row in episode["rows"])
    assert all(row["controller"] == "MECHANISM_CONTROL" for row in episode["rows"])


def test_rng_namespaces_are_separate_and_action_seed_is_observationally_inert():
    base = _episode("RANDOM_USE")
    changed_mark = _episode("RANDOM_USE", {**SEEDS, "mark": 457})
    changed_action = _episode("RANDOM_USE", {**SEEDS, "action": 790})

    assert [row["event"] for row in base["rows"]] == [
        row["event"] for row in changed_mark["rows"]
    ]
    assert [row["mark"] for row in base["rows"]] != [
        row["mark"] for row in changed_mark["rows"]
    ]
    assert base["rows"] == changed_action["rows"]
    assert base["outcome"] == changed_action["outcome"]
    assert base["rng_draws"]["action"] == changed_action["rng_draws"]["action"] == 0


@pytest.mark.parametrize("controller", CONTROLLERS)
def test_every_controller_collects_one_complete_natural_episode(controller: str):
    episode = _episode(controller)
    assert episode["outcome"]["action_opportunities"] == _spec().action_denominator
    assert episode["final_environment_state"]["time"] == _spec().horizon


def _first_snapshot(controller: str = "MECHANISM_CONTROL"):
    return _episode(controller)["branch_snapshots"][0]


def test_branch_selection_is_outcome_blind_first_age_three_state():
    episode = _episode("MECHANISM_CONTROL")
    assert 1 <= len(episode["branch_snapshots"]) <= 2
    assert all(snapshot["selection"]["age"] == 3 for snapshot in episode["branch_snapshots"])
    assert all(snapshot["selection"]["cue_present"] is False for snapshot in episode["branch_snapshots"])
    assert all(
        snapshot["selection"]["remaining_active_opportunities"] >= 2
        for snapshot in episode["branch_snapshots"]
    )
    assert all(
        snapshot["selection"]["terminal_event_same_step"] is False
        for snapshot in episode["branch_snapshots"]
    )
    assert all("outcome" not in snapshot for snapshot in episode["branch_snapshots"])
    assert [snapshot["target_slot"] for snapshot in episode["branch_snapshots"]] == [0, 1]


@pytest.mark.parametrize("intervention", (run_event_intervention, run_mark_intervention))
def test_paired_branches_restore_exact_origin_and_keep_common_future_rng(intervention):
    result = intervention(_first_snapshot("RANDOM_USE"), "RANDOM_USE")
    assert result["branch_origin_equal"] is True
    assert result["common_random_numbers"]["equal"] is True
    assert result["common_random_numbers"]["left_draws"] == result["common_random_numbers"]["right_draws"]


def test_event_and_mark_interventions_are_separate_registered_contrasts():
    snapshot = _first_snapshot()
    event_result = run_event_intervention(snapshot, "MECHANISM_CONTROL")
    mark_result = run_mark_intervention(snapshot, "MECHANISM_CONTROL")

    assert event_result["contrast"] == {
        "left": {"event": "KEEP", "mark": "current"},
        "right": {"event": "RENEW", "mark": "opposite"},
    }
    assert mark_result["contrast"] == {
        "left": {"event": "RENEW", "mark": "current"},
        "right": {"event": "RENEW", "mark": "opposite"},
    }
    assert event_result["branches"]["left"]["intervention_event"] == "KEEP"
    assert event_result["branches"]["right"]["intervention_event"] == "RENEW"
    assert mark_result["branches"]["left"]["intervention_event"] == "RENEW"
    assert mark_result["branches"]["right"]["intervention_event"] == "RENEW"


def test_downstream_window_excludes_intervention_action_and_terminal_runs_to_end():
    result = run_event_intervention(_first_snapshot(), "MECHANISM_CONTROL", window=6)
    for branch in result["branches"].values():
        assert len(branch["downstream_actions"]) == 6
        assert branch["intervention_time"] not in branch["downstream_times"]
        assert all(time > branch["intervention_time"] for time in branch["downstream_times"])
        assert branch["terminal_time"] == HORIZON


def test_branch_continuation_does_not_copy_a_natural_future_reference():
    snapshot = _first_snapshot("RANDOM_USE")
    baseline = run_event_intervention(snapshot, "RANDOM_USE")
    snapshot["untrusted_natural_future"] = [
        {"action": 99, "reward": float("nan"), "outcome": "must-not-be-read"}
    ]
    repeated = run_event_intervention(snapshot, "RANDOM_USE")
    assert repeated == baseline
    assert "untrusted_natural_future" not in repeated


def test_owned_snapshot_survives_a_json_round_trip_without_branch_drift():
    snapshot = _first_snapshot("RANDOM_USE")
    restored = json.loads(json.dumps(snapshot))
    assert run_mark_intervention(restored, "RANDOM_USE") == run_mark_intervention(
        snapshot, "RANDOM_USE"
    )


def _complete_records():
    records = []
    for controller in CONTROLLERS:
        for split, durations in (("fitting", (6, 14)), ("heldout", (10, 18))):
            for roster_size in (2, 3):
                for duration in durations:
                    for sign_start in (-1, 1):
                        for rotation in (0, 1):
                            spec = make_episode_spec(
                                split, roster_size, duration, sign_start, rotation
                            )
                            episode = collect_natural_episode(spec, controller, SEEDS)
                            episode["event_interventions"] = [
                                run_event_intervention(snapshot, controller)
                                for snapshot in episode["branch_snapshots"]
                            ]
                            episode["mark_interventions"] = [
                                run_mark_intervention(snapshot, controller)
                                for snapshot in episode["branch_snapshots"]
                            ]
                            records.append(episode)
    return records


def _finite_leaves(value):
    if isinstance(value, dict):
        return all(_finite_leaves(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_leaves(item) for item in value)
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        return value == value and abs(float(value)) != float("inf")
    return True


def test_analyzer_emits_only_complete_measurements_and_provenance_with_finite_values():
    analysis = analyze_prototype(_complete_records())
    assert set(analysis) == {"status", "measurement_tuple", "controller_provenance"}
    assert analysis["status"] == "COMPLETE"
    assert set(analysis["measurement_tuple"]) == {
        "policy_dependence",
        "instantaneous_tv",
        "sequence_hamming",
        "terminal_utility_delta",
        "natural_mediation",
        "heldout_robustness",
    }
    assert set(analysis["controller_provenance"]) == set(CONTROLLERS)
    assert _finite_leaves(analysis["measurement_tuple"])
    serialized = repr(analysis).lower()
    assert "threshold" not in serialized
    assert "p_value" not in serialized
    assert "scientific_disposition" not in serialized
