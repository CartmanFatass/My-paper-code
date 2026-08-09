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
   `temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md`. Create the minimal
   binding at `temp/sessions/research_scheduler/bindings/<assignment_id>.json`
   with exactly
   `assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active`.
   The initial owner prompt forbids mutation until the Scheduler sends one
   binding-ready follow-up naming that exact binding.
   The roster retains the returned exact `threadId`+`hostId` pair as
   task-observation locators. The binding's `session_id` is the exact owner hook
   session identity carried by the owner PreToolUse/Stop hook payloads. Use a
   Desktop-exposed locator-to-hook-session mapping only when it is observable;
   never substitute `hostId` or `threadId` for `session_id`, and never infer
   the mapping from titles or history. Before sending the binding-ready
   follow-up, mechanically match the returned task locator to that exact hook
   session identity. If the mapping is unavailable or ambiguous, do not
   activate the binding or authorize mutation; record one unresolved
   observation in the roster and require exact Desktop/user resolution. Do not
   create a second owner, retry, or scan threads.
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

## Resource-conflict routing

There is no fixed capacity pool. Compare observed CPU, memory, GPU, process, I/O,
network, paid-service, mutable-path, mutable-object and output-root facts for the
exact assignments. Serialize only a named dependency, an observed resource
shortage, or an actual mutable resource conflict. Scientific evidence level
A/B/C is orthogonal to this resource vector and cannot be changed by routing.

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
