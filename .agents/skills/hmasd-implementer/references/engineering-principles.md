# HMASD Engineering Principles

## Batch and device

- Keep environment, agent, active-member, branch, skill, replica and evaluation
  dimensions explicit. Batch independent work through an existing tensor path;
  retain loops only for real causal, autoregressive, simulator or recurrent
  dependence.
- Pack padded or indexed data once per collection boundary, transfer it once and
  reuse it across optimizer passes.
- Accumulate metrics on device and synchronize only at update, reporting or
  immediate corruption-control boundaries.
- Reuse batched inference for evaluation, controls, forced branches, replicas
  and audits when the estimand and RNG contract permit it.

## Semantic integrity

- Preserve ownership and ordering of hidden state, active/reset/valid masks,
  segment boundaries and initial chunk states.
- Sampling, storage, replay and update use the same support, masks, prefixes,
  probability factorization, recurrent inputs and detach boundaries.
- Preserve intended RNG independence, common-random-number coupling and exact
  checkpoint continuation.
- Serialize complete runtime state only at named recovery or evidence
  boundaries.

## Runtime structure

- Reuse a known-good process/device topology; avoid duplicate CUDA contexts and
  serialization without real concurrency.
- Conclusion-bearing runners expose stage-level wall time sufficient to locate
  order-of-magnitude regressions.
- Before return, inspect the changed end-to-end path once for scalar CUDA work,
  repeated packing/transfer, premature synchronization, recurrent leakage,
  replay mismatch, RNG drift, excessive persistence and serial evaluation.

Fix an observed issue once. Do not create a separate performance gate or loop
on speculative optimization.
