# MAPPO baseline navigation

`mappo_rnn.py` and `mappo_rnn_smax.py` are the principal recurrent MAPPO paths. They share the
IPPO-style scan/vmap structure but use a central value input where the script supplies one (SMAX
uses world-state handling). Read `batchify`/`unbatchify`, recurrent reset masks, and the config
before comparing with IPPO.

Performance reading: rollout collection is temporal `lax.scan` over batched environments; policy
and value updates scan epochs/minibatches. `jax.random.permutation` shuffles actor axes. Logging in
the recurrent scripts is a JAX host callback, so it may add synchronization/host overhead inside
the compiled update loop. The exact entry point determines whether final outputs are explicitly
blocked before saving.

Preserve agent order, global-state shape, action masks, and explicit key splitting. A central critic
changes memory and compute shapes even when the environment and `NUM_ENVS` match IPPO.
