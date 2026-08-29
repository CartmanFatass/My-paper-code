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

## Inputs
- Canonical repository root, the exact `omp/workflow` local and remote refs,
  exact base SHA, and actor `root | em:<direction> | cm:<direction>`.
- Provisioned assignment worktree, one candidate commit, an exact
  assignment-owned path allowlist, direction ID, and worktree kind
  `research | engineering`.
- The predecessor handoff result when applicable: an EM `integrated_sha` for a
  CM request, or a CM `integrated_sha` for EM result interpretation.
- Focused verification references and current target/remote observations.

## Bounded cycle

1. Resolve repository, worktree, target, receipt, and every allowlisted path
   canonically. Refuse symlinks, destructive ambiguity, dirty target/worktree
   state, any final target other than `omp/workflow`, and any changed path not
   in the exact allowlist.
2. Verify the candidate is one non-merge commit directly descended from the
   declared base and every changed path is assignment-owned. Require actor,
   direction, and kind to match exactly: `em:<direction>` may integrate a
   research worktree, `cm:<direction>` may integrate an engineering worktree,
   and `root` may integrate only its declared shared/recovery allowlist.
3. Enforce writer transfer for direction work. EM commits its exact allowlist
   and ends its overlapping Git-visible writer phase before integration. Its
   accepted `integrated_sha` is the exact CM base. CM begins only from that
   integrated SHA, commits its exact allowlist, and ends its writer phase before
   integration. The CM `integrated_sha` is then the exact base that EM must
   observe before beginning result interpretation and resuming its writer
   phase. A candidate based on any other SHA is stale.
4. Prepare and apply the clean candidate to `omp/workflow` once. Fetch the
   intended remote immediately before push and compare its observed tip with
   the candidate's required predecessor. Push only the verified integration to
   `omp/workflow`, and only while that remote tip is unchanged. A stale base,
   non-fast-forward, mixed ownership, dirty target, writer overlap, or conflict
   stops unchanged and returns exact evidence to Root; the manager never
   cherry-picks around the handoff, rebases, merges, or retries blindly.
5. Root uses the same primitive for shared-authority and recovery integration.
   Direction managers batch ordinary intermediate events into one
   cycle-completion checkpoint rather than requesting Root commits after every
   transition. Root does not become the routine writer for direction-owned
   paths.

One bounded cycle permits one candidate/apply/push attempt to `omp/workflow`.
No automatic retry, conflict loop, multi-candidate merge, or second writer
phase is permitted. After an unknown push outcome, fetch and compare the exact
remote ref; observation may establish the prior outcome but never authorizes a
blind resend.

## State writes

- Git alone is authoritative for candidate and integration commits, and the
  returned `integrated_sha` is the next layer's base authority.
- EM writes only its provisioned research worktree during the EM writer phase;
  CM writes only its provisioned engineering worktree during the CM writer
  phase. Root writes shared/recovery checkpoints.
- Stage only paths in the canonical exact allowlist. Do not stage unowned
  paths, generated runtime data, raw runs, secrets, unverified source, or
  unrelated user changes. Never use `git add -A`.
- Runtime worktree registry/receipt updates remain helper-owned bookkeeping;
  they do not grant writer, scientific, or integration authority.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-git-integration"` and payload:

```json
{
  "kind": "git",
  "direction_id": "<direction-id>",
  "base_sha": "<exact-base-sha>",
  "candidate_sha": "<candidate-sha>",
  "integrated_sha": "<integrated-commit-sha>",
  "changed_paths": [],
  "actor": "root | em:<direction> | cm:<direction>"
}
```

A refusal is `status: "BLOCKED"` or `"FAILED"` with the exact
path/base/conflict reference and no partial integration.

## Failure handling

Refuse dirty worktrees, stale bases, non-handoff bases, overlapping writer phases,
conflicts, multiple commits, mismatched actor/direction/kind, any changed path
outside the exact allowlist, canonical path failures, final-target violations,
focused-check failures, and non-fast-forward pushes. Leave `omp/workflow`
unchanged on pre-apply refusal. If apply succeeds but push cannot be proven,
preserve the candidate and fetch before any further decision; never retry
blindly. Return exit code `4` for stale base, `5` for ownership/path/writer
refusal, `6` for observed conflict, and `1` for another directly observed
failure.

## Deletion condition

Delete this Skill when an approved OMP integration primitive enforces canonical
paths, one-commit exact-allowlist ownership, actor/direction/kind matching,
layered EM-to-CM-to-EM bases, the sole final target `omp/workflow`, and
unchanged-on-refusal semantics without returning direction-owned routine
commits to Root.
