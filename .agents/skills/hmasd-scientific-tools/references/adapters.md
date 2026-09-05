# Task-specific adapters

This is the approved second-batch routing, not a requirement to install every library.

| Need | First implementation source | Integration boundary |
| --- | --- | --- |
| New PyTorch MARL benchmark | C:/Projects/ref-lib/reports/BenchMARL/CORE_EVIDENCE.md and ROOT_RETURN.md; official BenchMARL/TorchRL | Select compatible algorithm/task API in a separate environment. Fixed BenchMARL1.5.2 study uses TorchRL0.11; do not assume the project's older TorchRL snapshot is compatible. |
| Cooperative baseline/PPO details | C:/Projects/ref-lib/reports/epymarl/ and on-policy/ plus their fixed source links | Trace observation, centralized critic, masks, recurrent state, terminal/truncation, optimizer and actual update counts. Reuse accepted code, not a library name as competence proof. |
| Graph connectivity/path calculation | Existing NetworkX3.2.1; source skill networkx when useful | Use a suitable algorithm, avoid all-path/all-subset enumeration by default. Graph metric is not task return. |
| GNN batching/message passing | Local torch-geometric skill and official version-matched PyG docs | Install only for an actual GNN task; confirm Torch/CUDA/wheel compatibility. Do not substitute newer skill examples into pinned2.6.1 silently. |
| PettingZoo adapter | https://pettingzoo.farama.org/content/environment_tests/ | Use api_test or parallel_api_test for the actual interface, within its focused test scope. Interface tests do not prove reward or information correctness. No forced rewrite of VNFC's native API. |
| Multiple-task/multiple-seed benchmark report | https://github.com/google-research/rliable | Optional isolated analysis dependency; upstream is archived. Use task/run arrays with explicit score normalization and uncertainty units. IQM/bootstrap do not manufacture independent seeds. |

For paired uncertainty use SciPy bootstrap with actual matched indices and correct
independent units, preserving task/zone strata where needed. Few training seeds mean
limited uncertainty information; do not turn resampling repetitions into new evidence.
Do not use paired differences when seed labels are coincidentally equal across unrelated runs.

First-batch references: PyTorch2.7 `torch.profiler` and `torch.utils.benchmark` at
https://docs.pytorch.org/docs/2.7/profiler.html and
https://docs.pytorch.org/docs/2.7/benchmark_utils.html . Existing native cost evidence
may be sufficient without either tool. Approved optional bounded profiling is part of
the concrete CM assignment, not a standing profiler framework or compulsory extra A.

PufferLib, JaxMARL/Mava and VMAS migration are third-batch work and are not introduced
by this adoption. Using the existing reference reports read-only remains allowed.
