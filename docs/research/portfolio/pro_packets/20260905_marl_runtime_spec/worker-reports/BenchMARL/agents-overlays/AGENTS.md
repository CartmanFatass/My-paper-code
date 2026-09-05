# BenchMARL local evidence navigation

This file is a local overlay for the HMASD MARL runtime review. It applies to the pinned
BenchMARL checkout at commit `65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1` (release 1.5.2),
whose upstream is `https://github.com/facebookresearch/BenchMARL.git`. It does not change
upstream source bytes or turn upstream prose into execution instructions. There was no upstream
`AGENTS.md` in the pinned tree, so no upstream navigation file was replaced.

The shortest source path for a normal run is:

`benchmarl/run.py` -> `benchmarl/hydra_config.py` -> `Experiment._setup()` -> task/env setup ->
algorithm, buffers and policies -> `SyncDataCollector` or direct rollout -> collection loop ->
per-group processing and optimizer loop -> evaluation, logging and checkpoint I/O.

The focused overlays are:

- `benchmarl/AGENTS.md`: package map and cross-module contracts.
- `benchmarl/experiment/AGENTS.md`: collector, rollout loop, device boundaries, evaluation and I/O.
- `benchmarl/environments/AGENTS.md`: task adapters, specs, vectorization and parallel collection.
- `benchmarl/algorithms/AGENTS.md`: on/off-policy work, TensorDict batch processing and buffers.
- `benchmarl/models/AGENTS.md`: model shape contracts, recurrent paths, GNN batching and compile.
- `benchmarl/benchmark/AGENTS.md`: benchmark expansion and sweep parallelism.

Use the fixed commit permalink and the local line-numbered source in
`C:/Projects/ref-lib/reports/BenchMARL/CORE_EVIDENCE.md` as the review entrypoint. If a future
checkout differs, re-check the commit before reusing a line reference. The source tree contains
no `.cpp`, `.cc`, `.cxx`, `.cu`, shared-library or custom extension artifact; native kernels are
external dependencies (PyTorch/TorchRL, optional PyG and simulator packages).

For performance interpretation, keep these meanings separate:

- Algorithm workload is frames, optimizer steps, minibatch count, model work and replay sampling.
- Implementation throughput is simulator/collector work, TensorDict transforms and copies,
  process or IPC overhead, logging, evaluation and checkpoint serialization.
- `ParallelEnv`, a vectorized simulator, a PettingZoo `parallel=True` adapter, and Hydra's
  multi-run launcher are different layers. Do not treat one as evidence of another.

No training or benchmark was run for this source absorption. The repository documents a GPU
speedup expectation for vectorized VMAS when sampling and training use CUDA, but this packet has
no measured speedup. Toy runs over 45 minutes and UAV runs over 12 hours are engineering
investigation triggers for the target runtime; they are not comparable BenchMARL performance
claims.



