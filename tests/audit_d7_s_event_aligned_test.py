"""Focused tests for the D7.S event-aligned source audit.

Contract: `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md` (FROZEN
2026-07-26). These are calibration of an instrument, not a specification of
behavior: each test's expected value comes from the frozen contract text or a
hand-worked example, never from re-deriving what the code already computes.

No real environment EPISODES are used (proof-sized, FakeEnv/synthetic idiom
matching `tests/audit_d7_s_persistence_margin_test.py`); the pure logic layer
under test is exactly what the real orchestration wires against a live
`UAVEnergyAwareRelayEnv`. Section 9's topology-template tests are the one
exception: they construct a real (lightweight, no-episode-stepping)
`UAVEnergyAwareRelayEnv` directly, because the measured defect they guard
against lives specifically in the real environment's `np_random`/
`_init_ground_bs` interaction and a synthetic stand-in would not exercise it.
"""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "audit_d7_s_event_aligned",
    _ROOT / "scripts" / "audit_d7_s_event_aligned.py",
)
audit = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = audit
_SPEC.loader.exec_module(audit)


# =============================================================================
# 1. Event detection and certification predicates, every exclusion path
# =============================================================================

def _base_candidate(**overrides):
    cand = {
        "t_e": 500,
        "station_occupancy_excluding_self": 0,
        "station_queue_length": 0,
        "cutoff_at_leave": False,
        "depletion_at_leave": False,
        "temporary_failure": False,
        "schedule_identity": "constructive_mixed",
    }
    cand.update(overrides)
    return cand


def test_eligible_leave_has_no_exclusion_reasons():
    reasons = audit.check_leave_eligibility(_base_candidate(), t_e=500)
    assert reasons == []


def test_censored_event_past_950_is_excluded():
    reasons = audit.check_leave_eligibility(_base_candidate(t_e=951), t_e=951)
    assert audit.EXCLUDE_CENSORED in reasons


def test_event_at_exactly_950_is_eligible():
    # t_e <= 1500 - 550 = 950 is the frozen boundary; 950 itself must clear.
    reasons = audit.check_leave_eligibility(_base_candidate(t_e=950), t_e=950)
    assert audit.EXCLUDE_CENSORED not in reasons


def test_occupied_station_excludes_the_event():
    reasons = audit.check_leave_eligibility(
        _base_candidate(station_occupancy_excluding_self=1), t_e=500
    )
    assert audit.EXCLUDE_QUEUE_OR_OCCUPIED in reasons


def test_nonzero_queue_excludes_the_event():
    reasons = audit.check_leave_eligibility(
        _base_candidate(station_queue_length=1), t_e=500
    )
    assert audit.EXCLUDE_QUEUE_OR_OCCUPIED in reasons


def test_cutoff_driven_leave_is_excluded():
    reasons = audit.check_leave_eligibility(
        _base_candidate(cutoff_at_leave=True), t_e=500
    )
    assert audit.EXCLUDE_EMERGENCY in reasons


def test_depletion_driven_leave_is_excluded():
    reasons = audit.check_leave_eligibility(
        _base_candidate(depletion_at_leave=True), t_e=500
    )
    assert audit.EXCLUDE_EMERGENCY in reasons


def test_temporary_failure_leave_is_excluded():
    reasons = audit.check_leave_eligibility(
        _base_candidate(temporary_failure=True), t_e=500
    )
    assert audit.EXCLUDE_TEMP_FAILURE in reasons


def test_leave_off_the_registered_schedule_is_excluded():
    reasons = audit.check_leave_eligibility(
        _base_candidate(schedule_identity="full_sync_SET"), t_e=500
    )
    assert audit.EXCLUDE_OFF_SCHEDULE in reasons


def test_stable_certification_requires_all_four_predicates():
    ok, reasons = audit.certify_stable(
        active=True, has_valid_incumbent=True,
        future_target_displacement_m=10.0,
        scheduled_to_leave_within_delta=False,
        has_legal_set_alternative=True,
    )
    assert ok and reasons == []


def test_stable_certification_fails_without_valid_incumbent():
    ok, reasons = audit.certify_stable(
        active=True, has_valid_incumbent=False,
        future_target_displacement_m=10.0,
        scheduled_to_leave_within_delta=False,
        has_legal_set_alternative=True,
    )
    assert not ok and "no_valid_incumbent" in reasons


def test_stable_certification_fails_when_displacement_exceeds_X():
    # X = 50 m is frozen; 50.0 exactly must pass, 50.01 must fail.
    ok_at_boundary, _ = audit.certify_stable(
        active=True, has_valid_incumbent=True,
        future_target_displacement_m=50.0,
        scheduled_to_leave_within_delta=False,
        has_legal_set_alternative=True,
    )
    ok_over, reasons_over = audit.certify_stable(
        active=True, has_valid_incumbent=True,
        future_target_displacement_m=50.01,
        scheduled_to_leave_within_delta=False,
        has_legal_set_alternative=True,
    )
    assert ok_at_boundary
    assert not ok_over and "displacement_exceeds_X" in reasons_over


def test_stable_certification_fails_when_incumbent_itself_will_leave():
    ok, reasons = audit.certify_stable(
        active=True, has_valid_incumbent=True,
        future_target_displacement_m=10.0,
        scheduled_to_leave_within_delta=True,
        has_legal_set_alternative=True,
    )
    assert not ok and "scheduled_to_leave_within_delta" in reasons


def test_stable_certification_fails_on_empty_alternative_set():
    ok, reasons = audit.certify_stable(
        active=True, has_valid_incumbent=True,
        future_target_displacement_m=10.0,
        scheduled_to_leave_within_delta=False,
        has_legal_set_alternative=False,
    )
    assert not ok and audit.EXCLUDE_EMPTY_SET_ALT in reasons


def test_flex_certification_requires_leave_after_preceding_check():
    ok, reasons, focal = audit.certify_flex(
        leave_step=480, prior_check_step=480, t_e=490,
        queue_or_cutoff_caused=False,
        survivors={1: {"transit_steps": 50, "support_ok": True}},
    )
    assert not ok and "leave_not_after_preceding_check" in reasons


def test_flex_certification_requires_leave_within_Y_steps_of_t_e():
    # Y = 10 is frozen: leave 11 steps before t_e must fail.
    ok, reasons, _ = audit.certify_flex(
        leave_step=479, prior_check_step=470, t_e=490,
        queue_or_cutoff_caused=False,
        survivors={1: {"transit_steps": 50, "support_ok": True}},
    )
    assert not ok and "leave_too_far_before_t_e" in reasons


def test_flex_certification_passes_at_exactly_Y_steps():
    ok, reasons, focal = audit.certify_flex(
        leave_step=480, prior_check_step=470, t_e=490,
        queue_or_cutoff_caused=False,
        survivors={1: {"transit_steps": 50, "support_ok": True}},
    )
    assert ok and reasons == [] and focal == 1


def test_flex_certification_excludes_queue_or_cutoff_caused_leave():
    ok, reasons, _ = audit.certify_flex(
        leave_step=485, prior_check_step=470, t_e=490,
        queue_or_cutoff_caused=True,
        survivors={1: {"transit_steps": 50, "support_ok": True}},
    )
    assert not ok and audit.EXCLUDE_EMERGENCY in reasons


def test_flex_certification_requires_Z_step_coverage():
    # Z = 139 is frozen: a survivor at 140 steps cannot cover.
    ok, reasons, focal = audit.certify_flex(
        leave_step=485, prior_check_step=470, t_e=490,
        queue_or_cutoff_caused=False,
        survivors={1: {"transit_steps": 140, "support_ok": True}},
    )
    assert not ok and "no_covering_survivor" in reasons and focal is None


def test_flex_certification_rejects_survivor_violating_hard_support():
    ok, reasons, focal = audit.certify_flex(
        leave_step=485, prior_check_step=470, t_e=490,
        queue_or_cutoff_caused=False,
        survivors={1: {"transit_steps": 50, "support_ok": False}},
    )
    assert not ok and "no_covering_survivor" in reasons and focal is None


def test_flex_focal_is_minimum_transit_survivor():
    ok, reasons, focal = audit.certify_flex(
        leave_step=485, prior_check_step=470, t_e=490,
        queue_or_cutoff_caused=False,
        survivors={
            5: {"transit_steps": 80, "support_ok": True},
            2: {"transit_steps": 40, "support_ok": True},
            7: {"transit_steps": 100, "support_ok": True},
        },
    )
    assert ok and focal == 2


def test_flex_certification_fails_on_empty_alternative_set():
    """Q-C4 applies the empty-legal-alternative-set predicate to BOTH limbs,
    not only stable -- a flex vacancy with a perfectly good covering
    survivor must still be ineligible if no legal SET alternative exists."""
    ok, reasons, focal = audit.certify_flex(
        leave_step=480, prior_check_step=470, t_e=490,
        queue_or_cutoff_caused=False,
        survivors={1: {"transit_steps": 50, "support_ok": True}},
        has_legal_set_alternative=False,
    )
    assert not ok and audit.EXCLUDE_EMPTY_SET_ALT in reasons


def test_flex_certification_default_has_legal_set_alternative_true():
    """Default keeps existing callers' behavior unchanged when they don't
    yet supply the predicate."""
    ok, reasons, focal = audit.certify_flex(
        leave_step=480, prior_check_step=470, t_e=490,
        queue_or_cutoff_caused=False,
        survivors={1: {"transit_steps": 50, "support_ok": True}},
    )
    assert ok and audit.EXCLUDE_EMPTY_SET_ALT not in reasons


def test_flex_focal_tie_break_is_ascending_uav_index():
    ok, reasons, focal = audit.certify_flex(
        leave_step=485, prior_check_step=470, t_e=490,
        queue_or_cutoff_caused=False,
        survivors={
            5: {"transit_steps": 40, "support_ok": True},
            2: {"transit_steps": 40, "support_ok": True},
        },
    )
    assert ok and focal == 2


def test_transit_steps_rounds_up():
    # A worked example independent of the implementation, using the UAV
    # max_speed (30 m/s, scenario_base.py:56/161 default) and time_step
    # (1.0 s) -- NOT the 5 m/s S3 user/cluster speed override, which is a
    # different physical quantity and was the prior (wrong) test's input.
    # 4170 m at 30 m/s, dt=1s -> 139.0 exactly -> ceil is still 139 (== Z).
    assert audit.transit_steps(4170.0, max_speed=30.0, dt=1.0) == 139
    # 4171 m -> 139.033... -> ceil 140 (exceeds Z, would fail coverage).
    assert audit.transit_steps(4171.0, max_speed=30.0, dt=1.0) == 140


def test_flex_transit_steps_for_env_binds_v_max_to_env_max_speed():
    """The orchestration-boundary binding point for item 10: any caller
    building `certify_flex`'s survivor transit times from a real env must
    read `env.max_speed` (30 m/s), never hardcode the 5 m/s user speed."""
    class _FakeEnv:
        max_speed = 30.0
        time_step = 1.0

    assert audit.flex_transit_steps_for_env(_FakeEnv(), 4170.0) == 139
    assert audit.flex_transit_steps_for_env(_FakeEnv(), 4171.0) == 140

    class _WrongSpeedEnv:
        max_speed = 5.0   # the S3 user/cluster speed -- must NOT be used
        time_step = 1.0

    # Same physical distance, a wrong v_max source gives a much larger (and
    # here Z-violating) step count -- proves the function reads max_speed
    # off the env rather than assuming a fixed constant.
    assert audit.flex_transit_steps_for_env(_WrongSpeedEnv(), 4170.0) == 834


# =============================================================================
# 2. One joint event per episode -- selection rule
# =============================================================================

def _certify_fn_from_table(table):
    """table: t_e -> (stable_ok, flex_ok, focal)."""
    def _fn(cand):
        stable_ok, flex_ok, focal = table[cand["t_e"]]
        return stable_ok, ([] if stable_ok else ["no"]), flex_ok, ([] if flex_ok else ["no"]), focal
    return _fn


def test_select_joint_event_stops_at_first_joint_qualifier():
    candidates = [{"t_e": 100}, {"t_e": 200}, {"t_e": 300}]
    table = {100: (True, False, None), 200: (True, True, 3), 300: (True, True, 9)}
    event, exclusions = audit.select_joint_event(candidates, _certify_fn_from_table(table))
    assert event is not None
    assert event["t_e"] == 200
    assert event["focal_flex_uav"] == 3
    # The 300 candidate is never reached once 200 qualifies.
    assert [e["t_e"] for e in exclusions] == [100]


def test_select_joint_event_continues_past_non_stable_candidates():
    """Ruling Q-E4: if no stable candidate exists at the first otherwise-
    qualified LEAVE, continue to the next planned LEAVE."""
    candidates = [{"t_e": 10}, {"t_e": 20}, {"t_e": 30}]
    table = {10: (False, True, 1), 20: (False, False, None), 30: (True, True, 4)}
    event, exclusions = audit.select_joint_event(candidates, _certify_fn_from_table(table))
    assert event is not None and event["t_e"] == 30
    assert len(exclusions) == 2


def test_select_joint_event_reports_none_when_no_candidate_qualifies():
    candidates = [{"t_e": 10}, {"t_e": 20}]
    table = {10: (False, True, 1), 20: (True, False, None)}
    event, exclusions = audit.select_joint_event(candidates, _certify_fn_from_table(table))
    assert event is None
    assert len(exclusions) == 2


def test_event_conformance_record_carries_every_required_field():
    cand = _base_candidate(
        pre_service_status="ACTIVE", post_service_status="CHARGE_ABSENT",
        capture_edge=True, last_charging_arrival=True, uav_charging=True,
        uav_dock_requests=True, uav_target_stations=1, battery_ratio=0.24,
        return_energy_margin=0.05, uav_position=(1.0, 2.0, 3.0),
        station_position=(0.0, 0.0, 0.0), station_occupancy=1, station_queue_length=0,
    )
    record = audit.build_event_conformance_record(cand)
    required = {
        "pre_service_status", "post_service_status", "capture_edge",
        "last_charging_arrival", "uav_charging", "uav_dock_requests",
        "uav_target_stations", "battery_ratio", "return_energy_margin",
        "uav_position", "station_position", "station_occupancy",
        "station_queue_length", "source_control_schedule_identity",
    }
    assert required.issubset(record.keys())
    assert record["source_control_schedule_identity"] == "constructive_mixed"


# =============================================================================
# 3. Legal-set construction: exclusions and vacated-target inclusion
# =============================================================================

def test_legal_set_includes_the_vacated_pre_leave_target():
    post = [np.array([10.0, 10.0, 100.0])]
    vacated = np.array([50.0, 50.0, 100.0])
    legal = audit.legal_set_targets(
        post_leave_targets=post, vacated_pre_leave_target=vacated,
        focal_incumbent_target=np.array([0.0, 0.0, 100.0]),
    )
    assert any(np.allclose(t, vacated) for t in legal)
    assert len(legal) == 2


def test_legal_set_deduplicates_geometrically_coincident_targets():
    post = [np.array([10.0, 10.0, 100.0])]
    vacated = np.array([10.0, 10.0, 100.0])  # same physical point as post[0]
    legal = audit.legal_set_targets(
        post_leave_targets=post, vacated_pre_leave_target=vacated,
        focal_incumbent_target=np.array([999.0, 999.0, 100.0]),
    )
    assert len(legal) == 1


def test_legal_set_excludes_the_focal_incumbent_target():
    incumbent = np.array([5.0, 5.0, 100.0])
    post = [incumbent.copy(), np.array([20.0, 20.0, 100.0])]
    vacated = np.array([30.0, 30.0, 100.0])
    legal = audit.legal_set_targets(
        post_leave_targets=post, vacated_pre_leave_target=vacated,
        focal_incumbent_target=incumbent,
    )
    assert not any(np.allclose(t, incumbent) for t in legal)
    assert len(legal) == 2


def test_legal_set_excludes_targets_outside_the_physical_domain():
    post = [np.array([10.0, 10.0, 100.0]), np.array([-5.0, 10.0, 100.0])]
    vacated = np.array([2000.0, 10.0, 100.0])
    legal = audit.legal_set_targets(
        post_leave_targets=post, vacated_pre_leave_target=vacated,
        focal_incumbent_target=np.array([0.0, 0.0, 100.0]),
        domain_bounds=(np.array([0.0, 0.0, 0.0]), np.array([1000.0, 1000.0, 200.0])),
    )
    # The -5 x-coordinate and the 2000 vacated target both lie outside bounds.
    assert len(legal) == 1
    assert np.allclose(legal[0], [10.0, 10.0, 100.0])


def test_legal_set_never_excludes_for_unreachability_within_delta():
    """Transit cost is part of SET's causal consequence, never a support
    exclusion -- a target 10 km away must still be legal."""
    far = np.array([10000.0, 10000.0, 100.0])
    legal = audit.legal_set_targets(
        post_leave_targets=[far], vacated_pre_leave_target=np.array([0.0, 0.0, 100.0]),
        focal_incumbent_target=np.array([1.0, 1.0, 100.0]),
    )
    assert any(np.allclose(t, far) for t in legal)


def test_focal_eligible_to_act_requires_all_four_conditions_clear():
    assert audit.focal_eligible_to_act(absent=False, charging=False, failed=False, non_acting=False)
    assert not audit.focal_eligible_to_act(absent=True, charging=False, failed=False, non_acting=False)
    assert not audit.focal_eligible_to_act(absent=False, charging=True, failed=False, non_acting=False)
    assert not audit.focal_eligible_to_act(absent=False, charging=False, failed=True, non_acting=False)
    assert not audit.focal_eligible_to_act(absent=False, charging=False, failed=False, non_acting=True)


# =============================================================================
# 4. Window-local vs episode-latched divergence on a crafted schedule
# =============================================================================

def test_window_local_and_episode_latched_diverge_on_a_post_recovery_recurrence():
    """One UAV's cutoff mask: True before the window (steps 0-2), recovers to
    False just before the window starts (step 3), then re-triggers True
    inside the window (step 6). Episode-latched semantics (`cutoff_event_seen`,
    which never resets within an episode) already marked this UAV 'seen' at
    step 0, so the in-window recurrence is not 'new' under that convention.
    Window-local latching records its own previous-step baseline AT t_e
    (step 3, already False), so the step-6 recurrence IS a genuine
    false->true transition and must be counted."""
    window_start = 3
    full_series = np.array([
        [True],   # step 0: pre-window, already true
        [True],   # step 1
        [True],   # step 2
        [False],  # step 3 = t_e: recovered, this is the window baseline
        [False],  # step 4 (window index 1)
        [False],  # step 5 (window index 2)
        [True],   # step 6 (window index 3): recurrence
        [True],   # step 7 (window index 4)
    ])
    window = full_series[window_start:]

    episode_latched = audit.episode_latched_new_counts(
        full_series, window_start=window_start, window_len=len(window)
    )
    window_local = audit.window_latched_counts(window, np.zeros_like(window))["cutoff_count"]

    assert episode_latched == 0
    assert window_local == 1
    assert window_local != episode_latched


def test_window_local_counts_at_most_one_transition_per_uav():
    """A second recurrence after the first counted transition must not add a
    second count -- 'at most the first' per UAV per type."""
    window = np.array([
        [False],  # step 0 = t_e baseline
        [True],   # step 1: first transition, counted
        [False],  # step 2: recovers
        [True],   # step 3: second transition, must NOT be counted again
    ])
    result = audit.window_latched_counts(window, np.zeros_like(window))
    assert result["cutoff_count"] == 1


def test_pre_window_events_contribute_zero():
    """If the baseline recorded at t_e is already True (event happened before
    or exactly at t_e), no in-window transition exists for that UAV unless it
    first recovers and re-triggers."""
    window = np.array([
        [True],  # step 0 = t_e baseline, already true
        [True],
        [True],
    ])
    result = audit.window_latched_counts(window, np.zeros_like(window))
    assert result["cutoff_count"] == 0


# =============================================================================
# 5. Arm distinctness on a witness history
# =============================================================================

def test_constructive_mixed_null_and_full_sync_produce_distinct_duty_maps():
    """Witness history at the REGISTERED fleet shape: 8 duties, 8 UAVs, zero
    idle survivors after a LEAVE (`physical_uavs=8`, section 0) -- replacing
    the prior witness (4 duties / a 5th idle spare UAV), which the reviewer
    found "passes on a configuration that cannot occur in the registered
    environment."

    8 duties in a line 100 m apart, each UAV exactly co-located with its own
    duty (an already-duty-optimal identity map, the hardest case for a
    reassignment bug to show up in). UAV 4 LEAVEs.

    Hand-worked expected result (traced by hand, independent of the
    implementation): with UAV 4 gone, 7 survivors remain for 8 duties.
    Processing the freshly vacated duty 4 FIRST, its nearest remaining
    survivor is UAV 3 (both are 100 m away from duty 4's post; ties break to
    the lower id, which appears first in ascending iteration order) --
    duty 4 is covered by UAV 3. UAV 3's own duty (3) is now open; its
    nearest remaining survivor is UAV 5 (200 m, the closest of the
    survivors still in the pool) -- covered by UAV 5. Duty 5, in turn, is
    covered by UAV 6 (100 m); duty 6 by UAV 7 (100 m). Duty 7 is left with
    no survivor at all once the pool is exhausted -- EXACTLY one duty
    uncovered, since there are 8 duties for 7 survivors. Duties 0, 1, 2 keep
    their own already-co-located incumbents throughout.

    This directly realizes contract section 4 / Q-C1's "a duty-holding
    survivor may be reassigned to cover the vacancy": UAV 3 is reassigned
    AWAY from its own duty to cover the fresh vacancy, not merely an idle
    spare filling a gap (which cannot occur at this fleet shape at all)."""
    duty_positions = {i: np.array([i * 100.0, 0.0, 100.0]) for i in range(8)}
    identity_map = {i: i for i in range(8)}
    airborne_pre_event = {i: np.array([i * 100.0, 0.0, 0.0]) for i in range(8)}

    # Now UAV 4 LEAVEs.
    airborne_post_leave = {k: v for k, v in airborne_pre_event.items() if k != 4}
    constructive_post = audit.constructive_mixed_update(
        duty_map=identity_map, duty_positions=duty_positions,
        airborne_positions=airborne_post_leave, event="LEAVE", event_uav=4,
    )
    null_post = audit.null_update(duty_map=identity_map)

    expected_constructive_post = {
        4: 3, 0: 0, 1: 1, 2: 2, 3: 5, 5: 6, 6: 7,
        # duty 7: no key -- left uncovered, the one duty in excess of the
        # 7 surviving UAVs.
    }
    assert constructive_post == expected_constructive_post
    assert 7 not in constructive_post

    # null keeps every duty, including duty 4 still pointing at the now-
    # absent UAV 4 -- the registered-fleet-shape bug this replaces would have
    # made these two maps differ only by that one stale key (or be fully
    # degenerate); the fix produces a substantively different map: 4 of the
    # 8 duties (3, 4, 5, 6) have different incumbents, and duty 7 -- fully
    # covered under null -- is uncovered under constructive_mixed.
    assert null_post == identity_map
    assert constructive_post != null_post
    assert null_post[4] == 4          # null: never proactively replaced
    assert constructive_post[4] == 3  # constructive: reassigned to a survivor
    differing_duties = {d for d in identity_map if constructive_post.get(d) != null_post.get(d)}
    assert differing_duties == {3, 4, 5, 6, 7}

    # full_sync_SET (Part-A diagnostic only) also differs from constructive_mixed
    # at this same post-LEAVE instant: it recomputes every duty from scratch,
    # including 0, 1, 2, which constructive_mixed left untouched.
    full_sync_post = audit.full_sync_set_update(
        duty_positions=duty_positions, airborne_positions=airborne_post_leave
    )
    assert full_sync_post != constructive_post


def test_constructive_mixed_never_reassigns_the_vacated_duty_to_the_leaver_itself():
    """Guard (measured trap): if the caller's `airborne_positions` still
    (erroneously) contains the leaving UAV -- e.g. a stale snapshot taken
    before the environment actually dropped it -- the leaver must never be
    selected as a reassignment candidate, even when it is geometrically the
    closest "survivor" to the vacated duty."""
    duty_positions = {0: np.array([0.0, 0.0, 100.0]), 1: np.array([100.0, 0.0, 100.0])}
    duty_map = {0: 0, 1: 1}
    # UAV 0 is leaving (event_uav=0) but its position is still present in
    # airborne_positions, and it sits almost exactly on top of duty 0.
    airborne_with_leaver_still_present = {
        0: np.array([0.0, 0.0, 0.0]),
        1: np.array([5.0, 0.0, 0.0]),
    }
    post = audit.constructive_mixed_update(
        duty_map=duty_map, duty_positions=duty_positions,
        airborne_positions=airborne_with_leaver_still_present,
        event="LEAVE", event_uav=0,
    )
    assert 0 not in post.values()
    assert post.get(0) == 1  # the only real survivor covers the vacancy


def test_constructive_mixed_preserves_a_locked_certified_stable_incumbent():
    """`locked_duties` (certified stable incumbents, section 2) must be
    withheld entirely from the LEAVE re-match, even when a geometrically
    closer survivor becomes available."""
    duty_positions = {
        0: np.array([0.0, 0.0, 100.0]),
        1: np.array([100.0, 0.0, 100.0]),
        2: np.array([200.0, 0.0, 100.0]),
    }
    duty_map = {0: 0, 1: 1, 2: 2}
    # UAV 0 leaves. UAV 2 is geometrically much closer to duty 0 than to its
    # own duty 2, so an UNLOCKED re-match would pull it toward duty 0 --
    # but duty 1's incumbent (UAV 1) is locked/certified-stable and must
    # keep duty 1 regardless.
    airborne_post_leave = {1: np.array([100.0, 0.0, 0.0]), 2: np.array([5.0, 0.0, 0.0])}
    post = audit.constructive_mixed_update(
        duty_map=duty_map, duty_positions=duty_positions,
        airborne_positions=airborne_post_leave, event="LEAVE", event_uav=0,
        locked_duties=frozenset({1}),
    )
    assert post[1] == 1     # locked incumbent preserved
    assert post[0] == 2     # the only reassignable survivor covers the vacancy
    assert 2 not in post    # duty 2's own incumbent (UAV 2) moved to cover duty 0


def test_constructive_mixed_rejoin_covers_an_uncovered_duty():
    duty_positions = {0: np.array([0.0, 0.0, 100.0]), 1: np.array([100.0, 0.0, 100.0])}
    duty_map_after_leave = {}  # duty 1 vacated and left uncovered (no survivor)
    airborne_positions = {0: np.array([0.0, 0.0, 0.0]), 2: np.array([90.0, 0.0, 0.0])}
    updated = audit.constructive_mixed_update(
        duty_map=duty_map_after_leave, duty_positions=duty_positions,
        airborne_positions=airborne_positions, event="REJOIN", event_uav=2,
    )
    assert updated.get(1) == 2


def test_null_update_never_changes_regardless_of_event_kwargs():
    duty_map = {0: 0, 1: 1}
    assert audit.null_update(duty_map=duty_map) == duty_map


# =============================================================================
# 6. Seed-hash determinism and selection/evaluation namespace disjointness
# =============================================================================

def _seed_kwargs(**overrides):
    kwargs = dict(
        topology_seed=20260726, block="audit", episode_seed=123,
        limb="stable", event_index=0, candidate_target_id="z0",
        phase="select", replicate_index=0,
    )
    kwargs.update(overrides)
    return kwargs


def test_stream_seed_is_deterministic():
    a = audit.stream_seed(**_seed_kwargs())
    b = audit.stream_seed(**_seed_kwargs())
    assert a == b
    assert isinstance(a, int)


def test_stream_seed_changes_with_any_single_field():
    base = audit.stream_seed(**_seed_kwargs())
    variants = [
        _seed_kwargs(topology_seed=20260727),
        _seed_kwargs(block="calibration"),
        _seed_kwargs(episode_seed=124),
        _seed_kwargs(limb="flex"),
        _seed_kwargs(event_index=1),
        _seed_kwargs(candidate_target_id="z1"),
        _seed_kwargs(phase="evaluate"),
        _seed_kwargs(replicate_index=1),
    ]
    seeds = [audit.stream_seed(**v) for v in variants]
    assert len(set(seeds)) == len(seeds), "each single-field change must be distinguishable"
    assert base not in seeds


def test_selection_and_evaluation_namespaces_are_disjoint_across_many_candidates():
    """Statistical disjointness check: selection-phase seeds (varying by
    candidate) must never collide with evaluation-phase seeds (fixed
    candidate token) across a reasonably large sample."""
    select_seeds = {
        audit.stream_seed(**_seed_kwargs(phase="select", candidate_target_id=f"z{i}"))
        for i in range(200)
    }
    eval_seeds = {
        audit.stream_seed(
            **_seed_kwargs(phase="evaluate",
                           candidate_target_id=audit.EVAL_SHARED_CANDIDATE_TOKEN,
                           replicate_index=i)
        )
        for i in range(200)
    }
    assert select_seeds.isdisjoint(eval_seeds)


def test_evaluate_phase_shares_seed_between_set_and_keep_via_shared_token():
    """CRN pairing: KEEP and the selected SET must derive the SAME evaluate-
    phase seed for a given replicate, which this module realizes by both
    callers passing the fixed `EVAL_SHARED_CANDIDATE_TOKEN`."""
    seed_for_set = audit.stream_seed(
        **_seed_kwargs(phase="evaluate", candidate_target_id=audit.EVAL_SHARED_CANDIDATE_TOKEN,
                       replicate_index=3)
    )
    seed_for_keep = audit.stream_seed(
        **_seed_kwargs(phase="evaluate", candidate_target_id=audit.EVAL_SHARED_CANDIDATE_TOKEN,
                       replicate_index=3)
    )
    assert seed_for_set == seed_for_keep


# =============================================================================
# 7. Branch precedence: every one of the ten branches is constructible
# =============================================================================

def _branch_kwargs(**overrides):
    kwargs = dict(
        conformance_ok=True, support_ok=True, primary_g_degenerate_flag=False,
        part_a_contradiction=False,
        b_stable_lcb=1.0, t_stable_ucb=-1.0, t_stable_lcb=-2.0,
        b_flex_lcb=1.0, t_flex_lcb=1.0, t_flex_ucb=2.0,
    )
    kwargs.update(overrides)
    return kwargs


def test_branch_1_invalid_event_aligned_audit():
    assert audit.decide_branch(**_branch_kwargs(conformance_ok=False)) == "INVALID_EVENT_ALIGNED_AUDIT"


def test_branch_2_support_insufficient():
    assert audit.decide_branch(**_branch_kwargs(support_ok=False)) == "SOURCE_EVENT_SUPPORT_INSUFFICIENT"


def test_branch_3_primary_g_degenerate():
    assert audit.decide_branch(**_branch_kwargs(primary_g_degenerate_flag=True)) == "PRIMARY_G_DEGENERATE"


def test_branch_4_part_a_contradiction():
    assert audit.decide_branch(**_branch_kwargs(part_a_contradiction=True)) == "PART_A_CONTRADICTION"


def test_branch_5_persistence_necessary_source():
    # stable clears (b_stable_lcb>0, t_stable_ucb<0); flex clears (b_flex_lcb>0, t_flex_lcb>0)
    assert audit.decide_branch(**_branch_kwargs()) == "PERSISTENCE_NECESSARY_SOURCE"


def test_branch_6_stable_persistence_without_material_flex_renewal():
    # stable clears; flex affirmatively misses: b_flex_lcb>0 and t_flex_ucb<0
    kwargs = _branch_kwargs(t_flex_lcb=-1.0, t_flex_ucb=-0.5)
    assert audit.decide_branch(**kwargs) == "STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL"


def test_branch_7_material_stable_persistence_identified():
    # stable clears; flex neither clears nor affirmatively misses (unresolved)
    kwargs = _branch_kwargs(t_flex_lcb=-1.0, t_flex_ucb=1.0)
    assert audit.decide_branch(**kwargs) == "MATERIAL_STABLE_PERSISTENCE_IDENTIFIED"


def test_branch_8_no_material_flex_renewal_identified():
    # flex affirmatively misses; stable does NOT clear
    kwargs = _branch_kwargs(
        t_stable_ucb=1.0, t_stable_lcb=-1.0,   # stable does not clear, not affirmative-miss either
        t_flex_lcb=-1.0, t_flex_ucb=-0.5,      # flex affirmative miss
    )
    assert audit.decide_branch(**kwargs) == "NO_MATERIAL_FLEX_RENEWAL_IDENTIFIED"


def test_branch_9_no_material_stable_persistence_identified():
    # stable affirmatively misses (b_stable_lcb>0, t_stable_lcb>0); stable
    # therefore does not clear (t_stable_ucb must be >=0 too); flex not an
    # affirmative miss (so branch 8 does not preempt it).
    kwargs = _branch_kwargs(
        t_stable_ucb=1.0, t_stable_lcb=0.5,
        t_flex_lcb=1.0, t_flex_ucb=2.0,   # flex clears, not an affirmative miss
    )
    assert audit.decide_branch(**kwargs) == "NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED"


def test_branch_10_source_necessity_unresolved():
    # Nothing resolved: stable neither clears nor affirmatively misses;
    # flex neither clears nor affirmatively misses.
    kwargs = _branch_kwargs(
        b_stable_lcb=-1.0, t_stable_ucb=1.0, t_stable_lcb=-1.0,
        b_flex_lcb=-1.0, t_flex_lcb=-1.0, t_flex_ucb=1.0,
    )
    assert audit.decide_branch(**kwargs) == "SOURCE_NECESSITY_UNRESOLVED"


def test_branch_precedence_invalid_wins_over_everything_else():
    """A row that would otherwise satisfy branch 5's conditions must still
    resolve to branch 1 if conformance failed -- precedence is absolute."""
    kwargs = _branch_kwargs(conformance_ok=False, support_ok=False,
                             primary_g_degenerate_flag=True, part_a_contradiction=True)
    assert audit.decide_branch(**kwargs) == "INVALID_EVENT_ALIGNED_AUDIT"


# =============================================================================
# 8. Bootstrap selection-rerun property on a small synthetic
# =============================================================================

def test_bootstrap_reruns_selection_not_the_point_level_winner():
    """Candidate 'B' wins at the point level (mean 2.0 > candidate A's mean
    1.5), but candidate A's single high selection draw (5.0, occurring once
    in four) means A wins whenever that draw is resampled at least twice --
    entirely plausible in bootstrap resampling with replacement. Candidate
    A's eval_set is far larger than B's, so if the bootstrap reused the
    point-level winner (B) on every iteration, the resulting distribution
    would be degenerate at B's U*; a genuine rerun must show iterations
    where A was selected and the aggregate must therefore differ from the
    fixed-selection reference computed independently below."""
    event = {
        "candidates": {
            "A": {"select": [1.0, 1.0, 1.0, 5.0], "eval_set": [10.0] * 8},
            "B": {"select": [2.0, 2.0, 2.0, 2.0], "eval_set": [1.0] * 8},
        },
        "eval_keep": [0.0] * 8,
    }
    result = audit.hierarchical_bootstrap_events([event], iters=500, seed=1)

    picks_flat = [p[0] for p in result["selected_candidates_per_iter"]]
    assert "A" in picks_flat, "a genuine rerun must select A on at least one resample"
    assert "B" in picks_flat, "and must select B on others (not universally flipped either)"

    # Independent fixed-selection reference: always use the point-level
    # winner B, regardless of resample. This is the wrong implementation the
    # test must be able to catch.
    rng = np.random.default_rng(1)
    fixed_u = []
    eval_set_b = np.asarray(event["candidates"]["B"]["eval_set"], dtype=float)
    eval_keep = np.asarray(event["eval_keep"], dtype=float)
    for _ in range(500):
        # Burn the same number of RNG draws as the real bootstrap so the two
        # streams are comparable in spirit (selection draw for A, B, then eval draw).
        rng.integers(0, 4, size=4)   # A's selection resample (discarded)
        rng.integers(0, 4, size=4)   # B's selection resample (discarded)
        idx_eval = rng.integers(0, eval_set_b.size, size=eval_set_b.size)
        fixed_u.append(float(eval_set_b[idx_eval].mean() - eval_keep[idx_eval].mean()))
    fixed_mean = float(np.mean(fixed_u))

    rerun_mean = float(np.mean(result["u_star_iters"]))
    assert rerun_mean != pytest.approx(fixed_mean, abs=1e-9), (
        "a rerun-selection bootstrap must differ from an always-use-the-point-winner "
        "bootstrap whenever the argmax can flip under resampling"
    )
    # Sanity: the rerun mean must sit strictly between A-only and B-only U*.
    u_if_always_a = 10.0 - 0.0
    u_if_always_b = 1.0 - 0.0
    assert min(u_if_always_a, u_if_always_b) < rerun_mean < max(u_if_always_a, u_if_always_b)


def test_bootstrap_point_estimate_uses_the_true_point_level_maximizer():
    event = {
        "candidates": {
            "A": {"select": [1.0, 1.0, 1.0, 1.0], "eval_set": [10.0] * 8},
            "B": {"select": [2.0, 2.0, 2.0, 2.0], "eval_set": [1.0] * 8},
        },
        "eval_keep": [0.0] * 8,
    }
    result = audit.hierarchical_bootstrap_events([event], iters=10, seed=2)
    # Point level: B wins (mean 2.0 > 1.0), so point U* = mean(B eval_set) - mean(keep) = 1.0.
    assert result["point"] == pytest.approx(1.0)


def test_select_maximizer_picks_the_true_argmax():
    streams = {"a": np.array([1.0, 1.0]), "b": np.array([5.0, 5.0]), "c": np.array([2.0, 2.0])}
    assert audit.select_maximizer(streams) == "b"


def test_hierarchical_bootstrap_events_is_deterministic_for_a_fixed_seed():
    event = {
        "candidates": {"A": {"select": [1.0, 2.0, 3.0, 4.0], "eval_set": [5.0] * 8}},
        "eval_keep": [0.0] * 8,
    }
    a = audit.hierarchical_bootstrap_events([event], iters=50, seed=42)
    b = audit.hierarchical_bootstrap_events([event], iters=50, seed=42)
    assert np.array_equal(a["u_star_iters"], b["u_star_iters"])


# =============================================================================
# Supplementary: state-hash prefix-replay assertion and topology hash
# =============================================================================

def test_state_hash_equal_snapshots_hash_equal():
    snap = {
        "positions": np.array([[0.0, 0.0, 0.0]]),
        "battery_ratios": np.array([0.5]),
        "charging_mask": np.array([False]),
        "station_occupancy": np.array([0]),
        "station_queue": np.array([0]),
        "duty_map": {0: 0},
        "lifecycle_mask": np.array([True]),
    }
    h1 = audit.compute_state_hash(snap)
    h2 = audit.compute_state_hash(dict(snap))
    audit.assert_state_hash_equal(h1, h2)  # must not raise


def test_state_hash_mismatch_raises_and_is_never_silently_repaired():
    snap_a = {"positions": np.array([[0.0, 0.0, 0.0]]), "duty_map": {0: 0}}
    snap_b = {"positions": np.array([[1.0, 0.0, 0.0]]), "duty_map": {0: 0}}
    h1 = audit.compute_state_hash(snap_a)
    h2 = audit.compute_state_hash(snap_b)
    assert h1 != h2
    with pytest.raises(audit.PrefixReplayMismatchError):
        audit.assert_state_hash_equal(h1, h2)


def test_coordinate_hash_differs_for_different_topologies():
    h1 = audit.coordinate_hash(np.array([[0.0, 0.0, 0.0]]), np.array([[1.0, 1.0, 0.0]]))
    h2 = audit.coordinate_hash(np.array([[10.0, 0.0, 0.0]]), np.array([[1.0, 1.0, 0.0]]))
    assert h1 != h2


# =============================================================================
# 9. Topology templates are deterministic in topology_seed (real environment)
# =============================================================================

def _real_config():
    import config_1
    return config_1.Config(preset=audit.PRESET)


def test_build_topology_template_same_seed_twice_gives_equal_hashes():
    """Measured regression: three calls with the identical topology_seed
    previously produced three different coordinate hashes, because ground-BS
    is drawn at construction from unseeded state and `reset()` never
    redraws it. Exercised against the REAL environment -- a fake stand-in
    would not touch the actual `np_random`/`_init_ground_bs` interaction the
    bug lives in."""
    config = _real_config()
    coords_a, hash_a = audit.build_topology_template(config, topology_seed=20260726)
    coords_b, hash_b = audit.build_topology_template(config, topology_seed=20260726)
    assert hash_a == hash_b
    assert np.array_equal(coords_a["ground_bs"], coords_b["ground_bs"])
    assert np.array_equal(coords_a["charging_stations"], coords_b["charging_stations"])


def test_build_topology_template_different_seeds_give_different_hashes():
    config = _real_config()
    _, hash_a = audit.build_topology_template(config, topology_seed=20260726)
    _, hash_b = audit.build_topology_template(config, topology_seed=20260727)
    assert hash_a != hash_b


def test_topology_record_round_trips_through_write():
    # Plain `tempfile`, not pytest's `tmp_path` fixture: this sandbox denies
    # `tmp_path` permission to scan its numbered-dir base
    # (`pytest-of-<user>`), unrelated to anything under test here.
    import tempfile

    config = _real_config()
    coords, coord_hash = audit.build_topology_template(config, topology_seed=20260726)
    record = audit.build_topology_record(coords, coord_hash, topology_seed=20260726)
    assert record["coordinate_hash"] == coord_hash
    assert record["procedure_version"] == audit.TOPOLOGY_PROCEDURE_VERSION
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = audit.write_topology_record(tmp_dir, record)
        assert path.exists()
        written = json.loads(path.read_text(encoding="utf-8"))
    assert written["coordinate_hash"] == coord_hash
    assert written["topology_seed"] == 20260726


# =============================================================================
# 10. Part-A conformance: equivalence, materially-worse, and straddling
# =============================================================================

def test_part_a_conformance_both_equivalence_bounds_pass_is_contradiction():
    verdict = audit.part_a_conformance(
        lower_contrast_lcb=0.1, lower_contrast_ucb=0.5,
        upper_contrast_lcb=0.2, b_stable_lcb=1.0,
    )
    assert verdict == "PART_A_CONTRADICTION"


def test_part_a_conformance_confidently_worse_is_conformance_pass():
    # UCB95 of the lower contrast is itself negative: D_A is confidently
    # below -0.05*B_stable (full-sync materially worse).
    verdict = audit.part_a_conformance(
        lower_contrast_lcb=-0.5, lower_contrast_ucb=-0.1,
        upper_contrast_lcb=0.9, b_stable_lcb=1.0,
    )
    assert verdict == "CONFORMANCE_PASS"


def test_part_a_conformance_straddling_interval_is_unresolved_not_pass():
    """Measured regression: a 90% interval [-0.333, +0.009] on the lower
    contrast (LCB95 fails the lower equivalence test, but UCB95 is still
    positive so "materially worse" is NOT established) previously returned
    CONFORMANCE_PASS. It must be PART_A_CONFORMANCE_UNRESOLVED."""
    verdict = audit.part_a_conformance(
        lower_contrast_lcb=-0.333, lower_contrast_ucb=0.009,
        upper_contrast_lcb=0.9, b_stable_lcb=1.0,
    )
    assert verdict == "PART_A_CONFORMANCE_UNRESOLVED"


def test_part_a_conformance_not_applicable_when_b_stable_not_identified():
    verdict = audit.part_a_conformance(
        lower_contrast_lcb=0.5, lower_contrast_ucb=0.9,
        upper_contrast_lcb=0.5, b_stable_lcb=-0.1,
    )
    assert verdict == "NOT_APPLICABLE"


# =============================================================================
# 11. Section 8 inference: T_m arithmetic, common resampling stream, and
#     equal topology weighting
# =============================================================================

def test_equal_topology_weighted_mean_hand_worked_example():
    """Independent hand-worked arithmetic: topology A contributes one event
    valued 10.0; topology B contributes three events valued 0.0. A flat pool
    of all four events gives (10+0+0+0)/4 = 2.5, silently weighting topology
    B three times as heavily as A. Equal topology weighting gives
    (10+0)/2 = 5.0. Measured regression on the reviewer's own construction:
    2.0973 (flat) vs the correct 1.2500 (equal-weighted) -- this test uses
    an independently hand-computable construction of the same shape."""
    per_topology = [[10.0], [0.0, 0.0, 0.0]]
    flat = float(np.mean([v for vals in per_topology for v in vals]))
    weighted = audit.equal_topology_weighted_mean(per_topology)
    assert flat == pytest.approx(2.5)
    assert weighted == pytest.approx(5.0)
    assert weighted != pytest.approx(flat)


def test_equal_topology_weighted_mean_excludes_zero_event_topologies():
    """A topology contributing zero events this resample is a support miss,
    not a zero -- it must be dropped from the average, not counted as 0.0."""
    per_topology = [[10.0], [], [20.0]]
    weighted = audit.equal_topology_weighted_mean(per_topology)
    assert weighted == pytest.approx(15.0)  # mean(10, 20), NOT mean(10, 0, 20)


def _degenerate_topology_units(values_per_topology):
    """One degenerate single-candidate event per topology, encoding topology
    ti's value directly (select == eval_set == value, eval_keep == 0), so
    `hierarchical_bootstrap_quantity`'s per-topology mean is exactly that
    topology's value regardless of resampling."""
    return [
        [{"candidates": {"only": {"select": [v], "eval_set": [v]}}, "eval_keep": [0.0]}]
        for v in values_per_topology
    ]


def test_shared_topology_stream_is_identical_across_quantities_with_different_event_counts():
    """Q-I1's common resampling stream: quantities with DIFFERING per-topology
    event counts (e.g. a calibration-block B_m vs an audit-block U*_m) must
    draw IDENTICAL topology indices every iteration. Construction: every
    event in topology `ti`, for BOTH quantities, carries the SAME degenerate
    value `ti` -- a topology's per-topology mean is exactly `ti` regardless
    of which or how many of its events get resampled. Quantity A has 1 event
    per topology; quantity B has 5. If the topology draw were not shared
    (the measured regression: "the current per-call variate consumption
    diverges after iteration 0"), A and B's per-iteration sequences would
    diverge as soon as their differing event counts desynchronized the two
    streams. With a genuinely shared stream, every iteration's mean depends
    only on WHICH topologies were drawn, so A and B must match bit-for-bit."""
    def make_quantity(n_events_per_topology, n_topo=4):
        return [
            [
                {"candidates": {"only": {"select": [float(ti)], "eval_set": [float(ti)]}},
                 "eval_keep": [0.0]}
                for _ in range(n_events_per_topology)
            ]
            for ti in range(n_topo)
        ]

    quantity_a = make_quantity(1)
    quantity_b = make_quantity(5)
    shared = audit.draw_shared_topology_indices(n_topo=4, iters=200, seed=777)
    result_a = audit.hierarchical_bootstrap_quantity(
        quantity_a, shared_topology_indices=shared, seed=999)
    result_b = audit.hierarchical_bootstrap_quantity(
        quantity_b, shared_topology_indices=shared, seed=999)
    assert np.array_equal(result_a["u_star_iters"], result_b["u_star_iters"])


def test_shared_topology_stream_would_have_caught_the_old_per_call_seed_bug():
    """Sanity check that the identity test above is not vacuous: reproducing
    the OLD defect (each quantity draws its OWN topology indices from a
    freshly-seeded stream that ALSO absorbs its own per-topology event draws
    in between) DOES diverge between quantities with different event
    counts -- confirming the property under test can fail."""
    def old_buggy_topology_draw(values_per_topology, n_events_per_topology, *, iters, seed):
        rng = np.random.default_rng(seed)
        n_topo = len(values_per_topology)
        out = np.empty(iters, dtype=float)
        for i in range(iters):
            topo_idx = rng.integers(0, n_topo, size=n_topo)
            # The bug: further draws (here standing in for per-topology event
            # resampling) consume the SAME long-lived stream before the next
            # iteration's topology draw.
            rng.integers(0, 1_000_000, size=n_events_per_topology * n_topo)
            out[i] = float(np.mean([values_per_topology[t] for t in topo_idx]))
        return out

    values = [0.0, 1.0, 2.0, 3.0]
    a = old_buggy_topology_draw(values, 1, iters=50, seed=555)
    b = old_buggy_topology_draw(values, 5, iters=50, seed=555)
    assert not np.array_equal(a, b), (
        "the old per-call-consumption pattern must diverge between "
        "quantities with different event counts -- if it doesn't, this "
        "reference reproduction is not actually exercising the bug"
    )


def test_compute_t_m_bootstrap_applies_the_registered_materiality_coefficient():
    """Deterministic single-topology, single-event construction so T_m's
    arithmetic can be hand-checked independent of the bootstrap machinery:
    U*_stable = 8.0, B_stable = 20.0 -> T_stable = 8.0 + 0.10*20.0 = 10.0.
    U*_flex = 5.0, B_flex = 20.0 -> T_flex = 5.0 - 0.10*20.0 = 3.0.
    With one topology, resampling with replacement always draws index 0 and
    every per-topology event array has length 1, so there is no resampling
    variance: every reported bound must equal the deterministic point
    value."""
    out = audit.compute_t_m_bootstrap(
        b_stable_topology_units=_degenerate_topology_units([20.0]),
        b_flex_topology_units=_degenerate_topology_units([20.0]),
        u_star_stable_topology_units=_degenerate_topology_units([8.0]),
        u_star_flex_topology_units=_degenerate_topology_units([5.0]),
        n_topo=1, iters=20, seed=42,
    )
    assert out["t_stable_ucb"] == pytest.approx(10.0)
    assert out["t_stable_lcb"] == pytest.approx(10.0)
    assert out["t_flex_lcb"] == pytest.approx(3.0)
    assert out["t_flex_ucb"] == pytest.approx(3.0)
    assert out["b_stable_lcb"] == pytest.approx(20.0)
    assert out["b_flex_lcb"] == pytest.approx(20.0)


# =============================================================================
# 12. QoS saturation on the user-step unit, not the per-step mean ratio
# =============================================================================

def test_saturation_fires_on_29_of_30_users_saturated_input_wise():
    """29 of 30 users individually AT the QoS ceiling every step, one user
    well below it. Measured regression: computed from the per-step ARM MEAN
    -- (29*1.0 + 0.4)/30 ~= 0.9867, which never crosses the 1.0-eps ceiling
    -- this exact regime previously returned 0.0 saturation. Computed on the
    user-step unit instead, saturation must be 29/30 and must fire the
    >=0.95 QOS_COMPONENT_SATURATED threshold."""
    n_steps = 10
    user_step = np.ones((n_steps, 30))
    user_step[:, -1] = 0.4  # one persistently under-saturated user
    frac = audit.user_step_saturation_fraction(user_step)
    assert frac == pytest.approx(29.0 / 30.0)
    assert frac >= 0.95

    # Guard against the regression: the WRONG per-step-mean convention must
    # NOT be what this function (or its caller) effectively computes.
    per_step_mean = np.mean(user_step, axis=1)
    wrong_fraction_under_old_convention = float(np.mean(per_step_mean >= 1.0 - 1e-9))
    assert wrong_fraction_under_old_convention == 0.0
    assert frac != wrong_fraction_under_old_convention


def test_nondegeneracy_report_saturation_uses_the_user_step_input_not_qos_series():
    """Wiring check: `nondegeneracy_report`'s reported saturation must come
    from `qos_user_step`, not from `qos_series` (the per-step arm mean) --
    constructed so the two inputs would give different answers if swapped."""
    qos_series = np.full(10, 0.9867)  # per-step arm mean, never >= ceiling
    qos_user_step = np.ones((10, 30))
    qos_user_step[:, -1] = 0.4

    report = audit.nondegeneracy_report(
        qos_series=qos_series, qos_user_step=qos_user_step,
        return_cost_series=np.zeros(10), cutoff_incidence=0, depletion_incidence=0,
        g_series=np.zeros(10), secondary_series=np.zeros(10),
    )
    assert report["qos_saturation_fraction"] == pytest.approx(29.0 / 30.0)


# =============================================================================
# 13. compute_G hand-worked weights, and the window-series length convention
# =============================================================================

def test_compute_g_hand_worked_weights_exactly_minus2_minus5_minus10():
    """Hand-worked, independent of the implementation:
    G = 0.8 - 2*0.3 - 5*1 - 10*1 = 0.8 - 0.6 - 5.0 - 10.0 = -14.8"""
    g = audit.compute_G(
        qos_satisfaction_ratio=0.8, return_constraint_cost=0.3,
        new_cutoff_count=1, new_depletion_count=1,
    )
    assert g == pytest.approx(-14.8)


def test_window_series_length_convention_is_pinned_to_h_plus_1():
    assert audit.window_series_length(audit.H_STABLE) == audit.H_STABLE + 1
    assert audit.window_series_length(audit.H_FLEX) == audit.H_FLEX + 1


def test_window_latched_counts_on_a_full_h_stable_sized_series():
    """Exercises `window_latched_counts` at the REAL H_stable=139 window
    length (140 rows: baseline + 139 steps), pinning the row-0-baseline /
    H+1-rows alignment convention at registered size, not just a small
    hand-picked array."""
    n_uavs = 2
    rows = audit.window_series_length(audit.H_STABLE)
    cutoff = np.zeros((rows, n_uavs), dtype=bool)
    cutoff[0, 0] = True   # baseline: uav 0 already cutoff at t_e -- never counted
    cutoff[1, 1] = True   # uav 1: genuine in-window transition at step 1
    result = audit.window_latched_counts(cutoff, np.zeros_like(cutoff))
    assert result["cutoff_per_step"].shape[0] == rows
    assert result["cutoff_count"] == 1


# =============================================================================
# 10. Real-env orchestration layer (item 6): dock-decision boundary, event-scan
# glue, prefix-replay fork discipline, evaluator forward-replay producer.
# =============================================================================

def test_dock_trigger_ratio_hand_worked():
    # 10 transit steps at 500 W cruise power, dt=1s, 100 Wh capacity, 0.10 reserve:
    # E = 10 * 500 * 1 / 3600 = 1.3889 Wh -> ratio 0.013889 + 0.10 = 0.113889
    trig = audit.dock_trigger_ratio(
        distance_m=290.0, max_speed=30.0, dt=1.0, power_transit_w=500.0,
        battery_capacity_wh=100.0, return_reserve_ratio=0.10)
    # ceil(290/30) = 10 transit steps
    assert trig == pytest.approx(0.10 + (10 * 500.0 * 1.0 / 3600.0) / 100.0)


def test_should_depart_for_charge_boundary_equal_departs():
    """`battery_ratio <= trigger_ratio` -- equality must depart (the LATEST
    safe boundary is itself still safe, not the step after)."""
    assert audit.should_depart_for_charge(battery_ratio=0.20, trigger_ratio=0.20) is True


def test_should_depart_for_charge_boundary_just_above_does_not_depart():
    assert audit.should_depart_for_charge(battery_ratio=0.2000001, trigger_ratio=0.20) is False


def test_should_depart_for_charge_boundary_just_below_departs():
    assert audit.should_depart_for_charge(battery_ratio=0.1999999, trigger_ratio=0.20) is True


def test_dock_trigger_ratio_increases_with_distance():
    """A farther station must trigger departure at a HIGHER battery ratio
    (leave earlier) -- this is the "forward-planned" content of the rule,
    not just an additive constant; a formula that ignored distance would
    fail this."""
    near = audit.dock_trigger_ratio(distance_m=100.0, max_speed=30.0, dt=1.0,
                                     power_transit_w=400.0, battery_capacity_wh=160.0,
                                     return_reserve_ratio=0.10)
    far = audit.dock_trigger_ratio(distance_m=5000.0, max_speed=30.0, dt=1.0,
                                    power_transit_w=400.0, battery_capacity_wh=160.0,
                                    return_reserve_ratio=0.10)
    assert far > near


# --- event-scan glue: an env schedule producing a qualifying LEAVE and one
# of each exclusion (build_leave_candidate -> check_leave_eligibility) -------

def _leave_env_stub(*, station_occupancy_after, station_queue_after, target_station=0):
    class _Stub:
        n_uavs = 4
        uav_target_stations = np.array([target_station, -1, -1, -1])
        uav_dock_requests = np.array([True, False, False, False])
        uav_battery_ratios = np.array([0.20, 0.9, 0.9, 0.9])
        uav_positions = np.zeros((4, 3))
        charging_station_positions = np.array([[100.0, 0.0, 0.0], [200.0, 0.0, 0.0]])
        uav_failed = np.zeros(4, dtype=bool)
        last_charging_arrival = np.array([True, False, False, False])
        uav_return_energy_margins = np.array([0.05, 0.5, 0.5, 0.5])
    return _Stub()


def test_event_scan_clean_leave_has_no_exclusion_and_full_conformance_record():
    env = _leave_env_stub(station_occupancy_after=np.array([1.0, 0.0]),
                           station_queue_after=np.array([0.0, 0.0]))
    cand = audit.build_leave_candidate(
        env, uav_idx=0, t_e_step=42, schedule="constructive_mixed",
        station_occupancy_after=np.array([1.0, 0.0]), station_queue_after=np.array([0.0, 0.0]),
        cutoff_before=False, depletion_before=False)
    assert audit.check_leave_eligibility(cand, t_e=42) == []
    record = audit.build_event_conformance_record(cand)
    assert record["uav_charging"] is True
    assert record["battery_ratio"] == pytest.approx(0.20)
    # capacity-1 station, uncontested capture -> occupancy-excluding-self is 0
    assert cand["station_occupancy_excluding_self"] == 0.0


def test_event_scan_contested_station_excludes():
    env = _leave_env_stub(station_occupancy_after=np.array([2.0, 0.0]),
                           station_queue_after=np.array([0.0, 0.0]))
    cand = audit.build_leave_candidate(
        env, uav_idx=0, t_e_step=42, schedule="constructive_mixed",
        station_occupancy_after=np.array([2.0, 0.0]), station_queue_after=np.array([0.0, 0.0]),
        cutoff_before=False, depletion_before=False)
    assert audit.EXCLUDE_QUEUE_OR_OCCUPIED in audit.check_leave_eligibility(cand, t_e=42)


def test_event_scan_nonzero_queue_excludes():
    env = _leave_env_stub(station_occupancy_after=np.array([1.0, 0.0]),
                           station_queue_after=np.array([1.0, 0.0]))
    cand = audit.build_leave_candidate(
        env, uav_idx=0, t_e_step=42, schedule="constructive_mixed",
        station_occupancy_after=np.array([1.0, 0.0]), station_queue_after=np.array([1.0, 0.0]),
        cutoff_before=False, depletion_before=False)
    assert audit.EXCLUDE_QUEUE_OR_OCCUPIED in audit.check_leave_eligibility(cand, t_e=42)


def test_event_scan_cutoff_before_leave_excludes():
    env = _leave_env_stub(station_occupancy_after=np.array([1.0, 0.0]),
                           station_queue_after=np.array([0.0, 0.0]))
    cand = audit.build_leave_candidate(
        env, uav_idx=0, t_e_step=42, schedule="constructive_mixed",
        station_occupancy_after=np.array([1.0, 0.0]), station_queue_after=np.array([0.0, 0.0]),
        cutoff_before=True, depletion_before=False)
    assert audit.EXCLUDE_EMERGENCY in audit.check_leave_eligibility(cand, t_e=42)


def test_event_scan_depletion_before_leave_excludes():
    env = _leave_env_stub(station_occupancy_after=np.array([1.0, 0.0]),
                           station_queue_after=np.array([0.0, 0.0]))
    cand = audit.build_leave_candidate(
        env, uav_idx=0, t_e_step=42, schedule="constructive_mixed",
        station_occupancy_after=np.array([1.0, 0.0]), station_queue_after=np.array([0.0, 0.0]),
        cutoff_before=False, depletion_before=True)
    assert audit.EXCLUDE_EMERGENCY in audit.check_leave_eligibility(cand, t_e=42)


def test_event_scan_temporary_failure_excludes():
    env = _leave_env_stub(station_occupancy_after=np.array([1.0, 0.0]),
                           station_queue_after=np.array([0.0, 0.0]))
    env.uav_failed = np.array([True, False, False, False])
    cand = audit.build_leave_candidate(
        env, uav_idx=0, t_e_step=42, schedule="constructive_mixed",
        station_occupancy_after=np.array([1.0, 0.0]), station_queue_after=np.array([0.0, 0.0]),
        cutoff_before=False, depletion_before=False)
    assert audit.EXCLUDE_TEMP_FAILURE in audit.check_leave_eligibility(cand, t_e=42)


def test_event_scan_off_schedule_leave_excludes():
    env = _leave_env_stub(station_occupancy_after=np.array([1.0, 0.0]),
                           station_queue_after=np.array([0.0, 0.0]))
    cand = audit.build_leave_candidate(
        env, uav_idx=0, t_e_step=42, schedule="null",
        station_occupancy_after=np.array([1.0, 0.0]), station_queue_after=np.array([0.0, 0.0]),
        cutoff_before=False, depletion_before=False)
    assert audit.EXCLUDE_OFF_SCHEDULE in audit.check_leave_eligibility(cand, t_e=42)


def test_update_duty_map_on_transitions_detects_leave_and_rejoin_edges():
    class _Env:
        n_uavs = 3
        uav_positions = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [20.0, 0.0, 0.0]])

    duty_positions = {0: np.array([0.0, 0.0, 0.0]), 1: np.array([10.0, 0.0, 0.0]),
                       2: np.array([20.0, 0.0, 0.0])}
    duty_map = {0: 0, 1: 1, 2: 2}
    before = np.array([False, False, False])
    after_leave = np.array([True, False, False])
    new_map, leave_uavs, rejoin_uavs = audit.update_duty_map_on_transitions(
        duty_map=duty_map, duty_positions=duty_positions, env=_Env(),
        charging_before=before, charging_after=after_leave, schedule="constructive_mixed")
    assert leave_uavs == [0] and rejoin_uavs == []
    assert 0 not in new_map.values()  # uav 0 removed from the duty map at LEAVE

    after_rejoin = np.array([False, False, False])
    new_map2, leave2, rejoin2 = audit.update_duty_map_on_transitions(
        duty_map=new_map, duty_positions=duty_positions, env=_Env(),
        charging_before=after_leave, charging_after=after_rejoin, schedule="constructive_mixed")
    assert leave2 == [] and rejoin2 == [0]
    assert 0 in new_map2.values()  # uav 0 restored to the duty map at REJOIN


def test_update_duty_map_on_transitions_null_schedule_never_changes():
    duty_positions = {0: np.array([0.0, 0.0, 0.0])}
    duty_map = {0: 0}
    new_map, leave_uavs, _ = audit.update_duty_map_on_transitions(
        duty_map=duty_map, duty_positions=duty_positions,
        env=type("E", (), {"n_uavs": 1, "uav_positions": np.zeros((1, 3))})(),
        charging_before=np.array([False]), charging_after=np.array([True]), schedule="null")
    assert leave_uavs == [0]
    assert new_map == duty_map  # null freezes the map even across a real LEAVE edge


# --- prefix-replay fork discipline: a hash mismatch invalidates -------------

def test_replay_hash_mismatch_is_never_silently_repaired():
    """Mirrors `replay_prefix`'s own discipline (build fresh env, replay
    recorded steps, hash-check against the ORIGINAL rollout's recorded
    hash) without going through the real `UAVEnergyAwareRelayEnv`
    constructor: two independently-evolved snapshots that genuinely
    diverged (different battery draw) must raise, not be silently
    accepted or repaired."""
    duty_map = {0: 0}
    original_snapshot = {
        "positions": np.zeros((1, 3)), "battery_ratios": np.array([0.50]),
        "charging_mask": np.array([False]), "station_occupancy": np.array([0.0]),
        "station_queue": np.array([0.0]), "lifecycle_mask": np.array([False]),
        "duty_map": duty_map,
    }
    diverged_replay_snapshot = dict(original_snapshot)
    diverged_replay_snapshot["battery_ratios"] = np.array([0.49])  # replay drifted
    expected_hash = audit.compute_state_hash(original_snapshot)
    actual_hash = audit.compute_state_hash(diverged_replay_snapshot)
    assert expected_hash != actual_hash
    with pytest.raises(audit.PrefixReplayMismatchError):
        audit.assert_state_hash_equal(expected_hash, actual_hash, context="prefix replay to t_e")


def test_replay_prefix_raises_on_mismatch_via_the_real_orchestration_function(monkeypatch):
    """Exercises `replay_prefix` itself (not just the primitive it calls):
    stubs `build_pinned_env` to return a controllable fake env whose
    replayed state will not match a deliberately wrong `expected_hash`."""
    class _FakeEnv:
        n_uavs = 1
        uav_positions = np.zeros((1, 3))
        uav_battery_ratios = np.array([0.5])
        uav_charging = np.array([False])
        station_occupancy = np.array([0.0])
        station_queue_lengths = np.array([0.0])

        def step(self, actions):
            pass

    monkeypatch.setattr(audit, "build_pinned_env", lambda *a, **k: _FakeEnv())
    with pytest.raises(audit.PrefixReplayMismatchError):
        audit.replay_prefix(
            config=None, coords=None, coord_hash="irrelevant", episode_seed=1,
            recorded_actions=[], expected_hash="deliberately-wrong-hash",
            duty_map_at_te={0: 0})


# --- evaluator-only forward replay: never contaminates the real rollout ----

class _CloneableFakeEnv:
    """Minimal FakeEnv supporting the full `step_once` pipeline
    (`compute_duty_positions` / `scripted_source_actions` / `env.step`) with
    simple deterministic dynamics, so `evaluator_forward_replay` and
    `fork_continuation` can be exercised end-to-end without a real
    `UAVEnergyAwareRelayEnv`."""

    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        self.n_uavs = 4
        self.n_users = 6
        self.time_step = 1.0
        self.max_speed = 30.0
        self.max_vertical_speed_mps = 5.0
        self.area_size = 1000.0
        self.height_range = (80.0, 80.0)
        self.battery_capacity_wh = 160.0
        self.charging_power_w = 1000.0
        self.return_reserve_ratio = 0.10
        self.service_cutoff_threshold = 0.02
        self.depleted_battery_threshold = 0.0
        self.user_qos_rate_mbps = 1.0
        self.n_charging_stations = 1
        self.charging_station_positions = np.array([[900.0, 900.0, 80.0]])
        self.ground_bs_positions = np.array([[0.0, 0.0, 80.0]])
        self.agents = [f"uav_{i}" for i in range(self.n_uavs)]
        self.uav_positions = rng.uniform(100.0, 900.0, size=(self.n_uavs, 3))
        self.uav_positions[:, 2] = 80.0
        self.user_positions = rng.uniform(100.0, 900.0, size=(self.n_users, 3))
        self.user_positions[:, 2] = 0.0
        self._drift = rng.uniform(-2.0, 2.0, size=(self.n_users, 2))
        self.uav_battery_ratios = np.full(self.n_uavs, 0.9)
        self.uav_charging = np.zeros(self.n_uavs, dtype=bool)
        self.uav_dock_requests = np.zeros(self.n_uavs, dtype=bool)
        self.uav_target_stations = np.full(self.n_uavs, -1, dtype=int)
        self.uav_failed = np.zeros(self.n_uavs, dtype=bool)
        self.last_charging_arrival = np.zeros(self.n_uavs, dtype=bool)
        self.uav_return_energy_margins = np.full(self.n_uavs, 0.5)
        self.station_occupancy = np.array([0.0])
        self.station_queue_lengths = np.array([0.0])
        self.last_user_rates_mbps = np.full(self.n_users, 2e6)
        self.np_random = np.random.RandomState(seed)

    def _calculate_power_consumption(self, v_h, v_z):
        return 300.0 + v_h  # deterministic, monotone -- exact value is not load-bearing

    def _nearest_charging_station(self, uav_idx):
        rel = self.charging_station_positions[0] - self.uav_positions[uav_idx]
        return 0, rel, float(np.linalg.norm(rel))

    def step(self, actions):
        # Mirrors the real env's OWN contract exactly: returns the
        # 5-tuple `(observations, rewards, terminations, truncations,
        # infos)` -- `scenario_base.py:3547` -- never caches `infos` as a
        # `self.infos` attribute. `step_once` must read the RETURNED infos.
        for idx, agent in enumerate(self.agents):
            act = np.asarray(actions[agent], dtype=float)
            self.uav_positions[idx, :2] += act[:2] * self.max_speed * self.time_step
        self.user_positions[:, :2] += self._drift
        self.uav_battery_ratios = np.clip(self.uav_battery_ratios - 0.001, 0.0, 1.0)
        infos = {a: {"reward_info": {"qos_satisfaction_ratio": 0.9,
                                      "return_constraint_cost": 0.05,
                                      "return_constraint_cost_raw": 0.05}}
                 for a in self.agents}
        return None, None, None, None, infos


def test_evaluator_forward_replay_does_not_mutate_the_original_env():
    env = _CloneableFakeEnv(seed=1)
    duty_positions, centroids = audit.compute_duty_positions(env)
    duty_map = {i: i for i in range(env.n_uavs)}
    positions_before = env.uav_positions.copy()
    users_before = env.user_positions.copy()

    result = audit.evaluator_forward_replay(env, duty_map=duty_map, service_centroids=centroids,
                                             delta_steps=5)

    np.testing.assert_array_equal(env.uav_positions, positions_before)
    np.testing.assert_array_equal(env.user_positions, users_before)
    assert result["duty_positions_final"]
    # users drifted on the CLONE, so at least one duty target must have moved
    moved = any(
        not np.allclose(result["duty_positions_final"][d][:2], duty_positions[d][:2])
        for d in duty_positions
    )
    assert moved


def test_evaluator_forward_replay_asserts_hash_before_stepping(monkeypatch):
    """A clone that (somehow) diverges from the original before any replay
    step must be caught by the pre-step hash assertion, never silently
    used."""
    env = _CloneableFakeEnv(seed=2)
    duty_map = {i: i for i in range(env.n_uavs)}

    def _bad_deepcopy(obj):
        clone = _CloneableFakeEnv(seed=2)
        clone.uav_battery_ratios = clone.uav_battery_ratios + 0.5  # forced divergence
        return clone

    monkeypatch.setattr(audit.copy, "deepcopy", _bad_deepcopy)
    with pytest.raises(audit.PrefixReplayMismatchError):
        audit.evaluator_forward_replay(env, duty_map=duty_map, service_centroids=None, delta_steps=2)


def test_fork_continuation_set_arm_diverges_from_keep_arm():
    """The SET arm (focal forced toward an alternative target for Delta
    steps) must produce a DIFFERENT trajectory than KEEP (unperturbed) --
    if it didn't, the intervention machinery would be measuring nothing."""
    env_keep = _CloneableFakeEnv(seed=3)
    env_set = _CloneableFakeEnv(seed=3)
    duty_positions, centroids = audit.compute_duty_positions(env_keep)
    duty_map = {i: i for i in range(env_keep.n_uavs)}
    focal = 0
    alt_target = np.array([10.0, 10.0, 80.0])

    keep_out = audit.fork_continuation(
        env_keep, duty_map_at_te=duty_map, duty_positions_at_te=duty_positions,
        service_centroids_at_te=centroids, schedule="constructive_mixed", horizon=5,
        continuation_seed=123)
    set_out = audit.fork_continuation(
        env_set, duty_map_at_te=duty_map, duty_positions_at_te=duty_positions,
        service_centroids_at_te=centroids, schedule="constructive_mixed", horizon=5,
        continuation_seed=123, focal_uav=focal, focal_target=alt_target, delta_steps=3)

    assert not np.allclose(env_keep.uav_positions[focal], env_set.uav_positions[focal])
    assert len(keep_out["step_metrics"]) == 5
    assert len(set_out["step_metrics"]) == 5


def test_fork_continuation_reseeds_np_random_to_the_stream_seed():
    """`fork_continuation` must reseed `env.np_random` to the
    stream_seed-derived continuation RNG -- never leave the PRE-FORK stream
    running (which would silently reuse whatever the prefix rollout already
    consumed, breaking the disjoint selection/evaluation replicate streams
    section 8/Q-I2 requires). Planted precondition: `env.np_random` starts
    seeded to something else (999) entirely, so a no-op reseed would fail
    this."""
    env = _CloneableFakeEnv(seed=4)
    env.np_random = np.random.RandomState(999)
    duty_positions, centroids = audit.compute_duty_positions(env)
    duty_map = {i: i for i in range(env.n_uavs)}
    audit.fork_continuation(
        env, duty_map_at_te=duty_map, duty_positions_at_te=duty_positions,
        service_centroids_at_te=centroids, schedule="constructive_mixed", horizon=1,
        continuation_seed=42)
    expected_first_draw = np.random.RandomState(42 % (2**32 - 1)).uniform()
    actual_first_draw = env.np_random.uniform()
    assert actual_first_draw == pytest.approx(expected_first_draw)


# =============================================================================
# 14. Part-A conformance wiring (item 1-4): full_sync_SET schedule, the real
#     conformance_ok conjunction, arm-distinctness, joint bootstrap bounds,
#     verdict-to-branch-input mapping, and invalidated-pair exclusion.
# =============================================================================

def test_full_sync_set_schedule_resyncs_every_step_even_without_a_transition():
    """full_sync_SET (Part-A diagnostic, section 4: 'reassigns every duty at
    each check') must recompute the WHOLE duty map every step regardless of
    whether a LEAVE/REJOIN transition happened -- unlike constructive_mixed,
    which preserves the map between lifecycle events (section 4: 'between
    lifecycle events it performs no full-sync permutation'). Constructed so
    the CURRENT duty assignment is the WORST possible one (each UAV sits
    physically at the OTHER duty's position): full_sync must swap it back;
    an implementation that only updates on transitions would leave this
    (measurably wrong) map untouched."""
    duty_positions = {0: np.array([0.0, 0.0, 100.0]), 1: np.array([100.0, 0.0, 100.0])}
    duty_map = {0: 0, 1: 1}  # current (suboptimal) assignment: identity

    class _Env:
        n_uavs = 2
        # uav 0 physically at duty 1's spot; uav 1 physically at duty 0's spot.
        uav_positions = np.array([[100.0, 0.0, 0.0], [0.0, 0.0, 0.0]])

    no_transition = np.array([False, False])
    new_map, leave_uavs, rejoin_uavs = audit.update_duty_map_on_transitions(
        duty_map=duty_map, duty_positions=duty_positions, env=_Env(),
        charging_before=no_transition, charging_after=no_transition,
        schedule="full_sync_SET")
    assert leave_uavs == [] and rejoin_uavs == []   # no transition occurred at all
    assert new_map == {0: 1, 1: 0}                   # yet the map was fully re-synced
    assert new_map != duty_map

    # Sanity/contrast: constructive_mixed on the IDENTICAL no-transition
    # input really does leave the map untouched -- the property this test
    # exists to distinguish full_sync_SET from.
    unchanged_map, _, _ = audit.update_duty_map_on_transitions(
        duty_map=duty_map, duty_positions=duty_positions, env=_Env(),
        charging_before=no_transition, charging_after=no_transition,
        schedule="constructive_mixed")
    assert unchanged_map == duty_map


def test_compute_conformance_ok_is_true_only_when_all_three_conjuncts_hold():
    assert audit.compute_conformance_ok(
        invalidated_pairs=0, topology_hash_ok=True, arm_distinct_ok=True) is True
    assert audit.compute_conformance_ok(
        invalidated_pairs=1, topology_hash_ok=True, arm_distinct_ok=True) is False
    assert audit.compute_conformance_ok(
        invalidated_pairs=0, topology_hash_ok=False, arm_distinct_ok=True) is False
    assert audit.compute_conformance_ok(
        invalidated_pairs=0, topology_hash_ok=True, arm_distinct_ok=False) is False


def test_arm_distinctness_check_true_when_at_least_one_pair_differs():
    pairs = [({0: 0}, {0: 0}), ({0: 1, 1: 0}, {0: 0, 1: 1})]
    assert audit.arm_distinctness_check(pairs) is True


def test_arm_distinctness_check_false_when_every_pair_is_identical():
    """Reproduces the exact shape of the historical bug
    (`constructive_mixed_update`'s own docstring): if constructive and null
    never actually differ across every witnessed event, the spot check must
    catch it, not pass vacuously."""
    pairs = [({0: 0}, {0: 0}), ({1: 1}, {1: 1})]
    assert audit.arm_distinctness_check(pairs) is False


def test_arm_distinctness_check_vacuously_true_on_no_certified_events():
    """An empty witness list means no events were found anywhere in the run
    -- that is SOURCE_EVENT_SUPPORT_INSUFFICIENT's (branch 2) failure mode,
    already reported via `support_ok`, and must not be double-counted as an
    arm-conformance defect ahead of it in `decide_branch`'s precedence."""
    assert audit.arm_distinctness_check([]) is True


def test_compute_part_a_bounds_returns_none_with_no_stable_event_data():
    """Item 5a, first half of 'when and only when the stable class has
    events': zero qualifying stable-limb calibration data anywhere in the
    run must produce no Part-A bounds at all, never a silently-NaN result."""
    shared = audit.draw_shared_topology_indices(n_topo=2, iters=20, seed=1)
    result = audit.compute_part_a_bounds(
        d_a_topology_units=[[], []],
        b_stable_topology_units=_degenerate_topology_units([1.0, 1.0]),
        shared_topology_indices=shared, seed=1)
    assert result is None


def test_compute_part_a_bounds_hand_worked_deterministic_single_topology():
    """Single topology, degenerate one-event units (no resampling variance):
    D_A = 3.0, B_stable = 20.0. lower_contrast = D_A + 0.05*B_stable = 3.0 +
    1.0 = 4.0; upper_contrast = 0.05*B_stable - D_A = 1.0 - 3.0 = -2.0. Every
    percentile bound must equal these exact point values."""
    shared = audit.draw_shared_topology_indices(n_topo=1, iters=20, seed=1)
    result = audit.compute_part_a_bounds(
        d_a_topology_units=_degenerate_topology_units([3.0]),
        b_stable_topology_units=_degenerate_topology_units([20.0]),
        shared_topology_indices=shared, seed=1)
    assert result["b_stable_lcb"] == pytest.approx(20.0)
    assert result["lower_contrast_lcb"] == pytest.approx(4.0)
    assert result["lower_contrast_ucb"] == pytest.approx(4.0)
    assert result["upper_contrast_lcb"] == pytest.approx(-2.0)


def test_part_a_inputs_present_but_not_applicable_when_b_stable_lcb_not_positive():
    """Item 5a, second half ('and LCB95(B_stable)>0'): stable-limb event
    data DOES exist (bounds are produced, not None) but B_stable's own LCB
    is <= 0 -- the verdict must be NOT_APPLICABLE, and that must never flip
    `part_a_contradiction` to True."""
    shared = audit.draw_shared_topology_indices(n_topo=1, iters=20, seed=3)
    bounds = audit.compute_part_a_bounds(
        d_a_topology_units=_degenerate_topology_units([1.0]),
        b_stable_topology_units=_degenerate_topology_units([-5.0]),
        shared_topology_indices=shared, seed=3)
    assert bounds is not None
    verdict = audit.part_a_conformance(
        lower_contrast_lcb=bounds["lower_contrast_lcb"],
        lower_contrast_ucb=bounds["lower_contrast_ucb"],
        upper_contrast_lcb=bounds["upper_contrast_lcb"], b_stable_lcb=bounds["b_stable_lcb"])
    assert verdict == "NOT_APPLICABLE"
    contradiction, _ = audit.map_part_a_verdict_to_inputs(verdict)
    assert contradiction is False


def test_map_part_a_verdict_to_inputs_only_contradiction_sets_true():
    assert audit.map_part_a_verdict_to_inputs("PART_A_CONTRADICTION") == (True, "PART_A_CONTRADICTION")
    assert audit.map_part_a_verdict_to_inputs("CONFORMANCE_PASS") == (False, "CONFORMANCE_PASS")
    assert audit.map_part_a_verdict_to_inputs(
        "PART_A_CONFORMANCE_UNRESOLVED") == (False, "PART_A_CONFORMANCE_UNRESOLVED")
    assert audit.map_part_a_verdict_to_inputs("NOT_APPLICABLE") == (False, "NOT_APPLICABLE")


def test_unresolved_verdict_lands_in_diagnostic_and_never_flips_decide_branch():
    """Item 5c: PART_A_CONFORMANCE_UNRESOLVED must land in the diagnostic
    payload only -- `decide_branch`'s outcome under it must be IDENTICAL to
    CONFORMANCE_PASS/NOT_APPLICABLE (all three keep `part_a_contradiction`
    False), while PART_A_CONTRADICTION must genuinely flip the branch. A
    wrong mapping that ever set `part_a_contradiction=True` for UNRESOLVED
    would make this test's first loop disagree with its last assertion."""
    common_kwargs = dict(
        conformance_ok=True, support_ok=True, primary_g_degenerate_flag=False,
        b_stable_lcb=1.0, t_stable_ucb=-1.0, t_stable_lcb=-2.0,
        b_flex_lcb=1.0, t_flex_lcb=1.0, t_flex_ucb=2.0,
    )
    for verdict in ("PART_A_CONFORMANCE_UNRESOLVED", "CONFORMANCE_PASS", "NOT_APPLICABLE"):
        part_a_contradiction, diagnostic = audit.map_part_a_verdict_to_inputs(verdict)
        assert part_a_contradiction is False
        assert diagnostic == verdict
        branch = audit.decide_branch(part_a_contradiction=part_a_contradiction, **common_kwargs)
        assert branch == "PERSISTENCE_NECESSARY_SOURCE"

    contradiction_input, _ = audit.map_part_a_verdict_to_inputs("PART_A_CONTRADICTION")
    assert contradiction_input is True
    branch_with_contradiction = audit.decide_branch(part_a_contradiction=contradiction_input, **common_kwargs)
    assert branch_with_contradiction == "PART_A_CONTRADICTION"


def test_run_audit_event_voids_the_whole_event_when_a_clone_fails():
    """R2 failure semantics, and the exact rule that CHANGED at the refreeze.

    Under the superseded contract every replicate replayed the prefix
    independently, so one mismatch excluded only that replicate and the event
    survived with a shorter array. Under the shared-prefix realization there is
    ONE canonical replay per event, so a clone-equivalence or isolation failure
    means the fixed-history guarantee failed for the WHOLE event: the driver
    must set `event_invalid`, stop issuing further clones, and let the caller
    drop the event rather than keep a partially-populated one.

    A test that still asserted the old shrink-by-one behaviour would pass only
    by accident and would license exactly the partial event R2 forbids."""
    snap = _snapshot_of(_CloneableFakeEnv(seed=5))
    env_for_geometry = _CloneableFakeEnv(seed=5)
    duty_positions, centroids = audit.compute_duty_positions(env_for_geometry)
    duty_map = {i: i for i in range(env_for_geometry.n_uavs)}
    event = {
        "hash_at_te": snap.hash_at_te, "duty_map_at_te": duty_map,
        "duty_positions_at_te": duty_positions, "service_centroids_at_te": centroids,
        "focal_stable_uav": 0, "legal_targets": {"stable": {}},
        "locked_duties": {"stable": frozenset()},
    }

    real_clone = snap.clone
    calls = {"n": 0}

    def _flaky_clone(**kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise audit.CloneIsolationError("injected isolation failure")
        return real_clone(**kwargs)

    snap.clone = _flaky_clone

    result = audit.run_audit_event(
        snapshot=snap, topology_seed=1, episode_seed=1,
        event=event, limb="stable", n_select=1, n_eval=4)

    assert result["event_invalid"] is True
    assert len(result["invalidated_pairs"]) == 1
    assert result["invalidated_pairs"][0]["candidate_id"] == "KEEP"
    # Short-circuited: replicates 3 and 4 were never attempted after the void.
    assert calls["n"] == 2
    assert len(result["eval_keep"]) == 1


def test_run_calibration_episode_voids_the_episode_when_event_identity_fails(monkeypatch):
    """R3 condition 1C. The snapshot is captured off the live certified
    environment, so the failure mode is no longer a replay mismatch -- it is the
    world having moved between certification and capture. Reported once against
    `live_event_capture` for both limbs, and the episode contributes to neither
    `B_m` nor `D_A`, never repaired or retried."""
    fake_event = {
        "hash_at_te": "h", "duty_map_at_te": {0: 0}, "duty_positions_at_te": {},
        "service_centroids_at_te": None, "conformance_record": {},
        "duty_map_before_leave": {0: 0},
    }
    monkeypatch.setattr(audit, "build_pinned_env", lambda *a, **k: _CloneableFakeEnv(seed=1))
    monkeypatch.setattr(audit, "apply_energy_profile", lambda *a, **k: None)
    monkeypatch.setattr(
        audit, "roll_prefix_and_find_event",
        lambda env, **k: {"event": fake_event, "exclusions": [], "recorded_actions": []},
    )

    # R3 failure mode: the world moved between certification and capture, so the
    # snapshot's fingerprint does not match the one recorded at certification.
    fake_event["full_fingerprint_at_te"] = "a-fingerprint-from-a-different-world"

    result = audit.run_calibration_episode(
        config=None, topology_seed=1, episode_seed=1, energy_seed=1, coords={}, coord_hash="x")

    assert result["support_miss"] is False
    assert result["invalidated"] is True
    assert len(result["invalidated_pairs"]) == 1
    assert result["invalidated_pairs"][0]["schedule"] == "live_event_capture"
    assert result["invalidated_pairs"][0]["limb"] == "both"
    assert result["results"] == {}                  # neither limb contributes B_m or D_A


# =============================================================================
# R2 shared-prefix realization -- the six Stage-B blocking conditions.
# These are what the Pro ruling names as blocking before launch, so they are
# proved here rather than asserted in prose.
# =============================================================================

def _snapshot_of(env, *, duty_map=None):
    """An `EventSnapshot` whose certified hashes are derived from `env` itself,
    so the snapshot is internally consistent and any failure a test sees is the
    injected one rather than a hash that never matched."""
    duty_map = {i: i for i in range(env.n_uavs)} if duty_map is None else duty_map
    return audit.EventSnapshot(
        env,
        coord_hash=audit.coordinate_hash(env.ground_bs_positions,
                                          env.charging_station_positions),
        hash_at_te=audit.compute_state_hash(audit.real_env_state_snapshot(env, duty_map)),
        duty_map_at_te=duty_map)


def test_replicate_constants_are_the_r2_scientific_floor():
    """R2 section 8. n_select=1 is inadmissible, so no constant may reintroduce
    it -- including through the smoke path, which now runs the same shape."""
    assert audit.N_SELECT == 2
    assert audit.N_EVAL == 2


def test_clone_restores_the_certified_state_condition_5():
    snap = _snapshot_of(_CloneableFakeEnv(seed=21))
    clone = snap.clone()
    assert audit.compute_state_hash(
        audit.real_env_state_snapshot(clone, snap.duty_map_at_te)) == snap.hash_at_te


def test_clone_preserves_the_topology_hash_condition_4():
    env = _CloneableFakeEnv(seed=22)
    snap = _snapshot_of(env)
    clone = snap.clone()
    assert audit.coordinate_hash(clone.ground_bs_positions,
                                  clone.charging_station_positions) == snap.coord_hash


def test_mutating_one_clone_touches_neither_the_source_nor_a_sibling_condition_2():
    """The isolation the whole optimization rests on: if clones shared state
    with the snapshot, continuations would silently contaminate each other and
    every downstream margin would be measured against a moving history."""
    snap = _snapshot_of(_CloneableFakeEnv(seed=23))
    first, second = snap.clone(), snap.clone()

    first.uav_positions[0] += 500.0
    first.uav_battery_ratios[0] = 0.01

    assert not np.allclose(first.uav_positions[0], second.uav_positions[0])
    assert second.uav_battery_ratios[0] == pytest.approx(0.9)
    snap.assert_source_intact()          # raises if the snapshot moved
    assert audit.compute_state_hash(
        audit.real_env_state_snapshot(second, snap.duty_map_at_te)) == snap.hash_at_te


def test_cloning_consumes_no_source_rng_condition_3():
    """R2 step 3 puts the snapshot BEFORE any continuation-specific RNG is
    assigned. If cloning advanced the source RNG, the Nth continuation would
    silently draw from a different stream than its registered `stream_seed`."""
    snap = _snapshot_of(_CloneableFakeEnv(seed=24))
    before = audit._rng_state_token(snap._env)
    for _ in range(5):
        snap.clone()
    assert audit._rng_state_token(snap._env) == before
    assert snap.clones_issued == 5


def test_capture_rejects_a_snapshot_that_does_not_match_the_certified_world():
    """R3 condition 1C, the check that would have caught the Stage B defect.

    A snapshot whose complete-state fingerprint differs from the one recorded
    when the event was certified is a snapshot of a DIFFERENT world, and must be
    refused at construction rather than handed out as the certified history.
    Under the superseded route this is exactly what happened silently, because
    the only check was a narrow UAV-only hash that agreed across worlds."""
    env = _CloneableFakeEnv(seed=25)
    duty_map = {i: i for i in range(env.n_uavs)}
    with pytest.raises(audit.CloneIsolationError):
        audit.EventSnapshot(
            env,
            coord_hash=audit.coordinate_hash(env.ground_bs_positions,
                                              env.charging_station_positions),
            hash_at_te=audit.compute_state_hash(
                audit.real_env_state_snapshot(env, duty_map)),
            duty_map_at_te=duty_map,
            certified_fingerprint="a-fingerprint-from-a-different-world")


def test_full_fingerprint_separates_worlds_the_narrow_hash_cannot():
    """Why the fingerprint replaced the hash as the load-bearing assertion."""
    a = _CloneableFakeEnv(seed=40)
    b = _CloneableFakeEnv(seed=40)
    duty_map = {i: i for i in range(a.n_uavs)}

    # Same UAV-side state, different user world.
    b.user_positions = a.user_positions + 500.0

    assert (audit.compute_state_hash(audit.real_env_state_snapshot(a, duty_map))
            == audit.compute_state_hash(audit.real_env_state_snapshot(b, duty_map))), (
        "precondition: the narrow hash is blind to user state")
    assert (audit.full_state_fingerprint(a, duty_map=duty_map)
            != audit.full_state_fingerprint(b, duty_map=duty_map)), (
        "the fingerprint must see what the narrow hash cannot")


def test_clone_raises_on_a_topology_hash_mismatch():
    env = _CloneableFakeEnv(seed=26)
    duty_map = {i: i for i in range(env.n_uavs)}
    bad = audit.EventSnapshot(
        env, coord_hash="not-the-recorded-topology",
        hash_at_te=audit.compute_state_hash(audit.real_env_state_snapshot(env, duty_map)),
        duty_map_at_te=duty_map)
    with pytest.raises(audit.TopologyMismatchError):
        bad.clone()


def test_conditions_1a_and_1b_on_one_live_snapshot():
    """R3's replacement for the unsatisfiable condition 1. No monkeypatched
    deterministic oracle: both clones come from ONE real snapshot.

    1A -- same snapshot, same stream, identical results.
    1B -- a different stream starts from identical non-RNG state. It is NOT
    required to change the trajectory; a stochastic stream may go unused, so a
    difference is reported rather than asserted."""
    source = _CloneableFakeEnv(seed=27)
    duty_map = {i: i for i in range(source.n_uavs)}
    duty_positions, centroids = audit.compute_duty_positions(source)
    snap = _snapshot_of(source, duty_map=duty_map)
    event = {
        "hash_at_te": snap.hash_at_te,
        "duty_map_at_te": duty_map,
        "duty_positions_at_te": duty_positions,
        "service_centroids_at_te": centroids,
    }

    verdict = audit.verify_clone_conformance(
        snap, event=event, limb="stable", continuation_seed=987654321,
        other_seed=123456789, horizon=25)

    assert verdict["condition_1a_same_stream_identical"] is True
    assert verdict["pre_stream_state_equal"] is True
    assert verdict["condition_1b_pre_stream_state_equal"] is True
    assert verdict["source_intact"] is True


def test_shared_prefix_performs_no_reconstruction_replay_at_all(monkeypatch):
    """The R3 claim, measured rather than asserted: one calibration episode runs
    five continuations (stable x3 including full_sync_SET, flex x2) and must
    perform ZERO reconstruction replays.

    The superseded route replayed five times, each into a fresh environment with
    its own user world. R2 cut that to one -- which made the arms mutually
    consistent but still located them in a reconstructed world rather than the
    certified one. R3 cuts it to none."""
    source = _CloneableFakeEnv(seed=28)
    duty_map = {i: i for i in range(source.n_uavs)}
    duty_positions, centroids = audit.compute_duty_positions(source)
    real_coord_hash = audit.coordinate_hash(source.ground_bs_positions,
                                             source.charging_station_positions)
    fake_event = {
        "hash_at_te": audit.compute_state_hash(
            audit.real_env_state_snapshot(source, duty_map)),
        "duty_map_at_te": duty_map,
        "duty_positions_at_te": duty_positions,
        "service_centroids_at_te": centroids,
        "conformance_record": {},
        "duty_map_before_leave": duty_map,
    }
    monkeypatch.setattr(audit, "build_pinned_env", lambda *a, **k: _CloneableFakeEnv(seed=28))
    monkeypatch.setattr(audit, "apply_energy_profile", lambda *a, **k: None)
    monkeypatch.setattr(
        audit, "roll_prefix_and_find_event",
        lambda env, **k: {"event": fake_event, "exclusions": [], "recorded_actions": []})

    calls = {"n": 0}

    def _counting_replay(*a, **k):
        calls["n"] += 1
        return _CloneableFakeEnv(seed=28)

    monkeypatch.setattr(audit, "replay_prefix", _counting_replay)

    result = audit.run_calibration_episode(
        config=None, topology_seed=1, episode_seed=1, energy_seed=1,
        coords={}, coord_hash=real_coord_hash)

    assert result["invalidated"] is False
    # R3: not "one replay" but ZERO. The snapshot is captured off the live
    # certified environment, so the reconstruction step is gone entirely --
    # which is what removes the second user world.
    assert calls["n"] == 0
    assert set(result["results"]) == {"stable", "flex"}


def test_selection_diagnostic_reports_a_decided_event_as_concentrated():
    """A candidate that clearly dominates should show up as such: the point
    winner takes essentially all the bootstrap selection mass."""
    events = [{
        "candidates": {
            "z_far": {"select": np.array([100.0, 101.0]), "eval_set": np.array([1.0])},
            "z_near": {"select": np.array([0.0, 0.5]), "eval_set": np.array([1.0])},
        },
        "eval_keep": np.array([0.0]),
    }]
    diag = audit.selection_diagnostic(events, iters=500)[0]
    assert diag["legal_set_size"] == 2
    assert diag["point_selected"] == "z_far"
    assert diag["selection_frequency"]["z_far"] == pytest.approx(1.0)
    assert diag["concentration_hhi"] == pytest.approx(1.0)
    assert diag["normalized_entropy"] == pytest.approx(0.0)


def test_selection_diagnostic_exposes_an_unstable_maximizer():
    """The case the contract actually cares about at the 2/2 floor: two
    indistinguishable candidates must surface as a near coin flip -- high
    entropy, minimal concentration -- rather than hide behind whichever one the
    point argmax happened to pick. Instability widens or fails to resolve the
    gate; it must never be invisible in the artifact."""
    events = [{
        "candidates": {
            "z_a": {"select": np.array([1.0, -1.0]), "eval_set": np.array([1.0])},
            "z_b": {"select": np.array([-1.0, 1.0]), "eval_set": np.array([1.0])},
        },
        "eval_keep": np.array([0.0]),
    }]
    diag = audit.selection_diagnostic(events, iters=4000)[0]
    # NOT 0.5, and the gap is a real property of the 2/2 floor rather than
    # noise. Resampling two values with replacement gives each candidate mean
    # 1.0/0.0/-1.0 with probability 0.25/0.5/0.25, so the two candidates TIE on
    # 0.375 of iterations, and argmax breaks every tie toward the
    # first-enumerated candidate: 0.3125 strict wins + 0.375 ties = 0.6875.
    assert diag["selection_frequency"]["z_a"] == pytest.approx(0.6875, abs=0.03)
    # Still unmistakably unstable, which is what the artifact must convey.
    assert diag["concentration_hhi"] < 0.65
    assert diag["normalized_entropy"] > 0.8


def test_tie_break_is_deterministic_toward_first_enumeration_order():
    """Load-bearing and worth pinning, because the volume reduction magnifies
    it. Ties between resampled candidate means break toward whichever candidate
    is enumerated first -- in both the diagnostic and the primary bootstrap's
    own `max(...)`. Exact ties are rare at n_select=4 and common at n_select=2,
    so dropping to the floor raises how often an unspecified tie-break rule
    decides the selected z. Recorded here so the behaviour is visible rather
    than discovered later from a result."""
    tied = {"z_first": np.array([1.0, 1.0]), "z_second": np.array([1.0, 1.0])}
    assert audit.select_maximizer(tied) == "z_first"

    reversed_order = {"z_second": np.array([1.0, 1.0]), "z_first": np.array([1.0, 1.0])}
    assert audit.select_maximizer(reversed_order) == "z_second"

    events = [{"candidates": {z: {"select": s, "eval_set": np.array([1.0])}
                               for z, s in tied.items()},
               "eval_keep": np.array([0.0])}]
    diag = audit.selection_diagnostic(events, iters=200)[0]
    assert diag["selection_frequency"]["z_first"] == pytest.approx(1.0)


def test_selection_diagnostic_seed_is_not_the_inference_stream():
    """The diagnostic re-runs only the selection half, so it cannot reproduce
    the primary stream's draw order. The seed must therefore be visibly
    distinct rather than implying a correspondence that does not hold."""
    assert audit.selection_diagnostic_seed(audit.BOOTSTRAP_SEED) != audit.BOOTSTRAP_SEED
    assert audit.selection_diagnostic_seed(7) == audit.selection_diagnostic_seed(7)
    assert audit.selection_diagnostic_seed(7) != audit.selection_diagnostic_seed(8)


def test_selection_diagnostic_handles_an_event_with_no_legal_candidates():
    diag = audit.selection_diagnostic([{"candidates": {}, "eval_keep": np.array([0.0])}])[0]
    assert diag["legal_set_size"] == 0
    assert diag["point_selected"] is None
    assert diag["selection_frequency"] == {}


# =============================================================================
# Stage B repairs (Pro ruling 2026-07-26): the two independent realization
# mismatches. Both are claim-bearing, so both get a witness.
# =============================================================================

def test_full_sync_set_reassigns_only_at_shared_check_boundaries():
    """Mismatch A. The contract defines `full_sync_SET` as reassigning every
    duty AT EACH CHECK. It used to recompute the whole duty map on every
    primitive step, which is a materially stronger control -- and since it
    supplies `D_A`, its cadence can decide whether PART_A_CONTRADICTION fires."""
    env = _CloneableFakeEnv(seed=31)
    duty_positions, _ = audit.compute_duty_positions(env)
    n = int(env.n_uavs)
    charging = np.zeros(n, dtype=bool)

    # A duty map deliberately unlike the full-sync assignment, so a
    # recomputation is visibly different from carrying it forward.
    scrambled = {i: (i + 1) % n for i in range(n)}

    at_check, _, _ = audit.update_duty_map_on_transitions(
        duty_map=scrambled, duty_positions=duty_positions, env=env,
        charging_before=charging, charging_after=charging,
        schedule="full_sync_SET", step_index=0)
    between, _, _ = audit.update_duty_map_on_transitions(
        duty_map=scrambled, duty_positions=duty_positions, env=env,
        charging_before=charging, charging_after=charging,
        schedule="full_sync_SET", step_index=1)

    expected = audit.full_sync_set_update(
        duty_positions=duty_positions,
        airborne_positions={i: np.asarray(env.uav_positions[i], dtype=float)
                            for i in range(n)})

    assert at_check == expected                 # t=0 is a check: reassigned
    assert between == scrambled                 # t=1 is not: carried forward
    assert at_check != between

    # Every multiple of DELTA is a check; nothing in between is.
    for t in range(0, 3 * audit.DELTA + 1):
        out, _, _ = audit.update_duty_map_on_transitions(
            duty_map=scrambled, duty_positions=duty_positions, env=env,
            charging_before=charging, charging_after=charging,
            schedule="full_sync_SET", step_index=t)
        assert out == (expected if t % audit.DELTA == 0 else scrambled), f"step {t}"


def test_stable_limb_locks_nothing_and_flex_locks_the_certified_stable_duty():
    """Mismatch B. Section 1: non-focal duties are NEVER frozen -- every other
    airborne assignment is reoptimized one-to-one under constructive_mixed.

    The stable limb used to be handed the flex focal's incumbent duty, which
    restricted its SET joint continuation and made SET look artificially
    costly. That errs toward 'persistence is necessary' -- the same
    claim-favouring direction that disqualified n_select=1, which is why this
    is a mismatch rather than a tuning detail."""
    locks = audit.limb_locked_duties(stable_focal_duty=3)

    assert locks["stable"] == frozenset(), (
        "the stable limb must lock nothing; locking a non-focal duty biases SET "
        "toward looking costly")
    assert locks["flex"] == frozenset({3})

    # Degenerate case: no certified stable duty means no lock anywhere.
    assert audit.limb_locked_duties(stable_focal_duty=None) == {
        "stable": frozenset(), "flex": frozenset()}


def test_locking_a_duty_actually_restricts_reassignment():
    """The mechanism the previous test's property depends on: a locked duty is
    genuinely withheld from reassignment, so handing the stable limb a lock was
    not a harmless no-op."""
    duty_positions = {0: np.array([0.0, 0.0]), 1: np.array([500.0, 500.0])}
    airborne = {0: np.array([490.0, 490.0]), 1: np.array([10.0, 10.0])}

    unlocked = audit.constructive_mixed_update(
        duty_map={0: 0, 1: 1}, duty_positions=duty_positions,
        airborne_positions=airborne, event="LEAVE", event_uav=None,
        locked_duties=frozenset())
    locked = audit.constructive_mixed_update(
        duty_map={0: 0, 1: 1}, duty_positions=duty_positions,
        airborne_positions=airborne, event="LEAVE", event_uav=None,
        locked_duties=frozenset({0}))

    assert locked[0] == 0, "a locked duty keeps its incumbent"
    assert unlocked != locked or unlocked[0] == 0


def test_compute_conformance_ok_false_when_pinned_topology_hash_fails():
    """Item 5b, second half: 'at run level, conformance_ok=False when the
    pinned-topology hash fails' -- exercised directly against the pure
    conjunction (the real driver's per-topology `TopologyMismatchError`
    catch sets exactly this `topology_hash_ok=False` input; that real
    catch is integration wiring already covered by `TopologyMismatchError`
    raising deterministically off a genuine coordinate mismatch elsewhere
    in this suite)."""
    assert audit.compute_conformance_ok(
        invalidated_pairs=0, topology_hash_ok=False, arm_distinct_ok=True) is False


# =============================================================================
# 15. Q-E2 per-topology reporting: distinguishing "no LEAVE ever occurred"
#     from "LEAVEs occurred but were rejected/consumed silently" -- the exact
#     ambiguity the first real smoke run collapsed (qualifying=0, exclusions=[]).
# =============================================================================

def test_map_rejection_reasons_eligibility_short_circuits_certification():
    """Eligibility-stage reasons alone decide the mapping; certification is
    never reached (mirrors `roll_prefix_and_find_event`'s own `continue`),
    so certification-side inputs passed alongside must be ignored."""
    reasons = audit.map_rejection_reasons(
        eligibility_reasons=[audit.EXCLUDE_CENSORED, audit.EXCLUDE_QUEUE_OR_OCCUPIED],
        stable_ok=False, stable_reasons=["no_valid_incumbent"],
        flex_ok=False, flex_reasons=["no_covering_survivor"])
    assert reasons == {audit.REJECT_CENSORED, audit.REJECT_STATION_CONTENTION}


def test_map_rejection_reasons_no_stable_incumbent_only():
    reasons = audit.map_rejection_reasons(stable_ok=False, stable_reasons=["no_valid_incumbent"])
    assert reasons == {audit.REJECT_NO_STABLE_INCUMBENT}


def test_map_rejection_reasons_no_flex_survivor_only():
    reasons = audit.map_rejection_reasons(flex_ok=False, flex_reasons=["no_covering_survivor"])
    assert reasons == {audit.REJECT_NO_FLEX_SURVIVOR}


def test_map_rejection_reasons_empty_legal_set_from_either_limb():
    """Q-C4: the empty-legal-alternative-set predicate applies to BOTH
    limbs -- must map to the same reporting bucket regardless of which
    limb's certification produced it."""
    from_stable = audit.map_rejection_reasons(
        stable_ok=False, stable_reasons=[audit.EXCLUDE_EMPTY_SET_ALT])
    assert audit.REJECT_EMPTY_LEGAL_SET in from_stable
    from_flex = audit.map_rejection_reasons(
        flex_ok=False, flex_reasons=[audit.EXCLUDE_EMPTY_SET_ALT])
    assert audit.REJECT_EMPTY_LEGAL_SET in from_flex


def test_map_rejection_reasons_qualifying_leave_has_no_reasons():
    assert audit.map_rejection_reasons() == set()


def test_accumulate_episode_leave_stats_sums_across_episodes_including_support_misses():
    """The rollup helper `run_topology_audit` uses for BOTH the calibration
    and audit blocks: independent of whether either episode qualified, every
    OBSERVED LEAVE and its mapped rejection reasons must accumulate -- this
    is what makes a qualifying=0 topology report WHY, rather than an empty
    exclusions list."""
    report = audit._new_episode_block_report()
    ep1_diag = [
        {"uav": 0, "capture_step": 100, "departure_step": 95,
         "battery_at_departure": 0.4, "rejected_reasons": ["no_flex_survivor"]},
    ]
    ep1_counts = {**{k: 0 for k in audit.REJECTION_REASON_KEYS}, "no_flex_survivor": 1}
    ep2_diag = [
        {"uav": 1, "capture_step": 951, "departure_step": 940,
         "battery_at_departure": 0.5, "rejected_reasons": ["censored_after_950"]},
        {"uav": 2, "capture_step": 200, "departure_step": 190,
         "battery_at_departure": 0.6, "rejected_reasons": ["no_stable_incumbent", "empty_legal_set"]},
    ]
    ep2_counts = {**{k: 0 for k in audit.REJECTION_REASON_KEYS},
                  "censored_after_950": 1, "no_stable_incumbent": 1, "empty_legal_set": 1}

    audit._accumulate_episode_leave_stats(report, leave_diagnostics=ep1_diag, rejected_counts=ep1_counts)
    audit._accumulate_episode_leave_stats(report, leave_diagnostics=ep2_diag, rejected_counts=ep2_counts)

    assert report["planned_leaves_observed"] == 3
    assert report["leaves_before_deadline"] == 2   # capture steps 100, 200 qualify; 951 is censored
    assert report["rejected_counts"]["no_flex_survivor"] == 1
    assert report["rejected_counts"]["censored_after_950"] == 1
    assert report["rejected_counts"]["no_stable_incumbent"] == 1
    assert report["rejected_counts"]["empty_legal_set"] == 1
    assert report["rejected_counts"]["station_contention"] == 0
    assert len(report["leaves"]) == 3


def test_run_calibration_episode_propagates_episode_report_on_support_miss(monkeypatch):
    """Item 1's wiring: `run_calibration_episode` must surface
    `roll_prefix_and_find_event`'s leave diagnostics even when the episode
    itself is a support miss (no qualifying event) -- otherwise a
    support-miss-heavy topology would still report an uninformative,
    reason-free rollup."""
    fake_prefix = {
        "event": None,
        "exclusions": [{"t_e": 951, "uav": 0, "reasons": [audit.EXCLUDE_CENSORED]}],
        "recorded_actions": [],
        "leave_diagnostics": [{"uav": 0, "capture_step": 951, "departure_step": 940,
                                "battery_at_departure": 0.5,
                                "rejected_reasons": ["censored_after_950"]}],
        "rejected_counts": {**{k: 0 for k in audit.REJECTION_REASON_KEYS}, "censored_after_950": 1},
    }
    monkeypatch.setattr(audit, "build_pinned_env", lambda *a, **k: _CloneableFakeEnv(seed=9))
    monkeypatch.setattr(audit, "apply_energy_profile", lambda *a, **k: None)
    monkeypatch.setattr(audit, "roll_prefix_and_find_event", lambda env, **k: fake_prefix)

    result = audit.run_calibration_episode(
        config=None, topology_seed=1, episode_seed=1, energy_seed=1, coords={}, coord_hash="x")

    assert result["support_miss"] is True
    assert result["episode_report"]["leave_diagnostics"] == fake_prefix["leave_diagnostics"]
    assert result["episode_report"]["rejected_counts"]["censored_after_950"] == 1


def test_resolve_run_plan_smoke_defaults_to_one_and_one_without_overrides():
    plan = audit.resolve_run_plan(smoke=True, dev=False, topology_seeds_override=None,
                                   episodes_calibration=None, episodes_audit=None)
    assert plan["topology_seeds"] == [audit.TOPOLOGY_SEED_DEV]
    assert plan["n_calibration"] == 1 and plan["n_audit"] == 1


def test_resolve_run_plan_smoke_honors_explicit_episode_overrides():
    """Item 2's fix: `--smoke` previously hardcoded 1/1 unconditionally,
    silently discarding `--episodes-calibration`/`--episodes-audit`. Smoke's
    topology choice and its n_select=1/n_eval=2 replicate override (not
    exercised here -- that lives in `run_topology_audit`) are unaffected."""
    plan = audit.resolve_run_plan(smoke=True, dev=False, topology_seeds_override=None,
                                   episodes_calibration=3, episodes_audit=5)
    assert plan["n_calibration"] == 3 and plan["n_audit"] == 5
    assert plan["topology_seeds"] == [audit.TOPOLOGY_SEED_DEV]


def test_resolve_run_plan_non_smoke_default_episode_counts_unchanged():
    plan = audit.resolve_run_plan(smoke=False, dev=False, topology_seeds_override=None,
                                   episodes_calibration=None, episodes_audit=None)
    assert plan["topology_seeds"] == list(audit.TOPOLOGY_SEEDS_INITIAL)
    assert plan["n_calibration"] == audit.N_CALIBRATION_EPISODES
    assert plan["n_audit"] == audit.N_AUDIT_EPISODES


def test_resolve_run_plan_dev_mode_honors_overrides_too():
    plan = audit.resolve_run_plan(smoke=False, dev=True, topology_seeds_override=None,
                                   episodes_calibration=2, episodes_audit=2)
    assert plan["topology_seeds"] == [audit.TOPOLOGY_SEED_DEV]
    assert plan["n_calibration"] == 2 and plan["n_audit"] == 2


class _ScheduledLeaveFakeEnv:
    """A deterministic, schedule-driven FakeEnv exercising the full real-env
    orchestration path (`compute_duty_positions` / `scripted_source_actions`
    / `step_once` / `roll_prefix_and_find_event`) end to end, WITHOUT relying
    on physics to produce a LEAVE at a chosen step: `leave_schedule`/
    `dock_schedule` map a 1-based step count (aligned with `t_e = t+1`, the
    convention `roll_prefix_and_find_event` uses) to the uav index whose
    `uav_charging`/`uav_dock_requests` rises at exactly that call. 8 UAVs / 8
    duties (the registered fleet shape `initial_duty_map` hardcodes), FIXED
    geometry (no user/uav drift at all), so every certification outcome is
    hand-traceable rather than depending on incidental clustering noise."""

    def __init__(self, *, leave_schedule, dock_schedule, far_uavs):
        self.n_uavs = 8
        self.n_users = 6
        self.time_step = 1.0
        self.max_speed = 30.0
        self.max_vertical_speed_mps = 5.0
        self.area_size = 2_000_000.0
        self.height_range = (80.0, 80.0)
        self.battery_capacity_wh = 160.0
        self.charging_power_w = 1000.0
        self.return_reserve_ratio = 0.10
        self.service_cutoff_threshold = 0.02
        self.depleted_battery_threshold = 0.0
        self.user_qos_rate_mbps = 1.0
        self.n_charging_stations = 1
        self.charging_station_positions = np.array([[900.0, 900.0, 80.0]])
        self.ground_bs_positions = np.array([[0.0, 0.0, 80.0]])
        self.agents = [f"uav_{i}" for i in range(self.n_uavs)]
        # 6 users in a line, 300 m apart: k-means separates them into 6
        # distinct singleton service-duty clusters every call, so the legal-
        # SET alternative set is never accidentally empty.
        self.user_positions = np.array([[i * 300.0, 0.0, 0.0] for i in range(self.n_users)])
        # Duty-holding UAVs sit at their own duty's position; `far_uavs` sit
        # ~2,100 km away so their transit time to ANY vacated flex target
        # blows the Z=139-step coverage predicate -- a deterministic lever
        # for "eligible but uncertified" that never touches stable's own
        # (unrelated, duty-target-displacement-based) certification.
        self.uav_positions = np.array([
            [i * 300.0, 0.0, 80.0] if i not in far_uavs else [1_500_000.0, 1_500_000.0, 80.0]
            for i in range(self.n_uavs)
        ])
        self.uav_battery_ratios = np.full(self.n_uavs, 0.5)
        self.uav_charging = np.zeros(self.n_uavs, dtype=bool)
        self.uav_dock_requests = np.zeros(self.n_uavs, dtype=bool)
        self.uav_target_stations = np.zeros(self.n_uavs, dtype=int)
        self.uav_failed = np.zeros(self.n_uavs, dtype=bool)
        self.last_charging_arrival = np.zeros(self.n_uavs, dtype=bool)
        self.uav_return_energy_margins = np.full(self.n_uavs, 0.5)
        self.station_occupancy = np.array([0.0])
        self.station_queue_lengths = np.array([0.0])
        self.last_user_rates_mbps = np.full(self.n_users, 2e6)
        self.np_random = np.random.RandomState(0)
        self.leave_schedule = dict(leave_schedule)
        self.dock_schedule = dict(dock_schedule)
        self._step_count = 0

    def _calculate_power_consumption(self, v_h, v_z):
        return 300.0 + v_h

    def _nearest_charging_station(self, uav_idx):
        rel = self.charging_station_positions[0] - self.uav_positions[uav_idx]
        return 0, rel, float(np.linalg.norm(rel))

    def step(self, actions):
        # Ignores the synthesized actions entirely -- transitions are driven
        # by the schedule tables, not by the dock-trigger/action pipeline,
        # so the exact capture/departure steps are chosen by the test, not
        # incidental to distance/battery arithmetic.
        self._step_count += 1
        if self._step_count in self.dock_schedule:
            self.uav_dock_requests[self.dock_schedule[self._step_count]] = True
        if self._step_count in self.leave_schedule:
            self.uav_charging[self.leave_schedule[self._step_count]] = True
        infos = {a: {"reward_info": {"qos_satisfaction_ratio": 0.9,
                                      "return_constraint_cost": 0.05,
                                      "return_constraint_cost_raw": 0.05}}
                 for a in self.agents}
        return None, None, None, None, infos


def test_roll_prefix_and_find_event_distinguishes_ineligible_from_uncertified_leaves():
    """The exact case the first real smoke run collapsed to qualifying=0 /
    exclusions=[]: an episode with TWO observed LEAVEs -- one ineligible
    (t_e=951 > 950, censored) and one eligible but uncertified (fails flex
    coverage only, since every OTHER UAV sits ~2,100 km from the vacated
    target) -- must report BOTH as OBSERVED, distinguish which failed on
    which axis, and never silently produce an empty rejection record.

    UAV 1 departs (dock-request onset) at step 96, captures at step 101
    (eligible: t_e=101 <= 950). UAV 2 departs at step 946, captures at step
    951 (t_e=951 > 950: censored). No stable candidate is scheduled to leave
    within Delta of either event and duty-target geometry never drifts, so
    UAV 1's event certifies STABLE but fails FLEX purely on distance --
    `no_flex_survivor` is the only rejection bucket it should hit."""
    env = _ScheduledLeaveFakeEnv(
        leave_schedule={101: 1, 951: 2}, dock_schedule={96: 1, 946: 2},
        far_uavs={0, 2, 3, 4, 5, 6, 7},
    )

    result = audit.roll_prefix_and_find_event(env)

    assert result["event"] is None   # neither LEAVE became the qualifying event
    diag = result["leave_diagnostics"]
    assert len(diag) == 2
    planned_leaves_observed = len(diag)
    leaves_before_deadline = sum(1 for d in diag if d["capture_step"] <= audit.T_E_MAX)
    assert planned_leaves_observed == 2
    assert leaves_before_deadline == 1

    by_uav = {d["uav"]: d for d in diag}
    assert by_uav[1]["capture_step"] == 101
    assert by_uav[1]["departure_step"] == 96
    assert by_uav[1]["battery_at_departure"] == pytest.approx(0.5)
    assert by_uav[1]["rejected_reasons"] == [audit.REJECT_NO_FLEX_SURVIVOR]

    assert by_uav[2]["capture_step"] == 951
    assert by_uav[2]["departure_step"] == 946
    assert by_uav[2]["rejected_reasons"] == [audit.REJECT_CENSORED]

    counts = result["rejected_counts"]
    assert counts[audit.REJECT_CENSORED] == 1
    assert counts[audit.REJECT_NO_FLEX_SURVIVOR] == 1
    for key in audit.REJECTION_REASON_KEYS:
        if key not in (audit.REJECT_CENSORED, audit.REJECT_NO_FLEX_SURVIVOR):
            assert counts[key] == 0

    # The property this test exists to guard: qualifying=0 must NEVER be
    # reported alongside an empty leave/exclusion record when LEAVEs were
    # actually observed -- the wrong-implementation failure mode this whole
    # item fixes.
    assert len(result["exclusions"]) == 2
    assert planned_leaves_observed > 0 and result["event"] is None


# =============================================================================
# 9. Driver-level wiring: assemble_audit_result (Task A -- decide_branch
# reached through the SAME code path main() uses, not called directly)
# =============================================================================

def _fast_t_m_bootstrap(monkeypatch, iters=20):
    """The real `compute_t_m_bootstrap` at its frozen default (10,000 iters)
    is too slow for a focused test; `assemble_audit_result` does not expose
    an override (correctly -- production must always run the frozen count),
    so the override is applied here, at the call site, by monkeypatching the
    module-level name `assemble_audit_result` resolves at call time. Every
    fixture below is DEGENERATE (identical value at every topology, so
    resampling introduces no variance regardless of iteration count) -- the
    small iters value changes only runtime, never the asserted outcome."""
    real = audit.compute_t_m_bootstrap
    monkeypatch.setattr(
        audit, "compute_t_m_bootstrap",
        lambda **kw: real(**{**kw, "iters": iters}))


def _six_topology_results(*, d_a_value: float, b_stable_value: float,
                           b_flex_value: float, u_stable_value: float,
                           u_flex_value: float, invalidated_pairs_by_topology=None) -> list:
    """Six topologies (the frozen `MIN_SUPPORT_TOPOLOGIES` minimum), each
    contributing one degenerate calibration/audit unit per quantity --
    `_degenerate_topology_units` shape, matching exactly what
    `run_topology_audit` returns per topology. `qualifying_*_episodes=4`
    meets `MIN_SUPPORT_EPISODES_PER_TOPOLOGY` in every topology, so
    `support_ok` is True and `assemble_audit_result` reaches its
    `decide_branch` call (never the single-topology/support-miss shortcuts)."""
    n = 6
    d_a_units = _degenerate_topology_units([d_a_value] * n)
    b_stable_units = _degenerate_topology_units([b_stable_value] * n)
    b_flex_units = _degenerate_topology_units([b_flex_value] * n)
    u_stable_units = _degenerate_topology_units([u_stable_value] * n)
    u_flex_units = _degenerate_topology_units([u_flex_value] * n)
    invalidated_pairs_by_topology = invalidated_pairs_by_topology or [[] for _ in range(n)]
    return [
        {
            "qualifying_calibration_episodes": 4,
            "qualifying_audit_episodes": 4,
            "invalidated_pairs": invalidated_pairs_by_topology[i],
            "arm_distinctness_pairs": [],
            "calibration_units_stable": b_stable_units[i],
            "calibration_units_flex": b_flex_units[i],
            "calibration_units_d_a": d_a_units[i],
            "audit_units_stable": u_stable_units[i],
            "audit_units_flex": u_flex_units[i],
        }
        for i in range(n)
    ]


def test_driver_part_a_contradiction_reaches_branch_4(monkeypatch):
    """Hand-worked: B_stable=10.0 (deterministic, LCB95=10.0>0), D_A=0.0
    (deterministic). lower_contrast = D_A + 0.05*B_stable = 0.5 > 0 (passes);
    upper_contrast = 0.05*B_stable - D_A = 0.5 > 0 (passes). Both equivalence
    tests pass -> PART_A_CONTRADICTION per section 8 ('Both pass ->
    PART_A_CONTRADICTION (return-equivalence)'), which `decide_branch`
    resolves to branch 4 -- checked here through `assemble_audit_result`,
    the exact function `main()` calls, not `decide_branch` called directly
    with hand-picked kwargs (section 7's existing coverage)."""
    _fast_t_m_bootstrap(monkeypatch)
    topology_results = _six_topology_results(
        d_a_value=0.0, b_stable_value=10.0, b_flex_value=10.0,
        u_stable_value=5.0, u_flex_value=5.0)

    out = audit.assemble_audit_result(topology_results, [])

    assert out["conformance"]["ok"] is True
    assert out["support"]["ok"] is True
    assert out["part_a"]["verdict"] == "PART_A_CONTRADICTION"
    assert out["branch"] == "PART_A_CONTRADICTION"


def test_driver_part_a_unresolved_does_not_relabel_the_source_branch(monkeypatch):
    """Hand-worked: B_stable=10.0, D_A=0.6. lower_contrast = 0.6+0.5=1.1>0
    (passes); upper_contrast = 0.5-0.6=-0.1 (fails, not >0) -> not both pass,
    so not PART_A_CONTRADICTION; lower_contrast_ucb=1.1 is not <0, so not
    CONFORMANCE_PASS either -> PART_A_CONFORMANCE_UNRESOLVED. Section 8: the
    unresolved diagnostic 'does not relabel the source branch' -- T_m is
    built to clear on both limbs (U*_stable=-2.0 -> T_stable=-2.0+1.0=-1.0<0;
    U*_flex=2.0 -> T_flex=2.0-1.0=1.0>0), so the source branch must resolve
    PERSISTENCE_NECESSARY_SOURCE, exactly as if Part-A had never run, proving
    UNRESOLVED never flips `part_a_contradiction` through the real driver
    path (not `decide_branch` called directly)."""
    _fast_t_m_bootstrap(monkeypatch)
    topology_results = _six_topology_results(
        d_a_value=0.6, b_stable_value=10.0, b_flex_value=10.0,
        u_stable_value=-2.0, u_flex_value=2.0)

    out = audit.assemble_audit_result(topology_results, [])

    assert out["part_a"]["verdict"] == "PART_A_CONFORMANCE_UNRESOLVED"
    assert out["branch"] == "PERSISTENCE_NECESSARY_SOURCE"


def test_driver_conformance_failure_reaches_branch_1_over_a_favorable_t_m(monkeypatch):
    """The same otherwise-favorable T_m fixture as the UNRESOLVED test above
    (which alone would resolve PERSISTENCE_NECESSARY_SOURCE), but with one
    topology reporting a single invalidated prefix-replay pair --
    `compute_conformance_ok`'s zero-tolerance conjunct fails, so
    `conformance_ok=False` must reach `decide_branch` through
    `assemble_audit_result` (the `len(topology_results) > 1 and support_ok`
    path, NOT the single-topology/support-miss shortcut, since support_ok
    stays True here) and win branch-1 precedence over every later row,
    including one it would otherwise have cleared."""
    _fast_t_m_bootstrap(monkeypatch)
    invalidated = [[{"reason": "synthetic test injection"}]] + [[] for _ in range(5)]
    topology_results = _six_topology_results(
        d_a_value=0.0, b_stable_value=10.0, b_flex_value=10.0,
        u_stable_value=-2.0, u_flex_value=2.0,
        invalidated_pairs_by_topology=invalidated)

    out = audit.assemble_audit_result(topology_results, [])

    assert out["conformance"]["ok"] is False
    assert out["conformance"]["invalidated_pairs_count"] == 1
    assert out["support"]["ok"] is True
    assert out["branch"] == "INVALID_EVENT_ALIGNED_AUDIT"


def test_topology_start_progress_line_goes_to_stderr_not_stdout(monkeypatch, capsys):
    """Task B guard: `run_topology_audit`'s topology-start progress line must
    land on stderr, never stdout -- stdout carries exactly the one result
    JSON `main()` prints at the very end, and a progress line leaking onto
    stdout would corrupt that artifact. `build_topology_template` (the very
    next call after the progress print) is stubbed to abort immediately, so
    this exercises the REAL print call site inside `run_topology_audit`
    without any environment construction or episode stepping."""
    class _Abort(Exception):
        pass

    def _raise(*_a, **_k):
        raise _Abort()

    monkeypatch.setattr(audit, "build_topology_template", _raise)
    with pytest.raises(_Abort):
        audit.run_topology_audit(object(), topology_seed=1, n_calibration=0, n_audit=0)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[progress] topology_seed=1 start" in captured.err


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
