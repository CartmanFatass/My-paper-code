# D7.S R5 obligation C — the same-support witness

**Status: NOT CLOSED.** The witness holds on every check it could be tested on.
The obligation stays open because one of its five paired negatives cannot be
constructed in 3 of 450 checks, and the reason is a source defect awaiting a
scientific ruling — not a hole in the witness.

Harness: `scripts/d7_s_r5_obligation_c_same_support.py`. Development topology
`20260725` only; emits no `D_A`, no branch, no population identity, and performs
no inference.

## What the obligation requires

Applying the derangement changes **only** eligible agent-to-duty ownership. The
covered-duty set, the number of assignments, the non-eligible incumbent pairs and
every energy/charging decision are unchanged.

## Independence, and the dependence declared

The witness never asks the control whether it behaved. It recomputes each clause
from the incoming and outgoing duty maps and from the **real environment's own
action vectors** under each map, whose element `[3]` is the dock-request bit — so
the charging decision is read off the action the environment would execute, not
off a flag this module maintains.

Declared dependence: like obligation B, this harness imports
`audit_d7_s_event_aligned` and steps real environments through its helpers. It is
a probe under the current audit/source realization, not independent verification
of that realization.

## Result — 3 episodes x 1500 steps

```text
deranged checks     450
same-support pass   450
refused (support)     0
```

## Paired negatives

```text
derangement takes an uncovered duty    caught= 44 missed=0 unconstructible=0  clean=True
non-eligible incumbent moved           caught=136 missed=0 unconstructible=3  clean=False
covered-duty count shrinks             caught=450 missed=0 unconstructible=0  clean=True
charging decision altered              caught=450 missed=0 unconstructible=0  clean=True
ineligible UAV's action changed        caught=258 missed=0 unconstructible=0  clean=True

OBLIGATION_C_CHECKS_PASS=False
```

## The three unconstructible cases, and why they are not a pass

Swapping two non-eligible incumbents is a **no-op when both duties are held by
the same UAV**. `constructive_mixed_update`'s REJOIN branch produces exactly that
state, so the mutation emits a map identical to the unmutated one and the witness
correctly reports no violation.

That is neither a caught mutation nor a missed one. It is a state in which the
negative **cannot be expressed**, and the harness scores it in its own
`UNCONSTRUCTIBLE` bucket with the reason attached rather than laundering it into
either column. `clean` requires `caught > 0 AND missed == 0 AND
unconstructible == 0`, so the gate stays red.

This is the whole reason the defect was found. Under the original scoring the
three cases counted as *missed*, which at least kept the gate red; had they been
scored as passes — the tempting reading, since the witness genuinely reported
correctly — a 33%-prevalence non-injective duty map would still be invisible.

**A negative that is never constructible is a negative that never ran.**

## Why the obligation cannot close here

The witness has no demonstrated hole: 136 caught, 0 missed on the same mutation.
What blocks closure is that the same-support property presumes a well-defined
ownership relation, and the source's relation is not one. Redefining it is a
scientific decision — round `20260729_d7_s_duty_map_injectivity`, §5.

Evidence:
`docs/research/cdc/EVIDENCE_NOTES/20260729_D7_S_ONE_UAV_CAN_HOLD_TWO_DUTIES.md`.

## A scope trap worth recording

A 1-episode/950-step smoke of this same harness printed
`OBLIGATION_C_CHECKS_PASS=True` with `unconstructible=0`. The first duplication
on the development topology occurs at **episode 0, step 911**, so the smoke
stopped essentially at the onset and never reached the defective region. The
green was an artifact of the reduced scope. A smoke that terminates before a
known defect's onset reports nothing about it.
