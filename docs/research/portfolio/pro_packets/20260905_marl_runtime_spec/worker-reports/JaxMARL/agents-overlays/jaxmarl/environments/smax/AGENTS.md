# SMAX environment navigation

`smax_env.py` contains `State` arrays indexed by all allies followed by all enemies, the
`Scenario` registry, reset, action decoding, world transition, observations, rewards, and legal
action masks. `speed.py` is the source-level throughput harness: it compiles before timing and
waits for completion inside the timed call.

Performance reading: one environment step invokes a nested `lax.scan` of
`world_steps_per_env_step` (default 8), and each world step vmaps per-unit actions and random keys.
`_push_units_away`, observation paths, and legal-action masks materialize unit-pair or per-unit
arrays; `num_agents`, observation type, map scenario, and world-step count are static shape
drivers. Baselines add an outer `vmap` over `NUM_ENVS` and often a temporal `lax.scan`.

The state uses explicit `uint8`/`bool`/`int32` fields for unit types and actions, while positions,
health, and most feature arrays use JAX defaults. Reset splits team, position, and unit-type keys;
the per-unit world kernel splits `num_agents` keys. Terminal means a team is all dead or the step
limit is reached. Do not count `speed.py`'s reported steps as world substeps or agent-actions.
