# BenchMARL performance-core evidence

## Scope and provenance

- Local source: `C:/Projects/ref-lib/BenchMARL`.
- Upstream: `https://github.com/facebookresearch/BenchMARL.git`.
- Fixed source commit: `65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1` (local `HEAD`, release 1.5.2).
- Official identity check: the [official repository](https://github.com/facebookresearch/BenchMARL),
  the [official 1.5.2 release](https://github.com/facebookresearch/BenchMARL/releases/tag/1.5.2),
  and the fixed [README](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/README.md)
  agree on the project name and purpose. The release page points 1.5.2 to short SHA `65d649d` and
  states that it is paired with TorchRL 0.11.
- License: [MIT](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/LICENSE).
  Source snippets below are short, attributed excerpts used for review; no source file is copied
  into HMASD. Every Python file inspected carries the same Meta copyright header and refers to the
  root MIT license.
- Upstream navigation: no `AGENTS.md` exists in the fixed Git tree. The files under the clone are
  local navigation overlays; their exact backups are under `agents-overlays/`.
- Method: direct `rg`, line-numbered reads and `git show` against the fixed clone. No dependency was
  installed; no training, benchmark, compiler or speed test was run.

## End-to-end call chain

The executable path is:

`benchmarl/run.py:14-38` -> `hydra_config.py:33-60` -> `Experiment._setup()`
(`experiment.py:386-395`) -> task/env setup (`447-503`) -> algorithm, buffers, losses and
optimizers (`505-537`) -> collector or direct rollout (`539-567`) -> collection/training loop
(`677-813`) -> evaluation (`889-952`), logger writes and checkpoint state (`954-1068`).

The fixed-commit entrypoint links are [run.py](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/run.py#L14-L38),
[experiment setup](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L386-L567),
and the [main loop](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L677-L865).

## Collector, vectorized environment and parallel environment

`Experiment._setup_task()` builds a test environment with `evaluation_episodes` and a training
factory with `n_envs_per_worker`, both on `sampling_device`. If the test env has an empty
`batch_size`, the training factory is wrapped in TorchRL `SerialEnv` or `ParallelEnv` according to
`parallel_collection`; a non-empty batch size is treated as native vectorization and used directly.
See [experiment.py:447-503](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L447-L503)
and the [TaskClass contract](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/environments/common.py#L57-L103).

The source selection is explicit and synchronous:

```python
self.collector = SyncDataCollector(
    self.env_func, self.policy, device=..., storing_device=..., frames_per_batch=...
)
```

This short excerpt is from [experiment.py:548-561](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L548-L561).
There is no custom async collector, queue, prefetcher or overlap loop in BenchMARL. The precise
worker, copy and IPC implementation belongs to the pinned TorchRL version.

The adapters demonstrate why “parallel” needs a qualifier:

- VMAS forwards `num_envs` to `VmasEnv` and supplies a device
  ([vmas/common.py:17-35](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/environments/vmas/common.py#L17-L35)).
- PettingZoo requests `parallel=True` for its multi-agent API but does not use `num_envs`
  ([pettingzoo/common.py:18-37](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/environments/pettingzoo/common.py#L18-L37)).
- SMACv2, MeltingPot and MAgent construct one external adapter without forwarding `num_envs`
  ([SMACv2](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/environments/smacv2/common.py#L19-L30),
  [MeltingPot](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/environments/meltingpot/common.py#L25-L42),
  [MAgent](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/environments/magent/common.py#L17-L34)).

The fixed docs table marks VMAS vectorized and these other adapters non-vectorized
([components.rst:71-95](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/docs/source/concepts/components.rst#L71-L95)).
Thus `ParallelEnv` is an environment execution wrapper, PettingZoo `parallel=True` is an API
adapter mode, VMAS `num_envs` is native simulator batching, and Hydra multi-run parallel launchers
are sweep scheduling. They are not interchangeable performance evidence.

## TensorDict batch semantics

`TaskClass.group_map()` says that agent data is stacked under group keys, while observation,
state, action and mask specs define the expected nested leaves
([common.py:144-237](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/environments/common.py#L144-L237)).
The algorithm layer validates one action leaf per group and, if present, one action-mask leaf
([algorithms/common.py:78-108](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/algorithms/common.py#L78-L108)).

No single global `[time, env, agent]` convention is imposed by BenchMARL. In the loop, non-RNN
group batches are reshaped to one flat transition-like dimension before buffer extension, whereas
RNN batches retain sequence structure
([experiment.py:727-743](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L727-L743)).
The RNN buffer sizes derive a sequence length using
`ceil(collected_frames_per_batch / n_envs_per_worker)`
([algorithms/common.py:157-165](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/algorithms/common.py#L157-L165)).
PPO's `process_batch` slices leading dimensions, computes GAE, and concatenates the slices
([mappo.py:208-259](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/algorithms/mappo.py#L208-L259)).
Therefore a replacement runner should inspect `TensorDict.batch_size`, `shape` and specs at the
actual TorchRL version; optimizing a reshape without preserving group, time and recurrent-state
meaning changes the estimator.

## On-policy versus off-policy workload

The experiment config keeps separate collection, environment, minibatch, optimizer-step and
memory fields for each mode ([base_experiment.yaml:57-84](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/conf/experiment/base_experiment.yaml#L57-L84)).
`ExperimentConfig` maps on-policy training batches to the collection batch and splits them into
minibatches; off-policy training samples use their own batch size
([experiment.py:126-167](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L126-L167)).

MAPPO declares `on_policy() == True` and computes group-aware GAE in `process_batch`
([mappo.py:208-259](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/algorithms/mappo.py#L208-L259),
[mappo.py:322-354](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/algorithms/mappo.py#L322-L354)).
QMIX declares `on_policy() == False`, reduces group termination with `any(-2)` and group reward
with `mean(-2)`, then feeds a mixer
([qmix.py:149-208](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/algorithms/qmix.py#L149-L208),
[qmix.py:211-233](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/algorithms/qmix.py#L211-L233)).
These operations are semantic algorithm work, not interchangeable implementation overhead.

Each group buffer chooses sampler and storage. On-policy uses without-replacement storage sized to
one collection batch. Off-policy uses random or prioritized sampling and can use tensor storage or
disk memmap. The implementation moves a batch into storage and sampled data back to train device:

```python
group_buffer.extend(group_batch.to(group_buffer.storage.device))
subdata = self.replay_buffers[group].sample().to(self.config.train_device)
```

See [experiment.py:734-742](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L734-L742),
[experiment.py:836-865](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L836-L865),
and [algorithms/common.py:144-198](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/algorithms/common.py#L144-L198).
One subtle boundary is that the off-policy disk branch passes the train device to
`LazyMemmapStorage`; the string `buffer_device="disk"` does not itself identify the mapped tensor
device.

## Device and CPU/GPU exchange

Environment construction and collector `device`/`storing_device` use `sampling_device`; algorithm
models and losses use `train_device`; off-policy tensor storage uses `buffer_device` except for the
disk branch just described. Direct rollout uses `rollout_env.to(sampling_device)` and
`auto_cast_to_device=True` ([experiment.py:539-567](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L539-L567)).
The collection loop then explicitly moves group data to training and storage devices
([experiment.py:731-742](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L731-L742)).

The project docs state an expectation that vectorized VMAS with both sampling and training on CUDA
gets important speed-ups because simulation and training are batched without movement
([features.rst:108-120](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/docs/source/concepts/features.rst#L108-L120)).
That is documentation guidance, not a measurement in this packet. `.to` may be a no-op for equal
devices, but collector internals, synchronization and allocator behavior belong to TorchRL/PyTorch
and were not executed here. Logger scalar extraction uses `.item()` in several paths, so host
synchronization is a possible per-iteration cost
([logger.py:113-175](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/logger.py#L113-L175)).

## Model, recurrent and native boundaries

Models are TensorDict modules with explicit input/output specs, group and agent dimensions,
centralization and parameter-sharing semantics
([models/common.py:50-163](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/models/common.py#L50-L163)).
MLP concatenates and flattens trailing feature dimensions, then calls TorchRL `MultiAgentMLP` or
per-agent modules ([mlp.py:55-84](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/models/mlp.py#L55-L84),
[mlp.py:124-154](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/models/mlp.py#L124-L154)).
GRU/LSTM unbind a time dimension in Python, use `torch.vmap` for selected multi-agent paths,
and optionally wrap the recurrent cell with `torch.compile(mode="reduce-overhead")`
([lstm.py:57-96](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/models/lstm.py#L57-L96),
[lstm.py:241-280](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/models/lstm.py#L241-L280)).
The fixed YAML defaults `compile: False`
([lstm.yaml](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/conf/model/layers/lstm.yaml#L1-L15)).

GNN glue flattens all leading batch dimensions into a PyG `Batch`, repeats edge indices and may
build radius graphs and edge features ([gnn.py:269-371](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/models/gnn.py#L269-L371),
[gnn.py:411-461](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/models/gnn.py#L411-L461)).
The fixed tree has no `.cpp`, `.cc`, `.cxx`, `.cu`, `.so` or `.dll` source/artifact and `setup.py`
only declares Python dependencies plus optional PyG and simulator extras
([setup.py:42-67](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/setup.py#L42-L67)).
PyTorch/TorchRL, PyG and simulator packages can contain native kernels, but their presence says
nothing by itself about end-to-end MARL throughput. Any comparison must measure the full codepath,
including collector, simulator, transfers and I/O.

## Evaluation, logging and file I/O

Evaluation is inside the training loop when enabled and the interval divides collected frames
([experiment.py:776-808](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L776-L808)).
The no-grad evaluation path loops episodes in Python for an unbatched test env, or performs one
vectorized rollout and unbinds it for a batched env
([experiment.py:889-952](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L889-L952)).
Rendering is enabled by default in the YAML and only the first evaluation episode is rendered;
video conversion and logger calls can add wall time
([features.rst:74-106](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/docs/source/concepts/features.rst#L74-L106),
[logger.py:176-260](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/logger.py#L176-L260)).

The experiment creates a `config.pkl` with pickled task/config/callback objects during setup,
serializes loss/buffer/collector state with `torch.save`, optionally excludes buffers, and retains
only the configured number of checkpoint files
([experiment.py:579-616](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L579-L616),
[experiment.py:954-1068](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/experiment.py#L954-L1068)).
The evaluation logger writes JSON metrics and may save videos
([logger.py:176-260](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/experiment/logger.py#L176-L260));
`eval_results.py` recursively walks JSON files and merges them, with optional output serialization
([eval_results.py:30-96](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/eval_results.py#L30-L96)).
Checkpoint, logger and cleanup time therefore belongs in a wall-clock claim unless the benchmark
protocol disables or reports it.

## Sweep semantics and workload accounting

`Benchmark` expands `len(algorithms) * len(tasks) * len(seeds)` and its own runner executes the
experiments sequentially ([benchmark.py:15-79](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/benchmarl/benchmark/benchmark.py#L15-L79)).
Hydra's multi-run launcher may be configured for joblib or Slurm, but that is external sweep
scheduling ([running.rst:24-35](https://github.com/facebookresearch/BenchMARL/blob/65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1/docs/source/usage/running.rst#L24-L35)).
An algorithm wall-time comparison must first match frames, model, env, seed count, optimizer
steps/minibatches, evaluation, logging, checkpointing and launcher contention. A larger algorithm
workload can be slower even when its implementation has higher raw throughput.

## Limits and non-claims

- No result-bearing run, profiler, FPS/steps-per-second capture, memory measurement, or
  CPU/GPU speedup measurement was performed.
- The project documentation's CUDA/VMAS speedup statement is a design expectation only; this
  evidence packet does not promote it to an empirical claim.
- The fixed tree has no task named `toy` or `UAV` in `benchmarl/conf/task`. A toy run over 45 minutes
  or a UAV run over 12 hours is an engineering verification trigger for the target runtime, not a
  comparable BenchMARL result or a promise about any implementation.
- Potential costs such as TorchRL collector internals, environment kernel efficiency, Python
  process/IPC overhead, PyG native kernels, allocator synchronization and logger backends remain
  inferred from call sites or external dependencies. They require an exact-version, fixed-hardware
  measurement before being used as an optimization or investment decision.
- “C++ exists” and “GPU is configured” are not throughput evidence. The relevant quantity is
  end-to-end implementation throughput under the same algorithm workload and I/O policy.

