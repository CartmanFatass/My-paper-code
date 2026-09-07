# Root experiment observation

Accepted experiment handles go directly to the Root configured in
`.codex/hmasd-monitor.toml`. `ROOT_OPERATIONS.md` defines the single shared heartbeat
for all current experiments and Pro work. Existing experiment/scientific constraints remain.

## Assignment and adoption

Root's native DM/CM sends the accepted handle through collaboration. Separate app tasks use
`send_message_to_thread` to the configured Root, without model/effort overrides. Root handles
its own assignment locally; it does not send an adoption message to itself.

Link the existing card/run record and supply only missing execution facts: node, accepted
supervisor handle, launch SHA, cwd, log/result/receipt paths, expected bound/reminder and the
responsible DM/CM identity. A private exec session number alone cannot transfer access;
local detached work needs PID/start identity and the existing exit witness. Tracking metadata
is not a new experiment launch condition. Preserve owner pause and existing launch bounds.

Root records adoption in `docs/research/portfolio/EXPERIMENT_TRACKING.md`, activates the
existing shared automation via `automation_update`, and reads back its ACTIVE state before
ACK. Preserve the full long-term prompt, thirty-minute schedule and Root target on updates.
An accepted message or one-off check does not establish recurring activation. Before ACK,
the launcher retains observation; after ACK Root owns routine polling. Repeated assignments
update the same (node, accepted handle). Root ACKs the actual native child or external sender.
CM retains launch/collection/technical acceptance and DM retains scientific intake.

## Bounded observation

On each shared wake, read all current assigned rows and relevant owner instructions. Check
every handle needing observation/terminal notification, not only the latest assignment.
Never adopt historical handles by scanning old tables. Batch independent read-only checks.
Use `.codex/hmasd-compute.toml`; on the configured node use
`ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task status <accepted-name>`
and, only when useful, `logs <accepted-name> 40`. Quote supplied names as data. Do not launch,
retry, stop, attach, change experiments or copy live output trees merely to monitor them.
Supervisor evidence controls terminal status; SSH failure/PID absence alone is unknown.
Exit zero is a process fact, not scientific validity.

On completion, failure, lost observation or a supplied bound/reminder, record the direct
fact and evidence and notify the responsible DM/CM and Portfolio. Root follows the command's named collection/intake route; Portfolio handles any unlisted next task. Use `send_message` for a running native
child and `followup_task` for an idle one. Reconcile uncertain delivery before retrying.
Healthy unchanged state is silent: no per-poll messages, commits or sleep loops.

Root writes meaningful adoption/terminal changes in the existing tracking table on main,
using explicit-path commits and immediate push. Preserve terminal rows and their collection
handoffs. No new registry, daemon, per-experiment task or monitoring worktree is required.
The shared heartbeat remains ACTIVE while ANY assigned experiment OR Pro request still
needs observation, reconciliation, archive or notification. A completed experiment does not
retire another item's observation. Pause only when that combined pending set is empty;
a new accepted assignment reactivates the same automation before ACK.
