# D7.S — the source-assignment correction you scheduled, and one place I think your own sequence has a gap

You scheduled a zero-compute source-assignment correction freezing six things.
It is written: `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CORRECTION.md`.

**The decision I need is §4.** §2 is the correction for you to accept or amend.
§3 is one measured result that arrived after the last fence and that I think
changes step 1 of your sequence.

Discarding this question's framing is a legitimate answer, including the claim in
§3 that your sequence has a gap.

## 1. Frozen inputs — not review surface

- Your 2026-07-29 ruling in full: (a1) the double hold is a realization defect;
  the assignment is a partial injection; a phantom duty is uncovered; A reopened
  at A1–A4 with solver and Hall lemmas retained; B's `1200/1200` retired; C never
  closed and needing an injectivity precondition; R4 immutable but
  `INVALID_R4_REALIZATION`.
- Your R5 ruling: one-sided falsification control, `V_D <= V*_notP`, equivalence
  refutes necessity while materially-worse does not establish it.
- `MATERIALITY_MARGIN = 5.0`, `DELTA = 10`, `H_STABLE = 139`. No threshold moves.
- The eight R4 topologies may never carry a successor confirmatory result.
- `D7.3` and `D8` remain blocked. Nothing here asks to unblock them.
- Panel **size** stays at eight.

## 2. The correction, for acceptance or amendment

Read the document itself; it is short and it is the artifact under review. It
freezes, in your order: partial-injection semantics; executable coverage
(`m_raw` / `m_exec` / `C = dom(m_exec)` separated); atomic lifecycle transition
behaviour; R5's treatment domain as the executably covered set; fail-closed
handling with **no synthetic zero**; and the R4 invalid-realization disposition.

I have tried to keep it to your words where you gave them, and to mark clearly
where I added structure — the three-object table and the resolution order are
mine, derived from your §7 and §1.2.

## 3. `[MEASURED, POST-FENCE]` The LEAVE branch does not need repairing

This arrived after `db7ad266` and you have not seen it. It is offered as a claim
to falsify.

Your sequence step 1 is "repair the development source controller". I measured
which part actually needs repair, by checking injectivity **between** the LEAVE
and REJOIN phases rather than across a whole step, over every simultaneous
LEAVE+REJOIN step in 8 development episodes:

```text
dup_in   dup_after_leaves   dup_out      n
True     False              True       241
False    False              True         8
                                       ---
                                       249
```

`dup_after_leaves` is **False in all 249**. `dup_out` is **True in all 249**. The
8 rows with `dup_in = False` are exactly the 8 onsets.

So the LEAVE phase produces an injective map every single time, and the REJOIN
phase re-creates the duplicate every single time. **Duplication is continuously
re-created, once per simultaneous transition — it is not persistent state that
nothing repairs.**

`[INFERENCE]` Two consequences I draw and want checked:

1. **The LEAVE branch needs no change**, and a repair that rewrites it risks
   changing behaviour your ruling did not ask to change. The rejoining UAV enters
   the LEAVE rematch pool only because `airborne_positions` is built from
   `charging_after`.
2. Your §1.2 resolution order — final action-capable set, remove, preserve locked,
   rematch, assert injection — is a **stronger** change than the minimum. It would
   also alter steps where no duplication occurs. I do not know whether you intend
   that stronger change, and it is not a decision I should make by choosing an
   implementation.

An earlier version of this note gave two different explanations for the same
persistence, both wrong, both reached by reading code instead of measuring. They
are retracted in the evidence note. This third one is the first I measured before
writing down, and I flag the history so you weight it accordingly.

## 4. THE DECISION

**(a) Accept or amend the correction in §2.** If any of the six freezes is wrong
or underspecified, say which and how.

**(b) Given §3, what is the scope of "repair the development source controller"?**

- **(b1) Minimum:** bar a rejoining UAV already assigned in the same transition
  batch from receiving a second duty. Leaves the LEAVE branch untouched.
- **(b2) Full atomic rebatch:** your §1.2 five-step resolution for every
  transition batch, changing steps that are currently correct.
- **(b3) Something else**, including the `u -> z_u` representation from your
  retained portfolio.

The measurement says (b1) is sufficient to eliminate every observed occurrence.
It does not say (b1) is sufficient in general, and I am not treating "no observed
occurrence" as "cannot occur".

**(c) Does the correction need its own paired-negative suite before the
controller repair, or does it ride on the repair's suite?** The correction is
prose freezing semantics; the obligations that consume it are code. I have not
assumed either answer.

## 5. What I have not done

- Not repaired the controller.
- Not rerun A1–A4, B or C.
- Not selected a topology panel. The predeclared rule fixes a rule, not a
  selection.
- Not written a replacement for A3. You ruled it rescuable once the domain
  becomes the injective executable relation; I have not tried to rescue it ahead
  of the domain change.

## 6. Required response sections

1. Accept or amend, per freeze.
2. The (b) scope ruling.
3. The (c) ruling on paired negatives.
4. Anything in §3 you judge false.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CORRECTION.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260729_D7_S_ONE_UAV_CAN_HOLD_TWO_DUTIES.md`
- `docs/external-review/rounds/20260729_d7_s_duty_map_injectivity/30_PM_SCIENTIFIC_RECONCILIATION.md`
- `scripts/audit_d7_s_event_aligned.py`
- `docs/research/designs/D7_S_R5_OBLIGATION_G_FRESH_PANEL_RULE.md`
- `tests/audit_d7_s_event_aligned_test.py`
