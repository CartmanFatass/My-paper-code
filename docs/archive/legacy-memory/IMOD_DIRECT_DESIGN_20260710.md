# IMOD-Direct: Interventional Multi-Agent Operator Decomposition

- Date: 2026-07-10
- Status: user-approved design draft; written-spec review and independent cross-family MARL review pending
- Scope: reward-off individual-skill identification under multi-agent interference
- Supersedes: graph-first CSOG as the active design direction
- Authorization: design only; no implementation, experiment launch, or reward-path authorization

## 1. Decision Summary

IMOD-Direct changes the order of evidence in the HMASD+OPT research line:

```text
frozen healthy policy
  -> randomized real skill-code assignment
  -> direct and spillover effect estimation
  -> policy-relative operator equivalence classes
  -> non-additive interaction audit
  -> evidence-earned graph or hypergraph, if needed
```

The graph is an output of intervention evidence, not an input to skill
discovery. A skill label is not an operator merely because it is used often,
predicted by a discriminator, separated in a learned embedding, or assigned by
a high-level policy. It becomes an operator only when randomized assignment
causes a stable, held-out, nontrivial effect on real behavior.

The first scientific question is deliberately narrow:

> Under a frozen, behaviorally healthy cooperative policy, do individual skill
> codes cause distinguishable multi-step behavior at all?

Failure stops the line before a world model, graph, asynchronous compiler, or
new intrinsic reward is introduced.

## 2. Research Claim And Claim Boundary

The strongest currently defensible claim is:

> A reward-off intervention-first method can identify policy-relative
> individual skill operators under multi-agent interference, decompose their
> direct, teammate-spillover, and non-additive interaction effects, and admit
> only agent-equivariant composition structure supported by held-out real
> interventions.

This is not a claim that:

- a universal environment-level causal skill has been recovered;
- OPT embeddings are causal, Markov-sufficient, controllable, or metric;
- a world-model counterfactual establishes an operator;
- graph structure, skill composition, asynchronous options, or causal MARL is
  new by itself;
- mechanism evidence at 160k or 320k establishes final task superiority.

Every operator is indexed by the frozen policy, outcome definition, context
support, intervention distribution, and horizon. Transfer beyond those objects
is a separate empirical gate.

## 3. Literature-Bounded Novelty

The following broad claims are unavailable because of existing work:

- causal/dependency-guided skill graphs: SkiLD and COInS;
- factor-specific and low-side-effect skill discovery: DUSDi and focused skill
  discovery;
- skill composition: Option Keyboard and related successor-feature methods;
- controllability-aware skill geometry: CSD and METRA;
- model-based multi-agent causal influence or credit: MAGIC and MACD;
- multi-agent world models: MAMBA, MARIE, and CoDreamer;
- dynamic coordination graphs: Deep Coordination Graphs and Deep Meta
  Coordination Graphs;
- role specialization and permutation-aware MARL: ROMA and SPECTra;
- asynchronous credit or macro-action execution: MacDec-POMDP methods and
  asynchronous credit-assignment work.

The narrower gap targeted here is the combination of:

1. randomized real intervention on the assigned individual skill code;
2. potential-outcome semantics that explicitly allow teammate interference;
3. direct, spillover, and interaction decomposition;
4. equivalence-class merging of interventionally duplicate labels;
5. graph/hyperedge admission only after additive composition fails on held-out
   real intervention data;
6. reward-off gating before any policy is optimized for the diagnostic.

The literature search supporting this boundary is broad but not exhaustive.
Before a publication claim is frozen, each contribution sentence must receive a
claim-by-claim novelty audit against the latest primary literature.

## 4. Binding Project Constraints

- Environment task reward remains external and is never relabeled intrinsic.
- Raw communication indicators cannot define an intrinsic reward or operator
  identity. They remain benchmark diagnostics only.
- All new mechanisms and reward paths are default-off.
- No reward path opens from model-only, simulated-only, online-probe-only, or
  collapsed-policy evidence.
- `q_D` cannot read `xi` directly.
- `q_d` and `q_D` reward paths remain blocked by R24-1 on the existing evidence
  line.
- Every admitted mechanism retires or supersedes a named mechanism.
- 160k/320k runs are mechanism diagnostics, not final performance verdicts.
- Final task claims require mature, matched, multi-seed evidence near the
  agreed 1M-step scale.
- The deployed low-level actor remains decentralized and skill-bottlenecked.
- No stored decision, active process, recurrent state, or log probability may
  cross a policy-version update boundary.

## 5. Formal Setting Under Interference

Let `C_t` be pre-intervention context at a skill boundary and
`Z = (z_1, ..., z_n)` the complete assigned skill vector. For horizon `H`, let

```text
Y_i^H(Z)
```

denote the potential behavior/effect outcome of agent `i`. The dependence on
the complete vector is intentional: in cooperative MARL, one agent's treatment
can change another agent's outcome, so ordinary no-interference assumptions do
not apply.

For focal agent `i`, skills `k` and `k'`, and a pre-registered teammate
assignment distribution `pi_-i`, define the direct assigned-skill effect:

```text
tau_self(i, k, k', c; pi_-i)
  = E_Z-i~pi_-i [
      Y_i^H(k, Z_-i) - Y_i^H(k', Z_-i)
      | C_t = c
    ]
```

For teammate `j != i`, the spillover effect is:

```text
tau_spill(i->j, k, k', c; pi_-i)
  = E_Z-i~pi_-i [
      Y_j^H(k, Z_-i) - Y_j^H(k', Z_-i)
      | C_t = c
    ]
```

For focal agents `i,j`, skills `k,l`, and reference assignments `b_i,b_j`, a
pairwise interaction contrast is:

```text
eta(i,j,k,l)
  = E[Y | do(k,l)]
  - E[Y | do(k,b_j)]
  - E[Y | do(b_i,l)]
  + E[Y | do(b_i,b_j)]
```

These are intention-to-treat estimands for randomized assigned codes. They are
not conditioned on post-treatment completion, success, compliance, or task
return. Such conditioning would reintroduce selection bias.

The confirmatory primary estimand averages these contrasts over one frozen,
pre-registered eligible-context distribution. Context-specific effects are
secondary unless a stratum was registered as primary. Identification requires
random assignment within the eligible support, positive probability for every
primary treatment cell, one frozen meaning for each code, a recorded teammate
exposure policy, and no interference across independent environment resets.
Sequential carryover is avoided in the primary audit by allowing one focal
randomized intervention per reset; repeated within-episode interventions are a
separate longitudinal analysis.

## 6. Evidence Objects

### 6.1 Frozen Context Substrate

OPT supplies a skill-blind, permutation-aware context representation:

```text
C_t = stopgrad(E_OPT(s_t, o_1:n,t, history_pre_t))
```

Its role is adjustment, stratification, and transfer analysis. It is not the
primary outcome, a causal variable by declaration, a team skill, or an assumed
Euclidean effect space. The encoder and every normalization statistic are
frozen before confirmatory intervention data is analyzed.

The implementation may be described as original OPT only after a fidelity
audit establishes the required prototype, sparse interaction, disagreement,
and CMI contracts. Otherwise it must be named an OPT-style recognition
substrate.

### 6.2 Skill-Blind Outcomes

Primary outcomes are frozen, pre-registered summaries of real action and
physical/relational state evolution over `H in {10,20,50}`. The outcome
extractor may include generic quantities such as action trajectories, motion,
energy state, pairwise physical geometry, and teammate physical responses when
those variables are available across tasks.

Primary outcomes must exclude:

- skill code or a deterministic transform of it;
- `xi` or assignment/edit structure as a shortcut outcome;
- environment reward or return;
- raw communication indicators;
- post-hoc features chosen because they separate a successful run;
- a jointly trained embedding that can reshape itself around the labels.

Benchmark-specific communication and coverage metrics may be reported only as
secondary policy-health or task diagnostics.

### 6.3 Compliance And Assigned Treatment

The forced assignment must be shown to change the low-level action distribution
before an operator interpretation is possible. This first-stage compliance
diagnostic is reported separately from the ITT estimate. A weak first stage
means the code is behaviorally inert; it does not justify replacing ITT with a
post-treatment per-protocol estimate.

### 6.4 Operator Effect Profile

For skill `k`, define its held-out profile as the collection of direct effects
across horizons, context strata, and agents:

```text
P_k = {tau_self(i, k, k_ref, c; pi_-i)}_(i,c,H)
```

An operator is an equivalence class of labels whose profiles are statistically
and practically indistinguishable under a pre-registered equivalence margin.
Duplicate labels merge. Unsupported labels retire. The empty codebook is a
valid result.

Agent equivariance is a tested property: relabeling homogeneous agents should
permute the profile, not change its semantics. Failure narrows the result to an
agent-specific operator and blocks a shared-operator claim.

## 7. Randomized Real-Intervention Protocol

The minimal confirmatory audit uses a frozen mature policy and fixed skill
duration to remove duration as a treatment confound.

1. Freeze policy, OPT/context encoder, outcome extractor, treatment set,
   horizons, context strata, analysis procedure, and all thresholds.
2. For the primary audit, select one eligible boundary per independent reset
   using a pre-treatment rule, then randomize the focal assigned code within
   pre-registered context/support strata. Repeated within-episode interventions
   are excluded from the confirmatory primary endpoint.
3. Draw teammate assignments from a fixed reference distribution or hold them
   at a registered assignment vector. Record the exact exposure policy.
4. Execute the real environment. World-model rollouts do not enter the primary
   evidence set.
5. Retain all randomized assignments in the ITT sample, including failed,
   stalled, and apparently ineffective executions.
6. Split by environment trajectory or episode. Adjacent windows cannot cross
   train, validation, and final test partitions.
7. Fit context adjustment and stopping rules on train/validation only. Open the
   final test once.
8. Report all skills, agents, horizons, seeds, and null variants, including
   negative results.

Common-random-number or matched-reset evaluations are useful for variance
reduction only if treatment assignment remains randomized and each matched
pair is analyzed as one dependence block.

## 8. Ordered Diagnostic Gates

No later gate compensates for an earlier failure.

### G-1: Instrument And Support Validity

Required before interpreting effects:

- policy behavior is non-collapsed on pre-registered health diagnostics;
- assignment counts satisfy the power analysis in every primary treatment cell;
- context balance after randomization has absolute standardized mean difference
  below `0.10` for every registered covariate; otherwise collect the registered
  additional sample block or mark the confirmatory audit underpowered rather
  than reinterpret the endpoint;
- no outcome, completion state, or task return affects sample inclusion;
- the action-distribution first-stage effect exceeds the 95% upper bound of its
  shuffled-code null and the pilot-frozen practical minimum;
- grouped train/validation/test integrity and device consistency pass.

The reward-off pilot determines variance and freezes the practical minimum and
sample size. Pilot data cannot be reused as confirmatory evidence.

The numeric values in G1-G3 are provisional preregistration values inherited
from the project's prior gates and current effect-scale assumptions. The
independent review and reward-off power pilot may revise them before any
confirmatory data is opened. Once frozen, a failed value cannot be replaced by
a more favorable post-hoc threshold.

### G1: Direct Individual Operator

Using cross-fitted context-residual outcomes, define:

```text
R_direct^H
  = median between-skill profile distance
    / median within-skill repeat distance
```

G1 passes only if:

- `R_direct^50 >= 1.20` and its episode-bootstrap 95% lower bound exceeds `1.0`;
- the registered max-statistic randomization test rejects the global equal-
  effect null after accounting for all tested skills;
- the real effect exceeds shuffled-code, context-only, pre-window, agent,
  duration, and same-capacity reduced-input nulls;
- the H50 effect is not lower than H10 by more than the pilot-frozen tolerance;
- direction and effect-profile ordering agree across two independent healthy
  policy seeds;
- leave-one-agent-out transfer retains at least `80%` of the in-agent
  standardized effect and preserves the registered profile ordering.

Failure means no shared individual operator has been demonstrated. No graph,
world-model compiler, asynchronous operator scheduler, or operator reward may
be introduced to rescue the gate.

### G2: Teammate Spillover

Only G1-promoted operators are tested. A directed `i -> j` spillover edge is
admitted only if its standardized ITT effect:

- exceeds its shuffled-treatment and no-spillover nulls;
- has an episode-bootstrap 95% interval excluding zero;
- clears the pilot-frozen practical minimum;
- agrees in direction across two healthy policy seeds;
- is not explained by a direct-effect-only, capacity-matched model.

Direct effects may pass while G2 fails. In that case IMOD remains an individual
operator codebook and makes no team-interference claim.

### G3: Non-Additive Interaction

A pairwise edge or higher-order hyperedge is admitted only after a randomized
factorial audit. The interaction model and additive node-set baseline receive
the same inputs, effective parameter budget, validation procedure, and device.

G3 passes only if:

- held-out interaction-model NLL improves at least `10%` over the capacity-
  matched additive model;
- the real factorial interaction contrast has a 95% interval excluding zero
  and exceeds all assignment-preserving structure nulls;
- the effect direction replicates across two healthy policy seeds;
- replacing one member of the real treatment pair with its registered reference
  assignment changes the held-out outcome in the direction predicted by the
  fitted factorial contrast.

If additive composition is adequate, no graph edge is created. The simpler
operator set is the accepted representation.

### G4: Utility Or Reward Consideration

G4 is outside the current design scope. Passing G1-G3 establishes an evidence
structure, not permission to optimize it. Any future operator reward or
controller must receive a separate design, independent cross-family review,
coefficient-zero control, reward-ratio guard, and real-policy gate. Task reward
remains external.

## 9. Evidence-Earned Graph Semantics

The initial graph is empty.

- A node exists only for a G1-promoted operator equivalence class.
- A directed edge exists only for a G2-promoted spillover relation.
- An interaction edge or hyperedge exists only for a G3-promoted non-additive
  effect.
- Edge absence is a scientific result, not missing implementation.
- The graph is initially an evidence object, not a policy input.

Only after a stable graph exists may a separate design ask whether a controller
should select or compose operators. This avoids using an end-to-end graph model
to manufacture the structure it is later claimed to discover.

## 10. Role Of The World Model And Temporal Geometry

No world model is required for G-1 or G1. This is deliberate.

After sufficient real intervention data exists, a calibrated model may screen
candidate treatment combinations or estimate where additional real samples are
most informative. It cannot promote an operator or edge. Required model
diagnostics include intervention MSE, held-out NLL, interval coverage,
factual/counterfactual branch separation, and horizon-wise support detection.

The previous primary effect `h_(t+H) - h_t` is retired. A Euclidean OPT latent
does not guarantee temporal distance, controllability, irreversibility-aware
geometry, or causal semantics. A directed temporal/quasimetric representation
may later become a secondary module, but only after observable-outcome G1
passes and an independent representation gate shows incremental value.

## 11. Asynchrony And Duration

The first direct-effect audit fixes duration. This does not reject the project's
asynchronous-lifetime motivation; it isolates skill identity from duration.

Only after G1 passes may a later design test whether an operator persists,
completes, or loses support at variable times. That design must use an SMDP or
virtual-synchrony contract, preserve on-policy update boundaries, and compare
against fixed/shared duration under identical operator pressure.

Event-driven termination is therefore a downstream execution question, not
part of operator identification and not a standalone novelty claim.

## 12. Mechanism Budget

| Existing or proposed mechanism | IMOD-Direct disposition |
| --- | --- |
| q_d label-recovery reward | retired on this line; replaced by randomized direct-effect evidence |
| q_D team-label reward | remains blocked; spillover/interaction evidence replaces its diagnostic role |
| graph-first CSOG generator | retired before implementation; graph becomes an evidence output |
| Euclidean OPT latent delta as primary effect | retired; observable skill-blind outcomes are primary |
| world model as causal judge | retired; optional candidate/sampling aid only after real effects pass |
| preselected event-driven operator lifetime | deferred until operator identity exists |
| q_A actionability | remains a separately validated source-policy mechanism, not an IMOD effect or reward |

If IMOD later becomes a controller, it must explicitly decide whether q_A is
retained or superseded. The mechanisms cannot be silently stacked.

## 13. Null Controls And Multiplicity

Required controls are:

- shuffled assigned code within registered context strata;
- context/pre-history-only outcome model;
- agent-identity and role-slot baselines;
- fixed-duration and duration-label controls;
- action-only and effect-only reduced-input variants;
- same-capacity additive node-set model for interaction tests;
- observational policy-selected skill contrast reported separately from the
  randomized estimate;
- sham assignment that writes the already-active code where the environment
  contract permits it.

All variants use identical capacity, validation-based early stopping, split,
device class, and reporting. The primary horizon and global statistic are
registered before final-test access. Secondary skills, horizons, agent pairs,
and subgroups are reported with family-wise or false-discovery control and
cannot silently replace a failed primary endpoint.

## 14. Failure Dispositions

- **Randomization/support failure:** mark the audit invalid and repair the
  instrument; do not interpret effect size.
- **No first stage:** the skill-conditioning path is inert; no operator claim.
- **First stage but no G1 effect:** codes create short action differences but no
  stable behavior operator; stop the line rather than redesign the probe target.
- **G1 only:** retain an individual operator codebook; make no spillover,
  composition, graph, or utility claim.
- **G1 plus G2, G3 fail:** retain directed influence evidence but use an
  additive operator set; no interaction graph.
- **Agent-equivariance failure:** narrow to agent-specific operators and drop
  shared-code transfer claims.
- **World-model failure:** remove the model; real intervention evidence is
  unaffected.
- **Task improvement without G1:** no mechanism success; task variance cannot
  override the direct-effect gate.
- **G1-G3 success without task improvement:** evidence structure is valid but
  algorithmic utility remains unproven.

## 15. Research Sequence And Cost Envelope

This sequence is conceptual and does not authorize implementation or launch.

| Phase | Question | Estimated cloud-CUDA wall time |
| --- | --- | --- |
| A | Freeze outcome/context contracts and run a variance/power pilot | 0.5-1.5 hours |
| B | Confirmatory single-agent randomized direct-effect audit | 2-4 hours per policy seed |
| C | Spillover audit for promoted operators | 3-6 hours per policy seed |
| D | Selected pairwise factorial interaction audit | 6-12 hours for a bounded pair set |
| E | Optional world-model screening or controller design | not authorized; estimate only after G1-G3 |

The estimates use current R24/R25 collection pace as a planning prior and must
be recalibrated from Phase A measured throughput before any launch. Heavy,
multi-seed work defaults to cloud CUDA. There is no silent CPU fallback.

## 16. Verification Requirements

Before any result is accepted, verify:

- frozen hashes/identifiers for policy, OPT encoder, outcome extractor, analysis
  configuration, and intervention schedule;
- treatment assignment is independent of post-treatment data;
- complete accounting from randomized assignment to analyzed sample;
- no adjacent trajectory leakage across splits;
- all nulls and negative cells are reported;
- primary and secondary endpoints remain distinct;
- confidence intervals use trajectory/episode dependence blocks;
- label-equivalence merging uses only held-out profiles;
- no graph object exists before its admitting gate;
- no reward tensor or policy optimizer reads IMOD diagnostics;
- environment reward, communication diagnostics, and intervention outcomes are
  logged as distinct channels.

## 17. Independent Review Gate

This is a core MARL design. Because Codex is the active controller, the binding
handover protocol requires an independent review from a different model family,
using pasted Claude or Gemini output archived through the external-review
workflow. Same-family automated GPT review does not satisfy this gate.

The review package must challenge:

1. identifiability under sequential interference;
2. the assigned-code ITT versus executable-skill distinction;
3. context support and positivity;
4. outcome circularity and OPT representation assumptions;
5. multiple comparisons and factorial scaling;
6. whether the contribution is an algorithm or only a measurement framework;
7. novelty relative to SkiLD, COInS, DUSDi, METRA, MAGIC, MACD, MARIE, and
   network-interference methods.

No implementation plan should be accepted until the user reviews this written
spec and the independent-review disposition is archived.

## 18. Acceptance Summary

The user-approved design direction commits to these choices:

1. replace graph-first CSOG with intervention-first IMOD-Direct;
2. ask whether individual skills cause differentiated behavior before asking
   about team conditioning, composition, lifetime, or reward;
3. identify assigned-skill effects under explicit multi-agent interference;
4. use observable skill-blind outcomes as primary evidence;
5. merge interventionally duplicate labels and accept an empty codebook;
6. make graph structure evidence-earned and initially non-executable;
7. defer the world model, directed latent geometry, and asynchronous compiler;
8. keep all IMOD diagnostics reward-off;
9. preserve q_A only as separate source-policy context, not as IMOD evidence;
10. require written-spec review and independent cross-family review before an
    implementation plan.
