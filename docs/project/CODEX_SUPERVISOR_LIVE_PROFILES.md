# Codex Supervisor Live Profiles

The App Server supervisor starts with exactly one runtime profile. The profile
is a fixed, typed command allowlist for that process; it is not semantic
authority, a workflow state, or a capability to create work. A different
profile requires an explicit stop of the current host followed by a new host
start. It must never be changed in place.

The runtime profile is process-local and noncanonical. It does not alter
repository-owned owner artifacts, SQLite's noncanonical status, or the managed
identity rule `threadId -> binding_id -> actor_context_id`.

| Profile | Allowed commands |
| --- | --- |
| `OBSERVER` | `STATUS`, `STOP`, `INSPECT` |
| `MANAGED_MANUAL` | `STATUS`, `STOP`, `INSPECT`, `MANAGED_CREATE`, `MANAGED_ADOPT`, `MANAGED_VERIFY`, `MANAGED_TURN`, `MANAGED_SUSPEND`, `MANAGED_REVOKE` |
| `MAILBOX_MANUAL` | `STATUS`, `STOP`, `INSPECT`, `MANAGED_SUSPEND`, `MANAGED_REVOKE`, `MAILBOX_ENQUEUE`, `MAILBOX_LIST`, `MAILBOX_DELIVER_ONCE` |
| `SINGLE_WAKE` | `STATUS`, `STOP`, `INSPECT`, `MAILBOX_ENQUEUE`, `MAILBOX_LIST`, `ARM_SINGLE_WAKE` |

The command channel rejects any command outside the selected profile with a
typed profile error. The allowlist is deliberately closed: there is no
`SCHEDULER_SERVE` command.

## Protected constraints

- Behavioral Hooks remain disabled and native auto-compaction is unchanged.
- Only `OPERATIONAL_ROOT` and `PORTFOLIO` can be managed in this Stage 2
  runtime; EM and CM remain native Codex/subagent workflows.
- No profile automatically sends to a provider, approves an action, or invokes
  `turn/steer`.
- `MAILBOX_DELIVER_ONCE` is explicit and manual. `SINGLE_WAKE` can expose only
  one explicitly armed wake for one host run; it does not enable scheduler
  serve or a recurring scheduler.
- The supervisor records mechanical runtime evidence only and never writes
  canonical repository artifacts or interprets scientific, technical, or
  Portfolio meaning.
