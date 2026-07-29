# Reconciliation — 20260730_d7_s_source_assignment_correction

Ruling: `21_PRO_OPEN_RAW.md`, archived byte-exact from the emitted source
(22936 chars, UTF-8, no BOM, round-trip verified). Scientific decisions are
Pro's; the code-side consequence below is mine.

## The ruling

**FREEZE AFTER MODIFICATION.** The six-object correction is sound in direction.
Per freeze:

| Freeze | Disposition |
|---|---|
| 1 partial-injection semantics | **ACCEPT** (notation amendment) |
| 2 executable coverage | **ACCEPT WITH A PROVENANCE AMENDMENT** |
| 3 atomic lifecycle transitions | **AMEND** |
| 4 R5 treatment domain | **ACCEPT WITH TEMPORAL PRECISION** |
| 5 fail-closed handling | **ACCEPT WITH A SCOPE CLARIFICATION** |
| 6 R4 disposition | **ACCEPT** |

**Scope of the repair: (b1) plus a universal final injectivity assertion — not
(b2).** Preserve the current LEAVE rematching semantics. Prevent any rejoining
UAV already assigned after the LEAVE phase from receiving another duty, process
multiple rejoiners deterministically, and assert injectivity after the complete
transition batch.

**Paired negatives: the correction rides on the repair's suite** — but that suite
must be **frozen before the repair** and must demonstrate red-to-green: freeze the
cases, run them against the old implementation and record the expected failures,
land repair and suite atomically, then require the same cases to pass **without
weakening their predicates**.

## The measurement changed the ruling

This is the part worth recording. My post-fence measurement — injectivity checked
*between* the LEAVE and REJOIN phases, `dup_after_leaves` False in all 249,
`dup_out` True in all 249 — was accepted as
*"strong enough to select the targeted REJOIN repair over a full rebatch as the
next realization"*, and Pro explicitly declined (b2) on that basis.

Pro also fenced what it does **not** prove, and the list is right:

- not that LEAVE can never violate injectivity under another topology or future
  lock configuration;
- not that REJOIN is the only possible future source of non-injectivity;
- not that the targeted repair guarantees all aspects of executable coverage;
- not that no UAV-to-target representation change will eventually be needed.

Hence the **universal final injectivity assertion** on top of (b1): the targeted
fix addresses the observed route, the assertion catches any other.

## Where my wording was wrong

Pro corrected one phrase of mine, and the correction is fair:

> "Duplication is continuously re-created, not persistent state"

**Both halves are true at different boundaries, and I dropped one.** At the
externally visible step boundary it *is* persistent after onset — that is what
explains how many downstream checks and events were contaminated. At the internal
phase boundary it is repaired and immediately recreated — that is what identifies
the minimal repair location.

I overcorrected. Having found the phase-level mechanism, I wrote it as replacing
the step-level fact rather than refining it, and the step-level fact is the one
that bounds the damage. Both statements are now carried together in the evidence
note.

## Consequences for A, B, C

- **A:** after the repair, rerun A1–A4 against the corrected assignment; prove
  every admitted `m_exec` is a partial injection; derive `D_e` from `m_exec`;
  require one unique incumbent duty per eligible UAV. **A3 is then rescued** —
  `|U_e| = |D_e|` follows because the corrected executable relation is injective.
  Solver, canonical tie-break, sparse-graph and Hall-witness lemmas stay retained.
- **B:** `1200/1200` is **not** rehabilitated by the localization. It was computed
  through the lossy view and must be repeated on trajectories from the corrected
  controller — and the trajectory itself may change after the REJOIN fix.
- **C:** must begin with five preconditions (incoming raw map injective; incoming
  and outgoing executable maps injective; every claimed covered duty has one
  duty-directed action; no action-bearing UAV represents more than one covered
  duty). Its mutation set must add a duplicate-holder case and a
  raw-map/action-provenance disagreement. The `UNCONSTRUCTIBLE` handling was
  honest but did not prove witness completeness.
- **D–F** remain open behind the corrected A–C sequence.

## The suite I now owe, frozen before the repair

Six mandatory positive witnesses: unassigned rejoiner fills one nearest uncovered
duty; **already-assigned rejoiner receives no second duty**; simultaneous
LEAVE+REJOIN batch ends injective; multiple rejoiners produce a deterministic
injective result; **LEAVE regression** — reduced-fleet rematch and locked-incumbent
behaviour unchanged; executable coverage — every duty in `C_t` has exactly one
`DUTY(d)` action-provenance record.

Eight mandatory paired negatives, each of which must independently make the
relevant guard fail: old REJOIN behaviour; raw non-injective map reaching the
action generator; reverse lookup before injectivity validation; a raw duty whose
holder's action source is `CHARGING`/`STATION_RETURN` while called covered; a
phantom raw duty with no `DUTY(d)` provenance; simultaneous transitions ending
with a duplicate holder; a deliberately removed final injection assertion; an
implementation that silently drops one duplicate and continues.

**Pro's warning about the shape of the suite:** testing only
`len(values) == len(set(values))` would close the duplicate-holder defect and
leave the historical charging/stale-holder mismatch invisible. The suite must
test map-level injectivity **and** action-provenance/executable-coverage
consistency.

Pro also noted the existing positive REJOIN test uses an empty incoming map, so
it proves only that an unassigned rejoiner fills an uncovered duty and cannot
exercise the duplicate-holder defect — which is exactly what this round's
evidence note already recorded about it. The strict xfail is a valuable first
negative but does not cover the complete correction.

## Standing constraints unchanged

`D7.3` and `D8` remain blocked. This review authorizes neither implementation nor
compute. No fresh confirmatory topology panel before the development obligations
close.
