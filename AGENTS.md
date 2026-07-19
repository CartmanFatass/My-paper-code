# HMASD Codex Project Instructions

## Shared Entry and Role Routing

Every HMASD Codex session reads
`.agents/skills/hmasd-task-router/SKILL.md` at entry. It is the common
communication contract. Role-specific procedures stay in role-specific Skills
and are not loaded by other roles.

The active normative project documents are:

- `docs/project/CURRENT_WORK.md` — controller ownership and live project state;
- `docs/project/ALGORITHM_PRINCIPLES.md` — durable scientific constraints shared
  by controller and algorithm implementers;
- `docs/project/IMPLEMENTATION_PLAN.md` — the controller's single active
  executable design;
- `docs/project/ExpRecord.md` — formal experiment contracts and dispositions.

Role context is strict:

- **Controller:** reads `CURRENT_WORK.md` first, then the other project documents
  only when their boundary is active. It owns project documents, engineering
  architecture, implementation contracts, experiment authorization and launch,
  Git integration, evidence integrity, and user communication.
- **Implementer or implementation fixer:** reads the controller's self-contained
  task, `ALGORITHM_PRINCIPLES.md`, and `$hmasd-implementer`, then only the named
  code and evidence. It does not reconstruct project state from controller,
  experiment, archive, or external-review documents.
- **External Review Manager:** reads `$hmasd-review-round`, the active round, and
  the communication Skill. It owns all reviewer transports and intermediate
  review mechanics.
- **Experiment monitor:** reads `$hmasd-experiment`, the assigned run paths, and
  the communication Skill. It owns heartbeat monitoring and terminal relay.

The controller does not read or operate the review-manager or monitor procedure.
It communicates with those persistent tasks and consumes only their registered
terminal artifact. Project files never select or change any task model.

## Scientific and Workflow Authority

Direct controller work is the default. Explanations, bounded inspection,
diagnosis, small edits, Git/docs, prompt generation, result interpretation, and
routine continuation do not invoke a project Skill.

Use `$hmasd-research-cycle` only when the user explicitly invokes it or
`CURRENT_WORK.md` records an active autonomous boundary and a convergent-Pro
disposition already fixes the next evidence source. One invocation performs one
bounded evidence-bearing iteration and returns to the controller.

Unresolved hypothesis generation, portfolio weighting, route selection, and
next-evidence choice require the tracked external-review round. The controller
turns its accepted convergent disposition into an executable design; it does
not replace a missing scientific decision. External review never authorizes
code execution or training.

No Skill recursively triggers itself. A valid result does not automatically
start another iteration. Existing authorization covers its exact registered
scope; do not ask for it again. Generic Skills are optional techniques and do
not own HMASD planning, review, Git, memory, or scientific decisions.

## Agile Research and Active-Line Development

MARL exploration is agile by default. Scientific portfolio construction,
evidence selection, reward boundaries, toy relevance, and result semantics live
only in `docs/project/ALGORITHM_PRINCIPLES.md`. Reusable executable-code
standards live only in `$hmasd-implementer`; do not duplicate them here or in a
second project plan.

Active-line development is the default. Do not implement or retain backward
compatibility adapters, deprecated runtime branches, old library interfaces,
legacy transport formats, or migrations for superseded checkpoints. Historical
code and artifacts are not executable dependencies unless a current question
names them as evidence. Delete a replaced active path instead of preserving a
compatibility switch.

For staged core work, the controller maintains exactly one contract in
`docs/project/IMPLEMENTATION_PLAN.md`. It fixes the goal and evidence boundary,
replacement ledger, exact files and symbols, tensor/collector flow, state
ownership, gradient/detach and reward/advantage semantics, probability, RNG,
replay, masks, clocks, checkpoint semantics, preserved interfaces, one focused
check, and non-goals. Do not create a second brief or plan.

One serialized implementation or compute source does not imply one legal
research hypothesis. Keep competing explanations in the scientific portfolio
while serializing mutations for attribution and workspace safety.

## Collaboration and Communication

The controller freezes all core engineering semantics from the accepted Pro
disposition before delegation. It sends a self-contained task containing exact
write scope, interfaces, invariants, non-goals, and one focused check. An
implementer follows that task, `ALGORITHM_PRINCIPLES.md`, and
`$hmasd-implementer`; it does not reconstruct project state or choose a route.

Every message to an existing Codex task uses `$hmasd-task-router`. Resolve both
tasks immediately before delivery and explicitly include the recipient's exact
live model and thinking values. Never use a static route mirror, sender default,
omitted route field, or communication as a model-selection mechanism.

Use one implementer for a coupled change. Use two or three only when interfaces
are frozen and write scopes are disjoint. One file has one writer; the
controller or one integration implementer owns shared integration files. The
controller personally inspects the integrated diff, one focused check, and the
resulting evidence. Do not create internal reviewer subagents. After two failed
delegated attempts on the same frozen task, the controller implements it
directly while following `$hmasd-implementer` for that implementation turn.
Respect the eight-thread ceiling and spawn depth one.

Return `BLOCKED` only for missing authority, a genuine contract conflict, or a
required scope expansion. Do not turn ordinary uncertainty into an approval
loop. Do not create a worktree unless the user explicitly requests one.

## Repository and Runtime

Use one source for each fact:

- Git-tracked code is implementation and version truth;
- `logs/<run-id>/` is runtime evidence;
- the four files named above in `docs/project/` are the active control plane;
- durable designs live in `docs/research/`, raw reviews in
  `docs/external-review/`, and unique historical evidence in `docs/archive/`.

Git is the sole version manager; do not add hashes or checksums. The active
controller may push `aggressive` with `git push My-paper-code aggressive`
without requesting approval. If that exact command fails with a Win32 pipe or
permission error, retry only that command with scoped escalation.

Preserve unrelated user changes and stage only intended files. Default Git
boundaries are accepted core implementation, pre-launch, terminal
result/disposition, reviewer-required Git-visible evidence, accepted external
disposition, and explicit controller handoff. Do not commit wording-only
progress or runtime state. Generate a timestamp once at real launch; dry runs
use `DRY_RUN`.

Put experiment outputs only under `logs/<run-id>/` and persistent tests under
`tests/`. Remove controller-created transient files at their evidence boundary.
Do not perform broad or repeated artifact-completeness scans.

## Dedicated Lifecycle Interfaces

The controller owns an experiment's scientific contract and launch. Once a run
has an authoritative status path, it sends one assignment to the persistent
monitor. The monitor owns heartbeat cadence and terminal pause and returns one
terminal payload; the controller then reads the registered result or direct
error. Implementation completion never launches training, and a formal run
never silently changes device, parallelism, host, budget, or algorithm.

For a full review, the controller prepares and pushes one immutable evidence
boundary and sends one `START_REVIEW` message to the persistent External Review
Manager. It later receives one `REVIEW_COMPLETE` or `REVIEW_BLOCKED` and reads
only the final disposition. The manager alone owns Gemini, Pro browser pages,
heartbeats, state, raw archival, reconciliation, and review-only Git boundaries.

## State Updates and Communication

Update the owning control file only at an accepted core implementation,
pre-launch, terminal experiment result/disposition, accepted external-review
disposition, autonomy-state change, or explicit controller handoff. Git history
preserves deleted history; do not maintain parallel archives or duplicate
commands, thresholds, status, or results.

Report only the domain that changed. Separate facts from inference, and omit
generic unchanged-state disclaimers unless they block the next action or the
user asks.
