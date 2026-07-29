# Reconciliation — the control forces exposure, but cannot infer necessity

Pro's ruling is `21_PRO_OPEN_RAW.md`, archived byte-exact. The scientific
decisions are Pro's; what follows is the code-side consequence and the
corrections to my own record.

## The ruling

```text
disposition  MODIFY BEFORE FREEZE
4a  exclusion cost is a MEDIATOR, not a confound -- it is the treatment definition
    but min-distance derangement is ONE MEMBER of the no-persistence class,
    not its optimum, so the control is ONE-SIDED
4b  cadence repair is a correction to intended semantics, but it is a DIFFERENT
    EXECUTED INTERVENTION and must be registered in a new R5 contract
4c  pre-intervention infeasibility  -> episode support miss
    post-start infeasibility       -> abort that topology's Part-A instrument
    solver/exposure failure        -> INVALID_EVENT_ALIGNED_AUDIT, zero tolerance
D7.3 / D8   still blocked. No implementation and no compute authorized.
```

## The one thing that changes the science, not just the code

I asked whether the exclusion constraint breaks comparability. Pro says no —
any transit, energy or QoS cost caused by forbidding the incumbent edge is a
**mediator of the value of persistence**, not an external confound. That was my
worry and it is answered.

**The real defect is one I did not see.** With

```text
Pi_notP  = policies forbidding incumbent retention at every eligible check
V*_notP  = sup over that class
pi_der   = the minimum-distance derangement,  pi_der in Pi_notP
```

`pi_der` is a *member*, not the optimizer, so `V_D <= V*_notP` and the two
outcomes are asymmetric:

- **equivalent within ±5** → a valid counterexample to individual-persistence
  necessity. Real benchmark weight.
- **materially worse** → proves only that *this least-distance derangement* is
  worse. It does **not** establish `V*_notP < V_C − 5`, because another
  no-persistence controller could use a different derangement, sacrifice a
  different duty, anticipate user motion, choose by expected `G` rather than
  distance, or coordinate future derangements to offset immediate transit cost.

So the successor is admissible as a **one-sided falsification control**, never as
an oracle positive control. `PERSISTENCE_NECESSARY_SOURCE` is not reachable from
a worse result, and **the R4-style rule where "full-sync materially worse" makes
Part A pass must not be retained.**

A two-sided test would need one of: an identified approximation to `V*_notP`; a
structural proof that min-distance upper-bounds every no-persistence controller
in `G`; a task-dynamic lower bound; or several structurally different strong
controls all failing with the residual policy-class gap bounded. None exists.

## Three corrections to the derivation, all mine to make

**1. The optimization domain was wrong, and my infeasibility worry was an
artifact of my own formulation.** I wrote a bijection over the full duty set.
The registered source normally has eight duties and, after one charging LEAVE,
seven airborne UAVs — and `constructive_mixed` deliberately leaves one unlocked
duty uncovered. So "fewer airborne UAVs than duties" is **not** infeasibility;
it is the normal state, and it only becomes infeasibility if the control insists
on covering every duty, which mine did.

The matched formulation permutes eligible incumbents over the **currently
covered** duty set, holding every non-eligible incumbent pair fixed:

```text
m0 : D -> U        incoming partial assignment
U_e                eligible action-bearing incumbents
D_e = { d : m0(d) in U_e }
solve bijection a : U_e -> D_e
minimising  sum over u in U_e of || p_u - z_a(u) ||
subject to  a(u) != d0(u)   for every u in U_e
```

This keeps the covered-duty set, the assignment count, the duty targets and the
non-eligible incumbents identical. Letting the derangement arm choose a
*different uncovered duty* would bundle a coverage-allocation intervention on
top of the persistence intervention — two changes, one contrast.

**2. My eligibility definition was necessary but insufficient.** "Airborne,
non-charging, holding a duty" misses that `scripted_source_actions` can ignore an
airborne UAV's duty entirely when the energy controller sends it to a station.
The frozen definition requires all six: present and active at the pre-action
boundary; airborne and not charging; not failed or terminal; an incumbent in the
incoming map; **its duty target — not a station-return or other override —
determines the scripted action at that check**; and it has at least one legal,
geometrically distinct non-incumbent target in the retained covered set.

A newly rejoined agent with no incumbent yet is not in the retention
denominator. An event with fewer than two eligible incumbents cannot instantiate
derangement and is a support miss.

**3. `EXPOSURE_OK` was too weak, and internally inconsistent with my own note.**
I recorded that a different duty ID can denote a geometrically identical target
and that bookkeeping reassignment need not change the physical action — then made
retention count alone load-bearing. Pro is right that those cannot both stand.

```text
EXPOSURE_OK = map_exposure_ok AND target_exposure_ok
              AND physical_exposure_ok AND lifetime_exposure_ok

map_exposure_ok       retained eligible incumbents == 0
target_exposure_ok    every eligible incumbent gets a target differing from its
                      incumbent target by more than the registered 1e-6 tolerance
physical_exposure_ok  every uncensored eligible incumbent's executed action
                      sequence differs from constructive_mixed at least once
                      during the DELTA-step interval
lifetime_exposure_ok  every uncensored eligible assignment run lasts EXACTLY one check
```

"Run lengths concentrated at one check" — my wording — is too weak; for
uncensored commitments it is exact. Lifecycle-truncated runs are reported
separately as **censored**, never counted as pass or fail. Action comparison uses
exact deterministic action-array inequality; no fractional threshold appears.

## Cadence: right correction, new intervention

The repair is a correction to the intended pre-action semantics, and it keeps
`DELTA = 10`, the same clock, the same renewal frequency and the same horizon —
so it is not a new cadence. **But it is a different executed intervention and it
is conclusion-bearing, so it cannot be a silent code fix applied to the
historical result.** R5 registers:

```text
derangement applied before action synthesis at every shared check
```

Frozen ordering: arrive at the pre-action boundary → process lifecycle state
visible there → establish the incoming map → solve the derangement → verify
exposure feasibility → synthesize that boundary's action from the **new** map →
carry until the next check, subject to lifecycle censoring.

**The R4 artifact stays valid, for exactly what it measured**: lagged greedy
reassignment recomputed *after* the boundary action. It never becomes evidence
for the repaired arm.

Pro confirms R4's control was **doubly** non-identifying: retention permitted and
unmeasured, and the map one primitive step late. The first defect alone suffices;
the second independently shows the physical timing never instantiated the
intended boundary intervention.

## Infeasibility, three cases and not one

- **Before the intervention begins** — build the matching graph at candidate-event
  certification. No full derangement → the event is ineligible, continue to the
  next candidate; if none qualifies the episode is a Part-A support miss. This is
  a pre-treatment support decision and is handled at episode level. Never
  reported as zero effect, never a greedy or partial fallback.
- **After an R5 continuation has started** — the episode must **not** be quietly
  dropped while its siblings are kept. That conditions the estimate on a
  post-treatment event and would preferentially retain trajectories where forced
  renewal was easiest. Instead: abort the Part-A instrument for that topology,
  discard all of that topology's `D_A` units, record
  `DERANGEMENT_CONTROL_NOT_TOTAL_ON_TOPOLOGY`, and neither retry nor substitute.
- **Solver or conformance failure is not infeasibility** — a legal matching exists
  but the implementation reports infeasible, retains an incumbent, duplicates a
  UAV, changes the covered set, violates the pre-action phase, or fails an
  exposure predicate. That is `INVALID_EVENT_ALIGNED_AUDIT`, zero tolerance.

## A claim of mine that Pro downgraded

My evidence note argued retention was the **geometrically favoured** outcome, not
merely permitted, and used that to explain `D_A ≈ 0`. Pro rules it **plausible
but not established**: service centroids move with users, a LEAVE/REJOIN may have
just rematched incumbents, another UAV can be nearer after motion, and an
airborne UAV may be travelling to a station rather than its duty. No retention
data were serialized, so the explanation is unmeasured.

**The durable reason R4 is non-identifying does not depend on it**: retention was
neither prohibited nor recorded. I have appended that correction to the note
rather than deleting the claim.

Pro also names the same overreach in a form worth keeping: I called the
assignment a constrained optimum when it is optimal only for **transit
distance**, not for cumulative primary `G`. That distinction has to appear in the
contract and in the branch meanings, "otherwise a worse result will again be
overread as a source theorem."

## What happens next — all zero-compute

Obligations A–G must close before any panel is frozen: a mathematical support
derivation with an infeasibility witness; real source-state feasibility recorded
per check on development topology `20260725`; a same-support witness; a
pre-action cadence witness carrying the **delayed R4 ordering as a paired
negative**; an exact exposure witness with five named paired negatives (permitted
retention, same geometric target under a different duty ID, post-action
recomputation, partial derangement, one-eligible-agent state); a branch-semantic
witness exercising all three outcomes; and only then a deterministic,
predeclared fresh-panel rule with the five-unit margin unchanged.

The compute grant (`r5_reanchor_compute_grant`) remains **unspent**. This ruling
authorizes neither implementation nor compute, and the next action is a
derivation amendment, not a run.

## The reusable principle, in Pro's words

> A constrained intervention's unavoidable natural cost is part of its causal
> effect; the inferential defect arises when one heuristic member of the
> constrained policy class is treated as the class optimum.
