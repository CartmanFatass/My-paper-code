# HMASD Agent Context

Supporting reference for HMASD execution-environment facts. The root
`AGENTS.md` is a small role router; authority lives in the applicable role
charter. Read this file only when an assignment needs runtime facts. Do not use
it as a role constitution or preload it into unrelated children.

Context hierarchy pointers, loaded only when the current actor needs them:

- Stable map: `docs/project/PROJECT_MAP.md`
- Source registry: `docs/project/CONTEXT_SOURCE_REGISTRY.toml`
- Precedence: `docs/project/CONTEXT_PRECEDENCE.md`
- Promotion: `docs/project/CONTEXT_PROMOTION_POLICY.md`
- Retention: `docs/project/CONTEXT_RETENTION_POLICY.md`
- Decisions: `docs/project/DECISIONS_INDEX.md`
- Assignment/execution boundary when assigned: `docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md`
- Experiment execution and preflight when assigned: `docs/project/EXPERIMENT_EXECUTION_POLICY.md`

## Execution environment

- Run Python directly with
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`
  (`torch 2.7.0+cpu`) on the registered CPU backend.
- Use CPU with torch threads 1 where the assignment's registered CPU contract
  applies. Never mix backends or thread configurations, and never resume a
  checkpoint across backends.
- Do not use `conda run`; invoke the registered interpreter directly.
- For scripts outside the repository root, set `PYTHONPATH` to this workspace.
- The focused suite and formal-path exercise use the registered CPU/one-thread
  contract and fail closed on backend or thread mismatch. Never add a fallback
  or infer CPU/CUDA trajectory equivalence.
- Experiment-specific worker/environment widths come only from a current
  CPU/memory resource preflight and the CM selection for that host and route.
  There is no project-wide worker default or cap. This is distinct from
  portfolio direction count, neighbor-count ceilings, and evidence
  candidate-count ceilings; none of those values supplies a worker count.
- User P0 native-first rule: a new experiment must freeze its native C++ batch
  boundary, loader/ABI identity, supported widths, worker contract and
  reference benchmark before production Python loops are written. Python is
  oracle/fixture-only; an unspecified serial production path is
  `REPAIR_REQUIRED` and cannot receive a heavy lease.

## Git

Root stages, commits, and pushes only when the current user request authorizes
those Git effects. Native children never run Git and leave their exact owned
paths to Root. There is no separate Git lane, Controller handoff,
per-file SHA-256 handoff requirement, or callback receipt. Internal handoffs
use repository-relative paths, object/revision identity, owner, and Git commit
when needed.

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
  scientific ambiguity is routed by PM through the dedicated External Review
  Operator as one focused Pro clarification; PM cannot choose the value or
  import browser mechanics into its own context.

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
- `docs/project/CURRENT_WORK.md` — PM-only code attention and runtime constraints.
- `.agents/skills/hmasd-agile-research-development/SKILL.md` — project-native
  implementation and verification procedure.
