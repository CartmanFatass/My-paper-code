# DISH promotion-source fork wave-2 scientific freeze

Date: `2026-08-30`

Object: `DISH-PROMOTION-SOURCE-FORK-R01`

Baseline audited: `1bea5cc9b0780a8986fb66df65976de376eb57e6`

## Conclusion

The RETAIN/COPY/SHADOW decomposition is scientifically coherent, but the current bytes are not
eligible to create the 24 fresh checkpoints or a result. The accepted source-factored code proves a
narrow TEST-only native transaction fact. It does not yet instantiate the declared STRUCTURED
policy process, execute the replay null, represent no-trigger rows, perform the frozen inference, or
measure production resources.

The strongest implementation contradiction is upstream of the fork. The frozen controller uses
owner motion from `h^I_owner` and standby motion plus commit from `h^S_standby`. The inherited live
path, optimizer replay, and native promotion use different fixed copy indices. Its recurrent replay
also starts each fragment from zero and does not reproduce the behavior normalization path. A fresh
update-1,024 checkpoint from that path would therefore not be a sample from the declared STRUCTURED
process. This is an engineering invalidity and supplies no scientific polarity.

The smallest next discriminator is a two-owner, one-tick pathwise conformance test joining native
execution, live collection, PPO replay, normalization, and promotion. Fresh training may begin only
after that and every result-blind production acceptance below pass.

## Question and non-goals

At the same natural first application-valid STRUCTURED boundary and on the same remaining physical
tape, does generic owner/actuator transfer help relative to retention, and does selecting the
pre-warmed standby-shadow recurrent state help beyond copying the incumbent active state?

The two estimands are kept separate:

```text
Delta_transfer = benefit(TRANSFER_COPY, RETAIN)
Delta_shadow   = benefit(TRANSFER_SHADOW, TRANSFER_COPY)
Delta_total    = benefit(TRANSFER_SHADOW, RETAIN)  # safeguard/report only
```

This is not full R06. It does not train FLEX, NEVER, IMMEDIATE, or HYSTERESIS; does not run the
legacy REAL/SHAM path; and does not inherit five-arm competence, NEVER headroom, or full-R06
WITNESS branches. It cannot support natural trigger prevalence, an optimally trained COPY
algorithm comparison, training advantage, unique mediation, arbitrary hosts, arbitrary `k`,
variable `N`, safety, deployment, or flight.

## Inputs

- `AGENTS.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/research/portfolio/PORTFOLIO.md`, DISH row at the audited baseline
- `docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md`
- `docs/research/candidates/degraded_incumbent_shadow_handover/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RBHR_R06_SCIENCE_COMPOSITE_20260822.md`
- the six R05 normative manifests incorporated by that composite
- the accepted source-factored source and tests under
  `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/` and
  `tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/`

## Direct observations

1. The complete direction test namespace passes `22` tests in the intended
   `hmasd-amd-cpu` environment; `8` are source-factored tests. They are TEST fixtures, not a
   production observation. The source-factored subset was independently observed as `8 passed in
   1.14s`.
2. The native source-factored predicate accepts only TEST modes `1` and `2`; production resets use
   mode `0`. The only Python entry is named `clone_test_only`. A production clone cannot currently
   reach the accepted native fork.
3. The 6,912-coordinate enumeration is exact:
   `24 blocks x 2 packages x 3 claim schedules x 3 speeds x 16 slots`. The accounting object counts
   no-trigger rows, but the data plane requires three fork receipts for every coordinate. It cannot
   truthfully seal a no-trigger row.
4. The replay shell validates caller-labelled opaque bytes and a caller-declared completion tick.
   It executes no checkpoint recurrence, measures no deadline, and compares no reconstructed state
   or action.
5. The reducer computes elementary 100-tick endpoints but accepts caller-supplied scientific
   Booleans. It has no blockwise trigger-conditioned estimator, simultaneous interval, derived
   materiality/nonharm predicate, or complete first-match result.
6. The data plane duplicates opaque checkpoint bytes in a raw file and again as manifest hex for
   every coordinate. A directly materialized STRUCTURED initial checkpoint was `836,667` bytes;
   duplicating only that payload across 6,912 coordinates would be about `5.386 GiB` raw and
   `16.158 GiB` with the hex copy, already above the `0.83 GiB` durable ceiling. Production must
   store one create-only checkpoint per block and reference it from the block's 288 coordinates.
7. The current trainer's live action path always reads motion copies `0` and `2` and reads commit
   from owner-I. The frozen law requires physical-role indexing: owner-I and standby-S. PPO replay
   uses another fixed copy selection, has no owner history for entity-aware promotion, starts every
   64-tick fragment at zero rather than its stored detached recurrent state, and consumes a
   normalization path different from behavior. Actor rollout Welford state also stops following
   later checkpoint Welford updates after update 1, while snapshot and critic statistics are not
   applied on their declared forward paths.
8. The current evaluator performs a policy forward before invoking the fork observer. The frozen
   cut is after application-tick arrivals and before CAS and before the application-tick observation
   is consumed by the GRU.
9. The current resource validator accepts caller-provided numbers; it does not observe process or
   filesystem counters. A read-only host assessment for the present `6.61 GiB` peak estimate found
   only about `0.600 GiB` usable after its reserve and returned `memory_safe=false`. This volatile
   technical fact is not a scientific result; a fresh direct preflight is required after the
   production implementation exists.
10. The inherited native observation materializer also disagrees with the frozen causal vectors.
    It computes current `D` but fills actor `G1/G5` and snapshot/readiness presence/age fields from
    the preparation latch,
    reads current partner physical state where the actor contract permits only the newest delivered
    STATE packet, and hardcodes the critic base position error to zero. These are upstream
    representation/information defects; source-factored production must repair or exactly contain
    them before checkpoint creation.

## Frozen treatment and causal cut

Physical entity identity remains `i in {0,1}` throughout. Owner and standby are roles, not entity
identities. Recurrent state is attached to `(physical_entity, copy_type)` in the order
`[U0-I,U0-S,U1-I,U1-S]`.

For current owner `o` and standby `s=1-o`, live authority before transfer is:

```text
owner motion   <- h^I_o
standby motion <- h^S_s
prepare        <- h^I_o
commit, service probabilities, and any source decision <- h^S_s
```

At a valid fork, all three branches consume the intent, increment `service_epoch`, set
`handover_used=1`, preserve `next_payload_sequence` and physical buffers, clear lineage locks,
invalidate stale transaction versions, suppress later transfer, and pay the same transaction
size, timing, energy, and policy-visible shell. Audit metadata may truthfully name the branch but is
output-disconnected from policy and physics.

```text
RETAIN:
  owner/actuator unchanged; all four recurrent states unchanged.

TRANSFER_COPY:
  owner/actuator o -> s;
  h^I_s <- P_h(h^I_o); h^S_o <- h^I_o;
  h^S_s and h^I_o retained.

TRANSFER_SHADOW:
  owner/actuator o -> s;
  h^I_s <- P_h(h^S_s); h^S_o <- h^I_o;
  h^S_s and h^I_o retained.
```

`P_h` is componentwise clipping to `[-1,1]`; a conforming GRU state is already finite and in that
set, so COPY is exact on reachable support. A production API must reject a nonfinite or out-of-range
source rather than use clipping to repair a malformed recurrent state.

Let the intent originate at renewal tick `n` and `t*=n+1`. The application predicate uses the
thirteen frozen R05 checks. Its SLEW term is exactly

```text
||b_i[n] - a_i[n-1]||_2 <= 1.5 m/s^2, for i=0,1,
```

using the stored origin bounded command and prior applied command. Current application-tick
`StepInput.raw_action` has no authority for this predicate.

The trigger is the earliest valid STRUCTURED application with

```text
tau_d_tick <= t* < tau_d_tick + 200
t* <= 1100
```

so ticks `t*,...,t*+99` remain inside the 1,200-tick episode. Neither state separation nor an
outcome may select a later trigger.

The application-tick order is exact:

1. process `t*` arrivals and buffer replacement;
2. apply any causally delivered snapshot assimilation to the standby-shadow recurrent state with
   the frozen snapshot normalizer/bridge, then evaluate the application predicate from common
   pre-treatment history;
3. snapshot immutable pre-CAS native state and all four recurrent states after arrival-triggered
   snapshot assimilation but before the `t*` actor-observation GRU update,
   frozen checkpoint/Welford state, held origin actions, typed causal prefix, and remaining
   counter-addressed physical tape;
4. clone and apply the declared branch transaction;
5. advance the common post-transaction/pre-action observation phase and materialize that branch's
   `t*` actor/critic observation;
6. execute exactly one branch-specific policy forward and common action projection;
7. execute exactly ticks `t*,...,t*+99`, with zero optimizer updates.

No observation is consumed twice. Physical future RNG addresses use physical entity/packet
endpoints, never owner role or branch, and are identical across branches even when deterministic
branch behavior changes whether a value is used.

## Fresh checkpoint and RNG sample law

The production RNG namespace is exactly:

```text
DISH/PROMOTION-SOURCE-FORK/R01
```

All R06 field vocabulary and allocation equations are retained after that sole prefix
substitution. The source-factored path is additive; it does not change the R06 address function,
native REAL/SHAM exports, or existing TEST clone.

Production native execution is a distinct sidecar with versioned
`DishPsfHostStateV1/DishPsfPreparedTickV1/DishPsfRecurrentHandoffV1/DishPsfForkOutputV1` layouts.
It may not extend the shared R06 state/ctypes layouts or exports. A nonmutating
`dish_psf_r01_begin_tick_batch` performs arrivals/buffer replacement and emits the typed snapshot-
assimilation request plus stored-origin predicate state. After the frozen Python snapshot bridge,
`dish_psf_r01_clone_prepared_batch` validates the recurrent handoff and produces the three branch
states/observations. No shared `StepInput`, caller-edited ownership field, or REAL/SHAM call is a
legal production substitute.

The direct runner generates exactly one 32-byte master from the operating-system CSPRNG on the
first invocation into an empty run root. It installs that master once with exclusive create-only
semantics before any coordinate or model exists. Resume reads the same bytes. Failure, invalidity,
or interruption never generates a replacement. A request containing any master, seed, or RNG
override is rejected.

Exactly one STRUCTURED job is trained for each block `b=0,...,23`. The original five-slot arm
permutation still prospectively assigns STRUCTURED's substream, but no other arm is trained. Every
job uses the inherited 32-lane allocation and performs exactly:

```text
1,024 updates x 4,096 primitive transitions = 4,194,304 transitions
32 optimizer steps per update
```

Across the object this is 24 jobs, 24,576 updates, and 100,663,296 training transitions. No block,
job, checkpoint, or seed is selected or replaced.

The sole evaluation checkpoint for block `b` is the create-only state immediately after update
1,024. It records the model, full AdamW state, update and optimizer-step counts, STRUCTURED/block
binding, and the exact actor/snapshot/critic Welford counts, means, and `M2` values under their
continuous-field present masks. Rollout-start Welford state is frozen within an update, becomes the
next rollout's state after that update, and freezes permanently after update 1,024. Interrupted and
uninterrupted training must reproduce the same checkpoint, native/rollout state, and counter-address
frontier under the same stored master.

Normalization uses these exact one-based index sets from the frozen actor and critic vectors:

```text
actor continuous:
  5..11,13,14,16..25,27,29..36,42,43,49,51,53
actor Boolean/one-hot passthrough:
  1..4,12,15,26,28,37..41,44..48,50,52,54

critic continuous:
  1..11,13,14,16..18,20,21,23..29,31,32,34..36,38,39,
  42..45,48,49,54,55
critic Boolean/one-hot passthrough:
  12,15,19,22,30,33,37,40,41,46,47,50..53,56..58
```

Actor camera coordinates `13..14` are present iff camera-present `12`; SOURCE age `27` iff
SOURCE-present `26`; partner age/position/velocity/action/battery `29..36` iff partner-STATE-present
`28`; snapshot age `51` iff snapshot-present `50`; and readiness age `53` iff readiness-present
`52`. Critic camera coordinates `13..14` and `31..32` are gated by camera-present `12` and `30`;
SOURCE age/sequence `20..21` and `38..39` by SOURCE-present `19` and `37`; and base age/error/
margins `42..45` by base-present `41`. Every other listed continuous field is present. Critic absent
fields receive the same exclusion and forced-normalized-zero protection as actor absent fields.
Boolean/one-hot values always pass through unchanged; specified absent Boolean values remain their
declared zero.

The snapshot normalizer has exactly eighteen continuous dimensions. A row is present only for an
accepted snapshot in delivery order; a nonaccepted row neither updates the snapshot normalizer nor
enters snapshot assimilation. Every normalizer has per-dimension counts because presence may differ
by field. For each dimension, variance is one when its count is below two and otherwise
`M2/(count-1)`; normalize with epsilon `1e-8`, clip to `[-10,10]`, and force an absent normalized
value to zero. Raw present values update after collection in lane-major, tick-major, physical-UAV,
copy-I-then-S order; critic updates once per lane/tick and snapshots in accepted-delivery order.

Evaluation starts all four recurrent states at zero at tick `-1`; training recurrent/native state is
not carried into evaluation. All 288 claim coordinates in block `b` use the one block-`b`
checkpoint and its frozen Welford state. Checkpoints are never copied per coordinate or interchanged
between blocks.

Before any fresh training, a two-owner sentinel-hidden test must prove exact agreement among live
collection, optimizer replay, and native execution for role-indexed actions, prepare/commit heads,
snapshot assimilation order, normalized inputs, stored fragment-initial recurrent state,
entity-aware promotion, masks, logits, and old-policy log probabilities. The behavior-policy ratio
must equal one before the first optimizer mutation. Addressed minibatch permutations, not an
implementation-local ordering, are mandatory.

The same pretraining gate must compare all 54 actor and 58 critic fields to a separate frozen-law
oracle on histories with present and absent camera, SOURCE, partner STATE, snapshot, readiness, and
base buffers; distinct current `D`, persistent `G1`, persistent `G5`, and preparation states; both
owners; stale partner packets; and nonzero base error. Current physical partner truth may not replace
delivered STATE content.

## Replay containing null

`TRANSFER_REPLAY` is a conclusion-blind containment certificate. It is not a fourth treatment arm,
not one of the 6,912 scientific rows, and not part of the max-t family. Existing REAL/SHAM is not
called, adapted, or reopened.

For a triggered row, replay receives a generator-produced typed ledger of exactly the causal actor
observations with present masks, accepted snapshot payloads/delivery order, reset masks, and
policy-visible messages from reset through the `t*` arrival/assimilation cut, excluding the `t*`
actor observation. It receives the same block checkpoint and frozen Welford state and starts from
zero recurrent state. It may not receive retained recurrent bytes,
critic/evaluator truth, opaque SOURCE, native hidden state, future tape, branch outcome, extra
training, or extra wire data.

Replay must reconstruct all four pre-CAS recurrent tensors, the SHADOW post-CAS policy state, and
the first projected physical action exactly, while direct monotonic process timing shows completion
within the one-tick `0.1 s` application deadline under the frozen production worker resources.
Caller-declared labels or completion ticks are not observations.

RETAIN, COPY, and SHADOW each run the complete 100-tick production potential outcome. Replay does
not run a fourth production outcome: equality of complete post-CAS native state, policy state,
checkpoint/Welford state, first projected action, and counter-address frontier implies equality of
the remaining deterministic 100-tick trajectory by induction. A separate TEST conformance twin
must nevertheless run the equal SHADOW/replay state for 100 ticks to detect an implementation
violation.

If every supported triggered row is reconstructed exactly and on time, the first-match conclusion
is `SHADOW_ABSORBED` before effect interpretation. A recurrent mismatch is protocol invalidity. A
deadline miss leaves replay non-containing and permits the three-arm effect analysis; it does not
prove that replay is impossible on another resource class.

## Population, no-trigger semantics, and inference

The complete scientific population is the fixed 6,912 claim rows:

```text
b=0,...,23
package in {TARGET_VISUAL_MASK,TERRAIN_RELAY_MASK}
schedule in {K8,K4_TO_K12,K12_TO_K4}
speed in {4,6,8}
slot=0,...,15
```

Every row first executes one deterministic mask-on STRUCTURED trajectory from reset. A row with no
eligible `t*` seals a typed `NO_TRIGGER` record containing the complete trigger scan and no fork
receipt or endpoint. It is never replaced.

Pre-onset competence is defined for every block/cell, using all sixteen rows regardless of later
trigger or terminal status:

```text
C_PRE[b,c]
 = (1/16) sum_i [(1/200) sum_{q=tau_d_tick-200}^{tau_d_tick-1}
                              valid_service_MASK_ON[b,c,i,q]].
```

The denominator is always `16*200`. Absorbing post-terminal service is zero. No-trigger rows remain
in this competence denominator. The simultaneous lower bound must be at least `0.85` in every
cell. No mask-off calibration row or five-arm competence gate is part of this object.

Let `T_bci` indicate the valid first trigger. Define `R_bc=sum_i T_bci/16`. Every block/cell must
have at least one trigger and simultaneous bounds must satisfy `L(R)>=0.10` and `U(R)<=0.90`.
Applied-command, not raw-head, separation is used:

```text
d_copy_action = ||a_COPY(t*)-a_RETAIN(t*)||_2 / 6
d_shadow_state = ||h^I_SHADOW,new_owner-h^I_COPY,new_owner||_2 / sqrt(128)
d_shadow_action = ||a_SHADOW(t*)-a_COPY(t*)||_2 / 6.
```

Here each `a_A(t*)` is the ordered four-vector of physical commands
`(U0_x,U0_y,U1_x,U1_y)` after the common norm and slew projection; it is not reordered by owner
role.

With `epsilon=1e-3`, block/cell support rates are the sixteen-row means of
`T*1{d_copy_action>=epsilon}` and
`T*1{d_shadow_state>=epsilon}*1{d_shadow_action>=epsilon}`. Each needs at least
one positive row per block/cell and simultaneous lower bound at least `0.10`. A support failure is
nonidentification, not negative mechanism evidence.

Fork endpoints use triggered rows only. For each branch and block/cell, reduce the 100 service bits
to mean service, fractional worst-10% tail service across trigger-tape service fractions, mean
service-deficit seconds, and mean capped recovery delay. Unrecovered rows receive the registered
`10 s` cap; the endpoint is not an uncensored time-to-recovery claim. A zero-trigger block stores
literal numeric zeros plus `fork_supported=0`; those endpoint zeros never have effect authority
because support fails first. No-trigger rows affect competence and trigger/support prevalence, not
fork endpoints.

The 24 blocks are the sole inferential units. For every frozen estimand `h`, form one block value
`X_bh`, its 24-block mean, and `sample_sd/sqrt(24)`. Use exactly 99,999 jointly paired
nonparametric block bootstrap resamples under the new RNG prefix; the same 24-index vector is used
for every estimand. Retain the R06 zero-SE rules and use ordered critical value `T_(95000)` from the
maximum absolute studentized statistic. The family contains every C_PRE, trigger rate, both
separation-support rates, both direct contrasts by cell and endpoint, corresponding energy ratios,
and absolute hard-event rates. Replay timing/state is outside this family.

Benefits use signs `(MEAN +, TAIL +, DEFICIT -, DELAY -)`. Material margins are
`(0.03,0.05,0.25 s,0.5 s)` and noninferiority margins are
`(0.01,0.02,0.25 s,0.5 s)`. A VALUE predicate requires at least one endpoint lower bound at a
common anchor speed to reach its material margin and every endpoint at every speed to meet
noninferiority. The same class and a nonempty common-anchor intersection are required across all
three schedules for a package and across both packages for a cross-package conclusion.
`NO_MATERIAL` requires every simultaneous interval to lie within its endpoint's symmetric material
margin. Precision requires every branch-changing direct-effect half-width to be no larger than its
material margin.

Nonharm uses blockwise branch energy ratios with simultaneous upper bound `<=0.03`, zero invalid
commit, token gap, dual owner/payload, buffer clear, command-slew breach, and separation-breach
events, minimum separation `>=15 m`, identical transaction size/timing/cost and policy-visible
shell, and no extra application tick. Mode- and owner-dependent audit receipts may differ; they are
not policy-visible transaction bytes.

For a contrast, each block/cell energy ratio is the difference of the two trigger-tape mean
100-tick energy totals divided by the comparator mean. If both means are zero, store ratio zero; if
only the comparator is zero, nonharm fails deterministically. A mean of tape-level ratios or a ratio
formed after pooling blocks is forbidden.

The first-match order is:

1. invalid protocol or measurement;
2. missing competence, trigger, or separation support;
3. `SHADOW_ABSORBED` when the replay certificate contains every supported trigger;
4. nonanswerable or imprecise;
5. nonharm failure;
6. `SHADOW_SPECIFIC_VALUE` when SHADOW-COPY has VALUE and SHADOW-RETAIN is a
   noninferior/nonharm safeguard; report generic transfer value separately if also present;
7. `GENERIC_TRANSFER_ONLY` when COPY-RETAIN has VALUE and SHADOW-COPY is NO_MATERIAL;
8. `TARGET_SPECIFIC_NO_MATERIAL` when both direct contrasts are NO_MATERIAL;
9. `UNRESOLVED` otherwise.

All six package/schedule atomic results and their anchor sets are retained before aggregation.

## Direct preflight, request, and runner acceptance

`gpu=0` and historical `GPU0` mean exactly `gpu_count=0`, `device=cpu`; they do not mean CUDA
device ordinal zero. The frozen ceilings are:

```text
workers <= 8
aggregate CPU cores <= 8
Torch threads per worker = 1
gpu_count = 0
CPU <= 40 h
wall <= 10 h
peak aggregate RSS <= 6.61 GiB
scratch high-water <= 1.66 GiB
durable output <= 0.83 GiB
total process-tree I/O <= 68.14 GiB
```

The maximum native evaluation work is 6,912 natural rows times 1,200 prefix ticks plus three
100-tick fork branches per triggered row: at most 8,294,400 prefix ticks and 2,073,600 fork ticks.
Replay GRU work and 99,999 block resamples are measured separately and included in total resources.

The direct TEST-only preflight must execute the exact production update, natural evaluation,
trigger/no-trigger, three-branch fork, replay, create-only data plane, complete 6,912-row inventory,
and reducer code on non-scientific inputs. It measures rather than accepts resource assertions:

- CPU is the sum over the process tree;
- wall is elapsed start to terminal receipt;
- RSS is the maximum concurrent process-tree sum;
- scratch and durable are filesystem high-water/final bytes;
- I/O is the process-tree read-plus-write byte sum; and
- workers, affinity/core union, Torch threads, device, and GPU count are directly observed.

It must also prove one shared create-only checkpoint/Welford generation per block, typed no-trigger
rows, production-mode native reachability, exact cold/crash resume, no seed replacement, and a
complete-result firewall. It uses a fixed TEST master and creates no scientific model, checkpoint,
coordinate, or result. Generic estimate-only resource assessment is supplementary and cannot make
the runner READY.

Only the two named `tools.experiments` modules are thin command wrappers. Scientific, checkpoint,
resource-reduction, lifecycle, and result logic remains in the DISH package. Focused dependency
tests must prove neither wrapper imports or calls the legacy full-R06 runner or data plane.

The prospective request schema is `DISH_PROMOTION_SOURCE_FORK_R01_REQUEST_V1`. It binds the exact
object/configuration, counts, thresholds, resource ceilings, source manifest and Git revision,
direct preflight receipt, new run root, complete-only publication, and
`master_policy=RUNNER_GENERATE_ONCE_OS_CSPRNG_256` with
`caller_master_allowed=false`. It contains no master/seed, lease, identity token, authentication
step, or non-RNG hash-verification gate.

After implementation and direct acceptance, the exact commands are:

```powershell
C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe -m tools.experiments.run_dish_rbhr_source_factored_preflight `
  --repository-root C:\Projects\HMASD `
  --run-root <fresh-test-only-preflight-root>

C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe -m tools.experiments.run_dish_rbhr_source_factored_fork `
  --repository-root C:\Projects\HMASD `
  --request <prospectively-frozen-request.json> `
  --run-root <fresh-source-factored-run-root>\artifacts
```

At the audited baseline neither module exists, so no command is READY. The legacy full-R06 runner
is forbidden as a substitute.

## Limitations and judgment impact

The direct observations are static or result-blind engineering observations. No fresh master,
checkpoint, natural coordinate, fork endpoint, inference result, or scientific branch was created.
The replay containment proof separates information from resource advantage: the recurrent state is
a deterministic function of checkpoint, Welford state, and causal prefix, so exact on-time replay
removes an information/representation-necessity claim. A deadline miss can leave a fixed-resource
latency/precomputation advantage; it cannot prove unique information.

All STRUCTURED checkpoints are trained under SHADOW promotion semantics. COPY and RETAIN are
evaluation-time interventions outside that learned transition distribution. A positive
SHADOW-COPY effect may therefore reflect partner/policy co-adaptation to a shadow-specific hidden
code. The maximum positive claim is fixed-checkpoint, fixed-host, finite-budget evidence that the
pre-warmed source improves the registered trigger-conditional 100-tick endpoint under that trained
STRUCTURED process. A matched train-time source-exposure study would be required to raise the
ceiling.

Current judgment: production scientific status remains unobserved. The source-state question
survives, but production is stopped before checkpoint generation until the role/replay/Welford/RNG,
no-trigger, inference, storage, resource, request, and runner gates above are directly accepted.

## Wave-2 CM return — 2026-08-31

CM chose the fail-closed branch rather than approximate the coupled host/controller/trainer repair.
The final additive code records production readiness gaps, writes one TEST-only direct preflight
receipt, and exposes the two authorized thin command wrappers. The guarded fork runner returns a
structured `NOT_READY` refusal before creating its requested run root. Native/backend REAL/SHAM
bytes were restored to the audited baseline; no production sidecar ABI or partial semantic repair is
represented as accepted.

Direct result-blind observations are:

- the focused DISH suite: CM observed `32 passed in 4.95s`; an independent EM rerun observed
  `32 passed in 4.98s`;
- final reviewed sentinel-preflight status `NOT_READY`, wall `0.039019000018015504s`, current-
  process CPU `0.046875s`, peak RSS `37,023,744` bytes, I/O read `2,235,854` bytes and write
  `4` bytes;
- preflight created only its receipt directory/file and created no scientific run root, master,
  model, checkpoint, or coordinate;
- the pre-existing native TEST cache was accepted read-only with unchanged inventory and zero
  toolchain/compiler children; cache absence or ambiguity fails closed without compiling;
- the guarded fork returned structured exit code `2` and created neither its run root nor its
  parent;
- the supplementary host assessment returned `memory_safe=false`, effective available
  `5.054607 GiB`, and adjusted peak estimate `8.2625 GiB`.

This is a single-process TEST transaction sentinel measurement, not the eventual full process-tree
resource preflight required for READY. It uses the fixed TEST master only. The receipt records
twelve exact gaps: phased source-factored sidecar/begin-tick ABI; application-boundary
snapshot assimilation and recurrent handoff; causal actor and critic; role-indexed live/snapshot/PPO
replay; per-dimension masked Welford; fresh-prefix producers/minibatch frontier; resume parity; typed
replay/deadline; shared checkpoint/no-trigger plane; paired max-t reducer; and direct complete-process
resource preflight. It expressly forbids a fresh master, checkpoint, result, or REAL/SHAM substitute.
Cache source/artifact digests in this TEST receipt are read-only integrity telemetry; they do not
authorize a request, identify a scientific run, or gate a scientific conclusion.

Exact technical evidence paths:

- `temp/directions/degraded_incumbent_shadow_handover/preflight/wave2-not-ready-final-reviewed-20260831/preflight-receipt.json`
- `temp/directions/degraded_incumbent_shadow_handover/preflight/wave2-resource-assessment-20260831.json`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_source_factored_contract.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_source_factored_preflight.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_source_factored_runner.py`
- `tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_source_factored_fail_closed.py`
- `tools/experiments/run_dish_rbhr_source_factored_preflight.py`
- `tools/experiments/run_dish_rbhr_source_factored_fork.py`

Judgment impact: the exact production command remains `NOT_READY`; no scientific polarity changes.
The direction retains the recast source-state question, the accepted TEST transaction scaffold, and
the frozen reentry above.
