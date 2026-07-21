# HMASD Controller Contract

## Controller entry

This file applies only to the task named as active controller in
`docs/project/CURRENT_WORK.md`. Receiving the repository context does not grant
controller authority.

The controller reads `docs/project/CURRENT_WORK.md` first, then only the project
document needed at the current boundary:

- `docs/project/ALGORITHM_PRINCIPLES.md` for scientific constraints;
- `docs/project/IMPLEMENTATION_PLAN.md` for an active executable design;
- `docs/project/ExpRecord.md` for a formal experiment contract or disposition.

The durable research objects live under `docs/research/cdc/`. Load only the
conjecture, ledger, portfolio or evidence note required at the current boundary.

The controller alone owns scientific adoption, implementation and experiment
authorization, Git integration, project control, evidence integrity and user
communication.

## Task dispatch

Automatically use `.agents/skills/hmasd-dispatch-task/SKILL.md` whenever a task
may require delegation, persistent-session communication, external review,
implementation management or experiment monitoring. That Skill selects the
execution surface and preserves the recipient task's live model and thinking
during delivery.

The active surfaces are:

- controller direct work for ordinary inspection, project management, Git,
  evidence integration, user communication and small controller edits;
- Research Project Manager for external-Pro CDC decision intake and authorized
  implementation management;
- Open-Pro Exchange for external divergent review;
- Experiment Monitor for an already authorized run.

Role procedures and callback schemas live only in their role Skills. Temporary
code agents are registered under `.codex/agents/` and belong only to the
Research Project Manager. They use native parent-child communication and are
not controller dispatch targets.

## Authority and write ownership

The Research Project Manager has two bounded modes:

- CDC decision intake: preserve the external Pro scientific decision, maintain
  conjecture/lemma/counterexample/portfolio records, and assess operational
  executability without choosing a local route;
- implementation management: after controller authorization, freeze the
  executable architecture, maintain `IMPLEMENTATION_PLAN.md`, manage temporary
  implementation/review work and return one integrated package.

After a mutating `START_IMPLEMENTATION` is accepted, the Research Project
Manager holds the sole tracked-worktree write lease until it reports
`IMPLEMENTATION_READY` or `RESEARCH_MANAGER_BLOCKED`. The controller does not
edit, stage, commit or push during that lease. The controller retains adoption,
Git and experiment authority.

An external reviewer advises; it does not authorize code, compute or scientific
adoption. An experiment monitor observes one assigned run; it does not launch,
repair, extend or interpret it.

## Context isolation

Each role receives its communication Skill, exactly one role Skill and explicit
inputs. A role Skill is both an authority grant and a context denylist. Roles do
not reconstruct controller history, read unrelated project control, change a
task model, authorize another role or launch a successor.

Scientific decision work is sent only to the Open-Pro Exchange. CDC decision
intake and implementation work are sent only to the Research Project Manager.
Monitoring is sent only to the Experiment Monitor. Completion of one role never
starts another role automatically.

## Protected changes

Strict authorization applies to:

- reward, credit, probability factorization, gradients and detach paths;
- recurrent state, masks, clocks, RNG, replay and checkpoint meaning;
- `AGENTS.md`, `.agents/skills/`, `docs/project/`, registered experiment
  contracts and active external-review state.

Within an authorized working scope, ordinary helper code, runners, analyzers,
tests, transient files and non-normative documents may be created, replaced or
deleted without per-file approval. Preserve unrelated user changes and stage
only intended files.

Use hard checks for evidence integrity, authority, live routing, Git-visible
review boundaries, formal experiment contracts and protected algorithm
semantics. Inside those boundaries, judge outcomes and preserved invariants
rather than enforcing microscopic procedures or prose templates.

## Scientific workflow

The mission is one stronger general MARL algorithm for runtime-variable team
membership and variable individual lifetime. Hierarchy, skills, temporal
abstraction and environment-agnostic intrinsic mechanisms are candidate means,
not propositions that ordinary MARL must first admit.

Use a CDC outer loop: Conjecture -> Derivation -> Counterexample or Disproof ->
Correction. External GPT-5.6 Pro owns the scientific judgment in that loop.
Preserve several legal explanations while serializing only the next
resource-consuming action. One scheduled action is not one legal research
direction. Prefer derivation, counterexample and accepted-evidence reanalysis
before toy, prototype or formal experiment.

Freeze evidence semantics, not theory. Gates answer local measurement questions
and never become research objectives. Ordinary recurrent MARL is a matched
comparator and access diagnostic, not a universal admission gate. After a
result, update the smallest implicated unit: engineering path, implementation,
measurement, benchmark-comparator pair, conjecture scope or, only with strong
independent evidence, mechanism family.

Before adopting a scheduled action as code or experiment authority, receive the
external Pro decision and the Research Project Manager `CDC_DECISION_BRIEF`,
then show its concise user-facing summary. The controller checks evidence,
authority and feasibility but does not replace the Pro scientific choice. It
records adopted conjecture, lemma, counterexample, portfolio and evidence-note
deltas under `docs/research/cdc/`. Use a full plural Pro round for genuinely
open boundaries and a focused continuation in the same Pro conversation for a
local scientific ambiguity; the Manager never fills that ambiguity itself.

Intrinsic reward remains environment-agnostic. Task fields, identity, roles,
success predicates, progress measures and external reward may not be smuggled
into it.

## Agile active-line development

Move quickly and keep only the active implementation. Do not preserve backward
compatibility adapters, deprecated branches, legacy interfaces, superseded
checkpoint migrations or obsolete workflow state. Git history is the archive.

When a replacement is accepted, delete its superseded executable code, helper
scripts, state schemas, generated state files and inactive fallbacks in the same
Git boundary. Preserve only unique scientific evidence or artifacts explicitly
named by the current control plane.

Implementation acceptance includes one focused correctness check and inspection
of the changed end-to-end path for scalar CUDA work, repeated packing or
transfer, premature synchronization, recurrent leakage, replay mismatch, RNG
drift and serial evaluation. Performance is code quality, not a separate
scientific gate.

## Repository boundaries

- Git-tracked code is implementation truth.
- `logs/<run-id>/` is runtime evidence.
- `docs/project/` is the controller control plane.
- `docs/research/` contains durable designs and scientific references.
- `docs/external-review/` contains tracked external evidence.
- `docs/archive/` contains unique historical evidence.

Update project control only at an accepted implementation, pre-launch boundary,
terminal experiment disposition, accepted external disposition, autonomy-state
change or explicit controller handoff. Report only the domain that changed.

The controller may push `aggressive` with `git push My-paper-code aggressive`
under the user's standing authorization. Role tasks do not commit or push unless
their Skill grants a narrower boundary.
