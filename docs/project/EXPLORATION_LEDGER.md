# Exploration ledger

```text
owner=project_manager
policy=user_20260725 -- stay open, record promising directions, order by cost,
       validate cheapest first unless the user designates a direction
ordering=external_ruling_20260725_research_direction_and_ledger
```

This is **not** the decision ledger. That one records protected decisions inside
a frozen contract. This one records *directions we might explore*, so that a
promising idea is neither lost nor silently promoted to the critical path.

## How it is used

- Anything plausible gets an entry, including ideas we do not intend to run soon.
  A cheap entry costs a row; a lost direction costs a rediscovery.
- Ordered by **cost**, cheapest first, and worked in that order **unless the user
  designates one**.
- A direction that is killed stays in the ledger with the reason. Deleting it
  invites its re-proposal.
- `settles` is recorded next to `cost` deliberately. Cheapest-first is the
  ordering rule, but a cheap probe that resolves nothing is worse than a slightly
  costlier one that kills or confirms a direction.

Cost is on three axes because they are not interchangeable: **build**, **compute**,
**review** (serial, and the scarcest).

**The cheapest-first rule was applied wrongly once already.** D1 led this ledger
because it was cheap, and the ruling dropped it because it did not settle what it
claimed to. Cheap-and-inconclusive loses to slightly-costlier-and-separating; the
policy said so, and the ordering did not follow it.

## Active directions

| Order | id | Direction | Build | Compute | Review | Settles |
|---:|---|---|---|---|---|---|
| **0** | **D0** | **Carrier and estimand derivation** — freeze check clock vs realized lifetime, define renewal urgency, define the search-cost estimand, state how R30 / fixed-`k` / legacy each instantiate the claim, fix censoring and exposure semantics | small | **none** | 0 | What "variable `k`" means, and what any later number is a number *of* |
| **1** | **D7** | **Instrumented R30 renewal-process diagnostic**, reward-pure, paired against the strongest shared fixed-lifetime control under matched exposure | medium — new logging | one paired run | 0–1 | Whether the source contains heterogeneous renewal urgency at all; natural hazard and lifetime behaviour; whether truncation/exposure/reward artefacts explain it |
| **2** | **D8** | **Learned two-regime renewal gate** — a decision-time gate between a stable and a flexible renewal regime, primitive skill policy unchanged, no duration catalogue | medium | paired run | 1 | Whether the simplest constrained realization already carries the contribution |
| 3 | D3′ | Role-conditioned renewal on R30 — richer state-dependent KEEP/SET over the same primitive | large | several | 1 | Whether richer conditioning beats the simple gate. **Only if D7 finds heterogeneity and D8 is insufficient** |
| 4 | D1′ | Legacy sampled-duration bias diagnostic | small | one run | 0 | Whether legacy's duration behaviour is short-segment sampling geometry or candidate truncation. **Comparator only** |
| 5 | D4 | Self-learned low-cardinality convergence | large | several | 1–2 | Whether periods can be learned rather than specified. **Parked** — without a causal stability condition it reproduces collapse and calls it convergence |
| 6 | D5 | G20R3 identification fragment | large | several | 2+ | Whether member-resolved delayed credit is identifiable. **Parked, infrastructure** |

D8 is new and did not exist in the previous ordering. It is the strongest simple
reduction: if a two-regime gate delivers the full benefit, a duration head and a
richer KEEP/SET model are unnecessary — and if a complex controller only matches
it, the complexity has no demonstrated value.

### Why D0 is first

It consumes nothing and it changes the question. Until check clock, realized
lifetime, renewal urgency and search cost are frozen, every later measurement is
a number without an estimand — which is how D1 came to claim it settled two
premises it could not reach.

D0 also has to be done before D7 rather than alongside it: D7's whole purpose is
to separate natural renewal from four other ways a segment can end, and that
separation is a definition, not an observation.

### What would change the ordering

- **No source heterogeneity** — paired KEEP-versus-redecide effects indistinguishable
  across agents and contexts. D8 and D3′ lose priority; the source does not identify
  the claim.
- **Unrestricted R30 already succeeds cheaply** — heterogeneous lifetimes emerge,
  fixed `k` is beaten, search cost is acceptable. The tractability motive weakens
  and D3′/D4 weaken sharply.
- **R30 cannot express the literal target** — if the claim needs per-agent physical
  check opportunities, R30 becomes a comparator and the carrier question reopens.
- **D8 succeeds** — do not proceed to D3′ automatically.
- **Legacy and R30 disagree** — collapse in legacy but not R30 supports the
  short-segment-bias explanation and demotes collapse as a general phenomenon.
- **Credit becomes the blocker** — reactivate only the minimum fragment of D5.
- **A valid no-training audit exists** — if a qualified R30 checkpoint and a
  reproducible trajectory path can answer D7 without training, that route moves ahead.

## Retired directions

| id | Direction | Why retired |
|---|---|---|
| D1 | "One instrumented legacy run settles both collapse and role separability" | Rests on three false premises — legacy as live default, collapse unobserved, a completed arm proving the current candidate set trains. Legacy's own sampling geometry can manufacture the reading it was meant to interpret. Survives only as the narrow comparator D1′ |
| D2 | Compute role stability from existing logs, zero compute | No per-step traces are persisted; run logs hold only a small result json |
| D6 | Grill mechanism V1/V2 validation | Not science. It answers no variable-`k` question and does not compete for scientific ordering. Governance lane, may proceed operationally in parallel |

## Retained candidate portfolio

| Candidate | Mechanism | Strongest simpler explanation | Reactivation / lowering |
|---|---|---|---|
| **A. R30 role-conditioned renewal hazard** — preferred | Fixed check opportunities, per-agent KEEP/SET, learned low-cardinality regimes | Unrestricted R30 or a two-clock gate matches it under matched exposure | Raise if held-out role swaps show regime-specific persistence and utility; lower if no renewal heterogeneity exists |
| **B. Two-clock learned gate** — strongest reduction | Decision-time gate over two renewal regimes, no duration catalogue | A recurrent fixed-clock controller may encode the same behaviour implicitly | Raise if it beats the best shared fixed `k`; **select over A if it merely matches A** |
| **C. Corrected legacy sampled duration** — comparator | Samples discrete candidates, reports intended and realized lifetime with bias accounting | Its effect may be entirely sampling geometry or Z truncation | Retain only if a sampled-duration claim is separately wanted, or if it beats R30 after matched correction |
| **D. Self-learned low-cardinality set** — parked | Learns period prototypes or a sparse duration distribution | Pathological collapse satisfies the surface metric without useful structure | Reactivate after source heterogeneity and a non-collapse semantic gate are established |

## Standing check before promoting any entry

From `RESEARCH_GOAL.md`: *what does this let us say about variable `k` that we
could not say before?* If the answer needs more than a sentence, the entry belongs
in this ledger rather than on the critical path.

D5 fails that check today. It is kept because delayed credit across unequal periods
is a real dependency the moment a variable period changes what a credit signal
attaches to — but it earns promotion only when it blocks a variable-`k` result.
