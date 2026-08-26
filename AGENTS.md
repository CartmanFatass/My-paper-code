# HMASD native Codex workflow

This repository preserves the OMP domain and effect contracts while using
Codex top-level tasks for durable interaction and direct leaf subagents for
bounded parallel work. Roles describe decision responsibility; they are not
permission gates. The v1 control plane is based on existing durable
Authority+CAS, exact Work Packets, typed Effect/ref domain observers, and
bounded `reconcile --once` with its native adapter. Return witnesses,
resource comparison, and the short dispatch lock are internal representations
or mechanisms, not new primitives.
Workflow-Clerk is only a program-generated exception path.

Stage A-C are implemented: the deterministic protocol
planner processes one explicit `work_id`, binds a typed agent result with
`assignment_id=work_id`, validates a canonical next-packet draft, binds a
`REQUEST_*` result uniquely through `next_action.input_refs=[draft.work_id]`,
and emits one program-constrained action from an explicit observed task
snapshot. Stage D closes the local protocol contracts. Live evidence now includes
the real no-model list/read/resume probe, read-only no-network Luna-low
`CONFORMANCE_OK`, `LOCAL_FAKE_TRANSPORT_GOLDEN` (including a real short
`hmasd_run`), and one real unique Experiment Operator leaf run to
`SUCCEEDED/exit0/group_quiescent/stdout marker`. Full real-native
EM→CM→Operator→Root unattended chaining remains unproven.

The [workflow design rationale](docs/project/WORKFLOW_DESIGN_PHILOSOPHY.md) is non-authoritative and adds no workflow primitive, authority, or gate.

## Agent skills

### Issue tracker

Planning specs and implementation tickets use local Markdown under `.scratch/`.
See `docs/agents/issue-tracker.md`.

### Domain docs

This is a single-context repository: use `CONTEXT.md` and root `docs/adr/`.
See `docs/agents/domain.md`.

## Task plane

- **Root** is the permanent highest-capability project orchestrator. It may use
  every genuine leaf capability and, when the user has authorized the decision,
  may form Portfolio, scientific, or engineering conclusions; it must record
  each conclusion under the referenced heading of the correct existing Markdown
  authority as `Decision owner: Root` (or the actual owner). Root is not the
  only user entry point.
- **Workflow-Clerk** is the unique Luna xhigh, event-driven, normally parked
  exception documentation and legacy-compatibility task. It receives only one
  exact program-generated typed-field/ref/schema/identity defect or
  legacy-unroutable input, documents that defect, and returns it to the
  program-named owner. Authority/path/Effect identity conflicts go to Root;
  material decisions go to the domain owner/user; Root override is direct.
  It does not handle the normal path, scan topology, infer routing from prose,
  publish/dispatch/create, wait/retry, own an Effect, keep private state, or act
  as a gate.
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

The former control-plane skills are retired pending redesign. Do not load,
resolve, or recreate them from historical references.

The Watcher Advisor may run alongside a top-level task when useful. Its output
is traceability and course-correction input, not a gate; reversible in-scope
recommendations may be applied immediately without acknowledgment or approval.

## One leaf layer

`.codex/agents/` contains the role configurations registered by the project
config. Root, Workflow-Clerk, Portfolio, EM, and CM identities are top-level
tasks, not custom agents from this directory. Root may spawn every genuine leaf role;
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
12. `CREATE_TASK` is a repeatable intent, not a creation receipt. Root alone
    single-flights a canonical manager identity: observe the Codex task list and
    task cache freshly before one create, observe errors or unknown outcomes
    before any retry, CAS only an observed identity, and re-observe a CAS
    conflict rather than create again.
13. Normal cross-session input is one exact validated Work Packet. Its
    `target_identity` must not be `Workflow-Clerk`; the dedicated Clerk
    top-level intake is not a normal packet. The receiving session writes only
    its existing authority/result/evidence and emits the
    machine-validated common agent result with `assignment_id=work_id`. It may
    request follow-on work only after the Work Packet `build` command emits a
    canonical draft; its `REQUEST_*` result then sets `next_action.input_refs`
    to exactly `[draft.work_id]`. Structured path+SHA256 state/artifact refs must
    be fresh. Opaque string payload refs receive schema validation only; their
    freshness belongs to a dedicated domain contract. All common file evidence
    uses path+sha file refs; legacy string file refs are schema-invalid. The protocol planner
    never guesses a path from a string or chooses a route from natural language.
14. Ordinary packets/results never wake Workflow-Clerk. Task identity conflict
    goes directly to Root; `UNKNOWN` Effect handling is programmatic
    observe-only; Root/user exact override needs no Clerk acknowledgment.
15. Pre-kernel authority retains its material goals, caps, paths, Effects, and
    decision owner. Legacy routing text is not executed or reinterpreted by a
    model; the program reports an exact legacy-unroutable defect. A Protocol
    Defect envelope includes `field_path`, `ref` (null or typed), `actual`,
    `expected`, `failure_scope`, `producing_command`, and
    `responsible_owner`; v1 protocol recovery always names `Root`, never a
    model-inferred target.
16. Every planner call supplies an explicit freshly observed task snapshot.
    Omission is a protocol defect; never fall back implicitly to a missing or
    stale task cache. Shared-core actions use the exact fenced
    `hmasd-shared-core-action-v1` record and byte-match proof; this proves the
    bound record, not that a conversation contained genuine consent. Effects
    use typed kind/resource_id/optional operation; legacy path-only Effects are
    read-only compatibility inputs and exact conflicts. Opaque file refs are
    structured; true operation IDs remain opaque and are never interpreted as
    paths. `file_ref` and `changed_paths` use Windows-safe canonical
    repo-relative paths, reject absolute/`..`/backslash/symlink-reparse aliases,
    normalize slashes, and casefold for deduplication. Root may use `--root-override-reason` for a known overlap or active
    unknown, recording the warning in native history; it cannot disguise an
    UNKNOWN send/create or bypass effect identity.

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
allowed Git effects. The record must come from a base-tracked existing durable
Markdown authority and use the top-level `hmasd-shared-core-action-v1` fence;
the exact authority allowlist is `AGENTS.md`,
`docs/project/WORKFLOW_PROTOCOL.md`, `docs/research/portfolio/PORTFOLIO.md`,
and the matching `docs/research/candidates/<id>/DIRECTION.md`; other Markdown,
including `WORKFLOW_DESIGN_PHILOSOPHY.md`, is not authority. Portfolio registry
JSON is only a writer-path exemption and never carries the fence. Root rechecks
the same bytes and hash. EM, Portfolio, and ordinary leaves
carrying non-writer-owned shared-core paths are rejected; Portfolio's two
existing authority writer paths are the only authority exception. The Action
digest is the SHA256 of the project's canonical JSON representation of those
bound fields. A candidate SHA is appended only as a result ref after
implementation; approval never requires an unknown candidate.
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
- A normal participant accepts one exact Work Packet and produces its existing
  authority/result/evidence plus the machine-validated common result using
  fresh structured path+SHA256 state/artifact refs. For `REQUEST_*`, first build the
  canonical draft and bind only its `work_id` in `next_action.input_refs`. One
  CM assignment covers ordinary review, same-scope repair,
  tests, verification/SANCheck, and terminal engineering return.
- Reviews and tests are proportional evidence, not authorization layers.
- One planner/reconcile call processes exactly one explicit `work_id` with one
  explicit freshly observed task snapshot and emits at most one bounded action.
  Never globally scan ready work or infer a missing snapshot from cache.
  Distinct explicit work IDs may proceed in parallel when their paths and
  Effects are disjoint.
- Normal dispatch is Root exact reconcile followed by a short native-dispatch
  critical section: fresh identity/active peers/resource comparison, then
  create-or-reuse and send. The receiver first performs exact return lookup,
  completes its slice, publishes the return witness, and only then sends a
  message. Lost messages are rebuilt from the witness. A terminal packet with
  no return resumes from native history for the same work_id at most three
  times; UNKNOWN send/create is observe-only. Full real-native unattended
  chaining remains unproven despite the completed probes and fake golden path.
- Use the documented CLIs rather than private helper functions or duplicate
  state writers.
