# Energy relay baselines

Lead: **Codex DM (independent session)**. Question: under the common S7 service–risk
conditions and declared information/exposure, does the ordinary learning deficit recur
across independent training instances, and which ordinary training or demonstration
initialisation package can reliably narrow it? D1 replication is the current candidate;
D4 imitation is a possible successor within this question, not a second active study.

## 2026-09-27 — Evidence reconstruction and preparation before the complete SET result

### Assignment, scope and source exposure

The owner-requested assignment creates this direct DM in task
`01a0e0ad-0710-71f3-8d9d-8012fe7b65b0` on shared main at `/home/fires/hmasd-wsl`.
Initial source is main `d81fc8622c79426c5c1fa53e4ae0e4f83b05555b`, verified against
published origin/main at 02:28 UTC. Root is preparing the initial index/routing entry;
until that is visible this session edits only its own paths. No App messages are authorised.
Owner pause is lifted in the current index. No result operation is accepted by this entry.

Source evidence:

- Corrected [Claude report](../../../inbox/2026-09-27-energy-relay-benchmark-report-and-directions-for-codex.md),
  correction commit `003d4d369`; its proposed nine fits and causal interpretation of D4 are
  advice, not the selected design.
- [B01 result and later corrections](../energy_relay_benchmark/NOTES.md#2026-09-26--b01-result-read-by-the-pre-registered-branches-operation-02f762d2-tag-b01_ref_a02),
  including the complete [response to independent reviews](../energy_relay_benchmark/NOTES.md#2026-09-26--dm-response-to-both-reviews-of-the-b01-reading-and-the-b02-proposal-revised-b02-stage-0-declared).
- [Stage 0 readings](../energy_relay_benchmark/b02_stage0_readings.json) and notebook results,
  [published c00–c03 readings](../energy_relay_benchmark/b02_stage1_readings.json) as present at
  source `d81fc8622`, and the [recovery declaration](../energy_relay_benchmark/NOTES.md#2026-09-27--stage-1-resumed-from-c03-declaration-engineering-review-and-launch-record-b02_s1_set_a01r-operation-faf881bc).
- Shared background at the same revision: [information structure](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构),
  [representation versus finite learning](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面),
  and [experimental units and native service/risk](../../RESEARCH.md#6-实证研究是在具体条件下缩小解释空间).

The shared background changes this design concretely: independent training attempts, not
evaluation worlds/checkpoints, are the replication units; complete service and native J must
be read beside return cost, battery tails and events; an ordinary reference may establish
task opportunity without diagnosing representation or credit. The B09 adverse training-shield
comparison remains contrary evidence to any presumption that shield exposure helps learning.

**Exposure boundary:** this session and its helpers have not read or used the sealed
957001–957032 outcomes. `runs/energy_relay_benchmark/b02_holdout_refs_a01/` is excluded.
Claude alone owns the accepted recovery, c04–c06 evaluations and once-only hold-out reading.
Only Claude's completed, published interpretation will inform this direction's next investment.
Later publication cannot turn those worlds into an unseen test set for this direction.

### What the available evidence changes

B01 supplies executed references on the exposed 955001–955032 development panel:
H_central about .774 QoS/step, H_local .597, and the old N .328. H_local's return cost is
substantially higher (about 65.9, against N 1.2); its service level is not a joint service–risk
optimum or a promised target for a learner. N was trained for 180k without the training shield;
the SET programme uses 1.2M with it. Their gap is therefore a package/exposure comparison,
not an estimate of an algorithm component or N's typicality.

N's two sampled-action panels are about .308/.318. Boundary occupancy falls from about .50
to .22 while service does not improve; a deterministic wall pose cannot by itself explain
the service deficit. Stage 0's H_spawn/H_park2 are about .232/.379, under the same shield.
They are executed package references, not a causal decomposition of the learner. In particular,
the shield can help a poorly deployed team while costing a well deployed heuristic service.

The c00–c03 SET curve rises from about .209/.243 to .325/.345 (deterministic/sampled) at 600k.
This shows movement beyond that initialisation, with still-large reference gaps. The sampled
c03 service advantage over deterministic N also carries more return cost and lower minimum
battery. Flat training summaries and rising frozen evaluations are different measurements;
this direction does not infer an objective/credit defect before their comparability is resolved.
Detailed numbers remain in the machine-readable sources rather than being duplicated here.

The original process ended at rollout 117 (702k collected transitions); c03 at 600k was the
last checkpoint. The accepted recovery restores learner/optimiser/sampler/value-normaliser
state and reseeds environment/action streams with 925131. Original rollouts 101–117 are
discarded from the continuing curve but remain real exposure and cost. The realised work is
not an uninterrupted independent 1.2M run and cannot be mechanically pooled with two fresh
fits into a three-seed confirmation. Native-fault root cause remains unestablished here.

### Information and executable conditions

Reuse the benchmark's S7-S2, 8 UAVs, H3000, production shield enter 0 / exit .05, ordinary
charging allocation, backhaul guard, native reward (`lambda_return=2`, `lambda_e=1`) and
evaluation metric definitions. No private host, changed decode or reward is selected.

- SET is the existing recurrent low-level MAPPO switch, with `k=10` and a held central
  snapshot of central state + all eight observations + ego one-hot. Current own observation
  also reaches the actor each step. It is a central-input actor, not a decentralised policy.
  High-level/discriminator learning is disabled; the low-level actor/critic are updated.
- H_local plans jointly from all eight legal, radius-gated observations. Pooling those
  observations is more than each independent local actor sees. It is a pooled-observation
  planner; H_central additionally uses central environment information. Neither is an
  identified upper bound for this network or learning procedure.
- The collector stores proposal actions and their log probabilities; the shield modifies
  submitted commands. Native transition reward/next inputs remain the learner's data.
  SET keeps B02's legacy clear-buffer semantics, including the documented live-lane edge.
- A fresh fit seeds Python, NumPy, Torch and module initialisation before agent construction,
  has its own rollout sampler, and starts two environment lanes at `seed + lane`. Sampled
  evaluation uses the existing `(policy seed, world, draw=0)` rule. Shared world panels pair
  deployment comparisons; matching integer seeds alone never creates paired training units.

### Candidate first comparison and the decision still needed

The Root-assigned independent review `/root/dm_allocation_review` (separate context, reported
in the assignment; its full published record is to be read when present) supports question
ownership, rejects the nine-fit menu and automatic all-checkpoint evaluation, and suggests
considering two new seeds of one ordinary recipe after Claude's final curve. That review is
reused for preparation, not represented as scrutiny of an as-yet-unselected confirmation plan.

**Prepared candidate, not a launch decision:** two fresh SET fits, provisionally seeds
`26092711` and `26092731`, each exactly 200 rollouts × 2 lanes × 3000 = 1.2M transitions.
Retain c00 and the existing six checkpoint positions for recovery evidence, but evaluate only
c00 and the fixed 1.2M endpoint c06 on the 32 exposed development worlds in both modes.
No best-checkpoint choice, no automatic extension/retry, no held-out evaluation and no BC
data collection. This is exploratory replication, not a confirmation or a seed-population claim.

The comparison will report each seed's initial-to-endpoint service/J/risk change and endpoint
gaps to the existing H_local/H_central/H_spawn/H_park2/N references on the same worlds, preserving
all adverse worlds and phase splits. H_local is labelled by its actual information and cost;
N's different exposure is displayed. Two fresh fits may show recurrence or heterogeneity;
neither a small spread nor a .03 difference establishes equivalence or a general ranking.
The .03 QoS scale is an inherited practical description, not a new hypothesis-test gate.

If the complete public SET result still leaves a costly recurrence question whose answer
changes the next investment, this narrow comparison is executable. If the final curve or
diagnostics instead points to a more useful ordinary package, revise the design before
running and obtain a focused independent review of the changed choice. No c04–c06 raw reads
or root/owner re-approval is needed to prepare; final recipe selection really depends on
Claude's publication. No fit is bought merely because a slot becomes free.

Prospective candidate cost: **2 started fits**, 2.4M training transitions; 2 seeds × 2
checkpoints × 2 modes × 32 worlds × 3000 = **768k evaluation steps / 256 episodes / 0 updates**.
At the published 168 s per 6000-transition rollout, training is about 18.6 summed node hours;
four two-mode checkpoint evaluations at about 15 min add about 1 h. Preparation, queues,
publication and actual occupancy are separately reported; concurrency speedup is unmeasured.
Prefer `wsl_4070`, one owned result operation at a time initially, subject to fresh admission
and total research/resource occupancy. Checkpoint saving is retained without purchasing
intermediate evaluations. Unknown future costs are not zero.

D4 remains a candidate successor. It requires newly collected observations/actions through
the **energy_relay_diagnostics DM's shared interface**, with explicit proposal versus submitted
teacher targets and the SET held-input contract. Collection, BC optimisation, any RL fine-tuning
and evaluation need separate cost accounting. Retain a closed-loop BC-only reading if chosen.
One BC success/failure cannot isolate representation, exploration, credit and optimisation.

### L0 — prepare the reusable independent-seed path (zero result effects)

Deliverable: a direction-owned B01 configuration and admission-guarded train/evaluate entrypoint
that can execute the candidate above after selection, without changing the benchmark's frozen
entrypoints. Owned code/tests are `experiments/candidates/energy_relay_baselines/b01/` and
`tests/experiments/candidates/energy_relay_baselines/b01/`. New entries live with the direction.
Reuse B02 `make_b02_config`, `collect_and_train`, `new_agent`, checkpoint schedule and the B01
`WorldTask`/`run_tasks` evaluator. Keep learner/host/feedback code shared; do not copy it.

Give new records their own object/direction identity, explicitly separate the two seed outputs,
and preserve per-rollout counts, optimiser steps, initial/final fingerprints, timings and
checkpoint hashes. Evaluate only owned c00/c06 on 955001–955032, both modes, using existing
row/trace/aggregate definitions. The CLI has no hold-out or resume switch. A terminal failure
requires reconciliation and a new explicit decision; saved checkpoints do not automate recovery.
Reject incompatible records/config/seed/checkpoint/bytes before output creation. Store bulk
traces/checkpoints once on the execution node, with compact readable summaries and locators.

Checks: seed isolation through real agent creation, production-config parity, unchanged
collector/evaluator function reuse, actual short native training/save/load/evaluation under
pytest-owned scratch, and rejection of wrong identity/seed/bytes/world/checkpoint before effects.
Reuse existing B02 tests for the unchanged recurrent/proposal/storage contract. No result-bearing
fit or development-panel run is authorised as a test. Independent engineering review covers the
new executable admission/identity/configuration before acceptance. Helpers edit only assigned
code/test files, no notebook or Git index, and never clean another helper's scratch.

### Preparation details (same entry, before results)

The SET critic receives the current central state through `SkillDiscoverer.get_value`; its
team skill is fixed by the MAPPO switch. The actor has 365 current own-observation values plus
a 3234-value held block (306 state + 8 × 365 observations + 8 identity), for 3599 values.
These are implemented input widths/refresh rights, not measured communication traffic.
Radius-gated user/peer/BS records and the always-complete energy suffix follow the benchmark's
corrected observation contract; the older claim that every actor observes all 30 users is
superseded and is not used here.

The DM additionally owns `experiments/candidates/energy_relay_baselines/read_comparison.py`
and its mirrored test while the Implementer owns B01. This is an offline reader of the
already-produced comparison, not a new simulator/evaluator. It will use the existing scalar
metric/gap definitions, fixed development reference filenames, explicit per-seed c00/c06
inputs and source hashes. Missing/duplicate/wrong-world panels must refuse a complete reading;
two training instances remain two units. Report per-seed endpoint and initialisation contrasts,
descriptive seed spread, service–risk conflicts and the phase metrics; do not concatenate
independent fits into the benchmark reader's recovered single-fit curve. Tests use synthetic
JSON under pytest scratch. This adds zero fits and zero environment steps.

### Registration and independent review now published

At main `ce3947efb`, the direction's exploring state, stable lead and this task's routing
are published. The [full independent allocation review and Root disposition](../../archive/2026-09-27/RESEARCH.md#two-dm-allocation-review)
have now been read. Its substantive dissent is against nine fits, automatic whole-curve
evaluation, and D4 as a representation bound; all three are incorporated above. Root's
resolution assigns cross-seed and imitation comparisons here and the shared trace interface
to diagnostics, preserving Claude's accepted operations. This settles the initial ownership
issue; it does not settle whether the still-unread final curve makes replication worth buying.

A thread heartbeat (`s7`, this task) is armed hourly for the real publication dependency.
It checks public NOTES/index only, stays quiet on unchanged state, and stops once the
publication has been handled and the selected continuation has its own observation, or the
investment is closed. There is currently no accepted operation of this direction for a native
launch waiter to observe. Any later accepted run uses `tools/hmasd_wait.py` on its own handle.

### Engineering preparation accepted; no result run selected (02:57 UTC)

The bounded Implementer returned the owned B01 entry, configuration, checkpoint persistence
and evaluation wrapper. The DM reconciled two launcher details before review: launcher-created
metadata may already occupy a fresh output directory, and evaluation consumes an explicitly
identified checkpoint from a distinct training output rather than reusing its claimed output.
Admission precedes candidate imports and scientific effects; the evaluation input includes
checkpoint bytes SHA-256 and training source SHA. Only the two declared fresh seeds and
c00/c06 development panels are exposed by this entry. It reuses the benchmark collector,
learner and default evaluator without copying or editing their implementations.

Independent engineering review by `/root/replication_engineering_review` found no material
entry/configuration/restore/RNG defect. It identified two P2 reader defects: demanding the
nominal maximum transition count would reject legitimate early native depletion, and phase
means without observed-world counts hid their different denominators. The DM fixed both.
The reader now reconciles evaluation summary steps with the sum of actual native episode
lengths, retains termination counts, and records each phase's observed worlds and total steps
beside its mean. Missing phase keys are rejected separately from legitimate absent phases.
The same reviewer independently reran the focused checks and closed both findings with no
remaining material issue in that scope. No additional scientific review or Pro round was
purchased merely to repeat the already-adopted allocation review.

Validation evidence:

- Native entry tests: **18 passed**. These cover real seed isolation, exact production
  configuration parity, an 80-transition test fit, checkpoint save/restore and both evaluation
  modes on short test worlds 317811/317812, plus admission and identity rejection paths.
- The DM's pre-fix combined suite was **29 passed in 39.04 s**; the independent reviewer
  also obtained **29 passed in 40.02 s**. After the reader-only corrections, the expanded
  reader suite was **15 passed in 0.67 s**, independently **15 passed in 0.57 s**.
  Thus the final preparation has 18 native entry and 15 reader cases covered; no unchanged
  native fit test was rerun just to inflate the check count. Existing matplotlib deprecations
  and singleton standard-deviation warnings were non-failing test diagnostics.
- Tests use checkout-owned pytest scratch with automatic teardown. No development or sealed
  hold-out panel was run as a test, and no new result checkpoint/trace was retained.

The earlier 768k evaluation-step estimate is a **maximum**, not a required achieved count:
256 episodes may finish early with native adverse outcomes. About 1 h for four two-mode
checkpoint evaluations assumes the existing 8-worker CPU evaluation shape; the entry's
default is one worker, so a selected launch must explicitly declare and admit its worker
count. Record actual transitions, wall time, memory and all started attempts. Training remains
two candidate 1.2M fits (2.4M transitions, about 18.6 summed node hours). These estimates are
not a commitment to spend that resource before the complete public curve is interpreted.

**Standing:** prepared, with zero new result-bearing fits/evaluations and no accepted launch
handle. The complete published Claude study remains the actual scientific dependency. On
publication, choose the smallest worthwhile comparison or close this candidate investment
with a reason; keep question ownership and revise the direction when evidence warrants it.
The shared evaluator currently has diagnostics-owned work in progress; this preparation uses
its existing default contract. Before any future result launch, inspect the published selected
source and relevant shared changes again. No foreign edit or sealed output belongs in this
direction's source publication.

## 2026-09-27 — Resume DM work and read the published c04 development result

The owner explicitly asked this DM to proceed with research and use observation when needed.
The prepared entry remains available; no result-bearing fit or evaluation of this direction
has yet started. Current public science was checked at `e5a74b3f6d6e86b336fc00e853c7ba1884670f7d`
and again at published main `eda9fae045607dc6e59133fb1bab8f1569744e08`; the intervening changes
do not alter the benchmark readings or this direction's prepared code. Only published development
readings and notebooks were opened. Sealed holdout outputs remain unread.

### Evidence update and the decision it can change

The public [Stage 1 readings](../energy_relay_benchmark/b02_stage1_readings.json) now include
c04 at 804k transitions. Deterministic/sampled QoS is .405685/.403767, up .080788/.058978 from
c03; native J is 1186.77/1179.53, up from 943.95/995.87. Return cost falls from 1.625/4.966 to
.912/1.648. Minimum battery is .110335/.106972: deterministic is lower than c03's .114311,
whereas sampled is higher than .105437. No development world has zero service at c04.
These are conditional observations of the existing recovered training instance, not a new fit
or evidence that all service/risk dimensions improve together.

This materially weakens an early-plateau reading of c02/c03. Ordinary continued training is a
stronger simple alternative to an immediate representation, reward or credit repair. The gain
coincides with changed altitude use and the recovery's reseeded environment/action streams;
the curve does not identify either as its cause. The remaining c04 mean service gap to H_local
is about .19 in both modes, while H_local has much greater return cost. Its .597 service is
therefore still an executed reference, not a same-risk optimum or a required learner target.
The shared [finite-learning distinction](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面)
and [experimental-unit reading](../../RESEARCH.md#6-实证研究是在具体条件下缩小解释空间)
apply directly: neither 32 worlds nor successive checkpoints adds independent training units.

The unresolved investment choice is whether two fresh fixed-1.2M SET runs will change what
ordinary package we retain or try next. A recurrent useful endpoint, recurrent substantial
shortfall, and strongly different endpoints would imply different follow-ups, without assigning
the cause of a shortfall. A still-rising final curve would instead leave the adequacy of this
fixed exposure unresolved. Complete published c06 evidence could therefore change the comparison
or its priority; waiting is a scientific choice to justify, not an approval requirement.
An independent ResearchCritic, `/root/baseline_investment_review`, is reconstructing the public
evidence in a separate context before reviewing this choice and the earlier allocation advice.
It is asked to recommend immediate useful work or a specific necessary external wait, not to
ratify the prepared candidate. No extra Pro round or repeat engineering tests are commissioned.

### Observation correction

The earlier hourly `s7` heartbeat entry above is historical: that automation is now paused.
The owner-requested standalone generic waiter was published at `e5a74b3f6`; the original stable
waiter and control files were not changed by that publication. This thread has one real
`git-publication` observation of the benchmark notebook, with 30-second probes and a 1500-second
checkpoint window. A file change only triggers reading; it does not certify a complete study.
The scientific decision and any resulting launch remain this DM's responsibility. There is no
owned experiment handle to restart, and no accepted Claude operation is touched.

### Independent scientific correction adopted — select the fixed two-fit comparison now

ResearchCritic `/root/baseline_investment_review` reconstructed public JSON and native development
panels before reading this notebook and the allocation review, with `fork_turns=none`. It found
substantial learning in one recovered instance, unresolved recurrence, and a service/risk trade-off.
Its native-panel aggregation also preserves c04 losses relative to c03 on 7/32 deterministic and
12/32 sampled service worlds, and lower deterministic minimum battery on 21/32 worlds. The
reviewer's provenance inspection exposed a public c04 commit subject; no future c05/c06, sealed
holdout or unfinished diagnostics outcomes were read.

**MATERIAL_DISSENT: yes — against requiring Claude's complete publication before selecting this
fixed-budget replication; supports the prepared two-fit investment now.** The decisive reason:
a strong c06 would make recurrence of ordinary competence useful; a weak c06 would leave
recurrence of the fixed-budget shortfall useful; a rising c06 would leave convergence unknown,
but would not answer what independent 1.2M instances deliver. Pending diagnostics add no fresh
training instances. A demonstrated shared-contract defect would warrant correction, while
ordinary path agreement, action-stream variability or wall descriptions do not choose a
replacement training package. Independent-context agreement is not empirical evidence.

**DM adopts the correction in full.** The earlier whole-publication gate was too broad and is
withdrawn. Retain the allocation's narrow one-recipe scope, reject nine fits/all-checkpoint
evaluation, and select B01 now. Claude's curve and the diagnostics remain relevant new evidence,
not prerequisites or approval sources. No unresolved direction disagreement remains. One adequate
scientific review covers this selection; no extra Pro round is useful. The existing 18 native
entry and 15 reader checks and completed independent engineering review still cover unchanged
source. No additional scientific evaluation is disguised as a test.

The concurrent published allocation at `4220ecd4fd2bf867a00777f16960c1c575195c27` transfers the
unexecuted D4/BC successor to `energy_relay_imitation`. Adopt that ownership correction: this DM
retains ordinary RL recurrence and recipe comparisons, does not launch BC or collect its teacher
data, and can use that direction's later published evidence. Earlier D4 candidate entries remain
historical. This transfer does not change the selected SET comparison.

### B01 fixed prospective inputs, costs and reading before launch

- **Training:** seeds 26092711 and 26092731, each one fresh CUDA FP32 fit, 4 Torch threads,
  200 rollouts × 2 lanes × 3000 = 1.2M transitions; 2 fits and 2.4M transitions in this fixed
  batch. Same S7-S2/SET/native reward/production shield and held-input contract declared above;
  retain ValueNorm enabled, with observation/state normalization disabled. The recorded config,
  rather than a broad statement that all normalizers are off, defines the unchanged contract.
- **Execution:** configured `wsl_4070`, one owned result operation at a time initially. Start
  seed 26092711 first, then complete the declared second seed regardless of the first seed's
  scores, subject to owner pause, actual resource admission and technical integrity. No automatic
  retry/recovery of a failed fit and no score-driven extension or horizon change. Accepted work
  on the node keeps its identity. Source and this prospective decision are published before launch.
- **Evaluation:** retain all seven checkpoints as recovery evidence but score only c00/c06,
  both declared modes, all 32 exposed worlds 955001–955032. Four two-mode evaluations, CPU FP32,
  8 workers × 2 Torch threads when separately admitted; 256 episodes, at most 768k environment
  transitions, zero evaluation updates. No checkpoint selection, extra draws or holdout reads.
  Evaluation is scheduled separately from this direction's training to limit contention.
- **Cost:** the prior 168 s/rollout projects 18.67 summed training hours; the resumed process's
  approximately 185 s/rollout projects 20.56 h. Use roughly 18.6–20.6 h as a planning range, not
  a timeout or guarantee. Evaluation adds about 1 h at the declared worker shape. Report actual
  contention, preparation/readback and node occupancy; unknown costs are not zero.
- **Reading:** report each fresh seed's own c00→c06 changes and final service/J/risk vector,
  native endings, phase denominators and all adverse worlds. Historical N has different training
  exposure; H_local has different pooled-information control and high return cost. Neither is
  relabelled as a matched learning arm. The recovered Claude fit is contextual evidence, never
  a third fresh replicate; worlds/checkpoints do not increase training n.

If both fresh instances show useful native gains with the observed risk trade-off acceptable
for the stated use, retain ordinary SET as the working learned comparator and reduce the urgency
of a rescue package. If both retain substantial service/J shortfalls, strengthen only recurrence
of this fixed-budget shortfall and compare a costed exposure/recipe change using the available
imitation evidence; more unchanged seeds have lower marginal value. Strongly different endpoints
make training variability central to the next comparison. Service gains with worse risk remain
a trade-off. These are exploratory action implications, not population-reliability, equivalence,
convergence or mechanism verdicts. Two matching signs or a small spread do not establish them.

## 2026-09-27 04:10 UTC — B01 first fresh fit accepted on wsl_4070

The selected inputs and prospective decision were published at
`8137cb9111746c425ee4161645f12d1e3facb533` before a single supervisor submission. Native admission
accepted seed 26092711, operation `983cf54937c5d5f9eaa4fcdd8c159ec2367fba8da58fa039db12c5d5786107f9`.
The supervisor's successful return means the detached runner was handed off, not that training
finished. Native status at 04:11:33 UTC showed matching running supervisor/runner identities,
consistent records and no exit witness. Initialization c00 was saved; that observation had
0 completed rollouts, 1 checkpoint and no reported failure, so it is not a learning result.

[Manifest](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092711/launch-manifest.json),
[fresh resource check](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092711/admission-preflight.json),
[actual config](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092711/config.json) and
[initial native status](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092711/launch-status.json)
retain the exact command/source/node/output/operation identities. The actual config confirms
CUDA FP32, 4 Torch threads, the declared seed and 1.2M exposure, and actor input width 3599.
Admission measured 13,102,297,088 available bytes against the 4 GiB floor. Checkpoints and full
training streams remain once at the manifest's durable node output; only compact control/config
records were copied and byte-hash verified locally. Actual started fits are now **1 of 2**;
the second fresh seed and all declared development evaluations have not started.

The node synchronized without overwriting Claude's modified live summary. Its pre-existing
Git auto-GC warning about historical tree `9e40125ee3e24973b69754649226d18847b45862` remained;
no GC repair/deletion was attempted. Current source preparation and native admission succeeded.

`tools/hmasd_wait.py` is armed with this same native operation reference, 30-second probes and
a 1500-second checkpoint window. Checkpoint events rearm observation without restarting the fit.
The generic publication watcher first delivered its real 25-minute checkpoint through queue;
generation 1 / wake `bc408f7c-b75d-48ca-8414-f5c788021673` was drained and acknowledged. That
publication observer was then stopped after the native run observer was registered, because
the withdrawn publication gate no longer warrants a separate wait. The standalone generic
tool remains published; no stable waiter, skill, role or control file was changed here.

### 2026-09-27 04:28 UTC — restore observation of the same accepted fit

The first native observer wake was BLOCKED after three unknown status reads, with reason
`manifest has no native-observation host binding` and `manifest_ref: null`. This was an
observation failure, not an exit witness. The node's claim still identified the accepted fit;
direct host/boot/PID/start-tick checks matched the original manifest for both supervisor and
runner. The live summary recorded 18,000 transitions, 3 completed rollouts, 6 episodes, one
checkpoint and no reported failure. No result interpretation or new launch followed this wake.

The node had advanced to `27b796888f4c5464bd7ed888fdc6fdce2cdaa747`. Its sparse selection omitted
this run directory: published `launch-manifest.json`, `admission-preflight.json` and `config.json`
were absent from the working tree although their Git objects and retained local copies existed.
The running summary/progress and original admission claim remained present. The status/launcher
source had not changed relative to the accepted source. These facts identify missing observation
records rather than a new host, a changed binding or evidence of a stopped worker.

Under the node's shared Git lock, added only
`runs/energy_relay_baselines/b01_set_a01/seed-26092711` to its sparse selection, retaining every
previous selection. All three restored records matched the originally published bytes by
SHA-256; the manifest hash is `7f2f38e9d393611c945fda1fe889479157c1502fec3d408f078b40191248561c`.
The original claim bytes and native process identities were unchanged. The same status command
then returned accepted/running, consistent records and no exit witness at 04:28:14 UTC.

Consumed generation 1 / wake `63f98163-44bc-49d5-8e3d-b3a0a6812f50` and resumed only the resolved
observer job with `--resume-jobs`, producing generation 2 and another 1500-second window.
Its operation reference and probe argv are unchanged; no worker, fit, checkpoint or submission
was restarted. Future runs in this fixed batch will retain their own output directory in the
node sparse selection before publishing compact records. No stable control code was edited.

## 2026-09-27 — diagnose the first fit's technical failure and prepare continuation

Owner requested diagnosis and preparation for later continuation. The same accepted operation
has a valid exit witness (exit 1, 2026-09-27 08:12:10 UTC). Its final summary and progress agree
on 72 completed rollouts, 432,000 transitions and 144 native episodes; additional partial-rollout
work is unmeasured. Runner wall was 14,092.577 s. The failure is `SystemError:
Objects/listobject.c:2529: bad argument to internal function`, reached while constructing an
environment observation through NumPy `clip`. This traceback identifies the failure site, not
its root cause. c00/c01/c02 checkpoint bytes match their recorded hashes; c02 is at 402,000
transitions. The compact [terminal observation](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092711/terminal-observation.json)
retains native identities, exit, traceback and verification. Bulk outputs stay on the original
node. No endpoint exists, so this is incomplete technical evidence, not a SET result.

The observer's 07:37 UTC checkpoint notification timed out in `codex queue`; its persisted
delivery is unknown. The old controller then stopped probing at its window boundary. Manual
reconciliation found the later native exit and stopped the observer. The failed worker and its
submission will not be restarted by observation recovery.

Preparation scope: reconstruct the failing input path and runtime/checkpoint limitations;
perform bounded technical checks without new fits or scored evaluation; independently review
any executable repair; and write an explicit next-attempt decision with the original failure's
cost preserved. Do not treat a checkpoint restart without full environment/RNG state as a fresh
replicate or exact continuation. The second declared seed and all evaluations remain unlaunched.
This preparation request does not itself start a replacement learning run.

The bounded observer repair covers `tools/hmasd_wait.py`, `tools/codex_wait.py`, their existing
skill tests, and the standalone usage note: keep read-only probes alive after a checkpoint while
its notification awaits acknowledgment, including an uncertain delivery; retain later terminal
facts without blindly resending queue or reviving terminal jobs. Preserve one wake, generation,
drain/ack ownership and explicit stop/cancellation. Validate with fake queue/probe regressions
and independent engineering review. No learner, environment, frozen source or other direction's
outputs are changed merely to hide this exception. A real current-session queue check, if used,
will be submitted once and reconciled under its own diagnostic identity.

### L0: preserve the next exception's local evidence without changing learning

The bounded source reconstruction found a scalar SINR path and no demonstrated bounds/lifetime
defect in the inspected native radio routine. Actual node metadata is Python 3.10.21 (custom
Clang build) and NumPy 1.26.3; one ordinary scalar clip control passed. The failed scalar value
and frame locals were not retained, and an upstream release's C line number does not by itself
identify the custom build's failing function. The shared runtime diagnosis in RESEARCH also
contains earlier failures with different immediate paths and no identified common cause.

Add failure-only forensic capture under `experiments/candidates/energy_relay_baselines/b01/`
and matching tests: preserve traceback locations and an explicit small allowlist of scalar
SINR/clip and collector position fields, plus interpreter/library identity, in a compact
`failure-context.json` bound from the existing summary. Enable Python faulthandler in the
admitted training entry. Do not dump arbitrary locals, tensors, full environment state or secrets;
do not call custom repr methods, draw RNG, retry exceptions or alter NumPy/environment/learner
semantics. Diagnostic-write failure must not replace the original training exception. Tests
inject a failure through the existing runner and check original re-raise, counts, context,
RNG preservation and bounded serialization. This increases the next failure's diagnostic value;
it is not a demonstrated repair of the original SystemError and adds no scientific fit.

### Diagnostic findings and independent continuation decision

Scout `/root/b01_crash_recon` reconstructed the frozen input path and the configured node
without a fit or scored evaluation. The source produces scalar SINR (including the declared
`-inf` unavailable-link value); inspected radio-array shape/lifetime checks reveal no demonstrated
out-of-bounds defect. No failed scalar value/type was saved. The interpreter executable resolves
to `/home/wu/.local/share/uv/python/cpython-3.10.21-linux-x86_64-gnu/bin/python3.10`, build-ID
`afb5e1790bd84db7ed2c50d21b86fd33a96784bf`. It has no usable line table. Targeted disassembly finds
the reported file/line and invalid-argument guard at `PyList_AsTuple` (entry `0x1680b0`, error call
`0x1680f7`) and another matching site in `PySequence_Tuple` (`0x155dbd`). This narrows the failure
to a CPython sequence-conversion boundary, without uniquely selecting the native caller or
establishing why it received an invalid argument. Mapping the custom binary by an upstream
release's line 2529 alone would be incorrect.

The expected radio extension cache is
`/tmp/hmasd_uav_cpp_extensions/build_6219ac65a6c895a1/source_1ff1eecb1c4a69ec/`;
its staged C++ source SHA256 is
`1ff1eecb1c4a69ec402f4f2a506dca830e140844f8ed9c56f52e2c99c94791dd`, matching the frozen input.
This is an on-disk correspondence, not proof that the failed process loaded that exact binary.
A bounded kernel-log check for the matching boot, 07:50–08:20 UTC, found WSL network and dxg
query messages but no OOM/kill/segfault/Xid match. It neither establishes the root cause nor
certifies the runtime/hardware as healthy. No interpreter, library, environment or driver was
replaced. The earlier B08/B18 evidence remains relevant context with an unknown common cause.

Independent ResearchCritic `/root/b01_failure_route_review`, with a separate context, read the
original-node terminal records, progress and checkpoints before this diagnosis. It confirmed
432,000 completed transitions and 162,000 recorded steps for each low-level optimizer; partial
rollout exposure remains unmeasured. Frozen `save_model` retains learner, optimizer, normalization
and rollout-sampler state, but not collector environments or the global environment/action RNG
streams. Resuming c02 would discard at least 30,000 completed post-checkpoint transitions and
add 798,000 transitions from reset streams. It cannot restore the original fresh-run contract.

The reviewer independently aggregated development worlds 955001–955032: the earlier recovered
SET's c00→c06 QoS rises from .209/.243 to .437/.438 and J from 587/693 to 1276/1281
(deterministic/sampled). H_local gives .597 QoS and J 1628 despite higher return cost. Sources are
the [c00 development panels](../../../../runs/energy_relay_benchmark/b02_s1_eval_c00_a01/checkpoint-eval/panels/)
(recorded source `759927b5e8caa0ba5bd8ba505ab5388985f6a2fa`),
[c06 development panels](../../../../runs/energy_relay_benchmark/b02_s1_eval_c06_a01/checkpoint-eval/panels/)
(`c369a6b91651ece4bdfbbedce1be26cd0599baff`) and
[H_local reference](../../../../runs/energy_relay_benchmark/b01_ref_a02/summary.json)
(`e1fdbe72f53a1597c34c1d32c89ac6700251dca0`, `reference/Hlocal_e0.00_x0.05`).
These support a useful ordinary learner plus a remaining native-J gap; they do not identify
representation, credit assignment or insufficient exposure as the cause. H_local's pooled
planning information and the recovered fit's lineage remain comparator limitations. The reviewer
encountered published holdout aggregates in the shared index but opened no sealed raw outputs;
those aggregates do not inform this decision.

**MATERIAL_DISSENT: no; recommendation adopted.** Retain the question and prepare the untouched
second seed **26092731** at the unchanged 1.2M recipe. The first endpoint remains missing: do not
impute zero, assume random missingness, substitute c02, pool nested worlds into extra fits, or
automatically purchase a replacement/recovery. No training or scored evaluation is launched by
this preparation. The next complete observation, when execution continues, is that seed's own
c00/c06 in both modes on the same 32 exposed worlds, CPU FP32 for evaluation. A useful endpoint
supports retaining that fresh instance; a recurring shortfall adds bounded evidence without
establishing its mechanism or convergence; a strongly different endpoint makes trajectory
sensitivity consequential. Another technical failure calls for a specific action based on the
new forensic evidence, not automatic seed substitution. Extra short stress runs are not selected:
an uneventful scalar check or short rollout would not resolve this delayed failure.

Cost already incurred is one started fit, 3.915 runner hours, 432,000 recorded transitions and
unmeasured partial-rollout/support work. The next original fit remains one fit and 1.2M transitions;
linear projection from this attempt is about 10.9 training hours, with substantial uncertainty.
Its complete c00/c06 evaluation is 128 episodes, at most 384,000 environment steps and zero
updates. Historical c00/c06 evaluation summaries record 787.659546 + 1718.187218 seconds =
0.6961 hours at CPU/8 workers/2 Torch threads; contention and preparation are separate. There is
no claim that the original two-fresh-endpoint comparison can now be completed without a new
prospective decision about its missing first cell.

### Observer repair and actual current-session delivery

Both waiters now continue bounded read-only probes while a checkpoint wake awaits handling;
late terminal evidence is retained under the existing wake, including unknown delivery. An
expired Pro observation retains a full bounded long-poll budget; outstanding probes cannot
suppress the checkpoint. Native rearm also requires prior drain. There is no automatic queue
resend, worker restart or revival of terminal jobs. Implementer checks passed 85 waiter/adapter
tests; independent Engineering Reviewer `/root/wait_repair_engineering_review` accepted both
corrected findings (Pro budget and outstanding-probe checkpoint) with no material finding left.
Tests use fake queue/probes, including virtual Pro startup and four spaced stable samples;
they are not a live browser test. Synchronous queue submission can still delay stop handling
by its bounded 20-second timeout.

A single owner-authorized current-session delivery diagnostic used the running App's executable,
`/mnt/c/Users/fires/.codex/bin/wsl/7d1db4ccd85248a5/codex` (0.158.0-alpha.2.1), with inherited
`CODEX_HOME=/mnt/c/Users/fires/.codex`. It returned queued, and diagnostic
`60d4c3cd-d5db-45a7-bdfc-051a9483c03e` was actually received in this session. Receipt is recorded in
`temp/directions/energy_relay_baselines/wait/queue-diagnostic-20260927.json`; no reply queue was sent.
PATH's standalone CLI is 0.157.1; this current routing difference does not prove the historical
timeout's cause. Future observation must select the verified current App executable explicitly
and refresh that path if the App changes. Neither queued status nor a 25-minute checkpoint
guarantees a service-side prompt-cache hit. The failed operation's observer remains stopped;
no rearm of it was performed during preparation.

### Engineering acceptance and prepared source boundary

The failure-only B01 capture is implemented in `b01/diagnostics.py` and bound by SHA256 from
the summary. It records bounded traceback/allowlisted scalar fields, stored versus partial
collector counts, runtime versions and already-loaded native-module paths, including Torch
extensions held only in the loader caches. It does not import/compile another extension or
change the successful numerical path. The admitted CLI enables faulthandler before candidate
imports. It cannot recover Python locals after a hard crash, and a storage failure can still
leave evidence incomplete. The original training exception now remains governing if diagnostic,
final-summary or progress writes fail; finalization errors still propagate on an otherwise
successful run.

Engineering Reviewer `/root/wait_repair_engineering_review` identified and rechecked both
material fixes: loader-cache identity capture, and persistent storage failure masking the
original exception. No material finding remains. The B01 suite passed 27 checks before the last
test expansion; the final 10 focused diagnostic cases passed, covering partial collector
counts, hash binding, bounded capture without custom repr, RNG preservation, cache-only
module discovery, broad ENOSPC, successful-path write failures and faulthandler order. These
are engineering fixtures, not additional research fits or scored development evaluations.

Before choosing a new published source, compared the reachable imports against first-fit source
`8137cb9111746c425ee4161645f12d1e3facb533`. At published main
`5050c3a8b4b71ff693827f75a7a11a6ee776436e`, the only relevant inherited changes are the B02
optional Recipe/construct/record hook and the shared learner/buffer's opt-in surrogate mask.
Independent review confirmed that B01 calls `construct=None` and `record_hook=None`, sets no
`_shield_surrogate_experiment`, leaves the buffer mask `None`, and uses its own checkpoint writer.
The default loss, clipping, storage, sampler and checkpoint semantics remain the original path.
Four focused checks (both samplers, default/unmasked update and RNG, production recipe/seed
isolation) passed in 6.18 seconds, alongside the published DM2 checkpoint-compatibility evidence.
CPU checks and code inspection do not establish a historical-SHA or production-CUDA bitwise
trajectory guarantee. The preparation introduces no environment/reward/horizon/seed change.

The committed source introducing this entry is the source to pin in the saved, unsubmitted
second-seed request under `temp/directions/energy_relay_baselines/launch/`. A future launch still
refreshes current direction control, actual node memory/resources and duplicate-claim checks
through `hmasd_launch`; its accepted manifest supplies the operation reference for observation.
No acceptance, worker or second-seed scientific output is claimed here. Keep the old observer
stopped until its stale observation state is reconciled through the supported workflow when
future work actually requires that state. Do not blindly reapply sparse checkout: the shared
index records that doing so can remove other completed directions' ignored bulk. Preparation
does not change the node's sparse selection or another direction's retained artifacts.

The exact old launcher snapshot's reclamation preview was refused because generated
`envs/native/__pycache__/` and `envs/pettingzoo/__pycache__/` remain. A read-only process-reference
check also cannot inspect `/proc/660/cwd` under the current account. No deletion or privileged
retry was performed: snapshot `991be7f5fde844678030c9fab5f89291` remains at its original node path,
with measured allocated size 795,213,824 bytes; reclaimed space is zero. Required outputs,
claims and the compact terminal record remain outside that snapshot. This leftover does not
mean a worker is running or that cleanup succeeded.

## 2026-09-27 — execute the untouched original second seed after preparation

Continue within the owner's earlier instruction to proceed with this research and the declared
two-seed scope. Root's coordination message requests actual continuation and reports DM2's new
failure; it supplies evidence and coordination, not permission to add a fit, restart seed1 or
lift a pause. Current RESEARCH at `c9842cbbe` retains the lifted owner pause and this direction's
active state/unchanged lead. The earlier preparation-only entry describes that completed turn;
the selected next action is now the untouched original seed **26092731**, not a replacement.

The new [DM2 A02 diagnosis](../energy_relay_diagnostics/NOTES.md#b02-a02-cache-failure-engineering-diagnosis-2026-09-27),
published at `4fdb5e77c`, records ordinary PPO failing with the mask off after 126,000 new
transitions / 3,371.235 s. Its immediate path is a bool at the communication-cache signature
lookup; reviewed writers only store None/dict, and the origin is unresolved. This is not the
same immediate failure as B01's sequence-conversion SystemError. No common cause or shared
semantic defect is established. DM2 owns that cache investigation; this DM changes no shared
environment code and introduces no silent fallback, exception retry or arbitrary library swap.

ResearchCritic `/root/b01_failure_route_review` reviewed this evidence delta using its completed
independent reconstruction. **MATERIAL_DISSENT: no; recommendation to execute the untouched
original second seed retained and adopted.** The additional failure lowers feasibility
confidence and increases uncertain expected completion cost, but does not identify a specific
discriminating prerequisite for this observation. Injecting invalid cache values explains the
exception, not its origin; a short passing run cannot establish long-run integrity. DM2's own
decision to diagnose before repeating its failed comparison is not a project-wide prerequisite.
A demonstrated shared semantic defect would change this decision; another B01 failure will be
read from the new evidence before any different technical investment, with no automatic seed
substitution. Completing this seed would yield one fresh complete endpoint and one missing
endpoint, not repair the original two-endpoint study.

Use already published source **`4a3e309f5e8e229eb6c0bc6e5de7008cc338dead`**, whose forensics,
observer changes and default semantics have independent engineering acceptance. The reachable
scientific/launcher imports have not changed between that source and the current preparation.
No unchanged test suite or extra scientific smoke is purchased. The fixed contract remains
1.2M training transitions, CUDA FP32 / 4 Torch threads, c00 and c06 only for development
evaluation, both modes, worlds 955001–955032, CPU FP32 / 8 workers / 2 threads: 128 evaluation
episodes, at most 384,000 steps and zero evaluation updates. Rough cost remains 10.9 training
hours plus 0.70 evaluation hours; failure probability, contention and support costs are unknown.
Seed1's 3.915 hours and missing endpoint remain charged; DM2's 0.936 hours is separate evidence,
not cost silently assigned to this study. Native admission supplies the fresh resource check.

The configured node has the same boot, an idle GPU, about 14.56 GiB available memory at the
preparation read and no second-seed output yet. These observations are not admission. Fetch
published objects without a checkout/sparse-selection change, preserve the node's existing
dirty records, then submit the exact new-seed request once. Reconcile the stopped stale observer
against seed1's terminal status through drain/rearm without `--resume-jobs` or a worker launch;
register the new accepted operation only from its verified manifest. Use the verified App CLI
for 1500-second checkpoints and 30-second read-only probes. No App-task ACK or reply is sent.

### Second original seed natively accepted and observed

Seed **26092731** was accepted on **2026-09-27 at 12:45:51 UTC** from the declared source
`4a3e309f5e8e229eb6c0bc6e5de7008cc338dead`, after one submission. Its native
[manifest](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092731/launch-manifest.json)
binds the operation reference, immutable source snapshot, original-node output and process
identities. The collected [status](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092731/launch-status.json)
verified the runner and supervisor identities as running with consistent records and no exit
witness. Native [admission](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092731/admission-preflight.json)
passed with 14,852,599,808 available bytes against a 4 GiB floor. The actual
[configuration](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092731/config.json)
confirms seed 26092731, CUDA FP32, four Torch threads, actor input width 3599 and the unchanged
two-lane / 200-rollout / 3000-step recipe (1.2M transitions). Manifest, preflight and config
bytes were collected from the admitted output and verified against their node-side SHA256.
Raw outputs remain at the single canonical node location recorded by the manifest.

The initial training summary had c00 and no completed rollout; this is startup evidence, not
a scored endpoint. This study now has two started fits: the first is a preserved technical
failure with a missing endpoint; the second is active. If training completes, verify produced
checkpoint bytes/source and execute the already-declared own-c00/c06 evaluation. There is no
replacement fit, checkpoint recovery or automatic retry in this acceptance.

Before registering the new handle, the old observer's generation-8 checkpoint was drained and
reconciled by read-only native status. The resulting generation-9 terminal event confirmed the
first operation's valid exit 1 and absent processes; it was acknowledged without `--resume-jobs`.
The first job remains failed. The new accepted operation is observed by the canonical per-session
controller at generation 11, using the verified App executable, 30-second probes and a
1500-second checkpoint window. A real native probe confirmed the new operation running; the
latest checked probe at 12:54:31 UTC still matched both process identities. This controller
continues observation across checkpoints without worker restart. Queue delivery and checkpoints
do not establish a service-side prompt-cache hit.

Node preparation fetched published Git objects only. Its existing dirty records and sparse
selection were preserved; no checkout or broad sparse-selection update was performed. This
routine acceptance record adds no scientific result or change to the published comparison.

## 2026-09-27 — second original seed failed; both fresh endpoints remain missing

The unchanged second fit, seed **26092731**, terminated with **SIGSEGV / exit -11**. The native
exit witness records **18:52:48.485 UTC**; the runner and supervisor identities are both absent
and the operation records are consistent. The verified
[terminal observation](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092731/terminal-observation.json)
contains the full faulthandler stderr, native exit/status, last completed rollout, per-file
hashes and original-node locations. It was collected as a compact record and its bytes checked
against the collection-side digest; the already-published config/manifest/preflight still match
their node bytes. Bulk remains in the original output directory, outside the disposable source.

The last fully recorded state is **858,000 transitions / 143 rollouts / 286 native episodes**,
with 321,750 low-actor and 321,750 low-critic optimizer steps. Partial rollout 144 exposure is
unmeasured. All five existing c00–c04 checkpoint hashes match their summary bindings; c04 is
804,000 steps. There is no c05 or c06 endpoint. The summary remains `INCOMPLETE` with
`failure: null`, and no `failure-context.json` or final CPU/RSS/training-wall fields were written.
These are preserved consequences of signal termination bypassing Python exception/finalization
code, not evidence of success or zero resource use. The failure-only exception recorder cannot
recover locals after this hard crash; faulthandler did retain the Python stack.

The top Python frame is frozen `routed_core.py:1229`,
`np.any(self.connections[:, user_idx])`, reached through native environment stepping in the
collector. Scout `/root/b01_crash_recon` mapped this boolean-array reduction and the earlier
radio/backend path. The relevant environment and native C++ source is byte-identical between
the first and second source revisions, but the first fit's `np.clip`/CPython sequence-conversion
SystemError and this reduction-time SIGSEGV are different immediate failures. Source inspection
found no specific invalid view or demonstrated memory-lifetime/bounds defect. It does not
establish healthy process memory, a NumPy defect, earlier C++ corruption or a common cause.
The SIGSEGV site is a fault boundary, not a root-cause diagnosis.

The second fit's **native acceptance-to-exit interval is 22,016.758 seconds (6.1158 hours)**,
including initialization and terminal handling; exact final training-only wall/CPU/RSS remain
unmeasured. The comparable first native interval is 14,529.286 seconds (4.0359 hours), while
its separately finalized training wall was 3.9146 hours. Thus the two native intervals sum to
**10.1517 hours**, not a homogeneous sum of measured training-only time. Total cost is two
started fits, **1,290,000 fully recorded training transitions**, plus unmeasured partial
rollouts and support work. This study has **zero complete fresh 1.2M endpoints and zero new
scored evaluation episodes**. Its two-seed recurrence question remains unanswered. Intermediate
training rewards/checkpoints do not replace the predeclared own-c00/c06 development comparison;
the failures are not zero scores or evidence that ordinary learning has no value.

The terminal notification was read with the artifacts and acknowledged against its exact
generation/wake/event. Generation 23 has no pending events and no active jobs; both original
fits remain failed. No worker was restarted, no partial checkpoint evaluated, no replacement
fit submitted, and no App-task message sent. The detached observer successfully retained and
delivered this terminal event. The current published background used for the next decision is
`834d400967a72bf8b07c23bf2307956bfe7c216b`: ordinary SET's prior recovered endpoint remains a useful
conditional baseline; finite-learning versus representation claims and incomplete runtime
comparisons retain their limits. The current planner/learning/credit questions have other
owners, and DM4's runtime/cache work is reserve rather than an active dependency. A focused
independent scientific review and bounded original-dump search address the next investment.

### Independent reading and DM disposition: end B01 replenishment

ResearchCritic `/root/b01_failure_route_review` continued its prior separate-context review,
reading both terminal records and frozen configurations before the current explanations; it
opened no sealed raw outputs. Its consequential update is zero complete fresh endpoints from
two started attempts, with real learning updates and failure costs preserved. The completed
recovered SET result still demonstrates conditional learning; ordinary planners still show
useful service within their information/control contracts. This batch resolves neither
fresh-fit recurrence nor a representation, gradient or optimization mechanism. The different
failure sites increase practical concern about obtaining uninterrupted endpoints on this runtime,
without identifying NumPy, CUDA, hardware or SET as the cause.

The review considered three concrete continuations. Another unchanged remote fit would buy
the same unresolved endpoint for roughly 8.5–10.9 hours before evaluation, with unknown
completion probability and no technical intervention. Checkpoint recovery would alter the
trajectory and reproduce the already-known limitation of the recovered ordinary reference.
Neither is selected. A complete `local_linux` CPU attempt is technically available and is the
strongest alternative: one new 1.2M fit plus 128 evaluation episodes / at most 384k steps. Its
full-size CPU training cost is unmeasured. The reviewer checked Python 3.10.20/Clang 22.1.3,
NumPy 1.26.3 and Torch 2.7.0+cpu there; changing machine, Python patch and device while retaining
shared source/runtime ancestry would be an operational alternative, not a clean causal test of
the original fault. Success would supply one complete CPU-trained instance, not a cause or
population reliability; failure would still not establish low policy value. It is declined for
its current marginal use relative to its whole cost, not until a runtime-health proof is supplied.

Current ownership makes that choice concrete: DM2's ordinary availability controls and DM3's
P/H versus learned-value comparison do not depend on these missing SET endpoints. Claude's
withdrawn assignment/credit fits no longer create that immediate dependency; DM4's cache work
is closed, not a producer to await. Reuse complete ordinary SET/planner references where their
actual contracts match. Do not enter another lead's study or invent a replacement question to
fill a runtime slot. Retain only the already-commissioned bounded original-core collection;
no stress fit, getter repeat, package swap or standing runtime investigation is selected.

**MATERIAL_DISSENT: no; recommendation adopted.** End the current B01 replication/replenishment
investment as an incomplete batch. Keep the broader ordinary-learning question in **reserve**,
with no selected next result operation, queued retry, unresolved Pro or external dependency.
This is not a scientific rejection of SET, an inference of random censoring, or a requirement
that all runtime faults be solved before other credible research. The earlier continuation
advice covered the original second seed and does not extend to a third. Any later investment
needs a new concrete use/comparison and prospective cost; no automatic re-entry is scheduled.


### Original core: bounded inspection completed, no causal repair selected

Scout `/root/b01_crash_recon` found the original dump on `hmasd-wsl-node`, outside both
source snapshots, at
`/mnt/c/Users/wu/AppData/Local/Temp/wsl-crashes/wsl-crash-1790535138-823176-_home_wu_.local_share_uv_python_cpython-3.10.21-linux-x86_64-gnu_bin_python3.10-11.dmp`.
It is a readable ELF64 x86-64 core, **2,625,273,856 bytes**, mtime
`2026-09-28 02:52:48.406528400 +0800`; its in-place SHA-256 is
`e797368713e44b40e257363e59479afcd0c8a31c03836621f41d45c04271680c`.
The original is retained as the single copy; nothing was copied, patched or installed.
Its location is the node's Windows Temp crash store, not a newly established durable archive.

The bounded GDB invocation used the existing `/usr/bin/gdb`, `-nx -batch`, auto-load and
debuginfod disabled, pagination off, and `libthread-db-search-path /nonexistent`; it opened
`/home/wu/.venvs/hmasd/bin/python` and the exact core, then read `bt 12` and registers only
(no live attach or execution). Initial metadata inspection also read file/thread/process/shared
library information. GDB reports SIGSEGV and current LWP **823176**, matching the native runner.
The reported stack is `pthread_kill -> raise -> faulthandler_fatal_error -> <signal handler>`;
its interrupted frames are `PyErr_Format -> type_getattro -> PyObject_GetAttr ->
get_array_function -> get_implementing_args_and_methods -> dispatcher_vectorcall ->
_PyEval_EvalFrameDefault -> _PyFunction_Vectorcall`. This is consistent with a fault during
NumPy array-function dispatch's Python attribute access, followed by faulthandler re-raising
SIGSEGV; it does not show why the earlier operation failed.

**Binary-identity limits remain material.** GDB explicitly warns that the core may not match
the specified executable and that current `libcuda.so.1` has a different build ID from the core;
it also reports a missing deleted `/dev/zero` mapping. The current Python has build ID
`afb5e1790bd84db7ed2c50d21b86fd33a96784bf`, but this pass did not bind it to core-resident GNU
notes. The available `readelf` could not decode the 64-bit NT_FILE note. Consequently the native
symbol names are best-effort readings against current files, not proven identities of the
core's Python, NumPy and libc. B08's separately established Python identity cannot fill this gap.

The original node's `/var/log/syslog` at `2026-09-28T02:52:18.909732+08:00` records fatal signal
11, followed at `.913425` by WSL CaptureCrash for PID **823176**. The CPU line instead names
PID **831518**; preserve that discrepancy. The signal-frame RIP is `0x7ac4b5e9ec0c`, with
RDI/RSI/RBX 823176 and RDX 11; syslog ORIG_RAX is `0xea`. These fit a signal re-raise and are
not proof that this is the original faulting instruction. Neither the source inspection nor
this bounded core reading establishes a common cause with the first seed, B08 or B18, a
NumPy/CUDA/hardware defect, or a verified repair. The helper is finished and no longer uses
source snapshots. This completes the selected diagnostic work; the no-replenishment decision
above stands, without opening a continuing debugger or runtime-health project.


### B01 retirement and measured reclamation

No live operation or helper consumes B01 source now. A source/config consumer search found
only this candidate's own imports and tests; its comparison reader is also fixed to the two
failed seeds and missing c06 endpoints. Under constitution sections 4/9, the unused six
candidate Python files and three tests leave current main. Their complete frozen form remains
recoverable at source
[`4a3e309f5e8e229eb6c0bc6e5de7008cc338dead`](https://github.com/CartmanFatass/My-paper-code/tree/4a3e309f5e8e229eb6c0bc6e5de7008cc338dead/experiments/candidates/energy_relay_baselines).
No shared observer, native environment, optimizer or launcher code was changed in this retirement.

On the original node, the supported snapshot collector first refused the first snapshot's six
ignored `.pyc` files; a read-only process scan found no consumers and a tracked-file check
confirmed those exact cache files were disposable. After removing only those caches, both
explicit snapshot previews were eligible. The collector's `--apply --sudo-process-scan`
rechecked terminal witnesses, absent processes, matching claims, external output retention,
durable source reachability and clean contents under the admission lock. It removed
`991be7f5fde844678030c9fab5f89291` and `8bcd2e133ae248c39d7e0ef5258ce01c` without force.
The final check confirms both paths absent and no longer registered as worktrees. Their
pre-cleanup allocated sizes were **795,213,824 + 797,949,952 = 1,593,163,776 bytes**;
remaining allocated bytes for these two targets are **0**. No archive or replacement copy
was made. Claims, manifests, exit witnesses, all three/five original checkpoints and raw
run files remain at their original node paths. Fresh native status still returns valid exit
1/-11, absent runner/supervisor and consistent records after source reclamation. Raw summary
hashes still match the compact observations; the original core is still present with unchanged
size and mtime.

Local candidate code/tests and direction scratch measured **180,224 + 192,512 + 40,960 =
413,696 allocated bytes** before retirement and **12,288** afterwards: **401,408 bytes freed**.
All nine source/test files, fifteen owned `.pyc` files and five obsolete launch/wait request
files are absent. The only retained file in direction scratch is
`temp/directions/energy_relay_baselines/wait/queue-diagnostic-20260927.json`, preserving the
owner-authorized transport receipt. The canonical observer state/history is retained outside
that scratch root and has no active job or pending event. The two original run directories
and original core are deliberately retained evidence, not failed deletion targets.

Across these explicitly measured cleanup targets, allocated usage fell by **1,593,565,184
bytes (about 1.484 GiB)**. This is a target-allocation delta, not whole-host free-space or
Git-object accounting; the new compact 22,699-byte terminal record and appended notebook
are separately retained evidence. No whole-tree backup, copied bulk or tarball was created.
Verification for this retirement is the frozen-source/consumer check, actual path and worktree
removal, original artifact/status checks, JSON integrity and publication diff check. No new
scientific fit, environment step or behavior-changing test was needed.
