# HMASD Codex Project Instructions

The durable research contract lives in `memory/ALGORITHM_PRINCIPLES.md`.

## Project Entry and Controller

Read `memory/CURRENT_WORK.md` first. It is the only mandatory default read. Read
additional sources only when the task crosses their boundary:

- `memory/ALGORITHM_PRINCIPLES.md` before algorithm, reward, or experiment
  design;
- the active `memory/IMPLEMENTATION_PLAN.md` section before staged core work;
- the relevant `memory/ExpRecord.md` row before a formal experiment or
  scientific result decision;
- `docs/research/`, `docs/external-review/`, or `docs/archive/` only through a
  current pointer or explicit request.

One active controller works directly in `C:\project\HMASD` and owns project
decisions, root memory, Git integration, scientific interpretation, experiment
authorization, and user communication. `memory/CURRENT_WORK.md` names that task
and is writable only by it. A new controller may write only after an explicit
handoff recorded there.

Implementers read root memory but do not edit it. Reviewers, monitors, and side
conversations are read-only unless the controller gives an exact non-root-memory
write scope.

## Unified Collaboration Workflow

Direct controller work is the default. Use no project Skill when the task does
not create or mutate collaboration state, experiment lifecycle state, or a
tracked external-review round, unless the user explicitly invokes a matching
Skill. In particular, without such explicit invocation, explanations, status reads,
read-only diagnosis, one-file changes, Git/docs, prompt generation, result
interpretation, and routine continuation stay direct.

Activate exactly one matching project Skill only under its observable trigger:

- `$hmasd-work`: the user names it, or the controller will delegate a coupled
  core change spanning at least two implementation files to an implementer and
  a combined reviewer;
- `$hmasd-experiment`: the action creates or mutates an experiment contract,
  package, launch, persistent monitor, failed runtime stage, or terminal closure;
- `$hmasd-review-round`: the action creates or resumes a tracked five-stage
  round governed by `05_REVIEW_STATE.json`.

The user-selected active controller model is fixed for the task; never select,
upgrade, downgrade, or repair it automatically. The active controller alone decides the
algorithm, architecture, causal route, reuse/replacement, data and gradient
flow, invariants, and stability goals. Implementers execute that frozen design;
reviewers inspect it. Detailed mechanics live only in the matching Skill and its
protocol. Never reconstruct them in an ad hoc prompt.

Respect the configured eight-thread ceiling and spawn depth one. Select a model
only when creating a new subagent; never change an existing conversation's
model. Return `BLOCKED` on missing authority, a contract conflict, or required
scope expansion.

## Research Loop

HMASD is an algorithm-exploration project. At architecture or direction
boundaries, keep two to four causal hypotheses and, when useful, two to four
candidate architectures. Generate and compare ideas in parallel, but serialize
mutating implementation and compute through one active evidence source. One
evidence source does not imply one permitted research direction.

```text
live hypothesis and architecture portfolio
-> choose a discriminating observation by information gain and final relevance
-> smallest coherent implementation, reanalysis, prototype or controlled run
-> interpret the evidence against the whole portfolio
-> reweight, merge or retire only evidence-resolved branches; repeat or stop
```

Progress means new algorithm capability, new experimental evidence, or a
decision that changes the portfolio. Documentation, audits, inventories,
repeated state checks, and workflow prose are support work. Keep contracts to
the minimum needed to prevent an invalid experiment, and do not re-prove an
accepted fact without a concrete contradiction.

There is no separate algorithm-verification stage. Let the next
evidence-bearing diagnostic or run exercise a coherent change. Add at most one
focused check for a concrete operational failure or a corruption risk the run
cannot cheaply expose. Retry only the failed operational path. Apply scientific
failure review only to a valid non-PASS result and preserve its estimand,
thresholds, and outcome branches.

Every toy must test a capability needed by the final target: one shared algorithm
with variable team membership and variable skill lifetime. Before implementing
a new route, its review question must record:

- the final capability it unlocks and what later integration would consume it;
- a replacement ledger: what is deleted, retained, and added;
- at least two competing causal explanations for the current evidence and the
  smallest observation that separates them;
- the strongest ordinary baseline or standard-MARL objection;
- the next serialized evidence source, the outcome-dependent updates for every
  live candidate and the conditions that would exhaust the whole portfolio.

Do not chain toys automatically. Prefer replacement and simplification over
module accumulation; an isolated mechanism pass does not authorize integration.

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
files. Core MARL changes must explicitly account for tensor shapes, gradient
and detach boundaries, clocks, masks, reward scale, advantage semantics,
checkpoint compatibility, and collector behavior.

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
`ALGORITHM_PRINCIPLES.md` and the owning `ExpRecord.md` contract; it fixes the
causal edge, authority, comparator, metrics, budgets, branches, prohibitions,
expected wall clock, placement, and status authority.

Formal experiments use CUDA and parallel execution sized for the wall-clock
target. Do not silently fall back to CPU or serial execution. Reuse a known
parallel topology; diagnose topology only after an actual launch failure or when
the registered collector backend, environment count, or memory envelope has no
known-good topology.

Long, multi-seed, or heavy work defaults to cloud data storage and a background
runner. An explicit authorization and contract may place bounded work on local
CUDA. Never migrate placement silently; request server wake-up only after a real
connection failure.

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

Reuse the registered persistent, role-specific conversations and never create
duplicates, mix open/convergent roles, change an existing model, or submit them
in parallel. Pro transport uses the Skill's guarded direct format with explicit
target host/thread/model/effort and pre/post identity checks. Archive every raw
before interpretation; missing or ambiguous raw is incomplete evidence. Private
local-source transfer to an external reviewer requires explicit informed
approval recorded against the exact allowlist path, Git commit, destination and
user-message reference. Any allowlist change invalidates that approval. Other
transport and recovery mechanics live only in
`$hmasd-review-round` and its protocol.

## State and Memory

Keep the four root memory files compact and current:

- `CURRENT_WORK.md`: controller, objective, actions, constraints, pointers;
- `ALGORITHM_PRINCIPLES.md`: durable research contract;
- `IMPLEMENTATION_PLAN.md`: current staged core work;
- `ExpRecord.md`: formal experiment dashboard.

Update the owning file only at an accepted core implementation, pre-launch,
terminal result/disposition, accepted external-review disposition, or explicit
controller handoff. Durable designs and
decisions belong in `docs/research/`; raw reviews in `docs/external-review/`;
unique legacy imports in `docs/archive/`. Git history preserves removed
material. Do not create memory archives or duplicate commands, thresholds,
status, or results.
