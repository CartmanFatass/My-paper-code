# Research Background For The Implementation Review

This is context so the audit is well-posed. It is not an invitation to reopen
the route.

## What the benchmark is for

The project target is one shared MARL algorithm with runtime-variable team
membership and variable individual skill lifetime. The prior
`NONCALENDAR_HETEROGENEOUS_TRACKING_G0` benchmark qualified only as
`NO_ACCESS_BENCHMARK_ORDINARY_CONTROL`: it established structural reachability
and the cost of a shared four-step renewal restriction, but established no
hierarchy, no learned skills and no learned heterogeneous lifetime.

`EVENT_HELD_COMMITMENT_LINK_G0` isolates exactly one question: **does an
event-held commitment reaching primitive action logits buy anything over an
information-matched control that carries the identical commitment machinery but
cannot act on it?**

## The three arms

- `OR` — ordinary recurrent direct learner, the full-algorithm comparator and
  the standing access null. 14,980 parameters, no additions.
- `DUM` — `OR` plus the complete commitment apparatus (`W_z`, `event_head`,
  `mark_head`), with the treatment gate closed (`m=0`).
- `EHC` — identical to `DUM` with the gate open (`m=1`).

The sole treatment is:

```text
primitive_logits = base_logits + W_z(m * stopgrad(z))
```

`DUM` exists to separate *representation* from *use*. It pays the same
parameter cost, runs the same event learning, and takes the same number of
optimizer steps as `EHC`; only the commitment-to-action link differs. If `EHC`
beats `DUM`, the gain is attributable to acting on commitment rather than to
capacity, to event-head learning, or to optimizer exposure.

The primary estimand `G` is held-out stochastic `U_EHC - U_DUM`. The secondary
`V` is `U_EHC - U_OR`. The analyzer returns exactly one of eight mutually
exclusive branches by first-match precedence and never performs a post-result
rescue.

## Standing constraints relevant to the audit

- Intrinsic reward stays environment-agnostic: no task field, identity, role,
  success predicate, progress measure or external reward may enter it.
- The critic never reads `z`.
- Event and mark heads share no parameter and no gradient with the base trunk.
- Lifecycle keys never enter a model input.
- A valid failure is not rescued by changing budget, seed, threshold, reward,
  model, task, skill count or carrier under the same claim.
- Active-line development: no compatibility adapters, no legacy branches.

## Current status

Implementation is complete and committed. All eight focused acceptance items in
`docs/project/IMPLEMENTATION_PLAN.md` were reproduced on CUDA before commit; the
measured numbers are in `QUESTION.md`. **No formal training or registered
evaluation has been launched.** This review is the last gate before that
authorization is considered.
