# MARL Empirical Evidence and Claim-Burden Specification

## 1. Purpose

This specification calibrates HMASD evidence requirements to the scientific practice of deep
multi-agent reinforcement learning (MARL). MARL mechanisms are often motivated by a structural
argument, an RL principle, or a diagnostic counterexample and then assessed empirically. A general
convergence, optimality, or generalization theorem is valuable when available, but it is not the
default admission condition for implementing or evaluating an algorithm.

Rigor is proportional to the claim. The project must not demand deployment-grade proof from a toy
mechanism study, and it must not present a toy result as evidence of deployment safety or general
MARL superiority.

This document specializes the A/B/C evidence burdens in
`docs/project/ALGORITHM_PRINCIPLES.md`. If a direction document asks for a stronger burden, that
stronger burden applies only to the named claim or object; it does not silently become a global MARL
standard.

## 2. Normative terms and scientific units

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` are normative. A justified departure from a `SHOULD` is
allowed when its effect on the claim ceiling is stated.

- **Direction**: a portfolio-level research programme that may contain several hypotheses,
  mechanisms, implementations, and studies.
- **Mechanism hypothesis**: a falsifiable account of how information, representation, credit,
  optimization, coordination, or control should change behavior.
- **Exploratory study family**: an adaptive sequence used to discover, debug, bound, or revise a
  mechanism. It is not a one-shot confirmatory object.
- **Frozen confirmatory object**: one prospectively fixed comparison with a population, estimand,
  comparator, budget, stopping rule, decision rule, and interpretation boundary.
- **Evidence attempt**: one execution intended to observe an object. An incomplete, corrupted, or
  nonconforming attempt is not a scientific result.
- **Claim ceiling**: the strongest statement that the collected evidence can support.

A negative result updates the smallest implicated unit. Failure of one implementation, host,
benchmark-comparator pair, or frozen object does not automatically close its mechanism hypothesis
or direction.

## 3. Evidence-burden classes

Use the smallest class able to answer the current decision question.

| Class | Purpose | Adaptation | Maximum default claim |
| --- | --- | --- | --- |
| **A — RECON** | Engineering/evidence reconnaissance and read-only probes | Adaptive | A path, implementation fact, access fact, or measurement fact; no algorithm effect |
| **B — EXPLORE** | Mechanism discovery, debugging, toy learnability, ablation scouting, variance and failure-mode discovery | Adaptive between named runs | Preliminary signal or counterexample on the observed setup; hypothesis-generating, not stable superiority |
| **C-BENCH — BOUNDED_BENCHMARK** | A conclusion-bearing comparison on a fixed toy or benchmark population | Frozen final evaluation after development/tuning | Bounded competence, component effect, or comparative performance on the declared population |
| **C-TRANSFER — SIM_TRANSFER** | Robustness or transfer across held-out tasks, scenarios, disturbances, populations, or UAV simulator conditions | Frozen held-out evaluation | Transfer/robustness only over the declared simulator distribution |
| **C-FORMAL — FORMAL_SAFETY** | Universal, exact, invariant, safety, deployment, or otherwise high-consequence claims | Frozen; proof/certificate obligations follow the claim | Only the exact theorem, invariant, safety envelope, or deployment claim checked |

`C-BENCH`, `C-TRANSFER`, and `C-FORMAL` are all conclusion-bearing C work. They are distinct because
their admissible claims and evidence obligations are not interchangeable.

## 4. Common integrity requirements

Every class MUST:

1. state the question, intended claim ceiling, and material non-goals;
2. identify the actual algorithm, environment or evidence path, and relevant comparator;
3. preserve direct observations, including null, unstable, and adverse outcomes;
4. distinguish environment interaction from optimizer-update and model-selection exposure;
5. report material implementation, precision, RNG, checkpoint, leakage, and side-effect changes;
6. treat an engineering or instrumentation failure as limiting the dependent observation; a
   separate direct fact remains reportable when it is independently trustworthy; and
7. bound interpretation to the population, information set, resource budget, and measurement that
   were actually observed.

Theoretical support SHOULD identify a plausible mechanism, its assumptions, a differentiating
prediction, and a credible simpler explanation or containing null. A general mathematical proof is
required only when the claim itself is general, exact, invariant, safety-critical, or otherwise
cannot be supported by bounded empirical evidence.

An exact lemma, finite counterexample, census, or proof is preferred when it is the cheapest
decision-relevant discriminator. It MUST NOT become a ritual prerequisite that delays a ready
algorithm experiment without changing the decision.

## 5. Class-specific requirements

### 5.1 A — RECON

A run or read-only probe MAY use a single seed or instance when that is sufficient to inspect a
path, reproduce a defect, or establish access. It MUST NOT be cited as an algorithm effect.

### 5.2 B — EXPLORE

B is the default early algorithm-research mode. The EM MAY revise architecture, hyperparameters,
reward-independent mechanism details, host, budget, measurement, and comparator between named runs
after seeing earlier results. Each material change and its reason MUST be recorded. Earlier nulls
and failures remain visible.

- One to three seeds can be sufficient for debugging or mechanism scouting.
- Three to five seeds can estimate preliminary direction and obvious instability.
- These counts do not by themselves support stable-performance, general-superiority, transfer, or
  retirement claims; they are defaults, not universal gates.
- A B run MUST exercise the real environment, policy, learner, trainer, and evaluator and report
  nonzero transition, update, and evaluation counts when it is called an algorithm experiment.
- Outcome-informed adaptation is legitimate exploration. It MUST NOT be relabelled as prospective
  confirmation.

A B result may justify implementation investment, a better discriminator, a bounded benchmark
study, or retirement of a narrow conjecture contradicted by direct evidence. It does not by itself
retire a direction.

A single trustworthy, meaningfully comparable observation may justify bounded follow-up under
§11.8; prior statistical significance or positive replication is not required. Training-seed
variation and evaluation noise are distinct; more episodes on one checkpoint do not add training runs.

### 5.3 C-BENCH — BOUNDED_BENCHMARK

Development and hyperparameter selection MUST be separated from the frozen final evaluation when
the study makes a conclusion-bearing claim. This separation is not a prerequisite for B
exploration.
Before final evaluation, freeze the treatment, competent comparator, task population, training and
evaluation budgets, primary estimand, checkpoints or selection rule, stopping rule, uncertainty
method, decision rule, and interpretation boundary.

The following are defaults rather than universal admissibility gates:

- plan approximately ten independent training runs for a direction-level comparative claim;
- five independent training runs may support a provisional, single-task bounded comparison when
  cost and observed variance justify it, but the reduced certainty must be explicit;
- use enough independent evaluation episodes to make evaluation noise subordinate to training
  variation; 32 episodes per evaluation point is a useful starting default when feasible;
- report individual runs and learning curves, not only the best seed or terminal mean;
- report a 95% uncertainty interval for the primary aggregate;
- across multiple tasks, prefer robust aggregates such as interquartile mean with stratified
  bootstrap intervals, performance profiles, and probability of improvement; and
- tune credible baselines fairly and report environment steps, optimizer exposure, model-selection
  exposure, and material compute differences.

Seed and episode counts SHOULD be increased when variance is high or the claimed margin is small.
They MAY be reduced for deterministic enumeration, very expensive systems, or a deliberately
provisional claim, but the claim ceiling must fall with the evidence.

A toy or benchmark result supports only the declared environment/task distribution. It may show
that an algorithm can learn, that a mechanism has an identifiable effect, or that it outperforms
named baselines under a fixed contract. It does not establish broad MARL generality, real-UAV
performance, safety, or deployment readiness.

### 5.4 C-TRANSFER — SIM_TRANSFER

Transfer evidence MUST add decision-relevant variation rather than repeat one favorable host. As
applicable, it SHOULD include:

- multiple scenarios and independently held-out tasks, maps, team sizes, or agent populations;
- dynamics, observation, sensor, communication, delay, dropout, and disturbance variation;
- competent baselines under matched information and work exposure;
- success, return, constraint violation, failure, and tail-risk metrics;
- independent training seeds and uncertainty reporting; and
- a prospectively declared rule for scenario aggregation and model selection.

Evidence on a UAV simulator supports only the declared simulator and perturbation population.
Claims about physical deployment additionally require a system-specific sim-to-real, safety,
validation, and operational assurance programme; MARL benchmark performance cannot substitute for
that programme.

### 5.5 C-FORMAL — FORMAL_SAFETY

Use C-FORMAL only when the claim requires it, including an exact invariant, universal containment,
convergence under stated assumptions, certified safety envelope, bit identity, or deployment-grade
assurance. Proof obligations, exhaustive support checks, formal certificates, and exact numerical
semantics MUST correspond to the stated claim.

A formal result does not establish practical learnability or performance unless those properties
are part of the theorem and its assumptions match the evaluated system. Conversely, lack of a
general theorem does not invalidate a bounded C-BENCH or C-TRANSFER result.

## 6. Iteration, failure, and consumption

### 6.1 Exploration is not one-shot

A and B objects have no one-shot consumption state. Repetition, repair, tuning, and
outcome-informed revision are expected when they answer a named uncertainty. Repeated execution
without a replication purpose, repair, or changed discriminator is low-value, but it is not an
integrity violation.

### 6.2 What consumes a confirmatory object

Only a valid, complete observation of an explicitly frozen C object consumes that exact object.
Consumption means that its prospective decision rule cannot be rewritten after the result; it does
not ban further research on the mechanism or direction.

The following do **not** consume a C object:

- failed or missing resource admission;
- absent prospective instrumentation needed by the estimand (optional resource telemetry alone
  does not invalidate a non-resource claim);
- code that does not conform to the frozen algorithm/comparison;
- truncated, corrupted, or unobserved output;
- leakage, RNG, checkpoint, precision, or evaluator defects that invalidate the estimand; or
- infrastructure and transport failures.

After repair, an outcome-blind fresh attempt MAY implement the unchanged C object. The invalid
artifact must be quarantined and cannot be interpreted as a complete result or salvaged for the
dependent claim. Independently trustworthy direct measurements from the same attempt may remain
visible at their narrower ceiling.

### 6.3 Learning after a valid result

A valid C result remains attached to its frozen meaning. It cannot be rescued or reversed by a
post-hoc seed, budget, metric, threshold, model, comparator, or population change. It MAY motivate:

- a new B study family;
- a new, transparently outcome-informed C object with a materially different estimand, comparator,
  support law, intervention, or decision rule; or
- a narrower or recast mechanism hypothesis.

The new object does not erase the old observation. Its motivation may use earlier outcomes while
new training random streams remain independent. Disclose adaptive design and selection; distinguish
fresh independent training evidence from reuse of observed data. Confirmation requires an applicable
prospectively fixed evaluation and analysis, not a motivation uninfluenced by prior research.

## 7. Lifecycle implications

Portfolio lifecycle is about a direction, not the fate of one run.

- **ACTIVE**: at least one valuable, executable, tier-appropriate next object can change a portfolio
  decision, and current investment is justified.
- **PARKED**: a plausible valuable question remains, but there is currently no sufficiently
  specified or feasible decision-relevant object, or a named dependency makes investment premature.
  PARKED does not mean that a theorem, permission, or user authorization is required unless that is
  the actual named dependency.
- **CLOSED**: no valuable independent question remains at any appropriate evidence class, the
  direction has been absorbed by another direction, the mechanism is structurally impossible or
  equivalent, or sufficient independent bounded evidence makes further investment dominated.

Absence of a general proof, exact support census, bit identity, real-UAV validation, or deployment
assurance is not by itself a reason to PARK or CLOSE an empirical MARL direction whose current claim
is B or C-BENCH. A failed C object closes that object. Broad direction closure normally needs a
structural contradiction/equivalence, several independent decision-relevant failures, absorption,
or a portfolio value judgment that no narrower or recast object merits investment.

## 8. Responsibility split

### 8.1 Portfolio / Root

Portfolio MUST:

1. identify the decision question and assign the lowest sufficient evidence class before investing;
2. compare directions at their honest claim ceilings rather than reward those with the most formal
   artifacts;
3. prioritize real algorithm implementation and bounded empirical discrimination when the project
   goal is performant MARL, unless the proposed claim itself requires formal work;
4. distinguish `CLOSE_OBJECT`, `PARK_DIRECTION`, `CLOSE_DIRECTION`, fusion, and absorption;
5. refuse to infer direction polarity from technical failure or missing formal evidence outside the
   selected class;
6. require transfer or safety evidence only before making the corresponding transfer or safety
   claim; and
7. state the evidence class, claim ceiling, contrary result, and smallest next investment in every
   material lifecycle packet and decision record.

When an external scientific consultation applies a stronger class than the stated claim requires,
Portfolio must treat the mismatch as an unresolved methodology issue and seek a class-corrected
answer. It must not convert the mismatched standard into a scientific negative.

### 8.2 Evidence / Experiment Manager

EM MUST:

1. declare the class, question, claim ceiling, non-goals, and promotion criterion at the start of a
   study;
2. use theory to clarify mechanism and differentiating predictions without demanding a general
   theorem for bounded empirical work;
3. iterate transparently in A/B and separate tuning/development from C evaluation;
4. design fair comparators, work/information parity, uncertainty reporting, and held-out evaluation
   in proportion to the selected class;
5. distinguish an invalid attempt, a failed implementation, a failed benchmark-comparator object,
   and a refuted mechanism proposition;
6. preserve every valid result at its original meaning while permitting explicitly new follow-up
   objects;
7. ask CM for the performance and instrumentation implementation required by the selected class,
   not for unrelated proof machinery; and
8. recommend lifecycle consequences at the smallest supported unit and state what evidence would
   justify promotion, parking, recasting, or closure.

EM MUST NOT recommend PARK or CLOSE solely because a deep MARL mechanism lacks a general
convergence/optimality theorem. It may recommend C-FORMAL work only when the target claim or a
decision-relevant failure mode requires it.

## 9. Minimum study record

Every evidence note or assignment should make the following discoverable without imposing a new
machine-readable status protocol:

- evidence class and claim ceiling;
- question, non-goals, mechanism prediction, and strongest live alternative;
- candidate, competent comparator, information/work exposure, and environment population;
- development/tuning boundary and, for C, the frozen final-evaluation contract;
- seeds, episodes, transitions, updates, selection exposure, compute, and uncertainty method as
  applicable;
- direct result, validity, limitations, and smallest scientific update; and
- next promotion, repair, discriminator, recast, park, or closure condition.

## 10. Methodological basis

This calibration is consistent with established deep-RL and MARL practice: algorithms such as
[MADDPG](https://arxiv.org/abs/1706.02275),
[QMIX](https://proceedings.mlr.press/v80/rashid18a.html), and
[MAPPO](https://arxiv.org/abs/2103.01955) combine bounded structural arguments with empirical
evaluation rather than a general deep-MARL convergence proof. Reproducibility and uncertainty
requirements follow the concerns in
[Deep Reinforcement Learning That Matters](https://ojs.aaai.org/index.php/AAAI/article/view/11694),
[Deep RL at the Edge of the Statistical Precipice](https://arxiv.org/abs/2108.13264), and the
[cooperative MARL evaluation protocol](https://papers.nips.cc/paper_files/paper/2022/file/249f73e01f0a2bb6c8d971b565f159a7-Paper-Conference.pdf).

These sources justify stronger empirical reporting, not a universal demand for formal proof. Exact
guarantees remain appropriate for deliberately restricted theoretical objects whose assumptions and
claim boundaries are explicit.

## 11. Owner calibration for exploratory directions (2026-09-02)

This section records a calibration agreed with the repository owner on 2026-09-02, after the
first-wave independent review found that contracts written for C-class claims were being applied to
B-class runs and that formal obligations were blocking launches without changing any decision. It
was written by Claude at the owner's request and is normative for every direction whose current
claim ceiling is B or C-BENCH. Where a `DIRECTION.md`, science card, or contract asks for more than
this section for a B or C-BENCH object, this section prevails unless the owner names the stronger
burden for that specific object in writing.

### 11.1 Research order: inspiration, then experiment

MARL mechanisms in this project are discovered by the following order, and the evidence class
follows the order rather than preceding it:

1. **Inspiration model.** A bandit, single-agent, or closed-form toy that isolates one quantity and
   yields a one-sentence prediction. It has no evidence class and no consumption state. Its purpose
   is to say what to try first and what to measure.
2. **B — EXPLORE ladder.** One-to-three-seed runs on the real learner, changed between named runs
   as the results suggest, with each change and its reason recorded. B is the default early mode
   (§5.2) and is entered directly from an inspiration model.
3. **C-BENCH** when a conclusion-bearing bounded comparison is justified by the claim, with its
   independent runs and uncertainty chosen for the task, variance, margin and cost. A repeatable
   B signal is useful evidence for promotion, but three to five seeds is not a universal gate.

Confirmatory contracts and consumption semantics apply to their declared C objects. Oracle-retuned
comparators and held-out transfer splits (train-k / test-k′, train-N / test-N′) apply only where the
specific claim needs them, not to every C-BENCH. External preregistration is not a universal duty.
These MUST NOT be launch conditions for A or B objects. A B object MAY be planned with them in mind,
but their absence never blocks a B launch and never lowers a B result below its §5.2 ceiling.

### 11.2 Theory ceiling

No direction is required to prove permutation or roster invariance, duration-independent skill
semantics, semigroup consistency, an exact support census, an exact equality theorem, or bit
identity in order to run or promote a B or C-BENCH object. Such results MAY be pursued as optional
analysis; they are not admission conditions and their absence is not a reason to park.

The preferred theoretical product for a direction is a **suboptimality or error bound for the
scheme as implemented**: a bound on the gap between the implemented (possibly heuristic) scheme and
a stated optimum or oracle, in terms of the environment quantities the scheme is meant to handle.
Such a bound is C-FORMAL only if the paper claims it as a theorem; as an analysis attached to a
C-BENCH result it needs no proof obligation beyond stating its assumptions. Its assumptions MUST
match the implemented scheme; a bound derived for an idealized scheme MUST NOT be presented as a
property of a different implemented one.

Empirically better performance on the declared population, under fair comparators and the §5.3
reporting defaults, is a sufficient direction-level claim.

### 11.3 Suboptimal schemes are legitimate objects

A treatment does not have to be optimal, learned end to end, or invariant by construction. Fixed
duration menus with hazard-rate termination, sum-plus-count pooling with boundary-deferred
re-planning, canonical-sort presentation, and similar simple schemes are admissible treatments and
admissible comparators. A direction MUST NOT be parked or closed because its scheme is known to be
suboptimal; it may be parked or closed only under §7.

### 11.4 What may gate a B launch

Only the following may hold a B launch: the §4 common integrity requirements; the §5.2 requirement
that the real learner runs and reports nonzero transition, update, and evaluation counts; the
mandatory resource admission; and one machine-generated **exposure line** (parameter displacement
budget relative to initialisation scale, or an equivalent statement that the learner can move in its
budget). Nothing else, including hash chains, byte manifests, telemetry completeness beyond what
the run's own claim needs, capacity gates, formal-analysis flags, or prospective contracts, may
hold a B launch. The quarantine rule for incomplete attempts (§6.2) is unchanged by this section;
whether an instrumentation failure downgrades rather than annuls a run is a separate owner decision
not taken here.

### 11.5 Direction separation for the untying programme

Untying the skill duration k and untying the agent count N are **two separate directions**, not one
joint algorithm. Each holds the other quantity fixed as a stated parameter of its objects and
reports sensitivity to it where the bound in §11.2 depends on it. No joint variable-k-plus-variable-N
object exists unless the owner opens one.

### 11.6 Effect on existing obligations

Obligations of the following kinds, wherever they appear in direction documents for B or C-BENCH
objects, are demoted to optional analysis by this section: theorem-or-witness dichotomies as
registration conditions, exact equality theorems over all reachable training paths, byte-addressed
finite-action laws as conformance conditions for a B run, formal-analysis-bound flags that refuse a
complete learner chain, and capacity or consumer-recompute gates that do not change a B decision.
Direction owners SHOULD record the demotion in the direction's next intake rather than rewrite
historical documents.

### 11.7 Headroom, minimum effect of interest, and card description fields (2026-09-04)

Set by the owner on 2026-09-04 and revised the same day after Codex Root's review
(`docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`). Everything in
this section is a description field or a Portfolio comparison input under §8.1. Nothing here is a
launch condition, an exclusion rule, or a rewrite of a B result's polarity, and nothing extends
§11.4.

- **Headroom record.** A direction's headroom on a host is the gap between a stated upper
  reference (a DP or Bayes solution, an oracle with privileged information, or the best arm of a
  competent comparator sweep) and a tuned same-information generic baseline, both with seeds and
  curves. Computing it from existing results is A/RECON; training or tuning a baseline for it is a
  B object and is declared as one. Headroom is a diagnostic and a sequencing input: Portfolio
  proposals state each direction's record or its absence, and a missing record is a reason to
  sequence the measurement early, never a reason to stop investing.
- **Minimum effect of interest (MEI).** Each card declares its own MEI, absolute, relative to the
  baseline return, or both, with the DM's reason for the choice. There is no repository-wide
  value; a relative value alone is unsuitable where the baseline return is near zero, negative, or
  on a different scale from other hosts. The declared MEI informs Portfolio comparison across
  directions. The card's own result branches remain the reading rule for the result.
- **Reading narrative.** Every B card carries a short narrative field, "how the result will be
  interpreted": what an effect above the MEI, inside it, and of opposite sign would each suggest
  and what the DM would then recommend. It is descriptive intake text written early, not a frozen
  decision rule and not a pre-registered failure boundary; its absence never holds a launch.
- **Baseline set.** Tuned baselines are kept per host as reusable evidence packages, frozen
  result documents and runner configuration under `docs/research/baselines/<host>/` and
  `experiments/baselines/<host>/`. A direction reuses them when its observation, action,
  information and budget match, and otherwise records which of those does not; they are never a
  mandatory comparator. Paired seeds and common random numbers across arms are the default where
  the host allows.
- **Binding structure line.** A card's first two lines are its one-sentence claim and the MARL
  structure the DM holds responsible for the effect: (a) agent-count scaling or roster change,
  (b) temporal abstraction or termination, (c) multi-agent credit assignment, (d) other-agent
  non-stationarity or partial observability, or `systems / information flow`. The field is a
  classification. A `systems / information flow` entry excludes nothing; the DM adds one sentence
  on how the question arises from multi-agent partial observability or non-stationarity, or states
  that it does not.

Ladders already open on 2026-09-04 continue under their cards unchanged. The fields apply to
every card frozen after that date.

### 11.8 Exploration and publication burden calibration (2026-09-05)

This section is the final Portfolio Pro calibration for all ACTIVE directions. It removes defaults
that do not serve the current claim; it does not rewrite historical results, completed objects or
the named VNFC E01 appendix.

#### 11.8.1 Claim determines burden

B exploration asks whether a bounded next investment is worthwhile; a conclusion-bearing comparison
asks what performance judgment the declared population supports. Ordinary A/B/C-BENCH work does not
default to extreme tolerances, cross-platform element/bit equality, exhaustive mechanism explanation,
full historical replay, full intermediate-array publication or exact support census. Require one only
when the current claim depends on it or a concrete correctness risk requires it. Missing an exact upper,
tuned headroom or complete causal explanation does not block performance exploration.

#### 11.8.2 A credible signal supports bounded follow-up

One real execution with a trustworthy primary measurement and clear comparison meaning may support a
bounded B follow-up. It need not first be statistically significant, replicated on several seeds,
positive on every seed or mechanistically localized. This is an investment signal, not stable
superiority. A local or proxy improvement is reported as local; native-return losses, wrong actions
or unchanged complete competence remain alongside it. Outcome selection of the best seed, checkpoint,
metric or configuration must be disclosed.

Absence of improvement may also motivate a specifically justified new B change. A positive result
is neither a universal prerequisite for follow-up nor an entitlement to unlimited further compute.

#### 11.8.3 Independent training seeds

When the question is learning performance, prefer a small follow-up with one or two new independent
training seeds using the same comparison and evaluation. Choose more when variance, margin, task
population or claim requires it. Preserve every seed, failure, curve and exposure; do not run until
all signs are positive. Paired treatment/control seeds or common exogenous randomness are allowed
when declared, but repeated evaluation of one checkpoint, another fold on the same data, or more
rollouts is not a new training sample. Few seeds require per-seed outcomes and a limited uncertainty
statement; they cannot support a stable population claim by themselves.

The one-or-two-seed follow-up is an economical starting point, not a launch requirement or assurance
of statistical sufficiency. One training seed cannot estimate training-seed population uncertainty;
resampling units must respect shared data, folds and actual independence.

#### 11.8.4 Publication-stage claims

Paper-level performance claims require fair comparators, transparent development/checkpoint selection,
independent training and evaluation appropriate to the task, and uncertainty reporting. The values
10 runs, 32 evaluation episodes and 95% intervals are planning defaults, not universal laws. Three
to five seeds, all-positive seeds or one significance test alone never guarantees sufficiency.
Mechanism attribution, exclusion of a competitor, invariance, safety or exact claims require only the
interventions, ablations or proof that those stronger claims actually need. An unresolved mechanism
does not erase an independently measured performance fact; it narrows the wording.

#### 11.8.5 Three kinds of reproducibility

Deterministic numerical replay serves a code path, regression, numerical diagnostic or explicitly
exact semantic object, and is conditional on the stated execution boundary. Statistical replication
serves a learning-performance claim through independent training runs, per-run results, aggregate
effect and uncertainty; it does not require trace equality. Exact algorithm/semantic validation keeps
the integer, support, ordering, tie or applicable tolerance checks needed by that named object only.
Source SHA or input identity does not imply output bit equality. There is no project-wide `1e-12` or
other extreme tolerance. Select absolute/relative or decision-level checks from dtype, scale,
conditioning, accumulation and actual action/metric consequences. Near a decision boundary, checking
the affected action, order or return can suffice; an equivalence claim cannot be made if its required
semantic check fails.

#### 11.8.6 Proportionate verification

An ordinary B must run the real environment, policy, learner, trainer and evaluator; its transitions,
updates, evaluation and selection exposure and primary comparison must be readable, with reward,
information and budget semantics intact. Use existing trustworthy paths and checks where applicable.
Add one focused verification for changed behavior and primary output; do not repeat smoke merely because
a launch boundary occurred. Do not default to cross-platform solve, all-history replay, full arrays,
support census or mechanism diagnosis. Resource admission remains required for each actual invocation.

#### 11.8.7 Failure follows dependency

Report observed exception, exit, missing output and counts immediately. Root-cause attribution requires
direct evidence, but reproducing and uniquely locating every historical cause is not a universal
prerequisite for later work. Repair or check a defect that threatens reward, information access,
comparison, training or the primary measurement. A credible alternative path may proceed without
solving unrelated historical failures, with the non-dependence stated. A damaged primary measurement
cannot support its dependent performance claim; independently trustworthy narrower facts remain
reportable. A new B that does not use an old publication system does not inherit that system's full
replay obligation. These rules do not retroactively change quarantined artifacts.

#### 11.8.8 Engineering proportion and transition

For ordinary research changes, the 30% orchestration ratio is a review signal, not an automatic return,
budget ceiling or scientific-validity test. Reviewers identify unnecessary machinery, concrete risk and
impact; required I/O, serialization and parameter handling are judged by purpose and readability. Do
not pad computation, compress code or move wrappers to satisfy a denominator. Existing 2,000-line,
600-line-runner, test and resource budgets remain unless a named task changes them. Future A/B objects
may remove or adjust unneeded diagnostics in their card/task and state the claim impact; no separate
tolerance or ratio approval is needed. Existing records, failures and named tasks retain their original
meaning. The current VNFC E01 exact appendix remains unchanged; finished CBSC/N3 work and old UCOPE
attempt02 are not reopened by this calibration.

No new line-by-line orchestration census or 100-line exception application is required for this
ordinary rule. Explicitly labelled reanalysis may use a revised method if existing data support it;
it must acknowledge observed outcomes and cannot be reported as passing the old rule or as fresh
independent confirmation. Adjusting irrelevant diagnostic burden alone is not a mechanism recast.

### 11.9 Applying the method in questions and decisions (OWNER_DIRECT, 2026-09-05)

Select the question as well as its evidence burden proportionately. A performance exploration
does not need to establish the exact maximum of a policy class, complete headroom, or a unique
causal explanation before real training and sampled return comparison. Choosing an exact claim
does not itself justify studying it. Replacing a census with bounded, beam or best-of-many search
does not repair an unnecessary search-before-learning dependency. Search remains appropriate
when it has an explicit algorithmic or separately justified diagnostic purpose; a smaller search
budget alone is not that purpose. Ordinary action selection/optimization is not a prerequisite
search over policies or future trajectories.

Prompt authors and Pro compare the decision value and known dominant work of a proposed diagnostic
with a minimal real learning comparison or directly sampled measurement. Finite, deterministic or
zero-learner work is not presumed cheap. Discuss prospective work even when the consultation itself
runs nothing; unknown cost is not zero and does not demand a separate calibration experiment.
On cost refusal, reconsider the chosen question and necessary evidence as well as execution.
Moving a prohibited B prerequisite into a preceding A does not make it permissible.

Pro decisions are final within current owner instructions and applicable specifications. In the
existing intake, Root/DM cites any concrete conflict and returns it to the same node for correction
before executing the affected requirement, while independent conforming work continues. Preserve
the exact response and do not invent a substitute decision. Explicit specification exceptions name
the rule, scientific necessity and scope and follow existing appropriate-node authority. No silent
exception follows from response completeness, and no extra reviewer/approval/launch gate is added.

This owner-directed clarification changes future authoring and current decision intake; it does
not rewrite accepted request bodies, historical results or completed experiment assignments.

**Request complexity.** Before selecting a new experimental design, describe the dominant work
factors. This is a MARL empirical-research repository: the default performance path is implement,
train on a selected task/benchmark, compare with competent baselines, and assess repeatability with
independent training seeds as the claim warrants. Neither bounded nor exhaustive policy search
substitutes for that comparison or supplies a general prerequisite for it. A bounded search can
still be combinatorially expensive; its cost advantage over actual experiments must not be assumed.

Describe dominant work
factors in its existing question/card: arms, independent training seeds, environment steps,
evaluation checkpoints/episodes, and nested candidate/trajectory/controller/solver calls. Separate
work intrinsic to the proposed algorithm from verification added to study it. Joint-action growth
such as a^N, trajectory branching b^H, all subsets, full cross-products and per-candidate replanning
are reasons to reconsider the question and sufficient measurement, not just accelerate its code.
Smaller sampled empirical comparisons and removal of unnecessary dimensions are preferable when
they answer the decision with an honest narrower claim. Intrinsic algorithmic search is assessed
as part of that algorithm, not silently removed while retaining an equivalence claim.

Use counts and existing measurements where available; distinguish total work, elapsed wall and
parallel capacity. Finite counts, native code or batching alone do not establish affordability.
No universal overhead multiplier, asymptotic proof, new profiling run or validation service is
required. Unknown work/cost stays unknown; a ratio to a budget cap is not an inflation ratio against
a minimal adequate experiment. This is design reasoning, not an extra §11.4 launch condition.
