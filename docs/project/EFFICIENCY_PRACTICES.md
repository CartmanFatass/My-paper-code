# Efficiency Practices

Living document. Records what we have measured about implementation and
experiment throughput, the practices derived from those measurements, and the
approaches we have already refuted so nobody retries them.

Two things are kept apart deliberately:

- **Measurements** are facts under stated conditions. They expire when the
  hardware, the model shape or the batch width changes.
- **Practices** are rules. They should survive a change of hardware, which is
  why most of them are about how to decide rather than what to choose.

Update this file when a measurement is taken or a practice is corrected. Record
the conditions with every number; a number without its conditions becomes a
false generalization within weeks.

## Practices

### P1. Measure before you state a number

Never report a cost, a speedup or a scaling factor that was not measured. If a
decision depends on a number, the measurement is part of the decision, not an
optional follow-up.

This exists because four estimates in one session were wrong, each by enough to
change a decision:

| Claim | Reality | Cost of the error |
|---|---|---|
| Fork batching lands around 18 minutes | ~3 h per replicate at full scale | An expensive requirement was adopted partly on this number |
| The 15 cells concurrent gives near-linear speedup | 2.0x, saturating at 4 processes | Would have specified the wrong parallelism strategy |
| `A_KEEP` may be zero by construction | An artifact of forking deterministically | Nearly retired the only bidirectional consequence gate |
| CUDA is the right device | CPU is 2.7-2.9x faster on this shape | Never questioned until measured |

Each measurement cost minutes. Each error would have cost hours or a wrong
scientific decision.

### P2. Device choice is a measurement, not a default

Do not assume CUDA. Decide by the ratio of kernel launch overhead to work per
launch, and measure it.

A workload is GPU-hostile when it has few parameters, a small batch, and many
sequential steps — the launch overhead then dominates the arithmetic. It becomes
GPU-favourable as model size, batch width or agent count grows.

Because the project's target capability is large variable-membership teams, the
correct device is expected to change as the work scales. Re-measure at each
significant change of shape rather than carrying a past answer forward.

### P3. Split correctness from performance, in that order

Decompose a task so that a correct slow implementation is a complete deliverable
before any performance work begins. Correctness gets its own review and its own
acceptance evidence.

A task scoped as "engine plus wiring" stalled for an hour and produced nothing,
because the hard part (exact state reconstruction) and the orthogonal part
(batched execution) were entangled. Re-scoped as "sequential single pair,
natural-branch reproduction only", it succeeded.

### P4. A test must be able to fail

Before recording a test as covering an invariant, state what wrong
implementation it would catch. If the answer is none, the test is worse than
absent, because it reads as covered in every later audit.

Verify the important ones by mutation: introduce the defect deliberately,
confirm the test goes red, revert, confirm the tree is byte-identical to a
pre-mutation backup.

A test asserting `requires_grad is False` inside a `torch.no_grad()` block
passed while proving nothing. In the other direction, a reviewer's claim that
the suite would miss a swapped `candidate_z` was refuted in five seconds by
mutation — the guard existed. Mutation testing settles both directions.

### P5. Numerical tolerances are device- and shape-coupled

A tolerance calibrated on one device at one batch width is not a property of the
algorithm. State the conditions under which a bound was established, and expect
any change of reduction order — a different device, a different batch width, a
different accumulation path — to move the error.

Prefer bounding each factor over bounding a derived sum. A quantity that
accumulates several component errors will always be the marginal one under a
single scalar bound.

### P6. Fix an observed issue once

From the standing engineering principles: do not create a separate performance
gate or a speculative optimization loop. Measure to decide, fix once, move on.

Applied in practice: a plausible optimization (sharing the frozen ledger between
forks instead of deep-copying) was measured at 288 microseconds per clone and
about 1.2 seconds across the whole fork budget, and dropped without being built.

## Measurements

Conditions unless stated otherwise: RTX 4070 8 GB (WDDM), 20 CPU cores,
`torch 2.7.0+cu118`, `EVENT_HELD_COMMITMENT_LINK_G0` at the registered width of
16 environments, horizon 80, 4 PPO epochs, model 14,980 base parameters,
`MAX_LIFECYCLES` 6. Taken 2026-07-21.

### Where the time goes

| Component | CUDA | Share |
|---|---|---|
| Per-arm update, end to end | ~8.1 s | 100% |
| `collect_trajectory` | 1.213 s | ~15% |
| `_replay_primitive`, one pass | 0.663-0.873 s | — |
| Replay x5 (4 epochs + `validate_replay`) | ~3.3 s | ~41% |
| Backward, optimizer, GAE, remainder | ~3.6 s | ~44% |

The replay walk is 80 sequential steps, each running the autoregressive loop
over up to 6 lifecycles at batch 16: roughly 480 sequential tiny kernel calls
per pass, about 2,400 per update per arm. `validate_replay` is a fifth full
replay on top of the four epochs.

Registered formal training, three arms and five replicates at 250 updates:
**7.5 h serial on CUDA**.

### Device

| Operation | CUDA | CPU 1 thread | CPU advantage |
|---|---|---|---|
| `collect_trajectory` | 1.213 s | 0.419 s | 2.90x |
| `_replay_primitive` | 0.663 s | 0.245 s | 2.70x |

CPU single-thread also beats CPU with 14 threads (0.419 s against 0.629 s):
the tensors are too small for thread synchronization to pay for itself.

**Not yet measured:** the backward pass and optimizer step on CPU, sustained
behaviour over 250 updates, RAM under many workers, and arms other than EHC.
The end-to-end CPU figure is therefore a projection from forward-pass
measurements, not an observation.

### Parallel scaling

Concurrent processes, each running the registered-size smoke:

| Workers | CUDA wall | CUDA scaling | CPU wall | CPU scaling |
|---|---|---|---|---|
| 1 | 43.6 s | 1.00x | 7.6 s | 1.00x |
| 2 | 55.0 s | 1.58x | — | — |
| 4 | 89.7 s | 1.94x | 9.1 s | 3.37x |
| 6 | 130.5 s | 2.00x | — | — |
| 8 | — | — | 11.7 s | 5.23x |
| 15 | — | — | 19.2 s | 5.94x |

CUDA saturates at about 2.0x by four processes. This is not a memory limit —
peak VRAM was 2,817 MiB of 8,188 with six workers. One card serializes kernel
execution across contexts under WDDM.

CPU reaches about 5.9x at 15 workers on 20 cores, limited by memory bandwidth
and cache contention rather than core count.

Combined projection, CPU with 15 single-thread workers against one CUDA
process: roughly 14x, putting registered formal training near 30 minutes rather
than 7.5 hours. **Projection, not measurement** — see the unmeasured items
above.

### Fork engine

One counterfactual fork pair, sequential, single environment: 1.06 s mean,
linear in `160 - fork_step`. The registered 32+32 quota is 320 pairs, about
5.65 minutes. Full per-opportunity forking would be roughly 10,300 pairs per
replicate, about 3 hours per replicate.

Environment clone via `snapshot_state` / `from_snapshot_state`: 288 microseconds.

## Refuted

Record here so no one spends time re-deriving these.

- **`torch.compile` on the recurrent replay: 1.00x.** No speedup at default
  settings; warmup of 1.9 s suggests it fell back to eager. Inductor fuses
  operators inside one `forward_step` call, but the 80x6 loop lives in Python,
  so each iteration still emits its own launches. Removing that overhead needs
  whole-walk CUDA graph capture, which would require restructuring the replay to
  preallocated outputs. Shapes are static — exactly one input-shape signature
  across all 80 steps — so capture is not ruled out, only unbuilt.
- **Process-level concurrency on one CUDA card: capped at 2.0x.** Adding
  workers past four adds wall time without adding throughput.
- **Sharing the frozen ledger between forks:** measured irrelevant, 1.2 s across
  the entire fork budget.
- **Batching the counterfactual forks:** not a scientific prerequisite. The
  registered subsample is 320 pairs at about 5.65 minutes, so a batched fork
  engine would save minutes.

## Blocked

- **CPU execution path.** `validate_replay` rejects it: `event_joint` reaches
  1.91e-6 on CPU against the registered `REPLAY_TOLERANCE` of 1e-6, where CUDA
  gives about 4.8e-7. The same quantity reaches 1.19e-6 under a width-1 versus
  width-16 reconstruction on CUDA, so the bound is marginal under any change of
  reduction order. Referred to external review at
  `docs/external-review/gpt5_6_pro/20260721_replay_tolerance_device_portability/`.
  `--device cpu` currently exists as a runner flag but `_require_cuda` rejects
  it, so the CPU path has never been exercised.
- **Fork prefix reconstruction at the factual batch width**, for the same
  reason.

## Frozen by contract

These are the experiment, not implementation detail. Changing them changes what
is being measured: 16 environments, horizon 80, 250 updates, 4 PPO epochs, 5
replicates, 320,000 transitions per arm, 1,000 base optimizer steps, and the
four evaluation cells at 256 episodes each.

One open question sits here rather than in engineering: the analyzer consumes
only `held_out_stochastic`, so three of the four evaluation cells feed no gate
and exist as reported diagnostics. Whether they can be reduced is a scientific
decision, not an optimization.

## Pointers

- `docs/project/AGENT_CONTEXT.md` — standing constraints for every subagent.
- `.agents/skills/hmasd-implementer/references/engineering-principles.md` —
  batching, packing, synchronization and the pre-return inspection.
- `.agents/skills/hmasd-reviewer/references/review-principles.md` — performance
  structure is reviewed as code quality.
