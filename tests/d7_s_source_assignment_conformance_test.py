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

## v3 amendments (Pro ruling 2026-07-30, `20260730_d7_s_conformance_suite_v2`)

That round returned **FREEZE AFTER MODIFICATION -- step 1 still not closed**,
with six blockers. Three of them were defects introduced while fixing three
others, and all six are the same shape as before: a check that cannot fail for
the reason it exists.

    P6e observed source text rather than production behaviour   -> rewritten as
        Pro's behavioural (b3) with a production-consumer spy
    N3's ordering poison sat behind an `if` and could be vacuous -> unconditional
    N6 recursively called its own monkeypatched self             -> real function
        captured before patching, plus a counter proving LEAVE ran
    the fake environment could not execute the station-return rule -> `_Env` now
        carries `_calculate_power_consumption` / `return_reserve_ratio`, so the
        REAL dock-trigger rule runs and its premise is asserted per case
    P6a and P6c did not fully distinguish the claimed sources    -> P6a predicts
        ONE tag; P6c separates all four by (target, dock bit)
    P4b bypassed the real multi-rejoin batch path                -> routed through
        `update_duty_map_on_transitions`, like P3 and P4a

Two further **realization bindings** become required, both carried by the hard
sentinel and neither a new semantic demand:

    invert_duty_map              a named reverse lookup, so N3's ordering proof
                                 can be unconditional rather than optional
    step_once()["executable_covered_duties"]
                                 executable coverage carried forward on the step
                                 result, so P6e can prove production consumes it
                                 rather than computing and discarding it
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
INVERSION_FN = "invert_duty_map"
COVERAGE_KEY = "executable_covered_duties"

_HAS_PROV = hasattr(audit, PROVENANCE_FN)
_HAS_VALIDATOR = hasattr(audit, VALIDATOR_FN)
_HAS_ERROR = hasattr(audit, ERROR_CLS)
_HAS_COVERAGE = hasattr(audit, COVERAGE_FN)
_HAS_INVERSION = hasattr(audit, INVERSION_FN)

needs_prov = pytest.mark.xfail(
    not _HAS_PROV, strict=True,
    reason=f"frozen before the repair: `{PROVENANCE_FN}` is contract, not yet built")
needs_validator = pytest.mark.xfail(
    not (_HAS_VALIDATOR and _HAS_ERROR), strict=True,
    reason=f"frozen before the repair: `{VALIDATOR_FN}` / `{ERROR_CLS}` not yet built")
needs_coverage = pytest.mark.xfail(
    not (_HAS_COVERAGE and _HAS_PROV), strict=True,
    reason=f"frozen before the repair: `{COVERAGE_FN}` not yet built")
needs_inversion = pytest.mark.xfail(
    not (_HAS_INVERSION and _HAS_PROV), strict=True,
    reason=f"frozen before the repair: `{INVERSION_FN}` not yet a named symbol")


# =============================================================================
# HARD SENTINEL -- unmarked, so the suite cannot be called green pre-repair
# =============================================================================

def test_sentinel_the_repair_surface_exists():
    """Unmarked and hard. Pro: final acceptance may not be accepted as green
    while provenance cases remain XFAIL, so one case must fail unconditionally
    until the repair lands. This is it."""
    missing = [n for n, present in (
        (PROVENANCE_FN, _HAS_PROV), (VALIDATOR_FN, _HAS_VALIDATOR),
        (ERROR_CLS, _HAS_ERROR), (COVERAGE_FN, _HAS_COVERAGE),
        (INVERSION_FN, _HAS_INVERSION)) if not present]
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
    """Pre-action state complete enough that the REAL dock-trigger rule runs.

    Pro (2026-07-30): the previous double could not execute the station-return
    branch at all -- `dock_trigger_ratio_for_env` calls
    `env._calculate_power_consumption` and reads `return_reserve_ratio`, and
    neither existed here, so every case that claimed to test STATION_RETURN
    died on an AttributeError before reaching its own branch.

    What the double supplies is the *constants*; the *rule* is production's.
    `_calculate_power_consumption` mirrors the deterministic stand-in already
    used by `tests/audit_d7_s_event_aligned_test.py`'s FakeEnv (`300 + v_h`),
    so the two suites do not disagree about the environment they emulate, and
    `_nearest_charging_station` derives its distance from the actual station
    and UAV positions rather than returning a constant that no geometry
    supports.

    With these constants the trigger sits at ~0.101, so a battery of 0.9 is
    firmly a DUTY and 0.01-0.02 is firmly a STATION_RETURN -- the margins are
    wide enough that the branch selection does not hinge on the exact
    `transit_steps` rounding convention.
    """
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
        self.return_reserve_ratio = 0.10
        self.service_cutoff_threshold = 0.02
        self.depleted_battery_threshold = 0.0

    def _calculate_power_consumption(self, v_h, v_z):
        return 300.0 + v_h

    def _nearest_charging_station(self, i):
        station = np.asarray(self.charging_station_positions[0], dtype=float)
        rel = station - np.asarray(self.uav_positions[i], dtype=float)
        return 0, rel, float(np.linalg.norm(rel))


def _trigger_ratio(env, i):
    """The production trigger, recomputed by the test through the production
    helper -- so a case that claims a branch can say WHY it fires."""
    _idx, _rel, dist = env._nearest_charging_station(i)
    return audit.dock_trigger_ratio_for_env(env, i, dist)


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


def _holdings(m):
    """duty ids held, per holder -- the registered semantics stated directly,
    rather than the `len(set(values))` shape check that only sees the count."""
    out = {}
    for d, u in m.items():
        out.setdefault(u, []).append(d)
    return {u: sorted(ds) for u, ds in out.items()}


def test_p3_simultaneous_leave_rejoin_batch_ends_injective():
    """Strengthened per Pro: injectivity alone under-specifies the batch. Three
    airborne survivors and four duties admit exactly one correct answer -- three
    covered duties, one holder each, and the leaver holding nothing. A repair
    that drops a duty to reach injectivity is refused by the count; one that
    leaves the phantom is refused by the per-holder assertion."""
    out, leaves, rejoins = _batch({0: 0, 1: 1, 2: 2},
                                  [False, False, False, True],
                                  [False, True, False, False], 4, 4)
    assert leaves == [1] and rejoins == [3]
    assert 1 not in out.values(), f"the UAV that left retains a duty: {out}"
    for u, ds in _holdings(out).items():
        assert len(ds) == 1, f"UAV {u} holds {ds} in {out}"
    assert len(out) == 3, (
        f"three airborne survivors must cover exactly three duties, got {out}")
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
    """The complementary situation: rejoiners the LEAVE rematch did NOT place.

    Rewritten per Pro: the previous version hand-rolled its own loop over the
    pure `constructive_mixed_update`, so it bypassed the real multi-rejoin
    batch path and could not witness anything about how production sequences
    several rejoiners in one transition. It now goes through
    `update_duty_map_on_transitions`, exactly like P3 and P4a."""
    args = ({0: 0}, [False, True, True, False],
            [False, False, False, False], 4, 4)
    first, leaves, rj = _batch(*args)
    second, _lv2, _rj2 = _batch(*args)
    assert leaves == [] and sorted(rj) == [1, 2], (
        "this case must exercise REJOIN only, with two rejoiners")
    assert first == second, "multi-rejoin batching is not deterministic"
    assert _is_partial_injection(first), f"non-injective: {first}"
    for u in rj:
        held = [d for d, holder in first.items() if holder == u]
        assert len(held) == 1, f"unassigned rejoiner {u} must take one duty, holds {held}"
    assert len(first) == 3, (
        f"two unassigned rejoiners must cover two further duties: {first}")


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
    # Pro: accepting either of two tags is not a prediction. The environment is
    # now complete enough to state which branch fires and why, so the case
    # names ONE tag per UAV and proves the premise for the interesting one.
    trigger = _trigger_ratio(env, 2)
    assert float(env.uav_battery_ratios[2]) <= trigger, (
        f"UAV 2 must be below the dock trigger for this case to mean anything: "
        f"battery={env.uav_battery_ratios[2]} trigger={trigger}")
    assert float(env.uav_battery_ratios[0]) > _trigger_ratio(env, 0), (
        "UAV 0 must be above its trigger, or its DUTY prediction is accidental")
    actions, prov = fn(env, duty_map=duty_map, duty_positions=dp,
                       target_override={3: np.array([5.0, 5.0, 100.0])})
    assert set(prov.keys()) == set(range(env.n_uavs)), "one record per UAV action"
    assert len(prov) == len(actions), "record count must equal action count"
    assert prov[0][0] == "DUTY" and prov[0][1] == 0
    assert prov[1][0] == "CHARGING", "docked UAV must be CHARGING"
    assert prov[2][0] == "STATION_RETURN", f"expected STATION_RETURN, got {prov[2]}"
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
    """Strengthened per Pro: the dock bit alone does not distinguish the four
    sources -- DUTY and IDLE_OR_OTHER share `dock=0`, CHARGING and
    STATION_RETURN share `dock=1`. What separates all four is the pair
    (target, dock bit), so this case exercises all four in ONE env and requires
    each action to equal the action its claimed source implies, recomputed
    independently through the production target rule.

        CHARGING        hold position, dock
        STATION_RETURN  move to the station, dock
        DUTY            move to the duty target, no dock
        IDLE_OR_OTHER   hold position, no dock
    """
    fn = getattr(audit, PROVENANCE_FN)
    env = _Env(n=4, charging=[True, False, False, False],
               batteries=[0.5, 0.9, 0.01, 0.9])
    dp = _positions(4)
    assert float(env.uav_battery_ratios[2]) <= _trigger_ratio(env, 2)
    assert float(env.uav_battery_ratios[1]) > _trigger_ratio(env, 1)
    actions, prov = fn(env, duty_map={1: 1}, duty_positions=dp)

    def _expect(i, target, dock):
        return audit.action_towards_target(
            np.asarray(env.uav_positions[i], dtype=float),
            np.asarray(target, dtype=float),
            max_speed=float(env.max_speed),
            max_vertical_speed_mps=float(env.max_vertical_speed_mps),
            dt=float(env.time_step), dock_request=dock)

    station = np.asarray(env.charging_station_positions[0], dtype=float)
    cases = {
        0: ("CHARGING", env.uav_positions[0], True),
        1: ("DUTY", dp[1], False),
        2: ("STATION_RETURN", station, True),
        3: ("IDLE_OR_OTHER", env.uav_positions[3], False),
    }
    for i, (tag, target, dock) in cases.items():
        assert prov[i][0] == tag, f"UAV {i} tagged {prov[i]}, expected {tag}"
        got = np.asarray(actions[audit.agent_name(i)], dtype=float)
        want = np.asarray(_expect(i, target, dock), dtype=float)
        assert np.allclose(got, want), (
            f"UAV {i} claims {tag} but its action {got} is not the {tag} action {want}")
    assert prov[1][1] == 1, "a DUTY record must carry the duty id"


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


class _StepEnv(_Env):
    """`_Env` plus the surface a REAL `step_once` needs: live user geometry for
    `compute_duty_positions`, and an `env.step` honouring the environment's own
    5-tuple contract (`scenario_base.py:3547`) with no `self.infos` side
    channel -- the side channel that once masked a real defect."""

    def __init__(self, n=4, charging=None, batteries=None):
        super().__init__(n=n, charging=charging, batteries=batteries)
        rng = np.random.default_rng(20260731)
        self.n_users = 8
        self.area_size = 1000.0
        self.height_range = (80.0, 80.0)
        self.user_positions = rng.uniform(100.0, 900.0, size=(self.n_users, 3))
        self.user_positions[:, 2] = 0.0
        self.ground_bs_positions = np.array([[0.0, 0.0, 80.0]])
        self.user_qos_rate_mbps = 1.0
        self.last_user_rates_mbps = np.full(self.n_users, 0.8)
        self.station_occupancy = np.array([0.0])
        self.station_queue_lengths = np.array([0.0])
        self.agents = [audit.agent_name(i) for i in range(n)]

    def step(self, actions):
        for i in range(self.n_uavs):
            act = np.asarray(actions[audit.agent_name(i)], dtype=float)
            self.uav_positions[i] = np.asarray(self.uav_positions[i], dtype=float)
            self.uav_positions[i][:2] += act[:2] * self.max_speed * self.time_step
        infos = {a: {"reward_info": {"qos_satisfaction_ratio": 0.9,
                                     "return_constraint_cost": 0.0,
                                     "return_constraint_cost_raw": 0.0}}
                 for a in self.agents}
        return {}, {}, {}, {}, infos


@needs_coverage
def test_p6e_the_conclusion_bearing_path_consumes_executable_coverage():
    """REWRITTEN BEHAVIOURALLY on Pro's ruling of 2026-07-30.

    The previous version asserted production integration by reading
    `step_once`'s SOURCE TEXT for a symbol name. Pro rejected it, and so did
    this suite's own author before sending: a source-text assertion passes on a
    comment and fails on any integration that takes a different route -- which
    is realization freedom Pro explicitly granted. It was the same defect class
    as every other item this round removed: **a check that cannot fail for the
    reason it exists.**

    Pro's replacement is a behavioural variant of (b3) with a
    production-consumer spy. On a constructed phantom state -- an injective map
    whose holder is docked, so the map claims a duty nobody flies to --

      1. the executable coverage production computes must DISAGREE with raw map
         membership (that is the phantom, observed through behaviour); and
      2. the spy must prove `step_once` actually called the coverage function
         (a correct wrapper production never invokes is no protection); and
      3. what production computed must be carried forward on the step result,
         not computed and discarded.

    (2) and (3) are separate claims. A call proves consumption; the returned
    value proves it survives the step.
    """
    cover = getattr(audit, COVERAGE_FN)
    seen = {"calls": 0, "last": None}

    def _spy(*a, **k):
        seen["calls"] += 1
        seen["last"] = cover(*a, **k)
        return seen["last"]

    env = _StepEnv(n=4, charging=[False, True, False, False],
                   batteries=[0.9, 0.5, 0.9, 0.9])
    raw_map = {0: 0, 1: 1, 2: 2, 3: 3}
    assert _is_partial_injection(raw_map), "the phantom must not be a shape violation"

    import unittest.mock as _mock
    with _mock.patch.object(audit, COVERAGE_FN, _spy):
        step = audit.step_once(env, duty_map=raw_map, service_centroids=None,
                               schedule="constructive_mixed", step_index=0)

    assert seen["calls"] > 0, (
        "step_once never called the coverage function: executable coverage is "
        "decorative, exactly the failure this case exists to catch")
    computed = seen["last"]
    assert set(computed) != set(raw_map), (
        f"production's executable coverage {sorted(computed)} agrees with raw map "
        f"membership {sorted(raw_map)} -- the docked holder's phantom duty is invisible")
    assert 1 not in computed, "duty 1's holder is docked; it is not executably covered"
    assert COVERAGE_KEY in step, (
        f"step_once computed executable coverage but did not carry it forward "
        f"as `{COVERAGE_KEY}`")
    assert set(step[COVERAGE_KEY]) == set(computed), (
        "the coverage on the step result is not the coverage production computed")


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


@needs_inversion
def test_n3_validation_is_upstream_of_the_reverse_lookup(monkeypatch):
    """Pro: N3 must prove ORDERING -- validation before inversion -- not merely
    that something raised.

    FIXED per the 2026-07-30 ruling. The previous version wrapped its poison in
    `if hasattr(audit, "invert_duty_map")`, so if the repair never created that
    symbol nothing was poisoned and the case passed having checked nothing
    about ordering. A guard behind an `if` that may never hold is not a guard.

    The poison is now UNCONDITIONAL. That makes the reverse lookup a REQUIRED
    NAMED SYMBOL rather than an optional one -- a realization binding, listed
    with the others and carried by the hard sentinel, not a new semantic
    demand. `monkeypatch.setattr` refuses a missing attribute, so an
    implementation that inlines the inversion fails this case loudly instead of
    passing it vacuously.
    """
    fn = getattr(audit, PROVENANCE_FN)
    err = _invariant_error()
    reached = {"inversion": False}

    def _poisoned(*a, **k):
        reached["inversion"] = True
        raise AssertionError("reverse lookup ran before validation")

    monkeypatch.setattr(audit, INVERSION_FN, _poisoned)
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
    is no protection.

    FIXED per the 2026-07-30 ruling. The previous version's `_old_rejoin` fell
    through to `audit.constructive_mixed_update` for non-REJOIN events -- the
    same module attribute it had just monkeypatched -- so the LEAVE phase
    re-entered the stub instead of the real re-match, and the case could not do
    what it claimed. The real function is now captured BEFORE the patch and
    called directly, and a second counter proves the LEAVE phase actually ran
    through it rather than being silently skipped.
    """
    err = _invariant_error()
    calls = {"validator": 0, "leave": 0}
    real_validator = getattr(audit, VALIDATOR_FN)
    real_update = audit.constructive_mixed_update      # captured BEFORE patching

    def _spy(m, *a, **k):
        calls["validator"] += 1
        return real_validator(m, *a, **k)

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
        calls["leave"] += 1
        return real_update(
            duty_map=duty_map, duty_positions=duty_positions,
            airborne_positions=airborne_positions, event=event,
            event_uav=event_uav, locked_duties=locked_duties)

    monkeypatch.setattr(audit, "constructive_mixed_update", _old_rejoin)
    with pytest.raises(err):
        _batch({0: 0, 1: 1, 2: 2}, [False, False, False, True],
               [False, True, False, False], 4, 4)
    assert calls["leave"] > 0, (
        "the LEAVE phase never reached the real re-match -- the stub recursed "
        "into itself and the case witnessed nothing")
    assert calls["validator"] > 0, "the transition batch never called the final assertion"


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
