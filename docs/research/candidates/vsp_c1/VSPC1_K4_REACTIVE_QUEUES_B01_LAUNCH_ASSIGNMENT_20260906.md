# VSPC1-K4-REACTIVE-QUEUES-B01 — exact launch assignment, 2026-09-06

**FACTOR run02 is technically accepted; the corrected GENERIC handoff in §6 awaits Root acceptance and dispatch.**
Source binding is the integrated, pushed main commit
`47674883572bbe078ede037cbb8f99b8cd54c159`. Root explicitly requested this assignment
and retained the stop until the exact handoff is accepted and source bytes are bound.
The existing B card, two arms and budget are unchanged.

## 1. Deliverable and ownership

CM `/root/dm_amx_vspc1_next/cm_reactive_queues_b01` technically collects one FACTOR arm
followed by one GENERIC arm, seed 401; Root dispatches only the currently accepted exact arm handoff under
[card §§2–7](VSPC1_K4_REACTIVE_QUEUES_B01_SCIENCE_CARD_20260906.md).
After accepted execution, return both summaries, the paired summary, resource receipts,
whole-invocation timing/exit facts and actual counts; DM intakes their scientific meaning.
The [source intake §6](VSPC1_K4_REACTIVE_QUEUES_CONVERGENCE_INTAKE_20260906.md)
and integrated CM record supply existing acceptance and exposure facts. This assignment
adds the exact integrated launch SHA, paths and current observation routing only.

Runtime ownership is the named output root below. CM may record launch/collection facts in
`VSPC1_K4_REACTIVE_QUEUES_B01_CM_RECORD_20260906.md` and the normal E0 result record;
no source, scientific card, comparator or governance edit is selected. Preserve all other work.

## 2. Bound source and preserved semantics

The complete launch checkout is the exact main commit above. These are the reviewed entry points:

- `experiments/candidates/vsp_c1/k4_reactive_queues_b01/experiment.py`
- `experiments/candidates/vsp_c1/k4_reactive_queues_b01/reporting.py`
- `scripts/run_vspc1_k4_reactive_queues_b01.py`
- Existing admission entry `scripts/hmasd_resource_preflight.py`.

DM compared those paths from reviewed source commit
`0652103f6d992a8c72ada7a45ca7b2384efdbe64` to integrated commit
`47674883572bbe078ede037cbb8f99b8cd54c159`: the Git diff is empty. `git ls-remote origin
refs/heads/main` returned that exact integrated SHA. No source changed and no check was repeated.
This records the source binding; it adds no runtime hash guard or manifest machinery. Later
unrelated documentation commits do not change the accepted source surface or require another smoke.

Preserve card §§2–5: one learning focal worker, known reactive partner, old-h simultaneous
choice, held actions for d=2/6, H=48, full served-work J/96, FACTOR 300 parameters versus
GENERIC 309, exact actual-segment Double-Q/terminal target, equal episode/period loss,
Adam/target-copy schedule and recorded RNG namespaces. Each arm has 256 updates and the
same nine fixed evaluation points with 128 episodes per period per point. Use CPU float32,
one compute thread and batch16 training episodes; do not pass the technical-fixture option.
No additional arm, seed, replay, period, checkpoint selection or parameter change is selected.

## 3. Exposure, cost, acceptance and stop

Reuse the CM's existing configuration-only machine output, generated before any selected run.
Its can-move line is reproduced verbatim below; actual seed-401 initial norms/displacement
remain to be measured inside the two selected invocations. No separate movement/cost probe.

```text
Trainable online parameters; one detached actual-segment Double-Q squared-loss Adam step per update, lr=0.01, clip=5; target unoptimized. Actual movement measured in run.
```

The same machine configuration gives per arm: 4,096 training episodes / 196,608 joint steps /
65,536 renewal rows / 61,440 nonterminal rows / 256 Adam steps; 2,304 evaluation episodes /
110,592 joint steps / 36,864 evaluation decisions; 454,656 scalar Q predictions and 17 target
copies. Pair totals are 614,400 joint steps and 512 Adam steps, one paired training instance.
The configuration-only output, this handoff preparation and source comparison add zero model,
training, evaluation or result-invocation exposure. Prior seed-9401 engineering test exposure
remains recorded separately in the source intake and CM record.

Reuse the CM record's approximately 916 s/arm assumption-based planning projection from the
already-required fixture. It is not observed selected-arm or remote time; the source cost law
and full work factors are in the card/CM record. The controlling cap is **2,700 s per entire
arm invocation**, covering runner imports, initialization, learning, every evaluation,
primary write/read, resource publication and exit. GENERIC's cap also includes offline paired
publication. The 5,400 s sum is a sum of caps, not a study elapsed forecast or transferable budget.
No extra profiling, test, result-bearing smoke, retry or budget extension is assigned.

Acceptance is card §7 / evidence-spec §§4, 5.2, 11.4, 11.8.6–11.9. The seven focused
semantic/rule checks, paired publication fixture and independent review are already accepted.
Check the actual run's supervisor terminal fact and primary summaries/counts, not just exit zero.
A missing resource-only quantity is `resources_unmeasured`; a primary/learner dependency gap
limits that dependent claim. Do not reinterpret technical failure as performance polarity.

FACTOR precedes GENERIC. Its terminal technical collection verifies the planned complete
path before the GENERIC command is dispatched; FACTOR's score/sign is not an arm-selection
condition. If FACTOR fails or its required primary path is incomplete, preserve the actual
facts and return that specific issue to DM rather than silently modifying or retrying the plan.
The same holds for a refused GENERIC admission or concrete failure. Stop after the prescribed
endpoint/publication/exit, whole-arm cap or concrete failure. Preserve partial output in place.

## 4. Corrected FACTOR-only transport assignment — preserved after run02 execution

The following repair assignment was accepted and executed by Root as run02; its terminal
technical acceptance is recorded in the CM record and §6. Original preparation facts follow.

Root's first accepted handle `vspc1-reactive-b01-factor-run01` is terminal with exit 0,
start/end `2026-09-07T13:57:52+08:00`, duration 0 s, and only supervisor start/end log lines.
The actual preserved remote `runner.sh` contains exactly:

```bash
eval 'bash -lc  cd '
```

That command runs only `cd`; the stored command contains neither memory admission nor a
runner invocation. Read-only inspection confirmed the old run01 output root is absent.
This supports zero experiment exposure from this accepted handle. The exact upstream
PowerShell transformation is not retained in these remote records; its attribution to
PowerShell interpolation is plausible but not independently reconstructed. Independently
verified: the accepted command was truncated, and the supervisor joins supplied arguments
with `COMMAND="$*"` then evaluates that string. Nested-shell argument quoting was unsuitable.
Preserve the failed handle and all its files under
`/home/wu/.agent-tasks/vspc1-reactive-b01-factor-run01/`; do not replay its command.

**Authorization:** DM assigned correction of this command-delivery failure, and Root explicitly
requested the bounded corrected FACTOR-only retry preparation on unchanged source. The existing
FACTOR object and its original scientific budget remain selected; this repair adds no seed,
arm, extension or automatic scientific retry budget. The prior accepted handle executed no
admission/learner. Root will accept the exact corrected payload below before dispatching once.
CM must not launch it independently. GENERIC remains undispatched and requires its later
original-arm handoff; the earlier GENERIC command is superseded for operational use.

The existing remote worktree was read back at exact SHA
`47674883572bbe078ede037cbb8f99b8cd54c159`:

- node: `wsl_4070`, SSH target `hmasd-wsl-node`;
- cwd: `/home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835`;
- interpreter: `/home/wu/.venvs/hmasd/bin/python`;
- new planned handle: `vspc1-reactive-b01-factor-run02`;
- new output: `/home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835/temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run02/FACTOR/`.

Both the new task directory and run02 output root were absent at the repair observation.
No checkout creation or source transfer is needed. Preserve the existing checkout and old
failed evidence. A later uncertain send must be reconciled using this same run02 handle.

**Exact Windows PowerShell payload for Root, once after acceptance:**

```powershell
$vspFactorLaunch = @'
import subprocess
command = "cd /home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835/temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run02/FACTOR/resource_admission.json && /usr/bin/time -p -o /home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835/temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run02/FACTOR/invocation.time timeout --signal=KILL 2700s /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_reactive_queues_b01.py --arm FACTOR --seed 401 --out /home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835/temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run02/FACTOR"
subprocess.run(['/usr/local/bin/agent-task', 'run', 'vspc1-reactive-b01-factor-run02', command], check=True)
'@
$vspFactorLaunch | ssh -T -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /home/wu/.venvs/hmasd/bin/python -
if ($LASTEXITCODE -ne 0) { throw 'FACTOR dispatch returned nonzero; inspect run02 status before any further action' }
```

The single-quoted PowerShell here-string preserves literal Python text over SSH stdin.
Python supplies `agent-task` one complete command-string argument; the string contains no
shell variables or nested `bash -c` layer. The supervisor's join/eval therefore receives the
intended `cd && admission && timed runner` chain. No PowerShell variable is embedded in that chain.

**Bounded transport acceptance:** the same literal command crossed this PowerShell → SSH stdin
→ remote Python boundary in a non-result check. `bash -n` returned 0. Parsed tokens were
asserted against the exact three expected command segments, including cwd, interpreter,
admission/receipt, timeout 2700s, FACTOR, seed401 and output. The prospective `agent-task`
argv was printed without calling it. No supervisor test task, preflight, model/RNG, runner,
source test or experiment was executed. Raw observations are under the CM repair checkout's
`temp/directions/vsp_c1/transport_repair_20260906/` (`accepted_runner.txt`, `status.json`,
`task.log`, `paths.json`, `argv_check.json`).

Fresh node-local `admit-memory` is adjacent through `&&` before the actual timed runner;
both physical/effective available memory must reach 4 GiB. The entire unchanged FACTOR arm,
including imports, 256 updates, nine evaluations, publication and exit, retains the 2700s cap.
CPU float32, one compute thread and batch16 remain source-defined. Outputs are
`resource_admission.json`, `invocation.time` and `summary.json` in the new FACTOR root.

Root observes acceptance with `agent-task status vspc1-reactive-b01-factor-run02` and
`agent-task logs vspc1-reactive-b01-factor-run02 40`; retained supervisor files are under
`/home/wu/.agent-tasks/vspc1-reactive-b01-factor-run02/` after acceptance.
Manual stop is `agent-task stop vspc1-reactive-b01-factor-run02`.
Exit 0 alone is not technical completion: collect primary output and actual counts.
CM owns technical collection; DM owns science. No scientific polarity follows from run01.

## 5. Current Root routing and observation ownership

Root reported routing ready at main `2a5cadd41`; the configuration and procedure at bound
main `476748835` confirm the endpoint: Root task `01a07249-b095-7821-8ce2-e9c32ba85267`,
Luna/xhigh, integrated Monitor/Transport, one shared thirty-minute fallback. Old standalone
Monitor/Transport tasks are retired. The existing heartbeat is `hmasd-experiment-monitor`;
Root, not this CM or DM, maintains/reads its ACTIVE state. This assignment creates no
monitoring handoff, automation or independent polling chain.

After **each actual accepted** `agent-task` handle, native CM sends it directly to `/root`
through collaboration, linking this assignment and the run record, with the accepted name,
node, bound SHA, cwd, receipt/result/timing paths, supervisor log/status commands, 2,700 s
whole-arm bound, responsible CM and DM `/root/dm_amx_vspc1_next`. Keep observation ownership
with CM until Root records adoption and ACKs after ACTIVE readback. Then Root owns routine
observation; CM retains terminal collection/technical acceptance and DM scientific intake.
Reuse the same (node, accepted handle) on reconciliation; do not relaunch to transfer observation.
If Root dispatches directly, it records local adoption/ACTIVE readback without a self-message;
CM still receives the handles for collection and technical acceptance, and DM intakes the result.

Source/card integration is now recorded at `476748835`, and this exact handoff remains
pending Root acceptance. Owner reviews on current main returned `[]` at preparation. The
object-tier record selects preparing this already-chosen bounded execution assignment, not
new scientific scope. No new P1/P2 owner decision is introduced; ordinary technical records
follow the existing P2 cutoff. Independent Portfolio retains cross-direction science.

## 6. GENERIC exact handoff after FACTOR acceptance — not dispatched

FACTOR run02 was technically accepted in CM commit
`02caf76d514f1dfc2d807964141e3e980336caa1` after actual artifact collection:
exit0, complete primary/counts, adjacent memory admission and whole-arm wall4.84s.
That acceptance, not FACTOR's return/sign, satisfies the prerequisite for the original
GENERIC arm. Root requested this corrected handoff; Root must accept and dispatch it once.
No GENERIC, admission or experiment was executed while preparing this handoff.

Bound source remains `47674883572bbe078ede037cbb8f99b8cd54c159`, node wsl_4070,
same existing detached cwd/interpreter as §4. New planned handle:
`vspc1-reactive-b01-generic-run02`; new output: same run02 root's `GENERIC/`.
Both were absent at preparation. Pair publication uses the accepted run02/FACTOR summary
and new run02/GENERIC summary and writes `run02/paired_summary.json`.
All scientific parameters and counts remain those in §§2–3 and the frozen card.

**Exact Windows PowerShell payload for Root after acceptance:**

```powershell
$vspGenericLaunch = @'
import shlex, subprocess
w = "/home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835"
p = "/home/wu/.venvs/hmasd/bin/python"
o = w + "/temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run02"
generic = [p, "scripts/run_vspc1_k4_reactive_queues_b01.py", "--arm", "GENERIC", "--seed", "401", "--out", o + "/GENERIC"]
paired = [p, "scripts/run_vspc1_k4_reactive_queues_b01.py", "--compare", o + "/FACTOR/summary.json", o + "/GENERIC/summary.json", "--out", o + "/paired_summary.json"]
both = "import subprocess; subprocess.run(" + repr(generic) + ", check=True); subprocess.run(" + repr(paired) + ", check=True)"
admission = [p, "scripts/hmasd_resource_preflight.py", "admit-memory", "--out", o + "/GENERIC/resource_admission.json"]
timed = ["/usr/bin/time", "-p", "-o", o + "/GENERIC/invocation.time", "timeout", "--signal=KILL", "2700s", p, "-c", both]
command = "cd " + shlex.quote(w) + " && " + shlex.join(admission) + " && " + shlex.join(timed)
argv = ["/usr/local/bin/agent-task", "run", "vspc1-reactive-b01-generic-run02", command]
subprocess.run(argv, check=True)
'@
$vspGenericLaunch | ssh -T -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /home/wu/.venvs/hmasd/bin/python -
if ($LASTEXITCODE -ne 0) { throw 'GENERIC dispatch returned nonzero; inspect run02 status before any further action' }
```

The same literal stdin transport is used. Python's standard `shlex.join` serializes
explicit argument lists for the supervisor's existing single command-string boundary.
The small fixed `python -c` sequence places both the GENERIC arm and offline paired
publication beneath one 2700s timeout; it adds no research source or generic launcher.
The second call runs only after the first exits zero. Fresh node-local `admit-memory`
with its own receipt is immediately adjacent before this capped command. Entire
initialization/256 updates/nine evaluations/primary readback/paired report/exit stay inside
the cap. No separate GENERIC probe, source change, test rerun or configuration selection.

Non-result transport verification passed through PowerShell → SSH stdin → remote Python:
bash syntax exit0, exact admission/timed argv roundtrip, and AST inspection that the two
embedded calls are precisely the GENERIC and paired-publication arrays shown above.
Only syntax/parsing occurred; prospective agent-task argv was printed, not dispatched.
Raw check: `temp/directions/vsp_c1/transport_repair_20260906/generic_argv_check.json`
in the CM repair worktree. Same Root adoption/ACTIVE readback and CM/DM ownership as §5.

After actual acceptance, inspect `agent-task status vspc1-reactive-b01-generic-run02`
and `agent-task logs vspc1-reactive-b01-generic-run02 40`; manual stop uses
`agent-task stop vspc1-reactive-b01-generic-run02`. An uncertain send must use this
same handle for reconciliation. Technical completion requires GENERIC summary/counts,
fresh receipt, complete timing/exit and paired summary. No new seed, retry allowance,
budget extension or scientific disposition is introduced.

Independent reviewer `review_ah_reactive_queues` found no material concern in this GENERIC
handoff. It checked the supervisor's actual `eval ${COMMAND@Q}` serialization, shlex argv,
shared timeout and paired-publication dependency. No launch/admission/test was performed.
