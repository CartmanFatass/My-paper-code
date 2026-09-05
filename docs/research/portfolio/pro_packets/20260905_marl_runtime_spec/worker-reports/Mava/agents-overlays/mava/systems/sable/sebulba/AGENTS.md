# `mava/systems/sable/sebulba/` navigation overlay

`ff_sable.py` is the current explicit-sharding reference.

## Navigation and boundary

The actor path mirrors PPO Sebulba and calls a jitted Sable action function on actor devices.
The learner creates a one-dimensional `Mesh` named `learner_devices`, uses `NamedSharding` and
`PartitionSpec`, and wraps the learner in `jax.jit(shard_map(...))`. Rollouts are stacked and
partitioned through `Pipeline`; learner state/parameters are published after readiness. Preserve
agent chunking, hidden-state initialization, and data axis conversion when comparing runtimes.


