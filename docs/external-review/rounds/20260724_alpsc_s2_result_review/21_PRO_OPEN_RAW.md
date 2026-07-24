
# GPT-5.6 Pro CDC Ruling — ALPSC S2 Exclusive-Channel Result

## Executive decision

S2 is accepted as a valid conclusion-bearing negative result.

    accepted_terminal=NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL
    S2_contract_valid=true
    terminal_affecting_defects=none
    S2_algorithm_code_executed=false
    S2_compute_executed=false
    conclusion_bearing_iterations_consumed=2
    iterations_remaining=8

The exact C-ALPSC contract is closed before implementation:

    exclusive z-only slow predictive channel
    + optimized predictive decoder
    + predictive NLL/write-rate scalarization
    + frozen interval 0 < beta < (1/2)ln3

does not make the cue writer globally unique throughout the complete registered
interval.

The decisive counterexample is not a side-channel leak. The admissible
`NEVER_WRITE_AFTER_JOIN` model preserves structural `z=B`, fits the optimal
softened decoder and trades a finite increase in predictive NLL for zero learned
writes. It ties the cue writer at an exact interior `beta_star` and is strictly
better above it.

Exactly one iteration-3 action is selected:

    S3_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_DERIVATION

The new candidate is:

    C-ALCPS
    Agent-Local Controlled Predictive State lifetime

C-ALCPS abandons fixed-beta rate–distortion selection. It defines a lifecycle
state through exact controlled predictive sufficiency under externally indexed
primitive-action interventions, then uses a lexicographic minimum-write and
minimum-decoder-state criterion. It is a new scientific contract, not an
interval narrowing or decoder restriction for C-ALPSC.

S3 is an exact derivation and counterexample action. It requires no algorithm
code, prototype, CPU/GPU execution, experiment, Monitor or resource allocation.

Iterations 4–10 remain unselected.

---

# 1. Evidence boundary

The pushed result-review stage is:

    bcbf74d2598af034b728b586d641dfce67bcbc9d

The exact substantive evidence commit is:

    60cd2d68a54e4c86f5bc0084ff627c779f1c7cb4

The round manifest classifies S2 as an exact derivation and excludes all local,
ignored, runtime and later-working-tree material. No untracked computation or
artifact is admissible. 


The current project record states that S2 is complete, two conclusion-bearing
iterations are consumed, eight remain, no code or compute occurred, and no
iteration-3 action had been selected at the evidence boundary.



The scientific principles retain the final mission of a general MARL algorithm
for variable membership and variable individual lifetime, require anonymous
lifecycle ownership and survivor continuity, prohibit task-specific intrinsic
signals, and favor derivation or counterexample before implementation.




---

# 2. S2 contract-validity audit

## 2.1 Immutable S1 source binding

S2 content-binds the S1 source without changing:

- independent uniform `B∈{0,1}`;
- independent uniform script `S∈{23,32}`;
- seven active rows per lifecycle;
- the regime sequences;
- cue positions;
- exact target law;
- three-lifecycle membership table;
- structural join semantics;
- active-step lifetime;
- temporary-absence freezing;
- utility control;
- registered invariances.

The two scripts remain:

    S=23:
      R = B,B,1-B,1-B,1-B,B,B
      cues = 0,2,5
      complete lifetimes = 2,3

    S=32:
      R = B,B,B,1-B,1-B,B,B
      cues = 0,3,5
      complete lifetimes = 3,2

There are 21 active rows across the three lifecycle epochs. Temporary absence
creates no objective row and advances neither active age nor state. Routing keys
do not enter the scientific filtration.



No source-binding defect exists.

## 2.2 Exclusive online filtration

At an active existing row, the admissible S2 writer receives only:

    current task-blind local observation O_n
    previous slow state z_n-
    fresh writer randomness

The slow decoder receives only:

    installed slow state z_n+

It receives no:

- current observation or direct cue;
- fast recurrent state `h`;
- age or active index;
- local or global clock;
- natural action;
- active-set summary;
- membership history;
- auxiliary persistent state;
- identity or role;
- task, reward, goal, success or progress field;
- future observation;
- oracle boundary.

Structural join sets `z=B` from the current cue through `q_join` and carries no
learned-write cost.

Membership status may determine whether an active transition exists, but it
does not enter the predictive decoder or encode a clock.




No admissible fast-state, action, clock or membership-history channel remains.

## 2.3 Candidate cue writer

The candidate:

1. structurally initializes `z=B`;
2. writes `z←X_n` on each post-join cue;
3. preserves `z` on every other active row;
4. predicts from `z` alone.

For both scripts, it has:

    predictive NLL = H
    H = ln4 -(3/4)ln3
    learned writes per lifecycle = 2
    learned-write rate = 2/7
    J_beta^SC = H +(2/7)beta
    boundary precision = 1
    boundary recall = 1
    complete lifetimes = {2,3}

Because the two regime-conditioned target laws are distinct and log score is
strictly proper, zero predictive excess requires the decoder-visible state to
identify `R` almost surely, up to the single `0↔1` latent relabeling.

A zero-excess model must therefore change decoder-equivalence class on every
actual regime-change cue. A script-independent fixed schedule must contain
`{2,3,5}` and consequently needs at least three writes. The observation-driven
cue writer is the unique zero-excess two-write schedule up to latent relabeling.


This accepted fact remains narrower than global optimality under a scalarized
rate–distortion objective.

## 2.4 NLL and write normalization

The registered S2 objective is:

    J_beta^SC(M)
      = mean_active E[-ln p_eta(Y_n | z_n+)]
        + beta * mean_active E[w_n]

The denominator is all active rows. Each lifecycle has seven active rows and two
learned writes; across all three lifecycles this is six learned writes over 21
active rows, still exactly `2/7`.

Structural join initialization is not a learned Bernoulli write.

The entropy value is exact:

    H
      = -(3/4)ln(3/4) -(1/4)ln(1/4)
      = ln4 -(3/4)ln3

No arithmetic or normalization defect exists.



## 2.5 Complete fixed-age and candidate-map enumeration

Every deterministic fixed-age policy is represented by one six-bit mask over
post-join active ages `1,...,6`. The artifact lists the complete power set:

    count by write cardinality:
      0 writes:  1 mask
      1 write:   6 masks
      2 writes: 15 masks
      3 writes: 20 masks
      4 writes: 15 masks
      5 writes:  6 masks
      6 writes:  1 mask

Total:

    1+6+15+20+15+6+1 = 64

At a scheduled age, the candidate map has six possible inputs:

    observation category ∈ {neutral,cue-0,cue-1}
    prior z ∈ {0,1}

and one binary output, giving `2^6=64` deterministic candidate maps per
scheduled age. Allowing a distinct map at every scheduled age yields the exact
finite family `64^|A|`. This over-approximates a shared candidate encoder and
therefore cannot unfairly weaken a null.

For every mask and candidate-map tuple, the artifact defines exact propagation
over all 28 equally weighted `(B,S,n)` cases and the maximum-likelihood decoder:

    q_z = K_z / (4N_z)

with objective:

    L(A,g) = (1/28) sum_z N_z h(q_z)

and:

    J_A(beta) = min_g L(A,g) + (|A|/7)beta

This is an exhaustive mathematical parametrization. Listing all
`64^|A|` bit strings individually is unnecessary: every element has a unique
finite index and a closed-form objective. It is not a sampled or hand-selected
enumeration.


No incomplete fixed-age obligation is found.

## 2.6 Periodic schedules

Every finite-horizon deterministic period/phase schedule maps to one of the 64
fixed-age masks:

    period 1: {1,2,3,4,5,6}
    period 2: {1,3,5} or {2,4,6}
    period 3: {1,4}, {2,5}, or {3,6}
    period 4: {1,5}, {2,6}, {3}, or {4}
    period 5: {1,6}, {2}, {3}, {4}, or {5}
    period 6: each singleton
    period >6: empty post-join set

Duplicate schedules collapse to the same deterministic mask and require no
second evaluation.


Coverage is complete.

## 2.7 Membership-event-only schedules

Structural join remains outside the learned-write factor and temporary absence
has no active objective row.

For current active rows, the artifact enumerates all eight deterministic
mappings over:

    ordinary
    rejoin
    terminal-leave

as:

    000 001 010 011 100 101 110 111

The exact three-lifecycle table determines the resulting write rows. Candidate
maps and decoder fits use the same exact finite count construction. Routing-key
use, inactive-row counting or membership-history use is explicitly rejected as
an active-set/time leak.


No missing registered mapping is identified.

## 2.8 Post-hoc segmentation

Post-hoc oracle boundaries may be scored after collection but cannot install
online state or alter an earlier prediction.

Consequently, its admissible online state and optimal decoder are exactly the
never-write case. Giving future boundaries to the online decoder would instead
be invalid.

This agrees with the frozen S2 contract.



## 2.9 Stochastic mixtures

Any finite stochastic policy can be represented by a random tape selecting a
deterministic policy. If the random-tape identity is not given to the decoder,
the resulting joint law of `(Y,z)` is a convex combination of deterministic
joint laws.

Conditional entropy is concave in that joint law and expected write count is
linear. Therefore:

    J_beta(mixture)
      >= sum_d alpha_d J_beta(d)
      >= min_d J_beta(d)

A stochastic mixture cannot beat its best deterministic component.

If the mixture identity is revealed to the decoder, it becomes an undeclared
persistent side channel and is rejected at the earlier leak branch. Even with
that identity, its weighted objective cannot be lower than its best component.


The extreme-point argument is correct and covers history-dependent stochastic
policies through their complete random tapes.

## 2.10 Mandatory leak controls

All six mandatory forbidden channels are reproduced separately:

1. `FAST_H_LEAK`

   A cue-updated recurrent bit reaches NLL `H` with zero `z` writes.

2. `AUXILIARY_RNN_LEAK`

   One hidden persistent bit recreates recurrent absorption.

3. `AGE_CLOCK_LEAK`

   Active age plus the cue pattern reconstructs the complete regime sequence
   with zero slow writes.

4. `ACTION_LEAK`

   A natural action selected from fast memory transfers the regime bit to the
   decoder.

5. `DIRECT_CUE_DECODER_LEAK`

   Direct cue access lets fixed writes at ages 3 and 6 reach NLL `H` and write
   rate `2/7` without matching the true boundary schedule.

6. `ACTIVE_SET_TIME_LEAK`

   A deterministic roster or membership sequence that reveals global/local time
   reproduces the age-clock shortcut.

These are explicitly outside admissible C-ALPSC. None is used by the decisive
never-write null.


The leak obligation is complete.

## 2.11 Constructive controls and invariances

Constructive policies remain:

    ALPSC:
      install z=R on cue rows
      choose primitive A=z

    G8:
      store R in lifecycle h
      choose primitive A=h

Both achieve:

    U*=1

No training or comparison is claimed.

The S1 invariances remain exact:

- lifecycle-key relabeling;
- active-member permutation;
- inactive padding;
- temporary-absence insertion;
- latent `0↔1` relabeling.

Every registered mismatch is zero.


The repository G8 base is a direct recurrent open-roster policy with no
skill/event hierarchy, lifecycle-owned hidden state and padding capacity
excluded from model input. Temporary absence freezes hidden state and genuine
join initializes a fresh zero state.




Its focused tests retain constructive utility, inactive-capacity invariance,
lifecycle ownership, replay and fail-closed evidence behavior.




## 2.12 Iteration accounting

S2 executed no code, algorithm, prototype, environment, optimizer or formal
analysis. Its exact valid terminal consumes iteration 2.

The repository consistently records:

    consumed=2
    remaining=8
    code=false
    compute=false
    formal_run=false
    iteration_3=unselected





## S2 audit conclusion

    immutable_source_valid=true
    exclusive_filtration_valid=true
    structural_join_valid=true
    NLL_arithmetic_valid=true
    write_normalization_valid=true
    fixed_age_masks_complete=true
    candidate_maps_complete=true
    periodic_coverage_complete=true
    membership_mapping_complete=true
    posthoc_semantics_valid=true
    stochastic_extreme_point_argument_valid=true
    mandatory_leaks_complete=true
    constructive_controls_valid=true
    invariances_valid=true
    iteration_accounting_valid=true
    terminal_affecting_defects=none

---

# 3. Independent never-write recomputation

## 3.1 Regime agreement with structural z

Never-write preserves:

    z=B

For script `23`:

    R=B on 4 rows
    R≠B on 3 rows

For script `32`:

    R=B on 5 rows
    R≠B on 2 rows

Averaging the two scripts:

    P(R=z)   = (4+5)/(2*7) = 9/14
    P(R≠z)   = (3+2)/(2*7) = 5/14

## 3.2 Fitted decoder probability

The target channel is:

    P(Y=R)=3/4
    P(Y≠R)=1/4

Therefore:

    P(Y=z | z)
      = P(R=z)(3/4) + P(R≠z)(1/4)
      = (9/14)(3/4) +(5/14)(1/4)
      = 27/56 +5/56
      = 32/56
      = 4/7

Equivalently:

    P(Y=1 | z=1)=4/7
    P(Y=1 | z=0)=3/7

## 3.3 Exact never-write NLL

The fitted binary entropy is:

    L_NW
      = h(4/7)
      = -(4/7)ln(4/7) -(3/7)ln(3/7)
      = ln7 -(4/7)ln4 -(3/7)ln3

It makes no learned writes:

    J_beta^SC(NW)=L_NW

The cue writer has:

    H = ln4 -(3/4)ln3
    J_beta^SC(CUE)=H +(2/7)beta

Because `4/7` lies strictly between `1/2` and `3/4`, strict binary-entropy
concavity gives:

    L_NW > H

## 3.4 Exact crossover

Let:

    G = L_NW - H

Then:

    G
      = ln7 -(4/7)ln4 -(3/7)ln3
        -ln4 +(3/4)ln3
      = ln7 -(11/7)ln4 +(9/28)ln3

The equality:

    L_NW = H +(2/7)beta

gives:

    beta_star
      = (7/2)G
      = (7/2)ln7 -(11/2)ln4 +(9/8)ln3

This matches the artifact exactly.


## 3.5 Exact proof that beta_star is inside the interval

Positivity follows from:

    G=L_NW-H>0

For the upper bound:

    beta_star < (1/2)ln3

Multiply by eight and rearrange:

    28ln7 +5ln3 <44ln4

Exponentiation gives the equivalent integer inequality:

    7^28 * 3^5 <4^44=2^88

Now:

    7^7=823543 <2^20=1048576

so:

    7^28 <2^80

and:

    3^5=243 <2^8=256

Therefore:

    7^28 *3^5 <2^80 *2^8 =2^88

strictly.

Hence:

    0 < beta_star < (1/2)ln3



## 3.6 Consequence across the frozen interval

    0 < beta < beta_star:
      never-write is worse than the cue writer

    beta = beta_star:
      never-write ties the cue writer
      uniqueness fails
      strict Delta_SC>0 fails

    beta_star < beta < (1/2)ln3:
      never-write is strictly better

The complete-interval PASS obligation is therefore false.


---

# 4. First-match terminal

The frozen terminal order is:

    1. INVALID_ALPSC_DERIVATION_CONTRACT
    2. SIDE_CHANNEL_OWNERSHIP_LEAK
    3. NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL
    4. PASS_ALPSC_IDENTIFIABILITY_DERIVATION

## 4.1 `INVALID_ALPSC_DERIVATION_CONTRACT`

Not selected.

The source, information order, structural initialization, arithmetic, finite
policy parametrization, null coverage, stochastic argument, membership
semantics and invariances are valid.

## 4.2 `SIDE_CHANNEL_OWNERSHIP_LEAK`

Not selected.

The decisive never-write model receives only structural `z=B`. Its decoder is a
memoryless fitted function of current `z`. It receives no fast state, cue, age,
time, action, active-set history, event history or auxiliary recurrence.

The six leak constructions are separately marked forbidden and are not used to
obtain the negative result.

## 4.3 `NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL`

Selected.

The registered branch applies whenever, under a valid exclusive contract:

- the cue writer is not unique anywhere in the frozen interval; or
- an admissible null has `Delta_SC(beta)<=0` anywhere in that interval.

At the exact interior `beta_star`, the never-write null ties the cue writer.
Above it, the null wins.

## 4.4 `PASS_ALPSC_IDENTIFIABILITY_DERIVATION`

Not reached.

The correct first-match terminal is therefore:

    NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL




No beta narrowing, forced decoder, restricted null or source change may relabel
this valid terminal.

---

# 5. Smallest supported and refuted propositions

## 5.1 Smallest supported proposition

    P_S2_CROSSOVER:

    On the exact S1/S2 source, under the exclusive z-only decoder and the
    optimized decoder family, the admissible never-write state z=B has NLL
    h(4/7) and crosses the two-write cue writer at an interior point of
    0 < beta < (1/2)ln3.

This is an exact source-and-objective proposition.

## 5.2 Smallest structural proposition

    P_EXCLUSION_NECESSARY_NOT_SUFFICIENT:

    Excluding alternative temporal channels is necessary to prevent S1
    recurrence absorption, but it is not sufficient to make a fine sparse state
    globally optimal under predictive-loss/write-rate scalarization.

The remaining ambiguity is rate–distortion, not state ownership through a hidden
side channel.

## 5.3 Smallest refuted proposition

    P_ALPSC_COMPLETE_INTERVAL:

    The cue writer is the unique global minimizer, up to latent relabeling, for
    every beta in 0 < beta < (1/2)ln3.

This exact proposition is refuted.

## 5.4 Proposition retained from S2

    P_ZERO_EXCESS_MINIMALITY:

    On the exact source, the cue writer is the unique zero-predictive-excess
    two-write schedule up to latent 0↔1 relabeling.

S2 does not refute this proposition. It shows that a scalar objective may prefer
a coarser state with positive predictive excess.

## 5.5 Propositions not refuted

S2 does not refute:

- exclusive predictive-state channels in general;
- sparse online segmentation under a constrained-sufficiency or other new
  objective;
- a controlled predictive state;
- continuous lifecycle-owned latent state;
- variable individual lifetime;
- causal primitive-action mediation;
- natural policy use;
- optimization or sample-efficiency benefit;
- held-out transport beyond G8;
- set-equivariant population memory;
- explicit task-directed termination on a new identified source.

It does not show that G8 and an explicit state have equal optimization or
generalization. It establishes only an exact objective-level negative.

The current conjecture and portfolio ledgers already preserve this narrow
scope. 


## 5.6 R42–R48 scopes remain unchanged

Nothing in S2 reopens or broadens the earlier routes:

- R42: categorical incumbent-roster logit residual remains closed.
- R43: treatment inference remains quarantined by the failed fixed anchor.
- R44: frozen-source global-`K=50` reward-credit renewal remains closed.
- R45: Alice–Bob natural-support Q/DR renewal remains closed.
- R46: exact HMRV estimator/read remains closed, not oracle heterogeneity.
- R47: exact natural spectral process-mode route remains closed.
- R48: focal hidden reset at categorical SET remains closed.

C-ALCPS is distinct from them: it uses no categorical skill label, renewal
hazard, external-return Q target, spectral rank or hidden-state reset.

---

# 6. Fresh plural CDC pass

## 6.1 Candidate A — C-ALCPS: Agent-Local Controlled Predictive State

### Conjecture

A lifecycle-owned state may have a canonical, threshold-free lifetime when it is
defined as the minimal online state sufficient for the complete vector of
task-blind primitive-action-interventional outcome laws.

The state is not selected by a beta-weighted write objective. Instead:

1. exact controlled predictive sufficiency is primary;
2. minimum learned state-transition count is secondary;
3. the coarsest decoder-distinct state partition is tertiary.

### Mechanism-to-capability edge

A task-blind controlled predictive state distinguishes histories that have
different generic consequences under primitive interventions, even when their
uncontrolled or action-marginal observation distributions are identical.

This supplies:

- an action-relevant but reward-free temporal state;
- an objective active-step lifetime;
- a state that ignores predictive nuisance variables;
- an intervention-ready object for a later behavioral audit.

### Strongest simpler explanation

G8 recurrence can store the same controlled predictive statistic and may learn
the same external policy. C-ALCPS therefore cannot claim representational
necessity.

A later algorithmic claim would have to concern optimization, mediation,
sample efficiency, robustness or held-out transport.

### Strongest counterexamples

- If all action-conditioned kernels are equal across regimes, there is no
  controlled state to identify.
- If only the natural action marginal is observed, action effects may cancel and
  the state becomes invisible.
- If query actions are selected by fast `h`, the action label itself can leak
  memory.
- If a nuisance variable changes without changing any controlled kernel, a
  representation that tracks it is not minimal.
- If several online state-transition schedules achieve the same controlled
  sufficiency, lifetime is non-unique.
- If the cue arrives after the controlled target, no online sufficient state
  exists for the current target.

### Correction

Use externally indexed action queries with exact support for every primitive
action at every finite source state. Query actions are intervention indices, not
natural actions and not outputs of `h`.

Define the state through predictive sufficiency and coarsest quotient, not a
beta interval.

### Disposition

Retain and select for S3 exact derivation.

## 6.2 C-JRDM — jointly rate-coded dual memory

Status remains parked.

A joint information or codelength objective could account for both `h` and `z`,
but channel ownership remains arbitrary under invertible mixing unless the code
is representation-invariant and its decomposition is scientifically justified.

S2 does not resolve that problem.

Reactivation condition:

    a representation-invariant joint code with a channel-decomposition theorem

## 6.3 C-ALH — explicit categorical agent-local hazard

Status remains parked.

A per-step KEEP/RENEW hazard still risks being the prior mechanism with `k=1`.
Its learning signal and causal source remain unresolved, and R43–R45 cannot be
revived by changing the opportunity frequency.

Reactivation condition:

    an independently identified source requiring a task-directed termination
    factor after a non-reward predictive state has been established

## 6.4 C-ATS — continuously adaptive timescale recurrence

Status remains parked.

It still lacks a threshold-free lifetime. It can be absorbed into recurrence,
and a post-hoc threshold on a leak coefficient would not create an identified
segment.

Reactivation condition:

    a threshold-invariant survival or causal-persistence estimand

## 6.5 C-SEPM — set-equivariant persistent population memory

Status remains parked.

It may address complementary allocation, but it simultaneously changes team
coordination and individual lifetime. TEAM_REC and ordinary set encoders remain
simpler explanations.

Reactivation condition:

    an identified complementary-allocation source on which lifecycle recurrence
    and TEAM_REC are insufficient

## 6.6 Broader predictive-state family

Status:

    live, corrected again

S1 rejects free alternative decoder-visible memory.

S2 rejects complete-interval scalarized rate–distortion selection even after
side-channel exclusion.

Neither result rejects a controlled minimal-sufficient predictive state.

## 6.7 G8 and ordinary recurrence

G8 remains:

- the accepted usable dynamic-roster base;
- the complete external-policy comparator;
- the strongest simpler explanation;
- a constructive source-control policy.

It is not a universal admission gate.

Any later C-ALCPS claim must be phrased as an optimization, causal-use,
complexity or transport claim—not finite representational impossibility.

---

# 7. Selected iteration-3 action

    action_id=S3_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_DERIVATION
    candidate=C_ALCPS
    action_class=exact_derivation_and_counterexample
    conclusion_bearing_iteration=3
    code_required=false
    compute_required=false
    prototype_required=false
    experiment_required=false
    Monitor_required=false

## 7.1 Exact question

Does a task-blind, action-interventional minimal-sufficiency criterion identify
one nontrivial agent-local state lifetime on a finite anonymous
runtime-membership source while correctly rejecting:

- action-marginal non-identification;
- temporal side-channel leakage;
- nuisance-state tracking;
- non-unique state-transition schedules?

The action must answer this before any learned implementation is considered.

## 7.2 Exact finite source

Reuse the S1 active-clock and membership structure:

- independent `B∈{0,1}`;
- independent scripts `23` and `32`;
- regime sequences and cue rows unchanged;
- complete lifetimes `{2,3}`;
- 21 active rows across three lifecycle epochs;
- temporary leave/rejoin;
- fresh genuine join;
- terminal leave;
- structural join initialization;
- all original invariances.

Add one task-blind iid nuisance observation:

    N_n ∈ {0,1}
    P(N_n=0)=P(N_n=1)=1/2

independent of:

    B
    S
    R
    membership
    intervention query
    target

The local writer observation is:

    O_n=(C_n,X_n,N_n)

The nuisance bit is included to test whether the coarsest predictive quotient
rejects irrelevant observed variation.

## 7.3 Controlled primitive-action query

Introduce an externally indexed query:

    u ∈ {0,1}

Both values are evaluated at every active source state. Query `u` is:

- not sampled by the natural policy;
- not a function of `h`, `z`, history or identity;
- not persistent across rows;
- not an input to the writer;
- supplied only as the current controlled decoder query.

The exact generic target law is:

    P(Y=1 | R,u) =
      3/4  if u=R
      1/4  if u≠R

Equivalently, for each fixed query action, the two regime kernels differ in
total variation by exactly `1/2`.

If `u` is marginalized uniformly and omitted from the decoder:

    P(Y=1 | R)=1/2

for both regimes.

Thus:

- action-marginal prediction contains no regime information;
- the complete controlled kernel does contain regime information;
- actual policy action cannot act as a memory side channel.

## 7.4 Scientific state object

Each lifecycle owns:

    h_i,n
      unrestricted fast recurrent primitive-control state
      excluded from the controlled predictive channel

    z_i,n
      finite controlled predictive state

    w_i,n
      learned state-installation indicator

    segment_i
      maximal active-step run in one decoder-equivalence class

Structural join initializes `z` from the current cue and has no learned
transition.

Temporary absence freezes ownership and segment age.

Terminal leave right-censors and deletes the state after evidence is recorded.

A C-ALCPS lifetime is the number of active primitive steps between changes of
decoder-equivalence class, not physical wall time and not a global cycle.

## 7.5 Writer filtration

At an active existing row, the writer may use only:

    current O_n=(C_n,X_n,N_n)
    previous z_n-
    fresh registered writer randomness

It may not use:

- `h`;
- age or active index;
- local/global clock;
- `t mod k`;
- observation history outside `z`;
- natural current or past actions;
- query history;
- active-set or membership history;
- persistent auxiliary memory;
- identity or role;
- external reward;
- task, goal, success or progress fields;
- future observations;
- oracle regime or boundary.

## 7.6 Controlled decoder

The decoder is:

    p_eta(Y_n | z_n+, u)

It receives exactly:

    installed z
    current externally indexed query u

It receives no natural action, current observation, cue, fast state, clock,
history or nuisance input.

Both query actions are evaluated for each legal history. A data stream that
contains only the action chosen by a policy is not sufficient evidence for S3.

## 7.7 Supervision and credit

Writer supervision is solely the exact task-blind controlled target law.

No external utility enters:

- writer input;
- writer loss;
- state target;
- decoder;
- boundary decision.

There is no:

- lifetime reward;
- switch penalty;
- renewal bonus;
- high-level advantage;
- external-return Q value;
- discriminator reward;
- primitive PPO gradient into the writer.

For a future implementation, controlled prediction and external policy learning
would remain separate authorities. S3 itself performs no learning.

## 7.8 Probability semantics

For each active legal history and both query actions, define:

    K_f^u(y)=P(Y=y | legal history f, do(u))

The candidate controlled state is sufficient when:

    P(Y | f,do(u)) = P(Y | z(f),do(u))

for every legal history, both query actions and both target values.

The decoder-distinct quotient identifies states only through differences in the
complete vector:

    (K^0,K^1)

Latent subdivisions having identical controlled kernels are merged.

## 7.9 Lexicographic scientific criterion

S3 does not use beta.

Define controlled predictive risk:

    L_ctrl(M)
      = mean over active histories and u∈{0,1}
          E[-ln p_M(Y | z,u)]

The exact Bayes floor is:

    L_star
      = H
      = ln4 -(3/4)ln3

because, conditional on the correct regime and query, the target probability is
always either `3/4` or `1/4`, with the same binary entropy.

Define predictive excess:

    E_ctrl(M)=L_ctrl(M)-L_star

Define learned-write rate:

    q(M)=mean_active E[w_n]

Define decoder-state cardinality:

    K(M)=number of distinct controlled decoder kernels
         after merging decoder-equivalent latent values

Models are ordered lexicographically by:

    (E_ctrl, q, K)

Thus:

1. exact controlled predictive sufficiency is non-negotiable;
2. among sufficient models, fewer learned writes are preferred;
3. among equal-write sufficient models, the coarsest controlled-kernel quotient
   is preferred.

This is a new estimand. It is not a post-result beta selection.

## 7.10 Candidate C-ALCPS writer

The candidate:

- structurally sets `z=B`;
- writes `z←X_n` on each post-join cue;
- preserves `z` otherwise;
- ignores nuisance `N`;
- decodes the complete controlled kernel from `(z,u)`.

Required exact values:

    E_ctrl=0
    q=2/7
    K=2
    boundary_precision=1
    boundary_recall=1
    complete_lifetimes={2,3}

The two decoder states are unique only up to `0↔1`.

## 7.11 Mandatory comparators and nulls

### Structural nulls

Evaluate:

- `NEVER_WRITE_AFTER_JOIN`;
- `ALWAYS_WRITE`;
- all 64 deterministic fixed-age masks;
- every finite-horizon periodic phase;
- all current-membership-event mappings;
- post-hoc segmentation;
- all stochastic mixtures;
- nuisance-only state tracking.

### Action-information null

`ACTION_MARGINAL_NULL` receives the uniform action-marginal target but not the
query action.

Required result:

    P(Y=1 | R)=1/2
    no nontrivial controlled state is identifiable

This proves that action conditioning is load-bearing.

### Query-leak null

`NATURAL_ACTION_QUERY` supplies only an action selected by a policy with access
to fast `h`.

Required classification:

    invalid action-as-memory channel

It is not admissible controlled evidence.

### Complete external-policy comparator

Exact G8 recurrence remains the complete constructive comparator.

## 7.12 Constructive external control

For audit only:

    external utility = 1 if primitive A=R, else 0

This utility is absent from state supervision.

Constructive C-ALCPS:

    choose A=z

Constructive G8:

    store R in h
    choose A=h

Required:

    U_star_ALCPS=1
    U_star_G8=1

This prevents a false claim of recurrent representational impossibility.

## 7.13 Exact proof obligations

A PASS requires every obligation.

1. Source variables, membership table and intervention target laws are exact.

2. Both action queries are available at every active legal history.

3. Query actions are independent intervention indices and carry no memory.

4. Controlled kernel separation is exact:

       TV(K_R=0^u, K_R=1^u)=1/2
       for each u∈{0,1}

5. Action-marginal separation is exactly zero:

       TV(P(Y|R=0),P(Y|R=1))=0
       after uniform query marginalization

6. Candidate C-ALCPS reaches:

       E_ctrl=0
       q=2/7
       K=2

7. Every model with `E_ctrl=0` must distinguish the two regime kernels almost
   surely.

8. Every `E_ctrl=0` model must change decoder-equivalence class on both actual
   post-join regime changes.

9. Therefore every sufficient model has:

       q >= 2/7

10. Equality `q=2/7` is possible only when learned writes occur exactly on the
    two post-join cue rows, up to null events and latent relabeling.

11. After decoder-equivalent states are merged, every equality model has:

       K=2

12. The iid nuisance bit does not change any controlled kernel and is absent
    from the coarsest quotient.

13. Every fixed-age, periodic, membership-only, post-hoc and stochastic null is
    either predictively insufficient or has lexicographically worse
    `(q,K)`.

14. The never-write fitted decoder may reproduce the S2 softened value, but it
    has strictly positive `E_ctrl` and cannot outrank a sufficient state.

15. Boundary precision and recall are exactly one.

16. Complete active-step lifetimes are exactly `{2,3}`.

17. Constructive C-ALCPS and G8 controls both have utility one.

18. Registered mismatches are zero under:

       lifecycle-key relabeling
       active-member permutation
       inactive padding
       temporary-absence insertion
       controlled-action label swap with corresponding kernel relabeling
       latent 0↔1 relabeling

19. No reward, identity, role, goal, success, progress, future input, natural
    action memory, clock or auxiliary persistence enters the state channel.

20. A negative control in which the two controlled regime kernels are made
    identical must correctly produce no nontrivial controlled state rather than
    a false lifetime PASS.

There is no statistical, mixed or underpowered branch.

## 7.14 First-match terminals

Apply in this exact order.

1. `INVALID_ALCPS_DERIVATION_CONTRACT`

   Any source arithmetic error, inconsistent intervention law, incomplete null,
   incorrect online order, invalid membership semantics, failed invariance or
   forbidden task/reward field.

2. `ACTION_QUERY_OR_TEMPORAL_SIDE_CHANNEL_LEAK`

   Query action is generated by `h` or history, query support is selective, or
   any admissible writer/decoder receives fast state, clock, natural action,
   active-set history or auxiliary persistence.

3. `CONTROLLED_SOURCE_NON_IDENTIFIABLE`

   Full intervention support is valid, but the controlled regime kernels are not
   distinct, the action-marginal/control separation is absent, or the candidate
   cannot attain the exact controlled Bayes floor.

4. `NO_UNIQUE_MINIMAL_CONTROLLED_LIFETIME`

   Controlled predictive sufficiency is attainable, but multiple different
   minimum-write schedules survive, the nuisance remains decoder-distinct, or a
   registered null has a lexicographically equal or better
   `(E_ctrl,q,K)` tuple.

5. `PASS_ALCPS_CONTROLLED_STATE_DERIVATION`

   Every exact proof obligation passes.

## 7.15 Required evidence artifact

The sole conclusion-bearing S3 artifact is:

    docs/research/cdc/EVIDENCE_NOTES/
    20260724_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_S3.md

It must contain:

- the exact finite source;
- the controlled potential-outcome table;
- action-query support and independence proof;
- exact target and entropy arithmetic;
- writer and decoder filtration;
- the lexicographic estimand;
- complete deterministic and stochastic null coverage;
- nuisance quotient proof;
- action-marginal and action-query-leak counterexamples;
- constructive C-ALCPS and G8 policies;
- membership and label invariances;
- smallest supported and refuted propositions;
- first-match terminal;
- no engineering plan, code or resource schedule.

## 7.16 Stop and iteration rule

Stop on the first valid S3 terminal.

A valid PASS or negative consumes iteration 3:

    consumed=3
    remaining=7

An invalid derivation consumes no iteration and permits at most one bounded
correction of transcription, arithmetic or proof checking under the identical:

- source;
- intervention table;
- filtration;
- null family;
- estimand;
- proof obligations;
- terminal order.

Changing any of those objects requires another Pro decision.

A second invalid realization is a blocker.

After a valid S3 terminal, return the exact result to this same registered Pro
conversation before selecting iteration 4.

---

# 8. Why no other action is scheduled first

## 8.1 Not another beta or decoder correction

S2 validly closes the exact scalarized interval.

Narrowing beta, forcing `p_z`, weakening never-write or changing the source
would be a direct post-result rescue.

## 8.2 Not immediate implementation

S1 and S2 were objective-level failures. Implementing another predictive writer
before fixing the scientific state definition would confound:

- mathematical non-identifiability;
- side-channel leakage;
- source non-identification;
- optimization failure;
- implementation error.

## 8.3 Not C-JRDM first

Joint coding introduces unresolved representation and channel-decomposition
invariance. C-ALCPS tests a canonical controlled sufficiency object before
adding a joint memory code.

## 8.4 Not C-ALH first

The categorical hazard line still lacks a structurally new supervision and
risks a `k=1` rename of R43–R45.

## 8.5 Not C-ATS first

No threshold-free lifetime exists yet.

## 8.6 Not C-SEPM first

It combines coordination and lifetime, producing weaker attribution at higher
cost.

C-ALCPS has the highest information gain, lowest cost and full reversibility:
one exact derivation can reject it without code.

---

# 9. Durable repository deltas after factual reconciliation

## 9.1 Conjecture ledger

Update `C-ALPSC`:

    status=closed_exact_S2_contract
    terminal=NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL
    no_local_beta_decoder_null_or_source_rescue=true

Retain:

    unique_zero_excess_two_write_schedule=true
    broader_exclusive_predictive_state_unresolved=true

Add:

### `C-ALCPS — Agent-Local Controlled Predictive State lifetime`

Status:

    selected for S3 exact derivation
    no code or compute selected

Claim:

    a task-blind lifecycle state may have a canonical active-step lifetime when
    it is the coarsest minimum-transition state sufficient for the full vector
    of primitive-action-interventional observation laws

Strongest simpler explanation:

    G8 recurrence stores the same controlled statistic and the explicit state
    provides no optimization, causal-use or transport benefit

Intervention consequence:

    decoder-controlled kernels differ under a same-history primitive query when
    z differs

Natural consequence:

    not yet established; S3 identifies only the internal controlled state

Held-out consequence:

    not yet established; future evidence must retain G8 and a mechanism-matched
    masked-z comparator

Update broader predictive-state status:

    scalarized rate-distortion closed at S2 scope
    controlled minimal sufficiency remains live

Retain C-JRDM, C-ALH, C-ATS and C-SEPM as parked with their existing
reactivation conditions.

Update C-REC:

    mandatory constructive comparator and simpler explanation
    not a universal admission gate

## 9.2 Lemma ledger

Add:

### `L-S2-VALID-NEGATIVE`

The exact S2 derivation validly rejects complete-interval global identification
for the C-ALPSC scalar objective.

Does not imply:

    all exclusive or controlled predictive-state definitions fail

### `L-RATE-DISTORTION-COARSENING`

A decoder optimized for a coarser persistent state can exchange finite
predictive excess for fewer state changes and defeat a finer boundary under
scalarization.

Scope:

    predictive-loss/write-rate objectives such as exact S2

### `L-EXCLUSION-NECESSARY-NOT-SUFFICIENT`

Retain and strengthen the existing lemma:

    removing alternative temporal channels prevents ownership leakage but does
    not resolve the predictive-accuracy/write-rate tradeoff

### `L-CONTROLLED-QUERY-SEPARATION` — pending S3

Record only in the S3 action note until proven:

    externally enumerated intervention queries may condition a predictive
    decoder without serving as temporal memory; natural policy actions cannot be
    assumed to have this property

Do not promote the pending statement to a retained lemma before a valid S3
terminal.

## 9.3 Counterexample ledger

Retain and strengthen:

### `CE-SOFTENED-NEVER-WRITE-DECODER`

Add the exact values:

    P(Y=z|z)=4/7
    L_NW=ln7-(4/7)ln4-(3/7)ln3
    beta_star=(7/2)ln7-(11/2)ln4+(9/8)ln3
    0<beta_star<(1/2)ln3

Add as S3 registered counterexample candidates, not accepted results:

### `CE-ACTION-MARGINAL-HIDES-CONTROLLED-STATE`

Uniformly marginalizing the action query makes the two regime target laws
identical even though their complete controlled kernels differ.

### `CE-NATURAL-ACTION-AS-QUERY-LEAK`

An action selected from fast recurrence can reveal the hidden regime to a
decoder and cannot substitute for externally indexed controlled support.

### `CE-PREDICTIVE-NUISANCE-SUBDIVISION`

A latent may encode an observed nuisance that changes no controlled kernel.
Decoder-equivalent nuisance subdivisions do not define additional skills or
lifetimes.

Promote these three to accepted counterexamples only after the S3 artifact
proves them.

## 9.4 Idea portfolio

Set:

    C-ALPSW:
      closed exact S1 formulation

    C-ALPSC:
      closed exact S2 formulation and interval

    C-ALCPS:
      live and selected for S3 derivation

    C-JRDM:
      parked

    C-ALH:
      parked

    C-ATS:
      parked

    C-SEPM:
      parked

    C-OPEN-ROSTER-DIRECT:
      accepted base and mandatory complete comparator

    C-REC:
      mandatory simpler explanation and constructive comparator

Scheduled action:

    S3_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_DERIVATION

Authorization:

    derivation selected
    code not selected
    compute not selected
    iterations 4_to_10 unselected

## 9.5 Evidence-note delta

Add:

    docs/research/cdc/EVIDENCE_NOTES/
    20260724_ALPSC_S2_RESULT_AND_ALCPS_S3_DIRECTION.md

Record:

- S2 validity audit;
- exact never-write recomputation;
- accepted first-match terminal;
- smallest supported and refuted propositions;
- unchanged R42–R48 scopes;
- plural portfolio;
- C-ALCPS contract;
- S3 exact source and proof obligations;
- iteration accounting;
- evidence commit
  `60cd2d68a54e4c86f5bc0084ff627c779f1c7cb4`;
- this response provenance.

No experiment row belongs in `ExpRecord.md` because S3 is a derivation.

## 9.6 Current-work delta

After factual reconciliation, set:

    last_completed_assignment_id=S2_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_DERIVATION
    active_assignment_id=S3_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_DERIVATION
    next_boundary=COMPLETE_EXACT_S3_DERIVATION_THEN_RETURN_TO_PRO
    conclusion_bearing_iterations_consumed=2
    skill_lifetime_chain_iterations_remaining=8
    k_decoupling_current_result=NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL
    active_scientific_direction=C_ALCPS
    active_scientific_contract=20260724_ALPSC_S2_RESULT_AND_ALCPS_S3_DIRECTION
    active_algorithm=PREFIX_NORMALIZED_OPEN_ROSTER_G8_imported_base
    s3_code_required=false
    s3_compute_required=false
    formal_compute_status=not_started

Only a valid S3 terminal changes the count to three consumed and seven
remaining.

---

# 10. What this ruling does not authorize

This response does not authorize:

- algorithm code;
- implementation planning;
- a toy implementation;
- prototype execution;
- CPU or GPU computation;
- formal training, evaluation or analysis;
- Monitor assignment;
- an experiment row;
- modification of G8;
- beta narrowing;
- forcing the S2 decoder;
- restricting the S2 never-write null;
- rerunning or rescuing C-ALPSW or C-ALPSC;
- a joint-memory information penalty;
- a categorical hazard;
- a continuous-timescale threshold;
- a population-memory module;
- natural action being used as an intervention query;
- reward in predictive supervision;
- identity, role, goal, success or progress fields;
- task-specific intrinsic reward;
- revival of R42–R48;
- mutation of `aggressive`;
- selection of iterations 4–10;
- a learned-skill, utility, optimization, transport or superiority claim;
- integration into the final HMASD algorithm.

A future S3 PASS would support only exact controlled-state and active-lifetime
identifiability on the frozen finite source. It would still require another CDC
decision before implementation.

External scientific review itself never authorizes code or compute.



---

# 11. 中文用户简报

S2 结论有效：`NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL`。

排除 fast `h`、age、时钟、action、active-set history 和辅助 RNN 后，合法
never-write null 仍保留 structural `z=B`，并把 decoder 优化为
`P(Y=z|z)=4/7`。其精确 NLL 为：

    ln7 -(4/7)ln4 -(3/7)ln3

它在

    beta_star=(7/2)ln7-(11/2)ln4+(9/8)ln3

与两次写入的 cue writer 相交。该交点严格位于冻结区间
`0<beta<(1/2)ln3` 内；交点处唯一性和严格 `Delta_SC>0` 失败，交点以上
never-write 更优。因此本轮失败不是 side-channel leak，而是合法的
rate–distortion tradeoff。C-ALPSC 的精确目标和完整区间关闭，不能缩窄 beta、
强制 decoder、限制 null 或更换 source 来救援。第 2 次结论性迭代已消耗，剩余
8 次。

下一项唯一行动是无代码、无计算的
`S3_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_DERIVATION`。新候选 C-ALCPS 不再用
beta 选择状态，而是先要求对所有外部枚举 primitive action 的 task-blind
controlled kernel 精确充分，再最小化写入次数和 decoder-distinct state 数量。
S3 使用含 action-interventional response、无关 nuisance 和原有
leave/rejoin/join 生命周期的精确有限 source；必须证明 cue writer 是唯一最小
controlled-sufficient lifetime，同时 action-marginal 数据确实无法识别该状态。

决定性否证条件是：controlled kernels 本身不可区分、query action 携带 fast-memory
泄漏、存在另一套相同最小写入的 sufficient schedule，或 nuisance 仍成为必要
decoder state。出现任一有效负分支即关闭精确 C-ALCPS 合同，不进入实现。迭代 4–10
仍未选择。
