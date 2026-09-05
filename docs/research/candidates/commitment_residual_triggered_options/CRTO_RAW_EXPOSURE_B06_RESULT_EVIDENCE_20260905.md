# CRTO RAW exposure B06 technical evidence

Scientific object **CRTO-RAW-EXPOSURE-B06**, B/EXPLORE. CM owns this technical
record; DM independently reconstructs the paired observations and scientific reading.

## Accepted implementation

Frozen science card and owner items were pushed at
`716aec8d513baa728c17d182aaaee23bd221bcff` before implementation. Source
`7cad2758a156ebde0bd150b24ecee70bcc68982a` was committed and pushed before remote
preparation. Only new raw_exposure_b06 experiment/test directories and
scripts/run_crto_raw_exposure_b06.py were added. All historical source remains unchanged.

The adapter reuses B04 train_path unchanged, with its effective1200-second
training-plus-evaluation arm cap and1500-second invocation cap. Each seed1/2 has
one fresh CPU FP32 trajectory to516, snapshots258/516, original canonical batch32,
Adam and explicit RNG namespaces. The import chain sets thread environment before
NumPy/PyTorch and one intra/inter-op thread. Both trajectories finish before
their ordinary endpoint readouts. There is no checkpoint I/O, cycle mean or paired
TRAIN-order intervention.

Preparation keeps B04 predictor tapes replicate0 and fitting replicate=seed,
100 updates/12800 examples, then B01 selected rows. Calibration is omitted.
Independent review confirmed calibration forecasts run eval/no_grad with local
hidden tensors and no optimizer, persistent hidden state or RNG mutation.
The accepted RAW builder uses the same target/mean/Cholesky as the B04 RAW view.
The omitted table never enters RAW. This is not an intervention on RAW information.

B02 label/forward/score/publication helpers retain full finite signed native G16,
legal predictions, first-printed ties and nonnegative regret. New paired reading
reports D=R258-R516, competence at both endpoints, every changed action and its
paired regret difference. New B06 MEI.000625 and first-match branches follow the
card; historical residual MEI.0025/rules are unchanged. Historical258 comparison
is external and descriptive, with no hardcoded metric/initialization gate.

## Scope and checks

Engineering-scope section4 additions: **none**. Final code:176 physical research
lines (144 module,31 runner,1 initializer); tests113 lines. Independent review
counts51/176=28.98% substantive orchestration (25 module,25 runner,1 initializer).
No padding, copied training loop, wrapper machinery or historical-source edit.

Implementer focused suite passed11 checks in5.70 seconds, including one toy
publication smoke. Toy wall2.162096999993082 seconds; missing local peak RSS was
explicitly resources_unmeasured. The toy has no scientific branch. The full-size
offline synthetic fixture publishes two16-row readouts,48 recipient keys at172/344,
8256/16512 examples and a changed-action contribution exactly reconstructing D.
Tests cover strict MEI boundaries, first-match precedence, aggregate partial/weak/
cost behavior and model-free projection. Independent reviewer inspected source,
tests and both publication artifacts and found no material issue. No learner
smoke or focused suite was repeated; no new historical A01 acceptance is implied.

Local test evidence is under
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/test/b06-implementation-20260905/`,
in test_one_toy_smoke_shared_path0/summary.json and
test_full_panel_changed_action0/summary.json.

## Cost, placement and exact calls

Both non-result --project-cost outputs ran on exact committed remote source and
printed3*(P+u*t_s+E_s), P125.72588114999235. Seed1 t=.0600742854535207,
E=.008204734011087567; seed2 t=.057716591918605016,E=.012151057992014103.
Actual invocation forecasts at516 are470.19725153406034/466.55938091395365 seconds,
each below1200 arm and1500 invocation limits. Total projected machine time
936.756632448014 seconds. The258/516 forecasts are not added within one trajectory.
Historical B05 initial scales/movement are explicitly prior measurements in the
planning output; actual B06 scales and movement are separate observations.

Node wsl_4070, SSH hmasd-wsl-node, interpreter /home/wu/.venvs/hmasd/bin/python.
For s=1/2, cwd /home/wu/hmasd-worktrees/crto-b06-s<s>-7cad2758, task
crto_raw_exposure_b06_s<s>_7cad2758_01, root
temp/directions/commitment_residual_triggered_options/exp/raw_exposure_b06_20260905/seed0<s>/attempt01,
receipt sibling attempt01_admission.json. Exact expanded runner argv is in each summary:

```sh
python -X faulthandler scripts/run_crto_raw_exposure_b06.py --seed <s> --execution-node wsl_4070 --output-dir <root>
```

Each saved supervisor runner.sh joins cd, actual-node fresh admit-memory --out
receipt and the above runner with &&. Expected RSS<2GiB and both available-memory
floors>=4GiB apply separately. Stop is complete summary or first declared failure;
no retry, resume, seed cancellation or parameter change was authorized or performed.
Shared tracker /root/tracker_tl_experiments acknowledged both unique handles and
owns routine observations; CM retains collection/acceptance, DM scientific intake.

One non-experiment preparation command reached a promisor Git fetch in a non-login
shell and stalled before tests or learner creation. Process inspection identified
git-remote-https; it was terminated and the same checkout retried through configured
zsh -lic, which succeeded. The pending repeated remote checks never ran and were
dropped per DM instruction. Both remote project-cost outputs exercised the new
runner import. Shell gitstatus/background-gc warnings did not prevent checkout.

## Terminal collection and technical acceptance

Both accepted tasks finished with exit0, tmux inactive according to tracker. CM collected
the original summaries, admissions and supervisor witnesses and technically accepts both
invocations. No result-bearing retry or post-result source change occurred.

| Observation | Seed1 | Seed2 |
| --- | --- | --- |
| Admission UTC | 2026-09-05T09:55:42.094386Z | 2026-09-05T09:56:06.422556Z |
| Physical/effective available bytes | 12925317120 | 13159759872 |
| Both >=4GiB floors | passed | passed |
| Supervisor start/end UTC | 09:55:42 /09:57:19 | 09:56:06 /09:57:38 |
| Exit /full duration seconds | 0 /97 | 0 /92 |
| Runner pre-publication wall seconds | 89.3549929009896 | 84.66593478999857 |
| Peak RSS bytes, measured | 1274687488 | 1277034496 |

Both full invocation times are below1500 seconds; training+forward+scoring is below1200
per arm. RSS is below the prospective2GiB expectation. Total supervisor machine time189
seconds includes startup/publication; runner timing does not. Later observation age is not
execution duration. No requested formal resource measurement is missing.

| Stage | Seed1 seconds | Seed2 seconds |
| --- | --- | --- |
| measured_preparation_seconds | 62.425374370999634 | 60.344383468996966 |
| measured_training_seconds | 26.919383424989064 | 24.311875275991042 |
| measured_seconds_per_update | 0.05216934772284702 | 0.047116037356571785 |
| measured_forward_seconds | 0.006209012994077057 | 0.006263385992497206 |
| measured_scoring_seconds | 0.0011958249961026013 | 0.0010504610108910128 |

Per seed actual predictor128 tapes/32256 examples/100 updates/12800 processed examples;
gate516 updates/16512 examples,32 forward/scored rows and16 unique EVAL members. Environment
transitions38464=128*256+5696 selected history steps; common-future branch steps3520.
Calibration tapes/examples and derangement packets are zero. Across both:1032 gate updates,
33024 processed examples,64 decisions over the same16 member identities.

| Seed | Initial L2 | Initial RMS | Initial Linf |
| --- | --- | --- | --- |
| 1 | 18.92643228704128 | 0.10428775735716496 | 0.287416011095047 |
| 2 | 18.844772502567565 | 0.10383779850280324 | 0.2884293794631958 |

| Seed | Update | Processed examples | Each recipient count | L2 movement ratio | Linf movement ratio |
| --- | --- | --- | --- | --- | --- |
| 1 | 258 | 8256 | 172 | 0.15185621905905447 | 1.1030603123304337 |
| 1 | 516 | 16512 | 344 | 0.2442592158905306 | 1.922981775039011 |
| 2 | 258 | 8256 | 172 | 0.1765496051797392 | 0.9841327580955074 |
| 2 | 516 | 16512 | 344 | 0.2792536742091679 | 2.055482417800879 |

All48 recipient keys have172/344 visits, no donor exposure. All four actual movement
lines are finite positive; batch32, lr.001, nominal exposure.258/.516 and cursor/phase0
are recorded. Each seed has one shared initialization across both snapshots.

Read-only technical arithmetic checked all64 legal prediction/native-label/action/regret
rows, first-printed maxima, finite values and nonnegative regret; canonical TRAIN order and
all native EVAL labels against B05; complete64 source metadata entries; exact argv/SHA/seed/
thread contract; actual counts/exposures and caps. Changed-action records exactly reconstruct
the changed row pairs and D is R258-R516. All checks passed.
Side means/exact counts, competence and emitted per-seed rule also reconstruct
directly from the rows. Both remote source worktrees remain clean at7cad2758a.
Root owner reviews returned [] at prelaunch and terminal boundaries; current
compute configuration remains remote_first/wsl_4070. No override was bypassed.

Descriptive historical258 comparison: both seeds have prediction max absolute difference
0.0 against B05 RAW-LONG, and every full readout row, initial scale and258 movement ratio
equals its earlier observation. This was measured after collection, not a launch/validity
predicate or a general bit-identity claim. Primary observations remain within each new path.

The original per-seed branches and all measurements remain in the full JSON. DM received
both originals before E0 completion for independent rule reconstruction. The only runtime
warning is the historical shared models.py:186 non-writable NumPy warning; no exception or
fault stack is present. This does not classify or repair historical A01.

Original summary bytes are retained as CRTO_RAW_EXPOSURE_B06_SEED01_RESULT_20260905.json
and CRTO_RAW_EXPOSURE_B06_SEED02_RESULT_20260905.json beside this E0. Local roots:
C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/raw_exposure_b06_20260905/
seed01/attempt01_artifacts/ and seed02/attempt01_artifacts/. Each contains summary.json,
attempt01_admission.json, runner.sh, task.log, status, exit_code, start_time and pid.
Remote evidence is preserved; no B06 run remains live.

Limit: technical conformance does not establish stable competence, residual value, seed-component
causality or independent-population performance on this exposed selected panel. DM owns
the scientific first-match reading and any later card.
