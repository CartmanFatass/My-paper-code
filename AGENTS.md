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

All live orchestration assets other than this root bootstrap contract live
under `.omp/`: native Skills in `.omp/skills/`, task profiles in
`.omp/agents/`, routing state beside its owning Skill, and OMP/BrowserMCP
configuration at the `.omp/` root. `.omp/legacy/` retains pre-unification
profiles only as non-active migration evidence. Scientific records, immutable
review rounds, algorithm source and runtime evidence remain project payload
outside the OMP asset bundle.

`CURRENT_WORK.md` selects the active execution surface. The Controller is one
unified scientific-to-code orchestrator: it performs direct evidence intake,
freezes executable plans inside the accepted scientific direction, dispatches
project-local OMP task agents, and operates the user-connected ChatGPT Pro tab
through BrowserMCP. Experiment monitoring remains separately registered.

The intact end-to-end loop is:
external GPT-5.6 Pro scientific review -> Controller evidence intake and frozen
executable plan -> local OMP implementation plus one collective
Reviewer/Verifier gate -> authorized run observed by the registered
`experiment_monitor` -> Controller result intake -> external GPT-5.6 Pro result
review. Consolidating assets never removes or substitutes a stage.

Persistent roles are resolved only from the dispatch Skill registry. Local code
agents are resolved only from `.omp/agents/`; external scientific transport is
resolved only from `.omp/mcp.json` plus
`hmasd-browser-pro-exchange`. Never infer a current role from a task title, an
old callback or conversation search. Unregistered former relay sessions and
removed profile roots are obsolete execution surfaces.

An execution-surface change is one atomic control boundary: update
`CURRENT_WORK.md`, the dispatch Skill, its role registry, local agent profiles
and the corresponding contract tests together. Do not activate a topology when
those sources disagree.

The controller alone owns workflow and role-topology design, routing, direct
evidence intake, executable algorithm realization, resource and
formal-experiment authorization, Git integration, project control, evidence
integrity and user communication. External GPT-5.6 Pro owns scientific
direction.

## Task dispatch

Automatically use `.omp/skills/hmasd-dispatch-task/SKILL.md` whenever work
may require Monitor dispatch or a persistent role callback. Use
`hmasd-browser-pro-exchange` for external review transport. Local code-agent
work uses the project OMP task profiles directly.

The active surfaces are:

- the unified Controller for workflow design, executable planning, direct local
  agent coordination, BrowserMCP Pro submission, observation and capture,
  integration, verification, Git, direct evidence intake, project control,
  evidence integration and user communication;
- the pinned `browsermcp-pro` server and one user-connected authenticated
  ChatGPT Pro tab for external scientific review;
- the registered native Codex `experiment_monitor` slot for one
  already-authorized run. Its archived task is rebuild-required before the next
  formal run; external review and local OMP work do not route through it.

The exact case-sensitive OMP `agent` values exposed under `.omp/agents/` are
`hmasd-code-scout`, `hmasd-implementer`, `hmasd-frontier-implementer`,
`hmasd-verifier`, `hmasd-reviewer` and `hmasd-exp-manager`. The Controller
dispatches them directly.
`hmasd-frontier-implementer` is reserved for one bounded
reproduced bug, runs Sol at `max`, follows the systematic debugging loop and
stops after at most five repair attempts with either verified evidence or a
structured unresolved-error report. No child may
spawn a successor. An `unknown agent` response is a workflow blocker; never
silently replace a registered project agent with an unnamed or bundled default
child.

The persistent Monitor receives a complete assignment through live route
resolution. BrowserMCP remains a Controller-owned connection and external
review is one Controller-owned state machine. No local or persistent role may
observe, submit, retry, capture or archive a Pro response. Local agents receive
one complete bounded assignment through the OMP task tool.

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

Inside that scientific direction, the Controller owns the executable algorithm:
network and state architecture, probability, gradients, credit, clocks,
lifecycle, replay, RNG, checkpoint meaning, batching, replacement and
implementation structure. It freezes `IMPLEMENTATION_PLAN.md`, selects and
manages the local agent task graph, integrates one package and performs one
bounded repair cycle.

The Controller/main conversation is the sole implementation-plan author. Before
one code implementation round it performs a scaled Superpowers-style design
pass itself: inspect current context, make requirements and success criteria
explicit, compare 2-3 viable approaches, select the smallest sound design, and
write exact files, interfaces, invariants, red/green checks and expected outputs
into `IMPLEMENTATION_PLAN.md`. Inside an active autonomous grant the Controller
automatically selects the recommended engineering approach; it asks the user or
Pro only when the choice changes protected authority or scientific meaning.
Planning is never delegated to an Implementer, Frontier Implementer, Reviewer or
Verifier.

Review is one collective gate per complete code implementation round, not one
gate per child task, file, repair attempt or intermediate failure. After every
planned implementation task and bounded repair is integrated and the
Controller's focused checks are green, dispatch exactly one Reviewer and one
Verifier in parallel over the same stable package. A second collective review
is required only if the resulting repair materially changes protected semantics
or the frozen plan contract.

Before implementation, the Controller records the current branch, `HEAD` and
inherited working-tree state in the assignment. Local agents work on that exact
visible source, preserve unrelated changes and never perform Git operations.

One writer owns a file scope at a time. A local agent's assignment is its sole
write lease. The Controller does not concurrently edit that scope and verifies
the returned package before Git integration. Local agents never stage, commit,
push, stash, reset, checkout tracked files or manipulate branches.

The rebuildable Monitor observes one assigned run. It does not launch, restart,
repair, extend or scientifically interpret it.

## Context isolation

The long-lived OMP Controller starts the pinned BrowserMCP server before the
user connects one exact ChatGPT Pro tab; an ephemeral process is not a valid
transport. BrowserMCP receives one exact Git-visible question. Pro reads pushed
result and evidence files plus named reference-code paths through its GitHub
connector; BrowserMCP does not upload local source. The Controller alone runs
the Skill-owned validate, reconcile, draft, submit, observe, stabilize, capture
and archive state machine. A no-clobber submission receipt prevents replay
after restart, and two stable snapshots must yield the same marked response
before raw archival.

Local task agents receive exactly one project profile and one complete
assignment. They do not reconstruct Controller history, change their model,
expand authority, invoke unrelated Skills or spawn agents. Their tool lists and
the project recursion limit enforce a depth-one task graph.

Scientific decision interaction uses only the pinned BrowserMCP Pro channel.
The stage commit contains the canonical question and manifest; those artifacts
name one exact ancestor evidence commit, current pushed branch and repository.
Reviewer evidence retrieval uses the GitHub connector at that evidence commit.
Submission receipt and raw archival are exclusive and no-clobber. The
Controller performs direct factual reconciliation, evidence intake and durable
CDC record application. Authorized algorithm realization remains in the
Controller's local OMP task tree. Experiment-run monitoring is sent only to
`experiment_monitor`. Pro response observation stays in the Controller session;
browser responses and automatic task results never start a successor without
Controller routing.

## Protected changes

Strict authorization applies to:

- reward, credit, probability factorization, gradients and detach paths;
- recurrent state, masks, clocks, RNG, replay and checkpoint meaning;
- `AGENTS.md`, `.omp/skills/`, `docs/project/`, registered experiment
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
provenance, authority and feasibility, preserves the Pro scientific choice, and
owns the executable realization inside it. It records conjecture, lemma,
counterexample, portfolio and evidence-note deltas under `docs/research/cdc/`.
Use a full plural Pro round for genuinely open boundaries and a focused
continuation in the same Pro conversation for a local scientific ambiguity;
neither the Controller nor a local worker fills a scientific ambiguity locally.

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
of the changed end-to-end path for scalar device work, repeated packing or
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

The Controller may push only `Claude` to `origin` under the user's current
authorization. It must not push, force-push, merge into or otherwise mutate
`aggressive` or any other branch. Fetching and merging `origin/aggressive` into
`Claude` is permitted. Local agents and persistent roles do not commit or push.
