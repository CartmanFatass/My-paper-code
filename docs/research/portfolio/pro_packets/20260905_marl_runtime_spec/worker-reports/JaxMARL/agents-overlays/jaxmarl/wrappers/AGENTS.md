# Baseline wrapper navigation

`baselines.py` is the main bridge from agent dictionaries to learner arrays. `LogWrapper` and
`SMAXLogWrapper` accumulate episode returns/lengths inside the JAX state and expose returned metrics
in `info`. `CTRolloutManager` owns the baseline batch axis.

Performance reading: `batch_reset` splits one key into `batch_size` keys and vmaps `wrapped_reset`;
`batch_step` does the same for keys, states, and action dictionaries. With preprocessing enabled,
agent observations are flattened, zero-padded to the maximum agent observation length, and appended
with a one-hot agent ID. It adds `obs["__all__"]`, `rewards["__all__"]`, and environment-specific
global-state/reward rules; these extra arrays affect both memory and learner shapes.

`jax.jit` surrounds wrapper calls, so inspect the first invocation separately. `LogWrapper` metrics
are JAX arrays until a callback or host consumer reads them. `MPELogWrapper` multiplies logged
rewards by `num_agents`; this is a semantic comparison caveat, not a performance optimization.
