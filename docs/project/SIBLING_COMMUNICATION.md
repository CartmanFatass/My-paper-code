# Codex task communication

Use native `collaboration` tools for agents in the current Root's task tree.
Use `send_message_to_thread` for a separate app task, addressed by its exact task UUID.
The current Root, Portfolio and observation endpoints are configured in `.codex/`;
ROOT_OPERATIONS.md defines Portfolio planning, Root command execution/reporting and the shared wake. Portfolio sends concrete targets, actions and return routes; Root forwards completed or blocked returns to Portfolio instead of selecting a replacement task.

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

Separate app tasks send to the configured Root without model/effort overrides for
routine evidence or adoption. Root handles its own dispatch and completion locally.
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
validity. Observation follows the configured shared heartbeat, not an extra agent task.

## Shared main checkout: Git index handoff

Portfolio and Root share one main checkout and index. Before either stages, commits or
cherry-picks there, notify the other of the paths and wait for its acknowledgment that its
current index operation has finished and it will not start another until release. Keep this
handoff limited to the short Git operation; native research, read-only work and other worktrees
continue. Commit by explicit path and push immediately, then release the index to the peer.
An in-progress cherry-pick/conflict must finish before the other session stages any path.
If unrelated authorized edits were already included, inspect and attribute them accurately;
preserve history rather than reset, stash or silently rewrite it. No lockfile, lease or scheduler
is introduced by this communication rule.
