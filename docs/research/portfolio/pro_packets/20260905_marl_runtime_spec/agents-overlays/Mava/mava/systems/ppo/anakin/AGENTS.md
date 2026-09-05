# `mava/systems/ppo/anakin/` navigation overlay

The current feed-forward reference is `ff_ippo.py`; recurrent layout is in `rec_ippo.py`.

## Navigation

`ff_ippo.py:get_learner_fn` contains rollout, GAE, minibatch/epoch scans, and the update-batch
`vmap`; `learner_setup` wraps it in device `pmap`, resets `D*UB*NE` environments, and reshapes
state to `(D, UB, NE, ...)`. The main loop measures a learner call after `time.time()` and waits
with `jax.block_until_ready`. `rec_ippo.py` adds recurrent hidden state and chunks rollout time
for minibatches.

## Parallel and semantic boundary

The leading axes are device `D`, update batch `UB`, environment `NE`, and scan time `T`; PPO
minibatch flattening merges time and environment axes only after rollout. `pmean` over `batch`
and then `device` is part of the optimizer semantics. Keys are split for network initialization,
environment reset, action sampling, shuffling, and entropy. Preserve these meanings when writing
runtime specifications; no steady-state speedup is implied by the transforms.

