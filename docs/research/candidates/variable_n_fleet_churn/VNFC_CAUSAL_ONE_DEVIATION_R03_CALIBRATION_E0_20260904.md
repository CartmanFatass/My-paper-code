# VNFC R03 — accepted calibration, wall-budget blocker

**Technical conclusion:** the sole result-blind calibration completed correctly and returned
`BLOCKED_WALL_CAP`. Conservative projected machine time is **347,623.18427552027 seconds**,
above the unchanged2,700-second cap. No full census implementation, census invocation or scientific
headroom result exists. No CI-A/B/C branch applies. The owner subsequently requested pause after
the current round; this terminal collection is the final clean boundary, with no next run.

## Exact execution facts

- Source commit, pushed before preparation: `9c41484a068e266581b6456bddfd3f6448d3931c`.
- Node: configured `wsl_4070`, SSH `hmasd-wsl-node`, CPU single process/thread.
- Cwd: `/home/wu/hmasd-worktrees/vnfc-causal-r03-9c41484a` (detached exact source commit).
- Interpreter: `/home/wu/.venvs/hmasd/bin/python`.
- Accepted once: `vnfc_causal_r03_calibration_20260904_01`, supervisor PID1598757.
- Supervisor: **finished, exit0, tmux inactive**; log start09:46:39 and exit09:46:43 on
  2026-09-05 at UTC+08, duration4 seconds. Runner wall **4.096142977999989 seconds**.
- Peak RSS **122,736,640 bytes**, observed by runner `getrusage`.
- Actual-node admission at **2026-09-05T01:46:39.283002Z**: physical/effective available both
  **15,428,743,168 bytes**, passing the4GiB floor before runner/native construction.
- Tracker directly ACKed the same handle, then directly woke CM/DM on terminal. No duplicate
  process, migration, relaunch, extra calibration or per-run heartbeat was created.

Exact accepted payload after `agent-task run vnfc_causal_r03_calibration_20260904_01`:

```bash
cd /home/wu/hmasd-worktrees/vnfc-causal-r03-9c41484a && export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/vnfc-causal-r03-9c41484a/temp/directions/variable_n_fleet_churn/exp/causal_r03_20260904/memory.json && timeout 60s /home/wu/.venvs/hmasd/bin/python scripts/run_vnfc_causal_headroom.py --mode calibration --seed 2026090311 --launch-sha 9c41484a068e266581b6456bddfd3f6448d3931c --out /home/wu/hmasd-worktrees/vnfc-causal-r03-9c41484a/temp/directions/variable_n_fleet_churn/exp/causal_r03_20260904/calibration
```

## Measured units and complete projection

Every synthetic BCRH epoch enumerated1,961 rows. Scorer/checker, independent enumeration and all
candidate-record comparisons agreed at all six epochs. Whole-call seconds for epochs0..5 were
`0.449180563, 0.332469345, 0.255135022, 0.182135240, 0.106291078, 0.063000095`.
The maximum complete-call time per row is **0.00022905689087200407 seconds**.
This includes the accepted expectation scorer and independent checker rather than a scalar
score-only microbenchmark. No command or endpoint was returned by the native timing adapter.

Four tick cases each performed2,560 synthetic ticks with accounting. Maximum tick unit time was
**2.6664843750000003e-8 seconds**. Six eight-agent prehistory enumeration/apply calls took
**0.022342233 seconds**. Synthetic exact solver time was **2.5419622539993725 seconds**:
502,016 states created,288 retained cumulatively,501,728 eliminated,31,376 input action records,
finite completion true. These are artificial optimizer values, not native-world outcomes.

The prospectively fixed factor2 applies to measured unit costs and projected solver/record work.
All corrected counts and overhead terms were recomputed from the archived summary:

| projected term | seconds |
| --- | ---: |
| 9,418,560 native ticks | 0.5022888615 |
| 738,685,168 whole-BCRH candidate rows | 338,401.855830688 |
| synthetic exact solver extrapolated to903,722,928 extensions | 9,152.017350242992 |
| history/record allocation and serialization allowance | 8.093854271807 |
| 96 prehistory enumeration calls | 0.714951456 |
| fixed setup/publication allowance | 60 |
| **total** | **347,623.18427552027** |

Native terms alone exceed the cap, independently of the large exact-solver extrapolation. This
is an empirical conservative planning projection over the declared upper count, not a theorem
that every realized census must take this time. It does not establish a universal exact-solver
runtime bound or scientific polarity. No outcome-informed smaller support, policy class, terminal
shortcut, comparator replacement, native change, second calibration or budget enlargement occurred.

## Implementation, checks and review

The calibration source adds **483 non-test lines**, including a **58-line runner**, within the
2,000/600 limits. Independent review found no material issue and counted binding/runner plumbing
below30%. Scientific timing, exact optimization and required-count reporting are computation.
Engineering scope section4: **none**. All existing native/source dependencies were read-only.

Six tiny solver tests compare exact rational results with brute force, including coupled zones,
dominance/tie preservation, epoch selection and sub-float differences. Projection arithmetic and
toy solver→summary publication bring the focused suite to8 checks. Local post-edit:7 passed;
the smoke fixture failed before execution because its basetemp parent did not exist. Creating
that parent and rerunning only the unexecuted smoke passed in0.09s. No production code repair
was needed. Remote prelaunch exact-source build and all8 tests passed in0.03s, task
`vnfc_causal_r03_build_9c41484a_01`, exit0. Independent reviewer did not repeat tests/calibration.
Pytest's pre-existing `cache_dir` warning did not affect execution.

Remote HTTPS Git fetch failed with `SSL connection timeout`. SSH remained available, so a2.6MB
Git bundle containing only already-committed/pushed history from the remote's existing base was
transferred, fetched and used to create this exact detached checkout. No uncommitted source was
transferred. A read-only `cat-file` that triggered another lazy network fetch was stopped before
preparation continued; it was not a scientific process. A pre-existing partial-repository gc
warning was left unchanged. Native compilation and tests subsequently completed over exact bytes.

Exposure: **zero new RNG draws, models, optimizer updates, training transitions, checkpoints,
native panel worlds and native candidate endpoints**. The seed is recorded metadata only.
The calibration output explicitly declares `scientific_result=false` and
`full_census_implemented=false`.

## Evidence and next boundary

The adjacent `VNFC_CAUSAL_ONE_DEVIATION_R03_CALIBRATION_EVIDENCE_20260904.json` preserves the
complete collected timing summary, admission receipt, supervisor facts and exact task log.
Raw remote summary and admission remain at the accepted output paths above; supervisor log is
`/home/wu/.agent-tasks/vnfc_causal_r03_calibration_20260904_01/task.log`.
CM independently recomputed projection arithmetic, checked all six agreement flags, exposure
zeros, wall bound and admission. Collection did not invoke another native process.

The previous technical contract contains source-grounded causal-field inventory and exact solver
semantics. Full causal-key construction, native census and its publication coverage remain
unimplemented, as permitted by the DM's calibration-first disposition. DM owns independent intake
and any later direction decision. Current live VNFC handles: **zero**. Pause at this clean
technical boundary; no new work is selected by CM.
