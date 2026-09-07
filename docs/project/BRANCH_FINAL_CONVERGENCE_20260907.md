# Branch convergence — 2026-09-07

OWNER_DIRECT: further reclaim finished temporary branches and audit dirty worktrees;
the owner clarified “按需建立即可 当前没有活跃的就先不创建”. Direction branches
are created only for actual work, then reused across DM/CM/implementation and stages.
No idle direction branches were provisioned. This changes branch management only.

## Executed result

This second cleanup retired **105 local and 128 remote branch names**, reducing the
fresh inventory from **109 to 4 local** and **135 to 7 remote**. Local heads are main
and the three current DISH, RCLE and VSP03 Pro delivery bindings. The remote also keeps
three older Pro bindings whose closure evidence still needs reconciliation (below).
The previous cleanup and audit remain recorded in BRANCH_CONSOLIDATION_20260907.md
and BRANCH_VERIFICATION_20260907.md; these are separate event counts.

All 157 distinct tips from the fresh local/remote/tracking inventory were preserved
as parents of archive commit `1e8e5bdf557d951db349cb6edb5f12a6d2217977`, pushed under
`archive/branch-final-convergence-20260907`. Its BRANCH_MANIFEST.json maps original
names to full SHAs. No historical unique patch was merged merely to retire its name.
Recovery can recreate a needed branch at the recorded SHA; the archive is not a
scientific acceptance record.

Ninety formerly branch-bound worktrees now have detached HEADs at their original
commits. Their indexes and working files were preserved; status was checked before
and after detachment. No worktree directory, ignored runtime root or evidence file
was deleted. Detached historical directories are retained evidence, not active
authoring checkouts or a reason to recreate their old branches.

All **18 dirty worktrees** were expanded and backed up locally at
`C:/Projects/HMASD-branch-backups/20260907T164718Z` (BACKUP_INDEX.json and 18 ZIPs).
Archives contain actual changed/untracked bytes, missing-path state, raw Git status,
index entries and binary staged/working diffs. ZIP integrity and member/source hashes
were verified when created, and archive hashes, status and saved contents were
rechecked before retirement. Both legacy control-plane worktrees are included.
Uncommitted contents remain local and unaccepted; they were not published into Git.

Obsolete draft [PR #2](https://github.com/CartmanFatass/My-paper-code/pull/2) was closed
without merging. Of its 61 submitted paths, 59 match current main; the VNFC direction
document and learning.py differ. The latter lacks main's optional evaluation uniform
supplier. All original commits and those differences remain recoverable in the archive.
Closing the PR accepts neither those differences nor a new scientific disposition.

## Remaining temporary delivery branches

These names retain unresolved delivery/intake work, not permanent engineering roles.
Root retires each after its stated dependency is resolved and recovery remains available.
An older replacement round alone does not establish the original round's completion.

| Remote branch suffix after `codex/pro-` | Remaining dependency |
| --- | --- |
| dish-post-b06-20260907 | Prepared, unsent question: complete authorized transport and intake. |
| rcle-post-a02-20260906 | Reconcile current request/send state and missing formed response; then intake. |
| vsp03-shared-service-convergence-20260906 | Reconcile accepted request's missing fixed Git response; a continuation receipt is not that response. |
| rcle-tbcfv-first-b-20260906 | Original response absent; reconcile obsolete-request closure separately from r02. |
| vnfc-b01-two-seed-convergence-20260905 | Response bytes are on main, but matching round intake was not located; reconcile closure. |
| vspc1-k4-three-seed-20260905 | Preserve misrouted Portfolio response and resolve original request closure separately from r02. |

Existing frozen TASK/HANDOFF files were not rebound or rewritten. No Send, experiment,
budget change or scientific intake was performed by branch cleanup.

## Maintained rule and verification

AGENTS §6 and ROOT_OPERATIONS now specify on-demand direction branches, reuse across
roles and stages, and Root's reclamation responsibility. Stale per-implementer isolation
text in CLAUDE/Claude CM and the older Astra calibration was corrected. Dispatch and
Pro authoring/transport skills state the temporary branch's completion/reclamation path.

Independent Luna review accepted five focused scenarios: idle direction, new stage,
completed Pro delivery, uncertain accepted delivery, and dirty/historical preservation.
Git diff whitespace checks passed; no runtime/scientific code changed. Fresh remote refs,
local refs, remaining branch-bound worktrees and closed PR state were read back.
The machine-readable receipt is BRANCH_FINAL_CONVERGENCE_20260907.json; detailed original
names and full preserved tips are in the immutable archive manifest.
