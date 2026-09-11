# VSP-C1 K4 B01 technical record

## Prospective engineering contract

CM owns the implementation and observed execution of the scientifically selected [B01 card](VSPC1_K4_FACTOR_VALUE_B01_SCIENCE_CARD_20260905.md), with science and successor decisions retained by DM. Starting main: `582a2e4de0e67e47c33bd1b5a8cabb496450a7bf`, clean when inspected. Worktree: `C:/Projects/HMASD-worktrees/cm-vspc1-b01-20260905`; branch `codex/cm-vspc1-b01-20260905`. Concurrent work remains outside the owned paths.

Acceptance is a real seed-0 FACTOR/GENERIC comparison on the eight full-support contexts: correct six-step partner-dependent rewards, legal held actions, CPU FP32 networks of 188/191 parameters, exactly 128 unfrozen Adam steps, 8192 renewal transitions, episode-weighted loss, detached pre-update bootstrap and fixed nine-checkpoint evaluation. Each arm executes 25008 joint primitive steps. Actual action/context counts, parameter norms/displacement, all context returns, final J and normalized trapezoidal AUC must be readable. Final comparison and competing parameterization/optimization predictions belong to the DM; code conformance alone establishes no scientific advantage.

Owned source is `experiments/candidates/vsp_c1/k4_factor_value_b01/`, thin `scripts/run_vspc1_k4_factor_value_b01.py`, mirrored tests under `tests/experiments/candidates/vsp_c1/k4_factor_value_b01/`, and this record. Runtime evidence lives under ignored `temp/directions/vsp_c1/exp/`. Old audit/code/results, core, scientific card/intake, DIRECTION, shared Portfolio/audit/owner and workflow specifications are non-goals. No reference controller, forced-action evaluation, prerequisite A, extra seed, hyperparameter search or optional framework is selected.

Engineering scope section 4 additions: **none**. Ordinary in-process batch32 and existing supervisor/admission/timeout tools suffice. No queue beyond two serial commands, registry, resume, compatibility layer, provenance guard, profiler service or additional smoke is added. Source limit 2000, runner 600, research checks 5 minutes; orchestration ratio is a review signal only.

## State and protected dependency map

Each arm owns its network, Adam state and actual action trajectories. One batch contains 32 episode states `(p,tau,c,t,held_action)`. Time advances causally through six primitive steps. Period/partner/channel contexts are balanced; context ordering and exploration draws are shared by named seed streams, addressed independently of each arm's outcomes. Model initialization uses separate named streams because shapes differ. Greedy evaluation consumes no training randomness.

Boundary state is four FP32 features, action code is two entries, period code is two entries. FACTOR maps six inputs through 16 tanh units to four coordinates and dots the two-by-four embedding; GENERIC maps eight inputs through 19 tanh units to scalar Q. Renewal rows last only for a rollout/update cycle: 48 short-period plus 16 long-period rows. Targets are computed before the sole update and detached. Loss weight per row is `1/(32*(6/p))`; each period contributes one half. No replay, recurrence or checkpoint/resume serialization exists. Fixed evaluation and compact JSON are the sole primary consumers.

Preserve action timing, reward and normalization, public information, population, ordering/pairing, dtype, CPU/thread topology, all RNG stream assignments, optimizer parameters, bootstrap terminal semantics, all checkpoints and adverse outcomes. No cross-host bit-identity promise or frozen checkpoint format exists.

## Cost, placement and stop

Per arm cost law: imports/initialization + 24576 training joint steps / 8192 renewals + 128 updates over 64 rows + 432 evaluation joint steps / 144 decisions + actual semantic checks and publication. Unit times are unknown before the real invocation, not zero. The selected tiny dense tensor path needs no independent calibration or reference search; no measured speedup is asserted.

Two arm invocations run serially on configured `wsl_4070`, CPU FP32, one scientific process and one compute thread, in-process batch32. Each complete runner invocation has a 2700-second external timeout, including import/init/train/evaluation/checks/write/read. Sum of caps is 5400 seconds; study critical path, summed actual wall and aggregate CPU are reported distinctly. External Git/SSH/checkout/preparation is not scientific invocation time and is reported separately without invented timings.

Only committed and pushed source enters an exact-SHA detached remote worktree. Fresh actual-node `admit-memory` immediately precedes each runner, joined with `&&` inside its existing `agent-task` command. Both physical and effective available memory must be at least 4 GiB. No remote process or admission exists at this record's initial boundary. A cap or technical failure preserves outputs, supplies no mechanism polarity, and does not authorize extra seeds/arms or duplicate launches.

## Verification plan

Read-only source inspection plus focused pure/serialization tests check the changed dependencies without extra model/learner/environment exposure. Independent reviewer inspects actual source; formal budgeted trajectories provide held-action, partner/reward, count and loss-weight observations. Primary JSON is written and read within each invocation and read independently after completion. No separate environment or learner smoke and no historical publication replay is selected. This uses current evidence-spec sections 11.8/11.9 over older directory smoke defaults.

Scientific-tools skill and only its relevant adapters reference were read. The selected small Q host needs no PPO rewrite, PettingZoo interface migration or new dependency. Existing Torch native tensor operations implement the specified networks; current node declares Torch 2.7.0 and Python 3.10.21. No global interpreter upgrade follows.

## Implementation, review and execution

The initial prospective boundary had no result; completed evidence follows.

## Completed implementation and direct technical acceptance

Source commit `e7e574b4496875f45e1d1b9b41c02cd35cf3684e` was committed and immediately pushed before remote preparation. It adds 248 experiment lines, 25 model-free reporting lines and a 66-line runner (339 non-test lines), plus 38 test lines. The implementation child's four pure tests passed in 0.09 seconds: declared arithmetic, Python parsing, fixed AUC including adverse values, and primary JSON readback. They import no experiment module and construct no model, RNG, environment or optimizer. No second smoke was run. CM inspected the integrated source; independent reviewer `/root/dm_amx_k4_vspc1_design/cm_am_vspc1_b01/rev_ah_vspc1_b01` inspected the same fixed commit and found no material defect before formal execution. Some runtime formula checks share expressions with generation; their zero counters are not independent proof by themselves. Source inspection and direct primary-output checks provide the separate evidence.

Actual source map: `Value` owns network parameters and two-action scoring; `state_at` supplies the common four features; `rollout` executes six batched joint ticks and gathers renewal rows; `evaluate` executes eight budgeted episodes; `run` owns one optimizer, 128 cycles and all nine checkpoints. `reporting.py` performs the fixed aggregate and JSON write/read. The thin runner sets BLAS threads before heavy imports and Torch intra/inter-op to one inside the run. There is no core import change, reference search, checkpoint recovery, extra seed or third arm.

Named NumPy streams are SeedSequence `[0,101]` for context permutation and `[0,102]` for exploration; each cycle draws a fixed `(32,6,2)` array. Torch FACTOR dense/embedding seeds are 201/202; GENERIC dense seed is 301. Evaluation is greedy/deterministic and takes no random draws. These are actual recorded streams, not a claim that different model shapes share parameter bytes. CPU FP32, Python 3.10.21, NumPy 1.26.3, Torch 2.7.0+cu118 (CPU tensors) were used.

## Exact formal execution and observations

Node: configured `wsl_4070`, SSH `hmasd-wsl-node`. Both invocations used detached cwd `/home/wu/hmasd-worktrees/vspc1-b01-e7e574b44` at the source SHA above. The ordinary non-login network fetch stalled; that preparation was interrupted and the configured `zsh -lic` fetch succeeded. Remote Git printed an existing background-gc/repack warning and shell prompt warnings, but fetch and exact detached checkout completed with exit zero. No scientific invocation had started during that preparation; no source bytes were copied uncommitted. Git/SSH/preparation wall is unmeasured and separate from experiment wall.

The existing supervisor accepted exactly these two task names, serially: `vspc1_b01_factor_s0_e7e574b44_01` and `vspc1_b01_generic_s0_e7e574b44_01`. Each command is recorded verbatim in the copied `runner.sh`. The logical command, substituting each selected arm and its distinct root, was:

```bash
cd /home/wu/hmasd-worktrees/vspc1-b01-e7e574b44 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out <root>/admission.json && /usr/bin/time -v -o <root>/invocation.time timeout --signal=TERM 2700s /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_factor_value_b01.py --arm <FACTOR|GENERIC> --seed 0 --out <root>
```

The complete command runs inside `/usr/local/bin/agent-task run <task> <command>`. Required publication/readback stays inside timeout. No automatic continuation or repeat exists. `<root>` is cwd plus `temp/directions/vsp_c1/exp/k4_b01_factor_seed0_e7e574b44_01` or `k4_b01_generic_seed0_e7e574b44_01` respectively.

| Observation | FACTOR | GENERIC |
| --- | ---: | ---: |
| Actual-node admission UTC | 2026-09-05 23:55:03.974447 | 2026-09-05 23:55:59.793693 |
| Physical/effective available bytes (both pass) | 15404367872 | 15411888128 |
| Supervisor PID | 1704221 | 1704797 |
| Terminal UTC | 2026-09-05 23:55:05 | 2026-09-05 23:56:03 |
| Supervisor exit | 0 | 0 |
| Complete external invocation wall seconds | 1.76 | 3.95 |
| External user + system CPU seconds | 1.52 + 0.19 | 1.58 + 0.18 |
| External maximum RSS KiB | 510076 | 510008 |
| Runner through final readback seconds | 1.479294379 | 3.190416295 |

Fresh `/proc/meminfo` receipts passed both 4-GiB floors; cgroup limits/headroom were unavailable in these receipts, not asserted as measured unlimited capacity. External GNU time covers process startup, imports, initialization, training, evaluation, checks, all writes/readbacks, stdout and process shutdown, including its waited descendants. Its maximum RSS is a process/descendant high-water observation, not a sum of simultaneous process peaks. Runner-internal RSS/CPU timestamps precede final metadata/stdout/shutdown and are not substituted for complete external accounting. Extra standard GNU time fields were not used to make additional telemetry claims.

Summed complete invocation wall is **5.71 seconds**, aggregate CPU **3.47 seconds** at GNU time precision. Supervisor timestamps bound study elapsed from first task start to last terminal at approximately **60 seconds**, including the serial handoff/observation gap; it is not 60 seconds of scientific compute. Neither invocation approaches the 2700-second cap. No profiler, device/worker sweep or new calibration was run. Actual contention/wait attribution is unmeasured; the longer GENERIC wall is not attributed to a specific cause or presented as an algorithm speed comparison.

The shared tracker `/root/tracker_tl_experiments` ACKed both exact handles and independently returned terminal exit-zero facts to CM and DM. CM did not relaunch either handle after handoff. All scientific processes for this assignment are terminal.

## Actual primary measurements

Both arms completed 4096 training episodes, 24576 training joint ticks, 8192 training renewals (6144 at p2 and 2048 at p6), exactly 128 Adam steps, 72 evaluation episodes, 432 evaluation ticks and 144 evaluation decisions. Complete totals are 25008 joint ticks and 8336 legal decisions per arm. Every training context received 512 episodes. Each arm checked 4168 actual budgeted episodes; held-action, partner-timing, reward, return, terminal-bootstrap and loss-weight violation counters are all zero. Both readable summaries state `complete`, with no primary dependency defect. Model parameter counts are actually 188/191. These measurements establish the complete selected implementation path, not mechanism truth or stable seed-population performance.

| Quantity | FACTOR | GENERIC |
| --- | ---: | ---: |
| theta0_norm | 4.01100826263 | 3.65843296051 |
| theta128_norm | 4.34473371506 | 3.87522768974 |
| theta_displacement_norm | 2.0328578949 | 1.59698557854 |
| displacement_to_initial_norm | 0.506819672708 | 0.436521755565 |
| initial_return | 0.5 | 0.5 |
| final_return | 0.625 | 0.666666666667 |
| learning_gain | 0.125 | 0.166666666667 |
| normalized_auc | 0.580729166667 | 0.609375 |

Direct arithmetic: FACTOR minus GENERIC final J = -0.04166666666666663 and normalized AUC = -0.02864583333333326. Scientific interpretation and successor selection remain with DM. The same J0 does not imply identical initial policies. The known analytic reference is not an executed arm or measured tuned headroom.

| Update | FACTOR J | GENERIC J |
| ---: | ---: | ---: |
| 0 | 0.5 | 0.5 |
| 16 | 0.541666666667 | 0.5 |
| 32 | 0.541666666667 | 0.541666666667 |
| 48 | 0.583333333333 | 0.583333333333 |
| 64 | 0.541666666667 | 0.666666666667 |
| 80 | 0.625 | 0.666666666667 |
| 96 | 0.625 | 0.666666666667 |
| 112 | 0.625 | 0.666666666667 |
| 128 | 0.625 | 0.666666666667 |

### FACTOR complete evaluation contexts

Context columns are `(p,tau,c)`; each entry is the native return from one real six-step episode.

| Update | 2,2,0 | 2,2,1 | 2,4,0 | 2,4,1 | 6,2,0 | 6,2,1 | 6,4,0 | 6,4,1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.666666666667 | 0.333333333333 | 0.333333333333 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 | 0.333333333333 |
| 16 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 |
| 32 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 |
| 48 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.333333333333 |
| 64 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 |
| 80 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 |
| 96 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 |
| 112 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 |
| 128 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 |

### GENERIC complete evaluation contexts

Context columns are `(p,tau,c)`; each entry is the native return from one real six-step episode.

| Update | 2,2,0 | 2,2,1 | 2,4,0 | 2,4,1 | 6,2,0 | 6,2,1 | 6,4,0 | 6,4,1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.333333333333 | 0.666666666667 | 0.666666666667 | 0.333333333333 | 0.333333333333 | 0.666666666667 | 0.666666666667 | 0.333333333333 |
| 16 | 0.666666666667 | 0.333333333333 | 0.333333333333 | 0.666666666667 | 0.666666666667 | 0.333333333333 | 0.333333333333 | 0.666666666667 |
| 32 | 0.666666666667 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 | 0.333333333333 | 0.333333333333 | 0.666666666667 |
| 48 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.333333333333 | 0.666666666667 | 0.666666666667 | 0.333333333333 |
| 64 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 |
| 80 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 |
| 96 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 |
| 112 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 |
| 128 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 | 0.666666666667 |

### Actual action counts

Counts below retain zero cells and all legal boundary choices; training/evaluation totals are 8192/144 per arm. Evaluation counts aggregate the nine fixed checkpoints and are not independent training samples.

| p | tau | c | tick | action | FACTOR train | GENERIC train | FACTOR eval | GENERIC eval |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 2 | 0 | 0 | 0 | 143 | 195 | 0 | 4 |
| 2 | 2 | 0 | 0 | 1 | 369 | 317 | 9 | 5 |
| 2 | 2 | 0 | 2 | 0 | 118 | 150 | 0 | 1 |
| 2 | 2 | 0 | 2 | 1 | 394 | 362 | 9 | 8 |
| 2 | 2 | 0 | 4 | 0 | 170 | 223 | 0 | 4 |
| 2 | 2 | 0 | 4 | 1 | 342 | 289 | 9 | 5 |
| 2 | 2 | 1 | 0 | 0 | 342 | 354 | 6 | 7 |
| 2 | 2 | 1 | 0 | 1 | 170 | 158 | 3 | 2 |
| 2 | 2 | 1 | 2 | 0 | 336 | 364 | 6 | 7 |
| 2 | 2 | 1 | 2 | 1 | 176 | 148 | 3 | 2 |
| 2 | 2 | 1 | 4 | 0 | 354 | 375 | 5 | 8 |
| 2 | 2 | 1 | 4 | 1 | 158 | 137 | 4 | 1 |
| 2 | 4 | 0 | 0 | 0 | 370 | 351 | 8 | 7 |
| 2 | 4 | 0 | 0 | 1 | 142 | 161 | 1 | 2 |
| 2 | 4 | 0 | 2 | 0 | 384 | 370 | 8 | 7 |
| 2 | 4 | 0 | 2 | 1 | 128 | 142 | 1 | 2 |
| 2 | 4 | 0 | 4 | 0 | 369 | 362 | 8 | 7 |
| 2 | 4 | 0 | 4 | 1 | 143 | 150 | 1 | 2 |
| 2 | 4 | 1 | 0 | 0 | 216 | 173 | 3 | 1 |
| 2 | 4 | 1 | 0 | 1 | 296 | 339 | 6 | 8 |
| 2 | 4 | 1 | 2 | 0 | 155 | 133 | 1 | 1 |
| 2 | 4 | 1 | 2 | 1 | 357 | 379 | 8 | 8 |
| 2 | 4 | 1 | 4 | 0 | 149 | 147 | 0 | 1 |
| 2 | 4 | 1 | 4 | 1 | 363 | 365 | 9 | 8 |
| 6 | 2 | 0 | 0 | 0 | 151 | 184 | 1 | 2 |
| 6 | 2 | 0 | 0 | 1 | 361 | 328 | 8 | 7 |
| 6 | 2 | 1 | 0 | 0 | 144 | 356 | 2 | 7 |
| 6 | 2 | 1 | 0 | 1 | 368 | 156 | 7 | 2 |
| 6 | 4 | 0 | 0 | 0 | 384 | 366 | 9 | 7 |
| 6 | 4 | 0 | 0 | 1 | 128 | 146 | 0 | 2 |
| 6 | 4 | 1 | 0 | 0 | 146 | 169 | 2 | 2 |
| 6 | 4 | 1 | 0 | 1 | 366 | 343 | 7 | 7 |

## Accessible evidence and limitations

Original remote output roots are above. Exact collected local copies are:

- `C:/Projects/HMASD/temp/directions/vsp_c1/exp/k4_b01_factor_seed0_e7e574b44_01/`
- `C:/Projects/HMASD/temp/directions/vsp_c1/exp/k4_b01_generic_seed0_e7e574b44_01/`

Each holds `summary.json`, `admission.json`, `invocation.time`, `task.log`, `exit_code`, `start_time`, and the supervisor's exact `runner.sh`. These are evidence copies, not new scientific runs. Remote supervisor evidence remains under `/home/wu/.agent-tasks/<task>/`. This tracked record preserves all curve/context/action measurements even though raw runtime roots are ignored.

CM independently read JSON and recomputed all eight-context means, nine-point schedule, action totals and training-context counts from existing data. No extra model or environment was executed. Independent primary-output review follows below. A single paired training seed cannot estimate training-seed uncertainty; fixed public partner, different parameterizations and initialization/optimization remain scientific limitations. No GPU, C++, exact replay, tuned baseline or broader claim was tested.

## Independent output review and CM conclusion

The same independent reviewer read both actual result packages, recomputed all 18 checkpoint populations/means/period/partner strata, and reconciled cumulative evaluation reward from action counts with the curve returns. All training-context counts, action totals (including five FACTOR evaluation zero cells and no GENERIC evaluation zero cells), update/transition/evaluation counts, norms/ratios, adjacent admissions, serial ordering, exit witnesses and complete GNU time boundaries were checked. It reported no material defect or missing primary dependency. It did not replay parameters or sample runtime threads: displacement comes from the actual learner's records and single-thread semantics from inspected configuration, not stronger unperformed verification.

CM accepts the implementation and both complete seed-0 arm observations for the selected B comparison. All assigned scientific processes are terminal; original and local copied outputs remain available. No source repair, scientific rerun or extra assessment was needed. Source `e7e574b44` and initial contract `63132a379` are pushed; this completion record is committed and pushed separately. The next step is the existing DM's scientific intake and successor decision using these exact measurements, preserving the negative endpoint/AUC differences and single-seed scope. No successor seed or extra arm is selected by this technical acceptance.

## Seed 1/2 extension: prospective contract

DM selected the same comparison on independent seeds 1 and 2 in the committed follow-up card and seed0 intake decision 2, DM branch at `363093f3716afd1800fe666f495032ad5d652de7`. The complete follow-up card was read from its exact committed local worktree. Only CLI choices change from `(0,)` to `(0,1,2)`; accepted scientific implementation `e7e574b44` remains byte-identical. No seed0 rerun or scientific/output/RNG change is selected. Scope section 4 additions: none. Existing source/primary-path checks are reused; no extra learner/environment smoke or profiler is needed.

Exactly four new invocations run serially: FACTOR1, GENERIC1, FACTOR2, GENERIC2. Each remains CPU FP32, single process/compute thread, batch32, 128 updates, 8192 renewals and 25008 joint steps. Fresh seed-keyed model/Adam and streams retain within-seed exogenous pairing and between-seed independence. Each complete invocation retains 2700 seconds and its own fresh actual-node memory admission immediately before runner. Existing exact-shape costs project 1.76 seconds per FACTOR and 3.95 per GENERIC, 11.42 summed seconds conditionally, not a guarantee. Four nominal caps sum to 10800 seconds; new exposure totals 100032 joint steps and 512 updates. No replacement seed, changed comparator, tuning, early metric window or continuation is authorized.

Ownership, remote-first node, detached exact-SHA source, output structure and tracker handoff remain the original CM contract. Independent review checks the one-line seed-choice diff and new actual seed/output records. All four complete measurements will be returned to DM separately; scientific aggregation and next decisions remain DM-owned.

## Seed 1/2 completed technical observations

Launch source is committed/pushed `e2f00991f4d6ccd169e531ef411ebc1547f2d371`. Independent reviewer confirmed the sole source change is seed CLI admission; accepted scientific dependencies remain unchanged. Existing pure tests and source review were reused, with zero extra model/environment/learner smoke. All four actual scientific invocations were accepted once and completed serially in selected order. No seed0 run, extra arm, tuning, repeat or repair occurred.

Exact detached remote cwd is `/home/wu/hmasd-worktrees/vspc1-b01-e2f00991f` on configured `wsl_4070`. Each used the original logical command above, substituting this cwd, its actual `--seed 1` or `--seed 2`, selected arm, and unique root. Each command is verbatim in its package's `runner.sh`: fresh configured-Python `admit-memory --out <root>/admission.json && /usr/bin/time -v -o <root>/invocation.time timeout --signal=TERM 2700s` followed by configured Python, unchanged B01 runner, arm/seed/out. All write/read and final shutdown remain within complete external time. Git/SSH/checkout and handoff overhead are separate, not attributed to algorithm cost. Existing remote prompt/background-gc warnings did not prevent successful fetch and exact checkout.

| Invocation | Task suffix after `vspc1_b01_` | Supervisor PID | Admission UTC (2026-09-06) | Physical/effective available bytes, both | Terminal UTC | Exit |
| --- | --- | ---: | --- | ---: | --- | ---: |
| FACTOR1 | factor_s1_e2f00991f_01 | 1818915 | 00:14:01.498168 | 15364902912 | 00:14:04 | 0 |
| GENERIC1 | generic_s1_e2f00991f_01 | 1819313 | 00:14:33.170286 | 15365132288 | 00:14:35 | 0 |
| FACTOR2 | factor_s2_e2f00991f_01 | 1826693 | 00:15:08.606978 | 15049617408 | 00:15:11 | 0 |
| GENERIC2 | generic_s2_e2f00991f_01 | 1841480 | 00:15:47.627755 | 14968045568 | 00:15:50 | 0 |

Every fresh actual-node receipt passes both 4-GiB floors. Tracker `/root/tracker_tl_experiments` ACKed and independently confirmed all four terminal handles, notifying this CM and DM. No process remains live.

| Invocation | Params | Train episodes / renewals / updates | Eval episodes / joint steps | Complete joint steps | J0 | J128 | Full normalized AUC |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| FACTOR1 | 188 | 4096 / 8192 / 128 | 72 / 432 | 25008 | 0.458333333333 | 0.708333333333 | 0.625 |
| GENERIC1 | 191 | 4096 / 8192 / 128 | 72 / 432 | 25008 | 0.5 | 0.625 | 0.591145833333 |
| FACTOR2 | 188 | 4096 / 8192 / 128 | 72 / 432 | 25008 | 0.458333333333 | 0.708333333333 | 0.59375 |
| GENERIC2 | 191 | 4096 / 8192 / 128 | 72 / 432 | 25008 | 0.5 | 0.625 | 0.5703125 |

Actual new totals: 16384 training episodes, 32768 renewals, 512 updates, 288 evaluation episodes, 100032 complete joint steps. Each invocation has 512 episodes per training context, 6144/2048 training renewals by period, 8192 training action choices and 144 evaluation choices. All nine fixed evaluation checkpoints and all context/action cells, including zeros and adverse values, remain in each raw summary. Actual violation counters are zero and all four primary dependency lists empty. Source/actual counters establish the selected complete execution, not stronger scientific claims.

| Invocation | Initial norm | Displacement norm | Displacement / initial | Complete wall seconds | User + system CPU seconds | External max RSS KiB |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| FACTOR1 | 4.01937103271 | 1.84172797203 | 0.458212978359 | 2.77 | 2.37 + 0.31 | 510160 |
| GENERIC1 | 3.57992482185 | 1.66074502468 | 0.463905000056 | 2.76 | 2.43 + 0.28 | 509652 |
| FACTOR2 | 3.88370251656 | 2.19178223610 | 0.564353790424 | 2.90 | 2.54 + 0.27 | 509960 |
| GENERIC2 | 3.48659014702 | 1.65313804150 | 0.474141775141 | 2.86 | 2.52 + 0.28 | 509892 |

Complete invocation wall sums to **11.29 seconds**, aggregate CPU **11.00 seconds**, at GNU time precision. The conditional 11.42-second planning projection was not a cap or performance guarantee. All four invocations are under their unchanged 2700-second cap. Supervisor timestamps give approximately **109 seconds** study elapsed including serial handoff/observation gaps. External RSS and full-wall/CPU scope remain as defined for seed0; no runtime contention cause, multi-host equivalence or parameter replay is inferred. No profiler or extra measurement was launched.

Actual NumPy streams are `[1,101]/[1,102]` and `[2,101]/[2,102]`; paired arms share these within each seed. FACTOR dense/embedding streams are 1201/1202 and 2201/2202; GENERIC dense streams 1301 and 2301. Evaluation consumes no training randomness. Fresh parameter norms and displacements are observed for every learner, not copied from seed0.

The four complete original packages are retained remotely at cwd plus `temp/directions/vsp_c1/exp/k4_b01_<factor|generic>_seed<1|2>_e2f00991f_01/`. Local copies are at `C:/Projects/HMASD/temp/directions/vsp_c1/exp/` with those same four directory names. Each contains `summary.json`, `admission.json`, `invocation.time`, `task.log`, `exit_code`, `start_time`, and exact supervisor `runner.sh`. Supervisor originals remain `/home/wu/.agent-tasks/<task>/`. DM received the readable paths for raw evidence archiving and complete scientific intake; the table above does not replace their full context/action/curve values.

CM's direct JSON count/readback review verifies actual seeds, stream addresses, full exposure, action totals and context support. Independent output review is recorded below. Seed0's adverse result is preserved; new seeds are not interpreted as reversing a population claim. DM owns separate new-seed and explicitly historical-inclusive three-seed summaries and all further decisions. No further invocation is selected by this return.

Independent reviewer completed read-only analysis of all four packages and found no material defect or missing primary dependency. It independently recalculated all endpoint/AUC/context/period/partner means, counts, seed stream assignments, parameter movement ratios, admissions, serial order and full timing. It retained the one FACTOR seed1 zero evaluation-action cell; no training action cell was missing. It reported endpoint differences +0.083333333333 for each new seed, AUC differences +0.033854166667 and +0.0234375, without discarding the contrary seed0. No new experiment, parameter replay or thread sampling occurred during review.

CM technically accepts all four selected SEED12 observations with the stated limitations. All handles are terminal and no work remains live in this assignment. The seed-permission source commit `e2f00991f` is pushed; this completion evidence is separately committed and immediately pushed. Return to the existing DM for scientific intake; no further seed or arm is authorized here.
