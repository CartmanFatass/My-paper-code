# D7.S source-assignment correction

**Zero-compute.** This document freezes semantics. It implements nothing, selects
no population, and authorizes no run. Scheduled by Pro's ruling of 2026-07-29
(`docs/external-review/rounds/20260729_d7_s_duty_map_injectivity/21_PRO_OPEN_RAW.md`,
§9) as the next scientific artifact.

Six things are frozen below, in the order Pro listed them.

---

## 1. Partial-injection semantics

```text
The executable duty assignment is a PARTIAL INJECTION from executable duties
to physical UAVs:

    m_t : D_t -> U_t     partial
    m_t(d1) = m_t(d2)  =>  d1 = d2

Each executable duty has at most one holder.
Each action-bearing UAV holds at most one executable duty.
```

**Why it is forced, not chosen.** The source controller emits exactly one
physical action per UAV, and obtains that action by inverting the assignment into
one `uav_to_duty` entry. A UAV cannot execute two duties. A map that assigns it
two is not a richer state; it is an inconsistent one, and the inversion resolves
the inconsistency silently by dictionary overwrite.

A legitimately multi-duty source would need a composite action serving several
targets, an explicit capacity allocation, or a defined aggregation from a duty
set to one trajectory. **None exists here**, so reinterpreting the duplicate as
legitimate would define a new source rather than describe this one.

## 2. Executable coverage

```text
A duty is COVERED by the controller iff exactly one action-bearing UAV's
scripted action is generated from that duty target.

Raw map membership alone does NOT establish coverage.
```

Three objects the previous workflow conflated, now separate and separately named:

| Object | Meaning |
|---|---|
| `m_raw` | the raw assignment ledger — what the dictionary claims |
| `m_exec` | pairs whose holder is present, action-capable, and whose action is actually generated from that duty target |
| `C = dom(m_exec)` | the covered-duty set |

**A phantom duty is UNCOVERED.** A map key is an assignment claim. Coverage
requires an executable action-bearing incumbent.

## 3. Atomic lifecycle transition behaviour

```text
Simultaneous LEAVE/REJOIN transitions produce ONE injective post-transition
assignment over the FINAL action-capable UAV set.

A rejoining UAV already assigned during the same transition batch cannot
receive a second duty.
```

Resolution order for a transition batch:

1. determine the final action-capable UAV set after **all** LEAVE and REJOIN edges;
2. remove assignments belonging to leaving or non-action-bearing UAVs;
3. preserve any valid locked incumbents;
4. rematch the remaining duties one-to-one over the remaining UAVs;
5. assert the result is a partial injection.

**The frozen object is the injective post-transition map, not any one conditional
statement.** A guard in the REJOIN branch is one permitted realization of this
invariant; it is not the contract, and satisfying the invariant some other way is
equally conformant.

### Measured evidence localizing the defect

Checking injectivity **between** the LEAVE and REJOIN phases, over every
simultaneous LEAVE+REJOIN step in 8 development episodes:

```text
dup_in   dup_after_leaves   dup_out      n
True     False              True       241
False    False              True         8
                                       ---
                                       249
```

`dup_after_leaves` is False in all 249; `dup_out` is True in all 249. The LEAVE
phase produces an injective map every time and the REJOIN phase re-creates the
duplicate every time. Duplication is therefore **continuously re-created**, once
per simultaneous step, not persistent state that nothing repairs.

**The LEAVE branch requires no change.** The rejoining UAV enters the LEAVE
rematch pool because `airborne_positions` is built from `charging_after`, under
which a UAV whose falling edge fires this step counts as airborne; it receives a
duty there, and the REJOIN loop then gives it a second.

Development topology `20260725` only. This localizes the repair; it does not
estimate a rate on any other panel.

## 4. R5's revised treatment domain

```text
R5 deranges eligible incumbents over the EXECUTABLY COVERED duty set.

Non-action-bearing, charging, failed, overridden and phantom assignments are
OUTSIDE the treatment domain.
```

The derangement is over `C = dom(m_exec)`, **not** over `m_raw.keys()`, **not**
over a multiset of holder-duty pairs, and **not** over the lossy inverse the
action generator currently consumes.

Holder-duty pairs are explicitly rejected as the treatment object: the executor
has no representation for them, so a derangement over them would not correspond
to anything the source can perform.

## 5. Fail-closed handling of non-injective maps

```text
noninjective executable map
lossy assignment inversion
claimed coverage without an action-bearing holder

    -> INVALID SOURCE-CONTROL REALIZATION
    -> no matching, no effect estimate, no synthetic zero
```

A detected violation produces **no** estimate. It does not fall back to a
degraded estimate, and it does not emit zero. A synthetic zero is the specific
prohibited outcome, because a zero is indistinguishable from a measured null once
it reaches an aggregate.

## 6. The R4 invalid-realization disposition

The historical artifact is **immutable**. The emitted string stays exactly as it
was:

```text
PART_A_CONTRADICTION
```

Do not rewrite the artifact. Its **scientific disposition** under later
implementation evidence is:

```text
INVALID_R4_REALIZATION:
DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED
```

This supersedes the earlier interpretive label
`PART_A_CONTROL_NON_IDENTIFYING_FOR_FORCED_INDIVIDUAL_RENEWAL`, which named a
defect in the control arm only. The present evidence adds an independent defect in
the `constructive_mixed` arm, so the fail-closed conclusion is that **the R4
artifact cannot demonstrate that either named Part-A arm instantiated its
registered semantics.**

R4 remains citable **only** as:

> a descriptive external-return observation produced by the exact historical code
> paths, including their noninjective and stale assignment behaviour.

It cannot support Part-A equivalence, persistence necessity or non-necessity,
`constructive_mixed` versus true full renewal, or the masked focal stable/flex
states.

**The masked focal measurements are affected too**, and this corrects a false
claim I made in the round-7 question. The map does not reach results only through
flown actions:

- `_stable_candidates_at` (`scripts/audit_d7_s_event_aligned.py:2627`) iterates
  `for d, u in sorted(duty_map.items())`, so a double-holding UAV appears **twice**
  as a stable-certification candidate;
- `_flex_survivors_at` (`:2663`) writes `survivors[u] = {...}`, keyed by UAV, so
  its two entries **collapse to one**.

The defect therefore changes the conditioning set and the focal-action identity,
not only the trajectories.

Under the project's result semantics, an invalid realization updates the
**implementation**, not the whole algorithm family. No conclusion about R30,
`D7.3`, `D8` or the broader variable-lifetime thesis follows.

---

## What this document does not do

- It does not repair the controller.
- It does not rerun A1–A4, B or C.
- It does not select a topology panel. The predeclared rule in
  `D7_S_R5_OBLIGATION_G_FRESH_PANEL_RULE.md` fixes a *rule*; Pro's constraint is
  on *selection*, and no selection is made here.
- It does not unblock `D7.3` or `D8`.

## Sequence this correction gates

Only after this correction is accepted through the ordinary implementation
boundary:

1. repair the development source controller;
2. add direct injectivity and phantom-coverage paired negatives;
3. rerun A1–A4 and B;
4. revise and rerun C, adding its injectivity/executable-coverage precondition;
5. resume D–F.

No fresh confirmatory topology panel may be selected before those development
obligations close.
