# CRTO RAW centered loss B07 technical evidence

Scientific object **CRTO-RAW-CENTERED-LOSS-B07**, B/EXPLORE. Both fixed seed
invocations completed and are technically accepted. DM owns independent native
arithmetic and scientific intake; engineering conformance supplies no mechanism value.

## Source, loss and protected path

Card/owner packet/items011/012 were pushed at52d700de8559677f3c34b4264c2968f8037ef22f
before implementation. Launch source5a4b5c20dd3e54350a0b18377541a0ae585d38bc was
committed and pushed before remote preparation. Only new raw_centered_loss_b07
experiment/test directories and scripts/run_crto_raw_centered_loss_b07.py were added.
All historical source and evidence remain unchanged.

The small local B04 train_path copy changes exactly the loss call. Predictions
and targets have separate FP32 legal means, each is subtracted from its own
vector, and the existing legal_masked_mse retains the pooled legal-element
denominator. The prediction mean remains differentiable. Evaluation uses ordinary
uncentered predictions. An error-first centering or detached mean is not substituted.

B06 predictor preparation and RAW packet construction remain unchanged: fixed
replicate0 tapes, seed-specific predictor initialization/fit permutation and gate
initialization, canonical48TRAIN/16EVAL population, native signed labels, CPU FP32,
pre-import thread environment and one intra/inter-op thread. Adam, gradient clipping,
batch32 and ordering remain identical except the intended new loss gradients.
Each seed trains one genesis-to516 path and reads only final516. No258 readout,
calibration, derangement, baseline replay, checkpoint I/O or old state is introduced.
The original1200-second training-plus-evaluation arm cap and1500-second invocation
cap are reused without global mutation or hidden clock offsets.

## Scope and verification

Engineering-scope section4 additions: **none**. Final research code219 physical
lines:186 module,32 runner,1 initializer. Tests124 lines. Independent review
counts63/219=28.77% substantive orchestration (36 module,26 runner,1 initializer).
There is no framework, callback layer, monkeypatch, padding or runtime digest guard.

One focused suite passed12 checks in3.93 seconds, with one toy publication smoke.
Mathematical checks cover pooled5-legal-element weighting, illegal exclusion,
separate FP32 means and prediction-mean gradients. The rounding case
p=[16777216,0],y=[16777218,1] gives loss.5 and gradient[-.5,.5], distinguishing
error-first centering and detached means. Source comparison verifies the copied
B04 loop is identical after reversing the one loss-call substitution. Tests cover
MEI boundaries/branch precedence and partial aggregation. Formal-size offline
publication joins16 frozen baseline rows with16 synthetic treatment rows even
when baseline order is reversed, checks native-label mismatch and changed-action D.

Toy wall1.6656692000105977 seconds; missing local peak RSS is resources_unmeasured,
and the toy has no scientific branch. Independent reviewer directly inspected
source, tests and publication artifacts and found no material issue. The only
post-suite edit corrected CLI help text; no learner or suite was repeated.
Test roots under C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/test/b07-implementation-20260905/:
test_one_toy_smoke_only_final_0/output/summary.json and
test_formal_baseline_join_and_0/summary.json. Historical A01 remains separate.

## Frozen baseline, projection and exact invocation

Baseline source is B06 E0 commit8c4c29cc9a9fd7c8faf838e3790920e1453a4137,
learner source7cad2758a156ebde0bd150b24ecee70bcc68982a. Original bytes were checked
against Git and the card before ordinary separate input staging, then checked on
the destination. No uncommitted source was transferred:

| Seed | Bytes | SHA256 |
| --- | --- | --- |
| 1 | 88379 | 8f7d2149af94a77a3f81520e0107e10559d47f5a02049c4e50069617ee4bcf05 |
| 2 | 88809 | 9fbabc802369e7b6ff285ad6f4e92cb593644849fb7e8ec90c3166c73ef9fc21 |

Inputs are /home/wu/hmasd-inputs/crto_b07_20260905/seed01_b06_summary.json and
seed02_b06_summary.json. Each comparison preserves its full baseline endpoint516
without modification; baseline data never enters the learner.

Both exact-source non-learning --project-cost outputs printed the carded law
3*(P+516*t_s+E_s), P62.425374370999634. Seed1 t=.05216934772284702,
E=.007404837990179658, projection268.05648790193663 seconds; seed2
t=.047116037356571785,E=.007313847003388219,projection260.2336904819822.
Total528.2901783839188 seconds; each arm is below1200 and each invocation below1500.
This old-objective extrapolation includes an unmeasured centering overhead and is
not a strict upper bound. Prior B06 scales/movement are labelled historical in
planning; new objective movement is measured separately in each result.

Node wsl_4070 /SSH hmasd-wsl-node. For s=1/2, cwd
/home/wu/hmasd-worktrees/crto-b07-s<s>-5a4b5c20, task
crto_raw_centered_b07_s<s>_5a4b5c20_01, root
temp/directions/commitment_residual_triggered_options/exp/raw_centered_loss_b07_20260905/seed0<s>/attempt01,
receipt sibling attempt01_admission.json. Each saved runner.sh joins cd, fresh
actual-node admission and this exact expanded scientific command with &&:

```sh
/home/wu/.venvs/hmasd/bin/python -X faulthandler scripts/run_crto_raw_centered_loss_b07.py --seed <s> --execution-node wsl_4070 --baseline-summary /home/wu/hmasd-inputs/crto_b07_20260905/seed0<s>_b06_summary.json --output-dir <root>
```

Both unique task names were absent before launch. Source fetch/worktree preparation
used configured zsh -lic and succeeded despite existing shell/gitstatus/background
gc warnings. No remote suite or repeat smoke ran. Fresh destination admission
requires physical/effective available>=4GiB, expectedRSS<2GiB per process. Stop is
complete summary or first carded failure/cap; no retry/resume or seed cancellation.
Tracker /root/tracker_tl_experiments acknowledged both handles and notified CM/DM
at terminal. CM did not duplicate routine polling.

## Terminal technical acceptance

Both tasks finished exit0 with tmux inactive. CM collected complete summaries,
admissions and supervisor files. Exact seed/SHA/argv/input path/thread contract,
unchanged predictor/source metadata/initialization, both resource floors and all
work counts agree with the card. Each baseline equals the original B06 endpoint516
record exactly. All32 new legal prediction/action/native-regret rows reconstruct
from printed-order maxima; native-label/identity alignment holds for every pair.
Side means/counts/competence, D, changed actions and emitted branches reconstruct
by read-only arithmetic. All48 recipient counts are344 and actual movement is
finite positive. These checks passed; DM received both originals before E0 completion.

Per seed: predictor128 tapes/32256 examples/100 updates/12800 processed examples;
gate516 updates/16512 examples,16 new forward/scored decisions and16 historical
decisions read. Environment transitions38464, common-future branch3520,
calibration tapes/examples and derangement packets zero. Across both:1032 updates,
33024 gate examples,32 new decisions plus32 historical reads,16 unique EVAL identities.
No baseline learner cost is invented.

The only learner warning in each log is the historical shared models.py:186
non-writable NumPy warning; no exception or fault stack. No source was changed
after result collection. No new diagnosis of the historical native crash follows.

Original summaries are preserved beside this E0 as
CRTO_RAW_CENTERED_LOSS_B07_SEED01_RESULT_20260905.json and
CRTO_RAW_CENTERED_LOSS_B07_SEED02_RESULT_20260905.json. Local evidence roots are
C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/raw_centered_loss_b07_20260905/
seed01/attempt01_artifacts/ and seed02/attempt01_artifacts/, each retaining
summary.json, attempt01_admission.json, runner.sh, task.log, status, exit_code,
start_time and pid. Remote inputs/results remain in place. Neither B07 task is live.

Remaining boundary: this is a finite objective comparison on an exposed panel,
not stable competence, independent generalization or residual value. A changed
loss also changes gradient scale, clipping and Adam trajectories; its effect cannot
isolate common-return fitting alone. DM owns the scientific reading and next object.
Root owner-review queries were [] at prelaunch and terminal boundaries; configured
remote_first/wsl_4070 route remains unchanged. Both remote source worktrees are
clean at5a4b5c20d. No owner override or unrelated workspace change was bypassed.

## Actual resources, scales and exposure

| Observation | Seed1 | Seed2 |
| --- | --- | --- |
| Admission UTC | 2026-09-05T10:30:39.534530Z | 2026-09-05T10:31:03.412659Z |
| Physical/effective available bytes | 12675358720 | 11448111104 |
| Both4GiB floors | passed | passed |
| Supervisor start/end UTC | 10:30:39 /10:32:43 | 10:31:03 /10:33:09 |
| Exit /duration seconds | 0 /124 | 0 /126 |
| Runner pre-publication wall seconds | 114.58920120599214 | 115.89204864800558 |
| Measured peak RSS bytes | 1285758976 | 1284915200 |
| measured_preparation_seconds | 78.89787938600057 | 82.43354327199631 |
| measured_training_seconds | 35.68319613300264 | 33.44885526500002 |
| measured_seconds_per_update | 0.0691534808779121 | 0.06482336291666671 |
| measured_forward_seconds | 0.004039987004944123 | 0.004585825998219661 |
| measured_scoring_seconds | 0.0009124239877564833 | 0.001242521990207024 |

Both supervisor durations are below1500 seconds; training+forward+scoring is below1200
per arm and both peaks are below2GiB. Total supervisor machine time250 seconds.
Runner wall ends before publication; later tracker uptime is observation age, not duration.
No formal resource telemetry is missing; the timing comparison is not a speed claim.

| Seed | Initial L2 | Initial RMS | Initial Linf | L2 movement ratio | Linf movement ratio |
| --- | --- | --- | --- | --- | --- |
| 1 | 18.92643228704128 | 0.10428775735716496 | 0.287416011095047 | 0.10900415513564093 | 0.9725612593361669 |
| 2 | 18.844772502567565 | 0.10383779850280324 | 0.2884293794631958 | 0.1206322176206708 | 1.0175024256157004 |

Both actual RAW exposure lines retain update516,batch32,16512examples,lr.001,
nominal LR exposure.516 and cycle phase/cursor0. Each of48TRAINrows occurs344times.
Initialization matches the same seed B06 initialization; new loss movement is its
own measured outcome and is not required to match the baseline.
