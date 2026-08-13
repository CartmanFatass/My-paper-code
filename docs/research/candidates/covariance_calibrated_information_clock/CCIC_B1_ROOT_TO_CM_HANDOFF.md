# CCIC B1 owner-prepared Root-to-CM handoff

```text
direction=covariance_calibrated_information_clock
revision=CCIC-B1-SCIENCE-20260813-08
supersedes_revision=CCIC-B1-SCIENCE-20260813-07
predecessor_disposition=PREACTIVITY_MODE_SPECIFIC_WORK_CAPACITY_UNCLOSED
author=EM_covariance_calibrated_information_clock
handoff_state=OWNER_PREPARED_CM_RELEASE_WITHHELD
scientific_activity_started=false
mathematical_closure=revision_08_PREPARED_NOT_SENT
construction_authorized=false
tests_authorized=false
compute_authorized=false
production_authorized=false
```

## Conclusion

This is a complete prospective scientific handoff, not a dispatch. Exact
revision 05 received Pro `CLOSED` but ended before activity because its work
gate was infeasible. Revision 06 received Pro `CLOSED` but ended before
activity because its observed-batch and zero-template outputs required two
functional learned evaluations while its one-call work object counted only
one. Revision 07 repaired that conflict, but Pro found that its initial
prospective-only and terminal modes lacked frozen useful-work and active-
capacity matching. Revision 08 freezes one common prevalidator, four exact
invocation modes, and one causally factored `RI-STRONG-v4` invocation; it
preserves `INFO-FLEX-v2`. Because this is a science-bearing correction, CM
release and every question-relevant action remain withheld until revision 08 receives
same-conversation Pro `CLOSED`, this EM intakes it, and Root separately
sequences CM.

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
- `CCIC-R1`, `ESS-SCALAR`, `RI-STRONG-v4`, `INFO-FLEX-v2`, and `ORIGIN-COUNT` arms,
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
14. `RI-STRONG-v4` makes one fusion invocation from the common canonical mode
   object. Its 83 scalars are exactly metadata `5 -> 3` (18), metadata
   `3 -> 16` (64), and `gamma_z` (1). Fixed width-eight means form
   `alpha,beta`; `r_J=(alpha+beta)/2` and
   `r_ell=(alpha+gamma_z)z+beta`. The evidence expression may see actual `z`;
   the prospective expression may not. Shared metadata features are evaluated
   once and each enabled scalar receives `r+tanh(r)` before ascending means and
   exact decodes. All 82 metadata scalars are active for prospective `J`; all
   83 are active when evidence is enabled. RI-v4 is intentionally advantaged
   by one total scalar over CCIC. A hidden second evaluation, clipping,
   feature-path leakage, ignored output, dummy arithmetic, or work-ledger-only
   increment is forbidden.
15. Learned covariance calibration must pass the exact all-roster panel,
   including `N=8`; hard gates, 29-of-32 plus pooled gates, work replay, and
   interval families use only their declared aggregation rules.
16. The covariance loading is literally `u_i := softplus(b_i)` using Latin
   `u`; no `nu_i`, square-root, or alternative transform is available.
17. `INFO-FLEX-v2` uses one invocation with separate 49-scalar observed-
   posterior and 30-scalar metadata-only prospective-information branches.
   The latter cannot see `q_hat`, observed posterior, or represented value.
   It challenges only the analytic Gaussian evidence-update/posterior map
   conditional on the shared exact physical-time HMM transition and does not
   challenge or identify that transition.
18. `J-SHUFFLE` uses the card's explicit nine-class successor cyclic
   permutation; a predecessor shift or any other rotation is forbidden.
19. Exact-copy loss identity is a deterministic certified family with point
   `[0,0]`, not a stochastic bootstrap family. The general zero-variance rule
   remains unresolved only for noncertified stochastic contrasts.
20. One identical deterministic sequential `PREVALIDATE` procedure owns
   validity, finite, quotient, ledger, order, cardinality, and alignment checks.
   Online it runs once per arm-local agent/decision and reports arm-local
   endogenous `V_mode`; matched replay runs it once per shared tuple and feeds
   both fusions, with common replay `V_mode` outside the differential boundary.
   Work replay uses exact
   canonical inputs for `BOTH`, `PROSPECTIVE_ONLY`, `OBSERVED_ONLY`, and
   `NEITHER`, expanded operations, the frozen cache-free liveness schedules,
   and active-capacity paths. Before activity it must reproduce the card's
   eight mode formulas, four peak pairs, four capacity pairs, all 108 mode-cell
   rows, and literal aggregate `passed=true`. Merely encoding rows or using a
   global median cannot establish matching.
21. Covariance specificity uses both adjacent regime differences for every
   comparator and axis in one 12-contrast family; equality to a regime average
   is not uniformity.
22. Every arm makes exactly one fusion invocation per agent per decision under
   the common four-mode certificate. For RI-v4 and INFO-FLEX-v2, batching or
   nesting a second learned row/head evaluation inside that nominal call is
   forbidden. At terminal support prospective information is zero; with no new
   evidence the observed increment is exactly zero; `NEITHER` evaluates no
   learned row; prevalidation mismatch fails before either arm runs.

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
- the deterministic exact-copy pathwise-identity proof, literal nine-class
  successor permutation for `J-SHUFFLE`, exact one-invocation causal branch
  tracing, and exact RI-v4/INFO-FLEX-v2 architectures;
- the identical online arm-local and shared matched-replay lifecycles of
  `PREVALIDATE`, exact canonical four-mode outputs, all modewise operation/peak/
  capacity formulas and liveness schedules, all 108 expanded mode-cell rows,
  every positive ratio `<=1.10`, exact `0/0` learned capacity in `NEITHER`, and
  aggregate `passed=true` before activity;
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
  12-contrast regime specificity, and per-mode/per-cell work, peak, capacity,
  common-prevalidation, and exposure outcomes;
- anomalies, missing data, resource use, and anything still unknown.

CM does not interpret support, alter the claim ceiling, or authorize another
surface. A no-data run is an engineering fact, not evidence against CCIC.

## Current owner disposition

Revisions 03 and 04 received natural Pro `REVISION_REQUIRED`. Revision 05
received natural Pro `CLOSED` but ended before activity on the deterministically
infeasible work gate. Revision 06 received natural Pro `CLOSED` but ended before
activity on its single-call/work-definition inconsistency. Revision 07 then
received Pro `REVISION_REQUIRED` because its work and active-capacity control
covered only `BOTH`, not the initial prospective-only or terminal modes. The EM
rejected value leakage, hidden second evaluation, padding, and gate relaxation,
and froze complete result-blind revision 08 with a common prevalidator, four
mode objects, and one-invocation RI-v4/INFO-FLEX-v2 branches. Revision 08 Pro
and independently blind Gemini requests are `PREPARED_NOT_SENT`; there is no
present CM release, provider turn, test, compute, production, or scientific-
activity action.
