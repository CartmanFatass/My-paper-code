# RECCT source-target association-cut EM intake

## Result interpreted

The real `RECCT-SOURCE-TARGET-ASSOCIATION-CUT` execution completed the frozen
scientific work: 416 episodes, 13,312 environment transitions, 33,280 policy
calls, 896 learner transitions, all 16 source rows, all 16 target rows, eight
paired analysis units, and all 256 sign-flip patterns. Time and memory remained
within the declared operating bounds. Historical RECCT-B4 data were not an
input.

The derangement changed enough pointers to expose both planned comparisons:
seven of eight pairs for `SIGNED`, seven of eight for `SIGN_DESTROYED`, and six
of eight for `DIRECTION_BLIND`. Therefore lack of a realized binding cut is not
the explanation for the observed result.

The target side did not expose a consequential choice. Every pair had
`mean_o |Y_LR - Y_RL| = 0`, hence `E_target = 0` and
`TARGET_EXPRESSIBLE = false`. All eight values of both `I_abs` and `I_blind`
were consequently zero. Their zero means, `p=1`, and zero positive-pair counts
are algebraic consequences of the outcome table and are not interpreted as
evidence against source-target binding.

## Scientific interpretation

This result answers the precondition rather than the binding question. On this
exact host, seed panel, one-port target update, evaluation schedule, and
held-out episode endpoint, LR and RL targets had identical observed value.
Once `Y_LR = Y_RL`, changing an intact source pointer to a deranged pointer
cannot change selected value, regardless of whether the pointer was produced
by signed credit, magnitude-only credit, or a direction-blind rule.

The following explanations of the zero interactions are removed for this run:

- incomplete question-relevant data or an exceeded operating bound;
- failure of the precommitted derangement to expose the two comparisons;
- sampling uncertainty in the interaction estimator as the immediate cause of
  the zero means. The observed target table itself makes every interaction
  exactly zero.

The result does **not** remove any of these scientific possibilities:

- signed source credit contains a useful target association that this target
  intervention cannot express;
- LR and RL commits differ internally but do not change the evaluated action
  distribution;
- the commits change proximal policy behavior but the finite episode metric is
  invariant because of host symmetry, action saturation, cancellation, reward
  coarseness, or insufficient downstream exposure;
- an expressive target intervention on this or another host would separate
  signed binding from magnitude-only or direction-blind selection.

The strongest alternative to “binding has no value” is therefore target-side
non-expression: the one-port LR/RL intervention and the chosen endpoint do not
form a causal readout of target direction. The source rules cannot be judged
until that readout exists.

## What is exhausted

The current combination of host, one-port target update, and held-out episode
endpoint is exhausted as a discriminator of source-target binding. Repeating
the same association cut with more seeds, a repaired threshold, or another
pointer permutation would still ask a question whose target side has not been
shown capable of producing a value contrast. No unchanged-treatment
replication is requested.

This does not exhaust the RECCT direction, authenticated credit, signed credit,
or association-dependent learning. It identifies the target intervention and
readout as the unresolved edge.

## Next worthwhile discriminator

If Root assigns further scientific value to this RECCT direction, the next
experiment should be a fresh **target-intervention expressibility localization**
without source-credit selection or derangement. Starting from matched
ancestors, compare LR, RL, and no-update target commits on fresh held-out states
where the two authenticated ports are action-relevant. Measure both:

1. a predeclared material proximal policy response, such as the change in the
   two authenticated port action probabilities or logits; and
2. the downstream held-out task endpoint on matched exogenous tapes.

This one-axis test divides the remaining explanations:

- no material proximal LR/RL difference means the present target update does
  not transmit direction into the evaluated policy, so no further binding
  experiment using that update is informative;
- a proximal difference with no downstream difference means the current host
  endpoint is insensitive, so the next scientific object must provide a
  genuine action-consequence readout before association is retested;
- differences in both proximal behavior and downstream value restore the
  missing support condition and make a fresh association-cut treatment
  identifiable.

The same-direction EM must define the material proximal observable and outcome
boundary before CM construction. This is a new scientific treatment, not a
repair or replication of the completed association cut.

## Claim ceiling

The maximum supported claim is:

> In this complete finite execution, the fixed RECCT host, one-port target
> update, and held-out episode endpoint produced zero LR/RL target-value
> separation in every paired unit; therefore the planned source-target binding
> interaction was not identifiable.

No claim is supported that signed credit, authenticated credit, source-target
binding, magnitude credit, or the RECCT family is ineffective. No population,
general-host, long-horizon, mediation, necessity, or superiority claim follows.
