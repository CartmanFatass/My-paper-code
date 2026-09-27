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
