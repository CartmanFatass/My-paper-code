# VNFC causal one-deviation R03 — calibration intake and owner-directed pause

- Direction: `variable_n_fleet_churn`, route N2
- Recorded: `2026-09-05T01:52:08Z` (2026-09-04 in Los Angeles)
- Object: `VNFC-CONTROLLER-HEADROOM-A-RECON-CAUSAL-ONE-DEVIATION-R03`
- Accepted observation: **valid result-blind engineering calibration / `BLOCKED_WALL_CAP`**
- Native headroom result: **none**; no CI-A, CI-B or CI-C branch applies
- Current execution: **paused at the owner's request; zero live VNFC processes**

## What I checked

I read CM's E0 and complete collected summary, admission receipt, supervisor facts and task log
against the frozen R03 card, the prospective cost-accounting addendum and the calibration-only
technical contract. I inspected the calibration code at pushed source
`9c41484a068e266581b6456bddfd3f6448d3931c`, including the synthetic native input, complete BCRH
call timing, solver and serialization probes, and the output path. The accepted evidence commit
is `f498fc1444dd369189957620eed0c6eb373c705a`.

The same task `vnfc_causal_r03_calibration_20260904_01` ran once in the exact detached remote
worktree `/home/wu/hmasd-worktrees/vnfc-causal-r03-9c41484a` on `wsl_4070`. Its fresh actual-node
admission passed at `2026-09-05T01:46:39.283002Z`, with physical and effective available memory
both `15,428,743,168` bytes. Supervisor PID `1598757` is terminal, exit 0, with no tmux session;
the log records a four-second task duration. Runner wall is `4.096142977999989` seconds and
peak RSS is `122,736,640` bytes. Tracker directly woke this DM; I acknowledged the terminal event
and took intake responsibility. No new native call or remote observation was needed for my intake.

I independently recomputed every projection term from the archived raw timings. The total matches
`347,623.18427552027` seconds, all six BCRH agreement rows pass, and the actual calibration is below
its 60-second bound. The six epochs each use 1,961 synthetic candidates, or 11,766 measured BCRH
rows. Four native cases each use 2,560 ticks, or 10,240 measured synthetic ticks. The synthetic
solver has 31,376 action records and 502,016 created states: 288 retained plus 501,728 eliminated.
There are zero target-panel worlds, target candidate endpoints, new RNG draws, models, optimizer
updates, training transitions or checkpoints. Full census implementation remains absent.

The source is technically accepted only as a calibration adapter and pure exact optimizer. CM's
independent review reports no material finding, 483 non-test source lines, a 58-line runner and
orchestration below 30%; scope section 4 is none. Eight local focused checks passed, followed by
eight checks and the native build at exact remote bytes. The local toy's missing temporary-parent
setup was repaired before that smoke executed; this is not an extra calibration. I did not repeat
those tests. Full census and its full publication path remain unimplemented.

## Rule applied and observation that bounds it

The calibration's recorded rule is:

```text
BLOCKED_WALL_CAP if projected_seconds >= 2700
otherwise CALIBRATION_BELOW_CAP
```

The prospective factor 2, complete operation counts and fixed overhead were recorded before this
calibration. Recomputed terms are:

| term | projected seconds |
| --- | ---: |
| native transitions | 0.5022888615 |
| full BCRH scoring, enumeration and independent checking | 338,401.855830688 |
| exact solver over the finite upper extension count | 9,152.017350242992 |
| history/record allocation and serialization | 8.093854271807 |
| prehistory enumeration | 0.714951456 |
| fixed setup and publication allowance | 60 |
| **total** | **347,623.18427552027** |

The conservative total is approximately 96.56 hours, or 128.75 times the unchanged 2,700-second
cap. The BCRH projection alone exceeds the cap; this refusal does not depend on accepting the
large synthetic solver extrapolation. The maximum measured whole-BCRH call cost per candidate is
`0.00022905689087200407` seconds; its scoring, independent checking and enumeration are included.

Direct observation is a short synthetic timing calibration. The full-panel duration is an
empirical conservative projection using upper counts and maximum unit timing, not an observed
96-hour run or a universal impossibility theorem. No full census was attempted or quarantined.
This is neither CI-C nor evidence that the one-deviation class lacks headroom.

## Decisions this intake produces

### 1. Accept the complete calibration and its execution refusal — object tier

Options:

- (a) Accept this complete result-blind calibration as engineering evidence and retain
  `BLOCKED_WALL_CAP`, without a full-census launch.
- (b) Withhold technical acceptance pending additional evidence from the same execution.

Recommendation: **(a)**. The summary, timings, complete arithmetic, actual-node admission and
terminal log agree, with no missing claim-bearing observation. Additional execution is unnecessary.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**.

This accepts a bounded engineering measurement. It does not accept a native causal-headroom
result, open or close a scientific family, change the 2,700-second cap or select another object.

### 2. Finish this round and pause — owner-direct scheduling

The owner said **“这轮完毕后暂停即可”**. Root relayed the exact boundary: finish current accepted
calibration collection and engineering intake, then pause; no census, new calibration/retry,
successor, Pro request or further implementation expansion. Provenance: **`OWNER_DIRECT`**.

That instruction is executed. The card's possible direction-tier return is retained as a future
resume boundary; no packet or Pro dispatch is created in this round. The current intake, brief,
owner items and source/evidence acceptance state are committed and pushed. Lifecycle remains
ACTIVE with the existing second-recast lowest sequencing rule; this pause is not a lifecycle or
scientific disposition.

## Predictions, support and limits

The R03 prediction of CI-B is **not tested**. No owner prediction was taken. The synthetic timing
results cannot score a hypothesis about native causal headroom.

Strongest engineering support is agreement of six full BCRH measurements and independently
recomputed arithmetic, with the native term itself far above the cap. The limiting evidence is
that a maximum-cost synthetic state and upper action counts are a planning estimate, not the
actual target census workload; no claim that every alternative implementation must fail follows.

The scientific evidence is unchanged: the privileged predecessor has one individual `7/60`
opportunity witness in zone 2, while its panel lower bound remains `7/960` and zone 1 remains zero.
Localized opportunity, incompatible action maps and privileged opportunity that cannot be selected
causally all remain live. The full in-panel one-deviation measurement is still missing. No learner,
unrestricted causal-optimality, transfer, safety or Portfolio claim is added.

## Recoverable pause boundary

- DM: `/root/dm_amx_vnfc_continue`, worktree
  `C:/Projects/HMASD-worktrees/dm-vnfc-continue-20260904`, branch
  `codex/dm-vnfc-continue-20260904` with its own upstream.
- CM: `/root/dm_amx_vnfc_continue/cm_am_vnfc_causal_r03`, worktree
  `C:/Projects/HMASD-worktrees/cm-vnfc-causal-r03-20260904`, branch
  `codex/cm-vnfc-causal-r03-20260904`, clean at evidence commit `f498fc1444dd369189957620eed0c6eb373c705a`.
- Accepted source is `9c41484a068e266581b6456bddfd3f6448d3931c`; it is calibration-only, with no
  target-history construction, native census or full-census publication implementation.
- CM reports no live experiment, build or child command; all four children completed. Two
  implementation worktrees (`impl-vnfc-causal-native-20260904` and
  `impl-vnfc-causal-solver-20260904`) retain untracked duplicate candidate files already integrated
  into the accepted source. Those copies are preserved; they are not reported as clean or as
  unique unaccepted work.
- Raw calibration summary and `memory.json` remain under the accepted remote worktree's
  `temp/directions/variable_n_fleet_churn/exp/causal_r03_20260904/`. The complete collected bytes
  needed for intake are in the adjacent committed `CALIBRATION_EVIDENCE` JSON. The supervisor log
  remains `/home/wu/.agent-tasks/vnfc_causal_r03_calibration_20260904_01/task.log`.
- After an owner resume, the next scientific boundary is the card's exact `BLOCKED_WALL_CAP`
  return to Convergence. Do not silently rerun calibration, enlarge the cap or change the policy
  class. Any future Pro request must use the current Transport configuration and a verified
  post-cutover 6 Pro context; all old provider IDs remain retired. No such request exists now.

At the clean boundary the owner-reviews CLI returned `[]`; no additional VNFC owner instruction
was pending. DIRECTION is unchanged because this intake adds engineering evidence only.

## Evidence

- `VNFC_CAUSAL_ONE_DEVIATION_R03_CALIBRATION_E0_20260904.md`
- `VNFC_CAUSAL_ONE_DEVIATION_R03_CALIBRATION_EVIDENCE_20260904.json`
- `VNFC_CAUSAL_ONE_DEVIATION_R03_TECHNICAL_CONTRACT_20260904.md`
- `VNFC_CAUSAL_ONE_DEVIATION_R03_COST_ACCOUNTING_ADDENDUM_20260904.md`
- `VNFC_CAUSAL_ONE_DEVIATION_R03_CONTINUATION_INTAKE_20260904.md`
- `VNFC_CONTROLLER_HEADROOM_A_RECON_CAUSAL_ONE_DEVIATION_R03_SCIENCE_CARD_20260904.md`

## Append-ready audit rows for Root

Owner items:
`docs/research/portfolio/owner/inbox/2026-09-04/20260904-vnfc-018.json` (technical acceptance)
and `docs/research/portfolio/owner/inbox/2026-09-04/20260904-vnfc-019.json` (engineering brief).
Root appends these rows to the shared ledger; this worktree does not edit it.

Anchors: `vnfc-r03-calibration-intake-20260904`, `vnfc-r03-calibration-brief-20260904`,
`vnfc-r03-owner-pause-20260904`.

| 2026-09-05T01:54:29Z | variable_n_fleet_churn | object | technical | accept complete calibration and retain wall-cap refusal; withhold acceptance for additional same-run evidence | accept valid result-blind calibration / BLOCKED_WALL_CAP, with no headroom result or new launch | yes | `OWNER_DELEGATED` — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-vnfc-018.json` | `none` | |
| 2026-09-05T01:54:30Z | variable_n_fleet_churn | object | technical | agree with bounded engineering reading; dispute reading | publish calibration-only Chinese brief; native causal-headroom hypothesis remains untested | yes | `DM_INTAKE`; no additional experiment or scientific result | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-vnfc-019.json` | `none` | |
| 2026-09-05T01:54:31Z | variable_n_fleet_churn | object | technical | finish the current accepted calibration collection/intake and pause, as instructed | pause with zero live VNFC handles; no census, calibration retry, successor or Pro | yes | `OWNER_DIRECT` — “这轮完毕后暂停即可” | `docs/research/candidates/variable_n_fleet_churn/VNFC_CAUSAL_ONE_DEVIATION_R03_CALIBRATION_INTAKE_AND_PAUSE_20260904.md` | `none` | |
