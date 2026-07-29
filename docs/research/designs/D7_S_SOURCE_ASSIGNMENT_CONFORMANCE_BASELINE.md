# D7.S source-assignment conformance suite — pre-repair baseline

**Frozen 2026-07-30, before the controller repair.** This is step 2 of Pro's
red-to-green procedure: the cases are frozen, run against the **old**
implementation, and their failures recorded here as expected.

Suite: `tests/d7_s_source_assignment_conformance_test.py`.

> **Step 4 is the binding one.** The same cases must pass after the repair
> **without weakening their predicates.** Relaxing a predicate to reach green is
> the specific prohibited repair. This document exists so that a later green run
> can be checked against what was supposed to be red.

## Baseline result

```text
6 failed, 4 passed, 4 xfailed
```

| # | Case | Now | Must be after repair |
|---|---|---|---|
| P1 | unassigned rejoiner fills one nearest uncovered duty | **PASS** | PASS |
| P2 | already-assigned rejoiner receives no second duty | **FAIL** | PASS |
| P3 | simultaneous LEAVE+REJOIN batch ends injective | **FAIL** | PASS |
| P4 | multiple rejoiners deterministic and injective | **FAIL** | PASS |
| P5 | LEAVE regression: reduced fleet + locked incumbent | **PASS** | PASS |
| P6 | every covered duty has exactly one `DUTY(d)` provenance | **xfail** | PASS |
| N1 | old REJOIN behaviour assigning a second duty | **PASS** | PASS |
| N2 | raw non-injective map reaching the action generator | **PASS** | PASS |
| N3 | reverse lookup before injectivity validation | **xfail** | PASS |
| N4 | `CHARGING`/`STATION_RETURN` holder counted as covered | **xfail** | PASS |
| N5 | phantom raw duty with no `DUTY(d)` provenance | **xfail** | PASS |
| N6 | simultaneous transitions ending with a duplicate holder | **FAIL** | PASS |
| N7 | a removed final injection assertion | **FAIL** | PASS |
| N8 | silently dropping one duplicate and continuing | **FAIL** | PASS |

## The repository is now RED BY DESIGN — exact expected state

Running the audit suite and this suite together:

```text
tests/audit_d7_s_event_aligned_test.py
tests/d7_s_source_assignment_conformance_test.py

6 failed, 269 passed, 5 xfailed        (~8m10s)
```

**All six failures are the conformance cases named below and nothing else.** The
audit suite's 269 all pass; the 5 xfails are this suite's 4 provenance cases plus
the pre-existing `test_rejoin_never_gives_one_uav_a_second_duty` strict xfail.

Recorded exactly so a later run can be diffed against it. A seventh failure, or a
failure outside this file, is a **regression** and not part of the plan.

**No CI gate is broken.** The only workflow is `.github/workflows/d7s-audit.yml`
and it does not invoke pytest. The redness is local and intentional.

> **Do not "fix" the red by deselecting these cases.** They are the record that
> the defect exists. The only sanctioned way to green is the repair.

## What each failure actually says

**P2** — the defect itself, at the pure function: `{0: 2}` + REJOIN(2) yields
`{0: 2, 1: 2}`.

**P3 and P4** — the same defect reproduced through the **real batching entry
point** `update_duty_map_on_transitions`, which is stronger evidence than the
three-line unit case because it exercises the actual LEAVE-then-REJOIN ordering:

```text
P3  batch ended non-injective: {1: 3, 0: 0, 2: 2, 3: 3}      UAV 3 holds duties 1 and 3
P4  non-injective:             {1: 4, 0: 0, 2: 3, 3: 2, 4: 2} UAV 2 holds duties 3 and 4
```

In P4 the **determinism assertion passed** — two runs produced identical maps —
and only injectivity failed. The two properties are asserted separately so a
future failure names which one broke.

**N6** — same construction as P3, stated as the guard rather than as an
observation, so the case reads identically before and after the repair.

**N7 and N8** — there is no named `assert_partial_injection`. Pro's ruling is
(b1) **plus a universal final injectivity assertion**; these two cases require it
to exist as a *callable, testable* function rather than an inline conditional a
refactor can drop silently. N8 additionally requires it to **reject** a
non-injective map rather than repair it by discarding a duty — silently dropping
a duplicate is the prohibited behaviour, because it produces a plausible answer.

## The four xfails are the provenance interface

`scripted_source_actions_with_provenance` does not exist. It is **part of the
frozen contract**, not an implementation detail:

```text
provenance[i] is one of
    ("DUTY", d)          flying to duty d's live target
    ("CHARGING",)        docked in place, energy controller owns the action
    ("STATION_RETURN",)  departing for a station, energy controller owns it
    ("OVERRIDE",)        intervention machinery forced this target
```

Marked `xfail(strict=True)`, so each turns red the moment the interface lands
without its mark being removed, and none can pass by accident.

**Why the contract needs this and not just map shape.** Pro: *"Testing only
`len(values) == len(set(values))` would close the duplicate-holder defect but
leave the historical charging/stale-holder mismatch invisible."* N4 is built to
prove that point — its duty map is **perfectly injective**, and the violation is
that a docked UAV's duty is still counted as covered. No map-shape check can
detect it.

## The two cases that pass now and must keep passing

**P5 (LEAVE regression)** is the guard on Pro's choice of (b1) over (b2).
Selecting the targeted repair means the reduced-fleet rematch and
locked-incumbent behaviour must **not** change. This case is green today; if the
repair turns it red, the repair overreached into behaviour that was already
correct.

**N1 and N2** are properties of the violation itself rather than of the source,
so they pass today and are here to keep the vocabulary of the suite honest — N2
asserts the inversion is lossy today and says so explicitly, so that when the
inversion stops losing, the case is recognised as stale rather than quietly
reinterpreted.

## What this document does not do

It does not repair the controller, does not implement the provenance interface,
and does not add the injectivity assertion. `D7.3` and `D8` remain blocked, and
Pro's ruling authorizes neither implementation nor compute.
