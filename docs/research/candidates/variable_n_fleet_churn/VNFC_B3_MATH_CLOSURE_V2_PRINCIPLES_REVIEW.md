# VNFC-B3 exact-composite v2 RL principles review

Review identity: `VNFC-B3-RL-PRINCIPLES-SPRDA-20260812-02`  
Registered reviewer: `hmasd-research-principles-analyst`  
Reviewer task: `/root/em_variable_n_fleet_churn/vnfc_b3_math_closure_v2_principles`  
Candidate: `VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1`  
Reviewed revision: `SP-RDA-MATH-CLOSURE-20260812-02`  
Sources: the exact v2 science card and `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
only

## Conclusion

Disposition: `SCIENCE_REVISION_REQUIRED`.

The core SP-RDA algorithm, `E<=3N` proof, HANDOFF multiplier, reward-input
boundary, evaluation-count arithmetic, pressure algebra, seed-level inference,
and no-rescue logic are sound. The complete v2 revision is not mathematically
closed because its retained-panel construction contradicts its mass/geometry
pairing claim. Its stochastic-action/evaluation, certificate-history selection,
and opportunity-gate aggregation also leave outcome-changing choices unfrozen.
No Stage-1 production command may use v2.

## RL_PRINCIPLE_ANALYSIS_PACKET

### 1. SP-RDA and complexity

`CLOSED_AS_WRITTEN`: fixed `R=3` gives `E<=3|U|<=3N`; immutable keys, Floyd heap
construction, exactly `E` pops, and at most `|U|` residual updates yield
`O(NR+E log max(E,2))=O(N log N)` time and `O(NR+E+N)=O(N)` live memory. The
three-query attention and at most `3N` outputs are linear. Excluding initially
satisfied tasks is safe because residual demand never rises.

`CM_CHECK_ONLY`: exact edge/key/pop/update counts, comparison bound, no rekey or
repeat scan, no `N x N`, dynamic edge, fallback, rollout, retained tracing/log
object, or hidden superlinear live allocation.

### 2. Reward-input boundary and arm paths

`CLOSED_AS_WRITTEN`: the decoder is accurately described as reward-input-blind
conditional on bids; the bidder is reward-trained and the decoder contains strong
demand/capacity/fill/scarcity structure. ZERO, FROZEN, HANDOFF, G, PERMUTE, and RC
have distinct information/action paths. ZERO/PERMUTE are channel interventions,
not formal mediation. RC supplies unrestricted physical headroom only.

### 3. HANDOFF comparator

`CLOSED_AS_WRITTEN`: a switched survivor contributes two of three ticks, hence
`eta=2/3`; a kept survivor or joiner contributes all three, hence `eta=1`. HANDOFF
receives the known previous-role/handoff facts and the same release-all SP-RDA. It
is not reward-complete because joint clipping, waste, and global allocation remain
outside its fixed score. It is an appropriate primary frozen promotion comparator.

### 4. Latent action and PPO

The hierarchical likelihood and joint PPO principle are correct: leases precede
the structural edge set; bid latents exist only on that set; one unnormalized joint
ratio, clipped surrogate, centralized advantage, value loss, and team return occur
per trial.

`SCIENCE_REVISION_REQUIRED` for three residual choices:

- Define an arm-specific `L_A(o)`: it contains eligible real-role survivors only
  for adaptive-lease arms and is empty for release-all and frozen-lease arms.
  Deterministic fixed leases are conditioning inputs, not likelihood terms.
- If deterministic leasing leaves `E=0`, `A_lat` can be empty; define its entropy
  regularizer as zero rather than the undefined mean of an empty set.
- Freeze adaptive evaluation leases. A suitable deterministic rule is
  `ell_i=1[p_i(o)>=0.5]`, with a stated tie convention. Stochastic evaluation would
  instead need an exact counter-keyed tape and estimand.

### 5. Pressure, geometry, and physical mass

`CLOSED_AS_WRITTEN`: `rho[r]=log(d[r]/sum_i c_i[r])` is well-defined and exactly
`log(1/1.25)` in fixed mass. It is visible-statistic inductive bias, not new
information. Both geometry matrices have unit column sums, and the abstract
fixed/real mass construction separates roster cardinality from real capacity.

### 6. Realized mass/geometry pairing

`SCIENCE_REVISION_REQUIRED`: v2 promises paired mass/geometry worlds but keys
physical draws by mass and geometry. More importantly, it retains the first 24
certificate successes independently within each `schedule x mass x geometry`
stratum. Since certificate pass/fail depends on variant, retained raw indices can
differ and contaminate geometry and real-minus-fixed estimands with selection-law
differences.

A coherent count-preserving repair is:

- generate one raw base candidate per `seed x schedule x raw-index` from a key
  excluding mass, geometry, and churn;
- deterministically derive all four mass-by-geometry variants;
- apply the finite certificate routine separately to each variant;
- retain a raw base index only when all four variants produce both churn
  certificates; and
- retain the first 24 joint successes.

The resulting maxima remain 2,048 shared raw bases, 8,192 variant records,
65,536 certificate calls if the per-variant cap stays eight, 6,144 retained churn
worlds, and 122,880 executable Stage-1 evaluations.

Alternatively, remove paired mass/geometry claims and redefine the estimands over
distinct certificate-conditioned laws.

### 7. Certificate target law

The finite 64-candidate/eight-call/no-top-up arithmetic is bounded and correct as
a work cap. `SCIENCE_REVISION_REQUIRED` because “best pre-event service-only
return” has no equation and v2 delegates the certificate routine and call order to
CM. Which satisfying histories are returned changes observations and outcomes.

A successor must define:

- the exact pre-event service-only functional;
- exact optimization objectives and sequence within the solver cap;
- deterministic selection among multiple qualifying KEEP/SWITCH histories; and
- whether failure of that exact routine is certificate failure even when another
  search might have found a pair.

Solver/runtime failure must be distinguished from a scientific certificate miss.

### 8. Count arithmetic

`CLOSED_AS_WRITTEN`: per seed,
`768 worlds * 4 row orders * 5 executable arms=15,360`; over eight seeds this is
122,880. The 6,144 retained RC ceilings are separate. Stage-1 training is 32,768
trials and 4,096 optimizer steps.

### 9. Inference

`CLOSED_AS_WRITTEN`: seed is the independent unit; replicas/worlds/cells are
nested before `D_s`. Two-sided 95% superiority, explicitly one-sided 95%
noninferiority/recovery, and 90% TOST equivalence are correctly separated.
Statistical conjuncts form an IUT; descriptive assignment and engineering gates
make the complete release a broader operational conjunction. Other claims remain
marginal absent their own simultaneous family.

### 10. Activity and opportunity denominators

The estimand-specific principle is correct. `SCIENCE_REVISION_REQUIRED` because:

- “16 contested worlds” does not state whether it is per seed, pooled, per
  schedule, or aggregated across both schedules reaching `N=15`;
- assignment-disagreement rates do not specify pooled-world versus equal-weight
  seed/cell aggregation; and
- Stage-2 “both retention and release physically feasible” has neither a precise
  predicate nor an exact seed/schedule/cell denominator.

The successor must freeze seed, schedule, mass, geometry, churn cell, denominator,
and aggregation for every opportunity/descriptive gate. A pressure-level gate must
likewise define the cell and numerical distinctness rule.

### 11. Operations and claim language

`CM_CHECK_ONLY`: timer resolution, full event-decision latency, peak RSS/live
objects, every positive-capability edge to an initially deficient task, opaque
mapping, zero-bid equality, and exact solver/call ledgers. A statistical effect may
remain reportable after a practical scaling failure, but cannot release Stage 2 or
the bridge.

`CLAIM_NARROWING_ONLY`: “non-outcome-enriched” is too broad because certificates
themselves use offline physical-return predicates. Say that the finite panel is
selected only by preregistered certificate predicates and is never selected or
topped up using Stage-1 arm/intervention outcomes.

`CLOSED_AS_WRITTEN`: RC/no-rescue interpretation and conditional UAV ceiling are
otherwise sound. A HANDOFF, fixed-mass, association, complexity, or latency failure
cannot be rescued; RC cannot localize bidder versus allocator failure.

### RL formulation and dynamics

This is a cooperative one-step contextual allocation problem. The context is the
post-churn unordered roster, capacities, demand, prior roles, event kind, and size.
Optional leases change the free set and structural bid dimension; continuous bids
matter only when they cross immutable-key ordering boundaries. Accepted edges
remove agents from all later edges and deplete one residual, so each agent's
assignment depends on other bids despite no dense agent-agent learned path.

Fixed-variance Gaussian bids provide passive rank-order exploration; Gaussian
entropy is constant in the bid means. Adaptive leases add Bernoulli exploration.
Report assignment entropy, order changes, joint log-ratio variance, and PPO clip
fraction by `N` as diagnostics. One global `J` and one centralized critic supply
joint score-function credit, not per-agent causal decomposition.

The temporal object is one membership event, one allocation, and three held
physical ticks. Handoff is a one-tick physical consequence, not long-horizon
memory. Any adaptive lease claim is one-event retain/release only.

### Validation and residual questions

Required validation includes analytic SP-RDA guards, joint likelihood without
unused lease terms or latent-count normalization, exact panel keys/acceptance
indices/solver calls, opportunity denominators, assignment/clip diagnostics, and
no dense path. Residual questions include joint-ratio scaling with N, whether fixed
Gaussian noise crosses enough ordering boundaries, bidder value versus decoder
hand structure, transfer beyond N=15/three tasks, and future top-16 graph scaling.

## Production consequence

`SP-RDA-MATH-CLOSURE-20260812-02` must not receive Stage-1 production acceptance.
The prior acceptance remains non-operative. After the mandated independent Critic
review of this unchanged v2 composite, the owner must reconcile both packets and,
if required, freeze one indivisible successor revision. That successor requires a
fresh whole-composite review and explicit Root-to-CM delta acceptance before any
training, evaluation, certificate scan, or production command. Stage 2 remains
unauthorized.

