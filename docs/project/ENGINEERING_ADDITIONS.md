# Engineering Principles — Measured Additions

Conditional guidance derived from the 2026-07-21 workload and host measurements.
Current execution policy is `docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md`.
Preserve the actual object's complete scientific and numerical contract; these
historical observations do not select a device, topology or new benchmark.

Numbers and conditions are in `docs/project/EFFICIENCY_PRACTICES.md`.

## Device selection

**Choose a device from the current complete path's launch, compute and transfer costs.**
Model size and batch affect that choice; a conformant path does not require a
fresh CPU/GPU comparison. Historical small-model CPU forward advantage does not
establish CPU whole-training advantage or an advantage on the current Linux node.

Current benchmark: 14,980 parameters, batch 16, ~480 sequential calls per epoch.
CPU single-thread forward was 2.7-2.9x faster than CUDA under those conditions.
Other widths, models and complete training paths were not established by that result.

**Set one thread per worker when tensors are small.** `torch.set_num_threads(1)`
beat 14 threads by 1.5x here — thread synchronization costs more than it saves
on a 32-wide GRU cell at batch 16.

## Parallelism

**Prefer in-process batching where independence and the scientific contract permit it.**
Preserve RNG, common-random-number coupling and state ownership. Process topology
depends on the actual environment API and assigned resources; a library's topology
does not itself authorize a new worker framework.

**Scope a measured limit to its host and workload.** The old WDDM multi-process
GPU measurement saturated near2.0x. It is not a limit for all hosts or proof that
one or many processes is always preferable. Apply the current runtime scope rules.

**Batch branches and replicas when they are independent.** Counterfactual forks
and repeated evidence runs are candidates for batching when their full semantics
allow it; preserve causal, autoregressive, simulator and recurrent dependence.

## Wasted compute

**Trace each output's scientific use, including analysis and reported diagnostics.**
Three of four historical evaluation cells fed no gate; the intervention metric was
computed for all four and read from one. Required diagnostics still remain required.

**Look for a validation pass that duplicates a training pass.**
`validate_replay` is a fifth full forward on top of four PPO epochs — about 20%
of the update — because it recomputes what an epoch already computes. Remove only
true duplication consistent with the original requirements and independent checking;
the observation alone does not authorize removal of validation.

**Honor the original reconstruction contract.** float32 reduction order
depends on tensor shape, so a width-1 reconstruction of a width-16 collection
does not reproduce it bitwise. Matching the width removes an entire class of
drift rather than bounding it.

## Numerics

**Bound each factor, not the derived sum.** A quantity that accumulates several
component errors will be the marginal one under a single scalar bound.
`event_joint` sums eight mark components plus a categorical term and is the only
quantity that ever approaches the tolerance.

**Bind a measured tolerance to its original object, device and batch width.**
State those conditions with the constant. Ours was calibrated on CUDA at width
16 and rejects both CPU execution and width-1 reconstruction in that object.
This is not a project-wide CPU or batch-change ban; new execution semantics are
validated against their own accepted exactness/tolerance contract.

## Historical negative measurements and untested candidates

**The measured recurrent replay obtained1.00x from `torch.compile`.**
No acceleration was observed in that configuration. The80x6 Python-level loop
was the suspected boundary; whole-walk CUDA graph capture with preallocated
outputs remains an unimplemented candidate, not a proven remedy.

**The measured immutable-state clone cost was small for that fork budget:**
288 microseconds per environment clone,1.2 seconds across its full budget.
