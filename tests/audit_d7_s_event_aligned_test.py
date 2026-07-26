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


def test_run_audit_event_excludes_an_invalidated_replicate_and_reports_it(monkeypatch):
    """Item 5b, first half: an injected `PrefixReplayMismatchError` on
    exactly one KEEP evaluation replicate must exclude ONLY that pair (the
    eval array shrinks by one) and report it via `invalidated_pairs`,
    never silently repaired and never crashing the whole audit event."""
    calls = {"n": 0}

    def _flaky_replay_prefix(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise audit.PrefixReplayMismatchError("injected mismatch")
        return _CloneableFakeEnv(seed=5)

    monkeypatch.setattr(audit, "replay_prefix", _flaky_replay_prefix)

    env_for_geometry = _CloneableFakeEnv(seed=5)
    duty_positions, centroids = audit.compute_duty_positions(env_for_geometry)
    duty_map = {i: i for i in range(env_for_geometry.n_uavs)}
    event = {
        "hash_at_te": "irrelevant", "duty_map_at_te": duty_map,
        "duty_positions_at_te": duty_positions, "service_centroids_at_te": centroids,
        "focal_stable_uav": 0, "legal_targets": {"stable": {}},
        "locked_duties": {"stable": frozenset()},
    }
    result = audit.run_audit_event(
        config=None, topology_seed=1, episode_seed=1, coords=None, coord_hash="x",
        recorded_actions=[], energies=None, event=event, limb="stable",
        n_select=1, n_eval=4)

    assert len(result["eval_keep"]) == 3          # one of the 4 requested replicates excluded
    assert len(result["invalidated_pairs"]) == 1
    assert result["invalidated_pairs"][0]["candidate_id"] == "KEEP"
    assert result["invalidated_pairs"][0]["phase"] == "evaluate"


def test_run_calibration_episode_excludes_the_whole_episode_on_a_replay_mismatch(monkeypatch):
    """Item 3/5b: a `PrefixReplayMismatchError` on any one schedule's
    fresh-env prefix replay invalidates the WHOLE calibration episode (every
    schedule shares the identical recorded prefix/expected hash, so a
    divergence means the fixed-history guarantee itself failed for this
    episode) -- reported via `invalidated_pairs`, and the episode
    contributes to neither `B_m` nor `D_A`, never repaired or retried."""
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

    calls = {"n": 0}

    def _flaky_replay_prefix(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] >= 2:   # first schedule call succeeds, every one after fails
            raise audit.PrefixReplayMismatchError("injected mismatch")
        return _CloneableFakeEnv(seed=2)

    monkeypatch.setattr(audit, "replay_prefix", _flaky_replay_prefix)

    result = audit.run_calibration_episode(
        config=None, topology_seed=1, episode_seed=1, energy_seed=1, coords={}, coord_hash="x")

    assert result["support_miss"] is False
    assert result["invalidated"] is True
    assert len(result["invalidated_pairs"]) == 2   # stable/null + flex/constructive_mixed
    assert result["results"] == {}                  # neither limb contributes B_m or D_A


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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
