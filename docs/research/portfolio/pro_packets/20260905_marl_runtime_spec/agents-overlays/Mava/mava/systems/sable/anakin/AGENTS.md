# `mava/systems/sable/anakin/` navigation overlay

Use `ff_sable.py` and `rec_sable.py` for current JAX-native Sable training.

## Navigation and boundary

The execution shape follows Anakin's device and update-batch replication, environment `vmap`, and
time/epoch/minibatch `scan`. Recurrent Sable carries hidden states; feed-forward Sable disables
temporal positional encoding and may chunk agents. Preserve network memory configuration, agent
axis ordering, reward/done handling, and RNG behavior. Transform placement is a layout fact, not
evidence of a measured speedup.

