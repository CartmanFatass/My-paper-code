# ACVC B1 scientific intake

Owner: `direction:acvc-counterevidence-veto` Explorer Manager  
Treatment: `ACVC-B1-LEARN-CORRECT-v1`  
Science card: [`ACVC_COUNTEREVIDENCE_VETO_SCIENCE_CARD.md`](ACVC_COUNTEREVIDENCE_VETO_SCIENCE_CARD.md)  
Result: [`ACVC_B1_RESULT.json`](ACVC_B1_RESULT.json)

## Result interpreted

The registered execution produced complete question-relevant data with no material
anomaly. Correct binding improved event-scene return relative to prospective random
reassociation: `tau_neg=0.546703`, with two-sided 95% interval
`[0.422530, 0.670876]`. The correct arm made no invalid completion. All-clean harm
was zero; harm to clean targets inside event scenes was `0.011012`, with one-sided
upper limit `0.017870`. These observations pass the frozen return, safety, and clean-
harm criteria.

The learned policy did not pass the frozen selective-handling criteria. Correct-arm
`D_joint=0.593854` with lower limit `0.390883`, below the required mean `0.90`.
Correct-minus-PERM and correct-minus-AUTH `D_joint` gaps were respectively
`0.455469` and `0.470000`, but their lower limits, `0.253464` and `0.267063`, did
not exceed the predeclared material gap `0.40`. Correct-arm `D_joint` also ranged
from `0` to `1` across the ten seeds, so the exact selective trace was not robust to
the registered learner seeds.

The deterministic exact-match alternative was stronger. `DET-BOUND` achieved event
return `3.46`, `D_joint=1`, zero invalid completion, and zero clean harm. Learned
correct binding had mean event return `3.316245`; learned-minus-DET was `-0.143755`
with 95% interval `[-0.270927, -0.016583]`. Thus the learned arm was not merely
unable to show the registered noninferiority margin: it was observably worse than
the deterministic rule on this finite panel. The result field
`all_prespecified_criteria_hold=false` is therefore the correct conjunctive outcome;
the individual primary, safety, and clean-harm predicates did pass, while four
selectivity or deterministic-comparator predicates did not.

## Scientific conclusion

This result supports one narrow mechanism claim: in this fixed constructed host,
preserving the association between a truthful negative verdict and its five-field
binding materially improves what an otherwise identical tabular learner obtains
relative to randomized association, without observed invalid completion or material
clean-target harm.

It does not support the registered stronger claim that the learner reliably acquired
selective bound-counterevidence handling. It also contradicts adaptive-learning
necessity or value for this B1 decision problem: exact-match routing already encodes
the sufficient decision rule and outperforms the learned policy. The positive
`tau_neg` is therefore evidence for correct semantic routing, not evidence that an
adaptive veto algorithm is better than a scoped deterministic protocol.

The strongest alternative explanation is `DET-BOUND`: authentication plus exact
event, epoch, target, predicate, and validity matching mechanically identifies the
only target requiring special handling. Return learning partially exploits that
feature but sometimes adds unnecessary actions or clean-target loss. No appeal to
general authority, unsafe completion, or randomized-binding leakage is needed to
explain the observed hierarchy.

## Relation to the variable-N / variable-k UAV objective

ACVC B1 is not a promising algorithm candidate under the project destination. It
has fixed agent roles and four fixed targets; it exercises neither within-episode
agent-count change nor variable skill period. It has no UAV-shaped dynamics or
toy-to-UAV robustness evidence. Most importantly, its adaptive component loses to a
simpler matched rule. Scaling this truthful exact-binding host to more targets would
increase bookkeeping but would not remove deterministic sufficiency.

The five-field binding remains a useful protocol primitive or control for a future
algorithm that actually addresses variable `N` or `k`. That retained primitive is
not itself an ACVC algorithm result. No unchanged B1 replication, extra seed panel,
budget increase, or learner tuning is scientifically requested.

## Smallest worthwhile reconsideration test

Further ACVC algorithm work is warranted only if a new treatment makes adaptive
judgment necessary and directly enters the project path. The smallest credible
successor is a new variable-`k` discriminator, not a B1 repair:

- individual agents execute skills with different within-episode periods and epoch
  changes, mapped to variable-duration UAV sensing, communication, charging, or
  motion skills;
- authenticated frames retain the five-field binding but have prospectively fixed,
  calibrated uncertainty or delay, so exact matching establishes relevance without
  making verdict truth and the optimal action deterministic;
- a size/period-compatible learned evidence gate is compared with the best matched
  deterministic confidence-and-freshness threshold, not with randomized binding
  alone;
- training covers a declared period family and evaluation uses held-out period and
  delay schedules; the toy must show a lower-bound robustness or task-return gain
  while remaining noninferior on invalid completion and clean-skill harm;
- only such a toy gain would justify the same-mechanism UAV-simulator check.

If the deterministic calibrated rule matches that successor on held-out `k`, the
adaptive ACVC algorithm line has no remaining project-level discriminator. Until a
meaning-complete variable-`k` treatment and explicit UAV mapping exist, there is no
next ACVC run.

## Claim ceiling

The maximum supported claim is:

> In one complete finite execution of the synchronous four-target host with a
> truthful fixed certifier, correct five-field association improved a tabular
> learner's event return over randomized association without observed invalid
> completion or material clean-target harm, but the learner did not meet the
> predeclared selective-handling criteria and was inferior to deterministic
> exact-match handling.

Nothing here establishes variable-agent or variable-period learning, dynamic
membership, delayed or uncertain evidence handling, robustness outside the ten-seed
panel, UAV transfer, cryptographic security, compromised-sender behavior,
deployment value, open-support generalization, or adaptive-learning superiority.
