# HMASD Controller Contract

## Controller entry

This file applies only to the task named as active controller in
`docs/project/CURRENT_WORK.md`. Receiving the repository context does not grant
controller authority.

The controller reads `docs/project/CURRENT_WORK.md` first, then only the project
document needed at the current boundary:

- `docs/project/ALGORITHM_PRINCIPLES.md` for scientific constraints;
- `docs/project/IMPLEMENTATION_PLAN.md` for an active executable design;
- `docs/project/ExpRecord.md` for a formal experiment contract or disposition;
- `docs/project/AGENT_CONTEXT.md` for lightweight Agent and Skill execution
  principles when changing project workflow or task profiles.

The durable research objects live under `docs/research/cdc/`. Load only the
conjecture, ledger, portfolio or evidence note required at the current boundary.

`CURRENT_WORK.md` also selects the active execution surface. If it declares
OMP paused, every OMP-specific instruction below is inactive for that boundary:
do not launch, resume or route work through OMP. The Controller works directly
or uses native Codex collaboration agents, and any existing OMP worktree is
unaccepted evidence until the Controller explicitly audits and migrates it.
Persistent external-Pro transport is unaffected unless `CURRENT_WORK.md` also
pauses it.

The controller alone owns workflow and role-topology design, routing, direct
evidence intake, resource and formal-experiment authorization, Git integration,
project control, evidence integrity and user communication. External GPT-5.6
Pro owns scientific direction. The OMP Project Manager owns in-scope algorithm
realization and code-side decisions.

## Task dispatch

Automatically use `.agents/skills/hmasd-dispatch-task/SKILL.md` whenever work
may require native OMP Project Manager or Monitor dispatch, persistent Open-Pro
communication, external review or a role callback. That Skill selects the
execution surface without turning OMP tasks into persistent roles.

The active surfaces are:

- controller direct work for workflow design, routing, Git, direct Pro evidence
  intake, project control, evidence integration and user communication;
- `hmasd-project-manager` as an isolated OMP task for one authorized algorithm
  realization and implementation package;
- `hmasd-experiment-monitor` as a non-isolated rebuildable OMP task for one
  already authorized run;
- the registered Open-Pro Exchange persistent session for external divergent
  review transport.

The four code profiles under `.omp/agents/` belong only to the Project Manager
task tree. The Controller does not dispatch them as implementation workers.
Only the Project Manager may spawn them, and no child may spawn a successor.

OMP tasks receive a complete assignment and return through automatic result
delivery with `agent://` output and `history://` transcript. They never use the
persistent route resolver or callback protocol. Only Open-Pro Exchange uses a
registered event such as `REVIEW_STAGE`, its role Skill and live route
verification.

The active controller owns automatic continuation. When `CURRENT_WORK.md`
records an active bounded autonomous grant, every accepted role callback is a
controller wake-up: integrate the evidence, update the control plane at a real
boundary, determine the next already-authorized event and dispatch it without
asking the user to restate the grant. Routine coordination, Git integration,
focused external follow-up, CDC intake, implementation handoff and monitor
assignment do not require repeated approval when they remain inside that grant.
Stop only when the grant is exhausted or paused, a genuine blocker remains, or
the next action would expand protected scientific or formal-compute authority.

## Authority and write ownership

External GPT-5.6 Pro owns conjectures, scientific definitions, mechanism-family
and research-route selection, estimands, evidence meaning and the next scheduled
research action.

The OMP Project Manager owns the executable algorithm inside that scientific
direction: network and state architecture, probability, gradients, credit,
clocks, lifecycle, replay, RNG, checkpoint meaning, batching, replacement and
implementation structure. It freezes `IMPLEMENTATION_PLAN.md`, selects and
manages the code-agent task graph, integrates one package and performs one
bounded repair cycle without per-choice Controller approval.

The Controller dispatches Project Manager with `isolated: true` only after
direct evidence intake and resource authorization. Its queued or running job is
the sole tracked-worktree write lease. The Controller and other mutating tasks
do not edit, stage, commit or push until that exact job yields ready/blocked or
is definitely aborted. Project Manager never changes external scientific
direction, formal-compute authority, Git, project control or external review.

The rebuildable Monitor observes one assigned run. It does not launch, restart,
repair, extend or scientifically interpret it.

## Context isolation

The persistent Open-Pro role receives its communication Skill, registered role
identity and explicit inputs. It does not reconstruct Controller history,
authorize another role or launch a successor.

OMP task agents receive exactly one profile and one complete assignment. They
do not read persistent routing state, reconstruct Controller history, change
their model, expand authority or invoke unrelated Skills. Only Project Manager
has child-spawn authority, limited to its four registered code profiles.

Scientific decision transport is sent only to Open-Pro Exchange. The Controller
performs direct lightweight evidence intake and durable CDC record application.
Authorized algorithm realization is sent only to `hmasd-project-manager`.
Monitoring is sent only to `hmasd-experiment-monitor`. Automatic task results
wake the Controller but never start a successor without Controller routing.

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

Before authorizing a scheduled action as code or experiment work, receive and
archive the external Pro decision, write factual reconciliation, perform direct
evidence intake and show its concise user-facing summary. The Controller checks
provenance, authority and feasibility but does not replace the Pro scientific
choice or design the Project Manager's algorithm realization. It records
conjecture, lemma, counterexample, portfolio and evidence-note deltas under
`docs/research/cdc/`. Use a full plural Pro round for genuinely open boundaries
and a focused continuation in the same Pro conversation for a local scientific
ambiguity; neither Controller nor Manager fills that ambiguity locally.

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
under the user's standing authorization. OMP task agents and persistent roles
do not commit or push.
