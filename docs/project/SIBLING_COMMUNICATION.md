# Codex task communication

Use native `collaboration` tools for agents in the current Root's task tree.
Use `send_message_to_thread` for a separate app task, addressed by its exact task UUID.
The current Root, Portfolio and observation endpoints are configured in `.codex/`;
ROOT_OPERATIONS.md defines Portfolio planning, Root command execution/reporting and goal-driven observation. Portfolio sends concrete targets, actions and return routes; Root logs ordinary execution and sends actionable planning gaps to Portfolio instead of selecting a replacement task.

## Native agent messages

| Tool | Use |
| --- | --- |
| `collaboration.send_message` | Send evidence, an ACK or steering to an existing agent. It does not start a new turn for an idle agent. |
| `collaboration.followup_task` | Assign continued work to an existing non-Root agent; it wakes an idle recipient. |
| `collaboration.list_agents` | Resolve current canonical names and status when needed. |
| `collaboration.wait_agent` | Wait for agent messages or completion; this does not supervise an experiment process. |

Call native tools directly, outside `functions.exec`. Use the exact agent ID or
canonical task name returned by the current runtime. Across nested branches, prefer
the full canonical name. Do not substitute an app task UUID, display nickname, PID or
remote supervisor name. Use only tools exposed to the current task; report an actual
tool-access gap without inventing another route or creating a replacement task.

Reuse the existing recipient for related work. Send evidence to a running DM/CM with
`send_message`; use `followup_task` when idle work must resume. Tool acceptance and
the recipient's ACK are distinct facts. Reconcile uncertain delivery before retrying.

## App tasks and experiment observation

All cross-session `send_message_to_thread` calls, including Root's reports to Portfolio and
Portfolio's commands to Root, omit both `model` and `thinking`. These optional fields
change the recipient task's settings; they do not describe the sender or the cost of
the message. Never copy the sender's model/effort into a recipient's message. Omission
preserves the recipient's current settings. Portfolio effort is selected by the owner
in the app; do not set or restore a fixed effort through task messages.
Root handles its own dispatch and completion locally.
Portfolio receives scientific updates at its configured task. Pro handoff routing
follows Prompt Author's rendered fields and the Transport skill.

DM/CM sends accepted experiment handles directly to Root. Supply the node, accepted
supervisor identity, launch SHA, cwd, log/result/receipt paths and responsible DM/CM
through the existing run record. Follow EXPERIMENT_MONITOR.md for adoption and ACK.
Root observes the same handle; CM retains collection and technical acceptance, and
DM performs scientific intake. Transferring observation never launches another run.

Private terminal sessions do not become accessible merely by forwarding their IDs.
Use the recorded detached supervisor, process identity and existing exit witness.
Supervisor state establishes process termination; it does not establish scientific
validity. Observation runs within the owner's active goal, without a scheduled automation.

## Root-to-Portfolio notification filter

OWNER_DIRECT 2026-09-07: ordinary execution receipts belong in
`docs/research/portfolio/root-log/YYYY-MM-DD.md`, using the local date. Root owns this
append-only daily log. Each meaningful entry gives time with timezone, direction/command,
what changed, evidence/commit or accepted handle, and the already-assigned next action.
Link original evidence rather than copying it; maintain EXPERIMENT_TRACKING.md as the current
operational state. Batch log entries into ordinary commits at clean boundaries; no per-entry
commit, notification, new scheduler or periodic digest is required. Portfolio reads relevant
entries when planning or when asked; it need not ACK each entry or poll the log.

Dispatch ACKs, integration/push receipts, accepted launches, healthy observations, intermediate
returns and terminal events with an executable named collection/intake/follow-on route are
log-only. Continue that route and notify its responsible native DM/CM as needed. A completion
requires a Portfolio message only when the assigned route is exhausted and creates an
actionable vacancy or requires a new command. Routine evidence stays available in the log.

Send Portfolio a new command/replacement or working-set decision needed, an unresolved
scope/authority/scientific conflict, or a changed dependency/uncertain external effect that
requires Portfolio action. Root also reliably escalates any problem it cannot resolve within
the supplied route: execution failure, missing input/tool/access, or uncertain state. This is
a repair request even when no scientific or Portfolio-tier decision is needed. Include the
failed action, exact error/evidence, repairs already attempted, affected dependency and help
needed. Send promptly once outside the assigned repair path; do not silently log it, wait for
the next observation pass, repeatedly retry, or stop all independent work. Portfolio owns arranging the
bounded repair and returning its next step; Root resumes at that step and reports a changed
blocker if it persists. Reconcile ordinary technical issues within the assigned route first;
never conceal a planning gap until the whole batch finishes. Name the decision/action needed,
the affected directions and relevant log/evidence, with a compact working-set delta. Coalesce
related facts and do not repeat an unchanged request. Required shared-index handoffs and direct
replies to an explicit Portfolio/owner request remain allowed; keep them concise. All these
messages preserve the recipient's model settings as specified above.

## Shared main checkout: Git index handoff

Portfolio and Root share one main checkout and index. Before either stages, commits or
cherry-picks there, notify the other of the paths and wait for its acknowledgment that its
current index operation has finished and it will not start another until release. An already
running index operation finishes first. For simultaneous requests, Root proceeds first;
Portfolio acknowledges and defers its request until Root releases. Keep the handoff limited
to the short Git operation; native research, reads and other worktrees continue. Commit by
explicit path and push immediately, then release the index after that push attempt. A failed
push retains the commit and its retry obligation, not exclusive use of a clean index.
An in-progress cherry-pick/conflict must be resolved by its initiating session, or its explicitly
assigned resolution owner, before the other session stages any path. If unrelated authorized
edits may already be included, inspect the resulting commit and remaining diff, attribute
included paths and commit only outstanding changes. Preserve history; do not blindly repeat
the operation, reset, stash or silently rewrite it. No lockfile, lease or scheduler is introduced.
