# VSPC1-K4-REACTIVE-QUEUES-B01 — exact launch assignment, 2026-09-06

**Prepared for Root's exact handoff acceptance; no result invocation has launched.**
Source binding is the integrated, pushed main commit
`47674883572bbe078ede037cbb8f99b8cd54c159`. Root explicitly requested this assignment
and retained the stop until the exact handoff is accepted and source bytes are bound.
The existing B card, two arms and budget are unchanged.

## 1. Deliverable and ownership

CM `/root/dm_amx_vspc1_next/cm_reactive_queues_b01` technically collects one FACTOR arm
followed by one GENERIC arm, seed 401; CM or Root may dispatch this exact reviewed command list under
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

## 4. Exact remote preparation and command list — not executed

Configured execution node is `wsl_4070`, reached through `ssh hmasd-wsl-node`;
node repository `/home/wu/projects/HMASD`, interpreter `/home/wu/.venvs/hmasd/bin/python`.
The card's CPU boundary is prospectively portable; retain the configured remote-first route.
No local fallback, accepted process or resource receipt is created by this assignment.

After Root accepts this exact handoff, CM prepares the exact committed remote checkout:

```bash
cd /home/wu/projects/HMASD
git fetch origin main
git worktree add --detach /home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835 47674883572bbe078ede037cbb8f99b8cd54c159
```

If preparation or task-name acceptance is uncertain, inspect the existing exact path/handle
before any further action. Do not delete a worktree/output, replace an accepted task or create
another name to bypass uncertainty. No new source is copied from an uncommitted checkout.
The two task names below are planned names, not accepted handles as of this assignment.

Run these as two sequential CM dispatches with the intervening FACTOR collection described
above, using the reviewed `agent-task` command structure. Each fresh node-local admission
is immediately adjacent to its own invocation in the same command; both physical and effective
available memory must be at least 4 GiB before model/RNG/learner initialization. Do not use a
preparation-time or other-arm receipt. Admission creates only its existing receipt path.

```bash
W=/home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835
P=/home/wu/.venvs/hmasd/bin/python
O=$W/temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run01
/usr/local/bin/agent-task run vspc1-reactive-b01-factor-run01 bash -lc "cd $W && $P scripts/hmasd_resource_preflight.py admit-memory --out $O/FACTOR/resource_admission.json && /usr/bin/time -p -o $O/FACTOR/invocation.time timeout --signal=KILL 2700s $P scripts/run_vspc1_k4_reactive_queues_b01.py --arm FACTOR --seed 401 --out $O/FACTOR"
/usr/local/bin/agent-task run vspc1-reactive-b01-generic-run01 bash -lc "cd $W && $P scripts/hmasd_resource_preflight.py admit-memory --out $O/GENERIC/resource_admission.json && /usr/bin/time -p -o $O/GENERIC/invocation.time timeout --signal=KILL 2700s bash -c '$P scripts/run_vspc1_k4_reactive_queues_b01.py --arm GENERIC --seed 401 --out $O/GENERIC && $P scripts/run_vspc1_k4_reactive_queues_b01.py --compare $O/FACTOR/summary.json $O/GENERIC/summary.json --out $O/paired_summary.json'"
```

Each runner records launch SHA from this detached checkout. `O/FACTOR/summary.json`,
`O/GENERIC/summary.json` and `O/paired_summary.json` are the primary output paths;
`resource_admission.json` and `invocation.time` are per-arm. Supervisor logs/exit records
remain under the existing `agent-task` facility: `agent-task status <accepted-name>` is the
terminal witness, `agent-task logs <accepted-name> 40` reads its log and `agent-task stop
<accepted-name>` is the explicit manual stop command if the selected stop condition requires it.
A lost SSH connection is not terminal evidence or authorization to relaunch.

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
