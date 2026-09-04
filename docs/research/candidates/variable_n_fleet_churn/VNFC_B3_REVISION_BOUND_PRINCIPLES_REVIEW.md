# VNFC-B3 revision-bound RL principles review

Review identity: `VNFC-B3-RL-PRINCIPLES-SPRDA-20260812-01`  
Registered reviewer: `hmasd-research-principles-analyst`  
Reviewer task: `/root/em_variable_n_fleet_churn/vnfc_b3_revision_math_principles_retry`  
Candidate: `VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1`  
Reviewed revision: `SP-RDA-COMPLEXITY-CORRECTION-20260812-01`  
Sources: `VNFC_SCALABLE_REWARD_SOURCE_CUT_SCIENCE_CARD.md` and
`docs/project/EVIDENCE_COMPLEXITY_POLICY.md` only

## Conclusion

The `SP-RDA` complexity correction is mathematically sound. With three fixed
tasks it uses linear candidate storage, Floyd heap construction, immutable edge
keys, exactly one pop per edge, and worst-case `O(N log N)` event-decision time
with `O(N)` live memory. Task-to-agent attention is `3 x N`, not `N x N`.

The complete reviewed revision cannot remain scientifically accepted unchanged.
Prospective corrections are required for the stochastic latent-action and
log-probability boundary, contest-conditioned sample selection, confidence-bound
sidedness and intersection-union semantics, and estimand-specific activity.
Pressure algebra must also be corrected before Stage 2. These are pre-activity
definition corrections; they neither reject `SP-RDA` nor authorize production.

## 1. Complexity

For fixed `R=3`, `|E|<=3|U|<=3N`. Each retained edge has one immutable key.
Floyd heap construction is `O(|E|)`; exactly `|E|` pops cost
`O(|E| log max(|E|,2))`; at most `|U|<=N` successful assignments update
residual demand. Agent encoding, sum/mean aggregation, three-query task-to-agent
attention, bid emission, and the critic are `O(NR)=O(N)`. Full deployment is

`O(NR + |E| log max(|E|,2)) = O(N log N)` time and  
`O(NR + |E| + N) = O(N)` live memory.

### Science correction: distinguish bid scores from allocator edge keys

Classification: `SCIENCE_REVISION_REQUIRED`.

The reviewed card incorrectly says actor bids require at most `E` score
evaluations. After leases, or when an initial residual is zero, `|E|` can be less
than the up-to-`3N` bid means emitted by the network.

Exact replacement:

> For fixed `R=3`, the learned forward pass emits at most `3N` bid scores and
> uses `O(NR)=O(N)` time and live activation memory. Conditional on leases, the
> allocator constructs `|E|<=3|U|<=3N` edge records, evaluates exactly `|E|`
> immutable edge keys, Floyd-heapifies them in `O(|E|)`, performs exactly `|E|`
> heap pops at `O(log max(|E|,2))` each, and performs at most `|U|<=N` residual
> updates. Full event-decision time is
> `O(NR+|E| log max(|E|,2))=O(N log N)` and live deployment memory is
> `O(NR+|E|+N)=O(N)`.

`CM_CHECK_ONLY`: verify one heap build, exact `E` pops including after residual
closure, the comparison bound, and absence of hidden dense attention, sorting,
tracing, logging, or fallback objects. Empirical timing is not the asymptotic
proof.

## 2. Reward blindness

`SP-RDA` is reward-input-blind at deployment: it reads no `J`, waste coefficient,
handoff consequence, future fact, cell label, or ceiling output. It is not
structure-blind. Residual demand, capacity, fill fraction, and scarcity weight
are a strong service-aligned hand-coded controller.

Classifications: `CLAIM_NARROWING_ONLY`.

- Use: “`SP-RDA` is mechanically reward-input-blind at deployment conditional
  on its supplied bids; the learned bidder itself is reward-trained, and the
  decoder contains substantial demand/capacity structure.”
- Rename `FROZEN-RDA` from “strongest simple frozen priority” to
  “preregistered comparative-advantage frozen priority.” Its contrast does not
  dominate all possible simple heuristics.

## 3. Information, action, and credit paths

- `ZERO-RDA`: residual-demand controller plus deterministic ties.
- `FROZEN-RDA`: the same controller plus fixed comparative-advantage priorities.
- `G-RELEASE`: the same controller plus roster-conditioned, agent-associated
  learned rankings.
- `G-PERMUTE`: preserves each task column's bid multiset while cutting its
  association with the receiving agent inside survivor/joiner strata.
- `RC-MIP`: unrestricted environmental physical-return headroom only; it is not
  bidder- or `SP-RDA`-reachable headroom.

### Science correction: freeze the joint latent action and one-return loss

Classification: `SCIENCE_REVISION_REQUIRED`.

“Causally active latent bids” is undefined. A mask chosen from realized winners,
heap rank, assignment effect, or return would bias the likelihood-ratio update.
Broadcasting `J` also must not replicate one team trial as `N` examples.

Exact replacement:

> Let `L(o)` be the eligible survivor-lease variables. Sample leases `ell`, then
> form `U(ell)`, `delta0(ell)`, and `E(o,ell)` without inspecting any sampled bid
> value. Define
> `A_lat=(ell_i : i in L(o), z_i,r : (i,r) in E(o,ell))`, with
> `log pi(A_lat|o) = sum_(i in L(o)) log Bernoulli(ell_i;p_i(o)) +
> sum_((i,r) in E(o,ell)) log Normal(z_i,r;mu_i,r(o),0.20^2)`.
> A bid-log-probability mask may depend only on observations, sampled leases, and
> the resulting pre-bid structural edge set. It may not depend on realized bid
> rank, whether an edge wins, whether it is later discarded, whether it changes
> the final assignment, or observed return. Use one joint trial return, one
> centralized-critic advantage, and one PPO loss term per trial; do not replicate
> or sum the same team return as `N` separate training examples. Normalize entropy
> over the variables in `A_lat`.

In Stage 1, release-all, positive capacities, and positive initial demands make
the structural bid set the full `3N` set.

Classifications: `CLAIM_NARROWING_ONLY`.

- `G-ZERO` and `G-PERMUTE` are controlled bid-channel interventions, not formal
  mediation estimates. Joint return and assignment changes support only that
  value flows through nonzero, correctly agent-associated rankings; they do not
  identify which observation feature supplied the information.
- `RC-MIP-FROZEN` is unrestricted physical headroom. If all `SP-RDA` arms remain
  far below it, the combined tested bidder/allocator package leaves headroom; the
  result does not distinguish poor learning from allocator reachability. A
  best-reachable-`SP-RDA` diagnostic would be needed for that distinction.

## 4. Geometry, mass, churn, and headroom

The matched geometry algebra is correct: every separable column sums to
`(.80+.10+.10)m_r=m_r`, and every coupled column sums to
`(.48+.48+.04)m_r=m_r`. Task-wise mass is matched while within-agent opportunity
cost changes. `FIXED_MASS` fixes each column at `1.25d_r`; `REAL_MASS` permits
roster events to change physical mass. The churn certificates change assignment
history while retaining local feasibility.

### Science correction: exact pressure constant

Classification: `SCIENCE_REVISION_REQUIRED` before Stage 2.

With epsilon,
`log((d_r+1e-6)/(1.25d_r+1e-6))` is not exactly `log(1/1.25)` and varies with
`d_r`. All registered denominators are positive, so use:

> `rho[r]=log(d[r]/sum_i c_i[r])`. In `FIXED_MASS`,
> `sum_i c_i[r]=1.25d[r]`, hence every pressure coordinate is exactly
> `log(1/1.25)`.

Classification: `CLAIM_NARROWING_ONLY`.

The coupled-minus-separable contrast is geometry-specific effect modification,
not identification of a particular learned mechanism. If “reduced coupled ceiling
gap” means reduction relative to FROZEN, it is algebraically redundant because
`GAP_F,C-GAP_G,C=(RC-F)-(RC-G)=G-F`. Report ceiling gaps descriptively.

## 5. Seed-level inference and multiplicity

The independent unit is the seed. Row-order replicas, worlds, and cells are
nested. For seed contrasts `D_s`, use `n=8`, `df=7`, and
`SE=sd_s(D_s)/sqrt(8)`. A 90% interval wholly inside `[-0.03,0.03]` is the TOST
equivalence rule at `alpha=.05`.

### Science correction: sidedness and intersection-union semantics

Classification: `SCIENCE_REVISION_REQUIRED`.

Exact replacement:

> For every contrast, average row-order replicas within world, worlds within
> cell, and registered cells with equal weight within seed to obtain `D_s`,
> `s=1,...,8`. Let `Dbar=mean_s D_s` and
> `SE=sd_s(D_s)/sqrt(8)`. The two-sided 95% Student-`t` interval is
> `Dbar +/- t_(0.975,7)SE`; its lower endpoint is used wherever a superiority
> condition says “paired 95% lower bound.” A one-sided 95% noninferiority lower
> bound is `Dbar-t_(0.95,7)SE`, and a one-sided recovery upper bound is
> `Dbar+t_(0.95,7)SE`; use these only for explicitly designated noninferiority or
> recovery conditions. Equivalence uses
> `Dbar +/- t_(0.95,7)SE` and passes only when both endpoints lie strictly inside
> `[-0.03,0.03]`.
>
> The Stage-1 release hypothesis is an intersection-union test: its null is that
> at least one required component fails, and release occurs only when every
> component passes. No multiplicity adjustment is required for this single
> conjunctive release decision. Assignment-disagreement thresholds are
> finite-panel descriptive gates, not confidence claims. Geometry, pressure,
> lease, subgroup, or other standalone claims retain marginal intervals unless a
> separate simultaneous-claim family and correction are preregistered; they may
> not be presented as jointly familywise-controlled.

## 6. Activity, panel law, scaling, and edge exclusion

The conjunctive release design and the opportunity-not-response principle are
sound. A valid statistical effect can be reported while a latency/memory failure
prevents Stage 2 and UAV progression.

### Science correction: remove outcome-dependent contest enrichment

Classification: `SCIENCE_REVISION_REQUIRED`.

“Rejection-sampled until at least 16 contested among 24” is unbounded, changes
the estimand using ZERO/FROZEN/RC-MIP outcomes, and conflicts with the fixed
retained ceiling count unless screening solves are separately accounted.

Exact replacement:

> After a candidate world satisfies only the registered mass/geometry/churn
> certificate, retain it in ascending counter-keyed base-world order. Freeze the
> first 24 certificate-valid worlds in each cell. Do not reject or replace a
> retained world using ZERO, FROZEN, `RC-MIP` headroom, G, or PERMUTE. After the
> panel is frozen, compute the contested count. If a required primary cell contains
> fewer than 16 contested worlds, that cell lacks registered opportunity and the
> Stage-1 release decision is non-identifying; do not run Stage 2. Count every
> solver call used during certificate construction separately in actual runtime.
> The 6,144 figure refers only to retained evaluation-world ceiling calculations.

Deliberate contest enrichment would require another prospective revision with a
finite attempt bound, deterministic acceptance order, screening-solve accounting,
and claims explicitly conditional on the enriched law.

### Science correction: estimand-specific activity

Classification: `SCIENCE_REVISION_REQUIRED`.

Exact replacement:

> Activity is estimand-specific. A completed contrast becomes question-relevant
> when all of its arms, paired worlds, mappings, observables, and opportunity
> conditions are complete. The conjunctive Stage-1 release decision becomes
> identifying only when every input to all seven release conditions and the
> complete scaling audit is available. A missing input prevents release but does
> not erase completed contrasts; it is neither a negative treatment response nor
> evidence for another comparison.

`CM_CHECK_ONLY`: verify latency protocol, actual peak RSS, live-element inventory,
edge completeness, and bridge exclusions. The finite memory-ratio audit is a
diagnostic; the analytic inventory proves linear memory. Excluding zero-capability
or initially satisfied-task edges is sound because residual demand never rises;
all other service-capable edges must remain.

## 7. Claim ceiling

Classifications: `CLAIM_NARROWING_ONLY`.

- The gate concerns `J`, not service alone. Say: “improved the registered
  three-tick physical return `J`, equal to capped mean service minus `0.10` times
  capped mean waste.” A service-specific claim needs its own gate.
- Name the churn-certificate-conditioned registered panel. The claim is one
  held-out above-training size and the combined learned-bid/structured-decoder
  package, not arbitrary roster scaling or generic learned coordination.

## RL_PRINCIPLE_ANALYSIS_PACKET

- `candidate_and_sources`: `direction:variable-n-fleet-churn`;
  `VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1`;
  `SP-RDA-COMPLEXITY-CORRECTION-20260812-01`; sources limited to the science card
  and complexity policy.
- `RL_problem_formulation`: one cooperative contextual allocation after an
  exogenous membership event. A shared set policy supplies continuous bids and
  optional leases; a deterministic decoder supplies one task-or-DUMMY assignment;
  one common three-tick physical return trains the joint latent action.
- `effective_state_observation_action_change`: observations contain current
  capabilities, membership/history, task demand/index, event kind, and roster-size
  context. Bids change only assignments reachable through immutable `SP-RDA`
  ordering; leases change the free set, residuals, and candidate graph.
- `exploration_driver`: fixed-variance Gaussian bid sampling, Bernoulli leases,
  entropy, and advantage-weighted PPO. Exploration is behaviorally expressed only
  when sampled rankings alter assignments.
- `exploitation_driver`: contextual bid means exploit roster composition/history;
  `SP-RDA` exploits demand/capacity structure; FROZEN exploits comparative
  advantage without learning.
- `information_flow`: unordered agent/task inputs -> encoders/summaries/three-query
  attention -> bid means -> immutable edge keys -> heap order/residual gating ->
  assignment -> handoff physics -> service/waste/`J`.
- `credit_flow`: one global `J`, one joint centralized-critic advantage, and one
  joint score-function loss. ZERO/PERMUTE localize the bid channel but not the
  responsible feature.
- `temporal_process`: one membership event, one allocation, three held service
  ticks, and one-tick handoff; no repeated policy decision or endogenous churn.
- `multi_agent_strategic_effect`: common-payoff complementarity and one-role
  opportunity cost; no independently learning opponent.
- `statistical_interpretation`: eight paired seeds; seed-level Student-`t`; 90%
  TOST equivalence; explicit one-sided noninferiority; Stage-1 intersection-union
  release; no automatic simultaneous coverage for standalone claims.
- `simple_explanation`: the learner ranks agent-task edges; the structured
  controller turns ranks into an assignment; the test asks whether learned ranks
  beat zero and registered comparative-advantage ranks at one unseen larger roster.
- `constructive_refinements`: separate `3N` bid scores from `E` edge keys; define
  pre-bid latent action and one-return loss; correct pressure; freeze inference
  sidedness/IUT; replace contest rejection with a deterministic panel; narrow
  mediation/headroom/geometry/service language.
- `validation_requirements`: exact edge/key/pop/update counts, Floyd heap, no dense
  objects/fallback/search, full-decision latency, live-memory inventory, handle
  mapping, zero-bid equality, seed aggregation, and exact edge exclusion.
- `unresolved_principle_questions`: best physical return reachable through
  `SP-RDA`; effective assignment entropy; joint PPO ratio/gradient scaling with
  `N`; features driving useful bid association; transfer beyond the conditioned
  panel and single `N=15`; sparse-edge fidelity for more than three tasks.
- `production_consequence`: retain the `SP-RDA` complexity proof, but supersede the
  complete reviewed revision before production. Stage-1 corrections are required
  for latent-action credit, inference, panel law, and activity; exact pressure must
  be corrected before Stage 2.

