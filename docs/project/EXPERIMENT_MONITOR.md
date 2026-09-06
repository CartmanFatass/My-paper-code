# Independent experiment monitor

OWNER_DIRECT 2026-09-06 replaces the native tracker with one reusable Codex task,
Luna/low, declared in `.codex/hmasd-monitor.toml`. Its own five-minute heartbeat
performs one bounded observation pass and ends the turn. Root's research heartbeat
is removed. This change does not resume OWNER_PAUSED research.

## Assignment and return

DM or CM sends accepted handles directly through `send_message_to_thread` to the
configured monitor task, using Luna/low. Native subagents can send to independent
tasks (owner-confirmed); an independent task cannot address Root's native children.
The return route is monitor -> configured research Root -> responsible native DM/CM.
Root uses `collaboration.send_message` for a running child or `followup_task` for an
idle child, resolving its current canonical identity. Do not guess a retired name.
Owner pause still controls any subsequent research or launch.

The assignment states the deliverable and links the existing card/run record. Include
only missing facts: execution node, accepted supervisor handle, launch SHA, cwd,
log/result/receipt paths, expected bound/reminder, responsible DM/CM canonical names.
Do not repeat the card or full scientific history. A private exec session number
alone does not transfer access; local detached work needs PID/start identity and its
existing exit witness. Tracking metadata is not an experiment launch condition.

The monitor records adoption and sends Root an ACK naming the assigning DM/CM;
Root forwards it. Before ACK the launcher owns observation; after ACK only the
monitor routinely polls. DM/CM/Operator retains launch, collection, verification and
science ownership. Repeated assignments update the same (node, accepted handle).

## One heartbeat pass

Read only the current assigned-handle rows and relevant owner instructions. Never
adopt historical handles by scanning old tables. Batch independent read-only checks.
Resolve the configured node via `.codex/hmasd-compute.toml`; on the current node use
`ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task status <accepted-name>`
and, only when useful, `logs <accepted-name> 40`. Quote the supplied name as data.
Never launch, retry, stop, attach, change experiments, or copy live output trees.
Use supervisor terminal evidence; SSH failure or PID absence alone is unknown.
Exit zero is a process fact, not scientific validity.

Notify Root once on completion, failure, lost observation, or a supplied reminder
or bound condition, with handle, direct fact, evidence and next responsible DM/CM.
Record notification state; reconcile uncertain delivery before retrying. Healthy
unchanged state is silent: no messages, commits, sleep loops or per-poll narratives.
CM collects results; DM judges validity and performs intake.

The monitor alone writes current rows in `docs/research/portfolio/EXPERIMENT_TRACKING.md`
in its configured worktree. Preserve historical evidence. Commit/push meaningful
adoption/terminal changes by explicit path; include commit and absolute record path
in Root notifications for integration. No new registry, event daemon or cost tracker.
When there are no handles needing observation, pause the same heartbeat. A direct
assignment wakes this task and reactivates that heartbeat; never create per-run jobs.
Keep terminal rows until handoff is acknowledged. A lost turn resumes from this table.

## Reading and handoff economy

Start with the assignment, current card/intake section and owned code. Read relevant
authority sections and dependencies as needed; do not preload every cited historical
artifact. A handoff gives the required deliverable, owned paths, acceptance and links
to accessible contracts; restate only changes, ambiguities and critical invariants.
Read broader evidence when a real scientific or engineering decision depends on it.
