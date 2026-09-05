# `benchmarl/benchmark/` overlay

`Benchmark` is an experiment enumerator. It creates the Cartesian product of algorithm configs,
tasks and seeds (`benchmark.py:15-68`) and `run_sequential()` executes one experiment at a time
(`benchmark.py:70-79`). It shares one `ExperimentConfig` across all experiments, so a benchmark
comparison inherits the same collection, optimizer, evaluation, logging and checkpoint settings
unless the caller creates separate configs.

Hydra's `-m` multi-run and its optional joblib/slurm launchers are outside this class and are
documented in `docs/source/usage/running.rst:24-35`. They are sweep scheduling choices, separate
from `ParallelEnv` inside one experiment. A sweep's wall time is therefore a product of experiment
count, algorithm workload and launcher/device contention; `Benchmark` itself contains no measured
throughput instrumentation or in-process concurrency.

