# `jaxmarl/` navigation

Package entry points are `registration.py` (`make` and `registered_envs`), `environments/`,
`wrappers/`, and `__init__.py`. The public environment contract and state tree live in the child
overlay under `environments/`; baseline-facing batching lives under `wrappers/`.

For performance reading, treat environment objects and agent name lists as static JIT arguments.
Trace `reset(key) -> (obs, state)` and `step(key, state, actions) -> (obs, state, reward, done,
info)` through the concrete environment. Arrays remain JAX values in the state tree; Python dicts
are a boundary for naming agents and are stacked in fixed order by wrappers and baselines.

RNG keys are not mutable: each transition must consume a split key. `MultiAgentEnv.step` splits a
reset key and auto-resets completed episodes, selecting reset versus stepped leaves with
`lax.select`; this affects both workload and returned state. Dtype and shape are environment
configuration, so compare them before comparing learner throughput.
