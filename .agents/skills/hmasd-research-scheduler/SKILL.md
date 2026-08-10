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
2. Treat the exact `{threadId, hostId}` returned by `create_thread` as the
   native Desktop lifecycle/routing handle. Keep it in the optional
   human-readable `temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md`
   roster only as a restart locator. The roster, assignment files and canonical
   result files are artifacts/continuity, never proof of LLM identity. Do not
   create any extra identity machinery or file-based activation; do not inspect
   hooks or infer a handle from a file.
3. Send the owner a self-contained natural-language assignment. It must state
   why the task exists, intended outcome, canonical inputs, protected decisions,
   exclusions, permitted local judgment, bounded recovery, exact cooperative
   write ownership, canonical result destination and observable completion
   evidence. Serialize writers of the same exact file; disjoint exact files may
   overlap. Direction owners write/return only their named disjoint files; the
   portfolio Explorer alone writes shared portfolio continuity/capsule state; a
   treatment CPM owner writes only its ticket worktree and declared result
   destination; an integration CPM owner writes the shared mainline integration
   surface for the accepted set.
4. Observe active owners with one bounded `wait_threads` call over exact native
   handles, at most eight targets per call. Use `read_thread` for each exact
   handle that completed or needs attention. Do not scan tasks, infer liveness
   from time, maintain a queue/monitor/registry, or relay semantic results.
5. The owner writes and returns its conclusion-first canonical capsule. Read
   the direct exact handle with `read_thread`, then mechanically confirm only
   the named canonical result locator and assignment completion evidence.
   Archive/close that exact native handle after the direct read; on success,
   it may remove its roster locator. If archive/close is ambiguous, keep the
   owner live, resolve the exact handle or ask the user, and never blindly
   retry; never create a replacement. Reload and selection use known exact handles
   only; no task scan exists.

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

The Explorer derives the current portfolio cardinality from canonical
scientific facts and records the live count only in its continuity/capsule
surfaces. The workflow never compresses, pads, fills, merges or otherwise
changes that scientific set. For one portfolio run, the Scheduler has an
initial owner concurrency ceiling of `3`, counting only active same-level
`owner_mode=direction` tasks. The ceiling excludes the portfolio owner,
registered native children and the result-bearing runtime pool. The Scheduler
may launch fewer than three and mechanically scans the exact Explorer-authored
ready assignments in their preserved order. It may pass over an item only for
its named dependency or an observed write/resource conflict so that a later
disjoint item can proceed; it never fills slots, invents readiness,
reprioritizes, merges, retires or scientifically selects assignments. When an
owner completes, return the result to the portfolio Explorer for intake before
any successor is marked ready. Ready state and order remain
assignment/capsule semantics, never roster state or Scheduler semantic state.

### Effective-cycle counting

One completed Scheduler cycle is one Explorer-owned C-level key breakthrough.
Increment the lifecycle count only after a direct read shows that an
Independent Research Explorer-owned canonical result explicitly declares and
substantiates one C-level key breakthrough and exposes the exact canonical
result locator. The Scheduler mechanically confirms only that declaration and
locator; it must not infer C from technical facts, evaluate the science,
rewrite or merge the result, or relay its meaning. Portfolio freeze or portfolio
selection, CPM `CODE_ACCEPTED`, technical acceptance or integration, ordinary
Explorer intake, wait/archive, resource or admission events, and lifecycle
terminals are non-counting examples. Start from 0 confirmed C-level
breakthrough cycles until Explorer canonical artifacts explicitly say otherwise.
This is lifecycle counting only and does not reinterpret existing research
state.

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

For an ambiguous create, send or archive action, record one unresolved locator
in the optional roster and use the direct exact native handle. Do not retry
blindly, create a second owner, scan threads or infer success. If the exact
handle cannot resolve the ambiguity, return it to the user/WDM without changing
the owner assignment.

There is no polling loop, daemon, lease, CAS, token/hash/epoch, revision,
idempotency protocol, thread scan, blind retry, CLI assumption or background
shell wakeup. There is no queue, monitor, registry or lifecycle state machine.
Reload uses canonical assignment/result locators and known exact native handles
only.

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
| treat a file as the prompt or identity proof | use the prose-first assignment and the exact native handle |
| wait by progress polling | one bounded exact-ID wait/read cycle |
| use completion order as priority | preserve owner-frozen scientific priority |
| route missing local capacity to unspecified cloud | fail closed until the user grants provider, budget, credential and egress |
| archive on a terminal label alone | require the durable canonical locator and direct read |
