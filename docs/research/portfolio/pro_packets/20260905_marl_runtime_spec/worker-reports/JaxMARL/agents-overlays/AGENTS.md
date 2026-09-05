# JaxMARL local navigation overlay

This is a local, read-only navigation overlay for the pinned evidence tree at
`b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9` (`https://github.com/FLAIROx/JaxMARL.git`, canonical
GitHub repository `bold-lab-ai/JaxMARL`). It does not modify upstream source semantics or authorize
training, dependency installation, benchmarking, or source reuse. Upstream has no `AGENTS.md` at
this commit; this file and the child overlays are local notes.

License: the source tree declares Apache License 2.0 in `LICENSE`. Preserve that notice and inspect
third-party notices before reusing any code.

## Navigation

- `jaxmarl/environments/multi_agent_env.py`, `registration.py`, and `spaces.py`: the jittable API,
  pure state transition contract, agent-keyed dictionaries, and space sampling.
- `jaxmarl/wrappers/baselines.py`: `LogWrapper`, `SMAXLogWrapper`, and `CTRolloutManager`; read
  this before interpreting agent, environment, reward, or observation dimensions.
- `jaxmarl/environments/mpe/`: MPE state layout and vectorized physical interactions.
- `jaxmarl/environments/smax/`: SMAX state, action masks, nested world-step scan, and quadratic
  unit-pair calculations.
- `jaxmarl/environments/hanabi/`, `overcooked_v2/`, and `storm/`: turn-based legality, recipe or
  spawn enumeration, and host-side construction paths.
- `baselines/IPPO/`, `baselines/MAPPO/`, and `baselines/QLearning/`: single-file JAX learners;
  compare the child overlays and `reports/JaxMARL/CORE_EVIDENCE.md`.
- `baselines/run_minimal_baseline_set.py`: launcher-level GPU slot concurrency and per-run logs.

## Performance reading rules

Read `jax.jit`, `jax.vmap`, and `jax.lax.scan` as transformation boundaries, then follow array
shapes and key splitting. Distinguish first-call compilation from steady-state execution. A timer
is meaningful only when it waits for device completion (`jax.block_until_ready`); a host callback or
Python-side enumeration is a possible synchronization or compile/startup cost. No performance,
GPU, or VNFC acceleration claim follows from this tree without a separately recorded benchmark.

RNG is explicit JAX key threading; never infer independent streams without following every
`jax.random.split`. `jnp` defaults and explicit casts determine dtype; inspect state fields and
`astype` calls rather than assuming float32 or integer width. Agent dictionaries are converted to
fixed arrays in a declared agent order, so changing names/order changes semantics and compilation
shapes.
