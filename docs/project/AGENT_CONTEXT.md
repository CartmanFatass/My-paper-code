# HMASD Agent Context

Supporting reference for HMASD execution-environment facts. The root
`AGENTS.md` is a small role router; authority lives in the applicable role
charter. Read this file only when an assignment needs runtime facts. Do not use
it as a role constitution or preload it into unrelated children.

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
- Experiment-specific environment widths, budgets and minimum representative
  test batch sizes come only from the assignment-named design. This reference
  never supplies a default scientific value.

## Git

Project Manager directly stages, commits and pushes accepted code-owned paths.
Workflow Manager separately stages, commits and pushes accepted workflow,
review, active-state, report and ledger paths.
Native children never run Git and leave their exact owned paths in the shared
working tree. Git authority follows the applicable role charter; there is no
Controller handoff, per-file hash exchange, or callback receipt.

If a markdown file will not stage, that is the repository's bare `*.md` ignore
rule. The remedy is a per-directory negation in `.gitignore`, never `git add -f`.
Report it rather than working around it.

## Role-contract boundary

Role-specific semantic ownership, reviewer-package authorship, acceptance,
repair, transport and archival responsibilities live in the applicable
`.agents/roles/*.md` contract. The experiment operator is a fixed native child,
not a persistent task or Skill-driven monitor. Do not turn this environment
reference into a parallel policy source.

## Development procedure

Use `$hmasd-agile-research-development` for active-line implementation,
debugging, proof-sized testing, file-safe parallelism, review and honest
completion evidence. It is the project-native procedure; generic Superpowers
Skills are reference-only and disabled for HMASD execution.

For an ordinary code gap inside a Pro-frozen scientific brief, Project Manager
takes the smallest reasonable implementation choice and keeps moving. A
scientific ambiguity is reported to Workflow Manager, which alone routes the
focused Pro clarification; PM cannot choose the scientific value.

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
- `docs/project/CURRENT_WORK.md` — Workflow-Manager-only live state and binding constraints.
- `.agents/skills/hmasd-agile-research-development/SKILL.md` — project-native
  implementation and verification procedure.
