# Problem Cache

Parked problems and open questions. Nothing here blocks the current round unless
it says so. The purpose is that a real issue noticed at a bad moment is recorded
rather than lost or allowed to derail the work in front of us.

Each entry states what it blocks, what evidence exists, and what would resolve
it. Move an entry out when it is resolved, and record where it went.

## Blocks interpreting this experiment's result

### P1. The fork engine is deterministic-only, but Replacement C is defined on held-out stochastic

`fork_single_opportunity` runs `deterministic=True` because a stochastic
collection's realized event, mark and primitive variates are not recoverable
from the record, so a stochastically collected episode cannot be reproduced by
its own natural branch.

The registered measurement uses held-out **stochastic** trajectories. This is not
cosmetic: under stochastic sampling a primitive action is selected by comparing a
uniform against the categorical CDF, so a small logit change can move the sampled
action without disturbing the top-1 ordering. Under `deterministic=True` the
action is an argmax, and the commitment bias cannot move it at all — which is why
`A_KEEP` measured exactly zero on all ten initialized natural-KEEP coordinates.
That zero was an artifact of the apparatus, not a property of the benchmark.

**Consequence:** `A_KEEP` and `A_RENEW` measured on the deterministic cell would
characterize the argmax policy rather than the behaviour policy `G` is computed
from. Training can proceed; the C gates cannot be honestly evaluated until this
is closed.

**What would resolve it:** retain the realized per-step variates during held-out
stochastic evaluation and script all four fork streams from them, the same
retention pattern already used for `candidate_u` and for the `opportunity`
stream. An internal review assessed this as retention-limited rather than
structurally limited, and named the obstacles: retain realized values rather than
generator states, fix the float32 dtype facade first, and expect width drift to
matter more because a uniform landing within ~1e-7 of a CDF boundary adds a
second flip channel.

### P1b. The fork engine cannot run on CPU

Measured directly: over the first six eligible held-out coordinates,
`fork_single_opportunity` succeeds 6 of 6 on CUDA and fails 6 of 6 on CPU, each
with `continuous = 4.768e-07` on `event_old_joint_logp` — not bitwise exact.

Cause: the fork reconstructs the forked step with the focal request removed from
the packed event batch, so the branch packs one fewer row than the collection
did. On CPU the surviving, unrelated rows then move, and the perturbation
cascades through `z`. A synthetic `nn.Linear` sweep does not reproduce this
cleanly — measured worst batch-size dependence was 3.4e-07 on CPU against
4.8e-07 on CUDA — so the effect is specific to the shapes and values in the real
path, and only the real fork is decisive.

This is the same shape-identity requirement the plan already states for width-1
versus width-16 prefixes; the fork engine additionally depends on the packed
request batch having identical size, which CUDA satisfies and CPU does not.

**Consequence:** CPU cannot produce `A_KEEP`/`A_RENEW`, and a CPU checkpoint
cannot be loaded under CUDA by design, so a CPU run cannot be evaluated on CUDA
either. The registered backend is therefore CUDA, and the measured 3.26x CPU
speed advantage on training is unusable for this experiment.

**What would resolve it:** make the branch pack the same number of requests as
the collection at the forked step, for example by retaining a masked placeholder
row instead of dropping the focal request. That requires changing
`collect_trajectory`, which is frozen, so it needs its own authorized boundary.

## Open scientific questions

### P2. Should the likelihood be accumulated in float64?

The joint log-likelihood is a categorical term plus eight transformed-mark
components, accumulated in float32 at a magnitude of 8 to 10 nats, where one ULP
is about 1e-6. Every replay bound therefore sits at the edge of the arithmetic by
construction. Measured `event_joint` on CUDA is 9.5367e-07, exactly one ULP and
95% of the retired 1e-6 wall; the first event row whose joint magnitude reaches
16 would make one ULP 1.9e-06 and break that wall deterministically.

Accumulating in float64 would drop one ULP to roughly 1e-15 and would likely
remove: the compositional joint bound and its `gamma_n` machinery, the width
coupling that forces fork reconstruction to match the collected batch shape, and
much of the device sensitivity between CPU and CUDA. The model has 14,980
parameters and the tensors are tiny, so the cost is close to zero — and nil on
CPU, which measured faster anyway.

Three of the last five repairs would likely not have existed.

**Blocked on:** this is protected probability semantics and would invalidate the
contract again, so it belongs to a later boundary, not this round. Ask the
external reviewer whether float64 accumulation changes any scientific meaning
before adopting it.

### P3. Three of four evaluation cells feed no gate

`aggregate_analysis` consumes only `held_out_stochastic`. The IID deterministic,
IID stochastic and held-out deterministic cells are computed, serialized, and
read by nothing. They are legitimate reported diagnostics, but they are 75% of
evaluation compute. Whether they can be reduced or dropped is a scientific
decision.

### P4. The natural-KEEP stratum is thin

At initialization only 10 of 645 held-out non-CREATE opportunities are natural
`KEEP`, roughly 160 per 256-episode replicate against a registered quota of 32
per replicate. That is about five times the quota, so it holds today, but it is
the narrowest margin in the design and it is a property of the trained policy,
which cannot be measured before training. If a trained replicate supplies fewer
than 32, the registered outcome is `BENCHMARK_NON_IDENTIFIABLE` rather than a
lowered quota.

## Deferred engineering

### P5. No per-cell training mode, so no concurrency

`formal_train` loops `for replicate in range(5)` internally and runs all 15
`(arm, replicate)` cells in one process. Concurrency requires a per-cell entry
point plus proof that per-cell execution produces bit-identical checkpoints to
the monolithic loop. Measured value: CPU scales to 5.94x across 15 workers where
one CUDA card saturates at 2.0x.

### P6. The fork prefix is re-derived per fork

Each fork reconstructs the episode prefix from step 0, about 40 times per
episode. Reconstructing once per source batch and snapshotting at each fork step
would amortize it; the environment snapshot contract already exists and costs 288
microseconds. At the registered 320-pair quota the current cost is about 9
minutes, so this is not urgent.

### P7. CUDA graph capture of the recurrent replay was never attempted

`torch.compile` measured 1.00x because the 80x6 loop lives in Python and each
iteration still emits its own launches. Whole-walk CUDA graph capture is the
mechanism that would work, and the shapes are static — exactly one input-shape
signature across all 80 steps. It needs the replay restructured to preallocated
outputs. Superseded in priority by the CPU path, which is simpler and measured
3.26x end to end.

### P8. `formal_train` and `formal_evaluate` have no test coverage

Neither is imported by the test module. Their evidence-writing paths were
rewritten by the replay tolerance change and are verified only by inspection plus
by their helpers being tested directly. Two latent defects have already been
found in this class of unreachable code: a `torch.flatnonzero` call that does not
exist in this torch build, and a slice omitting `env_index`.

### P9. Training manifest evidence is write-only

`validate_operational_records` checks only the update count and the boolean
families, so the per-update replay records written into the training manifest are
never re-validated on read-back. `TRAIN_MANIFEST_SCHEMA` was also left at 1 while
`EVALUATION_CELL_SCHEMA` went to 2 for the analogous change.
