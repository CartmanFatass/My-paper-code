# `benchmarl/experiment/` overlay

`experiment.py` is the runtime spine. `_setup_task()` constructs a test environment and a
training environment factory on `sampling_device`; if the test environment is unbatched it wraps
the factory in `SerialEnv` or `ParallelEnv` according to `parallel_collection`, while a native
vectorized environment is used directly (`experiment.py:447-503`). `_setup_algorithm()` creates
one replay buffer, loss/updater and optimizer map per agent group. `_setup_collector()` selects
TorchRL `SyncDataCollector` for no-gradient collection, or direct `EnvBase.rollout` when
`collect_with_grad=True` (`experiment.py:505-567`).

The loop first receives one collection batch, logs it, detaches it, then for each group excludes
other groups and info keys, moves the group batch to `train_device`, calls the algorithm's
`process_batch`, flattens non-RNN batches, moves them to the storage device, and extends that
group's buffer. Each optimizer iteration samples and moves data back to `train_device`, computes
losses, backpropagates, clips, steps and optionally updates priorities/targets
(`experiment.py:677-865`). After training it may evaluate, log timers, and serialize a
checkpoint. The collector policy weights are updated only in the no-gradient branch.

Batch axes are not globally renamed by BenchMARL. Use `TensorDict.batch_size`, `shape` and each
spec's group shape. Non-RNN training calls `reshape(-1)`, so transition-like leading dimensions
are flattened before buffering. RNN paths preserve sequence structure; buffer sequence length is
derived as `ceil(collected_frames_per_batch / n_envs_per_worker)` in
`algorithms/common.py:157-165`. PPO's `process_batch` explicitly slices leading dimensions and
concatenates them after value estimation, so a new runner must verify the exact TorchRL collector
batch layout rather than assume a universal `[time, env, agent]` order.

The explicit device boundaries are `sampling_device` for envs and collector storage,
`train_device` for algorithm models and sampled training data, and off-policy `buffer_device` for
tensor/memmap storage. A `.to(...)` that already targets the same device may be a no-op; collector
placement and transfer details remain TorchRL behavior. `.item()` in logging can synchronize a
CUDA scalar with the host. No async overlap or measured throughput claim is implemented here.

`_evaluation_loop()` is no-grad and local-seed aware. An unbatched test env runs episodes in a
Python loop; a batched test env performs one rollout and unbinds it. Rendering, JSON/logger writes,
video conversion and periodic `torch.save` checkpoints are part of wall time unless explicitly
excluded by the experiment configuration. `close()` also removes disk-buffer scratch directories.

