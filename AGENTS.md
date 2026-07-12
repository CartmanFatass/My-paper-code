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

## Controller Role

The controller owns task understanding, execution, verification, scientific
interpretation, user communication, and final decisions. It must:

- clarify ambiguous scope, assumptions, success criteria, and scientific claims;
- inspect the codebase before non-trivial implementation decisions;
- implement the work directly and carry it through verification;
- separate factual evidence from interpretation and recommendation;
- preserve unrelated user changes in a dirty worktree;
- explain changed files, checks run, unresolved risk, and next actions.

**Process must be proportional to risk.** Ordinary bounded work needs no design
document, plan, progress ledger, status file, review package, or multi-stage
review. Use those only when they materially reduce risk or preserve evidence.

Core algorithm and numerical code may be written directly, with explicit
reasoning about tensor shapes, gradient flow, detach boundaries, clocks, masks,
reward scale, advantage semantics, checkpoint compatibility, and collector
behavior as applicable.

Git is the sole source-version manager. Do not add application-layer hashes or
checksums to active workflows. Experiment identity uses registered
experiment/checkpoint names, paths, seeds, and run directories.

## Controller Communication

When experiment evidence, plan state, or implementation results change what the
user should understand, give a compact handoff — never make the user ask what a
result means:

- **Situation:** what is running, complete, blocked, or waiting.
- **Meaning:** what the facts imply, evidence separated from inference.
- **Next plan / recommendation:** the next permitted action and the branch for
  likely outcomes. Waiting is a valid recommendation — if so, name exactly what
  is being waited on and what must not change meanwhile.
- **Core MARL impact:** whether reward, policy/critic architecture,
  optimizer/loss/advantage, collector semantics, environment dynamics, credit
  assignment, team intent, or latent-skill semantics are affected.
- **Open gates:** the metric, null, review, or user decision still required.

## Experiments

**When an experiment's state or interpretation actually changes** — launching,
stopping, accepting, rejecting, or reinterpreting one — additionally state:
hypothesis and causal edge; comparator and baseline level; metrics, thresholds,
nulls, seeds, and update exposure; PASS/FAIL/MIXED/UNDERPOWERED/INVALID branches
and the single next action each authorizes; what must not change while the gate
is open; and the status source.

Register that same content in `memory/ExpRecord.md` before a meaningful launch.
A status check, a progress read, or a mechanical command is **not** an experiment
transition — answer it plainly and do not manufacture a scientific read.

Every compute-bearing proposal states expected wall-clock cost before launch.
Experiments default to CUDA; never silently fall back to CPU — if the GPU is
occupied, present the options with their costs and let the user choose.

Long training, multi-seed batches, and heavy analysis default to the user's cloud
server: write a self-contained Bash runner under `scripts/` following existing
conventions; use timestamped roots under `logs/`; record commands, expected
artifacts, device, env count, seed, timesteps, and eval cadence in
`memory/ExpRecord.md`; commit and push before asking the user to pull and launch.
The local GPU is for smokes and small diagnostics.

Preserve negative results as constraints. Do not rename, delete, reinterpret, or
re-run a failed line until it looks favorable, and do not redesign metrics after
viewing results.

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
algorithm suite. Do not claim completion from stale or partial evidence.

## External Review

Archive external model responses raw before interpreting them — a summary is a
pointer, not evidence. Read the raw text and disposition the advice
(accept/reject/modify/defer). If raw text is missing, mark the evidence
incomplete. Record source model, date, related claim, and disposition.

## Memory Shape

Keep root `memory/` compact and current — `CURRENT_WORK.md` (objective, active
causal edge, next actions, pointers), `ALGORITHM_PRINCIPLES.md` (research
contract), `IMPLEMENTATION_PLAN.md` (staged ledger), `ExpRecord.md` (factual
dashboard). Target: each stays small enough to read in full without cost.

**Rotate, don't accumulate.** When a round completes or is superseded, move its
long-form detail to `memory/LTM/` and leave a pointer. Update compact memory only
at meaningful plan, implementation, experiment, result, or external-review
boundaries.
