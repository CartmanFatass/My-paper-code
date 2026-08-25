# HMASD Scientific Exploration Principles

This file is the durable scientific contract for HMASD algorithm exploration.
It contains cross-experiment principles, not the active route, implementation
specification, experiment dashboard, or research history.

Current ownership and the scheduled action belong in
`docs/project/CURRENT_WORK.md`. Durable conjectures, retained lemmas,
counterexamples, idea status and evidence notes live under
`docs/research/cdc/`. Canonical role authority for scientific decisions,
adoption, realization and acceptance is defined only in root `AGENTS.md` and
the applicable `.agents/roles/*.md` contracts; this file does not restate it.
Formal experiment contracts and dispositions belong in
`docs/project/ExpRecord.md`. Git history preserves removed research history.

## 1. Research Mission

The final target is one general MARL algorithm that can learn under both:

- variable team membership, including join, leave, rejoin, active-agent masks,
  and survivor-state continuity; and
- variable individual skill lifetime, without forcing all active agents to
  renew skills on one shared duration.

The method must remain useful beyond one UAV benchmark. A toy, diagnostic, or
mechanism is relevant only when it tests a capability consumed by this final
target.

Development may stage these two dimensions instead of forcing both into every
early experiment. A user-authorized variable-membership stage may freeze skill
lifetime and remove the skill controller entirely. The first objective of such
a stage is an absolutely usable shared policy under changing membership; it
does not have to establish superiority over a fixed-`N` or hierarchical
algorithm. Comparative advantage and the frozen lifetime dimension are added
only after the shared dynamic-roster path is reliable.

HMASD and OPT are sources of functional ideas, evidence, and baselines. They are
not compatibility contracts. New work may retain useful functions while
replacing their concrete modules, interfaces, checkpoints, or training paths.

## 2. Algorithmic Boundaries

### 2.1 External reward, intrinsic reward, and shaping

Keep these three objects distinct:

- external reward is the environment task return;
- intrinsic reward is an algorithmic exploration or semantic signal with the
  same mathematical form and input contract across environments;
- reward shaping is an explicitly task-specific intervention or ablation.

Intrinsic reward must not read or encode benchmark goals, named objects,
identities, assigned roles, contacts, phases, distances, success predicates,
task progress, or external reward. Environment-specific shaping cannot be
renamed intrinsic reward and cannot support a general sparse-exploration claim.

An access failure is addressed through observation, dynamics, policy capacity,
or benchmark design. Do not conceal it by customizing intrinsic reward.

### 2.2 Skill semantics and cooperation

Skill-label usage, entropy, or classifier accuracy is not sufficient evidence
of a useful skill. Evidence for a skill claim must distinguish as applicable:

- intervention-sensitive executable behavior;
- persistent effects across a relevant process window;
- differentiation beyond stochastic execution noise and shortcut variables;
- natural-policy use and transport outside forced branches;
- contribution to complementary joint behavior.

Individual skill differentiation is not equivalent to complementary team
composition. A team latent or coordination context is not useful merely because
it is predictable; it must change assignment or behavior in the claimed way.

### 2.3 Variable membership and lifetime

Variable-`N` evidence must exercise membership change rather than only compare
fixed agent counts across episodes. It must account for anonymous membership,
active masks, join/leave/rejoin transitions, state ownership, and survivor
continuity. Fixed identity slots cannot be the sole carrier of cooperation.

Variable-lifetime evidence must distinguish the observation/check clock,
renewal or service opportunity, realized skill segment, and learning-credit
window. A long-lived skill must arise from learned behavior under the declared
clock contract, not from a task-specific lifetime reward or an enlarged
duration-action catalogue alone.

### 2.4 Replacement before accumulation

Prefer replacement and simplification over module accumulation. Every proposed
mechanism states what it deletes, retains, and adds. A new latent, posterior,
critic, reward term, scheduler, graph, or attention module requires a causal
role that the active implementation does not already supply.

An isolated mechanism pass does not authorize integration. Decorative support,
diagnostic predictability, or added capacity is not an algorithmic contribution.

## 3. CDC Open Research Loop

Use the default loop `Conjecture -> minimum necessary derivation or
counterexample -> real algorithm implementation -> environment experiment ->
interpretation -> revision or retirement`. Operate it under the canonical role
contracts: Explorer may interpret A/B observations only inside its advisory
research state; External Pro owns scoped scientific acceptance and
conclusion-bearing decisions when invoked; Project Manager owns code
realization, runtime execution and technical acceptance. A useful next action
is not delayed until every possible interpretation is frozen. Once a mechanism is implementable, has a
differentiating prediction and a simple matched comparator, has no
meaning-changing internal contradiction, and can use a real toy path or an
independently justified sibling environment, implementation and a small
experiment are the default next steps. Additional synthetic fixtures,
certificates or enumerations require a named unresolved question whose answer
could change the result or next decision; they are not the default substitute
for implementation or experiment.

Classify the next evidence action by its scientific burden:

- **A — engineering/evidence reconnaissance or a read-only runtime probe.**
  State one question, the data or runtime path, the non-intervention boundary
  and a fixed small resource cap. A probe may reveal a new observation or
  establish that an existing object is reusable, but it does not establish an
  algorithm effect.
- **B — small exploratory toy algorithm experiment.** State the question,
  candidate and matched comparator, and an initial toy path. Before each named
  run, fix the exact code revision, configuration, seeds and small budget cap so
  that run is reproducible. Between named B runs, the toy host, threshold,
  observations, sample composition and training settings may change when the
  change and its reason are recorded. B is the normal path once the conditions
  above hold. It must call the real environment, policy, learner, trainer and
  evaluation runner and produce nonzero transitions, updates **and** evaluations.
  Tests, truth tables, enumerators, censuses, certificates and byte-stability
  checks are useful evidence but, alone, are neither an algorithm implementation
  nor an experiment. Missing support, unstable training, comparator equivalence
  and non-discriminating observations are valid B outcomes that guide the next
  run; B does not itself make a terminal support, promotion or retirement claim.
- **C — conclusion-bearing, promotion/retirement or expensive experiment.**
  Before collecting or observing a run intended to support superiority,
  promotion or retirement, freeze the outcome or estimand, null and comparator,
  instance or population, stop rule, budget, decision criterion and
  interpretation boundary. Require thresholds,
  confidence, checkpoint/exclusion and multiple-comparison controls only when
  omitting them could change the conclusion. Formal compute authority remains
  user-only. An expensive exploratory run still obeys its resource and compute
  controls, but expense alone does not make its diagnostics conclusion-bearing
  or require irrelevant decision thresholds. The strict methodology in
  `research-methodology.md` is a reference for conclusion-bearing C work, not a
  prerequisite for ordinary B iteration.

Reports identify the current stages `conjecture | derivation | algorithm
implementation | experiment` and state the real calls, transition/update/
evaluation counts, result, strongest alternative explanation and next step.
Binding, closure, PASS counts or certificate production cannot stand in for
those stages. For a new conclusion-bearing design, the same-direction EM
freezes the scientific object, obtains the exact Pro closure required by
`AGENTS.md`, and the CM establishes implementation conformance before formal
compute. `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md` preserves legacy audit
names only; it is not an additional workflow gate.

Maintain several live conjectures when evidence permits. Each states its scope,
mechanism-to-behavior-to-capability edge, strongest simpler explanation, and
observable intervention, natural-execution and held-out consequences. When
material, state why ordinary recurrence, capacity or information reorganization
cannot explain the same consequence.

Actively construct policies or measurements that satisfy a surface metric
without the intended semantics. A useful counterexample, corrected definition,
retained lemma or benchmark-identification result is progress even when no code
is launched.

Scientific attribution is treatment/direction/design/source/run/root/seed
isolation. Already-selected and independently frozen ordinary A/B work across
directions is parallel-first. Serialize only for a named direction dependency
or intake, a shared mutable/path conflict, or an observed resource constraint;
there is no CPM experiment pool, default one-treatment rule, WIP limit, or
experiment-capacity admission condition. Do not invent or fill capacity,
reprioritize science, or reactivate parked directions. Choose by information
gain, cost and reversibility,
normally in this order: derivation, counterexample, accepted-evidence
reanalysis, toy, bounded prototype, formal experiment. Unscheduled ideas remain
live or parked with a reactivation condition.

## 4. Evidence Design

Freeze evidence, not theory. For A, record only the local question, path,
non-intervention boundary and fixed resource cap. For B, record each run's exact
code revision, configuration, seeds, small budget cap, real calls and counts,
then record every between-run change and its reason in the natural-language task
or result brief; do not turn these cues into a required file, schema or admission
checklist. A common exploratory progression is support mapping, then learnability
under a discriminating host, then a small multi-seed estimate of direction,
variance and failure modes. These are judgment-guided questions, not required
states. A controlled host may be adjusted to expose both sides of a support or
label distinction, but that result establishes only controlled identifiability
or learnability, not value in a natural production distribution. Report every
run: a favorable adjusted run must not be presented as preregistered confirmation
or used to erase earlier null, unstable, equivalent or non-discriminating runs.
Before collecting or observing a conclusion-bearing C result, freeze provenance,
primary estimand, comparator information, resource boundaries, stop rule,
decision criterion, probability and credit authority, external/intrinsic reward
semantics, leakage boundaries and conclusion-bearing metrics. Afterward,
preserve the observation and its registered meaning while allowing the
conjecture, definition, scope, benchmark or architecture to be corrected.

An evidence note states the cheapest separating observation and the controls
needed for its selected A/B/C burden. It does not claim that all future
theoretical interpretations are exhausted, and it must not smuggle C-level
freeze requirements into ordinary exploratory work.

Match the comparator to the claim. Use diagnostic nulls for incremental signal,
mechanism-matched controls for a component claim, temporal controls for a
lifetime claim, and complete-algorithm baselines for an end-to-end claim.
Historical runs are references rather than causal controls after architecture,
capacity, optimizer exposure, environment, seed, or evaluation changes.

Report both environment interaction and optimizer-update exposure. Equal
environment steps do not imply equal learning opportunity.

Create an implementation plan when implementation is the cheapest necessary
evidence action and the research object is precise enough that two reasonable
implementations instantiate the same intended comparison. Add focused
operational checks only for concrete corruption risks the evidence-bearing run
cannot cheaply expose; their number and scope follow the named risk, not a
fixed project limit. Do not repeatedly re-prove accepted facts without a
concrete contradiction or named result-relevant question.

For C, evaluate claimed learning signals at the forced initial state, prove
that a positive control makes the target behavior necessary rather than merely
permitted, construct witnesses for result gates, check threshold arithmetic
and zero denominators, and freeze result-sensitive choices. External Pro
remains science-only: it may assess the frozen scientific object and claim
boundary under the governing science route, but never reads a pushed
implementation commit for code acceptance. CM owns implementation conformance
and technical acceptance. These are scoped scientific assertion checks, not
generic review layers or a per-iteration gate on B.

## 5. Toys, Access, and Transfer

A toy environment must expose the target capability rather than merely make the
current mechanism easy to pass. For variable membership and lifetime research,
the same toy should make membership changes and heterogeneous temporal duties
causally relevant while keeping task-specific reward shaping out of the
algorithm.

For a positive control, write the relevant optimal-policy set. If any optimal
solution avoids the target behavior—for example, a permutation-invariant role
swap replacing temporal persistence—the control cannot support a negative
claim about that behavior.

Separate four questions:

1. Can an ordinary controller access the benchmark under the observation,
   model, and budget contract?
2. Is the proposed mechanism implemented and statistically identifiable?
3. Does it create the claimed behavior under intervention?
4. Does that behavior transport to natural policy execution and later target
   integration?

A constructive access result does not prove the research mechanism. A mechanism
pass does not prove natural transport, cooperation, task improvement, or parity.
A benchmark access failure does not by itself reject the algorithm family.

## 6. Result Semantics

Interpret outcomes narrowly and update the smallest implicated unit:

- engineering failure produces no scientific update;
- invalid implementation updates only that implementation;
- valid implementation with invalid estimand updates the measurement;
- benchmark no-access or non-identification updates only that
  benchmark-comparator pair;
- an identified failed consequence updates the corresponding conjecture or its
  scope;
- a valid positive supports only the frozen causal claim.

Mixed and underpowered results preserve unresolved explanations. A B result may
motivate a new named run with recorded changes, but the new run does not replace
or reinterpret the earlier observation. Do not rescue a valid conclusion-bearing
C negative by changing seed, budget, model, learning rate, metric, threshold,
reward or name after the frozen decision contract. Broad mechanism retirement
requires a structural contradiction, equivalence proof or multiple independent
identified counterexamples.

Every result records the smallest supported or refuted proposition, a retained
lemma, any counterexample, what the result does not imply and the portfolio
delta. PASS does not automatically integrate; FAIL does not select a successor;
NO_ACCESS does not veto stronger-MARL work.

## 7. Scientific Progress and Review

Progress includes a new capability, decision-relevant evidence, a concrete
counterexample, a corrected definition, a retained lemma, a benchmark
identification result or a portfolio update. Documentation and workflow status
alone are support work.

Role-specific responsibilities for scientific review, adoption, implementation,
acceptance, provenance, resources and communication are defined only in root
`AGENTS.md` and `.agents/roles/*.md`. This principles file specifies the
scientific result and evidence semantics those roles must preserve.

Review output never authorizes code or compute by itself.

Integration is a separate late decision. Require natural use, intervention-
sensitive sequential behavior, external value, held-out transport, resistance
to simpler explanations and acceptable complexity benefit before considering a
local mechanism part of the full algorithm.

## 8. Maintaining This Contract

Update this file only when accepted evidence or explicit user direction reveals
a cross-experiment scientific rule. Record the concrete result elsewhere, then
write only the generalized principle here.

Do not add round numbers, current portfolio status, run paths, numerical gates,
implementation symbols, historical narratives, deprecation notices, or
superseded text. Do not create a principles-only commit for a one-off issue;
when possible, update the principle at the same accepted boundary as the
evidence or concrete correction that motivated it.
