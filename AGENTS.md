# HMASD Codex Project Instructions

The durable scientific contract lives in `memory/ALGORITHM_PRINCIPLES.md`.
The durable MARL implementation contract lives in
`docs/research/MARL_ENGINEERING_PRINCIPLES.md`.

## Project Entry and Controller

Read `memory/CURRENT_WORK.md` first. It is the only mandatory default read. Read
additional sources only when the task crosses their boundary:

- `memory/ALGORITHM_PRINCIPLES.md` before algorithm, reward, benchmark,
  scientific-evidence, or experiment-contract decisions;
- `docs/research/MARL_ENGINEERING_PRINCIPLES.md` before implementing or
  reviewing training, runtime, collector, replay, evaluation, intervention
  audit, analyzer, or runner code;
- the active `memory/IMPLEMENTATION_PLAN.md` section before staged core work;
- the relevant `memory/ExpRecord.md` row before a formal experiment or
  scientific result decision;
- `docs/research/`, `docs/external-review/`, or `docs/archive/` only through a
  current pointer or explicit request.

One active controller works directly in `C:\project\HMASD` and owns project
decisions, root memory, scientific interpretation, experiment authorization,
final Git integration and push, and user communication.
`memory/CURRENT_WORK.md` names that task; controller ownership changes only
through an explicit handoff recorded there.

## Unified Collaboration Workflow

Direct controller work is the default. Explanations, status reads, bounded
inspection or diagnosis, one-file changes, Git/docs, prompt generation, result
interpretation and routine continuation stay direct.

Only three project Skills own conditional workflows:

- use `$hmasd-research-cycle` for an explicit autonomous research iteration, an
  unresolved architecture boundary, selection of a discriminating evidence
  source, or a valid result that must reweight the live portfolio;
- use `$hmasd-experiment` for authorized experiment lifecycle mutations;
- use `$hmasd-review-round` for a tracked five-stage external-review round.

Generic skills are optional techniques selected by the controller. They do not
own project planning, delegation, review, edit, commit, Git, memory or scientific
decision boundaries. Existing HMASD authorization satisfies the approval
boundary for its registered scope; do not request it again. Do not create a
worktree unless the user explicitly requests one.

Active-line development is the default. Do not implement or retain
backward-compatibility adapters, deprecated runtime branches, old library
interfaces, legacy transport formats or migrations for superseded checkpoints.
Historical code and artifacts are not executable or design dependencies. Read
them only when a current research question explicitly names them as evidence;
otherwise do not inspect, import, adapt or test them. When the active design
replaces a component, delete the replaced path instead of keeping a
compatibility switch. Only an explicit current user instruction may reopen a
retired interface.

Scientific exploration rules live only in `memory/ALGORITHM_PRINCIPLES.md`.
MARL implementation and efficiency rules live only in
`docs/research/MARL_ENGINEERING_PRINCIPLES.md`. A task that changes both
scientific semantics and executable MARL code reads both. Do not duplicate
either contract in this file or in a project Skill.

For staged core work, keep one persistent plan in
`memory/IMPLEMENTATION_PLAN.md` with one `HMASD Contract` section. Freeze the
causal or engineering goal, evidence boundary, reused/replaced/deleted/added
components, exact files and symbols, tensor and collector flow, state ownership,
gradient and detach boundaries, reward and advantage semantics, probability,
RNG, replay, masks, clocks, active checkpoint semantics, preserved current
interfaces and non-goals.
Do not create a parallel collaboration brief or duplicate plan.

One active implementation plan or serialized evidence source does not imply one
research hypothesis, architecture or permitted successor. Research keeps a
live competing portfolio; implementation and compute are serialized only to
preserve attribution and workspace integrity.

The active controller alone decides the algorithm, architecture, causal route,
reuse/replacement, data and gradient flow, invariants and stability goals. Freeze
those decisions in the active plan before delegated implementation; unresolved
core semantics return directly to the controller.

Project files do not select or record the controller model. Every newly spawned
HMASD implementer or implementation fixer uses gpt-5.6-sol xhigh. Never change
an existing conversation's model; stop it and create a correctly routed
replacement when a route must change. The active controller personally inspects
every integrated implementation, focused check and evidence result; do not
spawn internal reviewer subagents. If delegated implementation fails twice on
the same task, stop delegating and the active controller takes over under the
same frozen contract and evidence boundary.

Use one implementer by default. When two or three implementation packages have
frozen interfaces and disjoint write scopes, run them in parallel. One file has
one writer; shared or strongly coupled integration files belong to the
controller or one designated integration implementer. Parallel implementation
must reduce the critical path rather than duplicate competing solutions.

Respect the configured eight-thread ceiling and spawn depth one. Return
`BLOCKED` on missing authority, a contract conflict or required scope expansion.

## Scientific and Engineering Contracts

Use `memory/ALGORITHM_PRINCIPLES.md` for portfolio construction, evidence
selection, reward boundaries, toy relevance, result semantics, and scientific
disposition. Use `docs/research/MARL_ENGINEERING_PRINCIPLES.md` for tensor and
device structure, batching, replay, RNG, recurrent state, persistence,
observability, and final experiment-code review. Current routes and exact
symbols remain in `CURRENT_WORK.md` and `IMPLEMENTATION_PLAN.md`, not in either
durable principles file.

## Repository and Runtime

Use one source for each fact:

- Git-tracked code is the implementation and version source.
- `logs/<run-id>/` is the runtime-evidence source.
- `memory/CURRENT_WORK.md` holds the controller, objective, next actions,
  immediate constraints, and pointers.
- `memory/IMPLEMENTATION_PLAN.md` holds active staged core work.
- `memory/ExpRecord.md` holds formal experiment contracts and decisions.

Git is the sole version manager; do not add hashes or checksums. While the
controller owns `aggressive`, push with `git push My-paper-code aggressive`. If
Git/MSYS fails with a Win32 pipe or permission error, retry that exact command
with scoped escalation.

The only default project boundaries are: accepted core implementation,
pre-launch, terminal experiment result/disposition, one pre-convergent
external-evidence package when the reviewer requires Git-visible inputs,
accepted external-review disposition, and explicit controller handoff. Use one stable pre-launch
commit/push and one terminal result/disposition boundary. Do not commit progress
pointers, dry runs, or wording alone; runtime
state stays in `logs/`. Batch related docs, and switch once to an exact fallback
if an edit method is rejected. Generate a timestamp once at real launch; dry
runs use `DRY_RUN`.

Preserve unrelated user changes in a dirty worktree and stage only intended
files. Apply `docs/research/MARL_ENGINEERING_PRINCIPLES.md` to every changed
MARL execution path rather than restating its checklist here.

Remove controller-created transient files at their evidence boundary. Delete
only exact verified paths under the project or OS temp directory; never remove
unrelated or user-created files.

New experiment output belongs under `logs/<experiment-id-or-run-id>/`. Do not
write loose root-level logs, CSVs, status files, checkpoints, or temp artifacts.
Persistent tests belong under `tests/`; pytest temp output belongs under
`tests/.pytest_tmp/<task-id>` and is removed after success. Do not perform broad
or repeated artifact-completeness scans; inspect the registered status source
and only the artifact needed for a result claim or concrete failure.

## Formal Experiments

Use `$hmasd-experiment` for every real experiment lifecycle. Before launch, read
`memory/ALGORITHM_PRINCIPLES.md` and the owning `memory/ExpRecord.md` contract;
it fixes the causal edge, authority, comparator, metrics, budgets, branches,
prohibitions, expected wall clock, placement, and status authority. If the run
uses new or changed executable MARL code, close the single pre-launch review in
`docs/research/MARL_ENGINEERING_PRINCIPLES.md`; unchanged frozen code does not
repeat that review.

Formal experiments use CUDA and parallel execution sized for the wall-clock
target. Do not silently fall back to CPU or serial execution. Reuse a known
parallel topology; diagnose topology only after an actual launch failure or when
the registered collector backend, environment count, or memory envelope has no
known-good topology.

Long, multi-seed, or heavy work defaults to cloud data storage and a background
runner. An explicit authorization and contract may place bounded work on local
CUDA. Never migrate placement silently; request server wake-up only after a real
connection failure.

Each launched run uses one depth-one `gpt-5.6-terra` medium monitor subagent.
The child remains active until the registered status authority reaches a
terminal state, then returns one final payload that the subagent runtime
delivers to `/root`. The controller does not create a monitor conversation,
heartbeat or automation and performs no status or child polling. A mailbox wait
is not status polling: keep at most one active `wait_agent` for the same child at
a time. If a native wait times out while that child remains active, wait on the
same child again without an intervening status/child read, sleep, poll or
replacement monitor.

Negative results are binding constraints. Do not retune, rename, reinterpret,
or rerun a failed line without a newly registered causal reason.

## Communication

Report only the domain that changed:

- algorithm work: semantics, implementation, direct evidence, remaining risk;
- experiment work: contract, execution state, result, interpretation, next gate;
- infrastructure or Git: operational outcome and immediate failure path.

Separate facts from inference. Do not append generic unchanged-state
disclaimers such as server availability, absent compute, or unchanged MARL
unless the fact changed, blocks the next action, or the user asked.

## External Review

Use `$hmasd-review-round` only when the controller creates or resumes its full
tracked five-stage round. A new round may address a cross-round architecture
contradiction, a route connected to the final variable-team plus
variable-lifetime algorithm, or a promotion/retirement boundary that the
registered contract cannot settle. Routine prompts, one returned review,
literature discussion, and registered PASS/FAIL interpretation stay direct.
Gemini and open Pro are blind divergent reviewers with equal
standing; controller synthesis precedes convergent Pro. Reviewers recommend but
never authorize code, experiments, promotion, disposition, or a unique legal
research direction.

Reuse the registered Gemini Codex Exchange and the two persistent role-specific
ChatGPT Pro sessions. Gemini alone uses guarded `send_message_to_thread` calls
with only `hostId`, `threadId` and `prompt`; never pass `model` or `thinking`.
The active controller accesses both Pro sessions directly through the pinned
`codex-chatgpt-control` plugin and the `chatgpt-delegate` workflow. Never create
or resume a Pro Codex Exchange, substitute a reviewer session, mix roles, or
submit roles in parallel. Submit once, verify the visible `Pro` setting, and
use bounded status/read calls on the same registered URL until natural
completion. Do not use review transport subagents, cross-task Pro relays,
heartbeat, automation, shell sleep or page controls that shorten, stop,
regenerate, retry or continue a response. Archive every raw before
interpretation; missing or ambiguous raw is incomplete evidence. Private
local-source transfer to an external reviewer requires explicit informed
approval recorded against the exact allowlist path, Git commit, destination and
user-message reference. The registered Gemini reviewer has standing user
approval for project-only, tracked, read-only per-round manifests, so the
controller records that exact boundary automatically without asking again.
Any allowlist change invalidates the recorded boundary; credentials, personal
data, project-external paths, writes, execution and training remain excluded.
Other transport and recovery mechanics live only in `$hmasd-review-round`.

## State and Memory

Keep the four root memory files compact and current:

- `CURRENT_WORK.md`: controller, objective, actions, constraints, pointers;
- `ALGORITHM_PRINCIPLES.md`: durable scientific exploration contract;
- `IMPLEMENTATION_PLAN.md`: current staged core work;
- `ExpRecord.md`: formal experiment dashboard.

`docs/research/MARL_ENGINEERING_PRINCIPLES.md` is the durable implementation
contract read only for relevant MARL code work; it is not a fifth root memory
file.

Update the owning file only at an accepted core implementation, pre-launch,
terminal result/disposition, accepted external-review disposition, or explicit
controller handoff. Durable designs and
decisions belong in `docs/research/`; raw reviews in `docs/external-review/`;
unique historical evidence in `docs/archive/`. Git history preserves removed
material. Do not create memory archives or duplicate commands, thresholds,
status, or results.
