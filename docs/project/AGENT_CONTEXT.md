# HMASD Agent Context

Normative source for designing HMASD task profiles and assignment briefs. Task
agents do not load this document automatically: each profile and assignment
embeds only the standing constraints required by that role.

## Execution environment

- Run Python directly with
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`
  (`torch 2.7.0+cpu`) on the registered CPU backend.
- Use CPU with torch threads 1 for every arm and paired replicate. Never mix
  backends or thread configurations, and never resume a checkpoint across
  backends.
- Do not use `conda run`; invoke the registered interpreter directly.
- For scripts outside the repository root, set `PYTHONPATH` to this workspace.
- The focused suite and formal-path exercise use the registered CPU/one-thread
  contract and fail closed on backend or thread mismatch. Never add a fallback
  or infer CPU/CUDA trajectory equivalence.
- Collections run at 16 parallel environments (`FORMAL_NUM_ENVS`). Never write a
  test at width 1 or 2; behavior at those widths is not representative and
  reconstruction drift is width-sensitive.

## Git

You do not commit. Leave your work in the working tree.

No `git add`, `commit`, `push`, `stash`, `reset`, `checkout` of tracked files, or
branch manipulation. The Project Manager integrates its assigned package; the
Controller verifies it independently and owns every commit. Read-only Git
inspection is allowed only when the assignment needs it.

If a markdown file will not stage, that is the repository's bare `*.md` ignore
rule. The remedy is a per-directory negation in `.gitignore`, never `git add -f`.
Report it rather than working around it.

## Active-line development

This is an active research line, not a maintained product. Do not add backward
compatibility adapters, deprecated aliases, legacy branches, or inactive
fallbacks. When a path is superseded, delete it in the same change. Git history
is the archive.

## Lightweight execution

This project optimizes conclusion-bearing iteration, not process artifacts.

- Start from one bounded brief with outcome, authority, scope, exclusions and an
  observable completion condition. Ordinary work does not require a separate
  brainstorm, spec, plan or worktree. Any protected-semantics change, multiple
  writers or a real isolation boundary requires its frozen plan before
  implementation begins.
- Make the smallest real change that can answer the question. Do not scaffold a
  future architecture or preserve a superseded path.
- Match proof to the claim: reproduce and close a bug, run an investigation,
  exercise the changed path, or use the smallest existing focused check. Add a
  permanent test only for a new observable contract or a plausible regression.
- Parallelize only genuinely independent scopes. One writer owns a path at a
  time; dependent steps remain serial.
- Use an independent reviewer for protected semantics, cross-scope integration
  or a concrete high-risk boundary—not as ceremony for every edit.
- On failure, identify the first causal boundary. Do not replace diagnosis with
  retries, weakened checks, fallbacks or extra abstraction.

## Working discipline

This is a requirement, not advice. A previous agent produced zero file writes in
an hour of reasoning and had to be killed.

- After reading the brief, named files and immediate interfaces, make the first
  real edit within the next few tool calls. Do not substitute broad exploration
  for progress; iterate against the smallest focused check.
- On a design question your brief does not answer, take the smallest reasonable
  choice, record it, and keep moving. Report the ambiguity at the end.
- A working implementation with a noted simplification beats an unwritten
  perfect one.
- If you conclude the task cannot be done as specified, say so early and
  plainly rather than continuing to search.

## Honest reporting

- Paste real command output. Never state that tests pass without the actual
  output line.
- Report what you could not do, plainly, rather than working around it silently.
- Disclose every simplification, assumption and known limitation. A disclosed
  gap is useful; an undisclosed one corrupts evidence.
- Do not describe a guard as proving something it does not prove. A test that
  passes trivially is worse than no test, because it reads as covered.

## Protected semantics

These carry experiment validity and are reviewed before any commit: reward and
intrinsic-signal construction, probability support and factorization, gradients
and detach boundaries, recurrent state, masks, clocks and lifecycle ownership,
RNG stream ownership and consumption, replay, credit assignment and checkpoint
meaning.

If your task appears to touch any of them and your brief did not say so, stop
and flag it rather than proceeding.

## Pointers

- `docs/project/IMPLEMENTATION_PLAN.md` — the frozen executable contract.
- `docs/project/CURRENT_WORK.md` — live project state and binding engineering
  constraints.
- `docs/project/CURRENT_WORK.md` — active-line engineering constraints.
- `docs/project/IMPLEMENTATION_PLAN.md` — accepted executable design and
  evidence requirements.
