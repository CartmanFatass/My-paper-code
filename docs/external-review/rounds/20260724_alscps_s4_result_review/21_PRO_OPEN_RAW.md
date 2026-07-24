
# GPT-5.6 Pro CDC Ruling — ALSCPS S4 Horizon-2 Result

## Executive decision

S4 is accepted as a valid conclusion-bearing positive derivation.

    accepted_terminal=PASS_ALSCPS_FUTURE_CLOSED_DERIVATION
    registered_scope=HORIZON_2_ONLY
    S4_contract_valid=true
    terminal_affecting_defects=none
    S4_algorithm_code_executed=false
    S4_compute_executed=false
    conclusion_bearing_iterations_consumed=4
    iterations_remaining=6

The smallest supported claim is:

    On the exact finite S4 source, the coarsest update-congruent quotient that is
    exactly sufficient for all four externally indexed horizon-2 controlled
    sequence kernels has two decoder classes. Every exactly sufficient online
    model has learned-installation rate at least 2/7; equality installs only at
    the two actual post-join regime changes. The resulting complete active-step
    lifetimes are {2,3}.

The registered label `FUTURE_CLOSED` is accepted only at the exact horizon-2
scope. It does not mean closure under arbitrary future horizons, natural
environment trajectories or learned predictive dynamics.

Exactly one iteration-5 conclusion-bearing action is selected:

    S5_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND_DERIVATION

The selected scientific question is whether a monolithic predictive-state
transition can be interpreted as a skill-lifetime transition once the state is
also required to predict generic transition phase. The shortest exact
discriminator reuses the same scripts and asks whether the next-active
observation law changes inside a segment whose current controlled behavior is
unchanged.

The associated live correction candidate is:

    C-ALBPF
    Agent-Local Behavioral / Predictive-Phase Factorization

S5 is an exact derivation and counterexample action. It requires no algorithm
code, prototype, CPU/GPU execution, experiment, Monitor or resource allocation.

Iterations 6–10 remain unselected.

---

# 1. Evidence boundary

The pushed review stage is:

    de15c718733d0641d857a1e3bfbdc90493f96005

The exact substantive evidence commit is:

    e619437c78b856ea6f24929a359853ac6de30d4e

The canonical question and manifest bind the review to that commit and exclude
browser snapshots, local files, untracked runtime artifacts, code execution,
Monitor observations and later working-tree changes. The S4 artifact is an
exact derivation rather than runtime evidence. 


The principal paths actually used at evidence commit `e619437...` are:

    docs/project/CURRENT_WORK.md
    docs/project/ALGORITHM_PRINCIPLES.md
    docs/project/ExpRecord.md
    docs/external-review/OPEN_REVIEW_PRINCIPLES.md
    docs/research/cdc/CONJECTURES.md
    docs/research/cdc/IDEA_PORTFOLIO.md
    docs/research/cdc/LEMMA_COUNTEREXAMPLE_LEDGER.md
    docs/research/cdc/EVIDENCE_NOTES/
      20260724_ALCPS_S3_RESULT_AND_ALSCPS_S4_DIRECTION.md
    docs/research/cdc/EVIDENCE_NOTES/
      20260724_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_S4.md
    docs/report/DECOUPLED_SKILL_LIFETIME_ITERATION_4.md
    docs/external-review/rounds/20260724_alcps_s3_result_review/
      01_SHARED_SOURCE_MANIFEST.md
      20_PRO_OPEN_QUESTION.md
      21_PRO_OPEN_RAW.md
      30_EVIDENCE_RECONCILIATION.md
    docs/research/cdc/EVIDENCE_NOTES/
      20260724_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_S3.md
      20260724_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_S2.md
    ha_ctse_process/open_roster_direct_mvp.py
    tests/ha_ctse_process_open_roster_direct_mvp_test.py

At this boundary, the project records S4 as a valid proof-only PASS, with four
iterations consumed, six remaining and no iteration-5 code or compute selected.



`ExpRecord.md` remains an experiment dashboard. S4 is absent as an experiment
because it executed no environment, optimizer, prototype or formal run; its
authoritative evidence is the derivation artifact and iteration report.


---

# 2. S4 contract-validity audit

## 2.1 Frozen lifecycle source

S4 preserves the exact S3 lifecycle source.

Each lifecycle independently samples:

    B ∈ {0,1}, uniformly
    S ∈ {23,32}, uniformly

with B and S mutually independent within and across lifecycles.

The active-step scripts are:

    S=23:
      R_0..R_6 = B,B,1-B,1-B,1-B,B,B
      cue rows = 0,2,5
      complete lifetimes = 2,3

    S=32:
      R_0..R_6 = B,B,B,1-B,1-B,B,B
      cue rows = 0,3,5
      complete lifetimes = 3,2

The three-lifecycle membership table still contains exactly 21 active rows, one
temporary leave/rejoin, one genuine join and terminal leaves. Temporary absence
creates no active transition, advances neither active age nor segment age, and
freezes lifecycle state and RNG. Routing keys remain provenance only.


The nuisance bit remains:

    N_n ~ Bernoulli(1/2)

independently of B, S, R, membership, plan and branch outcomes. It is a legally
observed nuisance rather than a hidden task variable.

No source-binding defect exists.

## 2.2 Writer filtration and online order

At an active existing row, the writer may use only:

    current O_n=(C_n,X_n,N_n)
    previous z_n-
    fresh registered writer randomness

It receives no:

- fast recurrent state `h`;
- active age or active index;
- local or global time;
- `t mod k`;
- observation history except through z;
- natural action;
- plan history;
- active-set or membership history;
- auxiliary persistent state;
- identity or role;
- external reward;
- task, goal, success or progress field;
- branch outcome;
- future observation;
- oracle regime or boundary.

Structural join sets `z=B` from the current cue without counting a learned
installation. Temporary leave freezes the state. Terminal leave right-censors
and deletes ownership only after evidence is recorded.



The writer update occurs before the sequential decoder and branch outcomes. No
future-data or task/reward leak is present.

## 2.3 External plan support and branch non-mutation

At every legal active history, S4 enumerates all four open-loop plans:

    a=(u_0,u_1) ∈ {00,01,10,11}

Every plan is:

- externally indexed;
- independent of h, z, history, identity and the natural policy;
- absent from writer input;
- branch-local;
- supplied only to the current sequential decoder;
- completely supported at every legal history.

The plan and branch do not mutate:

- the natural lifecycle;
- membership;
- writer state;
- natural segment age;
- natural RNG.

This is exact controlled support rather than selective natural-policy support.


## 2.4 Sequential decoder filtration

The decoder is:

    p_eta(Y1,Y2 | z,a)

It receives exactly:

    installed z
    current external plan a

It receives no:

- current observation or cue;
- fast recurrence;
- nuisance;
- clock;
- natural action;
- branch future;
- membership history;
- auxiliary temporal state.

Two latent values are sequentially equivalent only when their complete joint
sequence kernels agree for all four plans. Quotient cardinality counts these
decoder-equivalence classes, not raw latent labels.


No direct-observation or temporal side channel is present.

---

# 3. Independent potential-outcome recomputation

## 3.1 Exact branch laws

The first branch observation is:

    Y1 ~ Bernoulli(1/2)

independently of regime, plan, nuisance and membership.

Let:

    v=u_0 XOR u_1

The delayed observation satisfies:

    P(Y2=1 | R,a)=3/4  if v=R
    P(Y2=1 | R,a)=1/4  if v≠R

Thus:

    plans 00 and 11 have v=0
    plans 01 and 10 have v=1

The exact table is:

    plan  parity   P(Y2=1|R=0)   P(Y2=1|R=1)
    00      0           3/4             1/4
    01      1           1/4             3/4
    10      1           1/4             3/4
    11      0           3/4             1/4

This matches the artifact. 

## 3.2 Immediate projection

For every R and plan:

    P(Y1=1 | R,a)=1/2

Therefore the two regime distributions of Y1 are identical:

    one_step_TV=0

The coarsest decoder quotient based only on Y1 has:

    K_1=1

The immediate projection is correctly non-identifying.


## 3.3 Complete joint kernels

When plan parity matches R:

    P(Y1,Y2)
      = (1/8,3/8,1/8,3/8)

in the order:

    (0,0),(0,1),(1,0),(1,1)

For the other regime:

    P(Y1,Y2)
      = (3/8,1/8,3/8,1/8)

The total variation is:

    TV
      = (1/2) [
          |1/8-3/8|
          +|3/8-1/8|
          +|1/8-3/8|
          +|3/8-1/8|
        ]
      = (1/2)(4 * 1/4)
      = 1/2

Hence:

    horizon2_TV=1/2

for every one of the four plans.

The artifact’s TV arithmetic is exact. 

## 3.4 Sequence Bayes floor

Because Y1 is fair and Y2 has the registered `3/4` versus `1/4` law:

    H(Y1)=ln2

and:

    H(Y2 | R,a)
      = H
      = -(3/4)ln(3/4) -(1/4)ln(1/4)
      = ln4 -(3/4)ln3

Conditional independence gives:

    L_2_star
      = H(Y1)+H(Y2|R,a)
      = ln2+H

This matches the registered criterion.


---

# 4. Update congruence

The registered quotient must admit one common online update:

    F(class(z_old),O_now) -> class(z_new)

The candidate uses:

    if C_n=1:
      F(z,O_n)=X_n

    otherwise:
      F(z,O_n)=z

Suppose two legal histories are in the same current regime class and receive
the same current legal observation.

- If both observations are non-cues, both preserve the same class.
- If both are cues with the same X, both install the same new class.
- If X differs, the observations are not the same input to F.

Therefore the next class depends only on the current quotient class and current
legal observation, not on a hidden representative, lifecycle key, earlier
history or script identity.

The update-congruence mismatch is exactly zero.


This establishes recursive updateability at the registered horizon-2 quotient.
It does not establish that the same two-class quotient is sufficient under
longer or natural evolving futures.

---

# 5. Sequential criterion and candidate

S4 defines:

    L_2(M)
      = mean over active histories and all four plans
          E[-ln p_M(Y1,Y2|z,a)]

    E_2(M)
      = L_2(M)-L_2_star

    q(M)
      = mean active-row learned-installation rate

    K_2(M)
      = horizon-2 decoder-kernel cardinality after quotienting

Models are ordered lexicographically:

    (E_2,q,K_2)

Strict propriety gives:

    E_2
      = mean KL(
          true horizon-2 kernel
          ||
          model kernel
        )
      >=0

Positive sequence excess therefore cannot be exchanged for fewer writes. This
correctly avoids the S2 rate–distortion failure.


The candidate:

- structurally installs `z=B`;
- writes `z←X_n=R_n` on both post-join cues;
- preserves z otherwise;
- ignores N;
- decodes the exact four-plan table from `(z,a)`.

It attains:

    E_2=0
    q=2/7
    K_2=2
    update_congruence_mismatch=0
    boundary_precision=1
    boundary_recall=1
    complete_lifetimes={2,3}

Six learned installations occur over the 21 active rows, so the write-rate
normalization is exactly `6/21=2/7`.


---

# 6. Minimum-transition theorem

## 6.1 Zero expected excess is an almost-sure condition

For a deterministic writer:

    E_2
      = mean_{f,a}
          KL(P_f^a || p_eta(.|z(f),a))

For a stochastic writer, the expectation additionally ranges over realized
writer randomness and installed state:

    E_2
      = mean_{f,a}
          E_z[
            KL(P_f^a || p_eta(.|z,a))
          ]

Every term is nonnegative.

Therefore:

    E_2=0

forces zero KL at every positive-probability legal history, plan and realized
installed state. A stochastic mixture cannot average incorrect component
predictions into an exact result.

The artifact applies this almost-sure interpretation correctly.


## 6.2 Every sufficient state distinguishes the current regime

For every plan, the two regime sequence kernels differ by total variation
`1/2`.

An exactly sufficient installed class must therefore distinguish R=0 from R=1,
up to an invertible relabeling.

At structural join, z starts in the class for B.

## 6.3 Both post-join changes require same-row installation

For script `23`, the regime changes at active ages:

    2 and 5

For script `32`, it changes at:

    3 and 5

Immediately before each change row, the installed decoder class denotes the old
regime.

The current cue is the first legal observation of the new regime. The decoder
does not receive that cue directly. Exact prediction on the same row therefore
requires the writer to move to the other decoder class before branch decoding.

Each lifecycle consequently requires at least two learned installations:

    q >= 2/7

## 6.4 Equality schedule

The candidate attains `q=2/7`.

If another sufficient model made any additional installation with positive
probability, both mandatory change-row installations would still be required,
so its rate would exceed `2/7`.

Therefore equality is possible only when learned installations occur at the two
actual post-join changes, up to:

- null-probability events;
- raw latent relabeling;
- decoder-equivalent internal subdivisions.

## 6.5 Quotient cardinality

Every sufficient model needs at least the two distinct regime sequence kernels.

Any extra latent values producing the same complete four-plan kernel are
decoder-equivalent and merge. N changes no sequence kernel and cannot survive
as an additional quotient class.

Hence every minimum-write sufficient model has:

    K_2=2

The theorem is valid at its exact scope.


It establishes uniqueness of the decoder-class transition schedule, not neural
parameters, raw coordinates or an optimization trajectory.

---

# 7. Complete null audit

## 7.1 One-step controlled quotient

Using only Y1 yields one fair kernel:

    K_1=1

A one-class model cannot reproduce both delayed regime kernels, so its
horizon-2 excess is strictly positive.

This is a valid constructive counterexample to one-step controlled sufficiency.


## 7.2 Never-write

Never-write preserves:

    z=B

Current regime equals z on:

    9/14

of source rows and differs on:

    5/14

When plan parity equals z:

    P(Y2=1|z,a)
      = (9/14)(3/4)+(5/14)(1/4)
      = 4/7

For opposite parity:

    P(Y2=1|z,a)=3/7

The fair first observation adds `ln2`, so:

    L_2_NW
      = ln2+h(4/7)

and:

    E_2_NW
      = h(4/7)-H
      >0

Never-write loses in the first lexicographic coordinate and cannot trade its
zero write count against prediction error.


## 7.3 Always-write

Always-write can remain sufficient but installs on every post-join row:

    q=6/7

It loses in the second coordinate.

## 7.4 All 64 deterministic fixed-age masks

Every deterministic fixed-age mask is a subset of:

    {1,2,3,4,5,6}

A sufficient mask must contain:

    age 2 for script 23
    age 3 for script 32
    age 5 for both

Thus it must contain:

    {2,3,5}

There are:

    2^(6-3)=8

such supersets.

Every sufficient fixed-age mask consequently has at least three scheduled
installations:

    q>=3/7

The remaining 56 masks miss at least one required change and have positive
sequence excess.

This partitions all 64 masks exactly.


## 7.5 Periodic schedules

Every finite-horizon deterministic period/phase schedule induces one of the 64
fixed-age masks. It is therefore either insufficient or has `q>=3/7`.

No periodic schedule matches the adaptive two-cue candidate.

## 7.6 All eight current-membership mappings

The current active-row membership categories are:

    ordinary
    rejoin
    terminal leave

There are eight deterministic write/no-write mappings over these categories.

If ordinary rows do not write, the rule misses one or more internal regime
changes.

If ordinary rows write, it installs on too many rows and exceeds `2/7`.

Membership events are independent of B and S and cannot identify the exact
source-adaptive boundary schedule.


## 7.7 Post-hoc segmentation

A future branch outcome cannot change a state that had to be installed before
the current sequence prediction.

Giving Y1 or Y2 to the writer before installation violates online order.
Restricting the segmenter to the legal filtration returns it to the
minimum-transition theorem.

## 7.8 Stochastic writers

Zero expected sequence excess forces exact sequence prediction almost surely.

Each positive-probability stochastic realization therefore crosses decoder
class at both actual regime changes. Mixing cannot average away the two
mandatory installations, and equality permits no additional positive-probability
write.


## 7.9 Nuisance-only state

N is independent of every horizon-2 kernel.

A nuisance-only state cannot distinguish regimes. Redundant N subdivisions in a
sufficient model have identical sequence kernels and merge.

## 7.10 Identical-kernel negative source

If both regimes are assigned identical complete horizon-2 kernels:

    K_2=1
    q=0

is sufficient, and no nontrivial lifetime is produced.

The criterion therefore does not manufacture a lifetime from cue frequency,
membership or nuisance alone.


No missing registered null is identified.

---

# 8. Leak and adaptive-plan audit

## 8.1 Natural plan as memory

A length-two plan selected by a policy with access to h can encode hidden regime
information.

Such a plan:

- lacks externally complete support;
- is selected by temporal state;
- can act as a memory label.

It is correctly rejected rather than treated as controlled evidence.

## 8.2 Future-outcome writer leak

Giving Y1 or Y2 to the writer before the current installation uses future
branch information and invalidates the online lifetime claim.

The S4 admissible path does not do this.

## 8.3 Adaptive second action

Let u0 be externally indexed and let:

    u1=g(u0,Y1)

for any deterministic function g.

Y1 is fair and independent of R, so the induced plan weights are
regime-independent.

Conditional on each realized Y1, the selected parity is fixed. Across the two
regimes, Y2 remains Bernoulli `3/4` versus `1/4`.

For each Y1 value, the conditional TV is `1/2`. Averaging over the two fair Y1
values leaves:

    adaptive_horizon2_TV=1/2

The adaptive rule neither creates information in the immediate projection nor
removes the registered horizon-2 distinction.


The adaptive-plan argument is correct.

---

# 9. Constructive controls and invariances

Audit-only utility is:

    U=1[A=R]

It enters no writer input, state target, sequential loss, decoder or boundary
decision.

Constructive C-ALSCPS:

    A=z

Constructive G8:

    store R in lifecycle h
    A=h

Both attain:

    U_star=1

G8 therefore remains a complete simpler explanation and blocks any
representational-necessity claim.


The actual repository comparator is a direct recurrent open-roster policy whose
skill/event hierarchy is absent, whose hidden state is lifecycle-owned and whose
padding capacity is not a model input. 

Its lifecycle implementation distinguishes temporary absence, rejoin, genuine
join and terminal leave; its focused contract checks freeze hidden state during
absence and initialize genuine joins from fresh zero hidden state.



Focused tests retain constructive utility, inactive-capacity invariance,
lifecycle ownership, replay and fail-closed analysis semantics.




S4’s registered invariances are valid:

- lifecycle-key relabeling;
- active-member permutation;
- inactive padding;
- temporary-absence insertion;
- arbitrary permutation of four plan labels with corresponding kernel columns;
- latent-state relabeling;
- nuisance-bit relabeling.

Every mismatch is zero.


---

# 10. S4 first-match terminal

The frozen order is:

    1. INVALID_ALSCPS_DERIVATION_CONTRACT
    2. ACTION_PLAN_OR_FUTURE_INFORMATION_LEAK
    3. NO_HORIZON_SEPARATING_CONTROLLED_SOURCE
    4. NO_UNIQUE_MINIMAL_FUTURE_CLOSED_LIFETIME
    5. PASS_ALSCPS_FUTURE_CLOSED_DERIVATION

## 10.1 Invalid contract

Not selected.

The source, target table, entropy, online order, membership semantics, null
coverage and invariances are valid.

## 10.2 Plan or future-information leak

Not selected.

All plans have complete external memory-free support and are absent from the
writer. Natural-plan and future-outcome paths are explicitly excluded.

## 10.3 No horizon-separating source

Not selected.

The immediate projection has:

    TV=0
    K_1=1

Every full plan has:

    horizon2_TV=1/2

and the candidate attains:

    L_2_star=ln2+H

## 10.4 No unique minimal future-closed lifetime

Not selected.

The quotient is update-congruent. Every sufficient model has `q>=2/7`.
Equality installs only at actual changes. Equivalent nuisance states merge and
every registered null is worse.

## 10.5 PASS

Selected.

The correct first-match terminal is:

    PASS_ALSCPS_FUTURE_CLOSED_DERIVATION

The artifact records the exact terminal tuple, iteration count and consequence
ceiling. 

Iteration 4 is validly consumed. Six iterations remain.

---

# 11. Smallest supported and refuted propositions

## 11.1 Smallest supported proposition

    P_S4_HORIZON2_STATE:

    On the exact S4 source, the coarsest update-congruent quotient sufficient
    for all externally indexed horizon-2 sequence kernels has two classes.
    Every sufficient online model has q>=2/7; equality installs only at the two
    actual post-join changes and yields complete active-step lifetimes {2,3}.

## 11.2 Delayed-information proposition

    P_DELAYED_CONTROLLED_SEPARATION:

    Histories with identical immediate controlled observation laws can have
    different delayed controlled sequence laws.

S4’s fair Y1 projection has zero separation while the complete pair has
separation `1/2`.

## 11.3 Update-congruence proposition

    P_UPDATE_CONGRUENCE:

    Predictive equivalence alone is not a sufficient scientific definition of a
    persistent lifecycle state. The quotient must admit one common update from
    current class and current legal observation.

The S4 candidate satisfies this criterion exactly.

## 11.4 Smallest refuted proposition

    P_ONE_STEP_COMPLETE:

    Equality of immediate controlled observation kernels is sufficient for
    equality of all registered delayed controlled futures.

This proposition is refuted by the S4 source.

## 11.5 Exact claim ceiling

S4 does not support:

- arbitrary-horizon controlled closure;
- sufficiency for natural evolving environment futures;
- learned-state recovery;
- a learned skill;
- recurrence insufficiency;
- optimization or sample-efficiency benefit;
- primitive-policy mediation by an implemented state;
- natural-policy value;
- held-out robustness;
- transfer;
- complementary coordination;
- final-algorithm integration.

The current conjecture, portfolio and lemma records preserve this narrow scope.




---

# 12. Fresh plural CDC pass

## 12.1 Candidate A — C-ALBPF: behavioral state / predictive-phase factorization

### Conjecture

A useful individual skill lifetime should be owned by the current
action-relevant behavioral state, not by every update of a broader predictive
state.

A separate lifecycle-local predictive-phase state may update when uncertainty
about transition timing changes, without resetting the behavioral skill.

### Mechanism-to-capability edge

Factor the agent-local temporal object into:

    b_i,t:
      coarsest current controlled-behavior kernel class

    p_i,t:
      task-blind predictive phase for generic state-transition dynamics

The primitive policy may consume b. The phase p may support transition
prediction or later boundary estimation, but a p-only information update does
not terminate the current b lifetime.

This could eventually provide:

- a stable skill identity;
- a separate transition-timing model;
- variable active-step skill lifetime;
- protection against predictive-state over-segmentation.

### Retains

- anonymous lifecycle ownership;
- active-step clock;
- S3/S4 controlled-kernel semantics;
- environment-agnostic prediction;
- survivor continuity;
- G8 as complete comparator.

### Deletes or replaces

- interpreting every monolithic predictive-state class change as a skill
  boundary.

### Minimally adds

- an explicit distinction between current behavioral class and predictive
  transition phase.

### Strongest simpler explanation

G8 recurrence can encode both behavioral content and transition phase without an
explicit factorization. Even a valid factorization would establish no
optimization, mediation or transport advantage.

### Intervention consequence

Holding b fixed while changing only p may change predicted transition timing but
must not change the current primitive-action kernel.

Changing b while holding admissible context fixed must change the current
controlled-action consequence.

### Natural consequence

p may update on an informative non-cue without resetting the current b
lifetime.

### Held-out consequence

Not established. A later learned comparison would need new duration processes,
a mechanism-matched factor-masked arm and exact G8.

### Plausibility-raising observation

A positive-probability online row where:

    current_behavior_TV=0
    transition_prediction_TV>0

and the broader monolithic predictive class must update.

### Plausibility-lowering observation

The generic transition law never changes unless the current controlled behavior
class changes, or no online behavior/phase separation exists.

### Disposition

Retain as a live correction candidate. Select the shortest exact confound
derivation before any factorized implementation.

## 12.2 Candidate B — monolithic full predictive state

### Conjecture

One state could summarize both current controlled behavior and future transition
dynamics, with its class changes defining lifetime.

### Strongest contradiction

A predictive state can change because uncertainty about transition phase is
resolved even while current action consequences remain identical.

Such an information-only update would split one behavioral skill into multiple
predictive-state segments.

### Disposition

Do not implement. Subject it to S5.

## 12.3 Candidate C — randomized-support controlled-state learner

### Conjecture

A task-blind randomized behavior process with known complete action support
could estimate the accepted controlled kernels without same-history oracle
enumeration.

### Strongest contradiction

Finite natural data may lack history-level support. An action selected by h can
be a memory label. A learner may recover cue shortcuts rather than the intended
state.

### Reactivation condition

Resolve whether the scientific lifetime is attached to a monolithic predictive
state or a behavioral projection first.

### Disposition

Park.

## 12.4 Candidate D — controlled-state primitive-policy link

### Conjecture

A learned primitive policy consuming a detached controlled state may improve
optimization, mediation or held-out transport over a matched state-masked arm.

### Strongest simpler explanation

G8 recurrence contains the same useful information. Extra capacity, direct cue
access or unequal optimizer exposure could explain an apparent gain.

### Reactivation condition

First obtain a learned state under an accepted lifetime semantics.

### Disposition

Park.

## 12.5 C-JRDM

Remain parked.

Jointly charging h and z still lacks representation-invariant channel
decomposition.

Reactivation requires:

    an invariant joint codelength or information theorem

## 12.6 C-ALH

Remain parked.

A per-step categorical hazard remains vulnerable to `k=1` renaming and the
R43–R45 closure.

Reactivation requires:

    an independently identified need for task-directed termination after a
    valid non-reward state and lifetime object exist

## 12.7 C-ATS

Remain parked.

Continuous leakage still lacks a threshold-free segment and can be absorbed into
recurrence.

Reactivation requires:

    a threshold-invariant survival or causal-persistence estimand

## 12.8 C-SEPM

Remain parked.

Population memory still changes coordination and individual lifetime
simultaneously; TEAM_REC and ordinary set encoders remain simpler explanations.

Reactivation requires:

    an identified complementary-allocation source on which lifecycle recurrence
    and TEAM_REC are insufficient

## 12.9 G8 and ordinary recurrence

G8 remains:

- the accepted usable dynamic-roster base;
- the complete external-policy comparator;
- the strongest simpler explanation;
- an equally capable constructive controller on S4.

It is not a universal admission gate.

Any later explicit-state claim must concern optimization, causal use, sample
efficiency, robustness, transport or complexity—not finite representational
impossibility.

The project principles require intervention-sensitive sequential behavior,
natural use, external value, held-out transport and simpler-explanation
resistance before integration. 



---

# 13. Selected iteration-5 action

    action_id=S5_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND_DERIVATION
    primary_candidate=C_ALBPF
    tested_null=MONOLITHIC_PREDICTIVE_STATE_DEFINES_SKILL_LIFETIME
    action_class=accepted_evidence_reanalysis_plus_exact_counterexample
    conclusion_bearing_iteration=5
    code_required=false
    compute_required=false
    prototype_required=false
    experiment_required=false
    Monitor_required=false

## 13.1 Exact question

On the immutable S1–S4 lifecycle source, does augmenting the controlled state
with a generic next-active-observation prediction force a predictive-state
class change inside a segment whose current controlled behavior is unchanged?

Equivalently:

    Can one monolithic predictive-state transition serve simultaneously as:
      a current behavioral skill boundary, and
      a predictive phase update?

Or must behavioral state and predictive phase be represented as separate
scientific objects?

## 13.2 Why this is the cheapest decisive action

S4 already establishes an exact horizon-2 state under a branch law determined
only by the current regime.

Before implementing that state, the next cheapest question is whether adding
ordinary transition prediction changes its lifetime semantics.

A bounded implementation now would confound:

- state-definition error;
- predictive-phase over-segmentation;
- estimator error;
- optimization failure;
- architecture leakage;
- implementation defects.

The S5 witness can resolve the semantic issue with exact conditional
probabilities and no code.

This follows the project rule to prefer a concrete derivation or counterexample
before implementation while the scientific object remains ambiguous.




---

# 14. Frozen S5 scientific contract

## 14.1 Claim ceiling

S5 can establish only whether predictive phase and current behavioral lifetime
are aligned or confounded on the exact finite source.

A PASS for the confound may support:

    monolithic predictive-state changes are not generally valid skill
    boundaries

It cannot establish:

- a learned factorization;
- optimal architecture;
- learned transition timing;
- primitive-policy benefit;
- recurrence insufficiency;
- natural value;
- held-out transport;
- final integration.

## 14.2 Immutable lifecycle source

Retain exactly:

- uniform independent B;
- uniform independent scripts `23` and `32`;
- the seven active-row regime sequences;
- cue rows;
- 21 active rows across three lifecycle epochs;
- temporary leave/rejoin;
- genuine join;
- terminal leave;
- structural join;
- nuisance N;
- active-step clock;
- all registered invariances.

No script probability, observation law or membership schedule may change.

## 14.3 Existing current-behavior object

Retain the S3 current controlled query:

    u ∈ {0,1}

with complete external support at each legal history and target law:

    P(Y=1 | R,u)=3/4 if u=R
    P(Y=1 | R,u)=1/4 otherwise

Define the current behavioral quotient:

    b(f)
      = equivalence class of the full current controlled vector
        (K_f^0,K_f^1)

On the frozen source, b is the current regime class, up to `0↔1` relabeling.

A behavioral lifetime is the active-step run between changes in b.

## 14.4 New task-blind transition target

For the current lifecycle at active age n, define:

    D_n = C_{n+1}

where `C_{n+1}` is the cue indicator in the next active lifecycle row.

If terminal leave or the finite horizon occurs before another active row, use an
explicit terminal symbol rather than zero-filling a cue.

D is:

- a future generic observation component;
- not an external reward;
- not a task-success field;
- not visible to the writer before current state installation;
- not a duration label supplied to the model;
- evaluated only after the current state is installed.

S5’s decisive rows occur before terminal censoring, so terminal conventions
cannot affect the witness.

## 14.5 Predictive-phase object

Define the predictive-phase law:

    Q_f(d)=P(D_n=d | legal history f)

Two histories are phase-equivalent only if their next-active cue laws agree.

A monolithic predictive state sufficient for both objects must reproduce:

    current controlled vector (K_f^0,K_f^1)
    next-active transition law Q_f

The phase decoder receives only the installed predictive state. It does not
receive current C, age, clock, script, membership history or future observation
as a bypass.

## 14.6 Writer filtration

Retain the S4 writer filtration:

    current O_n=(C_n,X_n,N_n)
    previous state
    fresh registered writer randomness

Prohibit:

- h;
- active age or index;
- local/global clock;
- `t mod k`;
- observation history outside the declared state;
- natural action;
- query history;
- active-set or membership history;
- persistent auxiliary memory;
- lifecycle identity;
- script S;
- external reward;
- task, role, goal, success or progress;
- D_n;
- any future cue or outcome;
- oracle boundary.

The no-cue observation at age 2 is current legal information, not future
information.

## 14.7 Decisive exact histories

Consider a lifecycle after its active-age-1 row.

Both scripts have produced the same legal cue history:

    C_0=1
    C_1=0

Therefore the posterior remains:

    P(S=23 | history)=1/2
    P(S=32 | history)=1/2

The next active cue is:

    C_2=1 for script 23
    C_2=0 for script 32

Hence:

    P(D_1=1 | age-1 history)=1/2

Now condition on the positive-probability script-32 age-2 no-cue history:

    S=32
    C_2=0
    R_1=B
    R_2=B

The no-cue observation identifies script 32. Its next active row is age 3, which
is a cue:

    C_3=1

Therefore:

    P(D_2=1 | S=32 age-2 history)=1

## 14.8 Exact behavior/phase contrast

At age 1 and at the script-32 age-2 row:

    current regime = B

Thus the full current controlled behavior vectors are identical:

    behavior_TV=0

But their next-cue laws are Bernoulli `1/2` and Bernoulli `1`:

    phase_TV
      = |1-1/2|
      = 1/2

The decisive exact signature is:

    current_behavior_TV=0
    predictive_phase_TV=1/2

The witness has positive source probability:

    P(S=32)=1/2

and is independent of B and nuisance N.

## 14.9 Consequence for a monolithic predictive-state lifetime

A state exactly sufficient for both current controlled behavior and Q must
assign the age-1 and script-32 age-2 histories to different predictive classes,
because their Q laws differ.

Yet b does not change between those rows.

Therefore a monolithic predictive-state transition occurs inside the first
script-32 behavioral segment:

    behavior segment:
      R=B on active ages 0,1,2
      length=3

    information-only predictive transition:
      age 2 no-cue
      current behavior unchanged

This is the precise state-lifetime confound under test.

S5 need not assume that every predictive state changes at every row. One
positive-probability nonboundary transition is sufficient to refute universal
alignment.

## 14.10 Constructive factor projection

As a diagnostic correction, construct two projections:

    b:
      current controlled-behavior class

    p:
      predictive phase needed for Q

At the decisive script-32 age-2 row:

    b_before=b_after=B
    p_before=script-uncertain
    p_after=script-32-next-cue-certain

The update is online because the current no-cue observation distinguishes the
two script possibilities.

The behavioral lifetime is defined only on changes of b. A p-only update does
not reset it.

S5 does not need to prove that this factorization is the unique or best learned
architecture. It must only prove that the two causal roles are distinct on the
registered source.

## 14.11 Comparators and nulls

### BEHAVIOR_ONLY

Uses b=R and preserves the registered skill lifetime.

Required result:

    exact current controlled sufficiency
    failure to reproduce both Q laws at the decisive histories

### MONOLITHIC_BEHAVIOR_PLUS_PHASE

Uses one quotient sufficient for both controlled behavior and Q.

Required result:

    exact prediction
    extra positive-probability class transition at script-32 age 2

### PHASE_AS_SKILL

Defines every phase-state transition as a skill boundary.

Required result:

    false additional boundary inside a constant behavior segment

### DIRECT_CURRENT_C_PHASE_DECODER

Gives current C directly to the phase decoder.

Classification:

    ownership bypass
    not admissible predictive-state evidence

### AGE_OR_CLOCK_PHASE

Uses active age, global time or `t mod k`.

Classification:

    forbidden clock shortcut

### SCRIPT_ORACLE

Supplies S directly.

Classification:

    forbidden hidden-source label

### FUTURE_CUE_WRITER

Supplies D_n before installation.

Classification:

    future-information leak

### MEMBERSHIP_PHASE

Uses membership history to infer phase.

Required result:

    invalid or insufficient because membership is independent of S

### NUISANCE_PHASE

Uses N.

Required result:

    no change in controlled behavior or Q
    decoder-equivalent nuisance subdivisions merge

### POST_HOC_BOUNDARY

Uses completed trajectory or future cues.

Classification:

    invalid online evidence

### G8

Remains the complete external-policy comparator and may store every relevant
quantity in recurrence. No representational-necessity claim is permitted.

## 14.12 Scientific estimands

Define:

    TV_behavior
      = TV between the complete current controlled vectors at the decisive
        age-1 and script-32 age-2 histories

    TV_phase
      = TV between their Bernoulli next-cue laws

    I_extra
      = 1[
          TV_behavior=0
          and TV_phase>0
        ]

    q_behavior
      = learned transition rate of the current-behavior quotient

    q_monolithic
      = transition rate of a quotient sufficient for both behavior and phase

    phase_only_boundary_count
      = count of positive-probability monolithic transitions occurring when b
        is unchanged

The conclusion-bearing exact values are:

    TV_behavior=0
    TV_phase=1/2
    I_extra=1
    phase_only_boundary_count>=1

No statistical interval or threshold is used.

## 14.13 Invariances

Require zero mismatch under:

- lifecycle-key relabeling;
- active-member permutation;
- inactive padding;
- temporary-absence insertion;
- B/behavior-label relabeling with controlled-kernel relabeling;
- nuisance-bit relabeling;
- equivalent renaming of phase classes.

The decisive history and probabilities must not depend on physical wall time,
padding position or identity.

## 14.14 Exact proof obligations

A valid S5 derivation must establish every item below.

1. The S1–S4 source and membership contract are unchanged.

2. D is the next active observation cue, not the next global-time row.

3. Temporary absence cannot create or erase the witness.

4. The age-1 histories under scripts 23 and 32 are observationally identical
   under the writer filtration.

5. Their script posterior is exactly one-half/one-half.

6. The age-1 next-cue probability is exactly:

       1/2

7. The script-32 age-2 no-cue observation is legal current information.

8. That observation identifies script 32 under the finite source.

9. Its next-cue probability is exactly:

       1

10. Current regime remains B from age 1 to script-32 age 2.

11. The complete current controlled behavior vectors are therefore identical:

       TV_behavior=0

12. The phase laws differ:

       TV_phase=1/2

13. Any quotient sufficient for both objects must change class at the
    script-32 age-2 row.

14. The current behavioral quotient does not change there.

15. The transition has positive probability.

16. The transition occurs inside the first complete script-32 behavior segment
    of active-step length three.

17. BEHAVIOR_ONLY fails Q sufficiency.

18. PHASE_AS_SKILL produces an extra nonbehavioral boundary.

19. The two-projection diagnostic updates p without resetting b.

20. Direct-C, clock, script, future-cue, membership-history and post-hoc
    shortcuts are rejected.

21. Nuisance subdivisions merge.

22. G8 remains a valid complete recurrent comparator.

23. Every registered invariance mismatch is zero.

24. No external reward, task field, identity, role, goal, success, progress,
    natural-action memory or future information enters the admissible state
    update.

There is no statistical, mixed or underpowered branch.

## 14.15 First-match terminals

Apply this exact order.

1. `INVALID_PHASE_LIFETIME_DERIVATION_CONTRACT`

   Any source mutation, incorrect conditional probability, wrong active-clock
   semantics, incomplete null, invalid membership treatment, failed invariance
   or forbidden task/reward input.

2. `FUTURE_CLOCK_OR_SCRIPT_INFORMATION_LEAK`

   The admissible state receives D, S, age, time, membership history, future cue
   or another temporal shortcut.

3. `NO_PREDICTIVE_PHASE_WITHIN_BEHAVIOR_SEGMENT`

   The exact source is valid, but `TV_phase=0`, current behavior changes with the
   phase law, or no positive-probability information-only transition exists.

4. `NO_VALID_BEHAVIOR_PHASE_PROJECTION`

   A predictive-phase transition exists, but no online projection can preserve
   the current behavior class while updating phase under the legal observation.

5. `PASS_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND`

   The exact `0` versus `1/2` contrast, extra monolithic transition, online
   behavior/phase projection, nulls and invariances all pass.

## 14.16 Required evidence artifact

The sole conclusion-bearing S5 artifact is:

    docs/research/cdc/EVIDENCE_NOTES/
    20260724_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND_S5.md

It must contain:

- exact source and active-clock table;
- age-1 and script-32 age-2 legal histories;
- posterior calculation;
- next-cue laws;
- current controlled behavior vectors;
- exact TV arithmetic;
- monolithic-state consequence;
- online behavior/phase projection;
- all null and leak cases;
- G8 constructive comparator;
- invariance proofs;
- smallest supported and refuted propositions;
- first-match terminal;
- no engineering plan, code or resource schedule.

## 14.17 Stop and iteration rule

Stop on the first valid S5 terminal.

A valid PASS or negative consumes iteration 5:

    consumed=5
    remaining=5

An invalid derivation consumes no iteration and permits at most one bounded
correction of transcription, arithmetic or proof checking under the identical:

- source;
- next-cue target;
- filtration;
- histories;
- null family;
- estimands;
- obligations;
- terminal order.

Changing any scientific object above requires another Pro decision.

A second invalid realization is a blocker.

After a valid S5 terminal, return the exact result to this same registered Pro
conversation before selecting iteration 6.

---

# 15. Why implementation is not scheduled yet

S3 and S4 identify controlled state objects, but neither determines whether
predictive-state updates and skill boundaries coincide after generic transition
prediction is added.

Implementing one monolithic writer now could silently produce:

- information-only state changes;
- extra apparent skill boundaries;
- lifetime fragmentation driven by phase estimation;
- a false positive for variable learned lifetime.

Implementing a factorized writer now would also be premature because the need
for two factors has not yet been established under a frozen exact source.

S5 directly separates those possibilities without code and is therefore cheaper
and more reversible than:

- randomized-support estimation;
- learned writer implementation;
- policy-link training;
- joint h/z information coding;
- explicit hazards;
- population memory.

---

# 16. Durable repository deltas after factual reconciliation

## 16.1 Conjecture ledger

Update `C-ALSCPS`:

    status=accepted_exact_S4_derivation_PASS
    terminal=PASS_ALSCPS_FUTURE_CLOSED_DERIVATION
    scope=horizon_2_only
    implementation_authorized=false
    compute_authorized=false

Retain:

    one_step_TV=0
    horizon2_TV=1/2
    minimum_q=2/7
    quotient_K_2=2
    update_congruence=true
    complete_lifetimes={2,3}

Add unresolved boundary:

    predictive phase updates may occur inside a constant current-behavior
    segment when generic transition dynamics are included

Add:

### `C-ALBPF — Agent-Local Behavioral / Predictive-Phase Factorization`

Status:

    live correction candidate
    selected only for S5 exact confound derivation
    no implementation or compute selected

Claim:

    current action-relevant state and predictive transition phase may require
    separate lifecycle projections so that an information-only phase update
    does not reset the behavioral skill lifetime

Strongest simpler explanation:

    G8 recurrence stores both objects without explicit factorization

Intervention consequence:

    changing p alone affects predicted transition law but not the current
    controlled action kernel; changing b affects current behavior

Natural consequence:

    p may update on an informative no-cue while b remains persistent

Held-out consequence:

    not established

Keep randomized-support learning and primitive-policy linkage parked.

Retain C-JRDM, C-ALH, C-ATS and C-SEPM under their existing reactivation
conditions.

## 16.2 Lemma ledger

Retain and explicitly scope:

### `L-S4-VALID-PASS`

The exact S4 derivation identifies a minimum-write, update-congruent horizon-2
controlled state.

Does not imply:

    arbitrary-horizon closure or learned skill lifetime

Retain:

### `L-SEQUENTIAL-CLOSURE-REQUIRES-FUTURE-KERNELS`

Immediate controlled equivalence need not imply delayed controlled equivalence.

Retain:

### `L-UPDATE-CONGRUENCE`

A predictive quotient must admit one common online update to count as a
persistent lifecycle state.

Add only as an S5 pending proposition:

### `L-PREDICTIVE-PHASE-NOT-SKILL-BOUNDARY`

A predictive-state update caused only by new transition-phase information need
not be a current behavioral skill boundary.

Do not promote it to a retained lemma until a valid S5 terminal.

## 16.3 Counterexample ledger

Retain the accepted S4 counterexamples:

- `CE-ONE-STEP-CONTROLLED-MYOPIA`;
- `CE-NATURAL-PLAN-AS-MEMORY`;
- `CE-FUTURE-OUTCOME-WRITER-LEAK`;
- `CE-NONCONGRUENT-PREDICTIVE-PARTITION`.

Add as S5 registered candidates:

### `CE-NO-CUE-INFORMATIONAL-STATE-UPDATE`

A legally observed absence of a cue can resolve hidden transition phase and
change the predictive law while leaving current controlled behavior unchanged.

### `CE-MONOLITHIC-PREDICTIVE-STATE-OVERSEGMENTATION`

Defining every predictive-state class change as a skill boundary can split one
constant behavioral segment into multiple apparent lifetimes.

### `CE-PHASE-AS-SKILL`

A state useful for predicting when a future transition occurs is not
automatically the current executable skill state.

Promote these only after S5 proves them.

## 16.4 Idea portfolio

Set:

    C-ALPSW:
      closed exact S1 formulation

    C-ALPSC:
      closed exact S2 formulation and interval

    C-ALCPS:
      accepted exact S3 one-step derivation
      implementation unselected

    C-ALSCPS:
      accepted exact S4 horizon-2 derivation
      implementation unselected

    C-ALBPF:
      live and selected for S5 confound derivation

    randomized-support controlled-state learner:
      parked pending lifetime semantics

    controlled-state primitive-policy link:
      parked pending learned-state semantics

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

    S5_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND_DERIVATION

Authorization:

    derivation selected
    code not selected
    compute not selected
    iterations 6_to_10 unselected

## 16.5 Evidence-note delta

Add:

    docs/research/cdc/EVIDENCE_NOTES/
    20260724_ALSCPS_S4_RESULT_AND_PHASE_CONFOUND_S5_DIRECTION.md

Record:

- S4 validity audit;
- independent joint-kernel, TV, entropy and never-write calculations;
- accepted first-match PASS;
- exact supported/refuted propositions;
- horizon-2 scope ceiling;
- plural portfolio;
- C-ALBPF conjecture;
- complete S5 contract;
- iteration accounting;
- evidence commit
  `e619437c78b856ea6f24929a359853ac6de30d4e`;
- this response provenance.

Do not add an experiment row to `ExpRecord.md`. S5 is a derivation.

## 16.6 Current-work delta

After factual reconciliation, set:

    last_completed_assignment_id=S4_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_DERIVATION
    active_assignment_id=S5_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND_DERIVATION
    next_boundary=COMPLETE_EXACT_S5_DERIVATION_THEN_RETURN_TO_PRO
    conclusion_bearing_iterations_consumed=4
    skill_lifetime_chain_iterations_remaining=6
    k_decoupling_current_result=PASS_ALSCPS_FUTURE_CLOSED_DERIVATION
    active_scientific_direction=C_ALBPF_PHASE_CONFOUND_TEST
    active_scientific_contract=20260724_ALSCPS_S4_RESULT_AND_PHASE_CONFOUND_S5_DIRECTION
    active_algorithm=PREFIX_NORMALIZED_OPEN_ROSTER_G8_imported_base
    s5_code_required=false
    s5_compute_required=false
    formal_compute_status=not_started

Only a valid S5 terminal changes the count to five consumed and five remaining.

---

# 17. Unchanged closure and quarantine scopes

S4 changes none of the imported R42–R48 boundaries.

- R42’s incumbent-conditioned categorical skill-logit residual remains closed.
- R43 remains scientifically quarantined because its fixed positive anchor
  failed.
- R44’s frozen-source global-`K=50` external-return renewal route remains closed.
- R45’s Alice–Bob natural-support Q/DR renewal route remains closed.
- R46’s exact HMRV estimator/read remains closed; oracle heterogeneity was not
  rejected.
- R47’s exact spectral view, basis and score remain closed.
- R48’s focal hidden reset at categorical SET remains closed.

S5 uses no categorical skill catalogue, reward-trained renewal, action-Q
heterogeneity estimator, spectral label, fixed global cycle or hidden reset. It
does not revive those routes.

---

# 18. What this ruling does not authorize

This response does not authorize:

- algorithm code;
- an implementation plan;
- a prototype;
- CPU or GPU execution;
- formal training, evaluation or analysis;
- Monitor assignment;
- resource allocation;
- an experiment row;
- modification of G8;
- implementation of C-ALCPS;
- implementation of C-ALSCPS;
- implementation of C-ALBPF;
- randomized controlled-state estimation;
- a primitive-policy link;
- natural policy actions as intervention queries;
- a beta objective;
- a joint h/z information penalty;
- an explicit categorical hazard;
- a continuous-timescale threshold;
- set-equivariant population memory;
- external reward in predictive supervision;
- task fields, identity, role, goal, success or progress inputs;
- an arbitrary-horizon claim;
- a learned-skill claim;
- an optimization, mediation, value, robustness or transport claim;
- revival of R42–R48;
- mutation of `aggressive`;
- selection of iterations 6–10;
- integration into the final HMASD algorithm.

A future S5 PASS would establish only that predictive phase and current
behavioral lifetime are distinct on the frozen finite source. It would still
require a new CDC decision before factorized-state derivation, estimator design,
implementation or behavioral testing.

External scientific review itself does not authorize code or compute.



---

# 19. 中文用户简报

S4 裁决有效：`PASS_ALSCPS_FUTURE_CLOSED_DERIVATION`，但 “future-closed” 只限
冻结的 horizon-2 查询族，不能外推到任意 horizon 或自然环境未来。

精确核验结果是：

    one_step_TV=0
    K_1=1
    horizon2_TV=1/2
    L_2_star=ln2+H
    candidate=(E_2,q,K_2)=(0,2/7,2)

任何 horizon-2 精确充分模型都必须在两个真实 post-join regime change 行切换
decoder class，所以 `q>=2/7`；达到等号时只能在这两个 cue 写入。quotient 可由同一
online update 递归更新，nuisance subdivision 会合并。never-write 的 excess 是
`h(4/7)-H>0`；全部 64 个 fixed-age mask、周期、membership、post-hoc、随机
writer、natural-plan leak 和 future-outcome leak 均不能达到相同 tuple。第 4 次
结论性迭代已消耗，剩余 6 次。

第 5 次唯一行动是无代码、无计算的
`S5_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND_DERIVATION`。它检验一个更接近实际
skill 语义的问题：当状态还要预测下一 active observation 的通用 transition phase
时，predictive-state change 是否会发生在 current controlled behavior 完全不变的
segment 内。

冻结 source 中，age 1 时两个脚本仍不可区分，下一 cue 概率是 `1/2`；script 32 在
age 2 观察到合法 no-cue 后，当前 regime 仍为 B，但下一 age 3 cue 的概率变成 `1`。
因此决定性签名是：

    current_behavior_TV=0
    predictive_phase_TV=1/2

若该推导成立，则 monolithic predictive state 必须在一个长度 3 的恒定行为 segment
内部额外切换，证明“predictive phase update”不能自动当作“skill lifetime boundary”。
随后才有理由研究 behavioral state 与 predictive phase 的因子化；本答复没有预选该
实现，也没有授权任何运行。

决定性否证条件是：上述两个合法 history 的 phase law 实际相同、当前 behavior 同时
发生改变、分离依赖 age/script/future cue 泄漏，或无法用合法 online projection 在
保持 behavior state 的同时更新 phase。任一有效终态都消耗第 5 次迭代；迭代 6–10
仍未选择。
