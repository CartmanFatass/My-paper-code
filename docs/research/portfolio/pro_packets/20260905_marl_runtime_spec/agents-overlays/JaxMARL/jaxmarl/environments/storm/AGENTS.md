# STORM / grid environment navigation

`storm_env.py` defines the grid-game environment and precomputes `AGENT_SPAWNS` at module import:
Python `itertools.combinations` creates all length-eight spawn combinations, then converts them to
a JAX array. This is a host/import and memory cost, separate from a compiled transition.

Performance reading: inspect the pure state transition separately from rendering and module-level
enumeration. Fixed arrays and `vmap`/`lax` kernels can be compiled, but import-time Python work is
already paid before the first JIT call. Agent count, grid dimensions, and coin counts are shape
drivers; do not infer scaling from a small scenario.

RNG keys and explicit integer state dtypes must be preserved. This overlay records source navigation
only; no environment execution or benchmark was performed.
