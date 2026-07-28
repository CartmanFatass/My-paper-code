# Reconciliation — D7.S audit 2 result disposition

Ruling: `21_PRO_OPEN_RAW.md`, stage commit `76c1ce32`. Round closed.

## What Pro ruled

| Ask | Ruling |
|---|---|
| Q1 disposition | **`PRIMARY_G_DEGENERATE`**, not the recorded `SOURCE_NECESSITY_UNRESOLVED`. Not `INVALID_EVENT_ALIGNED_AUDIT` — the run stays usable. |
| Q2 wiring | **Disjunctive** across limbs, with per-limb statuses preserved. |
| Q3 expansion | **Not admissible.** Both `T_m` points have the wrong sign; §9 forbids it independently of Q1. |
| Q4 smallest unit | The **signed empirical normalizer `B_m = G(constructive_mixed) − G(null)`** is retired *as an identified positive materiality scale* for this frozen route. |
| Next action | An **artifact-only** normalizer-identifiability autopsy. Not another environment run. |

Durable conclusion, quoted: *"D7.S R3 produced a valid matched observation but an
unidentifiable materiality scale. The result closes this measurement route, not
the heterogeneous-renewal research question."*

## Where Pro corrected this conversation

Recorded because a question's errors must be corrected rather than edited away.

1. **I leant conjunctive on Q2; the answer is disjunctive.** My reading would let
   a failed limb erase a valid result belonging to the other limb, which
   contradicts frozen branches 7–9. Both readings agree on *this* run, which is
   why the error was invisible here and would not have been later.
2. **A non-positive LCB is not proof the true `B_m` is non-positive.** The point
   estimates are positive (`+0.180`, `+4.289`). The defensible statement is
   *"positive calibration contrast not established"*, never *"constructive is
   proved no better than null."* The earlier evidence note's phrasing —
   "`B_m` could not establish a positive source-control contrast" — survives;
   any stronger reading of it does not.
3. **`PRIMARY_G_DEGENERATE` does not mean primary `G` is defective.** The
   implicated object is the objective–comparator–normalizer *pair*, not the
   objective. Branch 3 fired through failure to identify a positive `B_m`, not
   through demonstrated arm-invariance of the component sequences.
4. **The two labels were never opposite next experiments.** My own correction in
   the question was accepted, and it was the load-bearing one: the framing the
   round would otherwise have rested on was wrong.

## Code-side consequences — the Project Manager's, and not a second ruling

Technical closure, explicitly *not* the next scientific evidence action:

1. **Wire branch 3.** Replace the hardcoded `primary_g_degenerate_flag=False`
   at `scripts/audit_d7_s_event_aligned.py:3788` with the disjunctive form Pro
   specified, and record `stable_b_identified` / `flex_b_identified` separately
   in the payload, labelling a failed limb `NORMALIZER_NOT_IDENTIFIED` rather
   than folding it into a generic unresolved.
2. **Record point estimates in the artifact.** The instrument writes only the six
   bounds. Every point used in this round had to be reconstructed post hoc; §9's
   own predicate is not evaluable from the recorded artifact without them.
3. **Enforce §9.** `expansion_allowed` is dead code and `--topology-seeds` lets a
   human bypass the predicate entirely. Pro: the dead function "does not make the
   scientific rule optional."
4. **Do not** rerun R3, add replicates, add topologies `20260734–20260741`, edit
   the historical JSON, or use the positive `B_m` points to bypass their
   non-positive bounds.

The recorded artifact stays byte-unchanged; the authoritative disposition is
attached, not substituted.

## Carried forward, deliberately not raised in this round

Three mutation sweeps ran over `scripts/audit_d7_s_event_aligned.py` while this
round was in flight. Their findings are in
`docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_THE_INSTRUMENT_BACK_HALF_SWEEP.md`.

They matter to this ruling because Pro's validity finding leans on exactly the
flags they implicate — *"conformance, support, topology identity, CRN pairing,
and episode-world provenance passed"*. Three of those were verified by the
Project Manager to be **unguarded**: `all_seed_controlled` can be hardcoded
`True`, `B_stable`'s sign can be flipped at its production fold, and the entire
qualifying-event construction branch can be disabled — each leaving the suite at
183 passed.

**This is not sent as a follow-up turn.** A workflow's Pro accesses are counted,
and this round is closed. It goes to the next workflow's plan review, where it is
context for the plan rather than a fourth access.

Nothing here reopens the disposition: an unguarded test means a defect would go
undetected, not that the recorded numbers are wrong. The production code is
correct as written and the run executed that code.
