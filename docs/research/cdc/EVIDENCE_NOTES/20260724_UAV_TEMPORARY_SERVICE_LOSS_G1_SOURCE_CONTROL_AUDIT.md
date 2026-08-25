# UAV temporary-service-loss G1 source-control audit

Date: 2026-07-24

```text
action=UAV_TEMPORARY_SERVICE_LOSS_G1_ZERO_COMPUTE_SOURCE_AUDIT
compute=none
iteration_cost=0
iterations_remaining=6
next_boundary=UAV_TEMPORARY_SERVICE_LOSS_G1_FORMAL_SOURCE_CLOSURE_ITERATION_22
```

## Decision

Run the already frozen G1 formal path from a fresh integrated source. The path
must execute the exact constructive and no-reallocation source controls before
creating a learned model. A valid source-identification failure returns the
registered second branch with zero learned updates. Only if the frozen source
predicates pass may the existing matched learned budget proceed.

Do not build a G31-to-UAV adapter first. G31 is already usable on its paired toy
sources, but an adapter cannot make an unidentifiable UAV source identifiable.
Closing the source predicate is therefore the smallest separating action.

## Read-only findings

- The control ledger, pre-action loss transition, QoS extraction, paired
  exogenous randomness and first-match source pruning are internally
  consistent. No operational control-source defect was found.
- The representative episode has constructive `J_event=0.943997` and
  no-reallocation `J_event=0.967834`. Even a perfect constructive controller
  could improve on that no-reallocation value by only `0.032166`, below the
  frozen `0.10` source margin. This is strong risk evidence, not a substitute
  for the registered multi-seed source screen.
- The two learned routing labels previously selected the same inherited
  anonymous-content order. That made `FIXED_MASK_REC` metadata-only. The
  accepted execution repair gives FIXED an active-first physical-slot order
  and leaves OPEN on the anonymous-content order. Parameters, critic values,
  active likelihood masks, observations, reward, source, seeds, budget and
  result gates remain unchanged.
- The complete focused proof set passes on CPU with one thread: `41 passed` for
  the UAV G1 core and runner tests. It covers matched parameter identity,
  distinct routing, permutation/current-information invariants, source
  controls, lifecycle replay, checkpoint binding and fail-closed manifests.

## Reuse and performance disposition

The final Scout pass found no additional high-value shared computation that is
safe to merge now. Strict UAV frontend MCS/FDMA SINR is not interchangeable
with the relaxed graph-capacity approximation; merging them would change the
communication model. Cross-run metric/bootstrap/serialization caches have low
measured value and would enlarge RNG, resume and invalidation surfaces.

The retained reusable optimizations remain the directional A2A/A2G/G2A
path-loss snapshot (`7.554426%` incremental median improvement, exact
transition/RNG match) and the shared first gradient-bearing PPO replay
(`20.307434%` median improvement, exact metrics and parameters). The routing
repair above is correctness work, not claimed as a speedup.

## Iteration accounting

This audit and repair consume zero conclusion-bearing iterations. A complete,
operationally valid formal analysis consumes iteration 22 regardless of which
registered scientific branch wins. An operator error or incomplete artifact
set consumes none.
