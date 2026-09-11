# B01 implementation and non-target check02 technical acceptance

The reviewed implementation exists and the explicitly selected check02 completed the real
N7 collection/update/evaluation/publication path. Source:
`33e08f440c2117dcfd9457d825f42fef7b38ccd7`; draft PR
https://github.com/CartmanFatass/My-paper-code/pull/2 . This is engineering evidence, not
a formal B01 learning result or a claim of statistical superiority.

## Implemented and independently reviewed

Five new owned files implement the card:37-line runner; `native.py`, `learning.py`,
`experiment.py` under the new B01 candidate;45-line existing-output test. Production538 lines.
R01/R02/R09/headroom sources remain read-only; scope:none. Independent reviewer found no
unresolved material source defect after repairing full cost coverage and making the narrow
presentation consequence check use the same batch size. Review traced native ABI, N7 survivors,
canonical/null/fixed/zone2 physical mapping, addressed RNG separation, episode-major GAE,
collected forced-command PPO replay, optimizer exposure, endpoint accounting and publication.

The implementation keeps two actual CPU binary64 learners, four PPO epochs/minibatch24,
32 optimizer steps per32-episode round, fixed BCRH and initial/mid/final checkpoints. Native
recovery context is explicitly20s-resolution observations plus endpoint ratios/native flags;
old shadow-system exact recovery latencies are unavailable and are not inferred.

## Actual check02 and outputs

DM selected this one unchanged retry in `VNFC_N7_DIRECT_RETURN_B01_CHECK01_INTAKE_20260905.md`
(original selection commit `cad14bbb2`, integrated as `a4036ac1e`). No source, dependency,
HMAC, seed, model or native-library source changed after check01.

Task `vnfc_b01_check_33e08f440_20260905_02` ran on configured `wsl_4070` at detached cwd
`/home/wu/hmasd-worktrees/vnfc_b01_check_33e08f440_02`, using the exact selected command.
Fresh admission passed:15,426,125,824 physical/effective available bytes. Terminal exit0.
The supervisor observed22s elapsed; precise external chain wall21.71s includes import/build,
both learners, BCRH, publication and output pytest. Aggregate user20.64+system1.87=22.51 CPU-s.
Runner wall through its complete publication20.218502969s; pytest reported1 passed in0.75s.
External maximum RSS543,720KiB is an observed maximum, not summed simultaneous memory.

| Observed work | MAPR | DIRECT | BCRH |
| --- | ---: | ---: | ---: |
| Complete training episodes | 64 | 64 | 0 |
| Joint training transitions | 384 | 384 | 0 |
| Optimizer steps/backward calls | 64/64 | 64/64 | 0 |
| Evaluation episodes | 24 | 24 | 8 |
| Complete BCRH controller/checker calls | 0 | 0 | 48 |
| Parameters | 89,090 | 148,739 | fixed |
| Initial parameter norm | 33.3166654994 | 38.6522987673 | n/a |
| Relative parameter movement | .0688416059 | .0693235828 | n/a |

Total184 episodes and44,160 native ticks. All terminal/endpoint reads completed. Test reconstructed
primary and training reward from native service/demand and read all six checkpoints. The runner
published five paired contrasts with aggregate/zone readings; no outcome was selected or dropped.
Training recorded219/239 null choices and456/467 fixed choices (MAPR/DIRECT),192 zone2 commands
per arm, and each arm's initial evaluation passed one same-batch presentation permutation
physical-action consequence check. Actual forced-command replay and first-minibatch likelihood
checks passed. DIRECT residual output parameter norm moved from0 to.08226634; evaluation residual
logit RMS was0 at initialization, .00786551 at midpoint, .05333662 at final. These establish actual
update/activity observations, not useful return or comparator competence.

Tracked raw outputs are under `evidence/b01_check_20260905_02/`: full task log, memory receipt,
external time, summary, training curves and all training/evaluation episode rows. All six `.pt`
checkpoints and built library remain at remote cwd plus
`temp/directions/variable_n_fleet_churn/b01_check_20260905_02/output/` and were read back.
The scientific-tool method was used to calculate exposure/phase tables from these actual JSON
outputs; no additional simulation, profile or timing invocation was run.

## Complete conditional cost projection

Use final stdout `complete_projection` in `check.log`. It includes the last summary replacement
write/readback, whereas `summary.json` explicitly carries the preceding intermediate projection.
Collection uses the actual32-episode batch and update uses actual24-transition minibatches.
Maximum observed per-unit/round wall among this check's measurements is used, with evaluation
and BCRH episode scaling, measured world generation, scaled residual bookkeeping overhead and
conservative full/check row-ratio scaling of all checkpoint/JSON publication.

| Formal work term | Projected seconds |
| --- | ---: |
| Shared import/build/initialization | 7.671873 |
| Training-world generation | 1.439145 |
| Evaluation-world generation | .038719 |
| Other measured overhead | .329268 |
| MAPR2048 collection episodes +64 updates +192 evaluation episodes | 112.199289 |
| DIRECT same complete work | 121.632887 |
| Fixed BCRH64 episodes,384 complete calls | 37.706789 |
| Complete publication | 1.593053 |
| Total | **282.611022** |

This is below the unchanged2700s complete formal cap and supplies applicable planning evidence.
It is not measured formal completion or a guaranteed upper bound. Evaluation/BCRH batch width
changes from8 in the check to64 formally; linear episode scaling is an explicit assumption.
World/state variation, later learner parameters and node contention may change unit costs.
The required formal bound remains external timeout2700s, with complete actual wall reported.
No unknown component is intentionally set to zero and no speedup is inferred from E01 or old
Windows wall. Shared preparation is counted once, with no concurrent learner assumption.

Preserve prior costs: check01 failed-chain3.90wall/3.28CPU plus check02 gives25.61 measured wall
and25.79 CPU-s. The earlier initialization diagnostic adds6s supervisor elapsed, without precise
CPU measurement; the small HMAC probes did not collect machine CPU/wall. These are not free or
folded into a claimed complete precise total. They are engineering preparation, not additional
formal2700s allocations. The original unexplained HMAC exception remains a runtime risk;
check02 success does not establish its cause or prove it cannot recur.

## Exact prospective formal handoff, not an execution

No third check or formal run has been launched. No current technical gap requires another smoke,
full historical replay, dependency change or Pro round. Root/DM may select the frozen formal
invocation from this evidence. It must use the same accepted source, fresh admission and new
output directory, with whole2700s bound; keep the original exception in intake.

Prospective detached cwd `/home/wu/hmasd-worktrees/vnfc_b01_formal_33e08f440_01` at source above;
task `vnfc_b01_formal_33e08f440_20260905_01`. If selected, the complete command is:

```sh
cd /home/wu/hmasd-worktrees/vnfc_b01_formal_33e08f440_01 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/variable_n_fleet_churn/b01_formal_20260905_01/memory.json && /usr/bin/time -v -o temp/directions/variable_n_fleet_churn/b01_formal_20260905_01/whole_time.txt timeout 2700s /home/wu/.venvs/hmasd/bin/python scripts/run_vnfc_n7_direct_b01.py --profile formal --seed 2026090501 --eval-seed 2026090502 --launch-sha 33e08f440c2117dcfd9457d825f42fef7b38ccd7 --out temp/directions/variable_n_fleet_churn/b01_formal_20260905_01/output
```

This runs64 rounds per arm, initial/32/64 evaluation and fixed BCRH exactly as the card;
its complete native/data/checkpoint publication is inside the timed invocation. It does not
repeat the engineering-only presentation probe or output pytest. Root receives ordered source
and docs commits for integration. DM retains scientific selection and interpretation.
