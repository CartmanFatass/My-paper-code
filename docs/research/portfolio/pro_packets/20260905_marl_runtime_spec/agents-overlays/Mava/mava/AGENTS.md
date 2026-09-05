# `mava/` navigation overlay

This additive overlay belongs to the fixed Mava source tree. Preserve upstream files and any
future upstream `AGENTS.md`; this file is only a study navigation aid.

## Local map

- `systems/`: algorithm runners and their Anakin/Sebulba execution loops.
- `evaluator.py`: JAX and CPU-vector evaluation, episode loops, and SPS timing.
- `utils/make_env.py`: environment registry and wrapper order.
- `utils/jax_utils.py`: leading-axis reshaping and unreplication helpers.
- `utils/sebulba/`: bounded pipelines, actor parameter sources, and rate limiters.
- `utils/logger.py`: console, Neptune, TensorBoard, and MARL-eval JSON sinks.
- `wrappers/`: Jumanji/JaxMARL/Gym adapters, auto-reset, and episode metrics.
- `networks/`: feed-forward/recurrent network contracts; `configs/`: runtime defaults.

## Boundary

`MarlEnv` exposes per-agent observations and masks; callers add leading device, update-batch,
environment, or time axes. Anakin owns JAX transforms and replicated state. Sebulba owns host
environment interaction and explicit learner-device sharding. Wrapper reward, discount, terminal,
and `real_next_obs` behavior is scientific meaning and must remain explicit in any downstream
specification.

