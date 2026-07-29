# D7.S R5 obligation G — the fresh-population panel rule

**Status: PREDECLARED, NOT IMPLEMENTED, NOT AUTHORIZED.**

Pro's R5 ruling gates obligation G on "only after A–F pass", and authorizes
neither implementation nor compute. This document does not execute G. It fixes
the *rule* G will later be executed under, and nothing else — no constant is
added to `scripts/audit_d7_s_event_aligned.py`, no panel is selected, no run is
proposed.

## Why write it now rather than when G runs

A predeclared rule is only worth the observation it precedes. Written now — with
A invalid, C blocked, and the §5 ruling still outstanding — no result can have
influenced the choice. Written after A–F pass, the same text would be
indistinguishable from a panel picked with some knowledge of what the panel is
for. The pre-registration is the whole value; deferring it spends it.

This is a PM-side implementation binding, recorded and disclosed. It is not a
scientific decision and is not routed to Pro for approval.

## What obligation G requires

Pro's four conditions, verbatim in substance:

- choose the untouched topology panel by a **deterministic, predeclared rule**;
- freeze its seed namespace and episode blocks;
- **prohibit reuse or pooling of R4 topologies**;
- retain the five-unit margin unchanged.

## Every seed already consumed

```text
TOPOLOGY_SEED_DEV        20260725               development, heavily observed
TOPOLOGY_SEEDS_INITIAL   20260726 .. 20260733   R3
TOPOLOGY_SEEDS_EXPANSION 20260734 .. 20260741   == TOPOLOGY_SEEDS_R4
TOPOLOGY_SEEDS_R4        20260734 .. 20260741   R4, observed
```

`TOPOLOGY_SEEDS_EXPANSION` and `TOPOLOGY_SEEDS_R4` are the **same eight numeric
values**; the module already asserts this. So the consumed interval is the single
contiguous run `20260725 .. 20260741`, with nothing above it used.

## The rule

> **R5's panel is the next contiguous block of eight above the highest seed any
> earlier population consumed:** `20260742 .. 20260749`, in ascending order, with
> its own population namespace `D7_S_R5_EXPOSURE_CERTIFIED_DERANGEMENT`.

Deterministic: the block is a function of the already-registered seed sets, with
no free parameter and no tie to break. Predeclared: it is fixed here, before the
§5 ruling and before any R5 treatment data exists. Non-overlapping: `20260742` is
one above `20260741`, so the block is disjoint from R3, R4 and the development
seed by construction rather than by checking.

Panel **size stays at eight**. This is not an expansion; it is the same panel
shape R4 used, on untouched ground.

## What the guard must assert when G is implemented

Not written yet — listed so the implementation cannot quietly ship without them,
and so each has a paired negative from the start:

1. `set(TOPOLOGY_SEEDS_R5) & set(TOPOLOGY_SEEDS_R4) == set()` — paired negative:
   a panel containing `20260741` must fail.
2. `set(TOPOLOGY_SEEDS_R5) & set(TOPOLOGY_SEEDS_INITIAL) == set()` — paired
   negative: a panel containing `20260733` must fail.
3. `TOPOLOGY_SEED_DEV not in TOPOLOGY_SEEDS_R5` — paired negative: a panel
   containing `20260725` must fail.
4. `len(TOPOLOGY_SEEDS_R5) == 8` and strictly ascending — paired negative: a
   seven-seed or unsorted panel must fail.
5. The R5 namespace is **not** `R4_POPULATION_NAMESPACE` — paired negative: a run
   declaring the R4 namespace over R5 seeds must fail.
6. `MATERIALITY_MARGIN == 5.0` unchanged — paired negative: any other value must
   fail.

Assertion 5 matters most and is the least obvious: the module already routes on
"whole topology-seed set is exactly the frozen `TOPOLOGY_SEEDS_R4`", so a panel
that is fresh but declares the wrong namespace would be accepted by a rule that
only checks seeds.

## What this document does not do

It does not claim A–F pass. A is invalid pending the §5 ruling
(`docs/external-review/rounds/20260729_d7_s_duty_map_injectivity/`), C is blocked
on the same ruling, and D, E and the integrated development witness are blocked
behind C. G runs after those close, or not at all.
