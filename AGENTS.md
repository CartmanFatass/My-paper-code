# HMASD Codex Project Instructions

The active project contract. Operational rules only — the research contract
lives in `memory/ALGORITHM_PRINCIPLES.md`.

The previous delegated-agent and Superpowers process rules are retired. Do not
infer routing, review, lifecycle, or process rules from historical files
(`.codex/agents/`, `docs/superpowers/`, `docs/subagents/` are provenance, not
authority). The controller works directly.

## First Read

Read `memory/CURRENT_WORK.md`. That is the only mandatory read.

Then read on demand, not by default:

- `memory/ALGORITHM_PRINCIPLES.md` — before any algorithm/reward/experiment
  design decision. It carries the falsifiable causal edges, the four-level
  baseline hierarchy, the experiment promotion ladder, and the failure-review
  gate. **These bind every experiment; read them before designing one.**
- `memory/IMPLEMENTATION_PLAN.md` — the active gate's section.
- `memory/ExpRecord.md` — the dashboard row for the experiment in question.
- `memory/LTM/` — only when a compact file points there or the user asks.

Codex and Claude Code alternate as controller; only one may modify the repo at a
time. Update the `Controller Handoff` block in `memory/CURRENT_WORK.md` when
ownership changes.

## Primary Mode: Algorithm Exploration

HMASD is an active algorithm-research project. The default work cycle is:

```text
one falsifiable causal question
-> smallest implementation or diagnostic that can answer it
-> focused smoke
-> parallel decision-grade experiment when needed
-> scientific interpretation
-> one next causal edge
```

Project progress means at least one of the following: new algorithm code that
enables the next causal test, new experiment evidence, or a decision that
eliminates a research branch and selects the next one. Status prose, process
documents, audit packages, artifact inventories, repeated consistency checks,
and workflow discussion are not algorithm progress.

The majority of active work time must go to algorithm implementation,
experiment execution, or interpretation of newly produced evidence. Process is
strictly subordinate: record only the minimum contract needed to avoid an
invalid experiment, update it inline at the evidence boundary, and return to
code or compute. Never make documentation, review, repository inspection,
resource polling, or artifact completeness checking the primary next action
when the next causal implementation or experiment is already known.

Do not re-prove accepted facts before moving forward. Reopen evidence only when
a concrete contradiction blocks the current causal test. A hard gate prevents
wrong or uninterpretable compute; it must not become a separate workstream.

## Lean Project Loop

The controller works directly. For each step, use the lightest applicable lane;
move to a heavier lane only when the next action actually requires it:

1. **Ordinary engineering:** inspect, implement, run the smallest focused checks
   that support the completion claim, and commit. This includes docs, SSH,
   packaging, CI, repository hygiene, dashboards, and runner maintenance. Do not
   create a design, plan, ledger, review package, or extra report.
2. **Engineering smoke:** run a small local command through the existing CLI
   (CUDA when it updates a model), read the existing manifest/metrics/checkpoint
   once, report engineering PASS/FAIL, and stop. It needs no ExpRecord
   transition, scheduler entry, custom runner, duplicate status file, or
   standalone validator. A missing frozen input is a separate artifact
   prerequisite: report it and stop rather than silently turning the local
   smoke into an SSH or remote-compute workflow.
3. **Formal experiment:** use the research contract and the hard gates below.
   Long, multi-seed, or conclusion-bearing compute belongs here.
4. **Status/result read:** inspect existing artifacts and answer directly. Do
   not edit code or memory unless the experiment's state or interpretation
   actually changes.

Do not silently promote work into a heavier lane. Add reusable orchestration
only for repeated matrices, remote/long jobs, or after a concrete failure proves
it is needed. Stop when the requested behavior and its immediate failure path
work.

Operational failure and scientific failure are different. Diagnose an
operational crash directly and run one focused confirmation. Apply the research
failure-review gate only to a non-PASS scientific result; keep that review in the
same experiment record unless two related gates fail or the research direction
changes.

## One Source Per Fact

- Git-tracked code is the implementation and version source.
- `logs/<run-id>/` is the runtime-evidence source.
- `memory/CURRENT_WORK.md` holds controller ownership, the current objective,
  next actions, immediate constraints, and pointers.
- `memory/IMPLEMENTATION_PLAN.md` holds only staged core-algorithm work.
- `memory/ExpRecord.md` holds only formal experiment contracts and decisions.

Record each fact in detail once. Other files may contain only a short pointer,
not a second copy of the command, thresholds, status, or result. Update the
owning source only at a meaningful boundary. Git is the sole version manager;
do not add application-layer hashes or checksums.

## Formal Experiment Hard Gates

Before a meaningful formal launch, read `memory/ALGORITHM_PRINCIPLES.md` and
ensure that experiment's single contract block in `memory/ExpRecord.md` records
the causal edge, upstream authorization, comparator/baseline level, metrics and
thresholds,
nulls, seeds, environment steps and optimizer updates, outcome branches with one
next action each, prohibited changes, expected wall clock, and status source.
Do not manufacture this record for a smoke, status check, or mechanical command.

Formal experiments default to CUDA and parallel execution sized for the wall
clock target. Never silently use CPU or serial fallback. Validate a matching
process/GPU topology once before a new workload shape; a failure stops launch.

Long training, multi-seed batches, and heavy analysis default to the cloud.
Reuse a compatible self-contained Bash runner under `scripts/`; create or
modify one only for a new workload shape. Write outputs under a timestamped
`logs/` root on the data disk, commit and push, then register the exact committed
job with the shared scheduler. The local GPU is for smokes and small
diagnostics. Treat the server as available by default and ask the user to wake
it only after a real SSH failure.

Preserve negative results as constraints. Do not rename, delete, reinterpret,
retune, or rerun a failed line until it looks favorable; do not redesign metrics
after reading results.

## Controller Communication

Scope every report to the domain that actually changed:

- algorithm/code changes report only the affected algorithm semantics,
  implementation, focused verification, and remaining algorithm risk;
- experiment transitions or result reads report only the experiment contract,
  execution state, evidence, interpretation, and next gate;
- infrastructure, Git, packaging, or artifact-transfer work reports only its
  operational outcome and immediate failure path.

Do not append generic unchanged-state disclaimers such as "no compute was
launched", "the server need not be started", "formal training is not
authorized", or "core MARL is unchanged". Mention such a fact only when it
changed, directly blocks the requested next action, or the user asks about it.
Keep factual evidence separate from inference.

Core MARL changes require explicit reasoning about applicable tensor shapes,
gradient flow, detach boundaries, clocks, masks, reward scale, advantage
semantics, checkpoint compatibility, and collector behavior. Preserve unrelated
user changes in a dirty worktree.

## Engineering Discipline

- Prefer existing repository patterns; keep changes scoped to the request.
- Use structured parsers and APIs, not ad hoc string manipulation.
- Add abstractions only when they remove real complexity.
- Scale tests with behavioral risk and blast radius.
- Use `rg` / `rg --files` for search; `apply_patch` for manual edits.
- Default to ASCII unless the file already uses otherwise.
- Comment only to clarify non-obvious logic.

The worktree may contain user changes: never revert or overwrite what you did not
write; work with overlapping edits; ignore unrelated dirty files; never
`git reset --hard`, destructive checkout, or force-push without an explicit
request; stage and commit only the intended files.

## Runtime Output And Test Hygiene

New experiment outputs go under `logs/<experiment-id-or-run-id>/...` unless a
registered runner requires another root. No loose root-level logs, CSVs, status
files, checkpoints, or temp artifacts.

Persistent tests go under `tests/`. Do not create root-level `test_*.py`,
`*_test.py`, or `.pytest_tmp*` scratch paths; put pytest temp output under
`tests/.pytest_tmp/<task-id>` and remove it when passing.

Verification must support the completion claim: changed code needs a focused test
for the changed path; config/syntax changes need the relevant check; experiment
packages need dry-run/path/dependency checks; result claims need the registered
artifacts and null controls read. A docs-only change does not need the full
algorithm suite. Existing manifests, metrics, logs, and checkpoints should be
read directly instead of duplicated into wrapper reports. Do not claim
completion from stale or partial evidence.

Do not perform broad or repeated local experiment-artifact completeness scans.
Use the registered status source for accepted results, and inspect only the
specific artifact needed for a new result claim or a concrete failure diagnosis.

## External Review

Archive external model responses raw before interpreting them — a summary is a
pointer, not evidence. Read the raw text and disposition the advice
(accept/reject/modify/defer). If raw text is missing, mark the evidence
incomplete. Record source model, date, related claim, and disposition.

## Memory Shape

Keep root `memory/` compact and current — `CURRENT_WORK.md` (controller,
objective, actions, constraints, pointers), `ALGORITHM_PRINCIPLES.md` (research
contract), `IMPLEMENTATION_PLAN.md` (current core stage), and `ExpRecord.md`
(formal dashboard). Target: each stays small enough to read in full without
cost.

**Rotate, don't accumulate.** When a round completes or is superseded, move its
long-form detail to `memory/LTM/` and leave a pointer. Update compact memory only
at meaningful plan, implementation, experiment, result, or external-review
boundaries.
