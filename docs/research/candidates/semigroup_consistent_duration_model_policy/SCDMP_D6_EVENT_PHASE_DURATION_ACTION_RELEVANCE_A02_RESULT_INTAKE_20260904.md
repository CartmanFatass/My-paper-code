# SCDMP D6 event-phase duration-action relevance A02 — result intake (2026-09-04)

- Object: `SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02`
- Evidence class: A/RECON
- Launch SHA: `c8010f2f14a23d36476c0e1d4f129f888917275d`
- Result: `A02_EVENT_PHASE_POPULATION_NOT_ESTABLISHED`
- Direction-tier status: convergence reopening required; no local next object authorized

## What this intake checked

1. The result document was checked against the complete frozen A02 card and CM intake. It used the
   accepted SHA, root seed `9173`, prospective cost `62.04781499574892 s`, one new root and one
   fresh runner-controlled resource admission.
2. The admission passed with `13,330,087,936` physical/effective available bytes before native
   host construction. Wall time was `4.797502100002021 s`; missing peak RSS is correctly marked
   `resources_unmeasured` for a non-resource claim.
3. Summary, receipt, stdout and stderr hashes were independently reproduced. The summary binds the
   exact launch SHA, object, seed, exposure, integrity, population state, reason and counts. Stderr
   is empty; stdout is the admission receipt.
4. Count arithmetic was independently recomputed: `2+321=323` native missions,
   `546+64,138=64,684` native transitions and `321` evaluator calls. Twenty-one terminal rows sum
   to `321` missions, `320` timeouts, `1` safe dock and zero failures.
5. The first-match rule was applied verbatim. Resource refusal does not match; invalid evidence
   does not match; population-not-established matches because the declared
   `K7-tick-273/countdown-78/clock-7/HR` group safe-docked before its scheduled event. No partial
   return, threshold or result-aware branch rewrite was used.
6. Absence of `K_b,d`, `K_d`, `N` and alignment quantities is consistent with the population
   branch. Those quantities are unobserved, not zero. The valid stop does not need the remaining
   447 candidate missions and does not create a technical retry.

## Observation and bounded interpretation

Direct observation: the exact six-base-state event-phase population cannot satisfy the card's
requirement that every scheduled event occur before native termination. The first stopping cell is
the latest K7 source state with the long countdown; one mission safe-docked before event time.
Earlier published groups account for 320 timeouts, but the stopped summary contains no endpoint
contrast table.

The bounded inference is population failure, not duration-policy failure. A02 does not show that
event alignment lacks value; it shows that this exact late-state/countdown construction cannot
measure the declared opposed alignment over its full required panel. The strongest support is the
explicit safe-dock-before-event row and integrity-valid first-match branch. The strongest
contradiction to a broad closure is that earlier cells progressed without triggering this stop;
however, the frozen estimand requires all cells, and no valid contrast can be reconstructed from
the partial inventory.

A01 remains the only native duration-action contrast: one-sided in favor of `k=13` on its exact
stationary/post-event panel. A02 adds no `k` sign. Together they do not supply the bidirectional
substrate required to make the proposed D6/D8 learner comparison decision-relevant.

## Flags for the owner

- A/RECON has no consumption state. This is a valid population observation, not a consumed C
  object and not a technical retry budget.
- Valid-result machine time is `4.797502100002021 s`; no learner or optimizer usage occurred.
- No replacement event tick, state, countdown, source population or second A02 is allowed by the
  controlling decision.
- The separate Portfolio A1 headroom item remains `HEADROOM_UNMEASURED`; this result does not
  supply an upper-reference/tuned-baseline gap and does not apply an MEI.
- Portfolio lifecycle, priority, capacity, fusion, registration and investment remain unchanged.

## Decisions this intake produces

The result creates one **direction-tier** decision and no object-tier launch authority.

Options to put to `em:semigroup_consistent_duration_model_policy:convergence`:

1. **(a), DM recommendation:** park the current D6 action-choice object family. A01 is uniformly
   one-sided and the sole additional Pro-admitted event-phase population was not established; the
   prior decision authorizes no second population, countdown sweep, learner or B.
2. **(b):** continue only if existing evidence, independent of the exhausted source-search
   lineage, already supports a qualitatively different direction-level recast within the finite
   claim ceiling; name its smallest supported object and explain why it does not evade the prior
   prohibition.
3. **(c):** launch another source/countdown A census or D6/D8 B from the partial A02 inventory.

Recommendation: (a). Option (b) requires an actual independent evidence basis; none is identified
locally. Option (c) conflicts with the complete prior direction decision and the frozen branch.

No local selection is made. Parking or recasting the object family is direction tier. This intake
therefore reopens the same persistent convergence binding with the complete A02 evidence, exposure
line and valid-result cost, then parks local object launch authority at this clean boundary until a
complete archive arrives.
