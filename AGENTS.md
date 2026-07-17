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

Only three repository workflows are user-facing:

- `$hmasd-work`: explicit or genuinely necessary collaboration for a non-trivial
  multi-file core algorithm, trainer, or runtime change;
- `$hmasd-experiment`: experiment contract, package, launch, persistent
  monitoring, failure diagnosis, and terminal result boundary;
- `$hmasd-review-round`: Gemini, open Pro, controller synthesis, convergent Pro,
  and review evidence archival.

Direct controller work is the default. Questions, explanations, status reports,
read-only inspection, bounded diagnosis, single-file edits, simple bugs,
ordinary Git or documentation, prompt generation, experiment-need decisions,
and routine continuation use no Skill, brief, subagent, reviewer, or plan
artifact. Even complex work stays direct when collaboration would not improve
it materially.

The active controller uses the strongest available model and exclusively
decides core algorithms, training architecture, causal hypotheses,
reuse/replacement/deletion, data and gradient flow, probability and clock
semantics, checkpoint invariants, and stability goals. Implementers execute a
frozen controller design and do not choose or redesign the route.

Invoke `$hmasd-work` only when the user explicitly names it or a non-trivial
multi-file core algorithm, trainer, or runtime change genuinely needs
collaboration. Such a task creates exactly one temporary artifact:

```text
.codex/collaboration/active/<task-id>/BRIEF.md
```

It contains authority, objective, necessary history, contracts, dependencies,
exact write scopes, dirty-worktree boundary, invariants, non-goals, focused
evidence, and stop conditions. Information priority is current user instruction,
then `BRIEF.md`, current repository contracts, and inherited relevant context.
Return `BLOCKED` on a real conflict.

Use one implementer for a coherent core implementation. Use bounded
implementers only for genuinely independent work packages with disjoint files
and a frozen interface; each file has one writer. Implementers inherit three to
five relevant turns, and the combined reviewer inherits one to three and reads
the same brief.

Use one fresh combined read-only reviewer after the complete diff is stable.
Route concrete findings to the original file owner, permit one repair/re-review
loop, and let the controller adjudicate anything unresolved. Task messages use
only `BLOCKED`, `PACKAGE_READY`, `REVIEW_READY`, and `COMPLETE`; do not send
heartbeat or unchanged-state messages.

Respect the configured eight-thread ceiling and spawn depth one. Choose a model
only while creating a subagent and only from the live runtime catalog. Never
change an existing task or reviewer conversation's model automatically. Detailed
mechanics live in the three project skills.

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

Batch repository and run boundaries:

- Make one pre-launch commit/push after code, runner, and contract are stable,
  then one result/disposition commit/push after the terminal outcome.
- Do not commit or push a launch pointer, progress-only memory update, dry-run,
  or status wording by itself. Runtime state belongs in `logs/` until the result
  boundary; an operational repair gets a commit only when tracked code changes.
- Batch related documentation edits after the implementation boundary settles.
  If one edit or deletion method is rejected, switch once to a verified exact
  fallback instead of retrying and restaging the same change repeatedly.
- Generate a timestamp exactly once when a real run starts. Dry-runs use a
  stable `DRY_RUN` placeholder and neither reserve nor report a real run ID.

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

Before a conclusion-bearing launch, read `memory/ALGORITHM_PRINCIPLES.md` and
the experiment's single `memory/ExpRecord.md` contract. That contract must name
the causal edge, authorization, comparator level, metrics and thresholds,
nulls, seeds, environment steps, optimizer updates, outcome branches,
prohibited changes, expected wall clock, and authoritative status source.

Formal experiments use CUDA and parallel execution sized for the wall-clock
target. Do not silently fall back to CPU or serial execution. Reuse a known
parallel topology; diagnose topology only after an actual launch failure or for
a genuinely new workload shape.

By default, long training, multi-seed batches, and heavy analysis run on the
cloud. Reuse a compatible Bash runner under `scripts/`, write outputs to a
timestamped `logs/` root on the data disk, commit and push the exact job, then
register it with the shared scheduler. An explicit user authorization and the
owning `ExpRecord.md` contract may instead place a bounded toy or formal run on
local CUDA. Follow that recorded placement and never migrate a run silently
between local and cloud. Treat the server as available and ask the user to wake
it only after a real SSH failure.

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
contract cannot settle. A routine registered PASS or FAIL does not trigger a
full round. Gemini and the open GPT-5.6 Pro are blind divergent reviewers with
equal standing. The controller archives both
raw responses, synthesizes them against repository evidence, and then submits
both plus the synthesis to the convergent GPT-5.6 Pro. The convergent review
ranks and stress-tests a plural portfolio; it may recommend the next serialized
evidence source, but it does not define a unique legal research direction.

Reuse the role-specific persistent reviewer conversations registered in
`docs/external-review/REVIEWER_CONVERSATIONS.json`; open and convergent Pro use
different external conversation IDs and are never mutual fallbacks. Each Pro
role also has a separate one-to-one local Codex exchange conversation and
heartbeat in that registry; the active controller does not perform Pro browser
transport or send Pro prompts directly across Codex threads. Wake only the
matching exchange heartbeat with no model/thinking override and require a
matching local-thread/role/external-thread/model ACK before any send. The
exchange pauses its heartbeat after exact raw archival or a transport blocker.
Dedicated experiment monitors and Pro exchange conversations are created as
`Luna High`; their models are frozen after creation and are never altered by a
heartbeat or later controller action.
GPT-5.6 Pro uses the Codex built-in browser; Gemini uses the persistent
Antigravity CLI conversation in plan and sandbox mode with the tracked
local-source allowlist. Before a Pro submission, verify the exact registered
URL, visible model and role heartbeat. Never change an existing conversation's
model or submit reviewers in parallel.

Archive every response raw before interpretation. Missing raw text is incomplete
evidence. Automatic exchange covers transport and archival only; no reviewer
authorizes code, experiments, promotion, or a scientific disposition. Use the
exact manual prompt when identity, authentication, page state, sources, or
response completeness is ambiguous. Detailed round mechanics live in
`docs/external-review/README.md` and `$hmasd-review-round`.

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
