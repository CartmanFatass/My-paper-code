# FSD E4 census — CM technical record

Engineering contract accepted against frozen card `FSD_E4_CENSUS_SCIENCE_CARD_20260905.md`
and assignment at `005643177`; source baseline `411adffc3`. CM owns the thin runner,
focused tests, exact invocation and technical acceptance. DM owns result interpretation.

Observable: one complete finite reference report per law at N6/K2/Z4/regions2/H400,
Delta .4, nominal mean20, shape1 and k={1,2,5,20,40}; all 96 open-loop rows, moments,
hazards, lognormal finite support/mass residual, native gaps and consistency discrepancies.
Calibration uses the six frozen full-H DP timings and cold triggered law computation.
The report must distinguish timing projection from a bound and numerical resolution from
certified error. Learner episodes/transitions/updates and model selection are zero.

Protected: unchanged enumerate_references and float64 DP, membership, age0 initial dwell,
399 transitions/400 scored steps, event/renewal semantics, tie order, RNG, checkpoints,
and core files. Non-goals: learners, new science, changed comparison, successor selection.
Owned source: scripts/run_flexible_skill_duration_e4_census.py and focused tests under
 tests/experiments/candidates/flexible_skill_duration/e4_census/.
Adds no scope section4 machinery. Whole logical source change uses the prospective
small-reuse exception (<=100 added non-test lines); final A/D/O reported after review.

Execution: portable CPU computation on configured wsl_4070, hmasd-wsl-node,
/home/wu/.venvs/hmasd/bin/python. Existing detached agent-task, timeout and resource
preflight reused externally; no runtime/configuration edits. Fresh actual-node >=4 GiB
physical/effective admission immediately precedes each invocation with &&. Calibration
120 seconds per law; final census300 seconds per law. All three measured projections
must be recorded by DM before any full-law launch. Source committed/pushed first.

Stop: completed census, actual refusal, incomplete calibration/projection above cap,
failed/nonfinite/inconsistent output or frozen timeout. Preserve incomplete artifacts;
no automatic retry, altered parameters, or successor. Missing optional RSS alone is not
scientific invalidity. Literal commands, receipts, review and observed results follow.


## Source acceptance and verification invocation

Source/test commit `bc3eaeecf5f97e630a886028db0053ba2d08d56f` pushed. Independent reviewer
reported no material findings; A91/D0/O76, O/(A+D)=83.52%; tests174 lines, card/docs227
separate. Existing core unchanged. Runtime facts still unverified at this boundary.
Actual remote detached checkout is /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf.
Configured bash -lc environment has no OMP/MKL/OPENBLAS/NUMEXPR variables observed;
no thread/config changes made. Verification cap300s, one focused suite, stop on terminal.
Task fsd_e4_test_bc3eaeecf_01, existing logs /home/wu/.agent-tasks/fsd_e4_test_bc3eaeecf_01/task.log.
Frozen exact invocation before dispatch:

```sh
/usr/local/bin/agent-task run fsd_e4_test_bc3eaeecf_01 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/test/receipt.json && /usr/bin/timeout 300s /usr/bin/time -v -o /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/test/process_time.txt /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/flexible_skill_duration/test/e4-census-bc3eaeecf tests/experiments/candidates/flexible_skill_duration/e4_census'"'"''
```


Test01 failed before all13 test bodies: pytest basetemp parent absent. Implementer reproduced
exact Path.mkdir(mode=448) on same remote path/interpreter, exit1 FileNotFoundError.
Technical directory setup failure, not scientific output; unchanged source bounded retry02
creates test parent before fresh admission. Frozen retry command:
```sh
/usr/local/bin/agent-task run fsd_e4_test_bc3eaeecf_02 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf && mkdir -p temp/directions/flexible_skill_duration/test && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/test02/receipt.json && /usr/bin/timeout 300s /usr/bin/time -v -o /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/test02/process_time.txt /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/flexible_skill_duration/test/e4-census-bc3eaeecf tests/experiments/candidates/flexible_skill_duration/e4_census'"'"''
```


Test02 finished exit0,13 passed in0.27s; one existing pytest unknown-option warning.
No code repair. Calibration proceeds sequentially at same source/shell/default threads.
All three exact commands frozen before first dispatch (120s/law, no scientific census yet):
```sh
/usr/local/bin/agent-task run fsd_e4_cal_deterministic_bc3eaeecf_01 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_deterministic/receipt.json && /usr/bin/timeout 120s /usr/bin/time -v -o /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_deterministic/process_time.txt /home/wu/.venvs/hmasd/bin/python scripts/run_flexible_skill_duration_e4_census.py --law deterministic --mode calibration --horizon 400 --seed 0 --launch-sha bc3eaeecf5f97e630a886028db0053ba2d08d56f --node wsl_4070 --output /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_deterministic/summary.json'"'"''
/usr/local/bin/agent-task run fsd_e4_cal_geometric_bc3eaeecf_01 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_geometric/receipt.json && /usr/bin/timeout 120s /usr/bin/time -v -o /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_geometric/process_time.txt /home/wu/.venvs/hmasd/bin/python scripts/run_flexible_skill_duration_e4_census.py --law geometric --mode calibration --horizon 400 --seed 0 --launch-sha bc3eaeecf5f97e630a886028db0053ba2d08d56f --node wsl_4070 --output /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_geometric/summary.json'"'"''
/usr/local/bin/agent-task run fsd_e4_cal_lognormal_bc3eaeecf_01 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_lognormal/receipt.json && /usr/bin/timeout 120s /usr/bin/time -v -o /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_lognormal/process_time.txt /home/wu/.venvs/hmasd/bin/python scripts/run_flexible_skill_duration_e4_census.py --law lognormal --mode calibration --horizon 400 --seed 0 --launch-sha bc3eaeecf5f97e630a886028db0053ba2d08d56f --node wsl_4070 --output /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_lognormal/summary.json'"'"''
```


## Calibration observed and transferred

All three calibration tasks finished exit0 at sourcebc3eaeecf. Six DP samples per law,
no learner exposure. Local artifacts under
`temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_<law>/`:
summary.json,receipt.json,process_time.txt. Same relative remote root under detached cwd.

| Law | Cold seconds | Heuristic projection seconds | Process wall s | Peak RSS KiB | Physical/effective available bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| deterministic | .00004823099880013615 | 1.5478515890717972 | .15 | 35076 | 15419650048 |
| geometric | .000025706991436891258 | .805505117605207 | .18 | 35192 | 15417974784 |
| lognormal | .0903399069939042 | 2.92621167763718 | .41 | 46996 | 15421640704 |

Each actual-node receipt passed both4GiB floors. Projection excludes interpreter startup/output;
external process wall includes them and is rounded by existing time tool. RSS in runner JSON is
marked unmeasured because runner does not measure it; external process_time supplies the observed
RSS above without changing JSON evidence. No runtime limit was reached. All projections below300s;
DM receives these facts to record before full census. No full census yet at this boundary.

## Full census literal commands frozen before dispatch

Same source and thread defaults as calibration; sequential law execution. Await recorded DM
projection document before actual first dispatch. Exactly36DPs/law and96 candidates expected,
300s cap, fresh admission per invocation; no automatic successor.
```sh
/usr/local/bin/agent-task run fsd_e4_census_deterministic_bc3eaeecf_01 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_deterministic/receipt.json && /usr/bin/timeout 300s /usr/bin/time -v -o /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_deterministic/process_time.txt /home/wu/.venvs/hmasd/bin/python scripts/run_flexible_skill_duration_e4_census.py --law deterministic --mode census --horizon 400 --seed 0 --launch-sha bc3eaeecf5f97e630a886028db0053ba2d08d56f --node wsl_4070 --output /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_deterministic/summary.json'"'"''
/usr/local/bin/agent-task run fsd_e4_census_geometric_bc3eaeecf_01 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_geometric/receipt.json && /usr/bin/timeout 300s /usr/bin/time -v -o /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_geometric/process_time.txt /home/wu/.venvs/hmasd/bin/python scripts/run_flexible_skill_duration_e4_census.py --law geometric --mode census --horizon 400 --seed 0 --launch-sha bc3eaeecf5f97e630a886028db0053ba2d08d56f --node wsl_4070 --output /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_geometric/summary.json'"'"''
/usr/local/bin/agent-task run fsd_e4_census_lognormal_bc3eaeecf_01 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_lognormal/receipt.json && /usr/bin/timeout 300s /usr/bin/time -v -o /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_lognormal/process_time.txt /home/wu/.venvs/hmasd/bin/python scripts/run_flexible_skill_duration_e4_census.py --law lognormal --mode census --horizon 400 --seed 0 --launch-sha bc3eaeecf5f97e630a886028db0053ba2d08d56f --node wsl_4070 --output /home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_lognormal/summary.json'"'"''
```


## Full census terminal technical acceptance

Before dispatch, DM committed/pushed all three cost projections in4ce1e416e; actual runner
source remainedbc3eaeecf. Every formal task finished exit0, summary COMPLETE, exactly96
unique zone-map/period pairs (288 total), five fixed-k values and zero learner episodes,
transitions, optimizer updates and checkpoint selection. Full config and law tables retained.
All numerical discrepancy fields are0, including deterministic switching-minus-k20; JSON
publication completed with finite quantities. Existing tie selection is preserved.

| Law | J switch = J greedy | Best k | m dur | Process wall s | Peak RSS KiB | Physical/effective bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | .381 | 20 | 0 | .41 | 35668 | 15423946752 |
| geometric | .38005 | 5 | .0970995000000001 | .47 | 35244 | 15423528960 |
| lognormal | .379674861370695 | 5 | .0982251362323475 | 1.47 | 47500 | 15424434176 |

All three fresh actual-node receipts passed the4GiB physical/effective floor. Observed process
wall was below both each heuristic projection and the300s cap; process wall total2.35s at time
utility display resolution. This is not a speed/generalization claim. Peak RSS was measured
externally, while original runner JSON correctly records that it did not internally measure RSS.
Native float64 DP reference observations exist; this does not establish D2/D8 learning value,
tuned generic headroom, infinite-support exactness or a certified error enclosure.

Original remote outputs under the recorded checkout's
`temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_<law>/` are unchanged.
CM copied summary.json,receipt.json,process_time.txt,task.log and terminal task_status.json
locally under the same relative root for DM archival. Task names are the frozen command names
above; all terminal witnesses show exit0. The DM owns tracked raw evidence/result/intake copies.
No live FSD task remains; no retry or successor is selected. No fresh platform refusal occurred.

Independent source review,13 focused tests and direct terminal/artifact observation support
technical acceptance of this exact observation. Source accounting remains A91/D0/O76 from
411adffc3; tests174 lines, documents separately. No source changed after review/test/calibration.
Limitations: numerical tolerance is the card's reporting convention; cold projection samples
are a heuristic; initial test fixture setup failed and was reproduced/repaired without a test
body or scientific computation. Current accepted publication path completed for all three laws.

Git note: attempted fast-forward of the DM projection commit into CM was refused because DM
integration ancestry diverged; no files/history were changed. DM projection remains pushed and
was read before dispatch. Root/DM can merge or cherry-pick this technical-record update normally.
