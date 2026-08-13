# CCIC B1 owner-prepared Root-to-CM handoff

```text
direction=covariance_calibrated_information_clock
revision=CCIC-B1-SCIENCE-20260812-05
supersedes_revision=CCIC-B1-SCIENCE-20260812-04_PRO_REVISION_REQUIRED
author=EM_covariance_calibrated_information_clock
handoff_state=OWNER_PREPARED_MATHEMATICALLY_CLOSED_ROOT_MAY_RELAY
scientific_activity_started=false
mathematical_closure=revision_05_CLOSED_EM_INTAKE_COMPLETE
construction_authorized=false
tests_authorized=false
compute_authorized=false
production_authorized=false
```

## Conclusion

This is a mathematically closed, constructible scientific handoff, not a
dispatch. Exact revision 05 received ChatGPT External Pro `CLOSED` and the
same-direction EM accepted the ruling without changing the card. Root may now
relay this packet to CM, but CM construction and every question-relevant action
still require Root's separate sequencing assignment.

The scientific source of truth is
`docs/research/candidates/covariance_calibrated_information_clock/CCIC_B1_SCIENCE_CARD.md`.
CM must not infer missing science, replace a literal copy with an independently
sampled equal value, turn the oracle into the deployed actor, or relax any
paired/matched boundary.

## What would be constructed after release

One analytic cooperative HMM toy and one shared-policy experiment with:

- hidden binary state, primitive horizon 30, flip hazard `0.04`, signal gain
  `0.75`, `N_train={2,5}`, `N_heldout={8}`, `k_train={1,3}`,
  `k_heldout={5}`, and `rho={1,0.5,0}`;
- ideal-real lineage-bearing packets accounted as one real scalar plus 64
  metadata bits, deterministic successful one-round
  all-gather, common action support
  `{SENSE,RELAY,COMMIT_MINUS,COMMIT_PLUS}`, and one actor call per agent;
- an analytic HMM/GLS Bayes object used only as theory and a separately named
  centralized `NUMERICAL-REFERENCE` used as teacher/reference;
- one frozen `5 -> 32 -> 32 -> 4` actor shared across agents, arms, `N`, and
  `k`;
- `CCIC-R1`, `ESS-SCALAR`, `RI-STRONG`, `INFO-FLEX`, and `ORIGIN-COUNT` arms,
  plus the declared diagnostics;
- 32 paired seed blocks, 256 evaluation episodes per `N x k x rho` cell,
  counter-addressed streams, fixed updates, no tuning, and no adaptive stop;
- exact collision, support, leakage, work, activity, inference, equivalence,
  and interpretation requirements from the science card.

## Scientific invariants CM may not change

1. A packet duplicate is defined by the episode-wide composite
   `origin_key=(origin_id,capture_tick)` and the same physical random variable.
   Every agent keeps a persistent assimilated-key ledger; later relays of an
   assimilated key contribute exactly `(0,0)`. Numerical equality alone never
   defines duplication, and an equal-valued fresh key remains new evidence.
2. Exact-copy invariance is conditional on matched successful receipt,
   latency, origin availability, topology, rounds, packet size, and contention.
3. The singular Gaussian likelihood lives on the replication-map support and
   uses the pseudoinverse identity in the science card. Per-copy noise/jitter is
   forbidden.
4. The scalar statistical channel is an ideal noiseless real. Do not encode it
   as binary64 or another finite word and then reuse the continuous Gaussian
   likelihood. The only fixed-width claim is 64 metadata bits; no bit-rate or
   quantization result is in scope.
5. `CORR` contains distinct origins with residual correlation `0.5`; `IND`
   contains distinct conditionally independent origins. Both must remain
   distinguishable from `DUP`.
6. Every deployed agent computes fixed-rank sufficient statistics and the
   shared actor locally. No execution-only global covariance, central posterior,
   oracle action, or centralized critic may enter.
7. The actor is trained once per seed from the frozen numerical-reference state
   grid and then reused
   unchanged across all arms. No arm-specific actor update is legal.
8. The covariance network sees only `(overlap_code,quality)` and never evidence
   values, received/unique count, multiplicity, `t`, `k`, rewards, future data,
   actor outputs, or held-out statistics.
9. Training is only the frozen `2 x 2` `N x k` support. All weights,
   normalization, thresholds, ranks, and temperatures are frozen before the
   `3 x 3` evaluation grid.
10. The exact phase-separated Philox counter map, `Y0` draw, state/snapshot
   construction, module order, losses, invertible RI/INFO targets, float64
   reductions, initialization, and minibatch mapping are science-bearing and
   may not be inferred or changed.
11. Latent/common/idiosyncratic/action base streams omit `N`, `k`, `rho`, and
   arm from their evaluation counter keys. Those axes select or transform one
   nested potential tape; training and inference occupy separate phase words.
12. Training seed is the inferential unit. Episodes and ticks are not treated as
   independent replicates.
13. Any missing required seed prevents an efficacy conclusion and is not
   replaced after activity.
14. `RI-STRONG` uses the invertible `asinh(Delta ell/8)` target and exact
   `8*sinh` inverse; posterior or increment clipping is forbidden.
15. Learned covariance calibration must pass the exact all-roster panel,
   including `N=8`; hard gates, 29-of-32 plus pooled gates, work replay, and
   interval families use only their declared aggregation rules.
16. The covariance loading is literally `u_i := softplus(b_i)` using Latin
   `u`; no `nu_i`, square-root, or alternative transform is available.
17. `INFO-FLEX` challenges only the analytic Gaussian evidence-update/posterior
   map conditional on the shared exact physical-time HMM transition. It does
   not challenge or identify that transition.
18. `J-SHUFFLE` uses the card's explicit nine-class successor cyclic
   permutation; a predecessor shift or any other rotation is forbidden.
19. Exact-copy loss identity is a deterministic certified family with point
   `[0,0]`, not a stochastic bootstrap family. The general zero-variance rule
   remains unresolved only for noncertified stochastic contrasts.
20. Work replay uses the exact fresh empty-ledger tables, expanded operation
   grammar, paired tuple counts, and separate 27-cell gates. A global median
   cannot establish work matching.
21. Covariance specificity uses both adjacent regime differences for every
   comparator and axis in one 12-contrast family; equality to a regime average
   is not uniformity.

## Preactivity deliverable, if later authorized

Before the activity criterion becomes true, CM would return a concise
certificate showing:

- literal frozen constants, ideal-real channel, and schemas;
- analytic `J` values and the support-qualified replication identity;
- the literal Latin-`u` covariance assignment and its unchanged use in every
  Woodbury, likelihood, gradient, `q`, and `J` expression;
- collision and `rho`-ordering fixtures;
- the same potential tapes, packet schema, transition/receipt law, action
  support, per-decision call opportunities, and stream pairing; realized
  histories/call totals are endogenous and reported rather than asserted equal;
- static absence of every forbidden covariance input;
- the deterministic exact-copy pathwise-identity proof and the literal
  nine-class successor permutation for `J-SHUFFLE`;
- coarse/fine numerical-reference stability; exact state/snapshot construction,
  phase namespaces, losses, initialization, reductions, and minibatches;
- at least 24 numerical-reference-information-sensitive states in the frozen
  96-state set;
- fresh result roots and projected compliance with 90 minutes, 4 GiB, 8 CPU
  threads, exactly 240,000 optimizer updates, and 60 million primitive ticks;
  eight full-rollout arms account for at most 53,084,160 evaluation ticks,
  while the remaining named diagnostics are shadow-only as specified.

Schema/unit/structural checks before labels, rewards, or stochastic tapes are
preactivity. Scientific activity starts at the earliest first learned update,
first learned evaluation on a frozen stochastic tape, or first result-bearing
endpoint computation.

## Required technical-result return, if later run

CM would report only technical facts needed for same-direction scientific
intake:

- whether the preactivity certificate passed and when activity began;
- whether all 32 paired seed blocks completed without substitution;
- the arm/cell/seed endpoint table and declared inference outputs;
- collision, `J` ordering, actor sensitivity, shuffled/clamped clock,
  all-roster covariance calibration, deterministic exact-copy identity,
  12-contrast regime specificity, and per-cell work/exposure outcomes;
- anomalies, missing data, resource use, and anything still unknown.

CM does not interpret support, alter the claim ceiling, or authorize another
surface. A no-data run is an engineering fact, not evidence against CCIC.

## Current owner disposition

Revisions 03 and 04 each received a natural ChatGPT Pro `REVISION_REQUIRED`
response, and the same-direction EM accepted their prospective science-bearing
definition defects before activity. Exact revision 05 then received natural
same-conversation Pro `CLOSED`; the EM accepted closure and made no subsequent
science change. Root may relay this exact owner packet to CM for technical
assessment/construction sequencing. No CM dispatch, construction, test,
compute, production, or scientific activity has yet occurred, and the
independently blind Gemini request remains `PREPARED_NOT_SENT`.
