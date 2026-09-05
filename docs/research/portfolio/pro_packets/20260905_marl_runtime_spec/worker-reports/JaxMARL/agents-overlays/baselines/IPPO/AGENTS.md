# IPPO baseline navigation

Key entry points are `ippo_rnn_smax.py`, `ippo_rnn.py`, and the feed-forward environment-specific
scripts. IPPO RNN uses Flax `nn.scan` for the GRU, collects transitions with an environment `vmap`
inside a temporal `lax.scan`, computes GAE with a reverse scan, then scans minibatches and update
epochs.

In `ippo_rnn_smax.py`, `NUM_ACTORS = env.num_agents * NUM_ENVS`; `batchify` reshapes agent-major
arrays to actors, while `unbatchify` restores `(agent, env, ...)`. The initial recurrent state and
trajectory dimensions are therefore actor- and time-dependent. Available-action masks are part of
the policy input and are applied to logits.

The main path vmaps independent keys/states across `NUM_ENVS`; seeds are split at the entry point.
SMAX's `world_steps_per_env_step` remains inside each environment step. The SMAX script uses
`io_callback` for WandB metrics and pins its compiled train function to `jax.devices()[0]`; it does
not provide a measured compile/steady-state report in source.
