# D7.S R5 — the exposure-certified control, before anything is built

You scheduled a zero-compute derivation: define the joint intervention that
actually removes individual persistence. This is that derivation, brought back
before any implementation.

**The decision I need is §4.** Everything before it is evidence, offered as
claims to falsify against the source, not as premises.

Discarding this question's framing is a legitimate answer.

## Frozen inputs — not review surface

- Your R4 ruling. `PART_A_CONTRADICTION` stands as emitted; the interpretive
  disposition `PART_A_CONTROL_NON_IDENTIFYING_FOR_FORCED_INDIVIDUAL_RENEWAL`
  attaches to the artifact and is not written into its JSON.
- `MATERIALITY_MARGIN = 5.0`. You ruled the anchor sound and the control
  defective. I am not proposing a threshold move, now or after any result.
- `DELTA = 10`, `H_STABLE = 139`, the duty set, the energy and charging policy,
  the shared check clock, CRN continuation and the paired-contrast stream
  discipline.
- The eight R4 topologies may not carry a successor confirmatory result. A
  conclusion-bearing successor gets a newly frozen, untouched panel.
- D7.3 and D8 remain blocked. Nothing here asks to unblock them.

## 1. Provenance

**Repository fact** unless marked. `[INFERENCE]` marks my own reading.

## 2. Your two source claims — both hold, and both are sharper

I verified them directly rather than accepting them, because the whole successor
design rests on them.

**Claim 1 — `full_sync_SET` cannot exclude the incumbent.** Confirmed at
`scripts/audit_d7_s_event_aligned.py:941`. `full_sync_set_update` takes exactly
`duty_positions` and `airborne_positions`. No incumbent map is passed, so none
can be excluded — the information never arrives. The body takes
`min(remaining, key=distance to duty d)` with no relation to the prior map.

`[INFERENCE]` **The sharpening: retention is the geometrically favoured outcome,
not merely an admissible one.** `scripted_source_actions` flies each assigned UAV
toward its own duty's live target, so a UAV servicing duty `d` is converging on
`d` and is ordinarily the airborne UAV nearest to `d` — exactly the one greedy
nearest-assignment picks. An arm that mostly returns the map it was handed is
close to a no-op, which is a mechanism for `D_A ~ 0` having nothing to do with
persistence being unnecessary.

**Claim 2 — the recomputed map is applied one step late.** Confirmed:
`step_once` synthesizes actions from the incoming map (`:2494`), steps the env
(`:2507`), then updates the map (`:2510`).

**The sharpening: it is a uniform lag at every check boundary, not a
`step_index=0` artifact.** Recomputation fires at `step_index % DELTA == 0`
(`:2413`) after that step's action has already executed, so the new map governs
steps `1..DELTA` of the window rather than `0..DELTA-1`.

The docstring at `:2394` asserts the schedule "never preserves any incumbent,
locked or not." That is false as written: the code guarantees no incumbent is
*protected*, not that none can be *reselected*.

## 3. The proposed control

Full derivation: `docs/research/designs/D7_S_R5_EXPOSURE_CERTIFIED_DERANGEMENT_CONTROL.md`.

At every shared check boundary, with `m0` the incoming map:

```text
minimise   sum_d c(d, m(d)),  c(d,u) = || pos(u)[:2] - dutypos(d)[:2] ||
subject to m injective on D
           m(d) != m0(d)  for every eligible d
```

A rectangular linear assignment with forbidden cells, the forbidden set being
exactly the incoming assignment.

**Exposure predicate, exact and not fractional:**

```text
EXPOSURE_OK  iff  retained_eligible_incumbents == 0
```

Recorded per check: incumbent-retention count, assignment Hamming distance,
per-agent target displacement (against the existing `1e-6` geometric dedup
tolerance, so a reassignment onto a geometrically identical target does not count
as exposure), action-vector divergence from `constructive_mixed`, and realized
assignment run lengths.

Infeasible derangement is an explicit support/instrument failure. There is no
greedy fallback and no partial-derangement accept — a quiet degraded mode is what
made the last control certify nothing.

## 4. The decision

**4a. Is minimum-cost derangement the right comparator?**

The worry I cannot resolve myself: incumbent exclusion is a *constraint on the
control*, and a constrained optimum is by construction no better than the
unconstrained one. So the successor arm pays a transit cost the old arm did not.
If `D_A` then comes out materially worse, I cannot distinguish "individual
persistence is necessary" from "I imposed a constraint and it cost transit."
Does that break comparability with `constructive_mixed`, and if so what makes the
contrast identify persistence rather than the constraint?

*Sub-branch, riding here rather than as its own question:* I define an eligible
active incumbent as an airborne, non-charging UAV holding a duty in the incoming
map — charging UAVs hold no duty to renew. Is that the right eligibility set, or
does it need to be pre-registered differently?

**4b. The phase-shift repair — same cadence, or a new intervention?**

Repairing it means applying the check-boundary recomputation *before* action
synthesis on that step. I am not treating this as an implementation binding,
because the R4 record establishes that this control's cadence can decide whether
`PART_A_CONTRADICTION` fires. Is the repair a correction to the registered
cadence, or a different intervention requiring its own registration?

If it is a different intervention, then `[INFERENCE]` the R4 result was produced
by an arm that is doubly non-identifying — wrong exposure *and* wrong phase — and
I would like that stated rather than assumed.

**4c. Infeasibility scope.**

When a full derangement is infeasible, is the correct refusal episode-level
invalidation, or a topology-level instrument abort? These differ in whether a
topology with one bad check still contributes.

## 5. Confidence

- **Verified by me against source**: both claims in §2, by reading
  `full_sync_set_update`, `update_duty_map_on_transitions` and `step_once`.
- **Not verified by anyone**: that a minimum-cost derangement is *feasible* at
  realistic airborne counts on this source. I have not run it. If derangement is
  routinely infeasible, 4c stops being a corner case and becomes the whole
  design, and `[INFERENCE]` I suspect that is the risk most likely to be
  underestimated here.
- **Not measured**: the incumbent-retention rate on run `30403322062`. The R4
  artifact records none of the exposure quantities, so it cannot be recovered
  from the artifact. Point your scepticism at §2's "geometrically favoured"
  inference first — it is the claim in this question I would most like falsified,
  since it is the reason I believe the old arm was near-inert.

## Evidence to read

- `docs/research/designs/D7_S_R5_EXPOSURE_CERTIFIED_DERANGEMENT_CONTROL.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260729_D7_S_THE_FULL_SYNC_ARM_CAN_HAND_A_DUTY_BACK.md`
- `docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md`
- `docs/research/designs/D7_S_R4_DECISION_LEDGER.md`
- `scripts/audit_d7_s_event_aligned.py`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`

## Required response sections

1. **4a** — comparator validity, and what makes the contrast identify persistence
   rather than the exclusion constraint. Include the eligibility sub-branch.
2. **4b** — cadence correction or new intervention.
3. **4c** — episode-level or topology-level refusal.
4. Anything in §2 or §3 you judge false, especially the "geometrically favoured"
   inference.
5. What must be demonstrated in the development exercise before a confirmatory
   panel is frozen.
