# ONLGR implementation threshold

Status: `NO_STANDALONE_CODE`

## Decision

ONLGR transfers definitions only into a future SCDMP receiver: capped physical-rate control,
service/cost accounting, and an outside-class age ceiling. It transfers no result polarity,
lifecycle state, threshold, endpoint, or mechanism label. No new ONLGR runner, learner, native
backend, checkpoint, or result command is warranted.

## Transferable clock control

At a real eligible boundary with treatment-common primitive-tick spacing `Delta_i`, define

\[
q_i(h)=\min(1,\Delta_i h),\qquad A_i\sim\operatorname{Bernoulli}(q_i(h)).
\]

`h` is executed events per primitive physical tick. Only real eligible boundaries sample and
execute; dummy ticks produce no event, reset, charge, or evidence. The control is state-blind and
order-erased. It may read only current spacing and the opportunity flag, never H/R order, latent
graph, task content, age, future tapes, outcomes, or post-result tuning.

Use ratio-of-expectations accounting:

\[
J=\frac{E[S-cN]}{E[T]}
 =\frac{E[S]}{E[T]}-c\frac{E[N]}{E[T]}.
\]

SCDMP retains its own native full-mission endpoint and native cost. ONLGR's `c=2`, lifetime,
ordering, weighting, grid, and `1/32` margin do not transfer. If the SCDMP object has no native event
cost, event rate is diagnostic only.

Where native service age exists, an outside-class competence ceiling may use

\[
\tau_\Delta=\Delta\lceil L/\Delta\rceil,
\qquad J_{age}=\frac{L-c}{\tau_\Delta},
\]

under explicitly frozen nonstacking service and service-before-boundary-action ordering. It may
observe only age or `expired = age >= L`; it is not a same-information null.

## Intended SCDMP-owned surface

Only after SCDMP defines a typed receiver seam may implementation add:

```text
experiments/candidates/scdmp_variable_k/
  foundation_conditioned_event_order_value/clock_controls.py
tests/experiments/candidates/scdmp_variable_k/
  test_foundation_conditioned_event_order_value_clock_controls.py
```

Proposed pure API:

- immutable `ClockControlSpec`;
- immutable `ServiceCostBreakdown`;
- `rate_probability(spec, spacing)`;
- `service_cost_breakdown(service, event_count, primitive_ticks, event_cost)`;
- `age_conditioned_ceiling(spec, spacing)`.

This module imports no native backend, runner, RNG, model, optimizer, checkpoint, registry, or
result publisher. Focused tests cover cap/unsaturated algebra, ratio-of-expectations, dummy-boundary
inertness, forbidden-input rejection, and age-ceiling ordering.

## Unique blocker

Current SCDMP hosts do not expose a typed seam separating boundary-event probability, service age,
event charge, and service value from graph `q`, exogenous `k`, physical action, and mission reward.
Repurposing those existing fields would change scientific meaning. SCDMP must define the receiver
contract before this control can be implemented.

## Forbidden transfer

Do not transfer or imply `RATE > EXP > RAW`, `GENERIC_RATE_SUPPORTED`, `1/32`, any ONLGR numeric
margin, exponential/hazard/lease/REBIND value, learned duration, termination hazard, variable
lifetime, arbitrary-`k` capability, SCDMP foundation competence, graph opportunity, safety, UAV
value, work parity, or lifecycle polarity.

## Closure boundary

Standalone ONLGR can close after its existing review objection is dispositioned and this control
contract is cited by SCDMP. Closure requires no CM implementation, result run, third-spacing assay,
or new provider operation.

## Evidence

- `DIRECTION.md`
- `evidence/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-em-synthesis.md`
- `external/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-pro-convergence-response.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md`
