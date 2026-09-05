# `mava/systems/sac/anakin/` navigation overlay

`ff_isac.py` is the feed-forward continuous-control reference.

## Navigation and layout

The learner state carries observation, environment state, Flashbax item-buffer state, actor/Q/
alpha parameters, optimizers, step counter, and a JAX key. `explore` fills the buffer with random
actions; `update_step` scans `rollout_length` acting steps followed by `epochs` replay samples.
The compiled wrappers are `pmap(device) -> vmap(batch) -> scan`. Q and actor/alpha gradients use
device and batch `pmean`.

## Boundary

Replay `min_length=explore_steps`, item batch size, delayed policy update, target entropy, key
splits, and done masks are algorithm semantics. `block_until_ready` bounds the training timer,
but first-call compilation is included; no warm-up or comparative speedup is established.

