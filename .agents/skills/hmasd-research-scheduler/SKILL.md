---
name: hmasd-research-scheduler
description: Use when a user-owned Desktop Scheduler must create, observe, route, or reclaim assignment-scoped Explorer or CPM owner tasks, especially when concurrent work needs exact resource-conflict isolation.
---

# HMASD Research Scheduler

## Boundary

The Scheduler owns task lifecycle and resource-conflict routing only. It has no
science, code, technical-acceptance, Git, runtime-execution, semantic-relay or
sibling-preload authority. It is a user-owned Desktop task, not a registered
child, daemon, queue or acceptance owner.

Every owner assignment is prose-first and self-contained. State why the task is
needed, its intended outcome, named canonical inputs, protected decisions,
exclusions, permitted local judgment, write paths, canonical result destination
and observable completion. A factual tail may carry assignment, owner mode and
locator facts; it never replaces that task model.

## Desktop normal path

1. Freeze one assignment ID and one owner mode: Explorer `direction|portfolio`
   or CPM `treatment|integration`. Create one same-level owner task with
   `create_thread`, `environment=local`, and no model or thinking override unless
   the user explicitly chose one. Call creation once.
2. Persist the returned exact `threadId` and `hostId` in
   `temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md`. Send exactly one
   read-only identity-probe follow-up to that exact `threadId`+`hostId`, asking
   the owner to execute exactly:
   `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_workspace_boundary_guard.py observe-owner-session --assignment-id <id> --thread-id <threadId> --host-id local`.
   The existing PreToolUse guard observes the real payload `session_id`,
   requires inherited `CODEX_THREAD_ID==threadId` and host `local`, and writes
   exactly four keys
   `assignment_id|thread_id|host_id|session_id` to
   `temp/sessions/research_scheduler/identity_observations/<assignment_id>.json`.
   This identity observation is read-only: it does not authorize mutation or
   activate a binding, and is not task context, a queue, registry, ledger,
   semantic result or acceptance. Mechanically match all four observed facts to
   the exact create result and assignment. Only after that match create the
   unchanged binding at
   `temp/sessions/research_scheduler/bindings/<assignment_id>.json` with exactly
   `assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active`,
   then send one separate binding-ready follow-up naming that exact binding.
   The initial owner prompt forbids mutation until that binding-ready follow-up.
   If the observation is missing or conflicting, the binding stays inactive
   (or remains absent) and one unresolved observation is recorded in the roster
   for exact Desktop/user resolution. Never scan, infer, substitute `hostId` or
   `threadId`, create a replacement, or retry blindly.
3. Observe active owners with one bounded `wait_threads` call over exact IDs, at
   most eight targets per call. Then use `read_thread` for each exact task that
   completed or needs attention. Do not scan tasks or infer liveness from time.
4. The owner writes and returns its conclusion-first canonical capsule. Read the
   direct exact task with `read_thread`, then mechanically confirm that the
   canonical result locator is durable and the assignment/owner identity match.
   Before requesting archive/close, change only the existing six-key binding's
   `active` value to `false` (`active=false`); this revokes owner mutation
   authority before archival. Request archive/close for the exact thread only
   after that deactivation. Inspect only the canonical locator and
   assignment/owner identity; semantic intake and acceptance stay with the
   declared owner.

   If archive succeeds, remove the task's entry from the human-readable active
   roster. Canonical assignment/result locators remain restart/archive evidence
   in their declared owner surfaces, not a Scheduler result ledger. If
   archive/close is ambiguous, keep the binding inactive and leave exactly one
   unresolved observation in the roster until direct exact-ID or user
   resolution. Never reactivate, blindly retry, or create a replacement owner.
   Reload and selection discover only `active=true` bindings; an exact stale
   identity remains fail-closed under the separate mechanical identity contract.

## Owner and child routing

A direction owner reads and writes one named direction and never preloads a
sibling. A portfolio owner receives an explicitly named direction set. A
treatment owner receives one exact ticket/worktree and one technical-acceptance
boundary. An integration owner receives only the exact already-accepted
commit/ticket set and shared-mainline integration scope.

Owner tasks use existing registered children through their existing profiles;
the Scheduler never becomes their parent, relays their answer, or creates a
child-of-child owner. Parent conversation history is background only. The
canonical owner assignment and result capsule are the restart boundary.

## Explorer portfolio routing

The Explorer owns portfolio target/state `12`, including scientific
selection, readiness marking, intake and successor readiness. For one portfolio
run, the Scheduler has an initial owner concurrency ceiling of `3`, counting
only active same-level `owner_mode=direction` tasks. The ceiling excludes the
portfolio owner, registered native children and the result-bearing runtime pool.
The Scheduler may launch fewer than three and mechanically scans the exact
Explorer-authored ready assignments in their preserved order. It may pass over
an item only for its named dependency or an observed write/resource conflict so
that a later disjoint item can proceed; it never fills slots, invents readiness,
reprioritizes, merges, retires or scientifically selects assignments. When an
owner completes, return the result to the portfolio Explorer for intake before
any successor is marked ready. Ready state and order remain assignment/capsule
semantics, never binding, roster, queue or Scheduler state.

## Resource-conflict routing

The per-run direction-owner ceiling is not a runtime capacity pool; there is no
fixed runtime capacity pool. Compare observed CPU, memory, GPU, process, I/O,
network, paid-service, mutable-path,
mutable-object and output-root facts for the exact assignments. Serialize only a
named dependency, an observed resource shortage, or an actual mutable resource
conflict. Scientific evidence level A/B/C is orthogonal to this resource vector
and cannot be changed by routing.

The local formal result-bearing runtime excludes only conflicting local experiment
runtime. The boundary is explicit: non-runtime work continues, including
research, intake, implementation, review and Pro. Non-conflicting ordinary work
remains parallel-first.

Cloud execution is ineligible unless the user explicitly names the provider,
budget, credential source and egress boundary. The Scheduler cannot infer or
increase that grant, change priority or choose a scientific treatment.

## One fallback

For an ambiguous create, send or archive action, record one unresolved
observation in the roster and use direct exact-ID resolution. Do not retry
blindly, create a second owner, scan threads or infer success. If the exact ID
cannot resolve the ambiguity, return it to the user/WDM without changing the
owner assignment.

There is no polling loop, daemon, lease, CAS, token/hash/epoch, revision,
idempotency protocol, thread scan, blind retry, CLI assumption or background
shell wakeup. The existing six-key binding is unchanged: no new lifecycle
fields, queue state or state machine is introduced. Reload uses the canonical
assignment/result locators and known exact IDs only.

## Quick reference

| Need | Owner |
|---|---|
| one scientific direction | Explorer `direction` |
| explicit cross-direction comparison | Explorer `portfolio` |
| one treatment ticket/runtime result | CPM `treatment` |
| accepted commits/shared-mainline repair | CPM `integration` |
| task lifecycle or observed conflict routing | Research Scheduler |

## Common mistakes

| Mistake | Correction |
|---|---|
| treat a binding as the prompt | use the prose-first assignment; binding is mutation-boundary identity |
| wait by progress polling | one bounded exact-ID wait/read cycle |
| use completion order as priority | preserve owner-frozen scientific priority |
| route missing local capacity to unspecified cloud | fail closed until the user grants provider, budget, credential and egress |
| archive on a terminal label alone | require the durable canonical locator and direct read |
