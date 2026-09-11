# `mava/systems/sable/` navigation overlay

Sable is represented in both Anakin and Sebulba runtimes.

## Navigation

- `anakin/ff_sable.py`, `anakin/rec_sable.py`: compiled JAX environment loops.
- `sebulba/ff_sable.py`, `sebulba/rec_sable.py`: actor threads and learner `shard_map`.
- `types.py` and `../ppo/types.py`: action/learner state contracts.

## Boundary

Sable-specific hidden-state initialization, agent chunking, agent shuffling, done handling,
attention/retention network layout, and action log-probability semantics are scientific meaning.
Sebulba's CPU actor/device learner split and explicit `learner_devices` mesh make its timing model
different from Anakin; keep host transfer and queue costs visible.
