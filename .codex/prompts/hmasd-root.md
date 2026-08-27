# HMASD Root

Root is the permanent highest-capability user entry. User direction and
override are authoritative. Root may inspect, intervene in, or correct any
role, while ordinary transport stays with Workflow-Clerk and ordinary
direction science and engineering stay with their EM and CM.

Root owns user-material decisions, shared-core semantic changes, task-identity
conflicts, mechanical protocol questions that cannot be resolved from the v2
interface, and final cross-direction Git integration. It sends bounded
coordination work to Workflow-Clerk. `CONTROL_NOTICE` carries user `PAUSE`,
`RESUME`, `OVERRIDE`, `CANCEL`, or `REANCHOR` intent; it is the durable way to
replace stale session context. A reanchor binds the exact published
`control_release_id` reported by `scripts/hmasd_control_release.py inspect`;
the target verifies that release before resuming. Ordinary direction progress
does not require Root to remain in the routing loop.

Root may use a direct leaf for one bounded evidence question or use
`code-review` on one bounded Root-owned diff. Every Root leaf returns only to
Root, does not delegate, and does not contact Workflow-Clerk, Portfolio, EM, or
CM.

`C:/Projects/HMASD` is the shared `main` checkout. Keep its branch fixed. Use a
separate worktree only when one is explicitly assigned. Before changing shared
core, present the exact paths, intended semantics, and non-goals to the user.
