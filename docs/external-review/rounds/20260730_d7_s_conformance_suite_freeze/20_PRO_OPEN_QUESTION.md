# D7.S — the conformance suite is frozen and red; accept it before the repair can land against it

You required the suite frozen **before** the repair, run against the old
implementation with its failures recorded, then landed atomically with the repair
and passing **without weakening its predicates**.

Steps 1 and 2 are done. `tests/d7_s_source_assignment_conformance_test.py`,
baseline in `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CONFORMANCE_BASELINE.md`.

**The decision I need is §4.** Everything before it is evidence. Discarding this
question's framing is a legitimate answer.

## 1. Frozen inputs — not review surface

- Your 2026-07-30 ruling in full: FREEZE AFTER MODIFICATION; repair scope **(b1)
  plus a universal final injectivity assertion, not (b2)**; the suite rides on
  the repair but must be frozen first and demonstrate red-to-green.
- Your six mandatory positive witnesses and eight mandatory paired negatives,
  adopted as given.
- The partial-injection invariant, executable coverage, the amended lifecycle
  semantics, the R5 domain, fail-closed with no synthetic zero, and the R4
  invalid-realization disposition.
- `MATERIALITY_MARGIN = 5.0`, `DELTA = 10`, `H_STABLE = 139`. No threshold moves.
- `D7.3` and `D8` remain blocked. Nothing here asks to unblock them.

## 2. The baseline — repository fact

```text
6 failed, 4 passed, 4 xfailed
```

| # | Case | Now | Required after repair |
|---|---|---|---|
| P1 | unassigned rejoiner fills one nearest uncovered duty | PASS | PASS |
| P2 | already-assigned rejoiner receives no second duty | **FAIL** | PASS |
| P3 | simultaneous LEAVE+REJOIN batch ends injective | **FAIL** | PASS |
| P4 | multiple rejoiners deterministic and injective | **FAIL** | PASS |
| P5 | LEAVE regression: reduced fleet + locked incumbent | PASS | PASS |
| P6 | every covered duty has exactly one `DUTY(d)` provenance | xfail | PASS |
| N1 | old REJOIN behaviour assigning a second duty | PASS | PASS |
| N2 | raw non-injective map reaching the action generator | PASS | PASS |
| N3 | reverse lookup before injectivity validation | xfail | PASS |
| N4 | `CHARGING`/`STATION_RETURN` holder counted as covered | xfail | PASS |
| N5 | phantom raw duty with no `DUTY(d)` provenance | xfail | PASS |
| N6 | simultaneous transitions ending with a duplicate holder | **FAIL** | PASS |
| N7 | a removed final injection assertion | **FAIL** | PASS |
| N8 | silently dropping one duplicate and continuing | **FAIL** | PASS |

P3 and P4 reproduce the defect through the **real batching entry point**
`update_duty_map_on_transitions`, not the pure function:

```text
P3  {1: 3, 0: 0, 2: 2, 3: 3}       UAV 3 holds duties 1 and 3
P4  {1: 4, 0: 0, 2: 3, 3: 2, 4: 2} UAV 2 holds duties 3 and 4
```

In P4 the determinism assertion **passed** and only injectivity failed; the two
properties are asserted separately so a later failure names which one broke.

## 3. Three choices I made that you did not specify

These are mine, they are load-bearing, and I would rather have them rejected now
than discovered later.

### 3.1 The provenance interface is frozen as contract, not left to the repair

Your P6, N3, N4 and N5 all require knowing *why* a UAV's action was generated. No
such interface exists. Rather than let the repair invent one, I froze its shape
in the suite:

```text
scripted_source_actions_with_provenance(env, *, duty_map, duty_positions,
                                        target_override=None)
    -> (actions, provenance)

provenance[i] in { ("DUTY", d), ("CHARGING",), ("STATION_RETURN",), ("OVERRIDE",) }
```

The four cases are `xfail(strict=True)` against it. `[INFERENCE]` I believe
freezing the interface is right because the alternative is a repair that defines
its own observability and then satisfies it — the same closed loop that let A3
pass. But it is a design commitment made by me, and it constrains the repair.

### 3.2 P5 is a guard on your choice of (b1) over (b2)

P5 is green **today**. I wrote it so that selecting the targeted repair is
checkable: if the repair reddens P5, it has changed the reduced-fleet rematch and
locked-incumbent behaviour, which (b1) exists to preserve. `[INFERENCE]` I treat
"a case that must stay green" as a legitimate member of a red-to-green suite.
Your procedure describes cases that go red-to-green; this one never goes red, and
I want that sanctioned or rejected explicitly.

### 3.3 N4 is deliberately built on an injective map

Its duty map is perfectly injective and the violation is that a docked UAV's duty
is still counted covered — so no `len(set(values))` check can detect it. This is
my reading of your warning that map shape alone is insufficient, turned into the
one case that would fail if a future maintainer "simplified" the suite to a shape
check.

## 4. THE DECISION

**(a) Accept the frozen suite as satisfying step 1, or name what is missing.**
Specifically: are the fourteen cases faithful to your six witnesses and eight
negatives, or has my rendering narrowed any of them?

**(b) Is freezing the provenance interface (§3.1) correct, or should the repair
define it?** If the repair defines it, I need to know what stops it from defining
an interface that only its own behaviour satisfies.

**(c) Are the four `xfail(strict=True)` provenance cases an acceptable form of
"recorded expected failure", or do you require them as hard failures now?** They
currently do not fail the suite; they are marked. A hard failure would make the
suite red in CI until the repair lands.

## 5. What I have not done

- Not repaired the controller.
- Not implemented the provenance interface or the injectivity assertion.
- Not weakened any predicate to reduce the failure count.
- Not rerun A1–A4, B or C.
- Not selected a topology panel.

## 6. Required response sections

1. Accept or amend the suite, per case where it matters.
2. The (b) ruling on the provenance interface.
3. The (c) ruling on xfail versus hard failure.
4. Anything in §2 or §3 you judge false.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `tests/d7_s_source_assignment_conformance_test.py`
- `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CONFORMANCE_BASELINE.md`
- `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CORRECTION.md`
- `docs/external-review/rounds/20260730_d7_s_source_assignment_correction/30_PM_SCIENTIFIC_RECONCILIATION.md`
- `scripts/audit_d7_s_event_aligned.py`
- `tests/audit_d7_s_event_aligned_test.py`
