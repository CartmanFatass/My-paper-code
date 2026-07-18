# HA-CTSE Implementation Plan

Purpose: staged core-algorithm work only. The binding research target, S7-S1
parity definition, baseline hierarchy, promotion ladder, and failure-review gate
live in `memory/ALGORITHM_PRINCIPLES.md`; they are not repeated here.

## Task 1: Iteration 3 Existing-Checkpoint Skill-Semantics Audit

Status: COMPLETE. The reviewed analyzer and direct-script regression passed 18
focused checks; the controller-owned offline invocation terminated validly as
`F_UNDERPOWERED_OR_UNIDENTIFIABLE`.

### HMASD Contract

Goal: distinguish whether terminal Stage C F1 contains a checkpoint-local,
persistent skill-conditioned action process, whether that process keeps its
relative meaning across lifecycle nuisances, and whether naturally assigned
segments enter the same coarse action-process regions. F1 alone selects the
scientific branch; F0 runs the identical analysis only as a matched diagnostic.

Evidence is strictly offline and read-only. Inputs are each arm's
`result/stage_c_arm.json` and `checkpoints/update_250_live.pt` under
`logs/f0f1_dynamic_roster_stage_c_20260717_221247`. No optimizer, collector,
environment, reward helper or new rollout is allowed. Only the first two forced
effect dimensions are read; the third primitive-action occupancy is
`1 - q0 - q1`. Reward, utility, wave, owner, progress, contact, success, role
and the task-effect dimensions are prohibited.

The audit may establish only local `do(z)` policy dependence, 12-active-step
action-mode stability and late-training natural-context overlap. It cannot
establish environment-independent transition semantics, transfer, cooperation,
commitment advantage or hierarchy superiority over Stage B.

### Binding Evidence-Sufficiency Revision

The pre-execution artifact mapping established that the registered forced
result stores only the aggregate tensor `[128,3,2,4]`; it does not retain each
forced snapshot's observation, recurrent state, lifecycle/event metadata,
primitive legal support or a key shared with the natural ledger. The natural
low ledger retains final-rollout observations and recurrent state but no
per-row source episode or forced-snapshot alignment. Consequently the full
stability and natural-overlap estimands below are not identifiable from the
existing artifacts without a new rollout, which this iteration forbids.

This iteration therefore performs an evidence-sufficiency audit before any
full semantic estimator:

1. validate both registered arm results and both schema-3 live checkpoints;
2. reconstruct the final low actor and derive the identifiable fixed-input
   `z -> primitive-action distribution` read plus final-versus-stored action
   log-probability drift directly from checkpoint rows;
3. validate and summarize the permitted first two dimensions of the aggregate
   forced tensor without inventing snapshot metadata, clusters or strata;
4. record an explicit field/support matrix for forced stability and natural
   overlap.

If any field needed by the full estimands is absent, the valid terminal result
is `F_UNDERPOWERED_OR_UNIDENTIFIABLE`. Do not synthesize zero metrics, fabricate
episode labels, accept precomputed metrics from a caller, merge strata or run an
environment to fill the gap. The A--E decision logic below is reachable only
when every required metric was actually derived from serialized evidence.

### Frozen Data and Probability Flow

Instantiate `EventLowActor` from the checkpoint architecture header and load
`low_actor_state` strictly. For every stored low row, hold observation and
`actor_hidden_before` fixed and evaluate the full three-action categorical
distribution for all three skills. This is the exact same-input `do(z)` read;
it does not replay a counterfactual history.

Reconstruct active age, entry/resume state, active team size and realized
constant-skill duration only from lifecycle key, membership epoch, physical
time, skill and active-set size. Inactive steps do not increase age; a skill
change resets age; rejoin preserves age when the skill is unchanged. Required
nuisance bins are:

- age: `0..9`, `10..19`, `>=20`;
- entry: first ten active steps of a membership epoch versus ordinary;
- active team size: `2`, `4`, `6`;
- active duration: `1..9`, `10..19`, `>=20`.

For registered forced effects, use only action occupancy
`q[c,z,r] = [effect0, effect1, 1-effect0-effect1]`. Evaluation episodes `0..15`
are the fixed reference fold and `16..31` are the inference fold. Select one
unordered pair on the reference fold by maximum cross-replica skill energy,
breaking ties lexicographically; never select a favorable arm or inference
pair after seeing results.

Natural data are split by environment episode, lifecycle key, membership epoch,
constant skill and constant active-N. A segment contributes at most its first
12 consecutive active steps; shorter segments are excluded and longer segments
do not receive extra weight. Replay the final actor recurrently over the stored
observations from the segment's stored initial hidden state. The resulting mean
categorical distribution is the window signature. Sampled actions are
diagnostic only.

All bootstrap and shuffle RNGs are local PCG64 generators; Python, global NumPy
and Torch RNG states and every checkpoint tensor must remain exactly unchanged.
Cluster bootstrap uses source episode, 10,000 repetitions and seed `307057`;
matched shuffles use seed `307058`.

### Frozen Metrics and Support

Let `delta = 1/12` and `delta_stratum = 1/24`, corresponding to one expected
primitive-action change per 12 active steps and half that effect within a
nuisance stratum.

1. **Same-input dependence.** For every skill pair, report episode-clustered
   mean total variation between exact categorical distributions. For the frozen
   pair also report the square root of nonnegative cross-replica forced skill
   energy. Persistent dependence requires both 95% lower bounds to reach
   `delta`.
2. **Stability.** Build per-skill reference centroids separately for exact and
   forced signatures. On the inference fold, the frozen pair's label-aligned
   distance margin must have a pooled lower bound of at least `delta` and a
   lower bound of at least `delta_stratum` in every required age, entry,
   active-N and duration stratum. An upper bound at or below zero is a reversal.
3. **Natural overlap.** Macro-average only the frozen pair. It requires a
   balanced distance-margin lower bound of at least `delta`, nearest-centroid
   balanced-accuracy lower bound above `0.5`, positive lower-bound gain over a
   leave-one-episode-out nuisance-only predictor, and a margin above the 95th
   percentile of the per-repetition maximum age-, duration-, entry- and
   active-N-matched segment-label shuffle. Skill prior is an additional null.
4. **Policy-lineage guard.** Re-evaluate stored actions under the final actor.
   If the 95th percentile absolute final-minus-old log-probability exceeds
   `log(1.2)`, natural overlap is unidentifiable and returns underpowered. This
   is a support guard, not replay parity: the ledger precedes the final PPO
   update.

Minimum support is eight independent episodes and 24 forced snapshots pooled,
eight episodes and eight snapshots per forced stratum, eight episodes and 32
exact rows per exact stratum, and eight episodes plus 24 natural windows for
each endpoint skill. Missing common support never permits bin merging or a
threshold change.

### Validity and Mutually Exclusive Result

M0 requires the registered valid source result, exact arm modes, schema-3
vector checkpoints, 16 runtimes, update 250, 320,000 transitions, zero intrinsic
applications, forced shape `[128,3,2,4]`, exact timing grid, 5,120 low rows per
arm, skill/action range `0..2`, full categorical support, finite occupancy
simplexes, no prohibited field reads, tensor equality before/after, unchanged
global RNG and exactly one result JSON. M0 failure is
`INVALID_ITERATION3_AUDIT`.

F1 selects exactly one outcome in this order:

- `A_NO_MATERIAL_Z_DEPENDENCE`: every pair's exact and forced upper bounds are
  below `delta`;
- `B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT`: some dependence exists, but the frozen
  pair is nonpersistent or a supported stratum definitively vanishes/reverses;
- `C_STABLE_FORCED_NO_NATURAL_OVERLAP`: stability passes and raw natural overlap
  definitively misses its thresholds;
- `D_STABLE_LOCAL_NATURAL_OVERLAP`: stability and all raw/matched natural reads
  pass; this remains checkpoint-local and is not a utility or credit success;
- `E_NUISANCE_SHORTCUT`: raw overlap passes the prior but fails the nuisance-only
  or matched-shuffle comparison;
- `F_UNDERPOWERED_OR_UNIDENTIFIABLE`: fields/support are missing, policy-lineage
  drift fails, or a confidence interval crosses a decision threshold.

### Execution

1. Add `tests/ha_ctse_process_stage_c_skill_semantics_test.py` first. Synthetic
   fixtures matching the real nested JSON/checkpoint/dataclass layout must
   demonstrate RED for two-arm M0, direct actor lineage, fixed-input `do(z)`,
   missing-field F, prohibited-field non-access and no-mutation/RNG behavior.
2. Add only `scripts/analyze_stage_c_skill_semantics.py`, with pure functions
   `load_audit_inputs`, `counterfactual_action_distributions`,
   `reconstruct_context_rows`, `forced_action_signatures`, `natural_segments`,
   `cluster_bootstrap_ci`, `matched_nulls`, `decide_outcome` and `run_audit`.
3. The complete entry point must parse the real nested source layout itself,
   invalidate the audit if either arm fails M0, calculate available diagnostics
   rather than accept them, and write one JSON-safe result. It must stop at F
   before unreachable stability/natural logic when the availability matrix is
   incomplete.
4. Run the focused test and return the implementation for review. Do not read
   or analyze the real Stage C inputs during implementation.

## Task 2: Iteration 3 Evidence Execution and Portfolio Disposition

The controller ran the analyzer once to
`logs/f0f1_dynamic_roster_stage_c_20260717_221247/result/iteration3_skill_semantics_audit.json`.
Both arms pass every M0 check. Final-versus-ledger policy lineage is supported
(`p95 |delta logp| = 0.04337` for F0 and `0.04253` for F1 against
`log(1.2) = 0.18232`). Fixed-input exact categorical reads show only small local
skill dependence: F1 pairwise mean TV is `0.009998`, `0.040035`, and `0.048072`.

The serialized forced aggregate has no per-snapshot observation, recurrent
state, lifecycle metadata, legal support, source episode, nuisance strata or
shared natural key. Natural rows likewise have no source episode or exact
forced alignment. Stability and natural overlap are therefore unidentified;
the valid terminal outcome is `F_UNDERPOWERED_OR_UNIDENTIFIABLE`, not zero
semantics or algorithm failure.

Iteration 3 leaves C3 as the empirical leader and C1 as the strongest live
hierarchical explanation; it neither promotes C2 nor opens credit. A repeated
read is allowed only as an instrument repair that preserves the environment,
frozen policies, estimand, thresholds and nulls while recording the missing
provenance at collection time. It may not add training, reward or a new toy.

## Task 3: Iteration 4 Provenance-Complete Frozen Evaluation

Status: implementation and combined review accepted at `05b40eb`; the
provenance-only CUDA audit is launch-ready under the frozen contract below.

### HMASD Contract

Repair only the evidence serialization that caused iteration 3 to return F.
Re-run the original final stochastic Stage C evaluation from each arm's strict
`update_250_eval.pt`: the same environment, F0/F1 weights and normalizers,
256 episode ledger, seeds, 128 source snapshots, three forced skills, two CRN
replicas and twelve primitive steps. No optimizer, gradient, training,
checkpoint mutation, reward mechanism, new toy, threshold or null changes.
The existing environment reward may pass through the frozen runtime exactly as
before but is excluded from provenance, metrics and interpretation.

Existing-row reconstruction is rejected because it cannot recover source
episode or forced--natural alignment. Checkpoint-schema augmentation plus
retraining is rejected because it would create new policies rather than repair
the frozen Stage C estimand.

### Replacement Ledger

- Retain the environment, policies, model-only checkpoints, seeds, stochastic
  evaluation, snapshot grid, forced effects, metrics, support floors, A--F
  order, F0 diagnostic role and C3 baseline.
- Replace aggregate-only forced evidence and unaligned training-ledger rows as
  inferential inputs.
- Add evaluation-only source provenance and a shared forced--natural boundary
  key. Add nothing to the algorithm.
- Do not change `variable_roster_event.py`, `dynamic_roster_testbed.py`,
  `collectors.py`, config, reward, optimizer, checkpoint schema or training
  update path.

### Collection Data Flow

Add an optional default-off provenance sink to
`ha_ctse_process.train::_evaluate_event_model` and explicit focal-key plumbing
to `_forced_event_snapshot_effects`. At every registered forced source, capture
the source state before cloning or branching. After the untouched source
`core.low_step`, match the focal `LowTransitionRow` emitted at that same
boundary. Forced branches may never provide source metadata.

The shared key is:

```text
(arm, task_master_seed=97057, episode_id, physical_time,
 lifecycle_key, membership_epoch)
```

For episodes 0--31, natural rows contain only the shared key, observation,
`actor_hidden_before`, natural skill/action/log-probability, full primitive
support, active set size and lifecycle inputs needed to derive active age,
entry/rejoin and realized constant-skill duration. Each of the 128 forced rows
contains the same source fields, focal index, full active keys/epochs/skills,
frontier, membership deltas, and the source PCG64 ledger/state identifiers
needed to establish branch pairing, plus the unchanged `[3,2,4]` effects.
Collector/environment snapshots remain internal to clone/restore and are not
serialized. Task phase, reward, utility, progress, role, contact, owner and
success fields are prohibited.

The source evaluator still completes all 256 episodes so its original
stochastic episode outputs and natural skill counts can be checked. Capturing
only episodes 0--31 bounds the provenance artifact while retaining the frozen
reference/inference folds. Capture performs no random draw and must not change
the source continuation.

### Validity and Analysis

M0 additionally requires:

- strict F0/F1 model-only source headers and update 250;
- exact equality between new and registered forced effects, natural skill
  counts and stochastic episode outcomes;
- 128 unique forced source rows and one exact natural match for every key;
- source observation/hidden equality with the matched natural row;
- full three-action primitive support and finite categorical probabilities;
- unchanged model tensors, `.grad` state, module mode and global RNG;
- no prohibited fields, optimizer construction or output overwrite.

Use episodes 0--15 only to select the unordered skill pair with maximum mean
cross-replica forced energy and form reference centroids. Episodes 16--31 are
the inference fold. Exact same-input dependence uses total variation of the
three-action distributions under all forced skills. Persistent process
dependence uses the square root of the nonnegative cross-replica forced energy.
Stability uses label-aligned distance margins pooled and separately by age,
entry/rejoin, active-N and duration. Natural overlap uses one first
12-consecutive-active-step window per constant episode/lifecycle/epoch/skill/N
segment, macro-averaged over the frozen pair.

Preserve `delta=1/12`, `delta_stratum=1/24`, the `log(1.2)` lineage guard,
10,000 episode-cluster bootstrap/shuffle repetitions, existing seeds, support
floors, context-only/skill-prior/global and nuisance-matched label nulls, and
the frozen A--F priority. Any missing field, insufficient stratum, CI crossing
or lineage failure remains `F_UNDERPOWERED_OR_UNIDENTIFIABLE`; no extra episode,
bin merge or threshold change is allowed.

### Claim and Stop Boundary

The result may identify only checkpoint-local `z -> action` dependence,
12-active-step persistence, nuisance-stratified stability and natural overlap
on this testbed. It cannot establish environment-independent semantics,
transfer, cooperation, hierarchy superiority, commitment advantage, credit
success or robustness across training seeds. Outcome D remains compatible with
the ordinary-MARL objection that the latent modes are redundant because Stage
C has no utility advantage over Stage B.

Implementation write scope is limited to:

- `ha_ctse_process/train.py` for default-off capture and focal-key plumbing;
- one new `scripts/run_stage_c_semantics_provenance_audit.py` entry point;
- one focused provenance test file.

The entry point writes raw provenance and one terminal result only under one
new `logs/<run-id>/` root. It refuses overwrite. An operational defect permits
only repair and unchanged retry; a valid A--F result closes iteration 4 and
updates the whole portfolio.

### Implementation Task 3A: Default-Off Provenance Capture

**Files**

- Modify `ha_ctse_process/train.py` only at `_forced_event_snapshot_effects`,
  `_evaluate_event_model` and adjacent private helpers.
- Create `tests/ha_ctse_process_stage_c_semantics_provenance_test.py`.

**Frozen interfaces**

- `_forced_event_snapshot_effects(*, model_owner, core, environment, snapshot,
  episode_id: int, audit_index: int, focal_key: str | None = None) ->
  list[list[list[float]]]`
- `_evaluate_event_model(model_owner, *, deterministic: bool,
  capture_prefix: bool, capture_forced_audit: bool,
  capture_semantic_provenance: bool = False) -> dict[str, Any]`

When provenance is false, the return structure and RNG/action sequence are
unchanged. When true, return `semantic_provenance` with schema 1,
`natural_rows[episodes 0..31]` and `forced_sources[128]`. The private projection
helpers accept already-produced runtime rows and perform no model/environment
action.

- [ ] Add RED tests for explicit focal-key equivalence, one-to-one shared-key
  pairing, allowed fields/shapes, default-off absence, source RNG immutability
  and prohibited-field absence.
- [ ] Run only the exact new test file and confirm the missing signatures/keys
  fail before production edits.
- [ ] Add the optional sink and projection helpers. Capture the source before
  branch clone; capture natural rows from the exact `low_ledger` slice emitted
  immediately after source `low_step`. Do not draw RNG or alter forced skill,
  hidden-state or age semantics.
- [ ] Run the focused test file and the existing Stage C focused file. Require
  all tests to pass and `git diff --check` to be clean.
- [ ] Commit only Task 3A files.

### Implementation Task 3B: One-Shot Collection and Frozen A--F Analysis

**Files**

- Create `scripts/run_stage_c_semantics_provenance_audit.py`.
- Extend only the same focused provenance test file.

**CLI and outputs**

```text
python scripts/run_stage_c_semantics_provenance_audit.py \
  --f0 <stage-c-f0-root> --f1 <stage-c-f1-root> \
  --output-root <new-log-root> --device cuda
```

The script loads each `checkpoints/update_250_eval.pt` strictly, calls the
provenance-enabled evaluator, compares in-memory task outcomes/counts/effects
to the registered arm result, then writes only:

```text
<output-root>/raw/f0_provenance.pt
<output-root>/raw/f1_provenance.pt
<output-root>/result/iteration4_provenance_audit.json
<output-root>/runner_status.txt
```

Raw files contain no task outcome/reward fields. The result contains parity
booleans, support counts, registered metrics, A--F outcome and claim ceiling.
Every destination uses create-new semantics; no overwrite or resume.

- [ ] Add RED synthetic tests for strict checkpoint identity, parity mismatch
  invalidation, duplicate/missing shared keys, fixed reference/inference pair
  selection, supported A--E decisions, underpowered F, prohibited-field
  rejection and second-write refusal.
- [ ] Run the exact new tests and confirm they fail on missing runner symbols.
- [ ] Implement strict load/collection, raw serialization, pair energy,
  episode-cluster bootstrap, exact/forced stability margins, natural-window
  margins, balanced accuracy, context-only comparator, global and four
  nuisance-matched segment shuffles, M0 and frozen A--F dispatch. Import the
  existing iteration-3 pure actor/signature/window helpers; do not change its
  result path or semantics.
- [ ] Preserve global Python/NumPy/Torch/CUDA RNG around construction and
  collection; assert every source tensor, `.grad` state and module mode is
  unchanged.
- [ ] Run Task 3A/3B focused tests plus the existing iteration-3 analyzer test;
  require all finite and `git diff --check` clean.
- [ ] Commit only Task 3B files.

### Review and Evidence Execution

Each implementation task receives a fresh Sol-xhigh task review before the
next begins. After both pass, a fresh whole-change reviewer checks design
fidelity, probability/RNG/clock/checkpoint semantics, data leakage and
scientific branches. The controller then reruns the focused tests and performs
exactly one CUDA collection under `$hmasd-experiment`. A launch/runtime defect
does not consume iteration 4; a valid A--F result does.

Implementation evidence: Task 3A and Task 3B passed fresh Sol-xhigh task
reviews; the whole change passed final review after controller takeover fixed
transactional result publication. Focused provenance tests are `32/32` and the
unchanged iteration-3 analyzer tests are `18/18`. The launch implementation is
`05b40eb563e03ca5d54d4d7ff410ba856da8ab9b`.

## Variable-N + Variable-Lifetime Event Architecture — Stage A Passed

The architecture and implementation-plan rounds are complete under:

- `docs/external-review/rounds/20260717_variable_n_lifetime_architecture/`;
- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/`.

The architecture verdict is `ACCEPT_WITH_CORRECTIONS`; the implementation-plan
verdict is `MODIFY_PLAN`, and its binding corrections are now applied.

The portfolio now contains only:

- `F0`: active-set scheduled recurrent MARL, the mandatory ordinary baseline;
- `F1`: exchangeable exogenous-opportunity event-frontier commitment editor,
  the sole leading skill-based family;
- learned event-time point process, deferred.

F2 is merged and retired as a separate name. R55's environment/gate is
repurposed out of execution; only its question about common-support prefix
dependence survives as F1's irreducibility condition. The proposed R53
zero-training reanalysis is unavailable because retained artifacts contain no
final weights or per-decision contexts.

The active artifact is
`docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md`.
It now freezes one event-runtime lifecycle store, worker/collector/runtime
ownership, the pre-removal/atomic-delta/post-membership transaction, exogenous
opportunity ownership, exact random-order probability, teacher-forced replay,
member-event `gamma^Delta` credit, the reference sum/count encoder, F1-to-F0
reduction and snapshot-aware fail-closed resume.

The focused review reached Outcome A. The shared implementation plan is:

`docs/research/designs/VARIABLE_N_LIFETIME_EVENT_IMPLEMENTATION_PLAN.md`.

It freezes an exchangeable bounded renewal schedule with mean active gap 10,
active-only ragged tensors, normative high/low ledgers, a dedicated trainable
event low actor, shared active-set critics, per-token pre-working-set values,
member-event credit, simulator-aware strict schema-3 resume and one deterministic
transaction trace. F0 reads the initial set summary; F1 reads the applied
working-set summary. No other intervention is allowed.

The authorized implementation now ends at that one focused trace:

- `ha_ctse_process/variable_roster_event.py` owns the event runtime and shared
  F0/F1 production graph;
- `ha_ctse_process/collectors.py` transports default-off snapshot-capable typed
  transactions without policy lifecycle state;
- `ha_ctse_process/train.py` reads the event header and fails closed before
  collector or fixed-N agent construction;
- `tests/ha_ctse_process_variable_roster_event_test.py` passed all eight focused
  checks on CPU.

The common-support constructive control changes relative normalized F1 logits,
so the `STOP_AT_F0` wiring condition did not trigger. This proves only that F1
is structurally distinct from F0. The next boundary is a separately authorized
architecture-matched testbed and experiment contract. Stop before a real
environment, subprocess collector, environment-data optimizer step, benchmark
or training.

The isolated `dynamic_roster_testbed.py` implements the accepted generic-`SHORT`
environment and Stage A no-learning carrier. Run
`logs/f0f1_dynamic_roster_stage_a_20260717_143552` completed valid
`PASS_STAGE_A_CARRIER`: all M0 checks pass, the constructive controller has
`P=S=U=1.0`, and uniform random has positive-utility fraction `1.0` with mean
utility `0.331217 < 0.55`.

The separately authorized Stage B instrument is isolated in
`ha_ctse_process/dynamic_roster_direct.py` and
`scripts/run_dynamic_roster_stage_b.py`. It adds only a 32-wide anonymous
per-lifecycle recurrent primitive actor, active-set sum/count context, raw
earlier-action counts, one centralized team critic, token-factor PPO with a
shared team advantage, exact replay and standalone schema-3 checkpointing. One
focused behavior test and a small CUDA fresh-to-resume smoke pass, including
exact continuation from the next unconsumed ledger ID. The next boundary is
the unchanged local 16-environment, 320,000-transition formal gate. Its first
attempt was invalid because merging recurrent chunks changed CUDA batch
geometry; the final contiguous original-batch repair makes replay exact. Fresh
run `logs/f0f1_dynamic_roster_stage_b_20260717_160956` is valid
`PASS_STAGE_B_DIRECT_ACCESS`: all M0 checks pass, deterministic utility is
`0.999105`, stochastic utility is `0.986654`, and paired improvement LCB95 is
`0.498535`. This establishes only the ordinary dynamic-roster access
prerequisite. Stop before F0/F1; it remains unimplemented and requires its
separate implementation authorization.

### Stage C F0/F1 Implementation — Terminal `SUPPORT_H2_SKILL_LIMIT`

The bounded implementation reuses `VariableRosterEventCore` as the sole
lifecycle, probability, credit and checkpoint owner and exposes the frozen
generic-`SHORT` testbed through the existing event collector/dispatch path.
F0 and F1 share every model, tensor, optimizer, ledger, RNG, mask and update
contract; the only non-parameter selector is:

```text
F0 -> immutable initial active-set summary
F1 -> current applied working-set summary
```

Implemented boundary:

1. `ha_ctse_process/dynamic_roster_testbed.py` now has a typed event adapter
   that emits pre-membership and post-membership snapshots, exact membership
   deltas, anonymous actor/critic fields and strict snapshot/restore state;
2. `ha_ctse_process/collectors.py` has default-off event transport;
3. `ha_ctse_process/variable_roster_event.py` has the common execution,
   differentiable replay, high/low PPO packing, terminal closure and resume
   plumbing required by the frozen Stage C contract;
4. `ha_ctse_process/train.py` has one event-mode branch while leaving the legacy
   fixed-N path unchanged; strict 16-environment schema-3 live resume preserves
   shared models, optimizers/normalizers, per-environment runtime/RNG/ledger
   state, simulator snapshots and counters;
5. `scripts/run_dynamic_roster_stage_c.py` launches the two frozen arms
   concurrently and owns one authoritative root status and terminal result;
6. one focused Stage C integration test covers vector resume, exact fresh
   evaluation, audit/analyzer wiring, replay evidence and zero-step dry
   validation;
7. the event branch batches ragged active members across environments and packs
   recurrent PPO rollout tensors once for reuse across PPO4. Per-core RNG draw
   order, old likelihoods, chunk weighting, optimizer exposure and checkpoint
   schemas remain unchanged.

The shared reward contract is frozen to sparse terminal external utility only.
No intrinsic reward is enabled because the reviewed Stage C contract registers
no new environment-agnostic intrinsic formula. Intrinsic-applied counts are
zero in both arms; task state, progress, owner, wave and success fields cannot
enter an intrinsic path.

The launch-readiness repair/re-review loop is approved. All 15 focused event
checks pass, and dry validation hard-blocks training, collector construction and
optimizer steps while confirming the frozen package. The registered Stage C
contract now authorizes one concurrent local-CUDA F0/F1 run at 320K transitions
per arm. This authorization does not extend to reward/model/threshold changes,
additional seeds, automatic integration or a successor route.

The first formal attempt was intentionally stopped at update 31 for a
performance-only repair and has no scientific interpretation. The reviewed
refactor passes all 20 focused CPU/CUDA tests; a concurrent 16-env resume
benchmark improved steady-state throughput by 3.1--3.6x with maximum replay
error `4.77e-7`.

The update-0 formal pair at
`logs/f0f1_dynamic_roster_stage_c_20260717_221247` completed validly as
`SUPPORT_H2_SKILL_LIMIT`. Both arms finish at `P/S/U=0/1/0.5` and neither has
executable naturally used skills. F1 changes its later-token distribution and
has a small forced skill effect, but it produces no utility transport over F0.
The Stage C implementation is complete and frozen; do not rescue it by changing
the selector, reward, model, budget, threshold or timing.

## ARES-SMDP / R54-HFSR-G0 — Terminal Representation Gate

GPT-5.6 Pro selected `ARES-SMDP` as the only literature-informed architecture
sequence. The first candidate gate is a Level-0 supervised representation test:
`full_active_set_reference` versus deterministic `hybrid_m8_l2` on the
multimodal capacitated-assignment toy. Slots, masses and exact residuals are
representations, not sampled MAT actions or PPO factors. Dynamic membership,
heterogeneous time, skills and intrinsic reward are excluded.

The exact 49,576-parameter, 600-update, held-out `N={8,16,32,64}` contract and
M0/M1/M2 thresholds live in the archived literature and R53 responses. Slot
reconstruction is active-member embedding MSE against the alpha-weighted slot
reconstruction; slot-mass KL is `KL(nu || Uniform(8))`, with
`nu_m=sum_i(alpha_im)/N`. The registered 256 mean-alias cases per N are paired
capability relocations; the same construction is represented in training so
held-out twins test transport rather than an unseen label rule. These choices
are frozen before the formal launch.

The isolated generator, paired models and local runner are implemented. The
focused CUDA wiring check passed. A first formal attempt isolated a padding
invariance defect; compacting masked active tokens fixed it without affecting
unmasked training. The fresh formal retry passed every M0 check but ended
`NO_ACCESS_R54_FULL_SET_REFERENCE`: the uncompressed prerequisite fails all M1
categories and degrades strongly with N. The hybrid arm is quarantined and M2
is not reached. Retire the exact R54 contract without rescue and select no
successor until the result review closes. Any successor must absorb a principle
by replacing or simplifying a bottleneck, not by stacking literature modules.

GPT-5.6 Pro confirmed the result and closed R54 permanently. Compression quality
is unidentified because the full-set prerequisite failed. ARES-SMDP retains
only its serial research and probability/event contracts; HFSR, fixed slots,
reconstruction residual selection and full-set attention are not active
architecture candidates.

## R55-ABRP-G0 — Repurposed Before Execution

The drafted design replaces global member-set representation with a shared
focal-member/candidate-entity edge scorer. Its anonymous typed-backlog toy uses
stable `N={4,8,12,16}`, four balanced capability/requirement types, horizon 8,
N productive unit-capacity queues plus anonymous idle, one arrival per queue per
step and terminal completed-work fraction only. Capability mismatch remains in
the action support and must be learned.

The exact actor/critic has 3,906 parameters and no member encoder, pooling,
attention, GNN, slots, residual selector, recurrence or identity. Four fixed-N
specialists are the access prerequisite for one shared variable-N policy. Use
100 balanced cycles, 32 episodes per N batch, 102,400 transitions per arm, one
PPO epoch, 100 shared steps and 100 steps per specialist. The archived R54 Pro
response owns the complete M0/M1/M2 thresholds and no-rescue branches. Add only
an isolated toy/model/gate/local runner, then one focused M0 check; do not touch
the existing controller.

R55 is retired as an environment and numbered experiment before testing or
launch. Its only retained question is whether earlier applied edits change later
learned scores on the common legal support. That question now defines F1's
algebraic/behavioral distinction from F0 in the active architecture contract;
it does not authorize the R55 draft, a replacement toy or R56.

## R53-RCMA-G0 Variable-N Queue Allocation — Terminal

The sole selected edge is residual-capacity masked autoregression in an
anonymous multi-rate queue task. Each autoregressive token sees the remaining
capacity of every action entity. Productive queues have unit capacity; one
anonymous idle/abstain entity has capacity N. The comparison remains one shared
N-independent policy against five architecture-identical fixed-N specialists
with equal aggregate exposure and specialists as the binding access
prerequisite.

Implement only the corrected launch-exact contract. The actor member fields are
`has_previous_queue` and `served_previous_step`; the critic has four
task-state scalars but the actor cannot read them. The N+1 productive queues and
one idle entity are always structurally active, and raw residual capacity is the
sole feasibility mask. Idle enters the same seven-dimensional entity encoder,
mean pool, presentation permutation, pointer key, replay ledger, and
previous-action relation. It has no arrival, service, deadline, or reward
effect. The model remains exactly 24,737 parameters.

Use 100 balanced cycles, 16 environments, horizon/rollout 16, 128K transitions
and 500 optimizer steps per arm, with 100 steps per fixed-N specialist.
Constructive, persistent-only, and burst-only schedules must produce
`(F_P,F_B,U)=(1,1,1),(1,0,0),(0,1,0)` for every N. Run one focused M0 smoke,
then the unchanged local CUDA gate. No field-slot, mean-field, skill, lifetime,
intrinsic, shaping, beam-search, joint-MAP, extra exposure, or R52 rescue work
may enter this stage.

Implementation status: terminal. The isolated module, gate and local runner
completed the exact 128K-per-arm contract. M0 passed, including zero replay and
checkpoint error. All final deterministic specialist and shared policies reach
utility `1.0`, but the registered causal learning-gain lower bounds fail at
specialist `N=5,6` and for the shared macro. The emitted status is
`NO_ACCESS_R53_RCMA_SPECIALISTS`; no implementation change, rerun or rescue is
authorized. The remaining work is result interpretation only.

## R52-ARFA-G0 Task-Dynamic Variable-N Learning — Launch Exact

Implement an isolated successor to R51 with recoverable station health,
irrecoverably expiring jobs, cumulative weakest-station reliability, and only
the terminal native utility `U=min(M,J)`. Add one anonymous focal-current-entity
relation to the pointer key so stay versus switch is observable. Preserve the
small recurrent set-pointer structure, paired shared/specialist comparison,
single PPO epoch, 125 balanced cycles, 320K transitions/arm, and exact-final
evaluation.

M0 must include constructive, no-job, and partial schedules in addition to the
probability/replay/count/checkpoint contract. Specialists must first show both
training return carrier and final task access. Shared results remain
quarantined unless every M1 gate passes. No R51 rescue, shaping, intrinsic,
skill, lifetime, membership-change, S7/UAV, or novelty work enters this stage.

Implementation status: complete. The focused M0 dry-run passed and the formal
gate ended in valid `NO_ACCESS_R52_ARFA_SPECIALISTS`. Retire the exact R52
contract, quarantine its shared result, and make no rescue change. GPT-5.6 Pro
confirmed this disposition and selected only R53-RCMA-G0; R52 requires no
further review or implementation.

## R51-AMDT-G0 Task-Dynamic Variable-N Learning — Launch Exact

Implement one isolated 32-step assignment-graph environment with stable
cross-episode `N={2,3,4,5,6}`. Each N has `floor(N/2)` persistent stations and
the remaining number of short dispatch jobs. The environment emits only a
terminal full-success reward. Agents are anonymous and act through a recurrent
set-pointer policy; no identity, role, shaping, intrinsic, skill, or lifetime
mechanism enters this gate.

The formal comparison is one shared N-independent model against five
architecture-identical fixed-N specialists. Use 125 balanced cycles, five
N-specific batches per cycle, 16 complete 32-step episodes per batch, 64K
transitions per N per arm, and 320K per arm. PPO uses one full-batch epoch:
shared optimizer steps are 625, specialist steps are 125/model and 625
aggregate. Pair reset, permutation, external AR-order, and categorical-uniform
ledgers. Evaluate zero-step and exact-final models on 128 deterministic paired
episodes per N.

Specialists must first establish ordinary task access. Only then may the
shared arm decide cross-N learning. A PASS authorizes only the same-task
exogenous within-episode membership gate; it does not authorize skill,
variable lifetime, intrinsic reward, S7/UAV, or novelty claims.

Implementation and formal execution are complete. Run
`logs/r51_amdt_20260716_211616` passed M0 but produced
`NO_ACCESS_R51_AMDT_SPECIALISTS`: every fixed-N final success and every block
mean was zero, with no positive training batch. The exact AMDT
dynamics/horizon/reset/reward contract is retired and shared results are
quarantined. No further R51 implementation or run is planned; the next core
plan must describe a newly accepted environment rather than an R51 rescue.

## R50-VNSL-G0 Variable-N Shared Learnability — Completed No-Access

R49 removed mask, padding, replay, membership, and parameter-shape ambiguity.
R50 therefore folds controller compatibility into the first evidence-bearing
learning run rather than opening another wiring-only stage. Its causal edge is:

```text
mixed-N set policy + ordinary team return
-> one shared parameterization learns a set-dependent roster rule
-> performance approaches matched fixed-N specialists
```

Every synthetic episode samples `N` from `{2,3,4,6,8,12,16}` and 12 generic
member features. A random episode offset prevents absolute local features from
solving the task. The opaque target code is the quadrant of the member's first
two features relative to the active-set mean. All members are new at the
episode boundary, so the active-only AR policy emits one of four SET codes per
member. External reward is the fraction of correct codes; there is no
intrinsic reward, low-level policy, environment, task identity, or UAV field.

One shared R49 policy and seven fixed-`N` specialists start from identical
parameters and receive the same batches, AR orders, and sampling uniforms.
Training uses 512 updates, 64 cases per size/update, Adam `1e-3`, value weight
`0.5`, gradient clip `1.0`, and entropy linearly annealed from `0.01` to zero.
Each arm receives 229,376 training cases and 1,671,168 token decisions; shared
optimizer steps are 512 and every specialist also receives 512. Evaluation is
deterministic on 512 fresh cases per size.

Specialist access requires macro/min token accuracy `>=0.90/0.82`, macro exact
roster success `>=0.55`, and N=16 exact success `>=0.30`. Shared learnability
requires macro/min token accuracy `>=0.87/0.78`, shared/specialist token ratio
`>=0.93`, macro exact success `>=0.45`, N=16 exact success `>=0.20`, and
shared/specialist exact ratio `>=0.75`. Specialist failure is a substrate
no-access result. Specialist PASS with shared failure isolates cross-N sharing
as the optimization problem. Joint PASS authorizes integration with the real
default-off controller, not a skill, lifetime, intrinsic, UAV, or cooperation
claim.

Formal run `logs/r50_vnsl_20260716_195649` passed M0 but ended
`NO_ACCESS_R50_SPECIALIST_SUBSTRATE`: the fixed-N specialists missed only the
registered N=16 exact-roster floor (`0.26953 < 0.30`). Although the shared arm
passed every numerical M2 threshold, M1 is a prerequisite, so those values do
not establish cross-N learnability. R50 is closed without rescue or controller
integration. Its synthetic set-relative label did not model task dynamics;
the next design must make team size change the toy task itself.

## R49-ORSE-G0 Open-Roster Set-Equivariant Interface — Completed PASS

R48 closed fixed-`N` skill/lifetime exploration. R49 is a separate,
architecture-only question: can a variable active set support a
set-equivariant roster representation and variable-length, active-only
autoregressive sampling/replay while preserving exact probability and
membership semantics? Its four categorical codes are opaque protocol states,
not learned or semantic skills.

The registered interface is a minimal Deep Sets model: a shared
`19 -> 64 -> 64` member encoder over 12 generic features, a four-way opaque
code, normalized age, joined, and processed flags; mean-pooled member and
working-roster summaries; `log(1+N)`; a shared KEEP/conditional-SET decoder;
and one pooled scalar value. External active keys and membership epochs are
ledger fields only. Persistent ID, padded-slot index, pairwise `N x N`
tensors, graph/attention blocks, task fields, reward, environment execution,
optimizer steps, checkpoint migration, and current trainer changes are absent.

The deterministic CPU gate uses model/data/sampling seeds
`49041/59041/69041`, active sizes `{1,2,3,4,6,8,12,16}`, 128 base cases per
size, eight permutations per case, 1,024 junk-padding variants, 1,024
sample/replay sequences, and 256 join/leave event pairs. M0 checks exact
counts, active-only token support, complete order/epoch/prefix ledgers,
finite values and gradients, zero environment/reward/optimizer/checkpoint
activity, and complete membership records.

M1 requires maximum permutation, padding, incremental/full-recompute, and
sampling/replay errors `<=1e-6`; exact joiner/leaver/survivor membership
semantics; prefix-actionability gradient support at least `0.99` with median
norm `>1e-4`; identical parameter shapes for every `N`; one active-set encode,
exactly `N` incremental roster updates and decoder calls, and no pairwise
tensor. `PASS_R49_ORSE_ARCHITECTURE` authorizes only a default-off,
cross-episode exogenous variable-`N` compatibility step. A valid fail retires
this exact Deep-Sets/open-roster interface without graph, Transformer, model,
budget, or threshold rescue and stops the current project line. An invalid
result permits repair only of the named wiring defect.

The isolated implementation uses `scripts/r49_orse.py`,
`scripts/run_r49_orse_gate.py`, and `scripts/run_r49_orse_local.ps1`. A
16-case dry-run covered every registered active size. M0 and M1 passed:
permutation-logit error `2.98e-8`, padding error `0`, incremental/full-logit
error `2.98e-8`, replay error `0`, prefix-actionability support `1.0` with
median norm `0.19955`, and zero complexity violations. Its transient output
was removed and served as the prelaunch evidence for the unchanged full gate.

Formal run `logs/r49_orse_20260716_191959` completed
`PASS_R49_ORSE_ARCHITECTURE`. M0/M1 passed at the exact 1,024-case contract.
Permutation-logit and incremental/full-logit errors were `2.98e-8`, padding
and replay errors were zero, prefix-actionability support was `1.0` with
median norm `0.19933`, every joiner/leaver/survivor rule passed, and complexity
violations were zero. Parameters remained bit-exact with zero environment,
reward, optimizer, or checkpoint exposure. The only permitted next design is
a default-off, exogenous cross-episode variable-`N` compatibility gate; R49
itself makes no algorithm-efficacy claim.

## R48-SBRS-G0 Skill-Boundary Recurrent State — Pro-Confirmed Valid Fail

GPT-5.6 Pro confirmed `VALID_FAIL_R47_NSOPM`, found no result-changing M0
defect, and permanently retired the exact R47 view/basis/score/reward line. The
only remaining fixed-`N` edge is whether skill SET needs an explicit focal
low-actor recurrent-state boundary.

R48 uses the same frozen adaptive-R30 checkpoint, `N=2`, `K=4`, `k0=10`, and
64 natural source reset groups. One context is captured per group after high
commit and before the first low action at check
`1 + floor(group/2) mod 4`, so every focal hidden contains at least one full
natural skill block. Each context forces all three nonincumbent targets for two
independent replicas and two matched arms:

- `carry_hidden`: target skill with the snapshot focal actor hidden;
- `reset_on_set`: the same target with only that focal actor hidden zeroed.

Both arms share the exact environment snapshot, observation, roster, team code,
critic hidden, teammate actor hidden, and explicit Gaussian innovation tape.
All parameters and normalizers are frozen; high checks are suppressed; every
branch holds its roster for 40 stochastic low-policy steps. No external return,
task field, intrinsic signal, optimizer, or normal-trainer modification enters.

The task-blind process is the four-dimensional normalized focal displacement
and teammate-relative displacement. H10 uses steps `1..10`; H40-late uses
`31..40`. For each arm/context, `B` averages same-replica distances across the
three target pairs and `W` averages the two-replica distance within each
target. `rho=E[B]/(E[W]+1e-8)`. A single 10,000-repetition paired context
bootstrap with seed `62048` keeps both arms, every target, both replicas, and
all trajectory coordinates together.

M1 requires at both horizons: reset-rho lower bound `>1`, reset/carry rho-ratio
lower bound `>1.25`, reset/carry within-ratio upper bound `<0.80`, and
reset/carry between-ratio lower bound `>0.90`. Every target skill must also
have H40-late reset rho `>1`. `PASS_R48_SBRS_G0` authorizes only a reward-pure
R30 `carry_on_SET` versus `reset_on_SET` pair. `VALID_FAIL_R48_SBRS` retires
the recurrent-boundary explanation and permanently stops fixed-`N`
skill/lifetime algorithm exploration. There is no underpowered or rescue
branch.

Implementation is isolated to:

- `scripts/r48_sbrs.py`
- `scripts/run_r48_sbrs_gate.py`
- `scripts/run_r48_sbrs_local.ps1`

One two-context CUDA check covered 24 branches and 960 forced steps. Snapshot,
hidden-boundary, explicit CRN, counts, parameter/normalizer freeze, and finite
statistics passed; the transient output was removed. Pre-launch commit
`eb6b9e6` was pushed before the formal run.

Run `logs/r48_sbrs_20260716_181833` completed valid
`VALID_FAIL_R48_SBRS`. M0 passed. H10 failed reset-rho, rho-gain, and within-noise
gates; H40-late passed absolute and per-skill reset rho plus between preservation
but failed rho-gain and within-noise gates. Within reset/carry means were
`1.00794` at H10 and `1.00156` at H40-late, so focal hidden reset did not reduce
the registered stochastic variability. GPT-5.6 Pro confirmed the valid-fail,
the no-rescue recurrent-boundary retirement, and the binding fixed-`N` stop.

## R47-NSOPM-G0 Natural-Support Orthogonal Process Modes — Valid Fail and Retired

GPT-5.6 Pro confirmed R46 as a valid learned Q/DR sign-transport failure and
selected one upstream reward-off successor:

```text
natural task-blind process support
-> stable persistent process modes
-> skill-conditioned causal mode occupancy
```

GPT-5.6 Pro issued `ACCEPT_R47_NSOPM_G0_LAUNCH_EXACT`. The fixed boundary is
local CUDA, `N=2`, `K=4`, `k0=10`, 64 natural reset groups, 512 staggered
natural windows, 64 matched forced-skill contexts, two replicas per skill,
`H=40`, and 20,480 causal branch steps. The seven-dimensional view contains
only focal displacement, teammate-relative-mean displacement, and relative-set
covariance displacement; for `N=2` the last three fields are exactly zero.

The implementation boundary is only:

- `scripts/r47_nsopm.py`
- `scripts/run_r47_nsopm_gate.py`
- `scripts/analyze_r47_nsopm.py`
- `scripts/run_r47_nsopm_local.ps1`

Natural groups `0..31` fit a population-standardized, initially centered
35-D quadratic feature map. Lags `{1,5}` form the pooled-covariance whitened
Gram estimator; 256 within-window temporal permutations, independent half-fit
alignment, held-out coherence, and a ten-field nuisance ridge audit define M1.
The frozen primary basis then scores H10 and H40-late forced-skill windows with
held-out natural-support filtering; assigned-mode contrast, between/within
causal SNR, and persistence define M2. Forced data never fits or aligns the
basis. Every policy, critic, posterior, and intrinsic optimizer exposure is
zero; external reward is discarded and never stored or used.

Before the formal run, execute exactly one two-group CUDA dry run covering 16
natural windows, one context, eight 40-step branches, two temporal nulls,
finite spectral/score tensors, snapshot restore, zero drift, and absence of a
reward field. It has no scientific status and its transient output is removed.

The focused dry run passed and its transient output was removed. Pre-launch
commit `078845b` was pushed before the formal local CUDA run. Run
`logs/r47_nsopm_20260716_172711` completed as valid
`VALID_FAIL_R47_NSOPM`: M0 passed; M1 and M2 failed. Only spectral rank 0 beat
its temporal null, lag-5 coherence crossed zero, H10 support was `0.71875`,
H10 assigned contrast crossed zero, H40 skill 0 contrast was negative, and
both causal-SNR lower bounds were below one. GPT-5.6 Pro confirmed validity,
found no result-changing M0 defect, and permanently retired this exact
view/map/lag/basis/score/reward pair. Reward-on training is closed; only the
structurally distinct R48 recurrent-state-boundary gate remains.

## R46-HMRV-G0 Heterogeneous-Maintenance Positive Control — Completed and Retired

GPT-5.6 Pro confirmed R45 and selected one new substrate-level causal edge:
before another renewal actor or joint skill mechanism, test whether a fixed
`N=2` process with native heterogeneous degradation yields identifiable
sign-changing KEEP/RENEW value under balanced natural support.

The gate is standalone and reward-off with respect to learning: fixed
Bernoulli-0.5 behavior generates 64,000 local CUDA steps; no policy, skill,
intrinsic, or source module exists or updates. Only four cross-fitted
`6 -> 32 GELU -> 2` true-Q/action-blind-sham critics train. The accepted
environment, budgets, M0--M3 thresholds, and terminal branches may not change.

The launch-exact clarification is accepted: `gamma=0.99`; agent-0 prefix is
`[0,0]`, agent-1 prefix is `[1,actual_b0]`; critic Adam and fold seeds match the
R45 contract; scientific bootstrap clusters independent `(env,episode)` rows;
evaluation replays seed `56041`; and ordered degradation strata `(1,2)` and
`(2,1)` must each clear the discordance lower-bound gate.

The formal local CUDA run completed at
`logs/r46_hmrv_64k_20260716_154508` as valid
`VALID_FAIL_R46_HMRV_SUBSTRATE`. M0, M1, and M2 passed: all traces and counts
were exact, agent/action ESS exceeded `4,700`, and true-Q beat its action-blind
sham with a positive ratio-gain lower bound. M3 failed because agent 0's top
quartile remained renewal-negative and pooled plus both ordered-role-stratum
predicted-sign discordance were exactly zero. Direct enumeration then showed
that the finite dynamics contain oracle sign heterogeneity; the valid failure is
therefore the registered learned Q/DR sign-transport line, not the transition
kernel itself. The exact dynamics/estimand/context/critic/read combination is
retired without rescue. No renewal
actor, S7, open-roster, or variable-`N` implementation is authorized before
the result review selects one structurally different edge.

## R45-SDRA Reward-Off Identifiability — Completed and Retired

GPT-5.6 Pro confirmed R44 and selected one upstream question before any new
renewal-actor update: does the frozen source-exact natural policy provide
enough overlap to identify agent/context-specific KEEP versus RENEW value?

Implementation boundary:

- `scripts/r45_sdra.py`
- `scripts/run_r45_sdra_gate.py`
- `scripts/analyze_r45_sdra.py`
- `scripts/run_r45_sdra_local.ps1`

The R41B source MAT, low policy, `q_D/q_d`, optimizers, ValueNorms, and the
zero-output renewal residual are frozen. Collection preserves the validated
R43/R44 global `k0=50` reset-censored clock and stores each natural binary
action's exact propensity, 148-D task-agnostic canonical-prefix context, and
discounted next-50 external return. No forced branch, simulator clone, actor
update, shaping, task field, or new intrinsic reward is used.

Environment ranks 0--7 and 8--15 form fixed cross-fit folds. Each fold trains
one `148 -> 32 GELU -> 2` true action-Q model and one initialization-, data-,
capacity-, optimizer-, and exposure-matched action-blind propensity-mixture
sham. All four models train offline for 15 epochs, 195 Adam steps each; their
held-out predictions produce the doubly robust score and sign-heterogeneity
read.

One two-update CUDA wiring check passed. It produced exactly 64 environment
checks, 16 structural rows, 48 normal checks, 96 paired factor rows, and 148-D
contexts. Source probability error was `4.768e-7`; binary replay and prefix
mismatch were zero. All source state and the renewal actor stayed exact, zero
and final deterministic traces matched, and each of the four critics received
one finite nonzero gradient step. The smoke output was removed after the check.

The user approved the nontrivial M2 interpretation before launch. The formal
run completed at `logs/r45_sdra_160k_20260716_144312` as valid
`VALID_FAIL_R45_SDRA_IDENTIFIABILITY`. M0 passed with exact freeze, replay,
prefix, count, optimizer, trace, and critic contracts. Frozen source service
remained `0.93/1.00/0.93`.

M2 passed: true-Q versus action-blind weighted MSE was
`0.03830/0.37667`; ratio-gain lower bound was `3.3623`, and top-minus-bottom
DR-score lower bound was `0.4083`. M1 failed because natural KEEP ESS was only
`33.59` and `3.30`, with excessive environment-cluster weight concentration.
M3 failed because both agents' bottom-quartile DR scores stayed positive and
same-check predicted-sign discordance was `0.000314` rather than `>=0.20`.
Alice--Bob K50 natural-support renewal credit and this temporal-mechanism
substrate are therefore retired without more data, capacity, clipping, seed,
threshold, forced-action, or actor-training rescue.

## R44-FS-NRC Frozen-Source Renewal — Completed and Retired

GPT-5.6 Pro confirmed R43 as invalid, accepted the fixed wrapper as
source-equivalent, and selected one successor: freeze the complete service-
capable R41B skill system and train only a native renewal actor and renewal
critic. This isolates renewal timing from the destructive source-continuation
drift observed in R43.

Implementation boundary:

- `scripts/r44_frozen_source_nrc.py`
- `scripts/run_r44_frozen_source_nrc_arm.py`
- `scripts/analyze_r44_frozen_source_nrc.py`
- `scripts/run_r44_frozen_source_nrc_local.ps1`

Both arms use the same source-exact KEEP/RENEW decomposition, frozen source
team and conditional-skill distributions, frozen low actor/critic, frozen
`q_D/q_d`, frozen ValueNorms, and a separate Adam optimizer over only the
renewal actor and critic. The control actor is frozen at zero while its critic
trains; the treatment enables the actor. Renewal credit is the next 50
external-reward steps with reset-censored execution and update-boundary old-
critic bootstrap. No renewal entropy, shaping, new intrinsic reward, or task
field is present.

Focused two-update CUDA evidence completed for both arms. Across 30 factor
steps per arm, every source module, source optimizer state, and ValueNorm was
exactly unchanged; high/factor/low replay and conditional-skill ratio error
were zero. The control actor had zero drift and zero actor gradients, its
zero/final deterministic high and low traces were identical, and the treatment
actor plus both critics had nonzero gradients on every factor step. The
formal run then completed at
`logs/r44_fsnrc_320k_20260716_132349` as valid
`VALID_FAIL_R44_FSNRC`. M0, the frozen service anchor, and service safety
passed: both arms retained win/key0/key1 `0.93/1.00/0.93`, all source state
drift was zero, and treatment-minus-control win CI was `[0,0]`. M3 failed:
both arms had zero discordant renewal, full-sync RENEW `1.0`, and minimum
KEEP/RENEW marginal `0`, despite treatment actor relative drift `0.353245` and
3,000 nonzero actor-gradient exposures. This permanently retires the frozen-
source K50 renewal timing route; no entropy, seed, budget, threshold, or source-
unfreezing rescue is active.

## R43-NRC True Renewal — Invalid and Closed

GPT-5.6 Pro confirmed the source clock contradiction and selected
`PRESERVE SOURCE-GLOBAL CLOCK`. R43 now decomposes each native individual
categorical factor into an explicit KEEP/RENEW factor and a non-incumbent
conditional skill factor opened only on RENEW. The source team token, low actor,
`q_D/q_d`, global `k0=50` checks, and five optimizer exposures remain intact.

The controller state persists across source auto-reset and outer updates:

- the whole training run has one structural assignment per environment;
- later rollout steps 0 and 50 are ordinary KEEP/RENEW checks;
- auto-reset creates no high action or row, preserves roster/age/spell, and
  censors only the low execution fragment;
- update boundaries bootstrap and truncate actor-valid event credit while a
  critic-only continuation carries the active spell;
- renewal/check credit spans the next 50 primitive steps and conditional-skill
  credit ends at the next RENEW or update boundary.

Implementation boundary:

- `scripts/r43_native_renewal.py`
- `scripts/run_r43_native_renewal_arm.py`
- `scripts/analyze_r43_native_renewal.py`
- `scripts/run_r43_native_renewal_local.ps1`

Focused real-checkpoint evidence is complete. Joint enumeration over all 32
`(Z,z1,z2)` outcomes had maximum decomposed log-probability error
`9.536743e-7`; the renewal actor, renewal critic, skill-event critic, and source
conditional decoder all had nonzero direct gradients. A two-update real CUDA
check preserved four global rows, one structural assignment, three normal
checks, cross-update carry, two reset-censored fragments, 30 combined high
optimizer steps, and zero high/low/factor replay or prefix error. No further
test layer was added before the registered paired gate.

The formal paired run completed at
`logs/r43_nrc_reset_censored_320k_20260716_121756_retry2` with status
`INVALID_R43_FIXED_ANCHOR_LOST`. M0 passed, including exact replay, clock,
optimizer, and carry checks, but the fixed arm ended at win/key0/key1
`0.52/0.54/0.81`. The treatment result is not scientific evidence.

Two bounded diagnostics closed the immediate ambiguity. The R41B source
checkpoint scored win `0.89` on its original reset stream and `0.93` on the
R43 stream, while the fixed final checkpoint scored `0.61/0.52` on the same
two streams. Untouched source continuation and the R43 fixed wrapper remained
parameter-exact across two updates (`max_abs=0` for high, low actor, low critic,
`q_D`, and `q_d`). Thus the evaluator and fixed wrapper are not the observed
failure carrier; continued optimization of the solved source checkpoint is
unstable under this registered continuation. GPT-5.6 Pro accepted this
localization, kept the treatment diagnostic-only, and selected R44-FS-NRC as
the sole next edge. R43 receives no rerun, seed substitution, or rescue.

## R42-IRR Native Incumbent-Roster Residual — Completed and Retired

Terminal result: valid `VALID_FAIL_R42_IRR_SERVICE` at
`logs/r42_irr_native_roster_residual_320k_20260716_100824`. M0 and the fixed
anchor passed, but treatment service was inferior and the registered temporal
decoupling gates failed. No R42 rescue implementation is active; the next
staged change must wait for failure review and select a structurally new edge.

Completed causal edge:

```text
positive R41B checkpoint + incumbent roster at the native k0=50 check
-> zero-initialized task-blind residual on MAT individual logits
-> learned per-agent retention/replacement probabilities
-> nontrivial renewal without losing Alice--Bob service
```

The three authorized GPT-5.6 Pro rounds are complete. The final proposed pure
categorical KEEP/SET interpretation is rejected after source audit: for every
sampled label `y_i`, retaining the incumbent when `y_i` equals it and otherwise
setting `y_i` always produces the same effective skill `y_i` as the original
full refresh. The source resets low recurrent state only on episode termination,
and no event label or age enters the policy, buffers, or nonrecurrent
discriminators. A paired run would therefore compare identical trajectory and
gradient distributions while manufacturing different renewal labels.

R42-IRR is the smallest non-decorative successor:

1. Keep the original team-token sampling and native `k0=50` clock unchanged.
2. At the sole ordinary check (`t=50`), add a shared residual to each existing
   MAT individual-token logit. Its input is only the pre-check/working roster,
   focal position, and active-agent mask; it reads no task field, reward,
   success, contact, distance, or age.
3. Zero-initialize the residual output so sampling, teacher-forced replay, low
   trajectories, and existing gradients exactly match R41B before learning.
4. Store the incumbent/working roster used at collection and use the same
   autoregressive prefixes during PPO replay. The residual trains through the
   existing per-agent high advantage; original low reward and all source
   optimizer paths remain unchanged.
5. Compare a fixed continuation arm with the same residual disabled against a
   treatment arm with it trainable. Do not add a duration action, separate KEEP
   head, new critic/latent, lifetime reward, switch reward, or new intrinsic.
6. The first evidence boundary must show exact zero-residual parity, replay
   error `<=1e-6`, a nonzero treatment residual update, retained fixed-arm
   source access, service noninferiority, and nondegenerate effective
   per-agent skill changes at `t=50`.

Implementation remains in external wrappers around a fresh `ref/hmasd.tar`
extraction. Do not edit the source archive or port it into the standalone
HA-CTSE trainer. Register the exact paired budget and thresholds in
`memory/ExpRecord.md` before launch.

Implementation boundary completed in:

- `scripts/r42_native_roster_residual.py`
- `scripts/run_r42_native_roster_residual_arm.py`
- `scripts/run_r42_native_roster_residual_local.ps1`
- `scripts/analyze_r42_native_roster_residual.py`

The overlay adds 548 parameters and stores `[high_step, env, agent]` incumbent
labels beside the unchanged high buffer. Sampling builds the working roster in
canonical agent order; replay reconstructs the same prefixes from stored high
actions. Gradients enter the residual and original MAT logits through the same
categorical PPO ratio. The low actor, critics, discriminators, rewards, clocks,
episode masks, and collector shapes are unchanged.

One real-checkpoint preflight with a one-env runner completed without training:
all sampled-action, log-probability, value, entropy, teacher-forced replay, and
base-MAT gradient errors were exactly zero; the treatment residual gradient
norm was `0.2221745794`. The next and only check is the registered paired run.

## R41B Full-Source HMASD Alice-and-Bob Access Reproduction

Active causal edge:

```text
original HMASD source and Alice_and_Bob task
-> exact 32-environment source exposure reproduces or rejects positive access
-> decide whether a same-checkpoint native KEEP/SET temporal gate is meaningful
```

R40 is a valid access failure and its `simple_spread_v3` contract is retired.
GPT-5.6 Pro modified R41 from a paper-guided reconstruction to an exact source
reproduction. Its `VOMASD` repository locator was factually rejected after the
user identified the authoritative local HMASD package at `ref/hmasd.tar`; the
remaining algorithm and budget contract was independently checked against that
archive. The raw response and controller disposition live under
`docs/external-review/gpt5_6_pro/20260715_r40_simple_spread_access_result/`.

R41A completed as a valid reduced-exposure no-access pilot. GPT-5.6 Pro round 1
accepted that result and selected exactly one full-source seed before any R30,
intrinsic, open-roster, or variable-team work. The raw response and disposition
are in `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/`.

One implementation/evidence boundary:

1. Freshly extract tracked `ref/hmasd.tar`; the enclosing project commit is the
   version identity and no application checksum layer is added.
2. Keep the extracted `hmasd/` source and `Alice_and_Bob0` implementation
   unchanged. Add only external wrappers and telemetry in this repository.
3. Use seed 1, 32 rollout environments, 100-step episodes, 937 outer updates,
   2,998,400 environment steps, `k=50`, `n_Z=2`, `n_z=4`, hidden size 64,
   original optimizers, and `lambda_e/D/d = 0/0.1/0.2`.
4. Record zero-step and exact-final deterministic 100-episode evaluations,
   actual optimizer-step counts, finite nonzero gradient evidence, source and
   runtime versions, and the pre-update stored/replayed likelihood error.
5. Run the single reproduction locally on CUDA and emit one result JSON implementing
   the registered M0--M2 branches in `memory/ExpRecord.md`.
6. Do not implement R30, port the task into the current
   trainer, add shaping/intrinsic reward, or change the source, seed, budget,
   threshold, network, action, observation, map, or checkpoint-selection rule.

Upstream result boundary: the corrected R41A run
`logs/r41a_hmasd_local_pilot_20260716_030013` at commit `a1ea76b` completed as
valid `NO_ACCESS_R41A_HMASD_ALICE_BOB_LOCAL_PILOT`. M0 passed with zero high,
low, and global replay error and exactly 14,055 updates on all five optimizer
paths. Exact zero-step and final win rates were both zero; the paired interval
was `[0, 0]`. R41B is the accepted full-source closure, not a rescue or tuned
variant.

R41B result boundary: `logs/r41b_hmasd_full_source_20260716_035300_retry2`
completed valid `PASS_R41B_SOURCE_ACCESS` at commit `e36f7df`. M0 passed with
zero replay error and exactly 14,055 updates on all five optimizer paths. Exact
final deterministic win/key0/key1 rates were `0.89/0.97/0.92`, versus zero-step
win `0`; the paired win-gain interval was `[0.82975, 0.95]`. All three automated
Pro rounds are archived. Their final pure-categorical route is source-equivalent
and retired without compute; R42-IRR is the next registered causal edge.

## R39 S7 Compatibility Boundary

R38 completed as a valid `FAIL_R38_CTS_ACCESS`; its replacement environment and
ordinary-MAPPO access route are retired. The accepted structural direction is
to return to S7 and compare current fixed-`k` HMASD with a same-substrate
per-agent KEEP/SET treatment. Environment-specific intrinsic reward remains
prohibited.

The GPT-5.6 Pro follow-up is accepted with controller closures in
`docs/external-review/gpt5_6_pro/20260715_r38_cts_access_result/`.
The only positive historical checkpoint was saved at 1.760M on the former
six-agent, three-action S7 stack; it remains reference-only. Current S7 uses the
eight-agent, four-action interface-v3 contract, and standalone R30 is not the
HMASD coordinator/trainer.

The user selected a lightweight synthetic mechanism gate before paying the S7
compute cost. This does not alter the accepted serial S7 route or implement
native-HMASD R39B. The completed standalone stage-0 diagnostic sequence used:

1. two agents receive identical constant local observations while centralized
   high context exposes one slow and one fast action target;
2. the shared dense external reward is invariant to swapping agent roles;
3. a single categorical final-skill action maps the incumbent to `KEEP` in the
   adaptive arm and maps every draw to `SET`, including the incumbent, in the
   full-refresh control;
4. both arms use the same 32-wide feedforward low policy and 16-dimensional
   compact/team representations, with every intrinsic and process auxiliary
   objective disabled;
5. the paired 12.8K-step run is the implementation and mechanism check.

First-run disposition: invalid `INVALID_R39_TOY_LOW_PPO`. The feedforward
learner crossed interleaved environments when computing returns, ignored the
registered three PPO epochs, and used a clipped-Normal likelihood that did not
describe executed actions. Its match and lifetime outcomes are not evidence.
The repair uses env-grouped bootstrapped GAE, three PPO epochs, and a
tanh-squashed Gaussian while retaining the 32-wide model and original compute
budget. Its valid rerun still failed dense access: adaptive/control match was
`0.445716/0.445838`, with all slow/fast components below `0.46`. The next toy
boundary therefore removes low learning entirely: four fixed axis primitives,
zero low parameters or optimizer steps, and the same 32-wide high stack. This
is only a high-controller positive control; it cannot establish skill discovery.

GPT-5.6 Pro subsequently accepted the controller's sequencing disposition. The
native-HMASD fixed-`N` positive credit anchor on the same
`two_timescale_role_free_actions` substrate froze two agents,
`n_Z=n_z=4`, `k0=5`, episode/rollout 40, high hidden 32, 16 environments, 12,800
steps, 20 outer updates, three high PPO epochs, seed 39041, 32 stochastic final
evaluations, zero trainable low parameters, and zero intrinsic reward. Sampling
and replay use the stored `Z,z_{<i}` chain and native team/agent values,
advantages, and ratios. The result owner is one
`result/r39_native_hmasd_toy_credit.json`.

The gate completed as valid `VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR`: M0 passed
with 20/20 outer updates, 60 high optimizer updates, replay error
`4.76837158203125e-7`, and zero low/discriminator updates, while
match/slow/fast were `0.455078125/0.46484375/0.4453125`. Retire this native
GAE/PPO credit route without rescue. The active boundary is now one fixed-`N`
joint-credit failure review that must select a structurally different causal
edge before any open-roster implementation or new compute.

The preserved R39A package boundary is:

1. native HMASD PPO teacher-forces stored `Z,z_{<i}`;
2. coordinator encoder/decoder dropout is zero so the stored joint action has
   one replayable conditional likelihood while categorical sampling remains
   stochastic;
3. one strict 1.6M-step/100-update CUDA runner trains from scratch and one
   independent stochastic evaluator owns the registered 100-episode decision;
4. launch is deferred until the toy gate reaches its registered result.

R39B remains unimplemented in native HMASD. Only a toy mechanism PASS followed
by `PASS_R39A_CURRENT_FIXED_HMASD_ANCHOR` may authorize its S7 implementation
and 320K matched temporal gate.

Do not partially load the old checkpoint, cross into the standalone R30 trainer,
or invent an experiment result before the source anchor and team-`Z` semantics
are closed.

## R37 Actor-Visible Task-Identity Access Gate

Active causal edge:

```text
actor-visible current task identity
-> removal of the hidden-information bottleneck
-> positive sparse collection access under constant-code recurrent MAPPO
```

Authorized by the valid R35--R36 access failures and accepted from GPT-5.6 Pro
with the capacity-matched control clarification in
`docs/external-review/gpt5_6_pro/20260715_r36_aem_access_result/DISPOSITION.md`.
R36 itself is retired: it expanded coarse joint-position coverage `3.8552x`
without one collection or successful cycle.

One coherent implementation/evidence boundary:

1. Reuse the R35 constant-code recurrent MAPPO actor and centralized critic.
   Add no skill, high policy, latent, classifier, intrinsic reward, shaping, or
   new optimization path.
2. Give both arms one identical 16-value actor layout: the original 12 values
   followed by two active-plate and two active-target slots. Treatment fills
   the slots with current true one-hots; control fills them with zeros. The
   existing 19-value centralized critic state is unchanged.
3. Keep the external reward collection-only. Do not expose clocks, contacts,
   collection/progress state, reward-derived fields, future state, distance, or
   oracle actions to either actor.
4. Compare the two trained arms from one common neutral zero-step
   initialization using seed `38031`, concurrent local CUDA, 16 environments
   per arm, rollout 80, 320,000 steps, 250 low updates, five PPO epochs,
   recurrent sequence length 10/batch 64, and 64 paired stochastic episodes.
5. The registered M0--M3 access gate in `memory/ExpRecord.md` is also the
   implementation check. Do not insert a smoke, identity ablation menu,
   threshold change, retuning, seed expansion, or longer budget.

This is an environment/access-instrument repair, not an algorithm contribution.
PASS establishes only a positive access floor under the repaired observation
contract. FAIL retires sparse Alice--Bob as the current algorithm-comparison
gate.

Result boundary complete: R37 is a valid `FAIL_R37_ACCESS`. Current-task
identity caused nonzero access but cycle success `0.01953125` remained below the
registered `0.05` floor. Retire this environment as an algorithm gate. No new
core implementation begins until one replacement benchmark/access contract is
selected and registered.

## R30 Fixed-Clock Autoregressive Edit Gate

Active causal edge:

```text
fixed global check clock k0
-> complete all-agent autoregressive KEEP/SET action
-> lifetime learned by KEEP survival without duration shortcut
```

Accepted design:
`docs/research/designs/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md`.

One coherent implementation boundary:

1. Replace the active duration head with separate keep and conditional
   switch-skill heads. Mask initial `KEEP` and normal `SET(current_skill)`.
2. At every `k0` check, give every agent one token in a stored order. Apply each
   token immediately to the working roster before evaluating the next agent.
3. Move high PPO from completed variable segments to a fixed-check buffer with
   per-environment check-sequence GAE, one prefix-independent scalar critic,
   and one shared block advantage. Re-evaluate stored token sequences with
   applied-roster teacher forcing and one combined ratio per executed token.
4. Keep process segments independent of the high buffer: `KEEP` continues the
   active segment; `SET` closes and opens it; process records never train the
   high controller.
5. Remove duration candidates, duration entropy floors, edit/switch penalties,
   forced maximum age, and lifetime rewards from the active mode. Initialize
   `p_keep=0.6` for the current `{1,2,3,4}`-block source.
6. Preserve `pi_l(a_i | o_i, z_i)`. Do not add a semantic reward in this
   implementation; retain only the fixed, duration-blind `W=k0` interface for
   the later realized-effect target.
7. Use deterministic expected bridge context, a per-environment
   `steps_to_check` clock, and actor-invalid continuation rows across PPO update
   boundaries. Preserve skills, ages, clock, and low recurrent state.
8. Load R30 checkpoints through an explicit versioned migration: reuse only
   compatible representation/low-policy/high-actor parameters and reinitialize
   keep head, high critic, high ValueNorm, high optimizer, clocks, and buffers.

The evidence-bearing check after implementation is one reward-pure,
mechanism-matched short comparison at approximately 320K transitions per arm,
16 environments, CUDA, seed 30031. It reads only: token/replay validity,
lifetime breadth, asynchronous switch-skill supply, and immediate task safety.
It does not add a duration sweep, team mechanism, or semantic reward.

Implementation status: complete. The next boundary is the registered paired
run in `memory/ExpRecord.md`; implementation and experiment are not separated
by another validation stage.

## R31 Natural-Window Causal Fixed-Window Effect Information

Active causal edge:

```text
natural on-policy prefix
-> persistent skill intervention under policy-matched stochastic execution
-> task-generic realized environment-effect separation
```

Accepted design source:
`docs/external-review/gpt5_6_pro/20260714_r30_sparse_exploration_review/RESPONSE_RAW.md`.
Controller disposition: `DISPOSITION.md` in the same directory.

R28 completed boundary:

- a separate default-off low-level reward module using frozen scorer/source
  continuity, exact same-forward deterministic-action evidence, natural clocks,
  common support, sham derangement, terminal-ten-step attribution, and
  fail-closed OOD/reward-ratio guards;
- checkpoint and CLI integration, R26 sidecar/export, family analyzer, and
  focused tests;
- explicit non-resumable tagging for engineering-smoke checkpoints.
- two exact one-update engineering smokes plus support-distance diagnostics;
  both support kills occurred before any R28 reward application;
- a feature-construction audit confirming shared feature code, action transform,
  duration mapping, source identity, and support-distance semantics.
- a separate paired transport sidecar that holds checkpoint, prefix, forced
  skill, scorer, and features fixed while changing only deterministic versus
  six-agent stochastic environment execution; no R27 artifact semantics were
  changed;
- reset-0 local CUDA smoke: 16 paired windows, deterministic OOD `0.0625`,
  stochastic OOD `1.0`, with the same temporal-standard-deviation shift.
- 64-reset decision: `FAIL_STOCHASTIC_SUPPORT_TRANSPORT`; deterministic OOD
  `0.068359`, stochastic OOD `0.823242`, and 64 rows in every label-duration
  cell. Random action execution is sufficient to break the frozen support.

R29 completed boundary:

1. R29-G0 passed the three-checkpoint reward-off gate. The natural on-policy
   action-information target is positive against the cyclic sham and the
   inactive-FiLM control is numerical zero.
2. External review modified R29-G1 into R29-T10. For each complete natural skill
   lifetime, the collection actor is replayed from the stored pre-step hidden
   state under each fixed candidate skill. The uniform density ratio uses the
   final 10 action likelihoods, then adds one detached clipped reward at the
   lifetime endpoint. Length-batched replay keeps this tractable on GPU; the
   actual-skill column is anchored to PPO's stored old likelihood after removing
   the common tanh Jacobian, while cross-skill columns follow full replay. This
   avoids CUDA GRU batch-shape drift without weakening the source likelihood.
3. The authorized single-seed `probe_only` versus `real_reward` pair completed
   at +320K steps per arm. Implementation was valid, but the score, R26
   transfer, and task-safety gates failed.
4. GPT-5.6 Pro returned `RETIRE`; the disposition and failure review accepted
   R29 as diagnostic-only and retired the online actor-density-ratio family.

Completed R31 boundary:

1. Keep R30 unchanged. Each genuine post-edit check opens one complete natural
   stochastic window per agent with fixed `W=k0`; incomplete terminal/update
   windows are invalid.
2. Alice--Bob effect input is normalized joint agent positions only. Build a
   focal/teammate endpoint and late-half displacement effect, conditioned on
   start positions and teammate skills. Exclude action, task reward, task
   identity, button/target/contact/phase, age, length, agent ID, and OPT compact.
3. Train a full effect posterior and context-only posterior on natural windows.
   Use signed `log q_full - log q_context`; matched shuffle is gate-only.
4. Score a rollout with the posterior frozen after the previous rollout, inject
   no reward in `probe_only`, run low PPO, then update the posterior from the
   detached natural windows. A later `real_reward` mode may inject one detached
   signed clipped endpoint reward per fixed block; it never enters R30 high
   return.
5. Keep the one-step transition discriminator as legacy diagnostic-only and
   fail closed if its reward, R28/R29 reward, environment shaping, wrong window
   length, forbidden input, incomplete-window reward, or high reward injection
   is active in R31 mode.
6. Implement a reward-off forced stochastic audit from matched simulator/RNG/
   recurrent-state contexts. Teammates resample their policy under common random
   numbers rather than replaying an action tape. Forced windows never train the
   natural scorer.
7. Only a reward-off PASS authorizes the registered 160K paired R31 reward
   comparison. FAIL retires CFEI; UNDERPOWERED adds only the same reset batch.

Core MARL impact: R31 reconstructs only the individual persistent-effect half
of HMASD's intrinsic exploration loop. It does not establish team composition,
delayed cooperative credit, sparse-task improvement, asynchronous-lifetime
benefit, or HMASD parity.

Gate result: valid `FAIL`. Natural heldout information was positive, but the
direct forced-skill between/within ratio was below one. The old absolute
near-zero matched-shuffle null was invalid and is no longer a failure reason;
the direct M2 independently retires R31-CFEI and its conditional reward pair.

## R32 Interventional Fixed-Window Effect Policy Gradient

Active causal edge:

```text
randomized focal-skill intervention
-> noise-corrected persistent effect separation
-> skill-FiLM-only actor change
-> natural joint-state coverage
```

Accepted design source: the raw `VALID FAIL / R32-IFEPG` response under
`docs/external-review/gpt5_6_pro/20260714_r31_cfei_gate_result/`.

One coherent implementation and evidence boundary:

1. From natural adaptive-R30 decision snapshots, force every focal skill for
   two independent stochastic `W=k0=10` replicas. Freeze the teammate behavior
   actor at each auxiliary round and keep teammate skills fixed.
2. Compute the signed cross-replica U-statistic over the existing eight-value
   normalized-position effect and average across six skill pairs and eight
   effect dimensions. Do not rectify negative scores.
3. Standardize each context score against a leave-one-context baseline and use
   it in one focal-action PPO-clipped surrogate epoch (`clip=0.10`, gradient
   clip `0.5`). Use the existing low actor learning rate `3e-4`, because the
   external contract introduced no separate auxiliary learning rate.
4. Train only `low.actor_film`; freeze actor base/RNN/action head/log standard
   deviation, critic, R30 high controller, OPT/bridge, and all posterior paths.
   No reward, value loss, GAE, entropy objective, task return, or high update
   enters the auxiliary step.
5. Keep R32 out of the normal trainer. The paired gate compares no-step
   `probe_only` with `real_update` from the same frozen R30 checkpoint and
   source context bank: 20 x 32 training contexts, 128 heldout contexts, four
   skills, two replicas, and one seed `32031`.
6. M0 checks exact branch counts, focal replay likelihood, FiLM/non-FiLM drift,
   and forbidden updates. M1 requires heldout causal SNR improvement; M2
   requires increased between-skill effect without within-skill noise growth;
   M3 requires natural 625-cell coverage transport while preserving R30
   lifetime and switch-skill supply.
7. M0 failure is implementation-invalid and permits only repair. Any valid
   M1--M3 failure retires direct IFEPG with no tuning or UNDERPOWERED branch.
   PASS authorizes only later production integration from a genuinely sparse,
   unshaped R30 source.

Core MARL impact: effect tensors are `[context, skill, replica, 8]`; actor
likelihood replay is `[context, skill, replica, W]`. Old behavior likelihoods,
effect scores, and standardized advantages are detached. The only gradient path
is current focal log-probability -> frozen actor stack -> skill FiLM. Natural
R30 clocks, masks, skill rosters, high returns, collectors, and checkpoint
format remain unchanged.

Gate result: valid `FAIL_M1_RETIRE_R32_IFEPG`. M0 passed, including exact
branch counts, maximum replay error `4.77e-6`, positive finite FiLM drift, zero
non-FiLM drift/gradient escape, and zero forbidden updates. The real causal
ratio reached only `1.015540` (CI `[0.877865, 1.207808]`), paired gain was
`0.028746` rather than `0.40`, and skills 0/1 remained below pooled ratio one.
Between-effect growth was `1.029965x` with unchanged within noise; natural
coverage grew only `1.012821x` with a paired CI crossing zero. R30 lifetime and
switch-skill safety passed. Retire direct IFEPG and all learning-rate,
update-count, window, replica, effect, threshold, seed, or scope variants.

Next boundary: external review must choose exactly one structurally different
R33 edge and its smallest Alice--Bob abandonment gate. It must explicitly
decide whether the individual-effect line is exhausted and complementary team
composition is now the missing causal level. Do not implement another R32
rescue or normal-trainer path.

## R33 Interventional Role-Swap Complementarity

Active causal edge:

```text
natural R30 context
-> randomized complete-roster effects
-> non-additive stable role-swap complementarity
-> exact high-level complementary-roster selection
-> natural joint and role-free coverage
```

The raw GPT-5.6 Pro review selected complete-roster composition. Controller
disposition is `MODIFY` because its original contrast was also large for
independently executed skills. For each agent and replica, R33 double-centers
the complete `4 x 4` effect table over both roster axes, then scores the
antisymmetric role-swap component minus the symmetric orientation component.
This removes agent/skill additive main effects and rejects one-sided pair
effects.

One implementation/evidence boundary:

1. Collect 16 complete final rosters, two independent replicas, and `W=10`
   stochastic steps from each natural R30 context. The branch-effect tensor is
   `[context,4,4,2,2,4]`; intervention trajectories are shared by both arms.
2. Compare `real_complementarity` with the fixed pair-permutation `pair_sham`.
   Their per-context roster-score multisets are identical.
3. Teacher-force all 16 KEEP/SET sequences through the existing R30
   `evaluate_sequence` and minimize the exact expectation of the detached
   standardized score. The roster-probability tensor is `[context,16]`.
4. Gradient enters only `FixedClockAREditPolicy.skill_head`. Keep the low
   actor, KEEP head/shared trunk, critics, OPT/bridge, posteriors, environment,
   reward, GAE, and normal high PPO frozen/outside the objective.
5. Add only
   `ha_ctse_process/r33_interventional_roster_complementarity.py` and
   `scripts/r33_roster_complementarity_gate.py` before the mechanism result.
   Do not modify the normal controller, trainer, or Alice--Bob environment.

The exact budget, thresholds, null, validity rules, and abandonment branches
are owned by `memory/ExpRecord.md`.

Gate result: valid `FAIL_M1_RETIRE_R33_IRSC`. M0 passed with exact roster
probabilities, score-multiset parity, finite head-only gradients and zero
non-head drift. Real mapping produced only `0.001955` heldout expected-score
gain and `0.001250` correct-top-two-pair mass gain; both were positive but two
orders of magnitude below their gates. Natural joint and nonredundant coverage
were slightly below pair-sham while R30 lifetime and skill supply remained
healthy. Retire direct intervention-scored roster-complementarity selection;
do not tune or integrate it.

## R34 Balanced Hindsight Mode Distillation

Active causal edge:

```text
unlabeled natural focal trajectories
-> balanced hindsight mode labels
-> full-episode recurrent low-actor distillation
-> intervention-reproducible numerical skills
-> frozen-R30 natural use
-> joint-state coverage transport
```

The two GPT-5.6 Pro responses selected the same route. Controller disposition
is `MODIFY`: response B's full-episode replay supersedes stale block-start
hidden replay; a frozen-source anchor prevents sham damage from masquerading as
mode creation; focal-only displacement labels keep the target controllable by
the focal skill; and mode formation, zero-shot selector use, and coverage are
separate result branches.

One implementation/evidence boundary:

1. Add only `ha_ctse_process/r34_balanced_hindsight_mode_distillation.py` and
   `scripts/r34_bhmd_gate.py` before the gate result.
2. Fit exact-balanced four-mode prototypes on train-only focal displacement
   sequences, then align their names to old numerical skills only for R30
   interface compatibility.
3. Compare `real_modes` and a maximum-Hamming episode-sequence sham from paired
   initial actors, with the unchanged source as a no-update anchor.
4. Replay complete 80-step source episodes from zero hidden and update only
   low actor FiLM, recurrent layers, and action mean. Recompute current prefix
   hidden for every heldout forced block.
5. Keep the normal trainer, R30 controller, environment, rewards, critics,
   OPT/bridge, and posteriors unchanged. The exact budget and decision contract
   are owned by `memory/ExpRecord.md`.

Gate result: valid `FAIL_M1_RETIRE_R34_BHMD`. All M0 checks passed and the
maximum-Hamming sham was strongly disrupted. Real distillation raised forced
fidelity only `0.0654` over the frozen source, below the registered `0.15`
gain, while persistent-mode SNR fell from `1.7608` to `1.5235`
(`real-source=-0.2962`, wholly negative CI). Natural mode agreement improved
only `0.0488`, and joint coverage did not improve over source under the paired
reset statistic. R30 safety passed. Retire fixed balanced hindsight mode
distillation and do not tune or integrate it; the next implementation boundary
must come from one structurally different post-R34 causal edge.

## R35 Sparse MAPPO Reset Baseline

Active causal question:

```text
matched sparse-reward low-level optimization
-> observation/history-only recurrent MAPPO versus active R30 skill editing
-> Alice--Bob task access and paired noninferiority
-> decide the optimization baseline, not a new paper contribution
```

The final GPT-5.6 Pro response correctly closes R35-OCSF, CBF, and TMPF and
selects a no-skill reset. Its trained-versus-frozen comparison is invalid, so
the controller accepts one modified pair:

1. Construct one neutral zero-step R30 checkpoint and load it into both arms.
2. `constant_code_mappo` keeps the existing four-column low FiLM and recurrent
   centralized critic shapes, but supplies dummy skill/team code zero at every
   step. It never executes or updates the high editor. Constant conditioning
   makes its behavior observation/history-only while preserving low capacity.
3. `reward_pure_r30` trains the same low stack and its KEEP/SET high editor.
   Both arms receive only the sparse Alice--Bob collection reward.
4. Match low rollout, recurrent minibatch, PPO epoch, actor/critic optimizer,
   environment-step, reset, and evaluation exposure. Report R30's additional
   high optimizer steps as the treatment rather than calling total optimizer
   exposure matched.
5. Add only the episode-level 625-cell joint-position coverage and zero-cycle
   flag required by the gate. Do not add a classifier, intrinsic reward, OPT
   actor input, new scheduler, or trained-checkpoint migration.

The exact budget, access floor, noninferiority margins, outcome branches, and
single result source are owned by `memory/ExpRecord.md`.

## Legacy Compatibility Boundary

- This branch is for constructing the new HA-CTSE/process algorithm, not for
  conservative HMASD maintenance.
- Keep old `hmasd`/`hmasd_original` runnable only as comparison baselines when
  doing so does not block the new algorithm.
- Do not keep fixed-k HMASD data-flow assumptions inside the HA-CTSE core just
  to preserve old behavior.
- Preserve archived `_server_package_*` folders by not editing them.

## Ruled Out / Stop Rules

- Segment posterior `q(z | S, g)`, context-residual posterior, and
  future-cooperation outcome residual probes repeatedly failed to beat
  shortcut/context baselines as reliable positive intrinsic rewards. Keep them
  diagnostic-only unless a new run pre-commits a falsification metric.
- Topology-role discrimination is the final classifier-style semantic probe in
  this family. If its full classifier does not sustainably beat the
  OPT/context/duration shortcut, stop adding new residual-discriminator heads.
- Duration-only shortcut is now a hard gate for segment-posterior intrinsic
  reward: if duration-only accuracy is not worse than posterior accuracy by the
  configured margin, segment posterior reward is zeroed before it can affect
  either high or low policy updates.
- Process reward with magnitude far below environment reward remains
  diagnostic-only unless explicitly changed to a centered/advantage-style
  shaping mode.
- Detached same-action actor-density ratios are diagnostic-only. Do not create
  online variants by changing their prior, window, aggregation, coefficient,
  normalization, or clip.


## Archived Plan History

Completed R22/R24/R26/R27 implementation detail is preserved by the frozen
designs and `docs/archive/legacy-memory/`. Read historical imports only when
this plan points there or the user asks for history.
