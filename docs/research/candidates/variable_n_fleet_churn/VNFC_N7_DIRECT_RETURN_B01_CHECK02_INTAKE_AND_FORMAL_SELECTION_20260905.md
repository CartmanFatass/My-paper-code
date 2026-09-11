# B01 check02 intake and formal execution selection

The selected non-target check02 completed the real N7 learner/evaluator/publication path.
Select one execution of the already frozen `VNFC-N7-DIRECT-RETURN-B01` B/EXPLORE card,
using the accepted source and unchanged total 2700-second wall cap. This is an object-tier
execution selection, not a new scientific object, direction disposition or formal result.

## Evidence and rule applied

Read the complete `VNFC_N7_DIRECT_RETURN_B01_TECHNICAL_ACCEPTANCE_20260905.md` and its raw
`evidence/b01_check_20260905_02/` JSON, task log, memory receipt and external time record at
CM commit `e212dbfcf`. The source remains `33e08f440c2117dcfd9457d825f42fef7b38ccd7`.
Read against the science card, CM handoff and selected unchanged retry in
`VNFC_N7_DIRECT_RETURN_B01_CHECK01_INTAKE_20260905.md`. No source or scientific-setting
change followed that selection. Root's current evidence spec sections 11.8/11.9 control;
current owner-console review instructions were empty at this clean boundary. The previous
low-priority sequencing instruction and recasts: 2 remain unchanged.

Evidence spec 11.4 states: "Only the following may hold a B launch: the §4 common integrity
requirements; the §5.2 requirement that the real learner runs and reports nonzero transition,
update, and evaluation counts; the mandatory resource admission; and one machine-generated
**exposure line** (parameter displacement budget relative to initialisation scale, or an
equivalent statement that the learner can move in its budget)."

Evidence spec 11.8.7 states: "Root-cause attribution requires direct evidence, but reproducing
and uniquely locating every historical cause is not a universal prerequisite for later work.
Repair or check a defect that threatens reward, information access, comparison, training or
the primary measurement." The selected check has now exercised those actual dependencies.
No third smoke, exact census, unique HMAC diagnosis, Pro round or GitHub write-capability
exercise is needed to select this already frozen B. Fresh remote admission remains required
immediately before the actual invocation.

## What was checked and observed

The detached check02 task was `vnfc_b01_check_33e08f440_20260905_02` on `wsl_4070`, at
`/home/wu/hmasd-worktrees/vnfc_b01_check_33e08f440_02`. It used the selected non-target
namespace `B01-ENGINEERING-CHECK`, training seed 2026090591 and evaluation seed 2026090592.
It ran two rounds of 32 complete episodes per arm, four PPO epochs with 24-transition
minibatches, eight evaluation episodes per checkpoint and eight fixed-BCRH episodes.

DM read all 128 training rows, 56 evaluation rows and four training-curve rows as recorded
data, and independently re-totalled the work without another simulation or check launch.
Each arm has 64 training episodes, 384 joint training transitions, 64 optimizer steps and
64 backward calls; each of its two rounds has 32 episodes, 192 transitions and 32 steps.
Each initial/midpoint/final evaluation contains eight episodes per arm. BCRH adds eight
episodes and 48 complete controller/checker calls. Total: **184 episodes, 44,160 native
ticks**. Episode rows and checkpoints are not independent training seeds.

The machine-generated exposure reports one actual non-target training instance per arm:
MAPR parameter count 89,090, initial norm 33.3166654994, relative displacement .0688416059;
DIRECT parameter count 148,739, initial norm 38.6522987673, relative displacement .0693235828.
DIRECT residual output parameter norm moved from 0 to .0822663397. Its evaluation residual
logit RMS was 0, .0078655136 and .0533366153 at initial, midpoint and final. These observations
establish learning activity and movement; they do not establish competent or useful return.

The saved technical acceptance reports native endpoint/reward reconstruction, both-zone
physical command mapping, forced-command PPO replay, first-minibatch likelihood agreement,
one same-batch presentation consequence check per arm, complete primary publication and
successful readback of all six checkpoints. The independent source/output reviewer found
no unresolved material mismatch. DM has not rerun the reviewer or substituted check returns
for the frozen formal seed. Native context is endpoint ratios, flags and 20-second observations;
it is not a recovered exact-latency measurement from the old shadow system.

Fresh admission passed with **15,426,125,824 bytes** both physical and effective available
memory. Check02 exited 0. External complete chain: **21.71 wall seconds**, **20.64 user +
1.87 system = 22.51 CPU seconds**, including import/build, both learners, BCRH, publication
and output pytest. Runner through complete publication: 20.218502969 seconds. Pytest: one
passed in .75 seconds. The supervisor's 22 seconds is a rounded observation, not a replacement
for external wall. Maximum RSS 543,720 KiB is an observed maximum, not an aggregate memory sum.

## Cost, uncertainty and retained failure

Use the final `complete_projection` JSON line in `check.log`, which includes the final summary
replacement/readback; the earlier `summary.json` projection is explicitly intermediate.
The complete conditional formal projection is **282.611022287 seconds**, comprising shared
setup 7.671873, training-world generation 1.439145, evaluation-world generation .038719,
other measured overhead .329268, MAPR 112.199289, DIRECT 121.632887, BCRH 37.706789 and
publication 1.593053 seconds. The actual algorithm law is shared work plus, per learned arm,
2048 collect episodes + 64 update rounds + 192 evaluation episodes, plus 64 complete BCRH
episodes and publication. Check collection batch 32 and minibatch 24 match the formal work.

Evaluation and BCRH batch width increases from 8 to 64: linear per-episode cost is a planning
assumption, not a demonstrated upper bound. Later policies, sampled worlds and node contention
may change costs. Formal actual wall/CPU and full cost remain **unknown until execution**.
The conditional projection is below the original 2700-second total; neither per-arm allowance,
parallel savings, E01 speedup nor a new profiling experiment is inferred. No unknown component
is intentionally counted as zero. Full initialization and publication remain inside one cap.

Check01's HMAC initialization exception remains unexplained. It produced no training or
evaluation; reduced HMAC tests and exact same-source initialization subsequently passed, and
now check02 passed the complete path. This supports proceeding without a speculative repair,
but does not establish the original cause or guarantee non-recurrence. Preserve check01 and
all diagnostic evidence. The two measured check chains cost 25.61 wall / 25.79 CPU seconds
in total; initialization diagnosis additionally recorded six supervisor seconds, with CPU
unmeasured, and the small HMAC probes lack precise wall/CPU. Preparation is not free and is
not an additional formal-run allocation.

The completed E01 remains 28.11 wall / 37.93 CPU seconds with its 123,765.5-second census
projection and original engineering stop. It is not rerun or reinterpreted. Historical R02
learner losses and quarantines also remain. Check02 is engineering evidence, with no new
scientific polarity, headroom, stable superiority, exact maximum or mechanism attribution.

## Decisions this intake produces

| Option | Consequence | Recommendation |
| --- | --- | --- |
| A. Execute the frozen formal B once with the accepted source and fresh remote admission | Obtain the selected real learning/return observation within the existing 2700-second total; retain all outcomes and any failure | Recommended and selected |
| B. Require another smoke or unique historical HMAC explanation first | Repeats or broadens work after the actual required path passed; no concrete remaining claim dependency justifies it | Not selected |
| C. Change source, seeds, arms or schedule before formal execution | Changes an already inspectable comparison without new scientific evidence or a source-supported repair | Not selected |

**Owner-delegated decision (unattended, 2026-09-03 instruction): A.** Tier: object;
kind: selection; provenance: OWNER_DELEGATED; reversible: yes; owner flag: none.
This does not decide Portfolio priority, lifecycle, investment beyond the frozen cap or a
direction-tier recast. Root integrates the shared ledger/owner decision item under the assigned
division of work; no owner reply is awaited. The card's prediction remains on record and the
owner prediction is not taken (unattended). No scientific valid-result brief is produced from
this engineering check.

## Exact CM execution handoff and result ceiling

After this selection is committed and pushed, CM executes exactly once using source
`33e08f440c2117dcfd9457d825f42fef7b38ccd7`, detached on `wsl_4070`, task
`vnfc_b01_formal_33e08f440_20260905_01`, cwd
`/home/wu/hmasd-worktrees/vnfc_b01_formal_33e08f440_01`. Use the exact command in the final
section of the technical acceptance: immediate same-node memory admission joined by `&&`,
external whole-invocation time and `timeout 2700s`, `--profile formal`, training seed
2026090501, evaluation seed 2026090502, and output root
`temp/directions/variable_n_fleet_churn/b01_formal_20260905_01/output`. No third check,
engineering presentation probe, extra pytest or automatic formal retry is selected.

Protected semantics are the science card and CM handoff: two actual CPU binary64 learners,
one Torch/native compute thread, N7 survivors, corrected public information/action mapping,
paired exogenous worlds with separate learner/action streams, unchanged optimizer, unshaped
reward, fixed BCRH and initial/32/64 checkpoints. Formal work is two arms × 64 rounds ×
32 full episodes × six decisions, four PPO epochs × eight minibatches per round; three
64-episode evaluations per arm and 64 BCRH episodes once. This is 4544 complete episodes,
1,090,560 native ticks and 2048 optimizer steps per arm. Scope-spec section 4 additions: none.

At selection time no formal task has been accepted. CM owns actual launch, terminal collection
and technical acceptance and hands any accepted handle directly to the shared tracker
`/root/tracker_tl_experiments`, naming this DM. Failure, cap expiry or missing primary output
returns its concrete observations and dependency boundary without a blind retry or a negative
algorithm claim. Success returns all primary outcomes, actual exposure and cost for DM intake.
The next discriminator is terminal-checkpoint native recovery: each arm's final-minus-initial,
MAPR-minus-DIRECT and each learner-minus-fixed-BCRH, aggregate and by failed zone, as already
selected. One paired training seed supports a bounded B observation, not training-seed population
uncertainty or stable superiority; learner improvements and native losses are reported separately.
