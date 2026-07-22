# HMASD Project Manager Engineering Principles

Require each implementation package to preserve the selected scientific
direction while making all algorithm-realization decisions computationally
coherent.

- Batch independent environment, member, branch, skill, replica and evaluation
  dimensions. Retain loops only for genuine causal, autoregressive, simulator
  or recurrent dependence.
- Pack and transfer rollout data once per collection boundary; reuse it across
  optimizer passes and synchronize metrics only at real control boundaries.
- Keep sampling, storage, replay and update identical in support, masks,
  prefixes, probability factorization, recurrent inputs and detach rules.
- Preserve RNG independence and coupling, survivor continuity, lifecycle state,
  exact checkpoint continuation and declared optimizer exposure.
- Inspect the end-to-end changed path once for scalar CUDA work, repeated
  packing/transfer, premature synchronization, recurrent leakage, replay
  mismatch, RNG drift, excessive persistence and serial evaluation.
- Prefer replacement over compatibility. Delete obsolete active paths in the
  same package; Git history is the archive.
- Run one focused check for the registered corruption risk. Do not create a
  separate performance gate or repeated internal review ceremony.
