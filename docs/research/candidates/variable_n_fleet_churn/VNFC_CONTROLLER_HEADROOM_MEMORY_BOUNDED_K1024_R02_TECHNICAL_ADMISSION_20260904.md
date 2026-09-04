# VNFC memory-bounded K=1024 R02 — technical admission

- Object: `VNFC-CONTROLLER-HEADROOM-A-RECON-MEMORY-BOUNDED-K1024-R02`
- Evidence class: `A/RECON`
- Card: `VNFC_CONTROLLER_HEADROOM_A_RECON_MEMORY_BOUNDED_K1024_R02_SCIENCE_CARD_20260904.md`
- Implementation and pilot SHA: `cd535770f809012f1d42f0669d6a3bcdf87c1b73`
- Disposition time: `2026-09-04T12:09:09Z`
- Technical disposition: `PILOT_ADMITTED`

## What I checked

I compared CM's accepted implementation, independent static review, focused suite, and the sole
capacity-pilot artifact with the frozen card. The implementation commit changes only the five
owned code/test paths and is pushed. Non-test research code is 1,593 lines, the runner is 360/600
lines, and treating the entire runner as orchestration gives a conservative 22.6% share. No
section-4 machinery was added; `scope: none` is correct.

The independent reviewer found one material engineering issue: live owned-byte telemetry scanned
the retained frontier per candidate, which would have changed the declared cost order to
`O(expansions*K)`. CM replaced it with exact O(1) scalar capacity bookkeeping. The reviewer then
rechecked add, reject, replace, sort, frontier swap, and clear paths and found no remaining
material issue. This is engineering conformance, not scientific evidence.

The final focused suite command was:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider `
  --basetemp C:/Projects/HMASD-worktrees/codex-vnfc-controller-headroom-20260904/temp/directions/variable_n_fleet_churn/test/controller_headroom_mb1024_final `
  tests/experiments/candidates/variable_n_fleet_churn_headroom/test_controller_headroom.py
```

It passed `17 passed, 1 warning in 13.25s`. The first call reached no test because the ignored
scratch parent did not exist and reported `14 passed, 3 setup errors`; creating that parent and
reissuing the exact test payload was an exact infrastructure retry, not a result attempt.

## Sole result-blind pilot

Exact invocation, from the direction worktree:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  C:/Projects/HMASD-worktrees/codex-vnfc-controller-headroom-20260904/scripts/run_vnfc_controller_headroom.py `
  --output-root C:/Projects/HMASD-worktrees/codex-vnfc-controller-headroom-20260904/temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/capacity_pilot_cd535770_20260904_01 `
  --launch-sha cd535770f809012f1d42f0669d6a3bcdf87c1b73 `
  --seed 1 --beam-width 1024 --capacity-pilot
```

The fixed non-target fixture was `deterministic_general_episode(1)`. Exit was zero; stdout and
stderr were empty. The artifact is
`temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/capacity_pilot_cd535770_20260904_01/summary.json`,
SHA-256 `9a745cd2ebd56fccf96e2cfcbc6a0d41f763fcf1cb00cd4e8d1859eee874d0f5`.

Directly observed facts:

- current and next frontiers both reached exactly 1,024;
- 1,513 post-saturation replacements occurred;
- live-node high water was 2,049, exactly `2*K+1`;
- dynamic search-owned-byte high water was 1,122,852;
- fixed enumerator scratch was 31,376 bytes;
- conservative fixed-storage allowance was 31,585 bytes;
- OS-backed process peak RSS was strictly positive at 191,827,968 bytes;
- peak RSS plus fixed allowance was 191,859,553 bytes, strictly below 2 GiB;
- dynamic owned bytes plus fixed allowance was 1,154,437 bytes, also below 2 GiB; and
- internal wall was 1.9493604000017513 seconds.

The pilot JSON contains no target-world identity, endpoint, trajectory, service numerator,
denominator, `L`, `U`, or scientific branch. It therefore neither reads nor permits an inference
about a K=1024 target outcome. The refused expanded-vector pilot was not repeated.

## Card rule and bounded reading

The card requires both K-sized frontiers to fill, replacement after saturation, exact live bounds,
positive OS RSS, and a conservative high water below 2 GiB. All conditions pass. Finite selector
equivalence and history/non-regression semantics are covered by the accepted focused suite. The
frozen result projection remains 64,289,424 worst-case expansions, 1,285,788,480 native ticks,
723.80 seconds, and one 2,700-second arm.

This admits only the implementation and one result invocation. It establishes no controller
headroom, no mechanism value, no MAPR competence, and no result polarity. A fresh central 4-GiB
physical/effective admission and a focused prelaunch suite remain mandatory immediately before
the result invocation.

## Decisions this admission produces

Options:

- (a) accept `PILOT_ADMITTED` and proceed to the carded final focused pass, fresh central preflight,
  duplicate-process check, and sole detached result invocation;
- (b) refuse the result because RSS or bounded live storage is unavailable or at least 2 GiB;
- (c) repeat the old vector-materialization pilot or run another uncarded pilot; or
- (d) change the population, width, comparator, result rule, or resource envelope.

Recommendation: **(a)**. The direct admission quantities meet every frozen threshold. Option (b)
contradicts the positive observations, (c) is expressly forbidden, and (d) changes scientific
meaning or direction scope.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This reversible object-tier decision admits only the already authorized sole
A/RECON invocation. It does not open MAPR or make a Direction- or Portfolio-tier decision.

## Next boundary

Run the one focused prelaunch suite on the pushed bytes. If it passes, obtain a fresh repository
memory receipt with both physical and effective availability at least 4,294,967,296 bytes, verify
the result root is absent and no process targets it, and launch exactly one detached result process.
