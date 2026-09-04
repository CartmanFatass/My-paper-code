# EOCIV-A1 headroom-reference inventory — DM intake

- Direction: `eociv_lite`
- Object: `EOCIV-A1-HEADROOM-REFERENCE-INVENTORY-R01`
- Evidence class / claim ceiling: **A/RECON**, committed-evidence answerability only
- Result branch: **`A1-GENERIC-COMPARATOR-WIN-WITHOUT-UPPER`**
- Intake date: 2026-09-04

## What I checked

I checked the science card against all eleven named object records, preserving B7/A8/B9 invalid
status. For B1--B6 I checked the frozen treatments, comparison arms, native-return summaries and
claim boundaries from the public JSON plus adjacent code/science indexes. For B9R1 and B10 I
checked the carded comparator identities, unchanged endpoints, aggregate formulas, global and
initialisation results, raw displacement bounds and bounded readings.

I separately checked that:

- B9R1's `B9R1_GENERIC_OR_SOURCE_HARM_ONLY` label is disjunctive and that its generic-gain clause
  was not the trigger;
- B10's positive relative `J` is compatible with a more damaged source arm;
- the B9R1/B10 `0.006814690014960328` bounds are parameter-displacement bounds, not native-return
  upper references;
- no value from a different object, root/profile panel, information set or return coordinate was
  spliced into the estimand; and
- activity counts for A1 itself are all zero, with no result invocation or receipt expected.

I then applied the frozen rule verbatim. The inventory is complete; no qualified matched pair
exists; at least one generic/control/baseline win exists. The selected result is therefore
`A1-GENERIC-COMPARATOR-WIN-WITHOUT-UPPER`.

## Observation and bounded interpretation

Direct observation: `Y_upper` is missing from every candidate same-host/same-information pair, so
the requested raw gap `H = Y_upper - Y_tuned_generic` is not numerically identified. Negative
`Delta_R` in B9R1/B10 is only receiver treatment below the unchanged semantic baseline. It is not
headroom. The B10 result and its bounded falsifier remain unchanged.

This is scientific missingness/answerability, not an engineering failure. There was no code,
runner, test, resource or publication path to accept. It makes no claim about a threshold, MEI,
saturation, best achievable return, or future learner value.

## Flags for the owner and Root

- `docs/research/portfolio/PORTFOLIO.md` remains the sole lifecycle authority and currently marks
  `eociv_lite` `ACTIVE / MEDIUM`.
- A Portfolio PARK proposal has not been approved. This intake makes no lifecycle or Portfolio
  selection.
- The archived B10 convergence disposition is bounded to the receiver-addressed credit family; it
  is not a Portfolio lifecycle change and is not extended by A1.
- MEI is not approved. No materiality threshold, stop-value rule, or B launch is inferred.
- A future numeric headroom claim would first need a new prospectively carded no-learner object
  containing the missing same-host pair. This intake neither selects nor launches that object.

## Decisions this intake produces

### Decision 1 — disposition of the completed A/RECON inventory (object tier)

Options:

- **(a) recommended:** accept the complete read-only branch
  `A1-GENERIC-COMPARATOR-WIN-WITHOUT-UPPER`, publish the relative gaps and explicit missing raw
  headroom, and stop at this clean boundary;
- **(b):** reinterpret `-Delta_R` or anchor-over-treatment CORRECT differences as headroom; or
- **(c):** expand the current object into comparator tuning, an upper-reference implementation or
  a learner/B run.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`; reversible: yes.

Option (b) changes the estimand and is scientifically invalid. Option (c) exceeds this frozen
read-only object and is not authorized by the current guidance.

### Direction and Portfolio tiers

No direction-tier decision is taken: A1 neither opens/closes a family nor selects a next B object.
No Portfolio-tier decision is taken. The current lifecycle remains `ACTIVE` until its owner changes
the Portfolio record.

## Evidence paths

- Card: `docs/research/candidates/eociv_lite/EOCIV_A1_HEADROOM_REFERENCE_INVENTORY_SCIENCE_CARD_20260904.md`
- Result: `docs/research/candidates/eociv_lite/EOCIV_A1_HEADROOM_REFERENCE_INVENTORY_RESULT_EVIDENCE_20260904.md`
- Direction authority: `docs/research/candidates/eociv_lite/DIRECTION.md`
- Audit: `docs/research/portfolio/audit/2026-09-04.md`
