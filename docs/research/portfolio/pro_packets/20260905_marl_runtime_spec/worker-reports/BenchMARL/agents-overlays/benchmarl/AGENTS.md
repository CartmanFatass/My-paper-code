# `benchmarl/` package overlay

`benchmarl/` is the Python integration layer. `run.py` and `hydra_config.py` turn Hydra choices
into typed task, algorithm, model and experiment configs. `experiment/` owns the lifecycle;
`environments/` owns TorchRL environment adapters and specs; `algorithms/` owns policy/loss/
buffer composition; `models/` owns TensorDict modules; `benchmark/` enumerates repeated
experiments. `conf/` supplies the default YAML values but has no separate overlay because its
semantics are read at the owning module.

Check `run.py:14-38`, `hydra_config.py:33-60`, and `experiment/experiment.py:386-567` at the
pinned commit before changing a runtime assumption. The object passed between these modules is a
TorchRL/TensorDict stack: environment specs establish nested group keys, the algorithm turns
those specs into policies and losses, and the experiment owns the collection/training/evaluation
ordering.

There is no package-local scheduler, asynchronous prefetcher, custom C++ extension, or benchmark
executor hidden at this level. Throughput observations must identify the external TorchRL,
TensorDict, PyTorch, simulator, logger and launcher versions involved.



