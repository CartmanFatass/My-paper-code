# VSP03 B04 / P67 E0 result evidence

The newly allocated sole P67 seed6 submission completed and published its required
endpoint, counts and weights. Final greedy G minus R0 is **+0.0026123046875000007**;
greedy G minus R is **+0.0017041015625000008**. Actual payload, controller, supervisor
and manager exits are0. This is one trained-instance observation; DM owns scientific
intake and any cross-instance summary. No extra scientific invocation was performed.

## Binding and execution

[P67 card](VSP03_B04_P67_SCIENCE_CARD_20260908.md) sections2/4–6;
[accepted source/command](VSP03_B04_P67_TECHNICAL_ACCEPTANCE_20260908.md).
Source828da00343e5036a4de93ccf1ec636e3b8c777b7; DM acceptance9191bd9bf.
Node wsl_4070, interpreter /home/wu/.venvs/hmasd/bin/python, CPU float32 and one
compute thread, inherited float64 worlds. Seed6, Torch40006, G arm1, no loaded model.
The configured supervisor accepted handle vsp03-b04-p67-20260908 inside its one-shot
unit. Exact detached cwd:
`/home/wu/hmasd-worktrees/vsp03-b04-p67-828da00343e5036a4de93ccf1ec636e3b8c777b7`.
Output root:
`/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p67_20260908`.
The same CM was sole executor/observer/collector; Root and DM received the actual
accepted/terminal handle. No parallel observation or per-shell Root relay occurred.

[Staged source verification](VSP03_B04_P67_RESULT_ARTIFACTS_20260908/staged_source_check.json)
confirmed all11 declared digests, canonical admission helper/dependency, exact cwd,
LF shell bytes, syntax and unused P67 handle/output before submission. The manager
reported degraded at preparation; that observation was retained rather than made a
new launch gate. The initial read-only inspection helper raised on its return1,
then captured the status normally; no scientific submission had yet occurred.
[Submission](VSP03_B04_P67_RESULT_ARTIFACTS_20260908/submission.json) records the one
execution of the committed launch_p67.sh. The actual
[supervisor wrapper](VSP03_B04_P67_RESULT_ARTIFACTS_20260908/supervisor_runner.sh)
and log retain the adjacent admission&&runner command. The historical P64/P65
missing-file failure, zero exposure and spent allowance remain unchanged.

## Endpoint and variation

Four final executions share1024 held-out world/phase entries. Absolute native returns:

| Endpoint | Mean |
| --- | ---: |
| G greedy | 0.356015625000 |
| G stochastic | 0.304648437500 |
| R0 | 0.353403320313 |
| R | 0.354311523438 |

| Contrast | Mean | Paired-world sample SD | Conditional-world SE |
| --- | ---: | ---: | ---: |
| G greedy−R0, primary | +0.002612304688 | 0.073820057336 | 0.002306876792 |
| G greedy−R | +0.001704101563 | 0.088711319922 | 0.002772228748 |
| G stochastic−R0 | −0.048754882813 | 0.339461417879 | 0.010608169309 |
| G stochastic−R | −0.049663085938 | 0.341420053236 | 0.010669376664 |
| G stochastic−G greedy | −0.051367187500 | 0.339042533653 | 0.010595079177 |

SD uses the sample denominator; SE=SD/32. These describe conditional world variation,
not independent-training uncertainty. The selected primary is update128 greedy G−R0;
all signs/modes are retained. No seed comparison or direction disposition is made by CM.
The [summary](VSP03_B04_P67_RESULT_ARTIFACTS_20260908/science/summary.json), four raw
endpoint files and paired_differences.json preserve the full available measurements.

## Learning, counts and weights

One2083-parameter G;128 real backward calls and128 Adam steps. Training completed
16384 joint episodes,655360 team ticks and1310720 target transitions, with63151 valid
and gradient rows. Four final1024-world executions add4096 joint episodes. Whole run:
20480 started/completed episodes,819200 team ticks,1638400 target transitions,
88790 decision rows and2149 rollout-policy forwards (objective/critic work excluded).
The G arm's evaluation_episodes2048 counts its two modes; R0/R add the other2048.
No extra validation model, episode, optimizer step or evaluation was executed.

Initial total parameter L2=5.734800338745117. First-step displacement L2=
0.023387808352708817, relative0.004078225390812213. Final displacement L2=
2.503492832183838, relative0.4365440266978239. Final actor/critic displacements are
2.433328151702881 /0.5885485410690308. All128 curve rows and G_final.pt are retained.
The normal run checked weight readback; collection verifies the saved weight bytes'
remote SHA256 without constructing another model or running another evaluation.

## Admission, complete clock and termination

[Fresh admission](VSP03_B04_P67_RESULT_ARTIFACTS_20260908/b04_seed6_p67_20260908_admission.json)
passed immediately before the runner in the same command: physical and effective
available bytes15623213056 each, against4294967296. Cgroup-specific limits/headroom
were null in the canonical helper's receipt; the actual receipt is preserved.

The original manager clock is385109.916299 monotonic seconds. Scientific output
readback completed at2.919540s, runner exit-ready at2.920019s, payload receipt/readback
at3.231537s and authoritative whole-task receipt/readback at3.249249s. Manager's
finished journal entry is at3.253184s from that origin, within complete120s; no timeout
or reserve overrun occurred. For this one invocation, observed study critical path
and summed invocation wall are3.253184s on this boundary. Admission/import, learner,
four final executions, required output checking/publication and termination are included.
Arm-only wall2.016852s and summary output-start2.919159s are narrower measurements.
Supervisor's integer wall line4s has coarser clock resolution.

[Manager JSON journal](VSP03_B04_P67_RESULT_ARTIFACTS_20260908/journal.jsonl) records
aggregate unit CPU_USAGE_NSEC3278770000 (3.278770s), MEMORY_PEAK8732672 bytes and zero
swap peak. Scientific process peak RSS is492875776 bytes. Cgroup-accounted memory
and process RSS are different measures and are retained separately. The summary's
aggregate_cpu_s is null; manager CPU supplies the complete-unit observation instead.
Successful transient-unit properties were unloaded before later systemctl show;
that not-found/default view is retained and is not substituted for actual configured
properties in the receipt or terminal facts in the journal/submission record.

[Whole-task receipt](VSP03_B04_P67_RESULT_ARTIFACTS_20260908/b04_seed6_p67_20260908_terminal.json)
and payload receipt report real root/task/supervisor0, no timeout/error, and no
remaining descendants. Controller killed/reaped private control descendants3018014,
3018015,3018028 before final publication. Collection found those PIDs absent and the
actual journal-identified unit cgroup removed. The original supervisor status is
finished/exit0; actual manager result is success/main code=exited,status0. No status
file was fabricated or overwritten by collection.

## Technical acceptance and remaining ownership

[Collection manifest](VSP03_B04_P67_RESULT_ARTIFACTS_20260908/collection.json) preserves
remote artifact paths, sizes and SHA256 digests. All transferred files match. The
[technical readback](VSP03_B04_P67_RESULT_ARTIFACTS_20260908/technical_readback.json)
checks source/seed/count/curve identities, paired world/phase order, existing endpoint
arithmetic, observed weight readback and actual exit/termination. The statistical
readback uses existing output only; no model/world/learner/evaluation was executed.
Engineering checks and the direct primary measurement conform to the selected task;
scientific interpretation remains with DM. No primary, count, weight, admission or
terminal evidence gap remains on this invocation.

One P67 submission was used; no retry, fallback, additional seed/mode, cap change,
source repair after output or prior scratch-cleanup retry occurred. Remote evidence
and the exact execution checkout remain intact for intake/integration; Root owns
checkout retirement after that delivery dependency closes. Return to DM for all-outcome
scientific intake and Root integration. This return selects no successor.
