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

Reordered again on 2026-07-25 by the D7 ruling. D7 is no longer one paired run;
it is a staged diagnostic that runs its cheapest qualifying stage first.

| Order | id | Direction | Build | Compute | Review | Settles |
|---:|---|---|---|---|---|---|
| **0** | **D0** | Carrier and estimand derivation — clocks, `U_opp` vs `U_pi`, `Δ`, `H`, continuation semantics, normalization, censoring | small | **none** | 0 | **Complete.** What "variable `k`" means, and what any later number is a number *of* |
| ~~1~~ | ~~D7.1~~ | Qualified-checkpoint preflight | none | none | 0 | **Done 2026-07-25 — negative.** No R30 checkpoint exists in either tree; zero `.pt` files in the external HMASD `logs/` at all |
| ~~2~~ | ~~D7.2A~~ | Frozen-policy audit | — | — | — | **Unavailable.** Closed by D7.1 |
| ~~1~~ | ~~D7.2B~~ | ~~Toy positive control on `two_timescale_role_free_actions`~~ | built | spent | 0 | **Source retired 2026-07-25.** It admits a full-sync swap optimum, so persistence is optional and a null is uninformative. `EVIDENCE_NOTES/20260725_D7_2B_TOY_SWAP_DEGENERACY_DERIVATION.md` |
| **1** | **D7.2B′** | **Replacement positive control** on a source where persistence is *necessary* | small — the audit, hook and ledger all transfer | one short run | **1** — the source contract is a scientific selection | Whether the learned-keep carrier can express urgency where it provably exists |
| **4** | **D7.3** | Main-scenario urgency audit, unless 2A settled it | medium | evaluation or run | 0–1 | Label-free, intervention-identified source heterogeneity |
| 5 | **D8-coadaptive** | Two-regime renewal gate, jointly trained, constraining only the renewal-regime representation | medium | paired run | 1 | Whether the simplest constrained realization carries the contribution. **Build only if D7.3 establishes predictable low-cardinality urgency** |
| 6 | D3′ | Richer state-dependent KEEP/SET over the same primitive | large | several | 1 | Whether richer conditioning beats the simple gate. Only if D8 is insufficient |
| 7 | D1′ | Legacy sampled-duration bias diagnostic | small | one run | 0 | Legacy's own update geometry. **Off the critical path** unless legacy behaviour must be explained |
| 8 | D4 | Self-learned low-cardinality convergence | large | several | 1–2 | **Parked** behind a causal non-collapse criterion |
| 9 | D5 | G20R3 identification fragment | large | several | 2+ | **Parked.** Reactivate only if identified source opportunity and policy capacity exist but renewal learning stays credit-limited |

### Why the order changed

The cheapest stage that can settle the question is a **frozen-policy evaluation**,
not a training run. A checkpoint's missing commitment state blocks reconstructing
past training trajectories, but not a fresh rollout — and the interventional
estimand is policy-conditional, so freezing the policy is desirable rather than a
compromise: both branches then refer to one snapshot.

That makes D7.1, a pure repository check costing nothing, the gate on whether
anything needs to be trained at all.

**A negative at D7.2A does not retire the carrier.** It cannot separate absent
source heterogeneity from an insufficient checkpoint, a bad skill policy, or
renewal-credit failure. It routes to the toy positive control.

### D8 split in two, and one half is dead

`D8-frozen` — freeze the skill controller, train only a renewal gate — **is
retired**. R44 ran that mechanism with a live gradient path and it collapsed to
full-sync renewal at zero minimum per-agent marginal. `D8-coadaptive` survives:
"primitive skill policy unchanged" means unchanged *architecture and information
contract*, not frozen weights. Read as frozen weights it is R44 again.

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
| D8-frozen | Renewal gate on a frozen skill controller | Already run as R44 with a live gradient path: actor drift `0.353` across 3,000/3,000 finite nonzero exposures, behaviour still full-sync RENEW at zero minimum per-agent marginal. Retired without rescue; `D8-coadaptive` is the survivor |
| D7.2B | Toy positive control on `two_timescale_role_free_actions` | The source cannot make persistence necessary. Its reward is the better of the two agent-to-duty assignments, so from any optimal pair a **full-sync swap** reaches the next optimal pair — both agents SET, every commitment lives exactly one check interval. Two distinct optima, one of which never persists, so a null says nothing about the carrier. Measured at competence: `A = 1.0/1.0`, `P(SET|flex) = 1.0`, `P(KEEP|stable) = 0.0`, full-sync SET `1.0`, `U~_flex 0.214` against `U~_stable 0.232`. Retires the benchmark pair only; carrier, estimands and machinery intact and reusable |

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
