# Engineering Principles — Measured Additions

Practical rules derived from measurements on this project. These extend, and do
not replace, the active-line engineering constraints (batch independent
dimensions, pack once, no scalar CUDA sync, no serial evaluation).

Numbers and conditions are in `docs/project/EFFICIENCY_PRACTICES.md`.

## Device selection

**Pick the device by the ratio of kernel launch overhead to work per launch.**
Few parameters, small batch and many sequential steps means the launch dominates
the arithmetic, and CPU wins. Large batch, large model or long fused kernels
means GPU wins. Measure both before committing; do not inherit a default.

Current benchmark: 14,980 parameters, batch 16, ~480 sequential calls per epoch.
CPU single-thread is 2.7-2.9x faster than CUDA. Expect this to reverse once
agent count or batch width grows.

**Set one thread per worker when tensors are small.** `torch.set_num_threads(1)`
beat 14 threads by 1.5x here — thread synchronization costs more than it saves
on a 32-wide GRU cell at batch 16.

## Parallelism

**Batch independent runs as a replica dimension inside one known-good process
and device topology.** Reuse the verified tensor path, preserve RNG and
common-random-number coupling, and avoid duplicate CUDA contexts. One process
per replica is not a scaling strategy for this project.

**Know the ceiling before changing topology.** One CUDA card saturated near
2.0x across concurrent processes because kernels from separate WDDM contexts
serialize. Separate processes are allowed only for work that cannot share the
registered tensor/device path and has an explicit resource assignment.

**Batch branches and replicas when they are independent.** Counterfactual forks
and repeated evidence runs are batched by default; keep a loop only for genuine
causal, autoregressive, simulator or recurrent dependence.

## Wasted compute

**Every produced artifact must have a reader.** Trace each output to the code
that consumes it. Three of four evaluation cells feed no gate; the intervention
metric was computed for all four cells and read from one.

**Look for a validation pass that duplicates a training pass.**
`validate_replay` is a fifth full forward on top of four PPO epochs — about 20%
of the update — because it recomputes what an epoch already computes.

**Reconstruct at the same batch width as the original.** float32 reduction order
depends on tensor shape, so a width-1 reconstruction of a width-16 collection
does not reproduce it bitwise. Matching the width removes an entire class of
drift rather than bounding it.

## Numerics

**Bound each factor, not the derived sum.** A quantity that accumulates several
component errors will be the marginal one under a single scalar bound.
`event_joint` sums eight mark components plus a categorical term and is the only
quantity that ever approaches the tolerance.

**A tolerance is valid only for the device and batch width it was measured on.**
State those conditions with the constant. Ours was calibrated on CUDA at width
16 and rejects both CPU execution and width-1 reconstruction.

## Refuted here — do not retry

**`torch.compile` does not remove launch overhead from a Python-level loop.**
Measured 1.00x on the recurrent replay. Inductor fuses operators inside one
call; the 80x6 loop lives in Python, so every iteration still emits its own
launches. Whole-walk CUDA graph capture is the mechanism that would work, and
shapes are static enough to allow it, but it needs the replay restructured to
preallocated outputs.

**Deep-copying immutable state per fork is not a bottleneck.** 288 microseconds
per environment clone, 1.2 seconds across the entire fork budget.
