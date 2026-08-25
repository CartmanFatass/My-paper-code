# HMASD native Codex workflow

This repository preserves the OMP domain and effect contracts while using
Codex top-level tasks for durable interaction and direct leaf subagents for
bounded parallel work. Roles describe decision responsibility; they are not
permission gates.

## Task plane

- **Root** is a low-cost operational orchestrator. It routes frozen decisions,
  reconciles task/runtime references, allocates worktrees and capacity, waits,
  recovers known effects, validates external archives, and performs final Git
  integration. It does not form material Portfolio, scientific, or engineering
  decisions and is not the only user entry point.
- **Portfolio** is a `gpt-5.6-sol` max top-level task. It owns cross-direction
  selection, priority, lifecycle, and whether to invest CM/resources. It writes
  Portfolio authorities and sends a Decision Packet to Root; it does not hold
  or dispatch EM/CM tasks.
- **EM/<direction-id>/g<generation>** is a top-level scientific task for one
  direction. It writes EM-owned science and research/external state.
- **CM/<direction-id>/g<generation>** is a top-level engineering task for one
  direction. It owns bounded technical judgment, engineering state, and
  assignment coordination.
- **Watcher Advisor** is an optional read-only observer for proxy capture,
  verification recursion, and workflow tail chasing. It uses
  `.codex/prompts/hmasd-anti-tail-chasing-watcher.md`, emits non-blocking
  advice, and has no execution or approval authority.

Users may interact directly with any of these tasks. Conversation history is
provenance, not durable authority. A material decision must be written by its
owner through the existing file/CAS contract before another task relies on it.
Task creation lineage does not confer authority.

Use the matching project skill to bootstrap a top-level task:
`hmasd-root-task`, `hmasd-portfolio-task`, `hmasd-em-task`, or `hmasd-cm-task`.
Portfolio, EM, and CM are never spawned from `.codex/agents`.

The Watcher Advisor may run alongside a top-level task when useful. Its output
is traceability and course-correction input, not a gate; reversible in-scope
recommendations may be applied immediately without acknowledgment or approval.

## One leaf layer

`.codex/agents/` contains the 18 role configurations registered by the project
config. The four long-lived Root/Portfolio/EM/CM identities are top-level tasks,
not custom agents from this directory. A top-level task may spawn only a role
allowed by its bootstrap skill; every spawned project agent is a leaf and must
not spawn or delegate another agent. Project config sets
`agents.max_depth = 1`; Codex must be restarted after changing project config
before its runtime enforcement is tested. Never ask a direct leaf to spawn
another child even before that fresh-host smoke passes. Delegation is optional
and is used only for useful parallelism or context separation.

## Hard boundaries

1. Resolve destructive targets canonically and keep them inside user scope.
2. Never expose secrets in prompts, state, logs, Dashboard APIs, or Git.
3. External provider sends are at-most-once per operation. Unknown commitment
   is observed and never resent.
4. Exactly one Experiment Operator owns one exact result-bearing command from
   launch through terminal observation.
5. Unsafe memory plans are reduced, batched, or sharded; they are not offered
   for approval.
6. A local result command estimated over 7200 seconds requires one performance
   reasonableness review attempt and explicit user approval bound to the frozen
   command and evidence.
7. Scientific, numerical, RNG, checkpoint, bit-identity, and external-effect
   semantics are never changed silently.
8. A role, task, subagent, review, test, Dashboard, lease, hash, or historical
   document never grants or denies ordinary authorized reversible work.
9. OMP and Codex must not simultaneously own the same direction, run, external
   operation, or Git integration after cutover.

## Durable authorities and writers

- `docs/research/portfolio/PORTFOLIO.md` and lifecycle reasons: Portfolio.
- `docs/research/portfolio/workflow/registry.json`: writer `Portfolio`, through
  `scripts/hmasd_state.py` with expected-revision CAS.
- `docs/research/candidates/<id>/DIRECTION.md`, research state, external index,
  and accepted scientific results: `EM-<id>` or an exact Artifact Writer
  assignment.
- Direction engineering state: `CM-<id>`.
- `temp/directions/<id>/exp/<run-id>/`: `Operator-<run-id>` through the run CLI.
- Runtime task/worktree references: Root, under ignored `.codex/runtime/`.
- External commitment: Agentify only. Exact archive validation and final Git
  integration: Root.

Tracked paths and durable references use repository-relative POSIX syntax,
without `..`, backslashes, symlink/reparse aliases, or absolute prefixes.
Concrete task IDs, host IDs, cursors, PIDs, and absolute worktree paths remain
ignored runtime data.

## Direction workspace and Git

Direction output lives only under:

```text
temp/directions/<direction-id>/exp/
temp/directions/<direction-id>/test/
```

Source lives in `experiments/candidates/`; tests live in
`tests/experiments/candidates/`; durable scientific artifacts live under the
matching `docs/research/candidates/` directory. Everything below
`temp/directions/` is disposable and never workflow authority.

Use native Windows Git and Python for this checkout. Sibling assignment
worktrees live under `C:/Projects/HMASD-worktrees` and use
`<direction>-<kind>-<assignment>` with branch
`omp/<direction>/<kind>/<assignment>`. Do not operate a Windows-created
worktree with WSL Git. Root alone integrates a verified, clean, in-scope
candidate into `main`; children do not commit or push unless their
exact assignment authorizes that effect.

Prefer `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` for project Python
commands. Durable Markdown, JSON, TOML, YAML, Python, and shell files use LF as
declared by `.gitattributes`; do not normalize bytes inside hash validation.

## Working style

- Preserve user changes and use the smallest useful decomposition.
- Freeze goals, non-goals, authority refs, owned paths, revisions, and effect
  refs in every material assignment or Decision Packet.
- Reviews and tests are proportional evidence, not authorization layers.
- One wake performs one reconciliation and at most one bounded reassessment;
  wait on task/process completion instead of model polling.
- Use the documented CLIs rather than private helper functions or duplicate
  state writers.
