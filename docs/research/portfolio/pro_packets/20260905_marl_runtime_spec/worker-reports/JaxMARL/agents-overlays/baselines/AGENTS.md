# Baseline navigation overlay

Baseline scripts follow a CleanRL-style single-file layout with Hydra YAML configuration. Read the
algorithm child overlay and the shared `jaxmarl/wrappers/baselines.py` overlay together. The launcher
`run_minimal_baseline_set.py` expands registry entries, runs each algorithm/environment combination
sequentially, and can run seeds concurrently in GPU slots.

Performance reading: learner code usually nests a temporal `lax.scan`, environment/agent `vmap`,
and an outer `jax.jit`; identify the axis each transform maps before comparing SPS. `NUM_UPDATES` is
derived from `TOTAL_TIMESTEPS // NUM_STEPS // NUM_ENVS`, while environment transition cost may have
additional world substeps. First-call compile and steady-state execution must be separated.

RNG keys are explicitly split and may be vmapped across `NUM_SEEDS`. WandB logging uses
`jax.debug.callback` or `jax.experimental.io_callback`, which is host-side work in the traced loop.
`jax.block_until_ready` appears in several entry points, but not every entry point waits explicitly;
check the exact script before timing. No benchmark or training was run during this inspection.
