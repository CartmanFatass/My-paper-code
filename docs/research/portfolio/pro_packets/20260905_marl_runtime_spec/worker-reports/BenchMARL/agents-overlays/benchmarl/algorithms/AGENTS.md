# `benchmarl/algorithms/` overlay

`common.py:36-76` binds an algorithm to the experiment's train and buffer devices, group map,
specs and on/off-policy mode. `get_loss_and_updater`, policy builders and `get_parameters` cache
per-group objects. `get_replay_buffer()` chooses sampler and storage from the mode: on-policy uses
without-replacement storage sized to one collection batch; off-policy uses random or prioritized
sampling and can use a tensor, disk memmap, or configured device (`common.py:144-198`). The
off-policy disk branch constructs `LazyMemmapStorage` with `self.device` (the train device), so
do not infer its device from the string `buffer_device == "disk"` alone.

`process_batch()` is the semantic boundary between collected TensorDicts and a loss. MAPPO is
on-policy (`mappo.py:208-259`, `322-354`): it expands global done/terminated/reward keys to each
group and computes GAE either across the whole batch or sliced minibatches. QMIX is off-policy
(`qmix.py:149-173`, `211-233`): it reduces group termination with `any(-2)` and group rewards
with `mean(-2)` to the mixer keys. These transformations encode algorithm semantics and cannot be
replaced by a throughput-motivated reshape without changing the estimator.

The experiment loop controls how many optimizer steps and minibatches are performed. The YAML has
separate on-policy and off-policy frame, environment, minibatch, replay-memory and optimizer-step
fields. Compare implementation throughput only after matching algorithm workload, model,
environment, seed and logging/checkpoint settings. An ensemble must keep all component algorithms
on the same policy mode (`experiment` docs, `features.rst:139-158`).



