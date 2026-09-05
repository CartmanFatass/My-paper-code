# `mava/systems/` navigation overlay

This local overlay indexes current algorithm runners. It does not replace upstream guidance.

## Navigation

- `ppo/anakin/`: feed-forward and recurrent PPO; compiled rollout and learner loops.
- `ppo/sebulba/`: CPU-vector actor threads, bounded rollout pipeline, sharded learner.
- `q_learning/anakin/`: recurrent IQL with per-device replicated trajectory replay.
- `q_learning/sebulba/`: recurrent IQL with one CPU Flashbax buffer per actor and a rate limiter.
- `sac/anakin/`: feed-forward SAC with item replay and nested act/train scans.
- `sable/anakin/`: feed-forward/recurrent Sable Anakin runners.
- `sable/sebulba/`: Sable actor threads plus learner `shard_map`.

## Parallelism and meaning

Anakin runner state is laid out with device and update-batch axes before vector environments;
rollout time is scanned and learner minibatches/epochs are scanned inside the compiled function.
Sebulba rollout data is collected on CPU vector environments, stacked as environment-major
`(B,T,...)`, then partitioned over learner devices. Algorithm transitions, masks, dones,
discounts, keys, and replay alignment are semantic data, not interchangeable layout axes.

