# HMASD Scientific Exploration Principles

This file is the durable scientific contract for HMASD algorithm exploration.
It contains cross-experiment principles, not the active route, implementation
specification, experiment dashboard, or research history.

Current ownership and the scheduled action belong in
`docs/project/CURRENT_WORK.md`. Durable conjectures, retained lemmas,
counterexamples, idea status and evidence notes live under
`docs/research/cdc/`. External GPT-5.6 Pro owns scientific CDC decisions. The
Controller archives and adopts those decisions and maintains the research
records. The Project Manager translates an adopted implementation action
into executable design.
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

Use Conjecture -> Derivation -> Counterexample or Disproof -> Correction.
External GPT-5.6 Pro owns scientific decisions in this loop. It may use a full
plural review or a focused continuation in the same registered conversation.
The Controller preserves and adopts that judgment; the Project Manager
realizes the adopted algorithm without replacing the scientific direction.

Maintain several live conjectures when evidence permits. Each states its scope,
mechanism-to-behavior-to-capability edge, strongest simpler explanation, and
observable intervention, natural-execution and held-out consequences. When
material, state why ordinary recurrence, capacity or information reorganization
cannot explain the same consequence.

Actively construct policies or measurements that satisfy a surface metric
without the intended semantics. A useful counterexample, corrected definition,
retained lemma or benchmark-identification result is progress even when no code
is launched.

Schedule one resource-consuming action at a time for attribution, not one legal
research direction. Choose by information gain, cost and reversibility,
normally in this order: derivation, counterexample, accepted-evidence
reanalysis, toy, bounded prototype, formal experiment. Unscheduled ideas remain
live or parked with a reactivation condition.

## 4. Evidence Design

Freeze evidence, not theory. Before observing a conclusion-bearing result,
freeze provenance, primary estimand, comparator information and resource
boundaries, probability and credit authority, external/intrinsic reward
semantics, leakage boundaries and conclusion-bearing metrics. Afterward,
preserve the observation and its registered meaning while allowing the
conjecture, definition, scope, benchmark or architecture to be corrected.

An evidence note states the local question, implicated conjectures, cheapest
separating observation, matched controls, frozen estimand and metrics, budget
and optimizer exposure, prohibited changes and plausible portfolio deltas. It
does not claim that all future theoretical interpretations are exhausted.

Match the comparator to the claim. Use diagnostic nulls for incremental signal,
mechanism-matched controls for a component claim, temporal controls for a
lifetime claim, and complete-algorithm baselines for an end-to-end claim.
Historical runs are references rather than causal controls after architecture,
capacity, optimizer exposure, environment, seed, or evaluation changes.

Report both environment interaction and optimizer-update exposure. Equal
environment steps do not imply equal learning opportunity.

Create an implementation plan only when implementation is the cheapest
necessary evidence action and the research object is precise enough that two
reasonable implementations instantiate the same estimand. Add at most one
focused operational check for a concrete corruption risk the evidence-bearing
run cannot cheaply expose. Do not repeatedly re-prove accepted facts without a
concrete contradiction.

## 5. Toys, Access, and Transfer

A toy environment must expose the target capability rather than merely make the
current mechanism easy to pass. For variable membership and lifetime research,
the same toy should make membership changes and heterogeneous temporal duties
causally relevant while keeping task-specific reward shaping out of the
algorithm.

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

Mixed and underpowered results preserve unresolved explanations. Retry only a
failed operational path. Do not rescue a valid negative by changing seed,
budget, model, learning rate, metric, threshold, reward or name. Broad mechanism
retirement requires a structural contradiction, equivalence proof or multiple
independent identified counterexamples.

Every result records the smallest supported or refuted proposition, a retained
lemma, any counterexample, what the result does not imply and the portfolio
delta. PASS does not automatically integrate; FAIL does not select a successor;
NO_ACCESS does not veto stronger-MARL work.

## 7. Scientific Progress and Review

Progress includes a new capability, decision-relevant evidence, a concrete
counterexample, a corrected definition, a retained lemma, a benchmark
identification result or a portfolio update. Documentation and workflow status
alone are support work.

External GPT-5.6 Pro generates and corrects conjectures, derives consequences,
constructs counterexamples, extracts lemmas and chooses one scheduled action
while retaining plural explanations. The Project Manager owns algorithmic and
technical feasibility, realization, independent review, tests and acceptance.
The Controller checks only mechanical provenance, maintains records and owns
resources, Git, claim ceilings and user communication; it does not validate PM
work.

```text
pm_acceptance_authority=exclusive
controller_validation_authority=none
```

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
