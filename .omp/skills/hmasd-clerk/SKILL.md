---
name: hmasd-clerk
description: Execute one Root-admitted immutable mechanical operation packet without acquiring semantic authority.
---

# HMASD Clerk

## Purpose

Execute exactly one content-addressed `ClerkOperationPacket` as a fresh,
nonblocking Root child. A Clerk is mechanical executor provenance only. The
packet's Root/EM/CM actor or document writer retains authority; the Clerk never
becomes the scientific, Portfolio, lifecycle, state, worktree, or Git actor.
Packet-file presence is inert. Root acceptance of the exact authorizer result
and packet SHA-256, followed by dispatch of the matching per-assignment Clerk,
is the only authorization event.

There is no watcher, daemon, shared parked Clerk, second scheduler, automatic
file authorization, prewalk, Advisor, child spawn, effort override, or model
fallback. Independent packets use independent assignments. One assignment has
one operation and one terminal result.

## Frozen inputs

Before dispatch, Root supplies:

- the immutable packet path and SHA-256;
- the accepted authorizer NodeKey (`logical_identity`, `generation`, and
  `assignment_id`) and accepted result SHA-256;
- the complete accepted producer-evidence set for every producer dependency,
  including exact NodeKey, result SHA-256, status, payload kind, and refs;
- the fresh `clerk_assignment_id`, equal to the common result
  `assignment_id`, with logical identity `Clerk-<clerk_assignment_id>`; and
- the exact operation-specific resource admission and physical writer lease.

The packet conforms to
`scripts/schemas/hmasd_clerk_operation.schema.json`. It fixes the executor and
authorizer tuples, exact dependencies, authority actor/writer, canonical
resources array, mutation class, operation target, hashes, one-attempt token,
effect budget, postconditions, stop condition, and Root return. Resource entries
are closed `{kind,key}` objects, unique and canonically sorted. Every mutating
worktree operation declares the shared runtime-worktrees state resource plus its
exact worktree or container; integration also declares the local Git target and
remote target resources. Root may bind an accepted result and resolve a declared
prior-operation receipt binding; it never rewrites packet bytes or chooses a
semantic field. A prior-operation binding is usable only when its operation ID,
receipt SHA-256, and named output field all match an accepted receipt.

## Pre-effect gate

Before acquiring a mutation lock or invoking an effect:

1. Verify the common assignment and logical identity against the packet.
2. Verify the packet SHA-256 over canonical JSON with `packet_sha256` omitted:
   sorted keys, two-space indentation, UTF-8, and one final newline.
3. Verify Root's dispatch binding against the packet authorizer and exact
   accepted result digest. The packet path alone grants nothing.
4. Compare every producer dependency against Root's complete accepted
   producer-evidence set: exact NodeKey, result SHA-256, required status,
   payload kind, and refs. File presence, job settlement, salience, or a later
   SHA never satisfies an edge.
5. Rely only on the harness-level pre-effect
   `retry.modelFallback: false` and exact Clerk profile. The executor never
   accepts child-authored model, effort, or fallback environment text as proof.
   The resolved profile is model `openai-codex/gpt-5.6-luna`, its thinking
   level is exactly `xhigh`, and model fallback is disabled.
6. Verify the packet-declared canonical paths, writer lease, complete resource
   array, expected revisions and predecessors, actor/writer, content and
   diff/tree digests, allowed and changed paths, and operation-specific
   preconditions.

Any mismatch refuses before effect. The Clerk never repairs, broadens,
regenerates, stages different bytes, resolves a conflict, rebases, merges,
changes a policy, or asks for a decision.

## One-shot execution

Invoke only the documented one-shot `scripts/hmasd_clerk.py execute` surface
with the exact packet and Root dispatch binding. Do not call raw Git or state
mutation commands to bypass it. The closed operation set is:

- `STATE_CAS`;
- `WORKTREE_PROVISION`, `WORKTREE_INSPECT`, or `WORKTREE_RELEASE`;
- `PATCH_APPLY`;
- `CANDIDATE_CREATE`;
- `GIT_RECORD` or `GIT_PREPARE`; and
- `GIT_INTEGRATE_PUSH`.

`STATE_CAS` cannot target `runtime_worktrees`,
`runtime_browser_assignments`, or `external_review_index`; those ledgers remain
owned by their discriminated primitives.

`WORKTREE_PROVISION` always binds one explicit current policy:
`EXACT_HANDOFF` or `ORTHOGONAL_DIRECTION`. An orthogonal provision also binds
the exact content-addressed `parallel_set_manifest_ref`; an exact provision
requires that ref to be null. `WORKTREE_RELEASE` always binds one explicit
`ignored_artifacts` disposition. `refuse` is a known zero-effect refusal,
`discard` succeeds only as `RELEASED`, and `retain` succeeds only as
`RETAINED_FOR_RECOVERY`.

The executor maps every operation to exactly one public primitive:

| Packet operation | Exact public primitive |
| --- | --- |
| `STATE_CAS` | `hmasd_state.replace` with exact kind/path/writer/revision/input digest |
| `WORKTREE_PROVISION` | `hmasd_worktree.py provision` |
| `WORKTREE_INSPECT` | `hmasd_worktree.py inspect` |
| `WORKTREE_RELEASE` | `hmasd_worktree.py release` with the frozen ignored-artifact disposition |
| `PATCH_APPLY` | `hmasd_worktree.py apply-patch` |
| `CANDIDATE_CREATE` | `hmasd_worktree.py create-candidate` |
| `GIT_RECORD` | `hmasd_worktree.py record-candidate` |
| `GIT_PREPARE` | `hmasd_worktree.py prepare-integration` |
| `GIT_INTEGRATE_PUSH` | `hmasd_worktree.py integrate-push` |

Precommit validation and result-blind reconciliation use only the documented
read-only primitives `hmasd_worktree.py inspect-repository`,
`hmasd_worktree.py validate-candidate`, and `hmasd_worktree.py observe`.
They consume no packet Effect budget. Clerk never imports or calls a private
`hmasd_worktree` helper.

Every worktree/Git target carries canonical repo/container/worktree, exact
registry revision and lifecycle, current worktree receipt SHA-256, frozen
policy, required handoff and dependency refs, and an explicit prior-operation
receipt binding (null only when no prior operation exists). Packet authority
direction, kind, actor, and authorizer must exactly match the registered
worktree before `STARTED`; Root is an exception only for an explicitly declared
shared or recovery assignment authority.

`PATCH_APPLY` uses a temporary index only. It produces an immutable prepared-tree
receipt and never changes manager worktree bytes, index, branch, or HEAD.
`CANDIDATE_CREATE` consumes that exact prior prepared-tree receipt, frozen commit
metadata, tree, and delta; creates one single-parent commit and dedicated
append-only candidate ref; and also leaves the checkout unchanged. `GIT_RECORD`
validates and records that exact object/ref. No patch or candidate path depends
on rollback.

`integrate-push` is remote-first for both current policies. Phases are
`PREPARED`, `PUSH_ATTEMPTED`, `REMOTE_PUSH_COMMITTED` or
`REMOTE_PUSH_REJECTED`/`REMOTE_PUSH_UNKNOWN`, one of
`RECONCILED_COMMITTED`, `RECONCILED_NOT_COMMITTED`, or
`RECONCILED_CONFLICTED`, followed only after remote proof by
`LOCAL_APPLY_ATTEMPTED` and `LOCAL_APPLY_COMMITTED` or
`LOCAL_APPLY_UNKNOWN`. Orthogonal integration compares the current target to
the packet's frozen expected predecessor before using or creating its prepared
integration object. One failed/unknown push permits one read-only reconciliation
observation and never a second push or object regeneration.

The claim is content-addressed by operation ID and packet SHA-256 and progresses
`PENDING -> STARTED -> SUCCEEDED | REFUSED | UNKNOWN`. The same ID and hash
returns the existing receipt without repeating an effect. The same ID with a
different hash refuses as an identity collision. An orphan `STARTED` claim
performs exactly one operation-specific read-only observation before terminal
`UNKNOWN`; helper unknowns preserve validated phase, local, remote, predecessor,
and observation-count facts. Never automatically retry, reapply, repush, or
convert uncertainty into success.

A manager owns its worktree until terminal handoff. After handoff the manager is
non-writing and this exact Clerk alone may hold the packet's mechanical lease.
Manager writing resumes only after terminal Clerk state and a new Root
assignment. Repository target mutation additionally obeys the repo-global
target lock. Locks exclude overlap; they never authorize, schedule, or select
operation content.

## Return contract

Return the common v2 envelope directly with `schema_version: 2`, role
`hmasd-clerk`, logical identity `Clerk-<clerk_assignment_id>`, the same
assignment ID, and the closed `clerk` payload. Copy the packet operation,
authorizer, authority actor/writer, canonical resources, and attempt; report
only directly observed outcome, effect state, structured observations, and
receipt refs. The raw immutable Clerk receipt path and SHA-256 are included in
the payload receipt refs. No model/fallback assertion appears in the executor
result. `decision_requests` and `next_actions` are always empty: the Clerk never
chooses a successor, retry, owner, conflict disposition, or reentry. Root alone
validates and routes the terminal fact.

`SUCCEEDED` means only that the packet's mechanical postconditions were directly
observed. `REFUSED` means no unauthorized effect was attempted. `UNKNOWN`
preserves uncertainty and is observe-only. None changes science, numerical/RNG
or checkpoint meaning, engineering acceptance, lifecycle, Portfolio action,
external commitment, or actor authority.
