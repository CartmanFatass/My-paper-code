# HMASD Codex Project Instructions

## Canonical Project Control

All active project-control documents live in `docs/project/`:

- `docs/project/CURRENT_WORK.md` — controller ownership, live objective, portfolio, next
  action, autonomy state, immediate constraints, and current pointers;
- `docs/project/ALGORITHM_PRINCIPLES.md` — durable scientific exploration contract;
- `docs/project/MARL_ENGINEERING_PRINCIPLES.md` — durable implementation and experiment-code
  contract;
- `docs/project/IMPLEMENTATION_PLAN.md` — the single active staged implementation contract;
- `docs/project/ExpRecord.md` — formal experiment contracts and terminal dispositions.

Read `docs/project/CURRENT_WORK.md` first. It is the only mandatory default
read. Load another control document only when the task crosses its boundary.
Read `docs/research/`, `docs/external-review/`, or `docs/archive/` only through a
current pointer or an explicit user request. Historical evidence is not an
active instruction source.

One active controller works directly in `C:\project\HMASD` and owns algorithm
and architecture decisions, root project state, scientific interpretation,
experiment authorization, final Git integration and push, and user
communication. `docs/project/CURRENT_WORK.md` names that task; ownership changes
only by an explicit handoff recorded there. Project files never select the
controller model.

## Workflow Routing

Direct controller work is the default. Explanations, status reads, bounded
inspection or diagnosis, small edits, Git/docs, prompt generation, result
interpretation, and routine continuation do not invoke a project Skill.

Only these conditional workflows exist:

- `$hmasd-research-cycle`: use only when the user explicitly invokes it or
  `docs/project/CURRENT_WORK.md` records `Autonomous Boundary: ACTIVE`; one
  invocation owns one bounded evidence-bearing iteration and must return to the
  controller;
- `$hmasd-experiment`: use for an authorized mutation of an experiment
  contract, package, launch, monitor, failed runtime stage, analysis repair, or
  terminal closure;
- `$hmasd-review-round`: use for a complete tracked five-stage external-review
  round, not for one prompt, one returned answer, routine result interpretation,
  literature discussion, or ordinary brainstorming.

No Skill recursively triggers itself from its own result. A valid result alone
does not start another research iteration. Generic Skills are optional
techniques; they do not own HMASD planning, delegation, review, Git, memory, or
scientific decisions. Existing project authorization satisfies its exact
registered scope. Do not ask for it again, and do not create a worktree unless
the user explicitly requests one.

## Agile Research and Active-Line Development

MARL exploration is agile by default. Scientific portfolio construction,
evidence selection, reward boundaries, toy relevance, and result semantics live
only in `docs/project/ALGORITHM_PRINCIPLES.md`. Tensor/device structure,
batching, replay, recurrent state, persistence, observability, and the single
final experiment-code review live only in
`docs/project/MARL_ENGINEERING_PRINCIPLES.md`. Do not restate either contract in
AGENTS or a Skill.

Active-line development is the default. Do not implement or retain backward
compatibility adapters, deprecated runtime branches, old library interfaces,
legacy transport formats, or migrations for superseded checkpoints. Historical
code and artifacts are not executable dependencies unless a current question
names them as evidence. Delete a replaced active path instead of preserving a
compatibility switch.

For staged core work, maintain exactly one contract in
`docs/project/IMPLEMENTATION_PLAN.md`. It fixes the goal and evidence boundary,
replacement ledger, exact files and symbols, tensor/collector flow, state
ownership, gradient/detach and reward/advantage semantics, probability, RNG,
replay, masks, clocks, checkpoint semantics, preserved interfaces, and
non-goals. Do not create a second brief or plan.

One serialized implementation or compute source does not imply one legal
research hypothesis. Keep competing explanations in the scientific portfolio
while serializing mutations for attribution and workspace safety.

## Collaboration

The controller freezes all core semantics before delegation. New HMASD
implementers and implementation fixers use `gpt-5.6-sol` with `xhigh`
reasoning. Never change an existing task's model; create a correctly routed
replacement instead.

When a project workflow sends to an existing Codex task, the call must include
that task's registered `model` and `thinking` values exactly. Omitting either is
forbidden because it can replace the target task's routing with the sender's;
matching the registered pair preserves the model and is not a model change.
For an external-review Exchange, the registry also mirrors the active
controller's current model and thinking for the return message. This mirror
does not select the controller model and must be refreshed from live task
metadata whenever the user changes it.

Use one implementer for a coupled change. Use two or three only when interfaces
are frozen and write scopes are disjoint. One file has one writer; the
controller or one integration implementer owns shared integration files. The
controller personally inspects the integrated diff, one focused check, and the
resulting evidence. Do not create internal reviewer subagents. After two failed
delegated attempts on the same frozen task, the controller implements it
directly. Respect the eight-thread ceiling and spawn depth one.

Return `BLOCKED` only for missing authority, a genuine contract conflict, or a
required scope expansion. Do not turn ordinary uncertainty into an approval
loop.

## Repository and Runtime

Use one source for each fact:

- Git-tracked code is implementation and version truth;
- `logs/<run-id>/` is runtime evidence;
- the five files in `docs/project/` are the active control plane;
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

## Experiments and External Review

Every real experiment lifecycle uses `$hmasd-experiment` and the owning
`docs/project/ExpRecord.md` contract. Implementation completion never launches
training. Formal runs use their registered CUDA/parallel topology and placement;
never silently fall back to CPU, serial execution, or another host. Monitoring,
deadlines, retry limits, and terminal closure live only in that Skill and its
protocol.

Every full external-review round uses `$hmasd-review-round`. Gemini and open Pro
are blind divergent reviewers with equal standing; controller synthesis precedes
convergent Pro. Reviewers recommend but never authorize code, experiments,
promotion, retirement, or a unique legal research direction. State, transport,
deadlines, raw archival, and recovery mechanics live only in that Skill.

## State Updates and Communication

Update the owning control file only at an accepted core implementation,
pre-launch, terminal experiment result/disposition, accepted external-review
disposition, autonomy-state change, or explicit controller handoff. Git history
preserves deleted history; do not maintain parallel archives or duplicate
commands, thresholds, status, or results.

Report only the domain that changed. Separate facts from inference, and omit
generic unchanged-state disclaimers unless they block the next action or the
user asks.
