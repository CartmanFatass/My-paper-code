# Root research planning and execution

Root owns Portfolio planning, scientific comparison, working-set readiness, task selection,
delegation, acceptance, integration and experiment observation. Its model and effort are
selected by the owner. DM owns direction-local scientific decisions; CM owns technical work
and acceptance. Independent Transport (Luna/high) owns Pro browser Send, observation and archival.
The decision ladder, scientific budgets and unattended delegation in AGENTS.md apply throughout.

## Current state and pause

Apply the owner's current pause/stop boundary before scheduling. Editing workflow files does
not resume research. Root maintains `docs/research/portfolio/PORTFOLIO.md`, accepted handles and
continuations in `EXPERIMENT_TRACKING.md`, and useful execution evidence in the existing root-log.
Use current card/intake sections and actual execution state; historical handoffs are evidence,
not a queue to replay. Root owns main's index and publishes explicit ready paths immediately.
Coordinate actual overlapping writers and preserve unrelated work.

Root's experiment endpoint is configured in `.codex/hmasd-monitor.toml`; independent Transport
is configured in `.codex/hmasd-transport.toml`. The current Root authors Portfolio questions and
receives their scientific results directly. Task UUIDs are routing facts, not scientific roles.

## Planning and execution loop

Use [hmasd-loop-dispatch](../../.agents/skills/hmasd-loop-dispatch/SKILL.md) on goal-turn entry,
returns, Transport receipts and before waits. Root keeps the whole working set current, handles
each direction's return promptly and selects ready replacements within existing authority.
Use [hmasd-portfolio-task](../../.agents/skills/hmasd-portfolio-task/SKILL.md) for cross-direction
comparison and proper-node decisions. Maintain the five-chain target under AGENTS §5 while
research is authorized. A batch packages ready work; it creates no completion barrier.

Delegate a complete bounded deliverable using AGENTS.md's five-item handoff. Resume the
original DM for direction-local decisions, CM work, repair and intake. Integrate accepted work
and continue its authorized route. Resolve readiness, scheduling and cross-direction conflicts
in Root. Escalate scientific decisions through the existing Pro/owner tier. An omitted
intermediate instruction does not stop an otherwise authorized direction-local route.

Before a long local operation, dispatch other ready independent work. Service changed facts
at recoverable boundaries and wait for the first event for at most 60 seconds only when no
authorized action is ready. A pending Pro decision holds only dependent work. Preserve exact
unknown acceptance and budget boundaries while advancing independent work.

## Independent Transport and native returns

The direction route is native DM/CM → Root → Transport → Root → original DM/CM.
The Portfolio route is Root → Transport → Root, with Root performing full scientific intake.
For new requests, source is the actual author UUID, parent is Root's app-task UUID, and
operator is Transport's UUID. The author supplies request ID, full HANDOFF commit/path,
fixed TASK URL and native return target where applicable. Root dispatches the unchanged
handoff with `send_message_to_thread`; app messages omit model/thinking overrides.

Transport preserves request identity, Send evidence, archives and its outbox. It returns one
completion or terminal-blocker receipt to the declared parent. Root reads the original evidence,
performs Portfolio intake locally or uses native `followup_task` for DM/CM intake. Use
[SIBLING_COMMUNICATION.md](SIBLING_COMMUNICATION.md) for addressing. A source UUID is not a
native tool address. Reconcile missing recipients and uncertain delivery; a receipt cannot
cause another Send or duplicate scientific intake.

App dispatch acceptance does not establish provider Send acceptance. On an event that leaves
a pending request unrepresented, consult Transport's existing state and resume that same task
for observation/recovery only. Keep unknown Send state intact. Transport interleaves due reads
and receipts with bounded waits while Root advances other work. Existing accepted request bytes
and receipt evidence remain immutable; reconcile external effects before any correction.

## Authoring branches

Use main plus one reusable branch/checkout for each direction with actual authoring work.
Create that branch on demand from accepted inputs; do not provision idle directions or give
each DM, CM, stage or child another branch. Record the chosen checkout in the existing command
handoff. Pro uses the corresponding direction branch too, with a fixed evidence SHA and its
one scoped response path. Serialize overlapping writers and reconcile remote Pro commits before
local pushes. Extra delivery branches need a concrete special isolation reason; only these are
temporary. Existing accepted requests retain their bindings through archival/intake or explicit
obsolete-request resolution. One completed Pro round does not retire a shared branch still in use.
At completion Root integrates accepted commits, preserves other unique commits and dirty files,
reconciles live writers/PRs/delivery dependencies, verifies recovery archives for unique commits
and noncommitted evidence, then unregisters and removes obsolete worktree directories and retires
obsolete local and remote names. A detached full checkout is not a recovery archive. Keep the
shared direction checkout while in use; an extra retained checkout names its actual live
dependency and cleanup owner/event in the existing return. Verify removed paths are absent both
on disk and from `git worktree list` before reporting reclamation complete.

### Reconcile routing when branches are retired

Root's reclamation return includes the retained direction branch/checkout and the affected
request IDs with their actual Send, delivery and archive states. Use current handoffs,
Transport's binding/request records and actual remote refs; a response merged to main does
not by itself close every request that names the branch. Resolve pending or uncertain delivery
before retiring its target. If an accepted target was already removed, preserve recovery refs
and let Root resolve a bounded restoration or delivery correction from its exact request/base.

Root updates current task locations and operational records, coordinating Transport-owned
request edits with its actual writer. Preserve old branches, bases and receipts in
the matching request history. Historical TASK/HANDOFF/archive files remain immutable evidence,
not sources for a new dispatch. A same-path file in an old checkout is not the latest handoff.
Do not mark cleanup complete while affected live routing remains unresolved; name any retained
dependency in the existing return. No new registry, scheduler or experiment gate is required.

### Execute the supplied launch command

Use the current CM's committed command/script and its exact node, source, cwd, output and
handle fields. Do not rebuild paths from a similar previous run or retype nested shell payloads.
Before submitting that command, compare its cwd with the actual staged checkout and its bound
source using the existing staging facts. A disagreement goes to the same CM for a mechanical
correction. When transporting shell text from Windows to Linux, preserve literal variables and
LF bytes; syntax-check the actual staged wrapper without executing the scientific payload.
Reuse that checked wrapper for the authorized submission. These are short transport checks,
not an extra experiment, new launcher framework or additional approval.

Supervisor acceptance, admission and scientific execution are separate facts. If a command
fails before admission, retain its exact failed identity and evidence; continue only the
already-authorized correction after acceptance is reconciled. Never infer a scientific retry,
changed source or extra allocation from a wrapper failure.

## Goal-driven observation

The owner's active goal drives execution and experiment observation. Use EXPERIMENT_MONITOR.md
for accepted-handle adoption; Transport observes its accepted Pro requests. No observation
automation, independent monitor task or replacement goal is created.

Each observation pass reads current assigned rows, batches independent supervisor checks,
services native/Transport returns and applies the loop skill. Update tracking on meaningful
adoption, terminal or continuation changes. Link detailed evidence instead of appending competing
current snapshots. A process exit is a technical fact; CM collection and DM intake establish
what the result supports. Empty observation state does not mean the research goal is complete.

Owner pause preserves accepted handles, pending request identities and explicit observation
handover. Continue only the closeout authorized by that pause. Do not adopt historical handles
or revive work from old planning entries.
