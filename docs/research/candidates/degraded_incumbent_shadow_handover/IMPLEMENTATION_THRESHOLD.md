# DISH promotion-source-factored implementation threshold

Status: `TEST_ONLY_IMPLEMENTATION_COMPLETE_PRODUCTION_CHAIN_MISSING`

Object: `DISH-PROMOTION-SOURCE-FORK-R01`. The bounded TEST_ONLY implementation and conformance work
are complete. The fresh checkpoint, production first-valid replay, 6,912-cell data plane, and direct
runner remain absent; therefore no scientific result command exists.

## Resolved transaction freeze

At the first application-valid tick `t*`, after arrivals and immediately before CAS, every branch
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
Replay receives only causal-prefix information and must complete before the same `t*` application
boundary.

## Estimands and claim ceiling

From one immutable pre-CAS checkpoint and one remaining physical tape:

```text
Delta_transfer = benefit(TRANSFER_COPY, RETAIN)
Delta_shadow   = benefit(TRANSFER_SHADOW, TRANSFER_COPY)
Delta_total    = benefit(TRANSFER_SHADOW, RETAIN)  # safeguard/report only
```

`Delta_transfer` identifies generic owner/actuator transfer conditional on a STRUCTURED-selected
valid event. `Delta_shadow` identifies only incremental promoted-state-source value. A competent
same-information `TRANSFER_REPLAY` arm replays the ordered causal actor/snapshot/message prefix
through the same checkpoint with no critic truth, opaque SOURCE, evaluator state, future tape,
extra training, or extra wire bytes. Exact reconstruction by the deadline absorbs the shadow object.

The maximum claim is fixed-host, finite-budget, trigger-conditional evidence for generic atomic
transfer and/or pre-warmed state-source value. It does not cover arbitrary checkpoints, `k`, speed,
`N`, natural prevalence, unique mediation, training advantage, shadow cost-effectiveness, full R06,
safety, deployment, or flight.

## Population, clocks, RNG, and work

Use a fresh namespace; no R05/R06 result identity or checkpoint transfers. Train only 24 STRUCTURED
jobs under the inherited 1,024-update × 4,096-transition law. Evaluate only the 6,912 claim cells:
24 blocks × 2 packages × 3 claim schedules × 3 speeds × 16 slots. Preserve no-trigger rows; no seed
replacement or selected checkpoint.

`dt=0.1s`; external `k` changes only at renewal. Intent originates at renewal `n`, application is
`n+1`, and every fork runs exactly 100 primitive ticks. Forks receive zero optimizer updates.
Checkpoint, normalization, causal prefix, pre-fork exogenous addresses, and future physical tape are
identical. Physical entity identity and `N=2` stay fixed; only owner/standby role changes.

Require inherited competence/opportunity/headroom, trigger support, COPY-versus-RETAIN first-action
separation `>=1e-3`, and SHADOW-versus-COPY state and first-action separation `>=1e-3`. Failure is
nonidentification.

## State ownership and atomicity

Native state owns physics, filters, SOURCE/base buffers, owner token, actuator authority, epoch,
payload sequence, protocol locks, held action, costs, hard events, and tape coordinates. PyTorch owns
checkpoint, four recurrent copies, and Welford state.

One native call validates and clones while leaving the parent immutable:

```cpp
clone_promotion_source_batch(
    const HostState* parent,
    const StepInput* current,
    size_t count,
    PromotionSourceForkOutput* out);
```

The linearization tuple binds owner, epoch, next payload sequence, `k` epoch, intent origin,
snapshot/readiness versions, lineage, and controller-hidden bytes. Python never writes native
ownership fields. Branch-specific observations are materialized before the first policy forward.
Create-only generations atomically bind native snapshot, rollout/Welford state, checkpoint, RNG
frontier, and receipts; sealed coordinates cannot be reforked.

## Endpoints and branches

Primary 100-tick endpoints are mean service, fractional worst-10% tail service, service deficit, and
recovery delay. Retain material margins `(0.03, 0.05, 0.25s, 0.5s)` and noninferiority margins
`(0.01, 0.02, 0.25s, 0.5s)`. Nonharm requires energy-ratio upper bound `<=0.03`, zero invalid commit,
token gap, dual owner/payload, buffer clear, slew/separation breach, minimum separation `>=15m`, and
byte-identical transaction shell with no extra application tick.

First-match branches: invalid protocol/measurement; missing competence/opportunity/support;
nonanswerable/imprecise; nonharm failure; `SHADOW_ABSORBED`; `SHADOW_SPECIFIC_VALUE`;
`GENERIC_TRANSFER_ONLY`; target-specific no-material; unresolved. No outcome-peeking stop, seed
replacement, budget extension, or threshold change.

## Implementation surface

Reuse existing production population, backend/native state, recurrent trainer, evaluator,
REAL/SHAM suffix pattern, data plane, reducer, and lifecycle as read-only semantics. Add:

```text
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/
  production_source_factored_contract.py
  production_source_factored_fork.py
  production_source_factored_reducer.py
  production_source_factored_data_plane.py
```

Add the new native output/API and explicit RETAIN/COPY/SHADOW policy-state modes without changing
existing REAL/SHAM exports. Telemetry records checkpoint identity, owner/actuator/epoch/CAS/application
reason, protocol-byte delta, transaction latency, minimum separation, and every nonharm event.

Focused tests cover native three-way clone allowlists, combined predicate/linearization,
exactly-once forking, `alpha=0/1` equivalence, transaction shell identity, future-address and
checkpoint equality, RETAIN suppression, replay information fence/deadline/work, complete 6,912-row
accounting, endpoint signs/margins/branches, crash-resume identity, duplicate refusal, complete-result
firewall, and CPU/RSS/I/O observation. These are conformance checks only.

## Future direct runner shape

```text
python -m tools.experiments.run_dish_rbhr_source_factored_fork \
  --repository-root C:\Projects\HMASD \
  --request <prospectively-frozen-request.json> \
  --run-root C:\Projects\HMASD\temp\directions\degraded_incumbent_shadow_handover\exp\<run-id>\artifacts
```

This is only a future shape; it carries no lease, identity token, authentication step, or current
execution path. The future result must use direct experiment inputs and complete terminal output.
Planning estimate is 35 CPUh
and 8 wall h; preflight ceiling 40 CPUh/10 wall h, at most eight workers/cores, one Torch thread,
GPU0, with conservative bounds 6.61 GiB RSS, 1.66 GiB scratch, 0.83 GiB durable output, and 68.14
GiB I/O.

## Evidence

- `DIRECTION.md`
- `DISH_RBHR_R06_SCIENCE_COMPOSITE_20260822.md`
- `DISH_RBHR_R06_ENGINEERING_CONFORMANCE_CM_TECHNICAL_PACKET_20260822.md`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_real_sham.py`
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py`
