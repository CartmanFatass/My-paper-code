# DISH block-certificate prevalence R02 implementation threshold

Status: `R02_CONDITIONAL_SCIENCE_PASS_PRODUCTION_INVESTMENT_STOPPED_CLOSE_RECOMMENDED`

Current scientific object: `DISH-BLOCK-CERTIFICATE-PREVALENCE-R02`.

Transaction substrate: `DISH-PROMOTION-SOURCE-FORK-R01`, ABI v1. The bounded TEST_ONLY transaction
scaffold and isolated two-owner phased/pathwise oracle remain accepted substrate. The full
production chain remains unaccepted, so no fresh checkpoint or scientific result command is
presently admissible.

## Controlling R02 supersession

R02 replaces the R01 continuous-mean/bootstrap inference object. R01 transaction, causal-fork,
endpoint, margin, and sidecar details below remain provenance and reusable substrate when they do
not conflict with this section. R01's 99,999-resample max-t, zero-SE rules, mean-return authority,
single first-match branch, generic-transfer wording, coupled support, and scientific hold are not
current executable authority.

The R02 population is exactly 24 independent roots
`U_b ~ Uniform({0,1}^256)`. Duplicate roots are retained. Every root enters the same canonical local
address map `F(U_b)`; global `b` is storage/order only and never enters an RNG address. Each root
censuses `2 packages x 3 schedules x 3 speeds x 16 slots`. Future physical, exogenous, and
evaluation stochastic addresses and the counter frontier are identical across RETAIN, COPY, and
SHADOW. Branch identity never enters a scientific RNG address; its non-RNG roles are limited to
transaction metadata, output metadata, and deterministic intervention state.

Four separately frozen exact-binomial tests cover
`COPY-RETAIN x {VALUE, NO_MATERIAL}` and
`SHADOW-COPY x {VALUE, NO_MATERIAL}`. Each test uses `alpha=1/80` without recycling and rejects
`p<=1/2` only at `K>=18` of 24 roots. The exact boundary tail is
`190051/16777216`; the Bonferroni family bound is `190051/4194304`; planning power at `p=0.8` is
`48343602127962112/59604644775390625`. Failure to reject VALUE never implies NO_MATERIAL. The
endpoint and anchor speed are root-local existential witnesses and may differ by root; no fixed
endpoint/anchor prevalence follows.

The two axes retain Cartesian dispositions. COPY means only atomic owner/actuator remap under the
common transaction shell, not generic or natural transfer. SHADOW VALUE additionally requires the
SHADOW-RETAIN total safeguard. Replay is an orthogonal SHADOW-only modifier and requires every
endpoint row, complete post-CAS native/policy/Welford/RNG state, and the full 100-tick twin; first
action equality alone is insufficient. R02 has algorithmic-root certificate-prevalence authority,
not expected/mean return, natural prevalence, optimal-COPY, unique-information, training-advantage,
safety, deployment, or flight authority.

The root panel is create-only. A failure before panel creation may create a fresh panel. After the
panel exists, a technical repair must rerun outcome-blind from the beginning with the same 24 roots;
redraw is forbidden. Missing instrumentation, bare nonfinite data, transport mismatch, or missing
required endpoints makes the assignment incomplete and non-consuming. Only a preregistered typed
`ALGORITHM_RUNTIME_OR_NONFINITE` terminal record may materialize finite worst-case endpoints and a
hard-event flag; that is a scientific zero/harm, not technical incompleteness.

## Current R02 implementation fact — 2026-08-31

`production_source_factored_reducer.py::exact_prevalence_preview` implements only result-blind
algebra preview under schema `DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_REDUCER_PREVIEW_V2` and status
`TEST_ONLY_NOT_READY`. Its output fixes
`scientific_object_consumed=false`, `scientific_tests_executed=false`,
`production_result_authority=false`, and `question_relevant_output=false`; caller-constructed root
indicators cannot publish or accept R02 evidence. A formal sealed branch producer, create-only
24-root parser, typed terminal parser, complete result parser, and production publication path are
still absent and remain part of the engineering gaps below.

The final focused DISH namespace passed `62` tests. Independent post-fix engineering review returned
`CLEAN` with no remaining Blocker or High. These observations establish TEST contract conformance,
not production readiness or scientific polarity. No result-bearing experiment was run.

## Remaining production blockers

Exact prevalence inference removes the former inference hold, but these ten engineering gaps remain:

1. production source-factored normal-tick and generator path;
2. checkpoint snapshot bridge and recurrent-handoff integration;
3. causal-vector and role-indexed policy integration;
4. role-indexed live/snapshot/PPO replay integration;
5. source-specific masked per-dimension Welford integration;
6. fresh-prefix producers and addressed minibatch frontier;
7. exact uninterrupted/resume checkpoint parity;
8. full typed causal replay and directly observed deadline;
9. shared block checkpoint plus typed no-trigger data plane; and
10. direct process-tree/filesystem resource preflight.

The guarded runner remains `NOT_READY` until all ten close. Immediately before every future
result-bearing invocation, resume, retry, or slice, run
`python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and require both physical
and effective available memory to be at least 4 GiB. The check must precede scientific roots,
masters, models, optimizers, checkpoints, and results.

The wave-2 freeze in
`evidence/2026-08-30-dish-promotion-source-fork-wave2-freeze.md` controls every production detail
that was previously implicit or ambiguous. It narrows and repairs this same object; it does not
reopen REAL/SHAM or full R06.

## Resolved transaction freeze

Let the intent originate at renewal `n` and application be `t*=n+1`. The trigger is the earliest
application-valid STRUCTURED boundary with
`tau_d_tick <= t* < tau_d_tick+200` and `t*<=1100`. After `t*` arrivals and immediately before CAS,
every branch
consumes the pending intent, increments `service_epoch`, sets `handover_used`, clears lineage locks,
invalidates old transaction versions, suppresses later transfer, emits an equal-size receipt, and
pays identical bytes, one-tick latency, and energy.

- `RETAIN`: no CAS; incumbent remains owner/actuator and its active recurrent state remains
  authoritative. Record `cas_applied=0, retained_by_design=1`; this is not an invalid commit.
- `TRANSFER_COPY`: legal incumbent-to-standby CAS/remap; recipient active state is an exact copy of
  incumbent active state (`alpha=0`).
- `TRANSFER_SHADOW`: identical CAS/remap; recipient active state is the pre-warmed standby shadow
  (`alpha=1`).

COPY and SHADOW share the successful CAS tuple and differ only in promoted-state-source bytes.
The application SLEW check uses stored origin history exactly
`||b_i[n]-a_i[n-1]||_2<=1.5` for both physical entities; current application-tick
`StepInput.raw_action` is forbidden. The arrival phase includes any causally delivered snapshot
assimilation through the frozen snapshot normalizer/bridge. The immutable cut contains recurrent
state after that assimilation but before the `t*` actor-observation GRU update. Each branch applies
its transaction, advances the common post-transaction observation
phase, materializes its `t*` observation, and then performs exactly one policy forward. No
application-tick observation is consumed twice.

## Estimands and claim ceiling

From one immutable pre-CAS checkpoint and one remaining physical tape:

```text
Delta_transfer = benefit(TRANSFER_COPY, RETAIN)
Delta_shadow   = benefit(TRANSFER_SHADOW, TRANSFER_COPY)
Delta_total    = benefit(TRANSFER_SHADOW, RETAIN)  # safeguard/report only
```

`Delta_transfer` identifies generic owner/actuator transfer conditional on a STRUCTURED-selected
valid event. `Delta_shadow` identifies only incremental promoted-state-source value under a policy
trained with SHADOW promotion. `TRANSFER_REPLAY` is a certificate-only containing null, outside the
6,912-row scientific population and simultaneous family. It replays a generator-produced typed
causal actor/snapshot/reset/message ledger through the same checkpoint and frozen Welford state from
zero recurrent state, without recurrent bytes, critic/evaluator truth, opaque SOURCE, future tape,
extra training, or extra wire bytes. It must reproduce all four pre-CAS tensors, the SHADOW post-CAS
state, and first projected action exactly within `0.1s` by direct monotonic timing. RETAIN, COPY, and
SHADOW run 100 production ticks; replay needs only an exact 100-tick TEST twin because complete-state
equality implies production trajectory equality by induction.

The maximum claim is fixed-host, finite-budget, first-trigger-conditional evidence for generic
atomic transfer and/or source selection under SHADOW-trained checkpoint co-adaptation. It does not
cover an optimally trained COPY policy, arbitrary checkpoints, `k`, speed, `N`, natural prevalence,
unique information or mediation, training advantage, shadow cost-effectiveness, full R06, safety,
deployment, or flight.

## Population, clocks, RNG, and work

The production RNG namespace is exactly `DISH/PROMOTION-SOURCE-FORK/R01`; retain the R06 field
vocabulary and allocation equations after that prefix substitution. The direct runner generates
one nonreplaceable 32-byte OS-CSPRNG master into an empty run root with exclusive create-only
semantics. Resume reuses it. The request rejects every caller master, seed, or RNG override.

Train only 24 STRUCTURED
jobs under the inherited 1,024-update × 4,096-transition law. The sole block checkpoint is the
model, complete AdamW state, and exact actor/snapshot/critic masked-Welford state immediately after
update 1,024; it is never selected or replaced. Evaluation recurrent state starts at zero and never
inherits training recurrent/native state. Evaluate only the 6,912 claim cells:
24 blocks × 2 packages × 3 claim schedules × 3 speeds × 16 slots. Preserve no-trigger rows; no seed
replacement or selected checkpoint.

`dt=0.1s`; external `k` changes only at renewal. Intent originates at renewal `n`, application is
`n+1`, and every fork runs exactly 100 primitive ticks. Forks receive zero optimizer updates.
Checkpoint, normalization, causal prefix, pre-fork exogenous addresses, and future physical tape are
identical. Physical entity identity and `N=2` stay fixed; only owner/standby role changes.

For every block/cell, pre-onset competence is

```text
C_PRE = (1/16) sum_i [(1/200) sum_{q=tau_d_tick-200}^{tau_d_tick-1}
                                   valid_service_MASK_ON[i,q]].
```

The denominator is always `16*200`; absorbing terminal service is zero and no-trigger rows remain
included. Require simultaneous `L(C_PRE)>=0.85`. Let `T` mark the valid first trigger and
`R=sum_i T_i/16`; require at least one trigger in every block/cell and simultaneous
`L(R)>=0.10,U(R)<=0.90`. Separation uses projected physical actions, not raw heads, with
`d_a=||a_A-a_C||_2/6`, state distance `d_h=||h_A-h_C||_2/sqrt(128)`, and `epsilon=1e-3`.
The sixteen-row COPY-action and SHADOW-state-plus-action support rates each require one positive row
per block/cell and simultaneous lower bound `>=0.10`. No five-arm calibration, learned NEVER
headroom, or full-R06 WITNESS gate is inherited; generic headroom is `Delta_transfer` itself.
Failure is nonidentification.

## State ownership and atomicity

Native state owns physics, filters, SOURCE/base buffers, owner token, actuator authority, epoch,
payload sequence, protocol locks, held action, costs, hard events, and tape coordinates. PyTorch owns
checkpoint, four recurrent copies, and Welford state.

The physical recurrent order is `[U0-I,U0-S,U1-I,U1-S]`. With owner `o` and standby `s=1-o`, owner
motion and prepare read `h^I_o`; standby motion, commit, and service/source decisions read `h^S_s`.
Live collection and PPO replay must use that same role-indexed law, stored fragment-initial recurrent
state, entity-aware promotion, causal masks, normalized inputs, and old-policy likelihood.

Actor, snapshot, and critic require separate source-specific masked Welford transforms. Only each
declared continuous present field updates and normalizes; an absent continuous field is excluded and
forced to normalized zero; Boolean/one-hot fields pass through. A scalar count shared across fields
is insufficient where presence differs. Snapshot and critic forward paths and PPO replay use their
declared transforms. Each update's final Welford state is the next rollout's start state, and the
update-1,024 state is frozen for evaluation. Current inherited scalar/all-field/raw-snapshot/raw-
critic semantics are not accepted authority.

The exact one-based continuous index sets are actor
`{5..11,13,14,16..25,27,29..36,42,43,49,51,53}` and critic
`{1..11,13,14,16..18,20,21,23..29,31,32,34..36,38,39,42..45,48,49,54,55}`;
all remaining indices are Boolean/one-hot passthrough. Actor presence gates are
`13..14<-12`, `27<-26`, `29..36<-28`, `51<-50`, and `53<-52`. Critic presence gates are
`13..14<-12`, `20..21<-19`, `31..32<-30`, `38..39<-37`, and `42..45<-41`.
The snapshot normalizer has eighteen continuous dimensions and updates only for accepted snapshots
in delivery order. Counts are per dimension; use variance one below count two, otherwise
`M2/(count-1)`, epsilon `1e-8`, clip `[-10,10]`, and normalized zero when absent. Raw present values
update lane-major, tick-major, physical-UAV, I-then-S; critic updates once per lane/tick.

Production requires a distinct additive sidecar ABI with its own versioned layouts; it may not add
fields or exports to the shared R06 `HostState`, `ResetInput`, backend library, or Python ctypes
surface. Keep the current TEST clone and every REAL/SHAM source/export bytewise untouched. The
conceptual sidecar split is:

```cpp
int32_t dish_psf_r01_begin_tick_batch(
    const DishPsfHostStateV1* parent,
    size_t count,
    DishPsfPreparedTickV1* out);

int32_t dish_psf_r01_clone_prepared_batch(
    const DishPsfPreparedTickV1* prepared,
    const DishPsfRecurrentHandoffV1* post_arrival_assimilated,
    size_t count,
    DishPsfForkOutputV1* out);
```

`begin_tick` is nonmutating and owns arrivals/buffer replacement plus the typed snapshot-
assimilation request and stored-origin application predicate. Python performs only the frozen
checkpoint/Welford snapshot bridge. `clone_prepared` validates that recurrent handoff, leaves its
inputs immutable, and applies RETAIN/COPY/SHADOW before branch observation materialization. No
generic `StepInput` or caller-edited owner field enters either interface.

The linearization tuple binds owner, epoch, next payload sequence, `k` epoch, intent origin,
snapshot/readiness versions, lineage, and controller-hidden bytes. Python never writes native
ownership fields. Branch-specific observations are materialized before the first policy forward.
Create-only generations atomically bind native snapshot, rollout/Welford state, checkpoint, RNG
frontier, typed causal prefix, and receipts; sealed coordinates cannot be reforked. A typed
`NO_TRIGGER` generation instead binds its complete scan and contains no fork receipts or endpoints.
Store each create-only block checkpoint once and reference it from that block's 288 coordinates;
per-cell checkpoint duplication is forbidden.

## Endpoints and branches

Primary 100-tick endpoints are mean service, fractional worst-10% tail service across triggered
tapes, service-deficit seconds, and capped recovery delay. An unrecovered row receives the registered
`10s` cap; this is not an uncensored time-to-event estimand. No-trigger rows affect competence and
support only. A zero-trigger block stores numeric zero plus `fork_supported=0`, and that zero has no
effect authority because support fails first. Retain material margins `(0.03, 0.05, 0.25s, 0.5s)` and noninferiority margins
`(0.01, 0.02, 0.25s, 0.5s)`. Nonharm requires energy-ratio upper bound `<=0.03`, zero invalid commit,
token gap, dual owner/payload, buffer clear, slew/separation breach, minimum separation `>=15m`, and
identical transaction size/timing/cost and policy-visible shell with no extra application tick.
Truthful output-disconnected audit receipts may name different modes/owners.

The 24 blocks are the sole inferential units. Form each trigger-conditioned paired block contrast,
then use exactly 99,999 jointly paired nonparametric block resamples with one common resampled block
vector across competence, trigger/separation support, both contrasts by cell/endpoint, energy ratios,
and absolute hard-event rates. Retain the R06 zero-SE rules and ordered maximum-absolute-studentized
critical value `T_(95000)`. Materiality, noninferiority, precision, nonharm, and branch Booleans are
derived from sealed rows; callers cannot supply them. VALUE needs one material endpoint at a common
anchor speed and noninferiority at every speed. The same class and nonempty anchor intersection are
required across all three schedules and both packages for the broad conclusion.

First-match branches: invalid protocol/measurement; missing competence/trigger/separation support;
`SHADOW_ABSORBED`; nonanswerable/imprecise; nonharm failure; `SHADOW_SPECIFIC_VALUE`;
`GENERIC_TRANSFER_ONLY`; target-specific no-material; unresolved. No outcome-peeking stop, seed
replacement, budget extension, or threshold change.

## Implementation surface

Reuse the existing population equations only after direct conformance to this freeze. The shared
native/backend bytes, current recurrent trainer, evaluator, data plane, and reducer are not accepted
production semantics. Existing REAL/SHAM is immutable and is never invoked as a shortcut. Add the
source-factored-only surface without changing the shared backend:

```text
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/
  native/dish_promotion_source_fork_r01.cpp
  production_source_factored_backend.py
  production_source_factored_contract.py
  production_source_factored_fork.py
  production_source_factored_reducer.py
  production_source_factored_data_plane.py
```

Add the new native output/API and explicit RETAIN/COPY/SHADOW policy-state modes without changing
existing REAL/SHAM exports. Telemetry records checkpoint identity, owner/actuator/epoch/CAS/application
reason, protocol-byte delta, transaction latency, minimum separation, and every nonharm event.

Focused tests cover both-owner live/replay/native role authority, source-specific masked Welford
forward/update/resume/evaluation equality, fragment-initial state and addressed minibatch order,
all 54 actor and 58 critic fields against a causal oracle with stale/absent delivered messages,
distinct `D/G1/G5` latches, true snapshot/readiness ages and nonzero base error,
native three-way clone allowlists, combined predicate/linearization,
exactly-once forking, `alpha=0/1` equivalence, transaction shell identity, future-address and
checkpoint equality, RETAIN suppression, replay information fence/deadline/work, complete 6,912-row
accounting with typed no-trigger rows, endpoint signs/margins/simultaneous inference/branches,
crash-resume identity, duplicate refusal, complete-result firewall, and direct CPU/RSS/I/O
observation. These are conformance checks only.

## Future direct runner shape

```text
C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe -m tools.experiments.run_dish_rbhr_source_factored_preflight \
  --repository-root C:\Projects\HMASD \
  --run-root <fresh-test-only-preflight-root>

C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe -m tools.experiments.run_dish_rbhr_source_factored_fork \
  --repository-root C:\Projects\HMASD \
  --request <prospectively-frozen-request.json> \
  --run-root C:\Projects\HMASD\temp\directions\degraded_incumbent_shadow_handover\exp\<run-id>\artifacts
```

The two thin wrapper modules now exist, but the production path intentionally does not. The direct
TEST-only preflight returns `NOT_READY`; the fork wrapper returns structured exit code `2` before
creating a run root, master, model, checkpoint, coordinate, or result. They carry no lease, identity
token, or authentication step. All science, resource reduction, lifecycle, and result logic remains
in the DISH package, and dependency tests prove the wrappers cannot call the legacy full-R06 runner
or data plane.
The request schema is `DISH_PROMOTION_SOURCE_FORK_R01_REQUEST_V1`; it contains no master/seed and
sets `master_policy=RUNNER_GENERATE_ONCE_OS_CSPRNG_256` and
`caller_master_allowed=false`. Direct preflight uses a fixed TEST master and measures exact-code
work: process-tree CPU sum, elapsed wall, peak concurrent aggregate RSS, scratch/durable bytes,
process-tree read-plus-write bytes, worker/core use, Torch threads, device, and GPU count. Caller-
supplied resource numbers and generic estimate-only admission are insufficient.

The prospective ceilings, not observed production usage, are 40 CPUh/10 wall h, at most eight
workers and eight aggregate CPU cores, one Torch thread per worker, `gpu_count=0` and `device=cpu`,
6.61 GiB peak aggregate RSS, 1.66 GiB scratch, 0.83 GiB durable output, and 68.14 GiB I/O.
Historical `GPU0` means zero GPUs here, not CUDA device ordinal zero.

Observed fail-closed receipts:

- `temp/directions/degraded_incumbent_shadow_handover/preflight/wave2-not-ready-final-reviewed-20260831/preflight-receipt.json`
- `temp/directions/degraded_incumbent_shadow_handover/preflight/wave2-resource-assessment-20260831.json`

The first receipt is explicitly a one-process fixed-TEST-master transaction sentinel. Its observed
CPU/wall/RSS/I/O values are not a projection or acceptance of the eventual full process-tree
training/evaluation/replay/reduction command.

## Evidence

- `DIRECTION.md`
- `DISH_RBHR_R06_SCIENCE_COMPOSITE_20260822.md`
- `DISH_RBHR_R06_ENGINEERING_CONFORMANCE_CM_TECHNICAL_PACKET_20260822.md`
- `evidence/2026-08-30-dish-promotion-source-fork-wave2-freeze.md`
- `evidence/2026-08-31-dish-phased-oracle-inference-hold.md`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_real_sham.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py`

## Wave-3 implementation threshold — 2026-08-31

The following TEST-only threshold is directly closed:

- independent phased ABI with nonmutating parent/prepared/handoff inputs;
- typed linearization binding and rejection of lane-swapped, stale, malformed, or wrong-recipient
  recurrent handoff;
- exact two-owner RETAIN/COPY/SHADOW source promotion before branch observation and before one policy
  forward;
- full 54/58 native causal vectors matching a separate Python oracle;
- actor/snapshot/critic per-dimension masked Welford with Boolean gate validation and exact state
  round-trip;
- independent live and typed-replay one-tick paths using stored fragment-initial state, explicit
  owner history, frozen `W^u`, equal hidden/logits/old log probability, ratio one, and equal
  post-collection `W^{u+1}`.

The complete R06 direction tests pass `48` tests. A fresh V2 TEST preflight observes the oracle from
read-only native caches with zero compiler children, but truthfully returns
`passed=false,status=NOT_READY,production_mode_reachable=false` and retains both scientific holds.
These facts remove the old absence of a minimal
phased/pathwise TEST discriminator, but do not close production integration. The runner remains
`PRODUCTION_NOT_READY`; normal-tick generation, real snapshot bridge, production trainer/PPO,
resume parity, full replay/deadline, shared block checkpoint/no-trigger plane, complete resources,
and a valid request/result path remain absent.

There is also a controlling `PROSPECTIVE_INFERENCE_HOLD`. The frozen max-t law has no finite-sample
coverage for the declared bounded/discrete block law, and the support/result algebra incorrectly
couples the generic-transfer and shadow-source axes. A revised fixed-panel or finite-sample-valid
superpopulation target, per-axis branch algebra, and replay scope must be prospectively frozen
before any production checkpoint work. Passing the TEST oracle cannot override this hold.

## R02 convergence stop — 2026-08-31

The R02 exact-binomial calculation supersedes the obsolete max-t hold above, but independent audit
found that the executable `F(U)` is not yet total, fixed before sampling, or proven independent of
the sealed panel. Equal root bytes can receive different TEST-preview witnesses across storage
indices; legacy geometry/addressing is block-indexed; repair can be panel-adaptive without reading
endpoints; and pre-fork algorithmic terminal states are incomplete. `WITHIN_MARGIN` versus
`NO_MATERIAL` wording and SHADOW-only replay scope also remain inconsistent between freeze and
preview.

Any future seal would have to retain the exact scientific request and complete source/native/
config/numeric/RNG/endpoint/reducer bundle as create-once raw bytes before reading entropy. Retry
requires direct raw-byte equality or a direct all-domain scientific behaviour-equivalence proof.
Hashes, digests, identities, or authentication values are not scientific or runtime gates. The
root is a separate 32-byte scientific key; canonical local addresses contain only semantic local
coordinates and never storage index or transaction branch.

Root stopped further implementation and result preparation before such a seal. The attempted
root-panel/address files were unreviewed, violated the anti-hash boundary, and were deleted. Thus
the formal producer/parser remains absent, all ten gaps above remain `REPAIR_REQUIRED`, and no
production command is admissible. The controlling convergence evidence is
`evidence/2026-08-31-dish-r02-production-investment-stop-and-closure.md`; it recommends closure of
the current object with no registered successor.
