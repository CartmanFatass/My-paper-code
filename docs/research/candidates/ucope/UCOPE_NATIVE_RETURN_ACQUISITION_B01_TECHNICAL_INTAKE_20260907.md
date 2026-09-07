# UCOPE native-return acquisition B01 — DM technical intake

Date: 2026-09-07. **Implementation accepted; formal B result INCOMPLETE (unrun).**
The two-seed batch is already selected by the [frozen card §§4–5](UCOPE_NATIVE_RETURN_ACQUISITION_B01_SCIENCE_CARD_20260907.md#4-effect-size-reading-rule-and-prediction).
Its initial CM assignment explicitly excluded formal execution. Section 6 below now supplies the
formal execution assignment for Root to dispatch; this intake starts no invocation.

## 1. Evidence checked and authority

DM checked CM's [technical acceptance](UCOPE_NATIVE_RETURN_ACQUISITION_B01_TECHNICAL_ACCEPTANCE_20260907.md)
at commit `79c538140`, source `a0b00f561159ddeedf66b65711cf3f7d2ec93b04`, against card commit
`3520ccd2ce90e8aca3c7bec8e838e403d00068db`, §§1–6. Root integrated source as `245047432` and
acceptance as `bd7e47a67`. At intake base `301603aee4fbb80f9ca332e108da3f833238c41b`, Git's
comparison with the accepted source is empty for the new learner/evaluator, runner/tests and
the four bound historical modules. No unrelated work or historical source changed.

The relevant standard is evidence spec §4, §5.2, §11.4 and §11.8.5–7. In particular, §11.4's
launch rule is: "Only the following may hold a B launch: the §4 common integrity requirements;
the §5.2 requirement that the real learner runs and reports nonzero transition, update, and
evaluation counts; the mandatory resource admission; and one machine-generated **exposure line**
(parameter displacement budget relative to initialisation scale, or an equivalent statement that
the learner can move in its budget)." No added diagnostic, headroom or Pro prerequisite follows.

Question-relevant acceptance checked: count-only tail information before the actual-mark service
component, including SEVERED; native paid/immediate reward and time counters; visited score terms
and the full 256-row loss denominator; fresh action/environment addresses and paired evaluation;
final modal endpoint and rule thresholds; parameter movement and complete/partial publication.
CM reports eleven synthetic cases passing and one remote real artifact readback. The independent
affected-path reviewer found no material defect; its independent gradient comparison differed
by at most 2.39e-9. DM accepts that focused coverage rather than rerunning it. Direct inspection of
the final evaluator/runner and the technical summary, admission receipt and process-time file
agrees with the relevant reported counts and publication boundary. No technical return was used
to retune the frozen learner or score the B prediction.

## 2. Direct observation, counts and receipts

The single real technical profile used seed 9006301, two updates and 16 evaluation episodes per
context per policy. It completed on `wsl_4070`, CPU FP32, one scientific process and one Torch
intra/inter-op thread. The accepted supervisor handle was
`ucope-native-return-b01-technical-9006301-launchfix`; terminal status was `finished`, exit 0,
2026-09-07T07:23:39Z. Runner status is `TECHNICAL_COMPLETE`.

| Technical exposure | Training | Actor evaluation | IMMEDIATE-4 evaluation | Total |
| --- | ---: | ---: | ---: | ---: |
| Episodes | 512 | 128 | 128 | 768 |
| Host-event transitions | 2,548 | 352 | 256 | 3,156 |
| Probe episodes | 254 | 16 | 0 | 270 |
| Committed period units | 2,200 | 480 | 512 | 3,192 |
| Probe time units | 508 | 32 | 0 | 540 |

There were two joint optimizer steps and two tail-active batches. Root initial L2 was 0;
displacement L2 was 0.01975463517 and maximum absolute movement 0.005997684784. Tail initial
L2 was 4.700405121, displacement L2 0.09943917394, relative displacement 0.02115544754 and
maximum absolute movement 0.006004042923. These establish the technical learner's nonzero
exposure, not acquisition value or competence.

Fresh destination admission at 2026-09-07T07:23:36.738Z measured physical and effective available
memory of 15,655,030,784 bytes. External whole-process wall was 2.66 s and peak RSS 506,256 KiB;
user/system CPU were 1.70/1.82 s. Aggregate CPU work (3.52 CPU-s), invocation wall and study
critical path remain different quantities. The summary retains `resources_unmeasured` because
it does not ingest the external RSS file; the directly measured values above remain reportable.
Its internal 2.244269494 s excludes interpreter startup and the final refresh write; external
wall covers both. The formal assignment uses external wall for the complete-invocation cap.

Artifacts: `summary.json`, `training.jsonl`, `final_parameters.pt`, `resource_admission.json`,
`process_time.csv` under `temp/directions/ucope/exp/native-return-b01-technical-9006301/` in
remote worktree `/home/wu/hmasd-worktrees/cm-ucope-native-return-b01-20260907` and the copied
local worktree `C:/Projects/HMASD-worktrees/cm-ucope-native-return-b01-20260907`.
CM's acceptance retains the exact command, failed pre-admission handle, receipt and readback argv.
The first supervisor handle exited 2 before admission/model creation due to command grouping;
the repaired native command string executed the technical learner once. That failure has zero
learner exposure and no scientific sign. No attempt or outcome has been discarded.

## 3. Rule applied verbatim and bounded reading

Card §4 says: "If a primary dependency is incomplete, publish `INCOMPLETE` with actual counts
and any trustworthy completed-seed facts; no two-seed branch is assigned. Missing optional
resource telemetry alone means `resources_unmeasured`. Engineering failures have no scientific
sign and select no retry. All outcomes remain; a negative bounds this learner/budget, not paid
information or the direction."

Formal training seeds completed: **0 of 2**. Formal episodes/optimizer steps/evaluations: **0/0/0**.
The technical profile is excluded from the formal population. Apply **INCOMPLETE**, with no NR-A,
NR-B or NR-C branch and no performance polarity. DM's prospective NR-B/all-immediate prediction
is **not yet scored**; owner prediction is **not taken (unattended)**. Passing tests, nonzero
movement, serialization and process exit are engineering evidence only.

The strongest existing scientific support remains PA-B's finite-host acquisition and TW-B's
6/6 versus 4/6 tail-direction coverage. The strongest contradiction remains full competence
3/6 in both TW arms and two false probes losing 0.028562899 each. This intake changes neither.
The surviving question is whether direct native-return learning produces a useful net gain at
this budget. It does not explain the parked retained-policy root residual, establish COUNT/RAW
advantage or support a MARL population claim. No DIRECTION.md scientific update is warranted.

## 4. Cost, exposure and engineering scope

Using the recorded technical timings, DM recomputed the card's cost law in Python without new
episodes: fixed remainder = 2.558917652 s; batch256 = 0.04874613600 s; evaluation pair =
0.00002804746873 s. Thus `fixed + 1024*batch256 + 32768*pair` projects **53.394020374 s per
seed**, **106.788040748 s summed**. This is a small-profile planning estimate, not a bound;
probe frequency, load and publication size may differ. It gives no new budget or cost pilot.

The selected complete work is unchanged: each of seeds 6301/6302 has 262,144 training episodes,
1,024 joint optimizer steps and 32,768 paired evaluations (65,536 evaluation episodes). Total:
655,360 episodes, 2,048 joint steps, and actual host-event transitions in the frozen
1,310,720–4,849,664 range. Contexts and evaluation episodes are not independent training seeds.
There is one learner arm and one fixed legal null, no nested candidate search or added
validation sweep. Caps remain **600 s per complete formal invocation**, **1,200 s summed**.
The separately selected technical profile consumed no formal invocation allowance.

ENGINEERING_SCOPE_SPEC §4: **needs none**, unchanged from card §5. CM reports 295 new non-test
source lines including the 111-line runner; 196 test lines, focused synthetic tests below five
minutes and the one real technical profile below 60 s. No §5 budget breach or unrequested
machinery was found. Existing resource admission, supervisor, process-time and OS timeout
utilities are reused for the frozen execution bounds; no code or new orchestration is commissioned.

## 5. Decisions this intake produces

1. **Technical acceptance (object tier).** Options: (a) accept the delivered implementation;
   (b) return a concrete information/reward/gradient/measurement defect to the same CM.
   Recommendation and selection: **(a)**; no material gap remains in the present claim's path.
   Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
2. **Continue the selected batch (object tier).** Options: (a) supply the exact formal assignment
   below for Root dispatch; (b) leave formal execution unassigned because a concrete unresolved
   card requirement prevents it. Recommendation and selection: **(a)**; the frozen batch is
   already selected and the technical evidence supplies the missing runtime/cost information.
   Owner-delegated decision (unattended, 2026-09-03 instruction): (a).

No direction-tier or Portfolio decision is taken. No owner instruction takes over either object
decision. At this clean boundary `item.py reviews --json` returned `[]`; the audit owner cells
were empty. The existing P2 frozen-card item `20260907-ucope-001` remains the same card. Both
decision commands and the brief command returned `skipped P4: owner maintains P1/P2 only; cite
the card/intake in the audit ledger`; no new inbox item was created.
Owner flags: **none**. The technical-only [Chinese brief](../../portfolio/owner/briefs/ucope/2026-09-07_native-return-b01-technical.md)
states the absence of a formal result. Audit rows: [September 7 ledger](../../portfolio/audit/2026-09-07.md).

## 6. Formal execution assignment — prepared, not dispatched

This is the DM's explicit formal execution assignment for the already selected B01 batch.
It supersedes only the initial handoff's implementation/checks-only endpoint; all frozen
scientific semantics and caps remain. **No formal invocation or accepted formal handle exists
at this intake.** The proposed handles below returned `not_found` in a read-only supervisor check.
Root receives this assignment for actual dispatch to the existing CM; readiness is not a launch.

1. **Deliverable:** execute formal seeds **6301 and 6302**, one fresh process each, then collect
   every complete/partial output and return technical acceptance. Use sequential invocations;
   neither seed is selected or cancelled by the other's return sign. A concrete shared technical
   failure returns to DM before dependent execution; no automatic retry or replacement follows.
2. **Owned paths/entry points:** existing accepted source
   `a0b00f561159ddeedf66b65711cf3f7d2ec93b04`, script
   `scripts/run_ucope_native_return_acquisition_b01.py`; runtime roots in the commands below and
   the B01 result evidence under this direction. No source edits or new tests are assigned.
3. **Preserved semantics:** card §§1–3 and §5, especially fresh RNG ancestry, count-only callback,
   realized cost-inclusive return, final-modal endpoint, both policies/all eight contexts,
   CPU FP32 and one Torch intra/inter-op thread. No pilot, tuning, checkpoint selection or
   retained-policy dependency is introduced.
4. **Acceptance:** card §3's primary/count/exposure fields and §4's unchanged reading rule,
   with evidence spec §4, §5.2, §11.4 and §11.8.5–7. Collect the summary, training JSONL, final
   state, admission receipt, process time and supervisor logs/status. Read back existing outputs;
   do not repeat learning or evaluation for collection. DM applies `reading_rule` to the two
   formal summaries, retaining each seed/context and conditional evaluation SE separately from
   training variation. Missing primary data stays INCOMPLETE; optional resource gaps stay marked.
5. **Budget/stop:** exactly two selected invocations, no extra allowance; 600 s each including
   interpreter/imports, learning, evaluation and publication. Existing OS timeout enforces the
   outer deadline; its two-second forced-termination interval permits cleanup only and adds no
   scientific allowance. Retain partial files and report any cap breach or termination; do not
   label an over-cap attempt a complete frozen comparison. No restart, resume or additional seed.

Execution node is `wsl_4070`, SSH target `hmasd-wsl-node`; use the existing detached exact-source
worktree `/home/wu/hmasd-worktrees/cm-ucope-native-return-b01-20260907` and interpreter
`/home/wu/.venvs/hmasd/bin/python`. Before dispatch, confirm that checkout still holds the
accepted source surface; reuse it without copying uncommitted code. `/usr/bin/timeout` was
present in the read-only node check. The exact native supervisor commands are:

```bash
/usr/local/bin/agent-task run ucope-native-return-b01-seed6301 'cd /home/wu/hmasd-worktrees/cm-ucope-native-return-b01-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/native-return-b01-seed6301/resource_admission.json && /usr/bin/time -f %e,%M -o temp/directions/ucope/exp/native-return-b01-seed6301/process_time.csv /usr/bin/timeout --signal=INT --kill-after=2s 600s /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_native_return_acquisition_b01.py --seed 6301 --profile science --out temp/directions/ucope/exp/native-return-b01-seed6301'
/usr/local/bin/agent-task run ucope-native-return-b01-seed6302 'cd /home/wu/hmasd-worktrees/cm-ucope-native-return-b01-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/native-return-b01-seed6302/resource_admission.json && /usr/bin/time -f %e,%M -o temp/directions/ucope/exp/native-return-b01-seed6302/process_time.csv /usr/bin/timeout --signal=INT --kill-after=2s 600s /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_native_return_acquisition_b01.py --seed 6302 --profile science --out temp/directions/ucope/exp/native-return-b01-seed6302'
```

Each preflight is a **new destination admission** immediately adjacent via `&&` to that seed's
runner. Both physical and effective available memory must be at least 4 GiB before any scientific
root/RNG/model creation. A missing/failed receipt refuses that invocation; the technical receipt
cannot admit it. No receipt, formal root, RNG master or process was created by this intake.

For each accepted handle, the launching CM sends Root the node, handle, source, cwd, log/result
and receipt paths, 600 s bound and responsible DM/CM using native collaboration, following
EXPERIMENT_MONITOR.md's accepted-handle handoff. Root records tracking/shared-heartbeat readback
and ACKs adoption; launcher observes until ACK, Root observes afterward, CM collects and accepts,
DM interprets. No relaunch transfers observation. A terminal handle goes directly to collection.

## 7. Next discriminator and unresolved risks

The next discriminator is exactly the two final formal native-return differences and their
uniform-context mean, read using the frozen ±0.001 branches. Small historical headroom, noisy
credit, premature loss of probe exposure and stochastic-training/modal-evaluation mismatch
remain scientific alternatives, not diagnosed causes. Complete formal runtime is unmeasured.
Until those data exist, the claim ceiling is technical path readiness plus the unchanged prior
finite-host B evidence. The retained-policy/numerical-locus family stays parked; Portfolio owns
the direction's lifecycle and sequencing.
