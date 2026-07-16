# HMASD Codex Project Instructions

Active operational instructions for HMASD. The research contract lives in
`memory/ALGORITHM_PRINCIPLES.md`.

## First Read and Ownership

Read `memory/CURRENT_WORK.md` first. It is the only mandatory default read.

Read other sources only when needed:

- `memory/ALGORITHM_PRINCIPLES.md` before algorithm, reward, or experiment
  design.
- The active section of `memory/IMPLEMENTATION_PLAN.md` before staged core work.
- The relevant row of `memory/ExpRecord.md` before a formal experiment or
  scientific result decision.
- `docs/research/`, `docs/external-review/`, and `docs/archive/` only through a
  current pointer or explicit user request.

One controller owns project decisions and repository writes at a time. The
active controller works directly in `C:\project\HMASD` and owns implementation,
focused review, experiments, Git, and user communication. Do not create or
message auxiliary role conversations, subthreads, or worktrees unless the user
explicitly requests them. Scheduled status checks, when needed, use one bounded
heartbeat in the main conversation. Record controller changes in
`memory/CURRENT_WORK.md`.

## Research Loop

HMASD is an algorithm-exploration project. At architecture or research-direction
boundaries, keep two to four competing causal hypotheses while serializing
execution to one evidence source at a time:

```text
live hypothesis portfolio
-> one falsifiable question that separates at least two hypotheses
-> smallest implementation, reanalysis or diagnostic that can answer it
-> smallest evidence-bearing controlled run
-> scientific interpretation
-> update, retire or merge hypotheses; integrate one edge or stop
```

Progress means new algorithm capability, new experimental evidence, or a
decision that materially changes the hypothesis portfolio. Multiple hypotheses
do not authorize parallel implementation or training; choose the active
experiment by information gain and relevance to the final target. Documentation,
status prose, audits, artifact inventories, repeated state checks, and workflow
discussion are support work, not the primary objective.

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
- the one active evidence source, its outcome-dependent portfolio updates and
  abandonment condition, or an explicit stop.

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

Long training, multi-seed batches, and heavy analysis run on the cloud. Reuse a
compatible Bash runner under `scripts/`, write outputs to a timestamped `logs/`
root on the data disk, commit and push the exact job, then register it with the
shared scheduler. Use the local GPU for small diagnostics. Treat the server as
available and ask the user to wake it only after a real SSH failure.

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

Archive an external response raw before interpreting it. Record the source
model, date, related claim, and accept/reject/modify/defer disposition. Missing
raw text means incomplete evidence.

GPT-5.6 Pro exchange is manual by default. After committing and pushing the
tracked question, give the user one directly copyable prompt and stop that
review step. The user submits it in the existing `HMASD Algorithm Consultation`
conversation and returns the raw response. Use browser or Computer Use only
when the user explicitly authorizes automation for that specific round. Reuse
the existing consultation conversation and never submit parallel prompts.

Use Pro as a sparse convergent adversarial reviewer, not as the controller that
automatically invents the next experiment after every FAIL. A Pro exchange is
appropriate only at one of these boundaries:

1. a cross-round architecture audit after several terminal branches or a
   contradiction in the current causal model;
2. design review of a coherent route that could connect to the final
   variable-`N` plus variable-lifetime algorithm;
3. a critical result whose validity or promotion decision cannot be settled
   from the registered contract.

The controller must first supply repository evidence and a concrete Requested
decision. The review must separate facts from inference, compare the live causal
hypotheses, inspect the replacement ledger and final-capability map, and may
decide to stop. A valid FAIL never obliges Pro to produce a successor. Pro may
revise or rank the portfolio; if work continues it selects at most one active
evidence source, not one permanently privileged research route. Do not request
parallel executions.

For every handoff, read
`docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md`, replace only its commit
and question-path placeholders, and include the resulting prompt verbatim in
the user-facing response.

Use the persistent Antigravity CLI conversation for Gemini 3.1 Pro (High) as a
divergent architecture reviewer. Its workflow is owned by
`docs/external-review/gemini_3_1_pro/README.md` and
`scripts/invoke_gemini_reviewer.ps1`. Every round must contain a tracked
question and `SOURCE_MANIFEST.md`; the manifest is the complete local-file
allowlist for that turn. Run in plan and sandbox mode, reuse the HMASD-rooted
conversation, never use `--dangerously-skip-permissions`, and archive the raw
response before interpretation. Gemini proposes or challenges hypotheses; it
does not authorize repository edits, experiments or promotion. Do not run the
scripted and interactive clients concurrently against the same conversation.

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
