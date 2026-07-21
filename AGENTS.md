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
- Research Project Manager for scientific convergence and authorized
  implementation management;
- Open-Pro Exchange for external divergent review;
- Experiment Monitor for an already authorized run.

Role procedures and callback schemas live only in their role Skills. Temporary
implementation and review subagents belong to the Research Project Manager and
use native parent-child communication; they are not controller dispatch targets.

## Authority and write ownership

The Research Project Manager has two bounded modes:

- scientific convergence: read external divergent evidence and project
  principles, maintain the idea portfolio and select one code-ready evidence
  source or stop;
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

Scientific convergence and implementation work are sent only to the Research
Project Manager. External review is sent only to the Open-Pro Exchange.
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

Preserve multiple plausible explanations while serializing code mutations and
formal compute for attribution. Do not convert open research into arbitrary gate
chains. Ordinary recurrent MARL is a matched comparator and access diagnostic,
not a universal research admission gate.

Before adopting a scientific source as code or experiment authority, receive a
Research Project Manager convergence brief and show its concise user-facing
summary. External divergent review is required for unresolved hypothesis
generation or portfolio expansion; focused contract completion may return to
the existing scientific owner without reopening a full portfolio round.

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
