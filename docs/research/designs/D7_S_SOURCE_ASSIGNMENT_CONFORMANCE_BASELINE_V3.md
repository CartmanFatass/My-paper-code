# D7.S conformance suite — hash-bound pre-repair baseline (v3)

Supersedes `D7_S_SOURCE_ASSIGNMENT_CONFORMANCE_BASELINE_V2.md`, which described
the suite Pro returned **FREEZE AFTER MODIFICATION — step 1 still not closed**
on 2026-07-30 with six blockers. V1 and V2 are retained as the record of what
was measured and what review changed; **this one is the live baseline.**

This is the baseline Pro's prospective authorization is conditioned on. Once it
exists and is hash-bound, ordinary PM authority may authorize the atomic repair
with **no further Pro design round**, provided no protected semantic choice
changes.

## Hash binding

The baseline below was measured against exactly these bytes. A later claim that
"the suite passed" is checkable against them; a claim measured against different
bytes is a different measurement.

The hashes are of the **working-tree bytes that were executed**, not of a commit.
At measurement time `HEAD` was `78c02b86` (round 10's closing commit); the suite
file was amended in the working tree and not yet committed, while the
implementation file was byte-identical to its `HEAD` version. The suite hash
below therefore does **not** match `HEAD`'s copy of that path, and is not meant
to — it identifies what ran.

```text
git HEAD at measurement   78c02b86bf438d86e89c0eac73786e955a1fe4c9

tests/d7_s_source_assignment_conformance_test.py   (suite, AMENDED, uncommitted)
  sha256  5C7BA39EEE101A08615FC6AD3251E015F48BCB04E9037EBEB97418901523A833

scripts/audit_d7_s_event_aligned.py                (implementation, UNCHANGED)
  sha256  5E207F362EC159D6371A18A95669251DFFF2951B03DCCBABF8471B6B752F4666

python  C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
```

**The implementation hash is the load-bearing half.** Pro's step 5 requires the
amended suite to be rerun against the *unchanged* implementation, and that is
what this hash pins: `audit_d7_s_event_aligned.py` is byte-identical to the
commit the v2 baseline was measured against. Nothing in the repair has been
written yet.

## Baseline

```text
4 failed, 3 passed, 14 xfailed        (0.85s)
```

| Case | Now | After repair |
|---|---|---|
| **sentinel** repair surface exists (unmarked, hard) | **FAIL** | PASS |
| P1 unassigned rejoiner fills one nearest uncovered duty | PASS | PASS |
| P2 already-assigned rejoiner receives no second duty | **FAIL** | PASS |
| P3 simultaneous batch: three survivors, three duties, one each | **FAIL** | PASS |
| P4a multiple already-assigned rejoiners skipped deterministically | **FAIL** | PASS |
| P4b multiple unassigned rejoiners fill through the real batch path | PASS | PASS |
| P5 LEAVE regression (reduced fleet + locked incumbent) | PASS | PASS |
| P6a producer: one record per action, one predicted tag each | xfail | PASS |
| P6b `IDLE_OR_OTHER` exists for a dutyless UAV | xfail | PASS |
| P6c all four sources separated by (target, dock bit) | xfail | PASS |
| P6d provenance actions bit-identical to production | xfail | PASS |
| P6e `step_once` **consumes** executable coverage (behavioural) | xfail | PASS |
| N1 old REJOIN output rejected by the named validator | xfail | PASS |
| N2 public action synthesis refuses a non-injective raw map | xfail | PASS |
| N3 validation upstream of the reverse lookup (unconditional) | xfail | PASS |
| N4a charging holder not executably covered | xfail | PASS |
| N4b station-return holder not executably covered | xfail | PASS |
| N5 override holder leaves a genuine phantom | xfail | PASS |
| N6 the batch path actually invokes the final assertion | xfail | PASS |
| N7 final assertion named, callable, classifies its refusal | xfail | PASS |
| N8 a bad map is refused, not silently repaired | xfail | PASS |

The **counts are unchanged from v2** — 4/3/14, same four failures. That is the
expected result and not a sign the amendments did nothing: every amendment made
a case stricter or made it able to fail, and none of them changed which cases
the *current* implementation can satisfy. P3 now fails one assertion earlier
(the per-holder count, `UAV 3 holds [1, 3]`) rather than on the shape check, and
P4b reaches its pass through `update_duty_map_on_transitions` instead of a
hand-rolled loop.

## Each red case fails for its named reason

A count of failures is not evidence that the right thing failed. The four reds,
with the map each one actually produced:

```text
sentinel  repair surface absent: [scripted_source_actions_with_provenance,
          assert_partial_injection, SourceAssignmentInvariantError,
          executable_covered_duties, invert_duty_map]
P2        UAV 2 holds [0, 1] in {0: 2, 1: 2}
P3        UAV 3 holds [1, 3] in {1: 3, 0: 0, 2: 2, 3: 3}
P4a       non-injective: {1: 4, 0: 0, 2: 3, 3: 2, 4: 2}      (UAV 2 holds 3 and 4)
```

P3 and P4a were hand-derived from `constructive_mixed_update` before the run and
the traces match exactly, including which UAV ends up doubled and which duty is
stranded. That matters because both cases route through
`update_duty_map_on_transitions`: the LEAVE phase re-matches and leaves the map
injective, and the REJOIN phase re-breaks it — the between-phase behaviour
measured in round 8, reproduced here as a unit witness rather than a statistic.

## The six amendments, and what each one actually changed

### 1. P6e rewritten behaviourally — Pro's (b3) plus a production-consumer spy

The v2 case asserted production integration by reading `step_once`'s **source
text** for a symbol name. It passes on a comment and fails on any integration
taking a different route — realization freedom Pro explicitly granted. It was
flagged in the question rather than presented as equivalent to the others, and
Pro rejected it and chose the behavioural variant.

P6e now constructs a phantom state (injective map, docked holder), runs a real
`step_once`, and requires three separate things:

```text
1  production's executable coverage DISAGREES with raw map membership
2  a spy proves step_once actually CALLED the coverage function
3  what production computed is CARRIED FORWARD on the step result
```

(2) and (3) are distinct claims. A call proves consumption; the returned value
proves it survives the step. A correct wrapper production never invokes fails
(2); one that computes and discards fails (3).

### 2. N3's poison is unconditional; N6 no longer recurses

**N3.** The v2 poison sat behind `if hasattr(audit, "invert_duty_map")`, so if
the repair never created that symbol the case passed having checked nothing
about ordering. The poison is now unconditional, which makes the reverse lookup
a **required named symbol**. `monkeypatch.setattr` refuses a missing attribute,
so an implementation that inlines the inversion fails loudly rather than passing
vacuously.

**N6.** The v2 `_old_rejoin` fell through to `audit.constructive_mixed_update`
for non-REJOIN events — the same attribute it had just monkeypatched — so the
LEAVE phase re-entered the stub. The real function is now captured *before* the
patch, and a second counter (`calls["leave"] > 0`) proves the LEAVE phase
actually reached it. Without that counter the fix would be unwitnessed.

### 3. The environment double can now execute the real station-return rule

`dock_trigger_ratio_for_env` calls `env._calculate_power_consumption` and reads
`return_reserve_ratio`; `_Env` carried neither, so **every case claiming to test
STATION_RETURN died on an `AttributeError` before reaching its own branch.**

`_Env` now supplies both, mirroring the deterministic stand-in already used by
`audit_d7_s_event_aligned_test.py`'s FakeEnv (`300 + v_h`) so the two suites do
not disagree about the environment they emulate, and `_nearest_charging_station`
derives its distance from actual geometry rather than returning a constant no
positions support. The double supplies the **constants**; the **rule** stays
production's.

Measured trigger ratios at these constants: `0.1044`–`0.1053`. A battery of 0.9
is firmly DUTY and 0.01–0.02 firmly STATION_RETURN, so branch selection does not
hinge on the `transit_steps` rounding convention.

### 4. P3, P4b and the P6 action semantics

- **P3** pins the registered answer, not just injectivity: three airborne
  survivors cover exactly three duties, one holder each, and the leaver holds
  nothing. A repair that drops a duty to reach injectivity is refused by the
  count; one that leaves the phantom is refused by the per-holder assertion.
- **P4b** goes through `update_duty_map_on_transitions`, like P3 and P4a. The v2
  version hand-rolled a loop over the pure function and so witnessed nothing
  about how production sequences several rejoiners in one transition.
- **P6a** predicts **one** tag per UAV instead of accepting either of two, and
  asserts the trigger premise (`battery <= trigger`) that makes the prediction a
  prediction rather than a guess.
- **P6c** separates all four non-override sources in one env. The dock bit alone
  cannot do this — DUTY and `IDLE_OR_OTHER` share `dock=0`, CHARGING and
  STATION_RETURN share `dock=1`. What separates them is the pair (target, dock
  bit), recomputed independently through the production target rule.

## Two new realization bindings

Neither is a new semantic demand; both are carried by the hard sentinel.

```text
invert_duty_map                          a named reverse lookup, so N3's
                                         ordering proof can be unconditional
step_once()["executable_covered_duties"] coverage carried forward on the step
                                         result, so P6e can prove consumption
```

## The fixtures were verified, because three cases xfail on their first line

P6a, P6c and P6e fail at `getattr(audit, ...)` — their **fixtures and branch
predictions never execute** pre-repair. That is precisely the shape this round
removed everywhere else: a check that cannot fail for the reason it exists, and
by symmetry a check that cannot *pass* for the reason it exists either. A broken
double would sit invisible until the repair landed and then read as a repair
failure.

So they were exercised separately against the unchanged implementation:

```text
P6a premise: UAV2 below trigger            battery=0.02  trigger=0.105333
P6a premise: UAV0 above trigger            battery=0.9   trigger=0.104444
P6c premise: UAV2 below trigger / UAV1 above trigger
P6c CHARGING        action matches production TODAY   [ 0. 0.  0. 1.]
P6c DUTY            action matches production TODAY   [ 1. 0.  0. 0.]
P6c STATION_RETURN  action matches production TODAY   [-1. 0. -1. 1.]
P6c IDLE_OR_OTHER   action matches production TODAY   [ 0. 0.  0. 0.]
all six tag pairs pairwise distinguishable
_StepEnv drives a real step_once           n_duties=8
the phantom premise holds: UAV1 is docked
coverage key absent pre-repair             (P6e is red for THAT reason)
```

Each expected P6c action equals what today's `scripted_source_actions` emits, so
**P6c can only fail after the repair on provenance, never on the double.**

## Fail-closed acceptance — unchanged from v2, and still the binding rule

```text
conditional xfail, condition False, test passes  -> PASS
unconditional strict xfail, test passes          -> XPASS(strict) -> FAILED
```

The conditional form does **not** go red by itself. Acceptance must therefore be:

- `pytest --runxfail ...` with every test passing; or
- a summary containing `0 failed, 0 xfailed, 0 xpassed, 0 skipped`.

`test_sentinel_the_repair_surface_exists` is unmarked and hard, so the suite
cannot read green before the repair under either rule.

The older **unconditional** strict xfail
`test_rejoin_never_gives_one_uav_a_second_duty` in
`audit_d7_s_event_aligned_test.py` must be removed or converted **in the same
atomic repair**, or the full suite will correctly fail on `XPASS(strict)`.

## Regression boundary

Four failures, all named above. A fifth failure, or any failure outside this
file, is a **regression** and not part of the plan. No CI gate runs pytest
(`.github/workflows/d7s-audit.yml` does not invoke it), so the redness is local
and intentional.

> Deselecting these cases is not a fix. The only sanctioned route to green is
> the repair.
