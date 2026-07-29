"""D7.S source-assignment conformance suite — FROZEN BEFORE THE REPAIR.

Pro's ruling of 2026-07-30
(`docs/external-review/rounds/20260730_d7_s_source_assignment_correction/21_PRO_OPEN_RAW.md`,
§3) requires this suite to exist and to be frozen *before* the controller repair,
and to demonstrate red-to-green:

    1. freeze the conformance cases now;
    2. run them against the old implementation and record the expected failures;
    3. land the controller repair and the suite atomically;
    4. require the same cases to pass WITHOUT WEAKENING THEIR PREDICATES.

**Step 4 is the whole point.** Every predicate here is written to describe the
corrected contract, not the current behaviour. A case that fails today is
supposed to fail today. Recorded expected failures live in
`docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CONFORMANCE_BASELINE.md`.

`xfail(strict=True)` marks the cases that must fail now and must go green when
the repair lands. Nothing here may be relaxed to make the suite green; relaxing a
predicate is the specific prohibited repair.

**CORRECTION (Pro, 2026-07-30), verified empirically.** An earlier version of
this docstring claimed a case "turns red the moment the interface lands without
its mark being removed". **That is false for the CONDITIONAL xfail used below.**
When `not _HAS_PROVENANCE` becomes False the mark is inactive, so a passing test
is an ordinary PASS, never `XPASS(strict)`:

```text
conditional xfail, condition False, test passes  -> PASS
unconditional strict xfail, test passes          -> XPASS(strict) -> FAILED
```

The property described belongs to the **unconditional** strict xfail
`test_rejoin_never_gives_one_uav_a_second_duty` in
`audit_d7_s_event_aligned_test.py`, which must be removed or converted in the
same atomic repair change or the full suite will correctly fail on XPASS.

Because of this, **final acceptance must be fail-closed** and cannot rely on the
marks: run with `pytest --runxfail` requiring every test to pass, or require
`0 failed, 0 xfailed, 0 xpassed, 0 skipped` plus an unmarked hard sentinel that
the provenance interface exists. A run is **not** green while provenance cases
remain XFAIL.

## Two axes, deliberately

Pro: *"Testing only `len(values) == len(set(values))` would close the
duplicate-holder defect but leave the historical charging/stale-holder mismatch
invisible."* So every executable-coverage case asserts **action provenance**, not
just map shape.

## The provenance interface this suite requires

The repair must expose, alongside the actions, which source generated each UAV's
action:

    scripted_source_actions_with_provenance(env, *, duty_map, duty_positions,
                                            target_override=None)
        -> (actions, provenance)

    provenance[i] is one of:
        ("DUTY", d)         flying to duty d's live target
        ("CHARGING",)       docked in place, energy controller owns the action
        ("STATION_RETURN",) departing for a station, energy controller owns it
        ("OVERRIDE",)       intervention machinery forced this target

It does not exist yet. Cases that need it fail at import-time lookup, and that
failure IS the recorded baseline — the interface is part of the contract being
frozen, not an implementation detail left to the repair.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import audit_d7_s_event_aligned as audit  # noqa: E402

PROVENANCE_ATTR = "scripted_source_actions_with_provenance"
_HAS_PROVENANCE = hasattr(audit, PROVENANCE_ATTR)

needs_provenance = pytest.mark.xfail(
    not _HAS_PROVENANCE, strict=True,
    reason=("frozen before the repair: the action-provenance interface "
            f"`{PROVENANCE_ATTR}` is part of the contract and does not exist yet"))


# =============================================================================
# Shared fixtures -- small hand-built states, no environment needed
# =============================================================================

def _positions(n):
    return {d: np.array([100.0 * d, 0.0, 100.0]) for d in range(n)}


def _airborne(ids, spread=10.0):
    return {u: np.array([spread * u, 0.0, 0.0]) for u in ids}


def _is_partial_injection(m):
    holders = list(m.values())
    return len(holders) == len(set(holders))


# =============================================================================
# 1-6. Mandatory positive witnesses
# =============================================================================

def test_positive_1_unassigned_rejoiner_fills_one_nearest_uncovered_duty():
    """An unassigned rejoiner fills exactly one nearest uncovered duty."""
    dp = _positions(2)
    m0 = {}                                  # duty 1 uncovered, rejoiner holds nothing
    ap = _airborne([0, 2])
    ap[2] = np.array([90.0, 0.0, 0.0])       # nearest to duty 1
    out = audit.constructive_mixed_update(
        duty_map=m0, duty_positions=dp, airborne_positions=ap,
        event="REJOIN", event_uav=2)
    assert out.get(1) == 2
    assert len([d for d, u in out.items() if u == 2]) == 1
    assert _is_partial_injection(out)


def test_positive_2_already_assigned_rejoiner_receives_no_second_duty():
    """A rejoiner assigned by the LEAVE phase receives no second duty.

    This is the defect itself. It must go green on the repair."""
    dp = _positions(2)
    m0 = {0: 2}                              # UAV 2 ALREADY holds duty 0
    ap = _airborne([0, 2])
    ap[2] = np.array([90.0, 0.0, 0.0])
    out = audit.constructive_mixed_update(
        duty_map=m0, duty_positions=dp, airborne_positions=ap,
        event="REJOIN", event_uav=2)
    held = [d for d, u in out.items() if u == 2]
    assert len(held) == 1, f"UAV 2 holds {held} in {out}"
    assert _is_partial_injection(out)


def test_positive_3_simultaneous_leave_rejoin_batch_ends_injective():
    """The complete transition batch ends injective.

    Drives the real batching entry point, not the pure function, because the
    batch order is the thing under contract."""
    class _Env:
        n_uavs = 4
        uav_positions = {i: np.array([10.0 * i, 0.0, 0.0]) for i in range(4)}
    env = _Env()
    dp = _positions(4)
    m0 = {0: 0, 1: 1, 2: 2}
    charging_before = np.array([False, False, False, True])
    charging_after = np.array([False, True, False, False])   # UAV1 leaves, UAV3 rejoins
    out, leaves, rejoins = audit.update_duty_map_on_transitions(
        duty_map=m0, duty_positions=dp, env=env,
        charging_before=charging_before, charging_after=charging_after,
        schedule="constructive_mixed", step_index=0)
    assert leaves == [1] and rejoins == [3]
    assert _is_partial_injection(out), f"batch ended non-injective: {out}"


def test_positive_4_multiple_rejoiners_are_deterministic_and_injective():
    """Canonical processing of several rejoiners produces a deterministic
    injective result -- run twice, require identical output."""
    class _Env:
        n_uavs = 5
        uav_positions = {i: np.array([10.0 * i, 0.0, 0.0]) for i in range(5)}
    env = _Env()
    dp = _positions(5)
    m0 = {0: 0, 1: 1}
    charging_before = np.array([False, False, True, True, False])
    charging_after = np.array([False, True, False, False, False])  # 1 leaves; 2,3 rejoin
    runs = [audit.update_duty_map_on_transitions(
                duty_map=dict(m0), duty_positions=dp, env=env,
                charging_before=charging_before, charging_after=charging_after,
                schedule="constructive_mixed", step_index=0)[0]
            for _ in range(2)]
    assert runs[0] == runs[1], "multiple-rejoiner processing is not deterministic"
    assert _is_partial_injection(runs[0]), f"non-injective: {runs[0]}"


def test_positive_5_leave_regression_reduced_fleet_and_locked_incumbent():
    """LEAVE regression: reduced-fleet rematch and locked-incumbent behaviour
    unchanged on representative valid inputs.

    Pro selected (b1) precisely so this behaviour does NOT change. This case is
    the guard on that promise -- it must be green BEFORE and AFTER the repair."""
    dp = _positions(3)
    m0 = {0: 0, 1: 1, 2: 2}
    ap = {0: np.array([0.0, 0.0, 0.0]), 2: np.array([200.0, 0.0, 0.0])}
    out = audit.constructive_mixed_update(
        duty_map=m0, duty_positions=dp, airborne_positions=ap,
        event="LEAVE", event_uav=1, locked_duties=frozenset({2}))
    assert out[2] == 2, "locked incumbent was not preserved"
    assert 1 not in out.values(), "the leaver retained a duty"
    assert _is_partial_injection(out)
    assert len(out) == 2, f"two survivors must cover exactly two duties: {out}"


@needs_provenance
def test_positive_6_every_covered_duty_has_exactly_one_duty_provenance():
    """Executable coverage: every duty counted in C_t has exactly one DUTY(d)
    action-provenance record."""
    fn = getattr(audit, PROVENANCE_ATTR)
    env = _RealisticEnv()
    dp = _positions(3)
    duty_map = {0: 0, 1: 1, 2: 2}
    _actions, prov = fn(env, duty_map=duty_map, duty_positions=dp)
    duty_records = [p[1] for p in prov.values() if p[0] == "DUTY"]
    assert len(duty_records) == len(set(duty_records)), "a duty has two DUTY records"
    covered = set(duty_records)
    assert covered == set(duty_map.keys()), (
        f"claimed covered {sorted(duty_map)} but DUTY provenance covers {sorted(covered)}")


class _RealisticEnv:
    """Minimal stand-in exposing only what the provenance interface reads.

    Deliberately NOT a full fake of the source: it is here so the provenance
    cases have something to run against once the interface exists, and it is
    never used to establish behaviour of the real environment."""
    n_uavs = 3
    time_step = 1.0
    max_speed = 20.0
    max_vertical_speed_mps = 5.0
    uav_positions = {i: np.array([10.0 * i, 0.0, 100.0]) for i in range(3)}
    uav_battery_ratios = np.array([0.9, 0.9, 0.9])
    uav_charging = np.array([False, False, False])
    charging_station_positions = {0: np.array([0.0, 0.0, 0.0])}

    def _nearest_charging_station(self, i):
        return 0, np.array([0.0, 0.0, 0.0]), 10.0


# =============================================================================
# 1-8. Mandatory paired negatives -- each must make the relevant guard FAIL
# =============================================================================
# Each case constructs the violation and asserts the guard rejects it. A guard
# that cannot reject its own violation is a comment.

def test_negative_1_old_rejoin_behaviour_assigning_a_second_duty_is_rejected():
    """The old REJOIN behaviour must be detectable as a violation."""
    violating = {0: 2, 1: 2}          # what the current code produces
    assert not _is_partial_injection(violating)


def test_negative_2_raw_noninjective_map_reaching_the_action_generator():
    """A raw non-injective map must never reach the action generator unchecked."""
    violating = {0: 5, 1: 5}
    inverted = {u: d for d, u in violating.items()}
    assert len(inverted) < len(violating), (
        "this inversion is the lossy step; if it stops losing, this negative is stale")
    assert not _is_partial_injection(violating)


@needs_provenance
def test_negative_3_reverse_lookup_before_injectivity_validation_is_rejected():
    """A reverse lookup performed BEFORE injectivity validation must fail."""
    fn = getattr(audit, PROVENANCE_ATTR)
    env = _RealisticEnv()
    dp = _positions(3)
    violating = {0: 1, 2: 1}          # UAV 1 holds duties 0 and 2
    with pytest.raises(Exception):
        fn(env, duty_map=violating, duty_positions=dp)


@needs_provenance
def test_negative_4_charging_or_station_return_holder_counted_as_covered():
    """A raw duty key whose holder's action source is CHARGING or
    STATION_RETURN, while the artifact calls it covered.

    This is the mismatch a map-shape-only check leaves invisible -- the map here
    is perfectly injective."""
    fn = getattr(audit, PROVENANCE_ATTR)
    env = _RealisticEnv()
    env.uav_charging = np.array([False, True, False])   # UAV 1 is docked
    dp = _positions(3)
    duty_map = {0: 0, 1: 1, 2: 2}
    assert _is_partial_injection(duty_map), "the point is that map shape is fine"
    _actions, prov = fn(env, duty_map=duty_map, duty_positions=dp)
    covered = {p[1] for p in prov.values() if p[0] == "DUTY"}
    assert 1 not in covered, "duty 1's holder is docked; it is not executably covered"


@needs_provenance
def test_negative_5_phantom_raw_duty_with_no_duty_provenance():
    """A phantom raw duty with no DUTY(d) provenance must not count as covered."""
    fn = getattr(audit, PROVENANCE_ATTR)
    env = _RealisticEnv()
    dp = _positions(4)
    duty_map = {0: 0, 1: 1, 2: 2, 3: 0}     # duty 3 is a phantom on UAV 0
    _actions, prov = fn(env, duty_map=duty_map, duty_positions=dp)
    covered = {p[1] for p in prov.values() if p[0] == "DUTY"}
    assert len(covered) < len(duty_map), "a phantom duty was counted as covered"


def test_negative_6_simultaneous_transitions_ending_with_a_duplicate_holder():
    """Simultaneous transitions whose final map contains a duplicate holder."""
    class _Env:
        n_uavs = 4
        uav_positions = {i: np.array([10.0 * i, 0.0, 0.0]) for i in range(4)}
    env = _Env()
    dp = _positions(4)
    m0 = {0: 0, 1: 1, 2: 2}
    charging_before = np.array([False, False, False, True])
    charging_after = np.array([False, True, False, False])
    out, _lv, _rj = audit.update_duty_map_on_transitions(
        duty_map=m0, duty_positions=dp, env=env,
        charging_before=charging_before, charging_after=charging_after,
        schedule="constructive_mixed", step_index=0)
    # The contract: this batch must be injective. Stated as the guard, so the
    # case reads identically before and after the repair.
    assert _is_partial_injection(out), f"batch ended with a duplicate holder: {out}"


def test_negative_7_a_removed_final_injection_assertion_is_itself_a_violation():
    """A deliberately removed final injection assertion.

    Pro requires a UNIVERSAL final injectivity assertion on top of (b1). This
    case asserts the assertion exists and is reachable -- a named, callable
    check, not an inline conditional that a refactor can drop silently."""
    checker = getattr(audit, "assert_partial_injection", None)
    assert checker is not None, (
        "no named final injectivity assertion exists; Pro's (b1)+universal "
        "assertion requires one that can be called and tested")
    checker({0: 1, 1: 2})                       # valid: must not raise
    with pytest.raises(Exception):
        checker({0: 1, 1: 1})                   # duplicate holder: must raise


def test_negative_8_silently_dropping_one_duplicate_and_continuing():
    """An implementation that silently drops one duplicate duty and continues.

    The failure mode is that the system produces a plausible answer. The guard
    must reject the input rather than repair it by discarding a duty."""
    checker = getattr(audit, "assert_partial_injection", None)
    if checker is None:
        pytest.fail("no named final injectivity assertion exists to test")
    violating = {0: 1, 1: 1, 2: 2}
    try:
        result = checker(violating)
    except Exception:
        return                                   # rejected: correct
    assert False, (
        f"silently returned {result!r} instead of rejecting a non-injective map; "
        "dropping a duty to make the map valid is the prohibited repair")
