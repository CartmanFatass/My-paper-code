# HMASD native Codex workflow

This repository preserves the OMP domain and effect contracts while using
Codex top-level tasks for durable interaction and direct leaf subagents for
bounded parallel work. Roles describe decision responsibility; they are not
permission gates. The v1 control plane has four primitives only: existing
durable authorities, runtime-only Work Packets, independently observed Effects,
and one bounded `reconcile --once` action.

## Task plane

- **Root** is the permanent highest-capability project orchestrator. It may use
  every genuine leaf capability and, when the user has authorized the decision,
  may form Portfolio, scientific, or engineering conclusions; it must record
  each conclusion under the referenced heading of the correct existing Markdown
  authority as `Decision owner: Root` (or the actual owner). Root is not the
  only user entry point.
- **Portfolio** is a `gpt-5.6-sol` max top-level task. It owns cross-direction
  selection, priority, lifecycle, and whether to invest CM/resources. It is
  created only when a direction needs it, then may park and recover independently.
- **EM/<direction-id>/g<generation>** is a top-level scientific task for one
  direction. It is created lazily for active science work, then may park and
  recover independently.
- **CM/<direction-id>/g<generation>** is a top-level engineering task for one
  direction. It is created lazily when Portfolio invests engineering, then may
  park and recover independently.
- **Watcher Advisor** is an optional read-only observer for proxy capture,
  verification recursion, and workflow tail chasing. It uses
  `.codex/prompts/hmasd-anti-tail-chasing-watcher.md`, emits non-blocking
  advice, and has no execution or approval authority.

Users may interact directly with any of these tasks. Conversation history is
provenance, not durable authority. A material decision must be written through
the existing file/CAS contract before another task relies on it; the decision
owner and runtime actor may differ. Existing JSON `writer` values remain domain
writers; Work Packet sender/session provenance identifies the runtime actor.
Root automatically creates or reuses a needed parked manager task, but reports
an identity conflict rather than making a duplicate. Task creation lineage does
not confer authority.

Use the matching project skill to bootstrap a top-level task:
`hmasd-root-task`, `hmasd-portfolio-task`, `hmasd-em-task`, or `hmasd-cm-task`.
Portfolio, EM, and CM are never spawned from `.codex/agents`.

The Watcher Advisor may run alongside a top-level task when useful. Its output
is traceability and course-correction input, not a gate; reversible in-scope
recommendations may be applied immediately without acknowledgment or approval.

## One leaf layer

`.codex/agents/` contains the role configurations registered by the project
config. The four long-lived Root/Portfolio/EM/CM identities are top-level tasks,
not custom agents from this directory. Root may spawn every genuine leaf role;
other top-level tasks use their matching bootstrap contract. Every spawned
project agent is a leaf and must not spawn or delegate another agent. Project config sets
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
10. Failure scope is explicit: project, direction, feature, or Effect. Never
    propagate a bare `BLOCKED` label across tasks or use it to close unrelated work.
11. Dashboard v1 is a read-only projection. Do not add a daemon, SQLite control
    plane, generic recovery engine, or a second durable workflow schema.

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

These writers identify the responsible domain, not a runtime permission gate.
Existing JSON `writer` fields remain domain-writer fields. An authorized Root
decision records `Decision owner: Root` (or the actual owner) under the
referenced heading in the appropriate existing Markdown authority; its runtime
actor is established by Work Packet sender/session provenance, not by a new
JSON field or parallel authority.

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

A source or test implementation folder name need not equal a direction ID.
Direction ownership comes only from the Work Packet's exact `owned_paths` and
authority refs; the path policy classifies a path but never maps it to a direction.

Use native Windows Git and Python for this checkout. Sibling assignment
worktrees live under `C:/Projects/HMASD-worktrees` and use
`<direction>-<kind>-<assignment>` with branch
`omp/<direction>/<kind>/<assignment>`. Do not operate a Windows-created
worktree with WSL Git. Direction-owned code may be modified, tested, committed,
and pushed autonomously within its assignment. Shared-core changes require one
user confirmation bound to the exact change, recorded by the user or Root under
the relevant Markdown authority heading. That heading records at least an
`Action digest`, `Base SHA`, sorted exact path set, objective/non-goals, and
allowed Git effects. The Action digest is the SHA256 of the project's canonical
JSON representation of those bound fields. A candidate SHA is appended only as
a result ref after implementation; approval never requires an unknown candidate.
Before execution or commit, Root compares the record with the current base,
paths, and requested effects. The path policy only classifies paths; unmatched
paths are shared-core and the policy is not an approval service. Root integrates
verified candidates mechanically and does not manually resolve candidate conflicts.

Prefer `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` for project Python
commands. Durable Markdown, JSON, TOML, YAML, Python, and shell files use LF as
declared by `.gitattributes`; do not normalize bytes inside hash validation.

## Working style

- Preserve user changes and use the smallest useful decomposition.
- Freeze goals, non-goals, authority refs, owned paths, revisions, and effect
  refs in every material Work Packet. Work Packets are ignored runtime transport,
  rebuildable from existing durable authorities, and never replace those authorities.
  Their locator delivery is at-least-once; receivers handle a repeated `work_id`
  idempotently and never generate a new packet for that redelivery.
- Reviews and tests are proportional evidence, not authorization layers.
- One `reconcile --once` advances at most one bounded action for a runnable
  direction; serialize the same scope/target/revision and allow distinct
  directions to proceed in parallel. Wait on task/process completion instead
  of model polling.
- Use the documented CLIs rather than private helper functions or duplicate
  state writers.
