# VSP03 B03 E0 result evidence

The sole seed5 G instance published its selected final endpoint and required counts and
weights. Greedy G minus R0 is **-0.013974609375000007**. This is readable single-instance
performance evidence; the supervisor numeric exit remains unavailable and is not called0.
DM owns scientific intake and the next decision. No additional invocation is selected.

## Binding and actual execution

[Card](VSP03_B03_SCIENCE_CARD_20260908.md) sections3–7,
[assignment](VSP03_B03_CM_ASSIGNMENT_20260908.md),
[source review](VSP03_B03_SOURCE_REVIEW_20260908.md), and
[launch body](VSP03_B03_LAUNCH_BOUNDARY_20260908.md).
Source SHA:4eb8a36b9184633f5e28eff999a99f2dbc948040, committed/pushed before execution.
DM source comparison intake:215849916. Node:wsl_4070, SSH:hmasd-wsl-node;
Python:/home/wu/.venvs/hmasd/bin/python; CPU float32, one compute thread, inherited
NumPy float64 worlds. Existing supervisor handle:vsp03-b03-p54-20260908,
PID2820202, tmux agent_vsp03-b03-p54-20260908.

Exact cwd:
`/home/wu/hmasd-worktrees/vsp03-b03-p54-4eb8a36b9184633f5e28eff999a99f2dbc948040`.
Result root:
`/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b03_seed5_p54_20260908`.
Receipt:that root plus `_admission.json`.
Log:`/home/wu/.agent-tasks/vsp03-b03-p54-20260908/task.log`.
The [actual generated supervisor wrapper](VSP03_B03_RESULT_ARTIFACTS_20260908/supervisor_runner.sh)
retains the exact command, including source cwd and one outer120s timeout. The command
matches the reviewed launch body with SOURCE_SHA resolved. Dispatch was accepted once,
exit0 from submission (not scientific-process exit). Root recorded this accepted handle
and observed its terminal facts before directing this CM to finish collection.

## Endpoint values

All four executions use the same1024 held-out world/phase entries. The independent
training unit is one G instance; worlds and execution modes are not training replicates.

| Endpoint | Native team-return mean |
| --- | ---: |
| G_greedy | 0.354721679688 |
| G_stochastic | 0.339628906250 |
| R0 | 0.368696289063 |
| R | 0.369497070313 |

| Contrast | Mean | Paired-world sample SD | Conditional-world SE |
| --- | ---: | ---: | ---: |
| G_greedy-R0 | -0.013974609375 | 0.233712072191 | 0.007303502256 |
| G_greedy-R | -0.014775390625 | 0.230615115963 | 0.007206722374 |
| G_stochastic-R0 | -0.029067382813 | 0.315309564642 | 0.009853423895 |
| G_stochastic-R | -0.029868164062 | 0.316407555465 | 0.009887736108 |
| G_stochastic-G_greedy | -0.015092773437 | 0.319897368969 | 0.009996792780 |

SD uses ddof1 and SE=SD/32. These are conditional evaluation variation, not uncertainty
across independent training. No mode, threshold, checkpoint or primary was changed.

## Counts, exposure and required output

One model with2083 parameters,128 real backwards and128 real Adam steps. Training:
16384 joint episodes,655360 team ticks,1310720 target transitions,64912 valid rows and
64912 gradient rows. Evaluation:four1024-episode executions,4096 total episodes;
total:20480 completed joint episodes,819200 team ticks,1638400 target transitions,
93244 decision rows and2142 rollout policy batch calls (excluding objective/critic work).
No T or old eight-world fixture, no extra validation model/episode/optimizer step.

Initial total parameter L2:5.832952976226807. First-step displacement:0.023387718945741653,
relative0.004009584689103836. Final displacement:2.9511311054229736,
relative0.5059411789278623. This is actual movement, not proof of value.

The normal run read back all endpoint JSON, final weights, primary and counts. Collection
read the recorded bytes without constructing any model or simulating any episode:
four1024-row endpoint files preserve world/phase, job utilities/outcomes/waits/submission
times and fixed/pending/eligible/blocked/final-clock counts; curve updates are1..128;
curve/endpoint count sums match the recorded totals. Primary calculated from saved rows
matches the published primary and per-world contrasts. The saved state has2083 finite
CPU float32 values. [Collection facts](VSP03_B03_RESULT_ARTIFACTS_20260908/collection.json)
include file sizes and necessary primary/count/weight readback.

All raw outputs remain at the remote result root and in the local mirror
`C:/Projects/HMASD-worktrees/dm-vsp03-p07-prep-20260907/temp/directions/vsp_03/exp/b03_seed5_p54_20260908`:
G_curve.jsonl,G_final.pt,G_greedy.json,G_stochastic.json,R0.json,R.json,
paired_differences.json,summary.json and copied task.log. No evidence root was deleted.
Compact tracked raw records: [summary](VSP03_B03_RESULT_ARTIFACTS_20260908/summary.json),
[admission](VSP03_B03_RESULT_ARTIFACTS_20260908/admission.json),
[log](VSP03_B03_RESULT_ARTIFACTS_20260908/task.log),
[terminal status](VSP03_B03_RESULT_ARTIFACTS_20260908/terminal_status.json).

## Resource and terminal boundary

Fresh adjacent admission at2026-09-08T20:30:47.940887Z measured both physical and
effective available memory15235641344 bytes, exceeding4294967296 bytes; passed=true.
The complete outer /usr/bin/time report is3.50s and peak_rss_kib515704. Internal elapsed
through readback is3.185330369s, runner_exit_ready3.185911552s; these are narrower than
outer wall. Summary process peak RSS492929024 bytes is also retained. Study critical
path and summed invocation wall each have this sole3.50s observation; aggregate CPU
is unmeasured. Historical planning time is not substituted for this observation.

The supervisor reports terminated,tmux_active=false,exit_code=null. The inspected actual
wrapper uses eval on the supplied payload; that payload's top-level exec /usr/bin/time
replaces the wrapper before EXIT_CODE assignment and its exit-file/footer publication.
The log contains final readback and runner_exit_ready followed by outer elapsed/RSS.
This establishes the published learner/output facts and reported bounded wall; it does
not recover a numeric exit. Do not infer exit0 from summary.complete or inactive tmux.
No supervisor repair, replay, retry or second scientific invocation was performed.

## Frozen reading rule and technical disposition

Card section4 states: "A zero or negative primary does not support replacing R0 here;
retaining readiness is the reasonable current control choice, without population
equivalence or direction failure." It also states: "Stochastic losses restrict any gain
to the declared greedy use; stochastic improvement without greedy improvement does not
answer the primary positively."

The observed primary is negative; greedy G is also below R, and all three stochastic
contrasts are negative. Its absolute primary magnitude is below the declared0.02 MEI.
These predicates are supplied for DM intake under the frozen rule, with every sign
retained. The null exit receipt is an observation/publication limitation; independently
trustworthy primary/count/weight facts remain usable under evidence-spec section11.8.7.
CM accepts those direct artifacts and source conformance, not an unobserved numeric
process exit, stable superiority/equivalence, UAV entry, C promotion or a new run.

Next owner:DM for complete scientific intake and selected continuation. Root owns
integration and eventual removal of the detached execution worktree after evidence
collection/integration; it has no ongoing execution need. The shared authoring checkout
remains the direction's active checkout. Test scratch cleanup remains this CM's separate
policy dependency, exactly recorded in the technical acceptance file; Root is not its
routine cleanup owner.
