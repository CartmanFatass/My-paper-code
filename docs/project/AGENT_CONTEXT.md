# HMASD Agent Context

Supporting reference for HMASD execution-environment facts and lightweight task
practice. Canonical role authority, routing, acceptance and validation
boundaries are defined only in the repository-root `AGENTS.md` and the
applicable `.agents/roles/*.md` contract. Do not use this file as a role
constitution. Task profiles and assignments embed the standing execution
constraints they need.

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
branch manipulation. Git ownership and integration routing follow the canonical
role contracts. Read-only Git inspection is allowed only when the assignment
needs it.

If a markdown file will not stage, that is the repository's bare `*.md` ignore
rule. The remedy is a per-directory negation in `.gitignore`, never `git add -f`.
Report it rather than working around it.

## Role-contract boundary

Role-specific semantic ownership, reviewer-package authorship, acceptance,
repair, transport and archival responsibilities live in root `AGENTS.md` and
the applicable `.agents/roles/*.md` contracts. Consult those sources directly
when constructing an assignment; do not copy their authority markers or turn
this environment reference into a parallel policy source.

## Development procedure

Use `$hmasd-agile-research-development` for active-line implementation,
debugging, proof-sized testing, file-safe parallelism, review and honest
completion evidence. It is the project-native procedure; generic Superpowers
Skills are reference-only and disabled for HMASD execution.

For an ordinary design gap inside an accepted brief, Project Manager takes the
smallest reasonable implementation choice and keeps moving. This rule does not apply to protected scientific choices; isolate those at their authority boundary.

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
- `docs/project/CURRENT_WORK.md` — live state and binding constraints.
- `.agents/skills/hmasd-agile-research-development/SKILL.md` — project-native
  implementation and verification procedure.
