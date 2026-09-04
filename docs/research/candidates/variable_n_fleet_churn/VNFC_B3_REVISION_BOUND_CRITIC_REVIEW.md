# VNFC-B3 revision-bound adversarial math and causal review

Review identity: `VNFC-B3-REVISION-MATH-CRITIC-20260812-01`  
Registered reviewer: `hmasd-research-critic`  
Reviewer task: `/root/em_variable_n_fleet_churn/vnfc_b3_revision_math_critic`  
Candidate: `VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1`  
Reviewed revision: `SP-RDA-COMPLEXITY-CORRECTION-20260812-01`  
Principles dependency: `VNFC-B3-RL-PRINCIPLES-SPRDA-20260812-01`  
Sources: the reviewed science card, `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`,
and `VNFC_B3_REVISION_BOUND_PRINCIPLES_REVIEW.md` only

## Conclusion

The sparse allocator proof passes, but the complete reviewed revision does not.
The Principles review correctly identified production-blocking defects in the
latent action, inference, pressure, panel law, and activity definitions. Its
repair needs two additions: the revision must define one joint PPO ratio and
clipped surrogate explicitly, and the churn-certificate generator itself needs a
finite attempt/solver-call law. The Critic also found that the frozen Stage-1
comparators omit known previous-role/handoff information visible to the learner;
the existing promotion claim therefore needs either a history-aware fixed
comparator and gate or an explicit ban on matched-baseline and UAV promotion.

The prior CM acceptance cannot remain operative for production. The allocator
subproof can carry forward, but a new prospective composite must be frozen and
explicitly rebound by CM before any production run.

## CRITIC_ASSESSMENT_PACKET

### 1. Complexity

For fixed `R=3`, the learned path emits at most `3N` bid means and uses `O(NR)`
work/storage. After leases, `|E|<=3|U|<=3N`. Candidate construction scans at most
`3|U|` structural pairs. One immutable key per retained edge, Floyd heap
construction, exactly `|E|` removals, and at most `|U|` successful residual
updates give

`O(NR+|E| log max(|E|,2))=O(N log N)` time and  
`O(NR+|E|+N)=O(N)` live memory.

Continuing to pop discarded edges after residual closure preserves the exact-`E`
scan. The Principles distinction between up to `3N` network scores and exactly
`E` allocator key evaluations is required and mathematically sufficient.

- `SCIENCE_REVISION_REQUIRED`: correct the false at-most-`E` actor-score wording.
- `CM_CHECK_ONLY`: one heap, exact edge/key/pop/update counters, no rekey/rescan,
  dense tensor, retained tracing/log object, fallback, or search; full-decision
  rather than allocator-only timing.

### 2. Reward-input blindness

The allocator is reward-input-blind only conditional on supplied bids. The bidder
is trained from `J`, and residual demand, capacity, fill, and scarcity are strong
service-aligned hand structure. Use exactly that narrowed statement. Rename the
frozen comparator to a preregistered comparative-advantage priority; it is not
known to be the strongest simple heuristic.

Classification: `CLAIM_NARROWING_ONLY`.

### 3. Information, action, and credit

The basic arm paths are coherent: ZERO is structured decoding with zero priority;
FROZEN adds comparative advantage; G adds learned agent-associated ranks; PERMUTE
preserves task-column/bid-row multisets while breaking receiving-agent association;
RC is unrestricted environmental headroom, not reachable-SP-RDA headroom.
ZERO/PERMUTE are channel interventions rather than formal mediation estimators.

The corrected stochastic order must be:

1. one forward pass emits authorized lease probabilities and at most `3N` means;
2. sample authorized leases;
3. build `U(ell)`, `delta0(ell)`, and the pre-bid structural `E(o,ell)`;
4. sample bid latents only for that structural set; and
5. store the joint action and old-policy joint log probability.

The complete revision must also freeze

`ratio_theta=exp(log pi_theta(A_lat|o)-log pi_old(A_lat|o))`

and apply one clipped PPO surrogate to this unnormalized joint ratio and one
centralized advantage per trial. The joint log probability cannot be divided by
agent/latent count; team return and value loss occur once per trial. Entropy may
be the separately defined mean over authorized latent variables. Per-agent or
per-edge clipping is not equivalent. No mask may depend on rank, winner/discard
status, final assignment change, or return.

Classification: `SCIENCE_REVISION_REQUIRED`.

### 4. Missing history-aware frozen baseline

The learner observes previous role, while ZERO and comparative-advantage FROZEN
omit it even though a kept survivor contributes on three ticks and a switched
survivor on two. A positive G contrast can therefore be elementary recovery of
known handoff physics rather than learned allocation value beyond a matched fixed
rule. PERMUTE cannot close that shortcut.

For the current promotion logic, add a preregistered reward-input-blind frozen
history/handoff comparator through release-all SP-RDA. A suitable form uses full
effective capacity for joiners or the previous role and `2/3` effective capacity
for another survivor-task pair, followed by the same comparative-advantage
arithmetic. Alternatively, narrow the candidate to ZERO/comparative-advantage
discrimination and prohibit matched-baseline or UAV-promotion claims.

Classification: `SCIENCE_REVISION_REQUIRED` for the existing promotion logic.

### 5. RC headroom and reachability

`RC-MIP-FROZEN` measures unrestricted physical headroom, not reachability through
SP-RDA. A switched survivor may close raw residual demand while contributing
nothing on tick zero; poor physical return can therefore be caused by bidder
learning, decoder reachability, or both. If all SP-RDA arms are below RC, the
combined package leaves physical headroom. Allocator attribution requires a
separately preregistered best-reachable-SP-RDA diagnostic. The family may still be
stopped without that attribution.

Classification: `CLAIM_NARROWING_ONLY`; remove the causal "allocator lacks action
support" statement.

### 6. Geometry, mass, churn, and pressure

Both geometry columns sum to the same task-wise block mass; fixed versus real mass
and the churn-certificate surface are coherent. The epsilon pressure expression is
not exactly constant. With positive registered denominators, use

`rho[r]=log(d[r]/sum_i c_i[r])`.

Then fixed mass is exactly `log(1/1.25)`. Coupled-minus-separable is effect
modification, not a feature-level mechanism. A ceiling-gap difference against the
same comparator is algebraically redundant with the return contrast.

- `SCIENCE_REVISION_REQUIRED`: pressure formula before Stage 2.
- `CLAIM_NARROWING_ONLY`: geometry/mechanism and ceiling language.

### 7. Inference and the release conjunction

The seed is the independent unit. Replicas, worlds, and cells are averaged before
forming eight seed contrasts; use `df=7`. Ordinary superiority uses the lower
endpoint of a two-sided 95% interval; explicitly named noninferiority/recovery
uses one-sided 95% bounds; equivalence uses the 90% interval strictly inside its
margin. Every condition must be mapped explicitly.

The statistical components form an intersection-union test, so the single
composite statistical assertion needs no multiplicity adjustment. The full
seven-way release also has descriptive assignment and engineering gates and is a
conjunctive scientific/operational rule, not one confidence-controlled hypothesis.
Point-estimate floors are practical gates; a CI excluding zero does not prove the
population effect exceeds that floor. Separate claims are marginal unless their
own simultaneous family is frozen.

Classification: `SCIENCE_REVISION_REQUIRED`.

### 8. Finite certificate and panel law

Removing arm/ceiling-outcome top-up is necessary but not sufficient: the earlier
churn-certificate rejection search is also unbounded and its screening solver
calls are outside the claimed retained-world ceiling count.

The replacement must freeze a numeric raw-candidate and solver-attempt ceiling per
seed and paired cell/stratum; scan candidates in ascending counter-keyed order;
retain the first 24 certificate-valid pairs within the cap; never top up from arm
outcomes; and declare the cell incomplete/non-identifying if fewer than 24 qualify.
Every certificate solver call is separately counted under the time/complexity
policy. After freeze, a low contested count may prevent the Stage-1 release but
does not erase completed contrasts.

Classification: additional `SCIENCE_REVISION_REQUIRED` beyond Principles.

### 9. Estimand-specific activity

A contrast becomes question-relevant when its own arms, paired worlds, mappings,
observables, and opportunities are complete. The full release is identifying only
with every gate input and scaling audit. A missing input neither erases a completed
contrast nor becomes a negative treatment response or evidence for another arm.

Classification: `SCIENCE_REVISION_REQUIRED`.

### 10. Operations and claim ceiling

Initial zero-capability and zero-residual edge exclusions are sound because
residual demand never rises. Finite memory ratios are diagnostics; the live-object
inventory and absence of dense paths establish linear memory. Practical latency
failure may block progression while leaving a return contrast reportable.

`CM_CHECK_ONLY`: latency protocol, peak RSS/live objects, edge coverage, opaque
mapping, zero-bid equality, RC solver certificate/tolerance, all screening versus
retained solver counts, and absence of dense/logging/tracing/fallback paths.

The maximum claim concerns `J`, not service alone, and is limited to the registered
certificate-conditioned panel, one held-out `N=15`, the combined learned bidder
and structured decoder, exact registered comparators, and fixed-three-task
`O(N log N)`/linear-memory deployment. It excludes arbitrary N, growing tasks,
feature-level mediation, best-reachable decoding, generic coordination,
long-horizon MARL, and UAV effectiveness.

## Production consequence

`SP-RDA-COMPLEXITY-CORRECTION-20260812-01` must be superseded. Production may
resume only after the owner freezes a new exact prospective revision, Root reviews
and relays its delta, and CM explicitly accepts the changed stochastic treatment,
comparator or progression ceiling, panel law, inference, activity, and counts.
Stage 2 remains barred until the revised Stage-1 conjunction passes.

