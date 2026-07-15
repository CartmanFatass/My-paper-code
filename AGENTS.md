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
- `memory/LTM/` only through a current pointer or explicit user request.

One controller owns project decisions and repository writes at a time. The
active controller works directly in `C:\project\HMASD` and owns implementation,
focused review, experiments, Git, and user communication. Do not create or
message auxiliary role conversations, subthreads, or worktrees unless the user
explicitly requests them. Scheduled status checks, when needed, use one bounded
heartbeat in the main conversation. Record controller changes in
`memory/CURRENT_WORK.md`.

## Research Loop

HMASD is an algorithm-exploration project. Use this cycle:

```text
one falsifiable causal question
-> smallest implementation or diagnostic that can answer it
-> smallest evidence-bearing controlled run
-> scientific interpretation
-> one next causal edge
```

Progress means new algorithm capability, new experimental evidence, or a
decision that eliminates a branch and selects the next edge. Documentation,
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

For every handoff, read
`docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md`, replace only its commit
and question-path placeholders, and include the resulting prompt verbatim in
the user-facing response.

## State and Memory

Keep the four root memory files compact and current:

- `CURRENT_WORK.md`: controller, objective, actions, constraints, pointers;
- `ALGORITHM_PRINCIPLES.md`: durable research contract;
- `IMPLEMENTATION_PLAN.md`: current staged core work;
- `ExpRecord.md`: formal experiment dashboard.

At each meaningful plan, implementation, experiment, result, or review
boundary, rotate superseded detail to `memory/LTM/` and leave one short pointer.
Do not duplicate commands, thresholds, status, or results across files.
