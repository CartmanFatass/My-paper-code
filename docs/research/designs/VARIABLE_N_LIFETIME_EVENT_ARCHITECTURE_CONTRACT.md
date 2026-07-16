# Variable-N + Variable-Lifetime Event Architecture Contract

Status: design contract; implementation and training are not authorized
Date: 2026-07-17
Owning disposition:
`docs/external-review/rounds/20260717_variable_n_lifetime_architecture/50_DISPOSITION.md`

## 1. Purpose

This contract freezes one shared execution and learning interface for two
competing policies:

- **F0 — Active-Set Scheduled Recurrent MARL**, the strongest ordinary-MARL
  reduction;
- **F1 — Exchangeable Exogenous-Opportunity Event-Frontier Commitment
  Editor**, the leading skill-based research family.

Both must eventually support:

1. episode-internal anonymous `JOIN`, temporary `LEAVE`, terminal `LEAVE` and
   `REJOIN` while preserving unaffected survivors;
2. heterogeneous realized individual skill lifetimes without a discrete
   duration action and without a full-team renewal barrier;
3. exact on-policy replay and duration-aware credit;
4. computation in active team size rather than maximum roster capacity.

F0 and F1 share every lifecycle, representation, low-policy, reward, credit,
collector and checkpoint contract. Their only algorithmic difference is whether
earlier applied edits alter later learned scores on the common legal support.
They share the same data-generation contract, external-randomness contract and
exposure budget. Their realized on-policy trajectories may diverge after the
mode switch changes a sampled action; that treatment-induced divergence is not
an infrastructure mismatch.

## 2. Non-goals

This contract does not add or authorize:

- a new environment, experiment, training launch or threshold;
- environment-specific intrinsic reward or reward shaping;
- a learned event-time hazard, point process or duration head;
- a sampled global team latent, bridge or default team discriminator;
- fixed slots, Hybrid Field-Slot, critical residuals or a sparse graph;
- a learned ordering pointer;
- a new low-level actor input;
- a rewrite of original `hmasd` or `hmasd_original`.

Existing environment-agnostic skill-semantic mechanisms, if enabled in a later
implementation, must be identical in F0 and F1 and remain outside the causal
intervention defined here.

## 3. Definitions

At primitive time `t`:

- `A_t` is the active member set;
- `F_t subset A_t` is the policy-opportunity frontier;
- `N_t = |A_t|`;
- `m_t = |F_t|`;
- `K` is the number of executable individual skills;
- `kappa_i` is an opaque lifecycle-routing key;
- `z_i` is member `i`'s current skill;
- `tau_i` is its accumulated active execution time for the current skill;
- `h_i` is its recurrent execution state;
- `x_i` is its ordinary policy-visible member/relational feature.

An **external membership event** changes which lifecycle is active. A **policy
opportunity** allows an active member to choose a commitment action. These are
different event owners and cannot share an actor likelihood merely because they
occur at the same primitive time.

## 4. Lifecycle state and visibility

### 4.1 Single authoritative policy lifecycle store

Ownership is split by domain, without a duplicated table:

```text
environment worker:
  physical simulator state, physical membership facts, environment RNG

collector:
  typed transport transaction only; no policy lifecycle state

event runtime:
  the sole policy-runtime LifecycleStore
```

The event runtime's store is indexed by `kappa_i`:

```text
LifecycleRecord_i = {
  status,
  membership_epoch,
  low_recurrent_state,
  high_recurrent_state_if_used,
  active_skill,
  skill_active_age,
  last_policy_event_time,
  next_exogenous_opportunity,
  open_event_trace,
  policy_version
}
```

Allowed `status` values are:

```text
ACTIVE | TEMPORARILY_ABSENT | TERMINAL
```

`kappa_i` and `membership_epoch` exist only to route exact state and reject
stale rows. They are stored in the ledger but never embedded, pooled, compared
or otherwise exposed to the policy.

The worker and collector may carry physical facts and transient transport
records, but neither may shadow the policy skill, age, hidden, opportunity or
open-trace fields. `StandaloneProcessAgent` also owns no event lifecycle copy.

### 4.2 Policy-visible member token

For an active member, the first reference token is:

```text
u_i = concat(
  x_i,
  skill_embedding(z_i),
  log(1 + tau_i),
  is_genuine_join,
  is_rejoin
)
```

For a genuine join with no incumbent skill, `skill_embedding(z_i)` is replaced
by one fixed, non-learned all-zero null vector. The join flag distinguishes this
state, and the action mask requires `SET`; no extra join-skill category is added.

The two lifecycle flags describe the current event type, not persistent member
identity. No permanent agent ID, roster index, lifecycle key, membership epoch
or padded slot index is policy-visible.

The exact contents of `x_i` remain the generic observation/relational contract
of the chosen environment. They may not include future membership, future
opportunity time, task oracle labels or reward-derived features.

## 5. Membership state machine

At one primitive time, membership handling uses this exact substep order:

1. advance active skill ages through the completed primitive transition;
2. close or truncate traces of members affected by an external leave using the
   old-policy value read defined below;
3. apply all external membership changes atomically;
4. form the post-membership active set and policy-opportunity frontier;
5. sample and apply policy commitment actions.

Thus external membership changes are fully applied before any policy token at
the same time, while a leaver's credit boundary is not evaluated from an
undefined post-removal member token.

Every membership boundary is transported as one atomic transaction:

```text
pre_membership_boundary_snapshot
  = post-transition, pre-removal active lifecycles and exact critic inputs

atomic_membership_delta
  = JOIN | TEMPORARY_LEAVE | TERMINAL_LEAVE | REJOIN
    plus lifecycle key and expected membership epoch

post_membership_pre_policy_snapshot
  = post-delta active set, event flags, new frontier and C_t^(0)
```

The event runtime validates the transaction against its sole `LifecycleStore`
and applies the delta exactly once. A temporary leaver's old-policy bootstrap
comes only from the first snapshot. The new frontier and initial commitment set
come only from the third. A stale epoch, missing snapshot or duplicated delta
fails before a policy token or primitive action is issued.

### 5.1 Genuine JOIN

```text
absent -> ACTIVE
new kappa
membership_epoch = 0
h_low = 0
h_high = 0, if present
z = undefined
tau = 0
```

The new member enters `F_t` immediately. Its legal policy action set contains
only `SET(z)` for `z in {0,...,K-1}`.

### 5.2 Temporary LEAVE

```text
ACTIVE -> TEMPORARILY_ABSENT
```

- The membership transition is external and has no actor log-probability.
- The open member event trace closes with a critic-only truncation at the leave
  boundary.
- The current low recurrent chunk also closes with a critic-only truncation.
- Its bootstrap value is read from the last active, post-primitive/pre-removal
  centralized context with an external-boundary flag. That value belongs to the
  old policy version and is stored before the member is removed.
- Recurrent state, active skill and skill age are frozen.
- Skill age and opportunity gap do not advance while absent, and inactive
  reward is not assigned to this lifecycle.
- Every other survivor's recurrent state, skill, age and event trace remain
  unchanged.

### 5.3 REJOIN

```text
TEMPORARILY_ABSENT -> ACTIVE
same kappa
membership_epoch += 1
restore h, z and tau
```

Rejoin is an external structural event with no actor likelihood. The restored
member also receives a policy opportunity in `F_t`, with normal `KEEP/SET`
support. The policy sees the restored semantic state and `is_rejoin=1`, never
the routing key. Rejoin opens a new low recurrent chunk and a new policy event
from the frozen hidden, skill and age state; its applied token samples and logs
a fresh opportunity gap.

### 5.4 Terminal LEAVE

```text
ACTIVE or TEMPORARILY_ABSENT -> TERMINAL
```

- Close any open trace with zero bootstrap.
- Delete the recurrent/skill state after the terminal row is finalized.
- Reuse of the same physical label later must create a new opaque lifecycle;
  it cannot resurrect terminal state.

The environment/collector must declare whether a leave is temporary or terminal
at the event boundary. The policy may not infer or relabel this after observing
future data.

## 6. Exogenous policy-opportunity ownership

The first architecture uses **exogenous per-member opportunities**.

The opportunity generator must be:

- independent of policy parameters and sampled policy actions;
- exchangeable under member relabeling;
- independent of task reward, goal identity, contact, phase, success predicate
  and distance;
- completely recorded for replay and resume;
- capable of producing staggered member frontiers rather than requiring every
  active member to be due together.

It may use a registered policy-independent episode RNG and generic lifecycle
time. The implementation plan must freeze one exact schedule before code work;
this contract does not permit environment-specific opportunity heuristics.

Consequences:

- Silent primitive steps have no high-policy action or survival likelihood.
- External membership events have no actor likelihood.
- The policy owns only commitment actions taken at an opportunity.
- Heterogeneous realized lifetime is the active execution time accumulated over
  any number of consecutive `KEEP` decisions before `SET`.

A learned termination or request time would require log-survival, termination
hazard and censoring factors. It is not part of F0 or F1 under this contract.

## 7. Commitment action

For an existing incumbent skill `z_i`, one combined categorical action has
exactly `K` effective choices:

```text
E_i(z_i) = {KEEP} union {SET(z) : z != z_i}
```

For a genuine join:

```text
E_i(join) = {SET(z) : z in [0, K)}
```

Semantics:

```text
KEEP:
  active_skill unchanged
  skill_active_age continues

SET(z):
  active_skill = z
  skill_active_age = 0
```

There is no separate duration head, no `SET(current)`, no post-sampling
conflict repair and no factor-wise clipping of subactions. Any hard legality
constraint is applied before sampling and stored exactly.

## 8. Reference active-set encoder

The first encoder is the smallest active-only permutation-compatible reference:

```text
g(C_t) = concat(
  sum_{i in A_t} phi(u_i),
  log(1 + |A_t|)
)
```

`phi` is shared across members. Sum/count, rather than fixed slots, is part of
the reference contract. An implementation may maintain the sum incrementally
by subtracting the old token embedding and adding the new token embedding after
an edit.

This is not a claim that sum pooling is universally sufficient. It is the
minimal F0/F1-shared starting point. Graphs, attention, slots, residuals or a
team latent require a later demonstrated information or scaling failure and
must replace, not stack on top of, this encoder.

## 9. Identity-free event-frontier order

After external membership events have been applied, the collector samples:

```text
sigma_t ~ Uniform(Perm(F_t))
q(sigma_t | F_t) = 1 / m_t!
```

Requirements:

- the RNG is policy-independent;
- every frontier permutation has equal probability;
- the sampled order is stored explicitly;
- the policy receives the focal member token and token position only through
  ordinary sequence execution, never a persistent order/slot embedding;
- relabeling active members relabels the joint distribution and ledger in the
  same way;
- replay uses the stored order; it never resamples an order.

`1/m_t!` may be retained in the augmented behavior probability for audit. It
is constant with respect to policy parameters and cancels exactly in the PPO
ratio. A learned pointer is neither used nor required.

## 10. F1 probability contract

Let `C_t^(0)` be the exact commitment set after external membership events and
before policy actions. For token `j` in the recorded order:

```text
i_j = sigma_t[j]
mask_j = Legal(C_t^(j-1), i_j)
e_i_j ~ pi_theta(. | u_i_j, h_i_j, g(C_t^(j-1)), mask_j)
C_t^(j) = Apply(C_t^(j-1), i_j, e_i_j)
```

The augmented joint behavior probability is:

```text
p_theta(sigma_t, E_t | C_t^(0))
  = (1 / m_t!)
    * product_{j=1..m_t}
        pi_theta(e_i_j |
                 u_i_j,
                 h_i_j,
                 g(C_t^(j-1)),
                 mask_j)
```

Every action is applied immediately to the working commitment set. Later
tokens therefore see:

- earlier applied skill edits and updated ages;
- incumbents of not-yet-processed members;
- exactly the legality state that existed at collection.

The applied working set, not token count, is the teacher-forcing prefix.

## 11. F0 probability contract

F0 uses the same active set, frontier, sampled order, action support, hard mask,
collector and ledger. Its learned scores are computed from the initial context:

```text
logits_i^F0 = f_theta(u_i, h_i, g(C_t^(0)))
```

For sequential feasibility, `mask_j` may still depend on `C_t^(j-1)`. On the
actions legal under both compared prefixes, learned F0 scores may not read the
applied prefix.

Thus:

```text
p_theta^F0(sigma_t, E_t | C_t^(0))
  = (1 / m_t!)
    * product_{j=1..m_t}
        CategoricalMasked(logits_i_j^F0, mask_j)[e_i_j]
```

F0 is not allowed to use an incorrect synchronous buffer or a weaker encoder.
Otherwise F1 would receive an artificial infrastructure advantage.

F0 and F1 use the same module graph, tensor widths and parameter count. F0
passes `g(C_t^(0))` through the same decoder input where F1 passes the current
`g(C_t^(j-1))`; no F1-only prefix adapter or extra hidden layer is allowed in
the first comparison.

For token `j`, both modes store and use the same centralized old value from the
exact pre-token working context:

```text
V_i_j = V_phi(u_i_j,
              h_i_j^pre,
              g(C_t^(j-1)),
              critic_global_features,
              boundary_kind)
```

The critic may see the applied working set in both modes. It may not read the
sampled current action, post-token set or future opportunity gap. Collection
and replay use the stored pre-token source tensors rather than reconstructing
them from a later roster.

## 12. Exact event ledger

Each policy token stores the actual structured data required to replay it. No
checksum or content digest substitutes for source tensors.

Required fields:

```text
environment_index
policy_version
physical_event_time
lifecycle_key_for_routing_only
membership_epoch
event_owner
external_membership_events_at_time
exact_active_lifecycle_list
exact_frontier_lifecycle_list
sampled_frontier_order
sampled_replacement_gap_for_each_served_owner
token_position
pre_event_member_tokens
pre_event_skills_and_ages
pre_token_working_skills_and_ages
pre_token_critic_member_and_global_source_tensors
exact_legal_mask
sampled_combined_action
post_token_working_skills_and_ages
old_token_log_probability
old_owner_centralized_value
owner_recurrent_state_snapshot
elapsed_physical_time_to_next_owner_boundary
terminal_or_truncation_kind
```

Routing keys may be used to locate rows but are removed before network input.
Replay must teacher-force the stored active set, frontier, order, action, mask
and working prefix. It must not:

- reconstruct a row from the current roster;
- resample order or actions;
- recompute a different legality mask;
- apply a conflict resolver after sampling;
- join rows across policy versions;
- expose routing metadata to the network.

## 13. Event return and trace

For owner `i`'s policy event `n`, let the next owner boundary be at primitive
time `t_{i,n+1}`:

```text
Delta_{i,n} = t_{i,n+1} - t_{i,n}

R_{i,n} = sum_{r=0..Delta_{i,n}-1}
            gamma^r * r_env[t_{i,n}+r]
```

For a nonterminal next boundary:

```text
bootstrap_{i,n} = gamma^Delta_{i,n}
                  * V_i(C_{t_{i,n+1}})
```

For terminal leave:

```text
bootstrap_{i,n} = 0
```

For temporary leave, the next boundary is the post-primitive/pre-removal value
snapshot defined in Section 5.2. It is a critic-only truncation: no leave action
or actor ratio is created. A new trace starts at the rejoin policy opportunity.

The reward is the unchanged environment team reward. It is not converted into
an intrinsic term. F0 and F1 use the same centralized active-set value inputs
and the same member-event return estimator.

Trace semantics:

- `lambda` advances only along successive policy-owned events of the same
  member;
- silent primitive steps do not create macro decisions;
- other members' events do not advance this owner's trace depth;
- external membership events have no actor ratio;
- temporary leave closes the row with critic-only truncation;
- a rollout update boundary bootstraps with the old critic and breaks the actor
  trace before the next policy version.

For a concurrent frontier, each token uses its owner's global-reward advantage.
Token losses are averaged over the actual frontier tokens so gradient scale
does not grow with `m_t`. This estimator is shared by F0 and F1; any later
credit replacement must be a separate causal intervention.

## 14. Recurrent and skill-state boundary

```text
active survivor:     recurrent state continuous
KEEP:                recurrent state continuous; age continues
SET:                 recurrent state continuous; new skill; age resets
temporary LEAVE:     recurrent state and skill commitment frozen
REJOIN:              frozen recurrent state and commitment restored
genuine JOIN:        recurrent state zero; skill assigned by SET
terminal LEAVE:      recurrent state discarded after finalization
PPO update boundary: simulator/lifecycle state may continue; actor rows do not
                     cross policy versions
```

The contract deliberately does not reset low recurrent state on `SET`; R48
provided no evidence that a skill-boundary reset is beneficial.

## 15. HMASD functions retained and removed

### Retained functions

- individual executable skill commitment;
- `pi_low(a_i | o_i, z_i)` skill bottleneck;
- persistence of a skill over multiple primitive steps;
- applied working-roster semantics;
- later-on-earlier cooperative assignment in F1;
- centralized cooperative value context;
- environment-agnostic requirement that skill semantics be behaviorally
  meaningful.

### Removed from the default architecture

- separately sampled global team latent `Z/g`;
- team-latent bridge and behavior probability;
- default team discriminator `q_D` and team-code classifier reward;
- discrete duration action/product;
- full-team synchronous renewal barrier;
- fixed roster slots.

Removal of default `q_D` does not authorize a replacement reward. Any retained
individual semantic objective must remain environment-agnostic, identical
between F0/F1 and separately justified by the research contract.

## 16. Algebraic reduction theorem

For any fixed `C_t^(0)`, frontier, recorded order and legal-mask sequence, let
`S_j` be the actions legal under both of two compared prefixes.

If, for every token `j` and every `a in S_j`:

```text
score_theta^F1(a | C_t^(j-1))
  = score_theta^F1(a | C_t^(0)) + c_j
```

where `c_j` is action-independent, then masked normalization removes `c_j` and
F1's learned conditional distribution equals F0's. The remaining sequence only
implements deterministic feasibility.

Therefore F1 has irreducible algorithmic content only if earlier applied edits
change later **relative learned scores on the common legal support**.

The eventual behavioral claim must additionally show that this dependence
improves cooperative utility relative to a capacity-, collector-, credit- and
data-generation-contract-matched F0 with the same exposure budget. Identical
realized on-policy trajectories are not required after the treatment changes an
action. Prefix-gradient existence alone, as in R49, is insufficient.

## 17. Permutation-compatibility statement

For any bijective relabeling `rho` of active members:

```text
g(rho(C)) = g(C)
q(rho(sigma) | rho(F)) = q(sigma | F)
p_theta(rho(E), rho(sigma) | rho(C))
  = p_theta(E, sigma | C)
```

provided member observations and lifecycle-event flags are relabeled with the
members. The opaque routing table may change keys under `rho`; because keys are
not network inputs, this cannot change logits or values.

Any implementation that requires a persistent slot, stable semantic order or
lifecycle-key embedding violates this contract and fails closed.

## 18. Capability and replacement map

| Capability | F0 | F1 | Deferred point process |
|---|---|---|---|
| Episode-internal join/leave/rejoin | shared lifecycle spine | shared lifecycle spine | could share later |
| Survivor continuity | yes | yes | could share later |
| Heterogeneous realized lifetime | exogenous opportunities + KEEP/SET | same | learned event time |
| Skill-conditioned low policy | yes | yes | optional later |
| Learned joint edit coupling | no; common-support logits independent | yes; applied-prefix conditioned | optional mark coupling |
| Exact probability and duration credit | required | required | additionally requires survival/intensity/censoring |
| Status | mandatory ordinary baseline | only leading research family | deferred |

Replacement ledger:

| Removed mechanism | Replacement |
|---|---|
| fixed `N_max` policy slots and dummy agents | active lifecycle table + active-only tokens |
| shared full-team renewal clock | exogenous per-member opportunity frontier |
| explicit duration category | run length of KEEP commitments |
| full-roster decode every check | decode actual opportunity frontier |
| sampled team latent / bridge | current active commitment set + applied prefix |
| stacked set/slot/graph summaries | one reference sum/count encoder |
| unowned synchronous return | member-event `gamma^Delta` return |
| learned pointer order | uniform external recorded frontier order |
| F2 name | independent mark policy in F0; learned time deferred |

## 19. Computational contract

With encoder width `d`, skill count `K`, active size `N_t` and frontier size
`m_t`, the reference target is:

```text
time:   O(N_t * d + m_t * (d + K))
memory: O(N_t * d)
```

Incremental sum updates may reduce repeated set aggregation. The policy may not
allocate permanent `[N_max, N_max]` pair tensors. A future sparse/global
relation encoder is a replacement decision only after measured necessity.

## 20. Collector and checkpoint fail-closed boundary

The future implementation must be default-off and versioned. Its checkpoint
schema must name:

```text
architecture_mode: F0 | F1
schema_version
snapshot_capability_name_and_version
encoder_state
policy_state
critic_state
optimizer_state
normalizer_state
lifecycle_table_schema
opportunity_generator_state
frontier_order_rng_state
open_event_trace_schema
policy_version
current_observation_and_state_boundary
collector_active_presentation
pending_membership_transaction
collector_pending_command_response_state
worker_environment_snapshot
environment_rng_state
```

Live resume is allowed only when all mode-specific modules, every live
lifecycle record, the collector boundary and the physical simulator can be
restored exactly. Missing opportunity/environment RNG state, order ledger,
membership epoch, open trace, pending transaction, simulator snapshot,
optimizer/normalizer state or policy version is a hard load error. A collector
or environment without the declared snapshot round trip cannot use event-mode
live resume; reset-and-continue is not a fallback.

Fresh-reset evaluation is a separate model/normalizer-only load and must
declare `runtime_state_absent_for_fresh_eval=true`. The mode and checkpoint
header are read before collector construction, environment reset or any
fixed-N agent construction. Schema 1/2 and permissive legacy migration never
enter the event loader.

At collection time, fail closed on:

- a lifecycle event without declared temporary/terminal semantics;
- stale membership epoch;
- a member in two lifecycle states;
- a policy opportunity for an inactive member;
- a mask/action mismatch;
- a working-prefix mismatch;
- an unlogged post-sampling repair;
- a replay row from another policy version;
- a routing key present in policy-visible tensors.

Original HMASD checkpoints and trainers remain untouched. Any later migration
requires its own explicit compatibility plan.

## 21. Contract review outcomes

### Outcome A — proceed to implementation planning

The contract may advance only if review confirms all of the following:

- no permanent semantic identity enters the policy;
- the augmented F0/F1 behavior probabilities are complete;
- external opportunity ownership is unambiguous;
- teacher-forced replay uses exact order, mask and working prefix;
- no conflict resolver operates outside the probability model;
- F0 and F1 share every correctness and capacity component;
- F1 has a direct parameter path from applied prefix to common-support relative
  scores;
- the F1-to-F0 reduction statement is valid;
- no team latent or representation stack is required for the contract to close.

Outcome A authorizes only a single shared implementation plan. It does not
authorize training.

### Outcome B — stop at F0

Stop the F1 route and adopt F0 as the current architecture explanation if
review finds any of the following is necessary:

- prefix affects only hard legality masks;
- learned logits do not read the applied prefix;
- semantic lifecycle identity or permanent slots are required;
- execution conflict is repaired outside the logged probability;
- correctness requires simultaneously adding team latent, slots, graph or
  learned hazard;
- F0 cannot receive the same lifecycle, credit or representation spine.

Do not respond to Outcome B by creating another isolated AR toy gate.

## 22. Review outcome and next boundary

The focused controller review reached **Outcome A**. The contract closes
without semantic identity, an unlogged repair, a team latent or a required
representation stack. The exact implementation boundary is now owned by:

`docs/research/designs/VARIABLE_N_LIFETIME_EVENT_IMPLEMENTATION_PLAN.md`

That plan freezes the external opportunity schedule, ragged tensor/storage
shapes, single F0/F1 mode dispatch, strict checkpoint boundary and focused
engineering checks. The second blind implementation-plan review returned
`MODIFY_PLAN` and authorized the finite document corrections now incorporated
here. Production implementation is conditionally permitted only after the
implementation plan contains the same ownership, transaction, critic,
live-resume and common-support evidence contracts. Its scope ends at one
hand-authored, deterministic production transaction trace. It does not
authorize a real environment, training, a testbed, scientific PASS/FAIL or
another automatic review round.
