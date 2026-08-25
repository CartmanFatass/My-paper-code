1. Evidence validity and exact delta
Repository facts

The registered result is:

NO_ACCESS_BENCHMARK_ORDINARY_CONTROL

with:

implementation_valid = true
successor_selected = false

M0 integrity passed. The run recorded:

320,000 transitions per causal arm;

1,000 optimizer steps per causal arm;

4,000 training episodes per causal arm;

2,048 evaluation episodes per causal arm;

H/S zero optimizer steps;

zero skill updates, high updates, intrinsic reward reads, posterior reads, and new critics.

Engineering integrity:

replay errors: 0;

checkpoint round-trip error: 0;

anonymous relabeling valid;

parameter count matched at 14980.

The benchmark explicitly separates:

H: exact noncausal primitive authority ceiling;

S: exact noncausal shared renewal-clock ceiling;

C: calendar/membership-phase/recurrent-memory information removal arm;

D: ordinary recurrent primitive controller retaining online demand.

H audit

Facts:

H is a noncausal exact ceiling. It has full primitive authority and solves held-out ledgers through exact DP. The DP state is future-relevant local physical state, target streak, and previous command; it does not splice separately optimal tracking and completion paths.

Result:

H tracking = 0.7961

H completion = 1.0

H utility = 0.8923

Interpretation:

H proves:

The benchmark is not trivially impossible under unrestricted primitive authority.

H does not prove:

learned hierarchy;

learned skills;

useful abstractions;

deployable causal policy.

S audit

Facts:

S is a noncausal restricted controller:

command changes only every four steps or at genuine JOIN/REJOIN;

otherwise command is held;

absence freezes command.

Result:

S tracking = 0.6809

S completion = 0.7070

S utility = 0.6932

The held-out H-S gap is large:

utility CI95:
[0.1963, 0.1991, 0.2018].

Interpretation:

S demonstrates that a shared four-step renewal restriction loses capability on this task.

It does not identify:

why;

whether learned skills solve it;

whether event abstraction is required.

C audit

Facts:

C removes current demand/error fields while preserving:

time;

roster size;

membership events;

previous command/run;

recurrent state;

active-set communication;

primitive AR prefix.

Its paired construction guarantees equal observations, order, uniforms, action tapes, and hidden states for sign mates.

Result:

held deterministic tracking: 0.5

completion: 0.4328

utility: 0.4636.

Interpretation:

C indicates that removing online demand/error information destroys causal access.

It does not prove:

a hierarchy is needed;

skills are the missing information;

temporal abstraction is required.

D audit

Facts:

D is the existing direct recurrent primitive controller. It keeps current online demand information. The architecture remains the ordinary primitive AR factorization:

member encoder;

active-set sum/count context;

lifecycle GRU;

primitive action head;

centralized critic.

Result:

IID:

utility 0.6262

Held deterministic:

utility 0.6163

Held stochastic:

utility 0.4815.

The deterministic D gain over C:

utility CI95:
[0.1321, 0.1527, 0.1732].

Interpretation:

D proves:

Ordinary recurrent primitive control can learn some causal access from online demand.

D does not prove:

it is sufficient for final variable-lifetime capability;

hierarchy is unnecessary;

skills have no value.

2. Two-to-four-candidate causal portfolio
Candidate A — Ordinary recurrent access is the main missing capability

Mechanism:

The benchmark difficulty may mainly be online demand tracking. C fails because information was removed; D succeeds because it retains causal fields.

Evidence:

C loses access;

D recovers substantial held-out performance.

Unknown:

Whether explicit temporal abstractions add anything after D has solved online access.

Strong contradiction:

A learned hierarchical controller with matched information does not improve over D.

Candidate B — Benchmark requires temporal persistence, but not learned skills

Mechanism:

The task may require maintaining commands across heterogeneous durations, but this can emerge as recurrent memory rather than explicit skill objects.

Evidence:

S restriction hurts;

D has recurrent state and improves.

Unknown:

Whether recurrent state is merely implementing implicit persistence or whether explicit skill commitments provide additional value.

Strong contradiction:

A primitive recurrent policy fails on duration-shift tests while a skill-based policy succeeds.

Candidate C — Explicit commitment/event abstraction is required

Mechanism:

Primitive actions every step may be insufficient for long-lived heterogeneous behaviors. A higher-level commitment layer could reduce temporal credit burden.

Evidence:

Only indirect:

S limitation;

variable-duration design motivation.

Missing:

learned executor;

learned skills;

hierarchy comparison.

Strong contradiction:

Matched direct recurrent control remains equal on unseen duration and membership conditions.

Candidate D — Benchmark still has hidden construction artifacts

Mechanism:

Although calendar effects were removed, other task-generation assumptions may simplify the problem:

finite-state dynamics;

discrete thrust;

target-flip structure;

terminal-only reward;

deterministic membership ledger patterns.

Evidence:

Task is deliberately controlled:

horizon 80;

local state clipped;

binary targets;

segment durations from fixed sets.

Strong contradiction:

Performance remains stable under broader task families while preserving the same information boundaries.

3. Benchmark versus learner diagnosis
Sparse terminal credit

Fact:

Reward is zero for steps 0–78 and only pays utility at step 79.

Possible implication:

Credit assignment remains difficult.

But:

D successfully learns partial access, so terminal sparsity alone cannot explain all failure.

Model/data-flow limits

Fact:

C and D share the same PPO factorization, model size, and optimizer contract.

Inference:

Large differences are less likely to come from architecture capacity alone.

Still unresolved:

Whether D's representation is sufficient for the final research target.

Direct action factorization

Fact:

D predicts primitive actions directly.

Possible limitation:

Primitive action factorization may force long temporal structures into recurrent hidden state.

Possible alternative:

Explicit commitment variables may simplify the learning problem.

Not established:

That skills are necessary.

Task construction

The benchmark removes obvious calendar shortcuts:

future duration;

future target;

future membership;

future order;

action randomness

do not enter causal networks.

However:

A finite-state benchmark can still be easier than the final target.

Genuine temporal abstraction need

Current evidence:

S demonstrates shared renewal restriction is harmful.

D demonstrates online primitive control works.

Missing:

A comparison where:

direct recurrent control;

commitment abstraction;

learned skills

face identical information and held-out lifetime shifts.

4. Replacement and simplification ledger
Candidate	Retain	Delete	Replace	Minimal addition
A: direct recurrent	active roster, anonymous lifecycle, PPO contract	hierarchy assumptions	high-level abstraction removed	none
B: recurrent persistence	lifecycle state, demand fields, recurrent hidden	explicit skill interpretation	skill semantics reduced to memory	duration-shift evaluation only
C: commitment abstraction	event ownership, active masks, physical/event clocks	primitive-only action decisions	primitive control replaced by commitments	explicit commitment state
D: benchmark reformulation	information boundaries, anonymous membership	simplifying task assumptions	harder demand/lifetime structure	new task family, not new model

No candidate requires:

intrinsic reward;

posterior;

identity;

role;

graph;

team latent.

5. Strongest ordinary-MARL reduction

The strongest reduction is not a weaker synchronous MARL baseline.

It should be:

Information-matched primitive recurrent active-set controller

Requirements:

same observation fields as hierarchy;

same membership semantics;

same communication budget;

same recurrent memory;

same optimizer exposure;

same checkpoint contract.

Current D is close but still needs careful interpretation.

A hierarchy claim requires:

U
hierarchy
	​

>U
matched direct recurrent
	​


under:

unseen durations;

unseen membership schedules;

held-out tasks.

Current D advantage over C only establishes access from online demand.

Intrinsic boundary:

Any intrinsic mechanism must remain:

environment agnostic;

independent of task success;

independent of identity/role;

independent of future information.

6. Variable membership and lifetime semantics
Membership

Repository facts:

Membership uses opaque routing keys.

Keys, ranks, epochs, identities and roles do not enter model inputs.

Lifecycle rules:

JOIN initializes physical and recurrent state to zero;

temporary absence freezes physical state, demand active-time, command and hidden state;

REJOIN restores and increments epoch;

terminal LEAVE deletes state after finalization.

Interpretation:

The lifecycle contract is strong.

It does not prove learned lifetime semantics.

Clocks

Must separate:

physical time;

membership event time;

command persistence time;

learning credit time.

Current benchmark tests heterogeneous duration structure through segment durations:

training/IID {5,9,13};

held-out {5,7,9}.

Unknown:

Whether the controller learns reusable lifetime abstractions or simply adapts recurrently.

Lifetime boundary

A learned lifetime claim requires:

learned commitment behavior;

heterogeneous realized durations;

held-out duration robustness;

causal benefit over direct recurrence.

S/H separation alone is not lifetime evidence.

7. Literature principles, not imports
ACAC

Compatible principle:

separate physical-time discount from event depth credit.

Conflict:

fixed roster assumptions.

ACE

Compatible:

asynchronous readiness concepts.

Conflict:

fixed capacity and incomplete dynamic roster semantics.

InforMARL

Compatible:

permutation-compatible active-set representation.

Conflict:

fixed configuration scaling is not episode-internal membership.

Sable / large-agent systems

Compatible:

capacity considerations.

Conflict:

large fixed populations are not dynamic lifecycle ownership.

Field/mean-field approaches

Compatible:

population summaries.

Conflict:

averaging may erase rare critical members.

General principle:

Do not stack:

graph + field + latent + communication + skill + hazard

without identifying the missing causal edge.

8. Separating evidence candidates
Evidence A — Matched direct versus commitment abstraction

Comparator:

D primitive recurrent;

explicit commitment controller.

Estimand:

Held-out utility and sample efficiency under identical information.

Branches:

direct wins → temporal abstraction unnecessary;

commitment wins → abstraction has value;

both fail → access problem.

Portfolio update:

Separates B/C from D.

Prohibited:

No intrinsic reward or task shaping.

Minimal boundary:

Only one abstraction variable changes.

Evidence B — Lifetime generalization test

Comparator:

Same controller classes under:

seen durations;

unseen durations;

altered membership timing.

Estimand:

Performance degradation under duration shift.

Branches:

all methods degrade equally → no lifetime abstraction evidence;

commitment method retains performance → possible abstraction benefit;

direct wins → recurrent memory sufficient.

Portfolio update:

Tests whether lifetime is truly load-bearing.

Prohibited:

No learned hazard or duration reward.

Minimal boundary:

Change evaluation distribution only.

Evidence C — Information ablation decomposition

Comparator:

D with subsets of observation fields.

Estimand:

Contribution of:

demand;

error;

membership;

recurrent state.

Branches:

demand dominates → benchmark is online control;

recurrence dominates → memory;

neither → representation issue.

Portfolio update:

Separates learner limitation from task information.

Prohibited:

No new architecture.

Minimal boundary:

Read-only analysis or matched ablation.

9. Unselected ideas and stop conditions
Useful but unselected ideas

Learned event hazard

Useful only if:

lifetime itself is a causal object;

survival modeling is required.

Currently not justified.

Skill semantics

Still possible.

But requires:

learned executor;

natural usage;

intervention-resistant behavior;

advantage over direct recurrence.

Sparse communication / graph representations

Potentially useful for larger N.

Not justified by current evidence.

Stop conditions

Retire explicit hierarchy claims if:

matched direct recurrent control equals hierarchy;

lifetime shifts do not expose hierarchy advantage;

skills are only labels for primitive actions.

Retire benchmark if:

all methods exploit hidden finite-state assumptions;

no learner distinction remains after task hardening.

Retire temporal abstraction if:

recurrent memory solves unseen lifetime and membership changes.

Retain hierarchy research only if:

learned commitments provide external capability beyond ordinary recurrent control;

not because H/S ceilings differ;

not because supplied primitives work;

not because a skill label exists.

Current evidence establishes:

a valid noncalendar benchmark;

ordinary recurrent access;

shared-clock limitation;

remaining ambiguity around whether explicit temporal abstraction is necessary.

It does not establish learned hierarchy, learned skills, or variable-lifetime capability.
