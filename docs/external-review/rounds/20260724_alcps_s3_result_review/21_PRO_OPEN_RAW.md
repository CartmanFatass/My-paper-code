
# GPT-5.6 Pro CDC Ruling — ALCPS S3 Controlled-State Result

## Executive decision

S3 is accepted as a valid conclusion-bearing positive derivation.

    accepted_terminal=PASS_ALCPS_CONTROLLED_STATE_DERIVATION
    S3_contract_valid=true
    terminal_affecting_defects=none
    S3_algorithm_code_executed=false
    S3_compute_executed=false
    conclusion_bearing_iterations_consumed=3
    iterations_remaining=7

The smallest accepted claim is:

    On the exact finite S3 source, the coarsest decoder-kernel quotient that is
    exactly sufficient for every externally indexed primitive-action query has
    two states. Among all exactly sufficient online models, the minimum learned
    installation rate is 2/7; equality installs only at the two actual post-join
    regime-change cues. The resulting complete active-step lifetimes are {2,3}.

The PASS does not establish:

- a learned skill;
- superiority or necessity relative to G8 or ordinary recurrence;
- learnability from a natural action stream;
- optimization or sample-efficiency benefit;
- primitive-policy causal mediation;
- natural-policy value;
- robustness;
- held-out transport;
- sequential sufficiency beyond the one-step controlled target;
- integration into the final HMASD algorithm.

Exactly one iteration-4 conclusion-bearing action is selected:

    S4_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_DERIVATION

The selected candidate is:

    C-ALSCPS
    Agent-Local Sequential Controlled Predictive State

S4 tests a concrete unresolved limitation of S3: equality of one-step controlled
kernels need not imply equality of delayed controlled futures. It replaces the
single controlled target with an exact two-microstep controlled observation
sequence, requires a recursively updateable quotient, and checks whether the
same minimum-write active-step lifetime remains identifiable.

S4 is another exact derivation and counterexample action. It requires no
algorithm code, prototype, CPU/GPU execution, experiment, Monitor or resource
allocation.

Iterations 5–10 remain unselected.

---

# 1. Evidence boundary

The pushed review stage is:

    1293f58b8960a60b8a2be2d9d25b8b441ae61948

The exact substantive evidence commit is:

    7cf10a01497176e4079c29c9f95fcb09fd60f660

The stage question and canonical manifest identify the exact paths and exclude
browser state, local files, untracked runtime evidence, code execution and later
working-tree changes. The S3 artifact is expressly an exact derivation rather
than runtime evidence. 


The principal load-bearing evidence paths used are:

    docs/project/CURRENT_WORK.md
    docs/project/ALGORITHM_PRINCIPLES.md
    docs/project/ExpRecord.md
    docs/external-review/OPEN_REVIEW_PRINCIPLES.md
    docs/research/cdc/CONJECTURES.md
    docs/research/cdc/IDEA_PORTFOLIO.md
    docs/research/cdc/LEMMA_COUNTEREXAMPLE_LEDGER.md
    docs/research/cdc/EVIDENCE_NOTES/
      20260724_ALPSC_S2_RESULT_AND_ALCPS_S3_DIRECTION.md
    docs/research/cdc/EVIDENCE_NOTES/
      20260724_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_S3.md
    docs/report/DECOUPLED_SKILL_LIFETIME_ITERATION_3.md
    docs/external-review/rounds/20260724_alpsc_s2_result_review/
      01_SHARED_SOURCE_MANIFEST.md
      20_PRO_OPEN_QUESTION.md
      21_PRO_OPEN_RAW.md
      30_EVIDENCE_RECONCILIATION.md
    docs/research/cdc/EVIDENCE_NOTES/
      20260724_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_S2.md
      20260723_ALPSW_IDENTIFIABILITY_DERIVATION_S1.md
    ha_ctse_process/open_roster_direct_mvp.py
    tests/ha_ctse_process_open_roster_direct_mvp_test.py

At the evidence boundary, repository state records S3 as a valid proof-only
PASS, with three iterations consumed, seven remaining and no iteration-4
action, code or compute yet selected. 


---

# 2. S3 contract-validity audit

## 2.1 Exact source binding

S3 preserves the S1/S2 lifecycle source:

    B ∈ {0,1}, uniform
    S ∈ {23,32}, uniform
    B and S independent within and across lifecycles

The active-step regime scripts are:

    S=23:
      R_0..R_6 = B,B,1-B,1-B,1-B,B,B
      cue rows = 0,2,5
      complete lifetimes = 2,3

    S=32:
      R_0..R_6 = B,B,B,1-B,1-B,B,B
      cue rows = 0,3,5
      complete lifetimes = 3,2

The three-lifecycle table still has exactly 21 active rows, one temporary
leave/rejoin, one genuine join and terminal leaves. Temporary absence creates no
active transition, does not advance active age and freezes lifecycle state and
RNG. Routing keys are provenance only. 

S3 adds:

    N_n ∈ {0,1}, iid Bernoulli(1/2)

with N independent of B, S, R, membership, query and target. The writer
observation is:

    O_n=(C_n,X_n,N_n)

This is a valid nuisance variable: it is legally observed but carries no
controlled-kernel information. 

No source mutation or identity leak is present.

## 2.2 Online order

The registered order is:

    1. establish active membership and current observation;
    2. structurally initialize a genuine join or apply the existing-row writer;
    3. expose the installed state to the controlled decoder;
    4. evaluate both external intervention queries;
    5. emit the controlled target;
    6. record audit-only boundaries and membership consequences.

The current cue is legally available before the writer update. The target and
future evidence are unavailable until after decoding. Structural join sets
`z=B` from the current cue without counting a learned installation. Terminal
leave closes and right-censors the final segment only after evidence is
recorded. 

This ordering is online and contains no future-data use.

## 2.3 Writer and decoder filtration

For an active existing lifecycle, the writer may use only:

    current O_n
    previous z_n-
    fresh registered writer randomness

It may not use:

- fast recurrent state `h`;
- active age or active index;
- local or global time;
- `t mod k`;
- observation history except through z;
- natural current or past actions;
- query history;
- active-set or membership history;
- auxiliary persistent state;
- identity or role;
- external reward;
- task, goal, success or progress fields;
- future observation;
- oracle regime or boundary.

The decoder is:

    p_eta(Y_n | z_n+,u)

and receives only installed z and the current external query u. It receives no
current observation, cue, nuisance, natural action, fast recurrence, clock,
history or membership information. 

The filtration matches the S2-selected contract. No prohibited information field
is present.

## 2.4 Complete external query support

At every legal active history, both values:

    u=0
    u=1

are evaluated.

The query is:

- externally indexed;
- independent of h, z, history, identity and natural policy;
- current-only;
- absent from writer input;
- supplied only to the current decoder.

This is not merely positivity in a natural policy. It is complete controlled
support at every legal history. 

`NATURAL_ACTION_QUERY` is correctly excluded: an action selected by a policy
with access to h can itself reveal R, and selective natural support cannot
substitute for the registered intervention table.


## 2.5 Controlled probability table

The table is:

    R=0:
      K^0(Y=1)=3/4
      K^1(Y=1)=1/4

    R=1:
      K^0(Y=1)=1/4
      K^1(Y=1)=3/4

The two controlled vectors are therefore:

    R=0 -> (3/4,1/4)
    R=1 -> (1/4,3/4)

They are distinct, and query labels are not temporal state. 

## 2.6 Structural join and lifecycle semantics

At genuine join:

- fresh lifecycle ownership is allocated;
- z is structurally initialized from the current cue;
- structural initialization is not counted as a learned write;
- fast recurrent state remains a separate primitive-control object.

At temporary leave:

- z, h, segment age and RNG are frozen;
- no controlled target, query or objective row occurs.

At rejoin:

- the same lifecycle state is restored;
- current observation is processed in the normal online order;
- rejoin does not itself force a write.

At terminal leave:

- the open segment is right-censored;
- evidence is recorded;
- state is deleted.

These semantics agree with the accepted open-roster base, whose skill hierarchy
is absent, padding capacity is not a model input, temporary absence freezes
hidden state and genuine join begins with a fresh zero hidden state.




The focused base tests independently cover constructive utility, inactive-width
invariance, lifecycle-state ownership, replay and fail-closed analysis.




## 2.7 Lexicographic estimand

S3 defines:

    L_ctrl(M)
      = mean over active histories and u
          E[-ln p_M(Y | z,u)]

    L_star
      = H
      = ln4 -(3/4)ln3

    E_ctrl(M)
      = L_ctrl(M)-L_star

    q(M)
      = mean active-row learned installation rate

    K(M)
      = number of decoder-distinct controlled kernels after quotienting
        decoder-equivalent latent values

Models are ordered lexicographically by:

    (E_ctrl,q,K)

This means:

1. exact controlled predictive sufficiency is mandatory;
2. positive predictive excess cannot be exchanged for fewer writes;
3. only among sufficient models is write rate minimized;
4. only among minimum-write sufficient models is decoder-kernel cardinality
   minimized.

This is a coherent correction to S2’s scalar rate–distortion objective and is
not a post-result beta change. 


## 2.8 Candidate values

The candidate:

- structurally installs `z=B`;
- writes `z←R` on each post-join cue;
- preserves z otherwise;
- ignores N;
- decodes the exact controlled table from `(z,u)`.

Before every decode:

    z=R

Therefore:

    E_ctrl=0
    q=2/7
    K=2

Its learned installations equal the two actual post-join regime changes.
Boundary precision and recall are one, and complete lifetimes are `{2,3}`.


The arithmetic and write normalization are exact: there are six learned
installations over 21 active rows, hence `6/21=2/7`.

---

# 3. Independent controlled-kernel recomputation

## 3.1 Fixed-query total variation

For `u=0`:

    R=0 -> Bernoulli(3/4)
    R=1 -> Bernoulli(1/4)

For Bernoulli distributions:

    TV(Bern(p),Bern(q))=|p-q|

so:

    TV(K_R=0^0,K_R=1^0)
      = |3/4-1/4|
      = 1/2

For `u=1`, the probabilities are reversed:

    TV(K_R=0^1,K_R=1^1)
      = |1/4-3/4|
      = 1/2

The artifact’s fixed-query separation is correct.

## 3.2 Uniform action marginal

Uniformly marginalizing u:

    P(Y=1 | R=0)
      = (1/2)(3/4)+(1/2)(1/4)
      = 1/2

    P(Y=1 | R=1)
      = (1/2)(1/4)+(1/2)(3/4)
      = 1/2

Therefore:

    TV(P(Y|R=0),P(Y|R=1))=0

The action marginal contains no regime information even though the complete
controlled vector does. This supports the registered
`CE-ACTION-MARGINAL-HIDES-CONTROLLED-STATE`.



## 3.3 Bayes floor

For every correct regime/query pair, the target probability is either `3/4` or
`1/4`. Both have the same entropy:

    H
      = -(3/4)ln(3/4) -(1/4)ln(1/4)
      = ln4 -(3/4)ln3

Thus:

    L_star=H

This is the exact controlled Bayes floor.

## 3.4 Never-write controlled probabilities

`NEVER_WRITE_AFTER_JOIN` preserves:

    z=B

Across the two scripts:

    P(R=z)
      = (4+5)/(2*7)
      = 9/14

    P(R≠z)
      = 5/14

For `z=0,u=0`:

    P(Y=1|z=0,u=0)
      = (9/14)(3/4)+(5/14)(1/4)
      = 4/7

For `z=0,u=1`:

    P(Y=1|z=0,u=1)
      = (9/14)(1/4)+(5/14)(3/4)
      = 3/7

For `z=1`, the two query probabilities reverse:

    u=0 -> 3/7
    u=1 -> 4/7

The fitted NLL is therefore:

    L_NW
      = h(4/7)
      = ln7 -(4/7)ln4 -(3/7)ln3

because `h(4/7)=h(3/7)`.

Its controlled excess is:

    E_ctrl(NW)
      = h(4/7)-H
      = ln7 -(11/7)ln4 +(9/28)ln3
      > 0

Strict positivity also follows directly from strict propriety: z=B merges
positive-probability histories whose true controlled vectors differ.



Thus never-write loses in the first lexicographic coordinate and cannot trade
its zero write rate against predictive excess.

---

# 4. Minimum-write and quotient theorem audit

## 4.1 Zero excess forces exact controlled kernels

The registered risk decomposes as an average of nonnegative KL divergences.

For deterministic writers:

    E_ctrl
      = mean_{f,u}
          KL(K_f^u || p_eta(.|z(f),u))

For stochastic writers, the expectation also includes the realized writer
randomness and installed z:

    E_ctrl
      = mean_{f,u}
          E_z[
            KL(K_f^u || p_eta(.|z,u))
          ]

Every term is nonnegative. Therefore:

    E_ctrl=0

implies zero KL for every positive-probability legal history, query and realized
installed state.

This almost-sure reading is required for the stochastic theorem and is already
applied by the artifact’s stochastic-writer argument.



No stochastic mixture can achieve zero expected excess by averaging incorrect
decoder states.

## 4.2 Every sufficient state distinguishes R

The two controlled vectors are:

    (3/4,1/4)
    (1/4,3/4)

They differ in both columns. Any decoder-visible state that gives the exact law
for every query must therefore distinguish the current regime almost surely.

The state need not use raw labels `0` and `1`; any invertible relabeling is
equivalent. But the decoder quotient must contain two distinct kernel classes.

## 4.3 Both change-row installations are mandatory

At structural join, the state is in the class for B.

For script `23`:

    first post-join change = active age 2
    second change = active age 5

For script `32`:

    first post-join change = active age 3
    second change = active age 5

Immediately before each change row, the installed decoder class represents the
old regime.

The current cue is the first legal information revealing the new regime.
Because decoding occurs after the writer update on that same row, exact
prediction requires the installed state to cross to the other decoder class on
that row.

The no-write transition preserves z. The decoder receives no current cue,
clock, h or other side channel. Therefore a decoder-class installation is
necessary at each of the two actual changes.


## 4.4 Lower bound on write rate

Every lifecycle has seven active rows and two mandatory post-join changes.

Therefore every controlled-sufficient model satisfies:

    q >= 2/7

The candidate attains equality.

## 4.5 Equality schedule

If a model with `q=2/7` installed at any additional no-change row with positive
probability, it would still need the two mandatory change-row installations and
would have:

    q > 2/7

Therefore equality allows no additional positive-probability installations.

Its only learned installations occur at the two actual post-join cue rows,
apart from null-probability events and latent relabeling.

This establishes schedule uniqueness at the decoder-equivalence-class level. It
does not require uniqueness of raw latent coordinates or parameters.

## 4.6 Quotient cardinality and nuisance removal

Every sufficient model requires at least the two distinct controlled kernels.

A latent may redundantly subdivide either kernel by:

- nuisance N;
- arbitrary coordinate labels;
- writer randomness;
- unused auxiliary bits.

But if two latent values induce the same complete controlled vector, they are
decoder-equivalent by definition and merge.

After quotienting:

    K=2

The iid nuisance N changes neither controlled vector and cannot survive as an
additional decoder-distinct state. It therefore cannot create an additional
skill or lifetime.



## 4.7 The theorem’s exact scope

The theorem establishes uniqueness of:

- minimum learned installation count;
- installation rows at equality;
- decoder-kernel quotient;
- active-step segment lengths.

It does not establish uniqueness of:

- neural parameters;
- raw latent coordinates;
- internal nuisance subdivisions before quotienting;
- the external primitive policy;
- optimization trajectory.

No theorem overreach is present in the S3 artifact.

---

# 5. Complete null-coverage audit

## 5.1 Never-write

Never-write has:

    q=0
    E_ctrl=h(4/7)-H>0

It loses in the first coordinate.

## 5.2 Always-write

Always-write can preserve controlled sufficiency, but it installs on all six
post-join rows:

    q=6/7>2/7

It loses in the second coordinate.

## 5.3 All 64 deterministic fixed-age masks

Each deterministic fixed-age mask is a subset of:

    {1,2,3,4,5,6}

For script `23`, a sufficient fixed mask must contain age 2.

For script `32`, it must contain age 3.

Both scripts require age 5.

Therefore every sufficient fixed-age mask contains:

    {2,3,5}

There are:

    2^(6-3)=8

supersets of `{2,3,5}`.

Every such mask schedules at least three installations:

    q>=3/7

The remaining 56 masks omit at least one mandatory change row and have positive
controlled excess.

This partitions all 64 masks. The general minimum-write theorem is stronger
than an enumeration of candidate-map parameters and covers every deterministic
online candidate map permitted under the fixed schedule.


## 5.4 Periodic schedules

Every finite-horizon deterministic period/phase schedule induces one of the 64
age masks. It is therefore either:

- insufficient; or
- a superset of `{2,3,5}` with at least three installations.

No periodic schedule reaches `(0,2/7,2)`.


## 5.5 Current-membership-event mappings

The current event categories are:

    ordinary
    rejoin
    terminal leave

There are exactly eight deterministic binary mappings over these three
categories.

If `ordinary=0`, writes can occur only at rejoin and/or terminal leave. Those
events are independent of B and S and cannot cover the two internal changes for
every lifecycle.

If `ordinary=1`, every ordinary active row is an installation row. Such a model
may be sufficient with an appropriate candidate map, but its write rate exceeds
`2/7`.

Thus none of the eight mappings matches the candidate tuple.


The artifact states the argument by category rather than printing the eight
three-bit strings. This is a complete proof, not an omitted terminal
obligation.

## 5.6 Post-hoc segmentation

A segmenter using a later target, future cue or completed trajectory violates
the registered online order.

When restricted to the legal online filtration, it is simply another online
writer and is subject to the same mandatory change-row theorem.

Post-hoc labels cannot install state retrospectively or improve an earlier
prediction.

## 5.7 Stochastic writers and mixtures

For any stochastic model, zero expected excess requires exact prediction almost
surely for every positive-probability history, query and writer realization.

Therefore every realized sufficient trajectory changes decoder class at both
actual regime changes.

Averaging across stochastic realizations cannot reduce expected write rate below
`2/7`.

A mixture with any positive-probability insufficient component has positive
excess and loses in the first coordinate. Equality leaves no
positive-probability extra write.


## 5.8 Nuisance-only state

A state based only on iid N has the same distribution under both regimes and
cannot reproduce the two distinct controlled vectors.

A sufficient state may encode N redundantly, but those subdivisions induce the
same controlled kernels and merge.

## 5.9 Action-marginal null

Without query u:

    P(Y=1|R=0)=P(Y=1|R=1)=1/2

The coarsest quotient has one state and correctly produces no nontrivial
controlled lifetime.

This is a valid negative control rather than a failure of the controlled source.

## 5.10 Natural-action query

A policy action selected with access to fast h may reveal R.

Such an action:

- lacks complete external support;
- is selected by temporal state;
- can act as a memory channel.

It is correctly classified as invalid controlled evidence rather than admitted
as a comparator.

## 5.11 Identical-kernel negative source

When the two regime controlled vectors are replaced by the same vector:

    K=1
    q=0 is sufficient
    no nontrivial controlled lifetime exists

The criterion therefore does not manufacture a lifetime from cue frequency,
nuisance or membership structure.


## Null-coverage conclusion

    never_write_covered=true
    always_write_covered=true
    all_64_fixed_age_masks_covered=true
    eight_sufficient_supersets_verified=true
    periodic_phases_covered=true
    all_membership_mappings_covered=true
    posthoc_meaning_valid=true
    stochastic_models_covered=true
    nuisance_only_covered=true
    action_marginal_control_valid=true
    natural_action_leak_rejected=true
    identical_kernel_negative_valid=true

No incomplete null obligation is found.

---

# 6. Constructive controls and invariances

The audit-only utility is:

    U=1[A=R]

and is absent from writer input, target, loss, decoder and boundary decision.

Constructive C-ALCPS:

    A=z

Constructive G8:

    store R in lifecycle h
    A=h

Both attain:

    U_star=1

This correctly blocks a representational-necessity claim. G8 remains a complete
external-policy comparator and strongest simpler explanation.


The exact invariances pass:

- lifecycle-key relabeling;
- active-member permutation;
- inactive padding;
- insertion of temporary-absence time;
- simultaneous controlled-query-label and kernel-column relabeling;
- latent-label relabeling.

Every registered mismatch is zero.


No reward, task, identity, role, success, progress, clock, natural-action memory,
active-set history or auxiliary persistence enters the controlled state channel.

---

# 7. S3 audit conclusion and first-match terminal

## 7.1 Exact audit result

    source_binding_valid=true
    nuisance_independence_valid=true
    online_order_valid=true
    writer_filtration_valid=true
    decoder_filtration_valid=true
    complete_query_support=true
    query_memory_leak=false
    probability_table_valid=true
    fixed_query_TV=1/2
    action_marginal_TV=0
    Bayes_floor_valid=true
    structural_join_valid=true
    lifecycle_semantics_valid=true
    lexicographic_estimand_valid=true
    candidate_tuple_valid=true
    minimum_write_theorem_valid=true
    equality_schedule_valid=true
    quotient_cardinality_valid=true
    null_coverage_complete=true
    constructive_controls_valid=true
    invariances_valid=true
    iteration_accounting_valid=true
    terminal_affecting_defects=none

One notation point should remain explicit in durable records:

    For stochastic writers, the KL decomposition includes the realized writer
    randomness and installed latent. Zero expected excess therefore means exact
    prediction almost surely, not merely correctness after marginalizing
    incompatible latent predictions.

The S3 artifact already applies this almost-sure condition, so this is a
clarification rather than a defect or repair.

## 7.2 First-match order

The frozen order is:

    1. INVALID_ALCPS_DERIVATION_CONTRACT
    2. ACTION_QUERY_OR_TEMPORAL_SIDE_CHANNEL_LEAK
    3. CONTROLLED_SOURCE_NON_IDENTIFIABLE
    4. NO_UNIQUE_MINIMAL_CONTROLLED_LIFETIME
    5. PASS_ALCPS_CONTROLLED_STATE_DERIVATION

### Branch 1 — invalid contract

Not selected.

No source, arithmetic, ordering, filtration, null, membership or invariance
defect exists.

### Branch 2 — action-query or temporal leak

Not selected.

Both queries have complete external support and carry no temporal memory. Fast
or natural-action query paths are excluded.

### Branch 3 — controlled source non-identifiable

Not selected.

Each fixed query separates regimes by TV `1/2`; the action marginal is zero as
required; the candidate attains the controlled Bayes floor.

### Branch 4 — no unique minimal lifetime

Not selected.

Every sufficient model has `q>=2/7`; equality installs only at the two actual
change cues; equivalent nuisance subdivisions merge to `K=2`; no registered
null has an equal or better lexicographic tuple.

### Branch 5 — PASS

Selected.

The correct first-match terminal is:

    PASS_ALCPS_CONTROLLED_STATE_DERIVATION

This agrees with the artifact’s recorded terminal and consequence boundary.


Iteration 3 is validly consumed. Seven remain.

---

# 8. Smallest supported and refuted propositions

## 8.1 Smallest supported proposition

    P_S3_MINIMAL_CONTROLLED_LIFETIME:

    On the exact finite S3 source, the coarsest quotient sufficient for the
    complete externally indexed one-step controlled-kernel vector has exactly
    two decoder classes. Every sufficient online model has learned installation
    rate at least 2/7; equality installs exactly at the two post-join change cues
    and yields complete active-step lifetimes {2,3}.

## 8.2 Smallest controlled-information proposition

    P_QUERY_VECTOR:

    The full controlled-query vector distinguishes the two regimes even though
    its uniform action marginal does not.

This supports the use of externally indexed controlled kernels as an
identification object. It does not validate natural policy actions as queries.

## 8.3 Smallest nuisance proposition

    P_QUOTIENT:

    Observed nuisance subdivisions that induce identical complete controlled
    kernels do not create additional controlled states or lifetimes after the
    decoder-equivalence quotient.

## 8.4 Smallest refuted proposition

S3 refutes:

    P_ACTION_MARGINAL_SUFFICIENCY:

    The action-marginal target law is sufficient to identify every
    action-relevant predictive regime distinguished by the complete controlled
    vector.

On this source, the marginal has zero regime separation while each controlled
query has separation `1/2`.

It also refutes:

    P_NATURAL_ACTION_QUERY_EQUIVALENCE:

    A selectively observed natural action chosen by a recurrent policy is
    interchangeable with an externally indexed query having complete support.

## 8.5 Propositions not supported

S3 does not support:

- learned skill semantics;
- a learned writer;
- a practical controlled-state estimator;
- recurrence insufficiency;
- an optimization advantage;
- sample-efficiency advantage;
- primitive-action mediation by an implemented z;
- natural write or state use;
- external utility gain;
- held-out robustness;
- transfer;
- complementary coordination;
- sufficiency for delayed or multi-step controlled futures;
- final algorithm integration.

The repository’s current conjecture and portfolio records preserve this ceiling.



---

# 9. Fresh plural CDC pass

## 9.1 Candidate A — C-ALSCPS: Agent-Local Sequential Controlled Predictive State

### Conjecture

A reusable lifecycle state should be identified by controlled future
observation sequences, not only by one immediate controlled target.

The state should also be update-congruent: histories placed in one
decoder-equivalence class must admit one common online state-update rule under
the same next legal observation.

### Mechanism-to-capability edge

A horizon-closed controlled state can preserve information whose causal effect
is delayed, while rejecting a one-step quotient that merges histories with
different future consequences.

This could eventually supply:

- a persistent state with sequential rather than instantaneous meaning;
- an objective active-step lifetime;
- an intervention-ready representation for delayed primitive consequences;
- a cleaner bridge to later policy mediation.

### Retains

- anonymous lifecycle ownership;
- active-step lifetime;
- S3’s complete externally indexed query support;
- task-blind supervision;
- lexicographic exact sufficiency, minimum writes and quotient cardinality;
- G8 as complete comparator.

### Deletes or replaces

- the assumption that one immediate controlled target is a sufficient state
  definition.

### Minimally adds

- a two-microstep controlled observation sequence;
- externally indexed length-two action plans;
- an update-congruence requirement.

### Strongest counterexample

Two histories can have identical one-step controlled kernels yet different
delayed controlled futures.

A one-step quotient then has one decoder class and no lifetime, even though an
action-sequence-conditioned second observation requires two persistent states.

### Strongest simpler explanation

G8 recurrence can encode the same delayed controlled statistic and may remain
equally useful. A future C-ALSCPS result cannot claim representational necessity.

### Plausibility-raising observation

An exact source where:

    one-step controlled TV = 0
    horizon-2 controlled TV = 1/2
    minimum sufficient q = 2/7
    quotient K = 2
    update-congruence mismatch = 0

### Plausibility-lowering observation

Any of:

- the horizon-2 kernels remain identical;
- the quotient is not recursively updateable;
- multiple different minimum-write schedules survive;
- future observations or action plans leak temporal state.

### Disposition

Retain and select for S4.

## 9.2 Candidate B — randomized-support C-ALCPS estimation

### Conjecture

A controlled quotient may be estimable from task-blind trajectories generated
under a known randomized primitive behavior policy with complete action support.

### Strongest contradiction

S3 supplies the complete controlled table directly. A finite natural data stream
may have inadequate per-history support, and an action chosen from h can create
selection or action-as-memory confounding.

### Required future correction

Before a learner is scheduled, freeze:

- sequential state object;
- randomized action-support contract;
- history clustering or representation class;
- estimation error semantics;
- a mechanism-matched null.

### Disposition

Park until the sequential controlled-state object is resolved. Implementing an
estimator for a potentially myopic one-step state is premature.

## 9.3 Candidate C — C-ALCPS primitive-policy link

### Conjecture

A learned primitive policy consuming a detached controlled state may obtain
better optimization, causal mediation or held-out transport than a
mechanism-matched masked-state arm.

### Strongest simpler explanation

G8 recurrence contains the same information and may learn the same policy.
Added capacity, different optimizer exposure or direct cue use could explain an
apparent gain.

### Required future evidence

- an implemented and valid controlled state;
- same-state z intervention;
- natural mediation;
- matched state-present/state-masked arms;
- exact G8 comparator;
- held-out dynamic-membership evaluation.

### Disposition

Park. S3 establishes an internal quotient only, not a behavioral link.

## 9.4 C-JRDM

Remain parked.

Joint h/z codelength still lacks an invariant decomposition under latent mixing.

Reactivation condition:

    representation-invariant joint information accounting plus a proven need
    for dual-channel ownership

## 9.5 C-ALH

Remain parked.

A per-step categorical hazard remains vulnerable to `k=1` renaming and the
R43–R45 closure.

Reactivation condition:

    an identified source requiring an explicit task-directed termination factor
    after a non-reward predictive state and its learning path are established

## 9.6 C-ATS

Remain parked.

Continuous timescale recurrence still lacks a threshold-free lifetime and can be
absorbed into recurrence.

Reactivation condition:

    a threshold-invariant survival or causal-persistence estimand

## 9.7 C-SEPM

Remain parked.

Population memory still changes coordination and lifetime together; TEAM_REC and
ordinary set encoders remain simpler explanations.

Reactivation condition:

    an identified complementary-allocation source on which lifecycle recurrence
    and TEAM_REC are insufficient

## 9.8 Broader predictive-state family

Status:

    strengthened locally, unresolved generally

S1 closed a free decoder-visible recurrence formulation.

S2 closed one scalarized rate–distortion interval.

S3 positively identifies a one-step controlled minimal state on one finite
source.

The next unresolved representation question is delayed future closure, not
one-step identifiability.

## 9.9 G8 and ordinary recurrence

G8 remains:

- the accepted usable dynamic-roster base;
- the complete external-policy comparator;
- the strongest simpler explanation;
- a constructive controller attaining utility one on the S3 source.

It is not a universal admission gate.

Any later explicit-state claim must concern optimization, sample efficiency,
causal use, robustness, transport or complexity—not finite representational
impossibility.

The scientific principles explicitly require matched comparators, sequential
intervention, natural transport and resistance to simpler explanations before
integration. 



---

# 10. Selected iteration-4 action

    action_id=S4_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_DERIVATION
    candidate=C_ALSCPS
    action_class=exact_derivation_counterexample_and_correction
    conclusion_bearing_iteration=4
    code_required=false
    compute_required=false
    prototype_required=false
    experiment_required=false
    Monitor_required=false

## 10.1 Exact question

Can a task-blind agent-local state be identified as the coarsest
minimum-transition state sufficient for a delayed two-microstep controlled
future when every immediate one-step controlled observation is
regime-uninformative?

The action must establish or refute all three edges:

1. the S3-style one-step quotient collapses;
2. the horizon-2 controlled future distinguishes regimes;
3. the horizon-2 quotient is online update-congruent and has one unique minimum
   active-step lifetime.

## 10.2 Scientific claim ceiling

A PASS may establish only:

    exact horizon-2 sequential controlled-state and active-step-lifetime
    identifiability on one finite anonymous-membership source

It cannot establish:

- arbitrary-horizon predictive sufficiency;
- learned state recovery;
- skill semantics;
- recurrence insufficiency;
- optimization or utility gain;
- primitive-policy mediation;
- natural value;
- held-out robustness;
- transfer;
- final integration.

## 10.3 Exact source

Retain from S3:

- independent `B∈{0,1}`;
- independent scripts `23/32`;
- the same regime sequences and cues;
- 21 active rows;
- three lifecycle epochs;
- temporary leave/rejoin;
- genuine join;
- terminal leave;
- structural join;
- nuisance `N`;
- complete lifetimes `{2,3}`;
- all registered membership and label invariances.

S4 is a new controlled-future source, not a reinterpretation or rescue of S3.

## 10.4 Writer observation and membership semantics

The writer observation remains:

    O_n=(C_n,X_n,N_n)

Writer filtration remains:

    current O_n
    previous z
    fresh writer randomness

All S3 prohibitions remain in force.

Structural join initializes z without a learned write.

Temporary absence freezes state, age and RNG.

Rejoin restores ownership and processes the current observation normally.

Terminal leave right-censors and deletes the state after evidence capture.

## 10.5 External action plan

At every legal active history, enumerate every open-loop binary plan:

    a=(u_0,u_1) ∈ {0,1}^2

There are four plans:

    00
    01
    10
    11

Each plan is:

- externally indexed;
- independent of h, z, history, identity and natural policy;
- absent from writer input;
- branch-local;
- supplied only to the sequential controlled decoder;
- evaluated with complete support at every legal history.

The plan does not persist into another natural active row.

## 10.6 Delayed controlled observation sequence

For each current regime R and plan `(u_0,u_1)`, emit two branch observations:

    Y^(1) ~ Bernoulli(1/2)

independent of R, plan, nuisance and membership.

Conditional on R and the plan, emit:

    P(Y^(2)=1 | R,u_0,u_1)
      = 3/4  if u_0 XOR u_1 = R
      = 1/4  otherwise

The two branch observations are conditionally independent given R and plan.

The branch starts from the current exact lifecycle snapshot and does not mutate
the natural lifecycle, membership, writer, segment age or natural RNG.

## 10.7 Required horizon separation

For the one-step projection containing only `Y^(1)`:

    P(Y^(1)=1 | R,a)=1/2

for every R and plan.

Therefore:

    one_step_TV=0

and the coarsest one-step quotient has:

    K_1=1

For every complete plan a, the two regimes have joint sequence distributions:

    P_R(Y^(1),Y^(2)|a)
      = Bernoulli(1/2) × Bernoulli(p_R(a))

with `p_R(a)` equal to `3/4` or `1/4`.

Because the first factor is identical:

    TV(P_R=0(.|a),P_R=1(.|a))
      = |3/4-1/4|
      = 1/2

for every plan.

Thus:

    horizon2_TV=1/2

The source must preserve the exact contrast:

    one_step_TV=0
    horizon2_TV=1/2

## 10.8 Sequential decoder and state quotient

The decoder is:

    p_eta(Y^(1),Y^(2) | z,a)

It receives exactly:

- installed z;
- current external plan a.

It receives no:

- current observation or cue;
- h;
- nuisance;
- clock;
- natural action;
- future observation;
- membership history;
- auxiliary persistent state.

Two latent values are sequentially decoder-equivalent iff their complete joint
sequence kernels agree for all four plans.

State cardinality `K_2` is counted only after merging equivalent latent values.

## 10.9 Update congruence

The quotient must admit one common online update function:

    F(class(z_n-),O_n) -> class(z_n+)

For the candidate:

    if C_n=1:
      F(z,O_n)=X_n

    otherwise:
      F(z,O_n)=z

A PASS requires exact congruence:

    histories in the same quotient class
    + the same legal current observation
    -> the same next quotient class

A predictive partition that cannot be updated recursively from its own state
and current legal observation is not an admissible lifecycle state.

## 10.10 Sequential predictive criterion

Define the exact sequence Bayes floor:

    H
      = ln4 -(3/4)ln3

    L_2_star
      = ln2 + H

The first term is the entropy of the fair immediate observation; the second is
the controlled delayed-response entropy.

Define:

    L_2(M)
      = mean over active histories and four plans
          E[-ln p_M(Y^(1),Y^(2)|z,a)]

    E_2(M)
      = L_2(M)-L_2_star

    q(M)
      = mean active-row learned installation rate

    K_2(M)
      = decoder-distinct horizon-2 sequence-kernel cardinality after quotienting

Order models lexicographically by:

    (E_2,q,K_2)

Positive horizon-2 predictive excess cannot be exchanged for fewer writes.

## 10.11 Candidate C-ALSCPS

The candidate:

- structurally sets `z=B`;
- writes `z←X_n` on each post-join cue;
- preserves z otherwise;
- ignores nuisance N;
- decodes the exact horizon-2 table from `(z,a)`.

Required values:

    E_2=0
    q=2/7
    K_2=2
    update_congruence_mismatch=0
    boundary_precision=1
    boundary_recall=1
    complete_lifetimes={2,3}

## 10.12 Mandatory comparators and nulls

### One-step quotient null

`ONE_STEP_CONTROLLED_QUOTIENT` uses only the one-step sequence projection.

Required:

    K_1=1
    E_2>0

Its best delayed prediction averages over R and cannot reproduce the
horizon-2 kernels.

### Never-write

Preserve `z=B`.

Its sequence NLL is:

    L_2_NW
      = ln2 + h(4/7)

and:

    E_2_NW
      = h(4/7)-H
      > 0

### Always-write

It may be sufficient, but:

    q=6/7

### Fixed-age and periodic schedules

Cover all 64 age masks and every finite-horizon period/phase schedule.

A sufficient fixed schedule must contain:

    {2,3,5}

and therefore has:

    q>=3/7

### Membership-only schedules

Cover all eight current-event mappings. They either miss internal regime
changes or write on ordinary rows at a rate greater than `2/7`.

### Post-hoc segmentation

Future branch observations cannot alter the already installed state or an
earlier sequence prediction.

### Stochastic writers

Zero expected sequence excess must imply exact sequence prediction almost
surely over writer randomness. Mixtures cannot average away the two mandatory
class changes.

### Nuisance-only state

N is independent of every horizon-2 controlled kernel. Nuisance subdivisions
must merge.

### Natural action-plan leak

A length-two plan chosen by a policy with fast recurrent memory is not external
controlled support and must be rejected.

### Future-outcome leak

Giving `Y^(1)` or `Y^(2)` to the writer before the current installation is
invalid.

### Identical-sequence-kernel negative source

If both regimes have identical complete horizon-2 kernels, the quotient must
have:

    K_2=1
    q=0

and no nontrivial lifetime.

## 10.13 Adaptive-plan audit

The four open-loop plans are the conclusion-bearing query set.

As an audit, any deterministic second-action rule based on `Y^(1)` must be shown
not to add temporal information. Because `Y^(1)` is independent of R, such a
feedback rule induces a regime-independent mixture over the four registered
open-loop plans.

It cannot turn the one-step projection into an informative state or eliminate
the horizon-2 regime distinction already present in the open-loop set.

## 10.14 Constructive external controls

Retain audit-only external utility:

    U=1[A=R]

Utility remains absent from sequential-state supervision.

Constructive C-ALSCPS:

    A=z

Constructive G8:

    store R in h
    A=h

Required:

    U_star_ALSCPS=1
    U_star_G8=1

This remains a source control, not comparative evidence.

## 10.15 Invariances

Require zero mismatch under:

- lifecycle-key relabeling;
- active-member permutation;
- inactive padding;
- temporary-absence insertion;
- arbitrary permutation of the four external plan labels with corresponding
  sequence-kernel columns;
- latent-state relabeling;
- nuisance-bit relabeling.

## 10.16 Exact proof obligations

A PASS requires every item below.

1. The S3 lifecycle and membership source is preserved exactly.

2. The delayed two-microstep controlled target law is finite and internally
   consistent.

3. All four open-loop plans have complete external support at every legal
   history.

4. Plans carry no temporal memory and are absent from the writer.

5. The immediate projection has:

       one_step_TV=0
       K_1=1

6. Every full plan has:

       horizon2_TV=1/2

7. The sequence Bayes floor is:

       L_2_star=ln2+H

8. The candidate reaches:

       E_2=0
       q=2/7
       K_2=2

9. Every model with `E_2=0` distinguishes the two regime sequence-kernel
   vectors almost surely.

10. Every sufficient online model changes decoder class at both actual
    post-join changes.

11. Therefore:

       q>=2/7

12. Equality writes only on the two actual cue rows, up to null events and
    latent relabeling.

13. Quotienting decoder-equivalent states yields:

       K_2=2

14. The candidate quotient is update-congruent under one common online function.

15. The one-step quotient is horizon-2 insufficient.

16. Never-write has exact positive excess:

       E_2_NW=h(4/7)-H>0

17. Every fixed-age, periodic, membership-only, post-hoc and stochastic null is
    insufficient or lexicographically worse.

18. Nuisance subdivisions merge.

19. Natural-plan and future-outcome leaks are rejected.

20. The identical-sequence-kernel negative control yields no false lifetime.

21. Boundary precision and recall are one.

22. Complete active-step lifetimes are `{2,3}`.

23. Constructive C-ALSCPS and G8 policies both have utility one.

24. Every registered invariance mismatch is zero.

25. No reward, task field, identity, role, goal, success, progress, natural
    action memory, clock, future observation or auxiliary persistence enters the
    admissible sequential state channel.

There is no statistical, mixed or underpowered branch.

## 10.17 First-match terminals

Apply this order.

1. `INVALID_ALSCPS_DERIVATION_CONTRACT`

   Any source arithmetic error, inconsistent delayed target, incomplete null,
   invalid online order, invalid membership semantics, failed invariance or
   forbidden task/reward field.

2. `ACTION_PLAN_OR_FUTURE_INFORMATION_LEAK`

   Query plans are selected by h/history, support is selective, the writer sees
   future branch outcomes, or another temporal side channel enters.

3. `NO_HORIZON_SEPARATING_CONTROLLED_SOURCE`

   The one-step projection does not collapse as registered, the horizon-2
   kernels do not separate, or the candidate cannot reach the exact sequence
   Bayes floor.

4. `NO_UNIQUE_MINIMAL_FUTURE_CLOSED_LIFETIME`

   Exact horizon-2 sufficiency is attainable, but the quotient is not
   update-congruent, another minimum-write schedule survives, nuisance remains
   decoder-distinct, or a registered null has an equal or better
   `(E_2,q,K_2)` tuple.

5. `PASS_ALSCPS_FUTURE_CLOSED_DERIVATION`

   Every exact proof obligation passes.

## 10.18 Required artifact

The sole S4 conclusion-bearing artifact is:

    docs/research/cdc/EVIDENCE_NOTES/
    20260724_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_S4.md

It must contain:

- the exact lifecycle source;
- the two-microstep controlled potential-outcome table;
- complete four-plan support;
- immediate and horizon-2 TV arithmetic;
- exact sequence entropy and excess calculations;
- writer/decoder filtration;
- update-congruence proof;
- complete deterministic and stochastic null treatment;
- one-step-myopia counterexample;
- natural-plan and future-outcome leak counterexamples;
- nuisance quotient;
- constructive C-ALSCPS and G8 controls;
- invariance proofs;
- smallest supported and refuted propositions;
- first-match terminal;
- no engineering plan, code or resource schedule.

## 10.19 Stop and iteration rule

Stop on the first valid S4 terminal.

A valid PASS or negative consumes iteration 4:

    consumed=4
    remaining=6

An invalid derivation consumes no iteration and permits at most one bounded
correction of transcription, arithmetic or proof checking under the identical:

- source;
- delayed target table;
- query-plan support;
- filtration;
- null family;
- estimand;
- proof obligations;
- terminal order.

Changing one of those objects requires a new Pro decision.

A second invalid realization is a blocker.

After a valid S4 terminal, return the exact result to this same registered Pro
conversation before selecting iteration 5.

---

# 11. Why S4 is the cheapest next action

S3 positively resolves one-step controlled-state identifiability. Repeating that
proof or implementing it immediately would not answer whether the state is
sequentially meaningful.

A bounded implementation now would conflate:

- one-step state myopia;
- delayed-effect representation failure;
- estimator error;
- architecture leakage;
- optimization failure;
- implementation defects.

The horizon-2 derivation can separate the first two before code exists.

It is cheaper and more reversible than:

- designing a learned controlled-state estimator;
- introducing a joint h/z information penalty;
- training a policy adapter;
- reviving an explicit hazard;
- adding population memory.

This follows the project rule to prefer derivation and counterexample before
implementation when the research object still has a structural ambiguity.




---

# 12. Durable repository deltas after factual reconciliation

## 12.1 Conjecture ledger

Update `C-ALCPS`:

    status=accepted_exact_S3_derivation_PASS
    terminal=PASS_ALCPS_CONTROLLED_STATE_DERIVATION
    implementation_authorized=false
    compute_authorized=false

Retain its exact supported scope:

    one-step complete external controlled-query vector
    minimum sufficient q=2/7
    quotient K=2
    active-step lifetimes={2,3}
    frozen finite source only

Add its main unresolved counterexample:

    one-step controlled equivalence may merge histories with different delayed
    controlled futures

Add:

### `C-ALSCPS — Agent-Local Sequential Controlled Predictive State`

Status:

    selected for S4 horizon-2 exact derivation
    no code or compute selected

Claim:

    a canonical lifecycle state and lifetime may be identified by the coarsest
    minimum-transition, update-congruent quotient sufficient for delayed
    controlled observation sequences

Strongest simpler explanation:

    G8 recurrence stores the same delayed statistic and the explicit state adds
    no optimization, mediation or transport benefit

Intervention consequence:

    histories merged by the immediate controlled projection have different
    externally indexed horizon-2 controlled futures

Natural consequence:

    not established by S4

Held-out consequence:

    not established by S4

Retain C-JRDM, C-ALH, C-ATS and C-SEPM as parked.

Retain G8 and ordinary recurrence as mandatory comparators, not admission gates.

## 12.2 Lemma ledger

Add:

### `L-S3-VALID-PASS`

The exact S3 derivation validly identifies a coarsest minimum-write one-step
controlled state and active-step lifetime on its frozen source.

Does not imply:

    skill learning, sequential closure, optimization benefit or transport

Retain:

### `L-CONTROLLED-QUERY-SEPARATION`

The complete external query vector can distinguish regimes whose action
marginal is identical.

Retain:

### `L-ALCPS-MINIMUM-WRITE-QUOTIENT`

Exact controlled sufficiency forces both change-row installations and quotient
cardinality two on S3.

Add only as an S4 pending proposition, not a retained lemma yet:

### `L-SEQUENTIAL-CLOSURE-REQUIRES-FUTURE-KERNELS`

One-step controlled equivalence need not imply equality of delayed controlled
futures.

Promote it only after a valid S4 terminal.

## 12.3 Counterexample ledger

Retain the accepted S3 counterexamples:

- `CE-ACTION-MARGINAL-HIDES-CONTROLLED-STATE`;
- `CE-NATURAL-ACTION-AS-QUERY-LEAK`;
- `CE-PREDICTIVE-NUISANCE-SUBDIVISION`.

Add as S4 registered counterexample candidates:

### `CE-ONE-STEP-CONTROLLED-MYOPIA`

Two regimes can induce identical immediate controlled observations while
producing different delayed controlled observation sequences.

### `CE-NATURAL-PLAN-AS-MEMORY`

An action plan selected by fast recurrence can encode hidden state and is not an
external intervention plan.

### `CE-FUTURE-OUTCOME-WRITER-LEAK`

A writer that sees a delayed branch outcome before its current installation
uses future information and cannot support an online lifetime claim.

### `CE-NONCONGRUENT-PREDICTIVE-PARTITION`

A partition can summarize current predictions yet fail to admit one common
online update rule, so it is not a valid persistent state.

Promote these only after the S4 artifact proves them.

## 12.4 Idea portfolio

Set:

    C-ALPSW:
      closed exact S1 formulation

    C-ALPSC:
      closed exact S2 formulation and interval

    C-ALCPS:
      exact S3 derivation PASS
      implementation and compute unselected

    C-ALSCPS:
      live and selected for S4 derivation

    randomized-support C-ALCPS estimation:
      parked pending sequential closure

    C-ALCPS primitive-policy link:
      parked pending a valid learned state

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

    S4_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_DERIVATION

Authorization:

    derivation selected
    code not selected
    compute not selected
    iterations 5_to_10 unselected

## 12.5 Evidence-note delta

Add:

    docs/research/cdc/EVIDENCE_NOTES/
    20260724_ALCPS_S3_RESULT_AND_ALSCPS_S4_DIRECTION.md

Record:

- S3 validity audit;
- independent controlled-kernel arithmetic;
- accepted first-match PASS;
- exact supported/refuted propositions;
- unchanged R42–R48 scopes;
- plural portfolio;
- C-ALSCPS scientific contract;
- S4 source, estimand, nulls and proof obligations;
- iteration accounting;
- evidence commit
  `7cf10a01497176e4079c29c9f95fcb09fd60f660`;
- this response provenance.

Do not add an experiment row to `ExpRecord.md`. S4 is a derivation.

## 12.6 Current-work delta

After factual reconciliation, set:

    last_completed_assignment_id=S3_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_DERIVATION
    active_assignment_id=S4_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_DERIVATION
    next_boundary=COMPLETE_EXACT_S4_DERIVATION_THEN_RETURN_TO_PRO
    conclusion_bearing_iterations_consumed=3
    skill_lifetime_chain_iterations_remaining=7
    k_decoupling_current_result=PASS_ALCPS_CONTROLLED_STATE_DERIVATION
    active_scientific_direction=C_ALSCPS
    active_scientific_contract=20260724_ALCPS_S3_RESULT_AND_ALSCPS_S4_DIRECTION
    active_algorithm=PREFIX_NORMALIZED_OPEN_ROSTER_G8_imported_base
    s4_code_required=false
    s4_compute_required=false
    formal_compute_status=not_started

Only a valid S4 terminal changes the count to four consumed and six remaining.

---

# 13. Unchanged R42–R48 scopes

S3 changes none of the imported closure or quarantine boundaries.

- R42’s incumbent-conditioned categorical skill-logit residual remains closed.
- R43 remains scientifically quarantined because its fixed positive anchor
  failed.
- R44’s frozen-source global-`K=50` external-return renewal route remains closed.
- R45’s Alice–Bob natural-support Q/DR renewal route remains closed.
- R46’s exact HMRV estimator/read combination remains closed; oracle
  heterogeneity was not rejected.
- R47’s exact spectral view, basis and score remain closed.
- R48’s focal hidden reset at categorical SET remains closed.

C-ALSCPS uses no categorical skill, reward-trained renewal, action-Q
heterogeneity estimator, spectral skill label or hidden reset. It is not a
rename or rescue of those routes.

---

# 14. What this ruling does not authorize

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
- a learned controlled-state estimator;
- natural policy actions as intervention queries;
- a beta objective;
- a joint h/z information penalty;
- an explicit categorical hazard;
- a continuous-timescale threshold;
- a set-equivariant population-memory module;
- external reward in predictive supervision;
- task fields, identity, role, goal, success or progress inputs;
- a skill, utility, optimization, mediation, robustness or transport claim;
- revival of R42–R48;
- mutation of `aggressive`;
- selection of iterations 5–10;
- integration into the final HMASD algorithm.

A future S4 PASS would establish only horizon-2 sequential controlled-state and
active-lifetime identifiability on the frozen finite delayed-effect source. It
would still require a new CDC decision before estimator design, implementation
or behavioral testing.

External scientific review itself does not authorize code or compute.



---

# 15. 中文用户简报

S3 裁决有效：`PASS_ALCPS_CONTROLLED_STATE_DERIVATION`。

完整外部 query 向量确实区分两种 regime：每个固定 query 的 total variation 都是
`1/2`，而均匀 action marginal 的区分度是 `0`。字典序标准先要求精确受控预测充分，
再最小化写入数和 quotient 状态数，因此 S2 的 rate–distortion 交换不再成立。
任何零 excess 模型都必须在两个真实 post-join change row 切换 decoder class，
所以 `q>=2/7`；达到等号时只能在这两个 cue 写入。合并 decoder-equivalent nuisance
subdivision 后恰好剩两类，得到 `{2,3}` 的 active-step lifetime。合同、query 支持、
null 覆盖、membership 语义和不变量均无终态缺陷。第 3 次结论性迭代已消耗，剩余
7 次。

该 PASS 只证明冻结有限 source 上的**单步受控状态可识别性**，不证明 learned
skill、普通 recurrence 不足、优化收益、自然因果中介、held-out value 或迁移。G8
仍能把同一 regime 存在 recurrent `h` 中并达到 utility 1。

第 4 次唯一行动是无代码、无计算的
`S4_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_DERIVATION`。它构造一个精确 delayed
controlled source：第一步 observation 对 regime 完全无信息，第二步受长度二 action
plan 控制并区分 regime。S4 必须证明单步 quotient 的 `K_1=1` 和 TV=0，同时两步
sequence kernel 的 TV=`1/2`，并证明新的 quotient 可递归更新、最小写入率仍为
`2/7`、状态数仍为 2、生命周期仍为 `{2,3}`。

决定性否证条件是：两步 kernel 不能形成新区分、query plan 或 future outcome 泄漏
时间信息、quotient 无法用一个共同在线更新函数递归更新、存在另一套相同最小写入
schedule，或 nuisance 仍为 decoder-distinct。任一有效负分支都会关闭精确
C-ALSCPS 合同，不进入实现。迭代 5–10 仍未选择。
