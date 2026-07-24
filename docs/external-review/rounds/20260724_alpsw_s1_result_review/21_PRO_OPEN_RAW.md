
# GPT-5.6 Pro CDC Ruling — ALPSW S1 Identifiability Result

## Executive decision

S1 is accepted as a valid conclusion-bearing negative result.

    accepted_terminal=NO_ONLINE_IDENTIFIABLE_SLOW_STATE
    S1_contract_valid=true
    S1_algorithm_code_executed=false
    S1_compute_executed=false
    conclusion_bearing_iterations_consumed=1
    iterations_remaining=9

The exact registered C-ALPSW formulation is rejected before implementation:

    predictive NLL
    + learned slow-state write cost
    + unrestricted unpenalized fast recurrence h visible to the decoder

cannot uniquely identify causal ownership of predictive memory in z.

The lower-precedence statement that the never-write null is equivalent is also
true, but it does not replace the earlier first-match terminal.

The broader scientific families are not rejected:

- predictive state;
- sparse segmentation;
- continuous lifecycle-owned latent state;
- individual variable lifetime;
- environment-agnostic latent dynamics;
- optimization or held-out transport benefits from an explicit slow channel.

Exactly one next conclusion-bearing action is selected for iteration 2:

    S2_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_DERIVATION

It is another exact derivation and counterexample action. It requires no code,
prototype, CPU/GPU execution, formal experiment or Monitor assignment.

The new scientific candidate is:

    C-ALPSC
    Agent-Local Predictive Slow Channel with exclusive temporal ownership

C-ALPSC is not a repair or revival of the rejected C-ALPSW contract. It is a new
contract whose central proposition is that z can be identified only after every
alternative temporal information channel into the slow predictive decoder is
either excluded or explicitly accounted for.

Iterations 3–10 remain unselected.

---

# 1. Evidence boundary

The review question and manifest are at pushed stage commit:

    a373d6becd08067d866d9a64252d4a163bde4fdb

The exact substantive evidence boundary is:

    b0a5c6b4c32121228c6449cd140b756ae9a17173

No local working tree, browser snapshot, agent transcript, runtime output,
untracked computation or later change is evidence. The manifest explicitly
classifies S1 as an exact derivation rather than runtime evidence.



The active project record states that S1 is complete, one conclusion-bearing
iteration is consumed, nine remain, no code or compute was executed, and the
current result is `NO_ONLINE_IDENTIFIABLE_SLOW_STATE`.



---

# 2. S1 contract-validity audit

## 2.1 Finite source and independent lifecycle changes

The source is complete and exact.

Each lifecycle independently samples:

    B ∈ {0,1}, uniformly
    S ∈ {23,32}, uniformly

with B and S independent within and across lifecycles.

The two scripts are:

    S=23:
      regime sequence = B,B,1-B,1-B,1-B,B,B
      cue indices      = 0,2,5
      complete lengths = 2,3

    S=32:
      regime sequence = B,B,B,1-B,1-B,B,B
      cue indices      = 0,3,5
      complete lengths = 3,2

The final segment is right-censored and is not counted as a complete lifetime.
Routing keys do not enter observations, actions, objectives or model inputs.


The membership table has three lifecycle epochs and exactly 21 active rows. It
contains:

- initial joins;
- one temporary leave;
- one rejoin;
- one fresh genuine join;
- terminal leaves.

Temporary absence does not advance the lifecycle active-step index, age, state
or RNG. Every lifecycle therefore receives the same seven-active-row local
process, independent of the membership schedule.


This satisfies the registered requirement for anonymous runtime membership and
identity-independent lifecycle change points.

## 2.2 Observation and target law

At active index n:

    O_n = (C_n, X_n)

where:

    C_n = 1 exactly on a cue row
    X_n = R_n on a cue row
    X_n = ⊥ otherwise

The generic binary target satisfies:

    P(Y_n = R_n | R_n)     = 3/4
    P(Y_n = 1-R_n | R_n)   = 1/4

All transition and observation probabilities are rational. The logarithms enter
only through the exact log score.

The source-control utility is separate:

    U_n = 1 iff A_n = R_n

It is used only to establish constructive external-policy access and is absent
from the writer objective and writer information.


A cue that is an ordinary online observation is not forbidden oracle
supervision. The oracle comparison is performed only after the finite source has
been defined. The construction is deliberately easy enough to isolate the
identifiability question; it is not presented as a learning-difficulty
benchmark.

## 2.3 Online filtration

The registered filtration contains:

- current and past legal local observations;
- past executed primitive actions;
- anonymous active masks and membership events;
- prior recurrent and slow states;
- already-realized writer randomness.

It excludes:

- the current target;
- future observations;
- B and S as oracle variables;
- unobserved future boundaries;
- external reward;
- routing identity.

The current cue is online and legal. Prediction is scored before later
information becomes available.


No future-data or identity leak is present.

## 2.4 Exact NLL arithmetic

For a correct remembered regime:

    H
      = -(3/4) ln(3/4) -(1/4) ln(1/4)
      = ln 4 -(3/4) ln 3

For the opposite regime:

    H_wrong
      = -(3/4) ln(1/4) -(1/4) ln(3/4)
      = ln 4 -(1/4) ln 3

Therefore one wrong-regime prediction costs exactly:

    H_wrong - H = (1/2) ln 3 > 0

The objective is normalized over all 21 active rows:

    J_beta(M)
      = mean_active E[-ln p_M(Y_n | F_n)]
        + beta * mean_active E[w_n]

Structural join initialization is not a learned Bernoulli write and therefore
has zero write cost.


The intended writer performs exactly two learned writes per seven active rows,
so:

    J_beta(SPARSE) = H +(2/7) beta

This normalization is correct: six learned writes occur across 21 active rows.
Boundary precision and recall are both exactly one, and the complete lifetimes
are exactly 2 and 3.


## 2.5 Registered structural nulls

The frozen predictive decoder is allowed to use h. A one-bit recurrent state
updates on a cue and persists otherwise:

    h_n = X_n        when C_n=1
    h_n = h_{n-1}    otherwise

Temporary absence freezes h.

This legal recurrence reaches H on every active row without a learned slow-state
write. For beta ≥ 0, the registered null optima are therefore:

    ALWAYS_WRITE
      NLL = H
      write rate = 6/7
      J = H +(6/7) beta

    NEVER_WRITE_AFTER_JOIN
      NLL = H
      write rate = 0
      J = H

    FIXED_AGE_OR_PERIODIC_WRITE
      NLL = H
      minimum registered positive write rate = 1/7
      J = H +(1/7) beta
      or H if optional eligible writes may be skipped

    MEMBERSHIP_EVENT_ONLY_WRITE
      NLL = H
      write rate = 1/21 when rejoin is required to write
      J = H +(1/21) beta
      or H if that write may be skipped

    POST_HOC_NONCAUSAL_SEGMENTATION
      no retrospective state may be installed online
      legal online prediction still uses h
      J = H

These values agree with the registered model class.


The deliberately restricted illustrative decoder in the subsequent reference
calculation is not a registered optimum. Its `H +(5/28) ln 3` value should be
read as applying to the stated p_z-style decoder that does not use the recurrent
solution. If it were instead interpreted as the optimum of every h-free decoder
over the full filtration, direct use of a current cue would need to be specified
and the reference count would differ. This is a wording boundary in a
non-gating example, not a defect in any registered null, theorem, inequality or
branch decision.

No contract-level enumeration defect is found.

## 2.6 Recurrent-absorption theorem

The theorem is admissible and correct under the frozen contract.

For any finite-horizon source with finite legal observations, actions and
membership events, the legal-history set is finite. A recurrent state can
encode:

- the complete legal history; or
- its predictive sufficient statistic.

For every legal history f, define the absorbed prediction:

    p_abs(y | f)
      = E[p_original(y | f,h,z) | f]

The negative logarithm is convex, so the log-sum/Jensen inequality gives:

    E[-ln p_abs(Y | f)]
      ≤ E[-ln p_original(Y | f,h,z)]

where the right side includes the original internal writer randomness.

If the original writer has expected learned-write rate q > 0:

    J_beta(absorbed) ≤ L
    J_beta(original) = L + beta q

Thus:

- beta > 0: zero-write absorption is strictly better;
- beta = 0: it is better or tied, so the sparse owner is not unique;
- beta < 0: an always-write realization is favored by the objective.

The frozen contract specifies no dimension bound, information bottleneck or
complexity penalty on h and explicitly supplies h to the predictive decoder.
On the concrete source, only one recurrent bit is required, so the theorem does
not rely on an impractically large history encoding.



## 2.7 Delta calculation

For beta ≥ 0, the complete C-ALPSW parameter class itself contains the absorbed
zero-write solution:

    min_C-ALPSW J_beta = H

The best registered null also reaches:

    min_null J_beta = H

Therefore:

    Delta_ID(beta) = 0

If the treatment class is restricted to the intended two-write construction:

    Delta_ID(beta)
      = H - [H +(2/7) beta]
      = -(2/7) beta < 0
      for beta > 0

For beta < 0, always-write is available and receives the most favorable write
term. No open interval on the real line has strictly positive Delta_ID.


## 2.8 Constructive controls

The intended ALPSW policy writes the observed regime into z and chooses:

    A_n = z

The recurrent control writes the observed regime into h and chooses:

    A_n = h

Both are correct on every active row:

    U_star_ALPSW = 1
    U_star_G8 = 1

This source therefore does not manufacture a claim that recurrent control lacks
the required representational capacity.


The G8 repository base is genuinely a direct recurrent open-roster policy with
no skill/event hierarchy, lifecycle-owned hidden state and no padding-capacity
input. Its lifecycle contract freezes hidden state during temporary absence and
initializes a genuine join with zero hidden state.




Its focused tests cover constructive utility, inactive-capacity invariance,
lifecycle ownership, replay and fail-closed evidence semantics.




## 2.9 Invariances

The exact proof correctly establishes zero mismatch under:

- lifecycle-key relabeling;
- active-member row permutation;
- inactive padding;
- temporary-absence insertion;
- latent 0↔1 relabeling.

The objective and state ownership are functions of lifecycle-local active
histories rather than key values or global row packing.


## 2.10 Iteration accounting

No algorithm, prototype, experiment or runtime action occurred. The exact
derivation is the first valid scientific terminal and therefore consumes one
iteration. Nine remain.

This agrees across:

- `CURRENT_WORK.md`;
- the S1 artifact;
- the Chinese iteration report;
- the idea portfolio.





## S1 validity conclusion

    finite_source_valid=true
    online_filtration_valid=true
    independent_lifecycle_changes=true
    membership_semantics_valid=true
    NLL_arithmetic_valid=true
    write_normalization_valid=true
    registered_nulls_valid=true
    absorption_theorem_valid=true
    constructive_controls_valid=true
    invariances_valid=true
    iteration_accounting_valid=true
    terminal_affecting_defects=none

---

# 3. First-match terminal

The correct terminal is:

    NO_ONLINE_IDENTIFIABLE_SLOW_STATE

The first-match order is:

    1. INVALID_ALPSW_DERIVATION_CONTRACT
    2. NO_ONLINE_IDENTIFIABLE_SLOW_STATE
    3. NULL_EQUIVALENT_PREDICTIVE_WRITE
    4. PASS_ALPSW_IDENTIFIABILITY_DERIVATION

`INVALID_ALPSW_DERIVATION_CONTRACT` does not apply. The source is finite,
online, exact, anonymous, membership-complete and invariant; no forbidden
information enters the registered writer or predictor.

`NO_ONLINE_IDENTIFIABLE_SLOW_STATE` applies because no nonempty beta interval
exists in which a nondegenerate sparse writer is uniquely optimal.

`NULL_EQUIVALENT_PREDICTIVE_WRITE` is factually true: the never-write null
attains the same H. It is lower precedence and is the witness for the earlier
non-identifiability result, not a competing terminal.



Recurrent absorption is admissible because:

1. h is part of the frozen C-ALPSW state;
2. h reads the same legal online history;
3. h is explicitly supplied to the predictive decoder;
4. no h capacity or information cost exists;
5. the never-write null is evaluated under the same factorization.

The raw frozen objective explicitly conditions the predictive decoder on both
z and h.



The result is not eligible for a beta adjustment, latent-width change, harder
source or empirical rescue. Those would change the frozen scientific contract.


---

# 4. Smallest supported and refuted propositions

## 4.1 Smallest supported proposition

Let C-ALPSW(S1) denote the exact registered factorization in which an
unrestricted, unpenalized fast recurrent state h:

- reads the legal online history; and
- is supplied to the predictive decoder.

S1 supports:

    P_absorption:

    For every finite discrete online source and every C-ALPSW(S1) predictive
    model, there exists a never-write-after-join recurrent model whose expected
    predictive NLL is no greater.

For any original model with positive expected write rate and beta > 0, the
absorbed model has strictly lower J_beta.

The explicit source strengthens this with a one-bit constructive witness.

## 4.2 Additional supported proposition

    P_ownership:

    A write-only complexity penalty cannot identify which state object owns
    predictive memory when another unpenalized temporal channel visible to the
    decoder can carry the same sufficient statistic.

This is broader than the one finite source but narrower than a claim that slow
states are useless.

## 4.3 Smallest refuted proposition

    P_ALPSW_exact:

    Predictive NLL plus a learned-write cost uniquely identifies a
    lifecycle-owned sparse slow state while an unrestricted, unpenalized fast
    recurrence reads the same online history and is also visible to the
    predictive decoder.

This exact proposition is refuted.

## 4.4 Propositions not refuted

S1 does not refute:

- existence of useful predictive states;
- existence of online process boundaries;
- sparse segmentation under a different information contract;
- variable individual lifetime;
- continuous slow state;
- a useful explicit state under intervention;
- optimization or sample-efficiency advantage over recurrence;
- held-out transport advantage over G8;
- set-equivariant population memory;
- an environment-agnostic source of lifecycle persistence.

It also does not prove that G8 and a future corrected mechanism train equally
well. The result concerns objective identifiability, not optimization dynamics.

## 4.5 Retained closure and quarantine scopes

Every R42–R48 boundary remains unchanged:

- R42 closes its incumbent-conditioned categorical logit residual;
- R43 remains quarantined because its fixed anchor failed;
- R44 closes the frozen-source global-K=50 reward-credit renewal route;
- R45 closes the Alice–Bob natural-support Q/DR route;
- R46 closes its exact HMRV estimator/read combination, not oracle
  heterogeneity;
- R47 closes its exact spectral representation and score;
- R48 closes focal zero-reset at categorical SET.

The accepted direction note already records these exact scopes.


---

# 5. Fresh plural CDC pass

## 5.1 Candidate A — C-ALPSC: exclusive agent-local predictive slow channel

### Conjecture

A lifecycle-owned slow state can be internally identifiable if it is the sole
cross-active-step information channel available to its self-supervised
predictive decoder.

The primitive controller may retain an unrestricted fast recurrent state h, but
h belongs to the control channel and is not visible to:

- the slow writer;
- the slow candidate encoder;
- the slow predictive decoder.

### Derivation

S1 did not show that z was unnecessary. It showed that the objective could not
distinguish z from an alternative free memory channel.

Removing alternative temporal channels from the slow predictive filtration
changes the question from:

    Which of h or z happens to store the information?

to:

    Does a sparse z transition provide the minimum-description online
    predictive state within the declared slow channel?

This is a scientifically meaningful ownership contract, while G8 remains the
complete external-behavior comparator.

### Strongest counterexamples

1. Fast-state leak:
   one recurrent bit restores the S1 zero-write solution.

2. Age or global-clock leak:
   on the S1 source, active age plus the current cue pattern can reconstruct the
   regime script without a slow write.

3. Action leak:
   if the current primitive action equals the remembered regime and is visible
   to the decoder, it transfers h into the predictor.

4. Auxiliary-writer recurrence:
   a separate hidden state inside the writer is z under another name.

5. Direct-cue decoder shortcut:
   if the current boundary cue is given directly to the decoder, a delayed
   fixed-age writer can predict the cue row directly and install the state later.
   On the S1 scripts, writes at active ages 3 and 6 can then match the two-write
   cue writer, destroying boundary uniqueness.

### Correction

Define an exclusive slow channel:

- current local observation enters the writer;
- the installed z enters the predictive decoder;
- current cue, h, age, clock, action history, active-set history and auxiliary
  recurrence do not bypass z into the decoder;
- membership events govern ownership and censoring but are not a predictive
  clock feature.

### Disposition

Retain and select for S2 exact derivation.

## 5.2 Candidate B — C-JRDM: jointly rate-coded dual memory

### Conjecture

Rather than excluding h from the predictive model, jointly charge information
or description length for both h and z, allowing the objective to decide which
channel should own fast and slow information.

### Strongest counterexample

The result can depend on arbitrary coding units, parameterization, state
dimension or invertible mixing between h and z. A penalty on activations or
dimension is not automatically an invariant information cost.

### Correction and status

A future version requires a representation-invariant joint codelength or mutual
information contract. Park it. It is more complex and less reversible than
testing exclusive ownership first.

## 5.3 C-ALH — categorical agent-local hazard

Status remains parked.

S1 does not rescue it. A per-step categorical hazard remains vulnerable to
`CE-HAZARD-AS-K1-RENAMING`, and reward-trained termination would revive the
R43–R45 family unless a new source and credit authority are independently
identified.

Reactivation condition:

    an identified source requires an explicit task-directed termination action
    after a predictive boundary object has already been established

## 5.4 C-ATS — continuous adaptive-timescale recurrence

Status remains parked and its objection is strengthened.

A continuous leak can also be absorbed into or reparameterized as recurrence.
It still lacks a threshold-free segment/lifetime estimand.

Reactivation condition:

    a threshold-invariant survival or causal-persistence quantity plus explicit
    accounting for alternative recurrent memory channels

## 5.5 C-SEPM — set-equivariant persistent population memory

Status remains parked.

It may address complementary allocation, but it changes coordination and
individual lifetime simultaneously. TEAM_REC and ordinary set encoders remain
simpler explanations.

Reactivation condition:

    an identified complementary-allocation source on which lifecycle recurrence
    and TEAM_REC are insufficient

## 5.6 Broader predictive-state family

Status:

    live, but corrected

S1 rejects ownership identification under an unrestricted alternative memory
channel. It does not reject predictive latent state.

Advancement condition:

    prove a coherent information partition or invariant joint memory cost before
    implementation

## 5.7 G8 and ordinary recurrence

G8 remains:

- the accepted usable dynamic-roster base;
- the complete external-policy comparator;
- the strongest simpler explanation.

S1 strengthens recurrence as an exact predictive-absorption counterexample. It
does not convert recurrence into a universal research-admission gate.

Any future advantage claim must concern:

- optimization;
- sample efficiency;
- causal mediation;
- robustness;
- held-out transport;
- or complexity benefit,

not finite representational impossibility.

---

# 6. Selected iteration-2 action

    action_id=S2_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_DERIVATION
    action_class=accepted_evidence_reanalysis_plus_exact_derivation
    conclusion_bearing_iteration=2
    code_required=false
    compute_required=false
    prototype_required=false
    formal_run_required=false
    Monitor_required=false

## 6.1 Exact scientific question

On the immutable S1 finite source, does an agent-local sparse writer become
online-identifiable when z is the only cross-active-step memory available to the
slow predictive decoder?

The action must determine whether there is a nonempty exact beta interval in
which:

1. the unique global optimum writes exactly on the two post-join cue rows;
2. every always-write, never-write, fixed-age, periodic,
   membership-event-only and post-hoc null has strictly larger J_beta;
3. no auxiliary temporal side channel is present;
4. boundary precision and recall remain exactly one;
5. complete lifetimes remain exactly 2 and 3;
6. constructive ALPSC and G8 policies both retain U*=1.

## 6.2 Why this is the cheapest decisive action

It reuses the accepted exact S1 source and arithmetic. No implementation,
optimization or environment run is needed.

It directly tests the correction implicated by S1:

    memory ownership is identifiable only relative to an information channel

A prototype would confound:

- mathematical non-identifiability;
- architectural leakage;
- implementation error;
- optimization failure.

A complexity-penalized dual-memory model is more expensive and introduces a new
invariance problem. C-ALH, C-ATS and C-SEPM each contain an unresolved
definitional confound. The exclusive-channel proof therefore has the highest
information gain at the lowest cost and is fully reversible.

---

# 7. Frozen C-ALPSC scientific contract for S2

## 7.1 Claim ceiling

S2 can establish only:

    an internally identifiable sparse predictive slow channel under a declared
    exclusive information partition

It cannot establish:

- utility gain;
- optimization gain;
- sample efficiency;
- natural policy use;
- causal action mediation;
- held-out transport;
- semantic skill;
- superiority over G8;
- necessity of explicit slow state.

Even a PASS authorizes only a later CDC decision.

## 7.2 State objects

Each lifecycle owns:

    h_i,t
      fast recurrent control state, belonging only to the primitive-control
      channel

    z_i,t
      bounded slow predictive state, sole cross-active-step memory of the slow
      predictive channel

    w_i,t
      learned slow-channel write indicator

    age_i,t
      evidence-only active-step segment age; not a writer or decoder input in S2

The S2 proof may use the binary witness state:

    z ∈ {0,1}

but its conclusion is invariant to the 0↔1 relabeling.

## 7.3 Exclusive online filtration

At an active post-join row, the slow writer may use only:

    current local task-blind observation O_i,t
    previous slow state z_i,t-
    fresh registered writer randomness

It may not use:

- h;
- age;
- active-step index;
- global time;
- `t mod k`;
- past observations except through z;
- current or past primitive actions;
- active-set or roster history;
- membership-event type as a predictive feature;
- another recurrent or persistent writer state;
- identity, role, goal, reward, success, progress or oracle boundary.

Structural join is handled separately by q_join.

Membership status may gate whether a transition exists, but it cannot encode a
predictive clock.

## 7.4 Writer and decoder factorization

At genuine join:

    z_i,0 ~ q_join(z | O_i,0)

There is no Bernoulli write cost at structural initialization.

At an active existing row:

    w_i,t ~ Bernoulli(lambda_phi(O_i,t, z_i,t-))

If w=1:

    z_i,t+ ~ q_phi(z | O_i,t, z_i,t-)

If w=0:

    z_i,t+ = z_i,t-

The slow predictive decoder is:

    p_eta(Y_i,t | z_i,t+)

For S2, the decoder does not receive:

- O_i,t directly;
- h;
- age or clock;
- action;
- active-set summary;
- membership history;
- auxiliary memory.

The current cue can affect prediction only by causing a slow-state write.

This restriction is the scientific object under test, not an implementation
detail.

## 7.5 Primitive-control separation

The complete primitive controller remains conceptually:

    a_t ~ pi_theta(
              a |
              current observations,
              h_t,
              stopgrad(z_t+),
              active mask,
              ordinary G8 active-set context
          )

Primitive reward gradients do not enter the S2 writer or decoder.

The S2 derivation trains or evaluates no primitive controller. The action path
exists only to define the later comparator and constructive U*=1 control.

## 7.6 Supervision and credit

The slow objective is:

    J_beta(M)
      = mean_active E[-ln p_eta(Y_n | z_n+)]
        + beta * mean_active E[w_n]

External reward is absent.

No task field, identity, role, goal, success, progress, duration label,
change-point label or future observation enters writer training.

Oracle boundaries remain audit-only.

There is no:

- renewal advantage;
- lifetime reward;
- switch penalty;
- entropy bonus;
- primitive PPO gradient into the writer;
- high-level reward objective.

## 7.7 Membership semantics

Retain the S1 lifecycle rules exactly:

Genuine join:

- allocate fresh ownership;
- structurally initialize z from the current local observation;
- initialize h separately for primitive control;
- set evidence age to zero.

Temporary leave:

- freeze h, z, writer RNG position and the open segment;
- emit no slow transition and no objective row.

Rejoin:

- restore the frozen state;
- resume from the next active local observation;
- do not force a write.

Terminal leave:

- right-censor the current segment;
- record evidence;
- delete state ownership.

Rollout, update and checkpoint boundaries are not lifetime events.

## 7.8 Immutable S2 source

S2 must use the exact S1 source without changing:

- the B and S laws;
- the two scripts;
- the membership table;
- the 21 active rows;
- the cue and target laws;
- the complete lifetimes;
- utility definition;
- structural join semantics;
- invariance transformations.

Changing source difficulty would be a different action.

## 7.9 Admissible structural nulls

The proof must evaluate:

1. `ALWAYS_WRITE`

2. `NEVER_WRITE_AFTER_JOIN`

3. every deterministic fixed-age subset over post-join active ages 1 through 6

   There are 2^6 such subsets. This is stronger than checking only one period.

4. every deterministic periodic schedule and phase representable within the
   seven-active-row horizon

5. `MEMBERSHIP_EVENT_ONLY_WRITE`

   Evaluate every deterministic mapping from the current membership event to a
   write decision, with no membership history.

6. `POST_HOC_NONCAUSAL_SEGMENTATION`

   Oracle boundaries may be scored after collection but cannot install online
   state or alter predictions.

7. every stochastic mixture of the deterministic policies above

   The proof must use linearity/convexity or explicit enumeration to show that a
   stochastic mixture cannot beat its best deterministic extreme point.

## 7.10 Mandatory side-channel counterexamples

S2 must also construct and record these deliberately forbidden leak controls:

### FAST_H_LEAK

Give the decoder the one-bit cue-updated h.

Required result:

    zero learned writes
    predictive NLL = H

### AUXILIARY_RNN_LEAK

Give the writer or decoder any additional persistent one-bit state.

Required result:

    recurrence absorption reappears

### AGE_CLOCK_LEAK

Give the decoder active age or an equivalent global/local clock together with
the current cue pattern.

Required result on the immutable source:

    a zero-write predictor can reconstruct the regime schedule

### ACTION_LEAK

Give the decoder a current action that equals the remembered regime.

Required result:

    action transfers fast-state information and removes the need for z

### DIRECT_CUE_DECODER_LEAK

Give the current cue directly to the decoder rather than routing it through z.

The proof must exhibit the delayed fixed-age construction, including the
two-write schedule at active ages 3 and 6, that matches the cue writer's
predictive NLL while breaking exact boundary ownership.

### ACTIVE_SET_TIME_LEAK

Give the decoder any active-set or membership-summary sequence from which local
active age or global row can be reconstructed.

Required result:

    classify it as a clock leak, not legitimate slow-state evidence

These leak controls are counterexamples, not admissible C-ALPSC models. Their
purpose is to prove that the exclusivity conditions are load-bearing and to
prevent a later implementation from silently restoring S1.

## 7.11 Estimands

Retain:

    H = ln 4 -(3/4) ln 3

Define:

    J_beta^SC(M)
      = mean_active E[-ln p_eta(Y_n | z_n+)]
        + beta * mean_active E[w_n]

Define:

    Delta_SC(beta)
      = minimum J_beta^SC over all admissible structural nulls
        - minimum J_beta^SC over C-ALPSC

Define exact ownership evidence:

    write_schedule_unique(beta)
    boundary_precision
    boundary_recall
    distinct_complete_lifetime_count

Constructive external controls remain:

    U_star_ALPSC
    U_star_G8

## 7.12 Exact proof obligations

A PASS requires every item below.

1. The source and filtration are exact and online.

2. The candidate cue writer:

       writes exactly at the two post-join cue rows
       achieves predictive NLL H
       has learned-write rate 2/7
       has J_beta = H +(2/7) beta

3. For every beta in the predeclared open interval:

       0 < beta < (1/2) ln 3

   the cue writer is the unique global minimizer up to the invertible 0↔1 latent
   relabeling.

4. For every beta in that interval:

       Delta_SC(beta) > 0

   against every registered admissible null.

5. The proof enumerates every deterministic fixed-age subset, every periodic
   phase, all membership-only policies and the relevant candidate-state maps.
   It may not evaluate only a hand-selected representative.

6. Any stochastic writer is handled by an exact convexity or extreme-point
   proof.

7. Boundary audit is exact:

       precision = 1
       recall = 1

8. Complete active-step lifetimes remain exactly:

       {2,3}

9. Constructive controls are exact:

       U_star_ALPSC = 1
       U_star_G8 = 1

10. Registered invariance mismatches are zero for:

       lifecycle-key relabeling
       active-member permutation
       inactive padding
       temporary-absence insertion
       latent 0↔1 relabeling

11. Every mandatory leak control reproduces the stated shortcut or equivalence.

12. No reward, task field, identity, role, success, progress, future input,
    auxiliary memory or clock enters the admissible slow channel.

There is no statistical, mixed or underpowered branch.

## 7.13 First-match terminals

Apply in this exact order.

1. `INVALID_ALPSC_DERIVATION_CONTRACT`

   Any incorrect source arithmetic, inconsistent online order, forbidden
   information, incomplete null enumeration, invalid membership semantics or
   failed invariance.

2. `SIDE_CHANNEL_OWNERSHIP_LEAK`

   Any supposedly admissible writer or decoder path carries temporal information
   outside z, including h, age, clock, action, direct cue bypass, active-set
   history or auxiliary recurrence.

3. `NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL`

   The exclusive contract is valid, but the exact interval is empty, the cue
   writer is not unique, or an admissible structural null has
   `Delta_SC(beta) <= 0` anywhere in the frozen interval.

4. `PASS_ALPSC_IDENTIFIABILITY_DERIVATION`

   Every exact proof obligation passes.

## 7.14 Required artifact

The sole conclusion-bearing artifact is:

    docs/research/cdc/EVIDENCE_NOTES/
    20260724_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_S2.md

It must contain:

- the immutable S1 source table or an exact content-bound reference to it;
- the corrected filtration;
- the complete deterministic-policy enumeration;
- the stochastic-policy argument;
- exact logarithmic objective values;
- the proof over the complete beta interval;
- every leak counterexample;
- constructive ALPSC and G8 controls;
- invariance proofs;
- smallest supported/refuted proposition;
- terminal branch;
- no engineering plan or resource schedule.

## 7.15 Stop and iteration rule

Stop on the first valid S2 terminal.

A valid PASS or negative consumes iteration 2, leaving eight.

An invalid derivation consumes no iteration and permits at most one bounded
correction of transcription, arithmetic or proof checking under the identical
source, filtration, nulls and interval.

Changing:

- the decoder filtration;
- the writer inputs;
- the beta interval;
- the source;
- the null family;
- the estimand;
- or the terminal order

requires another Pro decision rather than a local repair.

A second invalid realization is a blocker.

After a valid S2 terminal, return it to this same registered Pro conversation
before selecting iteration 3.

---

# 8. Durable repository deltas after factual reconciliation

## 8.1 Conjecture deltas

Update `C-ALPSW`:

    status=closed_exact_formulation
    terminal=NO_ONLINE_IDENTIFIABLE_SLOW_STATE
    no_local_rescue=true

Retain its consequence boundary:

    broader predictive state and sparse segmentation remain unresolved

Add:

### `C-ALPSC — Agent-local predictive slow channel`

Status:

    selected for S2 exact derivation
    no implementation or compute selected

Claim:

    a lifecycle-owned sparse slow state may be internally identifiable when it
    is the sole cross-active-step memory in the task-blind slow predictive
    channel

Strongest simpler explanation:

    the separation merely assigns memory ownership by architecture and produces
    no optimization, mediation or held-out benefit over G8

Intervention consequence:

    not yet tested; a future same-state z intervention would have to alter
    primitive behavior after S2

Natural consequence:

    not yet tested; S2 establishes only an identifiable internal write process

Held-out consequence:

    not yet tested; G8 and a mechanism-matched masked-z arm remain mandatory

Add parked:

### `C-JRDM — jointly rate-coded dual memory`

Reactivation:

    an invariant joint codelength or information cost for h and z

Update `C-ATS`:

    recurrence absorption is an additional objection; retain the threshold-free
    lifetime requirement

Update `C-ALH` and `C-SEPM` without promotion.

Update `C-REC`:

    retain as the exact S1 absorption witness and mandatory comparator, not a
    universal admission gate

## 8.2 Lemma deltas

Add:

### `L-S1-VALID-NEGATIVE`

The exact S1 source and proof validly reject the registered C-ALPSW objective
before implementation.

Does not imply:

    predictive or sparse lifetime mechanisms are generally impossible

### `L-OWNERSHIP-RELATIVE-TO-FILTRATION`

Memory ownership is identifiable only relative to an explicit information
filtration or a joint complexity accounting over every alternative temporal
channel.

### `L-UNPENALIZED-CHANNEL-DOMINANCE`

Penalizing writes to z cannot identify z when an unpenalized temporal channel
visible to the decoder carries the same predictive sufficient statistic.

### `L-CONTROL-PREDICTION-SEPARATION`

A recurrent G8 policy may remain the complete external-behavior comparator even
when h is excluded from a separately defined slow self-supervised channel.

This does not imply:

    the separated channel improves behavior

Retain and strengthen `L-RECURRENT-NESTING` with the accepted S1 theorem.
The current ledger already records the narrow absorption conclusion.


## 8.3 Counterexample deltas

Add:

### `CE-FAST-STATE-PREDICTIVE-ABSORPTION`

A free h visible to the decoder absorbs z and eliminates write cost.

### `CE-AGE-CLOCK-AS-SLOW-STATE`

Age or global time can encode regime phase and counterfeit predictive lifetime.

### `CE-ACTION-AS-PREDICTIVE-MEMORY`

An action selected from h can transfer the same persistent bit into the
predictive decoder.

### `CE-AUXILIARY-WRITER-RECURRENCE`

A recurrent writer hidden state is an undeclared second slow state and restores
the ownership ambiguity.

### `CE-DIRECT-CUE-DELAYED-WRITE`

Direct cue access by the decoder permits a delayed fixed-age writer to match
predictive NLL without matching the true boundary.

### `CE-ACTIVE-SET-CLOCK-LEAK`

A deterministic roster or membership pattern may reveal global/local time and
substitute for learned slow memory.

Retain:

- `CE-RECURRENCE-ABSORPTION`;
- `CE-ALWAYS-WRITE-PREDICTOR`;
- `CE-NEVER-WRITE-PERSISTENCE`;
- `CE-MEMBERSHIP-GAP-AS-LIFETIME`;
- `CE-HAZARD-AS-K1-RENAMING`.



## 8.4 Portfolio delta

Set:

    C-ALPSW:
      closed exact formulation

    C-ALPSC:
      live and selected for S2 derivation

    C-JRDM:
      parked pending invariant joint complexity

    C-ALH:
      parked

    C-ATS:
      parked

    C-SEPM:
      parked

    C-OPEN-ROSTER-DIRECT:
      accepted base and mandatory complete comparator

    C-REC:
      mandatory simpler explanation and S1 absorption witness

Scheduled action:

    S2_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_DERIVATION

Authorization:

    derivation selected
    code not selected
    compute not selected
    iterations 3–10 unselected

## 8.5 Evidence-note delta

Add:

    docs/research/cdc/EVIDENCE_NOTES/
    20260724_ALPSW_S1_RESULT_AND_S2_DIRECTION.md

Record:

- S1 validity audit;
- accepted first-match terminal;
- exact supported and refuted propositions;
- all unchanged R42–R48 scopes;
- the new C-ALPSC contract;
- S2 action and proof obligations;
- iteration accounting;
- evidence commit
  `b0a5c6b4c32121228c6449cd140b756ae9a17173`;
- this response provenance.

Do not add an experiment row to `ExpRecord.md`. S2 is not an experiment.

## 8.6 Current-work delta

After factual reconciliation, set:

    last_completed_assignment_id=S1_ALPSW_IDENTIFIABILITY_DERIVATION
    active_assignment_id=S2_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_DERIVATION
    next_boundary=COMPLETE_EXACT_S2_DERIVATION_THEN_RETURN_TO_PRO
    conclusion_bearing_iterations_consumed=1
    skill_lifetime_chain_iterations_remaining=9
    k_decoupling_current_result=NO_ONLINE_IDENTIFIABLE_SLOW_STATE
    active_scientific_direction=C_ALPSC
    active_algorithm=PREFIX_NORMALIZED_OPEN_ROSTER_G8_imported_base
    code_required=false
    compute_required=false
    formal_compute_status=not_started

Only a valid S2 terminal changes the iteration count to two consumed and eight
remaining.

---

# 9. What this ruling does not authorize

This response does not authorize:

- algorithm code;
- an implementation plan;
- a prototype;
- CPU or GPU execution;
- formal training, evaluation or analysis;
- Monitor assignment;
- modification of G8;
- a fast-state capacity change;
- an h complexity penalty;
- a beta sweep;
- a new source;
- a harder source;
- direct cue access by the S2 decoder;
- h, age, time, action or active-set history in the S2 slow channel;
- an auxiliary writer RNN;
- external reward in predictive supervision;
- task fields, identity, roles, goals, success or progress;
- a categorical skill catalogue;
- a reward-trained hazard;
- revival of R42–R48;
- mutation of `aggressive`;
- selection of iterations 3–10;
- an individual-skill, utility, transport or superiority claim;
- integration into the final HMASD algorithm.

A future S2 PASS would establish only internal identifiability under the
exclusive channel. It would still require a new CDC decision before any
implementation or behavioral evidence.

---

# 10. 中文用户简报

S1 裁决有效：`NO_ONLINE_IDENTIFIABLE_SLOW_STATE`。原因不是 predictive state
本身无用，而是冻结合同把同一在线历史同时交给了不受容量限制、没有复杂度代价的快速
recurrent 状态 h，并允许预测器直接读取 h。一个 recurrent bit 就能达到与 sparse z
相同的精确预测熵 H，同时不支付任何 learned-write cost。因此 beta>0 时 never-write
更优，beta=0 时不唯一，beta<0 时 always-write 更优；不存在合格的开放 beta 区间。
较低优先级的 `NULL_EQUIVALENT_PREDICTIVE_WRITE` 虽然也成立，但不能覆盖更早的
first-match 终态。本轮精确负结果消耗第 1 次迭代，剩余 9 次。

第 2 次结论性行动只做一个新的精确推导：
`S2_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_DERIVATION`。新候选 C-ALPSC 要求 z
成为慢预测通道唯一的跨 active-step 记忆；writer 可以看到当前通用局部观测，但
decoder 只能通过写入后的 z 获得持续信息。h、age、全局时钟、动作、active-set 历史、
当前 cue 的 decoder 直通和任何辅助 RNN 都必须被排除，并分别构造 shortcut
反例。S2 必须在不修改 S1 有限 source 的情况下，精确证明 cue writer 在冻结区间
`0 < beta < (1/2) ln 3` 内是唯一最优，并严格击败所有 always/never/fixed-age/
periodic/membership-only/post-hoc null。

决定性反证条件是：任何合法侧信道仍能以零写入达到 H，任何结构 null 与 cue writer
等价，或冻结 beta 区间内 writer 不唯一。出现任一情况即关闭这份 C-ALPSC 合同，不
进入实现。该行动不写代码、不运行计算；只有有效 S2 终态才消耗第 2 次迭代，其余
第 3–10 次行动仍未选择。
