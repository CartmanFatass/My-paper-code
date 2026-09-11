# FOLR public lifecycle TIMING-B02 closeout

Date: 2026-09-10
Execution node: `hmasd-wsl-node` (`LAPTOP-U9TDKC8A`)
Source commit: `6a8eacdad072c37d477aca95a9c871aba68cee78`
Recovery ref: `refs/archive/folr-public-lifecycle-timing-b02-20260910`

The exact remote execution worktree and three terminal supervisor directories were preserved,
verified, and reclaimed after final inactive-PID checks. The worktree archive excludes its `.git`
pointer; the supervisor archive contains all three complete named directories.

Remote recovery: `/home/wu/hmasd-recovery/folr-public-lifecycle-timing-b02-20260910`
Local retained copy: `C:/Projects/HMASD-worktrees/codex-vap-folr/temp/directions/vap_folr_core/exp/folr-public-lifecycle-timing-b02-20260910`

| Artifact | SHA-256 |
|---|---|
| `folr-public-lifecycle-timing-b02-worktree.tar.gz` | `d76ca3acc5c84d51fe5ae3e0c5706781950bf3489cd05b2e6a4f2e300f48468c` |
| `folr-public-lifecycle-timing-b02-supervisors.tar.gz` | `ad71fbc382349d060ab233764027b2bee7eac135daaa4593c3b00e2ec75a52da` |

Terminal facts supplied for the batch: RETAIN exit 0, PID 3086548, ended
2026-09-10T17:03:30Z; EVENT exit 0, PID 3088772, ended 2026-09-10T17:23:14Z;
RANDOM exit 0, PID 3090888, ended 2026-09-10T17:42:28Z. Final checks found all three
PIDs inactive. The remote worktree path is absent and no longer registered in Git; all three
exact supervisor paths are absent. Raw local three-arm outputs, memory, monitor receipts, and
the shared authoring checkout were not touched. The previously rejected `timing_b02_check01`
target was not touched.

No new scientific invocation, retry, test, preflight, or polling loop was performed.

## Exact reclamation record

The four removed absolute paths were:

* `/home/wu/hmasd-worktrees/folr-public-lifecycle-timing-b02-6a8eacda`
* `/home/wu/.agent-tasks/folr-public-lifecycle-timing-b02-retain-20260910`
* `/home/wu/.agent-tasks/folr-public-lifecycle-timing-b02-event-20260910`
* `/home/wu/.agent-tasks/folr-public-lifecycle-timing-b02-random-20260910`

Ordering and results: the remote archives were created first, then both archives were read with
`tar -tzf` successfully (`ARCHIVE_VERIFY_OK`). The recovery directory was copied locally and
both local SHA-256 values matched the remote recorded values before removal. A byte-for-byte
tar-to-original comparison was not performed; verification was archive listing plus whole-file
digest matching after transfer. Only after those checks, and a second inactive check for PIDs
3086548, 3088772, and 3090888, were the exact worktree and supervisor paths removed. The final
remote check confirmed all four paths absent and the worktree absent from `git worktree list`.

The source-ref mapping was verified as `refs/archive/folr-public-lifecycle-timing-b02-20260910`
pointing to `6a8eacdad072c37d477aca95a9c871aba68cee78`. Tool-reported wall times were 1.0 s
(initial inspection), 2.1 s (remote archive and digest), 8.3 s (copy and local digest check),
and 0.7 s (reclamation and final verification); these are command-tool measurements, not a
separate scientific timing measurement.
