# Q-learning baseline navigation

`vdn_ff.py` is the clearest feed-forward centralized-training-with-parameter-sharing path;
`vdn_rnn.py`, `qmix_rnn.py`, `pqn_vdn_*`, and `shaq.py` extend the same family. `flashbax` replay
buffer operations are JIT-wrapped; `buffer.add` donates its state argument.

In `vdn_ff.py`, each rollout update scans `NUM_STEPS`, batches Q-network calls over agents with
`vmap`, flattens `(time, env)` before replay insertion, and scans `NUM_EPOCHS` replay updates. The
VDN target sums per-agent max-Q values; the `CTRolloutManager` supplies padded observations,
available-action masks, and global reward/state. Entry-level `jax.jit(jax.vmap(make_train(...)))`
maps independent seeds and explicitly blocks the result in `single_run`.

RNG is split for exploration, stepping, replay sampling, testing, and seed mapping. Evaluation is a
separate greedy rollout over `TEST_NUM_ENVS` and `TEST_NUM_STEPS`. WandB uses `jax.debug.callback`
inside the update scan; host logging is not part of the pure device kernel. Compare configs because
`NUM_ENVS`, test batch size, replay capacity, and action/observation padding all alter workload.
