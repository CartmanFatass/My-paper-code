---
name: hmasd-git-integration
description: Verify and integrate one assignment-owned candidate on omp/workflow.
---

# HMASD Git Integration

## Purpose

Keep Git integration direction-scoped, layered over OMP, and fail-closed.
`omp/workflow` is the transfer spine and the final target for every accepted
handoff; assignment worktree branches are candidate sources, never substitute
targets. For one direction, only one EM or CM Git-visible writer phase may own
overlapping paths at a time. Root owns shared-authority/recovery integration; a
matching EM or CM owns its direction checkpoint without gaining
cross-direction authority.

Git integration has exactly two explicit current provision-time policies:

- `EXACT_HANDOFF` preserves direct-child, exact-predecessor,
  fast-forward-only behavior.
- `ORTHOGONAL_DIRECTION` is available only through one immutable
  content-addressed parallel-set manifest at a common epoch.

Missing or any other policy is invalid and grants no authority.

## Inputs and authority

- Canonical repository root and Git common directory, exact local
  `refs/heads/omp/workflow`, exact configured remote identity and remote ref,
  exact base SHA, and actor `root | em:<direction> | cm:<direction>`.
- Provisioned assignment worktree, one candidate commit, exact expected changed
  paths, allowed roots, direction, kind, assignment, focused evidence, and the
  accepted manager-to-Clerk physical mutation lease.
- `EXACT_HANDOFF` has the exact required predecessor. Same-direction EM→CM and
  CM→EM always use this policy: EM commits its exact allowlist and ends its
  overlapping Git-visible writer phase; its accepted `integrated_sha` is the
  exact CM base; CM begins only from that integrated SHA; the CM
  `integrated_sha` is then the exact base that EM must observe before result
  interpretation and resuming its writer phase.
- `ORTHOGONAL_DIRECTION` has no required handoff or dependency edge. Its
  manifest freezes `parallel_set_id`, common epoch, authorized
  direction/kind/assignment tuples, exact paths, roots, dependency footprint,
  evidence digests, prospective checks, and remote identity.

Packet presence and locks are inert. Root acceptance and dispatch authorize one
exact operation; the manager remains the actor and the Clerk is only the
executor. Every mutator verifies the packet's expected registry revision,
lifecycle, canonical worktree/container, receipt digest, and content-addressed
handoff before an effect.

## Public mechanical surfaces

Use only the documented `scripts/hmasd_worktree.py` one-shot commands. Every
mutator takes the exact manager-to-Clerk lease plus
`--expected-registry-revision`, `--expected-lifecycle`,
`--expected-worktree-path`, `--expected-container-path`, and the current
`--expected-receipt-sha256` (omitted only for an actually absent provision).
The runtime registry must already be schema v2. Every operation rejects any
other registry version; there is no compatibility read, default, alias, or
migration surface.

- `apply-patch` binds the clean baseline commit/tree, retained patch path and
  SHA-256, exact paths/roots, canonical delta SHA-256, and result tree. It
  rejects nested repositories, submodules, binary patches, symlinks, and
  mode/type changes. It applies only to a temporary index and publishes an
  immutable prepared-tree receipt. Manager worktree bytes, index, branch, and
  HEAD are never changed on success, refusal, failure, or crash.
- `create-candidate` requires lifecycle `PATCHED`, the exact prior
  prepared-tree receipt, canonical tree/delta/paths, and content-addressed
  closed `hmasd.candidate-metadata/v1` JSON. It uses `commit-tree` with the
  frozen author/committer/message, creates a dedicated immutable candidate ref,
  and never changes the checked-out assignment branch, worktree, index, or
  HEAD. The result is one deterministic single-parent candidate, lifecycle
  `CANDIDATE_READY`, and receipt-bound object/ref evidence.
- `record-candidate` validates and records that exact candidate object and
  dedicated ref. `prepare-integration` remains a separate exact registry
  operation. Their Clerk packets bind a future candidate only through the
  producing operation ID, Clerk receipt SHA-256, and named output.
- `integrate-push` is the remote-first public integration surface for both
  current policies. It consumes the prepared operation ID/receipt SHA/output,
  frozen candidate/base/predecessors, local and remote refs,
  paths/dependencies/delta, evidence, push authorization, actor, lease, and
  current registry/receipt facts. Orthogonal integration verifies that the
  current target equals the packet's frozen expected predecessor before using
  a prepared integration object. Exact integration fetches the exact remote
  predecessor, creates no alternate object, pushes the frozen candidate once
  with exact force-with-lease, proves the remote, then fast-forwards the clean
  local target.

There is no local-only `apply` command or other compatibility surface.

## Locks

The target mutex is repository-global: canonical Git common directory plus
`refs/heads/omp/workflow`. It is independent of worktree container locks.
Worktree-content/container locks and short state CAS locks remain separate.
Every operation obeys target lock → worktree lock → state CAS; no caller may
acquire them in reverse. The target lock covers revalidation, prospective tree
construction/checks, integration-object proof, fetch, the one push attempt,
unknown reconciliation, and local fast-forward. Unrelated safe worktree/state
operations do not acquire it.

## EXACT_HANDOFF bounded cycle

1. Resolve repository, worktree, target, receipt, remote, and every allowlisted
   path canonically. Refuse symlinks, destructive ambiguity, dirty
   target/worktree state, any final target other than `omp/workflow`, and any
   changed path not in the exact allowlist.
2. Verify one non-merge candidate directly descended from the declared base.
   Require actor, direction, and kind to match exactly: `em:<direction>` may
   integrate a research worktree, `cm:<direction>` may integrate an engineering
   worktree, and `root` may integrate only its declared shared/recovery
   allowlist. Every changed path is assignment-owned.
3. Require local target and fetched remote target to equal the exact base.
   The candidate uses an exact assignment-owned path allowlist; actor,
   direction, and kind must match exactly. Overlapping writer phases refuse.
   Prepare/apply once and fast-forward only. Fetch the intended remote
   immediately before push, compare its observed tip with the candidate's
   required predecessor, and push only the verified integration to
   `omp/workflow` while that predecessor is unchanged.
4. Refusal and unknown-outcome semantics are evidence-preserving and
   one-attempt. Leave `omp/workflow` unchanged on pre-effect refusal; stale or
   non-handoff bases refuse. One bounded cycle permits one candidate/push
   attempt to `omp/workflow`, with no automatic retry. After an unknown outcome,
   compare the exact remote ref once; the observation never creates retry
   authority.

## ORTHOGONAL_DIRECTION bounded cycle

1. Require the candidate `C` to be one clean non-merge child of common epoch
   `B`. Its computed canonical delta must have exactly the manifest's changed
   paths, lie within its allowed roots, and preserve the frozen evidence
   digests. Path-only semantic inference is forbidden.
2. Under the target lock observe `T`. Require `B` to be an ancestor of `T` and
   `merge-base(T,C)==B`. Every first-parent commit in `B..T` must have one
   verified terminal receipt from another authorized sibling in the identical
   manifest. Same-direction, shared, recovery, unreceipted, other-parallel-set,
   non-descendant, and merge lineage refuse unchanged.
3. Compute versioned raw tree deltas with renames disabled and strict UTF-8
   repository-relative paths. Each length-prefixed record binds path, old mode
   and OID, and new mode and OID; it therefore covers binary blobs, executable
   mode changes, additions, deletions, and rename-as-delete-plus-add. Require no
   exact or prefix collision between target changes and candidate paths/roots,
   or between target changes and the declared authority/input/interface
   dependency footprint.
4. Construct prospective merge tree `M` without moving a ref. Conflicts refuse;
   run every frozen contract-relevant focused check against exactly `M` and
   revalidate evidence digests. Base-era check presence is not evidence.
5. Before prepared-object use, require observed `T` to equal the packet's
   frozen expected target predecessor. Create one immutable commit object `I`
   with tree `M` and sole parent `T` without moving the target. Persist `I`,
   tree, parent, provenance, candidate delta, and effect fingerprint. Prove
   `canonical_delta(T,I)==canonical_delta(B,C)` and record candidate/applied
   equality before any ref or push effect.
6. Fetch the exact remote and require it equals `T`. Persist `PUSH_ATTEMPTED`,
   then push frozen `I` exactly once using the exact refspec and
   `--force-with-lease=<remote-ref>:T`. Never regenerate or re-push `I`.
7. After remote proof, fast-forward the clean local target from `T` to `I`.
   Verify target tree/status, then CAS the registry and persist the terminal
   receipt. Four authorized same-base candidates may therefore integrate as one
   proven single-parent first-parent chain without stale replay.

## Phase-specific idempotency and unknown outcomes

The immutable receipt distinguishes `PREPARED`,
`INTEGRATION_OBJECT_CREATED`, `PUSH_ATTEMPTED`,
`REMOTE_PUSH_COMMITTED`, `REMOTE_PUSH_REJECTED`,
`REMOTE_PUSH_UNKNOWN`, `RECONCILED_COMMITTED`,
`RECONCILED_NOT_COMMITTED`, `RECONCILED_CONFLICTED`,
`LOCAL_APPLY_ATTEMPTED`, `LOCAL_APPLY_COMMITTED`, and
`LOCAL_APPLY_UNKNOWN`. Object creation, push, local apply, and reconciliation
have separate one-attempt counters/tokens.

An orphaned `PUSH_ATTEMPTED` or unknown push performs exactly one fetch and
compare of the exact remote ref. Remote `I` proves the original attempt landed;
remote `T` proves it was not observed but does not authorize resend; any third
SHA or failed fetch remains conflicted/unknown. A known rejection does not move
the local target. Unknown local apply observes the exact local ref once.
Duplicate terminal operation identity returns the existing receipt. No phase
regenerates, re-pushes, rebases, cherry-picks, merges around a conflict, or
silently changes evidence, digest, actor, policy, or dependency facts.
There is one fetch reconciliation and never a second push.

## State writes and results

- Git alone is authoritative for candidate/integration objects and returned
  `integrated_sha`; receipts are provenance and idempotency evidence, not
  scientific, writer, or integration authority.
- Stage only paths in the canonical exact allowlist. Do not stage unowned
  paths, generated runtime data, raw runs, secrets, unverified source, or
  unrelated user changes. Never use `git add -A`.
- A refusal records the exact base/path/lineage/conflict/dependency/evidence/
  digest/phase reason without an alternate effect. Exit code `4` is stale
  facts, `5` ownership/path/writer refusal, `6` conflict/unsafe state, and `1`
  another observed or unknown failure.
- This Skill is policy consumed by Root and Clerk, not an active result
  producer. `hmasd_clerk` emits the sole common-v2 mechanical result with raw
  receipt reference; no obsolete common Git payload is returned.
## Deletion condition

Delete this Skill when an approved OMP primitive enforces both frozen policies,
canonical structural deltas, dependency-fresh prospective checks, repository
target serialization, one-attempt remote CAS/unknown reconciliation, exact
actor/writer leases, and the sole final target `omp/workflow` without returning
direction-owned routine commits to Root.
