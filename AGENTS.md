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

Direct controller work is the default. Explanations, status, bounded inspection
or diagnosis, small edits, simple bugs, ordinary Git/docs, prompt generation,
and routine continuation use no Skill, brief, subagent, or reviewer.

Use one matching project Skill only when its full lifecycle is required:

- `$hmasd-work`: collaboration-dependent multi-file core implementation;
- `$hmasd-experiment`: real experiment launch, monitoring, repair, or closure;
- `$hmasd-review-round`: a complete tracked Gemini/Pro review round.

The active controller uses the strongest available model and alone decides the
algorithm, architecture, causal route, reuse/replacement, data and gradient
flow, invariants, and stability goals. Implementers execute that frozen design;
reviewers inspect it. Detailed mechanics live only in the matching Skill and its
protocol. Never reconstruct them in an ad hoc prompt.

Respect the configured eight-thread ceiling and spawn depth one. Select a model
only when creating a new subagent; never change an existing conversation's
model. Return `BLOCKED` on missing authority, a contract conflict, or required
scope expansion.

## Research Loop

HMASD is an algorithm-exploration project. At architecture or research-direction
boundaries, keep two to four competing causal hypotheses and, when useful, two
to four candidate architectures. Separate intellectual exploration from compute
scheduling: ideas may be generated and compared in parallel, while mutating
implementation and experiment execution remain serialized to one evidence
source at a time.

```text
divergent candidate generation
-> live hypothesis and architecture portfolio
-> choose the next evidence source by expected information gain
-> smallest coherent implementation, reanalysis, prototype or controlled run
-> interpret the evidence against the whole portfolio
-> reweight, merge or retire only evidence-resolved branches; repeat or stop
```

Progress means new algorithm capability, new experimental evidence, or a
decision that materially changes the hypothesis portfolio. One active evidence
source does not mean one permitted research direction. A focused run may target
one discriminating observable, but neither the controller nor a reviewer may
declare a unique route merely because compute is serialized. Multiple
hypotheses do not authorize parallel competing implementations or training;
choose the active evidence source by information gain and relevance to the final
target. Documentation, status prose, audits, artifact inventories, repeated
state checks, and workflow discussion are support work, not the primary
objective.

Keep process subordinate to code and evidence. Record only the minimum contract
needed to prevent an invalid experiment. Do not re-prove accepted facts unless a
concrete contradiction blocks the current test.

There is no separate algorithm-verification stage. Let the next
evidence-bearing diagnostic or controlled run exercise a coherent change. Add a
focused check only after a concrete operational failure, or when the run cannot
cheaply expose a direct corruption or wrong-experiment risk. Ordinary
engineering receives at most one direct behavioral check when use itself is not
demonstrative.

Diagnose an operational crash and retry only the failed path. Apply the research
failure-review gate only to a valid non-PASS scientific result. Preserve its
registered estimand, thresholds, and outcome branches.

Do not turn terminal toy results into an automatic sequence of new toys. Every
toy must test a capability that is necessary for the final target: one shared
algorithm with variable team membership and variable skill lifetime. Before a
new route is implemented, record in its review question:

- the final capability it unlocks and what later integration would consume it;
- a replacement ledger: what is deleted, retained, and added;
- at least two competing causal explanations for the current evidence and the
  smallest observation that separates them;
- the strongest ordinary baseline or standard-MARL objection;
- the next serialized evidence source, the outcome-dependent updates for every
  live candidate and the conditions that would exhaust the whole portfolio.

Prefer architectural replacement and simplification over module accumulation.
Passing an isolated mechanism gate does not by itself authorize integration.

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

Use one stable pre-launch commit/push and one terminal result/disposition
boundary. Do not commit progress pointers, dry runs, or wording alone; runtime
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
parallel topology; diagnose topology only after an actual launch failure or for
a genuinely new workload shape.

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

Use `$hmasd-review-round` only for a cross-round architecture contradiction, a
coherent route connected to the final variable-team plus variable-lifetime
algorithm, or a critical promotion or retirement boundary that the registered
contract cannot settle; routine prompts and registered PASS/FAIL interpretation
stay direct. Gemini and open Pro are blind divergent reviewers with equal
standing; controller synthesis precedes convergent Pro. Reviewers recommend but
never authorize code, experiments, promotion, disposition, or a unique legal
research direction.

Reuse the registered persistent, role-specific conversations and never create
duplicates, mix open/convergent roles, change an existing model, or submit them
in parallel. Pro transport uses the Skill's guarded direct format with explicit
target host/thread/model/effort and pre/post identity checks. Archive every raw
before interpretation; missing or ambiguous raw is incomplete evidence. All
other transport and recovery mechanics live only in `$hmasd-review-round` and
`docs/external-review/README.md`.

## State and Memory

Keep the four root memory files compact and current:

- `CURRENT_WORK.md`: controller, objective, actions, constraints, pointers;
- `ALGORITHM_PRINCIPLES.md`: durable research contract;
- `IMPLEMENTATION_PLAN.md`: current staged core work;
- `ExpRecord.md`: formal experiment dashboard.

At each meaningful boundary, update the one owning file. Durable designs and
decisions belong in `docs/research/`; raw reviews in `docs/external-review/`;
unique legacy imports in `docs/archive/`. Git history preserves removed
material. Do not create memory archives or duplicate commands, thresholds,
status, or results.
