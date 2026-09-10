# RCLE fresh1000 S22 result evidence — 2026-09-10

**INCOMPLETE PAIRED OBJECT.** W1 completed; W100 stopped with an ordinary Python
exception after983 recorded blocks; the reference was not invoked. No seed22 W100
endpoint, paired effect or replication verdict is available. Intact W1 measurements
and completed-block records are preserved at their narrower scope.

- Card: [S22 science card](RCLE_B03_FRESH1000_S22_SCIENCE_CARD_20260910.md), freeze
  `d09667fcc`; source **`9a11fb084a16f293c27f3bd1fe8275dc19bd1a47`**.
- [Execution and prospective logging repair](RCLE_B03_FRESH1000_S22_EXECUTION_20260910.md).
- [Machine readback](RCLE_B03_FRESH1000_S22_RESULT_SUMMARY_20260910.json) contains
  all19 output/supervisor hashes, admissions, counts, arm metadata, recomputed W1
  measurements, source facts and missing-output flags.
- [Present scenario rows](b03_fresh1000_s22_20260910/SCENARIOS.csv),
  [all recorded curves](b03_fresh1000_s22_20260910/CURVES.json),
  [one-arm run summary](b03_fresh1000_s22_20260910/W1_RUN_SUMMARY.json).

## 1. Rule applied verbatim

Card §4 condition: **“Damaged training, information or primary”**.

Reading: **“Report failure/counts and only intact narrower facts; no algorithmic polarity.”**

W100 has no final evaluation or saved final parameter state; reference is absent.
The eight other result rows require an unavailable paired effect or W100 endpoint and
cannot be scored by replacing it with a training curve. The intended comparison is
incomplete, not zero or negative. A/B has no consumption state. Earlier complete and
quarantined artifacts keep their original meanings.

## 2. Direct terminal observations and diagnostic limits

Handle `rcle-b03-fresh1000-s22-20260910`, wsl_4070, CPU FP64/one compute thread.
Monitor observed termination at2026-09-10T19:23:21.5306913Z: exit2, PID3095314,
tmux inactive. Supervisor reports start2026-09-11T03:12:25+08:00 and
exit2026-09-11T03:23:09+08:00, duration644s. The latter is19:23:09Z.
Direct terminal collection independently read the same failed supervisor state.

W100 summary records exactly:

```text
TypeError: unsupported operand type(s) for *: 'range_iterator' and 'int'
```

The source catches `Exception`, records type/message and returns TECHNICAL_STOP;
the CLI then returns2. The fixed wrapper correctly stops before reference. This was
not a600s arm timeout,1250s outer timeout or failed memory admission.

The handler at frozen B03 `study.py:175` retained no exception traceback. The combined
log has admissions, COMPLETE W1, TECHNICAL_STOP W100 and supervisor exit, with no
originating Python frame. Fatal-stack capture does not recover a caught ordinary
exception's stack. No concrete learner/native cause is established. The message does
not establish a range construction bug, memory corruption, a ctypes lifetime defect,
a seed22-specific defect, or identity with the old signal11 failure.

Independent Astra/high Reviewer checked this failure path and the count boundary,
read-only without a scientific/test invocation. Its conclusion was: **“The failure
is established; its cause is not.”** It identified traceback loss as the concrete
diagnostic omission, not an explanation of the failing multiplication.

## 3. Artifact and implementation readback

All13 present run-root files and6 supervisor files match the remote hashes. The
Monitor terminal text was copied without byte normalization; SHA256
`4fad7c8788be4def361ef70a4d19caa17d54dcf06e6b2f3de859c182992e784e`.
Local raw root is `temp/directions/roster_consistent_latent_exploration/exp/b03-actor100-fresh1000-s22-20260910`;
collection receipts are in `fresh1000-s22-preparation/` beside the prior launch records.
Remote source/dependency/preflight bytes matched9a11fb084 at collection.

Both arms use master22 root
`9e02ca6eed367ce80c7b396fc99a128c501c744d0e888e374803b5b2a4feb9fa`, block digest
`17d27675aa05de9ca420bfd915292995dc29ed28ef9407c678cd294507a7fad3` and the original
FLEX-REKEY RNG namespace/consumers. Actual initial state dictionaries contain26,161
finite FP64 scalars, identical within the pair;25,440 components differ from retained
S21. Initial norm is21.20666078552823. Retained S21 initial-file hash was checked.

W1 has all1,000 curves at indices0–999; W100 has983 at0–982. Each summary curve equals
its corresponding completed_blocks.jsonl record. All contain64 episodes/4096 ticks,
8 cells×8 episodes, finite loss/metrics/gradient norm, nonzero step and parameter-update
then baseline-update order. Maximum recorded step-norm deviation from.02 is1.04e-17
for both; recorded path lengths are20.00 and19.66. These are path lengths, not net change.
W1 final tensors are finite FP64 and give displacement.7281851118; its final baselines
match reconstruction from zero (maximum difference3.33e-16). W100 has no final tensor
or final-baseline record, so neither final displacement nor its actual terminal baseline
is asserted. Reconstruction through the last recorded block is retained as such.

The two present panels—common initialization and W1 final—each contain8 cells×256
unique scenario indices, with all U/Y/tau/F means independently recomputed. W100 has
zero final rows and no partial evaluation rows; no reference directory/admission exists.
Readback loaded stored state dictionaries only, without a model/native/RNG/learner call.

## 4. Exposure: recorded work and bounded missing work

| Quantity | W1 | W100 | Total recorded |
| --- | ---: | ---: | ---: |
| Completed training blocks / backward calls | 1,000 | 983 | 1,983 |
| Completed training episodes | 64,000 | 62,912 | 126,912 |
| Initialization/final evaluation episodes | 4,096 | 0 | 4,096 |
| Total episodes | 68,096 | 62,912 | **131,008** |
| Primitive ticks | 4,358,144 | 4,026,368 | **8,384,512** |
| Recorded nonzero / zero steps | 1,000 / 0 | 983 / 0 | 1,983 / 0 |

The training function can execute episodes/backward/update before returning its curve;
the caller records the returned curve afterward. Therefore the recorded counts are
lower bounds on total execution. Under this loop, at most one additional interrupted
block can be missing:0–64 episodes,0–4096 primitive ticks and0–1 backward/step call.
No exact within-block progress or missing zero/nonzero count is inferred. New-attempt
upper bounds are131,072 episodes/8,388,608 ticks/1,984 calls. This is not a983-update
checkpoint selected for evaluation or a claim that all missing work occurred.

There were12 model allocations:2 fits started and10 untrained helpers. Recorded training
agent ticks/claim decisions are32,768,000/8,192,000 for W1 and32,210,944/8,052,736 for W100.
Known B03 cumulative lower totals are334,784 episodes/21,426,176 ticks/4,783 calls/54 models,
plus this new bounded interrupted block and the separate old unknown W100 prefix upper
12,800 episodes/819,200 ticks/200 calls. Historical upper bounds are not observed counts.

## 5. Intact W1 measurement and the missing comparison

| ACTIVE_CONTINUATION path | Initialization U | W1 final U | W1 gain from initialization |
| --- | ---: | ---: | ---: |
| 8→12 | .6917887370 | .6884521484 | +.0033365885 |
| 12→8 | .7194702148 | .7148925781 | +.0045776367 |
| Equal primary mean | **.7056294759** | **.7016723633** | **+.0039571126** |

W1 gain has conditional paired-scenario SE.0009328018 and approximate interval
[.0021288212,.0057854041]. It is below MEI.05 and represents.15828 normalized unmet-demand
ticks over40. Primary Y rises from.2965749105 to.3000793457; primary F falls from.2966389974
to.2903889974. Every initialization and W1 final scenario has tau40. These are one-arm,
single-training-instance observations, not a W100 contrast or robust learning claim.

Recorded W100 training U falls from first-block.70850 to last recorded-block.36493
(index982), with training Y.29364→.62660. The full curves and all windows are retained.
Those are changing-policy observations on training rosters, not the fixed final held-out
observable. They cannot fill missing Delta_U, W100 G_U or reference values or score a
replication success. S21 remains the sole complete same1000 paired result.

## 6. Resource, timing and scope evidence

W1 admission at19:12:25.049409Z measured physical/effective availability15,633,362,944B;
W100 at19:17:58.264040Z measured15,617,634,304B. Both passed the4GiB floor immediately
before their invocations. No reference admission was taken.

GNU complete-process walls: W1333.18s, W100310.74s; sum643.92s. Whole sequence644.00s
is charged once, including admissions and process overhead, not added to that sum.
Complete-process peak RSS597300KiB and592388KiB, respectively. Interpreter-only times
317.2263/305.7210s are retained separately and do not replace complete-process charge.

Conservative complete charge **894.00s =100s prelaunch support +644s sequence +150s
postlaunch support**, within1500. The two support amounts are conservative full charges,
not assertions of exact measured use. They include packaging failure/repair, all checks,
collection, traceback-reporting repair, publication and scoped preservation/closeout.
Actual recorded collection5.6936399s and readback including imports2.1827749s remain in
their receipts. Aggregate CPU and complete calendar critical path are unmeasured.
No arm/sequence/source/runner/test budget breach was observed. Cumulative focused-test
wall is44.1164295/300s after the prospectively limited diagnostic-reporting check.

The explicitly named same1000 window now charges S21997.01s plus this incomplete
attempt894.00s =**1891.01s for one complete paired result**. This attempt adds zero to
that denominator; the valid narrower W1 observation does not manufacture a paired result.
This is a named window, not the direction's unmeasured full-history cost.

## Verified preservation before remote removal

The exact execution checkout (excluding only its Git pointer), supervisor and source-only
stage were archived before removal. Remote `tar -d` comparison against all original
archived members passed; PID3095314 was absent and supervisor state was terminal exit2.
The archive contains **2355 regular members**, **11549691 bytes**, SHA256
`023d847fe1a2665ebf9788b13ead873a6d106ad2b144156860fa4a44eef9a885`. Local transfer hash matches; all19 accepted
output/supervisor members and both original/corrected source bundles match their retained
bytes. `members.json` SHA256 is `02d6c1c5455ec3eba927e9f3b9db90c4a3968fa23aa4e48b7a64d02a7b533ab5`.

Remote archive: `/home/wu/hmasd-recovery/rcle-b03-fresh1000-s22-20260910/remote.tar.gz`.
Local archive: `temp/directions/roster_consistent_latent_exploration/closeout/b03-fresh1000-s22-20260910/remote.tar.gz`.
Recovery ref `refs/recovery/rcle-b03-fresh1000-s22-20260910` preserves source9a11fb084.
Preservation/transfer5.393398699990939s and member verification0.43075230000249576s count
inside the same150s postlaunch support charge. No scientific evidence was discarded,
no new learner invoked, and historical/native-cache/shared-authoring paths are outside
the cleanup inventory. Final removal facts will be appended after result publication.
