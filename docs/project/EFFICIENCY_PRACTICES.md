# Efficiency Practices

Historical measurements and unresolved paths for the named2026-07-21 host and
object. Preserve these numbers and their unmeasured boundaries; current policy is
`docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md`, with conditional guidance in
`docs/project/ENGINEERING_ADDITIONS.md`. Old WDDM limits and replay tolerances do
not become global constraints on other objects or current Linux execution.

Record the conditions with every measurement — hardware, model shape, batch
width. A number without its conditions becomes a false generalization within
weeks. Add to this file whenever a measurement is taken.

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
**7.5 h serial on CUDA (projection, not a completed formal-study measurement)**.

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

Reconstruction runs at the collected 16-environment width, which makes it
bitwise exact. Cost is linear in the reconstructed step count, which is the
prefix plus two tails:

```
per fork  =  0.184 s  +  12.86 ms x (160 - fork_step)
```

Measured 2.178 s at `t=4` down to 1.227 s at `t=76`. The mean eligible fork step
is 43.3 over 645 opportunities, giving about **1.68 s per fork** and **9.0
minutes for the registered 320-pair quota** — roughly 18 minutes if both DUM and
EHC are forked. Reconstructing at width 1 was faster per fork but not bitwise
exact, and the difference reached 1.19e-6 on `event_old_joint_logp`.

Environment clone via `snapshot_state` / `from_snapshot_state`: 288 microseconds.

### Batch width is nearly free on this workload

A full 80-step collection costs 1.126 s at width 16 against 0.597 s at width 1.
**Sixteen times the environments costs 1.89x the wall clock.**

This is the clearest single measurement of where the cost lives: the workload is
bound by the number of sequential physical steps, not by the width of each one.
Widening a batch is close to free; adding sequential steps is not. It also means
reconstructing at the factual width costs far less than the 16x its shape
suggests, which is why exactness was affordable.

## Refuted

These are historical configuration-specific findings, not universal performance
dispositions or authorization to retry the original object.

- **`torch.compile` on the recurrent replay: 1.00x.** No speedup at default
  settings; warmup of 1.9 s suggests it fell back to eager. Inductor fuses
  operators inside one `forward_step` call, but the 80x6 loop lives in Python,
  so each iteration still emits its own launches. Whole-walk CUDA graph capture
  is an untested candidate for that overhead and would require restructuring the replay to
  preallocated outputs. Shapes are static — exactly one input-shape signature
  across all 80 steps — so capture is not ruled out, only unbuilt.
- **Process-level concurrency on one CUDA card: capped at 2.0x.** Adding
  workers past four adds wall time without adding throughput.
- **Sharing the frozen ledger between forks:** measured irrelevant, 1.2 s across
  the entire fork budget.
- **Batching the counterfactual forks:** not a scientific prerequisite. The
  registered subsample is 320 pairs at about 5.65 minutes, so a batched fork
  engine would save minutes.

## Blocked in the historical object

These describe the original object and its then-current implementation. They do
not impose a general CPU, batch-width or current-host ban. Retain their exact
unmeasured scope and apply a new object's actual numerical contract.

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
- `docs/project/CURRENT_WORK.md` — batching, packing, synchronization and the
  pre-return inspection for the active line.
