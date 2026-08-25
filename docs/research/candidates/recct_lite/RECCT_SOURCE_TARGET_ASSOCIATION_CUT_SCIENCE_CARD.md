# RECCT source-target association-cut science card

## Scientific identity

- Direction: `recct-lite-factorized-source-target`
- Treatment: `RECCT-SOURCE-TARGET-ASSOCIATION-CUT`
- Host: `RECCT-OrientationPairedRelayCancellation-v1`
- Evidence scope: ordinary finite exploratory evidence on this host and seed
  panel only

This is a new treatment because it changes the scientific comparison from
choosing among pointer rules to cutting the association between a source
pointer and its target. It is not a renamed or repaired RECCT-B4 run.

## Question

When target alternatives have enough held-out value separation to make pointer
choice consequential, does signed authenticated source credit obtain value
specifically from the intact source-to-target association, beyond both a
sign-destroyed magnitude rule and a direction-blind rule?

The question matters because a signed rule can select a different pointer
without using the correct source-target relation. A binding cut distinguishes
association-bearing credit from pointer diversity, magnitude, or topology-only
selection.

## Host and matched objects

The independent analysis units are eight master-seed pairs:
`(27201, 27202, 27203, 27204, 27205, 27206, 27207, 27208)`. Each pair contains
the ordered orientations `PLUS` and `MINUS`. The direction-blind tie bits are
fixed before construction as `(LR, RL, LR, RL, RL, LR, RL, LR)`.

For every pair and orientation, CM constructs one common backbone and disjoint
fresh source, target, and evaluation namespaces. Only the post-backbone model
and complete optimizer state may seed the source and target constructions.
Source data cannot enter target construction or evaluation; target outcomes
cannot enter a selector or the binding map.

The source capsule produces authenticated conditional LR and RL credits. From
the same source record, three rules return a pointer:

- `SIGNED`: choose by the signed conditional-credit mean;
- `SIGN_DESTROYED`: choose by the mean absolute conditional credit, with no
  sign access;
- `DIRECTION_BLIND`: choose only from the precommitted pair tie bit.

The target side independently constructs LR and RL one-port update cells from
the same target ancestor. Each cell is recomputed from a separate disposable
clone to detect mutation or cross-cell contamination. Both cells are evaluated
with zero updates on the same eight held-out exogenous tapes. This creates the
hidden outcome table

`Y[j,o,d]`, for pair `j`, orientation `o`, and target direction `d in {LR,RL}`.

One target bank and one matched evaluation-tape set are shared by all rule and
binding arms. Existing RECCT construction primitives may be reused, but the
observed RECCT-B4 target banks, tapes, outcomes, and statistics are not inputs
to this treatment.

## Intact and deranged binding

Before any source credit, target cell, or outcome exists, freeze the
orientation-preserving no-fixed-point map

`pi = (3, 0, 6, 1, 7, 4, 2, 5)`.

For rule `r`, let `s[r,j,o]` be its source pointer. The intact arm applies
`s[r,j,o]` to target table `(j,o)`. The deranged arm applies
`s[r,pi[j],o]` to the same target table `(j,o)`. The same `pi` is used for all
rules and both orientations. It preserves orientation and each rule's pointer
marginal while removing every source-pair's own target association.

The scientific treatment is `SIGNED x INTACT` versus `SIGNED x DERANGED`.
Its primary comparator is the same binding contrast under `SIGN_DESTROYED`.
The second comparator is the same binding contrast under `DIRECTION_BLIND`.
No arm receives additional training, target cells, evaluation tapes, or model
updates; arms only index the already hidden outcome table.

## Observables and inference

For each pair, first measure whether the target side can express a consequential
choice:

`X[j] = mean_o |Y[j,o,LR] - Y[j,o,RL]|`

and

`E_target = mean_j X[j]`.

`TARGET_EXPRESSIBLE` requires `E_target >= 0.05`. The value `0.05` is the
predeclared minimum material held-out value difference; if the target table
cannot expose that much average LR/RL separation, a binding effect of that
scientific size is not available to the selector. This is an effect-size
condition, not a floating-point identity check.

For rule `r` and binding `b`, define

`V[j,r,b] = mean_o Y[j,o,pointer(r,b,j,o)]`

and the pair-level binding effect

`B[j,r] = V[j,r,INTACT] - V[j,r,DERANGED]`.

The two primary pair-level interactions are

- `I_abs[j] = B[j,SIGNED] - B[j,SIGN_DESTROYED]`;
- `I_blind[j] = B[j,SIGNED] - B[j,DIRECTION_BLIND]`.

Also report, for every rule, how many of the 16 orientation units receive a
different target pointer under intact versus deranged binding. Each primary
comparison requires at least four of the eight pairs to contain an actual
pointer change for both rules in that comparison. If not, the planned cut did
not expose enough binding variation and its interaction is not interpreted.

The eight master-seed pairs are the only inferential units; PLUS and MINUS are
never treated as independent. For each interaction, enumerate all `2^8` joint
sign flips of its eight pair values. The one-sided exact p-value is the fraction
of sign patterns whose mean is at least the observed mean. There are two
predeclared interactions, so each uses `alpha=0.05`, giving familywise
one-sided `alpha=0.10` by Bonferroni. A narrow positive result requires, for
both interactions:

- mean interaction at least `0.05`;
- exact one-sided `p <= 0.05`; and
- positive interaction in at least seven of eight pairs.

All finite-value calculations use ordinary numerical tolerances. Bit-level
floating-point equality is not a scientific condition.

## Activity start and outcome map

Question-relevant scientific activity starts when the first finite LR/RL
conditional source-credit record is computed from a fresh source capsule.
Backbone construction before that fact is engineering and common training, not
an observed source-target contrast.

Interpret complete data in this order:

1. If the source credit, matched target table, binding arms, or all eight pair
   rows are incomplete, no association conclusion is available. Engineering
   causes return to CM; a completed but scientifically ambiguous row returns
   to this EM.
2. If `TARGET_EXPRESSIBLE` is false, do not interpret either binding
   interaction. The supported statement is only that this exact host,
   one-port target update, and held-out endpoint did not expose enough target
   value separation to test source-target binding. This is not evidence that
   signed credit, magnitude credit, or binding is generally ineffective.
3. If target value is expressive but a primary comparison lacks the required
   pointer-change exposure, report which rule did not vary; do not interpret
   the corresponding interaction.
4. If target value and both cuts are exposed and both positive-result rules
   pass, the result supports a signed, association-dependent value advantage on
   this fixed host and panel.
5. If the conditions are exposed but either interaction is nonpositive, the
   exact panel supplies no signed-specific association advantage over that
   comparator. A positive result against only one comparator is comparator-
   specific and does not support the full signed-binding claim. Positive but
   subthreshold or imprecise interactions remain unresolved at this budget.

The strongest alternative explanation for a positive interaction is that the
signed rule has a more favorable pointer-frequency or pointer-diversity pattern
on this finite panel, rather than carrying general authenticated causal credit.
The within-rule derangement preserves pointer marginals, and the two comparator
interactions reduce this explanation, but they do not eliminate host or panel
specificity.

## Budget and claim ceiling

Use one real foreground execution with horizon 32 and no preliminary smoke
run. The construction budget is 128 backbone episodes, 16 source episodes, 16
target episodes, and 256 held-out evaluation episodes: 416 environment
episodes, 13,312 joint transitions, 33,280 policy calls, 896 learner optimizer
transitions, 32 stored target cells, 32 independent recomputations, and 256
sign-flip patterns. Use one process and one thread. Expected operational bounds
are 1,200 CPU seconds, 1,200 wall seconds, and 2 GiB peak RSS.

The time and memory bounds schedule the real command; a missing resource probe
alone does not erase complete scientific observations. Truncation, OOM, an
extra process, changed seeds, changed comparators, or incomplete question-
relevant rows must be reported as concrete anomalies for owner intake.

Even the strongest outcome supports only a fixed-host, fixed-update,
fixed-seed-panel, one-step held-out association claim. It does not establish
general causal credit semantics, population robustness, long-horizon utility,
mediation, necessity of signed credit in other learners, or superiority of the
RECCT family.

## CM-buildable request

CM owns the implementation, focused contract checks, real launcher, resource
observation, engineering repair, Operator dispatch, and retained result. Build
the fresh association-cut runner around the accepted RECCT host and reusable
source/target construction primitives. Materialize the hidden target table
once, apply the frozen intact and deranged bindings without arm-specific
training or evaluation, report the expressibility and pointer-exposure facts,
compute the exact pair-level interactions and sign-flip inference, and return
question-relevant output or the concrete point at which it ceased to exist.
Missing code or adapters are CM work and do not change this treatment.
