# UCOPE native-return acquisition B01 technical acceptance

Accepted source: `a0b00f561159ddeedf66b65711cf3f7d2ec93b04`, branch
`codex/cm-ucope-native-return-b01-20260907`, based on frozen card commit
`3520ccd2ce90e8aca3c7bec8e838e403d00068db`. This is engineering acceptance of
[card §§1–6](UCOPE_NATIVE_RETURN_ACQUISITION_B01_SCIENCE_CARD_20260907.md), not a B result.
Formal seeds 6301 and 6302 have not been run by this assignment.

## Delivered source and boundaries

- `experiments/candidates/ucope/native_return_acquisition_b01/learner.py`: fresh 468-parameter
  CPU FP32 actor, dedicated initialization/root/tail generators, real-host collector, one joint
  Adam update per 256 episodes, detached within-context leave-one-out return advantage.
- `evaluation.py`: final modal policy, matched host ancestry/index for IMMEDIATE-4, Python-float
  moments and conditional Monte Carlo SE, context outputs, counters and two-seed `reading_rule`.
- `scripts/run_ucope_native_return_acquisition_b01.py`: fixed science/technical profiles,
  training JSONL, final parameter serialization, exposure and complete/partial summary publication.
- `tests/experiments/candidates/ucope/native_return_acquisition_b01/test_native_return.py`:
  focused synthetic cases and readback of the single admitted real smoke artifact.

Actor state and optimizer live for one seed/process. Root inputs are public context; the tail
network takes the context one-hot and displayed count/6. Its 8x7 table batches policy calculations
only; the host callback selects the row after the display exists. Host reward is consumed only
after the callback returns. No actual mark, paid component, posterior or oracle target enters the
tail input. Only visited log terms contribute to the all-256-row loss. Every row consumes one root
and one tail Torch uniform, including unused tail uniforms. Each update gets fresh episodes in
context order; evaluation uses the separate eval namespaces and freezes the final modal actions.
There is no replay, recurrence, retained policy, resume or intermediate-checkpoint selection.

Git comparison of the four reused conditioning-discriminator modules against source binding
`f095d53732705b4db00156f57d61976c979fd61a` is empty. No old object or core file changed.
Scope §4 additions: **none**, as card §5 requires. New non-test source: **295 lines**, including
the **111-line runner**; tests:196 lines. Source, runner and focused-test budgets are satisfied.

## Focused checks and independent review

Local Python `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` ran the synthetic suite:

```text
python -m pytest -q -p no:cacheprovider tests/experiments/candidates/ucope/native_return_acquisition_b01 -k 'not real_technical_smoke' --basetemp temp/directions/ucope/test/native-return-b01-unit
```

Ten cases passed in3.58s. The partial-summary case initially had a pytest setup error because
the new scratch parent did not exist; after creating that directory, that case alone passed
in2.12s. No scientific execution occurred in this setup failure or repair. Tests cover dedicated
Xavier initialization without global draws; categorical equality/remainder; detached advantage
and denominator; selected-action gradients; full action-stream consumption and ancestry;
SEVERED callback-before-actual-mark order; native paid/immediate reward/counters; modal ties;
paired addresses, float64 means/SE; NR-A/B/C thresholds and incomplete result handling; and
zero-exposure initialization-failure summary publication. Pytest reports its existing unknown
`cache_dir` warning when cacheprovider is disabled.

Independent native Reviewer `review_ah_ucope_b01` inspected affected source and the frozen card,
then independently checked synthetic collection/evaluation with no real host samples or optimizer
steps. It found **no material defect**. Its explicit per-row reference gradient comparison had
maximum absolute difference2.39e-9; it also checked interrupted-evaluation counts/serialization.
The review confirmed no §4 machinery and unchanged bound modules. Its remaining runtime boundary
is supplied by the single real smoke below. Its wall-accounting observation is preserved below.

## One real technical profile and artifacts

Node `wsl_4070` (`LAPTOP-U9TDKC8A`), exact-sha detached worktree:
`/home/wu/hmasd-worktrees/cm-ucope-native-return-b01-20260907`.
Python3.10.21, Torch2.7.0+cu118 running **CPU FP32**, one scientific process,
Torch intra-op/inter-op threads both1. No GPU/native team or configuration sweep.

Frozen invocation was seed9006301, profile`technical`:2 updates and16 evaluation episodes/context/policy,
stop at completion or60s. The supervisor's accepted command was:

```bash
/usr/local/bin/agent-task run ucope-native-return-b01-technical-9006301-launchfix 'cd /home/wu/hmasd-worktrees/cm-ucope-native-return-b01-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/native-return-b01-technical-9006301/resource_admission.json && /usr/bin/time -f %e,%M,%U,%S -o temp/directions/ucope/exp/native-return-b01-technical-9006301/process_time.csv /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_native_return_acquisition_b01.py --seed 9006301 --profile technical --out temp/directions/ucope/exp/native-return-b01-technical-9006301'
```

The first launcher handle `ucope-native-return-b01-technical-9006301` exited2 before admission or
learner execution: passing `bash -lc` through the supervisor's string-joined command lost the cwd
grouping and Python looked for `/home/wu/scripts/hmasd_resource_preflight.py`. Inspection of the
existing supervisor established the quoting cause; its native command string repaired this
pre-learner failure. The accepted learner argv above executed **once**. Both supervisor records
remain under `/home/wu/.agent-tasks/`; no result-bearing retry or new profile occurred.

Fresh admission at2026-09-07T07:23:36.738Z passed with physical and effective available memory
15,655,030,784bytes, above the4GiB floor. Handle`ucope-native-return-b01-technical-9006301-launchfix`
reached terminal`finished`, exit0, on2026-09-07T07:23:39Z. Runner status`TECHNICAL_COMPLETE`.

Outputs reside at `temp/directions/ucope/exp/native-return-b01-technical-9006301/` under that remote
worktree and are copied to the same relative path under
`C:/Projects/HMASD-worktrees/cm-ucope-native-return-b01-20260907/`:
`summary.json`, `training.jsonl`, `final_parameters.pt`, `resource_admission.json`, `process_time.csv`.
Summary readback and the468-parameter state load passed remotely in0.79s:

```bash
UCOPE_TECHNICAL_OUTPUT=temp/directions/ucope/exp/native-return-b01-technical-9006301 /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider tests/experiments/candidates/ucope/native_return_acquisition_b01/test_native_return.py::test_real_technical_smoke --basetemp temp/directions/ucope/test/native-return-b01-smoke-readback
```

This reads existing outputs and never repeats the learner. Publication coverage is the actual
learner→final state→paired evaluation→summary→JSON/state readback path; synthetic failure checks
cover partial publication. No historical publisher or replay path is inherited.

| Technical exposure | Training | Actor evaluation | Reference evaluation | Total |
| --- | ---: | ---: | ---: | ---: |
| Episodes |512|128|128|768|
| Host-event transitions |2548|352|256|3156|
| Probe episodes |254|16|0|270|
| Committed period units |2200|480|512|3192|
| Probe time units |508|32|0|540|

Joint optimizer steps2; tail-active batches2. Root initialL2=0, displacementL2=0.01975463517,
maximum absolute movement=0.005997684784. Tail initialL2=4.700405121,
displacementL2=0.09943917394, displacement/initialL2=0.02115544754,
maximum absolute movement=0.006004042923. These are technical exposure facts, not evidence of
scientific improvement or competence. The formal batch remains `INCOMPLETE`; no NR branch assigned.

## Cost evidence and remaining ownership

External whole-process `/usr/bin/time`: **2.66s wall**, **506256KiB peak RSS**,1.70s user plus1.82s
system CPU (**3.52 aggregate CPU-s**). This includes interpreter startup and final publication/exit;
the supervisor records3s rounded elapsed including admission. No CPU ceiling is asserted.
The summary conservatively retains `resources_unmeasured` because it does not ingest external RSS;
the actual measurement above is in`process_time.csv`.

The internal2.244269494s includes imports, initialization, learner, evaluation, exposure and first
summary write. The final measurement-refresh write is excluded from that internal number, as the
reviewer noted; external2.66s covers it. Initialization2.140224569s; two batches0.097492272s;
128 evaluation pairs0.003590076s. Python computed the card's own cost-law projection from these
recorded timings, retaining all fixed measured remainder:

```text
fixed = 2.66 - 0.09749227200518362 - 0.003590075997635722 = 2.558917652 s
T_batch256 = 0.09749227200518362 / 2 = 0.04874613600 s
T_eval_pair = 0.003590075997635722 / 128 = 0.00002804746873 s
per seed = fixed + 1024*T_batch256 + 32768*T_eval_pair = 53.394020374 s
two-seed summed wall projection = 106.788040748 s
```

Per-seed logical invocation remains `python scripts/run_ucope_native_return_acquisition_b01.py
--seed 6301 --out <new-seed6301-root>` and the same with6302, each with its own adjacent destination
admission and600s cap. Each includes1024 learning batches,32768 paired evaluations, final state and
summary publication. Both required comparisons and all contexts are retained. This is a small-profile
planning estimate, not a runtime bound: probe frequencies and host load may differ, and larger JSONL
publication is extrapolated with batches. It is well below each600s cap; no fresh pilot is required.
If executed sequentially, study critical path is approximately summed wall plus intervening overhead;
concurrent critical path is unmeasured. Formal aggregate CPU work is unmeasured and is not obtained
by substituting wall time. No formal study cost was consumed here.

No implementation gap remains. DM owns scientific intake and any two-seed aggregation through
`reading_rule`; Root owns explicit-path integration and later remote invocation/observation.
This initial CM task authorizes neither formal seed launch nor further tuning/diagnostic exposure.
