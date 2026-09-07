# VSP03 B02 P10 — completed technical E0

The selected LF-delivered P10 attempt is **technically accepted as complete**. Collected
supervisor evidence records exit0 and5.05s whole wall, passing the120s cap. Fresh
destination admission passed. All frozen counts, six paired endpoint sets, curves,
weights, exposure, the sole in-run check and required readback are present and consistent.
This acceptance establishes execution conformance; DM owns the scientific intake.

Primary final update128 greedy **T−R = +0.001083984375**, conditional world
SD0.022572718968 / SE0.000705397468. T−R0 is zero; all1024 saved T-greedy and R0 records
are equal. Greedy T−G is−0.003994140625. Both stochastic learner-minus-R results are
negative and retained below. The independent unit is one paired training instance,
seed4; world SD/SE describes conditional evaluation variation, not training-population
uncertainty. No general policy identity, stable-superiority or causal claim follows.

## Bound execution and direct evidence

- Scientific source SHA: `00ebefa5823dbb41e64aed11b90ba26a8ff97020`, in existing detached
  cwd `/home/wu/hmasd-worktrees/vsp03-b02-p09-00ebefa5823dbb41e64aed11b90ba26a8ff97020`.
  Root directly verified that cwd SHA; collected summary records the same SHA.
- Node/interpreter: configured `wsl_4070`, `/home/wu/.venvs/hmasd/bin/python`; CPU float32,
  declared single compute thread. Scientific argv/RNG/seed/learner/comparators unchanged.
- Delivery artifact commit: `4e02c34bc4548f016d1d61ad16fc92430a25117c`; remote command
  `/home/wu/hmasd-inputs/vsp03-b02-p10-lf-20260907.sh`, as bound in the
  [LF repair handoff](VSP03_B02_P10_LF_REPAIR_HANDOFF_20260907.md).
- Root's actual supervisor command:
  `/usr/local/bin/agent-task run vsp03-b02-p10-lf-20260907 '/bin/bash /home/wu/hmasd-inputs/vsp03-b02-p10-lf-20260907.sh'`.
- Handle `vsp03-b02-p10-lf-20260907`; collected status `finished`, exit0, PID2745786.
  Root's terminal status reported tmux inactive; source/terminal publication is
  `a7a307db952e743f016754db4a4b1e26e3423515`. The later status uptime93s was observation
  age, not scientific runtime.
- Collected log starts `2026-09-08T04:48:14+08:00` (2026-09-07T20:48:14Z) and ends
  `04:48:19+08:00`, duration5s. Its finer outer `/usr/bin/time` observation is5.05s.
  The timeout encloses timestamp/admission/imports/check/learning/all evaluations/
  publication/readback/runner exit; no stage clock resets. Supervisor bookkeeping is
  distinct from that complete scientific invocation boundary.
- [Admission](b02_p10_result_20260907/admission.json) captured
  `2026-09-07T20:48:14.626522Z`, assessed `20:48:14.626844Z`; physical/effective available
  **15664111616 /15664111616 bytes**, above4294967296. Source `/proc/meminfo`; both
  floors passed with no failure reasons. It admits this adjacent P10 runner only.

Compact originals are [summary](b02_p10_result_20260907/summary.json),
[supervisor log](b02_p10_result_20260907/supervisor.log) and
[supervisor runner](b02_p10_result_20260907/supervisor_runner.sh).
The runner records execution of the selected command file; its log and status/exit files
agree. The summary's command ends `--node wsl_4070`, without the prior trailing CR.

## Complete exposure and readback

| Measurement | Observed |
| --- | ---: |
| Models / independent training pairs | 2 /1 |
| Complete joint episodes | 38920 |
| Team ticks / target transitions | 1556800 /3113600 |
| Optimizer steps | 256 |
| T training episodes / steps / valid-gradient rows | 16384 /128 /90504 |
| G training episodes / steps / valid-gradient rows | 16384 /128 /58610 |
| Curve rows per arm / evaluation episodes per arm | 128 /2048 |
| R worlds / R0 worlds | 1024 /1024 |
| In-run check episodes / ticks / transitions / steps | 8 /320 /640 /0 |
| In-run check valid-gradient rows / backward calls | 44 /1 |
| All rollout decision rows / rollout policy forwards | 187200 /4295 |

The saved check's eight expected integer job-unit pairs match the frozen fixture facts;
its rule observations are tie-submit true, R yield false-action and R0 submit true-action.
The successful original call exercised release/exclusion, service failure timing,
blocked-final clocks, forced-wait latches and decision-prefix assertions. Collection read
those saved outputs only; it did not execute the fixture again. Check gradients were
cleared with zero optimizer steps before normal learning.

Both final state files contain11 finite float32 tensors totaling2083 parameters,
1570 actor/direct plus513 critic. Loading their saved tensors for inspection constructed
no model and performed no forward/optimizer operation. Their actor/critic/total norms
match final summary exposure. Both in-run weight readbacks are true. Initial and
first/final exposure is retained in full in the summary:

| Arm | Initial total L2 | First-step total displacement | Final total displacement | Final displacement / initial L2 |
| --- | ---: | ---: | ---: | ---: |
| T | 6.3732247353 | 0.02338799648 | 3.1672637463 | 0.4969640767 |
| G | 5.8807516098 | 0.02338798530 | 2.2199153900 | 0.3774883786 |

Each arm has exactly128 ordered curve entries,128 complete episodes per entry. Summed
curve valid/gradient rows equal the arm counters. Adding those rows, all six endpoint
eligible counts and the44 fixture rows gives187200. No forced-wait padding was added
to equalize the arms. First/last batch returns are retained as training observations,
not held-out checkpoints or independent seeds.

## All selected observations

Absolute mean joint returns on the same1024 exogenous worlds and phase assignments:

| Execution | Mean return |
| --- | ---: |
| T greedy | 0.350673828125 |
| T stochastic | 0.3388134765625 |
| G greedy | 0.354667968750 |
| G stochastic | 0.2890380859375 |
| R | 0.349589843750 |
| R0 | 0.350673828125 |

Every selected paired-world contrast, recomputed from persisted endpoint rows and checked
against both `paired_differences.json` and the summary:

| Contrast | Mean | Conditional world SD | Conditional world SE |
| --- | ---: | ---: | ---: |
| T greedy−R (primary) | +0.001083984375 | 0.022572718968 | 0.000705397468 |
| T greedy−G greedy | −0.003994140625 | 0.137321158784 | 0.004291286212 |
| G greedy−R | +0.005078125000 | 0.139168890939 | 0.004349027842 |
| T greedy−R0 | 0 | 0 | 0 |
| G greedy−R0 | +0.003994140625 | 0.137321158784 | 0.004291286212 |
| T stochastic−R | −0.010776367188 | 0.251636205367 | 0.007863631418 |
| T stochastic−R0 | −0.011860351563 | 0.251484315084 | 0.007858884846 |
| T stochastic−T greedy | −0.011860351563 | 0.251484315084 | 0.007858884846 |
| G stochastic−R | −0.060551757812 | 0.352689378781 | 0.011021543087 |
| G stochastic−R0 | −0.061635742187 | 0.353771793738 | 0.011055368554 |
| G stochastic−G greedy | −0.065629882812 | 0.358912047711 | 0.011216001491 |

Native totals across2048 jobs per execution, without treating jobs as independent seeds:

| Execution | Success | Attempt | Failed attempt | Non-submission | Waiting ticks | Blocked pending / final |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T greedy | 970 | 1863 | 893 | 185 | 31734 | 2041 /11 |
| T stochastic | 940 | 1973 | 1033 | 75 | 29492 | 2041 /11 |
| G greedy | 964 | 2019 | 1055 | 29 | 27338 | 2047 /10 |
| G stochastic | 786 | 2037 | 1251 | 11 | 18440 | 2048 /0 |
| R | 968 | 1862 | 894 | 186 | 31788 | 2041 /11 |
| R0 | 970 | 1863 | 893 | 185 | 31734 | 2041 /11 |

Each execution has17408 fixed calendar clocks. Pending/eligible/blocked counts and all
job-level integer outcomes are retained in the raw endpoints and compact analysis.
Blocked opportunities are observations, not counterfactual scheduling errors. The card's
MEI0.02, prediction and reading branches remain for DM intake; no outcome selects a new
primary, evaluator, comparator or extra attempt.

## Physical collection and focused acceptance

CM copied the terminal output directory, admission sibling and entire supervisor folder
using three configured SCP calls, all exit0. Full originals remain remotely and locally:

- Local output: `C:/Projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907`.
- Local admission: `C:/Projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907_admission.json`.
- Local supervisor: `C:/Projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907_supervisor/`.
- Remote output: `/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907`;
  receipt is sibling `b02_seed4_p10_lf_20260907_admission.json`.
- Remote supervisor: `/home/wu/.agent-tasks/vsp03-b02-p10-lf-20260907/`.

All13 required output files are present: summary, focused check, two curves, two weights,
six endpoints and paired differences. Supervisor files include task.log, runner.sh,
status, exit_code, pid and start_time. [Collection analysis](b02_p10_result_20260907/collection_analysis.json)
records file sizes, native totals, all recomputed contrasts and focused acceptance facts.

One local persisted-output analysis command exited0 in4.6861168s:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe C:/Projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907_acceptance.py
```

It checked1024 sequential world IDs and matching phase labels across all six endpoints;
integer job utility and joint-return accounting; legal calendar submission times and
non-overlapping services; clock-count identities; per-world contrast persistence and
sample SD/ddof1 with SE/32; full curve/count reconciliation; saved check facts; finite
float32 weight tensors and final norms; and admission/status/exit consistency. It used
only saved data and constructed no RNG stream, model, environment or optimizer.
Original local helper tests/source review were reused, not repeated. This analysis
establishes consistency of the collected evidence; it is not an independent learner replay.

## Cost, limitations and return

Complete repaired invocation wall is5.05s, including fresh admission and through exit.
Internal elapsed through JSON readback is4.7584404300s and exit-ready4.7598259360s;
these narrower readings do not replace the outer wall. Peak RSS from outer time is
514736KiB; the runner's own peak is495247360 bytes. Neither is a sampled aggregate
simultaneous-process memory measurement. Actual admission supplies the required memory
fact. CPU work is unmeasured; no thread census, CPU estimate or new profiling is claimed.

The runner's arm timers are T2.4270010200s and G1.4709916990s. T includes the in-run check;
these are measured stage spans, not separate complete invocation caps or an allocation
of shared costs. One repaired serial invocation has equal5.05s critical path and summed
invocation wall. The historical conditional23.62029694s whole-pair anchor was planning
evidence, not a measured N2/per-arm cost. The prior P09 pre-learner exit2 cost1.59s is
retained separately; their observed outer walls sum6.64s, which is not continuous
elapsed across the intervening repair. Git/transport/collection time is outside those
scientific-command walls and is not assigned zero cost.

No missing or damaged primary/count/weight dependency was found. Scientific limitations
remain the one-seed, synthetic-host, same-information B/EXPLORE ceiling and conditional
evaluation uncertainty. Summary float32/single-thread declarations are supported by
the accepted source path; no cross-platform bit-equality claim is made. Final greedy T/R0
equality is specifically equality of the1024 collected records, not a universal policy proof.

P10 changed shell delivery and attempt storage only. Accepted P09 exit2 and earlier
PATH_UNAVAILABLE evidence remain unchanged. No admission, learning, fixture, additional
evaluation, retry, seed or child was invoked during collection. This CM returns technical
acceptance and exact new evidence paths to DM for all-outcome scientific intake and the
Chinese brief; Root integrates the named evidence commits. No further run is selected.
