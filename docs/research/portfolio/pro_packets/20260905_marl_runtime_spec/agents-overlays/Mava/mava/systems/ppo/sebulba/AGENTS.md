# `mava/systems/ppo/sebulba/` navigation overlay

`ff_ippo.py` is the current reference for the Sebulba PPO execution path.

## Navigation

Actors run `GymToJumanji` CPU vector environments in threads. A jitted actor function moves
observations to an actor device and actions back to CPU. `Pipeline` stacks each rollout, puts it
under a bounded queue, and shards it for learner devices. The learner uses `shard_map` with a
`learner_devices` mesh, scans PPO epochs/minibatches, publishes parameters through
`ParamsSource`, and reports timings to the main evaluation loop.

## Boundary

`num_envs` is per actor thread; each learner gets `num_envs / len(learner_device_ids)` after the
pipeline's data partition. Queue blocking is an intentional freshness/backpressure boundary,
and actor parameter publication is asynchronous between learner updates. CPU environment steps,
device transfers, JIT compilation, learner synchronization, and evaluation time must remain
separate in a performance specification.

