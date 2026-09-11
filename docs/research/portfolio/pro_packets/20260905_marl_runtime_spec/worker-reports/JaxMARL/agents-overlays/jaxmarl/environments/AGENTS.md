# `jaxmarl/environments/` navigation

Start with `multi_agent_env.py` and `spaces.py`, then the concrete environment overlay matching the
question. `registration.py` maps public IDs to constructors; it does not create a separate worker
pool. `MultiAgentEnv.State` is a Flax dataclass with scalar `done` and `step`; concrete states add
fixed-shape JAX arrays.

Performance reading: public `reset`, `step`, and `get_avail_actions` are JIT-decorated with the
environment object static. Concrete `step_env` should be pure over `(key, state, actions)` and
return new arrays. Parallel environments are normally an outer `jax.vmap` over independent keys,
states, and action trees; temporal rollout is an outer `lax.scan` in baselines. Do not confuse
these axes with the agent axis introduced by `batchify`.

The source uses agent-keyed dictionaries for API compatibility, then dense arrays for kernels.
Check action masks, auto-reset behavior, `__all__`, and any environment-specific world state before
reusing dimensions. Static Python loops, `itertools` enumeration, rendering, and host callbacks are
outside the pure steady-state kernel unless a caller proves otherwise.
