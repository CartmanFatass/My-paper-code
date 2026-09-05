# CRTO paired TRAIN order B03 technical evidence

Object `CRTO-PAIRED-ORDER-B03`, B/EXPLORE. CM technical evidence under
`CRTO_PAIRED_ORDER_B03_SCIENCE_CARD_20260904.md`; DM owns scientific intake.

## Source and implementation

Launch SHA `fd76e7d7fabcef34e9465c1c3a4f4406ff23b040` was committed and pushed on
`cm-crto-b02-20260904` before remote preparation. Card commit `037fe8316` was
cherry-picked as `6e7846326` onto the accepted B02 source/evidence. Four new files
implement B03: module, initializer, runner and mirrored test. B01/B02 and shared
helpers are unchanged; no core/control-plane changes were made.

One predictor/population/RAW packet preparation feeds two fresh seed-0 CPU FP32
learners, CANONICAL then PAIRED. Both call accepted B02 `train_raw`, with one shared
600-second start time. The only training intervention is the rows/packet index
permutation: original pair declaration positions and both source addresses bind
KEEP then REPLAN; event/onset is not treated as a unique pair identity. Existing
PacketDataset checks verify row-key alignment. Both learners finish before any
evaluation, using identical canonical EVAL data. No cycle mean, residual arm,
checkpoint files, optimizer-state reuse or historical-anchor gate is introduced.

Snapshots at 252/255/258 correspond to 168/170/172 occurrences of every TRAIN row
in both arms. Each PAIRED batch contains 16 original pairs, 16 KEEP and 16 REPLAN.
Intermediate-prefix equality is not claimed. All legal predicted scores, signed
native G16, first-printed legal ties, actions, regrets, keyed occurrence counts
and six parameter-exposure lines are retained for independent reconstruction.

## Scope and validation

Engineering-scope section 4 additions: **none**. Research code totals 232 physical
lines: module 192, runner 39, initializer 1; tests add 144 lines and reuse B02's
native-label fixture. Substantive orchestration totals 67 lines (34 module, 32
runner, 1 initializer), or 28.88% of new physical research lines. Neutral whitespace
is excluded from the numerator; this explicit classification found no breach.
No padding or unrelated code was added to change the ratio. Git diff checking
reported one harmless trailing blank line in the runner; no semantic defect.

Independent Reviewer inspected final source, tests and published engineering
artifacts and found no material finding. Local focused suite: 8 passed in 4.00
seconds, including one toy smoke (1.8127602 seconds pre-publication wall), no
repair or repeat. Tests cover original pair identity, same row/packet permutation,
all 258 PAIRED batches' balance/adjacency, exact keyed endpoint multisets, two
fresh equal-parameter models and empty Adam states, shared timer, evaluation after
both learners, and all five first-matching branches including threshold ties.

The offline publication profile runs six 16-row summaries with clearly synthetic
FP32 predictions and existing native labels through actual B03 comparison and JSON
publication. It establishes new-object publication coverage; no empirical values
are inferred from those fixtures. The historical native crash and earlier A01
formal-publication gap remain at their original identities.

Exact committed remote source passed the same 8 checks in 1.83 seconds, including
one prelaunch smoke. Pytest emitted its existing unknown `cache_dir` warning.
Remote checkout used configured `zsh -lic`; gitstatus and background gc/repack
warnings were printed, but fetch, exact-SHA worktree creation and tests succeeded.
These are preparation observations, not a result or a learner failure.

Focused command, from remote cwd below:

```sh
mkdir -p temp/directions/commitment_residual_triggered_options/test && /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/commitment_residual_triggered_options/test/b03-prelaunch-20260904 tests/experiments/candidates/commitment_residual_triggered_options/paired_order_b03
```

## Cost and exact launch

Non-result runner `project-cost --seed 0` emitted the carded B02 stage law:
`B=72.21711447201233`, `t=0.055606570529173026`, `f=0.0031416169993462974`,
`r=0.0031209949956974015` seconds. Factor-3 forecasts are
`259.72846654359813` seconds per arm and `302.79622668617213` shared, both below
600 seconds. Both arm forecasts conservatively include preparation; actual shared
time is charged once. No sweep or extra pilot was run.

Node `wsl_4070`, SSH `hmasd-wsl-node`, detached cwd
`/home/wu/hmasd-worktrees/crto-b03-fd76e7d7`. The one accepted task is
`crto_paired_order_b03_fd76e7d7_01`; supervisor root
`/home/wu/.agent-tasks/crto_paired_order_b03_fd76e7d7_01/` contains runner.sh,
task.log, start_time, status and exit_code. Default tracker
`/root/tracker_tl_experiments` acknowledged adoption of this exact handle/SHA;
CM released routine polling and retained collection/technical acceptance.

Exact accepted payload:

```sh
cd /home/wu/hmasd-worktrees/crto-b03-fd76e7d7 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/commitment_residual_triggered_options/exp/paired_order_b03_20260904/attempt01_admission.json && /home/wu/.venvs/hmasd/bin/python -X faulthandler scripts/run_crto_paired_order_b03.py run --seed 0 --output-dir temp/directions/commitment_residual_triggered_options/exp/paired_order_b03_20260904/attempt01 --execution-node wsl_4070
```

The destination admission immediately precedes the learner. CPU FP32, one thread,
expected RSS below 2 GiB; shared wall bound 600 seconds. Stop is one complete
summary or first admission/integrity/nonfinite/measurement/cap failure. No retry,
resume or duplicate accepted process is authorized by observer changes.

## Terminal collection

The accepted task finished with exit 0. CM collected the summary, fresh admission
and supervisor witnesses; exact SHA, argv including `-X faulthandler`, node, thread
declarations and stop boundary match the prospective contract. The implementation
and one completed observation are technically accepted; scientific interpretation
and independent rule application remain with DM.

| Direct observation | Value |
| --- | --- |
| Start / terminal UTC | 2026-09-05 00:54:25 / 00:56:20 |
| Admission UTC | 2026-09-05T00:54:25.247225Z |
| Physical / effective available bytes | 12,594,327,552 / 12,594,327,552; both 4-GiB floors passed |
| Supervisor exit / total duration | 0 / 115 seconds |
| Runner wall before publication | 109.53502406500047 seconds |
| Peak RSS | 1,279,832,064 bytes; measured, below expected 2 GiB |
| Predictor tapes / materialized examples | 128 / 32,256 |
| Predictor updates / processed examples | 100 / 12,800 |
| RAW updates / processed examples, both arms | 516 / 16,512 |
| Environment transitions / common-future branch steps | 38,464 / 3,520 |
| Forward / scored / unique EVAL rows | 96 / 96 / 16 |
| TRUE / DERANGED update and evaluation counts | all zero |
| CANONICAL / PAIRED training seconds | 16.579543292995368 / 14.374934131999908 |
| CANONICAL / PAIRED seconds per update | 0.06426179570928436 / 0.055716798961239954 |
| Forward / readout seconds | 0.029052272999251727 / 0.006876482999359723 |
| Forward seconds per snapshot | 0.0048420454998752875 |

The supervisor measures the full invocation, establishing total wall below 600;
the runner wall ends before publication. Tracker's later 292-second uptime is time
since launch, not run duration. All resource telemetry requested by this card is
present on the formal invocation. Machine time is charged once for shared preparation
and both paths; timing differences between arms are not a throughput claim.

Both arms' initial L2/RMS/Linf are
`18.87916908516977 / 0.10402732933491829 / 0.28862619400024414`.
Every saved endpoint has positive finite learner movement:

| Arm | Update | Examples | Per-row occurrences | L2 displacement / initial L2 | Linf displacement / initial Linf |
| --- | --- | --- | --- | --- | --- |
| CANONICAL | 252 | 8064 | 168 | 0.13399672519322534 | 0.9036122085192626 |
| CANONICAL | 255 | 8160 | 170 | 0.1354501914870501 | 0.9097531394403207 |
| CANONICAL | 258 | 8256 | 172 | 0.1369227563959056 | 0.915735779252775 |
| PAIRED | 252 | 8064 | 168 | 0.13568145972307277 | 0.9348288052748834 |
| PAIRED | 255 | 8160 | 170 | 0.1372608724719561 | 0.9423504724674662 |
| PAIRED | 258 | 8256 | 172 | 0.1388633711404481 | 0.949537384425807 |

Each occurrence record is keyed by all 48 TRAIN row identities; both orders and
full original pair addresses are retained. All endpoints have phase/cursor 0/0,
batch 32, Adam lr .001, and nominal LR exposure .252/.255/.258. Exact per-row
multiset equality, complete pair binding and legal scoring can be recomputed from
the output. No old-result-driven learner input or evaluation feedback was introduced.

Complete 285,563-byte collected summary is preserved alongside this E0 as
`CRTO_PAIRED_ORDER_B03_RESULT_20260904.json`. It includes the emitted branch and
full predictions/actions/native labels needed for independent DM rule application.
No post-result source changes or additional learner invocation occurred.

Local collection root:
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/paired_order_b03_20260904/attempt01_artifacts/`.
It contains summary.json, attempt01_admission.json, runner.sh, task.log, status,
start_time, exit_code and supervisor PID data. Remote evidence remains under its
original task/output roots. DM received the local summary before E0 completion
to independently reconstruct the comparison.

Limits: technical conformance establishes this bounded order-package observation,
not an isolated side-balance mechanism, general performance claim, independent
replication or resolution of the historical native crash. DM retains the scientific
ceiling and next-object decision; CM launches nothing further under this card.
