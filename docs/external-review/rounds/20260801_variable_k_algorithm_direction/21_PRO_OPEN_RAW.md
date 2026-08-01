RULING
Select a modified B1: first qualify heterogeneous renewal urgency, then test unrestricted R30’s natural access to it

The first conclusion-bearing variable-k package should be:

V-K0A  exact renewal-urgency source qualification
       environment: two_timescale_role_free_actions
       controller: no learned controller; exhaustive legal KEEP/SET oracle
       compute: proof-sized, no training

V-K0B  unrestricted-R30 natural-access screen
       environment: the same toy
       controller: r30_fixed_clock_ar_edit
       executor: the existing fixed four-skill primitive table
       compute: bounded training plus held-out interventional evaluation
       launch condition: V-K0A passes

This is one ordered scientific sequence, not two competing routes.

It advances the first premise of the paper claim:

the task actually contains per-agent, state-dependent renewal urgency, and the selected unrestricted carrier can encounter and orient its natural renewal decisions toward that quantity.

It does not yet test:

superiority to the best shared fixed period;

the search-efficiency tradeoff;

a learned low-cardinality renewal class;

UAV transfer;

variable membership;

or asynchronous offered-decision clocks.

Those remain later stages. The user-owned goal makes heterogeneous renewal urgency and unrestricted-R30 access prerequisites to the learned constrained comparison; it also explicitly defines R30 as untying realized renewal intervals, not the shared check clock.

Why two_timescale_role_free_actions

This is the cleanest first source because:

both agents have constant, identical local observations;

the centralized state exposes the slow target, fast target, and their phases;

reward is anonymous and uses the better of the two agent-to-target assignments;

the low-level executor is a fixed, zero-parameter four-action table;

the fast target changes every five primitive steps, while the slow target changes every thirty;

one R30 check interval is therefore exactly the smallest meaningful renewal window.

This removes learned-skill discovery, sparse reward, recurrent low-level optimization, and task-specific intrinsic reward as explanations. It isolates high-level temporal control.

Why the source gate must come before anchors or a constrained mechanism

A return comparison between fixed-k and R30 would be ambiguous until three different facts are separated:

whether the source contains heterogeneous individual renewal urgency;

whether unrestricted R30 can access it under its actual autoregressive continuation;

whether a structured low-cardinality approximation improves finite-budget learning.

The constrained mechanism does not exist, so B2 would require choosing its representation before learning what structure the source and carrier expose. That risks hard-coding the toy’s slow/fast labels into the mechanism—the opposite of the paper claim.

B3 is also premature. A fixed-k-versus-R30 result could be negative because:

the source does not identify the primitive;

R30 lacks access;

R30 has access but its replacement-skill distribution is poor;

or shared k genuinely suffices.

V-K0 distinguishes these before adding another controller.

Conditional successor tree
V-K0A source qualification fails
    -> retire this toy as a variable-k source
    -> do not tune R30 or design the constrained arm
    -> select another toy source, with Alice–Bob retained as a live candidate

V-K0A passes, V-K0B competence/access fails
    -> retain the source result
    -> classify the smallest R30 access failure
    -> do not design the constrained arm yet

V-K0A and V-K0B both pass
    -> next conclusion-bearing experiment is V-K1:
       best true shared fixed period versus unrestricted R30
       under one shared artifact and exposure contract

V-K1 then establishes a useful unrestricted baseline
    -> only then derive the learned low-cardinality renewal-class mechanism

The principles require source access, mechanism identification, intervention behavior, and natural transport to remain distinct questions; they also require the cheapest separating evidence before implementation accumulation.

MEASUREMENT
1. The clocks

Freeze:

primitive step             environment step
offered-decision clock     k0 = 5 primitive steps, shared by both agents
renewal window Δ           5 primitive steps, exactly one offered-check interval
slow source period         30 primitive steps = 6 checks
episode horizon            40 primitive steps = 8 checks

The experiment concerns heterogeneous realized renewal intervals under repeated KEEP decisions. It makes no claim that agents are offered decisions at different physical times. The existing R30 carrier and goal statement both preserve that boundary.

Define the external-return window:

G
Δ
	​

(x
t
	​

,a)=
τ=0
∑
4
	​

r
t+τ
ext
	​

.

No intrinsic reward, switch penalty, duration reward, or shaping enters G
Δ
	​

.

2. V-K0A: source-level renewal urgency
Why a fixed-teammate contrast is insufficient

The toy is role-free. If the focal agent changes target, the other agent may swap duties and preserve full team reward. Therefore a contrast that freezes the teammate’s factual token can manufacture “individual necessity” that the actual joint action support avoids.

The source qualification must ask the stronger question required by a mechanism claim:

After constraining the focal agent to KEEP or SET, what is the best return available under the same legal joint action support for every other agent?

This follows the project rule that a control cannot establish necessity if an equally good legal solution avoids the target behavior.

Registered source estimand

At an active R30 check state x
t
	​

, let A(x
t
	​

) be every legal joint edit sequence under the current R30 support:

an active agent may KEEP;

or SET to any non-incumbent skill;

same-label SET is excluded;

after the edit, the fixed supplied primitive is executed for Δ=5;

no further high-level check occurs inside the window.

For focal agent i:

V
i
K
	​

(x
t
	​

)=
a∈A(x
t
	​

):a
i
	​

=KEEP
max
	​

G
Δ
	​

(x
t
	​

,a),
V
i
S
	​

(x
t
	​

)=
a∈A(x
t
	​

):
a
i
	​

=SET(z), z

=z
i
	​

	​

max
	​

G
Δ
	​

(x
t
	​

,a),
U
i
src
	​

(x
t
	​

,Δ)=max(0,V
i
S
	​

(x
t
	​

)−V
i
K
	​

(x
t
	​

)).
	​


Including zero reflects the actual redecision opportunity: an agent offered a decision may still KEEP. SET alone is not the definition of redecision.

This is a finite exhaustive computation: two agents, four supplied skills, and one five-step deterministic continuation. It has no fitted estimator and no optimization noise.

Canonical source panel

Enumerate one full slow cycle under all:

initial slow sign                 {-1, +1}
initial fast sign                 {-1, +1}
anonymous slot assignment         both agent permutations
noninitial shared checks          7 per episode template

This gives:

4 sign combinations
× 2 agent permutations
× 7 noninitial checks
× 2 focal agents
= 112 focal source rows

The initial check is recorded but excluded from U
i
	​

, because no incumbent exists and KEEP is not legal.

The panel must contain the expected structural pattern without using agent identity:

at each fast-only target change, one focal state is materially urgent and one is stable;

at the joint slow-plus-fast change, both focal states are urgent;

swapping the two agent slots leaves the unordered urgency pair unchanged;

each physical slot appears in both urgency classes somewhere in the panel.

The analyzer may read target vectors and supplied skill actions to compute the oracle. Those source labels are evaluation truth only; they are never policy inputs and must not become a future renewal-class label.

3. Task-semantic materiality unit

Freeze:

δ
U
	​

=0.5 external-return units.
	​


The environment’s team reward is the mean of the slow and fast target-match scores. Moving one required target from complete mismatch to exact match changes team reward by 0.5 for one primitive step. Thus δ
U
	​

=0.5 is one full target-slot improvement for one primitive step—an externally interpretable unit fixed from the source definition, not from observed effects.

For source classification:

URGENT    U_src > +0.5
STABLE    U_src < +0.5
BOUNDARY  U_src = +0.5, classified unresolved

Because U
i
src
	​

≥0, no negative-stability threshold is needed.

The expected full correction over one five-step interval is 2.5, but 2.5 must not be used as the threshold: it is the maximum one-target window effect, so requiring a lower bound above it would be structurally unreachable.

4. V-K0B: unrestricted-R30 access

V-K0B uses the existing evaluation-only forced-token surface. The R30 sampler already supports:

focal forced KEEP;

focal forced SET to a named skill;

focal forced SET with the replacement sampled from π
SET
	​

;

common base draws;

and natural downstream autoregressive responses by later agents.

The current implementation deliberately lets later agents see the focal agent’s modified prefix. That is the deployed autoregressive continuation, not the fixed-teammate direct effect.

Register three policy-side quantities.

A. Accessible opportunity

For candidate skill z:

U
i,z
opp,π
	​

=E
ω
	​

[G
Δ
	​

(SET
i
	​

(z),π
−i
AR
	​

)−G
Δ
	​

(KEEP
i
	​

,π
−i
AR
	​

)],

and

U
i
opp,π
	​

=max(0,
z
max
	​

U
i,z
opp,π
	​

).
	​


This asks whether some legal focal renewal has value when the remaining autoregressive roster responds under the learned policy.

B. Sampled-SET competence
U
i
SET,π
	​

=E
ω
	​

[G
Δ
	​

(SET
i
	​

(z∼π
SET
	​

),π
−i
AR
	​

)−G
Δ
	​

(KEEP
i
	​

,π
−i
AR
	​

)].

This separates “the carrier can expose a useful SET” from “its learned replacement-skill distribution selects one.”

C. Natural decision value and hazard

Using the unforced factual token:

U
i
nat,π
	​

=E
ω
	​

[G
Δ
	​

(a
i
	​

∼π,π
−i
AR
	​

)−G
Δ
	​

(KEEP
i
	​

,π
−i
AR
	​

)],

and

λ
i
π
	​

(x
t
	​

)=1−p
KEEP,i
	​

(x
t
	​

).

Record both:

the policy propensity 1−p
KEEP
	​

;

and the realized natural SET indicator.

keep_prob is valid only for active learned-KEEP decisions. Initial assignments and forced-refresh/native-categorical paths must remain NaN or explicitly ineligible, consistent with the R30 implementation.

Interpretation

This yields a useful failure decomposition:

Observation	Smallest interpretation
U
src
 fails	toy source does not identify the primitive
U
src
 passes, U
opp,π
 fails	R30 continuation/action access failure
U
opp,π
 passes, U
SET,π
 fails	replacement-skill selection failure
opportunity and SET pass, natural hazard does not align	KEEP/SET policy-orientation failure
all pass	unrestricted R30 naturally accesses heterogeneous renewal urgency
5. Paired replay semantics

Every counterfactual family at one check must begin from one immutable snapshot containing:

environment state
centralized state and observations
current skills
skill ages
active mask
steps_to_check
agent order
all high/low hidden state
environment RNG
NumPy RNG
PyTorch CPU/CUDA RNG
policy/checkpoint identity

For one base draw:

Restore the snapshot.

Run focal forced KEEP.

Restore it again.

Run focal forced SET or natural policy.

Use the same base random draws.

Permit later autoregressive agents to respond to the modified roster.

Roll exactly five primitive steps.

Assert that no further high check occurred.

The R30 hook draws the KEEP uniform and skill categorical before applying a forced token, specifically to preserve common-random-number alignment.

For U
opp,π
, use:

n_select = 2 per legal SET candidate
n_eval   = 2 for the selected candidate and paired KEEP

Candidate selection and evaluation streams must be disjoint. The maximizer may not be selected and evaluated on the same two draws.

For U
SET,π
 and U
nat,π
, use two paired evaluation draws per row.

A fixed-teammate direct contrast may be retained as a diagnostic. It must not carry the source or policy-access verdict because it does not represent the deployed autoregressive continuation.

6. Minimal bounded trace

The missing instrumentation is not a primitive-step training log. The smallest sufficient addition is an evaluation-only row at every offered high-level check, per agent, plus the five external rewards for each paired continuation.

renewal_check_trace.jsonl

One row per check-agent:

contract and trace-schema version
training seed / evaluation seed / episode id
primitive step / check index
agent order and anonymous slot permutation
agent id only as bookkeeping, never as a class
active mask
current skill and skill age
steps_to_check
state, observation and pre-check snapshot hashes
current and previous target vectors
oracle U_src and oracle urgency class
natural token kind
natural SET skill
keep_prob
full factual joint token vector
voluntary/exogenous ending reason
renewal_counterfactual_units.jsonl

One row per check-agent/base-draw/candidate:

pre-check state and RNG hashes
focal constraint
later-agent continuation semantics = autoregressive_policy_response
candidate skill
phase = select | evaluate
replicate index and derived seed
five-step external-reward vector
window return
post-window state hash
paired KEEP unit id
replay-conformance booleans
Other durable files
source_oracle_panel.json
train_and_checkpoint_manifest.json
summary.json

summary.json must be reproducible solely from the two JSONL files and the oracle panel. It may not contain a statistic whose row-level source was discarded.

The trace must distinguish voluntary SET from:

initial assignment;

episode termination;

active-mask change;

team-intent boundary;

forced renewal.

The current goal document identifies these as different segment-ending authorities; collapsing them would measure environment scheduling rather than learned hazard.

EVIDENCE_DESIGN
Stage V-K0A — exact source qualification
Exposure
training                         none
optimizer steps                  zero
source states                    56 check states
focal rows                       112
legal joint edits                exhaustive
continuation horizon             5 primitive steps
random sampling                  none
V-K0A validity

Emit:

INVALID_RENEWAL_URGENCY_SOURCE_AUDIT

if any of the following occurs:

a supposedly identical initial state differs between KEEP and SET branches;

a branch crosses another high check;

a legal edit sequence is missing or duplicated;

same-label SET enters the legal support;

the fixed primitive table differs across branches;

non-external reward enters the return;

agent permutation changes the underlying source state rather than only relabelling it;

the full action-support maximization is not exhausted.

V-K0A acceptance

Emit:

TOY_HETEROGENEOUS_RENEWAL_URGENCY_IDENTIFIED

only if all of the following hold:

every fast-only transition has one U
src
>0.5 focal and one U
src
<0.5 focal;

every joint slow-plus-fast transition has two U
src
>0.5 focals;

both anonymous slot permutations produce the same unordered urgency values;

each physical slot occupies both classes somewhere in the panel;

no row lies exactly on the 0.5 boundary.

Otherwise emit:

TOY_HETEROGENEOUS_RENEWAL_URGENCY_NOT_IDENTIFIED

This is a valid source result, not an implementation failure, provided the validity checks passed.

V-K0B does not launch unless V-K0A identifies the source.

Stage V-K0B — unrestricted R30
Training contract

Use the existing learned-KEEP toy configuration unchanged apart from the trace/analyzer hooks:

controller                      r30_fixed_clock_ar_edit
environment                     two_timescale_role_free_actions
fixed primitive executor        axis4_xy_v1
local observations              constant zero
high context                    registered direct centralized state
training seeds                  2026080101–2026080106
environment steps per seed      640,000
parallel environments           16
rollout length                  40
outer updates                   1,000
high PPO epochs                 3
high learning rate              1e-3
low-level optimizer             absent
external reward only            yes
checkpoint read                 final checkpoint only
early stopping                  none
adaptive expansion              none

The existing configuration already fixes the 640,000-step, 16-environment, 1,000-update learned-KEEP attempt and removes the low-level optimizer and every intrinsic/shaping path.

Record actual, rather than nominal:

environment interactions;

high-check sequences;

agent tokens;

high actor/value optimizer steps;

low optimizer steps;

invalid/aborted batches.

A run whose actual exposure differs is invalid rather than rescaled.

Held-out evaluation

For each training seed:

episodes                         64
episode length                   40
updates during evaluation        zero
evaluation seed bank             one frozen common bank for all training seeds
agent order                      32 canonical + 32 reversed
noninitial check-agent rows      64 × 7 × 2 = 896 maximum
counterfactual candidate volume  2 select + 2 evaluate

The evaluation seed bank and every counterfactual seed must be derived from a new frozen contract namespace, not selected after checkpoint inspection.

The reverse agent order is required because the environment is role-free but R30’s autoregressive roster contains identity-indexed prefix features. The result must therefore show that access is not confined to one canonical slot ordering. The source itself is explicitly anonymous.

Support floor

Each of the six training seeds must contribute at least:

192 oracle-URGENT eligible rows
192 oracle-STABLE eligible rows
64 rows of each class under each agent order

Rows on the 0.5 oracle boundary are retained in the artifact but excluded from the binary urgency comparison.

Failure is:

R30_URGENCY_TRACE_SUPPORT_INSUFFICIENT

It is not a zero effect.

Competence floor

The equal-training-seed-weighted one-sided 95% lower bounds must satisfy:

LCB
95
	​

(slow_match)>0.75,
LCB
95
	​

(fast_match)>0.75.

The same direction must hold separately under canonical and reversed agent order.

Failure is:

R30_TOY_ACCESS_NOT_ESTABLISHED

No source conclusion is retracted; only the learned carrier remains unjudged.

The 0.75 competence floor is already the explicit architectural-access floor in the toy configuration, where zero local observations make centralized state necessary.

Inference

Do not treat check rows or episodes as independent top-level samples.

Use:

top inferential unit       training seed
nested unit                evaluation episode
within-episode unit        paired check-agent counterfactual
training-seed weighting    equal
bootstrap iterations       10,000, one frozen seed

Resample training seeds first, then episodes within each selected seed. All quantities from one bootstrap iteration must share the same seed/episode indices where their covariance matters.

Stable equivalence uses two one-sided 95% tests against ±0.5. Equality at a boundary is unresolved.

V-K0B primary gates

Define:

Δ
λ
	​

=E[1−p
KEEP
	​

∣URGENT]−E[1−p
KEEP
	​

∣STABLE].
Opportunity access

Pass only if, pooled and separately under both agent orders:

LCB
95
	​

(E[U
opp,π
∣URGENT])>0.5,
UCB
95
	​

(E[U
opp,π
∣STABLE])<0.5,
LCB
95
	​

(E[U
opp,π
∣URGENT]−E[U
opp,π
∣STABLE])>0.5.
Natural access

Pass only if:

LCB
95
	​

(E[U
nat,π
∣URGENT])>0.5,

the two one-sided equivalence tests place

E[U
nat,π
∣STABLE]

inside (−0.5,+0.5), and

LCB
95
	​

(Δ
λ
	​

)>0.

The realized natural SET-rate contrast must also be positive in point estimate and reported with its interval; the propensity contrast is primary because it is not inflated by one sampled Bernoulli token.

Replacement-skill diagnosis

Report U
SET,π
 with the same urgent/stable bounds. It is diagnostic rather than a separate required source gate:

opportunity passes but sampled SET fails → skill-selection failure;

both fail → broader continuation/action access failure.

First-match result system
Precedence	Result
1	INVALID_VARIABLE_K_URGENCY_AUDIT
2	TOY_HETEROGENEOUS_RENEWAL_URGENCY_NOT_IDENTIFIED
3	R30_URGENCY_TRACE_SUPPORT_INSUFFICIENT
4	R30_TOY_ACCESS_NOT_ESTABLISHED
5	SOURCE_IDENTIFIED_R30_OPPORTUNITY_NOT_ACCESSED
6	SOURCE_IDENTIFIED_R30_NATURAL_ALIGNMENT_WRONG_DIRECTION
7	SOURCE_IDENTIFIED_R30_NATURAL_ALIGNMENT_UNRESOLVED
8	HETEROGENEOUS_URGENCY_AND_R30_NATURAL_ACCESS_IDENTIFIED

WRONG_DIRECTION requires an upper confidence bound at or below the corresponding zero/materiality boundary. Merely failing a lower-bound gate is UNRESOLVED.

There is:

no seed expansion
no budget expansion
no checkpoint selection
no threshold adjustment
no rerun after a valid unresolved or negative result

Operational corruption may be rerun at the identical contract.

What follows a pass

Only result 8 schedules the fixed-period anchor study.

That later anchor must use true shared deterministic periods, not the default legacy duration catalogue. On this toy there are only eight offered checks, so the natural candidate family is the complete shared-period set:

k
shared
	​

∈{1,2,3,4,5,6,7,8} checks,

equivalently 5 through 40 primitive steps.

The best shared period must be selected on a disjoint validation bank and read on a held-out test bank. Unrestricted R30 uses the same information, primitive executor, training interactions, and high-level optimizer budget. legacy_duration may be included only as the already registered sampled-duration bias diagnostic.

No constrained renewal-class mechanism is selected by this ruling.

CORRECTIONS
1. The R31–R33 statement in RESEARCH_GOAL.md is stale as scientific status

The dashboard is unambiguous:

R31 is a valid FAIL and retired;

R32 is a valid FAIL and retired;

R33 is a valid FAIL and retired;

R33’s “R30 safety PASS” is a subordinate safety observation inside a failed IRSC mechanism gate, not positive evidence that R30 learned renewal urgency;

the R30 fixed-clock paired 320K run was stopped and superseded before completion, with no M1–M4 scientific outcome.

Therefore none of R31–R33 supplies a positive variable-k anchor for this design. The reusable fact is narrower: R30 existed as a functioning carrier in those pipelines.

The goal document’s critical-path statement remains current; its historical “anchored R31–R33” sentence should not be used as evidence.

2. (3,7,13,24) is not the fixed-k arm this toy should complete

The tuple is the standalone package’s default legacy duration-candidate catalogue, expressed in high-level intervals for long-horizon Scenario 7. R30 itself does not choose from it. The current toy config overrides it to (1,2) even though the learned-KEEP R30 carrier obtains lifetime through repeated KEEP decisions.

Consequently B3’s proposed “complete the (3,7,13,24) fixed-k arm” conflates:

a sampled-duration comparator;

a true shared deterministic period;

and an unrestricted KEEP/SET policy.

Values 13 and 24 also exceed the toy’s eight offered checks and would largely be episode-censored. They are not an admissible definition of “best shared fixed k” here.

3. Fact 5 asks for more instrumentation than is necessary

A primitive-step, per-agent training trace is not required.

Renewal decisions occur only at offered checks. The smallest sufficient surface is:

one evaluation row per offered check per agent;

one five-reward vector per paired continuation;

explicit segment-ending authority.

The current update-level renewal summaries cannot recover KEEP decisions or age-conditioned hazard because they aggregate segment starts and synchronization statistics. That makes the new check-level trace necessary, but does not justify logging every primitive training transition.

4. The question hides two distinct intervention estimands

There are two scientifically different quantities:

a fixed-teammate direct focal effect;

the total focal effect under downstream autoregressive policy response.

The current R30 hook deliberately implements the second when only the focal token is forced: later agents observe the modified prefix.

The fixed-teammate effect may be reported, but it cannot establish the paper primitive on this role-free source. Coordinated role swaps are legal and can erase a direct-assignment cost. V-K0A therefore maximizes over the same joint action support, while V-K0B uses the deployed autoregressive continuation.

5. SMDP support being enabled is not evidence of access

use_smdp_discounted_high_return=True and use_smdp_bootstrap=True are genuine implementation facts.

They do not establish that:

the toy source is identifying;

R30 reaches competent histories;

its critic or actor orients renewal correctly;

or the natural hazard tracks U
i
	​

.

A failure in V-K0B may motivate a later credit/access localization, but credit instrumentation must not precede the source and access observation.

6. The direct centralized state is acceptable here, but becomes a matching obligation

The toy’s local observations are all zero, while the centralized state contains the changing targets and phases. The current R30 toy config deliberately supplies that state so the competence question is about renewal control rather than architectural blindness.

Any future constrained and unrestricted arms must receive the identical state, roster, age, and action support. A learned renewal class that receives less information would be an unfair negative; one receiving a slow/fast label would be an invalid positive.

7. A V-K0 pass remains a toy-carrier result

Even the strongest pass supports only:

This dense, fixed-N=2, supplied-executor toy contains anonymous state-dependent renewal urgency, and unrestricted R30 naturally aligns its KEEP/SET behavior with it under the registered shared check clock.

It does not support:

learned skill discovery;

low-level temporal abstraction;

variable membership;

join/leave/rejoin transport;

UAV relevance;

search-efficiency superiority;

or the low-cardinality contribution.

Those require the later anchors, constrained mechanism, held-out transfer, and variable-roster stages.

Convergence decision
SELECTED NOW
    V-K0A exact source-urgency qualification
    followed conditionally by
    V-K0B unrestricted-R30 natural-access screen

NOT SELECTED
    direct three-arm comparison
    constrained renewal-class design
    legacy (3,7,13,24) completion as fixed-k evidence
    UAV execution
    delayed-credit infrastructure work

CONDITIONAL NEXT
    true best-shared-period versus unrestricted-R30 anchors,
    only after source and natural access are identified

This ruling selects the scientific experiment and its result semantics. It does not itself authorize implementation or compute.