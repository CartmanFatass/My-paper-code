# MARL Engineering Principles

This file is the durable engineering contract for HMASD training, runtime,
collector, replay, evaluation, intervention-audit, checkpoint, analyzer, and
experiment-runner code. It is implementation guidance, not a scientific gate or
an experiment history.

Implementers follow these rules. The active controller owns exceptions and
updates this document only when a repeated problem yields a general rule.

## E1. Batch-First Execution

- **Requirement:** Keep independent environment, agent, active-member, branch,
  skill, replica, and evaluation dimensions explicit and batch them through the
  established tensor path.
- **Allowed exception:** Genuine autoregressive dependence, causal event order,
  incompatible recurrent boundaries, or an API that cannot preserve semantics
  when batched.
- **Review question:** Does any Python loop launch equivalent scalar CUDA work
  that an existing or small batched entry point can perform?

## E2. Pack and Transfer Once

- **Requirement:** Construct padded or indexed rollout/intervention tensors once
  per collection boundary, transfer them to the target device once, and reuse
  them across PPO epochs or auxiliary optimizer passes.
- **Allowed exception:** Data produced by a later causal stage or data whose
  mutation is part of the registered algorithm.
- **Review question:** Are NumPy stacking, padding, indexing, or host-to-device
  copies repeated inside optimizer loops?

## E3. Device-Resident Accumulation

- **Requirement:** Accumulate losses, entropy, KL, clip fractions, gradient
  summaries, and counters on device and synchronize at a natural update or
  reporting boundary.
- **Allowed exception:** A scalar that immediately controls execution or detects
  a non-finite condition that cannot wait until the boundary.
- **Review question:** Are `.item()`, `.cpu()`, or `.numpy()` calls synchronizing
  every sample or minibatch?

## E4. Recurrent State and Mask Ownership

- **Requirement:** Preserve the declared owner and ordering of actor/critic
  hidden state, active-agent masks, reset masks, valid rows, segment boundaries,
  and initial chunk states. Batch construction must not infer these from padded
  values or fixed agent identity.
- **Allowed exception:** None without a controller-approved change to the active
  algorithm contract.
- **Review question:** Can batching, membership change, truncation, or episode
  reset leak state across environments, agents, segments, or policy versions?

## E5. Probability, Gradient, and Replay Equivalence

- **Requirement:** Sampling, storage, replay, and update must use the same
  executed action support, masks, autoregressive prefix, distribution
  factorization, and recurrent inputs. Preserve declared gradient and detach
  boundaries while optimizing the computational structure.
- **Allowed exception:** An explicitly registered algorithm change that replaces
  the probability or credit contract.
- **Review question:** Does the optimized path reproduce stored likelihoods and
  update only the intended parameters on valid rows?

## E6. RNG and Common-Random-Number Contracts

- **Requirement:** Preserve independence and coupling intentionally: independent
  branches keep independent streams; paired interventions retain their declared
  common random numbers; evaluation must not consume training RNG accidentally.
- **Allowed exception:** A declared stochastic-contract change in the active
  plan.
- **Review question:** Did batching change which samples share a stream, the
  order of draws inside a paired comparison, or checkpoint-resume continuation?

## E7. Batched Evaluation and Intervention

- **Requirement:** Reuse batched inference for evaluation, controls, forced
  branches, replicas, and semantic audits. Batch compatible branches from the
  same snapshot and, where state shapes permit, compatible source snapshots.
- **Allowed exception:** Branches whose causal order or simulator snapshot
  semantics cannot be represented independently in one batch.
- **Review question:** Are evaluation or audit paths recreating environments and
  running scalar actor forwards for independent branches?

## E8. Shared Immutable Work Across Matched Arms

- **Requirement:** Compute and share immutable preprocessing, source banks,
  initial evaluations, or intervention tables when parameters, inputs, expected
  outputs, and RNG contracts are identical across arms.
- **Allowed exception:** Independent execution is part of the estimand or is
  needed to prove arm isolation.
- **Review question:** Are matched arms repeating byte-equivalent work that does
  not depend on the treatment?

## E9. Checkpoint and Runtime Persistence

- **Requirement:** Serialize the full runtime only at recovery or evidence
  boundaries required by the active contract. Use sparse periodic recovery
  checkpoints and one final checkpoint unless the contract requires finer
  durability.
- **Allowed exception:** A short checkpoint-resume test or a run with an explicit
  recovery-frequency requirement.
- **Review question:** Is each update serializing models, optimizers, collectors,
  environments, RNG, and ledgers without a registered recovery need?

## E10. Stage-Level Wall-Time Observability

- **Requirement:** Conclusion-bearing runners expose cumulative wall time for
  the material stages needed to locate order-of-magnitude regressions, such as
  environment stepping, high events, low inference, packing/update, checkpoint,
  evaluation, audit, and analysis.
- **Allowed exception:** Tiny code tests where timing would not inform a runtime
  decision.
- **Review question:** Can the controller identify the dominant stage without
  repeatedly profiling or reading broad artifacts?

## E11. Process and Device Topology

- **Requirement:** Select subprocess, sharded, or multi-arm execution from the
  actual CPU/GPU workload and reuse a known-good topology. Multiple CUDA
  processes must justify their context and memory overhead through useful
  concurrency.
- **Allowed exception:** A frozen experiment topology whose scientific contract
  must not change mid-run.
- **Review question:** Is a single GPU being slowed by competing CUDA contexts,
  CPU-bound environment workers, serialization, or an undersized batch?

## E12. Final Experiment-Code Review

After implementation and one focused correctness check, the controller reviews
the actual end-to-end experiment path once for both semantic correctness and
engineering efficiency. Inspect batching, packing, device transfers,
synchronization, recurrent ownership, replay, RNG, serialization, evaluation,
analysis, and topology.

Fix actionable findings once before launch and re-review only the changed paths.
Do not create an independent performance gate, require a fixed speedup, or loop
on speculative optimization. If runtime later becomes grossly inconsistent
with the declared wall-clock range, the controller may stop the run and repair
the engineering path without changing the scientific contract.

## Maintaining These Principles

When a repeated issue appears, fix the concrete code first. If the lesson
generalizes across experiments, update an existing `E` rule or add one concise
rule at the same accepted code boundary. Do not record incident timelines,
experiment-specific loop counts, deprecated-path notices, or one-off tuning
advice here. Implementers may report a conflict but may not weaken or reinterpret
these principles independently.
