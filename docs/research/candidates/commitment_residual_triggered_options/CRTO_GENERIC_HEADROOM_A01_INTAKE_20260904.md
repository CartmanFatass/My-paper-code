# CRTO generic-headroom A01 design intake

Date: `2026-09-04`

Direction: `commitment_residual_triggered_options`

Object: `CRTO-GENERIC-HEADROOM-A-RECON-R01`

Disposition: `EXISTING_HEADROOM_NOT_ESTABLISHED_FREEZE_MINIMAL_A_RECON`

Evidence class and claim ceiling: object-level read-only intake plus a frozen `A/RECON` design;
the existing values are finite-panel G16 gaps, not a competent-baseline mechanism result or a
Portfolio disposition.

Design input: action A1 in
`docs/Claude_docs/plans/MARL_EXPLORATION_GUIDANCE_20260904.md`, applied only at object tier under
the current Root assignment. Its proposed MEI and lifecycle dispositions are not authority here.

## Question checked

Does the current CRTO host already have the A1 quantity

```text
stated upper reference - tuned generic same-information baseline
```

on the exact outcome-informed B01 population?

I checked the accepted B01 card, result and summary; the earlier common-history competence freeze;
and the repository/worktree paths for a later RAW checkpoint trace. The current result has a stated
upper reference: for each EVAL row it reports every legal G16 value and uses
`max_legal G16` as the zero-regret oracle. It also reports the action selected by the RAW learner at
SHORT and LONG. No completed update-`252..264` RAW-only trace, tuned generic-baseline result, or
saved baseline checkpoint is present.

## Directly observed gap and path

The existing RAW quantities are already upper-reference-minus-selected-action gaps because native
regret is defined row by row as

```text
max_legal G16 - G16(RAW_selected_action).
```

They remain useful raw observations:

| RAW checkpoint | KEEP mean gap | REPLAN mean gap | equal-side mean gap | exact actions |
| --- | ---: | ---: | ---: | --- |
| SHORT | `0.013163761979059926` | `0` | `0.006581880989529963` | `1/8`, `8/8` |
| LONG | `0` | `0.0066464623737892345` | `0.0033232311868946172` | `8/8`, `4/8` |

The original current-host artifact is
`temp/directions/commitment_residual_triggered_options/exp/balanced_residual_b01_r1_20260904/summary.json`,
SHA-256
`32549E0AA5C20DF7BD83F6E89DFB4073170BE45C266917E2100EB13550CB7843`. The fields are
`representations.RAW.{SHORT,LONG}.sides` and
`representations.RAW.{SHORT,LONG}.equal_side_regret`; row-level upper and selected values are under
`representations.RAW.{SHORT,LONG}.rows`. The tracked rendering is
`CRTO_BALANCED_RESIDUAL_B01_R1_RESULT_20260904.md#direct-scientific-observations`.

These values do **not** establish the requested headroom measurement. RAW-LONG is the registered
same-information comparator and failed the registered REPLAN competence conditions (`4/8` exact,
mean gap `0.0066464623737892345` versus `>=6/8` and `<=0.005`). RAW-SHORT fails on KEEP. Choosing
the better checkpoint separately by EVAL side would use the answer to construct the comparator;
it is not a tuned deployable baseline. A weak comparator is therefore an identification limit, not
a negative CRTO result and not evidence that headroom is absent.

The earlier logged deterministic script is described as a simple same-information diagnostic in
the common-history freeze, but no value for that script on this exact 48/16 B01 population is
published. Values from the older natural-support population cannot be transferred here.

## Minimal frozen discriminator

`CRTO_GENERIC_HEADROOM_A01_SCIENCE_CARD_20260904.md` freezes one no-learner A/RECON. It replays only
the exact existing 48 TRAIN and 16 EVAL rows, computes the already stated per-row G16 oracle, tunes
a finite generic action-rule family on TRAIN only, and reports the untouched EVAL G16 gap. It
creates no predictor, representation, neural gate, optimizer, checkpoint, or new B comparison.

This is deliberately narrower than a future host-wide trained-baseline set. A nonzero gap would be
headroom above the card's declared generic no-learner family, not proof that a competent trained
generic learner leaves the same gap. No relative percentage, MEI threshold, mechanism polarity, or
lifecycle action is attached to the result.

## Flags for the owner

- CRTO remains Portfolio `ACTIVE`; no conditional or `PARK` disposition is taken here.
- The proposed `5%` headroom floor and `25%` closure share are not ratified and are not used.
- The prior RAW update-`252..264` trace selection was never launched. This newer reversible
  object-tier selection supersedes it as the immediate discriminator without rewriting that
  historical decision.
- No new B is frozen or launched, and this intake performs no result-bearing invocation.
- The B01 `BR-E — COMPARATOR_WEAK` reading is preserved exactly and is not converted into negative
  mechanism evidence.

## Decisions this intake produces

### Decision 1 — route the A1 headroom question (object tier)

Options:

- **(a)** declare the existing RAW-LONG equal-side gap `0.0033232311868946172` to be the completed
  tuned-generic A1 headroom measurement;
- **(b)** retain the raw SHORT/LONG gaps as descriptive, reject a competent-baseline claim, and
  freeze one minimal no-learner generic-headroom A/RECON without launching it; or
- **(c)** apply the proposed `5%`/`25%` MEI numbers, make a lifecycle recommendation, or start a
  new B despite the missing competent baseline.

Recommendation: **(b)**. It preserves the direct oracle-gap observations, does not let comparator
weakness acquire scientific polarity, and supplies the smallest reversible object that can measure
a clean finite-panel gap without another learner.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (b).** The decision is reversible,
changes no frozen result, and remains entirely at object tier.

### Direction and Portfolio tiers

No direction-tier decision is produced. No direction family is opened, closed, parked, promoted,
or recast. No Portfolio lifecycle, priority, capacity, fusion, separation, registration, or
investment decision is made; CRTO's current `ACTIVE` row is returned to Root unchanged.
