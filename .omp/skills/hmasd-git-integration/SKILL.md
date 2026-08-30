---
name: hmasd-git-integration
description: Integrate one exact assignment-owned candidate through the stable Clerk service.
---

# HMASD Git integration

## Purpose and ownership

`omp/*` is the only ordinary branch-effect namespace. `omp/workflow` remains the
normal shared transfer spine. EM or CM owns candidate semantics and the exact
changed-path set; Root admits one concise frozen integration job; the stable
logical `Clerk` performs the bounded Git mechanics under the supplied actor.
Neither Root admission nor Clerk execution changes scientific, technical,
Portfolio, lifecycle, actor, or writer authority.

One Git-visible writer owns the target during the job. Root assigns Clerk the
canonical repository, exact source base and candidate commit, target branch,
exact expected predecessor, actor, commit message, nonempty exact allowed-path
set, authorized effects, competing refusal outcomes, stop, and return route.
Clerk never expands those fields, resolves conflicts, rebases, broad-stages,
chooses a target, or schedules a successor.

## Public command

Use only the ordinary-flag local CLI:

```bash
python3 scripts/hmasd_clerk.py integrate-candidate \
  --job-id <job-id> \
  --repo <repository> \
  --source-base <commit> \
  --candidate <commit> \
  --target-branch <omp/branch> \
  --expected-predecessor <commit> \
  --actor <root|em:direction|cm:direction> \
  --commit-message <message> \
  --allowed-path <path> [--allowed-path <path> ...]
```

There is no JSON input, build step, persisted integration graph, alternate apply
surface, or compatibility route.

## Exact integration cycle

1. Discover the canonical Git top level from `--repo`. Require a canonical
   `omp/*` target with a configured same-name upstream, the target checked out,
   and the complete target worktree clean. Refuse symlink-traversing or
   noncanonical allowed paths.
2. Resolve all three supplied object IDs exactly. Require the candidate to be
   one non-merge commit whose sole parent is the source base. Compute its Git
   diff with renames disabled and require the exact changed-path set to equal
   the nonempty allowlist. Extra allowed paths and extra candidate paths both
   refuse.
3. In a temporary detached worktree rooted at the expected target predecessor,
   apply the candidate's standard binary Git diff to the index and worktree.
   Refuse any apply conflict or post-apply path drift. Commit once with the
   exact supplied actor and message; require the result to have the expected
   predecessor as its sole parent. The temporary worktree is removed when the
   job becomes terminal.
4. Fetch the configured remote target immediately before push and require its
   observed tip to equal the exact expected predecessor. A stale remote refuses
   before push. Push the one frozen integration commit exactly once using an
   exact `--force-with-lease=<remote-ref>:<expected-predecessor>` condition.
5. A known successful push is followed by one exact local fast-forward. A
   failed or interrupted push is never repeated. Perform one read-only fetch
   and comparison of the exact remote ref: report the integration commit as
   observed, the predecessor as not observed committed, a third SHA as
   divergent, or a failed observation as unknown. An explicit rejection may be
   `REFUSED`; every ambiguous effect remains `UNKNOWN` even when the observation
   narrows what occurred. The observation grants no retry authority.

## Refusal and result contract

Refuse a non-`omp/*` target, noncanonical repository or path, dirty target,
missing upstream, stale local or remote predecessor, changed candidate parent,
merge candidate, nonexact allowlist, conflict, applied-path drift, or changed
frozen intent. No refusal creates an alternate commit on the target or changes
the remote.

The command emits one compact stdout JSON object and writes no protocol
artifact. Its stable identity is `Clerk`; each Root assignment supplies a new
sequential `job_id`. `operation` is `integrate-candidate`; `outcome` is
`COMPLETED`, `REFUSED`, or `UNKNOWN`; `observations` contain only directly
observed repository, path, commit, push-attempt, and remote-comparison facts.
Root alone decides whether a later compatible assignment exists.

## State and worktree chores

State replacement uses the public `scripts/hmasd_state.py replace` command
directly with complete desired bytes, writer, and `--expected-revision`.
Worktree chores use ordinary documented Git/worktree or existing public
worktree commands under the assignment's exact paths. Do not split one coherent
chore into primitive jobs or manufacture another authorization artifact.

## Unchanged external boundary

This skill grants no network/provider submission authority. Agentify remains
the sole external submission ledger. Existing immutable provider target,
operation, idempotency key, request fingerprint, and unknown-never-resend
semantics are unchanged. If `send_attempted` is true, Clerk may only preserve or
observe that exact receipt; it never activates Send.
