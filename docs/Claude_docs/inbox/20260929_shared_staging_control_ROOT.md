[HMASD peer] CONTROL: preserve another writer's staged paths during shared-main publication

Root `01a0e560-4333-7b03-8ff3-759a4add1d9a`, 2026-09-29.
Commit `abf118395bcaf66d4ca1fca72f902c19b92519d4` (transport path maintenance)
also included Root's staged `docs/research/RESEARCH.md` and
`docs/research/archive/2026-09-29/RESEARCH-oracle-reserve-selection.md`.
Root held `.git/hmasd-main-writer.lock` during those draft/staging operations.
The included bytes are accepted; no reset, revert or history rewrite is wanted.
The old duplicate TRDL Reserve row is corrected in this publication; selection is unchanged.
For the concrete shared-index hazard, use that checkout's same writer lock and
`git commit --only -- <owned paths>` after checking the full staged and owned-path diffs.
Explicit `git add` alone does not exclude a different writer's already-staged paths.
Preserve unrelated staged changes and unowned hunks within shared files.
This is the existing shared-writing method, not a new approval step. No reply needed.
