# Causal Skill Operator Graph Design

- Date: 2026-07-10
- Status: user-approved research design
- Scope: radical HMASD+OPT redesign; design only, no implementation or experiment authorization

## 1. Technical Summary

Causal Skill Operator Graph (CSOG) replaces arbitrary skill labels, a separate
team-class latent, and preselected duration with three executable objects:

```text
OPT interaction state h_t
  -> causal individual operators O_k
  -> sparse executable team program graph G_t
  -> event-driven asynchronous execution
```

An individual skill is defined by a repeatable multi-step intervention effect
on the OPT interaction state. Team intent is the executable graph that assigns
and composes those operators; there is no separate team label that must later
be made actionable. Skill lifetime ends when the assigned operator completes,
stalls, becomes invalid, or leaves the calibrated model support.

A training-only world model discovers high-confidence reachable effects and
supports counterfactual diagnostics. It is not an input to the deployed actor.
Real forced-skill interventions remain the final evidence for operator validity.
The environment reward remains external. The only eventual intrinsic path is a
gated low-level operator-progress signal; the team graph is selected by external
return and may use the world model only as a counterfactual control variate.

## 2. Research Claim

The intended scientific claim is:

> In cooperative MARL, skills can be represented as causal operators over a
> learned interaction state. Sparse graph composition of these operators makes
> team intent directly executable, while effect-triggered termination produces
> heterogeneous asynchronous lifetimes without preselecting durations.

The claim has three independently falsifiable parts:

1. **Causal executability:** changing an operator code changes a real multi-step
   local behavior/effect process under matched initial context.
2. **Structural compositionality:** the program graph predicts and induces joint
   effects beyond individual operator marginals.
3. **Endogenous temporality:** operator completion and failure events produce
   nontrivial asynchronous lifetimes and outperform fixed/shared controls.

Task performance alone cannot establish any of these mechanism claims.

## 3. Binding Boundaries

- OPT remains a recognition substrate, not a controller or team skill.
- The deployed actor remains decentralized: `pi_i(a_i | o_i, z_i)`.
- Global state, program graph, world model, and raw communication indicators do
  not enter the deployed low-level actor.
- Environment reward remains external and is never relabeled as intrinsic.
- No intrinsic signal is computed from raw communication fields.
- New reward paths are default-off and require real intervention evidence.
- Every new mechanism supersedes an existing mechanism; CSOG is not added as a
  parallel reward stack.
- PPO samples, active nodes, recurrent state, and stored log probabilities do
  not cross policy-version update boundaries.
- 160k/320k runs are mechanism gates. Thesis-level task claims require mature
  approximately 1M-step, matched, multi-seed evidence.

## 4. Core Objects

### 4.1 OPT Interaction State

```text
h_t = stopgrad(E_OPT_target(s_t, o_1:n,t))
```

`h_t` contains the OPT prototype activations, relation structure, and compact
interaction aggregate required for generic multi-agent dynamics. A target OPT
encoder is frozen over one operator-discovery cycle so effect coordinates do
not move while operators are evaluated. The online encoder may continue to
learn, but promotion of new operators pauses whenever online/target drift
exceeds its calibration bound.

### 4.2 Training-Time World Model

```text
p(h_t+1:t+H | h_t, a_1:n,t:t+H) = M_psi
```

The world model is distributional and multi-horizon. An ensemble or equivalent
epistemic estimator reports uncertainty. It is trained from completed real
on-policy windows and is frozen before it supplies targets or diagnostics for
the next rollout. It never supplies an execution-time actor input.

### 4.3 Causal Skill Operator

```text
O_k : (h_t, o_i,t) -> p(delta_h_i,t:t+H | do(z_i = k))
```

`O_k` is shared across agents. It represents a context-equivariant reachable
effect field, not an agent identity or a fixed displacement. Its identity is
anchored by real trajectories and real forced interventions.

### 4.4 Team Program Graph

```text
Z_t := G_t = (V_t, E_t)
```

There is no independent sampled team-class label. Team intent is the program
graph itself.

Each node contains:

```text
agent or role slot
operator code
activation precondition
status: pending | active | completed | stalled | invalid
```

Each sparse edge has one generic type:

```text
enable | inhibit | co-activate | none
```

These types refer only to generic latent interaction events. They carry no UAV
or communication-specific semantics.

### 4.5 Event-Driven Lifetime

Normal operator lifetime is not sampled:

```text
T_i = first event time of {
  effect achieved,
  progress stalled,
  precondition invalid,
  calibrated support lost
}
```

Minimum dwell and maximum timeout remain as safety constraints. They are not
policy decisions, reward targets, or skill identifiers.

## 5. Discovering Reachable Operators

### 5.1 World-Model Fit

The model is fitted against persistence and action-shuffled nulls at horizons
H10, H20, and H50. Uncertainty must predict real error rather than merely grow
with horizon.

### 5.2 Reachable Effect Extraction

For a real trajectory window:

```text
e_t^H = h_t+H - h_t
```

Operator candidates are selected from high-confidence reachable effect windows.
The discovery objective balances:

```text
coverage       cover effects the current system can actually reach
separation     exceed matched-context natural trajectory noise
persistence    retain a coherent transformation through H50
equivariance   preserve operator meaning across agents and contexts
confidence     reject effects outside calibrated model support
```

Candidate grouping conditions on or matches initial interaction context. It
must not recover clusters primarily from agent id, duration, phase, or
pre-window history.

Free learnable effect prototypes are prohibited. The world model may propose
counterfactual candidates, but a candidate enters the codebook only if it has
real trajectory support.

### 5.3 Supervised Operator Distillation Before Reward

Opening an operator reward before the actor can execute operators would violate
the diagnostic gate. CSOG therefore uses a reward-off bridge:

1. assign each high-confidence real trajectory window to an operator candidate;
2. use the assigned code as a stopped-gradient label;
3. distill the observed actions into the skill-conditioned actor on current-
   policy windows;
4. test forced operator execution in the real environment;
5. open operator progress reward only after the real forced-intervention gate.

The distillation target is behavior that already occurred, not model-imagined
actions. This establishes execution capacity without treating a model
counterfactual as reward evidence.

### 5.4 Real Intervention Calibration

The definitive comparison is:

```text
same or matched initial interaction context
do(z_i = k_1) versus do(z_i = k_2)
between-operator effect versus within-operator repeat noise
```

Model-predicted separation without real separation retires the candidate.

## 6. Program Graph Generation And Execution

### 6.1 Sparse Autoregressive Generator

The graph policy follows the useful HMASD autoregressive assignment spirit:

```text
for each agent or role slot i:
    k_i ~ pi_operator(k_i | h_t, previous nodes)

for each bounded candidate relation (i, j):
    e_ij ~ pi_edge(e_ij | h_t, selected nodes)
```

The joint graph log probability is stored for high-level PPO. Sparsity and a
bounded edge candidate set prevent combinatorial graph growth. The initial
design permits at most one active node and one pending successor per agent;
longer programs are produced through local replanning rather than a deeper DAG.

### 6.2 Direct Actionability

Because `Z_t` is the executable graph, assignment is part of team intent rather
than a downstream variable. The former `Z -> xi` actionability problem is
removed structurally. No q_A reward is retained alongside CSOG.

### 6.3 Asynchronous Scheduler

Every issued graph must contain at least one executable root for each agent.
Pending successor nodes do not replace the current active operator until their
preconditions hold.

When a node closes:

```text
if a ready successor exists:
    activate it
else:
    replan only the affected agent and incident edges
```

Other active operators and recurrent states remain intact. A full graph replan
occurs only after major interaction-structure change, multiple critical
invalidations, absence of executable roots, program completion, or a policy-
version boundary.

### 6.4 Progress And Close Reasons

For operator `k`:

```text
Phi_k(h_t) = -distance(h_t, reachable_effect_target_k)
progress_i(t) = Phi_k(h_t+delta) - Phi_k(h_t)
```

Close semantics are:

- `completed`: real effect enters the calibrated target region;
- `stalled`: progress remains below threshold for a bounded window;
- `invalid`: graph precondition or dependency no longer holds;
- `uncertain`: support is lost and local replan is required;
- `timeout`: maximum safety bound is reached.

Only `completed` earns completion credit.

## 7. Objectives And Gradient Boundaries

### 7.1 Model And Codebook Objectives

```text
L_model =
    multi-step latent prediction
  + uncertainty calibration
  + intervention consistency

L_operator =
    reachable-effect coverage
  + matched-context separation
  + cross-context equivariance
  + temporal persistence
```

These losses update the world model, codebook, and associated representation
targets. They do not backpropagate into the policy.

### 7.2 Gated Low-Level Operator Signal

After the real executability gate passes:

```text
r_op_i,t =
    confidence_gate
    * clip(gamma * Phi_k(h_t+1) - Phi_k(h_t))
```

This signal:

- updates only the focal low-level executor;
- is computed from a model/codebook snapshot frozen before rollout;
- is zero outside calibrated support;
- ends immediately when the node closes;
- contains neither environment reward nor communication fields.

The policy objective is:

```text
J_policy =
    J_high_PPO(external SMDP return)
  + J_low_PPO(external return)
  + gate_exec * lambda_op * J_low_PPO(operator progress)
```

`gate_exec` opens only after the real G2 operator-executability gate defined in
Section 10 passes.

### 7.3 Team Graph Selection

The graph policy receives only cumulative external team return and event-time
bootstrap. Composition residual is diagnostic and is never maximized as a
reward, because destructive interaction can also create strong residuals.

### 7.4 Optional Counterfactual Credit Baseline

After graph composition evidence passes, the world model may provide a
stopped-gradient action-independent baseline:

```text
b_i_cf = E_k' Q_hat(h, replace_node(G, i, k'))
A_i_cf = Q_real(h, G) - stopgrad(b_i_cf)
```

The same construction may ablate one edge. This is a control variate for the
external-return policy gradient, not an intrinsic reward. The expectation is
computed from `h`, `G` without node `i`, and the current alternative-operator
distribution; it cannot condition on the sampled `k_i`. If calibration fails,
the graph policy uses the ordinary centralized critic.

## 8. Update Order And On-Policy Contract

Each rollout follows this order:

```text
1. freeze E_OPT_target, M_old, and the operator codebook
2. sample and execute an on-policy program graph
3. compute external returns and any already-gated r_op from the frozen snapshot
4. update low actor and graph policy with PPO
5. fit the world model on completed current-policy windows
6. refresh candidates only at the slow operator-discovery boundary
7. calibrate candidates using real forced interventions
8. promote or retire candidates for the next policy version
```

At a PPO boundary, active and pending nodes are closed with a valid bootstrap or
dropped. Graph commitments, high-level recurrent state, and stored log
probabilities are never reused under the next policy version. Simulator episode
continuity does not relax this learning-data contract.

## 9. Composition Evidence

The joint model is compared with an individual-marginal baseline:

```text
p_joint(delta_h^H | h_t, G_t)
p_marginal(delta_h^H | h_t, {O_k_i})
```

Required nulls are:

- node/operator shuffle preserving marginal frequencies;
- edge shuffle preserving node assignments;
- agent-matched composition shuffle;
- time shuffle;
- pre-window/history-only baseline;
- individual-marginal model without graph edges.

A valid graph must beat the marginal model and all structure-destroying nulls.
Removing a key node or edge must change real joint effects in the predicted
direction. q_D may not read assignment or graph structure directly and is not a
CSOG reward mechanism.

## 10. Pre-Registered Gates

| Gate | Question | Minimum acceptance criterion |
| --- | --- | --- |
| G0 Dynamics | Is the OPT latent dynamics model trustworthy? | H10/H20/H50 beat persistence and action-shuffle nulls; H50 error improves at least 10%; held-out uncertainty/error Spearman rho at least 0.3 |
| G1 Reachability | Do stable reachable operator candidates exist? | At least 3 supported operators; normalized usage entropy at least 0.8; no operator over 50%; held-out H50 between/within at least 1.2 |
| G2 Executability | Can the actor realize operator identity? | Real forced-operator H50 between/within at least 1.2; H50 ratio is not below H10; behavior-only held-out residual at least 0.05 with positive fraction at least 0.60 and above every pre/history/duration/agent null |
| G3 Composition | Does graph structure add joint semantics? | Joint held-out NLL improves at least 10% over individual marginals and beats every graph null; real node/edge intervention between/within is at least 1.2 in the predicted effect direction |
| G4 Utility | Does gated operator pressure help rather than distort? | Matched coefficient-zero control; G2 metrics remain above threshold; final 320k coverage is not more than 10% relatively below control; two seeds agree in direction |
| G5 Thesis | Is event-driven composition useful? | Approximately 1M-step multi-seed evidence beats best fixed/shared CSOG control and reaches coverage-equals-one step fraction at least 0.5 with low failed/zero-service episode fraction |

No later gate may compensate for an earlier failure.

## 11. Failure Handling

- **High model uncertainty:** set operator signal to zero and use the ordinary
  centralized critic.
- **Operator collapse:** freeze promotion and reduce the candidate set; do not
  add entropy reward to manufacture categories.
- **No stable reachable effects:** stop CSOG or fall back to the simpler
  Effect-Addressed Skill Codebook.
- **Reachable effects but failed actor execution:** replace skill conditioning
  capacity; do not increase operator reward.
- **Graph deadlock:** trigger a well-formed local/full replan, record the event,
  and give no completion credit.
- **Renewal chatter:** enforce minimum dwell; do not add task-specific switch
  penalties.
- **Permanent activation:** close as `stalled` at maximum timeout.
- **Representation drift:** pause operator promotion until target/model
  recalibration.
- **Composition failure after individual success:** retain the individual
  operator contribution and drop the team-graph claim.
- **Mechanism success without task benefit:** keep CSOG diagnostic or auxiliary;
  do not proceed to S7-S3.

## 12. Verification Requirements

### 12.1 Structural Invariants

- deployed actors cannot access the world model, global state, graph, or raw
  communication indicators;
- every graph has an executable root or an explicit replan outcome;
- graph log probabilities match executed node/edge decisions;
- pending nodes receive no executed-action log probability;
- uncertainty gating exactly zeros the operator path outside support;
- coefficient zero is behaviorally matched to the mechanism-off control;
- external and operator reward channels remain separately logged;
- all node close reasons and policy versions are traceable;
- active nodes cannot cross PPO update boundaries.

### 12.2 Evidence Splits

Train, validation, and test windows are grouped by environment, episode, or
trajectory. Adjacent windows from one trajectory cannot cross splits. Forced
intervention data is labeled and reported separately from observational data.

### 12.3 Null And Counterfactual Checks

All operator and graph probes receive the same capacity, optimization budget,
early-stopping procedure, and final held-out test. Final test data never selects
the stopping point. Device class is held fixed within a comparison.

## 13. Experiment Sequence And Cost Envelope

No experiment is authorized by this design document. Expected CUDA costs are
planning estimates that must be recalibrated after the first smoke.

| Phase | Purpose | Estimated CUDA wall time |
| --- | --- | --- |
| A | Offline world-model feasibility on existing real windows | 1-2 hours |
| B | 160k reward-off operator-distillation active/inactive pair and real executability gate | 1.5-2 hours per arm; 3-4 hours serial |
| C | 320k graph gate with operator progress coefficient zero and external-return graph PPO only | 2.5-3 hours per run; 5-6 hours for two seeds; 10-12 hours with matched graph-off controls |
| D | 320k operator-signal coefficient-zero vs active, two seeds | approximately 10-12 hours serial |
| E | 1M CSOG event/fixed/shared and HMASD matrix | approximately 7-8 hours per run before parallelism |

Compute-bearing work defaults to cloud CUDA. No phase may silently fall back to
CPU. Phase E is prohibited until G0-G4 pass.

## 14. Mechanism Budget

| Existing mechanism or branch | CSOG disposition |
| --- | --- |
| separate sampled team label `Z` | replaced by executable program graph `G` |
| q_A actionability reward | structurally superseded because graph intent includes assignment |
| q_d label-recovery reward | replaced by gated operator-progress execution signal |
| q_D team-label discriminator/reward | retired; composition uses graph-vs-marginal evidence |
| parallel independent assignment | replaced by sparse autoregressive graph generation |
| discrete duration policy | replaced by effect-triggered event lifetime |
| q_D target and horizon sweeps | closed in favor of graph counterfactuals |
| old intrinsic reward stack | not run in parallel with CSOG |

## 15. Fallback Portfolio

### 15.1 Effect-Addressed Skill Codebook

If reachable individual effects exist but graph composition is too complex,
team policy emits agent-wise latent effect targets that are quantized into a
skill codebook. This retains effect-grounded skills but drops graph dependencies.

### 15.2 Event-Triggered Causal Contracts

If operator semantics and composition pass but temporal coordination remains
the dominant issue, graph nodes are extended into explicit precondition/effect/
completion contracts. This is a later specialization, not a parallel initial
mechanism.

## 16. Prohibited Interpretations

- High world-model accuracy alone does not establish a skill.
- Operator usage entropy does not establish behavioral semantics.
- Strong composition residual does not establish useful cooperation.
- A 160k/320k task improvement does not establish final performance.
- Fixed/shared controls losing after unequal operator pressure does not establish
  event-driven lifetime superiority.
- Communication improvements remain benchmark diagnostics and cannot define the
  intrinsic objective.
- Model-generated counterfactuals cannot replace real intervention evidence.

## 17. Acceptance Summary

The approved design commits to the following decisions:

1. use a radical causal-skill redesign rather than another discriminator target;
2. use a training-only world model with decentralized model-free deployment;
3. discover operators from high-confidence real reachable effects;
4. require real forced interventions before opening operator reward;
5. define team intent as an executable sparse program graph;
6. remove policy-selected duration in favor of event-driven lifetime;
7. restrict operator intrinsic pressure to the low-level executor;
8. train the graph policy from external return only;
9. treat model counterfactual credit only as a gated control variate;
10. retire superseded q_A/q_d/q_D and duration branches rather than stack them.
