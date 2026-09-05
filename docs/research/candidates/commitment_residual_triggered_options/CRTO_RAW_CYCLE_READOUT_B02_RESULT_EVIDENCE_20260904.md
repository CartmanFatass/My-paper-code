# CRTO RAW cycle readout B02 technical evidence

Object: `CRTO-RAW-CYCLE-READOUT-B02`, B/EXPLORE. CM technical evidence; DM owns
scientific intake. Frozen card: `CRTO_RAW_CYCLE_READOUT_B02_SCIENCE_CARD_20260904.md`.

## Source and acceptance contract

Launch source is pushed `2b667289603b0f7b82508119b902090ddb841728`, branch
`cm-crto-b02-20260904`, based on card commit `dc5f52117e5e6a548fea76be6c44ddc3b54013ab`.
Only the new B02 experiment, runner, and mirrored tests/fixture changed. Historical
B01/A01 source and evidence remain unchanged; no core or control-plane files changed.

One seed-0 CPU FP32/one-thread RAW path processes 257 updates, 8224 examples;
snapshots 253..257 feed fixed endings 255/256/257. Endpoint and cycle readout share
each ending's path, labels, legal masks and exposure. Cycle predictions convert FP32
outputs to FP64 before left-associated ascending-update addition and division by 3.
Existing printed-order legal ties, signed native G16, nonnegative regret, predictor,
RNG, loss, Adam and snapshot timing remain protected. Evaluation follows all training.
No checkpoint files, optimizer-state I/O, residual arms, historical-anchor gate,
confirmation reads or result-sensitive stopping are introduced.

The A01 helper hardcodes 1800 seconds. DM explicitly accepted a B02-local equivalent
training loop changing only helper qualification and the 600-second wall monitor.
A focused source comparison strips those changes and checks equality to A01 `_train`.
This is engineering method under the frozen card, not a scientific amendment.

## Scope, review and checks

Engineering-scope section 4 additions: **none**. Research code: 323 lines, comprising
284 experiment, 38 runner and 1 initializer. Conservative orchestration: 91/323 =
28.17%. Tests: 130 Python lines plus 390 native-label fixture lines. No budget breach.
Independent Reviewer inspected the complete final diff and found no material issue;
it independently matched all 16 fixture labels to the accepted A02 trace-256 artifact.

Local focused suite initially had 7 passes and one cost-literal rounding failure in
6.22 seconds. Toy smoke ran once and completed in 2.8215756 seconds. The corrected
affected non-smoke test passed; final DM-directed reporting uses the actual formula
and a 1e-9 test tolerance against the printed card value. An intermediate reporting
repair was tested once before the DM preferred the simpler formula-only report.
No scientific parameter or cap changed.

The new formal publication profile exercises 16 native-label rows, five synthetic
FP32 prediction arrays, three endings and both readouts through the actual scoring
and JSON publication functions. Synthetic scores are explicitly marked engineering
fixtures, not learner evidence. Tests cover mean precision/order, legal ties, signed
labels, branch precedence, shared trajectory, source-loop equivalence and counters.
Historical A01 publication-coverage gap and native crash remain historical open items;
new B02 coverage does not repair or interpret them.

On the exact committed remote source, six checks passed in 1.03 seconds; two fixture
setups could not create the absent pytest basetemp parent, before either test ran.
Creating the parent and rerunning only those two checks gave 2 passes in 1.77 seconds.
Thus the remote prelaunch smoke executed once. Pytest emitted an existing unknown
`cache_dir` option warning. No source repair was needed for directory setup.

## Cost and execution

Remote `project-cost --seed 0` emitted:
`3 * (66.43271435800852 + 257 * 0.053103706378764895 + 5 * 0.004135982461425906)`
= `240.3031404289747` seconds per readout, under the shared 600-second cap.
The approximately 1.4e-12-second difference from the card's printed decimal is
rounding of its displayed stage constants, not a budget deviation. Each arm carries
the full shared cost projection; actual invocation time is charged once. No sweep
or additional pilot was performed.

Node `wsl_4070`, SSH `hmasd-wsl-node`; detached cwd
`/home/wu/hmasd-worktrees/crto-b02-2b667289`. Task
`crto_raw_cycle_b02_2b667289_01`, supervisor directory
`/home/wu/.agent-tasks/crto_raw_cycle_b02_2b667289_01/` (runner.sh, task.log,
status, start_time, exit_code). Tracker `/root/tracker_tl_experiments` acknowledged
adoption of this exact handle and SHA; CM released routine polling.

Exact accepted task payload:

```sh
cd /home/wu/hmasd-worktrees/crto-b02-2b667289 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/commitment_residual_triggered_options/exp/raw_cycle_readout_b02_20260904/attempt01_admission.json && /home/wu/.venvs/hmasd/bin/python -X faulthandler scripts/run_crto_raw_cycle_readout_b02.py run --seed 0 --output-dir temp/directions/commitment_residual_triggered_options/exp/raw_cycle_readout_b02_20260904/attempt01 --execution-node wsl_4070
```

Prelaunch preparation initially used a non-login network shell and stalled in Git
fetch/worktree materialization. Those preparation processes were terminated, with
no learner or scientific root created. The configured `zsh -lic` route successfully
materialized the committed SHA. Shell startup printed gitstatus/gc warnings; source
checkout and subsequent focused checks succeeded. No experiment was retried.

## Terminal collection

The accepted task finished with exit 0. CM collected the complete summary, adjacent
memory receipt and supervisor files. Exact launch SHA, argv including `-X faulthandler`,
node and one-thread declarations match the prospective command. Technical execution
is accepted; scientific result interpretation remains with DM.

| Direct observation | Value |
| --- | --- |
| Start / terminal UTC | 2026-09-05 00:03:41 / 00:05:11 |
| Admission UTC | 2026-09-05T00:03:41.594468Z |
| Physical / effective available bytes | 12,931,575,808 / 12,931,575,808; both floors passed |
| Supervisor exit / total duration | 0 / 90 seconds |
| Runner wall before publication | 86.52683217800222 seconds |
| Peak RSS | 1,286,844,416 bytes; measured, below expected 2 GiB |
| Predictor tapes / materialized examples | 128 / 32,256 |
| Predictor updates / processed examples | 100 / 12,800 |
| RAW updates / processed examples | 257 / 8,224 |
| TRAIN / EVAL population | 48 / 16 |
| Environment transitions / common-future branch steps | 38,464 / 3,520 |
| Snapshots / forward rows / scored decisions | 5 / 80 / 96 |
| TRUE / DERANGED update and evaluation counts | all zero |
| Training / forward / readout seconds | 14.290888625997468 / 0.015708084996731486 / 0.0031209949956974015 |
| Observed training seconds per update | 0.055606570529173026 |
| Observed forward seconds per snapshot | 0.0031416169993462974 |

Total supervisor duration establishes the complete invocation stayed below 600 seconds;
the runner wall field ends before JSON publication and is not represented as total time.
No peak-RSS or wall resource gap exists on the formal invocation. Uptime in a later
tracker status query includes time since completion and is not execution duration.

Initial L2/RMS/Linf: `18.87916908516977 / 0.10402732933491829 / 0.28862619400024414`.
Every recorded displacement is finite and positive. Snapshot exposure is:

| Update | Phase / cursor | Processed examples | Nominal LR exposure | L2 displacement / initial L2 | Linf displacement / initial Linf |
| --- | --- | --- | --- | --- | --- |
| 253 | 1 / 32 | 8096 | 0.253 | 0.13446324849442542 | 0.9054062776725487 |
| 254 | 2 / 16 | 8128 | 0.254 | 0.134960800203279 | 0.9077021699098619 |
| 255 | 0 / 0 | 8160 | 0.255 | 0.1354501914870501 | 0.9097531394403207 |
| 256 | 1 / 32 | 8192 | 0.256 | 0.1359241401392685 | 0.9115042541897065 |
| 257 | 2 / 16 | 8224 | 0.257 | 0.136428218836403 | 0.913744698073908 |

The initialization and update-256 historical descriptive comparisons both report
matches. This is an observed descriptive fact, not an additional validity predicate
or a repair of any earlier attempt. No result-conditioned code or launch change occurred.

The complete collected summary is preserved verbatim as
`CRTO_RAW_CYCLE_READOUT_B02_RESULT_20260904.json` alongside this E0. It contains all
five legal prediction vectors per row, both readouts at all three endings, native
labels/actions/regrets, exposure and emitted rule fields. DM independently recomputes
these fields and applies the frozen scientific rule in the separate intake.

Local collection root:
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/raw_cycle_readout_b02_20260904/attempt01_artifacts/`.
It contains `summary.json`, `attempt01_admission.json`, `runner.sh`, `task.log`,
`status`, `start_time`, `exit_code` and supervisor PID data. Remote scientific files
remain in the original output root; there was exactly one accepted invocation.

Residual limitation: this engineering acceptance establishes conformance of one
within-trajectory B/EXPLORE comparison. It supplies no independent-seed evidence or
scientific generalization, and does not close the historical native-crash question.
