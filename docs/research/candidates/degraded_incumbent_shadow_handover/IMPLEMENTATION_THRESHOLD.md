# DISH promotion-source-factored implementation threshold

Status: `SCIENCE_FROZEN_TEST_SCAFFOLD_ONLY_PRODUCTION_BLOCKED_BEFORE_CHECKPOINTS`

Object: `DISH-PROMOTION-SOURCE-FORK-R01`. The bounded TEST_ONLY transaction scaffold is complete.
The inherited trainer currently disagrees with the frozen role/recurrent/normalization law, and the
fresh checkpoint, real first-valid path, replay certificate, 6,912-cell data plane, inference,
resource preflight, request, and direct runner remain unaccepted. No fresh checkpoint or scientific
result command is presently admissible.

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
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_real_sham.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py`
