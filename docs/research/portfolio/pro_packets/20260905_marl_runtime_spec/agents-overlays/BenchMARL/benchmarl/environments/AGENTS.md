# `benchmarl/environments/` overlay

`common.py:57-103` defines the `TaskClass` factory contract. A task returns a zero-argument
factory for a TorchRL `EnvBase`, receives `num_envs`, action mode, seed and device, and declares
group maps plus observation/state/action/info/mask specs. Group data is expected to be stacked
under the group key; the algorithm layer validates the required action and mask leaf names.
Transforms are split between environment transforms and optional replay-buffer sample transforms
(`common.py:259-293`).

Vectorization has two independent meanings in this tree:

- VMAS passes `num_envs` into `VmasEnv` (`vmas/common.py:17-35`), and the environment table marks
  VMAS vectorized.
- PettingZoo sets `parallel=True` on its multi-agent adapter but does not use `num_envs`
  (`pettingzoo/common.py:18-37`); SMACv2, MeltingPot and MAgent likewise construct one adapter
  without using `num_envs` (`smacv2/common.py:19-30`, `meltingpot/common.py:25-42`,
  `magent/common.py:17-34`). The experiment layer therefore emulates batches with
  `SerialEnv`/`ParallelEnv` when `batch_size == ()`.

`ParallelEnv` is selected by `experiment.parallel_collection`; it is an environment execution
wrapper and must not be conflated with a PettingZoo parallel API, a native vectorized simulator,
or a Hydra multi-run launcher. Adapter implementations define the actual simulator cost,
reset/termination behavior and device support. This package contains no standalone performance
benchmark for those costs.

