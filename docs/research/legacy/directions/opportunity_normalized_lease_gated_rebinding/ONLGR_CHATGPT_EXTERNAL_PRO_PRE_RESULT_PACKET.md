# ONLGR dedicated ChatGPT External Pro pre-result packet

```text
status=PREPARED_UNSENT
provider=chatgpt
model=visible Pro
direction=opportunity_normalized_lease_gated_rebinding
review_id=ONLGR-PRO-PRE-RESULT-20260812-01
conversation=new direction-dedicated conversation
release_authority=Root only
provider_partition=blind to every Gemini prompt and answer
result_use=advisory causal/mathematical review; same conversation may later be
           reused for result convergence if Root retains the direction
```

This packet is frozen from the same prospective state as the separate Gemini
innovation packet. It has not been sent. A later transport operator must send
the question once in one clean native ChatGPT conversation, preserve the raw
answer separately, and never expose a Gemini answer merely to seek agreement.

## Frozen outbound question

# Rigorous pre-result review: opportunity-normalized lease-gated rebinding

Please act as a rigorous external scientific reviewer, not an approver and not
a code reviewer. Examine one direct variable-skill-period MARL candidate before
it is implemented or run. Test its causal identification, probability
mathematics, matched controls, claim boundaries, and most valuable correction.

The project seeks one shared algorithm and parameterization that handles an
externally changed high-level callback/skill period `k` and improves either
task performance or robustness against a matched fixed or adaptive baseline.
It need not also solve variable agent count.

The proposed candidate is Opportunity-Normalized Lease-Gated Rebinding
(`ONLGR-B1-MARKED-LEASE-CENSORED-RATE-v1`). In a 256-primitive-tick two-agent
tracking-relay toy, fixed-rate physics and sensors evolve independently of the
high-level callback grid. The agents choose `KEEP`, `REFRESH-SAME`, or `REBIND`.
Refresh preserves the binary tactic/binding and resets plan age; rebind flips
the binding; both cause explicit cost/downtime and start the same 12-tick
physical lease. A separate safety event forces an immediate same-tick refresh
or rebind, bypasses the lease, and is outside policy credit in every arm. At a
coincident routine callback, routine action is suppressed for both agents: the
affected agent records only the safety boundary and resets its risk origin;
the unaffected agent has only a dummy call and neither resets its origin nor
advances its own-boundary index.

At a routine callback, eligible exposure is the count of physical ticks since
the previous routine or forced boundary during which the lease allowed a
voluntary non-KEEP action. Lease-masked ticks contribute zero. One head first
chooses whether an event occurs and a conditional mark head chooses refresh or
rebind. The proposed treatment uses

```text
lambda = softplus(g(o,delta_t,e))
u = 1-exp(-lambda*e)
P(KEEP)=1-u
P(REFRESH)=u*rho
P(REBIND)=u*(1-rho).
```

The primary matched learner, `RAW-BOUNDARY-LEASE`, uses
`u=sigmoid(g(o,delta_t,e))`. A third learned arm uses
`q_1=sigmoid(g)` and `u=1-(1-q_1)^e`; it is mathematically equivalent to a rate
through `lambda=-log(1-q_1)`. All arms receive the same realized preceding
`delta_t`, eligible exposure `e`, observations, action masks, conditional mark
head, architecture, parameter count, initialization intensity, ordinary team
SMDP-GAE, PPO work, communication, and physical budget. RAW is therefore
capable of learning the same elapsed-time mapping; the intended claim is a
useful inductive bias under held-out schedules, not function-class incapacity.

The policy is feed-forward. It sees role, binding, a fixed-eight-physics-tick
mismatch cue, plan age, lease remaining, busy state, a two-bit partner summary,
prospective cause, backward-looking `delta_t`, and eligible exposure. It does
not see a schedule label, absolute time, callback count/history, future `k`,
switch phase, latent mode, reward, seed, or environment ID. At a switch, the
next interval is chosen exogenously after the current action. Named schedule
cells are evaluator groupings only.

Training uses one final checkpoint over constants `k={8,24}` plus midpoint
switches in both directions. The unchanged checkpoint is evaluated on held-out
constants `{4,16,32}`, midpoint `4<->32`, and 64-tick `4/32` alternation in
both phase directions. Ordinary team credit is physical-time SMDP-GAE with
segment discount `gamma_tick^Delta` and trace `lambda_tick^Delta`; complete
episode loss rows are weighted by their following physical duration and
renormalized within episode so a finer grid does not obtain more optimizer
mass merely from more callbacks. The entropy bonus on an eligible row is the
three-action entropy `H_Bernoulli(u)+u*H_Bernoulli(rho)`, with the same duration
weight; masked, `e=0`, and forced rows contribute zero policy entropy.

The primary outcomes are equal-weight mean return across the seven held-out
schedules and the minimum per-schedule expected return, computed inside each
of eight paired seeds. The proposed material effects over RAW are `0.02` for
mean and `0.03` for worst-schedule return, each with a paired two-sided 95%
Student-t lower bound above zero. Safety and matched-resource facts are hard
conditions. The exact conservative package is `6,782,976` team ticks under a
`7,000,000`-tick cap; the partition probe is analytic.

Mechanism controls include:

1. a 16-cell equal-time partition-refinement probe crossing role `{T,R}`,
   active binding `{0,1}`, mismatch cue `{0.25,0.75}`, and age `{16,32}`; it
   splits the same 32 eligible physical ticks into 32-, 16-, 8-, or 4-tick
   opportunities and measures first-event probability instability;
2. the mathematically equivalent probability-exponent arm;
3. a closed-loop evaluation-only exposure clamp: live masks, actions, state,
   physics, and reward evolve normally, but the actor/critic see
   `delta_t=e=8` at every lease-eligible routine row;
4. a validation-selected state-blind fixed-rate policy with the same lease and
   safety path, using the total tie order lower rate, then `rho` closest to
   `0.5`, then lower `rho`;
5. degenerate always-keep/refresh/rebind policies and a state oracle; and
6. a secondary bounded exact boundary yoke. On each matched ONLGR/RAW pair with
   the same `m>=2` interior dwell blocks, it checks at most 16 deterministic
   cyclic rotations. With frozen zero-based seed/schedule/episode ordinals
   `(p,c,n)`, it uses `C=min(16,m-1)`,
   `b=(17p+31c+n) mod (m-1)`, and shift
   `s_j=1+((b+j) mod (m-1))` for `j=0,...,C-1`; it selects the first rotation
   jointly legal for both arms. It keeps the ordered joint action and
   tactic sequence fixed and preserves exact action/mark/tactic, dwell, lease,
   cause, mask, cost, and simultaneity quantities. There is no outcome use,
   repair, or search expansion. Comparative `Psi` requires at least 15/16
   common eligible pairs in every seed/schedule. For every arm/schedule, the
   fraction of ticks whose joint binding/age/busy/lease signature changes must
   have mean at least `0.10` and a 95% lower limit above `0.05`; the claim is
   limited to this bounded cyclic support. The yoke applies only to native
   no-safety episodes; safety
   events and initial/terminal censored blocks stay at destination ticks.
   Native unyoked evaluation remains primary.

The complete prospective science card is in repository
`CartmanFatass/My-paper-code`, branch `aggressive`, at
`docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_VARIABLE_K_SCIENCE_CARD.md`.
Use it only as scientific context. Do not validate implementation, files,
tests, hashes, receipts, runtime mechanics, or transport.

Please answer these questions precisely:

1. Is the marked event law and lease-censored exposure definition coherent?
   Identify any interval-censoring, simultaneous-event, survival, or policy-
   gradient error and give the smallest exact correction.
2. Given that both heads observe `delta_t` and `e`, what can ONLGR-versus-RAW
   and ONLGR-versus-probability-exponent legitimately identify? State the
   strongest equivalence or non-identifiability result.
3. Does the physical-time SMDP-GAE, duration-weighted PPO, and marked-
   distribution entropy construction avoid opportunity-count credit and
   optimizer-exposure shortcuts without changing the intended return objective?
   If not, replace it with a correct matched construction.
4. Can current callback timing still act as a schedule shortcut or privileged
   predictor of future `k`? Distinguish legitimate elapsed-time adaptation from
   schedule-label leakage and propose the smallest falsification audit.
5. Is the equal-time partition probe sufficient to identify operational
   opportunity normalization? What result pattern across the three learned
   links would be decisive?
6. Is the bounded first-jointly-legal cyclic dwell-block yoke scientifically
   interpretable as a secondary alignment control on its stated support?
   Identify any selection, post-treatment, support, intervention-materiality,
   tactic-occupancy, or legality failure and propose the smallest correction.
7. Are the materiality, uncertainty, safety, resource, activity, and
   nondegeneracy rules sufficient to prevent a lease-only, fixed-cadence,
   always-KEEP, or safety-dominated false positive?
8. State the strongest alternative explanation, the maximum positive and null
   claim ceilings, and the single most valuable next discriminator before a
   continuous UAV-facing surface.

Do not rank unrelated directions, authorize implementation or compute, or make
a portfolio decision. Return every heading below exactly once:

### REVIEW_IDENTITY

### FORMAL_EVENT_AND_CENSORING_OBJECT

### COMPARATOR_CAPABILITY_AND_EQUIVALENCE

### SMDP_CREDIT_AND_OPTIMIZATION_MATCH

### LEAKAGE_AND_SCHEDULE_SHORTCUTS

### PARTITION_AND_YOKE_IDENTIFICATION

### SAFETY_RESOURCE_AND_ACTIVITY_GATES

### STRONGEST_ALTERNATIVE_AND_CLAIM_CEILING

### REQUIRED_CORRECTIONS

### NEXT_HIGH_INFORMATION_DISCRIMINATOR

### RESIDUAL_UNCERTAINTY

### INDEPENDENT_RESEARCH_DIRECTION_PACKET

In the last section provide `review_mode=pre_result_rigorous`,
`review_id=ONLGR-PRO-PRE-RESULT-20260812-01`,
`candidate_id=ONLGR-B1-MARKED-LEASE-CENSORED-RATE-v1`,
`required_correction_count`, `scientific_opportunity_count`, and
`formal_project_effect=none`.
