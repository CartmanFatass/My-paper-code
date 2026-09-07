# Direction branch consolidation — 2026-09-07

OWNER_DIRECT: stop creating authoring branches for each task, object, stage or agent;
reuse one authoring branch/worktree per research direction. AGENTS section 6, Codex CM/DM,
loop-dispatch and Claude hub/Grok instructions were aligned. Independent review found and
resolved input synchronization and starting-status issues; final net diff was accepted.
Role TOML parsing and whitespace checks passed. No scientific requirement or run budget changed.

## Completed first cleanup

- Initial inventory: 237 local branches, 243 actual remote branches, 201 worktrees.
- Snapshot at cleanup: 238 local branches (one already-active research branch appeared),
  243 remote branches, 282 distinct tips.
- Recovery archive: tag `archive/branch-consolidation-20260907`, commit
  `720c41efa2cf736a8c000b2ea6fa500c1196e266`. Its `BRANCH_MANIFEST.json` records the exact
  local/remote branch-to-SHA mapping and worktree inventory. Every distinct tip is an archive
  parent; local reachability and the remote annotated-tag target were verified before cleanup.
- Retired 130 local branch names and 110 matching remote branch names. These had no outstanding
  patch in the main comparison, no dirty checkout, no identified active writer, no open PR and
  no protected Pro delivery. Tips and working-tree state were rechecked before local retirement;
  remote names were checked against the archived tips before deletion. No force push was used.
- 106 retired clean worktrees were detached at their existing HEAD. All 201 worktree directories,
  tracked contents, ignored runtime artifacts and evidence remain. No working-tree deletion,
  history rewrite, scientific intake or experiment invocation was performed by this cleanup.
- After cleanup: **108 local branches and 133 remote branches**.

The archive is recovery storage, not a research merge or acceptance decision. Restore a needed
branch from the exact SHA in the manifest with ordinary branch creation; inspect and integrate
its work through the normal owner before execution. Do not rerun historical experiments merely
because a branch is restored. Immutable commit links still resolve to preserved commits.

## Remaining work and handoff

The 108 retained local branches comprise 74 with positive `git cherry main` inventory, 18 with
uncommitted work, 8 protected/current/changed branches and 8 Pro delivery branches (exclusive
inventory categories, not scientific status). Some remote-only branches also remain. A positive
patch inventory is a reconciliation lead, not proof that a scientific result is unaccepted.
This first pass does **not** claim that the existing branch set has already reached one per direction.

Root received the rule commits and live-checkout protection list. CBSC's current DM/CM,
DISH's current DM and UCOPE's current DM checkouts were protected; newly active work and the
VNFC open PR remain protected. Accepted Pro requests keep their original delivery bindings.
At clean boundaries Root carries forward one authoring checkout per direction after current
accepted writers finish. Reconcile remaining unique patches, dirty work and completed Pro
archives before retiring their branch names, using the recovery manifest rather than deleting
work or replaying already-integrated commits. New assignments do not create replacement branches
while this backlog is being reconciled.
