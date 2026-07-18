# HMASD Scientific Exploration Principles

This file is the durable scientific contract for HMASD algorithm exploration.
It contains cross-experiment principles, not the active route, implementation
specification, experiment dashboard, or research history.

Current ownership and the live portfolio belong in `memory/CURRENT_WORK.md`.
Executable design belongs in `memory/IMPLEMENTATION_PLAN.md`. Formal experiment
contracts and dispositions belong in `memory/ExpRecord.md`. Git history preserves
removed research history.

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

## 3. Portfolio-First Exploration

At an unresolved architecture or direction boundary, maintain two to four
structurally distinct causal explanations and, when useful, candidate
architectures. Each candidate states:

- the final capability it unlocks and what later integration would consume it;
- its replacement ledger;
- the evidence it explains and the evidence it does not explain;
- its strongest ordinary-MARL or simpler-controller reduction;
- an observation that would strengthen, weaken, merge, or retire it.

Generate and compare ideas in parallel when useful, but serialize mutating
implementation and compute to preserve attribution and workspace integrity.
One active evidence source does not imply one legal research direction or one
mandatory successor.

Select the next evidence source by expected information gain and relevance to
the final target. It may be a reanalysis, constructive toy, bounded prototype,
controlled intervention, or training run. Prefer the smallest coherent source
whose plausible outcomes change relative support among live candidates or
cause a real stop or integration decision.

Do not replace algorithm exploration with a chain of arbitrary gates. A result
constrains only the causal claim and implementation family it identifies.
Failure of one mechanism does not prohibit a structurally different route.

## 4. Evidence Design

Before implementing a new scientific route or launching a conclusion-bearing
experiment, record in the active plan and, for a formal run, `ExpRecord.md`:

- the exact causal claim and estimand;
- at least two plausible explanations for the current evidence;
- the smallest observation that separates them;
- the strongest ordinary baseline and mechanism-matched comparator;
- metrics, nulls, budgets, optimizer exposure, and result branches;
- what every scientific outcome does to every live candidate;
- changes prohibited while the evidence source is open;
- the condition that would exhaust the relevant portfolio.

Match the comparator to the claim. Use diagnostic nulls for incremental signal,
mechanism-matched controls for a component claim, temporal controls for a
lifetime claim, and complete-algorithm baselines for an end-to-end claim.
Historical runs are references rather than causal controls after architecture,
capacity, optimizer exposure, environment, seed, or evaluation changes.

Report both environment interaction and optimizer-update exposure. Equal
environment steps do not imply equal learning opportunity.

Add at most one focused operational check for a concrete corruption risk the
evidence-bearing run cannot cheaply expose. Do not add a separate algorithm
verification stage or repeatedly re-prove accepted facts without a concrete
contradiction.

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

Interpret outcomes narrowly:

- `PASS`: supports only the registered causal claim under the frozen contract;
- `VALID_FAIL`: rejects or weakens that registered claim and implementation
  family without automatically rejecting structurally different routes;
- `MIXED`: resolves only the branches supported by the observed components;
- `INVALID`: an implementation, replay, probability, RNG, data, or analysis
  defect prevents scientific interpretation;
- `NO_ACCESS`: the benchmark or ordinary-policy access condition was not
  established, so the intended algorithm comparison is not identified;
- `UNDERPOWERED`: the estimand is valid but the registered evidence cannot
  resolve it at the declared precision.

Retry only a failed operational path. Preserve scientific thresholds and the
estimand after observing results. Do not rescue a valid negative by changing
seed, budget, model size, learning rate, metric, threshold, reward, or name.

Negative results are reusable constraints. Reopening a failed family requires a
new causal reason that changes the relevant mechanism or evidence boundary, not
a parameter search over the retired estimand.

## 7. Scientific Progress and Review

Progress is one of:

- a new algorithm capability;
- new decision-relevant evidence;
- a portfolio update that changes what should be built or tested.

Documentation, inventories, repeated status reads, and workflow prose are
support work. Keep them to the minimum required for valid attribution.

External reviewers provide independent hypotheses, objections, and evidence
assessment. They do not authorize code, experiments, promotion, retirement, or
a unique legal successor. The active controller integrates reviewer advice with
repository evidence and owns the scientific disposition.

## 8. Maintaining This Contract

Update this file only when accepted evidence or explicit user direction reveals
a cross-experiment scientific rule. Record the concrete result elsewhere, then
write only the generalized principle here.

Do not add round numbers, current portfolio status, run paths, numerical gates,
implementation symbols, historical narratives, deprecation notices, or
superseded text. Do not create a principles-only commit for a one-off issue;
when possible, update the principle at the same accepted boundary as the
evidence or concrete correction that motivated it.
