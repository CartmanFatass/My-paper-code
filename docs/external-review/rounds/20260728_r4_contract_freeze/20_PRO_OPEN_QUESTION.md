# The R4 contract is frozen — two decisions it deliberately leaves open

The scheduled action is done. `docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN.md`
records your decision at freeze and authorizes neither implementation nor
compute.

This is the result submission. **Two things in the contract are deliberately
unfrozen**, because both are scientific and choosing either locally would be
inventing a registered quantity: §6's expansion rule and §7's evidence
population. They are Q1 and Q2.

## What was frozen, and where each clause came from

Every clause traces to your ruling; I am naming the mapping so you can check I
did not add anything.

| Contract clause | Source |
|---|---|
| `UCB95(U*_stable) < -5.0`, `LCB95(U*_flex) > +5.0` | ANCHOR — Anchor E selected |
| the derivation of 5.0, and that it is **not unique** | ANCHOR — recorded so it is not inherited as forced |
| same margin both horizons; unequal per-step bars are not a flaw | ANCHOR — cumulative task value over different causal windows |
| deletes `B_m` denominators, the `LCB95(B_m) > 0` requirement, the normalizer half of branch 3, the R3 expansion predicate | DERIVABLE |
| Part-A rederived at `-5 < D_A < +5` with the three one-sided rules | DERIVABLE — a disjoint contradiction-control block stays conclusion-bearing |
| branch 3 bound to focal `(KEEP, SET(z))` pairs, **not** the R3 calibration pair | BRANCH_3_UNDER_R4 |
| `primary_g_degenerate = NOT (separate_stable OR separate_flex)`, no fraction threshold | BRANCH_3_UNDER_R4 |
| missing audit → branch 1; complete-and-invariant → branch 3 with `FOCAL_KEEP_SET_COMPONENTS_EXACTLY_INVARIANT` | BRANCH_3_UNDER_R4 |
| four per-limb states plus `MATERIAL_FLEX_RENEWAL_IDENTIFIED` and `FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE` | DERIVABLE — preserve flex-only positive evidence |
| fresh population mandatory; no rethresholding R3 at ±5 | DERIVABLE |

**The pair-set change is recorded as an explicit supersession**, not a silent
edit: the calibration-pair aggregation rule you froze earlier the same day was
R3-specific because it tied component separation to the normalizer source
controls. The implementation already records the calibration and focal pair
families separately, so the change is a rewiring rather than new measurement.

## Both of your corrections are recorded where they will be read again

`CURRENT_WORK.md` — the live state file, not only the sealed round — carries that
the ratio/linear divergence was **not** an R3 design defect and that
`U*_stable = −3` means SET is **worse** than KEEP. Both were my errors and both
were the kind that propagate if only the round archive holds them.

## Launch preconditions, current status

1. **Guard gaps — closed.** All seven areas you made a precondition now have
   paired negatives, each watched failing. The suite went 183 → 215.
2. **Pooler — swept and repaired since your last ruling.** Its seven refusal
   sites are all **clean**, and the four conditions previously cited as evidence
   the run was trustworthy fire independently without masking each other. But its
   reconstruction whitelist had five unguarded fields, two verified by me
   directly: the calibration limbs could be swapped, and the entire
   `topology_hash_failures` collection could be dropped, both with the suite
   green. Now guarded, 21 passed.
3. **Component audit aggregation — not wired**, fail-closed default retained, as
   you indicated is appropriate until it is.
4. **Expansion rule — open.** Q1.
5. **Fresh population — undefined.** Q2.

## What is asked

**Q1 — expansion.** Freeze an R4-specific one-expansion rule, or freeze no
expansion? If a rule, it needs a predicate over the absolute-margin point
directions and unresolved bounds, and I will not invent that predicate. My
inference, marked as such: **no expansion** is the cleaner default, because R3's
expansion rule already proved to be the thing nobody could evaluate — its inputs
were never recorded — and a measurement whose population is fixed in advance
cannot be accused of growing until it clears.

**Q2 — the fresh population.** What makes a population "fresh and untouched"
here? Specifically: may it reuse the eight registered topology *seeds* with new
episode and energy seeds, or must the topology seeds themselves be new? The
former keeps the topology-level inference frame identical and changes only the
episode draws; the latter changes the inferential population. R3's own §E treats
the user world as a topology-conditioned episode-level factor, which suggests the
former is defensible — but this decides what the R4 result is a statement about,
so it is yours.

**Q3 — anything in the freeze I got wrong.** The contract is a transcription of
your ruling. If any clause misstates it, that is a defect in the frozen artifact
and I would rather supersede it now than discover it after a run.

## Required response sections

```text
1. EXPANSION           a rule, or no expansion
2. POPULATION          what "fresh" means, precisely
3. FREEZE_CORRECTIONS  clauses that misstate the ruling
4. NEXT_ACTION         what follows the freeze
5. CHALLENGES          which claims above you checked and found wrong
```

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN.md`
- `docs/external-review/rounds/20260728_r4_materiality_derivation/21_PRO_OPEN_RAW.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md`
- `scripts/audit_d7_s_event_aligned.py`
