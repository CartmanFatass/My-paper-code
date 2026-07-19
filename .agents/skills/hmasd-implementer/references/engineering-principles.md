# HMASD Implementer Engineering Principles

Apply these rules to executable MARL code. They optimize implementation quality
without changing the controller's scientific or algorithm contract.

## Batch and device

- Keep environment, agent, active-member, branch, skill, replica, and
  evaluation dimensions explicit. Batch independent work through an existing
  tensor path; retain a loop only for real autoregressive, causal, simulator, or
  recurrent dependence.
- Pack padded or indexed data once per collection boundary, transfer it once,
  and reuse it across optimizer passes.
- Accumulate metrics on device and synchronize at update or reporting
  boundaries. A scalar sync is justified only when it immediately controls
  execution or detects corruption.
- Reuse batched inference for evaluation, controls, forced branches, replicas,
  and semantic audits. Share immutable work between matched arms only when the
  estimand and RNG contract permit it.

## Semantic integrity

- Preserve the declared owner and ordering of actor and critic hidden state,
  active masks, reset masks, valid rows, segment boundaries, and initial chunk
  states. Never infer validity from padding or fixed identity.
- Sampling, storage, replay, and update use the same action support, masks,
  autoregressive prefix, distribution factorization, recurrent inputs, and
  declared detach boundaries.
- Preserve intentional RNG independence and coupling. Batching must not change
  common-random-number pairings, branch independence, training/evaluation RNG
  separation, or checkpoint continuation.
- Serialize complete runtime state only at recovery or evidence boundaries
  named by the task. Do not checkpoint every update without a registered need.

## Runtime structure

- Reuse a known-good process/device topology. Multiple CUDA processes must
  provide useful concurrency rather than duplicate contexts and serialization.
- Conclusion-bearing runners expose enough stage-level wall time to locate an
  order-of-magnitude regression without repeated profiling.
- Before handing back executable experiment code, inspect the changed end-to-
  end path once for scalar CUDA work, repeated packing or transfer, premature
  synchronization, recurrent leakage, replay mismatch, RNG drift, excessive
  persistence, and serial evaluation.

Fix an observed issue once. Do not create a separate performance gate, require
a fixed speedup, or loop on speculative optimization. If a recurring problem
reveals a reusable rule, update this reference at the same accepted code
boundary rather than adding workflow prose elsewhere.
