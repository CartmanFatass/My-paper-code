# SCDMP TBOV support-representation factorial count-semantics correction

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-TBOV-SUPPORT-REPRESENTATION-FACTORIAL-CHECKPOINT
revision=SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260820-03
supersedes_revision=SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260819-02
revision_scope=count_semantics_only
owner=EM_semigroup_consistent_duration_model_policy
composite_base=SCDMP_TBOV_SUPPORT_REPRESENTATION_FACTORIAL_CHECKPOINT_SCIENCE_CARD_20260819.md
scientific_activity_started=false
identity_or_coordinate_materialization_authorized=false
```

## Complete composite and sole revision

The complete prospective revision 03 composite is:

1. the entire exact revision 02 science card
   `SCDMP_TBOV_SUPPORT_REPRESENTATION_FACTORIAL_CHECKPOINT_SCIENCE_CARD_20260819.md`;
   plus
2. this correction, which supersedes only revision 02's assertion that the
   panel contains exactly `224,604,160` executed model-example evaluations.

Every other revision 02 sentence and scientific condition remains operative
without reinterpretation. In particular, revision 03 changes no question,
factor, cell, row, segment target, row weight, loss, model, initializer,
Fisher-Yates order, optimizer, logical step, seed block, evaluation panel,
competence threshold, confidence family, effect definition, first-true branch,
modifier, activity boundary, strongest alternative or claim ceiling. The
inactive revision 02 HMAC namespace and all of its domain labels are preserved;
no revision 02 master or derived identity was ever materialized.

The replacement count semantics below are complete. No unregistered
relation/order path, dummy evaluation, padding example, repeated example,
balanced prefix, truncated batch or alternative counting convention may be
added.

One **registered direct model-example evaluation** means one registered
training row-segment example or one registered direct evaluation query
evaluated once by one factorial cell. Vectorizing or batching several examples
into one model-function invocation does not change this unit: an invocation
contributes one unit for each registered example it evaluates. Every count in
this correction uses that unit and is not a count of framework-level function
invocations.

## Why the old total cannot be an executed-count contract

Revision 02 defines only direct checkpoint training, untouched fit-support
evaluation and direct target diagnostics. Its inherited `224,604,160` total
also counted `19,906,560` model-example evaluations from four copies of the
old r07 correct/reversed composed-path evaluation. Those paths are not an
observable of this checkpoint-only factorial and are explicitly excluded by
the card.

Removing those evaluations yields the prospective value `204,697,600`, but that
number is not an exact realized model-example count either. Every cell performs 600
logical 256-row steps: 37 complete 4,096-row epochs followed by the first
2,048 rows of a fresh Fisher-Yates permutation for epoch 37. Each support
panel contains exactly 2,048 rows at `k=4` and 2,048 rows at `k=10`, but its
final prefix is not stratified by duration. A `k=4` row has 10 legal nonempty
contiguous segments and a `k=10` row has 55. The number of direct segment
evaluations in the final prefix is therefore a blinded consequence of the already
frozen row order.

## Exact prospective and realized accounting law

For seed `s in {0,...,9}` and support level `a in {S0,S1}`, let

```text
n10_s,a = number of k=10 rows among the first 2,048 rows
          of support a's fresh epoch-37 Fisher-Yates permutation.
```

The two representation cells at the same `(s,a)` use the same permutation, as
revision 02 requires. For either representation cell, the 37 complete epochs
contain exactly

```text
37 * (2,048*10 + 2,048*55) = 4,925,440
```

direct training segment-example evaluations. Its final 2,048-row prefix contains exactly

```text
(2,048-n10_s,a)*10 + n10_s,a*55
= 20,480 + 45*n10_s,a
```

such evaluations. Hence:

```text
TRAIN_CELL_ACTUAL_s,a = 4,945,920 + 45*n10_s,a

TRAIN_PANEL_ACTUAL
  = 2 * sum_s,a TRAIN_CELL_ACTUAL_s,a
  = 197,836,800 + 90*sum_s,a n10_s,a.
```

The direct evaluation family is exact and unchanged:

```text
untouched fit-support direct examples =    40,960
target-diagnostic direct examples      = 4,976,640
DIRECT_EVALUATION_EXACT                = 5,017,600.
```

The realized full-panel direct model-example count is therefore

```text
DIRECT_PANEL_ACTUAL
  = 202,854,400 + 90*sum_s,a n10_s,a.
```

Because a uniform permutation gives `E[n10_s,a]=1,024`, the frozen prospective
expected direct-accounting value is

```text
E[DIRECT_PANEL_ACTUAL] = 204,697,600.
```

The exact attainable lattice, and therefore its numeric range, is

```text
DIRECT_PANEL_ACTUAL in
  {202,854,400 + 90*m : m is an integer and 0 <= m <= 40,960},

202,854,400 <= DIRECT_PANEL_ACTUAL <= 206,540,800.
```

`204,697,600` is only the prospective expected direct-accounting value used for
cost comparison. It is not an executed-count equality, cap, stopping rule,
activity threshold, treatment condition, competence gate, inferential
observable or branch input. The realized count is a deterministic accounting
consequence of the frozen blinded permutations. It is recorded with the
technically accepted complete atomic panel and is not exposed or interpreted
from a partial seed or cell.

The exact formula is a technical-conformance check, not a ninth scientific
branch. A packet that violates the formula is not technically accepted by CM;
the EM does not reinterpret such a mismatch through the revision 02 result
map.

## Scientific meaning of the final-prefix variation

Every cell still receives exactly 600 logical AdamW steps and 153,600 row
presentations. The direct loss first averages equally over a row's registered
segments and then averages rows equally, so the stochastic number of segment
evaluations does not change the frozen equal-row weighting law. It is a compute
consequence of the registered duration mixture and final permutation prefix,
not an additional dose or outcome.

At a fixed support level, `R0` and `R1` share the same rows and minibatch order,
so their realized prefix duration composition remains paired. Across `S0` and
`S1`, independent registered permutations can yield different `n10` values.
That variation remains part of the already stated total finite support-package
and optimizer-geometry estimand. It does not create a pure coverage claim, a
post-hoc adjustment, a seed repair or a new comparator. The realized count may
not be used as a covariate, exclusion rule, restart trigger, branch modifier or
explanation that overrides the frozen strongest alternative.

## Preserved interpretation and claim ceiling

The strongest alternative remains finite package and optimizer geometry:
support stratification changes roster regularity, fitted scales, standardized
loss geometry, finite prefix composition and AdamW trajectory; the context
representation changes parameter count, initialization, curvature, clipping
and moment history. A favorable result cannot uniquely identify coverage or
context conditioning as its mechanism.

The maximum possible claim remains exactly the revision 02 claim:

> On this exact fixed-four-carrier direct checkpoint task, under ten fresh
> paired seeds, 600 AdamW steps, the frozen `0.65` untouched-fit-support rule
> and simultaneous three-effect family, the prospectively specified training-
> support allocation, context-conditioned segment representation, or their
> interaction materially changed the direct checkpoint error ratio, with the
> reported four-cell competence vector.

No outcome establishes correct relation direction, semigroup or reward-cocycle
value, policy value, held-out/switch-`k` return or failure robustness,
arbitrary `k`, variable `N`, unique mediation, Stage B, second-surface, UAV,
safety or deployment value.

## Activity and authority boundary

Revision 03 remains prospective. Scientific activity begins at the exact
revision 02 boundary immediately before the first master candidate, seed
identity, stochastic row, coordinate, scale atom or parameter is materialized.
No such object exists.

The Root-applied Portfolio correction authorizes preparation and exact
same-conversation Pro review of this successor. It supplies no mathematical
closure, scientific approval, identity materialization or activity by itself.
This composite grants no source, build, test, runtime or resource authority;
any identity-free CM work proceeds only under the separate Root-issued
operational envelope and does not change this science.

Revision 03 is not operative for identity materialization or activity until
the existing SCDMP ChatGPT Pro conversation returns `CLOSED` on the complete
composite followed by same-direction EM intake. Heavy activity additionally
requires a later Root lease.

No r07 rerun, Stage B, relation assay, coordinate or checkpoint reuse,
threshold/seed/budget repair, factor or architecture search, second surface or
UAV action is authorized. The Gemini revision 01 advisory operation remains
observe-only/no-resend and non-gating.
