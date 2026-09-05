# `mava/systems/q_learning/anakin/` navigation overlay

`rec_iql.py` is the current Anakin reference.

## Navigation and layout

Initialization builds a Flashbax trajectory buffer and replicates state across devices and update
batches. Each action step vmaps `env.step`, appends a one-step transition, and scans rollout
time. Training samples the replay buffer, aligns first/next time slices, swaps `(B,T)` to `(T,B)`
for `ScannedRNN`, then runs target-Q and optimizer updates. The outer update is device `pmap`,
update-batch `vmap`, and nested `scan`.

## Boundary

`num_envs`, `sample_sequence_length`, `sample_batch_size`, terminal alignment, and PRNG stream
are part of the IQL object. `unreplicate_batch_dim` is only for evaluation/checkpoint views; it
does not mean the training state is single-copy.

