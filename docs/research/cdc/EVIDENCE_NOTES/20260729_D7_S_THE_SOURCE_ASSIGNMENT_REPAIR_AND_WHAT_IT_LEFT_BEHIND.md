# The source-assignment repair, and what it deliberately left behind

Date: 2026-07-29. Branch `untied-k`.

The duty map is now a partial injection. This note records what was measured
after the repair, not what was intended by it.

Companion documents, none of them restated here:

- the defect itself — `20260729_D7_S_ONE_UAV_CAN_HOLD_TWO_DUTIES.md`
- the frozen semantics — `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CORRECTION.md`
- the pre-repair gate — `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CONFORMANCE_BASELINE_V3.md`
- the rulings — `docs/external-review/rounds/20260730_d7_s_conformance_suite_v2/`

## The first re-measurement was a false pass, and it was my own script

Recorded first because it is the most useful thing in this note.

The defect was discovered as a **rate**: 33.6% of steps and 33.3% of check
boundaries on the development topology, in all 8 episodes, absorbing. A passing
test suite cannot speak to that number, so it was re-measured directly with
`scripts/d7_s_source_assignment_repair_verification.py`. The first run returned:

```text
episodes=8  steps=400        steps=3200  checks=320
non-injective at steps  : 0  (0.0000%)
non-injective at checks : 0  (0.0000%)
REPAIR_VERIFICATION_OK
```

That is worthless as evidence, and it was nearly recorded as proof. Adding two
counters showed why:

```text
LEAVE events            : 0      REJOIN events: 0
steps with a UAV docked : 0
```

**The repaired branch is inside REJOIN handling, and no REJOIN ever happened.**
Zero percent was arithmetic over an empty set. The charging onset on this
topology is around step 900 — the same onset that made a 950-step smoke print
`PASS` one round earlier — so 400-step episodes stop before any battery depletes
enough to dock, and nothing the repair touches ever executes.

This is the exact defect the whole sequence exists to remove — **a check that
cannot fail for the reason it exists** — appearing in the script written to
verify the fix for it. It is the sixth instance, and the first one inside a
measurement rather than a test.

The script now refuses to report success without the events:

```text
if tot["rejoins"] == 0:  -> REPAIR_VERIFICATION_INCONCLUSIVE, exit 2
```

Silence must not be able to look like success. A rate is only evidence if the
mechanism that produces it ran, and "the run was long enough" is a claim to be
measured rather than assumed.

## What the under-powered run did establish

Not nothing, but much less than it looked like.

```text
steps with >=1 phantom  : 91  (total phantom duty-steps 91)
episode 3   tags={'STATION_RETURN': 91}   uavs={2: 91}
episodes 0,1,2,4,5,6,7      phantom_steps=0
```

Ninety-one steps where the map claims a duty nobody is flying to. **A phantom is
not a residual defect** — a holder returning to a station is genuinely not
covering its duty, and the executable-coverage ruling is precisely that such a
duty must read UNCOVERED. Before the repair these steps existed and were
invisible; the repair made them countable rather than creating them.

A count concentrated in one episode invites a story, so the tag and holder were
recorded per phantom rather than inferred. Every one is `STATION_RETURN`, from a
single UAV mid-transit. With zero docking anywhere in the run, this is a UAV that
crossed its dock trigger and was still flying to the station when the episode
ended — which is also why no `CHARGING` phantom appears, and why that absence
carries no information about whether docking removes a duty from the map.

**The properly powered re-measurement is what settles the rate**, and it is
reported below rather than inferred from this one.

## The powered re-measurement

Same topology, same construction, 1400 steps per episode — past the onset:

```text
episodes=8  steps=1400            steps=11200  checks=1120
non-injective at steps  : 0  (0.0000%)
non-injective at checks : 0  (0.0000%)
LEAVE events            : 56      REJOIN events: 48
steps with a UAV docked : 4504
steps with a HOLDER docked: 0
```

**48 REJOIN events, zero duplications**, against 33.6% of steps before. The
repaired branch executed 48 times and never produced a second holding, at either
boundary.

Two things this run settles that the short one could not:

- **`CHARGING` cannot be a phantom source, and now that is measured.** 4504
  steps with a UAV docked and **0** steps with a docked *holder*: docking fires a
  LEAVE, which removes the duty from the map. Previously this was a derivation
  from source with an identical-looking alternative (nobody ever docked), and the
  short run could not tell them apart.
- **The phantom distribution is not lumpy.** All 8434 phantom duty-steps are
  still `STATION_RETURN`, but they now appear in all eight episodes across most
  UAVs. The single-episode concentration was an artifact of truncation, not a
  property worth explaining.

Note the comparison is across trajectory families, not within one: the repair
changes the duty map, which changes actions, which changes trajectories. The
claim is that **on corrected trajectories the map is injective at every step and
every check**, not that a specific pre-repair trajectory was rerun clean.

## The verification script was itself put through a paired negative

Otherwise it is only known that the script reports zero — not that it *can*
report anything else. The (b1) skip was removed at the byte level and the same
measurement rerun:

```text
FAIL-CLOSED REFUSALS (the repair did not hold):
  episode 0: step 910: DUPLICATE_HOLDER: duty map is not a partial injection:
  UAV(s) [5] hold more than one duty in {6:6, 0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 7:5}

REPAIR_VERIFICATION_FAILED        exit 1
```

**Step 910** — independently reproducing the previously known ~911 onset from a
different direction. All three verdicts are now exercised against real
trajectories: `OK` when repaired, `FAILED` when the defect is reintroduced,
`INCONCLUSIVE` when the run is too short to contain the event.

Two mistakes were made building this and are recorded because both are the
generic kind:

- **The first mutation attempt never reached disk.** The pattern used `\n` and
  the file is CRLF, so `count` was 0 — and the run printed
  `REPAIR_VERIFICATION_OK` against *unmutated* source. That is the exact failure
  `paired_negative.py`'s docstring already warns about; it happened because the
  sweep was hand-rolled instead of run through that tool. The mutation is now
  read back off disk and asserted present before anything else runs.
- **A conclusive detection was labelled INCONCLUSIVE.** The refusal breaks the
  episode loop before that step's counters are added, so the REJOIN count stayed
  0 and the power guard fired. A refusal now dominates the power guard:
  under-powered means "no evidence", but a refusal *is* evidence.

## The guards were watched failing

A green suite proves the guards agree with the code. It does not prove they could
ever disagree, and this project has shipped guards that could not go red often
enough that the distinction is the whole point. Four paired negatives, one per
property the repair claims, each run through
`.claude/skills/hmasd-acceptance-gate/scripts/paired_negative.py` (which reads
the mutation back off disk before running, and restores byte-identically):

```text
(b1) REJOIN skip removed            -> P2, P3, P4a          reddened
universal final assertion removed   -> N6                   reddened
executable coverage = raw map keys  -> P6e, N4a, N4b, N5     reddened
entry-point validation removed      -> N2, N3               reddened
```

Each mutation reddened exactly the cases named to that property and nothing
else. In particular **N6 is the one that proves the assertion is INVOKED** rather
than merely present — it was the case that recursed into its own monkeypatch two
rounds ago and witnessed nothing.

Full state, all three suites:

```text
tests/audit_d7_s_event_aligned_test.py
tests/d7_s_source_assignment_conformance_test.py
tests/pool_d7_s_event_aligned_shards_test.py

319 passed        (0 failed, 0 xfailed, 0 xpassed, 0 skipped)
```

Fail-closed under both acceptance rules, and reconciling exactly against the
pre-repair run: audit 266 + conformance 21 + pooler 32. The audit suite's
formerly strict-xfailed `test_rejoin_never_gives_one_uav_a_second_duty` is now an
ordinary passing positive, removed in the same atomic change as the repair —
left behind, it would have reported `XPASS(strict)` and failed the suite.

## Two things this note does NOT claim

**It does not claim the defect is gone from every topology.** It is gone from the
development topology at 3200 steps. Pro fenced this explicitly when selecting
(b1): the between-phase measurement does not prove LEAVE can never violate
injectivity under another topology or lock configuration, and REJOIN is not
provably the only future source. That is exactly why the repair carries a
**universal final assertion** over the complete transition batch and not only a
REJOIN guard — the assertion is the part that covers the case the measurement
cannot.

**It does not claim the audit's results are now correct.** Obligations A1-A4 and
B must be rerun on corrected trajectories, C revised and rerun, and D-F resumed
behind them. `D7.3` and `D8` remain blocked. No conclusion-bearing compute is
authorized and no fresh topology panel may be instantiated or inspected.

## What the repair actually is

Pro's scope **(b1) plus a universal final injectivity assertion**, explicitly not
(b2)'s full atomic rebatch:

```text
constructive_mixed_update    a rejoining UAV that already holds a duty after the
                             LEAVE phase receives no second one -- and nothing
                             else in that function changed
update_duty_map_on_transitions
                             assert_partial_injection over the COMPLETE batch,
                             on every branch including the carried-forward one
```

The LEAVE re-match is untouched. `P5` is the regression witness on that, and it
was green before the repair and green after — a repair that reddens it has
overreached into correct code.

Alongside, the surface that makes coverage answerable at all: one canonical
action generator producing five-tag provenance, a named reverse lookup with
validation proven upstream of it, and `step_once` consuming executable coverage
and carrying it forward rather than computing and discarding it.

## The rule this whole sequence produced

Across four review rounds every defect found — in the instrument and in the
tests written to check the instrument — was one shape: **a check that cannot
fail for the reason it exists.** A sampler that built the property it tested. A
grep that could not reach its own counterexample. Assertions about their own
fixtures. A test that read source text. A poison behind an `if` that might never
hold. Fixtures that never execute because their case dies on its first line.

The counter-discipline is the one obligation C already had, and it is worth more
than any of the individual fixes: **a mutation that cannot be constructed is
neither caught nor missed, and must be recorded as its own outcome.** That rule
is what surfaced the non-injectivity in the first place, and it is now also how
obligation C scores a fail-closed refusal.
