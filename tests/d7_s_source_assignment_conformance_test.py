"""D7.S source-assignment conformance suite — AMENDED, frozen before the repair.

Amended on Pro's ruling of 2026-07-30
(`docs/external-review/rounds/20260730_d7_s_conformance_suite_freeze/21_PRO_OPEN_RAW.md`),
which returned **FREEZE AFTER MODIFICATION — step 1 is NOT closed** on the first
version, with five blocking issues:

    N5 contradicts fail-closed injectivity;
    provenance omits IDLE_OR_OTHER;
    the provenance path is not bound to production;
    N1/N2/N6 are observations rather than rejection tests;
    final acceptance can pass with provenance cases still XFAIL.

## The defect the amendments fix

Three of the five were one shape: **a check that never touches the thing it
protects.** N1 asserted a duplicate map is non-injective; N2 asserted a lossy
inversion loses. Both true by construction, and neither could fail if the guard
were deleted. Every negative below now drives a **production entry point** and
requires a **registered, specifically-classified** rejection.

Pro's phrasing is the one to keep: *a named validator that is never invoked by
production is no protection.*

## Fail-closed acceptance — the marks cannot be trusted

`pytest.mark.xfail(condition, strict=True)` is INACTIVE when `condition` is
false, so a passing test is an ordinary PASS, never `XPASS(strict)`. Verified:

    conditional xfail, condition False, test passes  -> PASS
    unconditional strict xfail, test passes          -> XPASS(strict) -> FAILED

An earlier docstring here claimed the conditional form goes red on its own. It
does not. Therefore final acceptance MUST be fail-closed:

    pytest --runxfail ...            requiring every test to pass
  or
    0 failed, 0 xfailed, 0 xpassed, 0 skipped   plus the hard sentinel below

A run is **not** green while provenance cases remain XFAIL. The older
UNCONDITIONAL strict xfail `test_rejoin_never_gives_one_uav_a_second_duty` in
`audit_d7_s_event_aligned_test.py` must be removed or converted in the same
atomic repair, or the full suite will correctly fail on XPASS.

## Frozen semantic objects (not realization bindings)

Protected: exhaustive and mutually exclusive source classification; one record
per action; duty identity on `DUTY(d)`; production integration; fail-closed
behaviour on invalid assignments. The symbol names below are **realization
bindings** — changing a name alone needs no new scientific review.

    exactly one action-source record per physical UAV action

    DUTY(d)          target selected from duty_positions[d]
    CHARGING         docked in place
    STATION_RETURN   energy-directed station motion
    OVERRIDE         intervention forced the target (takes precedence)
    IDLE_OR_OTHER    no-duty stationary action

    SourceAssignmentInvariantError with a specific `reason`, e.g.
        NONINJECTIVE_RAW_ASSIGNMENT
        DUPLICATE_HOLDER

Nothing here may be relaxed to reach green. Relaxing a predicate is the specific
prohibited repair.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import audit_d7_s_event_aligned as audit  # noqa: E402

PROVENANCE_FN = "scripted_source_actions_with_provenance"
VALIDATOR_FN = "assert_partial_injection"
ERROR_CLS = "SourceAssignmentInvariantError"
COVERAGE_FN = "executable_covered_duties"

_HAS_PROV = hasattr(audit, PROVENANCE_FN)
_HAS_VALIDATOR = hasattr(audit, VALIDATOR_FN)
_HAS_ERROR = hasattr(audit, ERROR_CLS)
_HAS_COVERAGE = hasattr(audit, COVERAGE_FN)

needs_prov = pytest.mark.xfail(
    not _HAS_PROV, strict=True,
    reason=f"frozen before the repair: `{PROVENANCE_FN}` is contract, not yet built")
needs_validator = pytest.mark.xfail(
    not (_HAS_VALIDATOR and _HAS_ERROR), strict=True,
    reason=f"frozen before the repair: `{VALIDATOR_FN}` / `{ERROR_CLS}` not yet built")
needs_coverage = pytest.mark.xfail(
    not (_HAS_COVERAGE and _HAS_PROV), strict=True,
    reason=f"frozen before the repair: `{COVERAGE_FN}` not yet built")


# =============================================================================
# HARD SENTINEL -- unmarked, so the suite cannot be called green pre-repair
# =============================================================================

def test_sentinel_the_repair_surface_exists():
    """Unmarked and hard. Pro: final acceptance may not be accepted as green
    while provenance cases remain XFAIL, so one case must fail unconditionally
    until the repair lands. This is it."""
    missing = [n for n, present in (
        (PROVENANCE_FN, _HAS_PROV), (VALIDATOR_FN, _HAS_VALIDATOR),
        (ERROR_CLS, _HAS_ERROR), (COVERAGE_FN, _HAS_COVERAGE)) if not present]
    assert not missing, f"repair surface absent: {missing}"


# =============================================================================
# Helpers
# =============================================================================

def _positions(n):
    return {d: np.array([100.0 * d, 0.0, 100.0]) for d in range(n)}


def _is_partial_injection(m):
    holders = list(m.values())
    return len(holders) == len(set(holders))


def _invariant_error():
    return getattr(audit, ERROR_CLS, Exception)


class _Env:
    """Minimal pre-action state. Attributes are set per test; nothing is
    inferred, so a case cannot pass because the double happened to agree."""
    def __init__(self, n=3, charging=None, batteries=None, positions=None):
        self.n_uavs = n
        self.time_step = 1.0
        self.max_speed = 20.0
        self.max_vertical_speed_mps = 5.0
        self.uav_positions = positions or {i: np.array([10.0 * i, 0.0, 100.0]) for i in range(n)}
        self.uav_battery_ratios = np.array(batteries if batteries is not None else [0.9] * n)
        self.uav_charging = np.array(charging if charging is not None else [False] * n)
        self.charging_station_positions = {0: np.array([0.0, 0.0, 0.0])}
        self.battery_capacity_wh = 100.0

    def _nearest_charging_station(self, i):
        return 0, np.array([0.0, 0.0, 0.0]), 10.0


# =============================================================================
# Positive witnesses
# =============================================================================

def test_p1_unassigned_rejoiner_fills_one_nearest_uncovered_duty():
    dp = _positions(2)
    ap = {0: np.array([0.0, 0.0, 0.0]), 2: np.array([90.0, 0.0, 0.0])}
    out = audit.constructive_mixed_update(
        duty_map={}, duty_positions=dp, airborne_positions=ap,
        event="REJOIN", event_uav=2)
    assert out.get(1) == 2
    assert len([d for d, u in out.items() if u == 2]) == 1
    assert _is_partial_injection(out)


def test_p2_already_assigned_rejoiner_receives_no_second_duty():
    dp = _positions(2)
    ap = {0: np.array([0.0, 0.0, 0.0]), 2: np.array([90.0, 0.0, 0.0])}
    out = audit.constructive_mixed_update(
        duty_map={0: 2}, duty_positions=dp, airborne_positions=ap,
        event="REJOIN", event_uav=2)
    held = [d for d, u in out.items() if u == 2]
    assert len(held) == 1, f"UAV 2 holds {held} in {out}"
    assert _is_partial_injection(out)


def _batch(m0, charging_before, charging_after, n, ndut):
    class _E:
        n_uavs = n
        uav_positions = {i: np.array([10.0 * i, 0.0, 0.0]) for i in range(n)}
    return audit.update_duty_map_on_transitions(
        duty_map=dict(m0), duty_positions=_positions(ndut), env=_E(),
        charging_before=np.array(charging_before),
        charging_after=np.array(charging_after),
        schedule="constructive_mixed", step_index=0)


def test_p3_simultaneous_leave_rejoin_batch_ends_injective():
    out, leaves, rejoins = _batch({0: 0, 1: 1, 2: 2},
                                  [False, False, False, True],
                                  [False, True, False, False], 4, 4)
    assert leaves == [1] and rejoins == [3]
    assert _is_partial_injection(out), f"batch ended non-injective: {out}"


def test_p4a_multiple_already_assigned_rejoiners_are_skipped_deterministically():
    """Pro: deterministic omission is still deterministic and injective, so
    injectivity alone is not enough. Assert the registered semantics."""
    args = ({0: 0, 1: 1}, [False, False, True, True, False],
            [False, True, False, False, False], 5, 5)
    first, _lv, rj = _batch(*args)
    second, _lv2, _rj2 = _batch(*args)
    assert first == second, "multiple-rejoin processing is not deterministic"
    assert _is_partial_injection(first), f"non-injective: {first}"
    assert sorted(rj) == [2, 3]
    for u in rj:
        held = [d for d, holder in first.items() if holder == u]
        assert len(held) <= 1, f"rejoiner {u} holds {held}"
    # Deterministic omission must not masquerade as success: every survivor that
    # can hold a duty does, so the covered count is pinned rather than free.
    assert len(first) == 4, f"expected 4 covered duties (4 airborne), got {first}"


def test_p4b_unassigned_rejoiners_fill_uncovered_duties_deterministically():
    """The complementary situation: rejoiners the LEAVE rematch did NOT place."""
    dp = _positions(4)
    ap = {1: np.array([100.0, 0.0, 0.0]), 2: np.array([200.0, 0.0, 0.0])}
    m = {0: 3}
    runs = []
    for _ in range(2):
        cur = dict(m)
        for u in (1, 2):
            cur = audit.constructive_mixed_update(
                duty_map=cur, duty_positions=dp, airborne_positions=ap,
                event="REJOIN", event_uav=u)
        runs.append(cur)
    assert runs[0] == runs[1], "rejoin order is not canonical"
    assert _is_partial_injection(runs[0]), f"non-injective: {runs[0]}"
    assert len(runs[0]) == 3, f"two unassigned rejoiners must cover two more duties: {runs[0]}"


def test_p5_leave_regression_reduced_fleet_and_locked_incumbent():
    """Green before AND after. Pro: a green regression witness belongs in a
    red-to-green suite -- it is what detects an over-broad repair, and it
    protects the choice of (b1) over (b2)."""
    dp = _positions(3)
    ap = {0: np.array([0.0, 0.0, 0.0]), 2: np.array([200.0, 0.0, 0.0])}
    out = audit.constructive_mixed_update(
        duty_map={0: 0, 1: 1, 2: 2}, duty_positions=dp, airborne_positions=ap,
        event="LEAVE", event_uav=1, locked_duties=frozenset({2}))
    assert out[2] == 2, "locked incumbent not preserved"
    assert 1 not in out.values(), "the leaver retained a duty"
    assert _is_partial_injection(out)
    assert len(out) == 2


@needs_prov
def test_p6a_producer_one_record_per_action_and_tag_matches_branch():
    """Producer correctness: independently predict the branch, compare the tag."""
    fn = getattr(audit, PROVENANCE_FN)
    env = _Env(n=4, charging=[False, True, False, False], batteries=[0.9, 0.5, 0.02, 0.9])
    dp = _positions(4)
    duty_map = {0: 0, 3: 3}
    actions, prov = fn(env, duty_map=duty_map, duty_positions=dp,
                       target_override={3: np.array([5.0, 5.0, 100.0])})
    assert set(prov.keys()) == set(range(env.n_uavs)), "one record per UAV action"
    assert len(prov) == len(actions), "record count must equal action count"
    assert prov[0][0] == "DUTY" and prov[0][1] == 0
    assert prov[1][0] == "CHARGING", "docked UAV must be CHARGING"
    assert prov[2][0] in ("STATION_RETURN", "IDLE_OR_OTHER")
    assert prov[3][0] == "OVERRIDE", "override takes precedence"


@needs_prov
def test_p6b_idle_or_other_exists_for_a_dutyless_uav():
    """Pro: the enum omitted the ordinary no-duty stationary branch."""
    fn = getattr(audit, PROVENANCE_FN)
    env = _Env(n=2)
    actions, prov = fn(env, duty_map={0: 0}, duty_positions=_positions(1))
    assert prov[1][0] == "IDLE_OR_OTHER", f"dutyless UAV tagged {prov[1]}"
    idle = np.asarray(actions[audit.agent_name(1)], dtype=float)
    assert float(idle[3]) == 0.0, "IDLE_OR_OTHER must not request docking"


@needs_prov
def test_p6c_action_consistency_the_action_matches_its_claimed_source():
    """The returned action must be the action the claimed source implies."""
    fn = getattr(audit, PROVENANCE_FN)
    env = _Env(n=2, charging=[True, False], batteries=[0.5, 0.9])
    dp = _positions(2)
    actions, prov = fn(env, duty_map={1: 1}, duty_positions=dp)
    assert prov[0][0] == "CHARGING"
    assert float(np.asarray(actions[audit.agent_name(0)])[3]) == 1.0, \
        "CHARGING holds position and requests docking"
    assert prov[1][0] == "DUTY" and prov[1][1] == 1
    assert float(np.asarray(actions[audit.agent_name(1)])[3]) == 0.0, \
        "a DUTY action must not request docking"


@needs_prov
def test_p6d_provenance_actions_are_bit_identical_to_the_production_path():
    """One canonical generator must own both outputs. Duplicated action logic in
    two functions is explicitly not acceptable."""
    fn = getattr(audit, PROVENANCE_FN)
    env = _Env(n=3)
    dp = _positions(3)
    duty_map = {0: 0, 1: 1, 2: 2}
    plain = audit.scripted_source_actions(env, duty_map=duty_map, duty_positions=dp)
    withprov, _prov = fn(env, duty_map=duty_map, duty_positions=dp)
    for k in plain:
        assert np.array_equal(np.asarray(plain[k], dtype=float),
                              np.asarray(withprov[k], dtype=float)), \
            f"action for {k} differs between the two projections"


@needs_prov
def test_p6e_the_conclusion_bearing_path_carries_provenance_forward():
    """Pro: a standalone correct wrapper no conclusion-bearing path uses is
    insufficient. `step_once` must expose or consume this exact provenance."""
    import inspect
    src = inspect.getsource(audit.step_once)
    assert PROVENANCE_FN in src, (
        "step_once still calls the actions-only generator; provenance is decorative")


# =============================================================================
# Paired negatives -- each drives PRODUCTION and requires a classified refusal
# =============================================================================

@needs_validator
def test_n1_old_rejoin_output_is_rejected_by_the_named_validator():
    """Pro: N1 previously proved only that the test helper recognises a
    duplicate. It must now require the registered invalid-realization failure
    from production's own validator."""
    validator = getattr(audit, VALIDATOR_FN)
    err = _invariant_error()
    historical = {0: 2, 1: 2}          # exactly what the old REJOIN emits
    with pytest.raises(err) as ei:
        validator(historical)
    assert getattr(ei.value, "reason", None) == "DUPLICATE_HOLDER", \
        f"expected reason DUPLICATE_HOLDER, got {getattr(ei.value, 'reason', None)!r}"


@needs_prov
def test_n2_public_action_synthesis_refuses_a_noninjective_raw_map():
    """Pro: the revised N2 must call the actual public entry point and require
    no actions, no provenance, and a registered error."""
    fn = getattr(audit, PROVENANCE_FN)
    err = _invariant_error()
    env = _Env(n=3)
    with pytest.raises(err) as ei:
        fn(env, duty_map={0: 1, 2: 1}, duty_positions=_positions(3))
    assert getattr(ei.value, "reason", None) == "NONINJECTIVE_RAW_ASSIGNMENT", \
        f"unspecific reason: {getattr(ei.value, 'reason', None)!r}"


@needs_prov
def test_n3_validation_is_upstream_of_the_reverse_lookup(monkeypatch):
    """Pro: N3 must prove ORDERING -- validation before inversion -- not merely
    that something raised. Poison the inversion so that reaching it is itself
    detectable; the validator must fire first."""
    fn = getattr(audit, PROVENANCE_FN)
    err = _invariant_error()
    reached = {"inversion": False}

    def _poisoned(*a, **k):
        reached["inversion"] = True
        raise AssertionError("reverse lookup ran before validation")

    if hasattr(audit, "invert_duty_map"):
        monkeypatch.setattr(audit, "invert_duty_map", _poisoned)
    env = _Env(n=3)
    with pytest.raises(err):
        fn(env, duty_map={0: 1, 2: 1}, duty_positions=_positions(3))
    assert not reached["inversion"], "the reverse lookup ran before validation"


@needs_coverage
def test_n4a_a_charging_holder_is_not_executably_covered():
    """The map here is PERFECTLY INJECTIVE -- no shape check can see this."""
    cover = getattr(audit, COVERAGE_FN)
    fn = getattr(audit, PROVENANCE_FN)
    env = _Env(n=3, charging=[False, True, False], batteries=[0.9, 0.5, 0.9])
    dp = _positions(3)
    duty_map = {0: 0, 1: 1, 2: 2}
    assert _is_partial_injection(duty_map), "the point is that map shape is fine"
    _actions, prov = fn(env, duty_map=duty_map, duty_positions=dp)
    assert prov[1][0] == "CHARGING"
    assert 1 not in cover(duty_map=duty_map, provenance=prov), \
        "a docked holder's duty was counted as executably covered"


@needs_coverage
def test_n4b_a_station_return_holder_is_not_executably_covered():
    """Pro: N4 as executed covered only uav_charging. This is the other branch."""
    cover = getattr(audit, COVERAGE_FN)
    fn = getattr(audit, PROVENANCE_FN)
    env = _Env(n=3, charging=[False, False, False], batteries=[0.9, 0.01, 0.9])
    dp = _positions(3)
    duty_map = {0: 0, 1: 1, 2: 2}
    _actions, prov = fn(env, duty_map=duty_map, duty_positions=dp)
    assert prov[1][0] == "STATION_RETURN", f"expected station return, got {prov[1]}"
    assert 1 not in cover(duty_map=duty_map, provenance=prov)


@needs_coverage
def test_n5_an_override_holder_leaves_a_genuine_phantom_duty():
    """REPLACEMENT N5. The previous version passed a NON-injective map to the
    provenance function and expected actions back, which contradicts the frozen
    fail-closed rule -- under a correct implementation it can never reach its
    assertion. This uses an INJECTIVE map whose holder executes an OVERRIDE, so
    the duty is a genuine phantom without violating injectivity, and stays
    distinct from N4's charging/station-return cases."""
    cover = getattr(audit, COVERAGE_FN)
    fn = getattr(audit, PROVENANCE_FN)
    env = _Env(n=3)
    dp = _positions(3)
    duty_map = {0: 0, 1: 1, 2: 2}
    assert _is_partial_injection(duty_map)
    _actions, prov = fn(env, duty_map=duty_map, duty_positions=dp,
                        target_override={1: np.array([7.0, 7.0, 100.0])})
    assert prov[1][0] == "OVERRIDE"
    covered = cover(duty_map=duty_map, provenance=prov)
    assert 1 not in covered, "an overridden holder's duty is a phantom, not covered"
    assert covered == {0, 2}


@needs_validator
def test_n6_the_batch_path_actually_invokes_the_final_assertion(monkeypatch):
    """Pro: N6 previously duplicated P3. It must now prove the GUARD fires --
    reintroduce the old REJOIN behaviour into the batch and require the
    universal final assertion to reject the result.

    This is also the spy Pro requires: a named validator production never calls
    is no protection."""
    err = _invariant_error()
    calls = {"n": 0}
    real = getattr(audit, VALIDATOR_FN)

    def _spy(m, *a, **k):
        calls["n"] += 1
        return real(m, *a, **k)

    monkeypatch.setattr(audit, VALIDATOR_FN, _spy)

    def _old_rejoin(*, duty_map, duty_positions, airborne_positions,
                    event=None, event_uav=None, locked_duties=frozenset()):
        """The historical behaviour: assign an uncovered duty unconditionally."""
        new_map = dict(duty_map)
        if event == "REJOIN" and event_uav is not None:
            uncovered = [d for d in duty_positions if d not in new_map]
            if uncovered:
                new_map[sorted(uncovered)[0]] = event_uav
            return new_map
        return audit.constructive_mixed_update(
            duty_map=duty_map, duty_positions=duty_positions,
            airborne_positions=airborne_positions, event=event,
            event_uav=event_uav, locked_duties=locked_duties)

    monkeypatch.setattr(audit, "constructive_mixed_update", _old_rejoin)
    with pytest.raises(err):
        _batch({0: 0, 1: 1, 2: 2}, [False, False, False, True],
               [False, True, False, False], 4, 4)
    assert calls["n"] > 0, "the transition batch never called the final assertion"


@needs_validator
def test_n7_the_final_assertion_is_named_callable_and_classifies_its_refusal():
    validator = getattr(audit, VALIDATOR_FN)
    err = _invariant_error()
    validator({0: 1, 1: 2})                      # valid: must not raise
    with pytest.raises(err) as ei:
        validator({0: 1, 1: 1})
    assert getattr(ei.value, "reason", None) == "DUPLICATE_HOLDER"


@needs_validator
def test_n8_a_bad_map_is_refused_not_silently_repaired():
    """The failure mode is producing a plausible answer. Dropping a duty to make
    the map valid is the prohibited repair."""
    validator = getattr(audit, VALIDATOR_FN)
    err = _invariant_error()
    violating = {0: 1, 1: 1, 2: 2}
    try:
        result = validator(violating)
    except err:
        return
    pytest.fail(f"silently returned {result!r} instead of refusing; dropping a "
                "duplicate to make the map valid is the prohibited repair")
